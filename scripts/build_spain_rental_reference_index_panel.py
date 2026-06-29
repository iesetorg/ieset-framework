#!/usr/bin/env python3
"""Build Spain rental reference-index panel from the MIVAU SERPAVI database.

Source: Sistema Estatal de Referencia del Precio del Alquiler de Vivienda (SERPAVI),
Ministerio de Vivienda y Agenda Urbana (MIVAU). This system is the OFFICIAL legal
cap basis for stressed-market ("zona de mercado residencial tensionado") rent limits
under Spain Law 12/2023. Values are tax-source reference/index statistics (medians and
the p25-p75 index RANGE), NOT observed transaction rents from a private listings panel.

The published key-free Excel database ("BD SERPAVI 2011-2024") carries, per territory
and per year (suffix _AA, AA in 11..24), median / p25 / p75 of:
  - ALQM2_LV_*  : monthly rent per m2 (EUR/m2/month)   -> reference index basis
  - ALQTBID12_* : monthly rent for the whole dwelling (EUR/month)
  - SLVM2_*     : dwelling floor area (m2)
split by dwelling segment VC (Vivienda Colectiva / apartment) and VU (Vivienda
Unifamiliar o Rural / single-family). BI_ALVHEPCO_T{VC,VU} are the rental-unit counts.

This builder reshapes the wide "Municipios" sheet into a long panel with one row per
(municipality_code, period[, dwelling_segment]) and crosswalks Madrid, Barcelona,
Valencia and Sevilla to the GHSL top-1000 spine.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
import unicodedata
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

SOURCE_URL = "https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi"
DOWNLOAD_URL = (
    "https://cdn.mivau.gob.es/portal-web-mivau/vivienda/serpavi/"
    "2026-03-09_bd_SERPAVI_2011-2024%20-%20DEFINITIVO%20WEB.xlsx"
)
METHODOLOGY_URL = "https://cdn.mivau.gob.es/portal-web-mivau/vivienda/serpavi/2026-03-18_Metodologia_SERPAVI.pdf"
LICENSE = "MIVAU / Ministerio de Vivienda y Agenda Urbana public reuse terms; verify bulk redistribution"
SOURCE_DATASET = "Sistema Estatal de Referencia del Precio del Alquiler de Vivienda (SERPAVI) — BD 2011-2024 (Municipios)"
SHEET = "Municipios"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) IESET-city-level-data-builder"

# Year suffix -> calendar year (tax exploitation Modelo 100).
YEAR_SUFFIXES = {f"{y:02d}": 2000 + y for y in range(11, 25)}

# Dwelling segment codes used in column names.
SEGMENTS = {
    "VC": "vivienda_colectiva",  # collective / apartment
    "VU": "vivienda_unifamiliar_rural",  # single-family / rural
}

# Identifier columns on the Municipios sheet.
ID_COLS = {
    "province_code": "CPRO",
    "province_name": "NPRO",
    "municipality_code": "CUMUN",
    "municipality_name": "NMUN",
}

# Measure prefix -> (output column, description). Suffix _<SEG>_<YY> appended in source.
MEASURES = {
    "BI_ALVHEPCO_T": "rental_unit_count",
    "ALQM2_LV_M": "ref_rent_per_m2_eur_median",
    "ALQM2_LV_25": "ref_rent_per_m2_eur_p25",
    "ALQM2_LV_75": "ref_rent_per_m2_eur_p75",
    "ALQTBID12_M": "ref_rent_monthly_eur_median",
    "ALQTBID12_25": "ref_rent_monthly_eur_p25",
    "ALQTBID12_75": "ref_rent_monthly_eur_p75",
    "SLVM2_M": "dwelling_area_m2_median",
}

# Explicit CUMUN (INE) -> GHSL crosswalk for the wave's flagship cities. Spanish NMUN
# labels differ from the English GHSL spine ("Sevilla" vs "Seville"), so we crosswalk on
# the stable INE municipality code rather than on the name.
TARGET_CITY_CODES = {
    "28079": "Madrid",
    "08019": "Barcelona",
    "46250": "Valencia",
    "41091": "Seville",  # NMUN="Sevilla"
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


def sha256_bytes(blob: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(blob)
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
    text = "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def download_workbook(dest: Path) -> tuple[bytes, str]:
    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as response:
        blob = response.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    return blob, sha256_bytes(blob)


def load_municipios(xlsx_path: Path) -> pd.DataFrame:
    return pd.read_excel(xlsx_path, sheet_name=SHEET, dtype={ID_COLS["municipality_code"]: str})


def reshape_long(frame: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    id_present = {logical: src for logical, src in ID_COLS.items() if src in frame.columns}
    for suffix, year in YEAR_SUFFIXES.items():
        for seg_code, seg_label in SEGMENTS.items():
            col_map: dict[str, str] = {}
            for prefix, out in MEASURES.items():
                src = f"{prefix}_{seg_code}_{suffix}"
                if src in frame.columns:
                    col_map[out] = src
            if not col_map:
                continue
            block = pd.DataFrame()
            for logical, src in id_present.items():
                block[logical] = frame[src]
            block["period"] = str(year)
            block["year"] = year
            block["dwelling_segment_code"] = seg_code
            block["dwelling_segment"] = seg_label
            for out, src in col_map.items():
                block[out] = pd.to_numeric(frame[src], errors="coerce")
            records.append(block)
    if not records:
        raise ValueError("No SERPAVI measure columns matched expected naming; check workbook schema.")
    long = pd.concat(records, ignore_index=True)
    # Drop rows with no rent signal at all (territory had no rental observations that year/segment).
    rent_cols = [c for c in long.columns if c.startswith("ref_rent_")]
    long = long.dropna(subset=rent_cols, how="all").copy()
    return long


def normalise_codes(long: pd.DataFrame) -> pd.DataFrame:
    long["municipality_code"] = (
        long["municipality_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(5)
    )
    long["province_code"] = (
        long["province_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(2)
    )
    long["municipality_name"] = long["municipality_name"].astype(str).str.strip()
    long["municipality_name_norm"] = long["municipality_name"].map(normalise_name)
    return long


def attach_city_matches(long: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_parquet(city_spine_path) if city_spine_path.suffix.lower() == ".parquet" else pd.read_csv(city_spine_path)
    spain = spine[spine["country_name"].eq("Spain")].copy()
    by_name = {normalise_name(r["city_name"]): r for r in spain.to_dict("records")}

    rows = []
    for code in sorted(long["municipality_code"].unique()):
        match = None
        match_type = "unmatched"
        ghsl_target = TARGET_CITY_CODES.get(code)
        if ghsl_target is not None:
            match = by_name.get(normalise_name(ghsl_target))
            match_type = "ine_code_to_ghsl_name"
        if match is None:
            rows.append(
                {
                    "municipality_code": code,
                    "ieset_city_id": None,
                    "ghsl_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "ghsl_match_flag": False,
                    "match_type": match_type if ghsl_target else "not_a_target_city",
                    "manual_review_required": bool(ghsl_target),
                }
            )
        else:
            rows.append(
                {
                    "municipality_code": code,
                    "ieset_city_id": match["ieset_city_id"],
                    "ghsl_city_id": match.get("ghsl_city_id"),
                    "ghsl_city_name": match["city_name"],
                    "ghsl_city_rank_2025": match.get("city_rank_2025"),
                    "ghsl_match_flag": True,
                    "match_type": match_type,
                    "manual_review_required": False,
                }
            )
    return long.merge(pd.DataFrame(rows), on="municipality_code", how="left")


def build_panel(*, xlsx_path: Path, city_spine_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = load_municipios(xlsx_path)
    long = reshape_long(frame)
    long = normalise_codes(long)
    long = attach_city_matches(long, city_spine_path)

    long["country_name"] = "Spain"
    long["country_iso3"] = "ESP"
    long["value_type"] = "official_reference_index"
    long["value_basis"] = "legal_cap_basis_law_12_2023"
    long["is_reference_not_observed"] = True
    long["source_dataset"] = SOURCE_DATASET
    long["source_url"] = SOURCE_URL
    long["source_download_url"] = DOWNLOAD_URL

    ordered = [
        "year",
        "period",
        "country_name",
        "country_iso3",
        "province_code",
        "province_name",
        "municipality_code",
        "municipality_name",
        "municipality_name_norm",
        "ieset_city_id",
        "ghsl_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "ghsl_match_flag",
        "match_type",
        "manual_review_required",
        "dwelling_segment_code",
        "dwelling_segment",
        "rental_unit_count",
        "ref_rent_per_m2_eur_median",
        "ref_rent_per_m2_eur_p25",
        "ref_rent_per_m2_eur_p75",
        "ref_rent_monthly_eur_median",
        "ref_rent_monthly_eur_p25",
        "ref_rent_monthly_eur_p75",
        "dwelling_area_m2_median",
        "value_type",
        "value_basis",
        "is_reference_not_observed",
        "source_dataset",
        "source_url",
        "source_download_url",
    ]
    ordered = [c for c in ordered if c in long.columns]
    panel = long[ordered].sort_values(
        ["year", "municipality_code", "dwelling_segment_code"]
    ).reset_index(drop=True)

    matched_codes = panel.loc[panel["ghsl_match_flag"], "municipality_code"].unique()
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "municipality_count": int(panel["municipality_code"].nunique()),
        "dwelling_segments": sorted(panel["dwelling_segment"].unique().tolist()),
        "matched_municipalities": int(len(matched_codes)),
        "matched_observation_rows": int(panel["ghsl_match_flag"].sum()),
        "unique_ieset_city_ids": int(panel.loc[panel["ghsl_match_flag"], "ieset_city_id"].nunique()),
        "matched_city_codes": sorted(matched_codes.tolist()),
        "fields": {
            "median_rent_per_m2": "ALQM2_LV_M_<SEG>_<YY>",
            "p25_rent_per_m2": "ALQM2_LV_25_<SEG>_<YY>",
            "p75_rent_per_m2": "ALQM2_LV_75_<SEG>_<YY>",
            "median_rent_monthly": "ALQTBID12_M_<SEG>_<YY>",
            "rental_unit_count": "BI_ALVHEPCO_T<SEG>_<YY>",
            "dwelling_area_m2": "SLVM2_M_<SEG>_<YY>",
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
    path = manifest_dir / f"fetch_run_{run_stamp}_spain_rental_reference_index.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "spain_rental_reference_index_panel",
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(
    panel: pd.DataFrame,
    stats: dict[str, Any],
    output_path: Path,
    fetch_ts: datetime,
    source_sha256: str,
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="mivau_serpavi",
        series_id="spain_rental_reference_index_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="reference rent EUR/m2/month and EUR/month (median and p25-p75 index range)",
        currency="EUR",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {
                "parquet_path": rel(output_path),
                "parquet_sha256": parquet_sha,
                "source_download_url": DOWNLOAD_URL,
                "source_xlsx_sha256": source_sha256,
            },
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "MIVAU SERPAVI wide 'Municipios' sheet reshaped to long municipality/year/segment rows. "
                "Reference index = median (and p25-p75 range) of monthly rent per m2 and whole-dwelling "
                "monthly rent from tax-source exploitation. Crosswalked to the GHSL top-1000 spine on INE "
                "municipality code for Madrid, Barcelona, Valencia and Sevilla."
            ),
            "caveat": (
                "Values are the OFFICIAL state reference/index (legal cap basis for Law 12/2023 stressed-market "
                "zones), NOT observed private-listing or repeat-sales transaction rents. value_type="
                "'official_reference_index'; is_reference_not_observed=true."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local path to a pre-downloaded SERPAVI .xlsx.")
    parser.add_argument("--output", default="data/derived/spain_rental_reference_index_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--cache", default="data/raw_cache/serpavi_bd_2011_2024.xlsx",
                        help="Where to cache the downloaded workbook.")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)

    if args.input:
        xlsx_path = path_arg(args.input).resolve()
        if not xlsx_path.exists():
            raise FileNotFoundError(xlsx_path)
        source_sha256 = sha256_path(xlsx_path)
    else:
        xlsx_path = path_arg(args.cache).resolve()
        _, source_sha256 = download_workbook(xlsx_path)

    panel, stats = build_panel(
        xlsx_path=xlsx_path,
        city_spine_path=path_arg(args.city_spine).resolve(),
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts, source_sha256)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK mivau_serpavi:spain_rental_reference_index_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} "
        f"municipalities={stats['municipality_count']} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
