#!/usr/bin/env python3
"""
Phase 5: the `FREQ` grid — rebalance cadence x weighting rule.

Pre-registered in CLAUDE.md §11 before any cell was run. 4 cadences x {reset, drift},
every cell through the identical engine, each with its own noise band on its own calendar
and weighting (D2), scored twice (D11-r): `z_own` against that cell's band, `z_qtr`
against the frozen quarterly sigma so the rows may be compared to each other.

Writes one tidy row per cell to output/sweep/summary.csv. Nothing here selects a
configuration — §9 forbids consulting the 2026 column to choose, and this script reports
both windows side by side precisely so the separation stays visible.
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

CADENCES = ["quarterly_first_trading_day", "monthly_first_trading_day",
            "weekly_first_trading_day", "every_trading_day"]
WEIGHTINGS = ["reset", "drift"]

# D11-r: the fixed ruler. Every arm's z_qtr divides by this, so the column may be read
# down the table. Sourced from the NOISE-r1 ledger row, not recomputed, because a ruler
# that moves is not a ruler.
SIGMA_QUARTERLY = 5_092_127


def label_of(cadence: str, weighting: str) -> str:
    return f"{cadence.replace('_first_trading_day', '')}_{weighting}"


def run(script: str, cadence: str, weighting: str, window: str) -> float:
    cmd = [sys.executable, str(ROOT / "scripts" / script),
           "--window", window, "--calendar", cadence, "--weighting", weighting]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        print(done.stdout[-3000:], file=sys.stderr)
        print(done.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"[sweep] {script} failed for {cadence}/{weighting}/{window}")
    return time.time() - t0


def read_metrics(label: str, window: str) -> pd.Series:
    tag = "" if window == "main" else "_stress"
    path = ROOT / "output" / "sweep" / label / f"metrics{tag}.csv"
    return pd.read_csv(path, index_col=0)["value"]


def read_noise(label: str, window: str) -> pd.Series:
    tag = "" if window == "main" else "_stress"
    path = ROOT / "output" / "sweep" / label / f"noise_summary{tag}.csv"
    return pd.read_csv(path, index_col=0)["value"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--windows", nargs="+", default=["main", "stress"],
                    choices=("main", "stress"))
    ap.add_argument("--skip-noise", action="store_true",
                    help="backtests only; no band. For a fast structural check.")
    args = ap.parse_args()

    rows: list[dict] = []
    total = time.time()
    for cadence in CADENCES:
        for weighting in WEIGHTINGS:
            label = label_of(cadence, weighting)
            timing = {}
            for window in args.windows:
                timing[f"v0_{window}_s"] = run("03_v0.py", cadence, weighting, window)
                if not args.skip_noise:
                    timing[f"noise_{window}_s"] = run("04_noise.py", cadence,
                                                      weighting, window)
            row = {"label": label, "cadence": cadence.replace("_first_trading_day", ""),
                   "weighting": weighting}
            for window in args.windows:
                m = read_metrics(label, window)
                pre = "" if window == "main" else "stress_"
                row |= {f"{pre}pnl": m["total_net_pnl"],
                        f"{pre}total_return": m["total_return"],
                        f"{pre}cagr": m["annualised_return"],
                        f"{pre}sharpe": m["sharpe"],
                        f"{pre}mdd": m["max_drawdown"],
                        f"{pre}costs": m["total_costs"],
                        f"{pre}turnover_pa": m["turnover_annualised"],
                        f"{pre}executions": m["executions"],
                        f"{pre}round_trips": m["round_trips"],
                        f"{pre}bench_ew": m["benchmark_equal_weight_universe_pnl"]}
                if not args.skip_noise:
                    n = read_noise(label, window)
                    row |= {f"{pre}band_mean": n["mean"], f"{pre}band_sigma": n["sigma"],
                            f"{pre}percentile": n["v0_percentile"]}
            row |= timing
            rows.append(row)
            print(f"[sweep] {label:22s} done in {sum(timing.values()):6.1f}s", flush=True)

    frame = pd.DataFrame(rows)
    if "pnl" in frame:
        base = frame.loc[frame["label"] == "quarterly_reset", "pnl"].iloc[0]
        frame["delta_vs_v0"] = frame["pnl"] - base
        frame["z_qtr"] = frame["delta_vs_v0"] / SIGMA_QUARTERLY
        if "band_sigma" in frame:
            frame["z_own"] = frame["delta_vs_v0"] / frame["band_sigma"]

    out = ROOT / "output" / "sweep"
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "summary.csv", index=False)

    print(f"\n[sweep] {len(rows)} cells in {time.time()-total:.1f}s -> {out}/summary.csv\n")
    cols = ["label", "pnl", "delta_vs_v0", "z_own", "z_qtr", "sharpe", "mdd",
            "turnover_pa", "costs", "percentile", "stress_pnl"]
    show = [c for c in cols if c in frame]
    print(frame[show].to_string(index=False,
                                float_format=lambda v: f"{v:,.2f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
