#!/usr/bin/env python3
"""Replication — Post-2008 OECD growth-emissions path vs IPCC 1.5C scenarios.

Spec: hypotheses/growth/post_2008_oecd_growth_emissions_path.yaml v1
Position-claim: degrowth #6 (school predicts: supported)

Tests two empirical regularities flagged by the degrowth school:
  PRIMARY 1: Mean OECD-country annual log-GDP growth 2009-2023 (excluding
             COVID 2020) is at most 2.0% — i.e. growth has slowed to
             the "1-2% trend" range in the claim.
  PRIMARY 2: 2023 per-capita CO2 emissions are above the 1.5C-consistent
             benchmark trajectory. Benchmark = linear path from 2008
             baseline reaching 50% of baseline by 2030 (a permissive
             reading of IPCC SSP1-1.9 fast-mitigation scenarios; the
             slow scenarios require steeper cuts so this is generous to
             the "growth is on track" alternative).

Hypothesis is SUPPORTED only if BOTH primaries hold (slow growth AND
above-1.5C emissions). REFUTED if growth is fast (>2.0%) AND emissions
are on/below benchmark. PARTIAL otherwise.

This is the canonical example replication script for batch-runnable
descriptive panel hypotheses. Other agents promoting stub hypotheses
to runnable should mirror its structure.
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
HID = "post_2008_oecd_growth_emissions_path"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from the spec (sample.countries)
COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "SWE",
    "NOR", "DNK", "FIN", "IRL", "JPN", "CAN", "AUS", "NZL", "KOR", "ISR",
    "CHE", "POL", "CZE", "HUN", "PRT", "GRC",
]
PERIOD = (2008, 2023)
EXCLUDE_YEARS = {2020}  # COVID — per sample.exclusion_rules

# Falsification thresholds (from spec.falsification.test, made dispositive)
GROWTH_THRESHOLD = 0.02  # 2.0% annual mean
EMISSIONS_TARGET_2030_FRACTION = 0.50  # 1.5C-consistent: -50% by 2030
EMISSIONS_BASELINE_YEAR = 2008
EMISSIONS_TARGET_YEAR = 2030


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


def load_long(path: Path) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value) rows. OWID uses
    the metric name as the value column instead of 'value'; treat the last
    non-meta column as the value field."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_path = latest("world_bank_wdi", "NY.GDP.MKTP.KD")
    co2pc_path = latest("owid", "co2-emissions-per-capita")

    manifest = {
        "real_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.MKTP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "co2_emissions_per_capita": {
            "publisher": "owid",
            "series": "co2-emissions-per-capita",
            "vintage_file": str(co2pc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(co2pc_path),
        },
    }

    gdp = load_long(gdp_path)
    co2 = load_long(co2pc_path)

    # ---------- PRIMARY 1: post-2008 growth ----------
    panel = gdp[
        (gdp["country_iso3"].isin(COUNTRIES))
        & (gdp["year"].between(PERIOD[0], PERIOD[1]))
    ].copy()
    panel["log_gdp"] = np.log(panel["value"])

    # Annual log-growth, excluding 2020-2021 (the year-on-year diffs that touch 2020)
    growth_rows = []
    for c in COUNTRIES:
        sub = panel[panel["country_iso3"] == c].set_index("year")["log_gdp"].sort_index()
        for y in range(PERIOD[0] + 1, PERIOD[1] + 1):
            if y - 1 in sub.index and y in sub.index and y not in EXCLUDE_YEARS and y - 1 not in EXCLUDE_YEARS:
                growth_rows.append({"country": c, "year": y, "log_growth": sub[y] - sub[y - 1]})
    growth_df = pd.DataFrame(growth_rows)
    mean_growth = float(growth_df["log_growth"].mean())
    median_growth = float(growth_df["log_growth"].median())

    primary1_growth_slowed = mean_growth <= GROWTH_THRESHOLD

    # ---------- PRIMARY 2: per-capita emissions vs 1.5C path ----------
    co2 = co2[
        (co2["country_iso3"].isin(COUNTRIES))
        & (co2["year"].between(PERIOD[0], PERIOD[1]))
    ].copy()
    co2["year"] = co2["year"].astype(int)

    co2_2008 = (
        co2[co2["year"] == 2008].groupby("country_iso3")["value"].mean()
    )
    co2_2023 = (
        co2[co2["year"] == 2023].groupby("country_iso3")["value"].mean()
    )

    # Linear 1.5C-consistent benchmark — fraction at 2023:
    # baseline at 2008 = 1.0, target at 2030 = 0.50 (50% cut by 2030).
    years_to_target = EMISSIONS_TARGET_YEAR - EMISSIONS_BASELINE_YEAR
    years_elapsed = 2023 - EMISSIONS_BASELINE_YEAR
    benchmark_fraction_2023 = 1.0 - (1.0 - EMISSIONS_TARGET_2030_FRACTION) * (
        years_elapsed / years_to_target
    )

    common = [c for c in COUNTRIES if c in co2_2008.index and c in co2_2023.index]
    actual_fractions = {c: float(co2_2023[c] / co2_2008[c]) for c in common}
    mean_actual_fraction = float(np.mean(list(actual_fractions.values())))
    n_above_benchmark = sum(1 for v in actual_fractions.values() if v > benchmark_fraction_2023)
    n_total = len(actual_fractions)

    # Country is "above 1.5C path" if its 2023/2008 ratio exceeds the benchmark
    primary2_emissions_above_path = (
        mean_actual_fraction > benchmark_fraction_2023
    )

    # ---------- Verdict ----------
    both = primary1_growth_slowed and primary2_emissions_above_path
    if both:
        verdict = (
            f"SUPPORTED — Mean OECD log-growth post-2008 (excl. 2020): "
            f"{mean_growth*100:+.2f}%/yr (≤ 2.0% threshold). "
            f"Mean per-capita emissions in 2023 are at "
            f"{mean_actual_fraction*100:.0f}% of 2008 baseline; the 1.5C-"
            f"consistent benchmark for 2023 is {benchmark_fraction_2023*100:.0f}% — "
            f"emissions are {(mean_actual_fraction - benchmark_fraction_2023)*100:+.0f}pp "
            f"above the path. {n_above_benchmark} of {n_total} OECD countries "
            f"are above their 1.5C share."
        )
    elif (not primary1_growth_slowed) and (not primary2_emissions_above_path):
        verdict = (
            f"refuted — Growth was {mean_growth*100:+.2f}%/yr (above 2.0% "
            f"threshold) AND emissions are at "
            f"{mean_actual_fraction*100:.0f}% of 2008 baseline (below the "
            f"{benchmark_fraction_2023*100:.0f}% benchmark). The "
            f"green-growth-on-track scenario fits."
        )
    else:
        which = (
            "growth held above 2%" if not primary1_growth_slowed
            else "emissions on/below 1.5C benchmark"
        )
        verdict = (
            f"partial — One primary held, the other did not "
            f"({which}). Mean growth {mean_growth*100:+.2f}%/yr; "
            f"emissions at {mean_actual_fraction*100:.0f}% of 2008 vs "
            f"{benchmark_fraction_2023*100:.0f}% benchmark."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": both,
        "primary1_growth_slowed": primary1_growth_slowed,
        "primary2_emissions_above_path": primary2_emissions_above_path,
        "mean_log_growth": mean_growth,
        "median_log_growth": median_growth,
        "growth_threshold": GROWTH_THRESHOLD,
        "n_country_year_growth_obs": int(len(growth_df)),
        "mean_emissions_fraction_2023_vs_2008": mean_actual_fraction,
        "benchmark_fraction_2023": benchmark_fraction_2023,
        "n_above_benchmark": n_above_benchmark,
        "n_with_data": n_total,
        "country_emissions_fractions": actual_fractions,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
    ]
    series = []
    for i, c in enumerate(COUNTRIES):
        sub = (
            co2[co2["country_iso3"] == c][["year", "value"]]
            .dropna()
            .sort_values("year")
        )
        if sub.empty or c not in co2_2008.index:
            continue
        baseline = co2_2008[c]
        if baseline <= 0:
            continue
        pts = [
            {"x": int(r.year), "y": float(r.value / baseline)}
            for r in sub.itertuples()
        ]
        series.append(
            {
                "id": c,
                "label": c,
                "color": palette[i % len(palette)],
                "treated": False,
                "points": pts,
            }
        )

    # Add the 1.5C benchmark trajectory
    benchmark_pts = []
    for y in range(PERIOD[0], PERIOD[1] + 1):
        elapsed = y - EMISSIONS_BASELINE_YEAR
        frac = 1.0 - (1.0 - EMISSIONS_TARGET_2030_FRACTION) * (elapsed / years_to_target)
        benchmark_pts.append({"x": y, "y": frac})
    series.insert(
        0,
        {
            "id": "BENCHMARK",
            "label": "1.5C-consistent (linear to -50% by 2030)",
            "color": "#1f1f1f",
            "treated": True,
            "points": benchmark_pts,
        },
    )

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "OECD per-capita CO2 emissions, indexed to 2008 baseline",
        "subtitle": (
            f"Mean OECD growth 2009-2023 (ex 2020): {mean_growth*100:+.2f}%/yr · "
            f"Mean 2023 emissions at {mean_actual_fraction*100:.0f}% of 2008 vs "
            f"{benchmark_fraction_2023*100:.0f}% on the 1.5C-consistent path."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "per-capita CO2 (2008 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Benchmark = linear path 1.0 (2008) → 0.50 (2030). "
                    f"At 2023 the benchmark is {benchmark_fraction_2023:.2f}; "
                    f"actual OECD mean is {mean_actual_fraction:.2f}."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [
            {"spec": "primary1", "term": "mean_log_growth", "estimate": mean_growth},
            {"spec": "primary1", "term": "median_log_growth", "estimate": median_growth},
            {"spec": "primary2", "term": "mean_emissions_fraction_2023", "estimate": mean_actual_fraction},
            {"spec": "primary2", "term": "benchmark_fraction_2023", "estimate": benchmark_fraction_2023},
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
        f"# Post-2008 OECD growth-emissions path",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Mean OECD annual log-growth 2009-2023 (excluding COVID 2020): "
        f"**{mean_growth*100:+.2f}%/yr** (median: {median_growth*100:+.2f}%/yr).",
        f"- Threshold for the degrowth claim's 'slowed-growth' premise: ≤ 2.0%/yr. "
        f"Premise {'holds' if primary1_growth_slowed else 'does NOT hold'}.",
        f"- Mean OECD 2023 per-capita CO2 emissions: "
        f"**{mean_actual_fraction*100:.0f}% of 2008 baseline**.",
        f"- 1.5C-consistent benchmark fraction at 2023: "
        f"**{benchmark_fraction_2023*100:.0f}%** (linear path 1.0 → 0.50 by 2030).",
        f"- {n_above_benchmark} of {n_total} OECD countries with data are "
        f"above their 1.5C share.",
        "",
        "## Method",
        "",
        "Two simple primary tests against the spec's stated falsification rule:",
        "",
        "1. Mean log-difference of NY.GDP.MKTP.KD across the 26 OECD-country "
        "panel, year-on-year 2009-2023, dropping any pair touching 2020.",
        "2. 2023 ÷ 2008 ratio of per-capita CO2 emissions, country-mean.",
        "",
        "The 1.5C-consistent benchmark used here (linear path to -50% by "
        "2030) is a permissive reading of fast-mitigation IPCC SSP1-1.9 "
        "scenarios — slower-mitigation scenarios require steeper cuts and "
        "would push the benchmark fraction lower, making the hypothesis "
        "harder to refute. Robustness to alternative benchmarks is left "
        "as a v2 question.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.MKTP.KD",
        f"- owid:co2-emissions-per-capita",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
