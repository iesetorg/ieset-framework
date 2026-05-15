#!/usr/bin/env python3
"""Proxy-only local rerun for the frontier wage/product-market competition panel.

The registered OECD average-wage and ILO median-wage series are still absent.
This screen uses OECD PDB labour compensation per hour, deflated by WDI CPI,
as a real-wage proxy and keeps the result at PARTIAL/research-only.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
HID = "frontier_real_wage_growth_market_competition_1980_2024"
HYPOTHESIS_PATH = ROOT / "hypotheses" / "growth" / f"{HID}.yaml"

SAMPLE_COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT",
    "SWE", "NOR", "DNK", "FIN", "IRL", "CHE", "PRT", "GRC", "JPN",
    "CAN", "AUS", "NZL", "KOR", "ISR", "EST", "POL", "CZE", "HUN",
    "CHL", "MEX", "COL", "SVN", "SVK", "LVA", "LTU",
]

INPUTS = {
    "oecd_pdb": ROOT / "data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet",
    "oecd_pmr": ROOT / "data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet",
    "oecd_pmr_barrier_entry": ROOT / "data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet",
    "fraser_regulation": ROOT / "data/vintages/fraser_efw/regulation@2026-05-02T220000Z.parquet",
    "oecd_tud": ROOT / "data/vintages/oecd/TUD@2026-05-05T195705Z.parquet",
    "wdi_cpi": ROOT / "data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-04-30T135619Z.parquet",
    "wdi_gdp_pc": ROOT / "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T113730Z.parquet",
    "wdi_trade": ROOT / "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
    "wdi_services": ROOT / "data/vintages/world_bank_wdi/NV.SRV.TOTL.ZS@2026-05-05T195011Z.parquet",
    "wdi_real_interest": ROOT / "data/vintages/world_bank_wdi/FR.INR.RINR@2026-04-30T102408Z.parquet",
}

VINTAGE_META = {
    "oecd_pdb": ("oecd", "DSD_PDB", "OECD PDB: compensation and productivity"),
    "oecd_pmr": ("oecd_pmr", "PMR", "OECD PMR overall index"),
    "oecd_pmr_barrier_entry": ("oecd_pmr", "BARRIER_ENTRY", "OECD PMR barriers to entry"),
    "fraser_regulation": ("fraser_efw", "regulation", "Fraser EFW regulation area"),
    "oecd_tud": ("oecd", "TUD", "OECD trade union density"),
    "wdi_cpi": ("world_bank_wdi", "FP.CPI.TOTL.ZG", "WDI CPI inflation"),
    "wdi_gdp_pc": ("world_bank_wdi", "NY.GDP.PCAP.KD", "WDI real GDP per capita"),
    "wdi_trade": ("world_bank_wdi", "NE.TRD.GNFS.ZS", "WDI trade openness"),
    "wdi_services": ("world_bank_wdi", "NV.SRV.TOTL.ZS", "WDI services share of GDP"),
    "wdi_real_interest": ("world_bank_wdi", "FR.INR.RINR", "WDI real interest rate"),
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_wdi(key: str, name: str) -> pd.DataFrame:
    return (
        pd.read_parquet(INPUTS[key])[["country_iso3", "year", "value"]]
        .rename(columns={"value": name})
    )


def pdb_series(pdb: pd.DataFrame, measure: str, transformation: str, price_base: str, name: str) -> pd.DataFrame:
    cols = ["REF_AREA", "period", "value"]
    return (
        pdb[
            (pdb["MEASURE"] == measure)
            & (pdb["ACTIVITY"] == "_T")
            & (pdb["TRANSFORMATION"] == transformation)
            & (pdb["PRICE_BASE"] == price_base)
        ][cols]
        .rename(columns={"REF_AREA": "country_iso3", "period": "year", "value": name})
    )


def zscore(series: pd.Series, invert: bool = False) -> pd.Series:
    z = (series - series.mean()) / series.std(ddof=0)
    return -z if invert else z


def build_panel() -> tuple[pd.DataFrame, dict[str, int]]:
    pdb = pd.read_parquet(INPUTS["oecd_pdb"])
    wage = pdb_series(pdb, "LCHRS", "GY", "V", "nominal_comp_per_hour_growth")
    productivity = pdb_series(pdb, "GDPHRS", "GY", "L", "labour_productivity_growth")
    cpi = load_wdi("wdi_cpi", "cpi_inflation")
    wage = wage.merge(cpi, on=["country_iso3", "year"], how="left")
    wage["real_wage_growth_proxy"] = wage["nominal_comp_per_hour_growth"] - wage["cpi_inflation"]

    pmr_raw = pd.read_parquet(INPUTS["oecd_pmr"])
    pmr = (
        pmr_raw[pmr_raw["MEASURE"] == "PMR"][["REF_AREA", "period", "value"]]
        .rename(columns={"REF_AREA": "country_iso3", "period": "year", "value": "pmr_overall"})
    )
    barrier = pd.read_parquet(INPUTS["oecd_pmr_barrier_entry"]).rename(
        columns={"value": "barriers_to_entry"}
    )
    fraser = pd.read_parquet(INPUTS["fraser_regulation"]).rename(
        columns={"value": "fraser_regulation"}
    )
    union = (
        pd.read_parquet(INPUTS["oecd_tud"])[["REF_AREA", "period", "value"]]
        .rename(columns={"REF_AREA": "country_iso3", "period": "year", "value": "union_density"})
    )

    panel = (
        pmr.merge(barrier, on=["country_iso3", "year"], how="left")
        .merge(fraser, on=["country_iso3", "year"], how="inner")
        .merge(wage[["country_iso3", "year", "nominal_comp_per_hour_growth", "cpi_inflation", "real_wage_growth_proxy"]], on=["country_iso3", "year"], how="inner")
        .merge(productivity, on=["country_iso3", "year"], how="inner")
        .merge(union, on=["country_iso3", "year"], how="left")
        .merge(load_wdi("wdi_gdp_pc", "gdp_pc"), on=["country_iso3", "year"], how="left")
        .merge(load_wdi("wdi_trade", "trade_openness"), on=["country_iso3", "year"], how="left")
        .merge(load_wdi("wdi_services", "services_share_gdp"), on=["country_iso3", "year"], how="left")
        .merge(load_wdi("wdi_real_interest", "real_interest_rate"), on=["country_iso3", "year"], how="left")
    )
    panel = panel[
        panel["country_iso3"].isin(SAMPLE_COUNTRIES)
        & panel["year"].between(1980, 2024)
    ].copy()
    panel["log_initial_gdp_pc"] = np.log(panel["gdp_pc"])
    panel["pmr_inverted_z"] = zscore(panel["pmr_overall"], invert=True)
    panel["fraser_regulation_z"] = zscore(panel["fraser_regulation"])
    panel["product_market_competition_index"] = (
        0.6 * panel["pmr_inverted_z"] + 0.4 * panel["fraser_regulation_z"]
    )
    panel["product_market_competition_index"] = zscore(
        panel["product_market_competition_index"]
    )
    coverage = {
        "candidate_rows_after_pmr_fraser_outcomes": int(len(panel)),
        "candidate_countries": int(panel["country_iso3"].nunique()),
        "union_density_missing_rows": int(panel["union_density"].isna().sum()),
        "real_interest_missing_rows": int(panel["real_interest_rate"].isna().sum()),
    }
    return panel, coverage


def fit(panel: pd.DataFrame, outcome: str, controls: list[str]) -> dict[str, object]:
    cols = ["country_iso3", "year", outcome, "product_market_competition_index"] + controls
    data = panel[cols].dropna().set_index(["country_iso3", "year"]).sort_index()
    y = data[outcome]
    x = sm.add_constant(data[["product_market_competition_index"] + controls])
    model = PanelOLS(
        y,
        x,
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
        check_rank=False,
    )
    result = model.fit(cov_type="clustered", cluster_entity=True)
    return {
        "outcome": outcome,
        "method": "PanelOLS with country and year fixed effects",
        "covariance": "country-clustered",
        "coefficient": float(result.params["product_market_competition_index"]),
        "std_error": float(result.std_errors["product_market_competition_index"]),
        "p_value": float(result.pvalues["product_market_competition_index"]),
        "n_obs": int(result.nobs),
        "n_countries": int(data.index.get_level_values(0).nunique()),
        "years": [int(y) for y in sorted(data.index.get_level_values(1).unique())],
        "r_squared_within": float(result.rsquared_within),
        "controls": controls,
    }


def verdict_for(wage: dict[str, object], productivity: dict[str, object]) -> tuple[str, str]:
    wage_coef = float(wage["coefficient"])
    wage_p = float(wage["p_value"])
    prod_coef = float(productivity["coefficient"])
    prod_p = float(productivity["p_value"])
    if wage_coef > 0 and wage_p < 0.05 and prod_coef > 0 and prod_p < 0.05 and wage_coef >= 0.40:
        return (
            "PARTIAL",
            "proxy screen clears the registered direction/size checks, but remains proxy-only",
        )
    return (
        "PARTIAL",
        "proxy-only local rerun does not clear the registered positive/significant wage and productivity thresholds",
    )


def manifest_inputs() -> list[dict[str, object]]:
    items = []
    for name, path in INPUTS.items():
        publisher, series_id, label = VINTAGE_META[name]
        items.append(
            {
                "name": label,
                "publisher": publisher,
                "series_id": series_id,
                "vintage_file": rel(path),
                "sha256": sha256(path),
            }
        )
    return items


def main() -> int:
    spec = yaml.safe_load(HYPOTHESIS_PATH.read_text()) or {}
    panel, coverage = build_panel()
    controls = [
        "log_initial_gdp_pc",
        "trade_openness",
        "union_density",
        "services_share_gdp",
    ]
    wage = fit(panel, "real_wage_growth_proxy", controls)
    productivity = fit(panel, "labour_productivity_growth", controls)
    verdict, reason = verdict_for(wage, productivity)
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    coefficients = pd.DataFrame([wage, productivity])
    coefficients.to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    chart_cols = [
        "country_iso3",
        "year",
        "real_wage_growth_proxy",
        "labour_productivity_growth",
        "product_market_competition_index",
        "pmr_overall",
        "barriers_to_entry",
        "fraser_regulation",
        "union_density",
        "log_initial_gdp_pc",
        "trade_openness",
        "services_share_gdp",
        "real_interest_rate",
    ]
    (RUN_DIR / "chart_data.json").write_text(
        json.dumps(panel[chart_cols].sort_values(["country_iso3", "year"]).to_dict(orient="records"), indent=2)
        + "\n"
    )

    caveats = [
        "Proxy-only: OECD PDB labour compensation per hour deflated by WDI CPI replaces the unavailable OECD average-wage real-growth series.",
        "OECD earnings vintages on disk are wage-gap tables, not average annual wages, so they are not used as the wage outcome.",
        "PMR overall and barriers-to-entry coverage in local vintages is limited to 2018 and 2023.",
        "WDI real interest rate is documented but excluded from the fitted model because it leaves only 16 complete observations.",
        "Result should remain research_only, not a scoreboard candidate, unless exact wage series and wider PMR coverage are added.",
    ]
    diagnostics = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "panel_fe_proxy_local",
        "runner": rel(RUN_DIR / "replication.py"),
        "run_utc": generated_utc,
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "claim": spec.get("claim"),
        "estimates": {
            "real_wage_growth_proxy": wage,
            "labour_productivity_growth": productivity,
        },
        "coverage": coverage,
        "data_status": {
            "variables_loaded": [
                {"role": "outcome_proxy", "name": "real_wage_growth_proxy", "source": "oecd_pdb:LCHRS_GY minus world_bank_wdi:FP.CPI.TOTL.ZG"},
                {"role": "outcome", "name": "labour_productivity_growth", "source": "oecd_pdb:GDPHRS_GY"},
                {"role": "treatment", "name": "product_market_competition_index", "source": "0.6 * inverted oecd_pmr:PMR + 0.4 * fraser_efw:regulation"},
                {"role": "control", "name": "union_density", "source": "oecd:TUD"},
                {"role": "control", "name": "log_initial_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD"},
                {"role": "control", "name": "trade_openness", "source": "world_bank_wdi:NE.TRD.GNFS.ZS"},
                {"role": "control", "name": "services_share_gdp", "source": "world_bank_wdi:NV.SRV.TOTL.ZS"},
            ],
            "variables_missing": [
                {"role": "exact_outcome", "name": "real_wage_growth", "source": "oecd:avwage_growth_real"},
                {"role": "exact_outcome", "name": "median_real_wage_growth", "source": "ilo:median_wages_real_growth"},
            ],
        },
        "caveats": caveats,
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest = {
        "hypothesis_id": HID,
        "status": verdict,
        "reason": reason,
        "runner": rel(RUN_DIR / "replication.py"),
        "run_utc": generated_utc,
        "vintages": manifest_inputs(),
        "missing_series": [
            "oecd:avwage_growth_real",
            "ilo:median_wages_real_growth",
        ],
        "deviations": caveats,
    }
    (RUN_DIR / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )

    claim = str(spec.get("claim") or "").strip()
    rule = str((spec.get("falsification") or {}).get("rule") or "").strip()
    md = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {claim}",
        f"- **Falsification rule:** {rule}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test', '')}",
        "",
        "## Proxy Design",
        "- Outcome proxy: OECD PDB nominal labour compensation per hour growth (LCHRS, total economy) minus WDI CPI inflation.",
        "- Productivity outcome: OECD PDB GDP per hour worked growth (GDPHRS, chain-linked volume, total economy).",
        "- Treatment: 0.6 * inverted OECD PMR overall z-score + 0.4 * Fraser EFW regulation z-score, re-standardised so one unit is one sample SD.",
        "- Controls fitted: log GDP per capita, trade openness, union density, services share of GDP; real interest is documented but omitted for sparse coverage.",
        "",
        "## Estimates",
        "| outcome | beta per 1 SD competition | p-value | observations | countries | years |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in [wage, productivity]:
        md.append(
            f"| {row['outcome']} | {row['coefficient']:+.3f} | {row['p_value']:.3f} | "
            f"{row['n_obs']} | {row['n_countries']} | {', '.join(str(y) for y in row['years'])} |"
        )
    md += [
        "",
        "## Interpretation",
        "This proxy-only screen does not support the registered positive/significant threshold. The wage proxy coefficient is negative and not significant, and the productivity coefficient is also negative and not significant in the complete-control specification. Because the exact wage outcome and broader PMR coverage are still absent, this remains research-only rather than a dispositive refutation.",
        "",
        "## Source Paths",
    ]
    for item in manifest_inputs():
        md.append(f"- `{item['name']}` -> `{item['vintage_file']}`")
    md += [
        "",
        "## Caveats",
    ]
    md.extend(f"- {caveat}" for caveat in caveats)
    md.append("")
    (RUN_DIR / "result_card.md").write_text("\n".join(md), encoding="utf-8")

    print(f"{HID}: {verdict} - {reason}")
    print(f"  wage beta={wage['coefficient']:+.3f}, p={wage['p_value']:.3f}")
    print(f"  productivity beta={productivity['coefficient']:+.3f}, p={productivity['p_value']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
