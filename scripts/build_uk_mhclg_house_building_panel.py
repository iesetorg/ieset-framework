#!/usr/bin/env python3
"""Build England district housing starts/completions panel from MHCLG Live Table 253."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
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

SOURCE_URL = "https://www.gov.uk/government/statistical-data-sets/live-tables-on-house-building"
DOWNLOAD_URL = "https://assets.publishing.service.gov.uk/media/6a34087e00ff27f06e3efa7b/LiveTable253.ods"
METHODOLOGY_URL = SOURCE_URL
LICENSE = "Open Government Licence v3.0 unless otherwise stated on GOV.UK"
SOURCE_DATASET = "MHCLG Live Table 253: housing supply indicators of new supply"

NS = {
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
}
FY_SHEET_RE = re.compile(r"^FY_(\d{4})_(\d{2})$")
LOCAL_AUTHORITY_CODE_RE = re.compile(r"^E0[6789]\d{6}$")

FIELD_ALIASES = {
    "fiscal_year": ["fiscal_year", "financial_year", "year"],
    "fiscal_year_start": ["fiscal_year_start", "year_start"],
    "fiscal_year_end": ["fiscal_year_end", "year_end"],
    "dclg_code": ["dclg_code", "dclg code"],
    "former_ons_code": ["former_ons_code", "formeronscode", "former ons code"],
    "local_authority_code": ["current_ons_code", "current ons code", "local_authority_code", "area_code"],
    "local_authority_name": ["authority_data", "authority data", "local_authority_name", "area"],
    "private_enterprise_starts": ["private_enterprise_starts", "private enterprise starts"],
    "housing_association_starts": ["housing_association_starts", "housing association starts"],
    "local_authority_starts": ["local_authority_starts", "local authority starts"],
    "all_starts": ["all_starts", "all starts"],
    "private_enterprise_completions": ["private_enterprise_completions", "private enterprise completions"],
    "housing_association_completions": ["housing_association_completions", "housing association completions"],
    "local_authority_completions": ["local_authority_completions", "local authority completions"],
    "all_completions": ["all_completions", "all completions"],
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


def normalise_token(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def normalise_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\b(UA|LB|DISTRICT|BOROUGH|COUNTY|MET|COUNCIL)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text == "BRISTOL CITY OF":
        return "BRISTOL"
    if text == "NEWCASTLE UPON TYNE":
        return "NEWCASTLE UPON TYNE"
    return text


def parse_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace("\u00a0", "")
    if text in {".", "..", "-", "nan", "NaN"}:
        return None
    text = text.replace(",", "")
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


def fiscal_year_parts(sheet_name: str) -> tuple[str, int, int]:
    match = FY_SHEET_RE.match(sheet_name)
    if not match:
        raise ValueError(f"unexpected fiscal-year sheet name: {sheet_name}")
    start = int(match.group(1))
    end_suffix = int(match.group(2))
    century = start // 100
    end = century * 100 + end_suffix
    if end < start:
        end += 100
    return f"{start}-{str(end)[-2:]}", start, end


def cell_text(cell: ET.Element) -> str:
    parts = []
    for node in cell.iter():
        if node.tag == f"{{{NS['text']}}}p":
            text = "".join(node.itertext()).strip()
            if text:
                parts.append(text)
    return " ".join(parts)


def cell_value(cell: ET.Element) -> str:
    value_type = cell.attrib.get(f"{{{NS['office']}}}value-type")
    if value_type in {"float", "percentage", "currency"}:
        return cell.attrib.get(f"{{{NS['office']}}}value") or cell_text(cell)
    if value_type == "date":
        return cell.attrib.get(f"{{{NS['office']}}}date-value") or cell_text(cell)
    return cell_text(cell)


def ods_tables(path: Path) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("content.xml"))
    tables: dict[str, list[list[str]]] = {}
    for table in root.findall(".//table:table", NS):
        name = table.attrib.get(f"{{{NS['table']}}}name")
        if not name:
            continue
        rows: list[list[str]] = []
        for row in table.findall("table:table-row", NS):
            row_repeat = int(row.attrib.get(f"{{{NS['table']}}}number-rows-repeated", "1"))
            cells: list[str] = []
            for cell in row.findall("table:table-cell", NS):
                repeat = int(cell.attrib.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
                value = cell_value(cell)
                cells.extend([value] * min(repeat, 64))
            for _ in range(min(row_repeat, 1)):
                rows.append(cells)
        tables[name] = rows
    return tables


def rows_from_ods(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sheet_name, rows in ods_tables(path).items():
        if not FY_SHEET_RE.match(sheet_name):
            continue
        fiscal_year, start, end = fiscal_year_parts(sheet_name)
        header = None
        for row in rows:
            tokens = {normalise_token(value) for value in row}
            if {"currentonscode", "authoritydata", "allstarts", "allcompletions"}.issubset(tokens):
                header = row
                break
        if header is None:
            continue
        header_idx = rows.index(header)
        columns = [str(value).strip() for value in header]
        for row in rows[header_idx + 1 :]:
            if len(row) < len(columns):
                row = row + [""] * (len(columns) - len(row))
            record = dict(zip(columns, row))
            record["fiscal_year"] = fiscal_year
            record["fiscal_year_start"] = start
            record["fiscal_year_end"] = end
            out.append(record)
    if not out:
        raise ValueError(f"no FY_* sheets with district starts/completions found in {path}")
    return out


def load_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"missing MHCLG input: {path}. Download LiveTable253.ods from {SOURCE_URL} into {rel(path)}."
        )
    suffix = path.suffix.lower()
    if suffix == ".ods":
        return rows_from_ods(path)
    if suffix == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("records", payload))
        if not isinstance(payload, list):
            raise ValueError(f"expected JSON list in {path}")
        return payload
    if suffix == ".csv":
        return pd.read_csv(path).to_dict("records")
    raise ValueError(f"unsupported input format: {path}")


def pick_field(columns: list[str], logical_name: str, required: bool = True) -> str | None:
    normalised = {normalise_token(column): column for column in columns}
    for alias in FIELD_ALIASES[logical_name]:
        match = normalised.get(normalise_token(alias))
        if match:
            return match
    if required:
        raise ValueError(f"could not identify field for {logical_name}; columns={columns}")
    return None


def build_uk_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    uk = city_spine[city_spine["country_name"].eq("United Kingdom")].copy()
    aliases: dict[str, list[dict[str, Any]]] = {}
    for row in uk.to_dict("records"):
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


def attach_city_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    alias_map = build_uk_alias_map(spine)
    rows = []
    for row in panel[["local_authority_code", "local_authority_name_norm"]].drop_duplicates().to_dict("records"):
        canonical = "LONDON" if str(row["local_authority_code"]).startswith("E09") else row["local_authority_name_norm"]
        match = alias_map.get(canonical)
        if match:
            match_type = "london_borough_to_ghsl" if str(row["local_authority_code"]).startswith("E09") else match["match_type"]
            rows.append({"local_authority_code": row["local_authority_code"], **match, "match_type": match_type})
        else:
            rows.append(
                {
                    "local_authority_code": row["local_authority_code"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="local_authority_code", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    input_path: Path | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if rows is None:
        if input_path is None:
            raise ValueError("input_path is required when rows are not supplied")
        rows = load_input(input_path)
    if not rows:
        raise ValueError("MHCLG Live Table 253 input returned no rows")
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    fields = {name: pick_field(columns, name) for name in FIELD_ALIASES}
    panel = pd.DataFrame(
        {
            "fiscal_year": frame[fields["fiscal_year"]].astype(str).str.strip(),
            "fiscal_year_start": frame[fields["fiscal_year_start"]].map(parse_int),
            "fiscal_year_end": frame[fields["fiscal_year_end"]].map(parse_int),
            "country_name": "United Kingdom",
            "country_iso3": "GBR",
            "local_authority_code": frame[fields["local_authority_code"]].astype(str).str.strip(),
            "former_ons_code": frame[fields["former_ons_code"]].astype(str).str.strip(),
            "dclg_code": frame[fields["dclg_code"]].astype(str).str.strip(),
            "local_authority_name": frame[fields["local_authority_name"]].astype(str).str.strip(),
            "private_enterprise_starts": frame[fields["private_enterprise_starts"]].map(parse_int),
            "housing_association_starts": frame[fields["housing_association_starts"]].map(parse_int),
            "local_authority_starts": frame[fields["local_authority_starts"]].map(parse_int),
            "all_starts": frame[fields["all_starts"]].map(parse_int),
            "private_enterprise_completions": frame[fields["private_enterprise_completions"]].map(parse_int),
            "housing_association_completions": frame[fields["housing_association_completions"]].map(parse_int),
            "local_authority_completions": frame[fields["local_authority_completions"]].map(parse_int),
            "all_completions": frame[fields["all_completions"]].map(parse_int),
        }
    )
    panel = panel[panel["local_authority_code"].map(lambda value: bool(LOCAL_AUTHORITY_CODE_RE.match(str(value))))].copy()
    panel = panel.dropna(subset=["fiscal_year_start", "fiscal_year_end", "local_authority_name"]).copy()
    if panel.empty:
        raise ValueError("MHCLG rows had no usable local-authority starts/completions observations")
    panel["fiscal_year_start"] = panel["fiscal_year_start"].astype(int)
    panel["fiscal_year_end"] = panel["fiscal_year_end"].astype(int)
    value_cols = [
        "private_enterprise_starts",
        "housing_association_starts",
        "local_authority_starts",
        "all_starts",
        "private_enterprise_completions",
        "housing_association_completions",
        "local_authority_completions",
        "all_completions",
    ]
    panel[value_cols] = panel[value_cols].fillna(0).astype(int)
    panel["local_authority_name_norm"] = panel["local_authority_name"].map(normalise_name)
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = SOURCE_URL
    panel["source_download_url"] = DOWNLOAD_URL
    panel["mhclg_table_note"] = (
        "Live Table 253 reports new-build dwelling starts and completions by building-control data source; "
        "figures are rounded to the nearest 10 and are not the comprehensive net-additional-dwellings measure."
    )
    panel = attach_city_matches(panel, city_spine_path)
    ordered = [
        "fiscal_year",
        "fiscal_year_start",
        "fiscal_year_end",
        "country_name",
        "country_iso3",
        "local_authority_code",
        "former_ons_code",
        "dclg_code",
        "local_authority_name",
        "local_authority_name_norm",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        *value_cols,
        "source_dataset",
        "source_url",
        "source_download_url",
        "mhclg_table_note",
    ]
    panel = panel[ordered].sort_values(["fiscal_year_start", "local_authority_code"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_fiscal_year": str(panel["fiscal_year"].iloc[0]),
        "end_fiscal_year": str(panel["fiscal_year"].iloc[-1]),
        "local_authority_count": int(panel["local_authority_code"].nunique()),
        "matched_local_authorities": int(panel[["local_authority_code", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "total_all_starts": int(panel["all_starts"].sum()),
        "total_all_completions": int(panel["all_completions"].sum()),
        "fields": fields,
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_uk_mhclg_house_building.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "uk_mhclg_house_building_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="uk_mhclg",
        series_id="uk_mhclg_house_building_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="new-build dwellings",
        currency=None,
        start_date=str(stats["start_fiscal_year"]),
        end_date=str(stats["end_fiscal_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "MHCLG Live Table 253 FY_* sheets normalized to district/fiscal-year starts and completions, "
                "then matched to the UK subset of the GHSL top-1000 city spine."
            ),
            "caveat": "Building-control new-build indicators are rounded and are not net additions.",
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", default="data/raw/city_level/LiveTable253.ods")
    parser.add_argument("--output", default="data/derived/uk_mhclg_house_building_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        input_path=path_arg(args.input).resolve(),
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK uk_mhclg:uk_mhclg_house_building_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
