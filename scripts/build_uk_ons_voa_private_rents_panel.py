#!/usr/bin/env python3
"""Build England local-authority private-rent panel from ONS/VOA PRMS workbooks."""
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

SOURCE_URL = "https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland"
DOWNLOAD_URL = (
    "https://www.ons.gov.uk/file?uri=%2Fpeoplepopulationandcommunity%2Fhousing%2Fdatasets%2F"
    "privaterentalmarketsummarystatisticsinengland%2Foctober2022toseptember2023%2F"
    "privaterentalmarketstatistics231220.xls"
)
METHODOLOGY_URL = SOURCE_URL
LICENSE = "Open Government Licence v3.0"
SOURCE_DATASET = "ONS/VOA Private Rental Market Summary Statistics in England"

TABLE_BEDROOM_CATEGORIES = {
    "Table2.1": ("room", "Room"),
    "Table2.2": ("studio", "Studio"),
    "Table2.3": ("one_bedroom", "One Bedroom"),
    "Table2.4": ("two_bedrooms", "Two Bedrooms"),
    "Table2.5": ("three_bedrooms", "Three Bedrooms"),
    "Table2.6": ("four_or_more_bedrooms", "Four or more Bedrooms"),
    "Table2.7": ("all_categories", "All categories"),
}

BEDROOM_CATEGORY_CANONICAL = {
    "room": "room",
    "studio": "studio",
    "onebedroom": "one_bedroom",
    "twobedrooms": "two_bedrooms",
    "threebedrooms": "three_bedrooms",
    "fourormorebedrooms": "four_or_more_bedrooms",
    "allcategories": "all_categories",
}

FIELD_ALIASES = {
    "period_start": ["period_start", "start_date", "periodstart", "from"],
    "period_end": ["period_end", "end_date", "periodend", "to"],
    "legacy_la_code": ["la_code", "la_code1", "legacy_la_code", "lad_code_numeric"],
    "local_authority_code": ["area_code", "area_code1", "local_authority_code", "lad_code", "geography_code"],
    "local_authority_name": ["area", "local_authority", "local_authority_name", "geography", "geography_name"],
    "bedroom_category": ["bedroom_category", "bedroom_type", "bedrooms", "category"],
    "bedroom_label": ["bedroom_label", "bedroom_category_label", "bedroom_type_label"],
    "rent_count": ["count_of_rents", "count", "rent_count", "observations", "count of rents"],
    "mean_monthly_rent_gbp": ["mean", "mean_monthly_rent_gbp", "average", "avg"],
    "lower_quartile_monthly_rent_gbp": ["lower_quartile", "lower_quartile_monthly_rent_gbp", "lq"],
    "median_monthly_rent_gbp": ["median", "median_monthly_rent_gbp"],
    "upper_quartile_monthly_rent_gbp": ["upper_quartile", "upper_quartile_monthly_rent_gbp", "uq"],
}

LOCAL_AUTHORITY_CODE_RE = re.compile(r"^E0[6789]\d{6}$")
PERIOD_RE = re.compile(r"between\s+(.+?)\s+to\s+(.+?)\s+by", re.IGNORECASE)
MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
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
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\b(UA|LB|DISTRICT|BOROUGH|COUNTY|MET|COUNCIL)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text == "BRISTOL CITY OF":
        return "BRISTOL"
    return text


def parse_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace("\u00a0", "")
    if text in {".", "..", "-", "nan", "NaN"}:
        return None
    if "," in text and "." in text:
        text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    text = re.sub(r"[^0-9.+-]", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int_string(value: object) -> str | None:
    number = parse_number(value)
    if number is None:
        return None
    return str(int(number))


def parse_date_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip().lower())
    match = re.match(r"(\d{1,2}) ([a-z]+) (\d{4})$", text)
    if not match:
        raise ValueError(f"could not parse PRMS date {value!r}")
    day, month, year = match.groups()
    return f"{year}-{MONTHS[month]}-{int(day):02d}"


def period_from_sheet(sheet: pd.DataFrame) -> tuple[str | None, str | None]:
    for value in sheet.head(6).to_numpy().ravel():
        if pd.isna(value):
            continue
        value = str(value)
        match = PERIOD_RE.search(value)
        if match:
            return parse_date_text(match.group(1)), parse_date_text(match.group(2))
    return None, None


def canonical_column(value: object) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def clean_bedroom_category(value: object) -> str:
    token = normalise_token(value)
    return BEDROOM_CATEGORY_CANONICAL.get(token, token or "all_categories")


def pick_field(columns: list[str], logical_name: str, required: bool = True) -> str | None:
    normalised = {normalise_token(column): column for column in columns}
    for alias in FIELD_ALIASES[logical_name]:
        match = normalised.get(normalise_token(alias))
        if match:
            return match
    if required:
        raise ValueError(f"could not identify field for {logical_name}; columns={columns}")
    return None


def header_row_index(sheet: pd.DataFrame) -> int:
    for idx, row in sheet.iterrows():
        tokens = {normalise_token(value) for value in row.dropna().tolist()}
        if {"areacode1", "area", "median"}.issubset(tokens):
            return int(idx)
    raise ValueError("could not find PRMS table header row")


def rows_from_workbook(path: Path) -> list[dict[str, Any]]:
    workbook = pd.read_excel(path, sheet_name=None, header=None)
    rows: list[dict[str, Any]] = []
    for sheet_name, category in TABLE_BEDROOM_CATEGORIES.items():
        if sheet_name not in workbook:
            continue
        sheet = workbook[sheet_name]
        header_idx = header_row_index(sheet)
        columns = [canonical_column(value) or f"unnamed_{idx}" for idx, value in enumerate(sheet.iloc[header_idx].tolist())]
        table = sheet.iloc[header_idx + 1 :].copy()
        table.columns = columns
        start, end = period_from_sheet(sheet)
        for record in table.to_dict("records"):
            record["period_start"] = start
            record["period_end"] = end
            record["bedroom_category"], record["bedroom_label"] = category
            rows.append(record)
    if not rows:
        raise ValueError(f"no Table2.* administrative-area sheets found in {path}")
    return rows


def load_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"missing ONS/VOA PRMS input: {path}. Download the workbook from {SOURCE_URL} into {rel(path)}."
        )
    suffix = path.suffix.lower()
    if suffix in {".xls", ".xlsx"}:
        return rows_from_workbook(path)
    if suffix == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("records", payload))
        if not isinstance(payload, list):
            raise ValueError(f"expected JSON list in {path}")
        return payload
    if suffix == ".csv":
        return pd.read_csv(path).to_dict("records")
    raise ValueError(f"unsupported input format: {path}")


def build_uk_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    uk = city_spine[city_spine["country_name"].eq("United Kingdom")].copy()
    aliases: dict[str, list[dict[str, Any]]] = {}
    for row in uk.to_dict("records"):
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


def canonical_match_name(area_code: object, area_name: object) -> str:
    code = "" if pd.isna(area_code) else str(area_code).strip()
    if code.startswith("E09"):
        return "LONDON"
    return normalise_name(area_name)


def attach_city_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    alias_map = build_uk_alias_map(spine)
    rows = []
    for row in panel[["local_authority_code", "local_authority_name_norm"]].drop_duplicates().to_dict("records"):
        canonical = "LONDON" if str(row["local_authority_code"]).startswith("E09") else row["local_authority_name_norm"]
        match = alias_map.get(canonical)
        if match:
            match_type = "london_borough_to_ghsl" if str(row["local_authority_code"]).startswith("E09") else match["match_type"]
            rows.append({"local_authority_code": row["local_authority_code"], **match, "match_type": match_type})
        else:
            rows.append(
                {
                    "local_authority_code": row["local_authority_code"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="local_authority_code", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    input_path: Path | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if rows is None:
        if input_path is None:
            raise ValueError("input_path is required when rows are not supplied")
        rows = load_input(input_path)
    if not rows:
        raise ValueError("ONS/VOA PRMS input returned no rows")
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    fields = {
        "period_start": pick_field(columns, "period_start", required=False),
        "period_end": pick_field(columns, "period_end", required=False),
        "legacy_la_code": pick_field(columns, "legacy_la_code", required=False),
        "local_authority_code": pick_field(columns, "local_authority_code"),
        "local_authority_name": pick_field(columns, "local_authority_name"),
        "bedroom_category": pick_field(columns, "bedroom_category", required=False),
        "bedroom_label": pick_field(columns, "bedroom_label", required=False),
        "rent_count": pick_field(columns, "rent_count"),
        "mean_monthly_rent_gbp": pick_field(columns, "mean_monthly_rent_gbp"),
        "lower_quartile_monthly_rent_gbp": pick_field(columns, "lower_quartile_monthly_rent_gbp"),
        "median_monthly_rent_gbp": pick_field(columns, "median_monthly_rent_gbp"),
        "upper_quartile_monthly_rent_gbp": pick_field(columns, "upper_quartile_monthly_rent_gbp"),
    }
    period_start = frame[fields["period_start"]].astype(str).str.strip() if fields["period_start"] else pd.NA
    period_end = frame[fields["period_end"]].astype(str).str.strip() if fields["period_end"] else pd.NA
    bedroom_category = (
        frame[fields["bedroom_category"]].map(clean_bedroom_category)
        if fields["bedroom_category"]
        else pd.Series("all_categories", index=frame.index)
    )
    bedroom_label = (
        frame[fields["bedroom_label"]].astype(str).str.strip()
        if fields["bedroom_label"]
        else bedroom_category.map(lambda value: value.replace("_", " ").title())
    )
    panel = pd.DataFrame(
        {
            "period_start": period_start,
            "period_end": period_end,
            "period_end_year": pd.to_datetime(period_end, errors="coerce").dt.year,
            "country_name": "United Kingdom",
            "country_iso3": "GBR",
            "local_authority_code": frame[fields["local_authority_code"]].astype(str).str.strip(),
            "legacy_la_code": frame[fields["legacy_la_code"]].map(parse_int_string) if fields["legacy_la_code"] else pd.NA,
            "local_authority_name": frame[fields["local_authority_name"]].astype(str).str.strip(),
            "bedroom_category": bedroom_category,
            "bedroom_label": bedroom_label,
            "rent_count": frame[fields["rent_count"]].map(parse_number),
            "mean_monthly_rent_gbp": frame[fields["mean_monthly_rent_gbp"]].map(parse_number),
            "lower_quartile_monthly_rent_gbp": frame[fields["lower_quartile_monthly_rent_gbp"]].map(parse_number),
            "median_monthly_rent_gbp": frame[fields["median_monthly_rent_gbp"]].map(parse_number),
            "upper_quartile_monthly_rent_gbp": frame[fields["upper_quartile_monthly_rent_gbp"]].map(parse_number),
        }
    )
    panel = panel[panel["local_authority_code"].map(lambda value: bool(LOCAL_AUTHORITY_CODE_RE.match(str(value))))].copy()
    panel = panel.dropna(subset=["period_end_year", "local_authority_name", "median_monthly_rent_gbp"]).copy()
    if panel.empty:
        raise ValueError("ONS/VOA PRMS rows had no usable local-authority median-rent observations")
    panel["period_end_year"] = panel["period_end_year"].astype(int)
    panel["rent_count"] = panel["rent_count"].fillna(0).astype(int)
    panel["local_authority_name_norm"] = panel["local_authority_name"].map(normalise_name)
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = SOURCE_URL
    panel["source_download_url"] = DOWNLOAD_URL
    panel["ons_comparability_note"] = (
        "PRMS rents are based on observed advertised/letting evidence collected for valuation purposes; "
        "ONS warns against treating year-to-year movements as a pure price index."
    )

    panel = attach_city_matches(panel, city_spine_path)
    ordered = [
        "period_start",
        "period_end",
        "period_end_year",
        "country_name",
        "country_iso3",
        "local_authority_code",
        "legacy_la_code",
        "local_authority_name",
        "local_authority_name_norm",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "bedroom_category",
        "bedroom_label",
        "rent_count",
        "mean_monthly_rent_gbp",
        "lower_quartile_monthly_rent_gbp",
        "median_monthly_rent_gbp",
        "upper_quartile_monthly_rent_gbp",
        "source_dataset",
        "source_url",
        "source_download_url",
        "ons_comparability_note",
    ]
    panel = panel[ordered].sort_values(["period_end_year", "local_authority_code", "bedroom_category"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_period_end_year": int(panel["period_end_year"].min()),
        "end_period_end_year": int(panel["period_end_year"].max()),
        "local_authority_count": int(panel["local_authority_code"].nunique()),
        "matched_local_authorities": int(panel[["local_authority_code", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "bedroom_categories": sorted(panel["bedroom_category"].dropna().unique().tolist()),
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
    path = manifest_dir / f"fetch_run_{run_stamp}_uk_ons_voa_private_rents.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "uk_ons_voa_private_rents_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="uk_ons_voa",
        series_id="uk_ons_voa_private_rents_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="monthly private rent, GBP",
        currency="GBP",
        start_date=str(stats["start_period_end_year"]),
        end_date=str(stats["end_period_end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "ONS/VOA PRMS Table2 administrative-area rows normalized to local-authority/period/"
                "bedroom-category observations and matched to the UK subset of the GHSL top-1000 city spine."
            ),
            "caveat": "PRMS is a rent distribution snapshot, not a repeat-sales or hedonic rent index.",
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", default="data/raw/city_level/privaterentalmarketstatistics231220.xls")
    parser.add_argument("--output", default="data/derived/uk_ons_voa_private_rents_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        input_path=path_arg(args.input).resolve(),
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK uk_ons_voa:uk_ons_voa_private_rents_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
