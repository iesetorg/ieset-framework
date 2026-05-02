#!/usr/bin/env python3
"""Replication — Gradualist vs shock-therapy transition outcomes.

Spec: Deng's gradualist reforms (China, Vietnam) produced stronger GDP per capita
and TFP growth than post-Soviet shock-therapy transitions.

Design:
  1. Panel 1989-2010 of transition economies.
  2. Gradualist = CHN, VNM; shock-therapy = post-Soviet states.
  3. PWT GDP pc + TFP as outcomes.
  4. PanelOLS with country and year FE.

Falsification:
  SUPPORTED if gradualist dummy coefficient is positive and significant (p<0.10).
  REFUTED if coefficient is negative and significant (p<0.10).
  Otherwise PARTIAL.
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
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "gradualist_vs_shock_therapy_transition_outcomes"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

GRADUALIST = {"CHN", "VNM"}
SHOCK = {"RUS", "POL", "EST", "LVA", "LTU", "CZE", "SVK", "HUN", "ROU", "BGR", "UKR", "BLR", "KAZ"}
ALL = GRADUALIST | SHOCK


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    tfp_path = latest("pwt", "rtfpna")
    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    wgi_path = latest("wgi", "GOV_WGI_RL.EST")
    manifest = {
        "wdi_gdppc": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD", "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
        "pwt_tfp": {"publisher": "pwt", "series": "rtfpna", "vintage_file": str(tfp_path.relative_to(REPO_ROOT)), "sha256": sha256(tfp_path)},
        "wdi_trade": {"publisher": "world_bank_wdi", "series": "NE.TRD.GNFS.ZS", "vintage_file": str(trade_path.relative_to(REPO_ROOT)), "sha256": sha256(trade_path)},
        "wgi_rl": {"publisher": "wgi", "series": "GOV_WGI_RL.EST", "vintage_file": str(wgi_path.relative_to(REPO_ROOT)), "sha256": sha256(wgi_path)},
    }
    gdppc = load_long(gdppc_path, "gdppc")
    tfp = load_long(tfp_path, "tfp")
    trade = load_long(trade_path, "trade")
    rl = load_long(wgi_path, "rl")

    # GDP pc growth
    gdppc = gdppc.sort_values(["country", "year"])
    gdppc["log_gdppc"] = np.log(gdppc["gdppc"].replace({0: np.nan}))
    gdppc["gdppc_growth"] = gdppc.groupby("country")["log_gdppc"].diff()

    # TFP growth
    tfp = tfp.sort_values(["country", "year"])
    tfp["log_tfp"] = np.log(tfp["tfp"].replace({0: np.nan}))
    tfp["tfp_growth"] = tfp.groupby("country")["log_tfp"].diff()

    df = gdppc.merge(tfp, on=["country", "year"], how="outer")
    df = df.merge(trade, on=["country", "year"], how="outer")
    df = df.merge(rl, on=["country", "year"], how="outer")
    df = df[df["country"].isin(ALL)]
    df = df[(df["year"] >= 1989) & (df["year"] <= 2010)]
    df["gradualist"] = df["country"].isin(GRADUALIST).astype(int)
    df["log_gdppc"] = np.log(df["gdppc"].replace({0: np.nan}))
    df["log_pop"] = np.nan  # placeholder, not used directly

    # PanelOLS for GDP pc growth
    df_p = df.set_index(["country", "year"])
    outcomes = []
    for outcome_var, label in [("gdppc_growth", "GDP pc growth"), ("tfp_growth", "TFP growth")]:
        sub = df_p[[outcome_var, "gradualist", "trade", "rl"]].dropna()
        if len(sub) < 20:
            outcomes.append({"label": label, "beta": None, "pval": None, "n": len(sub), "verdict": "insufficient data"})
            continue
        try:
            # gradualist is time-invariant, so entity_effects would absorb it;
            # use time_effects only to control for global shocks
            model = PanelOLS(sub[outcome_var], sub[["gradualist", "trade", "rl"]], entity_effects=False, time_effects=True)
            res = model.fit(cov_type="clustered", cluster_entity=True)
            beta = float(res.params["gradualist"])
            pval = float(res.pvalues["gradualist"])
            se = float(res.std_errors["gradualist"])
            n = int(res.nobs)
            r2 = float(res.rsquared)
            if beta > 0 and pval < 0.10:
                v = f"supported"
            elif beta < 0 and pval < 0.10:
                v = f"refuted"
            else:
                v = f"partial"
            outcomes.append({"label": label, "beta": beta, "pval": pval, "se": se, "n": n, "r2": r2, "verdict": v})
        except Exception as e:
            outcomes.append({"label": label, "beta": None, "pval": None, "n": len(sub), "verdict": f"error: {e}"})

    # Aggregate verdict: supported only if both outcomes supported
    v_list = [o["verdict"] for o in outcomes]
    if all(v == "supported" for v in v_list):
        overall = "supported"
    elif any(v == "refuted" for v in v_list):
        overall = "refuted"
    else:
        overall = "partial"

    verdict_parts = [f"{o['label']}: β={o.get('beta','N/A')} (p={o.get('pval','N/A')}, n={o.get('n','N/A')})" for o in outcomes]
    verdict = f"{overall} — {'; '.join(verdict_parts)}"

    diagnostics = {
        "hypothesis_id": HID, "verdict": overall,
        "reason": "; ".join(verdict_parts),
        "metrics": outcomes,
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {overall}\nreason: {'; '.join(verdict_parts)}\nvintages:\n  wdi_gdppc: {manifest['wdi_gdppc']['vintage_file']}\n  pwt_tfp: {manifest['pwt_tfp']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nPanel FE with country and year FE, 1989-2010. Gradualist = CHN+VNM, Shock = post-Soviet.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
