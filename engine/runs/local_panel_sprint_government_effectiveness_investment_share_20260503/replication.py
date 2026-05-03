#!/usr/bin/env python3
"""Replicate the registered panel-FE run for local_panel_sprint_government_effectiveness_investment_share_20260503."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.run_panel_fe import run_one


if __name__ == "__main__":
    print(run_one("local_panel_sprint_government_effectiveness_investment_share_20260503", force=True, persist_preflight_inconclusive=True))
