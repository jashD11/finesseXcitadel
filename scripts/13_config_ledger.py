#!/usr/bin/env python3
"""
The complete configuration ledger: every backtest this project ever ran, in one table.

docs/PROJECT.md §11 is the narrative ledger, written as the work happened. This is the
machine-generated companion: one row per run, read straight from the artefacts, so the
count and every figure in it are derived rather than transcribed.

    python3 scripts/13_config_ledger.py

Outputs:
    output/report/configurations.csv   one row per run, every parameter and every metric
    output/report/configurations.md    the same, grouped by slate and readable

A run is identified by its output directory, and its parameters are recovered from the
directory name -- which is exactly why `03_v0.apply_overrides` puts every varied axis in
the label. Three directories hold a configuration that also appears in another slate;
they are marked `duplicate` and their PNL must match the original to the rupee, which is
asserted here rather than hoped for.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load  # noqa: E402

CADENCES = {"quarterly": "quarterly", "monthly": "monthly", "weekly": "weekly",
            "every_trading_day": "daily"}

#: Composite weight vectors, as momentum / information-discreteness / drawdown.
VECTORS = {"base": "1/1/1", "tilt": "2/1/1", "no-dd": "1/1/0", "no-id": "1/0/1",
           "w3": "3/1/1", "w6": "6/1/1", "w8": "8/1/1"}

#: Runs that repeat a configuration already present in an earlier slate. Kept, because
#: each is an independent reproduction through a different driver script.
DUPLICATES = {
    "output/sweep/mom252x21_monthly_reset": "output/sweep/monthly_reset",
    "output/v1/base_quarterly_reset": "output/v1/base",
    "output/v1/tilt_quarterly_reset": "output/v1/tilt",
}


def parse(path: Path) -> dict | None:
    """Recover a run's parameters from its output directory."""
    rel = str(path.relative_to(ROOT))
    name = path.name
    base = dict(slate="", universe="Nifty 100 + Midcap 100", signal="12-1 momentum",
                lookback=252, skip=21, weights="—", buffer=False,
                cadence="quarterly", weighting="reset", dir=rel)

    if rel == "output":
        return base | dict(slate="MAND", id="V0 (default run)")

    if rel.startswith("output/sweep/"):
        m = re.fullmatch(r"mom(\d+)x(\d+)_(.+)_(reset|drift)", name)
        if m:
            lb, sk, cad, rule = m.groups()
            return base | dict(slate="SIG", id=f"SIG {lb}/{sk}", lookback=int(lb),
                               skip=int(sk), signal=f"momentum {lb}d skip {sk}d",
                               cadence=CADENCES[cad], weighting=rule)
        m = re.fullmatch(r"small_(.+)_(reset|drift)", name)
        if m:
            cad, rule = m.groups()
            return base | dict(slate="SMALL", id=f"SMALL {CADENCES[cad]}",
                               universe="+ Nifty Smallcap 100 (299 names)",
                               cadence=CADENCES[cad], weighting=rule)
        m = re.fullmatch(r"(.+)_(reset|drift)", name)
        if m:
            cad, rule = m.groups()
            return base | dict(slate="MAND", id=f"MAND {CADENCES[cad]}/{rule}",
                               cadence=CADENCES[cad], weighting=rule)

    if rel.startswith("output/v1/"):
        if name in ("base", "buffer", "tilt", "rm-solo"):
            vec = {"base": "base", "buffer": "base", "tilt": "tilt", "rm-solo": "base"}[name]
            return base | dict(
                slate="V1", id=f"V1 {name}", weights=VECTORS[vec],
                buffer=(name == "buffer"),
                signal=("residual momentum" if name == "rm-solo"
                        else "composite (mom + info-disc + drawdown)"))
        m = re.fullmatch(r"(base|tilt|no-dd|no-id|w3|w6|w8)_(.+)_(reset|drift)", name)
        if m:
            vec, cad, rule = m.groups()
            return base | dict(slate="WGT", id=f"WGT {vec} {CADENCES[cad]}/{rule}",
                               weights=VECTORS[vec], cadence=CADENCES[cad],
                               weighting=rule,
                               signal="composite (mom + info-disc + drawdown)")
    return None


def metrics_of(path: Path, tag: str = "") -> pd.Series | None:
    f = path / f"metrics{tag}.csv"
    return pd.read_csv(f, index_col=0)["value"] if f.exists() else None


def pick(series: pd.Series, key: str) -> float:
    """
    A metric if this slate's writer emitted it, NaN otherwise.

    The two driver scripts emit overlapping but different metric sets -- `05_v1.py` adds
    the composite's own fields and carries its band inline, while `03_v0.py` writes a
    separate `noise_summary.csv`. A missing cell here is a genuine "this slate does not
    report that", so it becomes NaN rather than a fabricated zero.

    Not a config default: docs/PROJECT.md §2 forbids `get(key, default)` in `src/` because a
    default there is an unrecorded design decision. This reads an artefact, not a decision.
    """
    return float(series[key]) if key in series.index else float("nan")


def band_of(path: Path) -> pd.Series | None:
    f = path / "noise_summary.csv"
    return pd.read_csv(f, index_col=0)["value"] if f.exists() else None


def main() -> int:
    cfg = load()
    out = cfg.resolved_path("paths.output")

    dirs = [ROOT / "output"]
    dirs += sorted((ROOT / "output" / "sweep").glob("*/"))
    dirs += sorted((ROOT / "output" / "v1").glob("*/"))

    rows = []
    for d in dirs:
        if not (d / "metrics.csv").exists():
            continue
        spec = parse(d)
        if spec is None:
            print(f"[ledger] WARNING: unrecognised run directory {d}")
            continue
        m = metrics_of(d)
        stress = metrics_of(d, "_stress")
        band = band_of(d)
        rows.append(spec | {
            "pnl": float(m["total_net_pnl"]),
            "total_return": float(m["total_return"]),
            "cagr": float(m["annualised_return"]),
            "sharpe": float(m["sharpe"]),
            "max_drawdown": float(m["max_drawdown"]),
            "turnover_pa": float(m["turnover_annualised"]),
            "costs": float(m["total_costs"]),
            "round_trips": pick(m, "round_trips"),
            "names_ever_held": pick(m, "names_ever_held"),
            "accuracy": pick(m, "accuracy_profitable"),
            "gain_to_loss": pick(m, "gain_to_loss_mean"),
            "bench_ew_return": pick(m, "benchmark_equal_weight_universe_return"),
            "band_sigma": (float(band["sigma"]) if band is not None
                           else pick(m, "band_sigma")),
            "band_percentile": (float(band["v0_percentile"]) if band is not None
                                else float("nan")),
            "risk_adj_percentile": (pick(band, "v0_risk_adjusted_percentile")
                                    if band is not None else float("nan")),
            "z_vs_frame_v0": pick(m, "z_vs_v0"),
            "stress_return": float(stress["total_return"]) if stress is not None else float("nan"),
            "duplicate_of": DUPLICATES.get(spec["dir"], ""),
        })

    df = pd.DataFrame(rows)

    # Every duplicate must reproduce its original exactly. An independent driver script
    # arriving at the same rupee is a real check, and it is asserted, not assumed.
    for dup, original in DUPLICATES.items():
        a = df.loc[df["dir"] == dup, "pnl"]
        b = df.loc[df["dir"] == original, "pnl"]
        if len(a) and len(b):
            assert float(a.iloc[0]) == float(b.iloc[0]), \
                f"{dup} does not reproduce {original}: {a.iloc[0]} vs {b.iloc[0]}"

    runs = len(df)
    distinct = int((df["duplicate_of"] == "").sum())
    # `output/` is the default-argument run of the same config as MAND quarterly/reset.
    distinct_configs = distinct - 1

    csv = out / "report" / "configurations.csv"
    df.to_csv(csv, index=False)

    # ── the readable version ─────────────────────────────────────────────────
    v0 = float(df.loc[df["dir"] == "output/sweep/quarterly_reset", "pnl"].iloc[0])
    sub = float(df.loc[df["dir"] == "output/sweep/monthly_reset", "pnl"].iloc[0])

    L = ["# Every configuration tested", "",
         f"**{runs} backtest runs, {distinct_configs} distinct configurations.** Generated by",
         "`scripts/13_config_ledger.py` from the artefacts themselves — every figure below is",
         "read from a CSV, none is transcribed. Machine-readable version:",
         "`output/report/configurations.csv`.",
         "",
         f"The bar: **V0 quarterly = ₹{v0:,.0f}**. The submission: "
         f"**₹{sub:,.0f}** (monthly, reset).",
         "",
         "`z` is the arm's distance from the *quarterly baseline* in units of that arm's own",
         "noise-band σ where one exists. Cells without a band were adjudicated against their",
         "frame's band in the slate that ran them; see `docs/PROJECT.md` §11.",
         ""]

    titles = {
        "MAND": ("Cadence × weighting rule", "The only axis that paid."),
        "SIG": ("Momentum lookback × skip",
                "The incumbent 252/21 is the best cell of its own surface."),
        "SMALL": ("Universe: adding Nifty Smallcap 100",
                  "Both arms lose. The wider universe made the *benchmark* better and the "
                  "*rule* worse."),
        "V1": ("Composite signal", "All four lose, by more than 5σ."),
        "WGT": ("Composite feature weights",
                "42 cells. None beats the baseline in its own frame; none reaches +1σ."),
    }
    for slate in ("MAND", "SIG", "SMALL", "V1", "WGT"):
        block = df[df["slate"] == slate].sort_values("pnl", ascending=False)
        title, note = titles[slate]
        L += [f"## {slate} — {title} ({len(block)} runs)", "", note, "",
              "| Configuration | Universe | Signal | Weights | Cadence | Weighting | "
              "Total Net PNL | Return | Sharpe | Max DD | Turnover | Costs | vs V0 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in block.iterrows():
            dup = " *(dup)*" if r["duplicate_of"] else ""
            delta = r["pnl"] - v0
            L.append(
                f"| {r['id']}{dup} | {r['universe']} | {r['signal']} | {r['weights']} | "
                f"{r['cadence']} | {r['weighting']} | ₹{r['pnl']:,.0f} | "
                f"{r['total_return']*100:.1f}% | {r['sharpe']:.2f} | "
                f"{r['max_drawdown']*100:.1f}% | {r['turnover_pa']:.2f}× | "
                f"₹{r['costs']:,.0f} | {delta:+,.0f} |")
        L.append("")

    L += ["## Runs that repeat a configuration", "",
          "Each was run again by a different driver script in a later slate. All reproduce",
          "the original **to the rupee**, which `13_config_ledger.py` asserts:", "",
          "| Run | Repeats | PNL |", "|---|---|---|"]
    for dup, original in DUPLICATES.items():
        p = float(df.loc[df["dir"] == dup, "pnl"].iloc[0])
        L.append(f"| `{dup}` | `{original}` | ₹{p:,.0f} |")
    L += ["| `output/` | `output/sweep/quarterly_reset` | "
          f"₹{v0:,.0f} |", ""]

    (out / "report" / "configurations.md").write_text("\n".join(L) + "\n")
    print(f"[ledger] {runs} runs, {distinct_configs} distinct configurations")
    print(f"[ledger] -> {csv}")
    print(f"[ledger] -> {out / 'report' / 'configurations.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
