#!/usr/bin/env python3
"""
Phase B — acquire daily prices. Run once.

Idempotent: if today's snapshot already exists the script exits without making a
single network request. Snapshots are immutable (A14), so re-fetching is a deliberate
act — delete the file first.

    python3 scripts/01_fetch.py
    python3 scripts/01_fetch.py --as-of 2026-08-24   # target an existing snapshot
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import fetch  # noqa: E402
from src.config import load  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", default=fetch.today_stamp())
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    cfg = load(args.config) if args.config else load()
    as_of = args.as_of

    paths = {k: fetch.snapshot_path(cfg, k, as_of)
             for k in ("universe", "prices", "indices")}

    if all(p.exists() for p in paths.values()):
        print(f"[fetch] snapshot {as_of} already on disk — no network calls made")
        for kind, path in paths.items():
            print(f"        {kind:9s} {path}")
        return 0

    pending = cfg.pending()
    print(f"[fetch] config OK · {len(pending)} config keys still blocked on decisions")
    print(f"[fetch] as_of={as_of}  window={cfg['fetch.start']} -> {as_of}")

    # ── universe ─────────────────────────────────────────────────────────────
    universe = fetch.fetch_universe(cfg)
    print(f"[fetch] universe: {len(universe)} names "
          f"({universe.index_name.value_counts().to_dict()})")
    if not paths["universe"].exists():
        paths["universe"].parent.mkdir(parents=True, exist_ok=True)
        universe.to_csv(paths["universe"], index=False)

    # ── prices ───────────────────────────────────────────────────────────────
    symbols = universe["yahoo_symbol"].tolist()
    if paths["prices"].exists():
        prices, _ = fetch.read_snapshot(paths["prices"])
        print(f"[fetch] prices already pinned: {len(prices):,} rows")
    else:
        print(f"[fetch] downloading {len(symbols)} symbols "
              f"in batches of {cfg['fetch.batch_size']} ...")
        prices = fetch.fetch_prices(cfg, symbols)
        fetch.write_snapshot(prices, paths["prices"], as_of, cfg["fetch.source"],
                             extra={"start": str(cfg["fetch.start"]),
                                    "n_symbols": str(prices.yahoo_symbol.nunique())})
        print(f"[fetch] prices: {len(prices):,} rows, "
              f"{prices.yahoo_symbol.nunique()} symbols")

    # ── indices ──────────────────────────────────────────────────────────────
    if paths["indices"].exists():
        indices, _ = fetch.read_snapshot(paths["indices"])
    else:
        indices = fetch.fetch_indices(cfg)
        fetch.write_snapshot(indices, paths["indices"], as_of, cfg["fetch.source"])
    print(f"[fetch] indices: {indices.yahoo_symbol.unique().tolist()}")

    # ── per-symbol log ───────────────────────────────────────────────────────
    log = (prices.groupby("yahoo_symbol")
                 .agg(n_rows=("date", "size"),
                      first_date=("date", "min"),
                      last_date=("date", "max"),
                      n_null_close=("close", lambda s: int(s.isna().sum())),
                      n_zero_volume=("volume", lambda s: int((s == 0).sum())))
                 .reset_index())
    got = set(prices.yahoo_symbol.unique())
    missing = sorted(set(symbols) - got)
    reports = cfg.resolved_path("paths.reports")
    reports.mkdir(parents=True, exist_ok=True)
    log.to_csv(reports / f"fetch_log_{as_of.replace('-', '')}.csv", index=False)

    print(f"[fetch] coverage: {len(got)}/{len(symbols)} symbols returned data")
    if missing:
        print(f"[fetch] MISSING: {missing}")
    print(f"[fetch] obs per symbol: min={log.n_rows.min()} "
          f"median={int(log.n_rows.median())} max={log.n_rows.max()}")
    print(f"[fetch] log -> {reports / f'fetch_log_{as_of.replace('-', '')}.csv'}")

    # Coverage is reported, not asserted: a name that IPO'd inside the window is
    # legitimately short, and A5 handles it by delaying eligibility. A symbol that
    # returned nothing at all is a real failure.
    assert not missing, f"{len(missing)} symbols returned no data: {missing}"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
