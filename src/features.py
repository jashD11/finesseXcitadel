"""
Signal computation. Causal by construction: every feature for a rebalance at t is
computed from data through the close of t-1 (B2, frozen).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.clean import Panel
from src.config import Config
from src.decisions import ConfigError, blocked


def momentum_12_1(cfg: Config, panel: Panel, cutoff: pd.Timestamp) -> pd.Series:
    """
    12-1 momentum: the return from ``lookback`` trading days before ``cutoff`` to
    ``skip`` trading days before it.

    C2 (frozen) counts both in trading days on the A8 calendar: 252 back, ending 21
    days early. The skip sits *inside* the 252-day window, so the signal is 11 months
    of return out of a 12-month window — which is what "12 minus 1" names.

    Takes ``cutoff`` rather than the rebalance date, and takes it from
    `calendar.formation_cutoff`, so the t-1 lag (B2) is visible at the call site instead
    of being a slicing convention someone has to remember.
    """
    if cfg["signal.lookback_unit"] != "trading_days":
        raise ConfigError(f"C2 froze 'trading_days'; got {cfg['signal.lookback_unit']!r}")

    days = panel.dates
    pos = days.get_loc(cutoff)
    lookback, skip = int(cfg["signal.lookback"]), int(cfg["signal.skip"])
    if pos - lookback < 0:
        raise ValueError(f"{cutoff.date()} has only {pos} prior trading days, needs {lookback}")

    start = panel.close.iloc[pos - lookback]
    finish = panel.close.iloc[pos - skip]

    basis = cfg["signal.return_type"]
    if basis == "simple":
        signal = finish / start - 1.0
    elif basis == "log":
        signal = np.log(finish / start)
    else:
        raise ConfigError(f"C1 allows 'simple' or 'log'; got {basis!r}")

    signal.name = f"mom_{lookback}_{skip}"
    return signal


def realised_vol(cfg: Config, panel: pd.DataFrame, cutoff: pd.Timestamp) -> pd.Series:
    raise blocked("C2", "the lookback unit")


def illiquidity(cfg: Config, panel: pd.DataFrame, cutoff: pd.Timestamp) -> pd.Series:
    raise blocked("C2", "the lookback unit")


def reversal(cfg: Config, panel: pd.DataFrame, cutoff: pd.Timestamp) -> pd.Series:
    raise blocked("C8", "whether the short-horizon feature reads as momentum or reversal")


def composite(cfg: Config, features: pd.DataFrame) -> pd.Series:
    """
    Cross-sectional z-score per feature, winsorise, then a fixed weighted average.

    Z-scoring is across names on one date, never across time for one name. The
    time-shuffle test in tests/test_causality.py pins that down.
    """
    raise blocked("C3", "the population the z-score is computed over")
