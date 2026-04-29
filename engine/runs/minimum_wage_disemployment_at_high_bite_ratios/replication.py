#!/usr/bin/env python3
"""Replication — Minimum-wage disemployment at high bite ratios, 1990-2022.

Spec: hypotheses/labour/minimum_wage_disemployment_at_high_bite_ratios.yaml v1
Steelman: hypotheses/steelman/minimum_wage_disemployment_at_high_bite_ratios.md
Position-claim: chicago_monetarism #12 (school predicts: supported)

PRIMARY (dispositive):
  Stratified Callaway-Sant'Anna staggered DiD on US states 1990-2022.
  States are split into HIGH-BITE (state-min / state-median-hourly-wage
  >= 0.55) vs LOW-BITE (< 0.45) cohorts. Outcome is teen 16-19
  employment-to-population ratio (BLS LAU state). The hypothesis is
  SUPPORTED iff:

      ATT_high_bite - ATT_low_bite <= -0.020 (pp of teen E/P)
      with p < 0.10, state-clustered SE.

  REFUTED iff differential >= 0 at p < 0.10 (Chicago direction wrong),
  OR |differential| < 0.005 with sufficient power (effect too small
  to support the claim's substantive content).

INFORMATIVE (also computed when data is present):
  - Border-county Dube-Lester-Reich elasticity on QCEW NAICS-722
    (food/accommodation) employment for state-pairs whose bite ratios
    diverge by >= 10pp.
  - Cross-country OECD bite-ratio panel (15-country) regression of
    low-skill unemployment rate on bite-ratio with country and year FE.

METHOD_VALID gates (per spec.falsification.threshold):
  - BLS LAU state teen E/P series for >= 40 of 50 states with
    >= 20 years of coverage.
  - USDOL state-minimum-wage history with >= 30 states having a
    state floor distinct from the federal floor.
  - OECD MWUSD bite-ratio for >= 12 of 15 spec countries with
    >= 20 years of coverage.

If any METHOD_VALID gate fails, the verdict is `inconclusive — data
gap on <publisher>:<series>` per HANDOFF_TO_RUN_AGENT.md ("Don't
fabricate data. If the publisher's vintage doesn't contain a series
the spec needs, emit `inconclusive` and stop."). A data gap is NOT
a refutation — the scoreboard treats inconclusive as neutral.

The verdict word is the first token of `diagnostics.verdict`, parsed
case-insensitively by the scoring layer (web/lib/content.ts).
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
HID = "minimum_wage_disemployment_at_high_bite_ratios"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1990, 2022)
EXCLUDE_YEARS = {2020, 2021}  # COVID labour-market shock — per sample.exclusion_rules

# ---- Falsification thresholds (from spec.falsification.threshold) ----
HIGH_BITE_CUTOFF = 0.55         # min/median wage >= this → HIGH-BITE cohort
LOW_BITE_CUTOFF = 0.45          # min/median wage <  this → LOW-BITE cohort
SUPPORTED_DIFFERENTIAL = -0.020  # ATT_high - ATT_low must be <= this
REFUTED_NEAR_ZERO_BAND = 0.005  # |differential| < this with power → refuted
SECONDARY_BORDER_CUTOFF = 0.10   # bite-ratio gap for border-pair inclusion

# METHOD_VALID gate thresholds
MIN_STATES_WITH_DATA = 40
MIN_YEARS_PER_STATE = 20
MIN_STATES_WITH_BINDING_CHANGE = 30
MIN_OECD_COUNTRIES = 12
MIN_OECD_YEARS = 20

OECD_COUNTRIES = [
    "USA", "GBR", "FRA", "DEU", "AUS", "CAN", "JPN", "KOR", "NLD",
    "BEL", "ESP", "IRL", "NZL", "POL", "MEX",
]

# Required series per spec.variables. Tuples of (publisher, series, role).
REQUIRED_OUTCOME = [
    # PRIMARY: state-level BLS LAU teen E/P panel (50 states × ~30 years).
    # Standard BLS series-id pattern: LAUST<FIPS>0000000016A (CPS state).
    # Currently only national LNS12300012 is on disk.
    ("bls", "LAU_state_teen_employment_population_ratio_panel"),
]
REQUIRED_TREATMENT = [
    # USDOL state minimum-wage history (statutory state floor by year).
    ("usdol", "state_minimum_wage_history"),
    # State median hourly wage (BLS OES) — needed to compute bite ratios.
    ("bls", "OES_state_median_hourly_wage_panel"),
]
REQUIRED_BORDER_PAIR = [
    # QCEW county-level NAICS-722 employment for the Dube-Lester-Reich
    # border-pair informative specification.
    ("bls", "QCEW_county_NAICS722_employment_panel"),
]
REQUIRED_OECD = [
    # OECD MWUSD: cross-country bite-ratio (min/median full-time wage).
    ("oecd", "MWUSD_minimum_to_median_wage_ratio"),
    # OECD low-skill unemployment-rate panel (DSD_LMS).
    ("oecd", "DSD_LMS_low_education_unemployment_rate"),
]

ALL_REQUIRED = (
    REQUIRED_OUTCOME
    + REQUIRED_TREATMENT
    + REQUIRED_BORDER_PAIR
    + REQUIRED_OECD
)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    """Return latest vintage parquet for (pub, series) or None if absent."""
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Vintage discovery ----------
    available: dict[str, dict] = {}
    for pub, series in ALL_REQUIRED:
        p = latest(pub, series)
        key = f"{pub}:{series}"
        if p is not None:
            available[key] = {
                "publisher": pub,
                "series": series,
                "vintage_file": str(p.relative_to(REPO_ROOT)),
                "sha256": sha256(p),
            }

    missing_outcome = [
        f"{p}:{s}" for p, s in REQUIRED_OUTCOME if f"{p}:{s}" not in available
    ]
    missing_treatment = [
        f"{p}:{s}" for p, s in REQUIRED_TREATMENT if f"{p}:{s}" not in available
    ]
    missing_border = [
        f"{p}:{s}" for p, s in REQUIRED_BORDER_PAIR if f"{p}:{s}" not in available
    ]
    missing_oecd = [
        f"{p}:{s}" for p, s in REQUIRED_OECD if f"{p}:{s}" not in available
    ]

    # The stratified Callaway-Sant'Anna primary needs THREE state-level series
    # (teen E/P, USDOL state minwage history, BLS OES state median hourly wage)
    # to (a) construct bite-ratio cohorts and (b) run the cross-cohort DiD.
    # Without all three the primary cannot be estimated at all.
    can_run_primary = (
        "bls:LAU_state_teen_employment_population_ratio_panel" in available
        and "usdol:state_minimum_wage_history" in available
        and "bls:OES_state_median_hourly_wage_panel" in available
    )
    can_run_border = (
        "bls:QCEW_county_NAICS722_employment_panel" in available
        and "usdol:state_minimum_wage_history" in available
    )
    can_run_oecd = (
        "oecd:MWUSD_minimum_to_median_wage_ratio" in available
        and "oecd:DSD_LMS_low_education_unemployment_rate" in available
    )

    # ---------- METHOD_VALID gate: data gap → inconclusive ----------
    if not can_run_primary:
        verdict = (
            "inconclusive — data gap on "
            + ", ".join(missing_outcome + missing_treatment)
            + ". The spec's primary stratified Callaway-Sant'Anna "
            "DiD on US-state cohorts split by bite ratio "
            "(state-min / state-median-hourly-wage) cannot be "
            "estimated without (a) the BLS LAU state teen "
            "employment-population panel, (b) the USDOL state "
            "minimum-wage history, and (c) the BLS OES state "
            "median-hourly-wage panel. On-disk BLS vintages currently "
            "include only national LNS/CES/CUUR series; the state "
            "fan-out has not been fetched. Cross-country OECD MWUSD "
            "bite-ratio fallback is also absent. No coefficients computed."
        )

        diagnostics = {
            "verdict": verdict,
            "all_pass": False,
            "method_valid": False,
            "data_gap": True,
            "can_run_primary": can_run_primary,
            "can_run_border_pair": can_run_border,
            "can_run_oecd_panel": can_run_oecd,
            "missing_outcome_series": missing_outcome,
            "missing_treatment_series": missing_treatment,
            "missing_border_pair_series": missing_border,
            "missing_oecd_series": missing_oecd,
            "available_series": sorted(available.keys()),
            "n_required": len(ALL_REQUIRED),
            "n_available": len(available),
            "thresholds": {
                "high_bite_cutoff": HIGH_BITE_CUTOFF,
                "low_bite_cutoff": LOW_BITE_CUTOFF,
                "supported_differential_pp": SUPPORTED_DIFFERENTIAL,
                "refuted_near_zero_band_pp": REFUTED_NEAR_ZERO_BAND,
            },
            "method_valid_gates": {
                "min_states_with_data": MIN_STATES_WITH_DATA,
                "min_years_per_state": MIN_YEARS_PER_STATE,
                "min_states_binding_change": MIN_STATES_WITH_BINDING_CHANGE,
                "min_oecd_countries": MIN_OECD_COUNTRIES,
                "min_oecd_years": MIN_OECD_YEARS,
            },
            "att_high_bite_pp": None,
            "att_low_bite_pp": None,
            "att_differential_pp": None,
            "att_differential_se": None,
            "att_differential_pvalue": None,
            "n_high_bite_states": None,
            "n_low_bite_states": None,
            "border_pair_elasticity": None,
            "oecd_panel_beta": None,
            "period": list(PERIOD),
            "exclude_years": sorted(EXCLUDE_YEARS),
            "countries_oecd": OECD_COUNTRIES,
        }
        (OUT_DIR / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2) + "\n"
        )

        # Empty coefficients table — schema-compliant placeholder.
        pd.DataFrame(
            [
                {"spec": "primary_stratified_cs", "term": "att_high_bite_pp", "estimate": np.nan},
                {"spec": "primary_stratified_cs", "term": "att_low_bite_pp", "estimate": np.nan},
                {"spec": "primary_stratified_cs", "term": "differential_pp", "estimate": np.nan},
                {"spec": "primary_stratified_cs", "term": "differential_se", "estimate": np.nan},
                {"spec": "border_pair_dlr", "term": "elasticity_naics722_minwage", "estimate": np.nan},
                {"spec": "oecd_panel_fe", "term": "beta_lowskill_unemp_on_bite_ratio", "estimate": np.nan},
            ]
        ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "Min-wage bite-ratio disemployment — DATA GAP",
            "subtitle": (
                f"{len(missing_outcome) + len(missing_treatment)} of "
                f"{len(REQUIRED_OUTCOME) + len(REQUIRED_TREATMENT)} required "
                "primary state-panel series not yet fetched. Stratified "
                "Callaway-Sant'Anna DiD on US-state bite-ratio cohorts "
                "cannot be estimated; OECD cross-country bite-ratio fallback "
                "is also absent."
            ),
            "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {
                "label": "ATT differential (HIGH - LOW bite cohorts), pp teen E/P",
                "type": "linear",
            },
            "series": [],
            "annotations": [
                {
                    "type": "note",
                    "label": (
                        "Required-but-missing series: "
                        + "; ".join(
                            missing_outcome
                            + missing_treatment
                            + missing_border
                            + missing_oecd
                        )
                    ),
                },
                {
                    "type": "note",
                    "label": (
                        "Pre-registered SUPPORTED threshold: "
                        f"ATT_high − ATT_low ≤ {SUPPORTED_DIFFERENTIAL:+.3f} pp "
                        "with p<0.10. REFUTED if differential ≥ 0 at p<0.10 "
                        f"OR |differential| < {REFUTED_NEAR_ZERO_BAND:+.3f} pp "
                        "with sufficient power."
                    ),
                },
            ],
            "sources": [
                {
                    "publisher_id": v["publisher"],
                    "series_id": v["series"],
                    "vintage_file": v["vintage_file"],
                }
                for v in available.values()
            ],
            "permalink": f"/h/{HID}",
        }
        (OUT_DIR / "chart_data.json").write_text(
            json.dumps(chart_data, indent=2) + "\n"
        )

        manifest_lines = [
            f"hypothesis_id: {HID}",
            f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
            "status: data_gap_inconclusive",
            "missing_series:",
        ]
        for k in missing_outcome + missing_treatment + missing_border + missing_oecd:
            manifest_lines.append(f"  - {k}")
        manifest_lines.append("vintages:")
        if available:
            for k, v in available.items():
                manifest_lines.append(f"  '{k}':")
                manifest_lines.append(f"    publisher: {v['publisher']}")
                manifest_lines.append(f"    series: {v['series']}")
                manifest_lines.append(f"    vintage_file: {v['vintage_file']}")
                manifest_lines.append(f"    sha256: {v['sha256']}")
        else:
            manifest_lines.append("  {}")
        (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

        card = [
            "# Minimum-wage disemployment at high bite ratios, 1990-2022",
            "",
            f"**Verdict:** {verdict}",
            "",
            "## Summary",
            "",
            "- Tests the Chicago-monetarist claim that high bite-ratio "
            "(state-min / state-median-hourly-wage ≥ 0.55) cohorts show "
            "measurable extra teen disemployment vs low bite-ratio "
            "(< 0.45) cohorts in the 1990-2022 US-state panel.",
            "- Primary statistic: ATT(high-bite) − ATT(low-bite) on teen "
            "E/P, percentage points. SUPPORTED iff ≤ −0.020 pp at p<0.10.",
            "- Informative: Dube-Lester-Reich border-county elasticity "
            "on QCEW NAICS-722 (food services); cross-country OECD "
            "bite-ratio panel regression for the 15 spec countries.",
            f"- Required series: {len(REQUIRED_OUTCOME)} outcome, "
            f"{len(REQUIRED_TREATMENT)} treatment (state min-wage history "
            "+ state median hourly wage), "
            f"{len(REQUIRED_BORDER_PAIR)} border-pair, "
            f"{len(REQUIRED_OECD)} OECD = {len(ALL_REQUIRED)} total.",
            f"- Found on-disk: {len(available)} of {len(ALL_REQUIRED)}.",
            f"- Missing primary outcome: {missing_outcome or '(none)'}.",
            f"- Missing treatment: {missing_treatment or '(none)'}.",
            f"- Missing border-pair: {missing_border or '(none)'}.",
            f"- Missing OECD cross-country: {missing_oecd or '(none)'}.",
            "",
            "## Method",
            "",
            "Pre-registered specification (50-state panel, 1990-2022, "
            "excluding 2020-2021 COVID labour-market shock):",
            "",
            "    Step 1: bite_ratio_{s,t} = state_min_wage_{s,t} /",
            "                                state_median_hourly_wage_{s,t}",
            "    Step 2: assign each (state, treatment-cohort) to",
            "            HIGH-BITE if max(bite_ratio) >= 0.55",
            "            LOW-BITE  if max(bite_ratio) <  0.45",
            "    Step 3: Callaway-Sant'Anna 2021 staggered DiD on teen E/P,",
            "            state and year FE, never- and late-treated controls,",
            "            state-clustered SE.",
            "    Step 4: Differential = ATT_high - ATT_low (percentage points).",
            "",
            "Falsification thresholds (dispositive):",
            f"  PRIMARY: differential ≤ {SUPPORTED_DIFFERENTIAL:+.3f} pp at "
            "p<0.10 → SUPPORTED.",
            f"  REFUTED if differential ≥ 0 at p<0.10 (Chicago direction wrong).",
            f"  REFUTED if |differential| < {REFUTED_NEAR_ZERO_BAND:+.3f} pp "
            "with sufficient power (effect too small to support the claim).",
            "",
            "Informative (not gating):",
            f"  Border-county DLR elasticity on QCEW NAICS-722 employment "
            f"for state-pairs whose bite ratios diverge by ≥ "
            f"{SECONDARY_BORDER_CUTOFF:.2f}.",
            f"  OECD MWUSD bite-ratio panel: low-skill unemployment "
            "rate ~ bite-ratio + country FE + year FE on the 15-country "
            "spec sample.",
            "",
            "## Data",
            "",
            "Required (per spec):",
            "",
        ]
        for pub, series in ALL_REQUIRED:
            status = "available" if f"{pub}:{series}" in available else "**missing**"
            card.append(f"- `{pub}:{series}` — {status}")
        card.append("")
        card.append(
            "Promotion verdict: inconclusive (method-validity gate fails on "
            "data availability — state-level BLS series and OECD MWUSD "
            "bite-ratio are not on disk; the BLS fetcher currently exposes "
            "only national LNS/CES/CUUR series, and the OECD harvester does "
            "not cover the MWUSD dataflow). Per HANDOFF_TO_RUN_AGENT.md a "
            "data gap is NOT a refutation — the scoreboard treats this as "
            "neutral. Re-run when (a) the BLS state fan-out lands "
            "(LAU state teen E/P panel, OES state median hourly wage), "
            "(b) the USDOL state-minimum-wage history is dropped, and "
            "(c) the OECD MWUSD bite-ratio dataflow is harvested."
        )
        (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

        print(f"verdict: {verdict}")
        return

    # ---------- (Future v2) — full stratified Callaway-Sant'Anna pipeline ----
    # Reserved: when the BLS state fan-out + USDOL state-min-wage + BLS OES
    # state-median-hourly-wage land, this branch should:
    #   1) Build long panel (state_fips, year, teen_ep, state_min_wage,
    #      state_median_hourly_wage, controls).
    #   2) Compute bite_ratio = state_min_wage / state_median_hourly_wage.
    #   3) Apply spec.sample.exclusion_rules (drop COVID 2020-2021,
    #      winsorise at 1/99).
    #   4) Assign cohorts: HIGH-BITE if peak bite >= 0.55, LOW-BITE if < 0.45.
    #   5) Run Callaway-Sant'Anna 2021 staggered-DiD via _lib_did_cs on
    #      each cohort independently.
    #   6) Compute differential = ATT_high - ATT_low and clustered SE
    #      via the delta method (or 200-iteration block bootstrap on states).
    #   7) If QCEW + USDOL state-min available, run Dube-Lester-Reich
    #      contiguous-county-pair OLS for border-pair informative.
    #   8) If OECD MWUSD + DSD_LMS available, run cross-country panel
    #      regression with country and year FE for OECD informative.
    #   9) Apply dispositive thresholds and emit verdict.
    raise NotImplementedError(
        "Primary regression branch not implemented; v1 is data-gated. "
        "When BLS state fan-out (LAU teen E/P + OES state median hourly "
        "wage), USDOL state minimum-wage history, and OECD MWUSD bite-ratio "
        "are on disk, extend this script with the stratified "
        "Callaway-Sant'Anna pipeline and emit the same six artifacts."
    )


if __name__ == "__main__":
    main()
