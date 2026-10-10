#!/usr/bin/env python3
"""Exact replay for the registered, source-locked electricity-access family."""
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
FAMILY = "wdi_electricity_access_forward_income_under5_2026_family"
IDS = ("wdi_electricity_access_2005_2015_forward_income_growth_v2",
       "wdi_electricity_access_2005_2015_forward_under5_improvement_v2")
SPEC = {IDS[0]: f"hypotheses/growth/{IDS[0]}.yaml",
        IDS[1]: f"hypotheses/healthcare/{IDS[1]}.yaml"}
REGISTRATION = "3afae0fedaeb05108a40cd65a61353ceadea8ad0"
SOURCE_LOCK = "378172e261446d2cb28493f11b2dd26b21efaba5"
LOCK_REL = f"prereg/locks/{FAMILY}.json"
RUNNER_REL = f"scripts/run_{FAMILY}.py"
ARTIFACTS = ("hypothesis.yaml", "manifest.yaml", "diagnostics.json",
             "coefficients.parquet", "chart_data.json", "result_card.md",
             "replication.py", "evidence_packet.yaml", "metric_results.parquet")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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


def verify(source_root: Path) -> tuple[dict, dict]:
    if subprocess.run(["git", "merge-base", "--is-ancestor", REGISTRATION, SOURCE_LOCK], cwd=ROOT).returncode:
        raise ValueError("Registration is not an ancestor of source lock")
    if subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_LOCK, "HEAD"], cwd=ROOT).returncode:
        raise ValueError("Source lock is not an ancestor of HEAD")
    for path in SPEC.values():
        if first_add(path) != REGISTRATION:
            raise ValueError(f"Invalid spec chronology: {path}")
        frozen(path, REGISTRATION)
    if first_add(LOCK_REL) != SOURCE_LOCK:
        raise ValueError("Invalid source-lock chronology")
    frozen(LOCK_REL, SOURCE_LOCK)
    lock = json.loads((ROOT / LOCK_REL).read_text())
    specs = {hid: yaml.safe_load((ROOT / SPEC[hid]).read_text()) for hid in IDS}
    if (lock["family_id"] != FAMILY or lock["registration_commit"] != REGISTRATION
            or lock["hypothesis_ids"] != list(IDS) or lock["family_size"] != 2
            or lock["selected_values_read"] is not False):
        raise ValueError("Family lock mismatch")
    roster = lock["country_roster"]
    roster_sha = hashlib.sha256("".join(f"{c}\n" for c in roster).encode()).hexdigest()
    if roster != sorted(roster) or len(roster) != 216 or roster_sha != lock["country_roster_sha256"]:
        raise ValueError("Frozen country roster mismatch")
    for hid, spec in specs.items():
        th = spec["falsification"]["threshold"]
        if (spec["hypothesis_id"] != hid or spec["status"] != "pre_registered"
                or th["family_id"] != FAMILY or th["family_size"] != 2
                or th["treatment_years"] != [2005, 2015]
                or th["outcome_years"] != [2015, 2023]):
            raise ValueError(f"Frozen specification mismatch: {hid}")
        for role, ref in th["source_files"].items():
            item = lock["source_files"][role]
            if ref["path"] != item["path"] or ref["sha256"] != item["sha256"]:
                raise ValueError(f"Frozen source mismatch: {role}")
    for role, ref in lock["source_files"].items():
        path = source_root / ref["path"]
        if not path.is_file() or sha(path) != ref["sha256"]:
            raise ValueError(f"Source bytes unavailable or changed: {role}")
        keys = pq.read_table(path, columns=["country_iso3", "year"]).to_pydict()
        selected = sorted((c, int(y)) for c, y in zip(keys["country_iso3"], keys["year"])
                          if c in roster and int(y) in ref["required_years"])
        digest = hashlib.sha256("".join(f"{c},{y}\n" for c, y in selected).encode()).hexdigest()
        if len(selected) != ref["selected_key_count"] or digest != ref["selected_key_sha256"]:
            raise ValueError(f"Selected source keys changed: {role}")
    return lock, specs


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
        selected = {}
        for row in pq.read_table(source_root / ref["path"], columns=["country_iso3", "year", "value"]).to_pylist():
            key = (row["country_iso3"], int(row["year"]))
            if key[0] in roster and key[1] in ref["required_years"]:
                if key in selected:
                    raise ValueError(f"Duplicate selected value: {role} {key}")
                selected[key] = row["value"]
        values[role] = selected
    return values


def panel_for(role: str, lock: dict, values: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    excluded = {"access_missing_or_invalid": 0, "income_missing_or_invalid": 0,
                "mortality_missing_or_invalid": 0}
    for country in lock["country_roster"]:
        a05 = finite(values["access"].get((country, 2005)))
        a15 = finite(values["access"].get((country, 2015)))
        g05 = finite(values["income"].get((country, 2005)))
        g15 = finite(values["income"].get((country, 2015)))
        g23 = finite(values["income"].get((country, 2023)))
        m05 = finite(values["mortality"].get((country, 2005)))
        m15 = finite(values["mortality"].get((country, 2015)))
        m23 = finite(values["mortality"].get((country, 2023)))
        bad_access = a05 is None or a15 is None or not (0 <= a05 <= 100) or not (0 <= a15 <= 100)
        bad_income = any(v is None or v <= 0 for v in (g05, g15, g23))
        bad_mortality = role == "mortality" and any(v is None or v <= 0 for v in (m05, m15, m23))
        if bad_access or bad_income or bad_mortality:
            if bad_access:
                excluded["access_missing_or_invalid"] += 1
            if bad_income:
                excluded["income_missing_or_invalid"] += 1
            if bad_mortality:
                excluded["mortality_missing_or_invalid"] += 1
            continue
        row = {"country_iso3": country, "access_gain_10pp": (a15-a05)/10,
               "access_gain_pp": a15-a05, "access_2005": a05,
               "log_income_2015": math.log(g15)}
        if role == "income":
            row["prior_income_growth"] = 100*(math.log(g15)-math.log(g05))/10
            row["future_outcome"] = 100*(math.log(g23)-math.log(g15))/8
        else:
            row["log_mortality_2015"] = math.log(m15)
            row["prior_mortality_decline"] = 100*(math.log(m05)-math.log(m15))/10
            row["future_outcome"] = 100*(math.log(m15)-math.log(m23))/8
        rows.append(row)
    return pd.DataFrame(rows), {"candidate_economies": len(lock["country_roster"]),
                                "complete_economies": len(rows), "excluded_by_reason_overlapping": excluded}


def fit(panel: pd.DataFrame, role: str) -> dict:
    controls = (["access_2005", "log_income_2015", "prior_income_growth"] if role == "income"
                else ["access_2005", "log_mortality_2015", "prior_mortality_decline", "log_income_2015"])
    x = np.column_stack([np.ones(len(panel)), panel["access_gain_10pp"].to_numpy(dtype=float)] +
                        [panel[name].to_numpy(dtype=float) for name in controls])
    y = panel["future_outcome"].to_numpy(dtype=float)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank model unavailable")
    result = sm.OLS(y, x).fit(cov_type="HC3")
    beta, se = float(result.params[1]), float(result.bse[1])
    p = float(2*student_t.sf(abs(beta/se), df=n-k)) if se > 0 else float("nan")
    covars = x[:, [0, *range(2, k)]]
    residual = x[:, 1] - covars @ np.linalg.lstsq(covars, x[:, 1], rcond=None)[0]
    squared = residual**2
    if not all(math.isfinite(v) for v in (beta, se, p)) or se <= 0 or squared.sum() <= 1e-12:
        raise ValueError("Finite HC3 estimate or identified exposure unavailable")
    return {"coefficient": beta, "standard_error": se, "p_value": p,
            "reference_df": n-k, "covariance": "HC3",
            "max_single_economy_residualized_exposure_share": float(squared.max()/squared.sum())}


def calculate(panel: pd.DataFrame, diag: dict, threshold: dict, role: str) -> tuple[dict, str]:
    n = len(panel)
    gain = panel["access_gain_pp"].to_numpy(dtype=float) if n else np.array([])
    diag["access_gain_10pp_economies"] = int((gain >= 10).sum())
    diag["access_gain_iqr_pp"] = float(np.quantile(gain, .75)-np.quantile(gain, .25)) if n else 0.0
    if (n < threshold["min_complete_economies"]
            or diag["access_gain_10pp_economies"] < threshold["min_access_gain_10pp_economies"]
            or diag["access_gain_iqr_pp"] < threshold["min_access_gain_iqr_pp"]):
        diag["failed_gate"] = "sample_or_exposure_floor"
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel, role)
        loo = []
        for i in range(n):
            try:
                loo.append(fit(panel.drop(index=i), role)["coefficient"])
            except ValueError:
                continue
    except ValueError as exc:
        diag["failed_gate"] = f"estimator:{exc}"
        return {}, "INCONCLUSIVE"
    estimate["loo_successes"] = len(loo)
    estimate["loo_positive_share"] = sum(v > 0 for v in loo)/len(loo) if loo else None
    estimate["loo_negative_share"] = sum(v < 0 for v in loo)/len(loo) if loo else None
    if (estimate["max_single_economy_residualized_exposure_share"] > threshold["max_single_economy_residualized_exposure_share"]
            or len(loo) < n-threshold["max_loo_failures"]):
        diag["failed_gate"] = "influence_or_loo"
        return estimate, "INCONCLUSIVE"
    if (estimate["coefficient"] >= threshold["min_abs_beta_annual_log_pp_per_10pp"]
            and estimate["p_value"] <= threshold["two_sided_p_max"]
            and estimate["loo_positive_share"] >= threshold["min_loo_sign_share"]):
        return estimate, "SUPPORTED"
    if (estimate["coefficient"] <= -threshold["min_abs_beta_annual_log_pp_per_10pp"]
            and estimate["p_value"] <= threshold["two_sided_p_max"]
            and estimate["loo_negative_share"] >= threshold["min_loo_sign_share"]):
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def jwrite(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")


def pwrite(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, hid: str, lock: dict, panel: pd.DataFrame,
         diag: dict, estimate: dict, verdict: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory/"hypothesis.yaml").write_bytes((ROOT/SPEC[hid]).read_bytes())
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    manifest = {"design_id": hid, "family_id": FAMILY, "family_size": 2,
                "independent_family_count": 1, "verdict": verdict,
                "evidence_type": "descriptive", "spec_commit": REGISTRATION,
                "lock_commit": SOURCE_LOCK, "spec_sha256": sha(ROOT/SPEC[hid]),
                "lock_sha256": sha(ROOT/LOCK_REL), "runner_sha256": sha(ROOT/RUNNER_REL),
                "source_files": lock["source_files"], "artifacts": list(ARTIFACTS), "credit": credit}
    (directory/"manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    correction = {"disposition": "descriptive_calibration_only", "causal_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0,
                  "school_score_eligible": False, "school_score_credit": 0,
                  "featured_eligible": False}
    jwrite(directory/"diagnostics.json", {**diag, "verdict": verdict, "estimate": estimate,
                                           "correction": correction, "family_id": FAMILY,
                                           "family_size": 2, "independent_family_count": 1,
                                           "analysis_scope": "descriptive_only"})
    has_estimate = "coefficient" in estimate
    pwrite(directory/"coefficients.parquet", {
        "term": ["access_gain_10pp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                  ("standard_error", pa.float64()), ("p_value", pa.float64())]))
    jwrite(directory/"chart_data.json", [
        {key: (str(value) if key == "country_iso3" else float(value))
         for key, value in row._asdict().items()}
        for row in panel.itertuples(index=False)
    ])
    lines = [f"# {hid}", "", f"**Verdict: {verdict} — descriptive only.**", "",
             f"Complete economies: {len(panel)} of {diag['candidate_economies']} source-key candidates.",
             f"2005–2015 electricity-access gains >=10 pp: {diag['access_gain_10pp_economies']}; exposure IQR: {diag['access_gain_iqr_pp']:.6g} pp."]
    if has_estimate:
        lines.append(f"Exposure coefficient: {estimate['coefficient']:.6g} annual log-improvement pp per 10-pp access gain; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}; LOO fits {estimate['loo_successes']}.")
    else:
        lines.append("No coefficient was estimated because a frozen gate failed.")
    lines += ["", "This is a forward descriptive association. Income and child-health endpoints are one evidence family with Bonferroni p<=0.025 each. No grid policy intervention is identified; zero causal, policy, school, position, or featured credit.", ""]
    (directory/"result_card.md").write_text("\n".join(lines))
    (directory/"replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER_REL}'), '--replay', *sys.argv[1:]], check=True)\n"
    )
    packet = {"design_id": hid, "family_id": FAMILY, "family_size": 2,
              "independent_family_count": 1, "verdict": verdict, "evidence_type": "descriptive",
              "causal_claim": False, "school_claim_links": [], "policy_effect_credit": False,
              "correction": correction, "source_hashes_verified": True,
              "strict_spec_lock_chronology_verified": True,
              "interpretation": "Baseline-adjusted forward electricity-access association; two distinct outcomes form one family. Old claims remain unchanged."}
    (directory/"evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    pwrite(directory/"metric_results.parquet", {
        "verdict": [verdict], "complete_economies": [len(panel)],
        "access_gain_10pp_economies": [diag["access_gain_10pp_economies"]],
    }, pa.schema([("verdict", pa.string()), ("complete_economies", pa.int64()),
                  ("access_gain_10pp_economies", pa.int64())]))
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError("Run artifact roster differs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--replay", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    lock, specs = verify(args.source_root)
    values = selected_values(args.source_root, lock)
    for hid in IDS:
        role = specs[hid]["falsification"]["threshold"]["outcome_role"]
        panel, diag = panel_for(role, lock, values)
        estimate, verdict = calculate(panel, diag, specs[hid]["falsification"]["threshold"], role)
        target = ROOT/"engine"/"runs"/hid
        if args.replay and not target.is_dir():
            raise ValueError(f"No run directory to replay: {hid}")
        if args.run and target.exists():
            raise ValueError(f"Run already exists: {hid}")
        with tempfile.TemporaryDirectory(prefix="ieset_electricity_family_") as temp:
            generated = Path(temp)/hid
            emit(generated, hid, lock, panel, diag, estimate, verdict)
            if args.replay:
                for artifact in ARTIFACTS:
                    if sha(generated/artifact) != sha(target/artifact):
                        raise ValueError(f"Exact replay mismatch: {hid}/{artifact}")
                print(f"{hid}: exact replay matched {len(ARTIFACTS)} artifacts")
            else:
                shutil.copytree(generated, target)
                print(f"{hid}: {verdict}; {len(panel)} complete economies; {len(ARTIFACTS)} artifacts")


if __name__ == "__main__":
    main()
