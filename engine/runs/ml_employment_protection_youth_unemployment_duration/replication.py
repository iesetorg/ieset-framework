#!/usr/bin/env python3
"""Reproduce the public generic panel run for `ml_employment_protection_youth_unemployment_duration`."""
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
            "ml_employment_protection_youth_unemployment_duration",
        ],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
