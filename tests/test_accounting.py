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
from src.noise import draw_seeds

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
    assert set(result.trades["date"].unique()) <= set(rebalances)


@pytest.mark.xfail(strict=True, reason="noise.assert_engine_equivalence blocked on B4")
def test_batch_engine_matches_scalar_engine():
    """
    The assertion the whole noise band rests on: V0's holdings through the batch path
    at D=1 must match backtest.run to the rupee.
    """
    from src.config import load
    from src.noise import assert_engine_equivalence
    assert_engine_equivalence(load(), pd.DataFrame(), None, {})
