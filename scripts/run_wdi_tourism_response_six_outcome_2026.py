#!/usr/bin/env python3
"""Frozen WDI tourism-demand response family with six distinct endpoints.

Only source keys were inspected before registration. All nine raw source files
must be copied and committed together in a later source-lock commit before
this runner may read selected measurements.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_tourism_response_six_outcome_family_2026_10_10"
RUNNER = "scripts/run_wdi_tourism_response_six_outcome_2026.py"
TEST = "tests/test_wdi_tourism_response_six_outcome_2026.py"
PREREG = "engine/audits/wdi_tourism_response_six_outcome_prereg_2026-10-10.md"
PARSER_ERRATUM = "engine/audits/wdi_tourism_response_parser_erratum_2026-10-10.md"
PARSER_ERRATUM_TEST = "tests/test_wdi_tourism_response_parser_erratum_2026.py"
ROSTER = "data/pinned_evidence/wdi_tourism_response_2026_key_roster.csv"
ROSTER_SHA = "018d735c2c6be4687db392b07e1872f6e5cb5fb6c8f50354f7a54f4dad09ff61"
LOCK = "data/pinned_evidence/wdi_tourism_response_six_outcome_2026.manifest.json"
SUMMARY = "engine/audits/wdi_tourism_response_six_outcome_results_2026-10-10.md"

M200056 = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
M200056_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
M203305 = "data/manifests/fetch_run_2026-05-05T203305Z.yaml"
M203305_SHA = "53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0"
M210519 = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
M210519_SHA = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"

def source(series: str, stamp: str, digest: str, manifest: str, manifest_sha: str) -> dict:
    return {"publisher": "world_bank_wdi", "series_id": series,
            "path": f"data/vintages/world_bank_wdi/{series}@{stamp}.parquet",
            "sha256": digest, "manifest": manifest, "manifest_sha256": manifest_sha}


SOURCES = {
    "arrivals": source("ST.INT.ARVL", "2026-05-05T203952Z", "1336df1cce2b3a2e784f917caa9487753d4cf53ad4ec65e5ea2fb045b0d41da5", M210519, M210519_SHA),
    "gdp_pc": source("NY.GDP.PCAP.KD", "2026-05-05T194645Z", "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f", M200056, M200056_SHA),
    "population": source("SP.POP.TOTL", "2026-05-05T194826Z", "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456", M200056, M200056_SHA),
    "employment": source("SL.EMP.TOTL.SP.ZS", "2026-05-05T194751Z", "13dd1ff36a27d38b5398196789130886c158c0d48ff0d8327567c9673bdbaeef", M200056, M200056_SHA),
    "investment": source("NE.GDI.FTOT.ZS", "2026-05-05T203056Z", "fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21", M203305, M203305_SHA),
    "registrations": source("IC.BUS.NREG", "2026-05-05T203439Z", "213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae", M210519, M210519_SHA),
    "services": source("NV.SRV.TOTL.ZS", "2026-05-05T195011Z", "3e4ecdf108553bd3449986ab0603ac062873ebc42bf40d2fa2c16dc52fc11fed", M200056, M200056_SHA),
    "inflation": source("FP.CPI.TOTL.ZG", "2026-05-05T194737Z", "dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0", M200056, M200056_SHA),
    "gdp_growth": source("NY.GDP.MKTP.KD.ZG", "2026-05-05T194655Z", "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58", M200056, M200056_SHA),
}
CASES = {
    "employment": {"id": "tourism_arrivals_adult_employment_response_forward_2026", "topic": "labour", "label": "adult employment-to-population rate", "meaningful_beta": 1.0, "unit": "percentage points", "bounds": (0.0, 100.0), "outcome_dim": "employment_labour"},
    "investment": {"id": "tourism_arrivals_fixed_investment_response_forward_2026", "topic": "growth", "label": "gross fixed capital formation share", "meaningful_beta": 0.5, "unit": "percentage points", "bounds": (0.0, 200.0), "outcome_dim": "industrial_capability"},
    "registrations": {"id": "tourism_arrivals_formal_business_entry_response_forward_2026", "topic": "growth", "label": "new formal business registrations per million residents", "meaningful_beta": 0.05, "unit": "log points", "bounds": (0.0, float("inf")), "outcome_dim": "industrial_capability"},
    "services": {"id": "tourism_arrivals_services_share_response_forward_2026", "topic": "growth", "label": "services value-added share", "meaningful_beta": 0.5, "unit": "percentage points", "bounds": (0.0, 100.0), "outcome_dim": "industrial_capability"},
    "inflation": {"id": "tourism_arrivals_inflation_response_forward_2026", "topic": "monetary", "label": "CPI inflation rate", "meaningful_beta": 0.5, "unit": "percentage points", "bounds": (-20.0, 50.0), "outcome_dim": "inflation"},
    "gdp_growth": {"id": "tourism_arrivals_gdp_growth_response_forward_2026", "topic": "growth", "label": "real GDP growth rate", "meaningful_beta": 0.5, "unit": "percentage points", "bounds": (-30.0, 30.0), "outcome_dim": "gdp_growth"},
}
T_START, T_END = 2007, 2018
EXPECTED_ROSTER_ROWS, EXPECTED_ROSTER_COUNTRIES = 2592, 216
MIN_YEARS_PER_COUNTRY = 5
MAX_ABS_LOG_CHANGE = 0.30
MATERIAL_LOG_CHANGE = 0.10
MIN_COMPLETE_ROWS, MIN_COMPLETE_COUNTRIES = 300, 25
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 60, 20
MAX_COUNTRY_RESIDUAL_SHARE = 0.20
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 6, "family_alpha": FAMILY_ALPHA, "bonferroni_p_max": P_MAX,
    "school_score_eligible": False, "school_score_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "International arrivals count inbound trips, not distinct people, spending, nights, or domestic tourism; country methods can change.",
    "Global demand, currencies, airline supply, security, policies, and domestic growth can jointly shift arrivals and outcomes.",
    "The adult employment ratio is ILO-modelled, and registrations cover formal limited-liability entities rather than all businesses or jobs.",
    "Fixed-investment share includes public and private capital; a services share can rise because other sectors shrink.",
    "Country and year effects, baseline outcomes, and forward timing do not identify a causal effect of tourism or policy.",
    "Six tests share treatment and many country-years; Bonferroni is within-family and does not adjust the broader IESET archive search.",
    "The family was selected after a visible SUPPORTED OECD youth-employment tourism-arrivals result; this informed selection of the exposure.",
    "No causal, school, policy, position, or featured credit is assigned.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(path: str) -> str:
    revisions = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"no first-addition commit for {path}")
    return revisions[-1]


def frozen(path: str, revision: str) -> None:
    candidate = ROOT / path
    if not candidate.is_file() or candidate.read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen byte mismatch: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen path: {path}")


def spec_rel(case: dict) -> str:
    return f"hypotheses/{case['topic']}/{case['id']}.yaml"


def steelman_rel(case: dict) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict) -> str:
    return f"engine/runs/{case['id']}"


def roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen key-roster hash mismatch")
    records = list(csv.DictReader((ROOT / ROSTER).open(newline="")))
    rows = [(r["country_iso3"], int(r["treatment_year"])) for r in records]
    if (len(rows) != EXPECTED_ROSTER_ROWS or len({c for c, _ in rows}) != EXPECTED_ROSTER_COUNTRIES
            or rows != sorted(rows, key=lambda z: (z[1], z[0])) or len(set(rows)) != len(rows)
            or any(not (len(c) == 3 and c.isupper() and T_START <= y <= T_END) for c, y in rows)):
        raise RuntimeError("frozen key-roster shape/order mismatch")
    return rows


def threshold_for(key: str, case: dict) -> dict:
    return {
        "family_id": FAMILY, "family_size": 6, "family_alpha": FAMILY_ALPHA,
        "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": case["meaningful_beta"], "meaningful_beta_unit": case["unit"],
        "min_complete_rows": MIN_COMPLETE_ROWS, "min_complete_countries": MIN_COMPLETE_COUNTRIES,
        "min_material_rows": MIN_MATERIAL_ROWS, "min_material_countries": MIN_MATERIAL_COUNTRIES,
        "material_abs_log_change": MATERIAL_LOG_CHANGE,
        "max_abs_treatment_log_change": MAX_ABS_LOG_CHANGE,
        "min_complete_years_per_country": MIN_YEARS_PER_COUNTRY,
        "max_top_country_residualized_exposure_share": MAX_COUNTRY_RESIDUAL_SHARE,
        "roster_sha256": ROSTER_SHA, "source_lock_path": LOCK,
        "causal_credit": 0, "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0, "featured_eligible": False,
    }


def registration_commit() -> str:
    paths = [PREREG, ROSTER, RUNNER, TEST]
    for case in CASES.values():
        paths += [spec_rel(case), steelman_rel(case)]
    revisions = {first_addition(path) for path in paths}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one first-addition commit")
    revision = revisions.pop()
    for path in paths:
        if path != RUNNER:
            frozen(path, revision)
    corrections = git("log", "--format=%H", f"{revision}..HEAD", "--", RUNNER).decode().splitlines()
    if len(corrections) != 1:
        raise RuntimeError("runner must have exactly one documented parser correction")
    correction = corrections[0]
    if (first_addition(PARSER_ERRATUM) != correction
            or first_addition(PARSER_ERRATUM_TEST) != correction):
        raise RuntimeError("parser correction lacks contemporaneous erratum and synthetic test")
    corrected_paths = set(git("diff", "--name-only", f"{correction}^", correction).decode().splitlines())
    if corrected_paths != {RUNNER, PARSER_ERRATUM, PARSER_ERRATUM_TEST}:
        raise RuntimeError("parser correction commit contains unrelated changes")
    for path in (RUNNER, PARSER_ERRATUM, PARSER_ERRATUM_TEST):
        frozen(path, correction)
    country_list = sorted({c for c, _ in roster()})
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "associational"
                or spec.get("sample", {}).get("countries") != country_list
                or spec.get("scope", {}).get("countries") != country_list
                or spec.get("falsification", {}).get("threshold") != threshold_for(key, case)
                or spec.get("steelman") != steelman_rel(case)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []):
            raise RuntimeError(f"registered spec mismatch: {key}")
        if git("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("measured result exists in registration commit")
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock already present in registration commit")
    return revision


def verify_source_manifest() -> None:
    for role, src in SOURCES.items():
        path = ROOT / src["manifest"]
        if sha256(path) != src["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest hash mismatch")
        doc = yaml.safe_load(path.read_text())
        matches = [e for e in doc.get("entries", [])
                   if e.get("publisher") == src["publisher"]
                   and e.get("series_id") == src["series_id"]
                   and e.get("parquet_path") == src["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != src["sha256"]:
            raise RuntimeError(f"{role} fetch-manifest entry mismatch")


def source_lock_commit(reg: str) -> tuple[str, dict]:
    prior_paths = []
    new_paths = []
    for src in SOURCES.values():
        path = src["path"]
        if git("ls-tree", "-r", "--name-only", reg, "--", path).strip():
            prior_paths.append(path)
        else:
            new_paths.append(path)
    revisions = {first_addition(path) for path in [LOCK] + new_paths}
    if len(revisions) != 1:
        raise RuntimeError("source lock and newly pinned raw files lack one first-addition commit")
    revision = revisions.pop()
    if revision == reg or subprocess.run(["git", "merge-base", "--is-ancestor", reg, revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock is not after registration")
    for path in [LOCK] + new_paths:
        frozen(path, revision)
    for path in prior_paths:
        frozen(path, reg)
        if git("log", "--format=%H", f"{reg}..HEAD", "--", path).strip():
            raise RuntimeError(f"prior tracked source changed after registration: {path}")
    manifest = json.loads((ROOT / LOCK).read_text())
    if manifest.get("registration_commit") != reg or manifest.get("sources") != SOURCES:
        raise RuntimeError("source-lock manifest does not match frozen source list")
    for role, src in SOURCES.items():
        if sha256(ROOT / src["path"]) != src["sha256"]:
            raise RuntimeError(f"{role} raw SHA-256 mismatch")
    verify_source_manifest()
    return revision, manifest


def normal_status(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or str(value).strip() in ("", "A")


def finite(value: object) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def load_sources() -> dict[str, dict[tuple[str, int], tuple[float | None, object]]]:
    """Read selected values only after registration and source lock checks."""
    out = {}
    allowed_countries = {country for country, _ in roster()}
    for role, src in SOURCES.items():
        frame = pd.read_parquet(ROOT / src["path"], columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
        series_ids = set(frame["indicator_id"].dropna().astype(str))
        if series_ids != {src["series_id"]}:
            raise RuntimeError(f"{role} indicator selector changed: {series_ids}")
        records = {}
        for row in frame.itertuples(index=False):
            country, _, year, value, status = row
            if country not in allowed_countries or not (T_START - 1 <= int(year) <= T_END + 1):
                continue
            key = (country, int(year))
            if key in records:
                raise RuntimeError(f"duplicate WDI country-year: {role}/{key}")
            records[key] = (finite(value), status)
        out[role] = records
    return out


def selected_value(data: dict, role: str, country: str, year: int) -> float | None:
    cell = data[role].get((country, year))
    if cell is None or not normal_status(cell[1]):
        return None
    return cell[0]


def baseline_followup(key: str, country: str, year: int, data: dict) -> tuple[float, float] | None:
    v0 = selected_value(data, key, country, year)
    v1 = selected_value(data, key, country, year + 1)
    if v0 is None or v1 is None:
        return None
    lower, upper = CASES[key]["bounds"]
    if not lower <= v0 <= upper or not lower <= v1 <= upper:
        return None
    if key == "registrations":
        p0 = selected_value(data, "population", country, year)
        p1 = selected_value(data, "population", country, year + 1)
        if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
            return None
        return (math.log1p(1e6 * v0 / p0), math.log1p(1e6 * v1 / p1))
    return v0, v1


def case_frame(key: str, data: dict) -> tuple[pd.DataFrame, dict]:
    records = []
    dropped = Counter()
    for country, year in roster():
        a0 = selected_value(data, "arrivals", country, year - 1)
        a1 = selected_value(data, "arrivals", country, year)
        gdp = selected_value(data, "gdp_pc", country, year)
        if a0 is None or a1 is None or gdp is None or a0 <= 0 or a1 <= 0 or gdp <= 0:
            dropped["missing_or_invalid_treatment_or_income"] += 1
            continue
        exposure = math.log(a1) - math.log(a0)
        if abs(exposure) > MAX_ABS_LOG_CHANGE:
            dropped["out_of_range_arrival_change"] += 1
            continue
        outcome = baseline_followup(key, country, year, data)
        if outcome is None:
            dropped["missing_or_invalid_outcome_pair"] += 1
            continue
        y0, y1 = outcome
        records.append({"country": country, "year": year, "x": exposure,
                        "baseline": y0, "log_gdp_pc": math.log(gdp), "response": y1 - y0})
    before = len(records)
    country_n = Counter(r["country"] for r in records)
    kept = [r for r in records if country_n[r["country"]] >= MIN_YEARS_PER_COUNTRY]
    frame = pd.DataFrame(kept).sort_values(["year", "country"]).reset_index(drop=True) if kept else pd.DataFrame()
    material = frame[abs(frame["x"]) >= MATERIAL_LOG_CHANGE] if len(frame) else frame
    sample = {
        "roster_rows": EXPECTED_ROSTER_ROWS,
        "complete_rows_before_five_year_country_floor": before,
        "valid_rows": len(frame), "valid_countries": int(frame["country"].nunique()) if len(frame) else 0,
        "material_exposure_rows": len(material),
        "material_exposure_countries": int(material["country"].nunique()) if len(material) else 0,
        "dropped": dict(dropped),
        "outcome_values_read_after_committed_lock": True,
    }
    return frame, sample


def fit_case(key: str, frame: pd.DataFrame, sample: dict) -> tuple[str, str, dict]:
    gates = []
    if sample["valid_rows"] < MIN_COMPLETE_ROWS or sample["valid_countries"] < MIN_COMPLETE_COUNTRIES:
        gates.append("complete_case_floor")
    if sample["material_exposure_rows"] < MIN_MATERIAL_ROWS or sample["material_exposure_countries"] < MIN_MATERIAL_COUNTRIES:
        gates.append("material_exposure_floor")
    if gates:
        return "INCONCLUSIVE", ", ".join(gates), {"gates_failed": gates}
    nuisance = patsy.dmatrix("baseline + log_gdp_pc + C(country) + C(year)", frame, return_type="dataframe").to_numpy(dtype=float)
    full = patsy.dmatrix("x + baseline + log_gdp_pc + C(country) + C(year)", frame, return_type="dataframe")
    X = full.to_numpy(dtype=float)
    if np.linalg.matrix_rank(X) != X.shape[1]:
        return "INCONCLUSIVE", "full-rank gate failed", {"gates_failed": ["full_rank"]}
    rx = sm.OLS(frame["x"].to_numpy(dtype=float), nuisance).fit().resid
    ss_by_country = pd.DataFrame({"country": frame["country"], "ss": rx * rx}).groupby("country", sort=True)["ss"].sum()
    total_ss = float(ss_by_country.sum())
    if not math.isfinite(total_ss) or total_ss <= 0:
        return "INCONCLUSIVE", "no residualized exposure", {"gates_failed": ["residual_exposure"]}
    top_share = float(ss_by_country.max() / total_ss)
    sample["top_country_residualized_exposure_share"] = top_share
    if top_share > MAX_COUNTRY_RESIDUAL_SHARE:
        return "INCONCLUSIVE", "one country dominates residualized exposure", {"gates_failed": ["residual_concentration"]}
    outcome = frame["response"].to_numpy(dtype=float)
    fit = sm.OLS(outcome, full).fit(cov_type="cluster", cov_kwds={"groups": frame["country"].to_numpy(), "use_correction": True})
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return "INCONCLUSIVE", "nonfinite country-cluster uncertainty", {"gates_failed": ["uncertainty"]}
    df = sample["valid_countries"] - 1
    p = float(2 * student_t.sf(abs(beta / se), df))
    critical = float(student_t.ppf(1 - P_MAX / 2, df))
    result = {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 1 - P_MAX, "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": sample["valid_rows"], "n_countries": sample["valid_countries"],
        "df_inference": df, "model_rank": X.shape[1],
        "top_country_residualized_exposure_share": top_share,
        "method": "country/year FE OLS with baseline outcome and GDP per person; country-cluster CR1; Student t(G-1)",
    }
    magnitude = CASES[key]["meaningful_beta"]
    if beta >= magnitude and p <= P_MAX:
        return "SUPPORTED", "positive magnitude and six-test multiplicity gates pass", result
    if beta <= -magnitude and p <= P_MAX:
        return "REFUTED", "negative magnitude and six-test multiplicity gates pass", result
    return "PARTIAL", "estimable association does not clear both directional gates", result


def artifacts(key: str, frame: pd.DataFrame, sample: dict, verdict: str, reason: str,
              result: dict, reg: str, lock_rev: str, run_utc: str) -> dict[str, bytes]:
    case = CASES[key]
    roles = ["arrivals", "gdp_pc", key] + (["population"] if key == "registrations" else [])
    input_sources = [SOURCES[role] for role in roles]
    diagnostic = {
        "hypothesis_id": case["id"], "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": reason, "run_utc": run_utc,
        "runner": RUNNER, "preregistration_commit": reg,
        "source_lock_commit": lock_rev, "source_lock": LOCK,
        "template": "panel_fe", "preflight": sample, "primary": result,
        "p_max_two_sided_bonferroni": P_MAX,
        "meaningful_beta_min_abs": case["meaningful_beta"],
        "data_status": {"variables_missing": [], "input_vintages": input_sources},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": case["id"], "run_utc": run_utc, "runner": RUNNER,
        "preregistration_commit": reg, "source_lock_commit": lock_rev,
        "source_lock": LOCK, "status": verdict, "vintages": input_sources,
        "derived_panel": sample, "correction": CORRECTION,
    }
    packet = {
        "packet_version": 1, "generated_utc": run_utc,
        "hypothesis": {"id": case["id"], "path": spec_rel(case), "topic": case["topic"]},
        "preregistration": {"spec_commit": reg, "source_lock_commit": lock_rev,
                            "family_id": FAMILY, "family_size": 6,
                            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                            "steelman": steelman_rel(case)},
        "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": {role: SOURCES[role] for role in roles}, "sample": sample},
        "results": {"primary": result}, "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    if verdict == "INCONCLUSIVE":
        finding = f"**INCONCLUSIVE.** {reason}. No directional claim is graded."
    else:
        finding = (f"**{verdict}.** The frozen descriptive coefficient is {result['coefficient']:+.5f} "
                   f"{case['unit']} per one log-point annual arrival growth (country-cluster SE "
                   f"{result['std_error']:.5f}, two-sided p={result['p_value_two_sided']:.5g}, "
                   f"{result['n_rows']} country-years, {result['n_countries']} countries). {reason}.")
    card = (f"# Tourism arrival growth and {case['label']}\n\n{finding}\n\n"
            "This is one of six pre-registered, economically distinct but data-overlapping response margins. "
            "The family was selected after a visible SUPPORTED OECD youth-employment tourism-arrivals result. "
            "Trips are not visitor spending; country/year controls and forward timing do not identify causality. "
            "Zero causal, policy, school, position, or featured credit.\n")
    chart = [{"country_iso3": str(r.country), "year": int(r.year),
              "arrival_log_change": float(r.x), "outcome_change": float(r.response)} for r in frame.itertuples()]
    coefficient = pd.DataFrame([{
        "hypothesis_id": case["id"], "term": "annual_log_arrival_change",
        "estimate": result.get("coefficient", float("nan")),
        "std_error": result.get("std_error", float("nan")),
        "p_value": result.get("p_value_two_sided", float("nan")),
    }])
    parquet = io.BytesIO()
    coefficient.to_parquet(parquet, index=False)
    replication = ("#!/usr/bin/env python3\nimport subprocess\nimport sys\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--verify']))\n")
    return {
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
        "diagnostics.json": (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(),
        "result_card.md": card.encode(),
        "chart_data.json": (json.dumps(chart, indent=2, ensure_ascii=False) + "\n").encode(),
        "coefficients.parquet": parquet.getvalue(),
        "hypothesis.yaml": (ROOT / spec_rel(case)).read_bytes(),
        "replication.py": replication.encode(),
    }


def run(verify: bool) -> None:
    reg = registration_commit()
    lock_rev, _ = source_lock_commit(reg)
    data = load_sources()
    if verify:
        prior = json.loads((ROOT / run_rel(CASES["employment"]) / "diagnostics.json").read_text())
        run_utc = prior["run_utc"]
    else:
        run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summaries = []
    for key, case in CASES.items():
        frame, sample = case_frame(key, data)
        verdict, reason, result = fit_case(key, frame, sample)
        produced = artifacts(key, frame, sample, verdict, reason, result, reg, lock_rev, run_utc)
        directory = ROOT / run_rel(case)
        if verify:
            mismatch = [name for name, content in produced.items()
                        if not (directory / name).is_file() or (directory / name).read_bytes() != content]
            if mismatch:
                raise RuntimeError(f"{case['id']} exact replay mismatch: {mismatch}")
        else:
            directory.mkdir(parents=True, exist_ok=False)
            for name, content in produced.items():
                (directory / name).write_bytes(content)
        summaries.append((case["id"], verdict, sample["valid_rows"], sample["valid_countries"], reason))
    if verify:
        print("Exact replay passed:", summaries)
        return
    lines = ["# Tourism response six-outcome family — results", "",
             f"Registration commit: `{reg}`; source-lock commit: `{lock_rev}`.",
             "All six registered outcomes remain in the Bonferroni denominator, including inconclusive cases.", "",
             "| Outcome | Verdict | Rows | Countries | Gate summary |",
             "| --- | --- | ---: | ---: | --- |"]
    for ident, verdict, rows, countries, reason in summaries:
        lines.append(f"| `{ident}` | {verdict} | {rows} | {countries} | {reason} |")
    lines += ["", "This family was selected after a visible SUPPORTED OECD youth-employment tourism-arrivals result; the six-test correction does not adjust archive-wide selection.",
              "All results are descriptive calibrations only, with zero causal, policy, school, position, or featured credit.",
              "The six response margins share treatment values and many country-years; they are not independent replications.", ""]
    (ROOT / SUMMARY).write_text("\n".join(lines))
    print(summaries)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-registration", action="store_true")
    group.add_argument("--check-source-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check_registration:
        print("registration", registration_commit())
    elif args.check_source_lock:
        reg = registration_commit()
        print("source lock", source_lock_commit(reg)[0])
    else:
        run(verify=args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
