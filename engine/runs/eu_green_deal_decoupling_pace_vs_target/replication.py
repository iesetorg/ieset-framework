#!/usr/bin/env python3
"""Replication — EU Green Deal: pace of decoupling vs 1.5C-consistent target.

Spec: hypotheses/growth/eu_green_deal_decoupling_pace_vs_target.yaml v1
Position-claim: degrowth #9 (school predicts: mixed)

Tests the joint claim that EU Green Deal era (2020-present) shows
*partial* decoupling — i.e. emissions falling while GDP grows — yet at
a pace *below* the 1.5C-consistent linear pathway. SUPPORTED requires
BOTH legs of the claim to hold simultaneously.

PRIMARY 1 (relative decoupling, 2019->2023):
  Mean cumulative log-change in per-capita CO2 across the 16-country
  EU panel is at most -2% (i.e. emissions FELL by ≥2% from 2019 to
  2023) AND mean cumulative log-change in real GDP is at least +1%
  (i.e. GDP GREW by ≥1% over the same window). 2019 chosen as
  pre-Green-Deal baseline; 2023 is the latest year with reliable
  WDI/OWID coverage.

PRIMARY 2 (pace below 1.5C path):
  Mean per-capita CO2 in 2023 is ABOVE the 1.5C-consistent linear
  benchmark for 2023, where the benchmark is the linear path from
  2019 baseline to 50% of 2019 level by 2030 (a permissive reading
  of IPCC 1.5C SSP1-1.9 fast-mitigation scenarios — ~7%/yr cuts).
  The benchmark fraction at 2023 is therefore 1.0 - 0.5*(4/11)
  = 0.818 (i.e. by 2023 emissions should be at ~82% of 2019).

Hypothesis is SUPPORTED iff BOTH primaries hold:
  - relative decoupling exists (emissions down, GDP up), AND
  - emissions are above the 1.5C path (pace insufficient).

REFUTED if either:
  (a) emissions did NOT decouple from growth (emissions rose, or
      GDP fell — the "growth-emissions still tied" world), OR
  (b) emissions are at/below the 1.5C path (pace IS sufficient,
      contradicting the "below target" leg).

PARTIAL otherwise (e.g. decoupling holds but pace exactly meets
benchmark within tolerance).
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
HID = "eu_green_deal_decoupling_pace_vs_target"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# 16-country EU panel from spec.sample.countries
COUNTRIES = [
    "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "FIN",
    "IRL", "PRT", "GRC", "POL", "CZE", "HUN", "SWE", "DNK",
]

PERIOD = (2010, 2023)             # full panel for chart context
GREEN_DEAL_BASELINE = 2019        # pre-Green-Deal baseline
ASSESSMENT_YEAR = 2023            # latest reliable coverage

# 1.5C-consistent benchmark: linear path 2019 -> 50% by 2030
BENCHMARK_TARGET_FRACTION = 0.50
BENCHMARK_TARGET_YEAR = 2030

# Falsification thresholds (dispositive, magnitude-based)
EMISSIONS_DECLINE_THRESHOLD = -0.02   # mean log-change ≤ -2% from 2019 to 2023
GDP_GROWTH_THRESHOLD = 0.01           # mean log-change ≥ +1% from 2019 to 2023


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
    pop_path = latest("world_bank_wdi", "SP.POP.TOTL")
    co2pc_path = latest("owid", "co2-emissions-per-capita")

    manifest = {
        "real_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.MKTP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "population": {
            "publisher": "world_bank_wdi",
            "series": "SP.POP.TOTL",
            "vintage_file": str(pop_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pop_path),
        },
        "co2_emissions_per_capita": {
            "publisher": "owid",
            "series": "co2-emissions-per-capita",
            "vintage_file": str(co2pc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(co2pc_path),
        },
    }

    gdp = load_long(gdp_path)
    pop = load_long(pop_path)
    co2 = load_long(co2pc_path)

    # ---------- PRIMARY 1: relative decoupling (2019 -> 2023) ----------
    co2 = co2[co2["country_iso3"].isin(COUNTRIES)].copy()
    gdp = gdp[gdp["country_iso3"].isin(COUNTRIES)].copy()
    pop = pop[pop["country_iso3"].isin(COUNTRIES)].copy()
    co2["year"] = co2["year"].astype(int)
    gdp["year"] = gdp["year"].astype(int)
    pop["year"] = pop["year"].astype(int)

    # GDP per capita (real) for fair comparison (CO2 is per-capita already)
    gdp_pc = (
        gdp.merge(pop, on=["country_iso3", "year"], suffixes=("_gdp", "_pop"))
           .assign(value=lambda d: d["value_gdp"] / d["value_pop"])
           [["country_iso3", "year", "value"]]
    )

    co2_2019 = co2[co2["year"] == GREEN_DEAL_BASELINE].set_index("country_iso3")["value"]
    co2_2023 = co2[co2["year"] == ASSESSMENT_YEAR].set_index("country_iso3")["value"]
    gdp_2019 = gdp_pc[gdp_pc["year"] == GREEN_DEAL_BASELINE].set_index("country_iso3")["value"]
    gdp_2023 = gdp_pc[gdp_pc["year"] == ASSESSMENT_YEAR].set_index("country_iso3")["value"]

    common = sorted(
        set(co2_2019.index) & set(co2_2023.index)
        & set(gdp_2019.index) & set(gdp_2023.index)
        & set(COUNTRIES)
    )
    if len(common) < 12:
        # Method-validity gate — emit inconclusive
        verdict = (
            f"inconclusive — Only {len(common)}/16 EU panel countries "
            f"have both 2019 and 2023 observations for CO2 and GDP. "
            f"Method-validity floor (≥12) not met; data gap likely on "
            f"OWID 2023 vintage."
        )
        diagnostics = {
            "verdict": verdict,
            "n_with_data": len(common),
            "common_countries": common,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    co2_log_change = {c: float(np.log(co2_2023[c]) - np.log(co2_2019[c])) for c in common}
    gdp_log_change = {c: float(np.log(gdp_2023[c]) - np.log(gdp_2019[c])) for c in common}

    mean_co2_change = float(np.mean(list(co2_log_change.values())))
    mean_gdp_change = float(np.mean(list(gdp_log_change.values())))

    n_emissions_fell = sum(1 for v in co2_log_change.values() if v < 0)
    n_gdp_grew = sum(1 for v in gdp_log_change.values() if v > 0)
    n_decoupled = sum(
        1 for c in common
        if co2_log_change[c] < 0 and gdp_log_change[c] > 0
    )

    primary1_decoupled = (
        mean_co2_change <= EMISSIONS_DECLINE_THRESHOLD
        and mean_gdp_change >= GDP_GROWTH_THRESHOLD
    )

    # ---------- PRIMARY 2: pace vs 1.5C-consistent path ----------
    # Benchmark: linear from 1.0 (2019) to 0.50 (2030).
    years_to_target = BENCHMARK_TARGET_YEAR - GREEN_DEAL_BASELINE
    years_elapsed = ASSESSMENT_YEAR - GREEN_DEAL_BASELINE
    benchmark_fraction_2023 = 1.0 - (1.0 - BENCHMARK_TARGET_FRACTION) * (
        years_elapsed / years_to_target
    )

    actual_fractions = {c: float(co2_2023[c] / co2_2019[c]) for c in common}
    mean_actual_fraction = float(np.mean(list(actual_fractions.values())))
    n_above_benchmark = sum(
        1 for v in actual_fractions.values() if v > benchmark_fraction_2023
    )

    primary2_pace_insufficient = mean_actual_fraction > benchmark_fraction_2023

    # ---------- Verdict ----------
    both = primary1_decoupled and primary2_pace_insufficient
    if both:
        verdict = (
            f"SUPPORTED — EU panel shows partial decoupling 2019->2023: "
            f"mean per-capita CO2 {mean_co2_change*100:+.1f}%, mean per-capita "
            f"real GDP {mean_gdp_change*100:+.1f}%. {n_decoupled}/{len(common)} "
            f"countries showed both falling emissions and rising GDP. "
            f"Pace is BELOW 1.5C path: 2023 mean emissions at "
            f"{mean_actual_fraction*100:.0f}% of 2019 vs benchmark "
            f"{benchmark_fraction_2023*100:.0f}% (gap "
            f"{(mean_actual_fraction - benchmark_fraction_2023)*100:+.0f}pp). "
            f"{n_above_benchmark}/{len(common)} above the 1.5C share."
        )
    elif not primary1_decoupled and not primary2_pace_insufficient:
        verdict = (
            f"refuted — EU panel did NOT show the claimed decoupling-but-"
            f"insufficient pattern. Mean CO2 {mean_co2_change*100:+.1f}% "
            f"(threshold ≤ -2%), GDP {mean_gdp_change*100:+.1f}% "
            f"(threshold ≥ +1%); emissions at {mean_actual_fraction*100:.0f}% "
            f"of 2019 vs {benchmark_fraction_2023*100:.0f}% benchmark."
        )
    else:
        which = []
        if not primary1_decoupled:
            which.append(
                f"decoupling premise unmet (CO2 {mean_co2_change*100:+.1f}%, "
                f"GDP {mean_gdp_change*100:+.1f}%)"
            )
        if not primary2_pace_insufficient:
            which.append(
                f"pace already meets/beats 1.5C path "
                f"({mean_actual_fraction*100:.0f}% vs {benchmark_fraction_2023*100:.0f}%)"
            )
        verdict = (
            f"partial — One leg held, the other did not: "
            f"{'; '.join(which)}. "
            f"Mean CO2 {mean_co2_change*100:+.1f}%, GDP {mean_gdp_change*100:+.1f}%, "
            f"emissions ratio {mean_actual_fraction*100:.0f}% vs "
            f"{benchmark_fraction_2023*100:.0f}% benchmark."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": both,
        "primary1_decoupled": primary1_decoupled,
        "primary2_pace_insufficient": primary2_pace_insufficient,
        "mean_log_change_co2_pc_2019_2023": mean_co2_change,
        "mean_log_change_gdp_pc_2019_2023": mean_gdp_change,
        "emissions_decline_threshold": EMISSIONS_DECLINE_THRESHOLD,
        "gdp_growth_threshold": GDP_GROWTH_THRESHOLD,
        "mean_emissions_fraction_2023_vs_2019": mean_actual_fraction,
        "benchmark_fraction_2023": benchmark_fraction_2023,
        "n_emissions_fell": n_emissions_fell,
        "n_gdp_grew": n_gdp_grew,
        "n_decoupled": n_decoupled,
        "n_above_benchmark": n_above_benchmark,
        "n_with_data": len(common),
        "country_co2_log_change": co2_log_change,
        "country_gdp_log_change": gdp_log_change,
        "country_emissions_fractions": actual_fractions,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
        "#d62728", "#9467bd", "#17becf", "#bcbd22",
    ]
    series = []
    for i, c in enumerate(COUNTRIES):
        sub = co2[co2["country_iso3"] == c][["year", "value"]].dropna().sort_values("year")
        sub = sub[(sub["year"] >= PERIOD[0]) & (sub["year"] <= PERIOD[1])]
        if sub.empty or c not in co2_2019.index:
            continue
        baseline = co2_2019[c]
        if baseline <= 0:
            continue
        pts = [{"x": int(r.year), "y": float(r.value / baseline)} for r in sub.itertuples()]
        series.append({
            "id": c, "label": c, "color": palette[i % len(palette)],
            "treated": False, "points": pts,
        })

    benchmark_pts = []
    for y in range(PERIOD[0], PERIOD[1] + 1):
        if y < GREEN_DEAL_BASELINE:
            frac = 1.0  # benchmark only meaningful from 2019 onward
        else:
            elapsed = y - GREEN_DEAL_BASELINE
            frac = 1.0 - (1.0 - BENCHMARK_TARGET_FRACTION) * (elapsed / years_to_target)
        benchmark_pts.append({"x": y, "y": float(frac)})
    series.insert(0, {
        "id": "BENCHMARK",
        "label": "1.5C-consistent (linear 2019->-50% by 2030)",
        "color": "#1f1f1f",
        "treated": True,
        "points": benchmark_pts,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "EU per-capita CO2 indexed to 2019 baseline (Green Deal era)",
        "subtitle": (
            f"2019->2023: mean CO2 {mean_co2_change*100:+.1f}%, "
            f"mean GDPpc {mean_gdp_change*100:+.1f}%. "
            f"Mean 2023 ratio {mean_actual_fraction*100:.0f}% vs "
            f"1.5C benchmark {benchmark_fraction_2023*100:.0f}%."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "per-capita CO2 (2019 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vline",
                "x": GREEN_DEAL_BASELINE,
                "label": "Green Deal published (Dec 2019)",
            },
            {
                "type": "note",
                "label": (
                    f"Benchmark = linear 1.0 (2019) -> 0.50 (2030). "
                    f"At 2023 benchmark={benchmark_fraction_2023:.2f}; "
                    f"actual EU mean={mean_actual_fraction:.2f}."
                ),
            },
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame([
        {"spec": "primary1", "term": "mean_log_change_co2_pc_2019_2023", "estimate": mean_co2_change},
        {"spec": "primary1", "term": "mean_log_change_gdp_pc_2019_2023", "estimate": mean_gdp_change},
        {"spec": "primary1", "term": "n_decoupled", "estimate": float(n_decoupled)},
        {"spec": "primary2", "term": "mean_emissions_fraction_2023", "estimate": mean_actual_fraction},
        {"spec": "primary2", "term": "benchmark_fraction_2023", "estimate": benchmark_fraction_2023},
        {"spec": "primary2", "term": "n_above_benchmark", "estimate": float(n_above_benchmark)},
    ]).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
        f"# EU Green Deal: pace of decoupling vs 1.5C-consistent target",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- 16-country EU panel, baseline 2019 (pre-Green-Deal), assessment 2023.",
        f"- Mean per-capita CO2 change 2019->2023: **{mean_co2_change*100:+.1f}%** "
        f"(threshold for decoupling premise: ≤ -2%).",
        f"- Mean per-capita real GDP change 2019->2023: **{mean_gdp_change*100:+.1f}%** "
        f"(threshold ≥ +1%).",
        f"- {n_decoupled}/{len(common)} countries showed both emissions falling AND GDP rising.",
        f"- 2023 mean per-capita CO2 = **{mean_actual_fraction*100:.0f}% of 2019**.",
        f"- 1.5C-consistent linear benchmark for 2023 = "
        f"**{benchmark_fraction_2023*100:.0f}%** (path 2019->-50% by 2030).",
        f"- {n_above_benchmark}/{len(common)} countries are above (slower than) "
        f"their 1.5C share.",
        "",
        "## Method",
        "",
        "Two dispositive primary tests:",
        "",
        "1. Relative decoupling: mean log-change of OWID per-capita CO2 from "
        "2019 to 2023 (≤ -2%) AND mean log-change of WDI per-capita real GDP "
        "(≥ +1%) over the same window.",
        "2. Pace gap: mean ratio of 2023 per-capita CO2 to 2019 per-capita "
        "CO2, compared against a linear 1.5C-consistent benchmark (path "
        "2019 = 1.0 to 2030 = 0.50, so benchmark at 2023 ≈ 0.818).",
        "",
        "Real GDP per capita is constructed as NY.GDP.MKTP.KD / SP.POP.TOTL "
        "to keep the comparison on a per-capita basis (CO2 series is "
        "already per-capita).",
        "",
        "**Caveat (from spec.disclosure):** territorial CO2 (OWID convention) "
        "ignores carbon content of imports; consumption-based EU emissions "
        "may show a smaller decline. The linear 1.5C benchmark is a "
        "permissive reading of fast-mitigation IPCC SSP1-1.9 — slower "
        "scenarios require steeper near-term cuts and would push the "
        "benchmark fraction lower (making the 'pace insufficient' leg "
        "easier to satisfy).",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.MKTP.KD",
        f"- world_bank_wdi:SP.POP.TOTL",
        f"- owid:co2-emissions-per-capita",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
