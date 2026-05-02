#!/usr/bin/env python3
"""Regenerate this structural-wave artifact."""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[3]
runpy.run_path(str(root / 'scripts' / 'generate_wdi_owid_structural_wave.py'), run_name='__main__')
