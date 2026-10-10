#!/usr/bin/env python3
"""Frozen ten-case BIS household DSR to OECD How's Life descriptive study.

All preflight and source-lock operations read dimensions and keys only. The
selected OECD outcome values and missingness are first opened by --run or
--verify, after separate committed registration and source-lock checks.
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
FAMILY = "bis_dsr_oecd_hsl_extended_wellbeing_2026_10_10"
PREREG = "engine/audits/bis_dsr_oecd_hsl_extended_prereg_2026-10-10.md"
RUNNER = "scripts/run_bis_dsr_oecd_hsl_extended_2026.py"
ROSTER = "data/pinned_evidence/bis_dsr_oecd_hsl_extended_2026_key_roster.csv"
ROSTER_SHA = "a1a9a2df5bc58ae9d1d14a88d4527ea8c39a520dfce079e6c6aa6cbb12f553dd"
LOCK = "data/pinned_evidence/bis_dsr_oecd_hsl_extended_2026.manifest.json"
SUMMARY = "engine/audits/bis_dsr_oecd_hsl_extended_results_2026-10-10.md"
BIS = "data/vintages/bis/WS_DSR@2026-07-22T141212Z.parquet"
HSL = "data/vintages/oecd/OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0@2026-07-23T150432Z.parquet"
SOURCES = {
    "treatment": {"publisher": "bis", "series_id": "WS_DSR", "path": BIS,
                  "sha256": "59cb6b2f260d3132f826a15ccf585a3016af8516c4d0c2197a5fda2c2916b3fd",
                  "manifest": "data/manifests/fetch_run_2026-07-22T141212Z.yaml",
                  "manifest_sha256": "895761a2da3bd2554da4466becd7fa85837258ce80442c519362bb9d4c5eaea2"},
    "outcome": {"publisher": "oecd", "series_id": "OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0",
                "path": HSL, "sha256": "ac7581cb015748d97a21d4feadd08a3afb16cb1d5912af9e0997913ce4db65db",
                "manifest": "data/manifests/fetch_run_2026-07-23T150922Z.yaml",
                "manifest_sha256": "f8d2a682717c02832a2cf323fb5ea777139502e14987348859f3114042bece51"},
}
BIS_TO_ISO3 = {"AU": "AUS", "BE": "BEL", "CA": "CAN", "DE": "DEU", "DK": "DNK",
               "ES": "ESP", "FI": "FIN", "FR": "FRA", "GB": "GBR", "IT": "ITA",
               "JP": "JPN", "KR": "KOR", "NL": "NLD", "NO": "NOR", "PT": "PRT",
               "SE": "SWE", "US": "USA"}
HSL_TOTAL = {"AGE": "_T", "SEX": "_T", "EDUCATION_LEV": "_T"}
CASES = {
    'relative_poverty': {'id': 'bis_household_dsr_relative_poverty_forward_2026', 'topic': 'distribution', 'measure': '1_4', 'label': 'Household disposable income below the relative income poverty line', 'unit': 'PT_POP', 'sign': 1, 'key_rows': 204, 'countries': 15, 'years': (2004, 2023), 'floor': (150, 12, 105, 10), 'material_prelock': (153, 15), 'bound': 100},
    'employment_rate': {'id': 'bis_household_dsr_employment_rate_forward_2026', 'topic': 'labour', 'measure': '2_1', 'label': 'Employment rate', 'unit': 'PT_POP_Y25T64', 'sign': -1, 'key_rows': 357, 'countries': 17, 'years': (2004, 2024), 'floor': (265, 14, 180, 14), 'material_prelock': (268, 17), 'bound': 100},
    'longterm_unemployment': {'id': 'bis_household_dsr_longterm_unemployment_forward_2026', 'topic': 'labour', 'measure': '2_3', 'label': 'Long-term unemployment rate', 'unit': 'PT_LF', 'sign': 1, 'key_rows': 354, 'countries': 17, 'years': (2004, 2024), 'floor': (260, 14, 180, 14), 'material_prelock': (265, 17), 'bound': 100},
    'youth_neet': {'id': 'bis_household_dsr_youth_neet_forward_2026', 'topic': 'labour', 'measure': '2_4', 'label': 'Youth not in employment, education or training', 'unit': 'PT_POP_Y15T24', 'sign': 1, 'key_rows': 311, 'countries': 16, 'years': (2004, 2023), 'floor': (230, 13, 160, 12), 'material_prelock': (237, 16), 'bound': 100},
    'paid_long_hours': {'id': 'bis_household_dsr_paid_long_hours_forward_2026', 'topic': 'labour', 'measure': '2_7', 'label': 'Long hours in paid work', 'unit': 'PT_SAL', 'sign': 1, 'key_rows': 315, 'countries': 15, 'years': (2004, 2024), 'floor': (230, 12, 160, 11), 'material_prelock': (243, 15), 'bound': 100},
    'low_earnings': {'id': 'bis_household_dsr_low_earnings_forward_2026', 'topic': 'distribution', 'measure': '2_8_DEP', 'label': 'Full-time employees earning less than two-thirds of gross median earnings', 'unit': 'PT_SAL_FT', 'sign': 1, 'key_rows': 214, 'countries': 11, 'years': (2004, 2024), 'floor': (155, 9, 110, 8), 'material_prelock': (163, 11), 'bound': 100},
    'negative_health': {'id': 'bis_household_dsr_negative_health_forward_2026', 'topic': 'healthcare', 'measure': '5_2_DEP', 'label': 'Perceived health as negative', 'unit': 'PT_POP_Y_GE16', 'sign': 1, 'key_rows': 269, 'countries': 14, 'years': (2004, 2023), 'floor': (200, 11, 140, 10), 'material_prelock': (204, 14), 'bound': 100},
    'despair_deaths': {'id': 'bis_household_dsr_despair_deaths_forward_2026', 'topic': 'healthcare', 'measure': '5_3', 'label': 'Deaths from suicide, alcohol, drugs', 'unit': 'DT_10P5HB', 'sign': 1, 'key_rows': 309, 'countries': 17, 'years': (2004, 2023), 'floor': (230, 14, 160, 13), 'material_prelock': (233, 17), 'bound': 500},
    'lack_social_support': {'id': 'bis_household_dsr_lack_social_support_forward_2026', 'topic': 'distribution', 'measure': '7_1_DEP', 'label': 'Lack of social support', 'unit': 'PT_POP_Y_GE15', 'sign': 1, 'key_rows': 323, 'countries': 17, 'years': (2006, 2024), 'floor': (240, 14, 165, 13), 'material_prelock': (239, 17), 'bound': 100},
    'physical_pain': {'id': 'bis_household_dsr_physical_pain_forward_2026', 'topic': 'healthcare', 'measure': '11_3', 'label': 'Feelings of physical pain', 'unit': 'PT_POP_Y_GE15', 'sign': 1, 'key_rows': 323, 'countries': 17, 'years': (2006, 2024), 'floor': (240, 14, 165, 13), 'material_prelock': (239, 17), 'bound': 100},
}
FAMILY_ALPHA = 0.01
P_MAX = 0.001
BETA_MIN = 0.25
MATERIAL_X = 0.1
MIN_YEARS = 3
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 10, "family_alpha": FAMILY_ALPHA, "bonferroni_p_max": P_MAX,
              "school_score_eligible": False, "school_score_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "BIS household DSR is an estimated aggregate payment-to-income ratio; within-country changes are more comparable than cross-country levels.",
    "Country and year effects and one-year ordering do not identify a causal debt-service, credit, or policy effect.",
    "The ten OECD HSL endpoints have different populations and units; survey measures can pool adjacent years and must not be treated as independent annual samples.",
    "The ten-test Bonferroni family is local to this prospective batch and does not correct the visible IESET archive-wide search or earlier BIS/HSL tests.",
    "No school, policy, causal, or featured credit follows from any result.",
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
    return f"hypotheses/{case['topic']}/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


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
    if any(git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip()
           for case in CASES.values()):
        raise RuntimeError("registration commit already contains this family results")
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        threshold = spec["falsification"]["threshold"]
        expected = {"family_id": FAMILY, "family_size": 10, "family_alpha": FAMILY_ALPHA,
                    "p_max_two_sided_bonferroni": P_MAX,
                    "adverse_beta_min_per_dsr_pp": BETA_MIN,
                    "min_valid_rows": case["floor"][0], "min_valid_countries": case["floor"][1],
                    "min_material_change_rows": case["floor"][2],
                    "min_material_change_countries": case["floor"][3],
                    "material_dsr_change_min_pp": MATERIAL_X,
                    "max_top_1pct_residual_variance": 0.30,
                    "max_country_residual_variance": 0.30,
                    "max_year_residual_variance": 0.30,
                    "outcome_valid_max": case["bound"],
                    "min_years_per_country": MIN_YEARS,
                    "expected_key_rows": case["key_rows"],
                    "expected_key_countries": case["countries"],
                    "roster_sha256": ROSTER_SHA,
                    "source_files": {role: {k: v for k, v in source.items()
                                            if k in ("path", "sha256", "manifest", "manifest_sha256")}
                                     for role, source in SOURCES.items()},
                    "school_score_eligible": False, "school_score_credit": 0,
                    "policy_score_eligible": False, "policy_score_credit": 0}
        if threshold != expected:
            raise RuntimeError(f"registered threshold mismatch: {key}")
        if (spec["hypothesis_id"] != case["id"] or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["steelman"] != steelman_rel(case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
                or spec["linked_conditions"] != []):
            raise RuntimeError(f"registered descriptive spec mismatch: {key}")
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
            raise RuntimeError(f"{role} manifest entry mismatch")
        e = matches[0]
        narrow[role] = {**source, "source_url": e.get("source_url"),
                        "methodology_url": e.get("methodology_url"),
                        "license": e.get("license"), "fetch_utc": e.get("fetch_utc"),
                        "rows": e.get("rows"), "frequency": e.get("frequency")}
    return narrow


def load_roster() -> dict[str, list[tuple[str, int]]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"case_id,country_iso3,year\n"):
        raise RuntimeError("frozen roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    result = {key: [] for key in CASES}
    for r in records:
        if r["case_id"] not in result:
            raise RuntimeError("unexpected case in roster")
        result[r["case_id"]].append((r["country_iso3"], int(r["year"])))
    expected_rows = [(key, c, y) for key, case in CASES.items()
                     for c, y in sorted(result[key], key=lambda z: (z[1], z[0]))]
    observed_rows = [(r["case_id"], r["country_iso3"], int(r["year"])) for r in records]
    if expected_rows != observed_rows or len(observed_rows) != 2979 or len(set(observed_rows)) != len(observed_rows):
        raise RuntimeError("frozen roster ordering, size, or uniqueness mismatch")
    for key, case in CASES.items():
        rows = result[key]
        if (len(rows) != case["key_rows"] or len({c for c, _ in rows}) != case["countries"]
                or (min(y for _, y in rows), max(y for _, y in rows)) != case["years"]):
            raise RuntimeError(f"frozen roster envelope mismatch: {key}")
    return result


def source_keys() -> tuple[set[tuple[str, int]], dict[str, set[tuple[str, int]]]]:
    """Dimensions and keys only; never selected OECD value or null/status fields."""
    bis = pd.read_parquet(ROOT / BIS, columns=["FREQ", "BORROWERS_CTY", "DSR_BORROWERS", "UNIT_MEASURE", "period", "OBS_STATUS"])
    if len(bis) != 7116:
        raise RuntimeError("BIS row-count contract changed")
    bis = bis.loc[bis.FREQ.eq("Q") & bis.DSR_BORROWERS.eq("H") & bis.UNIT_MEASURE.eq(367) & bis.OBS_STATUS.eq("A")].copy()
    if bis.duplicated(["BORROWERS_CTY", "period"]).any():
        raise RuntimeError("duplicate BIS country-quarter")
    bis["year"] = bis.period.str[:4].astype(int)
    bis["quarter"] = bis.period.str[-1].astype(int)
    annual = {(BIS_TO_ISO3[c], int(y)) for (c, y), q in bis.groupby(["BORROWERS_CTY", "year"]).quarter.agg(set).items()
              if c in BIS_TO_ISO3 and q == {1, 2, 3, 4}}
    hsl = pd.read_parquet(ROOT / HSL, columns=["REF_AREA", "MEASURE", "Measure", "UNIT_MEASURE", "AGE", "SEX", "EDUCATION_LEV", "period"])
    if len(hsl) != 111266:
        raise RuntimeError("OECD HSL row-count contract changed")
    for col, expected in HSL_TOTAL.items():
        hsl = hsl.loc[hsl[col].eq(expected)]
    out = {}
    for key, case in CASES.items():
        chosen = hsl.loc[hsl.MEASURE.eq(case["measure"]) & hsl.UNIT_MEASURE.eq(case["unit"])].copy()
        if not chosen.Measure.eq(case["label"]).all() or chosen.duplicated(["REF_AREA", "period"]).any():
            raise RuntimeError(f"OECD HSL label or duplicate-key mismatch: {key}")
        out[key] = {(str(c), int(y)) for c, y in chosen[["REF_AREA", "period"]].itertuples(index=False, name=None)}
    return annual, out


def key_preflight() -> dict[str, Any]:
    annual, hsl = source_keys()
    roster = load_roster()
    report = {"measured_outcome_values_read": False, "outcome_null_masks_read": False,
              "roster_sha256": ROSTER_SHA, "cases": {}}
    for key, case in CASES.items():
        keys = hsl[key]
        candidates = {(c, y) for c, y in keys if (c, y + 1) in keys
                      and (c, y - 1) in annual and (c, y) in annual}
        counts = Counter(c for c, _ in candidates)
        chosen = sorted(((c, y) for c, y in candidates if counts[c] >= MIN_YEARS),
                        key=lambda z: (z[1], z[0]))
        if chosen != roster[key]:
            raise RuntimeError(f"source key preflight differs from roster: {key}")
        report["cases"][key] = {"key_rows": len(chosen),
                                "countries": len({c for c, _ in chosen}),
                                "t_years": list(case["years"]),
                                "prelock_exposure_only_material_rows": case["material_prelock"][0],
                                "prelock_exposure_only_material_countries": case["material_prelock"][1]}
    return report


def lock_payload(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_value_access_before_lock": False,
            "outcome_null_mask_access_before_lock": False,
            "exposure_values_inspected_before_registration": True,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    revision = registration_commit()
    narrow = check_sources()
    preflight = key_preflight()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(revision, narrow, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening selected OECD outcomes")


def check_source_lock(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, narrow, preflight):
        raise RuntimeError("source lock differs from preregistration, raw pins, or key preflight")
    commit = first_addition(LOCK)
    if commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return commit


def finite_range(value: Any, upper: float) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) and 0 <= numeric <= upper else None


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First selected outcome numeric access; caller must verify two Git commits."""
    bis = pd.read_parquet(ROOT / BIS, columns=["FREQ", "BORROWERS_CTY", "DSR_BORROWERS", "UNIT_MEASURE", "period", "value", "OBS_STATUS"])
    bis = bis.loc[bis.FREQ.eq("Q") & bis.DSR_BORROWERS.eq("H") & bis.UNIT_MEASURE.eq(367) & bis.OBS_STATUS.eq("A")].copy()
    bis["year"] = bis.period.str[:4].astype(int)
    bis["quarter"] = bis.period.str[-1].astype(int)
    quarter = {(BIS_TO_ISO3[c], int(y), int(q)): finite_range(v, 100)
               for c, y, q, v in bis[["BORROWERS_CTY", "year", "quarter", "value"]].itertuples(index=False, name=None)
               if c in BIS_TO_ISO3}
    hsl = pd.read_parquet(ROOT / HSL, columns=["REF_AREA", "MEASURE", "UNIT_MEASURE", "AGE", "SEX", "EDUCATION_LEV", "period", "value", "OBS_STATUS"])
    for col, expected in HSL_TOTAL.items():
        hsl = hsl.loc[hsl[col].eq(expected)]
    results = {}
    for key, case in CASES.items():
        chosen = hsl.loc[hsl.MEASURE.eq(case["measure"]) & hsl.UNIT_MEASURE.eq(case["unit"])]
        vals = {(str(c), int(y)): (finite_range(v, case["bound"]), None if pd.isna(s) else str(s))
                for c, y, v, s in chosen[["REF_AREA", "period", "value", "OBS_STATUS"]].itertuples(index=False, name=None)}
        rows, dropped = [], 0
        status_counts = Counter()
        for c, y in roster[key]:
            q_prev = [quarter.get((c, y - 1, q)) for q in range(1, 5)]
            q_now = [quarter.get((c, y, q)) for q in range(1, 5)]
            old, old_status = vals.get((c, y), (None, None))
            new, new_status = vals.get((c, y + 1), (None, None))
            if (any(v is None for v in q_prev + q_now) or old is None or new is None
                    or (old_status not in (None, "", "A")) or (new_status not in (None, "", "A"))):
                dropped += 1
                continue
            status_counts[old_status or "<missing>"] += 1
            status_counts[new_status or "<missing>"] += 1
            rows.append({"country_iso3": c, "year": y,
                         "dsr_change_pp": sum(q_now) / 4 - sum(q_prev) / 4,
                         "adverse_outcome_change_pp": case["sign"] * (new - old)})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "dsr_change_pp", "adverse_outcome_change_pp"])
        before = len(panel)
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        material = panel.dsr_change_pp.abs().ge(MATERIAL_X)
        gate = {"roster_rows": len(roster[key]), "dropped_invalid_or_missing_pairs": dropped,
                "complete_pairs_before_three_year_country_floor": before,
                "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
                "material_dsr_change_rows": int(material.sum()),
                "material_dsr_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
                "selected_outcome_status_counts_for_complete_pairs": dict(sorted(status_counts.items())),
                "outcome_values_read_after_lock": True}
        results[key] = panel, gate
    return results


def estimate(panel: pd.DataFrame, gate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    min_n, min_g, min_m, min_mg = case["floor"]
    if (gate["valid_rows"] < min_n or gate["valid_countries"] < min_g
            or gate["material_dsr_change_rows"] < min_m
            or gate["material_dsr_change_countries"] < min_mg):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen sample or material DSR variation floor failed", "primary": None}
    residual = smf.ols("dsr_change_pp ~ C(country_iso3) + C(year)", data=panel).fit().resid.to_numpy()
    squared = np.square(residual)
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "no residualized treatment variation", "primary": None}
    top_n = max(1, int(math.ceil(0.01 * len(panel))))
    by = panel[["country_iso3", "year"]].copy()
    by["squared"] = squared
    influence = {"top_1pct_rows": float(np.sort(squared)[-top_n:].sum() / total),
                 "largest_country": float(by.groupby("country_iso3").squared.sum().max() / total),
                 "largest_year": float(by.groupby("year").squared.sum().max() / total)}
    gate["residualized_treatment_variance_shares"] = influence
    if any(v > 0.30 for v in influence.values()):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen residualized-treatment concentration gate failed", "primary": None}
    model = smf.ols("adverse_outcome_change_pp ~ dsr_change_pp + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "fixed-effect design lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    if groups <= 1:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "insufficient country clusters", "primary": None}
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True,
                                                  "df_correction": True}, use_t=True)
    beta, se = float(fit.params["dsr_change_pp"]), float(fit.bse["dsr_change_pp"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive clustered uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(0.9995, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite country-cluster t inference", "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.999, "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS, country-cluster CR1, Student t(G-1)"}
    if beta >= BETA_MIN and p <= P_MAX:
        verdict, reason = "SUPPORTED", "adverse association clears frozen magnitude and Bonferroni cutoff"
    elif beta <= -BETA_MIN and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears frozen magnitude and Bonferroni cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict, gate, primary = case["id"], result["verdict"], result["gate"], result["primary"]
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": case["topic"]},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 10, "key_roster": ROSTER,
                                  "key_roster_sha256": ROSTER_SHA, "steelman": steelman_rel(case)},
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
                   "adverse_beta_min_per_dsr_pp": BETA_MIN,
                   "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source-lock commit: `{lock_commit}`.\n\n"
            f"Pinned OECD HSL `{case['measure']}` **{case['label']}**; sign {case['sign']:+d} "
            f"so positive coefficients mean worsening. Key-only upper bound: {case['key_rows']} "
            f"country-years / {case['countries']} countries. Valid complete cases: {gate['valid_rows']} "
            f"rows / {gate['valid_countries']} countries; material DSR changes: "
            f"{gate['material_dsr_change_rows']} rows / {gate['material_dsr_change_countries']} countries.\n")
    if primary is not None:
        card += (f"\nPrimary beta={primary['coefficient']:+.6g} adverse outcome {'deaths per 100,000' if key == 'despair_deaths' else 'percentage points'} "
                 f"per one DSR percentage point, country-cluster SE={primary['std_error']:.6g}, "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}, "
                 f"99.9% CI={primary['confidence_interval']}.\n")
    card += (f"\nFamily correction: ten registered tests, Bonferroni family alpha 0.01, "
             f"individual two-sided p <= {P_MAX}; |beta| >= {BETA_MIN} is also required. "
             "This is descriptive country-panel calibration only. No causal, policy, school, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = [{"term": "dsr_change_pp", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# BIS household DSR × OECD How's Life: ten-test result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "All ten prespecified tests remain in one Bonferroni family (alpha 0.01, each two-sided p <= 0.001).",
             "", "| Case | Verdict | Valid country-years / countries | Material DSR-change rows / countries | Adverse beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['label']} (`{case['measure']}`) | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_dsr_change_rows']} / {gate['material_dsr_change_countries']} | {beta} | {p} |")
    lines += ["", "Beta is adverse-oriented outcome units per one percentage-point annual DSR change. Deaths are per 100,000 residents; all other measures are percentages. Some survey country averages may pool multiple years.",
              "", "These are ecological descriptive associations with visible prior related studies. Ten-test correction is local to this batch. No school, policy, causal, or featured credit.", ""]
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
        print("BIS and OECD source SHA pins match; selected OECD outcomes not opened")
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
    print("verified exact replay", FAMILY, {k: v["verdict"] for k, v in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
