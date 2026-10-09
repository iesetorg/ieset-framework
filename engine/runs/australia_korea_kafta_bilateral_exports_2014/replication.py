#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_fta_baci_two_north_asia_event_family_2026.py'), 'verify', '--case', 'australia_korea_kafta_bilateral_exports_2014'], cwd=root))
