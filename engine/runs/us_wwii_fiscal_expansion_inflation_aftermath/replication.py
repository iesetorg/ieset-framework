#!/usr/bin/env python3
"""Replication — US WWII fiscal expansion & post-control inflation aftermath.

Spec: hypotheses/fiscal/us_wwii_fiscal_expansion_inflation_aftermath.yaml v1
Position-claim: mmt #2 (school predicts: supported)

Tests the MMT-aligned claim that the largest 20th-century US fiscal
expansion (federal deficits 20-27% of GDP, 1942-1945; debt approaching
106% of GDP by 1946) did NOT produce sustained inflation once OPA
price controls were lifted (Nov 1946) and real productive capacity
returned.

PRIMARY (dispositive): mean YoY CPI inflation, 1949-1953 (5-year window
starting 2 full years after Nov-1946 OPA termination so the immediate
de-control spike washes out).
  <= 3.0%/yr  -> SUPPORTED
   > 5.0%/yr  -> REFUTED
  3.0-5.0%/yr -> partial

INFORMATIVE: peak 1947 YoY (the spike that the MMT framing discounts);
1953-1957 follow-on mean (second sustainability check).

METHOD_VALID: CPIAUCNS and FYFSGDA188S vintages cover 1939-1957 with
no gaps, AND WWII-peak (1943-1945 mean) federal deficit is at least
15% of GDP (i.e. we are testing the WWII case, not a small-expansion
edge case).
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
HID = "us_wwii_fiscal_expansion_inflation_aftermath"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Windows from spec
PRIMARY_WINDOW = (1949, 1953)        # 5-yr post-control sustained-inflation test
PEAK_WINDOW = (1947, 1948)           # immediate post-de-control spike (informative)
FOLLOWON_WINDOW = (1953, 1957)       # late-1950s sustainability follow-on
WWII_PEAK_DEFICIT_WINDOW = (1943, 1945)  # treatment-magnitude check
PREWAR_BASELINE_WINDOW = (1923, 1940)    # pre-WWII inflation norm (descriptive)

OPA_START = "1942-01-30"  # Emergency Price Control Act
OPA_END = "1946-11-09"    # OPA termination

# Dispositive thresholds
PRIMARY_SUPPORTED_THRESHOLD = 3.0    # mean YoY CPI <= 3.0% -> SUPPORTED
PRIMARY_REFUTED_THRESHOLD = 5.0      # mean YoY CPI > 5.0% -> REFUTED
WWII_DEFICIT_MAGNITUDE_GATE = 15.0   # |1943-45 mean deficit %GDP| must exceed 15%


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


def load_fred(path: Path) -> pd.Series:
    """FRED parquet schema: (date, value, realtime_start, realtime_end).
    Returns a date-indexed Series of value (float), latest-vintage row
    per date."""
    t = pq.read_table(path).to_pandas()
    t["date"] = pd.to_datetime(t["date"])
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.sort_values(["date", "realtime_start"]).drop_duplicates(
        "date", keep="last"
    )
    return t.set_index("date")["value"].dropna()


def annual_mean(monthly: pd.Series) -> pd.Series:
    """Resample a monthly (or daily) series to annual mean, indexed by year."""
    if monthly.index.freqstr is None or "Y" not in (monthly.index.freqstr or ""):
        ann = monthly.resample("YS").mean()
    else:
        ann = monthly
    ann.index = ann.index.year
    return ann.dropna()


def window_mean(series_yearly: pd.Series, lo: int, hi: int) -> float:
    sub = series_yearly[(series_yearly.index >= lo) & (series_yearly.index <= hi)]
    if sub.empty:
        return float("nan")
    return float(sub.mean())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --------- Inputs ---------
    cpi_path = latest("fred", "CPIAUCNS")
    deficit_path = latest("fred", "FYFSGDA188S")

    manifest = {
        "cpi_unadjusted": {
            "publisher": "fred",
            "series": "CPIAUCNS",
            "vintage_file": str(cpi_path.relative_to(REPO_ROOT)),
            "sha256": sha256(cpi_path),
        },
        "federal_surplus_pct_gdp": {
            "publisher": "fred",
            "series": "FYFSGDA188S",
            "vintage_file": str(deficit_path.relative_to(REPO_ROOT)),
            "sha256": sha256(deficit_path),
        },
    }

    cpi_monthly = load_fred(cpi_path)
    deficit_annual = load_fred(deficit_path)
    deficit_annual.index = deficit_annual.index.year

    # --------- METHOD_VALID ---------
    cpi_ann = annual_mean(cpi_monthly)
    cpi_yoy = (cpi_ann.pct_change() * 100.0).dropna()

    full_coverage_ok = (
        cpi_yoy.index.min() <= 1939
        and cpi_yoy.index.max() >= 1957
        and deficit_annual.index.min() <= 1939
        and deficit_annual.index.max() >= 1955
    )

    wwii_peak_deficit = window_mean(
        deficit_annual, WWII_PEAK_DEFICIT_WINDOW[0], WWII_PEAK_DEFICIT_WINDOW[1]
    )
    # Sign convention: FYFSGDA188S is surplus (+) / deficit (-). Magnitude:
    wwii_peak_deficit_magnitude = abs(wwii_peak_deficit)
    magnitude_ok = wwii_peak_deficit_magnitude >= WWII_DEFICIT_MAGNITUDE_GATE
    method_valid = full_coverage_ok and magnitude_ok

    # --------- PRIMARY ---------
    primary_mean = window_mean(cpi_yoy, *PRIMARY_WINDOW)

    if not method_valid:
        verdict_word = "inconclusive"
        verdict_reason = (
            f"method-valid gate failed: coverage_ok={full_coverage_ok}, "
            f"WWII-peak deficit magnitude {wwii_peak_deficit_magnitude:.1f}%GDP "
            f"vs gate {WWII_DEFICIT_MAGNITUDE_GATE:.1f}%."
        )
    elif primary_mean <= PRIMARY_SUPPORTED_THRESHOLD:
        verdict_word = "SUPPORTED"
        verdict_reason = (
            f"5-yr post-control mean CPI YoY {primary_mean:+.2f}%/yr "
            f"<= {PRIMARY_SUPPORTED_THRESHOLD:.1f}%/yr threshold."
        )
    elif primary_mean > PRIMARY_REFUTED_THRESHOLD:
        verdict_word = "refuted"
        verdict_reason = (
            f"5-yr post-control mean CPI YoY {primary_mean:+.2f}%/yr "
            f"> {PRIMARY_REFUTED_THRESHOLD:.1f}%/yr — sustained inflation."
        )
    else:
        verdict_word = "partial"
        verdict_reason = (
            f"5-yr post-control mean CPI YoY {primary_mean:+.2f}%/yr "
            f"in the {PRIMARY_SUPPORTED_THRESHOLD:.1f}-{PRIMARY_REFUTED_THRESHOLD:.1f}%/yr "
            f"partial band."
        )

    # --------- INFORMATIVE ---------
    peak_1947 = float(cpi_yoy.get(1947, float("nan")))
    peak_window_mean = window_mean(cpi_yoy, *PEAK_WINDOW)
    followon_mean = window_mean(cpi_yoy, *FOLLOWON_WINDOW)
    prewar_mean = window_mean(cpi_yoy, *PREWAR_BASELINE_WINDOW)

    verdict = (
        f"{verdict_word} — {verdict_reason} "
        f"WWII-peak federal deficit (1943-45 mean): "
        f"{wwii_peak_deficit:+.1f}%GDP (magnitude {wwii_peak_deficit_magnitude:.1f}%). "
        f"Immediate post-control 1947 YoY: {peak_1947:+.1f}%; "
        f"1947-48 mean: {peak_window_mean:+.1f}%; "
        f"1953-57 follow-on mean: {followon_mean:+.1f}%; "
        f"pre-WWII (1923-40) baseline mean: {prewar_mean:+.1f}%."
    )

    diagnostics = {
        "verdict": verdict,
        "verdict_word": verdict_word,
        "method_valid": bool(method_valid),
        "full_coverage_ok": bool(full_coverage_ok),
        "magnitude_gate_ok": bool(magnitude_ok),
        "primary_window": list(PRIMARY_WINDOW),
        "primary_mean_cpi_yoy_pct": primary_mean,
        "primary_supported_threshold_pct": PRIMARY_SUPPORTED_THRESHOLD,
        "primary_refuted_threshold_pct": PRIMARY_REFUTED_THRESHOLD,
        "wwii_peak_deficit_pct_gdp_signed": wwii_peak_deficit,
        "wwii_peak_deficit_magnitude_pct_gdp": wwii_peak_deficit_magnitude,
        "wwii_peak_deficit_window": list(WWII_PEAK_DEFICIT_WINDOW),
        "informative_peak_1947_yoy_pct": peak_1947,
        "informative_peak_1947_48_mean_pct": peak_window_mean,
        "informative_followon_1953_57_mean_pct": followon_mean,
        "informative_prewar_1923_40_mean_pct": prewar_mean,
        "cpi_yoy_by_year_1939_1957": {
            int(y): float(v)
            for y, v in cpi_yoy[(cpi_yoy.index >= 1939) & (cpi_yoy.index <= 1957)].items()
        },
        "federal_deficit_pct_gdp_by_year_1939_1955": {
            int(y): float(v)
            for y, v in deficit_annual[
                (deficit_annual.index >= 1939) & (deficit_annual.index <= 1955)
            ].items()
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # --------- Chart ---------
    chart_years = list(range(1939, 1958))
    cpi_pts = [
        {"x": int(y), "y": float(cpi_yoy.get(y, float("nan")))}
        for y in chart_years
        if not pd.isna(cpi_yoy.get(y, float("nan")))
    ]
    # Federal deficit as -1 * surplus to plot deficit-positive (more intuitive)
    deficit_pts = [
        {"x": int(y), "y": float(-deficit_annual.get(y, float("nan")))}
        for y in chart_years
        if not pd.isna(deficit_annual.get(y, float("nan")))
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US WWII fiscal expansion and CPI inflation, 1939-1957",
        "subtitle": (
            f"PRIMARY 1949-1953 mean CPI YoY: {primary_mean:+.2f}%/yr "
            f"(threshold for SUPPORTED <= {PRIMARY_SUPPORTED_THRESHOLD:.1f}%). "
            f"WWII-peak (1943-45) federal deficit magnitude: "
            f"{wwii_peak_deficit_magnitude:.1f}% of GDP."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "% (YoY for CPI; % of GDP for deficit)", "type": "linear"},
        "series": [
            {
                "id": "cpi_yoy",
                "label": "CPI inflation, YoY % (CPIAUCNS, annual mean)",
                "color": "#E15759",
                "treated": True,
                "points": cpi_pts,
            },
            {
                "id": "fed_deficit_pct_gdp",
                "label": "Federal deficit, % of GDP (FYFSGDA188S, sign-flipped)",
                "color": "#4E79A7",
                "treated": False,
                "points": deficit_pts,
            },
        ],
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"OPA price controls active {OPA_START} to {OPA_END}. "
                    f"PRIMARY window 1949-1953 starts 2 yrs after OPA termination "
                    f"so the 1947 spike ({peak_1947:+.1f}%) is reported "
                    f"INFORMATIVE-only."
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

    # --------- Coefficients ---------
    pd.DataFrame(
        [
            {"spec": "primary", "term": "mean_cpi_yoy_1949_1953", "estimate": primary_mean},
            {"spec": "informative", "term": "cpi_yoy_1947", "estimate": peak_1947},
            {"spec": "informative", "term": "mean_cpi_yoy_1947_1948", "estimate": peak_window_mean},
            {"spec": "informative", "term": "mean_cpi_yoy_1953_1957", "estimate": followon_mean},
            {"spec": "informative", "term": "mean_cpi_yoy_1923_1940_baseline", "estimate": prewar_mean},
            {"spec": "method_valid", "term": "wwii_peak_deficit_signed_1943_1945", "estimate": wwii_peak_deficit},
            {"spec": "method_valid", "term": "wwii_peak_deficit_magnitude_1943_1945", "estimate": wwii_peak_deficit_magnitude},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # --------- Manifest ---------
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

    # --------- Result card ---------
    card = [
        f"# US WWII fiscal expansion & inflation aftermath",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- WWII-peak federal deficit (1943-1945 mean): "
        f"**{wwii_peak_deficit:+.1f}% of GDP** "
        f"(magnitude {wwii_peak_deficit_magnitude:.1f}%; "
        f"the largest sustained US fiscal expansion of the 20th century).",
        f"- Pre-WWII baseline CPI inflation (1923-1940 mean): "
        f"**{prewar_mean:+.2f}%/yr** (deflationary tilt of the inter-war era).",
        f"- Immediate post-OPA-termination CPI YoY: 1947 = "
        f"**{peak_1947:+.1f}%**; 1947-1948 mean = "
        f"**{peak_window_mean:+.1f}%/yr**.",
        f"- **PRIMARY (dispositive):** mean CPI YoY 1949-1953 = "
        f"**{primary_mean:+.2f}%/yr**.",
        f"  - SUPPORTED threshold: <= {PRIMARY_SUPPORTED_THRESHOLD:.1f}%/yr.",
        f"  - REFUTED threshold: > {PRIMARY_REFUTED_THRESHOLD:.1f}%/yr.",
        f"- 1953-1957 follow-on mean: **{followon_mean:+.2f}%/yr** "
        f"(second sustainability check).",
        "",
        "## Method",
        "",
        "Window-mean test on annualised FRED CPIAUCNS YoY inflation, with",
        "the dispositive PRIMARY window 1949-1953 chosen to start 2 full",
        "years after the Nov-1946 OPA price-control termination so the",
        "immediate 1947 de-control spike is excluded from the dispositive",
        "test. The 1947 spike and the 1947-1948 window are reported as",
        "INFORMATIVE so the reader can see what the MMT framing discounts.",
        "",
        "METHOD_VALID gates: (i) FRED CPIAUCNS and FYFSGDA188S vintages",
        "cover the full 1939-1957 window; (ii) WWII-peak (1943-1945 mean)",
        f"federal deficit magnitude must exceed {WWII_DEFICIT_MAGNITUDE_GATE:.0f}% of GDP",
        "(confirms we are testing the WWII-scale fiscal expansion case).",
        "",
        "Caveat (per the spec's `disclosure` field): the verdict is",
        "window-choice sensitive. The 8-year 1946-1953 window mean is",
        "substantially higher (the 1946-1948 surge dominates), and the",
        "Korean-War 1951 spike (separate fiscal-impulse event) is included",
        "in the PRIMARY window. The Romer-counterfactual price-control",
        "adjustment (reflate suppressed wartime CPI) is left to v2.",
        "",
        "## Data",
        "",
        f"- fred:CPIAUCNS — US CPI all items, 1913+ monthly",
        f"- fred:FYFSGDA188S — US federal surplus/deficit % GDP, 1929+ annual",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
