# Point-in-time universe: the index-inclusion bias measurement

The V0 baseline (12-1 momentum, top 10, equal weight, **quarterly**, reset) re-run with
`universe.membership_mode: point_in_time`. Every other setting is unchanged, so the run differs
from `output/metrics.csv` only in which names the eligibility gate admits on each date.

| | Today's constituents (mandated) | Point-in-time |
|---|---|---|
| Total Net PNL | ₹8,76,46,846 (`output/metrics.csv`) | **₹3,88,03,708** (`metrics.csv` here) |
| Total return | +876.5% | +388.0% |
| Equal-weight universe | +284.9% | +151.6% |
| Random books beating it | 0 of 10,000 | 4 of 10,000 (`noise_summary.csv` here) |
| Risk-adjusted percentile | 62.97 | 73.74 |

876.5% − 388.0% = **488 percentage points** of index-inclusion bias.

**To regenerate:** set `membership_mode: point_in_time` in `config.yaml`, then run
`python3 scripts/03_v0.py` and `python3 scripts/04_noise.py`. Both scripts write to
`output/`, overwriting the quarterly baseline's files, so copy `metrics.csv` and
`noise_summary.csv` here, set the word back, and re-run both scripts. Runtime is about 6 s in total.
These two files were generated on 2026-09-27 from snapshot 2026-08-28. They match the figures
first recorded in `docs/PROJECT.md` §11 (`PIT-V0`, 2026-08-28) to the rupee.
