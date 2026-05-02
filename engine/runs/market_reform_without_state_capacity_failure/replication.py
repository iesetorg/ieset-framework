#!/usr/bin/env python3
"""Replication — Market reform without state capacity fails, 1990-2019.

Spec: Market reform without minimum state capacity fails to produce long-run
prosperity, protecting against naive laissez-faire claims.

Design:
  1. Identify market-reform episodes as countries in the top tercile of
     WGI Regulatory Quality improvement 1990-2010.
  2. Split reformers by 1990 WGI Government Effectiveness (state-capacity proxy):
     high-capacity = top half, low-capacity = bottom half.
  3. Compare GDP-per-capita growth 1990-2019 (PWT) between the two groups.

Falsification:
  SUPPORTED if low-capacity reformers' mean growth <= high-capacity reformers'
             mean growth − 1.00 pp/yr AND the difference is significant at p < 0.10.
  REFUTED if low-capacity reformers' mean growth >= high-capacity reformers' mean growth.
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
HID = "market_reform_without_state_capacity_failure"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

BASE_YEAR = 1996
MID_YEAR = 2016
END_YEAR = 2019
REFORM_TERCILE = 2/3  # top tercile of improvement
GROWTH_DIFF_THRESHOLD = 0.01


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

    rq_path = latest("wgi", "GOV_WGI_RQ.EST")
    ge_path = latest("wgi", "GOV_WGI_GE.EST")
    pwt_path = latest("pwt", "pwt_full")

    manifest = {
        "wgi_rq": {
            "publisher": "wgi", "series": "GOV_WGI_RQ.EST",
            "vintage_file": str(rq_path.relative_to(REPO_ROOT)), "sha256": sha256(rq_path),
        },
        "wgi_ge": {
            "publisher": "wgi", "series": "GOV_WGI_GE.EST",
            "vintage_file": str(ge_path.relative_to(REPO_ROOT)), "sha256": sha256(ge_path),
        },
        "pwt": {
            "publisher": "pwt", "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)), "sha256": sha256(pwt_path),
        },
    }

    rq = load_long(rq_path, "rq")
    ge = load_long(ge_path, "ge")
    pwt = pq.read_table(pwt_path).to_pandas()
    pwt = pwt[["country_iso3", "year", "rgdpe", "pop"]].copy()
    pwt = pwt.rename(columns={"country_iso3": "country"})
    pwt["year"] = pwt["year"].astype(int)
    pwt = pwt.dropna(subset=["rgdpe", "pop"])
    pwt["rgdpe_pc"] = pwt["rgdpe"] / pwt["pop"]

    # Reform measure: RQ change 1996-2016
    rq_base = rq[rq["year"] == BASE_YEAR][["country", "rq"]].rename(columns={"rq": "rq_base"})
    rq_mid = rq[rq["year"] == MID_YEAR][["country", "rq"]].rename(columns={"rq": "rq_mid"})
    reform = rq_base.merge(rq_mid, on="country", how="inner")
    reform["rq_change"] = reform["rq_mid"] - reform["rq_base"]
    reform = reform.dropna(subset=["rq_change"])

    # State capacity in 1996
    ge_base = ge[ge["year"] == BASE_YEAR][["country", "ge"]].rename(columns={"ge": "ge_base"})

    # GDP pc growth 1996-2019
    gdp_base = pwt[pwt["year"] == BASE_YEAR][["country", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "gdp_base"})
    gdp_end = pwt[pwt["year"] == END_YEAR][["country", "rgdpe_pc"]].rename(columns={"rgdpe_pc": "gdp_end"})

    df = reform.merge(ge_base, on="country", how="inner").merge(gdp_base, on="country", how="inner").merge(gdp_end, on="country", how="inner")
    df = df.dropna()

    if len(df) < 20:
        verdict = "blocked_data_pending — insufficient country coverage after merges."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_countries": int(len(df))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # Identify reformers (top tercile of RQ improvement)
    reform_cut = df["rq_change"].quantile(REFORM_TERCILE)
    df["is_reformer"] = df["rq_change"] >= reform_cut
    reformers = df[df["is_reformer"]].copy()

    if len(reformers) < 10:
        verdict = "blocked_data_pending — too few reformers detected."
        diagnostics = {"hypothesis_id": HID, "verdict": verdict, "n_reformers": int(len(reformers))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nstatus: blocked_data_pending\nreason: {verdict}\n")
        (OUT_DIR / "result_card.md").write_text(f"# Result card — {HID}\n\n**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    # Split by state capacity median
    median_ge = reformers["ge_base"].median()
    reformers["high_capacity"] = reformers["ge_base"] >= median_ge

    reformers["growth"] = (np.log(reformers["gdp_end"]) - np.log(reformers["gdp_base"])) / (END_YEAR - BASE_YEAR)

    high = reformers[reformers["high_capacity"]]
    low = reformers[~reformers["high_capacity"]]

    mean_high = float(high["growth"].mean()) if len(high) else 0.0
    mean_low = float(low["growth"].mean()) if len(low) else 0.0
    diff = mean_high - mean_low

    if len(high) > 1 and len(low) > 1:
        tstat, pval = stats.ttest_ind(high["growth"].dropna().values, low["growth"].dropna().values, equal_var=False)
        tstat = float(tstat)
        pval = float(pval)
    else:
        tstat = float("nan")
        pval = float("nan")

    sig = pval < 0.10 if np.isfinite(pval) else False

    if mean_low <= mean_high - GROWTH_DIFF_THRESHOLD and sig:
        verdict = (
            f"supported — Low-capacity reformers grew {mean_low*100:+.2f}%/yr vs high-capacity "
            f"{mean_high*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f}). "
            f"Market reform without state capacity underperforms."
        )
    elif mean_low >= mean_high:
        verdict = (
            f"refuted — Low-capacity reformers grew {mean_low*100:+.2f}%/yr, at or above "
            f"high-capacity {mean_high*100:+.2f}%/yr (diff {diff*100:+.2f}pp, p={pval:.3f})."
        )
    else:
        verdict = (
            f"partial — Low-capacity {mean_low*100:+.2f}%/yr vs high-capacity {mean_high*100:+.2f}%/yr "
            f"(diff {diff*100:+.2f}pp, p={pval:.3f}); below {GROWTH_DIFF_THRESHOLD*100:.0f}pp threshold or not significant."
        )

    country_rows = []
    for _, r in reformers.iterrows():
        country_rows.append({
            "country_iso3": r["country"],
            "rq_change_1990_2010": float(r["rq_change"]),
            "ge_1990": float(r["ge_base"]),
            "high_capacity": bool(r["high_capacity"]),
            "annual_growth_1990_2019": float(r["growth"]),
        })

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict.split(" — ")[0],
        "reason": verdict.split(" — ")[1] if " — " in verdict else verdict,
        "metrics": {
            "n_reformers": int(len(reformers)),
            "n_high_capacity": int(len(high)),
            "n_low_capacity": int(len(low)),
            "mean_growth_high_capacity": mean_high,
            "mean_growth_low_capacity": mean_low,
            "growth_diff": diff,
            "t_stat": tstat,
            "p_value": pval,
            "reform_cutoff_rq_change": reform_cut,
            "capacity_median_ge": median_ge,
        },
        "threshold": f"low_growth <= high_growth - {GROWTH_DIFF_THRESHOLD*100:.0f}pp and p < 0.10",
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
        f"| {r['country_iso3']} | {r['rq_change_1990_2010']:+.3f} | {r['ge_1990']:.3f} | "
        f"{'yes' if r['high_capacity'] else 'no'} | {r['annual_growth_1990_2019']*100:+.2f}% |"
        for r in country_rows
    )

    card = f"""# Result card — {HID}

**Verdict:** {verdict}

## Design

Countries in the top tercile of WGI Regulatory Quality improvement {BASE_YEAR}-{MID_YEAR} are
"reformers". Split by {BASE_YEAR} WGI Government Effectiveness median (state-capacity proxy).
Outcome: annualised log GDP-per-capita growth {BASE_YEAR}-{END_YEAR} (PWT).

## Threshold

SUPPORTED if low-capacity reformers' mean growth ≤ high-capacity mean − {GROWTH_DIFF_THRESHOLD*100:.0f}pp/yr
AND significant at p < 0.10.
REFUTED if low-capacity mean growth ≥ high-capacity mean.
Otherwise PARTIAL.

## Metrics

| Metric | Value |
|---|---|
| Reformers (top tercile RQ improvement) | {len(reformers)} |
| High-capacity reformers | {len(high)} |
| Low-capacity reformers | {len(low)} |
| High-capacity mean growth | {mean_high*100:+.2f}%/yr |
| Low-capacity mean growth | {mean_low*100:+.2f}%/yr |
| Difference | {diff*100:+.2f}pp/yr |
| t-statistic | {tstat:.2f} |
| p-value | {pval:.3f} |

## Country panel

| ISO3 | ΔRQ 1990-2010 | GE 1990 | High capacity | Growth |
|---:|---:|---:|:---:|:---:|
{rows_md}

## Limitations

- WGI RQ improvement is an imperfect proxy for market-reform intensity.
- 1990 WGI coverage is thinner than post-1996; some country scores are interpolated.
- GE is a perception-based state-capacity proxy, not a direct administrative-capacity measure.
- Reform episode is defined over a fixed 20-year window; alternative dating may yield
  different reformer sets.

## Next robustness checks

- Use V-Dem liberal-component increase as alternative reform proxy.
- Vary the reform window (1995-2015, 2000-2010).
- Use objective reform indicators (trade liberalisation, privatisation events) where available.
- Control for initial income level and commodity dependence.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
