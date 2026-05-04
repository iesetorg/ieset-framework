#!/usr/bin/env python3
"""
Replication — Australia's tobacco excise vs harm-reduction comparators.

Spec: hypotheses/fiscal/australia_tobacco_excise_punitive_vs_harm_reduction_comparators.yaml v1
Position-claim: social_democratic #0 (school predicts: supported)
                classical_liberal #0 inverted (school predicts: supported)

PRIMARY (dispositive):
  Australia's absolute decline in adult male smoking prevalence 2000→2022 (pp)
  must be STRICTLY GREATER than the unweighted mean absolute decline of
  NZL + GBR + SWE over the same period.

  SUPPORTED if AUS_decline > comparator_mean_decline
  REFUTED   if AUS_decline <= comparator_mean_decline
  PARTIAL   if equal within 0.5pp

INFORMATIVE:
  - Female smoking decline reported for symmetry check.
  - Relative-% decline reported.
  - Year-by-year trajectory charted.

METHOD_VALID:
  WDI SH.PRV.SMOK.MA must have >=5 non-null observations for each country
  in 2000-2022.
"""

import json
import sys
from pathlib import Path
import pandas as pd
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HID = "australia_tobacco_excise_punitive_vs_harm_reduction_comparators"
REPO = Path(__file__).resolve().parents[3]
RUN_DIR = REPO / "engine" / "runs" / HID
VINTAGES = REPO / "data" / "vintages" / "world_bank_wdi"

COUNTRIES = {
    "AUS": "Australia",
    "NZL": "New Zealand",
    "GBR": "United Kingdom",
    "SWE": "Sweden",
}
COMPARATORS = ["NZL", "GBR", "SWE"]
WINDOW = (2000, 2022)

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def latest_vintage(series: str) -> Path:
    """Return the most recent parquet for a WDI series."""
    candidates = list(VINTAGES.glob(f"{series}@*.parquet"))
    if not candidates:
        raise FileNotFoundError(f"No vintage found for {series}")
    return sorted(candidates, key=lambda p: p.name.split("@")[-1].replace(".parquet", ""))[-1]


def load_series(series: str) -> pd.DataFrame:
    """Load a WDI series and return country/year/value."""
    path = latest_vintage(series)
    df = pd.read_parquet(path)
    return df[["country_iso3", "year", "value"]].copy()


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------

def main() -> dict:
    # Load male and female smoking prevalence
    male_df = load_series("SH.PRV.SMOK.MA")
    female_df = load_series("SH.PRV.SMOK.FE")

    # Filter to window and countries
    male_df = male_df[
        (male_df["year"] >= WINDOW[0]) &
        (male_df["year"] <= WINDOW[1]) &
        (male_df["country_iso3"].isin(COUNTRIES.keys()))
    ].dropna(subset=["value"])

    female_df = female_df[
        (female_df["year"] >= WINDOW[0]) &
        (female_df["year"] <= WINDOW[1]) &
        (female_df["country_iso3"].isin(COUNTRIES.keys()))
    ].dropna(subset=["value"])

    # METHOD_VALID gate: >=5 observations per country
    male_counts = male_df.groupby("country_iso3").size()
    for iso in COUNTRIES:
        if male_counts.get(iso, 0) < 5:
            return {
                "verdict": f"INCONCLUSIVE — METHOD_VALID failure: {iso} has only {male_counts.get(iso, 0)} non-null male smoking observations (need >=5).",
                "verdict_label": "INCONCLUSIVE_DATA_PENDING",
                "verdict_reason": f"Insufficient data for {iso}",
                "hypothesis_id": HID,
                "template": "descriptive_cross_section",
                "estimate": {"error": f"METHOD_VALID: {iso} insufficient observations"},
            }

    # Compute absolute declines: first available value minus last available value
    def get_decline(df: pd.DataFrame, iso: str):
        sub = df[df["country_iso3"] == iso].sort_values("year")
        if sub.empty:
            return None
        first = sub.iloc[0]
        last = sub.iloc[-1]
        return round(first["value"] - last["value"], 2)

    def get_first_last(df: pd.DataFrame, iso: str):
        sub = df[df["country_iso3"] == iso].sort_values("year")
        if sub.empty:
            return None, None, None, None
        first = sub.iloc[0]
        last = sub.iloc[-1]
        return first["year"], first["value"], last["year"], last["value"]

    results = {}
    for iso, name in COUNTRIES.items():
        fy, fv, ly, lv = get_first_last(male_df, iso)
        decline = get_decline(male_df, iso)
        _, ffv, _, flv = get_first_last(female_df, iso)
        f_decline = get_decline(female_df, iso) if ffv is not None else None
        results[iso] = {
            "name": name,
            "first_year": int(fy) if fy else None,
            "first_value": round(fv, 2) if fv else None,
            "last_year": int(ly) if ly else None,
            "last_value": round(lv, 2) if lv else None,
            "absolute_decline_pp": decline,
            "relative_decline_pct": round(decline / fv * 100, 1) if decline and fv else None,
            "female_first": round(ffv, 2) if ffv else None,
            "female_last": round(flv, 2) if flv else None,
            "female_decline_pp": f_decline,
        }

    aus_decline = results["AUS"]["absolute_decline_pp"]
    comp_declines = [results[c]["absolute_decline_pp"] for c in COMPARATORS]
    comp_mean = round(sum(comp_declines) / len(comp_declines), 2) if all(d is not None for d in comp_declines) else None

    # Primary dispositive test
    if comp_mean is None:
        verdict = "INCONCLUSIVE — missing comparator data"
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
    elif aus_decline > comp_mean + 0.5:
        verdict = f"SUPPORTED — AUS decline {aus_decline}pp > comparator mean {comp_mean}pp (threshold: >{comp_mean + 0.5}pp)"
        verdict_label = "SUPPORTED"
    elif aus_decline < comp_mean - 0.5:
        verdict = f"REFUTED — AUS decline {aus_decline}pp < comparator mean {comp_mean}pp (threshold: <{comp_mean - 0.5}pp)"
        verdict_label = "REFUTED"
    else:
        verdict = f"PARTIAL — AUS decline {aus_decline}pp within 0.5pp of comparator mean {comp_mean}pp"
        verdict_label = "PARTIAL"

    # Build chart data
    chart_data = {
        "kind": "result",
        "title": "Smoking prevalence decline 2000-2022",
        "x_label": "Country",
        "y_label": "Absolute decline (percentage points)",
        "series": [
            {
                "name": "Male smoking decline (pp)",
                "data": [
                    {"x": results[iso]["name"], "y": results[iso]["absolute_decline_pp"]}
                    for iso in COUNTRIES
                ],
            }
        ],
        "annotations": [
            {"text": f"Comparator mean: {comp_mean}pp", "x": "United Kingdom", "y": comp_mean}
        ] if comp_mean else [],
    }

    # Build coefficients table
    coeff_rows = []
    for iso in COUNTRIES:
        r = results[iso]
        coeff_rows.append({
            "country": iso,
            "country_name": r["name"],
            "first_year": r["first_year"],
            "first_value": r["first_value"],
            "last_year": r["last_year"],
            "last_value": r["last_value"],
            "absolute_decline_pp": r["absolute_decline_pp"],
            "relative_decline_pct": r["relative_decline_pct"],
            "female_decline_pp": r["female_decline_pp"],
        })
    coeff_df = pd.DataFrame(coeff_rows)

    # Build diagnostics
    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_reason": f"Primary: AUS decline {aus_decline}pp vs comparator mean {comp_mean}pp",
        "hypothesis_id": HID,
        "template": "descriptive_cross_section",
        "claim_direction_inferred": "-",
        "falsification_rule_text": "AUS decline > comparator mean + 0.5pp -> SUPPORTED; AUS decline < comparator mean - 0.5pp -> REFUTED; otherwise PARTIAL",
        "estimate": {
            "aus_decline_pp": aus_decline,
            "comparator_mean_pp": comp_mean,
            "comparator_individual_pp": {c: results[c]["absolute_decline_pp"] for c in COMPARATORS},
            "female_declines_pp": {iso: results[iso]["female_decline_pp"] for iso in COUNTRIES},
            "relative_declines_pct": {iso: results[iso]["relative_decline_pct"] for iso in COUNTRIES},
        },
        "data_status": {
            "variables_loaded": [
                {"role": "outcome", "name": "male_smoking_prevalence", "source": "world_bank_wdi:SH.PRV.SMOK.MA", "n_rows": len(male_df)},
                {"role": "outcome", "name": "female_smoking_prevalence", "source": "world_bank_wdi:SH.PRV.SMOK.FE", "n_rows": len(female_df)},
            ],
            "variables_missing": [],
        },
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "runner": "engine/runs/australia_tobacco_excise_punitive_vs_harm_reduction_comparators/replication.py",
    }

    # Build result card
    result_card = f"""# Result — {HID}

## Verdict

**{verdict_label}** — {verdict}

## Summary

Australia's adult male smoking prevalence declined from {results['AUS']['first_value']}% ({results['AUS']['first_year']}) to {results['AUS']['last_value']}% ({results['AUS']['last_year']}), an absolute decline of **{aus_decline} percentage points** ({results['AUS']['relative_decline_pct']}% relative).

Comparator countries (harm-reduction approach):
- **New Zealand**: {results['NZL']['absolute_decline_pp']}pp decline ({results['NZL']['first_value']}% -> {results['NZL']['last_value']}%)
- **United Kingdom**: {results['GBR']['absolute_decline_pp']}pp decline ({results['GBR']['first_value']}% -> {results['GBR']['last_value']}%)
- **Sweden**: {results['SWE']['absolute_decline_pp']}pp decline ({results['SWE']['first_value']}% -> {results['SWE']['last_value']}%)

**Comparator mean decline: {comp_mean}pp**

## Female smoking (informative)

- Australia: {results['AUS']['female_decline_pp']}pp decline
- New Zealand: {results['NZL']['female_decline_pp']}pp decline
- United Kingdom: {results['GBR']['female_decline_pp']}pp decline
- Sweden: {results['SWE']['female_decline_pp']}pp decline

## Method

Simple comparator calculation using WDI smoking-prevalence series (SH.PRV.SMOK.MA / .FE). No regression — the dispositive test is a direct comparison of absolute declines across four countries over 2000-2022.

## Data

- WDI male smoking prevalence: `{latest_vintage('SH.PRV.SMOK.MA')}`
- WDI female smoking prevalence: `{latest_vintage('SH.PRV.SMOK.FE')}`
"""

    # Write artifacts
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    with open(RUN_DIR / "diagnostics.json", "w") as f:
        json.dump(diagnostics, f, indent=2)

    with open(RUN_DIR / "chart_data.json", "w") as f:
        json.dump(chart_data, f, indent=2)

    coeff_df.to_parquet(RUN_DIR / "coefficients.parquet", index=False)

    with open(RUN_DIR / "result_card.md", "w") as f:
        f.write(result_card)

    # Manifest
    manifest = {
        "hypothesis_id": HID,
        "run_utc": diagnostics["run_utc"],
        "vintages": [
            {"publisher": "world_bank_wdi", "series": "SH.PRV.SMOK.MA", "path": str(latest_vintage("SH.PRV.SMOK.MA").relative_to(REPO))},
            {"publisher": "world_bank_wdi", "series": "SH.PRV.SMOK.FE", "path": str(latest_vintage("SH.PRV.SMOK.FE").relative_to(REPO))},
        ],
    }
    with open(RUN_DIR / "manifest.yaml", "w") as f:
        yaml.dump(manifest, f)

    print(verdict)
    return diagnostics


if __name__ == "__main__":
    diag = main()
    sys.exit(0 if diag["verdict_label"] in ("SUPPORTED", "REFUTED", "PARTIAL") else 1)
