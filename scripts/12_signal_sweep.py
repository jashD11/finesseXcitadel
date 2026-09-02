#!/usr/bin/env python3
"""
The `SIG` grid — momentum lookback x skip (CLAUDE.md §11, pre-registered 2026-09-02).

C2 froze `signal.lookback = 252` and `signal.skip = 21` on the published 12-1 convention
and the surface was never swept. This runs it: 3 lookbacks x 2 skips, every cell through
the identical engine, in the frame the `MAND` grid selected.

**No band is drawn.** A random draw ignores the signal entirely, so all six cells share
the frame's existing band -- a yardstick fixed before this grid was conceived. Re-drawing
it could only introduce drift.

**Adoption rule (pre-registered, binding):** a cell replaces the incumbent only if it
beats it by more than 1 sigma. Anything inside the band is a resampling of luck (§5) and
252/21 stays. This is stricter than §11's plain-max rule on purpose -- the axis has no
mechanism favouring one value over another, so taking the argmax of six correlated cells
would be fitting.

    python3 scripts/12_signal_sweep.py
    python3 scripts/12_signal_sweep.py --calendar weekly_first_trading_day
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

#: The pre-registered grid. 252/21 is the incumbent and is run like any other cell, so
#: the baseline sits inside its own surface rather than beside it.
LOOKBACKS = [126, 189, 252]
SKIPS = [0, 21]
INCUMBENT = (252, 21)

#: The frame the `MAND` grid selected on 2021-25 PNL alone (§11).
DEFAULT_CADENCE = "monthly_first_trading_day"
DEFAULT_WEIGHTING = "reset"

#: The bar. Pre-registered: more than one band sigma over the incumbent, in this frame.
ADOPTION_SIGMA = 1.0


def cell_label(lookback: int, skip: int, cadence: str, weighting: str) -> str:
    """Must match `03_v0.apply_overrides`, which owns the naming."""
    return (f"mom{lookback}x{skip}_"
            f"{cadence.replace('_first_trading_day', '')}_{weighting}")


def run_cell(lookback: int, skip: int, cadence: str, weighting: str,
             window: str) -> float:
    cmd = [sys.executable, str(ROOT / "scripts" / "03_v0.py"),
           "--window", window, "--calendar", cadence, "--weighting", weighting,
           "--lookback", str(lookback), "--skip", str(skip)]
    t0 = time.time()
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        print(done.stdout[-3000:], file=sys.stderr)
        print(done.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"[sig] 03_v0.py failed for {lookback}/{skip}")
    return time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--calendar", default=DEFAULT_CADENCE)
    ap.add_argument("--weighting", default=DEFAULT_WEIGHTING)
    args = ap.parse_args()

    frame = f"{args.calendar.replace('_first_trading_day', '')}_{args.weighting}"
    band = pd.read_csv(ROOT / "output" / "sweep" / frame / "noise_summary.csv",
                       index_col=0)["value"]
    sigma = float(band["sigma"])
    print(f"[sig] frame {frame} | band sigma Rs {sigma:,.0f} "
          f"(drawn before this grid; not re-drawn)")
    print(f"[sig] adoption bar: incumbent {INCUMBENT[0]}/{INCUMBENT[1]} "
          f"+ {ADOPTION_SIGMA:.0f} sigma = Rs {ADOPTION_SIGMA * sigma:,.0f}")

    rows: list[dict] = []
    t_all = time.time()
    for lookback in LOOKBACKS:
        for skip in SKIPS:
            secs = run_cell(lookback, skip, args.calendar, args.weighting, "main")
            label = cell_label(lookback, skip, args.calendar, args.weighting)
            m = pd.read_csv(ROOT / "output" / "sweep" / label / "metrics.csv",
                            index_col=0)["value"]
            rows.append({
                "lookback": lookback, "skip": skip, "label": label, "frame": frame,
                "pnl": float(m["total_net_pnl"]),
                "total_return": float(m["total_return"]),
                "cagr": float(m["annualised_return"]),
                "sharpe": float(m["sharpe"]),
                "mdd": float(m["max_drawdown"]),
                "turnover_pa": float(m["turnover_annualised"]),
                "costs": float(m["total_costs"]),
                "round_trips": float(m["round_trips"]),
                "bench_ew": float(m["benchmark_equal_weight_universe_pnl"]),
                "seconds": secs,
            })
            print(f"  {lookback:>3}d skip {skip:>2}  PNL {rows[-1]['pnl']:>14,.0f}  "
                  f"Sharpe {rows[-1]['sharpe']:.2f}  turnover {rows[-1]['turnover_pa']:.2f}x")

    df = pd.DataFrame(rows)
    incumbent = df[(df.lookback == INCUMBENT[0]) & (df.skip == INCUMBENT[1])]
    assert len(incumbent) == 1, "the incumbent cell must be in the grid"
    base_pnl = float(incumbent["pnl"].iloc[0])
    df["delta_vs_incumbent"] = df["pnl"] - base_pnl
    df["z_vs_incumbent"] = df["delta_vs_incumbent"] / sigma
    df["band_sigma"] = sigma

    out = ROOT / "output" / "sweep" / "sig_summary.csv"
    df.to_csv(out, index=False)

    print()
    print("=" * 74)
    print(f"THE SURFACE — PNL in Rs crore, frame {frame}")
    print("=" * 74)
    grid = df.pivot(index="lookback", columns="skip", values="pnl") / 1e7
    print(grid.round(2).to_string())
    print()
    print("z vs the incumbent (252/21), in band sigma:")
    print(df.pivot(index="lookback", columns="skip",
                   values="z_vs_incumbent").round(2).to_string())

    print()
    print("=" * 74)
    print("THE PRE-REGISTERED ADOPTION RULE")
    print("=" * 74)
    best = df.loc[df["pnl"].idxmax()]
    cleared = df[df["z_vs_incumbent"] > ADOPTION_SIGMA]
    print(f"  incumbent  {INCUMBENT[0]}/{INCUMBENT[1]}  Rs {base_pnl:>14,.0f}")
    print(f"  best cell  {int(best.lookback)}/{int(best.skip)}  "
          f"Rs {best.pnl:>14,.0f}   z {best.z_vs_incumbent:+.2f}")
    print(f"  cells clearing +{ADOPTION_SIGMA:.0f} sigma: {len(cleared)} of {len(df)}"
          f"  (null expectation on luck alone: ~1)")
    if len(cleared):
        print(f"  -> ADOPT {int(best.lookback)}/{int(best.skip)}: it beats the incumbent "
              f"by more than the band.")
    else:
        print(f"  -> KEEP {INCUMBENT[0]}/{INCUMBENT[1]}: no cell clears the band. The "
              f"surface is reported as a measurement, not a selection.")

    print()
    print("PREDICTION 3 — shorter lookbacks lose (126 < 189 < 252 at both skips)")
    for skip in SKIPS:
        seq = df[df.skip == skip].sort_values("lookback")["pnl"].tolist()
        mono = all(x < y for x, y in zip(seq, seq[1:]))
        print(f"  skip {skip:>2}: {'CONFIRMED' if mono else 'FAILED'}  "
              f"{' < '.join(f'{v/1e7:.2f}' for v in seq)}")

    print()
    print("PREDICTION 2 — |252x21 vs 252x0| < 1 sigma")
    pair = df[(df.lookback == 252)].set_index("skip")["pnl"]
    z = (pair[0] - pair[21]) / sigma
    print(f"  skip 0 - skip 21 = Rs {pair[0] - pair[21]:+,.0f}  ({z:+.2f} sigma)  "
          f"{'CONFIRMED' if abs(z) < 1 else 'FAILED'}")

    print(f"\n[sig] {len(df)} cells in {time.time() - t_all:.1f}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
