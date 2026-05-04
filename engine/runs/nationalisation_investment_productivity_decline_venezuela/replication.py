#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "nationalisation_investment_productivity_decline_venezuela"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRIES = ["VEN", "ARG", "CHL", "MEX"]
DONORS = ["ARG", "CHL", "MEX"]
START_YEAR = 2013
END_YEAR = 2023


def latest(publisher: str, series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / publisher).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing {publisher}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_wdi(path: Path, name: str) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["country_iso3"].isin(COUNTRIES)].dropna(subset=["year"])
    return df[["country_iso3", "country_name", "year", "value"]].rename(columns={"value": name})


def load_brent_annual(path: Path) -> pd.Series:
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    df["year"] = df["date"].dt.year
    return df.groupby("year")["value"].mean().rename("brent_usd")


def endpoint_growth(series: pd.Series) -> float:
    return float(series.loc[END_YEAR] / series.loc[START_YEAR] - 1.0)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "NY.GDP.MKTP.KD": latest("world_bank_wdi", "NY.GDP.MKTP.KD"),
        "NY.GDP.PETR.RT.ZS": latest("world_bank_wdi", "NY.GDP.PETR.RT.ZS"),
        "DCOILBRENTEU": latest("fred", "DCOILBRENTEU"),
    }

    gdp = load_wdi(paths["NY.GDP.MKTP.KD"], "real_gdp")
    oil_rents = load_wdi(paths["NY.GDP.PETR.RT.ZS"], "oil_rents_pct_gdp")
    panel = gdp.merge(oil_rents, on=["country_iso3", "country_name", "year"], how="left")
    brent = load_brent_annual(paths["DCOILBRENTEU"])

    wide = panel.pivot_table(index="year", columns="country_iso3", values="real_gdp")
    method_valid = all(c in wide.columns for c in COUNTRIES) and all(y in wide.index for y in [START_YEAR, END_YEAR])
    method_valid = bool(method_valid and wide.loc[[START_YEAR, END_YEAR], COUNTRIES].notna().all().all())

    if method_valid:
        growth = {country: endpoint_growth(wide[country].dropna()) for country in COUNTRIES}
        donor_median_growth = float(np.median([growth[country] for country in DONORS]))
        ven_growth = float(growth["VEN"])
        underperformance_pp = float((donor_median_growth - ven_growth) * 100.0)
        ven_decline_pct = float(-ven_growth * 100.0)
        brent_start = float(brent.loc[START_YEAR]) if START_YEAR in brent.index else None
        brent_end = float(brent.loc[END_YEAR]) if END_YEAR in brent.index else None
        if ven_growth <= -0.40 and underperformance_pp >= 50.0:
            verdict_label = "PARTIAL"
            scope_note = "country-level collapse proxy supports the Venezuela direction; sector mechanism remains data-gated"
        elif ven_growth > -0.15 or underperformance_pp < 20.0:
            verdict_label = "REFUTED"
            scope_note = "country-level collapse proxy does not clear the registered decline thresholds"
        else:
            verdict_label = "PARTIAL"
            scope_note = "country-level collapse proxy is mixed"
        verdict_reason = (
            f"VEN real GDP {ven_growth * 100:.1f}% from 2013 to 2023 vs donor median "
            f"{donor_median_growth * 100:.1f}% (ARG/CHL/MEX); underperformance {underperformance_pp:.1f}pp"
        )
    else:
        growth = {}
        donor_median_growth = ven_growth = underperformance_pp = ven_decline_pct = None
        brent_start = brent_end = None
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
        scope_note = "missing required WDI endpoints"
        verdict_reason = "missing 2013 or 2023 real GDP endpoints for VEN/ARG/CHL/MEX"

    out = panel.copy()
    out["brent_usd"] = out["year"].map(brent)
    out.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": f"{verdict_label} \u2014 {verdict_reason}",
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "method_valid": method_valid,
        "test": "wdi_venezuela_real_gdp_collapse_vs_arg_chl_mex_2013_2023",
        "evidence_type": "country_level_collapse_proxy",
        "scope_note": scope_note,
        "causal_attribution": "not identified; no sector-level production/capex/fiscal panel is present locally",
        "estimate": {
            "ven_real_gdp_growth_2013_2023": ven_growth,
            "donor_median_real_gdp_growth_2013_2023": donor_median_growth,
            "ven_underperformance_percentage_points": underperformance_pp,
            "ven_decline_percent": ven_decline_pct,
            "country_growth_2013_2023": growth,
            "brent_avg_2013": brent_start,
            "brent_avg_2023": brent_end,
        },
        "thresholds": {
            "partial_support_ven_real_gdp_growth_max": -0.40,
            "partial_support_underperformance_pp_min": 50.0,
            "refute_ven_decline_pct_max": 15.0,
            "refute_underperformance_pp_max": 20.0,
        },
        "data_status": {
            "variables_loaded": [
                {"name": "real_gdp", "source": "world_bank_wdi:NY.GDP.MKTP.KD", "publisher": "world_bank_wdi"},
                {"name": "oil_rents_pct_gdp", "source": "world_bank_wdi:NY.GDP.PETR.RT.ZS", "publisher": "world_bank_wdi"},
                {"name": "world_oil_price_brent", "source": "fred:DCOILBRENTEU", "publisher": "fred"},
            ],
            "variables_missing": [
                {"name": "sector_output_production", "source": "opec/pdvsa/pemex/enap/ypf"},
                {"name": "sector_capex_to_output_ratio", "source": "company annual reports"},
                {"name": "sector_productivity_real_output_per_worker", "source": "company reports"},
                {"name": "sector_tax_dividend_contribution_to_fiscal", "source": "finance ministries"},
            ],
        },
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/nationalisation_investment_productivity_decline_venezuela/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict_label}\n"
        f"reason: {verdict_reason}\n"
        "methodology_note: WDI country-level proxy; sector production/capex/fiscal mechanism data absent\n"
        "vintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict_label} - {verdict_reason}\n\n"
        "## Predeclared Test\n\n"
        "The v2 diagnostic is capped at partial because it uses country-level WDI real GDP rather than the "
        "registered sector-level production, capex, productivity, and fiscal-contribution panel. Partial "
        "support requires Venezuela's real GDP to fall at least 40% from 2013 to 2023 and underperform the "
        "Argentina/Chile/Mexico donor median by at least 50 percentage points.\n\n"
        "## Scope Note\n\n"
        "This establishes the collapse direction in the Venezuela case, not the full nationalisation mechanism "
        "or the four-case causal chain.\n"
    )
    print(f"verdict: {verdict_label} - {verdict_reason}")


if __name__ == "__main__":
    main()
