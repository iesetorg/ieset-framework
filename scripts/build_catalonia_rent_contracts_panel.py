#!/usr/bin/env python3
"""Build Catalonia municipality rent-contract panel from Generalitat Open Data."""
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

SOCRATA_DOMAIN = "https://analisi.transparenciacatalunya.cat"
DATASET_ID = "qww9-bvhh"
SOURCE_URL = f"{SOCRATA_DOMAIN}/d/{DATASET_ID}"
API_URL = f"{SOCRATA_DOMAIN}/resource/{DATASET_ID}.json"
METHODOLOGY_URL = SOURCE_URL
LICENSE = "Generalitat de Catalunya open-data terms; verify per dataset metadata"
SOURCE_DATASET = "Catalonia housing rental contracts and average contractual rent by municipality"

FIELD_ALIASES = {
    "territorial_scope": ["ambit_territorial", "ambitterritorial", "scope", "ambit"],
    "year": ["any", "year", "ano", "exercici"],
    "quarter": ["trimestre", "quarter", "trim"],
    "municipality_code": ["codi_municipi", "codimunicipi", "codi_ine", "codine", "codi_territorial", "coditerritorial"],
    "municipality_name": [
        "municipi",
        "nom_municipi",
        "nommunicipi",
        "municipality",
        "nom_territorial",
        "nomterritorial",
        "nom_territori",
        "nomterritori",
    ],
    "contracts": ["nombre_contractes", "nombrecontractes", "contractes", "num_contractes", "n_contractes", "ncontractes", "habitatges"],
    "rent_price_band": ["tram_preus", "trampreus", "price_band", "rent_band"],
    "avg_monthly_rent_eur": [
        "lloguer_mitja_mensual",
        "lloguermitjamensual",
        "lloguer_mitja",
        "renda_mitjana_mensual",
        "rendamitjanamensual",
        "renda",
        "preu_mig",
        "preumig",
        "import_mitja",
    ],
    "avg_rent_per_m2_eur": [
        "lloguer_mitja_per_m2",
        "lloguermitjaperm2",
        "renda_mitjana_m2",
        "rendamitjanam2",
        "euros_m2",
        "preu_m2",
    ],
}

FUZZY_TOKENS = {
    "territorial_scope": [["ambit"], ["scope"]],
    "year": [["any"], ["year"], ["exercici"]],
    "quarter": [["trimestre"], ["quarter"]],
    "municipality_code": [["codi", "municip"], ["codi", "territorial"], ["ine"]],
    "municipality_name": [["nom", "municip"], ["municipi"], ["municipality"], ["nom", "territor"]],
    "contracts": [["contract"], ["nombre", "contract"], ["num", "contract"], ["habitatg"]],
    "rent_price_band": [["tram", "preus"], ["price", "band"], ["rent", "band"]],
    "avg_monthly_rent_eur": [["lloguer", "mitj"], ["renda", "mitjan"], ["preu", "mig"], ["import", "mitj"]],
    "avg_rent_per_m2_eur": [["m2"], ["superficie"], ["metre"]],
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
    text = re.sub(r"\b(CITY|MUNICIPI|MUNICIPALITY|MUNICIPIO)\b", " ", text)
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
    if value is None or value == "":
        return None
    text = str(value).strip().replace("\u00a0", "")
    if "," in text:
        number = parse_number(text)
        return None if number is None else int(number)
    text = re.sub(r"[^0-9+-]", "", text)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def fetch_rows(limit: int = 50000, sleep_seconds: float = 0.05) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        url = API_URL + "?" + urllib.parse.urlencode({"$limit": limit, "$offset": offset})
        req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = json.load(response)
        if not payload:
            break
        rows.extend(payload)
        if len(payload) < limit:
            break
        offset += limit
        time.sleep(sleep_seconds)
    return rows


def load_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict) and "data" in payload:
            payload = payload["data"]
        if not isinstance(payload, list):
            raise ValueError(f"expected JSON list in {path}")
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


def build_spain_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    spain = city_spine[city_spine["country_name"].eq("Spain")].copy()
    aliases: dict[str, list[dict[str, Any]]] = {}
    for row in spain.to_dict("records"):
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
    alias_map = build_spain_alias_map(spine)
    rows = []
    for row in panel[["municipality_name", "municipality_name_norm"]].drop_duplicates().to_dict("records"):
        match = alias_map.get(row["municipality_name_norm"])
        if match:
            rows.append({"municipality_name_norm": row["municipality_name_norm"], **match})
        else:
            rows.append(
                {
                    "municipality_name_norm": row["municipality_name_norm"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="municipality_name_norm", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    rows: list[dict[str, Any]] | None = None,
    fetcher: Callable[[], list[dict[str, Any]]] = fetch_rows,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = rows if rows is not None else fetcher()
    if not rows:
        raise ValueError("Catalonia rent dataset returned no rows")
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    fields = {
        "territorial_scope": pick_field(columns, "territorial_scope", required=False),
        "year": pick_field(columns, "year"),
        "quarter": pick_field(columns, "quarter", required=False),
        "municipality_code": pick_field(columns, "municipality_code", required=False),
        "municipality_name": pick_field(columns, "municipality_name"),
        "contracts": pick_field(columns, "contracts", required=False),
        "rent_price_band": pick_field(columns, "rent_price_band", required=False),
        "avg_monthly_rent_eur": pick_field(columns, "avg_monthly_rent_eur"),
        "avg_rent_per_m2_eur": pick_field(columns, "avg_rent_per_m2_eur", required=False),
    }
    if fields["territorial_scope"]:
        scope = frame[fields["territorial_scope"]].map(normalise_token)
        frame = frame[scope.eq("municipi")].copy()
        if frame.empty:
            raise ValueError("Catalonia rent dataset had no municipality rows after scope filtering")

    panel = pd.DataFrame(
        {
            "year": frame[fields["year"]].map(parse_int),
            "quarter": frame[fields["quarter"]].map(parse_int) if fields["quarter"] else pd.NA,
            "municipality_code": frame[fields["municipality_code"]].astype(str) if fields["municipality_code"] else pd.NA,
            "municipality_name": frame[fields["municipality_name"]].astype(str).str.strip(),
            "contracts": frame[fields["contracts"]].map(parse_int) if fields["contracts"] else pd.NA,
            "rent_price_band": frame[fields["rent_price_band"]].astype(str).str.strip() if fields["rent_price_band"] else pd.NA,
            "avg_monthly_rent_eur": frame[fields["avg_monthly_rent_eur"]].map(parse_number),
            "avg_rent_per_m2_eur": frame[fields["avg_rent_per_m2_eur"]].map(parse_number) if fields["avg_rent_per_m2_eur"] else pd.NA,
        }
    )
    panel = panel.dropna(subset=["year", "municipality_name", "avg_monthly_rent_eur"]).copy()
    panel["year"] = panel["year"].astype(int)
    panel["municipality_name_norm"] = panel["municipality_name"].map(normalise_name)
    panel["period"] = panel.apply(
        lambda row: f"{int(row['year'])}Q{int(row['quarter'])}" if pd.notna(row["quarter"]) else str(int(row["year"])),
        axis=1,
    )
    panel["country_name"] = "Spain"
    panel["region_name"] = "Catalonia"
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_dataset_id"] = DATASET_ID
    panel["source_url"] = SOURCE_URL

    panel = attach_city_matches(panel, city_spine_path)
    ordered = [
        "year",
        "quarter",
        "period",
        "country_name",
        "region_name",
        "municipality_code",
        "municipality_name",
        "municipality_name_norm",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "contracts",
        "rent_price_band",
        "avg_monthly_rent_eur",
        "avg_rent_per_m2_eur",
        "source_dataset",
        "source_dataset_id",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["year", "quarter", "municipality_name"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "municipality_count": int(panel["municipality_name_norm"].nunique()),
        "matched_municipalities": int(panel[["municipality_name_norm", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "rent_price_band_count": int(panel["rent_price_band"].nunique(dropna=True)),
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
    path = manifest_dir / f"fetch_run_{run_stamp}_catalonia_rent_contracts.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "catalonia_rent_contracts_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="generalitat_catalunya_open_data",
        series_id="catalonia_rent_contracts_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="quarterly or annual, as published",
        units="rental contracts and euros",
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
                "Generalitat Socrata rent-contract rows normalized to municipality-period observations. "
                "Municipality names are matched to the Spain subset of the GHSL top-1000 spine where unambiguous."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local JSON or CSV dump of the Socrata rows.")
    parser.add_argument("--output", default="data/derived/catalonia_rent_contracts_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_rows = load_input(path_arg(args.input).resolve()) if args.input else None
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        rows=input_rows,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK generalitat_catalunya_open_data:catalonia_rent_contracts_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
