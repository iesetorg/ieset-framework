#!/usr/bin/env python3
"""Build vintage parquets for the Soviet-collapse canonical-case hypothesis.

Reads manually compiled CSVs from data/manual/soviet_collapse/ and emits
tidy (country_iso3, year, value) parquet vintages under
data/vintages/<publisher>/<series>@<utc_stamp>.parquet, keyed against the
publishers and series referenced in
hypotheses/growth/soviet_union_central_planning_gdp_collapse_1989_1991.yaml.

The publisher/series keys mirror the hypothesis YAML's `source:` strings
so the multi-metric checklist runner picks them up via
`latest_vintage(publisher, series)`.

Per METHODOLOGY.md invariant #2 we mint a synthetic FetchResult/manifest
for each emission so provenance is preserved alongside the canonical
fetcher pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, write_manifest, write_vintage  # noqa: E402

MANUAL_DIR = ROOT / "data" / "manual" / "soviet_collapse"


def _read_csv(name: str) -> pd.DataFrame:
    p = MANUAL_DIR / name
    return pd.read_csv(p, comment="#")


def _emit(publisher: str, series: str, df: pd.DataFrame, source_note: str) -> FetchResult:
    fetch_ts = utc_now()
    if "country_iso3" not in df.columns:
        raise ValueError(f"{publisher}/{series}: missing country_iso3 column")
    if "value" not in df.columns:
        raise ValueError(f"{publisher}/{series}: missing value column")
    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out_path, sha = write_vintage(publisher=publisher, series_id=series, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher=publisher, series_id=series,
        source_url=f"manual://soviet_collapse/{source_note}",
        methodology_url="hypotheses/growth/soviet_union_central_planning_gdp_collapse_1989_1991.yaml",
        license="academic_citation",
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=str(df.get("unit", pd.Series(["?"])).iloc[0]) if "unit" in df.columns else "?",
        currency=None,
        start_date=str(int(df["year"].min())) if df["year"].notna().any() else None,
        end_date=str(int(df["year"].max())) if df["year"].notna().any() else None,
        sha256=sha,
        parquet_path=out_path,
        extra={"manual_drop_dir": str(MANUAL_DIR.relative_to(ROOT)), "source_note": source_note},
    )


def main() -> int:
    results: list[FetchResult] = []

    # --- Russian male life expectancy 1987-1999 (Rosstat / HMD / Brainerd-Cutler) ---
    le = _read_csv("rosstat_male_life_expectancy_rus_2026-04-24.csv")
    le_panel = le[["country_iso3", "year", "value"]].copy()
    # Hypothesis spec source: "who_gho:life_expectancy; human_mortality_database:RUS;
    #   rosstat:demographic_yearbook"
    # Emit under all three publisher namespaces so the runner picks any of them.
    results.append(_emit("rosstat", "demographic_yearbook", le_panel,
                        "Rosstat Demographic Yearbook of Russia (various editions 1995-2005) male LE 1987-1999"))
    results.append(_emit("human_mortality_database", "RUS", le_panel,
                        "Human Mortality Database (mortality.org) Russia data file male LE 1987-1999"))
    results.append(_emit("who_gho", "life_expectancy", le_panel,
                        "WHO HFA-DB cross-reference for HMD/Rosstat male LE 1987-1999"))

    # --- FSU -> OECD cumulative emigration 1989-1996 ---
    em = _read_csv("oecd_sopemi_fsu_emigration_1989_1996.csv")
    em_panel = em[["country_iso3", "year", "value"]].copy()
    # Hypothesis spec source: "un_desa:international_migrant_stock; oecd:sopemi;
    #   israel_cbs:immigration_statistics; destatis_germany:aussiedler_statistics"
    results.append(_emit("oecd", "sopemi", em_panel,
                        "OECD SOPEMI 'Trends in International Migration' annual reports 1992-2000"))
    results.append(_emit("un_desa", "international_migrant_stock", em_panel,
                        "UN DESA International Migrant Stock — FSU emigration cumulative to OECD"))
    results.append(_emit("israel_cbs", "immigration_statistics", em_panel,
                        "Israeli CBS Statistical Abstract of Israel — aliyah from former-USSR"))
    results.append(_emit("destatis_germany", "aussiedler_statistics", em_panel,
                        "Destatis / Bundesverwaltungsamt Aussiedler arrivals 1989-1996"))

    # --- Currency regime events 1989-1998 (Aslund / IMF AIV / decrees) ---
    cu = _read_csv("cbr_currency_regime_events_1989_1998.csv")
    cu_panel = cu[["country_iso3", "year", "value"]].copy()
    # Hypothesis spec source: "cbr:official_decrees; imf:article_iv_consultation_rus;
    #   academic:aslund_building_capitalism"
    results.append(_emit("cbr", "official_decrees", cu_panel,
                        "USSR/RF currency-regime decrees: Pavlov 1991, redenomination 1997/98, default Aug 1998"))
    results.append(_emit("imf", "article_iv_consultation_rus", cu_panel,
                        "IMF Article IV consultation Russian Federation staff reports 1992-1999"))

    manifest_path = write_manifest(results, run_stamp=None)
    print(f"OK — wrote {len(results)} vintages.")
    for r in results:
        print(f"  {r.publisher:<24s} {r.series_id:<40s} rows={r.rows:>3d} "
              f"sha={r.sha256[:8]} {r.parquet_path.relative_to(ROOT)}")
    print(f"manifest: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
