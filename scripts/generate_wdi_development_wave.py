#!/usr/bin/env python3
"""Generate a bounded WDI development-checklist wave.

The country list and thresholds are explicit by design: this is for producing
auditable, pre-registered checklist specs, not for searching all countries and
auto-selecting winners.
"""
from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
HYP_DIR = REPO_ROOT / "hypotheses" / "growth"
STEEL_DIR = REPO_ROOT / "hypotheses" / "steelman"


COUNTRIES = [
    {
        "iso3": "CHN",
        "name": "China",
        "slug": "china",
        "thresholds": {"growth": 5.5, "mortality": 80, "life": 10, "services": 40},
        "tags": ["china_post_1990_growth", "structural_transformation", "health_transition"],
    },
    {
        "iso3": "KOR",
        "name": "South Korea",
        "slug": "south_korea",
        "thresholds": {"growth": 3.5, "mortality": 75, "life": 15, "services": 65},
        "tags": ["korea_convergence", "services_shift", "health_transition"],
    },
    {
        "iso3": "POL",
        "name": "Poland",
        "slug": "poland",
        "thresholds": {"growth": 3.0, "mortality": 70, "life": 10, "services": 55},
        "tags": ["poland_transition_growth", "eu_convergence", "health_transition"],
    },
    {
        "iso3": "TUR",
        "name": "Turkey",
        "slug": "turkey",
        "thresholds": {"growth": 3.0, "mortality": 75, "life": 10, "services": 50},
        "tags": ["turkey_middle_income_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "IDN",
        "name": "Indonesia",
        "slug": "indonesia",
        "thresholds": {"growth": 3.0, "mortality": 70, "life": 10, "services": 45},
        "tags": ["indonesia_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "CHL",
        "name": "Chile",
        "slug": "chile",
        "thresholds": {"growth": 2.5, "mortality": 60, "life": 9, "services": 65},
        "tags": ["chile_convergence", "services_shift", "health_transition"],
    },
    {
        "iso3": "NPL",
        "name": "Nepal",
        "slug": "nepal",
        "thresholds": {"growth": 2.5, "mortality": 75, "life": 25, "services": 40},
        "tags": ["nepal_development", "services_shift", "health_transition"],
    },
    {
        "iso3": "KHM",
        "name": "Cambodia",
        "slug": "cambodia",
        "thresholds": {"growth": 3.0, "mortality": 80, "life": 25, "services": 35},
        "tags": ["cambodia_post_conflict_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "RWA",
        "name": "Rwanda",
        "slug": "rwanda",
        "thresholds": {"growth": 3.5, "mortality": 70, "life": 35, "services": 35},
        "tags": ["rwanda_post_conflict_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "MDV",
        "name": "Maldives",
        "slug": "maldives",
        "thresholds": {"growth": 3.0, "mortality": 85, "life": 25, "services": 65},
        "tags": ["maldives_tourism_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "ARM",
        "name": "Armenia",
        "slug": "armenia",
        "thresholds": {"growth": 3.5, "mortality": 75, "life": 12, "services": 45},
        "tags": ["armenia_transition_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "LKA",
        "name": "Sri Lanka",
        "slug": "sri_lanka",
        "thresholds": {"growth": 3.0, "mortality": 70, "life": 10, "services": 45},
        "tags": ["sri_lanka_development", "services_shift", "health_transition"],
    },
    {
        "iso3": "IND",
        "name": "India",
        "slug": "india",
        "thresholds": {"growth": 4.0, "mortality": 75, "life": 20, "services": 30},
        "tags": ["india_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "THA",
        "name": "Thailand",
        "slug": "thailand",
        "thresholds": {"growth": 2.5, "mortality": 70, "life": 10, "services": 40},
        "tags": ["thailand_development", "services_shift", "health_transition"],
    },
    {
        "iso3": "MYS",
        "name": "Malaysia",
        "slug": "malaysia",
        "thresholds": {"growth": 3.0, "mortality": 45, "life": 7, "services": 55},
        "tags": ["malaysia_development", "services_shift", "health_transition"],
    },
    {
        "iso3": "GHA",
        "name": "Ghana",
        "slug": "ghana",
        "thresholds": {"growth": 2.5, "mortality": 65, "life": 15, "services": 40},
        "tags": ["ghana_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "UZB",
        "name": "Uzbekistan",
        "slug": "uzbekistan",
        "thresholds": {"growth": 2.5, "mortality": 75, "life": 10, "services": 45},
        "tags": ["uzbekistan_transition_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "ALB",
        "name": "Albania",
        "slug": "albania",
        "thresholds": {"growth": 3.5, "mortality": 70, "life": 8, "services": 40},
        "tags": ["albania_transition_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "MNG",
        "name": "Mongolia",
        "slug": "mongolia",
        "thresholds": {"growth": 2.5, "mortality": 80, "life": 20, "services": 40},
        "tags": ["mongolia_transition_growth", "services_shift", "health_transition"],
    },
    {
        "iso3": "BTN",
        "name": "Bhutan",
        "slug": "bhutan",
        "thresholds": {"growth": 4.0, "mortality": 80, "life": 25, "services": 30},
        "tags": ["bhutan_development", "services_shift", "health_transition"],
    },
]


def metric(metric_id: str, description: str, threshold: str, window: str,
           source: str, transformation: str, independence: str) -> dict:
    return {
        "metric_id": metric_id,
        "description": description,
        "threshold": threshold,
        "window": window,
        "source": source,
        "direction": "supports_claim",
        "independence_justification": independence,
    }


def build_spec(country: dict) -> dict:
    t = country["thresholds"]
    hid = f"{country['slug']}_growth_health_services_shift_1990_2023"
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": "growth",
        "claim": (
            f"{country['name']}'s 1990-2023 development trajectory combined "
            "sustained real income growth, large child-mortality reductions, "
            "rising life expectancy, and a services-employment shift. The "
            f"narrow test is whether {country['name']} clears at least three "
            "of four independent outcome thresholds over the period, using "
            "WDI vintages already present in the pipeline."
        ),
        "evidence_type": "canonical_case_multi_metric",
        "sample": {
            "countries": [country["iso3"]],
            "period": [1990, 2023],
            "temporal_structure": "time_series",
        },
        "canonical_metrics": [
            metric(
                "real_gdp_pc_growth_sustained",
                f"{country['name']} average annual real GDP per-capita growth",
                f"average annual growth >= {t['growth']}%",
                "1990-2023",
                "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
                "annual_mean",
                "Income-growth series separate from health and employment composition.",
            ),
            metric(
                "under5_mortality_decline_large",
                f"{country['name']} under-5 mortality rate decline",
                f">= {t['mortality']}% decline",
                "1990-2023",
                "world_bank_wdi:SH.DYN.MORT",
                "peak_to_trough_decline",
                "Health outcome independently collected from GDP/employment statistics.",
            ),
            metric(
                "life_expectancy_gain_large",
                f"{country['name']} life expectancy increased substantially from the 1990 baseline",
                f">= {t['life']}% increase",
                "1990-2023",
                "world_bank_wdi:SP.DYN.LE00.IN",
                "pct_change",
                "Population health stock measure distinct from under-5 mortality rate.",
            ),
            metric(
                "services_employment_share_high",
                f"{country['name']} services employment reached a substantial share before COVID",
                f">= {t['services']}% during 2019",
                "2019",
                "world_bank_wdi:SL.SRV.EMPL.ZS",
                "level",
                "Labour-market composition measured independently of health and growth outcomes.",
            ),
        ],
        "multi_metric_falsification": {
            "total_metrics": 4,
            "support_threshold": 3,
            "refute_threshold": 1,
        },
        "estimator": {
            "template": "multi_metric_checklist",
            "clustering": "none",
            "notes": "Canonical-case checklist over WDI income, health, and employment-composition series.",
        },
        "falsification": {
            "rule": (
                "SUPPORTED if at least 3 of 4 metrics meet their thresholds, "
                "REFUTED if at most 1 metric is met after all available data "
                "are evaluated, and otherwise INCONCLUSIVE."
            ),
            "test": "multi_metric_checklist_development_and_services_shift",
            "threshold": "MET >= 3 of 4; REFUTE when confirmed MET <= 1 with no pending path to support",
        },
        "variables": {
            "outcome": [
                {
                    "name": "real_gdp_pc_growth",
                    "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
                    "transformation": "annual_mean",
                },
                {
                    "name": "under5_mortality",
                    "source": "world_bank_wdi:SH.DYN.MORT",
                    "transformation": "peak_to_trough_decline",
                },
                {
                    "name": "life_expectancy",
                    "source": "world_bank_wdi:SP.DYN.LE00.IN",
                    "transformation": "pct_change",
                },
                {
                    "name": "services_employment_share",
                    "source": "world_bank_wdi:SL.SRV.EMPL.ZS",
                    "transformation": "level",
                },
            ]
        },
        "prior_confidence": 0.78,
        "disclosure": (
            f"Author prior expects {country['name']} to clear the health and "
            "growth thresholds. The checklist is descriptive and does not "
            "identify which policy package, sectoral driver, or external "
            "condition caused the pattern."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {
            "period": [1990, 2023],
            "countries": [country["iso3"]],
            "outcome_dim": ["gdp_growth", "life_expectancy_health", "employment_labour"],
            "policy_family": ["industrial_policy", "labour_market", "institutional_reform"],
            "treatment_tags": country["tags"],
        },
    }


def write_steelman(country: dict) -> None:
    hid = f"{country['slug']}_growth_health_services_shift_1990_2023"
    text = f"""# Steelman: {country['name']} growth, health, and services shift

The strongest caution is that {country['name']}'s outcome pattern is not a
clean test of one mechanism. Demographic transition, global trade exposure,
commodity cycles, migration, remittances, public-health diffusion, education
gains, and classification changes in employment can all move together. A
supported result would show that the descriptive development pattern is real,
not that any single reform model caused it.
"""
    (STEEL_DIR / f"{hid}.md").write_text(text)


def main() -> None:
    HYP_DIR.mkdir(parents=True, exist_ok=True)
    STEEL_DIR.mkdir(parents=True, exist_ok=True)
    for country in COUNTRIES:
        hid = f"{country['slug']}_growth_health_services_shift_1990_2023"
        spec = build_spec(country)
        path = HYP_DIR / f"{hid}.yaml"
        with path.open("w") as f:
            f.write("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n")
            yaml.safe_dump(spec, f, sort_keys=False, width=88)
        write_steelman(country)
        print(hid)


if __name__ == "__main__":
    main()
