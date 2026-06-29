#!/usr/bin/env python3
"""Build the Eurostat Cities / Urban Audit covariate-and-supply panel.

Pulls JSON-stat from the Eurostat dissemination API (key-free, open) for a
curated set of Urban Audit (``urb_*``) datasets that carry housing supply,
living-condition, and population indicators at the city (Urban Audit code)
grain. The panel is long-format with one row per
``(eurostat_city_code, year, indicator)``. Eurostat city codes and city
names are preserved, and each row is crosswalked (by name + country) to the
IESET / GHSL top-1000 city universe with a ``ghsl_match_flag``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
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

API_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
METHODOLOGY_URL = "https://ec.europa.eu/eurostat/web/cities/methodology"
LICENSE = "Eurostat reuse policy (CC BY 4.0 equivalent); attribute Eurostat"
PUBLISHER = "eurostat"
SERIES_ID = "eurostat_city_urban_audit_panel"

# Curated indicator subset per dataset. Restricting the population pull to the
# total/male/female headline series keeps the panel focused on covariates and
# housing supply rather than the full 75-band age pyramid.
DATASETS: dict[str, dict[str, Any]] = {
    "urb_clivcon": {
        "theme": "living_conditions_and_housing",
        "indicators": [
            "DE3001V",  # Private households (excl. institutional)
            "DE3017V",  # Population living in private households
            "SA1001V",  # Number of conventional dwellings
            "SA1004V",  # Number of houses
            "SA1005V",  # Number of apartments
            "SA1007V",  # Households living in houses
            "SA1008V",  # Households living in apartments
            "SA1011V",  # Households owning their own dwelling
            "SA1012V",  # Households in social housing
            "SA1013V",  # Households in private rented housing
            "SA1050V",  # Average price for buying a house - EUR
            "SA1051V",  # Average price for buying an apartment - EUR
            "SA1049V",  # Average annual rent for housing per m2 - EUR
            "SA1018V",  # Dwellings lacking basic amenities
            "SA1025V",  # Empty conventional dwellings
        ],
    },
    "urb_cpop1": {
        "theme": "population",
        "indicators": [
            "DE1001V",  # Population on the 1st of January, total
            "DE1002V",  # Population on the 1st of January, male
            "DE1003V",  # Population on the 1st of January, female
        ],
    },
}

# Eurostat city-code 2-letter prefix -> GHSL/IESET country_name. Eurostat uses
# EL for Greece and UK for the United Kingdom (not ISO-2 GR / GB).
EUROSTAT_PREFIX_TO_COUNTRY = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CH": "Switzerland",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DK": "Denmark",
    "EE": "Estonia",
    "EL": "Greece",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MT": "Malta",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "TR": "Turkey",
    "UK": "United Kingdom",
}

# Spine may spell some countries differently; accept these aliases when joining.
COUNTRY_NAME_ALIASES = {
    "Czechia": {"Czechia", "Czech Republic"},
    "Turkey": {"Turkey", "Turkiye", "Türkiye"},
    "United Kingdom": {"United Kingdom", "UK", "Great Britain"},
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


_GREATER_CITY_SUFFIXES = re.compile(
    r"\s*\((greater city|kreisfreie stadt|city)\)\s*$", re.IGNORECASE
)


def clean_city_name(label: str) -> str:
    """Drop the Eurostat "(greater city)" / "(city)" qualifier for matching/display."""
    return _GREATER_CITY_SUFFIXES.sub("", str(label)).strip()


def normalise_name(value: object) -> str:
    text = "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    # A Eurostat label can carry alternate spellings split by "/" (e.g.
    # "Bruxelles/Brussel"); keep the first form for the normalised key.
    text = text.split("/")[0]
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_jsonstat(dataset: str, *, session: requests.Session | None = None, timeout: int = 180) -> dict[str, Any]:
    url = f"{API_BASE}{dataset}"
    getter = session.get if session is not None else requests.get
    response = getter(
        url,
        params={"format": "JSON"},
        timeout=timeout,
        headers={"User-Agent": "IESET city-level data builder"},
    )
    response.raise_for_status()
    return response.json()


def jsonstat_to_rows(dataset: str, payload: dict[str, Any], wanted_indicators: list[str]) -> list[dict[str, Any]]:
    """Decode a JSON-stat 2.0 cube into long rows for the wanted indicators.

    JSON-stat stores a dense value map keyed by a flattened multi-index over the
    dimensions listed in ``id`` with sizes in ``size``. We compute the linear
    index for each (indicator, city, time) cell and read sparse values.
    """
    dim_ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]
    dimension = payload["dimension"]
    values = payload["value"]
    if isinstance(values, list):
        value_map: dict[int, Any] = {i: v for i, v in enumerate(values) if v is not None}
    else:
        value_map = {int(k): v for k, v in values.items() if v is not None}

    # Per-dimension ordered category codes + label maps.
    cat_index: dict[str, list[str]] = {}
    cat_label: dict[str, dict[str, str]] = {}
    for did in dim_ids:
        category = dimension[did]["category"]
        index = category["index"]
        if isinstance(index, dict):
            ordered = sorted(index, key=lambda k: index[k])
        else:
            ordered = list(index)
        cat_index[did] = ordered
        cat_label[did] = category.get("label", {})

    # Strides for the flattened index (row-major over dim_ids order).
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    indic_dim = "indic_ur"
    city_dim = "cities"
    time_dim = "time"
    for required in (indic_dim, city_dim, time_dim):
        if required not in dim_ids:
            raise ValueError(f"dataset {dataset} missing expected dimension {required!r}; got {dim_ids}")

    indic_pos = dim_ids.index(indic_dim)
    city_pos = dim_ids.index(city_dim)
    time_pos = dim_ids.index(time_dim)

    # Fixed positions for any singleton dimensions (e.g. freq) — always index 0.
    fixed: dict[int, int] = {}
    for pos, did in enumerate(dim_ids):
        if did not in (indic_dim, city_dim, time_dim):
            fixed[pos] = 0  # singleton

    indic_codes = cat_index[indic_dim]
    indic_labels = cat_label[indic_dim]
    city_codes = cat_index[city_dim]
    city_labels = cat_label[city_dim]
    time_codes = cat_index[time_dim]

    wanted = [c for c in wanted_indicators if c in indic_codes]

    rows: list[dict[str, Any]] = []
    for indic_code in wanted:
        i_idx = indic_codes.index(indic_code)
        indic_label = indic_labels.get(indic_code, indic_code)
        for c_idx, city_code in enumerate(city_codes):
            # City-level Urban Audit codes are 6 chars ending in C; 2-letter
            # codes are national aggregates and are excluded from the city grain.
            if len(city_code) <= 2 or not city_code.endswith("C"):
                continue
            prefix = city_code[:2]
            country_name = EUROSTAT_PREFIX_TO_COUNTRY.get(prefix)
            city_label = clean_city_name(city_labels.get(city_code, city_code))
            for t_idx, time_code in enumerate(time_codes):
                # Build the flattened linear index.
                linear = 0
                for pos, did in enumerate(dim_ids):
                    if pos == indic_pos:
                        coord = i_idx
                    elif pos == city_pos:
                        coord = c_idx
                    elif pos == time_pos:
                        coord = t_idx
                    else:
                        coord = fixed[pos]
                    linear += coord * strides[pos]
                value = value_map.get(linear)
                if value is None:
                    continue
                try:
                    year = int(time_code)
                except ValueError:
                    continue
                rows.append(
                    {
                        "eurostat_city_code": city_code,
                        "eurostat_city_name": city_label,
                        "country_iso2_eurostat": prefix,
                        "country_name": country_name,
                        "year": year,
                        "indicator": indic_code,
                        "indicator_label": indic_label,
                        "value": float(value),
                        "dataset": dataset,
                        "dataset_theme": DATASETS[dataset]["theme"],
                    }
                )
    return rows


def load_spine(city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    if city_spine_path.suffix.lower() == ".csv":
        return pd.read_csv(city_spine_path)
    return pd.read_parquet(city_spine_path)


def build_spine_lookup(spine: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    """Map (normalised city name, country_name) -> spine row info."""
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in spine.to_dict("records"):
        country = row.get("country_name")
        name = row.get("city_name")
        if country is None or name is None:
            continue
        key = (normalise_name(name), str(country))
        # Prefer the higher-ranked (smaller rank number) city on collisions.
        existing = lookup.get(key)
        rank = row.get("city_rank_2025")
        if existing is not None and existing.get("_rank") is not None and rank is not None:
            if rank >= existing["_rank"]:
                continue
        lookup[key] = {
            "ieset_city_id": row.get("ieset_city_id"),
            "ghsl_city_id": row.get("ghsl_city_id"),
            "ghsl_city_name": row.get("city_name"),
            "ghsl_city_rank_2025": row.get("city_rank_2025"),
            "_rank": rank,
        }
    return lookup


def _country_candidates(country_name: str | None) -> list[str]:
    if country_name is None:
        return []
    return list(COUNTRY_NAME_ALIASES.get(country_name, {country_name}))


def attach_ghsl_matches(panel: pd.DataFrame, spine: pd.DataFrame) -> pd.DataFrame:
    lookup = build_spine_lookup(spine)
    # Match at the city level, then broadcast onto rows.
    city_keys = panel[["eurostat_city_code", "eurostat_city_name", "country_name"]].drop_duplicates()
    records = []
    for row in city_keys.to_dict("records"):
        name_norm = normalise_name(row["eurostat_city_name"])
        match = None
        for country in _country_candidates(row["country_name"]):
            match = lookup.get((name_norm, country))
            if match is not None:
                break
        if match is not None:
            records.append(
                {
                    "eurostat_city_code": row["eurostat_city_code"],
                    "ieset_city_id": match["ieset_city_id"],
                    "ghsl_city_id": match["ghsl_city_id"],
                    "ghsl_city_name": match["ghsl_city_name"],
                    "ghsl_city_rank_2025": match["ghsl_city_rank_2025"],
                    "ghsl_match_flag": True,
                    "ghsl_match_type": "name_country_exact",
                }
            )
        else:
            records.append(
                {
                    "eurostat_city_code": row["eurostat_city_code"],
                    "ieset_city_id": None,
                    "ghsl_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "ghsl_match_flag": False,
                    "ghsl_match_type": "unmatched",
                }
            )
    match_df = pd.DataFrame(records)
    return panel.merge(match_df, on="eurostat_city_code", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    payloads: dict[str, dict[str, Any]] | None = None,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if payloads is None:
        payloads = {}
        for dataset in DATASETS:
            payloads[dataset] = fetch_jsonstat(dataset, session=session)

    rows: list[dict[str, Any]] = []
    dataset_urls: dict[str, str] = {}
    for dataset, spec in DATASETS.items():
        payload = payloads.get(dataset)
        if payload is None:
            continue
        dataset_urls[dataset] = f"{API_BASE}{dataset}?format=JSON"
        rows.extend(jsonstat_to_rows(dataset, payload, spec["indicators"]))

    if not rows:
        raise ValueError("Eurostat Urban Audit API returned no usable city observations")

    panel = pd.DataFrame(rows)
    spine = load_spine(city_spine_path)
    panel = attach_ghsl_matches(panel, spine)

    ordered = [
        "eurostat_city_code",
        "eurostat_city_name",
        "country_iso2_eurostat",
        "country_name",
        "year",
        "indicator",
        "indicator_label",
        "value",
        "dataset",
        "dataset_theme",
        "ieset_city_id",
        "ghsl_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "ghsl_match_flag",
        "ghsl_match_type",
    ]
    panel = panel[ordered].sort_values(
        ["eurostat_city_code", "year", "indicator"]
    ).reset_index(drop=True)

    # Drop fully duplicated grain rows defensively (same indicator appears in one
    # dataset only, but guard against overlap between datasets).
    panel = panel.drop_duplicates(subset=["eurostat_city_code", "year", "indicator"]).reset_index(drop=True)

    matched_cities = panel.loc[panel["ghsl_match_flag"], "eurostat_city_code"].nunique()
    indicators_present = sorted(panel["indicator"].unique())
    indicator_labels = (
        panel.drop_duplicates("indicator").set_index("indicator")["indicator_label"].to_dict()
    )
    stats = {
        "panel_rows": int(len(panel)),
        "city_count": int(panel["eurostat_city_code"].nunique()),
        "matched_city_count": int(matched_cities),
        "unmatched_city_count": int(panel["eurostat_city_code"].nunique() - matched_cities),
        "match_rate": round(matched_cities / max(panel["eurostat_city_code"].nunique(), 1), 4),
        "country_count": int(panel["country_iso2_eurostat"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "indicator_count": len(indicators_present),
        "indicators": indicators_present,
        "indicator_labels": indicator_labels,
        "datasets": dataset_urls,
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_eurostat_city_urban_audit.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "eurostat_city_urban_audit_panel",
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    primary_url = next(iter(stats["datasets"].values()), API_BASE)
    return FetchResult(
        publisher=PUBLISHER,
        series_id=SERIES_ID,
        source_url=primary_url,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="mixed per indicator (counts, EUR prices, EUR rent per m2)",
        currency="EUR",
        start_date=str(stats["year_min"]),
        end_date=str(stats["year_max"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Eurostat dissemination API (key-free) JSON-stat pulled for curated Urban Audit "
                "datasets (housing/living conditions + headline population). Decoded to one row per "
                "(eurostat_city_code, year, indicator); national aggregate codes excluded. Crosswalked "
                "to the IESET/GHSL top-1000 city universe by normalised name + country with a "
                "ghsl_match_flag; unmatched cities retained and flagged false."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--output", default="data/derived/eurostat_city_urban_audit_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    parser.add_argument(
        "--input-dir",
        help="Optional directory of cached <dataset>.json JSON-stat files; otherwise fetch from API.",
    )
    return parser.parse_args(argv)


def load_cached_payloads(input_dir: Path) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for dataset in DATASETS:
        path = input_dir / f"{dataset}.json"
        if path.exists():
            payloads[dataset] = json.loads(path.read_text())
    if not payloads:
        raise FileNotFoundError(f"no cached <dataset>.json files found under {input_dir}")
    return payloads


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    payloads = None
    if args.input_dir:
        payloads = load_cached_payloads(path_arg(args.input_dir).resolve())
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        payloads=payloads,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        f"OK {PUBLISHER}:{SERIES_ID} rows={result.rows} "
        f"years={result.start_date}->{result.end_date} cities={stats['city_count']} "
        f"matched={stats['matched_city_count']} ({stats['match_rate']:.1%}) "
        f"indicators={stats['indicator_count']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
