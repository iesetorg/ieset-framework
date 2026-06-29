#!/usr/bin/env python3
"""Build the Ireland RTB Rent Index (RPZ) standardised-rent panel.

Pulls JSON-stat 2.0 from the CSO (Central Statistics Office) PxStat open read
API (key-free) for the RTB Average Monthly Rent Report (RTB Rent Index,
produced by the RTB with the ESRI). Table ``RIA02`` carries the official
standardised average monthly rent in EUR by Year x Number of Bedrooms x
Property Type x Location for the whole of Ireland (2008-present), the exact
measure underpinning Rent Pressure Zone (RPZ) designation.

The panel is long-format with one row per
``(location_code, year, bedrooms_code, property_type_code)``. The CSO/RTB
location codes and labels are preserved verbatim. RPZ-relevant urban centres
(Dublin, Cork, Galway, Limerick, Waterford) are crosswalked to the IESET/GHSL
top-1000 city universe by curated location-code mapping with a
``ghsl_match_flag``; all other locations are retained and flagged false.
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

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location(
        "ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py"
    )
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

import yaml  # noqa: E402  (yaml is a base dependency; imported after base load for parity)

# CSO PxStat read API (key-free): ReadDataset returns JSON-stat 2.0.
API_BASE = (
    "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/"
    "{table}/JSON-stat/2.0/en"
)
TABLE = "RIA02"  # RTB Average Monthly Rent Report (annual)
SOURCE_URL = API_BASE.format(table=TABLE)
METHODOLOGY_URL = "https://www.rtb.ie/about-rtb/data-insights/data-hub/rent-index"
LICENSE = "CSO / RTB open data (Creative Commons BY 4.0); attribute CSO & RTB"
PUBLISHER = "ireland_rtb_cso"
SERIES_ID = "ireland_rtb_rent_index_panel"

# JSON-stat dimension ids in table RIA02.
STATISTIC_DIM = "STATISTIC"
TIME_DIM = "TLIST(A1)"
BEDROOMS_DIM = "C02970V03592"
PROPTYPE_DIM = "C02969V03591"
LOCATION_DIM = "C03004V03625"

# RPZ-relevant urban centres -> IESET/GHSL top-1000 crosswalk. The RTB location
# code for the headline county/city total maps to the GHSL urban centre. Only
# Dublin is currently in the IESET top-1000 spine; Cork/Galway/Limerick/
# Waterford codes are kept here so the match resolves automatically if/when the
# spine is expanded. ``ghsl_match_flag`` is set true only when the spine join
# actually resolves a GHSL id.
RPZ_LOCATION_TO_CITY = {
    "120500": "Dublin",
    "113000": "Cork",
    "115200": "Cork",
    "140200": "Galway",
    "141600": "Galway",
    "150100": "Limerick",
    "151900": "Limerick",
    "164000": "Waterford",
    "167100": "Waterford",
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
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_jsonstat(*, session: requests.Session | None = None, timeout: int = 180) -> dict[str, Any]:
    getter = session.get if session is not None else requests.get
    response = getter(
        SOURCE_URL,
        timeout=timeout,
        headers={"User-Agent": "IESET city-level data builder"},
    )
    response.raise_for_status()
    return response.json()


def _ordered_codes(category: dict[str, Any]) -> list[str]:
    index = category["index"]
    if isinstance(index, dict):
        return sorted(index, key=lambda k: index[k])
    return list(index)


def jsonstat_to_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Decode the RIA02 JSON-stat 2.0 cube into long standardised-rent rows."""
    dim_ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]
    dimension = payload["dimension"]
    values = payload["value"]
    if isinstance(values, list):
        value_map: dict[int, Any] = {i: v for i, v in enumerate(values) if v is not None}
    else:
        value_map = {int(k): v for k, v in values.items() if v is not None}

    for required in (STATISTIC_DIM, TIME_DIM, BEDROOMS_DIM, PROPTYPE_DIM, LOCATION_DIM):
        if required not in dim_ids:
            raise ValueError(
                f"RIA02 payload missing expected dimension {required!r}; got {dim_ids}"
            )

    cat = {did: dimension[did]["category"] for did in dim_ids}
    codes = {did: _ordered_codes(cat[did]) for did in dim_ids}
    labels = {did: cat[did].get("label", {}) for did in dim_ids}

    # Row-major strides over dim_ids order.
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    pos = {did: dim_ids.index(did) for did in dim_ids}

    stat_codes = codes[STATISTIC_DIM]
    stat_labels = labels[STATISTIC_DIM]
    time_codes = codes[TIME_DIM]
    bed_codes = codes[BEDROOMS_DIM]
    bed_labels = labels[BEDROOMS_DIM]
    prop_codes = codes[PROPTYPE_DIM]
    prop_labels = labels[PROPTYPE_DIM]
    loc_codes = codes[LOCATION_DIM]
    loc_labels = labels[LOCATION_DIM]

    # Singleton statistic dimension (the rent measure). Always index 0.
    stat_idx = 0
    statistic_code = stat_codes[stat_idx]
    statistic_label = stat_labels.get(statistic_code, statistic_code)

    rows: list[dict[str, Any]] = []
    for t_idx, time_code in enumerate(time_codes):
        try:
            year = int(time_code)
        except ValueError:
            continue
        for b_idx, bed_code in enumerate(bed_codes):
            bed_label = bed_labels.get(bed_code, bed_code)
            for p_idx, prop_code in enumerate(prop_codes):
                prop_label = prop_labels.get(prop_code, prop_code)
                for l_idx, loc_code in enumerate(loc_codes):
                    coord = {
                        STATISTIC_DIM: stat_idx,
                        TIME_DIM: t_idx,
                        BEDROOMS_DIM: b_idx,
                        PROPTYPE_DIM: p_idx,
                        LOCATION_DIM: l_idx,
                    }
                    linear = sum(coord[did] * strides[pos[did]] for did in dim_ids)
                    value = value_map.get(linear)
                    if value is None:
                        continue
                    rows.append(
                        {
                            "location_code": loc_code,
                            "location_name": loc_labels.get(loc_code, loc_code),
                            "year": year,
                            "bedrooms_code": bed_code,
                            "bedrooms_label": bed_label,
                            "property_type_code": prop_code,
                            "property_type_label": prop_label,
                            "statistic_code": statistic_code,
                            "statistic_label": statistic_label,
                            "standardised_avg_rent_eur": float(value),
                            "rent_measure": "RTB standardised average monthly rent (official)",
                            "currency": "EUR",
                        }
                    )
    return rows


def load_spine(city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    if city_spine_path.suffix.lower() == ".csv":
        return pd.read_csv(city_spine_path)
    return pd.read_parquet(city_spine_path)


def build_spine_lookup(spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Map normalised Irish city name -> spine row info (Ireland rows only)."""
    lookup: dict[str, dict[str, Any]] = {}
    for row in spine.to_dict("records"):
        if str(row.get("country_name")) != "Ireland":
            continue
        name = row.get("city_name")
        if name is None:
            continue
        lookup[normalise_name(name)] = {
            "ieset_city_id": row.get("ieset_city_id"),
            "ghsl_city_id": row.get("ghsl_city_id"),
            "ghsl_city_name": row.get("city_name"),
            "ghsl_city_rank_2025": row.get("city_rank_2025"),
        }
    return lookup


def attach_ghsl_matches(panel: pd.DataFrame, spine: pd.DataFrame) -> pd.DataFrame:
    lookup = build_spine_lookup(spine)
    loc_keys = panel[["location_code"]].drop_duplicates()
    records = []
    for loc_code in loc_keys["location_code"].tolist():
        city = RPZ_LOCATION_TO_CITY.get(loc_code)
        match = lookup.get(normalise_name(city)) if city else None
        if match is not None:
            records.append(
                {
                    "location_code": loc_code,
                    "ieset_city_id": match["ieset_city_id"],
                    "ghsl_city_id": match["ghsl_city_id"],
                    "ghsl_city_name": match["ghsl_city_name"],
                    "ghsl_city_rank_2025": match["ghsl_city_rank_2025"],
                    "ghsl_match_flag": True,
                    "ghsl_match_type": "rpz_location_code_curated",
                }
            )
        else:
            records.append(
                {
                    "location_code": loc_code,
                    "ieset_city_id": None,
                    "ghsl_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "ghsl_match_flag": False,
                    "ghsl_match_type": "unmatched",
                }
            )
    match_df = pd.DataFrame(records)
    return panel.merge(match_df, on="location_code", how="left")


GRAIN = ["location_code", "year", "bedrooms_code", "property_type_code"]

ORDERED_COLUMNS = [
    "location_code",
    "location_name",
    "year",
    "bedrooms_code",
    "bedrooms_label",
    "property_type_code",
    "property_type_label",
    "statistic_code",
    "statistic_label",
    "standardised_avg_rent_eur",
    "rent_measure",
    "currency",
    "ieset_city_id",
    "ghsl_city_id",
    "ghsl_city_name",
    "ghsl_city_rank_2025",
    "ghsl_match_flag",
    "ghsl_match_type",
]


def build_panel(
    *,
    city_spine_path: Path,
    payload: dict[str, Any] | None = None,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if payload is None:
        payload = fetch_jsonstat(session=session)

    rows = jsonstat_to_rows(payload)
    if not rows:
        raise ValueError("CSO RIA02 read API returned no usable rent observations")

    panel = pd.DataFrame(rows)
    spine = load_spine(city_spine_path)
    panel = attach_ghsl_matches(panel, spine)

    panel = panel[ORDERED_COLUMNS].sort_values(GRAIN).reset_index(drop=True)
    panel = panel.drop_duplicates(subset=GRAIN).reset_index(drop=True)

    matched_locations = panel.loc[panel["ghsl_match_flag"], "location_code"].nunique()
    stats = {
        "panel_rows": int(len(panel)),
        "location_count": int(panel["location_code"].nunique()),
        "matched_location_count": int(matched_locations),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "bedroom_categories": sorted(panel["bedrooms_code"].unique().tolist()),
        "property_type_categories": sorted(panel["property_type_code"].unique().tolist()),
        "rent_min_eur": float(panel["standardised_avg_rent_eur"].min()),
        "rent_max_eur": float(panel["standardised_avg_rent_eur"].max()),
        "rent_median_eur": float(panel["standardised_avg_rent_eur"].median()),
        "dublin_matched": bool(
            panel.loc[panel["location_code"].eq("120500"), "ghsl_match_flag"].any()
        ),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "source_url": SOURCE_URL,
        "table": TABLE,
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_ireland_rtb_rent_index.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "ireland_rtb_rent_index_panel",
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher=PUBLISHER,
        series_id=SERIES_ID,
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="EUR per month (standardised average rent)",
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
                "CSO PxStat read API (key-free) JSON-stat 2.0 pulled for table RIA02 "
                "(RTB Average Monthly Rent Report / RTB Rent Index, produced by the RTB "
                "with the ESRI). Decoded to one row per "
                "(location_code, year, bedrooms_code, property_type_code); the official "
                "RTB standardised average monthly rent in EUR is preserved with original "
                "CSO/RTB location/bedroom/property-type codes and labels. RPZ-relevant "
                "urban centres (Dublin/Cork/Galway/Limerick/Waterford) crosswalked to the "
                "IESET/GHSL top-1000 city universe via curated RTB location-code mapping "
                "with a ghsl_match_flag; unmatched locations retained and flagged false."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--output", default="data/derived/ireland_rtb_rent_index_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    parser.add_argument(
        "--input-json",
        help="Optional cached RIA02 JSON-stat file; otherwise fetch from the CSO API.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    payload = None
    if args.input_json:
        payload = json.loads(path_arg(args.input_json).read_text())
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        payload=payload,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        f"OK {PUBLISHER}:{SERIES_ID} rows={result.rows} "
        f"years={result.start_date}->{result.end_date} "
        f"locations={stats['location_count']} matched={stats['matched_location_count']} "
        f"dublin_matched={stats['dublin_matched']} "
        f"rent_eur[{stats['rent_min_eur']:.0f}..{stats['rent_max_eur']:.0f}]"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
