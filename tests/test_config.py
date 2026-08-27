"""
Config is the enforcement point for the governing rule: nothing runs on a default for
an unresolved decision. These tests check the enforcement, not the values.
"""

from __future__ import annotations

import textwrap

import pytest
import yaml

from src.config import KNOWN, NULLABLE, PENDING, load
from src.decisions import ConfigError, UnresolvedDecision


def _write(tmp_path, tree):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(tree))
    return path


def test_repo_config_loads():
    load()


def test_every_pending_key_is_declared_known():
    assert set(PENDING) <= KNOWN
    assert set(NULLABLE) <= KNOWN


def test_pending_and_nullable_are_disjoint():
    assert not (set(PENDING) & set(NULLABLE))


def test_reading_a_pending_key_raises_with_its_decision_id():
    cfg = load()
    for key, decision in cfg.pending().items():
        with pytest.raises(UnresolvedDecision) as exc:
            cfg[key]
        assert decision in str(exc.value), f"{key} did not name decision {decision}"


def test_unknown_key_raises(tmp_path):
    tree = yaml.safe_load(load().path.read_text())
    tree["meta"]["not_a_real_key"] = 1
    with pytest.raises(ConfigError, match="unknown config keys"):
        load(_write(tmp_path, tree))


def test_missing_key_raises(tmp_path):
    tree = yaml.safe_load(load().path.read_text())
    del tree["mandate"]["capital"]
    with pytest.raises(ConfigError, match="declared but absent"):
        load(_write(tmp_path, tree))


def test_null_without_a_declared_reason_raises(tmp_path):
    tree = yaml.safe_load(load().path.read_text())
    tree["mandate"]["capital"] = None
    with pytest.raises(ConfigError, match="null with no declared reason"):
        load(_write(tmp_path, tree))


def test_filling_in_a_pending_decision_raises(tmp_path):
    """
    The one that matters. Setting a value for an open decision must fail, so a
    decision cannot be resolved in config.yaml alone without the ledger entry.
    """
    tree = yaml.safe_load(load().path.read_text())
    # Taken from PENDING rather than hardcoded: naming a specific key here made the
    # test go stale the moment that decision was resolved.
    section, _, leaf = next(iter(PENDING)).partition(".")
    tree[section][leaf] = "a value nobody recorded in the ledger"
    with pytest.raises(ConfigError, match="declared PENDING but have values"):
        load(_write(tmp_path, tree))


def test_frozen_decisions_are_present_and_not_null():
    """Decisions recorded FROZEN in DECISIONS.md must carry a value."""
    cfg = load()
    for key in ("prices.return_basis", "prices.price_field", "fetch.source",
                "fetch.start", "eligibility.require_full_window",
                "signal.formation_lag_days", "weighting.reset_to_target",
                "noise.n_draws", "noise.rebalanced", "noise.replacement",
                "metrics.trade_basis", "mandate.stress_start",
                # B1 is FROZEN (amended 2026-08-27) and was missing from this list.
                "execution.rebalance_calendar",
                # A8's rider: the override file must be declared, not implied.
                "clean.phantom_day_overrides"):
        assert cfg[key] is not None


def test_the_configured_calendar_is_one_the_code_supports():
    """
    Guards the seam B1's amendment created: `config.yaml` names a cadence and
    `src/calendar.py` dispatches it. A typo here would not be caught by the KNOWN-key
    check, which validates key names and not values.
    """
    from src.calendar import supported_calendars
    assert load()["execution.rebalance_calendar"] in supported_calendars()


def test_no_get_with_default_anywhere_in_src():
    """
    A default in a getter is a design decision made in the dark. ``Config`` offers no
    default at all; this catches the pattern creeping in via plain dicts.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "src"
    pattern = re.compile(r"cfg\.get\(|config\.get\(")
    offenders = [p.name for p in root.glob("*.py") if pattern.search(p.read_text())]
    assert not offenders, f"config.get(...) with a default found in: {offenders}"
