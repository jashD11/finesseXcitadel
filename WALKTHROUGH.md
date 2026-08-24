# What we built, what we found — a walkthrough

**For teammates who read finance, not code.** Nothing here requires opening a Python file.
Every number below is produced by the repo and can be checked in the CSVs in `output/`,
which open in Excel.

Status as of 24 Aug 2026: the strategy work is done and tested. The written report is not
yet started.

---

## 1 · The brief, and what it implies

Pick at most 10 stocks from Nifty 100 + Nifty Midcap 100. ₹1 crore, 1 Jan 2021 to
31 Dec 2025, 10 bps per transaction. Ranked on **Total Net PNL** — rupees, not
risk-adjusted. Then the organisers re-run the model on Jan–Jun 2026.

Three consequences shaped every decision:

- **The metric is not risk-adjusted.** Concentration, volatility and beta are *rewarded*.
  Risk overlays, vol targeting and regime gates would all cost PNL, so they are excluded
  by design — not by oversight.
- **Costs barely matter.** At quarterly turnover, 10 bps is a rounding error. We measured
  it: 0.38% a year. Turnover control was never a design priority.
- **Luck dominates.** Ten names out of ~180 carries enormous dispersion. Two managers with
  identical (zero) skill can differ by many crores. This is the single most important fact
  about the project, and Section 6 is the response to it.

---

## 2 · Headline numbers

| | 2021–2025 | H1 2026 (out-of-sample) |
|---|---|---|
| **Total Net PNL** | **₹8,80,13,313** | **₹15,47,867** |
| Total return | +880.1% | +15.5% |
| CAGR | 57.90% | — |
| Max drawdown | −32.50% | −10.69% |
| Sharpe | 2.22 | 1.26 |
| Equal-weight universe | +284.9% | +0.20% |
| Nifty 100 index | +89.4% | −6.65% |
| Costs paid | ₹8,87,427 | ₹18,637 |

Two arithmetic checks, both passing: the trade log rebuilds the closing NAV to within
**₹1**, and the P&L of all 92 individual round trips sums to Total Net PNL with a
**zero-rupee** gap.

---

## 3 · The data, and four things wrong with it

Prices come from Yahoo Finance; index membership from NSE's own constituent files. Before
running anything we went looking for defects, and found four worth knowing about.

**Yahoo invented four trading days.** On 15 Jan, 1 May, 28 May and 26 Jun 2026 it
published prices for 189–200 stocks on days the exchange was shut. The tell: every one
had zero volume. All four sit inside the stress window. Our trading calendar is built from
days on which something actually traded, which drops all four while retaining the two
genuine Muhurat sessions.

**Three corporate actions were mis-adjusted, and the defect is systematic.** We swept all
79 splits across 61 names. Yahoo back-adjusts only to 1 January of the action's year,
leaving earlier history at the pre-split level. Motilal Oswal showed a **−74.6%** single-day
"crash" that was really +1.55%. Same defect in CONCOR (Jul-25 bonus) and TRENT (Jun-26
bonus). All three corrected against NSE's corporate action records, with the correction
cross-checked against exchange closing prices.

**Two demergers deliberately left uncorrected.** Tata Motors (Oct-25, −40.2%) and Vedanta
(Apr-26, −64.9%) genuinely fell — holders received shares in the spun-off entity. Adjusting
requires an entitlement ratio NSE does not publish in this feed, and inventing one would be
fabricating data. Both are flagged and disclosed. **We checked whether it mattered:** V0
held Tata Motors once, in Q2 2021 — four years before its demerger — and never held
Vedanta. So the distortion never touched our results.

**26 names listed after the window opened.** Rather than drop them, a stock becomes
eligible once it has a full year of history. That cohort turned out to be a barbell, not a
systematic drag — some enormous winners, some losers.

Final panel: **1,787 trading days × 200 names, no gaps.** 174 names eligible at the first
rebalance, rising to 193 by 2026.

### On dividends

We use **price returns only**. Measured: the median stock returned +173.8% on price alone
and +198.3% with dividends — a gap of roughly **9 percentage points** over five years. But
the *ranking* barely moves (rank correlation 0.99, 9 of the same top 10), so including them
would raise the number without changing which stocks we pick. Yahoo's dividend-adjusted
series also contains obvious errors, and the Nifty indices we compare against are
themselves price-only.

**This must be disclosed:** our PNL understates a dividend-reinvesting book by roughly 9pp
of median five-year return.

---

## 4 · The strategy

Deliberately the simplest thing that could work, with **zero fitted parameters**. Nothing
was optimised, so there is nothing to overfit — that is both the point and the defence.

**Signal — 12-1 momentum.** For each stock, the cumulative return from 252 trading days ago
to 21 trading days ago. In words: *how much did it rise over the past year, ignoring the
most recent month.* The month is skipped because very recent movers tend to mean-revert.

**Selection.** Rank all eligible names, take the top 10. No screens, no sector caps, no
buffer.

**Weighting.** Equal — 1/10th each, reset every quarter.

**Rebalancing.** First trading day of January, April, July and October. 20 dates.

**Execution discipline.**

- The signal uses prices only through **yesterday's close**; we fill at **this morning's
  open**. We can never rank a stock on a price we then trade at.
- **Whole shares only.** NSE does not trade fractions, so a backtest that buys 3.7 shares is
  describing orders that could not have been placed.
- 10 bps charged on every trade **including the opening purchase** — skipping that would
  flatter PNL by about ₹1 lakh.
- A small reserve is held back so the costs can actually be paid. This one was found by an
  assertion failing, not by a number looking wrong: ₹1 crore split ten ways and rounded to
  whole shares left ₹7,116 against a ₹10,000 build cost — the first rebalance was ₹2,884
  short of payable. We now hold back 2 × 10bps of the book, which guarantees it. **Cost:
  about 0.2% sits in cash permanently.** A tighter alternative existed; we chose the
  version whose guarantee doesn't depend on a loop converging.

**Eligibility.** A name must have a complete 252-day price history and must have traded the
previous day. Both are evaluated *as of* the rebalance date — never against what we know
today.

---

## 5 · Where the +880% actually came from

Before asking whether the strategy is good, we asked what produced the number. Each rung
below changes exactly **one** thing, run through the same engine, same dates, same costs.

| Step | Change | Return | Attributable |
|---|---|---|---|
| Nifty 100 index | being invested at all | +89.4% | **+89 pp** |
| → equal-weight *the same 100 names* | weighting | +249.8% | **+160 pp** |
| → add the mid-caps | universe | +284.9% | **+35 pp** |
| → hold 10 names **at random** | concentration | +265.1% | **−20 pp** |
| → pick those 10 by momentum | **selection** | +880.1% | **+615 pp** |

The fourth row is the *median* of 10,000 randomly-chosen 10-stock portfolios (Section 6),
so the bottom two rungs are measured rather than modelled.

> **Correction, 25 Aug 2026.** These two rows previously read *+421 pp concentration /
> +174 pp selection*. That came from levering the equal-weight benchmark 1.60× to match
> V0's volatility — which answers a different question, because **concentration is not
> leverage**. Holding 10 names rather than 182 multiplies your idiosyncratic risk; it does
> not multiply your market exposure per rupee. The old proxy overstated the concentration
> rung by roughly 440 pp and understated selection by the same amount.

**The finding that surprised us: same 100 companies, +89.4% cap-weighted versus +249.8%
equal-weighted.** The mega-caps that dominate the Nifty 100 underperformed the smaller
names *inside the same index*, so cap-weighting meant owning mostly the laggards. That one
choice is worth more than the entire index return — and roughly **4× more than the
large-vs-mid tilt** we had assumed was the dominant lever.

**The second finding: concentration does not raise expected return.** Holding 10 names
instead of 182 gave a *median* of +265.1% against the benchmark's +284.9% — very slightly
*worse*. What it does is widen the range: those 10,000 random books span **+155% to +429%**
between the 5th and 95th percentiles. Concentration buys dispersion, not expected return.

**Implication:** weighting is worth +160pp and comes free with the design. The selection
rule itself is worth **+615pp** — the dominant term. Section 7 then asks the harder
question of *why* it is worth that much, and the answer is not flattering.

---

## 6 · Is the result better than luck? The noise band

The core problem: ten names out of ~180 produces enormous dispersion by chance alone, so
"we beat the benchmark" proves very little. The equal-weight benchmark holds ~182 stocks;
we hold 10. Comparing them conflates *picking well* with *being concentrated*.

**The correct control for a 10-stock strategy is other 10-stock portfolios.**

So: draw 10 names **at random** from the same as-of eligible list, on the same dates, run
them through the identical engine — same capital, same equal weighting, same whole-share
rounding, same costs, same 20 rebalances. Re-draw at every rebalance. Record the final PNL.
**Repeat 10,000 times.**

A random draw contains zero forecasting content, so the entire spread of those 10,000
outcomes is *luck*.

| | Total Net PNL |
|---|---|
| Worst of 10,000 | ₹64,97,424 |
| 25th percentile | ₹2,14,02,002 |
| Median | ₹2,65,12,509 |
| Mean | ₹2,74,71,586 |
| 95th percentile | ₹4,29,39,785 |
| 99th percentile | ₹5,29,45,568 |
| Best of 10,000 | ₹8,05,50,575 |
| **V0** | **₹8,80,13,313** |
| Standard deviation of the band | ₹86,05,419 |

**Not one of the 10,000 random portfolios beat V0.** 100th percentile, +7.04 standard
deviations above the random mean.

**Why this comparison is fair in a way the benchmark isn't.** Every objection we had raised
about our own number cancels out: the random books hold 10 names too, drawn from the *same*
survivorship-affected list, on the *same* dates, with the *same* weighting and costs. The
only difference is which names got picked. Survivorship bias, in particular, affects both
sides identically — so it cannot be the explanation.

**Sanity check the band passes:** the mean random draw (₹2.75 Cr) sits just below the
equal-weight benchmark (₹2.85 Cr), with the median below the mean — the right-skew that
concentrated compounding must produce. If it hadn't, we'd have suspected a bug.

---

## 7 · But was it skill, or a bigger bet?

Raw PNL cannot separate *a better signal* from *a riskier one*.

Two players at the same card table. One bets ₹100 a hand, the other ₹1,000. The second wins
more money. Better player? No — bigger stake. To compare skill you look at winnings per
rupee wagered.

Momentum mechanically buys volatile stocks. The rule says *buy whatever rose most last
year*, and a stock that rose 600% is by definition a violent mover — a calm compounder can
never top that ranking. So we checked:

| Measured on the same basis as the band | V0 | The 10,000 random books |
|---|---|---|
| Annualised volatility | 39.5% | median 21.4%, **max 31.6%** |
| Return per unit of risk | **1.47** | median 1.38, best 2.70 |
| Percentile | — | **V0 ranks 3,704th of 10,000** |

**V0 was more volatile than every single one of the 10,000 random portfolios.** Per unit of
risk it is slightly above average and nowhere near the best.

Put concretely: **if you scaled those 3,704 random portfolios up to V0's risk level, all of
them would have made more money than V0.** They only made less because they were playing
for smaller stakes.

> Read on the main window alone, momentum's edge here looks like a **risk premium** —
> systematic, repeatable, and legitimate under a raw-PNL metric — rather than stock-picking.

*(Volatility is quoted here from quarterly rebalance marks so V0 and the random books are
measured identically. Against the benchmark on a daily basis the figures are 26.1% for V0
versus 16.3% — same conclusion, different measurement basis.)*

---

## 8 · The out-of-sample test — which disagrees

Fresh ₹1 crore on 1 Jan 2026, two rebalances, nothing carried over from 2021–25.

| | H1 2026 |
|---|---|
| **V0** | **+15.48%** |
| Equal-weight universe | +0.20% |
| Nifty 100 index | −6.65% |
| V0 max drawdown | −10.69% *(benchmark −13.51%)* |
| A fresh 10,000-draw band on this window | median **−₹12,584** |
| **V0's percentile** | **98.15%** — 185 draws beat it |

**This is evidence against the risk-premium reading.** If V0 were only a larger bet on a
rising market, a flat-to-falling market should have punished it. The bet size *was* still
larger — V0's beta to the equal-weight universe is **1.27** here and **1.31** over 2021–25,
so the loading is stable and real. But beta alone predicted about **+0.25%**. V0 returned
**+15.48%**, at a *shallower* drawdown than the benchmark, in a window where the median
random 10-stock book made nothing at all.

That is selection content the main-window risk test did not detect.

**How much weight to put on it:** six months, two rebalance dates, one market regime, and
185 random draws did beat it. One observation, not a refutation.

**Critically — this window was never used to choose anything.** It is a one-way rejection
filter: if a candidate collapses there, we drop it. We never go back and pick whatever
scores highest on 2026. Same data, opposite epistemics — rejecting fragile candidates is
robustness work; selecting on the test set is fitting it, and that is exactly what a
Citadel panel screens for.

---

## 9 · Where that leaves us

**What we know:**

1. The strategy beat chance on money, decisively — 10,000/10,000 in the main window, 98th
   percentile out-of-sample.
2. The selection rule is the dominant term (+615pp vs a random 10-stock book), with
   equal weighting worth a further +160pp and the mid-cap universe +35pp. Concentration
   itself adds nothing to expected return — it only widens the range of outcomes.
3. The rule systematically loads on volatility and beta. Real, repeatable, and rewarded
   under this scoring metric.
4. It survived out-of-sample, which is the one result that would have killed it.

**What is genuinely unresolved:** whether there is selection skill on top of the risk
loading. The 2021–25 risk test says no; the 2026 window says yes.

**We are reporting both, with the tension stated rather than resolved.** Picking the
flattering one is the failure mode this whole exercise was built to avoid — and for a jury
screening on process, two results that disagree plus an honest account of why is a stronger
position than a tidy story.

---

## 10 · Known biases, disclosed rather than buried

**Survivorship / index inclusion.** We use *today's* index membership applied back to 2021.
Names are partly in the index *because* they rose. Every team has this; the differentiator
is quantifying it — 20 of the 101 names in the Feb-2019 Nifty 100 are absent from today's
universe. Note this does **not** explain the noise-band result, since the random draws
carry the identical bias.

**Window specificity.** 2021–25 was exceptional for Indian mid-caps. A passive, brainless
equal-weight basket scored a Sharpe of **1.90** in this window — in a normal decade that
would be perhaps 0.5. The strategy is not shown to work in general, only over the mandated
window.

**Price return only.** Understates a dividend-reinvesting book by ~9pp (Section 3).

**Two uncorrected demergers.** Disclosed in Section 3; verified not to have touched our
results.

**Concentration of profit.** One name (GVT&D) is 16% of all profit; the top three are 33%;
the top five are 46%. Drop two or three lucky names and the character of the result changes.

**Accuracy is beta-inflated.** 67.4% of round trips were profitable — but the median stock
in this universe rose 176%, so a dart-thrower scores well too. Against the benchmark over
the same dates, only **48.9%** of our trades won. Both numbers are reported; quoting only
the first would be misleading.

---

## 11 · How the work is made checkable

These are the process guarantees, in plain terms. They matter because "trust me, the
backtest is right" is not a defensible position in a jury round.

**Every design choice was written down before the code was written.** 48 of them, each with
the options considered, the choice made, and the reasoning — including choices we rejected
and why. 42 are now closed; the 6 open ones relate to a more complex model we have not
built.

**The code physically refuses to run on an undecided question.** A parameter whose decision
is still open is left empty, and reading it raises an error naming the decision rather than
quietly using a sensible-looking default. You cannot accidentally ship an unexamined
assumption.

**Look-ahead is tested, not asserted.** We scramble every price from the rebalance date
onward and require the selected 10 names to be *identical*. A second test scrambles the
lookback window instead and requires the picks to *change* — otherwise the first test would
prove nothing.

**The random-portfolio engine is proven to be the same engine.** We run our actual
portfolio through the random-draw machinery and require it to produce the same rupee
figure. Without that, a difference between V0 and the random draws might just be two
calculators disagreeing.

**Results are exactly reproducible.** Same inputs, same random seed, same numbers, every
time — down to the last rupee, regardless of how the computation is batched.

**Data snapshots are frozen.** Yahoo silently revises history. Our download is date-stamped
and the code refuses to overwrite it, so a result computed today is reproducible tomorrow.

54 automated tests currently pass.

---

## 12 · Reading the outputs yourself

Everything in `output/` opens in Excel. Files ending `_stress` are the 2026 run.

| File | What's in it |
|---|---|
| `metrics.csv` | Every headline figure in one place. **Start here.** |
| `nav.csv` | Daily portfolio value, cash, and costs charged |
| `trades.csv` | Every execution: date, stock, side, shares, price, cost |
| `round_trips.csv` | The 92 complete entry-to-exit trades with P&L and return |
| `holdings.csv` | Share counts held, per stock, per day |
| `weights.csv` | Portfolio weights, per stock, per day |
| `benchmarks.csv` | The equal-weight universe and Nifty 100 series |
| `noise_band.csv` | All 10,000 random-portfolio outcomes |
| `noise_summary.csv` | The band's statistics and where V0 sits in it |
| `data/reports/data_quality.md` | The full data audit — generated, not hand-written |

Two documents carry the reasoning: **`DECISIONS.md`** is the authoritative record of every
choice, written in plain language. **`CLAUDE.md`** holds the mandate, the strategy, the
known biases and the trial ledger — every configuration ever evaluated, including the
failures, written as the work happened rather than reconstructed afterwards.

---

## 13 · What is left

The **5–6 page report** is the main outstanding deliverable and has not been started.
Sections 5 through 8 above are its natural spine — the attribution ladder, the noise band,
and the honest tension between the two windows.

Optionally: a semi-annual rebalance trial, which is a one-word configuration change. We are
not planning to pursue the more complex machine-learning model — the attribution work shows
the available headroom is small, and it would need a look-ahead defence we would then have
to argue for.
