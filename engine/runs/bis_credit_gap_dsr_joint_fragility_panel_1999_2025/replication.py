#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_bis_batch01_credit_cycle_2026_05_12.py'), 'bis_credit_gap_dsr_joint_fragility_panel_1999_2025']))
