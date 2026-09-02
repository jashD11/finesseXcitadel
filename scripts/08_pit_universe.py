#!/usr/bin/env python3
"""
Build the point-in-time universe snapshot (A3 amended / A17).

Takes the existing as-of snapshot -- today's 200 constituents and their prices -- adds
every name that was a Nifty 100 or Midcap 100 constituent at any point in the scoring
window, and writes a new dated snapshot alongside it. The old snapshot is never touched:
A14 makes snapshots immutable, so this creates a new stamp rather than editing one.

    python3 scripts/08_pit_universe.py --as-of 2026-08-28

Network step, like 01_fetch. The historical price pull is cached to its own raw file, so
re-running makes no network calls (docs/PROJECT.md §2).
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import calendar, fetch, membership  # noqa: E402
from src.config import load  # noqa: E402

BASE_AS_OF = "2026-08-24"

#: Historical members Yahoo does not serve. Excluded and disclosed rather than guessed at.
#: Three (GSPL, GUJGASLTD, SONACOMS-class names) are still listed, so this is a gap in the
#: data source and not a delisting -- which is why it is stated rather than rationalised.
UNPRICEABLE_NOTE = ("no usable Yahoo series; excluded from the tradeable universe and "
                    "disclosed (docs/PROJECT.md §10)")


def historical_symbols(cfg, universe: pd.DataFrame, as_of: dt.date,
                       start: dt.date) -> tuple[pd.DataFrame, list[str]]:
    """Membership spans, plus the symbols that never appear in today's list."""
    today = {"nifty 100": set(universe.loc[universe.index_name == "NIFTY100", "symbol"]),
             "nifty midcap 100": set(universe.loc[universe.index_name == "MIDCAP100",
                                                  "symbol"])}
    spans = membership.membership_spans(cfg, today, as_of, start)
    extra = sorted(set(spans["symbol"]) - set(universe["symbol"]))
    return spans, extra


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", default="2026-08-28")
    args = ap.parse_args()
    cfg = load()
    as_of = args.as_of
    start = pd.Timestamp(cfg["mandate.start"]).date()
    base_date = dt.date.fromisoformat(BASE_AS_OF)

    prices, meta = fetch.read_snapshot(fetch.snapshot_path(cfg, "prices", BASE_AS_OF))
    universe = pd.read_csv(fetch.snapshot_path(cfg, "universe", BASE_AS_OF))
    print(f"[pit] base snapshot {meta['as_of']}: {len(prices):,} rows, "
          f"{universe['symbol'].nunique()} names")

    spans, extra = historical_symbols(cfg, universe, base_date, start)
    print(f"[pit] membership: {len(spans)} spans, {spans['symbol'].nunique()} symbols, "
          f"{len(extra)} never in today's list")

    hist_path = fetch.snapshot_path(cfg, "prices", as_of).with_name(
        f"prices_hist_{as_of.replace('-', '')}.parquet")
    if not hist_path.exists():
        import yfinance as yf
        warnings.filterwarnings("ignore")
        print(f"[pit] fetching {len(extra)} historical members from Yahoo...")
        raw = yf.download([s + cfg["universe.yahoo_suffix"] for s in extra],
                          start=cfg["fetch.start"], end="2026-08-25", progress=False,
                          auto_adjust=False, threads=True, group_by="ticker")
        frames = []
        for sym in extra:
            tick = sym + cfg["universe.yahoo_suffix"]
            if tick not in set(raw.columns.get_level_values(0)):
                continue
            block = raw[tick].dropna(how="all").reset_index()
            block.columns = [str(c).lower() for c in block.columns]
            block["yahoo_symbol"] = tick
            frames.append(block[["date", "yahoo_symbol", "open", "high", "low",
                                 "close", "volume"]])
        hist = pd.concat(frames, ignore_index=True)
        fetch.write_snapshot(hist, hist_path, as_of, "yfinance/historical-members")
        print(f"[pit] cached {len(hist):,} rows -> {hist_path.name}")
    hist, _ = fetch.read_snapshot(hist_path)

    priced = sorted(set(hist.loc[hist["close"].notna(), "yahoo_symbol"]
                        .str.replace(cfg["universe.yahoo_suffix"], "", regex=False)))
    missing = sorted(set(extra) - set(priced))
    print(f"[pit] historical members priced {len(priced)}, unpriceable {len(missing)}: "
          f"{missing}")

    # ── the extended universe: today's 200 plus every priced historical member ──
    rows = universe.to_dict("records")
    for sym in priced:
        rows.append({
            "index_name": "HISTORICAL", "company_name": sym, "industry": "",
            "symbol": sym, "series": "EQ",
            # A7 rider: no ISIN is published for a name that left the index, so a
            # synthetic stable key stands in. It cannot collide with a real ISIN and it
            # is never displayed -- `symbols` maps it straight back to the ticker.
            "isin": f"SYNTH{sym}",
            "yahoo_symbol": sym + cfg["universe.yahoo_suffix"],
        })
    extended = pd.DataFrame(rows)
    assert extended["isin"].is_unique and extended["symbol"].is_unique, \
        "extended universe has a duplicate identity key"

    keep = set(extended["yahoo_symbol"])
    merged = (pd.concat([prices, hist[hist["yahoo_symbol"].isin(keep)]], ignore_index=True)
                .drop_duplicates(subset=["date", "yahoo_symbol"])
                .sort_values(["date", "yahoo_symbol"])
                .reset_index(drop=True))

    # The calendar must not move. It is derived from every name that printed a volume, so
    # adding 82 series could in principle invent a session and silently shift every
    # positional lookback -- the exact failure mode the A8 rider was written about.
    before = calendar.trading_days(cfg, prices)
    after = calendar.trading_days(cfg, merged)
    assert after.equals(before), (
        f"the calendar moved: {len(before)} -> {len(after)} days. "
        f"Added: {sorted(set(after) - set(before))}"
    )
    print(f"[pit] calendar unchanged at {len(after)} trading days")

    fetch.write_snapshot(merged, fetch.snapshot_path(cfg, "prices", as_of), as_of,
                         f"{meta['source']}+historical-members")
    extended.to_csv(fetch.snapshot_path(cfg, "universe", as_of), index=False)
    spans.to_csv(fetch.snapshot_path(cfg, "universe", as_of)
                 .with_name(f"membership_{as_of.replace('-', '')}.csv"), index=False)
    print(f"[pit] wrote snapshot {as_of}: {len(merged):,} price rows, "
          f"{len(extended)} names ({len(priced)} historical)")
    print(f"[pit] unpriceable and excluded ({len(missing)}): {UNPRICEABLE_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
