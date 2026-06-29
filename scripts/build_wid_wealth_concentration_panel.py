#!/usr/bin/env python3
"""Build a country-year WID net-wealth-concentration + wealth/income panel.

Purpose
-------
Construct a long-format country-year panel that operationalises the
Gabriel Zucman / Saez-Zucman wealth-concentration hypotheses:

  * Z2 - the post-1980 rise in top wealth shares (top 1% / top 0.1% / top 10%
    net personal wealth shares).
  * Z3 - the secular rise in the aggregate wealth-to-income ratio.

Source
------
Reads the on-disk WID bulk export vintage
``data/vintages/wid/wid_all@<UTC>.parquet`` (full all-country export).
No network access is required; the on-disk vintage is authoritative.

WID variable codes used (verified present in the vintage)
---------------------------------------------------------
Net personal wealth SHARES - variable ``shwealj992``
    shortname "Net personal wealth", unit "share" (stored as a 0-1 fraction;
    we rescale to 0-100 percent). pop=j (equal-split adults), age=992 (adults).
      * p99p100   -> top 1%  net personal wealth share
      * p99.9p100 -> top 0.1% net personal wealth share
      * p90p100   -> top 10% net personal wealth share

Wealth/income RATIO - variable ``whweali999``
    shortname "Net personal wealth", unit "% of national income"
    (net personal/household wealth expressed as a multiple of net national
    income; stored as a multiple, e.g. 2.96 = 296%). This is the household /
    personal variant of the wealth-to-income ratio, chosen to mirror the
    personal-wealth share numerator. percentile p0p100, pop=i, age=999.

Note on requested codes: the brief suggested ``shweal992j``/``shwealj992`` for
shares (matches ``shwealj992`` here) and ``wwealn999i`` for the ratio. The
``wwealn`` ratio family is NOT present in this vintage; the WID market-value
wealth-to-income ratios are instead carried under the ``w*weali999`` family
(``whweali999`` personal, ``wpweali999`` private, ``wnweali999`` national).
We use the personal variant ``whweali999`` to align with the share series.

Output
------
  * data/derived/wid_wealth_concentration_panel.parquet
        long format: country_iso3, year, series_id, value, unit
        (also carries country_wid (ISO2) and series_label for traceability).
  * data/manifests/fetch_run_<UTC>_wid_wealth_concentration.yaml
        provenance manifest (publisher=wid, source vintage path + sha256,
        retrieval timestamp, row count, series list).
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import utc_now, utc_stamp  # noqa: E402

WID_VINTAGE = ROOT / "data" / "vintages" / "wid" / "wid_all@2026-05-05T204054Z.parquet"
OUT_PARQUET = ROOT / "data" / "derived" / "wid_wealth_concentration_panel.parquet"

SOURCE_URL = "https://wid.world/bulk_download/"
SOURCE_PAGE_URL = "https://wid.world/data/"
METHODOLOGY_URL = "https://wid.world/methodology/"
LICENSE = "academic_citation"
PUBLISHER = "wid"

YEAR_MIN = 1980
YEAR_MAX = 2023

# Series specifications. Each maps a derived series_id to the underlying WID
# variable + percentile slice, the output unit, and a value scale factor.
SHARE_VARIABLE = "shwealj992"
RATIO_VARIABLE = "whweali999"

SERIES_SPECS: dict[str, dict[str, Any]] = {
    "top1_net_personal_wealth_share": {
        "variable": SHARE_VARIABLE,
        "percentile": "p99p100",
        "scale": 100.0,
        "unit": "share of net personal wealth (%)",
        "label": "Top 1% net personal wealth share",
    },
    "top01_net_personal_wealth_share": {
        "variable": SHARE_VARIABLE,
        "percentile": "p99.9p100",
        "scale": 100.0,
        "unit": "share of net personal wealth (%)",
        "label": "Top 0.1% net personal wealth share",
    },
    "top10_net_personal_wealth_share": {
        "variable": SHARE_VARIABLE,
        "percentile": "p90p100",
        "scale": 100.0,
        "unit": "share of net personal wealth (%)",
        "label": "Top 10% net personal wealth share",
    },
    "net_personal_wealth_income_ratio": {
        "variable": RATIO_VARIABLE,
        "percentile": "p0p100",
        "scale": 100.0,  # WID stores multiples (2.96); rescale to % of nat. income
        "unit": "net personal wealth as % of national income",
        "label": "Net personal wealth / national income ratio",
    },
}

# Target coverage emphasis (OECD + major economies). RU is absent from this
# WID vintage and is therefore reported as a coverage gap in the brief.
PRIORITY_ISO2 = [
    "US", "FR", "DE", "GB", "IT", "ES", "SE", "NO", "JP", "CA",
    "AU", "CN", "IN", "BR", "ZA",
]

# WID uses ISO2 country codes. Explicit ISO2 -> ISO3 map for every country that
# carries the net-personal-wealth series in this vintage (fixed, audited set).
ISO2_TO_ISO3 = {
    "AR": "ARG", "AT": "AUT", "AU": "AUS", "BE": "BEL", "BR": "BRA",
    "CA": "CAN", "CH": "CHE", "CL": "CHL", "CN": "CHN", "CO": "COL",
    "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EG": "EGY",
    "ES": "ESP", "FI": "FIN", "FR": "FRA", "GB": "GBR", "GR": "GRC",
    "ID": "IDN", "IE": "IRL", "IL": "ISR", "IN": "IND", "IT": "ITA",
    "JP": "JPN", "KR": "KOR", "MX": "MEX", "NG": "NGA", "NL": "NLD",
    "NO": "NOR", "NZ": "NZL", "PE": "PER", "PL": "POL", "PT": "PRT",
    "SE": "SWE", "SG": "SGP", "TR": "TUR", "US": "USA", "ZA": "ZAF",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not WID_VINTAGE.exists():
        raise FileNotFoundError(f"missing WID vintage: {WID_VINTAGE}")

    variables = sorted({spec["variable"] for spec in SERIES_SPECS.values()})
    raw = pd.read_parquet(
        WID_VINTAGE,
        columns=["country", "variable", "percentile", "year", "value"],
    )
    raw["variable"] = raw["variable"].astype("string")
    raw = raw[raw["variable"].isin(variables)].copy()
    raw["percentile"] = raw["percentile"].astype("string")
    raw["country"] = raw["country"].astype("string")
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").astype("Int64")
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")

    frames: list[pd.DataFrame] = []
    per_series_stats: dict[str, dict[str, Any]] = {}
    for series_id, spec in SERIES_SPECS.items():
        sub = raw[
            (raw["variable"] == spec["variable"])
            & (raw["percentile"] == spec["percentile"])
        ].copy()
        sub = sub.dropna(subset=["country", "year", "value"])
        sub = sub[(sub["year"] >= YEAR_MIN) & (sub["year"] <= YEAR_MAX)]
        # Map ISO2 -> ISO3; drop aggregates / regions not in the country map.
        sub["country_iso3"] = sub["country"].map(ISO2_TO_ISO3)
        sub = sub[sub["country_iso3"].notna()].copy()
        sub["value"] = sub["value"] * float(spec["scale"])
        # one row per country-year (vintage already unique on pop=j/i, age)
        sub = (
            sub.sort_values(["country_iso3", "year"])
            .drop_duplicates(subset=["country_iso3", "year"], keep="first")
        )
        out = pd.DataFrame(
            {
                "country_iso3": sub["country_iso3"].astype(str),
                "country_wid": sub["country"].astype(str),
                "year": sub["year"].astype(int),
                "series_id": series_id,
                "series_label": spec["label"],
                "value": sub["value"].astype(float),
                "unit": spec["unit"],
            }
        )
        frames.append(out)
        per_series_stats[series_id] = {
            "wid_variable": spec["variable"],
            "percentile": spec["percentile"],
            "unit": spec["unit"],
            "rows": int(len(out)),
            "countries": int(out["country_iso3"].nunique()),
            "year_min": int(out["year"].min()) if len(out) else None,
            "year_max": int(out["year"].max()) if len(out) else None,
        }

    panel = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["series_id", "country_iso3", "year"])
        .reset_index(drop=True)
    )

    priority_present = sorted(
        {ISO2_TO_ISO3[c] for c in PRIORITY_ISO2 if c in ISO2_TO_ISO3}
        & set(panel["country_iso3"].unique())
    )
    priority_missing = sorted(
        {ISO2_TO_ISO3.get(c, c) for c in PRIORITY_ISO2}
        - set(panel["country_iso3"].unique())
    )

    stats = {
        "total_rows": int(len(panel)),
        "country_count": int(panel["country_iso3"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "series": per_series_stats,
        "countries_iso3": sorted(panel["country_iso3"].unique()),
        "priority_countries_present": priority_present,
        "priority_countries_missing": priority_missing,
    }
    return panel, stats


def write_manifest(
    *, panel: pd.DataFrame, stats: dict[str, Any], fetch_ts: datetime, source_sha: str
) -> Path:
    manifests = ROOT / "data" / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp(fetch_ts)
    path = manifests / f"fetch_run_{stamp}_wid_wealth_concentration.yaml"
    payload = {
        "run_utc": stamp,
        "retrieval_timestamp": fetch_ts.isoformat(),
        "publisher": PUBLISHER,
        "source_url": SOURCE_URL,
        "source_page_url": SOURCE_PAGE_URL,
        "methodology_url": METHODOLOGY_URL,
        "license": LICENSE,
        "source_vintage": {
            "path": str(WID_VINTAGE.relative_to(ROOT)),
            "sha256": source_sha,
        },
        "output": {
            "path": str(OUT_PARQUET.relative_to(ROOT)),
            "format": "long: country_iso3, year, series_id, value, unit",
            "row_count": stats["total_rows"],
            "country_count": stats["country_count"],
            "year_range": [stats["year_min"], stats["year_max"]],
        },
        "series": [
            {
                "series_id": sid,
                "wid_variable": s["wid_variable"],
                "percentile": s["percentile"],
                "unit": s["unit"],
                "rows": s["rows"],
                "countries": s["countries"],
                "year_range": [s["year_min"], s["year_max"]],
            }
            for sid, s in stats["series"].items()
        ],
        "coverage": {
            "priority_present": stats["priority_countries_present"],
            "priority_missing": stats["priority_countries_missing"],
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def main() -> int:
    fetch_ts = utc_now()
    panel, stats = build_panel()

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT_PARQUET, engine="pyarrow", index=False)

    source_sha = sha256(WID_VINTAGE)
    manifest = write_manifest(
        panel=panel, stats=stats, fetch_ts=fetch_ts, source_sha=source_sha
    )

    print(f"OK wid:wid_wealth_concentration_panel rows={stats['total_rows']}")
    print(f"  countries={stats['country_count']} years={stats['year_min']}-{stats['year_max']}")
    for sid, s in stats["series"].items():
        print(
            f"  {sid}: var={s['wid_variable']} pct={s['percentile']} "
            f"rows={s['rows']} countries={s['countries']} "
            f"years={s['year_min']}-{s['year_max']}"
        )
    print(f"  priority present: {stats['priority_countries_present']}")
    print(f"  priority missing: {stats['priority_countries_missing']}")
    print(f"parquet: {OUT_PARQUET.relative_to(ROOT)}")
    print(f"manifest: {manifest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
