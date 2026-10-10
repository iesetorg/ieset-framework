#!/usr/bin/env python3
"""Guarded one-test ALMP-to-employment calibration; outcomes open only after source lock."""
from __future__ import annotations

import argparse
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
STUDY = "oecd_almp_low_education_employment_forward_2026"
FAMILY = "oecd_almp_low_education_employment_2026_10_10"
RUNNER = "scripts/run_oecd_almp_low_education_employment_2026.py"
TEST = "tests/test_oecd_almp_low_education_employment_2026.py"
SPEC = f"hypotheses/labour/{STUDY}.yaml"
STEELMAN = f"hypotheses/steelman/{STUDY}.md"
PREREG = "engine/audits/oecd_almp_low_education_employment_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/oecd_almp_low_education_employment_2026_key_roster.csv"
ROSTER_SHA = "0b6d3f7c6758641c29ba8e03006f08a0be44d60023ffc08c3710582eecf84445"
LOCK = "data/pinned_evidence/oecd_almp_low_education_employment_2026.manifest.json"
RESULT_DIR = f"engine/runs/{STUDY}"
SUMMARY = "engine/audits/oecd_almp_low_education_employment_results_2026-10-10.md"

T_START, T_END, MIN_YEARS = 2005, 2018, 5
EVENT_CUT = 0.05
P_MAX, SESOI = 0.01, 0.5
MIN_ROWS, MIN_COUNTRIES = 300, 25
MIN_EVENT_ROWS, MIN_EVENT_COUNTRIES = 50, 15
MAX_TOP_ROWS, MAX_TOP_COUNTRY = 0.30, 0.30
KEY_ROWS, KEY_COUNTRIES, KEY_INCREASES, KEY_DECREASES = 410, 30, 78, 82

SOURCES = {
    "almp": {"publisher": "oecd", "series_id": "DSD_SOCX@DF_SOCX_AGG",
             "path": "data/vintages/oecd/DSD_SOCX_DF_SOCX_AGG@2026-05-05T210247Z.parquet",
             "sha256": "93e7e29b24dc791baf22833ae5596b4a381a366ddd0d78499bf59f7b80786124",
             "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
             "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "gdp_per_person": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
                       "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
                       "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
                       "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
                       "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "outcome": {"publisher": "eurostat", "series_id": "lfsa_ergaedn",
                "path": "data/vintages/eurostat/lfsa_ergaedn@2026-04-30T125100Z.parquet",
                "sha256": "6bdae02133c40b7498922a0a1fa2b28d3e63fcde3fff3915353e87275c78edc3",
                "manifest": "data/manifests/fetch_run_2026-04-30T125203Z.yaml",
                "manifest_sha256": "9fb01a47d0598eb7d91de7765aea54a25f100c490d88b9414c6e8453a90d1df6"},
}
SOCX_SELECTOR = {"FREQ": "A", "MEASURE": "SOCX", "UNIT_MEASURE": "PT_B1GQ",
                 "EXPEND_SOURCE": "ES10", "SPENDING_TYPE": "_T",
                 "PROGRAMME_TYPE": "TP60", "PRICE_BASE": "_Z", "OBS_STATUS": "A"}
OUTCOME_SELECTOR = {"freq": "A", "citizen": "TOTAL", "isced11": "ED0-2",
                    "sex": "T", "age": "Y25-64", "unit": "PC"}
OUTCOME_KEY_COLUMNS = ["freq", "citizen", "isced11", "sex", "age", "unit", "geo_code", "period"]
EURO_TO_ISO3 = dict(zip(
    "AT BE BG CH CZ DE DK ES EE FI FR UK EL HR HU IE IS IT LT LU LV NL NO PL PT RO SK SI SE TR".split(),
    "AUT BEL BGR CHE CZE DEU DNK ESP EST FIN FRA GBR GRC HRV HUN IRL ISL ITA LTU LUX LVA NLD NOR POL PRT ROU SVK SVN SWE TUR".split(),
))
assert len(EURO_TO_ISO3) == KEY_COUNTRIES

CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 1, "family_alpha": P_MAX,
              "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "featured_eligible": False}
LIMITATIONS = [
    "Public ALMP spending reacts to labour-market conditions and its GDP denominator changes with GDP.",
    "SOCX TP60 spending does not identify participation, programme quality, or implementation.",
    "Eurostat low-education employment is a survey rate, not job quality or wage income.",
    "The pinned Eurostat vintage has no cell status or method-break flag; no break-screened claim is possible.",
    "Baseline-rate adjustment can be sensitive to regression to the mean.",
    "Country and year effects and next-year ordering do not identify causality.",
    "This one-test alpha does not correct for the broader exploratory IESET archive.",
    "No causal, programme-effect, policy, school, position, or featured credit is permitted.",
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
    revisions = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"no first-addition commit: {relative}")
    return revisions[-1]


def frozen_file(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"registered or locked file changed: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted registered or locked file: {relative}")


def threshold() -> dict[str, Any]:
    files = {role: {field: source[field] for field in ("path", "sha256", "manifest", "manifest_sha256")}
             for role, source in SOURCES.items()}
    return {"family_id": FAMILY, "family_size": 1, "family_alpha": P_MAX,
            "p_max_two_sided": P_MAX, "meaningful_contrast_pp": SESOI,
            "event_change_gdp_pp": EVENT_CUT, "min_valid_rows": MIN_ROWS,
            "min_valid_countries": MIN_COUNTRIES, "min_years_per_country": MIN_YEARS,
            "min_increase_rows": MIN_EVENT_ROWS, "min_increase_countries": MIN_EVENT_COUNTRIES,
            "min_decrease_rows": MIN_EVENT_ROWS, "min_decrease_countries": MIN_EVENT_COUNTRIES,
            "max_top_one_percent_residual_event_share": MAX_TOP_ROWS,
            "max_top_country_residual_event_share": MAX_TOP_COUNTRY,
            "expected_key_rows": KEY_ROWS, "expected_key_countries": KEY_COUNTRIES,
            "expected_increase_rows": KEY_INCREASES, "expected_decrease_rows": KEY_DECREASES,
            "roster_sha256": ROSTER_SHA, "source_files": files,
            "causal_credit": 0, "policy_score_eligible": False,
            "policy_score_credit": 0, "school_score_eligible": False,
            "school_score_credit": 0, "featured_eligible": False}


def check_sources(source_root: Path) -> dict[str, dict[str, Any]]:
    selected = {}
    for role, source in SOURCES.items():
        raw, manifest = source_root / source["path"], source_root / source["manifest"]
        if not raw.is_file() or sha256(raw) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched raw source: {role}")
        if not manifest.is_file() or sha256(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [entry for entry in entries
                   if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"fetch manifest lacks pinned entry: {role}")
        selected[role] = {**source, "source_url": matches[0].get("source_url"),
                          "methodology_url": matches[0].get("methodology_url"),
                          "license": matches[0].get("license"), "fetch_utc": matches[0].get("fetch_utc")}
    return selected


def load_roster() -> list[tuple[str, int]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("frozen key roster hash mismatch")
    raw = pd.read_csv(path)
    if list(raw.columns) != ["study_id", "country_iso3", "year"] or raw.duplicated().any():
        raise RuntimeError("invalid or duplicate key roster")
    if not raw.study_id.eq(STUDY).all() or len(raw) != KEY_ROWS or raw.country_iso3.nunique() != KEY_COUNTRIES:
        raise RuntimeError("frozen key roster envelope changed")
    sorted_raw = raw.sort_values(["study_id", "country_iso3", "year"]).reset_index(drop=True)
    if not raw.reset_index(drop=True).equals(sorted_raw):
        raise RuntimeError("frozen key roster order changed")
    return [(str(c), int(y)) for c, y in raw[["country_iso3", "year"]].itertuples(index=False, name=None)]


def registration_commit() -> str:
    paths = [RUNNER, TEST, SPEC, STEELMAN, PREREG, ROSTER]
    revisions = {first_addition(path) for path in paths}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in paths:
        frozen_file(path, revision)
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RESULT_DIR).strip():
        raise RuntimeError("registration commit already contained measured results")
    if git_output("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("registration commit already contained a source lock")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != STUDY or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "+"
            or spec.get("steelman") != STEELMAN or spec["sample"].get("period") != [T_START, T_END]
            or spec["sample"].get("countries") != sorted({c for c, _ in load_roster()})
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or spec["falsification"].get("threshold") != threshold()):
        raise RuntimeError("frozen hypothesis specification differs from guarded runner")
    return revision


def selected_keys(source_root: Path) -> set[tuple[str, int]]:
    """Read only Eurostat dimension columns; never load value or its null mask."""
    path = source_root / SOURCES["outcome"]["path"]
    parquet = pq.ParquetFile(path)
    if parquet.metadata.num_rows != 1184864 or parquet.schema.names != OUTCOME_KEY_COLUMNS + ["value"]:
        raise RuntimeError("Eurostat source schema or row count changed")
    frame = pd.read_parquet(path, columns=OUTCOME_KEY_COLUMNS)
    for column, value in OUTCOME_SELECTOR.items():
        frame = frame.loc[frame[column].eq(value)]
    frame = frame.loc[frame.geo_code.isin(EURO_TO_ISO3)].copy()
    frame["country_iso3"] = frame.geo_code.map(EURO_TO_ISO3)
    frame["year"] = pd.to_numeric(frame.period, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate selected Eurostat country-year key")
    return {(str(c), int(y)) for c, y in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def treatment_and_controls(source_root: Path) -> tuple[dict[tuple[str, int], float], dict[tuple[str, int], float]]:
    socx_columns = ["REF_AREA", "FREQ", "MEASURE", "UNIT_MEASURE", "EXPEND_SOURCE",
                    "SPENDING_TYPE", "PROGRAMME_TYPE", "PRICE_BASE", "period", "value", "OBS_STATUS"]
    socx = pd.read_parquet(source_root / SOURCES["almp"]["path"], columns=socx_columns)
    for column, value in SOCX_SELECTOR.items():
        socx = socx.loc[socx[column].eq(value)]
    socx = socx.copy()
    socx["year"] = pd.to_numeric(socx.period, errors="raise").astype(int)
    if socx.duplicated(["REF_AREA", "year"]).any():
        raise RuntimeError("duplicate selected SOCX country-year")
    socx["value"] = pd.to_numeric(socx.value, errors="coerce")
    socx = socx.loc[np.isfinite(socx.value) & socx.value.between(0, 10)]
    treatment = {(str(c), int(y)): float(v)
                 for c, y, v in socx[["REF_AREA", "year", "value"]].itertuples(index=False, name=None)}

    wdi = pd.read_parquet(source_root / SOURCES["gdp_per_person"]["path"],
                          columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(wdi) != 17556 or not wdi.indicator_id.eq("NY.GDP.PCAP.KD").all():
        raise RuntimeError("WDI source row or indicator contract changed")
    wdi = wdi.loc[wdi.country_iso3.isin(EURO_TO_ISO3.values())].copy()
    if wdi.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate selected WDI country-year")
    wdi["value"] = pd.to_numeric(wdi.value, errors="coerce")
    wdi = wdi.loc[wdi.obs_status.fillna("").eq("") & np.isfinite(wdi.value) & wdi.value.gt(0)]
    gdp = {(str(c), int(y)): math.log(float(v))
           for c, y, v in wdi[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    return treatment, gdp


def event_indicators(delta: float) -> tuple[int, int]:
    if not math.isfinite(delta):
        raise ValueError("nonfinite SOCX change")
    return int(delta >= EVENT_CUT), int(delta <= -EVENT_CUT)


def candidate_panel(source_root: Path) -> pd.DataFrame:
    treatment, gdp = treatment_and_controls(source_root)
    keys = selected_keys(source_root)
    rows = []
    for country, year in sorted(keys):
        if (not T_START <= year <= T_END or (country, year + 1) not in keys
                or (country, year) not in treatment or (country, year - 1) not in treatment
                or (country, year) not in gdp):
            continue
        delta = treatment[(country, year)] - treatment[(country, year - 1)]
        increase, decrease = event_indicators(delta)
        rows.append({"country_iso3": country, "year": year, "delta": delta,
                     "increase": increase, "decrease": decrease, "log_gdp_pc": gdp[(country, year)]})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "delta", "increase", "decrease", "log_gdp_pc"])
    counts = panel.country_iso3.value_counts()
    return panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].reset_index(drop=True)


def residual_shares(panel: pd.DataFrame, event: str, include_baseline: bool) -> tuple[float, float] | None:
    opposite = "decrease" if event == "increase" else "increase"
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    baseline = " + baseline_rate" if include_baseline else ""
    fit = smf.ols(f"{event} ~ {opposite} + log_gdp_pc{baseline} + C(country_iso3) + C(year)", data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * len(panel)))
    top_rows = float(np.sort(squared)[-top_n:].sum() / total)
    top_country = float(pd.DataFrame({"country": panel.country_iso3.to_numpy(), "sq": squared})
                        .groupby("country").sq.sum().max() / total)
    return top_rows, top_country


def preflight(source_root: Path) -> dict[str, Any]:
    panel = candidate_panel(source_root)
    roster = [(str(c), int(y)) for c, y in panel[["country_iso3", "year"]].itertuples(index=False, name=None)]
    if roster != load_roster():
        raise RuntimeError("source-only candidate keys differ from frozen roster")
    inc, dec = int(panel.increase.sum()), int(panel.decrease.sum())
    if (len(panel) != KEY_ROWS or panel.country_iso3.nunique() != KEY_COUNTRIES
            or inc != KEY_INCREASES or dec != KEY_DECREASES):
        raise RuntimeError("treatment-only event envelope changed")
    shares = {event: residual_shares(panel, event, include_baseline=False)
              for event in ("increase", "decrease")}
    if any(share is None or share[0] > MAX_TOP_ROWS or share[1] > MAX_TOP_COUNTRY
           for share in shares.values()):
        raise RuntimeError("prelock event concentration gate failed")
    return {"key_rows": len(panel), "key_countries": int(panel.country_iso3.nunique()),
            "increase_rows": inc, "increase_countries": int(panel.loc[panel.increase.eq(1), "country_iso3"].nunique()),
            "decrease_rows": dec, "decrease_countries": int(panel.loc[panel.decrease.eq(1), "country_iso3"].nunique()),
            "stable_rows": len(panel) - inc - dec,
            "residual_event_shares": {event: {"top_one_percent_rows": share[0], "top_country": share[1]}
                                      for event, share in shares.items()},
            "roster_sha256": ROSTER_SHA, "treatment_values_read": True,
            "control_values_read": True, "outcome_selector_keys_only": True,
            "outcome_values_read": False, "outcome_null_masks_read": False,
            "outcome_status_read": False}


def lock_payload(registration: str, sources: dict[str, Any], keys: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
            "sources": sources, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": keys, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_lock(sources: dict[str, Any], keys: dict[str, Any]) -> None:
    registration = registration_commit()
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, sources, keys), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit it separately before --run")


def check_lock(registration: str, sources: dict[str, Any], keys: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if not path.is_file() or json.loads(path.read_text()) != lock_payload(registration, sources, keys):
        raise RuntimeError("source lock differs from registration or source-only preflight")
    revision = first_addition(LOCK)
    if revision == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, revision],
                                                   cwd=ROOT).returncode:
        raise RuntimeError("source-lock commit must descend separately from registration")
    frozen_file(LOCK, revision)
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RESULT_DIR).strip():
        raise RuntimeError("source-lock commit already contained measured results")
    return revision


def finite_rate(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) and 0 <= numeric <= 100 else None


def measured_panel(source_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """The first permitted read of selected Eurostat numeric employment values."""
    candidate = candidate_panel(source_root)
    path = source_root / SOURCES["outcome"]["path"]
    frame = pd.read_parquet(path, columns=OUTCOME_KEY_COLUMNS + ["value"])
    for column, value in OUTCOME_SELECTOR.items():
        frame = frame.loc[frame[column].eq(value)]
    frame = frame.loc[frame.geo_code.isin(EURO_TO_ISO3)].copy()
    frame["country_iso3"] = frame.geo_code.map(EURO_TO_ISO3)
    frame["year"] = pd.to_numeric(frame.period, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate measured Eurostat selector key")
    values = {(str(c), int(y)): finite_rate(v)
              for c, y, v in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    rows, invalid = [], 0
    for row in candidate.itertuples(index=False):
        baseline = values.get((row.country_iso3, row.year))
        forward = values.get((row.country_iso3, row.year + 1))
        if baseline is None or forward is None:
            invalid += 1
            continue
        rows.append({"country_iso3": row.country_iso3, "year": row.year,
                     "increase": row.increase, "decrease": row.decrease,
                     "log_gdp_pc": row.log_gdp_pc, "baseline_rate": baseline,
                     "y": forward - baseline})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "increase", "decrease",
                                        "log_gdp_pc", "baseline_rate", "y"])
    before_year_floor = len(panel)
    counts = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    gate = {"key_only_rows": len(candidate), "invalid_or_missing_endpoint_pairs": invalid,
            "complete_pairs_before_five_year_country_floor": before_year_floor,
            "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
            "increase_rows": int(panel.increase.sum()),
            "increase_countries": int(panel.loc[panel.increase.eq(1), "country_iso3"].nunique()),
            "decrease_rows": int(panel.decrease.sum()),
            "decrease_countries": int(panel.loc[panel.decrease.eq(1), "country_iso3"].nunique()),
            "outcome_values_read_after_lock": True, "outcome_break_flags_available": False}
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES
            or gate["increase_rows"] < MIN_EVENT_ROWS or gate["increase_countries"] < MIN_EVENT_COUNTRIES
            or gate["decrease_rows"] < MIN_EVENT_ROWS or gate["decrease_countries"] < MIN_EVENT_COUNTRIES):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen complete-case or event floor failed",
                "primary": None}
    shares = {event: residual_shares(panel, event, include_baseline=True)
              for event in ("increase", "decrease")}
    gate["residual_event_shares"] = {event: {"top_one_percent_rows": share[0], "top_country": share[1]}
                                     for event, share in shares.items() if share is not None}
    if any(share is None or share[0] > MAX_TOP_ROWS or share[1] > MAX_TOP_COUNTRY
           for share in shares.values()):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen residual-event concentration gate failed",
                "primary": None}
    formula = "y ~ increase + decrease + baseline_rate + log_gdp_pc + C(country_iso3) + C(year)"
    model = smf.ols(formula, data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "primary fixed-effect design lacks full rank",
                "primary": None}
    g = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                   "use_correction": True, "df_correction": True}, use_t=True)
    beta_inc, beta_dec = float(fit.params["increase"]), float(fit.params["decrease"])
    covariance = fit.cov_params()
    variance = float(covariance.loc["increase", "increase"] + covariance.loc["decrease", "decrease"]
                     - 2 * covariance.loc["increase", "decrease"])
    if not math.isfinite(variance) or variance <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive contrast uncertainty",
                "primary": None}
    beta, se = beta_inc - beta_dec, math.sqrt(variance)
    p = float(2 * student_t.sf(abs(beta / se), g - 1))
    critical = float(student_t.ppf(0.995, g - 1))
    if not all(math.isfinite(x) for x in (beta, se, p, critical)):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite primary inference",
                "primary": None}
    primary = {"contrast_increase_minus_decrease_pp": beta, "increase_coefficient": beta_inc,
               "decrease_coefficient": beta_dec, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.99, "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": g, "df_inference": g - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS with baseline rate and log GDPpc, country-cluster CR1, Student t(G-1)"}
    if beta >= SESOI and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive event contrast clears frozen size and two-sided p gates"
    elif beta <= -SESOI and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite event contrast clears frozen size and two-sided p gates"
    else:
        verdict, reason = "PARTIAL", "estimable contrast does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": STUDY, "path": SPEC, "topic": "labour"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                    "family_id": FAMILY, "family_size": 1,
                                    "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                    "steelman": STEELMAN},
              "reproduction": {"runner": RUNNER, "run_dir": RESULT_DIR,
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": SOURCES, "sample": gate},
              "results": {"primary": primary}, "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": STUDY, "family_id": FAMILY, "verdict": verdict,
                   "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
                   "primary": primary, "p_max_two_sided": P_MAX,
                   "meaningful_contrast_pp": SESOI,
                   "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": STUDY, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {STUDY}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
            f"OECD TP60 spending increase/decrease events in t predict Eurostat ED0-2 adult employment-rate "
            f"change t to t+1. Key-only upper bound: {KEY_ROWS} country-years / {KEY_COUNTRIES} countries. "
            f"Complete pairs: {gate['valid_rows']} / {gate['valid_countries']}; increase events: "
            f"{gate['increase_rows']} / {gate['increase_countries']}; decrease events: "
            f"{gate['decrease_rows']} / {gate['decrease_countries']}.\n")
    if primary is not None:
        card += (f"\nIncrease-minus-decrease contrast={primary['contrast_increase_minus_decrease_pp']:+.6g} "
                 f"employment-rate points; country-cluster SE={primary['std_error']:.6g}; "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}; "
                 f"99% CI={primary['confidence_interval']}.\n")
    card += ("\nSingle prespecified two-sided test: p <= 0.01 and |contrast| >= 0.5 point for a directional verdict. "
             "The Eurostat vintage lacks cell-level quality and break flags. Descriptive calibration only; "
             "no causal, programme-effect, policy, school, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": STUDY, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = ([{"term": "increase_minus_decrease", "coefficient": primary["contrast_increase_minus_decrease_pp"],
                     "std_error": primary["std_error"], "p_value_two_sided": primary["p_value_two_sided"],
                     "confidence_level": primary["confidence_level"], "confidence_interval": primary["confidence_interval"],
                     "n_rows": primary["n_rows"], "n_countries": primary["n_countries"],
                     "df_inference": primary["df_inference"], "model_rank": primary["model_rank"],
                     "method": primary["method"]}] if primary is not None else [])
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = f"{primary['contrast_increase_minus_decrease_pp']:+.6g}" if primary else "not estimated"
    p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
    return ("# Public ALMP spending and low-education employment: descriptive result\n\n"
            f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
            f"Verdict **{result['verdict']}**: {result['reason']}.\n\n"
            f"Complete pairs {gate['valid_rows']} / {gate['valid_countries']} countries; "
            f"increase events {gate['increase_rows']} / {gate['increase_countries']}; "
            f"decrease events {gate['decrease_rows']} / {gate['decrease_countries']}. "
            f"Increase-minus-decrease contrast {beta} employment-rate points; two-sided p {p}.\n\n"
            "Country and year effects do not establish a programme effect. The Eurostat vintage has no "
            "cell-level quality or break flags. Zero causal, policy, school, position, and featured credit.\n")


def write_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RESULT_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = artifact_payload(result, registration, lock_commit, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["coefficients"], columns=["term", "coefficient", "std_error",
                 "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows",
                 "n_countries", "df_inference", "model_rank", "method"]).to_parquet(folder / "coefficients.parquet", index=False)
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
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
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
        raise AssertionError("family summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("preflight", "lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT,
                        help="Only for read-only --preflight outside this checkout")
    args = parser.parse_args()
    if args.source_root != ROOT and not args.preflight:
        parser.error("--source-root override is restricted to read-only preflight")
    sources = check_sources(args.source_root)
    keys = preflight(args.source_root)
    if args.preflight:
        print(json.dumps(keys, indent=2, sort_keys=True))
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
