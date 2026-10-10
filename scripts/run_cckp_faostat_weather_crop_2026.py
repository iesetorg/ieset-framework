#!/usr/bin/env python3
"""Measure the frozen 56-cell CCKP weather / FAOSTAT crop family.

The source cache is external to Git. This runner refuses to inspect selected
measurements until the registered specifications and subsequent source lock are
committed, unchanged, and matched to every local source file by SHA-256.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
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
RUNNER = "scripts/run_cckp_faostat_weather_crop_2026.py"
PREREG = "engine/audits/cckp_faostat_weather_crop_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/cckp_faostat_weather_crop_2026_key_roster.csv"
LOCK = "data/pinned_evidence/cckp_faostat_weather_crop_2026.manifest.json"
SOURCE_MANIFEST = "data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml"
SUMMARY = "engine/audits/cckp_faostat_weather_crop_results_2026-10-10.md"
FAMILY = "cckp_faostat_weather_crop_family_2026_10_10"
REGISTRATION_COMMIT = "523795918ea67425a4fb0e7e2db679f3357de071"
SOURCE_ACQUISITION_COMMIT = "0c4d156b2565d4af1edb0a6fa6b8a33d2688973f"
SOURCE_LOCK_COMMIT = "27c84ae35afd819dcbe26a1be1674711d32534ad"
ROSTER_SHA256 = "0df474914d96a59e7fe16d53c33210cc9a46be63b0f56c661efa864a5cbeb5dc"
SOURCES = {
    "cckp_raw": {"path": "data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json", "sha256": "b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14"},
    "faostat_crop_panel": {"path": "data/vintages/faostat/faostat_prod_All_Data_(Normalized)@2026-05-02T212007Z.parquet", "sha256": "02d93061467ca6e9a6cc738ba72702271d26abbaa21480c51d04d29b1017734a"},
    "faostat_crop_archive": {"path": "data/vintages/faostat/Production_Crops_Livestock_E_All_Data_(Normalized)@2026-05-02T211649Z.zip", "sha256": "c5835418c18f9322e7decbd6800f93a216eaae3cdfa31acb08f0518c0c6d6853"},
    "faostat_flag_legend": {"path": "data/vintages/faostat/faostat_prod_Flags@2026-05-02T212007Z.parquet", "sha256": "c9c44507c716b6fe7bd22d68febe1752c3cb4d08c11d62e2311092a8bacc2a6d"},
}
ITEMS = {
    "cereals": 1717, "roots": 1720, "pulses": 1726, "oilcrops": 1732,
    "wheat": 15, "rice": 27, "maize": 56, "potatoes": 116,
    "cassava": 125, "soybean": 236, "sugarcane": 156,
    "coffee": 656, "cotton": 328, "tomatoes": 388,
}
MARGINS = {"yield": (5412, "kg/ha"), "area": (5312, "ha")}
EXPOSURES = ("temperature", "precipitation")
CASES = [(item, margin, exposure) for item in ITEMS for margin in MARGINS for exposure in EXPOSURES]
ALLOWED_FLAGS = {"A", "E", "X"}
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MEANINGFUL_BETA = 0.02
MIN_ROWS, MIN_COUNTRIES = 500, 30
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 100, 20
MIN_COUNTRY_YEARS = 5
MAX_ABS_GROWTH = 1.0
MAX_COUNTRY_EXPOSURE_SHARE = 0.20
LIMITATIONS = [
    "Country-average annual weather does not measure crop-zone or growing-season exposure.",
    "Crop mix, irrigation, technology, reporting and other shocks may confound these associations.",
    "FAOSTAT group and named-crop cells overlap; the 56 cells are correlated and are not independent replications.",
    "FAOSTAT's locally derived parquet lacks a tracked archive-to-parquet transformation.",
    "The 0.01/56 cutoff does not adjust the wider IESET research selection.",
    "No causal, policy, school, position or featured credit is assigned.",
]
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "featured_eligible": False}


def case_id(case: tuple[str, str, str]) -> str:
    item, margin, exposure = case
    return f"cckp_faostat_{item}_{exposure}_{margin}_2026"


def case_paths(case: tuple[str, str, str]) -> tuple[str, str, str]:
    ident = case_id(case)
    return (f"hypotheses/growth/{ident}.yaml",
            f"hypotheses/steelman/{ident}.md", f"engine/runs/{ident}")


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
    target = ROOT / path
    if not target.is_file() or target.read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen byte mismatch: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen path: {path}")


def source_path(source_root: Path, role: str) -> Path:
    return source_root / SOURCES[role]["path"]


def roster_rows() -> dict[tuple[str, str], list[tuple[str, int]]]:
    rows = defaultdict(list)
    with (ROOT / ROSTER).open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["item"], row["margin"])
            rows[key].append((row["country_iso3"], int(row["outcome_year"])))
    if set(rows) != {(item, margin) for item in ITEMS for margin in MARGINS}:
        raise RuntimeError("roster item/margin grid differs from registration")
    for key, entries in rows.items():
        if len(entries) != len(set(entries)) or any(not 1963 <= year <= 2024 for _, year in entries):
            raise RuntimeError(f"duplicate or invalid roster keys: {key}")
    return rows


def check_custody(source_root: Path) -> dict[tuple[str, str], list[tuple[str, int]]]:
    """All checks here avoid reading selected values, flags, or null masks."""
    if len(CASES) != 56 or P_MAX != 0.01 / 56:
        raise RuntimeError("family grid or denominator changed")
    reg = REGISTRATION_COMMIT
    if not ancestor(SOURCE_ACQUISITION_COMMIT, reg) or not ancestor(reg, SOURCE_LOCK_COMMIT):
        raise RuntimeError("source acquisition / registration / lock chronology failed")
    if first_addition(SOURCE_MANIFEST) != git("rev-parse", SOURCE_ACQUISITION_COMMIT).decode().strip():
        raise RuntimeError("source acquisition manifest chronology failed")
    frozen(SOURCE_MANIFEST, SOURCE_ACQUISITION_COMMIT)
    for path in (PREREG, ROSTER):
        if first_addition(path) != reg:
            raise RuntimeError(f"preregistration chronology failed: {path}")
        frozen(path, reg)
    if sha256(ROOT / ROSTER) != ROSTER_SHA256:
        raise RuntimeError("key roster hash mismatch")
    if first_addition(LOCK) != git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip():
        raise RuntimeError("source lock was not first added in the lock commit")
    if subprocess.run(["git", "cat-file", "-e", f"{reg}:{LOCK}"],
                      cwd=ROOT, capture_output=True).returncode == 0:
        raise RuntimeError("source lock already existed at registration")
    frozen(LOCK, SOURCE_LOCK_COMMIT)
    lock = json.loads((ROOT / LOCK).read_text())
    if (lock.get("family_id") != FAMILY or lock.get("registration_commit") != reg or
            lock.get("source_acquisition_commit") != SOURCE_ACQUISITION_COMMIT or
            lock.get("roster_sha256") != ROSTER_SHA256 or lock.get("sources") != SOURCES):
        raise RuntimeError("source lock content differs from the fixed contract")
    roster = roster_rows()
    for case in CASES:
        spec_path, steelman_path, run_path = case_paths(case)
        for path in (spec_path, steelman_path):
            if first_addition(path) != reg:
                raise RuntimeError(f"specification chronology failed: {path}")
            frozen(path, reg)
        if git("ls-tree", "-r", "--name-only", reg, "--", run_path).strip():
            raise RuntimeError(f"run existed before registration: {run_path}")
        spec = yaml.safe_load((ROOT / spec_path).read_text())
        item, margin, exposure = case
        threshold = spec.get("falsification", {}).get("threshold", {})
        countries = sorted({country for country, _ in roster[(item, margin)]})
        if (spec.get("hypothesis_id") != case_id(case) or spec.get("status") != "pre_registered" or
                spec.get("claim_direction") != "-" or spec.get("sample", {}).get("countries") != countries or
                spec.get("scope", {}).get("countries") != countries or spec.get("steelman") != steelman_path or
                spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != [] or
                threshold.get("family_id") != FAMILY or threshold.get("family_size") != 56 or
                threshold.get("p_max_two_sided_bonferroni") != P_MAX or
                threshold.get("roster_sha256") != ROSTER_SHA256 or
                threshold.get("source_lock_path") != LOCK or
                threshold.get("meaningful_beta_min_abs") != MEANINGFUL_BETA or
                threshold.get("max_top_country_residualized_exposure_share") != MAX_COUNTRY_EXPOSURE_SHARE):
            raise RuntimeError(f"registered specification mismatch: {case_id(case)}")
    runner_commit = first_addition(RUNNER)
    if runner_commit == git("rev-parse", SOURCE_LOCK_COMMIT).decode().strip() or not ancestor(SOURCE_LOCK_COMMIT, runner_commit):
        raise RuntimeError("runner was not committed after source lock")
    frozen(RUNNER, runner_commit)
    for role, pinned in SOURCES.items():
        path = source_path(source_root, role)
        if not path.is_file() or sha256(path) != pinned["sha256"]:
            raise RuntimeError(f"pinned source missing or hash mismatch: {role}")
    return roster


def iso3(m49: object) -> str | None:
    try:
        country = pycountry.countries.get(numeric=str(m49).strip().replace("'", "").zfill(3))
        return country.alpha_3 if country is not None else None
    except (TypeError, AttributeError):
        return None


def finite(value: object) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def selected_crop(crops: dict, item: int, element: int, country: str, year: int,
                  unit: str) -> tuple[float, str] | None:
    cell = crops.get((item, element, country, year))
    if cell is None:
        return None
    value, flag, actual_unit = cell
    if value is None or value <= 0 or flag not in ALLOWED_FLAGS or actual_unit != unit:
        return None
    return (value, flag)


def climate_departures(tas_series: dict, pr_series: dict) -> dict[int, tuple[float, float]]:
    """Absolute anomalies in degC and baseline sample-SD units, respectively."""
    baseline = {}
    for variable, series in (("tas", tas_series), ("pr", pr_series)):
        values = [finite(series.get(f"{year}-07")) for year in range(1961, 1991)]
        if any(value is None for value in values):
            return {}
        baseline[variable] = values
    pr_sd = statistics.stdev(baseline["pr"])
    if not math.isfinite(pr_sd) or pr_sd <= 0:
        return {}
    tas_normal = statistics.mean(baseline["tas"])
    pr_normal = statistics.mean(baseline["pr"])
    result = {}
    for year in range(1963, 2025):
        tas = finite(tas_series.get(f"{year}-07"))
        pr = finite(pr_series.get(f"{year}-07"))
        if tas is not None and pr is not None:
            result[year] = (abs(tas - tas_normal), abs(pr - pr_normal) / pr_sd)
    return result


def load_values(source_root: Path) -> tuple[dict, dict]:
    """Call only after check_custody has completed successfully."""
    climate_json = json.loads(source_path(source_root, "cckp_raw").read_text())
    data = climate_json.get("data", {})
    if set(data) != {"tas", "pr"}:
        raise RuntimeError("CCKP response variables differ from source contract")
    weather = {}
    for country in sorted(set(data["tas"]) & set(data["pr"])):
        if country == "KSV":
            continue
        for year, departure in climate_departures(data["tas"][country], data["pr"][country]).items():
            weather[(country, year)] = departure
    crop = pd.read_parquet(source_path(source_root, "faostat_crop_panel"),
                           columns=["Area Code (M49)", "Item Code", "Element Code", "Year", "Value", "Flag", "Unit"])
    crop = crop.loc[crop["Item Code"].isin(ITEMS.values()) &
                    crop["Element Code"].isin([code for code, _ in MARGINS.values()]) &
                    crop["Year"].between(1961, 2024)]
    crops = {}
    for area, item, element, year, value, flag, unit in crop.itertuples(index=False, name=None):
        country = iso3(area)
        if country is None:
            continue
        key = (int(item), int(element), country, int(year))
        if key in crops:
            raise RuntimeError(f"duplicate FAOSTAT crop key: {key}")
        crops[key] = (finite(value), str(flag).strip(), str(unit))
    return weather, crops


def case_frame(case: tuple[str, str, str], roster: dict, weather: dict,
               crops: dict) -> tuple[pd.DataFrame, dict]:
    item, margin, exposure = case
    item_code, (element, unit) = ITEMS[item], MARGINS[margin]
    rows = roster[(item, margin)]
    records, dropped, flag_counts = [], Counter(), Counter()
    for country, year in rows:
        climate = weather.get((country, year))
        if climate is None:
            dropped["climate_baseline_or_year"] += 1
            continue
        cells = [selected_crop(crops, item_code, element, country, year + offset, unit)
                 for offset in (-2, -1, 0)]
        if any(cell is None for cell in cells):
            dropped["crop_value_flag_or_unit"] += 1
            continue
        old, previous, current = cells
        prior = math.log(previous[0] / old[0])
        response = math.log(current[0] / previous[0])
        if abs(prior) > MAX_ABS_GROWTH or abs(response) > MAX_ABS_GROWTH:
            dropped["crop_growth_bound"] += 1
            continue
        tas, pr = climate
        focal, other = (tas, pr) if exposure == "temperature" else (pr, tas)
        records.append({"country": country, "year": year, "x": focal,
                        "other": other, "prior": prior, "response": response})
        for role, cell in zip(("crop_t_minus_2", "crop_t_minus_1", "crop_t"), cells):
            flag_counts[f"{role}:{cell[1]}"] += 1
    before_country_floor = len(records)
    years_by_country = Counter(row["country"] for row in records)
    records = [row for row in records if years_by_country[row["country"]] >= MIN_COUNTRY_YEARS]
    frame = (pd.DataFrame.from_records(records).sort_values(["year", "country"]).reset_index(drop=True)
             if records else pd.DataFrame(columns=["country", "year", "x", "other", "prior", "response"]))
    material = frame.loc[frame["x"].abs() >= 1.0]
    sample = {"key_rows": len(rows), "key_countries": len({country for country, _ in rows}),
              "complete_rows_before_country_floor": before_country_floor,
              "valid_rows": len(frame), "valid_countries": int(frame["country"].nunique()),
              "material_exposure_rows": len(material),
              "material_exposure_countries": int(material["country"].nunique()),
              "dropped": dict(sorted(dropped.items())),
              "admitted_crop_flag_counts_before_country_floor": dict(sorted(flag_counts.items())),
              "selected_values_read_after_committed_source_lock": True}
    return frame, sample


def fit_case(frame: pd.DataFrame, sample: dict) -> tuple[str, str, dict]:
    failures = []
    if sample["valid_rows"] < MIN_ROWS or sample["valid_countries"] < MIN_COUNTRIES:
        failures.append("complete_case_floor")
    if (sample["material_exposure_rows"] < MIN_MATERIAL_ROWS or
            sample["material_exposure_countries"] < MIN_MATERIAL_COUNTRIES):
        failures.append("material_exposure_floor")
    if failures:
        return "INCONCLUSIVE", ", ".join(failures), {"gates_failed": failures}
    nuisance = patsy.dmatrix("1 + other + prior + C(country) + C(year)", frame,
                             return_type="dataframe").to_numpy(dtype=float)
    x = frame["x"].to_numpy(dtype=float)
    y = frame["response"].to_numpy(dtype=float)
    n, k_nuisance = nuisance.shape
    q, r = scipy.linalg.qr(nuisance, mode="economic", check_finite=False)
    diagonal = np.abs(np.diag(r))
    tolerance = np.finfo(float).eps * max(n, k_nuisance) * diagonal.max()
    if np.any(diagonal <= tolerance):
        return "INCONCLUSIVE", "full-rank gate failed", {"gates_failed": ["full_rank"],
                                                            "nuisance_rank": int(np.sum(diagonal > tolerance))}
    x_resid = x - q @ (q.T @ x)
    y_resid = y - q @ (q.T @ y)
    x_ss = float(x_resid @ x_resid)
    if not math.isfinite(x_ss) or x_ss <= (np.finfo(float).eps * max(n, k_nuisance + 1) * max(1.0, float(np.linalg.norm(x)))) ** 2:
        return "INCONCLUSIVE", "full-rank focal-exposure gate failed", {"gates_failed": ["full_rank"]}
    by_country = defaultdict(float)
    for country, square in zip(frame["country"], x_resid * x_resid):
        by_country[country] += float(square)
    top_share = max(by_country.values()) / x_ss
    sample["top_country_residualized_exposure_share"] = top_share
    if top_share > MAX_COUNTRY_EXPOSURE_SHARE:
        return "INCONCLUSIVE", "one country exceeds residualized-exposure share cap", {
            "gates_failed": ["residual_concentration"],
            "top_country_residualized_exposure_share": top_share}
    beta = float(x_resid @ y_resid / x_ss)
    errors = y_resid - beta * x_resid
    cluster_scores = defaultdict(float)
    for country, score in zip(frame["country"], x_resid * errors):
        cluster_scores[country] += float(score)
    groups = sample["valid_countries"]
    k = k_nuisance + 1
    if n <= k:
        return "INCONCLUSIVE", "full-rank degrees-of-freedom gate failed", {"gates_failed": ["full_rank"]}
    cr1 = groups / (groups - 1) * (n - 1) / (n - k)
    variance = cr1 * math.fsum(score * score for score in cluster_scores.values()) / (x_ss * x_ss)
    se = math.sqrt(variance) if variance >= 0 and math.isfinite(variance) else float("nan")
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return "INCONCLUSIVE", "country-cluster uncertainty is not positive finite", {
            "gates_failed": ["uncertainty"]}
    df = groups - 1
    p = float(2 * student_t.sf(abs(beta / se), df))
    critical = float(student_t.ppf(1 - P_MAX / 2, df))
    result = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
              "confidence_level": 1 - P_MAX,
              "confidence_interval": [beta - critical * se, beta + critical * se],
              "n_rows": n, "n_countries": groups, "df_inference": df,
              "model_rank": k, "top_country_residualized_exposure_share": top_share,
              "method": "country/year FE OLS; prior growth and other-weather controls; country CR1; Student t(G-1)"}
    if beta <= -MEANINGFUL_BETA and p <= P_MAX:
        return "SUPPORTED", "negative magnitude and 56-test family cutoff pass", result
    if beta >= MEANINGFUL_BETA and p <= P_MAX:
        return "REFUTED", "positive magnitude and 56-test family cutoff pass", result
    return "PARTIAL", "estimable association does not meet the registered sign, magnitude and family cutoff", result


def artifacts(case: tuple[str, str, str], sample: dict, verdict: str, reason: str,
              result: dict, run_utc: str) -> dict[str, bytes]:
    item, margin, exposure = case
    ident = case_id(case)
    spec_path, steelman_path, run_path = case_paths(case)
    diagnostic = {"hypothesis_id": ident, "family_id": FAMILY, "verdict": verdict,
                  "verdict_label": verdict, "verdict_reason": reason, "run_utc": run_utc,
                  "runner": RUNNER, "preregistration_commit": REGISTRATION_COMMIT,
                  "source_lock_commit": SOURCE_LOCK_COMMIT, "source_lock": LOCK,
                  "template": "panel_fe", "preflight": sample, "primary": result,
                  "p_max_two_sided_bonferroni": P_MAX,
                  "meaningful_beta_min_abs": MEANINGFUL_BETA,
                  "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                  "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": ident, "run_utc": run_utc, "runner": RUNNER,
                "preregistration_commit": REGISTRATION_COMMIT,
                "source_lock_commit": SOURCE_LOCK_COMMIT, "source_lock": LOCK,
                "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": sample, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": run_utc,
              "hypothesis": {"id": ident, "path": spec_path, "topic": "growth"},
              "preregistration": {"spec_commit": REGISTRATION_COMMIT,
                                  "source_lock_commit": SOURCE_LOCK_COMMIT,
                                  "family_id": FAMILY, "family_size": len(CASES),
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA256,
                                  "steelman": steelman_path},
              "reproduction": {"runner": RUNNER, "run_dir": run_path,
                               "command": f"python3 {RUNNER} --source-root <local raw cache> --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": SOURCES, "sample": sample},
              "results": {"primary": result}, "limitations": LIMITATIONS,
              "correction": CORRECTION}
    if verdict == "INCONCLUSIVE":
        finding = f"**INCONCLUSIVE.** {reason}. No directional claim is graded."
    else:
        finding = (f"**{verdict}.** Frozen descriptive beta {result['coefficient']:+.5f} "
                   f"same-year log {margin} growth per one unit of {exposure} departure "
                   f"(country CR1 SE {result['std_error']:.5f}; two-sided "
                   f"p={result['p_value_two_sided']:.5g}; {result['n_rows']} country-years, "
                   f"{result['n_countries']} countries). {reason}.")
    flag_counts = sample["admitted_crop_flag_counts_before_country_floor"]
    flag_line = ", ".join(f"{key}={value}" for key, value in flag_counts.items()) or "none"
    card = (f"# {item} {margin} and annual {exposure} departure\n\n{finding}\n\n"
            f"Admitted FAOSTAT input flags before the country-year floor: {flag_line}. "
            "A=official, E=estimated, X=external organization; other flags excluded.\n\n"
            "One of 56 correlated CCKP/FAOSTAT cells under a shared 0.01/56 cutoff. "
            "Country-average annual weather is not crop-zone or seasonal exposure. "
            "Group and named-crop cells overlap. All results are descriptive; zero causal, "
            "policy, school, position and featured credit. Exact replay requires the matching "
            "hash-pinned local source cache.\n")
    replication = ("#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\n"
                   "root = os.environ.get('IESET_RAW_ROOT')\n"
                   "if not root:\n    raise SystemExit('set IESET_RAW_ROOT to the matching raw cache')\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', "
                   "'--source-root', root, '--verify']))\n")
    return {"manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "diagnostics.json": (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(),
            "result_card.md": card.encode(), "hypothesis.yaml": (ROOT / spec_path).read_bytes(),
            "replication.py": replication.encode()}


def summary_bytes(summaries: list[tuple[str, str, int, int, str]]) -> bytes:
    lines = ["# CCKP weather and FAOSTAT crop family — results", "",
             f"Registration commit: `{REGISTRATION_COMMIT}`; source-lock commit: `{SOURCE_LOCK_COMMIT}`.",
             "All 56 registered cells remain in the Bonferroni denominator, including inconclusive cases.", "",
             "| Cell | Verdict | Rows | Countries | Gate summary |",
             "| --- | --- | ---: | ---: | --- |"]
    for ident, verdict, n, countries, reason in summaries:
        lines.append(f"| `{ident}` | {verdict} | {n} | {countries} | {reason} |")
    lines += ["", "These correlated country-average weather and crop associations are descriptive. "
              "The broad crop groups overlap named crops; cells are not independent replications. "
              "The shared 0.01/56 cutoff does not adjust wider IESET selection. "
              "Zero causal, policy, school, position and featured credit.",
              "Raw archives and locally derived parquet are hash-pinned in an ignored cache. "
              "The archive-to-parquet transformation is not tracked. Source rights and attribution apply.", ""]
    return "\n".join(lines).encode()


def run(source_root: Path, verify: bool) -> None:
    roster = check_custody(source_root)
    weather, crops = load_values(source_root)
    first_dir = ROOT / case_paths(CASES[0])[2]
    run_utc = (json.loads((first_dir / "diagnostics.json").read_text())["run_utc"]
               if verify else datetime.now(timezone.utc).isoformat(timespec="seconds"))
    summaries = []
    for index, case in enumerate(CASES, start=1):
        frame, sample = case_frame(case, roster, weather, crops)
        verdict, reason, result = fit_case(frame, sample)
        produced = artifacts(case, sample, verdict, reason, result, run_utc)
        directory = ROOT / case_paths(case)[2]
        if verify:
            mismatch = [name for name, content in produced.items()
                        if not (directory / name).is_file() or (directory / name).read_bytes() != content]
            if mismatch:
                raise RuntimeError(f"{case_id(case)} exact replay mismatch: {mismatch}")
        else:
            directory.mkdir(parents=True, exist_ok=False)
            for name, content in produced.items():
                (directory / name).write_bytes(content)
        summaries.append((case_id(case), verdict, sample["valid_rows"],
                          sample["valid_countries"], reason))
        print(f"{index}/56 {case_id(case)} {verdict} {sample['valid_rows']} rows", flush=True)
    summary = summary_bytes(summaries)
    if verify:
        if (ROOT / SUMMARY).read_bytes() != summary:
            raise RuntimeError("family summary exact replay mismatch")
        print("Exact replay passed for 56/56 run packets and family summary")
    else:
        path = ROOT / SUMMARY
        if path.exists():
            raise RuntimeError("family result summary already exists")
        path.write_bytes(summary)
        print("Verdicts:", dict(Counter(verdict for _, verdict, _, _, _ in summaries)))


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
        print(f"Committed source custody and hashes pass for {len(roster)} crop/margin rosters")
    else:
        run(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
