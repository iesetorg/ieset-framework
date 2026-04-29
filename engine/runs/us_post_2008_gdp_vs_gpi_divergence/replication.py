#!/usr/bin/env python3
"""Replication — US post-2008 GDP vs median-household-income divergence.

Spec: hypotheses/growth/us_post_2008_gdp_vs_gpi_divergence.yaml v1
Position-claim: degrowth #11 (school predicts: supported)

Tests the degrowth-school claim that US post-2008 recovery shows rising real
GDP per capita alongside stagnant or declining median-household welfare. The
spec's first-best variable would be ISEW/GPI (Talberth/Kubiszewski), which is
not on disk in any publisher vintage. We substitute FRED's MEHOINUSA672N
(real median household income, annual). This is a WEAKER test than a true
GPI comparison because median income excludes leisure, ecological costs,
household labour, and inequality adjustments that GPI captures.

PRIMARY (dispositive) — both must hold for SUPPORTED:
  1. log(GDP_pc_2023 / GDP_pc_2008)
     - log(MEHOIN_2023 / MEHOIN_2008)
     >= 0.15  (GDP/cap pulls ahead by at least ~16pp cumulatively).
  2. log(MEHOIN_2023 / MEHOIN_2008) <= 0  (median income flat-or-declining).

REFUTED if median income grows at the same rate as or faster than GDP/cap
(gap <= 0). PARTIAL if direction is right (gap > 0) but a threshold misses.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "us_post_2008_gdp_vs_gpi_divergence"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRY = "USA"
YEAR_BASE = 2008
YEAR_END = 2023

# Falsification thresholds (from spec.falsification.threshold)
GAP_THRESHOLD = 0.15            # PRIMARY 1: log-points
INCOME_FLAT_THRESHOLD = 0.0     # PRIMARY 2: cumulative log change <= 0


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


def load_wdi_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def load_fred_annual(path: Path) -> pd.DataFrame:
    """FRED schema: (date, value, realtime_start, realtime_end). MEHOINUSA672N
    is annual with date stamped at YYYY-01-01. We project to year-of-date and
    take the latest realtime observation per year."""
    t = pq.read_table(path).to_pandas()
    t["year"] = pd.to_datetime(t["date"]).dt.year
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    # Pick the latest realtime_end per year (most-recent vintage of the obs)
    t = t.sort_values(["year", "realtime_end"])
    t = t.dropna(subset=["year", "value"]).drop_duplicates("year", keep="last")
    return t[["year", "value"]].reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    inc_path = latest("fred", "MEHOINUSA672N")

    manifest = {
        "real_gdp_per_capita": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "real_median_household_income": {
            "publisher": "fred",
            "series": "MEHOINUSA672N",
            "vintage_file": str(inc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(inc_path),
        },
    }

    gdp = load_wdi_long(gdp_path)
    inc = load_fred_annual(inc_path)

    us_gdp = (
        gdp[(gdp["country_iso3"] == COUNTRY)][["year", "value"]]
        .drop_duplicates("year")
        .set_index("year")["value"]
        .sort_index()
    )
    us_inc = inc.set_index("year")["value"].sort_index()

    # ---------- Method-validity check ----------
    needed_years = {YEAR_BASE, YEAR_END}
    missing_gdp = needed_years - set(us_gdp.index)
    missing_inc = needed_years - set(us_inc.index)
    if missing_gdp or missing_inc:
        verdict = (
            f"inconclusive — data gap. Missing GDP/cap years: {sorted(missing_gdp)}; "
            f"missing median-income years: {sorted(missing_inc)}."
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "missing_gdp_years": sorted(missing_gdp),
            "missing_income_years": sorted(missing_inc),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    gdp_base = float(us_gdp.loc[YEAR_BASE])
    gdp_end = float(us_gdp.loc[YEAR_END])
    inc_base = float(us_inc.loc[YEAR_BASE])
    inc_end = float(us_inc.loc[YEAR_END])

    log_gdp_growth = float(np.log(gdp_end / gdp_base))
    log_inc_growth = float(np.log(inc_end / inc_base))
    log_gap = log_gdp_growth - log_inc_growth

    primary1_gap_meets = log_gap >= GAP_THRESHOLD
    primary2_income_flat = log_inc_growth <= INCOME_FLAT_THRESHOLD

    # ---------- Verdict ----------
    if primary1_gap_meets and primary2_income_flat:
        verdict = (
            f"SUPPORTED — US 2008-2023 cumulative log gap "
            f"GDP/cap minus real median household income = "
            f"{log_gap:+.3f} (>= 0.15 threshold) AND median income "
            f"cumulative log change = {log_inc_growth:+.3f} "
            f"(flat-or-declining). GDP/cap +{log_gdp_growth*100:.1f} log-pp; "
            f"median income +{log_inc_growth*100:.1f} log-pp."
        )
    elif log_gap <= 0:
        verdict = (
            f"refuted — US real median household income grew at least as "
            f"fast as real GDP per capita 2008-2023. Cumulative log GDP/cap = "
            f"{log_gdp_growth:+.3f} ({log_gdp_growth*100:+.1f} log-pp); "
            f"cumulative log median income = {log_inc_growth:+.3f} "
            f"({log_inc_growth*100:+.1f} log-pp); gap = {log_gap:+.3f}. "
            f"The GDP-vs-median-income divergence framing of the claim does "
            f"not hold in the 2008-2023 window."
        )
    elif not primary1_gap_meets and not primary2_income_flat:
        verdict = (
            f"refuted — Both primary tests failed. Cumulative log gap = "
            f"{log_gap:+.3f} (below 0.15 threshold) AND median income grew "
            f"{log_inc_growth*100:+.1f} log-pp (not flat-or-declining). "
            f"GDP/cap +{log_gdp_growth*100:.1f} log-pp; the divergence and "
            f"stagnation premises both miss."
        )
    else:
        which = (
            "gap below 0.15 threshold" if not primary1_gap_meets
            else "median income grew (not flat-or-declining)"
        )
        verdict = (
            f"partial — Direction is consistent with the claim "
            f"(GDP/cap outgrew median income by {log_gap:+.3f} log-points), "
            f"but {which}. GDP/cap +{log_gdp_growth*100:.1f} log-pp; "
            f"median income +{log_inc_growth*100:.1f} log-pp."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "all_pass": bool(primary1_gap_meets and primary2_income_flat),
        "primary1_gap_meets_threshold": bool(primary1_gap_meets),
        "primary2_income_flat_or_declining": bool(primary2_income_flat),
        "log_gdp_pc_growth_2008_2023": log_gdp_growth,
        "log_real_median_income_growth_2008_2023": log_inc_growth,
        "log_gap_gdp_minus_income": log_gap,
        "gap_threshold": GAP_THRESHOLD,
        "income_flat_threshold": INCOME_FLAT_THRESHOLD,
        "gdp_pc_2008": gdp_base,
        "gdp_pc_2023": gdp_end,
        "real_median_income_2008": inc_base,
        "real_median_income_2023": inc_end,
        "country": COUNTRY,
        "period": [YEAR_BASE, YEAR_END],
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: indexed series 2008 = 100 ----------
    years = sorted(set(us_gdp.index) & set(us_inc.index))
    years = [int(y) for y in years if YEAR_BASE <= y <= YEAR_END]
    gdp_pts = [
        {"x": int(y), "y": float(us_gdp.loc[y] / gdp_base * 100.0)} for y in years
    ]
    inc_pts = [
        {"x": int(y), "y": float(us_inc.loc[y] / inc_base * 100.0)} for y in years
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US real GDP per capita vs real median household income, 2008 = 100",
        "subtitle": (
            f"2008-2023 cumulative log change: GDP/cap "
            f"{log_gdp_growth*100:+.1f} log-pp; median income "
            f"{log_inc_growth*100:+.1f} log-pp; gap {log_gap*100:+.1f} log-pp "
            f"(threshold: gap >= 15 log-pp AND income <= 0)."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Index (2008 = 100)", "type": "linear"},
        "series": [
            {
                "id": "GDP_PC",
                "label": "Real GDP per capita (WDI NY.GDP.PCAP.KD)",
                "color": "#4E79A7",
                "treated": False,
                "points": gdp_pts,
            },
            {
                "id": "MEDIAN_INCOME",
                "label": "Real median household income (FRED MEHOINUSA672N)",
                "color": "#E15759",
                "treated": True,
                "points": inc_pts,
            },
        ],
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Median household income is a WEAKER proxy than ISEW/GPI; "
                    f"GPI would deduct ecological costs and inequality, which "
                    f"would generally widen the divergence on the degrowth "
                    f"reading. See methodology_note in the spec."
                ),
            }
        ],
        "sources": [
            {
                "publisher_id": v["publisher"],
                "series_id": v["series"],
                "vintage_file": v["vintage_file"],
            }
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [
            {"spec": "primary1", "term": "log_gdp_pc_growth_2008_2023", "estimate": log_gdp_growth},
            {"spec": "primary1", "term": "log_real_median_income_growth_2008_2023", "estimate": log_inc_growth},
            {"spec": "primary1", "term": "log_gap_gdp_minus_income", "estimate": log_gap},
            {"spec": "primary1", "term": "gap_threshold", "estimate": GAP_THRESHOLD},
            {"spec": "primary2", "term": "income_flat_threshold", "estimate": INCOME_FLAT_THRESHOLD},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + "".join(
            f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
            f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
            for k, v in manifest.items()
        )
    )

    card = [
        f"# US post-2008 GDP-per-capita vs real-median-income divergence",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- US real GDP per capita 2008 = ${gdp_base:,.0f} → 2023 = ${gdp_end:,.0f} "
        f"(cumulative log change **{log_gdp_growth*100:+.1f} log-pp**).",
        f"- US real median household income 2008 = ${inc_base:,.0f} → 2023 = "
        f"${inc_end:,.0f} (cumulative log change **{log_inc_growth*100:+.1f} log-pp**).",
        f"- Cumulative log gap (GDP/cap minus median income) = "
        f"**{log_gap*100:+.1f} log-pp**. Threshold for SUPPORTED: gap >= 15 "
        f"log-pp AND median income <= 0.",
        f"- PRIMARY 1 (gap >= 0.15): "
        f"{'PASS' if primary1_gap_meets else 'FAIL'}.",
        f"- PRIMARY 2 (median income flat-or-declining): "
        f"{'PASS' if primary2_income_flat else 'FAIL'}.",
        "",
        "## Method",
        "",
        "Endpoint comparison of two indexed series for the United States, "
        "2008 → 2023:",
        "",
        "1. **Real GDP per capita** — World Bank WDI `NY.GDP.PCAP.KD` "
        "(constant-USD GDP per capita).",
        "2. **Real median household income** — FRED `MEHOINUSA672N` "
        "(annual real median household income in 2023 CPI-U-RS dollars).",
        "",
        "Cumulative log change is `ln(value_2023 / value_2008)` for each "
        "series. The PRIMARY statistic is the difference of the two log "
        "changes (the divergence gap). The hypothesis is SUPPORTED only "
        "if BOTH the gap is >= 0.15 log-points (~+16pp) AND median income "
        "is flat-or-declining (cumulative log change <= 0).",
        "",
        "## Steelman if the verdict is missing",
        "",
        "Median household income is a **weaker** proxy than the ISEW/GPI "
        "the original claim references. A true GPI run would deduct "
        "ecological costs (depletion, climate damage), defensive "
        "expenditures, and an inequality adjustment that median income "
        "ignores; on the degrowth school's reading those deductions widen "
        "the divergence. The cleanest steelman: even if median income "
        "rose, the GPI version of welfare may still have stagnated. ISEW/"
        "GPI series are not on disk in any publisher vintage, so this "
        "hypothesis cannot dispositively REFUTE the broader GPI framing — "
        "only the GDP-vs-median-income framing. A v2 promotion that wires "
        "in a Kubiszewski/Talberth GPI vintage would tighten the test.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.PCAP.KD",
        f"- fred:MEHOINUSA672N",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
