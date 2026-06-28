#!/usr/bin/env python3
"""Reproduce the public generic panel run for `renewable_share_electricity_price_transition_cost_panel`."""
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
            "renewable_share_electricity_price_transition_cost_panel",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
