#!/usr/bin/env python3
"""Fail-closed exact preflight for the frozen transition-privatisation panel.

All mass-privatisation dates precede the first WGI observations. Retaining the
registered institutional-quality control makes the two-way-FE treatment fully
absorbed. Preserve the old fallback and report the non-identification rather
than changing the frozen covariate set to manufacture a coefficient.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_panel_fe  # noqa: E402
import frozen_source_lock  # noqa: E402

HID = "privatisation_transition_tfp_panel"
RUN_DIR = ROOT / "engine" / "runs" / HID
RHS = [
    "mass_privatisation_indicator", "eu_accession_candidate",
    "log_initial_gdp_per_capita", "institutional_quality",
    "trade_openness", "inflation_rate", "investment_share_gdp",
]
UCDP_COUNTRY = {
    "Albania": "ALB", "Armenia": "ARM", "Azerbaijan": "AZE",
    "Bosnia-Herzegovina": "BIH", "Croatia": "HRV", "Georgia": "GEO",
    "Kyrgyzstan": "KGZ", "Moldova": "MDA", "North Macedonia": "MKD",
    "Poland": "POL", "Romania": "ROU", "Russia (Soviet Union)": "RUS",
    "Serbia (Yugoslavia)": "SRB", "Tajikistan": "TJK",
    "Ukraine": "UKR", "Uzbekistan": "UZB",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adoption_years(source: str) -> dict[str, int]:
    return {country: int(year) for country, year in re.findall(
        r"\b([A-Z]{3})\s+from\s+(19\d{2}|20\d{2})\b", source,
    )}


def high_intensity_conflict_years() -> tuple[set[tuple[str, int]], dict]:
    path = frozen_source_lock.pinned_vintage(HID, "ucdp", "ged")
    events = pd.read_parquet(path, columns=[
        "country", "year", "type_of_violence", "conflict_new_id", "best",
    ])
    events = events[events.type_of_violence.eq(1)].copy()
    events["country_iso3"] = events.country.map(UCDP_COUNTRY)
    events = events[events.country_iso3.notna() & events.year.between(1990, 2015)]
    conflict_years = events.groupby(
        ["country_iso3", "year", "conflict_new_id"], dropna=False,
    ).best.sum()
    # UCDP intensity level 2 is a state-based conflict with >=1,000
    # battle-related deaths in a calendar year.
    high = conflict_years[conflict_years >= 1000]
    pairs = {(country, int(year)) for country, year, _ in high.index}
    return pairs, {
        "vintage": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
        "definition": "state-based conflict-year with >=1000 GED best-estimate deaths",
        "excluded_country_years": sorted([{"country_iso3": c, "year": y} for c, y in pairs],
                                         key=lambda row: (row["country_iso3"], row["year"])),
    }


def prepare() -> tuple[pd.DataFrame, dict, dict, dict]:
    found = run_panel_fe.load_spec(HID)
    if not found:
        raise RuntimeError("frozen v1 spec missing")
    spec_path, spec = found
    if spec.get("version") != 1 or (spec.get("estimator") or {}).get("template") != "panel_fe":
        raise RuntimeError("frozen v1 estimator contract changed")
    treatment_items = spec["variables"]["treatment"]
    mass = adoption_years(treatment_items[0]["source"])
    eu = adoption_years(treatment_items[1]["source"])
    if len(mass) != 13 or len(eu) != 11 or max(mass.values()) != 1995:
        raise RuntimeError("declared mass-privatisation or EU adoption dates changed")
    panel, status = frozen_source_lock.checked_build_panel(HID, spec)
    panel = run_panel_fe.filter_sample(panel, spec).sort_values(["country_iso3", "year"]).copy()
    panel["mass_privatisation_indicator"] = [
        int(year >= mass.get(country, 9999))
        for country, year in zip(panel.country_iso3, panel.year)
    ]
    panel["eu_accession_candidate"] = [
        int(year >= eu.get(country, 9999))
        for country, year in zip(panel.country_iso3, panel.year)
    ]
    # The generic loader mapped log_diff_annual to log level. The registered
    # annual TFP-growth outcome is the consecutive-year log difference in pp.
    grouped = panel.groupby("country_iso3", sort=False)
    panel["tfp_growth_annual"] = grouped.tfp_growth_annual.diff().mul(100)
    panel.loc[grouped.year.diff().ne(1), "tfp_growth_annual"] = np.nan
    pre_exclusion = len(panel)
    high, conflict_meta = high_intensity_conflict_years()
    panel = panel[[
        (country, int(year)) not in high
        for country, year in zip(panel.country_iso3, panel.year)
    ]].copy()
    conflict_dropped = pre_exclusion - len(panel)
    outlier_dropped = int(panel.tfp_growth_annual.gt(25).sum())
    panel = panel[~panel.tfp_growth_annual.gt(25)].copy()
    panel = panel.sort_values(["country_iso3", "year"])
    if panel.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate country-year in frozen input panel")
    meta = {
        "spec_path": str(spec_path.relative_to(ROOT)), "spec_sha256": sha256_file(spec_path),
        "input_panel_sha256": hashlib.sha256(panel.to_csv(
            index=False, float_format="%.17g", na_rep="NA",
        ).encode()).hexdigest(),
        "ucdp": conflict_meta,
        "exclusions": {"high_intensity_conflict_country_years_dropped": conflict_dropped,
                       "tfp_growth_above_25_percent_dropped": outlier_dropped},
        "mass_adoption_dates": mass, "eu_candidacy_dates": eu,
        "prior_run": "historical/2026-05-03_rank_fallback",
        **frozen_source_lock.provenance(HID),
    }
    return panel, spec, status, meta


def build() -> tuple[dict, str]:
    panel, spec, status, meta = prepare()
    required = ["tfp_growth_annual", *RHS]
    complete = panel[["country_iso3", "year", *required]].dropna()
    variation = complete.groupby("country_iso3").mass_privatisation_indicator.nunique()
    varying_countries = sorted(variation[variation > 1].index.tolist())
    ex_russia = complete[complete.country_iso3.ne("RUS")]
    ex_russia_varying = sorted(ex_russia.groupby("country_iso3").mass_privatisation_indicator.nunique().pipe(
        lambda values: values[values > 1]
    ).index.tolist())
    if varying_countries:
        raise RuntimeError("frozen treatment is identified; extend runner to fit full specified test")
    reason = (
        "mass-privatisation adoption is constant within every complete-case country "
        "after the registered WGI control begins; country FE absorb the treatment"
    )
    preflight = {
        "declared_countries": len(spec["sample"]["countries"]),
        "complete_case_country_years": len(complete),
        "complete_case_countries": int(complete.country_iso3.nunique()),
        "complete_case_first_year": int(complete.year.min()) if len(complete) else None,
        "complete_case_last_year": int(complete.year.max()) if len(complete) else None,
        "within_country_mass_treatment_variation_countries": varying_countries,
        "ex_russia_treatment_variation_countries": ex_russia_varying,
        "wgi_first_observed_year": int(panel.loc[panel.institutional_quality.notna(), "year"].min()),
        "latest_mass_adoption_year": max(meta["mass_adoption_dates"].values()),
        "registered_effect_threshold_pp_per_year": 0.5,
        "eu_coefficient_comparison": "unassessable without identified mass-privatisation coefficient",
        "ex_russia_robustness": "unassessable: treatment also absorbed by country FE after excluding RUS",
    }
    diagnostics = {
        "hypothesis_id": HID, "template": "panel_fe",
        "verdict": f"INCONCLUSIVE_DATA_PENDING — {reason}",
        "verdict_label": "INCONCLUSIVE_DATA_PENDING", "verdict_reason": reason,
        "runner": "scripts/rerun_privatisation_transition_tfp_frozen.py",
        "falsification_rule_text": spec["falsification"]["rule"],
        "estimate": {"error": reason, "method": "not fitted: frozen treatment unidentifiable under two-way FE",
                     "n_obs": len(complete), "n_countries": int(complete.country_iso3.nunique())},
        "frozen_rule_components": {
            "mass_coefficient_positive_p_below_0_10_and_at_least_0_5pp": None,
            "mass_coefficient_larger_than_eu_candidate": None,
            "ex_russia_sign_robustness": None,
        },
        "preflight": preflight, "data_status": status, "provenance": meta,
    }
    card = "\n".join([
        f"# Result card — {HID}", "",
        f"**Verdict:** {diagnostics['verdict']}", "",
        "## Frozen exclusions and method", "",
        f"- Annual PWT log TFP growth in percentage points; {meta['exclusions']['high_intensity_conflict_country_years_dropped']} UCDP intensity-2 conflict country-years and {meta['exclusions']['tfp_growth_above_25_percent_dropped']} >25% growth outliers excluded.",
        f"- The registered institutional-quality control first appears in {preflight['wgi_first_observed_year']}; the latest mass-privatisation adoption is {preflight['latest_mass_adoption_year']}.",
        f"- {len(complete)} complete country-years in {preflight['complete_case_countries']} countries; zero countries have within-country treatment transitions. The ex-Russia sample also has zero.", "",
        "## Frozen 0.5 pp, EU, and ex-Russia rule", "",
        "All three components are unassessable because country fixed effects absorb the treatment. The 0.5 percentage-point threshold and EU-candidacy coefficient comparison cannot be graded. The previous rank-deficient near-zero fallback is retained in `historical/` but has no public evidence credit.", "",
        f"Spec SHA-256: `{meta['spec_sha256']}`", f"Input-panel SHA-256: `{meta['input_panel_sha256']}`", "",
    ])
    return diagnostics, card


def snapshot_prior() -> None:
    target = RUN_DIR / "historical" / "2026-05-03_rank_fallback"
    target.mkdir(parents=True, exist_ok=True)
    names = ("diagnostics.json", "result_card.md", "replication.py")
    for name in names:
        source, dest = RUN_DIR / name, target / name
        if source.exists() and not dest.exists():
            shutil.copy2(source, dest)
    manifest = target / "sha256.json"
    if not manifest.exists():
        manifest.write_text(json.dumps(
            {name: sha256_file(target / name) for name in names if (target / name).exists()},
            indent=2, sort_keys=True,
        ) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?", default=HID)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.hypothesis_id != HID:
        parser.error(f"this runner only handles {HID}")
    diagnostics, card = build()
    manifest = frozen_source_lock.manifest_text(diagnostics)
    if args.check:
        existing = json.loads((RUN_DIR / "diagnostics.json").read_text())
        if (existing != diagnostics or (RUN_DIR / "result_card.md").read_text() != card
                or (RUN_DIR / "manifest.yaml").read_text() != manifest):
            print("FAIL: exact replay artifacts stale", file=sys.stderr)
            return 1
    else:
        snapshot_prior()
        (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True, allow_nan=False) + "\n")
        (RUN_DIR / "result_card.md").write_text(card)
        (RUN_DIR / "manifest.yaml").write_text(manifest)
    print(f"{HID}: {diagnostics['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
