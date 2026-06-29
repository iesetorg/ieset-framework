#!/usr/bin/env python3
"""Build dense top-wealth-share vintages from the raw WID.world dump.

The OWID wealth mirrors (owid:top-N-share-of-total-wealth) only start in
1980, which starves pre-1980 policy events (e.g. France's 1982 ISF
introduction) of a usable pre-period and collapses synthetic-control donor
pools. The raw WID dump (data/vintages/wid/wid_all@*.parquet) carries
net-personal-wealth shares back to ~1800 for the same countries.

This script projects the canonical Saez/Zucman/WID net-personal-wealth share
series (variable shwealj992 = share, equal-split adults) for the top 1%,
top 0.1%, and top 10% onto the generic (country_iso3, year, value) schema
that scripts/run_panel_fe.py:normalise_panel expects. Values are scaled to
percentage points (×100) to match the OWID convention, so existing
falsification thresholds expressed in "percentage points" carry over.

Output: data/vintages/wid_clean/<series>@<utc>.parquet
  series ∈ {top1_wealth_share, top01_wealth_share, top10_wealth_share}

Publisher namespace `wid_clean` is deliberately NOT a meta-prefix, so
load_variable() resolves it through the normal vintage path.
"""
from __future__ import annotations

import glob
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data/vintages/wid_clean"

# WID alpha2 -> ISO3 for the countries used in wealth-tax hypotheses + donor pools.
ALPHA2_TO_ISO3 = {
    "FR": "FRA", "DE": "DEU", "IT": "ITA", "ES": "ESP", "NL": "NLD",
    "BE": "BEL", "AT": "AUT", "PT": "PRT", "FI": "FIN", "CH": "CHE",
    "NO": "NOR", "SE": "SWE", "DK": "DNK", "GB": "GBR", "IE": "IRL",
    "US": "USA", "CA": "CAN", "CO": "COL", "CL": "CHL", "MX": "MEX",
    "BR": "BRA", "AR": "ARG", "PE": "PER", "UY": "URY", "JP": "JPN",
    "AU": "AUS", "NZ": "NZL", "GR": "GRC", "PL": "POL", "CZ": "CZE",
}

SERIES = {
    "top1_wealth_share": "p99p100",
    "top01_wealth_share": "p99.9p100",
    "top10_wealth_share": "p90p100",
}
WID_VARIABLE = "shwealj992"  # net personal wealth share, equal-split adults


def main() -> None:
    src = sorted(glob.glob(str(ROOT / "data/vintages/wid/wid_all@*.parquet")))[-1]
    print(f"source: {src}")
    df = pd.read_parquet(src, columns=["country", "variable", "percentile", "year", "value"])
    df = df[df["variable"] == WID_VARIABLE]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

    for series, pctile in SERIES.items():
        sub = df[df["percentile"] == pctile].copy()
        sub["country_iso3"] = sub["country"].map(ALPHA2_TO_ISO3)
        sub = sub.dropna(subset=["country_iso3", "year", "value"])
        sub["year"] = pd.to_numeric(sub["year"], errors="coerce").astype("Int64")
        sub["value"] = pd.to_numeric(sub["value"], errors="coerce") * 100.0  # share -> pp
        out = (
            sub.groupby(["country_iso3", "year"], as_index=False)["value"]
            .mean()
            .dropna()
            .sort_values(["country_iso3", "year"])
            .reset_index(drop=True)
        )
        path = OUT_DIR / f"{series}@{stamp}.parquet"
        out.to_parquet(path, index=False)
        cov = out.groupby("country_iso3")["year"].agg(["min", "max", "count"])
        keep = [c for c in ["FRA", "NOR", "ESP", "COL", "CHE", "SWE", "DEU"] if c in cov.index]
        print(f"\n{series}: {len(out)} rows, {out['country_iso3'].nunique()} countries -> {path.name}")
        print(cov.loc[keep].to_string())


if __name__ == "__main__":
    main()
