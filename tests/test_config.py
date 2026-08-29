"""
Config is the enforcement point for the governing rule: nothing runs on a default for
an unresolved decision. These tests check the enforcement, not the values.
"""

from __future__ import annotations

import textwrap

import pytest
import yaml

from src.config import DEFAULT_CONFIG, KNOWN, NULLABLE, PENDING, load
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


def test_reading_a_pending_key_raises_with_its_decision_id(monkeypatch):
    """
    PENDING has been empty since 2026-08-30, when Phase 2 closed the last five decisions
    (C3, C4, C5, C8, C9). Iterating `cfg.pending()` therefore passes vacuously, so the
    enforcement is exercised against a SYNTHETIC entry as well -- otherwise the day someone
    opens a new decision, the test that was supposed to guard it would never have run.
    """
    import src.config as config_module

    cfg = load()
    for key, decision in cfg.pending().items():          # empty today, kept for tomorrow
        with pytest.raises(UnresolvedDecision) as exc:
            cfg[key]
        assert decision in str(exc.value), f"{key} did not name decision {decision}"

    monkeypatch.setitem(config_module.PENDING, "signal.skip", "C-SYNTHETIC")
    cfg._flat["signal.skip"] = None
    with pytest.raises(UnresolvedDecision) as exc:
        cfg["signal.skip"]
    assert "C-SYNTHETIC" in str(exc.value)


def test_a_dead_decisions_key_raises_with_its_reason():
    """
    C4 and C8 are DEAD -- the questions ceased to exist rather than being answered -- so
    their keys are declared nulls carrying the reason, not PENDING entries. Reading one must
    still refuse rather than hand back a default, and must say why.
    """
    cfg = load()
    for key, expect in (("composite.winsor_z", "C4"), ("composite.reversal_sign", "C8")):
        with pytest.raises(ConfigError) as exc:
            cfg[key]
        assert expect in str(exc.value), f"{key} did not explain itself"


def test_every_composite_feature_has_a_sign_and_a_weight():
    """
    C10/C14/C15: a feature cannot enter the composite without a declared sign, because a
    reversed sign is the one V1 error that produces a plausible-looking run. `src/config.py`
    declares one KNOWN key per sign for this reason; this asserts the two stay in step.
    """
    cfg = load()
    for feature in cfg["composite.features"]:
        assert cfg[f"composite.feature_signs.{feature}"] in (1, -1)
        for vector in ("base", "tilt"):
            assert cfg[f"composite.weight_vectors.{vector}.{feature}"] > 0


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


def test_filling_in_a_pending_decision_raises(tmp_path, monkeypatch):
    """
    The one that matters. Setting a value for an open decision must fail, so a
    decision cannot be resolved in config.yaml alone without the ledger entry.

    This has now been wrong twice in opposite directions. Naming a key here made the test go
    stale the moment that decision was resolved; taking one from PENDING raised
    StopIteration once PENDING emptied on 2026-08-30. It now injects a synthetic entry over
    a key that genuinely carries a value, which exercises the clash itself and depends on
    neither the contents of PENDING nor the state of any particular decision.
    """
    import src.config as config_module

    tree = yaml.safe_load(DEFAULT_CONFIG.read_text())
    monkeypatch.setitem(config_module.PENDING, "signal.skip", "C-SYNTHETIC")
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
