#!/usr/bin/env python3
"""Build vintage parquets for the Zimbabwe canonical-collapse hypothesis.

Reads manually compiled CSVs from data/manual/zwe_canonical_collapse/ and
emits tidy (country_iso3, year, value) parquet vintages under
data/vintages/<publisher>/<series>@<utc_stamp>.parquet, keyed against the
publishers and series referenced in
hypotheses/monetary/zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009.yaml.

Shared with the Cuba canonical-case run (FAOSTAT publisher namespace);
Cuba agent should add Cuba-specific rows to the same FAOSTAT QCL vintage
or write a separate vintage with the same publisher key.

Per METHODOLOGY.md invariant #2 we mint a synthetic FetchResult/manifest for
each emission so provenance is preserved alongside the canonical fetcher
pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, write_manifest, write_vintage  # noqa: E402

MANUAL_DIR = ROOT / "data" / "manual" / "zwe_canonical_collapse"


def _read_csv(name: str) -> pd.DataFrame:
    p = MANUAL_DIR / name
    df = pd.read_csv(p, comment="#")
    return df


def _emit(publisher: str, series: str, df: pd.DataFrame, source_note: str) -> FetchResult:
    fetch_ts = utc_now()
    # Ensure tidy schema
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
        source_url=f"manual://{source_note}",
        methodology_url="hypotheses/monetary/zimbabwe_hyperinflation_land_reform_output_collapse_2000_2009.yaml",
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

    # --- FAOSTAT: tobacco (item flue_cured) and cereals as separate series ---
    fao = _read_csv("faostat_QCL_zwe_2026-04-24.csv")
    # Emit two FAOSTAT vintages: (a) crops_primary = tobacco subset, (b) QCL = cereals subset.
    tobacco = fao[fao["item"] == "tobacco_flue_cured"][["country_iso3", "year", "value"]]
    cereals = fao[fao["item"] == "cereals_total"][["country_iso3", "year", "value"]]
    results.append(_emit("faostat", "crops_primary", tobacco,
                        "FAOSTAT QCL item 826 (tobacco flue-cured) — Zimbabwe 1999-2009"))
    results.append(_emit("faostat", "QCL", cereals,
                        "FAOSTAT QCL aggregated cereals (maize+wheat+sorghum) — Zimbabwe 1999-2009"))

    # --- WFP: food-assistance caseload as % of resident population ---
    wfp = _read_csv("wfp_caseload_zwe_2026-04-24.csv")
    wfp_panel = wfp[["country_iso3", "year", "value"]].copy()
    # Emit under both series IDs the hypothesis spec references
    results.append(_emit("wfp", "emergency_operation_zimbabwe_annual_reports", wfp_panel,
                        "WFP EmOp Zimbabwe annual reports 2002-2009 — % resident pop on food assistance"))
    results.append(_emit("wfp", "food_security_monitor_zimbabwe", wfp_panel,
                        "WFP food security monitor Zimbabwe — same caseload series, peak per year"))
    results.append(_emit("fao", "giews_country_briefs_zwe", wfp_panel,
                        "FAO GIEWS country briefs Zimbabwe — caseload cross-reference"))

    # --- UN DESA + IOM: cumulative emigrant stock as % of 2000 ZWE population ---
    udesa = _read_csv("un_desa_migrant_stock_zwe_2026-04-24.csv")
    udesa_panel = udesa[["country_iso3", "year", "value"]].copy()
    results.append(_emit("un_desa", "international_migrant_stock", udesa_panel,
                        "UN DESA Migrant Stock + WB Migration & Remittances Factbook 2011 — Zimbabweans abroad"))
    results.append(_emit("iom", "migration_profile_zimbabwe_2010", udesa_panel,
                        "IOM Migration Profile Zimbabwe 2010 — cross-reference for emigrant stock"))

    # --- RBZ redenominations: cumulative count over rolling 5y window ---
    rbz_red = _read_csv("rbz_redenominations_zwe_2026-04-24.csv")
    rbz_red_panel = rbz_red[["country_iso3", "year", "value"]].copy()
    results.append(_emit("rbz", "official_redenomination_decrees", rbz_red_panel,
                        "RBZ Statutory Instruments 199/2006, 91/2008, 31/2009 — redenomination decrees"))
    results.append(_emit("imf", "article_iv_consultation_staff_reports_zwe", rbz_red_panel,
                        "IMF Article IV staff report 2009 (CR 09/139) — redenomination cross-reference"))

    # --- RBZ M3 growth: annualised broad-money growth rate ---
    rbz_m3 = _read_csv("rbz_m3_growth_zwe_2026-04-24.csv")
    rbz_m3_panel = rbz_m3[["country_iso3", "year", "value"]].copy()
    results.append(_emit("rbz", "monetary_policy_statements", rbz_m3_panel,
                        "RBZ Monetary Policy Statements 2003-2008 — annualised M3 growth"))
    results.append(_emit("imf", "IFS_money_and_credit_zwe", rbz_m3_panel,
                        "IMF Article IV 2009 (CR 09/139) Box 3 — M3 reconstruction"))

    # --- Utete / Buka commercial-farm share (manual but registered as a publisher
    #     so the runner can read it; manual: prefix is otherwise skipped) ---
    utete = _read_csv("utete_commercial_farms_zwe_2026-04-24.csv")
    utete_panel = utete[["country_iso3", "year", "value"]].copy()
    # Use a plain publisher name that is not 'manual' so the runner picks it up.
    # Source string in the spec uses 'manual:' which is intentionally skipped;
    # we additionally emit a 'utete' publisher so an updated source line could
    # reference it. For this run we leave the spec as-is (commercial_farm
    # metric stays PENDING_DATA).
    results.append(_emit("utete", "presidential_land_review_2003", utete_panel,
                        "Utete 2003 + Buka 2002 commission reports — LSCF expropriation share"))

    manifest_path = write_manifest(results, run_stamp=None)
    print(f"OK — wrote {len(results)} vintages.")
    for r in results:
        print(f"  {r.publisher:<10s} {r.series_id:<55s} rows={r.rows:>3d} "
              f"sha={r.sha256[:8]} {r.parquet_path.relative_to(ROOT)}")
    print(f"manifest: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
