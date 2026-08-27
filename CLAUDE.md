# Finesse x Citadel Portfolio Challenge

Round 2 submission. Everything except the decision register lives here; the decisions
themselves are in **`DECISIONS.md`**, which is the authoritative ledger.

---

## 1 · The mandate

| | |
|---|---|
| Universe | Nifty 100 + Nifty Midcap 100, **point-in-time** — whoever was actually in either index on the rebalance date (`DECISIONS.md` A3/A17). 283 names ever eligible. Smallcap 100 permitted by the rules but excluded by choice — see §6. |
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

**Beta is a large return term — and this section has now been wrong twice, in the same
direction.** It first claimed ~85% of PNL would come from being invested; that was never
derived from data. It was then corrected against a universe built from *today's* index
membership, which inflated every row. Both are superseded. Measured on the point-in-time
universe (2021-01-01 → 2025-12-31, price return):

| | Return | PNL on ₹1 Cr |
|---|---|---|
| Nifty 100 index (`^CNX100`) | **+89.4%** | ₹0.89 Cr |
| Equal-weight universe, quarterly, after costs | **+151.6%** | ₹1.52 Cr |
| V0 (12-1 momentum, top 10, quarterly) | **+388.0%** | ₹3.88 Cr |
| **`PIT-wk-drift` (same rule, weekly, drift)** | **+485.5%** | **₹4.86 Cr** |

For comparison, the same rows on the old today's-constituents universe read +284.9% and
+876.5%. **Index-inclusion bias was worth 488 percentage points on V0** — more than half
the old headline (§10, `DECISIONS.md` A3).

**The band has since been run (§5)** and the gap is not luck: 0 of 10,000 random 10-stock
books matched V0. But it is also not per-unit-risk skill — V0 sits at the 63rd percentile
there. What the selection rule reliably does is load on volatility. §7 carries the full
attribution.

**Costs are close to irrelevant — at quarterly. The claim is cadence-conditional, and
§11's cadence grid measured how conditional.** On V0, gross turnover is **4.24× a year**
(both sides, resetting all ten weights every quarter with no rank buffer), which at 10 bps
is ₹6.11 lakh against ₹3.88 Cr of profit. Immaterial.

Across the cadence grid the bill spans 8×:

| | quarterly | monthly | weekly | daily |
|---|---|---|---|---|
| Gross turnover p.a. | 4.24× | 7.29× | 16.75× | 37.55× |
| Costs | ₹6.11 L | ₹11.05 L | ₹26.79 L | ₹51.44 L |

Even at the extreme this does not become the deciding term: daily loses to weekly by
₹1.09 Cr while paying only ₹25 L more, so cadence is a *selection* story, not a cost story.
Turnover control is still not a design priority — but "costs are irrelevant" is a
statement about quarterly rebalancing, not about the strategy in general.

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

### Result — run 2026-08-28 on the point-in-time universe, seed 20260824, 10,000 draws

| | PNL |
|---|---|
| Mean random draw | ₹1,46,74,219 |
| Median random draw | ₹1,41,32,086 |
| σ of the band | ₹50,92,127 (± ₹36,009) |
| Worst / best draw | ₹15,91,046 / ₹4,35,52,516 |
| 95th / 99th percentile | ₹2,38,52,127 / ₹2,89,65,933 |
| **V0** | **₹3,88,03,708** |

**V0 sits at the 99.96th percentile — 4 of 10,000 random draws beat it, +4.74σ above the
random mean.** On the old today's-constituents universe this read *100th percentile, 0 of
10,000, +6.99σ*. Fixing the universe cost about two sigma of apparent edge, and the result
still stands comfortably.

The comparison remains clean for the same reason it always was: the random draws are
sampled from the *same* as-of eligible set, so universe, concentration, costs, weighting
and the calendar all cancel.

Consistency check the band passes: the mean random draw (₹1.47 Cr) sits just under the
equal-weight benchmark (₹1.52 Cr), with the median below the mean — the right-skew a
concentrated compounding book must produce.

### The same band, adjusted for the risk taken

Raw PNL cannot separate *a better signal* from *a riskier one*. A concentrated momentum
book in a bull market systematically holds higher-volatility names. So the band is also
read on return per unit of risk (CAGR ÷ annualised volatility, both from rebalance marks):

| | V0 | Random draws |
|---|---|---|
| Annualised volatility | **33.06%** | median 19.93%, max 30.80% |
| Return per unit of risk | **1.13** | median 0.97, max 2.24 |

**V0 is more volatile than every one of the 10,000 random draws, and on a risk-adjusted
basis it sits at the 73.74th percentile — 2,626 draws match or beat it.**

**This moved in the strategy's favour when the universe was fixed, which is worth
noticing.** On the old universe the same figure was the 63.49th percentile, and this
section concluded that V0's raw PNL was "very largely the price of the risk it took, not
evidence of selection skill". On a point-in-time universe the risk-adjusted standing is
ten percentiles better even though raw PNL more than halved.

The reading that survives both runs: 12-1 momentum does load on volatility — a real,
systematic property of the rule, and under a raw-PNL metric a rewarded one (§3) — but it is
*not only* a volatility loading. At the 74th percentile per unit of risk it is no longer
mid-pack, though it is still far from the 99.96th percentile the raw number suggests.

Both readings go in the report. Quoting only the raw one would be the exact failure this
section exists to prevent.

*Caveat:* volatility is estimated from ~20 quarterly marks, so the 73.74th percentile is
indicative, not precise. The 100th-percentile PNL result does not depend on it.

*And the caveat weakens at higher cadence, which is an argument in the grid's favour.* The
same estimate rests on 60 marks at monthly, 262 at weekly and 1,235 at daily. §11's `FREQ`
arms therefore report a far better-determined risk view than V0 can — an asymmetry the
noise script now prints explicitly, so nobody reads "monthly has a risk number and
quarterly doesn't" as a property of the strategy rather than of the calendar.

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

## 7 · What actually moves the number — re-measured on the point-in-time universe

This section has been rewritten twice. The first version named cap tilt and holding period
as the two levers, from estimates never derived from data. The second measured a ladder
properly but did so on a universe built from **today's** index membership, which inflated
every rung above the index. Both are superseded; the old numbers are kept in §11 rather
than deleted.

Each rung below changes exactly one thing, all through the same engine, same dates, same
costs, on the point-in-time universe.

| Step | What it adds | Total return | Attributable |
|---|---|---|---|
| Nifty 100 index (cap-weighted) | Being invested at all | +89.4% | **+89 pp** |
| → equal-weight the point-in-time universe | Weighting + cap tilt | +151.6% | **+62 pp** |
| → hold 10 names **at random** | Concentration | +141.3% (median of 10,000) | **−10 pp** |
| → pick those 10 by 12-1 momentum | **Selection** | +388.0% | **+247 pp** |
| → rebalance **weekly**, let weights **drift** | Cadence + weighting rule | +485.5% | **+98 pp** |

**Selection is the dominant term, at +247 pp** — and unlike the previous version of this
table, that number is not resting on a hindsight-picked universe. The old ladder put
selection at +611 pp; roughly three-fifths of that was the universe handing the rule names
that had already risen enough to join an index.

**Weighting and cap tilt are now one rung.** The earlier version separated them (+160 pp
weighting, +35 pp cap tilt) using equal-weight Nifty-100 and equal-weight Midcap-100
benchmarks built on today's membership. Those two sub-benchmarks have **not** been rebuilt
point-in-time, so the split is not reported rather than carried over at values that no
longer apply.

**Concentration still contributes roughly nothing to expected return.** Measured directly
off the band: the median random 10-stock book returned +141.3% against the equal-weight
universe's +151.6%. What concentration buys is *dispersion* — the 5th-to-95th percentile of
those random books spans +73.5% to +238.5% — not expected return. *How many* names you hold
has no effect; *which* names the rule selects has a large one.

**Holding period is an inverted U, and the peak moved.** On the old universe the grid
peaked at monthly; point-in-time it peaks at **weekly**, with daily giving the gain back
(§11). Rebalancing faster than weekly trades against the momentum persistence the strategy
harvests. The direction of the effect is stable across both universes; its location is not,
which is a caution against reading the peak as a precise number.

**The weighting rule reversed outright.** On the old universe, resetting to 1/10 beat
letting weights drift at all four cadences. Point-in-time, **drift beats reset at all
four** (`DECISIONS.md` B3). The concern that kept B3 open for two years of project time —
that resetting sells your winners — turns out to be right; it only looked wrong in a
universe stuffed with names selected for having already run.

**Consequence for the backlog.** Selection is worth +247 pp and §5 says it is not luck
(99.96th percentile, and 73.7th per unit of risk). A better signal still has real room to
move the number, and each candidate has to clear one band σ — now **₹50,92,127**, not the
₹86,05,419 the old universe implied.

## 8 · Modification backlog

Ordered by expected value, not by interest. Nothing here is built until V0 and the noise
band are done, and nothing is kept unless it clears the band.

| # | Modification | Rationale | Risk | Status |
|---|---|---|---|---|
| 1 | Feature weight variants on the composite | Cheap to test, directly changes selection | Each variant is a trial; log it | Not started |
| 2 | ~~Semi-annual vs quarterly rebalance~~ → **the full `FREQ` cadence grid** | Holding-period effect, likely material | Fewer observations, noisier | **Done 2026-08-27.** Superseded by an 8-cell grid (4 cadences × reset/drift). **Monthly reset wins: +₹2.00 Cr, `z_qtr` +2.32.** §11 |
| 3 | Universe tilt toward midcap | Largest single PNL lever | Concentrates index-inclusion bias | Not started |
| 4 | Score-weighted instead of equal weight | Mild concentration into conviction | 1/N is hard to beat at 10 names | Not started — but note `FREQ` found **reset-to-1/N beats letting weights drift at every cadence**, so 1/N is if anything harder to beat than assumed |
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

### V0's stress result — re-run 2026-08-28 on the point-in-time universe

Fresh ₹1 crore on 2026-01-01, two rebalances, nothing carried over (B8).

| | H1 2026 |
|---|---|
| **V0** | **+10.77%** (₹10,77,021) |
| Equal-weight universe | −0.05% |
| Nifty 100 index | −6.65% |
| V0 max drawdown | −12.55% |
| **V0's percentile** | **93.47%** of a fresh 10,000-draw band |

**Verdict: passes the filter.** Nothing here was or may be used to choose a parameter.

### The whole grid against the same filter

All eight cells pass — none collapses. The selected cell (weekly, drift) returns **+5.44%
at the 95.45th percentile**.

| Cadence | reset | drift |
|---|---|---|
| quarterly | +10.77% (93.5 pct) | +11.97% (95.3 pct) |
| monthly | +6.35% (86.2) | +5.50% (83.1) |
| **weekly** | +6.17% (96.3) | **+5.44% (95.5)** |
| daily | +0.98% (100.0) | +0.18% (100.0) |

**A16's phantom-loss problem is gone, and that is a real change from the previous run.**
Until 2026-08-28, the weekly and daily arms held VEDL across its uncorrected 2026-04-30
demerger and booked a ~6.5pp loss no real holder suffered — an artefact large enough that
an earlier draft read it as evidence that fast rebalancing is fragile. B10's ex-date rule
now sells before the discontinuity in both the strategy and the band, so those rows are
comparable to the others for the first time.

**Weigh it accordingly:** six months, two rebalance dates at quarterly, one market regime.
It is one observation. §9 forbids promoting it into a selection criterion, and the winning
cell was chosen on 2021–25 alone — where, note, quarterly scores *best* in 2026 and still
loses the selection because it lost on the window that counts. That is the rule working.

### A previous version of this section was halved by a one-day data fix

Kept because it is the best evidence in the project that the process has teeth. Until
2026-08-27 this section reported **+15.48%, 98.15th percentile**. Removing a single stale
bar (`2025-03-18`, not a trading session) slid the positional 12-1 lookback for every
rebalance after it, and the figure fell to +7.69% at the 86th percentile. **One bad bar was
carrying roughly half the headline stress result.** Two rebalance dates are a very thin
reed, and the current +10.77% deserves the same scepticism.

Same data, opposite epistemics: rejecting fragile candidates is robustness work; selecting
for the best 2026 number is fitting the test set. The second is what a Citadel panel is
screening for.

---

## 10 · Known biases, disclosed rather than hidden

**Survivorship / index inclusion — measured and now largely removed.** The universe is
point-in-time (`DECISIONS.md` A3/A17): membership is whoever was actually in Nifty 100 or
Midcap 100 on the rebalance date, rebuilt from 27 NSE press releases and verified by
rolling today's list backwards under three invariants. Running the identical rule on the
old today's-constituents universe returns **+876.5%** against **+388.0%** — the bias was
worth **488 percentage points**, more than half the old headline. Both numbers are reported.

**A residue remains, and it leans the same way.** Six names that were index members
in-window have no usable price series (DHANI, GSPL, HDFC, ISEC, MINDTREE, PEL) and are
excluded. Two of them merged into acquirers. If one would have ranked top-10 at some
rebalance, we skipped a pick and cannot know it.

**Three membership waivers.** MRF, BANKBARODA and NATIONALUM swap between the two indices
in March 2021 with no sourced release returning them. All three stay inside the union
throughout, which is the only thing eligibility reads, but the per-index split is
approximate for them (A17).

**Window specificity.** 2021–25 was a strong period for Indian mid-caps. The strategy is
not shown to work in general, only over the mandated window.

**Price return.** Reported PNL understates a dividend-reinvesting book by roughly 9pp of
median five-year return (`DECISIONS.md` A2).

**Split-adjusted share counts.** B4 floors to whole shares on Yahoo's back-adjusted prices,
so the trade log's share counts are not the counts a real investor would have held.

**Demergers are exited, not corrected.** B10 sells before the ex-date rather than adjusting
for an entitlement ratio NSE does not publish. Conservative — we forgo the spun-off entity
— but it is a rule, not a correction.

---

## 11 · Trial ledger

Every configuration evaluated gets one line, written **as the work happens**. "How did you
select this configuration?" will be asked. A ledger is the answer.

Rules: one line per configuration including failures · **nothing is ever deleted** · `z` is
the delta in noise-band standard deviations, recorded as a number rather than a pass/fail
because the rebalanced band sets a lower bar · the 2026 column is a **rejection filter
only** · seeds are logged for every stochastic run.

**Two `z` columns as of 27 Aug 2026** (`DECISIONS.md` D11-r). `z_own` divides by the σ of a
band built on that row's *own* calendar and weighting — D2 taken literally, and the stronger
claim for any single row. `z_qtr` divides by a frozen quarterly σ — **₹86,05,419** for the
2026-08-24/27 rows built on the old universe, **₹50,92,127** for the 2026-08-28 `PIT-` rows
built on the point-in-time one. The two blocks are not comparable to each other and are not
meant to be; within each block `z_qtr` is the only
one of the two that may be read *down* the table, because the rebalanced band's σ is itself
a function of cadence (₹86.05 L quarterly → ₹8.22 L daily). A row's `z_own` is not
comparable to another row's `z_own` unless both share a calendar.

| Date | ID | What changed | PNL (₹) | Δ vs V0 (₹) | z_own | z_qtr | Cleared? | 2026 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 2026-08-24 | `V0` | Baseline. 12-1 momentum (252/21), top 10, equal weight, quarterly, whole shares, B12 cost reserve. Zero fitted parameters. | 8,80,13,313 | — | +7.04 vs random mean | baseline | **100th pct** | not run | **SUPERSEDED by `V0-r1` (2026-08-27)** — computed on a calendar that contained `2025-03-18`, a stale bar that is not a trading session (A8 rider). Kept per §11: nothing is deleted. |
| 2026-08-24 | `NOISE` | The band itself (§5). 10,000 draws, seed 20260824, resampled each rebalance from the as-of eligible set, same engine (asserted), costs charged. | mean 2,74,71,586 | σ = 86,05,419 | — | — | — | n/a | **The measuring stick.** Engine equivalence asserted; `chunk_size` bit-exact across 4 values. |
| 2026-08-24 | `V0-2026` | Same model, B8 restart on the stress window. **Not a trial** — a rejection filter (§9). Nothing tuned on it, ever. | 15,47,867 | — | +2.22 vs random mean | n/a | **98.15th pct** | **pass** | **SUPERSEDED by `V0-2026-r1`** — same stale-bar calendar. The 2025-03-18 bar sits inside the 252-day lookback for both 2026 rebalances, so it moved the picks. Kept per §11. |
| 2026-08-24 | `NOISE-2026` | The band re-run on the stress window, same seed. Risk view suppressed — 2 marks is too few to estimate volatility. | median −12,584 | σ = 6,90,288 | — | — | — | n/a | Reference. The random 10-stock book made **nothing** in H1 2026, which is what makes V0's +15.5% informative. |
| 2026-08-24 | `BM-ew` | Reference, not a trial: equal-weight universe, same dates, same engine, costs charged. | 2,84,90,164 | −5,95,23,149 | — | — | — | not run | Benchmark. V0 is +₹5.95 Cr over it — **unadjudicated until the noise band runs.** |
| 2026-08-24 | `BM-idx` | Reference, not a trial: Nifty 100 index level, cost-free by construction. | 89,41,008 | — | — | — | — | not run | Benchmark. Mandate-facing comparison (guidelines §8). |
| 2026-08-24 | `BM-ew-n100` | Attribution rung: equal-weight the Nifty-100 constituents only. Isolates **weighting** from universe. | 2,49,78,801 | — | — | — | — | not run | Reference. vs `BM-idx`, equal-weighting the *same 100 names* is worth **+160 pp**. Rewrote §7. |
| 2026-08-24 | `BM-ew-mid` | Attribution rung: equal-weight the Midcap-100 constituents only. Isolates the **cap tilt**. | 3,24,43,730 | — | — | — | — | not run | Reference. vs `BM-ew-n100`, the mid-cap tilt is worth ~75 pp — far less than weighting. |
| 2026-08-27 | `V0-r1` | **Re-baseline, not a trial.** Identical model; the *calendar* lost `2025-03-18` (A8 rider). The 12-1 lookback is positional (`cutoff_pos − 252`), so dropping one session slides the window start and moves the picks at the 3 rebalances after it. | 8,76,46,846 | −3,66,467 vs `V0` | −0.04 | −0.04 | **100th pct** | see `V0-2026-r1` | **The corrected baseline.** Every `Δ vs V0` below is measured against this. CAGR 57.79%, Sharpe 2.21, MDD −32.50%, costs ₹8,84,694. Still beats 10,000/10,000 on PNL; 63.49th pct risk-adjusted. |
| 2026-08-27 | `NOISE-r1` | The band re-run on the corrected calendar, same seed 20260824. | mean 2,74,71,586 | σ = 86,05,419 | — | — | — | n/a | **Byte-identical to `NOISE`.** The 20 rebalance dates and their eligible sets did not move — only V0's own momentum scores did. The measuring stick is unchanged, which is why `V0-r1` is directly comparable. |
| 2026-08-27 | `V0-2026-r1` | Stress window re-run on the corrected calendar. **Rejection filter only** (§9). | 7,69,462 | −7,78,405 vs `V0-2026` | — | n/a | **86.21st pct** | **pass** | **Still passes, but far less emphatically.** +7.7% vs EW +0.20% and Nifty 100 −6.6%; MDD −12.84% vs EW −13.51%. 1,379 of 10,000 draws beat it, +1.09σ — against 185 and +2.22σ before. One stale bar was carrying half the headline stress result. §9 rewritten. |
| 2026-08-27 | `FREQ-qt-drift` (absorbs the pre-registered `B3-drift`) | Quarterly cadence, **drift** weighting: retained names keep their drifted share count; only exits and entries trade (B3, B3-r). | 86,377,499 | -1,269,346 | -0.15 | -0.15 | **100th pct** | **pass** (+7.85%, 86.8th pct) | **B3's hypothesis is refuted at every cadence, starting here.** B3 feared that resetting to 1/10 'sells your winners' and cuts against momentum. It does not pay: drift is −₹12.69 L, and the gap widens at monthly and weekly. Turnover falls 3.77x → 3.05x and costs fall ₹1.40 L, so the loss is not a cost effect. |
| 2026-08-27 | `FREQ-mo-reset` | Monthly cadence (60 rebalances), reset weighting. One config word; nothing else changed. | 107,649,806 | +20,002,960 | +2.68 | +2.32 | **100th pct** | **pass** (+7.60%, 89.3th pct) | **The best cell in the grid and the sweep's answer.** +₹2.00 Cr over V0 on the metric that scores. Sharpe rises 2.21 → 2.42 and MDD is flat at −32%, so it is not bought with risk. Costs rise ₹8.85 L → ₹20.60 L and remain immaterial against the gain. |
| 2026-08-27 | `FREQ-mo-drift` | Monthly cadence, drift weighting. | 94,887,434 | +7,240,588 | +0.97 | +0.84 | **100th pct** | **pass** (+7.73%, 89.7th pct) | Beats V0 but loses ₹1.28 Cr to `FREQ-mo-reset`. The reset/drift gap is 10x its quarterly size — the cadence and the weighting rule genuinely interact, which is why the grid was run 2-D rather than as a single sweep. |
| 2026-08-27 | `FREQ-wk-reset` | Weekly cadence (262 rebalances, first trading day of each ISO week — B1 amendment), reset weighting. | 99,894,149 | +12,247,304 | +2.41 | +1.42 | **100th pct** | **pass** (+1.61%, 85.7th pct) — **but see A16: this arm holds VEDL across its uncorrected 2026-04-30 demerger, a ~6.5pp phantom loss. The 2026 figure understates it** | Past the peak. +₹1.22 Cr over V0 but ₹7.76 L short of monthly, at 2.2x the turnover. The cadence term is an **inverted U**, not a trend. |
| 2026-08-27 | `FREQ-wk-drift` | Weekly cadence, drift weighting. | 84,868,962 | -2,777,884 | -0.55 | -0.32 | **100th pct** | **pass** (+1.73%, 86.1th pct) — **but see A16: this arm holds VEDL across its uncorrected 2026-04-30 demerger, a ~6.5pp phantom loss. The 2026 figure understates it** | **Loses to V0** (−₹27.78 L). The largest reset/drift gap in the grid at ₹1.50 Cr. |
| 2026-08-27 | `FREQ-dy-reset` | Daily cadence (1,235 rebalances, `every_trading_day` — B1 amendment), reset weighting. | 92,946,976 | +5,300,131 | +6.45 | +0.62 | **100th pct** | **pass** (+2.06%, 100.0th pct) — **but see A16: this arm holds VEDL across its uncorrected 2026-04-30 demerger, a ~6.5pp phantom loss. The 2026 figure understates it** | **The row D11-r was written for.** `z_own` = +6.45 against `z_qtr` = +0.62 — a 10x gap created entirely by the denominator, exactly as pre-registered. Read `z_qtr`. PNL is ₹1.47 Cr below monthly on 10x the turnover; costs reach ₹88.71 L, which retires §3's 'costs are close to irrelevant' as an unconditional claim. |
| 2026-08-27 | `FREQ-dy-drift` | Daily cadence, drift weighting. | 86,809,592 | -837,253 | -1.02 | -0.10 | **100th pct** | **pass** (+2.18%, 100.0th pct) — **but see A16: this arm holds VEDL across its uncorrected 2026-04-30 demerger, a ~6.5pp phantom loss. The 2026 figure understates it** | **Loses to V0** (−₹8.37 L). Note the reset/drift gap *narrows* here to ₹61.37 L from weekly's ₹1.50 Cr — pre-registered prediction 3 said the gap would widen monotonically with cadence, and it does not. Recorded as a failed prediction. |
| 2026-08-27 | `NOISE-qt-drift` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean 27,455,773 | σ = 8,619,787 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-27 | `NOISE-mo-reset` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean 24,389,136 | σ = 7,457,268 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-27 | `NOISE-mo-drift` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean 24,377,125 | σ = 7,460,888 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-27 | `NOISE-wk-reset` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean 13,572,785 | σ = 5,081,178 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-27 | `NOISE-wk-drift` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean 13,558,269 | σ = 5,075,942 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-27 | `NOISE-dy-reset` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean -6,217,101 | σ = 821,336 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-27 | `NOISE-dy-drift` | Band for that arm: 10,000 draws, seed 20260824, **its own calendar and weighting** (D2 'same engine'). | mean -6,212,783 | σ = 821,924 | — | — | — | n/a | Reference. σ vs quarterly's ₹86,05,419 — this is the denominator behind that arm's `z_own`. |
| 2026-08-28 | `EXIT-rule` | **Not a trial — a correction.** B10/A18 forced mid-cycle exits in *both* engines: sell at the open of the last cum-entitlement session, hold cash to the next rebalance. | — | — | — | — | — | — | Fires on TMPV (2025-10-13) and VEDL (2026-04-29). V0 quarterly holds neither across an ex-date, so its PNL is **unchanged to the rupee**. The weekly stress arm, which does hold VEDL, goes **+1.61% → +8.6%**. Scheduling the exit *on* the ex-date instead gave +1.8% — the ex-date's open is already ex-entitlement, so the off-by-one silently does nothing. |
| 2026-08-28 | `PIT-V0` | **Re-baseline, not a trial.** Identical model on the **point-in-time universe** (A3 amended / A17): 283 names, membership from 27 NSE press releases, verified by a self-checking backward roll. | 3,88,03,708 | −4,88,43,138 vs `V0-r1` | — | — | **99.96th pct** | **pass** (+10.77%, 93.5th pct) | **The corrected baseline; every row below is measured against it.** CAGR 37.34%, Sharpe 1.43, MDD −31.29%, costs ₹6,11,232, 106 round trips. Index-inclusion bias was worth **488 pp**. Risk-adjusted percentile *rises* 63.49 → **73.74**. |
| 2026-08-28 | `PIT-NOISE` | The band rebuilt on the point-in-time universe, same seed 20260824, with the B10 exit rule applied to every draw. | mean 1,46,74,219 | σ = 50,92,127 (± 36,009) | — | — | — | n/a | **The new measuring stick.** σ falls from ₹86.05 L to ₹50.92 L. 4 of 10,000 draws beat `PIT-V0`, +4.74σ. Engine equivalence asserted with events active. |
| 2026-08-28 | `PIT-qt-drift` | Quarterly, drift weighting. | 3,92,95,173 | +4,91,465 | +0.10 | +0.10 | 99.95th pct | **pass** (+11.97%) | Beats reset — the first cell of a clean sweep for drift. |
| 2026-08-28 | `PIT-mo-reset` | Monthly, reset. | 4,14,36,423 | +26,32,714 | +0.57 | +0.52 | 100th pct | **pass** (+6.35%) | The cell that won on the *old* universe. Now third. |
| 2026-08-28 | `PIT-mo-drift` | Monthly, drift. | 4,28,70,507 | +40,66,798 | +0.88 | +0.80 | 100th pct | **pass** (+5.50%) | Sharpe 1.52. |
| 2026-08-28 | `PIT-wk-reset` | Weekly, reset. | 4,56,50,900 | +68,47,192 | +2.18 | +1.34 | 100th pct | **pass** (+6.17%, 96.3rd pct) | Sharpe 1.61. |
| 2026-08-28 | **`PIT-wk-drift`** | **Weekly cadence, drift weighting.** | **4,85,51,143** | **+97,47,435** | **+3.10** | **+1.91** | **100th pct** | **pass** (+5.44%, 95.5th pct) | **The selected configuration.** +₹0.97 Cr over `PIT-V0`, Sharpe 1.43 → **1.64**, MDD −31.3% → **−30.6%**. Chosen on 2021–25 alone; note quarterly scores *better* in 2026 and still loses, which is §9 working. |
| 2026-08-28 | `PIT-dy-reset` | Daily, reset. | 3,47,66,478 | −40,37,230 | −7.86 | −0.79 | 100th pct | **pass** (+0.98%) | **Loses to `PIT-V0`.** `z_own` −7.86 vs `z_qtr` −0.79 — the denominator gap D11-r predicted, in the other direction. Read `z_qtr`. |
| 2026-08-28 | `PIT-dy-drift` | Daily, drift. | 3,54,59,887 | −33,43,822 | −6.51 | −0.66 | 100th pct | **pass** (+0.18%) | Also loses. The cadence term is an inverted U peaking at **weekly**, not monthly. |

### `PIT` result — run 2026-08-28 on the point-in-time universe, seed 20260824, 8 cells, 291 s

Selected on 2021–25 alone (§9). PNL in ₹, `z_qtr` divides by the point-in-time band's
σ of ₹50,92,127.

| Cadence | reset PNL | drift PNL | drift − reset | `z_qtr` (best) | Sharpe | turnover p.a. | costs |
|---|---|---|---|---|---|---|---|
| quarterly (`PIT-V0`) | 3,88,03,708 | 3,92,95,173 | +4,91,465 | +0.10 | 1.43 | 4.24× | 6,11,232 |
| monthly | 4,14,36,423 | 4,28,70,507 | +14,34,084 | +0.80 | 1.52 | 7.29× | 11,04,610 |
| **weekly** | 4,56,50,900 | **4,85,51,143** | **+29,00,243** | **+1.91** | **1.64** | 16.75× | 26,79,370 |
| daily | 3,47,66,478 | 3,54,59,887 | +6,93,409 | −0.66 | 1.38 | 37.55× | 51,44,398 |

**The answer: weekly, drift.** +₹0.97 Cr over `PIT-V0`, `z_qtr` +1.91, Sharpe 1.43 → 1.64
with max drawdown slightly *better* at −30.6% against V0's −31.3%. It passes the 2026 filter at +5.44% (95.5th
percentile) and nothing was tuned on that window.

**Two findings reverse what the old universe said.** The cadence peak moved monthly →
weekly. And **drift now beats reset at every cadence**, where reset had beaten drift at
every cadence before — see `DECISIONS.md` B3, which records the reversal rather than
restating the conclusion.

### `FREQ` result — run 2026-08-27 on the superseded today's-constituents universe

Selected on 2021–25 alone (§9). PNL in ₹, `z_qtr` is the comparable column (D11-r).

| Cadence | reset PNL | drift PNL | reset − drift | `z_qtr` (reset) | Sharpe | turnover p.a. | costs |
|---|---|---|---|---|---|---|---|
| quarterly (V0) | 8,76,46,846 | 8,63,77,499 | +12,69,346 | 0.00 | 2.21 | 3.77× | 8,84,694 |
| **monthly** | **10,76,49,806** | 9,48,87,434 | +1,27,62,372 | **+2.32** | **2.42** | 7.36× | 20,59,816 |
| weekly | 9,98,94,149 | 8,48,68,962 | +1,50,25,188 | +1.42 | 2.33 | 16.20× | 45,19,048 |
| daily | 9,29,46,976 | 8,68,09,592 | +61,37,384 | +0.62 | 2.26 | 37.03× | 88,70,587 |

**The answer: monthly, reset.** +₹2.00 Cr over V0, `z_qtr` +2.32, Sharpe up from 2.21 to
2.42 with max drawdown unchanged at −32% — so it is not bought with risk. It passes the
2026 filter (+7.60%, 89.3rd percentile) and nothing was tuned on that window.

**The cadence term is an inverted U, not a trend.** Rebalancing more often helps up to
monthly and hurts after. That is the answer §7 asked for and could not previously give.

#### Scoring the four pre-registered predictions

**1 · Daily's `z_own` would be inflated. Confirmed, and larger than expected.** `z_own`
+6.45 against `z_qtr` +0.62 — a 10× gap produced entirely by the denominator. The daily
band's σ is **₹8,21,336** against quarterly's ₹86,05,419, and its **mean PNL is −₹62.17
lakh**: a random book re-drawing 10 of ~180 names every session pays 37× annual turnover
and loses money on commissions alone. Had only `z_own` been reported, the worst cell in the
reset row would have looked like the best result in the project.

**2 · §3's "costs are close to irrelevant" would not survive. Confirmed.** Costs run
₹8.85 L → ₹20.60 L → ₹45.19 L → ₹88.71 L, a 10× spread. Still not decisive — daily loses to
monthly by ₹1.47 Cr while paying only ₹68 L more — so cadence is not *primarily* a cost
story, but §3's claim is now cadence-conditional rather than general.

**3 · Reset and drift would diverge more as cadence rises. FAILED.** The gap widens
₹12.69 L → ₹1.28 Cr → ₹1.50 Cr from quarterly to weekly, then **narrows to ₹61.37 L at
daily**. The prediction was monotone and the data is not. Recorded as wrong rather than
reworded: at daily the book's composition churns so fast that few names are retained long
enough for a drifted weight to diverge from 1/10, so the two rules converge again. That is
a post-hoc explanation and is labelled as one.

**4 · No direction was predicted for cadence.** The answer is monthly.

#### What the grid says about B3

**Drift loses at every single cadence** — by ₹12.69 L, ₹1.28 Cr, ₹1.50 Cr and ₹61.37 L. B3
stood `PROVISIONAL` for two years of project time on the concern that resetting to 1/10
"sells your winners every quarter, which works against momentum". Measured, that concern is
**backwards**: resetting is worth money at every cadence tested, and drift also loses on
Sharpe in three of four. It is not a cost effect — drift trades *less* (3.05× vs 3.77× at
quarterly) and still loses.

The honest reading: at 10 names with a monthly-or-slower re-pick, trimming winners back to
1/10 is a rebalancing premium, not a momentum tax. B3 moves from `PROVISIONAL` to
**resolved in favour of reset**, on evidence rather than on the assumption that held it open.

---

### Pre-registered trials

Declared before being run, so they are not post-hoc fishing.

| ID | Trial | Origin | Phase |
|---|---|---|---|
| `B3-drift` | Retained names keep their drifted weight; only entries and exits are traded, with exit proceeds spread across new entries. Config: `weighting.reset_to_target: false`. | `DECISIONS.md` B3, recorded `PROVISIONAL`. Resetting to 1/10 trims winners every quarter, which cuts against the momentum persistence §7 says paid. | 5 |
| `FREQ` | **The frequency sweep — 8 arms, declared 27 Aug 2026 as one grid.** 4 cadences × 2 weighting rules, every cell through the identical engine. Absorbs `B3-drift` as its quarterly-drift cell. | §7 records holding period as untested and asserts "costs do not constrain it"; `DECISIONS.md` B1 queued alternative cadences. | 5 |

This requires `backtest.py` to be **weighting-agnostic as well as signal-agnostic** — if a
variant doesn't run through the identical engine, its PNL isn't comparable to V0's and the
noise band cannot adjudicate it.

#### `FREQ` — the grid, and what we expect to find

|  | quarterly | monthly | weekly | daily |
|---|---|---|---|---|
| **reset** (V0 rule) | `V0` *(exists)* | `FREQ-mo-reset` | `FREQ-wk-reset` | `FREQ-dy-reset` |
| **drift** (B3) | `FREQ-qt-drift` | `FREQ-mo-drift` | `FREQ-wk-drift` | `FREQ-dy-drift` |

Every cell gets its own noise band on its own calendar *and* weighting, so the grid is 14
new ledger rows (7 trial + 7 band). Each is scored twice per D11-r.

**Four predictions, recorded before the runs so they cannot be retrofitted.** The grid is a
sweep, not a hypothesis test — but stating what we expect is what separates a result from a
rationalisation.

1. **Daily's `z_own` will be large and meaningless.** The rebalanced band's σ collapses with
   cadence and the daily band's mean PNL goes *negative*, because a random book re-drawing
   10 of ~180 names every session pays ~470× annual turnover. Read `z_qtr` for that row.
2. **§3's "costs are close to irrelevant" will not survive the sweep.** It was measured at
   3.77× turnover. Costs scale roughly with cadence, so the daily arms will pay an order of
   magnitude more, and §3 becomes a cadence-conditional claim.
3. **Reset and drift will diverge more as cadence rises.** At quarterly the two rules differ
   4 times a year; at daily, reset trims every winner every session. If the grid shows no
   reset/drift gap at daily, suspect the engine before believing the result.
4. **We do not predict a direction for the cadence term.** §7 poses it as an open question —
   momentum persistence favours longer holds, reversal favours shorter — and we have no
   basis to call it in advance. Whatever the grid says on 2021–25 is the answer; §9 forbids
   consulting 2026 to choose.

**Selection rule, fixed now:** the winning cell is chosen on 2021–25 Total Net PNL alone.
2026 is a one-way rejection filter for every arm (§9). If the best 2021–25 cell collapses in
2026 it is dropped and the next one is taken — never the reverse.

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
  universe.py          as-of eligibility: full window, tradeable, member (A5/A10/A17)
  membership.py        A17 — press-release parsing, backward roll, membership mask
  events.py            B10/A18 — forced mid-cycle exits: one table, two sources
  features.py          signal computation
  select.py            ranking, buffer, tie-break
  backtest.py          execution, costs, NAV, trades — signal- and weighting-agnostic
  metrics.py           round-trips and reported figures
  noise.py             the 10,000-draw band
  excel.py             workbook writer            [NOT BUILT — the deliverable is a report]
scripts/               01_fetch  02_clean  03_v0  04_noise  05_v1  06_report  07_sweep
                       08_pit_universe — builds the point-in-time snapshot
tests/                 conftest  test_config  test_causality  test_accounting  test_clean  test_selection
data/raw/              immutable, as-of stamped snapshots
data/raw/press_releases/  27 NSE index-review PDFs — the membership evidence (A17)
data/clean/            validated panel
data/reports/          fetch log, data_quality.md (generated)
data/corporate_actions_overrides.csv
data/membership_overrides.csv  A17: renames, revocations, substitutions, waivers
data/phantom_days.csv  A8 rider: non-sessions the volume filter keeps. evidence-carrying
output/                nav, trades, holdings, weights, benchmarks, metrics, round_trips (CSV)
output/sweep/<cell>/   one FREQ grid cell each, so a variant never overwrites V0
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
python3 scripts/04_noise.py       # the 10,000-draw band
python3 scripts/08_pit_universe.py # point-in-time universe -> a new dated snapshot
python3 scripts/07_sweep.py       # the cadence x weighting grid, 8 cells, ~290 s
python3 -m pytest tests/ -q       # 84 pass, 1 xfail-strict

# add --window stress for the 2026 rejection filter; --calendar/--weighting for one cell
```

A stub script prints every config key still blocked and the decision blocking it.

---

## 13 · Data — what is verified

**Source:** Yahoo Finance via `yfinance`. All 200 symbols resolve with a `.NS` suffix.
Snapshot pinned at `data/raw/prices_20260824.parquet`: 332,450 rows, 2019-06-03 →
2026-08-24, zero null closes. Indices `^NSEI` and `^CNX100`.

**Panel:** `data/clean/panel_20260828.parquet`, **1,786 trading days × 283 names**, zero
interior gaps, 3 corporate-action corrections applied and 2 handled by B10's exit rule. The
calendar excludes 5 non-sessions: 4 zero-volume holiday bars, and `2025-03-18`, a stale bar
hand-excluded on evidence (A8 rider).

**Point-in-time membership (A17):** 976 NSE press-release PDFs swept, **27 carry Nifty 100
or Midcap 100 changes**, giving 43 change records and 391 membership spans over 289 symbols.
The backward roll completes in 28 states with every invariant holding. **Adding 83
historical price series did not move the trading calendar** — asserted in
`scripts/08_pit_universe.py`, because a new session would silently shift every positional
lookback, which is exactly how the `2025-03-18` defect did its damage.

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
Never below 174 **on a rebalance date** — but see `DECISIONS.md` B9: evaluated over *every*
trading day the floor is 2, on the one date poisoned by the `2025-03-18` stale bar. The
assertion in `universe.eligibility_matrix` is what surfaced it.

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

Deadline **31 August 2026**. Today **28 August 2026**.

**Done.** Skeleton, data acquisition, the full cleaning layer, V0 end-to-end, the noise
band, the cadence × weighting grid, **B10/A18 forced mid-cycle exits**, and **the
point-in-time universe rebuild (A3 amended / A17)**. 84 tests pass, 1 xfail-strict (V1
composite). Decisions A1–A18, B1–B12, C1, C2, C6, C7, D1–D11 are closed — 47 of 52, with
A3, A6, B1, B3, B9 and B10 all amended or resolved after being found wrong.

**The headline, on an honest universe.**

| | Point-in-time | Today's constituents (superseded) |
|---|---|---|
| V0 Total Net PNL | **₹3,88,03,708** (+388.0%) | ₹8,76,46,846 (+876.5%) |
| Equal-weight universe | +151.6% | +284.9% |
| Selection over its own universe | +236 pp | +592 pp |
| Sharpe / MDD | 1.43 / −31.29% | 2.21 / −32.50% |

**Best configuration found: `PIT-wk-drift` — the same rule rebalanced weekly, letting
weights drift. ₹4,85,51,143 (+485.5%), CAGR 42.43%, Sharpe 1.64, MDD −30.64%.** +₹0.97 Cr over V0,
`z_qtr` +1.91, selected on 2021–25 alone and passing the 2026 filter at +5.44%.

**Four findings from 2026-08-28 a reader should not have to dig for.**

1. **A3's premise was false, and the concession cost 488 percentage points.** The entry
   said "no free 2021 membership list exists" and was never checked. NSE publishes every
   index change; 27 press releases cover the window. More than half the old headline was
   index-inclusion bias.
2. **The bias was hiding selection skill, not only inflating it.** Raw PNL more than
   halved, but the risk-adjusted percentile *rose* from 63.5 to **73.7**. The old universe
   made the strategy look like a pure volatility loading; on point-in-time data it does not.
3. **B3 reversed.** Reset beat drift at all four cadences on the old universe; drift beats
   reset at all four on the point-in-time one. A conclusion this project published for one
   day was overturned by fixing the data under it.
4. **The ex-date rule's off-by-one silently does nothing if you get it wrong.** The
   ex-date's own *open* is already ex-entitlement. Scheduling the exit on the ex-date gave
   +1.8% where one session earlier gave +8.6%.

**Next, in order.**

1. **Push to GitHub and write the 5–6 page report.** Both are hard checklist items still at
   zero and worth more marks than any further strategy work. The universe rebuild is the
   report's strongest section: a measured bias, a self-checking reconstruction, and two
   published conclusions overturned by it.
2. Then the backlog (§8), cheapest first. Cadence is done twice over; the tree ensemble
   (#7) is almost certainly not worth the days it costs.

Still open: C3, C4, C5, C8, C9 (V1 composite). Nothing open blocks V0, the band, or the
selected configuration.
