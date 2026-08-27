#!/usr/bin/env python3
"""
Phase 2: V0 end-to-end.

The null model (CLAUDE.md §4): 12-1 momentum, top 10, equal weight, quarterly, no
buffer, no optimiser, zero fitted parameters. Everything after this is measured as a
delta against the number it prints.

`--calendar` and `--weighting` run one cell of §11's `FREQ` grid through the same engine,
writing under output/sweep/ so a variant can never overwrite the V0 baseline the ledger
measures against.

Writes CSV artefacts, not a workbook: the guidelines require a GitHub repo and a 5-6
page report, and Excel appears nowhere in them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (backtest, calendar, clean, events, features, metrics,  # noqa: E402
                 select, universe)
from src.config import load  # noqa: E402

AS_OF = "2026-08-28"

# B8 (frozen): the stress window is a *separate* backtest that restarts with the full
# capital on the first trading day of 2026. Nothing carries over from 2021-25 — no
# holdings, no cash, no drifted weights. §9: it is a rejection filter, never a selection
# criterion, so no parameter may ever be chosen by looking at it.
WINDOWS = {"main": ("mandate.start", "mandate.end"),
           "stress": ("mandate.stress_start", "mandate.stress_end")}


def build_events(cfg, panel) -> dict[pd.Timestamp, list[str]]:
    """
    Forced mid-cycle exits (B10 / A18, `src/events.py`).

    Today this is the A16 ex-date source alone. The index-exit source joins it here once
    membership is point-in-time, which is why `events.merge` exists.
    """
    return events.ex_date_events(cfg, panel, clean.load_overrides(cfg))


def _tagged(name: str, tag: str) -> str:
    """`nav.csv` -> `nav_stress.csv`, so a stress run never overwrites the scored one."""
    stem, _, ext = name.rpartition(".")
    return f"{stem}{tag}.{ext}"


def apply_overrides(cfg, calendar_name: str | None, weighting: str | None) -> str:
    """
    Point the config at one cell of the `FREQ` grid and return a directory label.

    Returns "" for the baseline config, which keeps V0's artefacts exactly where they
    have always been. Any *other* cell writes under `output/sweep/<label>/`, because
    `output.nav` and friends are bare filenames -- without this a second cadence would
    silently overwrite the entire V0 baseline, and the ledger's `Δ vs V0` would be
    measured against a file that no longer holds V0.
    """
    if calendar_name is not None:
        if calendar_name not in calendar.supported_calendars():
            raise SystemExit(f"[v0] unsupported --calendar {calendar_name!r}; "
                             f"expected one of {calendar.supported_calendars()}")
        cfg._flat["execution.rebalance_calendar"] = calendar_name
    if weighting is not None:
        cfg._flat["weighting.reset_to_target"] = (weighting == "reset")

    cadence = str(cfg["execution.rebalance_calendar"]).replace("_first_trading_day", "")
    rule = "reset" if bool(cfg["weighting.reset_to_target"]) else "drift"
    if calendar_name is None and weighting is None:
        return ""
    return f"{cadence}_{rule}"


def output_dir(cfg, label: str):
    """`output/` for the baseline, `output/sweep/<label>/` for a grid cell."""
    out = cfg.resolved_path("paths.output")
    return out if not label else out / "sweep" / label


def build_holdings(cfg, panel, dates) -> dict[pd.Timestamp, list[str]]:
    """
    The V0 selection rule. Causal by construction: the signal for a rebalance at t is
    computed at `formation_cutoff(t)` = t-1 (B2) and filled at t's open.

    The incumbent book is threaded through only for C7's tie-break; V0 has no rank
    buffer, so it never changes which names are picked except in an exact tie.
    """
    lag = int(cfg["signal.formation_lag_days"])
    n = int(cfg["mandate.book_size"])
    book: list[str] = []
    holdings: dict[pd.Timestamp, list[str]] = {}
    for day in dates:
        cutoff = calendar.formation_cutoff(day, panel.dates, lag)
        assert cutoff < day, "signal saw the rebalance date"
        eligible = universe.eligible_at(cfg, panel, day)
        scores = features.momentum_12_1(cfg, panel, cutoff).reindex(eligible)
        book = select.top_n(cfg, scores, n, book)
        holdings[day] = book
    return holdings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", choices=sorted(WINDOWS), default="main",
                    help="main = 2021-25 (scored); stress = Jan-Jun 2026 (B8, rejection "
                         "filter only)")
    ap.add_argument("--calendar", default=None,
                    help="override execution.rebalance_calendar (FREQ grid, CLAUDE.md §11)")
    ap.add_argument("--weighting", default=None, choices=("reset", "drift"),
                    help="override weighting.reset_to_target (B3)")
    args = ap.parse_args()
    start_key, end_key = WINDOWS[args.window]
    tag = "" if args.window == "main" else "_stress"

    cfg = load()
    label = apply_overrides(cfg, args.calendar, args.weighting)
    pending = cfg.pending()
    print(f"[v0] config OK — {len(pending)} decisions still open "
          f"({', '.join(sorted(set(pending.values())))}), none blocking V0")

    panel = clean.load_panel(cfg, clean.panel_path(cfg, AS_OF),
                             clean.universe_path(cfg, AS_OF))
    capital = float(cfg["mandate.capital"])
    start = pd.Timestamp(cfg[start_key])
    end = pd.Timestamp(cfg[end_key])
    print(f"[v0] window '{args.window}': {start.date()} -> {end.date()}")
    print(f"[v0] calendar {cfg['execution.rebalance_calendar']} | weighting "
          f"{'reset' if cfg['weighting.reset_to_target'] else 'drift'}"
          f"{f' | -> output/sweep/{label}/' if label else ''}")
    print(f"[v0] panel {panel.close.shape[0]} days x {panel.close.shape[1]} names")

    dates = calendar.rebalance_dates(cfg, panel.dates, start, end)
    eligibility = universe.eligibility_matrix(cfg, panel, dates)
    print(f"[v0] {len(dates)} rebalances, {dates[0].date()} -> {dates[-1].date()} | "
          f"eligible names {eligibility.sum(axis=1).min()}-{eligibility.sum(axis=1).max()}")

    holdings = build_holdings(cfg, panel, dates)
    forced = build_events(cfg, panel)
    if forced:
        n = sum(len(v) for v in forced.values())
        print(f"[v0] {n} forced exit(s) declared on {len(forced)} date(s): "
              f"{', '.join(str(d.date()) for d in sorted(forced))}")
    result = backtest.run(cfg, panel, holdings, capital, start, end, forced)
    backtest.reconcile(result, panel, capital)
    print(f"[v0] reconciled: the trade log explains the NAV to within Rs 1")

    benchmarks = metrics.benchmark_series(cfg, panel, eligibility, dates,
                                          capital, start, end)
    trips = metrics.round_trips(cfg, result, panel)
    ew = benchmarks["equal_weight_universe"]

    pnl = metrics.total_net_pnl(result, capital)
    acc = metrics.accuracy(cfg, trips, ew)
    gtl = metrics.gain_to_loss(cfg, trips)
    turn = metrics.turnover(result)

    summary = {
        "total_net_pnl": pnl,
        "final_nav": float(result.nav.iloc[-1]),
        "total_return": metrics.total_return(result, capital),
        "annualised_return": metrics.annualised_return(cfg, result, capital),
        "sharpe": metrics.sharpe(cfg, result, capital),
        "max_drawdown": metrics.max_drawdown(cfg, result, capital),
        "total_costs": float(result.costs.sum()),
        "executions": float(len(result.trades)),
        "round_trips": float(len(trips)),
        "open_at_end": float(trips["open_at_end"].sum()),
        "names_ever_held": float(trips["symbol"].nunique()),
        "accuracy_profitable": acc["profitable"],
        "accuracy_beat_benchmark": acc["beat_benchmark"],
        "gain_to_loss_mean": gtl["mean_win_over_mean_loss"],
        "profit_factor": gtl["profit_factor"],
        "turnover_mean_per_rebalance": float(turn.mean()),
        "turnover_annualised": float(turn.sum() / metrics.elapsed_years(cfg, result)),
        "final_cash": float(result.cash.iloc[-1]),
        "elapsed_years": metrics.elapsed_years(cfg, result),
    }
    for name in benchmarks.columns:
        series = benchmarks[name]
        summary[f"benchmark_{name}_return"] = float(series.iloc[-1] / capital - 1.0)
        summary[f"benchmark_{name}_pnl"] = float(series.iloc[-1] - capital)

    out = output_dir(cfg, label)
    out.mkdir(parents=True, exist_ok=True)
    result.nav.rename("nav").to_frame().join(
        result.cash.rename("cash")).join(
        result.costs.rename("costs")).to_csv(out / _tagged(cfg["output.nav"], tag))
    result.trades.to_csv(out / _tagged(cfg["output.trades"], tag), index=False)
    result.holdings.to_csv(out / _tagged(cfg["output.holdings"], tag))
    result.weights.to_csv(out / _tagged(cfg["output.weights"], tag))
    benchmarks.to_csv(out / _tagged(cfg["output.benchmarks"], tag))
    pd.Series(summary).rename("value").to_csv(out / _tagged(cfg["output.metrics"], tag))
    trips.to_csv(out / _tagged("round_trips.csv", tag), index=False)

    print()
    print(f"  Total Net PNL       Rs {pnl:>18,.0f}   ({summary['total_return']*100:>7.1f}%)")
    print(f"  Final NAV           Rs {summary['final_nav']:>18,.0f}")
    print(f"  Annualised (CAGR)      {summary['annualised_return']*100:>17.2f}%")
    print(f"  Sharpe (x sqrt 252)    {summary['sharpe']:>18.2f}")
    print(f"  Max drawdown           {summary['max_drawdown']*100:>17.2f}%")
    print(f"  Costs paid          Rs {summary['total_costs']:>18,.0f}"
          f"   ({summary['turnover_annualised']:.2f}x turnover p.a.)")
    print(f"  Round trips            {len(trips):>18d}"
          f"   ({int(summary['open_at_end'])} open at end, marked)")
    print(f"  Accuracy               {acc['profitable']*100:>17.1f}%"
          f"   (vs benchmark {acc['beat_benchmark']*100:.1f}%)")
    print(f"  Gain/loss              {gtl['mean_win_over_mean_loss']:>18.2f}"
          f"   (profit factor {gtl['profit_factor']:.2f})")
    print()
    for name in benchmarks.columns:
        print(f"  benchmark {name:22s} {summary[f'benchmark_{name}_return']*100:>8.1f}%"
              f"   PNL Rs {summary[f'benchmark_{name}_pnl']:>16,.0f}")
    print()
    print(f"[v0] artefacts -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
