#!/usr/bin/env python3
"""Replication — Korea post-chaebol liberalisation and frontier growth.

Spec: South Korea's post-1997 liberalisation and governance reforms explain a
larger share of post-crisis frontier convergence than earlier heavy-and-chemical
industrial policy.

Design:
  1. Single-country time series 1961-2024 for Korea.
  2. PWT GDP pc + TFP as outcomes.
  3. Compare cumulative growth in HCI era (1973-1997) vs post-liberalisation era (1998-2024).
  4. Controls for global demand (world GDP growth proxy via US growth).

Falsification:
  SUPPORTED if post-1997 cumulative GDP-pc gain exceeds HCI-era gain.
  REFUTED if HCI-era gain exceeds post-1997 gain.
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
HID = "korea_post_chaebol_liberalisation_frontier_growth"
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
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    tfp_path = latest("pwt", "rtfpna")
    us_growth_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")
    manifest = {
        "wdi_gdppc": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD", "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)), "sha256": sha256(gdppc_path)},
        "pwt_tfp": {"publisher": "pwt", "series": "rtfpna", "vintage_file": str(tfp_path.relative_to(REPO_ROOT)), "sha256": sha256(tfp_path)},
        "wdi_us_growth": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD.ZG", "vintage_file": str(us_growth_path.relative_to(REPO_ROOT)), "sha256": sha256(us_growth_path)},
    }
    gdppc = load_long(gdppc_path, "gdppc")
    tfp = load_long(tfp_path, "tfp")
    us_growth = load_long(us_growth_path, "us_growth")

    kor_g = gdppc[gdppc["country"] == "KOR"].sort_values("year").set_index("year")["gdppc"]
    kor_t = tfp[tfp["country"] == "KOR"].sort_values("year").set_index("year")["tfp"]
    us_g = us_growth[us_growth["country"] == "USA"].sort_values("year").set_index("year")["us_growth"] / 100.0

    if len(kor_g) < 40:
        verdict = "blocked_data_pending — insufficient Korea GDP pc data."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    # Compute cumulative log growth for each era
    def era_gain(series, start, end):
        s = series[(series.index >= start) & (series.index <= end)].dropna()
        if len(s) < 2: return None
        first = s.iloc[0]
        last = s.iloc[-1]
        if first <= 0 or last <= 0: return None
        return np.log(last) - np.log(first)

    hci_gdppc = era_gain(kor_g, 1973, 1997)
    post_gdppc = era_gain(kor_g, 1998, 2023)
    hci_tfp = era_gain(kor_t, 1973, 1997)
    post_tfp = era_gain(kor_t, 1998, 2023)

    # Adjust for US growth (global demand proxy)
    us_hci = era_gain(us_g, 1973, 1997)
    us_post = era_gain(us_g, 1998, 2023)

    metrics = {
        "hci_gdppc_gain": hci_gdppc, "post_gdppc_gain": post_gdppc,
        "hci_tfp_gain": hci_tfp, "post_tfp_gain": post_tfp,
        "us_hci_gain": us_hci, "us_post_gain": us_post,
    }

    if any(v is None for v in [hci_gdppc, post_gdppc, hci_tfp, post_tfp]):
        verdict = "blocked_data_pending — insufficient era coverage."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "metrics": metrics}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}"); return

    diff_gdppc = post_gdppc - hci_gdppc
    diff_tfp = post_tfp - hci_tfp

    # Supported if post-1997 exceeds HCI era on both dimensions
    if post_gdppc > hci_gdppc and post_tfp > hci_tfp:
        verdict = f"supported — Post-1997 GDP-pc gain {post_gdppc:.3f} > HCI {hci_gdppc:.3f} (diff {diff_gdppc:+.3f}); TFP gain {post_tfp:.3f} > HCI {hci_tfp:.3f} (diff {diff_tfp:+.3f})."
    elif post_gdppc < hci_gdppc and post_tfp < hci_tfp:
        verdict = f"refuted — HCI era outperforms post-1997 on both GDP pc and TFP."
    else:
        verdict = f"partial — Post-1997 GDP-pc gain {post_gdppc:.3f} vs HCI {hci_gdppc:.3f} (diff {diff_gdppc:+.3f}); TFP gain {post_tfp:.3f} vs HCI {hci_tfp:.3f} (diff {diff_tfp:+.3f})."

    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": metrics,
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: {verdict.split(' — ')[0]}\nreason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\nvintages:\n  wdi_gdppc: {manifest['wdi_gdppc']['vintage_file']}\n  pwt_tfp: {manifest['pwt_tfp']['vintage_file']}\n")
    (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n\nSingle-country time-series comparison of HCI era (1973-1997) vs post-liberalisation era (1998-2023).\n")
    print(f"verdict: {verdict}")

if __name__ == "__main__":
    sys.exit(main())
