#!/usr/bin/env python3
"""
The `WGT` weight surface — feature weights x rebalance cadence x weighting rule.

Pre-registered in CLAUDE.md §11 before any cell was run, and closing §8's backlog item 1
(`DECISIONS.md` C9-r). Seven weight vectors through six frames, every cell through the
identical engine, each scored against a point-in-time noise band drawn 2026-08-28 — before
any of these arms existed. **No band is re-drawn here**; `05_v1.py` reads each cell's sigma
back and asserts it.

The claim this sweep makes is a *shape*: PNL monotone in momentum weight, replicated across
six independent frames. It is explicitly **not** an argmax claim — with 39 new arms, six or
so cells clearing +1 sigma is the null expectation (§11 prediction 6). The summary therefore
prints the surface, and flags the best cell only against `PIT-wk-drift`'s bar.

    python3 scripts/10_weight_sweep.py            # the full surface, ~2 min
    python3 scripts/10_weight_sweep.py --arms w8  # one vector across all six frames
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load  # noqa: E402
from src import features  # noqa: E402

# The ladder in ascending momentum weight, then the two isolation arms. Order is the
# monotonicity claim's own order, so a reader meets the prediction in the table's layout.
LADDER = ["base", "tilt", "w3", "w6", "w8"]
ISOLATION = ["no-dd", "no-id"]
CADENCES = ["quarterly_first_trading_day", "monthly_first_trading_day",
            "weekly_first_trading_day"]          # daily excluded by instruction
WEIGHTINGS = ["reset", "drift"]

# The submission's bar (§11 selection rule). An arm is adopted only if it clears this.
# A3-r 2026-09-02: the mandated universe is today's constituents and the selected cell is
# monthly + reset. The point-in-time bar was 48_551_143; it is not comparable and is not
# carried over.
SUBMISSION_PNL = 107_649_806
SUBMISSION = "MAND-mo-reset"


def cell_label(cadence: str, weighting: str) -> str:
    return f"{cadence.replace('_first_trading_day', '')}_{weighting}"


def run_arm(arm: str, cadence: str, weighting: str) -> float:
    cmd = [sys.executable, str(ROOT / "scripts" / "05_v1.py"), "--arm", arm,
           "--calendar", cadence, "--weighting", weighting]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        print(done.stdout[-3000:], file=sys.stderr)
        print(done.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"[wgt] 05_v1.py failed for {arm}/{cadence}/{weighting}")
    return time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arms", nargs="+", default=LADDER + ISOLATION)
    args = ap.parse_args()

    cfg = load()
    w_mom = {}
    for arm in args.arms:
        vector = __import__("importlib").import_module("05_v1").ARMS[arm]["weights"]
        cfg._flat["composite.active_weights"] = vector
        w_mom[arm] = features.weights(cfg)["mom_12_1"]

    rows: list[dict] = []
    t_all = time.time()
    for cadence in CADENCES:
        for weighting in WEIGHTINGS:
            cell = cell_label(cadence, weighting)
            for arm in args.arms:
                secs = run_arm(arm, cadence, weighting)
                m = pd.read_csv(ROOT / "output" / "v1" / f"{arm}_{cell}" / "metrics.csv",
                                index_col=0)["value"]
                rows.append({
                    "arm": arm, "cadence": cadence.replace("_first_trading_day", ""),
                    "weighting": weighting, "cell": cell, "w_mom": w_mom[arm],
                    "pnl": float(m["total_net_pnl"]),
                    "v0_pnl": float(m["v0_pnl_same_frame"]),
                    "delta_vs_v0": float(m["delta_vs_v0"]),
                    "z_vs_v0": float(m["z_vs_v0"]),
                    "band_sigma": float(m["band_sigma"]),
                    "sharpe": float(m["sharpe"]),
                    "max_drawdown": float(m["max_drawdown"]),
                    "turnover": float(m["turnover_annualised"]),
                    "costs": float(m["total_costs"]),
                    "churn": float(m["names_replaced_per_rebalance"]),
                    "seconds": secs,
                })
                print(f"  {cell:<18}{arm:<8} w_mom {w_mom[arm]:.3f}  "
                      f"PNL {rows[-1]['pnl']:>13,.0f}  z {rows[-1]['z_vs_v0']:+6.2f}")

    df = pd.DataFrame(rows)
    out = ROOT / "output" / "v1" / "wgt_summary.csv"
    df.to_csv(out, index=False)

    print()
    print("=" * 78)
    print("PREDICTION 1 — monotone in momentum weight, in every frame")
    print("=" * 78)
    ladder = [a for a in LADDER if a in args.arms]
    ok = 0
    for cell, b in df[df.arm.isin(ladder)].groupby("cell", sort=False):
        b = b.sort_values("w_mom")
        v0 = float(b["v0_pnl"].iloc[0])
        seq = list(b["pnl"]) + [v0]          # V0 is the w_mom = 1 endpoint of the curve
        mono = all(x < y for x, y in zip(seq, seq[1:]))
        ok += mono
        print(f"  {cell:<18}{'MONOTONE' if mono else 'NOT monotone':<14}"
              + "  ".join(f"{v/1e7:.2f}" for v in seq) + "  (Rs crore, ending at V0)")
    print(f"  -> holds in {ok} of {df[df.arm.isin(ladder)].cell.nunique()} frames")

    print()
    print("=" * 78)
    print("PREDICTION 3/4 — the three vectors at w_mom = 0.500")
    print("=" * 78)
    half = df[df.arm.isin(["tilt", "no-dd", "no-id"])]
    if not half.empty:
        piv = half.pivot(index="cell", columns="arm", values="pnl")
        for cell, r in piv.iterrows():
            t, nd, ni = r.get("tilt"), r.get("no-dd"), r.get("no-id")
            print(f"  {cell:<18}tilt {t:>12,.0f}  no-dd {nd:>12,.0f}  no-id {ni:>12,.0f}"
                  f"   tilt best: {'YES' if t >= max(nd, ni) else 'NO':<3}"
                  f"  no-dd>no-id: {'YES' if nd > ni else 'NO'}")

    print()
    print("=" * 78)
    print(f"PREDICTION 2 — does any arm clear {SUBMISSION} at Rs {SUBMISSION_PNL:,}?")
    print("=" * 78)
    best = df.loc[df.pnl.idxmax()]
    clears = df[df.pnl > SUBMISSION_PNL]
    print(f"  best cell: {best['arm']} @ {best['cell']}  Rs {best['pnl']:,.0f}  "
          f"({best['pnl'] - SUBMISSION_PNL:+,.0f} vs the submission)")
    print(f"  arms clearing the bar: {len(clears)} of {len(df)}")
    print(f"  cells with z_vs_v0 > +1: {(df.z_vs_v0 > 1).sum()} of {len(df)} "
          f"(null expectation ~{0.16 * len(df):.0f} — §11 prediction 6)")
    print()
    print(f"[wgt] {len(df)} arms in {time.time() - t_all:.0f}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
