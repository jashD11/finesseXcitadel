"""
As-of eligibility: which names may be ranked on a given rebalance date.

A5/C6 are frozen — a name needs the complete lookback window ending at t-1, with no
partial windows and no imputation. C2 (frozen) defines that window as 252 trading days,
so a name is rankable only once it has 253 unbroken closes ending at the formation date.

Everything here is evaluated strictly before the rebalance date. Computing eligibility
against the whole panel would be look-ahead: a name that listed in 2022 would look
eligible in 2021 because the 2026 panel knows it exists.
"""

from __future__ import annotations

import pandas as pd

from src.calendar import formation_cutoff
from src.clean import Panel
from src.config import Config


def _window_bounds(cfg: Config, days: pd.DatetimeIndex, day: pd.Timestamp) -> tuple[int, int]:
    """
    Integer positions [first, cutoff] of the feature window for a rebalance at ``day``.

    ``cutoff`` is t-1 (B2 frozen), and the window reaches ``signal.lookback`` trading
    days further back. Returned as positions rather than dates so the caller slices the
    panel by position and never by label — ``panel.loc[:t]`` includes t.
    """
    lag = int(cfg["signal.formation_lag_days"])
    cutoff = formation_cutoff(day, days, lag)
    cutoff_pos = days.get_loc(cutoff)
    return cutoff_pos - int(cfg["signal.lookback"]), cutoff_pos


def eligible_at(cfg: Config, panel: Panel, day: pd.Timestamp) -> list[str]:
    """
    Names eligible for selection at ``day``.

    Two conditions, both frozen:

    - **A5/C6** — an unbroken close over the full feature window ending at t-1. No
      partial windows, no imputation: a name that has not been listed long enough sits
      the quarter out rather than being ranked on a made-up number.
    - **A10** — tradeable at ``day``, which `clean.flag_zero_volume` computed from
      *yesterday's* volume. A name that printed a price but traded nothing cannot be
      bought at this morning's open.
    """
    if not bool(cfg["eligibility.require_full_window"]):
        raise ValueError("A5/C6 froze require_full_window: true")

    days = panel.dates
    first, cutoff_pos = _window_bounds(cfg, days, day)
    if first < 0:
        return []

    window = panel.close.iloc[first:cutoff_pos + 1]
    complete = window.notna().all()
    tradeable = panel.tradeable.loc[day]
    names = panel.isins[(complete & tradeable).to_numpy()]
    return sorted(names)


def eligibility_matrix(cfg: Config, panel: Panel,
                       dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Boolean (rebalance date x ISIN). The noise band draws from these rows, so it samples
    exactly the frame the strategy chose from — sampling instead from names with full
    2021-25 history would leak survivorship into the band and make it too easy to beat.
    """
    matrix = pd.DataFrame(False, index=dates, columns=panel.isins)
    for day in dates:
        matrix.loc[day, eligible_at(cfg, panel, day)] = True

    floor = int(cfg["eligibility.min_eligible"])
    counts = matrix.sum(axis=1)
    assert (counts >= floor).all(), (
        f"eligible names fell below {floor} on "
        f"{[str(d.date()) for d in counts.index[counts < floor]]}"
    )
    return matrix
