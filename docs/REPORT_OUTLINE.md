# Report handoff: structure, every number, and the two arguments that must be made

Written 2 Sep 2026, for whoever writes the 5–6 page report. This is the scaffold and the
data pack — not the report. It maps the organisers' requirements
(`docs/guidelines.docx` §9) onto sections, gives each a word budget, states what each must
claim, and names the file every figure comes from.

**One rule while writing: no number gets typed from memory.** Everything required is
generated. If a figure is not in one of the files in §0, it does not go in the report.

---

## 0 · The data pack — everything you need, and where it is

Regenerate all of it with `python3 scripts/06_report.py` and
`python3 scripts/13_config_ledger.py`.

| You need | File |
|---|---|
| Every metric guidelines §7 requires, formatted | `output/report/numbers.md` §1 |
| Benchmark comparison | `output/report/numbers.md` §2 |
| The noise band, raw and risk-adjusted | `output/report/numbers.md` §3 |
| **Liquidity: trade size vs traded volume** | `output/report/numbers.md` §5 |
| Out-of-sample H1 2026 result | `output/report/numbers.md` §6 |
| Portfolio composition and weights, 6 dates | `output/report/composition.md` |
| Longest-held names, with entry counts | `output/report/composition.md` |
| **Every configuration tested, all 63 runs** | `output/report/configurations.md` (readable) and `.csv` (machine) |
| Growth of ₹1 crore vs both benchmarks | `output/figures/01_growth.png` |
| The noise band chart | `output/figures/02_noise_band.png` |
| Drawdown curve | `output/figures/03_drawdown.png` |
| Cadence × weighting heatmap | `output/figures/04_cadence_grid.png` |
| Per-cell grid results | `output/sweep/summary.csv`, `sig_summary.csv`, `output/v1/wgt_summary.csv` |
| Data quality: counts, corrections, exclusions | `data/reports/data_quality.md` |
| The narrative trial ledger, with predictions scored | `docs/PROJECT.md` §11 |
| Every design decision, including the reversals | `docs/DECISIONS.md` |
| Mechanism reasoning and bug hunts | `docs/NOTES.md` |
| The story of how it was explored | `../WALKTHROUGH.md` |

---

## 1 · Budget

Target **2,600–3,000 words** and four figures across seven sections.

| § | Section | Words | Figures |
|---|---|---|---|
| 1 | Problem and strategy overview | 350 | — |
| 2 | Data | 400 | — |
| 3 | Methodology | 550 | — |
| 4 | Tools and software | 120 | — |
| 5 | Results and performance metrics | 600 | 1, 3 |
| 6 | Benchmark comparison | 300 | 1 |
| 7 | Limitations and discussion | 600 | 2, 4 |

**Sections 7 and the second half of 3 are where this submission is differentiated.**
Everyone will have a results table. Not everyone will have 59 configurations with
pre-registered predictions, a measured bias in their own universe, and an honest account of
where the strategy would fail.

---

## 2 · The two arguments that must be made, and are easy to get wrong

### A · The universe is forward-looking. Say it first, say it plainly, and give the number.

**This is the most important disclosure in the report, and burying it would be the single
worst editorial choice available.**

The universe is the Nifty 100 and Nifty Midcap 100 **as they stand today**, applied backwards
across 2021–25. The organisers specified this, so it is the correct thing to do — but it
means the eligible list was chosen with knowledge of the future, in two distinct ways:

1. **Index inclusion.** A stock is in today's Nifty 100 partly *because* it rose over
   2021–25. Buying "the top 10 by momentum from a list of companies that did well" is not
   the same experiment as buying the top 10 from the list available at the time.
2. **Survivorship.** Companies that were delisted, acquired, or fell out of the indices
   between 2021 and 2026 are absent from today's lists entirely. The strategy is never even
   offered them, so it can never be caught holding one on the way down.

**We measured effect 1 rather than describing it.** The point-in-time universe was rebuilt
from 27 dated NSE index-review press releases (committed in `data/raw/press_releases/`), and
the identical strategy was run on it:

| Same rule, same dates, same engine | Total Net PNL | Return |
|---|---|---|
| Today's constituents (mandated) | ₹8,76,46,846 | +876.5% |
| Point-in-time membership | ₹3,88,03,708 | +388.0% |

**Index-inclusion bias is worth 488 percentage points — more than half the headline.** The
strategy's edge over its *own* universe falls from +592pp to +236pp. Flipping one config word
(`universe.membership_mode`) reproduces either number, so an evaluator can check it.

**Three things to be careful about when writing this up:**

- **Distinguish the universe from the strategy.** The *strategy* has no look-ahead: the
  signal uses data strictly through t−1 and fills at t's open, and a test scrambles every
  price from the rebalance date onward and requires the book to be unchanged. All of the
  forward-looking content sits in the universe definition the mandate specifies. Say this
  explicitly — otherwise a reader may assume the backtest itself is compromised.
- **Do not over-claim the correction.** The edge *survives* it — the point-in-time run still
  beats 9,996 of 10,000 random books — but do not say the bias "doesn't matter". It halves
  the headline.
- **Do not present the point-in-time number as the result.** The mandated number is the
  submission. The point-in-time run is the *measurement of what the mandated number
  contains*.

### B · This maximises the scored metric. It is not what you would run with real money.

The mandate ranks on **Total Net PNL**, not on anything risk-adjusted. That single fact
drove the design, and the report should own it rather than let a jury raise it first.

**What the metric rewarded, and what we therefore did:**

- **Volatility is rewarded, so risk reduction is a handicap.** We excluded vol targeting,
  regime gates and beta hedging **by design and in writing before building anything**, not by
  omission. The strategy holds 10 names, fully invested, with no stop-loss and no drawdown
  control — and takes a **−32.4% maximum drawdown** as a direct consequence.
- **Concentration buys dispersion, not expected return.** We measured this: the median random
  10-stock book returns roughly what the equal-weight universe does. What 10 names buys is a
  much wider distribution of outcomes. Under a PNL-ranked competition, wide is good. Under a
  mandate to preserve a client's capital, wide is the problem.

**What a real deployment would need, and we would say so:**

| Real-world concern | What we did | What a live book would do |
|---|---|---|
| Drawdown | Accepted −32.4% | Position limits, a drawdown circuit-breaker, or a vol target |
| Concentration | 10 names, 1/10 each | Sector caps and a larger book |
| Costs | 0.1% per trade, as specified | Model STT, stamp duty, exchange fees, GST and slippage separately |
| Signal | One factor, unhedged | Diversify across factors; monitor factor crowding |
| Regime | None — always fully invested | Momentum crashes hard on sharp reversals; some regime awareness |

**One thing that is *not* a problem, and the report should say so with the number**, because
it is the first practical objection a jury raises: **liquidity**. Measured against each
name's 20-session average daily rupee volume, **99% of the 758 executions are under 1.82% of
that name's daily volume**, and the median is near zero. At ₹1 crore, market impact is
negligible. `output/report/numbers.md` §5.

**The honest closing line for §7** is roughly: *this configuration was selected to maximise
the metric the competition scores, on a universe the competition specifies; both of those
choices inflate the number relative to what a live, risk-managed book would have earned, and
both are stated rather than discovered.*

---

## 3 · Section-by-section

### §1 · Problem and strategy overview (~350 words)

**Lead with the rule, in two sentences**, so a reader could reimplement it: rank eligible
stocks by 12-1 momentum, hold the top 10 equal-weighted, rebalance monthly.

**Then the central idea, which is not the momentum rule.** It is that a 10-stock book out of
~190 has enormous luck-driven dispersion, so any result must be measured against what luck
alone produces. State the headline and the band together, never separately: ₹10,76,49,806,
and 0 of 10,000 random 10-stock books beat it.

State the exclusions (no optimiser, no risk overlay, no fitted parameter) and why — §2B.

*Source:* `numbers.md` §1; `docs/PROJECT.md` §3–§4.

### §2 · Data (~400 words)

Guidelines §9 asks for source, frequency, period, variables, cleaning.

- Yahoo Finance via `yfinance`, daily OHLCV, 2019-06-03 → 2026-08-24. Explain the 18-month
  pre-window buffer: the first rebalance needs a full 252-day lookback.
- Universe: NSE-published Nifty 100 + Midcap 100, today's lists (→ forward-looking bias, §2A,
  forward-reference §7).
- Cleaning with the numbers: a 1,786-day calendar built as the union of days any name traded;
  5 non-sessions removed; 3 corporate actions corrected against NSE records; 2 demergers with
  no published ratio handled by selling before the ex-date; zero interior gaps.
- **One sentence on what was checked and found wrong**, because it shows the process has
  teeth: a single stale bar (`2025-03-18`) that Yahoo printed but NSE never traded shifted
  every positional lookback after it and was worth roughly half of an earlier stress result.

*Source:* `data/reports/data_quality.md`; `docs/PROJECT.md` §13; `docs/DECISIONS.md` A8/A16/A17.

### §3 · Methodology (~550 words)

Four rules, each in its own short block:

1. **Selection.** 12-1 momentum, `P(t−21)/P(t−252) − 1`, computed through the close of t−1.
   Top 10 by rank. Eligibility needs a complete 252-day window, tradeable status from
   yesterday's volume, and index membership.
2. **Weighting.** Equal, 1/10, reset each rebalance. Say why not an optimiser: at 10 names an
   estimated covariance matrix is mostly noise, and the metric rewards return, not efficiency.
3. **Rebalancing.** Monthly, first trading day. 0.1% on traded notional, both sides, charged
   on every execution including the opening build.
4. **Causality.** The paragraph a quant panel looks for — see §2A's third bullet.

**Then how the configuration was chosen**, which is the differentiator. Every axis was
pre-registered with predictions before it ran and adjudicated against a band drawn
beforehand. **59 distinct configurations across 63 runs, and the simple rule won.** Use the
summary table from `docs/PROJECT.md` §15 or the full ledger in
`output/report/configurations.md`. Mention that the losing arms are reported with their
failed predictions.

### §4 · Tools (~120 words)

Python 3.12; pandas, numpy, scipy, yfinance, pyarrow, matplotlib, pytest. **No ML in the
submitted strategy** — say so explicitly, and note the composite-signal and diagnostic work
used scikit-learn and was rejected on measurement. One line on reproducibility: every
parameter in `config.yaml`, every stochastic step seeded (20260824), 95 tests.

### §5 · Results and performance metrics (~600 words)

**Reproduce the guidelines §7 table verbatim from `numbers.md` §1.** Do not paraphrase.

Then three things the table does not say:

- **Figure 1** (growth of ₹1 crore, log scale) with both benchmarks on the same axes.
- **Figure 3** (drawdown) — pair −32.4% with *when* it happened rather than leaving a scalar.
- **The band.** 0 of 10,000 random books beat the strategy; at the **96th percentile per unit
  of risk**, this is not merely a volatility loading. Report both and say why both are needed.

**The out-of-sample window belongs here:** +7.60% in H1 2026 against the Nifty 100's −6.65%,
at the 88.9th percentile of a fresh band. State that it was used **only** as a one-way
rejection filter, and that six months is one observation.

### §6 · Benchmark comparison (~300 words)

Guidelines §8 asks which benchmark and why. Use **both**:

- **Nifty 100** — the mandate-facing comparison, cost-free by construction: +89.4%.
- **Equal-weight universe** — the honest one: the same 200 names, same dates, same costs,
  same engine, equally weighted: +280.55%. This separates *stock selection* from *being
  invested in a rising universe*, and it is the much harder bar.

Say the quiet part: against the index the strategy is +987pp; against its own equal-weight
universe, +796pp. The second number is the one that measures the strategy.

### §7 · Limitations and discussion (~600 words)

Order matters. Lead with §2A (the forward-looking universe, 488pp, unhedged), then §2B (built
for the metric, not for a live book), then:

- **Window specificity.** 2021–25 was exceptional for Indian mid-caps; the strategy is not
  shown to work in general.
- **Price return only** — roughly 9pp of median five-year return understated.
- **Demergers exited, not corrected**; whole-share flooring on back-adjusted prices; one name
  (FORCEMOT) excluded for a 41-session data hole.
- **Liquidity is fine and here is the number** — §2B's last paragraph.

**Close on the negative results, not the positive one.** Figures 4 and 2 support the
strongest available claim: 59 configurations were tested, each pre-registered, and the
simplest rule won. A strategy that survived a search this wide and is reported *with* its
failures is a different object from one tuned until it looked good.

---

## 4 · Checklist before submitting (guidelines §11)

- [ ] Only Nifty 100 / Midcap 100 / Smallcap 100 stocks — yes, two of the three (the third
      was tested and rejected; `docs/DECISIONS.md` A19)
- [ ] ≤ 10 stocks — exactly 10
- [ ] 1 Jan 2021 – 31 Dec 2025 — yes
- [ ] ₹1 crore starting capital — yes
- [ ] 0.1% costs incorporated — yes, ₹20,59,816 charged
- [ ] Selection and weighting explained and consistently applied — §3
- [ ] All required metrics reported and reproducible from the code — §5, `numbers.md`
- [ ] Benchmark comparison included and discussed — §6
- [ ] GitHub repo with complete code and a clear README — done
- [ ] 5–6 page report covering data, methodology, tools, results, benchmark, limitations
