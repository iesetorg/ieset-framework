#!/usr/bin/env python3
"""Guarded WGI-to-WITS calibration; WITS counts open only after a separate source lock."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
STUDY = "wgi_ge_exported_hs6_breadth_forward_2026"
FAMILY = "wgi_ge_wits_exported_hs6_breadth_2026_10_10"
RUNNER = "scripts/run_wgi_ge_wits_exported_hs6_breadth_2026.py"
TEST = "tests/test_wgi_ge_wits_exported_hs6_breadth_2026.py"
SPEC = f"hypotheses/trade/{STUDY}.yaml"
STEELMAN = f"hypotheses/steelman/{STUDY}.md"
PREREG = "engine/audits/wgi_ge_wits_exported_hs6_breadth_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wgi_ge_wits_exported_hs6_breadth_2026_key_roster.csv"
ROSTER_SHA = "459f554e2fca7cda99b83a4281fd45a112b38c88878f176f3d2c98fecffd0bb2"
LOCK = "data/pinned_evidence/wgi_ge_wits_exported_hs6_breadth_2026.manifest.json"
RESULT_DIR = f"engine/runs/{STUDY}"
SUMMARY = "engine/audits/wgi_ge_wits_exported_hs6_breadth_results_2026-10-10.md"

T_START, T_END, WINDOW, MIN_YEARS = 2003, 2016, 3, 6
MATERIAL, PRACTICAL_BETA, P_MAX = 0.15, 0.10, 0.01
MIN_ROWS, MIN_REPORTERS = 1200, 100
MIN_UP_ROWS, MIN_UP_REPORTERS = 200, 75
MIN_DOWN_ROWS, MIN_DOWN_REPORTERS = 100, 50
MAX_TOP_ROWS, MAX_TOP_REPORTER = 0.30, 0.20
KEY_ROWS, KEY_REPORTERS, KEY_UP, KEY_DOWN = 1862, 153, 508, 252

SOURCES = {
    "treatment": {
        "publisher": "wgi", "series_id": "GOV_WGI_GE.EST",
        "path": "data/vintages/wgi/GOV_WGI_GE.EST@2026-05-05T195208Z.parquet",
        "sha256": "607d47979340b803fec2fefc1e57c94a7a167432317451ea0b1ade3ee0503edc",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
    "control": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
    "outcome": {
        "publisher": "wits", "series_id": "unique_hs6_products",
        "path": "data/vintages/wits/unique_hs6_products@2026-07-23T153652Z.parquet",
        "sha256": "29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934",
        "manifest": "data/manifests/fetch_run_2026-07-23T153659Z.yaml",
        "manifest_sha256": "542aacbcc80b1856262eda14f37d0532c7a14611c8b9d698ab516529942d0b73",
    },
}
WITS_SELECTOR = {
    "freq_id": "A", "partner_iso3": "WLD", "product_code": "999999",
    "indicator_id": "NMBR-XPRT-HS6-PRDCT", "series_id": "unique_hs6_products",
}
WITS_KEY_COLUMNS = ["freq_id", "country_iso3", "partner_iso3", "product_code",
                    "indicator_id", "year", "series_id"]
FORMULA = ("forward_change ~ delta_wgi + baseline_breadth + prior_breadth_change "
           "+ log_gdp_pc + prior_gdp_change + C(country_iso3) + C(year)")
RESIDUAL_FORMULA = ("delta_wgi ~ baseline_breadth + prior_breadth_change "
                    "+ log_gdp_pc + prior_gdp_change + C(country_iso3) + C(year)")
PREFLIGHT_RESIDUAL_FORMULA = "delta_wgi ~ log_gdp_pc + prior_gdp_change + C(country_iso3) + C(year)"
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": P_MAX,
    "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0,
    "featured_eligible": False,
}
LIMITATIONS = [
    "WGI government effectiveness is a composite estimate, not policy assignment or a direct customs measure.",
    "Income, trade agreements, demand, infrastructure, exchange rates and governance can move together.",
    "Prior export breadth may be affected by governance, and its adjustment can attenuate a genuine pathway.",
    "WITS counts reported exported HS6 categories, not export value, complexity, domestic content or welfare.",
    "The pinned WITS Parquet has no observation-status or method-break field; normal status is unverified.",
    "Three-year windows overlap; reporter clustering does not establish causality.",
    "The WITS outcome source has appeared in related archive work, so this is not an archive-wide independent holdout.",
    "Zero causal, policy, position, school-score and featured credit applies to every verdict.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"no first-addition commit: {relative}")
    return commits[-1]


def frozen_file(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"registered or locked file changed: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted registered or locked file: {relative}")


def threshold() -> dict[str, Any]:
    files = {role: {field: source[field] for field in ("path", "sha256", "manifest", "manifest_sha256")}
             for role, source in SOURCES.items()}
    return {
        "family_id": FAMILY, "family_size": 1, "family_alpha": P_MAX,
        "p_max_two_sided": P_MAX, "meaningful_abs_beta_log_per_point": PRACTICAL_BETA,
        "material_abs_change_wgi_points": MATERIAL,
        "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_REPORTERS,
        "min_years_per_country": MIN_YEARS,
        "min_improvement_rows": MIN_UP_ROWS, "min_improvement_countries": MIN_UP_REPORTERS,
        "min_deterioration_rows": MIN_DOWN_ROWS, "min_deterioration_countries": MIN_DOWN_REPORTERS,
        "max_top_one_percent_residual_treatment_share": MAX_TOP_ROWS,
        "max_top_country_residual_treatment_share": MAX_TOP_REPORTER,
        "expected_key_rows": KEY_ROWS, "expected_key_countries": KEY_REPORTERS,
        "expected_improvement_rows": KEY_UP, "expected_deterioration_rows": KEY_DOWN,
        "roster_sha256": ROSTER_SHA, "source_files": files,
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }


def check_sources(source_root: Path) -> dict[str, dict[str, Any]]:
    """Hash files and select the three original fetch entries, without opening outcome columns."""
    selected = {}
    for role, pin in SOURCES.items():
        raw, manifest = source_root / pin["path"], source_root / pin["manifest"]
        if not raw.is_file() or sha256(raw) != pin["sha256"]:
            raise RuntimeError(f"missing or mismatched raw source: {role}")
        if not manifest.is_file() or sha256(manifest) != pin["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("publisher") == pin["publisher"]
                   and entry.get("series_id") == pin["series_id"]
                   and entry.get("parquet_path") == pin["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != pin["sha256"]:
            raise RuntimeError(f"fetch manifest lacks exact pinned entry: {role}")
        entry = matches[0]
        selected[role] = {**pin, "source_url": entry.get("source_url"),
                          "methodology_url": entry.get("methodology_url"),
                          "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc")}
    return selected


def load_roster() -> list[tuple[str, int]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("fixed key-only roster hash mismatch")
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["study_id", "country_iso3", "year"]:
            raise RuntimeError("invalid key roster header")
        rows = list(reader)
    if len(rows) != KEY_ROWS or any(row["study_id"] != STUDY for row in rows):
        raise RuntimeError("key roster identity or row count changed")
    keys = [(row["country_iso3"], int(row["year"])) for row in rows]
    if len(set(keys)) != len(keys) or keys != sorted(keys) or len({c for c, _ in keys}) != KEY_REPORTERS:
        raise RuntimeError("invalid key roster order, duplicates, or reporter count")
    if any(not (T_START <= year <= T_END) for _, year in keys):
        raise RuntimeError("key roster treatment year outside frozen window")
    return keys


def registration_commit() -> str:
    paths = [RUNNER, TEST, SPEC, STEELMAN, PREREG, ROSTER]
    revisions = {first_addition(path) for path in paths}
    if len(revisions) != 1:
        raise RuntimeError("six registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in paths:
        frozen_file(path, revision)
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RESULT_DIR).strip():
        raise RuntimeError("registration commit already contained measured results")
    if git_output("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("registration commit already contained source lock")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    roster_countries = sorted({country for country, _ in load_roster()})
    if (spec.get("hypothesis_id") != STUDY or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "+"
            or spec.get("steelman") != STEELMAN or spec["sample"].get("period") != [T_START, T_END]
            or spec["sample"].get("countries") != roster_countries
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or spec["falsification"].get("threshold") != threshold()):
        raise RuntimeError("registered hypothesis differs from guarded runner or roster")
    return revision


def selected_wits_keys(source_root: Path) -> set[tuple[str, int]]:
    """Read only WITS dimension and key columns; never its value or null mask."""
    path = source_root / SOURCES["outcome"]["path"]
    parquet = pq.ParquetFile(path)
    names = parquet.schema_arrow.names
    if (parquet.metadata.num_rows != 5308 or any(name not in names for name in WITS_KEY_COLUMNS + ["value"])
            or any("status" in name.lower() for name in names)):
        raise RuntimeError("WITS schema, row count, or status-field contract changed")
    frame = pd.read_parquet(path, columns=WITS_KEY_COLUMNS)
    for column, value in WITS_SELECTOR.items():
        frame = frame.loc[frame[column].eq(value)]
    frame = frame.copy()
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate selected WITS reporter-year key")
    return {(str(country), int(year)) for country, year in
            frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def treatment_and_control(source_root: Path, allowed: set[str]) -> tuple[dict[tuple[str, int], float], dict[tuple[str, int], float]]:
    wgi = pd.read_parquet(source_root / SOURCES["treatment"]["path"],
                          columns=["country_iso3", "indicator_id", "year", "value"])
    if len(wgi) != 5616 or not wgi.indicator_id.eq("GOV_WGI_GE.EST").all():
        raise RuntimeError("WGI source row or indicator contract changed")
    wgi = wgi.loc[wgi.country_iso3.isin(allowed)].copy()
    if wgi.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WGI reporter-year key")
    wgi["value"] = pd.to_numeric(wgi.value, errors="coerce")
    wgi = wgi.loc[np.isfinite(wgi.value) & wgi.value.between(-2.5, 2.5)]
    treatment = {(str(c), int(y)): float(v) for c, y, v in
                 wgi[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}

    wdi = pd.read_parquet(source_root / SOURCES["control"]["path"],
                          columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(wdi) != 17556 or not wdi.indicator_id.eq("NY.GDP.PCAP.KD").all():
        raise RuntimeError("WDI source row or indicator contract changed")
    wdi = wdi.loc[wdi.country_iso3.isin(allowed)].copy()
    if wdi.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI reporter-year key")
    wdi["value"] = pd.to_numeric(wdi.value, errors="coerce")
    wdi = wdi.loc[wdi.obs_status.fillna("").eq("") & np.isfinite(wdi.value) & wdi.value.gt(0)]
    control = {(str(c), int(y)): math.log(float(v)) for c, y, v in
               wdi[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    return treatment, control


def candidate_panel(source_root: Path) -> pd.DataFrame:
    roster = load_roster()
    allowed = {country for country, _ in roster}
    keys = selected_wits_keys(source_root)
    treatment, control = treatment_and_control(source_root, allowed)
    rows = []
    for country in sorted(allowed):
        for year in range(T_START, T_END + 1):
            if any((country, y) not in keys for y in (year - WINDOW, year, year + WINDOW)):
                continue
            if any((country, y) not in treatment or (country, y) not in control
                   for y in (year - WINDOW, year)):
                continue
            delta = treatment[country, year] - treatment[country, year - WINDOW]
            rows.append({"country_iso3": country, "year": year, "delta_wgi": delta,
                         "improvement": int(delta >= MATERIAL), "deterioration": int(delta <= -MATERIAL),
                         "log_gdp_pc": control[country, year],
                         "prior_gdp_change": control[country, year] - control[country, year - WINDOW]})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "delta_wgi", "improvement",
                                        "deterioration", "log_gdp_pc", "prior_gdp_change"])
    if panel.empty:
        raise RuntimeError("no source-only candidate panel")
    counts = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].reset_index(drop=True)
    derived = [(str(c), int(y)) for c, y in panel[["country_iso3", "year"]].itertuples(index=False, name=None)]
    if derived != roster:
        raise RuntimeError("source-only candidate keys differ from fixed roster")
    return panel


def residual_shares(panel: pd.DataFrame, *, complete: bool) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    fit = smf.ols(RESIDUAL_FORMULA if complete else PREFLIGHT_RESIDUAL_FORMULA, data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * len(panel)))
    top_rows = float(np.sort(squared)[-top_n:].sum() / total)
    top_reporter = float(pd.DataFrame({"reporter": panel.country_iso3.to_numpy(), "squared": squared})
                         .groupby("reporter").squared.sum().max() / total)
    return top_rows, top_reporter


def preflight(source_root: Path) -> dict[str, Any]:
    panel = candidate_panel(source_root)
    up, down = int(panel.improvement.sum()), int(panel.deterioration.sum())
    if (len(panel) != KEY_ROWS or panel.country_iso3.nunique() != KEY_REPORTERS
            or up != KEY_UP or down != KEY_DOWN):
        raise RuntimeError("source-only treatment envelope changed")
    shares = residual_shares(panel, complete=False)
    if shares is None or shares[0] > MAX_TOP_ROWS or shares[1] > MAX_TOP_REPORTER:
        raise RuntimeError("source-only residual treatment concentration gate failed")
    return {
        "key_only_rows": len(panel), "key_only_reporters": int(panel.country_iso3.nunique()),
        "treatment_years": int(panel.year.nunique()), "material_improvement_rows": up,
        "material_improvement_reporters": int(panel.loc[panel.improvement.eq(1), "country_iso3"].nunique()),
        "material_deterioration_rows": down,
        "material_deterioration_reporters": int(panel.loc[panel.deterioration.eq(1), "country_iso3"].nunique()),
        "top_one_percent_treatment_share": round(shares[0], 6),
        "top_reporter_treatment_share": round(shares[1], 6),
        "outcome_value_or_null_opened": False, "outcome_status_field_available": False,
    }


def lock_payload(registration: str, sources: dict[str, Any], keys: dict[str, Any]) -> dict[str, Any]:
    return {"schema": "ieset-narrow-source-lock-v1", "family_id": FAMILY,
            "preregistration_commit": registration, "selected_sources": sources,
            "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": keys, "outcome_values_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_lock(sources: dict[str, Any], keys: dict[str, Any]) -> None:
    registration = registration_commit()
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, sources, keys), indent=2,
                               sort_keys=True, allow_nan=False) + "\n")
    print(f"wrote {LOCK}; commit it separately before --run")


def check_lock(registration: str, sources: dict[str, Any], keys: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if not path.is_file() or json.loads(path.read_text()) != lock_payload(registration, sources, keys):
        raise RuntimeError("source lock differs from registration or source-only preflight")
    revision = first_addition(LOCK)
    if revision == registration or subprocess.run(
        ["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT, check=False
    ).returncode:
        raise RuntimeError("source-lock commit must separately descend from registration")
    frozen_file(LOCK, revision)
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RESULT_DIR).strip():
        raise RuntimeError("source-lock commit already contained measured results")
    return revision


def valid_count(value: Any) -> int | None:
    """The only permitted numeric WITS value conversion, called after lock checks."""
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
        return None
    return int(numeric)


def measured_panel(source_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read selected WITS counts only after registration and source lock verification."""
    candidate = candidate_panel(source_root)
    path = source_root / SOURCES["outcome"]["path"]
    frame = pd.read_parquet(path, columns=WITS_KEY_COLUMNS + ["value"])
    for column, value in WITS_SELECTOR.items():
        frame = frame.loc[frame[column].eq(value)]
    frame = frame.loc[frame.country_iso3.isin(candidate.country_iso3.unique())].copy()
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate measured WITS selector key")
    values = {(str(c), int(y)): valid_count(v) for c, y, v in
              frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    rows, invalid = [], 0
    for row in candidate.itertuples(index=False):
        before = values.get((row.country_iso3, row.year - WINDOW))
        baseline = values.get((row.country_iso3, row.year))
        forward = values.get((row.country_iso3, row.year + WINDOW))
        if before is None or baseline is None or forward is None:
            invalid += 1
            continue
        prior = math.log1p(baseline) - math.log1p(before)
        rows.append({"country_iso3": row.country_iso3, "year": row.year,
                     "delta_wgi": row.delta_wgi, "improvement": row.improvement,
                     "deterioration": row.deterioration, "log_gdp_pc": row.log_gdp_pc,
                     "prior_gdp_change": row.prior_gdp_change,
                     "baseline_breadth": math.log1p(baseline), "prior_breadth_change": prior,
                     "forward_change": math.log1p(forward) - math.log1p(baseline)})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "delta_wgi", "improvement",
                                        "deterioration", "log_gdp_pc", "prior_gdp_change",
                                        "baseline_breadth", "prior_breadth_change", "forward_change"])
    before_country_floor = len(panel)
    if not panel.empty:
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].reset_index(drop=True)
    gate = {
        "key_only_rows": len(candidate), "invalid_or_missing_wits_triples": invalid,
        "complete_triples_before_six_year_reporter_floor": before_country_floor,
        "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
        "improvement_rows": int(panel.improvement.sum()),
        "improvement_countries": int(panel.loc[panel.improvement.eq(1), "country_iso3"].nunique()),
        "deterioration_rows": int(panel.deterioration.sum()),
        "deterioration_countries": int(panel.loc[panel.deterioration.eq(1), "country_iso3"].nunique()),
        "outcome_values_read_after_lock": True, "outcome_status_field_available": False,
    }
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_REPORTERS
            or gate["improvement_rows"] < MIN_UP_ROWS
            or gate["improvement_countries"] < MIN_UP_REPORTERS
            or gate["deterioration_rows"] < MIN_DOWN_ROWS
            or gate["deterioration_countries"] < MIN_DOWN_REPORTERS):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case, reporter, or treatment-movement floor failed", "primary": None}
    shares = residual_shares(panel, complete=True)
    gate["residual_treatment_shares"] = (
        {"top_one_percent_rows": shares[0], "top_reporter": shares[1]} if shares else None
    )
    if shares is None or shares[0] > MAX_TOP_ROWS or shares[1] > MAX_TOP_REPORTER:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residual treatment concentration gate failed", "primary": None}
    model = smf.ols(FORMULA, data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed primary design lacks full rank", "primary": None}
    clusters = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                   "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["delta_wgi"]), float(fit.bse["delta_wgi"])
    if not all(math.isfinite(x) for x in (beta, se)) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive country-cluster uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), clusters - 1))
    critical = float(student_t.ppf(0.995, clusters - 1))
    if not all(math.isfinite(x) for x in (p, critical)):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite primary inference", "primary": None}
    primary = {
        "beta_log1p_breadth_per_wgi_point": beta, "std_error": se,
        "p_value_two_sided": p, "confidence_level": 0.99,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_reporters": clusters, "df_inference": clusters - 1,
        "model_rank": int(fit.model.rank),
        "method": "reporter/year FE OLS with prior export breadth and GDP controls, reporter-cluster CR1, Student t(G-1)",
    }
    if beta >= PRACTICAL_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive WGI coefficient clears frozen size and two-sided p gates"
    elif beta <= -PRACTICAL_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite WGI coefficient clears frozen size and two-sided p gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": STUDY, "path": SPEC, "topic": "trade"},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                            "family_id": FAMILY, "family_size": 1, "key_roster": ROSTER,
                            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RESULT_DIR,
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary}, "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": STUDY, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "primary": primary,
        "p_max_two_sided": P_MAX, "meaningful_abs_beta_log_per_point": PRACTICAL_BETA,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": STUDY, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
        "derived_panel": gate, "correction": CORRECTION,
    }
    card = (f"# Result card: {STUDY}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
            f"WGI government-effectiveness change from t-3 to t predicts WITS exported-HS6 "
            f"product-count change from t to t+3, conditional on fixed controls. Key-only ceiling: "
            f"{KEY_ROWS} reporter-years / {KEY_REPORTERS} reporter economies. "
            f"Complete rows: {gate['valid_rows']} / {gate['valid_countries']}; material improvements: "
            f"{gate['improvement_rows']} / {gate['improvement_countries']}; deteriorations: "
            f"{gate['deterioration_rows']} / {gate['deterioration_countries']}.\n")
    if primary is not None:
        card += (f"\nPrimary coefficient={primary['beta_log1p_breadth_per_wgi_point']:+.6g} "
                 f"log1p-count point per WGI point; reporter-cluster SE={primary['std_error']:.6g}; "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}; "
                 f"99% CI={primary['confidence_interval']}.\n")
    card += ("\nOne fixed two-sided test: p <= 0.01 and |coefficient| >= 0.10 for a directional verdict. "
             "WITS has no source status or method-break field. Descriptive calibration only; "
             "zero causal, policy, position, school-score, and featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": STUDY, "family_id": FAMILY, "verdict": verdict,
             "primary_coefficient": primary}
    coefficients = ([{
        "term": "wgi_government_effectiveness_three_year_change",
        "coefficient": primary["beta_log1p_breadth_per_wgi_point"], "std_error": primary["std_error"],
        "p_value_two_sided": primary["p_value_two_sided"],
        "confidence_level": primary["confidence_level"],
        "confidence_interval": primary["confidence_interval"],
        "n_rows": primary["n_rows"], "n_reporters": primary["n_reporters"],
        "df_inference": primary["df_inference"], "model_rank": primary["model_rank"],
        "method": primary["method"],
    }] if primary is not None else [])
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = f"{primary['beta_log1p_breadth_per_wgi_point']:+.6g}" if primary else "not estimated"
    p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
    return ("# WGI government effectiveness and exported HS6 breadth: descriptive result\n\n"
            f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
            f"Verdict **{result['verdict']}**: {result['reason']}.\n\n"
            f"Complete pairs {gate['valid_rows']} / {gate['valid_countries']} reporter economies; "
            f"material improvements {gate['improvement_rows']} / {gate['improvement_countries']}; "
            f"material deteriorations {gate['deterioration_rows']} / {gate['deterioration_countries']}. "
            f"Primary coefficient {beta} log1p-count point per WGI point; two-sided p {p}.\n\n"
            "This is a source-distinct descriptive calibration with no causal, policy, position, "
            "school-score, or featured credit. WITS has no status or method-break field.\n")


def write_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RESULT_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = artifact_payload(result, registration, lock_commit, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2, allow_nan=False) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2, allow_nan=False) + "\n")
    pd.DataFrame(payload["coefficients"], columns=[
        "term", "coefficient", "std_error", "p_value_two_sided", "confidence_level",
        "confidence_interval", "n_rows", "n_reporters", "df_inference", "model_rank", "method",
    ]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(result, registration, lock_commit))


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
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RESULT_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    payload = artifact_payload(result, registration, lock_commit, saved["run_utc"])
    equal_close(saved, payload["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"], "packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"], "chart")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != payload["card"]
            or (folder / "replication.py").read_text() != payload["wrapper"]):
        raise AssertionError("result text artifact mismatch")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                payload["coefficients"], "coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(result, registration, lock_commit):
        raise AssertionError("summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("preflight", "lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT,
                        help="Allowed only for read-only --preflight outside this checkout")
    args = parser.parse_args()
    if args.source_root != ROOT and not args.preflight:
        parser.error("--source-root override is restricted to read-only preflight")
    sources = check_sources(args.source_root)
    keys = preflight(args.source_root)
    if args.preflight:
        print(json.dumps(keys, indent=2, sort_keys=True, allow_nan=False))
        return 0
    if args.lock:
        write_lock(sources, keys)
        return 0
    registration = registration_commit()
    lock_commit = check_lock(registration, sources, keys)
    panel, gate = measured_panel(ROOT)
    result = estimate(panel, gate)
    if args.run:
        write_artifacts(result, registration, lock_commit)
        print(result["verdict"], result["reason"])
        return 0
    verify_artifacts(result, registration, lock_commit)
    print("verified exact replay", STUDY, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
