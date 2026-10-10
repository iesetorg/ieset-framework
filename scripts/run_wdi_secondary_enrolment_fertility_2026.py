#!/usr/bin/env python3
"""Frozen descriptive secondary-enrolment to fertility decade test.

Before the registration and later source-lock commits, preflight reads schooling
and GDP values but only fertility country-year keys. Fertility values and their
missingness are first read by --run/--verify after both chronology checks.
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
HID = "wdi_secondary_enrolment_fertility_decade_followthrough_2026"
FAMILY = "wdi_secondary_enrolment_fertility_2026_10_10"
RUNNER = "scripts/run_wdi_secondary_enrolment_fertility_2026.py"
SPEC = f"hypotheses/labour/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PREREG = "engine/audits/wdi_secondary_enrolment_fertility_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_secondary_enrolment_fertility_2026_key_roster.csv"
ROSTER_SHA = "ceefc2f69f90551e07fa336260778c11f75ff2a6e7bb1a46725fba8529b45e2c"
LOCK = "data/pinned_evidence/wdi_secondary_enrolment_fertility_2026.manifest.json"
SUMMARY = "engine/audits/wdi_secondary_enrolment_fertility_results_2026-10-10.md"
RUN_DIR = f"engine/runs/{HID}"
SOURCES = {
    "schooling": {"publisher": "world_bank_wdi", "series_id": "SE.SEC.ENRR",
        "path": "data/vintages/world_bank_wdi/SE.SEC.ENRR@2026-05-05T204008Z.parquet",
        "sha256": "787f29eb93204dbf11dd408449910c28b523376c054734f1fc68d4215b7b2044",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "fertility": {"publisher": "world_bank_wdi", "series_id": "SP.DYN.TFRT.IN",
        "path": "data/vintages/world_bank_wdi/SP.DYN.TFRT.IN@2026-04-30T130516Z.parquet",
        "sha256": "ff1eb90d4033e42ca63bb0de72c27f21044e55b69e44568d65321dd81cd8cfd1",
        "manifest": "data/manifests/fetch_run_2026-04-30T130536Z.yaml",
        "manifest_sha256": "ab56887949d3a51f3e3001ac1065c62538af1db4d4a722e39e29a774447f511b"},
    "income": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
}
ANCHORS = (1990, 2000, 2010)
CANDIDATE_ROWS, CANDIDATE_COUNTRIES = 168, 72
MATERIAL_ROWS, MATERIAL_COUNTRIES = 85, 57
MIN_ROWS, MIN_COUNTRIES = 140, 60
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 65, 45
MATERIAL_CHANGE = 5.0
MAX_ENROLMENT, MAX_CHANGE = 150.0, 40.0
MIN_FERTILITY, MAX_FERTILITY = 0.5, 10.0
ALPHA, MIN_ABS_BETA = 0.01, 0.003
MAX_TOP_ONE_PERCENT, MAX_TOP_COUNTRY = 0.30, 0.20
ISO3 = frozenset(country.alpha_3 for country in pycountry.countries)
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": ALPHA, "family_p_max": ALPHA,
    "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "Gross secondary enrolment includes both sexes, counts over-age and under-age pupils, and can exceed 100%; it is not female completion or a policy treatment.",
    "WDI total fertility is a national births-per-woman estimate from multiple demographic sources; within-country method continuity cannot be certified by this pinned file.",
    "The pinned WDI files carry blank observation-status cells, so there is no source-provided break flag for country-year exclusions.",
    "Schooling and fertility both follow development transitions. Baseline fertility, real income, country and anchor fixed effects do not resolve confounding, migration, family-policy changes, or reverse timing.",
    "Three disjoint ten-year outcome windows use 1985-2010 schooling exposure years and 1990-2020 fertility endpoints. The key roster is an upper bound; fertility values and nulls were sealed during selection.",
    "Prior IESET education, fertility, labour, and development cases make archive-wide selection relevant; this single-test 0.01 rule is only local.",
    "No causal, policy, school-score, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def threshold() -> dict[str, Any]:
    return {"family_id": FAMILY, "family_size": 1, "family_alpha": ALPHA,
        "p_max_two_sided": ALPHA, "expected_beta_sign": "-",
        "meaningful_beta_min_abs": MIN_ABS_BETA,
        "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_COUNTRIES,
        "min_material_change_rows": MIN_MATERIAL_ROWS,
        "min_material_change_countries": MIN_MATERIAL_COUNTRIES,
        "material_enrolment_change_min_abs": MATERIAL_CHANGE,
        "max_enrolment_level": MAX_ENROLMENT, "max_abs_enrolment_change": MAX_CHANGE,
        "fertility_value_range": [MIN_FERTILITY, MAX_FERTILITY],
        "min_complete_anchors_per_country": 2,
        "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT,
        "max_top_country_residual_x_share": MAX_TOP_COUNTRY,
        "expected_key_rows": CANDIDATE_ROWS, "expected_key_countries": CANDIDATE_COUNTRIES,
        "roster_sha256": ROSTER_SHA,
        "source_files": {role: {field: source[field] for field in
            ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()},
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False}


def validate_spec() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    roster = load_roster()
    countries = sorted({country for country, _ in roster})
    if (spec.get("hypothesis_id") != HID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational"
            or spec.get("claim_direction") != "-"
            or spec.get("steelman") != STEELMAN
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or spec["sample"].get("countries") != countries
            or spec["sample"].get("period") != [1990, 2020]
            or spec["falsification"].get("threshold") != threshold()):
        raise RuntimeError("frozen hypothesis specification differs from runner")


def registration_commit() -> str:
    files = [SPEC, STEELMAN, PREREG, ROSTER, RUNNER]
    revisions = {first_addition(relative) for relative in files}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise RuntimeError("registration commit already contained measured artifacts")
    validate_spec()
    return revision


def check_sources() -> dict[str, dict[str, Any]]:
    selected = {}
    for role, source in SOURCES.items():
        raw = ROOT / source["path"]
        manifest_path = ROOT / source["manifest"]
        if not raw.is_file() or sha256(raw) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned raw source: {role}")
        if not manifest_path.is_file() or sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest_path.read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("publisher") == source["publisher"]
            and entry.get("series_id") == source["series_id"]
            and entry.get("parquet_path") == source["path"]
            and entry.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest lacks exact pinned source entry: {role}")
        selected[role] = {**source, "source_url": matches[0].get("source_url"),
            "methodology_url": matches[0].get("methodology_url"),
            "license": matches[0].get("license"), "fetch_utc": matches[0].get("fetch_utc")}
    return selected


def read_key_frame(role: str, with_value: bool) -> pd.DataFrame:
    columns = ["country_iso3", "year"] + (["value"] if with_value else [])
    frame = pd.read_parquet(ROOT / SOURCES[role]["path"], columns=columns)
    frame = frame.loc[frame.country_iso3.isin(ISO3), columns].copy()
    frame["year"] = frame.year.astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate selected country-year keys: {role}")
    if with_value:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def expected_roster() -> list[tuple[str, int]]:
    # Outcome country-year keys only: do not read the fertility value or its null mask.
    fertility_keys = set(read_key_frame("fertility", False).set_index(["country_iso3", "year"]).index)
    schooling = read_key_frame("schooling", True).set_index(["country_iso3", "year"]).value
    income = read_key_frame("income", True).set_index(["country_iso3", "year"]).value
    rows = []
    for anchor in ANCHORS:
        for country in sorted(ISO3):
            keys = ((country, anchor - 5), (country, anchor))
            if (keys[0] not in schooling or keys[1] not in schooling
                    or keys[1] not in income or keys[1] not in fertility_keys
                    or (country, anchor + 10) not in fertility_keys):
                continue
            before, at, gdp = (float(schooling[keys[0]]), float(schooling[keys[1]]),
                               float(income[keys[1]]))
            if not (math.isfinite(before) and math.isfinite(at) and math.isfinite(gdp)
                    and 0 <= before <= MAX_ENROLMENT and 0 <= at <= MAX_ENROLMENT
                    and abs(at - before) <= MAX_CHANGE and gdp > 0):
                continue
            rows.append((country, anchor))
    counts = pd.Series([country for country, _ in rows]).value_counts()
    return sorted((country, anchor) for country, anchor in rows if counts[country] >= 2)


def load_roster() -> list[tuple[str, int]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"country_iso3,anchor_year\n"):
        raise RuntimeError("key-only roster header/hash mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    rows = [(record["country_iso3"], int(record["anchor_year"])) for record in records]
    if (rows != sorted(set(rows)) or len(rows) != CANDIDATE_ROWS
            or len({country for country, _ in rows}) != CANDIDATE_COUNTRIES
            or any(year not in ANCHORS for _, year in rows)):
        raise RuntimeError("key-only roster shape or ordering changed")
    return rows


def preflight() -> dict[str, Any]:
    roster = load_roster()
    if expected_roster() != roster:
        raise RuntimeError("frozen roster differs from treatment/control values and outcome keys")
    schooling = read_key_frame("schooling", True).set_index(["country_iso3", "year"]).value
    changes = [(country, float(schooling[country, anchor]) - float(schooling[country, anchor - 5]))
               for country, anchor in roster]
    material = [(country, change) for country, change in changes if abs(change) >= MATERIAL_CHANGE]
    if len(material) != MATERIAL_ROWS or len({country for country, _ in material}) != MATERIAL_COUNTRIES:
        raise RuntimeError("registered treatment-only material envelope changed")
    return {"key_only_rows": len(roster), "key_only_countries": CANDIDATE_COUNTRIES,
        "material_treatment_rows": len(material), "material_treatment_countries": MATERIAL_COUNTRIES,
        "anchor_years": list(ANCHORS), "outcome_values_opened": False,
        "outcome_null_masks_opened": False,
        "note": "Fertility source has a full country-year key grid; these are upper bounds, not complete cases."}


def lock_payload(registration: str, selected: dict[str, dict[str, Any]],
                 blind: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
        "sources": selected, "key_only_preflight": blind,
        "statement": "Source SHA pins and exact manifest entries locked after preregistration; fertility values and nulls still unopened."}


def write_source_lock() -> None:
    registration = registration_commit()
    selected = check_sources()
    blind = preflight()
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, selected, blind), indent=2, sort_keys=True) + "\n")


def check_source_lock(registration: str, selected: dict[str, dict[str, Any]],
                      blind: dict[str, Any]) -> str:
    lock_commit = first_addition(LOCK)
    if lock_commit == registration:
        raise RuntimeError("source lock must have a separate later commit")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", registration, lock_commit], cwd=ROOT)
    committed_unchanged(LOCK, lock_commit)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, selected, blind):
        raise RuntimeError("committed source lock differs from frozen source pins")
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_DIR).strip():
        raise RuntimeError("source-lock commit already contained measured artifacts")
    return lock_commit


def measured_panel(roster: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    # This is the first selected outcome-value/null access, after both commits.
    outcome = read_key_frame("fertility", True).set_index(["country_iso3", "year"]).value
    schooling = read_key_frame("schooling", True).set_index(["country_iso3", "year"]).value
    income = read_key_frame("income", True).set_index(["country_iso3", "year"]).value
    rows = []
    invalid_pairs = 0
    for country, anchor in roster:
        base, future = float(outcome[country, anchor]), float(outcome[country, anchor + 10])
        if not (math.isfinite(base) and math.isfinite(future)
                and MIN_FERTILITY <= base <= MAX_FERTILITY
                and MIN_FERTILITY <= future <= MAX_FERTILITY):
            invalid_pairs += 1
            continue
        rows.append({"country_iso3": country, "anchor_year": anchor,
            "x": float(schooling[country, anchor]) - float(schooling[country, anchor - 5]),
            "log_gdp": math.log(float(income[country, anchor])),
            "log_baseline_fertility": math.log(base),
            "y": math.log(future / base)})
    panel = pd.DataFrame(rows, columns=["country_iso3", "anchor_year", "x", "log_gdp",
                                             "log_baseline_fertility", "y"])
    counts = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(counts).ge(2)].copy()
    panel = panel.sort_values(["country_iso3", "anchor_year"]).reset_index(drop=True)
    material = panel.x.abs().ge(MATERIAL_CHANGE)
    gate = {"key_only_rows": len(roster), "invalid_or_missing_fertility_pairs": invalid_pairs,
        "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
        "material_change_rows": int(material.sum()),
        "material_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
        "min_complete_anchors_per_country": 2, "outcome_values_read_after_lock": True}
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES
            or gate["material_change_rows"] < MIN_MATERIAL_ROWS
            or gate["material_change_countries"] < MIN_MATERIAL_COUNTRIES):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen complete-case or material-enrolment floor failed",
                "gate": gate, "primary": None}
    residual_model = smf.ols("x ~ log_gdp + log_baseline_fertility + C(country_iso3) + C(anchor_year)", data=panel)
    if np.linalg.matrix_rank(residual_model.exog) != residual_model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "treatment residualization lacks full rank",
                "gate": gate, "primary": None}
    residual = np.square(np.asarray(residual_model.fit().resid, dtype=float))
    total = float(residual.sum())
    if not math.isfinite(total) or total <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "no finite residual treatment variation",
                "gate": gate, "primary": None}
    top_n = max(1, math.ceil(.01 * len(panel)))
    shares = panel.assign(residual_sq=residual)
    gate["top_one_percent_residual_x_share"] = float(sum(sorted(residual, reverse=True)[:top_n]) / total)
    gate["top_country_residual_x_share"] = float(shares.groupby("country_iso3").residual_sq.sum().max() / total)
    if (gate["top_one_percent_residual_x_share"] > MAX_TOP_ONE_PERCENT
            or gate["top_country_residual_x_share"] > MAX_TOP_COUNTRY):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen residual-treatment concentration gate failed",
                "gate": gate, "primary": None}
    model = smf.ols("y ~ x + log_gdp + log_baseline_fertility + C(country_iso3) + C(anchor_year)", data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "primary model lacks full rank",
                "gate": gate, "primary": None}
    countries = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
        "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive country-cluster uncertainty",
                "gate": gate, "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), countries - 1))
    critical = float(student_t.ppf(0.995, countries - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"verdict": "INCONCLUSIVE", "reason": "nonfinite Student t inference",
                "gate": gate, "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 0.99, "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": countries, "df_inference": countries - 1,
        "model_rank": int(fit.model.rank),
        "method": "country/anchor FE OLS with baseline log fertility and log real GDP per person; country-cluster CR1; Student t(G-1)"}
    if beta <= -MIN_ABS_BETA and p <= ALPHA:
        verdict, reason = "SUPPORTED", "negative descriptive association clears frozen size and significance gates"
    elif beta >= MIN_ABS_BETA and p <= ALPHA:
        verdict, reason = "REFUTED", "opposite descriptive association clears frozen size and significance gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate": gate, "primary": primary}


def payload(result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    diagnostic = {"hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK, "template": "panel_fe",
        "preflight": gate, "primary": primary, "data_status": {"variables_missing": [],
        "input_vintages": list(SOURCES.values())}, "limitations": LIMITATIONS,
        "correction": CORRECTION}
    manifest = {"hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
        "derived_panel": gate, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "topic": "labour"},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": 1, "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
            "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate}, "results": {"primary": primary},
        "limitations": LIMITATIONS, "correction": CORRECTION}
    card = (f"# Result card: {HID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
        f"Gross secondary enrolment change from t−5 to t; log fertility change from t to t+10. "
        f"Complete pairs: {gate['valid_rows']} / {gate['valid_countries']} countries; "
        f"material schooling changes: {gate['material_change_rows']} / "
        f"{gate['material_change_countries']} countries.\n")
    if primary is not None:
        card += (f"\nBeta={primary['coefficient']:+.6g} log fertility change per +1 enrolment point; "
            f"country-cluster SE={primary['std_error']:.6g}; two-sided t p="
            f"{primary['p_value_two_sided']:.6g}; 99% CI={primary['confidence_interval']}.\n")
    card += ("\nThe single fixed test uses p≤0.01 and |beta|≥0.003 for direction. "
        "Gross both-sex enrolment and modeled fertility limit mechanism interpretation. "
        "Descriptive calibration only; zero causal, policy, school, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict,
        "primary": primary}
    coefficients = [{"term": "secondary_enrolment_change_pp", **primary}] if primary is not None else []
    return {"diagnostic": diagnostic, "manifest": manifest, "packet": packet,
        "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = f"{primary['coefficient']:+.6g}" if primary else "not estimated"
    p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
    return ("# Secondary enrolment and later fertility: frozen descriptive result\n\n"
        f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
        "| Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
        f"| **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | "
        f"{gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |\n\n"
        "Beta is ten-year log fertility change per +1 percentage-point five-year rise in gross secondary enrolment. "
        "The single-test directional rule requires p≤0.01 and |beta|≥0.003. "
        "This is a descriptive calibration without causal, policy, school-score, position, or featured credit.\n")


def normalize(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize(actual)
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
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected,
                rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def write_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated = payload(result, registration, lock_commit, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(generated["diagnostic"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(generated["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(generated["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(generated["card"])
    (folder / "replication.py").write_text(generated["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(generated["chart"], indent=2) + "\n")
    pd.DataFrame(generated["coefficients"], columns=["term", "coefficient", "std_error",
        "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows",
        "n_countries", "df_inference", "model_rank", "method"]).to_parquet(
            folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary(result, registration, lock_commit))


def verify_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    generated = payload(result, registration, lock_commit, saved["run_utc"])
    equal_close(saved, generated["diagnostic"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), generated["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), generated["packet"], "evidence_packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), generated["chart"], "chart")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
        generated["coefficients"], "coefficients")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != generated["card"]
            or (folder / "replication.py").read_text() != generated["wrapper"]
            or (ROOT / SUMMARY).read_text() != summary(result, registration, lock_commit)):
        raise AssertionError("text result artifact differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "validate-spec", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    selected = check_sources()
    if args.check_sources:
        print("three exact WDI vintage/manifest pins match; fertility values unopened")
        return 0
    if args.validate_spec:
        validate_spec()
        print("frozen specification, key-only roster, and runner agree")
        return 0
    blind = preflight()
    if args.preflight:
        print(json.dumps(blind, indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    registration = registration_commit()
    lock_commit = check_source_lock(registration, selected, blind)
    panel, gate = measured_panel(load_roster())
    result = estimate(panel, gate)
    if args.run:
        write_artifacts(result, registration, lock_commit)
        print(HID, result["verdict"], gate)
        return 0
    verify_artifacts(result, registration, lock_commit)
    print("verified exact replay", HID, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
