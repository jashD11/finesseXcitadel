"""
Shared fixtures.

A synthetic panel rather than the real one: these tests must fail for the reason they
name, and a 200-name market panel makes a failure hard to attribute. The synthetic
prices are deterministic, so the expected book is known by construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.clean import Panel
from src.config import load

# Distinct compound growth rates, so the momentum ranking is unambiguous and no two
# names can tie except where a test deliberately makes them.
_DRIFT = {"AAA": 0.0016, "BBB": 0.0012, "CCC": 0.0008, "DDD": 0.0004,
          "EEE": -0.0002, "FFF": 0.0020}
_LATE = "FFF"          # lists partway through, to exercise as-of eligibility
_LATE_FROM = 320


@pytest.fixture(scope="session")
def cfg():
    return load()


@pytest.fixture
def panel() -> Panel:
    days = pd.DatetimeIndex(pd.bdate_range("2020-01-01", periods=400))
    isins = pd.Index([f"INE000{i:02d}01010" for i in range(len(_DRIFT))], name="isin")
    tickers = list(_DRIFT)

    closes = {}
    for isin, ticker in zip(isins, tickers):
        path = 100.0 * np.exp(_DRIFT[ticker] * np.arange(len(days)))
        if ticker == _LATE:
            path[:_LATE_FROM] = np.nan
        closes[isin] = path

    close = pd.DataFrame(closes, index=days, columns=isins)
    frames = dict(close=close, open=close * 0.99, high=close * 1.01, low=close * 0.98,
                  volume=pd.DataFrame(1e6, index=days, columns=isins))
    flags = {k: pd.DataFrame(False, index=days, columns=isins)
             for k in ("stale", "bad_tick", "filled")}
    frames["volume"] = frames["volume"].where(close.notna())

    # A10 is computed the same way `clean.flag_zero_volume` computes it, from t-1.
    tradeable = (frames["volume"].shift(1) > 0) & close.notna()

    return Panel(symbols=pd.Series(tickers, index=isins), tradeable=tradeable,
                 **frames, **flags)


@pytest.fixture
def rebalances(panel) -> pd.DatetimeIndex:
    """Three dates, all far enough in for the 252-day window to be complete."""
    return panel.dates[[300, 330, 360]]
