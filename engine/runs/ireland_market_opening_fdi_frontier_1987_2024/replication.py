#!/usr/bin/env python3
"""Replication — Ireland market opening, FDI, and frontier convergence, 1987-2019.

Spec: Ireland's long-run convergence is better predicted by trade openness, tax
competitiveness, and FDI entry than by classic industrial planning.

Design:
  1. Ireland + OECD comparator set.
  2. Mean FDI inflows (% of GDP, WDI BX.KLT.DINV.WD.GD.ZS) 1987-2019.
  3. GDP-per-capita convergence slope (PWT RGDPE pc relative to US) 1987-2019.
  4. Grade: Ireland must be in the top half on both FDI intensity and
     convergence slope for SUPPORT.

Falsification:
  SUPPORTED if Ireland FDI/GDP ≥ comparator median AND Ireland convergence slope
             ≥ comparator median + 0.50 pp/yr.
  REFUTED if Ireland convergence slope < comparator median.
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
HID = "ireland_market_opening_fdi_frontier_1987_2024"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1987
END_YEAR = 2019
DIFF_THRESHOLD = 0.005

TARGET = "IRL"
FRONTIER = "USA"

COUNTRIES = [
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "CZE", "DEU", "DNK", "ESP",
    "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL", "ISR", "ITA",
    "JPN", "KOR", "LTU", "LUX", "LVA", "MEX", "NLD", "NOR", "NZL", "POL",
    "PRT", "SVK", "SVN", "SWE", "TUR", "USA",
]


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


def load_wdi(path: Path, name: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fdi_path = latest("world_bank_wdi", "BX.KLT.DINV.WD.GD.ZS")
    pwt_path = latest("pwt", "pwt_full")
    manifest = {
        "wdi_fdi": {
            "publisher": "world_bank_wdi", "series": "BX.KLT.DINV.WD.GD.ZS",
            "vintage_file": str(fdi_path.relative_to(REPO_ROOT)), "sha256": sha256(fdi_path),
        },
        "pwt": {
            "publisher": "pwt", "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path),
        },
    }

    fdi = load_wdi(fdi_path, "fdi_gdp")
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt[(pwt["year"] >= BASE_YEAR) & (pwt["year"] <= END_YEAR)]
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]
    pwt = pwt.rename(columns={"country_iso3": "country"})

    # Frontier
    frontier = pwt[pwt["country"] == FRONTIER][["year", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "frontier_rgdpe_pc"})
    gdp = pwt.merge(frontier, on="year", how="inner")
    gdp["log_rel_frontier"] = np.log(gdp["rgdpe_pc"] / gdp["frontier_rgdpe_pc"])

    # Country-level aggregates
    rows = []
    for iso3 in COUNTRIES:
        gdp_sub = gdp[gdp["country"] == iso3].sort_values("year")
        fdi_sub = fdi[(fdi["country"] == iso3) & (fdi["year"] >= BASE_YEAR) & (fdi["year"] <= END_YEAR)]
        if gdp_sub.empty or fdi_sub.empty:
            continue
        base = gdp_sub[gdp_sub["year"] == BASE_YEAR]
        end = gdp_sub[gdp_sub["year"] == END_YEAR]
        if base.empty or end.empty:
            continue
        log_rel_base = float(base["log_rel_frontier"].iloc[0])
        log_rel_end = float(end["log_rel_frontier"].iloc[0])
        slope = (log_rel_end - log_rel_base) / (END_YEAR - BASE_YEAR)
        mean_fdi = float(fdi_sub["fdi_gdp"].mean())
        rows.append({
            "country_iso3": iso3,
            "log_rel_1987": log_rel_base,
            "log_rel_2019": log_rel_end,
            "convergence_slope": slope,
            "mean_fdi_gdp": mean_fdi,
            "is_ireland": iso3 == TARGET,
        })

    results = pd.DataFrame(rows)
    if len(results) < 10:
        verdict = "blocked_data_pending — insufficient comparator coverage."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(results))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    ire = results[results["is_ireland"]]
    comp = results[~results["is_ireland"]]
    ire_slope = float(ire["convergence_slope"].iloc[0]) if len(ire) else float("nan")
    ire_fdi = float(ire["mean_fdi_gdp"].iloc[0]) if len(ire) else float("nan")
    comp_median_slope = float(comp["convergence_slope"].median())
    comp_median_fdi = float(comp["mean_fdi_gdp"].median())
    diff_slope = ire_slope - comp_median_slope

    fdi_above_median = ire_fdi >= comp_median_fdi
    slope_above_median = ire_slope >= comp_median_slope + DIFF_THRESHOLD

    if fdi_above_median and slope_above_median:
        verdict = (
            f"supported — Ireland FDI {ire_fdi:.1f}% of GDP vs OECD median {comp_median_fdi:.1f}%; "
            f"convergence slope {ire_slope*100:+.2f}pp/yr vs median {comp_median_slope*100:+.2f}pp/yr "
            f"(diff {diff_slope*100:+.2f}pp)."
        )
    elif not slope_above_median and ire_slope < comp_median_slope:
        verdict = (
            f"refuted — Ireland convergence slope {ire_slope*100:+.2f}pp/yr below OECD median "
            f"{comp_median_slope*100:+.2f}pp/yr."
        )
    else:
        verdict = (
            f"partial — Ireland FDI {ire_fdi:.1f}% vs median {comp_median_fdi:.1f}%; "
            f"slope {ire_slope*100:+.2f}pp/yr vs median {comp_median_slope*100:+.2f}pp/yr. "
            f"Does not meet both conditions."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_comparators": int(len(comp)),
            "ireland_convergence_slope": ire_slope,
            "ireland_mean_fdi_gdp": ire_fdi,
            "comparator_median_slope": comp_median_slope,
            "comparator_median_fdi": comp_median_fdi,
            "diff_slope_vs_median": diff_slope,
            "fdi_above_median": fdi_above_median,
            "slope_above_threshold": slope_above_median,
        },
        "threshold": "ireland_fdi >= median AND ireland_slope >= median + 0.5pp",
        "countries": rows,
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
        f"| {r['country_iso3']} | {r['mean_fdi_gdp']:.1f} | {r['log_rel_1987']:+.3f} | "
        f"{r['log_rel_2019']:+.3f} | {r['convergence_slope']*100:+.2f}pp | "
        f"{'Ireland' if r['is_ireland'] else 'Comparator'} |"
        for r in rows
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Ireland vs {len(comp)} OECD comparators, {BASE_YEAR}-{END_YEAR}. Mean FDI inflows
(% of GDP, WDI) and log GDP-per-capita convergence slope relative to US (PWT).

## Threshold

SUPPORTED if Ireland mean FDI/GDP ≥ comparator median AND convergence slope
≥ comparator median + {DIFF_THRESHOLD*100:.1f}pp/yr.
REFUTED if Ireland slope < comparator median.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Ireland mean FDI/GDP | {ire_fdi:.1f}% |
| OECD median FDI/GDP | {comp_median_fdi:.1f}% |
| Ireland convergence slope | {ire_slope*100:+.2f}pp/yr |
| OECD median slope | {comp_median_slope*100:+.2f}pp/yr |
| Diff vs median | {diff_slope*100:+.2f}pp/yr |

## Country panel

| ISO3 | Mean FDI/GDP | Log rel 1987 | Log rel 2019 | Slope | Group |
|---:|---:|---:|---:|---:|:---|
{rows_md}

## Limitations

- FDI/GDP is a flow measure that can be distorted by corporate-tax routing
  (double-Irish, etc.). Does not distinguish real investment from pass-through.
- Endpoint slope sensitive to 1987 and 2019 levels.
- Tax competitiveness and trade openness are not directly measured.
- US is used as frontier benchmark; EU-15 average may be more appropriate for Ireland.

## Next robustness checks

- Use EU-15 average instead of US as frontier.
- Control for initial income level.
- Use median FDI instead of mean to reduce outlier sensitivity.
- Separate pre- and post-Celtic-Tiger periods.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
