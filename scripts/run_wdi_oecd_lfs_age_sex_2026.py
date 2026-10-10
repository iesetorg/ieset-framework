#!/usr/bin/env python3
"""Frozen 20-cell GDP-growth to OECD employment-ratio descriptive family.

Source checks and key preflight never access selected OECD employment values,
observation statuses, or missingness. Only --run/--verify may do so, after a
separate committed source lock descended from the registration commit.
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
FAMILY = "wdi_growth_oecd_lfs_age_sex_2026_10_10"
RUNNER = "scripts/run_wdi_oecd_lfs_age_sex_2026.py"
TEST = "tests/test_wdi_oecd_lfs_age_sex_prereg.py"
PREREG = "engine/audits/wdi_growth_oecd_lfs_age_sex_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_growth_oecd_lfs_age_sex_2026_key_roster.csv"
ROSTER_SHA = "5323ed232b5f2a70b331259f290053c40869524eb701f0a1f06db63c79558aa7"
LOCK = "data/pinned_evidence/wdi_growth_oecd_lfs_age_sex_2026.manifest.json"
SUMMARY = "engine/audits/wdi_growth_oecd_lfs_age_sex_results_2026-10-10.md"
GDP = "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet"
LFS = "data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-07-23T151216Z.parquet"
SOURCES = {
    "exposure": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG", "path": GDP,
                 "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
                 "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
                 "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "outcome": {"publisher": "oecd", "series_id": "DSD_LFS_DF_LFS_INDIC", "path": LFS,
                "sha256": "ac58f9ea05eb07e0d4696a81334021120cd679f58847a2fb32dc70e06074e6ae",
                "manifest": "data/manifests/fetch_run_2026-07-23T151302Z.yaml",
                "manifest_sha256": "4952688fa8fbf62df91c20409bf4180b75977bc638bb33e2a00a267b3053b601"},
}
AGES = tuple((n, n + 4) for n in range(15, 65, 5))
CASES = {
    f"{sex.lower()}_{low}_{high}": {
        "id": f"wdi_growth_oecd_employment_{sex.lower()}_{low}_{high}_forward_2026",
        "sex": sex, "age": f"Y{low}T{high}", "age_label": f"{low}–{high}",
        "sex_label": "women" if sex == "F" else "men",
    }
    for sex in ("F", "M") for low, high in AGES
}
FAMILY_SIZE = len(CASES)
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
BETA_MIN = 0.10
MATERIAL_X = 2.0
MIN_COMPLETE_YEARS = 8
FLOORS = {"min_valid_rows": 750, "min_valid_countries": 40,
          "min_material_growth_rows": 500, "min_material_growth_countries": 35,
          "min_distinct_years": 20, "min_complete_years_per_country": MIN_COMPLETE_YEARS,
          "max_top_1pct_partialled_growth_share": 0.35,
          "max_country_partialled_growth_share": 0.20,
          "max_year_partialled_growth_share": 0.20}
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "These 20 age-by-sex cells are disjoint populations but highly correlated outcomes sharing country-years and the same GDP exposure; they are one family, not independent replications.",
    "Annual OECD age-band employment ratios are repeated cross sections, not a panel of individuals aging through a cohort.",
    "GDP growth and employment may respond jointly to demand, demographics, policy, measurement changes, and shocks; timing and fixed effects do not identify causality.",
    "The 20-test Bonferroni correction is local to this preregistered family, not to the adaptively searched IESET archive.",
    "Ireland's 2015 GDP growth and other national-accounts outliers remain in the untrimmed registered exposure; complete-case concentration may render a cell INCONCLUSIVE.",
    "No causal, policy, school, position, or featured credit follows from any result.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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


def threshold() -> dict[str, Any]:
    return {"family_id": FAMILY, "family_size": FAMILY_SIZE,
            "family_alpha": FAMILY_ALPHA, "p_max_two_sided_bonferroni": P_MAX,
            "positive_beta_min_employment_pp_per_growth_pp": BETA_MIN,
            "material_growth_min_abs_pp": MATERIAL_X,
            "expected_key_rows": 1094, "expected_key_countries": 50,
            "expected_key_years": [1995, 2018], "roster_sha256": ROSTER_SHA,
            **FLOORS,
            "source_files": {role: {k: v for k, v in source.items()
                                    if k in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role, source in SOURCES.items()},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER, TEST]
    for case in CASES.values():
        frozen.extend([spec_rel(case), steelman_rel(case)])
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    if any(git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(c)).strip()
           for c in CASES.values()):
        raise RuntimeError("registration commit already contains results")
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec["hypothesis_id"] != case["id"] or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["claim_direction"] != "+"
                or spec["falsification"]["threshold"] != threshold()
                or spec["steelman"] != steelman_rel(case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
                or spec["linked_conditions"] != []):
            raise RuntimeError(f"registered spec mismatch: {key}")
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
            raise RuntimeError(f"{role} fetch-manifest entry mismatch")
        e = matches[0]
        narrow[role] = {**source, "source_url": e.get("source_url"),
                        "methodology_url": e.get("methodology_url"),
                        "license": e.get("license"), "fetch_utc": e.get("fetch_utc"),
                        "rows": e.get("rows"), "frequency": e.get("frequency")}
    return narrow


def exposure_values() -> dict[tuple[str, int], float]:
    """WDI treatment/control access is permitted before registration."""
    gdp = pd.read_parquet(ROOT / GDP, columns=["country_iso3", "year", "value", "obs_status"])
    gdp = gdp.loc[gdp.country_iso3.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
    if gdp.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI country-year")
    gdp["value"] = pd.to_numeric(gdp.value, errors="coerce")
    gdp = gdp.loc[np.isfinite(gdp.value) & gdp.value.between(-100, 100)
                  & gdp.obs_status.fillna("").isin(["", "A"])]
    return {(str(c), int(y)): float(v) for c, y, v in
            gdp[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}


def outcome_keys() -> dict[str, set[tuple[str, int]]]:
    """OECD dimensions and keys only; never value, Observation value, or OBS_STATUS."""
    cols = ["REF_AREA", "MEASURE", "UNIT_MEASURE", "SEX", "AGE", "LABOUR_FORCE_STATUS", "period"]
    oecd = pd.read_parquet(ROOT / LFS, columns=cols)
    if len(oecd) != 535380:
        raise RuntimeError("OECD LFS row-count contract changed")
    oecd = oecd.loc[oecd.MEASURE.eq("EMP_RATIO") & oecd.UNIT_MEASURE.eq("PT_POP_SUB")
                    & oecd.LABOUR_FORCE_STATUS.eq("EMP")
                    & oecd.REF_AREA.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
    result = {}
    for key, case in CASES.items():
        chosen = oecd.loc[oecd.SEX.eq(case["sex"]) & oecd.AGE.eq(case["age"])]
        if chosen.duplicated(["REF_AREA", "period"]).any():
            raise RuntimeError(f"duplicate OECD outcome key: {key}")
        result[key] = {(str(c), int(y)) for c, y in
                       chosen[["REF_AREA", "period"]].itertuples(index=False, name=None)}
    return result


def candidate_rows(keys: set[tuple[str, int]], growth: dict[tuple[str, int], float]) -> list[tuple[str, int]]:
    raw = {(c, y) for c, y in keys if 1995 <= y <= 2018
           and (c, y + 1) in keys and (c, y) in growth and (c, y - 1) in growth}
    counts = Counter(c for c, _ in raw)
    return sorted((r for r in raw if counts[r[0]] >= MIN_COMPLETE_YEARS), key=lambda z: (z[1], z[0]))


def load_roster() -> list[tuple[str, int]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("frozen roster SHA-256/header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    rows = [(r["country_iso3"], int(r["year"])) for r in records]
    if (rows != sorted(set(rows), key=lambda z: (z[1], z[0])) or len(rows) != 1094
            or len({c for c, _ in rows}) != 50 or (min(y for _, y in rows), max(y for _, y in rows)) != (1995, 2018)):
        raise RuntimeError("frozen roster order, uniqueness, or envelope mismatch")
    return rows


def key_preflight() -> dict[str, Any]:
    growth = exposure_values()
    keys = outcome_keys()
    roster = load_roster()
    for key in CASES:
        if candidate_rows(keys[key], growth) != roster:
            raise RuntimeError(f"OECD key-only preflight differs from roster: {key}")
    panel = pd.DataFrame([{"country_iso3": c, "year": y,
                           "gdp_growth": growth[c, y], "lagged_growth": growth[c, y - 1]}
                          for c, y in roster])
    material = panel.gdp_growth.abs().ge(MATERIAL_X)
    residual = smf.ols("gdp_growth ~ lagged_growth + C(country_iso3) + C(year)", data=panel).fit().resid.to_numpy()
    shares = concentration(panel, residual)
    return {"outcome_values_read": False, "outcome_null_masks_read": False,
            "outcome_statuses_read": False, "roster_sha256": ROSTER_SHA,
            "cases": FAMILY_SIZE, "shared_key_rows_per_case": len(roster),
            "key_countries": int(panel.country_iso3.nunique()), "t_years": [1995, 2018],
            "exposure_only_material_rows": int(material.sum()),
            "exposure_only_material_countries": int(panel.loc[material, "country_iso3"].nunique()),
            "exposure_only_negative_or_zero_growth_rows": int(panel.gdp_growth.le(0).sum()),
            "exposure_only_growth_ge_three_rows": int(panel.gdp_growth.ge(3).sum()),
            "exposure_only_partialled_growth_variance_shares": shares}


def concentration(panel: pd.DataFrame, residual: np.ndarray) -> dict[str, float]:
    squares = np.square(np.asarray(residual, dtype=float))
    total = float(squares.sum())
    if not math.isfinite(total) or total <= 0:
        raise ValueError("no residualized treatment variation")
    top_n = max(1, math.ceil(0.01 * len(panel)))
    by = panel[["country_iso3", "year"]].copy()
    by["squared"] = squares
    return {"top_1pct_rows": float(np.sort(squares)[-top_n:].sum() / total),
            "largest_country": float(by.groupby("country_iso3").squared.sum().max() / total),
            "largest_year": float(by.groupby("year").squared.sum().max() / total)}


def lock_payload(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_value_access_before_lock": False,
            "outcome_null_mask_access_before_lock": False,
            "outcome_status_access_before_lock": False,
            "exposure_values_inspected_before_registration": True,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    revision = registration_commit()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(revision, check_sources(), key_preflight()), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening OECD outcomes")


def check_source_lock(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, narrow, preflight):
        raise RuntimeError("source lock differs from registration, raw pins, or key preflight")
    commit = first_addition(LOCK)
    if commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    if any(git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(c)).strip()
           for c in CASES.values()):
        raise RuntimeError("source-lock commit already contains measured results")
    return commit


def finite_ratio(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) and 0 <= numeric <= 100 else None


def measured_panels(roster: list[tuple[str, int]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First selected-outcome numeric and status access; caller checks two commits."""
    growth = exposure_values()
    cols = ["REF_AREA", "MEASURE", "UNIT_MEASURE", "SEX", "AGE", "LABOUR_FORCE_STATUS", "period", "value", "OBS_STATUS"]
    oecd = pd.read_parquet(ROOT / LFS, columns=cols)
    oecd = oecd.loc[oecd.MEASURE.eq("EMP_RATIO") & oecd.UNIT_MEASURE.eq("PT_POP_SUB")
                    & oecd.LABOUR_FORCE_STATUS.eq("EMP")
                    & oecd.REF_AREA.astype(str).str.fullmatch(r"[A-Z]{3}")]
    result = {}
    for key, case in CASES.items():
        chosen = oecd.loc[oecd.SEX.eq(case["sex"]) & oecd.AGE.eq(case["age"])]
        vals = {(str(c), int(y)): (finite_ratio(v), None if pd.isna(s) else str(s))
                for c, y, v, s in chosen[["REF_AREA", "period", "value", "OBS_STATUS"]].itertuples(index=False, name=None)}
        rows, dropped = [], 0
        statuses = Counter()
        for c, y in roster:
            old, old_status = vals.get((c, y), (None, None))
            new, new_status = vals.get((c, y + 1), (None, None))
            if old is None or new is None or old_status not in (None, "", "A") or new_status not in (None, "", "A"):
                dropped += 1
                continue
            statuses[old_status or "<missing>"] += 1
            statuses[new_status or "<missing>"] += 1
            rows.append({"country_iso3": c, "year": y, "gdp_growth": growth[c, y],
                         "lagged_growth": growth[c, y - 1], "employment_change": new - old})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "gdp_growth", "lagged_growth", "employment_change"])
        before = len(panel)
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_COMPLETE_YEARS)].copy()
        material = panel.gdp_growth.abs().ge(MATERIAL_X)
        gate = {"roster_rows": len(roster), "dropped_invalid_or_missing_pairs": dropped,
                "complete_pairs_before_country_floor": before, "valid_rows": len(panel),
                "valid_countries": int(panel.country_iso3.nunique()),
                "distinct_years": int(panel.year.nunique()),
                "material_growth_rows": int(material.sum()),
                "material_growth_countries": int(panel.loc[material, "country_iso3"].nunique()),
                "selected_outcome_status_counts_for_complete_pairs": dict(sorted(statuses.items())),
                "outcome_values_read_after_lock": True}
        result[key] = panel, gate
    return result


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < FLOORS["min_valid_rows"]
            or gate["valid_countries"] < FLOORS["min_valid_countries"]
            or gate["distinct_years"] < FLOORS["min_distinct_years"]
            or gate["material_growth_rows"] < FLOORS["min_material_growth_rows"]
            or gate["material_growth_countries"] < FLOORS["min_material_growth_countries"]):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen sample or material-growth floor failed", "primary": None}
    residual = smf.ols("gdp_growth ~ lagged_growth + C(country_iso3) + C(year)", data=panel).fit().resid.to_numpy()
    try:
        shares = concentration(panel, residual)
    except ValueError:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "no partialled GDP-growth variation", "primary": None}
    gate["partialled_growth_variance_shares"] = shares
    if (shares["top_1pct_rows"] > FLOORS["max_top_1pct_partialled_growth_share"]
            or shares["largest_country"] > FLOORS["max_country_partialled_growth_share"]
            or shares["largest_year"] > FLOORS["max_year_partialled_growth_share"]):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen partialled-growth concentration gate failed", "primary": None}
    model = smf.ols("employment_change ~ gdp_growth + lagged_growth + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "fixed-effect design lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["gdp_growth"]), float(fit.bse["gdp_growth"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive country-cluster uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite country-cluster t inference", "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 1 - P_MAX,
               "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS with lagged growth, country-cluster CR1, Student t(G-1)"}
    if beta >= BETA_MIN and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive employment association clears frozen magnitude and Bonferroni cutoff"
    elif beta <= -BETA_MIN and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears frozen magnitude and Bonferroni cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict, gate, primary = case["id"], result["verdict"], result["gate"], result["primary"]
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": "labour"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": FAMILY_SIZE,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": steelman_rel(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": SOURCES, "sample": gate}, "results": {"primary": primary},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
                   "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
                   "primary": primary, "p_max_two_sided_bonferroni": P_MAX,
                   "positive_beta_min_employment_pp_per_growth_pp": BETA_MIN,
                   "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source-lock commit: `{lock_commit}`.\n\n"
            f"OECD LFS employment ratio: {case['sex_label']}, ages {case['age_label']}; "
            f"key-only upper bound: 1,094 country-years / 50 countries. "
            f"Valid pairs: {gate['valid_rows']} / {gate['valid_countries']}; "
            f"material GDP-growth rows: {gate['material_growth_rows']} / "
            f"{gate['material_growth_countries']} countries.\n")
    if primary is not None:
        card += (f"\nPrimary beta={primary['coefficient']:+.6g} employment percentage-point change "
                 f"per one GDP-growth percentage point, country-cluster SE={primary['std_error']:.6g}, "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}, "
                 f"{100*(1-P_MAX):.3f}% CI={primary['confidence_interval']}.\n")
    card += (f"\nFamily correction: 20 registered tests, Bonferroni family alpha 0.01, "
             f"individual two-sided p <= {P_MAX}; |beta| >= {BETA_MIN} also required. "
             "One correlated descriptive family; no causal, policy, school, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = [{"term": "gdp_growth", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# WDI GDP growth × OECD LFS employment: 20-cell result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "All 20 prespecified cells remain in one Bonferroni family (alpha 0.01, each two-sided p <= 0.0005).",
             "", "| Cell | Verdict | Valid pairs / countries | Material growth rows / countries | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['sex_label']} {case['age_label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_growth_rows']} / {gate['material_growth_countries']} | {beta} | {p} |")
    lines += ["", "Beta is next-year employment-ratio change in percentage points per one percentage point of current real GDP growth, conditioning on prior-year growth and country/year fixed effects.",
              "", "Age-sex outcomes are correlated repeated-cross-section measures, not independent replications. This local correction does not cover archive-wide search. No causal, policy, school, position, or featured credit.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(c)).exists() for c in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("one or more result artifacts already exist")
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


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for k, v in expected.items():
            equal_close(actual[k], v, f"{label}.{k}")
    elif isinstance(expected, list):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist()
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for i, v in enumerate(expected):
            equal_close(actual[i], v, f"{label}[{i}]")
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
        equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"] ,f"{key}.chart")
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
        print("WDI and OECD source SHA pins match; selected OECD outcomes unopened")
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
    results = {key: estimate(*panels[key]) for key in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        for key, result in results.items():
            print(key, result["verdict"], result["reason"])
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", FAMILY, {k: v["verdict"] for k, v in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
