#!/usr/bin/env python3
"""Replication — us_median_wage_stagnation_1973_2000_decomposition (v1).

Spec: hypotheses/distribution/us_median_wage_stagnation_1973_2000_decomposition.yaml
Steelman: hypotheses/steelman/us_median_wage_stagnation_1973_2000_decomposition.md

Single-country time-series decomposition of the cumulative real-wage-vs-
real-GDP-per-capita gap, US, 1973→2000.

Spec channels:
  (a) total-comp-vs-wages ratio (benefit substitution, healthcare)
  (b) female LFP rise (compositional)
  (c) CPI vs GDP-deflator wedge (Feldstein measurement)
  (d) top-1% income share rise (residual rent-extraction)

Pre-registered falsification:
  0.50 ≤ compositional_and_measurement_share ≤ 0.85 AND
  0.15 ≤ top_strata_residual ≤ 0.50

DEVIATIONS:
  - BLS CES production-and-nonsupervisory wage series CES0500000008 NOT in
    vintages (only post-2024 BLS data fetched). Substitute the JST
    Macrohistory `wage` series (long-run nominal-wage index) deflated by
    JST `cpi` for the real-wage-index outcome. JST data covers 1870-2020
    and is the operational substitute for the BLS time series the spec
    requires.
  - JST does not contain a separate output-price deflator distinct from
    its CPI; the (c) "CPI vs GDP deflator" wedge channel is operationalised
    by computing a GDP-deflator-equivalent from JST `gdp` (nominal) over
    `rgdpmad` (Maddison real GDP) — order-of-magnitude only, not the
    exact BEA NIPA deflator.
  - Channel (a) total-compensation/wages ratio: BLS CES0500000002 not in
    vintages — channel skipped, flagged in deviations.
  - Channel (b) female LFP: WDI SL.TLF.CACT.FE.ZS not in vintages —
    channel skipped, flagged in deviations.
  - Channel (d) top-1% share: OWID top-1-share-of-total-income not in
    vintages; OWID Gini coefficient series substituted as a coarser
    distributional proxy (less informative than top-1% share — Gini
    moves less with top-strata capture).

Therefore the v1 decomposition is at best a TWO-channel attribution:
  - measurement (CPI vs GDP-deflator wedge)
  - residual (top-strata distributional, proxied via Gini)
plus the residual-residual (compositional + comp/wage-substitution
that we cannot estimate).
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
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "us_median_wage_stagnation_1973_2000_decomposition"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1973, 2000)
COUNTRY = "USA"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, ser: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(f"{ser}@*.parquet"),
                   key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{ser}")
    return files[-1]


def assemble() -> tuple[pd.DataFrame, dict]:
    manifest = {}

    p_jst = latest("jst", "jst_r6")
    manifest["jst_macrohistory"] = {"publisher": "jst", "series": "jst_r6",
                                    "vintage_file": str(p_jst.relative_to(REPO_ROOT)),
                                    "sha256": sha256(p_jst)}
    jst = pq.read_table(p_jst).to_pandas()
    jst = jst[jst["country_iso3"] == COUNTRY].copy()
    jst["year"] = jst["year"].astype(int)
    jst = jst[(jst["year"] >= PERIOD[0]) & (jst["year"] <= PERIOD[1])]
    jst = jst[["year", "wage", "cpi", "rgdpmad", "gdp", "pop"]].sort_values("year")

    # OWID Gini (US, 1973-2000)
    p_gini = latest("owid", "economic-inequality-gini-index")
    manifest["gini"] = {"publisher": "owid", "series": "economic-inequality-gini-index",
                        "vintage_file": str(p_gini.relative_to(REPO_ROOT)),
                        "sha256": sha256(p_gini)}
    gini = pq.read_table(p_gini).to_pandas()
    gini = gini[gini["country_iso3"] == COUNTRY].copy()
    gini = gini.rename(columns={"Gini coefficient": "gini"})
    gini["year"] = gini["year"].astype(int)
    gini = gini[["year", "gini"]]

    df = jst.merge(gini, on="year", how="left")
    return df, manifest


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df, manifest = assemble()

    # All channels normalised to 1.0 at 1973
    base_year = PERIOD[0]
    end_year = PERIOD[1]

    df = df.dropna(subset=["wage", "cpi", "rgdpmad", "pop", "gdp"]).copy()
    df["real_wage_idx"] = (df["wage"] / df["cpi"]) / (df["wage"].iloc[0] / df["cpi"].iloc[0])
    df["real_gdp_pc"] = df["rgdpmad"]
    df["real_gdp_pc_idx"] = df["real_gdp_pc"] / df["real_gdp_pc"].iloc[0]
    # GDP deflator proxy: nominal_gdp / real_gdp_mad
    df["gdp_deflator_proxy"] = df["gdp"] / df["rgdpmad"]
    df["gdp_deflator_idx"] = df["gdp_deflator_proxy"] / df["gdp_deflator_proxy"].iloc[0]
    df["cpi_idx"] = df["cpi"] / df["cpi"].iloc[0]
    df["cpi_gdp_wedge"] = df["cpi_idx"] / df["gdp_deflator_idx"]

    # Wage deflated by GDP deflator instead of CPI (Feldstein adjustment)
    df["real_wage_gdp_defl_idx"] = ((df["wage"] / df["gdp_deflator_proxy"])
                                    / (df["wage"].iloc[0] / df["gdp_deflator_proxy"].iloc[0]))

    log_wage_growth = float(np.log(df.set_index("year").loc[end_year, "real_wage_idx"]))
    log_gdp_pc_growth = float(np.log(df.set_index("year").loc[end_year, "real_gdp_pc_idx"]))
    raw_gap_log = log_gdp_pc_growth - log_wage_growth  # positive = productivity outpaced wages

    # Channel: CPI-vs-GDP-deflator wedge
    log_wage_growth_gdp_defl = float(np.log(df.set_index("year").loc[end_year, "real_wage_gdp_defl_idx"]))
    feldstein_share_of_gap = (log_wage_growth_gdp_defl - log_wage_growth) / raw_gap_log if raw_gap_log != 0 else float("nan")

    # Channel: top-strata residual (proxied via Gini delta)
    g = df.set_index("year")["gini"].dropna()
    if len(g) >= 2:
        gini_start = float(g.iloc[0])
        gini_end = float(g.iloc[-1])
        gini_delta = gini_end - gini_start
    else:
        gini_start = gini_end = gini_delta = float("nan")

    # The Gini-share calibration: assume a 1pp Gini rise corresponds to
    # roughly 1.5pp of the real-wage gap absorbed by top-strata capture
    # (rough mapping, illustrative — true mapping requires WID top-1%
    # share). We DO NOT pretend this is causally identified.
    illustrative_gini_to_gap_factor = 0.015
    top_strata_share_of_gap_proxy = (gini_delta * illustrative_gini_to_gap_factor) / raw_gap_log if (raw_gap_log != 0 and not np.isnan(gini_delta)) else float("nan")

    # Compositional + benefit-substitution channel jointly = residual
    measurement_share = feldstein_share_of_gap
    top_strata_share = top_strata_share_of_gap_proxy
    compositional_residual = 1.0 - measurement_share - top_strata_share if not (np.isnan(measurement_share) or np.isnan(top_strata_share)) else float("nan")

    # Pre-registered: channels (a)+(b)+(c) jointly absorb 50-85%
    # (we have only (c) so v1 can only test a weakened version)
    compositional_and_measurement_share = measurement_share + (compositional_residual if not np.isnan(compositional_residual) else 0)
    top_strata_residual = top_strata_share

    in_band_compmeas = (not np.isnan(compositional_and_measurement_share) and
                        0.50 <= compositional_and_measurement_share <= 0.85)
    in_band_topstrata = (not np.isnan(top_strata_residual) and
                         0.15 <= top_strata_residual <= 0.50)

    if not (np.isnan(measurement_share) or np.isnan(top_strata_share)):
        all_pass = in_band_compmeas and in_band_topstrata
        if all_pass:
            verdict = (f"supported — Feldstein measurement wedge absorbs "
                       f"{measurement_share:.0%} of cumulative wage-prod gap; Gini-proxied "
                       f"top-strata residual {top_strata_share:.0%}; compositional residual "
                       f"{compositional_residual:.0%}; both bands satisfied")
        else:
            verdict = (f"weakened — bands not jointly satisfied. Feldstein wedge "
                       f"{measurement_share:.0%}; Gini-proxied top-strata residual "
                       f"{top_strata_share:.0%}; compositional residual {compositional_residual:.0%}. "
                       f"Pre-registered top-strata band [0.15, 0.50] violated: {not in_band_topstrata}")
    else:
        verdict = "indeterminate — required series missing"
        all_pass = False

    rows = [
        {"spec": "raw_gap_log", "term": "log_real_wage_to_log_real_gdp_pc",
         "estimate": raw_gap_log, "n_obs": len(df)},
        {"spec": "channel_feldstein_wedge", "term": "cpi_vs_gdp_deflator",
         "estimate": measurement_share, "n_obs": len(df)},
        {"spec": "channel_top_strata_proxy_gini", "term": "gini_delta_to_gap",
         "estimate": top_strata_share, "n_obs": len(g)},
        {"spec": "channel_residual_compositional", "term": "implied_compositional_plus_benefit",
         "estimate": compositional_residual, "n_obs": len(df)},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diag = {
        "verdict": verdict, "all_pass": all_pass,
        "period": PERIOD,
        "log_real_wage_growth_1973_to_2000": log_wage_growth,
        "log_real_gdp_pc_growth_1973_to_2000": log_gdp_pc_growth,
        "raw_cumulative_log_gap": raw_gap_log,
        "channel_feldstein_wedge_share": measurement_share,
        "gini_1973": gini_start, "gini_2000": gini_end, "gini_delta": gini_delta,
        "top_strata_share_proxy_via_gini": top_strata_share,
        "compositional_plus_benefit_residual": compositional_residual,
        "thresholds": {"compositional_and_measurement": [0.50, 0.85],
                       "top_strata": [0.15, 0.50]},
        "in_band_compositional_and_measurement": in_band_compmeas,
        "in_band_top_strata": in_band_topstrata,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2,
                                                         default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID, "run_utc": pd.Timestamp.utcnow().isoformat(),
        "vintages": manifest,
        "deviations": [
            "BLS CES0500000008 production-nonsupervisory wage series not in vintages (BLS fetcher only carries 2024+ data); JST Macrohistory `wage` substitutes as the long-run nominal wage series, deflated by JST `cpi`.",
            "BLS CES0500000002 total-compensation series not in vintages; benefits-substitution channel skipped.",
            "WDI SL.TLF.CACT.FE.ZS female LFP not in vintages; female-LFP compositional channel skipped.",
            "OWID top-1-share-of-total-income not in vintages; substituted with OWID Gini coefficient — coarser proxy because Gini moves less with pure top-strata capture; channel attribution is illustrative not identified.",
            "GDP deflator proxied as JST nominal GDP / Maddison real GDP; not the BEA NIPA deflator the spec implies.",
            "v1 decomposition tests a weakened version of the spec: Feldstein measurement wedge + Gini-proxied top-strata + residual (compositional+benefits). The full four-channel attribution requires BEA NIPA + BLS CES + WID + WDI fetchers.",
        ],
    }, sort_keys=False))

    lines = [
        f"# Result card — {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "Pre-registered: 0.50 ≤ compositional_and_measurement_share ≤ 0.85 AND 0.15 ≤ top_strata_residual ≤ 0.50.",
        "",
        "## Cumulative US 1973→2000 (data: JST Macrohistory wage/cpi/rgdpmad/gdp)",
        "",
        "| Quantity | log change |",
        "|---|---:|",
        f"| Real wage (JST wage / JST cpi) | {log_wage_growth:+.3f} |",
        f"| Real GDP per capita (Maddison) | {log_gdp_pc_growth:+.3f} |",
        f"| **Raw wage-productivity gap** | **{raw_gap_log:+.3f}** |",
        "",
        "## Channel decomposition (illustrative, not all channels available)",
        "",
        "| Channel | Share of raw gap |",
        "|---|---:|",
        f"| (c) Feldstein CPI-vs-GDP-deflator measurement wedge | {measurement_share:+.0%} |",
        f"| (d) Top-strata residual (Gini-proxied) | {top_strata_share:+.0%} |",
        f"| (a)+(b) compositional + benefit-substitution residual | {compositional_residual:+.0%} |",
        f"| Compositional + measurement combined | {compositional_and_measurement_share:+.0%} |",
        "",
        f"Gini Δ 1973→2000: {gini_start:.1f} → {gini_end:.1f} ({gini_delta:+.1f} points). "
        f"Top-strata share derived via illustrative 0.015×Δgini/raw_gap mapping; "
        f"WID top-1% share would be the correct series.",
        "",
        f"Sample N: {len(df)} country-years (USA, {PERIOD[0]}-{PERIOD[1]}).",
        "",
        "## Deviations from pre-registration",
        "",
        "- BLS CES0500000008 (production-and-nonsupervisory wage) not in vintages; JST Macrohistory `wage` substituted.",
        "- BLS CES0500000002 (total compensation) not in vintages; benefit-substitution channel (a) skipped.",
        "- WDI SL.TLF.CACT.FE.ZS (female LFP) not in vintages; compositional channel (b) skipped.",
        "- OWID top-1-share-of-total-income not in vintages; OWID Gini substituted (coarser proxy).",
        "- GDP deflator proxied as JST nominal GDP / Maddison real GDP, not BEA NIPA.",
        "- The v1 result tests a weakened version of the spec: only the measurement wedge (c) is identified directly; (a), (b) are absorbed into the residual; (d) is illustrative via Gini.",
        "",
        "## Steelman live concerns",
        "",
        "See [hypotheses/steelman/us_median_wage_stagnation_1973_2000_decomposition.md]"
        "(../../../hypotheses/steelman/us_median_wage_stagnation_1973_2000_decomposition.md) "
        "for the Bivens-Mishel rent-extraction reading, the EPI compensation-vs-output measurement debate, "
        "and the Feldstein-Lebergott household-vs-establishment series critique.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  raw cumulative gap (log GDP pc - log real wage): {raw_gap_log:+.3f}")
    print(f"  Feldstein wedge share: {measurement_share:+.2f}")
    print(f"  Gini-proxied top-strata: {top_strata_share:+.2f}")
    print(f"  Residual (composition+benefits): {compositional_residual:+.2f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
