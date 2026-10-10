#!/usr/bin/env python3
"""Frozen two-exposure WASH coverage and later child mortality family.

Preflight reads WHO exposure and WDI income values, but only WDI mortality keys.
Mortality values are inaccessible to this runner until registration and a later
source-lock commit both exist and match their first-addition bytes.
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
import pycountry
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wash_service_child_mortality_forward_2026_10_10"
RUNNER = "scripts/run_wash_child_mortality_2026.py"
TEST = "tests/test_wash_child_mortality_2026.py"
PREREG = "engine/audits/wash_child_mortality_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wash_child_mortality_2026_key_roster.csv"
ROSTER_SHA = "ad59eb9f838b41eb3e1f30babd35dc05370a684b30a4403f240792505e076af9"
LOCK = "data/pinned_evidence/wash_child_mortality_2026.manifest.json"
SUMMARY = "engine/audits/wash_child_mortality_results_2026-10-10.md"
WDI_A = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
WDI_A_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
WHO = "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml"
WHO_SHA = "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"
SOURCES = {
    "income": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": WDI_A, "manifest_sha256": WDI_A_SHA},
    "mortality": {"publisher": "world_bank_wdi", "series_id": "SH.DYN.MORT",
        "path": "data/vintages/world_bank_wdi/SH.DYN.MORT@2026-05-05T194907Z.parquet",
        "sha256": "ad63729ccd5d1d4be6f3da5bbcac45b8a2c87d48c063cefeba8f0ddbe4b88f55",
        "manifest": WDI_A, "manifest_sha256": WDI_A_SHA},
    "water": {"publisher": "who_gho", "series_id": "WSH_WATER_SAFELY_MANAGED",
        "path": "data/vintages/who_gho/WSH_WATER_SAFELY_MANAGED@2026-04-30T114745Z.parquet",
        "sha256": "c0ed754e9d42fda94390ebbe2be36fc630e4e2e8e05f9a1a57aeb75178a6bc91",
        "manifest": WHO, "manifest_sha256": WHO_SHA},
    "sanitation": {"publisher": "who_gho", "series_id": "WSH_SANITATION_SAFELY_MANAGED",
        "path": "data/vintages/who_gho/WSH_SANITATION_SAFELY_MANAGED@2026-04-30T114745Z.parquet",
        "sha256": "c55eb958ce8409eafc335fb20eb74a0562d8650d6a3372e141f2e64243d4b077",
        "manifest": WHO, "manifest_sha256": WHO_SHA},
}
CASES = {
    "water": {"id": "wash_safe_water_under5_mortality_forward_2026",
        "label": "prior national safely managed drinking water rise", "key_rows": 696,
        "key_countries": 142, "rise_rows": 189, "rise_countries": 52,
        "flat_rows": 174, "flat_countries": 53,
        "min_rows": 500, "min_countries": 100},
    "sanitation": {"id": "wash_safe_sanitation_under5_mortality_forward_2026",
        "label": "prior national safely managed sanitation rise", "key_rows": 683,
        "key_countries": 139, "rise_rows": 264, "rise_countries": 64,
        "flat_rows": 115, "flat_countries": 45,
        "min_rows": 500, "min_countries": 100},
}
ANCHORS = (2004, 2008, 2012, 2016, 2020)
ISO3 = frozenset({country.alpha_3 for country in pycountry.countries} | {"XKX"})
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_ABS_BETA = 0.002  # log under-five mortality change per +1 service point
MIN_ANCHORS_PER_COUNTRY = 3
MIN_VALID_ANCHORS = 4
MIN_RISE_ROWS, MIN_RISE_COUNTRIES = 80, 25
MIN_FLAT_ROWS, MIN_FLAT_COUNTRIES = 20, 10
MATERIAL_RISE, FLAT_CHANGE = 2.0, 0.2
MAX_RAW_CHANGE = 30.0
MAX_TOP_ONE_PERCENT = 0.25
MAX_COUNTRY = 0.15
MAX_ANCHOR = 0.35
CORRECTION = {
    "family_scope": "retrospective_descriptive_calibration", "family_id": FAMILY,
    "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
    "bonferroni_p_max": P_MAX, "causal_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0,
    "featured_eligible": False,
}
LIMITATIONS = [
    "WHO/UNICEF JMP national safe water and sanitation shares are modeled estimates, not infrastructure investment or randomized treatment.",
    "WDI under-five mortality is a UN IGME modeled probability per 1,000 live births, not individual death records.",
    "Water and sanitation coverage co-move and are correlated exposures; two records are one question family.",
    "Health-system expansion, vaccination, fertility, income, conflict, service measurement, and country-specific trends can confound every estimate.",
    "Country/anchor effects, baseline mortality, prior mortality trend, service baseline, and income controls do not identify a causal WASH effect.",
    "This retrospectively selected family uses a local two-test correction; it does not correct the wider IESET archive or supply independent replication.",
    "WHO source manifest records CC-BY-NC-SA-3.0 IGO; source-rights review is required before distributing raw files or publishing derived displays.",
    "Zero causal, policy, school, position, and featured credit for all outcomes.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git_bytes("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def unchanged_since(relative: str, revision: str) -> None:
    if (ROOT / relative).read_bytes() != git_bytes("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from its first-addition commit: {relative}")
    if git_bytes("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_path(role: str) -> str:
    return f"hypotheses/healthcare/{CASES[role]['id']}.yaml"


def steelman_path(role: str) -> str:
    return f"hypotheses/steelman/{CASES[role]['id']}.md"


def run_dir(role: str) -> str:
    return f"engine/runs/{CASES[role]['id']}"


def source_metadata(source_root: Path) -> dict[str, dict[str, Any]]:
    """Verify exact bytes and provenance, without projecting WHO value columns."""
    locked = {}
    for role, source in SOURCES.items():
        path = source_root / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned source: {role}")
        manifest = ROOT / source["manifest"]
        if not manifest.is_file() or sha256(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched tracked manifest: {role}")
        matches = [entry for entry in yaml.safe_load(manifest.read_text()).get("entries", [])
                   if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]
                   and entry.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"manifest lacks exact source entry: {role}")
        entry = matches[0]
        locked[role] = {**source, "source_url": entry.get("source_url"),
                        "methodology_url": entry.get("methodology_url"),
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc")}
    return locked


def wdi_income_values(source_root: Path) -> dict[tuple[str, int], float]:
    role = "income"
    source = SOURCES[role]
    frame = pd.read_parquet(source_root / source["path"],
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"wrong WDI indicator in {role}")
    frame = frame.loc[frame.country_iso3.isin(ISO3)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate national WDI keys in {role}")
    values = {}
    for c, y, raw, status in frame[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None):
        try:
            number = float(raw)
        except (ValueError, TypeError, OverflowError):
            continue
        if not math.isfinite(number) or not (pd.isna(status) or str(status).strip() == ""):
            continue
        if number <= 0:
            continue
        values[(str(c), int(y))] = number
    return values


def mortality_keys(source_root: Path) -> set[tuple[str, int]]:
    """Read only WDI country/year/indicator keys before the source-lock commit."""
    frame = pd.read_parquet(source_root / SOURCES["mortality"]["path"],
                            columns=["country_iso3", "indicator_id", "year"])
    if not frame.indicator_id.eq(SOURCES["mortality"]["series_id"]).all():
        raise RuntimeError("wrong WDI mortality indicator")
    frame = frame.loc[frame.country_iso3.isin(ISO3)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate national WDI mortality keys")
    return {(str(c), int(y)) for c, y in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def who_exposure_values(source_root: Path, role: str) -> dict[tuple[str, int], float]:
    """Exposure values may be read before outcome registration."""
    if role not in CASES:
        raise RuntimeError("not a selected WHO exposure")
    frame = pd.read_parquet(source_root / SOURCES[role]["path"], columns=[
        "country_iso3", "year", "IndicatorCode", "SpatialDimType", "Dim1Type", "Dim1", "value"])
    if not frame.IndicatorCode.eq(SOURCES[role]["series_id"]).all():
        raise RuntimeError(f"wrong WHO exposure indicator for {role}")
    frame = frame.loc[frame.country_iso3.isin(ISO3)
                      & frame.SpatialDimType.eq("COUNTRY")
                      & frame.Dim1Type.eq("RESIDENCEAREATYPE")
                      & frame.Dim1.eq("RESIDENCEAREATYPE_TOTL")]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate total-country-year WHO keys in {role}")
    result = {}
    for c, y, raw in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None):
        try:
            number = float(raw)
        except (ValueError, TypeError, OverflowError):
            continue
        if math.isfinite(number) and 0 <= number <= 100:
            result[(str(c), int(y))] = number
    return result


def candidate_rows(role: str, exposure: dict[tuple[str, int], float],
                   income: dict[tuple[str, int], float],
                   keys: set[tuple[str, int]]) -> list[tuple[str, str, int]]:
    possible = []
    for c in sorted(ISO3):
        for anchor in ANCHORS:
            if any((c, y) not in keys for y in (anchor - 4, anchor, anchor + 4)):
                continue
            if any((c, y) not in exposure or (c, y) not in income for y in (anchor - 4, anchor)):
                continue
            if abs(exposure[c, anchor] - exposure[c, anchor - 4]) > MAX_RAW_CHANGE:
                continue
            possible.append((role, c, anchor))
    counts = Counter(c for _, c, _ in possible)
    return [(role, c, a) for role, c, a in possible if counts[c] >= MIN_ANCHORS_PER_COUNTRY]


def load_roster() -> list[tuple[str, str, int]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("frozen key-roster SHA-256 mismatch")
    raw = path.read_bytes()
    if not raw.startswith(b"exposure,country_iso3,anchor_year\n"):
        raise RuntimeError("frozen key-roster header changed")
    rows = [(record["exposure"], record["country_iso3"], int(record["anchor_year"]))
            for record in csv.DictReader(io.StringIO(raw.decode()))]
    if rows != sorted(set(rows), key=lambda row: (row[0], row[2], row[1])):
        raise RuntimeError("frozen key-roster order or uniqueness changed")
    for role, case in CASES.items():
        subset = [(r, c, a) for r, c, a in rows if r == role]
        if len(subset) != case["key_rows"] or len({c for _, c, _ in subset}) != case["key_countries"]:
            raise RuntimeError(f"frozen key-roster shape changed for {role}")
    if any(r not in CASES or c not in ISO3 or a not in ANCHORS for r, c, a in rows):
        raise RuntimeError("invalid selected role, national ISO3, or anchor")
    return rows


def preflight(source_root: Path) -> tuple[list[tuple[str, str, int]], dict[str, dict[tuple[str, int], float]], dict[str, Any]]:
    roster = load_roster()
    values = {"income": wdi_income_values(source_root),
              **{role: who_exposure_values(source_root, role) for role in CASES}}
    keys = mortality_keys(source_root)
    reconstructed = [row for role in CASES for row in candidate_rows(role, values[role], values["income"], keys)]
    reconstructed.sort(key=lambda row: (row[0], row[2], row[1]))
    if reconstructed != roster:
        raise RuntimeError("frozen roster differs from exposure/control values and WHO keys")
    by_role = {}
    for role, case in CASES.items():
        subset = [(c, a) for r, c, a in roster if r == role]
        changes = [(c, values[role][c, a] - values[role][c, a - 4]) for c, a in subset]
        rise = [(c, x) for c, x in changes if x >= MATERIAL_RISE]
        flat = [(c, x) for c, x in changes if abs(x) <= FLAT_CHANGE]
        observed = (len(rise), len({c for c, _ in rise}), len(flat), len({c for c, _ in flat}))
        expected = (case["rise_rows"], case["rise_countries"], case["flat_rows"], case["flat_countries"])
        if observed != expected:
            raise RuntimeError(f"frozen exposure-only counts changed for {role}: {observed}")
        by_role[role] = {"key_rows": len(subset), "key_countries": case["key_countries"],
                         "material_rise_rows": observed[0], "material_rise_countries": observed[1],
                         "flat_rows": observed[2], "flat_countries": observed[3]}
    report = {"outcome_columns_read": ["country_iso3", "indicator_id", "year"],
              "outcome_values_read": False, "outcome_null_masks_read": False,
              "anchors": list(ANCHORS), "roster_sha256": ROSTER_SHA,
              "by_outcome": by_role}
    return roster, values, report


def threshold(role: str) -> dict[str, Any]:
    case = CASES[role]
    return {
        "family_id": FAMILY, "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
        "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "-",
        "meaningful_abs_beta": MIN_ABS_BETA,
        "min_complete_rows": case["min_rows"], "min_complete_countries": case["min_countries"],
        "min_complete_anchors": MIN_VALID_ANCHORS,
        "min_anchors_per_country": MIN_ANCHORS_PER_COUNTRY,
        "material_rise_min_raw_pp": MATERIAL_RISE,
        "min_material_rise_rows": MIN_RISE_ROWS,
        "min_material_rise_countries": MIN_RISE_COUNTRIES,
        "flat_change_max_abs_raw_pp": FLAT_CHANGE,
        "min_flat_rows": MIN_FLAT_ROWS, "min_flat_countries": MIN_FLAT_COUNTRIES,
        "max_abs_raw_service_change": MAX_RAW_CHANGE,
        "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT,
        "max_top_country_residual_x_share": MAX_COUNTRY,
        "max_top_anchor_residual_x_share": MAX_ANCHOR,
        "expected_key_rows": case["key_rows"],
        "expected_key_countries": case["key_countries"],
        "roster_sha256": ROSTER_SHA,
        "source_files": {source_role: {field: source[field] for field in
                         ("path", "sha256", "manifest", "manifest_sha256")}
                         for source_role, source in SOURCES.items() if source_role in ("mortality", "income", role)},
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }


def registration_commit() -> str:
    paths = [RUNNER, TEST, PREREG, ROSTER]
    for role in CASES:
        paths.extend([spec_path(role), steelman_path(role)])
    additions = {first_addition(path) for path in paths}
    if len(additions) != 1:
        raise RuntimeError("blind registration files lack one common first-addition commit")
    revision = additions.pop()
    for path in paths:
        unchanged_since(path, revision)
    if git_bytes("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("registration already contained source lock")
    for role, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_path(role)).read_text())
        countries = sorted({c for r, c, _ in load_roster() if r == role})
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("claim_direction") != "-" or spec.get("evidence_type") != "associational"
                or spec.get("sample", {}).get("countries") != countries
                or spec.get("sample", {}).get("period") != [2004, 2024]
                or spec.get("falsification", {}).get("threshold") != threshold(role)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != [] or spec.get("steelman") != steelman_path(role)):
            raise RuntimeError(f"frozen spec disagrees with runner for {role}")
        if git_bytes("ls-tree", "-r", "--name-only", revision, "--", run_dir(role)).strip():
            raise RuntimeError("registration already contained measured run")
    return revision


def lock_payload(registration: str, selected: dict[str, dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
            "selected_sources": selected, "key_preflight": report,
            "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_raw_sources_copied": False}


def write_lock(source_root: Path) -> None:
    registration = registration_commit()
    if (ROOT / LOCK).exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("source lock or result already exists")
    selected = source_metadata(source_root)
    _, _, report = preflight(source_root)
    (ROOT / LOCK).write_text(json.dumps(lock_payload(registration, selected, report), indent=2, sort_keys=True) + "\n")


def committed_lock(registration: str, selected: dict[str, dict[str, Any]], report: dict[str, Any]) -> str:
    revision = first_addition(LOCK)
    if revision == registration or subprocess.run(
        ["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT
    ).returncode:
        raise RuntimeError("source lock must be separately committed after registration")
    unchanged_since(LOCK, revision)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, selected, report):
        raise RuntimeError("source-lock payload differs from frozen sources and key preflight")
    for role in CASES:
        if git_bytes("ls-tree", "-r", "--name-only", revision, "--", run_dir(role)).strip():
            raise RuntimeError("source-lock commit already contained measured run")
    return revision


def mortality_values(source_root: Path) -> dict[tuple[str, int], float]:
    """First outcome-value/null-mask read; caller checked both earlier commits."""
    frame = pd.read_parquet(source_root / SOURCES["mortality"]["path"],
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if not frame.indicator_id.eq(SOURCES["mortality"]["series_id"]).all():
        raise RuntimeError("wrong WDI mortality indicator")
    frame = frame.loc[frame.country_iso3.isin(ISO3)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate national WDI mortality values")
    result = {}
    for c, y, raw, status in frame[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None):
        try:
            value = float(raw)
        except (ValueError, TypeError, OverflowError):
            continue
        if math.isfinite(value) and 0 < value <= 500 and (pd.isna(status) or str(status).strip() == ""):
            result[(str(c), int(y))] = value
    return result


def measured_panel(role: str, roster: list[tuple[str, str, int]],
                   support: dict[str, dict[tuple[str, int], float]],
                   outcome: dict[tuple[str, int], float]) -> tuple[pd.DataFrame, dict[str, Any]]:
    exposure, income = support[role], support["income"]
    selected = [(c, a) for r, c, a in roster if r == role]
    rows = []
    missing_or_invalid = 0
    for c, anchor in selected:
        levels = [outcome.get((c, y), math.nan) for y in (anchor - 4, anchor, anchor + 4)]
        if not all(math.isfinite(v) and 0 < v <= 500 for v in levels):
            missing_or_invalid += 1
            continue
        prior, baseline, future = levels
        rows.append({
            "country_iso3": c, "anchor": anchor,
            "x": exposure[c, anchor] - exposure[c, anchor - 4],
            "prior_service_share": exposure[c, anchor - 4],
            "log_baseline_mortality": math.log(baseline),
            "prior_log_mortality_change": math.log(baseline / prior),
            "log_income": math.log(income[c, anchor]),
            "prior_log_income_change": math.log(income[c, anchor]) - math.log(income[c, anchor - 4]),
            "y": math.log(future / baseline),
        })
    columns = ["country_iso3", "anchor", "x", "prior_service_share", "log_baseline_mortality",
               "prior_log_mortality_change", "log_income", "prior_log_income_change", "y"]
    panel = pd.DataFrame(rows, columns=columns)
    before_country_floor = len(panel)
    if len(panel):
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_ANCHORS_PER_COUNTRY)].copy()
    panel = panel.sort_values(["anchor", "country_iso3"]).reset_index(drop=True)
    rise = panel.loc[panel.x.ge(MATERIAL_RISE), "country_iso3"]
    flat = panel.loc[panel.x.abs().le(FLAT_CHANGE), "country_iso3"]
    gate = {"key_rows": len(selected), "missing_or_invalid_outcome_triples": missing_or_invalid,
            "complete_rows_before_country_floor": before_country_floor,
            "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
            "valid_anchors": int(panel.anchor.nunique()),
            "material_rise_rows": len(rise), "material_rise_countries": int(rise.nunique()),
            "flat_rows": len(flat), "flat_countries": int(flat.nunique()),
            "selected_outcome_values_read_after_committed_lock": True}
    return panel, gate


def concentration(design: np.ndarray, treatment_index: int, panel: pd.DataFrame) -> dict[str, float] | None:
    other = np.delete(design, treatment_index, axis=1)
    x = design[:, treatment_index]
    residual = x - other @ np.linalg.lstsq(other, x, rcond=None)[0]
    weight = np.square(residual)
    total = float(weight.sum())
    if not math.isfinite(total) or total <= 1e-12:
        return None
    top = max(1, math.ceil(len(weight) / 100))
    frame = pd.DataFrame({"country": panel.country_iso3.to_numpy(),
                          "anchor": panel.anchor.to_numpy(), "weight": weight})
    return {"top_one_percent_rows": float(np.sort(weight)[-top:].sum() / total),
            "top_country": float(frame.groupby("country").weight.sum().max() / total),
            "top_anchor": float(frame.groupby("anchor").weight.sum().max() / total)}


def estimate(role: str, panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    case = CASES[role]
    gate = dict(gate)
    if (gate["valid_rows"] < case["min_rows"] or gate["valid_countries"] < case["min_countries"]
            or gate["valid_anchors"] < MIN_VALID_ANCHORS
            or gate["material_rise_rows"] < MIN_RISE_ROWS
            or gate["material_rise_countries"] < MIN_RISE_COUNTRIES
            or gate["flat_rows"] < MIN_FLAT_ROWS
            or gate["flat_countries"] < MIN_FLAT_COUNTRIES):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen completeness, time, or exposure-support floor failed",
                "gate": gate, "primary": None}
    formula = ("y ~ x + prior_service_share + log_baseline_mortality + prior_log_mortality_change + "
               "log_income + prior_log_income_change + C(country_iso3) + C(anchor)")
    model = smf.ols(formula, data=panel)
    design = model.exog
    if design.shape[0] != len(panel) or np.linalg.matrix_rank(design) != design.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "frozen fixed-effects design lacks full rank",
                "gate": gate, "primary": None}
    shares = concentration(design, model.exog_names.index("x"), panel)
    gate["residual_exposure_concentration"] = shares
    if (shares is None or shares["top_one_percent_rows"] > MAX_TOP_ONE_PERCENT
            or shares["top_country"] > MAX_COUNTRY or shares["top_anchor"] > MAX_ANCHOR):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen residual-exposure concentration gate failed",
                "gate": gate, "primary": None}
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                    "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    countries = gate["valid_countries"]
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return {"verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive clustered uncertainty",
                "gate": gate, "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), countries - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, countries - 1))
    if not (math.isfinite(p) and math.isfinite(critical)):
        return {"verdict": "INCONCLUSIVE", "reason": "nonfinite country-cluster inference",
                "gate": gate, "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 1 - P_MAX,
               "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": countries,
               "df_inference": countries - 1, "design_rank": int(fit.model.rank),
               "method": "country/anchor FE OLS with baseline and prior mortality trend, prior service share and income controls; country-cluster CR1, Student t(G-1)"}
    if beta <= -MIN_ABS_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "registered service-improvement association clears size and family significance gates"
    elif beta >= MIN_ABS_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears size and family significance gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate": gate, "primary": primary}


def tier(verdict: str) -> str:
    return "inconclusive_archive" if verdict == "INCONCLUSIVE" else "public_descriptive_calibration"


def artifact(role: str, result: dict[str, Any], registration: str,
             lock_commit: str, stamp: str) -> dict[str, Any]:
    case, gate, primary = CASES[role], result["gate"], result["primary"]
    inputs = {source_role: SOURCES[source_role] for source_role in ("mortality", "income", role)}
    diagnostic = {
        "hypothesis_id": case["id"], "family_id": FAMILY,
        "verdict": result["verdict"], "verdict_label": result["verdict"],
        "verdict_reason": result["reason"], "publication_tier": tier(result["verdict"]),
        "run_utc": stamp, "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK, "template": "panel_fe",
        "preflight": gate, "primary": primary,
        "analysis_scope": "descriptive_only", "data_status": {"variables_missing": [],
            "input_vintages": list(inputs.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": case["id"], "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": result["verdict"],
                "publication_tier": tier(result["verdict"]),
                "vintages": list(inputs.values()), "derived_panel": gate,
                "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": case["id"], "path": spec_path(role), "topic": "healthcare"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                  "family_id": FAMILY, "family_size": len(CASES),
                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                  "steelman": steelman_path(role)},
              "reproduction": {"runner": RUNNER, "run_dir": run_dir(role),
                  "command": f"python3 {RUNNER} --verify --source-root <PINNED_SOURCE_ROOT>"},
              "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                  "reason": result["reason"], "publication_tier": tier(result["verdict"])},
              "data": {"inputs": inputs, "sample": gate},
              "results": {"primary": primary}, "limitations": LIMITATIONS,
              "correction": CORRECTION}
    lines = [f"# Result card: {case['id']}", "",
             f"Verdict: **{result['verdict']}**. {result['reason']}.", "",
             f"Disposition: **{tier(result['verdict'])}**. One of two correlated WASH exposures.", "",
             f"Registration `{registration}`; source lock `{lock_commit}`.", "",
             f"Complete rows: {gate['valid_rows']} across {gate['valid_countries']} countries; "
             f"material rises {gate['material_rise_rows']}; flat exposures {gate['flat_rows']}.", ""]
    if primary is not None:
        lines.extend([f"Beta={primary['coefficient']:+.6g} next-period log under-five mortality change "
                      f"per +1 point prior national safe-service rise; SE={primary['std_error']:.6g}; "
                      f"two-sided p={primary['p_value_two_sided']:.6g}; "
                      f"family-adjusted CI={primary['confidence_interval']}.", ""])
    lines.extend(["WHO/JMP exposures and UN IGME under-five mortality are modeled estimates, not interventions or individual records.",
                  "Zero causal, policy, school, position, or featured credit.", ""])
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify', "
               "'--source-root', str(root)], cwd=root))\n")
    coeff_cols = ["term", "coefficient", "std_error", "p_value_two_sided", "ci_low", "ci_high",
                  "n_rows", "n_countries", "df_inference", "design_rank", "method"]
    coeff = ([] if primary is None else [{"term": "safe_service_prior_change_pp",
        "coefficient": primary["coefficient"], "std_error": primary["std_error"],
        "p_value_two_sided": primary["p_value_two_sided"],
        "ci_low": primary["confidence_interval"][0], "ci_high": primary["confidence_interval"][1],
        "n_rows": primary["n_rows"], "n_countries": primary["n_countries"],
        "df_inference": primary["df_inference"], "design_rank": primary["design_rank"],
        "method": primary["method"]}])
    return {"diagnostic": diagnostic, "manifest": manifest, "packet": packet,
            "card": "\n".join(lines), "wrapper": wrapper,
            "chart": {"hypothesis_id": case["id"], "family_id": FAMILY,
                      "verdict": result["verdict"], "publication_tier": tier(result["verdict"]),
                      "primary": primary},
            "coefficients": pd.DataFrame(coeff, columns=coeff_cols)}


def summary(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# National WASH services and later under-five mortality: frozen descriptive results", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "Two correlated exposure tests; family alpha .01, two-sided Bonferroni p<=.005 per exposure.", "",
             "| Prior service exposure | Verdict | Disposition | Complete rows / countries | Beta | Two-sided p |",
             "| --- | --- | --- | ---: | ---: | ---: |"]
    for role, case in CASES.items():
        result, gate = results[role], results[role]["gate"]
        primary = result["primary"]
        beta = "not estimated" if primary is None else f"{primary['coefficient']:+.6g}"
        p = "not estimated" if primary is None else f"{primary['p_value_two_sided']:.6g}"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {tier(result['verdict'])} | "
                     f"{gate['valid_rows']} / {gate['valid_countries']} | {beta} | {p} |")
    lines.extend(["", "National WHO/JMP safely managed service share changes from t-4 to t are descriptive exposures, "
                  "not assigned treatments. WDI under-five mortality changes on a log scale from t to t+4. "
                  "Five adjacent but nonoverlapping four-year outcome windows use anchors 2004, 2008, 2012, 2016, 2020. "
                  "Country and anchor effects, baseline mortality, prior mortality change, prior service share, "
                  "baseline real income, and prior income growth are fixed controls.", "",
                  "SUPPORTED, REFUTED, and gate-cleared PARTIAL receive public descriptive calibration only; "
                  "INCONCLUSIVE is archived. These two records are one correlated research family, with "
                  "zero causal, policy, school, position, and featured credit. WHO data carry a noncommercial "
                  "share-alike license, so publication awaits source-rights review. The local two-test "
                  "correction does not adjust wider IESET archive selection.", ""])
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if (ROOT / SUMMARY).exists() or any((ROOT / run_dir(role)).exists() for role in CASES):
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for role in CASES:
        data = artifact(role, results[role], registration, lock_commit, stamp)
        folder = ROOT / run_dir(role)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_path(role)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(data["diagnostic"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(data["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(data["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(data["card"])
        (folder / "replication.py").write_text(data["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(data["chart"], indent=2) + "\n")
        data["coefficients"].to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary(results, registration, lock_commit))


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for role in CASES:
        folder = ROOT / run_dir(role)
        saved = json.loads((folder / "diagnostics.json").read_text())
        data = artifact(role, results[role], registration, lock_commit, saved["run_utc"])
        checks = (("diagnostics.json", saved, data["diagnostic"]),
                  ("manifest.yaml", yaml.safe_load((folder / "manifest.yaml").read_text()), data["manifest"]),
                  ("evidence_packet.yaml", yaml.safe_load((folder / "evidence_packet.yaml").read_text()), data["packet"]),
                  ("chart_data.json", json.loads((folder / "chart_data.json").read_text()), data["chart"]))
        for label, actual, expected in checks:
            if actual != expected:
                raise AssertionError(f"{role} {label} differs from exact replay")
        if (folder / "result_card.md").read_text() != data["card"]:
            raise AssertionError(f"{role} result card differs from exact replay")
        if (folder / "replication.py").read_text() != data["wrapper"]:
            raise AssertionError(f"{role} replication wrapper differs from exact replay")
        if (folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_path(role)).read_bytes():
            raise AssertionError(f"{role} frozen spec copy differs")
        pd.testing.assert_frame_equal(pd.read_parquet(folder / "coefficients.parquet"),
                                      data["coefficients"], check_dtype=False,
                                      check_exact=False, rtol=1e-11, atol=1e-12)
    if (ROOT / SUMMARY).read_text() != summary(results, registration, lock_commit):
        raise AssertionError("family result summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for action in ("preflight", "lock", "run", "verify"):
        mode.add_argument(f"--{action}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    selected = source_metadata(source_root)
    roster, support, report = preflight(source_root)
    if args.preflight:
        print(json.dumps({"sources": selected, "key_preflight": report}, indent=2))
        return 0
    if args.lock:
        write_lock(source_root)
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    registration = registration_commit()
    lock_commit = committed_lock(registration, selected, report)
    # Nothing above this line reads WDI mortality values or their null masks.
    results = {}
    measured = mortality_values(source_root)
    for role in CASES:
        panel, gate = measured_panel(role, roster, support, measured)
        results[role] = estimate(role, panel, gate)
    if args.run:
        write_artifacts(results, registration, lock_commit)
    else:
        verify_artifacts(results, registration, lock_commit)
    for role, result in results.items():
        print(role, result["verdict"], result["gate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
