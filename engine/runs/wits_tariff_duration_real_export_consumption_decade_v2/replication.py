#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
subprocess.run([sys.executable, str(root / 'scripts/run_wits_tariff_duration_real_export_consumption_decade_v2.py'), '--replay', *sys.argv[1:]], check=True)
