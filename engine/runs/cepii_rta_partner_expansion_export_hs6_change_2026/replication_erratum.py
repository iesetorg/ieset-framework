#!/usr/bin/env python3
"""Working exact replay for the frozen CEPII/WITS result packet."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call(
    [sys.executable, str(root / "scripts/verify_cepii_rta_hs6_2026.py")], cwd=root
))
