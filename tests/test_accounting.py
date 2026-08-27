"""
NAV and trade-log reconciliation. Phase 2's acceptance gate.

The reconciliation tests run against the synthetic panel from conftest, so a failure
points at the engine rather than at the market. `test_batch_engine_matches_scalar_engine`
stays xfail-strict until the noise band exists, so the day it lands it turns red until
it genuinely passes rather than quietly reporting green.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtest import reconcile, run
from src.metrics import round_trips, total_net_pnl
from src.noise import assert_engine_equivalence, band, draw_seeds

CAPITAL = 1_000_000.0


@pytest.fixture
def result(cfg, panel, rebalances):
    book = sorted(panel.symbols[panel.symbols != "FFF"].index)[:3]
    holdings = {day: book for day in rebalances}
    return run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1])


def test_draw_seeds_are_reproducible():
    """Same master seed, same generators — the band must reproduce bit-for-bit."""
    a = [g.random() for g in draw_seeds(20260824, 8)]
    b = [g.random() for g in draw_seeds(20260824, 8)]
    assert a == b


def test_draw_seeds_are_independent_of_batch_size():
    """
    Draw i must be identical whether the run is chunked or not. If this failed,
    changing ``noise.chunk_size`` would silently change the PNL distribution.
    """
    full = [g.random() for g in draw_seeds(20260824, 16)]
    chunked = [g.random() for g in draw_seeds(20260824, 16)[:4]]
    assert full[:4] == chunked


def test_draw_seeds_differ_across_draws():
    values = [g.random() for g in draw_seeds(20260824, 64)]
    assert len(set(values)) == 64


def test_trade_log_reconciles_to_nav(cfg, panel, result):
    """Sum of P&L less costs must equal final NAV minus capital, within ₹1."""
    reconcile(result, panel, CAPITAL, tol=1.0)


def test_round_trip_pnl_sums_to_total_net_pnl(cfg, panel, result):
    """
    Every rupee is either idle cash or inside a round trip, so the decomposition is an
    identity. It catches a whole class of cost-accounting slips that reconcile() cannot,
    because reconcile() never looks at the round-trip construction.
    """
    trips = round_trips(cfg, result, panel)
    assert np.isclose(trips["pnl"].sum(), total_net_pnl(result, CAPITAL), atol=1.0)


def test_cash_is_never_negative(result):
    """B12: the cost reserve makes this a guarantee, not a property of the data."""
    assert (result.cash >= -1e-6).all()


def test_share_counts_are_whole(cfg, result):
    """B4: fractional shares cannot be bought on NSE."""
    assert cfg["execution.share_granularity"] == "whole"
    shares = result.holdings.to_numpy()
    assert np.allclose(shares, np.round(shares))


def test_costs_are_exactly_the_configured_rate(cfg, result):
    rate = float(cfg["mandate.cost_bps"]) / 10_000.0
    trades = result.trades
    assert np.allclose(trades["cost"], trades["notional"].abs() * rate)


def test_nav_starts_at_the_first_rebalance_date(result, rebalances):
    """B7: the clock starts with the capital at the open of the first rebalance."""
    assert result.nav.index[0] == rebalances[0]
    assert result.capital == CAPITAL


def test_nothing_trades_between_rebalances(result, rebalances):
    """
    True for a book with no declared events. B10/A18 added forced mid-cycle exits, which
    are the *only* sanctioned exception; `result` declares none, so the original
    invariant still holds here and the events case is pinned separately below by
    `test_forced_exit_holds_cash_until_the_next_rebalance`.

    Note for high-frequency cadences: under `every_trading_day` every date IS a
    rebalance date, so this assertion becomes trivially true and stops testing
    anything. Kept deliberately -- it still has teeth at every other cadence, and
    deleting it would remove the guard for the cadences it does constrain.
    """
    assert set(result.trades["date"].unique()) <= set(rebalances)


# ── B3: the drift weighting rule ────────────────────────────────────────────────

@pytest.fixture
def drift_result(cfg, panel, rebalances, monkeypatch):
    """Three rebalances where the book actually turns over, so drift and reset differ."""
    names = sorted(panel.symbols[panel.symbols != "FFF"].index)
    books = [names[:3], names[1:4], names[2:5]]
    monkeypatch.setitem(cfg._flat, "weighting.reset_to_target", False)
    holdings = dict(zip(rebalances, books))
    return run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1]), holdings


def test_drift_never_trades_a_retained_name(drift_result):
    """
    B3's defining property. A name selected at t and still selected at t+1 keeps its
    exact share count -- it is not traded, and not even re-floored to a new target.
    """
    result, holdings = drift_result
    days = sorted(holdings)
    for prev, day in zip(days, days[1:]):
        retained = set(holdings[prev]) & set(holdings[day])
        traded = set(result.trades.loc[result.trades["date"] == day, "isin"])
        assert not (retained & traded), \
            f"drift traded retained names {sorted(retained & traded)} on {day.date()}"


def test_drift_and_reset_agree_on_the_first_rebalance(cfg, panel, rebalances, monkeypatch):
    """
    With no incumbents every name is an entry, so the two rules must produce identical
    trades. A free assertion that the drift path shares the reset path's sizing.
    """
    book = sorted(panel.symbols[panel.symbols != "FFF"].index)[:3]
    holdings = {rebalances[0]: book}
    out = {}
    for reset in (True, False):
        monkeypatch.setitem(cfg._flat, "weighting.reset_to_target", reset)
        out[reset] = run(cfg, panel, holdings, CAPITAL,
                         rebalances[0], panel.dates[-1])
    pd.testing.assert_frame_equal(out[True].trades, out[False].trades)


def test_drift_cash_is_never_negative(drift_result):
    """B3-r: the reserve applies to deployable cash, not book value. This is its canary."""
    result, _ = drift_result
    assert (result.cash >= -1e-6).all()


def test_drift_trade_log_reconciles_to_nav(drift_result, cfg, panel):
    result, _ = drift_result
    reconcile(result, panel, CAPITAL)


def test_drift_round_trip_pnl_sums_to_total_net_pnl(drift_result, cfg, panel):
    result, _ = drift_result
    trips = round_trips(cfg, result, panel)
    assert np.isclose(trips["pnl"].sum(), total_net_pnl(result, CAPITAL), atol=1.0)


def test_drift_share_counts_are_whole(drift_result):
    result, _ = drift_result
    assert (result.trades["shares"] % 1 == 0).all()


def test_batch_engine_matches_scalar_engine(cfg, panel, rebalances, result):
    """
    The assertion the whole noise band rests on: a holdings map through the batch path
    at D=1 must match backtest.run to the rupee. Without it, a divergence in plumbing
    would masquerade as a difference in selection.
    """
    book = sorted(panel.symbols[panel.symbols != "FFF"].index)[:3]
    assert_engine_equivalence(cfg, panel, result, {d: book for d in rebalances},
                              CAPITAL, panel.dates[-1])


def test_batch_engine_matches_scalar_engine_under_drift(cfg, panel, rebalances,
                                                        drift_result):
    """
    The same assertion for B3's drift rule. A drift arm scored against a reset band
    would violate "same engine", and the noise band could not adjudicate it -- so the
    equivalence has to hold in both modes, not just the one V0 uses.
    """
    result, holdings = drift_result
    assert_engine_equivalence(cfg, panel, result, holdings, CAPITAL, panel.dates[-1])


def test_chunk_size_cannot_change_a_rupee(cfg, panel, rebalances, monkeypatch):
    """
    `chunk_size` is a memory knob. If it moved the PNL distribution, the band would not
    be reproducible and every z in the ledger would depend on how the run was batched.

    This is bit-exactness, not a tolerance: the engine avoids BLAS matrix products for
    exactly this reason (see `_run_batch`).
    """
    monkeypatch.setitem(cfg._flat, "mandate.book_size", 3)
    monkeypatch.setitem(cfg._flat, "noise.n_draws", 40)
    keep = sorted(panel.symbols[panel.symbols != "FFF"].index)
    elig = pd.DataFrame(False, index=rebalances, columns=panel.isins)
    elig.loc[:, keep] = True

    monkeypatch.setitem(cfg._flat, "noise.chunk_size", 40)
    whole = band(cfg, panel, elig, rebalances, CAPITAL, panel.dates[-1])
    monkeypatch.setitem(cfg._flat, "noise.chunk_size", 3)
    chunked = band(cfg, panel, elig, rebalances, CAPITAL, panel.dates[-1])
    assert np.array_equal(whole.pnl, chunked.pnl)


# ── B10 / A18: forced mid-cycle exits ───────────────────────────────────────────

@pytest.fixture
def event_setup(cfg, panel, rebalances):
    """A book holding three names, with one force-exited midway through segment one."""
    book = sorted(panel.symbols[panel.symbols != "FFF"].index)[:3]
    holdings = {day: book for day in rebalances}
    segment = panel.dates[(panel.dates > rebalances[0]) & (panel.dates < rebalances[1])]
    return book, holdings, {segment[len(segment) // 2]: [book[0]]}


def test_forced_exit_sells_the_whole_position_on_its_date(cfg, panel, rebalances,
                                                          event_setup):
    book, holdings, events = event_setup
    day = next(iter(events))
    out = run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1], events)

    sold = out.trades[(out.trades["date"] == day) & (out.trades["isin"] == book[0])]
    assert len(sold) == 1 and sold.iloc[0]["side"] == "SELL"
    assert out.holdings.loc[day, panel.symbols[book[0]]] == 0.0, \
        "the position survived its own forced exit"


def test_forced_exit_holds_cash_until_the_next_rebalance(cfg, panel, rebalances,
                                                         event_setup):
    """A18/B10: proceeds are not redeployed early -- nothing else trades mid-segment."""
    book, holdings, events = event_setup
    day = next(iter(events))
    out = run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1], events)

    between = panel.dates[(panel.dates > day) & (panel.dates < rebalances[1])]
    assert (out.cash.loc[between] == out.cash.loc[day]).all(), "cash moved mid-segment"
    assert not len(out.trades[(out.trades["date"] > day)
                              & (out.trades["date"] < rebalances[1])]), \
        "something traded between the forced exit and the next rebalance"


def test_forced_exit_never_trades_a_name_it_does_not_hold(cfg, panel, rebalances):
    """An event naming an unheld stock is inert, not an error and not a short sale."""
    names = sorted(panel.symbols[panel.symbols != "FFF"].index)
    holdings = {day: names[:3] for day in rebalances}
    segment = panel.dates[(panel.dates > rebalances[0]) & (panel.dates < rebalances[1])]
    day = segment[len(segment) // 2]

    out = run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1],
              {day: [names[4]]})
    assert not len(out.trades[out.trades["date"] == day]), \
        "an event on an unheld name produced a trade"


def test_forced_exit_reconciles_and_cash_stays_non_negative(cfg, panel, rebalances,
                                                            event_setup):
    _, holdings, events = event_setup
    out = run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1], events)
    reconcile(out, panel, CAPITAL, tol=1.0)
    assert (out.cash >= -1e-6).all()
    trips = round_trips(cfg, out, panel)
    assert np.isclose(trips["pnl"].sum(), total_net_pnl(out, CAPITAL), atol=1.0)


@pytest.mark.parametrize("reset", [True, False])
def test_batch_engine_matches_scalar_engine_with_events(cfg, panel, rebalances,
                                                        event_setup, monkeypatch, reset):
    """
    The assertion the band rests on, now with events in play. If the two engines applied
    forced exits differently, the band would be adjudicating the exit rule rather than
    the selection -- and every `z` in the ledger would be measuring the wrong thing.
    """
    _, holdings, events = event_setup
    monkeypatch.setitem(cfg._flat, "weighting.reset_to_target", reset)
    out = run(cfg, panel, holdings, CAPITAL, rebalances[0], panel.dates[-1], events)
    assert_engine_equivalence(cfg, panel, out, holdings, CAPITAL, panel.dates[-1], events)


def test_the_event_fires_before_the_ex_date_not_on_it(cfg, panel):
    """
    The off-by-one that makes the whole rule work or silently do nothing.

    The ex-date's own open is already ex-entitlement, so an exit scheduled *on* it books
    the phantom drop instead of avoiding it. `ex_date_events` must therefore resolve to
    the last session strictly before the ex-date.
    """
    from src.events import ex_date_events

    isin = panel.isins[0]
    ex = panel.dates[300]
    overrides = pd.DataFrame([{
        "symbol": panel.symbols[isin], "isin": isin, "action": "Demerger",
        "ex_date": ex.strftime("%Y-%m-%d"), "ratio": "", "boundary_date": "",
        "applied": False, "verified_on": "2026-08-28", "source": "synthetic", "note": "",
    }])
    events = ex_date_events(cfg, panel, overrides)
    assert list(events) == [panel.dates[299]], \
        f"expected the last cum session {panel.dates[299].date()}, got {list(events)}"


def test_hold_through_mode_declares_no_events(cfg, panel, monkeypatch):
    """B10 keeps the old behaviour reachable by config rather than by editing an engine."""
    from src.events import ex_date_events

    monkeypatch.setitem(cfg._flat, "execution.corporate_action_mode", "hold_through")
    isin = panel.isins[0]
    overrides = pd.DataFrame([{
        "symbol": panel.symbols[isin], "isin": isin, "action": "Demerger",
        "ex_date": panel.dates[300].strftime("%Y-%m-%d"), "ratio": "",
        "boundary_date": "", "applied": False, "verified_on": "2026-08-28",
        "source": "synthetic", "note": "",
    }])
    assert ex_date_events(cfg, panel, overrides) == {}
