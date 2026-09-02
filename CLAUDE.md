# Finesse x Citadel Portfolio Challenge

Round 2 submission. Everything except the decision register lives here; the decisions
themselves are in **`DECISIONS.md`**, which is the authoritative ledger.

---

## 1 · The mandate

| | |
|---|---|
| Universe | Nifty 100 + Nifty Midcap 100, **as of today** — the organisers' clarification of 2 Sep 2026 (`DECISIONS.md` A3-r). 200 names, held flat across the window. The point-in-time reconstruction (A17) remains runnable behind one config word and is now how §10 *measures* the bias this rule carries. Smallcap 100 is permitted by the rules and was **tested and rejected on PNL** — A19, §11. |
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

**Analysis notes get written down.** `NOTES.md` is the running notebook for reasoning that
is neither a decision (`DECISIONS.md`) nor a configuration (§11): mechanism arguments,
anomalies noticed in passing, hypotheses with the evidence for and against, and the
occasional finding that a published conclusion rests on less than it appears to. Anything
interesting enough to say out loud once is written there the same day, because the 5–6 page
report is assembled from it and reconstructed reasoning is worse reasoning. Each entry is
dated, states plainly which parts are measured and which are speculation, and names the
in-sample test that would settle it.

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

**Superseded a third time, by A3-r.** The mandated universe is today's constituents, so
the ladder that governs is the right-hand column. Both are kept, because the *gap* between
them is §10's bias measurement:

| | Mandated (today's constituents) | Point-in-time (A17) |
|---|---|---|
| Nifty 100 index (`^CNX100`) | +89.4% · ₹0.89 Cr | +89.4% · ₹0.89 Cr |
| Equal-weight universe, quarterly, after costs | **+284.9%** · ₹2.85 Cr | +151.6% · ₹1.52 Cr |
| V0 (12-1 momentum, top 10, quarterly) | **+876.5%** · ₹8.76 Cr | +388.0% · ₹3.88 Cr |
| **The submission (monthly, reset)** | **+1,076.5%** · **₹10.76 Cr** | — |
| Best point-in-time cell (weekly, drift) | — | +485.5% · ₹4.86 Cr |

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

> **Read this section as historical.** Every figure below was measured on the
> **point-in-time** universe (A3/A17), which A3-r retired as the scored rule on
> 2026-09-02. The mandated-universe equivalents are in §11's `MAND` block and §15. The
> section is kept rather than rewritten because it is what was concluded at the time, and
> because the point-in-time run is still reproducible with one config word — that is what
> makes §10's bias measurement a measurement.


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

Only after V0 and the noise band exist. **The feature set was frozen 30 Aug 2026 as
`DECISIONS.md` C10–C16, on the Phase 0 diagnostic** (`scripts/09_feature_diagnostics.py`,
`NOTES.md` N3). This section previously specified a 4–6 feature set that measurement
retired; the old list is kept below rather than deleted.

**Three features, one per concept.** Averaging seventeen features where six are momentum
variants silently makes the composite 60% momentum — and the first draft of this section
made a milder version of that mistake, which is what Phase 0 caught.

| Feature | Definition | Concept | Sign |
|---|---|---|---|
| 12-1 momentum | `P(t−21)/P(t−252) − 1` | how much it rose | **+** |
| Information discreteness | `sign(Mom) × (%neg − %pos)` over the 231-day window | how the rise arrived | **−** (C14) |
| Drawdown from 252d peak | `P(t−1)/max(P over 252d) − 1` | where it sits vs its own high | **+** (C15) |

**Signs are in `config.yaml`, deliberately.** A reversed sign on information discreteness
is the one V1 error that leaves no trace — the run completes, reconciles to the rupee and
reports plausible numbers while buying the opposite of what was intended. Low information
discreteness is the predictive state, so it enters negated.

**No new numeric parameter.** The drawdown window *is* `signal.lookback`; information
discreteness uses the same `lookback`/`skip` pair as the momentum signal. V1 inherits V0's
zero-fitted-parameter defence intact.

**What Phase 0 retired, and why.** Residual momentum measured `ρ = +0.883` against 12-1
momentum, selecting 7.8 of the same 10 names — this section's old plan would have been
three concepts in four weight slots. It is held back as a single-change Phase 3 arm
instead (C10). Volatility is out: beta, idiosyncratic vol and total vol are one concept in
three columns (ρ 0.49–0.75). Liquidity is out: Amihud and rupee turnover are near mirror
images at `ρ = −0.79`. Short-horizon reversal is out: it is a separate bet, not a
refinement (C8).

**The combination rule is not settled.** How the three columns become one score — z-scores
or ranks, and with what clipping and weights — is C3/C4/C9, still `OPEN`, and is Phase 2 of
`PLAN.md`. This section used to specify "z-scored, winsorised at ±3" as though it were
settled; it never was, and Phase 0 measured that the choice is consequential — a
z-composite and a rank composite share only **5.7 of 10** names despite correlating 0.971.
It is being taken on its own evidence rather than inherited from a first draft.
Whatever is chosen, features are compared **across stocks on the rebalance date** — never
across time for one stock — and combined with fixed weights, so nothing is fit, and there
is no training window, no walk-forward, and no look-ahead question to answer.

**Rank buffer:** a name enters at top 10 and is only evicted below top 20. Hysteresis, one
rule, kills most churn. An incumbent that becomes ineligible exits regardless of rank.

**Result, 30 Aug 2026: this composite was built, run, and lost.** All five pre-registered
arms came in −3.47σ to −5.22σ against `PIT-V0` (§11), and PNL is monotone in the momentum
weight — every unit of weight moved off the two new features and onto 12-1 momentum earned
money. V1 is **not adopted**. (The submission named here was `PIT-wk-drift`, which A3-r
later retired along with the point-in-time universe; the slate was **re-run on the mandated
universe on 2026-09-02 and lost by more** — −5.15σ to −7.49σ, §11's `MAND` block. The
verdict did not depend on the universe.) The section above is
kept as specified rather than rewritten, because it is what was declared before the runs.
`NOTES.md` N6 carries the mechanism and the methodological lesson: **the one-per-concept
rule defends against double-counting, and is not evidence the concepts are worth counting
once.** An orthogonal feature that carries no signal does *more* damage to a composite than
a redundant one, because it dilutes without correlating.

---

## 7 · What actually moves the number — re-measured on the point-in-time universe

> **Read this section as historical.** Every figure below was measured on the
> **point-in-time** universe (A3/A17), which A3-r retired as the scored rule on
> 2026-09-02. The mandated-universe equivalents are in §11's `MAND` block and §15. The
> section is kept rather than rewritten because it is what was concluded at the time, and
> because the point-in-time run is still reproducible with one config word — that is what
> makes §10's bias measurement a measurement.


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
| 1 | Feature weight variants on the composite | Cheap to test, directly changes selection | Each variant is a trial; log it | **Done 2026-08-30.** `WGT`: 7 vectors × 6 frames = 42 cells (C9-r). **0 of 42 beat V0 in their own frame; 0 reached +1σ.** Axis closed. §11 |
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

> **Read this section as historical.** Every figure below was measured on the
> **point-in-time** universe (A3/A17), which A3-r retired as the scored rule on
> 2026-09-02. The mandated-universe equivalents are in §11's `MAND` block and §15. The
> section is kept rather than rewritten because it is what was concluded at the time, and
> because the point-in-time run is still reproducible with one config word — that is what
> makes §10's bias measurement a measurement.


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

**Survivorship / index inclusion — present by mandate, measured rather than mentioned.**
`DECISIONS.md` A3-r: the organisers confirmed on 2 Sep 2026 that the scored universe is the
index constituents **as of today**, applied backwards across 2021–25. A stock is therefore
eligible in January 2021 partly because it had risen enough to be in the index by 2026.

This is the largest single caveat on the headline number, and it is quantified rather than
acknowledged. The point-in-time reconstruction (A17) is still in this repo, still runs, and
is one config word away — `universe.membership_mode: point_in_time`, rebuilt from 27 NSE
press releases and verified by rolling today's list backwards under three invariants:

| Same rule, same dates, same engine | Total Net PNL | Total return | Equal-weight benchmark |
|---|---|---|---|
| **Today's constituents (mandated)** | **₹8,76,46,846** | **+876.5%** | +284.9% |
| Point-in-time membership | ₹3,88,03,708 | +388.0% | +151.6% |

**Index-inclusion bias is worth 488 percentage points — more than half the headline.** The
strategy's edge *over its own universe* falls from +592 pp to +236 pp, which is the honest
way to read what the rule contributes. Both numbers go in the report. The edge survives the
correction and the noise band still says it is not luck (99.96th percentile point-in-time),
so disclosing this costs the argument nothing and omitting it would cost the argument
everything.

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
| 2026-08-30 | `V1-base` | **The composite.** 12-1 momentum + information discreteness (negated) + drawdown from the 252-day peak, as scaled ranks (C17), equal weights, strict top 10, quarterly/reset. | 1,31,92,525 | −2,56,11,184 | −5.03 | −5.03 | **fails** | **run 2026-08-30 (N8): −1.11%, 43.6th pct, −0.21σ — a random book. V0 is +10.77% at the 93.5th.** Diagnostic only; §9 forbids it moving anything | **Loses decisively, and on every axis.** Sharpe 1.43 → 0.84, MDD −31.3% → −40.5%, annualised vol 26.1% → 21.8%. Implementation verified against Phase 0's independent path: book overlap with V0 3.35/10 against a predicted 3.4/10. |
| 2026-08-30 | `V1-buffer` | `V1-base` plus the §6 rank buffer, 10/20 hysteresis. A second change, so its own line. | 1,22,09,183 | −2,65,94,526 | −5.22 | −5.22 | **fails** | not run | **Worst arm in the slate.** Churn 7.21 → 5.58 and costs fall ₹5.51 L → ₹4.28 L, so the buffer does what it is for; it just does not pay. Moves PNL −0.19σ from `V1-base` — inside the band, as predicted. |
| 2026-08-30 | `RM-solo` | V0's rule with standardised residual momentum (C12/C13) swapped in for 12-1. One feature changed, nothing else. The C10 promise. | 1,78,33,244 | −2,09,70,465 | −4.12 | −4.12 | **fails** | not run | **Answers C10's held-back question: plain momentum wins.** Annualised vol 20.34% against V0's 26.12% — prediction 3 confirmed — but it gives up ₹2.10 Cr to buy that, and loses on Sharpe too (1.12 vs 1.43). |
| 2026-08-30 | `V1-tilt` | `V1-base` with the 2/1/1 weight vector (C9), pre-registered before any arm ran and run unconditionally. | 2,11,58,779 | −1,76,44,929 | −3.47 | −3.47 | **fails** | not run | **Best V1 arm, still ₹1.76 Cr behind V0.** Lands between `V1-base` and V0 exactly as prediction 4 said. The ordering is monotone in momentum weight — 1/3 → 1/2 → 1 gives ₹1.32 Cr → ₹2.12 Cr → ₹3.88 Cr. |
| 2026-08-30 | `V1-wk-drift` | `V1-base` (which beat `V1-buffer`) re-run at weekly + drift, the selected configuration's own frame. Scored against that cell's own σ of ₹31,39,462. | 2,35,50,835 | −2,50,00,308 | −7.96 | −4.91 | **fails** | not run | **The cadence gain does not rescue the signal.** Weekly+drift lifts the composite ₹1.32 Cr → ₹2.36 Cr, the same direction it lifted V0, but `PIT-wk-drift` is at ₹4.86 Cr. Costs reach ₹37.28 L at 29.85× turnover. |
| 2026-08-30 | `WGT` (42 cells) | **The weight surface.** 7 weight vectors × 3 cadences × 2 weighting rules, pre-registered as one set (C9-r). Per-cell ledger in `output/v1/wgt_summary.csv` — one row per configuration, nothing omitted. | best 4,00,18,129 | −85,33,014 vs submission | — | — | **0 of 42 clear** | not run (§9 — none is a candidate) | **The weighting axis is closed.** Every cell loses to V0 in its own frame. **0 of 42 reached +1σ**, against a null expectation of ~7, so the multiple-comparisons discount was never needed. §8 backlog item 1 done. |
| 2026-08-30 | `WGT-w6-wk-reset` | Best of the 42: 6/1/1 weights, weekly, reset. | 4,00,18,129 | +11,52,000 vs `PIT-wk-reset` | −1.79 | — | **fails** | not run | **The high-water mark of the whole composite programme, and still ₹85 L short of `PIT-wk-drift`.** Loses to V0 on its own frame by −1.79σ. |
| 2026-08-30 | `WGT-no-dd` (6 frames) | Isolation: 1/1/0 — drops drawdown, keeps information discreteness. `w_mom` held at 0.500. | 1,83,13,039 – 2,44,95,800 | — | −3.92 to −7.66 | — | **fails** | not run | **Loses to `no-id` in 6 of 6 frames** despite retaining *more* of the top-10-momentum tail (47.5% vs 31.0%). Prediction 4 failed unanimously; N7's retention model does not explain this pair. |
| 2026-08-30 | `WGT-no-id` (6 frames) | Isolation: 1/0/1 — drops information discreteness, keeps drawdown. `w_mom` held at 0.500. | 1,99,17,575 – 2,76,38,884 | — | −3.30 to −7.16 | — | **fails** | not run | **Information discreteness is the more damaging of the two added features** — the opposite of what N9's forward Spearman (+0.001 vs −0.012) predicted. Retires that reading. |

### `MAND` block — 2026-09-02, the mandated universe (A3-r)

**A different universe, so a different block.** Every row above was computed on either the
old today's-constituents panel (pre-B10) or the point-in-time one. These rows are computed
on **today's constituents with B10's forced exits active**, which is what the organisers
mandate and what the submission is scored on. `z_qtr` here divides by **₹86,16,185**, the σ
of `MAND-NOISE`. The three blocks are not comparable to each other and are not meant to be.

| Date | ID | What changed | PNL (₹) | Δ vs V0 (₹) | z_own | z_qtr | Cleared? | 2026 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-02 | `MAND-V0` | **Re-baseline, not a trial.** A3-r: today's 200 constituents, held flat. Identical model, identical calendar, B10 active. | 8,76,46,846 | — | — | — | **100th pct** | **pass** (+7.69%, 85.7th pct) | **The mandated baseline; every row below is measured against it. Reproduces `V0-r1` to the rupee** across five days of universe work — the regression gate that licensed everything after it. CAGR 57.79%, Sharpe 2.21, MDD −32.50%, costs ₹8,84,694, 92 round trips. Risk-adjusted 62.97th pct. |
| 2026-09-02 | `MAND-NOISE` | The band on the mandated universe, seed 20260824, B10 applied to every draw. | mean 2,75,59,022 | σ = 86,16,185 (± 60,929) | — | — | — | n/a | **The measuring stick for this block.** 0 of 10,000 draws beat `MAND-V0`, +6.97σ. σ moves only ₹10,766 from the pre-B10 `NOISE-r1` — the exit rule touches one in-window name, so the ruler is effectively unchanged and the old block stays legible. |
| 2026-09-02 | `MAND-qt-drift` | Quarterly, drift. | 8,63,77,499 | −12,69,346 | −0.15 | −0.15 | 100th pct | **pass** (+7.85%) | Loses. B3 flips back to reset — see `DECISIONS.md` B3, which now records **two** reversals, both caused by the universe rather than the weighting rule. |
| 2026-09-02 | **`MAND-mo-reset`** | **Monthly cadence (60 rebalances), reset weighting.** One config word against V0. | **10,76,49,806** | **+2,00,02,960** | **+2.68** | **+2.32** | **100th pct** | **pass** (+7.60%, 88.9th pct) | **THE SUBMISSION.** +₹2.00 Cr over V0 on the metric that scores. Sharpe 2.21 → **2.42**, MDD flat at −32.4%, so it is not bought with risk — and the **risk-adjusted percentile rises 62.97 → 96.01**, which is the strongest single number in the project. Costs ₹8.85 L → ₹20.60 L, immaterial against the gain. |
| 2026-09-02 | `MAND-mo-drift` | Monthly, drift. | 9,48,87,434 | +72,40,588 | +0.97 | +0.84 | 100th pct | **pass** (+7.73%) | Beats V0, loses ₹1.28 Cr to reset. |
| 2026-09-02 | `MAND-wk-reset` | Weekly, reset. | 9,98,94,149 | +1,22,47,304 | +2.41 | +1.42 | 100th pct | **pass** (+8.58%, 98.2nd pct) | Past the peak. ₹77.6 L short of monthly at 2.2× the turnover. The cadence term is an **inverted U**. |
| 2026-09-02 | `MAND-wk-drift` | Weekly, drift. | 8,48,68,962 | −27,77,884 | −0.55 | −0.32 | 100th pct | **pass** (+9.02%) | **Loses to V0.** Note this cell was the *submission* on the point-in-time universe. |
| 2026-09-02 | `MAND-dy-reset` | Daily (1,235 rebalances), reset. | 9,29,46,976 | +53,00,131 | +6.45 | +0.62 | 100th pct | **pass** (+2.06%) | **The row D11-r exists for.** `z_own` +6.45 vs `z_qtr` +0.62 — a 10× gap made entirely by the denominator. Read `z_qtr`. Costs ₹88.71 L retires §3's unconditional "costs are irrelevant". |
| 2026-09-02 | `MAND-dy-drift` | Daily, drift. | 8,68,09,592 | −8,37,253 | −1.02 | −0.10 | 100th pct | **pass** (+2.18%) | Loses to V0. |
| 2026-09-02 | `SIG` (6 cells) | **The signal grid.** `lookback ∈ {126,189,252}` × `skip ∈ {0,21}`, pre-registered, in the submitted frame. No band re-drawn — a random draw ignores the signal. Per-cell ledger: `output/sweep/sig_summary.csv`. | 7,36,00,599 – 10,76,49,806 | — | −4.56 to 0.00 | — | **0 of 6 clear** | not run (§9 — none is a candidate) | **The incumbent 252/21 is the argmax of its own surface.** 0 of 6 cells beat it at all, let alone by the pre-registered 1σ, against a null expectation of ~1. C2-r. |
| 2026-09-02 | `SMALL-qt` | **The Smallcap 100 arm.** Today's Nifty Smallcap 100 added — 299 names. Own band from its own eligible set (σ ₹1,02,72,310). | 8,04,04,132 | **−72,42,714** | −0.70 | −0.84 | 99.91st pct | **pass** (+6.55%) | **Loses.** Its equal-weight benchmark *rises* to +307.1%, so the universe got better and the **selection got worse**. |
| 2026-09-02 | `SMALL-mo` | Same, at the submitted cadence. Band σ ₹87,47,150. | 6,37,38,800 | **−4,39,11,006** | −5.02 | −5.10 | 99.90th pct | **pass** (+9.16%) | **Loses by −5.1σ.** A19 closes §8 backlog item 3 with a measured negative: the "largest single PNL lever" points **down**. |
| 2026-09-02 | `V1` (4 arms) | The composite slate re-run on the mandated universe: `base`, `buffer`, `tilt`, `rm-solo`, quarterly/reset. | 2,31,22,522 – 4,33,02,965 | −6,45,24,324 to −4,33,43,881 | −7.49 to −5.15 | same | **fails** | not run | **The verdict replicates, and harder.** Same ordering as point-in-time — `base` < `buffer` < `tilt` < `rm-solo` < V0 — and every arm now loses by more than 5σ. |
| 2026-09-02 | `WGT` (42 cells) | The weight surface re-run on the mandated universe. 7 vectors × 3 cadences × 2 rules. Per-cell ledger: `output/v1/wgt_summary.csv`. | 2,19,54,568 – 8,39,78,365 | best −2,36,71,441 vs submission | −3.17 (best) | — | **0 of 42 clear** | not run | **0 of 42 beat V0 in their own frame; 0 reached +1σ** against a null expectation of ~7. Best cell (`w8`, monthly/reset, ₹8.40 Cr) is ₹2.37 Cr short of the submission. |
| 2026-09-02 | `WGT-no-id` vs `WGT-no-dd` | The isolation pair, 6 frames, both at `w_mom` = 0.500. | no-id 4,36,40,606 – 5,84,49,070 · no-dd 2,93,75,316 – 4,02,37,430 | — | −4.49 to −13.88 | — | **fails** | not run | **`no-id` beats `no-dd` in 6 of 6 frames — the point-in-time finding replicates on a different universe.** Information discreteness is the more damaging of the two added features, and that now rests on 12 frames across two universes rather than 6 across one. |


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

### `WGT` result — run 2026-08-30, 42 cells, 78 s

7 weight vectors x 3 cadences x 2 weighting rules, all against bands drawn 2026-08-28.
**Full per-cell ledger: `output/v1/wgt_summary.csv`, one row per configuration** — §11's
"one line per configuration" is honoured there rather than by 42 markdown rows, deliberately,
because a table nobody can read is not a ledger. PNL in ₹ crore.

| frame | `base` 0.333 | `tilt` 0.500 | `w3` 0.600 | `w6` 0.750 | `w8` 0.800 | **V0** 1.000 |
|---|---|---|---|---|---|---|
| quarterly reset | 1.32 | 2.12 | 2.23 | 2.22 | 2.52 | **3.88** |
| quarterly drift | 1.31 | 1.94 | 2.03 | 2.19 | 3.14 | **3.93** |
| monthly reset | 1.85 | 2.46 | 3.30 | 2.73 | 3.00 | **4.14** |
| monthly drift | 1.90 | 2.57 | 3.46 | 2.80 | 3.68 | **4.29** |
| weekly reset | 2.17 | 2.83 | 3.44 | **4.00** | 3.89 | **4.57** |
| weekly drift | 2.36 | 2.84 | 3.45 | 3.98 | 3.85 | **4.86** |

The two isolation arms, both at `w_mom` = 0.500:

| frame | `tilt` (split) | `no-dd` (all on ID) | `no-id` (all on drawdown) |
|---|---|---|---|
| quarterly reset | **2.12** | 1.83 | 2.04 |
| quarterly drift | 1.94 | 1.93 | **1.99** |
| monthly reset | 2.46 | 2.21 | **2.47** |
| monthly drift | 2.57 | 2.14 | **2.76** |
| weekly reset | **2.83** | 2.42 | 2.70 |
| weekly drift | **2.84** | 2.45 | 2.61 |

#### Scoring the six pre-registered predictions

**2 · No arm beats the submission. CONFIRMED, and by a wider margin than expected.** The
best of 42 is `w6` at weekly/reset, **₹4,00,18,129 — ₹85,33,014 short** of `PIT-wk-drift`.
**Not one of the 42 reached even +1σ against its own frame's V0.** `PIT-wk-drift` remains the
submission; the selection rule was never in doubt and is not being rewritten.

**6 · Multiple comparisons. Not exercised, and the reason is the strongest single line in
the phase.** 42 arms at P(z > 1) ≈ 16% predicts about **7** cells above +1σ on luck alone.
**Observed: 0.** The discount rule never had to be invoked because nothing came close.

**1 · Monotone in momentum weight in every frame. FAILED — it holds in 1 of 6.** But the
failure is confined to one region and that is the finding. Measured in each frame's own σ:

| frame | base→tilt | tilt→w3 | w3→w6 | w6→w8 |
|---|---|---|---|---|
| quarterly reset | +1.56σ | +0.22σ | −0.02σ | +0.59σ |
| quarterly drift | +1.24σ | +0.18σ | +0.31σ | +1.87σ |
| monthly reset | +1.33σ | +1.82σ | **−1.23σ** | +0.58σ |
| monthly drift | +1.46σ | +1.92σ | **−1.42σ** | +1.92σ |
| weekly reset | +2.10σ | +1.96σ | +1.77σ | −0.36σ |
| weekly drift | +1.53σ | +1.95σ | +1.69σ | −0.41σ |

**`base` → `tilt` → `w3` rises in 6 of 6 frames, every step positive.** Every inversion sits
in the `w3` → `w6` → `w8` plateau, where the weight increments are small and the PNL steps
are mostly inside ±1.5σ. That is precisely the shape `NOTES.md` N9's noise-column null
predicted — **a cliff between w = 1.0 and w ≈ 0.8, then a plateau** — so the strict
prediction failed while the model behind it was confirmed. Recorded as a failed prediction
rather than reworded: the claim was monotone in 6/6 and it is not.

**4 · `no-dd` beats `no-id`. FAILED, unanimously and in the opposite direction.** `no-id` —
the arm that **drops information discreteness** — wins in **6 of 6** frames. Six-for-six is
not luck. The prediction rested on N9's forward Spearman (ID +0.001, drawdown −0.012), and
that reading is now retired: **information discreteness is the more damaging of the two
features**, not drawdown.

**And the mechanism N7 built does not explain it, which is the honest headline.** N7's model
was that PNL tracks how much of the top-10-momentum tail a book retains. Across the ladder
that model is near-perfect — retention runs **33.5% → 40.5% → 46.0% → 62.5% → 67.0%** for
base/tilt/w3/w6/w8, monotone with PNL. On the isolation pair it **inverts**: `no-dd` retains
**47.5%** of top-10-momentum name-dates and `no-id` only **31.0%**, and `no-id` still wins
everywhere. So keeping information discreteness displaces *less* of the momentum tail and
costs *more*, which means it is damaging the book *within* the tail rather than by moving it.
N7's retention model is therefore sufficient for the weight ladder and **insufficient in
general**, and §7/N7 should be read with that limit attached.

**3 · `tilt` beats both isolation arms. HALF RIGHT — 3 of 6.** `tilt` wins at quarterly/reset
and both weekly frames; `no-id` wins at quarterly/drift and both monthly frames. The
noise-averaging argument (splitting the spare half across two independent columns gives
sd ∝ 0.354 against 0.500 for concentrating it) predicts `tilt` should always win. It does not,
and the reason is prediction 4's: the two columns are not interchangeable noise.

**5 · No direction predicted for how cadence changes the curve's steepness. The answer is
clear.** Dilution costs proportionally **less** at faster cadence — `base` retains 34.0% /
33.3% of V0's PNL at quarterly, 44.5% / 44.3% at monthly, and 47.5% / 48.5% at weekly. A
plausible reading is that faster rebalancing draws the dilution noise more often and averages
it away; that is post-hoc and labelled as such. No number here was predicted in advance, so
it is reported as a measurement, not a confirmation.

#### What `WGT` settles

**The weighting axis is closed and the composite is not rescued by it.** Every point on the
curve loses to V0 in its own frame, in all six frames, and the best of 42 is ₹85 L short of
the submission. §8 backlog item 1 is done.

**The axis was worth running for a reason unrelated to its outcome.** V1 was previously judged
on two weight vectors; it is now judged on seven across six frames, and the negative result is
correspondingly harder to dismiss as an artefact of one arbitrary choice. It also produced the
`no-id` reversal, which no amount of reasoning about the earlier result would have found.

### `V1` result — run 2026-08-30, 5 pre-registered arms

**Every arm loses, and not narrowly.** Against `PIT-V0`'s ₹3,88,03,708:

| Arm | PNL | Δ vs V0 | z | Sharpe | MDD | ann. vol | churn/reb |
|---|---|---|---|---|---|---|---|
| **`PIT-V0`** | **3,88,03,708** | — | — | **1.43** | **−31.29%** | **26.12%** | **5.05** |
| `V1-tilt` | 2,11,58,779 | −1,76,44,929 | −3.47 | 1.14 | −37.83% | 22.43% | 6.58 |
| `RM-solo` | 1,78,33,244 | −2,09,70,465 | −4.12 | 1.12 | −34.79% | 20.34% | 6.00 |
| `V1-base` | 1,31,92,525 | −2,56,11,184 | −5.03 | 0.84 | −40.52% | 21.84% | 7.21 |
| `V1-buffer` | 1,22,09,183 | −2,65,94,526 | −5.22 | 0.77 | −38.76% | 22.40% | 5.58 |

**This is a clean negative result and it is reported as the headline of the phase.** V1 is
not adopted. Under §11's selection rule the submission remains `PIT-wk-drift`, exactly as
the pre-registration said it would if every arm lost — V1 was declared a candidate, not a
commitment, before any number existed.

**The mechanism, and it is the one §3 predicted.** Every V1 arm has *lower* volatility than
V0 — 20.3% to 22.4% against 26.1% — and every one earns less. Drawdown-from-the-high tilts
away from high-volatility names by construction (Phase 0: ρ(F8, idio vol) = −0.28 Spearman,
−0.41 Pearson), which is precisely what C15 cited *in its favour*. Under a raw-PNL metric
that de-risking is a handicap, which §3 has said from the beginning: *risk-reduction
machinery is a handicap under this metric.*

**But de-risking is not the whole story, and saying so would be too kind to V1.** If the
composite merely traded return for risk it would hold its own per unit of risk. It does not:
Sharpe falls 1.43 → 0.84 and max drawdown gets *worse*, −31.3% → −40.5%. The composite is
worse on the risk-adjusted metric **and** the risk metric, not just the scoring one. The
honest reading is that the two added features are not merely metric-inappropriate here —
over this window they carry no demonstrated forecasting content at all, and Phase 0 said in
advance that it could only establish they were *distinct*, never that they *worked*.

**The loss is mostly dilution arithmetic, not bad features — measured 2026-08-30.** Replace
the two new columns with **random** ones of the same rank distribution and the gross
compounded return still falls +393.2% → +207.9% (2,000 draws, seed 20260830). `V1-base`'s
+138.6% sits at the **16.5th percentile of that noise-column null** — mildly worse than
random, inside the band. So roughly 185pp of the ~255pp gross gap is what *any* two
uninformative columns would have cost. The dilution curve is a cliff then a plateau: giving
away 20% of the ranking vote costs 116pp, giving away the next 47% costs only 69pp more.
A top-10-of-190 rule is a knife edge. **The error was C9's default, not the feature
research** — equal weighting is not the neutral choice on a knife-edge rule, it is close to
the most aggressive claim available. `NOTES.md` N9 carries the eight-check bug hunt behind
this, including two implementation findings: scaled-rank composites produce *exact ties*
(158–179 distinct scores over 183–195 names; the tie-break decided 1 name), and
drawdown-from-peak cannot discriminate in the top decile (15.1% of name-dates sit within 2%
of their own high).

**Was it a bug?** Checked before writing any of the above. `V1-base`'s book overlaps V0's by
**3.35/10**, against the **3.4/10** that `scripts/09_feature_diagnostics.py` computed
independently on 2026-08-29 through a completely separate code path. The composite is
implemented as C17 specifies, and `tests/` asserts the defining property — invariance to a
monotone transform of any one feature — that a z-composite could not satisfy.

#### Scoring the six pre-registered predictions

**1 · Turnover. Half right, and the failed half is instructive.** Churn was predicted at
**7.21** names per quarter and came in at **exactly 7.21** — Phase 0's cross-sectional
estimate transferred to the live backtest without adjustment. But the cost forecast of
**₹8.5–9 L was wrong: costs came in at ₹5.51 L, *below* V0's ₹6.11 L.** The prediction
implicitly assumed V1's NAV would grow like V0's; turnover is a ratio while costs are rupees
on traded notional, and V1's book compounded to about a third of V0's, so a higher turnover
ratio on a much smaller portfolio costs fewer rupees. Recorded as a failed sub-prediction
rather than reworded. **The substantive claim it was making is confirmed emphatically:** V1
paid *less* in costs than V0 and still lost ₹2.56 Cr, so this is not a cost story.

**2 · The buffer at quarterly. Half right.** The PNL half is confirmed — `V1-buffer` moves
**−0.19σ** from `V1-base`, comfortably inside the band, so at quarterly the buffer does not
matter. The churn half **narrowly failed**: predicted a cut of ≥2 names per quarter, measured
**1.63** (7.21 → 5.58). N1's mechanism 1 survives this test in the weak sense that quarterly
has little boundary churn to kill — but note the arm was never a fair test of the mechanism,
which N1 predicts should bite at *weekly*, and no buffered weekly arm was pre-registered.

**3 · `RM-solo` volatility. Confirmed.** 20.34% annualised against V0's 26.12%, the largest
volatility reduction in the slate, exactly as the mechanism said: residualising strips the
beta loading §5 identified. PNL direction was explicitly not predicted; it fell ₹2.10 Cr.
Falling PNL alongside falling volatility is §3 behaving as designed, **but** Sharpe fell too
(1.12 vs 1.43), so this is not purely a metric artefact.

**4 · `V1-tilt` lands between `V1-base` and V0. Confirmed.** ₹2.12 Cr sits between ₹1.32 Cr
and ₹3.88 Cr. Stronger than predicted: PNL is **monotone in the momentum weight** across all
three points — 1/3 → 1/2 → 1 gives ₹1.32 Cr → ₹2.12 Cr → ₹3.88 Cr. Every unit of weight
moved from the two new features to momentum earns money, which is the cleanest possible
statement that the two new features are the problem.

**5 · No direction predicted for `V1-base`. Honoured** — and worth noting that had a
direction been guessed it would almost certainly have been the wrong one, since the
composite was assembled from features chosen on the strength of their distinctness.

**6 · Multiple comparisons. Not exercised.** No arm came close to +1σ, so the commitment to
discount a lone +1.0σ to +1.5σ result never had to be honoured. It stands for future slates.


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
| `V1` | **The composite slate — 5 arms, declared 30 Aug 2026 before any arm was run.** The §6 feature set through the identical engine, plus the rank buffer, the residual-momentum swap and a second weight vector. | `DECISIONS.md` C10–C17; `PLAN.md` Phases 2–4. | 4 |
| `SIG` | **The signal grid — 6 cells, declared 2 Sep 2026 before any cell was run.** `signal.lookback ∈ {126, 189, 252}` × `signal.skip ∈ {0, 21}`, in the selected frame. | C2 froze 252/21 on external evidence and it was **never swept**. "Did you check the lookback?" is the first question a panel asks about a momentum rule. | 8 |
| `SMALL` | **The Smallcap 100 arm — declared 2 Sep 2026 before it was run.** Today's Nifty Smallcap 100 added to the universe; nothing else changes. | Guidelines §2 permits all three indices; CLAUDE.md §6 excluded the third **by choice**, never by measurement. §8 backlog item 3. | 8 |

This requires `backtest.py` to be **weighting-agnostic as well as signal-agnostic** — if a
variant doesn't run through the identical engine, its PNL isn't comparable to V0's and the
noise band cannot adjudicate it.

#### `SIG` — the signal grid, declared 2 Sep 2026 before any cell was run

**Why now.** C2 froze `lookback = 252`, `skip = 21` at the start of the project, citing the
published 12-1 convention, and no cell of that surface has ever been run. Every other axis
in this project has been swept; this one was asserted. It is also the axis with the most
obvious overfitting hazard, which is why the adoption rule below is fixed *before* the
numbers exist.

**The grid.** `lookback ∈ {126, 189, 252}` × `skip ∈ {0, 21}` = 6 cells, run in the selected
frame (**monthly + reset**, from the `MAND` grid). `252 × 21` is the incumbent and is one of
the six, so the baseline sits inside its own surface rather than beside it.

**No new bands.** A random draw ignores the signal entirely, so every cell in this frame is
adjudicated against the *same* band the frame already has — σ = **₹74,70,579** — drawn on
2026-09-02 before the grid was conceived. Nothing is re-drawn and nothing can drift.

**Adoption rule, fixed now and binding.** A cell replaces 12-1 **only if it beats the
incumbent by more than 1σ in that frame** — more than ₹74.71 L. Anything inside the band is
a resampling of luck (§5), the incumbent stays, and the surface is reported as a
measurement. This is deliberately stricter than §11's plain-max-PNL rule, because unlike
cadence or weighting this axis has no mechanism behind a preference for one value over
another: picking the argmax of six correlated cells is fitting, and 6 cells at P(z > 1) ≈ 16%
puts the null expectation at about **1** cell above +1σ on luck alone.

**Three predictions, recorded before the runs.**

1. **All six cells beat the equal-weight benchmark and sit above the 95th percentile of the
   band.** Momentum over *any* of these windows is a real effect over 2021–25; if a cell
   lands mid-band, suspect the plumbing before believing the result.
2. **`skip = 0` costs little, and may gain.** The one-month skip exists to dodge short-horizon
   reversal, which is a monthly-frequency effect measured in US data. At the 12-month
   lookback the skipped month is 8% of the window. Predicted: |Δ| < 1σ between `252×21` and
   `252×0`. **If dropping the skip gains more than 1σ, the reversal premise does not hold in
   this universe** and that is the finding, not the PNL.
3. **Shorter lookbacks lose.** 126 days is half a cycle and turns the rule into
   intermediate-horizon momentum with higher churn. Predicted: `126 < 189 < 252` at both skip
   values. No claim about the size of the gap.

**Whatever the outcome, the zero-fitted-parameter defence changes shape and the report says
so.** It becomes "one parameter was swept, pre-registered, against a band fixed in advance,
and the incumbent was kept unless beaten by more than a standard deviation" — which is a
stronger claim than "never checked", and an honest one either way.

#### `SMALL` — the Smallcap 100 arm, declared 2 Sep 2026 before it was run

**Why it exists.** The guidelines permit Nifty 100, Nifty Midcap 100 **and** Nifty Smallcap
100. This project used two of the three and §6 recorded that as a choice. It was never
measured, and §8 backlog item 3 ("universe tilt toward midcap — largest single PNL lever")
has been open since the backlog was written.

**What changes: exactly one thing.** The universe gains today's 100 Smallcap constituents —
74 new names plus 26 that were already priced as historical members of the larger indices.
Same engine, same calendar (1,786 days, asserted unchanged), same costs, same signal, same
selection rule. `data/raw/prices_small_20260902.parquet`, built by
`scripts/11_smallcap_universe.py`.

**Its own band.** A 300-name universe is a different sampling frame, so the arm gets its own
10,000 draws from *its* eligible set on the same seed. Comparing a 300-name book against a
200-name band would credit the universe change to the selection rule.

**Two predictions, recorded before the run.**

1. **PNL rises materially — more than 1σ.** Smallcaps have the highest dispersion in the
   permitted universe and 2021–25 was an exceptional period for them.
2. **The risk-adjusted standing does not improve, and may fall.** If the gain is a
   volatility loading rather than better selection, the band's own mean rises with it and the
   percentile stays put. **The percentile, not the PNL, is what says whether the rule got
   better** — and under §1's raw-PNL metric we would still submit the higher number while
   reporting both.

**What this costs in disclosure, stated in advance.** Today's Smallcap 100 is the most
survivorship-loaded list of the three: a stock is on it because it was small *and still
listed and still index-worthy* in 2026. §10 already measures index-inclusion bias at 488 pp
on the two-index universe; this arm can only increase it. It is adopted on PNL if it wins,
and the report states plainly what the number is made of.

#### `V1` — the slate, and what we expect to find

Five arms, declared here **before the first was run**. Every cell's noise band already
exists, so the slate costs no band runs and every arm is scored against a σ that was fixed
before the arm was conceived.

| # | ID | What it is | Frame | σ |
|---|---|---|---|---|
| 1 | `V1-base` | The §6 composite — 12-1 momentum, information discreteness (negated), drawdown from the 252-day peak — as scaled ranks, equal weights, strict top 10 | quarterly + reset | ₹50,92,127 |
| 2 | `V1-buffer` | Arm 1 plus the 10/20 rank buffer. A **second** change, so it gets its own line rather than being folded into arm 1 | quarterly + reset | ₹50,92,127 |
| 3 | `RM-solo` | V0's rule with standardised residual momentum swapped in for 12-1. One feature changed, nothing else — the cleanest possible attribution, and the C10 promise honoured | quarterly + reset | ₹50,92,127 |
| 4 | `V1-tilt` | Arm 1 with the 2/1/1 weight vector. Declared now and run **unconditionally**, so it is a pre-registered configuration and not a reaction to arm 1's number | quarterly + reset | ₹50,92,127 |
| 5 | `V1-wk-drift` | Whichever of arms 1–2 wins, re-run at weekly + drift as a confirmation cell on the selected configuration's own frame | weekly + drift | ₹31,39,462 |

**Base frame is quarterly + reset, not the submitted `PIT-wk-drift`.** Quarterly's band is
the one with most confidence behind it and is the reference for §7's whole attribution
ladder. Building V1 on weekly+drift would stack a new signal on a weighting rule whose own
evidence never cleared the band (`NOTES.md` N2: the drift-minus-reset gaps are +0.10 to
+0.57σ against a 1.0σ bar), and a V1 gain and a cadence gain would be confounded. Arm 5 is
how the selected frame still gets checked.

##### Six predictions, recorded before the runs so they cannot be retrofitted

1. **Turnover rises ~43% and it will not explain anything.** Measured in the cross-section,
   `V1-base` replaces **7.21** names per quarter against V0's **5.05**, so costs should go
   from ₹6.11 L to roughly ₹8.5–9 L. That is immaterial against ₹3.88 Cr, so **if V1 loses,
   it is not a cost story** — committed to in advance rather than reached for afterwards.
2. **The buffer has little room at quarterly.** `V1-buffer` cuts churn by ≥2 names per
   quarter and moves PNL by **less** than 1σ from `V1-base`. Quarterly meets the rank
   boundary only four times a year. If the buffer moves PNL by *more* than 1σ here, N1's
   boundary-churn mechanism is stronger than N1 supposed and that is the finding.
3. **`RM-solo` comes in below V0's 33.06% annualised volatility**, because residualising
   strips the beta loading §5 identified as V0's dominant exposure. Direction predicted on
   mechanism. **No direction predicted for its PNL** — but if PNL falls while volatility
   falls further, that is §3's "raw PNL rewards volatility" behaving exactly as designed.
4. **`V1-tilt` lands between `V1-base` and V0.** Measured basis: tilt shares **4.0/10**
   names with V0 against base's **3.4/10**, and ρ against 12-1 momentum rises 0.789 → 0.903.
   If tilt does not land between them on PNL, the link between book overlap and PNL is
   weaker than this project has been assuming.
5. **No direction is predicted for `V1-base`'s PNL.** Phase 0 established the three features
   are *distinct*; it established nothing about forecasting power, and two of the three rest
   entirely on external evidence. A direction here would be a guess dressed as a hypothesis.
6. **Multiple comparisons, committed in advance.** Under a roughly normal band, P(z > 1) per
   arm is ~16%, so across five arms *some* positive result is likely on luck alone. **A
   single arm landing between +1.0σ and +1.5σ will be reported as "did not clearly beat the
   band", not as a finding.** Two or more arms clearing +1σ in the same direction is a
   different matter and will be read as such.

**Selection rule, fixed now:** the winning configuration is chosen on 2021–25 Total Net PNL
alone, across *all* candidates including the V0 family. **V1 is a candidate, not a
commitment** — if every arm loses to `PIT-wk-drift`, `PIT-wk-drift` is submitted and V1 is
reported as a measured negative result. 2026 remains a one-way rejection filter (§9).

#### `WGT` — the weight surface, declared 30 Aug 2026 before any cell was run

**Why this exists.** §8's backlog item 1 is "feature weight variants on the composite",
logged before any V1 result existed, and C9 was the open weight decision. V1 was judged on
**two** weight vectors; judging a whole axis on two points is exactly the single-vector bias
the backlog item was written to remove. C9 is amended (`DECISIONS.md` C9-r) from "only these
two vectors are ever tried" to the pre-registered set below.

**What we already know, stated first so the result cannot be dressed up.** `NOTES.md` N9
measured the dilution curve with random columns: the top-10-of-190 rule is a knife edge, and
PNL is monotone in momentum weight across the three real points already on the ledger
(₹1.32 Cr → ₹2.12 Cr → ₹3.88 Cr at w = 1/3, 1/2, 1). **This sweep is therefore expected to
confirm a shape, not to discover a winner.** Its value is that it converts an assumption into
a measurement across six independent frames and closes the axis.

**Seven weight vectors × six frames.** Momentum / information discreteness / drawdown, as
integers normalised at use (C9's rule, retained). V0 is the w = 1 endpoint of the same curve
and already exists in all six frames from the `PIT` grid.

| Vector | Weights | `w_mom` | Role |
|---|---|---|---|
| `base` | 1 / 1 / 1 | 0.333 | exists at quarterly+reset and weekly+drift |
| `tilt` | 2 / 1 / 1 | 0.500 | exists at quarterly+reset |
| `no-dd` | 1 / 1 / 0 | 0.500 | **isolation** — drops drawdown, keeps ID |
| `no-id` | 1 / 0 / 1 | 0.500 | **isolation** — drops ID, keeps drawdown |
| `w3` | 3 / 1 / 1 | 0.600 | ladder |
| `w6` | 6 / 1 / 1 | 0.750 | ladder |
| `w8` | 8 / 1 / 1 | 0.800 | ladder ceiling — the steep part of N9's null curve |
| *(V0)* | 1 / 0 / 0 | 1.000 | endpoint, already run |

Frames: {quarterly, monthly, weekly} × {reset, drift}. Daily excluded. **All six bands
already exist** as point-in-time draws from 2026-08-28 (σ ₹50,92,127 / ₹50,93,505 quarterly,
₹46,16,674 / ₹46,10,591 monthly, ₹31,42,153 / ₹31,39,462 weekly), so every arm is scored
against a yardstick fixed before it was conceived and **no band is re-drawn**.

**The three vectors at `w_mom` = 0.500 are the designed comparison.** `tilt` splits the
remaining half across both features; `no-dd` and `no-id` put all of it on one. That holds
momentum's weight constant and varies only *what the other half is spent on*, which is the
cleanest attribution available without changing the frozen feature set (C10). A zero weight
expresses "drop this feature" without disturbing `composite.features` or its signs.

##### Six predictions, recorded before the runs

1. **Monotone in `w_mom`, in every frame.** `base` < `tilt` < `w3` < `w6` < `w8` < V0 on
   Total Net PNL, in all six frames independently. **This is the claim being made, and it is
   a shape claim across six replications, not an argmax claim about one cell.** If it holds
   in 6/6 that is strong; if it breaks, the frames where it breaks are the finding.
2. **No arm beats `PIT-wk-drift`'s ₹4,85,51,143.** If one does, §11's selection rule applies
   unchanged and it is adopted — the rule is not being rewritten now that more arms exist.
3. **`tilt` beats *both* isolation arms**, despite all three having `w_mom` = 0.500. This is
   a real consequence of the dilution model rather than a guess: if both added features are
   noise, then splitting the spare half across two independent columns gives a combined noise
   term with sd ∝ 0.25·√2 ≈ 0.354, against 0.500 for concentrating it on one. Averaging two
   noise columns is *less* damaging than doubling down on either. **If an isolation arm beats
   `tilt`, the feature it dropped is worse than noise and N9's "indistinguishable from
   random" reading is too generous.**
4. **`no-dd` beats `no-id`** — i.e. dropping drawdown helps more than dropping information
   discreteness. Basis: N9 measured drawdown's forward Spearman at **−0.012** against ID's
   **+0.001**, and drawdown carries the granularity defect (15.1% of name-dates within 2% of
   their own high; 99th percentile at −0.08%), so it manufactures rank distance from
   rounding. Direction predicted on measurement, not preference.
5. **No direction predicted for how the curve's *steepness* varies with cadence.** Faster
   rebalancing resamples the dilution noise more often, which could average it away or
   compound it. We have no basis to call it.
6. **Multiple comparisons, committed in advance and binding.** 39 new arms. Under a roughly
   normal band P(z > 1) ≈ 16% per arm, so **six or so cells clearing +1σ is the null
   expectation, not a signal.** No individual cell will be reported as a finding on its own
   `z`. Only the *surface* — monotonicity, and the three-way comparison at `w_mom` = 0.5 —
   is claimed. Any single standout cell is reported as consistent with luck unless it clears
   prediction 2's bar.

**2026 is not run for these arms.** §9 makes the stress window a rejection filter for
*candidates*; on prediction 2 none of these becomes one. `NOTES.md` N8 already notes this
project has now looked at 2026 twice for the V1 family, and a third look on 39 arms would
erode the filter for no decision it could inform.

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
NOTES.md               analysis notebook — mechanism reasoning, raw material for the report
PLAN.md                the V1 build plan — phases, and the decision queue behind each
src/
  config.py            load + validate; refuses a value for an open decision
  decisions.py         UnresolvedDecision, blocked()
  calendar.py          trading calendar, rebalance dates, lag arithmetic
  fetch.py             network only. writes data/raw/. never imported by backtest
  clean.py             panel construction, corporate actions, flags, quality report
  universe.py          as-of eligibility: full window, tradeable, member (A5/A10/A17)
  membership.py        A17 — press-release parsing, backward roll, membership mask
  events.py            B10/A18 — forced mid-cycle exits: one table, two sources
  features.py          signal computation — the 3 frozen features + the composite (C17)
  select.py            ranking, buffer, tie-break
  backtest.py          execution, costs, NAV, trades — signal- and weighting-agnostic
  metrics.py           round-trips and reported figures
  noise.py             the 10,000-draw band
scripts/               01_fetch  02_clean  03_v0  04_noise  07_sweep
                       05_v1 — the pre-registered composite arms (C10/C17)
                       06_report — report numbers, composition, the four figures
                       08_pit_universe — builds the point-in-time snapshot
                       09_feature_diagnostics — Phase 0. correlations only, no PNL
                       10_weight_sweep — the `WGT` weight surface, 42 cells (C9-r)
                       11_smallcap_universe — the `SMALL` arm's universe (A19)
                       12_signal_sweep — the `SIG` lookback x skip grid (C2-r)
tests/                 conftest  test_config  test_causality  test_accounting  test_clean  test_selection
data/raw/              immutable, as-of stamped snapshots
data/raw/press_releases/  27 NSE index-review PDFs — the membership evidence (A17)
data/clean/            validated panel
data/reports/          fetch log, data_quality.md (generated)
data/corporate_actions_overrides.csv
data/membership_overrides.csv  A17: renames, revocations, substitutions, waivers
data/phantom_days.csv  A8 rider: non-sessions the volume filter keeps. evidence-carrying
output/                nav, trades, holdings, weights, benchmarks, metrics, round_trips (CSV)
output/sweep/<cell>/   one variant cell each, so a variant never overwrites V0
output/report/         numbers.md + composition.md — generated, never hand-typed
output/figures/        the four report charts
output/v1/<arm>/       one pre-registered V1 arm each, same reason
output/v1/wgt_summary.csv  the WGT surface — one row per configuration
output/diagnostics/    Phase 0's feature study — the evidence behind C10-C17
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
python3 scripts/09_feature_diagnostics.py  # Phase 0: feature correlations, no PNL
python3 scripts/05_v1.py --arm base        # the composite. --arm buffer|tilt|rm-solo
                                           #   |w3|w6|w8|no-dd|no-id  (C9-r)
python3 scripts/10_weight_sweep.py         # the WGT weight surface, 42 cells, ~78 s
python3 -m pytest tests/ -q       # 92 pass, 0 xfail

# add --window stress for the 2026 rejection filter; --calendar/--weighting for one cell
```

`05_v1.py` runs **no** noise band: every cell's σ already exists, is read back and asserted,
so an arm is scored against a yardstick built before the arm was conceived. Re-drawing it
could only introduce drift.

No stub script remains — `cfg.pending()` has been empty since 2026-08-30, so there is no
config key left to be blocked on. The machinery stays in place for the next open decision.

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

Today **2 September 2026**. The universe rule changed under the project on 2 Sep (A3-r):
the organisers confirmed the scored universe is **the index constituents as of today**, not
point-in-time. Everything below is on that basis.

**Done.** Skeleton, data acquisition, the full cleaning layer, V0 end-to-end, the noise
band, the cadence × weighting grid, B10/A18 forced mid-cycle exits, the point-in-time
universe reconstruction (A17, now a robustness measurement rather than the scored rule),
the V1 composite and its 42-cell weight surface, **the signal grid (C2-r) and the Smallcap
100 arm (A19)** — and the whole search re-run on the mandated universe. **95 tests pass,
none xfail.** Every decision is closed.

### The submission

**`MAND-mo-reset` — 12-1 momentum, top 10, equal weight, rebalanced monthly, weights reset
to 1/10 each rebalance.** Nifty 100 + Nifty Midcap 100 as of today. Zero fitted parameters.

| | Value |
|---|---|
| **Total Net PNL** | **₹10,76,49,806** (+1,076.5%) |
| Final portfolio value | ₹11,76,49,806 |
| CAGR | 63.78% |
| Sharpe | 2.42 |
| Max drawdown | −32.40% |
| Costs paid | ₹20,59,816 (7.36× turnover p.a.) |
| Equal-weight universe benchmark | +280.6% |
| Nifty 100 benchmark | +89.4% |
| **Percentile of 10,000 random 10-stock books** | **100.00th — 0 of 10,000 beat it** |
| **Risk-adjusted percentile** | **96.01st** |
| H1 2026 rejection filter | **passes**: +7.60% vs Nifty 100 −6.65%, 88.9th pct |

### Is there anything better? Sixty-two configurations say no

The question was asked properly rather than assumed. Every axis available was swept, each
pre-registered before it ran, each scored against a band drawn beforehand:

| Axis | Cells | Result |
|---|---|---|
| Cadence × weighting (`MAND`) | 8 | **Monthly + reset wins.** +₹2.00 Cr over quarterly, `z_qtr` +2.32 |
| Momentum lookback × skip (`SIG`, C2-r) | 6 | **The frozen 252/21 is the argmax of its own surface.** 0 of 6 clear the 1σ bar |
| Universe: + Smallcap 100 (`SMALL`, A19) | 2 | **Loses** — −₹72 L quarterly, −₹4.39 Cr monthly (−5.1σ) |
| Composite signal (`V1`) | 4 | **All lose**, −5.15σ to −7.49σ |
| Composite feature weights (`WGT`) | 42 | **0 of 42 beat V0**, 0 reached +1σ against a null expectation of ~7 |

**Nothing beat the simple rule.** That is the finding, and it is reported as one rather than
buried: the losing arms are in §11 with their pre-registered predictions scored, including
the predictions that failed.

### Five findings a reader should not have to dig for

1. **The mandated universe carries 488 percentage points of index-inclusion bias, and we
   measured it rather than waiting to be asked.** The identical rule on a point-in-time
   universe returns +388.0% against +876.5%. The organisers mandate today's constituents, so
   this is a disclosed property of the scoring rule, not a defect in the strategy — but a
   number that large, computable with one config word in this repo, would be the most
   damaging possible omission. §10.
2. **B3 has now flipped twice, and both flips were the universe, not the weighting rule.**
   Reset beat drift on today's constituents, drift beat reset point-in-time, reset wins again
   now. Whether trimming winners is a premium or a tax depends on how many of your holdings
   were selected for having already run. `DECISIONS.md` B3.
3. **Adding smallcaps made the universe better and the strategy worse.** The equal-weight
   benchmark rises to +307.1% while the rule's PNL falls ₹4.39 Cr. A top-10-of-290 rule lets
   100 high-variance candidates win the ranking on noise. A19.
4. **Monthly rebalancing is not just more PNL — it is better selection.** The risk-adjusted
   percentile rises from 62.97 to **96.01** against V0's quarterly. That is the number that
   answers "or did it just take more risk?", and here it says no.
5. **The lookback sweep strengthened the zero-fitted-parameter defence instead of costing
   it.** The claim is now "swept over six pre-registered cells against a band fixed in
   advance, and the convention we started with won outright". C2-r.

### What is left

1. **The 5–6 page report.** `REPORT_OUTLINE.md` has the structure, the word budget and a
   pointer to the source of every number; `output/report/numbers.md` and
   `output/report/composition.md` are generated so nothing is hand-typed, and
   `output/figures/` holds the four charts. Writing the prose is the remaining work.
2. **Push to GitHub.** The repo is already wired to `origin`.
3. Strategy work is **closed**. §8's backlog is exhausted: item 1 by `WGT`, item 3 by A19,
   items 4–6 by the sub-band weighting evidence, item 7 (the tree ensemble) is not worth the
   remaining time to search a feature space three hand-picked features just failed in.
