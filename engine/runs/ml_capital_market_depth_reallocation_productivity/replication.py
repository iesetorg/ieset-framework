#!/usr/bin/env python3
"""Reproduce the public generic panel run for `ml_capital_market_depth_reallocation_productivity`."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    return subprocess.call(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_panel_fe.py"),
            "--force",
            "ml_capital_market_depth_reallocation_productivity",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
