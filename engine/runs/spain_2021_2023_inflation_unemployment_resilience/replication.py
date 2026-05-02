#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.generate_national_event_wave import run_one

if __name__ == '__main__':
    run_one('spain_2021_2023_inflation_unemployment_resilience')
