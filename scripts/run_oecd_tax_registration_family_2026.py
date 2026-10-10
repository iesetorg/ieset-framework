#!/usr/bin/env python3
"""Frozen OECD tax-cut to WDI registration-growth two-test study.

--preflight reads OECD treatment values and WDI country/year keys only.
--lock requires an earlier committed registration and writes a narrow source lock.
--run/--verify read WDI values and status only after the source lock is separately committed.
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
from scipy import sparse
from scipy.sparse.linalg import lsqr
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "oecd_tax_registration_family_forward_2026_10_10"
RUNNER = "scripts/run_oecd_tax_registration_family_2026.py"
PREREG = "engine/audits/oecd_tax_registration_family_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/oecd_tax_registration_family_2026_key_roster.csv"
ROSTER_SHA = "7f52d0b7316e08e79693ded46fc47d1006f614fd515e5147fb4f5f0509a9cc92"
LOCK = "data/pinned_evidence/oecd_tax_registration_family_2026.manifest.json"
SUMMARY = "engine/audits/oecd_tax_registration_family_results_2026-10-10.md"
TAX_MANIFEST = "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml"
TAX_MANIFEST_SHA = "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18"
WDI_MANIFEST = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
WDI_MANIFEST_SHA = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"
SOURCES = {
    "cit": {"publisher": "oecd", "series_id": "oecd_combined_corporate_income_tax_rate",
            "path": "data/vintages/oecd/oecd_combined_corporate_income_tax_rate@2026-07-23T153857Z.parquet",
            "sha256": "3e9c5987717087d04d5f82461fc1a3fb5e406ba646fb9f333f8c542e5f3f5ee1",
            "manifest": TAX_MANIFEST, "manifest_sha256": TAX_MANIFEST_SHA},
    "pit": {"publisher": "oecd", "series_id": "oecd_top_statutory_pit_rate",
            "path": "data/vintages/oecd/oecd_top_statutory_pit_rate@2026-07-23T153857Z.parquet",
            "sha256": "b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151",
            "manifest": TAX_MANIFEST, "manifest_sha256": TAX_MANIFEST_SHA},
    "outcome": {"publisher": "world_bank_wdi", "series_id": "IC.BUS.NREG",
            "path": "data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet",
            "sha256": "213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae",
            "manifest": WDI_MANIFEST, "manifest_sha256": WDI_MANIFEST_SHA},
}
CASES = {
    "cit": {"id": "oecd_cit_cut_business_registration_forward_2026",
            "label": "combined statutory corporate income-tax cut",
            "key_rows": 1691, "key_countries": 141,
            "key_cut_rows": 196, "key_cut_countries": 93,
            "key_hike_rows": 56, "key_hike_countries": 37,
            "preflight_top_row_share": 0.10466263681204271,
            "preflight_top_country_share": 0.022270124602218958,
            "floor": (700, 60, 70, 35, 20, 15)},
    "pit": {"id": "oecd_top_pit_cut_business_registration_forward_2026",
            "label": "top statutory personal income-tax cut",
            "key_rows": 454, "key_countries": 38,
            "key_cut_rows": 43, "key_cut_countries": 23,
            "key_hike_rows": 43, "key_hike_countries": 23,
            "preflight_top_row_share": 0.13580842561632808,
            "preflight_top_country_share": 0.07599381315520742,
            "floor": (250, 25, 20, 12, 15, 10)},
}
T_START, T_END, MIN_YEARS = 2007, 2018, 5
EVENT_THRESHOLD_PP = 1.0
FAMILY_ALPHA, P_MAX = 0.01, 0.005
MEANINGFUL_LOG_BETA = 0.05
MAX_TOP_ROW_SHARE, MAX_TOP_COUNTRY_SHARE = 0.30, 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "OECD statutory rates are not effective business or owner tax rates; top PIT measures high-bracket gross wage income and is a weak proxy for new corporations.",
    "WDI IC.BUS.NREG counts newly registered limited-liability firms, not active firms, sole proprietorships, jobs, or population-adjusted entry.",
    "Registry procedures, coverage, population growth, macro shocks, anticipation, and legal-form substitution may move registrations independently of tax changes.",
    "Country/year fixed effects and one-year temporal ordering do not identify tax-policy effects.",
    "The two-test Bonferroni correction is local to this prospectively registered family, not the visible IESET archive.",
    "No result receives causal, policy, school, or featured credit.",
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
    return f"hypotheses/fiscal/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(key: str, case: dict[str, Any]) -> dict[str, Any]:
    n, g, cut_n, cut_g, hike_n, hike_g = case["floor"]
    return {"family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
            "meaningful_beta_min_abs": MEANINGFUL_LOG_BETA,
            "min_valid_rows": n, "min_valid_countries": g,
            "min_cut_rows": cut_n, "min_cut_countries": cut_g,
            "min_hike_rows": hike_n, "min_hike_countries": hike_g,
            "min_years_per_country": MIN_YEARS,
            "max_top_one_percent_partialled_cut_share": MAX_TOP_ROW_SHARE,
            "max_top_country_partialled_cut_share": MAX_TOP_COUNTRY_SHARE,
            "expected_key_rows": case["key_rows"],
            "expected_key_countries": case["key_countries"],
            "expected_key_cut_rows": case["key_cut_rows"],
            "expected_key_cut_countries": case["key_cut_countries"],
            "expected_key_hike_rows": case["key_hike_rows"],
            "expected_key_hike_countries": case["key_hike_countries"],
            "roster_sha256": ROSTER_SHA,
            "source_files": {role: {f: source[f] for f in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role, source in (("treatment", SOURCES[key]), ("outcome", SOURCES["outcome"]))},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


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
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
                        "rows": entry.get("rows"), "frequency": entry.get("frequency"),
                        "units": entry.get("units")}
    return narrow


def load_roster() -> dict[str, list[tuple[str, int]]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"case_id,country_iso3,year\n"):
        raise RuntimeError("frozen key-roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    result = {key: [] for key in CASES}
    for record in records:
        if record["case_id"] not in result:
            raise RuntimeError("unexpected roster case")
        result[record["case_id"]].append((record["country_iso3"], int(record["year"])))
    observed = [(r["case_id"], r["country_iso3"], int(r["year"])) for r in records]
    expected = [(key, c, y) for key in CASES
                for c, y in sorted(result[key], key=lambda item: (item[1], item[0]))]
    if observed != expected or len(observed) != 2145 or len(set(observed)) != len(observed):
        raise RuntimeError("frozen roster ordering, size, or uniqueness mismatch")
    for key, case in CASES.items():
        rows = result[key]
        if len(rows) != case["key_rows"] or len({c for c, _ in rows}) != case["key_countries"]:
            raise RuntimeError(f"frozen roster envelope mismatch: {key}")
    return result


def source_keys() -> tuple[dict[str, dict[tuple[str, int], float]], set[tuple[str, int]]]:
    """Read selected OECD tax VALUES, but only WDI outcome keys and dimensions."""
    exposures = {}
    for key in CASES:
        frame = pd.read_parquet(ROOT / SOURCES[key]["path"], columns=["country_iso3", "year", "value"])
        if frame.duplicated(["country_iso3", "year"]).any() or not frame.country_iso3.str.fullmatch("[A-Z]{3}").all():
            raise RuntimeError(f"{key} OECD treatment keys are not unique country-year codes")
        if key == "cit" and len(frame) != 3640 or key == "pit" and len(frame) != 950:
            raise RuntimeError(f"{key} OECD tax row-count contract changed")
        rates = {(str(c), int(y)): float(v) for c, y, v in frame.itertuples(index=False, name=None)}
        invalid = [((c, y), v) for (c, y), v in rates.items() if not math.isfinite(v) or not 0 <= v <= 100]
        if (key == "cit" and invalid) or (key == "pit" and invalid != [(("FRA", 2013), 122.796992)]):
            raise RuntimeError(f"{key} tax validity contract changed: {invalid[:3]}")
        exposures[key] = rates
    outcome = pd.read_parquet(ROOT / SOURCES["outcome"]["path"],
                              columns=["country_iso3", "indicator_id", "year"])
    if len(outcome) != 17556 or not outcome.indicator_id.eq("IC.BUS.NREG").all():
        raise RuntimeError("WDI registration key/indicator contract changed")
    outcome = outcome.loc[outcome.country_iso3.fillna("").str.fullmatch("[A-Z]{3}")]
    if outcome.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("selected WDI ISO3 country-year key is duplicated")
    return exposures, {(str(c), int(y)) for c, y in outcome[["country_iso3", "year"]].itertuples(index=False, name=None)}


def partialled_cut_concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    """FWL residualize cut on country, year and the prespecified hike indicator."""
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    c = pd.Categorical(panel.country_iso3).codes
    y = pd.Categorical(panel.year).codes
    n, nc, ny = len(panel), int(c.max()) + 1, int(y.max()) + 1
    design = sparse.csr_matrix((np.ones(2 * n),
                                (np.r_[np.arange(n), np.arange(n)], np.r_[c, nc + y])),
                               shape=(n, nc + ny))
    design = sparse.hstack([design, sparse.csr_matrix(panel.hike.to_numpy(dtype=float)[:, None])], format="csr")
    fit = lsqr(design, panel.cut.to_numpy(dtype=float), atol=1e-13, btol=1e-13)
    residual = panel.cut.to_numpy(dtype=float) - design @ fit[0]
    squares = np.square(residual)
    total = float(squares.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * n))
    top_row_share = float(np.sort(squares)[-top_n:].sum() / total)
    grouped = pd.DataFrame({"country_iso3": panel.country_iso3.to_numpy(), "squared": squares})
    top_country_share = float(grouped.groupby("country_iso3").squared.sum().max() / total)
    return top_row_share, top_country_share


def key_preflight() -> dict[str, Any]:
    exposures, outcome_keys = source_keys()
    roster = load_roster()
    report = {"treatment_values_read": True, "outcome_values_read": False,
              "outcome_null_masks_read": False, "outcome_status_read": False,
              "exact_year_join": True, "roster_sha256": ROSTER_SHA, "cases": {}}
    for key, case in CASES.items():
        rates = exposures[key]
        candidates = []
        for (country, year), current in rates.items():
            if not (T_START <= year <= T_END and (country, year - 1) in rates
                    and (country, year) in outcome_keys and (country, year + 1) in outcome_keys):
                continue
            previous = rates[(country, year - 1)]
            if not (math.isfinite(current) and 0 <= current <= 100
                    and math.isfinite(previous) and 0 <= previous <= 100):
                continue
            change = current - previous
            candidates.append((country, year, int(change <= -EVENT_THRESHOLD_PP),
                               int(change >= EVENT_THRESHOLD_PP)))
        counts = Counter(c for c, _, _, _ in candidates)
        rows = sorted(((c, y, cut, hike) for c, y, cut, hike in candidates if counts[c] >= MIN_YEARS),
                      key=lambda item: (item[1], item[0]))
        selected = [(c, y) for c, y, _, _ in rows]
        if selected != roster[key]:
            raise RuntimeError(f"{key} outcome-key-only roster changed")
        frame = pd.DataFrame(rows, columns=["country_iso3", "year", "cut", "hike"])
        cut = frame.loc[frame.cut.eq(1)]
        hike = frame.loc[frame.hike.eq(1)]
        shares = partialled_cut_concentration(frame)
        if shares is None:
            raise RuntimeError(f"{key} has no partialled cut variation")
        if (len(frame) != case["key_rows"] or frame.country_iso3.nunique() != case["key_countries"]
                or len(cut) != case["key_cut_rows"] or cut.country_iso3.nunique() != case["key_cut_countries"]
                or len(hike) != case["key_hike_rows"] or hike.country_iso3.nunique() != case["key_hike_countries"]
                or not math.isclose(shares[0], case["preflight_top_row_share"], abs_tol=1e-9)
                or not math.isclose(shares[1], case["preflight_top_country_share"], abs_tol=1e-9)):
            raise RuntimeError(f"{key} frozen treatment-only envelope changed")
        report["cases"][key] = {"key_rows": len(frame), "key_countries": int(frame.country_iso3.nunique()),
                                "key_cut_rows": len(cut), "key_cut_countries": int(cut.country_iso3.nunique()),
                                "key_hike_rows": len(hike), "key_hike_countries": int(hike.country_iso3.nunique()),
                                "partialled_cut_top_one_percent_share": shares[0],
                                "partialled_cut_top_country_share": shares[1],
                                "t_years": [T_START, T_END]}
    return report


def lock_payload(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    revision = registration_commit()
    payload = lock_payload(revision, check_sources(), key_preflight())
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit it alone before reading WDI outcome values")


def check_source_lock(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, narrow, preflight):
        raise RuntimeError("source lock differs from preregistration, pins, or key preflight")
    commit = first_addition(LOCK)
    if commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, commit],
                                            cwd=ROOT).returncode:
        raise RuntimeError("source lock did not follow the registration commit")
    committed_unchanged(LOCK, commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return commit


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First WDI values, null-mask, and status access; chronology must already be checked."""
    exposures, _ = source_keys()
    frame = pd.read_parquet(ROOT / SOURCES["outcome"]["path"],
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    frame = frame.loc[frame.indicator_id.eq("IC.BUS.NREG")
                      & frame.country_iso3.fillna("").str.fullmatch("[A-Z]{3}")]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("selected WDI outcome keys duplicated")
    values = {}
    for c, y, value, status in frame[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None):
        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError):
            numeric = float("nan")
        values[(str(c), int(y))] = (numeric, "" if pd.isna(status) else str(status).strip())
    output = {}
    for key, case in CASES.items():
        rows = []
        dropped_invalid_or_missing = 0
        dropped_status = 0
        for country, year in roster[key]:
            old, old_status = values.get((country, year), (float("nan"), ""))
            new, new_status = values.get((country, year + 1), (float("nan"), ""))
            if not (math.isfinite(old) and old > 0 and math.isfinite(new) and new > 0):
                dropped_invalid_or_missing += 1
                continue
            if old_status or new_status:
                dropped_status += 1
                continue
            delta = exposures[key][(country, year)] - exposures[key][(country, year - 1)]
            rows.append({"country_iso3": country, "year": year,
                         "cut": int(delta <= -EVENT_THRESHOLD_PP),
                         "hike": int(delta >= EVENT_THRESHOLD_PP),
                         "registration_log_growth": math.log(new) - math.log(old)})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "cut", "hike", "registration_log_growth"])
        before = len(panel)
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        cut = panel.loc[panel.cut.eq(1)]
        hike = panel.loc[panel.hike.eq(1)]
        gate = {"roster_rows": len(roster[key]),
                "dropped_invalid_or_missing_endpoint_pairs": dropped_invalid_or_missing,
                "dropped_nonblank_wdi_status_pairs": dropped_status,
                "complete_pairs_before_five_year_country_floor": before,
                "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
                "cut_rows": len(cut), "cut_countries": int(cut.country_iso3.nunique()),
                "hike_rows": len(hike), "hike_countries": int(hike.country_iso3.nunique()),
                "stable_rows": int((panel.cut.eq(0) & panel.hike.eq(0)).sum()),
                "outcome_values_read_after_lock": True}
        output[key] = panel, gate
    return output


def estimate(panel: pd.DataFrame, gate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    min_n, min_g, min_cut_n, min_cut_g, min_hike_n, min_hike_g = case["floor"]
    if (gate["valid_rows"] < min_n or gate["valid_countries"] < min_g
            or gate["cut_rows"] < min_cut_n or gate["cut_countries"] < min_cut_g
            or gate["hike_rows"] < min_hike_n or gate["hike_countries"] < min_hike_g):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or cut/hike event floor failed", "primary": None}
    shares = partialled_cut_concentration(panel)
    if shares is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "no finite cut variation after fixed effects and hike indicator", "primary": None}
    gate["top_one_percent_partialled_cut_share"], gate["top_country_partialled_cut_share"] = shares
    if shares[0] > MAX_TOP_ROW_SHARE or shares[1] > MAX_TOP_COUNTRY_SHARE:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen partialled-cut concentration gate failed", "primary": None}
    model = smf.ols("registration_log_growth ~ cut + hike + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed-effect design lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["cut"]), float(fit.bse["cut"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive clustered uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(0.9975, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite country-cluster inference", "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.995,
               "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
               "model_rank": int(fit.model.rank),
               "hike_coefficient_nuisance": float(fit.params["hike"]),
               "method": "country/year FE OLS with cut and hike indicators; country-cluster CR1; Student t(G-1)"}
    if beta >= MEANINGFUL_LOG_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive cut association clears frozen magnitude and Bonferroni cutoff"
    elif beta <= -MEANINGFUL_LOG_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite cut association clears frozen magnitude and Bonferroni cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable cut association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any],
                     registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict, gate, primary = case["id"], result["verdict"], result["gate"], result["primary"]
    inputs = {role: SOURCES[role] for role in (key, "outcome")}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": "fiscal"},
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
                   "run_utc": stamp, "runner": RUNNER,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
                   "primary": primary, "p_max_two_sided_bonferroni": P_MAX,
                   "meaningful_beta_min_abs": MEANINGFUL_LOG_BETA,
                   "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source-lock commit: `{lock_commit}`.\n\n"
            f"Key-only upper bound: {case['key_rows']} country-years / {case['key_countries']} countries. "
            f"Complete pairs: {gate['valid_rows']} / {gate['valid_countries']}; cut years: "
            f"{gate['cut_rows']} / {gate['cut_countries']}; hike years: "
            f"{gate['hike_rows']} / {gate['hike_countries']}.\n")
    if primary is not None:
        card += (f"\nPrimary cut beta={primary['coefficient']:+.6g} log points versus tax-stable years, "
                 f"country-cluster SE={primary['std_error']:.6g}, two-sided t p={primary['p_value_two_sided']:.6g}, "
                 f"99.5% CI={primary['confidence_interval']}. Hike coefficient is nuisance only.\n")
    card += ("\nTwo prespecified tests; Bonferroni family alpha 0.01, each two-sided p≤0.005; "
             "cut beta magnitude ≥0.05 log point is also required. Descriptive calibration only. "
             "No causal, policy, school, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = [{"term": "cut", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# OECD statutory tax cuts and next-year registration growth: two-test result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "Both tests stay in one Bonferroni family (alpha 0.01; each two-sided p≤0.005).",
             "", "| Treatment | Verdict | Complete pairs / countries | Cut years / countries | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['cut_rows']} / {gate['cut_countries']} | {beta} | {p} |")
    lines += ["", "The coefficient is the difference in next-year log registration growth between tax-cut and tax-stable years, with hike, country and year indicators in the model. Large valid tax reforms remain included. These associations are not tax-policy effects.",
              "", "The local two-test correction does not adjust for the visible older tax and entry archive. No causal, policy, school, or featured credit.", ""]
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
        cols = ["term", "coefficient", "std_error", "p_value_two_sided", "confidence_level",
                "confidence_interval", "n_rows", "n_countries", "df_inference", "model_rank",
                "hike_coefficient_nuisance", "method"]
        pd.DataFrame(payload["coefficients"], columns=cols).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for key, case in CASES.items():
        folder = ROOT / run_rel(case)
        packet = yaml.safe_load((folder / "evidence_packet.yaml").read_text())
        diag = json.loads((folder / "diagnostics.json").read_text())
        if (packet["preregistration"]["spec_commit"] != registration
                or packet["preregistration"]["source_lock_commit"] != lock_commit
                or packet["verdict"]["raw"] != results[key]["verdict"]
                or diag["verdict"] != results[key]["verdict"]
                or diag["preflight"] != results[key]["gate"]):
            raise AssertionError(f"{key} frozen result metadata differs from replay")
        current = results[key]["primary"]
        saved = diag["primary"]
        if (current is None) != (saved is None):
            raise AssertionError(f"{key} frozen primary availability differs")
        if current is not None:
            for field in ("coefficient", "std_error", "p_value_two_sided", "hike_coefficient_nuisance"):
                if not math.isclose(current[field], saved[field], rel_tol=1e-10, abs_tol=1e-12):
                    raise AssertionError(f"{key} primary {field} differs")
        if (folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes():
            raise AssertionError(f"{key} frozen hypothesis copy differs")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from replay")
    print("verified two preregistered tax-registration results")


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
    registration = registration_commit()
    narrow, preflight = check_sources(), key_preflight()
    lock_commit = check_source_lock(registration, narrow, preflight)
    panels = measured_panels(load_roster())
    results = {key: estimate(*panels[key], CASES[key]) for key in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        for key, result in results.items():
            print(key, result["verdict"], result["gate"])
    else:
        verify_artifacts(results, registration, lock_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
