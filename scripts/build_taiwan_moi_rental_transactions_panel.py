#!/usr/bin/env python3
"""Build Taiwan MOI rental transaction panel from official current ZIP."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import re
import sys
import unicodedata
import zipfile
from dataclasses import asdict
from datetime import date, datetime, timezone
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

SOURCE_URL = "https://plvr.land.moi.gov.tw/Download?type=zip&fileName=lvr_landcsv.zip"
METHODOLOGY_URL = "https://plvr.land.moi.gov.tw/DownloadOpenData"
LICENSE = "Taiwan MOI Open Data authorization terms; verify current download conditions"
SOURCE_DATASET = "Taiwan MOI actual real-estate transaction rental open data"

TOP1000_MUNICIPALITY_ALIASES = {
    "TAIPEI": "Taipei",
    "TAICHUNG": "Taichung",
    "TAINAN": "Tainan",
    "KAOHSIUNG": "Kaohsiung",
    "HSINCHU": "Hsinchu",
}

MUNICIPALITY_EN = {
    "臺北市": "Taipei",
    "台北市": "Taipei",
    "臺中市": "Taichung",
    "台中市": "Taichung",
    "臺南市": "Tainan",
    "台南市": "Tainan",
    "高雄市": "Kaohsiung",
    "新竹市": "Hsinchu",
    "新北市": "New Taipei",
    "桃園市": "Taoyuan",
    "基隆市": "Keelung",
    "嘉義市": "Chiayi",
    "新竹縣": "Hsinchu County",
    "苗栗縣": "Miaoli County",
    "南投縣": "Nantou County",
    "彰化縣": "Changhua County",
    "雲林縣": "Yunlin County",
    "嘉義縣": "Chiayi County",
    "屏東縣": "Pingtung County",
    "宜蘭縣": "Yilan County",
    "花蓮縣": "Hualien County",
    "臺東縣": "Taitung County",
    "台東縣": "Taitung County",
    "澎湖縣": "Penghu County",
}

RENT_COLUMNS = {
    "district": "鄉鎮市區",
    "transaction_target": "交易標的",
    "address": "土地位置建物門牌",
    "land_area_sqm": "土地面積平方公尺",
    "lease_date": "租賃年月日",
    "lease_count": "租賃筆棟數",
    "lease_floor": "租賃層次",
    "total_floors": "總樓層數",
    "building_type": "建物型態",
    "main_use": "主要用途",
    "building_material": "主要建材",
    "building_completion_date": "建築完成年月",
    "building_area_sqm": "建物總面積平方公尺",
    "rooms": "建物現況格局-房",
    "living_rooms": "建物現況格局-廳",
    "bathrooms": "建物現況格局-衛",
    "compartmented": "建物現況格局-隔間",
    "has_management_org": "有無管理組織",
    "has_furniture": "有無附傢俱",
    "total_rent_ntd": "總額元",
    "rent_per_sqm_ntd": "單價元平方公尺",
    "parking_type": "車位類別",
    "parking_area_sqm": "車位面積平方公尺",
    "parking_rent_ntd": "車位總額元",
    "notes": "備註",
    "source_serial_number": "編號",
    "rental_type": "出租型態",
    "has_manager": "有無管理員",
    "lease_period": "租賃期間",
    "has_elevator": "有無電梯",
    "equipment": "附屬設備",
    "rental_residential_service": "租賃住宅服務",
}


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def parse_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text.lower() in {"", "nan", "none", "-", "--"}:
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


def parse_minguo_date(value: object) -> date | None:
    if value is None or pd.isna(value):
        return None
    text = re.sub(r"[^0-9]", "", str(value))
    if len(text) < 5:
        return None
    try:
        month = int(text[-4:-2])
        day = int(text[-2:])
        year = int(text[:-4]) + 1911
        return date(year, month, day)
    except ValueError:
        return None


def parse_minguo_month(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = re.sub(r"[^0-9]", "", str(value))
    if len(text) < 5:
        return None
    try:
        if len(text) in {5, 6}:
            year = int(text[:-2]) + 1911
            month = int(text[-2:])
            if not 1 <= month <= 12:
                return None
            return f"{year:04d}-{month:02d}"
        parsed = parse_minguo_date(text)
        if parsed is None:
            return None
        year = parsed.year
        month = parsed.month
        if not 1 <= month <= 12:
            return None
        return f"{year:04d}-{month:02d}"
    except ValueError:
        return None


def parse_lease_period(value: object) -> tuple[date | None, date | None]:
    text = "" if value is None or pd.isna(value) else str(value)
    parts = re.split(r"\s*[~－至-]\s*", text)
    if len(parts) < 2:
        return None, None
    return parse_minguo_date(parts[0]), parse_minguo_date(parts[1])


def fetch_zip_bytes(timeout: int = 120) -> bytes:
    response = requests.get(SOURCE_URL, timeout=timeout, headers={"User-Agent": "IESET city-level data builder"})
    response.raise_for_status()
    return response.content


def read_zip_bytes(path: Path | None) -> bytes:
    if path is None:
        return fetch_zip_bytes()
    return path.read_bytes()


def read_manifest(zip_file: zipfile.ZipFile) -> list[dict[str, str]]:
    text = zip_file.read("manifest.csv").decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def manifest_city_name(description: str) -> str:
    return re.sub(r"(不動產租賃|不動產買賣|預售屋買賣|建物|土地|停車場)", "", description).strip()


def city_match_map(city_spine_path: Path) -> dict[str, dict[str, Any]]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    taiwan = spine[spine["country_name"].eq("Taiwan")].copy()
    matches: dict[str, dict[str, Any]] = {}
    for row in taiwan.to_dict("records"):
        city_norm = normalise_name(row["city_name"])
        admin_name = TOP1000_MUNICIPALITY_ALIASES.get(city_norm)
        if not admin_name:
            continue
        matches[normalise_name(admin_name)] = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": int(row["city_rank_2025"]),
            "match_type": "manual_taiwan_municipality_name",
            "manual_review_required": False,
        }
    return matches


def attach_city_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    matches = city_match_map(city_spine_path)
    rows = []
    for municipality_en in panel["municipality_name_en"].drop_duplicates():
        match = matches.get(normalise_name(municipality_en))
        if match:
            rows.append({"municipality_name_en": municipality_en, **match})
        else:
            rows.append(
                {
                    "municipality_name_en": municipality_en,
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_not_top1000_admin_city",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="municipality_name_en", how="left")


def rental_file_records(zip_file: zipfile.ZipFile) -> list[dict[str, str]]:
    records = []
    for row in read_manifest(zip_file):
        if row.get("schema") == "schema-main-rent.csv" and row.get("name", "").endswith("_c.csv"):
            records.append(row)
    return records


def rows_from_rent_file(zip_file: zipfile.ZipFile, file_record: dict[str, str]) -> list[dict[str, Any]]:
    file_name = file_record["name"]
    prefix = file_name.split("_", 1)[0]
    municipality_zh = manifest_city_name(file_record.get("description", ""))
    municipality_en = MUNICIPALITY_EN.get(municipality_zh, municipality_zh)
    text = zip_file.read(file_name).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, Any]] = []
    for raw in reader:
        if raw.get(RENT_COLUMNS["district"]) == "The villages and towns urban district":
            continue
        lease_date = parse_minguo_date(raw.get(RENT_COLUMNS["lease_date"]))
        if lease_date is None:
            continue
        lease_start, lease_end = parse_lease_period(raw.get(RENT_COLUMNS["lease_period"]))
        total_rent = parse_number(raw.get(RENT_COLUMNS["total_rent_ntd"]))
        if total_rent is None:
            continue
        rows.append(
            {
                "period": f"{lease_date.year:04d}-{lease_date.month:02d}",
                "period_type": "month",
                "transaction_date": lease_date.isoformat(),
                "year": lease_date.year,
                "month": lease_date.month,
                "country_name": "Taiwan",
                "municipality_code": prefix,
                "municipality_name_zh": municipality_zh,
                "municipality_name_en": municipality_en,
                "district_name_zh": raw.get(RENT_COLUMNS["district"]),
                "transaction_target_zh": raw.get(RENT_COLUMNS["transaction_target"]),
                "land_area_sqm": parse_number(raw.get(RENT_COLUMNS["land_area_sqm"])),
                "lease_count_text": raw.get(RENT_COLUMNS["lease_count"]),
                "lease_floor": raw.get(RENT_COLUMNS["lease_floor"]),
                "total_floors": parse_int(raw.get(RENT_COLUMNS["total_floors"])),
                "building_type_zh": raw.get(RENT_COLUMNS["building_type"]),
                "main_use_zh": raw.get(RENT_COLUMNS["main_use"]),
                "building_material_zh": raw.get(RENT_COLUMNS["building_material"]),
                "building_completion_month": parse_minguo_month(raw.get(RENT_COLUMNS["building_completion_date"])),
                "building_area_sqm": parse_number(raw.get(RENT_COLUMNS["building_area_sqm"])),
                "rooms": parse_int(raw.get(RENT_COLUMNS["rooms"])),
                "living_rooms": parse_int(raw.get(RENT_COLUMNS["living_rooms"])),
                "bathrooms": parse_int(raw.get(RENT_COLUMNS["bathrooms"])),
                "compartmented_zh": raw.get(RENT_COLUMNS["compartmented"]),
                "has_management_org_zh": raw.get(RENT_COLUMNS["has_management_org"]),
                "has_furniture_zh": raw.get(RENT_COLUMNS["has_furniture"]),
                "total_rent_ntd": total_rent,
                "rent_per_sqm_ntd": parse_number(raw.get(RENT_COLUMNS["rent_per_sqm_ntd"])),
                "parking_type_zh": raw.get(RENT_COLUMNS["parking_type"]),
                "parking_area_sqm": parse_number(raw.get(RENT_COLUMNS["parking_area_sqm"])),
                "parking_rent_ntd": parse_number(raw.get(RENT_COLUMNS["parking_rent_ntd"])),
                "notes_zh": raw.get(RENT_COLUMNS["notes"]),
                "source_serial_number": raw.get(RENT_COLUMNS["source_serial_number"]),
                "rental_type_zh": raw.get(RENT_COLUMNS["rental_type"]),
                "has_manager_zh": raw.get(RENT_COLUMNS["has_manager"]),
                "lease_start_date": lease_start.isoformat() if lease_start else None,
                "lease_end_date": lease_end.isoformat() if lease_end else None,
                "lease_period_text": raw.get(RENT_COLUMNS["lease_period"]),
                "has_elevator_zh": raw.get(RENT_COLUMNS["has_elevator"]),
                "equipment_zh": raw.get(RENT_COLUMNS["equipment"]),
                "rental_residential_service_zh": raw.get(RENT_COLUMNS["rental_residential_service"]),
                "source_file": file_name,
                "source_description": file_record.get("description"),
                "source_dataset": SOURCE_DATASET,
                "source_url": SOURCE_URL,
            }
        )
    return rows


def build_panel(
    *,
    city_spine_path: Path,
    zip_bytes: bytes | None = None,
    input_zip: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    payload = zip_bytes if zip_bytes is not None else read_zip_bytes(input_zip)
    archive_sha = sha256_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as zip_file:
        rent_files = rental_file_records(zip_file)
        rows: list[dict[str, Any]] = []
        for record in rent_files:
            rows.extend(rows_from_rent_file(zip_file, record))
        build_time_note = None
        if "build_time.xml" in zip_file.namelist():
            build_time_note = zip_file.read("build_time.xml").decode("utf-8-sig", errors="replace")
            build_time_note = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", build_time_note)).strip()
    if not rows:
        raise ValueError("Taiwan MOI ZIP returned no rental transaction rows")
    panel = pd.DataFrame(rows)
    panel = attach_city_matches(panel, city_spine_path)
    ordered = [
        "period",
        "period_type",
        "transaction_date",
        "year",
        "month",
        "country_name",
        "municipality_code",
        "municipality_name_zh",
        "municipality_name_en",
        "district_name_zh",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "transaction_target_zh",
        "land_area_sqm",
        "lease_count_text",
        "lease_floor",
        "total_floors",
        "building_type_zh",
        "main_use_zh",
        "building_material_zh",
        "building_completion_month",
        "building_area_sqm",
        "rooms",
        "living_rooms",
        "bathrooms",
        "compartmented_zh",
        "has_management_org_zh",
        "has_furniture_zh",
        "total_rent_ntd",
        "rent_per_sqm_ntd",
        "parking_type_zh",
        "parking_area_sqm",
        "parking_rent_ntd",
        "notes_zh",
        "source_serial_number",
        "rental_type_zh",
        "has_manager_zh",
        "lease_start_date",
        "lease_end_date",
        "lease_period_text",
        "has_elevator_zh",
        "equipment_zh",
        "rental_residential_service_zh",
        "source_file",
        "source_description",
        "source_dataset",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["period", "municipality_code", "district_name_zh", "source_serial_number"]).reset_index(drop=True)
    matched = panel["ieset_city_id"].notna()
    stats = {
        "panel_rows": int(len(panel)),
        "start_period": str(panel["period"].min()),
        "end_period": str(panel["period"].max()),
        "municipality_count": int(panel["municipality_code"].nunique()),
        "matched_municipalities": int(panel.loc[matched, "municipality_name_en"].nunique()),
        "matched_observation_rows": int(matched.sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "source_archive_sha256": archive_sha,
        "source_rent_files": len(set(panel["source_file"])),
        "build_time_note": build_time_note,
        "address_policy": "Publisher street address field is intentionally omitted from the derived panel.",
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_taiwan_moi_rental_transactions.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "taiwan_moi_rental_transactions_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="taiwan_moi_department_of_land_administration",
        series_id="taiwan_moi_rental_transactions_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="current public batch",
        units="rental transactions, NTD, and square metres",
        currency="TWD",
        start_date=stats["start_period"],
        end_date=stats["end_period"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Official MOI current open-data ZIP parsed for main rental transaction CSV files only. "
                "Rows retain municipality/district, lease date, rent, area, attributes, source file, and "
                "official serial number; street addresses are omitted from the derived panel."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local MOI ZIP, otherwise fetch current official ZIP.")
    parser.add_argument("--output", default="data/derived/taiwan_moi_rental_transactions_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_zip = path_arg(args.input).resolve() if args.input else None
    panel, stats = build_panel(city_spine_path=path_arg(args.city_spine).resolve(), input_zip=input_zip)
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK taiwan_moi_department_of_land_administration:taiwan_moi_rental_transactions_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
