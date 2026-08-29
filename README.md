# finesseXcitadel

A systematic, long-only equity strategy for the Finesse × Citadel Round 2 portfolio
construction challenge. At most 10 stocks drawn from the Nifty 100 and Nifty Midcap 100
indices, backtested 1 Jan 2021 – 31 Dec 2025 on ₹1 crore with 0.1% transaction costs, and
stress-tested on 1 Jan – 30 Jun 2026.

The universe is **point-in-time**: eligibility on any rebalance date is whichever stocks
were actually in either index on that date, reconstructed from NSE index-review press
releases. See [Data](#data).

Full narrative, no code required: **[`WALKTHROUGH.md`](WALKTHROUGH.md)**.
Every design choice and its reasoning: **[`DECISIONS.md`](DECISIONS.md)**.

## Results

Main window, 2021–25, after costs.

| | Total Net PNL | Return | CAGR | Sharpe | Max DD |
|---|---|---|---|---|---|
| **Selected: weekly rebalance, drifting weights** | **₹4,85,51,143** | **+485.5%** | 42.4% | 1.64 | −30.6% |
| V0 baseline: 12-1 momentum, quarterly, equal weight | ₹3,88,03,708 | +388.0% | 37.3% | 1.43 | −31.3% |
| Benchmark: equal-weight universe | ₹1,51,62,127 | +151.6% | — | — | — |
| Benchmark: Nifty 100 index | ₹89,41,008 | +89.4% | — | — | — |

V0 beats 9,996 of 10,000 random 10-stock portfolios drawn from the same eligible set on
the same dates. The configuration was selected on 2021–25 alone; the 2026 window is used
only as a one-way rejection filter.

**A three-feature composite signal was pre-registered, built and tested — all five arms
lost**, by −3.5σ to −5.2σ against the baseline. It is not adopted, and the negative result
is reported in full: [`WALKTHROUGH.md` §10a](WALKTHROUGH.md) for the narrative, `CLAUDE.md`
§11 for the arms and the scored predictions.

## Requirements

Python 3.12, with `pandas`, `numpy`, `scipy`, `yfinance`, `matplotlib`, `scikit-learn`,
`pyarrow`, `PyYAML`, `pytest`, `requests`, `xlsxwriter`.

## Usage

```bash
python3 scripts/01_fetch.py         # network. writes data/raw/. re-runs make zero calls
python3 scripts/08_pit_universe.py  # point-in-time universe -> a new dated snapshot
python3 scripts/02_clean.py         # raw -> validated panel + data quality report
python3 scripts/03_v0.py            # the backtest -> output/*.csv
python3 scripts/04_noise.py         # 10,000 random portfolios -> the significance band
python3 scripts/07_sweep.py         # cadence x weighting grid, 8 cells (~5 min)
python3 scripts/09_feature_diagnostics.py   # feature correlations + shapes. no PNL
python3 scripts/05_v1.py --arm base # the composite. --arm buffer|tilt|rm-solo
python3 -m pytest tests/ -q         # 92 pass
```

Steps 1, 8 and 2 must run before the rest, in that order. Add `--window stress` for the
Jan–Jun 2026 run. `03_v0.py`, `04_noise.py` and `05_v1.py` accept `--calendar` and
`--weighting` to run a single grid cell, writing under `output/sweep/<cell>/` and
`output/v1/<arm>/` so a variant cannot overwrite the baseline. `05_v1.py` runs no noise
band: every cell's band already exists and is read back and asserted, so an arm is scored
against a yardstick built before it existed. `06_report.py` is not implemented.

## Layout

```
config.yaml       every parameter. no number lives anywhere else in the repo
CLAUDE.md         the mandate, the strategy, the trial ledger
DECISIONS.md      the decision register — authoritative
WALKTHROUGH.md    the whole project explained without code
src/
  config.py       load + validate; refuses to run on an unresolved decision
  calendar.py     trading calendar, rebalance dates, the t-1 formation lag
  fetch.py        network only. never imported by the analysis path
  clean.py        panel construction, corporate actions, quality report
  membership.py   point-in-time index membership from NSE press releases
  universe.py     as-of eligibility: full window, tradeable, index member
  features.py     signal computation
  select.py       ranking, buffer, tie-break
  events.py       forced mid-cycle exits (index exits, unmodellable ex-dates)
  backtest.py     execution, costs, NAV, trades — signal- and weighting-agnostic
  metrics.py      round trips and every reported figure
  noise.py        the 10,000-draw significance band
scripts/          01_fetch 02_clean 03_v0 04_noise 05_v1 07_sweep 08_pit_universe
                  09_feature_diagnostics
tests/            config, causality, accounting, cleaning, selection
output/           nav, trades, holdings, weights, benchmarks, metrics (CSV)
output/v1/        one directory per pre-registered composite arm
output/diagnostics/  the feature correlation study behind the composite's design
```

## Data

**Prices:** Yahoo Finance via `yfinance`. **Index membership:** NSE constituent lists plus
27 dated index-review press releases, committed under `data/raw/press_releases/` as the
evidence behind the point-in-time universe. Membership is rebuilt by rolling today's
published list backwards; at every step each added name must already be present, each
removed name must be absent, and the list must stay at 100. A missed release breaks one of
those invariants immediately.

**Verified:** 1,786 trading days × 283 names, no interior gaps, 3 corporate-action
corrections applied and 2 handled by an exit rule, 5 non-sessions excluded from the
calendar. Adding 83 historical price series does not move the trading calendar — asserted,
because a new session would shift every positional lookback. See
`data/reports/data_quality.md`, which is generated rather than hand-written.

**Not committed:** `data/raw/*.parquet` and `data/clean/*.parquet` are excluded by
`.gitignore` — they are large and the scripts reproduce them. Snapshots are stamped with a
fetch date and are immutable: the code refuses to overwrite one, because Yahoo silently
revises history.

## How this repo is organised to be checkable

**Every parameter is in `config.yaml`.** There is no `get(key, default)` anywhere in
`src/` — a default in a getter is a design decision made in the dark, and a test greps for
the pattern. A parameter whose decision is still open is `null`, and reading it raises an
error naming the decision rather than guessing.

**`DECISIONS.md` records every choice**, including the ones that were rejected, and the
ones that were later found wrong and reversed. All 59 are now closed; two are recorded as
*dead* rather than answered, because the question ceased to exist rather than being
resolved.

**Variants are pre-registered before they are run.** The composite slate and its six
predictions were written into `CLAUDE.md` §11 before the first arm executed, and every arm
is reported with its predictions scored — including the two predictions that turned out
half wrong.

**`backtest.py` is signal- and weighting-agnostic.** It takes a holdings map and nothing
about how those names were chosen, so the baseline, every variant, the benchmark and all
10,000 noise draws run through one engine. An assertion pins the batched and scalar engines
to the rupee.

**`fetch.py` is never imported by the analysis path.** Network and analysis are separate
scripts with a file boundary between them.

**Causality is tested, not asserted.** `tests/test_causality.py` scrambles every price from
the rebalance date onward and requires the selected book to be unchanged — then scrambles
the formation window to prove the first test is not vacuous.

## Known limitations

Disclosed rather than hidden; see `DECISIONS.md` and CLAUDE.md §10.

- **Six historical members cannot be priced** (DHANI, GSPL, HDFC, ISEC, MINDTREE, PEL) and
  are excluded from the tradeable universe. This reintroduces a small amount of the
  survivorship bias the point-in-time universe removes.
- **Three names carry membership waivers.** MRF, BANKBARODA and NATIONALUM move between the
  two indices in March 2021 with no sourced release returning them. All three remain inside
  the union of the two indices throughout, which is what eligibility reads.
- **Price return only.** Dividends are excluded, understating a dividend-reinvesting book
  by roughly 9pp of median five-year return.
- **Demergers are exited, not corrected.** Positions are sold before the ex-date rather
  than adjusted by an entitlement ratio NSE does not publish.
- **Window specificity.** 2021–25 was an exceptional period for Indian mid-caps. The
  strategy is not shown to work in general, only over the mandated window.
