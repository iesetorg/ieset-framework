#!/usr/bin/env python3
"""Replication — labour_market_flexibility_unemployment_duration (v1).

Spec: hypotheses/labour/labour_market_flexibility_unemployment_duration.yaml
Steelman: hypotheses/steelman/labour_market_flexibility_unemployment_duration.md

Two-way FE panel: long-term unemployment share (Eurostat une_ltu_a) and
unemployment rate (Eurostat une_rt_a, secondary), regressed on OECD EPL_R
(employment protection — regular contracts).

Pre-registered falsification:
  panel_FE_beta(EPL) on long_term_share > 0 at p<0.05 AND
  panel_FE_beta(EPL) on median_duration > 0 at p<0.05 AND
  EPL coefficient remains significant at p<0.10 after UI generosity control

DEVIATIONS:
  - OECD median_unemployment_duration / DSD_LMS not in vintages; substitute
    the Eurostat une_ltu_a long-term-unemployment series (% of active pop)
    as the primary outcome and the Eurostat une_rt_a total unemployment
    rate as a secondary triangulation outcome (the spec's u-rate is
    explicitly NOT the registered claim, but it provides triangulation).
  - OECD UI replacement-rate (DSD_UBR) not in vintages; UI-robustness
    sub-test cannot be run as designed. We instead use trade openness +
    log GDP per capita PPP as macro controls and report this deviation.
  - ALMP, unionisation, output gap not in vintages; dropped.
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
HID = "labour_market_flexibility_unemployment_duration"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Spec sample
COUNTRIES = ["AUT", "BEL", "CAN", "CHE", "CZE", "DEU", "DNK", "ESP", "EST",
             "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ITA", "JPN", "KOR",
             "LUX", "MEX", "NLD", "NOR", "NZL", "POL", "PRT", "SVK", "SVN",
             "SWE", "TUR", "USA", "AUS"]
PERIOD = (1985, 2023)

EU2ISO3 = {"AT": "AUT", "BE": "BEL", "CZ": "CZE", "DE": "DEU", "DK": "DNK",
           "ES": "ESP", "EE": "EST", "FI": "FIN", "FR": "FRA", "UK": "GBR",
           "EL": "GRC", "HU": "HUN", "IE": "IRL", "IT": "ITA", "LU": "LUX",
           "NL": "NLD", "NO": "NOR", "PL": "POL", "PT": "PRT", "SK": "SVK",
           "SI": "SVN", "SE": "SWE", "TR": "TUR", "CH": "CHE"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, ser: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(f"{ser}@*.parquet"),
                   key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{ser}")
    return files[-1]


def load_long_wdi(path: Path, var: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": var, "country_iso3": "country"})


def load_eurostat_unemp_ltu(path: Path) -> pd.DataFrame:
    """Long-term unemployment % of active population, both sexes, age 15-74."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["sex"] == "T") & (t["age"] == "Y15-74") &
            (t["unit"] == "PC_ACT") & (t["indic_em"] == "LTU")].copy()
    sub["year"] = sub["period"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["country"] = sub["geo_code"].map(EU2ISO3)
    sub = sub.dropna(subset=["country"])
    return sub.groupby(["country", "year"], as_index=False)["value"].mean().rename(
        columns={"value": "long_term_unemp_share"})


def load_eurostat_unemp_rt(path: Path) -> pd.DataFrame:
    """Unemployment rate, both sexes, age 15-74."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["sex"] == "T") & (t["age"] == "Y15-74") &
            (t["unit"] == "PC_ACT")].copy()
    sub["year"] = sub["period"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["country"] = sub["geo_code"].map(EU2ISO3)
    sub = sub.dropna(subset=["country"])
    return sub.groupby(["country", "year"], as_index=False)["value"].mean().rename(
        columns={"value": "unemp_rate"})


def load_oecd_epl(path: Path) -> pd.DataFrame:
    """OECD EPL_R (employment protection, regular contracts)."""
    t = pq.read_table(path).to_pandas()
    sub = t[t["MEASURE"] == "EPL_R"].copy()
    sub["country"] = sub["REF_AREA"]
    sub["year"] = sub["period"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    return sub.groupby(["country", "year"], as_index=False)["value"].mean().rename(
        columns={"value": "epl_r"})


def assemble() -> tuple[pd.DataFrame, dict]:
    manifest, frames = {}, []

    paths = {
        "trade_openness": ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "gdp_pc_ppp":     ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "u_total":        ("world_bank_wdi", "SL.UEM.TOTL.ZS"),
    }
    for var, (pub, ser) in paths.items():
        p = latest(pub, ser)
        manifest[var] = {"publisher": pub, "series": ser,
                         "vintage_file": str(p.relative_to(REPO_ROOT)),
                         "sha256": sha256(p)}
        frames.append(load_long_wdi(p, var))

    p = latest("eurostat", "une_ltu_a")
    manifest["long_term_unemp_share"] = {"publisher": "eurostat", "series": "une_ltu_a",
                                         "vintage_file": str(p.relative_to(REPO_ROOT)),
                                         "sha256": sha256(p)}
    frames.append(load_eurostat_unemp_ltu(p))

    p = latest("eurostat", "une_rt_a")
    manifest["unemp_rate_eu"] = {"publisher": "eurostat", "series": "une_rt_a",
                                 "vintage_file": str(p.relative_to(REPO_ROOT)),
                                 "sha256": sha256(p)}
    frames.append(load_eurostat_unemp_rt(p))

    p = latest("oecd", "OECD.ELS.JAI_DSD_EPL_DF_EPL_1.0")
    manifest["epl_r"] = {"publisher": "oecd", "series": "OECD.ELS.JAI:DSD_EPL@DF_EPL/EPL_R",
                         "vintage_file": str(p.relative_to(REPO_ROOT)),
                         "sha256": sha256(p)}
    frames.append(load_oecd_epl(p))

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(COUNTRIES)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    return panel.sort_values(["country", "year"]).reset_index(drop=True), manifest


def fit_twfe(df: pd.DataFrame, outcome: str, regressors: list[str]) -> dict:
    cols = ["country", "year", outcome] + regressors
    d = df[cols].dropna().copy().set_index(["country", "year"])
    X = d[regressors]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=True, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True)
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in regressors:
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    # Primary spec: EPL on long-term-unemp share
    primary = fit_twfe(panel, "long_term_unemp_share", ["epl_r"])
    # Secondary: EPL on unemployment rate (Eurostat)
    secondary = fit_twfe(panel, "unemp_rate", ["epl_r"])
    # Robustness: add macro controls (trade_openness, log_gdp_pc_ppp)
    robust = fit_twfe(panel, "long_term_unemp_share",
                      ["epl_r", "trade_openness", "log_gdp_pc_ppp"])

    b_pri = primary["coefs"].get("epl_r", {})
    b_sec = secondary["coefs"].get("epl_r", {})
    b_rob = robust["coefs"].get("epl_r", {})

    pri_pos_sig = b_pri.get("estimate", 0) > 0 and b_pri.get("p", 1) < 0.05
    sec_pos_sig = b_sec.get("estimate", 0) > 0 and b_sec.get("p", 1) < 0.05
    rob_sig = b_rob.get("p", 1) < 0.10

    all_pass = pri_pos_sig and sec_pos_sig and rob_sig
    if all_pass:
        verdict = (f"supported — EPL_R β on long-term-unemp share = "
                   f"{b_pri.get('estimate', 0):+.3f} pp (p={b_pri.get('p', 1):.3f}); "
                   f"survives macro-control robustness (β={b_rob.get('estimate', 0):+.3f}, "
                   f"p={b_rob.get('p', 1):.3f})")
    elif pri_pos_sig:
        verdict = (f"partial — primary EPL effect on long-term-unemp share is "
                   f"positive and significant (β={b_pri.get('estimate', 0):+.3f}, "
                   f"p={b_pri.get('p', 1):.3f}); but secondary outcome (unemp rate) "
                   f"or robustness control failed pre-registered threshold")
    else:
        verdict = (f"refuted — primary EPL coefficient on long-term-unemp share is "
                   f"β={b_pri.get('estimate', 0):+.3f} (p={b_pri.get('p', 1):.3f}); "
                   f"fails sign-and-significance test")

    rows = [
        {"spec": "primary_long_term_unemp", "term": "epl_r",
         "estimate": b_pri.get("estimate"), "se": b_pri.get("se"),
         "p": b_pri.get("p"), "n_obs": primary["n_obs"]},
        {"spec": "secondary_unemp_rate", "term": "epl_r",
         "estimate": b_sec.get("estimate"), "se": b_sec.get("se"),
         "p": b_sec.get("p"), "n_obs": secondary["n_obs"]},
        {"spec": "robust_with_controls", "term": "epl_r",
         "estimate": b_rob.get("estimate"), "se": b_rob.get("se"),
         "p": b_rob.get("p"), "n_obs": robust["n_obs"]},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diag = {
        "verdict": verdict, "all_pass": all_pass,
        "primary_long_term_unemp": primary,
        "secondary_unemp_rate": secondary,
        "robust_with_controls": robust,
        "falsification_components": {
            "primary_pos_p05": pri_pos_sig,
            "secondary_pos_p05": sec_pos_sig,
            "robust_p10": rob_sig,
        },
        "sample": {"countries_in_data": sorted(panel["country"].unique().tolist()),
                   "n_obs_panel": int(len(panel))},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2,
                                                         default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID, "run_utc": pd.Timestamp.utcnow().isoformat(),
        "vintages": manifest,
        "deviations": [
            "OECD DSD_LMS median-duration not in vintages; primary outcome substituted with Eurostat une_ltu_a (long-term-unemp share, % of active pop). Secondary outcome substituted with Eurostat une_rt_a unemployment rate.",
            "OECD DSD_UBR UI replacement rate not in vintages; pre-registered UI-generosity robustness control replaced with macro controls (trade openness, log GDP pc PPP).",
            "ALMP, unionisation, output gap controls dropped (not in vintages).",
            "Sample restricted to Eurostat-reporting countries with EPL data; OECD non-EU members (USA, JPN, KOR, MEX, NZL, AUS, CAN) lack Eurostat outcome data and drop out of primary spec.",
        ],
    }, sort_keys=False))

    lines = [
        f"# Result card — {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "Pre-registered: panel_FE_beta(EPL) on long_term_share > 0 at p<0.05 AND on duration > 0 at p<0.05 AND EPL beta survives p<0.10 after macro/UI control.",
        "",
        "## Coefficient summary (TWFE country + year FE, clustered by country)",
        "",
        "| Spec | Outcome | β(EPL_R) | SE | p | n_obs |",
        "|---|---|---:|---:|---:|---:|",
        f"| primary | long_term_unemp_share | {b_pri.get('estimate', float('nan')):+.4f} | {b_pri.get('se', float('nan')):.4f} | {b_pri.get('p', float('nan')):.3f} | {primary['n_obs']} |",
        f"| secondary | unemp_rate | {b_sec.get('estimate', float('nan')):+.4f} | {b_sec.get('se', float('nan')):.4f} | {b_sec.get('p', float('nan')):.3f} | {secondary['n_obs']} |",
        f"| robust | long_term_unemp_share + macro ctrl | {b_rob.get('estimate', float('nan')):+.4f} | {b_rob.get('se', float('nan')):.4f} | {b_rob.get('p', float('nan')):.3f} | {robust['n_obs']} |",
        "",
        f"Sample N (primary): {primary['n_obs']} country-year observations.",
        "",
        "## Deviations from pre-registration",
        "",
        "- Outcome substitution: Eurostat une_ltu_a long-term-unemployment share replaces OECD DSD_LMS median-duration (not in vintages).",
        "- UI-generosity robustness control replaced with macro controls (trade openness + log GDP pc PPP) because OECD DSD_UBR not in vintages.",
        "- Sample shrinks to EU/Eurostat-reporting countries (USA/JPN/KOR/MEX/AUS/NZL/CAN drop from primary because Eurostat lacks them).",
        "",
        "## Steelman live concerns",
        "",
        "See [hypotheses/steelman/labour_market_flexibility_unemployment_duration.md]"
        "(../../../hypotheses/steelman/labour_market_flexibility_unemployment_duration.md) "
        "for the Bassanini-Duval heterogeneity argument, the flexicurity counterexample, "
        "and the v1-v2 EPL methodology break confound.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  primary  β(EPL→LTU share)= {b_pri.get('estimate', float('nan')):+.4f}  p={b_pri.get('p', float('nan')):.3f}  n={primary['n_obs']}")
    print(f"  second.  β(EPL→u rate)  = {b_sec.get('estimate', float('nan')):+.4f}  p={b_sec.get('p', float('nan')):.3f}  n={secondary['n_obs']}")
    print(f"  robust   β(EPL+ctrl)    = {b_rob.get('estimate', float('nan')):+.4f}  p={b_rob.get('p', float('nan')):.3f}  n={robust['n_obs']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
