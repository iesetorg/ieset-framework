#!/usr/bin/env python3
"""Replication — Frontier income persistence and market institutions, 1960-2018.

Spec: Countries with stronger market-institution scores in 1960 retain high-income
frontier status through 2018 more often than countries with weaker property-rights
scores.

Design:
  1. Classify countries by Maddison GDP-per-capita quartile in 1960.
  2. Among 1960-top-quartile countries, split by V-Dem v2x_liberal median
     (market-institution proxy).
  3. Compare retention in top income quartile by 2018.
  4. Compare absolute GDP-per-capita growth 1960-2018.

Falsification:
  SUPPORTED if high-liberal retention >= 50% AND
             (high-liberal retention − low-liberal retention) >= 15pp.
  REFUTED if high-liberal retention < low-liberal retention.
  Otherwise PARTIAL.

Limitation: V-Dem v2x_liberal is a liberal-component index (rule of law, judicial
independence, legislative constraints), not a direct market-institution measure.
1960 coverage is good but not universal.
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
HID = "frontier_income_persistence_market_institutions_1960_2024"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1960
END_YEAR = 2018
RETENTION_THRESHOLD = 0.50
DIFF_THRESHOLD = 0.15


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


def load_maddison(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    return t[["country_iso3", "year", "gdppc"]].copy()


def load_vdem(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[t["country_text_id"].notna() & (t["country_text_id"].str.len() == 3)]
    out = t[["country_text_id", "year", "v2x_liberal"]].copy()
    out = out.rename(columns={"country_text_id": "country_iso3"})
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype(int)
    return out.dropna(subset=["v2x_liberal"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    madd_path = latest("maddison", "gdppc")
    vdem_path = latest("vdem", "vdem_cy_full")

    manifest = {
        "maddison_gdppc": {
            "publisher": "maddison",
            "series": "gdppc",
            "vintage_file": str(madd_path.relative_to(REPO_ROOT)),
            "sha256": sha256(madd_path),
        },
        "vdem": {
            "publisher": "vdem",
            "series": "vdem_cy_full",
            "vintage_file": str(vdem_path.relative_to(REPO_ROOT)),
            "sha256": sha256(vdem_path),
        },
    }

    madd = load_maddison(madd_path)
    vdem = load_vdem(vdem_path)

    # Base-year income
    base = madd[madd["year"] == BASE_YEAR][["country_iso3", "gdppc"]].copy()
    base = base.rename(columns={"gdppc": "gdppc_base"})

    # End-year income
    end = madd[madd["year"] == END_YEAR][["country_iso3", "gdppc"]].copy()
    end = end.rename(columns={"gdppc": "gdppc_end"})

    # Institutions in base year
    inst = vdem[vdem["year"] == BASE_YEAR][["country_iso3", "v2x_liberal"]].copy()
    inst = inst.rename(columns={"v2x_liberal": "liberal_base"})

    # Merge
    df = base.merge(end, on="country_iso3", how="inner").merge(inst, on="country_iso3", how="inner")
    df = df.dropna()

    if len(df) < 20:
        verdict = "blocked_data_pending — insufficient country overlap between Maddison and V-Dem in 1960."
        diagnostics = {
            "hypothesis_id": HID,
            "verdict": verdict,
            "n_countries": int(len(df)),
            "threshold": f"retention_high >= {RETENTION_THRESHOLD} and diff >= {DIFF_THRESHOLD}",
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n"
        )
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # Top income quartile in base year
    q75_base = df["gdppc_base"].quantile(0.75)
    df["frontier_1960"] = df["gdppc_base"] >= q75_base

    # Top income quartile in end year
    q75_end = df["gdppc_end"].quantile(0.75)
    df["frontier_2018"] = df["gdppc_end"] >= q75_end

    frontier = df[df["frontier_1960"]].copy()
    if len(frontier) < 10:
        verdict = "blocked_data_pending — fewer than 10 frontier countries in 1960."
        diagnostics = {
            "hypothesis_id": HID,
            "verdict": verdict,
            "n_frontier_countries": int(len(frontier)),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n"
        )
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # Split frontier by median liberal score
    median_lib = frontier["liberal_base"].median()
    frontier["high_liberal"] = frontier["liberal_base"] >= median_lib

    high = frontier[frontier["high_liberal"]]
    low = frontier[~frontier["high_liberal"]]

    high_retention = float(high["frontier_2018"].mean()) if len(high) else 0.0
    low_retention = float(low["frontier_2018"].mean()) if len(low) else 0.0
    diff = high_retention - low_retention

    high_growth = float((np.log(high["gdppc_end"]) - np.log(high["gdppc_base"])).mean()) if len(high) else 0.0
    low_growth = float((np.log(low["gdppc_end"]) - np.log(low["gdppc_base"])).mean()) if len(low) else 0.0

    # Verdict
    if high_retention >= RETENTION_THRESHOLD and diff >= DIFF_THRESHOLD:
        verdict = (
            f"supported — High-liberal frontier retention {high_retention:.1%} vs "
            f"low-liberal {low_retention:.1%} (diff {diff:+.1%}pp, threshold >= {DIFF_THRESHOLD:.0%})."
        )
    elif high_retention < low_retention:
        verdict = (
            f"refuted — High-liberal retention {high_retention:.1%} below low-liberal "
            f"{low_retention:.1%} (diff {diff:+.1%}pp)."
        )
    else:
        verdict = (
            f"partial — High-liberal retention {high_retention:.1%} vs low-liberal "
            f"{low_retention:.1%} (diff {diff:+.1%}pp); does not meet full threshold."
        )

    # Country-level detail
    country_rows = []
    for _, r in frontier.iterrows():
        country_rows.append({
            "country_iso3": r["country_iso3"],
            "gdppc_1960": float(r["gdppc_base"]),
            "gdppc_2018": float(r["gdppc_end"]),
            "v2x_liberal_1960": float(r["liberal_base"]),
            "high_liberal": bool(r["high_liberal"]),
            "retained_frontier": bool(r["frontier_2018"]),
            "log_growth_1960_2018": float(np.log(r["gdppc_end"]) - np.log(r["gdppc_base"])),
        })

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_countries_total": int(len(df)),
            "n_frontier_1960": int(len(frontier)),
            "n_high_liberal": int(len(high)),
            "n_low_liberal": int(len(low)),
            "high_liberal_retention_rate": high_retention,
            "low_liberal_retention_rate": low_retention,
            "retention_diff": diff,
            "high_liberal_mean_log_growth": high_growth,
            "low_liberal_mean_log_growth": low_growth,
            "median_liberal_threshold": median_lib,
            "q75_gdppc_1960": q75_base,
            "q75_gdppc_2018": q75_end,
        },
        "threshold": f"retention_high >= {RETENTION_THRESHOLD} and diff >= {DIFF_THRESHOLD}",
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
        f"| {r['country_iso3']} | {r['gdppc_1960']:.0f} | {r['gdppc_2018']:.0f} | "
        f"{r['v2x_liberal_1960']:.3f} | {'yes' if r['high_liberal'] else 'no'} | "
        f"{'yes' if r['retained_frontier'] else 'no'} | {r['log_growth_1960_2018']:.3f} |"
        for r in country_rows
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Countries in the top quartile of Maddison GDP-per-capita in {BASE_YEAR} are classified as
"frontier". Among these, split by median V-Dem `v2x_liberal` (market-institution proxy).
Outcome: share retaining top-quartile income status by {END_YEAR}.

## Threshold

SUPPORTED if high-liberal retention >= {RETENTION_THRESHOLD:.0%} AND
(high-liberal − low-liberal) >= {DIFF_THRESHOLD:.0%}pp.
REFUTED if high-liberal retention < low-liberal retention.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Total countries with data | {len(df)} |
| Frontier 1960 | {len(frontier)} |
| High-liberal (≥ median) | {len(high)} |
| Low-liberal (< median) | {len(low)} |
| High-liberal retention | {high_retention:.1%} |
| Low-liberal retention | {low_retention:.1%} |
| Difference | {diff:+.1%}pp |
| High-liberal mean log growth | {high_growth:.3f} |
| Low-liberal mean log growth | {low_growth:.3f} |

## Country panel

| ISO3 | GDPpc 1960 | GDPpc 2018 | v2x_liberal | High liberal | Retained | Log growth |
|---|---:|---:|---:|:---:|:---:|:---:|
{rows_md}

## Limitations

- V-Dem `v2x_liberal` is a liberal-democracy component, not a direct market-institution
  index. It correlates with property rights and rule of law but also captures judicial
  independence and legislative constraints.
- 1960 V-Dem scores are back-projected via expert coding for some countries.
- No direct measure of state-directed-credit intensity in 1960; low-liberal group is an
  imperfect proxy for the developmentalist-comparison group in the original hypothesis.
- Income threshold is relative (top quartile), not absolute frontier.

## Next robustness checks

- Use WGI Rule of Law (1996 earliest) as alternative institution proxy.
- Use absolute US-relative frontier threshold instead of quartile.
- Control for initial population size and resource endowments.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
