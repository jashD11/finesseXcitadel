#!/usr/bin/env python3
"""
Add Nifty Smallcap 100 to the universe snapshot (A19, the `SMALL` arm).

The guidelines permit Nifty 100, Nifty Midcap 100 **and** Nifty Smallcap 100. This
project excluded the third by choice (docs/PROJECT.md §6); A19 tests that choice instead of
asserting it. The script takes the existing 283-name snapshot, adds today's Smallcap 100
list and the prices of every name it introduces, and writes a new dated snapshot. The
old one is never touched -- A14 makes snapshots immutable.

    python3 scripts/11_smallcap_universe.py --as-of 2026-09-02

Network step, like 01_fetch and 08_pit_universe. The price pull is cached to its own raw
file, so re-running makes no network calls (docs/PROJECT.md §2).

Two things this deliberately does **not** do:

- It does not reconstruct point-in-time Smallcap membership. The mandated rule is A3-r's
  `current_constituents`, and the 27 press releases behind A17 cover the two large-cap
  indices only. The snapshot therefore carries no membership table, and the loader
  refuses to run `point_in_time` against it rather than quietly treating every name as a
  member forever.
- It does not widen the corporate-action or liquidity treatment. Both are checked after
  the panel is built, and anything they surface is a decision (docs/PROJECT.md §2), not
  something this script resolves on its own.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import calendar, fetch  # noqa: E402
from src.config import load  # noqa: E402

BASE_AS_OF = "2026-08-28"
INDEX_NAME = "SMALLCAP100"


def smallcap_list(cfg) -> pd.DataFrame:
    """Today's published Smallcap 100 constituents, in the universe file's schema."""
    raw = fetch._get_csv(cfg["universe.smallcap100_url"], cfg["fetch.user_agent"],
                         cfg["fetch.max_retries"], cfg["fetch.request_pause_s"])
    raw.columns = [c.strip() for c in raw.columns]
    df = pd.DataFrame({
        "index_name": INDEX_NAME,
        "company_name": raw["Company Name"].str.strip(),
        "industry": raw["Industry"].str.strip(),
        "symbol": raw["Symbol"].str.strip(),
        "series": raw["Series"].str.strip(),
        "isin": raw["ISIN Code"].str.strip(),
    })
    per_list = int(cfg["universe.expected_per_list"])
    assert len(df) == per_list, f"{INDEX_NAME}: expected {per_list} rows, got {len(df)}"
    df["yahoo_symbol"] = df["symbol"] + cfg["universe.yahoo_suffix"]
    return df


def worst_interior_gap(series: pd.Series) -> int:
    """
    The longest run of missing sessions *after* a name's first print, in sessions.

    Leading NaNs are not a gap -- the name had simply not listed yet, which A5/C6 already
    handles by requiring a complete lookback window. Only holes inside a live series are
    a data defect, and a hole longer than the forward-fill cap cannot be filled without
    inventing prices (A19).

    Returns 0 for a series with no interior hole, including an all-NaN one.
    """
    listed = series.notna().cummax()
    interior = series.isna() & listed
    if not interior.any():
        return 0
    runs = interior.groupby((interior != interior.shift()).cumsum()).sum()
    return int(runs.max())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", default="2026-09-02")
    args = ap.parse_args()
    cfg = load()
    as_of = args.as_of

    prices, meta = fetch.read_snapshot(fetch.snapshot_path(cfg, "prices", BASE_AS_OF))
    universe = pd.read_csv(fetch.snapshot_path(cfg, "universe", BASE_AS_OF))
    print(f"[small] base snapshot {meta['as_of']}: {len(prices):,} rows, "
          f"{len(universe)} names "
          f"({universe.index_name.value_counts().to_dict()})")

    smallcap = smallcap_list(cfg)
    print(f"[small] Smallcap 100 list: {len(smallcap)} names")

    # A name can already be in the snapshot two ways: it is a current large/mid-cap (the
    # three lists must then be disjoint -- assert, do not assume), or it is one of the 83
    # HISTORICAL names that left the big indices and is now a smallcap. The second is a
    # *relabel*, not an addition: it is already priced and already in the universe file.
    current = set(universe.loc[universe.index_name.isin(["NIFTY100", "MIDCAP100"]),
                               "symbol"])
    overlap = sorted(set(smallcap["symbol"]) & current)
    assert not overlap, f"Smallcap 100 overlaps the two large-cap lists: {overlap}"

    known = set(universe["symbol"])
    relabel = sorted(set(smallcap["symbol"]) & known)
    fresh = smallcap[~smallcap["symbol"].isin(known)].reset_index(drop=True)
    print(f"[small] {len(relabel)} already priced as HISTORICAL (relabelled), "
          f"{len(fresh)} new names to fetch")

    price_path = fetch.snapshot_path(cfg, "prices", as_of).with_name(
        f"prices_small_{as_of.replace('-', '')}.parquet")
    if not price_path.exists():
        import yfinance as yf
        warnings.filterwarnings("ignore")
        print(f"[small] fetching {len(fresh)} smallcap series from Yahoo...")
        raw = yf.download(fresh["yahoo_symbol"].tolist(),
                          start=cfg["fetch.start"], end="2026-08-25", progress=False,
                          auto_adjust=False, threads=True, group_by="ticker")
        frames = []
        for tick in fresh["yahoo_symbol"]:
            if tick not in set(raw.columns.get_level_values(0)):
                continue
            block = raw[tick].dropna(how="all").reset_index()
            block.columns = [str(c).lower() for c in block.columns]
            block["yahoo_symbol"] = tick
            frames.append(block[["date", "yahoo_symbol", "open", "high", "low",
                                 "close", "volume"]])
        small = pd.concat(frames, ignore_index=True)
        fetch.write_snapshot(small, price_path, as_of, "yfinance/smallcap100")
        print(f"[small] cached {len(small):,} rows -> {price_path.name}")
    small, _ = fetch.read_snapshot(price_path)

    suffix = cfg["universe.yahoo_suffix"]
    priced = set(small.loc[small["close"].notna(), "yahoo_symbol"]
                 .str.replace(suffix, "", regex=False))
    missing = sorted(set(fresh["symbol"]) - priced)
    print(f"[small] priced {len(priced)}, unpriceable {len(missing)}: {missing}")

    # A9 admits a name only if its series is usable: an interior hole longer than the
    # forward-fill cap cannot be filled without inventing prices, and a stale price fed
    # into a 252-day momentum window is a fabricated signal, not a missing one. A name
    # that fails this is excluded and disclosed, exactly as the six unpriceable
    # historical members are (docs/PROJECT.md §10) -- the alternative, raising the cap, would
    # silently weaken a rule that has already caught real defects.
    #
    # This checks the names being *added*. The base snapshot was validated when it was
    # built and is immutable (A14).
    days = calendar.trading_days(cfg, prices)
    cap = int(cfg["clean.ffill_max_days"])
    gapped: dict[str, int] = {}
    for sym in sorted(priced):
        series = (small.loc[small["yahoo_symbol"] == sym + suffix]
                       .set_index("date")["close"].reindex(days))
        worst = worst_interior_gap(series)
        if worst > cap:
            gapped[sym] = worst
    if gapped:
        print(f"[small] excluded for interior gaps beyond the A9 cap of {cap} sessions: "
              + ", ".join(f"{s} ({n} sessions)" for s, n in sorted(gapped.items())))
    priced -= set(gapped)

    # ── the extended universe ────────────────────────────────────────────────
    extended = universe.copy()
    extended.loc[extended["symbol"].isin(relabel), "index_name"] = INDEX_NAME
    extended = pd.concat(
        [extended, fresh[fresh["symbol"].isin(priced)]], ignore_index=True)
    assert extended["isin"].is_unique and extended["symbol"].is_unique, \
        "extended universe has a duplicate identity key"

    keep = set(extended["yahoo_symbol"])
    merged = (pd.concat([prices, small[small["yahoo_symbol"].isin(keep)]],
                        ignore_index=True)
                .drop_duplicates(subset=["date", "yahoo_symbol"])
                .sort_values(["date", "yahoo_symbol"])
                .reset_index(drop=True))

    # The calendar must not move. It is the union of days any name printed a volume, so
    # ~100 new series could in principle invent a session, and a single extra session
    # slides every positional 252-day lookback -- exactly how the 2025-03-18 defect did
    # its damage (A8 rider). If this fires, the smallcap arm is not comparable to
    # anything already measured and that is a decision, not a fixup.
    before = calendar.trading_days(cfg, prices)
    after = calendar.trading_days(cfg, merged)
    assert after.equals(before), (
        f"the calendar moved: {len(before)} -> {len(after)} days. "
        f"Added: {sorted(set(after) - set(before))}; "
        f"removed: {sorted(set(before) - set(after))}"
    )
    print(f"[small] calendar unchanged at {len(after)} trading days")

    fetch.write_snapshot(merged, fetch.snapshot_path(cfg, "prices", as_of), as_of,
                         f"{meta['source']}+smallcap100")
    extended.to_csv(fetch.snapshot_path(cfg, "universe", as_of), index=False)
    counts = extended.index_name.value_counts().to_dict()
    scored = int((extended["index_name"] != "HISTORICAL").sum())
    print(f"[small] wrote snapshot {as_of}: {len(merged):,} price rows, "
          f"{len(extended)} names {counts}")
    print(f"[small] set universe.expected_total: {len(extended)} and "
          f"universe.expected_members: {scored} to run on this snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
