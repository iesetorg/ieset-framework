#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_bis_batch04_wave_2026_05_12.py'), 'bis_reer_volatility_investment_drag_panel_1964_2026']))
