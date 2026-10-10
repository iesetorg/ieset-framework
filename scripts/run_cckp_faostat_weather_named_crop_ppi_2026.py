#!/usr/bin/env python3
"""Measure the frozen CCKP/weather -> subsequent named-crop FAOSTAT PPI family.

Selected measurements and flags are opened only after committed registration,
source lock, runner chronology, frozen-byte checks and source hashes pass.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import pycountry
import scipy.linalg
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_cckp_faostat_weather_named_crop_ppi_2026.py"
TEST = "tests/test_cckp_faostat_weather_named_crop_ppi_2026.py"
PREREG = "engine/audits/cckp_faostat_weather_named_crop_ppi_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/cckp_faostat_weather_named_crop_ppi_2026_key_roster.csv"
LOCK = "data/pinned_evidence/cckp_faostat_weather_named_crop_ppi_2026.manifest.json"
SOURCE_MANIFEST = "data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml"
ARCHIVE_CHECK = "engine/audits/cckp_faostat_weather_named_crop_ppi_archive_check_2026-10-10.json"
SUMMARY = "engine/audits/cckp_faostat_weather_named_crop_ppi_results_2026-10-10.md"
FAMILY = "cckp_faostat_weather_named_crop_ppi_family_2026_10_10"
SUPERSEDED_COMMIT = "278af727f3004e271b87df6d920cdb8a8fea2e11"
REGISTRATION_COMMIT = "6211f97bfa0500379572c1c192ec75003ce4bade"
SOURCE_ACQUISITION_COMMIT = "0c4d156b2565d4af1edb0a6fa6b8a33d2688973f"
SOURCE_LOCK_COMMIT = "27b2bcaa41cbaf9d205adb993e6acc9559229405"
ROSTER_SHA256 = "1653dab95b99fdd7f409811619b135af4622c90c731a72207b6c59025a167610"
SOURCES = {
    "cckp_raw": {"path": "data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json",
                 "sha256": "b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14"},
    "faostat_price_panel": {"path": "data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet",
                            "sha256": "c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c"},
    "faostat_price_archive": {"path": "data/vintages/faostat/prices@2026-05-02T212150Z.zip",
                              "sha256": "0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b"},
}
INDEX_ELEMENT, ANNUAL_MONTH = 5539, 7021
START, END = 1995, 2022
EXPOSURES = ("temperature", "precipitation")
FAMILY_SIZE = 118
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
MEANINGFUL_BETA = 0.02
ALLOWED_FLAGS = {"A", "E", "X"}
MIN_ROWS, MIN_COUNTRIES = 500, 30
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 100, 20
MIN_COUNTRY_YEARS = 5
MAX_ABS_GROWTH = 1.0
MAX_COUNTRY_EXPOSURE_SHARE = 0.20
LIMITATIONS = [
    "Annual national CCKP weather does not isolate crop growing regions or seasons.",
    "Nominal local-currency farm-gate PPI is not farm income, real producer prices, or food consumer-price inflation.",
    "Inflation, exchange rates, market policy, imports, demand, storage, crop substitution and reporting may confound the association.",
    "The selected FAOSTAT parquet lacks a tracked archive-to-parquet transformation; selected rows are checked against the pinned archive.",
    "The 118 tests are correlated and one Bonferroni correction does not adjust the wider IESET research search.",
    "No causal, policy, school, position, or featured credit is assigned.",
]
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "featured_eligible": False}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(path: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if not commits:
        raise RuntimeError(f"no committed first addition: {path}")
    return commits[-1]


def ancestor(earlier: str, later: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", earlier, later],
                          cwd=ROOT, capture_output=True).returncode == 0


def frozen(path: str, revision: str) -> None:
    file = ROOT / path
    if not file.is_file() or file.read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen-byte mismatch: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen file: {path}")


def source_path(source_root: Path, role: str) -> Path:
    return source_root / SOURCES[role]["path"]


def case_id(code: int, exposure: str) -> str:
    return f"cckp_faostat_crop{code}_{exposure}_forward_ppi_2026"


def case_paths(code: int, exposure: str) -> tuple[str, str, str]:
    ident = case_id(code, exposure)
    return (f"hypotheses/growth/{ident}.yaml",
            f"hypotheses/steelman/{ident}.md", f"engine/runs/{ident}")


def roster_rows() -> dict[int, list[tuple[str, int]]]:
    rows: dict[int, list[tuple[str, int]]] = defaultdict(list)
    with (ROOT / ROSTER).open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows[int(row["item_code"])].append((row["country_iso3"], int(row["exposure_year"])))
    if len(rows) != 59:
        raise RuntimeError("registered item count changed")
    for code, entries in rows.items():
        if (len(entries) < 1300 or len({c for c, _ in entries}) < 55 or
                len(entries) != len(set(entries)) or
                entries != sorted(entries) or
                any(not START <= year <= END for _, year in entries)):
            raise RuntimeError(f"invalid frozen key roster for item {code}")
    if list(rows) != sorted(rows):
        raise RuntimeError("item roster order changed")
    return dict(rows)


def check_custody(source_root: Path) -> dict[int, list[tuple[str, int]]]:
    """Source and Git checks, with no Value/Flag/weather measurement access."""
    if not (ancestor(SOURCE_ACQUISITION_COMMIT, SUPERSEDED_COMMIT) and
            ancestor(SUPERSEDED_COMMIT, REGISTRATION_COMMIT) and
            ancestor(REGISTRATION_COMMIT, SOURCE_LOCK_COMMIT)):
        raise RuntimeError("acquisition / supersession / registration / source-lock chronology failed")
    if first_addition(SOURCE_MANIFEST) != git("rev-parse", SOURCE_ACQUISITION_COMMIT).decode().strip():
        raise RuntimeError("CCKP acquisition first-addition chronology failed")
    frozen(SOURCE_MANIFEST, SOURCE_ACQUISITION_COMMIT)
    for path in (PREREG, ROSTER):
        if first_addition(path) != REGISTRATION_COMMIT:
            raise RuntimeError(f"registration first-addition chronology failed: {path}")
        frozen(path, REGISTRATION_COMMIT)
    if sha256(ROOT / ROSTER) != ROSTER_SHA256:
        raise RuntimeError("roster hash mismatch")
    if first_addition(LOCK) != git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip():
        raise RuntimeError("source-lock first-addition chronology failed")
    if subprocess.run(["git", "cat-file", "-e", f"{REGISTRATION_COMMIT}:{LOCK}"],
                      cwd=ROOT, capture_output=True).returncode == 0:
        raise RuntimeError("source lock existed at registration")
    frozen(LOCK, SOURCE_LOCK_COMMIT)
    lock = json.loads((ROOT / LOCK).read_text())
    if (lock.get("family_id") != FAMILY or
            lock.get("registration_commit") != REGISTRATION_COMMIT or
            lock.get("source_acquisition_commit") != SOURCE_ACQUISITION_COMMIT or
            lock.get("superseded_prevalue_registration_commit") != SUPERSEDED_COMMIT or
            lock.get("roster_sha256") != ROSTER_SHA256 or
            lock.get("sources") != SOURCES or
            lock.get("selection", {}).get("family_size") != FAMILY_SIZE):
        raise RuntimeError("source-lock content mismatch")
    roster = roster_rows()
    if len(roster) * len(EXPOSURES) != FAMILY_SIZE or P_MAX != 0.01 / 118:
        raise RuntimeError("registered family denominator changed")
    for code, entries in roster.items():
        countries = sorted({country for country, _ in entries})
        for exposure in EXPOSURES:
            spec_path, steelman_path, run_path = case_paths(code, exposure)
            for path in (spec_path, steelman_path):
                if first_addition(path) != REGISTRATION_COMMIT:
                    raise RuntimeError(f"spec first-addition chronology failed: {path}")
                frozen(path, REGISTRATION_COMMIT)
            if git("ls-tree", "-r", "--name-only", REGISTRATION_COMMIT, "--", run_path).strip():
                raise RuntimeError(f"run existed at preregistration: {run_path}")
            spec = yaml.safe_load((ROOT / spec_path).read_text())
            threshold = spec.get("falsification", {}).get("threshold", {})
            if (spec.get("hypothesis_id") != case_id(code, exposure) or
                    spec.get("status") != "pre_registered" or
                    spec.get("claim_direction") != "+" or
                    spec.get("sample", {}).get("countries") != countries or
                    spec.get("scope", {}).get("countries") != countries or
                    spec.get("steelman") != steelman_path or
                    spec.get("covers_claims") != [] or
                    spec.get("linked_hypotheses") != [] or
                    threshold.get("family_id") != FAMILY or
                    threshold.get("family_size") != FAMILY_SIZE or
                    threshold.get("p_max_two_sided_bonferroni") != P_MAX or
                    threshold.get("roster_sha256") != ROSTER_SHA256 or
                    threshold.get("source_lock_path") != LOCK or
                    threshold.get("item_code") != code or
                    threshold.get("meaningful_beta_min_abs") != MEANINGFUL_BETA or
                    threshold.get("max_top_country_residualized_exposure_share") != MAX_COUNTRY_EXPOSURE_SHARE):
                raise RuntimeError(f"registered specification mismatch: {case_id(code, exposure)}")
    runner_commit = first_addition(RUNNER)
    if not ancestor(SOURCE_LOCK_COMMIT, runner_commit) or runner_commit == git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip():
        raise RuntimeError("runner was not committed after source lock")
    frozen(RUNNER, runner_commit)
    if first_addition(TEST) != runner_commit:
        raise RuntimeError("test first-addition differs from runner commit")
    frozen(TEST, runner_commit)
    for role, pin in SOURCES.items():
        path = source_path(source_root, role)
        if not path.is_file() or sha256(path) != pin["sha256"]:
            raise RuntimeError(f"pinned source missing or hash mismatch: {role}")
    return roster


def iso3(m49: object) -> str | None:
    try:
        country = pycountry.countries.get(numeric=str(m49).strip().replace("'", "").zfill(3))
        return country.alpha_3 if country else None
    except (TypeError, AttributeError):
        return None


def finite(value: object) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def canon_number(value: object) -> str:
    if value is None or str(value).strip() == "":
        return ""
    number = float(value)
    if math.isnan(number):
        return ""
    if not math.isfinite(number):
        raise RuntimeError("nonfinite archive/parquet numeric source value")
    return number.hex()


def archive_parquet_check(source_root: Path, items: set[int]) -> dict:
    """After custody, compare every selected item/index/annual archive row."""
    archive = source_path(source_root, "faostat_price_archive")
    if not zipfile.is_zipfile(archive):
        raise RuntimeError("pinned FAOSTAT archive is not ZIP")
    original = {}
    with zipfile.ZipFile(archive) as handle:
        names = [name for name in handle.namelist() if name.endswith("All_Data_(Normalized).csv")]
        if len(names) != 1:
            raise RuntimeError(f"unexpected FAOSTAT archive members: {names}")
        with handle.open(names[0]) as binary:
            reader = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            for row in reader:
                if (int(row["Item Code"]) not in items or
                        int(row["Element Code"]) != INDEX_ELEMENT or
                        int(row["Months Code"]) != ANNUAL_MONTH):
                    continue
                key = (row["Area Code (M49)"].strip(), int(row["Item Code"]),
                       int(row["Element Code"]), int(row["Year"]), int(row["Months Code"]))
                if key in original:
                    raise RuntimeError(f"duplicate selected archive key: {key}")
                original[key] = (canon_number(row["Value"]), row["Flag"].strip(), row["Unit"].strip())
    columns = ["Area Code (M49)", "Item Code", "Element Code", "Year",
               "Months Code", "Value", "Flag", "Unit"]
    frame = pd.read_parquet(source_path(source_root, "faostat_price_panel"), columns=columns)
    frame = frame.loc[(frame["Item Code"].isin(items)) &
                      (frame["Element Code"] == INDEX_ELEMENT) &
                      (frame["Months Code"] == ANNUAL_MONTH)]
    derived = {}
    for m49, item, element, year, month, value, flag, unit in frame.itertuples(index=False, name=None):
        key = (str(m49).strip(), int(item), int(element), int(year), int(month))
        if key in derived:
            raise RuntimeError(f"duplicate selected parquet key: {key}")
        derived[key] = (canon_number(value), "" if flag is None else str(flag).strip(),
                        "" if unit is None else str(unit).strip())
    if original != derived:
        missing = sorted(original.keys() - derived.keys())[:5]
        extra = sorted(derived.keys() - original.keys())[:5]
        changed = [(key, original[key], derived[key])
                   for key in sorted(original.keys() & derived.keys()) if original[key] != derived[key]][:5]
        raise RuntimeError(f"FAOSTAT archive/parquet selected rows differ: missing={missing}; extra={extra}; changed={changed}")
    digest = hashlib.sha256()
    for key, fields in sorted(original.items()):
        digest.update(json.dumps([key, fields], ensure_ascii=False, separators=(",", ":")).encode())
        digest.update(b"\n")
    return {"family_id": FAMILY, "registration_commit": REGISTRATION_COMMIT,
            "source_lock_commit": git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip(),
            "selected_item_count": len(items), "selected_archive_parquet_rows": len(original),
            "selected_key_value_flag_unit_sha256": digest.hexdigest(),
            "exact_selected_archive_parquet_match": True,
            "scope": "all registered item/index/annual rows, including non-ISO3 countries, excluded flags and years outside the outcome window",
            "limit": "Exact selected raw-cache equality does not establish upstream FAOSTAT collection accuracy or future source availability."}


def climate_departures(tas: dict, pr: dict) -> dict[int, tuple[float, float]]:
    baseline = {}
    for variable, series in (("tas", tas), ("pr", pr)):
        values = [finite(series.get(f"{year}-07")) for year in range(1961, 1991)]
        if any(value is None for value in values):
            return {}
        baseline[variable] = values
    pr_sd = statistics.stdev(baseline["pr"])
    if not math.isfinite(pr_sd) or pr_sd <= 0:
        return {}
    tas_normal, pr_normal = statistics.mean(baseline["tas"]), statistics.mean(baseline["pr"])
    result = {}
    for year in range(START, END + 1):
        tas_value, pr_value = finite(tas.get(f"{year}-07")), finite(pr.get(f"{year}-07"))
        if tas_value is not None and pr_value is not None:
            result[year] = (abs(tas_value - tas_normal),
                            abs(pr_value - pr_normal) / pr_sd)
    return result


def load_values(source_root: Path, items: set[int], countries: set[str]) -> tuple[dict, dict]:
    climate = json.loads(source_path(source_root, "cckp_raw").read_text()).get("data", {})
    if set(climate) != {"tas", "pr"}:
        raise RuntimeError("CCKP response variables differ from contract")
    weather = {}
    for country in sorted(countries):
        if country in climate["tas"] and country in climate["pr"]:
            weather.update({(country, year): value for year, value in
                            climate_departures(climate["tas"][country], climate["pr"][country]).items()})
    columns = ["Area Code (M49)", "Item Code", "Element Code", "Months Code",
               "Year", "Value", "Flag"]
    frame = pd.read_parquet(source_path(source_root, "faostat_price_panel"), columns=columns)
    frame = frame.loc[(frame["Item Code"].isin(items)) &
                      (frame["Element Code"] == INDEX_ELEMENT) &
                      (frame["Months Code"] == ANNUAL_MONTH) &
                      (frame["Year"].between(START - 1, END + 1))]
    prices = {}
    for m49, item, element, month, year, value, flag in frame.itertuples(index=False, name=None):
        country = iso3(m49)
        if country not in countries:
            continue
        key = (int(item), country, int(year))
        if key in prices:
            raise RuntimeError(f"duplicate selected PPI key: {key}")
        prices[key] = (finite(value), "" if flag is None else str(flag).strip())
    return weather, prices


def item_frame(code: int, keys: list[tuple[str, int]], weather: dict, prices: dict) -> tuple[pd.DataFrame, dict]:
    records, dropped, raw_flags, admitted_flags = [], Counter(), Counter(), Counter()
    for country, year in keys:
        climate = weather.get((country, year))
        if climate is None:
            dropped["climate_baseline_or_exposure_year"] += 1
            continue
        triple = [prices.get((code, country, year + offset)) for offset in (-1, 0, 1)]
        if any(cell is None for cell in triple):
            dropped["missing_ppi_row"] += 1
            continue
        for role, cell in zip(("t_minus_1", "t", "t_plus_1"), triple):
            raw_flags[f"{role}:{cell[1] or '<blank>'}"] += 1
        if any(cell[0] is None or cell[0] <= 0 for cell in triple):
            dropped["nonpositive_or_nonfinite_ppi"] += 1
            continue
        if any(cell[1] not in ALLOWED_FLAGS for cell in triple):
            dropped["excluded_ppi_flag"] += 1
            continue
        prior = math.log(triple[1][0] / triple[0][0])
        response = math.log(triple[2][0] / triple[1][0])
        if abs(prior) > MAX_ABS_GROWTH or abs(response) > MAX_ABS_GROWTH:
            dropped["ppi_growth_bound"] += 1
            continue
        tas, pr = climate
        records.append({"country": country, "year": year, "tas": tas, "pr": pr,
                        "prior": prior, "response": response})
        for role, cell in zip(("t_minus_1", "t", "t_plus_1"), triple):
            admitted_flags[f"{role}:{cell[1]}"] += 1
    before_floor = len(records)
    by_country = Counter(record["country"] for record in records)
    records = [record for record in records if by_country[record["country"]] >= MIN_COUNTRY_YEARS]
    frame = (pd.DataFrame.from_records(records).sort_values(["year", "country"]).reset_index(drop=True)
             if records else pd.DataFrame(columns=["country", "year", "tas", "pr", "prior", "response"]))
    sample = {
        "key_rows": len(keys), "key_countries": len({c for c, _ in keys}),
        "complete_rows_before_country_floor": before_floor,
        "dropped": dict(sorted(dropped.items())),
        "dropped_by_five_year_country_floor": before_floor - len(frame),
        "valid_rows": len(frame), "valid_countries": int(frame["country"].nunique()),
        "observed_ppi_flag_counts_before_value_flag_gates": dict(sorted(raw_flags.items())),
        "admitted_ppi_flag_counts_before_country_floor": dict(sorted(admitted_flags.items())),
        "values_read_after_committed_source_lock": True,
    }
    return frame, sample


def exposure_frame(frame: pd.DataFrame, common: dict, exposure: str) -> tuple[pd.DataFrame, dict]:
    focal, other = ("tas", "pr") if exposure == "temperature" else ("pr", "tas")
    data = frame.rename(columns={focal: "x", other: "other"})[
        ["country", "year", "x", "other", "prior", "response"]].copy()
    material = data.loc[data["x"] >= 1.0]
    sample = {**common, "exposure": exposure,
              "material_exposure_rows": len(material),
              "material_exposure_countries": int(material["country"].nunique())}
    return data, sample


def fit_case(frame: pd.DataFrame, sample: dict) -> tuple[str, str, dict]:
    failed = []
    if sample["valid_rows"] < MIN_ROWS or sample["valid_countries"] < MIN_COUNTRIES:
        failed.append("complete_case_floor")
    if (sample["material_exposure_rows"] < MIN_MATERIAL_ROWS or
            sample["material_exposure_countries"] < MIN_MATERIAL_COUNTRIES):
        failed.append("material_exposure_floor")
    if failed:
        return "INCONCLUSIVE", ", ".join(failed), {"gates_failed": failed}
    nuisance = patsy.dmatrix("1 + other + prior + C(country) + C(year)", frame,
                             return_type="dataframe").to_numpy(dtype=float)
    x = frame["x"].to_numpy(dtype=float)
    y = frame["response"].to_numpy(dtype=float)
    n, k_nuisance = nuisance.shape
    q, r = scipy.linalg.qr(nuisance, mode="economic", check_finite=False)
    diagonal = np.abs(np.diag(r))
    tolerance = np.finfo(float).eps * max(n, k_nuisance) * diagonal.max()
    if np.any(diagonal <= tolerance):
        return "INCONCLUSIVE", "full-rank nuisance design failed", {
            "gates_failed": ["full_rank"], "nuisance_rank": int(np.sum(diagonal > tolerance))}
    x_resid = x - q @ (q.T @ x)
    y_resid = y - q @ (q.T @ y)
    x_ss = float(x_resid @ x_resid)
    if not math.isfinite(x_ss) or x_ss <= (
            np.finfo(float).eps * max(n, k_nuisance + 1) * max(1.0, float(np.linalg.norm(x)))) ** 2:
        return "INCONCLUSIVE", "full-rank focal exposure failed", {"gates_failed": ["full_rank"]}
    by_country = defaultdict(float)
    for country, square in zip(frame["country"], x_resid * x_resid):
        by_country[country] += float(square)
    top_share = max(by_country.values()) / x_ss
    sample["top_country_residualized_exposure_share"] = top_share
    if top_share > MAX_COUNTRY_EXPOSURE_SHARE:
        return "INCONCLUSIVE", "top-country residualized exposure cap failed", {
            "gates_failed": ["residual_concentration"],
            "top_country_residualized_exposure_share": top_share}
    beta = float(x_resid @ y_resid / x_ss)
    errors = y_resid - beta * x_resid
    scores = defaultdict(float)
    for country, score in zip(frame["country"], x_resid * errors):
        scores[country] += float(score)
    groups, k = sample["valid_countries"], k_nuisance + 1
    if n <= k:
        return "INCONCLUSIVE", "degrees of freedom failed", {"gates_failed": ["full_rank"]}
    cr1 = groups / (groups - 1) * (n - 1) / (n - k)
    variance = cr1 * math.fsum(score * score for score in scores.values()) / (x_ss * x_ss)
    se = math.sqrt(variance) if variance >= 0 and math.isfinite(variance) else float("nan")
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return "INCONCLUSIVE", "country-cluster uncertainty not positive finite", {
            "gates_failed": ["uncertainty"]}
    df = groups - 1
    p = float(2 * student_t.sf(abs(beta / se), df))
    critical = float(student_t.ppf(1 - P_MAX / 2, df))
    result = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
              "confidence_level": 1 - P_MAX,
              "confidence_interval": [beta - critical * se, beta + critical * se],
              "n_rows": n, "n_countries": groups, "df_inference": df,
              "model_rank": k, "top_country_residualized_exposure_share": top_share,
              "method": "country/exposure-year FE OLS; prior PPI growth and other-weather control; country CR1; Student t(G-1)"}
    if beta >= MEANINGFUL_BETA and p <= P_MAX:
        return "SUPPORTED", "positive magnitude and 118-test family cutoff pass", result
    if beta <= -MEANINGFUL_BETA and p <= P_MAX:
        return "REFUTED", "negative magnitude and 118-test family cutoff pass", result
    return "PARTIAL", "estimable result misses registered sign, magnitude or family cutoff", result


def artifacts(code: int, label: str, exposure: str, sample: dict, verdict: str,
              reason: str, result: dict, run_utc: str) -> dict[str, bytes]:
    ident = case_id(code, exposure)
    spec_path, steelman_path, run_dir = case_paths(code, exposure)
    diagnostic = {"hypothesis_id": ident, "item_code": code, "item_label": label,
                  "family_id": FAMILY, "verdict": verdict, "verdict_label": verdict,
                  "verdict_reason": reason, "run_utc": run_utc, "runner": RUNNER,
                  "preregistration_commit": REGISTRATION_COMMIT,
                  "source_lock_commit": git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip(),
                  "source_lock": LOCK, "template": "panel_fe",
                  "preflight": sample, "primary": result,
                  "p_max_two_sided_bonferroni": P_MAX,
                  "meaningful_beta_min_abs": MEANINGFUL_BETA,
                  "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                  "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": ident, "run_utc": run_utc, "runner": RUNNER,
                "preregistration_commit": REGISTRATION_COMMIT,
                "source_lock_commit": git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip(),
                "source_lock": LOCK, "status": verdict,
                "vintages": list(SOURCES.values()), "derived_panel": sample,
                "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": run_utc,
              "hypothesis": {"id": ident, "path": spec_path, "topic": "growth"},
              "preregistration": {"spec_commit": REGISTRATION_COMMIT,
                                  "source_lock_commit": git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip(),
                                  "family_id": FAMILY, "family_size": FAMILY_SIZE,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA256,
                                  "steelman": steelman_path},
              "reproduction": {"runner": RUNNER, "run_dir": run_dir,
                               "command": f"python3 {RUNNER} --source-root <local raw cache> --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": SOURCES, "sample": sample},
              "results": {"primary": result}, "limitations": LIMITATIONS,
              "correction": CORRECTION}
    if verdict == "INCONCLUSIVE":
        finding = f"**INCONCLUSIVE.** {reason}. No directional estimate is graded."
    else:
        finding = (f"**{verdict}.** Frozen descriptive beta {result['coefficient']:+.5f} "
                   f"later PPI log growth per unit {exposure} departure "
                   f"(country CR1 SE {result['std_error']:.5f}; two-sided "
                   f"p={result['p_value_two_sided']:.5g}; {result['n_rows']} country-years, "
                   f"{result['n_countries']} countries). {reason}.")
    flag_counts = sample["admitted_ppi_flag_counts_before_country_floor"]
    flag_text = ", ".join(f"{key}={value}" for key, value in flag_counts.items()) or "none"
    dropped = ", ".join(f"{key}={value}" for key, value in sample["dropped"].items()) or "none"
    card = (f"# {label} ({code}) subsequent producer price index and annual {exposure} departure\n\n"
            f"{finding}\n\n"
            f"Source-key rows {sample['key_rows']}; complete rows before five-year-country floor "
            f"{sample['complete_rows_before_country_floor']}; final rows {sample['valid_rows']}. "
            f"Attrition: {dropped}; five-year-country floor removed "
            f"{sample['dropped_by_five_year_country_floor']} rows.\n\n"
            f"Admitted FAOSTAT PPI input flags before country floor: {flag_text}. "
            "A=official, E=estimated, X=external; other flags excluded. "
            "Per-role observed flag counts, including excluded flags, are in diagnostics.\n\n"
            f"One of {FAMILY_SIZE} correlated named-crop/weather tests under one "
            f"two-sided 0.01/{FAMILY_SIZE} cutoff. The local-currency nominal "
            "farm-gate PPI is neither farm income nor food CPI. Annual national "
            "weather misses crop zones and seasons. Descriptive only; zero causal, "
            "policy, position, school and featured credit. Exact replay needs "
            "the hash-pinned local source cache.\n")
    replication = ("#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\n"
                   "source = os.environ.get('IESET_RAW_ROOT')\n"
                   "if not source:\n    raise SystemExit('set IESET_RAW_ROOT to the matching local raw cache')\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', "
                   "'--source-root', source, '--verify']))\n")
    return {"manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "diagnostics.json": (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(),
            "result_card.md": card.encode(),
            "hypothesis.yaml": (ROOT / spec_path).read_bytes(),
            "replication.py": replication.encode()}


def summary_bytes(summaries: list[dict], run_utc: str) -> bytes:
    counts = Counter(row["verdict"] for row in summaries)
    lines = ["# CCKP annual weather and FAOSTAT named-crop producer PPI — results", "",
             f"Run UTC: {run_utc}. Registration `{REGISTRATION_COMMIT}`; source lock "
             f"`{git('rev-parse', SOURCE_LOCK_COMMIT).decode().strip()}`. "
             f"Source-key roster `{ROSTER}` ({ROSTER_SHA256}).",
             f"All {FAMILY_SIZE} registered cells remain in the single two-sided Bonferroni denominator "
             f"(family α={FAMILY_ALPHA}; p≤{P_MAX:.12g}), including INCONCLUSIVE cases.",
             f"Verdicts: {dict(sorted(counts.items()))}.", "",
             "| Item | Exposure | Verdict | Key rows | Complete rows | Countries | Material rows | Material countries | Beta | p | Gate/interpretation |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for row in summaries:
        result = row["result"]
        lines.append(
            f"| {row['label']} ({row['code']}) | {row['exposure']} | {row['verdict']} | "
            f"{row['sample']['key_rows']} | {row['sample']['valid_rows']} | "
            f"{row['sample']['valid_countries']} | {row['sample']['material_exposure_rows']} | "
            f"{row['sample']['material_exposure_countries']} | "
            f"{result['coefficient']:+.5f} | {result['p_value_two_sided']:.5g} | {row['reason']} |"
            if "coefficient" in result else
            f"| {row['label']} ({row['code']}) | {row['exposure']} | {row['verdict']} | "
            f"{row['sample']['key_rows']} | {row['sample']['valid_rows']} | "
            f"{row['sample']['valid_countries']} | {row['sample']['material_exposure_rows']} | "
            f"{row['sample']['material_exposure_countries']} | — | — | {row['reason']} |"
        )
    lines += ["", "## Interpretation and custody", "",
              "The selected raw FAOSTAT archive and derived parquet match exactly on every registered item/index/annual row, including value, flag and unit; see the archive check JSON. The parquet transformation remains untracked.",
              "All individual cells disclose key-to-complete-case attrition and admitted/excluded PPI flag counts in their diagnostics. These annual national weather and nominal local-currency farm-gate PPI associations are correlated and descriptive. PPI growth is not farm income, real price growth, or food consumer-price inflation. Country/year effects do not eliminate inflation, exchange-rate, trade, demand, market-policy or reporting confounding. The family correction does not adjust the wider IESET research search. Zero causal, policy, school, position and featured credit.", ""]
    return "\n".join(lines).encode()


def run(source_root: Path, verify: bool) -> None:
    roster = check_custody(source_root)
    items = set(roster)
    archive_check = archive_parquet_check(source_root, items)
    weather, prices = load_values(source_root, items, {c for entries in roster.values() for c, _ in entries})
    first_dir = ROOT / case_paths(next(iter(roster)), EXPOSURES[0])[2]
    run_utc = (json.loads((first_dir / "diagnostics.json").read_text())["run_utc"]
               if verify else datetime.now(timezone.utc).isoformat(timespec="seconds"))
    # Human labels are taken from the frozen preregistered item census, not
    # selected numeric observations.
    registered_labels = {}
    for line in (ROOT / PREREG).read_text().splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) >= 7 and fields[1].isdigit():
            registered_labels[int(fields[1])] = fields[2]
    if set(registered_labels) != items:
        raise RuntimeError("preregistered item-label census mismatch")
    summaries = []
    count = 0
    for code, keys in roster.items():
        common_frame, common_sample = item_frame(code, keys, weather, prices)
        for exposure in EXPOSURES:
            count += 1
            frame, sample = exposure_frame(common_frame, common_sample, exposure)
            verdict, reason, result = fit_case(frame, sample)
            produced = artifacts(code, registered_labels[code], exposure, sample,
                                 verdict, reason, result, run_utc)
            directory = ROOT / case_paths(code, exposure)[2]
            if verify:
                mismatch = [name for name, content in produced.items()
                            if not (directory / name).is_file() or
                            (directory / name).read_bytes() != content]
                if mismatch:
                    raise RuntimeError(f"{case_id(code, exposure)} exact replay mismatch: {mismatch}")
            else:
                directory.mkdir(parents=True, exist_ok=False)
                for name, content in produced.items():
                    (directory / name).write_bytes(content)
            summaries.append({"code": code, "label": registered_labels[code],
                              "exposure": exposure, "verdict": verdict, "reason": reason,
                              "sample": sample, "result": result})
            print(f"{count}/{FAMILY_SIZE} {case_id(code, exposure)} {verdict} "
                  f"{sample['valid_rows']} rows", flush=True)
    expected = {
        ARCHIVE_CHECK: (json.dumps(archive_check, indent=2, sort_keys=True) + "\n").encode(),
        SUMMARY: summary_bytes(summaries, run_utc),
    }
    for name, content in expected.items():
        path = ROOT / name
        if verify:
            if not path.is_file() or path.read_bytes() != content:
                raise RuntimeError(f"exact family-level replay mismatch: {name}")
        else:
            if path.exists():
                raise RuntimeError(f"family-level result already exists: {name}")
            path.write_bytes(content)
    print(("Exact replay passed" if verify else "Measured") +
          f" for {FAMILY_SIZE} cells; verdicts {dict(Counter(x['verdict'] for x in summaries))}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-custody", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    if args.check_custody:
        roster = check_custody(args.source_root)
        print(f"Committed custody and source hashes pass for {len(roster)} named crops")
    else:
        run(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
