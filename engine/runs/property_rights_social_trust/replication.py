#!/usr/bin/env python3
"""Replication — Property rights and social trust / corruption control.

Spec: Stronger rule-of-law proxies predict higher control-of-corruption scores.

Design:
  1. Panel 1996-2019 (WGI coverage).
  2. WGI CC.EST as outcome.
  3. WGI RL.EST as treatment.
  4. Controls: log GDP pc, WGI GE.EST.
  5. PanelOLS with country and year FE.

Falsification:
  SUPPORTED if β_RL > 0 and p < 0.10.
  REFUTED if β_RL < 0 and p < 0.10.
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
HID = "property_rights_social_trust"
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
    cc_path = latest("wgi", "GOV_WGI_CC.EST")
    rl_path = latest("wgi", "GOV_WGI_RL.EST")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    ge_path = latest("wgi", "GOV_WGI_GE.EST")
    manifest = {
        "wgi_cc": {"publisher": "wgi", "series": "GOV_WGI_CC.EST", "vintage_file": str(cc_path.relative_to(REPO_ROOT)), "sha256": sha256(cc_path)},
        "wgi_rl": {"publisher": "wgi", "series": "GOV_WGI_RL.EST", "vintage_file": str(rl_path.relative_to(REPO_ROOT)), "sha256": sha256(rl_path)},
        "wdi_gdppc": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD", "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
        "wgi_ge": {"publisher": "wgi", "series": "GOV_WGI_GE.EST", "vintage_file": str(ge_path.relative_to(REPO_ROOT)), "sha256": sha256(ge_path)},
    }
    cc = load_long(cc_path, "cc")
    rl = load_long(rl_path, "rl")
    gdppc = load_long(gdppc_path, "gdppc")
    ge = load_long(ge_path, "ge")

    df = cc.merge(rl, on=["country", "year"], how="outer")
    df = df.merge(gdppc, on=["country", "year"], how="outer")
    df = df.merge(ge, on=["country", "year"], how="outer")
    df = df[(df["year"] >= 1996) & (df["year"] <= 2019)]
    df["log_gdppc"] = np.log(df["gdppc"].replace({0: np.nan}))
    df = df.dropna(subset=["cc", "rl", "log_gdppc", "ge"])
    if len(df) < 50:
        verdict = "blocked_data_pending — insufficient observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_obs": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    df = df.set_index(["country", "year"])
    exog = df[["rl", "log_gdppc", "ge"]]
    model = PanelOLS(df["cc"], exog, entity_effects=True, time_effects=True)
    res = model.fit(cov_type="clustered", cluster_entity=True)
    beta = float(res.params["rl"])
    pval = float(res.pvalues["rl"])
    se = float(res.std_errors["rl"])
    n = int(res.nobs)

    if beta > 0 and pval < 0.10:
        verdict = f"supported — β_RL={beta:+.4f} (SE {se:.4f}, p={pval:.3f}, n={n}). Stronger rule of law predicts lower corruption."
    elif beta < 0 and pval < 0.10:
        verdict = f"refuted — β_RL={beta:+.4f} (SE {se:.4f}, p={pval:.3f}, n={n}). Opposite sign."
    else:
        verdict = f"partial — β_RL={beta:+.4f} (SE {se:.4f}, p={pval:.3f}, n={n}). Does not meet threshold."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_obs": n, "beta_rl": beta, "se_rl": se, "p_value": pval},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wgi_cc: {manifest['wgi_cc']['vintage_file']}\n  wgi_rl: {manifest['wgi_rl']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nPanel FE with country and year fixed effects.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
