#!/usr/bin/env python3
"""Four source-pinned, country-disjoint descriptive panel holdouts.

Preflight projects source dimensions and country/year keys only. Value loading
requires an unchanged first-addition preregistration commit containing all four
specs, their steelmen, and this runner, with no run artifacts in that commit.
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
RUNNER_REL = "scripts/run_fourth_legacy_panel_geographic_holdouts_v2.py"
FAMILY_ID = "fourth_legacy_panel_geographic_holdouts_2026_10_09"
FAMILY_ALPHA = 0.10
FAMILY_P_MAX = FAMILY_ALPHA / 4
MIN_PAIRS_PER_COUNTRY = 5
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
COEFFICIENT_COLUMNS = (
    "term", "coefficient", "std_error", "p_value", "ci95", "n_obs",
    "n_countries", "r_squared", "method",
)

# Every pinned byte sequence has one matching tracked fetch-manifest entry.
# WITS high-tech exports, WITS tariffs, and WIPO patents here are World Bank API
# mirrors of the stated indicator codes, not independent provider feeds.
SOURCE_FILES: dict[str, dict[str, str]] = {
    "tariff": {
        "source": "wits:weighted_mean_applied_tariff",
        "path": "data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet",
        "sha256": "73520e0da6a44048e51a64671c97369aadf160130937f351f90375fb86b0e010",
        "manifest": "data/manifests/fetch_run_2026-07-23T151550Z.yaml",
        "series_id": "weighted_mean_applied_tariff",
        "indicator_id": "TM.TAX.MRCH.WM.AR.ZS",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/TM.TAX.MRCH.WM.AR.ZS?format=json",
    },
    "private_consumption": {
        "source": "world_bank_wdi:NE.CON.PRVT.PC.KD",
        "path": "data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet",
        "sha256": "e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NE.CON.PRVT.PC.KD",
        "indicator_id": "NE.CON.PRVT.PC.KD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NE.CON.PRVT.PC.KD?format=json",
    },
    "patents": {
        "source": "wipo:patent_applications_resident",
        "path": "data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet",
        "sha256": "8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e",
        "manifest": "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
        "series_id": "patent_applications_resident",
        "indicator_id": "IP.PAT.RESD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/IP.PAT.RESD?format=json",
    },
    "hightech": {
        "source": "wits:high_tech_exports",
        "path": "data/vintages/wits/high_tech_exports@2026-07-23T153650Z.parquet",
        "sha256": "812e79d58bb1a18c4e6725639d7faec21e8302d87201cd58e1a6027bb8d30cb1",
        "manifest": "data/manifests/fetch_run_2026-07-23T153659Z.yaml",
        "series_id": "high_tech_exports",
        "indicator_id": "TX.VAL.TECH.CD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/TX.VAL.TECH.CD?format=json",
    },
    "regulatory_quality": {
        "source": "wgi:GOV_WGI_RQ.EST",
        "path": "data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet",
        "sha256": "4d8084d77990bc1d10f5630cdf8100c9ce2e1b610ade3aa7b46340fb658c8e2e",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "GOV_WGI_RQ.EST",
        "indicator_id": "GOV_WGI_RQ.EST",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/GOV_WGI_RQ.EST?format=json&source=3",
    },
    "poverty": {
        "source": "world_bank_wdi:SI.POV.DDAY",
        "path": "data/vintages/world_bank_wdi/SI.POV.DDAY@2026-05-05T194939Z.parquet",
        "sha256": "3f816fbe1a546495ff8b9adf6065bcd8a0cfec91026ce80865dafbe66bcb8b55",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "SI.POV.DDAY",
        "indicator_id": "SI.POV.DDAY",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/SI.POV.DDAY?format=json",
    },
    "migration": {
        "source": "world_bank_wdi:SM.POP.NETM",
        "path": "data/vintages/world_bank_wdi/SM.POP.NETM@2026-04-30T114756Z.parquet",
        "sha256": "8f6ca61f0ad42d02f1bbdba8966fdca38394b64651e1fba8397042580c8042be",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "series_id": "SM.POP.NETM",
        "indicator_id": "SM.POP.NETM",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/SM.POP.NETM?format=json",
    },
    "population": {
        "source": "world_bank_wdi:SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "SP.POP.TOTL",
        "indicator_id": "SP.POP.TOTL",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json",
    },
    "income": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NY.GDP.PCAP.KD",
        "indicator_id": "NY.GDP.PCAP.KD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json",
    },
    "rule_of_law": {
        "source": "wgi:RL.EST",
        "path": "data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet",
        "sha256": "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "series_id": "RL.EST",
        "indicator_id": "GOV_WGI_RL.EST",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/RL.EST?format=json&source=3",
    },
}

COHORT: dict[str, dict[str, Any]] = {
    "tariff_private_consumption_growth_holdout_v2": {
        "topic": "growth", "old_topic": "growth",
        "old_id": "market_dynamism_tariff_reduction_consumption_pc",
        "old_run_commit": "441b76cba266e45285ffc1e4bdc81dc303a88e29",
        "old_verdict": "REFUTED", "old_direction": "-", "old_n_obs": 1021,
        "old_n_countries": 39, "old_country_count": 40,
        "period": [1996, 2021], "min_observations": 500, "min_countries": 40,
        "roles": {"treatment": "tariff", "outcome": "private_consumption"},
        "treatment_name": "weighted_applied_tariff_pct",
        "outcome_name": "next_year_log_real_private_consumption_pc_growth",
        "treatment_transform": "level", "outcome_transform": "log_growth",
        "controls": [], "expected_sign": "-",
        "measurement_limit": "Weighted applied merchandise tariff is not every trade barrier; real private consumption per person is not a causal welfare estimate.",
    },
    "resident_patents_hightech_exports_growth_holdout_v2": {
        "topic": "trade", "old_topic": "trade",
        "old_id": "wipo_patent_applications_hightech_export_followthrough_panel",
        "old_run_commit": "441b76cba266e45285ffc1e4bdc81dc303a88e29",
        "old_verdict": "SUPPORTED", "old_direction": "+", "old_n_obs": 444,
        "old_n_countries": 30, "old_country_count": 30,
        "period": [1996, 2021], "min_observations": 300, "min_countries": 25,
        "roles": {"treatment": "patents", "outcome": "hightech"},
        "treatment_name": "log_one_plus_resident_patent_applications",
        "outcome_name": "next_year_log_hightech_export_value_growth",
        "treatment_transform": "log1p", "outcome_transform": "log_growth",
        "controls": [], "expected_sign": "+",
        "measurement_limit": "Patent application counts do not measure patent quality; high-tech export value is current USD and can move with prices and exchange rates. Both series are World Bank API mirrors.",
    },
    "regulatory_quality_poverty_headcount_holdout_v2": {
        "topic": "growth", "old_topic": "growth",
        "old_id": "market_reform_poverty_exit_20yr",
        "old_run_commit": "e786a95e676c9d6283c123682d43bf54dbacd73b",
        "old_verdict": "PARTIAL", "old_direction": "-", "old_n_obs": 647,
        "old_n_countries": 39, "old_country_count": 40,
        "period": [1996, 2021], "min_observations": 300, "min_countries": 30,
        "roles": {"treatment": "regulatory_quality", "outcome": "poverty",
                  "income": "income", "rule_of_law": "rule_of_law"},
        "treatment_name": "regulatory_quality_estimate",
        "outcome_name": "next_year_poverty_headcount_3usd_2021ppp_pct",
        "treatment_transform": "level", "outcome_transform": "next_level",
        "controls": ["log_income", "rule_of_law"], "expected_sign": "-",
        "measurement_limit": "WGI regulatory quality is a perception composite, not a market-reform event; the $3/day poverty ratio does not identify policy causation.",
    },
    "regulatory_quality_net_migration_rate_holdout_v2": {
        "topic": "housing", "old_topic": "housing",
        "old_id": "market_housing_supply_migration_opportunity",
        "old_run_commit": "e786a95e676c9d6283c123682d43bf54dbacd73b",
        "old_verdict": "PARTIAL", "old_direction": "+", "old_n_obs": 1000,
        "old_n_countries": 40, "old_country_count": 40,
        "period": [1996, 2021], "min_observations": 500, "min_countries": 40,
        "roles": {"treatment": "regulatory_quality", "outcome": "migration",
                  "denominator": "population", "income": "income",
                  "rule_of_law": "rule_of_law"},
        "treatment_name": "regulatory_quality_estimate",
        "outcome_name": "next_year_net_migration_per_1000_residents",
        "treatment_transform": "level", "outcome_transform": "migration_rate",
        "controls": ["log_income", "rule_of_law"], "expected_sign": "+",
        "measurement_limit": "Net migration per resident is not housing supply, migration opportunity, or migrant welfare; WGI regulatory quality is a perception composite.",
    },
}


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = COHORT[hypothesis_id]["topic"]
    return (f"hypotheses/{topic}/{hypothesis_id}.yaml",
            f"hypotheses/steelman/{hypothesis_id}.md",
            f"engine/runs/{hypothesis_id}")


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_source(source: str) -> str:
    aliases = {
        "wgi:RQ.EST": "wgi:GOV_WGI_RQ.EST",
        "wits:weighted_mean_applied_tariff": "world_bank_wdi:TM.TAX.MRCH.WM.AR.ZS",
        "wipo:patent_applications_resident": "world_bank_wdi:IP.PAT.RESD",
        "wits:high_tech_exports": "world_bank_wdi:TX.VAL.TECH.CD",
    }
    return aliases.get(source, source)


def source_pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(
        tuple(sorted({normalize_source(item["source"])
                      for item in variables.get(role, []) if isinstance(item, dict)
                      and item.get("source") and item.get("name") != "population_denominator"}))
        for role in ("treatment", "outcome")
    )


def assert_no_prior_same_pair() -> None:
    index = json.loads((ROOT / "engine/preregistration_index.json").read_text())
    registered: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = {}
    for hypothesis_id, row in index["registrations"].items():
        if row.get("status") != "verified" or hypothesis_id in COHORT:
            continue
        path = ROOT / row["path"]
        if path.is_file():
            spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            registered.setdefault(source_pair(spec), []).append(hypothesis_id)
    for hypothesis_id, config in COHORT.items():
        treatment = SOURCE_FILES[config["roles"]["treatment"]]["source"]
        outcome = SOURCE_FILES[config["roles"]["outcome"]]["source"]
        pair = ((normalize_source(treatment),), (normalize_source(outcome),))
        if registered.get(pair):
            raise ValueError(f"alias-equivalent strict source pair already exists: {hypothesis_id}: {registered[pair]}")


def validate_spec(hypothesis_id: str) -> dict[str, Any]:
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, _ = paths(hypothesis_id)
    spec = yaml.safe_load((ROOT / spec_rel).read_text(encoding="utf-8"))
    old_commit = config["old_run_commit"]
    old_spec = yaml.safe_load(git_show(
        old_commit, f"hypotheses/{config['old_topic']}/{config['old_id']}.yaml"
    ))
    old_diag = json.loads(git_show(
        old_commit, f"engine/runs/{config['old_id']}/diagnostics.json"
    ))
    old_roster = old_spec["sample"]["countries"]
    if len(old_roster) != config["old_country_count"] or len(set(old_roster)) != len(old_roster):
        raise ValueError(f"historical roster changed: {hypothesis_id}")
    historical_runner = git_show(old_commit, "scripts/run_panel_fe.py").decode()
    if ('out = out[out["country_iso3"].isin(countries)]' not in historical_runner or
            "panel_filt = filter_sample(panel, spec)" not in historical_runner or
            "est = run_panel_ols(\n        panel_filt," not in historical_runner):
        raise ValueError(f"old runner lacks fitted-country proof: {hypothesis_id}")
    for role in ("treatment", "outcome"):
        old_sources = {normalize_source(item["source"])
                       for item in old_spec["variables"][role]}
        source = SOURCE_FILES[config["roles"][role]]["source"]
        if old_sources != {normalize_source(source)}:
            raise ValueError(f"old measured source pair changed: {hypothesis_id}: {role}")
    if (old_diag["verdict_label"] != config["old_verdict"] or
            old_diag["claim_direction_inferred"] != config["old_direction"] or
            old_diag["estimate"]["n_obs"] != config["old_n_obs"] or
            old_diag["estimate"]["n_countries"] != config["old_n_countries"]):
        raise ValueError(f"historical old result changed: {hypothesis_id}")
    if (spec.get("hypothesis_id") != hypothesis_id or
            spec.get("status") != "pre_registered" or
            spec.get("evidence_type") != "associational" or
            spec.get("claim_direction") != config["expected_sign"] or
            spec.get("covers_claims") != [] or
            spec.get("linked_hypotheses") != [] or
            spec.get("linked_conditions") != [] or
            spec.get("steelman") != steelman_rel or
            not (ROOT / steelman_rel).is_file()):
        raise ValueError(f"invalid preregistration or school linkage: {spec_rel}")
    if (spec["sample"].get("countries") != ["GLOBAL"] or
            spec["sample"].get("period") != config["period"] or
            spec["sample"]["exclusion_rules"][0] !=
            "Exclude all countries in the historical old specification: " +
            " ".join(sorted(old_roster)) + "."):
        raise ValueError(f"sample or full old-roster exclusion changed: {spec_rel}")
    expected_threshold = {
        "family_id": FAMILY_ID, "family_size": len(COHORT),
        "family_alpha": FAMILY_ALPHA, "family_p_max": FAMILY_P_MAX,
        "expected_sign": config["expected_sign"],
        "min_observations": config["min_observations"],
        "min_countries": config["min_countries"],
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
        "old_hypothesis_id": config["old_id"],
        "old_result_bucket": config["old_verdict"],
        "old_claim_direction": config["old_direction"],
        "old_n_obs": config["old_n_obs"],
        "old_n_countries": config["old_n_countries"],
        "old_run_commit": old_commit,
        "old_country_count": config["old_country_count"],
        "old_country_ids": sorted(old_roster),
        "school_score_credit": 0, "school_score_eligible": False,
        "source_files": {role: SOURCE_FILES[key] for role, key in config["roles"].items()},
    }
    if spec["falsification"]["threshold"] != expected_threshold:
        raise ValueError(f"frozen rule or source custody changed: {spec_rel}")
    expected_variables = {
        "treatment": [(config["treatment_name"], SOURCE_FILES[config["roles"]["treatment"]]["source"])],
        "outcome": [(config["outcome_name"], SOURCE_FILES[config["roles"]["outcome"]]["source"])],
        "controls": [],
    }
    if "denominator" in config["roles"]:
        expected_variables["outcome"].append(
            ("population_denominator", SOURCE_FILES[config["roles"]["denominator"]]["source"])
        )
    if "log_income" in config["controls"]:
        expected_variables["controls"].append(("log_income", SOURCE_FILES["income"]["source"]))
    if "rule_of_law" in config["controls"]:
        expected_variables["controls"].append(("rule_of_law", SOURCE_FILES["rule_of_law"]["source"]))
    actual_variables = {
        role: [(item["name"], item["source"]) for item in spec["variables"].get(role, [])]
        for role in expected_variables
    }
    if actual_variables != expected_variables:
        raise ValueError(f"measured variables changed: {spec_rel}")
    if (spec["estimator"].get("template") != "panel_fe" or
            spec["estimator"].get("fixed_effects") != ["country", "year"] or
            spec["estimator"].get("clustering") != "country"):
        raise ValueError(f"estimator changed: {spec_rel}")
    return spec


def verify_sources(spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    records = {}
    for role, pin in spec["falsification"]["threshold"]["source_files"].items():
        relative = Path(pin["path"])
        source_path = (ROOT / relative).resolve()
        if (not source_path.is_relative_to(ROOT.resolve()) or not source_path.is_file()
                or source_path.suffix != ".parquet" or sha256(source_path) != pin["sha256"]):
            raise ValueError(f"missing or changed pinned source: {relative}")
        manifest = yaml.safe_load((ROOT / pin["manifest"]).read_text(encoding="utf-8"))
        if not any(
            entry.get("parquet_path") == pin["path"] and
            entry.get("sha256") == pin["sha256"] and
            entry.get("series_id") == pin["series_id"] and
            entry.get("source_url") == pin["source_url"]
            for entry in manifest.get("entries", [])
        ):
            raise ValueError(f"pin absent from tracked fetch manifest: {relative}")
        records[role] = {
            "source": pin["source"], "vintage_file": pin["path"],
            "sha256": pin["sha256"], "source_manifest": pin["manifest"],
            "indicator_id": pin["indicator_id"], "series_id": pin["series_id"],
        }
    return records


def source_frame(record: dict[str, str], *, values: bool):
    import pandas as pd

    path = ROOT / record["vintage_file"]
    columns = ["country_iso3", "year", "indicator_id"]
    if record["source"].startswith("wits:"):
        columns.append("series_id")
    if values:
        columns.append("value")
    frame = pd.read_parquet(path, columns=columns)
    frame = frame[frame["indicator_id"] == record["indicator_id"]].copy()
    if "series_id" in frame:
        frame = frame[frame["series_id"] == record["series_id"]].copy()
    frame = frame[frame["country_iso3"].isin(ISO3_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame[frame["year"].notna()].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country/year keys: {record['vintage_file']}")
    if values:
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        return frame[["country_iso3", "year", "value"]]
    return frame[["country_iso3", "year"]]


def key_envelope(hypothesis_id: str, records: dict[str, dict[str, str]]) -> set[tuple[str, int]]:
    config = COHORT[hypothesis_id]
    old = set(config["old_roster"])
    keys = {
        role: set(zip(frame["country_iso3"], frame["year"]))
        for role, record in records.items()
        for frame in [source_frame(record, values=False)]
    }
    treatment_year = set(keys["treatment"])
    for role in config["roles"]:
        if role not in {"treatment", "outcome", "denominator"}:
            treatment_year &= keys[role]
    treatment_year &= {(country, year - 1) for country, year in keys["outcome"]}
    if config["outcome_transform"] == "log_growth":
        treatment_year &= keys["outcome"]
    if "denominator" in keys:
        treatment_year &= {(country, year - 1) for country, year in keys["denominator"]}
    lo, hi = config["period"]
    treatment_year = {(country, year) for country, year in treatment_year
                      if country not in old and lo <= year <= hi}
    counts: dict[str, int] = {}
    for country, _ in treatment_year:
        counts[country] = counts.get(country, 0) + 1
    return {(country, year) for country, year in treatment_year
            if counts[country] >= MIN_PAIRS_PER_COUNTRY}


def preflight(hypothesis_id: str) -> dict[str, Any]:
    assert_no_prior_same_pair()
    spec = validate_spec(hypothesis_id)
    config = COHORT[hypothesis_id]
    config["old_roster"] = spec["falsification"]["threshold"]["old_country_ids"]
    records = verify_sources(spec)
    keys = key_envelope(hypothesis_id, records)
    countries = {country for country, _ in keys}
    years = [year for _, year in keys]
    return {
        "hypothesis_id": hypothesis_id,
        "key_pairs_upper_bound": len(keys),
        "key_countries_upper_bound": len(countries),
        "treatment_years": [min(years), max(years)] if years else [],
        "old_countries_excluded": config["old_country_count"],
        "old_country_overlap": len(countries & set(config["old_roster"])),
        "key_envelope_passed": len(keys) >= config["min_observations"] and
        len(countries) >= config["min_countries"] and
        not bool(countries & set(config["old_roster"])),
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
            raise RuntimeError(f"commit unchanged four-case preregistration before values: {relative}")
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"missing first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("all four specs, steelmen, and runner must first appear in one commit")
    commit = additions[0]
    for relative in files:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration bytes changed since first addition: {relative}")
    for hypothesis_id in COHORT:
        run_rel = paths(hypothesis_id)[2]
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit, "--", run_rel],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if result.returncode or result.stdout.strip():
            raise RuntimeError(f"run artifacts present in registration commit: {run_rel}")
    return commit


def value_frame(record: dict[str, str], role: str, old_roster: set[str]):
    import numpy as np

    frame = source_frame(record, values=True)
    frame = frame[~frame["country_iso3"].isin(old_roster)].copy()
    frame[role] = frame["value"]
    frame = frame[np.isfinite(frame[role])].copy()
    return frame[["country_iso3", "year", role]]


def build_panel(hypothesis_id: str, records: dict[str, dict[str, str]]):
    import numpy as np

    config = COHORT[hypothesis_id]
    old = set(config["old_roster"])
    frames = {role: value_frame(record, role, old) for role, record in records.items()}
    future = frames["outcome"].copy()
    future["year"] -= 1
    future = future.rename(columns={"outcome": "outcome_next"})
    panel = frames["treatment"].merge(future, on=["country_iso3", "year"], validate="one_to_one")
    if config["outcome_transform"] == "log_growth":
        panel = panel.merge(frames["outcome"], on=["country_iso3", "year"], validate="one_to_one")
        panel = panel[(panel["outcome"] > 0) & (panel["outcome_next"] > 0)].copy()
        panel[config["outcome_name"]] = np.log(panel["outcome_next"]) - np.log(panel["outcome"])
    elif config["outcome_transform"] == "migration_rate":
        denominator = frames["denominator"].copy()
        denominator["year"] -= 1
        panel = panel.merge(denominator, on=["country_iso3", "year"], validate="one_to_one")
        panel = panel[panel["denominator"] > 0].copy()
        panel[config["outcome_name"]] = 1000 * panel["outcome_next"] / panel["denominator"]
    else:
        panel = panel[panel["outcome_next"].between(0, 100)].copy()
        panel[config["outcome_name"]] = panel["outcome_next"]
    if config["treatment_transform"] == "log1p":
        panel = panel[panel["treatment"] >= 0].copy()
        panel[config["treatment_name"]] = np.log1p(panel["treatment"])
    elif hypothesis_id == "tariff_private_consumption_growth_holdout_v2":
        panel = panel[panel["treatment"] >= 0].copy()
        panel[config["treatment_name"]] = panel["treatment"]
    else:
        panel[config["treatment_name"]] = panel["treatment"]
    if "income" in frames:
        panel = panel.merge(frames["income"], on=["country_iso3", "year"], validate="one_to_one")
        panel = panel[panel["income"] > 0].copy()
        panel["log_income"] = np.log(panel["income"])
    if "rule_of_law" in frames:
        panel = panel.merge(frames["rule_of_law"], on=["country_iso3", "year"], validate="one_to_one")
    lo, hi = config["period"]
    panel = panel[panel["year"].between(lo, hi)].copy()
    required = [config["outcome_name"], config["treatment_name"], *config["controls"]]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_PAIRS_PER_COUNTRY].copy()
    if set(panel["country_iso3"]) & old:
        raise AssertionError("old fitted-country roster entered holdout")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate_one(hypothesis_id: str, records: dict[str, dict[str, str]]):
    import statsmodels.formula.api as smf

    config = COHORT[hypothesis_id]
    panel = build_panel(hypothesis_id, records)
    countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": len(panel), "countries": countries,
        "old_country_overlap": 0,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
        "passed": len(panel) >= config["min_observations"] and countries >= config["min_countries"],
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "registered complete-case sample gate failed", None
    primary = config["treatment_name"]
    rhs = " + ".join([primary, *config["controls"]])
    formula = f"{config['outcome_name']} ~ {rhs} + C(country_iso3) + C(year)"
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"], "use_correction": True}
        )
        coefficient = float(fit.params[primary])
        std_error = float(fit.bse[primary])
        p_value = float(fit.pvalues[primary])
        ci95 = [float(x) for x in fit.conf_int().loc[primary].tolist()]
        if (fit.model.rank < fit.model.exog.shape[1] or
                not all(math.isfinite(x) for x in (coefficient, std_error, p_value, *ci95)) or
                std_error <= 0):
            raise ValueError("rank-deficient or nonfinite primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    sign = 1 if config["expected_sign"] == "+" else -1
    if sign * coefficient > 0 and p_value <= FAMILY_P_MAX:
        verdict = "SUPPORTED"
        reason = "predeclared direction clears the four-test family threshold"
    elif sign * coefficient < 0 and p_value <= FAMILY_P_MAX:
        verdict = "REFUTED"
        reason = "opposite direction clears the four-test family threshold"
    else:
        verdict = "PARTIAL"
        reason = "estimable coefficient does not clear the directional family rule"
    estimate = {
        "coefficient": coefficient, "std_error": std_error, "p_value": p_value,
        "ci95": ci95, "n_obs": len(panel), "n_countries": countries,
        "r_squared": float(fit.rsquared),
        "method": "country/year FE OLS, country-clustered standard errors",
    }
    return gate, verdict, reason, estimate


def artifact_records(hypothesis_id: str, prereg_commit: str,
                     records: dict[str, dict[str, str]], gate: dict[str, Any],
                     verdict: str, reason: str, estimate: dict[str, Any] | None,
                     stamp: str):
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, run_rel = paths(hypothesis_id)
    source_list = [{"role": role, **record} for role, record in records.items()]
    limitations = [
        "Descriptive country-disjoint association, not a causal policy effect.",
        "The old same-commit result was known before this new registration.",
        "The four tests share source families and a Bonferroni correction.",
        "No school claim or position receives score credit.",
        "These holdouts may overlap other IESET studies outside the named old fit.",
        config["measurement_limit"],
    ]
    correction = {"disposition": "descriptive_calibration_only",
                  "school_score_eligible": False, "school_score_credit": 0}
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "panel_fe",
        "preflight": gate, "estimate": estimate, "family_id": FAMILY_ID,
        "family_size": len(COHORT), "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": source_list},
        "limitations": limitations, "correction": correction,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": verdict,
        "old_hypothesis_id": config["old_id"], "old_verdict": config["old_verdict"],
        "old_run_commit": config["old_run_commit"], "old_claim_direction": config["old_direction"],
        "vintages": source_list, "derived_panel": gate, "correction": correction,
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
        "results": estimate, "limitations": limitations, "correction": correction,
    }
    card = (
        f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
        f"Old same-commit run: {config['old_id']} ({config['old_verdict']} known).\n"
        f"Preregistration commit: {prereg_commit}.\n"
        f"Held-out sample: {gate['observations']} country-year pairs, "
        f"{gate['countries']} countries, zero old-country overlap.\n"
        f"Family threshold: two-sided p <= {FAMILY_P_MAX:.8f} over four tests.\n"
    )
    if estimate is not None:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; "
                 f"clustered SE {estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += ("\nMeasurement boundary: " + config["measurement_limit"] +
             "\nDescriptive calibration only. No school-score credit.\n")
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
    return [{key: value.tolist() if hasattr(value, "tolist") else value
             for key, value in row.items()} for row in frame.to_dict(orient="records")]


def write_run(hypothesis_id: str, prereg_commit: str,
              records: dict[str, dict[str, str]], gate: dict[str, Any],
              verdict: str, reason: str, estimate: dict[str, Any] | None) -> dict[str, Any]:
    import pandas as pd

    spec_rel, _, run_rel = paths(hypothesis_id)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, wrapper, chart, rows = artifact_records(
        hypothesis_id, prereg_commit, records, gate, verdict, reason, estimate, stamp
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
    pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS).to_parquet(
        run_dir / "coefficients.parquet", index=False
    )
    return {"hypothesis_id": hypothesis_id, "verdict": verdict, "run_dir": run_rel}


def run_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit()
    run_rel = paths(hypothesis_id)[2]
    if (ROOT / run_rel).exists():
        raise FileExistsError(f"existing run: {run_rel}")
    assert_no_prior_same_pair()
    spec = validate_spec(hypothesis_id)
    config = COHORT[hypothesis_id]
    config["old_roster"] = spec["falsification"]["threshold"]["old_country_ids"]
    records = verify_sources(spec)
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, records)
    return write_run(hypothesis_id, prereg_commit, records, gate, verdict, reason, estimate)


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
    coefficients = read_coefficient_rows(run_dir / "coefficients.parquet")
    if (run_dir / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel).read_bytes():
        raise AssertionError("stored spec snapshot mismatch")
    assert_no_prior_same_pair()
    spec = validate_spec(hypothesis_id)
    config = COHORT[hypothesis_id]
    config["old_roster"] = spec["falsification"]["threshold"]["old_country_ids"]
    records = verify_sources(spec)
    expected = artifact_records(
        hypothesis_id, prereg_commit, records, diagnostics["preflight"],
        diagnostics["verdict_label"], diagnostics["verdict_reason"],
        diagnostics["estimate"], diagnostics["run_utc"]
    )
    for label, actual, should in zip(
        ("diagnostics", "manifest", "evidence_packet", "chart_data", "coefficients"),
        (diagnostics, manifest, packet, chart, coefficients),
        (expected[0], expected[1], expected[2], expected[5], expected[6]),
    ):
        assert_equal(actual, should, label)
    if card != expected[3] or wrapper != expected[4]:
        raise AssertionError("stored text artifact mismatch")
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, records)
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
        rows = {hypothesis_id: preflight(hypothesis_id) for hypothesis_id in ids}
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0 if all(row["key_envelope_passed"] for row in rows.values()) else 1
    if args.check:
        rows = {hypothesis_id: check_one(hypothesis_id) for hypothesis_id in ids}
    else:
        rows = {hypothesis_id: run_one(hypothesis_id) for hypothesis_id in ids}
    print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
