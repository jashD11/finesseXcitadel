# Report numbers — generated, never typed

Every figure below is read from `output/sweep/monthly_reset/`. Regenerate with
`python3 scripts/06_report.py`. Nothing here is hand-entered (docs/PROJECT.md §2).

## 1 · Required metrics (guidelines §7)

| Metric | Submitted strategy | V0 baseline (quarterly) |
|---|---|---|
| Absolute / total return | **1076.50%** | 876.47% |
| Annualised return (CAGR) | **63.78%** | 57.79% |
| Maximum drawdown | **-32.40%** | -32.50% |
| Sharpe ratio | **2.42** | 2.21 |
| Gain-to-loss ratio | **2.01** | 1.83 |
| Accuracy (% profitable trades) | **62.50%** | 67.39% |
| Total round trips | **168** | 92 |
| Executions (single-name fills) | **758** | 282 |
| Turnover (annualised) | **7.36×** | 3.77× |
| Transaction costs paid | **₹2,059,816** | ₹884,694 |
| Total Net PNL | **₹107,649,806** | ₹87,646,846 |
| Final portfolio value | **₹117,649,806** | ₹97,646,846 |
| Names ever held | 83 | 67 |
| Round trips per stock | 2.02 | 1.37 |

## 2 · Benchmark comparison (guidelines §8)

| | Total return | Total Net PNL |
|---|---|---|
| **Strategy** | **1076.50%** | **₹107,649,806** |
| Equal-weight universe (costed) | 280.55% | ₹28,054,515 |
| Nifty 100 index (cost-free) | 89.41% | ₹8,941,008 |

## 3 · The significance band (docs/PROJECT.md §5)

10,000 random 10-stock portfolios, same universe, same dates, same costs, same
engine. The only thing that differs is which names are held.

| | Value |
|---|---|
| Random draws | 10,000 |
| Seed | 20260824 |
| Mean random PNL | ₹24,456,551 |
| Median random PNL | ₹23,647,903 |
| σ of the band | ₹7,470,579 |
| Best random draw | ₹64,823,490 |
| **Strategy percentile** | **100.00%** |
| Draws beating the strategy | 0 of 10,000 |
| Strategy vs random mean | 11.14σ |
| Strategy annualised volatility | 31.78% |
| Random volatility (median) | 18.67% |
| **Risk-adjusted percentile** | **96.01%** |

**Both readings go in the report, whatever they say.** The raw percentile
answers 'is this better than picking 10 names at random?'. The risk-adjusted
one answers 'or did it just take more risk?' — the rule does load on
volatility, and under a raw-PNL metric that is rewarded, so the second number
is the one that says whether the selection itself is any good. Quoting only
whichever is higher would be exactly the dishonesty this band was built to
prevent.

## 5 · Could this actually be traded? (liquidity)

Every one of the 758 executions, measured against the **20-session average
daily rupee volume of that same name**, ending the session before the trade.

| | % of the name's 20-day ADV |
|---|---|
| Median trade | 0.00% |
| 90th percentile | 0.35% |
| 95th percentile | 0.74% |
| 99th percentile | 1.82% |
| Largest single trade | 20.82% |

At the final NAV a full position is ₹11,764,981. **Liquidity is not a binding
constraint at ₹1 crore of capital** — 99% of executions are under 2% of the name's
daily volume, and the single worst is a one-off. The median is near zero because
most monthly trades are small resets back to 1/10, not full entries or exits.

This is a measurement, not a claim that the strategy is frictionless: it says market
impact is negligible at this size, and says nothing about the other real-world costs
in §7.

## 6 · Out-of-sample stress window (guidelines §6)

Fresh ₹1 crore on 2026-01-01, nothing carried over. A **one-way rejection
filter** — no parameter was ever chosen by looking at it (docs/PROJECT.md §9).

| | H1 2026 |
|---|---|
| Strategy return | 7.60% |
| Strategy PNL | ₹759,692 |
| Max drawdown | -12.59% |
| Equal-weight universe | 0.17% |
| Nifty 100 index | -6.65% |
| Percentile of a fresh band | 88.88% |

