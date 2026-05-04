#!/usr/bin/env python3
"""Replicate this event-study run from the preregistered hypothesis spec."""
from scripts.run_event_study import run_one

if __name__ == '__main__':
    print(run_one('argentina_default_collapse_output_effects', force=True))
