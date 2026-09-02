"""
The script layer: the pure functions that decide what gets published.

`src/` is covered by the other five test modules. The functions here live in `scripts/`
because they are pipeline logic rather than engine logic, but two of them are
load-bearing for what a reader sees:

- `13_config_ledger.parse` turns an output directory back into the configuration that
  produced it. Every row of `output/report/configurations.md` -- and the published count
  of how many configurations were tested -- depends on it being right. A directory
  assigned to the wrong slate would misreport the search without any number changing.
- `11_smallcap_universe.worst_interior_gap` is the rule that excluded FORCEMOT (A19). It
  decides whether a name enters the universe at all, which is exactly the kind of rule
  that should not live only in a script's inner loop.

Scripts are imported by path because their names begin with a digit.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(stem: str):
    """Import a numbered script as a module."""
    path = ROOT / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ledger = _load("13_config_ledger")
smallcap = _load("11_smallcap_universe")
report = _load("06_report")


# ── 13_config_ledger.parse ───────────────────────────────────────────────────


@pytest.mark.parametrize("directory,slate,cadence,weighting", [
    ("output", "MAND", "quarterly", "reset"),
    ("output/sweep/quarterly_reset", "MAND", "quarterly", "reset"),
    ("output/sweep/monthly_reset", "MAND", "monthly", "reset"),
    ("output/sweep/every_trading_day_drift", "MAND", "daily", "drift"),
    ("output/sweep/mom126x0_monthly_reset", "SIG", "monthly", "reset"),
    ("output/sweep/small_quarterly_reset", "SMALL", "quarterly", "reset"),
    ("output/v1/base", "V1", "quarterly", "reset"),
    ("output/v1/rm-solo", "V1", "quarterly", "reset"),
    ("output/v1/w8_weekly_drift", "WGT", "weekly", "drift"),
    ("output/v1/no-id_monthly_reset", "WGT", "monthly", "reset"),
])
def test_parse_assigns_the_right_slate_and_frame(directory, slate, cadence, weighting):
    """A directory name is the only record of what a run was. It must decode exactly."""
    spec = ledger.parse(ROOT / directory)
    assert spec is not None, f"{directory} was not recognised at all"
    assert spec["slate"] == slate
    assert spec["cadence"] == cadence
    assert spec["weighting"] == weighting


def test_parse_recovers_the_signal_parameters():
    """The SIG grid's whole point is the lookback/skip pair; it must survive the round trip."""
    spec = ledger.parse(ROOT / "output/sweep/mom189x21_weekly_drift")
    assert (spec["lookback"], spec["skip"]) == (189, 21)
    assert "189" in spec["signal"] and "21" in spec["signal"]


def test_parse_marks_the_smallcap_universe():
    """A SMALL row must never be read as if it ran on the submitted universe."""
    assert "Smallcap" in ledger.parse(ROOT / "output/sweep/small_monthly_reset")["universe"]
    assert "Smallcap" not in ledger.parse(ROOT / "output/sweep/monthly_reset")["universe"]


def test_parse_distinguishes_the_buffer_arm():
    """`buffer` differs from `base` only in the buffer flag — the one bit that names it."""
    assert ledger.parse(ROOT / "output/v1/buffer")["buffer"] is True
    assert ledger.parse(ROOT / "output/v1/base")["buffer"] is False


def test_parse_returns_none_for_an_unknown_directory():
    """Unrecognised is reported, never guessed: `main` prints a warning on None."""
    assert ledger.parse(ROOT / "output/sweep/not_a_real_cell_name_xyz") is None


def test_every_declared_duplicate_names_a_real_directory_pair():
    """A stale DUPLICATES entry would silently drop a run from the distinct-config count."""
    for dup, original in ledger.DUPLICATES.items():
        assert ledger.parse(ROOT / dup) is not None, dup
        assert ledger.parse(ROOT / original) is not None, original
        assert dup != original


def test_weight_vectors_match_the_config():
    """The ledger prints weight vectors as text; they must be the ones actually run."""
    from src.config import load
    cfg = load()
    for arm, printed in ledger.VECTORS.items():
        key = {"no-dd": "no_ddown", "no-id": "no_idisc"}.get(arm, arm)
        actual = [str(int(cfg[f"composite.weight_vectors.{key}.{f}"]))
                  for f in ("mom_12_1", "info_discreteness", "drawdown_252")]
        assert printed == "/".join(actual), f"{arm}: ledger says {printed}, config says {actual}"


# ── 11_smallcap_universe.worst_interior_gap (A19) ────────────────────────────


def _series(values):
    return pd.Series(values, index=pd.date_range("2021-01-01", periods=len(values)))


def test_no_gap_in_a_complete_series():
    assert smallcap.worst_interior_gap(_series([1.0, 2.0, 3.0, 4.0])) == 0


def test_leading_nans_are_not_a_gap():
    """A name that had not listed yet is not a data defect — A5/C6 already handles it."""
    assert smallcap.worst_interior_gap(_series([np.nan, np.nan, 1.0, 2.0])) == 0


def test_an_interior_hole_is_measured_in_sessions():
    assert smallcap.worst_interior_gap(_series([1.0, np.nan, np.nan, 4.0])) == 2


def test_the_longest_run_wins_not_the_total():
    """Two short holes must not add up to an exclusion; the cap is on a single run."""
    assert smallcap.worst_interior_gap(
        _series([1.0, np.nan, 3.0, np.nan, np.nan, np.nan, 7.0])) == 3


def test_trailing_nans_count_only_after_a_print():
    """A series that ends in NaN has a real hole — the name printed, then stopped."""
    assert smallcap.worst_interior_gap(_series([1.0, 2.0, np.nan, np.nan])) == 2


def test_an_all_nan_series_has_no_interior_gap():
    """Never listed at all: unpriceable, handled separately, and not a gap."""
    assert smallcap.worst_interior_gap(_series([np.nan, np.nan, np.nan])) == 0


def test_forcemot_style_gap_exceeds_the_configured_cap():
    """The A19 exclusion, as a property: a 41-session hole must not survive the A9 cap."""
    from src.config import load
    cap = int(load()["clean.ffill_max_days"])
    series = _series([1.0] + [np.nan] * 41 + [1.0])
    assert smallcap.worst_interior_gap(series) == 41
    assert smallcap.worst_interior_gap(series) > cap


# ── 06_report formatting ─────────────────────────────────────────────────────


@pytest.mark.parametrize("value,kind,expected", [
    (0.6378, "pct", "63.78%"),
    (-0.3240, "pct", "-32.40%"),
    (107649806.0, "rs", "₹107,649,806"),
    (168.0, "int", "168"),
    (7.36, "x", "7.36×"),
    (2.42, "num", "2.42"),
])
def test_report_formatting(value, kind, expected):
    """The report quotes these strings verbatim, so their shape is part of the output."""
    assert report.fmt(value, kind) == expected


def test_every_required_metric_key_exists_in_a_real_metrics_file():
    """
    Guidelines §7 lists the metrics that must be reported. `06_report.REQUIRED` is that
    list, and a renamed metric would silently drop a required row from the report.
    """
    path = ROOT / "output" / "sweep" / "monthly_reset" / "metrics.csv"
    if not path.exists():
        pytest.skip("submitted cell has not been run in this checkout")
    metrics = pd.read_csv(path, index_col=0)["value"]
    for _, key, _ in report.REQUIRED:
        assert key in metrics.index, f"required metric {key!r} is not emitted"
