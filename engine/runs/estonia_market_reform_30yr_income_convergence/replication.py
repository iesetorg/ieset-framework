#!/usr/bin/env python3
"""Replication — Estonia market reform and 30-year income convergence, 1991-2019.

Spec: Estonia's radical market reform predicts stronger 1991-2019 GDP-per-capita
convergence than more gradual post-Soviet reform comparators.

Design:
  1. Estonia + post-Soviet / CEE comparator set.
  2. PWT RGDPE per capita 1991-2019.
  3. Convergence measured as log GDPpc relative to Germany (the largest
     nearby frontier economy with continuous PWT data).
  4. Annualised log convergence slope 1991-2019 for each country.
  5. Compare Estonia's slope to the comparator median.

Falsification:
  SUPPORTED if Estonia convergence slope >= comparator median + 0.50 pp/yr.
  REFUTED if Estonia convergence slope <= comparator median.
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
HID = "estonia_market_reform_30yr_income_convergence"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1991
END_YEAR = 2019
DIFF_THRESHOLD = 0.005  # 0.5 pp/yr

# Comparator set: post-Soviet + CEE transition economies
COMPARATORS = [
    "LVA", "LTU", "POL", "CZE", "SVK", "HUN", "SVN", "HRV",
    "BGR", "ROU", "RUS", "UKR", "BLR", "KAZ", "GEO", "ARM", "AZE", "MDA",
]
TARGET = "EST"
FRONTIER = "DEU"


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

    pwt_path = latest("pwt", "pwt_full")
    manifest = {
        "pwt": {
            "publisher": "pwt", "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pwt_path),
        },
    }

    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt[(pwt["year"] >= BASE_YEAR) & (pwt["year"] <= END_YEAR)]
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]

    # Frontier (Germany)
    frontier = pwt[pwt["country_iso3"] == FRONTIER][["year", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "frontier_rgdpe_pc"})
    panel = pwt.merge(frontier, on="year", how="inner")
    panel["log_rel_frontier"] = np.log(panel["rgdpe_pc"] / panel["frontier_rgdpe_pc"])

    # Compute endpoint slopes 1991-2019
    countries = [TARGET] + COMPARATORS
    rows = []
    for iso3 in countries:
        sub = panel[panel["country_iso3"] == iso3].sort_values("year")
        if len(sub) < 2:
            continue
        base = sub[sub["year"] == BASE_YEAR]
        end = sub[sub["year"] == END_YEAR]
        if base.empty or end.empty:
            continue
        log_rel_base = float(base["log_rel_frontier"].iloc[0])
        log_rel_end = float(end["log_rel_frontier"].iloc[0])
        slope = (log_rel_end - log_rel_base) / (END_YEAR - BASE_YEAR)
        rows.append({
            "country_iso3": iso3,
            "log_rel_1991": log_rel_base,
            "log_rel_2019": log_rel_end,
            "convergence_slope": slope,
            "is_estonia": iso3 == TARGET,
        })

    results = pd.DataFrame(rows)
    if len(results) < 5:
        verdict = "blocked_data_pending — insufficient comparator coverage in PWT."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(results))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    est = results[results["is_estonia"]]
    comp = results[~results["is_estonia"]]
    est_slope = float(est["convergence_slope"].iloc[0]) if len(est) else float("nan")
    comp_median = float(comp["convergence_slope"].median())
    comp_mean = float(comp["convergence_slope"].mean())
    diff = est_slope - comp_median

    if est_slope >= comp_median + DIFF_THRESHOLD:
        verdict = (
            f"supported — Estonia convergence slope {est_slope*100:+.2f}pp/yr vs comparator "
            f"median {comp_median*100:+.2f}pp/yr (diff {diff*100:+.2f}pp, threshold >= {DIFF_THRESHOLD*100:.1f}pp)."
        )
    elif est_slope <= comp_median:
        verdict = (
            f"refuted — Estonia slope {est_slope*100:+.2f}pp/yr at or below comparator median "
            f"{comp_median*100:+.2f}pp/yr (diff {diff*100:+.2f}pp)."
        )
    else:
        verdict = (
            f"partial — Estonia slope {est_slope*100:+.2f}pp/yr vs comparator median "
            f"{comp_median*100:+.2f}pp/yr (diff {diff*100:+.2f}pp); below {DIFF_THRESHOLD*100:.1f}pp threshold."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_comparators": int(len(comp)),
            "estonia_slope": est_slope,
            "comparator_median_slope": comp_median,
            "comparator_mean_slope": comp_mean,
            "diff_vs_median": diff,
        },
        "threshold": f"estonia_slope >= comparator_median + {DIFF_THRESHOLD*100:.1f}pp",
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
        f"| {r['country_iso3']} | {r['log_rel_1991']:+.3f} | {r['log_rel_2019']:+.3f} | {r['convergence_slope']*100:+.2f}pp | "
        f"{'Estonia' if r['is_estonia'] else 'Comparator'} |"
        for r in rows
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Estonia vs {len(comp)} post-Soviet/CEE comparators. Convergence measured as log
GDP-per-capita (PWT RGDPE) relative to Germany, endpoint slope {BASE_YEAR}-{END_YEAR}.

## Threshold

SUPPORTED if Estonia annualised convergence slope ≥ comparator median + {DIFF_THRESHOLD*100:.1f}pp/yr.
REFUTED if Estonia slope ≤ comparator median.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Estonia slope | {est_slope*100:+.2f}pp/yr |
| Comparator median | {comp_median*100:+.2f}pp/yr |
| Comparator mean | {comp_mean*100:+.2f}pp/yr |
| Diff vs median | {diff*100:+.2f}pp/yr |

## Country panel

| ISO3 | Log rel 1991 | Log rel 2019 | Slope | Group |
|---:|---:|---:|---:|:---|
{rows_md}

## Limitations

- Endpoint slope is sensitive to single-year measurement error in 1991 or 2019.
- Germany may not be the right frontier benchmark for all comparators.
- Does not control for initial reform intensity, EU accession timing, or
  geographic / trade advantages.
- Estonia's small population and proximity to Finland may confound reform effects.

## Next robustness checks

- Use EU-15 average instead of Germany as frontier.
- Control for initial income level (convergence conditional on β-convergence).
- Extend to 2022/2023 using WDI where PWT ends.
- Add Baltic peers (LVA, LTU) as a separate sub-group comparison.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
