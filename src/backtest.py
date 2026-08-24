"""
The execution engine. One engine, used by everything.

``run`` takes a holdings map and nothing else about how those names were chosen. V0,
V1, every backlog variant, the 2026 restart, the survivorship parallel and all 10,000
noise draws go through this function. If any of them did not, the noise band would be
measuring a difference in plumbing rather than a difference in selection, and every
``z`` in the trial ledger would be meaningless.

That is why the signature carries no signal, no feature, no score.

Frozen conventions, all read from config rather than assumed here:
B2 fill at the open of t on a signal through t-1 · B4 whole shares · B5 residue held
uninvested · B6 the opening build pays costs like any other trade · B7 the clock starts
with the capital at the open of the first rebalance date.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.clean import Panel
from src.config import Config
from src.decisions import ConfigError

_TRADE_COLUMNS = ["date", "isin", "symbol", "side", "shares", "price", "notional", "cost"]


@dataclass(frozen=True)
class BacktestResult:
    """Everything the metrics module and the report need."""
    nav: pd.Series           # daily, indexed on the trading calendar
    holdings: pd.DataFrame   # (date x symbol) share counts
    trades: pd.DataFrame     # date, symbol, side, shares, price, notional, cost
    cash: pd.Series          # daily residue, an explicit line
    costs: pd.Series         # daily costs charged
    capital: float           # the t0 value, at the open of the first rebalance (B7)

    @property
    def weights(self) -> pd.DataFrame:
        """Daily drifted weights. Executed weights at a rebalance are this frame's row
        on that date, before the market moves it."""
        return self.holdings.div(self.nav, axis=0)


def _investable(cfg: Config, value: float, rate: float) -> float:
    """
    The part of the book that may be bought, after B12's cost reserve.

    Worst-case gross turnover at a rebalance is a full replacement — sell everything,
    buy everything — so holding back ``multiple x rate x value`` makes non-negative cash
    a guarantee rather than something that happens to hold on this data.
    """
    rule = cfg["execution.cost_reserve"]
    if rule != "worst_case_gross_turnover":
        raise ConfigError(f"B12 froze 'worst_case_gross_turnover'; got {rule!r}")
    multiple = float(cfg["execution.cost_reserve_multiple"])
    return value * (1.0 - multiple * rate)


def _target_shares(cfg: Config, names: list[str], opens: pd.Series,
                   value: float) -> pd.Series:
    """Equal-notional target, converted to share counts under B4."""
    per_name = value / len(names)
    prices = opens.reindex(names)
    assert prices.notna().all(), f"no open price for {list(prices.index[prices.isna()])}"
    assert (prices > 0).all(), "non-positive open price"

    granularity = cfg["execution.share_granularity"]
    if granularity == "whole":
        return np.floor(per_name / prices)
    if granularity == "fractional":
        return per_name / prices
    raise ConfigError(f"B4 allows 'whole' or 'fractional'; got {granularity!r}")


def run(cfg: Config, panel: Panel, holdings_map: dict[pd.Timestamp, list[str]],
        capital: float, start: pd.Timestamp, end: pd.Timestamp) -> BacktestResult:
    """
    Execute a holdings map.

    At each rebalance date the book is marked at that day's open, split equally across
    the named stocks, and traded to the target; costs are charged on traded notional
    both sides. Between rebalances nothing trades and NAV follows the closes.
    """
    if cfg["execution.nav_start_convention"] != "capital_at_first_rebalance_open":
        raise ConfigError(f"B7 froze 'capital_at_first_rebalance_open'; "
                          f"got {cfg['execution.nav_start_convention']!r}")
    if cfg["execution.cash_residue"] != "hold_uninvested":
        raise ConfigError(f"B5 froze 'hold_uninvested'; "
                          f"got {cfg['execution.cash_residue']!r}")

    rate = float(cfg["mandate.cost_bps"]) / 10_000.0
    charge_build = bool(cfg["execution.charge_initial_build"])

    rebalances = [d for d in sorted(holdings_map) if start <= d <= end]
    assert rebalances, f"no rebalance dates in [{start.date()}, {end.date()}]"

    days = panel.dates[(panel.dates >= rebalances[0]) & (panel.dates <= end)]
    assert len(days), "no trading days in the backtest window"
    assert days[0] == rebalances[0], "NAV must start on the first rebalance date (B7)"

    isins = panel.isins
    holdings = pd.DataFrame(0.0, index=days, columns=isins)
    cash_series = pd.Series(0.0, index=days)
    costs = pd.Series(0.0, index=days)
    trade_rows: list[dict] = []

    shares = pd.Series(0.0, index=isins)
    cash = float(capital)

    for i, day in enumerate(rebalances):
        opens = panel.open.loc[day]
        held = shares[shares != 0.0].index
        assert opens.reindex(held).notna().all(), f"held name has no open on {day.date()}"
        value = float((shares.reindex(held) * opens.reindex(held)).sum()) + cash

        names = list(holdings_map[day])
        assert len(names) == len(set(names)), f"duplicate name in the book on {day.date()}"
        target = pd.Series(0.0, index=isins)
        target.loc[names] = _target_shares(cfg, names, opens,
                                           _investable(cfg, value, rate))

        delta = target - shares
        traded = delta[delta != 0.0]
        notional = traded * opens.reindex(traded.index)

        # B6: the opening build is a transaction like any other. The flag exists so the
        # alternative is a config change, not an edit to the engine.
        charged = charge_build or i > 0
        cost_per_trade = notional.abs() * rate if charged else notional.abs() * 0.0
        total_cost = float(cost_per_trade.sum())

        cash -= float(notional.sum()) + total_cost
        assert cash >= -1e-6, (
            f"negative cash {cash:,.2f} on {day.date()} — targets exceeded the book"
        )
        shares = target

        for isin in traded.index:
            trade_rows.append({
                "date": day,
                "isin": isin,
                "symbol": panel.symbols[isin],
                "side": "BUY" if traded[isin] > 0 else "SELL",
                "shares": float(traded[isin]),
                "price": float(opens[isin]),
                "notional": float(notional[isin]),
                "cost": float(cost_per_trade[isin]),
            })

        # Hold this state until the next rebalance (or the end of the window).
        stop = rebalances[i + 1] if i + 1 < len(rebalances) else None
        segment = days[days >= day] if stop is None else days[(days >= day) & (days < stop)]
        holdings.loc[segment, :] = shares.to_numpy()
        cash_series.loc[segment] = cash
        costs.loc[day] = total_cost

    closes = panel.close.loc[days]
    # `closes[mask]` would blank the un-held cells to NaN and check those instead.
    assert not (holdings.ne(0.0) & closes.isna()).any().any(), \
        "a held name has no close price"
    nav = (holdings * closes).sum(axis=1) + cash_series
    assert nav.notna().all(), "NaN in the NAV series"

    trades = pd.DataFrame(trade_rows, columns=_TRADE_COLUMNS)
    holdings.columns = [panel.symbols[i] for i in holdings.columns]

    return BacktestResult(nav=nav, holdings=holdings, trades=trades,
                          cash=cash_series, costs=costs, capital=float(capital))


def reconcile(result: BacktestResult, panel: Panel, capital: float,
              tol: float = 1.0) -> None:
    """
    Assert the trade log explains the NAV.

    Deliberately rebuilt from ``result.trades`` — the persisted artefact — rather than
    from the engine's internal state, and marked against ``panel``'s own closing prices
    rather than against the NAV being checked. Reconciling internal state against itself
    would be a tautology; this way a trade the engine executed but logged wrongly fails,
    which is the bug class that matters when a reviewer reads the trade table.
    """
    cash = float(capital)
    position: dict[str, float] = defaultdict(float)
    for row in result.trades.itertuples():
        cash -= row.notional + row.cost
        position[row.symbol] += row.shares

    last_day = result.nav.index[-1]
    ticker_close = panel.close.loc[last_day].rename(index=panel.symbols)
    held = pd.Series(position, dtype=float)
    held = held[held != 0.0]
    marked = float((held * ticker_close.reindex(held.index)).sum())

    rebuilt = cash + marked
    reported = float(result.nav.iloc[-1])
    gap = abs(rebuilt - reported)
    assert gap <= tol, (
        f"trade log does not explain the NAV: rebuilt \u20b9{rebuilt:,.2f} vs "
        f"NAV \u20b9{reported:,.2f}, gap \u20b9{gap:,.2f}"
    )

    engine_cash = float(result.cash.iloc[-1])
    assert abs(cash - engine_cash) <= tol, (
        f"cash from the trade log (\u20b9{cash:,.2f}) disagrees with the engine's "
        f"(\u20b9{engine_cash:,.2f})"
    )

    engine_shares = result.holdings.iloc[-1]
    engine_shares = engine_shares[engine_shares != 0.0]
    assert set(engine_shares.index) == set(held.index), (
        "trade log and final holdings name different stocks: "
        f"{sorted(set(engine_shares.index) ^ set(held.index))}"
    )
    assert np.allclose(held.reindex(engine_shares.index).to_numpy(),
                       engine_shares.to_numpy(), atol=1e-6), \
        "trade log does not reproduce the final share counts"
