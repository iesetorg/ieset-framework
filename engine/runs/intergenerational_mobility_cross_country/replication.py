#!/usr/bin/env python3
"""Replication — Cross-country intergenerational mobility decomposition.

Spec: hypotheses/distribution/intergenerational_mobility_cross_country.yaml v1
Steelman: hypotheses/steelman/intergenerational_mobility_cross_country.md

PRIMARY (dispositive): the cross-country regression
    mobility = b0 + b1*edu_inequality + b2*residential_segregation
             + b3*housing_affordability + b4*controls + epsilon
must be ESTIMABLE (i.e. all four left-hand-side / institutional-channel
series available for at least 12 of the 20 OECD countries in the
sample) AND must yield:
    partial_R2_institutional_channels >= 0.40
    partial_R2_institutional_channels >  partial_R2_gini_alone
    leave-one-out: no single country flips the sign of any of b1, b2, b3.

If any of those LHS or institutional-channel series is not in the
on-disk vintages, this replication emits `inconclusive — data gap`
with a complete listing of which publisher:series are missing, per
HANDOFF_TO_RUN_AGENT.md ("Don't fabricate data. If the publisher's
vintage doesn't contain a series the spec needs, emit `inconclusive
(data gap on <publisher>:<series>)` and stop.").

Method-validity gates (METHOD_VALID):
  - n >= 12 of 20 OECD-country panel with non-null mobility AND
    non-null institutional channels.
  - leave-one-out stability across all 20 countries.

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
HID = "intergenerational_mobility_cross_country"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
COUNTRIES = [
    "USA", "GBR", "CAN", "AUS", "FRA", "DEU", "ITA", "ESP", "NLD", "SWE",
    "NOR", "DNK", "FIN", "CHE", "BEL", "AUT", "IRL", "NZL", "JPN", "KOR",
]
PERIOD = (1990, 2020)

# Required series the spec calls for. (publisher, series).
# The primary regression needs at least one true mobility outcome and all
# three institutional channels. Controls are reported as gaps but are not
# the binding blocker in the current local vintage set.
REQUIRED_OUTCOME = [
    ("owid", "intergenerational-earnings-elasticity"),
    ("owid", "share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile"),
]
REQUIRED_CHANNELS = [
    # OECD Education-at-a-Glance subnational per-pupil spending dispersion
    ("oecd", "OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0"),
    # OECD Affordable Housing Database — income segregation index
    ("oecd", "OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0"),
    # BIS price-to-income (housing affordability)
    ("bis", "WS_SPP"),
]
REQUIRED_CONTROLS = [
    ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
    ("world_bank_wdi", "SI.POV.GINI"),
    ("wgi", "GOV_WGI_GE.EST"),
    ("world_bank_wdi", "SE.TER.CUAT.BA.ZS"),
]

# Falsification thresholds (from spec.falsification.threshold)
PARTIAL_R2_INSTITUTIONAL_THRESHOLD = 0.40
MIN_COUNTRIES_WITH_DATA = 12  # of 20


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    """Return latest vintage parquet for (pub, series) or None if absent.

    Per spec the OECD subnational dataflows use comma/at-separated URNs;
    on-disk files use underscore-flattened names. Try both forms.
    """
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    candidates = []
    for s in {series, series.replace(",", "_").replace("@", "_")}:
        candidates.extend(sorted(d.glob(f"{s}@*.parquet"), key=lambda p: p.stat().st_mtime))
    return candidates[-1] if candidates else None


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

    # ---------- Vintage discovery ----------
    available: dict[str, dict] = {}
    missing: list[str] = []

    for pub, series in REQUIRED_OUTCOME + REQUIRED_CHANNELS + REQUIRED_CONTROLS:
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

    # ---------- Decide if we can run the regression ----------
    missing_outcome = [f"{p}:{s}" for p, s in REQUIRED_OUTCOME if f"{p}:{s}" not in available]
    missing_channels = [f"{p}:{s}" for p, s in REQUIRED_CHANNELS if f"{p}:{s}" not in available]
    missing_controls = [f"{p}:{s}" for p, s in REQUIRED_CONTROLS if f"{p}:{s}" not in available]

    # The regression needs at least one mobility outcome and all three channels.
    can_run = (
        len(missing_outcome) < len(REQUIRED_OUTCOME)
        and len(missing_channels) == 0
    )

    # ---------- METHOD_VALID gate: not enough data -> inconclusive ----------
    if not can_run:
        binding_missing = []
        if len(missing_outcome) == len(REQUIRED_OUTCOME):
            binding_missing.extend(missing_outcome)
        binding_missing.extend(missing_channels)
        if not binding_missing:
            binding_missing = missing_outcome + missing_channels
        available_outcomes = [
            f"{p}:{s}" for p, s in REQUIRED_OUTCOME if f"{p}:{s}" in available
        ]
        verdict_reason = (
            "data gap on "
            + ", ".join(binding_missing)
            + ". The spec's primary regression cannot be estimated without "
            "a mobility outcome series and all three institutional-channel "
            "series. The v1 notes explicitly data-gate this test on an OWID "
            "or OECD intergenerational-mobility mirror, OECD Education-at-a-"
            "Glance subnational spending dispersion, and OECD Affordable "
            "Housing Database income-segregation indices. No coefficients "
            "computed."
        )
        verdict = (
            "inconclusive - " + verdict_reason
        )
        data_repair_note = (
            "2026-05-04 source repair fetched the live OWID Corak/Chen-"
            "Forster-Llena-Nozal intergenerational earnings-elasticity mirror "
            f"({', '.join(available_outcomes) or 'no mobility outcome available'}). "
            "The primary regression still remains data-gated because the OECD "
            "subnational education-spending dispersion and OECD Affordable "
            "Housing income-segregation channels are not present locally. The "
            "bottom-to-top-quintile mobility outcome is also still unavailable "
            "as a robustness outcome. WDI GDP per capita or poverty-headcount "
            "series are not valid substitutes for the preregistered mobility "
            "outcomes or institutional channels."
        )

        diagnostics = {
            "verdict": verdict,
            "verdict_label": "INCONCLUSIVE_DATA_PENDING",
            "verdict_reason": verdict_reason,
            "all_pass": False,
            "method_valid": False,
            "data_gap": True,
            "data_repair_note": data_repair_note,
            "binding_missing_series": binding_missing,
            "missing_outcome_series": missing_outcome,
            "missing_channel_series": missing_channels,
            "missing_control_series": missing_controls,
            "available_series": sorted(available.keys()),
            "n_countries_in_sample": len(COUNTRIES),
            "min_countries_required": MIN_COUNTRIES_WITH_DATA,
            "partial_r2_institutional_channels": None,
            "partial_r2_gini_alone": None,
            "loo_robust": None,
            "primary_threshold_partial_r2": PARTIAL_R2_INSTITUTIONAL_THRESHOLD,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

        # Empty coefficients table — schema-compliant placeholder.
        pd.DataFrame(
            [
                {"spec": "primary", "term": "partial_r2_institutional_channels", "estimate": np.nan},
                {"spec": "primary", "term": "partial_r2_gini_alone",            "estimate": np.nan},
            ]
        ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

        # Chart data — show what the analysis WOULD look like by listing the
        # required-but-missing series. Render-friendly empty result.
        chart_data = {
            "kind": "result",
            "chart_id": f"{HID}/fig1",
            "title": "Intergenerational mobility cross-country — DATA GAP",
            "subtitle": (
                f"{len(missing_outcome)+len(missing_channels)} of "
                f"{len(REQUIRED_OUTCOME)+len(REQUIRED_CHANNELS)} required outcome/"
                f"channel series not yet fetched. Regression cannot be estimated."
            ),
            "type": "line",
            "x_axis": {"label": "Country", "type": "linear"},
            "y_axis": {"label": "intergenerational earnings elasticity (target)", "type": "linear"},
            "series": [],
            "annotations": [
                {
                    "type": "note",
                    "label": (
                        "Required-but-missing series: "
                        + "; ".join(binding_missing)
                    ),
                }
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
        (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

        manifest_lines = [
            f"hypothesis_id: {HID}",
            f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
            "status: data_gap_inconclusive",
            "missing_series:",
        ]
        for k in missing_outcome + missing_channels + missing_controls:
            manifest_lines.append(f"  - {k}")
        manifest_lines.append("vintages:")
        for k, v in available.items():
            manifest_lines.append(f"  '{k}':")
            manifest_lines.append(f"    publisher: {v['publisher']}")
            manifest_lines.append(f"    series: {v['series']}")
            manifest_lines.append(f"    vintage_file: {v['vintage_file']}")
            manifest_lines.append(f"    sha256: {v['sha256']}")
        (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

        card = [
            "# Intergenerational mobility — cross-country decomposition",
            "",
            f"**Verdict:** {verdict}",
            "",
            "## Summary",
            "",
            "- The hypothesis requires a cross-country regression of mobility on "
            "three institutional channels (education-spending inequality, residential "
            "segregation, housing affordability) plus controls.",
            "- The v1 spec flags the data gap explicitly: OECD SDD SOC "
            "mobility extension, Chetty opportunity-atlas (US-only), OECD "
            "Education-at-a-Glance subnational spending dispersion, and OECD "
            "Affordable Housing Database income-segregation support are not "
            "fully present in the local vintage set.",
            "- 2026-05-04 source repair: the live OWID elasticity chart was "
            "mapped and fetched as the preregistered earnings-elasticity "
            "outcome; the bottom-to-top-quintile robustness outcome and the "
            "two OECD institutional-channel vintages remain unavailable.",
            f"- Required series: {len(REQUIRED_OUTCOME)} outcome, "
            f"{len(REQUIRED_CHANNELS)} institutional-channel, "
            f"{len(REQUIRED_CONTROLS)} controls.",
            f"- Found on-disk: {len(available)} of "
            f"{len(REQUIRED_OUTCOME)+len(REQUIRED_CHANNELS)+len(REQUIRED_CONTROLS)}.",
            f"- Missing outcome: {missing_outcome or '(none)'}.",
            f"- Binding missing series: {binding_missing or '(none)'}.",
            f"- Missing channels: {missing_channels or '(none)'}.",
            f"- Missing controls: {missing_controls or '(none)'}.",
            "",
            "## Method",
            "",
            "Pre-registered specification (cross-section, n ~ 20):",
            "",
            "    mobility ~ edu_inequality + residential_segregation",
            "             + housing_affordability + log(GDP_pc) + Gini + gov_eff",
            "",
            "Primary statistic: partial R-squared of the three institutional "
            "channels relative to the controls-only model. Secondary: partial "
            "R-squared of Gini alone, leave-one-out sign stability of each "
            "channel coefficient.",
            "",
            "Falsification thresholds: partial_R2_channels >= 0.40 AND "
            "partial_R2_channels > partial_R2_gini_alone AND no single country "
            "flips a channel sign.",
            "",
            "## Data",
            "",
            "Required (per spec):",
            "",
        ]
        for pub, series in REQUIRED_OUTCOME + REQUIRED_CHANNELS + REQUIRED_CONTROLS:
            status = "available" if f"{pub}:{series}" in available else "**missing**"
            card.append(f"- `{pub}:{series}` — {status}")
        card.append("")
        card.append(
            "Promotion verdict: inconclusive (method-validity gate fails on data "
            "availability). Per HANDOFF_TO_RUN_AGENT.md a data gap is NOT a "
            "refutation - the scoreboard treats this as neutral. Re-run when "
            "the remaining OECD subnational fetchers are wired."
        )
        (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

        print(f"verdict: {verdict}")
        return

    # ---------- (Future v2) — full regression path ----------
    # Reserved: when the missing series are fetched, this branch should
    # implement the OLS + bootstrap + LOO + partial-R2 pipeline against
    # MIN_COUNTRIES_WITH_DATA-of-20 thresholds.
    raise NotImplementedError(
        "Regression branch not implemented; v1 is data-gated. When the "
        "OWID mobility mirror + OECD subnational fetchers land, extend "
        "this script with the cross-section regression and LOO loop, "
        "writing the same four artifacts."
    )


if __name__ == "__main__":
    main()
