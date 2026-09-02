#!/usr/bin/env python3
"""
Phase 0 (docs/PLAN.md): feature diagnostics.

Computes every candidate feature F1-F10 on every quarterly rebalance date in the scored
window and reports how they relate to one another. **No selection, no backtest, no PNL.**
Nothing here chooses a configuration; the point is to answer the factual questions D1-D6
rest on before those decisions are put to the user (docs/PROJECT.md §2).

Three properties make this a diagnostic rather than strategy code:

- **It reads no pending config key.** Every V1 parameter is still `null` and stays so.
  The feature definitions live here, as locals, and are promoted into `src/features.py`
  only in Phase 4 once D1-D5 have been answered.
- **Where a decision names alternatives, both are computed.** D2's two market proxies,
  D3's raw and standardised residual momentum, D5's two consistency measures. Reporting
  one of each would be answering the decision by implementing it.
- **Nothing is ranked on an outcome.** The only rankings taken are cross-sectional, on
  the rebalance date, and are never carried into a portfolio.

Causality (docs/PROJECT.md §2): every feature for a rebalance at `t` is computed from closes
through `formation_cutoff(t)` = t-1 (B2). Positional slices end at `cutoff_pos` and the
script asserts it. The eligible set is `universe.eligible_at(t)`, the same gate V0 uses,
so the cross-section here is exactly the cross-section a V1 selector would face.

    python3 scripts/09_feature_diagnostics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import calendar, clean, features, universe  # noqa: E402
from src.config import load  # noqa: E402

# The snapshot every analysis script reads. Sourced from config rather than repeated
# here: the same date lived in four files until 2026-09-02, and a *different* duplicated
# universe count is exactly what silently broke a cold `01_fetch.py` (see src/fetch.py).
# config.yaml is the single source of every value in this repo, dates included.
AS_OF = str(load()["universe.snapshot"])

# Diagnostic-only constants. These are not strategy parameters and deliberately do not
# enter config.yaml: config.yaml is the single source for values that change a reported
# number, and nothing here reaches a number that gets reported as a result.
#
# Every quarterly rebalance in the scored window is used rather than docs/PLAN.md's "~8".
# Sampling 8 of 20 would be a choice needing a defence; taking all 20 costs two seconds
# and needs none.
CADENCE = "quarterly_first_trading_day"

# Short window shared by F5 (realised vol) and F10 (rupee turnover). 60 and 20 sessions
# are the conventional definitions docs/PLAN.md states; they are printed alongside the results
# so a reader can see they were not tuned.
VOL_WINDOW = 60
TURNOVER_WINDOW = 20
DRAWDOWN_WINDOW = 252
BLOCK = 21          # sessions per "month" for D5's block alternative
N_BLOCKS = 11       # 11 x 21 = 231, exactly the formation window

FEATURES = ["F1_mom_12_1", "F2_resid_mom", "F3_beta", "F4_idio_vol", "F5_total_vol",
            "F6_amihud", "F7_skip_month", "F8_drawdown", "F9_info_disc",
            "F10_turnover"]


# ── the formation-window regression (docs/PLAN.md "Why F2, F3 and F4 come from one
#     regression") ────────────────────────────────────────────────────────────


def _regress(r: np.ndarray, r_m: np.ndarray) -> dict[str, np.ndarray]:
    """
    OLS of each name's daily log returns on the market's, over the formation window.

    `r` is (T, N), `r_m` is (T,). One pass gives F3 (slope), F4 (residual scatter) and
    F2 (intercept). The intercept route is not a stylistic preference: residuals of an
    OLS with an intercept sum to exactly zero over their own estimation window, so
    "cumulate the residuals" returns 0.0 for every name. `T * alpha` is the quantity
    that survives, and it rearranges to `Mom - beta * Mom_market`.
    """
    T = r.shape[0]
    assert r_m.shape == (T,), f"market series is {r_m.shape}, returns are {r.shape}"

    m_dev = r_m - r_m.mean()
    denom = float((m_dev ** 2).sum())
    assert denom > 0, "the market had zero variance over the formation window"

    beta = (r - r.mean(axis=0)) .T @ m_dev / denom
    alpha = r.mean(axis=0) - beta * r_m.mean()
    resid = r - (alpha[None, :] + np.outer(r_m, beta))

    # The normal equations, asserted rather than trusted: both must hold to machine
    # precision, and if they do not, the decomposition below is not the one documented.
    assert np.abs(resid.sum(axis=0)).max() < 1e-8, "residuals do not sum to zero"
    assert np.abs(resid.T @ m_dev).max() < 1e-6, "residuals are not orthogonal to market"

    sd_eps = np.sqrt((resid ** 2).sum(axis=0) / (T - 2))
    return {"beta": beta, "alpha": alpha, "sd_eps": sd_eps,
            "idio_vol": sd_eps * np.sqrt(252.0), "T": T}


def compute(cfg, panel, day: pd.Timestamp, eligible: list[str],
            index_close: pd.Series) -> pd.DataFrame:
    """Every candidate feature for one rebalance date, plus the decision alternatives."""
    days = panel.dates
    lag = int(cfg["signal.formation_lag_days"])
    cutoff = calendar.formation_cutoff(day, days, lag)
    assert cutoff < day, "the signal saw the rebalance date"
    pos = days.get_loc(cutoff)

    look, skip = int(cfg["signal.lookback"]), int(cfg["signal.skip"])
    close = panel.close.loc[:, eligible]
    volume = panel.volume.loc[:, eligible]

    # Formation window: closes at [pos-252 .. pos-21] -> 231 daily returns.
    blk = close.iloc[pos - look: pos - skip + 1].to_numpy(dtype=float)
    assert not np.isnan(blk).any(), "eligibility promised a complete window and did not deliver"
    r = np.diff(np.log(blk), axis=0)
    T = r.shape[0]
    assert T == look - skip == N_BLOCKS * BLOCK, f"formation window is {T} returns"

    # D2's two market proxies, both computed. (a) the equal-weight return of the
    # point-in-time eligible set — the benchmark the rest of the project measures
    # against; (b) the cap-weighted Nifty 100 level.
    ew_simple = (blk[1:] / blk[:-1] - 1.0).mean(axis=1)
    mkt = {
        "ew_universe": np.log1p(ew_simple),
        "cnx100": np.diff(np.log(
            index_close.reindex(days).iloc[pos - look: pos - skip + 1].to_numpy(float))),
    }

    fit = {k: _regress(r, v) for k, v in mkt.items()}
    log_mom = r.sum(axis=0)                      # = log(P[pos-21] / P[pos-252])

    out = pd.DataFrame(index=pd.Index(eligible, name="isin"))

    # F1 comes from src/features.py, not from a re-implementation here, so the
    # diagnostic cross-section is the live V0 signal to the rupee.
    out["F1_mom_12_1"] = features.momentum_12_1(cfg, panel, cutoff).reindex(eligible)
    assert np.allclose(np.log1p(out["F1_mom_12_1"].to_numpy(float)), log_mom, atol=1e-10), \
        "the local formation window and src/features.py disagree"

    for name, f in fit.items():
        mom_m = float(mkt[name].sum())
        raw = log_mom - f["beta"] * mom_m
        assert np.allclose(raw, f["T"] * f["alpha"], atol=1e-9), \
            "RM != T*alpha; the decomposition in docs/PLAN.md is not what was computed"
        out[f"F2raw_{name}"] = raw                                    # D3 (a)
        out[f"F2std_{name}"] = raw / (f["sd_eps"] * np.sqrt(f["T"]))  # D3 (b)
        out[f"F3beta_{name}"] = f["beta"]
        out[f"F4idio_{name}"] = f["idio_vol"]

    # The columns carried into the headline matrix use D2's recommended proxy. Both
    # remain in the frame and the D2 block below compares them directly.
    out["F2_resid_mom"] = out["F2std_ew_universe"]
    out["F3_beta"] = out["F3beta_ew_universe"]
    out["F4_idio_vol"] = out["F4idio_ew_universe"]

    short = close.iloc[pos - VOL_WINDOW: pos + 1].to_numpy(float)
    out["F5_total_vol"] = np.std(np.diff(np.log(short), axis=0), axis=0, ddof=1) * np.sqrt(252.0)

    # F6 Amihud over the formation window. Zero-volume sessions are excluded from the
    # mean rather than treated as infinite illiquidity: A10 already screens tradeability
    # and an untraded day is missing information, not evidence of price impact.
    px = close.iloc[pos - look + 1: pos - skip + 1].to_numpy(float)
    vol = volume.iloc[pos - look + 1: pos - skip + 1].to_numpy(float)
    rupee = px * vol
    with np.errstate(divide="ignore", invalid="ignore"):
        impact = np.where(rupee > 0, np.abs(np.diff(np.log(blk), axis=0)) / rupee, np.nan)
    out["F6_amihud"] = np.nanmean(impact, axis=0) * 1e9   # scaled for readability only

    p_now = close.iloc[pos].to_numpy(float)
    out["F7_skip_month"] = p_now / close.iloc[pos - skip].to_numpy(float) - 1.0
    # F8 is bounded above at 0 and enters the composite POSITIVELY (C15): nearer the
    # 252-day high scores higher. Its window is signal.lookback -- no new parameter.
    peak = close.iloc[pos - DRAWDOWN_WINDOW + 1: pos + 1].to_numpy(float).max(axis=0)
    out["F8_drawdown"] = p_now / peak - 1.0

    # C16 (NON-ISSUE): a day with a return of exactly zero is neither up nor down, so
    # both fractions are taken over all T days and flat days dilute them equally, pushing
    # a thin name toward mid-rank. Measured against rescaling over non-flat days only:
    # rho +0.9997, 9.8/10 top-10 overlap, worst single-name shift 3.3 percentile points.
    frac_neg = (r < 0).mean(axis=0)
    frac_pos = (r > 0).mean(axis=0)
    # Reported raw here. C14 enters it into the composite NEGATED -- low ID is the
    # predictive state (continuous information) while every other column is
    # higher-is-better. The negation lives in config.yaml, not in this expression.
    out["F9_info_disc"] = np.sign(log_mom) * (frac_neg - frac_pos)

    turn = (close.iloc[pos - TURNOVER_WINDOW + 1: pos + 1].to_numpy(float)
            * volume.iloc[pos - TURNOVER_WINDOW + 1: pos + 1].to_numpy(float))
    out["F10_turnover"] = turn.mean(axis=0)

    # D5 (a): fraction of the 11 non-overlapping 21-session blocks that rose.
    edges = blk[:: BLOCK]
    assert edges.shape[0] == N_BLOCKS + 1
    out["D5a_frac_pos_blocks"] = (edges[1:] / edges[:-1] - 1.0 > 0).mean(axis=0)

    out.insert(0, "date", day)
    assert out.drop(columns="date").notna().all().all(), "a feature came back NaN"
    return out


# ── reporting ────────────────────────────────────────────────────────────────


def _per_date_corr(frame: pd.DataFrame, cols: list[str], method: str) -> pd.DataFrame:
    """Cross-sectional correlation on each date, averaged across dates.

    Correlating the pooled stack instead would blend cross-sectional structure with
    variation in the level of each feature over time, which is a different question
    from the one D1 asks."""
    mats = [g[cols].corr(method=method) for _, g in frame.groupby("date")]
    return sum(mats) / len(mats)


def _fmt(matrix: pd.DataFrame) -> str:
    short = {c: c.split("_")[0] for c in matrix.columns}
    m = matrix.rename(index=short, columns=short)
    return m.to_string(float_format=lambda v: f"{v:6.2f}")


def main() -> int:
    cfg = load()
    print(f"[diag] config OK — {len(cfg.pending())} decisions open "
          f"({', '.join(sorted(set(cfg.pending().values())))}); this script reads none of them")

    panel = clean.load_panel(cfg, clean.panel_path(cfg, AS_OF), clean.universe_path(cfg, AS_OF))
    cfg._flat["execution.rebalance_calendar"] = CADENCE
    dates = calendar.rebalance_dates(cfg, panel.dates,
                                     pd.Timestamp(cfg["mandate.start"]),
                                     pd.Timestamp(cfg["mandate.end"]))
    index_close = (pd.read_parquet(cfg.resolved_path("paths.data_raw") / "indices_20260824.parquet")
                   .query("yahoo_symbol == '^CNX100'").set_index("date")["close"]
                   .sort_index().reindex(panel.dates).ffill())
    assert index_close.notna().all(), "^CNX100 does not cover the panel calendar"

    print(f"[diag] panel {panel.close.shape[0]} days x {panel.close.shape[1]} names | "
          f"{len(dates)} quarterly rebalances {dates[0].date()} -> {dates[-1].date()}")

    frames = []
    for day in dates:
        eligible = universe.eligible_at(cfg, panel, day)
        frames.append(compute(cfg, panel, day, eligible, index_close))
    data = pd.concat(frames)
    counts = data.groupby("date").size()
    print(f"[diag] {len(data):,} name-dates | eligible per date {counts.min()}-{counts.max()}\n")

    out = cfg.resolved_path("paths.output") / "diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    data.to_csv(out / "phase0_features.csv")

    # ── 1 · distribution shape, which is D6's whole argument ──────────────────
    print("=" * 78)
    print("1 · CROSS-SECTIONAL DISTRIBUTION SHAPE  (mean across the 20 dates)")
    print("=" * 78)
    rows = []
    for f in FEATURES:
        g = data.groupby("date")[f]
        z = g.transform(lambda s: (s - s.mean()) / s.std(ddof=1))
        rows.append({
            "feature": f, "skew": g.skew().mean(),
            "excess_kurt": g.apply(lambda s: s.kurt()).mean(),
            "min": g.min().mean(), "median": g.median().mean(), "max": g.max().mean(),
            "max_z": z.groupby(data["date"]).max().mean(),
            "pct_beyond_3z": float((z.abs() > 3).mean() * 100),
        })
    shape = pd.DataFrame(rows).set_index("feature")
    print(shape.to_string(float_format=lambda v: f"{v:11.3f}"))
    shape.to_csv(out / "phase0_shape.csv")
    print("\n  max_z = the most extreme name's z-score; pct_beyond_3z = share of all")
    print("  name-dates a C4/D8 clip at +/-3 would touch.")

    # ── 2 · the correlation matrices ─────────────────────────────────────────
    for method, note in (("spearman", "rank — what a rank composite (D6b) would see"),
                         ("pearson", "linear — what a z-score composite (D6a) would see")):
        print("\n" + "=" * 78)
        print(f"2 · CROSS-SECTIONAL {method.upper()} CORRELATION  ({note})")
        print("=" * 78)
        m = _per_date_corr(data, FEATURES, method)
        print(_fmt(m))
        m.to_csv(out / f"phase0_corr_{method}.csv")

    sp = _per_date_corr(data, FEATURES, "spearman")

    # ── 3 · the questions each decision actually turns on ─────────────────────
    print("\n" + "=" * 78)
    print("3 · WHAT EACH DECISION TURNS ON")
    print("=" * 78)

    per_date = {f: [g[["F1_mom_12_1", f]].corr(method="spearman").iloc[0, 1]
                    for _, g in data.groupby("date")] for f in FEATURES}

    def band(f: str) -> str:
        v = np.array(per_date[f])
        return f"{v.mean():+.2f}  (per-date range {v.min():+.2f} .. {v.max():+.2f})"

    print("\nD1 · is F8 too correlated with F1 to be its own concept? (threshold ~0.70)")
    print(f"     rho(F1, F8_drawdown)      {band('F8_drawdown')}")
    print(f"     rho(F1, F2_resid_mom)     {band('F2_resid_mom')}")
    print(f"     rho(F1, F9_info_disc)     {band('F9_info_disc')}")
    print(f"     rho(F1, F7_skip_month)    {band('F7_skip_month')}")

    # docs/PLAN.md aims the redundancy threshold at F8 and never states one for F2. If F2 is
    # a near-copy of F1 the composite is momentum twice, which is the exact failure
    # docs/PROJECT.md §6's "one per concept" rule exists to prevent, so it is measured too --
    # under both D3 variants, since D3 is still open.
    for col, lab in [("F2raw_ew_universe", "raw RM"), ("F2std_ew_universe", "std RM")]:
        r = np.mean([g[["F1_mom_12_1", col]].corr(method="spearman").iloc[0, 1]
                     for _, g in data.groupby("date")])
        ov = np.mean([len(set(g["F1_mom_12_1"].nlargest(10).index)
                          & set(g[col].nlargest(10).index)) for _, g in data.groupby("date")])
        print(f"     rho(F1, {lab})  {r:+.3f}   top-10 overlap ranking on F1 alone "
              f"vs {lab} alone: {ov:.1f}/10")

    print("\n     redundancy docs/PLAN.md warns about: var ~ beta^2*var_m + var_eps")
    print(f"     rho(F5_total_vol, F3_beta)      {sp.loc['F5_total_vol','F3_beta']:+.2f}")
    print(f"     rho(F5_total_vol, F4_idio_vol)  {sp.loc['F5_total_vol','F4_idio_vol']:+.2f}")
    print(f"     rho(F3_beta,     F4_idio_vol)   {sp.loc['F3_beta','F4_idio_vol']:+.2f}")

    print("\nD2 · does the market proxy change the residual? (a) EW universe vs (b) ^CNX100")
    for a, b, label in [("F3beta_ew_universe", "F3beta_cnx100", "beta"),
                        ("F2std_ew_universe", "F2std_cnx100", "standardised RM"),
                        ("F2raw_ew_universe", "F2raw_cnx100", "raw RM")]:
        rho = np.mean([g[[a, b]].corr(method="spearman").iloc[0, 1] for _, g in data.groupby("date")])
        print(f"     rho({label:16s} under (a) vs (b))   {rho:+.3f}")
    print("     size tilt check — does the (b) residual still carry a size bet?")
    for col, lab in [("F2std_ew_universe", "(a) EW"), ("F2std_cnx100", "(b) CNX100")]:
        rho = np.mean([g[[col, "F10_turnover"]].corr(method="spearman").iloc[0, 1]
                       for _, g in data.groupby("date")])
        print(f"     rho(RM {lab:11s}, F10_turnover)          {rho:+.3f}")

    print("\nD3 · raw or standardised residual momentum")
    rho = np.mean([g[["F2raw_ew_universe", "F2std_ew_universe"]].corr(method="spearman").iloc[0, 1]
                   for _, g in data.groupby("date")])
    print(f"     rho(raw RM, standardised RM)                {rho:+.3f}")
    for col, lab in [("F2raw_ew_universe", "raw"), ("F2std_ew_universe", "std")]:
        for other in ("F4_idio_vol", "F5_total_vol"):
            r2 = np.mean([g[[col, other]].corr(method="spearman").iloc[0, 1]
                          for _, g in data.groupby("date")])
            print(f"     rho({lab} RM, {other:13s})                  {r2:+.3f}")
    print(f"     rho(F1_mom_12_1, F4_idio_vol)               {sp.loc['F1_mom_12_1','F4_idio_vol']:+.3f}"
          "   <- the loading D3(b) is meant to remove")
    # D3's premise is that raw RM's spread scales with sd(eps), so the raw ranking
    # inherits an idio-vol loading. That is a claim about this cross-section and is
    # checkable directly, in both correlation senses.
    for meth in ("spearman", "pearson"):
        rr = np.mean([g[["F2raw_ew_universe", "F4idio_ew_universe"]].corr(method=meth).iloc[0, 1]
                      for _, g in data.groupby("date")])
        ss = np.mean([g[["F2std_ew_universe", "F4idio_ew_universe"]].corr(method=meth).iloc[0, 1]
                      for _, g in data.groupby("date")])
        aa = np.mean([g["F2raw_ew_universe"].abs().corr(g["F4idio_ew_universe"], method=meth)
                      for _, g in data.groupby("date")])
        print(f"     [{meth[:4]}] raw RM vs idio {rr:+.3f} | std RM vs idio {ss:+.3f} | "
              f"|raw RM| vs idio {aa:+.3f}  <- the spread claim")

    print("\nD5 · information discreteness (b) vs fraction of positive 21d blocks (a)")
    rho = np.mean([g[["F9_info_disc", "D5a_frac_pos_blocks"]].corr(method="spearman").iloc[0, 1]
                   for _, g in data.groupby("date")])
    n_distinct = data.groupby("date")["D5a_frac_pos_blocks"].nunique().mean()
    print(f"     rho(F9, D5a)                                {rho:+.3f}")
    print(f"     distinct values per date: F9 {data.groupby('date')['F9_info_disc'].nunique().mean():.0f}"
          f"  vs  D5a {n_distinct:.0f}   (D5a can take only {N_BLOCKS + 1} values)")
    ties = data.groupby("date")["D5a_frac_pos_blocks"].apply(
        lambda s: s.duplicated().mean()).mean() * 100
    print(f"     share of names in a tied D5a bucket:        {ties:.1f}%")
    print("     sign convention: F9 is *low* for continuously-arriving information, which")
    print("     is the state Da-Gurun-Warachka find predictive, so the two measures agree")
    print("     when rho is NEGATIVE. It is -0.19, i.e. they barely agree at all.")

    # Kept as D1's *original* four-feature proposal, deliberately: this row is the
    # evidence that retired it (C10), so re-pointing it at the frozen three would
    # destroy the record. The frozen set is F1 + F9 + F8 with F9 negated (C14) and F8
    # positive (C15) -- see config.yaml composite.feature_signs.
    print("\nD6 · z-composite vs rank-composite, on D1(a)'s four features, equal weights")
    d1a = ["F1_mom_12_1", "F2_resid_mom", "F9_info_disc", "F8_drawdown"]
    overlaps, rhos = [], []
    for _, g in data.groupby("date"):
        z = g[d1a].apply(lambda s: ((s - s.mean()) / s.std(ddof=1)).clip(-3, 3)).mean(axis=1)
        q = g[d1a].rank(pct=True).mean(axis=1)
        rhos.append(z.corr(q, method="spearman"))
        overlaps.append(len(set(z.nlargest(10).index) & set(q.nlargest(10).index)))
    print(f"     rho(z-composite, rank-composite)            {np.mean(rhos):+.3f}")
    print(f"     names in common in the top 10:              {np.mean(overlaps):.1f} of 10"
          f"   (range {min(overlaps)}-{max(overlaps)})")
    print("     descriptive only — neither composite is backtested and no PNL is computed.")

    print(f"\n[diag] artefacts -> {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
