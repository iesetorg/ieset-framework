#!/usr/bin/env python3
"""Build country-year CEPII Gravity exposure panels.

Inputs:
- Local CEPII Gravity V202211 official CSV zip at data/raw/cepii/.

Outputs:
- A wide country-year panel of gravity exposures.
- Narrow country-year series for FTA/WTO/EU market access and trade-flow
  exposure, suitable for generic IESET panel runners.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, utc_stamp, write_manifest, write_vintage  # noqa: E402


RAW_ZIP = ROOT / "data" / "raw" / "cepii" / "Gravity_csv_V202211.zip"
GRAVITY_MEMBER = "Gravity_V202211.csv"
SOURCE_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
METHODOLOGY_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf"
LICENSE = "CEPII Gravity database; see CEPII terms and documentation"

SERIES: dict[str, dict[str, str]] = {
    "gravity_fta_partner_count": {
        "column": "fta_partner_count",
        "units": "partner count",
        "description": "Count of active foreign partners with CEPII fta_wto == 1.",
    },
    "gravity_new_fta_partner_count": {
        "column": "new_fta_partner_count",
        "units": "partner count",
        "description": "Positive year-over-year increase in active CEPII FTA partner count.",
    },
    "gravity_fta_partner_gdp_share": {
        "column": "fta_partner_gdp_share",
        "units": "share of observed foreign partner GDP",
        "description": "Share of observed foreign partner GDP covered by CEPII fta_wto == 1.",
    },
    "gravity_fta_market_potential_share": {
        "column": "fta_market_potential_share",
        "units": "share of distance-weighted observed foreign partner GDP",
        "description": "FTA-covered share of distance-weighted foreign GDP market potential.",
    },
    "gravity_foreign_market_potential": {
        "column": "foreign_market_potential",
        "units": "CEPII GDP divided by distance",
        "description": "Sum over active foreign partners of destination GDP divided by CEPII distw_harmonic.",
    },
    "gravity_wto_partner_gdp_share": {
        "column": "wto_partner_gdp_share",
        "units": "share of observed foreign partner GDP",
        "description": "Share of observed foreign partner GDP where both origin and destination are WTO members.",
    },
    "gravity_eu_partner_gdp_share": {
        "column": "eu_partner_gdp_share",
        "units": "share of observed foreign partner GDP",
        "description": "Share of observed foreign partner GDP where both origin and destination are EU members.",
    },
    "gravity_goods_services_rta_partner_count": {
        "column": "goods_services_rta_partner_count",
        "units": "partner count",
        "description": "Count of active partners with RTA coverage coded as goods and services.",
    },
    "gravity_fta_tradeflow_baci_share": {
        "column": "fta_tradeflow_baci_share",
        "units": "share of observed BACI tradeflow",
        "description": "Share of observed CEPII BACI tradeflow with FTA partners.",
    },
    "gravity_fta_manuf_tradeflow_baci_share": {
        "column": "fta_manuf_tradeflow_baci_share",
        "units": "share of observed BACI manufacturing tradeflow",
        "description": "Share of observed CEPII BACI manufacturing tradeflow with FTA partners.",
    },
    "gravity_total_tradeflow_baci": {
        "column": "total_tradeflow_baci",
        "units": "CEPII BACI tradeflow level",
        "description": "Sum of observed CEPII BACI tradeflow over active foreign partners.",
    },
    "gravity_manuf_tradeflow_baci_share": {
        "column": "manuf_tradeflow_baci_share",
        "units": "share of observed BACI tradeflow",
        "description": "Manufacturing tradeflow share of observed CEPII BACI tradeflow.",
    },
}


def safe_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    if pd.isna(out):
        return None
    return out


def truthy(value: object) -> bool:
    numeric = safe_float(value)
    return bool(numeric is not None and numeric > 0)


def ratio(numerator: float, denominator: float) -> float | None:
    if denominator > 0:
        return numerator / denominator
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def empty_agg() -> dict[str, Any]:
    return {
        "partner_count": 0,
        "fta_partner_count": 0,
        "wto_partner_count": 0,
        "eu_partner_count": 0,
        "goods_services_rta_partner_count": 0,
        "partner_gdp_total": 0.0,
        "fta_partner_gdp": 0.0,
        "wto_partner_gdp": 0.0,
        "eu_partner_gdp": 0.0,
        "foreign_market_potential": 0.0,
        "fta_market_potential": 0.0,
        "total_tradeflow_baci": 0.0,
        "fta_tradeflow_baci": 0.0,
        "manuf_tradeflow_baci": 0.0,
        "fta_manuf_tradeflow_baci": 0.0,
        "origin_gdp": None,
    }


def build_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not RAW_ZIP.exists():
        raise FileNotFoundError(f"missing local CEPII Gravity zip: {RAW_ZIP}")

    aggs: defaultdict[tuple[str, int], dict[str, Any]] = defaultdict(empty_agg)
    raw_rows = 0
    dyads_used = 0

    with zipfile.ZipFile(RAW_ZIP) as zf:
        with zf.open(GRAVITY_MEMBER) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            for row in reader:
                raw_rows += 1
                year_float = safe_float(row.get("year"))
                if year_float is None:
                    continue
                year = int(year_float)
                origin = str(row.get("iso3_o") or "").strip().upper()
                dest = str(row.get("iso3_d") or "").strip().upper()
                if len(origin) != 3 or len(dest) != 3 or origin == dest:
                    continue
                if not truthy(row.get("country_exists_o")) or not truthy(row.get("country_exists_d")):
                    continue

                key = (origin, year)
                item = aggs[key]
                item["partner_count"] += 1
                dyads_used += 1

                origin_gdp = safe_float(row.get("gdp_o"))
                if origin_gdp is not None and origin_gdp > 0:
                    previous = item["origin_gdp"]
                    item["origin_gdp"] = origin_gdp if previous is None else max(previous, origin_gdp)

                partner_gdp = safe_float(row.get("gdp_d"))
                distance = safe_float(row.get("distw_harmonic")) or safe_float(row.get("dist"))
                weighted_gdp = None
                if partner_gdp is not None and partner_gdp > 0:
                    item["partner_gdp_total"] += partner_gdp
                    if distance is not None and distance > 0:
                        weighted_gdp = partner_gdp / distance
                        item["foreign_market_potential"] += weighted_gdp

                is_fta = truthy(row.get("fta_wto"))
                is_wto_pair = truthy(row.get("wto_o")) and truthy(row.get("wto_d"))
                is_eu_pair = truthy(row.get("eu_o")) and truthy(row.get("eu_d"))

                if is_fta:
                    item["fta_partner_count"] += 1
                    if partner_gdp is not None and partner_gdp > 0:
                        item["fta_partner_gdp"] += partner_gdp
                    if weighted_gdp is not None:
                        item["fta_market_potential"] += weighted_gdp
                if is_wto_pair:
                    item["wto_partner_count"] += 1
                    if partner_gdp is not None and partner_gdp > 0:
                        item["wto_partner_gdp"] += partner_gdp
                if is_eu_pair:
                    item["eu_partner_count"] += 1
                    if partner_gdp is not None and partner_gdp > 0:
                        item["eu_partner_gdp"] += partner_gdp
                if str(row.get("rta_coverage") or "").strip() == "2":
                    item["goods_services_rta_partner_count"] += 1

                tradeflow = safe_float(row.get("tradeflow_baci"))
                if tradeflow is not None and tradeflow > 0:
                    item["total_tradeflow_baci"] += tradeflow
                    if is_fta:
                        item["fta_tradeflow_baci"] += tradeflow
                manuf_tradeflow = safe_float(row.get("manuf_tradeflow_baci"))
                if manuf_tradeflow is not None and manuf_tradeflow > 0:
                    item["manuf_tradeflow_baci"] += manuf_tradeflow
                    if is_fta:
                        item["fta_manuf_tradeflow_baci"] += manuf_tradeflow

    rows: list[dict[str, object]] = []
    for (country, year), item in sorted(aggs.items()):
        partner_gdp_total = item["partner_gdp_total"]
        market_potential = item["foreign_market_potential"]
        tradeflow = item["total_tradeflow_baci"]
        manuf_tradeflow = item["manuf_tradeflow_baci"]
        rows.append(
            {
                "country_iso3": country,
                "year": year,
                "partner_count": item["partner_count"],
                "fta_partner_count": item["fta_partner_count"],
                "wto_partner_count": item["wto_partner_count"],
                "eu_partner_count": item["eu_partner_count"],
                "goods_services_rta_partner_count": item["goods_services_rta_partner_count"],
                "partner_gdp_total": partner_gdp_total or None,
                "fta_partner_gdp_share": ratio(item["fta_partner_gdp"], partner_gdp_total),
                "wto_partner_gdp_share": ratio(item["wto_partner_gdp"], partner_gdp_total),
                "eu_partner_gdp_share": ratio(item["eu_partner_gdp"], partner_gdp_total),
                "foreign_market_potential": market_potential or None,
                "fta_market_potential_share": ratio(item["fta_market_potential"], market_potential),
                "total_tradeflow_baci": tradeflow or None,
                "fta_tradeflow_baci_share": ratio(item["fta_tradeflow_baci"], tradeflow),
                "manuf_tradeflow_baci": manuf_tradeflow or None,
                "fta_manuf_tradeflow_baci_share": ratio(item["fta_manuf_tradeflow_baci"], manuf_tradeflow),
                "manuf_tradeflow_baci_share": ratio(manuf_tradeflow, tradeflow),
                "origin_gdp": item["origin_gdp"],
            }
        )

    panel = pd.DataFrame(rows).sort_values(["country_iso3", "year"]).reset_index(drop=True)
    panel["new_fta_partner_count"] = (
        panel.groupby("country_iso3")["fta_partner_count"].diff().clip(lower=0).fillna(0).astype(int)
    )
    panel["fta_partner_count_change"] = panel.groupby("country_iso3")["fta_partner_count"].diff().fillna(0)
    panel["year"] = panel["year"].astype(int)

    stats = {
        "raw_rows": raw_rows,
        "directed_dyads_used": dyads_used,
        "country_year_rows": int(len(panel)),
        "country_count": int(panel["country_iso3"].nunique()),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "source_zip_sha256": sha256(RAW_ZIP),
    }
    return panel, stats


def emit(
    *,
    frame: pd.DataFrame,
    series_id: str,
    units: str,
    fetch_ts: datetime,
    source_sha: str,
    extra: dict[str, Any],
) -> FetchResult:
    out, parquet_sha = write_vintage(
        publisher="cepii",
        series_id=series_id,
        frame=frame,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="cepii",
        series_id=series_id,
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(frame),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(frame["year"].min())) if len(frame) else None,
        end_date=str(int(frame["year"].max())) if len(frame) else None,
        sha256=parquet_sha,
        parquet_path=out,
        extra={"source_zip_sha256": source_sha, **extra},
    )


def main() -> int:
    fetch_ts = utc_now()
    panel, stats = build_panel()

    results: list[FetchResult] = []
    wide_extra = {
        "input_file": str(RAW_ZIP.relative_to(ROOT)),
        "input_member": GRAVITY_MEMBER,
        "construction": (
            "Directed dyads are filtered to existing origin and destination countries, "
            "excluding self-pairs, then collapsed by origin country-year."
        ),
        "stats": stats,
        "columns": list(panel.columns),
    }
    results.append(
        emit(
            frame=panel,
            series_id="gravity_exposure_panel",
            units="mixed; see column names",
            fetch_ts=fetch_ts,
            source_sha=stats["source_zip_sha256"],
            extra=wide_extra,
        )
    )

    for series_id, spec in SERIES.items():
        column = spec["column"]
        narrow = panel[["country_iso3", "year", column]].dropna().rename(columns={column: "value"})
        narrow = narrow.sort_values(["country_iso3", "year"]).reset_index(drop=True)
        results.append(
            emit(
                frame=narrow,
                series_id=series_id,
                units=spec["units"],
                fetch_ts=fetch_ts,
                source_sha=stats["source_zip_sha256"],
                extra={
                    "input_series": "cepii:gravity_exposure_panel",
                    "source_column": column,
                    "definition": spec["description"],
                    "country_count": int(narrow["country_iso3"].nunique()) if len(narrow) else 0,
                },
            )
        )

    manifest = write_manifest(results, run_stamp=utc_stamp(fetch_ts))
    audit = ROOT / "engine" / "audits" / f"cepii_gravity_exposure_panel_build_{utc_stamp(fetch_ts)}.json"
    audit.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2) + "\n")

    for result in results:
        print(
            f"OK {result.publisher}:{result.series_id} rows={result.rows} "
            f"period={result.start_date}->{result.end_date} vintage={result.parquet_path.relative_to(ROOT)}"
        )
    print(f"manifest: {manifest.relative_to(ROOT)}")
    print(f"audit: {audit.relative_to(ROOT)}")
    print(
        "stats: "
        f"raw_rows={stats['raw_rows']} dyads_used={stats['directed_dyads_used']} "
        f"country_year_rows={stats['country_year_rows']} countries={stats['country_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
