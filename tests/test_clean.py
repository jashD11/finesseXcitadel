"""
Phase 1 acceptance. Every expected figure here was measured against the real
snapshot before the code was written, so these are regression locks, not
self-fulfilling assertions.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src import calendar, clean, fetch
from src.config import load
from src.decisions import ConfigError

AS_OF = "2026-08-24"

# Measured against data/raw/prices_20260824.parquet before clean.py existed.
N_DAYS = 1787
N_NAMES = 200
PHANTOMS = ["2026-01-15", "2026-05-01", "2026-05-28", "2026-06-26"]
MUHURAT = ["2019-10-27", "2020-11-14"]


@pytest.fixture(scope="module")
def cfg():
    return load()


@pytest.fixture(scope="module")
def raw(cfg):
    path = fetch.snapshot_path(cfg, "prices", AS_OF)
    if not path.exists():
        pytest.skip("raw snapshot absent; run scripts/01_fetch.py")
    prices, _ = fetch.read_snapshot(path)
    universe = pd.read_csv(fetch.snapshot_path(cfg, "universe", AS_OF))
    return prices, universe


@pytest.fixture(scope="module")
def panel(cfg, raw):
    prices, universe = raw
    days = calendar.trading_days(cfg, prices)
    p = clean.build_panel(cfg, prices, universe, days)
    p = clean.apply_corporate_actions(p, clean.load_overrides(cfg))
    p = clean.fill_missing(cfg, p)
    p = clean.flag_zero_volume(cfg, p)
    p = clean.flag_stale(cfg, p)
    return clean.flag_bad_ticks(cfg, p)


# ── A8 calendar ──────────────────────────────────────────────────────────────


def test_calendar_length(cfg, raw):
    assert len(calendar.trading_days(cfg, raw[0])) == N_DAYS


def test_phantom_days_excluded(cfg, raw):
    """Yahoo emits a bar on these market holidays: a price on 189-200 names, zero
    volume on every one. All four fall inside the 2026 stress window."""
    days = calendar.trading_days(cfg, raw[0])
    assert calendar.phantom_days(raw[0]).tolist() == [pd.Timestamp(d) for d in PHANTOMS]
    for d in PHANTOMS:
        assert pd.Timestamp(d) not in days


def test_muhurat_sessions_retained(cfg, raw):
    """Real Diwali sessions with real volume. ^NSEI omits both, which is why it is
    not the calendar."""
    days = calendar.trading_days(cfg, raw[0])
    for d in MUHURAT:
        assert pd.Timestamp(d) in days


def test_calendar_rejects_an_unfrozen_rule(cfg, raw, monkeypatch):
    monkeypatch.setitem(cfg._flat, "clean.trading_calendar", "nsei")
    with pytest.raises(ConfigError, match="A8 froze"):
        calendar.trading_days(cfg, raw[0])


# ── A9 gaps ──────────────────────────────────────────────────────────────────


def test_panel_shape(panel):
    assert panel.close.shape == (N_DAYS, N_NAMES)


def test_no_interior_nan_after_listing(panel):
    listed = panel.close.notna().cummax()
    assert int((panel.close.isna() & listed).sum().sum()) == 0


def test_forward_fill_never_fires_on_this_snapshot(panel):
    """On the A8 calendar every name is contiguous from listing. The cap is
    defensive; if this ever fires, the calendar changed."""
    assert int(panel.filled.sum().sum()) == 0


def test_fill_cap_assertion_fires_on_a_real_gap(cfg, panel):
    """The cap must actually be enforced, not merely configured."""
    broken = clean.Panel(**{k: v.copy() if hasattr(v, "copy") else v
                            for k, v in panel.__dict__.items()})
    col = broken.close.columns[0]
    broken.close.iloc[100:120, broken.close.columns.get_loc(col)] = float("nan")
    with pytest.raises(AssertionError, match="exceeds the A9 cap"):
        clean.fill_missing(cfg, broken)


# ── A16 corporate actions ────────────────────────────────────────────────────


def test_overrides_all_carry_a_source(cfg):
    ov = clean.load_overrides(cfg)
    assert (ov["source"].astype(str).str.strip() != "").all()
    assert len(ov) == 5
    assert int(ov["applied"].astype(bool).sum()) == 3


def test_unsourced_override_is_rejected(cfg, tmp_path, monkeypatch):
    ov = clean.load_overrides(cfg)
    ov.loc[0, "source"] = ""
    path = tmp_path / "ov.csv"
    ov.to_csv(path, index=False)
    monkeypatch.setitem(cfg._flat, "clean.corporate_action_overrides", str(path))
    with pytest.raises(ConfigError, match="no source"):
        clean.load_overrides(cfg)


def test_applied_override_without_a_ratio_is_rejected(cfg, tmp_path, monkeypatch):
    ov = clean.load_overrides(cfg)
    ov["ratio"] = ov["ratio"].astype(object)
    ov.loc[ov.index[0], "ratio"] = ""
    path = tmp_path / "ov.csv"
    ov.to_csv(path, index=False)
    monkeypatch.setitem(cfg._flat, "clean.corporate_action_overrides", str(path))
    with pytest.raises(ConfigError, match="no ratio"):
        clean.load_overrides(cfg)


def test_back_adjustment_preserves_non_boundary_returns():
    """Rescaling a level is information-free. A change to any other return would be
    a look-ahead-grade defect."""
    days = pd.bdate_range("2024-01-01", periods=10)
    isin = "INE000A00001"
    close = pd.DataFrame({isin: [100.0, 101, 102, 103, 26, 26.5, 27, 27.5, 28, 28.5]},
                         index=days)
    p = clean.Panel(close=close, open=close.copy(), high=close.copy(),
                    low=close.copy(), volume=close.copy() * 0 + 1000,
                    tradeable=close.notna(), stale=close.notna(),
                    bad_tick=close.notna(), filled=close.notna(),
                    symbols=pd.Series({isin: "TEST"}))
    before = p.close.pct_change()
    ov = pd.DataFrame([dict(symbol="TEST", isin=isin, action="Bonus 3:1",
                            ex_date="2024-01-12", ratio=4.0,
                            boundary_date=days[4].date().isoformat(), applied=True,
                            verified_on="2026-08-24", source="unit test", note="")])
    clean.apply_corporate_actions(p, ov)
    after = p.close.pct_change()
    delta = (before - after).abs()
    delta.iloc[4] = 0.0           # the boundary return is the one that may change
    assert float(delta.max().max()) < 1e-12
    assert abs(p.close[isin].iloc[0] - 25.0) < 1e-12   # 100 / 4


def test_corrections_remove_the_phantom_returns(panel):
    """The three Yahoo defects produced -74.6%, -20.9% and -33.0%. After correction
    each must be an ordinary daily move."""
    sym_to_isin = {v: k for k, v in panel.symbols.items()}
    ret = panel.close.pct_change()
    for symbol, date in (("MOTILALOFS", "2024-01-01"), ("CONCOR", "2025-01-01"),
                         ("TRENT", "2026-01-01")):
        r = ret.loc[pd.Timestamp(date), sym_to_isin[symbol]]
        assert abs(r) < 0.05, f"{symbol} still shows {r:+.1%} on {date}"


def test_uncorrected_demergers_are_left_alone(panel):
    """TMPV and VEDL match the exchange exactly, so they are flagged and disclosed
    rather than adjusted on an invented ratio."""
    sym_to_isin = {v: k for k, v in panel.symbols.items()}
    ret = panel.close.pct_change()
    assert ret.loc[pd.Timestamp("2025-10-14"), sym_to_isin["TMPV"]] < -0.35
    assert ret.loc[pd.Timestamp("2026-04-30"), sym_to_isin["VEDL"]] < -0.60


# ── A10 / A11 flags ──────────────────────────────────────────────────────────


def test_tradeable_never_reads_same_day_volume(panel):
    """
    A10 screens on t-1 deliberately: the book executes at the open, so consulting
    today's volume first would be look-ahead. Proven by construction — the flag must
    equal the shifted volume test on every cell.
    """
    expected = (panel.volume.shift(1) > 0) & panel.close.notna()
    assert panel.tradeable.equals(expected)


def test_tradeable_is_false_on_the_first_day(panel):
    """There is no t-1 for the first row, so nothing is tradeable there."""
    assert not panel.tradeable.iloc[0].any()


def test_stale_flag_catches_patanjali_and_only_patanjali(panel):
    """1,826 runs of >=2 identical closes exist, but 1,748 are length 2 - ordinary
    tick granularity. At N=10 exactly one genuine suspension survives."""
    flagged = sorted(panel.symbols[i] for i in panel.stale.columns
                     if panel.stale[i].any())
    assert flagged == ["PATANJALI"]
