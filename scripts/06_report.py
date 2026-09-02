#!/usr/bin/env python3
"""
The report pack: every figure the submission quotes, and every chart it shows.

The guidelines (§7, §9) require a specific list of metrics and a benchmark comparison,
and the report is written by hand from them. This script exists so that **no number in
the report is ever typed by a human** -- it reads the artefacts the backtest already
wrote and emits one markdown table per required item, plus the charts.

    python3 scripts/06_report.py                  # the submitted cell
    python3 scripts/06_report.py --cell weekly_reset

Outputs:
    output/report/numbers.md      every required metric, pre-formatted
    output/report/composition.md  portfolio composition and weights at each rebalance
    output/figures/*.png          the four charts

CLAUDE.md §2: no fabricated numbers, ever. A figure that is not computed from data in
this repo does not get stated, and this is the mechanism that makes that cheap to obey.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load  # noqa: E402

#: The submitted configuration (CLAUDE.md §11, selected on 2021-25 PNL alone).
SUBMISSION_CELL = "monthly_reset"
BASELINE_CELL = "quarterly_reset"

#: The seven metric families guidelines §7 requires, mapped to the keys `metrics.py`
#: emits. Written as a table so a missing metric is a KeyError here rather than an
#: omission a reader has to notice.
REQUIRED = [
    ("Absolute / total return", "total_return", "pct"),
    ("Annualised return (CAGR)", "annualised_return", "pct"),
    ("Maximum drawdown", "max_drawdown", "pct"),
    ("Sharpe ratio", "sharpe", "num"),
    ("Gain-to-loss ratio", "gain_to_loss_mean", "num"),
    ("Accuracy (% profitable trades)", "accuracy_profitable", "pct"),
    ("Total round trips", "round_trips", "int"),
    ("Executions (single-name fills)", "executions", "int"),
    ("Turnover (annualised)", "turnover_annualised", "x"),
    ("Transaction costs paid", "total_costs", "rs"),
    ("Total Net PNL", "total_net_pnl", "rs"),
    ("Final portfolio value", "final_nav", "rs"),
]


def fmt(value: float, kind: str) -> str:
    if kind == "pct":
        return f"{value * 100:.2f}%"
    if kind == "rs":
        return f"₹{value:,.0f}"
    if kind == "int":
        return f"{value:,.0f}"
    if kind == "x":
        return f"{value:.2f}×"
    return f"{value:.2f}"


def cell_dir(cell: str) -> Path:
    return ROOT / "output" / "sweep" / cell if cell else ROOT / "output"


def read_metrics(cell: str, tag: str = "") -> pd.Series:
    return pd.read_csv(cell_dir(cell) / f"metrics{tag}.csv", index_col=0)["value"]


def read_band(cell: str, tag: str = "") -> pd.Series:
    return pd.read_csv(cell_dir(cell) / f"noise_summary{tag}.csv", index_col=0)["value"]


# ── the numbers pack ─────────────────────────────────────────────────────────


def numbers_pack(cell: str, out: Path) -> None:
    main = read_metrics(cell)
    base = read_metrics(BASELINE_CELL)
    stress = read_metrics(cell, "_stress")
    band = read_band(cell)
    stress_band = read_band(cell, "_stress")

    lines = [
        "# Report numbers — generated, never typed",
        "",
        f"Every figure below is read from `output/sweep/{cell}/`. Regenerate with",
        "`python3 scripts/06_report.py`. Nothing here is hand-entered (CLAUDE.md §2).",
        "",
        "## 1 · Required metrics (guidelines §7)",
        "",
        "| Metric | Submitted strategy | V0 baseline (quarterly) |",
        "|---|---|---|",
    ]
    for label, key, kind in REQUIRED:
        lines.append(f"| {label} | **{fmt(float(main[key]), kind)}** | "
                     f"{fmt(float(base[key]), kind)} |")

    trades_per_stock = float(main["round_trips"]) / float(main["names_ever_held"])
    lines += [
        f"| Names ever held | {fmt(float(main['names_ever_held']), 'int')} | "
        f"{fmt(float(base['names_ever_held']), 'int')} |",
        f"| Round trips per stock | {trades_per_stock:.2f} | "
        f"{float(base['round_trips']) / float(base['names_ever_held']):.2f} |",
        "",
        "## 2 · Benchmark comparison (guidelines §8)",
        "",
        "| | Total return | Total Net PNL |",
        "|---|---|---|",
        f"| **Strategy** | **{fmt(float(main['total_return']), 'pct')}** | "
        f"**{fmt(float(main['total_net_pnl']), 'rs')}** |",
        f"| Equal-weight universe (costed) | "
        f"{fmt(float(main['benchmark_equal_weight_universe_return']), 'pct')} | "
        f"{fmt(float(main['benchmark_equal_weight_universe_pnl']), 'rs')} |",
        f"| Nifty 100 index (cost-free) | "
        f"{fmt(float(main['benchmark_nifty100_index_return']), 'pct')} | "
        f"{fmt(float(main['benchmark_nifty100_index_pnl']), 'rs')} |",
        "",
        "## 3 · The significance band (CLAUDE.md §5)",
        "",
        "10,000 random 10-stock portfolios, same universe, same dates, same costs, same",
        "engine. The only thing that differs is which names are held.",
        "",
        "| | Value |",
        "|---|---|",
        f"| Random draws | {fmt(float(band['n_draws']), 'int')} |",
        f"| Seed | {int(band['master_seed'])} |",
        f"| Mean random PNL | {fmt(float(band['mean']), 'rs')} |",
        f"| Median random PNL | {fmt(float(band['median']), 'rs')} |",
        f"| σ of the band | {fmt(float(band['sigma']), 'rs')} |",
        f"| Best random draw | {fmt(float(band['max']), 'rs')} |",
        f"| **Strategy percentile** | **{float(band['v0_percentile']):.2f}%** |",
        f"| Draws beating the strategy | {fmt(float(band['draws_beating_v0']), 'int')} "
        f"of {fmt(float(band['n_draws']), 'int')} |",
        f"| Strategy vs random mean | {float(band['v0_z_vs_mean']):.2f}σ |",
        f"| Strategy annualised volatility | "
        f"{fmt(float(band['v0_volatility']), 'pct')} |",
        f"| Random volatility (median) | "
        f"{fmt(float(band['random_volatility_median']), 'pct')} |",
        f"| **Risk-adjusted percentile** | "
        f"**{float(band['v0_risk_adjusted_percentile']):.2f}%** |",
        "",
        "**Both readings go in the report, whatever they say.** The raw percentile",
        "answers 'is this better than picking 10 names at random?'. The risk-adjusted",
        "one answers 'or did it just take more risk?' — the rule does load on",
        "volatility, and under a raw-PNL metric that is rewarded, so the second number",
        "is the one that says whether the selection itself is any good. Quoting only",
        "whichever is higher would be exactly the dishonesty this band was built to",
        "prevent.",
        "",
        "## 4 · Out-of-sample stress window (guidelines §6)",
        "",
        "Fresh ₹1 crore on 2026-01-01, nothing carried over. A **one-way rejection",
        "filter** — no parameter was ever chosen by looking at it (CLAUDE.md §9).",
        "",
        "| | H1 2026 |",
        "|---|---|",
        f"| Strategy return | {fmt(float(stress['total_return']), 'pct')} |",
        f"| Strategy PNL | {fmt(float(stress['total_net_pnl']), 'rs')} |",
        f"| Max drawdown | {fmt(float(stress['max_drawdown']), 'pct')} |",
        f"| Equal-weight universe | "
        f"{fmt(float(stress['benchmark_equal_weight_universe_return']), 'pct')} |",
        f"| Nifty 100 index | "
        f"{fmt(float(stress['benchmark_nifty100_index_return']), 'pct')} |",
        f"| Percentile of a fresh band | "
        f"{float(stress_band['v0_percentile']):.2f}% |",
        "",
    ]
    out.write_text("\n".join(lines) + "\n")
    print(f"[report] numbers -> {out}")


# ── portfolio composition ────────────────────────────────────────────────────


def composition(cell: str, out: Path, show: int = 6) -> None:
    """
    Guidelines §9 asks for portfolio composition and weights.

    `weights.csv` is a **daily** series, not one row per rebalance, so the rebalance
    dates are taken from the trade log — the days the book was actually re-picked — and
    a holding count is reported in days, which is what the daily frame can support.
    Counting daily rows and calling them rebalances would overstate the number by ~20x.
    """
    weights = pd.read_csv(cell_dir(cell) / "weights.csv", index_col=0, parse_dates=True)
    trades = pd.read_csv(cell_dir(cell) / "trades.csv", parse_dates=["date"])
    held = weights.loc[:, (weights != 0).any()]

    rebalances = sorted(trades["date"].unique())
    picked = [rebalances[i] for i in
              range(0, len(rebalances), max(1, len(rebalances) // show))][:show]

    lines = ["# Portfolio composition", "",
             f"Target weights at {len(picked)} of the {len(rebalances)} rebalance dates, "
             f"from `output/sweep/{cell}/weights.csv`. The book is equal-weight 1/10 by",
             "construction (CLAUDE.md §4), so the interest is in *which* names, not how much;",
             "the small deviations from 10.00% are whole-share flooring (B4).",
             ""]
    for day in picked:
        row = held.loc[day]
        row = row[row > 0].sort_values(ascending=False)
        lines += [f"**{pd.Timestamp(day).date()}** — {len(row)} names",
                  "",
                  "| Stock | Weight |", "|---|---|"]
        lines += [f"| {name} | {w * 100:.2f}% |" for name, w in row.items()]
        lines.append("")

    days_held = (held > 0).sum().sort_values(ascending=False)
    picks = trades[trades["side"] == "BUY"].groupby("symbol").size()
    lines += ["## Longest-held names across the whole window", "",
              f"Out of {len(held.index):,} trading days in the window. A name can be "
              f"re-picked many times, so `times bought` counts entries, not names.",
              "",
              "| Stock | Days held | Times bought |", "|---|---|---|"]
    lines += [f"| {name} | {n} | {int(picks.get(name, 0))} |"
              for name, n in days_held.head(15).items()]
    out.write_text("\n".join(lines) + "\n")
    print(f"[report] composition -> {out}")


# ── figures ──────────────────────────────────────────────────────────────────


STYLE = {"figure.figsize": (9, 5), "axes.grid": True, "grid.alpha": 0.25,
         "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
         "savefig.dpi": 160, "savefig.bbox": "tight"}


def figures(cell: str, out_dir: Path) -> None:
    plt.rcParams.update(STYLE)
    d = cell_dir(cell)
    nav = pd.read_csv(d / "nav.csv", index_col=0, parse_dates=True)
    bench = pd.read_csv(d / "benchmarks.csv", index_col=0, parse_dates=True)

    # 1 · growth of ₹1 crore, log scale
    fig, ax = plt.subplots()
    ax.plot(nav.index, nav["nav"] / 1e7, label="Strategy", lw=1.8, color="#1b3a6b")
    for col, colour in zip(bench.columns, ["#c1502e", "#7a7a7a"]):
        ax.plot(bench.index, bench[col] / 1e7, lw=1.2, color=colour,
                label=col.replace("_", " ").title())
    ax.set_yscale("log")
    ax.set_ylabel("Portfolio value (₹ crore, log scale)")
    ax.set_title("Growth of ₹1 crore, 2021–2025, after 0.1% costs")
    ax.legend(frameon=False)
    fig.savefig(out_dir / "01_growth.png"); plt.close(fig)

    # 2 · the noise band — the single strongest slide (§5)
    band = pd.read_csv(d / "noise_band.csv")["pnl"] / 1e7
    summary = read_band(cell)
    fig, ax = plt.subplots()
    ax.hist(band, bins=70, color="#9fb3c8", edgecolor="white", linewidth=0.4)
    ax.axvline(band.median(), color="#7a7a7a", ls="--", lw=1.2,
               label=f"Median random book (₹{band.median():.2f} Cr)")
    strategy = float(summary["v0_pnl"]) / 1e7
    ax.axvline(strategy, color="#c1502e", lw=2,
               label=f"Strategy (₹{strategy:.2f} Cr, {float(summary['v0_percentile']):.2f}th pct)")
    ax.set_xlabel("Total Net PNL (₹ crore)")
    ax.set_ylabel("Random portfolios")
    ax.set_title("10,000 random 10-stock portfolios vs the strategy")
    ax.legend(frameon=False)
    fig.savefig(out_dir / "02_noise_band.png"); plt.close(fig)

    # 3 · drawdown
    curve = nav["nav"] / nav["nav"].cummax() - 1
    fig, ax = plt.subplots()
    ax.fill_between(curve.index, curve * 100, 0, color="#c1502e", alpha=0.35)
    ax.plot(curve.index, curve * 100, color="#8c3a20", lw=1)
    ax.set_ylabel("Drawdown (%)")
    ax.set_title(f"Drawdown from peak — worst {curve.min() * 100:.2f}%")
    fig.savefig(out_dir / "03_drawdown.png"); plt.close(fig)

    # 4 · the cadence x weighting surface
    grid = pd.read_csv(ROOT / "output" / "sweep" / "summary.csv")
    pivot = (grid.pivot(index="cadence", columns="weighting", values="pnl") / 1e7)
    order = [c for c in ["quarterly", "monthly", "weekly", "every_trading_day"]
             if c in pivot.index]
    pivot = pivot.loc[order]
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(pivot.to_numpy(), cmap="BuPu", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)),
                  [i.replace("every_trading_day", "daily") for i in pivot.index])
    for y in range(pivot.shape[0]):
        for x in range(pivot.shape[1]):
            ax.text(x, y, f"{pivot.iat[y, x]:.2f}", ha="center", va="center",
                    color="#1b1b1b", fontsize=10)
    ax.set_title("Total Net PNL (₹ crore) by cadence × weighting rule")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.savefig(out_dir / "04_cadence_grid.png"); plt.close(fig)

    print(f"[report] 4 figures -> {out_dir}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default=SUBMISSION_CELL)
    args = ap.parse_args()

    cfg = load()
    out = cfg.resolved_path("paths.output")
    (out / "report").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    print(f"[report] cell {args.cell}")
    numbers_pack(args.cell, out / "report" / "numbers.md")
    composition(args.cell, out / "report" / "composition.md")
    figures(args.cell, out / "figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
