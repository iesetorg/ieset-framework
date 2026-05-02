#!/usr/bin/env python3
"""Replication — Government consumption share and TFP growth.

Spec: Higher government-consumption shares predict weaker TFP growth after
controlling for public investment, education, and health spending, across a
broad panel 1970-2020.

Design:
  1. Broad panel 1970-2019.
  2. PWT TFP (rtfpna) as outcome.
  3. WDI government consumption (NE.CON.GOVT.ZS) as treatment.
  4. Controls: public investment (NE.GDI.FTOT.ZS), secondary enrollment
     (SE.SEC.ENRR), life expectancy (SP.DYN.LE00.IN), initial income,
     trade openness.
  5. PanelOLS with country and year FE, clustered SEs.

Falsification:
  SUPPORTED if β_gov_consumption < -0.03 and p <= 0.05.
  REFUTED if β_gov_consumption > +0.03 and p <= 0.05.
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
HID = "government_consumption_share_tfp"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


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
    tfp_path = latest("pwt", "rtfpna")
    gc_path = latest("world_bank_wdi", "NE.CON.GOVT.ZS")
    inv_path = latest("world_bank_wdi", "NE.GDI.FTOT.ZS")
    edu_path = latest("world_bank_wdi", "SE.SEC.ENRR")
    le_path = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    manifest = {
        "pwt_tfp": {"publisher": "pwt", "series": "rtfpna", "vintage_file": str(tfp_path.relative_to(REPO_ROOT)), "sha256": sha256(tfp_path)},
        "wdi_gc": {"publisher": "world_bank_wdi", "series": "NE.CON.GOVT.ZS", "vintage_file": str(gc_path.relative_to(REPO_ROOT)), "sha256": sha256(gc_path)},
        "wdi_inv": {"publisher": "world_bank_wdi", "series": "NE.GDI.FTOT.ZS", "vintage_file": str(inv_path.relative_to(REPO_ROOT)), "sha256": sha256(inv_path)},
        "wdi_edu": {"publisher": "world_bank_wdi", "series": "SE.SEC.ENRR", "vintage_file": str(edu_path.relative_to(REPO_ROOT)), "sha256": sha256(edu_path)},
        "wdi_le": {"publisher": "world_bank_wdi", "series": "SP.DYN.LE00.IN", "vintage_file": str(le_path.relative_to(REPO_ROOT)), "sha256": sha256(le_path)},
        "wdi_gdppc": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD", "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
        "wdi_trade": {"publisher": "world_bank_wdi", "series": "NE.TRD.GNFS.ZS", "vintage_file": str(trade_path.relative_to(REPO_ROOT)), "sha256": sha256(trade_path)},
    }
    tfp = load_long(tfp_path, "tfp")
    gc = load_long(gc_path, "gc")
    inv = load_long(inv_path, "inv")
    edu = load_long(edu_path, "edu")
    le = load_long(le_path, "le")
    gdppc = load_long(gdppc_path, "gdppc")
    trade = load_long(trade_path, "trade")

    # Compute TFP growth
    tfp = tfp.sort_values(["country", "year"])
    tfp["log_tfp"] = np.log(tfp["tfp"].replace({0: np.nan}))
    tfp["tfp_growth"] = tfp.groupby("country")["log_tfp"].diff()

    # Merge all
    df = tfp.merge(gc, on=["country", "year"], how="outer")
    df = df.merge(inv, on=["country", "year"], how="outer")
    df = df.merge(edu, on=["country", "year"], how="outer")
    df = df.merge(le, on=["country", "year"], how="outer")
    df = df.merge(gdppc, on=["country", "year"], how="outer")
    df = df.merge(trade, on=["country", "year"], how="outer")
    df = df[(df["year"] >= 1970) & (df["year"] <= 2020)]
    df = df.dropna(subset=["tfp_growth", "gc"])
    if len(df) < 400:
        verdict = "blocked_data_pending — insufficient observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_obs": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    # Lag government consumption by 1 year
    df = df.sort_values(["country", "year"])
    df["gc_lag"] = df.groupby("country")["gc"].shift(1)
    df["log_gdppc"] = np.log(df["gdppc"].replace({0: np.nan}))
    df = df.dropna(subset=["tfp_growth", "gc_lag"])

    # PanelOLS
    df = df.set_index(["country", "year"])
    exog_cols = ["gc_lag", "inv", "edu", "le", "log_gdppc", "trade"]
    df_model = df[["tfp_growth"] + exog_cols].dropna()
    if len(df_model) < 400:
        verdict = "blocked_data_pending — insufficient observations after dropping missings."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_obs": int(len(df_model))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    try:
        model = PanelOLS(df_model["tfp_growth"], df_model[exog_cols], entity_effects=True, time_effects=True)
        res = model.fit(cov_type="clustered", cluster_entity=True)
        beta_gc = float(res.params["gc_lag"])
        pval_gc = float(res.pvalues["gc_lag"])
        se_gc = float(res.std_errors["gc_lag"])
        n_obs = int(res.nobs)
        r2 = float(res.rsquared_within)
    except Exception as e:
        verdict = f"blocked_method — estimation error: {e}"
        diagnostics = {"hypothesis_id": HID, "verdict": verdict}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_method\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    if beta_gc < -0.03 and pval_gc <= 0.05:
        verdict = f"supported — β_gov_consumption={beta_gc:+.4f} (SE {se_gc:.4f}, p={pval_gc:.3f}, n={n_obs}), R²_within={r2:.3f}. Negative and significant."
    elif beta_gc > 0.03 and pval_gc <= 0.05:
        verdict = f"refuted — β_gov_consumption={beta_gc:+.4f} (SE {se_gc:.4f}, p={pval_gc:.3f}, n={n_obs}), R²_within={r2:.3f}. Positive and significant."
    else:
        verdict = f"partial — β_gov_consumption={beta_gc:+.4f} (SE {se_gc:.4f}, p={pval_gc:.3f}, n={n_obs}), R²_within={r2:.3f}. Does not meet falsification threshold."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_obs": n_obs, "beta_gc": beta_gc, "se_gc": se_gc, "p_value_gc": pval_gc, "r2_within": r2},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  pwt_tfp: {manifest['pwt_tfp']['vintage_file']}\n  wdi_gc: {manifest['wdi_gc']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nPanel FE with country and year fixed effects, clustered SEs. Government consumption lagged 1 year.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
