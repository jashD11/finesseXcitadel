"""
The noise band (CLAUDE.md §5) — the decision rule for everything after V0.

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

from src.backtest import BacktestResult
from src.config import Config
from src.decisions import blocked


@dataclass(frozen=True)
class NoiseBand:
    pnl: np.ndarray          # (n_draws,) final Total Net PNL per draw
    master_seed: int
    n_draws: int

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


def band(cfg: Config, panel: pd.DataFrame, eligibility: pd.DataFrame,
         dates: pd.DatetimeIndex) -> NoiseBand:
    raise blocked("B4", "the execution conventions the band must share with the live "
                        "book — the band is only meaningful if it runs the identical "
                        "engine, so it inherits every open decision in backtest.run")


def assert_engine_equivalence(cfg: Config, panel: pd.DataFrame,
                              v0: BacktestResult,
                              holdings_map: dict[pd.Timestamp, list[str]]) -> None:
    """Run V0's holdings through the batch path at D=1; NAV must match to the rupee."""
    raise blocked("B4", "shared with band()")


def z_score(variant_pnl: float, v0_pnl: float, band_: NoiseBand) -> float:
    raise blocked("D11", "whether significance is measured against the level sigma or "
                         "a paired null that resamples the change itself")
