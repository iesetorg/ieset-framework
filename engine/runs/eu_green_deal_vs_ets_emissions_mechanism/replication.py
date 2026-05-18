#!/usr/bin/env python3
"""Exact blocker/provenance wrapper for the EU Green Deal vs ETS mechanism test."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
GHG_PATH = ROOT / "data/vintages/eea/greenhouse_gas_inventory@2026-04-30T115944Z.parquet"
ETS_PATH = ROOT / "data/vintages/eea/eu_ets_verified_emissions@2026-04-30T115942Z.parquet"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect(path: Path) -> dict:
    df = pd.read_parquet(path)
    note = ""
    if "note" in df.columns and df["note"].notna().any():
        note = str(df["note"].dropna().iloc[0])
    return {
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "rows": int(len(df)),
        "non_null_values": int(df["value"].notna().sum()) if "value" in df.columns else 0,
        "is_bootstrap_stub": "bootstrap-stub" in note,
        "note": note,
    }


def main() -> None:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    vintages = {
        "eea_greenhouse_gas_inventory": inspect(GHG_PATH),
        "eea_eu_ets_verified_emissions": inspect(ETS_PATH),
    }
    has_real_outcome = all(v["non_null_values"] > 0 and not v["is_bootstrap_stub"] for v in vintages.values())
    manifest = {
        "hypothesis_id": "eu_green_deal_vs_ets_emissions_mechanism",
        "run_utc": run_utc,
        "verdict_label": "INCONCLUSIVE_DATA_PENDING",
        "wrapper": "engine/runs/eu_green_deal_vs_ets_emissions_mechanism/replication.py",
        "status": "blocked" if not has_real_outcome else "ready_for_full_event_study",
        "reason": (
            "Local EEA vintages are bootstrap stubs with no non-null emissions outcomes; "
            "the preregistered sectoral event study cannot be graded."
        ),
        "vintages": vintages,
        "next_unblock": [
            "Populate real EEA greenhouse-gas inventory by country-sector-year.",
            "Populate real EEA EU ETS verified emissions by country-sector-year.",
            "Then run the sectoral post-2020 Green Deal versus ETS-only event-study design.",
        ],
    }
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    print(json.dumps({"hypothesis_id": manifest["hypothesis_id"], "status": manifest["status"]}, indent=2))


if __name__ == "__main__":
    main()
