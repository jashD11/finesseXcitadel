# V1 build plan

Written 29 Aug 2026. **Closed 2 Sep 2026 — all seven phases done; V1 was measured and
rejected.** The route from the selected V0-family configuration to a V1 composite signal,
and every design decision that route requires. Kept as written rather than rewritten: it is
the plan that was followed, including to a negative result.

**How this file is used.** Phases are worked **one at a time**, each opened in plan mode.
A phase's decisions are answered *before* its code is written (`PROJECT.md` §2). When a
decision is answered it moves to `DECISIONS.md`, which stays the authoritative ledger —
this file only holds the *queue*. Nothing here is a decision that has been taken.

Decisions are numbered `D1…D16` for this document only. Where one restates an existing
open entry in `DECISIONS.md`, the original ID is given.

---

## Phases

| Phase | What happens | Decisions | Cost |
|---|---|---|---|
| ~~**0**~~ | **DONE 2026-08-29.** Feature diagnostics: all 10 candidates on all 20 quarterly rebalance dates (not ~8 — taking every date needs no sampling defence), 3,809 name-dates. `scripts/09_feature_diagnostics.py`, artefacts `output/diagnostics/`, write-up `NOTES.md` N3. | **none** | 2 s |
| ~~**1**~~ | **DONE 2026-08-30.** Feature set and definitions frozen as `DECISIONS.md` **C10–C16**. Phase 0 overturned D1, D3 and D5, and surfaced two decisions this document omitted. | D1–D5 **+2 omitted** | — |
| ~~**2**~~ | **DONE 2026-08-30.** Combination rule frozen as **C17** (scaled ranks); C3 and C9 closed, C4 and C8 `DEAD`, C5 `NON-ISSUE`. `cfg.pending()` is empty for the first time. | D6–D11 | — |
| ~~**3**~~ | **DONE 2026-08-30.** Five-arm `V1` slate and six predictions written into `PROJECT.md` §11 before any arm ran. | D12–D14 | — |
| ~~**4**~~ | **DONE 2026-08-30.** `features.py` + `05_v1.py` built, 5 arms run, no band re-run. **All five lost, −3.47σ to −5.22σ.** V1 is not adopted; `PIT-wk-drift` remains the submission. `NOTES.md` N6, `PROJECT.md` §11. | none | 4 min |
| ~~**5**~~ | **DONE 2026-08-30.** The weighting axis went further than two cells: `WGT`, 7 vectors × 6 frames = 42, all rejected. | D15–D16 | 100 s |
| ~~**6**~~ | **DONE.** 2026 filter run on every survivor; all pass. §9 held — it never selected anything. | none | — |
| ~~**7**~~ | **DONE 2026-09-02.** Configuration frozen: **`MAND-mo-reset`**, ₹10,76,49,806. See `PROJECT.md` §15. Report scaffolded in `REPORT_OUTLINE.md`. | none | — |

**This file is now closed.** It planned the route to a V1 composite; the composite was
built, measured across 46 arms and two universes, and rejected every time. The route it
describes was walked in full and the destination turned out not to be worth arriving at,
which is a result rather than a failure of the plan. `PROJECT.md` §15 carries live status.

Phase 0 runs without any answer and is a prerequisite for D1: F8's inclusion turns on a
correlation this project has not measured. It introduces no selection bias because nothing
is chosen on PNL.

---

## The feature universe

Ten things are computable from price and volume alone. Notation: `P[i](d)` = close of stock
*i* on day *d*; `r[i,τ]` = daily log return; `t` = the rebalance date; every feature is
computed from data through the close of `t−1` (B2).

| # | Feature | Formula | Concept |
|---|---|---|---|
| F1 | 12-1 total momentum | `P[i](t−21) / P[i](t−252) − 1` | trend magnitude |
| F2 | Residual momentum | `logMom[i] − β[i] × logMom[market]` | trend net of market beta |
| F3 | Beta | `cov(r[i], r[m]) / var(r[m])` | market sensitivity |
| F4 | Idiosyncratic vol | `sqrt( SUM(ε[i,τ]²) / (T−2) ) × sqrt(252)` | own-reasons wobble |
| F5 | Total realised vol (60d) | `stdev( r[i, t−60..t−1] ) × sqrt(252)` | total wobble |
| F6 | Amihud illiquidity | `(1/D) · SUM over d of |r[i,d]| / (V[i,d] · P[i,d])` | price impact per rupee |
| F7 | 20-day reversal | `P[i](t−1) / P[i](t−21) − 1` | short-horizon move |
| F8 | Drawdown from 252d peak | `P[i](t−1) / max(P[i](τ), τ in [t−252,t−1]) − 1` | path — proximity to high |
| F9 | Information discreteness | `sign(Mom[i]) × (%neg days − %pos days)` | path — how the move arrived |
| F10 | Rupee turnover (20d) | `mean( V[i,d] × P[i,d] )` | size / tradability proxy |

### Why F2, F3 and F4 come from one regression

Over the formation window (τ = t−252 … t−21, T = 231 days):

```
  r[i,τ]  =  α[i]  +  β[i] · r[m,τ]  +  ε[i,τ]
```

The slope is F3, the residual scatter is F4, the intercept gives F2. Summing over the
window, with log returns:

```
  SUM(r[i,τ])  =  T·α[i]  +  β[i] · SUM(r[m,τ])  +  SUM(ε[i,τ])
  -----------                                       -----------
  log 12-1 momentum                                 = 0 EXACTLY
```

**The trap:** the last term is a normal equation of OLS with an intercept — residuals sum
to exactly zero over the window they were estimated on. Naively "cumulating the residuals"
returns identically zero for every stock. Use the intercept instead, which rearranges to

```
  RM[i]  =  Mom[i]  −  β[i] × Mom[market]
```

— your 12-month return minus the part explained by being a β-times-leveraged bet on the
index. Exact, one regression, no extra parameter.

**Redundancy that must not be built.** `var(r[i]) ≈ β[i]²·var(r[m]) + var(ε[i])`, so total
vol is close to a deterministic function of beta and idio vol. F3, F4 and F5 in one
composite is triple-counting a single concept — the failure §6's "one per concept" rule
exists to prevent. At most one of the three.

**Why residualising is not cosmetic here.** Total momentum = β × market move + residual.
The market's 252-day move was large and positive across most of 2021–25, so total momentum
was *mechanically* loaded on beta — which is what §5 caught when it measured V0's
volatility (33.06%) as higher than all 10,000 random draws.

---

## Phase 1 decisions — what goes into the signal

### D1 · Which features are in — `ANSWERED 2026-08-30 as C10: F1 + F9 + F8`

> **Amended in place, not rewritten.** Phase 0 measured what the option list below assumed.
> **The 0.70 redundancy threshold was aimed at the wrong feature.** It is stated here for
> F8 and stated nowhere for F2. Measured: **F8 vs F1 = +0.43** (passes comfortably);
> **F2 vs F1 = +0.883**, selecting **7.8 of the same 10 names**. Option (a) was therefore
> three concepts in four weight slots — the exact failure `PROJECT.md` §6's one-per-concept
> rule exists to prevent — and the fallback in option (b) would have dropped the feature
> that passes while keeping the one that fails.
>
> The mechanism is arithmetic, so it should generalise: `RM = Mom − β·Mom[market]`
> subtracts one scalar times β, and β spans 0.196–2.244 against 12-month returns spanning
> −52% to +329%.
>
> The option actually put was a four-way choice — F1+F9+F8, F2+F9+F8, the original
> F1+F2+F9+F8, or F1+F8 — with each candidate's measured top-10 overlap against V0's own
> book (3.4, 3.0, 3.8, 3.1 of 10). **F1 + F9 + F8 was chosen.** F2 is held back as a
> single-change Phase 3 arm, which is a sharper test of the residual-momentum hypothesis
> than burying it in a composite.

- **What it affects:** which stocks get picked, at every rebalance. The largest single lever in V1.
- **Options:**
  - (a) F1 + F2 + F9 + F8 — four features, one concept each
  - (b) the same minus F8 — three features, if Phase 0 shows F8 too correlated with F1
  - (c) F1 + F2 only — the minimal version of the "residual paired with normal momentum" proposal
  - (d) something else
- **Recommendation:** (a), conditional on Phase 0 — fall back to (b) if F8's correlation with
  F1 exceeds ~0.7. The four measure genuinely different things: how much it rose, whether it
  rose for its own reasons, how steadily it rose, and where it sits versus its high.
- **What breaks if wrong:** two correlated features silently become one double-weighted
  feature, and the composite is not what the documentation says it is.

**Dropped candidates, one line each.** F5 total vol — redundant with F3+F4 and
metric-negative. F3 beta — as a positively weighted feature it is "buy the highest-beta
names," and it directly cancels F2; keep as a reported diagnostic. F4 idio vol — used as
F2's denominator under D3(b) rather than as its own column. F6 Amihud — ₹10 lakh per
position is not a liquidity constraint in this universe and A10 already screens on volume;
the illiquidity premium is largely a microcap effect. F10 turnover — a size proxy, and §7
measured that tilting large hurts (+62pp for equal-weighting away from cap weighting).
F7 reversal — a separate bet, not a refinement; see D10.

### D2 · What "the market" means in residual momentum — `ANSWERED 2026-08-30 as C11: equal-weight eligible universe`

> Phase 0 measured this as close to inert: ρ between the two proxies is **+0.934** for β,
> **+0.980** for standardised RM. The stated worry against (b) — a size bet left inside
> the residual — does not appear either: ρ(RM, rupee turnover) is +0.127 under (a) and
> +0.120 under (b). Decided on internal consistency, because the numbers do not decide it.

- **What it affects:** the beta of every stock, therefore every residual momentum score.
- **Options:** (a) equal-weight return of the point-in-time eligible universe · (b) Nifty 100
  (`^CNX100`) · (c) two factors, market + a size proxy
- **Recommendation:** (a) — the benchmark the rest of the project already measures against,
  so the residual means "beat your own eligible set," the same question the noise band asks.
  (b) is cap-weighted and §7 measured cap-weighting as itself a large return term.
- **What breaks if wrong:** under (b) the residual quietly contains a size bet, and we claim
  to have removed a market effect we only partly removed.

### D3 · Raw residual momentum, or standardised — `ANSWERED 2026-08-30 as C12: standardised`

> **The recommendation below was right and its stated reason was wrong.** Phase 0 tested
> the premise directly. The *spread* claim holds — `ρ(|raw RM|, idio vol) = +0.29`
> Spearman, **+0.44** Pearson — but it does not reach the signed ranking:
> `ρ(raw RM, idio vol) = +0.070`, and standardising **raises** it to **+0.107**. There was
> almost nothing to remove. For scale, plain F1 carries **+0.239**, three times as much, so
> the residualisation does real work on that exposure and the standardisation does not.
>
> C12 therefore stands on a **different reason**: standardised RM is the only near-Gaussian
> column in the set (excess kurtosis **0.13**, **0.21%** of name-dates beyond ±3σ, against
> **3.03** and **1.50%** raw), which keeps D6/D8 genuinely open instead of forcing the clip.
> Also note the two are not interchangeable despite ρ = 0.988 — they select **7.3 of the
> same 10 names**.

- **What it affects:** whether the residual ranking fills with high-volatility names.
- **Options:** (a) raw `RM = Mom − β × Mom[market]` · (b) standardised, `RM / (sd(ε)·sqrt(T))`
  — algebraically the t-statistic on α
- **Recommendation:** lean (b). Raw RM has a spread that scales with the stock's own
  volatility (`spread ≈ sd(ε)·sqrt(T)`), so unstandardised it swaps a beta loading for an
  idio-vol loading — half a fix. §5 already showed the headline is partly a volatility
  loading. But §3 says raw PNL *rewards* volatility, so (b) will cost PNL. Genuinely close.
- **What breaks if wrong:** under (a) we claim to have de-risked the signal and have not;
  under (b) we hand back PNL on the metric that scores.

### D4 · Beta estimation window — `ANSWERED 2026-08-30 as C13: the 231-day formation window`

> Taken on the recommendation below. Note Phase 0 did **not** measure option (b) — no
> 36-month betas were computed — so this is decided on the zero-extra-parameter argument
> and on the exact decomposition (`Mom = β·Mom[market] + T·α`, verified to 1e−9), not on
> a comparison.

- **What it affects:** stability of residual momentum between rebalances; turnover.
- **Options:** (a) the same 231-day formation window · (b) 36 months, per Blitz–Huij–Martens
- **Recommendation:** (a) — one window, zero extra parameters, and it makes residual momentum
  an exact algebraic decomposition of the momentum we already compute. (b) is more faithful
  to the paper but adds a parameter we cannot justify from our own data.
- **What breaks if wrong:** under (a) betas are noisier and residual scores jump around more
  between rebalances than they should.

### D5 · How steadiness is measured — `ANSWERED 2026-08-30 as C14: information discreteness`

> **Framed below as a choice of estimator; Phase 0 measured it as a choice of concept.**
> `ρ(F9, D5a) = −0.194` — and *negative is the agreeing direction*, because low information
> discreteness and a high fraction of positive months describe the same state. So the two
> barely agree at all.
>
> The coarseness argument for (b) is confirmed and stronger than stated: (a) realises only
> **9 distinct values** across ~190 names, leaving **95.5%** of names in a tied bucket,
> which under a rank composite contributes almost no ordering.
>
> **What this document never states, and C14 now does:** F9 enters the composite
> **negated**. Low ID is the predictive state while every other column is
> higher-is-better, and a reversed sign here is the one V1 error that leaves no trace.

- **What it affects:** the F9 column; roughly a quarter of the composite.
- **Options:** (a) fraction of the 11 monthly blocks with a positive return · (b) information
  discreteness, `sign(Mom) × (%neg days − %pos days)` (Da, Gurun & Warachka 2014)
- **Recommendation:** (b) — uses ~231 observations rather than 11, so far better determined,
  and needs no block-size parameter; (a) forces "monthly" to be chosen out of the air.
  Mechanism: investors underreact to a steady drip of news and overreact to dramatic jumps,
  so continuous information produces momentum that persists.
- **What breaks if wrong:** (a) at 11 blocks is coarse and noisy and may not clear the band on
  its own merits.

### Two Phase 1 decisions this document omitted — found 2026-08-30

Recorded here because a plan that hid two blocking decisions is a fact about the plan, and
`PROJECT.md` §2 is explicit that if it is unclear whether something counts as a decision,
it counts.

**D1b · F8's sign — `ANSWERED as C15: positive, nearer the high scores higher`.** The
feature table above lists F8 and its concept and **states no sign anywhere in this
document**. That is the same shape of ambiguity as D10/C8, which this project refuses to
resolve silently — and D1's answer has now put F8 in the composite. Chosen positive on
George & Hwang (2004), on coherence with a long-only momentum book, and on a Phase 0
measurement of our own: `ρ(F8, idio vol) = −0.28` Spearman / **−0.41** Pearson, so a
positively-signed F8 tilts *away* from the exposure §5 called V0's dominant one. The
negative reading would have admitted the reversal bet D10 already excluded, through a
different column.

**D1c · Flat days in information discreteness — `ANSWERED as C16: count as neither,
NON-ISSUE`.** `ID = sign(Mom) × (%neg − %pos)` needs a rule for a day with a return of
exactly zero, and this document defines none. Both fractions are taken over all 231 days,
so flat days dilute each equally and push a thin name toward mid-rank, which fails safe.
Recorded `NON-ISSUE` on measurement rather than assertion: against the alternative,
`ρ = +0.9997`, **9.8 of 10** names in common, largest single-name shift **3.3 percentile
points**. Flat days are 0.45% of name-days; the worst single name-date is 16.0%.

**The pattern worth noting.** Both omissions are the same kind: this document specifies
*which* features and *how they are computed*, and twice forgot to specify *how they are
read*. Phase 2's D6–D11 should be checked for the same gap before it is worked.

---

## Phase 2 decisions — how features become one number

### D6 · The combination rule *(gating — settles D8 and interacts with D10)*

- **What it affects:** everything downstream, and whether D8/C4 still needs answering at all.
- **Options:**
  - (a) **z-score composite** (what §6 currently specs):
    ```
      z[i,k]  =  (x[i,k] − mean(x[·,k])) / sd(x[·,k])      across NAMES on date t
      zc[i,k] =  clip(z[i,k], −3, +3)
      S[i]    =  SUM over k of w[k] · zc[i,k]
    ```
  - (b) **rank composite** (van der Waerden):
    ```
      q[i,k]  =  NormInv( rank[i,k] / (N+1) )              N = eligible names
      S[i]    =  SUM over k of w[k] · q[i,k]
    ```
    (plain scaled ranks `rank/(N+1)` work almost as well and explain more easily)
  - (c) **two-stage:** top *k* by plain momentum, then rank those *k* by the other features
- **Recommendation:** (b). Momentum's cross-section is severely right-skewed — a handful up
  300% while the median is up 15% — and a z-score on that compresses nearly everyone into a
  narrow band and lets the tail decide the portfolio. Ranks are immune to skew, make features
  genuinely commensurable, are robust to exactly the data defects this project keeps finding
  (a stale bar moves a rank a few places and a z-score five sigma), **and dissolve D8/C4
  entirely** — there are no outliers to clip.
- **What breaks if wrong:** under (a) the composite is effectively "momentum plus noise,"
  because the skewed feature dominates the sum regardless of the weights set.

### D7 · Compare each stock against whom — `DECISIONS.md` **C3**

- **What it affects:** whether the book tilts toward mid-caps or stays balanced across indices.
- **Options:** (a) all eligible names pooled · (b) rank within Nifty 100 and Midcap 100
  separately, then merge
- **Recommendation:** (a). §7 measured the cap tilt as worth real money (+62pp for
  equal-weighting away from cap weighting); (b) deliberately cancels it by making large-caps
  compete only with each other. Under a raw-PNL metric that gives away return for a tidiness
  nobody asked for.
- **What breaks if wrong:** (b) neutralises a measured, rewarded tilt and the book becomes
  structurally more index-like.

### D8 · Capping extreme scores — `DECISIONS.md` **C4** — *dissolves if D6 = (b)*

- **What it affects:** only applies under D6 = (a).
- **Options:** (a) clip at ±3 · (b) no cap · (c) not applicable — ranks have no outliers
- **Recommendation:** choose D6 = (b) and this ceases to exist. That is one of the strongest
  arguments for the rank route: ±3 is a number picked from the air, which §2 calls a design
  decision made in the dark.
- **What breaks if wrong:** a free parameter enters the model that cannot be justified from
  data — V1's weakest point.

### D9 · Missing inputs — `DECISIONS.md` **C5**

- **What it affects:** how many names are eligible; whether recent listings can be picked.
- **Options:** (a) any missing input ⇒ ineligible that rebalance · (b) score on available
  features and rescale weights · (c) fill with the cross-sectional median
- **Recommendation:** (a). Effectively what A10's eligibility already does for momentum, it is
  one rule, and (b)/(c) mean two stocks are ranked by different formulas — which violates the
  mandate's "same core methodology applied consistently across all 10 stocks."
- **What breaks if wrong:** (b) systematically favours names with fewer inputs, because they
  are scored on a shorter, easier list.

### D10 · Is a recent rise good or bad — `DECISIONS.md` **C8** — *dissolves if D1 excludes F7*

- **What it affects:** whether a 20-day return feature enters, and with which sign.
- **Options:** (a) leave F7 out of V1 · (b) include negatively (reversal) · (c) include
  positively (continuation)
- **Recommendation:** (a). **V0's 12-1 skip already sits out the last month, which is a
  *neutral* stance** — so adding F7 is not a refinement of the existing bet but a second,
  separate bet on short-term reversal. If we want that bet it should be its own
  pre-registered arm, judged against the band on its own. (a) closes C8 without pretending
  the ambiguity was resolved.
- **What breaks if wrong:** reversal is the most cost-sensitive and most regime-sensitive
  feature in the list; the wrong sign in a trending market is directly costly.

### D11 · Feature weights — `DECISIONS.md` **C9**

- **What it affects:** the composite score, and V1's entire defensibility.
- **Options:** (a) equal weights, fixed in `config.yaml` before any result is seen ·
  (b) overweight momentum, e.g. 0.4/0.2/0.2/0.2 · (c) fit the weights on 2021–25
- **Recommendation:** (a). V0's whole defence is zero fitted parameters and equal weights
  preserve it. (c) is disqualifying — it fits on the scoring window and the noise band could
  no longer adjudicate the result. (b) is defensible but *is* a choice made on a hunch, and
  one hand-set weight vector opens a search space of hundreds.
- **What breaks if wrong:** under (c) any result is unfalsifiable, which is what a panel
  screens for.

---

## Phase 3 decisions — how V1 gets tested

### D12 · What V1 is built on top of

- **What it affects:** whether V1's result is cleanly attributable to the signal change, and
  which noise band applies.
- **Options:** (a) quarterly + reset to 1/N — the `PIT-V0` frame, judged against the frozen
  quarterly σ of ₹50,92,127 · (b) weekly + drift — the `PIT-wk-drift` frame · (c) both
- **Recommendation:** (a) first, then re-run the winner at weekly/drift as a confirmation
  cell. Quarterly's band is the one with most confidence behind it and is the reference for
  §7's whole attribution ladder; building on weekly/drift stacks a new signal on top of a
  weighting rule whose own evidence never cleared the band (D15).
- **What breaks if wrong:** under (b) a V1 gain and a cadence gain are confounded and neither
  can be attributed.

### D13 · The rank buffer

- **What it affects:** turnover, costs, and how much the book actually changes each rebalance.
- **Options:** (a) buffer 10/20 as §6 specs · (b) no buffer, strict top 10 as V0 · (c) both as
  separate cells
- **Recommendation:** (b) for V1's first arm, then (a) as a separate pre-registered cell. The
  buffer is a *second* change; introduced alongside four new features, the result cannot be
  attributed. It is also independently interesting — N1's leading explanation for the
  out-of-sample cadence inversion is boundary churn, and the buffer is the fix that theory
  predicts.
- **What breaks if wrong:** one ledger line covering two changes, which is the failure mode
  §11 exists to prevent.

### D14 · Arm budget and pre-registration

- **What it affects:** whether V1's result is a finding or a fishing expedition.
- **Options:** (a) pre-register a fixed grid before running — e.g. 4 arms: V1 base, V1 with
  buffer, V1-alt two-stage, one weighting cell — written into §11 with predictions, as the
  `FREQ` block did · (b) run exploratorily and log honestly as we go
- **Recommendation:** (a), and small. With σ = ₹50,92,127 and a roughly normal band, about
  **1 in 40 arbitrary configurations clears +1σ by luck alone**; four pre-registered arms is
  interpretable and twenty exploratory ones is not.
  > **Corrected 2026-08-30: the "1 in 40" does not derive.** Under a normal band
  > P(z > 1) ≈ **16%**, not 2.5% — 1 in 40 is the *two*-sigma rate. Across five arms, the
  > chance that at least one clears +1σ on luck alone is therefore large, not negligible.
  > The recommendation is unaffected and the error runs in the direction that makes the arm
  > cap **more** necessary, so the cap stands and only the arithmetic is fixed. §11's
  > prediction 6 now commits in advance to reading a lone +1.0σ to +1.5σ arm as "did not
  > clearly beat the band".
  >
  > Related and separate: the band σ is the spread of *unrelated* random 10-name books,
  > while two arms sharing a universe, a signal family and most holdings have a much tighter
  > spread between them. 1σ is therefore a **conservative** bar for a variant-vs-V0
  > comparison rather than a calibrated one — see `NOTES.md` N5.
- **What breaks if wrong:** under (b) we will find something above one sigma and will not be
  able to say whether it is real.

**The bar to clear:** ₹50,92,127 on top of `PIT-wk-drift`'s ₹4.86 Cr — about **5 percentage
points of total return** over five years. Achievable for a real signal improvement; not
achievable by rearranging weights.

---

## Phase 5 decisions — weighting

### D15 · Reopen B3

- **What it affects:** the frame every subsequent test sits on, and the honesty of the ledger.
- **Options:** (a) reopen as `UNDETERMINED`, use reset-to-1/N as the reference frame on
  grounds of simplicity · (b) leave it resolved in favour of drift · (c) reopen and test it
  properly with more arms
- **Recommendation:** (a). B3 has been resolved twice in opposite directions on evidence that
  never cleared the band: the drift-minus-reset gaps were ₹4.91 L, ₹14.34 L, ₹29.00 L,
  ₹6.93 L — **+0.10, +0.28, +0.57, +0.14 σ** against a bar of 1.0. The finding is not "drift
  wins" or "reset wins" but that **the weighting axis does not move the number by enough to
  measure**, which is a clean result and a good report paragraph. `PIT-wk-drift` can still be
  the submission; we would only stop claiming drift was *chosen* on evidence. See `NOTES.md`
  N2.
- **What breaks if wrong:** under (b) the report states a conclusion the project's own
  methodology contradicts — precisely what a panel probes.

### D16 · Whether to test weighting at all

- **What it affects:** two ledger lines and ~20 minutes of compute.
- **Options:** (a) two cells — inverse-volatility and rank-weight, both against 1/N — then
  stop regardless of result · (b) skip the axis, citing B3's sub-band gaps · (c) more schemes
- **Recommendation:** (a), expecting both inside the band. Inverse-vol on ten momentum names
  with vols spanning 25%–55% moves weights from a flat 10% to roughly 6%–14%: a *smaller*
  perturbation than five years of drift already produced, and drift did not clear the bar.
  Reinforced by §7 — going from ~190 equally weighted names to 10 was worth **−10pp**, so
  redistributing weight among the surviving ten is a smaller lever still. Two cells buys a
  defensible negative: *we tested the weighting axis properly and it does not matter.*
- **Caution:** if D3 = (b), do **not** also run inverse-vol. Standardised residual momentum
  and inverse-vol weighting remove the same exposure through different channels; doing both
  double-doses it for no extra robustness. Prefer the signal channel, because a signal change
  is attributable through the band while a weighting change is confounded.
- **What breaks if wrong:** (c) burns D14's arm budget on the axis with the most evidence of
  being inert.

**Weighting schemes considered.**

| Scheme | Formula | Verdict |
|---|---|---|
| Equal (1/N) | `w[i] = 1/10` | the right default — hard to beat at 10 names, zero estimation error |
| Inverse-vol | `w[i] = (1/σ[i]) / SUM over j of (1/σ[j])` | test once; expect inside the band |
| Rank weight | `w[i] ∝ (N + 1 − rank[i])` | cleanest *conviction* test — 18% down to 1.8%, scale-free, no free parameter |
| Score weight | `w[i] ∝ S[i]` | scale-dependent, unstable near zero; rank weight dominates it |
| Market cap | `w[i] ∝ mcap[i]` | **no** — §7 measured equal-weighting beat cap-weighting by +62pp |
| Beta weight | `w[i] ∝ β[i]` | the metric-optimal extreme stated crudely; name it in the report, do not submit it |
| True risk parity | solve `w[i]·(COV·w)[i] = w[j]·(COV·w)[j]` | **no** — 45 correlations from ≤252 days on a book that re-picks weekly; DeMiguel–Garlappi–Uppal |

**Inverse-vol is not risk parity.** They coincide only when all pairwise correlations are
equal — the assumption a momentum book, which clusters in sectors, most reliably violates.

---

## Decision index

| ID | Phase | Name | `DECISIONS.md` |
|---|---|---|---|
| D1 | 1 | Feature set | **closed as C10** |
| D1b | 1 | **F8's sign** — omitted from this plan | **closed as C15** |
| D1c | 1 | **Flat days in ID** — omitted from this plan | **closed as C16** (`NON-ISSUE`) |
| D2 | 1 | Residualisation benchmark | **closed as C11** |
| D3 | 1 | Residual momentum: raw or standardised | **closed as C12** |
| D4 | 1 | Beta estimation window | **closed as C13** |
| D5 | 1 | Consistency feature definition | **closed as C14** |
| D6 | 2 | Combination rule | new (gating) |
| D7 | 2 | Ranking population | **C3** |
| D8 | 2 | Capping extreme scores | **C4** — dissolves if D6 = (b) |
| D9 | 2 | Missing input policy | **C5** |
| D10 | 2 | Reversal sign | **C8** — dissolves if D1 excludes F7 |
| D11 | 2 | Feature weights | **C9** |
| D12 | 3 | V1 base configuration | new |
| D13 | 3 | Rank buffer | new (§6 specs it) |
| D14 | 3 | Arm budget / pre-registration | new |
| D15 | 5 | B3 status | **B3** |
| D16 | 5 | Weighting axis scope | new |

Answering D1–D16 on the recommendations above closes C3, C4, C5, C8 and C9 — the five
entries that currently block V1 — and moves B3, the entry that has been resolved twice in
opposite directions.

*Updated 2026-08-30.* Phase 1 is closed and added **seven** new ledger entries (C10–C16),
not five: two of its decisions were missing from this document entirely. The five entries
listed above are still open and are Phase 2's work. C8 no longer has a live question — C10
excludes F7 — but is deliberately left `OPEN` until D10 closes it in Phase 2, rather than
being closed as a side effect of a decision about a different feature.
