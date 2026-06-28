#!/usr/bin/env python3
"""Build a U.S. city-month rent panel from Zillow's city-level ZORI CSV."""
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

SOURCE_URL = "https://files.zillowstatic.com/research/public_csvs/zori/City_zori_uc_sfrcondomfr_sm_month.csv"
METHODOLOGY_URL = "https://www.zillow.com/research/zhvi-methodology-2019-highlights-26221/"
LICENSE = "Zillow Research data terms; verify before redistribution"
SOURCE_DATASET = "Zillow Observed Rent Index, city, all homes plus multifamily smoothed monthly"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PILOT_ALIAS_OVERRIDES = {
    ("NEW YORK", "NY"): "NEW YORK",
    ("SAINT PAUL", "MN"): "SAINT PAUL",
    ("MINNEAPOLIS", "MN"): "MINNEAPOLIS",
    ("SAN FRANCISCO", "CA"): "SAN FRANCISCO",
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
    for alias in list(aliases):
        if alias.endswith(" CITY"):
            aliases.add(alias[: -len(" CITY")].strip())
    return {alias for alias in aliases if alias}


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
        unique_ids = {record["ieset_city_id"] for record in records}
        if len(unique_ids) == 1:
            out[alias] = records[0]
    return out


def build_panel(input_path: Path, city_spine_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"missing Zillow input: {input_path}. Download {SOURCE_URL} into {rel(input_path)}."
        )
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")

    raw = pd.read_csv(input_path)
    city_spine = pd.read_csv(city_spine_path)
    date_cols = [column for column in raw.columns if DATE_RE.match(str(column))]
    if not date_cols:
        raise ValueError("Zillow CSV has no monthly date columns")

    raw["zillow_name_norm"] = raw["RegionName"].map(normalise_name)
    zillow_name_counts = raw.groupby("zillow_name_norm")["State"].nunique(dropna=True).to_dict()
    spine_aliases = build_spine_alias_map(city_spine)

    match_rows = []
    for row in raw[["RegionID", "RegionName", "State", "zillow_name_norm"]].to_dict("records"):
        alias = PILOT_ALIAS_OVERRIDES.get((row["zillow_name_norm"], row["State"]), row["zillow_name_norm"])
        match = spine_aliases.get(alias)
        ambiguous_zillow_name = zillow_name_counts.get(row["zillow_name_norm"], 0) > 1
        if match and (not ambiguous_zillow_name or (row["zillow_name_norm"], row["State"]) in PILOT_ALIAS_OVERRIDES):
            match_rows.append(
                {
                    "RegionID": row["RegionID"],
                    **match,
                    "zillow_match_name": alias,
                    "zillow_name_ambiguous": bool(ambiguous_zillow_name),
                }
            )
        else:
            match_rows.append(
                {
                    "RegionID": row["RegionID"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                    "zillow_match_name": alias,
                    "zillow_name_ambiguous": bool(ambiguous_zillow_name),
                }
            )
    matches = pd.DataFrame(match_rows)

    panel = raw.merge(matches, on="RegionID", how="left")
    id_vars = [column for column in panel.columns if column not in date_cols]
    panel = panel.melt(
        id_vars=id_vars,
        value_vars=date_cols,
        var_name="month_end",
        value_name="zori_usd",
    )
    panel["month_end"] = pd.to_datetime(panel["month_end"]).dt.date.astype(str)
    panel["year"] = panel["month_end"].str.slice(0, 4).astype(int)
    panel["month"] = panel["month_end"].str.slice(5, 7).astype(int)
    panel["zori_usd"] = pd.to_numeric(panel["zori_usd"], errors="coerce")
    panel = panel.dropna(subset=["zori_usd"]).reset_index(drop=True)
    panel = panel.rename(
        columns={
            "RegionID": "zillow_region_id",
            "SizeRank": "zillow_size_rank",
            "RegionName": "zillow_region_name",
            "RegionType": "zillow_region_type",
            "StateName": "state_name",
            "State": "state",
            "Metro": "metro",
            "CountyName": "county_name",
            "zillow_name_norm": "zillow_region_name_norm",
        }
    )
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = SOURCE_URL
    panel = panel.sort_values(["zillow_size_rank", "zillow_region_id", "month_end"]).reset_index(drop=True)

    stats = {
        "raw_region_rows": int(len(raw)),
        "date_columns": int(len(date_cols)),
        "long_non_null_rows": int(len(panel)),
        "start_month": min(date_cols),
        "end_month": max(date_cols),
        "matched_regions": int(panel[["zillow_region_id", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].dropna().nunique()),
        "ambiguous_name_regions": int(matches["zillow_name_ambiguous"].sum()),
        "source_csv_sha256": sha256_path(input_path),
    }
    return panel, stats


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_zillow_city_rent.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "us_zillow_city_rent_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def emit(panel: pd.DataFrame, stats: dict[str, Any], input_path: Path, output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="zillow",
        series_id="us_city_rent_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="monthly",
        units="U.S. dollars, observed rent index",
        currency="USD",
        start_date=stats["start_month"],
        end_date=stats["end_month"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "input_file": rel(input_path),
            "input_sha256": stats["source_csv_sha256"],
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "crosswalk_rule": (
                "Attach IESET city ids only for unambiguous normalized Zillow city names "
                "or explicit pilot aliases; leave duplicate-name cities for manual review."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/city_level/City_zori_uc_sfrcondomfr_sm_month.csv")
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.csv")
    parser.add_argument("--output", default="data/derived/us_city_rent_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    input_path = path_arg(args.input).resolve()
    output_path = path_arg(args.output).resolve()
    panel, stats = build_panel(input_path, path_arg(args.city_spine).resolve())
    result = emit(panel, stats, input_path, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK zillow:us_city_rent_panel "
        f"rows={result.rows} matched_regions={stats['matched_regions']} "
        f"ieset_cities={stats['unique_ieset_city_ids']} period={result.start_date}->{result.end_date}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
