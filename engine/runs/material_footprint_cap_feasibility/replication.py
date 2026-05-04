#!/usr/bin/env python3
"""Replication — material-footprint cap feasibility no-collapse proxy.

Spec: hypotheses/growth/material_footprint_cap_feasibility.yaml v2

This deliberately tests only the pre-registered macro no-collapse component.
It cannot fully support the claim without country/Wales material-footprint and
binding-cap implementation data.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
HID = "material_footprint_cap_feasibility"
OUT_DIR = ROOT / "engine" / "runs" / HID

COUNTRIES = ["CHE", "GBR"]
START_YEAR = 2015
END_YEAR = 2023
GDP_REFUTE_THRESHOLD = -0.02
UNEMP_REFUTE_THRESHOLD_PP = 2.0


def latest(pub: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_wdi(path: Path) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    out = df[df["country_iso3"].isin(COUNTRIES)][["country_iso3", "year", "value"]].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["year", "value"])


def value_at(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].iloc[0])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    unemp_path = latest("world_bank_wdi", "SL.UEM.TOTL.ZS")
    material_path = latest("owid", "material-footprint-per-capita")

    gdp = load_wdi(gdp_path)
    unemp = load_wdi(unemp_path)
    material_raw = pq.read_table(material_path).to_pandas()
    material_countries = sorted(str(x) for x in material_raw.get("country_iso3", pd.Series(dtype=str)).dropna().unique())
    material_has_cases = any(c in material_countries for c in COUNTRIES)

    cases = []
    missing = []
    for country in COUNTRIES:
        gdp_start = value_at(gdp, country, START_YEAR)
        gdp_end = value_at(gdp, country, END_YEAR)
        unemp_start = value_at(unemp, country, START_YEAR)
        unemp_end = value_at(unemp, country, END_YEAR)
        if None in {gdp_start, gdp_end, unemp_start, unemp_end}:
            missing.append(country)
            continue
        gdp_change = (gdp_end / gdp_start) - 1
        unemp_change = unemp_end - unemp_start
        breached = (gdp_change < GDP_REFUTE_THRESHOLD) or (
            unemp_change > UNEMP_REFUTE_THRESHOLD_PP
        )
        cases.append(
            {
                "country_iso3": country,
                "gdp_pc_2015": gdp_start,
                "gdp_pc_2023": gdp_end,
                "gdp_pc_change_ratio": gdp_change,
                "unemployment_2015": unemp_start,
                "unemployment_2023": unemp_end,
                "unemployment_change_pp": unemp_change,
                "no_collapse_breach": breached,
            }
        )

    method_valid = not missing and len(cases) == len(COUNTRIES)
    if not method_valid:
        verdict_label = "inconclusive"
        verdict = (
            "INCONCLUSIVE_DATA_PENDING — missing WDI GDP/unemployment endpoint data for "
            f"{missing}"
        )
    else:
        breached_cases = [c["country_iso3"] for c in cases if c["no_collapse_breach"]]
        if breached_cases:
            verdict_label = "refuted"
            verdict = (
                "refuted — at least one registered national proxy breached the no-collapse "
                f"threshold: {breached_cases}."
            )
        else:
            verdict_label = "partial"
            verdict = (
                "partial — CHE and GBR pass the registered 2015-2023 no-collapse macro "
                "thresholds, but material-footprint and Wales-specific binding-cap evidence "
                "remain unavailable locally, so full support is not scored."
            )

    manifest = {
        "gdp_pc": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_path.relative_to(ROOT)),
            "sha256": sha256(gdp_path),
        },
        "unemployment": {
            "publisher": "world_bank_wdi",
            "series": "SL.UEM.TOTL.ZS",
            "vintage_file": str(unemp_path.relative_to(ROOT)),
            "sha256": sha256(unemp_path),
        },
        "material_footprint": {
            "publisher": "owid",
            "series": "material-footprint-per-capita",
            "vintage_file": str(material_path.relative_to(ROOT)),
            "sha256": sha256(material_path),
            "case_country_coverage": material_has_cases,
            "country_codes_present": material_countries,
        },
    }

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": method_valid,
        "countries": COUNTRIES,
        "period": [START_YEAR, END_YEAR],
        "gdp_refute_threshold": GDP_REFUTE_THRESHOLD,
        "unemployment_refute_threshold_pp": UNEMP_REFUTE_THRESHOLD_PP,
        "material_footprint_case_country_coverage": material_has_cases,
        "cases": cases,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n"
        f"  gdp_pc: {manifest['gdp_pc']['vintage_file']}\n"
        f"  unemployment: {manifest['unemployment']['vintage_file']}\n"
        f"  material_footprint: {manifest['material_footprint']['vintage_file']}\n"
    )
    pd.DataFrame(cases).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "chart_data.json").write_text(
        json.dumps(
            {
                "kind": "result",
                "chart_id": f"{HID}/fig1",
                "title": "No-collapse proxy for material-footprint cap cases",
                "subtitle": "Endpoint changes from 2015 to 2023; full material-footprint evidence unavailable locally.",
                "type": "bar",
                "series": [
                    {
                        "id": "gdp_pc_change",
                        "label": "Real GDP pc change",
                        "points": [
                            {"x": c["country_iso3"], "y": c["gdp_pc_change_ratio"]}
                            for c in cases
                        ],
                    },
                    {
                        "id": "unemployment_change_pp",
                        "label": "Unemployment change, pp",
                        "points": [
                            {"x": c["country_iso3"], "y": c["unemployment_change_pp"]}
                            for c in cases
                        ],
                    },
                ],
            },
            indent=2,
        )
        + "\n"
    )
    lines = [
        f"# {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Registered Test",
        "",
        "- Cases: Switzerland (`CHE`) and United Kingdom national proxy for Wales (`GBR`).",
        "- Period: 2015 to 2023 endpoints.",
        "- Refute if any case has real GDP per capita below -2% or unemployment above +2pp.",
        "- Full support is blocked unless country/Wales material-footprint and binding-cap data are available.",
        "",
        "## Case Results",
        "",
    ]
    for case in cases:
        lines.append(
            "- "
            f"{case['country_iso3']}: GDP pc {case['gdp_pc_change_ratio']*100:+.1f}%, "
            f"unemployment {case['unemployment_change_pp']:+.1f}pp."
        )
    lines.extend(
        [
            "",
            "## Data Limitation",
            "",
            "The local OWID material-footprint vintage contains no CHE/GBR/Wales observations; this run therefore cannot score full support.",
            "",
        ]
    )
    (OUT_DIR / "result_card.md").write_text("\n".join(lines))
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
