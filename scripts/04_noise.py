#!/usr/bin/env python3
"""Phase 3 noise band. Not implemented — inherits every open decision in backtest.run."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load  # noqa: E402


def main() -> int:
    cfg = load()
    pending = cfg.pending()
    print("Phase 3 noise band: not implemented.")
    print("inherits every open decision in backtest.run.")
    print(f"{len(pending)} config keys are still blocked:")
    for key, decision in pending.items():
        print(f"  {decision:>4s}  {key}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
