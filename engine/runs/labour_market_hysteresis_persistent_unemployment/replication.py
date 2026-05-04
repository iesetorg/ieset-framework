#!/usr/bin/env python3
"""Replicate this local-projections run from the preregistered hypothesis spec."""
from scripts.run_local_projections import run_one

if __name__ == '__main__':
    print(run_one('labour_market_hysteresis_persistent_unemployment', force=True))
