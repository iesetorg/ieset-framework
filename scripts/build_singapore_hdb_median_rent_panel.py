#!/usr/bin/env python3
"""Build Singapore HDB town/flat-type median rent panel from data.gov.sg."""
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

DATASET_ID = "d_23000a00c52996c55106084ed0339566"
SOURCE_URL = f"https://data.gov.sg/datasets/{DATASET_ID}/view"
METADATA_URL = f"https://api-production.data.gov.sg/v2/public/api/datasets/{DATASET_ID}/metadata"
INITIATE_DOWNLOAD_URL = f"https://api-open.data.gov.sg/v1/public/api/datasets/{DATASET_ID}/initiate-download"
METHODOLOGY_URL = "https://guide.data.gov.sg/developer-guide/dataset-apis/download-dataset"
LICENSE = "Singapore Open Data Licence; attribution required, no endorsement"
SOURCE_DATASET = "HDB Median Rent By Town And Flat Type"
SINGAPORE_IESET_CITY_ID = "ghsl_ucdb_r2024a:178"


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


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def fetch_metadata() -> dict[str, Any]:
    payload = fetch_json(METADATA_URL)
    if payload.get("code") != 0:
        raise RuntimeError(f"data.gov.sg metadata failed: {payload}")
    return payload["data"]


def fetch_live_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = fetch_metadata()
    payload = fetch_json(INITIATE_DOWNLOAD_URL)
    if payload.get("code") != 0 or not payload.get("data", {}).get("url"):
        raise RuntimeError(f"data.gov.sg download initiation failed: {payload}")
    download_url = payload["data"]["url"]
    req = urllib.request.Request(download_url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
        rows = pd.read_csv(response).to_dict("records")
    return rows, metadata


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"missing Singapore HDB input: {path}")
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


def parse_quarter(value: object) -> tuple[str, int, int, str, str]:
    text = str(value).strip().upper()
    match = re.match(r"^(\d{4})[-\s]?Q([1-4])$", text)
    if not match:
        raise ValueError(f"could not parse Singapore HDB quarter {value!r}")
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


def singapore_city_record(city_spine_path: Path) -> dict[str, Any]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_parquet(city_spine_path) if city_spine_path.suffix.lower() == ".parquet" else pd.read_csv(city_spine_path)
    match = spine[spine["ieset_city_id"].eq(SINGAPORE_IESET_CITY_ID)]
    if match.empty:
        match = spine[(spine["country_name"].eq("Singapore")) & (spine["city_name"].eq("Singapore"))]
    if match.empty:
        raise ValueError("could not find Singapore in city spine")
    row = match.iloc[0].to_dict()
    return {
        "ieset_city_id": row["ieset_city_id"],
        "ghsl_city_name": row["city_name"],
        "ghsl_city_rank_2025": int(row["city_rank_2025"]),
    }


def build_panel(
    *,
    city_spine_path: Path,
    rows: list[dict[str, Any]] | None = None,
    input_path: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if rows is None:
        if input_path is None:
            rows, metadata = fetch_live_rows()
        else:
            rows = load_rows(input_path)
    if not rows:
        raise ValueError("Singapore HDB median-rent input returned no rows")

    city = singapore_city_record(city_spine_path)
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    quarter_col = pick_column(columns, ["quarter"])
    town_col = pick_column(columns, ["town"])
    flat_type_col = pick_column(columns, ["flat_type", "flat type"])
    rent_col = pick_column(columns, ["median_rent", "median rent"])

    quarter_parts = frame[quarter_col].map(parse_quarter)
    parsed = pd.DataFrame(
        quarter_parts.tolist(),
        columns=["quarter", "year", "quarter_number", "quarter_start", "quarter_end"],
    )
    panel = pd.DataFrame(
        {
            "quarter": parsed["quarter"],
            "year": parsed["year"],
            "quarter_number": parsed["quarter_number"],
            "quarter_start": parsed["quarter_start"],
            "quarter_end": parsed["quarter_end"],
            "country_name": "Singapore",
            "country_iso3": "SGP",
            "town": frame[town_col].astype(str).str.strip(),
            "town_norm": frame[town_col].map(normalise_name),
            "flat_type": frame[flat_type_col].astype(str).str.strip(),
            "median_monthly_rent_sgd": frame[rent_col].map(parse_number),
            "median_rent_reported": frame[rent_col].astype(str).str.strip(),
            **city,
            "match_type": "city_state_assignment",
            "manual_review_required": False,
            "source_dataset_id": DATASET_ID,
            "source_dataset": SOURCE_DATASET,
            "source_url": SOURCE_URL,
        }
    )
    panel = panel.dropna(subset=["median_monthly_rent_sgd"]).copy()
    if panel.empty:
        raise ValueError("Singapore HDB rows had no numeric median rent observations")
    panel["median_monthly_rent_sgd"] = panel["median_monthly_rent_sgd"].astype(float)
    panel["hdb_scope_note"] = (
        "Median rents by HDB town and flat type; source is public-housing subletting rents, "
        "not the full private rental market."
    )
    ordered = [
        "quarter",
        "year",
        "quarter_number",
        "quarter_start",
        "quarter_end",
        "country_name",
        "country_iso3",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "town",
        "town_norm",
        "flat_type",
        "median_monthly_rent_sgd",
        "median_rent_reported",
        "source_dataset_id",
        "source_dataset",
        "source_url",
        "hdb_scope_note",
    ]
    panel = panel[ordered].sort_values(["quarter", "town", "flat_type"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_quarter": str(panel["quarter"].min()),
        "end_quarter": str(panel["quarter"].max()),
        "town_count": int(panel["town_norm"].nunique()),
        "flat_type_count": int(panel["flat_type"].nunique()),
        "matched_city_id": city["ieset_city_id"],
        "source_metadata": {
            "dataset_id": DATASET_ID,
            "last_updated_at": metadata.get("lastUpdatedAt") if metadata else None,
            "coverage_start": metadata.get("coverageStart") if metadata else None,
            "coverage_end": metadata.get("coverageEnd") if metadata else None,
            "managed_by": metadata.get("managedBy") if metadata else None,
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
    path = manifest_dir / f"fetch_run_{run_stamp}_singapore_hdb_median_rent.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "singapore_hdb_median_rent_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="data_gov_sg_hdb",
        series_id="singapore_hdb_median_rent_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="quarterly",
        units="median monthly rent by HDB town and flat type",
        currency="SGD",
        start_date=stats["start_quarter"],
        end_date=stats["end_quarter"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Downloaded the official data.gov.sg HDB Median Rent By Town And Flat Type CSV, "
                "dropped suppressed/non-numeric rent cells, retained town and flat-type categories, "
                "and assigned observations to the GHSL Singapore city-state record."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local CSV/XLSX/JSON export. If omitted, fetches from data.gov.sg.")
    parser.add_argument("--output", default="data/derived/singapore_hdb_median_rent_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        input_path=path_arg(args.input).resolve() if args.input else None,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK data_gov_sg_hdb:singapore_hdb_median_rent_panel "
        f"rows={result.rows} quarters={result.start_date}->{result.end_date} towns={stats['town_count']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
