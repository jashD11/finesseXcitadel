# Data Quality Report

Generated from snapshot `as_of = 2026-08-24`. Every figure below is computed by
`scripts/02_clean.py` from `data/raw/`; none is hand-entered.

## Panel

| | |
|---|---|
| Trading days (A8) | **1787** |
| Window | 2019-06-03 to 2026-08-24 |
| Names | 200 |
| Cells | 357,400 |
| Identity key (A7) | ISIN |

## Calendar (A8)

Union of days any name printed, minus days on which no name in the universe traded.
**4 days excluded** as market holidays for which Yahoo emitted a bar
with a price on 189-200 names and zero volume on every one:

`2026-01-15`, `2026-05-01`, `2026-05-28`, `2026-06-26`

All four fall inside the 2026 stress window. Two genuine Diwali Muhurat sessions
(2019-10-27, 2020-11-14) are retained: they carry real volume across 174-178 names,
and `^NSEI` omits both.

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
fabricated number. This is a known limitation affecting 2 of 200 names.

## Gaps (A9)

Interior gaps after each name's first print: **0**.
Forward-fill cap is 5 days and currently fires
**0** times. On the A8 calendar every name is contiguous
from listing; the apparent gaps seen on a union calendar were an artefact of the four
phantom days.

**28 names list after the window opens**, earliest
360ONE (2019-09-19), IRCTC (2019-10-14), SBICARD (2020-03-16), POWERINDIA (2020-03-30), MAXHEALTH (2020-08-21).
A5 delays their eligibility rather than excluding them.

## Zero-volume days (A10)

**300** name-days where a price printed but nothing traded, across
192 names. Concentrated in
PATANJALI (53), POLYCAB (6), DLF (5), ZYDUSLIFE (5).
Tradeability is screened on the **previous** day's volume, so the flag never reads
data from the day it gates.

## Stale prices (A11)

Runs of 10+ identical consecutive closes.
Names flagged: **1** — PATANJALI.
Report-only; a flagged name is not removed from eligibility.

## Extreme returns (A12)

Within the scoring window, **26** daily returns exceed
±20%, across 19 names.
These are flagged, never corrected — winsorising would edit the PNL being scored.
After the A16 corrections the remainder are genuine market events (the 2024-06-04
election crash, ADANIENT in Feb-2023, INDUSINDBK in Mar-2025) plus the two
uncorrected demergers.
