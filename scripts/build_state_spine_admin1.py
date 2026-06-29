#!/usr/bin/env python3
"""Build the initial admin1/state identity spine.

The first landed spine is intentionally conservative: it mints stable U.S.
admin1 IDs from the existing USDOL state minimum-wage vintage and crosswalks
them to BLS FIPS keyed panels already on disk. Global admin1 sources are tracked
in data/state_level/source_inventory.yaml and should extend this builder once
geoBoundaries/GADM/ISO-3166-2 inputs are dropped or fetched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages"
DERIVED = ROOT / "data" / "derived"
MANIFESTS = ROOT / "data" / "manifests"


TERRITORY_FIPS = {"60", "66", "69", "72", "78"}


def utc_stamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_vintage(publisher: str, series: str) -> Path:
    candidates = list((VINTAGES / publisher).glob(f"{series}@*.parquet"))
    candidates.extend((VINTAGES / publisher).glob(f"{series}.parquet"))
    if not candidates:
        raise FileNotFoundError(f"No vintage found for {publisher}:{series}")
    return max(candidates, key=lambda p: p.name)


def write_table(df: pd.DataFrame, stem: str) -> dict[str, str]:
    DERIVED.mkdir(parents=True, exist_ok=True)
    csv_path = DERIVED / f"{stem}.csv"
    json_path = DERIVED / f"{stem}.json"
    parquet_path = DERIVED / f"{stem}.parquet"
    df.to_csv(csv_path, index=False)
    json_path.write_text(df.to_json(orient="records", indent=2) + "\n")
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    return {
        "csv_path": str(csv_path.relative_to(ROOT)),
        "csv_sha256": sha256(csv_path),
        "json_path": str(json_path.relative_to(ROOT)),
        "json_sha256": sha256(json_path),
        "parquet_path": str(parquet_path.relative_to(ROOT)),
        "parquet_sha256": sha256(parquet_path),
    }


def build_from_usdol(usdol_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    raw = pd.read_parquet(usdol_path)
    required = {"country_iso3", "unit_id", "state_abbr", "state_fips", "state_name"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{usdol_path.relative_to(ROOT)} is missing columns: {sorted(missing)}")

    states = (
        raw[list(required)]
        .dropna(subset=["country_iso3", "unit_id", "state_abbr", "state_fips", "state_name"])
        .drop_duplicates()
        .sort_values(["country_iso3", "state_fips", "state_abbr"])
        .reset_index(drop=True)
    )
    states["state_fips"] = states["state_fips"].astype(str).str.zfill(2)
    states["state_abbr"] = states["state_abbr"].astype(str).str.upper()
    states["country_name"] = states["country_iso3"].map({"USA": "United States"}).fillna(states["country_iso3"])
    states["ieset_state_id"] = states["unit_id"]
    states["iso_3166_2"] = states["unit_id"]
    states["admin1_code"] = states["state_abbr"]
    states["admin1_kind"] = states["state_fips"].map(
        lambda fips: "federal_district" if fips == "11" else ("territory" if fips in TERRITORY_FIPS else "state")
    )
    states["is_state_equivalent"] = True
    states["source_system"] = "usdol_state_minimum_wage_history"
    states["source_dataset"] = str(usdol_path.relative_to(ROOT))
    states["spine_note"] = (
        "U.S. admin1 v0 seeded from USDOL state minimum-wage history; "
        "global admin1 anchors should extend this table in later waves."
    )

    universe_cols = [
        "ieset_state_id",
        "country_iso3",
        "country_name",
        "state_name",
        "state_abbr",
        "state_fips",
        "iso_3166_2",
        "admin1_code",
        "admin1_kind",
        "is_state_equivalent",
        "source_system",
        "source_dataset",
        "spine_note",
    ]
    universe = states[universe_cols].copy()

    crosswalk_rows: list[dict[str, Any]] = []
    for rec in universe.to_dict(orient="records"):
        crosswalk_rows.append(
            {
                "ieset_state_id": rec["ieset_state_id"],
                "source_system": "iso_3166_2",
                "source_id": rec["iso_3166_2"],
                "source_name": rec["state_name"],
                "source_country_iso3": rec["country_iso3"],
                "match_type": "native_code",
                "match_score": 1.0,
                "manual_review_required": False,
                "source_id_column": "iso_3166_2",
                "source_name_column": "state_name",
            }
        )
        crosswalk_rows.append(
            {
                "ieset_state_id": rec["ieset_state_id"],
                "source_system": "us_fips_state",
                "source_id": rec["state_fips"],
                "source_name": rec["state_name"],
                "source_country_iso3": rec["country_iso3"],
                "match_type": "native_code",
                "match_score": 1.0,
                "manual_review_required": False,
                "source_id_column": "state_fips",
                "source_name_column": "state_name",
            }
        )
        crosswalk_rows.append(
            {
                "ieset_state_id": rec["ieset_state_id"],
                "source_system": "us_state_abbr",
                "source_id": rec["state_abbr"],
                "source_name": rec["state_name"],
                "source_country_iso3": rec["country_iso3"],
                "match_type": "native_code",
                "match_score": 1.0,
                "manual_review_required": False,
                "source_id_column": "state_abbr",
                "source_name_column": "state_name",
            }
        )
    crosswalks = pd.DataFrame(crosswalk_rows)

    stats = {
        "raw_rows": int(len(raw)),
        "admin1_rows": int(len(universe)),
        "country_count": int(universe["country_iso3"].nunique()),
        "state_rows": int((universe["admin1_kind"] == "state").sum()),
        "federal_district_rows": int((universe["admin1_kind"] == "federal_district").sum()),
        "territory_rows": int((universe["admin1_kind"] == "territory").sum()),
        "crosswalk_rows": int(len(crosswalks)),
        "source_columns": sorted(required),
    }
    return universe, crosswalks, stats


def write_manifest(run: str, usdol_path: Path, universe_artifacts: dict[str, str], crosswalk_artifacts: dict[str, str], stats: dict[str, Any]) -> Path:
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFESTS / f"fetch_run_{run}_state_spine.yaml"
    fetch_utc = datetime.now(tz=timezone.utc).isoformat()
    payload = {
        "run_utc": run,
        "pipeline": "state_spine_admin1",
        "entries": [
            {
                "publisher": "derived",
                "series_id": "state_universe_admin1",
                "source_url": "derived://usdol:state_minimum_wage_history",
                "methodology_url": "data/state_level/README.md",
                "license": "Derived from U.S. Department of Labor public data; global spine terms vary by future anchor",
                "fetch_utc": fetch_utc,
                "rows": stats["admin1_rows"],
                "frequency": "cross-section",
                "units": "admin1 state-equivalent units",
                "currency": None,
                "start_date": None,
                "end_date": None,
                "sha256": universe_artifacts["parquet_sha256"],
                "parquet_path": universe_artifacts["parquet_path"],
                "extra": {
                    "input_file": str(usdol_path.relative_to(ROOT)),
                    "input_sha256": sha256(usdol_path),
                    "stats": stats,
                    "artifacts": universe_artifacts,
                },
            },
            {
                "publisher": "derived",
                "series_id": "state_crosswalks",
                "source_url": "derived://usdol:state_minimum_wage_history",
                "methodology_url": "data/state_level/README.md",
                "license": "Derived from U.S. Department of Labor public data; global spine terms vary by future anchor",
                "fetch_utc": fetch_utc,
                "rows": stats["crosswalk_rows"],
                "frequency": "cross-section",
                "units": "admin1-source links",
                "currency": None,
                "start_date": None,
                "end_date": None,
                "sha256": crosswalk_artifacts["parquet_sha256"],
                "parquet_path": crosswalk_artifacts["parquet_path"],
                "extra": {
                    "input_file": str(usdol_path.relative_to(ROOT)),
                    "input_sha256": sha256(usdol_path),
                    "stats": stats,
                    "artifacts": crosswalk_artifacts,
                },
            },
        ],
    }
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--usdol-input",
        type=Path,
        default=None,
        help="Optional path to state_minimum_wage_history parquet. Defaults to latest vintage.",
    )
    args = parser.parse_args()

    try:
        usdol_path = args.usdol_input or latest_vintage("usdol", "state_minimum_wage_history")
        if not usdol_path.is_absolute():
            usdol_path = (ROOT / usdol_path).resolve()
        universe, crosswalks, stats = build_from_usdol(usdol_path)
    except Exception as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1

    universe_artifacts = write_table(universe, "state_universe_admin1")
    crosswalk_artifacts = write_table(crosswalks, "state_crosswalks")
    run = utc_stamp()
    manifest_path = write_manifest(run, usdol_path, universe_artifacts, crosswalk_artifacts, stats)
    print(
        json.dumps(
            {
                "status": "ok",
                "state_rows": stats["admin1_rows"],
                "crosswalk_rows": stats["crosswalk_rows"],
                "manifest": str(manifest_path.relative_to(ROOT)),
                "state_universe": universe_artifacts["parquet_path"],
                "state_crosswalks": crosswalk_artifacts["parquet_path"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
