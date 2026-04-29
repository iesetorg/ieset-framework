#!/usr/bin/env python3
"""Replication — US state minimum-wage employment effects, 1990-2024.

Spec: hypotheses/labour/minimum_wage_employment_effect_us_states.yaml v1
Steelman: hypotheses/steelman/minimum_wage_employment_effect_us_states.md
Position-claim: democratic_socialist #4 (school predicts: supported)

PRIMARY (dispositive):
  Callaway-Sant'Anna staggered DiD elasticity of teen employment-to-population
  ratio (BLS LAU state) with respect to the log state minimum wage (USDOL state
  history) over the 1990-2024 panel must fall in [-0.15, +0.05] with the 95%
  confidence interval crossing zero — consistent with the post-1990 border-
  discontinuity literature (Card-Krueger 1994 / Dube-Lester-Reich 2010 /
  Cengiz-Dube-Lindner-Zipperer 2019).

  REFUTED if the elasticity is significantly < -0.15 (Neumark-Wascher
  nationwide-panel-style finding) OR significantly > +0.10 (claim is
  "close to zero", not "positive").

  SECONDARY (also dispositive per spec.falsification.threshold):
  Border-pair Dube-Lester-Reich design on QCEW accommodation-and-food-services
  county employment must produce an elasticity in [-0.20, +0.05].

METHOD_VALID gates:
  - State-level BLS LAU teen employment-to-population series available
    for at least 40 of 50 states with >=20 years of coverage.
  - USDOL state minimum-wage history file available with at least
    one binding state-level change distinct from the federal floor
    in at least 30 states over the period.
  - QCEW NAICS-722 (accommodation/food services) county-level
    employment available for the border-pair specification.

If any of those required state-level series is not in the on-disk
vintages, this replication emits `inconclusive — data gap` with a full
listing of which publisher:series are missing, per HANDOFF_TO_RUN_AGENT.md
("Don't fabricate data. If the publisher's vintage doesn't contain a
series the spec needs, emit `inconclusive (data gap on
<publisher>:<series>)` and stop.").

The verdict word is the first token in `diagnostics.verdict`, parsed
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
HID = "minimum_wage_employment_effect_us_states"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1990, 2024)
EXCLUDE_YEARS = {2020}  # COVID — per sample.exclusion_rules

# Required series the spec calls for. Tuples of (publisher, series, role).
# Spec.variables.outcome / treatment / controls direct these.
#
# State-level BLS series follow the SM/LAU naming conventions. The
# concrete IDs would be:
#   - LAUST<STATE_FIPS>0000000005 — state employment level (LAU)
#   - LAUST<STATE_FIPS>0000000006 — state employment-pop ratio
#   - LAUST<STATE_FIPS>0000000016A — teen E/P (CPS state tabulation)
#   - SMS<STATE_FIPS>0000000000001 — state CES total nonfarm
#   - ENU<STATE_FIPS>10510         — QCEW NAICS-722 county employment
# None of those are on disk; the BLS fetcher currently pulls only
# national LNS/CES/CUUR ids. The state fan-out is open backlog work.
REQUIRED_OUTCOME = [
    # Primary: state-level teen E/P. v1 expects an aggregate "all states"
    # parquet keyed (state_fips, year, value).
    ("bls", "LAU_state_teen_employment_population_ratio_panel"),
    # Secondary: state-level accommodation/food-services employment.
    ("bls", "CES_state_NAICS722_employment_panel"),
]
REQUIRED_TREATMENT = [
    # USDOL state minimum-wage history (statutory state floor by year).
    ("usdol", "state_minimum_wage_history"),
]
REQUIRED_BORDER_PAIR = [
    # QCEW county-level NAICS-722 employment for the Dube-Lester-Reich
    # border-pair robustness specification.
    ("bls", "QCEW_county_NAICS722_employment_panel"),
    # Vaghul-Zipperer 2016 effective minimum-wage by county (manual drop).
    ("manual", "vaghul_zipperer_county_minimum_wage"),
]
REQUIRED_CONTROLS = [
    # State unemployment rate (LAU adult).
    ("bls", "LAU_state_unemployment_rate_panel"),
    # State GDP — currently fetcher-pending (FRED state series).
    ("fred", "state_real_gdp_panel"),
]

ALL_REQUIRED = (
    REQUIRED_OUTCOME
    + REQUIRED_TREATMENT
    + REQUIRED_BORDER_PAIR
    + REQUIRED_CONTROLS
)

# Falsification thresholds (from spec.falsification.threshold)
PRIMARY_ELASTICITY_BAND = (-0.15, 0.05)
PRIMARY_REFUTE_BELOW = -0.15
PRIMARY_REFUTE_ABOVE = 0.10
BORDER_PAIR_ELASTICITY_BAND = (-0.20, 0.05)

MIN_STATES_WITH_DATA = 40
MIN_YEARS_PER_STATE = 20
MIN_STATES_WITH_BINDING_CHANGE = 30


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
    missing: list[str] = []

    for pub, series in ALL_REQUIRED:
        p = latest(pub, series)
        key = f"{pub}:{series}"
        if p is None:
            missing.append(key)
        else:
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
    missing_controls = [
        f"{p}:{s}" for p, s in REQUIRED_CONTROLS if f"{p}:{s}" not in available
    ]

    # The Callaway-Sant'Anna primary needs at least the teen E/P state
    # panel AND the state minimum-wage history. Without either we cannot
    # estimate any elasticity at all. The border-pair secondary needs
    # the QCEW county panel and the Vaghul-Zipperer county minimum.
    can_run_primary = (
        f"bls:LAU_state_teen_employment_population_ratio_panel" in available
        and f"usdol:state_minimum_wage_history" in available
    )
    can_run_border = (
        f"bls:QCEW_county_NAICS722_employment_panel" in available
        and f"manual:vaghul_zipperer_county_minimum_wage" in available
    )

    # ---------- METHOD_VALID gate: data gap → inconclusive ----------
    if not can_run_primary:
        verdict = (
            "inconclusive — data gap on "
            + ", ".join(missing_outcome + missing_treatment)
            + ". The spec's primary Callaway-Sant'Anna staggered DiD on the "
            "1990-2024 US-state panel cannot be estimated without the "
            "state-level BLS LAU teen employment-to-population series and "
            "the USDOL state minimum-wage history. On-disk BLS vintages "
            "currently include only national-level series (LNS*, CES05*, "
            "CUUR*); the state fan-out (SMS*, LAUST*, ENU*-county QCEW) "
            "and the USDOL state-history table have not been fetched. "
            "No coefficients computed."
        )

        diagnostics = {
            "verdict": verdict,
            "all_pass": False,
            "method_valid": False,
            "data_gap": True,
            "can_run_primary": can_run_primary,
            "can_run_border_pair": can_run_border,
            "missing_outcome_series": missing_outcome,
            "missing_treatment_series": missing_treatment,
            "missing_border_pair_series": missing_border,
            "missing_control_series": missing_controls,
            "available_series": sorted(available.keys()),
            "n_required": len(ALL_REQUIRED),
            "n_available": len(available),
            "min_states_required": MIN_STATES_WITH_DATA,
            "min_years_per_state": MIN_YEARS_PER_STATE,
            "primary_elasticity_band": list(PRIMARY_ELASTICITY_BAND),
            "primary_refute_below": PRIMARY_REFUTE_BELOW,
            "primary_refute_above": PRIMARY_REFUTE_ABOVE,
            "border_pair_elasticity_band": list(BORDER_PAIR_ELASTICITY_BAND),
            "cs_att_elasticity": None,
            "cs_att_se": None,
            "cs_att_ci95": None,
            "border_pair_elasticity": None,
            "border_pair_se": None,
            "border_pair_ci95": None,
            "n_states": None,
            "n_state_years": None,
            "period": list(PERIOD),
            "exclude_years": sorted(EXCLUDE_YEARS),
        }
        (OUT_DIR / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2) + "\n"
        )

        # Empty coefficients table — schema-compliant placeholder.
        pd.DataFrame(
            [
                {"spec": "primary_cs_att", "term": "elasticity_teen_ep_minwage", "estimate": np.nan},
                {"spec": "primary_cs_att", "term": "se", "estimate": np.nan},
                {"spec": "border_pair_dlr", "term": "elasticity_naics722_minwage", "estimate": np.nan},
                {"spec": "border_pair_dlr", "term": "se", "estimate": np.nan},
            ]
        ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "US state minimum-wage employment effects — DATA GAP",
            "subtitle": (
                f"{len(missing_outcome)+len(missing_treatment)} of "
                f"{len(REQUIRED_OUTCOME)+len(REQUIRED_TREATMENT)} required "
                "primary outcome/treatment series not yet fetched. "
                "Callaway-Sant'Anna DiD cannot be estimated."
            ),
            "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {
                "label": "teen E/P elasticity w.r.t. log state min wage",
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
                            + missing_controls
                        )
                    ),
                },
                {
                    "type": "note",
                    "label": (
                        "Pre-registered band for SUPPORTED: elasticity in "
                        f"[{PRIMARY_ELASTICITY_BAND[0]:+.2f}, "
                        f"{PRIMARY_ELASTICITY_BAND[1]:+.2f}]. "
                        f"REFUTED if < {PRIMARY_REFUTE_BELOW:+.2f} or "
                        f"> {PRIMARY_REFUTE_ABOVE:+.2f}."
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
        for k in missing_outcome + missing_treatment + missing_border + missing_controls:
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
            "# US state minimum-wage employment effects, 1990-2024",
            "",
            f"**Verdict:** {verdict}",
            "",
            "## Summary",
            "",
            "- The hypothesis tests the post-1990 Card-Krueger / "
            "Dube-Lester-Reich consensus that state-level minimum-wage "
            "elasticities are small (in the [-0.15, +0.05] band) against "
            "the Neumark-Wascher claim of elasticities < -0.2.",
            "- Primary statistic: Callaway-Sant'Anna staggered-DiD "
            "elasticity of teen employment-to-population ratio with respect "
            "to log state minimum wage on the 1990-2024 US-state panel.",
            "- Secondary: Dube-Lester-Reich contiguous-county-pair "
            "elasticity on QCEW NAICS-722 (accommodation/food services) "
            "county employment.",
            f"- Required series: {len(REQUIRED_OUTCOME)} outcome, "
            f"{len(REQUIRED_TREATMENT)} treatment, "
            f"{len(REQUIRED_BORDER_PAIR)} border-pair, "
            f"{len(REQUIRED_CONTROLS)} controls "
            f"= {len(ALL_REQUIRED)} total.",
            f"- Found on-disk: {len(available)} of {len(ALL_REQUIRED)}.",
            f"- Missing primary outcome: {missing_outcome or '(none)'}.",
            f"- Missing treatment: {missing_treatment or '(none)'}.",
            f"- Missing border-pair: {missing_border or '(none)'}.",
            f"- Missing controls: {missing_controls or '(none)'}.",
            "",
            "## Method",
            "",
            "Pre-registered specification (50-state panel, 1990-2024, "
            "excluding 2020 COVID and federal-floor-binding state-years):",
            "",
            "    log(teen_E/P)_{s,t} = beta * log(min_wage)_{s,t}",
            "                        + alpha_s + tau_t + X_{s,t}'gamma + e",
            "",
            "with state and year fixed effects, Callaway-Sant'Anna 2021 "
            "estimator using never- and late-treated states as controls. "
            "Standard errors clustered by state. Border-pair robustness uses "
            "Dube-Lester-Reich 2010 contiguous-county-pair fixed effects on "
            "QCEW NAICS-722 employment.",
            "",
            "Falsification thresholds (dispositive):",
            f"  PRIMARY: CS_ATT_elasticity in "
            f"[{PRIMARY_ELASTICITY_BAND[0]:+.2f}, {PRIMARY_ELASTICITY_BAND[1]:+.2f}] "
            "with 95% CI crossing zero → SUPPORTED.",
            f"  CS_ATT_elasticity < {PRIMARY_REFUTE_BELOW:+.2f} significant at "
            f"5% → REFUTED (Neumark-Wascher direction).",
            f"  CS_ATT_elasticity > {PRIMARY_REFUTE_ABOVE:+.2f} significant at "
            f"5% → REFUTED (positive-effect direction).",
            f"  SECONDARY: border_pair_elasticity in "
            f"[{BORDER_PAIR_ELASTICITY_BAND[0]:+.2f}, "
            f"{BORDER_PAIR_ELASTICITY_BAND[1]:+.2f}] required for full "
            "SUPPORTED verdict.",
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
            "data availability — state-level BLS series are not on disk; "
            "the BLS fetcher currently exposes only national LNS/CES/CUUR "
            "series). Per HANDOFF_TO_RUN_AGENT.md a data gap is NOT a "
            "refutation — the scoreboard treats this as neutral. Re-run "
            "when the BLS state fan-out (LAU state teen E/P, SMS state CES, "
            "ENU county QCEW) and USDOL state minimum-wage history fetchers "
            "are wired and the Vaghul-Zipperer county-minimum dataset is "
            "dropped into data/manual/."
        )
        (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

        print(f"verdict: {verdict}")
        return

    # ---------- (Future v2) — full Callaway-Sant'Anna pipeline ----------
    # Reserved: when state-level BLS LAU + USDOL state-min-wage history land,
    # this branch should:
    #   1) Build long panel (state_fips, year, teen_ep, state_min_wage,
    #      controls).
    #   2) Apply spec.sample.exclusion_rules (drop federal-hike years,
    #      drop 2020).
    #   3) Run Callaway-Sant'Anna 2021 staggered-DiD via _lib_did_cs.
    #   4) Compute elasticity = beta_log_minwage and clustered-by-state SE.
    #   5) If QCEW NAICS-722 + Vaghul-Zipperer county-minwage are available,
    #      run Dube-Lester-Reich contiguous-county-pair OLS for the
    #      secondary specification.
    #   6) Apply the dispositive thresholds above and emit verdict.
    raise NotImplementedError(
        "Primary regression branch not implemented; v1 is data-gated. "
        "When the BLS state fan-out (LAU state teen E/P, SMS state CES) "
        "and USDOL state minimum-wage history fetchers land, extend this "
        "script with the Callaway-Sant'Anna staggered-DiD pipeline and the "
        "Dube-Lester-Reich border-pair robustness, writing the same four "
        "artifacts."
    )


if __name__ == "__main__":
    main()
