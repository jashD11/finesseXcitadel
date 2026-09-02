"""
Decision gating.

`docs/DECISIONS.md` is the ledger; this module is the enforcement. Nothing in this repo
is allowed to run on a default for an unresolved design decision, so both failure
modes below are loud exceptions rather than fallbacks.
"""

from __future__ import annotations


class UnresolvedDecision(RuntimeError):
    """Raised when code reads a config value whose decision is still open."""


class ConfigError(RuntimeError):
    """Raised when config.yaml and the declared schema disagree."""


def blocked(decision: str, what: str) -> "NotImplementedError":
    """
    Build the exception a stub raises.

    Returned rather than raised so the call site reads ``raise blocked(...)`` and
    static analysis still sees a terminating statement.
    """
    return NotImplementedError(
        f"blocked on decision {decision}: {what}. "
        f"Resolve it, record it in docs/DECISIONS.md, set the value in config.yaml, "
        f"then implement."
    )
