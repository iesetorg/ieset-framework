#!/usr/bin/env python3
"""Graduate household-energy Eurostat panels now that nrg_pc_204 is present."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"

ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
    "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC",
    "ES": "ESP", "FI": "FIN", "FR": "FRA", "HR": "HRV", "HU": "HUN",
    "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
    "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK",
}
COUNTRIES = set(ISO2_TO_ISO3.values())
PERIOD = (2019, 2024)


def latest(publisher: str, series: str) -> Path:
    matches = sorted((ROOT / "data" / "vintages" / publisher).glob(f"{series}@*.parquet"))
    if not matches:
        raise FileNotFoundError(f"{publisher}:{series}")
    return matches[-1]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def hypothesis(hid: str) -> dict:
    path = ROOT / "hypotheses" / "energy" / f"{hid}.yaml"
    return yaml.safe_load(path.read_text())


def household_price() -> tuple[pd.DataFrame, Path]:
    path = latest("eurostat", "nrg_pc_204")
    df = pd.read_parquet(path)
    df = df[
        (df["siec"] == "E7000")
        & (df["nrg_cons"] == "KWH2500-4999")
        & (df["unit"] == "KWH")
        & (df["tax"] == "I_TAX")
        & (df["currency"] == "EUR")
    ].copy()
    df["country"] = df["geo_code"].map(ISO2_TO_ISO3)
    df["year"] = df["period"].astype(str).str.slice(0, 4).astype(int)
    df["household_electricity_price"] = pd.to_numeric(df["value"], errors="coerce")
    out = (
        df.dropna(subset=["country", "household_electricity_price"])
        .groupby(["country", "year"], as_index=False)["household_electricity_price"]
        .mean()
    )
    return out, path


def wdi(series: str, out_col: str) -> tuple[pd.DataFrame, Path]:
    path = latest("world_bank_wdi", series)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].copy()
    out.columns = ["country", "year", out_col]
    out = out[out["country"].isin(COUNTRIES)].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out[out_col] = pd.to_numeric(out[out_col], errors="coerce")
    return out.dropna(), path


def warmth_stress() -> tuple[pd.DataFrame, Path]:
    path = latest("eurostat", "ilc_mdes01")
    df = pd.read_parquet(path)
    df = df[
        (df["hhtyp"] == "TOTAL")
        & (df["incgrp"] == "TOTAL")
        & (df["unit"] == "PC")
    ].copy()
    df["country"] = df["geo_code"].map(ISO2_TO_ISO3)
    df["year"] = pd.to_numeric(df["period"], errors="coerce")
    df["distribution_stress"] = pd.to_numeric(df["value"], errors="coerce")
    out = df[["country", "year", "distribution_stress"]].dropna()
    out["year"] = out["year"].astype(int)
    return out, path


def run_fe(panel: pd.DataFrame, outcome: str, treatment: str) -> dict:
    model_df = panel.dropna(subset=[outcome, treatment, "gdp_pc_growth"]).copy()
    formula = f"Q('{outcome}') ~ Q('{treatment}') + Q('gdp_pc_growth') + C(country) + C(year)"
    model = smf.ols(formula, data=model_df)
    result = model.fit(cov_type="cluster", cov_kwds={"groups": model_df["country"]})
    return {
        "method": "statsmodels OLS with country and year fixed effects",
        "formula": formula,
        "coefficient": float(result.params[f"Q('{treatment}')"]),
        "std_error": float(result.bse[f"Q('{treatment}')"]),
        "p_value": float(result.pvalues[f"Q('{treatment}')"]),
        "n_obs": int(len(model_df)),
        "n_countries": int(model_df["country"].nunique()),
        "start_year": int(model_df["year"].min()),
        "end_year": int(model_df["year"].max()),
    }


def verdict(estimate: dict, expected_sign: str) -> tuple[str, str]:
    coef = estimate["coefficient"]
    p = estimate["p_value"]
    if p < 0.10 and ((expected_sign == "+" and coef > 0) or (expected_sign == "-" and coef < 0)):
        return "SUPPORTED", "coefficient has the preregistered sign at p<0.10"
    if p < 0.10:
        return "REFUTED", "coefficient has the opposite sign at p<0.10"
    return "PARTIAL", "coefficient is not statistically decisive at p<0.10"


def write_run(
    *,
    hid: str,
    outcome: str,
    treatment: str,
    expected_sign: str,
    panel: pd.DataFrame,
    estimate: dict,
    vintages: list[tuple[str, str, Path]],
) -> None:
    spec = hypothesis(hid)
    label, reason = verdict(estimate, expected_sign)
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diagnostics = {
        "verdict": f"{label} - {reason}",
        "verdict_label": label,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "panel_fe",
        "estimate": estimate,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "data_input",
                    "name": name,
                    "source": source,
                    "publisher": source.split(":", 1)[0],
                    "n_rows": int(pd.read_parquet(path).shape[0]),
                }
                for name, source, path in vintages
            ],
            "variables_missing": [],
        },
        "run_utc": run_utc,
        "runner": f"scripts/graduate_eurostat_household_energy_panels_2026_05_15.py::{hid}",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    manifest = {
        "status": label,
        "runner": "scripts/graduate_eurostat_household_energy_panels_2026_05_15.py",
        "vintages": [
            {"name": role, "vintage_file": rel(path)}
            for role, _source, path in vintages
        ],
    }
    (out_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    md = [
        f"# Result card - {hid}",
        "",
        f"**Verdict:** {label} - {reason}",
        "",
        "## Plain-English Claim",
        "",
        spec.get("claim", "").strip(),
        "",
        "## What Was Measured",
        "",
        f"- Outcome: `{outcome}`.",
        f"- Treatment: `{treatment}`.",
        "- Controls: `gdp_pc_growth`.",
        "",
        "## Results",
        "",
        f"- Usable panel: **{estimate['n_obs']} observations**, **{estimate['n_countries']} countries**, {estimate['start_year']}-{estimate['end_year']}.",
        f"- Coefficient on treatment: **{estimate['coefficient']:+.4g}** (SE {estimate['std_error']:.4g}, p={estimate['p_value']:.4g}).",
        "",
        "## Specification",
        "",
        f"`{estimate['formula']}`",
        "",
        "This is a short European household-energy panel screen using landed Eurostat and WDI vintages. Treat it as throughput evidence, not final causal proof.",
        "",
    ]
    (out_dir / "result_card.md").write_text("\n".join(md))
    print(f"{hid}: {label} - {reason}")


def main() -> int:
    price, price_path = household_price()
    gdp, gdp_path = wdi("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth")
    consumption, consumption_path = wdi("NE.CON.PRVT.KD.ZG", "household_consumption_growth")
    stress, stress_path = warmth_stress()

    base = price.merge(gdp, on=["country", "year"], how="inner")
    base = base[(base["year"] >= PERIOD[0]) & (base["year"] <= PERIOD[1])].copy()

    consumption_panel = base.merge(consumption, on=["country", "year"], how="inner")
    consumption_est = run_fe(consumption_panel, "household_consumption_growth", "household_electricity_price")
    write_run(
        hid="eurostat_household_electricity_price_consumption_panel",
        outcome="household_consumption_growth",
        treatment="household_electricity_price",
        expected_sign="-",
        panel=consumption_panel,
        estimate=consumption_est,
        vintages=[
            ("household_consumption_growth", "world_bank_wdi:NE.CON.PRVT.KD.ZG", consumption_path),
            ("household_electricity_price", "eurostat:nrg_pc_204", price_path),
            ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", gdp_path),
        ],
    )

    stress_panel = base.merge(stress, on=["country", "year"], how="inner")
    stress_est = run_fe(stress_panel, "distribution_stress", "household_electricity_price")
    write_run(
        hid="eurostat_energy_price_household_distribution_stress",
        outcome="distribution_stress",
        treatment="household_electricity_price",
        expected_sign="+",
        panel=stress_panel,
        estimate=stress_est,
        vintages=[
            ("distribution_stress", "eurostat:ilc_mdes01", stress_path),
            ("household_electricity_price", "eurostat:nrg_pc_204", price_path),
            ("gdp_pc_growth", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", gdp_path),
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
