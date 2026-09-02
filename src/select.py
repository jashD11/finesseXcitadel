"""
Ranking, the rank buffer, and the tie-break.

V0 takes the plain top 10 with no buffer; the buffer arrives with V1 (docs/PROJECT.md §6).
Both paths land here so selection logic lives in exactly one place.

C7 (frozen) is the tie-break: incumbent first, then ISIN ascending. Exact ties on
float64 scores are near-impossible, but without a deterministic rule the backtest is
not bit-reproducible, and reproducibility is a submission requirement.
"""

from __future__ import annotations

import pandas as pd

from src.config import Config
from src.decisions import ConfigError

_TIE_BREAK = "incumbent_then_isin"


def _ordered(cfg: Config, scores: pd.Series, incumbents: list[str]) -> pd.Index:
    """Scores sorted under the C7 tie-break. Shared by both selection paths."""
    if cfg["selection.tie_break"] != _TIE_BREAK:
        raise ConfigError(f"C7 froze {_TIE_BREAK!r}; got {cfg['selection.tie_break']!r}")
    assert scores.notna().all(), "a NaN score reached selection — C5 forbids imputation"
    assert scores.index.is_unique, "duplicate names in the score series"

    held = set(incumbents)
    frame = pd.DataFrame({
        "score": scores.to_numpy(),
        "incumbent": [1 if name in held else 0 for name in scores.index],
        "name": scores.index,
    })
    frame = frame.sort_values(["score", "incumbent", "name"],
                              ascending=[False, False, True])
    return pd.Index(frame["name"])


def top_n(cfg: Config, scores: pd.Series, n: int, incumbents: list[str]) -> list[str]:
    """V0 selection: highest ``n`` scores, deterministically ordered."""
    assert len(scores) >= n, f"only {len(scores)} scored names, need {n}"
    picked = list(_ordered(cfg, scores, incumbents)[:n])
    assert len(picked) == n and len(set(picked)) == n
    return picked


def with_buffer(cfg: Config, scores: pd.Series, incumbents: list[str],
                n: int) -> list[str]:
    """
    V1 selection: hysteresis. A name enters at top ``enter_rank`` and is evicted only
    below ``exit_rank``. An incumbent that has become ineligible exits regardless of
    rank — eligibility overrides the buffer, because it is not scored at all.

    Unexercised until V1 lands; it needs no open decision, so it lives here rather than
    as a stub that would have to claim a resolved decision was blocking it.
    """
    enter = int(cfg["composite.buffer_enter_rank"])
    exit_rank = int(cfg["composite.buffer_exit_rank"])
    assert enter <= exit_rank, "buffer would evict a name it just admitted"

    order = list(_ordered(cfg, scores, incumbents))
    rank = {name: i + 1 for i, name in enumerate(order)}

    # Eligibility overrides the buffer: an incumbent absent from `scores` was not
    # eligible this date and leaves whatever its old rank was.
    kept = [name for name in incumbents if rank.get(name, exit_rank + 1) <= exit_rank]
    entrants = [name for name in order if name not in set(kept) and rank[name] <= enter]

    book = (kept + entrants)[:n]
    if len(book) < n:  # buffer held too few; backfill by rank
        book += [name for name in order if name not in set(book)][:n - len(book)]
    assert len(book) == n and len(set(book)) == n
    return book
