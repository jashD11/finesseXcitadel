#!/usr/bin/env python3
"""
Phase 3: the noise band (CLAUDE.md §5).

10,000 random 10-stock portfolios over the same window, the same rebalance calendar, the
same costs, the same engine. Only the choice of names differs, so the spread of outcomes
is pure luck -- the amount by which final PNL moves for reasons unrelated to any strategy.

Two things get read off it. Where V0 sits says whether 12-1 momentum beats coin-flipping
at all. Then every later change is scored as (PNL_variant - PNL_V0) / sigma (D11).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import backtest, calendar, clean, metrics, noise, universe  # noqa: E402
from src.config import load  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module  # noqa: E402

AS_OF = "2026-08-24"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", choices=("main", "stress"), default="main")
    args = ap.parse_args()
    tag = "" if args.window == "main" else "_stress"

    cfg = load()
    v0_module = import_module("03_v0")
    start_key, end_key = v0_module.WINDOWS[args.window]

    panel = clean.load_panel(cfg, clean.panel_path(cfg, AS_OF),
                             clean.universe_path(cfg, AS_OF))
    capital = float(cfg["mandate.capital"])
    start, end = pd.Timestamp(cfg[start_key]), pd.Timestamp(cfg[end_key])
    print(f"[noise] window '{args.window}': {start.date()} -> {end.date()}")

    dates = calendar.rebalance_dates(cfg, panel.dates, start, end)
    eligibility = universe.eligibility_matrix(cfg, panel, dates)

    holdings = v0_module.build_holdings(cfg, panel, dates)
    v0 = backtest.run(cfg, panel, holdings, capital, start, end)
    backtest.reconcile(v0, panel, capital)
    v0_pnl = metrics.total_net_pnl(v0, capital)

    # The assertion the whole band rests on. Without it a divergence in plumbing would
    # masquerade as a difference in selection.
    noise.assert_engine_equivalence(cfg, panel, v0, holdings, capital, end)
    print("[noise] engine equivalence: batch path reproduces backtest.run on V0")

    print(f"[noise] drawing {int(cfg['noise.n_draws']):,} portfolios "
          f"(seed {int(cfg['noise.master_seed'])}, "
          f"chunk {int(cfg['noise.chunk_size'])})...")
    band = noise.band(cfg, panel, eligibility, dates, capital, end)

    pnl = band.pnl
    percentile = float((pnl < v0_pnl).mean() * 100.0)
    z = noise.z_score(v0_pnl, float(pnl.mean()), band)

    print()
    print(f"  draws                {band.n_draws:>18,d}")
    print(f"  mean random PNL      Rs {pnl.mean():>15,.0f}")
    print(f"  median random PNL    Rs {np.median(pnl):>15,.0f}")
    print(f"  sigma of the band    Rs {band.sigma:>15,.0f}   (+/- {band.sigma_stderr:,.0f})")
    print(f"  worst / best draw    Rs {pnl.min():>15,.0f} / Rs {pnl.max():,.0f}")
    print()
    for q in (1, 5, 25, 50, 75, 95, 99):
        print(f"  {q:>2d}th percentile      Rs {np.percentile(pnl, q):>15,.0f}")
    print()
    print(f"  V0                   Rs {v0_pnl:>15,.0f}")
    print(f"  V0 percentile        {percentile:>18.2f}%")
    print(f"  V0 vs random mean    {z:>18.2f} sigma")
    print(f"  random draws beating V0: {int((pnl >= v0_pnl).sum()):,} of {band.n_draws:,}")

    # The harder question: unusual *for the risk it took*? A concentrated momentum book
    # in a bull market is systematically more volatile than a random one, so raw PNL
    # alone cannot separate a better signal from a riskier one.
    years = metrics.elapsed_years(cfg, v0)
    min_marks = 8
    if band.marks.shape[0] - 1 < min_marks:
        print(f"\n  --- risk view skipped: {band.marks.shape[0]-1} rebalance marks, "
              f"fewer than {min_marks}. A volatility estimated from that few points "
              f"is not worth reporting. ---")
        _save(cfg, band, pnl, v0_pnl, percentile, z, tag, risk=None)
        return 0
    rar = band.return_per_unit_risk(years)
    v0_marks = np.array([capital]
                        + [float((v0.holdings.loc[dates[i - 1]].to_numpy()
                                  * np.nan_to_num(panel.open.loc[d].rename(index=panel.symbols)
                                                  .reindex(v0.holdings.columns).to_numpy())).sum()
                                 + float(v0.cash.loc[dates[i - 1]]))
                           for i, d in enumerate(dates[1:], 1)]
                        + [float(v0.nav.iloc[-1])])
    v0_q = v0_marks[1:] / v0_marks[:-1] - 1.0
    periods = len(v0_marks) - 1
    v0_vol = v0_q.std(ddof=1) * np.sqrt(periods / years)
    v0_rar = ((v0_marks[-1] / capital) ** (1.0 / years) - 1.0) / v0_vol
    rar_pct = float((rar < v0_rar).mean() * 100.0)
    rand_vol = band.quarterly_returns().std(axis=0, ddof=1) * np.sqrt(periods / years)

    print()
    print("  --- adjusted for the risk taken ---")
    print(f"  V0 volatility        {v0_vol*100:>17.2f}%   "
          f"(random: median {np.median(rand_vol)*100:.2f}%, max {rand_vol.max()*100:.2f}%)")
    print(f"  V0 return/risk       {v0_rar:>18.2f}   "
          f"(random: median {np.median(rar):.2f}, max {rar.max():.2f})")
    print(f"  V0 percentile        {rar_pct:>18.2f}%   "
          f"({int((rar >= v0_rar).sum()):,} of {band.n_draws:,} match or beat it)")
    print("  NOTE: volatility from ~20 quarterly marks — indicative, not precise.")

    _save(cfg, band, pnl, v0_pnl, percentile, z, tag,
          risk={"v0_volatility": v0_vol,
                "random_volatility_median": float(np.median(rand_vol)),
                "random_volatility_max": float(rand_vol.max()),
                "v0_return_per_unit_risk": v0_rar,
                "random_return_per_unit_risk_median": float(np.median(rar)),
                "v0_risk_adjusted_percentile": rar_pct,
                "draws_matching_v0_risk_adjusted": int((rar >= v0_rar).sum())})
    return 0


def _save(cfg, band, pnl, v0_pnl, percentile, z, tag, risk):
    out = cfg.resolved_path("paths.output")
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "n_draws": band.n_draws, "master_seed": band.master_seed,
        "mean": pnl.mean(), "median": float(np.median(pnl)),
        "sigma": band.sigma, "sigma_stderr": band.sigma_stderr,
        "min": pnl.min(), "max": pnl.max(),
        "v0_pnl": v0_pnl, "v0_percentile": percentile, "v0_z_vs_mean": z,
        "draws_beating_v0": int((pnl >= v0_pnl).sum()),
    }
    summary.update(risk or {})
    pd.Series(pnl, name="pnl").to_csv(out / f"noise_band{tag}.csv", index=False)
    pd.Series(summary, name="value").to_csv(out / f"noise_summary{tag}.csv")
    print(f"\n[noise] artefacts -> {out}/noise_band{tag}.csv, noise_summary{tag}.csv")


if __name__ == "__main__":
    raise SystemExit(main())
