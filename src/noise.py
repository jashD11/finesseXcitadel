"""
The noise band (docs/PROJECT.md §5) — the decision rule for everything after V0.

D2 is frozen: 10,000 draws, resampled at every rebalance date, without replacement,
from the as-of eligible set, charged the same costs, through the same engine.

Why it is a null. A random draw carries no forecasting content, so the spread across
10,000 outcomes cannot come from skill — only from which names happened to be picked.
That spread is the amount by which final PNL moves for reasons unrelated to any
strategy, and it is large here: ten names against a 200-name universe over five years.

Two things get compared against it. Where V0 sits inside the distribution says whether
12-1 momentum beats coin-flipping at all. Then every later change is scored as
``(PNL_variant - PNL_V0) / sigma_band`` and that ``z`` — not a pass/fail tick — is what
the ledger records, because the rebalanced band is narrower than a static one and so
sets a lower bar than intuition suggests.

Design, for when this is built:

- **Batched across draws, not looped.** State is a dense (D, N) holdings matrix —
  10,000 x 200 float64, about 16 MB — which makes turnover a plain |target - current|
  reduction over N with no index alignment. Per rebalance segment: draw (D, 10) picks,
  gather opens, size, charge costs against prior holdings, then gather closes over the
  segment for a (segment_len, D) NAV block. Peak gather is roughly 62 x 10,000 x 10.
- **Seeded per draw, not per run.** ``SeedSequence(master_seed).spawn(n_draws)`` gives
  draw i its own generator, so results are identical regardless of ``chunk_size`` or
  iteration order. Changing the batching must not change a single rupee.
- **Equivalence is asserted, not assumed.** ``assert_engine_equivalence`` runs V0's own
  holdings map through this batch path at D=1 and requires the NAV to match
  ``backtest.run`` exactly. Without it, a divergence in plumbing would masquerade as a
  difference in selection.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.backtest import BacktestResult, _weighting_rule
from src.clean import Panel
from src.config import Config
from src.decisions import ConfigError


@dataclass(frozen=True)
class NoiseBand:
    pnl: np.ndarray          # (n_draws,) final Total Net PNL per draw
    marks: np.ndarray        # (n_rebalances + 1, n_draws) value at each rebalance open
    master_seed: int
    n_draws: int

    def period_returns(self) -> np.ndarray:
        """
        (n_periods, n_draws) rebalance-to-rebalance returns. The risk side of the band.

        Named `period_` and not `quarterly_`: the arithmetic is `marks[1:]/marks[:-1]-1`
        and has always been cadence-agnostic, but the old name asserted a calendar the
        `FREQ` grid does not use.
        """
        return self.marks[1:] / self.marks[:-1] - 1.0

    def return_per_unit_risk(self, years: float) -> np.ndarray:
        """
        CAGR / annualised volatility per draw, both from the rebalance marks.

        The band answers "was V0's PNL unusual?". This answers the harder question
        "was it unusual *for the risk it took*?" — a concentrated momentum book in a
        bull market is systematically more volatile than a random one, so raw PNL alone
        cannot separate a better signal from a riskier one.

        Frequency-agnostic: `periods` is the number of rebalance marks this band
        actually has, not a fixed 20, so the annualisation is correct at any cadence.
        The *precision* is not — at quarterly this rests on ~20 observations and the
        resulting percentile is indicative only. At monthly (60), weekly (262) and daily
        (1,235) it is far better determined, which is an asymmetry `04_noise.py` prints
        rather than hides.
        """
        periods = self.marks.shape[0] - 1
        cagr = (self.marks[-1] / self.marks[0]) ** (1.0 / years) - 1.0
        vol = self.period_returns().std(axis=0, ddof=1) * np.sqrt(periods / years)
        return cagr / vol

    @property
    def sigma(self) -> float:
        return float(self.pnl.std(ddof=1))

    @property
    def sigma_stderr(self) -> float:
        """Standard error of the band's own sigma. Reported next to it so the
        significance threshold is not read as more precise than it is."""
        return self.sigma / np.sqrt(2.0 * (self.n_draws - 1))


def draw_seeds(master_seed: int, n_draws: int) -> list[np.random.Generator]:
    """One generator per draw, so batching never changes the result."""
    return [np.random.default_rng(s)
            for s in np.random.SeedSequence(master_seed).spawn(n_draws)]


def _rebalance_inputs(cfg: Config, panel: Panel, dates: pd.DatetimeIndex,
                      end: pd.Timestamp):
    """Arrays the batch path needs, extracted once rather than per chunk."""
    opens = panel.open.loc[dates].to_numpy(dtype=float)
    last_day = panel.dates[panel.dates <= end][-1]
    final_close = panel.close.loc[last_day].to_numpy(dtype=float)

    # Names that had not listed yet carry NaN. They can never be chosen (eligibility
    # requires a full window) and are never held, so their contribution is 0 x price --
    # but 0 x NaN is NaN, which would poison the whole row. `backtest.run` sidesteps this
    # only because pandas `.sum()` skips NaN; here it has to be explicit. The prices of
    # names actually chosen are asserted finite in `_run_batch`, so this densification
    # cannot hide a missing price for a name that matters.
    return np.nan_to_num(opens), np.nan_to_num(final_close), last_day


def _segment_events(panel: Panel, dates: pd.DatetimeIndex,
                    events: dict[pd.Timestamp, list[str]] | None,
                    end: pd.Timestamp) -> list[list[tuple[np.ndarray, np.ndarray]]]:
    """
    Per rebalance segment, the forced exits to apply as (column positions, open prices).

    Mirrors `backtest.run` exactly: an event landing on the rebalance date itself is
    already expressed by that day's targets, so only events strictly inside the segment
    fire. The band has to apply the same rule as the arm it adjudicates -- a strategy
    that dumps a name mid-quarter scored against a band that cannot would be measuring
    the rule, not the selection.
    """
    if not events:
        return [[] for _ in dates]

    position = {isin: i for i, isin in enumerate(panel.isins)}
    day_set = set(panel.dates)
    out: list[list[tuple[np.ndarray, np.ndarray]]] = []
    for r, day in enumerate(dates):
        stop = dates[r + 1] if r + 1 < len(dates) else None
        per_segment = []
        for e in sorted(events):
            if e <= day or e > end or e not in day_set:
                continue
            if stop is not None and e >= stop:
                continue
            cols = np.array([position[n] for n in events[e] if n in position], dtype=int)
            if not len(cols):
                continue
            prices = panel.open.loc[e].to_numpy(dtype=float)[cols]
            per_segment.append((cols, np.nan_to_num(prices)))
        out.append(per_segment)
    return out


def _run_batch(cfg: Config, opens: np.ndarray, final_close: np.ndarray,
               picks: list[np.ndarray], capital: float,
               seg_events: list[list[tuple[np.ndarray, np.ndarray]]] | None = None
               ) -> np.ndarray:
    """
    The batch engine: ``D`` portfolios advanced together through one holdings schedule.

    Every line mirrors `backtest.run` deliberately — the same mark at the open, the same
    B12 reserve, the same floor to whole shares, the same cost on gross traded notional.
    `assert_engine_equivalence` pins that correspondence to the rupee, because a
    divergence in plumbing here would masquerade as a difference in selection and every
    ``z`` in the ledger would be meaningless.

    ``picks[r]`` is a (D, k) array of *column positions* chosen at rebalance ``r``.
    Returns final PNL per draw and the (R+1, D) value marked at each rebalance open.

    Both B3 weighting rules live here, because the band has to be built on the *same*
    rule as the arm it adjudicates. A drift arm scored against a reset band would violate
    the "same engine" commitment that makes every ``z`` in the ledger meaningful.
    """
    rate = float(cfg["mandate.cost_bps"]) / 10_000.0
    reserve = 1.0 - float(cfg["execution.cost_reserve_multiple"]) * rate
    charge_build = bool(cfg["execution.charge_initial_build"])
    rule = _weighting_rule(cfg)

    n_draws = picks[0].shape[0]
    n_names = opens.shape[1]
    rows = np.arange(n_draws)[:, None]

    shares = np.zeros((n_draws, n_names), dtype=float)
    cash = np.full(n_draws, float(capital))
    marks = np.empty((len(picks) + 1, n_draws), dtype=float)

    for r, chosen in enumerate(picks):
        day_open = opens[r]
        chosen_open = day_open[chosen]
        assert np.isfinite(chosen_open).all() and (chosen_open > 0).all(), \
            f"a chosen name has no usable open price at rebalance {r}"

        # `shares @ day_open` would be a BLAS matrix-vector product whose accumulation
        # order depends on the number of rows, so chunking would perturb the last bit of
        # a few draws. An elementwise product with a numpy reduction is order-stable in
        # D, which keeps `chunk_size` a pure memory knob.
        value = (shares * day_open).sum(axis=1) + cash
        marks[r] = value

        target = np.zeros_like(shares)
        if rule == "reset":
            per_name = value * reserve / chosen.shape[1]
            target[rows, chosen] = np.floor(per_name[:, None] / chosen_open)
        else:
            # B3 drift, mirroring `backtest.run` line for line. A name is "held" when its
            # share count is non-zero, so a selected name that floored to zero shares last
            # time counts as an entry now -- the same test the scalar engine applies.
            selected = np.zeros_like(shares, dtype=bool)
            selected[rows, chosen] = True
            held = shares > 0.0

            target[selected & held] = shares[selected & held]      # retained: untouched
            proceeds = (np.where(held & ~selected, shares, 0.0) * day_open).sum(axis=1)
            sell_cost = np.abs(proceeds) * rate if (charge_build or r > 0) \
                else np.zeros(n_draws)

            entering = selected & ~held
            n_entering = entering.sum(axis=1)
            # B3-r: the reserve applies to deployable cash, not to book value.
            deployable = np.maximum((cash + proceeds - sell_cost) * reserve, 0.0)
            per_name = np.divide(deployable, n_entering,
                                 out=np.zeros_like(deployable),
                                 where=n_entering > 0)
            bought = np.floor(np.divide(per_name[:, None], day_open,
                                        out=np.zeros_like(shares),
                                        where=day_open > 0))
            target[entering] = bought[entering]

        notional = (target - shares) * day_open
        cost = np.abs(notional).sum(axis=1) * rate if (charge_build or r > 0) \
            else np.zeros(n_draws)
        cash = cash - notional.sum(axis=1) - cost
        assert (cash >= -1e-6).all(), f"negative cash at rebalance {r}"
        shares = target

        # Forced exits inside this segment (src/events.py). Reducing over the handful of
        # exited columns rather than over N keeps the accumulation order independent of
        # D, for the same reason the mark above avoids a BLAS matvec.
        for cols, prices in (seg_events[r] if seg_events else ()):
            gross = shares[:, cols] * prices
            cash = cash + gross.sum(axis=1) - np.abs(gross).sum(axis=1) * rate
            assert (cash >= -1e-6).all(), f"negative cash after a forced exit in segment {r}"
            shares[:, cols] = 0.0

    marks[-1] = (shares * final_close).sum(axis=1) + cash
    return marks[-1] - float(capital), marks


def band(cfg: Config, panel: Panel, eligibility: pd.DataFrame,
         dates: pd.DatetimeIndex, capital: float, end: pd.Timestamp,
         events: dict[pd.Timestamp, list[str]] | None = None) -> NoiseBand:
    """
    D2 (frozen): 10,000 draws of 10 names, resampled at every rebalance date, without
    replacement, from the as-of eligible set, charged the same costs, through the same
    engine.

    Drawing from ``eligibility`` rather than from the full universe is defence #6: names
    with unbroken 2021-25 history are survivors, and sampling them would hand the random
    portfolios the same advantage the strategy has, quietly making the band easier to beat.
    """
    if cfg["noise.sampling_frame"] != "as_of_eligible":
        raise ConfigError(f"D2 froze 'as_of_eligible'; got {cfg['noise.sampling_frame']!r}")
    if bool(cfg["noise.replacement"]):
        raise ConfigError("D2 froze sampling without replacement")
    if not bool(cfg["noise.rebalanced"]):
        raise ConfigError("D2 froze resampling at every rebalance date")
    if not bool(cfg["noise.charge_costs"]):
        raise ConfigError("D2 froze charging the band the same costs as the book")

    n_draws = int(cfg["noise.n_draws"])
    chunk = int(cfg["noise.chunk_size"])
    master_seed = int(cfg["noise.master_seed"])
    k = int(cfg["mandate.book_size"])

    opens, final_close, _ = _rebalance_inputs(cfg, panel, dates, end)
    seg_events = _segment_events(panel, dates, events, end)
    frame = [np.flatnonzero(row) for row in eligibility.to_numpy()]
    for r, positions in enumerate(frame):
        assert len(positions) >= k, f"only {len(positions)} eligible at rebalance {r}"

    # One generator per draw (not per chunk), so `chunk_size` is a memory knob that
    # cannot change a single rupee. tests/test_accounting.py pins this.
    generators = draw_seeds(master_seed, n_draws)

    pnl = np.empty(n_draws, dtype=float)
    marks = np.empty((len(dates) + 1, n_draws), dtype=float)
    for lo in range(0, n_draws, chunk):
        hi = min(lo + chunk, n_draws)
        picks = [np.stack([generators[d].choice(positions, size=k, replace=False)
                           for d in range(lo, hi)])
                 for positions in frame]
        pnl[lo:hi], marks[:, lo:hi] = _run_batch(cfg, opens, final_close, picks,
                                                 capital, seg_events)

    return NoiseBand(pnl=pnl, marks=marks, master_seed=master_seed, n_draws=n_draws)


def assert_engine_equivalence(cfg: Config, panel: Panel, v0: BacktestResult,
                              holdings_map: dict[pd.Timestamp, list[str]],
                              capital: float, end: pd.Timestamp,
                              events: dict[pd.Timestamp, list[str]] | None = None) -> None:
    """
    Run V0's own holdings through the batch path at D=1; the PNL must match
    `backtest.run` to the rupee.

    Without this the whole band is unfalsifiable: any difference between V0 and the
    random draws could be an artefact of the two engines disagreeing, and there would be
    no way to tell that from a real selection effect.
    """
    dates = pd.DatetimeIndex(sorted(holdings_map))
    opens, final_close, _ = _rebalance_inputs(cfg, panel, dates, end)
    seg_events = _segment_events(panel, dates, events, end)
    position = {isin: i for i, isin in enumerate(panel.isins)}
    picks = [np.array([[position[name] for name in holdings_map[day]]]) for day in dates]

    batch = float(_run_batch(cfg, opens, final_close, picks, capital, seg_events)[0][0])
    scalar = float(v0.nav.iloc[-1]) - float(capital)
    gap = abs(batch - scalar)
    assert gap <= 0.01, (
        f"batch and scalar engines disagree by \u20b9{gap:,.4f} under "
        f"{_weighting_rule(cfg)} weighting "
        f"(batch \u20b9{batch:,.2f}, backtest.run \u20b9{scalar:,.2f}) - the noise band "
        f"would be measuring plumbing, not selection"
    )


def z_score(variant_pnl: float, v0_pnl: float, band_: NoiseBand) -> float:
    """
    D11 (frozen): the change measured against the standard deviation of the whole band.

    Deliberately conservative — a variant shares most of its holdings with V0, so their
    difference varies less than either does alone, and this understates significance.
    Recorded as a number, never a pass/fail tick.
    """
    return (float(variant_pnl) - float(v0_pnl)) / band_.sigma
