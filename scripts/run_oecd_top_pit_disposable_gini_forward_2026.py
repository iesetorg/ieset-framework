#!/usr/bin/env python3
"""Frozen OECD top-PIT hike to next-year disposable-income Gini study.

--preflight opens tax values and Gini selector/geo/year keys only.
--lock requires the committed registration and writes a narrow source lock.
--run and --verify open Gini values/status only after that lock is committed.
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
import pyarrow.compute as pc
import pyarrow.dataset as ds
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_top_pit_disposable_gini_forward_2026"
FAMILY = ID + "_10_10"
RUNNER = "scripts/run_oecd_top_pit_disposable_gini_forward_2026.py"
SPEC = f"hypotheses/distribution/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PREREG = "engine/audits/oecd_top_pit_disposable_gini_prereg_2026-10-10.md"
TESTS = "tests/test_oecd_top_pit_disposable_gini_forward_2026.py"
ROSTER = "data/pinned_evidence/oecd_top_pit_disposable_gini_forward_2026_key_roster.csv"
ROSTER_SHA = "169effde75deb7226ff45b4d00d0e438a2b39b9d4bd79a38814be35438983caf"
LOCK = "data/pinned_evidence/oecd_top_pit_disposable_gini_forward_2026.manifest.json"
RUN_DIR = f"engine/runs/{ID}"
SUMMARY = "engine/audits/oecd_top_pit_disposable_gini_results_2026-10-10.md"
SOURCES = {
    "treatment": {
        "publisher": "oecd", "series_id": "oecd_top_statutory_pit_rate",
        "path": "data/vintages/oecd/oecd_top_statutory_pit_rate@2026-07-23T153857Z.parquet",
        "sha256": "b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151",
        "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
        "manifest_sha256": "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18",
    },
    "outcome": {
        "publisher": "oecd", "series_id": "DSD_IDD",
        "path": "data/vintages/oecd/DSD_IDD@2026-05-05T200556Z.parquet",
        "sha256": "869fa437691bda1a322f7b5463944ebbbb9066d689d5b76ed3d1a32620beb60e",
        "manifest": "data/manifests/fetch_run_2026-05-05T200618Z.yaml",
        "manifest_sha256": "6399c99e282dab5753bfa0e14f154429967f04a449d6762251067dce0fc84dba",
    },
}
SELECTOR = {
    "FREQ": "A", "MEASURE": "INC_DISP_GINI",
    "STATISTICAL_OPERATION": "_Z", "UNIT_MEASURE": "0_TO_1",
    "AGE": "_T", "METHODOLOGY": "METH2012",
    "DEFINITION": "D_CUR", "POVERTY_LINE": "_Z",
}
T_START, T_END, MIN_YEARS = 2007, 2018, 5
EVENT_PP = 1.0
P_MAX, MEANINGFUL_BETA = 0.005, 0.005
MIN_ROWS, MIN_COUNTRIES = 220, 25
MIN_HIKE_ROWS, MIN_HIKE_COUNTRIES = 20, 12
MIN_CUT_ROWS, MIN_CUT_COUNTRIES = 15, 10
MAX_TOP_1PCT, MAX_COUNTRY, MAX_YEAR = 0.20, 0.20, 0.30
KEY_COUNTRIES = [
    "AUT", "CAN", "CHE", "CRI", "CZE", "DEU", "DNK", "ESP", "EST", "FIN",
    "GBR", "GRC", "HUN", "IRL", "ISL", "ISR", "ITA", "KOR", "LTU", "LVA",
    "NLD", "NOR", "NZL", "POL", "PRT", "SVK", "SVN", "SWE", "TUR", "USA",
]
EXPECTED = {
    "key_rows": 312, "key_countries": 30,
    "hike_rows": 31, "hike_countries": 16,
    "cut_rows": 29, "cut_countries": 17,
    "top_one_percent_share": 0.13022238503529174,
    "top_country_share": 0.10882977500372716,
    "top_year_share": 0.23131540247960386,
}
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": P_MAX,
    "p_max_two_sided": P_MAX,
    "archive_wide_multiplicity_control": False,
    "school_score_eligible": False, "school_score_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "The statutory top personal income-tax rate measures a high wage bracket, not the effective rate paid by high-income households.",
    "Bracket thresholds, deductions, capital-income rules, other taxes and transfers, income shifting, and tax anticipation may move independently of the headline rate.",
    "The all-age disposable-income Gini is a broad survey-based distribution measure, not a WID pretax top-share or an absolute-poverty rate.",
    "Macroeconomic shocks, contemporaneous reforms, and survey/methodology changes can confound this forward association.",
    "Related earlier top-PIT and OECD IDD Gini cases are visible; the 0.005 cutoff does not correct archive-wide selection.",
    "No causal, policy, school, position, or featured credit.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}: {commits}")
    return commits[0]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from its first commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def threshold() -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 1, "family_alpha": P_MAX,
        "p_max_two_sided": P_MAX, "expected_beta_sign": "-",
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_COUNTRIES,
        "min_years_per_country": MIN_YEARS,
        "min_hike_rows": MIN_HIKE_ROWS, "min_hike_countries": MIN_HIKE_COUNTRIES,
        "min_cut_rows": MIN_CUT_ROWS, "min_cut_countries": MIN_CUT_COUNTRIES,
        "max_top_one_percent_partialled_hike_share": MAX_TOP_1PCT,
        "max_top_country_partialled_hike_share": MAX_COUNTRY,
        "max_top_year_partialled_hike_share": MAX_YEAR,
        "expected_key_rows": EXPECTED["key_rows"],
        "expected_key_countries": EXPECTED["key_countries"],
        "expected_key_hike_rows": EXPECTED["hike_rows"],
        "expected_key_hike_countries": EXPECTED["hike_countries"],
        "expected_key_cut_rows": EXPECTED["cut_rows"],
        "expected_key_cut_countries": EXPECTED["cut_countries"],
        "roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {name: source[name] for name in ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()
        },
        "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
        "featured_eligible": False,
    }


def registration_commit() -> str:
    frozen = [SPEC, STEELMAN, PREREG, RUNNER, TESTS, ROSTER]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec["hypothesis_id"] != ID or spec["status"] != "pre_registered"
            or spec["claim_direction"] != "-" or spec["evidence_type"] != "associational"
            or spec["steelman"] != STEELMAN
            or spec["sample"]["countries"] != KEY_COUNTRIES
            or spec["sample"]["period"] != [T_START, T_END]
            or spec["falsification"]["threshold"] != threshold()
            or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
            or spec["linked_conditions"] != []):
        raise RuntimeError("frozen specification differs from runner contract")
    for forbidden in (LOCK, RUN_DIR, SUMMARY):
        if git("ls-tree", "-r", "--name-only", revision, "--", forbidden).strip():
            raise RuntimeError(f"registration commit contains postregistration artifact: {forbidden}")
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
        matches = [
            row for row in manifest.get("entries", [])
            if row.get("publisher") == source["publisher"]
            and row.get("series_id") == source["series_id"]
            and row.get("parquet_path") == source["path"]
            and row.get("sha256") == source["sha256"]
        ]
        if len(matches) != 1:
            raise RuntimeError(f"{role} source entry missing or ambiguous")
        row = matches[0]
        narrow[role] = {
            **source, "source_url": row.get("source_url"),
            "fetch_utc": row.get("fetch_utc"), "license": row.get("license"),
            "rows": row.get("rows"), "frequency": row.get("frequency"),
            "units": row.get("units"),
        }
    return narrow


def load_roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("fixed key-roster SHA-256 mismatch")
    raw = (ROOT / ROSTER).read_bytes()
    if not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("fixed key-roster header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    rows = [(row["country_iso3"], int(row["year"])) for row in records]
    if (len(rows) != EXPECTED["key_rows"] or len(set(rows)) != len(rows)
            or rows != sorted(rows, key=lambda item: (item[1], item[0]))
            or sorted({c for c, _ in rows}) != KEY_COUNTRIES):
        raise RuntimeError("fixed key-roster shape, order, or countries changed")
    return rows


def categories(delta: float) -> tuple[int, int]:
    """Return (hike, cut), with symmetric inclusive one-point boundaries."""
    return int(delta >= EVENT_PP), int(delta <= -EVENT_PP)


def source_keys() -> tuple[dict[tuple[str, int], float], set[tuple[str, int]]]:
    """Only the treatment value and selected outcome dimensions/keys are opened."""
    tax = pd.read_parquet(ROOT / SOURCES["treatment"]["path"],
                          columns=["country_iso3", "year", "value"])
    if (len(tax) != 950 or tax.duplicated(["country_iso3", "year"]).any()
            or not tax.country_iso3.str.fullmatch("[A-Z]{3}").all()):
        raise RuntimeError("OECD PIT source key contract changed")
    rates = {(str(c), int(y)): float(v)
             for c, y, v in tax.itertuples(index=False, name=None)}
    invalid = sorted(((c, y), v) for (c, y), v in rates.items()
                     if not math.isfinite(v) or not 0 <= v <= 100)
    if invalid != [(("FRA", 2013), 122.796992)]:
        raise RuntimeError(f"PIT validity contract changed: {invalid[:3]}")
    # The projection below intentionally omits value, Observation value,
    # OBS_STATUS, and Observation status. Do not widen it in preflight.
    key_columns = ["REF_AREA", "period", *SELECTOR]
    dimensions = pd.read_parquet(ROOT / SOURCES["outcome"]["path"], columns=key_columns)
    if len(dimensions) != 118344:
        raise RuntimeError("OECD IDD raw key envelope changed")
    selected = dimensions
    for column, code in SELECTOR.items():
        selected = selected.loc[selected[column].eq(code)]
    selected = selected[["REF_AREA", "period"]].copy()
    selected["period"] = pd.to_numeric(selected.period, errors="raise").astype(int)
    if (len(selected) != 656 or selected.REF_AREA.nunique() != 45
            or selected.duplicated(["REF_AREA", "period"]).any()):
        raise RuntimeError("selected IDD Gini keys changed or duplicated")
    outcome_keys = {(str(c), int(y)) for c, y in selected.itertuples(index=False, name=None)}
    return rates, outcome_keys


def partialled_hike_concentration(panel: pd.DataFrame) -> dict[str, float] | None:
    """Residualize hike on cut and country/year FE, then measure signal spread."""
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    design = pd.concat([
        panel[["cut"]].reset_index(drop=True).astype(float),
        pd.get_dummies(panel.country_iso3, drop_first=True, dtype=float).reset_index(drop=True),
        pd.get_dummies(panel.year, drop_first=True, dtype=float).reset_index(drop=True),
    ], axis=1)
    design.insert(0, "intercept", 1.0)
    x = panel.hike.to_numpy(dtype=float)
    matrix = design.to_numpy(dtype=float)
    residual = x - matrix @ np.linalg.lstsq(matrix, x, rcond=None)[0]
    squared = np.square(residual)
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(len(panel) * 0.01))
    labels = pd.DataFrame({
        "country": panel.country_iso3.to_numpy(),
        "year": panel.year.to_numpy(),
        "signal": squared,
    })
    return {
        "top_one_percent_share": float(np.sort(squared)[-top_n:].sum() / total),
        "top_country_share": float(labels.groupby("country").signal.sum().max() / total),
        "top_year_share": float(labels.groupby("year").signal.sum().max() / total),
    }


def key_preflight() -> dict[str, Any]:
    rates, gini_keys = source_keys()
    candidates = []
    for (country, year), current in rates.items():
        if not (T_START <= year <= T_END and (country, year - 1) in rates
                and (country, year) in gini_keys and (country, year + 1) in gini_keys):
            continue
        previous = rates[(country, year - 1)]
        if not (math.isfinite(current) and 0 <= current <= 100
                and math.isfinite(previous) and 0 <= previous <= 100):
            continue
        hike, cut = categories(current - previous)
        candidates.append((country, year, hike, cut))
    counts = Counter(c for c, _, _, _ in candidates)
    rows = sorted((r for r in candidates if counts[r[0]] >= MIN_YEARS),
                  key=lambda r: (r[1], r[0]))
    if [(c, y) for c, y, _, _ in rows] != load_roster():
        raise RuntimeError("key-only roster no longer matches source keys and tax values")
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "hike", "cut"])
    hike, cut = panel.loc[panel.hike.eq(1)], panel.loc[panel.cut.eq(1)]
    shares = partialled_hike_concentration(panel)
    if shares is None:
        raise RuntimeError("no treatment signal after key-only fixed effects")
    if (len(panel) != EXPECTED["key_rows"]
            or panel.country_iso3.nunique() != EXPECTED["key_countries"]
            or len(hike) != EXPECTED["hike_rows"]
            or hike.country_iso3.nunique() != EXPECTED["hike_countries"]
            or len(cut) != EXPECTED["cut_rows"]
            or cut.country_iso3.nunique() != EXPECTED["cut_countries"]
            or any(not math.isclose(shares[name], EXPECTED[name], abs_tol=1e-8)
                   for name in ("top_one_percent_share", "top_country_share", "top_year_share"))):
        raise RuntimeError("frozen exposure-only envelope changed")
    return {
        "treatment_values_read": True, "outcome_values_read": False,
        "outcome_null_masks_read": False, "outcome_status_read": False,
        "outcome_dimensions_and_keys_only": True,
        "treatment_years": [T_START, T_END],
        "roster_sha256": ROSTER_SHA, "key_rows": len(panel),
        "key_countries": int(panel.country_iso3.nunique()),
        "hike_rows": len(hike), "hike_countries": int(hike.country_iso3.nunique()),
        "cut_rows": len(cut), "cut_countries": int(cut.country_iso3.nunique()),
        "stable_rows": int((panel.hike.eq(0) & panel.cut.eq(0)).sum()),
        "partialled_hike": shares,
    }


def lock_payload(revision: str, sources: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
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
    if (ROOT / RUN_DIR).exists() or (ROOT / SUMMARY).exists():
        raise RuntimeError("measured result artifacts exist before source lock")
    payload = lock_payload(revision, check_sources(), key_preflight())
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit it separately before reading Gini outcome values")


def check_source_lock(revision: str, sources: dict[str, Any],
                      preflight: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if json.loads(path.read_text()) != lock_payload(revision, sources, preflight):
        raise RuntimeError("committed source lock differs from frozen sources or preflight")
    commit = first_addition(LOCK)
    if commit == revision or subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock must follow registration in a separate commit")
    committed_unchanged(LOCK, commit)
    for forbidden in (RUN_DIR, SUMMARY):
        if git("ls-tree", "-r", "--name-only", commit, "--", forbidden).strip():
            raise RuntimeError(f"source-lock commit contains measured result: {forbidden}")
    return commit


def measured_panel(roster: list[tuple[str, int]],
                   lock_commit: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """First access to selected Gini values, null masks, and OBS_STATUS."""
    if first_addition(LOCK) != lock_commit:
        raise RuntimeError("committed source lock required before Gini measurement")
    rates, _ = source_keys()
    selector = None
    for dimension, code in SELECTOR.items():
        clause = pc.field(dimension) == code
        selector = clause if selector is None else selector & clause
    frame = ds.dataset(ROOT / SOURCES["outcome"]["path"]).to_table(
        columns=["REF_AREA", "period", "value", "OBS_STATUS"],
        filter=selector,
    ).to_pandas()
    frame["period"] = pd.to_numeric(frame.period, errors="raise").astype(int)
    if frame.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("selected Gini outcome keys duplicated")
    values = {
        (str(c), int(y)): (pd.to_numeric(v, errors="coerce"), "" if pd.isna(s) else str(s).strip())
        for c, y, v, s in frame.itertuples(index=False, name=None)
    }
    rows = []
    missing_or_invalid = 0
    rejected_status = 0
    for country, year in roster:
        current, current_status = values.get((country, year), (float("nan"), ""))
        future, future_status = values.get((country, year + 1), (float("nan"), ""))
        if not (math.isfinite(current) and 0 <= current <= 1
                and math.isfinite(future) and 0 <= future <= 1):
            missing_or_invalid += 1
            continue
        if current_status != "A" or future_status != "A":
            rejected_status += 1
            continue
        hike, cut = categories(rates[(country, year)] - rates[(country, year - 1)])
        rows.append({
            "country_iso3": country, "year": year, "hike": hike, "cut": cut,
            "gini_forward_change": float(future - current),
        })
    panel = pd.DataFrame(rows, columns=[
        "country_iso3", "year", "hike", "cut", "gini_forward_change",
    ])
    before = len(panel)
    counts = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    hike, cut = panel.loc[panel.hike.eq(1)], panel.loc[panel.cut.eq(1)]
    gate = {
        "roster_rows": len(roster),
        "dropped_missing_or_invalid_endpoint_pairs": missing_or_invalid,
        "dropped_non_A_status_pairs": rejected_status,
        "complete_pairs_before_five_year_country_floor": before,
        "valid_rows": len(panel),
        "valid_countries": int(panel.country_iso3.nunique()),
        "hike_rows": len(hike),
        "hike_countries": int(hike.country_iso3.nunique()),
        "cut_rows": len(cut),
        "cut_countries": int(cut.country_iso3.nunique()),
        "stable_rows": int((panel.hike.eq(0) & panel.cut.eq(0)).sum()),
        "outcome_values_read_after_lock": True,
    }
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES
            or gate["hike_rows"] < MIN_HIKE_ROWS
            or gate["hike_countries"] < MIN_HIKE_COUNTRIES
            or gate["cut_rows"] < MIN_CUT_ROWS
            or gate["cut_countries"] < MIN_CUT_COUNTRIES):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or hike/cut event floor failed", "primary": None}
    shares = partialled_hike_concentration(panel)
    gate["partialled_hike"] = shares
    if (shares is None or shares["top_one_percent_share"] > MAX_TOP_1PCT
            or shares["top_country_share"] > MAX_COUNTRY
            or shares["top_year_share"] > MAX_YEAR):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "partialled-hike concentration or variation gate failed", "primary": None}
    model = smf.ols("gini_forward_change ~ hike + cut + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed-effect model lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={
        "groups": panel.country_iso3, "use_correction": True,
        "df_correction": True,
    }, use_t=True)
    beta, se = float(fit.params["hike"]), float(fit.bse["hike"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive country-cluster uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite country-cluster t inference", "primary": None}
    primary = {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 1 - P_MAX,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": groups,
        "df_inference": groups - 1, "model_rank": int(fit.model.rank),
        "cut_coefficient_nuisance": float(fit.params["cut"]),
        "method": "country/year FE OLS with hike and cut indicators; country-cluster CR1; Student t(G-1)",
    }
    if beta <= -MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "negative hike association clears frozen magnitude and p cutoff"
    elif beta >= MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "positive hike association clears frozen magnitude and p cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable hike association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def summary_text(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = "not estimated" if primary is None else f"{primary['coefficient']:+.6g}"
    p = "not estimated" if primary is None else f"{primary['p_value_two_sided']:.6g}"
    return (
        "# OECD top PIT hikes and next-year disposable-income Gini\n\n"
        f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
        f"**{result['verdict']}** — {result['reason']}.\n\n"
        f"Key-only upper bound: {EXPECTED['key_rows']} country-years / {EXPECTED['key_countries']} countries. "
        f"Complete pairs: {gate['valid_rows']} / {gate['valid_countries']}; "
        f"hike years: {gate['hike_rows']} / {gate['hike_countries']}; "
        f"cut years: {gate['cut_rows']} / {gate['cut_countries']}.\n\n"
        f"Hike coefficient: {beta} Gini units; two-sided country-cluster t p: {p}. "
        "The cut coefficient is nuisance only. A meaningful verdict requires |beta| >= 0.005 "
        "and p <= 0.005. This one-test threshold does not correct the visible archive-wide search. "
        "No causal, policy, school, position, or featured credit.\n"
    )


def artifacts(result: dict[str, Any], registration: str,
              lock_commit: str, stamp: str) -> dict[str, Any]:
    gate, primary = result["gate"], result["primary"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC, "topic": "distribution"},
        "preregistration": {
            "spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": 1, "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN,
        },
        "reproduction": {
            "runner": RUNNER, "run_dir": RUN_DIR,
            "command": f"python3 {RUNNER} --verify",
        },
        "verdict": {
            "raw": result["verdict"], "bucket": result["verdict"].lower(),
            "reason": result["reason"],
        },
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary}, "limitations": LIMITATIONS,
        "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": ID, "family_id": FAMILY,
        "verdict": result["verdict"], "verdict_label": result["verdict"],
        "verdict_reason": result["reason"], "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
        "primary": primary, "p_max_two_sided": P_MAX,
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": result["verdict"],
        "vintages": list(SOURCES.values()), "derived_panel": gate,
        "correction": CORRECTION,
    }
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\n"
        "import subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    chart = {"hypothesis_id": ID, "family_id": FAMILY,
             "verdict": result["verdict"], "primary": primary}
    coefficients = [{"term": "hike", **primary}] if primary is not None else []
    return {
        "packet": packet, "diagnostics": diagnostics, "manifest": manifest,
        "wrapper": wrapper, "chart": chart, "coefficients": coefficients,
    }


def write_artifacts(result: dict[str, Any], registration: str,
                    lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("result artifact already exists")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = artifacts(result, registration, lock_commit, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(summary_text(result, registration, lock_commit))
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    columns = [
        "term", "coefficient", "std_error", "p_value_two_sided",
        "confidence_level", "confidence_interval", "n_rows", "n_countries",
        "df_inference", "model_rank", "cut_coefficient_nuisance", "method",
    ]
    pd.DataFrame(payload["coefficients"], columns=columns).to_parquet(
        folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(result, registration, lock_commit))


def replay_equal(actual: Any, expected: Any, label: str) -> None:
    """Compare complete artifacts, normalizing Parquet arrays and numeric scalars."""
    if isinstance(actual, np.ndarray):
        actual = actual.tolist()
    if isinstance(expected, np.ndarray):
        expected = expected.tolist()
    if isinstance(actual, np.generic):
        actual = actual.item()
    if isinstance(expected, np.generic):
        expected = expected.item()
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label} mapping keys differ")
        for key, value in expected.items():
            replay_equal(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label} list differs")
        for index, (got, wanted) in enumerate(zip(actual, expected)):
            replay_equal(got, wanted, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not isinstance(actual, (float, int)) or not math.isclose(
                actual, expected, rel_tol=1e-10, abs_tol=1e-12):
            raise AssertionError(f"{label} numeric result differs")
    elif type(actual) is not type(expected) or actual != expected:
        raise AssertionError(f"{label} differs")


def verify_artifacts(result: dict[str, Any], registration: str,
                     lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    diagnostics = json.loads((folder / "diagnostics.json").read_text())
    stamp = diagnostics["run_utc"]
    datetime.fromisoformat(stamp)
    expected = artifacts(result, registration, lock_commit, stamp)
    replay_equal(diagnostics, expected["diagnostics"], "diagnostics")
    replay_equal(
        yaml.safe_load((folder / "evidence_packet.yaml").read_text()),
        expected["packet"], "evidence_packet",
    )
    replay_equal(
        yaml.safe_load((folder / "manifest.yaml").read_text()),
        expected["manifest"], "manifest",
    )
    replay_equal(
        json.loads((folder / "chart_data.json").read_text()),
        expected["chart"], "chart_data",
    )
    saved_coefficients = pd.read_parquet(folder / "coefficients.parquet").to_dict("records")
    replay_equal(saved_coefficients, expected["coefficients"], "coefficients")
    if (folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes():
        raise AssertionError("stored hypothesis copy differs")
    if (folder / "replication.py").read_text() != expected["wrapper"]:
        raise AssertionError("replication wrapper differs")
    summary = summary_text(result, registration, lock_commit)
    if (folder / "result_card.md").read_text() != summary:
        raise AssertionError("result card differs from replay")
    if (ROOT / SUMMARY).read_text() != summary:
        raise AssertionError("summary differs from replay")
    print("verified full preregistered top-PIT to disposable-Gini artifact set")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for mode in ("preflight", "lock", "run", "verify"):
        modes.add_argument(f"--{mode}", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps({"sources": check_sources(), "key_preflight": key_preflight()}, indent=2))
        return 0
    if args.lock:
        write_source_lock()
        return 0
    registration = registration_commit()
    sources, preflight = check_sources(), key_preflight()
    lock_commit = check_source_lock(registration, sources, preflight)
    panel, gate = measured_panel(load_roster(), lock_commit)
    result = estimate(panel, gate)
    if args.run:
        write_artifacts(result, registration, lock_commit)
        print(result["verdict"], result["gate"])
    else:
        verify_artifacts(result, registration, lock_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
