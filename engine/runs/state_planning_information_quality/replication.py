#!/usr/bin/env python3
"""Replication — State planning and information quality (voice & accountability).

Spec: Higher government consumption share predicts weaker voice-and-accountability
(WGI VA.EST) across a broad panel.
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
HID = "state_planning_information_quality"
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
    va_path = latest("wgi", "GOV_WGI_VA.EST")
    gc_path = latest("world_bank_wdi", "NE.CON.GOVT.ZS")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    rl_path = latest("wgi", "GOV_WGI_RL.EST")
    manifest = {
        "wgi_va": {"publisher": "wgi", "series": "GOV_WGI_VA.EST", "vintage_file": str(va_path.relative_to(REPO_ROOT)), "sha256": sha256(va_path)},
        "wdi_gc": {"publisher": "world_bank_wdi", "series": "NE.CON.GOVT.ZS", "vintage_file": str(gc_path.relative_to(REPO_ROOT)), "sha256": sha256(gc_path)},
        "wdi_gdppc": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD", "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
        "wgi_rl": {"publisher": "wgi", "series": "GOV_WGI_RL.EST", "vintage_file": str(rl_path.relative_to(REPO_ROOT)), "sha256": sha256(rl_path)},
    }
    va = load_long(va_path, "va")
    gc = load_long(gc_path, "gc")
    gdppc = load_long(gdppc_path, "gdppc")
    rl = load_long(rl_path, "rl")

    df = va.merge(gc, on=["country", "year"], how="outer")
    df = df.merge(gdppc, on=["country", "year"], how="outer")
    df = df.merge(rl, on=["country", "year"], how="outer")
    df = df[(df["year"] >= 1996) & (df["year"] <= 2019)]
    df["log_gdppc"] = np.log(df["gdppc"].replace({0: np.nan}))
    df = df.dropna(subset=["va", "gc", "log_gdppc"])
    if len(df) < 50:
        verdict = "blocked_data_pending — insufficient observations."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_obs": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    df = df.set_index(["country", "year"])
    exog = df[["gc", "log_gdppc", "rl"]]
    model = PanelOLS(df["va"], exog, entity_effects=True, time_effects=True)
    res = model.fit(cov_type="clustered", cluster_entity=True)
    beta = float(res.params["gc"])
    pval = float(res.pvalues["gc"])
    se = float(res.std_errors["gc"])
    n = int(res.nobs)

    if beta < 0 and pval < 0.10:
        verdict = f"supported — β_gc={beta:+.4f} (SE {se:.4f}, p={pval:.3f}, n={n}). Higher gov consumption predicts weaker voice & accountability."
    elif beta > 0 and pval < 0.10:
        verdict = f"refuted — β_gc={beta:+.4f} (SE {se:.4f}, p={pval:.3f}, n={n}). Opposite sign."
    else:
        verdict = f"partial — β_gc={beta:+.4f} (SE {se:.4f}, p={pval:.3f}, n={n}). Does not meet threshold."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_obs": n, "beta_gc": beta, "se_gc": se, "p_value": pval},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wgi_va: {manifest['wgi_va']['vintage_file']}\n  wdi_gc: {manifest['wdi_gc']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nPanel FE with country and year fixed effects.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
