#!/usr/bin/env python3
"""Build a local export-diversification proxy from WDI merchandise shares.

The preferred high-resolution recipe for export diversification is a product
Theil or HHI from UN Comtrade/UNCTAD product-level exports. That data is not
always present locally, so this script builds a broad but reproducible proxy
from WDI/UN merchandise-export share series:

  - agricultural raw materials exports (% of merchandise exports)
  - fuel exports (% of merchandise exports)
  - manufactures exports (% of merchandise exports)
  - ores and metals exports (% of merchandise exports)
  - residual other exports

It writes:
  - derived:export_diversification_index, value = 1 - HHI
  - derived:export_concentration_hhi_broad, value = HHI
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, utc_stamp, write_manifest, write_vintage

VINTAGES = ROOT / "data" / "vintages"

COMPONENTS = {
    "agricultural_raw_materials": "TX.VAL.AGRI.ZS.UN",
    "fuel": "TX.VAL.FUEL.ZS.UN",
    "manufactures": "TX.VAL.MANF.ZS.UN",
    "ores_metals": "TX.VAL.MMTL.ZS.UN",
}

MIN_COMPONENTS = 3


def latest_vintage(publisher: str, series: str) -> Path:
    paths = sorted((VINTAGES / publisher).glob(f"{series}@*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no local vintage for {publisher}:{series}")
    return paths[-1]


def load_component(label: str, series: str) -> pd.DataFrame:
    path = latest_vintage("world_bank_wdi", series)
    df = pd.read_parquet(path, columns=["country_iso3", "country_name", "year", "value"])
    df["country_iso3"] = df["country_iso3"].astype(str).str.strip()
    df = df[df["country_iso3"].str.fullmatch(r"[A-Z]{3}", na=False)].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["country_iso3", "year"])
    df["year"] = df["year"].astype(int)
    return df.rename(columns={"value": label})[["country_iso3", "country_name", "year", label]]


def build_panel() -> pd.DataFrame:
    frames = [load_component(label, series) for label, series in COMPONENTS.items()]
    out = frames[0]
    for frame in frames[1:]:
        out = out.merge(frame, on=["country_iso3", "country_name", "year"], how="outer")

    component_cols = list(COMPONENTS)
    out["components_observed"] = out[component_cols].notna().sum(axis=1)
    out = out[out["components_observed"] >= MIN_COMPONENTS].copy()
    if out.empty:
        raise RuntimeError("no rows with enough WDI export-share components")

    shares = out[component_cols].clip(lower=0.0, upper=100.0).fillna(0.0) / 100.0
    known_sum = shares.sum(axis=1)
    overfull = known_sum > 1.0
    shares.loc[overfull, component_cols] = shares.loc[overfull, component_cols].div(
        known_sum.loc[overfull],
        axis=0,
    )
    residual = (1.0 - shares.sum(axis=1)).clip(lower=0.0)
    hhi = shares.pow(2).sum(axis=1) + residual.pow(2)

    out["export_concentration_hhi_broad"] = hhi.astype(float)
    out["export_diversification_index"] = (1.0 - hhi).astype(float)
    out["share_other_residual"] = residual.astype(float)
    out["component_share_sum_raw"] = known_sum.astype(float)
    return out.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def write_series(
    *,
    series_id: str,
    frame: pd.DataFrame,
    value_col: str,
    fetch_ts: datetime,
    units: str,
) -> FetchResult:
    cols = ["country_iso3", "country_name", "year", value_col]
    out = frame[cols].rename(columns={value_col: "value"}).dropna(subset=["value"]).copy()
    path, digest = write_vintage(
        publisher="derived",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="derived",
        series_id=series_id,
        source_url="derived://world_bank_wdi:" + "+".join(COMPONENTS.values()),
        methodology_url="local://scripts/build_export_diversification_vintage.py",
        license="internal_derived_from_wdi_cc_by_4_0",
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(out["year"].min())) if not out.empty else None,
        end_date=str(int(out["year"].max())) if not out.empty else None,
        sha256=digest,
        parquet_path=path,
        extra={
            "recipe": (
                "clip WDI merchandise export shares to [0,100], divide by 100, "
                "renormalise rows whose observed broad shares exceed 100%, "
                "add residual other share, then compute HHI=sum(shares^2)"
            ),
            "components": COMPONENTS,
            "min_components": MIN_COMPONENTS,
        },
    )


def build(args: argparse.Namespace) -> list[FetchResult]:
    fetch_ts = (
        datetime.strptime(args.stamp, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if args.stamp
        else utc_now()
    )
    panel = build_panel()
    results = [
        write_series(
            series_id="export_diversification_index",
            frame=panel,
            value_col="export_diversification_index",
            fetch_ts=fetch_ts,
            units="1 - broad merchandise export-share HHI; higher means more diversified",
        ),
        write_series(
            series_id="export_concentration_hhi_broad",
            frame=panel,
            value_col="export_concentration_hhi_broad",
            fetch_ts=fetch_ts,
            units="broad merchandise export-share HHI; higher means more concentrated",
        ),
        write_series(
            series_id="export_share_other_residual",
            frame=panel,
            value_col="share_other_residual",
            fetch_ts=fetch_ts,
            units="residual merchandise export share after WDI broad categories",
        ),
    ]
    manifest = write_manifest(results, run_stamp=f"export_diversification_{utc_stamp(fetch_ts)}")
    summary = {
        "generated_at": fetch_ts.isoformat(),
        "manifest": str(manifest.relative_to(ROOT)),
        "rows": int(panel.shape[0]),
        "countries": int(panel["country_iso3"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "series_written": [r.series_id for r in results],
        "mean_diversification": float(np.nanmean(panel["export_diversification_index"])),
    }
    print(pd.Series(summary).to_string())
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp", help="UTC stamp to use, format YYYY-MM-DDTHHMMSSZ")
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
