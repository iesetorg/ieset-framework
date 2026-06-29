#!/usr/bin/env python3
"""Build Italy OMI assessor rent-quotation panel from the key-free national mirror.

Source: Agenzia delle Entrate - Osservatorio del Mercato Immobiliare (OMI)
"Quotazioni Immobiliari". The official bulk download ("Forniture dati OMI") is
gated behind SPID/Fisconline/Entratel login, so this builder reads the open,
key-free national mirror published by onData APS, which republishes the official
OMI semestral CSV extractions verbatim (UTF-8, comma-separated) per semester.

IMPORTANT semantics: OMI publishes assessor *quotation ranges* (semi-official
valuation bands by OMI zone, property typology and condition), NOT individual
transaction rents. This panel extracts the LOCAZIONE (rent, canone di locazione)
fields only -- Loc_min / Loc_max in EUR/m2/month -- and never the COMPRAVENDITA
(sale) fields, deriving a rent midpoint. Sale-price fields are deliberately
excluded so rent and sale bands cannot be conflated downstream.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
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

# Key-free national mirror of the official OMI semestral CSV extractions.
RAW_BASE = "https://raw.githubusercontent.com/ondata/quotazioni-immobiliari-agenzia-entrate/master/data"
SOURCE_URL = "https://github.com/ondata/quotazioni-immobiliari-agenzia-entrate"
METHODOLOGY_URL = "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari"
LICENSE = (
    "OMI data: Agenzia Entrate - OMI (attribution required, 'Agenzia Entrate - OMI'); "
    "open key-free redistribution by onData APS. Verify current OMI reuse terms."
)
SOURCE_DATASET = "Agenzia delle Entrate OMI quotazioni immobiliari (locazione / rent quotation ranges)"

# Each VALORI file is one official OMI semestral extraction. The semester is
# encoded in the file name token (e.g. _20182_ -> 2018 semester 2).
VALORI_FILES = [
    "QI_294586_1_20161_VALORI_utf8.csv",
    "QI_294583_1_20162_VALORI_utf8.csv",
    "QI_294582_1_20171_VALORI_utf8.csv",
    "QI_294581_1_20172_VALORI_utf8.csv",
    "QI_294585_1_20181_VALORI_utf8.csv",
    "QI_294577_1_20182_VALORI_utf8.csv",
]

# OMI uppercase Italian comune name -> top-1000 GHSL city English name.
OMI_COMUNE_TO_GHSL = {
    "ROMA": "Rome",
    "MILANO": "Milan",
    "NAPOLI": "Naples",
    "TORINO": "Turin",
    "FIRENZE": "Florence",
    "PALERMO": "Palermo",
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
    text = "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_omi_number(value: object) -> float | None:
    """Parse an OMI numeric cell. Decimal separator is a comma (e.g. '5,1')."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if text in {"", "nan", "None", "-", "--", "0", "0,0", "0,00"}:
        # OMI uses 0 / blank to flag a missing rent band; treat as missing.
        return None
    text = text.replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.]", "", text)
    if not text or text == ".":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if number > 0 else None


def semester_from_filename(file_name: str) -> tuple[str, int, int]:
    """Return (semester_label, year, semester) from a VALORI file name token."""
    match = re.search(r"_(\d{4})(\d)_VALORI", file_name)
    if not match:
        raise ValueError(f"Cannot decode semester from {file_name}")
    year = int(match.group(1))
    semester = int(match.group(2))
    if semester not in (1, 2):
        raise ValueError(f"Unexpected semester digit in {file_name}")
    return f"{year}-S{semester}", year, semester


def fetch_csv_bytes(file_name: str, timeout: int = 180) -> bytes:
    url = f"{RAW_BASE}/{file_name}"
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "IESET city-level data builder"})
    response.raise_for_status()
    return response.content


def read_csv_bytes(file_name: str, input_dir: Path | None) -> bytes:
    if input_dir is not None:
        local = input_dir / file_name
        if local.exists():
            return local.read_bytes()
    return fetch_csv_bytes(file_name)


def _s(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def rows_from_valori(payload: bytes, file_name: str) -> list[dict[str, Any]]:
    semester_label, year, semester = semester_from_filename(file_name)
    frame = pd.read_csv(io.BytesIO(payload), dtype=str, sep=",", keep_default_na=False, na_values=[""])
    rows: list[dict[str, Any]] = []
    for raw in frame.to_dict("records"):
        loc_min = parse_omi_number(raw.get("Loc_min"))
        loc_max = parse_omi_number(raw.get("Loc_max"))
        if loc_min is None and loc_max is None:
            # No rent band published for this typology/zone in this semester.
            continue
        lo = loc_min if loc_min is not None else loc_max
        hi = loc_max if loc_max is not None else loc_min
        if lo is not None and hi is not None and lo > hi:
            # A few source rows publish Loc_min > Loc_max; normalise band order
            # so min<=max holds (the midpoint is unaffected).
            lo, hi = hi, lo
        midpoint = round((lo + hi) / 2.0, 4) if lo is not None and hi is not None else None
        comune_name = _s(raw.get("Comune_descrizione"))
        rows.append(
            {
                "country_name": "Italy",
                "country_iso3": "ITA",
                "semester_label": semester_label,
                "year": year,
                "semester": semester,
                "area_territoriale": _s(raw.get("Area_territoriale")),
                "regione": _s(raw.get("Regione")),
                "prov": _s(raw.get("Prov")),
                "comune_istat_code": _s(raw.get("Comune_ISTAT")),
                "comune_cat_code": _s(raw.get("Comune_cat")),
                "comune_amm_code": _s(raw.get("Comune_amm")),
                "comune_descrizione": comune_name,
                "fascia": _s(raw.get("Fascia")),
                "omi_zona": _s(raw.get("Zona")),
                "omi_link_zona": _s(raw.get("LinkZona")),
                "cod_tipologia": _s(raw.get("Cod_Tip")),
                "descr_tipologia": _s(raw.get("Descr_Tipologia")),
                "stato_conservativo": _s(raw.get("Stato")),
                "stato_prevalente": _s(raw.get("Stato_prev")),
                "rent_min_eur_m2_month": round(lo, 4) if lo is not None else None,
                "rent_max_eur_m2_month": round(hi, 4) if hi is not None else None,
                "rent_mid_eur_m2_month": midpoint,
                "rent_surface_basis": _s(raw.get("Sup_NL_loc")),
                "value_type": "assessor_quotation_rent_band",
                "value_note": (
                    "OMI semi-official rent quotation range (canone di locazione) by zone, "
                    "typology and condition; NOT individual transaction rents."
                ),
                "source_file": file_name,
                "source_dataset": SOURCE_DATASET,
                "source_url": SOURCE_URL,
            }
        )
    return rows


def ghsl_match_map(city_spine_path: Path) -> dict[str, dict[str, Any]]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = (
        pd.read_csv(city_spine_path)
        if city_spine_path.suffix.lower() == ".csv"
        else pd.read_parquet(city_spine_path)
    )
    italy = spine[spine["country_name"].astype(str).str.fullmatch("Italy", case=False, na=False)].copy()
    by_norm_name = {normalise_name(row["city_name"]): row for row in italy.to_dict("records")}
    matches: dict[str, dict[str, Any]] = {}
    for omi_name, ghsl_en in OMI_COMUNE_TO_GHSL.items():
        row = by_norm_name.get(normalise_name(ghsl_en))
        if row is None:
            continue
        matches[normalise_name(omi_name)] = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_id": row["ghsl_city_id"],
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": int(row["city_rank_2025"]),
            "ghsl_match_flag": True,
            "ghsl_match_type": "manual_omi_comune_name",
        }
    return matches


def attach_ghsl_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    matches = ghsl_match_map(city_spine_path)
    rows = []
    for comune in panel["comune_descrizione"].drop_duplicates():
        match = matches.get(normalise_name(comune))
        if match:
            rows.append({"comune_descrizione": comune, **match})
        else:
            rows.append(
                {
                    "comune_descrizione": comune,
                    "ieset_city_id": None,
                    "ghsl_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "ghsl_match_flag": False,
                    "ghsl_match_type": "unmatched_or_not_top1000_city",
                }
            )
    return panel.merge(pd.DataFrame(rows), on="comune_descrizione", how="left")


ORDERED_COLUMNS = [
    "country_name",
    "country_iso3",
    "semester_label",
    "year",
    "semester",
    "area_territoriale",
    "regione",
    "prov",
    "comune_istat_code",
    "comune_cat_code",
    "comune_amm_code",
    "comune_descrizione",
    "ieset_city_id",
    "ghsl_city_id",
    "ghsl_city_name",
    "ghsl_city_rank_2025",
    "ghsl_match_flag",
    "ghsl_match_type",
    "fascia",
    "omi_zona",
    "omi_link_zona",
    "cod_tipologia",
    "descr_tipologia",
    "stato_conservativo",
    "stato_prevalente",
    "rent_min_eur_m2_month",
    "rent_max_eur_m2_month",
    "rent_mid_eur_m2_month",
    "rent_surface_basis",
    "value_type",
    "value_note",
    "source_file",
    "source_dataset",
    "source_url",
]

GRAIN_KEYS = ["comune_istat_code", "omi_link_zona", "semester_label", "cod_tipologia", "stato_conservativo"]


def build_panel(
    *,
    city_spine_path: Path,
    input_dir: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    file_shas: dict[str, str] = {}
    for file_name in VALORI_FILES:
        payload = read_csv_bytes(file_name, input_dir)
        file_shas[file_name] = sha256_bytes(payload)
        rows.extend(rows_from_valori(payload, file_name))
    if not rows:
        raise ValueError("OMI VALORI files returned no locazione (rent) rows")
    panel = pd.DataFrame(rows)
    panel = attach_ghsl_matches(panel, city_spine_path)
    panel = panel[ORDERED_COLUMNS].copy()
    # De-duplicate to the declared grain (a few OMI rows can repeat verbatim).
    panel = panel.drop_duplicates(subset=GRAIN_KEYS).reset_index(drop=True)
    panel = panel.sort_values(GRAIN_KEYS).reset_index(drop=True)

    matched = panel["ghsl_match_flag"] == True  # noqa: E712
    mids = panel["rent_mid_eur_m2_month"].dropna()
    stats = {
        "panel_rows": int(len(panel)),
        "start_semester": str(panel["semester_label"].min()),
        "end_semester": str(panel["semester_label"].max()),
        "semester_count": int(panel["semester_label"].nunique()),
        "comune_count": int(panel["comune_istat_code"].nunique()),
        "omi_zone_count": int(panel["omi_link_zona"].nunique()),
        "typology_count": int(panel["cod_tipologia"].nunique()),
        "matched_comuni": int(panel.loc[matched, "comune_descrizione"].nunique()),
        "matched_rows": int(matched.sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "rent_mid_min": float(mids.min()) if not mids.empty else None,
        "rent_mid_median": float(mids.median()) if not mids.empty else None,
        "rent_mid_max": float(mids.max()) if not mids.empty else None,
        "source_file_sha256": file_shas,
        "value_semantics": (
            "OMI assessor quotation rent ranges (semi-official valuation bands), "
            "not individual transaction rents."
        ),
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_italy_omi_rent.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "italy_omi_rent_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="agenzia_delle_entrate_omi",
        series_id="italy_omi_rent_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="semestral",
        units="rent quotation range, EUR per square metre per month",
        currency="EUR",
        start_date=stats["start_semester"],
        end_date=stats["end_semester"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "grain": GRAIN_KEYS,
            "construction": (
                "Official OMI semestral 'quotazioni immobiliari' VALORI extractions read from the "
                "key-free onData national mirror. Only LOCAZIONE (rent) fields (Loc_min/Loc_max, "
                "EUR/m2/month) are extracted; COMPRAVENDITA (sale) fields are excluded. A rent "
                "midpoint is derived. OMI ISTAT comune codes, OMI zone IDs/labels, typology and "
                "condition codes are preserved verbatim. Top Italian cities are crosswalked to GHSL "
                "urban-centre IDs via the top-1000 city universe; unmatched comuni are retained with "
                "ghsl_match_flag=False. Values are assessor quotation ranges, not transaction rents."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input-dir", help="Optional local dir with the OMI VALORI CSVs; otherwise fetch the mirror.")
    parser.add_argument("--output", default="data/derived/italy_omi_rent_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_dir = path_arg(args.input_dir).resolve() if args.input_dir else None
    panel, stats = build_panel(city_spine_path=path_arg(args.city_spine).resolve(), input_dir=input_dir)
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK agenzia_delle_entrate_omi:italy_omi_rent_panel "
        f"rows={result.rows} semesters={result.start_date}->{result.end_date} "
        f"comuni={stats['comune_count']} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
