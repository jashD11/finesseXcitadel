"""
Cleaning and panel construction: raw snapshot -> validated panel + quality report.

Every rule here is frozen in DECISIONS.md (A7-A13, A16) and parameterised in
config.yaml. Nothing in this module chooses a threshold on its own.

The ordering matters. Corporate actions are corrected *before* anything is flagged,
because an uncorrected bonus looks exactly like a bad tick; the calendar is settled
*before* gaps are counted, because on the wrong calendar the panel appears to have
gaps it does not have.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src import calendar
from src.config import Config
from src.decisions import ConfigError

_FIELDS = ("open", "high", "low", "close", "volume")
_PRICE_FIELDS = ("open", "high", "low", "close")


@dataclass
class Panel:
    """Wide (date x ISIN) frames plus the flags the report and the backtest read."""
    close: pd.DataFrame
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    volume: pd.DataFrame
    tradeable: pd.DataFrame   # A10 — screened on t-1 volume
    stale: pd.DataFrame       # A11 — report-only
    bad_tick: pd.DataFrame    # A12 — flag, never corrected
    filled: pd.DataFrame      # A9 — where a price was carried forward
    member: pd.DataFrame      # A17 — point-in-time index membership (either index)
    symbols: pd.Series        # ISIN -> ticker, for display only (A7)

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.close.index

    @property
    def isins(self) -> pd.Index:
        return self.close.columns


# ── Corporate-action overrides (A16) ─────────────────────────────────────────


def load_overrides(cfg: Config) -> pd.DataFrame:
    """
    Read the override table and refuse anything that is not evidence-carrying.

    A16 is explicit that a correction is applied only where an external record
    confirms both the action and its ratio, so an unsourced row is a hard error
    rather than a warning.
    """
    path = Path(cfg["clean.corporate_action_overrides"])
    if not path.is_absolute():
        from src.config import REPO_ROOT
        path = REPO_ROOT / path
    if not path.exists():
        raise ConfigError(f"corporate action override table missing: {path}")

    df = pd.read_csv(path)
    required = {"symbol", "isin", "action", "ex_date", "ratio", "boundary_date",
                "applied", "verified_on", "source", "note"}
    missing = required - set(df.columns)
    if missing:
        raise ConfigError(f"override table missing columns: {sorted(missing)}")

    unsourced = df[df["source"].isna() | (df["source"].astype(str).str.strip() == "")]
    if len(unsourced):
        raise ConfigError(
            f"override rows with no source: {unsourced['symbol'].tolist()}. "
            f"A16 requires an external record; a price drop is not evidence of its "
            f"own cause."
        )

    active = df[df["applied"].astype(bool)]
    for col in ("ratio", "boundary_date"):
        blank = active[active[col].isna() | (active[col].astype(str).str.strip() == "")]
        if len(blank):
            raise ConfigError(
                f"applied override rows with no {col}: {blank['symbol'].tolist()}"
            )
    return df


def apply_corporate_actions(panel: Panel, overrides: pd.DataFrame) -> Panel:
    """
    Back-adjust history Yahoo failed to adjust.

    The measured defect is systematic: Yahoo back-adjusts only from 1 January of the
    split's year, so everything before that boundary is left at the pre-bonus level.
    The fix divides prices strictly before ``boundary_date`` by the action's ratio.

    Back-adjustment rescales a level, which is information-free. Any change to a
    return other than the one at the boundary would be a real defect, so it is
    asserted rather than assumed.
    """
    active = overrides[overrides["applied"].astype(bool)]
    if not len(active):
        return panel

    before = panel.close.pct_change()
    boundaries: list[tuple[str, pd.Timestamp]] = []

    for row in active.itertuples():
        isin = row.isin
        if isin not in panel.close.columns:
            raise ConfigError(f"override for {row.symbol} ({isin}) is not in the universe")
        ratio = float(row.ratio)
        boundary = pd.Timestamp(row.boundary_date)
        mask = panel.close.index < boundary
        if not mask.any():
            raise ConfigError(f"override for {row.symbol}: no dates before {boundary.date()}")
        for field in _PRICE_FIELDS:
            frame = getattr(panel, field)
            frame.loc[mask, isin] = frame.loc[mask, isin] / ratio
        # Volume moves the other way: the same rupee turnover, more shares.
        panel.volume.loc[mask, isin] = panel.volume.loc[mask, isin] * ratio
        boundaries.append((isin, boundary))

    _assert_returns_preserved(before, panel.close.pct_change(), boundaries)
    return panel


def _assert_returns_preserved(before: pd.DataFrame, after: pd.DataFrame,
                              boundaries: list[tuple[str, pd.Timestamp]],
                              tol: float = 1e-9) -> None:
    """Only the return at each boundary may change. Everything else is untouched."""
    diff = (before - after).abs()
    for isin, boundary in boundaries:
        pos = diff.index.searchsorted(boundary)
        if pos < len(diff.index):
            diff.iloc[pos, diff.columns.get_loc(isin)] = 0.0
    worst = float(np.nanmax(diff.to_numpy())) if diff.size else 0.0
    assert worst < tol, f"back-adjustment changed a non-boundary return by {worst:.2e}"


# ── Panel construction ───────────────────────────────────────────────────────


def build_panel(cfg: Config, prices: pd.DataFrame, universe: pd.DataFrame,
                days: pd.DatetimeIndex, spans: pd.DataFrame | None = None) -> Panel:
    """
    Long raw prices -> wide (date x ISIN) frames on the A8 calendar.

    Keyed by ISIN (A7) because tickers get renamed. The ticker is kept alongside for
    display and is never used to join anything.

    ``spans`` is the point-in-time membership table (A17). Passing None marks every name
    a member on every date, which is exactly the pre-A17 behaviour and is what the
    synthetic test panel wants -- it has no index membership to speak of.
    """
    if cfg["universe.identity_key"] != "isin":
        raise ConfigError(f"A7 froze 'isin'; got {cfg['universe.identity_key']!r}")

    key = universe.set_index("yahoo_symbol")["isin"]
    df = prices[prices["date"].isin(days)].copy()
    df["isin"] = df["yahoo_symbol"].map(key)
    unmapped = df[df["isin"].isna()]["yahoo_symbol"].unique()
    assert not len(unmapped), f"prices for symbols outside the universe: {list(unmapped)}"

    frames = {f: df.pivot_table(index="date", columns="isin", values=f).reindex(
        index=days, columns=universe["isin"]) for f in _FIELDS}

    blank = {k: pd.DataFrame(False, index=days, columns=universe["isin"]) for k in
             ("tradeable", "stale", "bad_tick", "filled")}
    symbols = universe.set_index("isin")["symbol"]
    if spans is None:
        member = pd.DataFrame(True, index=days, columns=universe["isin"])
    else:
        from src.membership import matrix
        member = matrix(spans, symbols, days).reindex(columns=universe["isin"])
    return Panel(symbols=symbols, member=member, **frames, **blank)


def panel_path(cfg: Config, as_of: str) -> Path:
    """Where `scripts/02_clean.py` persists the panel for a given snapshot date."""
    return cfg.resolved_path("paths.data_clean") / f"panel_{as_of.replace('-', '')}.parquet"


def membership_path(cfg: Config, as_of: str) -> Path:
    """The point-in-time membership table for a snapshot (A17)."""
    return (cfg.resolved_path("paths.data_raw")
            / f"membership_{as_of.replace('-', '')}.csv")


def universe_path(cfg: Config, as_of: str) -> Path:
    return cfg.resolved_path("paths.data_raw") / f"universe_{as_of.replace('-', '')}.csv"


def load_panel(cfg: Config, panel_file: Path, universe_file: Path) -> Panel:
    """
    Read the persisted panel back into the wide ``Panel`` the analysis layer expects.

    `scripts/02_clean.py` stacks the panel to long form to persist it; every consumer
    wants wide frames again. This is the inverse of that stack, pivoting through the
    same ``universe["isin"]`` column order that `build_panel` used so the two paths
    cannot drift apart.

    Takes explicit paths rather than reaching for `fetch.read_snapshot`: CLAUDE.md §12
    keeps the network module out of the analysis path, and importing it here would put
    it back in transitively. The two lines of provenance-metadata reading are duplicated
    from `fetch.read_snapshot` for that reason.
    """
    if not panel_file.exists():
        raise ConfigError(f"no clean panel at {panel_file}: run scripts/02_clean.py first")

    schema = pq.read_schema(panel_file)
    meta = {k.decode(): v.decode() for k, v in (schema.metadata or {}).items()
            if not k.startswith(b"pandas")}
    if "as_of" not in meta:
        raise ConfigError(f"{panel_file} has no as_of stamp - not a pinned snapshot")

    long = pd.read_parquet(panel_file)
    universe = pd.read_csv(universe_file)
    isins = pd.Index(universe["isin"])

    # `.pivot`, not `.pivot_table`: the clean panel has exactly one row per (date, isin),
    # and pivot_table would aggregate the four boolean flag columns into floats.
    frames = {f: long.pivot(index="date", columns="isin", values=f).reindex(columns=isins)
              for f in _FIELDS}
    flags = {f: long.pivot(index="date", columns="isin", values=f)
                     .reindex(columns=isins).astype(bool)
             for f in ("tradeable", "stale", "bad_tick", "filled", "member")}

    panel = Panel(symbols=universe.set_index("isin")["symbol"], **frames, **flags)

    assert panel.close.index.is_monotonic_increasing and panel.close.index.is_unique
    assert len(panel.isins) == int(cfg["universe.expected_total"]), \
        f"expected {cfg['universe.expected_total']} names, got {len(panel.isins)}"
    if "n_days" in meta:
        assert len(panel.dates) == int(meta["n_days"]), \
            f"panel has {len(panel.dates)} days, snapshot metadata says {meta['n_days']}"

    # A9: on the A8 calendar every name is contiguous from its first print. A NaN after
    # a name has listed would mean a gap the cleaning layer reported as absent.
    listed = panel.close.notna().cummax()
    interior = int((panel.close.isna() & listed).sum().sum())
    assert interior == 0, f"{interior} interior NaN closes in the panel"

    return panel


def fill_missing(cfg: Config, panel: Panel) -> Panel:
    """
    Forward-fill an interior gap, capped (A9). Never backward.

    A ``bfill`` moves a future price into a past cell. ``tests/test_causality.py``
    greps ``src/`` to prove none exists anywhere in this codebase.
    """
    cap = int(cfg["clean.ffill_max_days"])
    worst = _max_interior_gap(panel.close)
    assert worst <= cap, f"interior gap of {worst} days exceeds the A9 cap of {cap}"

    was_na = panel.close.isna() & _listed(panel.close)
    for field in _PRICE_FIELDS:
        setattr(panel, field, getattr(panel, field).ffill(limit=cap))
    panel.volume = panel.volume.where(~was_na, 0.0)
    panel.filled = was_na & panel.close.notna()

    remaining = int((panel.close.isna() & _listed(panel.close)).sum().sum())
    assert remaining == 0, f"{remaining} interior NaN closes survived the fill"
    return panel


def _listed(close: pd.DataFrame) -> pd.DataFrame:
    """True from each name's first print onward. Pre-listing cells are not gaps."""
    return close.notna().cummax()


def _max_interior_gap(close: pd.DataFrame) -> int:
    worst = 0
    listed = _listed(close)
    gap = (close.isna() & listed)
    for col in gap.columns:
        run = 0
        for flag in gap[col].to_numpy():
            run = run + 1 if flag else 0
            worst = max(worst, run)
    return worst


# ── Flags ────────────────────────────────────────────────────────────────────


def flag_zero_volume(cfg: Config, panel: Panel) -> Panel:
    """
    A10: a name that traded nothing yesterday cannot be filled today.

    The screen reads *t-1* deliberately. Reading *t*'s volume before *t*'s open would
    be look-ahead, and the whole book is executed at the open.
    """
    if cfg["clean.zero_volume_policy"] != "not_tradeable_prev_day":
        raise ConfigError(f"A10 froze 'not_tradeable_prev_day'; "
                          f"got {cfg['clean.zero_volume_policy']!r}")
    panel.tradeable = (panel.volume.shift(1) > 0) & panel.close.notna()
    return panel


def flag_stale(cfg: Config, panel: Panel) -> Panel:
    """A11: runs of N or more identical consecutive closes. Report-only in V0."""
    n = int(cfg["clean.stale_price_n"])
    out = pd.DataFrame(False, index=panel.close.index, columns=panel.close.columns)
    for col in panel.close.columns:
        series = panel.close[col]
        same = series.eq(series.shift(1)) & series.notna()
        group = (~same).cumsum()
        size = same.groupby(group).transform("size") + 1
        out[col] = same & (size >= n)
    panel.stale = out
    return panel


def flag_bad_ticks(cfg: Config, panel: Panel) -> Panel:
    """
    A12: flag |daily return| above the threshold. Never corrected.

    This is a corporate-action detector, not a return filter. Winsorising would edit
    the PNL being scored.
    """
    thr = float(cfg["clean.bad_tick_abs_return"])
    panel.bad_tick = panel.close.pct_change().abs() > thr
    return panel


# ── Report ───────────────────────────────────────────────────────────────────


def quality_report(cfg: Config, panel: Panel, prices: pd.DataFrame,
                   phantoms: pd.DatetimeIndex, overrides: pd.DataFrame,
                   as_of: str) -> str:
    """Markdown for data/reports/data_quality.md. Ends Phase 1."""
    sym = panel.symbols
    listed = _listed(panel.close)
    first = panel.close.apply(lambda c: c.first_valid_index())
    late = first[first > panel.dates[5]]
    zv = ((panel.volume == 0) & listed)
    win = (panel.dates >= pd.Timestamp(cfg["mandate.start"])) & \
          (panel.dates <= pd.Timestamp(cfg["mandate.end"]))
    ticks = panel.bad_tick.loc[win]

    applied = overrides[overrides["applied"].astype(bool)]
    flagged = overrides[~overrides["applied"].astype(bool)]

    # A8's two exclusion routes, split back out: "no name traded" and "hand-excluded on
    # evidence" are different claims, and blending them would hide the second.
    overridden = calendar.overridden_days(cfg)
    zero_volume = phantoms.difference(overridden)
    phantom_rows = pd.read_csv(cfg["clean.phantom_day_overrides"])
    overrides_block = "\n".join(
        f"- `{r.date}` — **{r.reason}**. {r.evidence}"
        for r in phantom_rows[phantom_rows["applied"].astype(bool)].itertuples()
    ) or "_none_"

    def tbl(df: pd.DataFrame, cols: list[str]) -> str:
        head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
        rows = "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n"
                       for _, r in df.iterrows())
        return head + rows

    stale_names = [sym[i] for i in panel.stale.columns if panel.stale[i].any()]

    return f"""# Data Quality Report

Generated from snapshot `as_of = {as_of}`. Every figure below is computed by
`scripts/02_clean.py` from `data/raw/`; none is hand-entered.

## Panel

| | |
|---|---|
| Trading days (A8) | **{len(panel.dates)}** |
| Window | {panel.dates[0].date()} to {panel.dates[-1].date()} |
| Names | {len(panel.isins)} |
| Cells | {len(panel.dates) * len(panel.isins):,} |
| Identity key (A7) | ISIN |

## Calendar (A8)

Union of days any name printed, minus days that are not trading sessions.
**{len(phantoms)} days excluded** by two separate routes, reported separately because
they rest on different evidence.

**Route 1 — the volume filter ({len(zero_volume)} days).** Yahoo emitted a bar with a
price on 189-200 names and zero volume on every one:

{", ".join(f"`{d.date()}`" for d in zero_volume)}

All four fall inside the 2026 stress window. Two genuine Diwali Muhurat sessions
(2019-10-27, 2020-11-14) are retained: they carry real volume across 174-178 names,
and `^NSEI` omits both.

**Route 2 — hand-excluded on evidence ({len(overridden)} day{"" if len(overridden)==1 else "s"}).** The volume filter
keeps these, because "at least one name traded" is satisfied, but they are not sessions.
Listed in `{cfg["clean.phantom_day_overrides"]}` with the evidence per row; a row acts
only when `applied` is true.

{overrides_block}

This route exists because A8's rule is stated as *at least one* name trading, and a
stale bar can clear that bar with two. The threshold was not loosened into a
participation fraction — see `DECISIONS.md` A8. **The cost of that choice, stated
plainly: the next such bar is caught only if someone looks.** `A11` below (10+ identical
closes) is the tripwire most likely to catch one.

## Corporate actions (A12, A16)

**{len(applied)} corrections applied**, each confirmed by NSE's corporate-action
record *and* by the NSE-vs-Yahoo close ratio measured on three or more dates:

{tbl(applied, ["symbol", "action", "ex_date", "ratio", "boundary_date"])}
The defect is systematic: Yahoo back-adjusts only from 1 January of the action's
year, leaving earlier history at the pre-bonus level. All 79 recorded splits across
61 names were swept; only these three are affected.

**{len(flagged)} confirmed actions deliberately NOT corrected:**

{tbl(flagged, ["symbol", "action", "ex_date", "note"])}
For these, Yahoo's close matches the exchange exactly, so the traded price genuinely
fell — the holder received shares in the demerged entity. Back-adjusting would need
an entitlement ratio NSE does not publish in this feed, and inventing one would be a
fabricated number. This is a known limitation affecting 2 of {len(panel.isins)} names.

## Gaps (A9)

Interior gaps after each name's first print: **{int((panel.close.isna() & listed).sum().sum())}**.
Forward-fill cap is {cfg['clean.ffill_max_days']} days and currently fires
**{int(panel.filled.sum().sum())}** times. On the A8 calendar every name is contiguous
from listing; the apparent gaps seen on a union calendar were an artefact of the four
phantom days.

**{len(late)} names list after the window opens**, earliest
{", ".join(f"{sym[i]} ({first[i].date()})" for i in late.sort_values().index[:5])}.
A5 delays their eligibility rather than excluding them.

## Zero-volume days (A10)

**{int(zv.sum().sum())}** name-days where a price printed but nothing traded, across
{int((zv.sum() > 0).sum())} names. Concentrated in
{", ".join(f"{sym[i]} ({int(zv[i].sum())})" for i in zv.sum().nlargest(4).index)}.
Tradeability is screened on the **previous** day's volume, so the flag never reads
data from the day it gates.

## Stale prices (A11)

Runs of {cfg['clean.stale_price_n']}+ identical consecutive closes.
Names flagged: **{len(stale_names)}** — {", ".join(stale_names) if stale_names else "none"}.
Report-only; a flagged name is not removed from eligibility.

## Extreme returns (A12)

Within the scoring window, **{int(ticks.sum().sum())}** daily returns exceed
±{cfg['clean.bad_tick_abs_return']:.0%}, across {int((ticks.sum() > 0).sum())} names.
These are flagged, never corrected — winsorising would edit the PNL being scored.
After the A16 corrections the remainder are genuine market events (the 2024-06-04
election crash, ADANIENT in Feb-2023, INDUSINDBK in Mar-2025) plus the two
uncorrected demergers.
"""
