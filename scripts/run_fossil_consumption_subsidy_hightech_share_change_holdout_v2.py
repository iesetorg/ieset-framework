#!/usr/bin/env python3
"""Source-pinned, country-disjoint descriptive fossil subsidy/high-tech share test.

--preflight reads keys and value null masks only. --run and --check can read
magnitudes only after an unchanged first-addition preregistration commit.
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
ID = "fossil_consumption_subsidy_hightech_share_change_holdout_v2"
SPEC_REL = f"hypotheses/energy/{ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{ID}.md"
RUNNER_REL = f"scripts/run_{ID}.py"
RUN_REL = f"engine/runs/{ID}"
ERRATUM_REL = f"engine/audits/{ID}_dtype_erratum_2026-10-09.json"
FAILED_ATTEMPT_REL = f"{RUN_REL}/attempts/initial_inconclusive"
FAILED_RUN_FILES = ("chart_data.json", "coefficients.parquet", "diagnostics.json",
                    "evidence_packet.yaml", "hypothesis.yaml", "manifest.yaml",
                    "replication.py", "result_card.md")
OLD_ID = "owid_fossil_subsidy_hightech_export_drag_panel"
OLD_COMMIT = "441b76cba266e45285ffc1e4bdc81dc303a88e29"
FAMILY_ID = "fossil_consumption_subsidy_hightech_share_change_2026_10_09"
OLD_COUNTRIES = tuple("ARG AUT CHN COL EGY FRA GBR GHA HUN IDN IND MEX MYS NGA PAK POL RUS SAU THA VNM ZAF".split())
HELD_COUNTRIES = tuple("AGO ARE AZE BGD BHR BOL BRN DZA ECU GAB HRV IRN KAZ KWT LKA OMN QAT SLV SVK TTO UKR UZB".split())
START_YEAR, END_YEAR = 2010, 2022
MIN_OBS, MIN_COUNTRIES, MIN_YEARS = 200, 20, 5
P_MAX = 0.01
PRIMARY = "asinh_fossil_consumption_subsidy_usd_per_resident_at_t"
SOURCE_FILES = {
    "subsidy": {
        "source": "owid:consumption-subsidies-for-fossil-fuels",
        "path": "data/vintages/owid/consumption-subsidies-for-fossil-fuels@2026-05-21T132141Z.parquet",
        "sha256": "b159daf19924d05bec517bcda656f83f92f580de0f51a890b6e2abf83211c3c3",
        "manifest": "data/manifests/fetch_run_2026-05-21T132148Z.yaml",
        "series_id": "consumption-subsidies-for-fossil-fuels",
        "source_url": "https://ourworldindata.org/grapher/consumption-subsidies-for-fossil-fuels.csv",
    },
    "population": {
        "source": "world_bank_wdi:SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "SP.POP.TOTL", "indicator_id": "SP.POP.TOTL",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json",
    },
    "hightech": {
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "path": "data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet",
        "sha256": "b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "TX.VAL.TECH.MF.ZS", "indicator_id": "TX.VAL.TECH.MF.ZS",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/TX.VAL.TECH.MF.ZS?format=json",
    },
    "gdp_pc": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NY.GDP.PCAP.KD", "indicator_id": "NY.GDP.PCAP.KD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json",
    },
}
COEFFICIENT_COLUMNS = ["term", "coefficient", "std_error", "p_value", "ci95",
                       "n_obs", "n_countries", "r_squared", "method"]


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_source(source: str) -> str:
    aliases = {
        "wits:high_tech_exports": "world_bank_wdi:TX.VAL.TECH.CD",
        "wits:high_tech_export_share": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "wdi:TX.VAL.TECH.MF.ZS": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "world_bank:TX.VAL.TECH.MF.ZS": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "wdi:SP.POP.TOTL": "world_bank_wdi:SP.POP.TOTL",
        "wdi:NY.GDP.PCAP.KD": "world_bank_wdi:NY.GDP.PCAP.KD",
    }
    return aliases.get(source, source)


def pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(tuple(sorted({normalized_source(x["source"]) for x in variables.get(role, [])
                               if isinstance(x, dict) and x.get("source")}))
                 for role in ("treatment", "outcome"))


def verify_old() -> None:
    old = yaml.safe_load(git_show(OLD_COMMIT, f"hypotheses/energy/{OLD_ID}.yaml"))
    diag = json.loads(git_show(OLD_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"))
    runner = git_show(OLD_COMMIT, "scripts/run_panel_fe.py").decode()
    if sorted(old["sample"]["countries"]) != list(OLD_COUNTRIES):
        raise ValueError("historical country roster changed")
    old_estimate = diag["estimate"]
    if (diag["verdict_label"] != "PARTIAL" or old_estimate["n_obs"] != 169
            or old_estimate["n_countries"] != 21
            or not math.isclose(old_estimate["coefficient"], 0.03031904065818789)
            or not math.isclose(old_estimate["p_value"], 0.22432307920771932)):
        raise ValueError("historical result changed")
    if ('out = out[out["country_iso3"].isin(countries)]' not in runner
            or "panel_filt = filter_sample(panel, spec)" not in runner
            or "est = run_panel_ols(\n        panel_filt," not in runner):
        raise ValueError("historical fitted-country exclusion proof unavailable")
    if set(OLD_COUNTRIES) & set(HELD_COUNTRIES):
        raise ValueError("historical and held-out country rosters overlap")
    if pair(old) != ((SOURCE_FILES["subsidy"]["source"],), ("world_bank_wdi:TX.VAL.TECH.CD",)):
        raise ValueError("historical measured pair changed")


def verify_spec() -> dict[str, Any]:
    verify_old()
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    threshold = spec["falsification"]["threshold"]
    frozen = {
        "family_id": FAMILY_ID, "family_size": 1, "family_alpha": P_MAX,
        "family_p_max": P_MAX, "expected_sign": "-",
        "min_observations": MIN_OBS, "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_YEARS,
        "old_hypothesis_id": OLD_ID, "old_result_bucket": "PARTIAL",
        "old_primary_coefficient": 0.03031904065818789,
        "old_primary_p_value": 0.22432307920771932,
        "old_n_obs": 169, "old_n_countries": 21,
        "old_spec_commit": OLD_COMMIT, "old_run_commit": OLD_COMMIT,
        "old_runner_filter_proof": "At old_run_commit, scripts/run_panel_fe.py filter_sample restricts country_iso3 to spec.sample.countries before run_panel_ols; every old fitted country is excluded.",
        "old_country_count": 21, "old_country_ids": list(OLD_COUNTRIES),
        "heldout_country_ids": list(HELD_COUNTRIES),
        "school_score_credit": 0, "school_score_eligible": False,
        "source_files": SOURCE_FILES,
    }
    if threshold != frozen:
        raise ValueError("threshold or source pins differ from guarded registration")
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-"
            or spec["sample"]["countries"] != list(HELD_COUNTRIES)
            or spec["sample"]["period"] != [START_YEAR, END_YEAR]
            or spec.get("scope", {}).get("countries") != list(HELD_COUNTRIES)
            or spec.get("steelman") != STEELMAN_REL
            or not (ROOT / STEELMAN_REL).is_file()
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []):
        raise ValueError("registration or held-out scope changed")
    actual = {role: [(x["name"], x["source"]) for x in spec["variables"][role]]
              for role in ("treatment", "outcome", "controls")}
    expected = {
        "treatment": [("fossil_consumption_subsidy_usd_per_resident_at_t", SOURCE_FILES["subsidy"]["source"]),
                      ("population_at_t", SOURCE_FILES["population"]["source"])],
        "outcome": [("next_year_change_hightech_manufactured_export_share_pp", SOURCE_FILES["hightech"]["source"])],
        "controls": [("real_gdp_per_capita_at_t", SOURCE_FILES["gdp_pc"]["source"])],
    }
    if actual != expected:
        raise ValueError("registered variables changed")
    if (spec["estimator"].get("template") != "panel_fe"
            or spec["estimator"].get("fixed_effects") != ["country", "year"]
            or spec["estimator"].get("clustering") != "country"):
        raise ValueError("estimator changed")
    target = ((SOURCE_FILES["subsidy"]["source"], SOURCE_FILES["population"]["source"]),
              (SOURCE_FILES["hightech"]["source"],))
    if pair(spec) != target:
        raise ValueError("registered source pair changed")
    for path in (ROOT / "hypotheses").rglob("*.yaml"):
        if path == ROOT / SPEC_REL:
            continue
        try:
            other = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if other.get("status") == "pre_registered" and pair(other) == target:
            raise ValueError(f"strict alias-equivalent source pair already exists: {path}")
    return spec


def verify_sources() -> None:
    for pin in SOURCE_FILES.values():
        source = (ROOT / pin["path"]).resolve()
        if not source.is_relative_to(ROOT.resolve()) or not source.is_file() or sha256(source) != pin["sha256"]:
            raise ValueError(f"pinned source absent or changed: {pin['path']}")
        manifest = yaml.safe_load((ROOT / pin["manifest"]).read_text(encoding="utf-8"))
        if not any(row.get("parquet_path") == pin["path"]
                   and all(row.get(key) == pin[key] for key in ("sha256", "series_id", "source_url"))
                   for row in manifest.get("entries", [])):
            raise ValueError(f"source not pinned in manifest: {pin['path']}")


def keyed_mask(role: str) -> set[tuple[str, int]]:
    """Read value validity bits without converting any numeric value to Python."""
    import pyarrow.parquet as pq
    pin = SOURCE_FILES[role]
    names = ["country_iso3", "year", "value"]
    if "indicator_id" in pin:
        names.append("indicator_id")
    table = pq.read_table(ROOT / pin["path"], columns=names)
    countries = table.column("country_iso3").to_pylist()
    years = table.column("year").to_pylist()
    valid = table.column("value").is_valid().to_pylist()
    indicators = table.column("indicator_id").to_pylist() if "indicator_id" in pin else None
    out: set[tuple[str, int]] = set()
    seen: set[tuple[str, int]] = set()
    for i, (country, year, present) in enumerate(zip(countries, years, valid)):
        if country not in HELD_COUNTRIES or not isinstance(year, int):
            continue
        if indicators is not None and indicators[i] != pin["indicator_id"]:
            continue
        key = (country, year)
        if key in seen:
            raise ValueError(f"duplicate pinned annual key: {role}, {key}")
        seen.add(key)
        if present:
            out.add(key)
    return out


def preflight() -> dict[str, Any]:
    verify_spec()
    verify_sources()
    masks = {role: keyed_mask(role) for role in SOURCE_FILES}
    candidate = {(country, year) for country in HELD_COUNTRIES for year in range(START_YEAR, END_YEAR + 1)
                 if (country, year) in masks["subsidy"]
                 and (country, year) in masks["population"]
                 and (country, year) in masks["hightech"]
                 and (country, year + 1) in masks["hightech"]
                 and (country, year) in masks["gdp_pc"]}
    counts = Counter(country for country, _ in candidate)
    eligible = {country for country, count in counts.items() if count >= MIN_YEARS}
    candidate = {(country, year) for country, year in candidate if country in eligible}
    result = {
        "hypothesis_id": ID, "null_mask_pairs_upper_bound": len(candidate),
        "null_mask_countries_upper_bound": len(eligible),
        "heldout_roster_size": len(HELD_COUNTRIES),
        "old_countries_excluded": len(OLD_COUNTRIES),
        "old_country_overlap": len(eligible & set(OLD_COUNTRIES)),
        "coverage_screen": "country/year keys plus Arrow value validity bits only",
        "complete_case_coverage_verified": False, "magnitudes_inspected_by_runner": False,
        "coefficient_estimated": False, "counts_are_upper_bounds": True,
    }
    result["null_mask_envelope_passed"] = (result["null_mask_pairs_upper_bound"] >= MIN_OBS
                                           and result["null_mask_countries_upper_bound"] >= MIN_COUNTRIES
                                           and result["old_country_overlap"] == 0)
    return result


def registration_commit() -> str:
    # These three previously ignored source slices must first appear with the spec.
    first_add = [SPEC_REL, STEELMAN_REL, RUNNER_REL,
                 SOURCE_FILES["subsidy"]["path"], SOURCE_FILES["population"]["path"],
                 SOURCE_FILES["hightech"]["path"]]
    additions = []
    for relative in first_add:
        current = (ROOT / relative).read_bytes()
        if relative != RUNNER_REL and git_show("HEAD", relative) != current:
            raise RuntimeError(f"commit unchanged preregistration before reading values: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1:
        raise RuntimeError("spec, steelman, runner, and three new source slices must first appear in one commit")
    commit = additions[0]
    for relative in first_add:
        if relative != RUNNER_REL and git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration bytes changed after first addition: {relative}")
    if git_show(commit, RUNNER_REL) != (ROOT / RUNNER_REL).read_bytes():
        verify_dtype_erratum(commit)
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", RUN_REL],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode or result.stdout.strip():
        raise RuntimeError("result artifacts existed in registration commit")
    return commit


def first_addition(relative: str) -> str:
    result = subprocess.run(["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
                            cwd=ROOT, capture_output=True, text=True)
    commits = result.stdout.strip().splitlines()
    if result.returncode or len(commits) != 1:
        raise RuntimeError(f"expected exactly one first-addition commit: {relative}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT, capture_output=True
    ).returncode == 0


def verify_dtype_erratum(registration: str) -> dict[str, Any]:
    """Pin the one post-failure runner version and the untouched failed attempt."""
    record_path = ROOT / ERRATUM_REL
    if not record_path.is_file():
        raise RuntimeError("dtype erratum must be committed before any corrected value read")
    record_bytes = record_path.read_bytes()
    erratum_commit = first_addition(ERRATUM_REL)
    if git_show(erratum_commit, ERRATUM_REL) != record_bytes:
        raise RuntimeError("dtype erratum record changed after first addition")
    runner_bytes = (ROOT / RUNNER_REL).read_bytes()
    if git_show(erratum_commit, RUNNER_REL) != runner_bytes:
        raise RuntimeError("corrected runner changed after dtype erratum commit")
    record = json.loads(record_bytes)
    failed_commit = record.get("failed_run_commit")
    if (record.get("schema") != "ieset-dtype-erratum-v1"
            or record.get("registration_commit") != registration
            or not isinstance(failed_commit, str)
            or record.get("corrected_runner_sha256") != hashlib.sha256(runner_bytes).hexdigest()
            or set(record.get("failed_artifact_sha256", {})) != set(FAILED_RUN_FILES)
            or not strict_ancestor(registration, failed_commit)
            or not strict_ancestor(failed_commit, erratum_commit)):
        raise RuntimeError("dtype erratum provenance or runner hash invalid")
    if git_show(erratum_commit, f"{RUN_REL}/diagnostics.json") != git_show(
            failed_commit, f"{RUN_REL}/diagnostics.json"):
        raise RuntimeError("failed canonical diagnostic changed before erratum commit")
    first_diagnostics = json.loads(git_show(failed_commit, f"{RUN_REL}/diagnostics.json"))
    if (first_diagnostics.get("verdict_label") != "INCONCLUSIVE"
            or first_diagnostics.get("estimate") is not None
            or first_diagnostics.get("preflight", {}).get("observations") != 247
            or first_diagnostics.get("preflight", {}).get("countries") != 22
            or "Int64Dtype" not in first_diagnostics.get("verdict_reason", "")):
        raise RuntimeError("first attempt was not the documented pre-estimate dtype failure")
    for name in FAILED_RUN_FILES:
        original = git_show(failed_commit, f"{RUN_REL}/{name}")
        archived = (ROOT / FAILED_ATTEMPT_REL / name).read_bytes()
        if (archived != original
                or git_show(erratum_commit, f"{FAILED_ATTEMPT_REL}/{name}") != archived
                or hashlib.sha256(original).hexdigest() != record["failed_artifact_sha256"][name]):
            raise RuntimeError(f"failed attempt archive changed: {name}")
    return record


def assert_initial_canonical(record: dict[str, Any]) -> None:
    """Allow one replacement only while the top-level files are the first failure."""
    failed_commit = record["failed_run_commit"]
    for name in FAILED_RUN_FILES:
        if (ROOT / RUN_REL / name).read_bytes() != git_show(failed_commit, f"{RUN_REL}/{name}"):
            raise RuntimeError(f"canonical run is not the recorded first attempt: {name}")


def annual(role: str):
    import numpy as np
    import pandas as pd
    pin = SOURCE_FILES[role]
    names = ["country_iso3", "year", "value"]
    if "indicator_id" in pin:
        names.append("indicator_id")
    frame = pd.read_parquet(ROOT / pin["path"], columns=names)
    frame = frame[frame["country_iso3"].isin(HELD_COUNTRIES)].copy()
    if "indicator_id" in pin:
        frame = frame[frame["indicator_id"] == pin["indicator_id"]].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate pinned annual keys: {role}")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame["value"])].copy()
    if role == "subsidy":
        frame = frame[frame["value"] >= 0].copy()
    elif role == "hightech":
        frame = frame[frame["value"].between(0, 100, inclusive="both")].copy()
    return frame[["country_iso3", "year", "value"]]


def build_panel():
    import numpy as np
    subsidy = annual("subsidy").rename(columns={"value": "subsidy_total_2023_usd"})
    population = annual("population").rename(columns={"value": "population_at_t"})
    hightech = annual("hightech")
    baseline = hightech.rename(columns={"value": "hightech_share_at_t"})
    future = hightech.rename(columns={"value": "hightech_share_at_t_plus_1"}).copy()
    future["year"] -= 1
    gdp_pc = annual("gdp_pc").rename(columns={"value": "real_gdp_per_capita_at_t"})
    panel = subsidy
    for frame in (population, baseline, future, gdp_pc):
        panel = panel.merge(frame, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[panel["year"].between(START_YEAR, END_YEAR)].copy()
    panel = panel[(panel["population_at_t"] > 0) & (panel["real_gdp_per_capita_at_t"] > 0)].copy()
    panel[PRIMARY] = np.arcsinh(panel["subsidy_total_2023_usd"] / panel["population_at_t"])
    panel["next_year_change_hightech_manufactured_export_share_pp"] = (
        panel["hightech_share_at_t_plus_1"] - panel["hightech_share_at_t"])
    panel["log_real_gdp_per_capita_at_t"] = np.log(panel["real_gdp_per_capita_at_t"])
    required = [PRIMARY, "next_year_change_hightech_manufactured_export_share_pp",
                "log_real_gdp_per_capita_at_t"]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_YEARS].copy()
    if set(panel["country_iso3"]) & set(OLD_COUNTRIES):
        raise AssertionError("historical fitted country entered holdout")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate():
    import numpy as np
    from scipy.stats import t as student_t
    import statsmodels.formula.api as smf
    panel = build_panel()
    n_countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": int(len(panel)), "countries": n_countries,
        "old_country_overlap": 0,
        "min_country_years": int(panel.groupby("country_iso3")["year"].size().min()) if len(panel) else 0,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
    }
    gate["passed"] = (gate["observations"] >= MIN_OBS and gate["countries"] >= MIN_COUNTRIES
                      and gate["min_country_years"] >= MIN_YEARS)
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "frozen complete-case sample gate failed", None
    # Pandas' nullable Int64 is an integer key but Patsy cannot build C(year) from it.
    # This changes representation only: no rows, year keys, or measured values change.
    panel["year"] = panel["year"].astype("int64")
    formula = ("next_year_change_hightech_manufactured_export_share_pp ~ " + PRIMARY
               + " + log_real_gdp_per_capita_at_t + C(country_iso3) + C(year)")
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"],
                                         "use_correction": True, "df_correction": True},
            use_t=True,
        )
        if np.linalg.matrix_rank(fit.model.exog) < fit.model.exog.shape[1]:
            raise ValueError("rank-deficient primary model")
        coefficient = float(fit.params[PRIMARY])
        std_error = float(fit.bse[PRIMARY])
        degrees_freedom = n_countries - 1
        p_value = float(2 * student_t.sf(abs(coefficient / std_error), degrees_freedom))
        half_width = float(student_t.ppf(0.975, degrees_freedom) * std_error)
        ci95 = [coefficient - half_width, coefficient + half_width]
        if std_error <= 0 or not all(math.isfinite(x) for x in (coefficient, std_error, p_value, *ci95)):
            raise ValueError("nonfinite or zero-uncertainty primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    if coefficient < 0 and p_value <= P_MAX:
        verdict, reason = "SUPPORTED", "negative coefficient cleared the frozen two-sided 0.01 rule"
    elif coefficient > 0 and p_value <= P_MAX:
        verdict, reason = "REFUTED", "positive coefficient cleared the frozen two-sided 0.01 rule"
    else:
        verdict, reason = "PARTIAL", "coefficient did not clear the frozen directional rule"
    row = {
        "coefficient": coefficient, "std_error": std_error, "p_value": p_value,
        "ci95": ci95, "n_obs": len(panel), "n_countries": n_countries,
        "r_squared": float(fit.rsquared),
        "method": f"country/year FE OLS; country-clustered t({degrees_freedom}) inference",
    }
    return gate, verdict, reason, row


def expected_artifacts(commit: str, gate: dict[str, Any], verdict: str, reason: str,
                       row: dict[str, Any] | None, stamp: str):
    inputs = [{"role": role, **pin} for role, pin in SOURCE_FILES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0}
    limits = [
        "The known old export-value result was PARTIAL, positive and nonsignificant; it was seen before this registration.",
        "The new high-tech share outcome is a proportion of manufactured exports, not export value, industrial productivity, or innovation.",
        "The old WITS export-value and new WDI export-share measures share the World Bank/WITS trade-data family; this is country-disjoint, not independent source replication.",
        "The reported 95% confidence interval is descriptive; verdicts use the frozen two-sided p<=0.01 cutoff.",
        "The 22 held-out countries are selected by source coverage and mostly resource-exporting economies; power with about 20 country clusters is limited.",
        "OWID/IEA measures explicit fossil-fuel consumption subsidies by price-gap estimates; commodity prices can alter the measure without policy change.",
        "The outcome denominator may change; observational association does not identify a subsidy policy or causal effect.",
        "No school, welfare, causal, or policy-score credit.",
        "The first registered execution hit a pandas nullable-year dtype exception before fitting; a committed technical erratum casts the same year keys to int64 and retains the first attempt byte-exact.",
    ]
    diagnostics = {
        "hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": commit, "template": "panel_fe", "preflight": gate,
        "technical_erratum": {"record": ERRATUM_REL, "failed_attempt": FAILED_ATTEMPT_REL},
        "estimate": row, "family_id": FAMILY_ID, "family_size": 1,
        "family_p_max": P_MAX, "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limits, "correction": correction,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": commit, "status": verdict,
        "technical_erratum": {"record": ERRATUM_REL, "failed_attempt": FAILED_ATTEMPT_REL},
        "old_hypothesis_id": OLD_ID, "old_verdict": "PARTIAL", "old_run_commit": OLD_COMMIT,
        "vintages": inputs, "derived_panel": gate, "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC_REL, "topic": "energy"},
        "preregistration": {"spec_commit": commit, "steelman": STEELMAN_REL,
                            "family_id": FAMILY_ID, "family_p_max": P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --check"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "technical_erratum": {"record": ERRATUM_REL, "failed_attempt": FAILED_ATTEMPT_REL},
        "data": {"inputs": inputs, "old_country_overlap": 0},
        "results": row, "limitations": limits, "correction": correction,
    }
    card = (f"# Result card: {ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Historical export-value result: {OLD_ID} (PARTIAL, p=0.224 known).\n"
            f"Preregistration commit: {commit}.\n"
            f"Held-out sample: {gate['observations']} country-year pairs, {gate['countries']} countries, zero old-country overlap.\n"
            f"Single-test threshold: two-sided p <= {P_MAX:.2f}.\n")
    if row:
        card += (f"Primary subsidy-per-resident coefficient: {row['coefficient']:+.6g}; "
                 f"clustered SE {row['std_error']:.6g}; p={row['p_value']:.6g}.\n")
    card += ("\nTechnical erratum: the first attempt hit a nullable-year dtype exception before "
             "any coefficient was estimated; its artifacts are preserved byte-exact under "
             f"{FAILED_ATTEMPT_REL}. The same year keys are cast to int64 for this replay.\n"
             "Measured association only; no causal, school, welfare, or policy-score credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n")
    chart = {"hypothesis_id": ID, "verdict": verdict,
             "coefficient": row["coefficient"] if row else None,
             "ci95": row["ci95"] if row else None, "family_p_max": P_MAX}
    coefficients = ([{"term": PRIMARY, **row}] if row else [])
    return diagnostics, manifest, packet, card, wrapper, chart, coefficients


def write_run(commit: str, gate: dict[str, Any], verdict: str, reason: str,
              row: dict[str, Any] | None, *, replace_initial: bool = False) -> None:
    import pandas as pd
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    expected = expected_artifacts(commit, gate, verdict, reason, row, stamp)
    path = ROOT / RUN_REL
    path.mkdir(parents=True, exist_ok=replace_initial)
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
    diagnostics = json.loads((path / "diagnostics.json").read_text(encoding="utf-8"))
    if (path / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes():
        raise AssertionError("stored spec differs from preregistration")
    gate, verdict, reason, row = estimate()
    if (diagnostics.get("preregistration_commit") != commit
            or diagnostics.get("preflight") != gate
            or diagnostics.get("verdict_label") != verdict
            or diagnostics.get("verdict_reason") != reason):
        raise AssertionError("rerun gate or verdict mismatch")
    expected = expected_artifacts(commit, gate, verdict, reason, row, diagnostics["run_utc"])
    artifacts = [diagnostics, yaml.safe_load((path / "manifest.yaml").read_text()),
                 yaml.safe_load((path / "evidence_packet.yaml").read_text()),
                 (path / "result_card.md").read_text(), (path / "replication.py").read_text(),
                 json.loads((path / "chart_data.json").read_text())]
    for actual, should in zip(artifacts, expected[:6]):
        if actual != should:
            raise AssertionError("stored evidence artifact mismatch")
    table = pd.read_parquet(path / "coefficients.parquet")
    if list(table.columns) != COEFFICIENT_COLUMNS or len(table) != len(expected[6]):
        raise AssertionError("stored coefficient table shape mismatch")
    for actual, should in zip(table.to_dict(orient="records"), expected[6]):
        for key in COEFFICIENT_COLUMNS:
            if key == "ci95":
                observed_ci, expected_ci = list(actual[key]), list(should[key])
                if len(observed_ci) != len(expected_ci) or any(
                    not math.isclose(float(x), float(y), rel_tol=1e-8, abs_tol=1e-10)
                    for x, y in zip(observed_ci, expected_ci)
                ):
                    raise AssertionError("stored coefficient interval mismatch")
            elif key in {"coefficient", "std_error", "p_value", "r_squared"}:
                if not math.isclose(float(actual[key]), float(should[key]), rel_tol=1e-8, abs_tol=1e-10):
                    raise AssertionError(f"stored coefficient {key} mismatch")
            elif actual[key] != should[key]:
                raise AssertionError(f"stored coefficient {key} mismatch")
    return {"hypothesis_id": ID, "verified": True, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--rerun-erratum", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = preflight()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["null_mask_envelope_passed"] else 1
    commit = registration_commit()  # Deliberately before any value-column read.
    verify_spec()
    verify_sources()
    if args.check:
        result = check_run(commit)
    else:
        if args.rerun_erratum:
            assert_initial_canonical(verify_dtype_erratum(commit))
        elif (ROOT / RUN_REL).exists():
            raise FileExistsError(f"run already exists: {RUN_REL}")
        gate, verdict, reason, row = estimate()
        write_run(commit, gate, verdict, reason, row, replace_initial=args.rerun_erratum)
        result = {"hypothesis_id": ID, "verdict": verdict, "run_dir": RUN_REL}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
