#!/usr/bin/env python3
"""Read-only, source-pinned replay for bis_reer_misalignment_current_account_repair_panel_1964_2026."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from replay_bis_pinned import replay_one

HYPOTHESIS_ID = "bis_reer_misalignment_current_account_repair_panel_1964_2026"
BATCH = "batch04"
RUN_DIR = Path(__file__).resolve().parent


def main() -> int:
    print(json.dumps(replay_one(HYPOTHESIS_ID, BATCH, RUN_DIR), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
