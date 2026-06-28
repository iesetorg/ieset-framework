#!/usr/bin/env python3
"""Build a U.S. place-year housing permit panel from Census BPS compiled data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import re
import sys
import unicodedata
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location("ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py")
    if spec is None or spec.loader is None:
        raise ImportError("Could not load data/fetchers/_base.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FETCHER_BASE = load_fetcher_base()
FetchResult = _FETCHER_BASE.FetchResult
utc_now = _FETCHER_BASE.utc_now
utc_stamp = _FETCHER_BASE.utc_stamp

SOURCE_URL = "https://www2.census.gov/econ/bps/Master%20Data%20Set/BPS_Compiled_File_202604.zip"
METHODOLOGY_URL = "https://www.census.gov/construction/bps/"
LICENSE = "U.S. Census Bureau public data; verify table metadata"
SOURCE_DATASET = "U.S. Census Building Permits Survey compiled file, annual place records"

STATE_ABBR = {
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
}

PILOT_ALIAS_OVERRIDES = {
    ("SAN FRANCISCO", "06"): "SAN FRANCISCO",
    ("SAINT PAUL", "27"): "SAINT PAUL",
    ("MINNEAPOLIS", "27"): "MINNEAPOLIS",
    ("LOS ANGELES", "06"): "LOS ANGELES",
}

NUMERIC_COLUMNS = [
    "BLDGS_1_UNIT",
    "BLDGS_1_UNIT_REP",
    "BLDGS_2_UNITS",
    "BLDGS_2_UNITS_REP",
    "BLDGS_3_4_UNITS",
    "BLDGS_3_4_UNITS_REP",
    "BLDGS_5_UNITS",
    "BLDGS_5_UNITS_REP",
    "TOTAL_BLDGS",
    "TOTAL_BLDGS_REP",
    "TOTAL_UNITS",
    "TOTAL_UNITS_REP",
    "TOTAL_VALUE",
    "TOTAL_VALUE_REP",
    "UNITS_1_UNIT",
    "UNITS_1_UNIT_REP",
    "UNITS_2_UNITS",
    "UNITS_2_UNITS_REP",
    "UNITS_3_4_UNITS",
    "UNITS_3_4_UNITS_REP",
    "UNITS_5_UNITS",
    "UNITS_5_UNITS_REP",
    "VALUE_1_UNIT",
    "VALUE_1_UNIT_REP",
    "VALUE_2_UNITS",
    "VALUE_2_UNITS_REP",
    "VALUE_3_4_UNITS",
    "VALUE_3_4_UNITS_REP",
    "VALUE_5_UNITS",
    "VALUE_5_UNITS_REP",
    "POP",
]

KEEP_COLUMNS = [
    "UNIQUE_PLACE_ID",
    "STATE_CODE",
    "STATE_NAME",
    "CENSUS_PLACE_CODE",
    "FIPS_PLACE_CODE",
    "COUNTY_CODE",
    "COUNTY_NAME",
    "PLACE_NAME",
    "LOCATION_NAME",
    "CBSA_CODE",
    "CBSA_NAME",
    "ZIP_CODE",
    "YEAR",
    "SURVEY_DATE",
    "FILE_NAME",
    *NUMERIC_COLUMNS,
]


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fetch_utc(value: str | None) -> datetime:
    if not value:
        return utc_now()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def normalise_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"\bST[. ]+", "SAINT ", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\b(CITY|TOWN|VILLAGE|BOROUGH|CDP|MUNICIPALITY)\b", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def city_aliases(city_name: object) -> set[str]:
    text = "" if pd.isna(city_name) else str(city_name)
    aliases = {normalise_name(text)}
    if "[" in text and "]" in text:
        before = text.split("[", 1)[0]
        inside = text.split("[", 1)[1].split("]", 1)[0]
        aliases.add(normalise_name(before))
        aliases.add(normalise_name(inside))
    for alias in list(aliases):
        if alias.endswith(" CITY"):
            aliases.add(alias[: -len(" CITY")].strip())
    return {alias for alias in aliases if alias}


def build_spine_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    us_spine = city_spine[city_spine["country_name"].eq("United States")].copy()
    candidates: dict[str, list[dict[str, Any]]] = {}
    for row in us_spine.to_dict("records"):
        canonical_alias = normalise_name(row["city_name"])
        for alias in city_aliases(row["city_name"]):
            candidates.setdefault(alias, []).append(
                {
                    "ieset_city_id": row["ieset_city_id"],
                    "ghsl_city_name": row["city_name"],
                    "ghsl_city_rank_2025": row["city_rank_2025"],
                    "match_type": "normalized_name" if alias == canonical_alias else "ghsl_alias",
                    "manual_review_required": bool(alias != canonical_alias or "[" in str(row["city_name"])),
                }
            )

    out = {}
    for alias, records in candidates.items():
        if len({record["ieset_city_id"] for record in records}) == 1:
            out[alias] = records[0]
    return out


def open_compiled_csv(path: Path):
    if path.suffix.lower() == ".zip":
        archive = zipfile.ZipFile(path)
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            archive.close()
            raise ValueError(f"expected exactly one CSV member in {path}, found {members}")
        raw = archive.open(members[0])
        return archive, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
    return None, path.open("r", encoding="utf-8-sig", newline="")


def load_place_annual_rows(input_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"missing Census BPS input: {input_path}. Download {SOURCE_URL} into {rel(input_path)}."
        )
    records: list[dict[str, Any]] = []
    raw_rows = 0
    archive, handle = open_compiled_csv(input_path)
    try:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_rows += 1
            if row.get("LOCATION_TYPE") != "Place" or row.get("PERIOD") != "Annual":
                continue
            records.append({column: row.get(column) for column in KEEP_COLUMNS})
    finally:
        handle.close()
        if archive is not None:
            archive.close()

    if not records:
        raise ValueError("no Census BPS annual place records found")
    frame = pd.DataFrame(records)
    return frame, {"raw_rows_scanned": raw_rows, "place_annual_rows": len(frame)}


def clean_code(value: object, width: int | None = None) -> str | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if width:
        text = text.zfill(width)
    return text


def build_panel(input_path: Path, city_spine_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw, stats = load_place_annual_rows(input_path)
    city_spine = pd.read_csv(city_spine_path)

    for column in NUMERIC_COLUMNS:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    raw["year"] = pd.to_numeric(raw["YEAR"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["year"]).copy()
    raw["year"] = raw["year"].astype(int)
    raw["state_code"] = raw["STATE_CODE"].map(lambda value: clean_code(value, 2))
    raw["state"] = raw["state_code"].map(STATE_ABBR)
    raw["state_name"] = raw["STATE_NAME"].where(raw["STATE_NAME"].astype(str).str.strip().ne(""), pd.NA)
    raw["census_place_code"] = raw["CENSUS_PLACE_CODE"].map(lambda value: clean_code(value))
    raw["fips_place_code"] = raw["FIPS_PLACE_CODE"].map(lambda value: clean_code(value, 5) if clean_code(value) else None)
    raw["census_unique_place_id"] = raw["UNIQUE_PLACE_ID"].map(lambda value: clean_code(value))
    raw["permit_place_name_norm"] = raw["PLACE_NAME"].map(normalise_name)

    name_state_counts = raw.groupby("permit_place_name_norm")["state_code"].nunique(dropna=True).to_dict()
    spine_aliases = build_spine_alias_map(city_spine)
    match_rows = []
    places = raw[["census_unique_place_id", "PLACE_NAME", "state_code", "permit_place_name_norm"]].drop_duplicates()
    for row in places.to_dict("records"):
        alias = PILOT_ALIAS_OVERRIDES.get((row["permit_place_name_norm"], row["state_code"]), row["permit_place_name_norm"])
        match = spine_aliases.get(alias)
        ambiguous_name = name_state_counts.get(row["permit_place_name_norm"], 0) > 1
        if match and (not ambiguous_name or (row["permit_place_name_norm"], row["state_code"]) in PILOT_ALIAS_OVERRIDES):
            match_rows.append(
                {
                    "census_unique_place_id": row["census_unique_place_id"],
                    "state_code": row["state_code"],
                    "permit_place_name_norm": row["permit_place_name_norm"],
                    **match,
                    "census_match_name": alias,
                    "census_name_ambiguous": bool(ambiguous_name),
                }
            )
        else:
            match_rows.append(
                {
                    "census_unique_place_id": row["census_unique_place_id"],
                    "state_code": row["state_code"],
                    "permit_place_name_norm": row["permit_place_name_norm"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                    "census_match_name": alias,
                    "census_name_ambiguous": bool(ambiguous_name),
                }
            )
    match_key = ["census_unique_place_id", "state_code", "permit_place_name_norm"]
    matches = pd.DataFrame(match_rows).drop_duplicates(subset=match_key, keep="first")

    panel = raw.merge(matches, on=match_key, how="left")
    panel = panel.rename(
        columns={
            "PLACE_NAME": "permit_place_name",
            "LOCATION_NAME": "permit_location_name",
            "COUNTY_CODE": "county_code",
            "COUNTY_NAME": "county_name",
            "CBSA_CODE": "cbsa_code",
            "CBSA_NAME": "cbsa_name",
            "ZIP_CODE": "zip_code",
            "SURVEY_DATE": "survey_date",
            "FILE_NAME": "source_file_name",
            "TOTAL_BLDGS": "total_buildings",
            "TOTAL_BLDGS_REP": "total_buildings_reported",
            "TOTAL_UNITS": "total_units",
            "TOTAL_UNITS_REP": "total_units_reported",
            "TOTAL_VALUE": "total_value_usd",
            "TOTAL_VALUE_REP": "total_value_reported_usd",
            "UNITS_1_UNIT": "units_1_unit",
            "UNITS_1_UNIT_REP": "units_1_unit_reported",
            "UNITS_2_UNITS": "units_2_units",
            "UNITS_2_UNITS_REP": "units_2_units_reported",
            "UNITS_3_4_UNITS": "units_3_4_units",
            "UNITS_3_4_UNITS_REP": "units_3_4_units_reported",
            "UNITS_5_UNITS": "units_5_units",
            "UNITS_5_UNITS_REP": "units_5_units_reported",
            "BLDGS_1_UNIT": "buildings_1_unit",
            "BLDGS_1_UNIT_REP": "buildings_1_unit_reported",
            "BLDGS_2_UNITS": "buildings_2_units",
            "BLDGS_2_UNITS_REP": "buildings_2_units_reported",
            "BLDGS_3_4_UNITS": "buildings_3_4_units",
            "BLDGS_3_4_UNITS_REP": "buildings_3_4_units_reported",
            "BLDGS_5_UNITS": "buildings_5_units",
            "BLDGS_5_UNITS_REP": "buildings_5_units_reported",
            "VALUE_1_UNIT": "value_1_unit_usd",
            "VALUE_1_UNIT_REP": "value_1_unit_reported_usd",
            "VALUE_2_UNITS": "value_2_units_usd",
            "VALUE_2_UNITS_REP": "value_2_units_reported_usd",
            "VALUE_3_4_UNITS": "value_3_4_units_usd",
            "VALUE_3_4_UNITS_REP": "value_3_4_units_reported_usd",
            "VALUE_5_UNITS": "value_5_units_usd",
            "VALUE_5_UNITS_REP": "value_5_units_reported_usd",
            "POP": "permit_population",
        }
    )
    keep = [
        "census_unique_place_id",
        "year",
        "permit_place_name",
        "permit_location_name",
        "permit_place_name_norm",
        "state_code",
        "state",
        "state_name",
        "census_place_code",
        "fips_place_code",
        "county_code",
        "county_name",
        "cbsa_code",
        "cbsa_name",
        "zip_code",
        "permit_population",
        "total_units",
        "total_units_reported",
        "units_1_unit",
        "units_1_unit_reported",
        "units_2_units",
        "units_2_units_reported",
        "units_3_4_units",
        "units_3_4_units_reported",
        "units_5_units",
        "units_5_units_reported",
        "total_buildings",
        "total_buildings_reported",
        "buildings_1_unit",
        "buildings_1_unit_reported",
        "buildings_2_units",
        "buildings_2_units_reported",
        "buildings_3_4_units",
        "buildings_3_4_units_reported",
        "buildings_5_units",
        "buildings_5_units_reported",
        "total_value_usd",
        "total_value_reported_usd",
        "value_1_unit_usd",
        "value_1_unit_reported_usd",
        "value_2_units_usd",
        "value_2_units_reported_usd",
        "value_3_4_units_usd",
        "value_3_4_units_reported_usd",
        "value_5_units_usd",
        "value_5_units_reported_usd",
        "survey_date",
        "source_file_name",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "census_match_name",
        "census_name_ambiguous",
    ]
    panel = panel[keep].sort_values(["state_code", "permit_place_name", "year"]).reset_index(drop=True)
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = SOURCE_URL

    stats.update(
        {
            "panel_rows": int(len(panel)),
            "start_year": int(panel["year"].min()),
            "end_year": int(panel["year"].max()),
            "unique_places": int(panel["census_unique_place_id"].nunique()),
            "matched_places": int(panel[["census_unique_place_id", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
            "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
            "unique_ieset_city_ids": int(panel["ieset_city_id"].dropna().nunique()),
            "ambiguous_name_places": int(matches["census_name_ambiguous"].sum()),
            "source_zip_sha256": sha256_path(input_path),
        }
    )
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_census_bps_city_permits.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "us_census_bps_city_permits_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], input_path: Path, output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="us_census",
        series_id="us_city_permits_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="permits, buildings, housing units, and permit value",
        currency="USD",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "input_file": rel(input_path),
            "input_sha256": stats["source_zip_sha256"],
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "crosswalk_rule": (
                "Attach IESET city ids only for unambiguous normalized Census place names "
                "or explicit pilot aliases keyed by FIPS state code; duplicate place names remain manual-review."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/city_level/BPS_Compiled_File_202604.zip")
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.csv")
    parser.add_argument("--output", default="data/derived/us_city_permits_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_path = path_arg(args.input).resolve()
    output_path = path_arg(args.output).resolve()
    panel, stats = build_panel(input_path, path_arg(args.city_spine).resolve())
    result = emit(panel, stats, input_path, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK us_census:us_city_permits_panel "
        f"rows={result.rows} places={stats['unique_places']} matched_places={stats['matched_places']} "
        f"ieset_cities={stats['unique_ieset_city_ids']} period={result.start_date}->{result.end_date}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
