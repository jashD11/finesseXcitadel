"""
Signal computation. Causal by construction: every feature for a rebalance at t is
computed from data through the close of t-1 (B2, frozen).

The V1 feature set is frozen as `docs/DECISIONS.md` C10: **three** features, one concept each —
12-1 momentum (how much it rose), information discreteness (how the rise arrived), and
drawdown from the 252-day peak (where it sits against its own high). Residual momentum is
deliberately *not* in the composite (it ranks the cross-section 0.883 like plain momentum)
and lives here only for the pre-registered `RM-solo` arm.

Every function takes ``cutoff`` rather than the rebalance date, and takes it from
`calendar.formation_cutoff`, so the t-1 lag (B2) is visible at the call site instead of
being a slicing convention someone has to remember. Every window is sliced by **position**,
never by label -- ``panel.loc[:t]`` includes t.

No feature here introduces a numeric parameter. The drawdown window *is* `signal.lookback`;
information discreteness and the residual regression run over the same
`signal.lookback`/`signal.skip` pair the momentum signal uses. V1 inherits V0's
zero-fitted-parameter defence intact (C10).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.clean import Panel
from src.config import Config
from src.decisions import ConfigError

_COMBINATION_RULE = "scaled_ranks"      # C17
_RANKING_POPULATION = "pooled_eligible"  # C3


def _window_positions(cfg: Config, panel: Panel, cutoff: pd.Timestamp) -> tuple[int, int, int]:
    """``(cutoff_pos, lookback, skip)`` with the history check done once, in one place."""
    if cfg["signal.lookback_unit"] != "trading_days":
        raise ConfigError(f"C2 froze 'trading_days'; got {cfg['signal.lookback_unit']!r}")
    pos = panel.dates.get_loc(cutoff)
    lookback, skip = int(cfg["signal.lookback"]), int(cfg["signal.skip"])
    if pos - lookback < 0:
        raise ValueError(f"{cutoff.date()} has only {pos} prior trading days, needs {lookback}")
    return pos, lookback, skip


def momentum_12_1(cfg: Config, panel: Panel, cutoff: pd.Timestamp) -> pd.Series:
    """
    12-1 momentum: the return from ``lookback`` trading days before ``cutoff`` to
    ``skip`` trading days before it.

    C2 (frozen) counts both in trading days on the A8 calendar: 252 back, ending 21
    days early. The skip sits *inside* the 252-day window, so the signal is 11 months
    of return out of a 12-month window -- which is what "12 minus 1" names.

    This is V0's live signal and is deliberately left byte-identical to the version that
    produced the ledger's baseline: every V1 arm is measured as a delta against it.
    """
    pos, lookback, skip = _window_positions(cfg, panel, cutoff)

    start = panel.close.iloc[pos - lookback]
    finish = panel.close.iloc[pos - skip]

    basis = cfg["signal.return_type"]
    if basis == "simple":
        signal = finish / start - 1.0
    elif basis == "log":
        signal = np.log(finish / start)
    else:
        raise ConfigError(f"C1 allows 'simple' or 'log'; got {basis!r}")

    signal.name = f"mom_{lookback}_{skip}"
    return signal


def information_discreteness(cfg: Config, panel: Panel, cutoff: pd.Timestamp) -> pd.Series:
    """
    C14: ``ID = sign(Mom) x (%neg days - %pos days)`` over the formation window.

    Da, Gurun & Warachka (2014). Momentum pays because investors underreact, and
    underreaction is larger when information arrives as a steady drip too small to command
    attention than when it arrives in salient jumps that get priced immediately. The
    ``sign(Mom)`` factor makes the measure read the same for winners and losers, so **low
    ID means continuous information** in both directions.

    **Low is the good state**, which is why C14 gives this feature a negative weight in
    `config.yaml`. The negation lives there, not in this expression: a reversed sign here is
    the one V1 error that leaves no trace -- the run completes, reconciles to the rupee and
    reports plausible numbers while buying the opposite of what was intended. This function
    returns the raw quantity as the paper defines it and nothing else.

    C16 (`NON-ISSUE`): a day with a return of exactly zero is neither up nor down. Both
    fractions are taken over all T days, so flat days dilute them equally and push a thinly
    traded name toward zero, i.e. toward mid-rank -- which fails safe. Measured against
    rescaling over non-flat days only: rho +0.9997, 9.8/10 top-10 overlap.
    """
    if cfg["composite.flat_day_policy"] != "count_as_neither":
        raise ConfigError(f"C16 froze 'count_as_neither'; "
                          f"got {cfg['composite.flat_day_policy']!r}")
    pos, lookback, skip = _window_positions(cfg, panel, cutoff)

    block = panel.close.iloc[pos - lookback: pos - skip + 1].to_numpy(dtype=float)
    returns = np.diff(np.log(block), axis=0)

    frac_neg = (returns < 0).mean(axis=0)
    frac_pos = (returns > 0).mean(axis=0)
    signal = pd.Series(np.sign(returns.sum(axis=0)) * (frac_neg - frac_pos),
                       index=panel.isins, name="info_discreteness")
    # A name with no usable window produces NaN through the log, not a fabricated 0.0.
    return signal.where(np.isfinite(block).all(axis=0))


def drawdown_from_peak(cfg: Config, panel: Panel, cutoff: pd.Timestamp) -> pd.Series:
    """
    C15: ``P(cutoff) / max(P over the lookback window) - 1``, bounded above at 0.

    Where the stock sits against its own 252-day high -- a *path* statistic, and a genuinely
    separate concept from how far it rose (Phase 0: rho +0.43 against 12-1 momentum, well
    inside the 0.70 redundancy threshold, and only -0.04 against information discreteness).

    **Higher is better**: nearer the high scores higher (George & Hwang 2004, the
    52-week-high effect). C15 records why the opposite sign was rejected -- it would make
    this a short-horizon reversal bet, which C8/C10 excluded from V1 through a different
    column, and admitting it here through the back door would defeat that.

    The window ends *at* the cutoff, not one day short of it: unlike momentum there is no
    reason to skip the recent month, since proximity to the high is a statement about now.
    It is `signal.lookback` long, so this feature adds no parameter.
    """
    pos, lookback, _ = _window_positions(cfg, panel, cutoff)

    window = panel.close.iloc[pos - lookback + 1: pos + 1]
    signal = panel.close.iloc[pos] / window.max() - 1.0
    assert (signal.dropna() <= 1e-12).all(), "drawdown from a peak cannot be positive"
    signal.name = "drawdown_252"
    return signal


# ── Residual momentum: the `RM-solo` arm only, never the composite (C10) ──────


def market_return(cfg: Config, panel: Panel, cutoff: pd.Timestamp,
                  eligible: list[str]) -> np.ndarray:
    """
    C11: daily log returns of the **equal-weight point-in-time eligible universe** over the
    formation window -- the benchmark §7's ladder and the noise band already measure
    against, so a residual means "beat your own eligible set".

    Computed as the log of one plus the cross-sectional mean *simple* return, which is the
    return an equal-weight portfolio actually earns. Averaging log returns instead would
    describe a portfolio nobody holds.

    Phase 0 measured the choice as nearly inert against `^CNX100` (rho +0.934 on beta,
    +0.980 on standardised RM), so this is settled on internal consistency rather than on a
    difference in the numbers.
    """
    if cfg["composite.market_proxy"] != "equal_weight_eligible":
        raise ConfigError(f"C11 froze 'equal_weight_eligible'; "
                          f"got {cfg['composite.market_proxy']!r}")
    pos, lookback, skip = _window_positions(cfg, panel, cutoff)
    block = panel.close.loc[:, eligible].iloc[pos - lookback: pos - skip + 1].to_numpy(float)
    assert not np.isnan(block).any(), "eligibility promised a complete window"
    return np.log1p((block[1:] / block[:-1] - 1.0).mean(axis=1))


def residual_momentum(cfg: Config, panel: Panel, cutoff: pd.Timestamp,
                      eligible: list[str]) -> pd.Series:
    """
    C12/C13: standardised residual momentum over the formation window, for the eligible set.

    One OLS of each name's daily log returns on the market's gives everything:

        r[i,t] = alpha[i] + beta[i] * r[m,t] + eps[i,t]

    **The trap C13 exists to avoid.** Residuals of an OLS with an intercept sum to exactly
    zero over their own estimation window, so "cumulate the residuals" returns 0.0 for every
    name. What survives is ``T * alpha``, which rearranges to ``Mom[i] - beta[i]*Mom[m]``.
    Both normal equations are asserted below rather than trusted.

    C13 uses the same 231-day formation window as the momentum signal, so this is an *exact*
    algebraic decomposition of a quantity the project already computes -- one window governs
    eligibility, momentum and beta together and they cannot drift apart.

    C12 divides by ``sd(eps)*sqrt(T)``, making it proportional to the t-statistic on alpha.
    Recorded there: this is **not** because it removes an idiosyncratic-vol loading (Phase 0
    measured raw at +0.070 and standardised at +0.107 -- standardising slightly *raises* it),
    but because it is the only near-Gaussian column in the candidate set.
    """
    if cfg["composite.residual_form"] != "standardised":
        raise ConfigError(f"C12 froze 'standardised'; got {cfg['composite.residual_form']!r}")
    if cfg["composite.beta_window"] != "formation":
        raise ConfigError(f"C13 froze 'formation'; got {cfg['composite.beta_window']!r}")

    pos, lookback, skip = _window_positions(cfg, panel, cutoff)
    block = panel.close.loc[:, eligible].iloc[pos - lookback: pos - skip + 1].to_numpy(float)
    r = np.diff(np.log(block), axis=0)
    r_m = market_return(cfg, panel, cutoff, eligible)
    T = r.shape[0]
    assert r_m.shape == (T,), f"market series is {r_m.shape}, returns are {r.shape}"

    m_dev = r_m - r_m.mean()
    denom = float((m_dev ** 2).sum())
    assert denom > 0, "the market had zero variance over the formation window"

    beta = (r - r.mean(axis=0)).T @ m_dev / denom
    alpha = r.mean(axis=0) - beta * r_m.mean()
    resid = r - (alpha[None, :] + np.outer(r_m, beta))

    assert np.abs(resid.sum(axis=0)).max() < 1e-8, "residuals do not sum to zero"
    assert np.abs(resid.T @ m_dev).max() < 1e-6, "residuals are not orthogonal to the market"

    raw = r.sum(axis=0) - beta * float(r_m.sum())
    assert np.allclose(raw, T * alpha, atol=1e-9), \
        "RM != T*alpha; this is not the decomposition C13 documents"

    sd_eps = np.sqrt((resid ** 2).sum(axis=0) / (T - 2))
    return pd.Series(raw / (sd_eps * np.sqrt(T)), index=pd.Index(eligible),
                     name="resid_mom_std")


# ── The composite (C17, C3, C9) ──────────────────────────────────────────────


def weights(cfg: Config) -> dict[str, float]:
    """
    C9: the active weight vector, normalised to sum to 1.

    Stored in `config.yaml` as **integers** -- ``{1,1,1}`` and ``{2,1,1}`` -- so the base
    vector is exactly one third each and the tilt exactly 0.5/0.25/0.25, with no
    floating-point weight constant written anywhere. `tilt` is a pre-registered arm declared
    before any V1 result was seen, not a response to one.
    """
    active = cfg["composite.active_weights"]
    raw = {f: float(cfg[f"composite.weight_vectors.{active}.{f}"])
           for f in cfg["composite.features"]}
    # C9-r admits a weight of **zero**, which is how the `no_ddown` / `no_idisc` isolation
    # vectors drop a feature without disturbing `composite.features` or its signs (C10 stays
    # frozen). Negative weights are refused: a negative weight silently inverts a feature and
    # would duplicate, and could contradict, the sign declared in `composite.feature_signs`.
    bad = {f: w for f, w in raw.items() if w < 0}
    assert not bad, f"negative weights in {active!r}: {bad}; invert via feature_signs instead"
    total = sum(raw.values())
    assert total > 0, f"weight vector {active!r} sums to {total}"
    return {f: w / total for f, w in raw.items()}


def weight_vector_names(cfg: Config) -> list[str]:
    """
    Every weight vector declared in `config.yaml`, in declaration order.

    Derived from the config rather than listed here, so the `WGT` sweep, the tests and the
    YAML cannot disagree about which vectors exist — the §2 consistency rule applied to a
    set of names rather than to a number.
    """
    prefix = "composite.weight_vectors."
    names: list[str] = []
    for key in cfg._flat:
        if key.startswith(prefix):
            name = key[len(prefix):].split(".", 1)[0]
            if name not in names:
                names.append(name)
    assert names, "no weight vectors declared"
    return names


def signs(cfg: Config) -> dict[str, int]:
    """
    C14/C15: +1 or -1 per feature, read from config so a reader meets them before the code.

    Every feature named in `composite.features` must carry one. `src/config.py` declares one
    key per sign for exactly this reason: a new column cannot arrive without one.
    """
    out = {f: int(cfg[f"composite.feature_signs.{f}"]) for f in cfg["composite.features"]}
    bad = {f: s for f, s in out.items() if s not in (1, -1)}
    assert not bad, f"feature signs must be +1 or -1; got {bad}"
    return out


def composite(cfg: Config, features: pd.DataFrame) -> pd.Series:
    """
    C17: sign each feature, rank it across names on the rebalance date, scale by ``1/(N+1)``,
    then take the C9-weighted average.

    Ranking is **across names on one date**, never across time for one name. The
    time-shuffle test in `tests/test_causality.py` pins that down.

    **Why ranks and not z-scores.** Only one of the three columns is pathological, and under
    z-scoring it would decide the book: 12-1 momentum has cross-sectional skew +2.31, excess
    kurtosis +11.67 and a most-extreme name at 5.64 sigma, against a benign -0.11/+0.20/2.72
    for information discreteness. Ranks make three differently-scaled features commensurable
    and are robust to the data defects this project keeps finding -- the 2025-03-18 stale bar
    moved a z-score several sigma and would move a rank a few places. The cost, stated in
    C17: magnitude is discarded, so a name up 300% ranks one place above a name up 200%.

    The defining property, which `tests/` asserts: the output is **invariant to any monotone
    transform of a single input feature**. A z-composite is not, and that is the cleanest
    evidence this was implemented as C17 specifies rather than as something that merely
    correlates with it.

    C3 is `pooled_eligible`: one ranking over everything eligible on the date. The caller
    passes only eligible names, so pooling is what the frame already is -- asserted here so
    a future within-index variant cannot arrive silently.
    """
    if cfg["composite.combination_rule"] != _COMBINATION_RULE:
        raise ConfigError(f"C17 froze {_COMBINATION_RULE!r}; "
                          f"got {cfg['composite.combination_rule']!r}")
    if cfg["composite.ranking_population"] != _RANKING_POPULATION:
        raise ConfigError(f"C3 froze {_RANKING_POPULATION!r}; "
                          f"got {cfg['composite.ranking_population']!r}")

    wanted = list(cfg["composite.features"])
    missing = set(wanted) - set(features.columns)
    assert not missing, f"composite.features names columns not supplied: {sorted(missing)}"
    assert features.index.is_unique, "duplicate names reached the composite"

    # C5: a NaN must never be imputed. Eligibility already guarantees this cannot fire on
    # the C10 features -- it is asserted, not handled, so the day it can fire it is loud.
    if cfg["composite.missing_feature_policy"] != "ineligible":
        raise ConfigError(f"C5 froze 'ineligible'; "
                          f"got {cfg['composite.missing_feature_policy']!r}")
    holes = features[wanted].isna().sum().sum()
    assert holes == 0, (
        f"{holes} missing feature value(s) reached the composite. C5 says such a name sits "
        f"the rebalance out; it must be dropped from the eligible set before scoring, never "
        f"filled in here."
    )

    sign, weight = signs(cfg), weights(cfg)
    n = len(features)
    assert n > 1, f"cannot rank a cross-section of {n}"

    score = pd.Series(0.0, index=features.index)
    for name in wanted:
        scaled = (sign[name] * features[name]).rank() / (n + 1)
        score += weight[name] * scaled

    assert score.notna().all(), "the composite produced a NaN"
    assert ((score > 0.0) & (score < 1.0)).all(), "a scaled rank escaped (0, 1)"
    score.name = "composite"
    return score
