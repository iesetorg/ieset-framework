#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[3]
source_root = os.environ.get('IESET_SOURCE_ROOT', str(root))
raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_wbes_constraints_next_wave_encoding_adapter_2026.py'), '--verify', '--source-root', source_root], cwd=root))
