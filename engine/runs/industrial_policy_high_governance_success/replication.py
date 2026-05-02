#!/usr/bin/env python3
"""Replication — Industrial policy success in high-governance states.

Spec: Industrial policy succeeds over long windows in high-governance states with
export discipline, challenging a blanket free-market claim.

Design:
  1. Broad panel 1996-2019.
  2. WGI Government Effectiveness (governance proxy) + V-Dem state ownership
     (industrial-policy intensity proxy; lower = more state direction).
  3. Split into high-governance / high-state-ownership vs high-governance / low-state-ownership.
  4. Compare GDP pc growth.

Falsification:
  SUPPORTED if high-gov + high-state growth >= high-gov + low-state growth.
  REFUTED if high-gov + high-state growth < high-gov + low-state growth − 0.50 pp/yr.
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
from scipy import stats

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "industrial_policy_high_governance_success"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1996, 2019)
GROWTH_DIFF_THRESHOLD = 0.005


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
    ge_path = latest("wgi", "GOV_WGI_GE.EST")
    vdem_path = latest("vdem", "vdem_cy_full")
    pwt_path = latest("pwt", "pwt_full")
    manifest = {
        "wgi_ge": {"publisher": "wgi", "series": "GOV_WGI_GE.EST",
                   "vintage_file": str(ge_path.relative_to(REPO_ROOT)), "sha256": sha256(ge_path)},
        "vdem": {"publisher": "vdem", "series": "vdem_cy_full",
                 "vintage_file": str(vdem_path.relative_to(REPO_ROOT)), "sha256": sha256(vdem_path)},
        "pwt": {"publisher": "pwt", "series": "pwt_full",
                "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path)},
    }
    ge = load_long(ge_path, "ge")
    vdem = pq.read_table(vdem_path).to_pandas()
    vdem = vdem[vdem["country_text_id"].notna() & (vdem["country_text_id"].str.len() == 3)]
    vdem = vdem[["country_text_id", "year", "v2clstown"]].rename(columns={"country_text_id": "country"})
    vdem["year"] = vdem["year"].astype(int)
    vdem = vdem.dropna(subset=["v2clstown"])
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]
    pwt["log_gdppc"] = np.log(pwt["rgdpe_pc"])
    pwt["growth_yoy"] = pwt.groupby("country")["log_gdppc"].diff()

    # Country-level means
    ge_mean = ge.groupby("country")["ge"].mean().reset_index()
    own_mean = vdem.groupby("country")["v2clstown"].mean().reset_index()
    growth_mean = pwt.groupby("country")["growth_yoy"].mean().reset_index()

    df = ge_mean.merge(own_mean, on="country", how="inner").merge(growth_mean, on="country", how="inner").dropna()
    if len(df) < 20:
        verdict = "blocked_data_pending — insufficient country overlap."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    # High governance = top half GE
    ge_median = df["ge"].median()
    own_median = df["v2clstown"].median()
    df["high_gov"] = df["ge"] >= ge_median
    df["high_state"] = df["v2clstown"] < own_median  # lower v2clstown = more state ownership

    hg_hs = df[df["high_gov"] & df["high_state"]]
    hg_ls = df[df["high_gov"] & ~df["high_state"]]

    mean_hs = float(hg_hs["growth_yoy"].mean()) if len(hg_hs) else 0.0
    mean_ls = float(hg_ls["growth_yoy"].mean()) if len(hg_ls) else 0.0
    diff = mean_hs - mean_ls

    if len(hg_hs) > 1 and len(hg_ls) > 1:
        tstat, pval = stats.ttest_ind(hg_hs["growth_yoy"].dropna().values, hg_ls["growth_yoy"].dropna().values, equal_var=False)
        tstat = float(tstat); pval = float(pval)
    else:
        tstat = float("nan"); pval = float("nan")

    if mean_hs >= mean_ls:
        verdict = f"supported — High-gov + high-state growth {mean_hs*100:+.2f}%/yr vs high-gov + low-state {mean_ls*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
    elif mean_hs < mean_ls - GROWTH_DIFF_THRESHOLD:
        verdict = f"refuted — High-gov + high-state growth {mean_hs*100:+.2f}%/yr below high-gov + low-state {mean_ls*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
    else:
        verdict = f"partial — High-gov + high-state {mean_hs*100:+.2f}%/yr vs high-gov + low-state {mean_ls*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {"n_countries": int(len(df)), "n_high_gov_high_state": int(len(hg_hs)), "n_high_gov_low_state": int(len(hg_ls)),
                    "mean_high_state": mean_hs, "mean_low_state": mean_ls, "diff": diff, "t_stat": tstat, "p_value": pval},
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wdi_ge: {manifest['wgi_ge']['vintage_file']}\n  vdem: {manifest['vdem']['vintage_file']}\n  pwt: {manifest['pwt']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nCross-section of {len(df)} countries. High governance = top half WGI GE. High state direction = bottom half V-Dem state ownership.\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
