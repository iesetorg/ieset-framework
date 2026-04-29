#!/usr/bin/env python3
"""Replication — Rule of law and institutional growth.

Spec:     hypotheses/institutional_quality/rule_of_law_institutional_growth.yaml
Steelman: hypotheses/steelman/rule_of_law_institutional_growth.md

Two-way fixed effects panel: regress 5-year-forward log GDP per capita growth on
WGI Rule of Law (RL) score plus controls (initial log GDP per capita, trade
openness, secondary school enrolment, WGI Government Effectiveness for the
attenuation robustness leg).

Falsification (need 2 of 3):
  panel_FE_beta(RL) > 0 at p<0.05, AND
  cross_section_beta(RL_mean) > 0 at p<0.05, AND
  RL coefficient attenuation when GE added < 70%.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "engine" / "runs" / "rule_of_law_institutional_growth"

COUNTRIES = [
    "ALB","ARG","AUS","AUT","BEL","BGD","BRA","CAN","CHE","CHL","CHN","COL","CZE",
    "DEU","DNK","EGY","ESP","EST","ETH","FIN","FRA","GBR","GHA","GRC","HUN","IDN",
    "IND","IRL","ISR","ITA","JPN","KAZ","KEN","KOR","LTU","LVA","MAR","MEX","MYS",
    "NGA","NLD","NOR","NZL","PAK","PER","PHL","POL","PRT","ROU","RUS","SGP","SVK",
    "SVN","SWE","THA","TUR","UKR","USA","VNM","ZAF",
]
PERIOD = (1996, 2023)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_long(path: Path, name: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def assemble():
    paths = {
        "gdp_pc":          ("world_bank_wdi", "NY.GDP.PCAP.KD"),
        "trade_openness":  ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "secondary_enr":   ("world_bank_wdi", "SE.SEC.ENRR"),
        "rule_of_law":     ("wgi", "GOV_WGI_RL.EST"),
        "gov_effective":   ("wgi", "GOV_WGI_GE.EST"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths.items():
        p = latest(pub, series)
        manifest[v] = {"publisher": pub, "series": series,
                       "vintage_file": str(p.relative_to(REPO_ROOT)),
                       "sha256": sha256(p)}
        frames.append(load_long(p, v))
    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")

    panel = panel[panel["country"].isin(COUNTRIES)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    panel["log_gdp_pc"] = np.log(panel["gdp_pc"])

    # 5-year-forward cumulative log growth
    panel["log_gdp_pc_t5"] = panel.groupby("country")["log_gdp_pc"].shift(-5)
    panel["growth_5yr_fwd"] = panel["log_gdp_pc_t5"] - panel["log_gdp_pc"]

    return panel, manifest


def fit_twfe(df, outcome, treatments, controls=None):
    controls = controls or []
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
    X = d[treatments + controls]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=True, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in treatments + controls:
        if t in res.params.index:
            out["coefs"][t] = {
                "estimate": float(res.params[t]),
                "se": float(res.std_errors[t]),
                "ci_lo": float(res.conf_int().loc[t, "lower"]),
                "ci_hi": float(res.conf_int().loc[t, "upper"]),
                "p": float(res.pvalues[t]),
                "t": float(res.tstats[t]),
            }
    return out


def cross_section_fit(df: pd.DataFrame) -> dict:
    """Country-mean cross-section: mean RL vs mean log GDP growth 1996-2023."""
    panel = df.copy()
    panel["log_gdp_pc"] = np.log(panel["gdp_pc"])
    panel["growth_yoy"] = panel.groupby("country")["log_gdp_pc"].diff()
    means = panel.groupby("country").agg(
        rl_mean=("rule_of_law", "mean"),
        ge_mean=("gov_effective", "mean"),
        growth_mean=("growth_yoy", "mean"),
        log_gdp_pc_initial=("log_gdp_pc", "first"),
        trade_mean=("trade_openness", "mean"),
        secondary_mean=("secondary_enr", "mean"),
    ).dropna()
    if means.shape[0] < 10:
        return {"error": "too few countries with complete data"}
    import statsmodels.api as sm
    X = sm.add_constant(means[["rl_mean", "log_gdp_pc_initial", "trade_mean", "secondary_mean"]])
    y = means["growth_mean"]
    res = sm.OLS(y, X).fit(cov_type="HC3")
    return {
        "n_countries": int(means.shape[0]),
        "rl_coef": float(res.params["rl_mean"]),
        "rl_se": float(res.bse["rl_mean"]),
        "rl_p": float(res.pvalues["rl_mean"]),
        "rl_t": float(res.tvalues["rl_mean"]),
        "r2": float(res.rsquared),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    # Spec 1: panel TWFE without GE
    spec1 = fit_twfe(panel, "growth_5yr_fwd",
                     ["rule_of_law"],
                     ["log_gdp_pc", "trade_openness", "secondary_enr"])

    # Spec 2: panel TWFE with GE (attenuation test)
    spec2 = fit_twfe(panel, "growth_5yr_fwd",
                     ["rule_of_law", "gov_effective"],
                     ["log_gdp_pc", "trade_openness", "secondary_enr"])

    # Cross-section spec
    cs = cross_section_fit(panel)

    # Falsification components
    rl1 = spec1["coefs"].get("rule_of_law", {})
    rl2 = spec2["coefs"].get("rule_of_law", {})

    panel_pass = rl1.get("estimate", 0) > 0 and rl1.get("p", 1) < 0.05
    cs_pass = (cs.get("rl_coef", 0) > 0) and (cs.get("rl_p", 1) < 0.05)

    if rl1.get("estimate", 0) != 0:
        attenuation = 1 - (rl2.get("estimate", 0) / rl1.get("estimate", 1))
    else:
        attenuation = 1.0
    attenuation_pass = abs(attenuation) < 0.70

    pass_count = int(panel_pass) + int(cs_pass) + int(attenuation_pass)
    if pass_count == 3:
        verdict = (f"SUPPORTED — strong; all 3 falsification legs pass: "
                   f"panel β_RL={rl1.get('estimate', 0):+.4f} (p={rl1.get('p', float('nan')):.3f}); "
                   f"cross-section β_RL={cs.get('rl_coef', float('nan')):+.4f} (p={cs.get('rl_p', float('nan')):.3f}); "
                   f"attenuation when GE added = {attenuation:+.0%}")
    elif pass_count >= 2:
        verdict = (f"SUPPORTED — 2 of 3 legs pass (threshold met): "
                   f"panel={'✓' if panel_pass else '✗'}, "
                   f"cross_section={'✓' if cs_pass else '✗'}, "
                   f"GE_attenuation_under_70%={'✓' if attenuation_pass else '✗'}; "
                   f"panel β_RL={rl1.get('estimate', 0):+.4f} p={rl1.get('p', float('nan')):.3f}")
    elif rl1.get("estimate", 0) < 0 and rl1.get("p", 1) < 0.05:
        verdict = (f"REFUTED — primary panel β_RL negative and significant "
                   f"(β={rl1.get('estimate', 0):+.4f}, p={rl1.get('p', float('nan')):.3f})")
    else:
        verdict = (f"PARTIAL — only {pass_count} of 3 legs pass falsification; "
                   f"panel β_RL={rl1.get('estimate', 0):+.4f} (p={rl1.get('p', float('nan')):.3f}); "
                   f"cross-section β_RL={cs.get('rl_coef', float('nan')):+.4f} (p={cs.get('rl_p', float('nan')):.3f})")

    # Coefficients table
    rows = []
    for spec_name, spec in [("primary_twfe_no_GE", spec1), ("twfe_with_GE", spec2)]:
        for t, c in spec.get("coefs", {}).items():
            rows.append({"spec": spec_name, "term": t, **c, "n_obs": spec["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "pass_count": pass_count,
        "primary_twfe": spec1,
        "twfe_with_GE": spec2,
        "cross_section": cs,
        "falsification_components": {
            "panel_FE_RL_positive_p05": panel_pass,
            "cross_section_RL_positive_p05": cs_pass,
            "attenuation_below_70pct": attenuation_pass,
            "attenuation_pct": attenuation,
        },
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "rule_of_law_institutional_growth",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # Result card
    lines = [
        "# Result card — Rule of law and institutional growth",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Primary spec (TWFE, country + year FE; no GE control)",
        "",
        "Outcome: 5-year-forward cumulative log GDP per capita growth.",
        "Treatment: WGI Rule of Law (RL.EST). Controls: log GDP per capita,",
        "trade openness, secondary school enrolment.",
        "",
        "| Term | Estimate | SE | 95% CI | p | t |",
        "|---|---:|---:|:---:|---:|---:|",
        f"| rule_of_law | {rl1.get('estimate', float('nan')):+.4f} | "
        f"{rl1.get('se', float('nan')):.4f} | "
        f"[{rl1.get('ci_lo', float('nan')):+.3f}, {rl1.get('ci_hi', float('nan')):+.3f}] | "
        f"{rl1.get('p', float('nan')):.3f} | {rl1.get('t', float('nan')):+.2f} |",
        "",
        f"n = {spec1['n_obs']} country-years, R² within = {spec1['r2_within']:.3f}",
        "",
        "## Robustness: TWFE with WGI Government Effectiveness added",
        "",
        "| Term | Estimate | SE | p |",
        "|---|---:|---:|---:|",
        f"| rule_of_law | {rl2.get('estimate', float('nan')):+.4f} | "
        f"{rl2.get('se', float('nan')):.4f} | "
        f"{rl2.get('p', float('nan')):.3f} |",
        f"| gov_effective | {spec2['coefs'].get('gov_effective', {}).get('estimate', float('nan')):+.4f} | "
        f"{spec2['coefs'].get('gov_effective', {}).get('se', float('nan')):.4f} | "
        f"{spec2['coefs'].get('gov_effective', {}).get('p', float('nan')):.3f} |",
        "",
        f"RL attenuation when GE added: {attenuation:+.0%} "
        f"({'below' if attenuation_pass else 'above'} 70% threshold).",
        "",
        "## Cross-section (country means)",
        "",
        f"n = {cs.get('n_countries', 'NA')} countries.",
        f"β_RL on mean annual log growth = {cs.get('rl_coef', float('nan')):+.4f} "
        f"(SE {cs.get('rl_se', float('nan')):.4f}, p {cs.get('rl_p', float('nan')):.3f}, "
        f"t {cs.get('rl_t', float('nan')):+.2f}). R² = {cs.get('r2', float('nan')):.3f}.",
        "",
        "## Falsification rule applied",
        "",
        "Spec requires at least 2 of 3 legs:",
        f"- Panel TWFE β_RL > 0 at p<0.05: **{'✓' if panel_pass else '✗'}**",
        f"- Cross-section β_RL > 0 at p<0.05: **{'✓' if cs_pass else '✗'}**",
        f"- Coefficient attenuation when GE added < 70%: **{'✓' if attenuation_pass else '✗'}** ({attenuation:+.0%})",
        "",
        f"Pass count: **{pass_count} / 3**.",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/rule_of_law_institutional_growth.md`. Key concerns:",
        "1. WGI subcomponents (RL, GE, CC, RQ) are highly collinear; identifying off",
        "   the non-overlapping component is fragile (Glaeser-La Porta 2004).",
        "2. Reverse causality: faster-growing countries may attract investment that",
        "   improves rule-of-law perceptions (which is what WGI measures).",
        "3. WGI is a perception index averaged across analyst sources, not an",
        "   institutional outcome measure; halo bias plausible.",
        "4. 5-year-forward growth windows shrink the sample at the panel ends.",
        "",
        "## Provenance",
        "",
        "Data: WDI NY.GDP.PCAP.KD, NE.TRD.GNFS.ZS, SE.SEC.ENRR; WGI RL.EST, GE.EST.",
        "See `manifest.yaml`. Reproduces from `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    # Console
    print(f"verdict: {verdict}")
    print(f"  panel β_RL: {rl1.get('estimate', float('nan')):+.4f} (p={rl1.get('p', float('nan')):.3f}, n={spec1['n_obs']})")
    print(f"  twfe+GE β_RL: {rl2.get('estimate', float('nan')):+.4f} (p={rl2.get('p', float('nan')):.3f}); attenuation {attenuation:+.0%}")
    print(f"  cross-section β_RL: {cs.get('rl_coef', float('nan')):+.4f} (p={cs.get('rl_p', float('nan')):.3f}, n={cs.get('n_countries', 'NA')})")
    print(f"  pass {pass_count}/3")


if __name__ == "__main__":
    sys.exit(main())
