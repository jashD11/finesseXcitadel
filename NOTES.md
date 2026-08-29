# Analysis notes

The running notebook (CLAUDE.md §2). Reasoning that is neither a decision (`DECISIONS.md`)
nor a configuration (CLAUDE.md §11) lands here the same day it is thought, because the
report is assembled from it and reconstructed reasoning is worse reasoning.

Each entry says plainly which parts are measured and which are speculation, and names the
in-sample test that would settle it. Nothing here has been tested against 2026 — §9 forbids
mining the stress window for explanations just as firmly as it forbids selecting on it.

---

## N1 · The cadence ordering inverts out of sample — 2026-08-28

**The observation.** Across the six non-daily grid arms, the rank correlation between
2021–25 PNL and H1 2026 return is **−0.89**. The selected configuration (`PIT-wk-drift`,
best in sample at ₹4.86 Cr) is close to the *worst* of the six out of sample at +5.44%.
`PIT-qt-drift`, which it beat by ₹0.93 Cr in sample, is the *best* out of sample at +11.97%.

At cadence level the two windows disagree everywhere except daily:

| | 2021–25 | H1 2026 |
|---|---|---|
| quarterly | worst ex-daily | **+11.37%** (best) |
| monthly | middle | +5.92% |
| weekly | **best** | +5.80% |
| daily | worst | +0.58% |

### The level drop is a separate question, and it is answered

All eight arms fell. The book is long-only and fully invested by design (§3) — no cash, no
regime gate — so its return is always *universe return + selection*, with no third term. In
sample the equal-weight universe compounded roughly 20%/yr; in H1 2026 it was flat. Around
20pp/yr of pure "being invested" disappeared.

That more than covers the level drop. It explains **nothing** about the ordering, because it
applies identically to all eight arms: a common factor moving cannot reorder positions that
all carry the same exposure to it. Worth keeping the two separate — conflating them is how
"the market changed" becomes an all-purpose excuse.

### First: there may be no flip to explain

Quarterly made **two** rebalance decisions in six months. Its +11.97% is essentially one
January basket held to April, plus one more. Weekly made about twenty-six. A two-decision
outcome has far wider variance than a twenty-six-decision outcome, so quarterly has much
more room to land in its own upper tail — and if it does, it reads as skill.

**The tell is already in the numbers: the percentile ranking does not show the flip.**
Measured against each arm's own random band — precisely the adjustment for cadences having
different outcome variance — weekly sits at 96.3 and 95.5 against quarterly's 95.3 and 93.5.
**Weekly is ahead on percentile and behind on raw return.** That pairing is the signature of
a variance artefact rather than a skill difference.

So the leading answer to "why did quarterly win out of sample" is that on this evidence, it
may not have. It won on a statistic that flatters low-decision-count arms and lost on the
one that corrects for it.

### If the flip is real: four mechanisms

*Speculation from here down. The frame:* cadence is a filter bandwidth. The 12-1 signal
updates daily and moves slowly — a 252-day lookback barely changes week to week. Cadence
does not control the signal, it controls how much of the ranking's high-frequency variation
gets **acted on**. Quarterly is a low-pass filter: only rank changes surviving a quarter are
traded. Weekly tracks the ranking closely, noise included. The question reduces to whether
that high-frequency component is signal or noise in a given regime.

**1 · Boundary churn.** With a 252-day lookback, most weekly turnover cannot be genuine
re-ranking — the signal has not moved enough. It is names oscillating across the rank-10
threshold on small price moves. What a crossing *means* is regime-dependent: in a trending
market a name crossing up is usually accelerating and acceleration persists, so the churn is
informative; in a choppy market a crossing is a wiggle that reverts, so the rule
systematically buys the local high and sells the local low. Same mechanism, opposite sign,
and it scales with cadence — quarterly only meets the boundary four times a year. *Lead
candidate, because it predicts its own fix: the §6 rank buffer exists to kill boundary churn
while preserving real signal change.*

**2 · Turning-point asymmetry.** Momentum's known failure mode is reversals, where prior
losers rip hardest and a momentum book is maximally exposed. Cadence sets how hard the book
re-commits at the turn. Quarterly, if the turn falls between dates, simply does not act —
passively wrong, but it does not re-express the view. Weekly re-picks straight through,
repeatedly buying whatever just topped. Fast cadence raises exposure to *being wrong at
turns* because it keeps restating a view that has just gone stale. Five years of bull market
contains few turns; six choppy months may be mostly turn.

**3 · Horizon matching — and this one reframes the project.** 12-1 momentum is documented to
pay over a roughly three-to-twelve-month holding period; the edge decays over months.
Quarterly cadence *matches* that horizon. Weekly holds each position far shorter than the
horizon over which the anomaly is known to work.

Which raises the possibility that we have this backwards. We treat 2021–25 as truth and 2026
as the anomaly. But 2021–25 was one unusually long, strong, persistent trend in Indian
midcaps — exactly the regime that rewards over-trading a slow signal. **"Weekly is best" may
be a finding about that regime rather than about the rule**, and quarterly's out-of-sample
win may be the rule reverting to its structurally sensible horizon. The data cannot settle
this, but it is the reading that would most change what we believe, so it is recorded rather
than left unsaid.

**4 · Costs as a fraction.** Costs are roughly linear in cadence and roughly constant per
unit time regardless of returns. At 20%/yr the extra weekly cost is noise; at 0%/yr the same
absolute drag is a visible share of the gap — about 0.7pp of the ~6.5pp difference, so
roughly a tenth of the effect. Real, directionally right, **not** the story. Stated
precisely so it does not get inflated into "it's a cost story."

### What would discriminate — in sample only

1. **Rank buffer at each cadence.** Direct test of mechanism 1, already backlogged as part
   of V1 (§6). *Prediction, recorded before running:* if boundary churn is the story, the
   buffer helps weekly substantially more than quarterly and compresses the cadence spread.
   If it barely moves weekly, mechanism 1 is wrong.
2. **Turnover decomposition.** At each cadence, what share of trades are names re-entering
   within a few rebalances of exiting? High recidivism at weekly confirms churn; low says
   the turnover is genuine signal change. Cheap and diagnostic.
3. **Regime sub-periods inside 2021–25.** The window contains real drawdowns (2022, the
   2024-06-04 election crash). Split it on a rule defined without reference to strategy
   returns and check whether the ordering flips in-sample too. Caveat: many comparisons on
   one dataset, so it generates hypotheses rather than settling them, and each cell needs its
   own band to be readable.

### Consequence for the report

**The shape is robust, the location is not.** Daily is clearly bad in both windows; the
quarterly-to-weekly range is a shallow, poorly-determined middle. The peak has already moved
once (monthly → weekly, on the universe fix) and 2026 disagrees with it on raw return —
three separate signals against reading the optimum as a precise number.

The selection does **not** change: §9 fixes it on 2021–25 PNL alone, and switching to
quarterly because 2026 prefers it is exactly the failure the rule exists to prevent. The
report should say plainly that quarterly, monthly and weekly are hard to separate
statistically, that weekly was selected because the pre-registered rule says highest 2021–25
PNL wins, and that the stress window ranked it differently on raw return while ranking it
first on percentile. That is a stronger section than a confident claim about weekly.

---

## N2 · B3 has been resolved twice, in opposite directions, on sub-band evidence — 2026-08-28

**Measured.** The drift-minus-reset gaps on the point-in-time universe are ₹4.91 L
(quarterly), ₹14.34 L (monthly), ₹29.00 L (weekly), ₹6.93 L (daily). The band's σ is
**₹50,92,127**. In σ units: **+0.10, +0.28, +0.57, +0.14**.

**Not one of the four clears one σ.** §5's rule is unambiguous — *if a change moves PNL by
less than the noise band, nothing has been found* — so by the project's own standard the
drift-versus-reset difference is undetermined.

Four same-signed sub-band results are weak evidence at best, and weaker than they look: the
four cells share a universe, a signal and largely overlapping holdings, so they are nowhere
near independent draws. A sign test on them is close to worthless.

**The uncomfortable part.** B3 was recorded `RESOLVED 2026-08-28 — drift` on this evidence,
having previously been resolved *in favour of reset* on the old universe — also on gaps
under one σ there. **The same decision has now been settled twice, in opposite directions,
both times on evidence that does not clear the project's own significance bar.** The honest
status is `UNDETERMINED`, and the conclusion the data supports is that the weighting rule
does not matter much at any cadence tested.

This is worth a paragraph in the report rather than a quiet correction. It is a clean
example of how a consistent sign across correlated cells impersonates a result, and the
project's own machinery is what catches it.

*Action:* raise with the user whether B3 should be reopened as `UNDETERMINED`. Per §2 that
is a decision, not a call to make unilaterally.

---

## N3 · Phase 0 feature diagnostics: the redundancy threshold was aimed at the wrong feature — 2026-08-29

**All measured**, on the point-in-time panel, 20 quarterly rebalance dates, 3,809
name-dates, 183–195 eligible names per date. Script `scripts/09_feature_diagnostics.py`,
artefacts in `output/diagnostics/`. No selection, no backtest, no PNL — nothing here was
chosen on an outcome.

Correlations are cross-sectional **on each rebalance date, then averaged across the 20
dates**. Pooling the stack instead would blend the cross-section with drift in each
feature's level over time, which is a different question from the one D1 asks.

### 1 · F2 is a near-copy of F1. PLAN.md put the threshold on F8 and never checked F2

`PLAN.md` D1 sets a redundancy threshold of ~0.70 for **F8 vs F1** and states no threshold
at all for **F2 vs F1**. Measured:

| pair | Spearman | top-10 overlap ranking on one alone vs the other alone |
|---|---|---|
| F1 vs **F2** (raw RM) | **+0.883** | **7.8 / 10** |
| F1 vs **F2** (standardised RM) | **+0.883** | 6.0 / 10 |
| F1 vs F8 drawdown | +0.43 (range −0.12 … +0.75) | — |
| F1 vs F9 info discreteness | −0.21 | — |
| F1 vs F7 skip-month | +0.06 | — |

**F8 passes the test PLAN.md set for it, comfortably. F2 fails the same test badly.** A
composite of F1 + F2 + F9 + F8 at equal weights is roughly half one concept: two of the
four columns rank the cross-section the same way 88% of the time, and ranking on raw
residual momentum alone reproduces 7.8 of plain momentum's top 10.

*Mechanism, and it is not a surprise once stated:* `RM = Mom − β·Mom_market`, and
`Mom_market` is a single scalar on each date. Subtracting a constant times β from Mom can
only re-rank names to the extent β varies — and the cross-sectional spread of β is small
against the spread of 12-month returns in this universe. This is arithmetic, not a
property of 2021–25, so the finding should generalise.

**This does not mean F2 is worthless** — the 12% of ranking it does not share with F1 is
precisely the beta-driven part, which §5 identified as V0's main exposure. It means the
pair cannot be treated as two independent concepts at equal weight. The live options are:
F2 *instead of* F1, F1 *instead of* F2, or both at weights that acknowledge the overlap.
Speculation as to which is better; **the in-sample test that settles it is one band-scored
arm per option**, and D14 caps the arm budget at four.

### 2 · D3 is nearly moot for the ranking, and its stated premise is half right

- `rho(raw RM, standardised RM) = +0.988`. The two produce almost the same ranking, though
  top-10 overlap against F1 differs (7.8 vs 6.0), so the choice is not literally free.
- D3's premise is that raw RM's spread scales with `sd(ε)`, so the raw ranking inherits an
  idio-vol loading. **The spread part is confirmed:** `rho(|raw RM|, F4) = +0.29` Spearman,
  **+0.44** Pearson.
- **The consequence is not.** The *signed* loading is `rho(raw RM, F4) = +0.070`, and
  standardising **raises** it to +0.107. Dividing by idio vol did not remove an idio-vol
  loading, because there was almost none in the signed ranking to remove.
- For scale: `rho(F1, F4) = +0.239`. Plain momentum carries three times the idio-vol
  loading that raw residual momentum does. The residualisation is doing real work on that
  exposure; the standardisation on top of it is not.

### 3 · D5's two options are not two estimators of one thing

`rho(F9, D5a) = −0.194`. Sign convention matters here and is easy to get backwards: F9
(information discreteness) is **low** when information arrives continuously, which is the
state Da–Gurun–Warachka find predictive, while D5a (fraction of positive 21-day blocks) is
**high** for the same state. **They agree when rho is negative**, so −0.19 is agreement —
and it is very weak agreement. These measure different things and D5 is a choice of
concept, not a choice of estimator.

D5a is also as coarse as predicted: 9 distinct values per date across ~190 names, and
**95.5% of names sit in a tied bucket**. Under a rank composite that is 95.5% of the
cross-section contributing no ordering information from that column.

*Consequence for whichever is chosen:* it enters the composite with a **negative** weight,
or negated. A feature list where every column is "higher is better" would have this one
backwards, and the error would be invisible in the output.

### 4 · D6 matters more than its correlation suggests

On D1(a)'s four features at equal weights: `rho(z-composite, rank-composite) = +0.971`,
but the two share only **5.7 of 10 names in the top 10** (range 4–8). A 0.97 correlation
across ~190 names is entirely compatible with the two rules disagreeing on 4 of the 10
positions that actually get bought. **Read the overlap, not the correlation** — for a
10-name book out of 190, the correlation statistic is measuring the wrong thing.

The skew premise behind D6's recommendation holds: F1 has cross-sectional skew **+2.31**,
excess kurtosis **+11.7**, a most-extreme name at **5.6σ**, and **1.5%** of all name-dates
beyond ±3σ. F6 is worse (skew +8.9, kurtosis +107). F2, by contrast, is almost symmetric
(skew −0.04, excess kurtosis +0.13) — residualising and standardising largely normalises
the distribution, which is a point in favour of the z route *if* F2 replaces F1.

### 5 · Two dropped candidates confirmed as droppable, one redundancy triangle confirmed

- `rho(F6 Amihud, F10 turnover) = −0.79`. Near mirror images, as expected. Dropping both
  costs one concept, not two.
- The triangle PLAN.md warns about is real: `rho(F5, F4) = +0.75`, `rho(F5, F3) = +0.59`,
  `rho(F3, F4) = +0.49`. F3, F4 and F5 in one composite would be triple-counting.
- **D2 is close to inert.** Between the EW-universe proxy and ^CNX100: `rho(β) = +0.934`,
  `rho(std RM) = +0.980`, `rho(raw RM) = +0.970`. The size-bet concern D2 raises against
  (b) does not show up either — RM's correlation with rupee turnover is +0.127 under (a)
  and +0.120 under (b). D2 should be decided on which is easier to defend, because the
  numbers will barely move.

---

## N4 · For a 10-name book, correlation understates disagreement — 2026-08-30

**Measured, three times, at three scales.** Phase 1 kept asking "are these two rules the
same?" and the rank correlation kept saying yes while the portfolio said otherwise:

| comparison | Spearman ρ | names in common in the top 10 |
|---|---|---|
| z-composite vs rank composite (D6/C3, still open) | +0.971 | **5.7 / 10** |
| raw vs standardised residual momentum (C12) | +0.988 | **7.3 / 10** |
| the two flat-day treatments (C16) | +0.9997 | **9.8 / 10** |

A 0.971 correlation across ~190 names looks like agreement and is compatible with the two
rules disagreeing on **four of the ten positions actually bought**.

**The mechanism is not subtle once stated.** The book is the top 10 of ~190 — the top 5%.
A correlation statistic is dominated by the bulk of the distribution, where most of the
mass sits and where the two rules do agree. It constrains the extreme tail only loosely,
and the tail is the entire portfolio. Nothing about this is specific to these features; it
follows from concentrating into 5% of the cross-section, so it applies to any comparison of
two selection rules in this project.

**The operational rule: report the top-10 overlap, not the correlation.** It is one line of
code and it answers the question that was actually asked — *would this change what we
hold?* — rather than a proxy for it.

**And the corollary is what made C16 easy.** The three rows above are a ladder: at ρ ≈ 0.97
the tail disagrees substantially, at 0.988 moderately, and only at **0.9997** does it
agree too. That is what separates a genuine `NON-ISSUE` from a decision with a small
measured effect, and it is a much better test than eyeballing whether a correlation "looks
high enough". C12's ρ = 0.988 would have passed a naive eyeball test and it changes 2.7
names out of 10.

*Caveat, stated because the same logic applies to it:* three points is not a calibration
curve. The ladder shows the direction, not a threshold — do not read "0.999 means
non-issue" as a rule. Measure the overlap each time; it costs nothing.

*Where this bites next:* D6 is exactly the comparison at the top of the table, and it is
Phase 2's first decision. It should be settled on the 5.7/10, not on the 0.971.

---

## N5 · The band σ is a conservative bar for variant-vs-V0, not a calibrated one — 2026-08-30

**The machinery, restated precisely.** §5's band is 10,000 random 10-stock portfolios. Its
σ (**₹50,92,127** on the point-in-time universe, quarterly) is the spread of outcomes across
*unrelated* books — draws that share the universe, the calendar and the cost model, and
nothing else. D11 then scores every variant as `(PNL_variant − PNL_V0) / σ`.

**Those are not the same distribution, and the mismatch runs in our favour.** Two arms of
the V1 slate share a universe, a signal family, a rebalance calendar and most of their
holdings — `V1-tilt` shares 4.0 of 10 names with V0 on any given date, `V1-base` 3.4. The
sampling spread of the *difference* between two such correlated books is much smaller than
the spread between two independent random draws. Using the random-draw σ as the denominator
therefore sets a **harder** bar than a properly matched null would.

That is a defensible way to be wrong. It means a variant that clears 1σ has cleared more
than it needed to, and a variant that fails may still be a real improvement we cannot see.
The project errs toward not finding things, which is the right direction for a
ten-day-old strategy with a competition deadline.

**What it forbids.** Reading σ as a calibrated significance threshold — "+1.2σ, therefore
p < 0.12" — is wrong in both directions at once: the denominator is too large *and* the
draws are not the right null. §5's rule is a **decision rule** ("if a change moves PNL by
less than the band, nothing has been found"), not a p-value, and should keep being written
that way in the report.

**A second, separate multiple-comparisons point.** `PLAN.md` D14 justified its arm cap with
"about 1 in 40 arbitrary configurations clears +1σ by luck alone". Under a normal band
P(z > 1) ≈ **16%** — 1 in 40 is the two-sigma rate. Corrected in place. The cap survives;
the error made it look less necessary than it is.

**What would settle it, in sample.** Build a *matched* null: instead of drawing 10 random
names, perturb V0's own rule — e.g. draw the book from the top 30 by momentum rather than
the top 10 — and measure the spread of that. That distribution is the right denominator for
"is this variant different from V0". It is a half-day of work on existing machinery
(`noise.py` already takes an arbitrary per-date candidate set), and it is the single
cheapest improvement available to the project's inference. **Not done, and not needed before
the deadline** — the current bar is conservative, so no result reported under it is
overstated. Recorded so the report can say plainly which bar was used and why.

---

## N6 · V1 failed, and the failure is monotone in the momentum weight — 2026-08-30

**All measured.** Five pre-registered arms (`CLAUDE.md` §11), every one scored against a
noise band drawn before the arms were conceived. Every one lost, by −3.47σ to −5.22σ.

### The single most informative number in the phase

PNL is **monotone in how much weight momentum carries**, across three points that were not
designed as a dose-response curve but form one:

| momentum weight | configuration | PNL |
|---|---|---|
| 1/3 | `V1-base` (equal weights) | ₹1,31,92,525 |
| 1/2 | `V1-tilt` (2/1/1) | ₹2,11,58,779 |
| 1 | `PIT-V0` (momentum alone) | ₹3,88,03,708 |

Every unit of weight moved *away* from information discreteness and drawdown, and *onto*
12-1 momentum, earned money. That is a far stronger statement than "the composite lost": it
says the two added features are not diluting a good signal with a neutral one, they are
diluting it with something that costs money over this window.

*Caveat, and it matters:* three points on one window is a suggestive shape, not a measured
gradient, and the two intermediate configurations are highly correlated with the endpoints.
The in-sample test that would settle it is a proper weight sweep — but §11's arm budget
exists precisely to stop that, and running one now would be searching a space after seeing
which direction pays. **Not run, deliberately.** The shape is recorded as an observation.

### The mechanism: de-risking, which the metric punishes — but that is not the whole story

Every V1 arm has lower annualised volatility than V0: **20.34%** (`RM-solo`), **21.84%**
(`V1-base`), **22.40%**, **22.43%**, against V0's **26.12%**. That is not an accident of the
window; it is built into the features. Drawdown-from-the-252-day-high correlates −0.28
(Spearman) / −0.41 (Pearson) with idiosyncratic volatility, so ranking on it tilts away from
volatile names by construction — and C15 cited exactly that property *in its favour*, on the
strength of §5's finding that V0's dominant exposure is a volatility loading.

So §3's standing claim is confirmed on live data for the first time: *risk-reduction
machinery is a handicap under this metric.* It had only ever been asserted.

**But stopping there would be too kind to V1.** If the composite were merely trading return
for risk it would hold its own per unit of risk. It does not — Sharpe falls 1.43 → 0.84, and
max drawdown gets **worse**, −31.29% → −40.52%. Lower volatility *and* deeper drawdown is not
a risk-return trade; it is a worse portfolio on every axis. The honest reading is that over
2021–25 the two added features carry no demonstrated forecasting content at all.

### The methodological lesson, which is the part worth carrying forward

**Phase 0 could not have predicted this, and said so at the time.** Its entire output was a
correlation structure: it established that momentum, information discreteness and drawdown
measure *distinct* things (ρ(F1,F9) = −0.21, ρ(F8,F9) = −0.04 — remarkably orthogonal). N3
stated plainly that distinctness is not forecasting power and that only a band-scored arm
could settle it.

That was right, and it is worth being precise about what it means. **A diagnostic that
selects features on orthogonality selects for exactly the thing that makes them useless if
they carry no signal:** an orthogonal-but-empty column does maximum damage to a composite,
because it dilutes the good signal without correlating with it. Had F9 been 0.9 correlated
with F1 it could not have hurt much. It was −0.21, so it hurt a lot.

The one-per-concept rule (§6) is a defence against double-counting. It is *not* evidence
that the concepts are worth counting once, and this project came close to reading it that
way. The rule should be stated in the report with that limit attached.

### What we did not do, and why

No post-hoc rescue was attempted: no re-weighting toward whatever wins, no dropping F9 and
re-running, no trying the z-composite after the rank composite lost. Each would be searching
the space after seeing the answer, and the pre-registration exists to make that visibly
off-limits. The tilt vector that *was* run was declared before any arm executed, which is
the whole distinction — and it is worth noting it came second-best of the five, so
pre-registering it was not a wasted slot.

**The result stands as reported: V1 is not adopted, `PIT-wk-drift` remains the submission,
and the negative result is a stronger report section than a marginal win would have been.**
