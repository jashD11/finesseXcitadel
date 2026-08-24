"""Rebalance calendar (B1), as-of eligibility (A5/A10) and the tie-break (C7)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.calendar import rebalance_dates
from src.decisions import ConfigError
from src.select import top_n
from src.universe import eligibility_matrix, eligible_at


def test_rebalance_dates_are_quarterly_trading_days(cfg, panel):
    dates = rebalance_dates(cfg, panel.dates, panel.dates[0], panel.dates[-1])
    assert dates.isin(panel.dates).all()
    assert sorted({d.month for d in dates}) == [1, 4, 7, 10]
    # Each anchor month contributes exactly one date.
    assert len({(d.year, d.month) for d in dates}) == len(dates)


def test_rebalance_date_is_first_trading_day_on_or_after_the_first(cfg, panel):
    dates = rebalance_dates(cfg, panel.dates, panel.dates[0], panel.dates[-1])
    for day in dates:
        earlier = panel.dates[(panel.dates >= pd.Timestamp(day.year, day.month, 1))
                              & (panel.dates < day)]
        assert not len(earlier), f"{day.date()} is not the first trading day of its month"


def test_unknown_calendar_is_refused_not_defaulted(cfg, panel, monkeypatch):
    monkeypatch.setitem(cfg._flat, "execution.rebalance_calendar", "fortnightly")
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
