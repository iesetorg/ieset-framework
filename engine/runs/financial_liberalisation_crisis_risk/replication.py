#!/usr/bin/env python3
"""Replication entrypoint for financial_liberalisation_crisis_risk.

This hypothesis is executed through the generic panel FE runner using the
pre-registered YAML spec and local vintages:
    python3 scripts/run_panel_fe.py financial_liberalisation_crisis_risk
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HYPOTHESIS_ID = "financial_liberalisation_crisis_risk"
RUNNER = ROOT / "scripts" / "run_panel_fe.py"
RUN_DIR = ROOT / "engine" / "runs" / HYPOTHESIS_ID


def main() -> None:
    subprocess.run(
        [sys.executable, str(RUNNER), HYPOTHESIS_ID, "--force"],
        cwd=str(ROOT),
        check=True,
    )
    diag_path = RUN_DIR / "diagnostics.json"
    if not diag_path.exists():
        raise FileNotFoundError(diag_path)
    diag = json.loads(diag_path.read_text())
    print(diag.get("verdict", "UNKNOWN"))


if __name__ == "__main__":
    main()
