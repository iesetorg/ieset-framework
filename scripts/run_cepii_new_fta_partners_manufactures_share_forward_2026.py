#!/usr/bin/env python3
"""Frozen CEPII FTA-partner expansion to WDI manufactures-share study.

--preflight reads treatment values and WDI selector/country/year keys only.
--lock requires a committed preregistration and writes a narrow source lock.
--run and --verify read selected WDI values only after that lock is committed.
No mode projects WDI observation status.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
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
ID = "cepii_new_fta_partners_manufactures_share_forward_2026"
FAMILY = ID + "_10_10"
RUNNER = f"scripts/run_{ID}.py"
SPEC = f"hypotheses/trade/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PREREG = "engine/audits/cepii_new_fta_partners_manufactures_share_prereg_2026-10-10.md"
TESTS = f"tests/test_{ID}.py"
ROSTER = f"data/pinned_evidence/{ID}_key_roster.csv"
ROSTER_SHA = "1f8d1b6c7a92ffcb3ffcdf226b3cf98fbf44f1bd8c5d6d3ee0f5027325ff82cf"
LOCK = f"data/pinned_evidence/{ID}.manifest.json"
RUN_DIR = f"engine/runs/{ID}"
SUMMARY = "engine/audits/cepii_new_fta_partners_manufactures_share_results_2026-10-10.md"
ALLOWLIST_SHA = "cc306b7deb4ff39f16097111f5a48412bc49e268a7fa5dfc42a9c9427adf0e6b"
RAW_ZIP = {
    "path": "data/raw/cepii/Gravity_csv_V202211.zip",
    "sha256": "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1",
}
SOURCES = {
    "treatment": {
        "publisher": "cepii", "series_id": "gravity_new_fta_partner_count",
        "path": "data/vintages/cepii/gravity_new_fta_partner_count@2026-05-15T175027Z.parquet",
        "sha256": "1120bf0082c64bd79b4bce2b011e7fe524b814ce821eff5bea5e976af379a53b",
        "manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
        "manifest_sha256": "5922b10683ebf977d4f45b994cd4196cde4e0845540a6e69adb727be91229a46",
    },
    "outcome": {
        "publisher": "world_bank_wdi", "series_id": "TX.VAL.MANF.ZS.UN",
        "path": "data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet",
        "sha256": "c5077c18a1ba1b953bc1cd66ac980f36b5cda7568fc3749126b91587cf17c98b",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e",
    },
}
T_START, T_END, MIN_YEARS = 1995, 2018, 5
P_MAX, MEANINGFUL_BETA = 0.005, 0.5  # WDI percentage points
MIN_ROWS, MIN_COUNTRIES = 1000, 70
MIN_EVENT_ROWS, MIN_EVENT_COUNTRIES, MIN_EVENT_YEARS = 150, 50, 15
MIN_CONTROL_ROWS, MIN_CONTROL_COUNTRIES = 500, 70
MAX_TOP_1PCT, MAX_COUNTRY, MAX_YEAR = 0.15, 0.05, 0.15
EXPECTED = {
    "key_rows": 5028, "key_countries": 212,
    "event_rows": 1013, "event_countries": 166, "event_years": 24,
    "top_one_percent_share": 0.08708762510978722,
    "top_country_share": 0.01267537367622035,
    "top_year_share": 0.07677526062852089,
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
    "CEPII new-FTA-partner count is the positive part of a year-over-year change in coded active fta_wto partner count; it is not a count of newly signed treaties or tariff cuts.",
    "Partner coverage and coding can change without a policy shock, and several countries can share one regional agreement event.",
    "Manufactures share is a composition of merchandise exports; commodity prices and nonmanufactures exports can move its denominator.",
    "Selection into agreements, exchange rates, global demand, industrial policy and country-specific trends can confound the association.",
    "The baseline share is both the subtraction endpoint and a covariate; this does not remove regression-to-the-mean or starting-composition concerns.",
    "Related CEPII FTA to high-tech/WITS studies and a PDB to the same WDI outcome are visible; the 0.005 cutoff does not correct archive-wide selection.",
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
        "p_max_two_sided": P_MAX, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_YEARS,
        "min_event_rows": MIN_EVENT_ROWS,
        "min_event_countries": MIN_EVENT_COUNTRIES,
        "min_event_years": MIN_EVENT_YEARS,
        "min_control_rows": MIN_CONTROL_ROWS,
        "min_control_countries": MIN_CONTROL_COUNTRIES,
        "max_top_one_percent_partialled_event_share": MAX_TOP_1PCT,
        "max_top_country_partialled_event_share": MAX_COUNTRY,
        "max_top_year_partialled_event_share": MAX_YEAR,
        "expected_key_rows": EXPECTED["key_rows"],
        "expected_key_countries": EXPECTED["key_countries"],
        "expected_key_event_rows": EXPECTED["event_rows"],
        "expected_key_event_countries": EXPECTED["event_countries"],
        "expected_key_event_years": EXPECTED["event_years"],
        "roster_sha256": ROSTER_SHA,
        "iso3_allowlist_sha256": ALLOWLIST_SHA,
        "source_files": {
            "treatment": {name: SOURCES["treatment"][name] for name in
                          ("path", "sha256", "manifest", "manifest_sha256")},
            "outcome": {name: SOURCES["outcome"][name] for name in
                        ("path", "sha256", "manifest", "manifest_sha256")},
            "raw_zip": RAW_ZIP,
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
            or spec["claim_direction"] != "+" or spec["evidence_type"] != "associational"
            or spec["steelman"] != STEELMAN
            or spec["sample"]["countries"] != ["GLOBAL"]
            or spec["sample"]["period"] != [T_START, T_END]
            or spec["falsification"]["threshold"] != threshold()
            or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
            or spec["linked_conditions"] != []):
        raise RuntimeError("frozen specification differs from runner contract")
    for forbidden in (LOCK, RUN_DIR, SUMMARY):
        if git("ls-tree", "-r", "--name-only", revision, "--", forbidden).strip():
            raise RuntimeError(f"registration commit contains postregistration artifact: {forbidden}")
    return revision


def check_sources() -> dict[str, Any]:
    if sha256(ROOT / RAW_ZIP["path"]) != RAW_ZIP["sha256"]:
        raise RuntimeError("CEPII raw Gravity ZIP SHA-256 mismatch")
    narrow: dict[str, Any] = {"raw_zip": dict(RAW_ZIP)}
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} Parquet SHA-256 mismatch")
        manifest_path = ROOT / source["manifest"]
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch")
        manifest = yaml.safe_load(manifest_path.read_text())
        matches = [row for row in manifest.get("entries", [])
                   if row.get("publisher") == source["publisher"]
                   and row.get("series_id") == source["series_id"]
                   and row.get("parquet_path") == source["path"]
                   and row.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"{role} source entry missing or ambiguous")
        row = matches[0]
        if role == "treatment" and row.get("extra", {}).get("source_zip_sha256") != RAW_ZIP["sha256"]:
            raise RuntimeError("CEPII derived series lacks pinned raw ZIP custody")
        narrow[role] = {
            **source, "source_url": row.get("source_url"),
            "fetch_utc": row.get("fetch_utc"), "license": row.get("license"),
            "rows": row.get("rows"), "frequency": row.get("frequency"),
            "units": row.get("units"),
        }
    return narrow


def current_iso3() -> set[str]:
    if pycountry.__version__ != "24.6.1":
        raise RuntimeError("pycountry allowlist version changed")
    allowed = {country.alpha_3 for country in pycountry.countries}
    digest = hashlib.sha256(("\n".join(sorted(allowed)) + "\n").encode()).hexdigest()
    if digest != ALLOWLIST_SHA:
        raise RuntimeError("current-country ISO3 allowlist changed")
    return allowed


def load_roster() -> list[tuple[str, int, int, int]]:
    raw = (ROOT / ROSTER).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROSTER_SHA:
        raise RuntimeError("fixed key-roster SHA-256 mismatch")
    if not raw.startswith(b"country_iso3,year,new_fta_partner_count,event\n"):
        raise RuntimeError("fixed key-roster header mismatch")
    reader = csv.DictReader(io.StringIO(raw.decode()))
    rows = [(row["country_iso3"], int(row["year"]),
             int(row["new_fta_partner_count"]), int(row["event"])) for row in reader]
    if (len(rows) != EXPECTED["key_rows"]
            or len({(c, y) for c, y, _, _ in rows}) != len(rows)
            or rows != sorted(rows, key=lambda row: (row[0], row[1]))
            or any(v < 0 or e != int(v >= 1) for _, _, v, e in rows)):
        raise RuntimeError("fixed roster shape, order, or event coding changed")
    return rows


def source_keys() -> tuple[dict[tuple[str, int], int], set[tuple[str, int]]]:
    """Project only CEPII treatment values and WDI indicator/country/year keys."""
    allowed = current_iso3()
    treatment = pd.read_parquet(ROOT / SOURCES["treatment"]["path"],
                                columns=["country_iso3", "year", "value"])
    if (len(treatment) != 16366 or treatment.duplicated(["country_iso3", "year"]).any()
            or treatment.value.isna().any()):
        raise RuntimeError("CEPII treatment source envelope changed")
    if not all(isinstance(v, (int, np.integer)) and v >= 0 for v in treatment.value):
        raise RuntimeError("CEPII treatment count contract changed")
    values = {(str(c), int(y)): int(v)
              for c, y, v in treatment.itertuples(index=False, name=None)}
    # This is the complete WDI outcome projection before the source lock.
    # Never add value, obs_status, or a selected-value null-mask operation here.
    keys_frame = pd.read_parquet(ROOT / SOURCES["outcome"]["path"],
                                 columns=["country_iso3", "indicator_id", "year"])
    if len(keys_frame) != 17556:
        raise RuntimeError("WDI outcome key envelope changed")
    keys_frame = keys_frame.loc[
        keys_frame.country_iso3.isin(allowed)
        & keys_frame.indicator_id.eq(SOURCES["outcome"]["series_id"]),
        ["country_iso3", "year"],
    ]
    if (len(keys_frame) != 14190
            or keys_frame.duplicated(["country_iso3", "year"]).any()):
        raise RuntimeError("WDI current-country selected keys changed or duplicated")
    keys = {(str(c), int(y)) for c, y in keys_frame.itertuples(index=False, name=None)}
    return values, keys


def signal_concentration(panel: pd.DataFrame, controls: np.ndarray) -> dict[str, float] | None:
    """Squared partialled event signal; controls exclude the event column."""
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    event = panel.event.to_numpy(dtype=float)
    residual = event - controls @ np.linalg.lstsq(controls, event, rcond=None)[0]
    squared = np.square(residual)
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(len(panel) * 0.01))
    labels = pd.DataFrame({"country": panel.country_iso3.to_numpy(),
                           "year": panel.year.to_numpy(), "signal": squared})
    return {
        "top_one_percent_share": float(np.sort(squared)[-top_n:].sum() / total),
        "top_country_share": float(labels.groupby("country").signal.sum().max() / total),
        "top_year_share": float(labels.groupby("year").signal.sum().max() / total),
    }


def key_preflight() -> dict[str, Any]:
    treatment, outcome_keys = source_keys()
    allowed = current_iso3()
    rows = sorted((c, y, v, int(v >= 1)) for (c, y), v in treatment.items()
                  if c in allowed and T_START <= y <= T_END
                  and (c, y - 1) in outcome_keys and (c, y + 2) in outcome_keys)
    if rows != load_roster():
        raise RuntimeError("key-only roster no longer matches source keys and treatment values")
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "new_fta_partner_count", "event"])
    events = panel.loc[panel.event.eq(1)]
    controls = np.column_stack([
        np.ones(len(panel)),
        pd.get_dummies(panel.country_iso3, drop_first=True, dtype=float).to_numpy(),
        pd.get_dummies(panel.year, drop_first=True, dtype=float).to_numpy(),
    ])
    shares = signal_concentration(panel, controls)
    if shares is None:
        raise RuntimeError("no treatment signal after key-only fixed effects")
    if (len(panel) != EXPECTED["key_rows"]
            or panel.country_iso3.nunique() != EXPECTED["key_countries"]
            or len(events) != EXPECTED["event_rows"]
            or events.country_iso3.nunique() != EXPECTED["event_countries"]
            or events.year.nunique() != EXPECTED["event_years"]
            or any(not math.isclose(shares[name], EXPECTED[name], abs_tol=1e-8)
                   for name in ("top_one_percent_share", "top_country_share", "top_year_share"))):
        raise RuntimeError("frozen exposure-only envelope changed")
    return {
        "treatment_values_read": True, "outcome_values_read": False,
        "outcome_null_masks_read": False, "outcome_status_read": False,
        "outcome_selector_and_keys_only": True,
        "treatment_years": [T_START, T_END],
        "roster_sha256": ROSTER_SHA, "key_rows": len(panel),
        "key_countries": int(panel.country_iso3.nunique()),
        "event_rows": len(events),
        "event_countries": int(events.country_iso3.nunique()),
        "event_years": int(events.year.nunique()),
        "control_rows": int(panel.event.eq(0).sum()),
        "partialled_event_country_year_only": shares,
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
    print(f"wrote {LOCK}; commit separately before opening WDI outcome values")


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


def measured_panel(roster: list[tuple[str, int, int, int]],
                   lock_commit: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """First access to selected WDI values, guarded by committed source lock."""
    if first_addition(LOCK) != lock_commit:
        raise RuntimeError("committed source lock required before WDI measurement")
    allowed = current_iso3()
    frame = pd.read_parquet(ROOT / SOURCES["outcome"]["path"],
                            columns=["country_iso3", "indicator_id", "year", "value"])
    frame = frame.loc[frame.country_iso3.isin(allowed)
                      & frame.indicator_id.eq(SOURCES["outcome"]["series_id"]),
                      ["country_iso3", "year", "value"]].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("selected WDI outcome keys duplicated")
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    values = {(str(c), int(y)): float(v)
              for c, y, v in frame.itertuples(index=False, name=None)}
    rows = []
    missing_or_invalid = 0
    for country, year, new_count, event in roster:
        baseline = values.get((country, year - 1), float("nan"))
        future = values.get((country, year + 2), float("nan"))
        if not (math.isfinite(baseline) and 0 <= baseline <= 100
                and math.isfinite(future) and 0 <= future <= 100):
            missing_or_invalid += 1
            continue
        rows.append({
            "country_iso3": country, "year": year,
            "new_fta_partner_count": new_count, "event": event,
            "baseline_share": baseline,
            "share_forward_change": future - baseline,
        })
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "new_fta_partner_count",
                                        "event", "baseline_share", "share_forward_change"])
    before = len(panel)
    country_n = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(country_n).ge(MIN_YEARS)].copy()
    events, controls = panel.loc[panel.event.eq(1)], panel.loc[panel.event.eq(0)]
    gate = {
        "roster_rows": len(roster),
        "dropped_missing_or_invalid_endpoint_pairs": missing_or_invalid,
        "complete_pairs_before_five_year_country_floor": before,
        "dropped_by_five_year_country_floor": before - len(panel),
        "valid_rows": len(panel),
        "valid_countries": int(panel.country_iso3.nunique()),
        "event_rows": len(events), "event_countries": int(events.country_iso3.nunique()),
        "event_years": int(events.year.nunique()),
        "control_rows": len(controls), "control_countries": int(controls.country_iso3.nunique()),
        "outcome_values_read_after_lock": True, "outcome_status_read": False,
    }
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES
            or gate["event_rows"] < MIN_EVENT_ROWS
            or gate["event_countries"] < MIN_EVENT_COUNTRIES
            or gate["event_years"] < MIN_EVENT_YEARS
            or gate["control_rows"] < MIN_CONTROL_ROWS
            or gate["control_countries"] < MIN_CONTROL_COUNTRIES):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or event/control floor failed", "primary": None}
    model = smf.ols("share_forward_change ~ event + baseline_share + C(country_iso3) + C(year)",
                    data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed-effect model lacks full rank", "primary": None}
    event_index = model.exog_names.index("event")
    controls = np.delete(model.exog, event_index, axis=1)
    shares = signal_concentration(panel, controls)
    gate["partialled_event_full_model"] = shares
    if (shares is None or shares["top_one_percent_share"] > MAX_TOP_1PCT
            or shares["top_country_share"] > MAX_COUNTRY
            or shares["top_year_share"] > MAX_YEAR):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "full-model partialled-event concentration gate failed", "primary": None}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={
        "groups": panel.country_iso3, "use_correction": True,
        "df_correction": True,
    }, use_t=True)
    beta, se = float(fit.params["event"]), float(fit.bse["event"])
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
        "baseline_share_coefficient_nuisance": float(fit.params["baseline_share"]),
        "method": "country/year FE OLS; baseline t-1 share; country-cluster CR1; Student t(G-1)",
    }
    if beta >= MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive event association clears frozen magnitude and p cutoff"
    elif beta <= -MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "negative event association clears frozen magnitude and p cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable event association does not clear both directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def summary_text(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = "not estimated" if primary is None else f"{primary['coefficient']:+.6g}"
    p = "not estimated" if primary is None else f"{primary['p_value_two_sided']:.6g}"
    return (
        "# CEPII FTA-partner expansion and manufactures export share\n\n"
        f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
        f"**{result['verdict']}** — {result['reason']}.\n\n"
        f"Key-only upper bound: {EXPECTED['key_rows']} country-years / {EXPECTED['key_countries']} countries. "
        f"Complete pairs: {gate['valid_rows']} / {gate['valid_countries']}; "
        f"event years: {gate['event_rows']} / {gate['event_countries']} countries / "
        f"{gate['event_years']} calendar years.\n\n"
        f"Event coefficient: {beta} percentage points; two-sided country-cluster t p: {p}. "
        "A directional verdict requires |beta| >= 0.5 percentage points and p <= 0.005. "
        "This one-test cutoff does not correct the visible archive-wide search. "
        "No causal, policy, school, position, or featured credit.\n"
    )


def artifacts(result: dict[str, Any], registration: str,
              lock_commit: str, stamp: str) -> dict[str, Any]:
    gate, primary = result["gate"], result["primary"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC, "topic": "trade"},
        "preregistration": {
            "spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": 1,
            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
            "steelman": STEELMAN,
        },
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                    "reason": result["reason"]},
        "data": {"inputs": SOURCES, "raw_source": RAW_ZIP, "sample": gate},
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
        "vintages": list(SOURCES.values()), "raw_source": RAW_ZIP,
        "derived_panel": gate, "correction": CORRECTION,
    }
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\n"
        "import subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    chart = {"hypothesis_id": ID, "family_id": FAMILY,
             "verdict": result["verdict"], "primary": primary}
    coefficients = [{"term": "event", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


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
    columns = ["term", "coefficient", "std_error", "p_value_two_sided",
               "confidence_level", "confidence_interval", "n_rows", "n_countries",
               "df_inference", "model_rank", "baseline_share_coefficient_nuisance", "method"]
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
        if not isinstance(actual, list):
            raise AssertionError(f"{label} is not a list")
        if len(actual) != len(expected):
            raise AssertionError(f"{label} list length differs")
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
    replay_equal(yaml.safe_load((folder / "evidence_packet.yaml").read_text()),
                 expected["packet"], "evidence_packet")
    replay_equal(yaml.safe_load((folder / "manifest.yaml").read_text()),
                 expected["manifest"], "manifest")
    replay_equal(json.loads((folder / "chart_data.json").read_text()),
                 expected["chart"], "chart_data")
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
    print("verified full preregistered CEPII to WDI artifact set")


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
