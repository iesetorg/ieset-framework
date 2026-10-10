#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,str(root/'scripts/run_imf_brent_export_transmission_2026.py'),'verify',*sys.argv[1:]],cwd=root))
