#!/usr/bin/env python3
"""Build a country-year OECD tax-structure panel (Zucman Z1/Z4 context).

Source: OECD SDMX REST (key-free public endpoint), Centre for Tax Policy and
Administration (OECD.CTP.TPS) dataflows.

Series pulled (all country-year, annual):
- Recurrent taxes on net wealth (Revenue Statistics category 4200), % of GDP
- Estate, inheritance and gift taxes (category 4300), % of GDP
- Total tax revenue, % of GDP
- Wealth / estate revenue as % of total taxation (derived: cat/GDP over total/GDP)
- Top statutory personal income tax rate (Tax Database, TS_PIT)
- Combined corporate income tax rate (Tax Database, CIT_C statutory)

Coverage is the union of the OECD comparative Revenue Statistics flow and the
broader Global comparative flow (OECD members + key partners), 1990-2024 where
available.

Output (long): country_iso3, year, series_id, value, unit.

Reuses the repo's OECD SDMX request idiom (data/fetchers/oecd.py) and the
FetchResult / write_vintage / write_manifest contract (data/fetchers/_base.py),
following scripts/build_cepii_gravity_exposure_panels_2026_05_15.py as the
build/manifest exemplar.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import (  # noqa: E402
    FetchResult,
    utc_now,
    utc_stamp,
    write_manifest,
    write_vintage,
)

OECD_BASE = "https://sdmx.oecd.org/public/rest/data"
LICENSE = "OECD standard permissions (attribution required)"
HEADERS = {"Accept": "text/csv,*/*;q=0.8", "User-Agent": "Mozilla/5.0 IESET"}

DERIVED = ROOT / "data" / "derived"
PANEL_PARQUET = DERIVED / "oecd_tax_structure_panel.parquet"

# Revenue Statistics comparative flows. OECD = members; GLOBAL = members + key
# partners. We pull both and union (OECD wins on overlap, identical figures).
REV_FLOW_OECD = "OECD.CTP.TPS,DSD_REV_COMP_OECD@DF_RSOECD,2.0"
REV_FLOW_GLOBAL = "OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,2.1"
# Revenue key order: REF_AREA.MEASURE.SECTOR.STANDARD_REVENUE.CTRY_SPECIFIC.UNIT.FREQ
REV_KEY = ".TAX_REV.S13.T_4200+T_4300+_T..PT_B1GQ.A"

CIT_FLOW = "OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0"
# CIT key order (9): REF_AREA.FREQ.MEASURE.TARGETING.UNIT.SECTOR.DIV.RATE.TAXBASE
CIT_KEY = ".A.CIT_C.ST......"

PIT_FLOW = "OECD.CTP.TPS,DSD_TAX_PIT@DF_PIT_TOP_EARN_THRESH,1.0"
# PIT key order (12): REF_AREA.FREQ.TRANSACTION.MEASURE.UNIT.SECTOR.CIVIL.HH.INCP.INCS.LEVEL.TAXBASE
PIT_KEY = ".A..TS_PIT.PT_WG_EARN_G......."

START_PERIOD = "1990"
END_PERIOD = "2024"

# Standard-revenue codes -> output series ids (% of GDP side).
REV_GDP_SERIES = {
    "T_4200": "oecd_tax_recurrent_net_wealth_pct_gdp",
    "T_4300": "oecd_tax_estate_inheritance_gift_pct_gdp",
    "_T": "oecd_tax_total_pct_gdp",
}
# Derived % of total-taxation series ids.
REV_PCT_TAX_SERIES = {
    "T_4200": "oecd_tax_recurrent_net_wealth_pct_total_tax",
    "T_4300": "oecd_tax_estate_inheritance_gift_pct_total_tax",
}

SERIES_UNITS = {
    "oecd_tax_recurrent_net_wealth_pct_gdp": "percent of GDP",
    "oecd_tax_estate_inheritance_gift_pct_gdp": "percent of GDP",
    "oecd_tax_total_pct_gdp": "percent of GDP",
    "oecd_tax_recurrent_net_wealth_pct_total_tax": "percent of total taxation",
    "oecd_tax_estate_inheritance_gift_pct_total_tax": "percent of total taxation",
    "oecd_top_statutory_pit_rate": "percent",
    "oecd_combined_corporate_income_tax_rate": "percent",
}


class BuildError(RuntimeError):
    pass


def pull_csv(flow: str, key: str) -> tuple[pd.DataFrame, str]:
    """Fetch a filtered OECD SDMX dataflow as a DataFrame (csvfilewithlabels)."""
    url = f"{OECD_BASE}/{flow}/{key or 'all'}"
    params = {
        "format": "csvfilewithlabels",
        "startPeriod": START_PERIOD,
        "endPeriod": END_PERIOD,
    }
    resp = requests.get(url, params=params, timeout=240, headers=HEADERS)
    if resp.status_code >= 400:
        raise BuildError(
            f"OECD HTTP {resp.status_code} for {flow} key='{key}': {resp.text[:200]}"
        )
    text = resp.text
    if not text.strip():
        raise BuildError(f"OECD returned empty CSV for {flow} key='{key}'")
    df = pd.read_csv(io.StringIO(text), low_memory=False)
    return df, f"{url}?startPeriod={START_PERIOD}&endPeriod={END_PERIOD}&format=csvfilewithlabels"


def is_country(code: object) -> bool:
    """Keep ISO3 country codes; drop SDMX aggregates (e.g. A9, F, OECD)."""
    s = str(code or "").strip().upper()
    return len(s) == 3 and s.isalpha() and s not in {"OEC", "OED", "WXD", "EUU"}


def long_rows_from_obs(
    df: pd.DataFrame, value_col: str, series_id: str, std_rev_filter: str | None = None
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sub = df
    if std_rev_filter is not None:
        sub = sub[sub["STANDARD_REVENUE"] == std_rev_filter]
    for _, r in sub.iterrows():
        area = r.get("REF_AREA")
        if not is_country(area):
            continue
        val = r.get(value_col)
        if pd.isna(val):
            continue
        try:
            year = int(str(r.get("TIME_PERIOD"))[:4])
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "country_iso3": str(area).strip().upper(),
                "year": year,
                "series_id": series_id,
                "value": float(val),
                "unit": SERIES_UNITS[series_id],
            }
        )
    return rows


def build_revenue_long() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build % GDP + derived % of total taxation rows from both comparative flows."""
    df_oecd, url_oecd = pull_csv(REV_FLOW_OECD, REV_KEY)
    df_global, url_global = pull_csv(REV_FLOW_GLOBAL, REV_KEY)

    # Build a country-year-category % GDP table; OECD flow takes precedence.
    def gdp_table(df: pd.DataFrame, source: str) -> pd.DataFrame:
        d = df[df["REF_AREA"].map(is_country)].copy()
        d = d[d["STANDARD_REVENUE"].isin(REV_GDP_SERIES)]
        d = d.dropna(subset=["OBS_VALUE"])
        d["year"] = d["TIME_PERIOD"].astype(str).str[:4].astype(int)
        d["country_iso3"] = d["REF_AREA"].str.strip().str.upper()
        d["source"] = source
        return d[["country_iso3", "year", "STANDARD_REVENUE", "OBS_VALUE", "source"]]

    tbl = pd.concat(
        [gdp_table(df_oecd, "oecd"), gdp_table(df_global, "global")],
        ignore_index=True,
    )
    # Prefer the OECD flow value on overlap.
    tbl["src_rank"] = (tbl["source"] == "oecd").astype(int)
    tbl = (
        tbl.sort_values(["country_iso3", "year", "STANDARD_REVENUE", "src_rank"])
        .drop_duplicates(["country_iso3", "year", "STANDARD_REVENUE"], keep="last")
        .reset_index(drop=True)
    )

    rows: list[dict[str, Any]] = []
    for code, series_id in REV_GDP_SERIES.items():
        sub = tbl[tbl["STANDARD_REVENUE"] == code]
        for _, r in sub.iterrows():
            rows.append(
                {
                    "country_iso3": r["country_iso3"],
                    "year": int(r["year"]),
                    "series_id": series_id,
                    "value": float(r["OBS_VALUE"]),
                    "unit": SERIES_UNITS[series_id],
                }
            )

    # Derived % of total taxation = (category % GDP) / (total % GDP) * 100.
    wide = tbl.pivot_table(
        index=["country_iso3", "year"],
        columns="STANDARD_REVENUE",
        values="OBS_VALUE",
        aggfunc="first",
    ).reset_index()
    for code, series_id in REV_PCT_TAX_SERIES.items():
        if code not in wide.columns or "_T" not in wide.columns:
            continue
        for _, r in wide.iterrows():
            cat = r.get(code)
            total = r.get("_T")
            if pd.isna(cat) or pd.isna(total) or total <= 0:
                continue
            rows.append(
                {
                    "country_iso3": r["country_iso3"],
                    "year": int(r["year"]),
                    "series_id": series_id,
                    "value": float(cat) / float(total) * 100.0,
                    "unit": SERIES_UNITS[series_id],
                }
            )

    meta = {
        "revenue_flow_oecd": REV_FLOW_OECD,
        "revenue_flow_global": REV_FLOW_GLOBAL,
        "revenue_key": REV_KEY,
        "revenue_url_oecd": url_oecd,
        "revenue_url_global": url_global,
        "rev_oecd_raw_rows": int(len(df_oecd)),
        "rev_global_raw_rows": int(len(df_global)),
    }
    return rows, meta


def build_rate_long() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    df_pit, url_pit = pull_csv(PIT_FLOW, PIT_KEY)
    df_cit, url_cit = pull_csv(CIT_FLOW, CIT_KEY)
    rows: list[dict[str, Any]] = []
    rows += long_rows_from_obs(df_pit, "OBS_VALUE", "oecd_top_statutory_pit_rate")
    rows += long_rows_from_obs(
        df_cit, "OBS_VALUE", "oecd_combined_corporate_income_tax_rate"
    )
    meta = {
        "pit_flow": PIT_FLOW,
        "pit_key": PIT_KEY,
        "pit_url": url_pit,
        "pit_measure": "TS_PIT (Top statutory personal income tax rate)",
        "cit_flow": CIT_FLOW,
        "cit_key": CIT_KEY,
        "cit_url": url_cit,
        "cit_measure": "CIT_C/ST (Combined statutory corporate income tax rate)",
    }
    return rows, meta


def build_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    rev_rows, rev_meta = build_revenue_long()
    rate_rows, rate_meta = build_rate_long()
    panel = pd.DataFrame(rev_rows + rate_rows)
    if panel.empty:
        raise BuildError("empty panel — all OECD pulls returned no usable rows")
    panel = (
        panel.dropna(subset=["value"])
        .drop_duplicates(["country_iso3", "year", "series_id"])
        .sort_values(["country_iso3", "year", "series_id"])
        .reset_index(drop=True)
    )
    panel["year"] = panel["year"].astype(int)

    series_coverage = {
        sid: {
            "rows": int((panel["series_id"] == sid).sum()),
            "countries": int(panel.loc[panel["series_id"] == sid, "country_iso3"].nunique()),
            "year_min": int(panel.loc[panel["series_id"] == sid, "year"].min()),
            "year_max": int(panel.loc[panel["series_id"] == sid, "year"].max()),
        }
        for sid in sorted(panel["series_id"].unique())
    }
    stats = {
        "rows": int(len(panel)),
        "countries": int(panel["country_iso3"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "series": sorted(panel["series_id"].unique()),
        "series_coverage": series_coverage,
        **rev_meta,
        **rate_meta,
    }
    return panel, stats


def emit_vintage(frame: pd.DataFrame, series_id: str, source_url: str, units: str, fetch_ts) -> FetchResult:
    path, sha = write_vintage(
        publisher="oecd",
        series_id=series_id,
        frame=frame,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="oecd",
        series_id=series_id,
        source_url=source_url,
        methodology_url="https://www.oecd.org/en/data/datasets/global-revenue-statistics-database.html",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=int(len(frame)),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(frame["year"].min())) if len(frame) else None,
        end_date=str(int(frame["year"].max())) if len(frame) else None,
        sha256=sha,
        parquet_path=path,
        extra={"series_id": series_id},
    )


def main() -> int:
    fetch_ts = utc_now()
    panel, stats = build_panel()

    DERIVED.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(PANEL_PARQUET, engine="pyarrow", index=False)
    panel_sha = hashlib.sha256(PANEL_PARQUET.read_bytes()).hexdigest()

    results: list[FetchResult] = []
    # One manifest entry for the consolidated long panel.
    results.append(
        FetchResult(
            publisher="oecd",
            series_id="oecd_tax_structure_panel",
            source_url=stats["revenue_url_oecd"],
            methodology_url="https://www.oecd.org/en/data/datasets/global-revenue-statistics-database.html",
            license=LICENSE,
            fetch_utc=fetch_ts,
            rows=int(len(panel)),
            frequency="annual",
            units="long: country_iso3, year, series_id, value, unit",
            currency=None,
            start_date=str(stats["year_min"]),
            end_date=str(stats["year_max"]),
            sha256=panel_sha,
            parquet_path=PANEL_PARQUET,
            extra={"stats": stats},
        )
    )
    # Plus a per-series narrow vintage for each series for downstream runners.
    for sid in stats["series"]:
        narrow = panel[panel["series_id"] == sid][["country_iso3", "year", "value"]].reset_index(drop=True)
        src = stats["pit_url"] if sid.endswith("pit_rate") else (
            stats["cit_url"] if "corporate" in sid else stats["revenue_url_oecd"]
        )
        results.append(
            emit_vintage(narrow, sid, src, SERIES_UNITS[sid], fetch_ts)
        )

    manifest = write_manifest(results, run_stamp=utc_stamp(fetch_ts))
    # Rename manifest to the task-specified scoped filename.
    scoped = manifest.parent / f"fetch_run_{utc_stamp(fetch_ts)}_oecd_tax_structure.yaml"
    manifest.rename(scoped)

    audit = ROOT / "engine" / "audits" / f"oecd_tax_structure_panel_build_{utc_stamp(fetch_ts)}.json"
    audit.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2) + "\n")

    print(f"panel: {PANEL_PARQUET.relative_to(ROOT)} rows={len(panel)} sha256={panel_sha[:12]}")
    print(
        f"coverage: countries={stats['countries']} years={stats['year_min']}-{stats['year_max']} "
        f"series={len(stats['series'])}"
    )
    for sid, cov in stats["series_coverage"].items():
        print(
            f"  {sid}: rows={cov['rows']} countries={cov['countries']} "
            f"{cov['year_min']}-{cov['year_max']}"
        )
    print(f"manifest: {scoped.relative_to(ROOT)}")
    print(f"audit: {audit.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
