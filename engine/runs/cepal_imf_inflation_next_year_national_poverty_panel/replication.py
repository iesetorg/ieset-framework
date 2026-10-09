#!/usr/bin/env python3
"""Read-only exact replay of the CEPAL/IMF descriptive packet."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_cepal_imf_inflation_next_year_national_poverty_panel.py'), '--check'], cwd=root))
