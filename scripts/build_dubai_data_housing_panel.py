#!/usr/bin/env python3
"""Build Dubai rent-index and building-supply panel from official Data Dubai JSON."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
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

SOURCE_URL = "https://data.dubai/"
METHODOLOGY_URL = "https://data.dubai/en/"
LICENSE = "Data Dubai open data terms; verify per dataset metadata"
SOURCE_DATASET = "Data Dubai residential rent price index and building supply statistics"
DUBAI_IESET_CITY_ID = "ghsl_ucdb_r2024a:1007"

DATASETS = {
    "residential_rent_price_index": {
        "dataset_id": "250159075",
        "source_name": "Residential Rent Price Index",
        "unit": "index",
    },
    "building_permits": {
        "dataset_id": "724747",
        "source_name": "Building Permits Statistics",
        "unit": None,
    },
    "completed_buildings": {
        "dataset_id": "725256",
        "source_name": "Completed Buildings Statistics",
        "unit": None,
    },
}

AR_DESCRIPTION_COL = "\u0627\u0644\u0648\u0635\u0641"
AR_TYPE_COL = "\u0627\u0644\u0646\u0648\u0639"
AR_TITLE_COL = "\u0627\u0644\u0639\u0646\u0648\u0627\u0646"

MONTHS = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
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


def normalise_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def dataset_url(dataset_key: str) -> str:
    dataset_id = DATASETS[dataset_key]["dataset_id"]
    return f"https://data.dubai/o/dda/data-services/dataset-metadata?datasetId={dataset_id}&download=true"


def fetch_dataset(dataset_key: str, timeout: int = 120) -> list[dict[str, Any]]:
    response = requests.get(dataset_url(dataset_key), timeout=timeout, headers={"User-Agent": "IESET city-level data builder"})
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise ValueError(f"Data Dubai returned unsuccessful payload for {dataset_key}: {payload.get('message')}")
    rows = payload.get("data") or []
    if not isinstance(rows, list):
        raise ValueError(f"Data Dubai payload for {dataset_key} did not contain a row list")
    return rows


def load_input(path: Path) -> dict[str, list[dict[str, Any]]]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and all(key in payload for key in DATASETS):
        return payload
    if isinstance(payload, dict) and "datasets" in payload:
        return payload["datasets"]
    raise ValueError(f"expected JSON mapping with dataset keys in {path}")


def parse_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text.lower() in {"", "nan", "none", "-"}:
        return None
    text = re.sub(r"[^0-9.+-]", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    number = parse_number(value)
    return None if number is None else int(number)


def month_number(row: dict[str, Any]) -> int | None:
    direct = parse_int(row.get("Month_Number"))
    if direct:
        return direct
    text = normalise_name(row.get("Month"))
    return MONTHS.get(text)


def quarter_number(row: dict[str, Any]) -> int | None:
    direct = parse_int(row.get("Quarter_Number"))
    if direct:
        return direct
    text = normalise_name(row.get("Quarter"))
    for word, number in [("FIRST", 1), ("SECOND", 2), ("THIRD", 3), ("FOURTH", 4)]:
        if word in text:
            return number
    return None


def period_from_row(row: dict[str, Any]) -> tuple[int | None, int | None, str | None]:
    year = parse_int(row.get("Year"))
    month = month_number(row)
    if year is None or month is None:
        return year, month, None
    return year, month, f"{year:04d}-{month:02d}"


def dubai_city_record(city_spine_path: Path) -> dict[str, Any]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_parquet(city_spine_path) if city_spine_path.suffix.lower() == ".parquet" else pd.read_csv(city_spine_path)
    match = spine[spine["ieset_city_id"].eq(DUBAI_IESET_CITY_ID)]
    if match.empty:
        match = spine[spine["city_name"].eq("Dubai")]
    if match.empty:
        raise ValueError("could not find Dubai in city spine")
    row = match.iloc[0].to_dict()
    return {
        "ieset_city_id": row["ieset_city_id"],
        "ghsl_city_name": row["city_name"],
        "ghsl_city_rank_2025": int(row["city_rank_2025"]),
    }


def base_row(row: dict[str, Any], city: dict[str, Any], dataset_key: str) -> dict[str, Any]:
    year, month, period = period_from_row(row)
    quarter = quarter_number(row)
    return {
        "period": period,
        "period_type": "month",
        "year": year,
        "month": month,
        "quarter": quarter,
        "country_name": "United Arab Emirates",
        "city_name": "Dubai",
        "ieset_city_id": city["ieset_city_id"],
        "ghsl_city_name": city["ghsl_city_name"],
        "ghsl_city_rank_2025": city["ghsl_city_rank_2025"],
        "match_type": "dubai_city_assignment",
        "manual_review_required": False,
        "source_dataset_key": dataset_key,
        "source_dataset": SOURCE_DATASET,
        "source_name": DATASETS[dataset_key]["source_name"],
        "source_dataset_id": DATASETS[dataset_key]["dataset_id"],
        "source_url": dataset_url(dataset_key),
        "quarter_label": row.get("Quarter"),
        "month_label": row.get("Month"),
        "sort_id": parse_int(row.get("sort_id")),
    }


def housing_supply_relevant(value: object) -> bool:
    text = normalise_name(value)
    if not text:
        return False
    tokens = ["VILLA", "VILLAS", "MULTI STOREY", "RESIDENTIAL", "APARTMENT", "APARTMENTS"]
    return any(token in text for token in tokens)


def rows_from_rent_index(rows: list[dict[str, Any]], city: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        value = parse_number(row.get("Value"))
        year, month, period = period_from_row(row)
        if value is None or period is None:
            continue
        type_label = str(row.get("Type") or "").strip()
        out.append(
            {
                **base_row(row, city, "residential_rent_price_index"),
                "measure": "residential_rent_price_index",
                "statistic": "index_value",
                "segment": type_label,
                "segment_norm": normalise_name(type_label),
                "building_type": None,
                "activity": None,
                "value": value,
                "unit": "index",
                "weight": parse_number(row.get("Weight")),
                "housing_supply_relevant": False,
            }
        )
    return out


def rows_from_building_permits(rows: list[dict[str, Any]], city: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        value = parse_number(row.get("Value"))
        year, month, period = period_from_row(row)
        if value is None or period is None:
            continue
        title = str(row.get("Title") or "").strip()
        building_type = str(row.get("Type") or "").strip()
        statistic = "permit_count" if normalise_name(title) == "NUMBER" else "permit_area"
        unit = "count" if statistic == "permit_count" else "square_foot"
        out.append(
            {
                **base_row(row, city, "building_permits"),
                "measure": "building_permits",
                "statistic": statistic,
                "segment": title,
                "segment_norm": normalise_name(title),
                "building_type": building_type,
                "activity": str(row.get(AR_DESCRIPTION_COL) or row.get("Description") or "").strip(),
                "value": value,
                "unit": unit,
                "weight": None,
                "housing_supply_relevant": housing_supply_relevant(building_type),
            }
        )
    return out


def rows_from_completed_buildings(rows: list[dict[str, Any]], city: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        value = parse_number(row.get("Value"))
        year, month, period = period_from_row(row)
        if value is None or period is None:
            continue
        description = str(row.get("Description") or "").strip()
        building_type = str(row.get("Title") or "").strip()
        desc_norm = normalise_name(description)
        if desc_norm == "NUMBER":
            statistic = "completed_building_count"
            unit = "count"
        elif desc_norm == "AREA":
            statistic = "completed_building_area"
            unit = "square_foot"
        elif desc_norm == "VALUE":
            statistic = "completed_building_value"
            unit = "million_aed_or_publisher_value"
        else:
            statistic = desc_norm.lower() or "value"
            unit = None
        out.append(
            {
                **base_row(row, city, "completed_buildings"),
                "measure": "completed_buildings",
                "statistic": statistic,
                "segment": description,
                "segment_norm": desc_norm,
                "building_type": building_type,
                "activity": None,
                "value": value,
                "unit": unit,
                "weight": None,
                "housing_supply_relevant": housing_supply_relevant(building_type),
            }
        )
    return out


def build_panel(
    *,
    city_spine_path: Path,
    datasets: dict[str, list[dict[str, Any]]] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    city = dubai_city_record(city_spine_path)
    if datasets is None:
        datasets = {dataset_key: fetch_dataset(dataset_key) for dataset_key in DATASETS}
    rows: list[dict[str, Any]] = []
    rows.extend(rows_from_rent_index(datasets.get("residential_rent_price_index", []), city))
    rows.extend(rows_from_building_permits(datasets.get("building_permits", []), city))
    rows.extend(rows_from_completed_buildings(datasets.get("completed_buildings", []), city))
    if not rows:
        raise ValueError("Data Dubai housing endpoints returned no usable rows")
    panel = pd.DataFrame(rows)
    panel = panel.dropna(subset=["period", "value"]).copy()
    panel["year"] = panel["year"].astype(int)
    panel["month"] = panel["month"].astype(int)
    panel["quarter"] = panel["quarter"].astype("Int64")
    panel["value"] = pd.to_numeric(panel["value"], errors="coerce")
    panel["housing_supply_relevant"] = panel["housing_supply_relevant"].astype(bool)
    ordered = [
        "period",
        "period_type",
        "year",
        "month",
        "quarter",
        "quarter_label",
        "month_label",
        "country_name",
        "city_name",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "source_dataset_key",
        "measure",
        "statistic",
        "segment",
        "segment_norm",
        "building_type",
        "activity",
        "value",
        "unit",
        "weight",
        "housing_supply_relevant",
        "sort_id",
        "source_dataset",
        "source_name",
        "source_dataset_id",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["source_dataset_key", "period", "sort_id", "segment_norm"]).reset_index(drop=True)
    rent_rows = panel["source_dataset_key"].eq("residential_rent_price_index")
    permit_rows = panel["source_dataset_key"].eq("building_permits") & panel["housing_supply_relevant"]
    completed_rows = panel["source_dataset_key"].eq("completed_buildings") & panel["housing_supply_relevant"]
    stats = {
        "panel_rows": int(len(panel)),
        "start_period": str(panel["period"].min()),
        "end_period": str(panel["period"].max()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "rent_index_rows": int(rent_rows.sum()),
        "rent_index_segments": int(panel.loc[rent_rows, "segment_norm"].nunique()),
        "building_permit_rows": int(permit_rows.sum()),
        "completed_building_rows": int(completed_rows.sum()),
        "housing_supply_relevant_rows": int(panel["housing_supply_relevant"].sum()),
        "source_endpoints": {key: dataset_url(key) for key in DATASETS},
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_dubai_data_housing.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "dubai_data_housing_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="data_dubai",
        series_id="dubai_data_housing_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="monthly",
        units="rent index, counts, area, and values",
        currency="AED",
        start_date=stats["start_period"],
        end_date=stats["end_period"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Official Data Dubai JSON rows normalized to Dubai month, source dataset, measure, "
                "segment, and building-type observations with a residential supply relevance flag."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional JSON mapping of Data Dubai dataset keys to row lists.")
    parser.add_argument("--output", default="data/derived/dubai_data_housing_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    datasets = load_input(path_arg(args.input).resolve()) if args.input else None
    panel, stats = build_panel(city_spine_path=path_arg(args.city_spine).resolve(), datasets=datasets)
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK data_dubai:dubai_data_housing_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
