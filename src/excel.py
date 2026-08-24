"""
The submission workbook (CLAUDE.md §1). A build item, not an export step.

Six sheets: Summary, Portfolio, NAV, Trades, Methodology, Robustness. The
Methodology sheet is not boilerplate — it carries the frozen decisions, the formula
behind every reported figure, and the disclosures DECISIONS.md requires: that PNL is
a price-return figure understating a total-return book by roughly 9 pp of median
five-year return on this universe, and that headline accuracy is beta-inflated
against a universe whose median name returned +173.8%.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest import BacktestResult
from src.config import Config
from src.decisions import blocked


def write_workbook(cfg: Config, path: Path, result: BacktestResult,
                   metrics: dict[str, float], benchmarks: pd.DataFrame) -> None:
    raise blocked("D1", "the benchmark set the comparison sheet reports")
