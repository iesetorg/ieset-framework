#!/usr/bin/env python3
"""Run the Worker D exact/proxy OECD productivity artifact."""
from __future__ import annotations

import sys
from pathlib import Path

RUNS_ROOT = Path(__file__).resolve().parents[1]
if str(RUNS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNS_ROOT))

from oecd_productivity_worker_d_exact import main


if __name__ == "__main__":
    raise SystemExit(main([__file__, "labor_reform_real_wage_growth"]))
