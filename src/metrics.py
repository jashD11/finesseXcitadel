"""
Reported metrics (docs/PROJECT.md §1, guidelines §7) and round-trip construction.

D6/D7/D8 are frozen: a trade is one completed entry-to-exit holding, accuracy and
gain-to-loss are computed on that basis and dual-reported. D10 is frozen: a position
still open on the last day is marked to market and counted as closed.

Every figure here carries its formula into the report. A number without a formula next
to it is not a deliverable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest import BacktestResult, run
from src.clean import Panel
from src.config import Config
from src.decisions import ConfigError

_ROUNDTRIP_COLUMNS = ["symbol", "entry", "exit", "open_at_end", "shares",
                      "cost_basis", "proceeds", "pnl", "return"]


def daily_returns(result: BacktestResult) -> pd.Series:
    """
    Daily portfolio returns, with the first measured against the starting capital.

    The NAV series begins at the *close* of the first rebalance date, by which point the
    book has already been bought and has already moved. Using ``nav.pct_change()`` alone
    would silently discard that first day's return.
    """
    nav = result.nav
    prior = nav.shift(1)
    prior.iloc[0] = result.capital
    return (nav / prior - 1.0).rename("return")


def total_net_pnl(result: BacktestResult, capital: float) -> float:
    """The primary metric. Final NAV less capital. Not risk-adjusted."""
    return float(result.nav.iloc[-1]) - float(capital)


def total_return(result: BacktestResult, capital: float) -> float:
    return float(result.nav.iloc[-1]) / float(capital) - 1.0


def elapsed_years(cfg: Config, result: BacktestResult) -> float:
    span = (result.nav.index[-1] - result.nav.index[0]).days
    return span / float(cfg["metrics.calendar_days_per_year"])


def annualised_return(cfg: Config, result: BacktestResult, capital: float) -> float:
    """D3: geometric (CAGR) over elapsed years — guidelines §7."""
    if cfg["metrics.annualisation"] != "cagr":
        raise ConfigError(f"D3 froze 'cagr'; got {cfg['metrics.annualisation']!r}")
    years = elapsed_years(cfg, result)
    assert years > 0, "zero-length backtest"
    return (float(result.nav.iloc[-1]) / float(capital)) ** (1.0 / years) - 1.0


def sharpe(cfg: Config, result: BacktestResult, capital: float) -> float:
    """
    D4: annualised return / (sample std of daily returns x sqrt(252)), rf = 0.

    Deviates from the guidelines as literally printed — §7 omits the sqrt(252), which
    mismatches units and inflates the ratio ~16x. The deviation is disclosed rather than
    silently applied; see docs/DECISIONS.md D4.
    """
    rets = daily_returns(result)
    sd = float(rets.std(ddof=int(cfg["metrics.sharpe_ddof"])))
    assert sd > 0, "zero volatility"
    annual_sd = sd * np.sqrt(float(cfg["metrics.trading_days_per_year"]))
    excess = annualised_return(cfg, result, capital) - float(cfg["metrics.risk_free"])
    return excess / annual_sd


def max_drawdown(cfg: Config, result: BacktestResult, capital: float) -> float:
    """
    D5: largest peak-to-trough decline in daily portfolio value, after costs.

    The starting capital seeds the running peak, so a drawdown that begins on day one is
    measured from ₹1 crore rather than from the first close.
    """
    if cfg["metrics.mdd_basis"] != "daily_nav":
        raise ConfigError(f"D5 froze 'daily_nav'; got {cfg['metrics.mdd_basis']!r}")
    series = pd.concat([pd.Series([float(capital)]), result.nav.reset_index(drop=True)])
    peak = series.cummax()
    return float((series / peak - 1.0).min())


def turnover(result: BacktestResult) -> pd.Series:
    """
    Gross traded notional at each rebalance as a fraction of that day's NAV.

    Both sides: a full replacement of the book scores ~2.0, because everything is sold
    and everything is bought. Annualised, multiplying by the cost rate gives the cost
    drag directly.
    """
    gross = result.trades.groupby("date")["notional"].apply(lambda x: x.abs().sum())
    return (gross / result.nav.reindex(gross.index)).rename("turnover")


# ── Round trips (D6/D7/D8, D10) ──────────────────────────────────────────────


def round_trips(cfg: Config, result: BacktestResult, panel: Panel) -> pd.DataFrame:
    """
    Build round-trips: a name's position going zero -> non-zero opens one, returning to
    zero closes it, and intermediate top-ups are adds to the same round-trip with the
    return measured on a cost-basis-weighted basis.

    Costs are inside the round-trip: a buy adds its cost to the basis, a sell nets its
    cost out of the proceeds. So the reported return is what the holder actually kept.
    """
    policy = cfg["metrics.open_roundtrip_policy"]
    if policy != "mark_to_market_closed":
        raise ConfigError(f"D10 froze 'mark_to_market_closed'; got {policy!r}")

    last_day = result.nav.index[-1]
    final_close = panel.close.loc[last_day].rename(index=panel.symbols)

    rows: list[dict] = []
    for symbol, group in result.trades.groupby("symbol", sort=True):
        shares = basis = proceeds = bought = realised_basis = 0.0
        entry: pd.Timestamp | None = None

        for row in group.sort_values("date").itertuples():
            if row.shares > 0:
                if shares == 0.0:
                    entry = row.date
                basis += row.notional + row.cost
                shares += row.shares
                bought += row.shares
            else:
                sold = -row.shares
                assert sold <= shares + 1e-9, f"{symbol}: sold more than held"
                # Cost basis leaves proportionally, and is accumulated rather than
                # discarded — a partial sell must still carry its share of the entry
                # price into the round trip's return.
                out = basis * (sold / shares)
                basis -= out
                realised_basis += out
                proceeds += -row.notional - row.cost
                shares -= sold
                if shares < 1e-9:
                    rows.append(_trip(symbol, entry, row.date, False, bought,
                                      realised_basis, proceeds))
                    shares = basis = proceeds = bought = realised_basis = 0.0
                    entry = None

        if shares > 1e-9:  # D10: still open on the final day, marked and counted closed
            marked = shares * float(final_close[symbol])
            rows.append(_trip(symbol, entry, last_day, True, bought,
                              realised_basis + basis, proceeds + marked))

    trips = pd.DataFrame(rows, columns=_ROUNDTRIP_COLUMNS)
    assert trips["cost_basis"].gt(0).all(), "a round trip has no cost basis"
    return trips


def _trip(symbol, entry, exit_, open_at_end, shares, basis, proceeds) -> dict:
    pnl = proceeds - basis
    return {"symbol": symbol, "entry": entry, "exit": exit_,
            "open_at_end": open_at_end, "shares": shares,
            "cost_basis": basis, "proceeds": proceeds,
            "pnl": pnl, "return": pnl / basis if basis else np.nan}


def accuracy(cfg: Config, trips: pd.DataFrame, benchmark: pd.Series) -> dict[str, float]:
    """Dual-reported (D6/D7/D8): share of round-trips with a positive net return, and
    share beating the benchmark over the same dates."""
    if not bool(cfg["metrics.dual_report"]):
        raise ConfigError("D6/D7/D8 froze dual_report: true")
    profitable = float((trips["return"] > 0).mean())

    bench_ret = []
    for row in trips.itertuples():
        a, b = benchmark.get(row.entry), benchmark.get(row.exit)
        bench_ret.append(np.nan if a is None or b is None else b / a - 1.0)
    beat = float((trips["return"].to_numpy() > np.array(bench_ret)).mean())
    return {"profitable": profitable, "beat_benchmark": beat}


def gain_to_loss(cfg: Config, trips: pd.DataFrame) -> dict[str, float]:
    """Dual-reported: mean win / |mean loss| (the guidelines' §7 definition, headline),
    and total gains / total losses (profit factor)."""
    wins = trips.loc[trips["pnl"] > 0, "pnl"]
    losses = trips.loc[trips["pnl"] < 0, "pnl"]
    mean_ratio = float(wins.mean() / abs(losses.mean())) if len(losses) else np.inf
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) else np.inf
    return {"mean_win_over_mean_loss": mean_ratio, "profit_factor": profit_factor}


# ── Benchmarks (D1, D9) ──────────────────────────────────────────────────────


def benchmark_series(cfg: Config, panel: Panel, eligibility: pd.DataFrame,
                     dates: pd.DatetimeIndex, capital: float,
                     start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """
    D1: the equal-weight universe, and the Nifty 100 index.

    The equal-weight series runs through `backtest.run` — the same engine, the same
    rebalance dates, the same costs (D9). That is what makes it a comparison of
    *selection* rather than of plumbing: the only difference from the strategy is which
    names are held.

    The index series is a level, cost-free by construction (D9), forward-filled onto our
    calendar from the last close at or before each day. Never backward — that would move
    a future level into a past cell.
    """
    wanted = list(cfg["benchmark.set"])
    if cfg["benchmark.charge_costs"] != "equal_weight_only":
        raise ConfigError(f"D9 froze 'equal_weight_only'; "
                          f"got {cfg['benchmark.charge_costs']!r}")

    out: dict[str, pd.Series] = {}

    if "equal_weight_universe" in wanted:
        book = {d: sorted(eligibility.columns[eligibility.loc[d].to_numpy()])
                for d in dates}
        ew = run(cfg, panel, book, capital, start, end)
        out["equal_weight_universe"] = ew.nav

    if "nifty100_index" in wanted:
        raw = pd.read_parquet(cfg.resolved_path("paths.data_raw")
                              / "indices_20260824.parquet")
        level = (raw[raw["yahoo_symbol"] == "^CNX100"]
                 .set_index("date")["close"].sort_index()
                 .reindex(panel.dates).ffill())
        window = level.loc[(level.index >= start) & (level.index <= end)]
        assert window.notna().all(), "^CNX100 has no close at or before the window start"
        out["nifty100_index"] = window / window.iloc[0] * capital

    missing = set(wanted) - set(out)
    assert not missing, f"D1 names a benchmark that is not built: {sorted(missing)}"
    return pd.DataFrame(out)
