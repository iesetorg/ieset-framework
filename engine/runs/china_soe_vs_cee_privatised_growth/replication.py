#!/usr/bin/env python3
"""Exact aggregate-industry bridge for the China vs CEE ownership hypothesis."""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from static_reform_worker_a_exact import run_case


if __name__ == "__main__":
    raise SystemExit(run_case("china_soe_vs_cee_privatised_growth"))
