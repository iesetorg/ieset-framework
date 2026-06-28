#!/usr/bin/env python3
"""Build an NYC housing supply/quality panel from pinned NYC Open Data views."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

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

SOCRATA_DOMAIN = "https://data.cityofnewyork.us"
SOURCE_URL = "https://opendata.cityofnewyork.us/"
METHODOLOGY_URL = "https://opendata.cityofnewyork.us/"
LICENSE = "NYC Open Data terms; verify per dataset metadata"
NYC_IESET_CITY_ID = "ghsl_ucdb_r2024a:8099"

DATASETS = {
    "dob_permit_issuance": {
        "id": "ipu4-2q9a",
        "name": "DOB Permit Issuance",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-Development/DOB-Permit-Issuance/ipu4-2q9a",
        "publisher": "NYC Department of Buildings",
        "measure_name": "dob_permit_records",
    },
    "hpd_complaint_problem": {
        "id": "ygpa-z7cr",
        "name": "Housing Maintenance Code Complaints and Problems",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-Development/Housing-Maintenance-Code-Complaints-and-Problems/ygpa-z7cr",
        "publisher": "NYC Department of Housing Preservation and Development",
        "measure_name": "hpd_complaint_problems",
    },
    "hpd_violation": {
        "id": "wvxf-dwi5",
        "name": "Housing Maintenance Code Violations",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-Development/Housing-Maintenance-Code-Violations/wvxf-dwi5",
        "publisher": "NYC Department of Housing Preservation and Development",
        "measure_name": "hpd_violations",
    },
}

BOROUGH_ALIASES = {
    "1": "MANHATTAN",
    "2": "BRONX",
    "3": "BROOKLYN",
    "4": "QUEENS",
    "5": "STATEN ISLAND",
    "MN": "MANHATTAN",
    "BX": "BRONX",
    "BK": "BROOKLYN",
    "QN": "QUEENS",
    "SI": "STATEN ISLAND",
    "NEW YORK": "MANHATTAN",
    "RICHMOND": "STATEN ISLAND",
}


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


def clean_text(value: object, default: str = "UNKNOWN") -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def parse_int(value: object, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value)))
    except ValueError:
        return default


def normalize_borough(value: object) -> str:
    text = clean_text(value).upper().replace("_", " ")
    text = " ".join(text.split())
    return BOROUGH_ALIASES.get(text, text)


def fetch_query(dataset_id: str, query: str) -> list[dict[str, Any]]:
    url = f"{SOCRATA_DOMAIN}/resource/{dataset_id}.json?" + urllib.parse.urlencode({"$query": query})
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def fetch_metadata(dataset_id: str) -> dict[str, Any]:
    url = f"{SOCRATA_DOMAIN}/api/views/{dataset_id}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    return {
        "id": dataset_id,
        "name": payload.get("name"),
        "attribution": payload.get("attribution"),
        "rows_updated_at": payload.get("rowsUpdatedAt"),
        "columns": [column.get("fieldName") for column in payload.get("columns", []) if column.get("fieldName")],
    }


def nyc_city_record(city_spine_path: Path) -> dict[str, Any]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path)
    match = spine[spine["ieset_city_id"].eq(NYC_IESET_CITY_ID)]
    if match.empty:
        match = spine[spine["city_name"].eq("New York City")]
    if match.empty:
        raise ValueError("could not find New York City in city spine")
    row = match.iloc[0].to_dict()
    return {
        "ieset_city_id": row["ieset_city_id"],
        "city_name": row["city_name"],
        "ghsl_city_rank_2025": int(row["city_rank_2025"]),
        "country_name": row["country_name"],
    }


def dob_queries(start_year: int, end_year: int) -> list[tuple[int, str]]:
    queries = []
    for year in range(start_year, end_year + 1):
        queries.append(
            (
                year,
                "select borough, job_type, permit_type, residential, permit_status, filing_status, "
                f"count(*) as value where issuance_date like '%{year}' "
                "group by borough, job_type, permit_type, residential, permit_status, filing_status "
                "limit 50000",
            )
        )
    return queries


def hpd_complaint_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(received_date) as year, borough, major_category, type, complaint_status, "
        "count(*) as value "
        f"where received_date between '{start_year}-01-01T00:00:00' and '{end_year}-12-31T23:59:59' "
        "group by year, borough, major_category, type, complaint_status "
        "order by year, borough, major_category, type, complaint_status "
        "limit 50000"
    )


def hpd_violation_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(inspectiondate) as year, boro, class, rentimpairing, violationstatus, "
        "count(*) as value "
        f"where inspectiondate between '{start_year}-01-01T00:00:00' and '{end_year}-12-31T23:59:59' "
        "group by year, boro, class, rentimpairing, violationstatus "
        "order by year, boro, class, rentimpairing, violationstatus "
        "limit 50000"
    )


def base_row(city: dict[str, Any], dataset_key: str, year: int, borough: object, value: object) -> dict[str, Any]:
    dataset = DATASETS[dataset_key]
    return {
        **city,
        "year": int(year),
        "geography_level": "nyc_borough",
        "borough": normalize_borough(borough),
        "source_dataset_key": dataset_key,
        "source_dataset_id": dataset["id"],
        "source_dataset_name": dataset["name"],
        "source_url": dataset["source_url"],
        "publisher": dataset["publisher"],
        "measure_name": dataset["measure_name"],
        "value": parse_int(value),
        "manual_review_required": False,
    }


def dob_rows(city: dict[str, Any], fetcher: Callable[[str, str], list[dict[str, Any]]], start_year: int, end_year: int) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    queries: list[str] = []
    dataset_id = DATASETS["dob_permit_issuance"]["id"]
    for year, query in dob_queries(start_year, end_year):
        queries.append(query)
        for item in fetcher(dataset_id, query):
            row = base_row(city, "dob_permit_issuance", year, item.get("borough"), item.get("value"))
            row.update(
                {
                    "category_1": clean_text(item.get("permit_type")),
                    "category_2": clean_text(item.get("job_type")),
                    "category_3": clean_text(item.get("residential"), "UNSPECIFIED"),
                    "category_4": clean_text(item.get("permit_status")),
                    "category_5": clean_text(item.get("filing_status")),
                }
            )
            rows.append(row)
        time.sleep(0.05)
    return rows, queries


def hpd_complaint_rows(city: dict[str, Any], fetcher: Callable[[str, str], list[dict[str, Any]]], start_year: int, end_year: int) -> tuple[list[dict[str, Any]], str]:
    query = hpd_complaint_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["hpd_complaint_problem"]["id"], query):
        row = base_row(city, "hpd_complaint_problem", parse_int(item.get("year")), item.get("borough"), item.get("value"))
        row.update(
            {
                "category_1": clean_text(item.get("major_category")),
                "category_2": clean_text(item.get("type")),
                "category_3": clean_text(item.get("complaint_status")),
                "category_4": "NA",
                "category_5": "NA",
            }
        )
        rows.append(row)
    return rows, query


def hpd_violation_rows(city: dict[str, Any], fetcher: Callable[[str, str], list[dict[str, Any]]], start_year: int, end_year: int) -> tuple[list[dict[str, Any]], str]:
    query = hpd_violation_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["hpd_violation"]["id"], query):
        row = base_row(city, "hpd_violation", parse_int(item.get("year")), item.get("boro"), item.get("value"))
        row.update(
            {
                "category_1": clean_text(item.get("class")),
                "category_2": clean_text(item.get("rentimpairing")),
                "category_3": clean_text(item.get("violationstatus")),
                "category_4": "NA",
                "category_5": "NA",
            }
        )
        rows.append(row)
    return rows, query


def build_panel(
    *,
    city_spine_path: Path,
    start_year: int,
    end_year: int,
    fetcher: Callable[[str, str], list[dict[str, Any]]] = fetch_query,
    metadata_fetcher: Callable[[str], dict[str, Any]] = fetch_metadata,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    city = nyc_city_record(city_spine_path)
    all_rows: list[dict[str, Any]] = []
    query_log: dict[str, Any] = {}

    rows, queries = dob_rows(city, fetcher, start_year, end_year)
    all_rows.extend(rows)
    query_log["dob_permit_issuance"] = queries

    rows, query = hpd_complaint_rows(city, fetcher, start_year, end_year)
    all_rows.extend(rows)
    query_log["hpd_complaint_problem"] = [query]

    rows, query = hpd_violation_rows(city, fetcher, start_year, end_year)
    all_rows.extend(rows)
    query_log["hpd_violation"] = [query]

    if not all_rows:
        raise ValueError("NYC Open Data queries returned no aggregate rows")

    panel = pd.DataFrame(all_rows)
    columns = [
        "ieset_city_id",
        "city_name",
        "ghsl_city_rank_2025",
        "country_name",
        "year",
        "geography_level",
        "borough",
        "source_dataset_key",
        "source_dataset_id",
        "source_dataset_name",
        "publisher",
        "measure_name",
        "category_1",
        "category_2",
        "category_3",
        "category_4",
        "category_5",
        "value",
        "manual_review_required",
        "source_url",
    ]
    panel = panel[columns].sort_values(
        ["source_dataset_key", "year", "borough", "category_1", "category_2", "category_3", "category_4", "category_5"]
    ).reset_index(drop=True)

    metadata = {key: metadata_fetcher(spec["id"]) for key, spec in DATASETS.items()}
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "borough_count": int(panel["borough"].nunique()),
        "datasets": {
            key: {
                "rows": int((panel["source_dataset_key"] == key).sum()),
                "value_sum": int(panel.loc[panel["source_dataset_key"] == key, "value"].sum()),
            }
            for key in DATASETS
        },
        "query_count": sum(len(items) for items in query_log.values()),
        "metadata": metadata,
        "queries": query_log,
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_nyc_housing_quality_supply.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "nyc_open_data_housing_quality_supply_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="nyc_open_data",
        series_id="us_city_rent_control_quality_leakage_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="annual aggregate counts",
        currency=None,
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Server-side Socrata aggregates by year, borough, and dataset-specific categories. "
                "All rows attach to GHSL New York City while preserving borough detail."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.csv")
    parser.add_argument("--output", default="data/derived/us_city_rent_control_quality_leakage_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--start-year", type=int, default=2007)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        start_year=args.start_year,
        end_year=args.end_year,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    dataset_summary = ", ".join(f"{key}={value['rows']}" for key, value in stats["datasets"].items())
    print(
        "OK nyc_open_data:us_city_rent_control_quality_leakage_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} {dataset_summary}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
