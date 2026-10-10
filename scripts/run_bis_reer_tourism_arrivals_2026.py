#!/usr/bin/env python3
"""Guarded one-test BIS real-appreciation to tourist-arrivals calibration.

--preflight decodes BIS treatment and GDP-control values plus tourism schema/keys
only. The first tourism value/null/status access is behind separate immutable
preregistration and source-lock commits. --verify replays every result artifact.
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
ID = "bis_reer_appreciation_tourism_arrivals_forward_2026"
FAMILY = "bis_reer_tourism_arrivals_forward_2026_10_10"
RUNNER = "scripts/run_bis_reer_tourism_arrivals_2026.py"
SPEC = f"hypotheses/trade/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PREREG = "engine/audits/bis_reer_tourism_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/reer_tourism_2026_key_roster.csv"
ROSTER_SHA = "0dc4d0162c1dcdc289f904c9331da8e08f4f2a98e8e57b3163c2a396771146eb"
TEST = "tests/test_bis_reer_tourism_prereg_2026.py"
LOCK = "data/pinned_evidence/reer_tourism_2026.manifest.json"
RUN = f"engine/runs/{ID}"
SUMMARY = "engine/audits/bis_reer_tourism_results_2026-10-10.md"
T_START, T_END, MIN_YEARS = 2004, 2018, 5
EVENT_MIN, MIN_ROWS, MIN_COUNTRIES = 5.0, 400, 25
MIN_EVENTS, MIN_EVENT_COUNTRIES = 30, 15
P_MAX, MEANINGFUL_BETA = 0.01, 0.03
MAX_COUNTRY_SHARE, MAX_TOP_ROW_SHARE = 0.15, 0.20
COUNTRIES = tuple(
    "ARE ARG AUS AUT BEL BGR BIH BRA CAN CHE CHL CHN COL CYP CZE DEU DNK DZA ESP EST FIN FRA GBR "
    "GRC HKG HRV HUN IDN IND IRL ISL ISR ITA JPN KOR LTU LUX LVA MAR MEX MKD MLT MYS NLD NOR "
    "NZL PER PHL POL PRT ROU RUS SAU SGP SRB SVK SVN SWE THA TUR USA ZAF".split()
)
BIS_TO_ISO3 = dict(zip(
    "AE AR AU AT BE BG BA BR CA CH CL CN CO CY CZ DE DK DZ ES EE FI FR GB GR HK HR HU ID IN IE "
    "IS IL IT JP KR LT LU LV MA MX MK MT MY NL NO NZ PE PH PL PT RO RU SA SG RS SK SI SE TH TR US ZA".split(),
    COUNTRIES,
))
assert len(COUNTRIES) == len(set(COUNTRIES)) == len(BIS_TO_ISO3) == 62
SOURCES = {
    "reer": {
        "publisher": "bis", "series_id": "WS_EER",
        "path": "data/vintages/bis/WS_EER@2026-07-23T151604Z.parquet",
        "sha256": "57bbce3e22fc428c8cd8ddee8a998d273b5240a816af89e532b81d41ade35170",
        "manifest": "data/manifests/fetch_run_2026-07-23T151632Z.yaml",
        "manifest_sha256": "1768f0d7c38c93f1ad4df591b0b1634b3460faa964f6267874b8798b7b8dbb81",
    },
    "arrivals": {
        "publisher": "world_bank_wdi", "series_id": "ST.INT.ARVL",
        "path": "data/vintages/world_bank_wdi/ST.INT.ARVL@2026-05-05T203952Z.parquet",
        "sha256": "1336df1cce2b3a2e784f917caa9487753d4cf53ad4ec65e5ea2fb045b0d41da5",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
    },
    "gdp_growth": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
        "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
        "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
}
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": P_MAX, "bonferroni_p_max": P_MAX,
    "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0,
    "position_score_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "BIS real EER weights are based on manufacturing trade, not tourist-origin shares.",
    "WDI tourist arrivals are trips rather than people and use differing country reporting methods.",
    "GDP growth and fixed effects do not remove destination safety, capacity, airfare, or other confounding.",
    "The local one-test cutoff does not correct earlier IESET corpus-wide selection.",
    "No causal, policy, position, school-score, or featured credit is permitted.",
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
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[0]


def committed_unchanged(relative: str, revision: str) -> None:
    if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file changed after first addition: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def threshold() -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 1, "family_alpha": P_MAX,
        "p_max_two_sided": P_MAX, "expected_beta_sign": "-",
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "min_complete_rows": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
        "min_years_per_country": MIN_YEARS, "event_min_log_points": EVENT_MIN,
        "min_event_rows": MIN_EVENTS, "min_event_countries": MIN_EVENT_COUNTRIES,
        "max_top_country_residual_x_share": MAX_COUNTRY_SHARE,
        "max_top_one_percent_residual_x_share": MAX_TOP_ROW_SHARE,
        "expected_key_rows": 930, "expected_key_countries": 62,
        "expected_treatment_and_gdp_control_rows": 930,
        "expected_treatment_events": 118,
        "expected_treatment_event_countries": 40,
        "roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {field: source[field] for field in ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()
        },
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }


def source_pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(tuple(sorted({variable["source"] for variable in variables.get(role, [])
                               if isinstance(variable, dict) and variable.get("source")}))
                 for role in ("treatment", "outcome"))


def verify_spec() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-"
            or spec.get("steelman") != STEELMAN
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or spec.get("sample", {}).get("countries") != list(COUNTRIES)
            or spec.get("sample", {}).get("period") != [T_START, T_END]
            or spec.get("scope", {}).get("countries") != list(COUNTRIES)
            or spec.get("scope", {}).get("period") != [T_START, T_END + 1]
            or spec.get("scope", {}).get("outcome_dim") != ["tourism_activity"]
            or spec.get("falsification", {}).get("threshold") != threshold()):
        raise RuntimeError("frozen tourism hypothesis contract mismatch")
    expected_pair = (("bis:WS_EER",), ("world_bank_wdi:ST.INT.ARVL",))
    if source_pair(spec) != expected_pair:
        raise RuntimeError("registered REER/tourism source pair changed")
    for path in (ROOT / "hypotheses").rglob("*.yaml"):
        if path == ROOT / SPEC:
            continue
        try:
            candidate = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            continue
        if candidate.get("status") == "pre_registered" and source_pair(candidate) == expected_pair:
            raise RuntimeError(f"duplicate strict REER/tourism source pair: {path}")


def check_sources() -> dict[str, dict[str, Any]]:
    narrow: dict[str, dict[str, Any]] = {}
    for role, source in SOURCES.items():
        raw_path = ROOT / source["path"]
        manifest_path = ROOT / source["manifest"]
        if not raw_path.is_file() or sha256(raw_path) != source["sha256"]:
            raise RuntimeError(f"{role} raw source SHA-256 mismatch")
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch")
        manifest = yaml.safe_load(manifest_path.read_text())
        matched = [row for row in manifest.get("entries", [])
                   if row.get("publisher") == source["publisher"]
                   and row.get("series_id") == source["series_id"]
                   and row.get("parquet_path") == source["path"]]
        if len(matched) != 1 or matched[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} fetch entry mismatch")
        row = matched[0]
        narrow[role] = {**source, "source_url": row.get("source_url"),
                        "methodology_url": row.get("methodology_url"),
                        "license": row.get("license"), "fetch_utc": row.get("fetch_utc"),
                        "rows": row.get("rows"), "frequency": row.get("frequency"),
                        "units": row.get("units")}
    return narrow


def wdi_keys(role: str) -> set[tuple[str, int]]:
    # Explicit Parquet projection: never decode tourism values, null masks, or status.
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "year", "indicator_id"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} source key contract changed")
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate {role} country/year key")
    return {(str(country), int(year))
            for country, year in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def annual_reer() -> dict[tuple[str, int], float]:
    # Treatment may be decoded before registration.
    source = SOURCES["reer"]
    columns = ["FREQ", "EER_TYPE", "EER_BASKET", "COLLECTION", "UNIT_MEASURE",
               "REF_AREA", "period", "value", "OBS_STATUS"]
    frame = pd.read_parquet(ROOT / source["path"], columns=columns)
    if len(frame) != 1203904:
        raise RuntimeError("BIS raw row-count contract changed")
    frame = frame.loc[frame.FREQ.eq("M") & frame.EER_TYPE.eq("R") & frame.EER_BASKET.eq("B")
                      & frame.COLLECTION.eq("A") & frame.UNIT_MEASURE.eq(882)
                      & frame.REF_AREA.isin(BIS_TO_ISO3)].copy()
    if not frame.period.astype(str).str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise RuntimeError("selected BIS month keys malformed")
    if frame.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate selected BIS month key")
    frame["country_iso3"] = frame.REF_AREA.map(BIS_TO_ISO3)
    frame["year"] = frame.period.str[:4].astype(int)
    frame = frame.loc[frame.year.between(T_START - 1, T_END)].copy()
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    frame = frame.loc[np.isfinite(frame.value) & frame.value.gt(0)
                      & frame.OBS_STATUS.eq("A")]
    annual = frame.groupby(["country_iso3", "year"]).agg(
        mean_reer=("value", "mean"), months=("period", "nunique"))
    annual = annual.loc[annual.months.eq(12)]
    return {(str(country), int(year)): float(row.mean_reer)
            for (country, year), row in annual.iterrows()}


def exposure(annual: dict[tuple[str, int], float], country: str, year: int) -> tuple[float, int] | None:
    current, previous = annual.get((country, year)), annual.get((country, year - 1))
    if current is None or previous is None:
        return None
    log_points = 100.0 * math.log(current / previous)
    return log_points, int(log_points >= EVENT_MIN)


def generated_roster(annual: dict[tuple[str, int], float]) -> list[tuple[str, int]]:
    arrival_keys, gdp_keys = wdi_keys("arrivals"), wdi_keys("gdp_growth")
    candidates = [(country, year) for year in range(T_START, T_END + 1) for country in COUNTRIES
                  if exposure(annual, country, year) is not None
                  and (country, year) in arrival_keys
                  and (country, year + 1) in arrival_keys
                  and (country, year) in gdp_keys]
    counts = Counter(country for country, _ in candidates)
    return [(country, year) for country, year in candidates if counts[country] >= MIN_YEARS]


def frozen_roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("fixed key roster SHA-256 mismatch")
    raw = (ROOT / ROSTER).read_bytes()
    if not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("fixed key roster header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    if any(set(record) != {"country_iso3", "year"} for record in records):
        raise RuntimeError("key roster column contract changed")
    return [(record["country_iso3"], int(record["year"])) for record in records]


def gdp_control() -> dict[tuple[str, int], float]:
    source = SOURCES["gdp_growth"]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "year", "indicator_id", "value", "obs_status"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError("GDP growth source contract changed")
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES)].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate GDP-growth key")
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    frame = frame.loc[np.isfinite(frame.value)
                      & frame.obs_status.fillna("").astype(str).str.strip().eq("")]
    return {(str(country), int(year)): float(value)
            for country, year, value in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}


def residual_shares(panel: pd.DataFrame, *, include_baseline: bool) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    rhs = "gdp_growth + C(country_iso3) + C(year)"
    if include_baseline:
        rhs = "baseline_log_arrivals + " + rhs
    model = smf.ols("x ~ " + rhs, data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return None
    residual = np.asarray(model.fit().resid, dtype=float)
    squares = residual * residual
    total = float(squares.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * len(squares)))
    country_squares = pd.DataFrame({"country": panel.country_iso3.to_numpy(),
                                    "squared": squares}).groupby("country").squared.sum()
    return float(country_squares.max() / total), float(np.sort(squares)[-top_n:].sum() / total)


def preflight() -> dict[str, Any]:
    verify_spec()
    annual = annual_reer()
    generated = generated_roster(annual)
    if generated != frozen_roster() or len(generated) != 930:
        raise RuntimeError("treatment/key-only envelope differs from fixed roster")
    control = gdp_control()
    rows = [{"country_iso3": country, "year": year,
             "x": exposure(annual, country, year)[1],
             "gdp_growth": control[(country, year)]}
            for country, year in generated if (country, year) in control]
    panel = pd.DataFrame(rows)
    shares = residual_shares(panel, include_baseline=False)
    if shares is None:
        raise RuntimeError("preflight exposure is not identifiable")
    events = panel.loc[panel.x.eq(1)]
    if len(panel) != 930 or len(events) != 118 or events.country_iso3.nunique() != 40:
        raise RuntimeError("screened treatment/GDP-control envelope changed")
    return {
        "key_rows_upper_bound": len(generated),
        "key_countries_upper_bound": len(set(country for country, _ in generated)),
        "treatment_and_gdp_control_rows": len(panel),
        "treatment_events": len(events),
        "treatment_event_countries": int(events.country_iso3.nunique()),
        "treatment_gdp_top_country_residual_x_share": shares[0],
        "treatment_gdp_top_one_percent_residual_x_share": shares[1],
        "key_roster_sha256": ROSTER_SHA,
        "tourism_values_decoded": False, "tourism_null_masks_decoded": False,
        "tourism_status_decoded": False, "outcome_complete_case_count_known": False,
    }


def registration_commit() -> str:
    files = [RUNNER, SPEC, STEELMAN, PREREG, ROSTER, TEST]
    commits = {first_addition(relative) for relative in files}
    if len(commits) != 1:
        raise RuntimeError("preregistration files lack one shared first-addition commit")
    revision = commits.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN).strip():
        raise RuntimeError("result artifacts existed in preregistration commit")
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock existed in preregistration commit")
    return revision


def lock_payload(revision: str, sources: dict[str, dict[str, Any]], key: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "preregistration_commit": revision,
        "sources": sources, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
        "key_preflight": key, "tourism_values_opened_before_lock": False,
        "tourism_null_masks_opened_before_lock": False,
        "tourism_status_opened_before_lock": False,
        "whole_fetch_manifests_copied": False,
    }


def write_source_lock(revision: str, sources: dict[str, dict[str, Any]], key: dict[str, Any]) -> None:
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(revision, sources, key), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit this lock separately before opening tourism measurements")


def check_source_lock(revision: str, sources: dict[str, dict[str, Any]],
                      key: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if not path.is_file() or json.loads(path.read_text()) != lock_payload(revision, sources, key):
        raise RuntimeError("source lock absent or changed")
    lock_commit = first_addition(LOCK)
    if lock_commit == revision or subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, lock_commit], cwd=ROOT
    ).returncode:
        raise RuntimeError("source lock did not follow preregistration")
    committed_unchanged(LOCK, lock_commit)
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN).strip():
        raise RuntimeError("result artifacts existed in source-lock commit")
    return lock_commit


def arrivals_after_lock() -> dict[tuple[str, int], float]:
    # First tourism value, null-mask and status decoding in this runner.
    source = SOURCES["arrivals"]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "year", "indicator_id", "value", "obs_status"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError("tourism source contract changed")
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES)].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate tourism key")
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    frame = frame.loc[np.isfinite(frame.value) & frame.value.gt(0)
                      & frame.obs_status.fillna("").astype(str).str.strip().eq("")]
    return {(str(country), int(year)): float(value)
            for country, year, value in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}


def build_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    annual = annual_reer()
    control = gdp_control()
    arrival = arrivals_after_lock()
    roster = frozen_roster()
    rows = []
    for country, year in roster:
        current, forward = arrival.get((country, year)), arrival.get((country, year + 1))
        growth = control.get((country, year))
        event = exposure(annual, country, year)
        if current is None or forward is None or growth is None or event is None:
            continue
        rows.append({"country_iso3": country, "year": year, "x": event[1],
                     "arrival_growth": math.log(forward / current),
                     "baseline_log_arrivals": math.log(current),
                     "gdp_growth": growth})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "arrival_growth",
                                        "baseline_log_arrivals", "gdp_growth"])
    before = len(panel)
    if before:
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    panel = panel.sort_values(["year", "country_iso3"]).reset_index(drop=True)
    events = panel.loc[panel.x.eq(1)]
    gate = {
        "key_roster_rows": len(roster), "complete_pairs_before_five_year_floor": before,
        "complete_rows": len(panel), "complete_countries": int(panel.country_iso3.nunique()) if len(panel) else 0,
        "event_rows": len(events),
        "event_countries": int(events.country_iso3.nunique()) if len(events) else 0,
        "tourism_values_decoded_after_lock": True,
    }
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["complete_rows"] < MIN_ROWS or gate["complete_countries"] < MIN_COUNTRIES
            or gate["event_rows"] < MIN_EVENTS or gate["event_countries"] < MIN_EVENT_COUNTRIES):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or material-event floor failed", "primary": None}
    shares = residual_shares(panel, include_baseline=True)
    if shares is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "post-complete-case residual exposure is not identifiable", "primary": None}
    gate["top_country_residual_x_share"], gate["top_one_percent_residual_x_share"] = shares
    if shares[0] > MAX_COUNTRY_SHARE or shares[1] > MAX_TOP_ROW_SHARE:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residual-exposure concentration gate failed", "primary": None}
    model = smf.ols(
        "arrival_growth ~ x + baseline_log_arrivals + gdp_growth + C(country_iso3) + C(year)",
        data=panel,
    )
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed-effect design is rank deficient", "primary": None}
    groups = int(panel.country_iso3.nunique())
    try:
        fit = model.fit(cov_type="cluster",
                        cov_kwds={"groups": panel.country_iso3,
                                   "use_correction": True, "df_correction": True},
                        use_t=True)
        beta, se = float(fit.params["x"]), float(fit.bse["x"])
        p = float(2 * student_t.sf(abs(beta / se), groups - 1))
        critical = float(student_t.ppf(1 - P_MAX / 2, groups - 1))
    except (ValueError, FloatingPointError, ZeroDivisionError, KeyError):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "country-cluster inference failed", "primary": None}
    if not all(math.isfinite(value) for value in (beta, se, p, critical)) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite country-cluster uncertainty", "primary": None}
    primary = {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 0.99,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
        "model_rank": int(fit.model.rank),
        "method": "country/year FE OLS, baseline arrivals and GDP controls, country-cluster CR1, Student t(G-1)",
    }
    if beta <= -MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "negative descriptive association clears the prespecified magnitude and p gate"
    elif beta >= MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite descriptive association clears the prespecified magnitude and p gate"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def payload(result: dict[str, Any], revision: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    vintages = list(SOURCES.values())
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC, "topic": "trade"},
        "preregistration": {"spec_commit": revision, "source_lock_commit": lock_commit,
                            "family_id": FAMILY, "family_size": 1,
                            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                            "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN,
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary}, "limitations": LIMITATIONS,
        "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": ID, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"],
        "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
        "primary": primary, "p_max_two_sided": P_MAX,
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "data_status": {"variables_missing": [], "input_vintages": vintages},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": vintages,
        "derived_panel": gate, "correction": CORRECTION,
    }
    card = (
        f"# Result card: {ID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Frozen preregistration: {revision}; source lock: {lock_commit}.\n\n"
        "Exposure: at least five log points of BIS broad real EER appreciation at t. "
        "Outcome: log international-arrival change from t to t+1. "
        f"Key-only upper bound: 930 rows / 62 countries. Complete pairs: "
        f"{gate['complete_rows']} / {gate['complete_countries']}.\n"
    )
    if primary is not None:
        card += (
            f"\nBeta={primary['coefficient']:+.6g} log outcome units per appreciation event; "
            f"country-cluster SE={primary['std_error']:.6g}; "
            f"two-sided t p={primary['p_value_two_sided']:.6g}; "
            f"99% CI={primary['confidence_interval']}.\n"
        )
    card += (
        "\nOne prespecified test at two-sided p<=0.01 and absolute beta>=0.03. "
        "Descriptive calibration only, without causal, policy, position, school or featured credit.\n"
    )
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    chart = {"hypothesis_id": ID, "family_id": FAMILY, "verdict": verdict,
             "primary": primary}
    coefficients = [{"term": "x", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart,
            "coefficients": coefficients}


def summary_text(result: dict[str, Any], revision: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = f"{primary['coefficient']:+.6g}" if primary else "not estimated"
    p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
    return (
        "# BIS real appreciation and international tourist arrivals: one-test result\n\n"
        f"Preregistration {revision}; source lock {lock_commit}.\n\n"
        "| Verdict | Complete pairs / countries | Appreciation events / countries | Beta | Two-sided p |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
        f"| **{result['verdict']}** | {gate['complete_rows']} / {gate['complete_countries']} | "
        f"{gate['event_rows']} / {gate['event_countries']} | {beta} | {p} |\n\n"
        "One fixed country/year FE descriptive test, with baseline arrivals and GDP-growth controls, "
        "country-cluster CR1, two-sided p<=0.01, and an absolute 0.03-log-point effect threshold. "
        "The cutoff is local rather than archive-wide selection control. "
        "No causal, policy, position, school-score, or featured credit.\n"
    )


def write_artifacts(result: dict[str, Any], revision: str, lock_commit: str) -> None:
    if (ROOT / RUN).exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("tourism result artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    parts = payload(result, revision, lock_commit, stamp)
    folder = ROOT / RUN
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(parts["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(parts["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(parts["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(parts["card"])
    (folder / "replication.py").write_text(parts["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(parts["chart"], indent=2) + "\n")
    columns = ["term", "coefficient", "std_error", "p_value_two_sided",
               "confidence_level", "confidence_interval", "n_rows", "n_countries",
               "df_inference", "model_rank", "method"]
    pd.DataFrame(parts["coefficients"], columns=columns).to_parquet(
        folder / "coefficients.parquet", index=False
    )
    (ROOT / SUMMARY).write_text(summary_text(result, revision, lock_commit))


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(actual, np.ndarray):
        actual = actual.tolist()
    if isinstance(actual, np.generic):
        actual = actual.item()
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
        if not math.isfinite(float(actual)) or not math.isclose(
            float(actual), expected, rel_tol=1e-9, abs_tol=1e-11
        ):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(result: dict[str, Any], revision: str, lock_commit: str) -> None:
    folder = ROOT / RUN
    saved = json.loads((folder / "diagnostics.json").read_text())
    parts = payload(result, revision, lock_commit, saved["run_utc"])
    equal_close(saved, parts["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), parts["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), parts["packet"], "packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), parts["chart"], "chart")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != parts["card"]
            or (folder / "replication.py").read_text() != parts["wrapper"]):
        raise AssertionError("text artifact mismatch")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                parts["coefficients"], "coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(result, revision, lock_commit):
        raise AssertionError("family summary differs from replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    for action in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        actions.add_argument(f"--{action}", action="store_true")
    args = parser.parse_args()
    sources = check_sources()
    if args.check_sources:
        print("three exact source and fetch-manifest hashes match; tourism measurements unopened")
        return 0
    key = preflight()
    if args.preflight:
        print(json.dumps(key, indent=2, sort_keys=True))
        return 0
    revision = registration_commit()
    if args.write_source_lock:
        write_source_lock(revision, sources, key)
        return 0
    lock_commit = check_source_lock(revision, sources, key)
    panel, gate = build_panel()
    result = estimate(panel, gate)
    if args.run:
        write_artifacts(result, revision, lock_commit)
        print(summary_text(result, revision, lock_commit))
    else:
        verify_artifacts(result, revision, lock_commit)
        print("exact tourism result artifact replay passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
