#!/usr/bin/env python3
"""Frozen three-test WDI internet diffusion and later economic composition family.

--preflight reads only internet, GDP-per-person, and population values, plus
(country, indicator, year) keys from the three selected outcome files. --lock
requires a committed first-addition registration. --run and --verify open
selected outcome measurements only after a separately committed source lock.
--source-root can point at an exact ignored raw cache without recording that
machine path in any artifact.
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
FAMILY = "wdi_digital_diffusion_structure_2026_10_10"
RUNNER = "scripts/run_wdi_digital_diffusion_structure_2026.py"
TEST = "tests/test_wdi_digital_diffusion_structure_2026.py"
PREREG = "engine/audits/wdi_digital_diffusion_structure_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_digital_diffusion_family_2026_key_roster.csv"
ROSTER_SHA = "6fb22b7e83afe60d5cf03f43620968bfef7d75303d07bcd9a419f4d5b10ea356"
LOCK = "data/pinned_evidence/wdi_digital_diffusion_structure_2026.manifest.json"
SUMMARY = "engine/audits/wdi_digital_diffusion_structure_results_2026-10-10.md"
WDI_MANIFEST_A = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
WDI_MANIFEST_A_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
WDI_MANIFEST_B = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
WDI_MANIFEST_B_SHA = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"
SOURCES = {
    "internet": {"publisher": "world_bank_wdi", "series_id": "IT.NET.USER.ZS",
        "path": "data/vintages/world_bank_wdi/IT.NET.USER.ZS@2026-05-05T203400Z.parquet",
        "sha256": "c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8",
        "provenance": WDI_MANIFEST_B, "provenance_sha256": WDI_MANIFEST_B_SHA},
    "gdp_pc": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "provenance": WDI_MANIFEST_A, "provenance_sha256": WDI_MANIFEST_A_SHA},
    "population": {"publisher": "world_bank_wdi", "series_id": "SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "provenance": WDI_MANIFEST_A, "provenance_sha256": WDI_MANIFEST_A_SHA},
    "entry": {"publisher": "world_bank_wdi", "series_id": "IC.BUS.NREG",
        "path": "data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet",
        "sha256": "213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae",
        "provenance": WDI_MANIFEST_B, "provenance_sha256": WDI_MANIFEST_B_SHA},
    "services": {"publisher": "world_bank_wdi", "series_id": "SL.SRV.EMPL.ZS",
        "path": "data/vintages/world_bank_wdi/SL.SRV.EMPL.ZS@2026-05-05T203741Z.parquet",
        "sha256": "5cc0fcababebe90b69eae253466a6a81beaf0f52f9c0ef5d59b8a2fa34f400c6",
        "provenance": WDI_MANIFEST_B, "provenance_sha256": WDI_MANIFEST_B_SHA},
    "hightech": {"publisher": "world_bank_wdi", "series_id": "TX.VAL.TECH.MF.ZS",
        "path": "data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet",
        "sha256": "b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994",
        "provenance": WDI_MANIFEST_A, "provenance_sha256": WDI_MANIFEST_A_SHA},
}
CASES = {
    "entry": {"id": "wdi_internet_uptake_business_registrations_forward_2026", "topic": "regulatory",
        "label": "new limited-liability registrations per million residents", "direction": "+",
        "meaningful_beta": 0.05, "unit": "log1p registration-intensity points"},
    "services": {"id": "wdi_internet_uptake_services_employment_forward_2026", "topic": "labour",
        "label": "services employment share", "direction": "+",
        "meaningful_beta": 0.5, "unit": "percentage points"},
    "hightech": {"id": "wdi_internet_uptake_hightech_export_share_forward_2026", "topic": "trade",
        "label": "high-tech share of manufactured exports", "direction": "+",
        "meaningful_beta": 1.0, "unit": "percentage points"},
}
T_START, T_END, MIN_YEARS = 2009, 2016, 5
ROSTER_ROWS, ROSTER_COUNTRIES = 1558, 196
PREFLIGHT_RISE_ROWS, PREFLIGHT_RISE_COUNTRIES = 528, 141
PREFLIGHT_LOW_ROWS, PREFLIGHT_LOW_COUNTRIES = 232, 77
MATERIAL_UP, MATERIAL_LOW = 10.0, 2.0  # raw internet percentage points over three years
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_COMPLETE_ROWS, MIN_COMPLETE_COUNTRIES = 400, 50
MIN_COMPLETE_YEARS = 7
MIN_RISE_ROWS, MIN_RISE_COUNTRIES = 60, 25
MIN_LOW_ROWS, MIN_LOW_COUNTRIES = 20, 10
MAX_TOP_ONE_PERCENT_RESIDUAL_SHARE = 0.25
MAX_COUNTRY_RESIDUAL_SHARE = 0.15
MAX_YEAR_RESIDUAL_SHARE = 0.20
CORRECTION = {
    "family_scope": "retrospective_descriptive_calibration", "family_id": FAMILY,
    "family_size": 3, "family_alpha": FAMILY_ALPHA,
    "bonferroni_p_max": P_MAX, "school_score_eligible": False,
    "school_score_credit": 0, "policy_score_eligible": False,
    "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "Internet use is observed adoption, not randomized access or digital policy exposure.",
    "New registrations cover limited-liability entities, not all startups, jobs, or innovation; population is a de facto resident denominator.",
    "Services employment is a modeled sectoral share; high-tech exports reflect classification, re-exports, and global value chains.",
    "Three-year windows overlap and common development shocks can confound all outcomes despite fixed effects and controls.",
    "Retrospective pinned files are not an independent future-data holdout; local Bonferroni correction does not adjust archive-wide selection.",
    "Zero causal, policy, school, position, and featured credit for every endpoint.",
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
    """Read only the registered exposure and supporting GDP/population values."""
    values = {}
    for role in ("internet", "gdp_pc", "population"):
        source = SOURCES[role]
        frame = pd.read_parquet(source_root / source["path"],
                                columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
        if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
            raise RuntimeError(f"{role} WDI indicator or physical row count changed")
        frame = frame.loc[frame.country_iso3.str.len().eq(3)]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate {role} country-year key")
        clean = {}
        for c, y, raw, status in frame[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None):
            try:
                value = float(raw)
            except (TypeError, ValueError, OverflowError):
                continue
            if not math.isfinite(value) or not (pd.isna(status) or str(status).strip() == ""):
                continue
            if role == "internet" and not 0 <= value <= 100:
                continue
            if role != "internet" and value <= 0:
                continue
            clean[(str(c), int(y))] = value
        values[role] = clean
    return values

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


def exposure(internet_t: float, internet_prior: float) -> float:
    """One exposure unit is a ten-percentage-point three-year uptake."""
    return (internet_t - internet_prior) / 10.0


def candidate_roster(values: dict[str, dict[tuple[str, int], float]],
                     keys: dict[str, set[tuple[str, int]]],
                     countries: set[str]) -> list[tuple[str, int]]:
    candidates = []
    internet, gdp, population = values["internet"], values["gdp_pc"], values["population"]
    for c in sorted(countries):
        for t in range(T_START, T_END + 1):
            if any((c, y) not in internet for y in (t - 3, t)):
                continue
            if any((c, y) not in gdp for y in (t - 3, t)):
                continue
            if any((c, y) not in population for y in (t - 3, t, t + 3)):
                continue
            if any((c, y) not in key_set for key_set in keys.values() for y in (t - 3, t, t + 3)):
                continue
            candidates.append((c, t))
    counts = Counter(c for c, _ in candidates)
    return sorted([(c, t) for c, t in candidates if counts[c] >= MIN_YEARS],
                  key=lambda item: (item[1], item[0]))


def source_preflight(source_root: Path) -> tuple[list[tuple[str, int]], dict[str, dict[tuple[str, int], float]], dict[str, Any]]:
    roster = load_roster()
    countries = {c for c, _ in roster}
    values = read_treatment_and_control(source_root)
    keys = {role: read_outcome_keys(source_root, role) for role in CASES}
    if candidate_roster(values, keys, countries) != roster:
        raise RuntimeError("frozen blind candidate roster changed")
    raw_changes = [(c, values["internet"][(c, t)] - values["internet"][(c, t - 3)])
                   for c, t in roster]
    rises = [(c, x) for c, x in raw_changes if x >= MATERIAL_UP]
    low = [(c, x) for c, x in raw_changes if x <= MATERIAL_LOW]
    if (len(rises), len({c for c, _ in rises}), len(low), len({c for c, _ in low})) != (
        PREFLIGHT_RISE_ROWS, PREFLIGHT_RISE_COUNTRIES,
        PREFLIGHT_LOW_ROWS, PREFLIGHT_LOW_COUNTRIES,
    ):
        raise RuntimeError("frozen treatment-only exposure counts changed")
    squares = sorted((x * x for _, x in raw_changes), reverse=True)
    top_count = max(1, math.ceil(len(squares) / 100))
    report = {
        "outcome_columns_read": ["country_iso3", "indicator_id", "year"],
        "outcome_values_read": False, "outcome_null_masks_read": False,
        "outcome_status_read": False, "treatment_and_supporting_values_read": True,
        "roster_sha256": ROSTER_SHA, "key_rows": len(roster),
        "key_economies": len(countries), "years": [T_START, T_END],
        "material_rise_rows": len(rises),
        "material_rise_economies": len({c for c, _ in rises}),
        "low_change_rows": len(low),
        "low_change_economies": len({c for c, _ in low}),
        "top_one_percent_raw_change_squared_share": sum(squares[:top_count]) / sum(squares),
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


def outcome_level(role: str, value: float, population: float) -> float | None:
    if not math.isfinite(value):
        return None
    if role == "entry":
        return math.log1p(1_000_000.0 * value / population) if value >= 0 and population > 0 else None
    if role in ("services", "hightech"):
        return value if 0 <= value <= 100 else None
    raise RuntimeError("unknown selected outcome")


def build_panel(roster: list[tuple[str, int]], values: dict[str, dict[tuple[str, int], float]],
                outcome: dict[tuple[str, int], tuple[float, str]], role: str):
    rows = []
    dropped_invalid = dropped_status = 0
    internet, gdp, population = values["internet"], values["gdp_pc"], values["population"]
    for c, t in roster:
        triple = [outcome.get((c, y), (math.nan, "")) for y in (t - 3, t, t + 3)]
        levels = [outcome_level(role, item[0], population[(c, y)])
                  for item, y in zip(triple, (t - 3, t, t + 3))]
        if any(level is None for level in levels):
            dropped_invalid += 1
            continue
        if any(status for _, status in triple):
            dropped_status += 1
            continue
        x = exposure(internet[(c, t)], internet[(c, t - 3)])
        rows.append({
            "country_iso3": c, "year": t, "exposure": x,
            "prior_internet": internet[(c, t - 3)] / 10.0,
            "baseline_outcome": levels[1],
            "prior_outcome_change": levels[1] - levels[0],
            "log_gdp_pc": math.log(gdp[(c, t)]),
            "prior_log_gdp_pc_change": math.log(gdp[(c, t)]) - math.log(gdp[(c, t - 3)]),
            "outcome_change": levels[2] - levels[1],
        })
    columns = ["country_iso3", "year", "exposure", "prior_internet",
               "baseline_outcome", "prior_outcome_change", "log_gdp_pc",
               "prior_log_gdp_pc_change", "outcome_change"]
    panel = pd.DataFrame(rows, columns=columns)
    before_min_years = len(panel)
    if len(panel):
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    rise = panel.loc[panel.exposure.ge(MATERIAL_UP / 10), "country_iso3"]
    low = panel.loc[panel.exposure.le(MATERIAL_LOW / 10), "country_iso3"]
    gate = {
        "roster_rows": len(roster), "dropped_invalid_selected_triples": dropped_invalid,
        "dropped_nonblank_selected_status_triples": dropped_status,
        "complete_triples_before_five_year_floor": before_min_years,
        "valid_rows": len(panel), "valid_economies": int(panel.country_iso3.nunique()),
        "valid_treatment_years": int(panel.year.nunique()),
        "material_rise_rows": len(rise), "material_rise_economies": int(rise.nunique()),
        "low_change_rows": len(low), "low_change_economies": int(low.nunique()),
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
            or gate["material_rise_rows"] < MIN_RISE_ROWS
            or gate["material_rise_economies"] < MIN_RISE_COUNTRIES
            or gate["low_change_rows"] < MIN_LOW_ROWS
            or gate["low_change_economies"] < MIN_LOW_COUNTRIES):
        return {"gate": gate, "primary": None, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case, time, or exposure-support floor failed"}
    formula = (
        "outcome_change ~ exposure + prior_internet + baseline_outcome + "
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


def publication_tier(verdict: str) -> str:
    if verdict in ("SUPPORTED", "REFUTED", "PARTIAL"):
        return "public_descriptive_calibration"
    if verdict == "INCONCLUSIVE":
        return "inconclusive_archive"
    raise RuntimeError(f"unknown verdict for publication tier: {verdict}")


def result_card(role: str, result: dict[str, Any], registration: str, lock_commit: str) -> str:
    case, gate, primary = CASES[role], result["gate"], result["primary"]
    lines = [f"# Result card: {case['id']}", "",
             f"Verdict: **{result['verdict']}**. {result['reason']}.", "",
             f"Disposition: **{publication_tier(result['verdict'])}**.", "",
             f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.", "",
             f"Measured triples: {gate['valid_rows']} across {gate['valid_economies']} economies; "
             f"material rises {gate['material_rise_rows']}, low changes {gate['low_change_rows']}.", ""]
    if primary:
        lines += [f"Beta per 10-point internet uptake: {primary['coefficient']:+.6g} {case['unit']}; "
                  f"SE={primary['std_error']:.6g}; two-sided p={primary['p_value_two_sided']:.6g}; "
                  f"family-adjusted CI={primary['confidence_interval']}.", ""]
    lines += ["Three Bonferroni tests (family alpha .01, each p<=.003333...).",
              "Zero causal, policy, school, position, or featured credit regardless of disposition.", ""]
    return "\n".join(lines)

def artifact_payload(role: str, result: dict[str, Any], registration: str,
                     lock_commit: str, stamp: str) -> dict[str, Any]:
    case, gate, primary = CASES[role], result["gate"], result["primary"]
    inputs = {r: SOURCES[r] for r in ("internet", "gdp_pc", "population", role)}
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": case["id"], "path": spec_path(case), "topic": case["topic"]},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                            "family_id": FAMILY, "family_size": len(CASES),
                            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                            "steelman": steelman_path(case)},
        "reproduction": {"runner": RUNNER, "run_dir": run_dir(case),
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                    "reason": result["reason"], "publication_tier": publication_tier(result["verdict"])},
        "data": {"inputs": inputs, "sample": gate},
        "results": {"primary": primary},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": case["id"], "family_id": FAMILY,
        "verdict": result["verdict"], "verdict_label": result["verdict"],
        "verdict_reason": result["reason"],
        "publication_tier": publication_tier(result["verdict"]), "run_utc": stamp,
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
                "publication_tier": publication_tier(result["verdict"]),
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
                      "verdict": result["verdict"],
                      "publication_tier": publication_tier(result["verdict"]),
                      "primary": primary},
            "coefficients": pd.DataFrame(coeff, columns=coeff_cols)}


def summary_text(results: dict[str, dict[str, Any]], registration: str,
                 lock_commit: str) -> str:
    lines = ["# Internet uptake and later economic composition", "",
             f"Preregistration `{registration}`; narrow lock `{lock_commit}`.",
             "Three-test Bonferroni alpha .01, each two-sided p<=.003333...; descriptive only.", "",
             "| Outcome | Verdict | Disposition | Complete triples / economies | Beta | Two-sided p |",
             "| --- | --- | --- | ---: | ---: | ---: |"]
    for role, case in CASES.items():
        result, gate = results[role], results[role]["gate"]
        primary = result["primary"]
        beta = "not estimated" if primary is None else f"{primary['coefficient']:+.6g}"
        p = "not estimated" if primary is None else f"{primary['p_value_two_sided']:.6g}"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {publication_tier(result['verdict'])} | {gate['valid_rows']} / "
                     f"{gate['valid_economies']} | {beta} | {p} |")
    lines += ["", "The exposure is the WDI internet-user share change from t-3 to t per ten percentage points. "
              "Outcomes change from t to t+3. The frozen model includes baseline outcome, prior outcome change, "
              "prior internet level, baseline real GDP per person, prior GDP-per-person change, and country and "
              "treatment-year fixed effects.", "", "SUPPORTED, REFUTED, and gate-cleared PARTIAL are public descriptive calibrations; INCONCLUSIVE is archived. "
              "No causal, policy, school, position, or featured credit; "
              "the family correction does not adjust for wider archive selection.", ""]
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
    print("verified three exact internet-uptake forward calibrations")


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
