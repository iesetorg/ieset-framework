#!/usr/bin/env python3
"""Frozen, value-blind registration and exact replay for the WHO AUD family.

Only --run/--verify project selected value columns, after registration and both
separately committed source locks have been verified against Git history.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import statsmodels.api as sm
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_who_aud_mortality_2016_2019.py"
FAMILY = "who_aud_mortality_2016_2019_2026"
PREREG = "engine/audits/who_aud_mortality_prereg_2026-10-10.md"
SUMMARY = "engine/audits/who_aud_mortality_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/who_aud_mortality_2016_2019_key_roster.csv"
ROSTER_SHA = "6ff9f6a09a3e41ec776bea452d56dcc8eed22928f64ced46f2e834e673ec529f"
MANIFEST_WHO = "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml"
MANIFEST_WHO_SHA = "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"
MANIFEST_WDI = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
MANIFEST_WDI_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
SOURCES = {
    "aud": {"publisher": "who_gho", "series_id": "SA_0000001462",
            "path": "data/vintages/who_gho/SA_0000001462@2026-04-30T114840Z.parquet",
            "sha256": "e102adefa334135d7c484b349262ee13340e091e60b1325c168ef7eb11fc7f13",
            "manifest": MANIFEST_WHO, "manifest_sha256": MANIFEST_WHO_SHA,
            "url": "https://ghoapi.azureedge.net/api/SA_0000001462",
            "methodology": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/alcohol-use-disorders-%2815-%29-12-month-prevalence-%28-%29-with-95-",
            "license": "CC-BY-NC-SA-3.0 IGO"},
    "suicide": {"publisher": "who_gho", "series_id": "SDGSUICIDE",
                "path": "data/vintages/who_gho/SDGSUICIDE@2026-04-30T114842Z.parquet",
                "sha256": "72bf65650b553ac47df60cd624f21ad5d12c062694b3564ebbe300275ccec937",
                "manifest": MANIFEST_WHO, "manifest_sha256": MANIFEST_WHO_SHA,
                "url": "https://ghoapi.azureedge.net/api/SDGSUICIDE",
                "methodology": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/crude-suicide-rates-%28per-100-000-population%29",
                "license": "CC-BY-NC-SA-3.0 IGO"},
    "ncd": {"publisher": "who_gho", "series_id": "NCDMORT3070",
            "path": "data/vintages/who_gho/NCDMORT3070@2026-04-30T114741Z.parquet",
            "sha256": "1ae4713b1f8244ab793787b12379a0e66d14030c5c01c152828e19224ab4f7c9",
            "manifest": MANIFEST_WHO, "manifest_sha256": MANIFEST_WHO_SHA,
            "url": "https://ghoapi.azureedge.net/api/NCDMORT3070",
            "methodology": "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/probability-of-dying-between-exact-ages-30-and-70-from-any-of-cardiovascular-disease-cancer-diabetes-or-chronic-respiratory-%28-%29/",
            "license": "CC-BY-NC-SA-3.0 IGO"},
    "gdp": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
            "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
            "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
            "manifest": MANIFEST_WDI, "manifest_sha256": MANIFEST_WDI_SHA,
            "url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD",
            "methodology": "https://data.worldbank.org/indicator/NY.GDP.PCAP.KD",
            "license": "CC BY 4.0"},
}
CASES = (
    ("who_aud_suicide_forward_2016_2019_2026", "suicide", 0.25,
     "all-age both-sex suicide deaths per 100,000"),
    ("who_aud_ncd_forward_2016_2019_2026", "ncd", 0.15,
     "probability of death from four target NCDs between ages 30 and 70, percentage points"),
)
REGIONS = ("AFR", "AMR", "EMR", "EUR", "SEAR", "WPR")
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_N = 150
MIN_REGION_N = 8
MIN_HOLDOUT_N = 100
MIN_CONCORDANT_HOLDOUTS = 5
MIN_EXPOSURE_IQR = 1.0
MAX_RESIDUAL_SHARE = 0.15
MAX_HAT_LEVERAGE = 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "The 2016 alcohol-use-disorder measure is 12-month diagnosed harmful use or dependence prevalence among adults 15+, not litres consumed or an alcohol-policy exposure.",
    "WHO models many alcohol-use-disorder observations using alcohol consumption, population structure, Muslim-population share, region, survey year, and PPP GDP; source-model dependence can bias cross-country associations.",
    "The WHO suicide and four-NCD outcomes are estimates, not uniformly complete civil-registration counts. Suicides can be underreported and four-NCD mortality excludes liver disease, injuries, and many other alcohol harms.",
    "The 2015 baseline precedes the 2016 exposure and the 2019 endpoint avoids the pandemic years, but a 2016 AUD prevalence level is not onset of alcohol exposure. Country-level prediction is not an individual-level or policy effect.",
    "The two WHO outcomes share countries and mortality-model inputs; one Bonferroni denominator covers both. No causal, policy, school, position, or featured credit is assigned.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(rel: str) -> str:
    found = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", rel).decode().splitlines()
    if len(found) != 1:
        raise RuntimeError(f"missing or ambiguous first addition: {rel}")
    return found[0]


def unchanged(rel: str, commit: str) -> None:
    if (ROOT / rel).read_bytes() != git("show", f"{commit}:{rel}"):
        raise RuntimeError(f"frozen bytes changed: {rel}")
    if git("status", "--porcelain", "--", rel).strip():
        raise RuntimeError(f"uncommitted frozen path: {rel}")


def spec_rel(case: tuple) -> str:
    return f"hypotheses/healthcare/{case[0]}.yaml"


def steel_rel(case: tuple) -> str:
    return f"hypotheses/steelman/{case[0]}.md"


def lock_rel(case: tuple) -> str:
    return f"data/pinned_evidence/{case[0]}.source.json"


def run_rel(case: tuple) -> str:
    return f"engine/runs/{case[0]}"


def checked_sources(source_root: Path) -> dict[str, Path]:
    paths = {}
    for name, source in SOURCES.items():
        path = source_root / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"pinned raw source absent or changed: {name}")
        paths[name] = path
        manifest = ROOT / source["manifest"]
        if not manifest.is_file() or sha256(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"tracked source manifest absent or changed: {name}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [row for row in entries if isinstance(row, dict)
                   and row.get("publisher") == source["publisher"]
                   and row.get("series_id") == source["series_id"]
                   and row.get("parquet_path") == source["path"]
                   and row.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"source manifest identity mismatch: {name}")
    return paths


def source_keys(paths: dict[str, Path]) -> tuple[dict[str, dict], dict[str, str]]:
    """Project dimension keys and region only; never project values or null status."""
    configs = {
        "aud": (["country_iso3", "year", "Dim1", "ParentLocationCode"],
                lambda r: r["year"] == 2016 and r["Dim1"] == "SEX_BTSX"),
        "suicide": (["country_iso3", "year", "Dim1", "Dim2", "ParentLocationCode"],
                    lambda r: r["year"] in (2012, 2015, 2019) and r["Dim1"] == "SEX_BTSX"
                    and r["Dim2"] == "AGEGROUP_YEARSALL"),
        "ncd": (["country_iso3", "year", "Dim1", "Dim2", "ParentLocationCode"],
                lambda r: r["year"] in (2012, 2015, 2019) and r["Dim1"] == "SEX_BTSX"
                and r["Dim2"] == "AGEGROUP_YEARS30-69"),
        "gdp": (["country_iso3", "year"], lambda r: r["year"] == 2015),
    }
    result = {}
    for name, (cols, choose) in configs.items():
        rows = [r for r in pq.read_table(paths[name], columns=cols).to_pylist()
                if choose(r) and r["country_iso3"]]
        keyed = {(r["country_iso3"], int(r["year"])): r for r in rows}
        if len(keyed) != len(rows):
            raise RuntimeError(f"duplicate exact source key: {name}")
        result[name] = keyed
    roster_regions = {}
    for country, year in result["aud"]:
        if all((country, y) in result[series] for series in ("suicide", "ncd")
               for y in (2012, 2015, 2019)) and (country, 2015) in result["gdp"]:
            region = result["aud"][(country, year)]["ParentLocationCode"]
            if region not in REGIONS or any(
                result[series][(country, y)]["ParentLocationCode"] != region
                for series in ("suicide", "ncd") for y in (2012, 2015, 2019)
            ):
                raise RuntimeError(f"WHO region mismatch: {country}")
            roster_regions[country] = region
    return result, roster_regions


def read_roster() -> list[dict[str, str]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("frozen source-key roster checksum mismatch")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 183 or list(rows[0]) != ["country_iso3", "who_region"]:
        raise RuntimeError("frozen roster shape mismatch")
    if [r["country_iso3"] for r in rows] != sorted({r["country_iso3"] for r in rows}):
        raise RuntimeError("frozen roster order/uniqueness mismatch")
    return rows


def preflight(paths: dict[str, Path], roster: list[dict[str, str]]) -> None:
    _keys, computed = source_keys(paths)
    if {r["country_iso3"]: r["who_region"] for r in roster} != computed:
        raise RuntimeError("frozen roster does not equal the full exact-key intersection")


def threshold(case: tuple) -> dict[str, object]:
    return {"family_id": FAMILY, "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
            "meaningful_beta_min_per_1pp_aud": case[2], "min_complete_countries": MIN_N,
            "min_complete_countries_each_who_region": MIN_REGION_N,
            "min_leave_one_region_out_countries": MIN_HOLDOUT_N,
            "min_concordant_regional_holdouts": MIN_CONCORDANT_HOLDOUTS,
            "min_aud_iqr_pp": MIN_EXPOSURE_IQR,
            "max_country_residualized_exposure_share": MAX_RESIDUAL_SHARE,
            "max_hat_leverage": MAX_HAT_LEVERAGE,
            "pretrend_year": 2012, "baseline_year": 2015, "aud_exposure_year": 2016,
            "outcome_year": 2019, "expected_key_countries": 183,
            "who_region_reference": "AFR", "who_regions": list(REGIONS),
            "source_key_roster_sha256": ROSTER_SHA, "source_lock_path": lock_rel(case),
            "source_sha256": {name: SOURCES[name]["sha256"] for name in ("aud", case[1], "gdp")},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def registration_commit() -> str:
    rels = [PREREG, RUNNER, ROSTER]
    for case in CASES:
        rels.extend((spec_rel(case), steel_rel(case)))
    additions = {first_addition(rel) for rel in rels}
    if len(additions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    commit = additions.pop()
    for rel in rels:
        unchanged(rel, commit)
    schema = json.loads(git("show", f"{commit}:schemas/hypothesis.schema.json"))
    validator = Draft202012Validator(schema)
    for case in CASES:
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if not validator.is_valid(spec) or spec.get("hypothesis_id") != case[0]:
            raise RuntimeError(f"invalid original registration: {case[0]}")
        if (spec["falsification"]["threshold"] != threshold(case)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []):
            raise RuntimeError(f"original spec differs from frozen contract: {case[0]}")
        if git("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit contains a measured run")
    return commit


def lock_payload(case: tuple, registration: str) -> dict[str, object]:
    return {"schema": "ieset-source-lock-v1", "family_id": FAMILY,
            "family_size": len(CASES), "hypothesis_id": case[0],
            "registration_commit": registration, "key_roster_sha256": ROSTER_SHA,
            "source_sha256": SOURCES["aud"]["sha256"],
            "sources": [SOURCES[name] for name in ("aud", case[1], "gdp")],
            "measurement_boundary": "All case locks precede selected values and null-mask inspection."}


def lock_commit(case: tuple, registration: str) -> str:
    rel = lock_rel(case)
    commit = first_addition(rel)
    if commit == registration:
        raise RuntimeError("source lock cannot share registration commit")
    git("merge-base", "--is-ancestor", registration, commit)
    unchanged(rel, commit)
    if json.loads((ROOT / rel).read_text()) != lock_payload(case, registration):
        raise RuntimeError(f"source lock differs from frozen contract: {case[0]}")
    return commit


def selected_values(paths: dict[str, Path], roster: list[dict[str, str]]) -> dict[str, dict]:
    allowed = {r["country_iso3"] for r in roster}
    configs = {
        "aud": (["country_iso3", "year", "Dim1", "value"],
                lambda r: r["year"] == 2016 and r["Dim1"] == "SEX_BTSX"),
        "suicide": (["country_iso3", "year", "Dim1", "Dim2", "value"],
                    lambda r: r["year"] in (2012, 2015, 2019) and r["Dim1"] == "SEX_BTSX"
                    and r["Dim2"] == "AGEGROUP_YEARSALL"),
        "ncd": (["country_iso3", "year", "Dim1", "Dim2", "value"],
                lambda r: r["year"] in (2012, 2015, 2019) and r["Dim1"] == "SEX_BTSX"
                and r["Dim2"] == "AGEGROUP_YEARS30-69"),
        "gdp": (["country_iso3", "year", "value"], lambda r: r["year"] == 2015),
    }
    result = {}
    for name, (cols, choose) in configs.items():
        rows = [r for r in pq.read_table(paths[name], columns=cols).to_pylist()
                if r["country_iso3"] in allowed and choose(r)]
        keyed = {(r["country_iso3"], int(r["year"])): r["value"] for r in rows}
        if len(keyed) != len(rows):
            raise RuntimeError(f"duplicate selected value key: {name}")
        result[name] = keyed
    return result


def number(value: object, lower: float, upper: float) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) and lower <= numeric <= upper else None


def measured_case(case: tuple, roster: list[dict[str, str]], values: dict[str, dict]) -> dict[str, object]:
    _hypothesis, outcome, magnitude, _label = case
    complete = []
    missing = Counter()
    upper = 1000.0 if outcome == "suicide" else 100.0
    for row in roster:
        country, region = row["country_iso3"], row["who_region"]
        x = number(values["aud"].get((country, 2016)), 0, 100)
        y12 = number(values[outcome].get((country, 2012)), 0, upper)
        y15 = number(values[outcome].get((country, 2015)), 0, upper)
        y19 = number(values[outcome].get((country, 2019)), 0, upper)
        gdp = number(values["gdp"].get((country, 2015)), 0.000001, 1000000)
        for label, value in (("aud", x), ("pretrend", y12), ("baseline", y15),
                             ("endpoint", y19), ("gdp", gdp)):
            if value is None:
                missing[f"{label}_missing_or_out_of_range"] += 1
        if None not in (x, y12, y15, y19, gdp):
            complete.append((country, region, x, y12, y15, y19, gdp))
    n = len(complete)
    sample: dict[str, object] = {"key_countries": len(roster), "complete_countries": n,
                                 "excluded_cell_counts": dict(sorted(missing.items())),
                                 "complete_who_regions": dict(sorted(Counter(r[1] for r in complete).items()))}
    failures = []
    if n < MIN_N:
        failures.append("sample_below_150_complete_countries")
    if any(sample["complete_who_regions"].get(region, 0) < MIN_REGION_N for region in REGIONS):
        failures.append("fewer_than_eight_complete_in_a_who_region")
    primary = None
    if n >= MIN_N:
        x = np.asarray([r[2] for r in complete], dtype=float)
        y12 = np.asarray([r[3] for r in complete], dtype=float)
        y15 = np.asarray([r[4] for r in complete], dtype=float)
        y19 = np.asarray([r[5] for r in complete], dtype=float)
        gdp = np.asarray([r[6] for r in complete], dtype=float)
        iqr = float(np.quantile(x, .75) - np.quantile(x, .25))
        sample["aud_iqr_pp"] = iqr
        if iqr < MIN_EXPOSURE_IQR:
            failures.append("aud_iqr_below_1pp")
        region_columns = [(np.asarray([r[1] == region for r in complete], dtype=float))
                          for region in REGIONS[1:]]
        controls = np.column_stack((np.ones(n), y15 / 10, (y15 - y12) / 10,
                                    np.log(gdp), *region_columns))
        design = np.column_stack((controls[:, 0], x, controls[:, 1:]))
        rank = int(np.linalg.matrix_rank(design))
        if rank != design.shape[1]:
            failures.append("design_not_full_rank")
        else:
            residual_x = x - controls @ np.linalg.lstsq(controls, x, rcond=None)[0]
            squared = residual_x ** 2
            total = float(squared.sum())
            if not math.isfinite(total) or total <= 0:
                failures.append("no_residual_aud_exposure")
            else:
                max_share = float(squared.max() / total)
                max_hat = float(np.diag(design @ np.linalg.pinv(design.T @ design) @ design.T).max())
                sample["max_country_residual_exposure_share"] = max_share
                sample["max_hat_leverage"] = max_hat
                if max_share > MAX_RESIDUAL_SHARE:
                    failures.append("country_residual_exposure_share_above_15pct")
                if max_hat > MAX_HAT_LEVERAGE:
                    failures.append("country_hat_leverage_above_20pct")
        if not failures:
            fit = sm.OLS(y19 - y15, design).fit(cov_type="HC3")
            beta, se = float(fit.params[1]), float(fit.bse[1])
            dof = n - design.shape[1]
            if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
                failures.append("nonfinite_or_nonpositive_hc3_uncertainty")
            else:
                p = float(2 * student_t.sf(abs(beta / se), dof))
                critical = float(student_t.ppf(1 - P_MAX / 2, dof))
                if not math.isfinite(p) or not math.isfinite(critical):
                    failures.append("nonfinite_inference")
                else:
                    primary = {"coefficient_per_1pp_aud": beta, "std_error_hc3": se,
                               "p_value_two_sided": p, "confidence_level": 1 - P_MAX,
                               "confidence_interval": [beta - critical * se, beta + critical * se],
                               "n_countries": n, "df_inference": dof, "design_rank": rank,
                               "method": "2019-minus-2015 outcome on 2016 AUD prevalence, 2015 outcome, 2012-to-2015 pretrend, log 2015 real GDP per person, and WHO region; HC3; Student t(n-k)"}
                    holdouts = []
                    for omit in REGIONS:
                        retained = [row for row in complete if row[1] != omit]
                        if len(retained) < MIN_HOLDOUT_N:
                            failures.append(f"regional_holdout_{omit}_below_100")
                            continue
                        xx = np.asarray([r[2] for r in retained], dtype=float)
                        yy12 = np.asarray([r[3] for r in retained], dtype=float)
                        yy15 = np.asarray([r[4] for r in retained], dtype=float)
                        yy19 = np.asarray([r[5] for r in retained], dtype=float)
                        gg = np.asarray([r[6] for r in retained], dtype=float)
                        present = [region for region in REGIONS if region != omit]
                        dd = np.column_stack((np.ones(len(retained)), xx, yy15 / 10,
                                              (yy15 - yy12) / 10, np.log(gg),
                                              *(np.asarray([r[1] == region for r in retained], dtype=float)
                                                for region in present[1:])))
                        if np.linalg.matrix_rank(dd) != dd.shape[1]:
                            failures.append(f"regional_holdout_{omit}_rank")
                            continue
                        fitted = sm.OLS(yy19 - yy15, dd).fit(cov_type="HC3")
                        holdout_beta, holdout_se = float(fitted.params[1]), float(fitted.bse[1])
                        if not math.isfinite(holdout_beta) or not math.isfinite(holdout_se) or holdout_se <= 0:
                            failures.append(f"regional_holdout_{omit}_uncertainty")
                            continue
                        holdouts.append({"omitted_who_region": omit,
                                         "n_countries": len(retained),
                                         "coefficient_per_1pp_aud": holdout_beta})
                    if not failures:
                        primary["regional_holdouts"] = holdouts
    if failures:
        verdict = "INCONCLUSIVE"
        reason = "one or more frozen sample, variation, region, influence, or estimator gates did not pass"
        primary = None
    elif (primary["p_value_two_sided"] <= P_MAX
          and primary["coefficient_per_1pp_aud"] >= magnitude
          and sum(row["coefficient_per_1pp_aud"] > 0 for row in primary["regional_holdouts"])
              >= MIN_CONCORDANT_HOLDOUTS):
        verdict = "SUPPORTED"
        reason = "positive descriptive association clears the frozen family and magnitude gates"
    elif (primary["p_value_two_sided"] <= P_MAX
          and primary["coefficient_per_1pp_aud"] <= -magnitude
          and sum(row["coefficient_per_1pp_aud"] < 0 for row in primary["regional_holdouts"])
              >= MIN_CONCORDANT_HOLDOUTS):
        verdict = "REFUTED"
        reason = "opposite descriptive association clears the frozen family and magnitude gates"
    else:
        verdict = "PARTIAL"
        reason = "estimable descriptive association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate_failures": failures,
            "sample": sample, "primary": primary}


def rendered_files(case: tuple, result: dict[str, object], registration: str,
                   source_lock_commit: str) -> dict[str, bytes]:
    hypothesis, outcome, _magnitude, label = case
    vintages = [SOURCES[name] for name in ("aud", outcome, "gdp")]
    diagnostics = {"hypothesis_id": hypothesis, "family_id": FAMILY,
                   "family_size": len(CASES), "registration_commit": registration,
                   "source_lock_commit": source_lock_commit,
                   "source_sha256": SOURCES["aud"]["sha256"],
                   "source_key_roster_sha256": ROSTER_SHA,
                   "result": result, "correction": CORRECTION,
                   "limitations": LIMITATIONS}
    diagnostic_bytes = (json.dumps(diagnostics, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    manifest = {"hypothesis_id": hypothesis, "status": result["verdict"],
                "runner": RUNNER, "preregistration_commit": registration,
                "source": {"source_sha256": SOURCES["aud"]["sha256"],
                           "source_lock_manifest": lock_rel(case),
                           "source_lock_commit": source_lock_commit},
                "vintages": vintages, "sample": result["sample"],
                "family_correction": CORRECTION}
    packet = {"packet_version": 1,
              "hypothesis": {"id": hypothesis, "path": spec_rel(case), "topic": "healthcare"},
              "preregistration": {"spec_commit": registration,
                                  "source_lock_commit": source_lock_commit,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA},
              "family": {"id": FAMILY, "size": len(CASES),
                         "members": sorted(c[0] for c in CASES)},
              "source": {"source_lock_manifest": lock_rel(case),
                         "source_lock_commit": source_lock_commit,
                         "source_sha256": SOURCES["aud"]["sha256"],
                         "input_vintages": vintages,
                         "attribution": "WHO Global Health Observatory; World Bank WDI"},
              "result": result,
              "reproduction": {"runner": RUNNER,
                               "command": f"python3 {RUNNER} --verify --source-root <pinned-cache-root>",
                               "result_sha256": hashlib.sha256(diagnostic_bytes).hexdigest()},
              "limitations": LIMITATIONS,
              "credit": {"causal": 0, "policy_effect": 0, "school": 0,
                         "position": 0, "featured": 0}, "correction": CORRECTION}
    if result["primary"]:
        beta = result["primary"]["coefficient_per_1pp_aud"]
        p = result["primary"]["p_value_two_sided"]
        figure = f"coefficient {beta:+.6f} outcome points per +1pp AUD; two-sided p={p:.6g}"
    else:
        figure = "no admitted coefficient under the frozen gates"
    card = (f"# {hypothesis} — {result['verdict']}\n\n"
            f"**Registered question:** 2016 adult alcohol-use-disorder prevalence and later change in {label}.\n\n"
            f"**Result:** {figure}. {result['reason'].capitalize()}.\n\n"
            f"**Sample:** {result['sample']['complete_countries']} complete countries of "
            f"{result['sample']['key_countries']} source-key countries. Gate findings: "
            f"{', '.join(result['gate_failures']) if result['gate_failures'] else 'none'}.\n\n"
            "The outcomes are WHO estimates and the 2016 exposure is modelled in many countries. "
            "This is a descriptive country comparison, not a policy or individual-level effect. "
            "Both endpoints share one Bonferroni family; no school, policy, causal, position, "
            "or featured credit is assigned.\n")
    wrapper = ("#!/usr/bin/env python3\nimport subprocess, sys\n"
               f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--verify', *sys.argv[1:]]))\n")
    return {"diagnostics.json": diagnostic_bytes,
            "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "hypothesis.yaml": (ROOT / spec_rel(case)).read_bytes(),
            "result_card.md": card.encode(), "replication.py": wrapper.encode()}


def summary(results: dict[str, dict[str, object]]) -> bytes:
    lines = ["# WHO alcohol-use-disorder / mortality family — results (2026-10-10)", "",
             "Two source-locked, descriptive questions use 2015 and 2012 mortality baselines, 2016 adult alcohol-use-disorder prevalence, and 2019 outcomes. They use one family correction and grant no causal, policy, school, position, or featured credit.", "",
             "| Question | Verdict | Complete countries | Association |", "| --- | --- | ---: | --- |"]
    for case in CASES:
        result = results[case[0]]
        primary = result["primary"]
        estimate = (f"β={primary['coefficient_per_1pp_aud']:+.4f}; p={primary['p_value_two_sided']:.4g}"
                    if primary else "No admitted coefficient")
        lines.append(f"| `{case[0]}` | {result['verdict']} | {result['sample']['complete_countries']} | {estimate} |")
    lines += ["", "The fixed 183-country roster is a source-key upper bound. WHO modelled source dependence, underregistration, and observational confounding limit interpretation. An INCONCLUSIVE member stays in the two-test denominator.", ""]
    return "\n".join(lines).encode()


def execute(mode: str, source_root: Path) -> None:
    paths = checked_sources(source_root)
    roster = read_roster()
    preflight(paths, roster)
    if mode == "preflight":
        print(json.dumps({"source_key_countries": len(roster),
                          "selected_values_or_null_masks_opened": False}, sort_keys=True))
        return
    registration = registration_commit()
    locks = {case[0]: lock_commit(case, registration) for case in CASES}
    values = selected_values(paths, roster)
    results = {case[0]: measured_case(case, roster, values) for case in CASES}
    generated = {case[0]: rendered_files(case, results[case[0]], registration, locks[case[0]])
                 for case in CASES}
    generated["summary"] = {SUMMARY: summary(results)}
    for name, files in generated.items():
        base = ROOT if name == "summary" else ROOT / "engine" / "runs" / name
        if mode == "run":
            base.mkdir(parents=True, exist_ok=True)
        for filename, expected in files.items():
            path = base / filename
            if mode == "run":
                path.write_bytes(expected)
            elif not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"exact replay differs: {path.relative_to(ROOT)}")
    print(json.dumps({"mode": mode,
                      "verdicts": dict(sorted(Counter(r["verdict"] for r in results.values()).items())),
                      "cases": {name: {"verdict": r["verdict"],
                                        "countries": r["sample"]["complete_countries"]}
                                for name, r in results.items()}}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--lock", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--verify", action="store_true")
    parser.add_argument("--case", choices=[c[0] for c in CASES])
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.preflight:
        execute("preflight", source_root)
        return
    if args.lock:
        if not args.case:
            parser.error("--lock needs --case")
        paths = checked_sources(source_root)
        roster = read_roster()
        preflight(paths, roster)
        registration = registration_commit()
        case = next(c for c in CASES if c[0] == args.case)
        rel = lock_rel(case)
        if (ROOT / rel).exists():
            raise RuntimeError("source lock already exists")
        (ROOT / rel).write_text(json.dumps(lock_payload(case, registration), sort_keys=True, indent=2) + "\n")
        print(json.dumps({"source_lock": rel, "registration_commit": registration,
                          "selected_values_or_null_masks_opened": False}, sort_keys=True))
        return
    execute("run" if args.run else "verify", source_root)


if __name__ == "__main__":
    main()
