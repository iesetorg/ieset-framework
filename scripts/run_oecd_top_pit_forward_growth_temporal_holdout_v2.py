#!/usr/bin/env python3
"""Frozen temporal holdout: OECD top statutory PIT and later real GDP/person.

--lock reads hashes and country/year columns only, after a registration commit.
--run first reads selected values after a separate committed source lock.
--verify recomputes the exact saved outputs without changing them.
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
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_top_pit_forward_growth_temporal_holdout_v2"
FAMILY = ID + "_2026_10_10"
RUNNER = f"scripts/run_{ID}.py"
SPEC = f"hypotheses/fiscal/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PREREG = f"engine/audits/{ID}_prereg_2026-10-10.md"
TESTS = f"tests/test_{ID}.py"
ROSTER = f"data/pinned_evidence/{ID}_key_roster.csv"
ROSTER_SHA = "48caf338dfbe15839a3bd185cb570823ef9253be45d122b4d97847e12c2c430e"
LOCK = f"data/pinned_evidence/{ID}.source_lock.json"
RUN_DIR = f"engine/runs/{ID}"
SUMMARY = f"engine/audits/{ID}_results_2026-10-10.md"
SOURCES = {
    "treatment": {
        "publisher": "oecd", "series_id": "oecd_top_statutory_pit_rate",
        "path": "data/vintages/oecd/oecd_top_statutory_pit_rate@2026-07-23T153857Z.parquet",
        "sha256": "b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151",
        "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
        "manifest_sha256": "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18",
    },
    "outcome": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
    "control_trade": {
        "publisher": "world_bank_wdi", "series_id": "NE.TRD.GNFS.ZS",
        "path": "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
        "sha256": "4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
}
COUNTRIES = [
    "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
    "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
    "ISR", "ITA", "JPN", "KOR", "LTU", "LUX", "LVA", "MEX", "NLD", "NOR",
    "NZL", "POL", "PRT", "SVK", "SVN", "SWE", "TUR", "USA",
]
T_START, T_END = 2000, 2016
EXPECTED_KEY_ROWS = 646
MIN_ROWS, MIN_COUNTRIES, MIN_YEARS = 450, 30, 10
MIN_VARIATION_COUNTRIES = 15
MAX_TOP_1PCT, MAX_COUNTRY, MAX_YEAR = 0.20, 0.20, 0.25
ALPHA, HARM = 0.005, -0.3
FORMULA = (
    "forward_growth_pp_ann ~ top_pit_per_ten_pp + baseline_log_gdp "
    "+ pretrend_growth_pp_ann + trade_share + C(country_iso3) + C(year)"
)
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": ALPHA,
    "archive_wide_multiplicity_control": False,
    "school_score_eligible": False, "school_score_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "The statutory top wage-income PIT rate is not the average effective tax rate, capital-income rate, or total tax burden.",
    "Postwar 70-percent top rates and the revenue-maximizing rate are outside this modern-sample estimand.",
    "Policy selection, tax-base and bracket changes, common shocks, and reverse causality can confound the association.",
    "Overlapping three-year GDP windows and unobserved cross-country shocks limit country-cluster inference.",
    "The named old run is time-disjoint, but related IESET top-PIT studies were visible before registration.",
    "No causal, policy, school, position, or featured credit; the one-test alpha does not correct archive-wide selection.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    revisions = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if len(revisions) != 1:
        raise RuntimeError(f"expected exactly one first addition for {relative}: {revisions}")
    return revisions[0]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition bytes: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def threshold() -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 1, "family_alpha": ALPHA,
        "confidence_level_two_sided": 1 - ALPHA,
        "meaningful_harm_pp_annual_per_ten_tax_pp": HARM,
        "min_complete_rows": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
        "min_rows_per_country": MIN_YEARS,
        "min_countries_with_five_pp_rate_range": MIN_VARIATION_COUNTRIES,
        "max_top_one_percent_partialled_exposure_share": MAX_TOP_1PCT,
        "max_top_country_partialled_exposure_share": MAX_COUNTRY,
        "max_top_year_partialled_exposure_share": MAX_YEAR,
        "expected_key_rows": EXPECTED_KEY_ROWS,
        "expected_key_countries": len(COUNTRIES),
        "key_roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {key: source[key] for key in ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()
        },
        "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
        "causal_credit": 0, "featured_eligible": False,
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
            or spec["evidence_type"] != "associational"
            or spec["sample"]["countries"] != COUNTRIES
            or spec["sample"]["period"] != [T_START, T_END]
            or spec["falsification"]["threshold"] != threshold()
            or spec["steelman"] != STEELMAN or spec["covers_claims"] != []
            or spec["linked_hypotheses"] != [] or spec["linked_conditions"] != []):
        raise RuntimeError("specification differs from frozen runner contract")
    for forbidden in (LOCK, RUN_DIR, SUMMARY):
        if git("ls-tree", "-r", "--name-only", revision, "--", forbidden).strip():
            raise RuntimeError(f"postregistration artifact in registration commit: {forbidden}")
    return revision


def check_sources() -> dict[str, dict[str, Any]]:
    locked = {}
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} source bytes do not match SHA-256")
        manifest_path = ROOT / source["manifest"]
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest bytes do not match SHA-256")
        manifest = yaml.safe_load(manifest_path.read_text())
        matches = [
            entry for entry in manifest.get("entries", [])
            if entry.get("publisher") == source["publisher"]
            and entry.get("series_id") == source["series_id"]
            and entry.get("parquet_path") == source["path"]
            and entry.get("sha256") == source["sha256"]
        ]
        if len(matches) != 1:
            raise RuntimeError(f"{role} source entry missing or ambiguous in fetch manifest")
        entry = matches[0]
        locked[role] = {**source, **{name: entry.get(name) for name in (
            "source_url", "fetch_utc", "license", "rows", "frequency", "units")}}
    return locked


def load_roster() -> list[tuple[str, int]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("source-key roster SHA-256 mismatch")
    raw = path.read_bytes()
    if not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("source-key roster header mismatch")
    rows = [(row["country_iso3"], int(row["year"])) for row in
            csv.DictReader(io.StringIO(raw.decode()))]
    if (len(rows) != EXPECTED_KEY_ROWS or len(set(rows)) != len(rows)
            or rows != sorted(rows, key=lambda item: (item[1], item[0]))
            or sorted({c for c, _ in rows}) != COUNTRIES):
        raise RuntimeError("frozen source-key roster shape or order changed")
    return rows


def source_key_set(role: str) -> set[tuple[str, int]]:
    """Project only country/year; never open value or null mask at lock time."""
    source = SOURCES[role]
    table = pq.read_table(ROOT / source["path"], columns=["country_iso3", "year"]).to_pydict()
    rows = [(str(c), int(y)) for c, y in zip(table["country_iso3"], table["year"])
            if c and y is not None]
    if len(rows) != len(set(rows)):
        raise RuntimeError(f"duplicate nonblank country/year keys in {role}")
    expected_raw_rows = 950 if role == "treatment" else 17556
    if len(table["year"]) != expected_raw_rows:
        raise RuntimeError(f"unexpected raw key envelope in {role}")
    return set(rows)


def key_preflight() -> dict[str, Any]:
    pit, gdp, trade = (source_key_set(role) for role in
                       ("treatment", "outcome", "control_trade"))
    rows = sorted(((c, y) for c in COUNTRIES for y in range(T_START, T_END + 1)
                   if (c, y) in pit and (c, y - 3) in gdp and (c, y) in gdp
                   and (c, y + 3) in gdp and (c, y) in trade),
                  key=lambda item: (item[1], item[0]))
    if rows != load_roster():
        raise RuntimeError("source-key join differs from frozen roster")
    return {
        "country_year_keys_only": True, "selected_values_or_null_masks_read": False,
        "key_rows": len(rows), "key_countries": len({c for c, _ in rows}),
        "treatment_years": [T_START, T_END],
        "gdp_endpoint_years": [T_START - 3, T_END + 3],
        "roster_sha256": ROSTER_SHA,
    }


def source_lock_payload(registration: str, sources: dict[str, Any],
                        preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "preregistration_commit": registration,
        "sources": sources, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
        "key_preflight": preflight,
        "treatment_values_opened_before_lock": False,
        "outcome_values_opened_before_lock": False,
        "control_values_opened_before_lock": False,
        "selected_null_masks_opened_before_lock": False,
        "whole_fetch_manifests_copied": False,
    }


def write_source_lock() -> None:
    registration = registration_commit()
    if (ROOT / LOCK).exists() or (ROOT / RUN_DIR).exists() or (ROOT / SUMMARY).exists():
        raise RuntimeError("source lock or measured artifacts already exist")
    payload = source_lock_payload(registration, check_sources(), key_preflight())
    (ROOT / LOCK).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit it separately before selected-value access")


def check_source_lock(registration: str, sources: dict[str, Any],
                      preflight: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if json.loads(path.read_text()) != source_lock_payload(registration, sources, preflight):
        raise RuntimeError("source lock differs from frozen source custody")
    revision = first_addition(LOCK)
    if revision == registration or subprocess.run(
            ["git", "merge-base", "--is-ancestor", registration, revision],
            cwd=ROOT, check=False).returncode:
        raise RuntimeError("source lock must be a later commit")
    committed_unchanged(LOCK, revision)
    for forbidden in (RUN_DIR, SUMMARY):
        if git("ls-tree", "-r", "--name-only", revision, "--", forbidden).strip():
            raise RuntimeError(f"measured artifact in source-lock commit: {forbidden}")
    return revision


def numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def values(role: str) -> dict[tuple[str, int], float]:
    """This function may be called only after check_source_lock succeeds."""
    table = pq.read_table(ROOT / SOURCES[role]["path"],
                          columns=["country_iso3", "year", "value"]).to_pydict()
    rows = [((str(c), int(y)), numeric(v)) for c, y, v in zip(
        table["country_iso3"], table["year"], table["value"])
        if c and y is not None and str(c) in COUNTRIES]
    if len(rows) != len({key for key, _ in rows}):
        raise RuntimeError(f"duplicate selected country/year values in {role}")
    return dict(rows)


def measured_panel(roster: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    pit, gdp, trade = (values(role) for role in
                       ("treatment", "outcome", "control_trade"))
    records = []
    drops = Counter()
    for country, year in roster:
        tax = pit.get((country, year), float("nan"))
        initial = gdp.get((country, year), float("nan"))
        previous = gdp.get((country, year - 3), float("nan"))
        future = gdp.get((country, year + 3), float("nan"))
        trade_share = trade.get((country, year), float("nan"))
        if not (math.isfinite(tax) and 0 <= tax <= 100):
            drops["invalid_top_pit"] += 1
            continue
        if not (math.isfinite(initial) and initial > 0
                and math.isfinite(previous) and previous > 0
                and math.isfinite(future) and future > 0):
            drops["missing_nonpositive_or_nonfinite_gdp_endpoint"] += 1
            continue
        if not (math.isfinite(trade_share) and trade_share >= 0):
            drops["missing_negative_or_nonfinite_trade"] += 1
            continue
        records.append({
            "country_iso3": country, "year": year,
            "top_pit_per_ten_pp": tax / 10,
            "top_pit_pct": tax,
            "forward_growth_pp_ann": 100 * (math.log(future) - math.log(initial)) / 3,
            "baseline_log_gdp": math.log(initial),
            "pretrend_growth_pp_ann": 100 * (math.log(initial) - math.log(previous)) / 3,
            "trade_share": trade_share,
        })
    panel = pd.DataFrame.from_records(records, columns=[
        "country_iso3", "year", "top_pit_per_ten_pp", "top_pit_pct",
        "forward_growth_pp_ann", "baseline_log_gdp", "pretrend_growth_pp_ann",
        "trade_share",
    ])
    before_country_floor = len(panel)
    counts = panel.country_iso3.value_counts() if len(panel) else pd.Series(dtype=int)
    panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    variation = panel.groupby("country_iso3").top_pit_pct.agg(
        lambda x: float(x.max() - x.min())) if len(panel) else pd.Series(dtype=float)
    gate = {
        "roster_rows": len(roster), "dropped_by_reason": dict(sorted(drops.items())),
        "complete_rows_before_country_floor": before_country_floor,
        "dropped_by_country_floor": before_country_floor - len(panel),
        "complete_rows": len(panel),
        "complete_countries": int(panel.country_iso3.nunique()),
        "countries_with_five_pp_rate_range": int(variation.ge(5).sum()),
        "min_retained_years_per_country": int(panel.country_iso3.value_counts().min()) if len(panel) else 0,
        "selected_values_read_after_committed_source_lock": True,
    }
    return panel, gate


def exposure_concentration(panel: pd.DataFrame) -> dict[str, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    nuisance = pd.concat([
        panel[["baseline_log_gdp", "pretrend_growth_pp_ann", "trade_share"]].reset_index(drop=True),
        pd.get_dummies(panel.country_iso3, drop_first=True, dtype=float).reset_index(drop=True),
        pd.get_dummies(panel.year, drop_first=True, dtype=float).reset_index(drop=True),
    ], axis=1)
    nuisance.insert(0, "intercept", 1.0)
    design = nuisance.to_numpy(dtype=float)
    if np.linalg.matrix_rank(design) != design.shape[1]:
        return None
    exposure = panel.top_pit_per_ten_pp.to_numpy(dtype=float)
    residual = exposure - design @ np.linalg.lstsq(design, exposure, rcond=None)[0]
    signal = np.square(residual)
    total = float(signal.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(len(panel) * 0.01))
    groups = pd.DataFrame({"country": panel.country_iso3.to_numpy(),
                           "year": panel.year.to_numpy(), "signal": signal})
    return {
        "top_one_percent_share": float(np.sort(signal)[-top_n:].sum() / total),
        "top_country_share": float(groups.groupby("country").signal.sum().max() / total),
        "top_year_share": float(groups.groupby("year").signal.sum().max() / total),
    }


def classify_interval(low: float, high: float,
                      leave_one_out: list[float]) -> tuple[str, str]:
    if low > HARM and all(beta > HARM for beta in leave_one_out):
        return "SUPPORTED", "99.5-percent interval and every country deletion rule out the frozen growth-harm margin"
    if high < HARM and all(beta < HARM for beta in leave_one_out):
        return "REFUTED", "99.5-percent interval and every country deletion lie below the frozen growth-harm margin"
    return "PARTIAL", "estimated association does not clear the frozen precision and country-deletion rule"


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["complete_rows"] < MIN_ROWS
            or gate["complete_countries"] < MIN_COUNTRIES
            or gate["min_retained_years_per_country"] < MIN_YEARS
            or gate["countries_with_five_pp_rate_range"] < MIN_VARIATION_COUNTRIES):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or within-country tax-variation floor failed",
                "primary": None}
    concentration = exposure_concentration(panel)
    gate["partialled_exposure_concentration"] = concentration
    if (concentration is None
            or concentration["top_one_percent_share"] > MAX_TOP_1PCT
            or concentration["top_country_share"] > MAX_COUNTRY
            or concentration["top_year_share"] > MAX_YEAR):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residual-exposure concentration or rank gate failed",
                "primary": None}
    model = smf.ols(FORMULA, data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "primary fixed-effect design lacks full rank", "primary": None}
    n_countries = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={
        "groups": panel.country_iso3, "use_correction": True,
        "df_correction": True,
    }, use_t=True)
    beta, se = float(fit.params["top_pit_per_ten_pp"]), float(fit.bse["top_pit_per_ten_pp"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive country-cluster uncertainty",
                "primary": None}
    critical = float(student_t.ppf(1 - ALPHA / 2, n_countries - 1))
    if not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite country-cluster t cutoff", "primary": None}
    loo = []
    for country in sorted(panel.country_iso3.unique()):
        sub = panel.loc[panel.country_iso3.ne(country)]
        submodel = smf.ols(FORMULA, data=sub)
        if np.linalg.matrix_rank(submodel.exog) != submodel.exog.shape[1]:
            return {"gate": gate, "verdict": "INCONCLUSIVE",
                    "reason": f"leave-one-country-out fixed-effect design lacks rank after {country}",
                    "primary": None}
        loo.append(float(submodel.fit().params["top_pit_per_ten_pp"]))
    low, high = beta - critical * se, beta + critical * se
    verdict, reason = classify_interval(low, high, loo)
    primary = {
        "coefficient_annual_growth_pp_per_ten_tax_pp": beta,
        "std_error": se, "confidence_level": 1 - ALPHA,
        "confidence_interval": [low, high],
        "harm_margin": HARM,
        "p_value_two_sided_zero": float(2 * student_t.sf(abs(beta / se), n_countries - 1)),
        "n_rows": len(panel), "n_countries": n_countries,
        "df_inference": n_countries - 1,
        "model_rank": int(fit.model.rank),
        "leave_one_country_out_coefficient_range": [min(loo), max(loo)],
        "leave_one_country_out_count": len(loo),
        "method": "country/year FE OLS with three frozen controls; country-cluster CR1; Student t(G-1)",
    }
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def summary_text(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    estimate_text = "No valid estimate." if primary is None else (
        f"Coefficient {primary['coefficient_annual_growth_pp_per_ten_tax_pp']:+.6f} "
        f"annual growth percentage points per +10 top-PIT points; "
        f"99.5% interval [{primary['confidence_interval'][0]:+.6f}, "
        f"{primary['confidence_interval'][1]:+.6f}].")
    return (
        "# OECD top PIT and three-year forward real GDP/person growth\n\n"
        f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
        f"**{result['verdict']}** — {result['reason']}.\n\n"
        f"{estimate_text}\n\n"
        f"Key-only upper bound {EXPECTED_KEY_ROWS} / {len(COUNTRIES)}; "
        f"complete sample {gate['complete_rows']} / {gate['complete_countries']}; "
        f"countries with at least five-point tax-rate range "
        f"{gate['countries_with_five_pp_rate_range']}.\n\n"
        "The frozen harm margin is -0.3 annual growth percentage points per "
        "ten top-PIT points. This is a modern descriptive association, not "
        "an estimate of tax reform effects or the old 70-percent postwar claim. "
        "No causal, policy, school, position, or featured credit.\n"
    )


def artifacts(result: dict[str, Any], registration: str,
              lock_commit: str, stamp: str) -> dict[str, Any]:
    gate, primary = result["gate"], result["primary"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC, "topic": "fiscal"},
        "preregistration": {
            "spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": 1, "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN,
        },
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                    "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": ID, "family_id": FAMILY,
        "verdict": result["verdict"], "verdict_label": result["verdict"],
        "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "template": "panel_fe",
        "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK,
        "preflight": gate, "primary": primary,
        "confidence_level": 1 - ALPHA, "harm_margin": HARM,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK,
        "status": result["verdict"], "vintages": list(SOURCES.values()),
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
    coefficients = [] if primary is None else [{
        "term": "top_pit_per_ten_pp",
        "coefficient": primary["coefficient_annual_growth_pp_per_ten_tax_pp"],
        "std_error": primary["std_error"],
        "ci_low": primary["confidence_interval"][0],
        "ci_high": primary["confidence_interval"][1],
        "n_rows": primary["n_rows"],
        "n_countries": primary["n_countries"],
    }]
    return {"packet": packet, "diagnostics": diagnostics,
            "manifest": manifest, "wrapper": wrapper,
            "chart": chart, "coefficients": coefficients}


def write_artifacts(result: dict[str, Any], registration: str,
                    lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("result artifacts already exist")
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
    pd.DataFrame(payload["coefficients"], columns=[
        "term", "coefficient", "std_error", "ci_low", "ci_high",
        "n_rows", "n_countries",
    ]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(result, registration, lock_commit))


def replay_equal(actual: Any, expected: Any, label: str) -> None:
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
    replay_equal(yaml.safe_load((folder / "manifest.yaml").read_text()),
                 expected["manifest"], "manifest")
    replay_equal(yaml.safe_load((folder / "evidence_packet.yaml").read_text()),
                 expected["packet"], "evidence packet")
    replay_equal(json.loads((folder / "chart_data.json").read_text()),
                 expected["chart"], "chart")
    for relative, expected_text in (
            ("result_card.md", summary_text(result, registration, lock_commit)),
            ("replication.py", expected["wrapper"])):
        if (folder / relative).read_text() != expected_text:
            raise AssertionError(f"saved {relative} differs from exact replay")
    if (ROOT / SUMMARY).read_text() != summary_text(result, registration, lock_commit):
        raise AssertionError("saved audit summary differs from exact replay")
    if (folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes():
        raise AssertionError("saved hypothesis snapshot differs from frozen spec")
    saved_coefficients = pd.read_parquet(folder / "coefficients.parquet")
    current_coefficients = pd.DataFrame(expected["coefficients"], columns=[
        "term", "coefficient", "std_error", "ci_low", "ci_high",
        "n_rows", "n_countries",
    ])
    if saved_coefficients.shape != current_coefficients.shape:
        raise AssertionError("saved coefficient shape differs from replay")
    if len(saved_coefficients):
        for name in current_coefficients.columns:
            for got, wanted in zip(saved_coefficients[name], current_coefficients[name]):
                replay_equal(got, wanted, f"coefficients.{name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-registration", action="store_true")
    mode.add_argument("--lock", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check_registration:
        print("registration", registration_commit())
        return
    if args.lock:
        write_source_lock()
        return
    registration = registration_commit()
    sources = check_sources()
    preflight = key_preflight()
    lock_commit = check_source_lock(registration, sources, preflight)
    result = estimate(*measured_panel(load_roster()))
    if args.run:
        write_artifacts(result, registration, lock_commit)
        print(ID, result["verdict"], result["gate"])
    else:
        verify_artifacts(result, registration, lock_commit)
        print(ID, "exact replay passed", result["verdict"])


if __name__ == "__main__":
    main()
