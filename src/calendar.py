"""
Trading calendar and rebalance-date arithmetic.

Everything downstream indexes off one calendar, so a wrong answer here is a wrong
answer everywhere. Both rules it needs are still open.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import Config
from src.decisions import ConfigError


def overridden_days(cfg: Config) -> pd.DatetimeIndex:
    """
    A8 rider: days excluded by hand because the volume filter cannot see them.

    A8 drops a day only when *no* name in the universe traded. A stale Yahoo bar where two
    names printed volume and 191 closes simply repeat the previous session clears that bar
    and is not a trading day either. Those are listed explicitly, with the evidence in the
    file, rather than by loosening A8 into a fitted participation threshold — see
    `docs/DECISIONS.md` A8.

    Evidence-carrying like the corporate-action overrides: a row is excluded only when
    ``applied`` is true, so a suspected day can be recorded without acting on it.
    """
    path = Path(cfg["clean.phantom_day_overrides"])
    if not path.exists():
        raise ConfigError(
            f"phantom-day override file {path} is missing; A8's rider names it. "
            f"An empty file with a header is how you say 'no overrides'."
        )
    frame = pd.read_csv(path)
    required = {"date", "reason", "evidence", "applied"}
    missing = required - set(frame.columns)
    if missing:
        raise ConfigError(f"{path} is missing columns {sorted(missing)}")
    if frame.empty:
        return pd.DatetimeIndex([])
    active = frame[frame["applied"].astype(bool)]
    return pd.DatetimeIndex(sorted(pd.to_datetime(active["date"])))


def trading_days(cfg: Config, prices: pd.DataFrame) -> pd.DatetimeIndex:
    """
    The authoritative date index. Every series is reindexed onto this.

    A8 (frozen): the union of days on which any universe name printed, minus days on
    which *no* name in the universe had volume. Those are market holidays for which
    Yahoo emitted a bar anyway — four of them, all inside the 2026 stress window,
    carrying a price for 189-200 names with zero volume on every one.

    The volume filter is what separates them from the two genuine Diwali Muhurat
    sessions, which carry real volume across 174-178 names. Using ^NSEI as the
    calendar would discard both real sessions; ^CNX100 would discard nine.

    Takes the raw long-format frame, since the phantom days have to be identified
    before anything is reindexed onto a calendar that does not yet exist.
    """
    if cfg["clean.trading_calendar"] != "volume_filtered_union":
        raise ConfigError(
            f"unsupported trading_calendar {cfg['clean.trading_calendar']!r}; "
            f"A8 froze 'volume_filtered_union'"
        )
    traded = prices.groupby("date")["volume"].max()
    days = pd.DatetimeIndex(sorted(traded[traded > 0].index))
    days = days.difference(overridden_days(cfg))
    assert len(days), "no trading days survived the volume filter"
    assert days.is_monotonic_increasing and days.is_unique
    return days


def phantom_days(cfg: Config, prices: pd.DataFrame) -> pd.DatetimeIndex:
    """
    Every day excluded from the calendar, from both A8 routes.

    Reported as one series because that is what a reader wants; `quality_report` splits
    them back out by route, since "no name traded" and "hand-excluded on evidence" are
    very different claims and blending them would hide the second.
    """
    traded = prices.groupby("date")["volume"].max()
    zero_volume = pd.DatetimeIndex(sorted(traded[traded == 0].index))
    return zero_volume.union(overridden_days(cfg))


# B1 (amended 2026-08-27). docs/PROJECT.md §7 puts holding period among the levers that move
# the number, so alternative cadences are ledger trials. B1 used to claim any cadence was
# "a one-word config change, not a code path". That was true only for month-anchored
# cadences: weekly and daily have no representation in an anchor-*month* map at all. The
# dispatch now has two anchor families plus one literal, and the month family below is
# untouched — so `quarterly` still resolves to the identical 20 dates and V0 stays the
# baseline the ledger measures against.
_ANCHOR_MONTHS: dict[str, tuple[int, ...]] = {
    "monthly": tuple(range(1, 13)),
    "quarterly": (1, 4, 7, 10),
    "semiannual": (1, 7),
    "annual": (1,),
}
_WEEK_ANCHORED = ("weekly",)
_CALENDAR_SUFFIX = "_first_trading_day"

# Named as a bare literal rather than `daily_first_trading_day`, which would be nonsense:
# there is no anchor to be first on or after.
_EVERY_DAY = "every_trading_day"


def supported_calendars() -> list[str]:
    """Every accepted value of `execution.rebalance_calendar`. Single source for the
    error message and for the tests, so adding a cadence cannot leave either stale."""
    anchored = tuple(_ANCHOR_MONTHS) + _WEEK_ANCHORED
    return sorted([f + _CALENDAR_SUFFIX for f in anchored] + [_EVERY_DAY])


def rebalance_dates(cfg: Config, days: pd.DatetimeIndex,
                    start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """
    Rebalance calendar over [start, end], inclusive of the first rebalance.

    Each anchor month contributes the first trading day on or after the 1st of that
    month, so a holiday moves the date forward rather than dropping the rebalance.
    """
    name = str(cfg["execution.rebalance_calendar"])
    frequency = name[: -len(_CALENDAR_SUFFIX)] if name.endswith(_CALENDAR_SUFFIX) else None
    if name != _EVERY_DAY and frequency not in _ANCHOR_MONTHS and frequency not in _WEEK_ANCHORED:
        raise ConfigError(
            f"unsupported rebalance_calendar {name!r}; expected one of "
            f"{supported_calendars()}"
        )

    window = days[(days >= start) & (days <= end)]
    assert len(window), f"no trading days in [{start.date()}, {end.date()}]"

    if name == _EVERY_DAY:
        out = pd.DatetimeIndex(window)
    elif frequency in _WEEK_ANCHORED:
        # First trading day of each ISO week. ISO year-week is used rather than a plain
        # week number because the two disagree across a year boundary, which would merge
        # or split the turn-of-year week. Grouping preserves B1's actual load-bearing
        # property: a holiday moves the rebalance forward, it never drops one.
        iso = window.isocalendar()
        keys = pd.MultiIndex.from_arrays([iso["year"], iso["week"]])
        out = pd.DatetimeIndex(pd.Series(window, index=keys).groupby(level=[0, 1]).first())
        out = pd.DatetimeIndex(sorted(out))
    else:
        picked: list[pd.Timestamp] = []
        for year in range(start.year, end.year + 1):
            for month in _ANCHOR_MONTHS[frequency]:
                anchor = pd.Timestamp(year=year, month=month, day=1)
                after = window[window >= anchor]
                if len(after):
                    picked.append(after[0])
        out = pd.DatetimeIndex(sorted(set(picked)))
    assert len(out), f"no rebalance dates for {name!r} in the window"
    assert out.isin(days).all(), "a rebalance date is not a trading day"
    assert out.is_monotonic_increasing and out.is_unique
    assert out[0] >= start and out[-1] <= end
    return out


def formation_cutoff(day: pd.Timestamp, days: pd.DatetimeIndex, lag: int) -> pd.Timestamp:
    """
    Last date a signal for a rebalance at ``day`` is allowed to see.

    B2 is frozen: the signal runs through the close of t-1 and fills at the open of t.
    ``panel.loc[:t]`` includes t, so this exists to make the exclusion explicit and
    testable rather than a slicing convention someone has to remember.
    """
    try:
        pos = days.get_loc(day)
    except KeyError as exc:
        raise ValueError(f"{day.date()} is not a trading day") from exc
    if not isinstance(pos, int):
        raise ValueError(f"{day.date()} is not a unique trading day")
    if pos < lag:
        raise ValueError(f"{day} has fewer than {lag} prior trading days")
    return days[pos - lag]
