#!/usr/bin/env python3
"""Build Singapore HDB approval and URA private-rental panel from data.gov.sg."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
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

METHODOLOGY_URL = "https://guide.data.gov.sg/developer-guide/dataset-apis/download-dataset"
LICENSE = "Singapore Open Data Licence; attribution required, no endorsement"
SINGAPORE_IESET_CITY_ID = "ghsl_ucdb_r2024a:178"

DATASETS = {
    "hdb_approval": {
        "dataset_id": "d_c9f57187485a850908655db0e8cfe651",
        "source_dataset": "Renting Out of Flats from Jan 2021",
        "source_url": "https://data.gov.sg/datasets/d_c9f57187485a850908655db0e8cfe651/view",
        "market_segment": "hdb_public_rental_approval",
    },
    "ura_private_non_landed": {
        "dataset_id": "d_149ac00a2734bb0a03867bbe2ec0e7b0",
        "source_dataset": "Rentals of Non-Landed Residential Buildings, Quarterly",
        "source_url": "https://data.gov.sg/datasets/d_149ac00a2734bb0a03867bbe2ec0e7b0/view",
        "market_segment": "ura_private_non_landed",
    },
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
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace("\u00a0", "")
    if text.lower() in {"", "na", "nan", "-", "."}:
        return None
    text = re.sub(r"[^0-9.+-]", "", text.replace(",", ""))
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    number = parse_number(value)
    return None if number is None else int(number)


def parse_month(value: object) -> tuple[str, int, int, str, str]:
    text = str(value).strip()
    match = re.match(r"^(\d{4})-(\d{1,2})$", text)
    if not match:
        raise ValueError(f"could not parse Singapore HDB approval month {value!r}")
    year = int(match.group(1))
    month = int(match.group(2))
    period = pd.Period(f"{year}-{month:02d}", freq="M")
    return f"{year}-{month:02d}", year, month, str(period.start_time.date()), str(period.end_time.date())


def parse_quarter(value: object) -> tuple[str, int, int, str, str]:
    text = str(value).strip().upper()
    match = re.match(r"^(\d{4})[-\s]?Q([1-4])$", text)
    if not match:
        raise ValueError(f"could not parse Singapore URA quarter {value!r}")
    year = int(match.group(1))
    quarter = int(match.group(2))
    period = pd.Period(f"{year}Q{quarter}", freq="Q-DEC")
    return f"{year}-Q{quarter}", year, quarter, str(period.start_time.date()), str(period.end_time.date())


def pick_column(columns: list[str], aliases: list[str]) -> str:
    normalised = {normalise_name(column): column for column in columns}
    for alias in aliases:
        match = normalised.get(normalise_name(alias))
        if match:
            return match
    raise ValueError(f"could not identify one of {aliases}; columns={columns}")


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def dataset_metadata(dataset_id: str) -> dict[str, Any]:
    url = f"https://api-production.data.gov.sg/v2/public/api/datasets/{dataset_id}/metadata"
    payload = fetch_json(url)
    if payload.get("code") != 0:
        raise RuntimeError(f"data.gov.sg metadata failed for {dataset_id}: {payload}")
    return payload["data"]


def dataset_rows(dataset_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = dataset_metadata(dataset_id)
    url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/initiate-download"
    payload = fetch_json(url)
    if payload.get("code") != 0 or not payload.get("data", {}).get("url"):
        raise RuntimeError(f"data.gov.sg download initiation failed for {dataset_id}: {payload}")
    req = urllib.request.Request(payload["data"]["url"], headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        rows = pd.read_csv(response).to_dict("records")
    return rows, metadata


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"missing Singapore rental input: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("records", payload))
        if not isinstance(payload, list):
            raise ValueError(f"expected JSON list in {path}")
        return payload
    if suffix == ".csv":
        return pd.read_csv(path).to_dict("records")
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path).to_dict("records")
    raise ValueError(f"unsupported input format: {path}")


def singapore_spine_records(city_spine_path: Path) -> dict[str, dict[str, Any]]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_parquet(city_spine_path) if city_spine_path.suffix.lower() == ".parquet" else pd.read_csv(city_spine_path)
    singapore = spine[spine["country_name"].eq("Singapore")].copy()
    records: dict[str, dict[str, Any]] = {}
    for row in singapore.to_dict("records"):
        records[normalise_name(row["city_name"])] = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": int(row["city_rank_2025"]),
        }
    singapore_record = records.get("SINGAPORE")
    if not singapore_record:
        match = spine[spine["ieset_city_id"].eq(SINGAPORE_IESET_CITY_ID)]
        if match.empty:
            raise ValueError("could not find Singapore in city spine")
        row = match.iloc[0].to_dict()
        singapore_record = {
            "ieset_city_id": row["ieset_city_id"],
            "ghsl_city_name": row["city_name"],
            "ghsl_city_rank_2025": int(row["city_rank_2025"]),
        }
        records["SINGAPORE"] = singapore_record
    return records


def match_singapore_town(town_norm: str, records: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], str]:
    if town_norm in records and town_norm != "SINGAPORE":
        return records[town_norm], "hdb_town_name_to_ghsl_city"
    return records["SINGAPORE"], "city_state_assignment"


def base_columns(row_count: int, city: dict[str, Any], match_type: str) -> dict[str, Any]:
    return {
        "country_name": "Singapore",
        "country_iso3": "SGP",
        "ieset_city_id": city["ieset_city_id"],
        "ghsl_city_name": city["ghsl_city_name"],
        "ghsl_city_rank_2025": city["ghsl_city_rank_2025"],
        "match_type": match_type,
        "manual_review_required": False,
    }


def build_hdb_panel(rows: list[dict[str, Any]], records: dict[str, dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    month_col = pick_column(columns, ["rent_approval_date"])
    town_col = pick_column(columns, ["town"])
    block_col = pick_column(columns, ["block"])
    street_col = pick_column(columns, ["street_name", "street name"])
    flat_type_col = pick_column(columns, ["flat_type", "flat type"])
    rent_col = pick_column(columns, ["monthly_rent", "monthly rent"])

    parsed = pd.DataFrame(
        frame[month_col].map(parse_month).tolist(),
        columns=["period", "year", "month", "period_start", "period_end"],
    )
    panel = pd.DataFrame(
        {
            "period": parsed["period"],
            "period_type": "month",
            "year": parsed["year"],
            "quarter": pd.PeriodIndex(parsed["period"], freq="M").asfreq("Q").astype(str).str.replace("Q", "-Q", regex=False),
            "month": parsed["month"],
            "quarter_number": pd.NA,
            "period_start": parsed["period_start"],
            "period_end": parsed["period_end"],
            "source_dataset_key": "hdb_approval",
            "source_dataset_id": DATASETS["hdb_approval"]["dataset_id"],
            "source_dataset": DATASETS["hdb_approval"]["source_dataset"],
            "source_url": DATASETS["hdb_approval"]["source_url"],
            "market_segment": DATASETS["hdb_approval"]["market_segment"],
            "town": frame[town_col].astype(str).str.strip(),
            "town_norm": frame[town_col].map(normalise_name),
            "block": frame[block_col].astype(str).str.strip(),
            "street_name": frame[street_col].astype(str).str.strip(),
            "flat_type": frame[flat_type_col].astype(str).str.strip(),
            "project_name": pd.NA,
            "project_name_norm": pd.NA,
            "postal_district": pd.NA,
            "monthly_rent_sgd": frame[rent_col].map(parse_number),
            "rent_p25_sgd_psf": pd.NA,
            "rent_median_sgd_psf": pd.NA,
            "rent_p75_sgd_psf": pd.NA,
            "rental_contracts": pd.NA,
            "observation_count": 1,
        }
    )
    matches = [match_singapore_town(town_norm, records) for town_norm in panel["town_norm"]]
    panel = pd.concat(
        [
            panel.reset_index(drop=True),
            pd.DataFrame([{**city, "match_type": match_type, "manual_review_required": False} for city, match_type in matches]),
        ],
        axis=1,
    )
    panel["country_name"] = "Singapore"
    panel["country_iso3"] = "SGP"
    panel = panel.dropna(subset=["monthly_rent_sgd"]).copy()
    return panel


def build_ura_panel(rows: list[dict[str, Any]], records: dict[str, dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    quarter_col = pick_column(columns, ["qtr", "quarter"])
    project_col = pick_column(columns, ["project_name", "project name"])
    district_col = pick_column(columns, ["postal_district", "postal district"])
    p25_col = pick_column(columns, ["25th_percentile", "25th percentile"])
    median_col = pick_column(columns, ["median"])
    p75_col = pick_column(columns, ["75th_percentile", "75th percentile"])
    contracts_col = pick_column(columns, ["rental_contracts", "rental contracts"])

    parsed = pd.DataFrame(
        frame[quarter_col].map(parse_quarter).tolist(),
        columns=["period", "year", "quarter_number", "period_start", "period_end"],
    )
    city = records["SINGAPORE"]
    panel = pd.DataFrame(
        {
            "period": parsed["period"],
            "period_type": "quarter",
            "year": parsed["year"],
            "quarter": parsed["period"],
            "month": pd.NA,
            "quarter_number": parsed["quarter_number"],
            "period_start": parsed["period_start"],
            "period_end": parsed["period_end"],
            "source_dataset_key": "ura_private_non_landed",
            "source_dataset_id": DATASETS["ura_private_non_landed"]["dataset_id"],
            "source_dataset": DATASETS["ura_private_non_landed"]["source_dataset"],
            "source_url": DATASETS["ura_private_non_landed"]["source_url"],
            "market_segment": DATASETS["ura_private_non_landed"]["market_segment"],
            "town": pd.NA,
            "town_norm": pd.NA,
            "block": pd.NA,
            "street_name": pd.NA,
            "flat_type": pd.NA,
            "project_name": frame[project_col].astype(str).str.strip(),
            "project_name_norm": frame[project_col].map(normalise_name),
            "postal_district": frame[district_col].map(parse_int),
            "monthly_rent_sgd": pd.NA,
            "rent_p25_sgd_psf": frame[p25_col].map(parse_number),
            "rent_median_sgd_psf": frame[median_col].map(parse_number),
            "rent_p75_sgd_psf": frame[p75_col].map(parse_number),
            "rental_contracts": frame[contracts_col].map(parse_int),
            "observation_count": frame[contracts_col].map(parse_int),
            **base_columns(len(frame), city, "city_state_assignment"),
        }
    )
    panel = panel.dropna(subset=["rent_median_sgd_psf"]).copy()
    return panel


def build_panel(
    *,
    city_spine_path: Path,
    hdb_rows: list[dict[str, Any]] | None = None,
    ura_rows: list[dict[str, Any]] | None = None,
    hdb_input_path: Path | None = None,
    ura_input_path: Path | None = None,
    hdb_metadata: dict[str, Any] | None = None,
    ura_metadata: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if hdb_rows is None:
        if hdb_input_path is None:
            hdb_rows, hdb_metadata = dataset_rows(DATASETS["hdb_approval"]["dataset_id"])
        else:
            hdb_rows = load_rows(hdb_input_path)
    if ura_rows is None:
        if ura_input_path is None:
            ura_rows, ura_metadata = dataset_rows(DATASETS["ura_private_non_landed"]["dataset_id"])
        else:
            ura_rows = load_rows(ura_input_path)
    if not hdb_rows and not ura_rows:
        raise ValueError("Singapore HDB/URA inputs returned no rows")

    records = singapore_spine_records(city_spine_path)
    hdb_panel = build_hdb_panel(hdb_rows, records)
    ura_panel = build_ura_panel(ura_rows, records)
    panels = [frame.astype(object) for frame in [hdb_panel, ura_panel] if not frame.empty]
    panel = pd.concat(panels, ignore_index=True)
    if panel.empty:
        raise ValueError("Singapore HDB/URA rows had no usable rental observations")

    panel["singapore_scope_note"] = (
        "HDB rows are owner-declared public-housing rental approvals; URA rows are private non-landed "
        "project-quarter rent distributions, with rent percentiles reported in SGD per square foot per month."
    )
    ordered = [
        "period",
        "period_type",
        "year",
        "quarter",
        "month",
        "quarter_number",
        "period_start",
        "period_end",
        "country_name",
        "country_iso3",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "source_dataset_key",
        "source_dataset_id",
        "source_dataset",
        "source_url",
        "market_segment",
        "town",
        "town_norm",
        "block",
        "street_name",
        "flat_type",
        "project_name",
        "project_name_norm",
        "postal_district",
        "monthly_rent_sgd",
        "rent_p25_sgd_psf",
        "rent_median_sgd_psf",
        "rent_p75_sgd_psf",
        "rental_contracts",
        "observation_count",
        "singapore_scope_note",
    ]
    panel = panel[ordered].sort_values(["period", "source_dataset_key", "ieset_city_id", "town", "project_name"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_period": str(panel["period"].min()),
        "end_period": str(panel["period"].max()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique()),
        "hdb_approval_rows": int(panel["source_dataset_key"].eq("hdb_approval").sum()),
        "hdb_town_count": int(panel.loc[panel["source_dataset_key"].eq("hdb_approval"), "town_norm"].nunique()),
        "ura_private_non_landed_rows": int(panel["source_dataset_key"].eq("ura_private_non_landed").sum()),
        "ura_project_count": int(panel.loc[panel["source_dataset_key"].eq("ura_private_non_landed"), "project_name_norm"].nunique()),
        "ura_postal_district_count": int(panel.loc[panel["source_dataset_key"].eq("ura_private_non_landed"), "postal_district"].nunique()),
        "source_metadata": {
            "hdb_approval": {
                "dataset_id": DATASETS["hdb_approval"]["dataset_id"],
                "last_updated_at": hdb_metadata.get("lastUpdatedAt") if hdb_metadata else None,
                "coverage_start": hdb_metadata.get("coverageStart") if hdb_metadata else None,
                "coverage_end": hdb_metadata.get("coverageEnd") if hdb_metadata else None,
                "managed_by": hdb_metadata.get("managedBy") if hdb_metadata else None,
            },
            "ura_private_non_landed": {
                "dataset_id": DATASETS["ura_private_non_landed"]["dataset_id"],
                "last_updated_at": ura_metadata.get("lastUpdatedAt") if ura_metadata else None,
                "coverage_start": ura_metadata.get("coverageStart") if ura_metadata else None,
                "coverage_end": ura_metadata.get("coverageEnd") if ura_metadata else None,
                "managed_by": ura_metadata.get("managedBy") if ura_metadata else None,
            },
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
    path = manifest_dir / f"fetch_run_{run_stamp}_singapore_hdb_ura_rentals.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "singapore_hdb_ura_rental_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="data_gov_sg_hdb_ura",
        series_id="singapore_hdb_ura_rental_panel",
        source_url="; ".join(dataset["source_url"] for dataset in DATASETS.values()),
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="monthly and quarterly",
        units="HDB monthly rent SGD; URA private non-landed rent SGD per square foot per month",
        currency="SGD",
        start_date=stats["start_period"],
        end_date=stats["end_period"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Downloaded official data.gov.sg HDB rental-approval and URA non-landed residential rental CSVs, "
                "normalized monthly HDB approval rents and quarterly URA project rent percentiles into one panel, "
                "and matched observations to GHSL Singapore city records where subcity names are available."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--hdb-input", help="Optional local HDB approval CSV/XLSX/JSON. If omitted, fetches from data.gov.sg.")
    parser.add_argument("--ura-input", help="Optional local URA rental CSV/XLSX/JSON. If omitted, fetches from data.gov.sg.")
    parser.add_argument("--output", default="data/derived/singapore_hdb_ura_rental_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        hdb_input_path=path_arg(args.hdb_input).resolve() if args.hdb_input else None,
        ura_input_path=path_arg(args.ura_input).resolve() if args.ura_input else None,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK data_gov_sg_hdb_ura:singapore_hdb_ura_rental_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} "
        f"hdb_rows={stats['hdb_approval_rows']} ura_rows={stats['ura_private_non_landed_rows']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
