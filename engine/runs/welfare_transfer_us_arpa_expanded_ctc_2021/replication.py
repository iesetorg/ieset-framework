#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from welfare_worker_b_exact import run_exact_benchmark

HYPOTHESIS_ID = "welfare_transfer_us_arpa_expanded_ctc_2021"


if __name__ == "__main__":
    raise SystemExit(run_exact_benchmark(__file__, HYPOTHESIS_ID))
