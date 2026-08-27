# Data Quality Report

Generated from snapshot `as_of = 2026-08-28`. Every figure below is computed by
`scripts/02_clean.py` from `data/raw/`; none is hand-entered.

## Panel

| | |
|---|---|
| Trading days (A8) | **1786** |
| Window | 2019-06-03 to 2026-08-24 |
| Names | 283 |
| Cells | 505,438 |
| Identity key (A7) | ISIN |

## Calendar (A8)

Union of days any name printed, minus days that are not trading sessions.
**5 days excluded** by two separate routes, reported separately because
they rest on different evidence.

**Route 1 — the volume filter (4 days).** Yahoo emitted a bar with a
price on 189-200 names and zero volume on every one:

`2026-01-15`, `2026-05-01`, `2026-05-28`, `2026-06-26`

All four fall inside the 2026 stress window. Two genuine Diwali Muhurat sessions
(2019-10-27, 2020-11-14) are retained: they carry real volume across 174-178 names,
and `^NSEI` omits both.

**Route 2 — hand-excluded on evidence (1 day).** The volume filter
keeps these, because "at least one name traded" is satisfied, but they are not sessions.
Listed in `data/phantom_days.csv` with the evidence per row; a row acts
only when `applied` is true.

- `2025-03-18` — **stale_bar**. 193 price rows but 191 closes identical to 2025-03-17; open == prior close for the same 191; median cross-sectional return exactly 0.0000%; only 2 of 193 names recorded any volume (14.3M vs a normal ~1.3bn). Next session's median move is 3.38%, i.e. two days of return in one. A8's volume filter passes it because 'at least one name traded' is satisfied by two.

This route exists because A8's rule is stated as *at least one* name trading, and a
stale bar can clear that bar with two. The threshold was not loosened into a
participation fraction — see `DECISIONS.md` A8. **The cost of that choice, stated
plainly: the next such bar is caught only if someone looks.** `A11` below (10+ identical
closes) is the tripwire most likely to catch one.

## Corporate actions (A12, A16)

**3 corrections applied**, each confirmed by NSE's corporate-action
record *and* by the NSE-vs-Yahoo close ratio measured on three or more dates:

| symbol | action | ex_date | ratio | boundary_date |
|---|---|---|---|---|
| MOTILALOFS | Bonus 3:1 | 2024-06-10 | 4.0 | 2024-01-01 |
| CONCOR | Bonus 1:4 | 2025-07-04 | 1.25 | 2025-01-01 |
| TRENT | Bonus 1:2 | 2026-06-04 | 1.5 | 2026-01-01 |

The defect is systematic: Yahoo back-adjusts only from 1 January of the action's
year, leaving earlier history at the pre-bonus level. All 79 recorded splits across
61 names were swept; only these three are affected.

**2 confirmed actions deliberately NOT corrected:**

| symbol | action | ex_date | note |
|---|---|---|---|
| TMPV | Demerger | 2025-10-14 | observed -40.2%. Holder received the demerged entity; no published adjustment ratio, so left uncorrected and disclosed |
| VEDL | Demerger | 2026-04-30 | observed -64.9%, inside the 2026 stress window. No published adjustment ratio; left uncorrected and disclosed |

For these, Yahoo's close matches the exchange exactly, so the traded price genuinely
fell — the holder received shares in the demerged entity. Back-adjusting would need
an entitlement ratio NSE does not publish in this feed, and inventing one would be a
fabricated number. This is a known limitation affecting 2 of 283 names.

## Gaps (A9)

Interior gaps after each name's first print: **0**.
Forward-fill cap is 5 days and currently fires
**1** times. On the A8 calendar every name is contiguous
from listing; the apparent gaps seen on a union calendar were an artefact of the four
phantom days.

**46 names list after the window opens**, earliest
INDIAMART (2019-07-04), 360ONE (2019-09-19), IRCTC (2019-10-14), FLUOROCHEM (2019-10-16), SBICARD (2020-03-16).
A5 delays their eligibility rather than excluding them.

## Zero-volume days (A10)

**865** name-days where a price printed but nothing traded, across
53 names. Concentrated in
FRETAIL (725), PATANJALI (52), POLYCAB (5), UBL (5).
Tradeability is screened on the **previous** day's volume, so the flag never reads
data from the day it gates.

## Stale prices (A11)

Runs of 10+ identical consecutive closes.
Names flagged: **2** — PATANJALI, FRETAIL.
Report-only; a flagged name is not removed from eligibility.

## Extreme returns (A12)

Within the scoring window, **35** daily returns exceed
±20%, across 26 names.
These are flagged, never corrected — winsorising would edit the PNL being scored.
After the A16 corrections the remainder are genuine market events (the 2024-06-04
election crash, ADANIENT in Feb-2023, INDUSINDBK in Mar-2025) plus the two
uncorrected demergers.
