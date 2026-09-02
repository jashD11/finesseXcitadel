"""
Load and validate config.yaml.

Four invariants, all enforced at load time:

1. Every key present in the YAML is declared in ``KNOWN`` — a typo raises instead of
   being silently ignored.
2. Every key in ``KNOWN`` is present in the YAML — a missing parameter raises instead
   of being papered over by a caller's default.
3. Every ``null`` value is either a declared pending decision or a declared
   non-decision null. A bare ``null`` with no reason raises.
4. Every declared pending decision is actually ``null``. This is the one that matters:
   it makes it impossible to quietly fill in a value for an open decision without
   first removing it from ``PENDING`` here, which forces the ledger update.

There is no ``get(key, default)`` anywhere in this codebase. A default in a getter is
a design decision made in the dark.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.decisions import ConfigError, UnresolvedDecision

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config.yaml"

# ── Pending decisions: dotted key -> decision ID in DECISIONS.md ──────────────
# Empty since 2026-08-30: Phase 2 closed the last five (C3, C4, C5, C8, C9). Kept, and
# still enforced, because the machinery is what makes a *future* open decision fail loudly
# instead of running on a default — and because `cfg.pending()` returning {} is a claim the
# ledger has to keep earning.
PENDING: dict[str, str] = {}

# Nulls that are not decisions. Each needs a stated meaning.
NULLABLE: dict[str, str] = {
    "fetch.end": "null means the run date",
    # C4 and C8 are DEAD, not open: the questions ceased to exist rather than being
    # answered. The keys stay so a reader meets the reason here rather than hunting the
    # ledger, and so reading one raises with that reason instead of returning a default.
    "composite.winsor_z": "C4 is DEAD — scaled ranks (C17) have no outliers to clip",
    "composite.reversal_sign": "C8 is DEAD — C10 excluded the reversal feature",
}

KNOWN: set[str] = {
    "meta.docs", "meta.ledger",
    "paths.data_raw", "paths.data_clean", "paths.reports", "paths.output",
    "output.nav", "output.trades", "output.holdings", "output.weights",
    "output.metrics", "output.benchmarks",
    "mandate.capital", "mandate.book_size", "mandate.cost_bps",
    "mandate.start", "mandate.end", "mandate.stress_start", "mandate.stress_end",
    "universe.nifty100_url", "universe.midcap100_url", "universe.smallcap100_url",
    "universe.expected_per_list",
    "universe.snapshot", "universe.expected_total", "universe.expected_members",
    "universe.yahoo_suffix", "universe.identity_key",
    "universe.press_release_dir", "universe.membership_overrides",
    "universe.membership_mode",
    "fetch.source", "fetch.start", "fetch.end", "fetch.indices", "fetch.batch_size",
    "fetch.request_pause_s", "fetch.max_retries", "fetch.user_agent",
    "prices.return_basis", "prices.price_field", "prices.execution_field",
    "clean.trading_calendar", "clean.ffill_max_days", "clean.zero_volume_policy",
    "clean.stale_price_n", "clean.bad_tick_abs_return", "clean.liquidity_floor",
    "clean.cache_immutable", "clean.corporate_action_overrides",
    "clean.phantom_day_overrides",
    "eligibility.require_full_window", "eligibility.min_eligible",
    "signal.lookback_unit", "signal.lookback", "signal.skip", "signal.return_type",
    "signal.formation_lag_days",
    "composite.features", "composite.market_proxy", "composite.residual_form",
    "composite.beta_window", "composite.flat_day_policy",
    # One key per feature sign, because `_flatten` recurses into mappings. The churn is
    # deliberate: a new feature cannot enter without its sign being declared here too.
    "composite.feature_signs.mom_12_1", "composite.feature_signs.info_discreteness",
    "composite.feature_signs.drawdown_252",
    "composite.combination_rule", "composite.ranking_population",
    "composite.missing_feature_policy", "composite.use_buffer",
    "composite.active_weights",
    "composite.weight_vectors.base.mom_12_1",
    "composite.weight_vectors.base.info_discreteness",
    "composite.weight_vectors.base.drawdown_252",
    "composite.weight_vectors.tilt.mom_12_1",
    "composite.weight_vectors.tilt.info_discreteness",
    "composite.weight_vectors.tilt.drawdown_252",
    "composite.weight_vectors.no_ddown.mom_12_1",
    "composite.weight_vectors.no_ddown.info_discreteness",
    "composite.weight_vectors.no_ddown.drawdown_252",
    "composite.weight_vectors.no_idisc.mom_12_1",
    "composite.weight_vectors.no_idisc.info_discreteness",
    "composite.weight_vectors.no_idisc.drawdown_252",
    "composite.weight_vectors.w3.mom_12_1",
    "composite.weight_vectors.w3.info_discreteness",
    "composite.weight_vectors.w3.drawdown_252",
    "composite.weight_vectors.w6.mom_12_1",
    "composite.weight_vectors.w6.info_discreteness",
    "composite.weight_vectors.w6.drawdown_252",
    "composite.weight_vectors.w8.mom_12_1",
    "composite.weight_vectors.w8.info_discreteness",
    "composite.weight_vectors.w8.drawdown_252",
    "composite.winsor_z", "composite.reversal_sign",
    "composite.buffer_enter_rank", "composite.buffer_exit_rank",
    "selection.tie_break",
    "execution.rebalance_calendar", "execution.share_granularity",
    "execution.cash_residue", "execution.charge_initial_build",
    "execution.cost_reserve", "execution.cost_reserve_multiple",
    "execution.nav_start_convention", "execution.corporate_action_mode",
    "weighting.target", "weighting.reset_to_target",
    "metrics.trade_basis", "metrics.dual_report", "metrics.annualisation",
    "metrics.sharpe_ddof", "metrics.trading_days_per_year",
    "metrics.calendar_days_per_year", "metrics.risk_free", "metrics.mdd_basis",
    "metrics.open_roundtrip_policy",
    "benchmark.set", "benchmark.charge_costs",
    "noise.n_draws", "noise.rebalanced", "noise.replacement", "noise.sampling_frame",
    "noise.charge_costs", "noise.master_seed", "noise.chunk_size",
    "noise.significance_test",
}


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    """Dotted-path view of the YAML tree. Lists are leaves, not branches."""
    out: dict[str, Any] = {}
    for key, value in node.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, f"{path}."))
        else:
            out[path] = value
    return out


class Config:
    """Validated config. Access is by dotted path and never returns a default."""

    def __init__(self, flat: dict[str, Any], path: Path) -> None:
        self._flat = flat
        self.path = path

    def __getitem__(self, key: str) -> Any:
        if key not in self._flat:
            raise ConfigError(f"{key!r} is not a config key (config: {self.path})")
        value = self._flat[key]
        if value is None:
            if key in PENDING:
                raise UnresolvedDecision(
                    f"{key!r} is blocked on decision {PENDING[key]}. "
                    f"Resolve it, record it in DECISIONS.md, then set it in config.yaml."
                )
            raise ConfigError(f"{key!r} is null: {NULLABLE.get(key, 'no reason declared')}")
        return value

    def raw(self, key: str) -> Any:
        """Value without the null check — only for code that must see the null itself."""
        if key not in self._flat:
            raise ConfigError(f"{key!r} is not a config key (config: {self.path})")
        return self._flat[key]

    def pending(self) -> dict[str, str]:
        """Open decisions, as {dotted key: decision ID}. Sorted for stable reporting."""
        return {k: PENDING[k] for k in sorted(PENDING) if self._flat.get(k) is None}

    def resolved_path(self, key: str) -> Path:
        return REPO_ROOT / str(self[key])


def load(path: str | Path = DEFAULT_CONFIG) -> Config:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config not found: {path}")

    tree = yaml.safe_load(path.read_text())
    if not isinstance(tree, dict):
        raise ConfigError(f"config did not parse to a mapping: {path}")
    flat = _flatten(tree)

    unknown = sorted(set(flat) - KNOWN)
    if unknown:
        raise ConfigError(f"unknown config keys (typo, or add to KNOWN): {unknown}")

    missing = sorted(KNOWN - set(flat))
    if missing:
        raise ConfigError(f"config keys declared but absent from {path.name}: {missing}")

    undeclared_nulls = sorted(
        k for k, v in flat.items() if v is None and k not in PENDING and k not in NULLABLE
    )
    if undeclared_nulls:
        raise ConfigError(
            f"null with no declared reason: {undeclared_nulls}. "
            f"Add to PENDING with a decision ID, or to NULLABLE with a meaning."
        )

    # The governing rule, enforced: a decision listed as open must not carry a value.
    silently_resolved = sorted(k for k in PENDING if flat.get(k) is not None)
    if silently_resolved:
        raise ConfigError(
            f"these keys are declared PENDING but have values: {silently_resolved}. "
            f"A decision cannot be resolved in config.yaml alone — record it in "
            f"DECISIONS.md and remove it from PENDING in src/config.py."
        )

    return Config(flat, path)
