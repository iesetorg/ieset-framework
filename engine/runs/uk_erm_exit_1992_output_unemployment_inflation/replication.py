#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_national_event_wave import run_one

if __name__ == '__main__':
    run_one('uk_erm_exit_1992_output_unemployment_inflation')
