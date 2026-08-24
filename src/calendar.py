"""
Trading calendar and rebalance-date arithmetic.

Everything downstream indexes off one calendar, so a wrong answer here is a wrong
answer everywhere. Both rules it needs are still open.
"""

from __future__ import annotations

import pandas as pd

from src.config import Config
from src.decisions import ConfigError, blocked


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
    assert len(days), "no trading days survived the volume filter"
    assert days.is_monotonic_increasing and days.is_unique
    return days


def phantom_days(prices: pd.DataFrame) -> pd.DatetimeIndex:
    """Days excluded by A8: a price printed, but not one name in the universe traded."""
    traded = prices.groupby("date")["volume"].max()
    return pd.DatetimeIndex(sorted(traded[traded == 0].index))


# B1 (frozen): the frequency is a config word, not a code path. CLAUDE.md §7 puts
# holding period among the two levers that actually move the number, so alternative
# cadences are queued as ledger trials — and a trial must be a one-word config change,
# or it is not comparable to V0 through the same engine.
_ANCHOR_MONTHS: dict[str, tuple[int, ...]] = {
    "monthly": tuple(range(1, 13)),
    "quarterly": (1, 4, 7, 10),
    "semiannual": (1, 7),
    "annual": (1,),
}
_CALENDAR_SUFFIX = "_first_trading_day"


def rebalance_dates(cfg: Config, days: pd.DatetimeIndex,
                    start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """
    Rebalance calendar over [start, end], inclusive of the first rebalance.

    Each anchor month contributes the first trading day on or after the 1st of that
    month, so a holiday moves the date forward rather than dropping the rebalance.
    """
    name = str(cfg["execution.rebalance_calendar"])
    frequency = name[: -len(_CALENDAR_SUFFIX)] if name.endswith(_CALENDAR_SUFFIX) else None
    if frequency not in _ANCHOR_MONTHS:
        raise ConfigError(
            f"unsupported rebalance_calendar {name!r}; expected one of "
            f"{sorted(f + _CALENDAR_SUFFIX for f in _ANCHOR_MONTHS)}"
        )

    window = days[(days >= start) & (days <= end)]
    assert len(window), f"no trading days in [{start.date()}, {end.date()}]"

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
