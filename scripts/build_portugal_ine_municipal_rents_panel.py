#!/usr/bin/env python3
"""Build the Portugal INE municipal new-lease median rent panel.

Pulls JSON from Statistics Portugal (INE)'s key-free open indicator API
(``https://www.ine.pt/ine/json_indicador/pindica.jsp``) for indicator
``0010732`` -- "Median house rental value of new lease agreements of household
dwellings (2021 Methodology)" -- reported in EUR per square metre at the
município grain, quarterly. The panel is long-format with one row per
``(municipality_code, period)``. INE município codes (DICO-derived) and names
are preserved, and each municipality is crosswalked (by normalised name +
country) to the IESET / GHSL top-1000 city universe with a ``ghsl_match_flag``;
unmatched municipalities are retained and flagged ``False``.

These are observed new-lease median rents (not a hedonic or repeat-contract
index). The national "Total" aggregate row is excluded from the municipal grain.
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

VARCD = "0010732"
DATA_API = "https://www.ine.pt/ine/json_indicador/pindica.jsp"
META_API = "https://www.ine.pt/ine/json_indicador/pindicaMeta.jsp"
INDICATOR_PAGE = (
    "https://www.ine.pt/xportal/xmain?xpid=INE&xpgid=ine_indicadores"
    f"&indOcorrCod={VARCD}&contexto=bd&selTab=tab2"
)
METHODOLOGY_URL = (
    "https://www.ine.pt/xportal/xmain?xpid=INE&xpgid=ine_destaques"
    "&DESTAQUESmodo=2"
)
LICENSE = "INE Portugal open data terms (attribution required)"
PUBLISHER = "portugal_ine"
SERIES_ID = "portugal_ine_municipal_rents_panel"
USER_AGENT = "IESET city-level data builder"

# INE quarterly period category codes (Dim1) for varcd 0010732, confirmed from
# the indicator metadata endpoint: 1st Quarter 2020 .. 4th Quarter 2023.
PERIOD_CODES = [
    "S5A20201", "S5A20202", "S5A20203", "S5A20204",
    "S5A20211", "S5A20212", "S5A20213", "S5A20214",
    "S5A20221", "S5A20222", "S5A20223", "S5A20224",
    "S5A20231", "S5A20232", "S5A20233", "S5A20234",
]

# Non-municipal aggregate geo codes returned by INE that must be excluded from
# the municipal grain.
AGGREGATE_GEOCODES = {"T"}

COUNTRY_NAME = "Portugal"
COUNTRY_ISO3 = "PRT"

# INE labels Lisbon as "Lisboa" and Porto as "Porto"; the GHSL spine uses the
# English "Lisbon" / "Porto". Map INE labels to GHSL spine display names.
INE_TO_GHSL_NAME = {
    "LISBOA": "Lisbon",
    "PORTO": "Porto",
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


def period_label_to_quarter(label: str) -> tuple[int, int]:
    """Map an INE English period label to (year, quarter)."""
    m = re.search(r"(\d)(?:st|nd|rd|th)\s+Quarter\s+(\d{4})", label)
    if not m:
        raise ValueError(f"unrecognised INE period label: {label!r}")
    return int(m.group(2)), int(m.group(1))


def fetch_indicator(
    period_codes: list[str],
    *,
    session: requests.Session | None = None,
    timeout: int = 180,
) -> tuple[dict[str, Any], str]:
    """Fetch the INE indicator JSON for the given periods. Returns (payload, url)."""
    dim1 = ",".join(period_codes)
    params = {"op": "2", "varcd": VARCD, "Dim1": dim1, "lang": "EN"}
    url = f"{DATA_API}?op=2&varcd={VARCD}&Dim1={dim1}&lang=EN"
    getter = session.get if session is not None else requests.get
    response = getter(
        DATA_API,
        params=params,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.json(), url


def payload_to_rows(payload: list | dict) -> list[dict[str, Any]]:
    """Decode the INE pindica JSON payload into long municipal rows."""
    top = payload[0] if isinstance(payload, list) else payload
    dados = top.get("Dados") or {}
    rows: list[dict[str, Any]] = []
    for period_label, records in dados.items():
        year, quarter = period_label_to_quarter(period_label)
        for rec in records:
            geocod = rec.get("geocod")
            geodsg = rec.get("geodsg")
            valor = rec.get("valor")
            if geocod is None or valor is None:
                continue
            if str(geocod) in AGGREGATE_GEOCODES:
                continue
            try:
                rent = float(valor)
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "municipality_code": str(geocod),
                    "municipality_name": geodsg,
                    "country_name": COUNTRY_NAME,
                    "country_iso3": COUNTRY_ISO3,
                    "period_label": period_label,
                    "year": year,
                    "quarter": quarter,
                    "period": f"{year}Q{quarter}",
                    "median_rent_eur_per_m2": rent,
                    "measure": "observed_new_lease_median_rent_eur_per_m2",
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
    """Map normalised GHSL city name -> spine info, restricted to Portugal."""
    lookup: dict[str, dict[str, Any]] = {}
    pt = spine[spine.get("country_name") == COUNTRY_NAME] if "country_name" in spine.columns else spine
    for row in pt.to_dict("records"):
        name = row.get("city_name")
        if name is None:
            continue
        key = normalise_name(name)
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


def attach_ghsl_matches(panel: pd.DataFrame, spine: pd.DataFrame) -> pd.DataFrame:
    lookup = build_spine_lookup(spine)
    keys = panel[["municipality_code", "municipality_name"]].drop_duplicates()
    records = []
    for row in keys.to_dict("records"):
        ine_norm = normalise_name(row["municipality_name"])
        ghsl_name = INE_TO_GHSL_NAME.get(ine_norm)
        match = lookup.get(normalise_name(ghsl_name)) if ghsl_name else lookup.get(ine_norm)
        if match is not None:
            records.append(
                {
                    "municipality_code": row["municipality_code"],
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
                    "municipality_code": row["municipality_code"],
                    "ieset_city_id": None,
                    "ghsl_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "ghsl_match_flag": False,
                    "ghsl_match_type": "unmatched",
                }
            )
    match_df = pd.DataFrame(records)
    return panel.merge(match_df, on="municipality_code", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    payload: list | dict | None = None,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], str]:
    if payload is None:
        payload, source_url = fetch_indicator(PERIOD_CODES, session=session)
    else:
        source_url = f"{DATA_API}?op=2&varcd={VARCD}&Dim1={','.join(PERIOD_CODES)}&lang=EN"

    rows = payload_to_rows(payload)
    if not rows:
        raise ValueError("INE indicator API returned no usable municipal observations")

    panel = pd.DataFrame(rows)
    spine = load_spine(city_spine_path)
    panel = attach_ghsl_matches(panel, spine)

    ordered = [
        "municipality_code",
        "municipality_name",
        "country_name",
        "country_iso3",
        "period",
        "period_label",
        "year",
        "quarter",
        "median_rent_eur_per_m2",
        "measure",
        "ieset_city_id",
        "ghsl_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "ghsl_match_flag",
        "ghsl_match_type",
    ]
    panel = panel[ordered].sort_values(
        ["municipality_code", "year", "quarter"]
    ).reset_index(drop=True)
    panel = panel.drop_duplicates(subset=["municipality_code", "period"]).reset_index(drop=True)

    matched = panel.loc[panel["ghsl_match_flag"], "municipality_code"].nunique()
    muni_count = panel["municipality_code"].nunique()
    stats = {
        "panel_rows": int(len(panel)),
        "municipality_count": int(muni_count),
        "matched_municipality_count": int(matched),
        "unmatched_municipality_count": int(muni_count - matched),
        "match_rate": round(matched / max(muni_count, 1), 4),
        "period_min": panel["period"].min(),
        "period_max": panel["period"].max(),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "rent_min_eur_per_m2": float(panel["median_rent_eur_per_m2"].min()),
        "rent_max_eur_per_m2": float(panel["median_rent_eur_per_m2"].max()),
        "matched_municipalities": sorted(
            panel.loc[panel["ghsl_match_flag"], "municipality_name"].unique().tolist()
        ),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
    }
    return panel, stats, source_url


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_portugal_ine_municipal_rents.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "portugal_ine_municipal_rents_panel",
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(
    panel: pd.DataFrame,
    stats: dict[str, Any],
    output_path: Path,
    fetch_ts: datetime,
    source_url: str,
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher=PUBLISHER,
        series_id=SERIES_ID,
        source_url=source_url,
        methodology_url=INDICATOR_PAGE,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="quarterly",
        units="median rent, EUR per square metre (new lease contracts)",
        currency="EUR",
        start_date=str(stats["period_min"]),
        end_date=str(stats["period_max"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "indicator": {
                "varcd": VARCD,
                "name": (
                    "Median house rental value of new lease agreements of household "
                    "dwellings (2021 Methodology)"
                ),
                "data_api": DATA_API,
                "meta_api": f"{META_API}?varcd={VARCD}&lang=EN",
            },
            "construction": (
                "Statistics Portugal (INE) key-free open indicator API (pindica.jsp, "
                f"varcd {VARCD}) pulled per quarter via Dim1; decoded to one row per "
                "(municipality_code, period). National 'Total' aggregate excluded. "
                "INE municipio codes/names preserved. Crosswalked to the Portugal subset "
                "of the IESET/GHSL top-1000 city universe by normalised name with a "
                "ghsl_match_flag; unmatched municipalities retained and flagged false."
            ),
            "caveat": (
                "Observed new-lease median rents (EUR/m2), not a hedonic or "
                "repeat-contract index. Coverage limited to municipalities with >100k "
                "inhabitants plus selected others, per INE local-level publication."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--output", default="data/derived/portugal_ine_municipal_rents_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    parser.add_argument(
        "--input-json",
        help="Optional path to a cached INE pindica JSON file; otherwise fetch from API.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    payload = None
    if args.input_json:
        payload = json.loads(path_arg(args.input_json).read_text())
    panel, stats, source_url = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        payload=payload,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts, source_url)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        f"OK {PUBLISHER}:{SERIES_ID} rows={result.rows} "
        f"periods={stats['period_min']}->{stats['period_max']} "
        f"municipalities={stats['municipality_count']} "
        f"matched={stats['matched_municipality_count']} ({stats['match_rate']:.1%}) "
        f"rent_eur_m2={stats['rent_min_eur_per_m2']:.2f}-{stats['rent_max_eur_per_m2']:.2f}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
