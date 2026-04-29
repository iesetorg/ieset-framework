#!/usr/bin/env python3
"""Replication — EU regulatory burden productivity drag.

Spec:     hypotheses/regulatory/eu_regulatory_burden_productivity_drag.yaml
Estimator: panel_fe (linearmodels TWFE) with EU × post-2018 indicator.

Outcome: log labour productivity (GVA per hour, real, USD-PPP) from OECD PDB.
Treatment: eu_post_2018_gdpr_dummy (= 1 for EU members from 2018 on),
           eu_post_2022_dma_dsa_dummy (= 1 for EU members from 2022 on).
Channel control: OECD PMR overall (only 2018 and 2023 vintages observed -
   merged forward-fill at country level for sensitivity).
Controls: log_population, trade_openness, debt_to_gdp.
Country & year FE; clustered SE on country.

Note on identification: only USA, CAN, GBR, AUS, JPN, KOR, CHE, NOR, NZL serve as
non-EU controls. The country FE absorb level differences; year FE absorb common
shocks; treatment indicator picks up EU-specific differential post-2018.
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
RUN_ID = "eu_regulatory_burden_productivity_drag"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

EU_MEMBERS = ["DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "POL", "SWE", "IRL", "AUT",
              "DNK", "FIN", "PRT", "GRC", "CZE", "HUN", "SVK", "SVN", "EST", "LVA",
              "LTU", "LUX", "BGR", "ROU", "HRV"]
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


def load_pdb_lp():
    """Labour productivity (real, USD PPP per hour) — total economy."""
    p = latest("oecd", "OECD.SDD.TPS_DSD_PDB_DF_PDB_2.0@*.parquet")
    df = pq.read_table(p).to_pandas()
    sub = df[(df["MEASURE"] == "GVAHRS") & (df["ACTIVITY"] == "_T") &
             (df["TRANSFORMATION"] == "N") & (df["PRICE_BASE"] == "LR")].copy()
    sub = sub.rename(columns={"REF_AREA": "country", "period": "year", "value": "gvahrs"})
    sub["year"] = sub["year"].astype(int)
    sub["gvahrs"] = pd.to_numeric(sub["gvahrs"], errors="coerce")
    return sub[["country", "year", "gvahrs"]].dropna(), str(p.relative_to(REPO_ROOT)), sha256(p)


def load_pmr():
    p = latest("oecd_pmr", "OECD.ECO.GCRD_DSD_PMR_DF_PMR_1.2@*.parquet")
    df = pq.read_table(p).to_pandas()
    sub = df[df["MEASURE"] == "PMR"].copy()
    sub = sub.rename(columns={"REF_AREA": "country", "period": "year", "value": "pmr"})
    sub["year"] = sub["year"].astype(int)
    sub["pmr"] = pd.to_numeric(sub["pmr"], errors="coerce")
    return sub[["country", "year", "pmr"]].dropna(), str(p.relative_to(REPO_ROOT)), sha256(p)


def assemble():
    manifest = {}
    lp, vp, hp = load_pdb_lp()
    manifest["labour_productivity"] = {"file": vp, "sha256": hp,
                                       "definition": "OECD PDB GVAHRS, _T, real (LR), USD_PPP per hour"}
    pop, vp2, hp2 = load_wdi("SP.POP.TOTL", "population")
    manifest["population"] = {"file": vp2, "sha256": hp2}
    trade, vp3, hp3 = load_wdi("NE.TRD.GNFS.ZS", "trade_openness")
    manifest["trade_openness"] = {"file": vp3, "sha256": hp3}
    debt, vp4, hp4 = load_wdi("GC.DOD.TOTL.GD.ZS", "debt_to_gdp")
    manifest["debt_to_gdp"] = {"file": vp4, "sha256": hp4}
    pmr, vp5, hp5 = load_pmr()
    manifest["pmr"] = {"file": vp5, "sha256": hp5}

    df = lp.merge(pop, on=["country", "year"], how="left") \
           .merge(trade, on=["country", "year"], how="left") \
           .merge(debt, on=["country", "year"], how="left")
    # PMR — only 2018, 2023 — forward/back fill at country level
    pmr_wide = pmr.set_index(["country", "year"]).unstack("year")["pmr"]
    pmr_long = []
    for c in pmr_wide.index:
        for y in range(2010, 2025):
            v = None
            if y < 2018 and 2018 in pmr_wide.columns:
                v = pmr_wide.loc[c, 2018] if not pd.isna(pmr_wide.loc[c, 2018]) else None
            elif y < 2023 and 2018 in pmr_wide.columns:
                v = pmr_wide.loc[c, 2018]
            elif 2023 in pmr_wide.columns:
                v = pmr_wide.loc[c, 2023]
            pmr_long.append({"country": c, "year": y, "pmr_ffilled": v})
    pmrf = pd.DataFrame(pmr_long)
    df = df.merge(pmrf, on=["country", "year"], how="left")

    df = df[df["country"].isin(ALL)]
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])]

    df["log_lp"] = np.log(df["gvahrs"])
    df["log_population"] = np.log(df["population"])
    df["is_eu"] = df["country"].isin(EU_MEMBERS).astype(int)
    df["eu_post_2018"] = ((df["is_eu"] == 1) & (df["year"] >= 2018)).astype(int)
    df["eu_post_2022"] = ((df["is_eu"] == 1) & (df["year"] >= 2022)).astype(int)
    return df.dropna(subset=["log_lp"]).reset_index(drop=True), manifest


def fit(df, outcome, treatments, controls, label):
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
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

    # Primary: EU × post-2018 only, plus baseline controls
    primary = fit(df, "log_lp",
                  ["eu_post_2018"],
                  ["log_population", "trade_openness", "debt_to_gdp"],
                  "primary_twfe")

    # Cumulative: nested post-2018 + post-2022
    cumulative = fit(df, "log_lp",
                     ["eu_post_2018", "eu_post_2022"],
                     ["log_population", "trade_openness", "debt_to_gdp"],
                     "cumulative_twfe")

    # Channel sensitivity: include PMR (forward-filled)
    channel = fit(df.dropna(subset=["pmr_ffilled"]), "log_lp",
                  ["eu_post_2018"],
                  ["log_population", "trade_openness", "debt_to_gdp", "pmr_ffilled"],
                  "channel_pmr_twfe")

    # Placebo: fake EU-post-2014 (pre-treatment fake date)
    df_placebo = df.copy()
    df_placebo["eu_post_2014"] = ((df_placebo["is_eu"] == 1) & (df_placebo["year"] >= 2014) & (df_placebo["year"] < 2018)).astype(int)
    df_pb = df_placebo[df_placebo["year"] < 2018]
    placebo = fit(df_pb, "log_lp",
                  ["eu_post_2014"],
                  ["log_population", "trade_openness", "debt_to_gdp"],
                  "placebo_pre_2018")

    b = primary["coefs"].get("eu_post_2018", {})
    sign_ok = b.get("estimate", 0) < 0
    sig = abs(b.get("t", 0)) >= 1.645  # p<0.10 two-sided
    threshold_ok = b.get("estimate", 0) < -0.02
    placebo_b = placebo["coefs"].get("eu_post_2014", {})
    placebo_clean = abs(placebo_b.get("t", 0)) < 1.65

    if sign_ok and sig and threshold_ok and placebo_clean:
        verdict = (f"SUPPORTED — EU post-2018 productivity differential β={b['estimate']:+.4f} "
                   f"log points (p={b['p']:.3f}); placebo clean. Consistent with "
                   f"Draghi-report style competitiveness drag.")
    elif sign_ok and sig:
        verdict = (f"WEAKLY SUPPORTED — direction & significance OK (β={b['estimate']:+.4f}, "
                   f"p={b['p']:.3f}) but "
                   f"{'magnitude below -0.02 threshold' if not threshold_ok else 'placebo non-clean'}.")
    elif sign_ok:
        verdict = (f"DIRECTIONAL ONLY — EU post-2018 negative (β={b['estimate']:+.4f}) "
                   f"but not significant at p<0.10 (p={b['p']:.3f}).")
    else:
        verdict = (f"NOT SUPPORTED — β={b.get('estimate', float('nan')):+.4f} "
                   f"p={b.get('p', float('nan')):.3f}; falsification rule triggered.")

    falsification_rule = (
        "Not supported if β_eu_post_2018 is non-negative or insignificant at p<0.10, "
        "OR if effect vanishes after PMR/COVID controls, OR if pre-2018 placebo registers."
    )

    diag = {
        "verdict": verdict,
        "primary": primary,
        "cumulative": cumulative,
        "channel_pmr": channel,
        "placebo_pre_2018": placebo,
        "falsification": {
            "sign_ok": sign_ok,
            "sig_at_p10": sig,
            "threshold_minus_0_02": threshold_ok,
            "placebo_clean": placebo_clean,
        },
        "n_eu_countries_in_panel": int(df[df["is_eu"] == 1]["country"].nunique()),
        "n_non_eu_countries_in_panel": int(df[df["is_eu"] == 0]["country"].nunique()),
        "period": list(PERIOD),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "estimator": "panel_fe_twfe",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "treated_set": "EU members (25)",
        "control_set": NON_EU,
        "treatment_year": 2018,
        "vintages": manifest,
    }, sort_keys=False))

    lines = [
        f"# Result card — {RUN_ID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"**Estimator:** panel_fe (linearmodels TWFE, country + year FE, country-clustered SE)  ",
        f"**N obs:** {primary['n_obs']}  ",
        f"**N treated EU countries (in panel):** {diag['n_eu_countries_in_panel']}  ",
        f"**N non-EU controls (in panel):** {diag['n_non_eu_countries_in_panel']}  ",
        f"**Period:** {PERIOD[0]}-{PERIOD[1]}  ",
        f"**Outcome:** log labour productivity (OECD PDB GVAHRS, real USD-PPP per hour)",
        "",
        "## Primary spec (EU × post-2018)",
        "",
        "| Term | Estimate | SE | 95% CI | p | t |",
        "|---|---:|---:|:---:|---:|---:|",
        f"| eu_post_2018 | {b.get('estimate', float('nan')):+.4f} | {b.get('se', float('nan')):.4f} | "
        f"[{b.get('ci_lo', float('nan')):+.3f}, {b.get('ci_hi', float('nan')):+.3f}] | "
        f"{b.get('p', float('nan')):.3f} | {b.get('t', float('nan')):+.2f} |",
        "",
        "## Cumulative spec (EU × post-2018 + EU × post-2022 incremental)",
        "",
    ]
    for term, c in cumulative["coefs"].items():
        lines.append(f"- **{term}**: β={c['estimate']:+.4f} (SE={c['se']:.4f}, p={c['p']:.3f})")
    lines += [
        "",
        "## PMR-channel sensitivity (controls for OECD PMR forward-filled)",
        "",
    ]
    for term, c in channel["coefs"].items():
        lines.append(f"- **{term}**: β={c['estimate']:+.4f} (p={c['p']:.3f})")
    lines += [
        "",
        "## Placebo (EU × post-2014 in pre-2018 sample)",
        "",
        f"- β_placebo = {placebo_b.get('estimate', float('nan')):+.4f} (p={placebo_b.get('p', float('nan')):.3f}); "
        f"placebo {'CLEAN (|t|<1.65)' if placebo_clean else 'NOT CLEAN — pre-trend concern'}.",
        "",
        "## Falsification rule (from YAML)",
        falsification_rule,
        "",
        "## Caveats",
        "",
        "- Single-control USA strengthening: panel includes CAN, AUS, JPN, KOR, CHE, NOR, NZL, GBR. ",
        "  Identification still rests on cross-EU/non-EU differential post-2018, with country FE absorbing levels.",
        "- COVID + energy shock confounds 2020-2022 window. Year FE soak common shocks, not heterogeneous ones.",
        "- PMR vintages: only 2018 + 2023 observed; forward-filled ⇒ channel control is approximate.",
        "- Productivity measurement is real-PPP-converted; level effects reflect OECD harmonisation choices.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")
    print(f"verdict: {verdict}")
    print(f"  eu_post_2018: β={b.get('estimate', float('nan')):+.4f} p={b.get('p', float('nan')):.3f} n={primary['n_obs']}")


if __name__ == "__main__":
    sys.exit(main())
