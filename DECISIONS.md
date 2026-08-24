# Decisions

Every choice where a reasonable person could have picked differently and the numbers
would have changed. **48 decisions: 37 frozen, 1 provisional, 1 dead, 3 non-issues,
6 still open.** They appear below as 46 entries — A5 and C6 are one question, and
D6/D7/D8 are three parts of one answer.

Fourteen were closed on 24 Aug 2026: six answered directly, four settled by the
organisers' guidelines document, four signed off with the V0 implementation plan. Where
the guidelines settle a question it is cited, because that is not our choice to make.

Each one is written in plain language: what the question is, what we chose, and why.
Nothing here was decided by default — an open decision is a `null` in `config.yaml`,
and the code raises an error naming the decision rather than guessing.

**Status key** — `FROZEN` decided and locked · `PROVISIONAL` decided but explicitly
revisitable · `OPEN` not yet decided, blocks code · `DEAD` no longer applies ·
`NON-ISSUE` checked and there is nothing to decide.

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

### A3 · Which stocks are in the universe, and as of when? `FROZEN`
**Today's Nifty 100 + Nifty Midcap 100 lists, frozen at download time.**

This is a known cheat and everybody doing this competition has it: today's index
members are partly there *because* they went up. Backtesting them from 2021 flatters
the result.

We can't fix it — no free 2021 membership list exists — so we **measure** it instead by
running the same strategy on a February 2019 membership snapshot and reporting the gap.
20 of the 101 names in that 2019 list are gone from today's universe.

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

### A6 · What about stocks that were delisted or taken over? `NON-ISSUE`
There aren't any — all 200 have data through today. But that's not clean data, that's
**the bias in A3 showing up**: we're only looking at survivors. We assert it rather than
writing a handler for a case that cannot occur.

### A7 · Names or ID numbers? `FROZEN`
**ISIN internally, ticker for display.** Tickers get renamed — Zomato became ETERNAL and
is in our universe right now. ISIN never changes.

### A8 · Which days count as trading days? `FROZEN`
**Every day at least one stock actually traded. 1,787 days.**

This one mattered more than expected. Yahoo emits price bars on **four market holidays**
— 15 Jan, 1 May, 28 May and 26 Jun 2026 — where 189–200 stocks all show a price and
*every single one* has zero volume. All four fall inside the 2026 stress window.

Filtering on volume removes all four fakes while keeping the two genuine Diwali Muhurat
sessions (a Sunday and a Saturday, both with real trading). Using Yahoo's Nifty 50 dates
instead would have thrown away both real sessions; using the Nifty 100 dates would have
thrown away nine.

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

Measured: 300 such days across the panel, 53 of them one stock (PATANJALI).

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

> **Open risk for Phase 2:** if the book ever holds TMPV or VEDL through those dates,
> the portfolio takes a loss the real holder didn't suffer. Not yet decided.

---

# B · Mechanics — dates, trading, accounting

### B1 · When do we rebalance? `FROZEN`
**Quarterly — the first trading day of January, April, July and October.** 20 rebalance
dates over the scoring window.

Two reasons beyond "easy to explain". The first rebalance lands on the first trading day
of 2021, which *is* the start of the mandated window — so B7 stops being a separate
question. And quarter boundaries need no defending, where a fixed 63-day spacing drifts
onto arbitrary dates over five years.

Not locked as the only frequency ever tested. CLAUDE.md §7 says holding period is one of
the two levers that actually move the number, so semi-annual and monthly are queued as
backlog trials. The code reflects that: the frequency is a **config word**, dispatched
through an anchor-month map, so a trial is a one-word change and not a code path. Each
alternative cadence gets its own ledger line.

### B2 · When is the signal measured, and when do we buy? `FROZEN`
**Signal uses data up to yesterday's close. We buy at this morning's open.**

This is the single most important rule for honesty. It guarantees we never rank a stock
using a price we then trade at.

There's a specific trap here: the obvious way to slice data in code (`panel.loc[:t]`)
*includes* today. There is a dedicated function and a test to prevent exactly that.

### B3 · Do we rebalance back to equal weights? `PROVISIONAL`
**For now: yes, reset all 10 back to 1/10 each quarter.** Deliberately not locked.

The concern: resetting means selling your winners every quarter. That works against
momentum, which is the whole strategy. So it's recorded in three places so it can't
quietly become permanent — flagged here, pre-registered as a trial to run, and exposed
as a one-line config switch rather than buried in code.

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

### B9 · What if fewer than 10 stocks are eligible? `NON-ISSUE`
Can't happen. The minimum number of eligible stocks on any date is **174**. We assert it
rather than writing a fallback that would never run.

### B10 · What if a stock we hold splits? `OPEN`
Recommended: handled automatically by adjusted prices, but disclosed — it means the share
counts in our trade log are adjusted numbers, not the raw counts you'd have held. A
reviewer will ask.

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

### C3 · Compare each stock against whom? `OPEN`
Recommended: all eligible stocks pooled together. Scoring within each index separately
would quietly cancel out the large-cap vs mid-cap tilt — and that tilt is worth more than
the stock-picking rule, so it must be a conscious choice, not a side effect.

### C4 · Capping extreme scores `OPEN`
Recommended: convert to a standard score first, then clip at ±3. Stops one runaway stock
from squashing all the others into a narrow band.

### C5 · What if a stock is missing one input? `OPEN`
Recommended: it sits out that quarter. Filling in an average would put a stock in the
ranking based on a made-up number.

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

### C8 · Is a recent price rise good or bad? `OPEN`
Genuinely ambiguous, and I won't pick it silently. All the scores have to point the same
direction before they're averaged, but a 20-day gain reads as *positive* under momentum
and *negative* under mean-reversion. **Blocks V1.**

### C9 · How much weight does each feature get? `OPEN`
Recommended: equal, fixed in the config before any result is seen. Tuning these weights
would destroy V1's main defence — that nothing was fitted to the data. **Blocks V1.**

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
need. We are not hunting for small effects; §7 shows only ~174 pp of V0's return sits in
the selection term at all.

The consequence is recorded in the ledger's own rules: `z` is written as a **number**,
never as a pass/fail tick, so nobody reads a cleared threshold as stronger evidence than
it is.

---

# What's left

**6 open.** Nothing on this list blocks V0 or the noise band.

| Blocks | Decisions |
|---|---|
| The V1 composite | C3, C4, C5, C8, C9 |
| Documentation only | B10 |

Two more are deliberately unresolved rather than open:

- **B3** (reset to equal weight each quarter) stands `PROVISIONAL`, with `B3-drift`
  pre-registered as a trial in CLAUDE.md §11.
- **How weights are reported** — target, executed, or daily drifted — is deferred until
  the strategy settles, since it changes no number. The backtest emits all three, so the
  choice stays free.

**No code is written against an open decision.** Each one is a `null` in `config.yaml`;
reading it raises an error naming the decision, and the config loader refuses to start if
someone fills in a value without first recording it here.
