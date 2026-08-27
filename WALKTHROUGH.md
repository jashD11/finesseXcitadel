# What we built, what we found — a walkthrough

**For teammates who read finance, not code.** Nothing here requires opening a Python file.
Every number below is produced by the repo and can be checked in the CSVs in `output/`,
which open in Excel.

Status as of **28 Aug 2026**: the strategy work is done and tested. The written report is
not yet started.

**One thing changed on 28 Aug that dwarfs everything else in this document, and a reader of
any earlier version needs to know it.** We had been picking stocks from *today's* index
membership, applied backwards to 2021 — which quietly hands the strategy a list of
companies partly chosen for having already gone up. We rebuilt the universe properly, from
NSE's own dated announcements, so that on any given day the strategy may only own what was
genuinely in the index that day.

**The headline fell from +876.5% to +388.0%.** More than half of it was never real. The new
Section 4a tells that story; it is the most important thing here.

Three smaller consequences follow from it. The best rebalancing frequency changed from
monthly to weekly. A conclusion we had published the day before — that resetting weights
beats letting them drift — reversed completely. And, counter-intuitively, the strategy
looks *better* once you adjust for risk than it did on the flattering universe.

---

## 1 · The brief, and what it implies

Pick at most 10 stocks from Nifty 100 + Nifty Midcap 100. ₹1 crore, 1 Jan 2021 to
31 Dec 2025, 10 bps per transaction. Ranked on **Total Net PNL** — rupees, not
risk-adjusted. Then the organisers re-run the model on Jan–Jun 2026.

Three consequences shaped every decision:

- **The metric is not risk-adjusted.** Concentration, volatility and beta are *rewarded*.
  Risk overlays, vol targeting and regime gates would all cost PNL, so they are excluded
  by design — not by oversight.
- **Costs barely matter — at quarterly speed.** We measured it: 0.38% a year. That stayed
  true up to monthly rebalancing (0.9%) but not at daily (3.7%), and Section 10 records
  where the claim stops holding. Turnover control was never a design priority, and it
  turned out not to need to be.
- **Luck dominates.** Ten names out of ~180 carries enormous dispersion. Two managers with
  identical (zero) skill can differ by many crores. This is the single most important fact
  about the project, and Section 6 is the response to it.

---

## 2 · Headline numbers

The baseline (V0: 12-1 momentum, top 10, equal weight, quarterly) on the corrected
point-in-time universe:

| | 2021–2025 | H1 2026 (out-of-sample) |
|---|---|---|
| **Total Net PNL** | **₹3,88,03,708** | **₹10,77,021** |
| Total return | +388.0% | +10.8% |
| CAGR | 37.34% | — |
| Max drawdown | −31.29% | −12.55% |
| Sharpe | 1.43 | — |
| Equal-weight universe | +151.6% | −0.05% |
| Nifty 100 index | +89.4% | −6.65% |
| Costs paid | ₹6,11,232 | — |

And the configuration we actually selected — the same rule rebalanced **weekly**, letting
weights **drift** between rebalances rather than resetting them:

| | 2021–2025 | H1 2026 |
|---|---|---|
| **Total Net PNL** | **₹4,85,51,143** | ₹5,43,597 |
| Total return | **+485.5%** | +5.4% |
| CAGR | 42.43% | — |
| Max drawdown | −30.64% | — |
| Sharpe | **1.64** | — |

For comparison, the same baseline on the old flattering universe read **₹8,76,46,846
(+876.5%)**, Sharpe 2.21. That number is still reproducible from this repo and is reported
alongside, because the gap between the two *is* the measurement (Section 4a).

Two arithmetic checks, both passing: the trade log rebuilds the closing NAV to within
**₹1**, and the P&L of all 106 individual round trips sums to Total Net PNL with a
**zero-rupee** gap.

---

## 3 · The data, and five things wrong with it

Prices come from Yahoo Finance; index membership from NSE's own constituent files. Before
running anything we went looking for defects, and found five worth knowing about. The
fifth was found late — on 27 Aug 2026, while building the frequency sweep — and it moved a
headline number, which is why it gets the space it does.

**Yahoo invented four trading days.** On 15 Jan, 1 May, 28 May and 26 Jun 2026 it
published prices for 189–200 stocks on days the exchange was shut. The tell: every one
had zero volume. All four sit inside the stress window. Our trading calendar is built from
days on which something actually traded, which drops all four while retaining the two
genuine Muhurat sessions.

**And a fifth, which that rule did not catch.** Our rule was "keep a day if *at least one*
stock traded". On **18 March 2025**, two did — so the day survived. But 191 of the 193
prices were *identical to the previous day's*, and the opening price equalled the previous
close for the same 191 names. The next day moved 3.4%, i.e. two days of movement in one. It
is a stale row, not a session.

Quarterly rebalancing never landed on it, so it went unnoticed for months. It surfaced the
moment we tested daily rebalancing, when the code asked "what traded yesterday?", got the
answer "two stocks", and **stopped with an error rather than proceeding on bad data**.

We excluded it by name, with the evidence recorded in `data/phantom_days.csv`, rather than
loosening the rule to "at least X% of stocks traded" — that threshold would have been a
number invented to fit a single observation. The cost of that choice, stated plainly: **the
next such day is caught only if someone looks.**

**It mattered more than one day should.** See Section 8 — removing it halved the 2026
result.

**Three corporate actions were mis-adjusted, and the defect is systematic.** We swept all
79 splits across 61 names. Yahoo back-adjusts only to 1 January of the action's year,
leaving earlier history at the pre-split level. Motilal Oswal showed a **−74.6%** single-day
"crash" that was really +1.55%. Same defect in CONCOR (Jul-25 bonus) and TRENT (Jun-26
bonus). All three corrected against NSE's corporate action records, with the correction
cross-checked against exchange closing prices.

**Two demergers deliberately left uncorrected.** Tata Motors (Oct-25, −40.2%) and Vedanta
(Apr-26, −64.9%) genuinely fell — holders received shares in the spun-off entity. Adjusting
requires an entitlement ratio NSE does not publish in this feed, and inventing one would be
fabricating data. Both are flagged and disclosed, with a standing rule attached: **any new
variant that holds either name across its ex-date must be re-checked.**

**For the baseline it does not matter:** V0 held Tata Motors once, in Q2 2021 — four years
before its demerger — and never held Vedanta, so the distortion never touched it. **For two
of the frequency variants it matters a great deal** — the weekly and daily portfolios both
held Vedanta across its demerger and each took a ~6.7% phantom loss in the 2026 window. The
standing rule is what caught it; Section 10 has the detail.

**26 names listed after the window opened.** Rather than drop them, a stock becomes
eligible once it has a full year of history. That cohort turned out to be a barbell, not a
systematic drag — some enormous winners, some losers.

Final panel: **1,786 trading days × 283 names, no gaps.** 183 names eligible at the first
rebalance, rising to 193 by 2026. One date, 19 Mar 2025, had only **2** eligible names —
the knock-on from the stale bar described above. It is excluded from the calendar.

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

**Weighting.** Equal — 1/10th each, reset at every rebalance. We later tested the
alternative (let the winners run, only trade what enters and leaves) at four different
rebalancing speeds. Resetting won every time — see Section 10.

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

## 4a · The universe was cheating, and fixing it cost half the return

This is the most important section in this document.

**The problem, in one sentence.** We were choosing our ten stocks from the list of
companies that are in the Nifty 100 and Midcap 100 *today* — but a company is in that list
today partly *because* it went up over the last five years.

Think about what that means. CGPOWER, BSE, RVNL, Mazagon Dock — none of these were index
names in 2019. They earned their place by rising tenfold. When our strategy "discovered"
them in 2021, it was choosing from a shortlist that somebody had already filtered using the
answer. That is not stock-picking; it is being handed the winners and asked to admire your
own judgement.

Everyone entering this competition has this problem. The original decision log conceded it
and moved on, on the stated grounds that *"no free 2021 membership list exists"*.

**That was wrong, and nobody had checked it.** NSE announces every single index change in a
dated press release, published at a predictable web address. We swept every weekday from
2019 to 2026 — 976 documents — and found **27 that change the Nifty 100 or Midcap 100**,
covering every review in the scoring window.

### How we rebuilt it, and why you can trust the rebuild

We started from today's published list and walked the announcements **backwards**. Undo the
March 2026 review, then September 2025, and so on back to the start of 2021.

The reason to do it backwards is that it checks itself. At every single step, three things
have to be true: every company the announcement *added* must already be in our list
(otherwise we have missed something), every company it *removed* must be absent, and the
list must still contain exactly 100 names. Miss one announcement and one of those three
breaks immediately.

It completes in 28 steps with all three holding throughout, landing on **100 Nifty 100
names and 99 Midcap 100 names** at the start of 2021, with no overlap.

Along the way the checks caught four things we would otherwise have got silently wrong:

- Table headings **repeat in the middle of a list** whenever a table runs across a page
  break in the PDF.
- One footnote — *"Excluded on account of exclusion from Nifty Midcap 150 index"* — ends the
  line on the bare number **150**, which our first parser cheerfully recorded as a stock
  ticker.
- Some announcements are later **cancelled**, usually with a replacement named in a
  differently-formatted follow-up. IREDA was announced for the Midcap 100 in March 2024,
  then withdrawn, with BSE put in its place.
- Three companies (MRF, Bank of Baroda, National Aluminium) demonstrably swap between the
  two indices in March 2021, and **no announcement returning them exists in any of the 976
  documents.** We waive those three by name, record exactly what we searched, and note that
  it does not matter for results: all three stay inside the pair of indices throughout, and
  the strategy only ever asks "is this stock in either one?"

We then had to buy the price history for 89 companies that were index members at some point
but are not in today's list. 83 of them are available. **Six are not** — including HDFC,
which merged into HDFC Bank, and Mindtree, which merged into LTIMindtree. Those six are
excluded and disclosed, which honestly puts a small amount of the original bias back.

### What it cost

Same rule, same dates, same engine. Only the list of stocks it may choose from changes.

| | Total Net PNL | Total return |
|---|---|---|
| Today's constituents (what we had) | ₹8,76,46,846 | +876.5% |
| **Point-in-time membership (correct)** | **₹3,88,03,708** | **+388.0%** |

**488 percentage points — more than half the headline — was index-inclusion bias.**

The benchmark moves too, so the honest way to read it is as the strategy's edge over its
own universe: **+592 pp before, +236 pp after.** The edge is real and large. It was also
being roughly doubled by the data.

### The part we did not expect

Fixing the universe made the raw number much worse and the *quality* of the result better.

Section 7 explains the risk-adjusted test properly, but the summary is this: on the old
universe, our strategy sat at the **63rd percentile** of random portfolios once you divided
by the risk it took — mid-pack, consistent with "it just bought volatile stocks". On the
corrected universe it sits at the **74th percentile**.

The flattering universe was inflating the headline *and* disguising the skill. Once every
stock in the pool is one you could genuinely have owned at the time, picking the right ten
of them counts for more.

---

## 5 · Where the +388% came from

Each rung below changes exactly **one** thing, run through the same engine, same dates,
same costs, on the corrected universe.

| Step | Change | Return | Attributable |
|---|---|---|---|
| Nifty 100 index | being invested at all | +89.4% | **+89 pp** |
| → equal-weight the point-in-time universe | weighting + cap tilt | +151.6% | **+62 pp** |
| → hold 10 names **at random** | concentration | +141.3% | **−10 pp** |
| → pick those 10 by momentum | **selection** | +388.0% | **+247 pp** |
| → rebalance weekly, let weights drift | cadence + weighting rule | +485.5% | **+98 pp** |

The third row is the *median* of 10,000 randomly-chosen 10-stock portfolios (Section 6), so
the concentration and selection rungs are measured rather than modelled.

> **This table has now been wrong twice.** The first version guessed at the numbers. The
> second measured them properly but on the flattering universe, which put selection at
> +611 pp. About three-fifths of that was the universe handing the rule pre-selected
> winners. We are keeping the history visible rather than quietly restating.

**Concentration does not raise expected return.** Holding 10 names instead of ~190 gave a
*median* of +141.3% against the benchmark's +151.6% — very slightly *worse*. What it does is
widen the range: those 10,000 random books span **+73.5% to +238.5%** between the 5th and
95th percentiles. Concentration buys dispersion, not expected return.

**Selection is the dominant term at +247 pp**, and Section 7 asks the harder question of
whether that is skill or just a bigger bet.

One earlier finding we can no longer quote: we previously reported that equal-weighting the
same 100 Nifty companies beat the cap-weighted index by +160 pp. That was measured on the
old universe and we have not rebuilt those two sub-benchmarks point-in-time, so weighting
and cap tilt are reported here as a single combined rung rather than carried over at
numbers that no longer apply.

---

## 6 · Is the result better than luck? The noise band

The core problem: ten names out of ~180 produces enormous dispersion by chance alone, so
"we beat the benchmark" proves very little. The equal-weight benchmark holds ~190 stocks;
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
| Worst of 10,000 | ₹15,91,046 |
| 25th percentile | ₹1,10,36,794 |
| Median | ₹1,41,32,086 |
| Mean | ₹1,46,74,219 |
| 95th percentile | ₹2,38,52,127 |
| 99th percentile | ₹2,89,65,933 |
| Best of 10,000 | ₹4,35,52,516 |
| **V0** | **₹3,88,03,708** |
| Standard deviation of the band | ₹50,92,127 |

**Four of the 10,000 random portfolios beat V0.** The 99.96th percentile, +4.74 standard
deviations above the random mean. On the old flattering universe this read *100th
percentile, zero of 10,000, +7.04 sigma* — fixing the universe cost about two sigma of
apparent edge, and the result still stands comfortably.

**Why this comparison is fair in a way the benchmark isn't.** Every objection we had raised
about our own number cancels out: the random books hold 10 names too, drawn from the *same*
eligible list on each date, on the *same* dates, with the *same* weighting and costs — and
since Section 4a, from the same point-in-time membership. The only difference is which
names got picked.

**Sanity check the band passes:** the mean random draw (₹1.47 Cr) sits just below the
equal-weight benchmark (₹1.52 Cr), with the median below the mean — the right-skew that
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
| Annualised volatility | 33.1% | median 19.9%, **max 30.8%** |
| Return per unit of risk | **1.13** | median 0.97, best 2.24 |
| Percentile | — | **V0 ranks 2,626th of 10,000** |

**V0 is still more volatile than every single one of the 10,000 random portfolios.** Per
unit of risk it sits at the 74th percentile — clearly above average, but nowhere near the
99.96th percentile the raw money figure suggests.

Put concretely: **if you scaled those 2,626 random portfolios up to V0's risk level, all of
them would have made more money than V0.** They only made less because they were playing
for smaller stakes.

**This is where fixing the universe changed the story, and it changed it in our favour.**
On the flattering universe the same measurement put V0 at the **63rd** percentile — mid-pack,
and this section used to conclude that momentum's edge was *"a risk premium rather than
stock-picking"*. At the 74th percentile that conclusion no longer holds cleanly.

> The honest reading that survives both runs: momentum does load on volatility — that is
> real, systematic, and under a raw-PNL metric perfectly legitimate — but it is **not only**
> a volatility loading. There is selection content the old universe was hiding.

---

## 8 · The out-of-sample test

Fresh ₹1 crore on 1 Jan 2026, two rebalances, nothing carried over from 2021–25.

| | H1 2026 |
|---|---|
| **V0** | **+10.77%** |
| Equal-weight universe | −0.05% |
| Nifty 100 index | −6.65% |
| V0 max drawdown | −12.55% |
| **V0's percentile** | **93.5%** of a fresh 10,000-draw band |

The selected weekly/drift configuration returns **+5.44%**, at the **95.5th percentile**.
All eight configurations we tested pass; none collapses.

Worth noting against the temptation to over-read this: quarterly scores *better* in 2026
than the configuration we chose. We chose weekly anyway, because weekly won on 2021–25 and
the rule is that 2026 may only reject, never select. That is the discipline working.

### This number was cut in half by a one-day data fix, and we are leaving the scar visible

Until 27 August this table read **+15.48%**, at the **98th percentile**, with only 185
random draws beating it. It was the strongest evidence in the whole project that the
strategy picks stocks rather than just taking more risk.

Then we found that **18 March 2025 is not a real trading day**. Yahoo published prices for
193 stocks, but 191 of them were *identical to the previous day's price*, and only 2 stocks
recorded any trading at all. It is a stale row, not a session.

Removing it barely touched the main result — ₹3.66 lakh on ₹8.8 crore. But the momentum
signal looks back twelve months, so a day removed in March 2025 shifts the twelve-month
window used for the January and April 2026 rebalances. Different window, different stocks
picked, and the 2026 result fell to **+7.69%**.

**One bad row of data was carrying about half the headline.** Nothing about the strategy
changed. We are recording this rather than quietly restating the number, because it is the
most honest available measure of how much weight *two rebalance dates* can carry.

### What survives the correction

**It is still evidence against the pure risk-premium reading, but weaker.** If V0 were only
a larger bet on a rising market, a flat-to-falling market should have punished it. The bet
size *was* still larger — V0's beta to the equal-weight universe is **1.28** here and
**1.31** over 2021–25, so the loading is stable and real. Beta alone predicted about
**+0.26%**. V0 returned **+7.69%**, at a *shallower* drawdown than the benchmark, in a
window where the median random 10-stock book made nothing at all.

That is still selection content the main-window risk test did not detect — about half as
much as we thought, and now with **1,379 of 10,000** random books beating it rather than
185.

**How much weight to put on it:** six months, two rebalance dates, one market regime, and
one stale data row away from a completely different headline. One observation, not a
refutation.

**Critically — this window was never used to choose anything.** It is a one-way rejection
filter: if a candidate collapses there, we drop it. We never go back and pick whatever
scores highest on 2026. Same data, opposite epistemics — rejecting fragile candidates is
robustness work; selecting on the test set is fitting it, and that is exactly what a
Citadel panel screens for.

---

## 9 · Where that leaves us

**What we know:**

1. **More than half the original headline was an artefact of the universe** (Section 4a).
   +876.5% became +388.0% once the strategy could only own what was genuinely in the index
   at the time. This is the single biggest finding in the project.
2. The strategy still beats chance on money, decisively — 9,996 of 10,000 random portfolios
   in the main window, 93rd percentile out-of-sample.
3. The selection rule is the dominant term (+247pp vs a random 10-stock book), with
   weighting and cap tilt worth +62pp and rebalancing rule and speed +98pp. Concentration
   itself adds nothing to expected return — it only widens the range of outcomes.
4. The rule loads on volatility. Real, repeatable, and rewarded under this scoring metric —
   **but it is no longer the whole story.** Per unit of risk the strategy sits at the 74th
   percentile on the corrected universe against the 63rd on the flattering one.
5. It survived out-of-sample, which is the one result that would have killed it.
6. **Rebalancing weekly and letting weights drift beats the quarterly baseline by
   ₹0.97 crore**, and rebalancing faster than weekly gives the gain back (Section 10).

**What is genuinely unresolved:** how much selection skill sits on top of the risk loading.
The risk-adjusted test says "some, but far less than the raw number implies". The 2026
window says "more than that". Both are single measurements over one regime.

**We are reporting both, with the tension stated rather than resolved.** Picking the
flattering one is the failure mode this whole exercise was built to avoid — and for a jury
screening on process, two results that disagree plus an honest account of why is a stronger
position than a tidy story.

**And the strongest evidence that the process has teeth is that it kept overturning us.**
Three published conclusions in this document were reversed by our own checks: a stale data
bar halved the out-of-sample result, the universe rebuild halved the headline, and the
weighting rule flipped outright.

---

## 10 · How often should we rebalance? The frequency sweep

The baseline rebalanced every quarter. That was chosen because quarter boundaries need no
defending, not because anything said it was best. So we measured it.

**Two things happen at a rebalance,** and they pull in opposite directions:

- we **re-pick** which 10 stocks to hold — doing this more often chases momentum faster;
- we **reset** all 10 back to equal weights — doing this more often sells whatever just
  went up, which fights momentum.

Rebalancing faster does *both* more often, so a simple speed test could not tell which
effect was responsible. We therefore ran a grid: **4 speeds × 2 weighting rules = 8
portfolios**, everything else identical. Total computing time: about 5 minutes.

### The answer: weekly, letting weights drift

Re-run on the corrected point-in-time universe. Best of the two weighting rules at each
speed:

| Rebalance every… | Total Net PNL | vs baseline | Sharpe | Costs |
|---|---|---|---|---|
| Quarter *(baseline)* | ₹3,88,03,708 | — | 1.43 | ₹6.11 L |
| Month | ₹4,28,70,507 | +₹0.41 Cr | 1.52 | ₹11.05 L |
| **Week** | **₹4,85,51,143** | **+₹0.97 Cr** | **1.64** | ₹26.79 L |
| Day | ₹3,54,59,887 | −₹0.33 Cr | 1.35 | ₹51.44 L |

**Both answers changed when the universe was fixed.** On the flattering universe this table
peaked at *monthly* and said resetting weights beat letting them drift. Point-in-time, the
peak moves to **weekly**, and **drift beats reset at every single speed** — reversing a
conclusion this document carried for exactly one day.

That reversal makes sense in hindsight, which is why we are labelling it as hindsight:
resetting to equal weights trims whatever just went up. In a universe stuffed with names
added *because* they had already run, there were more winners to trim and trimming them
looked free. On an honest universe it costs money, which is what the original objection to
resetting said all along.

The old table, for the record:

| Rebalance every… | Total Net PNL (old universe) | Sharpe |
|---|---|---|
| Quarter | ₹8,76,46,846 | 2.21 |
| **Month** | **₹10,76,49,806** | **2.42** |
| Week | ₹9,98,94,149 | +₹1.22 Cr | 2.33 | ₹45.19 L |
| Day | ₹9,29,46,976 | +₹0.53 Cr | 2.26 | ₹88.71 L |

**It is a hill, not a slope.** Speeding up helps until monthly and hurts after. Monthly is
better on the money *and* on risk — the drawdown is unchanged at −32%, so the extra ₹2
crore is not bought by taking bigger swings.

The plain reading: momentum in these stocks persists for roughly a month. Re-picking more
often than that means reacting to noise and selling positions before they have paid.

**Costs are not what decides it.** Daily rebalancing pays ₹68 lakh more than monthly, but
loses ₹1.47 crore. It is worse because it picks worse, not because it pays more.

### The weighting question, settled the other way round

We had recorded a worry for months: resetting to equal weights each time means *selling
your winners*, which ought to work against a momentum strategy. We had never tested it.

Tested at all four speeds, **resetting won every single time** — by ₹0.13 Cr, ₹1.28 Cr,
₹1.50 Cr and ₹0.61 Cr. And it wins while trading *less* than the alternative at quarterly
speed, so it is not a cost artefact.

The worry was backwards. With only 10 stocks, trimming whatever ran up and topping up
whatever lagged is a small, repeated profit — enough to outweigh the momentum it gives up.
That question is now closed on evidence rather than left open on an assumption.

### One trap worth describing, because we walked up to it

Every portfolio is scored against 10,000 random portfolios rebalanced on the same dates. At
daily speed, a *random* portfolio sells all 10 stocks and buys 10 new ones every single
day, paying a fee each time — about 37 times the portfolio's value traded per year. The
average random daily portfolio therefore **loses money**, and the spread of their outcomes
collapses to roughly a tenth of the quarterly spread.

Scores are measured in multiples of that spread. So the daily portfolio scores **+6.45**
against its own yardstick and **+0.62** against the fixed one — a tenfold difference caused
entirely by the yardstick shrinking, not by the portfolio being better. Reported carelessly,
the *worst* result in the grid would have looked like the best in the project.

We wrote that prediction down **before** running the grid, and we report both numbers. Only
the fixed yardstick may be compared between rows.

### A trap we did *not* walk into, because a standing check caught it

The 2026 out-of-sample numbers for the weekly and daily portfolios look terrible — **+1.6%
and +2.1%**, against monthly's +7.6%. The obvious story writes itself: fast rebalancing is
fragile.

That story is wrong. Both portfolios happened to be holding **Vedanta** on 30 April 2026,
the day it demerged. Vedanta's *price* fell 64.9%, but holders did not lose that money —
they received shares in the spun-off company. Our data is price-only and cannot see those
shares, a limitation we documented months ago (Section 3) and attached a standing rule to:
*any new variant holding a flagged name across its ex-date must be re-checked.*

Re-checked, the damage is:

| Portfolio | Vedanta weight | Phantom loss |
|---|---|---|
| Weekly | 10.5% | −6.8% of the portfolio |
| Daily | 10.4% | −6.7% of the portfolio |

**Roughly all of the gap is that one artefact.** The quarterly and monthly portfolios did
not hold Vedanta across that date and are unaffected.

This changes no decision — the demerger is in 2026, and monthly was chosen on 2021–25 data
that Vedanta never touched. But without the standing check we would have published a
confident and wrong explanation of why fast rebalancing fails.

### One prediction we got wrong

We also predicted the reset-versus-drift gap would keep widening as rebalancing got faster.
It widened from quarterly to weekly and then **narrowed at daily**. The prediction was
wrong and is recorded as wrong in the trial ledger, with the explanation labelled as
after-the-fact.

---

## 11 · Known biases, disclosed rather than buried

**Survivorship / index inclusion — measured, and now largely removed.** This was the
biggest problem in the project and Section 4a is devoted to it. The universe is now
point-in-time. The bias was worth **488 percentage points**, more than half the original
headline. Both numbers are reported.

**What remains of it.** Six companies that were index members in-window have no usable
price history (including HDFC and Mindtree, both of which merged into acquirers) and are
excluded. If one of them would have been a top pick at some rebalance, we skipped it and
cannot know. Three more (MRF, Bank of Baroda, National Aluminium) carry membership waivers
where we could not source the announcement returning them to their current index — harmless
for results, since all three stay inside the pair of indices throughout, but stated.

**Window specificity.** 2021–25 was exceptional for Indian mid-caps. A passive, brainless
equal-weight basket scored a Sharpe of **1.27** in this window — in a normal decade that
would be perhaps 0.5. The strategy is not shown to work in general, only over the mandated
window.

**Price return only.** Understates a dividend-reinvesting book by ~9pp (Section 3).

**Demergers are exited, not corrected.** A demerger prints a price crash the holder never
suffered — they received shares in the spun-off company that a price-only dataset cannot
see. NSE publishes no ratio to adjust for it, so instead we sell the position on the last
day it still trades with the entitlement attached. Conservative: we give up whatever the
spun-off company was worth. The random-portfolio baseline gets the identical rule.

**Concentration of profit.** One name (Mazagon Dock) is 10% of all profit; the top three
(with BHEL and RVNL) are 29%; the top five are 44%. Drop two or three lucky names and the
character of the result changes. Note these are *different* names from the ones that
dominated on the old universe — CGPOWER, BSE and GVT&D were largely artefacts of a
hindsight-picked list.

**Accuracy is beta-inflated.** 59.4% of round trips were profitable — but in a rising
market a dart-thrower scores well too. Against the benchmark over the same dates, only
**41.5%** of our trades won. Both numbers are reported; quoting only the first would be
misleading. The gap is the point: the strategy makes its money on the size of its winners,
not on being right more often than not.

---

## 12 · How the work is made checkable

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

76 automated tests currently pass.

---

## 13 · Reading the outputs yourself

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

## 14 · What is left

The **5–6 page report** is the main outstanding deliverable and has not been started.
**Section 4a is its spine** — a bias everyone carries, measured rather than conceded, with
a reconstruction that checks itself and two of our own published conclusions overturned in
the process. Sections 6 through 9 supply the rest: the noise band, the risk-adjusted test,
and the honest tension between the two windows.

Also outstanding: pushing the repository to GitHub.

Not planned: the machine-learning model. The attribution work shows the available headroom
is smaller than it looked, and it would need a look-ahead defence we would then have to
argue for. The composite-score variant (Section 4) remains the cheapest untried idea.
