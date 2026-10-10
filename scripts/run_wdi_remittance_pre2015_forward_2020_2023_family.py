#!/usr/bin/env python3
"""Exact replay for the source-locked two-outcome remittance forecast family."""
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
FAMILY = "wdi_remittance_pre2015_forward_2020_2023_family"
IDS = (
    "wdi_remittance_pre2015_forward_current_account_v2",
    "wdi_remittance_pre2015_forward_private_consumption_v2",
)
SPEC = {
    IDS[0]: f"hypotheses/trade/{IDS[0]}.yaml",
    IDS[1]: f"hypotheses/growth/{IDS[1]}.yaml",
}
REGISTRATION = "32c4cee26edc73c1bae87d23963d90d81a4a48af"
SOURCE_LOCK = "da47dbe1ddcebbe0b4241c6d56dd19eb9b780988"
LOCK_REL = f"prereg/locks/{FAMILY}.json"
RUNNER_REL = f"scripts/run_{FAMILY}.py"
PRE = (2010, 2011, 2012, 2013, 2014)
FUTURE = (2020, 2021, 2022, 2023)
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def first_add(path: str) -> str:
    history = git("log", "--diff-filter=A", "--format=%H", "--", path).splitlines()
    if not history:
        raise ValueError(f"Missing first-addition commit for {path}")
    return history[-1]


def frozen(path: str, commit: str) -> None:
    content = (ROOT / path).read_bytes()
    if content != subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT):
        raise ValueError(f"Committed first-addition file changed: {path}")
    if content != subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT):
        raise ValueError(f"Working file differs from HEAD: {path}")


def verify(source_root: Path) -> tuple[dict, dict[str, dict]]:
    if git("rev-parse", REGISTRATION) != REGISTRATION or git("rev-parse", SOURCE_LOCK) != SOURCE_LOCK:
        raise ValueError("Commit identity mismatch")
    if subprocess.run(["git", "merge-base", "--is-ancestor", REGISTRATION, SOURCE_LOCK], cwd=ROOT).returncode:
        raise ValueError("Source lock does not descend from registration")
    if subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_LOCK, "HEAD"], cwd=ROOT).returncode:
        raise ValueError("Source lock is not an ancestor of HEAD")
    for path in SPEC.values():
        if first_add(path) != REGISTRATION:
            raise ValueError(f"Invalid strict registration: {path}")
        frozen(path, REGISTRATION)
    if first_add(LOCK_REL) != SOURCE_LOCK:
        raise ValueError("Invalid strict source-lock chronology")
    frozen(LOCK_REL, SOURCE_LOCK)
    lock = json.loads((ROOT / LOCK_REL).read_text())
    specs = {hid: yaml.safe_load((ROOT / SPEC[hid]).read_text()) for hid in IDS}
    if lock["family_id"] != FAMILY or lock["registration_commit"] != REGISTRATION:
        raise ValueError("Source-lock family or registration mismatch")
    if lock["hypothesis_ids"] != list(IDS) or lock["family_size"] != 2 or lock["selected_values_read"] is not False:
        raise ValueError("Invalid source-lock family accounting")
    if lock["country_roster"] != sorted(lock["country_roster"]) or len(lock["country_roster"]) != 216:
        raise ValueError("Source-lock roster changed")
    roster_hash = hashlib.sha256("".join(f"{c}\n" for c in lock["country_roster"]).encode()).hexdigest()
    if roster_hash != lock["country_roster_sha256"]:
        raise ValueError("Source-lock roster SHA mismatch")
    for hid, spec in specs.items():
        th = spec["falsification"]["threshold"]
        if (spec["hypothesis_id"] != hid or spec["status"] != "pre_registered"
                or th["family_id"] != FAMILY or th["family_size"] != 2
                or th["pre_years"] != list(PRE) or th["future_years"] != list(FUTURE)):
            raise ValueError(f"Registered family parameters differ: {hid}")
        for role, ref in th["source_files"].items():
            locked = lock["source_files"][role]
            if ref["path"] != locked["path"] or ref["sha256"] != locked["sha256"]:
                raise ValueError(f"Registered source differs from lock: {role}")
    for role, ref in lock["source_files"].items():
        path = source_root / ref["path"]
        if not path.is_file() or sha(path) != ref["sha256"]:
            raise ValueError(f"Source unavailable or SHA mismatch: {role}")
        columns = pq.read_table(path, columns=["country_iso3", "year"]).to_pydict()
        years = set(ref["required_years"])
        keys = sorted((c, int(y)) for c, y in zip(columns["country_iso3"], columns["year"])
                      if c in lock["country_roster"] and int(y) in years)
        if len(keys) != ref["selected_key_count"]:
            raise ValueError(f"Selected key count changed: {role}")
        key_hash = hashlib.sha256("".join(f"{c},{y}\n" for c, y in keys).encode()).hexdigest()
        if key_hash != ref["selected_key_sha256"]:
            raise ValueError(f"Selected keys changed: {role}")
    return lock, specs


def finite(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def selected_values(source_root: Path, lock: dict) -> dict[str, dict[tuple[str, int], object]]:
    allowed = set(lock["country_roster"])
    values = {}
    for role, ref in lock["source_files"].items():
        years = set(ref["required_years"])
        out = {}
        for row in pq.read_table(source_root / ref["path"], columns=["country_iso3", "year", "value"]).to_pylist():
            key = (row["country_iso3"], int(row["year"]))
            if key[0] in allowed and key[1] in years:
                if key in out:
                    raise ValueError(f"Duplicate selected value: {role} {key}")
                out[key] = row["value"]
        values[role] = out
    return values


def panel_for(role: str, lock: dict, values: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    excluded = {"remittance_missing_or_invalid": 0, "income_missing_or_invalid": 0,
                "outcome_missing_or_nonfinite": 0}
    for country in lock["country_roster"]:
        remit = [finite(values["remittance"].get((country, y))) for y in PRE]
        income = finite(values["income"].get((country, 2014)))
        baseline = [finite(values[role].get((country, y))) for y in PRE]
        future = [finite(values[role].get((country, y))) for y in FUTURE]
        bad_remit = any(v is None or v < 0 or v > 100 for v in remit)
        bad_income = income is None or income <= 0
        bad_outcome = any(v is None for v in baseline + future)
        if bad_remit or bad_income or bad_outcome:
            if bad_remit:
                excluded["remittance_missing_or_invalid"] += 1
            if bad_income:
                excluded["income_missing_or_invalid"] += 1
            if bad_outcome:
                excluded["outcome_missing_or_nonfinite"] += 1
            continue
        rows.append({"country_iso3": country, "remit_per_10pp": float(np.mean(remit))/10,
                     "remit_pp": float(np.mean(remit)), "baseline_outcome": float(np.mean(baseline)),
                     "log_income_2014": math.log(income), "future_outcome": float(np.mean(future))})
    return pd.DataFrame(rows), {"candidate_economies": len(lock["country_roster"]),
                                "complete_economies": len(rows), "excluded_by_reason_overlapping": excluded}


def fit(panel: pd.DataFrame) -> dict:
    x = np.column_stack((np.ones(len(panel)), panel["remit_per_10pp"],
                         panel["baseline_outcome"], panel["log_income_2014"]))
    y = panel["future_outcome"].to_numpy(dtype=float)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank model unavailable")
    fitted = sm.OLS(y, x).fit(cov_type="HC3")
    beta, se = float(fitted.params[1]), float(fitted.bse[1])
    p = float(2*student_t.sf(abs(beta/se), df=n-k)) if se > 0 else float("nan")
    controls = x[:, [0, 2, 3]]
    residual = x[:, 1] - controls @ np.linalg.lstsq(controls, x[:, 1], rcond=None)[0]
    squared = residual**2
    if not all(math.isfinite(v) for v in (beta, se, p)) or se <= 0 or squared.sum() <= 1e-12:
        raise ValueError("Finite HC3 estimate or identified exposure unavailable")
    return {"coefficient": beta, "standard_error": se, "p_value": p,
            "reference_df": n-k, "covariance": "HC3",
            "max_single_economy_residualized_exposure_share": float(squared.max()/squared.sum())}


def calculate(panel: pd.DataFrame, diag: dict, threshold: dict) -> tuple[dict, str]:
    n = len(panel)
    remit_pp = panel["remit_pp"].to_numpy(dtype=float) if n else np.array([])
    diag["remit_5pct_economies"] = int((remit_pp >= 5).sum())
    diag["remit_iqr_pp"] = float(np.quantile(remit_pp, .75)-np.quantile(remit_pp, .25)) if n else 0.0
    if (n < threshold["min_complete_economies"]
            or diag["remit_5pct_economies"] < threshold["min_remit_5pct_economies"]
            or diag["remit_iqr_pp"] < threshold["min_remit_iqr_pp"]):
        diag["failed_gate"] = "sample_or_exposure_floor"
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel)
        loo = []
        for i in range(n):
            try:
                loo.append(fit(panel.drop(index=i))["coefficient"])
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
    if (estimate["coefficient"] >= threshold["min_abs_beta_outcome_pp_per_10pp"]
            and estimate["p_value"] <= threshold["two_sided_p_max"]
            and estimate["loo_positive_share"] >= threshold["min_loo_sign_share"]):
        return estimate, "SUPPORTED"
    if (estimate["coefficient"] <= -threshold["min_abs_beta_outcome_pp_per_10pp"]
            and estimate["p_value"] <= threshold["two_sided_p_max"]
            and estimate["loo_negative_share"] >= threshold["min_loo_sign_share"]):
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def jwrite(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")


def pwrite(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, hid: str, spec: dict, lock: dict, panel: pd.DataFrame,
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
        "term": ["remit_per_10pp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                  ("standard_error", pa.float64()), ("p_value", pa.float64())]))
    jwrite(directory/"chart_data.json", [
        {"country_iso3": str(row.country_iso3), "remit_share_pre2015_pp": float(row.remit_pp),
         "baseline_outcome_mean": float(row.baseline_outcome),
         "future_outcome_mean": float(row.future_outcome)}
        for row in panel.itertuples(index=False)
    ])
    lines = [f"# {hid}", "", f"**Verdict: {verdict} — descriptive only.**", "",
             f"Complete economies: {len(panel)} of {diag['candidate_economies']} source-key candidates.",
             f"Pre-2015 remittance share >=5% GDP: {diag['remit_5pct_economies']}; exposure IQR: {diag['remit_iqr_pp']:.6g} pp."]
    if has_estimate:
        lines.append(f"Exposure coefficient: {estimate['coefficient']:.6g} future-outcome pp per 10-pp higher remittance share; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}; LOO fits {estimate['loo_successes']}.")
    else:
        lines.append("No coefficient was estimated because a frozen gate failed.")
    lines += ["", "The result is a baseline-adjusted forecast association. The two endpoints are one evidence family with Bonferroni p<=0.025 each. It does not identify a remittance policy effect or confer causal, policy, school, position, or featured credit.", ""]
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
              "interpretation": "Baseline-adjusted forward remittance association; two distinct outcomes form one family. Old claims remain unchanged."}
    (directory/"evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    pwrite(directory/"metric_results.parquet", {
        "verdict": [verdict], "complete_economies": [len(panel)],
        "remit_5pct_economies": [diag["remit_5pct_economies"]],
    }, pa.schema([("verdict", pa.string()), ("complete_economies", pa.int64()),
                  ("remit_5pct_economies", pa.int64())]))
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
        estimate, verdict = calculate(panel, diag, specs[hid]["falsification"]["threshold"])
        target = ROOT/"engine"/"runs"/hid
        if args.replay and not target.is_dir():
            raise ValueError(f"No run directory to replay: {hid}")
        if args.run and target.exists():
            raise ValueError(f"Run already exists: {hid}")
        with tempfile.TemporaryDirectory(prefix="ieset_remittance_family_") as temp:
            generated = Path(temp)/hid
            emit(generated, hid, specs[hid], lock, panel, diag, estimate, verdict)
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
