#!/usr/bin/env python3
"""Exact blocker/provenance wrapper for the EU ETS price-signal test."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
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
    ets = inspect(ETS_PATH)
    has_real_ets = ets["non_null_values"] > 0 and not ets["is_bootstrap_stub"]
    manifest = {
        "hypothesis_id": "eu_ets_price_2022_2026_carbon_signal_strength",
        "run_utc": run_utc,
        "verdict_label": "INCONCLUSIVE_DATA_PENDING",
        "wrapper": "engine/runs/eu_ets_price_2022_2026_carbon_signal_strength/replication.py",
        "status": "blocked" if not has_real_ets else "emissions_ready_price_series_missing",
        "reason": (
            "Local EU ETS verified-emissions vintage is a bootstrap stub, and no local EUA/TTF "
            "price vintage is available. The price-signal intensity panel cannot be graded."
        ),
        "vintages": {
            "eea_eu_ets_verified_emissions": ets,
        },
        "missing_required_vintages": [
            "EEX or equivalent EUA allowance price, monthly or annual average",
            "TTF natural gas price, monthly or annual average",
            "Country-sector EU ETS verified emissions with non-null values",
            "Industry or power activity denominator for emissions intensity",
        ],
        "next_unblock": [
            "Replace the EEA bootstrap ETS vintage with real verified-emissions data.",
            "Add manual or fetched EUA and TTF price vintages.",
            "Run the post-2021 emissions-intensity trend-break specification.",
        ],
    }
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    print(json.dumps({"hypothesis_id": manifest["hypothesis_id"], "status": manifest["status"]}, indent=2))


if __name__ == "__main__":
    main()
