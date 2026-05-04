#!/usr/bin/env python3
"""Replication — Ordoliberal anti-cartel policy and post-war German growth.

Spec: Post-war West Germany's Wirtschaftswunder (1948-1965) reflects the combined
effect of Erhard's 1948 currency reform plus the 1957 GWB anti-cartel law. The test
compares real GDP-pc growth in the pre-GWB window (1949-1957) vs post-GWB window
(1958-1965).

Design:
  1. Single-country time series for Germany (DEU).
  2. Maddison GDP pc + PWT rgdpna + WDI industrial production growth.
  3. Compare mean annual growth in 1949-1957 vs 1958-1965.

Falsification:
  SUPPORTED if post-GWB growth >= 50% of pre-GWB growth.
  REFUTED if post-GWB growth < 50% of pre-GWB growth.
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

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "ordo_anti_cartel_post_war_germany_economic_miracle"
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
    maddison_path = latest("maddison", "mpd2020")
    pwt_path = latest("pwt", "rgdpna")
    ind_path = latest("world_bank_wdi", "NV.IND.TOTL.KD.ZG")
    manifest = {
        "maddison": {"publisher": "maddison", "series": "maddison", "vintage_file": str(maddison_path.relative_to(REPO_ROOT)), "sha256": sha256(maddison_path)},
        "pwt": {"publisher": "pwt", "series": "rgdpna", "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path)},
        "wdi_ind": {"publisher": "world_bank_wdi", "series": "NV.IND.TOTL.KD.ZG", "vintage_file": str(ind_path.relative_to(REPO_ROOT)), "sha256": sha256(ind_path)},
    }

    # Load Maddison
    maddison = pq.read_table(maddison_path).to_pandas()
    maddison = maddison[(maddison["country_iso3"] == "DEU") & (maddison["year"].notna())]
    maddison["year"] = maddison["year"].astype(int)
    maddison = maddison.set_index("year")["gdppc"].sort_index()

    # Load PWT
    pwt = load_long(pwt_path, "rgdpna")
    pwt = pwt[pwt["country"] == "DEU"].set_index("year")["rgdpna"].sort_index()

    # Load industrial production growth
    ind = load_long(ind_path, "ind_growth")
    ind = ind[ind["country"] == "DEU"].set_index("year")["ind_growth"].sort_index()

    def mean_growth(series, start, end):
        s = series[(series.index >= start) & (series.index <= end)].dropna()
        if len(s) < 2:
            return None
        log_s = np.log(s.replace({0: np.nan}))
        return float((log_s.iloc[-1] - log_s.iloc[0]) / (log_s.index[-1] - log_s.index[0]))

    def mean_ind_growth(series, start, end):
        s = series[(series.index >= start) & (series.index <= end)].dropna()
        if len(s) == 0:
            return None
        return float(s.mean() / 100.0)  # WDI growth is in %

    pre_m = mean_growth(maddison, 1949, 1957)
    post_m = mean_growth(maddison, 1958, 1965)
    pre_p = mean_growth(pwt, 1949, 1957)
    post_p = mean_growth(pwt, 1958, 1965)
    pre_i = mean_ind_growth(ind, 1949, 1957)
    post_i = mean_ind_growth(ind, 1958, 1965)

    metrics = {
        "maddison_pre_1949_1957": pre_m, "maddison_post_1958_1965": post_m,
        "pwt_pre_1949_1957": pre_p, "pwt_post_1958_1965": post_p,
        "ind_pre_1949_1957": pre_i, "ind_post_1958_1965": post_i,
    }

    # Count supported metrics (post >= 50% of pre)
    supported_count = 0
    total_count = 0
    for label, (pre, post) in [("maddison", (pre_m, post_m)), ("pwt", (pre_p, post_p)), ("ind", (pre_i, post_i))]:
        if pre is not None and post is not None and pre > 0:
            total_count += 1
            if post >= 0.5 * pre:
                supported_count += 1

    if total_count < 2:
        verdict = "blocked_data_pending — insufficient era coverage."
    elif supported_count / total_count >= 0.80:
        verdict = f"supported — {supported_count}/{total_count} metrics show post-GWB growth >= 50% of pre-GWB."
    elif supported_count / total_count <= 0.40:
        verdict = f"refuted — Only {supported_count}/{total_count} metrics meet threshold."
    else:
        verdict = f"partial — {supported_count}/{total_count} metrics meet threshold."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0] if " — " in verdict else verdict,
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": metrics,
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0] if ' — ' in verdict else verdict}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  maddison: {manifest['maddison']['vintage_file']}\n  pwt: {manifest['pwt']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nSingle-country time-series comparison of West Germany pre-GWB (1949-1957) vs post-GWB (1958-1965).\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
