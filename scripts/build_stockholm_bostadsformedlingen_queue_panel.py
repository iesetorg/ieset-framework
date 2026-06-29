#!/usr/bin/env python3
"""Build Stockholm rent-band and housing-queue allocation panel."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
import urllib.parse
import urllib.request
import unicodedata
import re
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

BASE_URL = "https://bostad.stockholm.se"
SOURCE_URL = f"{BASE_URL}/statistik/"
METHODOLOGY_URL = f"{BASE_URL}/statistik/hyra-och-kotid-per-omrade/"
LICENSE = "Bostadsformedlingen/Stockholm city website terms; verify reuse before redistribution"
SOURCE_DATASET = "Bostadsformedlingen Stockholm rent and queue-time statistics"
AREA_FILTER = "Stockholm"
APARTMENT_TYPE_FILTER_VALUE = ""
APARTMENT_TYPE_FILTER_NAME = "Vanlig hyresratt"
BUILDING_TYPE_FILTER_VALUE = ""
BUILDING_TYPE_FILTER_NAME = "Alla"
ROOMS_FILTER_VALUE = ""
ROOMS_FILTER_NAME = "Alla"
DEFAULT_QUEUES = ["Bostadskön", "Interna byteskön", "Värmdökön"]
DEFAULT_START_YEAR = 2017
DEFAULT_END_YEAR = 2026

MEASURES = {
    "rent_band_count": {
        "endpoint": "/statistik/data/hyra-per-omrade",
        "band_unit": "SEK_monthly_rent",
        "band_width": 2000,
        "band_multiplier": 1000,
    },
    "queue_time_band_count": {
        "endpoint": "/statistik/data/kotid-per-omrade",
        "band_unit": "queue_years",
        "band_width": 2,
        "band_multiplier": 1,
    },
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


def fetch_chart_payload(
    measure: str,
    params: dict[str, Any],
    *,
    timeout: int = 120,
) -> dict[str, Any]:
    endpoint = MEASURES[measure]["endpoint"]
    url = f"{BASE_URL}{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def load_payloads(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text())
    if isinstance(payload, dict) and "payloads" in payload:
        payload = payload["payloads"]
    if not isinstance(payload, list):
        raise ValueError(f"expected JSON list of payload records in {path}")
    return payload


def build_sweden_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    sweden = city_spine[city_spine["country_name"].eq("Sweden")].copy()
    aliases: dict[str, list[dict[str, Any]]] = {}
    for row in sweden.to_dict("records"):
        name = normalise_name(row["city_name"])
        aliases.setdefault(name, []).append(
            {
                "ieset_city_id": row["ieset_city_id"],
                "ghsl_city_name": row["city_name"],
                "ghsl_city_rank_2025": row["city_rank_2025"],
                "match_type": "normalized_name",
                "manual_review_required": False,
            }
        )
    return {alias: records[0] for alias, records in aliases.items() if len({r["ieset_city_id"] for r in records}) == 1}


def attach_stockholm_match(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    match = build_sweden_alias_map(spine).get("STOCKHOLM")
    if not match:
        match = {
            "ieset_city_id": None,
            "ghsl_city_name": None,
            "ghsl_city_rank_2025": pd.NA,
            "match_type": "unmatched_or_ambiguous_name",
            "manual_review_required": True,
        }
    for column, value in match.items():
        panel[column] = value
    return panel


def request_params(year: int, queue: str) -> dict[str, Any]:
    return {
        "apartmentType": APARTMENT_TYPE_FILTER_VALUE,
        "area": AREA_FILTER,
        "buildingType": BUILDING_TYPE_FILTER_VALUE,
        "queue": queue,
        "rooms": ROOMS_FILTER_VALUE,
        "year": year,
    }


def band_bounds(measure: str, group: Any) -> tuple[float, float | None, bool]:
    info = MEASURES[measure]
    lower = float(group) * float(info["band_multiplier"])
    is_open_upper = float(group) >= 20
    upper = None if is_open_upper else lower + float(info["band_width"])
    return lower, upper, is_open_upper


def rows_from_payload(
    *,
    measure: str,
    year: int,
    queue: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    labels = payload.get("labels") or []
    datasets = payload.get("datasets") or []
    if not datasets:
        return []
    counts = datasets[0].get("data") or []
    rows: list[dict[str, Any]] = []
    for label, count in zip(labels, counts):
        group = label.get("group")
        lower, upper, open_upper = band_bounds(measure, group)
        rows.append(
            {
                "year": int(year),
                "country_name": "Sweden",
                "municipality_name": AREA_FILTER,
                "municipality_name_norm": "STOCKHOLM",
                "queue_name": queue,
                "measure": measure,
                "band_label_short": str(label.get("short", "")),
                "band_label_long": str(label.get("long", "")),
                "band_group": group,
                "band_lower": lower,
                "band_upper": upper,
                "band_open_upper": bool(open_upper),
                "band_unit": MEASURES[measure]["band_unit"],
                "allocated_dwellings": int(count or 0),
                "area_filter": AREA_FILTER,
                "apartment_type_filter_value": APARTMENT_TYPE_FILTER_VALUE,
                "apartment_type_filter_name": APARTMENT_TYPE_FILTER_NAME,
                "building_type_filter_value": BUILDING_TYPE_FILTER_VALUE,
                "building_type_filter_name": BUILDING_TYPE_FILTER_NAME,
                "rooms_filter_value": ROOMS_FILTER_VALUE,
                "rooms_filter_name": ROOMS_FILTER_NAME,
                "api_endpoint": f"{BASE_URL}{MEASURES[measure]['endpoint']}",
                "source_dataset": SOURCE_DATASET,
                "source_url": SOURCE_URL,
            }
        )
    return rows


def build_panel(
    *,
    city_spine_path: Path,
    years: list[int] | None = None,
    queues: list[str] | None = None,
    payloads: list[dict[str, Any]] | None = None,
    fetcher: Callable[[str, dict[str, Any]], dict[str, Any]] = fetch_chart_payload,
    sleep_seconds: float = 0.05,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if payloads is not None:
        for record in payloads:
            rows.extend(
                rows_from_payload(
                    measure=record["measure"],
                    year=int(record["year"]),
                    queue=record["queue"],
                    payload=record["payload"],
                )
            )
    else:
        years = years or list(range(DEFAULT_START_YEAR, DEFAULT_END_YEAR + 1))
        queues = queues or DEFAULT_QUEUES
        for year in years:
            for queue in queues:
                params = request_params(year, queue)
                for measure in MEASURES:
                    payload = fetcher(measure, params)
                    rows.extend(rows_from_payload(measure=measure, year=year, queue=queue, payload=payload))
                    time.sleep(sleep_seconds)

    if not rows:
        raise ValueError("Stockholm queue statistics returned no rows")

    panel = pd.DataFrame(rows)
    panel = attach_stockholm_match(panel, city_spine_path)
    panel["allocated_dwellings"] = panel["allocated_dwellings"].astype("Int64")
    panel["year"] = panel["year"].astype(int)
    panel["positive_band"] = panel["allocated_dwellings"].fillna(0).gt(0)
    ordered = [
        "year",
        "country_name",
        "municipality_name",
        "municipality_name_norm",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "queue_name",
        "measure",
        "band_label_short",
        "band_label_long",
        "band_group",
        "band_lower",
        "band_upper",
        "band_open_upper",
        "band_unit",
        "allocated_dwellings",
        "positive_band",
        "area_filter",
        "apartment_type_filter_value",
        "apartment_type_filter_name",
        "building_type_filter_value",
        "building_type_filter_name",
        "rooms_filter_value",
        "rooms_filter_name",
        "api_endpoint",
        "source_dataset",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["year", "queue_name", "measure", "band_group"]).reset_index(drop=True)

    rent_rows = panel["measure"].eq("rent_band_count")
    queue_rows = panel["measure"].eq("queue_time_band_count")
    stats = {
        "panel_rows": int(len(panel)),
        "positive_band_rows": int(panel["positive_band"].sum()),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "queue_count": int(panel["queue_name"].nunique()),
        "queues": sorted(panel["queue_name"].unique().tolist()),
        "rent_band_rows": int((rent_rows & panel["positive_band"]).sum()),
        "queue_time_band_rows": int((queue_rows & panel["positive_band"]).sum()),
        "rent_band_allocated_dwellings": int(panel.loc[rent_rows, "allocated_dwellings"].sum()),
        "queue_time_allocated_dwellings": int(panel.loc[queue_rows, "allocated_dwellings"].sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "source_endpoints": {measure: f"{BASE_URL}{info['endpoint']}" for measure, info in MEASURES.items()},
        "filters": {
            "area": AREA_FILTER,
            "apartment_type": APARTMENT_TYPE_FILTER_NAME,
            "building_type": BUILDING_TYPE_FILTER_NAME,
            "rooms": ROOMS_FILTER_NAME,
        },
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_stockholm_bostadsformedlingen_queue.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "stockholm_bostadsformedlingen_queue_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="bostadsformedlingen_stockholm",
        series_id="stockholm_bostadsformedlingen_queue_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual, as published",
        units="allocated dwellings by rent and queue-time band",
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
                "Official Bostadsformedlingen chart JSON endpoints normalized to Stockholm municipality-year, "
                "queue, measure, and band observations. Rows are aggregate allocation counts, not apartment records."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local JSON list of captured chart payload records.")
    parser.add_argument("--output", default="data/derived/stockholm_bostadsformedlingen_queue_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    parser.add_argument("--queues", nargs="*", default=DEFAULT_QUEUES)
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    payloads = load_payloads(path_arg(args.input).resolve()) if args.input else None
    years = list(range(args.start_year, args.end_year + 1))
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        years=years,
        queues=args.queues,
        payloads=payloads,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK bostadsformedlingen_stockholm:stockholm_bostadsformedlingen_queue_panel "
        f"rows={result.rows} years={result.start_date}->{result.end_date} "
        f"matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
