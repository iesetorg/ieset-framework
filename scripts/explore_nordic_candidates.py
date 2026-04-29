#!/usr/bin/env python3
"""Ask-the-data: what candidate factors might explain the Nordic GDP residual?

For every on-disk series with a country-year shape, compute:
  - Nordic-5 vs Southern-Europe-4 mean gap over 1996-2023
  - Correlation with log GDP per capita PPP within the 10-country sample
  - Data coverage on the sample

Rank by |discriminant| * |gdp_correlation| * coverage → candidate channels
the v1 spec missed.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[1]
VINTAGE_ROOT = REPO_ROOT / "data" / "vintages"

NORDIC = {"NOR", "SWE", "DNK", "FIN", "ISL"}
SE = {"ESP", "ITA", "GRC", "PRT"}
SAMPLE = sorted(NORDIC | SE | {"FRA"})
PERIOD = (1996, 2023)


def latest_vintages() -> dict[str, list[Path]]:
    by_pub: dict[str, list[Path]] = {}
    for pub_dir in sorted(VINTAGE_ROOT.iterdir()):
        if not pub_dir.is_dir():
            continue
        seen: dict[str, Path] = {}
        for p in sorted(pub_dir.glob("*.parquet")):
            series = p.name.split("@")[0]
            if series not in seen or p.stat().st_mtime > seen[series].stat().st_mtime:
                seen[series] = p
        by_pub[pub_dir.name] = list(seen.values())
    return by_pub


def extract_country_year(path: Path) -> pd.DataFrame | None:
    """Best-effort extraction of (country_iso3, year, variable, value) long format."""
    try:
        df = pq.read_table(path).to_pandas()
    except Exception:
        return None
    cols = {c.lower(): c for c in df.columns}
    # Standard WDI/WGI/IMF shape
    if "country_iso3" in cols and "year" in cols and "value" in cols:
        out = df[[cols["country_iso3"], cols["year"], cols["value"]]].copy()
        out.columns = ["country", "year", "value"]
        out["series"] = path.name.split("@")[0]
    # V-Dem shape (country_text_id + year + dozens of indicators)
    elif "country_text_id" in cols and "year" in cols:
        iso = df[cols["country_text_id"]]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if cols["year"] in numeric_cols:
            numeric_cols.remove(cols["year"])
        if not numeric_cols:
            return None
        # melt top ~40 numeric indicators to long
        to_melt = numeric_cols[:40]
        long = df[[cols["country_text_id"], cols["year"]] + to_melt].melt(
            id_vars=[cols["country_text_id"], cols["year"]],
            value_vars=to_melt,
            var_name="series",
            value_name="value",
        )
        long.columns = ["country", "year", "series", "value"]
        out = long
        out["series"] = path.name.split("@")[0] + ":" + out["series"].astype(str)
    # JST shape (iso2/iso3 + year + many macro vars)
    elif "iso" in cols and "year" in cols:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if cols["year"] in numeric_cols:
            numeric_cols.remove(cols["year"])
        to_melt = numeric_cols
        if not to_melt:
            return None
        long = df[[cols["iso"], cols["year"]] + to_melt].melt(
            id_vars=[cols["iso"], cols["year"]],
            value_vars=to_melt,
            var_name="series",
            value_name="value",
        )
        long.columns = ["country", "year", "series", "value"]
        out = long
        out["series"] = path.name.split("@")[0] + ":" + out["series"].astype(str)
    # OECD PMR / OECD shape (OBS_VALUE + REF_AREA + TIME_PERIOD)
    elif any("REF_AREA" in c for c in df.columns):
        col_map = {c.upper(): c for c in df.columns}
        if "REF_AREA" not in col_map or "OBS_VALUE" not in col_map:
            return None
        time_col = col_map.get("TIME_PERIOD") or col_map.get("TIME")
        if not time_col:
            return None
        out = df[[col_map["REF_AREA"], time_col, col_map["OBS_VALUE"]]].copy()
        out.columns = ["country", "year", "value"]
        out["series"] = path.name.split("@")[0]
    # Polity5 shape
    elif "scode" in cols and "year" in cols:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if cols["year"] in numeric_cols:
            numeric_cols.remove(cols["year"])
        to_melt = [c for c in ("polity2", "polity", "democ", "autoc", "xconst", "parcomp") if c in cols]
        if not to_melt:
            return None
        long = df[[cols["scode"], cols["year"]] + to_melt].melt(
            id_vars=[cols["scode"], cols["year"]],
            value_vars=to_melt,
            var_name="series",
            value_name="value",
        )
        long.columns = ["country", "year", "series", "value"]
        long["series"] = "polity5:" + long["series"]
        out = long
    else:
        return None

    # Coerce
    out["country"] = out["country"].astype(str).str.strip()
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["country", "year", "value"])
    out = out[(out["year"] >= PERIOD[0]) & (out["year"] <= PERIOD[1])]
    out = out[out["country"].str.len() == 3]  # ISO3 only
    out = out[out["country"].isin(SAMPLE)]
    return out


def main() -> int:
    vintages = latest_vintages()

    # Reference outcome — log GDP per capita PPP from WDI
    gdp_path = next((p for p in vintages["world_bank_wdi"] if p.name.startswith("NY.GDP.PCAP.PP.KD@")), None)
    if gdp_path is None:
        print("ERROR: no WDI NY.GDP.PCAP.PP.KD", file=__import__("sys").stderr)
        return 2
    gdp = extract_country_year(gdp_path).rename(columns={"value": "gdp"}).drop(columns=["series"])
    gdp["log_gdp"] = np.log(gdp["gdp"])
    gdp = gdp[["country", "year", "log_gdp"]]

    rows: list[dict] = []
    for pub, paths in vintages.items():
        if pub in ("shiller", "bls"):  # US-only
            continue
        for path in paths:
            series_root = path.name.split("@")[0]
            df = extract_country_year(path)
            if df is None or df.empty:
                continue
            for series, sub in df.groupby("series"):
                sub = sub[["country", "year", "value"]].drop_duplicates(["country", "year"])
                merged = sub.merge(gdp, on=["country", "year"], how="inner")
                if len(merged) < 30:
                    continue
                merged["nordic"] = merged["country"].isin(NORDIC)
                n_mean = merged.loc[merged["nordic"], "value"].mean()
                s_mean = merged.loc[(~merged["nordic"]) & (merged["country"].isin(SE)), "value"].mean()
                if pd.isna(n_mean) or pd.isna(s_mean):
                    continue
                gap = n_mean - s_mean
                # Normalise gap by SD of series over sample for comparability
                s_std = merged["value"].std()
                gap_z = gap / s_std if s_std and not np.isnan(s_std) else 0.0
                # Correlation with log GDP
                try:
                    corr = merged[["value", "log_gdp"]].corr().iloc[0, 1]
                except Exception:
                    corr = 0.0
                if pd.isna(corr):
                    corr = 0.0
                # Coverage = min countries × years we see the series for
                coverage = len(merged) / (len(SAMPLE) * (PERIOD[1] - PERIOD[0] + 1))
                rows.append({
                    "publisher": pub,
                    "series": series,
                    "n_obs": len(merged),
                    "coverage": round(coverage, 2),
                    "nordic_mean": round(n_mean, 3),
                    "se_mean": round(s_mean, 3),
                    "gap_raw": round(gap, 3),
                    "gap_z": round(gap_z, 2),
                    "corr_with_log_gdp": round(corr, 2),
                    "score": round(abs(gap_z) * abs(corr) * coverage, 3),
                })

    res = pd.DataFrame(rows).sort_values("score", ascending=False)

    # Strip v1 channels so we surface things NOT in the original spec
    v1_channels = {"NY.GDP.PCAP.PP.KD", "SI.POV.GINI", "SL.UEM.TOTL.ZS",
                   "GC.DOD.TOTL.GD.ZS", "GGXWDG_NGDP", "SP.POP.TOTL",
                   "SP.URB.TOTL.IN.ZS", "GOV_WGI_GE.EST", "GOV_WGI_RL.EST"}
    res["in_v1"] = res["series"].apply(lambda s: any(k in s for k in v1_channels))
    novel = res[~res["in_v1"]].copy()

    print("=" * 100)
    print("TOP 30 CANDIDATE MISSING CHANNELS (not in v1), ranked by |gap_z| * |corr_with_log_gdp| * coverage")
    print("=" * 100)
    print(novel.head(30)[["publisher", "series", "coverage", "gap_z", "corr_with_log_gdp", "score"]].to_string(index=False))
    print()
    print(f"Total candidate series examined: {len(res)}  (novel = {len(novel)})")

    out_path = REPO_ROOT / "engine" / "runs" / "nordic_outcome_persistence_decomposition" / "exploratory_candidates.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)
    print(f"Full ranking written to {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
