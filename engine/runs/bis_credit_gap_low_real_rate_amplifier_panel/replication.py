#!/usr/bin/env python3
"""Read-only, source-pinned replay for bis_credit_gap_low_real_rate_amplifier_panel."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from replay_bis_pinned import replay_one

HYPOTHESIS_ID = "bis_credit_gap_low_real_rate_amplifier_panel"
BATCH = "batch01"
RUN_DIR = Path(__file__).resolve().parent


def main() -> int:
    print(json.dumps(replay_one(HYPOTHESIS_ID, BATCH, RUN_DIR), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
