#!/usr/bin/env python3
"""Replication — Spain Sánchez economic trajectory 2018-2023.

Spec:     hypotheses/growth/spain_sanchez_economic_trajectory_2018_2023.yaml
Steelman: hypotheses/steelman/spain_sanchez_economic_trajectory_2018_2023.md

Multi-outcome TWFE: ESP vs euro-area donor pool 2005-2023. Treatment indicator
spain_post_2018. ESP is single treated country; use donor-country dummies + time FE.

Outcomes by data availability in local vintages:
  - log GDP pc PPP (WDI NY.GDP.PCAP.PP.KD) — primary
  - unemployment rate harmonised (Eurostat une_rt_a, Y15-74 PC_ACT)
  - real house-price-to-income index (proxy: Eurostat prc_hpi_a I15_A_AVG
    deflated by GDP pc PPP per the YAML; YAML's preferred OECD source URN
    is unverified)

Definition-controlled sub-analysis: report β separately for each outcome
to test the YAML's pre-registered DIFFERENTIATED pattern (zero/positive on
output, negative on housing). The YAML treats uniform direction in either
sense as falsification. The "definition-controlled" framing in the task
description refers to OUTCOME differentiation (not a definitional shift like
the LO 10/2022 hypothesis), so we report each outcome with its own coefficient
and pattern verdict.

Eurostat employment_rate_15_64 (lfsi_emp_a) is not present in vintages and
real_wage_index (OECD earnings) lacks adequate coverage; both are dropped from
v1 with the limitation flagged.
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
OUT_DIR = REPO_ROOT / "engine" / "runs" / "spain_sanchez_economic_trajectory_2018_2023"

TREATED = "ESP"
DONORS = ["FRA", "ITA", "PRT", "GRC", "DEU", "NLD", "BEL"]  # IRL excluded baseline
ALL = [TREATED] + DONORS
PERIOD = (2005, 2023)

# Eurostat geo codes mapping
EU_TO_ISO3 = {
    "ES": "ESP", "FR": "FRA", "IT": "ITA", "PT": "PRT", "EL": "GRC",
    "DE": "DEU", "NL": "NLD", "BE": "BEL", "IE": "IRL",
}


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


def load_wdi(path, name):
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def load_eurostat_unemp(path):
    t = pq.read_table(path).to_pandas()
    # Filter: total (sex T), 15-74, % of active pop
    t = t[(t["age"] == "Y15-74") & (t["sex"] == "T") & (t["unit"] == "PC_ACT")]
    t["country"] = t["geo_code"].map(EU_TO_ISO3)
    t = t.dropna(subset=["country"])
    out = t[["country", "period", "value"]].rename(columns={"period": "year", "value": "unemployment_rate"})
    out["year"] = out["year"].astype(int)
    out["unemployment_rate"] = pd.to_numeric(out["unemployment_rate"], errors="coerce")
    return out


def load_eurostat_hpi(path):
    """Eurostat house-price index: prefer DW_EXST (existing dwellings) I15_A_AVG."""
    t = pq.read_table(path).to_pandas()
    t = t[(t["purchase"] == "TOTAL") & (t["unit"] == "I15_A_AVG")] if "purchase" in t.columns else t
    if t.shape[0] == 0:
        # fallback to DW_EXST
        t = pq.read_table(path).to_pandas()
        t = t[(t["purchase"] == "DW_EXST") & (t["unit"] == "I15_A_AVG")]
    t["country"] = t["geo_code"].map(EU_TO_ISO3)
    t = t.dropna(subset=["country"])
    out = t[["country", "period", "value"]].rename(columns={"period": "year", "value": "house_price_index"})
    out["year"] = out["year"].astype(int)
    out["house_price_index"] = pd.to_numeric(out["house_price_index"], errors="coerce")
    return out


def assemble():
    paths_wdi = {
        "gdp_pc_ppp":     ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "population":     ("world_bank_wdi", "SP.POP.TOTL"),
        "trade_openness": ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths_wdi.items():
        p = latest(pub, series)
        manifest[v] = {"publisher": pub, "series": series,
                       "vintage_file": str(p.relative_to(REPO_ROOT)),
                       "sha256": sha256(p)}
        frames.append(load_wdi(p, v))
    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")

    # Eurostat unemployment
    p_unemp = latest("eurostat", "une_rt_a")
    manifest["unemployment_rate"] = {"publisher": "eurostat", "series": "une_rt_a",
                                     "vintage_file": str(p_unemp.relative_to(REPO_ROOT)),
                                     "sha256": sha256(p_unemp)}
    panel = panel.merge(load_eurostat_unemp(p_unemp), on=["country", "year"], how="outer")

    # Eurostat house price index
    p_hpi = latest("eurostat", "prc_hpi_a")
    manifest["house_price_index"] = {"publisher": "eurostat", "series": "prc_hpi_a",
                                     "vintage_file": str(p_hpi.relative_to(REPO_ROOT)),
                                     "sha256": sha256(p_hpi)}
    panel = panel.merge(load_eurostat_hpi(p_hpi), on=["country", "year"], how="outer")

    panel = panel[panel["country"].isin(ALL)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["log_population"] = np.log(panel["population"])
    panel["log_house_price_index"] = np.log(panel["house_price_index"])
    # housing affordability proxy: log(HPI) - log(real GDP per capita)
    # higher value = housing more expensive relative to income
    panel["log_house_price_to_gdp_pc"] = panel["log_house_price_index"] - panel["log_gdp_pc_ppp"]
    panel["spain_post_2018"] = ((panel["country"] == TREATED) & (panel["year"] >= 2018)).astype(int)
    return panel, manifest


def fit(df, outcome, treatments, controls=None):
    controls = controls or []
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
    for c in DONORS[1:]:
        d[f"donor_{c}"] = (d.index.get_level_values("country") == c).astype(float)
    donor_cols = [f"donor_{c}" for c in DONORS[1:]]
    X = d[donor_cols + treatments + controls]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=False, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in treatments:
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    res = {}
    for outcome in ["log_gdp_pc_ppp", "unemployment_rate",
                    "log_house_price_index", "log_house_price_to_gdp_pc"]:
        try:
            res[outcome] = fit(panel, outcome, ["spain_post_2018"],
                               ["log_population"])
        except Exception as e:
            res[outcome] = {"error": str(e), "coefs": {}}

    def b(o): return res.get(o, {}).get("coefs", {}).get("spain_post_2018", {})

    # Pre-registered pattern: NON-NEG on output, NEG on housing-affordability
    bg = b("log_gdp_pc_ppp")
    bu = b("unemployment_rate")  # lower unemployment = better; β_neg means good
    bh = b("log_house_price_index")  # housing prices alone
    ba = b("log_house_price_to_gdp_pc")  # housing-to-income (negative=good aff)

    output_nonneg = bg.get("estimate", 0) >= 0
    output_p = bg.get("p", 1.0) < 0.10
    aff_neg_supported = ba.get("estimate", 0) > 0 and ba.get("p", 1.0) < 0.10
    # ↑ a positive β on log(HPI/GDPpc) = housing got more expensive relative to income
    # which IS the negative-housing-trajectory finding the YAML expects

    pattern_match = output_nonneg and aff_neg_supported

    if pattern_match:
        verdict = (
            f"SUPPORTED — pre-registered differentiated pattern holds. "
            f"Output (log GDP pc PPP) β_spain_post_2018 = {bg.get('estimate', 0):+.3f} "
            f"(p={bg.get('p', 1):.3f}, non-negative as expected); housing affordability "
            f"(log HPI / GDP pc) β = {ba.get('estimate', 0):+.3f} "
            f"(p={ba.get('p', 1):.3f}, positive = worse affordability as expected). "
            f"Spain's 2018-onward trajectory is fine on aggregate output but materially "
            f"worse on housing affordability. Note: employment_rate_15_64 outcome dropped "
            f"due to data unavailability; unemployment-rate stand-in β = "
            f"{bu.get('estimate', 0):+.3f} (lower=better)."
        )
    elif bg.get("estimate", 0) < 0 and bg.get("p", 1.0) < 0.10 and ba.get("estimate", 0) > 0:
        verdict = (
            f"REFUTED — Spain is uniformly negative including on output "
            f"(β_gdp_pc = {bg.get('estimate', 0):+.3f}, p={bg.get('p', 1):.3f}); "
            f"the differentiated pattern is not supported. The 'Sánchez = aggregate "
            f"economic decline' framing IS data-supported, contrary to YAML prior."
        )
    elif output_nonneg and not aff_neg_supported:
        verdict = (
            f"PARTIAL — output side supported (β_gdp_pc = {bg.get('estimate', 0):+.3f}, "
            f"p={bg.get('p', 1):.3f}, non-negative) but housing-affordability side not "
            f"distinguishable (β_hpi/gdppc = {ba.get('estimate', 0):+.3f}, "
            f"p={ba.get('p', 1):.3f}). Critics' housing concern not data-supported here."
        )
    else:
        verdict = (
            f"PARTIAL — pattern does not cleanly match either uniform direction. "
            f"output β = {bg.get('estimate', 0):+.3f} p={bg.get('p', 1):.3f}; "
            f"housing-affordability β = {ba.get('estimate', 0):+.3f} p={ba.get('p', 1):.3f}."
        )

    rows = []
    for o, r in res.items():
        for t, c in r.get("coefs", {}).items():
            rows.append({"spec": f"twfe_{o}", "term": t, **c, "n_obs": r.get("n_obs", 0)})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "results_by_outcome": res,
        "pattern_match_nonneg_output_negative_housing": pattern_match,
        "missing_outcomes_v1": ["employment_rate_15_64 (lfsi_emp_a not in vintages)",
                                 "real_wage_index (OECD DF_EARN not in vintages)",
                                 "real_house_price_to_income (OECD URN not in vintages — using HPI/GDPpc proxy)"],
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "spain_sanchez_economic_trajectory_2018_2023",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    lines = [
        "# Result card — Spain Sánchez economic trajectory 2018-2023",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Multi-outcome TWFE (definition-controlled sub-analyses)",
        "",
        "Each outcome reports β_spain_post_2018 separately to test the pre-registered",
        "DIFFERENTIATED pattern (non-negative on output, negative on housing-affordability).",
        "",
        "| Outcome | β | SE | 95% CI | p | t | n |",
        "|---|---:|---:|:---:|---:|---:|---:|",
    ]
    for o, label in [
        ("log_gdp_pc_ppp", "log GDP pc PPP (output — expect ≥0)"),
        ("unemployment_rate", "unemployment rate (lower=better)"),
        ("log_house_price_index", "log house-price index (raw)"),
        ("log_house_price_to_gdp_pc", "log HPI / log GDP pc (affordability — expect >0 = worse)"),
    ]:
        bb = b(o)
        n = res.get(o, {}).get("n_obs", 0)
        lines.append(
            f"| {label} | {bb.get('estimate', float('nan')):+.4f} | "
            f"{bb.get('se', float('nan')):.4f} | "
            f"[{bb.get('ci_lo', float('nan')):+.3f}, {bb.get('ci_hi', float('nan')):+.3f}] | "
            f"{bb.get('p', float('nan')):.3f} | {bb.get('t', float('nan')):+.2f} | {n} |"
        )

    lines += [
        "",
        f"Donor pool: {', '.join(DONORS)}. IRL excluded from baseline (FDI distortion).",
        "",
        "## Missing v1 outcomes (data-gated)",
        "",
        "- employment_rate_15_64 — Eurostat lfsi_emp_a not in local vintages",
        "- real_wage_index — OECD DF_EARN not in local vintages",
        "- OECD analytical real house-price-to-income — URN unverified, not in vintages",
        "",
        "Substituted: log(Eurostat HPI) / log(WDI GDP pc PPP) as a housing-affordability",
        "proxy. The proxy is upper-bound conservative because it uses national-average",
        "GDP per capita rather than household disposable income (which grew slower in",
        "Spain than GDP per capita).",
        "",
        "## Steelman concerns",
        "",
        "1. Donor pool is euro-area-only by design; pure monetary-regime confound absorbed.",
        "2. 2018 cutoff covers Sánchez but year FE absorb COVID + energy + ECB shocks common to euro-area.",
        "3. Housing-affordability mechanism may be Spain-supply-constraint (tourism, short-let, Madrid-Barcelona concentration) rather than Sánchez-policy-content.",
        "4. The HPI/GDPpc proxy is a coarser measure than OECD's real-house-price-to-income; sign should be informative even if magnitude is biased.",
        "",
        "## Provenance",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict[:160]}...")
    for o in ["log_gdp_pc_ppp", "unemployment_rate", "log_house_price_index", "log_house_price_to_gdp_pc"]:
        bb = b(o)
        print(f"  {o}: β={bb.get('estimate', float('nan')):+.4f} p={bb.get('p', float('nan')):.3f}")


if __name__ == "__main__":
    sys.exit(main())
