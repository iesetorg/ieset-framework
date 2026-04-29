#!/usr/bin/env python3
"""Replication — GDPR digital-sector firm-scale effect.

Spec:     hypotheses/regulatory/gdpr_digital_sector_firm_scale_effect.yaml
Estimator: panel_fe (linearmodels TWFE).

v1 weak: firm-level Crunchbase / PitchBook outcomes are commercial and not on
disk. We run the sector-aggregate proxy version flagged in the YAML's "weaker
v1" path (notes line 165): outcome = log GVA per hour and log EMP in ISIC J
(information & communication) from OECD PDB. EU members vs non-EU controls,
treatment = post-2018 (GDPR enforcement May 2018) + nested post-2022
(DMA/DSA application).

Limitation: this measures sectoral productivity & employment, not firm-scale
distribution. Firm-scale (revenue per firm, scale-up rate, VC per firm) is the
hypothesis's true target and remains v1.1-blocked on commercial firm-level data.
"""
from __future__ import annotations
import json, sys, warnings, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "gdpr_digital_sector_firm_scale_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

EU_MEMBERS = ["DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "POL", "SWE", "IRL", "AUT",
              "DNK", "FIN", "PRT", "GRC", "CZE", "HUN", "SVK", "SVN", "EST", "LVA",
              "LTU", "LUX"]
NON_EU = ["USA", "GBR", "CAN", "AUS", "JPN", "KOR", "CHE", "NOR", "NZL"]
ALL = EU_MEMBERS + NON_EU
PERIOD = (2010, 2024)


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def latest(pub, pattern):
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(pattern), key=lambda x: x.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{pattern}")
    return files[-1]


def load_wdi(series, name):
    p = latest("world_bank_wdi", f"{series}@*.parquet")
    t = pq.read_table(p).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.rename(columns={"value": name, "country_iso3": "country"})
    return out, str(p.relative_to(REPO_ROOT)), sha256(p)


def load_pdb_sector(measure, activity, price_base="LR"):
    p = latest("oecd", "OECD.SDD.TPS_DSD_PDB_DF_PDB_2.0@*.parquet")
    df = pq.read_table(p).to_pandas()
    sub = df[(df["MEASURE"] == measure) & (df["ACTIVITY"] == activity) &
             (df["TRANSFORMATION"] == "N")].copy()
    if price_base is not None:
        sub = sub[sub["PRICE_BASE"] == price_base]
    sub = sub.rename(columns={"REF_AREA": "country", "period": "year", "value": "v"})
    sub["year"] = sub["year"].astype(int)
    sub["v"] = pd.to_numeric(sub["v"], errors="coerce")
    return sub[["country", "year", "v"]].dropna(), str(p.relative_to(REPO_ROOT)), sha256(p)


def assemble():
    manifest = {}
    # ICT (NACE J / ISIC J) labour productivity (GVA per hour, real)
    j_lp, vp1, hp1 = load_pdb_sector("GVAHRS", "J", "LR")
    j_lp = j_lp.rename(columns={"v": "ict_lp"})
    manifest["ict_labour_productivity"] = {"file": vp1, "sha256": hp1,
                                           "definition": "OECD PDB GVAHRS, ACTIVITY=J, real LR USD-PPP per hour"}
    # ICT employment (persons, thousands)
    j_emp, vp2, hp2 = load_pdb_sector("EMP", "J", price_base=None)
    j_emp = j_emp.rename(columns={"v": "ict_emp"})
    manifest["ict_employment"] = {"file": vp2, "sha256": hp2}
    # Total economy employment for share denominator
    t_emp, vp3, hp3 = load_pdb_sector("EMP", "_T", price_base=None)
    t_emp = t_emp.rename(columns={"v": "tot_emp"})
    manifest["total_employment"] = {"file": vp3, "sha256": hp3}

    pop, vp4, hp4 = load_wdi("SP.POP.TOTL", "population")
    manifest["population"] = {"file": vp4, "sha256": hp4}
    gdp, vp5, hp5 = load_wdi("NY.GDP.PCAP.PP.KD", "gdp_pc_ppp")
    manifest["gdp_pc_ppp"] = {"file": vp5, "sha256": hp5}

    df = j_lp.merge(j_emp, on=["country", "year"], how="outer") \
             .merge(t_emp, on=["country", "year"], how="outer") \
             .merge(pop, on=["country", "year"], how="left") \
             .merge(gdp, on=["country", "year"], how="left")
    df = df[df["country"].isin(ALL)]
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])]

    df["log_ict_lp"] = np.log(df["ict_lp"])
    df["log_ict_emp"] = np.log(df["ict_emp"])
    df["ict_emp_share"] = df["ict_emp"] / df["tot_emp"]
    df["log_population"] = np.log(df["population"])
    df["log_gdp_pc"] = np.log(df["gdp_pc_ppp"])
    df["is_eu"] = df["country"].isin(EU_MEMBERS).astype(int)
    df["eu_post_2018"] = ((df["is_eu"] == 1) & (df["year"] >= 2018)).astype(int)
    df["eu_post_2022"] = ((df["is_eu"] == 1) & (df["year"] >= 2022)).astype(int)
    return df.reset_index(drop=True), manifest


def fit(df, outcome, treatments, controls, label):
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
    if d.empty:
        return {"label": label, "n_obs": 0, "coefs": {}, "error": "empty after dropna"}
    X = d[treatments + controls]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=True, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    out = {"label": label, "n_obs": int(res.nobs),
           "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in treatments:
        if t in res.params.index:
            ci = res.conf_int().loc[t]
            out["coefs"][t] = {
                "estimate": float(res.params[t]),
                "se": float(res.std_errors[t]),
                "ci_lo": float(ci["lower"]),
                "ci_hi": float(ci["upper"]),
                "p": float(res.pvalues[t]),
                "t": float(res.tstats[t]),
            }
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df, manifest = assemble()

    # Three outcomes: log ICT labour productivity, log ICT employment, ICT employment share
    spec_lp = fit(df, "log_ict_lp", ["eu_post_2018"],
                  ["log_population", "log_gdp_pc"], "ict_lp_post_2018")
    spec_emp = fit(df, "log_ict_emp", ["eu_post_2018"],
                   ["log_population", "log_gdp_pc"], "ict_emp_post_2018")
    spec_share = fit(df, "ict_emp_share", ["eu_post_2018"],
                     ["log_population", "log_gdp_pc"], "ict_share_post_2018")

    # Cumulative DMA/DSA
    cum_lp = fit(df, "log_ict_lp", ["eu_post_2018", "eu_post_2022"],
                 ["log_population", "log_gdp_pc"], "ict_lp_cumulative")

    # Placebo at fake 2014
    df_pl = df.copy()
    df_pl["eu_post_2014"] = ((df_pl["is_eu"] == 1) & (df_pl["year"] >= 2014) & (df_pl["year"] < 2018)).astype(int)
    df_pl = df_pl[df_pl["year"] < 2018]
    placebo = fit(df_pl, "log_ict_lp", ["eu_post_2014"],
                  ["log_population", "log_gdp_pc"], "placebo_pre_2018")

    b_lp = spec_lp["coefs"].get("eu_post_2018", {})
    b_emp = spec_emp["coefs"].get("eu_post_2018", {})
    b_sh = spec_share["coefs"].get("eu_post_2018", {})
    pl_b = placebo["coefs"].get("eu_post_2014", {})

    # Hypothesis predicts firm-scale ↓; sector-aggregate productivity may rise
    # (compositional: smaller firms exit, surviving firms more productive) or fall.
    # We report direction-honest, not direction-imposed.
    n_neg_at_p10 = sum(int(c.get("estimate", 0) < 0 and abs(c.get("t", 0)) >= 1.645)
                       for c in [b_lp, b_emp, b_sh])
    placebo_clean = abs(pl_b.get("t", 0)) < 1.65

    if n_neg_at_p10 >= 2 and placebo_clean:
        verdict = (f"WEAKLY SUPPORTED (sectoral proxy) — {n_neg_at_p10} of 3 ICT outcomes "
                   f"show EU-post-2018 negative differential at p<0.10; placebo clean. "
                   f"Note: sector-aggregate is not the hypothesis's primary target.")
    elif any(c.get("estimate", 0) < 0 and abs(c.get("t", 0)) >= 1.645 for c in [b_lp, b_emp, b_sh]):
        verdict = (f"INCONCLUSIVE — only {n_neg_at_p10} ICT outcome(s) negative & significant; "
                   f"firm-scale specific test (Crunchbase) still required.")
    else:
        verdict = (f"NOT SUPPORTED at sectoral aggregate — none of (ICT log GVA-per-hour, "
                   f"ICT log emp, ICT emp share) shows EU-post-2018 negative differential at p<0.10. "
                   f"This is the falsification path flagged in the YAML notes — sector aggregate "
                   f"may mask firm-scale-distribution effects, which need v1.1 commercial firm data.")

    falsification_rule = (
        "Hypothesis target outcomes (firm-revenue, scale-up rate, VC per firm) are "
        "data-gated on commercial Crunchbase / PitchBook. v1 weak proxy uses sector-"
        "aggregate ICT GVA-per-hour, employment, and employment share. Falsification: "
        "non-negative β on at least 2 of 3 outcomes at p<0.10, OR placebo flags pre-trend."
    )

    diag = {
        "verdict": verdict,
        "spec_ict_lp": spec_lp,
        "spec_ict_emp": spec_emp,
        "spec_ict_share": spec_share,
        "cumulative_dma_dsa": cum_lp,
        "placebo_pre_2018": placebo,
        "n_eu_in_panel": int(df.dropna(subset=["log_ict_lp"])[df["is_eu"] == 1]["country"].nunique()),
        "n_non_eu_in_panel": int(df.dropna(subset=["log_ict_lp"])[df["is_eu"] == 0]["country"].nunique()),
        "period": list(PERIOD),
        "n_negative_at_p10": n_neg_at_p10,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "estimator": "panel_fe_twfe_sector_proxy",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "treated_set": "EU members",
        "control_set": NON_EU,
        "treatment_year": 2018,
        "v1_caveat": "weak sector-aggregate proxy; firm-level outcomes data-gated on commercial sources",
        "vintages": manifest,
    }, sort_keys=False))

    lines = [
        f"# Result card — {RUN_ID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"**Estimator:** panel_fe (TWFE, country + year FE, country-clustered SE)  ",
        f"**Period:** {PERIOD[0]}-{PERIOD[1]}  ",
        f"**Outcomes (sector proxy):** OECD PDB ICT-sector (ACTIVITY=J) GVA per hour, employment, employment share  ",
        "",
        "## Sector-aggregate specs (EU × post-2018)",
        "",
        "| Outcome | β | SE | 95% CI | p | t | n |",
        "|---|---:|---:|:---:|---:|---:|---:|",
        f"| log_ict_lp (GVA/hr) | {b_lp.get('estimate', float('nan')):+.4f} | {b_lp.get('se', float('nan')):.4f} | "
        f"[{b_lp.get('ci_lo', float('nan')):+.3f},{b_lp.get('ci_hi', float('nan')):+.3f}] | "
        f"{b_lp.get('p', float('nan')):.3f} | {b_lp.get('t', float('nan')):+.2f} | {spec_lp['n_obs']} |",
        f"| log_ict_emp | {b_emp.get('estimate', float('nan')):+.4f} | {b_emp.get('se', float('nan')):.4f} | "
        f"[{b_emp.get('ci_lo', float('nan')):+.3f},{b_emp.get('ci_hi', float('nan')):+.3f}] | "
        f"{b_emp.get('p', float('nan')):.3f} | {b_emp.get('t', float('nan')):+.2f} | {spec_emp['n_obs']} |",
        f"| ict_emp_share | {b_sh.get('estimate', float('nan')):+.4f} | {b_sh.get('se', float('nan')):.4f} | "
        f"[{b_sh.get('ci_lo', float('nan')):+.3f},{b_sh.get('ci_hi', float('nan')):+.3f}] | "
        f"{b_sh.get('p', float('nan')):.3f} | {b_sh.get('t', float('nan')):+.2f} | {spec_share['n_obs']} |",
        "",
        "## Cumulative DMA/DSA (EU × post-2022 incremental)",
        "",
    ]
    for term, c in cum_lp["coefs"].items():
        lines.append(f"- **{term}** on log_ict_lp: β={c['estimate']:+.4f} (p={c['p']:.3f})")
    lines += [
        "",
        f"## Placebo (fake EU × post-2014, pre-2018 sample)",
        f"",
        f"- β_placebo on log_ict_lp = {pl_b.get('estimate', float('nan')):+.4f} "
        f"(p={pl_b.get('p', float('nan')):.3f}); "
        f"placebo {'CLEAN' if placebo_clean else 'NOT CLEAN'}.",
        "",
        "## Falsification rule",
        falsification_rule,
        "",
        "## Caveats",
        "",
        "- This is the YAML's explicitly-flagged WEAK v1: sector-aggregate ICT outcomes ",
        "  do not test firm-scale distribution (the hypothesis's true target). v1.1 needs ",
        "  Crunchbase/PitchBook firm-level data.",
        "- Sectoral productivity rising AND employment falling is consistent with smaller-",
        "  firm exit + surviving-firm scale, which the firm-level test would distinguish.",
        "- Capital-market depth (EU VC thinness pre-dates GDPR) is not controlled here.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")
    print(f"verdict: {verdict}")
    print(f"  log_ict_lp:    β={b_lp.get('estimate', float('nan')):+.4f} p={b_lp.get('p', float('nan')):.3f}")
    print(f"  log_ict_emp:   β={b_emp.get('estimate', float('nan')):+.4f} p={b_emp.get('p', float('nan')):.3f}")
    print(f"  ict_emp_share: β={b_sh.get('estimate', float('nan')):+.4f} p={b_sh.get('p', float('nan')):.3f}")


if __name__ == "__main__":
    sys.exit(main())
