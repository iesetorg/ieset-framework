#!/usr/bin/env python3
"""Guarded, source-pinned country holdout for remittances and modelled LFP.

--preflight reads keys, categorical metadata, and Arrow value null masks only.
--run and --check may read magnitudes only after an unchanged first-addition
preregistration commit containing the spec, steelman, runner, and four sources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ID = "remittance_share_male_prime_age_lfp_country_holdout_v2"
SPEC_REL = f"hypotheses/growth/{ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{ID}.md"
RUNNER_REL = f"scripts/run_{ID}.py"
RUN_REL = f"engine/runs/{ID}"
OLD_ID = "demo_remittance_corridor_dependency"
OLD_COMMIT = "0265cebb33d0ef5e98fd44b09a59717a89003522"
OLD_COUNTRIES = tuple("BGD EGY GTM HND IND JAM LKA MAR MEX NPL PAK PHL SLV".split())
HELD_COUNTRIES = tuple((
    "AFG AGO ALB ARG ARM AUS AUT AZE BDI BEL BEN BFA BGR BIH BLR BLZ "
    "BOL BRA BRB BTN BWA CAN CHE CHL CHN CIV CMR COD COG COL COM CPV "
    "CRI CYP CZE DEU DJI DNK DOM DZA ECU ESP EST ETH FIN FJI FRA GAB "
    "GBR GEO GHA GIN GMB GNB GRC GUY HKG HRV HTI HUN IDN IRL IRQ ISL "
    "ISR ITA JOR JPN KAZ KEN KGZ KHM KOR KWT LAO LBN LBR LCA LSO LTU "
    "LUX LVA MAC MDA MDG MDV MKD MLI MLT MMR MNE MNG MOZ MUS MWI MYS "
    "NAM NER NGA NIC NLD NOR NZL OMN PAN PER PNG POL PRT PRY PSE QAT "
    "ROU RUS RWA SAU SDN SEN SLB SLE SRB STP SUR SVK SVN SWE SWZ SYR "
    "TGO THA TJK TLS TON TTO TUN TUR TZA UGA UKR URY USA UZB VCT VUT "
    "WSM ZAF ZMB ZWE"
).split())
START_YEAR, END_YEAR = 2000, 2022
MIN_OBS, MIN_COUNTRIES, MIN_YEARS = 500, 40, 8
FAMILY_ID = "simple_measured_legacy_pair_screen_2026_10_09"
FAMILY_SIZE, FAMILY_ALPHA = 8, 0.05
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
MEANINGFUL_BETA = -0.2
PRIMARY = "personal_remittances_received_pct_gdp_at_t"
OUTCOME = "male_prime_age_lfp_pct_at_t_plus_1"
SOURCE_FILES = {
    "remittances": {
        "source": "world_bank_wdi:BX.TRF.PWKR.DT.GD.ZS",
        "path": "data/vintages/world_bank_wdi/BX.TRF.PWKR.DT.GD.ZS@2026-04-30T114721Z.parquet",
        "sha256": "9139bffa26cd6f78bf8a963400e703398b9d59919bb92ab0b2ec2b7e04885b1d",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e",
        "publisher": "world_bank_wdi", "series_id": "BX.TRF.PWKR.DT.GD.ZS",
        "indicator_id": "BX.TRF.PWKR.DT.GD.ZS",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/BX.TRF.PWKR.DT.GD.ZS?format=json",
    },
    "lfp": {
        "source": "ilostat:EAP_2WAP_SEX_AGE_RT_A",
        "path": "data/vintages/ilostat/EAP_2WAP_SEX_AGE_RT_A@2026-07-23T152621Z.parquet",
        "sha256": "17e1ed07bf963364d866304ff6384dbbfb8bc06d5ba30b42a474098c2c54e395",
        "manifest": "data/manifests/fetch_run_2026-07-23T152624Z.yaml",
        "manifest_sha256": "367fc796f8738908e3be217054f798e7684d29acee3d7304107136aecd05cdb6",
        "publisher": "ilostat", "series_id": "EAP_2WAP_SEX_AGE_RT_A",
        "physical_indicator": "EAP_2WAP_SEX_AGE_RT",
        "source_url": "https://rplumber.ilo.org/data/indicator/?id=EAP_2WAP_SEX_AGE_RT_A&format=.csv",
    },
    "gdp_ppp": {
        "source": "world_bank_wdi:NY.GDP.PCAP.PP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet",
        "sha256": "6432d570bd5e7d94d659d310c48454caedb7b105db0bfeebbe1e44189c63ecfb",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.PP.KD",
        "indicator_id": "NY.GDP.PCAP.PP.KD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.KD?format=json",
    },
    "fertility": {
        "source": "world_bank_wdi:SP.DYN.TFRT.IN",
        "path": "data/vintages/world_bank_wdi/SP.DYN.TFRT.IN@2026-04-30T130516Z.parquet",
        "sha256": "ff1eb90d4033e42ca63bb0de72c27f21044e55b69e44568d65321dd81cd8cfd1",
        "manifest": "data/manifests/fetch_run_2026-04-30T130536Z.yaml",
        "manifest_sha256": "ab56887949d3a51f3e3001ac1065c62538af1db4d4a722e39e29a774447f511b",
        "publisher": "world_bank_wdi", "series_id": "SP.DYN.TFRT.IN",
        "indicator_id": "SP.DYN.TFRT.IN",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/SP.DYN.TFRT.IN?format=json",
    },
}
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL, *(p["path"] for p in SOURCE_FILES.values()))
COEFFICIENT_COLUMNS = ("term", "coefficient", "std_error", "p_value", "ci_family",
                       "n_obs", "n_countries", "r_squared", "method")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def first_addition(relative: str) -> str:
    result = subprocess.run(["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
                            cwd=ROOT, capture_output=True, text=True)
    commits = result.stdout.strip().splitlines()
    if result.returncode or len(commits) != 1:
        raise RuntimeError(f"expected exactly one first-addition commit: {relative}")
    return commits[0]


def normalized_source(source: str) -> str:
    aliases = {
        "ilostat:EAP_2WAP_SEX_AGE_RT": "ilostat:EAP_2WAP_SEX_AGE_RT_A",
        "world_bank:BX.TRF.PWKR.DT.GD.ZS": SOURCE_FILES["remittances"]["source"],
        "wdi:BX.TRF.PWKR.DT.GD.ZS": SOURCE_FILES["remittances"]["source"],
    }
    return aliases.get(source, source)


def measured_pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(tuple(sorted({normalized_source(x["source"]) for x in variables.get(role, [])
                               if isinstance(x, dict) and isinstance(x.get("source"), str)}))
                 for role in ("treatment", "outcome"))


def verify_old() -> None:
    old = yaml.safe_load(git_show(OLD_COMMIT, f"hypotheses/growth/{OLD_ID}.yaml"))
    diagnostic = json.loads(git_show(OLD_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"))
    runner = git_show(OLD_COMMIT, "scripts/run_panel_fe.py").decode("utf-8")
    old_normalizer = runner.split("def normalise_panel(", 1)[1].split("\ndef parse_source(", 1)[0]
    estimate = diagnostic["estimate"]
    if (tuple(sorted(old["sample"]["countries"])) != OLD_COUNTRIES
            or old["variables"]["outcome"][0]["source"] != "ilostat:EAP_2WAP_SEX_AGE_RT"
            or old["variables"]["treatment"][0]["source"] != SOURCE_FILES["remittances"]["source"]
            or diagnostic.get("verdict_label") != "PARTIAL"
            or estimate.get("n_obs") != 312 or estimate.get("n_countries") != 13
            or not math.isclose(estimate.get("coefficient"), 0.07958104882532327)
            or not math.isclose(estimate.get("p_value"), 0.38016852784282396)):
        raise ValueError("archived old specification or result differs from registered history")
    if ('out = out[out["country_iso3"].isin(countries)]' not in runner
            or "panel_filt = filter_sample(panel, spec)" not in runner
            or "out = out.groupby([\"country_iso3\", \"year\"], as_index=False)[\"value\"].mean()" not in old_normalizer
            or "classif1" in old_normalizer or "SEX_M" in old_normalizer):
        raise ValueError("old country exclusion or dimension-mixing proof changed")
    if set(OLD_COUNTRIES) & set(HELD_COUNTRIES):
        raise ValueError("old fitted roster overlaps fixed holdout")
    if measured_pair(old) != ((SOURCE_FILES["remittances"]["source"],), (SOURCE_FILES["lfp"]["source"],)):
        raise ValueError("old source-pair alias differs from registered history")


def verify_spec() -> dict[str, Any]:
    verify_old()
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    threshold = spec["falsification"]["threshold"]
    expected_threshold = {
        "family_id": FAMILY_ID, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
        "family_p_max": P_MAX, "meaningful_negative_pp_per_pp": MEANINGFUL_BETA,
        "expected_sign": "-", "min_observations": MIN_OBS, "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_YEARS, "old_hypothesis_id": OLD_ID,
        "old_result_bucket": "PARTIAL", "old_primary_coefficient": 0.07958104882532327,
        "old_primary_p_value": 0.38016852784282396, "old_n_obs": 312,
        "old_n_countries": 13, "old_spec_commit": OLD_COMMIT, "old_run_commit": OLD_COMMIT,
        "old_endpoint_limitation": threshold.get("old_endpoint_limitation"),
        "old_country_ids": list(OLD_COUNTRIES), "heldout_country_count": len(HELD_COUNTRIES),
        "null_mask_pairs_upper_bound": 3220,
        "null_mask_screen": threshold.get("null_mask_screen"),
        "school_score_credit": 0, "school_score_eligible": False,
        "source_files": SOURCE_FILES,
    }
    if threshold != expected_threshold:
        raise ValueError("threshold, historical record, or source pins differ from frozen runner")
    expected_variables = {
        "outcome": [(OUTCOME, SOURCE_FILES["lfp"]["source"])],
        "treatment": [(PRIMARY, SOURCE_FILES["remittances"]["source"])],
        "controls": [("real_gdp_per_capita_ppp_at_t", SOURCE_FILES["gdp_ppp"]["source"]),
                     ("total_fertility_rate_at_t", SOURCE_FILES["fertility"]["source"])],
    }
    variables = {role: [(x["name"], x["source"]) for x in spec["variables"][role]]
                 for role in expected_variables}
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-"
            or spec["sample"]["countries"] != list(HELD_COUNTRIES)
            or spec["scope"]["countries"] != list(HELD_COUNTRIES)
            or spec["sample"]["period"] != [START_YEAR, END_YEAR]
            or spec["scope"]["period"] != [START_YEAR, END_YEAR + 1]
            or spec["estimator"]["template"] != "panel_fe"
            or spec["estimator"]["fixed_effects"] != ["country", "year"]
            or spec["estimator"]["clustering"] != "country"
            or variables != expected_variables or spec.get("steelman") != STEELMAN_REL
            or not (ROOT / STEELMAN_REL).is_file()
            or any(spec.get(key) != [] for key in ("covers_claims", "linked_hypotheses", "linked_conditions"))):
        raise ValueError("frozen design, outcome slice, or credit boundary changed")
    target = ((SOURCE_FILES["remittances"]["source"],), (SOURCE_FILES["lfp"]["source"],))
    if measured_pair(spec) != target:
        raise ValueError("registered treatment/outcome pair changed")
    for path in (ROOT / "hypotheses").rglob("*.yaml"):
        if path == ROOT / SPEC_REL:
            continue
        try:
            other = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if other.get("status") == "pre_registered" and measured_pair(other) == target:
            raise ValueError(f"alias-equivalent active preregistration already exists: {path}")
    return spec


def verify_sources() -> None:
    for role, pin in SOURCE_FILES.items():
        source = (ROOT / pin["path"]).resolve()
        manifest = (ROOT / pin["manifest"]).resolve()
        if (not source.is_relative_to(ROOT.resolve()) or not source.is_file()
                or sha256(source) != pin["sha256"]):
            raise ValueError(f"pinned source absent or changed: {role}")
        if (not manifest.is_relative_to(ROOT.resolve()) or not manifest.is_file()
                or sha256(manifest) != pin["manifest_sha256"]
                or git_show("HEAD", pin["manifest"]) != manifest.read_bytes()):
            raise ValueError(f"tracked manifest absent or changed: {role}")
        entries = yaml.safe_load(manifest.read_text(encoding="utf-8"))["entries"]
        if not any(all(row.get(key) == pin[key] for key in
                       ("publisher", "series_id", "source_url", "sha256"))
                   and row.get("parquet_path") == pin["path"] for row in entries):
            raise ValueError(f"source custody row differs: {role}")


def keyed_mask(role: str, eligible_areas: set[str]) -> set[tuple[str, int]]:
    """Use keys and validity bits, never convert a candidate magnitude to Python."""
    import pyarrow.parquet as pq
    pin = SOURCE_FILES[role]
    names = (["country_iso3", "year", "value", "indicator", "sex", "classif1", "source", "obs_status"]
             if role == "lfp" else ["country_iso3", "year", "value", "indicator_id"])
    table = pq.read_table(ROOT / pin["path"], columns=names)
    keys = table.select([name for name in names if name != "value"]).to_pydict()
    present = table.column("value").is_valid().to_pylist()
    out: set[tuple[str, int]] = set()
    seen: set[tuple[str, int]] = set()
    for i in range(table.num_rows):
        area, year = keys["country_iso3"][i], keys["year"][i]
        if area not in eligible_areas or not isinstance(year, int):
            continue
        if role == "lfp":
            if ((keys["indicator"][i], keys["sex"][i], keys["classif1"][i])
                    != ("EAP_2WAP_SEX_AGE_RT", "SEX_M", "AGE_AGGREGATE_Y25-54")
                    or not str(keys["source"][i]).startswith("XA:")
                    or keys["obs_status"][i] not in (None, "R")):
                continue
        elif keys["indicator_id"][i] != pin["indicator_id"]:
            continue
        key = (area, year)
        if key in seen:
            raise ValueError(f"duplicate selected source key: {role}, {key}")
        seen.add(key)
        if present[i]:
            out.add(key)
    return out


def preflight() -> dict[str, Any]:
    import pycountry
    verify_spec()
    verify_sources()
    eligible_areas = {country.alpha_3 for country in pycountry.countries} | {"XKX"}
    eligible_areas -= set(OLD_COUNTRIES)
    masks = {role: keyed_mask(role, eligible_areas) for role in SOURCE_FILES}
    candidate = {(area, year) for area in eligible_areas for year in range(START_YEAR, END_YEAR + 1)
                 if (area, year) in masks["remittances"]
                 and (area, year + 1) in masks["lfp"]
                 and (area, year) in masks["gdp_ppp"]
                 and (area, year) in masks["fertility"]}
    counts = Counter(area for area, _ in candidate)
    screened = tuple(sorted(area for area, count in counts.items() if count >= MIN_YEARS))
    fixed_pairs = {(area, year) for area, year in candidate if area in HELD_COUNTRIES}
    result = {
        "hypothesis_id": ID, "frozen_roster_size": len(HELD_COUNTRIES),
        "null_mask_pairs_upper_bound": len(fixed_pairs),
        "null_mask_countries_upper_bound": len({area for area, _ in fixed_pairs}),
        "all_eligible_eight_pair_roster_matches": screened == HELD_COUNTRIES,
        "old_country_overlap": len(set(HELD_COUNTRIES) & set(OLD_COUNTRIES)),
        "coverage_screen": "exact keys, categorical ILO metadata, and Arrow value validity bits only",
        "complete_case_coverage_verified": False,
        "magnitudes_inspected_by_runner": False, "coefficient_estimated": False,
        "counts_are_upper_bounds": True,
    }
    result["null_mask_envelope_passed"] = (
        result["all_eligible_eight_pair_roster_matches"]
        and result["null_mask_pairs_upper_bound"] == 3220
        and result["null_mask_countries_upper_bound"] == len(HELD_COUNTRIES)
        and result["old_country_overlap"] == 0
        and result["null_mask_pairs_upper_bound"] >= MIN_OBS
        and result["null_mask_countries_upper_bound"] >= MIN_COUNTRIES
    )
    return result


def registration_commit() -> str:
    additions = []
    for relative in REGISTRATION_FILES:
        current = (ROOT / relative).read_bytes()
        if git_show("HEAD", relative) != current:
            raise RuntimeError(f"commit unchanged preregistration before reading values: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1:
        raise RuntimeError("spec, steelman, runner, and four source files must first appear in one commit")
    commit = additions[0]
    for relative in REGISTRATION_FILES:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registered bytes changed after first addition: {relative}")
    for pin in SOURCE_FILES.values():
        if git_show(commit, pin["manifest"]) != (ROOT / pin["manifest"]).read_bytes():
            raise RuntimeError(f"source manifest changed after registration: {pin['manifest']}")
    listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", RUN_REL],
                            cwd=ROOT, capture_output=True, text=True)
    if listed.returncode or listed.stdout.strip():
        raise RuntimeError("result artifacts existed in first-addition preregistration commit")
    return commit


def annual(role: str):
    """Magnitude access: call only after registration_commit succeeds."""
    import numpy as np
    import pandas as pd
    pin = SOURCE_FILES[role]
    names = (["country_iso3", "year", "value", "obs_value", "indicator", "sex",
              "classif1", "source", "obs_status"] if role == "lfp"
             else ["country_iso3", "year", "value", "indicator_id"])
    frame = pd.read_parquet(ROOT / pin["path"], columns=names)
    frame = frame[frame["country_iso3"].isin(HELD_COUNTRIES)].copy()
    if role == "lfp":
        frame = frame[(frame["indicator"] == pin["physical_indicator"])
                      & (frame["sex"] == "SEX_M")
                      & (frame["classif1"] == "AGE_AGGREGATE_Y25-54")
                      & (frame["source"].astype(str).str.startswith("XA:"))
                      & (frame["obs_status"].isna() | (frame["obs_status"] == "R"))].copy()
        original = pd.to_numeric(frame["obs_value"], errors="coerce")
        normalized = pd.to_numeric(frame["value"], errors="coerce")
        if not np.array_equal(original.notna().to_numpy(), normalized.notna().to_numpy()):
            raise ValueError("ILO normalized value and source obs_value null masks differ")
        comparable = np.isfinite(original) & np.isfinite(normalized)
        if not np.allclose(original[comparable], normalized[comparable], rtol=0, atol=1e-9):
            raise ValueError("ILO normalized value differs from source obs_value")
    else:
        frame = frame[frame["indicator_id"] == pin["indicator_id"]].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame[frame["year"].notna()].copy()
    frame["year"] = frame["year"].astype("int64")
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate selected annual key: {role}")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame["value"])].copy()
    if role == "remittances":
        frame = frame[frame["value"] >= 0].copy()
    elif role == "lfp":
        frame = frame[frame["value"].between(0, 100, inclusive="both")].copy()
    elif role == "gdp_ppp":
        frame = frame[frame["value"] > 0].copy()
    elif role == "fertility":
        frame = frame[frame["value"] >= 0].copy()
    keep = ["country_iso3", "year", "value"] + (["obs_status"] if role == "lfp" else [])
    return frame[keep]


def build_panel():
    import numpy as np
    rem = annual("remittances").rename(columns={"value": PRIMARY})
    outcome = annual("lfp").rename(columns={"value": OUTCOME}).copy()
    outcome["year"] -= 1
    gdp = annual("gdp_ppp").rename(columns={"value": "real_gdp_per_capita_ppp_at_t"})
    fertility = annual("fertility").rename(columns={"value": "total_fertility_rate_at_t"})
    panel = rem.merge(outcome, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(gdp, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(fertility, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[panel["year"].between(START_YEAR, END_YEAR)].copy()
    panel["log_real_gdp_per_capita_ppp_at_t"] = np.log(panel["real_gdp_per_capita_ppp_at_t"])
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(
        subset=[PRIMARY, OUTCOME, "log_real_gdp_per_capita_ppp_at_t", "total_fertility_rate_at_t"])
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_YEARS].copy()
    if set(panel["country_iso3"]) & set(OLD_COUNTRIES):
        raise AssertionError("old fitted country entered holdout")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate():
    import numpy as np
    from scipy.stats import t as student_t
    import statsmodels.formula.api as smf
    panel = build_panel()
    n_countries = int(panel["country_iso3"].nunique())
    status_counts = {("blank" if key is None or key == "" else str(key)): int(value)
                     for key, value in Counter(panel["obs_status"].fillna("")).items()}
    gate = {
        "observations": int(len(panel)), "countries": n_countries,
        "min_country_years": int(panel.groupby("country_iso3")["year"].size().min()) if len(panel) else 0,
        "old_country_overlap": 0, "outcome_obs_status_counts": status_counts,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
        "outcome_year_cap": END_YEAR + 1, "outcome_measurement": "ILO modelled estimates",
    }
    gate["passed"] = (gate["observations"] >= MIN_OBS and gate["countries"] >= MIN_COUNTRIES
                      and gate["min_country_years"] >= MIN_YEARS)
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "frozen complete-case sample gate failed", None
    panel["year"] = panel["year"].astype("int64")
    formula = (f"{OUTCOME} ~ {PRIMARY} + log_real_gdp_per_capita_ppp_at_t"
               " + total_fertility_rate_at_t + C(country_iso3) + C(year)")
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"],
                                         "use_correction": True, "df_correction": True},
            use_t=True)
        if np.linalg.matrix_rank(fit.model.exog) < fit.model.exog.shape[1]:
            raise ValueError("rank-deficient primary model")
        coefficient, standard_error = float(fit.params[PRIMARY]), float(fit.bse[PRIMARY])
        if standard_error <= 0 or not all(math.isfinite(x) for x in (coefficient, standard_error)):
            raise ValueError("nonfinite or zero-uncertainty primary estimate")
        degrees_freedom = n_countries - 1
        p_value = float(2 * student_t.sf(abs(coefficient / standard_error), degrees_freedom))
        half_width = float(student_t.ppf(1 - P_MAX / 2, degrees_freedom) * standard_error)
        ci_family = [coefficient - half_width, coefficient + half_width]
        if not all(math.isfinite(x) for x in (p_value, *ci_family, float(fit.rsquared))):
            raise ValueError("nonfinite primary inference")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    if coefficient <= MEANINGFUL_BETA and p_value <= P_MAX:
        verdict, reason = "SUPPORTED", "registered meaningful-negative coefficient cleared family p cutoff"
    elif ci_family[0] > MEANINGFUL_BETA:
        verdict, reason = "REFUTED", "family confidence interval excludes registered meaningful-negative effect"
    else:
        verdict, reason = "PARTIAL", "registered directional or precision rule did not resolve the claim"
    row = {
        "coefficient": coefficient, "std_error": standard_error, "p_value": p_value,
        "ci_family": ci_family, "n_obs": len(panel), "n_countries": n_countries,
        "r_squared": float(fit.rsquared),
        "method": f"country/year FE OLS; country-clustered t({degrees_freedom}) inference",
    }
    return gate, verdict, reason, row


def expected_artifacts(commit: str, gate: dict[str, Any], verdict: str, reason: str,
                       row: dict[str, Any] | None, stamp: str):
    inputs = [{"role": role, **pin} for role, pin in SOURCE_FILES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0, "causal_credit": 0}
    limits = [
        "The archived old PARTIAL fit averaged ILO sex/age rows; it is not a male 25-54 endpoint result.",
        "This outcome is an ILO modelled estimate, not direct survey evidence; blank and R status codes are counted but not interpreted.",
        "ILO modelling may use World Bank/IMF macro inputs, so the modelled outcome is not independent of WDI predictors or controls.",
        "Reverse causation, GDP-ratio denominator changes, migration selection and country-specific trends remain.",
        "A lagged level with country/year effects is descriptive and does not identify a policy or mechanism.",
        "The eight-slot cutoff does not cure selection and multiple testing across the full IESET archive.",
        "No school, welfare, causal, or policy-score credit.",
    ]
    diagnostics = {
        "hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": commit, "template": "panel_fe", "preflight": gate,
        "estimate": row, "family_id": FAMILY_ID, "family_size": FAMILY_SIZE,
        "family_p_max": P_MAX, "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limits, "correction": correction,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": commit, "status": verdict,
        "old_hypothesis_id": OLD_ID, "old_verdict": "PARTIAL", "old_run_commit": OLD_COMMIT,
        "vintages": inputs, "derived_panel": gate, "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC_REL, "topic": "growth"},
        "preregistration": {"spec_commit": commit, "steelman": STEELMAN_REL,
                            "family_id": FAMILY_ID, "family_size": FAMILY_SIZE,
                            "family_p_max": P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --check"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": inputs, "old_country_overlap": 0,
                 "outcome_measurement": "ILO modelled estimates"},
        "results": row, "limitations": limits, "correction": correction,
    }
    card = (f"# Result card: {ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration commit: {commit}.\n"
            f"Archived old run: {OLD_ID}, PARTIAL (312 observations, 13 countries), with mixed ILO sex/age rows.\n"
            f"Held-out fit: {gate['observations']} area-year pairs, {gate['countries']} areas, zero old-area overlap.\n"
            f"Primary: exact t+1 ILO-modelled male age-25-to-54 LFP level through 2023; status counts {gate['outcome_obs_status_counts']}.\n"
            f"Eight-slot family: two-sided p <= {P_MAX}; meaningful negative beta <= {MEANINGFUL_BETA}.\n")
    if row:
        card += (f"Coefficient: {row['coefficient']:+.6g} pp LFP per pp remittance/GDP; "
                 f"clustered SE {row['std_error']:.6g}; p={row['p_value']:.6g}; "
                 f"family interval {row['ci_family']}.\n")
    card += ("\nThe old coefficient is not adopted as a male-25-to-54 result. ILO modelling can use "
             "World Bank/IMF macro inputs, so this is not independent survey validation. "
             "Descriptive calibration only; no causal, school, welfare, or policy-score credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n")
    chart = {"hypothesis_id": ID, "verdict": verdict,
             "coefficient": row["coefficient"] if row else None,
             "ci_family": row["ci_family"] if row else None,
             "family_p_max": P_MAX, "meaningful_negative": MEANINGFUL_BETA}
    coefficients = ([{"term": PRIMARY, **row}] if row else [])
    return diagnostics, manifest, packet, card, wrapper, chart, coefficients


def write_run(commit: str, gate: dict[str, Any], verdict: str, reason: str,
              row: dict[str, Any] | None) -> None:
    import pandas as pd
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    expected = expected_artifacts(commit, gate, verdict, reason, row, stamp)
    path = ROOT / RUN_REL
    path.mkdir(parents=True, exist_ok=False)
    (path / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (path / "diagnostics.json").write_text(json.dumps(expected[0], indent=2) + "\n", encoding="utf-8")
    (path / "manifest.yaml").write_text(yaml.safe_dump(expected[1], sort_keys=False), encoding="utf-8")
    (path / "evidence_packet.yaml").write_text(yaml.safe_dump(expected[2], sort_keys=False), encoding="utf-8")
    (path / "result_card.md").write_text(expected[3], encoding="utf-8")
    (path / "replication.py").write_text(expected[4], encoding="utf-8")
    (path / "chart_data.json").write_text(json.dumps(expected[5], indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(expected[6], columns=COEFFICIENT_COLUMNS).to_parquet(path / "coefficients.parquet", index=False)


def check_run(commit: str) -> dict[str, Any]:
    import pandas as pd
    path = ROOT / RUN_REL
    diagnostic = json.loads((path / "diagnostics.json").read_text(encoding="utf-8"))
    if (path / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes():
        raise AssertionError("saved hypothesis differs from registered spec")
    gate, verdict, reason, row = estimate()
    expected = expected_artifacts(commit, gate, verdict, reason, row, diagnostic["run_utc"])
    actual = [diagnostic, yaml.safe_load((path / "manifest.yaml").read_text()),
              yaml.safe_load((path / "evidence_packet.yaml").read_text()),
              (path / "result_card.md").read_text(), (path / "replication.py").read_text(),
              json.loads((path / "chart_data.json").read_text())]
    for observed, registered in zip(actual, expected[:6]):
        if observed != registered:
            raise AssertionError("saved evidence fields differ from exact semantic replay")
    table = pd.read_parquet(path / "coefficients.parquet")
    if list(table.columns) != list(COEFFICIENT_COLUMNS) or len(table) != len(expected[6]):
        raise AssertionError("coefficient table shape differs from exact semantic replay")
    for actual_row, expected_row in zip(table.to_dict(orient="records"), expected[6]):
        for key in COEFFICIENT_COLUMNS:
            if key == "ci_family":
                if (len(actual_row[key]) != len(expected_row[key])
                        or any(not math.isclose(float(a), float(b), rel_tol=1e-8, abs_tol=1e-10)
                               for a, b in zip(actual_row[key], expected_row[key]))):
                    raise AssertionError("family interval differs from replay")
            elif key in {"coefficient", "std_error", "p_value", "r_squared"}:
                if not math.isclose(float(actual_row[key]), float(expected_row[key]), rel_tol=1e-8, abs_tol=1e-10):
                    raise AssertionError(f"coefficient {key} differs from replay")
            elif actual_row[key] != expected_row[key]:
                raise AssertionError(f"coefficient {key} differs from replay")
    return {"hypothesis_id": ID, "verified": True, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = preflight()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["null_mask_envelope_passed"] else 1
    commit = registration_commit()  # This guard precedes every numeric value read.
    verify_spec()
    verify_sources()
    if args.check:
        result = check_run(commit)
    else:
        if (ROOT / RUN_REL).exists():
            raise FileExistsError(f"run already exists: {RUN_REL}")
        gate, verdict, reason, row = estimate()
        write_run(commit, gate, verdict, reason, row)
        result = {"hypothesis_id": ID, "verdict": verdict, "run_dir": RUN_REL}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
