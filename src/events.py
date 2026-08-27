"""
Forced mid-cycle exits — one mechanism, two event sources.

An *event* is a single instruction: sell the whole position in one name, at the open of
one date, and hold the proceeds as cash until the next rebalance. Nothing else in either
engine trades between rebalance dates, so this is the only exception, and it is declared
in data rather than inferred in code.

Two things generate events:

- **A16 ex-dates.** A demerger we cannot model prints a price fall the holder never
  suffered: they received shares in the spun-off entity that a price-only panel cannot
  see. We sell on the last session that still trades *cum* entitlement — see
  `_last_cum_session`, where the off-by-one is load-bearing — and forgo whatever the
  spun-off entity was worth rather than book a loss that did not happen.
- **A18 index exits.** A name that leaves the index on its effective date is sold that
  day, so the book never holds outside the universe the mandate names.

Both are *causal*. An ex-date and an index-review effective date are each published weeks
ahead, so a real investor standing on that morning already knows.

What this deliberately does **not** do is change eligibility. A demerged name keeps
trading and stays in the panel; its 12-1 momentum will span the discontinuity and read as
a large fall, so a momentum rule ranks it near the bottom and simply does not re-buy it.
That is self-correcting in the conservative direction, and it needs no extra parameter.
"""

from __future__ import annotations

import pandas as pd

from src.clean import Panel
from src.config import Config
from src.decisions import ConfigError

#: The two modes B10 allows. `hold_through` is the pre-2026-08-28 behaviour, kept so the
#: rule can be switched off in config rather than by editing an engine.
MODES = ("hold_through", "exit_at_ex_date")


def _last_cum_session(days: pd.DatetimeIndex, ex_date: pd.Timestamp):
    """
    The last session that still trades *cum* entitlement, or None if it precedes the panel.

    This is the whole subtlety of the rule, and getting it wrong silently does nothing.
    The ex-date's own **open** is already ex-entitlement: VEDL closed at 773.60 on
    2026-04-29 and opened at 289.50 on 2026-04-30, a -62.6% gap. Because the engine fills
    at opens (B2), selling at the open of the ex-date books the entire phantom loss
    rather than avoiding it. The exit must therefore fire one session earlier.

    The cost is explicit and conservative: we give up the final cum session's intraday
    move, and we forgo whatever the spun-off entity was worth. Both err against us, which
    is the right direction for a distortion we cannot measure.

    An ex-date is an exchange fact and need not be one of our sessions (A8 drops phantom
    bars), so the boundary is found by search rather than assumed present.
    """
    earlier = days[days < ex_date]
    return earlier[-1] if len(earlier) else None


def ex_date_events(cfg: Config, panel: Panel,
                   overrides: pd.DataFrame) -> dict[pd.Timestamp, list[str]]:
    """
    B10: force-exit every name carrying a corporate action we could not correct.

    Reads the *unapplied* rows of the A16 table — the ones where NSE publishes no
    entitlement ratio, so `clean.apply_corporate_actions` deliberately left the price
    alone. Those are exactly the rows that would otherwise put a phantom loss in the NAV.
    """
    mode = cfg["execution.corporate_action_mode"]
    if mode not in MODES:
        raise ConfigError(f"B10 allows {list(MODES)}; got {mode!r}")
    if mode == "hold_through":
        return {}

    known = set(panel.isins)
    events: dict[pd.Timestamp, list[str]] = {}
    uncorrected = overrides[~overrides["applied"].astype(bool)]
    for row in uncorrected.itertuples():
        if row.isin not in known:
            # A name flagged in the table but absent from this universe. Not an error --
            # the table outlives any one universe -- but it must not silently vanish.
            continue
        session = _last_cum_session(panel.dates, pd.Timestamp(row.ex_date))
        if session is None:
            continue
        events.setdefault(session, []).append(row.isin)
    return events


def merge(*tables: dict[pd.Timestamp, list[str]]) -> dict[pd.Timestamp, list[str]]:
    """Combine event tables from different sources, de-duplicating per date.

    Two sources can name the same (date, name) — an index exit that coincides with a
    demerger is the obvious case — and selling twice would book the proceeds twice.
    """
    out: dict[pd.Timestamp, list[str]] = {}
    for table in tables:
        for day, names in table.items():
            bucket = out.setdefault(pd.Timestamp(day), [])
            for name in names:
                if name not in bucket:
                    bucket.append(name)
    return {d: sorted(v) for d, v in sorted(out.items())}
