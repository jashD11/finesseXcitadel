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
