#!/usr/bin/env python3
"""Reproduce the public generic panel run for `bis_household_dsr_policy_rate_consumption_slowdown_panel`."""
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
            "bis_household_dsr_policy_rate_consumption_slowdown_panel",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
