#!/usr/bin/env python3
"""Build the initial admin1/state identity spine.

The first landed spine is intentionally conservative: it mints stable U.S.
admin1 IDs from Census TIGER/Line state geographies and crosswalks them to the
FIPS-keyed and abbreviation-keyed panels already on disk. Global admin1 sources
are tracked in data/state_level/source_inventory.yaml and should extend this
builder once geoBoundaries/GADM/ISO-3166-2 inputs are dropped or fetched.
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


SOURCE_SYSTEM = "us_census_tiger_state_geographies"
SOURCE_URL = "derived://us_census:tiger_state_geographies"
SOURCE_LICENSE = (
    "Derived from U.S. Census Bureau TIGER/Line public-domain state geography "
    "data; global spine terms vary by future anchor"
)

TERRITORY_FIPS = {"60", "66", "69", "72", "78"}
FIPS_TO_ABBR = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "60": "AS",
    "66": "GU",
    "69": "MP",
    "72": "PR",
    "78": "VI",
}

STATE_FIPS_COLUMNS = ("STATEFP", "STATEFP10", "state_fips", "statefp", "state", "GEOID")
STATE_ABBR_COLUMNS = ("STUSPS", "USPS", "state_abbr", "state_abbreviation", "abbr", "postal")
STATE_NAME_COLUMNS = ("NAME", "STATE_NAME", "state_name", "name")


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


def latest_tiger_vintage() -> Path:
    """Return the newest local Census TIGER state geography vintage."""
    errors: list[str] = []
    for series in ("tiger_state_geographies", "us_census_tiger_state_geographies"):
        try:
            return latest_vintage("us_census", series)
        except FileNotFoundError as exc:
            errors.append(str(exc))
    raise FileNotFoundError("; ".join(errors))


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


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


def read_source_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str)
    if suffix == ".json":
        return pd.read_json(path)
    if suffix in {".geojson", ".shp", ".zip"}:
        try:
            import geopandas as gpd  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(f"Reading {suffix} TIGER inputs requires geopandas") from exc
        return pd.DataFrame(gpd.read_file(path))
    raise ValueError(f"Unsupported Census TIGER input format: {path.suffix}")


def find_column(df: pd.DataFrame, candidates: tuple[str, ...], *, required: bool = True) -> str | None:
    columns = list(df.columns)
    for candidate in candidates:
        if candidate in columns:
            return candidate
    by_lower = {str(column).lower(): str(column) for column in columns}
    for candidate in candidates:
        found = by_lower.get(candidate.lower())
        if found:
            return found
    if required:
        raise ValueError(f"missing expected columns; tried {list(candidates)}")
    return None


def normalise_state_fips(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    if not text:
        return None
    return text.zfill(2)


def build_from_census_tiger(tiger_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    raw = read_source_table(tiger_path)
    fips_col = find_column(raw, STATE_FIPS_COLUMNS)
    name_col = find_column(raw, STATE_NAME_COLUMNS)
    abbr_col = find_column(raw, STATE_ABBR_COLUMNS, required=False)

    states = pd.DataFrame(
        {
            "state_fips": raw[fips_col].map(normalise_state_fips),
            "state_name": raw[name_col].astype("string").str.strip(),
        }
    )
    if abbr_col:
        states["state_abbr"] = raw[abbr_col].astype("string").str.strip().str.upper()
    else:
        states["state_abbr"] = pd.NA

    missing_abbr = states["state_abbr"].isna() | states["state_abbr"].eq("")
    states.loc[missing_abbr, "state_abbr"] = states.loc[missing_abbr, "state_fips"].map(
        FIPS_TO_ABBR
    )
    states = (
        states.dropna(subset=["state_fips", "state_abbr", "state_name"])
        .drop_duplicates()
        .sort_values(["state_fips", "state_abbr"])
        .reset_index(drop=True)
    )
    if states["state_fips"].duplicated().any():
        duplicates = states.loc[states["state_fips"].duplicated(), "state_fips"].tolist()
        raise ValueError(f"duplicate Census TIGER STATEFP values: {duplicates}")
    if states["state_abbr"].isna().any() or states["state_abbr"].eq("").any():
        missing = states.loc[
            states["state_abbr"].isna() | states["state_abbr"].eq(""), "state_fips"
        ].tolist()
        raise ValueError(f"missing state abbreviations for FIPS codes: {missing}")

    states["country_iso3"] = "USA"
    states["country_name"] = "United States"
    states["ieset_state_id"] = "US-" + states["state_abbr"]
    states["iso_3166_2"] = states["ieset_state_id"]
    states["admin1_code"] = states["state_abbr"]
    states["admin1_kind"] = states["state_fips"].map(
        lambda fips: "federal_district"
        if fips == "11"
        else ("territory" if fips in TERRITORY_FIPS else "state")
    )
    states["is_state_equivalent"] = True
    states["source_system"] = SOURCE_SYSTEM
    states["source_dataset"] = display_path(tiger_path)
    states["spine_note"] = (
        "U.S. admin1 v0 anchored on Census TIGER/Line state geographies; "
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
        "source_columns": sorted(str(column) for column in raw.columns),
        "source_fips_column": fips_col,
        "source_abbr_column": abbr_col,
        "source_name_column": name_col,
    }
    return universe, crosswalks, stats


def write_manifest(
    run: str,
    tiger_path: Path,
    universe_artifacts: dict[str, str],
    crosswalk_artifacts: dict[str, str],
    stats: dict[str, Any],
) -> Path:
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
                "source_url": SOURCE_URL,
                "methodology_url": "data/state_level/README.md",
                "license": SOURCE_LICENSE,
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
                    "input_file": display_path(tiger_path),
                    "input_sha256": sha256(tiger_path),
                    "stats": stats,
                    "artifacts": universe_artifacts,
                },
            },
            {
                "publisher": "derived",
                "series_id": "state_crosswalks",
                "source_url": SOURCE_URL,
                "methodology_url": "data/state_level/README.md",
                "license": SOURCE_LICENSE,
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
                    "input_file": display_path(tiger_path),
                    "input_sha256": sha256(tiger_path),
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
        "--census-tiger-input",
        "--tiger-input",
        type=Path,
        default=None,
        help="Optional path to Census TIGER/Line state geography parquet/CSV/shapefile. Defaults to latest local vintage.",
    )
    args = parser.parse_args()

    try:
        tiger_path = args.census_tiger_input or latest_tiger_vintage()
        if not tiger_path.is_absolute():
            tiger_path = (ROOT / tiger_path).resolve()
        universe, crosswalks, stats = build_from_census_tiger(tiger_path)
    except Exception as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1

    universe_artifacts = write_table(universe, "state_universe_admin1")
    crosswalk_artifacts = write_table(crosswalks, "state_crosswalks")
    run = utc_stamp()
    manifest_path = write_manifest(run, tiger_path, universe_artifacts, crosswalk_artifacts, stats)
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
