#!/usr/bin/env python3
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[3]
subprocess.run(['python3', 'scripts/run_placeholder_redesign_two_case_2026.py', '--verify'], cwd=root, check=True)
