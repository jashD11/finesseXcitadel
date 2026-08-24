"""
Look-ahead defences, named in the plan so they are tests rather than hopes.

Most of these cannot run until the modules they cover exist, and they are marked
xfail-strict for that reason: when the implementation lands, a test that silently
kept passing would be a test that was never really checking anything.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.calendar import formation_cutoff
from src.features import momentum_12_1
from src.select import top_n
from src.noise import band
from src.universe import eligible_at

SRC = Path(__file__).resolve().parent.parent / "src"


def test_no_bfill_anywhere_in_src():
    """
    Defence #4. Any backward fill in the cleaning path is a leak: it moves a future
    price into a past cell. This is the cheapest possible test and it runs today.
    """
    pattern = re.compile(r"\.bfill\(|method\s*=\s*['\"]bfill['\"]|fillna\([^)]*bfill")
    offenders = [p.name for p in SRC.glob("*.py")
                 if pattern.search(p.read_text()) and p.name != "clean.py"]
    # clean.py mentions bfill only in prose explaining why it is banned.
    body = (SRC / "clean.py").read_text()
    code_lines = [ln for ln in body.splitlines()
                  if "bfill" in ln and not ln.strip().startswith(("#", '"', "'"))
                  and "``bfill``" not in ln]
    assert not offenders, f"bfill found in: {offenders}"
    assert not code_lines, f"bfill in clean.py code: {code_lines}"


def test_formation_cutoff_excludes_the_rebalance_date():
    """
    Defence #1. ``panel.loc[:t]`` includes t. B2 is frozen at signal-through-t-1, so
    the cutoff for a rebalance at t must be strictly earlier than t.
    """
    days = pd.bdate_range("2021-01-01", periods=30)
    t = days[10]
    cutoff = formation_cutoff(t, days, lag=1)
    assert cutoff < t
    assert cutoff == days[9]


def test_formation_cutoff_rejects_a_non_trading_day():
    days = pd.bdate_range("2021-01-04", periods=10)
    with pytest.raises(ValueError):
        formation_cutoff(pd.Timestamp("2021-01-09"), days, lag=1)


@pytest.mark.xfail(strict=True, reason="features.composite blocked on C3")
def test_zscore_is_cross_sectional_not_time_series():
    """
    Defence #5. Shuffling the time axis must leave every per-date z-score unchanged.
    A z computed across time for one name would move.
    """
    from src.config import load
    from src.features import composite
    composite(load(), pd.DataFrame())


def test_selection_ignores_every_price_from_the_rebalance_date_onward(cfg, panel,
                                                                      rebalances):
    """
    Defence #1, the strong form. Scramble every price at t and later; a causal signal
    for t sees only t-1 and earlier, so the book it picks must not move by one name.

    Defence #2 (eligibility is as-of, not evaluated against the full panel) lives in
    tests/test_selection.py, where it can be checked date by date.
    """
    day = rebalances[0]
    cutoff = formation_cutoff(day, panel.dates, int(cfg["signal.formation_lag_days"]))
    scored = momentum_12_1(cfg, panel, cutoff).reindex(eligible_at(cfg, panel, day))
    baseline = top_n(cfg, scored, 3, incumbents=[])

    scrambled = copy.deepcopy(panel)
    future = scrambled.close.index >= day
    rng = np.random.default_rng(20260824)
    scrambled.close.loc[future] *= rng.uniform(0.2, 5.0, scrambled.close.loc[future].shape)

    after = momentum_12_1(cfg, scrambled, cutoff).reindex(eligible_at(cfg, scrambled, day))
    assert top_n(cfg, after, 3, incumbents=[]) == baseline, \
        "a price at or after the rebalance date changed the book — look-ahead"


def test_the_scramble_test_is_not_vacuous(cfg, panel, rebalances):
    """
    The guard on the test above. If scrambling the *formation* window left the book
    unchanged too, the signal would be ignoring its own input and the invariance proved
    nothing.
    """
    day = rebalances[0]
    cutoff = formation_cutoff(day, panel.dates, int(cfg["signal.formation_lag_days"]))
    scored = momentum_12_1(cfg, panel, cutoff).reindex(eligible_at(cfg, panel, day))
    baseline = top_n(cfg, scored, 3, incumbents=[])

    scrambled = copy.deepcopy(panel)
    past = scrambled.close.index < cutoff
    rng = np.random.default_rng(1)
    scrambled.close.loc[past] *= rng.uniform(5.0, 20.0, scrambled.close.loc[past].shape)

    after = momentum_12_1(cfg, scrambled, cutoff).reindex(eligible_at(cfg, scrambled, day))
    assert top_n(cfg, after, 3, incumbents=[]) != baseline, \
        "the signal does not depend on its own lookback window"


def test_noise_band_draws_only_from_the_as_of_eligible_set(cfg, panel, rebalances,
                                                          monkeypatch):
    """
    Defence #6. Drawing from names with full 2021-25 history would leak survivorship into
    the band and make it too easy to beat.

    Tested by invariance rather than by inspecting the draws: an excluded name's prices
    are scrambled beyond recognition, and the band must come out bit-identical. It can
    only do that if the name was never picked.
    """
    monkeypatch.setitem(cfg._flat, "mandate.book_size", 2)
    monkeypatch.setitem(cfg._flat, "noise.n_draws", 60)

    names = sorted(panel.symbols[panel.symbols != "FFF"].index)
    excluded, allowed = names[0], names[1:]
    elig = pd.DataFrame(False, index=rebalances, columns=panel.isins)
    elig.loc[:, allowed] = True

    before = band(cfg, panel, elig, rebalances, 1_000_000.0, panel.dates[-1])

    tampered = copy.deepcopy(panel)
    tampered.close[excluded] *= 1000.0
    tampered.open[excluded] *= 1000.0
    after = band(cfg, tampered, elig, rebalances, 1_000_000.0, panel.dates[-1])

    assert np.array_equal(before.pnl, after.pnl), \
        "an ineligible name influenced the band — it was drawn when it should not have been"
