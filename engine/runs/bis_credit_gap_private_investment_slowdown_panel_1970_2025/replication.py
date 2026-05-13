#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_bis_batch04_wave_2026_05_12.py'), 'bis_credit_gap_private_investment_slowdown_panel_1970_2025']))
