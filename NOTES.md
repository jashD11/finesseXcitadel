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

---

## N7 · Why V1 lost by so much: it traded the right tail, not the risk — 2026-08-30

N6 recorded *that* V1 lost and offered the §3 de-risking mechanism with the honest rider
that Sharpe and drawdown both got worse, so de-risking could not be the whole story. This
entry is the follow-up diagnosis. **Nothing here is a trial** — no configuration was
backtested, no engine was run. Every number is a cross-sectional statistic over the same
20 quarterly rebalance dates the arms used (3,809 name-dates, forward returns measured
open-to-open between consecutive rebalance dates, matching B2's execution convention), plus
the two NAV series already on disk. No §11 ledger row is owed.

### The single line that says it

| | V0 | `V1-base` |
|---|---|---|
| Accuracy (profitable round trips) | 59.43% | **59.18%** |
| Gain-to-loss (mean win ÷ mean loss) | **1.92** | **1.14** |

**V1 wins on the same fraction of trades and makes far less on the ones it wins.** The
composite did not pick more losers. It picked smaller winners. Everything below is why.

### 1 · The composite demotes the extreme momentum names, and that is where the money was

The book still looks like a momentum book by *rank* — mean percentile 0.896 against V0's
0.976, median momentum rank 18 of ~190, and only 0.5% of picks sit below the momentum
median. But by *magnitude* it is a different portfolio: mean trailing 12-1 momentum of the
names held falls from **+181.9% to +102.7%** (universe mean +33.2%). Sliding from rank ~3
to rank ~18 costs 79 percentage points of trailing momentum, because the top of that
distribution is extremely right-skewed — the point C17 conceded when it chose ranks over
z-scores ("a name up 300% ranks one place above a name up 200%").

Measured forward return by momentum rank bucket, equal-weight, mean over the 20 quarters:

| 12-1 momentum rank | mean forward quarter | annualised | quarterly sd | mean/sd |
|---|---|---|---|---|
| **1–10** | **+9.56%** | **+44.1%** | 16.58% | 0.576 |
| 11–20 | +5.14% | +22.2% | 12.20% | 0.421 |
| 21–30 | +6.03% | +26.4% | 10.85% | 0.556 |
| 31–50 | +5.08% | +21.9% | 10.59% | 0.480 |
| 51–100 | +5.76% | +25.1% | 8.99% | 0.641 |
| 101+ | +4.19% | +17.8% | 8.14% | 0.514 |

**The payoff is a step at rank 10, not a gradient.** Past the top ten the curve is flat at
5–6% against a universe mean of 5.12%. V1's median pick sits at rank 18 — on the flat part.
(The 51–100 bucket's mean/sd of 0.641 is not a rival: it is a 50-name portfolio, so its sd
is lower for diversification reasons alone. The like-for-like comparisons are 1–10 vs 11–20
vs 21–30.)

### 2 · Two thirds of the selection is made by columns with no measured forward content

Cross-sectional Spearman against the next quarter's return, computed per date and averaged
over 20 dates, with each feature signed as it enters the composite:

| Feature | mean ρ | median | ρ > 0 on | t |
|---|---|---|---|---|
| 12-1 momentum (+) | +0.035 | +0.062 | 12/20 | 0.99 |
| Information discreteness (−) | **+0.001** | +0.014 | 11/20 | 0.04 |
| Drawdown from 252d peak (+) | **−0.012** | −0.002 | 10/20 | −0.49 |
| The composite | +0.015 | +0.037 | 12/20 | 0.49 |
| Residual momentum (+) | +0.036 | +0.061 | 12/20 | 1.10 |

Information discreteness is indistinguishable from noise and drawdown-from-peak is *weakly
the wrong sign* over this window. At equal weights across three near-orthogonal columns each
gets roughly a third of the say — Spearman of the composite's rank against each signed
feature rank is +0.789 (momentum), +0.703 (drawdown), +0.575 (ID). So about two thirds of
the selection is being made by columns that, measured here, forecast nothing. This is N6's
orthogonality lesson with a number attached.

### 3 · The swap reconciles the gap almost exactly

Of the 200 top-10-momentum name-dates, the composite keeps only **67** (34%). The
arithmetic of why: a rank-1 momentum name earns 1/3 from momentum, and the 10th-best
composite score averages 0.835, so it must also place around 25th of ~190 on *both* other
features to survive. Extreme in one thing is not enough; the composite selects consensus.

| | n | mean forward quarter |
|---|---|---|
| Top-10-momentum names V1 **kept** | 67 | +6.42% |
| Top-10-momentum names V1 **cut** | 133 | **+11.14%** |
| What V1 bought instead | 132 | +4.87% |

6.65 of 10 names swapped per quarter × (4.87 − 11.14) ÷ 10 = **−4.17pp per quarter implied
drag**, against a **−4.10pp measured** gap between the two books' gross equal-weight
quarterly returns (V0 +9.56%, V1 +5.46%). The mechanism accounts for essentially the whole
shortfall; there is no residual to explain.

### 4 · Why Sharpe fell, when de-risking alone would have left it flat

Volatility fell 16.4% (26.12% → 21.84%). Return fell 50.9% (37.34% → 18.34%). A
Sharpe-neutral de-risking would have left 37.34 × 21.84/26.12 = **31.22%** of return; V1
delivered 18.34%, so **12.9pp of annual return was given up without buying any risk
reduction for it**.

The reason is that the volatility it did remove came off the wrong side:

| | days > +2% | mean of them | days < −2% | mean of them | best day | worst day |
|---|---|---|---|---|---|---|
| V0 | 116 | +3.03% | 101 | −3.27% | +8.37% | −11.18% |
| `V1-base` | 70 | +2.84% | 83 | −2.98% | +6.20% | −5.70% |

**The right tail is cut 40%, the left tail only 18%.** Compounded, V0's best 20 days are
worth +152.0% and its worst 20 −67.4%; V1's are +113.8% and −58.7%. Portfolio volatility is
a two-sided second moment and treats those alike — compounded PNL does not. That asymmetry
is the entire Sharpe drop, and it is also why §3's "raw PNL rewards volatility" is too loose
a statement of the effect: what raw PNL rewards is *right-tail exposure*, and volatility is
only its proxy.

### 5 · Why max drawdown got worse despite lower volatility

Both books peak on the same day, **2024-09-24**, and neither recovers by 2025-12-31. From
that peak V0 falls −31.29% over 170 days at 26.1% annualised volatility; V1 falls **−40.52%
over 195 days at 20.6%**. V1's drawdown is not a volatility event, it is a *drift* event —
it has **more** down days (45.5% vs 42.7%) that are individually **smaller** (−1.04% vs
−1.24%). A grind, not a shock.

This is what the two added features should be expected to produce on a reversal. Low
information discreteness selects for a smooth information drip; a smooth uptrend that turns
over is a smooth *downtrend*, and the feature has no way to tell the difference. Drawdown
from the 252-day peak compounds it: V1's book sits **−2.81%** from its 252-day high against
V0's −11.35% and the universe's −14.38%, so it is buying names at the point of maximum
distance from any recent support. Both are path-smoothness bets, and path smoothness is
exactly the property that survives a regime turn while the returns do not.

### 6 · The honest caveat, which cuts against the tidy story above

**The top-10 tail premium is real in this window but thin per observation.** Top 10 minus
ranks 11–30, per quarter: mean +3.97pp, positive in only **12 of 20** quarters, paired
t = **+1.66**. Drop the single best quarter and it falls to +2.78pp; **drop the best three
of twenty and it is +0.66pp.** Within the top-10 bucket itself the mean forward return is
+9.56% against a **median of +3.54%** (skew +1.50); excluding the best 20 of 200
name-quarters drops the bucket mean to +3.18%.

And the composite's split of that bucket is a *mean* effect, not a distributional one: kept
names median +3.29% vs cut names median +3.95%, Mann-Whitney p = **0.357**. The composite
was not systematically choosing the worse half of the top-momentum names — it was declining
a small number of extreme winners.

**So the correct statement is narrower than "V1 forecasts worse".** V1 lost ₹2.56 Cr because
it systematically declined the names with the highest chance of being an extreme winner, and
over 2021–25 four or five of those decided the PNL. That is the same thin edge §5 already
found: V0 beats 9,996 of 10,000 random books on raw PNL but only sits at the 73.74th
percentile per unit of risk. The two findings are the same fact seen twice.

### 7 · Consistency checks that came out clean

- **Monotone in momentum weight, on the mechanism as well as the PNL.** Median momentum rank
  of the book: V0 6 → `V1-tilt` 14 → `V1-base` 18. Share of top-10-momentum name-dates
  retained: 100% → 40% → 34%. Gross mean quarterly return: +9.56% → +7.06% → +5.46%. The
  ledger's PNL ordering (₹3.88 Cr → ₹2.12 Cr → ₹1.32 Cr) is reproduced by a statistic
  computed without the backtest engine at all.
- **`RM-solo` fits the same curve.** It keeps 60% of the top-10-momentum names, median
  momentum rank 8, gross +6.14%/quarter — between V0 and the composite, exactly where its
  60% retention puts it.
- **Annual damage tracks the annual tail premium.** The top-10-minus-11-30 premium by year
  is +6.5, +3.8, +4.2, +9.4, −4.1pp for 2021–25; V1's NAV gap against V0 is −9.9, −12.6,
  −41.1, −34.7, −3.5pp. Correlation −0.586 on n = 5 — weak evidence, but note that 2025, the
  single year the premium went *negative*, is also the year V1 lost least.

### 8 · What must not be done with this entry

Every number above is measured on **2021–25, the selection window, after seeing the
result**. The obvious rescue it suggests — rank on momentum first and let the other two
features break ties inside the top 20 or 30 — would be a configuration chosen by looking at
the answer, and §9's discipline applies to the selection window just as much as to 2026. It
would need pre-registration, its own ledger row and its own band, and it would still be
resting on a t = 1.66 premium that three quarters of twenty carry.

It is not being run. The deadline is 31 Aug, `PIT-wk-drift` is the submission, and this
entry's value is as report material explaining a negative result — not as a lead.

---

## N8 · V0 vs `V1-base` on the 2026 window — pre-registration — 2026-08-30

**Written before the run.** `V1-base`'s ledger row says `2026: not run`, because §9 reserves
the window for candidates and V1 lost 2021–25 by −5.03σ. It is being run now as a
**diagnostic on the mechanism N7 identified**, not as a rescue. The selection rule is
unchanged and cannot be changed by what follows: `PIT-wk-drift` is the submission, chosen on
2021–25, and §9 forbids promoting a config on a 2026 number in either direction.

### The claim being tested

The user's, stated before the run: *"pure momentum (V0) seems most profitable even though it
takes more risk — much of this can be attributed to a very bullish market over the backtest
period. I expect the gap between V0 and V1-base to reduce at the very least."*

This is a real, falsifiable mechanism and it follows from N7 rather than contradicting it.
N7 measured that V0's edge is **right-tail exposure**: it holds the top-10-momentum bucket,
which returned +9.56%/quarter against +5–6% everywhere else, and that premium is carried by
a handful of name-quarters. A tail premium of that shape needs a market that produces
extreme winners. If H1 2026 does not, V0's advantage should shrink or invert.

Note the direction this cuts: it is **not** a defence of V1. It says V0's margin is
regime-dependent, which is a weakness of V0, not a strength of the composite.

### Predictions, recorded now

1. **The gap narrows.** V0 minus `V1-base` on H1 2026 total return comes in **smaller than
   the 2021–25 gap** — trivially likely on horizon alone (6 months vs 5 years), so the
   honest version is the *annualised* comparison: the H1 2026 annualised gap comes in below
   the 2021–25 annualised gap of 37.34% − 18.34% = **19.0pp**.
2. **The mechanism, not just the outcome.** If the gap narrows, the top-10-momentum bucket's
   premium over ranks 11–30 should be **smaller in H1 2026** than its 2021–25 mean of
   +3.97pp/quarter. If the gap narrows while the premium does *not*, the narrowing is luck
   over two rebalances and will be reported as such.
3. **Two rebalance dates is one observation.** §9 already says this about V0's own +10.77%,
   and §9's own history says it louder: a single stale bar once halved that figure. Whatever
   comes out, no ordering established here is evidence about either configuration.
4. **No direction is predicted for the sign.** The gap narrowing to zero, and V1 *beating*
   V0 over six months, are both consistent with N7 — a tail premium that is positive in
   12 of 20 quarters is negative in 8.

### What this run may not be used for

It may not move `PIT-wk-drift`, revive V1, or motivate a momentum-first hybrid. N7 §8
already ruled the hybrid out on the selection window; adding a 2026 look would make it
worse, not better. This entry exists so that the number, once it exists, is bounded by what
was said before it did.

### Result — run 2026-08-30, after the predictions above were written

`python3 scripts/05_v1.py --arm base --window stress`. Quarterly/reset, two rebalances
(2026-01-01, 2026-04-01), B8 restart with a fresh ₹1 Cr, B10 exits active, same engine.

| H1 2026 | V0 | `V1-base` |
|---|---|---|
| Total return | **+10.77%** | **−1.11%** (₹−1,11,393) |
| Annualised | +23.07% | −2.25% |
| Sharpe | 0.85 | **−0.10** |
| Max drawdown | −12.55% | −16.67% |
| Percentile in the fresh 10,000-draw band | **93.47th** (+1.57σ) | **43.58th** (−0.21σ) |
| Draws beating it | 653 of 10,000 | 5,642 of 10,000 |

**Prediction 1: FAILED. The gap widened.** Annualised, 2021–25 was 37.34% vs 18.34% = 19.0pp;
H1 2026 is 23.07% vs −2.25% = **25.3pp**. `V1-base` is not merely worse than V0 out of
sample — at the 43.58th percentile it is **indistinguishable from a random 10-stock book**,
while V0 stays at the 93rd. It also lost money in a window where V0 made 10.8%.

**Prediction 2: FAILED, and this is the substantive part.** The mechanism N7 identified did
not weaken in the flatter window; it strengthened slightly. Top-10-momentum bucket minus
ranks 11–30, equal-weight, per period:

| | 2021–25 | H1 2026 |
|---|---|---|
| Tail premium | +3.97pp per quarter | **+4.35pp per period** |

**A contamination was caught computing this and is corrected above.** The raw figure was
+5.54pp. VEDL sat at momentum rank **25** on 2026-04-01, so its uncorrected −57.24% bar —
the A16 demerger discontinuity, not a real loss — was dragging the 21–30 bucket to −0.10%.
Dropping VEDL from the cross-section puts that bucket at +2.26% and the premium at +4.35pp.
The backtests themselves were never affected: B10 exits VEDL on 2026-04-29 in both engines.
The same artefact explains why an uncorrected gross calculation gives `V1-base` −6.58%
against its true −1.11%, while V0 (which never held VEDL) reconciles at +11.22% gross vs
+10.77% net.

### The bull-market hypothesis does not survive the down leg

The premium in the two legs was **+6.49pp** then **+2.22pp** — larger in the *falling* one.
H1 2026 splits into a down leg (2026-01-01 → 2026-04-01, universe −11.6% equal-weight) and a
recovery. In the down leg:

| momentum rank | forward return, Jan → Apr 2026 |
|---|---|
| **1–10** | **−6.20%** |
| 11–20 | −12.39% |
| 21–30 | −12.97% |
| 31–50 | −11.39% |
| 51–100 | −8.73% |
| 101+ | −11.63% |

The top-10-momentum bucket **fell roughly half as much as every other bucket**. On this one
observation the tail premium is not a bull-market amplifier — it was defensive. That is one
market leg and must not be read as a general property, but it is evidence *against* the
reading that V0's 2021–25 margin is simply beta to a rising mid-cap market, and it is the
same direction §5 pointed when the point-in-time rebuild *raised* V0's risk-adjusted
percentile from 63.5 to 73.7.

### Two observations that were not predicted

**V1's 2026 book was more momentum-like than its 2021–25 book, and still lost.** Median
momentum rank of the composite's picks was **11** here against 18 in sample, and it retained
**9 of 20** top-10-momentum name-dates (45%) against 34%. So the loss out of sample cannot be
attributed to rank displacement alone — the two added features were simply wrong. Their
forward Spearman over the two periods: information discreteness (negated) **−0.040**, wrong
sign in *both* periods; drawdown from peak +0.150 then −0.142, sign-flipping. 12-1 momentum
was +0.061, the only column positive in both.

**The B10 exit rule is doing more work than the ledger shows.** VEDL ranked **6th on the
composite** on 2026-04-01 while ranking 25th on momentum — the two path features liked a name
about to gap down on a demerger. V1 bought it; V0 did not. Without B10's forced exit V1's
H1 2026 would have been materially worse. This is the third time A16/B10 has changed a
headline number (§9's weekly arm, §11's `EXIT-rule` row, now this).

### What this changes: nothing about the submission

Both predictions failed, so the entry ends where it began. `PIT-wk-drift` is the submission,
selected on 2021–25. §9's rule is symmetric — this window may not demote a candidate onto a
better one any more than it may promote one — and V1 needed no demoting, having lost by
−5.03σ on the window that counts. The value of the run is that a *reader's* obvious objection
("V0 is just long a bull market") now has a measured answer rather than an assurance.

---

## N9 · Bug hunt on the V1 result, and what it actually found — 2026-08-30

Prompted by the objection that a single indicator crushing a three-feature composite, in
sample *and* out of sample, is the shape a bug makes rather than a finding. Eight checks
below. **No bug was found**, but check 4 changes how the result should be read and check 3
turned up a structural property of C17 nobody had noticed.

### Checks 1–2 · Do the diagnostics reproduce the engine, and does the one mismatch matter?

Rebuilding both books from the panel and comparing name-for-name against the engine's own
`holdings.csv` across 20 rebalance dates: **V0 matched on 20 of 20**. `V1-base` matched on
19 of 20; the exception is 2025-04-01, where the 10th and 11th composite scores are
**exactly equal** at 0.821930 and C7's incumbent-first tie-break picks HINDALCO. Engine
correct, diagnostic naive. Every figure in N7 and N8 stands.

### Check 3 · Scaled ranks tie, and z-scores could not have

Under C17 with equal weights the score is `(a+b+c)/(3(N+1))` for integer ranks `a,b,c` — a
discrete lattice. Measured: **158–179 distinct composite scores across 183–195 names**, so
15–20 names per date share a score with someone. The 10th place was an exact tie on **2 of
20** dates and the C7 tie-break decided **1** name over the whole backtest.

Immaterial to the result — one name in twenty rebalances — but it is a real property C17 did
not anticipate, and it is the opposite of the robustness argument that motivated ranks. It
belongs in the report's discussion of the combination rule, not in its defence.

### Check 4 · The finding that reframes N7: the damage is dilution arithmetic, not bad features

Replace information discreteness and drawdown with **two random columns** of the same rank
distribution, keep 12-1 momentum, keep equal weights. 2,000 draws, seed 20260830. Gross
compounded return of the top-10 book over the 20 quarters, cost-free:

| | gross compounded |
|---|---|
| V0 — momentum alone | **+393.2%** |
| momentum + **two random columns** | **+207.9%** (5th–95th: +105.2% to +333.4%) |
| `V1-base` — momentum + the two real columns | +138.6% |

**`V1-base` sits at the 16.5th percentile of the noise-column null — mildly worse than
random, but inside the distribution.** So of the ~255pp gross gap between V0 and `V1-base`,
roughly **185pp is what two columns of pure noise would have cost anyway**. The two features
are not the story. The *combination rule* is.

The dilution curve, same null, 500 draws per point:

| momentum weight `w` | gross compounded | 5th–95th |
|---|---|---|
| 1.00 | **+393.2%** | — |
| 0.80 | +277.6% | +169.0% to +418.2% |
| 0.67 | +254.8% | +133.7% to +420.3% |
| 0.50 | +227.9% | +118.6% to +372.4% |
| 0.33 | +209.1% | +109.9% to +354.0% |
| 0.00 | +148.1% | +71.7% to +237.8% |

**The curve is a cliff, then a plateau.** Handing away just 20% of the vote costs 116pp;
handing away the remaining 47% costs only another 69pp more. That is the top-10-of-190
selection rule being a knife edge — N7's step function at rank 10 seen from the other side.
Once any contamination knocks the book off the extreme momentum tail, further contamination
is nearly free.

**Two consistency checks the null passes.** At `w = 0` it returns +148.1%, against §5's
median random draw of +141.3% and the equal-weight universe's +151.6% — it converges on the
right object. And the real arms fall where the curve says: ₹3.88 Cr at `w = 1`, ₹2.12 Cr at
`w = 0.5`, ₹1.32 Cr at `w = 0.33`.

### Checks 5–6 · Are the features specified as their literature specifies them?

**A latent sign pathology exists and did not fire.** `ID = sign(Mom) × (%neg − %pos)`, so a
smoothly-*declining* loser gets a low ID and, entering negated, a **high** composite score.
Da, Gurun & Warachka (2014) is an interaction — among winners, low-ID names continue — and
C14 applied it as an unconditional main effect. Measured: losers average ID −0.0337 against
winners' −0.0454, so the mechanism is live in the cross-section. It cost nothing here because
**only 1 of 199 picks had negative momentum** (worst momentum bought: −9.9%). Recorded as a
defect in the specification, not as a cause.

**Conditioning does not rescue either feature.** Forward Spearman, unconditional vs computed
within the top 30 and top 50 by momentum:

| feature | all names | top-30 mom | top-50 mom |
|---|---|---|---|
| info discreteness (−) | +0.001 | +0.006 | −0.017 |
| drawdown from peak (+) | −0.012 | −0.002 | −0.050 |
| 12-1 momentum (+) | +0.035 | **−0.001** | +0.030 |

The DGW-faithful conditional form is +0.006. There is no hidden signal that the wrong
functional form was suppressing. **Note the third row:** momentum's own rho *within* the top
30 is −0.001 — it separates the top 10 from the field and carries no ordering information
inside the winners. That is the same step function again, and it is why a tie-break-quality
composite cannot recover what strict momentum ranking gets.

### Check 7 · The drawdown column cannot discriminate where it matters

Drawdown from the 252-day peak is bounded above at zero with mass piled at the top: **15.1%
of name-dates sit within 2% of their own 252-day high**, and the mean 99th percentile across
dates is **−0.08%**. In the region that decides the book the feature separates names by
fractions of a percent, and the ranking then treats those fractions as full ranks apart. It
manufactures rank distance out of rounding. This is noise, which check 4 has already priced.

### Check 8 · Conclusion

**The result is not a bug, and it is not really "one indicator beats three" either.** It is
that a top-10-of-190 rule is a knife-edge selection, and equal weighting is a *strong prior*
— it asserts that all three features deserve an equal vote. Two of them never met that
burden, and C9 granted it by default because equal weighting looks like the neutral choice.
It is not neutral. On a knife-edge rule it is close to the most aggressive claim available.

That is the sentence for the report: **the error was in the combination rule's default, not
in the feature research.** The one-per-concept discipline (§6) and Phase 0's orthogonality
screen were sound work aimed at the wrong risk — they defended against double-counting a
good signal, when the live risk was giving a two-thirds vote to columns whose forecasting
power had never been measured at all.

---

## N10 · The weight surface, and the limit it put on N7's mechanism — 2026-08-30

`WGT`: 7 weight vectors × 3 cadences × 2 weighting rules = 42 cells, pre-registered as one
set (`DECISIONS.md` C9-r, `CLAUDE.md` §11) with six predictions written before any ran. Full
results and prediction scoring are in §11; this entry carries the mechanism.

### The headline is a non-result, and it is a clean one

**0 of 42 cells beat V0 in their own frame. 0 of 42 reached even +1σ**, against a null
expectation of about 7 at P(z > 1) ≈ 16%. The best of 42 — `w6` at weekly/reset,
₹4,00,18,129 — is ₹85,33,014 short of `PIT-wk-drift`. The composite is not rescued by
re-weighting, and it is now judged on seven vectors across six frames rather than two.

### N9's cliff-then-plateau was right, which is why prediction 1 was wrong

`base` → `tilt` → `w3` (w_mom 0.333 → 0.500 → 0.600) rises in **6 of 6** frames, every step
positive and most above +1.3σ. Every inversion sits in the `w3` → `w6` → `w8` plateau
(0.600 → 0.800), where steps run −1.42σ to +1.92σ with no consistent sign. N9's noise-column
null said the curve is a cliff between w = 1.0 and w ≈ 0.8 and a plateau below it; the strict
monotonicity prediction failed **because the model behind it was right**. Worth keeping as an
example of a prediction that was stated too strongly for its own mechanism.

### The finding I did not see coming: N7's retention model has a boundary

N7 explained V1's loss as displacement of the top-10-momentum tail, and across the weight
ladder that model is close to exact:

| vector | `w_mom` | top-10-mom name-dates retained | median momentum rank | direction of PNL |
|---|---|---|---|---|
| `base` | 0.333 | 67/200 (33.5%) | 18 | lowest |
| `tilt` | 0.500 | 81/200 (40.5%) | 14 | ↑ |
| `w3` | 0.600 | 92/200 (46.0%) | 11 | ↑ |
| `w6` | 0.750 | 125/200 (62.5%) | 8 | ↑ |
| `w8` | 0.800 | 134/200 (67.0%) | 8 | highest |

Monotone in retention, monotone in PNL. **Then the isolation pair breaks it.** Both hold
momentum at exactly 0.500 and differ only in what the spare half is spent on:

| vector | spare half on | top-10-mom retained | PNL |
|---|---|---|---|
| `no_ddown` (1/1/0) | information discreteness | **95/200 (47.5%)** | **loses in 6/6** |
| `no_idisc` (1/0/1) | drawdown from peak | **62/200 (31.0%)** | **wins in 6/6** |

**The arm that keeps more of the momentum tail loses, unanimously, in every frame.** So
retention is not the operative variable here. Keeping information discreteness displaces
*less* of the tail and costs *more*, which means it must be selecting worse names **within**
the tail rather than moving the book off it.

**Consequences, stated plainly.**

1. **N7 and §7 must be read with a boundary attached.** "PNL tracks how much of the top-10
   momentum tail you hold" is sufficient for the weight ladder and **false in general**. It
   was derived from a comparison (V0 vs `V1-base`) that varied retention and feature content
   together; the isolation pair varies them in opposite directions and separates them.
2. **N9's ranking of the two features is retired.** Forward Spearman said drawdown was the
   worse column (−0.012 against ID's +0.001). Six frames say the opposite, unanimously.
   A cross-sectional rank correlation over ~190 names was the wrong instrument for a
   question about a 10-name book — which is **N4's own finding**, applied here to a
   diagnostic N4 should have warned me off. Recorded as a methodological repeat offence,
   not a one-off.
3. **What would settle *why* information discreteness is the more harmful column** is a
   within-tail test: among the top-30 by momentum, sort by ID and measure forward returns.
   N9's check 5 ran the conditional Spearman (+0.006, near zero) but not the *selection*
   version — what the top 10 by ID within the top 30 by momentum actually returned. That is
   the in-sample test that would discriminate, and it is **not being run**: it is a new
   diagnostic suggested by a result, on the selection window, on the last day before the
   deadline, and it could not change the submission.

### Cadence, which no prediction covered

Dilution costs proportionally **less** at faster cadence: `base` retains 34.0%/33.3% of V0's
PNL at quarterly, 44.5%/44.3% at monthly, 47.5%/48.5% at weekly. A plausible mechanism is
that faster rebalancing draws the dilution noise more often and averages it away. That is
post-hoc and labelled as such — no direction was predicted, so this is a measurement, not a
confirmation, and it is the kind of claim that should be pre-registered before it is believed.

---

## N11 · The payoff surface is a plateau with a cliff at rank 10 — 2026-08-30

Written in response to a direct question — *what signals or features would enhance PNL, or
improve Sharpe without costing PNL much?* — and answering it with measurement before
proposing anything. Four diagnostics, all on the point-in-time panel, all causal (trailing
windows end at `formation_cutoff`, forward returns run open(t) → open(t+1) per B2).

**Everything below is a diagnostic, not a backtest.** No costs, no whole-share flooring, no
B10 events, no cash reserve. The calibration check is that the 12-1 book compounds to
**+369.3%** here against `PIT-V0`'s measured **+388.0%** — close enough that gaps of 150pp+
in the same table are real and not artefacts of what the diagnostic omits.

### 1 · Inside the top 10, forward return is flat in momentum rank

N7 measured the step *at* rank 10. This measures the shape *inside* it. Mean forward return
by momentum rank within the selected book, 1 = strongest:

| rank | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| quarterly, fwd % | 3.87 | 6.32 | 10.68 | 12.74 | 13.94 | 10.86 | 8.81 | 9.04 | 13.52 | 8.15 |
| weekly, fwd % | 0.32 | 0.45 | 1.14 | 1.29 | 1.06 | 1.01 | 0.30 | 0.75 | 0.65 | 0.64 |

Per-date Spearman(momentum rank, forward return), averaged: **+0.0118** quarterly,
**+0.0180** weekly. The strongest-momentum name is the *worst* bucket at quarterly (+3.87%
against a book mean near +9.8%) — noise at n=19, but decidedly not an ordering.

**This closes §8 backlog item 4 (score-weighted instead of equal weight) on evidence rather
than leaving it "not started".** Conviction weighting needs the score to order forward
returns among the names you already hold. It does not. Tilting toward rank 1 tilts toward
nothing. 1/N is not merely hard to beat here; there is no measured gradient to beat it with.

### 2 · Combined with N7, the payoff surface is fully characterised

N7: forward return by momentum rank bucket is **+9.56%** for 1–10 and **+5.14%/+6.03%** for
11–20/21–30 — flat past the top ten. §1 above: flat *inside* the top ten. So:

> **A plateau at rank ≤ 10, a cliff at the boundary, a second flat plateau beyond it.**

Every result in this project falls out of that shape, which is why it should be the report's
spine rather than one finding among many:

- Anything that changes **which** names are held pushes picks over the cliff. Composites do
  this (N7, N9), feature weights do this (N10, 0 of 42), and so do alternative signals (§3
  below). The cost is roughly the step size times the number of names displaced.
- Anything that changes **how much** of each name is held moves along the plateau. It cannot
  earn the step and cannot lose it.
- Therefore **weighting can only act through the risk side**, never the return side — and §4
  measures how much room that leaves.

### 3 · Two single-signal replacements for 12-1, screened Phase-0 style — both lose

The architectural lesson of N9/N10 is that additive composites dilute catastrophically on a
top-10-of-190 rule. The obvious response is to stay **one-dimensional**: change what the
single column measures rather than adding a second. Two candidates, both reusing
`signal.lookback`/`signal.skip` so V0's zero-fitted-parameter defence would survive intact:

- **`TS-mom`** — the t-statistic of the OLS slope of log price on time over the formation
  window. One estimator combining *how much it rose* with *how steadily*: the concept
  information discreteness carried, repackaged as a single well-posed statistic instead of a
  second additive column. Since N9/N10 showed the damage was architectural rather than
  informational, this is a genuinely different test of the same idea.
- **`VS-mom`** — momentum ÷ trailing volatility over the same window.

| candidate | ρ vs 12-1 | names shared /10 | compounded, 2021–25 |
|---|---|---|---|
| **12-1** | — | — | **+369.3%** |
| `TS-mom` | 0.832 | 3.60 | +201.4% |
| `VS-mom` | 0.973 | 7.40 | +195.9% |

**Neither is worth a ledger row, and `VS-mom` is the more informative of the two.** It ranks
the cross-section at ρ = 0.973 and shares **7.4 of 10 names**, yet gives up **173pp** —
swapping 2.6 names of ten costs nearly half the compounded return. That is a fourth
independent measurement of the cliff, after N7's swap reconciliation, N9's dilution curve
and N10's weight ladder, and it is the cleanest of the four because it holds the architecture
fixed and changes only the estimator.

`TS-mom` deserves one honest note: at ρ = 0.832 and 3.6/10 shared it *is* a distinct signal,
so this is a real test of steadiness-as-an-estimator rather than a restatement. It lost.

**Recorded as a reason not to run these as arms, not as a result about them.** A diagnostic
with no costs and no engine is not a backtest, and if either had come in *above* 12-1 the
correct response would have been to run it properly, not to believe this table.

### 4 · Inverse-volatility weighting: the room is real but small, and the reason is measurable

Weighting is the only lever §2 leaves untouched by the cliff. What it has to work with:

| | quarterly | weekly |
|---|---|---|
| trailing vol, most volatile name in the book | 64.7% | 63.1% |
| trailing vol, least volatile name | 33.6% | 32.5% |
| dispersion (median max/min) | 1.84× | 1.85× |
| Spearman(vol rank, forward return) | −0.0220 | +0.0514 |
| ex-ante book vol, 1/N | 26.3% | 25.7% |
| ex-ante book vol, inverse-vol | 25.0% | 24.4% |
| **reduction** | **−4.8%** | **−5.1%** |
| share of book variance from the noisiest name under 1/N | 15.1% | 15.4% |
| … from the quietest | 5.4% | 5.3% |

Three readings.

**1/N is not equal-risk — the risk budget runs 15.1% to 5.4%, a 2.8× spread.** That is the
textbook case for inverse-vol weighting and it is genuinely present here.

**And fixing it barely moves the book, because the ten names are highly correlated.** All ten
are momentum winners in one market; the correlation term dominates the variance and caps what
re-weighting can achieve at about **5%**. Sharpe 1.64 would become roughly 1.72 *if* return
were unchanged — and §3's argument says it will not be, since down-weighting volatility is
exactly the de-risking that a raw-PNL metric penalises (the mechanism V1 already demonstrated:
every V1 arm had lower vol and lower PNL).

**Forward return is not ordered by volatility inside the book either** (−0.022 / +0.051,
opposite signs across cadences). So inverse-vol weighting is not giving up a measured return
premium — it is trading an unmeasured one for a small, well-determined vol reduction. That is
the honest framing in both directions.

### What this argues for

**Not more signal work.** Three independent lines now say the same thing — additive
composites dilute (N9), feature weights do not rescue them (N10, 0 of 42), and the two
natural one-dimensional alternatives lose 168–173pp (§3). A fourth attempt would be
searching, not testing.

**§8 backlog items 4 and, by implication, 5 are answerable from the measurements above**
rather than from runs: there is no within-book return gradient for conviction weighting to
exploit (§1), and a sector cap — like any constraint that displaces names — pays the cliff
(§2) while reducing a variance the metric rewards (§3 of `CLAUDE.md`).

**The one arm with a defensible mechanism is inverse-vol weighting**, and it is defensible
for Sharpe, not for PNL. It requires an engine change: `backtest._target_shares` hardcodes
`value / len(names)`, so target weights would have to be threaded through `backtest.run` —
the same engine all 10,000 noise draws use, which makes it the highest-regression-risk change
available on the last day. Whether that is worth ~5% of book volatility on a metric that is
not the scored one is a judgement call, and it is recorded here as one.

---

## N12 · The universe changed under the project, and three conclusions moved with it — 2026-09-02

**What happened.** The organisers confirmed the scored universe is the index constituents
**as of today**, not point-in-time (`DECISIONS.md` A3-r). Five days of point-in-time work
stopped being the rule and became the measurement. Every headline was re-derived.

**The first thing that happened is the thing worth recording.** The mandated universe was
already in this repo — it is what the project ran on until 2026-08-28 — so the switch was
implemented as a config word over the same 283-name panel and the same 1,786-day calendar
rather than as a rollback. The regression gate was that V0 must reproduce **₹8,76,46,846**
to the rupee, the figure the ledger recorded on 2026-08-27, *before* the point-in-time
universe, the B10 exit rule and the composite existed. It did. That is the strongest
evidence in the project that the engine has not drifted under five days of edits, and it
cost one command to obtain because the artefact was in the ledger.

**Three things moved, and the pattern in how they moved is the finding.**

1. **B3 flipped back to reset**, having flipped to drift on 2026-08-28. This entry has now
   reversed **twice, in two directions, without the weighting rule changing at all**. The
   honest reading is not "reset is right" — it is that *whether trimming winners costs money
   depends on how many of your holdings were selected for having already run*. In a universe
   defined by today's membership, winners are over-represented by construction, so trimming
   them is close to free. Point-in-time, it is not. The rule is downstream of the universe,
   which is not how a weighting rule is usually discussed.

2. **The cadence peak moved back to monthly** from weekly, and the *submission* moved with
   it. `MAND-wk-drift` — the point-in-time submission — now **loses to the quarterly
   baseline** by ₹27.78 L on the mandated universe. A configuration this project selected
   and published on 28 Aug is, on the universe it will actually be scored on, worse than
   doing nothing.

3. **The risk-adjusted percentile of the winning cell is 96.01**, against V0's 62.97 at
   quarterly. This is measured, not modelled, and it is the number I would put in front of a
   panel: monthly rebalancing does not merely take more risk to earn more, it earns more per
   unit of risk. Speculation, flagged as such: re-picking more often lets the rule exit a
   name whose momentum has broken before a quarterly calendar would allow it, which trims
   the left tail without touching the right. The in-sample test that would settle it is a
   per-holding-period attribution of returns to entry rank, which was not run.

**What did not move, across two universes.** `no-id` beats `no-dd` in **6 of 6 frames on
both universes** — information discreteness is the more damaging of the two added features,
now on 12 frames rather than 6. And the ordering of the V1 arms is identical. A finding that
survives a universe change is a different kind of finding from one that does not, and this
project now has one of each.

---

## N13 · Adding smallcaps improved the universe and broke the rule — 2026-09-02

**Measured** (`DECISIONS.md` A19). Adding today's Nifty Smallcap 100 — 299 scored names
instead of 200, everything else identical:

| | equal-weight benchmark | strategy PNL |
|---|---|---|
| Two indices | +284.9% | ₹10,76,49,806 |
| + Smallcap 100 | **+307.1%** | **₹6,37,38,800** |

**The universe got better and the strategy got worse by ₹4.39 Cr.** That combination rules
out the easy explanations: it is not that smallcaps did badly, and it is not costs
(turnover barely moves).

**The mechanism, and it is one this project has already measured from the other side.**
`NOTES.md` N9 and N11 established that a top-10-of-190 rule is a knife edge — the payoff
surface is a plateau with a cliff at rank 10, so anything that perturbs which names land in
the top 10 is expensive. N9 perturbed it by diluting the *score* with uninformative columns.
A19 perturbs it by adding 100 uninformative *candidates*. Both cost roughly the same kind of
money, and for the same reason: 12-1 momentum cannot distinguish a smallcap that ran because
it is compounding from one that ran because it is small and volatile, so the added names win
the ranking on noise and displace better ones.

**Speculation, labelled.** If that reading is right, a liquidity or size floor applied
*before* ranking should recover most of the loss, because it removes the candidates whose
momentum is noisiest without touching the signal. That was not run — it adds a fitted
parameter, which is exactly what §4's zero-parameter defence exists to avoid, and the
measured answer to "should we include smallcaps" is already no.

**What this closes.** §8 backlog item 3 called a universe tilt "the largest single PNL
lever". It is a large lever, it was never measured, and it points **down**.
