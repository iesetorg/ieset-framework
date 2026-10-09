#!/usr/bin/env python3
"""Eight source-pinned, country-disjoint measured-association holdouts.

Preflight reads only country/year keys. Outcome values can be loaded only after
all eight specs, steelmen, and this runner exist unchanged in one earlier Git
commit that contains no result artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_third_legacy_panel_geographic_holdouts_v2.py"
OLD_RUN_COMMIT = "e786a95e676c9d6283c123682d43bf54dbacd73b"
OLD_COUNTRIES = frozenset(
    "ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR IDN IND "
    "ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL SWE "
    "THA TUR USA VNM ZAF".split()
)
ISO3_COUNTRIES = frozenset((
    "ABW AFG AGO AIA ALA ALB AND ARE ARG ARM ASM ATA ATF ATG AUS AUT AZE BDI BEL BEN "
    "BES BFA BGD BGR BHR BHS BIH BLM BLR BLZ BMU BOL BRA BRB BRN BTN BVT BWA CAF CAN "
    "CCK CHE CHL CHN CIV CMR COD COG COK COL COM CPV CRI CUB CUW CXR CYM CYP CZE DEU "
    "DJI DMA DNK DOM DZA ECU EGY ERI ESH ESP EST ETH FIN FJI FLK FRA FRO FSM GAB GBR "
    "GEO GGY GHA GIB GIN GLP GMB GNB GNQ GRC GRD GRL GTM GUF GUM GUY HKG HMD HND HRV "
    "HTI HUN IDN IMN IND IOT IRL IRN IRQ ISL ISR ITA JAM JEY JOR JPN KAZ KEN KGZ KHM "
    "KIR KNA KOR KWT LAO LBN LBR LBY LCA LIE LKA LSO LTU LUX LVA MAC MAF MAR MCO MDA "
    "MDG MDV MEX MHL MKD MLI MLT MMR MNE MNG MNP MOZ MRT MSR MTQ MUS MWI MYS MYT NAM "
    "NCL NER NFK NGA NIC NIU NLD NOR NPL NRU NZL OMN PAK PAN PCN PER PHL PLW PNG POL "
    "PRI PRK PRT PRY PSE PYF QAT REU ROU RUS RWA SAU SDN SEN SGP SGS SHN SJM SLB SLE "
    "SLV SMR SOM SPM SRB SSD STP SUR SVK SVN SWE SWZ SXM SYC SYR TCA TCD TGO THA TJK "
    "TKL TKM TLS TON TTO TUN TUR TUV TWN TZA UGA UKR UMI URY USA UZB VAT VCT VEN VGB "
    "VIR VNM VUT WLF WSM XKX YEM ZAF ZMB ZWE"
).split())
FAMILY_ID = "third_legacy_panel_geographic_holdouts_2026_10_09"
FAMILY_P_MAX = 0.10 / 8
PERIOD = [1996, 2023]
MIN_OBSERVATIONS = 800
MIN_COUNTRIES = 50
MIN_PAIRS_PER_COUNTRY = 5
COEFFICIENT_COLUMNS = (
    "term", "coefficient", "std_error", "p_value", "ci95", "n_obs",
    "n_countries", "r_squared", "method",
)

# Every file is recorded in a tracked fetch manifest. Source IDs are exact
# indicator names; the RQ file's source ID is GOV_WGI_RQ.EST, not the old alias.
SOURCE_FILES: dict[str, dict[str, str]] = {'services': {'source': 'world_bank_wdi:SL.SRV.EMPL.ZS',
              'path': 'data/vintages/world_bank_wdi/SL.SRV.EMPL.ZS@2026-04-30T115129Z.parquet',
              'sha256': '5cc0fcababebe90b69eae253466a6a81beaf0f52f9c0ef5d59b8a2fa34f400c6',
              'manifest': 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
              'series_id': 'SL.SRV.EMPL.ZS'},
 'privatecons': {'source': 'world_bank_wdi:NE.CON.PRVT.PC.KD',
                 'path': 'data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet',
                 'sha256': 'e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe',
                 'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
                 'series_id': 'NE.CON.PRVT.PC.KD'},
 'govcons': {'source': 'world_bank_wdi:NE.CON.GOVT.ZS',
             'path': 'data/vintages/world_bank_wdi/NE.CON.GOVT.ZS@2026-05-05T194701Z.parquet',
             'sha256': 'a6605c618d3dd91b061c4dae7960c4c0baad66c037125aec44cb6b71ccb6a79d',
             'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
             'series_id': 'NE.CON.GOVT.ZS'},
 'income': {'source': 'world_bank_wdi:NY.GDP.PCAP.KD',
            'path': 'data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet',
            'sha256': '0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f',
            'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
            'series_id': 'NY.GDP.PCAP.KD'},
 'rq': {'source': 'wgi:GOV_WGI_RQ.EST',
        'path': 'data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet',
        'sha256': '4d8084d77990bc1d10f5630cdf8100c9ce2e1b610ade3aa7b46340fb658c8e2e',
        'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
        'series_id': 'GOV_WGI_RQ.EST'},
 'ge': {'source': 'wgi:GOV_WGI_GE.EST',
        'path': 'data/vintages/wgi/GOV_WGI_GE.EST@2026-05-05T195208Z.parquet',
        'sha256': '607d47979340b803fec2fefc1e57c94a7a167432317451ea0b1ade3ee0503edc',
        'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
        'series_id': 'GOV_WGI_GE.EST'},
 'rl': {'source': 'wgi:RL.EST',
        'path': 'data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet',
        'sha256': '63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d',
        'manifest': 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
        'series_id': 'RL.EST'},
 'lfp': {'source': 'world_bank_wdi:SL.TLF.CACT.ZS',
         'path': 'data/vintages/world_bank_wdi/SL.TLF.CACT.ZS@2026-04-30T115141Z.parquet',
         'sha256': 'db20633db7749779fa9e106848ba5f32dae3627fb6615c832a3fe2ad25132925',
         'manifest': 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
         'series_id': 'SL.TLF.CACT.ZS'},
 'physicians': {'source': 'world_bank_wdi:SH.MED.PHYS.ZS',
                'path': 'data/vintages/world_bank_wdi/SH.MED.PHYS.ZS@2026-04-30T114635Z.parquet',
                'sha256': 'dc4fea8a387adb212f254bdcdae60323b694b0a9a18be81c1ec1484fa7bbed33',
                'manifest': 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
                'series_id': 'SH.MED.PHYS.ZS'},
 'tertiary': {'source': 'world_bank_wdi:SE.TER.ENRR',
              'path': 'data/vintages/world_bank_wdi/SE.TER.ENRR@2026-05-05T195043Z.parquet',
              'sha256': '0459b48b5625f54872c4708f4a6107e66c8c44087b18d798c99e91e83511cede',
              'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
              'series_id': 'SE.TER.ENRR'},
 'electricity': {'source': 'world_bank_wdi:EG.ELC.ACCS.ZS',
                 'path': 'data/vintages/world_bank_wdi/EG.ELC.ACCS.ZS@2026-05-05T195057Z.parquet',
                 'sha256': 'aa564cbe2947b3d1c3499d7ecb9b2c38c6aa5de073d2cc1a797cfe2fe42f2931',
                 'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
                 'series_id': 'EG.ELC.ACCS.ZS'},
 'urban': {'source': 'world_bank_wdi:SP.URB.TOTL.IN.ZS',
           'path': 'data/vintages/world_bank_wdi/SP.URB.TOTL.IN.ZS@2026-04-30T114159Z.parquet',
           'sha256': 'd3545e1c27b14eabafd3cbe7bbbc5edb5f21c7b97954ab76fc70392599c675f6',
           'manifest': 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
           'series_id': 'SP.URB.TOTL.IN.ZS'},
 'hightech': {'source': 'world_bank_wdi:TX.VAL.TECH.MF.ZS',
              'path': 'data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet',
              'sha256': 'b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994',
              'manifest': 'data/manifests/fetch_run_2026-05-05T200056Z.yaml',
              'series_id': 'TX.VAL.TECH.MF.ZS'}}

COHORT: dict[str, dict[str, Any]] = {'services_employment_private_consumption_geographic_holdout_v2': {'old_id': 'private_sector_job_creation_consumption',
                                                                   'old_topic': 'labour',
                                                                   'topic': 'growth',
                                                                   'old_verdict': 'PARTIAL',
                                                                   'old_n_obs': 956,
                                                                   'old_n_countries': 39,
                                                                   'old_direction': '+',
                                                                   'roles': {'treatment': 'services',
                                                                             'outcome': 'privatecons',
                                                                             'rule_of_law': 'rl',
                                                                             'income': 'income'},
                                                                   'outcome_name': 'next_year_log_private_consumption_pc_growth',
                                                                   'treatment_name': 'services_employment_share_pct',
                                                                   'outcome_transform': 'log_change',
                                                                   'treatment_transform': 'level',
                                                                   'controls': ['log_income', 'rule_of_law'],
                                                                   'expected_sign': '+'},
 'regulatory_quality_labor_participation_geographic_holdout_v2': {'old_id': 'portable_benefits_market_flexibility',
                                                                  'old_topic': 'labour',
                                                                  'topic': 'labour',
                                                                  'old_verdict': 'PARTIAL',
                                                                  'old_n_obs': 1000,
                                                                  'old_n_countries': 40,
                                                                  'old_direction': '+',
                                                                  'roles': {'treatment': 'rq',
                                                                            'outcome': 'lfp',
                                                                            'rule_of_law': 'rl',
                                                                            'income': 'income'},
                                                                  'outcome_name': 'next_year_labor_force_participation_pct',
                                                                  'treatment_name': 'regulatory_quality_estimate',
                                                                  'outcome_transform': 'next_level',
                                                                  'treatment_transform': 'level',
                                                                  'controls': ['log_income', 'rule_of_law'],
                                                                  'expected_sign': '+'},
 'real_income_physician_density_geographic_holdout_v2': {'old_id': 'medical_migration_market_opportunity',
                                                         'old_topic': 'healthcare',
                                                         'topic': 'healthcare',
                                                         'old_verdict': 'SUPPORTED',
                                                         'old_n_obs': 766,
                                                         'old_n_countries': 40,
                                                         'old_direction': '+',
                                                         'roles': {'treatment': 'income',
                                                                   'outcome': 'physicians',
                                                                   'rule_of_law': 'rl'},
                                                         'outcome_name': 'next_year_physicians_per_thousand',
                                                         'treatment_name': 'log_real_income_pc',
                                                         'outcome_transform': 'next_level',
                                                         'treatment_transform': 'log',
                                                         'controls': ['rule_of_law'],
                                                         'expected_sign': '+'},
 'government_effectiveness_tertiary_enrollment_geographic_holdout_v2': {'old_id': 'tertiary_autonomy_research_output',
                                                                        'old_topic': 'growth',
                                                                        'topic': 'growth',
                                                                        'old_verdict': 'PARTIAL',
                                                                        'old_n_obs': 768,
                                                                        'old_n_countries': 40,
                                                                        'old_direction': '+',
                                                                        'roles': {'treatment': 'ge',
                                                                                  'outcome': 'tertiary',
                                                                                  'rule_of_law': 'rl',
                                                                                  'income': 'income'},
                                                                        'outcome_name': 'next_year_gross_tertiary_enrollment_pct',
                                                                        'treatment_name': 'government_effectiveness_estimate',
                                                                        'outcome_transform': 'next_level',
                                                                        'treatment_transform': 'level',
                                                                        'controls': ['log_income',
                                                                                     'rule_of_law'],
                                                                        'expected_sign': '+'},
 'government_effectiveness_electricity_access_geographic_holdout_v2': {'old_id': 'state_capacity_market_infrastructure_complement',
                                                                       'old_topic': 'energy',
                                                                       'topic': 'energy',
                                                                       'old_verdict': 'PARTIAL',
                                                                       'old_n_obs': 988,
                                                                       'old_n_countries': 40,
                                                                       'old_direction': '+',
                                                                       'roles': {'treatment': 'ge',
                                                                                 'outcome': 'electricity',
                                                                                 'rule_of_law': 'rl',
                                                                                 'income': 'income'},
                                                                       'outcome_name': 'next_year_electricity_access_pct',
                                                                       'treatment_name': 'government_effectiveness_estimate',
                                                                       'outcome_transform': 'next_level',
                                                                       'treatment_transform': 'level',
                                                                       'controls': ['log_income',
                                                                                    'rule_of_law'],
                                                                       'expected_sign': '+'},
 'government_consumption_electricity_access_geographic_holdout_v2': {'old_id': 'state_monopoly_infrastructure_cost_overrun',
                                                                     'old_topic': 'energy',
                                                                     'topic': 'energy',
                                                                     'old_verdict': 'PARTIAL',
                                                                     'old_n_obs': 955,
                                                                     'old_n_countries': 39,
                                                                     'old_direction': '-',
                                                                     'roles': {'treatment': 'govcons',
                                                                               'outcome': 'electricity',
                                                                               'rule_of_law': 'rl',
                                                                               'income': 'income'},
                                                                     'outcome_name': 'next_year_electricity_access_pct',
                                                                     'treatment_name': 'government_final_consumption_share_gdp',
                                                                     'outcome_transform': 'next_level',
                                                                     'treatment_transform': 'level',
                                                                     'controls': ['log_income',
                                                                                  'rule_of_law'],
                                                                     'expected_sign': '-'},
 'regulatory_quality_urban_population_geographic_holdout_v2': {'old_id': 'market_urbanization_slum_reduction',
                                                               'old_topic': 'housing',
                                                               'topic': 'housing',
                                                               'old_verdict': 'PARTIAL',
                                                               'old_n_obs': 1000,
                                                               'old_n_countries': 40,
                                                               'old_direction': '+',
                                                               'roles': {'treatment': 'rq',
                                                                         'outcome': 'urban',
                                                                         'rule_of_law': 'rl',
                                                                         'income': 'income'},
                                                               'outcome_name': 'next_year_urban_population_share_pct',
                                                               'treatment_name': 'regulatory_quality_estimate',
                                                               'outcome_transform': 'next_level',
                                                               'treatment_transform': 'level',
                                                               'controls': ['log_income', 'rule_of_law'],
                                                               'expected_sign': '+'},
 'government_consumption_hightech_export_share_geographic_holdout_v2': {'old_id': 'incumbent_subsidy_innovation_drag',
                                                                        'old_topic': 'regulatory',
                                                                        'topic': 'trade',
                                                                        'old_verdict': 'PARTIAL',
                                                                        'old_n_obs': 612,
                                                                        'old_n_countries': 39,
                                                                        'old_direction': '-',
                                                                        'roles': {'treatment': 'govcons',
                                                                                  'outcome': 'hightech',
                                                                                  'rule_of_law': 'rl',
                                                                                  'income': 'income'},
                                                                        'outcome_name': 'next_year_hightech_manufactured_export_share_pct',
                                                                        'treatment_name': 'government_final_consumption_share_gdp',
                                                                        'outcome_transform': 'next_level',
                                                                        'treatment_transform': 'level',
                                                                        'controls': ['log_income',
                                                                                     'rule_of_law'],
                                                                        'expected_sign': '-'}}

MEASUREMENT_LIMITS = {'services_employment_private_consumption_geographic_holdout_v2': 'WDI services employment share is a '
                                                                  'modelled ILO sector share, not '
                                                                  'private-sector job creation; private '
                                                                  'consumption per person does not '
                                                                  'identify a service-market policy '
                                                                  'effect.',
 'regulatory_quality_labor_participation_geographic_holdout_v2': 'WGI regulatory quality is a '
                                                                 'perceptions-based composite, not a '
                                                                 'portable-benefits rule or direct '
                                                                 'labor-market flexibility measure; WDI '
                                                                 'participation does not identify '
                                                                 'employment quality.',
 'real_income_physician_density_geographic_holdout_v2': 'Real GDP per person is not a market-policy '
                                                        'treatment; physician density is not a direct '
                                                        'measure of medical migration, retention, care '
                                                        'quality, or access.',
 'government_effectiveness_tertiary_enrollment_geographic_holdout_v2': 'WGI government effectiveness is '
                                                                       'a perceptions-based '
                                                                       'public-service composite; gross '
                                                                       'tertiary enrollment is not '
                                                                       'university autonomy, education '
                                                                       'quality, completion, or '
                                                                       'research output.',
 'government_effectiveness_electricity_access_geographic_holdout_v2': 'WGI government effectiveness is '
                                                                      'a perceptions-based composite; '
                                                                      'electricity access is not '
                                                                      'infrastructure quality, '
                                                                      'reliability, affordability, or '
                                                                      'state-market complementarity.',
 'government_consumption_electricity_access_geographic_holdout_v2': 'Government final consumption share '
                                                                    'is not state monopoly, procurement '
                                                                    'practice, electricity investment, '
                                                                    'or project cost overruns; '
                                                                    'electricity access is only a '
                                                                    'coverage measure.',
 'regulatory_quality_urban_population_geographic_holdout_v2': 'WGI regulatory quality is not '
                                                              'housing-supply reform; urban population '
                                                              'share uses national urban definitions '
                                                              'and says nothing about slums, housing '
                                                              'affordability, or migration welfare.',
 'government_consumption_hightech_export_share_geographic_holdout_v2': 'Government final consumption is '
                                                                       'not an incumbent subsidy; '
                                                                       'high-technology share of '
                                                                       'manufactured exports is export '
                                                                       'composition, not innovation, '
                                                                       'domestic value added, or firm '
                                                                       'failure.'}

def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = COHORT[hypothesis_id]["topic"]
    return (
        f"hypotheses/{topic}/{hypothesis_id}.yaml",
        f"hypotheses/steelman/{hypothesis_id}.md",
        f"engine/runs/{hypothesis_id}",
    )


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"], cwd=ROOT,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_spec(hypothesis_id: str) -> dict[str, Any]:
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, _ = paths(hypothesis_id)
    spec = yaml.safe_load((ROOT / spec_rel).read_text(encoding="utf-8"))
    old_rel = f"hypotheses/{config['old_topic']}/{config['old_id']}.yaml"
    old_spec = yaml.safe_load(git_show(OLD_RUN_COMMIT, old_rel))
    old_diagnostics = json.loads(git_show(
        OLD_RUN_COMMIT, f"engine/runs/{config['old_id']}/diagnostics.json"
    ))
    if set(old_spec["sample"]["countries"]) != OLD_COUNTRIES:
        raise ValueError(f"historical old-country roster changed: {hypothesis_id}")
    def source_identity(source: str) -> str:
        return source.replace("wgi:GOV_WGI_", "wgi:")

    for role in ("treatment", "outcome"):
        old_sources = {
            source_identity(item["source"])
            for item in old_spec["variables"][role]
        }
        pinned_source = source_identity(SOURCE_FILES[config["roles"][role]]["source"])
        if old_sources != {pinned_source}:
            raise ValueError(f"historical old source pair changed: {hypothesis_id}: {role}")
    historical_runner = git_show(OLD_RUN_COMMIT, "scripts/run_panel_fe.py").decode()
    if ('out = out[out["country_iso3"].isin(countries)]' not in historical_runner or
            "panel_filt = filter_sample(panel, spec)" not in historical_runner or
            "est = run_panel_ols(\n        panel_filt," not in historical_runner):
        raise ValueError("historical old runner no longer proves country restriction")
    if old_diagnostics["estimate"]["n_obs"] != config["old_n_obs"] or \
            old_diagnostics["estimate"]["n_countries"] != config["old_n_countries"] or \
            old_diagnostics["verdict_label"] != config["old_verdict"] or \
            old_diagnostics["claim_direction_inferred"] != config["old_direction"]:
        raise ValueError(f"historical old result changed: {hypothesis_id}")
    if spec["hypothesis_id"] != hypothesis_id or spec["status"] != "pre_registered":
        raise ValueError(f"incorrect new registration: {spec_rel}")
    if spec.get("evidence_type") != "associational" or spec.get("claim_direction") != config["expected_sign"]:
        raise ValueError(f"claim direction or evidence type changed: {spec_rel}")
    if spec["sample"]["period"] != PERIOD or spec["sample"]["countries"] != ["GLOBAL"]:
        raise ValueError(f"sample period changed: {spec_rel}")
    expected_exclusion = (
        "Exclude all 40 countries in the historical old specification: "
        + " ".join(sorted(OLD_COUNTRIES)) + "."
    )
    if spec["sample"]["exclusion_rules"][0] != expected_exclusion:
        raise ValueError(f"written old-country exclusion changed: {spec_rel}")
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": FAMILY_ID, "family_size": len(COHORT),
        "family_alpha": 0.10, "family_p_max": FAMILY_P_MAX,
        "expected_sign": config["expected_sign"],
        "min_observations": MIN_OBSERVATIONS,
        "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
        "old_hypothesis_id": config["old_id"],
        "old_result_bucket": config["old_verdict"],
        "old_country_count": len(OLD_COUNTRIES),
        "old_country_ids": sorted(OLD_COUNTRIES),
        "old_run_commit": OLD_RUN_COMMIT, "old_claim_direction": config["old_direction"],
        "school_score_credit": 0, "school_score_eligible": False,
    }
    if any(threshold.get(key) != value for key, value in expected.items()):
        raise ValueError(f"frozen threshold or old-roster mismatch: {spec_rel}")
    if set(threshold["source_files"]) != set(config["roles"]):
        raise ValueError(f"source roles changed: {spec_rel}")
    for role, source_key in config["roles"].items():
        if threshold["source_files"][role] != SOURCE_FILES[source_key]:
            raise ValueError(f"source pin changed: {spec_rel}: {role}")
    variables = spec["variables"]
    observed = {
        block: {item["name"]: item["source"] for item in variables.get(block, [])}
        for block in ("outcome", "treatment", "controls")
    }
    if observed["outcome"] != {config["outcome_name"]: SOURCE_FILES[config["roles"]["outcome"]]["source"]}:
        raise ValueError(f"outcome source changed: {spec_rel}")
    if observed["treatment"] != {config["treatment_name"]: SOURCE_FILES[config["roles"]["treatment"]]["source"]}:
        raise ValueError(f"treatment source changed: {spec_rel}")
    if set(observed["controls"]) != set(config["controls"]):
        raise ValueError(f"control set changed: {spec_rel}")
    expected_controls = {
        "log_income": SOURCE_FILES[config["roles"].get("income", "income")]["source"],
        "rule_of_law": SOURCE_FILES["rl"]["source"],
    }
    if any(observed["controls"][name] != expected_controls[name] for name in config["controls"]):
        raise ValueError(f"control sources changed: {spec_rel}")
    if spec["steelman"] != steelman_rel or not (ROOT / steelman_rel).is_file():
        raise ValueError(f"missing steelman: {steelman_rel}")
    if spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != [] or spec.get("linked_conditions") != []:
        raise ValueError(f"school links prohibited: {spec_rel}")
    if spec["estimator"] != {
        "template": "panel_fe", "fixed_effects": ["country", "year"],
        "clustering": "country",
        "notes": "One fixed primary coefficient with country and treatment-year effects, country-clustered uncertainty, no automatic covariate dropping, and an eight-test Bonferroni rule.",
    }:
        raise ValueError(f"estimator changed: {spec_rel}")
    return spec


def verify_sources(hypothesis_id: str, spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    pins = spec["falsification"]["threshold"]["source_files"]
    for role, pin in pins.items():
        relative = Path(pin["path"])
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or path.suffix != ".parquet":
            raise ValueError(f"invalid source path: {relative}")
        if sha256(path) != pin["sha256"]:
            raise ValueError(f"source SHA-256 mismatch: {relative}")
        manifest = yaml.safe_load((ROOT / pin["manifest"]).read_text(encoding="utf-8"))
        if not any(
            item.get("parquet_path") == pin["path"] and
            item.get("sha256") == pin["sha256"] and
            item.get("series_id") == pin["series_id"]
            for item in manifest.get("entries", [])
        ):
            raise ValueError(f"source absent from tracked fetch manifest: {relative}")
        records[role] = {
            "source": pin["source"], "vintage_file": pin["path"],
            "sha256": pin["sha256"], "source_manifest": pin["manifest"],
        }
    return records


def load_keys(record: dict[str, str]) -> set[tuple[str, int]]:
    """Project only country/year columns; value and null status stay unopened."""
    import pandas as pd

    frame = pd.read_parquet(ROOT / record["vintage_file"], columns=["country_iso3", "year"])
    frame = frame[frame["country_iso3"].isin(ISO3_COUNTRIES) &
                  ~frame["country_iso3"].isin(OLD_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame[frame["year"].notna()].copy()
    keys = list(zip(frame["country_iso3"], frame["year"].astype(int)))
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate country-year keys: {record['vintage_file']}")
    return set(keys)


def complete_keys(hypothesis_id: str, sources: dict[str, dict[str, str]]) -> set[tuple[str, int]]:
    config = COHORT[hypothesis_id]
    keys = {role: load_keys(record) for role, record in sources.items()}
    base = set.intersection(*(keys[role] for role in config["roles"] if role != "outcome"))
    if config["outcome_transform"] == "log_change":
        base &= keys["outcome"]
    future = {(country, year - 1) for country, year in keys["outcome"]}
    base &= future
    base = {(country, year) for country, year in base if PERIOD[0] <= year <= PERIOD[1]}
    counts: dict[str, int] = {}
    for country, _ in base:
        counts[country] = counts.get(country, 0) + 1
    return {(country, year) for country, year in base
            if counts[country] >= MIN_PAIRS_PER_COUNTRY}


def preflight(hypothesis_id: str) -> dict[str, Any]:
    spec = validate_spec(hypothesis_id)
    sources = verify_sources(hypothesis_id, spec)
    keys = complete_keys(hypothesis_id, sources)
    countries = {country for country, _ in keys}
    years = [year for _, year in keys]
    return {
        "hypothesis_id": hypothesis_id,
        "key_pairs_upper_bound": len(keys),
        "key_countries_upper_bound": len(countries),
        "treatment_years": [min(years), max(years)] if years else [],
        "old_countries_excluded": len(OLD_COUNTRIES),
        "old_country_overlap": len(countries & OLD_COUNTRIES),
        "key_envelope_passed": len(keys) >= MIN_OBSERVATIONS and
        len(countries) >= MIN_COUNTRIES and not bool(countries & OLD_COUNTRIES),
        "complete_case_coverage_verified": False,
        "counts_are_upper_bounds": True,
        "coefficient_estimated": False,
        "outcome_values_loaded": False,
    }


def registration_commit() -> str:
    files = [RUNNER_REL]
    for hypothesis_id in COHORT:
        files.extend(paths(hypothesis_id)[:2])
    additions = []
    for relative in files:
        current = (ROOT / relative).read_bytes()
        if git_show("HEAD", relative) != current:
            raise RuntimeError(f"commit the complete eight-test preregistration: {relative}")
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"missing first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("all eight specs, steelmen, and runner must first appear together")
    commit = additions[0]
    for relative in files:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration bytes differ from first addition: {relative}")
    for hypothesis_id in COHORT:
        _, _, run_rel = paths(hypothesis_id)
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit, "--", run_rel],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if result.returncode or result.stdout.strip():
            raise RuntimeError(f"run artifacts existed in registration commit: {run_rel}")
    return commit


def load_values(record: dict[str, str], role: str):
    import numpy as np
    import pandas as pd

    frame = pd.read_parquet(
        ROOT / record["vintage_file"], columns=["country_iso3", "year", "value"]
    )
    frame = frame[frame["country_iso3"].isin(ISO3_COUNTRIES) &
                  ~frame["country_iso3"].isin(OLD_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[role] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["year"].notna() & np.isfinite(frame[role])].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country-year keys: {record['vintage_file']}")
    return frame[["country_iso3", "year", role]]


def build_panel(hypothesis_id: str, sources: dict[str, dict[str, str]]):
    import numpy as np

    config = COHORT[hypothesis_id]
    frames = {role: load_values(record, role) for role, record in sources.items()}
    future = frames["outcome"].copy()
    future["year"] -= 1
    future = future.rename(columns={"outcome": "outcome_next"})
    roles = [role for role in frames if role != "outcome"]
    panel = frames[roles[0]]
    for role in roles[1:]:
        panel = panel.merge(frames[role], on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    if config["outcome_transform"] == "log_change":
        panel = panel.merge(frames["outcome"], on=["country_iso3", "year"], validate="one_to_one")
        panel = panel[(panel["outcome"] > 0) & (panel["outcome_next"] > 0)].copy()
        panel[config["outcome_name"]] = np.log(panel["outcome_next"]) - np.log(panel["outcome"])
    else:
        panel[config["outcome_name"]] = panel["outcome_next"]
    if config["treatment_transform"] == "log":
        panel = panel[panel["treatment"] > 0].copy()
        panel[config["treatment_name"]] = np.log(panel["treatment"])
    else:
        panel[config["treatment_name"]] = panel["treatment"]
    if "log_income" in config["controls"]:
        panel = panel[panel["income"] > 0].copy()
        panel["log_income"] = np.log(panel["income"])
    panel = panel[panel["year"].between(*PERIOD)].copy()
    required = [config["outcome_name"], config["treatment_name"], *config["controls"]]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_PAIRS_PER_COUNTRY].copy()
    if set(panel["country_iso3"]) & OLD_COUNTRIES:
        raise AssertionError("old countries entered the new fitted sample")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def classify(coefficient: float, p_value: float, expected_sign: str) -> tuple[str, str]:
    direction = 1 if expected_sign == "+" else -1
    if direction * coefficient > 0 and p_value <= FAMILY_P_MAX:
        return "SUPPORTED", "predeclared direction clears the eight-test family threshold"
    if direction * coefficient < 0 and p_value <= FAMILY_P_MAX:
        return "REFUTED", "opposite direction clears the eight-test family threshold"
    return "PARTIAL", "estimable coefficient does not clear the directional family rule"


def estimate_one(hypothesis_id: str, sources: dict[str, dict[str, str]]):
    import statsmodels.formula.api as smf

    config = COHORT[hypothesis_id]
    panel = build_panel(hypothesis_id, sources)
    countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": len(panel), "countries": countries,
        "old_country_overlap": 0,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
        "passed": len(panel) >= MIN_OBSERVATIONS and countries >= MIN_COUNTRIES,
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "registered complete-case sample gate failed", None
    treatment = config["treatment_name"]
    controls = " + ".join(config["controls"])
    formula = (f"{config['outcome_name']} ~ {treatment} + {controls} "
               "+ C(country_iso3) + C(year)")
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"], "use_correction": True}
        )
        coefficient = float(fit.params[treatment])
        std_error = float(fit.bse[treatment])
        p_value = float(fit.pvalues[treatment])
        ci95 = [float(x) for x in fit.conf_int().loc[treatment].tolist()]
        if fit.model.rank < fit.model.exog.shape[1] or \
                not all(math.isfinite(x) for x in (coefficient, std_error, p_value, *ci95)) or \
                std_error <= 0:
            raise ValueError("rank-deficient or nonfinite primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    verdict, reason = classify(coefficient, p_value, config["expected_sign"])
    estimate = {
        "coefficient": coefficient, "std_error": std_error, "p_value": p_value,
        "ci95": ci95, "n_obs": len(panel), "n_countries": countries,
        "r_squared": float(fit.rsquared),
        "method": "country/year FE OLS, country-clustered standard errors",
    }
    return gate, verdict, reason, estimate


def artifact_records(hypothesis_id: str, prereg_commit: str,
                     sources: dict[str, dict[str, str]], gate: dict[str, Any],
                     verdict: str, reason: str, estimate: dict[str, Any] | None,
                     stamp: str):
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, run_rel = paths(hypothesis_id)
    source_list = [{"role": role, **record} for role, record in sources.items()]
    limitations = [
        "These are country-disjoint measured associations, not causal policy effects.",
        "The old same-commit result was seen before this new registration.",
        "The eight tests share macro source families and use a within-family correction.",
        "No linked school or position receives score credit from this calibration-only test.",
        "Source vintages and eligible countries may overlap other IESET v2 studies.",
        MEASUREMENT_LIMITS[hypothesis_id],
    ]
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "panel_fe",
        "preflight": gate, "estimate": estimate, "family_id": FAMILY_ID,
        "family_size": len(COHORT), "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": source_list},
        "limitations": limitations,
        "correction": {"disposition": "descriptive_calibration_only",
                       "school_score_eligible": False, "school_score_credit": 0},
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": verdict,
        "old_hypothesis_id": config["old_id"], "old_verdict": config["old_verdict"],
        "old_run_commit": OLD_RUN_COMMIT, "old_claim_direction": config["old_direction"],
        "vintages": source_list,
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_rel, "topic": config["topic"]},
        "preregistration": {"spec_commit": prereg_commit, "steelman": steelman_rel,
                            "family_id": FAMILY_ID, "family_p_max": FAMILY_P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": run_rel,
                         "command": f"python3 {RUNNER_REL} --check {hypothesis_id}"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": source_list, "old_country_overlap": 0},
        "results": estimate, "limitations": limitations,
    }
    card = (
        f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
        f"Old same-commit run: {config['old_id']} ({config['old_verdict']} known).\n"
        f"Preregistration commit: {prereg_commit}.\n"
        f"Held-out sample: {gate['observations']} country-year pairs, "
        f"{gate['countries']} countries, zero old-country overlap.\n"
        f"Family threshold: two-sided p <= {FAMILY_P_MAX:.8f} over eight tests.\n"
    )
    if estimate is not None:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; "
                 f"clustered SE {estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += ("\nMeasurement boundary: " + MEASUREMENT_LIMITS[hypothesis_id]
             + "\nDescriptive calibration only. The old causal or mechanism label is not validated. "
             "No school-score credit.\n")
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / {RUNNER_REL!r}), '--check', {hypothesis_id!r}], cwd=root))\n"
    )
    chart = {
        "hypothesis_id": hypothesis_id, "verdict": verdict,
        "coefficient": estimate["coefficient"] if estimate else None,
        "ci95": estimate["ci95"] if estimate else None,
        "family_p_max": FAMILY_P_MAX,
    }
    rows = ([{key: ({"term": config["treatment_name"], **estimate}).get(key)
              for key in COEFFICIENT_COLUMNS}] if estimate else [])
    return diagnostics, manifest, packet, card, wrapper, chart, rows


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label} fields mismatch")
        for key, value in expected.items():
            assert_equal(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            raise AssertionError(f"{label} length mismatch")
        for index, value in enumerate(expected):
            assert_equal(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, int):
        if isinstance(actual, bool) or not isinstance(actual, int) or actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, float):
        try:
            number = float(actual)
        except (ValueError, TypeError) as error:
            raise AssertionError(f"{label} is not numeric") from error
        if not math.isfinite(number) or not math.isclose(number, expected, rel_tol=1e-8, abs_tol=1e-10):
            raise AssertionError(f"{label} mismatch")
    elif actual != expected:
        raise AssertionError(f"{label} mismatch")


def read_coefficient_rows(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_parquet(path)
    if list(frame.columns) != list(COEFFICIENT_COLUMNS):
        raise AssertionError("stored coefficient columns mismatch")
    return [
        {key: value.tolist() if hasattr(value, "tolist") else value
         for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def write_run(hypothesis_id: str, prereg_commit: str, sources: dict[str, dict[str, str]],
              gate: dict[str, Any], verdict: str, reason: str,
              estimate: dict[str, Any] | None) -> dict[str, Any]:
    import pandas as pd

    spec_rel, _, run_rel = paths(hypothesis_id)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, wrapper, chart, rows = artifact_records(
        hypothesis_id, prereg_commit, sources, gate, verdict, reason, estimate, stamp
    )
    run_dir = ROOT / run_rel
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "hypothesis.yaml").write_bytes((ROOT / spec_rel).read_bytes())
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "replication.py").write_text(wrapper, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS).to_parquet(run_dir / "coefficients.parquet", index=False)
    return {"hypothesis_id": hypothesis_id, "verdict": verdict, "run_dir": run_rel}


def run_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit()
    _, _, run_rel = paths(hypothesis_id)
    if (ROOT / run_rel).exists():
        raise FileExistsError(f"existing run: {run_rel}")
    spec = validate_spec(hypothesis_id)
    sources = verify_sources(hypothesis_id, spec)
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, sources)
    return write_run(hypothesis_id, prereg_commit, sources, gate, verdict, reason, estimate)


def check_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit()
    spec_rel, _, run_rel = paths(hypothesis_id)
    run_dir = ROOT / run_rel
    if not run_dir.is_dir():
        raise FileNotFoundError(f"missing run: {run_rel}")
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text(encoding="utf-8"))
    packet = yaml.safe_load((run_dir / "evidence_packet.yaml").read_text(encoding="utf-8"))
    chart = json.loads((run_dir / "chart_data.json").read_text(encoding="utf-8"))
    card = (run_dir / "result_card.md").read_text(encoding="utf-8")
    wrapper = (run_dir / "replication.py").read_text(encoding="utf-8")
    hypothesis = (run_dir / "hypothesis.yaml").read_bytes()
    coefficients = read_coefficient_rows(run_dir / "coefficients.parquet")
    if hypothesis != (ROOT / spec_rel).read_bytes():
        raise AssertionError("stored hypothesis snapshot mismatch")
    spec = validate_spec(hypothesis_id)
    sources = verify_sources(hypothesis_id, spec)
    stamp = diagnostics["run_utc"]
    expected = artifact_records(
        hypothesis_id, prereg_commit, sources, diagnostics["preflight"],
        diagnostics["verdict_label"], diagnostics["verdict_reason"],
        diagnostics["estimate"], stamp,
    )
    for label, actual, should in zip(
        ("diagnostics", "manifest", "evidence_packet", "chart_data", "coefficients"),
        (diagnostics, manifest, packet, chart, coefficients),
        (expected[0], expected[1], expected[2], expected[5], expected[6]),
    ):
        assert_equal(actual, should, label)
    if card != expected[3] or wrapper != expected[4]:
        raise AssertionError("stored text artifact mismatch")
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, sources)
    assert_equal(diagnostics["preflight"], gate, "sample gate")
    assert_equal(diagnostics["verdict_label"], verdict, "verdict")
    assert_equal(diagnostics["verdict_reason"], reason, "verdict reason")
    assert_equal(diagnostics["estimate"], estimate, "estimate")
    return {"hypothesis_id": hypothesis_id, "verified": True, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", metavar="ID", choices=[*COHORT, "all"])
    mode.add_argument("--check", metavar="ID", choices=[*COHORT, "all"])
    args = parser.parse_args()
    selected = args.run or args.check
    ids = list(COHORT) if args.preflight or selected == "all" else [selected]
    if args.preflight:
        results = {hypothesis_id: preflight(hypothesis_id) for hypothesis_id in ids}
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if all(row["key_envelope_passed"] for row in results.values()) else 1
    if args.check:
        results = {hypothesis_id: check_one(hypothesis_id) for hypothesis_id in ids}
    else:
        results = {hypothesis_id: run_one(hypothesis_id) for hypothesis_id in ids}
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
