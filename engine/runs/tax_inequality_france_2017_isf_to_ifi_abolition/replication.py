#!/usr/bin/env python3
"""Replication wrapper for `tax_inequality_france_2017_isf_to_ifi_abolition`.

Re-runs the canonical `scripts/run_synth_did.py` pipeline with `--force` so the
archived synthetic-control run can be reproduced without duplicating estimator
logic in this directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from _replication_runner import rerun

HYPOTHESIS_ID = "tax_inequality_france_2017_isf_to_ifi_abolition"
RUNNER = "scripts/run_synth_did.py"


if __name__ == "__main__":
    raise SystemExit(rerun(__file__, HYPOTHESIS_ID, RUNNER))
