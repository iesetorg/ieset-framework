#!/usr/bin/env python3
"""Build a U.S. ACS place-year housing incidence panel for city policy tests."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
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

SOURCE_URL = "https://api.census.gov/data/{year}/acs/acs5"
METHODOLOGY_URL = "https://www.census.gov/data/developers/data-sets/acs-5year.html"
LICENSE = "U.S. Census Bureau public data; API key required for data calls"
SOURCE_DATASET = "American Community Survey 5-year summary tables, place geography"

STATE_ABBR = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}

STATE_NAMES = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
}

ACS_VARIABLES = [
    "B25003_001E",
    "B25003_002E",
    "B25003_003E",
    "B25070_001E",
    "B25070_007E",
    "B25070_008E",
    "B25070_009E",
    "B25070_010E",
    "B25070_011E",
    "B25064_001E",
    "B25058_001E",
    "B19013_001E",
    "B25034_001E",
    "B25034_002E",
    "B25034_003E",
    "B25034_004E",
    "B25034_011E",
    "B25002_001E",
    "B25002_002E",
    "B25002_003E",
    "B07013_001E",
    "B07013_003E",
    "B07013_006E",
    "B07013_009E",
    "B07013_012E",
    "B07013_015E",
    "B07013_018E",
    "B25024_001E",
    "B25024_006E",
    "B25024_007E",
    "B25024_008E",
    "B25024_009E",
]

VARIABLE_LABELS = {
    "B25003_001E": "occupied_housing_units",
    "B25003_002E": "owner_occupied_housing_units",
    "B25003_003E": "renter_occupied_housing_units",
    "B25070_001E": "gross_rent_burden_total_renter_households",
    "B25070_007E": "gross_rent_30_34pct_renter_households",
    "B25070_008E": "gross_rent_35_39pct_renter_households",
    "B25070_009E": "gross_rent_40_49pct_renter_households",
    "B25070_010E": "gross_rent_50plus_pct_renter_households",
    "B25070_011E": "gross_rent_not_computed_renter_households",
    "B25064_001E": "median_gross_rent_usd",
    "B25058_001E": "median_contract_rent_usd",
    "B19013_001E": "median_household_income_usd",
    "B25034_001E": "housing_units_by_year_built_total",
    "B25034_002E": "housing_units_built_2020_or_later",
    "B25034_003E": "housing_units_built_2010_2019",
    "B25034_004E": "housing_units_built_2000_2009",
    "B25034_011E": "housing_units_built_1939_or_earlier",
    "B25002_001E": "housing_units_occupancy_total",
    "B25002_002E": "occupied_housing_units_occupancy_table",
    "B25002_003E": "vacant_housing_units",
    "B07013_001E": "mobility_householders_total",
    "B07013_003E": "mobility_renter_householders_total",
    "B07013_006E": "same_house_1y_renter_householders",
    "B07013_009E": "moved_same_county_renter_householders",
    "B07013_012E": "moved_diff_county_same_state_renter_householders",
    "B07013_015E": "moved_diff_state_renter_householders",
    "B07013_018E": "moved_abroad_renter_householders",
    "B25024_001E": "structure_units_total",
    "B25024_006E": "structures_5_to_9_units",
    "B25024_007E": "structures_10_to_19_units",
    "B25024_008E": "structures_20_to_49_units",
    "B25024_009E": "structures_50plus_units",
}

SENTINELS = {-666666666, -222222222, -333333333, -555555555, -888888888, -999999999}

PILOT_ALIAS_OVERRIDES = {
    ("NEW YORK", "36"): "NEW YORK",
    ("SAN FRANCISCO", "06"): "SAN FRANCISCO",
    ("SAINT PAUL", "27"): "SAINT PAUL",
    ("MINNEAPOLIS", "27"): "MINNEAPOLIS",
    ("LOS ANGELES", "06"): "LOS ANGELES",
    ("WASHINGTON", "11"): "WASHINGTON",
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
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"\bST[. ]+", "SAINT ", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\b(CITY|TOWN|VILLAGE|BOROUGH|CDP|MUNICIPALITY|URBAN COUNTY)\b", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def city_aliases(city_name: object) -> set[str]:
    text = "" if pd.isna(city_name) else str(city_name)
    aliases = {normalise_name(text)}
    if "[" in text and "]" in text:
        before = text.split("[", 1)[0]
        inside = text.split("[", 1)[1].split("]", 1)[0]
        aliases.add(normalise_name(before))
        aliases.add(normalise_name(inside))
    return {alias for alias in aliases if alias}


def parse_place_name(name: object, state_code: object) -> str:
    text = "" if pd.isna(name) else str(name)
    state_name = STATE_NAMES.get(str(state_code).zfill(2))
    if state_name and text.endswith(f", {state_name}"):
        text = text[: -len(f", {state_name}")]
    return text.strip()


def build_spine_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    us_spine = city_spine[city_spine["country_name"].eq("United States")].copy()
    candidates: dict[str, list[dict[str, Any]]] = {}
    for row in us_spine.to_dict("records"):
        canonical_alias = normalise_name(row["city_name"])
        for alias in city_aliases(row["city_name"]):
            candidates.setdefault(alias, []).append(
                {
                    "ieset_city_id": row["ieset_city_id"],
                    "ghsl_city_name": row["city_name"],
                    "ghsl_city_rank_2025": row["city_rank_2025"],
                    "match_type": "normalized_name" if alias == canonical_alias else "ghsl_alias",
                    "manual_review_required": bool(alias != canonical_alias or "[" in str(row["city_name"])),
                }
            )

    out = {}
    for alias, records in candidates.items():
        if len({record["ieset_city_id"] for record in records}) == 1:
            out[alias] = records[0]
    return out


def parse_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(str(value))
    except ValueError:
        return None
    if int(number) in SENTINELS:
        return None
    return number


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.where(denominator.ne(0))
    return numerator / denominator


def fetch_census_state(year: int, state_code: str, variables: list[str], api_key: str) -> list[list[str]]:
    params = {
        "get": ",".join(["NAME", *variables]),
        "for": "place:*",
        "in": f"state:{state_code}",
        "key": api_key,
    }
    url = SOURCE_URL.format(year=year) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level ACS builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        snippet = raw[:400].decode("utf-8", errors="replace")
        raise ValueError(f"Census ACS API did not return JSON for {year} state {state_code}: {snippet}") from exc
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Census ACS API returned empty payload for {year} state {state_code}")
    return payload


def payload_to_frame(payload: list[list[str]], year: int) -> pd.DataFrame:
    header = payload[0]
    rows = payload[1:]
    frame = pd.DataFrame(rows, columns=header)
    frame["acs_year"] = int(year)
    return frame


def attach_matches(frame: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path)
    aliases = build_spine_alias_map(spine)
    match_rows = []
    for row in frame[["NAME", "state", "place"]].to_dict("records"):
        state_code = str(row["state"]).zfill(2)
        place_name = parse_place_name(row["NAME"], state_code)
        place_norm = normalise_name(place_name)
        alias = PILOT_ALIAS_OVERRIDES.get((place_norm, state_code), place_norm)
        match = aliases.get(alias)
        if match:
            match_rows.append(
                {
                    "state": row["state"],
                    "place": row["place"],
                    **match,
                    "acs_place_name": place_name,
                    "acs_place_name_norm": place_norm,
                    "acs_match_name": alias,
                }
            )
        else:
            match_rows.append(
                {
                    "state": row["state"],
                    "place": row["place"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                    "acs_place_name": place_name,
                    "acs_place_name_norm": place_norm,
                    "acs_match_name": alias,
                }
            )
    return frame.merge(pd.DataFrame(match_rows), on=["state", "place"], how="left")


def derive_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for variable, label in VARIABLE_LABELS.items():
        out[label] = out[variable].map(parse_number)

    out["gross_rent_burden_30plus_renter_households"] = out[
        [
            "gross_rent_30_34pct_renter_households",
            "gross_rent_35_39pct_renter_households",
            "gross_rent_40_49pct_renter_households",
            "gross_rent_50plus_pct_renter_households",
        ]
    ].sum(axis=1, min_count=1)
    out["gross_rent_burden_computed_renter_households"] = (
        out["gross_rent_burden_total_renter_households"] - out["gross_rent_not_computed_renter_households"].fillna(0)
    )
    out["gross_rent_burden_30plus_share"] = safe_divide(
        out["gross_rent_burden_30plus_renter_households"],
        out["gross_rent_burden_computed_renter_households"],
    )
    out["gross_rent_burden_50plus_share"] = safe_divide(
        out["gross_rent_50plus_pct_renter_households"],
        out["gross_rent_burden_computed_renter_households"],
    )
    out["renter_share_occupied_housing_units"] = safe_divide(
        out["renter_occupied_housing_units"],
        out["occupied_housing_units"],
    )
    out["vacancy_rate"] = safe_divide(out["vacant_housing_units"], out["housing_units_occupancy_total"])
    out["housing_units_built_2010plus"] = out[
        ["housing_units_built_2020_or_later", "housing_units_built_2010_2019"]
    ].sum(axis=1, min_count=1)
    out["housing_units_built_2000plus"] = out[
        ["housing_units_built_2020_or_later", "housing_units_built_2010_2019", "housing_units_built_2000_2009"]
    ].sum(axis=1, min_count=1)
    out["multifamily_5plus_structures"] = out[
        ["structures_5_to_9_units", "structures_10_to_19_units", "structures_20_to_49_units", "structures_50plus_units"]
    ].sum(axis=1, min_count=1)
    out["multifamily_5plus_share_structures"] = safe_divide(out["multifamily_5plus_structures"], out["structure_units_total"])
    out["renter_moved_1y_householders"] = out[
        [
            "moved_same_county_renter_householders",
            "moved_diff_county_same_state_renter_householders",
            "moved_diff_state_renter_householders",
            "moved_abroad_renter_householders",
        ]
    ].sum(axis=1, min_count=1)
    out["renter_moved_1y_share"] = safe_divide(out["renter_moved_1y_householders"], out["mobility_renter_householders_total"])
    return out


def build_panel(
    *,
    city_spine_path: Path,
    years: list[int],
    states: list[str],
    api_key: str,
    fetcher: Callable[[int, str, list[str], str], list[list[str]]] = fetch_census_state,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not api_key:
        raise ValueError("Census ACS API key required. Pass --api-key or set CENSUS_API_KEY.")

    frames = []
    query_count = 0
    for year in years:
        for state_code in states:
            payload = fetcher(year, state_code.zfill(2), ACS_VARIABLES, api_key)
            frames.append(payload_to_frame(payload, year))
            query_count += 1
            time.sleep(0.05)
    if not frames:
        raise ValueError("no ACS frames fetched")

    raw = pd.concat(frames, ignore_index=True)
    raw["state"] = raw["state"].astype(str).str.zfill(2)
    raw["place"] = raw["place"].astype(str).str.zfill(5)
    raw["acs_place_geoid"] = raw["state"] + raw["place"]
    raw["state_abbr"] = raw["state"].map(STATE_ABBR)
    raw["state_name"] = raw["state"].map(STATE_NAMES)
    matched = attach_matches(raw, city_spine_path)
    panel = derive_metrics(matched)
    panel["country_name"] = "United States"
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = panel["acs_year"].map(lambda year: SOURCE_URL.format(year=year))

    ordered = [
        "acs_year",
        "acs_place_geoid",
        "acs_place_name",
        "state",
        "state_abbr",
        "state_name",
        "place",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "country_name",
        "occupied_housing_units",
        "owner_occupied_housing_units",
        "renter_occupied_housing_units",
        "renter_share_occupied_housing_units",
        "gross_rent_burden_total_renter_households",
        "gross_rent_burden_computed_renter_households",
        "gross_rent_burden_30plus_renter_households",
        "gross_rent_burden_30plus_share",
        "gross_rent_50plus_pct_renter_households",
        "gross_rent_burden_50plus_share",
        "median_gross_rent_usd",
        "median_contract_rent_usd",
        "median_household_income_usd",
        "housing_units_occupancy_total",
        "vacant_housing_units",
        "vacancy_rate",
        "housing_units_by_year_built_total",
        "housing_units_built_2010plus",
        "housing_units_built_2000plus",
        "housing_units_built_1939_or_earlier",
        "multifamily_5plus_structures",
        "multifamily_5plus_share_structures",
        "mobility_renter_householders_total",
        "same_house_1y_renter_householders",
        "renter_moved_1y_householders",
        "renter_moved_1y_share",
        "source_dataset",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["acs_year", "state", "place"]).reset_index(drop=True)

    stats = {
        "panel_rows": int(len(panel)),
        "years": sorted(int(year) for year in panel["acs_year"].unique()),
        "state_count": int(panel["state"].nunique()),
        "place_count": int(panel["acs_place_geoid"].nunique()),
        "matched_places": int(panel[["acs_place_geoid", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "query_count": query_count,
        "variables": ACS_VARIABLES,
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_us_acs_place_housing_incidence.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "us_acs_place_housing_incidence_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="us_census_acs",
        series_id="us_acs_place_housing_incidence_panel",
        source_url="https://api.census.gov/data/{year}/acs/acs5",
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual ACS 5-year vintage",
        units="ACS estimates and derived shares",
        currency="USD",
        start_date=str(min(stats["years"])),
        end_date=str(max(stats["years"])),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "ACS 5-year summary table estimates at Census place geography. "
                "Rows are name-matched to GHSL U.S. top-1000 cities where unambiguous; "
                "ambiguous and unmatched places are retained with review flags."
            ),
        },
    )


def parse_years(value: str) -> list[int]:
    years = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not years:
        raise argparse.ArgumentTypeError("at least one year is required")
    return years


def parse_states(value: str) -> list[str]:
    if value.lower() == "all":
        return sorted(STATE_ABBR)
    states = [part.strip().zfill(2) for part in value.split(",") if part.strip()]
    unknown = [state for state in states if state not in STATE_ABBR]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown Census state codes: {', '.join(unknown)}")
    return states


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.csv")
    parser.add_argument("--output", default="data/derived/us_acs_place_housing_incidence_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--years", type=parse_years, default=[2024], help="Comma-separated ACS 5-year vintages.")
    parser.add_argument("--states", type=parse_states, default=sorted(STATE_ABBR), help="Comma-separated Census state FIPS or 'all'.")
    parser.add_argument("--api-key", default=os.environ.get("CENSUS_API_KEY"), help="Census API key; defaults to CENSUS_API_KEY.")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        years=args.years,
        states=args.states,
        api_key=args.api_key or "",
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK us_census_acs:us_acs_place_housing_incidence_panel "
        f"rows={result.rows} years={stats['years']} matched_places={stats['matched_places']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
