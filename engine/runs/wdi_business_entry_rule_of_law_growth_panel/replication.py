#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"
WGI = ROOT / "data" / "vintages" / "wgi"
HYPOTHESIS_ID = "wdi_business_entry_rule_of_law_growth_panel"

SAMPLE_COUNTRIES = [
    "ALB", "ARG", "AUS", "AUT", "BEL", "BGD", "BRA", "CAN", "CHE", "CHL",
    "CHN", "COL", "CZE", "DEU", "DNK", "EGY", "ESP", "EST", "ETH", "FIN",
    "FRA", "GBR", "GHA", "GRC", "HUN", "IDN", "IND", "IRL", "ISR", "ITA",
    "JPN", "KAZ", "KEN", "KOR", "LTU", "LVA", "MAR", "MEX", "MYS", "NGA",
    "NLD", "NOR", "NZL", "PAK", "PER", "PHL", "POL", "PRT", "ROU", "RUS",
    "SGP", "SVK", "SVN", "SWE", "THA", "TUR", "UKR", "USA", "VNM", "ZAF",
]

GATE = {
    "interaction_coef_min": 0.25,
    "interaction_p_max": 0.10,
    "marginal_gap_min": 0.40,
    "min_observations": 700,
    "min_countries": 50,
}


def latest(root: Path, stem: str) -> Path:
    files = sorted(root.glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage: {root}/{stem}@*.parquet")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return None


def wdi_series(stem: str, name: str) -> tuple[pd.DataFrame, dict]:
    path = latest(WDI, stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].rename(
        columns={"country_iso3": "country", "value": name}
    )
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out = out[out["country"].astype(str).str.fullmatch(r"[A-Z]{3}")]
    out = out.dropna(subset=["country", "year", name])
    meta = {
        "publisher": "world_bank_wdi",
        "series_id": stem,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "rows": int(len(df)),
    }
    return out, meta


def wgi_rule_of_law() -> tuple[pd.DataFrame, dict]:
    path = latest(WGI, "RuleOfLaw")
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].rename(
        columns={"country_iso3": "country", "value": "rule_of_law"}
    )
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["rule_of_law"] = pd.to_numeric(out["rule_of_law"], errors="coerce")
    out = out[out["country"].astype(str).str.fullmatch(r"[A-Z]{3}")]
    out = out.dropna(subset=["country", "year", "rule_of_law"])
    meta = {
        "publisher": "wgi",
        "series_id": "GOV_WGI_RL.EST",
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "rows": int(len(df)),
    }
    return out, meta


def build_panel() -> tuple[pd.DataFrame, dict]:
    entry, entry_meta = wdi_series("IC.BUS.NREG", "new_business_registrations")
    pop, pop_meta = wdi_series("SP.POP.TOTL", "population")
    growth, growth_meta = wdi_series("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth")
    rule, rule_meta = wgi_rule_of_law()

    panel = (
        entry.merge(pop, on=["country", "year"], how="inner")
        .merge(rule, on=["country", "year"], how="inner")
        .merge(growth, on=["country", "year"], how="inner")
    )
    panel = panel[panel["country"].isin(SAMPLE_COUNTRIES)].copy()
    panel["year"] = panel["year"].astype(int)
    panel = panel.sort_values(["country", "year"])
    panel["business_entry_per_million"] = (
        panel["new_business_registrations"] / panel["population"] * 1_000_000
    )
    panel["log_business_entry_per_million"] = np.log1p(panel["business_entry_per_million"])
    panel["fwd_gdp_pc_growth_3y_avg"] = (
        panel.groupby("country")["gdp_pc_growth"].shift(-1)
        + panel.groupby("country")["gdp_pc_growth"].shift(-2)
        + panel.groupby("country")["gdp_pc_growth"].shift(-3)
    ) / 3
    panel = panel.replace([math.inf, -math.inf], np.nan).dropna(
        subset=[
            "fwd_gdp_pc_growth_3y_avg",
            "log_business_entry_per_million",
            "rule_of_law",
            "gdp_pc_growth",
        ]
    )
    return panel, {
        "IC.BUS.NREG": entry_meta,
        "SP.POP.TOTL": pop_meta,
        "NY.GDP.PCAP.KD.ZG": growth_meta,
        "GOV_WGI_RL.EST": rule_meta,
    }


def verdict_from(stats: dict) -> tuple[str, str]:
    enough = (
        stats["observations"] >= GATE["min_observations"]
        and stats["countries"] >= GATE["min_countries"]
    )
    effect = (
        stats["interaction_coef"] >= GATE["interaction_coef_min"]
        and stats["interaction_p"] <= GATE["interaction_p_max"]
    )
    magnitude = stats["marginal_gap_p75_vs_p25"] >= GATE["marginal_gap_min"]
    if not enough:
        return "inconclusive", "insufficient country-year coverage for the predeclared gate"
    if effect and magnitude:
        return "supported", "positive interaction clears p-value, magnitude, and coverage gates"
    if effect or magnitude:
        return "partial", "only one of the interaction or marginal-magnitude gates cleared"
    return "refuted", "interaction and model-implied marginal-magnitude gates failed"


def main() -> int:
    panel, sources = build_panel()
    formula = (
        "fwd_gdp_pc_growth_3y_avg ~ "
        "log_business_entry_per_million * rule_of_law + "
        "gdp_pc_growth + C(country) + C(year)"
    )
    fit = smf.ols(formula, data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel["country"]}
    )
    term = "log_business_entry_per_million:rule_of_law"
    interaction = float(fit.params[term])
    p_value = float(fit.pvalues[term])
    se = float(fit.bse[term])
    ci_low, ci_high = [float(x) for x in fit.conf_int().loc[term].tolist()]

    p25_rule = float(panel["rule_of_law"].quantile(0.25))
    p75_rule = float(panel["rule_of_law"].quantile(0.75))
    base_entry = float(fit.params["log_business_entry_per_million"])
    marginal_p25 = base_entry + interaction * p25_rule
    marginal_p75 = base_entry + interaction * p75_rule
    marginal_gap = marginal_p75 - marginal_p25

    high_rule = panel[panel["rule_of_law"] >= panel["rule_of_law"].median()]
    low_rule = panel[panel["rule_of_law"] < panel["rule_of_law"].median()]
    raw_high = float(
        smf.ols("fwd_gdp_pc_growth_3y_avg ~ log_business_entry_per_million", data=high_rule)
        .fit()
        .params["log_business_entry_per_million"]
    )
    raw_low = float(
        smf.ols("fwd_gdp_pc_growth_3y_avg ~ log_business_entry_per_million", data=low_rule)
        .fit()
        .params["log_business_entry_per_million"]
    )

    stats = {
        "observations": int(len(panel)),
        "countries": int(panel["country"].nunique()),
        "period": [int(panel["year"].min()), int(panel["year"].max())],
        "interaction_coef": interaction,
        "interaction_se": se,
        "interaction_p": p_value,
        "interaction_ci95": [ci_low, ci_high],
        "rule_of_law_p25": p25_rule,
        "rule_of_law_p75": p75_rule,
        "marginal_entry_effect_at_rule_p25": float(marginal_p25),
        "marginal_entry_effect_at_rule_p75": float(marginal_p75),
        "marginal_gap_p75_vs_p25": float(marginal_gap),
        "raw_entry_slope_low_rule_half": raw_low,
        "raw_entry_slope_high_rule_half": raw_high,
    }
    verdict, detail = verdict_from(stats)
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID,
        "generated_utc": generated_utc,
        "verdict": verdict,
        "verdict_detail": detail,
        "estimator": {
            "template": "panel_fe",
            "formula": formula,
            "fixed_effects": ["country", "year"],
            "clustering": "country",
        },
        "gate": GATE,
        "stats": stats,
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest = {
        "hypothesis_id": HYPOTHESIS_ID,
        "generated_utc": generated_utc,
        "sources": sources,
        "vintages": {
            key: {
                "publisher": item["publisher"],
                "series_id": item["series_id"],
                "vintage_file": item["vintage_file"],
                "sha256": item["sha256"],
                "rows": item["rows"],
            }
            for key, item in sources.items()
        },
        "derived_panel": {
            "rows_after_join": int(len(panel)),
            "countries_after_join": int(panel["country"].nunique()),
            "period": stats["period"],
            "keys": ["country", "year"],
            "notes": "Business registrations per million population; forward outcome uses t+1 through t+3 GDP-per-capita growth.",
        },
    }
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    evidence_packet = {
        "packet_version": 1,
        "generated_utc": generated_utc,
        "repository": {"root": str(ROOT), "git_commit": git_commit()},
        "hypothesis": {
            "id": HYPOTHESIS_ID,
            "path": "hypotheses/institutional_quality/wdi_business_entry_rule_of_law_growth_panel.yaml",
            "topic": "institutional_quality",
            "claim": "Business entry predicts stronger forward growth mainly where rule of law is higher.",
        },
        "verdict": {"raw": verdict.upper(), "bucket": verdict, "reason": detail},
        "preregistration": {
            "falsification_rule": "Interaction coefficient >= 0.25, p <= 0.10, marginal gap >= 0.40, at least 700 observations and 50 countries.",
            "threshold": GATE,
            "estimator": diagnostics["estimator"],
            "steelman": "hypotheses/steelman/wdi_business_entry_rule_of_law_growth_panel.md",
        },
        "reproduction": {
            "run_dir": "engine/runs/wdi_business_entry_rule_of_law_growth_panel",
            "replication_script": "engine/runs/wdi_business_entry_rule_of_law_growth_panel/replication.py",
            "suggested_command": "python3 engine/runs/wdi_business_entry_rule_of_law_growth_panel/replication.py",
        },
        "data": {"inputs": list(sources.values())},
        "results": stats,
    }
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(evidence_packet, sort_keys=False))

    result_card = f"""# Result Card - {HYPOTHESIS_ID}

Verdict: **{verdict.upper()}** ({detail}).

## Design

- Claim: business-entry intensity predicts stronger three-year forward GDP-per-capita growth mainly where WGI rule of law is higher.
- Data: local WDI new business registrations, population, GDP-per-capita growth, and WGI rule-of-law vintages listed in `manifest.yaml`.
- Sample: {stats["observations"]} country-years, {stats["countries"]} countries, {stats["period"][0]}-{stats["period"][1]} after forward-outcome construction.
- Estimator: OLS panel FE with country and year fixed effects, clustered by country.

## Primary Result

- Interaction coefficient: {interaction:.3f}
- Clustered p-value: {p_value:.3f}
- 95% CI: [{ci_low:.3f}, {ci_high:.3f}]
- Model-implied marginal entry effect at rule-of-law p25 ({p25_rule:.3f}): {marginal_p25:.3f}
- Model-implied marginal entry effect at rule-of-law p75 ({p75_rule:.3f}): {marginal_p75:.3f}
- P75-minus-p25 marginal gap: {marginal_gap:.3f}

## Caveats

This is an associational screen. Business-registration counts can move because of filing reforms, formalisation drives, tax incentives, or shell-firm behavior. The result should not be scored as causal evidence without a richer design.
"""
    (RUN_DIR / "result_card.md").write_text(result_card)
    print(json.dumps({"verdict": verdict, "stats": stats}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
