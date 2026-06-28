#!/usr/bin/env python3
"""Reproduce the public generic panel run for `redistribution_gap_bottom40_real_income_growth_oecd`."""
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
            "redistribution_gap_bottom40_real_income_growth_oecd",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
