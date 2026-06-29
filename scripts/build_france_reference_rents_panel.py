#!/usr/bin/env python3
"""Build French rent-control reference-rent panel from Opendatasoft datasets."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
import unicodedata
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

DEFAULT_DATASET_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
    "logement-encadrement-des-loyers/records"
)
DEFAULT_EXPORT_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
    "logement-encadrement-des-loyers/exports/json"
)
SOURCE_URL = "https://opendata.paris.fr/explore/dataset/logement-encadrement-des-loyers/"
METHODOLOGY_URL = SOURCE_URL
LICENSE = "Paris open-data terms; verify Opendatasoft dataset metadata"
SOURCE_DATASET = "Paris rent-control reference rents"
DEFAULT_SELECT_FIELDS = [
    "annee",
    "ville",
    "id_zone",
    "id_quartier",
    "nom_quartier",
    "piece",
    "epoque",
    "meuble_txt",
    "ref",
    "max",
    "min",
]

FIELD_ALIASES = {
    "year": ["annee", "année", "year", "an"],
    "city_name": ["ville", "commune", "nom_commune", "libelle_commune", "territoire"],
    "zone_id": ["id_zone", "zone", "secteur", "id_secteur"],
    "neighborhood_name": ["nom_quartier", "quartier", "libelle_quartier", "nom_zone"],
    "rooms": ["piece", "pieces", "nb_pieces", "nombre_pieces", "nb_piece"],
    "construction_period": ["epoque", "epoque_construction", "periode_construction", "date_construction"],
    "furnished": ["meuble", "meuble_txt", "location_meublee", "type_location", "furnished"],
    "reference_rent_eur_m2": ["ref", "loyer_ref", "loyer_reference", "reference", "loyer_de_reference"],
    "ceiling_rent_eur_m2": ["max", "loyer_max", "loyer_majore", "loyer_reference_majore", "majore"],
    "floor_rent_eur_m2": ["min", "loyer_min", "loyer_minore", "loyer_reference_minore", "minore"],
}

FUZZY_TOKENS = {
    "year": [["annee"], ["year"]],
    "city_name": [["ville"], ["commune"], ["territoire"]],
    "zone_id": [["zone"], ["secteur"]],
    "neighborhood_name": [["quartier"], ["zone"]],
    "rooms": [["piece"], ["pieces"]],
    "construction_period": [["epoque"], ["construction"], ["periode"]],
    "furnished": [["meubl"], ["furnished"]],
    "reference_rent_eur_m2": [["ref"], ["reference"]],
    "ceiling_rent_eur_m2": [["max"], ["majore"]],
    "floor_rent_eur_m2": [["min"], ["minore"]],
}

CITY_ALIASES = {
    "PARIS": "PARIS",
    "LILLE": "LILLE",
    "LOMME": "LILLE",
    "HELLEMMES": "LILLE",
    "LYON": "LYON",
    "VILLEURBANNE": "LYON",
    "BORDEAUX": "BORDEAUX",
    "MONTPELLIER": "MONTPELLIER",
    "PLAINE COMMUNE": "PARIS",
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
    text = re.sub(r"\b(CITY|COMMUNE|VILLE|ARRONDISSEMENT)\b", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace("\u00a0", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
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


def fetch_records(
    dataset_url: str = DEFAULT_DATASET_URL,
    limit: int = 100,
    sleep_seconds: float = 0.05,
    select_fields: list[str] | None = DEFAULT_SELECT_FIELDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = {"limit": limit, "offset": offset}
        if select_fields:
            params["select"] = ",".join(select_fields)
        url = dataset_url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = json.load(response)
        records = payload.get("results", payload if isinstance(payload, list) else [])
        if not records:
            break
        rows.extend(records)
        total = payload.get("total_count") if isinstance(payload, dict) else None
        if len(records) < limit or (total is not None and len(rows) >= int(total)):
            break
        offset += limit
        time.sleep(sleep_seconds)
    return rows


def fetch_export_records(
    export_url: str = DEFAULT_EXPORT_URL,
    select_fields: list[str] | None = DEFAULT_SELECT_FIELDS,
) -> list[dict[str, Any]]:
    params = {}
    if select_fields:
        params["select"] = ",".join(select_fields)
    url = export_url + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise ValueError(f"expected Opendatasoft JSON export list from {export_url}")
    return payload


def load_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = payload.get("results", payload.get("data", payload.get("records", payload)))
        if not isinstance(payload, list):
            raise ValueError(f"expected JSON list or Opendatasoft payload in {path}")
        return payload
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path).to_dict("records")
    raise ValueError(f"unsupported input format: {path}")


def pick_field(columns: list[str], logical_name: str, required: bool = True) -> str | None:
    normalised = {normalise_token(column): column for column in columns}
    for alias in FIELD_ALIASES[logical_name]:
        match = normalised.get(normalise_token(alias))
        if match:
            return match
    for column in columns:
        token = normalise_token(column)
        for token_set in FUZZY_TOKENS[logical_name]:
            if all(part in token for part in token_set):
                return column
    if required:
        raise ValueError(f"could not identify field for {logical_name}; columns={columns}")
    return None


def build_france_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    france = city_spine[city_spine["country_name"].eq("France")].copy()
    aliases: dict[str, list[dict[str, Any]]] = {}
    for row in france.to_dict("records"):
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
    alias_map = build_france_alias_map(spine)
    rows = []
    for row in panel[["city_name_norm"]].drop_duplicates().to_dict("records"):
        canonical = CITY_ALIASES.get(row["city_name_norm"], row["city_name_norm"])
        match = alias_map.get(canonical)
        if match:
            rows.append({"city_name_norm": row["city_name_norm"], **match})
        else:
            rows.append(
                {
                    "city_name_norm": row["city_name_norm"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="city_name_norm", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    rows: list[dict[str, Any]] | None = None,
    fetcher: Callable[[], list[dict[str, Any]]] = fetch_export_records,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = rows if rows is not None else fetcher()
    if not rows:
        raise ValueError("French reference-rent dataset returned no rows")
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    fields = {
        "year": pick_field(columns, "year"),
        "city_name": pick_field(columns, "city_name", required=False),
        "zone_id": pick_field(columns, "zone_id", required=False),
        "neighborhood_name": pick_field(columns, "neighborhood_name", required=False),
        "rooms": pick_field(columns, "rooms"),
        "construction_period": pick_field(columns, "construction_period"),
        "furnished": pick_field(columns, "furnished", required=False),
        "reference_rent_eur_m2": pick_field(columns, "reference_rent_eur_m2"),
        "ceiling_rent_eur_m2": pick_field(columns, "ceiling_rent_eur_m2"),
        "floor_rent_eur_m2": pick_field(columns, "floor_rent_eur_m2"),
    }
    city_values = frame[fields["city_name"]].astype(str).str.strip() if fields["city_name"] else pd.Series("Paris", index=frame.index)
    panel = pd.DataFrame(
        {
            "year": frame[fields["year"]].map(parse_int),
            "country_name": "France",
            "city_name": city_values,
            "zone_id": frame[fields["zone_id"]].astype(str) if fields["zone_id"] else pd.NA,
            "neighborhood_name": frame[fields["neighborhood_name"]].astype(str) if fields["neighborhood_name"] else pd.NA,
            "rooms": frame[fields["rooms"]].map(parse_int),
            "construction_period": frame[fields["construction_period"]].astype(str).str.strip(),
            "furnished": frame[fields["furnished"]].astype(str).str.strip() if fields["furnished"] else pd.NA,
            "reference_rent_eur_m2": frame[fields["reference_rent_eur_m2"]].map(parse_number),
            "ceiling_rent_eur_m2": frame[fields["ceiling_rent_eur_m2"]].map(parse_number),
            "floor_rent_eur_m2": frame[fields["floor_rent_eur_m2"]].map(parse_number),
        }
    )
    panel = panel.dropna(subset=["year", "city_name", "rooms", "reference_rent_eur_m2", "ceiling_rent_eur_m2"]).copy()
    if panel.empty:
        raise ValueError("French reference-rent dataset had rows, but none survived required-field normalization")
    panel["year"] = panel["year"].astype(int)
    panel["rooms"] = panel["rooms"].astype(int)
    panel["city_name_norm"] = panel["city_name"].map(normalise_name)
    panel["rent_ceiling_multiplier"] = panel["ceiling_rent_eur_m2"] / panel["reference_rent_eur_m2"]
    panel["rent_floor_multiplier"] = panel["floor_rent_eur_m2"] / panel["reference_rent_eur_m2"]
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = SOURCE_URL

    panel = attach_city_matches(panel, city_spine_path)
    ordered = [
        "year",
        "country_name",
        "city_name",
        "city_name_norm",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "zone_id",
        "neighborhood_name",
        "rooms",
        "construction_period",
        "furnished",
        "reference_rent_eur_m2",
        "ceiling_rent_eur_m2",
        "floor_rent_eur_m2",
        "rent_ceiling_multiplier",
        "rent_floor_multiplier",
        "source_dataset",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["year", "city_name", "zone_id", "rooms", "construction_period"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "city_count": int(panel["city_name_norm"].nunique()),
        "matched_cities": int(panel[["city_name_norm", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
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
    path = manifest_dir / f"fetch_run_{run_stamp}_france_reference_rents.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "france_reference_rents_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="paris_open_data",
        series_id="france_reference_rents_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="euros per square metre",
        currency="EUR",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Opendatasoft reference-rent rows normalized to annual city/zone/dwelling-cell observations. "
                "Rows are matched to the France subset of the GHSL top-1000 city spine where unambiguous."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local JSON or CSV dump of Opendatasoft records.")
    parser.add_argument("--dataset-url", default=DEFAULT_DATASET_URL)
    parser.add_argument("--export-url", default=DEFAULT_EXPORT_URL)
    parser.add_argument("--output", default="data/derived/france_reference_rents_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_rows = load_input(path_arg(args.input).resolve()) if args.input else None
    fetcher = lambda: fetch_export_records(args.export_url)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        rows=input_rows,
        fetcher=fetcher,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK paris_open_data:france_reference_rents_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
