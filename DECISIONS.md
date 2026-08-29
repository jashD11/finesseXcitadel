# Decisions

Every choice where a reasonable person could have picked differently and the numbers
would have changed. **59 decisions: 51 frozen, 1 resolved on evidence, 3 dead,
4 non-issues, and — for the first time in this project — none open.** They appear below as
58 entries — A5 and C6 are two entries for one question, and D6/D7/D8 is one entry covering
three.

*Recounted 2026-08-30, twice.* The tally before Phase 1 read "50 decisions ... 48 entries,
1 under trial, 6 still open" and was stale in three places at once: there were 50 entries
not 48, B3 stopped being under trial when it resolved on 28 Aug, and only five entries were
`OPEN`. Counted directly from the headings rather than incremented, then again after Phase 2
closed the last five.

**Nothing being open is a statement about the ledger, not about the strategy.** C4 and C8
are `DEAD` because the questions ceased to exist rather than because they were answered, and
each says so in place. `NOTES.md` N2 separately records that B3 was resolved twice in
opposite directions on evidence that never cleared the project's own significance bar.

Fourteen were closed on 24 Aug 2026: six answered directly, four settled by the
organisers' guidelines document, four signed off with the V0 implementation plan. Where
the guidelines settle a question it is cited, because that is not our choice to make.

Each one is written in plain language: what the question is, what we chose, and why.
Nothing here was decided by default — an open decision is a `null` in `config.yaml`,
and the code raises an error naming the decision rather than guessing.

**Status key** — `FROZEN` decided and locked · `PROVISIONAL` decided but explicitly
revisitable · `UNDER TRIAL` both options being measured, ledger decides · `OPEN` not yet
decided, blocks code · `DEAD` no longer applies · `NON-ISSUE` checked and there is nothing
to decide.

Two decisions were amended on 27 Aug 2026 because they turned out to be **wrong, not just
incomplete**: B1 claimed any cadence was a one-word config change (false below monthly),
and B9 claimed fewer than 10 eligible names could not happen (false on one date). Both
corrections are recorded in place rather than by editing the original claim away.

---

# Mandate corrections

Not decisions — places where this repo had recorded the brief wrongly, found by reading
the organisers' guidelines document on 24 Aug 2026.

**The deliverable is not an Excel workbook.** §9 and the §11 checklist require a **GitHub
repository** plus a **5-6 page report**. Excel is never mentioned. `src/excel.py` is
therefore not built for V0; the backtest writes CSV artefacts to `output/` instead, and
the report structure stays undecided until the strategy settles.

**The deadline is 31 August**, stated twice in the guidelines. This repo had recorded 30.

**Two required metrics were missing** from our list: absolute/total return, and turnover
(§7 asks for "total number of trades, trades per stock, turnover").

**Two permissions we had not registered:** Smallcap 100 is explicitly allowed (we still
exclude it by choice), and a book of *fewer* than 10 names is allowed — "10 is the
maximum, not a requirement".

---

# A · Data and universe

*All 16 resolved.*

### A1 · Where do the prices come from? `FROZEN`
**Yahoo Finance, downloaded fresh.** All 200 stocks are available there, and one
download covers the whole period including 2026.

The alternative was a set of exchange files already on this machine. Rejected because
they stop at 30 June 2025 — missing six months of the scoring window and all of the
stress window.

*Caveat, measured:* Yahoo is not flawless. See A16 — three stocks needed correcting.
A1 stands on **coverage**, not on quality.

### A2 · Do we count dividends? `FROZEN`
**No. Price only.** We use the closing price and ignore dividends entirely.

Measured: over five years the typical stock returned +173.8% on price alone and
+198.3% with dividends — a gap of about **9 percentage points**. But the ranking barely
moves (rank correlation 0.99, and 9 of the same top 10). So including dividends would
raise the number without changing which stocks we pick.

Two reasons this is the better choice anyway: Yahoo's dividend-adjusted series has some
wild values (one stock differs by +394 percentage points, which is not a dividend), and
the Nifty indices we compare against are themselves price-only — so we're comparing
like with like.

*We must disclose in the Excel that our profit figure understates a dividend-reinvesting
portfolio by roughly 9pp.*

### A3 · Which stocks are in the universe, and as of when? `AMENDED 2026-08-28`
**Point-in-time membership: whichever stocks were actually in Nifty 100 or Nifty Midcap
100 on the day we rebalance.** See A17 for how that was rebuilt.

This entry used to read *"today's Nifty 100 + Nifty Midcap 100 lists, frozen at download
time"*, justified by the claim that **"no free 2021 membership list exists"**. That claim
was false, and it was never checked. NSE publishes every index change as a dated press
release at a stable URL; 11 semi-annual reviews cover the scoring window.

The concession mattered far more than the entry assumed. Measured, same rule, same dates,
same engine, only the permitted list differing:

| Universe | Total Net PNL | Total return |
|---|---|---|
| Today's 200 constituents | ₹8,76,46,846 | +876.5% |
| **Point-in-time membership** | **₹3,88,03,708** | **+388.0%** |

**Index-inclusion bias was worth 488 percentage points — more than half the old headline.**
The equal-weight benchmark moves with it (+284.9% to +151.6%), so the strategy's edge over
its own universe falls from +592pp to +236pp. It is still large, and the noise band still
says it is not luck, but the old number was over half artefact.

Kept for comparison rather than deleted: the old universe remains runnable and both sets of
figures are reported side by side. That gap *is* the measurement this entry originally
promised, done properly.

### A4 · Do the two index lists overlap? `NON-ISSUE`
Checked: they don't. 200 stocks, 200 unique IDs, no duplicates. There was nothing to
decide. Asserted in code so a future index reshuffle can't silently shrink the universe.

### A5 · What about stocks that listed after 2021? `FROZEN`
**A stock can't be picked until it has a full year of price history.**

26 of the 200 listed after the start. This rule *delays* them rather than excluding
them — a stock that listed in October 2020 becomes eligible around October 2021 and
takes part for most of the period.

Measured: this cohort is a barbell, not a systematic drag. Some were huge winners
(+2154%, +1301%), some were losers (−28%, −17%), and only 2 of the 26 would have made
the universe-wide top 20 anyway.

### A6 · What about stocks that were delisted or taken over? `NON-ISSUE (re-verified 2026-08-28)`
Under A3's original today's-only universe this was trivially true, and the entry said so:
"that's not clean data, that's **the bias in A3 showing up**".

Re-checked once A17 added 89 historical members: **none of the 83 we can price stops
trading inside the window.** Delistings genuinely do not occur here, so the case still
needs no handler. Six historical members have no usable Yahoo series at all (DHANI, GSPL,
HDFC, ISEC, MINDTREE, PEL) — two of those merged into acquirers. They are excluded from
the tradeable universe and disclosed, which reintroduces a sliver of the very bias A3
removes. Stated rather than buried: if one of the six would have ranked top-10 at some
rebalance, we skipped a pick and cannot know it.

### A7 · Names or ID numbers? `FROZEN`
**ISIN internally, ticker for display.** Tickers get renamed — Zomato became ETERNAL and
is in our universe right now. ISIN never changes.

### A8 · Which days count as trading days? `FROZEN`
**Every day at least one stock actually traded, minus days hand-excluded on evidence.
1,786 days.**

This one mattered more than expected. Yahoo emits price bars on **four market holidays**
— 15 Jan, 1 May, 28 May and 26 Jun 2026 — where 189–200 stocks all show a price and
*every single one* has zero volume. All four fall inside the 2026 stress window.

Filtering on volume removes all four fakes while keeping the two genuine Diwali Muhurat
sessions (a Sunday and a Saturday, both with real trading). Using Yahoo's Nifty 50 dates
instead would have thrown away both real sessions; using the Nifty 100 dates would have
thrown away nine.

**Rider, 27 Aug 2026 — one stale bar the volume filter does not catch.** The rule above is
"at least *one* stock traded". `2025-03-18` clears that bar by a margin of two: it carries
prices for 193 names, of which **191 have a close identical to `2025-03-17`**, with
`open == prior close` for the same 191 and a median return of exactly `0.0000%`. Total
volume across the universe is 14.3 M against a normal ~1.3 bn, concentrated in 2 names.
The next session moves 3.38% at the median — two days of return compressed into one.

It is a stale Yahoo bar, not a trading session. It never surfaced before because no
quarterly rebalance falls in March; it surfaces the moment any cadence evaluates every
trading day, via A10 (which reads yesterday's volume) and the B9 assertion.

**Handled as an explicit blacklist, not by loosening A8.** `clean.phantom_day_overrides`
names a file of dates excluded by hand, with the evidence recorded per row, and
`data_quality.md` reports them separately from the volume-filtered days.

The alternative was to restate A8 as a *participation threshold* — drop a day where fewer
than some fraction of the universe traded. It was rejected for now on the grounds that the
threshold would be a fitted number with exactly one observation to fit it against, and A8
is frozen on a rule that is currently correct for 1,786 of 1,787 days. A blacklist makes
the exception visible and countable; a threshold would silently reclassify days nobody has
looked at. The cost is stated plainly: **the next such bar is caught only if someone
looks.** `A11` (10+ identical closes) is the tripwire most likely to catch it, and the
quality report now carries a cross-universe staleness line for the same reason.

### A9 · What if a stock we hold has no price that day? `FROZEN`
**Carry yesterday's price forward, for at most 5 days. Never backwards.**

Filling backwards would put a future price into a past cell — that's cheating, and there
is a test that greps the whole codebase to prove we never do it.

In practice this rule **never fires**: on the A8 calendar every stock has an unbroken
series from its first day. It's a tripwire, not a routine.

### A10 · A stock shows a price but nobody traded. Can we buy it? `FROZEN`
**No — and we check yesterday's volume, not today's.**

Holding through a dead day is fine. *Buying* on one is a trade that couldn't have
happened. We check yesterday because we buy at the morning open, and looking at today's
full-day volume before deciding would be seeing the future.

Measured: **109** such days across the panel, 53 of them one stock (PATANJALI).
*(Was 300 before the A8 rider. 191 of those were the `2025-03-18` stale bar alone — the same defect, counted from the other side.)*

### A11 · A stock's price hasn't moved in days. Is it broken? `FROZEN`
**Flag 10 or more identical closes in a row. Report it, don't act on it.**

Measured: 1,826 runs of repeated prices exist, but 1,748 are just two days long —
completely normal. Exactly one is real: **PATANJALI, 52 identical closes**, a genuine
suspension. A stricter threshold would wrongly flag cheap stocks like IDEA and YESBANK
whose prices repeat simply because they're low.

### A12 · What about enormous one-day moves? `FROZEN`
**Flag anything above ±20%. Never smooth it, never delete it.**

Smoothing a return would edit the profit figure we're being scored on.

The flag earns its keep: 30 moves exceed ±20% inside the window and **none** was
recorded by Yahoo as a stock split. Sorting them by whether the whole market moved that
day cleanly separates real events (the 4 June 2024 election crash — 107 stocks moved
>5%, index −5.9%) from single-stock oddities on quiet days. The oddities turned out to
be five corporate actions. See A16.

### A13 · Should we skip stocks that barely trade? `FROZEN`
**No floor needed.** Our position size is ₹0.10 crore. The *thinnest* stock in the
universe trades ₹3.31 crore a day — **33 times our position**. Not one stock falls below
even 5× a position. A floor would exclude nothing while adding a knob to tune.

### A14 · Can we re-download the data? `FROZEN`
**No. Downloads are stamped with a date and are permanently frozen.** The code refuses
to overwrite one.

Yahoo quietly revises history. Without pinning, a result from today couldn't be
reproduced tomorrow and nothing would record that the inputs had moved.

### A15 · How far back do we download? `FROZEN`
**1 June 2019.** That gives a full year of history before the first trade in January
2021, plus buffer for holidays.

### A16 · Corporate actions Yahoo got wrong `FROZEN`
**Keep a small correction table where every row cites its source. Correct only what an
outside record confirms.** A price drop is never proof of its own cause.

We checked **all 79 stock splits across 61 stocks**. Three are broken, and the pattern is
systematic — **Yahoo adjusts history only back to 1 January of the split's year**, leaving
everything earlier at the old price level:

| Stock | What happened | Effect before fixing | After fixing |
|---|---|---|---|
| MOTILALOFS | Bonus 3:1, June 2024 | fake **−74.6%** drop | +1.55% |
| CONCOR | Bonus 1:4, July 2025 | fake −20.9% drop | −1.10% |
| TRENT | Bonus 1:2, June 2026 | fake −33.0% drop | +0.43% |

Each ratio is confirmed twice: by NSE's own corporate-action record, and by comparing
Yahoo against exchange closing prices on several dates, which match to four decimals.
The corrected MOTILALOFS figure (+1.55%) matches what the stock actually did that day.

**Two more are confirmed but deliberately left alone:**

| Stock | What happened | Left as |
|---|---|---|
| TMPV (Tata Motors) | Demerger, Oct 2025 | −40.2% |
| VEDL (Vedanta) | Demerger, Apr 2026 | −64.9% |

Here Yahoo matches the exchange **exactly** — the traded price really did fall, because
shareholders received shares in the spun-off company instead. Adjusting for that needs a
ratio NSE doesn't publish, and inventing one would be making up a number. Both are
flagged and disclosed.

> **Open risk, now measured (2026-08-24):** if the book ever held TMPV or VEDL through
> those dates it would take a loss the real holder didn't suffer. Checked against every
> book V0 actually held: **TMPV appears once, in Q2 2021** — four years before its Oct-2025
> demerger — and **VEDL never**. The stress-window book holds neither, nor TRENT. So the
> risk did not materialise for V0. It is *not* closed in general: any future variant that
> holds either name across those dates must re-run this check.

**Rider exercised 2026-08-27 — and it fired.** The `FREQ` grid (CLAUDE.md §11) added seven
variants, and the standing re-check found that **weekly and daily rebalancing both hold
VEDL across its 2026-04-30 demerger**, at roughly a 10% book weight, for a phantom loss of
**6.2–6.8% of NAV** in the stress window. Quarterly and monthly hold no flagged name across
an ex-date and remain clean.

This is the rider doing the job it was written for. Those two arms report H1-2026 returns of
+1.6% and +2.1% against monthly's +7.6%, and without the check that gap would have been
reported as evidence that fast rebalancing is fragile. Almost all of it is one uncorrected
corporate action.

No selection depends on it — the demerger falls outside the 2021–25 window that selects, and
§9 forbids choosing on 2026 regardless — so the four affected ledger rows are annotated
rather than restated, and the arms keep their `pass`.

---

# B · Mechanics — dates, trading, accounting

### A17 · Where does historical index membership come from? `FROZEN 2026-08-28`
**NSE's own index-review press releases, rebuilt by rolling today's published list
backwards — and the roll-back checks itself.**

NSE announces every index change in a dated PDF at
`niftyindices.com/Press_Release/ind_prs{DDMMYYYY}.pdf`. Sweeping every weekday from 2019 to
2026 found 976 documents, of which **27 change Nifty 100 or Nifty Midcap 100**, yielding
**43 change records** across the window.

The reconstruction runs *backwards* from today's list, and that is what makes it
verifiable rather than merely plausible. At each step three things must hold: every
`included` name must already be present, every `excluded` name must be absent, and the list
must stay at exactly 100. A missed or misparsed release breaks one of them at once. The
walk completes in **28 states**, and at the window edge lands on **Nifty 100 = 100,
Midcap 100 = 99, overlap = 0**.

Every quirk below was found by an invariant failing, not by reading ahead:

- The `Sr. No. Company Name Symbol` table header **repeats mid-list** wherever a table
  crosses a page break, so it must be deleted everywhere rather than split on.
- A ticker is the **last all-caps token containing a letter**. Footnote prose
  ("*Excluded on account of exclusion from Nifty Midcap 150 index") otherwise ends the
  entry on the bare number `150`, which is silently taken as the symbol.
- Some changes are later **revoked**, usually with a substitute named in the same
  differently-formatted release (IREDA out, BSE in, March 2024). Those documents are not
  parsed; they are recorded as evidence-carrying rows.

**Three names are waived, by name, with the search recorded.** MRF, BANKBARODA and
NATIONALUM demonstrably swap between the two indices in March 2021, and no release
returning them exists in any of the 976 documents. The membership checks are waived for
those three; the size invariant is not, and its only slack is the number of waived names in
that same record — a fixed tolerance would be exactly the fallback rule B9 refuses. The
practical impact is nil: all three stay inside Nifty 100 ∪ Midcap 100 throughout, and the
union is the only thing eligibility reads.

The walk stops at the window edge. Membership is read only on rebalance dates, the first
of which is the first trading day of the window, so reconstructing further back buys
nothing — while the 2019–20 releases carry defects (the bank mergers, the ALKEM/LTI
reshuffle) whose repair would be pure cost.

*Rider to A7:* a name that left the index has no ISIN we can source, so those 83 carry a
synthetic stable key. It cannot collide with a real ISIN and is never displayed.

### A18 · A stock we own leaves the index mid-quarter. What happens? `FROZEN 2026-08-28`
**Sell it on the effective date and hold the cash to the next rebalance.** Same mechanism
as B10 (`src/events.py`), and the noise band applies it identically.

Causal: NSE announces a review about five weeks before it takes effect, so an investor
standing on that morning already knows. The alternative — hold the name until the next
scheduled rebalance, where it simply fails eligibility — costs nothing to implement and was
the other serious candidate. Selling was chosen because it makes one claim true without
qualification: **the book never holds a stock outside the universe the mandate names.**

**The cost, stated rather than discovered.** Stocks are usually dropped from an index
because they *fell*, so selling on the effective date harvests part of a known
index-deletion effect. That is a second signal riding alongside momentum, and §1 asks for
one methodology applied consistently. It is disclosed, and the alternative rule remains a
config switch so the sensitivity can be measured rather than argued about.

### B1 · When do we rebalance? `FROZEN`
**Quarterly — the first trading day of January, April, July and October.** 20 rebalance
dates over the scoring window.

Two reasons beyond "easy to explain". The first rebalance lands on the first trading day
of 2021, which *is* the start of the mandated window — so B7 stops being a separate
question. And quarter boundaries need no defending, where a fixed 63-day spacing drifts
onto arbitrary dates over five years.

Not locked as the only frequency ever tested. CLAUDE.md §7 says holding period is one of
the two levers that actually move the number, so alternative cadences are queued as
backlog trials. Each alternative cadence gets its own ledger line.

**Amended 27 Aug 2026 — the "one-word change" claim was false below monthly.** This entry
used to say the frequency is "a **config word**, dispatched through an anchor-month map,
so a trial is a one-word change and not a code path." That holds for monthly, semi-annual
and annual, which are all anchored to a month boundary. It does not hold for **weekly or
daily**, which have no representation in an anchor-*month* map at all — `_ANCHOR_MONTHS`
maps a cadence to a tuple of months and `rebalance_dates` loops `for year: for month:`.
The claim was written when only month-anchored cadences were contemplated and was not
re-checked when the frequency sweep was proposed.

The fix keeps the spirit and drops the overreach. The dispatch now has **two anchor
families plus one literal**:

| Name | Anchor |
|---|---|
| `monthly` / `quarterly` / `semiannual` / `annual` `_first_trading_day` | first trading day on or after the 1st of each anchor month |
| `weekly_first_trading_day` | first trading day of each ISO week |
| `every_trading_day` | every trading day in the window |

The month family is **untouched**, so quarterly resolves to the identical 20 dates and V0
remains the baseline the ledger is measured against. Weekly keeps B1's actual load-bearing
property — a holiday moves the rebalance forward rather than dropping it. Daily is named
as a literal because `daily_first_trading_day` would be nonsense.

What this entry rejected, and still rejects, is **stride spacing** — "every N trading
days". That was rejected because "a fixed 63-day spacing drifts onto arbitrary dates over
five years", and the objection stands: stride would also move quarterly off 1 Jan / 1 Apr
/ 1 Jul / 1 Oct and break comparability with the existing V0 result. Calendar anchoring is
retained at every cadence.

### B2 · When is the signal measured, and when do we buy? `FROZEN`
**Signal uses data up to yesterday's close. We buy at this morning's open.**

This is the single most important rule for honesty. It guarantees we never rank a stock
using a price we then trade at.

There's a specific trap here: the obvious way to slice data in code (`panel.loc[:t]`)
*includes* today. There is a dedicated function and a test to prevent exactly that.

### B3 · Do we rebalance back to equal weights? `RESOLVED 2026-08-28 — drift`
**V0 keeps resetting all 10 back to 1/10 at every rebalance. Both rules are now being
measured against each other rather than assumed.**

The concern that kept this provisional: resetting means selling your winners every
rebalance, which works against momentum, the whole strategy. It was recorded in three
places so it could not quietly become permanent — flagged here, pre-registered as a trial,
and exposed as a one-line config switch rather than buried in code.

**Promoted to a trial on 27 Aug 2026, because the frequency sweep forces it.** A rebalance
does two separable jobs: it re-picks *which* names to hold, and it resets *how much* of
each. Changing the cadence changes how often **both** happen, and they pull in opposite
directions — re-picking more often chases momentum faster, resetting more often trims
winners harder. At daily cadence the reset job means trimming every winner every single
day. A one-dimensional cadence sweep at `reset_to_target: true` would therefore not be
measuring holding period; it would be measuring holding period confounded with a reset
penalty that grows with the same knob.

So the sweep is run as a **2-D grid**: 4 cadences × {reset, drift}, which separates the two
effects and absorbs the pre-registered `B3-drift` trial into the same piece of work. The
drift rule is: retained names keep their drifted share count and are not traded at all;
exits sell in full; the proceeds plus existing cash fund the entries, split equally. Book
size is fixed at 10, so `#exits == #entries` always, and the first rebalance has no
incumbents and is therefore identical to reset — a free assertion.

Config: `weighting.reset_to_target`. The key already existed and the engine ignored it;
`backtest.py` and `noise.py` are now genuinely weighting-agnostic, which CLAUDE.md §11
requires or the noise band cannot adjudicate the variant.

**Resolved 2026-08-28, and the answer reversed when the universe was fixed.**

Run on the old today's-constituents universe, the `FREQ` grid said **reset** wins at all
four cadences, and this entry was briefly closed that way — "resetting is a rebalancing
premium, not a momentum tax". Re-run on A3's point-in-time universe, **drift wins at all
four cadences**:

| cadence | drift − reset |
|---|---|
| quarterly | +₹4,91,465 |
| monthly | +₹14,34,084 |
| weekly | **+₹29,00,243** |
| daily | +₹6,93,409 |

So the original concern behind B3 — that resetting to 1/10 sells your winners and works
against momentum — **is correct after all**, and the earlier "backwards" verdict was an
artefact of a universe stuffed with names that were added *because* they had already run.
Reset trims winners; in a hindsight-selected universe there are more winners to trim, and
trimming them looked free.

Recorded rather than quietly restated: a conclusion this project published for a day was
reversed by fixing the data underneath it, not by a better argument.

### B3-r · What pays the cost under drift? `FROZEN`
**The B12 reserve multiple applies to deployable cash, not to book value.**

A rider forced by B3's drift path, recorded separately because it is a real choice. B12
sizes targets on `value × (1 − 2·rate)` where `value` is the **whole book**. Under drift
that is incoherent: taking a haircut against the whole book would require selling part of
a *retained* position to raise the reserve, which contradicts the one thing drift is
defined to do — leave retained names alone.

So under drift the same multiple applies to the cash actually being deployed:

    deployable = (cash + sell_proceeds) × (1 − 2 · rate)

This is conservative. The true requirement is roughly `1 × rate` on the buys, since the
sell-side cost has already been deducted from proceeds; reserving `2 × rate` overshoots.
That is deliberate and matches B12's stated reasoning: a single pass, explainable in one
sentence, with a guarantee that does not depend on a loop converging. The alternative —
solving `buy_notional = (cash + proceeds − sell_cost) / (1 + rate)` exactly — was rejected
for the same reason B12 rejected iterating to convergence.

### B4 · Whole shares or fractions? `FROZEN`
**Whole shares.** NSE does not trade fractions, so a backtest that buys 3.7 shares is
describing orders that could not have been placed.

The cost is that weights no longer land exactly on 1/10 and a small cash residue appears
each quarter — which is what B5 answers. That is the right trade: the alternative buys
tidier arithmetic with an unimplementable strategy.

### B5 · What happens to leftover cash? `FROZEN`
**Held uninvested, earning nothing, as its own line in the NAV.**

It is a rounding artefact of B4, not a position, and it is under 0.03% of the book. The
two alternatives — scaling the weights up to absorb it, or sweeping it into one name —
both quietly break equal weighting to hide a number too small to matter. Showing it costs
nothing and keeps the reported weights honest.

### B6 · Do we pay costs on the very first purchase? `FROZEN`
**Yes.** Settled by the guidelines rather than chosen: §4 says costs "must be included in
return calculations" and §3 says they apply "whenever relevant". Buying the opening ₹1
crore of stock is a transaction.

Skipping it would flatter profit by about ₹1 lakh — small, but it is the kind of omission
that reads as a thumb on the scale.

### B7 · When does the clock start? `FROZEN`
**₹1 crore, invested at the open of the first rebalance date.**

Largely settled by B1: with quarterly rebalancing anchored on the first trading day of
January, that date is the start of the mandated window, so there is no idle day between
"the backtest begins" and "the money is invested" to explain. Guidelines §4 — start with
the corpus and track value through time — is consistent with this and with nothing
simpler.

### B8 · How do we run the 2026 stress test? `FROZEN`
**Start fresh with ₹1 crore on the first trading day of 2026.** A separate backtest, not
a continuation — nothing carries over.

### B9 · What if fewer than 10 stocks are eligible? `FROZEN`
**We assert, and we fix the data. There is no fallback rule.**

This entry read `NON-ISSUE — can't happen. The minimum number of eligible stocks on any
date is 174.` **That was measured over quarterly rebalance dates only, and it is false in
general.** Evaluated over *every* trading day in the window, there is one date —
`2025-03-19` — where exactly **2** names are eligible.

The cause is not a market event. It is a bad bar: `2025-03-18` carries prices for 193
names of which **191 are identical to the previous close**, with `open == prior close` and
only 2 names recording any volume. A10 reads *yesterday's* volume to decide what is
tradeable today, so a stale day poisons the next day's eligible set. See the A8 rider.

The response is to correct the calendar (A8 rider), not to write a fallback. A rule that
says "if fewer than 10 are eligible, do something else" would have silently absorbed a
data defect and produced a plausible-looking number instead of an error. The assertion at
`universe.eligibility_matrix` did its job: it is what surfaced the bad bar at all.

### B10 · What if a stock we hold splits, or demerges? `FROZEN 2026-08-28`
**Splits and bonuses: handled by adjusted prices (A16). Corporate actions we cannot
model: sell the position on the last session that still trades cum entitlement, and hold
the cash to the next rebalance.** Config: `execution.corporate_action_mode:
exit_at_ex_date`; `hold_through` keeps the old behaviour, so this is a config switch and
not an engine edit.

Why it was needed. A demerger prints a price fall the holder never suffered — they
received shares in the spun-off entity that a price-only panel cannot see, and NSE
publishes no ratio to adjust it (A16). Selling before the discontinuity is the
conservative reading: we forgo whatever the spun-off entity was worth, and we give up the
final cum session's intraday move. Both err against us, which is the right direction for a
distortion we cannot measure.

**The off-by-one is the whole rule and it is easy to get silently wrong.** The ex-date's
own *open* is already ex-entitlement: VEDL closed at 773.60 on 2026-04-29 and opened at
289.50 on 2026-04-30, a −62.6% gap. Because the engine fills at opens (B2), an exit
scheduled *on* the ex-date books the entire phantom loss instead of avoiding it. Measured
on the weekly arm's stress window, which does hold VEDL across it: scheduling on the
ex-date gave +1.8%, one session earlier gave **+8.6%** — against +1.61% with no rule at
all. The first attempt looked like it worked and did almost nothing.

The band implements the identical rule (`src/events.py`, `noise._run_batch`), because a
strategy that can dump a name mid-quarter scored against a baseline that cannot would be
measuring the rule rather than the selection.

Disclosed either way: the share counts in our trade log are split-adjusted numbers, not the
raw counts a holder would have had.

### B11 · What do we do with dividend cash? `DEAD`
Nothing — A2 removed dividends from the project entirely.

### B12 · What pays the transaction cost? `FROZEN`
**Hold back a fixed reserve of 2 x 10 bps of the book, and size the targets on what is
left.**

Found while building the engine, not anticipated: B4 (whole shares), B5 (residue held)
and B6 (the opening build pays costs) are each fine alone, but together they leave the
*funding* of the cost unspecified. Splitting ₹1 crore ten ways and flooring to whole
shares left ₹7,116 of residue against a ₹10,000 build cost — the first rebalance could
not be paid for, and the engine's own assertion caught it rather than letting the book
run ₹2,884 overdrawn.

The multiple is 2 because the worst case a rebalance can present is a **full
replacement**: sell the entire book and buy a new one, so gross traded notional is twice
the book value. Reserving `2 x rate x value` makes non-negative cash a guarantee rather
than something that happens to hold on this data.

*The cost, stated plainly:* roughly **0.2% of the book sits in cash permanently**, and
under the scoring metric that is forgone PNL. The alternative considered was sizing
against the actual computed cost by iterating to convergence, which would idle only the
true cost for a single day. The fixed reserve was chosen instead: it is a single pass, it
is explainable in one sentence, and its guarantee does not depend on a loop converging.
Overdrafting was rejected outright — it is borrowing money the mandate did not give us.

---

# C · The signal

### C1 · Simple or logarithmic returns? `FROZEN`
**Simple returns.**

For V0 this genuinely cannot change anything: log is a monotonic transform of simple, so
ranking by either produces the identical top 10. The choice matters only once features are
averaged together in the V1 composite, where the scales differ.

Fixed now rather than later, and fixed to the more readable of the two, because a report
that says "12-month return" and means a log return invites a question with no interesting
answer.

### C2 · Do we count "12 months" in trading days or calendar months? `FROZEN`
**Trading days: 252 back, skipping the most recent 21.**

Trading days are the native unit here — our calendar is itself built from days on which
someone actually traded (A8), so counting in them needs no conversion. Calendar months
would make the lookback's true length vary with the holiday schedule, so different
rebalances would see different amounts of data for no reason anyone chose.

The skip sits *inside* the 252-day window rather than before it: the signal is the
return from 252 trading days ago to 21 trading days ago — 11 months of return out of a
12-month window, which is what "12 minus 1" names.

This same definition sets A5's "full year of history" for eligibility, so one number
governs both and they cannot drift apart. A name needs 252 trading days of unbroken
closes before the formation date (253 observations) before it can be ranked.

### C3 · Compare each stock against whom? `FROZEN 2026-08-30`
**All eligible stocks pooled together** — one ranking over everything eligible on the date.

**Chosen for simplicity, and the reason originally given for it is wrong.** The
recommendation that stood here read: *"Scoring within each index separately would quietly
cancel out the large-cap vs mid-cap tilt — and that tilt is worth more than the
stock-picking rule."* Measured on the frozen feature set, there is no large tilt for
within-index ranking to cancel: **the pooled top 10 is already 52% midcap**, roughly the
50/50 that ranking within each index would force. And the two rules select **9.3 of the
same 10 names**.

So pooling is taken because it is one rule instead of two, needs no per-index membership
path, and was measured not to matter — not because it protects a return term. Within-index
ranking would also lean on a split A17 records as approximate for MRF, BANKBARODA and
NATIONALUM (63 name-dates sit in both indices at once), which is a second reason to prefer
the union the eligibility gate already reads.

### C4 · Capping extreme scores `DEAD 2026-08-30`
**The question ceases to exist under C17.** Scaled ranks have no outliers to clip: the most
extreme name scores `N/(N+1)` and the least extreme `1/(N+1)`, whatever the raw values do.
There is no threshold left to choose.

**Two things are recorded separately, so the ledger does not overstate why it died.** The
question is dead *because of C17*. It was also, independently, **much smaller than this
entry assumed** — Phase 0 measured a ±3 clip as touching **2.88%** of names and changing a
z-composite's book by ~0.6 names of 10 (ρ 0.9993, 9.4/10 overlap). `PLAN.md` D8 argued that
dissolving this decision was "one of the strongest arguments for the rank route"; it was
not, and C17 rests on robustness instead.

### C5 · What if a stock is missing one input? `NON-ISSUE 2026-08-30`
**The rule is recorded — a stock missing any input sits that rebalance out** — but it
cannot fire on the frozen feature set, for a structural reason rather than a lucky one.

All three C10 features are pure functions of closes over windows that A5/C6 eligibility
already requires to be complete, so a name that is eligible necessarily has all three. Phase
0 confirms it: **zero NaN across 3,809 name-dates**, asserted rather than eyeballed.

Kept as a live config value (`missing_feature_policy: ineligible`) rather than deleted,
because it is the rule that would apply the moment a feature is added that *can* be missing
— a volume-based column, for instance, which F6 and F10 would both have been. Filling with
a cross-sectional average would rank a stock on a made-up number and would mean two stocks
were scored by different formulas, which the mandate's "same core methodology applied
consistently across all 10 stocks" forbids.

### C6 · How much history to compute a feature? `FROZEN`
Full window, same as A5.

### C7 · Two stocks tie for 10th place. Who wins? `FROZEN`
**The existing holding, then by ISIN ascending.**

Exact ties on float64 momentum scores are near-impossible, but the rule has to exist or
the backtest is not bit-reproducible — and reproducibility is a submission requirement,
not a nicety.

Incumbent-first is deliberately the same principle as V1's rank buffer, so the two rules
agree instead of pulling against each other: neither will evict a holding for a newcomer
that is merely equal. ISIN is the tie-break of last resort because it is the one
identifier that never gets renamed (A7).

### C8 · Is a recent price rise good or bad? `DEAD 2026-08-30`
Genuinely ambiguous, and I won't pick it silently. All the scores have to point the same
direction before they're averaged, but a 20-day gain reads as *positive* under momentum
and *negative* under mean-reversion. **Blocks V1.**

*2026-08-30, Phase 2:* **closed as `DEAD`, not answered.** C10 excludes F7 from the V1
feature set, so there is no longer a feature whose sign this question governs. The ambiguity
was never resolved and this entry should not be read as resolving it — if a short-horizon
reversal arm is ever wanted, C8 reopens and must be answered on its own evidence.

C15 records the related trap: signing F8 negatively would have admitted the same reversal
bet through a different column, so excluding F7 only works if F8's sign is positive.

### C9 · How much weight does each feature get? `FROZEN 2026-08-30`
**Equal — one third each — fixed in `config.yaml` before any V1 result was seen.** With
three features there is no weight vector to search, so V0's zero-fitted-parameter defence
carries into V1 intact and any V1 gain is attributable to the feature set alone.

**A second vector is pre-registered as an arm, which is not the same thing as tuning.**
`V1-tilt` uses **2 / 1 / 1** — momentum weighted as much as the other two combined —
declared in `CLAUDE.md` §11 before anything ran and **run unconditionally**, so it is one
more pre-registered configuration the noise band adjudicates, not a response to a
disappointing number. The distinction matters: choosing the tilt *after* seeing that the
equal-weight composite lost PNL would fit the scoring window and is precisely what this
entry was written to forbid. Only these two vectors are ever tried.

Both are stored as **integers** (`{1,1,1}` and `{2,1,1}`) normalised at use, so they are
exactly 1/3 each and exactly 0.5/0.25/0.25 with no floating-point constant written anywhere,
and the tilt is a statable rule rather than a number picked from the air.

Fitting the weights on 2021–25 was considered and **refused**: it fits on the scoring
window, the band could no longer adjudicate the result, and no V1 number would be
falsifiable.

### C10 · Which measurements go into the V1 score? `FROZEN 2026-08-30`
**Three: 12-month momentum (F1), information discreteness (F9), and drawdown from the
252-day peak (F8).** One measurement per concept — how much it rose, how the rise arrived,
and where it now sits against its own high.

Residual momentum (F2) was in the proposed set and is **out**. `PLAN.md` set a redundancy
threshold of 0.70 for F8 against F1 and never applied one to F2. Phase 0 measured both:
F8 comes in at **+0.43**, F2 at **+0.883** with 7.8 of the same 10 names selected. The
proposed four-measurement score was three concepts occupying four weight slots, which is
exactly what `CLAUDE.md` §6's one-per-concept rule exists to prevent.

The overlap is arithmetic rather than a property of this window: `RM = Mom − β·Mom[market]`
subtracts one scalar times β, and β's spread (0.196–2.244) is small against the spread of
12-month returns (−52% to +329%), so the subtraction cannot reorder much. Expect it to hold
in other periods.

F2 is not thereby discarded. The ~12% of ranking it does not share with F1 is the
beta-driven part, which `CLAUDE.md` §5 identified as V0's dominant exposure. It is held
back as a **single-change Phase 3 arm** — F2 swapped for F1, nothing else altered — which
is a cleaner test of the residual-momentum hypothesis than burying it inside a composite.

Dropped and why, one line each: F3 beta, F4 idiosyncratic vol and F5 total vol are one
concept in three columns (Phase 0: 0.49, 0.59, 0.75 between them). F6 Amihud and F10 rupee
turnover are near mirror images (**−0.79**), so dropping both costs one concept. F7
short-horizon reversal is a separate bet, not a refinement — see C8.

**This introduces no new numeric parameter.** F8's 252-day window *is* `signal.lookback`;
F9's window is the same `lookback`/`skip` pair F1 already uses. V1 inherits V0's
zero-fitted-parameter defence intact.

### C11 · What counts as "the market" when stripping out market movement? `FROZEN 2026-08-30`
**The equal-weight return of the point-in-time eligible universe**, not the Nifty 100 index.

It is the benchmark `CLAUDE.md` §7's attribution ladder and the noise band already measure
against, so a residual means "beat your own eligible set" — the same question §5 asks.

Phase 0 measured the choice as nearly inert: between the two proxies, ρ is **+0.934** for
β, **+0.980** for standardised residual momentum, **+0.970** for raw. The stated worry
against the index — that being cap-weighted it leaves a size bet inside the residual —
does not appear either: ρ(RM, rupee turnover) is +0.127 under the equal-weight proxy and
+0.120 under the index. Decided on internal consistency, because the numbers do not decide it.

### C12 · Residual momentum: raw, or divided by its own noise? `FROZEN 2026-08-30`
**Standardised: `RM / (sd(ε)·√T)`**, which is proportional to the t-statistic on α.

**The reason is not the one originally proposed, and the original was tested and refuted.**
The proposal argued that raw RM's spread scales with `sd(ε)`, so the raw ranking inherits an
idiosyncratic-vol loading. Phase 0: the spread claim holds (ρ(|raw RM|, idio vol) = +0.29
Spearman, **+0.44** Pearson) but it does not reach the signed ranking — ρ(raw RM, idio vol)
is **+0.070**, and standardising *raises* it to **+0.107**. There was almost nothing there
to remove. For scale, plain momentum carries **+0.239**, three times as much; the
residualisation does real work on that exposure, the standardisation does not.

The reason it is chosen instead: standardised RM is the only near-Gaussian column in the
candidate set — excess kurtosis **0.13** and **0.21%** of name-dates beyond ±3σ, against
**3.03** and **1.50%** for raw. That keeps C4's clip-or-not question genuinely open rather
than forcing a ±3 clip chosen from the air.

The two are not interchangeable despite ρ = 0.988: they select **7.3 of the same 10 names**.

### C13 · How far back is market sensitivity measured? `FROZEN 2026-08-30`
**The same 231-day formation window the momentum signal uses** (τ = t−252 … t−21), not a
separate 36-month window.

Zero extra parameters, and it makes residual momentum an *exact* algebraic decomposition of
the momentum already computed: `Mom = β·Mom[market] + T·α`, verified to 1e−9 in
`scripts/09_feature_diagnostics.py`. One window governs eligibility, F1 and β together, so
they cannot drift apart. A 36-month window is more faithful to Blitz–Huij–Martens and gives
steadier betas, but adds a parameter with no justification from our own data, lengthens the
history requirement, and breaks the exact decomposition.

### C14 · How is "rose steadily" measured? `FROZEN 2026-08-30`
**Information discreteness: `ID = sign(Mom) × (%neg days − %pos days)`** over the 231-day
formation window (Da, Gurun & Warachka 2014). Not the fraction of positive 21-day blocks.

The mechanism: momentum pays because investors underreact, and underreaction is larger when
information arrives in a steady drip too small to command attention than when it arrives in
salient jumps that are priced immediately. `sign(Mom)` makes the measure read the same for
winners and losers, so **low ID = continuous information** in both directions.

**It enters the score negated**, because low ID is the predictive state and every other
column is higher-is-better. This is the one sign error in V1 that would be invisible: a run
with F9's sign reversed completes, reconciles to the rupee, and reports plausible numbers
while buying the opposite of what was intended. The signs therefore live in `config.yaml`
where a reader can see them, not in a function body.

Phase 0 showed the two candidates are not two estimators of one concept: ρ = **−0.194**,
and *negative is the agreeing direction* because low ID and many positive months describe
the same state — so agreement is very weak. The block alternative is also far coarser: 9
distinct values across ~190 names, leaving **95.5%** of names in a tied bucket, which under
a rank-based score contributes almost no ordering. It also forces "monthly" to be chosen
with no justification, where ID uses all 231 observations and needs no block size.

F9 is close to orthogonal to both companions — ρ(F1, F9) = **−0.21**, ρ(F8, F9) = **−0.04**
— which is the strongest argument for the slot. **Disclosed:** it rests on one published
result with no in-house evidence. Phase 0 establishes it is *distinct*, not that it
*forecasts*. Keeping it means V1 carries one bet sourced from outside this project.

### C15 · Is being near the 252-day high good or bad? `FROZEN 2026-08-30`
**Good — nearer the high scores higher.** F8 = `P(t−1) / max(P over 252d) − 1`, bounded
above at 0, entering the score with a positive sign.

`PLAN.md` listed F8 in its feature table and **never stated a sign anywhere**, which is the
same shape of ambiguity C8 refuses to resolve silently. Recording it as its own decision
rather than as an implementation detail.

Positive is the documented direction (George & Hwang 2004, the 52-week-high effect, which
subsumes much of conventional momentum) and the only reading coherent with a long-only
momentum book. Phase 0 adds a reason of our own: ρ(F8, idio vol) = **−0.28** Spearman /
**−0.41** Pearson, so a positively-signed F8 tilts *away* from the high-volatility exposure
§5 identified as V0's dominant one — work the score actually wants done.

The negative reading ("buy the dip inside a winner") is coherent as a thesis, but it makes
F8 a short-horizon reversal bet, and C8 has already decided reversal stays out of V1 and
gets its own pre-registered arm if it is wanted. Signing F8 negatively would admit that bet
through a different column.

### C16 · Days a stock did not move at all `NON-ISSUE 2026-08-30`
Information discreteness counts up-days and down-days; a day with a return of exactly zero
is neither, so the treatment has to be stated. **Both `%neg` and `%pos` are fractions of all
231 days**, so flat days dilute both equally and push a thinly-traded name's score toward
zero, i.e. toward the middle of the ranking. That is the paper's own construction and it
fails safe.

Recorded as `NON-ISSUE` on measurement rather than assertion. Against the alternative
(rescaling over non-flat days only): ρ = **+0.9997**, **9.8 of 10** names in common,
largest single-name shift **3.3 percentile points**. Flat days are 0.45% of name-days
overall; 1.00% of name-dates exceed 5% flat and 0.37% exceed 10%, with a worst case of
16.0%. The two treatments are the same measurement to three decimal places.


### C17 · How do the three features become one score? `FROZEN 2026-08-30`
**Scaled ranks.** Each feature is ranked across eligible names on the rebalance date,
divided by `N+1` to put it on (0,1), and the three are averaged with the C9 weights. Never
ranked across time for one stock — the time-shuffle test in `tests/test_causality.py` pins
that down.

This is the largest V1 decision after C10: a z-score composite and a rank composite over
the same three features share only **6.6 of 10 names** (ρ +0.974). They are not
interchangeable, and note that the correlation badly understates the disagreement — see
`NOTES.md` N4.

**Why ranks.** Only one of the three columns is pathological, and under z-scoring it would
decide the book: 12-1 momentum has cross-sectional skew **+2.31**, excess kurtosis
**+11.67**, and a most-extreme name at **5.64σ**. Drawdown (−1.41 / +4.34 / 1.28) and
information discreteness (−0.11 / +0.20 / 2.72) are benign. Ranks make three
differently-scaled features genuinely commensurable and are robust to exactly the data
defects this project keeps finding — the `2025-03-18` stale bar moved a z-score by several
sigma and would move a rank by a few places.

**What ranks cost, stated plainly.** Magnitude information is discarded: a name up 300%
ranks one place above a name up 200%. That is real signal thrown away, and it is the
strongest argument for the z route.

**The argument this decision does NOT rest on.** `PLAN.md` D6 claimed ranks were worth
choosing partly because they "dissolve D8/C4 entirely — there are no outliers to clip". They
do dissolve it, but Phase 0 measured that clip as nearly inert to begin with (C4). The
saving is real and small; the robustness argument is what carries the decision.

Van der Waerden normal scores, `NormInv(rank/(N+1))`, were considered and rejected: they
share **8.3/10** names with plain scaled ranks, so they are a genuine third option rather
than a variant, but they re-introduce tail sensitivity for a transformation harder to
justify to a reader than either neighbour.

**Testable consequence, and the check that proves this landed as specified:** a rank
composite is invariant to any monotone transform of a single input feature. A z-composite
is not. `tests/` asserts it.


---

# D · Measuring the result

### D1 · What do we compare against? `FROZEN`
**Two series, reported side by side.**

**Equal-weight portfolio of the full universe**, rebalanced on our dates, through our
engine. This is the analytically useful one: it is the only comparison that separates
*stock-picking* from *tilting toward mid-caps*, and CLAUDE.md §7 says the tilt is worth
more than the selection rule. Beating this is evidence of selection skill; beating an
index is not.

**Nifty 100 (`^CNX100`)**, the mandate-facing comparison. Guidelines §8 names Nifty 100 or
Nifty 500 as examples; Nifty 500 is not in our snapshot, and CLAUDE.md §13 records that
the Yahoo midcap index series is unreliable, so Nifty 100 is the one index we can quote
without caveat.

### D2 · How do we measure luck? `FROZEN`
**10,000 random 10-stock portfolios, re-drawn at every rebalance date**, same universe,
same dates, same costs, same engine. Only the choice of stocks differs.

Because random picks contain zero skill, the spread of those 10,000 results is pure luck.
Every later change is scored against it: if a change moves profit by less than that
spread, nothing was found.

*One consequence to be honest about:* re-drawing each quarter averages out some
randomness, making the band **narrower** than a buy-and-hold version — so it sets a
**lower** bar. The ledger therefore records the raw score, not a pass/fail tick.

### D3 · How do we annualise the return? `FROZEN`
**Compound growth (CAGR) over the actual elapsed years.** Settled by the guidelines rather
than chosen: §7 asks for the "geometric average return over the test period".

Elapsed years are calendar days ÷ 365.25. The formula goes into the report verbatim next
to the number.

### D4 · Exact Sharpe formula `FROZEN`
**Annualised return ÷ (sample standard deviation of daily returns × √252), risk-free rate
zero.** Sample standard deviation means `ddof = 1`.

> **Required disclosure.** This deviates from the guidelines as literally printed. §7 says
> "Annualised Return divided by the standard deviation of daily returns" — with no √252,
> which mismatches units and inflates the ratio by roughly 16×. We report the conventional
> figure and print **both** the guideline wording and the formula actually used, so the
> deviation is visible rather than silent.

There is nothing to game here: the ranking metric is Total Net PNL, not Sharpe.

### D5 · How is maximum drawdown measured? `FROZEN`
**On daily portfolio value, after costs.** Settled by the guidelines: §7 defines MDD as
the "largest peak-to-trough decline in portfolio value", and our portfolio value is a
daily series.

Intraday lows would produce a larger, scarier number that could not be reconciled against
the NAV series we actually report — two drawdown figures in one document, neither
explaining the other.

### D6 / D7 / D8 · What counts as a "trade"? `FROZEN`
This was genuinely ambiguous — the competition asks for trade count, accuracy and
gain-to-loss ratio, but those are defined for a trade-by-trade strategy, not a
rebalancing portfolio.

**A trade is one complete round trip:** from when a stock enters the book to when it
leaves. Buying more of something we already hold is part of the same round trip.

Both accuracy measures are reported: the share of round trips that made money, **and**
the share that beat the benchmark over the same dates. Same for gain-to-loss: average
winner ÷ average loser, **and** total gains ÷ total losses.

> **Required disclosure:** raw accuracy will look impressive, but the median stock in
> this universe rose 173.8% over five years. In a market like that, almost any portfolio
> shows high accuracy. It must not be presented as skill.

### D9 · Does the benchmark pay trading costs too? `FROZEN`
**The equal-weight benchmark pays costs; the index series does not, and is labelled
cost-free.**

The equal-weight benchmark rebalances, so charging it the same 10 bps is what makes it a
like-for-like comparison. It is also the conservative choice for our own claim: a
cost-free benchmark would be easier to beat, and we would rather understate the gap.

An index level is cost-free by construction — there is no portfolio behind it to charge —
so it is reported as-is with that stated plainly.

### D10 · What about positions still open on the last day? `FROZEN`
**Valued at the final closing price and counted as closed round-trips.**

The alternative — excluding them — drops roughly 10 of the most recent trades. In a market
that rose as much as this one did, those are disproportionately winners, so excluding them
would bias accuracy and gain-to-loss *downwards* for a purely cosmetic reason.

The open ones are flagged as such in the trade table, so anyone who prefers the stricter
convention can recompute without rerunning anything.

### D11 · How do we judge whether a change is real? `FROZEN`
**Against the standard deviation of the whole random distribution.**
`z = (PNL_variant - PNL_V0) / sigma_band`.

The known objection, stated rather than hidden: a new version and the old one share most
of their holdings, so the difference between them varies *less* than either varies on its
own. Measuring that small difference against the *whole* band's spread therefore sets a
bar that is too high, and will reject some genuine but modest improvements.

That is the intended posture. A panel is more impressed by a strict test we might fail
than by a clever one that flatters us, and the alternative — a paired null that resamples
only what changed — costs a paragraph of explanation to buy statistical power we do not
need. (This paragraph used to close with "§7 shows only ~174 pp of V0's return sits in the
selection term at all". That figure was superseded when §7's attribution ladder was
corrected on 25 Aug 2026 — the selection term is **+615 pp**, not 174 pp. The argument for
the strict posture does not depend on it, but the number was wrong and is removed.)

The consequence is recorded in the ledger's own rules: `z` is written as a **number**,
never as a pass/fail tick, so nobody reads a cleared threshold as stronger evidence than
it is.

### D11-r · Which sigma, when the calendar itself is the variable? `FROZEN`
**Both. The ledger carries two `z` columns.**

Recorded 27 Aug 2026, **before the frequency sweep was run**, because the effect is
predictable from D2's construction and would look like an excuse if it were written down
afterwards.

D2 re-draws all 10 names at *every* rebalance date. That is deliberate, and D2 already
concedes it "sets a **lower** bar" than a buy-and-hold null. What D2 did not anticipate is
that **the size of that effect is a function of the rebalance cadence**, which is exactly
the variable a frequency sweep moves. Two things happen at once as cadence rises:

1. Averaging. Re-drawing 20 times averages out some luck; re-drawing 1,235 times averages
   out proportionally more, so the spread collapses.
2. Costs. A fresh draw of 10 from ~180 retains about 0.55 names, so each re-draw turns over
   ~94% of the book and pays 10 bps on it. At daily that is ~470x annual turnover.

Measured across the sweep's cadences, the band's standard deviation falls from
**Rs 86.05 lakh** (quarterly) to **Rs 8.22 lakh** (daily), and the daily band's *mean PNL
is negative* — the random book loses money paying its own commissions.

So a `z` taken against each cadence's own sigma is **not comparable down the table**: the
daily arm would post a large `z` mostly because its denominator shrank tenfold, not because
it found anything more. Reporting only that number would be the precise failure D2's
"record the raw score, not a pass/fail tick" rule exists to prevent.

The ledger therefore records:

| Column | Definition | Answers |
|---|---|---|
| `z_own` | `(PNL_arm − PNL_V0) / sigma` of a band on **that arm's own calendar and weighting** | Does this arm beat random portfolios trading at the same speed? |
| `z_qtr` | `(PNL_arm − PNL_V0) / 86,05,419` — the frozen quarterly sigma | How do the arms rank against **one fixed ruler**? |

`z_own` keeps D2 literal and is the stronger claim for any single arm. `z_qtr` is the only
one of the two that may be read *across* rows. Neither is dropped, because each answers a
question the other cannot.

---

# What's left

**6 open.** Nothing on this list blocks V0 or the noise band.

| Blocks | Decisions |
|---|---|
| The V1 composite | C3, C4, C5, C8, C9 |
| Documentation only | B10 |

One more is deliberately unresolved rather than open:

- **How weights are reported** — target, executed, or daily drifted — is deferred until
  the strategy settles, since it changes no number. The backtest emits all three, so the
  choice stays free.

**No code is written against an open decision.** Each one is a `null` in `config.yaml`;
reading it raises an error naming the decision, and the config loader refuses to start if
someone fills in a value without first recording it here.
