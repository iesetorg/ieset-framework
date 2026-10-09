#!/usr/bin/env python3
"""Three source-pinned, country-disjoint panel holdouts.

--preflight verifies source custody and reads only country/year keys, yielding
upper bounds on complete-case coverage. --run refuses to load outcome values
until all three specifications, steelmen, and this runner match their shared
first-addition Git preregistration commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_legacy_panel_geographic_holdouts_v2.py"
FAMILY_ID = "legacy_wdi_wgi_owid_panel_holdouts_2026_10_09"
FAMILY_P_MAX = 0.10 / 3
MIN_PAIRS_PER_COUNTRY = 5
COEFFICIENT_COLUMNS = (
    "term", "coefficient", "std_error", "p_value", "ci95", "n_obs",
    "n_countries", "r_squared", "method",
)
# Frozen ISO 3166-1 alpha-3 allowlist plus XKX. Embedded so structural CI
# imports no optional data-science package and WDI aggregates never enter.
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

# These are the complete spec.country rosters at the commits holding the old
# diagnostics. Historical versions of run_panel_fe.py filtered to these rosters
# before fitting; see the dated audit for exact commits and runner lines.
OLD_FREEDOM_COUNTRIES = frozenset(
    "ARG AUS AUT BEL BRA CAN CHL CHN CZE DEU DNK EGY ESP EST FIN FRA GBR "
    "GHA HKG HUN IDN IND IRL ITA JPN KEN KOR MEX MYS NGA NLD NOR NZL PHL "
    "POL RUS SGP SWE THA TUR USA VEN VNM ZAF".split()
)
OLD_FORTY_COUNTRIES = frozenset(
    "ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR IDN "
    "IND ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL "
    "SWE THA TUR USA VNM ZAF".split()
)

# New ID: old ID, old topic, run-artifact commit, old roster, treatment years,
# minimum pairs, minimum countries, source-role mapping, expected series.
COHORT: dict[str, dict[str, Any]] = {
    "fraser_freedom_forward_income_geographic_holdout_v2": {
        "old_id": "economic_freedom_index_income_correlation",
        "topic": "growth",
        "old_run_commit": "5c77bbcf615b19ffc7dbc085d17a05255969ddd4",
        "old_countries": OLD_FREEDOM_COUNTRIES,
        "period": [2000, 2021],
        "min_observations": 1500,
        "min_countries": 70,
        "sources": {
            "outcome": "world_bank_wdi:NY.GDP.PCAP.PP.KD",
            "treatment": "fraser_efw:aggregate_score",
            "population": "world_bank_wdi:SP.POP.TOTL",
            "trade": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "rule_of_law": "wgi:RL.EST",
            "legal_sensitivity": "fraser_efw:legal_system_property_rights",
            "sound_money_sensitivity": "fraser_efw:sound_money",
        },
        "treatment_name": "fraser_aggregate_score",
        "outcome_name": "next_year_log_real_gdp_pc_ppp_growth",
        "control_names": ["log_population", "trade_openness", "rule_of_law"],
        "old_verdict": "PARTIAL",
    },
    "private_credit_tfp_growth_geographic_holdout_v2": {
        "old_id": "financial_market_depth_productivity",
        "topic": "regulatory",
        "old_run_commit": "0265cebb33d0ef5e98fd44b09a59717a89003522",
        "old_countries": OLD_FORTY_COUNTRIES,
        "period": [1996, 2018],
        "min_observations": 1000,
        "min_countries": 50,
        "sources": {
            "outcome": "pwt:rtfpna",
            "treatment": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
            "income": "world_bank_wdi:NY.GDP.PCAP.KD",
            "rule_of_law": "wgi:RL.EST",
        },
        "treatment_name": "private_credit_pct_gdp",
        "outcome_name": "next_year_log_tfp_change",
        "control_names": ["log_gdp_pc", "rule_of_law"],
        "old_verdict": "SUPPORTED",
    },
    "services_share_female_lfp_geographic_holdout_v2": {
        "old_id": "female_lfp_market_opportunity",
        "topic": "labour",
        "old_run_commit": "f94eaa58c6579e3a48bdcca2c3db51099b1ea728",
        "old_countries": OLD_FORTY_COUNTRIES,
        "period": [1996, 2022],
        "min_observations": 2500,
        "min_countries": 100,
        "sources": {
            "outcome": "world_bank_wdi:SL.TLF.CACT.FE.ZS",
            "treatment": "world_bank_wdi:NV.SRV.TOTL.ZS",
            "income": "world_bank_wdi:NY.GDP.PCAP.KD",
            "rule_of_law": "wgi:RL.EST",
        },
        "treatment_name": "services_value_added_pct_gdp",
        "outcome_name": "next_year_female_lfp_pct",
        "control_names": ["log_gdp_pc", "rule_of_law"],
        "old_verdict": "SUPPORTED",
    },
}


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = COHORT[hypothesis_id]["topic"]
    return (
        f"hypotheses/{topic}/{hypothesis_id}.yaml",
        f"hypotheses/steelman/{hypothesis_id}.md",
        f"engine/runs/{hypothesis_id}",
    )


def git_show(revision: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{path}")
    return result.stdout


def validate_spec(hypothesis_id: str) -> dict[str, Any]:
    config = COHORT[hypothesis_id]
    spec_path, steelman_path, _ = paths(hypothesis_id)
    spec = yaml.safe_load((ROOT / spec_path).read_text(encoding="utf-8"))
    old_path = f"hypotheses/{config['topic']}/{config['old_id']}.yaml"
    old_spec = yaml.safe_load(git_show(config["old_run_commit"], old_path))
    if set(old_spec["sample"]["countries"]) != config["old_countries"]:
        raise ValueError(f"historical old-country roster changed: {hypothesis_id}")
    if spec["hypothesis_id"] != hypothesis_id or spec["status"] != "pre_registered":
        raise ValueError(f"wrong new registration: {spec_path}")
    if spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "+":
        raise ValueError(f"claim evidence or direction changed: {spec_path}")
    if spec["sample"]["period"] != config["period"] or spec["sample"]["countries"] != ["GLOBAL"]:
        raise ValueError(f"sample period or country scope changed: {spec_path}")
    excluded = set(re.findall(r"\b[A-Z]{3}\b", spec["sample"]["exclusion_rules"][0]))
    if excluded != config["old_countries"]:
        raise ValueError(f"old-country exclusion changed: {spec_path}")
    if spec["steelman"] != steelman_path or not (ROOT / steelman_path).is_file():
        raise ValueError(f"missing steelman: {steelman_path}")
    estimator = spec["estimator"]
    if estimator.get("template") != "panel_fe" or estimator.get("fixed_effects") != ["country", "year"] or estimator.get("clustering") != "country":
        raise ValueError(f"primary estimator changed: {spec_path}")
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": FAMILY_ID, "family_size": len(COHORT),
        "family_alpha": 0.10, "family_p_max": FAMILY_P_MAX,
        "expected_sign": "+", "min_observations": config["min_observations"],
        "min_countries": config["min_countries"],
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
        "old_hypothesis_id": config["old_id"],
        "old_result_bucket": config["old_verdict"],
        "old_country_count": len(config["old_countries"]),
        "old_country_ids": sorted(config["old_countries"]),
    }
    if any(threshold.get(key) != value for key, value in expected.items()):
        raise ValueError(f"family or coverage threshold changed: {spec_path}")
    if set(threshold["source_files"]) != set(config["sources"]):
        raise ValueError(f"source roles changed: {spec_path}")
    # Semantic source IDs are independent of the local file paths in the spec.
    var_sources = {
        item["name"]: item["source"]
        for block in ("outcome", "treatment", "controls")
        for item in spec["variables"].get(block, [])
    }
    if var_sources[config["outcome_name"]] != config["sources"]["outcome"]:
        raise ValueError(f"outcome source changed: {spec_path}")
    if var_sources[config["treatment_name"]] != config["sources"]["treatment"]:
        raise ValueError(f"treatment source changed: {spec_path}")
    control_roles = ({
        "log_population": "population", "trade_openness": "trade",
        "rule_of_law": "rule_of_law", "log_gdp_pc": "income",
    })
    for name in config["control_names"]:
        if var_sources.get(name) != config["sources"][control_roles[name]]:
            raise ValueError(f"control source changed: {spec_path}: {name}")
    return spec


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verified_sources(hypothesis_id: str, spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    pins = spec["falsification"]["threshold"]["source_files"]
    records = {}
    for role, source in COHORT[hypothesis_id]["sources"].items():
        pin = pins[role]
        relative = Path(pin["path"])
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError(f"missing or nonlocal source: {relative}")
        if path.suffix != ".parquet" or sha256(path) != pin["sha256"]:
            raise ValueError(f"pinned source hash mismatch: {relative}")
        records[role] = {
            "source": source, "vintage_file": str(relative), "sha256": pin["sha256"],
        }
        if hypothesis_id == "fraser_freedom_forward_income_geographic_holdout_v2" and role in {
            "treatment", "legal_sensitivity", "sound_money_sensitivity",
        }:
            records[role]["provenance_status"] = "local_vintage_pinned_derivation_unverified"
            records[role]["source_manifest"] = None
    return records


def load_keys(record: dict[str, str], old_countries: frozenset[str]) -> set[tuple[str, int]]:
    """Read country/year keys only; never load pre-registration values."""
    import pandas as pd

    frame = pd.read_parquet(ROOT / record["vintage_file"], columns=["country_iso3", "year"])
    frame = frame[
        frame["country_iso3"].isin(ISO3_COUNTRIES)
        & ~frame["country_iso3"].isin(old_countries)
    ].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame[frame["year"].notna()].copy()
    keys = list(zip(frame["country_iso3"], frame["year"].astype(int)))
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate country-year keys: {record['vintage_file']}")
    return set(keys)


def complete_keys(hypothesis_id: str, sources: dict[str, dict[str, str]]) -> set[tuple[str, int]]:
    config = COHORT[hypothesis_id]
    if hypothesis_id == "fraser_freedom_forward_income_geographic_holdout_v2":
        required = ["treatment", "population", "trade", "rule_of_law", "outcome"]
    elif hypothesis_id == "private_credit_tfp_growth_geographic_holdout_v2":
        required = ["treatment", "income", "rule_of_law", "outcome"]
    else:
        required = ["treatment", "income", "rule_of_law"]
    needed = dict.fromkeys([*required, "outcome"])
    keys = {role: load_keys(sources[role], config["old_countries"])
            for role in needed}
    outcome_at_t = {(country, year - 1) for country, year in keys["outcome"]}
    complete = outcome_at_t.intersection(*(keys[role] for role in required))
    start, end = config["period"]
    complete = {(country, year) for country, year in complete if start <= year <= end}
    counts: dict[str, int] = {}
    for country, _ in complete:
        counts[country] = counts.get(country, 0) + 1
    return {(country, year) for country, year in complete
            if counts[country] >= MIN_PAIRS_PER_COUNTRY}


def preflight(hypothesis_id: str) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    spec = validate_spec(hypothesis_id)
    sources = verified_sources(hypothesis_id, spec)
    keys = complete_keys(hypothesis_id, sources)
    countries = {country for country, _ in keys}
    years = [year for _, year in keys]
    config = COHORT[hypothesis_id]
    result = {
        "key_pairs_upper_bound": len(keys), "key_countries_upper_bound": len(countries),
        "treatment_years": [min(years), max(years)] if years else [],
        "old_countries_excluded": len(config["old_countries"]),
        "old_country_overlap": len(countries & config["old_countries"]),
        "minimum_observations": config["min_observations"],
        "minimum_countries": config["min_countries"],
        "minimum_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
        "key_envelope_passed": len(keys) >= config["min_observations"]
        and len(countries) >= config["min_countries"]
        and not (countries & config["old_countries"]),
        "complete_case_coverage_verified": False,
        "counts_are_upper_bounds": True,
        "coefficient_estimated": False,
        "outcome_values_loaded": False,
    }
    return result, sources


def registration_commit() -> str:
    """Require a complete earlier family registration before any estimation."""
    files = [RUNNER_REL]
    for hypothesis_id in COHORT:
        spec, steelman, _ = paths(hypothesis_id)
        files.extend([spec, steelman])
    for relative in files:
        if git_show("HEAD", relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"commit the entire three-test preregistration: {relative}")
    additions = []
    for relative in files:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"missing first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("commit all three registrations, steelmen, and runner together")
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
            raise RuntimeError("run artifacts must be absent from preregistration commit")
    return commit


def load_values(record: dict[str, str], old_countries: frozenset[str], name: str) -> pd.DataFrame:
    import numpy as np
    import pandas as pd

    frame = pd.read_parquet(ROOT / record["vintage_file"], columns=["country_iso3", "year", "value"])
    frame = frame[
        frame["country_iso3"].isin(ISO3_COUNTRIES)
        & ~frame["country_iso3"].isin(old_countries)
    ].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[name] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["year"].notna() & np.isfinite(frame[name])].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country-year keys: {record['vintage_file']}")
    return frame[["country_iso3", "year", name]]


def build_panel(hypothesis_id: str, sources: dict[str, dict[str, str]]) -> pd.DataFrame:
    """Outcome values are loaded only after registration_commit has succeeded."""
    import numpy as np

    config = COHORT[hypothesis_id]
    old = config["old_countries"]
    primary_roles = [role for role in sources if not role.endswith("_sensitivity")]
    source_frames = {role: load_values(sources[role], old, role) for role in primary_roles}
    outcome_next = source_frames["outcome"].copy()
    outcome_next["year"] -= 1  # Exact calendar t+1, even across data gaps.
    roles = [role for role in source_frames if role != "outcome"]
    panel = source_frames[roles[0]]
    for role in roles[1:]:
        panel = panel.merge(source_frames[role], on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(outcome_next, on=["country_iso3", "year"], validate="one_to_one")
    if hypothesis_id in {
        "fraser_freedom_forward_income_geographic_holdout_v2",
        "private_credit_tfp_growth_geographic_holdout_v2",
    }:
        panel = panel.merge(
            source_frames["outcome"].rename(columns={"outcome": "outcome_t"}),
            on=["country_iso3", "year"], validate="one_to_one",
        )
    start, end = config["period"]
    panel = panel[panel["year"].between(start, end)].copy()
    if hypothesis_id == "fraser_freedom_forward_income_geographic_holdout_v2":
        panel = panel[(panel["outcome"] > 0) & (panel["outcome_t"] > 0)
                      & (panel["population"] > 0)].copy()
        panel[config["outcome_name"]] = np.log(panel["outcome"]) - np.log(panel["outcome_t"])
        panel["log_population"] = np.log(panel["population"])
        panel["trade_openness"] = panel["trade"]
    elif hypothesis_id == "private_credit_tfp_growth_geographic_holdout_v2":
        panel = panel[(panel["outcome"] > 0) & (panel["outcome_t"] > 0)
                      & (panel["income"] > 0)].copy()
        panel[config["outcome_name"]] = np.log(panel["outcome"]) - np.log(panel["outcome_t"])
        panel["log_gdp_pc"] = np.log(panel["income"])
    else:
        panel = panel[panel["income"] > 0].copy()
        panel[config["outcome_name"]] = panel["outcome"]
        panel["log_gdp_pc"] = np.log(panel["income"])
    panel[config["treatment_name"]] = panel["treatment"]
    required = [config["outcome_name"], config["treatment_name"], *config["control_names"]]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_PAIRS_PER_COUNTRY].copy()
    if set(panel["country_iso3"]) & old:
        raise AssertionError("old and new fitted countries overlap")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def classify(coefficient: float, p_value: float) -> tuple[str, str]:
    if coefficient > 0 and p_value <= FAMILY_P_MAX:
        return "SUPPORTED", "positive association clears the three-test family threshold"
    if coefficient < 0 and p_value <= FAMILY_P_MAX:
        return "REFUTED", "negative association clears the three-test family threshold"
    return "PARTIAL", "estimable association does not clear the three-test family threshold"


def estimate_one(hypothesis_id: str, sources: dict[str, dict[str, str]]) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    import statsmodels.formula.api as smf

    config = COHORT[hypothesis_id]
    panel = build_panel(hypothesis_id, sources)
    countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": len(panel), "countries": countries,
        "old_country_overlap": 0,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
        "passed": len(panel) >= config["min_observations"] and countries >= config["min_countries"],
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "registered complete-case sample gate failed", None
    treatment = config["treatment_name"]
    controls = " + ".join(config["control_names"])
    formula = f"{config['outcome_name']} ~ {treatment} + {controls} + C(country_iso3) + C(year)"
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"], "use_correction": True}
        )
        coefficient = float(fit.params[treatment])
        std_error = float(fit.bse[treatment])
        p_value = float(fit.pvalues[treatment])
        ci95 = [float(value) for value in fit.conf_int().loc[treatment].tolist()]
        if fit.model.rank < fit.model.exog.shape[1] or not all(
            math.isfinite(value) for value in (coefficient, std_error, p_value, *ci95)
        ) or std_error <= 0:
            raise ValueError("rank-deficient or nonfinite primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    verdict, reason = classify(coefficient, p_value)
    estimate = {
        "coefficient": coefficient, "std_error": std_error, "p_value": p_value,
        "ci95": ci95, "n_obs": len(panel), "n_countries": countries,
        "r_squared": float(fit.rsquared),
        "method": "country/year FE OLS, country-clustered standard errors",
    }
    if hypothesis_id == "fraser_freedom_forward_income_geographic_holdout_v2":
        # These fixed component regressions have no verdict or claim credit.
        sensitivities = {}
        for role in ("legal_sensitivity", "sound_money_sensitivity"):
            sensitivity_n_obs = 0
            sensitivity_n_countries = 0
            sensitivity_formula = (
                f"{config['outcome_name']} ~ {role} + {controls} "
                "+ C(country_iso3) + C(year)"
            )
            try:
                component = load_values(sources[role], config["old_countries"], role)
                sensitivity_panel = panel.merge(
                    component, on=["country_iso3", "year"], validate="one_to_one",
                )
                counts = sensitivity_panel.groupby("country_iso3")["year"].transform("size")
                sensitivity_panel = sensitivity_panel[counts >= MIN_PAIRS_PER_COUNTRY].copy()
                sensitivity_n_obs = len(sensitivity_panel)
                sensitivity_n_countries = int(sensitivity_panel["country_iso3"].nunique())
                sensitivity = smf.ols(sensitivity_formula, data=sensitivity_panel).fit(
                    cov_type="cluster", cov_kwds={
                        "groups": sensitivity_panel["country_iso3"], "use_correction": True,
                    },
                )
                component_estimate = {
                    "coefficient": float(sensitivity.params[role]),
                    "std_error": float(sensitivity.bse[role]),
                    "p_value": float(sensitivity.pvalues[role]),
                }
                if not all(math.isfinite(value) for value in component_estimate.values()):
                    raise ValueError("nonfinite descriptive sensitivity estimate")
                sensitivities[role] = {
                    **component_estimate,
                    "n_obs": sensitivity_n_obs,
                    "n_countries": sensitivity_n_countries,
                    "verdict": None,
                }
            except Exception as error:
                sensitivities[role] = {
                    "error": f"{type(error).__name__}: {error}",
                    "n_obs": sensitivity_n_obs,
                    "n_countries": sensitivity_n_countries,
                    "verdict": None,
                }
        estimate["descriptive_sensitivities"] = sensitivities
    return gate, verdict, reason, estimate


def render_card(hypothesis_id: str, prereg_commit: str, gate: dict[str, Any],
                verdict: str, reason: str, estimate: dict[str, Any] | None) -> str:
    config = COHORT[hypothesis_id]
    card = (
        f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
        f"Old same-commit run: `{config['old_id']}` ({config['old_verdict']} known).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        f"Held-out sample: {gate.get('observations', 0)} country-year pairs, "
        f"{gate.get('countries', 0)} countries, zero old-country overlap.\n"
        f"Family threshold: two-sided p <= {FAMILY_P_MAX:.8f} over three tests.\n"
    )
    if estimate is not None:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; "
                 f"clustered SE {estimate['std_error']:.6g}; "
                 f"p={estimate['p_value']:.6g}.\n")
    if hypothesis_id == "fraser_freedom_forward_income_geographic_holdout_v2":
        card += "Fraser slices: local SHA-256 pinned; upstream acquisition and derivation unverified.\n"
    return card + "\nAssociation only; no causal or scoreboard claim follows automatically.\n"


def render_replication_wrapper(hypothesis_id: str) -> str:
    return (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / {RUNNER_REL!r}), '--check', {hypothesis_id!r}], cwd=root))\n"
    )


def read_coefficient_rows(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_parquet(path)
    if list(frame.columns) != list(COEFFICIENT_COLUMNS):
        raise AssertionError("stored coefficient columns mismatch")
    records = frame.to_dict(orient="records")
    return [
        {key: value.tolist() if hasattr(value, "tolist") else value
         for key, value in record.items()}
        for record in records
    ]


def assert_records_match(actual: Any, expected: Any, label: str) -> None:
    """Compare replay numerics across platforms while requiring exact structure.

    1e-8 relative and 1e-10 absolute tolerate tiny BLAS/statsmodels rounding
    changes. Country counts, sample years, labels, methods, and list lengths are
    exact; material coefficient or packet changes fail replay.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label} fields mismatch")
        for key, value in expected.items():
            assert_records_match(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            raise AssertionError(f"{label} length mismatch")
        for index, value in enumerate(expected):
            assert_records_match(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, int):
        if isinstance(actual, bool) or not isinstance(actual, int) or actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, float):
        try:
            number = float(actual)
        except (TypeError, ValueError) as error:
            raise AssertionError(f"{label} is not numeric") from error
        if not math.isfinite(number) or not math.isfinite(expected) or not math.isclose(
            number, expected, rel_tol=1e-8, abs_tol=1e-10
        ):
            raise AssertionError(f"{label} mismatch")
    elif actual != expected:
        raise AssertionError(f"{label} mismatch")


def artifact_records(hypothesis_id: str, prereg_commit: str,
                     sources: dict[str, dict[str, str]], gate: dict[str, Any],
                     verdict: str, reason: str, estimate: dict[str, Any] | None,
                     stamp: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any],
                                         str, str, dict[str, Any], list[dict[str, Any]]]:
    """Build canonical run contents in memory for writing or read-only replay."""
    spec_path, steelman_path, run_rel = paths(hypothesis_id)
    config = COHORT[hypothesis_id]
    source_list = [{"role": role, **record} for role, record in sources.items()]
    limitations = [
        "Country-disjoint association; this does not identify a causal policy effect.",
        f"The old {config['old_verdict']} result was seen before registration.",
        "The three tests share international macro sources and receive family correction.",
    ]
    if hypothesis_id == "fraser_freedom_forward_income_geographic_holdout_v2":
        limitations.append(
            "Fraser slice acquisition and derivation are unverified beyond pinned local hashes."
        )
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "panel_fe",
        "preflight": gate, "estimate": estimate, "family_id": FAMILY_ID,
        "family_size": len(COHORT), "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": source_list},
        "limitations": limitations,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": verdict,
        "old_hypothesis_id": config["old_id"], "old_verdict": config["old_verdict"],
        "old_run_commit": config["old_run_commit"], "vintages": source_list,
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_path, "topic": config["topic"]},
        "preregistration": {"spec_commit": prereg_commit, "steelman": steelman_path,
                            "family_id": FAMILY_ID, "family_p_max": FAMILY_P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": run_rel,
                         "command": f"python3 {RUNNER_REL} --check {hypothesis_id}"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": source_list, "old_country_overlap": 0},
        "results": estimate, "limitations": limitations,
    }
    card = render_card(hypothesis_id, prereg_commit, gate, verdict, reason, estimate)
    wrapper = render_replication_wrapper(hypothesis_id)
    chart = {"hypothesis_id": hypothesis_id, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None,
             "family_p_max": FAMILY_P_MAX}
    rows = ([{key: ({"term": config["treatment_name"], **estimate}).get(key)
              for key in COEFFICIENT_COLUMNS}] if estimate else [])
    return diagnostics, manifest, packet, card, wrapper, chart, rows


def write_run(hypothesis_id: str, prereg_commit: str, sources: dict[str, dict[str, str]],
              gate: dict[str, Any], verdict: str, reason: str,
              estimate: dict[str, Any] | None) -> dict[str, Any]:
    import pandas as pd

    spec_path, _, run_rel = paths(hypothesis_id)
    run_dir = ROOT / run_rel
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, wrapper, chart, rows = artifact_records(
        hypothesis_id, prereg_commit, sources, gate, verdict, reason, estimate, stamp
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "hypothesis.yaml").write_bytes((ROOT / spec_path).read_bytes())
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
    prereg_commit = registration_commit()  # Must precede any held-out value load.
    _, _, run_rel = paths(hypothesis_id)
    if (ROOT / run_rel).exists():
        raise FileExistsError(f"existing run: {run_rel}")
    spec = validate_spec(hypothesis_id)
    sources = verified_sources(hypothesis_id, spec)
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, sources)
    return write_run(hypothesis_id, prereg_commit, sources, gate, verdict, reason, estimate)


def check_one(hypothesis_id: str) -> dict[str, Any]:
    """Replay an existing result and compare it without writing any file."""
    prereg_commit = registration_commit()
    spec_path, _, run_rel = paths(hypothesis_id)
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
    if hypothesis != (ROOT / spec_path).read_bytes():
        raise AssertionError("stored hypothesis snapshot mismatch")
    spec = validate_spec(hypothesis_id)
    sources = verified_sources(hypothesis_id, spec)
    stamp = diagnostics["run_utc"]
    stored_gate = diagnostics["preflight"]
    stored_verdict = diagnostics["verdict_label"]
    stored_reason = diagnostics["verdict_reason"]
    stored_estimate = diagnostics["estimate"]
    expected = artifact_records(
        hypothesis_id, prereg_commit, sources, stored_gate,
        stored_verdict, stored_reason, stored_estimate, stamp,
    )
    expected_diagnostics, expected_manifest, expected_packet, expected_card, \
        expected_wrapper, expected_chart, expected_coefficients = expected
    assert_records_match(diagnostics, expected_diagnostics, "diagnostics")
    assert_records_match(manifest, expected_manifest, "manifest")
    assert_records_match(packet, expected_packet, "evidence_packet")
    assert_records_match(chart, expected_chart, "chart_data")
    assert_records_match(coefficients, expected_coefficients, "coefficients")
    if card != expected_card:
        raise AssertionError("result_card mismatch")
    if wrapper != expected_wrapper:
        raise AssertionError("replication wrapper mismatch")

    gate, verdict, reason, estimate = estimate_one(hypothesis_id, sources)
    assert_records_match(stored_gate, gate, "sample gate")
    assert_records_match(stored_verdict, verdict, "verdict")
    assert_records_match(stored_reason, reason, "verdict reason")
    assert_records_match(stored_estimate, estimate, "estimate")
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
        results = {hypothesis_id: preflight(hypothesis_id)[0] for hypothesis_id in ids}
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if all(result["key_envelope_passed"] for result in results.values()) else 1
    if args.check:
        results = {hypothesis_id: check_one(hypothesis_id) for hypothesis_id in ids}
    else:
        results = {hypothesis_id: run_one(hypothesis_id) for hypothesis_id in ids}
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
