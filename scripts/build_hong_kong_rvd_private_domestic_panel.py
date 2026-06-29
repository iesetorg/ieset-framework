#!/usr/bin/env python3
"""Build Hong Kong RVD private domestic rent/supply panel from official XLS files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
import tempfile
import urllib.request
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

SOURCE_URL = "https://www.rvd.gov.hk/en/publications/property_market_statistics.html"
RENTAL_INDEX_URL = "https://www.rvd.gov.hk/doc/en/statistics/his_data_3.xls"
SUPPLY_URL = "https://www.rvd.gov.hk/doc/en/statistics/private_domestic.xls"
METHODOLOGY_URL = SOURCE_URL
LICENSE = "Hong Kong government/RVD terms; verify XLS reuse before redistribution"
HONG_KONG_IESET_CITY_ID = "ghsl_ucdb_r2024a:11185"

CLASS_LABELS = {
    "A": "Less than 40 m2",
    "B": "40 m2 to 69.9 m2",
    "C": "70 m2 to 99.9 m2",
    "D": "100 m2 to 159.9 m2",
    "E": "160 m2 or above",
    "ABC": "Less than 100 m2",
    "DE": "100 m2 or above",
    "ALL": "All Classes",
    "TOTAL": "Total",
}

RENT_INDEX_COLUMNS = [
    ("A", 5),
    ("B", 8),
    ("C", 11),
    ("D", 14),
    ("E", 17),
    ("ABC", 20),
    ("DE", 23),
    ("ALL", 26),
]
SUPPLY_CLASS_COLUMNS = [("A", 4), ("B", 6), ("C", 8), ("D", 10), ("E", 12), ("TOTAL", 14)]
VACANCY_CLASS_COLUMNS = [
    ("A", 4, 5),
    ("B", 6, 7),
    ("C", 8, 9),
    ("D", 10, 11),
    ("E", 12, 13),
    ("TOTAL", 14, 15),
]
TAKE_UP_COLUMNS = [("ABC", 4), ("DE", 8), ("TOTAL", 12)]


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


def parse_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace("\u00a0", "")
    if text.lower() in {"", "nan", "-", ".", "n.a.", "na"}:
        return None
    text = text.replace("(", "").replace(")", "")
    text = re.sub(r"[^0-9.+-]", "", text.replace(",", ""))
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_year(value: object) -> int | None:
    number = parse_number(value)
    if number is None:
        return None
    year = int(number)
    if 1900 <= year <= 2100:
        return year
    return None


def download_to_temp(url: str, name: str) -> Path:
    path = Path(tempfile.gettempdir()) / name
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        path.write_bytes(response.read())
    return path


def read_excel_frame(path: Path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet_name, header=None)


def hong_kong_city_record(city_spine_path: Path) -> dict[str, Any]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_parquet(city_spine_path) if city_spine_path.suffix.lower() == ".parquet" else pd.read_csv(city_spine_path)
    match = spine[spine["ieset_city_id"].eq(HONG_KONG_IESET_CITY_ID)]
    if match.empty:
        match = spine[spine["city_name"].eq("Hong Kong")]
    if match.empty:
        raise ValueError("could not find Hong Kong in city spine")
    row = match.iloc[0].to_dict()
    return {
        "ieset_city_id": row["ieset_city_id"],
        "ghsl_city_name": row["city_name"],
        "ghsl_city_rank_2025": int(row["city_rank_2025"]),
    }


def base_row(city: dict[str, Any], *, year: int, source_dataset_key: str, source_url: str) -> dict[str, Any]:
    return {
        "period": str(year),
        "period_type": "year",
        "year": year,
        "period_start": f"{year}-01-01",
        "period_end": f"{year}-12-31",
        "country_name": "China",
        "country_iso3": "CHN",
        "ieset_city_id": city["ieset_city_id"],
        "ghsl_city_name": city["ghsl_city_name"],
        "ghsl_city_rank_2025": city["ghsl_city_rank_2025"],
        "match_type": "hong_kong_city_assignment",
        "manual_review_required": False,
        "source_dataset_key": source_dataset_key,
        "source_url": source_url,
        "geography": "Hong Kong territory-wide",
    }


def parse_rental_index_frame(frame: pd.DataFrame, city: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, source_row in frame.iterrows():
        year = parse_year(source_row.get(2))
        if year is None:
            continue
        for property_class, column in RENT_INDEX_COLUMNS:
            value = parse_number(source_row.get(column))
            if value is None:
                continue
            rows.append(
                {
                    **base_row(city, year=year, source_dataset_key="rvd_rental_index", source_url=RENTAL_INDEX_URL),
                    "measure": "rental_index",
                    "property_class": property_class,
                    "property_class_label": CLASS_LABELS[property_class],
                    "value": value,
                    "unit": "index_1999_100",
                    "rvd_scope_note": "Private domestic rental indices by class, territory-wide; 1999 = 100.",
                }
            )
    return rows


def parse_supply_class_frame(
    frame: pd.DataFrame,
    city: dict[str, Any],
    *,
    measure: str,
    columns: list[tuple[str, int]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, source_row in frame.iterrows():
        year = parse_year(source_row.get(2))
        if year is None:
            continue
        for property_class, column in columns:
            value = parse_number(source_row.get(column))
            if value is None:
                continue
            rows.append(
                {
                    **base_row(city, year=year, source_dataset_key="rvd_private_domestic_supply", source_url=SUPPLY_URL),
                    "measure": measure,
                    "property_class": property_class,
                    "property_class_label": CLASS_LABELS[property_class],
                    "value": value,
                    "unit": "units",
                    "rvd_scope_note": "Private domestic annual supply table; figures from 2003 onwards exclude village houses.",
                }
            )
    return rows


def parse_vacancy_frame(frame: pd.DataFrame, city: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, source_row in frame.iterrows():
        year = parse_year(source_row.get(2))
        if year is None:
            continue
        for property_class, unit_column, rate_column in VACANCY_CLASS_COLUMNS:
            vacancy_units = parse_number(source_row.get(unit_column))
            vacancy_rate = parse_number(source_row.get(rate_column))
            if vacancy_units is not None:
                rows.append(
                    {
                        **base_row(city, year=year, source_dataset_key="rvd_private_domestic_supply", source_url=SUPPLY_URL),
                        "measure": "vacancy_units",
                        "property_class": property_class,
                        "property_class_label": CLASS_LABELS[property_class],
                        "value": vacancy_units,
                        "unit": "units",
                        "rvd_scope_note": "Private domestic vacancy at year end by class.",
                    }
                )
            if vacancy_rate is not None:
                rows.append(
                    {
                        **base_row(city, year=year, source_dataset_key="rvd_private_domestic_supply", source_url=SUPPLY_URL),
                        "measure": "vacancy_rate",
                        "property_class": property_class,
                        "property_class_label": CLASS_LABELS[property_class],
                        "value": vacancy_rate,
                        "unit": "share_of_stock",
                        "rvd_scope_note": "Private domestic vacancy at year end as share of stock by class.",
                    }
                )
    return rows


def build_panel(
    *,
    city_spine_path: Path,
    rental_index_path: Path | None = None,
    supply_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rental_index_path = rental_index_path or download_to_temp(RENTAL_INDEX_URL, "hong_kong_rvd_his_data_3.xls")
    supply_path = supply_path or download_to_temp(SUPPLY_URL, "hong_kong_rvd_private_domestic.xls")
    city = hong_kong_city_record(city_spine_path)

    rows: list[dict[str, Any]] = []
    rows.extend(parse_rental_index_frame(read_excel_frame(rental_index_path, "Annual  按年"), city))
    supply_sheet_specs = [
        ("Completions_落成量", "completions", SUPPLY_CLASS_COLUMNS),
        ("Stock_總存量", "stock", SUPPLY_CLASS_COLUMNS),
        ("Take-up_入住量", "take_up", TAKE_UP_COLUMNS),
    ]
    for sheet_name, measure, columns in supply_sheet_specs:
        rows.extend(parse_supply_class_frame(read_excel_frame(supply_path, sheet_name), city, measure=measure, columns=columns))
    rows.extend(parse_vacancy_frame(read_excel_frame(supply_path, "Vacancy_空置量"), city))

    if not rows:
        raise ValueError("Hong Kong RVD workbooks produced no usable rows")
    panel = pd.DataFrame(rows)
    ordered = [
        "period",
        "period_type",
        "year",
        "period_start",
        "period_end",
        "country_name",
        "country_iso3",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "geography",
        "source_dataset_key",
        "source_url",
        "measure",
        "property_class",
        "property_class_label",
        "value",
        "unit",
        "rvd_scope_note",
    ]
    panel = panel[ordered].sort_values(["year", "source_dataset_key", "measure", "property_class"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "measure_counts": {str(k): int(v) for k, v in panel["measure"].value_counts().sort_index().to_dict().items()},
        "rental_index_years": int(panel.loc[panel["measure"].eq("rental_index"), "year"].nunique()),
        "supply_years": int(panel.loc[panel["source_dataset_key"].eq("rvd_private_domestic_supply"), "year"].nunique()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique()),
        "source_files": {
            "rental_index_url": RENTAL_INDEX_URL,
            "supply_url": SUPPLY_URL,
            "rental_index_sha256": sha256_path(rental_index_path),
            "supply_sha256": sha256_path(supply_path),
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
    path = manifest_dir / f"fetch_run_{run_stamp}_hong_kong_rvd_private_domestic.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "hong_kong_rvd_private_domestic_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="hong_kong_rvd",
        series_id="hong_kong_rvd_private_domestic_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="rental index, private domestic units, and vacancy share",
        currency="HKD",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Downloaded official Hong Kong RVD private domestic XLS workbooks; extracted annual territory-wide "
                "rental indices plus completions, stock, vacancy units/rates, and take-up by RVD property class; "
                "assigned all rows to the GHSL Hong Kong urban centre."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--rental-index-input", help="Optional local RVD his_data_3 XLS/XLSX.")
    parser.add_argument("--supply-input", help="Optional local RVD private_domestic XLS/XLSX.")
    parser.add_argument("--output", default="data/derived/hong_kong_rvd_private_domestic_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        rental_index_path=path_arg(args.rental_index_input).resolve() if args.rental_index_input else None,
        supply_path=path_arg(args.supply_input).resolve() if args.supply_input else None,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK hong_kong_rvd:hong_kong_rvd_private_domestic_panel "
        f"rows={result.rows} years={result.start_date}->{result.end_date} measures={stats['measure_counts']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
