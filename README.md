# Finesse x Citadel — Round 2 Portfolio Construction Challenge

A systematic, long-only equity strategy over the Nifty 100 + Nifty Midcap 100 universe,
backtested 1 Jan 2021 – 31 Dec 2025 on ₹1 crore of virtual capital with 0.1% costs per
transaction.

**Current state: V0, the null model.** 12-1 momentum, top 10, equal weight, quarterly
rebalance, zero fitted parameters. It exists to be a baseline, not a submission — every
later change is measured as a delta against it.

> **New to the repo, or reading this from a finance rather than an engineering
> background?** Start with **[`WALKTHROUGH.md`](WALKTHROUGH.md)** — the full story of what
> was built, what was tested and what was found, with no code required.

---

## Running it

Requires **Python 3.12**. Dependencies: `pandas`, `numpy`, `scipy`, `yfinance`,
`xlsxwriter`, `matplotlib`, `scikit-learn`, `pyarrow`, `PyYAML`, `pytest`, `requests`.

```bash
python3 scripts/01_fetch.py     # network. writes data/raw/. re-runs make zero calls
python3 scripts/02_clean.py     # raw -> validated panel + data quality report
python3 scripts/03_v0.py        # the backtest. writes output/*.csv
python3 -m pytest tests/ -q
```

Steps 1 and 2 must run before step 3. `scripts/04_noise.py`, `05_v1.py` and `06_report.py`
are not yet implemented and print the decisions still blocking them.

## Data

**Source:** Yahoo Finance via `yfinance`, plus NSE constituent CSVs for index membership.
Both are pulled by `scripts/01_fetch.py`.

**Not committed.** `data/raw/*.parquet` and `data/clean/*.parquet` are excluded by
`.gitignore` — they are large, and `scripts/01_fetch.py` reproduces them. Snapshots are
stamped with a fetch date and are **immutable**: the code refuses to overwrite one,
because Yahoo silently revises history and an unpinned snapshot would make today's
result unreproducible tomorrow.

The committed `data/raw/universe_20260824.csv` (index membership),
`data/corporate_actions_overrides.csv` (the evidence-carrying correction table) and
`data/reports/` are small and are kept in the repo.

**Verified:** 1,787 trading days × 200 names, no interior gaps, 3 corporate-action
corrections applied and 2 disclosed. See `data/reports/data_quality.md`, which is
generated, not hand-written.

## Layout

```
config.yaml       every parameter. no number lives anywhere else in the repo
CLAUDE.md         the mandate, the strategy, the trial ledger
DECISIONS.md      the decision register — authoritative
src/
  config.py       load + validate; refuses to run on an unresolved decision
  calendar.py     trading calendar, rebalance dates, the t-1 formation lag
  fetch.py        network only. never imported by the analysis path
  clean.py        panel construction, corporate actions, quality report
  universe.py     as-of eligibility
  features.py     signal computation
  select.py       ranking, buffer, tie-break
  backtest.py     execution, costs, NAV, trades — signal-agnostic
  metrics.py      round trips and every reported figure
  noise.py        the 10,000-draw significance band   [not yet built]
scripts/          01_fetch  02_clean  03_v0  04_noise  05_v1  06_report
tests/            config, causality, accounting, cleaning, selection
output/           nav, trades, holdings, weights, benchmarks, metrics (CSV)
```

## How this repo is organised to be checkable

**Every parameter is in `config.yaml`.** There is no `get(key, default)` anywhere in
`src/` — a default in a getter is a design decision made in the dark, and a test greps
for the pattern. A parameter whose decision is still open is `null`, and reading it
raises an error naming the decision rather than guessing.

**`DECISIONS.md` records every choice**, including the ones that were rejected and why.
48 of them so far.

**`backtest.py` is signal-agnostic.** It takes a holdings map and nothing about how those
names were chosen, so V0, every later variant, the benchmark and all 10,000 noise draws
run through one engine. A variant that ran through different plumbing would not be
comparable.

**`fetch.py` is never imported by the analysis path.** Network and analysis are separate
scripts with a file boundary between them.

**Causality is tested, not asserted.** `tests/test_causality.py` scrambles every price
from the rebalance date onward and requires the selected book to be unchanged — and
scrambles the formation window to prove the first test is not vacuous.

## Known limitations

Disclosed rather than hidden; see `DECISIONS.md` and CLAUDE.md §10.

- **Survivorship / index inclusion.** The universe is today's index membership, applied
  from 2021. Names are partly in it *because* they rose. 20 of the 101 names in the
  Feb-2019 Nifty 100 are absent from today's universe.
- **Price return only.** Dividends are excluded, which understates a dividend-reinvesting
  book by roughly 9pp of median five-year return.
- **Two uncorrected demergers** (TMPV, VEDL) carry price drops a real holder did not
  suffer, because NSE does not publish the entitlement ratio needed to adjust them.
- **Window specificity.** 2021–25 was an exceptional period for Indian mid-caps. The
  strategy is not shown to work in general, only over the mandated window.
