#!/usr/bin/env python3
"""Build New Zealand Tenancy Services rental-bond rent panel from the official monthly TLA CSV.

Source: MBIE / Tenancy Services "Rental bond data" — detailed monthly rents by
territorial authority (TLA), key-free CSV at tenancy.govt.nz. Each row is an
observed bond-lodgement aggregate for a territorial authority in a month: lodged/
active/closed bond counts plus median, geometric-mean, and quartile weekly rents.

The monthly TLA file aggregates across all bedroom counts and dwelling types, so
the panel grain is (territorial_authority, period, bedroom_band) with bedroom_band
fixed to "ALL". Original Location Id / Location labels are preserved. Major TLAs
(Auckland, Wellington, Christchurch, ...) are crosswalked to GHSL urban-centre IDs
via the city universe spine; ghsl_match_flag records whether a match landed.
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

SOURCE_URL = (
    "https://www.tenancy.govt.nz/assets/Uploads/Tenancy/Rental-bond-data/"
    "detailed-monthly-tla-tenancy-v2.csv?m=bef970379280bdcf81464c5e8a29ab88f4ae7bca"
)
METHODOLOGY_URL = "https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/"
LICENSE = "New Zealand Tenancy Services (MBIE) open data; verify current download conditions"
SOURCE_DATASET = "New Zealand Tenancy Services rental bond data, detailed monthly by territorial authority"

# GHSL-matchable major TLAs. Keys are normalised NZ TLA labels; values are the
# normalised GHSL urban-centre city names they correspond to in the spine.
TLA_TO_GHSL_CITY = {
    "AUCKLAND": "AUCKLAND",
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


def tla_match_key(label: object) -> str:
    """Normalise a TLA label and strip the trailing 'CITY'/'DISTRICT' suffix for matching."""
    norm = normalise_name(label)
    norm = re.sub(r"\s+(CITY|DISTRICT)$", "", norm)
    return norm


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
    return None if number is None else int(round(number))


def fetch_csv_bytes(timeout: int = 180) -> bytes:
    response = requests.get(SOURCE_URL, timeout=timeout, headers={"User-Agent": "IESET city-level data builder"})
    response.raise_for_status()
    return response.content


def read_csv_bytes(path: Path | None) -> bytes:
    if path is None:
        return fetch_csv_bytes()
    return path.read_bytes()


def ghsl_match_map(city_spine_path: Path) -> dict[str, dict[str, Any]]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    nz = spine[spine["country_name"].eq("New Zealand")].copy()
    by_city_norm: dict[str, dict[str, Any]] = {}
    for row in nz.to_dict("records"):
        by_city_norm[normalise_name(row["city_name"])] = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": int(row["city_rank_2025"]),
        }
    matches: dict[str, dict[str, Any]] = {}
    for tla_key, ghsl_city_norm in TLA_TO_GHSL_CITY.items():
        info = by_city_norm.get(ghsl_city_norm)
        if info:
            matches[tla_key] = {
                **info,
                "match_type": "manual_nz_tla_to_ghsl_city_name",
                "manual_review_required": False,
            }
    return matches


def attach_ghsl_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    matches = ghsl_match_map(city_spine_path)
    rows = []
    for location in panel["location"].drop_duplicates():
        match = matches.get(tla_match_key(location))
        if match:
            rows.append(
                {
                    "location": location,
                    "ghsl_match_flag": True,
                    **match,
                }
            )
        else:
            rows.append(
                {
                    "location": location,
                    "ghsl_match_flag": False,
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_not_top1000_ghsl_city",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="location", how="left")


def normalise_period(value: object) -> str | None:
    text = "" if value is None or pd.isna(value) else str(value).strip()
    if not text:
        return None
    # Source format is ISO date YYYY-MM-DD (first of month). Reduce to YYYY-MM.
    match = re.match(r"^(\d{4})-(\d{2})-\d{2}$", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    # Fallback: D/M/YYYY style.
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if match:
        return f"{int(match.group(3)):04d}-{int(match.group(2)):02d}"
    return None


def build_panel(
    *,
    city_spine_path: Path,
    csv_bytes: bytes | None = None,
    input_csv: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    payload = csv_bytes if csv_bytes is not None else read_csv_bytes(input_csv)
    source_sha = sha256_bytes(payload)
    frame = pd.read_csv(io.BytesIO(payload), dtype=str)
    frame.columns = [str(c).strip() for c in frame.columns]

    rows: list[dict[str, Any]] = []
    for raw in frame.to_dict("records"):
        period = normalise_period(raw.get("Time Frame"))
        if period is None:
            continue
        location_id = str(raw.get("Location Id", "")).strip()
        location = str(raw.get("Location", "")).strip()
        # Skip the aggregate roll-up rows ("ALL", id -99) and the unknown bucket (id -1, "NA").
        if location.upper() in {"ALL", "NA"} or location_id in {"-99", "-1"}:
            continue
        median_rent = parse_number(raw.get("Median Rent"))
        if median_rent is None:
            continue
        year, month = period.split("-")
        rows.append(
            {
                "period": period,
                "period_type": "month",
                "year": int(year),
                "month": int(month),
                "country_name": "New Zealand",
                "location_id": location_id,
                "location": location,
                "spatial_grain": "territorial_authority",
                "bedroom_band": "ALL",
                "dwelling_type": "all",
                "lodged_bonds": parse_int(raw.get("Lodged Bonds")),
                "active_bonds": parse_int(raw.get("Active Bonds")),
                "closed_bonds": parse_int(raw.get("Closed Bonds")),
                "median_weekly_rent_nzd": median_rent,
                "geometric_mean_weekly_rent_nzd": parse_number(raw.get("Geometric Mean Rent")),
                "upper_quartile_weekly_rent_nzd": parse_number(raw.get("Upper Quartile Rent")),
                "lower_quartile_weekly_rent_nzd": parse_number(raw.get("Lower Quartile Rent")),
                "log_std_dev_weekly_rent": parse_number(raw.get("Log Std Dev Weekly Rent")),
                "rent_basis": "observed_bond_lodgement_weekly_rent",
                "source_dataset": SOURCE_DATASET,
                "source_url": SOURCE_URL,
            }
        )

    if not rows:
        raise ValueError("New Zealand Tenancy Services TLA CSV returned no rental bond rows")

    panel = pd.DataFrame(rows)
    panel = attach_ghsl_matches(panel, city_spine_path)
    ordered = [
        "period",
        "period_type",
        "year",
        "month",
        "country_name",
        "location_id",
        "location",
        "spatial_grain",
        "bedroom_band",
        "dwelling_type",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "ghsl_match_flag",
        "match_type",
        "manual_review_required",
        "lodged_bonds",
        "active_bonds",
        "closed_bonds",
        "median_weekly_rent_nzd",
        "geometric_mean_weekly_rent_nzd",
        "upper_quartile_weekly_rent_nzd",
        "lower_quartile_weekly_rent_nzd",
        "log_std_dev_weekly_rent",
        "rent_basis",
        "source_dataset",
        "source_url",
    ]
    panel = (
        panel[ordered]
        .sort_values(["period", "location_id", "bedroom_band"])
        .reset_index(drop=True)
    )

    matched = panel["ghsl_match_flag"].fillna(False)
    stats = {
        "panel_rows": int(len(panel)),
        "start_period": str(panel["period"].min()),
        "end_period": str(panel["period"].max()),
        "location_count": int(panel["location"].nunique()),
        "matched_locations": int(panel.loc[matched, "location"].nunique()),
        "matched_observation_rows": int(matched.sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "source_csv_sha256": source_sha,
        "bedroom_dimension": "aggregate_all_bedrooms (monthly TLA file is not split by bedroom count)",
        "rent_basis_note": "Observed bond-lodgement weekly rents listed by tenancy start month.",
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_nz_tenancy_rental_bond.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "nz_tenancy_rental_bond_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="nz_tenancy_services_mbie",
        series_id="nz_tenancy_rental_bond_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="monthly",
        units="weekly rent in NZD and bond counts",
        currency="NZD",
        start_date=stats["start_period"],
        end_date=stats["end_period"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Official Tenancy Services detailed monthly TLA rental-bond CSV parsed into one row per "
                "(territorial authority, month, bedroom_band=ALL). Captures lodged/active/closed bond counts and "
                "median, geometric-mean, and quartile observed bond-lodgement weekly rents. Aggregate ALL/NA roll-up "
                "rows are dropped. Original Location Id and Location labels are preserved; Auckland and other matchable "
                "TLAs are crosswalked to GHSL urban-centre IDs via the city universe spine with ghsl_match_flag retained."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local Tenancy Services TLA CSV, otherwise fetch official CSV.")
    parser.add_argument("--output", default="data/derived/nz_tenancy_rental_bond_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_csv = path_arg(args.input).resolve() if args.input else None
    panel, stats = build_panel(city_spine_path=path_arg(args.city_spine).resolve(), input_csv=input_csv)
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK nz_tenancy_services_mbie:nz_tenancy_rental_bond_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
