#!/usr/bin/env python3
"""Replication — Developmental state to market transition success, 1980-2019.

Spec: The strongest long-run performers are countries that use developmentalist
tools for catch-up, then transition toward market competition, fiscal discipline,
and rule-bound institutions before frontier convergence stalls.

Design:
  1. Classify countries by V-Dem state ownership (`v2clstown`) in 1980 and 2010.
     Higher = less state ownership (more private/market).
  2. Three groups:
     - Transitioned: bottom quartile in 1980 (high state) AND top half in 2010 (market).
     - Persistent developmental: bottom quartile in both 1980 and 2010.
     - Persistent market: top half in both 1980 and 2010.
  3. Compare PWT GDP-per-capita growth 1980-2019 across groups.

Falsification:
  SUPPORTED if transitioned mean growth >= persistent_dev_mean + 0.50 pp/yr
             AND transitioned mean growth >= persistent_market_mean − 0.50 pp/yr.
  REFUTED if transitioned mean growth < persistent_dev_mean.
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
HID = "developmental_state_to_market_transition_success"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1980
MID_YEAR = 2010
END_YEAR = 2019
DIFF_THRESHOLD = 0.005


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    vdem_path = latest("vdem", "vdem_cy_full")
    pwt_path = latest("pwt", "pwt_full")

    manifest = {
        "vdem": {
            "publisher": "vdem", "series": "vdem_cy_full",
            "vintage_file": str(vdem_path.relative_to(REPO_ROOT)), "sha256": sha256(vdem_path),
        },
        "pwt": {
            "publisher": "pwt", "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path),
        },
    }

    vdem = pq.read_table(vdem_path).to_pandas()
    vdem = vdem[vdem["country_text_id"].notna() & (vdem["country_text_id"].str.len() == 3)]
    vdem = vdem[["country_text_id", "year", "v2clstown"]].copy()
    vdem = vdem.rename(columns={"country_text_id": "country"})
    vdem["year"] = vdem["year"].astype(int)
    vdem = vdem.dropna(subset=["v2clstown"])

    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]

    # State ownership in base and mid years
    own_base = vdem[vdem["year"] == BASE_YEAR][["country", "v2clstown"]].rename(columns={"v2clstown": "own_base"})
    own_mid = vdem[vdem["year"] == MID_YEAR][["country", "v2clstown"]].rename(columns={"v2clstown": "own_mid"})

    # GDP pc growth
    gdp_base = pwt[pwt["year"] == BASE_YEAR][["country", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "gdp_base"})
    gdp_end = pwt[pwt["year"] == END_YEAR][["country", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "gdp_end"})

    df = own_base.merge(own_mid, on="country", how="inner").merge(gdp_base, on="country", how="inner").merge(gdp_end, on="country", how="inner")
    df = df.dropna()

    if len(df) < 20:
        verdict = "blocked_data_pending — insufficient country coverage after merges."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # Define groups
    q25_base = df["own_base"].quantile(0.25)
    q50_base = df["own_base"].quantile(0.50)
    q50_mid = df["own_mid"].quantile(0.50)

    df["persistent_dev"] = (df["own_base"] <= q25_base) & (df["own_mid"] <= q25_base)
    df["persistent_market"] = (df["own_base"] >= q50_base) & (df["own_mid"] >= q50_mid)
    df["transitioned"] = (df["own_base"] <= q25_base) & (df["own_mid"] >= q50_mid)

    df["growth"] = (np.log(df["gdp_end"]) - np.log(df["gdp_base"])) / (END_YEAR - BASE_YEAR)

    dev = df[df["persistent_dev"]]
    mkt = df[df["persistent_market"]]
    trans = df[df["transitioned"]]

    mean_dev = float(dev["growth"].mean()) if len(dev) else float("nan")
    mean_mkt = float(mkt["growth"].mean()) if len(mkt) else float("nan")
    mean_trans = float(trans["growth"].mean()) if len(trans) else float("nan")

    diff_vs_dev = mean_trans - mean_dev
    diff_vs_mkt = mean_trans - mean_mkt

    # Verdict
    if (mean_trans >= mean_dev + DIFF_THRESHOLD) and (mean_trans >= mean_mkt - DIFF_THRESHOLD):
        verdict = (
            f"supported — Transitioned {mean_trans*100:+.2f}%/yr vs persistent-dev {mean_dev*100:+.2f}%/yr "
            f"(diff {diff_vs_dev*100:+.2f}pp) and vs persistent-market {mean_mkt*100:+.2f}%/yr "
            f"(diff {diff_vs_mkt*100:+.2f}pp)."
        )
    elif mean_trans < mean_dev:
        verdict = (
            f"refuted — Transitioned {mean_trans*100:+.2f}%/yr underperforms persistent-dev "
            f"{mean_dev*100:+.2f}%/yr (diff {diff_vs_dev*100:+.2f}pp)."
        )
    else:
        verdict = (
            f"partial — Transitioned {mean_trans*100:+.2f}%/yr vs persistent-dev {mean_dev*100:+.2f}%/yr "
            f"(diff {diff_vs_dev*100:+.2f}pp) and vs persistent-market {mean_mkt*100:+.2f}%/yr "
            f"(diff {diff_vs_mkt*100:+.2f}pp); does not meet both thresholds."
        )

    country_rows = []
    for _, r in df.iterrows():
        group = None
        if r["persistent_dev"]:
            group = "persistent_dev"
        elif r["persistent_market"]:
            group = "persistent_market"
        elif r["transitioned"]:
            group = "transitioned"
        if group:
            country_rows.append({
                "country_iso3": r["country"],
                "v2clstown_1980": float(r["own_base"]),
                "v2clstown_2010": float(r["own_mid"]),
                "group": group,
                "annual_growth_1980_2019": float(r["growth"]),
            })

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_countries_total": int(len(df)),
            "n_persistent_dev": int(len(dev)),
            "n_persistent_market": int(len(mkt)),
            "n_transitioned": int(len(trans)),
            "mean_growth_persistent_dev": mean_dev,
            "mean_growth_persistent_market": mean_mkt,
            "mean_growth_transitioned": mean_trans,
            "diff_vs_dev": diff_vs_dev,
            "diff_vs_mkt": diff_vs_mkt,
            "q25_own_1980": q25_base,
            "q50_own_1980": q50_base,
            "q50_own_2010": q50_mid,
        },
        "threshold": f"trans >= dev + {DIFF_THRESHOLD*100:.1f}pp and trans >= mkt - {DIFF_THRESHOLD*100:.1f}pp",
        "countries": country_rows,
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
        "sha256": {k: v["sha256"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict.split(' — ')[0]}\n"
        f"reason: {verdict.split(' — ')[1] if ' — ' in verdict else verdict}\n"
        "vintages:\n"
        + "".join(f"  {k}: {v['vintage_file']}\n" for k, v in manifest.items())
    )

    rows_md = "\n".join(
        f"| {r['country_iso3']} | {r['v2clstown_1980']:.3f} | {r['v2clstown_2010']:.3f} | "
        f"{r['group']} | {r['annual_growth_1980_2019']*100:+.2f}% |"
        for r in country_rows
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Countries classified by V-Dem `v2clstown` (state ownership of economy, higher = less
state ownership) in {BASE_YEAR} and {MID_YEAR}.

- **Persistent developmental**: bottom quartile in both years.
- **Persistent market**: top half in both years.
- **Transitioned**: bottom quartile in {BASE_YEAR}, top half in {MID_YEAR}.

Outcome: annualised log GDP-per-capita growth {BASE_YEAR}-{END_YEAR} (PWT).

## Threshold

SUPPORTED if transitioned mean growth ≥ persistent-dev mean + {DIFF_THRESHOLD*100:.1f}pp/yr
AND transitioned mean growth ≥ persistent-market mean − {DIFF_THRESHOLD*100:.1f}pp/yr.
REFUTED if transitioned mean growth < persistent-dev mean growth.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Total countries | {len(df)} |
| Persistent developmental | {len(dev)} |
| Persistent market | {len(mkt)} |
| Transitioned | {len(trans)} |
| Persistent dev growth | {mean_dev*100:+.2f}%/yr |
| Persistent market growth | {mean_mkt*100:+.2f}%/yr |
| Transitioned growth | {mean_trans*100:+.2f}%/yr |
| Diff vs dev | {diff_vs_dev*100:+.2f}pp/yr |
| Diff vs market | {diff_vs_mkt*100:+.2f}pp/yr |

## Country panel

| ISO3 | v2clstown 1980 | v2clstown 2010 | Group | Growth |
|---:|---:|---:|:---|---:|
{rows_md}

## Limitations

- V-Dem `v2clstown` measures state ownership of the economy, not the full
  developmental-state toolkit (directed credit, industrial policy, export discipline).
- Classification into quartiles is mechanical and may mislabel countries with
  idiosyncratic ownership structures (e.g., Singapore, Norway).
- 1980 V-Dem coverage is good but some scores are back-projected.
- No control for initial income level, commodity booms, or geopolitical shocks.

## Next robustness checks

- Use WGI RQ or Fraser EFW as alternative transition proxy.
- Vary the classification years (1990, 2000).
- Control for initial GDP per capita and population.
- Add a "failed transition" group (high state ownership that rose then fell).
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
