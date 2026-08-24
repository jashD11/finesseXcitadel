# Finesse x Citadel Portfolio Challenge

Round 2 submission. Everything except the decision register lives here; the decisions
themselves are in **`DECISIONS.md`**, which is the authoritative ledger.

---

## 1 · The mandate

| | |
|---|---|
| Universe | Nifty 100 + Nifty Midcap 100 (≈200 names). Smallcap 100 permitted by the rules but excluded by choice — see §6. |
| Book size | Maximum 10 stocks |
| Capital | ₹1,00,00,000 |
| Period | 1 Jan 2021 – 31 Dec 2025 |
| Costs | 0.1% per transaction |
| Direction | Long-only, fully invested |
| Primary metric | **Total Net PNL** = final value − ₹1 Cr. Not risk-adjusted. |
| Reported metrics | Absolute/total return, annualised return, MDD, Sharpe (ann. ret ÷ std dev of daily returns, rf = 0 — see `DECISIONS.md` D4), gain-to-loss ratio, accuracy, trade statistics (count, trades per stock, turnover) |
| Benchmark | Relevant index over the same window |
| Stress test | Organisers re-run on 1 Jan – 30 Jun 2026 |
| Deliverable | **GitHub repo + 5–6 page report.** Not Excel — the guidelines never mention it. Report covers data, methodology, tools, results, benchmark comparison, limitations |
| Constraint | Same core methodology applied consistently across all 10 stocks |

---

## 2 · Working rules

**Every design decision is run past the user before it is implemented.** No exceptions,
no defaults, no "I'll use the standard approach for now." A design decision is anything
where a reasonable person could pick differently and the resulting numbers would change.
If it's unclear whether something counts, it counts. Ask in this format:

> **Decision needed: \<name\>** / What it affects: \<one line\> / Options: (a) … (b) … (c) … /
> My recommendation and why: \<two lines\> / What breaks if we choose wrong: \<one line\>

Batch related decisions into one message. Never proceed past an unanswered one by picking
a default and flagging it later. Once answered, record it in `DECISIONS.md`, then
implement.

**Config over constants.** Every parameter lives in `config.yaml`. No number is buried in
a function body. There is no `get(key, default)` anywhere in `src/` — a default in a
getter is a design decision made in the dark, and a test greps for the pattern.

**Assertions over eyeballing.** Each phase ends with hard `assert` statements. No silent
NaN propagation.

**Causal only.** Any signal for a rebalance at *t* uses data strictly through *t*. State
the lag explicitly. Flag any place look-ahead could sneak in, even where it's avoided.

**Cache network pulls once.** Never re-fetch. Data pulls and analysis are separate steps
with a file boundary between them.

**No fabricated numbers, ever.** If a figure isn't computed from data in this repo, it
doesn't get stated. If something can't be verified, say so plainly rather than producing a
plausible-looking value. Push back if the user asserts something the data doesn't support.

**Trial ledger.** Every configuration evaluated gets a line in §11 below, written as the
work happens, not reconstructed afterwards.

**Seeds.** Every stochastic operation takes an explicit seed and logs it. The noise band
must be exactly reproducible.

**Consistency.** Code, documentation and chart legends must agree. If a rule changes in
code, grep for every place it's described in prose and fix those in the same pass.

### Not wanted

Code before decisions are answered. The tree ensemble built early because it's
interesting. Risk overlays, regime gates, vol targeting, beta hedging — excluded by design
(§3). Optimisers; equal weight, 1/10. **Any tuning against the Jan–Jun 2026 window** — it
is a rejection filter only, never a selection criterion (§9).

---

## 3 · What the scoring rule implies

Three consequences that drive every design choice.

**Beta is a large return term — but this section's original estimate was wrong.**
It claimed a 50/50 Nifty 100 / Midcap 100 blend compounds to roughly +115–120% and that
~85% of final PNL would come from being invested. Neither figure was derived from data in
this repo, and both are now measured (2021-01-01 → 2025-12-31, price return):

| | Return | PNL on ₹1 Cr |
|---|---|---|
| Nifty 100 index (`^CNX100`) | **+89.4%** | ₹0.89 Cr |
| Equal-weight universe, quarterly, after costs | **+284.9%** | ₹2.85 Cr |
| V0 (12-1 momentum, top 10) | **+880.1%** | ₹8.80 Cr |

So beta accounts for roughly a third of V0's PNL against the equal-weight benchmark, not
85%. The equal-weight number is far above the index because equal weighting tilts hard
toward mid-caps *and* because the universe is today's membership (§10).

**The band has since been run (§5)** and the gap is not luck: 0 of 10,000 random 10-stock
books matched V0. But it is also not per-unit-risk skill — V0 sits at the 63rd percentile
there. What the selection rule reliably does is load on volatility. §7 carries the full
attribution.

**Costs are close to irrelevant.** Measured on V0: gross turnover is **3.77× a year**
(both sides, and V0 resets all ten weights every quarter with no rank buffer), which at 10
bps is **0.38% p.a.** — ₹8.87 lakh against ₹8.80 Cr of profit. Higher than the 1–2× this
section originally guessed, still immaterial. Turnover control is *not* a design priority;
it only needs to be sane.

**Selection noise exceeds selection skill.** Ten equal-weight names against a 200-name
universe carries roughly 12–15% annual tracking error. Over five years that is a ±30–40 pp
swing — wider than the entire expected alpha. This is why §5 exists and why it is not
optional.

Implication: risk-reduction machinery is a handicap under this metric. Excluded by design,
not by omission.

---

## 4 · V0 — the null model

Build end-to-end first. It must produce a valid Excel deliverable. Everything afterwards
is measured as a delta against it.

- **Signal:** 12-month momentum, skipping the most recent month (12-1)
- **Selection:** top 10 by signal. No rank buffer — that arrives with V1
- **Weighting:** equal, 1/10
- **Rebalance:** quarterly, fixed calendar dates
- **Costs:** 0.1% on traded notional, both sides
- **Benchmark:** equal-weight portfolio of the full universe, same rebalance dates

No optimiser, no covariance estimation, no fitting. Zero free parameters to overfit, which
is both the point and the defence.

**Acceptance:** NAV runs the full window without gaps; trade log reconciles to the NAV
within ₹1; costs appear as an explicit line; benchmark series exists; Excel opens and is
readable by someone who has not seen the code.

---

## 5 · Noise band — the decision rule for everything after V0

Generate 10,000 random 10-stock portfolios over the same window, same rebalance calendar,
same costs, same engine. Record the distribution of final PNL.

A random draw carries no forecasting content, so the spread across those outcomes is pure
luck. Every subsequent modification is judged against it:

> If a change moves PNL by less than the noise band, nothing has been found.
> It is a resampling of luck.

Without this, the remaining days get spent chasing differences that cannot be
distinguished from chance — the standard failure mode of a 10-stock competition entry. It
is also the strongest single slide for the jury round: the distribution of random
outcomes, with our rule marked on it.

**Engineering.** Batched across draws, quarter by quarter. State is a dense `(D, N)`
holdings matrix — 10,000 × 200 float64, ~16 MB — which makes turnover a plain
`|target − current|` reduction with no index alignment. Seeding is
`SeedSequence(master_seed).spawn(n)`, one generator per draw, so `chunk_size` cannot change
a single rupee.

`assert_engine_equivalence` runs V0's own holdings through the batch path at `D = 1` and
requires an exact match against `backtest.run`. Without it, a divergence in plumbing would
masquerade as a difference in selection.

### Result — run 2026-08-24, seed 20260824, 10,000 draws

| | PNL |
|---|---|
| Mean random draw | ₹2,74,71,586 |
| Median random draw | ₹2,65,12,509 |
| σ of the band | ₹86,05,419 (± ₹60,853) |
| Worst / best draw | ₹64,97,424 / ₹8,05,50,575 |
| 95th / 99th percentile | ₹4,29,39,785 / ₹5,29,45,568 |
| **V0** | **₹8,80,13,313** |

**V0 sits at the 100th percentile. Zero of 10,000 random draws beat it; +7.04σ above the
random mean.** On the competition's own metric — Total Net PNL — this is unambiguous, and
it is not a survivorship artefact: the random draws are sampled from the *same* as-of
eligible set, so survivorship, concentration, costs, weighting and the calendar all cancel.

Consistency check the band passes: the mean random draw (₹2.75 Cr) sits just under the
equal-weight benchmark (₹2.85 Cr), with the median below the mean — the right-skew a
concentrated compounding book must produce.

### The same band, adjusted for the risk taken

Raw PNL cannot separate *a better signal* from *a riskier one*. A concentrated momentum
book in a bull market systematically holds higher-volatility names. So the band is also
read on return per unit of risk (CAGR ÷ annualised volatility, both from rebalance marks):

| | V0 | Random draws |
|---|---|---|
| Annualised volatility | **39.49%** | median 21.44%, max 31.64% |
| Return per unit of risk | **1.47** | median 1.38, max 2.70 |

**V0 is more volatile than every one of the 10,000 random draws, and on a risk-adjusted
basis it sits at the 63rd percentile — 3,704 draws match or beat it.**

**The honest reading: V0's extraordinary raw PNL is very largely the price of the risk it
took, not evidence of selection skill.** What 12-1 momentum reliably does here is *load on
volatility* — a real, systematic, repeatable property of the rule, and under a raw-PNL
scoring metric a legitimate and rewarded one (§3). What it does not demonstrate is an
ability to pick better stocks per unit of risk.

Both readings go in the report. Quoting only the first would be the exact failure this
section exists to prevent.

*Caveat:* volatility is estimated from ~20 quarterly marks, so the 63rd percentile is
indicative, not precise. The 100th-percentile PNL result does not depend on it.

---

## 6 · V1 — composite score

Only after V0 and the noise band exist.

Cross-sectional z-score composite, 4–6 features, **one per concept**. Averaging seventeen
features where six are momentum variants silently makes the composite 60% momentum.

- Momentum: 12-1 cumulative return
- Volatility: 60-day realised vol
- Liquidity: Amihud illiquidity or 20-day turnover
- Reversal or drawdown: 20-day return, or drawdown from 252-day peak

Each feature is z-scored **across stocks on the rebalance date** — never across time for
one stock — winsorised at ±3, then averaged with fixed weights. Fixed weights mean nothing
is fit, so there is no training window, no walk-forward, and no look-ahead question to
answer.

**Rank buffer:** a name enters at top 10 and is only evicted below top 20. Hysteresis, one
rule, kills most churn. An incumbent that becomes ineligible exits regardless of rank.

---

## 7 · What actually moves the number — measured, 2026-08-24

This section previously named **cap tilt** and **holding period** as the two levers. The
first claim is now measured and it is wrong: **weighting matters roughly four times more
than the cap tilt.** Each rung below changes exactly one thing, all through the same
engine, same dates, same costs.

| Step | What it adds | Total return | Attributable |
|---|---|---|---|
| Nifty 100 index (cap-weighted) | Being invested at all | +89.4% | **+89 pp** |
| → equal-weight *the same 100 names* | Weighting | +249.8% | **+160 pp** |
| → add the mid-caps (182 eligible) | Universe | +284.9% | **+35 pp** |
| → hold 10 names **at random** | Concentration | +265.1% (median of 10,000) | **−20 pp** |
| → pick those 10 by 12-1 momentum | Selection | +880.1% | **+615 pp** |

**Corrected 2026-08-25.** The bottom two rows previously read *+421 pp concentration /
+174 pp selection*, from levering the equal-weight benchmark 1.60× to match V0's
volatility and compounding it. That proxy was wrong: **concentration is not leverage.**
Holding 10 names instead of 182 multiplies *idiosyncratic* risk; it does not multiply
market exposure per rupee, which is what levering does. The proxy answered a different
question than the row claimed, and overstated the rung by roughly 440 pp.

The noise band already measures this rung directly — 10,000 portfolios that hold exactly
10 names with no selection content — so the corrected rows are measured, not modelled.

**Weighting.** Same 100 companies, same five years: **+89.4% cap-weighted vs +249.8%
equal-weighted.** The mega-caps that dominate the index underperformed the smaller names
*inside the same index*, so cap-weighting meant owning mostly the laggards. That one
choice is worth more than the entire index return. V0 inherits this advantage before
momentum picks a single stock.

**Cap tilt.** Real but smaller than assumed: EW Nifty-100 +249.8% vs EW Midcap-100
+324.4%, and blending them lands at +284.9%. Worth ~35 pp, not the dominant lever.
Smallcap 100 stays excluded — heaviest index-inclusion bias, and this is a reversible
*decision*, not a fact.

**Concentration.** Measured directly off the band, it contributes **roughly nothing to
expected return** — the median random 10-stock book returned +265.1% against the
equal-weight universe's +284.9%, i.e. −20 pp, and the mean −10 pp. What concentration does
is widen the *range*: the 5th-to-95th percentile of those random books spans **+155.0% to
+429.4%**. It buys dispersion, not expected return.

**Selection is the dominant term after all, at +615 pp** — but read it with §5. Momentum
does not pick better names *per unit of risk* (63rd percentile there); it systematically
picks the **high-volatility** names, which in a rising market pays. The distinction that
matters: *how many* names you hold (no effect) is not the same as *which* names the rule
selects (large effect, largely a volatility loading).

**Holding period.** Still untested. Costs do not constrain it. The question is whether the
strategy harvests momentum persistence (longer holds) or reversal (shorter). Quarterly is
the V0 baseline; semi-annual and monthly are one-word config changes (B1) awaiting trials.

**Consequence for the backlog.** The selection term is **+615 pp**, not the ~174 pp this
section claimed before the correction — so the signal matters far more than we had
concluded, and §5 confirms it is not luck (0 of 10,000 random draws matched it). What §5
*also* says is that most of that 615 pp is a volatility loading rather than per-unit-risk
skill. A different signal therefore has real room to move the number; whether any of §8's
candidates actually does is untested, and each still has to clear one band σ (₹86,05,419).

---

## 8 · Modification backlog

Ordered by expected value, not by interest. Nothing here is built until V0 and the noise
band are done, and nothing is kept unless it clears the band.

| # | Modification | Rationale | Risk | Status |
|---|---|---|---|---|
| 1 | Feature weight variants on the composite | Cheap to test, directly changes selection | Each variant is a trial; log it | Not started |
| 2 | Semi-annual vs quarterly rebalance | Holding-period effect, likely material | Fewer observations, noisier | Not started |
| 3 | Universe tilt toward midcap | Largest single PNL lever | Concentrates index-inclusion bias | Not started |
| 4 | Score-weighted instead of equal weight | Mild concentration into conviction | 1/N is hard to beat at 10 names | Not started |
| 5 | Sector cap (max 2–3 per sector) | Defensible, presents well | Reduces variance — works *against* PNL ranking | Not started; sector field confirmed as the `Industry` column |
| 6 | Pre-screen then rank | Top 5% of a weak forecast is noise-dominated | Adds a free parameter | Not started |
| 7 | Tree ensemble (RF / GBRT) | Reference implementation exists | Needs walk-forward and a look-ahead defence; expected gain below the band | Deliberately last |
| 8 | Regime overlay | — | **Excluded by design** — cash days are forgone PNL | Excluded |

Also queued: the **Feb-2019 constituent parallel backtest** for survivorship
quantification. Not a strategy trial — a bias measurement.

---

## 9 · Out-of-sample discipline

The Jan–Jun 2026 window is already-realised data that anyone can pull. It is not
out-of-sample in any meaningful sense.

**Rule:** select the configuration entirely on 2021–25. Use 2026 only as a one-way
rejection filter — if a candidate collapses there, drop it. Never go back and pick the
config that scores *highest* on 2026.

### V0's stress result — run 2026-08-24

Fresh ₹1 crore on 2026-01-01, two rebalances, nothing carried over (B8).

| | H1 2026 |
|---|---|
| **V0** | **+15.48%** (₹15,47,867) |
| Equal-weight universe | +0.20% |
| Nifty 100 index | −6.65% |
| V0 max drawdown | −10.69% (vs equal-weight −13.51%) |
| Noise band, 10,000 draws | median −₹12,584, σ ₹6,90,288 |
| **V0's percentile** | **98.15%** — 185 of 10,000 draws beat it, +2.22σ |

**Verdict: passes the filter. It did not collapse.** Nothing here was or may be used to
choose a parameter.

**And it complicates §5's reading, honestly.** The 2021–25 band said V0's edge looked like
a risk premium — mid-pack per unit of risk. If that were the whole story, a flat-to-down
market should have hurt it: V0's beta to the equal-weight universe is **1.27** here
(**1.31** over 2021–25 — the loading is stable and real). Beta alone would have predicted
roughly **+0.25%** against the benchmark's +0.20%. V0 returned **+15.48%**, at a shallower
drawdown than the benchmark.

So in this window the return is *not* explained by the volatility loading. That is evidence
for genuine selection content that §5's risk view did not detect.

**Weigh it accordingly:** six months, two rebalance dates, one market regime, and 185
draws did beat it. It is one observation, not a refutation of §5 — and §9 forbids
promoting it into a selection criterion. Both results go in the report, with the tension
between them stated rather than resolved.

**A16's open risk is closed for this run:** the stress book held none of VEDL, TMPV or
TRENT, so no uncorrected corporate action touched it.

Same data, opposite epistemics: rejecting fragile candidates is robustness work; selecting
for the best 2026 number is fitting the test set. The second is what a Citadel panel is
screening for.

---

## 10 · Known biases, disclosed rather than hidden

**Survivorship / index inclusion.** Backtesting today's constituents from 2021 includes
names promoted into the index *because* they rose. Every team carries it; the
differentiator is quantifying it. Measured: 20 of the 101 names in the Feb-2019 Nifty 100
are absent from today's universe.

**Window specificity.** 2021–25 was a strong period for Indian mid-caps. The strategy is
not shown to work in general, only over the mandated window.

**Price return.** Reported PNL understates a dividend-reinvesting book by roughly 9pp of
median five-year return (see `DECISIONS.md` A2).

**Two uncorrected demergers.** TMPV and VEDL carry price drops a real holder did not
suffer (see `DECISIONS.md` A16).

---

## 11 · Trial ledger

Every configuration evaluated gets one line, written **as the work happens**. "How did you
select this configuration?" will be asked. A ledger is the answer.

Rules: one line per configuration including failures · **nothing is ever deleted** · `z` is
the delta in noise-band standard deviations, recorded as a number rather than a pass/fail
because the rebalanced band sets a lower bar · the 2026 column is a **rejection filter
only** · seeds are logged for every stochastic run.

| Date | ID | What changed | PNL (₹) | Δ vs V0 (₹) | z | Cleared? | 2026 | Verdict |
|---|---|---|---|---|---|---|---|---|
| 2026-08-24 | `V0` | Baseline. 12-1 momentum (252/21), top 10, equal weight, quarterly, whole shares, B12 cost reserve. Zero fitted parameters. | 8,80,13,313 | — | +7.04 vs random mean | **100th pct** | not run | **Baseline.** Reconciles to the rupee; round-trip P&L sums to Total Net PNL with zero gap. Beats 10,000/10,000 random draws on PNL — but only the 63rd pct risk-adjusted. |
| 2026-08-24 | `NOISE` | The band itself (§5). 10,000 draws, seed 20260824, resampled each rebalance from the as-of eligible set, same engine (asserted), costs charged. | mean 2,74,71,586 | σ = 86,05,419 | — | — | n/a | **The measuring stick.** Engine equivalence asserted; `chunk_size` bit-exact across 4 values. |
| 2026-08-24 | `V0-2026` | Same model, B8 restart on the stress window. **Not a trial** — a rejection filter (§9). Nothing tuned on it, ever. | 15,47,867 | — | +2.22 vs random mean | **98.15th pct** | **pass** | Did not collapse. Beat EW (+0.20%) and Nifty 100 (−6.65%) with a shallower drawdown. Held no A16-flagged name. |
| 2026-08-24 | `NOISE-2026` | The band re-run on the stress window, same seed. Risk view suppressed — 2 marks is too few to estimate volatility. | median −12,584 | σ = 6,90,288 | — | — | n/a | Reference. The random 10-stock book made **nothing** in H1 2026, which is what makes V0's +15.5% informative. |
| 2026-08-24 | `BM-ew` | Reference, not a trial: equal-weight universe, same dates, same engine, costs charged. | 2,84,90,164 | −5,95,23,149 | — | — | not run | Benchmark. V0 is +₹5.95 Cr over it — **unadjudicated until the noise band runs.** |
| 2026-08-24 | `BM-idx` | Reference, not a trial: Nifty 100 index level, cost-free by construction. | 89,41,008 | — | — | — | not run | Benchmark. Mandate-facing comparison (guidelines §8). |
| 2026-08-24 | `BM-ew-n100` | Attribution rung: equal-weight the Nifty-100 constituents only. Isolates **weighting** from universe. | 2,49,78,801 | — | — | — | not run | Reference. vs `BM-idx`, equal-weighting the *same 100 names* is worth **+160 pp**. Rewrote §7. |
| 2026-08-24 | `BM-ew-mid` | Attribution rung: equal-weight the Midcap-100 constituents only. Isolates the **cap tilt**. | 3,24,43,730 | — | — | — | not run | Reference. vs `BM-ew-n100`, the mid-cap tilt is worth ~75 pp — far less than weighting. |

### Pre-registered trials

Declared before being run, so they are not post-hoc fishing.

| ID | Trial | Origin | Phase |
|---|---|---|---|
| `B3-drift` | Retained names keep their drifted weight; only entries and exits are traded, with exit proceeds spread across new entries. Config: `weighting.reset_to_target: false`. | `DECISIONS.md` B3, recorded `PROVISIONAL`. Resetting to 1/10 trims winners every quarter, which cuts against the momentum persistence §7 says paid. | 5 |

This requires `backtest.py` to be **weighting-agnostic as well as signal-agnostic** — if a
variant doesn't run through the identical engine, its PNL isn't comparable to V0's and the
noise band cannot adjudicate it.

---

## 12 · Repo layout

```
config.yaml            every parameter. no number lives anywhere else
CLAUDE.md              this file
DECISIONS.md           the decision ledger — authoritative
src/
  config.py            load + validate; refuses a value for an open decision
  decisions.py         UnresolvedDecision, blocked()
  calendar.py          trading calendar, rebalance dates, lag arithmetic
  fetch.py             network only. writes data/raw/. never imported by backtest
  clean.py             panel construction, corporate actions, flags, quality report
  universe.py          as-of eligibility          [STUB — C2]
  features.py          signal computation         [STUB — C2, C3, C8]
  select.py            ranking, buffer, tie-break  [STUB — C7]
  backtest.py          execution, costs, NAV, trades [STUB — B4-B7]
  metrics.py           round-trips and reported figures [STUB — D3-D5, D10]
  noise.py             the 10,000-draw band       [STUB — inherits backtest]
  excel.py             workbook writer            [NOT BUILT — the deliverable is a report]
scripts/               01_fetch  02_clean  03_v0  04_noise  05_v1  06_report
tests/                 conftest  test_config  test_causality  test_accounting  test_clean  test_selection
data/raw/              immutable, as-of stamped snapshots
data/clean/            validated panel
data/reports/          fetch log, data_quality.md (generated)
data/corporate_actions_overrides.csv
output/                nav, trades, holdings, weights, benchmarks, metrics, round_trips (CSV)
```

**Two structural commitments, expensive to reverse:**

- **`fetch` is never imported by `backtest`.** Network and analysis are separate scripts
  with a file boundary between them, which enforces cache-once mechanically.
- **`backtest.py` is signal-agnostic and weighting-agnostic.** It accepts a holdings map
  and nothing else. V0, V1, every backlog variant, the 2026 restart and all 10,000 noise
  draws run through one engine — otherwise the noise band is not comparable and §5 is
  worthless.

### Running it

```bash
python3 scripts/01_fetch.py       # once. re-runs make zero network calls
python3 scripts/02_clean.py       # raw -> panel + data quality report
python3 scripts/03_v0.py          # the backtest -> output/*.csv
python3 -m pytest tests/ -q
```

A stub script prints every config key still blocked and the decision blocking it.

---

## 13 · Data — what is verified

**Source:** Yahoo Finance via `yfinance`. All 200 symbols resolve with a `.NS` suffix.
Snapshot pinned at `data/raw/prices_20260824.parquet`: 332,450 rows, 2019-06-03 →
2026-08-24, zero null closes. Indices `^NSEI` and `^CNX100`.

**Panel:** `data/clean/panel_20260824.parquet`, **1,787 trading days × 200 names**, zero
interior gaps, 3 corporate-action corrections applied and 2 disclosed.

**Universe:** NSE constituent CSVs, browser User-Agent required (plain curl gets nothing).
100 rows each, disjoint, with the `Industry` column retained.

**Corporate-action adjustment, verified rather than assumed.** RELIANCE's Yahoo ÷ NSE-raw
ratio is a step function constant between actions (0.457166 → 0.461500 → 0.500000 →
1.000000), aligning with the 2020 rights issue, 2023 Jio demerger and Oct-2024 bonus.
DIVISLAB matched NSE exactly on price and volume; PERSISTENT matched exactly across a 1:1
bonus. But this does **not** generalise — see `DECISIONS.md` A16 for the three defects
found by sweeping all 79 splits.

**What does not work:** Stooq serves a JavaScript challenge to non-browser clients.
`NIFTY_MIDCAP_100.NS` is unreliable (1,610 observations against 1,643 for `^NSEI`, last
print five weeks stale) — build a Midcap benchmark from constituents instead. No free
Jan-2021 constituent snapshot exists; Wayback holds Feb-2019 and Aug-2023 only.

**Eligibility:** 174 names eligible at the first rebalance, rising to 193 by 2026-04.
Never below 174, so book size is never constrained.

### Available but not adopted

`/Users/jash/Desktop/Quant Research/qrtf_engine` (2.6 GB) holds an exchange-sourced
bhavcopy panel (5.03 M rows, 2013 → **2025-06-30**, ISIN-keyed), `lifecycle.csv` with 322
delisted and 194 acquired names, 806 detected corporate actions, 3,082 daily index files
carrying official **Nifty 100** and **NIFTY Midcap 100** closes, a point-in-time NSE-500
membership mask, and a resumable downloader.

Not adopted because it stops six months short of the scoring window and misses demergers.
Kept on the table for: exchange-sourced benchmarks (D1), survivorship quantification, and
an exhaustive Yahoo-vs-exchange audit over 2021-01 → 2025-06.

---

## 14 · Environment

Python 3.12.0 at `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3` —
five other interpreters exist on this machine and none has pandas, so there is no ambiguity
about which runs the repo.

pandas 2.2.2 · numpy 2.2.6 · scipy 1.14.0 · yfinance 0.2.65 · xlsxwriter 3.2.9 ·
matplotlib 3.9.0 · scikit-learn 1.5.1 · pyarrow 19.0.0 · PyYAML 6.0.1 · pytest 7.4.4 ·
requests 2.32.3.

Everything through backlog item 7 is installed; no new library is required, so no library
decision is forced. `openpyxl` is absent — xlsxwriter covers writing and we never read xlsx.

---

## 15 · Status

Deadline **31 August 2026** (the guidelines say 31; this file previously said 30). Today
**24 August 2026**.

**Done.** Skeleton, data acquisition, the full cleaning layer, **V0 end-to-end**, and
**the noise band**. 54 tests pass, 1 xfail-strict (V1 composite). Decisions A1–A16,
B1–B12, C1, C2, C6, C7, D1–D11 are closed — 42 of 48. The repo is a git repository with
a README.

V0: **Total Net PNL ₹8,80,13,313** (+880.1%), CAGR 57.90%, Sharpe 2.22, MDD −32.50%,
92 round trips, ₹8.87 lakh of costs. The trade log reconciles to the NAV to within ₹1 and
the round-trip decomposition sums to Total Net PNL with a zero-rupee gap.

**The noise band's verdict (§5):** V0 beats 10,000 of 10,000 random draws on PNL, but
sits at the 63rd percentile once risk is accounted for — over 2021–25 the edge reads as a
volatility loading, not stock-picking.

**The stress window disagrees (§9):** in a flat-to-down H1 2026, V0 returned +15.48% at
the 98th percentile of a fresh band, where the median random book made nothing and beta
alone predicted +0.25%. Two honest readings of the same strategy, in tension. Both go in
the report; neither gets resolved by picking the flattering one.

**Next, in order.**

1. **Push to GitHub and write the 5–6 page report.** Both are hard checklist items still
   at zero, and they are worth more marks than any further strategy work. The §5/§9
   tension is the report's most interesting section.
2. Then the backlog (§8), cheapest first — semi-annual rebalance (#2) is a one-word config
   change. The tree ensemble (#7) is almost certainly not worth the days it costs.

Still open: C3, C4, C5, C8, C9 (V1 composite), B10 (documentation only).
