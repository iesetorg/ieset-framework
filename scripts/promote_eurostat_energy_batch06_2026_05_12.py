#!/usr/bin/env python3
"""Promote and run Batch 06 Eurostat energy-price hypotheses.

This batch is deliberately narrow: use the local Eurostat nrg_pc_205
industrial electricity-price vintage plus local sectoral/labour, OWID, IRENA,
and WDI vintages. Household-price and distributional claims are audited as
blocked because only nrg_pc_205 is present locally, not the household
electricity-price table nrg_pc_204 or household micro/distribution data.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages"
HYPOTHESES = ROOT / "hypotheses" / "energy"
STEELMEN = ROOT / "hypotheses" / "steelman"
RUNS = ROOT / "engine" / "runs"
AUDITS = ROOT / "engine" / "audits"

EUROSTAT_ISO2 = {
    "EL": "GRC",
    "UK": "GBR",
}

EUROSTAT_SAMPLE_COUNTRIES = [
    "AUT", "BEL", "BGR", "CHE", "CYP", "CZE", "DEU", "DNK", "ESP", "EST",
    "FIN", "FRA", "GBR", "GRC", "HRV", "HUN", "IRL", "ISL", "ITA", "LTU",
    "LUX", "LVA", "MLT", "NLD", "NOR", "POL", "PRT", "ROU", "SVK", "SVN",
    "SWE",
]


def iso2_to_iso3(code: str) -> str | None:
    code = str(code).upper()
    if code in EUROSTAT_ISO2:
        return EUROSTAT_ISO2[code]
    if len(code) != 2:
        return None
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except Exception:
        return None


def latest(pub: str, stem: str) -> Path:
    files = sorted((VINTAGES / pub).glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing local vintage {pub}:{stem}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def meta(pub: str, stem: str, label: str) -> dict:
    path = latest(pub, stem)
    return {
        "publisher": pub,
        "series": stem,
        "label": label,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def eurostat_industrial_price() -> tuple[pd.DataFrame, dict]:
    path = latest("eurostat", "nrg_pc_205")
    df = pd.read_parquet(path)
    df = df[
        (df["siec"] == "E7000")
        & (df["nrg_cons"] == "MWH2000-19999")
        & (df["unit"] == "KWH")
        & (df["tax"] == "I_TAX")
        & (df["currency"] == "EUR")
    ].copy()
    df["country"] = df["geo_code"].map(iso2_to_iso3)
    df["year"] = df["period"].astype(str).str.slice(0, 4).astype(int)
    df["half"] = df["period"].astype(str).str.extract(r"S([12])").astype(int)
    df["industrial_electricity_price"] = pd.to_numeric(df["value"], errors="coerce")
    annual = (
        df.dropna(subset=["country", "industrial_electricity_price"])
        .groupby(["country", "year"], as_index=False)["industrial_electricity_price"]
        .mean()
    )
    annual["electricity_price_yoy"] = annual.groupby("country")[
        "industrial_electricity_price"
    ].pct_change() * 100
    annual["electricity_price_volatility"] = annual.groupby("country")[
        "electricity_price_yoy"
    ].transform(lambda s: s.rolling(3, min_periods=2).std())
    return annual, meta("eurostat", "nrg_pc_205", "industrial electricity prices, medium band, EUR/kWh incl. taxes")


def wdi(stem: str, out_col: str) -> tuple[pd.DataFrame, dict]:
    path = latest("world_bank_wdi", stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].copy()
    out.columns = ["country", "year", out_col]
    out["country"] = out["country"].astype(str).str.upper()
    out = out[out["country"].str.fullmatch(r"[A-Z]{3}")]
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out[out_col] = pd.to_numeric(out[out_col], errors="coerce")
    return out.dropna(), meta("world_bank_wdi", stem, out_col)


def owid(stem: str, value_col: str, out_col: str) -> tuple[pd.DataFrame, dict]:
    path = latest("owid", stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", value_col]].copy()
    out.columns = ["country", "year", out_col]
    out["country"] = out["country"].astype(str).str.upper()
    out = out[out["country"].str.fullmatch(r"[A-Z]{3}")]
    out[out_col] = pd.to_numeric(out[out_col], errors="coerce")
    return out.dropna(), meta("owid", stem, out_col)


def eurostat_unemployment() -> tuple[pd.DataFrame, dict]:
    path = latest("eurostat", "une_rt_a")
    df = pd.read_parquet(path)
    df = df[(df["age"] == "Y15-74") & (df["unit"] == "PC_ACT") & (df["sex"] == "T")].copy()
    df["country"] = df["geo_code"].map(iso2_to_iso3)
    df["year"] = pd.to_numeric(df["period"], errors="coerce")
    df["unemployment_rate"] = pd.to_numeric(df["value"], errors="coerce")
    out = df[["country", "year", "unemployment_rate"]].dropna()
    out["year"] = out["year"].astype(int)
    return out, meta("eurostat", "une_rt_a", "Eurostat unemployment rate, age 15-74, total sex")


def eurostat_sector_employment() -> tuple[pd.DataFrame, dict]:
    path = latest("eurostat", "nama_10_a10_e")
    df = pd.read_parquet(path)
    df = df[(df["unit"] == "THS_PER") & (df["na_item"] == "EMP_DC")].copy()
    df["country"] = df["geo_code"].map(iso2_to_iso3)
    df["year"] = pd.to_numeric(df["period"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    broad = {"A", "B-E", "F", "G-I", "J", "K", "L", "M_N", "O-Q", "R-U"}
    d = df[df["nace_r2"].isin(broad)].dropna(subset=["country", "year", "value"])
    piv = d.pivot_table(index=["country", "year"], columns="nace_r2", values="value", aggfunc="mean")
    total = piv[[c for c in broad if c in piv.columns]].sum(axis=1)
    services = piv[[c for c in ["G-I", "J", "K", "L", "M_N", "O-Q", "R-U"] if c in piv.columns]].sum(axis=1)
    industry = piv["B-E"] if "B-E" in piv.columns else np.nan
    out = pd.DataFrame(
        {
            "industry_employment_share": industry / total * 100,
            "services_minus_industry_employment_share": (services - industry) / total * 100,
        }
    ).reset_index()
    out = out.dropna()
    out["year"] = out["year"].astype(int)
    return out, meta("eurostat", "nama_10_a10_e", "Eurostat sector employment shares")


def irena_capacity(stem: str, out_col: str) -> tuple[pd.DataFrame, dict]:
    path = latest("irena", stem)
    df = pd.read_parquet(path)
    out = df[["country", "year", "value"]].copy()
    out.columns = ["country", "year", out_col]
    out["country"] = out["country"].astype(str).str.upper()
    out[out_col] = pd.to_numeric(out[out_col], errors="coerce")
    return out.dropna(), meta("irena", stem, out_col)


@dataclass(frozen=True)
class Case:
    hid: str
    topic: str
    claim: str
    treatment: str
    outcome: str
    direction: str
    schools: tuple[str, ...]
    dims: tuple[str, ...]
    policy: tuple[str, ...]
    controls: tuple[str, ...] = ("gdp_pc_growth",)
    runnable: bool = True
    blocker: str | None = None


CASES = [
    Case("eurostat_industrial_electricity_price_manufacturing_va_2007_2025", "energy", "Higher industrial electricity prices predict lower manufacturing value-added shares in European panels.", "industrial_electricity_price", "manufacturing_va_share", "-", ("classical_liberal", "ordoliberal", "developmentalism"), ("energy", "industrial_capability"), ("energy_policy", "industrial_policy")),
    Case("eurostat_household_electricity_price_consumption_panel", "energy", "Higher household electricity prices reduce real household consumption growth.", "household_electricity_price", "household_consumption_pc", "-", ("post_keynesian", "social_democratic", "empirical_pragmatist"), ("energy", "welfare_state"), ("energy_policy", "welfare_architecture"), runnable=False, blocker="Local Eurostat inventory has nrg_pc_205 industrial prices only; nrg_pc_204 household electricity prices are not present."),
    Case("eurostat_electricity_price_inflation_pass_through", "energy", "Industrial electricity-price inflation passes through to headline CPI inflation.", "electricity_price_yoy", "cpi_inflation", "+", ("new_keynesian", "post_keynesian", "chicago_monetarism"), ("energy", "inflation"), ("energy_policy", "monetary_policy"), ()),
    Case("eurostat_nuclear_retention_industrial_price_panel", "energy", "Countries retaining higher nuclear-electricity shares have lower industrial electricity prices.", "nuclear_share", "industrial_electricity_price", "-", ("ordoliberal", "developmentalism", "eco_socialist"), ("energy", "industrial_capability"), ("energy_policy", "industrial_policy")),
    Case("eurostat_renewable_share_electricity_price_transition_cost", "energy", "Higher renewable-electricity shares are associated with higher industrial prices during the transition window.", "renewable_share", "industrial_electricity_price", "+", ("eco_socialist", "degrowth", "classical_liberal"), ("energy", "regulation_compliance_cost"), ("energy_policy",), ("gdp_pc_growth",)),
    Case("eurostat_energy_price_household_distribution_stress", "energy", "Energy-price spikes increase household distributional stress.", "household_electricity_price", "distribution_stress", "+", ("social_democratic", "post_keynesian", "eco_socialist"), ("energy", "poverty_inequality"), ("energy_policy", "welfare_architecture"), runnable=False, blocker="No local household electricity-price vintage, EU-SILC distribution table, or poverty stress panel was present for this batch."),
    Case("eurostat_energy_price_export_competitiveness_panel", "energy", "Higher industrial electricity prices reduce export competitiveness.", "industrial_electricity_price", "export_share", "-", ("classical_liberal", "developmentalism", "ordoliberal"), ("energy", "trade_liberalisation"), ("energy_policy", "trade_policy")),
    Case("eurostat_energy_price_unemployment_regional_panel", "energy", "Higher industrial electricity prices predict higher unemployment in European labour-market panels.", "industrial_electricity_price", "unemployment_rate", "+", ("post_keynesian", "ordoliberal", "empirical_pragmatist"), ("energy", "employment_labour"), ("energy_policy", "labour_market")),
    Case("eurostat_electricity_price_volatility_industrial_exit", "energy", "Industrial electricity-price volatility predicts industrial employment-share decline.", "electricity_price_volatility", "industry_employment_share", "-", ("austrian", "ordoliberal", "developmentalism"), ("energy", "employment_labour"), ("energy_policy", "industrial_policy")),
    Case("eurostat_energy_price_services_vs_industry_reallocation", "energy", "Higher industrial electricity prices accelerate reallocation from industry toward services.", "industrial_electricity_price", "services_minus_industry_employment_share", "+", ("empirical_pragmatist", "developmentalism", "degrowth"), ("energy", "employment_labour"), ("energy_policy", "industrial_policy")),
]


def build_sources() -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
    frames: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict] = {}

    price, price_meta = eurostat_industrial_price()
    frames["industrial_electricity_price"] = price[["country", "year", "industrial_electricity_price"]]
    frames["electricity_price_yoy"] = price[["country", "year", "electricity_price_yoy"]]
    frames["electricity_price_volatility"] = price[["country", "year", "electricity_price_volatility"]]
    metas["industrial_electricity_price"] = price_meta
    metas["electricity_price_yoy"] = price_meta
    metas["electricity_price_volatility"] = price_meta

    for stem, col in [
        ("NV.IND.MANF.ZS", "manufacturing_va_share"),
        ("FP.CPI.TOTL.ZG", "cpi_inflation"),
        ("NE.EXP.GNFS.ZS", "export_share"),
        ("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth"),
        ("SP.POP.TOTL", "population"),
    ]:
        frames[col], metas[col] = wdi(stem, col)

    frames["nuclear_share"], metas["nuclear_share"] = owid("share-electricity-nuclear", "Nuclear", "nuclear_share")
    frames["renewable_share"], metas["renewable_share"] = owid("share-electricity-renewables", "Renewables", "renewable_share")
    frames["unemployment_rate"], metas["unemployment_rate"] = eurostat_unemployment()
    sector, sector_meta = eurostat_sector_employment()
    frames["industry_employment_share"] = sector[["country", "year", "industry_employment_share"]]
    frames["services_minus_industry_employment_share"] = sector[["country", "year", "services_minus_industry_employment_share"]]
    metas["industry_employment_share"] = sector_meta
    metas["services_minus_industry_employment_share"] = sector_meta

    renew_cap, renew_meta = irena_capacity("installed_capacity_renewable", "renewable_capacity_mw")
    frames["renewable_capacity_mw"] = renew_cap
    metas["renewable_capacity_mw"] = renew_meta
    return frames, metas


def merge_panel(keys: list[str], frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    panel = None
    for key in keys:
        frame = frames[key]
        panel = frame if panel is None else panel.merge(frame, on=["country", "year"], how="outer")
    assert panel is not None
    return panel


def verdict(coef: float, pval: float, direction: str) -> tuple[str, str]:
    expected = 1 if direction == "+" else -1
    sign = 1 if coef > 0 else -1 if coef < 0 else 0
    if pval < 0.10 and sign == expected:
        return "SUPPORTED", "coefficient is statistically significant in the predicted direction"
    if pval < 0.10 and sign == -expected:
        return "REFUTED", "coefficient is statistically significant in the opposite direction"
    return "PARTIAL", "coefficient is not statistically decisive at p<0.10"


def run_case(case: Case, frames: dict[str, pd.DataFrame], metas: dict[str, dict], run_utc: str) -> dict:
    controls = [c for c in case.controls if c not in {case.treatment, case.outcome}]
    keys = [case.treatment, case.outcome] + controls
    panel = merge_panel(keys, frames)
    d = panel[["country", "year"] + keys].replace([math.inf, -math.inf], np.nan).dropna().copy()
    d = d[(d["year"] >= 2019) & (d["year"] <= 2025)]
    d["year"] = d["year"].astype(int)
    for col in keys:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna()
    if len(d) < 30 or d["country"].nunique() < 8:
        raise ValueError(f"insufficient usable panel for {case.hid}: n={len(d)}, countries={d['country'].nunique()}")

    rhs = [f"Q('{case.treatment}')"] + [f"Q('{c}')" for c in controls] + ["C(country)", "C(year)"]
    formula = f"Q('{case.outcome}') ~ " + " + ".join(rhs)
    model = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
    coef = float(model.params[f"Q('{case.treatment}')"])
    se = float(model.bse[f"Q('{case.treatment}')"])
    pval = float(model.pvalues[f"Q('{case.treatment}')"])
    ci = [float(x) for x in model.conf_int().loc[f"Q('{case.treatment}')"].tolist()]
    label, reason = verdict(coef, pval, case.direction)

    run_dir = RUNS / case.hid
    run_dir.mkdir(parents=True, exist_ok=True)
    diagnostics = {
        "hypothesis_id": case.hid,
        "verdict_label": label,
        "verdict_reason": reason,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "period_min": int(d["year"].min()),
        "period_max": int(d["year"].max()),
        "formula": formula,
        "coefficient": coef,
        "standard_error_cluster_country": se,
        "p_value": pval,
        "ci95": ci,
        "direction": case.direction,
        "treatment": case.treatment,
        "outcome": case.outcome,
        "controls": controls,
        "run_utc": run_utc,
        "runner": "scripts/promote_eurostat_energy_batch06_2026_05_12.py",
        "school_focus": list(case.schools),
        "batch": "06_eurostat_energy_prices_nuclear_transition",
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    manifest = {
        "hypothesis_id": case.hid,
        "run_utc": run_utc,
        "verdict_label": label,
        "vintages": {key: metas[key] for key in keys},
        "formula": formula,
    }
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    pd.DataFrame(
        [{"term": case.treatment, "coefficient": coef, "std_error": se, "p_value": pval, "ci95_low": ci[0], "ci95_high": ci[1]}]
    ).to_parquet(run_dir / "coefficients.parquet", index=False)
    chart = (
        d[["country", "year", case.treatment, case.outcome]]
        .sort_values(["country", "year"])
        .to_dict(orient="records")
    )
    (run_dir / "chart_data.json").write_text(json.dumps(chart[:2000], indent=2) + "\n")
    (run_dir / "result_card.md").write_text(
        f"# Result card - {case.hid}\n\n"
        f"**Verdict:** {label} - {reason}.\n\n"
        "## Plain-English Claim\n\n"
        f"{case.claim}\n\n"
        "## School Coverage\n\n"
        f"{', '.join(case.schools)}\n\n"
        "## What Was Measured\n\n"
        f"- Outcome: `{case.outcome}`.\n"
        f"- Treatment: `{case.treatment}`.\n"
        f"- Controls: {', '.join(f'`{c}`' for c in controls) if controls else 'none'}.\n\n"
        "## Results\n\n"
        f"- Usable panel: **{len(d):,} observations**, **{d['country'].nunique()} countries**, {int(d['year'].min())}-{int(d['year'].max())}.\n"
        f"- Coefficient on treatment: **{coef:.4f}** (SE {se:.4f}, p={pval:.4f}).\n\n"
        "## Specification\n\n"
        f"`{formula}`\n\n"
        "This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.\n"
    )
    (run_dir / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\nimport sys\n"
        "ROOT = Path(__file__).resolve().parents[3]\n"
        "sys.path.insert(0, str(ROOT / 'scripts'))\n"
        "from promote_eurostat_energy_batch06_2026_05_12 import main\n\n"
        "if __name__ == '__main__':\n    main()\n",
        encoding="utf-8",
    )
    return diagnostics


def write_hypotheses() -> None:
    HYPOTHESES.mkdir(parents=True, exist_ok=True)
    STEELMEN.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        spec = {
            "hypothesis_id": case.hid,
            "version": 1,
            "status": "candidate" if case.runnable else "draft",
            "topic": case.topic,
            "claim": case.claim,
            "methodology_note": "Promoted for Batch 06 on 2026-05-12 using local Eurostat nrg_pc_205 and companion local vintages.",
            "evidence_type": "associational",
            "sample": {
                "countries": EUROSTAT_SAMPLE_COUNTRIES,
                "period": [2019, 2025],
                "temporal_structure": "panel",
                "exclusion_rules": ["drop non-country aggregates and country-years missing treatment/outcome"],
            },
            "variables": {
                "outcome": [{"name": case.outcome, "source": "local_batch06_derived", "transformation": "level_or_growth"}],
                "treatment": [{"name": case.treatment, "source": "local_batch06_derived", "transformation": "annual_mean_or_growth"}],
                "controls": [{"name": c, "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "transformation": "level"} for c in case.controls],
            },
            "estimator": {
                "template": "panel_fe",
                "fixed_effects": ["country", "year"],
                "clustering": "country",
                "notes": "Short-panel throughput screen; household/distribution claims require additional local tables before running.",
            },
            "falsification": {
                "rule": "SUPPORTED if treatment coefficient has the predicted sign at p<0.10; REFUTED if opposite sign at p<0.10; otherwise PARTIAL.",
                "test": f"panel_fe_{case.hid}",
                "threshold": "p<0.10 with pre-registered sign",
            },
            "prior_confidence": 0.5,
            "disclosure": case.blocker or "Associational short-panel design; energy shocks, market design, and industrial composition remain possible confounders.",
            "steelman": f"hypotheses/steelman/{case.hid}.md",
            "scope": {
                "period": [2019, 2025],
                "countries": ["EU"],
                "outcome_dim": list(case.dims),
                "policy_family": list(case.policy),
                "treatment_tags": ["electricity_prices", "energy_transition", "eurostat_batch06"],
            },
        }
        path = HYPOTHESES / f"{case.hid}.yaml"
        path.write_text(
            "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
            + yaml.safe_dump(spec, sort_keys=False, width=100),
            encoding="utf-8",
        )
        steel = STEELMEN / f"{case.hid}.md"
        if not steel.exists():
            steel.write_text(
                f"# Steelman - {case.hid}\n\n"
                "The strongest counterargument is that short-run European electricity prices reflect gas shocks, tax relief, market design, and industrial composition as much as the policy channel named in the hypothesis. "
                "A stronger design would add direct tariff/contract data, household-price tables where relevant, and pre-2022 policy timing with event-study checks.\n"
            )


def write_audit(results: list[dict], blocked: list[dict], run_utc: str, metas: dict[str, dict]) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    tally = {}
    for row in results:
        tally[row["verdict_label"]] = tally.get(row["verdict_label"], 0) + 1
    audit = {
        "batch": "06_eurostat_energy_prices_nuclear_transition",
        "run_utc": run_utc,
        "attempted_ids": len(CASES),
        "promoted_specs": len(CASES),
        "runnable_results": len(results),
        "blocked": blocked,
        "verdict_tally": tally,
        "inventory": {
            "eurostat_nrg_pc_205": metas.get("industrial_electricity_price"),
            "eurostat_sectoral": metas.get("industry_employment_share"),
            "eurostat_labour": metas.get("unemployment_rate"),
            "irena": metas.get("renewable_capacity_mw"),
            "wdi_examples": {
                "manufacturing_va_share": metas.get("manufacturing_va_share"),
                "export_share": metas.get("export_share"),
                "cpi_inflation": metas.get("cpi_inflation"),
            },
        },
        "results": results,
    }
    json_path = AUDITS / "batch06_eurostat_energy_prices_readiness_2026-05-12.json"
    md_path = AUDITS / "batch06_eurostat_energy_prices_readiness_2026-05-12.md"
    json_path.write_text(json.dumps(audit, indent=2) + "\n")
    lines = [
        "# Batch 06 Eurostat Energy Prices / Nuclear Transition Readiness Audit - 2026-05-12",
        "",
        f"- Promoted specs: {len(CASES)}",
        f"- Runnable results written: {len(results)}",
        f"- Blocked IDs: {len(blocked)}",
        f"- Verdict tally: {tally}",
        "",
        "## Local Inventory",
        "",
        "- Eurostat `nrg_pc_205`: present; industrial electricity prices by semester, consumption band, tax, currency, country.",
        "- Eurostat sectoral/labour: `nama_10_a10_e` and `une_rt_a` present; national panels are usable, regional unemployment design was downgraded to national overlap.",
        "- IRENA: renewable capacity and LCOE vintages present; capacity is inventoried, while LCOE is world-only and not suitable for country fixed effects.",
        "- WDI: manufacturing value added, CPI inflation, exports, GDP growth, population, sector employment proxies present.",
        "",
        "## Runnable Results",
        "",
    ]
    for row in results:
        lines.append(
            f"- `{row['hypothesis_id']}`: {row['verdict_label']} ({row['n_observations']} obs, {row['n_countries']} countries, p={row['p_value']:.4f})."
        )
    lines += ["", "## Blockers", ""]
    for row in blocked:
        lines.append(f"- `{row['hypothesis_id']}`: {row['blocker']}")
    lines.append("")
    md_path.write_text("\n".join(lines))


def main() -> int:
    run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    write_hypotheses()
    frames, metas = build_sources()
    results: list[dict] = []
    blocked: list[dict] = []
    for case in CASES:
        if not case.runnable:
            blocked.append({"hypothesis_id": case.hid, "blocker": case.blocker})
            continue
        try:
            results.append(run_case(case, frames, metas, run_utc))
        except Exception as exc:
            blocked.append({"hypothesis_id": case.hid, "blocker": str(exc)})
    write_audit(results, blocked, run_utc, metas)
    print(f"promoted={len(CASES)} runnable={len(results)} blocked={len(blocked)}")
    print("tally", {k: sum(1 for r in results if r["verdict_label"] == k) for k in sorted({r["verdict_label"] for r in results})})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
