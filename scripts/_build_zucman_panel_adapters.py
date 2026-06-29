#!/usr/bin/env python3
"""Adapter: bridge the data-layer agent's derived Zucman panels into vintages
the hypothesis runner can load.

The runner (run_panel_fe.load_variable / normalise_panel) reads
data/vintages/<publisher>/<series>@<utc>.parquet projected onto
(country_iso3, year, value). The data-layer agent's panels live in
data/derived/*.parquet as long format with a series_id column, so they need
to be sliced per-series. This script materialises those slices.

Source of truth = data/derived/* (owned by the data-layer agent). For the WID
wealth-share series we splice in deep pre-1980 history from the raw WID dump
(identical at the 1980 boundary — verified) so the FRA-1982 ISF event has a
pre-period; their panel alone starts in 1980.

Outputs:
  data/vintages/wid_concentration/{top1,top01,top10}_net_personal_wealth_share
  data/vintages/wid_concentration/net_personal_wealth_income_ratio
  data/vintages/oecd_taxstruct/combined_corporate_income_tax_rate
  data/vintages/oecd_taxstruct/recurrent_net_wealth_pct_gdp
"""
from __future__ import annotations

import glob
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")

ALPHA2_TO_ISO3 = {
    "FR": "FRA", "DE": "DEU", "IT": "ITA", "ES": "ESP", "NL": "NLD",
    "BE": "BEL", "AT": "AUT", "PT": "PRT", "FI": "FIN", "CH": "CHE",
    "NO": "NOR", "SE": "SWE", "DK": "DNK", "GB": "GBR", "US": "USA",
}
WID_PCTILE = {
    "top1_net_personal_wealth_share": "p99p100",
    "top01_net_personal_wealth_share": "p99.9p100",
    "top10_net_personal_wealth_share": "p90p100",
}


def write_vintage(df: pd.DataFrame, publisher: str, series: str) -> None:
    out = ROOT / "data/vintages" / publisher
    out.mkdir(parents=True, exist_ok=True)
    df = (df.dropna(subset=["country_iso3", "year", "value"])
            .groupby(["country_iso3", "year"], as_index=False)["value"].mean()
            .sort_values(["country_iso3", "year"]))
    df["year"] = df["year"].astype(int)
    path = out / f"{series}@{STAMP}.parquet"
    df.to_parquet(path, index=False)
    print(f"  {publisher}:{series} -> {len(df)} rows, "
          f"{df['country_iso3'].nunique()} ctys, {int(df.year.min())}-{int(df.year.max())}")


def main() -> None:
    # --- WID wealth concentration (their panel 1980+, spliced w/ raw WID pre-1980)
    their = pd.read_parquet(ROOT / "data/derived/wid_wealth_concentration_panel.parquet")
    raw = pd.read_parquet(
        sorted(glob.glob(str(ROOT / "data/vintages/wid/wid_all@*.parquet")))[-1],
        columns=["country", "variable", "percentile", "year", "value"],
    )
    raw = raw[raw["variable"] == "shwealj992"]

    print("WID wealth-concentration adapter:")
    for series, pctile in WID_PCTILE.items():
        canon = their[their["series_id"] == series][["country_iso3", "year", "value"]].copy()
        deep = raw[(raw["percentile"] == pctile)].copy()
        deep["country_iso3"] = deep["country"].map(ALPHA2_TO_ISO3)
        deep = deep.dropna(subset=["country_iso3"])
        deep["value"] = deep["value"] * 100.0
        deep = deep[deep["year"] < canon["year"].min()][["country_iso3", "year", "value"]]
        write_vintage(pd.concat([canon, deep], ignore_index=True),
                      "wid_concentration", series)

    ratio = their[their["series_id"] == "net_personal_wealth_income_ratio"][
        ["country_iso3", "year", "value"]]
    write_vintage(ratio, "wid_concentration", "net_personal_wealth_income_ratio")

    # --- OECD tax structure (corporate rate covers the full race-to-bottom era)
    oecd = pd.read_parquet(ROOT / "data/derived/oecd_tax_structure_panel.parquet")
    print("OECD tax-structure adapter:")
    for series_id, out_series in [
        ("oecd_combined_corporate_income_tax_rate", "combined_corporate_income_tax_rate"),
        ("oecd_tax_recurrent_net_wealth_pct_gdp", "recurrent_net_wealth_pct_gdp"),
        ("oecd_tax_estate_inheritance_gift_pct_gdp", "estate_inheritance_gift_pct_gdp"),
    ]:
        slc = oecd[oecd["series_id"] == series_id][["country_iso3", "year", "value"]]
        write_vintage(slc, "oecd_taxstruct", out_series)


if __name__ == "__main__":
    main()
