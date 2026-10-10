#!/usr/bin/env python3
"""Exact source-locked replay for the agricultural transition/services productivity test."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_agriculture_transition_services_productivity_forward_2026"
ID = "wdi_agriculture_transition_services_productivity_forward_v2"
SPEC_REL = f"hypotheses/growth/{ID}.yaml"
REGISTRATION = "a4fd27986d4b2296a59108d666070ec4cf32bfee"
SOURCE_LOCK = "9d61a8b77776f3fe8ce7c6efc810e7e7fc0e9bac"
LOCK_REL = f"prereg/locks/{FAMILY}.json"
RUNNER_REL = f"scripts/run_{FAMILY}.py"
ARTIFACTS = ("hypothesis.yaml", "manifest.yaml", "diagnostics.json",
             "coefficients.parquet", "chart_data.json", "result_card.md",
             "replication.py", "evidence_packet.yaml", "metric_results.parquet")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def first_add(path: str) -> str:
    lines = git("log", "--diff-filter=A", "--format=%H", "--", path).splitlines()
    if not lines:
        raise ValueError(f"Missing first-addition commit: {path}")
    return lines[-1]


def frozen(path: str, commit: str) -> None:
    current = (ROOT / path).read_bytes()
    committed = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
    head = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    if current != committed or current != head:
        raise ValueError(f"Frozen file changed: {path}")


def source_keys(path: Path, role: str, ref: dict) -> list[tuple[str, int]]:
    if role == "total_employed":
        selected = pq.read_table(path, columns=["country_iso3", "sex", "classif1", "year"]).to_pylist()
        return [(str(row["country_iso3"]), int(row["year"])) for row in selected
                if row["sex"] == ref["selector"]["sex"]
                and row["classif1"] == ref["selector"]["classif1"]
                and row["year"] in ref["required_years"]]
    selected = pq.read_table(path, columns=["country_iso3", "year"]).to_pylist()
    return [(str(row["country_iso3"]), int(row["year"])) for row in selected
            if row["year"] in ref["required_years"]]


def verify(source_root: Path) -> tuple[dict, dict]:
    if subprocess.run(["git", "merge-base", "--is-ancestor", REGISTRATION, SOURCE_LOCK],
                      cwd=ROOT).returncode:
        raise ValueError("Registration is not an ancestor of source lock")
    if subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_LOCK, "HEAD"],
                      cwd=ROOT).returncode:
        raise ValueError("Source lock is not an ancestor of HEAD")
    if first_add(SPEC_REL) != REGISTRATION:
        raise ValueError("Invalid specification chronology")
    frozen(SPEC_REL, REGISTRATION)
    if first_add(LOCK_REL) != SOURCE_LOCK:
        raise ValueError("Invalid source-lock chronology")
    frozen(LOCK_REL, SOURCE_LOCK)
    runner_commit = first_add(RUNNER_REL)
    if subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_LOCK, runner_commit],
                      cwd=ROOT).returncode:
        raise ValueError("Runner was not committed after source lock")
    frozen(RUNNER_REL, runner_commit)
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text())
    lock = json.loads((ROOT / LOCK_REL).read_text())
    if (lock["family_id"] != FAMILY or lock["registration_commit"] != REGISTRATION
            or lock["hypothesis_ids"] != [ID] or lock["family_size"] != 1
            or lock["selected_values_read"] is not False):
        raise ValueError("Family lock mismatch")
    roster = lock["country_roster"]
    roster_sha = hashlib.sha256("".join(f"{c}\n" for c in roster).encode()).hexdigest()
    if roster != sorted(roster) or len(roster) != 186 or roster_sha != lock["country_roster_sha256"]:
        raise ValueError("Frozen country roster mismatch")
    th = spec["falsification"]["threshold"]
    if (spec["hypothesis_id"] != ID or spec["status"] != "pre_registered"
            or th["family_id"] != FAMILY or th["family_size"] != 1
            or th["treatment_years"] != [2005, 2015]
            or th["outcome_years"] != [2015, 2023]):
        raise ValueError("Frozen specification mismatch")
    if set(lock["source_files"]) != set(th["source_files"]):
        raise ValueError("Frozen source roles mismatch")
    for role, ref in lock["source_files"].items():
        wanted = th["source_files"][role]
        if ref["path"] != wanted["path"] or ref["sha256"] != wanted["sha256"]:
            raise ValueError(f"Frozen source mismatch: {role}")
        if role == "total_employed" and ref.get("selector") != {
                "sex": "SEX_T", "classif1": "AGE_YTHADULT_YGE15"}:
            raise ValueError("Frozen total-employment selector mismatch")
        path = source_root / ref["path"]
        if not path.is_file() or sha(path) != ref["sha256"]:
            raise ValueError(f"Source bytes unavailable or changed: {role}")
        if pq.ParquetFile(path).schema_arrow.names != ref["schema_names"]:
            raise ValueError(f"Source schema changed: {role}")
        selected = sorted((c, y) for c, y in source_keys(path, role, ref) if c in roster)
        if len(selected) != len(set(selected)):
            raise ValueError(f"Duplicate selected key: {role}")
        key_sha = hashlib.sha256("".join(f"{c},{y}\n" for c, y in selected).encode()).hexdigest()
        if len(selected) != ref["selected_key_count"] or key_sha != ref["selected_key_sha256"]:
            raise ValueError(f"Selected source keys changed: {role}")
    return lock, spec


def finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def selected_values(source_root: Path, lock: dict) -> dict:
    values = {}
    roster = set(lock["country_roster"])
    for role, ref in lock["source_files"].items():
        path = source_root / ref["path"]
        selected = {}
        if role == "total_employed":
            rows = pq.read_table(path, columns=["country_iso3", "sex", "classif1",
                                                "year", "value"]).to_pylist()
            rows = [row for row in rows
                    if row["sex"] == ref["selector"]["sex"]
                    and row["classif1"] == ref["selector"]["classif1"]]
        else:
            rows = pq.read_table(path, columns=["country_iso3", "year", "value"]).to_pylist()
        for row in rows:
            key = (str(row["country_iso3"]), int(row["year"]))
            if key[0] in roster and key[1] in ref["required_years"]:
                if key in selected:
                    raise ValueError(f"Duplicate selected value: {role} {key}")
                selected[key] = row["value"]
        values[role] = selected
    return values


def panel_for(lock: dict, values: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    excluded = {"agricultural_share_missing_or_invalid": 0,
                "services_share_missing_or_invalid": 0,
                "services_va_missing_or_invalid": 0,
                "total_employed_missing_or_invalid": 0,
                "income_missing_or_invalid": 0}
    for country in lock["country_roster"]:
        a05, a15 = (finite(values["agriculture_employment"].get((country, year)))
                    for year in (2005, 2015))
        s05, s15 = (finite(values["services_employment_share"].get((country, year)))
                    for year in (2005, 2015))
        v05, v15 = (finite(values["services_real_value_added"].get((country, year)))
                    for year in (2005, 2015))
        e05, e15 = (finite(values["total_employed"].get((country, year)))
                    for year in (2005, 2015))
        g05, g15, g23 = (finite(values["income"].get((country, year)))
                         for year in (2005, 2015, 2023))
        bad = {
            "agricultural_share_missing_or_invalid":
                any(v is None or not 0 <= v <= 100 for v in (a05, a15)),
            "services_share_missing_or_invalid":
                any(v is None or not 0 < v <= 100 for v in (s05, s15)),
            "services_va_missing_or_invalid":
                any(v is None or v <= 0 for v in (v05, v15)),
            "total_employed_missing_or_invalid":
                any(v is None or v <= 0 for v in (e05, e15)),
            "income_missing_or_invalid":
                any(v is None or v <= 0 for v in (g05, g15, g23)),
        }
        for reason, failed in bad.items():
            if failed:
                excluded[reason] += 1
        if any(bad.values()):
            continue
        productivity_growth = 100 * ((math.log(v15)-math.log(v05))
                                     - (math.log(e15)-math.log(e05))
                                     - (math.log(s15)-math.log(s05))) / 10
        rose = int(productivity_growth > 0)
        decline_pp = a05-a15
        rows.append({"country_iso3": country, "ag_decline_pp": decline_pp,
                     "ag_decline_10pp": decline_pp/10,
                     "services_productivity_growth": productivity_growth,
                     "services_productivity_rose": rose,
                     "ag_decline_x_rose": decline_pp/10*rose,
                     "ag_share_2005": a05, "log_income_2015": math.log(g15),
                     "prior_income_growth": 100*(math.log(g15)-math.log(g05))/10,
                     "future_outcome": 100*(math.log(g23)-math.log(g15))/8})
    panel = pd.DataFrame(rows)
    return panel, {"candidate_economies": len(lock["country_roster"]),
                   "complete_economies": len(rows),
                   "excluded_by_reason_overlapping": excluded}


def fit(panel: pd.DataFrame) -> dict:
    columns = ["ag_decline_10pp", "services_productivity_rose", "ag_decline_x_rose",
               "ag_share_2005", "log_income_2015", "prior_income_growth"]
    x = np.column_stack([np.ones(len(panel))] +
                        [panel[name].to_numpy(dtype=float) for name in columns])
    y = panel["future_outcome"].to_numpy(dtype=float)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank model unavailable")
    result = sm.OLS(y, x).fit(cov_type="HC3")
    beta = np.asarray(result.params, dtype=float)
    covariance = np.asarray(result.cov_params(), dtype=float)
    se = np.asarray(result.bse, dtype=float)
    df = n-k
    if se[1] <= 0 or se[3] <= 0:
        raise ValueError("Finite HC3 uncertainty unavailable")
    rising_slope = float(beta[1]+beta[3])
    rising_variance = covariance[1, 1]+covariance[3, 3]+2*covariance[1, 3]
    if rising_variance <= 0:
        raise ValueError("Positive rising-slope variance unavailable")
    rising_se = float(math.sqrt(rising_variance))
    other = x[:, [0, 1, 2, 4, 5, 6]]
    residual = x[:, 3]-other @ np.linalg.lstsq(other, x[:, 3], rcond=None)[0]
    squared = residual**2
    if squared.sum() <= 1e-12:
        raise ValueError("Identified interaction exposure unavailable")
    critical = float(student_t.ppf(0.975, df=df))
    estimate = {
        "interaction_coefficient": float(beta[3]),
        "interaction_standard_error": float(se[3]),
        "interaction_p_value": float(2*student_t.sf(abs(beta[3]/se[3]), df=df)),
        "non_rising_slope": float(beta[1]),
        "non_rising_slope_standard_error": float(se[1]),
        "non_rising_slope_upper_95": float(beta[1]+critical*se[1]),
        "rising_slope": rising_slope,
        "rising_slope_standard_error": rising_se,
        "rising_slope_p_value": float(2*student_t.sf(abs(rising_slope/rising_se), df=df)),
        "reference_df": df, "covariance": "HC3",
        "max_single_economy_residualized_interaction_share": float(squared.max()/squared.sum()),
    }
    if not all(math.isfinite(v) for v in estimate.values() if isinstance(v, (int, float))):
        raise ValueError("Nonfinite estimate statistic")
    return estimate


def calculate(panel: pd.DataFrame, diag: dict, threshold: dict) -> tuple[dict, str]:
    n = len(panel)
    if n:
        rising = panel.loc[panel["services_productivity_rose"] == 1, "ag_decline_pp"].to_numpy(float)
        non_rising = panel.loc[panel["services_productivity_rose"] == 0, "ag_decline_pp"].to_numpy(float)
        gains = panel["ag_decline_pp"].to_numpy(float)
    else:
        rising = non_rising = gains = np.array([])
    diag["rising_group_economies"] = len(rising)
    diag["non_rising_group_economies"] = len(non_rising)
    diag["agricultural_decline_5pp_economies"] = int((gains >= 5).sum())
    diag["agricultural_decline_iqr_pp_rising"] = (
        float(np.quantile(rising, .75)-np.quantile(rising, .25)) if len(rising) else 0.0)
    diag["agricultural_decline_iqr_pp_non_rising"] = (
        float(np.quantile(non_rising, .75)-np.quantile(non_rising, .25)) if len(non_rising) else 0.0)
    if (n < threshold["min_complete_economies"]
            or min(len(rising),len(non_rising)) < threshold["min_each_services_productivity_group"]
            or diag["agricultural_decline_5pp_economies"] <
                threshold["min_agricultural_decline_5pp_economies"]
            or min(diag["agricultural_decline_iqr_pp_rising"],
                   diag["agricultural_decline_iqr_pp_non_rising"]) <
                threshold["min_agricultural_decline_iqr_pp_each_group"]):
        diag["failed_gate"] = "sample_group_or_exposure_floor"
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel)
        loo = []
        for i in range(n):
            try:
                loo.append(fit(panel.drop(index=i)))
            except ValueError:
                continue
    except ValueError as exc:
        diag["failed_gate"] = f"estimator:{exc}"
        return {}, "INCONCLUSIVE"
    estimate["loo_successes"] = len(loo)
    if (estimate["max_single_economy_residualized_interaction_share"] >
            threshold["max_single_economy_residualized_interaction_share"]
            or len(loo) < n-threshold["max_loo_failures"]):
        diag["failed_gate"] = "influence_or_loo"
        return estimate, "INCONCLUSIVE"
    estimate["loo_positive_interaction_share"] = sum(
        item["interaction_coefficient"] > 0 for item in loo)/len(loo)
    estimate["loo_negative_interaction_share"] = sum(
        item["interaction_coefficient"] < 0 for item in loo)/len(loo)
    estimate["loo_positive_rising_slope_share"] = sum(
        item["rising_slope"] > 0 for item in loo)/len(loo)
    estimate["loo_negative_rising_slope_share"] = sum(
        item["rising_slope"] < 0 for item in loo)/len(loo)
    if (estimate["interaction_coefficient"] >=
            threshold["min_abs_interaction_annual_log_pp_per_10pp"]
            and estimate["interaction_p_value"] <= threshold["two_sided_p_max"]
            and estimate["rising_slope"] >=
                threshold["min_abs_rising_slope_annual_log_pp_per_10pp"]
            and estimate["rising_slope_p_value"] <= threshold["two_sided_p_max"]
            and estimate["non_rising_slope_upper_95"] <
                threshold["max_non_rising_slope_upper_95"]
            and min(estimate["loo_positive_interaction_share"],
                    estimate["loo_positive_rising_slope_share"]) >=
                threshold["min_loo_direction_share"]):
        return estimate, "SUPPORTED"
    if ((estimate["interaction_coefficient"] <=
             -threshold["min_abs_interaction_annual_log_pp_per_10pp"]
          and estimate["interaction_p_value"] <= threshold["two_sided_p_max"]
          and estimate["loo_negative_interaction_share"] >=
              threshold["min_loo_direction_share"])
        or (estimate["rising_slope"] <=
              -threshold["min_abs_rising_slope_annual_log_pp_per_10pp"]
            and estimate["rising_slope_p_value"] <= threshold["two_sided_p_max"]
            and estimate["loo_negative_rising_slope_share"] >=
                threshold["min_loo_direction_share"])):
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def jwrite(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")


def pwrite(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, lock: dict, panel: pd.DataFrame,
         diag: dict, estimate: dict, verdict: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory/"hypothesis.yaml").write_bytes((ROOT/SPEC_REL).read_bytes())
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    manifest = {"design_id": ID, "family_id": FAMILY, "family_size": 1,
                "independent_family_count": 1, "verdict": verdict,
                "evidence_type": "descriptive", "spec_commit": REGISTRATION,
                "lock_commit": SOURCE_LOCK, "spec_sha256": sha(ROOT/SPEC_REL),
                "lock_sha256": sha(ROOT/LOCK_REL), "runner_sha256": sha(ROOT/RUNNER_REL),
                "source_files": lock["source_files"], "artifacts": list(ARTIFACTS), "credit": credit}
    (directory/"manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    correction = {"disposition": "descriptive_calibration_only", "causal_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0,
                  "school_score_eligible": False, "school_score_credit": 0,
                  "featured_eligible": False}
    jwrite(directory/"diagnostics.json", {**diag, "verdict": verdict, "estimate": estimate,
                                           "correction": correction, "family_id": FAMILY,
                                           "family_size": 1, "independent_family_count": 1,
                                           "analysis_scope": "descriptive_only"})
    has_estimate = "interaction_coefficient" in estimate
    pwrite(directory/"coefficients.parquet", {
        "term": ["ag_decline_x_services_productivity_rose"] if has_estimate else [],
        "coefficient": [estimate["interaction_coefficient"]] if has_estimate else [],
        "standard_error": [estimate["interaction_standard_error"]] if has_estimate else [],
        "p_value": [estimate["interaction_p_value"]] if has_estimate else [],
    }, pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                  ("standard_error", pa.float64()), ("p_value", pa.float64())]))
    jwrite(directory/"chart_data.json", [
        {key: (str(value) if key == "country_iso3" else float(value))
         for key, value in row._asdict().items()}
        for row in panel.itertuples(index=False)
    ])
    lines = [f"# {ID}", "", f"**Verdict: {verdict} — descriptive only.**", "",
             f"Complete economies: {len(panel)} of {diag['candidate_economies']} source-key candidates.",
             f"Services productivity rising/non-rising groups: {diag['rising_group_economies']}/{diag['non_rising_group_economies']}.",
             f"Agricultural-share declines >=5 pp: {diag['agricultural_decline_5pp_economies']}; group IQRs: {diag['agricultural_decline_iqr_pp_rising']:.6g}/{diag['agricultural_decline_iqr_pp_non_rising']:.6g} pp."]
    if has_estimate:
        lines += [f"Interaction coefficient: {estimate['interaction_coefficient']:.6g} annual log-growth pp per 10-pp agricultural-share decline; HC3 SE {estimate['interaction_standard_error']:.6g}; two-sided p {estimate['interaction_p_value']:.6g}.",
                  f"Rising-group slope: {estimate['rising_slope']:.6g} (p {estimate['rising_slope_p_value']:.6g}); non-rising slope: {estimate['non_rising_slope']:.6g} (95% upper {estimate['non_rising_slope_upper_95']:.6g}); leave-one-out fits {estimate['loo_successes']}."]
    else:
        lines.append("No coefficient was estimated because a frozen gate failed.")
    lines += ["", "This is a later-outcome descriptive association. Real services value added per services worker combines WDI and ILOSTAT conventions. The old generic proxy result remains unchanged. No structural-transition policy effect is identified; zero causal, policy, school, position, or featured credit.", ""]
    (directory/"result_card.md").write_text("\n".join(lines))
    (directory/"replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER_REL}'), '--replay', *sys.argv[1:]], check=True)\n"
    )
    packet = {"design_id": ID, "family_id": FAMILY, "family_size": 1,
              "independent_family_count": 1, "verdict": verdict, "evidence_type": "descriptive",
              "causal_claim": False, "school_claim_links": [], "policy_effect_credit": False,
              "correction": correction, "source_hashes_verified": True,
              "strict_spec_lock_chronology_verified": True,
              "interpretation": "Agricultural-employment transition with preperiod services-productivity condition and later GDP-per-person growth; archived proxy verdict unchanged."}
    (directory/"evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    pwrite(directory/"metric_results.parquet", {
        "verdict": [verdict], "complete_economies": [len(panel)],
        "rising_group_economies": [diag["rising_group_economies"]],
        "non_rising_group_economies": [diag["non_rising_group_economies"]],
    }, pa.schema([("verdict", pa.string()), ("complete_economies", pa.int64()),
                  ("rising_group_economies", pa.int64()), ("non_rising_group_economies", pa.int64())]))
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError("Run artifact roster differs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--replay", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    lock, spec = verify(args.source_root)
    values = selected_values(args.source_root, lock)
    panel, diag = panel_for(lock, values)
    estimate, verdict = calculate(panel, diag, spec["falsification"]["threshold"])
    target = ROOT/"engine"/"runs"/ID
    if args.replay and not target.is_dir():
        raise ValueError(f"No run directory to replay: {ID}")
    if args.run and target.exists():
        raise ValueError(f"Run already exists: {ID}")
    with tempfile.TemporaryDirectory(prefix="ieset_agriculture_transition_") as temp:
        generated = Path(temp)/ID
        emit(generated, lock, panel, diag, estimate, verdict)
        if args.replay:
            for artifact in ARTIFACTS:
                if sha(generated/artifact) != sha(target/artifact):
                    raise ValueError(f"Exact replay mismatch: {ID}/{artifact}")
            print(f"{ID}: exact replay matched {len(ARTIFACTS)} artifacts")
        else:
            shutil.copytree(generated, target)
            print(f"{ID}: {verdict}; {len(panel)} complete economies; {len(ARTIFACTS)} artifacts")


if __name__ == "__main__":
    main()
