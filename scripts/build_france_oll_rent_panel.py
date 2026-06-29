#!/usr/bin/env python3
"""Build a France OBSERVED market-rent panel from the Observatoires Locaux des Loyers (OLL).

The OLL network (Observatoires Locaux des Loyers) publishes annual OBSERVED private
market rents ("loyers de marché", EUR/m2 and EUR/month) by agglomeration. The national
results are released on data.gouv.fr as per-year CSV files hosted on
observatoires-des-loyers.org (KEY-FREE).

This complements the existing France reference-rent (legal ceiling) panel
(`france_reference_rents_panel`) with OBSERVED market rents.

Grain: one row per
  (observatory_code, agglomeration, data_year, zone, dwelling_type, construction_period,
   tenure_length, rooms_band)
carrying observed rent quantiles in EUR/m2 and EUR/month.

The five GHSL crosswalk targets (Paris, Lyon, Marseille, Toulouse, Nice) are matched to
the France subset of the GHSL top-1000 city spine via an explicit agglomeration->city map.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import sys
import unicodedata
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

DATASET_PAGE = "https://www.data.gouv.fr/datasets/resultats-nationaux-des-observatoires-locaux-des-loyers"
SOURCE_URL = DATASET_PAGE
METHODOLOGY_URL = "https://www.observatoires-des-loyers.org/"
LICENSE = "Licence Ouverte / Open Licence 2.0 (lov2)"
SOURCE_DATASET = "OLL national results - observed agglomeration market rents"
RENT_MEASURE_LABEL = "observed_oll_market_rent"

# KEY-FREE stable per-year CSV endpoints (data.gouv.fr resource URLs).
DEFAULT_YEARS = list(range(2014, 2026))
BASE_URL_TEMPLATE = "https://www.observatoires-des-loyers.org/datagouv/{year}/Base_OP_{year}_Nationale.csv"

# Raw OLL columns (semicolon-separated, latin-1, decimal comma).
DIM_COLUMNS = {
    "observatory_code": "Observatory",
    "data_year": "Data_year",
    "agglomeration": "agglomeration",
    "zone_complementaire": "Zone_complementaire",
    "dwelling_type": "Type_habitat",
    "construction_period": "epoque_construction_homogene",
    "tenure_length": "anciennete_locataire_homogene",
    "rooms_band": "nombre_pieces_homogene",
}
RENT_M2_COLUMNS = {
    "rent_eur_m2_decile1": "loyer_1_decile",
    "rent_eur_m2_quartile1": "loyer_1_quartile",
    "rent_eur_m2_median": "loyer_median",
    "rent_eur_m2_quartile3": "loyer_3_quartile",
    "rent_eur_m2_decile9": "loyer_9_decile",
    "rent_eur_m2_mean": "loyer_moyen",
}
RENT_MONTHLY_COLUMNS = {
    "rent_eur_month_decile1": "loyer_mensuel_1_decile",
    "rent_eur_month_quartile1": "loyer_mensuel_1_quartile",
    "rent_eur_month_median": "loyer_mensuel_median",
    "rent_eur_month_quartile3": "loyer_mensuel_3_quartile",
    "rent_eur_month_decile9": "loyer_mensuel_9_decile",
    "rent_eur_month_mean": "moyenne_loyer_mensuel",
}
EXTRA_COLUMNS = {
    "mean_surface_m2": "surface_moyenne",
    "n_observations": "nombre_observations",
    "n_dwellings": "nombre_logements",
    "production_method": "methodologie_production",
}

GRAIN_KEYS = [
    "observatory_code",
    "agglomeration",
    "data_year",
    "zone_complementaire",
    "dwelling_type",
    "construction_period",
    "tenure_length",
    "rooms_band",
]

# Explicit agglomeration -> GHSL top-1000 city map for the requested crosswalk targets.
# Keys are normalised agglomeration labels; values are the GHSL city_name in the spine.
AGGLO_TO_GHSL_CITY = {
    "AGGLOMERATION PARISIENNE": "Paris",
    "PARIS INTRA MUROS": "Paris",
    "AGGLOMERATION DE LYON": "Lyon",
    "AGGLOMERATION D AIX MARSEILLE": "Marseille",
    "AGGLOMERATION DE TOULOUSE": "Toulouse",
    "AGGLOMERATION DE NICE MENTON": "Nice",
    "AGGLOMERATION DE BORDEAUX": "Bordeaux",
    "AGGLOMERATION DE LILLE": "Lille",
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
    text = "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("'", " ").replace("-", " ")
    text = "".join(ch if ch.isalnum() else " " for ch in text)
    return " ".join(text.split())


def parse_number(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(" ", "").replace(" ", "")
    if text == "" or text.upper() in {"NA", "ND", "N/A"}:
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    number = parse_number(value)
    if number is None or pd.isna(number):
        return None
    return int(round(number))


def fetch_year_rows(year: int) -> list[dict[str, Any]]:
    url = BASE_URL_TEMPLATE.format(year=year)
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=180) as response:
        raw = response.read()
    text = raw.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    return list(reader)


def fetch_all_years(years: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in years:
        try:
            year_rows = fetch_year_rows(year)
        except Exception as exc:  # noqa: BLE001 - tolerate a missing year, fail only if all fail
            sys.stderr.write(f"warning: could not fetch OLL year {year}: {exc}\n")
            continue
        rows.extend(year_rows)
    if not rows:
        raise ValueError("OLL national results returned no rows for any requested year")
    return rows


def load_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="latin-1")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    return list(reader)


def build_ghsl_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    france = city_spine[city_spine["country_name"].eq("France")].copy()
    by_name: dict[str, dict[str, Any]] = {}
    for row in france.to_dict("records"):
        by_name[normalise_name(row["city_name"])] = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_id": row.get("ghsl_city_id"),
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": row["city_rank_2025"],
        }
    return by_name


def attach_ghsl_crosswalk(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    ghsl_by_name = build_ghsl_map(spine)

    rows = []
    for agglo_norm in panel["agglomeration_norm"].drop_duplicates():
        ghsl_city = AGGLO_TO_GHSL_CITY.get(agglo_norm)
        match = ghsl_by_name.get(normalise_name(ghsl_city)) if ghsl_city else None
        if match:
            rows.append(
                {
                    "agglomeration_norm": agglo_norm,
                    "ieset_city_id": match["ieset_city_id"],
                    "ghsl_city_id": match["ghsl_city_id"],
                    "ghsl_city_name": match["ghsl_city_name"],
                    "ghsl_city_rank_2025": match["ghsl_city_rank_2025"],
                    "ghsl_match_flag": True,
                }
            )
        else:
            rows.append(
                {
                    "agglomeration_norm": agglo_norm,
                    "ieset_city_id": None,
                    "ghsl_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "ghsl_match_flag": False,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="agglomeration_norm", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    rows: list[dict[str, Any]] | None = None,
    years: list[int] | None = None,
    fetcher: Callable[[list[int]], list[dict[str, Any]]] = fetch_all_years,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    years = years or DEFAULT_YEARS
    rows = rows if rows is not None else fetcher(years)
    if not rows:
        raise ValueError("OLL national results dataset returned no rows")
    frame = pd.DataFrame(rows)

    out: dict[str, Any] = {}
    for logical, raw in DIM_COLUMNS.items():
        if raw not in frame.columns:
            raise ValueError(f"expected OLL column {raw!r}; columns={list(frame.columns)}")
        series = frame[raw]
        if logical == "data_year":
            out[logical] = series.map(parse_int)
        else:
            out[logical] = series.fillna("").astype(str).str.strip().replace({"": pd.NA})
    for logical, raw in {**RENT_M2_COLUMNS, **RENT_MONTHLY_COLUMNS, "mean_surface_m2": EXTRA_COLUMNS["mean_surface_m2"]}.items():
        out[logical] = frame[raw].map(parse_number) if raw in frame.columns else pd.NA
    for logical in ("n_observations", "n_dwellings"):
        raw = EXTRA_COLUMNS[logical]
        out[logical] = frame[raw].map(parse_int) if raw in frame.columns else pd.NA
    out["production_method"] = (
        frame[EXTRA_COLUMNS["production_method"]].fillna("").astype(str).str.strip().replace({"": pd.NA})
        if EXTRA_COLUMNS["production_method"] in frame.columns
        else pd.NA
    )

    panel = pd.DataFrame(out)
    # Require year + agglomeration + at least one observed rent measure.
    panel = panel.dropna(subset=["data_year", "agglomeration"]).copy()
    rent_cols = list(RENT_M2_COLUMNS.keys()) + list(RENT_MONTHLY_COLUMNS.keys())
    panel = panel[panel[rent_cols].notna().any(axis=1)].copy()
    if panel.empty:
        raise ValueError("OLL dataset had rows, but none carried a year + agglomeration + observed rent")

    panel["data_year"] = panel["data_year"].astype(int)
    panel["country_name"] = "France"
    panel["agglomeration_norm"] = panel["agglomeration"].map(normalise_name)
    panel["rent_measure"] = RENT_MEASURE_LABEL
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = SOURCE_URL

    panel = attach_ghsl_crosswalk(panel, city_spine_path)

    ordered = (
        [
            "data_year",
            "country_name",
            "observatory_code",
            "agglomeration",
            "agglomeration_norm",
            "zone_complementaire",
            "ieset_city_id",
            "ghsl_city_id",
            "ghsl_city_name",
            "ghsl_city_rank_2025",
            "ghsl_match_flag",
            "dwelling_type",
            "construction_period",
            "tenure_length",
            "rooms_band",
        ]
        + list(RENT_M2_COLUMNS.keys())
        + list(RENT_MONTHLY_COLUMNS.keys())
        + [
            "mean_surface_m2",
            "n_observations",
            "n_dwellings",
            "production_method",
            "rent_measure",
            "source_dataset",
            "source_url",
        ]
    )
    panel = panel[ordered]
    # Some source-year files (notably 2020) contain fully-identical duplicate rows.
    # Drop only exact duplicates across every column, then guarantee grain uniqueness.
    before_dedup = len(panel)
    panel = panel.drop_duplicates().reset_index(drop=True)
    exact_duplicates_dropped = before_dedup - len(panel)

    key = panel[GRAIN_KEYS].astype(object).where(panel[GRAIN_KEYS].notna(), "__NA__")
    if key.duplicated().any():
        raise ValueError(
            f"{int(key.duplicated().sum())} rows collide on grain {GRAIN_KEYS} with differing measures; "
            "source cells are not uniquely keyed"
        )

    panel = panel.sort_values(GRAIN_KEYS, na_position="last").reset_index(drop=True)

    matched = panel[panel["ghsl_match_flag"]]
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["data_year"].min()),
        "end_year": int(panel["data_year"].max()),
        "observatory_count": int(panel["observatory_code"].nunique(dropna=True)),
        "agglomeration_count": int(panel["agglomeration_norm"].nunique()),
        "ghsl_matched_rows": int(panel["ghsl_match_flag"].sum()),
        "ghsl_matched_cities": int(matched["ieset_city_id"].nunique(dropna=True)),
        "matched_city_names": sorted(matched["ghsl_city_name"].dropna().unique().tolist()),
        "rent_measure": RENT_MEASURE_LABEL,
        "exact_duplicate_rows_dropped": int(exact_duplicates_dropped),
    }
    return panel, stats


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_france_oll_rent.yaml"
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    doc = {"run_utc": run_stamp, "pipeline": "france_oll_rent_panel", "entries": [payload]}
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    return path


def emit(
    panel: pd.DataFrame,
    stats: dict[str, Any],
    output_path: Path,
    fetch_ts: datetime,
    source_urls: list[str],
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="observatoires_locaux_des_loyers",
        series_id="france_oll_rent_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="euros per square metre and euros per month",
        currency="EUR",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "rent_measure_label": (
                "OBSERVED OLL market rent (loyers de marche). Per-cell rents are produced by the "
                "observatories either by direct estimation ('Estimation directe') or by an econometric "
                "market-value model ('Estimation econometrique (pour valeur de marche)'); the per-row "
                "method is preserved in production_method."
            ),
            "fetched_source_urls": source_urls,
            "construction": (
                "OLL national agglomeration results (per-year CSV) concatenated across years and normalised "
                "to one row per (observatory, agglomeration, year, zone, dwelling type, construction period, "
                "tenure length, rooms band). Observed rent quantiles kept in EUR/m2 and EUR/month. The five "
                "requested GHSL targets (Paris, Lyon, Marseille, Toulouse, Nice) are crosswalked to the France "
                "subset of the GHSL top-1000 city spine via an explicit agglomeration->city map; ghsl_match_flag "
                "marks matched rows. Original INSEE-linked observatory codes and agglomeration labels preserved."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local OLL CSV dump (semicolon, latin-1).")
    parser.add_argument("--years", help="Comma-separated years to fetch (default 2014-2025).")
    parser.add_argument("--output", default="data/derived/france_oll_rent_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    years = [int(y) for y in args.years.split(",")] if args.years else DEFAULT_YEARS
    input_rows = load_input(path_arg(args.input).resolve()) if args.input else None
    source_urls = [BASE_URL_TEMPLATE.format(year=y) for y in years]
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        rows=input_rows,
        years=years,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts, source_urls)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK observatoires_locaux_des_loyers:france_oll_rent_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} "
        f"matched_cities={stats['ghsl_matched_cities']} ({','.join(stats['matched_city_names'])})"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
