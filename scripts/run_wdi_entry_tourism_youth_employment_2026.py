#!/usr/bin/env python3
"""Frozen two-test WDI exposure to OECD youth employment study.

Before separate registration and source-lock Git commits, only raw/manifest
hashes, WDI treatment values, and OECD outcome keys/dimensions/status are read.
OECD outcome values and null masks are first opened by --run or --verify after
both commits pass immutable-file and chronology guards.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_entry_tourism_oecd_youth_employment_2026_10_10"
RUNNER = "scripts/run_wdi_entry_tourism_youth_employment_2026.py"
PREREG = "engine/audits/wdi_entry_tourism_youth_employment_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_entry_tourism_youth_employment_2026_key_roster.csv"
ROSTER_SHA = "b571b45b3a94765bf1661b97908670dac88980d8598d92c43e3fdeb74449f556"
LOCK = "data/pinned_evidence/wdi_entry_tourism_youth_employment_2026.manifest.json"
SUMMARY = "engine/audits/wdi_entry_tourism_youth_employment_results_2026-10-10.md"
OUTCOME = "data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-07-23T151216Z.parquet"
ENTRY = "data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet"
TOURISM = "data/vintages/world_bank_wdi/ST.INT.ARVL@2026-05-05T203952Z.parquet"
SOURCES = {
    "outcome": {"publisher": "oecd", "series_id": "DSD_LFS_DF_LFS_INDIC",
                "path": OUTCOME, "sha256": "ac58f9ea05eb07e0d4696a81334021120cd679f58847a2fb32dc70e06074e6ae",
                "manifest": "data/manifests/fetch_run_2026-07-23T151302Z.yaml",
                "manifest_sha256": "4952688fa8fbf62df91c20409bf4180b75977bc638bb33e2a00a267b3053b601"},
    "entry": {"publisher": "world_bank_wdi", "series_id": "IC.BUS.NREG",
              "path": ENTRY, "sha256": "213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae",
              "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
              "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "tourism": {"publisher": "world_bank_wdi", "series_id": "ST.INT.ARVL",
                "path": TOURISM, "sha256": "1336df1cce2b3a2e784f917caa9487753d4cf53ad4ec65e5ea2fb045b0d41da5",
                "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
}
# All normal-status three-letter REF_AREA codes in the pinned selected outcome.
# Explicitly excludes OECD/EU/G7 aggregates and the historical DEU_F subseries.
COUNTRY_CODES = frozenset("ARG AUS AUT BEL BGR BRA CAN CHE CHL CHN COL CRI CYP CZE DEU DNK ESP EST FIN FRA GBR GRC HRV HUN IDN IND IRL ISL ISR ITA JPN KOR LTU LUX LVA MEX MKD MLT NLD NOR NZL PER POL PRT ROU RUS SVK SVN SWE THA TUR USA ZAF".split())
CASES = {
    "entry": {"id": "wdi_new_business_registrations_oecd_youth_employment_forward_2026",
              "label": "new limited-liability business registrations", "cap": 0.4,
              "key_rows": 489, "key_countries": 45, "prelock_material_rows": 175,
              "prelock_material_countries": 43, "floor": (350, 30, 100, 25),
              "meaningful_beta": 1.0},
    "tourism": {"id": "wdi_tourism_arrivals_oecd_youth_employment_forward_2026",
                "label": "international inbound arrival trips", "cap": 0.3,
                "key_rows": 564, "key_countries": 50, "prelock_material_rows": 124,
                "prelock_material_countries": 40, "floor": (400, 35, 70, 25),
                "meaningful_beta": 1.0},
}
T_START, T_END, HORIZON, MIN_YEARS = 2007, 2018, 1, 5
MATERIAL_LOG_CHANGE = 0.1
FAMILY_ALPHA, P_MAX = 0.01, 0.005
MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE = 0.30
MAX_TOP_COUNTRY_RESIDUAL_X_SHARE = 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "featured_eligible": False}
LIMITATIONS = [
    "WDI IC.BUS.NREG counts formal newly registered limited-liability corporations, not active firms, sole proprietors, informal firms, net firm creation, or jobs; registry coverage and procedures can change.",
    "WDI ST.INT.ARVL counts inbound arrival trips, not unique people or domestic tourism. Where overnight-visitor counts are unavailable, broader visitor counts may be used; border, survey, air-only, and accommodation methods differ.",
    "Both WDI treatment files have blank observation-status fields, so within-country method breaks are not identified by a quality flag; frozen log-change caps cannot repair undetected breaks.",
    "OECD 15-24 employment-to-population ratios are based on labour-force surveys; only exact normal-status A country-year endpoints are used and B series breaks or unlabeled statuses are excluded.",
    "Country/year fixed effects and one-year ordering do not identify policy or causal effects. Macroeconomic demand, migration, demography, survey changes, anticipation, and reverse timing can move treatment and employment together.",
    "Prior IESET business-entry/growth, business-freedom/employment, tourism-development, and youth-wage-gap/youth-employment studies are thematically related; this local two-test correction does not cover archive-wide selection.",
    "No causal, policy, school-score, or featured credit is permitted for either result.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/labour/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(key: str, case: dict[str, Any]) -> dict[str, Any]:
    n, countries, material, material_countries = case["floor"]
    return {"family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
            "meaningful_beta_min_abs": case["meaningful_beta"],
            "min_valid_rows": n, "min_valid_countries": countries,
            "min_material_change_rows": material,
            "min_material_change_countries": material_countries,
            "material_log_change_min_abs": MATERIAL_LOG_CHANGE,
            "max_abs_treatment_log_change": case["cap"],
            "min_years_per_country": MIN_YEARS,
            "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE,
            "max_top_country_residual_x_share": MAX_TOP_COUNTRY_RESIDUAL_X_SHARE,
            "expected_key_rows": case["key_rows"],
            "expected_key_countries": case["key_countries"],
            "roster_sha256": ROSTER_SHA,
            "source_files": {role: {field: SOURCES[role][field]
                                    for field in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role in (key, "outcome")},
            "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
            "school_score_eligible": False, "school_score_credit": 0,
            "featured_eligible": False}


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER]
    for case in CASES.values():
        frozen += [spec_rel(case), steelman_rel(case)]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec["hypothesis_id"] != case["id"] or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["steelman"] != steelman_rel(case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
                or spec["falsification"]["threshold"] != threshold_for(key, case)):
            raise RuntimeError(f"registered spec mismatch: {key}")
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contains measured results")
    return revision


def check_sources() -> dict[str, dict[str, Any]]:
    narrow = {}
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} raw SHA-256 mismatch")
        manifest_path = ROOT / source["manifest"]
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch")
        manifest = yaml.safe_load(manifest_path.read_text())
        matches = [e for e in manifest.get("entries", [])
                   if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} selected source entry mismatch")
        entry = matches[0]
        narrow[role] = {**source, "source_url": entry.get("source_url"),
                        "methodology_url": entry.get("methodology_url"),
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
                        "rows": entry.get("rows"), "frequency": entry.get("frequency"),
                        "units": entry.get("units")}
    return narrow


def load_roster() -> dict[str, list[tuple[str, int]]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"case_id,country_iso3,year\n"):
        raise RuntimeError("frozen roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    result = {key: [] for key in CASES}
    for row in records:
        if row["case_id"] not in result:
            raise RuntimeError("unexpected case in roster")
        result[row["case_id"]].append((row["country_iso3"], int(row["year"])))
    observed = [(r["case_id"], r["country_iso3"], int(r["year"])) for r in records]
    expected = [(key, c, y) for key in CASES
                for c, y in sorted(result[key], key=lambda item: (item[1], item[0]))]
    if observed != expected or len(observed) != 1053 or len(set(observed)) != len(observed):
        raise RuntimeError("frozen roster ordering, size, or uniqueness mismatch")
    for key, case in CASES.items():
        rows = result[key]
        if len(rows) != case["key_rows"] or len({c for c, _ in rows}) != case["key_countries"]:
            raise RuntimeError(f"frozen roster envelope mismatch: {key}")
    return result


def source_keys() -> tuple[dict[str, dict[tuple[str, int], float]], set[tuple[str, int]]]:
    """Read WDI treatment values and only OECD keys, dimensions and status."""
    exposures = {}
    for key in CASES:
        src = SOURCES[key]
        frame = pd.read_parquet(ROOT / src["path"], columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
        if len(frame) != 17556 or not frame.indicator_id.eq(src["series_id"]).all():
            raise RuntimeError(f"{key} WDI row or indicator contract changed")
        if not frame.obs_status.fillna("").eq("").all():
            raise RuntimeError(f"{key} treatment status semantics changed")
        frame = frame.loc[frame.country_iso3.fillna("").str.fullmatch("[A-Z]{3}")]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate {key} country-year key")
        frame = frame.loc[frame.country_iso3.isin(COUNTRY_CODES)].copy()
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame = frame.loc[np.isfinite(frame.value) & frame.value.gt(0)]
        exposures[key] = {(str(c), int(y)): float(v)
                          for c, y, v in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    outcome = pd.read_parquet(ROOT / OUTCOME, columns=["REF_AREA", "MEASURE", "UNIT_MEASURE", "SEX",
                                                       "AGE", "LABOUR_FORCE_STATUS", "period", "OBS_STATUS"])
    if len(outcome) != 535380:
        raise RuntimeError("OECD LFS raw row-count contract changed")
    outcome = outcome.loc[outcome.MEASURE.eq("EMP_RATIO") & outcome.UNIT_MEASURE.eq("PT_POP_SUB")
                          & outcome.SEX.eq("_T") & outcome.AGE.eq("Y15T24")
                          & outcome.LABOUR_FORCE_STATUS.eq("EMP")]
    valid = outcome.loc[outcome.REF_AREA.isin(COUNTRY_CODES) & outcome.OBS_STATUS.eq("A")]
    if set(valid.REF_AREA) != COUNTRY_CODES or len(valid) != 1930 or valid.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("selected normal-status country-only OECD LFS key contract changed")
    return exposures, {(str(c), int(y)) for c, y in valid[["REF_AREA", "period"]].itertuples(index=False, name=None)}


def build_roster(exposures: dict[str, dict[tuple[str, int], float]],
                 outcome_keys: set[tuple[str, int]]) -> tuple[dict[str, list[tuple[str, int]]], dict[str, dict[str, Any]]]:
    chosen = {}
    metrics = {}
    for key, case in CASES.items():
        values = exposures[key]
        candidates = []
        for (country, year), current in values.items():
            if not (T_START <= year <= T_END and (country, year - 1) in values
                    and (country, year) in outcome_keys and (country, year + HORIZON) in outcome_keys):
                continue
            log_change = float(np.log(current) - np.log(values[(country, year - 1)]))
            if abs(log_change) <= case["cap"]:
                candidates.append((country, year, log_change))
        counts = Counter(country for country, _, _ in candidates)
        rows = sorted(((country, year, delta) for country, year, delta in candidates
                       if counts[country] >= MIN_YEARS), key=lambda item: (item[1], item[0]))
        material = [(c, y) for c, y, delta in rows if abs(delta) >= MATERIAL_LOG_CHANGE]
        selected = [(c, y) for c, y, _ in rows]
        treatment_only_panel = pd.DataFrame(
            [{"country_iso3": c, "year": y, "treatment_log_change": delta}
             for c, y, delta in rows])
        shares = concentration(treatment_only_panel)
        if (shares is None or shares[0] > MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE
                or shares[1] > MAX_TOP_COUNTRY_RESIDUAL_X_SHARE):
            raise RuntimeError(f"{key} prelock treatment concentration gate failed")
        if (len(selected) != case["key_rows"]
                or len({c for c, _ in selected}) != case["key_countries"]
                or len(material) != case["prelock_material_rows"]
                or len({c for c, _ in material}) != case["prelock_material_countries"]):
            raise RuntimeError(f"{key} treatment-only key or material envelope changed")
        chosen[key] = selected
        metrics[key] = {"key_rows": len(selected), "key_countries": len({c for c, _ in selected}),
                        "t_years": [min(y for _, y in selected), max(y for _, y in selected)],
                        "treatment_only_material_rows": len(material),
                        "treatment_only_material_countries": len({c for c, _ in material}),
                        "treatment_only_top_one_percent_residual_x_share": shares[0],
                        "treatment_only_top_country_residual_x_share": shares[1],
                        "treatment_log_change_cap": case["cap"]}
    return chosen, metrics


def key_preflight() -> dict[str, Any]:
    exposures, outcomes = source_keys()
    generated, metrics = build_roster(exposures, outcomes)
    frozen = load_roster()
    if generated != frozen:
        raise RuntimeError("source key preflight differs from frozen roster")
    return {"treatment_values_read": True, "outcome_values_read": False,
            "outcome_null_masks_read": False, "outcome_status_read": True,
            "outcome_status_selector": "A at t and t+1", "exact_year_join": True,
            "roster_sha256": ROSTER_SHA, "cases": metrics}


def lock_payload(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    revision = registration_commit()
    narrow = check_sources()
    preflight = key_preflight()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(revision, narrow, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening OECD outcome values")


def check_source_lock(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, narrow, preflight):
        raise RuntimeError("source lock differs from preregistration, raw pins, or preflight")
    commit = first_addition(LOCK)
    if commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return commit


def finite_pct(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(numeric) or not 0 <= numeric <= 100:
        return None
    return numeric


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First outcome-value/null access; caller has verified registration and lock commits."""
    exposures, _ = source_keys()
    outcome = pd.read_parquet(ROOT / OUTCOME, columns=["REF_AREA", "MEASURE", "UNIT_MEASURE", "SEX",
                                                     "AGE", "LABOUR_FORCE_STATUS", "period", "OBS_STATUS", "value"])
    outcome = outcome.loc[outcome.MEASURE.eq("EMP_RATIO") & outcome.UNIT_MEASURE.eq("PT_POP_SUB")
                          & outcome.SEX.eq("_T") & outcome.AGE.eq("Y15T24")
                          & outcome.LABOUR_FORCE_STATUS.eq("EMP") & outcome.OBS_STATUS.eq("A")
                          & outcome.REF_AREA.isin(COUNTRY_CODES)]
    if outcome.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate selected OECD outcome key")
    youth = {(str(c), int(y)): finite_pct(v)
             for c, y, v in outcome[["REF_AREA", "period", "value"]].itertuples(index=False, name=None)}
    panels = {}
    for key, case in CASES.items():
        rows = []
        missing = 0
        for country, year in roster[key]:
            baseline, forward = youth.get((country, year)), youth.get((country, year + HORIZON))
            if baseline is None or forward is None:
                missing += 1
                continue
            x = float(np.log(exposures[key][(country, year)]) - np.log(exposures[key][(country, year - 1)]))
            rows.append({"country_iso3": country, "year": year,
                         "treatment_log_change": x, "youth_employment_forward_change_pp": forward - baseline})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "treatment_log_change",
                                            "youth_employment_forward_change_pp"])
        before = len(panel)
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        material = panel.treatment_log_change.abs().ge(MATERIAL_LOG_CHANGE)
        gate = {"roster_rows": len(roster[key]), "dropped_missing_or_invalid_outcome_endpoint_pairs": missing,
                "complete_pairs_before_five_year_country_floor": before,
                "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
                "material_change_rows": int(material.sum()),
                "material_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
                "outcome_values_read_after_lock": True}
        panels[key] = panel, gate
    return panels


def concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    fit = smf.ols("treatment_log_change ~ C(country_iso3) + C(year)", data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * len(squared)))
    top_row_share = float(np.sort(squared)[-top_n:].sum() / total)
    grouped = pd.DataFrame({"country_iso3": panel.country_iso3.to_numpy(), "squared": squared})
    top_country_share = float(grouped.groupby("country_iso3").squared.sum().max() / total)
    return top_row_share, top_country_share


def estimate(panel: pd.DataFrame, gate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    min_n, min_c, min_m, min_mc = case["floor"]
    if (gate["valid_rows"] < min_n or gate["valid_countries"] < min_c
            or gate["material_change_rows"] < min_m or gate["material_change_countries"] < min_mc):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or material-treatment floor failed", "primary": None}
    shares = concentration(panel)
    if shares is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "no finite residual treatment variation", "primary": None}
    gate["top_one_percent_residual_x_share"], gate["top_country_residual_x_share"] = shares
    if shares[0] > MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE or shares[1] > MAX_TOP_COUNTRY_RESIDUAL_X_SHARE:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residual-treatment concentration gate failed", "primary": None}
    model = smf.ols("youth_employment_forward_change_pp ~ treatment_log_change + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed-effect design lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["treatment_log_change"]), float(fit.bse["treatment_log_change"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive country-cluster uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(0.9975, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite country-cluster t inference", "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.995,
               "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS, country-cluster CR1, Student t(G-1)"}
    magnitude = case["meaningful_beta"]
    if beta >= magnitude and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive association clears frozen magnitude and Bonferroni cutoff"
    elif beta <= -magnitude and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears frozen magnitude and Bonferroni cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any],
                     registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict, gate, primary = case["id"], result["verdict"], result["gate"], result["primary"]
    inputs = {role: SOURCES[role] for role in (key, "outcome")}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": "labour"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 2, "key_roster": ROSTER,
                                  "key_roster_sha256": ROSTER_SHA, "steelman": steelman_rel(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": inputs, "sample": gate}, "results": {"primary": primary},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
                   "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER, "preregistration_commit": registration,
                   "source_lock_commit": lock_commit, "source_lock": LOCK, "template": "panel_fe",
                   "preflight": gate, "primary": primary,
                   "p_max_two_sided_bonferroni": P_MAX,
                   "meaningful_beta_min_abs": case["meaningful_beta"],
                   "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
            f"Exposure: {case['label']}; outcome: OECD 15–24 employment/population rate. "
            f"Key-only upper bound: {case['key_rows']} country-years / {case['key_countries']} countries. "
            f"Valid complete pairs: {gate['valid_rows']} / {gate['valid_countries']}; "
            f"material log changes: {gate['material_change_rows']} / {gate['material_change_countries']}.\n")
    if primary is not None:
        card += (f"\nBeta={primary['coefficient']:+.6g} youth-employment percentage points "
                 f"per one-unit treatment log change; country-cluster SE={primary['std_error']:.6g}; "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}; "
                 f"99.5% CI={primary['confidence_interval']}.\n")
    card += ("\nTwo prespecified tests; Bonferroni family alpha 0.01, each two-sided p <= 0.005; "
             "absolute beta >= 1.0 pp per log point required. Positive supports the directional claim. "
             "Descriptive calibration only. No causal, policy, school, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = [{"term": "treatment_log_change", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# Business registrations and inbound tourism to youth employment: two-test result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "Both prespecified tests stay in one Bonferroni family (alpha 0.01; each two-sided p <= 0.005).",
             "", "| Exposure | Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |")
    lines += ["", "The coefficient is the one-year forward change in OECD youth employment percentage points per one-unit log change in the WDI treatment. Positive is the preregistered direction. These are measured associations, not policy effects.",
              "", "Earlier IESET business-entry, tourism, and youth-employment studies are disclosed in the preregistration. The two-test correction is local to this family. No school, policy, causal, or featured credit.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("one or more family result artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for key, case in CASES.items():
        payload = artifact_payload(key, case, results[key], registration, lock_commit, stamp)
        folder = ROOT / run_rel(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
        pd.DataFrame(payload["coefficients"], columns=["term", "coefficient", "std_error",
                                                       "p_value_two_sided", "confidence_level",
                                                       "confidence_interval", "n_rows", "n_countries",
                                                       "df_inference", "model_rank", "method"]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def normalize_arrow(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize_arrow(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize_arrow(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_arrow(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize_arrow(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for key, case in CASES.items():
        folder = ROOT / run_rel(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(key, case, results[key], registration, lock_commit, saved["run_utc"])
        equal_close(saved, payload["diagnostics"], f"{key}.diagnostics")
        equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"], f"{key}.manifest")
        equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"], f"{key}.packet")
        equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"], f"{key}.chart")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != payload["card"]
                or (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"{key}: text artifact mismatch")
        equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                    payload["coefficients"], f"{key}.coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    narrow = check_sources()
    if args.check_sources:
        print("WDI exposures and OECD LFS source SHA pins match; outcome values unopened")
        return 0
    if args.preflight:
        print(json.dumps(key_preflight(), indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    registration = registration_commit()
    preflight = key_preflight()
    lock_commit = check_source_lock(registration, narrow, preflight)
    panels = measured_panels(load_roster())
    results = {key: estimate(*panels[key], CASES[key]) for key in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        for key, result in results.items():
            print(key, result["verdict"], result["reason"])
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", FAMILY, {key: result["verdict"] for key, result in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
