#!/usr/bin/env python3
"""Replicate this descriptive run from the preregistered hypothesis spec."""
from scripts.run_descriptive import run_one

if __name__ == '__main__':
    print(run_one('shock_therapy_institutional_preconditions_conditionality', force=True))
