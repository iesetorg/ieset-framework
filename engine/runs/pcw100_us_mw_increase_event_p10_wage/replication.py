#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
command = [
    sys.executable,
    str(root / "scripts" / "policy_contrast_wave_100.py"),
    "--run-one",
    "pcw100_us_mw_increase_event_p10_wage",
    "--force",
]
raise SystemExit(subprocess.call(command, cwd=root))
