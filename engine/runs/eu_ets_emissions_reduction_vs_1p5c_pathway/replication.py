#!/usr/bin/env python3
"""Replication — EU ETS emissions trajectory vs 1.5C-style pathway.

Spec: hypotheses/energy/eu_ets_emissions_reduction_vs_1p5c_pathway.yaml v2

This is a descriptive pathway test. It does not estimate the causal effect of
the EU ETS; it tests the narrower pre-registered claim that EU emissions failed
to fall at a 1.5C-aligned pace.
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
HID = "eu_ets_emissions_reduction_vs_1p5c_pathway"
OUT_DIR = ROOT / "engine" / "runs" / HID

BASE_YEAR = 1990
PATH_START = 2015
PATH_END = 2030
OBS_END = 2023
TARGET_REDUCTION = 0.55
FAIL_GAP_THRESHOLD = 0.10


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    inventory_path = latest("eurostat", "env_air_gge")
    raw = pq.read_table(
        inventory_path,
        columns=["unit", "airpol", "src_crf", "geo_code", "period", "value"],
    ).to_pandas()
    panel = raw[
        (raw["unit"] == "MIO_T")
        & (raw["airpol"] == "CO2")
        & (raw["src_crf"] == "TOTX4_MEMO")
        & (raw["geo_code"] == "EU27_2020")
    ].copy()
    panel["year"] = pd.to_numeric(panel["period"], errors="coerce").astype("Int64")
    panel["value"] = pd.to_numeric(panel["value"], errors="coerce")
    panel = panel.dropna(subset=["year", "value"]).sort_values("year")

    observed_years = set(panel["year"].astype(int))
    required_years = {BASE_YEAR, PATH_START, *range(PATH_START, OBS_END + 1)}
    missing = sorted(required_years - observed_years)
    method_valid = not missing

    if not method_valid:
        verdict_label = "inconclusive"
        verdict = (
            "INCONCLUSIVE_DATA_PENDING — Eurostat env_air_gge is missing required "
            f"EU27 CO2 years: {missing}"
        )
        diagnostics = {
            "hypothesis_id": HID,
            "verdict": verdict,
            "verdict_label": verdict_label,
            "method_valid": False,
            "missing_years": missing,
            "run_utc": datetime.now(timezone.utc).isoformat(),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        return 0

    by_year = {int(r.year): float(r.value) for r in panel.itertuples()}
    base_1990 = by_year[BASE_YEAR]
    start_2015 = by_year[PATH_START]
    target_2030 = base_1990 * (1 - TARGET_REDUCTION)

    rows = []
    actual_cumulative = 0.0
    path_cumulative = 0.0
    for year in range(PATH_START, OBS_END + 1):
        actual = by_year[year]
        path_value = start_2015 + ((year - PATH_START) / (PATH_END - PATH_START)) * (
            target_2030 - start_2015
        )
        gap = (actual / path_value) - 1
        actual_cumulative += actual
        path_cumulative += path_value
        rows.append(
            {
                "year": year,
                "actual_co2_mio_t": actual,
                "path_co2_mio_t": path_value,
                "gap_ratio": gap,
            }
        )

    endpoint_gap = rows[-1]["gap_ratio"]
    cumulative_gap = (actual_cumulative / path_cumulative) - 1

    if cumulative_gap > FAIL_GAP_THRESHOLD and endpoint_gap > FAIL_GAP_THRESHOLD:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED — EU27 CO2 exceeded the registered 1.5C-style pathway by "
            f"{cumulative_gap*100:.1f}% cumulatively over 2015-2023 and "
            f"{endpoint_gap*100:.1f}% at the 2023 endpoint."
        )
    elif abs(cumulative_gap) <= FAIL_GAP_THRESHOLD and abs(endpoint_gap) <= FAIL_GAP_THRESHOLD:
        verdict_label = "refuted"
        verdict = (
            "refuted — EU27 CO2 tracked within the registered ±10% pathway band: "
            f"cumulative 2015-2023 gap {cumulative_gap*100:+.1f}%, 2023 endpoint "
            f"gap {endpoint_gap*100:+.1f}%."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            "weakened — EU27 CO2 missed one registered pathway criterion but not both: "
            f"cumulative gap {cumulative_gap*100:+.1f}%, endpoint gap "
            f"{endpoint_gap*100:+.1f}%."
        )

    manifest = {
        "eurostat_env_air_gge": {
            "publisher": "eurostat",
            "series": "env_air_gge",
            "vintage_file": str(inventory_path.relative_to(ROOT)),
            "sha256": sha256(inventory_path),
            "filters": {
                "unit": "MIO_T",
                "airpol": "CO2",
                "src_crf": "TOTX4_MEMO",
                "geo_code": "EU27_2020",
            },
        }
    }
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "benchmark": {
            "base_year": BASE_YEAR,
            "path_start": PATH_START,
            "path_end": PATH_END,
            "observed_end": OBS_END,
            "target_reduction_from_1990": TARGET_REDUCTION,
            "support_gap_threshold": FAIL_GAP_THRESHOLD,
            "base_1990_co2_mio_t": base_1990,
            "path_start_2015_co2_mio_t": start_2015,
            "target_2030_co2_mio_t": target_2030,
        },
        "actual_cumulative_2015_2023": actual_cumulative,
        "path_cumulative_2015_2023": path_cumulative,
        "cumulative_gap_ratio": cumulative_gap,
        "endpoint_gap_ratio_2023": endpoint_gap,
        "series": rows,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n"
        f"  eurostat_env_air_gge: {manifest['eurostat_env_air_gge']['vintage_file']}\n"
        f"  sha256: {manifest['eurostat_env_air_gge']['sha256']}\n"
    )
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "chart_data.json").write_text(
        json.dumps(
            {
                "kind": "result",
                "chart_id": f"{HID}/fig1",
                "title": "EU27 CO2 vs registered 1.5C-style path",
                "subtitle": (
                    f"Cumulative gap {cumulative_gap*100:+.1f}%; "
                    f"2023 endpoint gap {endpoint_gap*100:+.1f}%"
                ),
                "type": "line",
                "x_axis": {"label": "Year", "type": "linear"},
                "y_axis": {"label": "CO2 excluding LULUCF/memo items, Mt", "type": "linear"},
                "series": [
                    {
                        "id": "actual",
                        "label": "Actual EU27 CO2",
                        "color": "#4E79A7",
                        "points": [{"x": r["year"], "y": r["actual_co2_mio_t"]} for r in rows],
                    },
                    {
                        "id": "path",
                        "label": "Registered pathway",
                        "color": "#E15759",
                        "points": [{"x": r["year"], "y": r["path_co2_mio_t"]} for r in rows],
                    },
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Registered Test",
                "",
                "- Data: Eurostat `env_air_gge`, EU27_2020 CO2, `TOTX4_MEMO`, million tonnes.",
                "- Benchmark: straight-line path from observed 2015 EU27 CO2 to 45% of 1990 EU27 CO2 by 2030.",
                "- Support threshold: cumulative and endpoint gaps both greater than +10%.",
                "- Refutation threshold: cumulative and endpoint gaps both within ±10%.",
                "",
                "## Key Numbers",
                "",
                f"- 1990 CO2: {base_1990:.1f} Mt.",
                f"- 2015 CO2: {start_2015:.1f} Mt.",
                f"- 2030 path target: {target_2030:.1f} Mt.",
                f"- 2015-2023 cumulative gap: {cumulative_gap*100:+.1f}%.",
                f"- 2023 endpoint gap: {endpoint_gap*100:+.1f}%.",
                "",
                "## Method Note",
                "",
                "This is descriptive and does not identify the causal contribution of the EU ETS.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
