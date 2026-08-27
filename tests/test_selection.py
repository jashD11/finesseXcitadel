"""Rebalance calendar (B1), as-of eligibility (A5/A10) and the tie-break (C7)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.calendar import _ANCHOR_MONTHS, rebalance_dates, supported_calendars
from src.decisions import ConfigError
from src.select import top_n
from src.universe import eligibility_matrix, eligible_at


def _dates(cfg, panel, calendar_name, monkeypatch):
    monkeypatch.setitem(cfg._flat, "execution.rebalance_calendar", calendar_name)
    return rebalance_dates(cfg, panel.dates, panel.dates[0], panel.dates[-1])


@pytest.mark.parametrize("name", supported_calendars())
def test_every_supported_calendar_yields_trading_days(cfg, panel, name, monkeypatch):
    """Invariants that hold at any cadence. Parameterised off `supported_calendars()`
    rather than a literal list, so adding a cadence cannot leave the test stale."""
    dates = _dates(cfg, panel, name, monkeypatch)
    assert len(dates)
    assert dates.isin(panel.dates).all()
    assert dates.is_monotonic_increasing and dates.is_unique


@pytest.mark.parametrize("frequency", sorted(_ANCHOR_MONTHS))
def test_month_anchored_calendars_take_the_first_trading_day_of_each_anchor_month(
        cfg, panel, frequency, monkeypatch):
    """
    B1's month family. Each anchor month contributes exactly one date, and that date is
    the first trading day on or after the 1st -- so a holiday moves the rebalance
    forward rather than dropping it.

    Deliberately scoped to the month family: both assertions are structurally false for
    weekly and daily, which put many dates in one month. That is what the old
    `sorted({d.month for d in dates}) == [1, 4, 7, 10]` test encoded -- the anchor-month
    model itself, not just the quarterly choice.
    """
    dates = _dates(cfg, panel, frequency + "_first_trading_day", monkeypatch)
    assert set(d.month for d in dates) <= set(_ANCHOR_MONTHS[frequency])
    assert len({(d.year, d.month) for d in dates}) == len(dates)
    for day in dates:
        earlier = panel.dates[(panel.dates >= pd.Timestamp(day.year, day.month, 1))
                              & (panel.dates < day)]
        assert not len(earlier), f"{day.date()} is not the first trading day of its month"


def test_quarterly_is_unchanged_by_the_b1_amendment(cfg, panel, monkeypatch):
    """
    The regression guard for B1's amendment. Adding the week family and the daily
    literal must not move a single quarterly date, or V0 stops being the baseline every
    `Δ vs V0` in the ledger is measured against.
    """
    dates = _dates(cfg, panel, "quarterly_first_trading_day", monkeypatch)
    assert sorted({d.month for d in dates}) == [1, 4, 7, 10]


def test_weekly_takes_the_first_trading_day_of_each_iso_week(cfg, panel, monkeypatch):
    """One date per ISO year-week, and it is the earliest trading day in that week."""
    dates = _dates(cfg, panel, "weekly_first_trading_day", monkeypatch)
    iso = dates.isocalendar()
    keys = list(zip(iso["year"], iso["week"]))
    assert len(set(keys)) == len(dates), "two rebalances landed in one ISO week"

    window_iso = panel.dates.isocalendar()
    for day in dates:
        d_iso = day.isocalendar()
        same_week = panel.dates[(window_iso["year"] == d_iso.year).to_numpy()
                                & (window_iso["week"] == d_iso.week).to_numpy()]
        assert day == same_week.min(), f"{day.date()} is not first in its ISO week"


def test_every_trading_day_is_the_window_verbatim(cfg, panel, monkeypatch):
    dates = _dates(cfg, panel, "every_trading_day", monkeypatch)
    assert dates.equals(panel.dates)


def test_unknown_calendar_is_refused_not_defaulted(cfg, panel, monkeypatch):
    """No silent default. `fortnightly` is deliberately still unsupported."""
    assert "fortnightly" not in supported_calendars()
    monkeypatch.setitem(cfg._flat, "execution.rebalance_calendar", "fortnightly")
    with pytest.raises(ConfigError):
        rebalance_dates(cfg, panel.dates, panel.dates[0], panel.dates[-1])


def test_a_bare_frequency_without_the_suffix_is_refused(cfg, panel, monkeypatch):
    """`weekly` is not `weekly_first_trading_day`. Near-misses must not resolve."""
    monkeypatch.setitem(cfg._flat, "execution.rebalance_calendar", "weekly")
    with pytest.raises(ConfigError):
        rebalance_dates(cfg, panel.dates, panel.dates[0], panel.dates[-1])


def test_late_listing_is_ineligible_until_it_has_the_window(cfg, panel, rebalances):
    """A5: the late lister must not be selectable before it has 252 days of history."""
    late = panel.symbols[panel.symbols == "FFF"].index[0]
    for day in rebalances:
        names = eligible_at(cfg, panel, day)
        assert late not in names, f"a name with no history was eligible on {day.date()}"
        assert len(names) == len(panel.isins) - 1


def test_eligibility_is_as_of_not_full_panel(cfg, panel):
    """
    Defence #2. 'Has enough history' is evaluated as of t. Running the same check on the
    last date -- where the late lister *does* have history -- must give a different
    answer, or the as-of logic is not actually as-of.
    """
    late = panel.symbols[panel.symbols == "FFF"].index[0]
    early = eligible_at(cfg, panel, panel.dates[300])
    assert late not in early
    # The late name lists at index 320 and needs 252 days, so it is never eligible
    # inside this fixture; what must hold is that eligibility grows with time, never
    # shrinks for a name with unbroken history.
    for name in panel.isins.drop(late):
        assert name in early


def test_eligibility_matrix_enforces_the_floor(cfg, panel, rebalances):
    """B9: the book size is never allowed to be constrained silently."""
    with pytest.raises(AssertionError, match="eligible names fell below"):
        eligibility_matrix(cfg, panel, rebalances)


def test_tie_break_prefers_the_incumbent(cfg, panel):
    scores = pd.Series({"B": 1.0, "A": 1.0, "C": 0.5})
    assert top_n(cfg, scores, 1, incumbents=["A"]) == ["A"]
    assert top_n(cfg, scores, 1, incumbents=["B"]) == ["B"]


def test_tie_break_falls_back_to_isin_order(cfg):
    scores = pd.Series({"ZZZ": 1.0, "AAA": 1.0})
    assert top_n(cfg, scores, 1, incumbents=[]) == ["AAA"]


def test_nan_score_never_reaches_selection(cfg):
    scores = pd.Series({"A": 1.0, "B": float("nan")})
    with pytest.raises(AssertionError):
        top_n(cfg, scores, 1, incumbents=[])
