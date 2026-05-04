#!/usr/bin/env python3
"""Replicate this DiD run from the preregistered hypothesis spec."""
from scripts.run_did_callaway_santanna import run_one

if __name__ == '__main__':
    print(run_one('tax_inequality_russia_2001_flat_tax_13pct', force=True))
