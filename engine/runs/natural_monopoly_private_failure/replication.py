#!/usr/bin/env python3
"""Replication entrypoint for natural_monopoly_private_failure.

This hypothesis is executed through the generic event-study runner:
    python3 scripts/run_event_study.py natural_monopoly_private_failure
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HYPOTHESIS_ID = "natural_monopoly_private_failure"
RUNNER = ROOT / "scripts" / "run_event_study.py"
RUN_DIR = ROOT / "engine" / "runs" / HYPOTHESIS_ID


def main() -> None:
    subprocess.run(
        ["python3", str(RUNNER), HYPOTHESIS_ID],
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
