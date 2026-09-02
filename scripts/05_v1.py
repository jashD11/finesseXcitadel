#!/usr/bin/env python3
"""
Phase 4: V1 -- the composite signal, and the pre-registered arms around it.

The feature set is `DECISIONS.md` C10 (12-1 momentum, information discreteness negated,
drawdown from the 252-day peak) and the combination rule is C17 (scaled ranks, C9 weights).
The five arms and six predictions were written into `CLAUDE.md` §11 **before this script was
first run**, which is what makes any result here a finding rather than a search.

Everything runs through `03_v0.py`'s helpers and `backtest.run` -- the identical engine V0,
the benchmarks and all 10,000 noise draws use. Only `build_holdings` differs. If a variant
did not run through that engine its PNL would not be comparable to V0's and §5's band could
not adjudicate it.

    python3 scripts/05_v1.py --arm base
    python3 scripts/05_v1.py --arm buffer
    python3 scripts/05_v1.py --arm rm-solo
    python3 scripts/05_v1.py --arm tilt
    python3 scripts/05_v1.py --arm base --calendar weekly_first_trading_day --weighting drift
    # --window stress for the §9 rejection filter, on survivors only

No noise band is run: every cell's sigma already exists and is read back, asserted, and
used as the denominator. Re-drawing it would change nothing and could only introduce drift.
"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import backtest, calendar, clean, features, metrics, select, universe  # noqa: E402
from src.config import load  # noqa: E402

v0 = import_module("03_v0")
AS_OF = v0.AS_OF

# The pre-registered slate (CLAUDE.md §11). `signal` picks which score is ranked; the other
# two fields are config overrides. Declared as data so the ledger, the CLI and the code
# cannot disagree about what an arm is.
ARMS: dict[str, dict] = {
    "base":    {"signal": "composite", "buffer": False, "weights": "base"},
    "buffer":  {"signal": "composite", "buffer": True,  "weights": "base"},
    "tilt":    {"signal": "composite", "buffer": False, "weights": "tilt"},
    "rm-solo": {"signal": "resid_mom", "buffer": False, "weights": "base"},
    # C9-r / CLAUDE.md §11 `WGT`: the pre-registered weight surface. Three ladder rungs
    # above `tilt`, and two isolation arms that hold momentum at exactly 1/2 while spending
    # the spare half on one feature instead of splitting it across both.
    "w3":      {"signal": "composite", "buffer": False, "weights": "w3"},
    "w6":      {"signal": "composite", "buffer": False, "weights": "w6"},
    "w8":      {"signal": "composite", "buffer": False, "weights": "w8"},
    "no-dd":   {"signal": "composite", "buffer": False, "weights": "no_ddown"},
    "no-id":   {"signal": "composite", "buffer": False, "weights": "no_idisc"},
}


def apply_arm(cfg, arm: str) -> None:
    """Point the config at one arm. Mirrors `03_v0.apply_overrides`, which handles cadence."""
    spec = ARMS[arm]
    cfg._flat["composite.use_buffer"] = spec["buffer"]
    cfg._flat["composite.active_weights"] = spec["weights"]


def score_frame(cfg, panel, cutoff, eligible: list[str], signal: str) -> pd.Series:
    """
    One rebalance date's scores over the eligible set.

    Causality is inherited from the caller: `cutoff` is `formation_cutoff(t)` = t-1 (B2) and
    every feature slices by position, ending at `cutoff`. Nothing here can see date t.
    """
    if signal == "resid_mom":
        # `RM-solo` (C10): one feature swapped for 12-1, nothing else changed. Not a
        # composite, so it takes no signs and no weights -- higher residual is better.
        return features.residual_momentum(cfg, panel, cutoff, eligible)

    frame = pd.DataFrame({
        "mom_12_1": features.momentum_12_1(cfg, panel, cutoff),
        "info_discreteness": features.information_discreteness(cfg, panel, cutoff),
        "drawdown_252": features.drawdown_from_peak(cfg, panel, cutoff),
    }).reindex(eligible)
    return features.composite(cfg, frame)


def build_holdings(cfg, panel, dates, signal: str) -> dict[pd.Timestamp, list[str]]:
    """
    The V1 selection rule. Same shape as `03_v0.build_holdings` so the two are comparable
    line for line: the only difference is which score is ranked and whether the rank buffer
    is applied.
    """
    lag = int(cfg["signal.formation_lag_days"])
    n = int(cfg["mandate.book_size"])
    use_buffer = bool(cfg["composite.use_buffer"])
    book: list[str] = []
    holdings: dict[pd.Timestamp, list[str]] = {}
    for day in dates:
        cutoff = calendar.formation_cutoff(day, panel.dates, lag)
        assert cutoff < day, "signal saw the rebalance date"
        eligible = universe.eligible_at(cfg, panel, day)
        scores = score_frame(cfg, panel, cutoff, eligible, signal)
        book = (select.with_buffer(cfg, scores, book, n) if use_buffer
                else select.top_n(cfg, scores, n, book))
        holdings[day] = book
    return holdings


def band_sigma(cfg, label: str, tag: str) -> tuple[float, float]:
    """
    Read back the *existing* noise band for this cell (sigma, V0's PNL on the same frame).

    D11 scores a variant as `(PNL_variant - PNL_V0) / sigma`. The band is a property of the
    universe, calendar and cost model -- not of the signal -- so a V1 arm is adjudicated by
    the band that was drawn before V1 existed. That is the point: the measuring stick cannot
    have been influenced by what it measures.
    """
    out = cfg.resolved_path("paths.output")
    path = (out if not label else out / "sweep" / label) / f"noise_summary{tag}.csv"
    if not path.exists():
        raise SystemExit(f"[v1] no noise band at {path}. Run scripts/04_noise.py for this "
                         f"cell first -- an arm cannot be scored without its sigma.")
    summary = pd.read_csv(path, index_col=0)["value"]
    return float(summary["sigma"]), float(summary["v0_pnl"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), default="base")
    ap.add_argument("--window", choices=sorted(v0.WINDOWS), default="main")
    ap.add_argument("--calendar", default=None)
    ap.add_argument("--weighting", default=None, choices=("reset", "drift"))
    args = ap.parse_args()
    start_key, end_key = v0.WINDOWS[args.window]
    tag = "" if args.window == "main" else "_stress"

    cfg = load()
    cell = v0.apply_overrides(cfg, args.calendar, args.weighting)
    apply_arm(cfg, args.arm)
    signal = ARMS[args.arm]["signal"]
    assert not cfg.pending(), f"open decisions block V1: {cfg.pending()}"

    panel = clean.load_panel(cfg, clean.panel_path(cfg, AS_OF),
                             clean.universe_path(cfg, AS_OF))
    capital = float(cfg["mandate.capital"])
    start, end = pd.Timestamp(cfg[start_key]), pd.Timestamp(cfg[end_key])

    print(f"[v1] arm '{args.arm}' | signal {signal} | weights "
          f"{cfg['composite.active_weights']} {features.weights(cfg)} | buffer "
          f"{cfg['composite.use_buffer']}")
    print(f"[v1] signs {features.signs(cfg)} | rule {cfg['composite.combination_rule']}")
    print(f"[v1] window '{args.window}': {start.date()} -> {end.date()} | calendar "
          f"{cfg['execution.rebalance_calendar']} | weighting "
          f"{'reset' if cfg['weighting.reset_to_target'] else 'drift'}")

    dates = calendar.rebalance_dates(cfg, panel.dates, start, end)
    eligibility = universe.eligibility_matrix(cfg, panel, dates)
    print(f"[v1] {len(dates)} rebalances | eligible {eligibility.sum(axis=1).min()}-"
          f"{eligibility.sum(axis=1).max()}")

    holdings = build_holdings(cfg, panel, dates, signal)
    forced = v0.build_events(cfg, panel)
    result = backtest.run(cfg, panel, holdings, capital, start, end, forced)
    backtest.reconcile(result, panel, capital)
    print("[v1] reconciled: the trade log explains the NAV to within Rs 1")

    benchmarks = metrics.benchmark_series(cfg, panel, eligibility, dates, capital, start, end)
    trips = metrics.round_trips(cfg, result, panel)
    pnl = metrics.total_net_pnl(result, capital)
    turn = metrics.turnover(result)
    gtl = metrics.gain_to_loss(cfg, trips)
    acc = metrics.accuracy(cfg, trips, benchmarks["equal_weight_universe"])

    # Churn, because §11's prediction 1 is about it and it is not in the V0 summary.
    books = [set(v) for v in holdings.values()]
    churn = sum(len(b - a) for a, b in zip(books, books[1:])) / max(len(books) - 1, 1)

    summary = {
        "arm": args.arm, "signal": signal,
        "weights": cfg["composite.active_weights"], "buffer": cfg["composite.use_buffer"],
        "total_net_pnl": pnl,
        "final_nav": float(result.nav.iloc[-1]),
        "total_return": metrics.total_return(result, capital),
        "annualised_return": metrics.annualised_return(cfg, result, capital),
        "sharpe": metrics.sharpe(cfg, result, capital),
        "max_drawdown": metrics.max_drawdown(cfg, result, capital),
        "total_costs": float(result.costs.sum()),
        "turnover_annualised": float(turn.sum() / metrics.elapsed_years(cfg, result)),
        "names_replaced_per_rebalance": churn,
        "round_trips": float(len(trips)),
        "accuracy_profitable": acc["profitable"],
        "gain_to_loss_mean": gtl["mean_win_over_mean_loss"],
    }
    for name in benchmarks.columns:
        summary[f"benchmark_{name}_pnl"] = float(benchmarks[name].iloc[-1] - capital)

    if args.window == "main":
        sigma, v0_pnl = band_sigma(cfg, cell, tag)
        summary["band_sigma"] = sigma
        summary["v0_pnl_same_frame"] = v0_pnl
        summary["delta_vs_v0"] = pnl - v0_pnl
        summary["z_vs_v0"] = (pnl - v0_pnl) / sigma

    out = cfg.resolved_path("paths.output") / "v1" / (args.arm if not cell
                                                      else f"{args.arm}_{cell}")
    out.mkdir(parents=True, exist_ok=True)
    result.nav.rename("nav").to_frame().join(result.cash.rename("cash")).join(
        result.costs.rename("costs")).to_csv(out / v0._tagged(cfg["output.nav"], tag))
    result.trades.to_csv(out / v0._tagged(cfg["output.trades"], tag), index=False)
    result.holdings.to_csv(out / v0._tagged(cfg["output.holdings"], tag))
    benchmarks.to_csv(out / v0._tagged(cfg["output.benchmarks"], tag))
    trips.to_csv(out / v0._tagged("round_trips.csv", tag), index=False)
    pd.Series(summary).rename("value").to_csv(out / v0._tagged(cfg["output.metrics"], tag))

    print()
    print(f"  Total Net PNL       Rs {pnl:>18,.0f}   ({summary['total_return']*100:>7.1f}%)")
    print(f"  Annualised (CAGR)      {summary['annualised_return']*100:>17.2f}%")
    print(f"  Sharpe                 {summary['sharpe']:>18.2f}")
    print(f"  Max drawdown           {summary['max_drawdown']*100:>17.2f}%")
    print(f"  Costs paid          Rs {summary['total_costs']:>18,.0f}"
          f"   ({summary['turnover_annualised']:.2f}x turnover p.a.)")
    print(f"  Names replaced         {churn:>18.2f}   per rebalance")
    if args.window == "main":
        print()
        print(f"  vs V0 (same frame)  Rs {summary['delta_vs_v0']:>18,.0f}"
              f"   z = {summary['z_vs_v0']:+.2f}  (sigma Rs {summary['band_sigma']:,.0f})")
    print()
    print(f"[v1] artefacts -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
