#!/usr/bin/env python3
"""Frozen three-test IMF inflation to later macro-outcome calibration family.

`--preflight` reads IMF inflation and WDI GDP-per-person control values, but only
(country, year, indicator) keys from the three selected outcome files. `--lock`
requires a committed first-addition registration. `--run` and `--verify` open
selected outcome measurements only after a separately committed narrow lock.
The default source root is this checkout; --source-root may point to an exact
ignored raw cache without recording that machine path in any artifact.
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
FAMILY = "imf_inflation_macro_responses_2026_10_10"
RUNNER = "scripts/run_imf_inflation_macro_responses_2026.py"
TEST = "tests/test_imf_inflation_macro_responses_2026.py"
PREREG = "engine/audits/imf_inflation_macro_responses_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/imf_inflation_macro_responses_2026_key_roster.csv"
ROSTER_SHA = "d09808f487e272d30ec847fca348bd9d0c1dc10b30f6a7fb71593363b311ca3d"
LOCK = "data/pinned_evidence/imf_inflation_macro_responses_2026.manifest.json"
SUMMARY = "engine/audits/imf_inflation_macro_responses_results_2026-10-10.md"
PRIOR_IMF_LOCK = "data/source_locks/cepal_imf_inflation_next_year_national_poverty_panel.yaml"
PRIOR_IMF_LOCK_SHA = "e93cb599cfc40c042a7b0cc7cac57642f0445318d97ef315bda9176d416fdc6e"
WDI_MANIFEST_A = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
WDI_MANIFEST_A_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
WDI_MANIFEST_B = "data/manifests/fetch_run_2026-05-05T203305Z.yaml"
WDI_MANIFEST_B_SHA = "53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0"
WDI_MANIFEST_C = "data/manifests/fetch_run_2026-05-05T200618Z.yaml"
WDI_MANIFEST_C_SHA = "6399c99e282dab5753bfa0e14f154429967f04a449d6762251067dce0fc84dba"
SOURCES = {
    "inflation": {"publisher": "imf_weo_sdmx", "series_id": "WEO__PCPIPCH",
        "path": "data/vintages/imf_weo_sdmx/WEO__PCPIPCH@2026-10-09T121600Z.parquet",
        "sha256": "89564e357988848ac8801d946f958c4dcef37881bf35ca77d4c03c225caa0568",
        "provenance": PRIOR_IMF_LOCK, "provenance_sha256": PRIOR_IMF_LOCK_SHA},
    "gdp_pc": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "provenance": WDI_MANIFEST_A, "provenance_sha256": WDI_MANIFEST_A_SHA},
    "consumption": {"publisher": "world_bank_wdi", "series_id": "NE.CON.PRVT.PC.KD",
        "path": "data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet",
        "sha256": "e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe",
        "provenance": WDI_MANIFEST_A, "provenance_sha256": WDI_MANIFEST_A_SHA},
    "investment": {"publisher": "world_bank_wdi", "series_id": "NE.GDI.FTOT.ZS",
        "path": "data/vintages/world_bank_wdi/NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet",
        "sha256": "fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21",
        "provenance": WDI_MANIFEST_B, "provenance_sha256": WDI_MANIFEST_B_SHA},
    "unemployment": {"publisher": "world_bank_wdi", "series_id": "SL.UEM.TOTL.ZS",
        "path": "data/vintages/world_bank_wdi/SL.UEM.TOTL.ZS@2026-05-05T200521Z.parquet",
        "sha256": "dfb2bae82f8ae7d95de21605e2d8c57f835cc7be4eeb53d58f8362da0b9e41c9",
        "provenance": WDI_MANIFEST_C, "provenance_sha256": WDI_MANIFEST_C_SHA},
}
CASES = {
    "consumption": {"id": "imf_inflation_real_consumption_pc_forward_2026", "topic": "growth",
        "label": "real household consumption per person", "direction": "-",
        "meaningful_beta": 0.015, "unit": "log points"},
    "investment": {"id": "imf_inflation_fixed_investment_share_forward_2026", "topic": "growth",
        "label": "gross fixed capital formation share", "direction": "-",
        "meaningful_beta": 0.75, "unit": "GDP percentage points"},
    "unemployment": {"id": "imf_inflation_unemployment_forward_2026", "topic": "labour",
        "label": "unemployment rate", "direction": "+",
        "meaningful_beta": 0.5, "unit": "percentage points"},
}
T_START, T_END, MIN_YEARS = 1995, 2016, 8
ROSTER_ROWS, ROSTER_COUNTRIES = 3919, 187
PREFLIGHT_ACCEL_ROWS, PREFLIGHT_ACCEL_COUNTRIES = 281, 121
PREFLIGHT_DECEL_ROWS, PREFLIGHT_DECEL_COUNTRIES = 547, 150
MATERIAL_X = 0.5
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_COMPLETE_ROWS, MIN_COMPLETE_COUNTRIES = 1200, 90
MIN_COMPLETE_YEARS = 15
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 75, 45
MAX_TOP_ONE_PERCENT_RESIDUAL_SHARE = 0.25
MAX_COUNTRY_RESIDUAL_SHARE = 0.15
MAX_YEAR_RESIDUAL_SHARE = 0.18
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 3, "family_alpha": FAMILY_ALPHA,
    "bonferroni_p_max": P_MAX, "school_score_eligible": False,
    "school_score_credit": 0, "policy_score_eligible": False,
    "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "IMF WEO annual average CPI inflation is an observed macro signal, not a monetary-policy treatment.",
    "The bounded tanh transformation avoids leverage from hyperinflation but compresses high-inflation differences.",
    "WDI private consumption, gross fixed capital formation, and ILO-modeled unemployment have different concepts and coverage; each outcome is tested separately.",
    "Country and calendar-year fixed effects, baseline outcome and income controls, and forward timing do not identify causal effects.",
    "The three-test Bonferroni correction does not correct selection across the wider IESET archive; these retrospective files are not a new-data holdout.",
    "All three outcomes receive zero school, policy, causal, and featured credit.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    history = git_bytes("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not history:
        raise RuntimeError(f"missing committed first addition: {relative}")
    return history[-1]


def unchanged_since(relative: str, commit: str) -> None:
    if (ROOT / relative).read_bytes() != git_bytes("show", f"{commit}:{relative}"):
        raise RuntimeError(f"frozen file changed after {commit}: {relative}")
    if git_bytes("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_path(case: dict[str, Any]) -> str:
    return f"hypotheses/{case['topic']}/{case['id']}.yaml"


def steelman_path(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_dir(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def load_roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("key-roster SHA-256 mismatch")
    raw = (ROOT / ROSTER).read_bytes()
    if not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("key-roster header mismatch")
    rows = [(r["country_iso3"], int(r["year"]))
            for r in csv.DictReader(io.StringIO(raw.decode()))]
    if (len(rows) != ROSTER_ROWS or len(set(rows)) != len(rows)
            or len({c for c, _ in rows}) != ROSTER_COUNTRIES
            or rows != sorted(rows, key=lambda item: (item[1], item[0]))
            or any(len(c) != 3 or not c.isupper() or not T_START <= y <= T_END for c, y in rows)):
        raise RuntimeError("key-roster shape, uniqueness, or order mismatch")
    return rows


def source_metadata(source_root: Path) -> dict[str, dict[str, Any]]:
    """Validate raw bytes and tracked provenance; do not project outcome columns."""
    narrow = {}
    for role, source in SOURCES.items():
        if sha256(source_root / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} raw byte hash mismatch")
        provenance = ROOT / source["provenance"]
        if sha256(provenance) != source["provenance_sha256"]:
            raise RuntimeError(f"{role} tracked provenance hash mismatch")
        doc = yaml.safe_load(provenance.read_text())
        if role == "inflation":
            matches = [doc["selected_source_entries"]["inflation"]]
        else:
            matches = [entry for entry in doc.get("entries", [])
                       if entry.get("publisher") == source["publisher"]
                       and entry.get("series_id") == source["series_id"]
                       and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} source-provenance entry mismatch")
        entry = matches[0]
        narrow[role] = {
            **source, "source_url": entry.get("source_url"),
            "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
            "rows": entry.get("rows"), "frequency": entry.get("frequency"),
            "units": entry.get("units"),
        }
    return narrow


def read_treatment_and_control(source_root: Path) -> dict[str, dict[tuple[str, int], float]]:
    inflation_source = SOURCES["inflation"]
    inflation = pd.read_parquet(source_root / inflation_source["path"],
                                columns=["country_iso3", "year", "value", "weo_flow"])
    if len(inflation) != 9874 or not inflation.weo_flow.eq("WEO").all():
        raise RuntimeError("IMF flow or physical row count changed")
    inflation = inflation.loc[inflation.country_iso3.str.len().eq(3)]
    if inflation.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate IMF country-year key")
    inflation_values = {}
    for c, y, v in inflation[["country_iso3", "year", "value"]].itertuples(index=False, name=None):
        try:
            numeric = float(v)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(numeric):
            inflation_values[(str(c), int(y))] = numeric
    gdp_source = SOURCES["gdp_pc"]
    gdp = pd.read_parquet(source_root / gdp_source["path"],
                          columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(gdp) != 17556 or not gdp.indicator_id.eq(gdp_source["series_id"]).all():
        raise RuntimeError("WDI GDP control indicator or physical row count changed")
    gdp = gdp.loc[gdp.country_iso3.str.len().eq(3)]
    if gdp.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate GDP control country-year key")
    gdp_values = {}
    for c, y, v, status in gdp[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None):
        try:
            numeric = float(v)
        except (TypeError, ValueError, OverflowError):
            continue
        if (math.isfinite(numeric) and numeric > 0
                and (pd.isna(status) or str(status).strip() == "")):
            gdp_values[(str(c), int(y))] = numeric
    return {"inflation": inflation_values, "gdp_pc": gdp_values}


def read_outcome_keys(source_root: Path, role: str) -> set[tuple[str, int]]:
    """Only permitted pre-lock projection of a selected WDI outcome file."""
    if role not in CASES:
        raise RuntimeError("not a selected outcome role")
    source = SOURCES[role]
    frame = pd.read_parquet(source_root / source["path"],
                            columns=["country_iso3", "indicator_id", "year"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} outcome indicator or physical row count changed")
    frame = frame.loc[frame.country_iso3.str.len().eq(3)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate {role} outcome country-year key")
    return {(str(c), int(y)) for c, y in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def exposure(pi_t: float, pi_prior: float) -> float:
    return 2.0 * (math.tanh(pi_t / 20.0) - math.tanh(pi_prior / 20.0))


def candidate_roster(values: dict[str, dict[tuple[str, int], float]],
                     keys: dict[str, set[tuple[str, int]]],
                     countries: set[str]) -> list[tuple[str, int]]:
    candidates = []
    inflation, gdp = values["inflation"], values["gdp_pc"]
    for c, t in sorted(inflation, key=lambda item: (item[1], item[0])):
        if c not in countries or not T_START <= t <= T_END:
            continue
        if (c, t - 3) not in inflation or (c, t - 3) not in gdp or (c, t) not in gdp:
            continue
        if any((c, y) not in key_set for key_set in keys.values() for y in (t - 3, t, t + 3)):
            continue
        candidates.append((c, t))
    counts = Counter(c for c, _ in candidates)
    return [(c, t) for c, t in candidates if counts[c] >= MIN_YEARS]


def source_preflight(source_root: Path) -> tuple[list[tuple[str, int]], dict[str, dict[tuple[str, int], float]], dict[str, Any]]:
    roster = load_roster()
    countries = {c for c, _ in roster}
    values = read_treatment_and_control(source_root)
    keys = {role: read_outcome_keys(source_root, role) for role in CASES}
    rebuilt = candidate_roster(values, keys, countries)
    if rebuilt != roster:
        raise RuntimeError("frozen blind candidate roster changed")
    shocks = [(c, exposure(values["inflation"][(c, t)], values["inflation"][(c, t - 3)]))
              for c, t in roster]
    accel = [(c, x) for c, x in shocks if x >= MATERIAL_X]
    decel = [(c, x) for c, x in shocks if x <= -MATERIAL_X]
    if (len(accel), len({c for c, _ in accel}), len(decel), len({c for c, _ in decel})) != (
        PREFLIGHT_ACCEL_ROWS, PREFLIGHT_ACCEL_COUNTRIES,
        PREFLIGHT_DECEL_ROWS, PREFLIGHT_DECEL_COUNTRIES,
    ):
        raise RuntimeError("frozen treatment-only shock counts changed")
    squares = sorted((x * x for _, x in shocks), reverse=True)
    top_count = max(1, math.ceil(len(squares) / 100))
    report = {
        "outcome_columns_read": ["country_iso3", "indicator_id", "year"],
        "outcome_values_read": False, "outcome_null_masks_read": False,
        "outcome_status_read": False, "treatment_and_control_values_read": True,
        "roster_sha256": ROSTER_SHA, "key_rows": len(roster),
        "key_economies": len(countries), "years": [T_START, T_END],
        "material_acceleration_rows": len(accel),
        "material_acceleration_economies": len({c for c, _ in accel}),
        "material_deceleration_rows": len(decel),
        "material_deceleration_economies": len({c for c, _ in decel}),
        "top_one_percent_raw_shock_squared_share": sum(squares[:top_count]) / sum(squares),
    }
    return roster, values, report


def registration_commit() -> str:
    frozen = [RUNNER, TEST, PREREG, ROSTER]
    for case in CASES.values():
        frozen += [spec_path(case), steelman_path(case)]
    commits = {first_addition(path) for path in frozen}
    if len(commits) != 1:
        raise RuntimeError("blind registration files lack one common first-addition commit")
    commit = commits.pop()
    for path in frozen:
        unchanged_since(path, commit)
    countries = sorted({c for c, _ in load_roster()})
    for case in CASES.values():
        spec = yaml.safe_load((ROOT / spec_path(case)).read_text())
        if (spec.get("hypothesis_id") != case["id"]
                or spec.get("status") != "pre_registered"
                or spec.get("sample", {}).get("countries") != countries
                or spec.get("covers_claims") != []
                or spec.get("falsification", {}).get("threshold", {}).get("roster_sha256") != ROSTER_SHA):
            raise RuntimeError(f"{case['id']} frozen spec fields disagree with runner")
        if git_bytes("ls-tree", "-r", "--name-only", commit, "--", run_dir(case)).strip():
            raise RuntimeError("registration commit already includes a measured run")
    if git_bytes("ls-tree", "-r", "--name-only", commit, "--", LOCK).strip():
        raise RuntimeError("narrow lock must be added later")
    return commit


def lock_payload(commit: str, sources: dict[str, dict[str, Any]],
                 report: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "preregistration_commit": commit,
        "selected_sources": sources, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
        "key_preflight": report, "outcome_values_opened_before_lock": False,
        "outcome_null_masks_opened_before_lock": False,
        "outcome_status_opened_before_lock": False,
        "whole_fetch_manifests_copied": False,
    }


def write_lock(source_root: Path) -> None:
    commit = registration_commit()
    if (ROOT / LOCK).exists() or (ROOT / SUMMARY).exists() or any((ROOT / run_dir(c)).exists() for c in CASES.values()):
        raise RuntimeError("lock or measured result already exists")
    sources = source_metadata(source_root)
    _, _, report = source_preflight(source_root)
    (ROOT / LOCK).write_text(json.dumps(lock_payload(commit, sources, report), indent=2, sort_keys=True) + "\n")
    print(f"wrote narrow {LOCK}; commit separately before selected outcome access")


def committed_lock(commit: str, sources: dict[str, dict[str, Any]], report: dict[str, Any]) -> str:
    target = ROOT / LOCK
    if json.loads(target.read_text()) != lock_payload(commit, sources, report):
        raise RuntimeError("narrow lock differs from frozen registration/preflight")
    lock_commit = first_addition(LOCK)
    if lock_commit == commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, lock_commit], cwd=ROOT).returncode:
        raise RuntimeError("lock must descend from registration in a separate commit")
    unchanged_since(LOCK, lock_commit)
    for case in CASES.values():
        if git_bytes("ls-tree", "-r", "--name-only", lock_commit, "--", run_dir(case)).strip():
            raise RuntimeError("source-lock commit already includes a measured run")
    return lock_commit


def authorized_measurement_context(source_root: Path):
    """All chronology and source checks finish before any selected value access."""
    commit = registration_commit()
    sources = source_metadata(source_root)
    roster, values, report = source_preflight(source_root)
    lock_commit = committed_lock(commit, sources, report)
    return commit, lock_commit, roster, values


def read_outcome_values(source_root: Path, role: str,
                        countries: set[str]) -> dict[tuple[str, int], tuple[float, str]]:
    """First selected measurement read. Caller must hold authorized context."""
    if role not in CASES:
        raise RuntimeError("not a selected outcome role")
    source = SOURCES[role]
    frame = pd.read_parquet(source_root / source["path"],
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} outcome indicator or physical row count changed")
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate {role} outcome country-year key")
    result = {}
    for c, y, v, status in frame[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None):
        try:
            numeric = float(v)
        except (TypeError, ValueError, OverflowError):
            numeric = math.nan
        result[(str(c), int(y))] = (numeric, "" if pd.isna(status) else str(status).strip())
    return result


def outcome_level(role: str, value: float) -> float | None:
    if not math.isfinite(value):
        return None
    if role == "consumption":
        return math.log(value) if value > 0 else None
    if role == "investment":
        return value if value >= 0 else None
    if role == "unemployment":
        return value if 0 <= value <= 100 else None
    raise RuntimeError("unknown selected outcome")


def build_panel(roster: list[tuple[str, int]], values: dict[str, dict[tuple[str, int], float]],
                outcome: dict[tuple[str, int], tuple[float, str]], role: str):
    rows = []
    dropped_invalid = dropped_status = 0
    inflation, gdp = values["inflation"], values["gdp_pc"]
    for c, t in roster:
        triple = [outcome.get((c, y), (math.nan, "")) for y in (t - 3, t, t + 3)]
        levels = [outcome_level(role, x[0]) for x in triple]
        if any(level is None for level in levels):
            dropped_invalid += 1
            continue
        if any(status for _, status in triple):
            dropped_status += 1
            continue
        x = exposure(inflation[(c, t)], inflation[(c, t - 3)])
        rows.append({
            "country_iso3": c, "year": t, "exposure": x,
            "prior_inflation": 2.0 * math.tanh(inflation[(c, t - 3)] / 20.0),
            "baseline_outcome": levels[1],
            "prior_outcome_change": levels[1] - levels[0],
            "log_gdp_pc": math.log(gdp[(c, t)]),
            "prior_log_gdp_pc_change": math.log(gdp[(c, t)]) - math.log(gdp[(c, t - 3)]),
            "outcome_change": levels[2] - levels[1],
        })
    columns = ["country_iso3", "year", "exposure", "prior_inflation",
               "baseline_outcome", "prior_outcome_change", "log_gdp_pc",
               "prior_log_gdp_pc_change", "outcome_change"]
    panel = pd.DataFrame(rows, columns=columns)
    before_min_years = len(panel)
    if len(panel):
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    up = panel.loc[panel.exposure.ge(MATERIAL_X), "country_iso3"]
    down = panel.loc[panel.exposure.le(-MATERIAL_X), "country_iso3"]
    gate = {
        "roster_rows": len(roster), "dropped_invalid_selected_triples": dropped_invalid,
        "dropped_nonblank_selected_status_triples": dropped_status,
        "complete_triples_before_eight_year_floor": before_min_years,
        "valid_rows": len(panel), "valid_economies": int(panel.country_iso3.nunique()),
        "valid_treatment_years": int(panel.year.nunique()),
        "material_acceleration_rows": len(up), "material_acceleration_economies": int(up.nunique()),
        "material_deceleration_rows": len(down), "material_deceleration_economies": int(down.nunique()),
        "selected_outcome_values_read_after_committed_lock": True,
    }
    return panel.sort_values(["year", "country_iso3"]).reset_index(drop=True), gate


def residual_concentration(design: np.ndarray, treatment_index: int,
                           panel: pd.DataFrame) -> dict[str, float] | None:
    other = np.delete(design, treatment_index, axis=1)
    x = design[:, treatment_index]
    residual = x - other @ np.linalg.lstsq(other, x, rcond=None)[0]
    weights = np.square(residual)
    total = float(weights.sum())
    if not math.isfinite(total) or total <= 1e-12:
        return None
    top = max(1, math.ceil(len(weights) / 100))
    frame = pd.DataFrame({"country": panel.country_iso3.to_numpy(),
                          "year": panel.year.to_numpy(), "weight": weights})
    return {
        "top_one_percent_rows": float(np.sort(weights)[-top:].sum() / total),
        "top_economy": float(frame.groupby("country").weight.sum().max() / total),
        "top_year": float(frame.groupby("year").weight.sum().max() / total),
    }


def estimate(panel: pd.DataFrame, gate: dict[str, Any], role: str) -> dict[str, Any]:
    gate = dict(gate)
    if (gate["valid_rows"] < MIN_COMPLETE_ROWS
            or gate["valid_economies"] < MIN_COMPLETE_COUNTRIES
            or gate["valid_treatment_years"] < MIN_COMPLETE_YEARS
            or gate["material_acceleration_rows"] < MIN_MATERIAL_ROWS
            or gate["material_acceleration_economies"] < MIN_MATERIAL_COUNTRIES
            or gate["material_deceleration_rows"] < MIN_MATERIAL_ROWS
            or gate["material_deceleration_economies"] < MIN_MATERIAL_COUNTRIES):
        return {"gate": gate, "primary": None, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case, time, or material-exposure floor failed"}
    formula = (
        "outcome_change ~ exposure + prior_inflation + baseline_outcome + "
        "prior_outcome_change + log_gdp_pc + prior_log_gdp_pc_change + "
        "C(country_iso3) + C(year)"
    )
    model = smf.ols(formula, data=panel)
    design = model.exog
    if design.shape[0] != len(panel) or np.linalg.matrix_rank(design) != design.shape[1]:
        return {"gate": gate, "primary": None, "verdict": "INCONCLUSIVE",
                "reason": "frozen fixed-effects design lacks full rank"}
    concentration = residual_concentration(design, model.exog_names.index("exposure"), panel)
    gate["residual_exposure_concentration"] = concentration
    if (concentration is None or concentration["top_one_percent_rows"] > MAX_TOP_ONE_PERCENT_RESIDUAL_SHARE
            or concentration["top_economy"] > MAX_COUNTRY_RESIDUAL_SHARE
            or concentration["top_year"] > MAX_YEAR_RESIDUAL_SHARE):
        return {"gate": gate, "primary": None, "verdict": "INCONCLUSIVE",
                "reason": "frozen residualized-exposure concentration gate failed"}
    fit = model.fit(cov_type="cluster",
                    cov_kwds={"groups": panel.country_iso3,
                              "use_correction": True, "df_correction": True}, use_t=True)
    beta = float(fit.params["exposure"])
    se = float(fit.bse["exposure"])
    groups = gate["valid_economies"]
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return {"gate": gate, "primary": None, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive country-cluster uncertainty"}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, groups - 1))
    if not (math.isfinite(p) and math.isfinite(critical)):
        return {"gate": gate, "primary": None, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite country-cluster inference"}
    primary = {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 1 - P_MAX,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_economies": groups, "df_inference": groups - 1,
        "design_rank": int(fit.model.rank),
        "residual_exposure_concentration": concentration,
        "method": "country/treatment-year FE OLS; baseline and pretrend controls; country-cluster CR1; Student t(G-1)",
    }
    case = CASES[role]
    meaningful = case["meaningful_beta"]
    sign = 1 if case["direction"] == "+" else -1
    aligned = sign * beta
    if aligned >= meaningful and p <= P_MAX:
        verdict, reason = "SUPPORTED", "registered direction clears family significance and practical-magnitude gates"
    elif aligned <= -meaningful and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite direction clears family significance and practical-magnitude gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "primary": primary, "verdict": verdict, "reason": reason}


def result_card(role: str, result: dict[str, Any], registration: str, lock_commit: str) -> str:
    case, gate, primary = CASES[role], result["gate"], result["primary"]
    lines = [f"# Result card: {case['id']}", "",
             f"Verdict: **{result['verdict']}**. {result['reason']}.", "",
             f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.", "",
             f"Measured triples: {gate['valid_rows']} across {gate['valid_economies']} economies; "
             f"accelerations {gate['material_acceleration_rows']}, decelerations {gate['material_deceleration_rows']}.", ""]
    if primary:
        lines += [f"Beta per one bounded-inflation-change unit: {primary['coefficient']:+.6g} {case['unit']}; "
                  f"SE={primary['std_error']:.6g}; two-sided p={primary['p_value_two_sided']:.6g}; "
                  f"family-adjusted CI={primary['confidence_interval']}.", ""]
    lines += ["Three Bonferroni tests (family alpha .01, each p<=.003333...).",
              "Retrospective descriptive calibration; zero causal, policy, school, or featured credit.", ""]
    return "\n".join(lines)


def artifact_payload(role: str, result: dict[str, Any], registration: str,
                     lock_commit: str, stamp: str) -> dict[str, Any]:
    case, gate, primary = CASES[role], result["gate"], result["primary"]
    inputs = {r: SOURCES[r] for r in ("inflation", "gdp_pc", role)}
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": case["id"], "path": spec_path(case), "topic": case["topic"]},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                            "family_id": FAMILY, "family_size": 3,
                            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                            "steelman": steelman_path(case)},
        "reproduction": {"runner": RUNNER, "run_dir": run_dir(case),
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                    "reason": result["reason"]},
        "data": {"inputs": inputs, "sample": gate},
        "results": {"primary": primary},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": case["id"], "family_id": FAMILY,
        "verdict": result["verdict"], "verdict_label": result["verdict"],
        "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "primary": primary,
        "analysis_scope": "descriptive_only", "data_status": {"variables_missing": [],
            "input_vintages": list(inputs.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {"hypothesis_id": case["id"], "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": result["verdict"],
                "vintages": list(inputs.values()), "derived_panel": gate,
                "correction": CORRECTION}
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    coeff_cols = ["term", "coefficient", "std_error", "p_value_two_sided", "ci_low", "ci_high",
                  "n_rows", "n_economies", "df_inference", "design_rank", "method"]
    coeff = ([] if primary is None else [{
        "term": "exposure", "coefficient": primary["coefficient"],
        "std_error": primary["std_error"], "p_value_two_sided": primary["p_value_two_sided"],
        "ci_low": primary["confidence_interval"][0], "ci_high": primary["confidence_interval"][1],
        "n_rows": primary["n_rows"], "n_economies": primary["n_economies"],
        "df_inference": primary["df_inference"], "design_rank": primary["design_rank"],
        "method": primary["method"],
    }])
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": result_card(role, result, registration, lock_commit),
            "wrapper": wrapper,
            "chart": {"hypothesis_id": case["id"], "family_id": FAMILY,
                      "verdict": result["verdict"], "primary": primary},
            "coefficients": pd.DataFrame(coeff, columns=coeff_cols)}


def summary_text(results: dict[str, dict[str, Any]], registration: str,
                 lock_commit: str) -> str:
    lines = ["# Bounded inflation changes and three later macro outcomes", "",
             f"Preregistration `{registration}`; narrow lock `{lock_commit}`.",
             "Three-test Bonferroni alpha .01, each two-sided p<=.003333...; descriptive only.", "",
             "| Outcome | Verdict | Complete triples / economies | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: |"]
    for role, case in CASES.items():
        result, gate = results[role], results[role]["gate"]
        primary = result["primary"]
        beta = "not estimated" if primary is None else f"{primary['coefficient']:+.6g}"
        p = "not estimated" if primary is None else f"{primary['p_value_two_sided']:.6g}"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / "
                     f"{gate['valid_economies']} | {beta} | {p} |")
    lines += ["", "The exposure is the t-3 to t change in twice the hyperbolic tangent of annual IMF CPI inflation divided by 20. "
              "Outcomes change from t to t+3. The frozen model includes baseline outcome, prior outcome change, "
              "prior inflation level, baseline real GDP per person, prior GDP-per-person change, and country and "
              "treatment-year fixed effects.", "", "No causal, policy, school, or featured credit; the family correction "
              "does not adjust for wider archive selection.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str,
                    lock_commit: str) -> None:
    if (ROOT / SUMMARY).exists() or any((ROOT / run_dir(c)).exists() for c in CASES.values()):
        raise FileExistsError("one or more measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for role, case in CASES.items():
        payload = artifact_payload(role, results[role], registration, lock_commit, stamp)
        folder = ROOT / run_dir(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_path(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
        payload["coefficients"].to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str,
                     lock_commit: str) -> None:
    for role, case in CASES.items():
        folder = ROOT / run_dir(case)
        diagnostics = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(role, results[role], registration, lock_commit, diagnostics["run_utc"])
        checks = (("diagnostics.json", diagnostics, payload["diagnostics"]),
                  ("evidence_packet.yaml", yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"]),
                  ("manifest.yaml", yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"]),
                  ("chart_data.json", json.loads((folder / "chart_data.json").read_text()), payload["chart"]))
        for label, actual, wanted in checks:
            if actual != wanted:
                raise AssertionError(f"{case['id']} {label} differs from exact replay")
        if (folder / "result_card.md").read_text() != payload["card"]:
            raise AssertionError(f"{case['id']} result card differs")
        if (folder / "replication.py").read_text() != payload["wrapper"]:
            raise AssertionError(f"{case['id']} wrapper differs")
        if (folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_path(case)).read_bytes():
            raise AssertionError(f"{case['id']} spec copy differs")
        pd.testing.assert_frame_equal(pd.read_parquet(folder / "coefficients.parquet"),
                                      payload["coefficients"], check_dtype=False,
                                      check_exact=False, rtol=1e-11, atol=1e-12)
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")
    print("verified three exact bounded-inflation forward calibrations")


def execute_measured(mode: str, source_root: Path):
    registration, lock_commit, roster, values = authorized_measurement_context(source_root)
    countries = {c for c, _ in roster}
    outcomes = {role: read_outcome_values(source_root, role, countries) for role in CASES}
    results = {}
    for role in CASES:
        panel, gate = build_panel(roster, values, outcomes[role], role)
        results[role] = estimate(panel, gate, role)
    if mode == "run":
        write_artifacts(results, registration, lock_commit)
    elif mode == "verify":
        verify_artifacts(results, registration, lock_commit)
    else:
        raise RuntimeError("unknown measured mode")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--lock", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.preflight:
        print(json.dumps({"sources": source_metadata(source_root),
                          "key_preflight": source_preflight(source_root)[2]}, indent=2))
        return 0
    if args.lock:
        write_lock(source_root)
        return 0
    results = execute_measured("run" if args.run else "verify", source_root)
    for role, result in results.items():
        print(role, result["verdict"], result["gate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
