#!/usr/bin/env python3
"""Replication — Absolute decoupling of GDP growth from material throughput,
global, 1990-2020.

Spec: hypotheses/growth/absolute_decoupling_global_material_throughput.yaml v1
Position-claim: degrowth #1 (school predicts: supported)

The claim: absolute decoupling of GDP growth from material throughput has
NOT been sustained at global scale 1970-2020; reported decoupling in
advanced economies reflects offshored manufacturing and is reversed under
consumption-based accounting.

DATA-GAP NOTE: The spec's preferred series — UNEP/IRP Domestic Material
Consumption (DMC) and Material Footprint (MF) — are NOT available in
data/vintages/. Neither is consumption-based CO2 (Global Carbon Project /
Eora MRIO). The TODO in the spec explicitly authorises CO2 emissions per
capita as an energy-throughput proxy. We therefore test the production-
based half of the claim using:

  - GDP per capita (constant USD, WDI NY.GDP.PCAP.KD)
  - CO2 emissions per capita (OWID co2-emissions-per-capita,
    production-based)

PRIMARY (dispositive): the hypothesis is SUPPORTED at the global level if,
across the 26-country panel, the population-weighted MEAN of (CO2 per
capita 2020 / CO2 per capita 1990) is at least 0.95 — i.e. less than a 5%
absolute fall in throughput over 30 years of GDP growth that more than
doubled real per-capita output. REFUTED if the ratio is at most 0.80
(>=20% absolute fall in per-capita CO2 — clearly sustained absolute
decoupling). PARTIAL otherwise.

SECONDARY (informative, not gating): per-country count of how many in the
26-country panel achieved sustained absolute decoupling, defined as 2020
per-capita CO2 below 1990 by at least 10%, alongside cumulative GDP
growth of at least 30%.

METHOD-VALID: at least 22 of 26 countries in the panel have both 1990
and 2020 observations on both series, otherwise the run emits an
'inconclusive (data gap)' verdict and stops.

Key honest caveat: this run cannot adjudicate the consumption-based
critique (offshoring) because Material Footprint / consumption-based CO2
is unavailable on disk. The verdict therefore speaks to the WEAKER
production-based version of the claim — refuting the production-based
version is sufficient to refute the global claim, but supporting it is
not sufficient to support the global claim (offshoring caveat survives).
This asymmetry is encoded in the verdict logic and the result_card.
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
HID = "absolute_decoupling_global_material_throughput"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample (sample.countries from spec)
COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "SWE",
    "NOR", "DNK", "FIN", "IRL", "JPN", "CAN", "AUS", "CHN", "IND", "BRA",
    "MEX", "IDN", "ZAF", "RUS", "TUR", "KOR",
]
PERIOD = (1990, 2020)  # post-1990 window per exclusion_rules; 2020 is end

# Falsification thresholds (sharpened from spec.falsification stub)
SUPPORTED_RATIO_FLOOR = 0.95   # mean (2020/1990) >= 0.95 -> SUPPORTED
REFUTED_RATIO_CEILING = 0.80   # mean (2020/1990) <= 0.80 -> REFUTED
COUNTRY_DECOUPLE_GDP_GROWTH_MIN = 0.30   # >=30% cumulative real per-cap GDP growth
COUNTRY_DECOUPLE_CO2_DROP_MIN = 0.10     # >=10% absolute drop in per-capita CO2
METHOD_VALID_MIN_COUNTRIES = 22  # of 26


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    """Search worktree first, fall back to parent repo (worktree vintages
    may be empty / .gitkeep only — data is gitignored)."""
    candidates = [
        REPO_ROOT / "data" / "vintages" / pub,
        Path("data/vintages") / pub,
    ]
    for d in candidates:
        if not d.exists():
            continue
        files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
        if files:
            return files[-1]
    raise FileNotFoundError(f"{pub}:{series}")


def load_long(path: Path) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value)."""
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

    gdp_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    co2pc_path = latest("owid", "co2-emissions-per-capita")
    pop_path = latest("world_bank_wdi", "SP.POP.TOTL")

    manifest = {
        "real_gdp_per_capita": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_path),
            "sha256": sha256(gdp_path),
        },
        "co2_emissions_per_capita": {
            "publisher": "owid",
            "series": "co2-emissions-per-capita",
            "vintage_file": str(co2pc_path),
            "sha256": sha256(co2pc_path),
        },
        "population": {
            "publisher": "world_bank_wdi",
            "series": "SP.POP.TOTL",
            "vintage_file": str(pop_path),
            "sha256": sha256(pop_path),
        },
    }

    gdp = load_long(gdp_path)
    co2 = load_long(co2pc_path)
    pop = load_long(pop_path)

    def at_year(df: pd.DataFrame, y: int) -> pd.Series:
        return (
            df[(df["country_iso3"].isin(COUNTRIES)) & (df["year"] == y)]
            .groupby("country_iso3")["value"]
            .mean()
        )

    gdp_1990 = at_year(gdp, 1990)
    gdp_2020 = at_year(gdp, 2020)
    co2_1990 = at_year(co2, 1990)
    co2_2020 = at_year(co2, 2020)
    pop_2020 = at_year(pop, 2020)

    common = sorted(
        set(gdp_1990.index)
        & set(gdp_2020.index)
        & set(co2_1990.index)
        & set(co2_2020.index)
        & set(pop_2020.index)
    )

    # ---------- METHOD-VALID gate ----------
    if len(common) < METHOD_VALID_MIN_COUNTRIES:
        verdict = (
            f"inconclusive (data gap) — only {len(common)} of 26 sample countries "
            f"have both 1990 and 2020 observations on per-capita GDP and per-capita "
            f"CO2. Threshold {METHOD_VALID_MIN_COUNTRIES} not met."
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "n_with_data": len(common),
            "method_valid_min": METHOD_VALID_MIN_COUNTRIES,
            "data_gap_note": (
                "Material Footprint / DMC unavailable in data/vintages/; CO2 used "
                "as proxy per spec TODO. Consumption-based CO2 also unavailable, "
                "so offshoring critique cannot be tested in this run."
            ),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    # ---------- PRIMARY: mean cross-country CO2 ratio ----------
    rows = []
    for c in common:
        co2_ratio = float(co2_2020[c] / co2_1990[c])
        gdp_ratio = float(gdp_2020[c] / gdp_1990[c])
        rows.append({
            "country": c,
            "co2_pc_1990": float(co2_1990[c]),
            "co2_pc_2020": float(co2_2020[c]),
            "co2_ratio_2020_1990": co2_ratio,
            "gdp_pc_1990": float(gdp_1990[c]),
            "gdp_pc_2020": float(gdp_2020[c]),
            "gdp_ratio_2020_1990": gdp_ratio,
            "pop_2020": float(pop_2020[c]),
        })
    df = pd.DataFrame(rows).set_index("country")

    mean_co2_ratio = float(df["co2_ratio_2020_1990"].mean())
    median_co2_ratio = float(df["co2_ratio_2020_1990"].median())
    pop_weighted_co2_ratio = float(
        (df["co2_ratio_2020_1990"] * df["pop_2020"]).sum() / df["pop_2020"].sum()
    )
    mean_gdp_ratio = float(df["gdp_ratio_2020_1990"].mean())

    # ---------- SECONDARY: country-level decoupling count ----------
    decoupled_mask = (
        (df["co2_ratio_2020_1990"] <= 1 - COUNTRY_DECOUPLE_CO2_DROP_MIN)
        & (df["gdp_ratio_2020_1990"] >= 1 + COUNTRY_DECOUPLE_GDP_GROWTH_MIN)
    )
    n_decoupled = int(decoupled_mask.sum())
    decoupled_countries = sorted(df.index[decoupled_mask].tolist())

    # ---------- Verdict ----------
    # The PRIMARY uses pop-weighted mean (the global question is about
    # global throughput, dominated by populous economies).
    if pop_weighted_co2_ratio >= SUPPORTED_RATIO_FLOOR:
        verdict = (
            f"SUPPORTED (production-based proxy) — Population-weighted mean "
            f"per-capita CO2 in 2020 was {pop_weighted_co2_ratio*100:.0f}% of "
            f"its 1990 level across the 26-country panel (>= {SUPPORTED_RATIO_FLOOR*100:.0f}% "
            f"floor). No global absolute decoupling visible in production-based "
            f"throughput. Cumulative real per-capita GDP grew "
            f"{(mean_gdp_ratio-1)*100:+.0f}% on average over the same window. "
            f"{n_decoupled} of {len(common)} countries individually achieved "
            f"sustained per-country absolute decoupling. "
            f"NOTE: Consumption-based MF/CO2 unavailable on disk — the offshoring "
            f"critique remains untested; see methodology_note."
        )
    elif pop_weighted_co2_ratio <= REFUTED_RATIO_CEILING:
        verdict = (
            f"refuted (production-based proxy) — Population-weighted mean "
            f"per-capita CO2 in 2020 fell to {pop_weighted_co2_ratio*100:.0f}% "
            f"of 1990 (<= {REFUTED_RATIO_CEILING*100:.0f}% ceiling). Sustained "
            f"absolute decoupling visible in the 26-country panel even before "
            f"consumption-based adjustments (which would only strengthen this "
            f"refutation if reported decoupling were a pure offshoring artifact)."
        )
    else:
        verdict = (
            f"partial — Population-weighted mean per-capita CO2 in 2020 was "
            f"{pop_weighted_co2_ratio*100:.0f}% of 1990, between the "
            f"{REFUTED_RATIO_CEILING*100:.0f}% refute-ceiling and "
            f"{SUPPORTED_RATIO_FLOOR*100:.0f}% support-floor. Some countries "
            f"decoupled ({n_decoupled} of {len(common)}); aggregate did not. "
            f"Consumption-based version remains untested."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "n_with_data": len(common),
        "primary": {
            "pop_weighted_co2_ratio_2020_1990": pop_weighted_co2_ratio,
            "mean_co2_ratio_2020_1990": mean_co2_ratio,
            "median_co2_ratio_2020_1990": median_co2_ratio,
            "supported_ratio_floor": SUPPORTED_RATIO_FLOOR,
            "refuted_ratio_ceiling": REFUTED_RATIO_CEILING,
        },
        "context": {
            "mean_gdp_pc_ratio_2020_1990": mean_gdp_ratio,
        },
        "secondary_country_decoupling": {
            "n_decoupled": n_decoupled,
            "n_total": len(common),
            "country_gdp_growth_min": COUNTRY_DECOUPLE_GDP_GROWTH_MIN,
            "country_co2_drop_min": COUNTRY_DECOUPLE_CO2_DROP_MIN,
            "decoupled_countries": decoupled_countries,
        },
        "country_data": df.reset_index().to_dict(orient="records"),
        "data_gap_note": (
            "Material Footprint / Domestic Material Consumption (UNEP IRP) "
            "unavailable in data/vintages/. Per-spec TODO, CO2 emissions per "
            "capita used as a production-based throughput proxy. "
            "Consumption-based CO2 (Global Carbon Project / Eora MRIO) also "
            "unavailable on disk, so the offshoring/consumption-based half of "
            "the claim cannot be tested in this run. The hypothesis can only "
            "be REFUTED on this evidence (sustained production-based decoupling "
            "would refute the broader claim); SUPPORTED status is provisional."
        ),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: scatter of country GDP-growth vs CO2-ratio ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
    ]
    series = []
    for i, c in enumerate(common):
        sub = (
            co2[(co2["country_iso3"] == c) & (co2["year"].between(1990, 2020))]
            [["year", "value"]]
            .dropna()
            .sort_values("year")
        )
        if sub.empty:
            continue
        baseline = float(co2_1990[c])
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

    # Add unity baseline (1990 = 1.0 reference line) and the floor/ceiling
    floor_pts = [{"x": y, "y": SUPPORTED_RATIO_FLOOR} for y in range(1990, 2021)]
    ceiling_pts = [{"x": y, "y": REFUTED_RATIO_CEILING} for y in range(1990, 2021)]
    series.insert(0, {
        "id": "SUPPORTED_FLOOR",
        "label": f"SUPPORTED floor ({SUPPORTED_RATIO_FLOOR:.2f})",
        "color": "#888888",
        "treated": True,
        "points": floor_pts,
    })
    series.insert(1, {
        "id": "REFUTED_CEILING",
        "label": f"REFUTED ceiling ({REFUTED_RATIO_CEILING:.2f})",
        "color": "#1f1f1f",
        "treated": True,
        "points": ceiling_pts,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Per-capita CO2 (production-based) indexed to 1990, 26-country panel",
        "subtitle": (
            f"Pop-weighted mean 2020/1990 ratio: {pop_weighted_co2_ratio:.2f}; "
            f"mean GDP-per-capita ratio: {mean_gdp_ratio:.2f}; "
            f"{n_decoupled}/{len(common)} countries decoupled "
            f"(>= {COUNTRY_DECOUPLE_GDP_GROWTH_MIN*100:.0f}% GDP growth AND "
            f">= {COUNTRY_DECOUPLE_CO2_DROP_MIN*100:.0f}% CO2 fall)."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "per-capita CO2 (1990 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Production-based proxy (CO2). Consumption-based MF "
                    f"unavailable on disk; offshoring critique untested."
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
            {"spec": "primary", "term": "pop_weighted_co2_ratio_2020_1990", "estimate": pop_weighted_co2_ratio},
            {"spec": "primary", "term": "mean_co2_ratio_2020_1990", "estimate": mean_co2_ratio},
            {"spec": "primary", "term": "median_co2_ratio_2020_1990", "estimate": median_co2_ratio},
            {"spec": "context", "term": "mean_gdp_pc_ratio_2020_1990", "estimate": mean_gdp_ratio},
            {"spec": "secondary", "term": "n_country_decoupled", "estimate": float(n_decoupled)},
            {"spec": "secondary", "term": "n_country_total", "estimate": float(len(common))},
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
        f"# Absolute decoupling of GDP from material throughput, global, 1990-2020",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Sample: {len(common)} of 26 countries with both 1990 and 2020 observations.",
        f"- Population-weighted mean per-capita CO2 in 2020: "
        f"**{pop_weighted_co2_ratio*100:.0f}% of 1990 baseline**.",
        f"- Simple cross-country mean: {mean_co2_ratio*100:.0f}%; "
        f"median {median_co2_ratio*100:.0f}%.",
        f"- Mean cumulative real per-capita GDP growth 1990-2020: "
        f"**{(mean_gdp_ratio-1)*100:+.0f}%**.",
        f"- Per-country decoupling (>= {COUNTRY_DECOUPLE_GDP_GROWTH_MIN*100:.0f}% GDP growth AND "
        f">= {COUNTRY_DECOUPLE_CO2_DROP_MIN*100:.0f}% CO2 drop): "
        f"**{n_decoupled} of {len(common)}** countries — "
        f"{', '.join(decoupled_countries) if decoupled_countries else 'none'}.",
        "",
        "## Method",
        "",
        "Cross-country snapshot of two ratios over 1990-2020:",
        "",
        f"1. PRIMARY: population-weighted mean of (CO2 per capita 2020 / "
        f"CO2 per capita 1990). SUPPORTED if >= "
        f"{SUPPORTED_RATIO_FLOOR}; REFUTED if <= {REFUTED_RATIO_CEILING}; "
        f"PARTIAL otherwise.",
        f"2. SECONDARY: country count where 2020 per-capita CO2 fell at "
        f"least {COUNTRY_DECOUPLE_CO2_DROP_MIN*100:.0f}% AND per-capita GDP "
        f"rose at least {COUNTRY_DECOUPLE_GDP_GROWTH_MIN*100:.0f}%.",
        "",
        "## Data gap (important caveat)",
        "",
        "The spec calls for UNEP/IRP Domestic Material Consumption + "
        "Material Footprint and the consumption-based reframing. Neither "
        "of those nor consumption-based CO2 (GCP/Eora MRIO) is available "
        "in `data/vintages/`. Per the spec's own TODO note, we substituted "
        "production-based CO2 per capita as a throughput proxy. This means "
        "the run can speak to the production-based half of the claim but "
        "NOT to the offshoring/consumption-based half. A SUPPORTED verdict "
        "is therefore provisional in the strong sense; only a REFUTED "
        "verdict on production-based throughput would dispositively refute "
        "the broader claim.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.PCAP.KD",
        f"- world_bank_wdi:SP.POP.TOTL",
        f"- owid:co2-emissions-per-capita (production-based)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
