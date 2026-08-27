#!/usr/bin/env python3
"""
Phase 1 — raw snapshot to validated panel plus a data quality report.

Reads only from data/raw/. Never touches the network.

    python3 scripts/02_clean.py
    python3 scripts/02_clean.py --as-of 2026-08-24 --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import calendar, clean, fetch  # noqa: E402
from src.config import load  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", default=fetch.today_stamp())
    ap.add_argument("--force", action="store_true",
                    help="delete an existing clean panel first (A14 blocks overwrite)")
    args = ap.parse_args()

    cfg = load()
    as_of = args.as_of
    stamp = as_of.replace("-", "")

    raw = fetch.snapshot_path(cfg, "prices", as_of)
    uni_path = fetch.snapshot_path(cfg, "universe", as_of)
    if not raw.exists():
        print(f"[clean] no raw snapshot for {as_of}: run scripts/01_fetch.py first")
        return 1

    prices, meta = fetch.read_snapshot(raw)
    universe = pd.read_csv(uni_path)
    print(f"[clean] raw snapshot as_of={meta['as_of']} source={meta['source']} "
          f"rows={len(prices):,}")

    # ── A8 ───────────────────────────────────────────────────────────────────
    days = calendar.trading_days(cfg, prices)
    phantoms = calendar.phantom_days(cfg, prices)
    print(f"[clean] calendar: {len(days)} trading days "
          f"({days[0].date()} -> {days[-1].date()}); "
          f"{len(phantoms)} phantom days excluded: "
          f"{[d.date().isoformat() for d in phantoms]}")

    # ── A16 before anything is flagged ───────────────────────────────────────
    overrides = clean.load_overrides(cfg)
    mem_path = clean.membership_path(cfg, as_of)
    spans = pd.read_csv(mem_path) if mem_path.exists() else None
    if spans is None:
        print(f"[clean] no membership table at {mem_path.name} — every name treated as "
              f"a member on every date (pre-A17 behaviour)")
    else:
        print(f"[clean] membership: {len(spans)} spans over "
              f"{spans['symbol'].nunique()} symbols (A17, point-in-time)")
    panel = clean.build_panel(cfg, prices, universe, days, spans)
    panel = clean.apply_corporate_actions(panel, overrides)
    applied = overrides[overrides["applied"].astype(bool)]
    print(f"[clean] corporate actions: {len(applied)} corrections applied, "
          f"{len(overrides) - len(applied)} confirmed but left uncorrected")
    for row in overrides.itertuples():
        mark = "applied " if row.applied else "FLAGGED "
        ratio = f"ratio {row.ratio}" if row.applied else "no published ratio"
        print(f"           {mark} {row.symbol:11s} {row.action:10s} "
              f"ex {row.ex_date}  {ratio}")

    # ── A9 -> A10 -> A11 -> A12 ──────────────────────────────────────────────
    panel = clean.fill_missing(cfg, panel)
    panel = clean.flag_zero_volume(cfg, panel)
    panel = clean.flag_stale(cfg, panel)
    panel = clean.flag_bad_ticks(cfg, panel)
    print(f"[clean] gaps filled: {int(panel.filled.sum().sum())} | "
          f"zero-volume name-days: {int(((panel.volume == 0) & panel.close.notna()).sum().sum())} | "
          f"stale-flagged names: {int(panel.stale.any().sum())} | "
          f"extreme returns flagged: {int(panel.bad_tick.sum().sum())}")

    # ── persist ──────────────────────────────────────────────────────────────
    out = cfg.resolved_path("paths.data_clean") / f"panel_{stamp}.parquet"
    if out.exists() and args.force:
        out.unlink()
    if out.exists():
        print(f"[clean] {out.name} exists and is immutable (A14) — pass --force to replace")
    else:
        long = pd.concat(
            [getattr(panel, f).stack(future_stack=True).rename(f)
             for f in ("open", "high", "low", "close", "volume",
                       "tradeable", "stale", "bad_tick", "filled", "member")],
            axis=1).reset_index().rename(columns={"level_0": "date", "level_1": "isin"})
        fetch.write_snapshot(long, out, as_of, cfg["fetch.source"],
                             extra={"calendar": cfg["clean.trading_calendar"],
                                    "n_days": str(len(days)),
                                    "n_names": str(len(panel.isins)),
                                    "overrides_applied": str(len(applied))})
        print(f"[clean] panel -> {out}  ({len(long):,} rows)")

    report = clean.quality_report(cfg, panel, prices, phantoms, overrides, as_of)
    rp = cfg.resolved_path("paths.reports") / "data_quality.md"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(report)
    print(f"[clean] report -> {rp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
