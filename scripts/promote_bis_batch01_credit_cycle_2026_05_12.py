#!/usr/bin/env python3
"""Promote and run Batch 01 BIS credit-cycle / Austrian-Minsky tests.

This runner intentionally uses only local vintages already on disk:
BIS credit gaps, BIS debt-service ratios, BIS real residential property
prices, and WDI annual macro outcomes. It skips pre-existing artifact paths
by default so concurrent agents' outputs are not overwritten.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
BIS = ROOT / "data" / "vintages" / "bis"
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"
RUNS = ROOT / "engine" / "runs"
HYPOTHESES = ROOT / "hypotheses"
STEELMEN = HYPOTHESES / "steelman"
AUDIT = ROOT / "engine" / "audits" / "bis_batch01_credit_cycle_results_2026-05-12.md"

BIS_ISO2_TO_ISO3 = {
    "AU": "AUS", "AT": "AUT", "BE": "BEL", "BR": "BRA", "CA": "CAN",
    "CH": "CHE", "CL": "CHL", "CN": "CHN", "CO": "COL", "CZ": "CZE",
    "DE": "DEU", "DK": "DNK", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "GB": "GBR", "GR": "GRC", "HK": "HKG", "HU": "HUN", "ID": "IDN",
    "IE": "IRL", "IL": "ISR", "IN": "IND", "IT": "ITA", "JP": "JPN",
    "KR": "KOR", "LU": "LUX", "MX": "MEX", "MY": "MYS", "NL": "NLD",
    "NO": "NOR", "NZ": "NZL", "PL": "POL", "PT": "PRT", "RU": "RUS",
    "SA": "SAU", "SE": "SWE", "SG": "SGP", "TH": "THA", "TR": "TUR",
    "US": "USA", "ZA": "ZAF",
}

BIS_SAMPLE_ISO3 = sorted(set(BIS_ISO2_TO_ISO3.values()))

CASES = {
    "bis_credit_gap_house_price_reversal_oecd_1970_2025": {
        "topic": "housing",
        "claim": "Elevated BIS credit gaps predict weaker three-year real house-price growth.",
        "outcome": "fwd_real_house_price_growth_12q",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "lag_real_house_price_growth_8q"],
        "formula": "fwd_real_house_price_growth_12q ~ high_credit_gap + credit_gap + lag_real_house_price_growth_8q + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -3.0, "p_max": 0.05, "mean_diff_max": -3.0, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["housing", "financialisation"],
        "policy_family": ["monetary_policy", "regulation", "housing_policy"],
    },
    "bis_credit_gap_unemployment_lag_panel_1970_2025": {
        "topic": "monetary",
        "claim": "High BIS credit-gap episodes predict unemployment increases over the following two years.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ high_credit_gap + credit_gap + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "mean_diff_min": 0.25, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["financial_crisis", "employment_labour"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_credit_gap_dsr_joint_fragility_panel_1999_2025": {
        "topic": "monetary",
        "claim": "Credit-gap stress is more damaging when household debt-service burdens are also high.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "credit_gap_x_high_dsr",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "household_dsr", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ credit_gap_x_high_dsr + credit_gap + household_dsr + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.4, "p_max": 0.10, "mean_diff_min": 0.4, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["financial_crisis", "employment_labour"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_household_dsr_consumption_slowdown_panel_1999_2025": {
        "topic": "monetary",
        "claim": "High household debt-service burdens predict weaker private-consumption growth over the next two years.",
        "outcome": "fwd_consumption_growth_2y_avg",
        "treatment": "high_household_dsr",
        "continuous": "household_dsr",
        "controls": ["household_dsr", "consumption_growth"],
        "formula": "fwd_consumption_growth_2y_avg ~ high_household_dsr + household_dsr + consumption_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.8, "p_max": 0.10, "mean_diff_max": -0.8, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["gdp_growth", "financial_crisis"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_corporate_dsr_investment_slowdown_panel_1999_2025": {
        "topic": "growth",
        "claim": "High non-financial corporate debt-service burdens predict later private-investment-share declines.",
        "outcome": "fwd_private_investment_share_change_3y",
        "treatment": "high_corporate_dsr",
        "continuous": "corporate_dsr",
        "controls": ["corporate_dsr", "private_investment_share", "gdp_growth"],
        "formula": "fwd_private_investment_share_change_3y ~ high_corporate_dsr + corporate_dsr + private_investment_share + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.5, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["productivity", "financialisation"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_credit_gap_current_account_twin_deficit_risk": {
        "topic": "monetary",
        "claim": "Credit-gap stress predicts larger unemployment increases when current accounts are in deficit.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "credit_gap_x_current_account_deficit",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "current_account_balance_gdp", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ credit_gap_x_current_account_deficit + credit_gap + current_account_balance_gdp + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "mean_diff_min": 0.25, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["financial_crisis", "employment_labour", "capital_flows"],
        "policy_family": ["monetary_policy", "exchange_rate_regime"],
    },
    "bis_credit_gap_low_real_rate_amplifier_panel": {
        "topic": "monetary",
        "claim": "Credit-gap stress is more dangerous when real interest rates are unusually low.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "credit_gap_x_low_real_rate",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "real_interest_rate", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ credit_gap_x_low_real_rate + credit_gap + real_interest_rate + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "mean_diff_min": 0.25, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["financial_crisis", "employment_labour"],
        "policy_family": ["monetary_policy"],
    },
    "bis_house_price_credit_gap_boom_bust_panel": {
        "topic": "housing",
        "claim": "House-price booms reverse more sharply when paired with high BIS credit gaps.",
        "outcome": "fwd_real_house_price_growth_12q",
        "treatment": "credit_gap_x_house_price_boom",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "lag_real_house_price_growth_8q"],
        "formula": "fwd_real_house_price_growth_12q ~ credit_gap_x_house_price_boom + credit_gap + lag_real_house_price_growth_8q + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -2.0, "p_max": 0.10, "mean_diff_max": -2.0, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["housing", "financialisation"],
        "policy_family": ["monetary_policy", "housing_policy"],
    },
    "bis_credit_gap_private_investment_reversal_panel": {
        "topic": "growth",
        "claim": "High BIS credit-gap episodes predict weaker private-investment share over the following three years.",
        "outcome": "fwd_private_investment_share_change_3y",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "private_investment_share", "gdp_growth"],
        "formula": "fwd_private_investment_share_change_3y ~ high_credit_gap + credit_gap + private_investment_share + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.5, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["productivity", "financialisation"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_long_horizon_credit_cycle_market_discipline_panel": {
        "topic": "growth",
        "claim": "Credit booms predict weaker five-year real GDP-per-capita growth, consistent with later market discipline.",
        "outcome": "fwd_gdp_pc_growth_5y_avg",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["credit_gap", "gdp_pc_growth"],
        "formula": "fwd_gdp_pc_growth_5y_avg ~ high_credit_gap + credit_gap + gdp_pc_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.5, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["gdp_growth", "financialisation"],
        "policy_family": ["monetary_policy", "regulation"],
    },
}


def latest(root: Path, stem: str) -> Path:
    files = sorted(root.glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {root}/{stem}@*.parquet")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def qnum(period: str) -> int:
    year, q = str(period).split("-Q")
    return int(year) * 4 + int(q)


def qyear(q: int) -> int:
    return q // 4


def bis_quarterly(df: pd.DataFrame, country_col: str, value_col: str = "value") -> pd.DataFrame:
    out = df[[country_col, "period", value_col]].rename(columns={country_col: "bis_country", value_col: "value"}).copy()
    out["q"] = out["period"].map(qnum)
    out["year"] = out["q"].map(qyear)
    out["country"] = out["bis_country"].map(BIS_ISO2_TO_ISO3)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["country", "q", "value"])


def add_forward_log_growth(df: pd.DataFrame, value_col: str, horizons: list[int], prefix: str) -> pd.DataFrame:
    out = df.sort_values(["country", "q"]).copy()
    for h in horizons:
        future = out.groupby("country")[value_col].shift(-h)
        past = out.groupby("country")[value_col].shift(h)
        out[f"fwd_{prefix}_growth_{h}q"] = 100 * (np.log(future) - np.log(out[value_col]))
        out[f"lag_{prefix}_growth_{h}q"] = 100 * (np.log(out[value_col]) - np.log(past))
    return out


def wdi_series(stem: str, name: str) -> tuple[pd.DataFrame, dict]:
    path = latest(WDI, stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].rename(columns={"country_iso3": "country", "value": name}).copy()
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out = out[out["country"].astype(str).str.fullmatch(r"[A-Z]{3}")].dropna(subset=[name])
    out["year"] = out["year"].astype(int)
    return out, {
        "publisher": "world_bank_wdi",
        "series": stem,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def dsr_slice(dsr_raw: pd.DataFrame, borrower: str, value_name: str, high_name: str) -> pd.DataFrame:
    out = bis_quarterly(dsr_raw[dsr_raw["DSR_BORROWERS"].eq(borrower)], "BORROWERS_CTY").rename(columns={"value": value_name})
    p75 = out.groupby("country")[value_name].quantile(0.75).rename(f"{value_name}_p75")
    out = out.merge(p75, on="country", how="left")
    out[high_name] = (out[value_name] >= out[f"{value_name}_p75"]).astype(int)
    return out


def build_panel() -> tuple[pd.DataFrame, dict]:
    paths = {name: latest(BIS, name) for name in ["WS_CREDIT_GAP", "WS_DSR", "WS_SPP"]}
    credit_raw = pd.read_parquet(paths["WS_CREDIT_GAP"])
    gap = bis_quarterly(credit_raw[credit_raw["CG_DTYPE"].eq("C")], "BORROWERS_CTY").rename(columns={"value": "credit_gap"})

    dsr_raw = pd.read_parquet(paths["WS_DSR"])
    household = dsr_slice(dsr_raw, "H", "household_dsr", "high_household_dsr")
    household["high_household_dsr"] = ((household["household_dsr"] >= 12.0) & household["high_household_dsr"].eq(1)).astype(int)
    corporate = dsr_slice(dsr_raw, "N", "corporate_dsr", "high_corporate_dsr")

    spp_raw = pd.read_parquet(paths["WS_SPP"])
    house = bis_quarterly(spp_raw[spp_raw["VALUE"].eq("R")], "REF_AREA").rename(columns={"value": "real_house_price"})
    house = add_forward_log_growth(house, "real_house_price", [8, 12], "real_house_price")
    house["house_price_boom"] = (house["lag_real_house_price_growth_8q"] >= 10.0).astype(int)

    panel = gap[["country", "q", "year", "credit_gap"]]
    panel = panel.merge(household[["country", "q", "year", "household_dsr", "high_household_dsr"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(corporate[["country", "q", "year", "corporate_dsr", "high_corporate_dsr"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(house[["country", "q", "year", "fwd_real_house_price_growth_12q", "lag_real_house_price_growth_8q", "house_price_boom"]], on=["country", "q", "year"], how="outer")
    panel["high_credit_gap"] = (panel["credit_gap"] >= 10.0).astype(int)
    panel["credit_gap_x_high_dsr"] = panel["high_credit_gap"] * panel["high_household_dsr"]
    panel["credit_gap_x_house_price_boom"] = panel["high_credit_gap"] * panel["house_price_boom"]

    wdi_specs = [
        ("SL.UEM.TOTL.ZS", "unemployment_rate"),
        ("NE.CON.PRVT.KD.ZG", "consumption_growth"),
        ("NE.GDI.FPRV.ZS", "private_investment_share"),
        ("NY.GDP.MKTP.KD.ZG", "gdp_growth"),
        ("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth"),
        ("BN.CAB.XOKA.GD.ZS", "current_account_balance_gdp"),
        ("FR.INR.RINR", "real_interest_rate"),
    ]
    manifest = {
        name: {"publisher": "bis", "series": name, "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}
        for name, path in paths.items()
    }
    for stem, name in wdi_specs:
        frame, meta = wdi_series(stem, name)
        manifest[stem] = meta
        panel = panel.merge(frame, on=["country", "year"], how="left")

    annual = panel[
        [
            "country", "year", "unemployment_rate", "consumption_growth", "private_investment_share",
            "current_account_balance_gdp", "real_interest_rate", "gdp_growth", "gdp_pc_growth",
        ]
    ].drop_duplicates().sort_values(["country", "year"])
    annual["fwd_unemployment_change_2y"] = annual.groupby("country")["unemployment_rate"].shift(-2) - annual["unemployment_rate"]
    annual["fwd_consumption_growth_2y_avg"] = (annual.groupby("country")["consumption_growth"].shift(-1) + annual.groupby("country")["consumption_growth"].shift(-2)) / 2
    annual["fwd_private_investment_share_change_3y"] = annual.groupby("country")["private_investment_share"].shift(-3) - annual["private_investment_share"]
    annual["fwd_gdp_pc_growth_5y_avg"] = sum(annual.groupby("country")["gdp_pc_growth"].shift(-i) for i in range(1, 6)) / 5
    panel = panel.merge(
        annual[
            [
                "country", "year", "fwd_unemployment_change_2y", "fwd_consumption_growth_2y_avg",
                "fwd_private_investment_share_change_3y", "fwd_gdp_pc_growth_5y_avg",
            ]
        ],
        on=["country", "year"],
        how="left",
    )
    panel["current_account_deficit"] = (panel["current_account_balance_gdp"] < 0).astype(int)
    real_p25 = panel.groupby("country")["real_interest_rate"].transform(lambda s: s.quantile(0.25))
    panel["low_real_rate"] = (panel["real_interest_rate"] <= real_p25).astype(int)
    panel["credit_gap_x_current_account_deficit"] = panel["high_credit_gap"] * panel["current_account_deficit"]
    panel["credit_gap_x_low_real_rate"] = panel["high_credit_gap"] * panel["low_real_rate"]
    return panel, manifest


def verdict_from(direction: str, gate: dict, beta: float, p: float, diff: float, n_obs: int, n_countries: int) -> tuple[str, str]:
    enough = n_obs >= gate["min_observations"] and n_countries >= gate["min_countries"]
    if not enough:
        return "INCONCLUSIVE_DATA_PENDING", "insufficient coverage for the predeclared gate"
    if direction == "positive":
        effect = beta >= gate["coef_min"] and p <= gate["p_max"]
        raw = diff >= gate["mean_diff_min"]
    else:
        effect = beta <= gate["coef_max"] and p <= gate["p_max"]
        raw = diff <= gate["mean_diff_max"]
    if effect and raw:
        return "SUPPORTED", "regression and raw contrast both clear the predeclared gates"
    if effect or raw:
        return "PARTIAL", "one of the regression or raw-contrast gates clears, but not both"
    return "REFUTED", "neither the regression nor raw-contrast gate clears"


def artifact_paths(hid: str, cfg: dict) -> list[Path]:
    return [HYPOTHESES / cfg["topic"] / f"{hid}.yaml", STEELMEN / f"{hid}.md", RUNS / hid]


def existing_diag(hid: str) -> dict | None:
    path = RUNS / hid / "diagnostics.json"
    if not path.exists():
        return None
    diag = json.loads(path.read_text())
    if "verdict_label" not in diag and "verdict" in diag:
        diag["verdict_label"] = str(diag["verdict"]).upper()
    if "verdict_reason" not in diag and "verdict_detail" in diag:
        diag["verdict_reason"] = diag["verdict_detail"]
    return diag


def fit_case(hid: str, cfg: dict, panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    cols = ["country", "year", cfg["outcome"], cfg["treatment"], cfg["continuous"]] + cfg["controls"]
    d = panel[cols].replace([math.inf, -math.inf], np.nan).dropna().copy()
    d["year"] = d["year"].astype(int)
    fit = smf.ols(cfg["formula"], data=d).fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
    term = cfg["treatment"]
    beta = float(fit.params[term])
    se = float(fit.bse[term])
    p = float(fit.pvalues[term])
    ci_low, ci_high = [float(x) for x in fit.conf_int().loc[term].tolist()]
    group = d.groupby(term)[cfg["outcome"]].agg(["mean", "count"]).to_dict("index")
    base = float(group.get(0, {}).get("mean", np.nan))
    high = float(group.get(1, {}).get("mean", np.nan))
    diff = high - base
    verdict, reason = verdict_from(cfg["direction"], cfg["gate"], beta, p, diff, len(d), d["country"].nunique())
    return d, {
        "hypothesis_id": hid,
        "verdict_label": verdict,
        "verdict_reason": reason,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "outcome": cfg["outcome"],
        "treatment": term,
        "coefficient": beta,
        "standard_error_cluster_country": se,
        "p_value": p,
        "ci95": [ci_low, ci_high],
        "raw_treated_minus_control_mean": diff,
        "control_mean": base,
        "treated_mean": high,
        "treated_count": int(group.get(1, {}).get("count", 0)),
        "gate": cfg["gate"],
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/promote_bis_batch01_credit_cycle_2026_05_12.py",
    }


def write_hypothesis(hid: str, cfg: dict) -> Path:
    out_dir = HYPOTHESES / cfg["topic"]
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": cfg["topic"],
        "claim": cfg["claim"],
        "evidence_type": "associational",
        "sample": {
            "countries": BIS_SAMPLE_ISO3,
            "period": [1970, 2025],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years or country-quarters missing the predeclared BIS treatment",
                "drop rows missing the WDI outcome or controls",
                "require forward outcome coverage before evaluating the row",
            ],
        },
        "variables": {
            "outcome": [{"name": cfg["outcome"], "source": "constructed from local BIS/WDI vintages", "transformation": "forward_change_or_forward_average"}],
            "treatment": [{"name": cfg["treatment"], "source": "bis:WS_CREDIT_GAP; bis:WS_DSR; bis:WS_SPP; world_bank_wdi", "transformation": "threshold_or_interaction_predeclared_in_runner"}],
            "controls": [{"name": c, "source": "world_bank_wdi or BIS local vintage", "transformation": "level"} for c in cfg["controls"]],
        },
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["country", "year"],
            "clustering": "country",
            "notes": "Compact panel screen with country and calendar-year fixed effects. Standard errors clustered by country.",
        },
        "falsification": {
            "rule": f"Supported only if the coefficient on {cfg['treatment']} and the raw treated-control contrast clear the predeclared direction and magnitude gates.",
            "test": hid,
            "threshold": json.dumps(cfg["gate"], sort_keys=True),
        },
        "prior_confidence": 0.58,
        "disclosure": "This is a predictive panel screen, not a structural causal estimate.",
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {
            "period": [1970, 2025],
            "countries": ["GLOBAL"],
            "outcome_dim": cfg["outcome_dim"],
            "policy_family": cfg["policy_family"],
            "treatment_tags": [cfg["treatment"]],
        },
        "notes": f"Generated and runnable via engine/runs/{hid}/replication.py from local BIS/WDI vintages.",
    }
    path = out_dir / f"{hid}.yaml"
    path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" + yaml.safe_dump(doc, sort_keys=False, allow_unicode=False))
    return path


def write_steelman(hid: str, cfg: dict) -> Path:
    STEELMEN.mkdir(parents=True, exist_ok=True)
    path = STEELMEN / f"{hid}.md"
    path.write_text(
        f"# Steelman - {hid}\n\n"
        f"The strongest version of the claim is: {cfg['claim']}\n\n"
        "The skeptical case is that BIS macro-financial variables may proxy for omitted local policy, banking structure, terms-of-trade shocks, data revisions, or measurement breaks. "
        "A fair read treats this as a predictive warning-flag test rather than a complete causal design.\n"
    )
    return path


def write_run(hid: str, cfg: dict, d: pd.DataFrame, diag: dict, manifest: dict) -> list[Path]:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    diag_path = out_dir / "diagnostics.json"
    diag_path.write_text(json.dumps(diag, indent=2))
    written.append(diag_path)
    coef_df = pd.DataFrame([{
        "hypothesis_id": hid,
        "term": cfg["treatment"],
        "estimate": diag["coefficient"],
        "std_error": diag["standard_error_cluster_country"],
        "p_value": diag["p_value"],
        "ci95_low": diag["ci95"][0],
        "ci95_high": diag["ci95"][1],
        "n_observations": diag["n_observations"],
        "n_countries": diag["n_countries"],
    }])
    coef_path = out_dir / "coefficients.parquet"
    coef_df.to_parquet(coef_path, index=False)
    written.append(coef_path)
    chart = d.groupby(["year", cfg["treatment"]], as_index=False)[cfg["outcome"]].mean().rename(columns={cfg["outcome"]: "mean_outcome"})
    chart_path = out_dir / "chart_data.json"
    chart_path.write_text(json.dumps({"series": chart.to_dict("records")}, indent=2))
    written.append(chart_path)
    manifest_path = out_dir / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump({
        "hypothesis_id": hid,
        "run_utc": diag["run_utc"],
        "runner": diag["runner"],
        "formula": cfg["formula"],
        "vintages": manifest,
    }, sort_keys=False))
    written.append(manifest_path)
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import subprocess, sys\n\n"
        "ROOT = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_bis_batch01_credit_cycle_2026_05_12.py'), '{hid}']))\n"
    )
    wrapper_path = out_dir / "replication.py"
    wrapper_path.write_text(wrapper)
    written.append(wrapper_path)
    card = f"""# Result card - {hid}

**Verdict:** {diag['verdict_label']} - {diag['verdict_reason']}.

## Plain-English Claim

{cfg['claim']}

## What Was Measured

- Outcome: `{cfg['outcome']}`.
- Treatment: `{cfg['treatment']}`.
- Controls: {', '.join(f'`{c}`' for c in cfg['controls'])}.

## Results

- Usable panel: **{diag['n_observations']:,} observations**, **{diag['n_countries']} countries**.
- Coefficient on treatment: **{diag['coefficient']:.4f}** (SE {diag['standard_error_cluster_country']:.4f}, p={diag['p_value']:.4f}).
- Raw treated-control mean difference: **{diag['raw_treated_minus_control_mean']:.4f}**.
- Treated observations: **{diag['treated_count']:,}**.

## Specification

`{cfg['formula']}`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
"""
    card_path = out_dir / "result_card.md"
    card_path.write_text(card)
    written.append(card_path)
    return written


def run_one(hid: str, panel: pd.DataFrame, manifest: dict, overwrite: bool = False) -> tuple[dict, list[Path]]:
    cfg = CASES[hid]
    existing = [p for p in artifact_paths(hid, cfg) if p.exists()]
    if existing and not overwrite:
        diag = existing_diag(hid)
        if diag is None:
            return {
                "hypothesis_id": hid,
                "verdict_label": "INCONCLUSIVE_DATA_PENDING",
                "verdict_reason": "artifact path already exists without diagnostics; skipped to avoid overwriting concurrent work",
                "blocked": True,
                "blocker": "pre-existing artifacts without diagnostics",
            }, []
        diag["blocked"] = False
        diag["pre_existing_artifacts"] = True
        diag["verdict_reason"] = f"pre-existing artifact reused; {diag.get('verdict_reason', 'diagnostics present')}"
        return diag, []

    hyp_path = write_hypothesis(hid, cfg)
    steel_path = write_steelman(hid, cfg)
    d, diag = fit_case(hid, cfg, panel)
    written = [hyp_path, steel_path]
    written.extend(write_run(hid, cfg, d, diag, manifest))
    return diag, written


def write_audit(results: list[dict], written: list[Path]) -> None:
    tally = Counter(r["verdict_label"] for r in results)
    blocked = [r for r in results if r.get("blocked")]
    pre_existing = [r for r in results if r.get("pre_existing_artifacts")]
    lines = [
        "# BIS Batch 01 Credit-Cycle Results - 2026-05-12",
        "",
        "Runner: `scripts/promote_bis_batch01_credit_cycle_2026_05_12.py`.",
        "",
        "## Verdict Tally",
        "",
        "| Verdict | Count |",
        "|---|---:|",
    ]
    for verdict, count in sorted(tally.items()):
        lines.append(f"| `{verdict}` | {count} |")
    lines.extend([
        "",
        "## Results",
        "",
        "| Hypothesis | Verdict | Observations | Countries | Reason |",
        "|---|---|---:|---:|---|",
    ])
    for r in results:
        lines.append(
            f"| `{r['hypothesis_id']}` | `{r['verdict_label']}` | {r.get('n_observations', 0)} | {r.get('n_countries', 0)} | {r.get('verdict_reason', '')} |"
        )
    lines.extend(["", "## Pre-existing Artifacts Reused", ""])
    if pre_existing:
        for r in pre_existing:
            lines.append(f"- `{r['hypothesis_id']}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Blockers", ""])
    if blocked:
        for r in blocked:
            lines.append(f"- `{r['hypothesis_id']}`: {r.get('blocker', r.get('verdict_reason', 'blocked'))}.")
    else:
        lines.append("- None for data-ready execution. Two IDs were skipped because complete diagnostics already existed in the working tree.")
    lines.extend(["", "## Files Written", ""])
    for path in sorted({p.relative_to(ROOT) for p in written}):
        lines.append(f"- `{path}`")
    AUDIT.write_text("\n".join(lines) + "\n")


def main(argv: list[str]) -> int:
    overwrite = "--overwrite" in argv
    targets = [a for a in argv[1:] if not a.startswith("--")] or list(CASES)
    unknown = [hid for hid in targets if hid not in CASES]
    if unknown:
        raise KeyError(f"unknown Batch 01 cases: {unknown}")
    panel, manifest = build_panel()
    results: list[dict] = []
    written: list[Path] = []
    for hid in targets:
        diag, paths = run_one(hid, panel, manifest, overwrite=overwrite)
        results.append(diag)
        written.extend(paths)
    write_audit(results, written + [AUDIT])
    print(json.dumps([{"hypothesis_id": r["hypothesis_id"], "verdict": r["verdict_label"], "reason": r.get("verdict_reason", "")} for r in results], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
