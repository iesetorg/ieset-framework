#!/usr/bin/env python3
"""Build Sweden municipal rent, completions, and dwelling-stock panel from SCB PXWeb."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import re
import subprocess
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

SCB_API_ROOT = "https://api.scb.se/OV0104/v1/doris/en/ssd"
SOURCE_URL = "https://www.scb.se/en/services/open-data-api/"
LICENSE = "Statistics Sweden open data terms; verify per table"
METHODOLOGY_URL = SOURCE_URL
SOURCE_DATASET = "Statistics Sweden municipal housing PXWeb tables"

TABLES = {
    "completed_new_dwellings": {
        "path": "BO/BO0101/BO0101A/LghReHtypUfAr",
        "contents": ["0000005O"],
        "measure": "completed_new_dwellings",
        "frequency": "annual",
    },
    "dwelling_stock": {
        "path": "BO/BO0104/BO0104D/BO0104T04",
        "contents": ["BO0104AH"],
        "measure": "dwelling_stock",
        "frequency": "annual",
    },
    "municipal_rent_per_sqm": {
        "path": "BO/BO0406/BO0406E/BO0406Tab01",
        "contents": ["000000J4", "000000RZ"],
        "measure": "municipal_rent_per_sqm",
        "frequency": "annual",
    },
}

CITY_TO_REGION_CODE = {
    "STOCKHOLM": "0180",
    "GOTHENBURG": "1480",
}
REGION_CODE_TO_CITY = {value: key for key, value in CITY_TO_REGION_CODE.items()}

DIMENSION_COLUMNS = {
    "Region": ("region_code", "region_name"),
    "Hustyp": ("building_type_code", "building_type_label"),
    "Upplatelseform": ("tenure_code", "tenure_label"),
    "Hyresuppg": ("rental_data_code", "rental_data_label"),
    "ContentsCode": ("contents_code", "contents_label"),
    "Tid": ("year", "year_label"),
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


def table_url(table_key: str) -> str:
    return f"{SCB_API_ROOT}/{TABLES[table_key]['path']}"


def fetch_metadata(table_key: str, timeout: int = 60) -> dict[str, Any]:
    response = requests.get(table_url(table_key), timeout=timeout, headers={"User-Agent": "IESET city-level data builder"})
    response.raise_for_status()
    return response.json()


def post_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=(10, timeout),
            headers={"User-Agent": "IESET city-level data builder"},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        completed = subprocess.run(
            [
                "curl",
                "-L",
                "-sS",
                "--max-time",
                str(timeout),
                "-X",
                "POST",
                url,
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                json.dumps(payload, ensure_ascii=False),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)


def fetch_table(table_key: str, metadata: dict[str, Any], region_codes: list[str], timeout: int = 90) -> dict[str, Any]:
    table = TABLES[table_key]
    queries = []
    for variable in metadata["variables"]:
        code = variable["code"]
        values = list(variable["values"])
        if code == "Region":
            values = [region_code for region_code in region_codes if region_code in values]
        elif code == "ContentsCode":
            values = [value for value in table["contents"] if value in values]
        if not values:
            raise ValueError(f"no query values left for {table_key}:{code}")
        queries.append({"code": code, "selection": {"filter": "item", "values": values}})
    payload = {"query": queries, "response": {"format": "JSON-stat2"}}
    return post_json(table_url(table_key), payload, timeout)


def load_payloads(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and "payloads" in payload:
        payload = payload["payloads"]
    if not isinstance(payload, list):
        raise ValueError(f"expected JSON list of payload records in {path}")
    return payload


def ordered_codes(dimension: dict[str, Any]) -> list[str]:
    index = dimension["category"]["index"]
    if isinstance(index, list):
        return [str(value) for value in index]
    return [code for code, _ in sorted(index.items(), key=lambda item: item[1])]


def value_at(values: Any, offset: int) -> Any:
    if isinstance(values, dict):
        return values.get(str(offset))
    if offset >= len(values):
        return None
    return values[offset]


def statistic_from_contents(contents_code: str, contents_label: str | None) -> str:
    label = normalise_name(contents_label or "")
    if "MEDIAN" in label:
        return "median"
    if "AVERAGE" in label:
        return "average"
    if "NUMBER" in label:
        return "count"
    if contents_code in {"000000J4"}:
        return "median"
    if contents_code in {"000000RZ"}:
        return "average"
    return "count"


def jsonstat_rows(table_key: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    ids = payload["id"]
    sizes = payload["size"]
    dimensions = payload["dimension"]
    code_lists = [ordered_codes(dimensions[dim_id]) for dim_id in ids]
    values = payload.get("value") or []
    rows: list[dict[str, Any]] = []
    multipliers: list[int] = []
    for index in range(len(sizes)):
        multiplier = 1
        for size in sizes[index + 1 :]:
            multiplier *= int(size)
        multipliers.append(multiplier)

    for combo in itertools.product(*code_lists):
        offset = sum(code_lists[i].index(code) * multipliers[i] for i, code in enumerate(combo))
        value = value_at(values, offset)
        if value is None:
            continue
        row: dict[str, Any] = {
            "source_table_key": table_key,
            "source_table_path": TABLES[table_key]["path"],
            "source_table_label": payload.get("label"),
            "source_updated": payload.get("updated"),
            "measure": TABLES[table_key]["measure"],
            "frequency": TABLES[table_key]["frequency"],
            "value": value,
            "source_url": table_url(table_key),
            "source_dataset": SOURCE_DATASET,
        }
        for dim_id, code in zip(ids, combo):
            dim = dimensions[dim_id]
            label = dim["category"].get("label", {}).get(code)
            code_column, label_column = DIMENSION_COLUMNS.get(dim_id, (f"{dim_id}_code", f"{dim_id}_label"))
            row[code_column] = code
            row[label_column] = label
            if dim_id == "ContentsCode":
                unit = dim["category"].get("unit", {}).get(code, {})
                row["unit"] = unit.get("base")
                row["unit_decimals"] = unit.get("decimals")
        row["measure_statistic"] = statistic_from_contents(row.get("contents_code", ""), row.get("contents_label"))
        rows.append(row)
    return rows


def build_city_match_map(city_spine_path: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    sweden = spine[spine["country_name"].eq("Sweden")].copy()
    match_map: dict[str, dict[str, Any]] = {}
    region_codes: list[str] = []
    for row in sweden.to_dict("records"):
        city_norm = normalise_name(row["city_name"])
        region_code = CITY_TO_REGION_CODE.get(city_norm)
        if not region_code:
            continue
        region_codes.append(region_code)
        match_map[region_code] = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": row["city_rank_2025"],
            "match_type": "manual_scb_municipality_code",
            "manual_review_required": False,
        }
    return sorted(set(region_codes)), match_map


def attach_city_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    _, match_map = build_city_match_map(city_spine_path)
    matches = []
    for region_code in panel["region_code"].drop_duplicates():
        match = match_map.get(region_code)
        if match:
            matches.append({"region_code": region_code, **match})
        else:
            matches.append(
                {
                    "region_code": region_code,
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_region_code",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(matches), on="region_code", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    payloads: list[dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    region_codes, _ = build_city_match_map(city_spine_path)
    if not region_codes and payloads is None:
        raise ValueError("no Sweden top-1000 cities have SCB municipality mappings")
    if payloads is not None:
        for record in payloads:
            rows.extend(jsonstat_rows(record["table_key"], record["payload"]))
    else:
        for table_key in TABLES:
            print(f"fetching SCB table {table_key}", flush=True)
            metadata = fetch_metadata(table_key)
            payload = fetch_table(table_key, metadata, region_codes)
            rows.extend(jsonstat_rows(table_key, payload))
    if not rows:
        raise ValueError("SCB municipal housing queries returned no rows")

    panel = pd.DataFrame(rows)
    panel["year"] = panel["year"].astype(int)
    panel["value"] = pd.to_numeric(panel["value"], errors="coerce")
    for column in [
        "building_type_code",
        "building_type_label",
        "tenure_code",
        "tenure_label",
        "rental_data_code",
        "rental_data_label",
        "unit",
        "unit_decimals",
    ]:
        if column not in panel.columns:
            panel[column] = pd.NA
    panel = attach_city_matches(panel, city_spine_path)
    panel["country_name"] = "Sweden"
    panel = panel.sort_values(
        ["region_code", "source_table_key", "year", "building_type_code", "tenure_code", "rental_data_code", "contents_code"],
        na_position="last",
    ).reset_index(drop=True)

    ordered = [
        "year",
        "country_name",
        "region_code",
        "region_name",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "measure",
        "measure_statistic",
        "value",
        "unit",
        "unit_decimals",
        "building_type_code",
        "building_type_label",
        "tenure_code",
        "tenure_label",
        "rental_data_code",
        "rental_data_label",
        "contents_code",
        "contents_label",
        "source_table_key",
        "source_table_path",
        "source_table_label",
        "source_updated",
        "frequency",
        "source_dataset",
        "source_url",
    ]
    panel = panel[ordered]
    completion_rows = panel["measure"].eq("completed_new_dwellings")
    stock_rows = panel["measure"].eq("dwelling_stock")
    rent_rows = panel["measure"].eq("municipal_rent_per_sqm")
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "region_count": int(panel["region_code"].nunique()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "completion_rows": int(completion_rows.sum()),
        "stock_rows": int(stock_rows.sum()),
        "rent_rows": int(rent_rows.sum()),
        "completed_new_dwellings": float(panel.loc[completion_rows, "value"].sum()),
        "source_tables": {key: table_url(key) for key in TABLES},
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_sweden_scb_municipal_housing.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "sweden_scb_municipal_housing_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="statistics_sweden_scb",
        series_id="sweden_scb_municipal_housing_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="dwellings and SEK per square metre",
        currency="SEK",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "SCB PXWeb JSON-stat2 tables normalized to municipality-year rows for Swedish top-1000 cities "
                "with explicit SCB municipality-code matches."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional JSON list of captured JSON-stat2 payload records.")
    parser.add_argument("--output", default="data/derived/sweden_scb_municipal_housing_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    payloads = load_payloads(path_arg(args.input).resolve()) if args.input else None
    panel, stats = build_panel(city_spine_path=path_arg(args.city_spine).resolve(), payloads=payloads)
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK statistics_sweden_scb:sweden_scb_municipal_housing_panel "
        f"rows={result.rows} years={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
