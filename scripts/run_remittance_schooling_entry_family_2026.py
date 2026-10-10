#!/usr/bin/env python3
"""Frozen remittance change to schooling and formal entry two-test family.

Preflight may read remittance and GDP control values, and outcome keys only.
Lock requires a prior committed registration. Run and verify open outcome
measurements only after a separately committed, unchanged source lock.
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
FAMILY = "wdi_remittance_schooling_entry_family_2026_10_10"
RUNNER = "scripts/run_remittance_schooling_entry_family_2026.py"
TEST = "tests/test_remittance_schooling_entry_family_2026.py"
PREREG = "engine/audits/remittance_schooling_entry_family_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/remittance_schooling_entry_family_2026_key_roster.csv"
ROSTER_SHA = "f7358d7c138542807b3ff8789c3e95f31a1efb9b82d8d3033e68a7c64467cc58"
LOCK = "data/pinned_evidence/remittance_schooling_entry_family_2026.manifest.json"
SUMMARY = "engine/audits/remittance_schooling_entry_family_results_2026-10-10.md"

BOOTSTRAP_MANIFEST = "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml"
BOOTSTRAP_MANIFEST_SHA = "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"
WDI_200056_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
WDI_200056_MANIFEST_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
WDI_210519_MANIFEST = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
WDI_210519_MANIFEST_SHA = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"
SOURCES = {
    "remittances": {
        "publisher": "world_bank_wdi", "series_id": "BX.TRF.PWKR.DT.GD.ZS",
        "path": "data/vintages/world_bank_wdi/BX.TRF.PWKR.DT.GD.ZS@2026-04-30T114721Z.parquet",
        "sha256": "9139bffa26cd6f78bf8a963400e703398b9d59919bb92ab0b2ec2b7e04885b1d",
        "manifest": BOOTSTRAP_MANIFEST, "manifest_sha256": BOOTSTRAP_MANIFEST_SHA,
    },
    "enrolment": {
        "publisher": "world_bank_wdi", "series_id": "SE.SEC.ENRR",
        "path": "data/vintages/world_bank_wdi/SE.SEC.ENRR@2026-05-05T204008Z.parquet",
        "sha256": "787f29eb93204dbf11dd408449910c28b523376c054734f1fc68d4215b7b2044",
        "manifest": WDI_210519_MANIFEST, "manifest_sha256": WDI_210519_MANIFEST_SHA,
    },
    "registrations": {
        "publisher": "world_bank_wdi", "series_id": "IC.BUS.NREG",
        "path": "data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet",
        "sha256": "213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae",
        "manifest": WDI_210519_MANIFEST, "manifest_sha256": WDI_210519_MANIFEST_SHA,
    },
    "gdp_pc": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": WDI_200056_MANIFEST, "manifest_sha256": WDI_200056_MANIFEST_SHA,
    },
    "gdp_growth": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
        "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
        "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
        "manifest": WDI_200056_MANIFEST, "manifest_sha256": WDI_200056_MANIFEST_SHA,
    },
}
CASES = {
    "enrolment": {
        "id": "remittance_change_secondary_gross_enrolment_forward_2026",
        "label": "secondary gross enrolment", "horizon": 2,
        "meaningful_beta": 0.2, "unit": "percentage points",
        "outcome_dim": "education_access",
    },
    "registrations": {
        "id": "remittance_change_new_limited_liability_registrations_forward_2026",
        "label": "new limited-liability registrations", "horizon": 1,
        "meaningful_beta": 0.02, "unit": "log points",
        "outcome_dim": "industrial_capability",
    },
}
T_START, T_END, MIN_YEARS = 2006, 2021, 5
ROSTER_ROWS, ROSTER_COUNTRIES = 2744, 180
MATERIAL_DELTA_PP = 1.0
PREFLIGHT_UP_ROWS, PREFLIGHT_DOWN_ROWS = 215, 169
FAMILY_ALPHA, P_MAX = 0.01, 0.005
MIN_COMPLETE_ROWS, MIN_COMPLETE_COUNTRIES = 300, 30
MIN_MATERIAL_COUNTRIES = 20
MAX_COUNTRY_RESIDUAL_SHARE = 0.30
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 2, "family_alpha": FAMILY_ALPHA,
    "bonferroni_p_max": P_MAX, "school_score_eligible": False,
    "school_score_credit": 0, "policy_score_eligible": False,
    "policy_score_credit": 0, "causal_credit": 0,
    "featured_eligible": False,
}
LIMITATIONS = [
    "Personal remittances received include household transfers and compensation of nonresident workers; the share of GDP can change when GDP changes.",
    "Secondary gross enrolment is a UNESCO UIS ratio of enrolment at any age to the official school-age population; it can exceed 100 and is not attainment.",
    "New business registrations count formal limited-liability entities, not all entrepreneurship, operating firms, or jobs; registry definitions can change.",
    "Migration selection, economic shocks, schooling reforms, registry coverage, and reverse timing can jointly move exposure and outcomes.",
    "Country/year fixed effects, controls, and forward timing do not identify a causal remittance or policy effect.",
    "The two-test Bonferroni correction does not correct selection across the visible IESET archive; both outcomes share WDI transport and many countries.",
    "No result receives school, policy, causal, or featured credit.",
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
        raise RuntimeError(f"frozen file differs from its first commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/growth/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(key: str, case: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
        "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": case["meaningful_beta"],
        "min_valid_rows": MIN_COMPLETE_ROWS,
        "min_valid_countries": MIN_COMPLETE_COUNTRIES,
        "min_years_per_country": MIN_YEARS,
        "min_material_exposure_countries": MIN_MATERIAL_COUNTRIES,
        "material_exposure_pp": MATERIAL_DELTA_PP,
        "max_country_residualized_exposure_share": MAX_COUNTRY_RESIDUAL_SHARE,
        "expected_key_rows": ROSTER_ROWS,
        "expected_key_countries": ROSTER_COUNTRIES,
        "expected_treatment_increase_rows": PREFLIGHT_UP_ROWS,
        "expected_treatment_decrease_rows": PREFLIGHT_DOWN_ROWS,
        "roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {field: SOURCES[role][field] for field in
                   ("path", "sha256", "manifest", "manifest_sha256")}
            for role in ("remittances", "gdp_pc", "gdp_growth", key)
        },
        "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
    }


def load_roster() -> list[tuple[str, int]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("frozen key-roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    rows = [(r["country_iso3"], int(r["year"])) for r in records]
    if (len(rows) != ROSTER_ROWS or len({c for c, _ in rows}) != ROSTER_COUNTRIES
            or len(set(rows)) != len(rows) or rows != sorted(rows, key=lambda x: (x[1], x[0]))
            or any(not (c.isupper() and len(c) == 3 and T_START <= y <= T_END) for c, y in rows)):
        raise RuntimeError("frozen key-roster size, ISO3 form, or order mismatch")
    return rows


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER, TEST]
    for case in CASES.values():
        frozen += [spec_rel(case), steelman_rel(case)]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    countries = sorted({c for c, _ in load_roster()})
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec["hypothesis_id"] != case["id"] or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["steelman"] != steelman_rel(case)
                or spec["sample"]["countries"] != countries
                or spec["scope"]["countries"] != countries
                or spec["falsification"]["threshold"] != threshold_for(key, case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []):
            raise RuntimeError(f"registered spec mismatch: {key}")
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contains measured results")
    if git_output("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock must be in a later commit")
    return revision


def check_sources() -> dict[str, dict[str, Any]]:
    """Check byte hashes and tracked provenance without opening selected columns."""
    narrow: dict[str, dict[str, Any]] = {}
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} raw SHA-256 mismatch")
        manifest_path = ROOT / source["manifest"]
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch")
        manifest = yaml.safe_load(manifest_path.read_text())
        entries = [e for e in manifest.get("entries", [])
                   if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(entries) != 1 or entries[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} source-manifest entry mismatch")
        entry = entries[0]
        narrow[role] = {
            **source, "source_url": entry.get("source_url"),
            "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
            "rows": entry.get("rows"), "frequency": entry.get("frequency"),
            "units": entry.get("units"),
        }
    return narrow


def read_value_series(role: str, countries: set[str]) -> dict[tuple[str, int], float]:
    """Only remittances and prespecified GDP controls call this before locking."""
    if role not in ("remittances", "gdp_pc", "gdp_growth"):
        raise RuntimeError("selected outcome value access is forbidden in preflight")
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "indicator_id", "year", "value"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} WDI physical indicator/row-count mismatch")
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"{role} country-year key duplicated")
    return {(str(c), int(y)): float(v) for c, y, v
            in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}


def read_outcome_keys(role: str, countries: set[str]) -> set[tuple[str, int]]:
    """The only allowed pre-lock projection of a selected outcome parquet."""
    if role not in CASES:
        raise RuntimeError("not a selected outcome")
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "indicator_id", "year"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} WDI physical indicator/row-count mismatch")
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"{role} country-year key duplicated")
    return {(str(c), int(y)) for c, y
            in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def candidate_roster(
    remittances: dict[tuple[str, int], float],
    gdp_pc: dict[tuple[str, int], float],
    gdp_growth: dict[tuple[str, int], float],
    outcome_keys: dict[str, set[tuple[str, int]]],
    countries: set[str],
) -> list[tuple[str, int]]:
    """Use treatment/control values and selected outcome keys, never outcome data."""
    candidates = []
    for (country, year), current in remittances.items():
        if country not in countries or not T_START <= year <= T_END:
            continue
        previous = remittances.get((country, year - 1), math.nan)
        income = gdp_pc.get((country, year), math.nan)
        growth = gdp_growth.get((country, year), math.nan)
        if not all(math.isfinite(v) for v in (current, previous, income, growth)):
            continue
        if current < 0 or previous < 0 or income <= 0:
            continue
        if any((country, year) not in outcome_keys[key]
               or (country, year + case["horizon"]) not in outcome_keys[key]
               for key, case in CASES.items()):
            continue
        candidates.append((country, year))
    counts = Counter(country for country, _ in candidates)
    return sorted(((c, y) for c, y in candidates if counts[c] >= MIN_YEARS),
                  key=lambda item: (item[1], item[0]))


def source_preflight() -> tuple[list[tuple[str, int]], dict[str, dict[tuple[str, int], float]], dict[str, Any]]:
    roster = load_roster()
    countries = {country for country, _ in roster}
    controls = {role: read_value_series(role, countries)
                for role in ("remittances", "gdp_pc", "gdp_growth")}
    outcome_keys = {role: read_outcome_keys(role, countries) for role in CASES}
    rebuilt = candidate_roster(controls["remittances"], controls["gdp_pc"],
                               controls["gdp_growth"], outcome_keys, countries)
    if rebuilt != roster:
        raise RuntimeError("frozen treatment/control and outcome-key roster changed")
    changes = [controls["remittances"][(c, t)] - controls["remittances"][(c, t - 1)]
               for c, t in roster]
    up = sum(delta >= MATERIAL_DELTA_PP for delta in changes)
    down = sum(delta <= -MATERIAL_DELTA_PP for delta in changes)
    if up != PREFLIGHT_UP_ROWS or down != PREFLIGHT_DOWN_ROWS:
        raise RuntimeError("frozen treatment-only material-change counts changed")
    material = [(c, delta) for (c, _), delta in zip(roster, changes)
                if abs(delta) >= MATERIAL_DELTA_PP]
    squared = sum(delta * delta for _, delta in material)
    shares = Counter()
    for country, delta in material:
        shares[country] += delta * delta
    top_share = round(max(shares.values()) / squared, 12) if squared else math.nan
    report = {
        "treatment_and_control_values_read": True,
        "selected_outcome_columns_read": ["country_iso3", "indicator_id", "year"],
        "selected_outcome_values_read": False,
        "selected_outcome_null_masks_read": False,
        "selected_outcome_status_read": False,
        "roster_sha256": ROSTER_SHA,
        "key_rows": len(roster), "key_countries": len(countries),
        "treatment_years": [T_START, T_END],
        "treatment_increase_ge_1pp_rows": up,
        "treatment_decrease_le_minus_1pp_rows": down,
        "material_change_countries": len({c for c, _ in material}),
        "raw_exposure_top_country_squares_share": top_share,
        "outcome_key_rows": {role: len(keys) for role, keys in outcome_keys.items()},
    }
    return roster, controls, report


def key_preflight() -> dict[str, Any]:
    return source_preflight()[2]


def lock_payload(revision: str, sources: dict[str, dict[str, Any]],
                 preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "preregistration_commit": revision,
        "sources": sources, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
        "key_preflight": preflight,
        "outcome_values_opened_before_lock": False,
        "outcome_null_masks_opened_before_lock": False,
        "outcome_status_opened_before_lock": False,
        "whole_fetch_manifests_copied": False,
    }


def write_source_lock() -> None:
    revision = registration_commit()
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise RuntimeError("measured result artifacts exist before the source-lock commit")
    payload = lock_payload(revision, check_sources(), key_preflight())
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit it separately before opening either outcome measurement")


def check_source_lock(revision: str, sources: dict[str, dict[str, Any]],
                      preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, sources, preflight):
        raise RuntimeError("source lock differs from preregistration, exact pins, or preflight")
    lock_commit = first_addition(LOCK)
    if lock_commit == revision or subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, lock_commit], cwd=ROOT,
        check=False,
    ).returncode:
        raise RuntimeError("source-lock commit must descend from preregistration commit")
    committed_unchanged(LOCK, lock_commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", lock_commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return lock_commit


def authorized_measurement_context() -> tuple[str, str, list[tuple[str, int]], dict[str, dict[tuple[str, int], float]]]:
    """All chronology checks finish before a selected measurement can be opened."""
    revision = registration_commit()
    sources = check_sources()
    roster, controls, preflight = source_preflight()
    lock_commit = check_source_lock(revision, sources, preflight)
    return revision, lock_commit, roster, controls


def read_outcome_values(role: str, countries: set[str]) -> dict[tuple[str, int], tuple[float, str]]:
    """First selected measurement access; caller must pass the committed lock gate."""
    if role not in CASES:
        raise RuntimeError("not a selected outcome")
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} WDI physical indicator/row-count mismatch")
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"{role} country-year key duplicated")
    result = {}
    for country, year, value, status in frame[
        ["country_iso3", "year", "value", "obs_status"]
    ].itertuples(index=False, name=None):
        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError):
            numeric = math.nan
        result[(str(country), int(year))] = (
            numeric, "" if pd.isna(status) else str(status).strip()
        )
    return result


def build_measured_panel(
    roster: list[tuple[str, int]],
    controls: dict[str, dict[tuple[str, int], float]],
    outcome: dict[tuple[str, int], tuple[float, str]],
    case: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Pure transformation shared by real and synthetic inputs."""
    rows: list[dict[str, Any]] = []
    dropped_missing_or_invalid = 0
    dropped_status = 0
    for country, year in roster:
        baseline, baseline_status = outcome.get((country, year), (math.nan, ""))
        future, future_status = outcome.get((country, year + case["horizon"]), (math.nan, ""))
        if not (math.isfinite(baseline) and baseline >= 0
                and math.isfinite(future) and future >= 0):
            dropped_missing_or_invalid += 1
            continue
        if baseline_status or future_status:
            dropped_status += 1
            continue
        remittance_change = (
            controls["remittances"][(country, year)]
            - controls["remittances"][(country, year - 1)]
        )
        income = controls["gdp_pc"][(country, year)]
        growth = controls["gdp_growth"][(country, year)]
        if not (math.isfinite(remittance_change) and math.isfinite(income)
                and income > 0 and math.isfinite(growth)):
            raise RuntimeError("frozen treatment/control value became invalid")
        if case is CASES["registrations"] or case["id"] == CASES["registrations"]["id"]:
            baseline_term = math.log1p(baseline)
            response = math.log1p(future) - baseline_term
        else:
            baseline_term = baseline
            response = future - baseline
        rows.append({
            "country_iso3": country, "year": year,
            "remittance_change_pp": remittance_change,
            "baseline_outcome": baseline_term,
            "log_gdp_pc": math.log(income), "gdp_growth": growth,
            "outcome_change": response,
        })
    columns = ["country_iso3", "year", "remittance_change_pp", "baseline_outcome",
               "log_gdp_pc", "gdp_growth", "outcome_change"]
    panel = pd.DataFrame(rows, columns=columns)
    before_five_year_floor = len(panel)
    if len(panel):
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    material = panel.remittance_change_pp.abs().ge(MATERIAL_DELTA_PP)
    gate = {
        "roster_rows": len(roster),
        "dropped_missing_or_invalid_outcome_pairs": dropped_missing_or_invalid,
        "dropped_nonblank_outcome_status_pairs": dropped_status,
        "complete_pairs_before_five_year_country_floor": before_five_year_floor,
        "valid_rows": len(panel),
        "valid_countries": int(panel.country_iso3.nunique()),
        "material_exposure_rows": int(material.sum()),
        "material_exposure_countries": int(panel.loc[material, "country_iso3"].nunique()),
        "outcome_values_read_after_committed_lock": True,
    }
    return panel.sort_values(["year", "country_iso3"]).reset_index(drop=True), gate


def country_residualized_exposure_share(design: np.ndarray, treatment_column: int,
                                        groups: pd.Series) -> float | None:
    """FWL residual squares by country after all controls and fixed effects."""
    if design.shape[0] < 2 or design.shape[1] < 2:
        return None
    treatment = design[:, treatment_column]
    other = np.delete(design, treatment_column, axis=1)
    residual = treatment - other @ np.linalg.lstsq(other, treatment, rcond=None)[0]
    squares = np.square(residual)
    total = float(squares.sum())
    if not math.isfinite(total) or total <= 1e-12:
        return None
    frame = pd.DataFrame({"country_iso3": groups.to_numpy(), "squared": squares})
    return float(frame.groupby("country_iso3").squared.sum().max() / total)


def estimate(panel: pd.DataFrame, gate: dict[str, Any],
             case: dict[str, Any]) -> dict[str, Any]:
    gate = dict(gate)
    if (gate["valid_rows"] < MIN_COMPLETE_ROWS
            or gate["valid_countries"] < MIN_COMPLETE_COUNTRIES
            or gate["material_exposure_countries"] < MIN_MATERIAL_COUNTRIES):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or material-exposure floor failed",
                "primary": None}
    formula = (
        "outcome_change ~ remittance_change_pp + baseline_outcome + "
        "log_gdp_pc + gdp_growth + C(country_iso3) + C(year)"
    )
    model = smf.ols(formula, data=panel)
    if (model.exog.shape[0] != len(panel)
            or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "prespecified fixed-effect design lacks full rank",
                "primary": None}
    treatment_column = model.exog_names.index("remittance_change_pp")
    share = country_residualized_exposure_share(
        model.exog, treatment_column, panel.country_iso3
    )
    gate["top_country_residualized_exposure_share"] = share
    if share is None or share > MAX_COUNTRY_RESIDUAL_SHARE:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residualized-exposure concentration gate failed",
                "primary": None}
    groups = gate["valid_countries"]
    fit = model.fit(
        cov_type="cluster",
        cov_kwds={"groups": panel.country_iso3,
                  "use_correction": True, "df_correction": True},
        use_t=True,
    )
    beta = float(fit.params["remittance_change_pp"])
    se = float(fit.bse["remittance_change_pp"])
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "country-cluster uncertainty is nonfinite or nonpositive",
                "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, groups - 1))
    if not (math.isfinite(p) and math.isfinite(critical)):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "country-cluster inference is nonfinite", "primary": None}
    primary = {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 1 - P_MAX,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": groups,
        "df_inference": groups - 1, "model_rank": int(fit.model.rank),
        "top_country_residualized_exposure_share": share,
        "method": "country/year FE OLS with baseline outcome and GDP controls; country-cluster CR1; Student t(G-1)",
    }
    meaningful = case["meaningful_beta"]
    if beta >= meaningful and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive association clears frozen magnitude and family p cutoff"
    elif beta <= -meaningful and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears frozen magnitude and family p cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def result_card(case: dict[str, Any], result: dict[str, Any],
                registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    lines = [
        f"# Result card: {case['id']}", "",
        f"Verdict: **{result['verdict']}**. {result['reason']}.", "",
        f"Frozen preregistration: `{registration}`; source-lock commit: `{lock_commit}`.", "",
        f"Treatment/control and outcome-key roster: {ROSTER_ROWS} country-years / {ROSTER_COUNTRIES} countries.",
        f"Complete measured pairs: {gate['valid_rows']} / {gate['valid_countries']} countries; "
        f"material exposure: {gate['material_exposure_rows']} rows / "
        f"{gate['material_exposure_countries']} countries.", "",
    ]
    if primary is not None:
        lines += [
            f"Primary beta per +1 GDP percentage point remittance-share change: "
            f"{primary['coefficient']:+.6g} {case['unit']}; "
            f"country-cluster SE={primary['std_error']:.6g}; "
            f"two-sided t p={primary['p_value_two_sided']:.6g}; "
            f"99.5% CI={primary['confidence_interval']}.", "",
        ]
    lines += [
        "Two fixed tests; Bonferroni family alpha 0.01, each two-sided p<=0.005.",
        "Descriptive calibration only. No causal, policy, school, or featured credit.", "",
    ]
    return "\n".join(lines)


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any],
                     registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    inputs = {role: SOURCES[role] for role in ("remittances", "gdp_pc", "gdp_growth", key)}
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": case["id"], "path": spec_rel(case), "topic": "growth"},
        "preregistration": {
            "spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": 2,
            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
            "steelman": steelman_rel(case),
        },
        "reproduction": {
            "runner": RUNNER, "run_dir": run_rel(case),
            "command": f"python3 {RUNNER} --verify",
        },
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": inputs, "sample": gate},
        "results": {"primary": primary},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": case["id"], "family_id": FAMILY,
        "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "primary": primary,
        "p_max_two_sided_bonferroni": P_MAX,
        "meaningful_beta_min_abs": case["meaningful_beta"],
        "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": case["id"], "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
        "derived_panel": gate, "correction": CORRECTION,
    }
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    coeff_columns = [
        "term", "coefficient", "std_error", "p_value_two_sided",
        "ci_low", "ci_high", "n_rows", "n_countries", "df_inference", "model_rank",
        "top_country_residualized_exposure_share", "method",
    ]
    coefficients = (
        [{
            "term": "remittance_change_pp",
            **{field: primary[field] for field in coeff_columns if field not in ("term", "ci_low", "ci_high")},
            "ci_low": primary["confidence_interval"][0],
            "ci_high": primary["confidence_interval"][1],
        }] if primary is not None else []
    )
    return {
        "packet": packet, "diagnostics": diagnostics, "manifest": manifest,
        "card": result_card(case, result, registration, lock_commit),
        "wrapper": wrapper,
        "chart": {"hypothesis_id": case["id"], "family_id": FAMILY,
                  "verdict": verdict, "primary": primary},
        "coefficients": pd.DataFrame(coefficients, columns=coeff_columns),
    }


def summary_text(results: dict[str, dict[str, Any]],
                 registration: str, lock_commit: str) -> str:
    lines = [
        "# Remittance changes, secondary enrolment and formal entry: two-test result", "",
        f"Preregistration `{registration}`; source lock `{lock_commit}`.",
        "Both tests remain in one Bonferroni family (alpha 0.01; each two-sided p<=0.005).", "",
        "| Outcome | Verdict | Complete pairs / countries | Material rows / countries | Beta per +1 pp | Two-sided p |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(
            f"| {case['label']} | **{result['verdict']}** | "
            f"{gate['valid_rows']} / {gate['valid_countries']} | "
            f"{gate['material_exposure_rows']} / {gate['material_exposure_countries']} | "
            f"{beta} | {p} |"
        )
    lines += [
        "",
        "The coefficients describe forward country-year associations per one GDP percentage point increase "
        "in personal remittances received from t-1 to t, conditional on baseline outcome, GDP controls, "
        "and country and treatment-year effects. The registration endpoint is formal limited-liability entry "
        "and the school endpoint is gross enrolment, not attainment.",
        "",
        "The local two-test correction does not adjust for the older remittance, schooling, or business-entry "
        "archive. No causal, policy, school, or featured credit.", "",
    ]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]],
                    registration: str, lock_commit: str) -> None:
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
        payload["coefficients"].to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def verify_artifacts(results: dict[str, dict[str, Any]],
                     registration: str, lock_commit: str) -> None:
    for key, case in CASES.items():
        folder = ROOT / run_rel(case)
        diagnostics = json.loads((folder / "diagnostics.json").read_text())
        stamp = diagnostics["run_utc"]
        expected = artifact_payload(key, case, results[key], registration, lock_commit, stamp)
        actual_packet = yaml.safe_load((folder / "evidence_packet.yaml").read_text())
        actual_manifest = yaml.safe_load((folder / "manifest.yaml").read_text())
        actual_chart = json.loads((folder / "chart_data.json").read_text())
        for label, actual, wanted in (
            ("packet", actual_packet, expected["packet"]),
            ("diagnostics", diagnostics, expected["diagnostics"]),
            ("manifest", actual_manifest, expected["manifest"]),
            ("chart", actual_chart, expected["chart"]),
        ):
            if actual != wanted:
                raise AssertionError(f"{case['id']} {label} differs from measured replay")
        if (folder / "result_card.md").read_text() != expected["card"]:
            raise AssertionError(f"{case['id']} result card differs")
        if (folder / "replication.py").read_text() != expected["wrapper"]:
            raise AssertionError(f"{case['id']} replication wrapper differs")
        if (folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes():
            raise AssertionError(f"{case['id']} frozen hypothesis copy differs")
        observed_coefficients = pd.read_parquet(folder / "coefficients.parquet")
        pd.testing.assert_frame_equal(
            observed_coefficients, expected["coefficients"],
            check_dtype=False, check_exact=False, rtol=1e-11, atol=1e-12,
        )
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from measured replay")
    print("verified two frozen remittance forward calibrations")


def execute_measured(mode: str) -> dict[str, dict[str, Any]]:
    registration, lock_commit, roster, controls = authorized_measurement_context()
    countries = {c for c, _ in roster}
    outcomes = {key: read_outcome_values(key, countries) for key in CASES}
    results = {}
    for key, case in CASES.items():
        panel, gate = build_measured_panel(roster, controls, outcomes[key], case)
        results[key] = estimate(panel, gate, case)
    if mode == "run":
        write_artifacts(results, registration, lock_commit)
    elif mode == "verify":
        verify_artifacts(results, registration, lock_commit)
    else:
        raise RuntimeError("unknown measured execution mode")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--lock", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps({"sources": check_sources(), "key_preflight": key_preflight()}, indent=2))
        return 0
    if args.lock:
        write_source_lock()
        return 0
    results = execute_measured("run" if args.run else "verify")
    for key, result in results.items():
        print(key, result["verdict"], result["gate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
