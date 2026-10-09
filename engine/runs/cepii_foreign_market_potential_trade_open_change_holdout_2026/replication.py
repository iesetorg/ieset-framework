#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_cepii_wdi_exposure_family_2026.py'), '--verify', 'cepii_foreign_market_potential_trade_open_change_holdout_2026'], cwd=root))
