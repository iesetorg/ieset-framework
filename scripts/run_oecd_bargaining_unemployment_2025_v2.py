#!/usr/bin/env python3
"""Guarded prospective OECD bargaining/unemployment temporal holdout.

--lock reads exposure values and unemployment keys only. Commit its two
source-slice files separately before --run. --run is the first path that reads
selected unemployment values, null masks, or observation statuses.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.dataset as ds
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_bargaining_unemployment_2025_temporal_holdout_v2"
SPEC = f"hypotheses/labour/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
ROSTER = f"data/pinned_evidence/{ID}_key_roster.csv"
AUDIT = "engine/audits/legacy_2025_unemployment_holdout_prereg_2026-10-10.md"
PREFLIGHT = "scripts/preflight_oecd_bargaining_unemployment_2025_v2.py"
RUNNER = "scripts/run_oecd_bargaining_unemployment_2025_v2.py"
SLICE = f"data/pinned_evidence/{ID}_source_slice.csv"
LOCK = f"data/pinned_evidence/{ID}.manifest.json"
RUN_DIR = f"engine/runs/{ID}"
SUMMARY = f"engine/audits/{ID}_results_2026-10-10.md"
ROSTER_SHA = "0160f69e5ff5a0995ba95da2d1dec1ace90aa251a07e1084414653591c81eebd"
FAMILY = "oecd_bargaining_unemployment_2025_temporal_holdout_v2_2026_10_10"
MARGIN = 0.2
ALPHA = 0.05
MIN_N = 24
MIN_IQR = 20.0
MAX_HAT = 0.35
MAX_PARTIALLED_X_SHARE = 0.20
CORRECTION = {
    "disposition": "descriptive_calibration_only",
    "family_id": FAMILY, "family_size": 1,
    "family_alpha_one_sided": ALPHA,
    "archive_wide_multiplicity_control": False,
    "school_score_eligible": False, "school_score_credit": 0,
    "position_score_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "One 26-country cross-section is a descriptive association, not a causal estimate.",
    "Bargaining coverage is endogenous to labour institutions, industry mix and prior employment.",
    "Country-specific 2023-2025 shocks can confound the forward association despite baseline adjustment.",
    "The 2025 OECD LFS vintage may overlap other IESET studies; the holdout is relative to the named old fit.",
    "The old same-commit manifest and diagnostics conflict; neither verdict transfers to this v2.",
    "No causal, policy, school, position or featured credit.",
]


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}: {commits}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT
    ).returncode == 0


def unchanged_since_first(relative: str, commit: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{commit}:{relative}"):
        raise RuntimeError(f"frozen file differs from first addition: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def registration_and_runner() -> tuple[str, str]:
    frozen = [SPEC, STEELMAN, ROSTER, AUDIT, PREFLIGHT]
    additions = {first_addition(relative) for relative in frozen}
    if len(additions) != 1:
        raise RuntimeError("blind registration package must enter in one commit")
    registration = additions.pop()
    for relative in frozen:
        unchanged_since_first(relative, registration)
    runner = first_addition(RUNNER)
    unchanged_since_first(RUNNER, runner)
    if not strict_ancestor(registration, runner):
        raise RuntimeError("runner must follow registration in a separate commit")
    return registration, runner


def spec_threshold() -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered":
        raise RuntimeError("unexpected frozen specification")
    threshold = spec["falsification"]["threshold"]
    if (threshold["family_id"] != FAMILY or threshold["family_size"] != 1
            or threshold["family_alpha_one_sided"] != ALPHA
            or threshold["noninferiority_margin_pp_per_ten_coverage_pp"] != MARGIN
            or threshold["min_valid_countries"] != MIN_N
            or threshold["min_exposure_iqr_pp"] != MIN_IQR
            or threshold["max_hat_diagonal"] != MAX_HAT
            or threshold["max_top_partialled_exposure_square_share"] != MAX_PARTIALLED_X_SHARE
            or threshold["key_roster_sha256"] != ROSTER_SHA):
        raise RuntimeError("frozen spec and runner disagree")
    return threshold


def roster() -> list[str]:
    if digest(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("key-only roster hash changed")
    with (ROOT / ROSTER).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    countries = [row["country_iso3"] for row in rows]
    if (len(countries) != 26 or countries != sorted(set(countries))
            or any(row["exposure_year"] != "2023"
                   or row["baseline_year"] != "2023"
                   or row["outcome_year"] != "2025" for row in rows)):
        raise RuntimeError("frozen key roster changed")
    return countries


def source_files() -> dict[str, dict[str, Any]]:
    sources = spec_threshold()["source_files"]
    for role, pin in sources.items():
        path = ROOT / pin["path"]
        manifest = ROOT / pin["manifest"]
        if digest(path) != pin["sha256"] or digest(manifest) != pin["manifest_sha256"]:
            raise RuntimeError(f"pinned source or fetch manifest changed: {role}")
        rows = yaml.safe_load(manifest.read_text()).get("entries", [])
        if not any(row.get("parquet_path") == pin["path"]
                   and row.get("sha256") == pin["sha256"] for row in rows):
            raise RuntimeError(f"fetch manifest does not pin source: {role}")
    return sources


def preflight() -> dict[str, Any]:
    output = subprocess.check_output(
        [sys.executable, str(ROOT / PREFLIGHT), "--source-root", str(ROOT)],
        cwd=ROOT,
    )
    report = json.loads(output)
    report.pop("source_root", None)
    if (report.get("status") != "key_only_preflight_pass"
            or report.get("selected_unemployment_values_or_status_read") is not False
            or report.get("roster_count") != 26
            or report.get("old_lfs_2025_key_count") != 0
            or report.get("new_lfs_joint_key_count") != 26):
        raise RuntimeError("frozen key-only preflight failed")
    return report


def slice_bytes(countries: list[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([
        "country_iso3", "coverage_measure", "coverage_year",
        "lfs_measure", "lfs_sex", "lfs_age", "lfs_labour_force_status",
        "baseline_year", "outcome_year",
    ])
    for country in countries:
        writer.writerow([country, "ERB", 2023, "UNE_RATE", "_T", "Y15T64", "UNE", 2023, 2025])
    return buffer.getvalue().encode()


def lock_payload(registration: str, runner: str, sources: dict[str, Any],
                 preflight_report: dict[str, Any], source_slice: bytes) -> dict[str, Any]:
    return {
        "schema": "ieset-source-slice-lock-v1",
        "hypothesis_id": ID, "family_id": FAMILY,
        "preregistration_commit": registration, "runner_commit": runner,
        "sources": sources,
        "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
        "source_slice": {"path": SLICE, "sha256": digest_bytes(source_slice)},
        "key_only_preflight": preflight_report,
        "selected_outcome_values_opened_before_lock": False,
        "selected_outcome_null_masks_opened_before_lock": False,
        "selected_outcome_status_opened_before_lock": False,
    }


def write_lock() -> None:
    registration, runner = registration_and_runner()
    if (ROOT / RUN_DIR).exists() or (ROOT / SUMMARY).exists():
        raise RuntimeError("measured result artifacts exist before lock")
    sources = source_files()
    countries = roster()
    preflight_report = preflight()
    source_slice = slice_bytes(countries)
    for relative in (SLICE, LOCK):
        if (ROOT / relative).exists():
            raise FileExistsError(relative)
    (ROOT / SLICE).write_bytes(source_slice)
    (ROOT / LOCK).write_text(
        json.dumps(lock_payload(registration, runner, sources, preflight_report, source_slice),
                   indent=2, sort_keys=True) + "\n"
    )
    print(f"wrote key-only {SLICE} and {LOCK}; commit both before any outcome access")


def committed_lock(registration: str, runner: str) -> str:
    sources = source_files()
    countries = roster()
    source_slice = slice_bytes(countries)
    preflight_report = preflight()
    expected = lock_payload(registration, runner, sources, preflight_report, source_slice)
    if (ROOT / SLICE).read_bytes() != source_slice:
        raise RuntimeError("source slice differs from frozen key roster")
    if json.loads((ROOT / LOCK).read_text()) != expected:
        raise RuntimeError("source lock differs from frozen inputs")
    lock = first_addition(LOCK)
    if first_addition(SLICE) != lock or not strict_ancestor(runner, lock):
        raise RuntimeError("source slice and lock must enter together after runner")
    unchanged_since_first(SLICE, lock)
    unchanged_since_first(LOCK, lock)
    if git("ls-tree", "-r", "--name-only", lock, "--", RUN_DIR, SUMMARY).strip():
        raise RuntimeError("lock commit contains measured result artifacts")
    return lock


def exposure_values(countries: list[str], sources: dict[str, Any]) -> dict[str, float]:
    frame = pd.read_parquet(ROOT / sources["coverage"]["path"], columns=[
        "REF_AREA", "MEASURE", "period", "value", "OBS_STATUS",
    ])
    frame = frame[
        frame.MEASURE.eq("ERB") & frame.period.eq(2023)
        & frame.OBS_STATUS.eq("A") & frame.REF_AREA.isin(countries)
    ]
    if len(frame) != 26 or frame.REF_AREA.nunique() != 26:
        raise RuntimeError("frozen exposure cells changed")
    values = pd.to_numeric(frame.value, errors="coerce")
    if not values.notna().all() or not values.between(0, 100).all():
        raise RuntimeError("invalid pinned exposure")
    return dict(zip(frame.REF_AREA.astype(str), values.astype(float)))


def measured_panel(countries: list[str], sources: dict[str, Any],
                   lock_commit: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """First and only entry point that opens selected LFS values/status/nulls."""
    if first_addition(LOCK) != lock_commit:
        raise RuntimeError("committed source lock required")
    selector = (
        (pc.field("MEASURE") == "UNE_RATE")
        & (pc.field("SEX") == "_T")
        & (pc.field("AGE") == "Y15T64")
        & (pc.field("LABOUR_FORCE_STATUS") == "UNE")
        & pc.field("REF_AREA").isin(countries)
        & pc.field("period").isin([2023, 2025])
    )
    frame = ds.dataset(ROOT / sources["unemployment"]["path"]).to_table(
        columns=["REF_AREA", "period", "value", "OBS_STATUS"],
        filter=selector,
    ).to_pandas()
    if frame.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("selected unemployment keys duplicated")
    observed = {
        (str(row.REF_AREA), int(row.period)): (row.value, row.OBS_STATUS)
        for row in frame.itertuples(index=False)
    }
    exposures = exposure_values(countries, sources)
    records = []
    dropped = []
    for country in countries:
        pair = [observed.get((country, year)) for year in (2023, 2025)]
        if any(item is None for item in pair):
            dropped.append({"country_iso3": country, "reason": "missing_key"})
            continue
        numeric = [pd.to_numeric(item[0], errors="coerce") for item in pair]
        if not all(math.isfinite(float(value)) and 0 <= float(value) <= 100 for value in numeric):
            dropped.append({"country_iso3": country, "reason": "nonfinite_or_out_of_range"})
            continue
        if not all(item[1] == "A" for item in pair):
            dropped.append({"country_iso3": country, "reason": "non_actual_status"})
            continue
        baseline, future = map(float, numeric)
        records.append({
            "country_iso3": country, "coverage_per_ten": exposures[country] / 10.0,
            "baseline_unemployment": baseline, "unemployment_change": future - baseline,
        })
    panel = pd.DataFrame(records, columns=[
        "country_iso3", "coverage_per_ten", "baseline_unemployment", "unemployment_change",
    ])
    return panel, {
        "roster_countries": 26, "valid_countries": len(panel),
        "dropped_countries": dropped,
        "selected_outcome_values_read_after_lock": True,
    }


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    def inconclusive(reason: str) -> dict[str, Any]:
        return {"verdict": "INCONCLUSIVE", "reason": reason, "gate": gate, "primary": None}
    if len(panel) < MIN_N:
        return inconclusive("fewer than 24 complete actual-status countries")
    x = panel.coverage_per_ten.to_numpy(float)
    baseline = panel.baseline_unemployment.to_numpy(float)
    y = panel.unemployment_change.to_numpy(float)
    iqr_pp = float(10 * (np.quantile(x, .75) - np.quantile(x, .25)))
    gate["exposure_iqr_pp_complete"] = iqr_pp
    if not math.isfinite(iqr_pp) or iqr_pp < MIN_IQR:
        return inconclusive("complete-case exposure IQR below frozen floor")
    design = np.column_stack([np.ones(len(panel)), x, baseline])
    rank = int(np.linalg.matrix_rank(design))
    gate["model_rank"] = rank
    if rank != 3 or len(panel) - rank < 20:
        return inconclusive("cross-sectional model rank or residual degrees of freedom failed")
    hat = np.sum(np.linalg.qr(design)[0] ** 2, axis=1)
    gate["max_hat_diagonal"] = float(hat.max())
    if gate["max_hat_diagonal"] > MAX_HAT:
        return inconclusive("maximum diagonal leverage exceeds frozen limit")
    residual_x = x - np.column_stack([np.ones(len(panel)), baseline]) @ np.linalg.lstsq(
        np.column_stack([np.ones(len(panel)), baseline]), x, rcond=None
    )[0]
    squares = residual_x ** 2
    if not math.isfinite(float(squares.sum())) or squares.sum() <= 0:
        return inconclusive("no partialled-out exposure variation")
    gate["max_top_partialled_exposure_square_share"] = float(squares.max() / squares.sum())
    if gate["max_top_partialled_exposure_square_share"] > MAX_PARTIALLED_X_SHARE:
        return inconclusive("partialled-out exposure is too concentrated")
    fit = sm.OLS(y, design).fit(cov_type="HC3")
    beta, se = float(fit.params[1]), float(fit.bse[1])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return inconclusive("non-finite or nonpositive HC3 uncertainty")
    df = len(panel) - rank
    critical = float(student_t.ppf(1 - ALPHA, df))
    if not math.isfinite(critical):
        return inconclusive("non-finite one-sided t critical value")
    lower, upper = beta - critical * se, beta + critical * se
    primary = {
        "coefficient_pp_per_ten_coverage_pp": beta, "std_error_hc3": se,
        "one_sided_95_lower": lower, "one_sided_95_upper": upper,
        "noninferiority_margin": MARGIN, "n_countries": len(panel),
        "df_inference": df,
        "p_one_sided_support": float(student_t.cdf((beta - MARGIN) / se, df)),
        "p_one_sided_refute": float(student_t.sf((beta - MARGIN) / se, df)),
        "method": "one-row-per-country OLS; baseline unemployment control; HC3; Student t(n-3)",
    }
    if upper <= MARGIN:
        verdict, reason = "SUPPORTED", "upper one-sided 95 percent bound clears the frozen non-inferiority margin"
    elif lower > MARGIN:
        verdict, reason = "REFUTED", "lower one-sided 95 percent bound exceeds the frozen margin"
    else:
        verdict, reason = "PARTIAL", "method-valid estimate does not resolve the frozen non-inferiority margin"
    return {"verdict": verdict, "reason": reason, "gate": gate, "primary": primary}


def summary_text(result: dict[str, Any], registration: str, lock: str) -> str:
    primary = result["primary"]
    estimate_text = "No coefficient estimated." if primary is None else (
        f"Coverage coefficient {primary['coefficient_pp_per_ten_coverage_pp']:+.6g} "
        f"unemployment points per ten coverage points; one-sided 95 percent "
        f"bounds [{primary['one_sided_95_lower']:+.6g}, {primary['one_sided_95_upper']:+.6g}]."
    )
    return (
        "# OECD bargaining coverage and 2025 unemployment holdout\n\n"
        f"Preregistration {registration}; source slice lock {lock}.\n\n"
        f"**{result['verdict']}** — {result['reason']}.\n\n"
        f"Complete countries: {result['gate']['valid_countries']} of 26. "
        f"{estimate_text} The frozen margin is +0.2 unemployment point "
        "per ten coverage points. This is one descriptive temporal holdout, "
        "with no causal, school, policy, position, or featured credit.\n"
    )


def artifact_payload(result: dict[str, Any], registration: str,
                     lock: str, stamp: str) -> dict[str, Any]:
    sources = spec_threshold()["source_files"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC, "topic": "labour"},
        "preregistration": {
            "spec_commit": registration, "source_lock_commit": lock,
            "family_id": FAMILY, "family_size": 1,
            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
            "source_slice": SLICE, "source_lock": LOCK, "steelman": STEELMAN,
        },
        "reproduction": {
            "runner": RUNNER, "run_dir": RUN_DIR,
            "command": f"python3 {RUNNER} --verify",
        },
        "verdict": {
            "raw": result["verdict"], "bucket": result["verdict"].lower(),
            "reason": result["reason"],
        },
        "data": {"inputs": sources, "sample": result["gate"]},
        "results": {"primary": result["primary"]},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": ID, "family_id": FAMILY,
        "verdict": result["verdict"], "verdict_label": result["verdict"],
        "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock, "source_lock": LOCK,
        "template": "descriptive", "gate_checks": result["gate"],
        "primary": result["primary"],
        "data_status": {"variables_missing": [], "input_vintages": sources},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock,
        "source_lock": LOCK, "status": result["verdict"],
        "verdict_label": result["verdict"], "vintages": sources,
        "derived_panel": result["gate"], "correction": CORRECTION,
    }
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import subprocess, sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    chart = {"hypothesis_id": ID, "family_id": FAMILY,
             "verdict": result["verdict"], "primary": result["primary"]}
    return {
        "packet": packet, "diagnostics": diagnostics, "manifest": manifest,
        "wrapper": wrapper, "chart": chart,
    }


def write_result(result: dict[str, Any], registration: str, lock: str) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured result already exists")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = artifact_payload(result, registration, lock, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(summary_text(result, registration, lock))
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    primary = result["primary"]
    row = [] if primary is None else [{"term": "coverage_per_ten", **primary}]
    pd.DataFrame(row, columns=[
        "term", "coefficient_pp_per_ten_coverage_pp", "std_error_hc3",
        "one_sided_95_lower", "one_sided_95_upper", "noninferiority_margin",
        "n_countries", "df_inference", "p_one_sided_support",
        "p_one_sided_refute", "method",
    ]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(result, registration, lock))


def compare(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label} mapping differs")
        for key, value in expected.items():
            compare(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label} list differs")
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not isinstance(actual, (float, int)) or not math.isclose(
            float(actual), expected, rel_tol=1e-10, abs_tol=1e-12
        ):
            raise AssertionError(f"{label} numeric result differs")
    elif actual != expected:
        raise AssertionError(f"{label} differs")


def verify_result(result: dict[str, Any], registration: str, lock: str) -> None:
    folder = ROOT / RUN_DIR
    diagnostics = json.loads((folder / "diagnostics.json").read_text())
    stamp = diagnostics["run_utc"]
    datetime.fromisoformat(stamp)
    expected = artifact_payload(result, registration, lock, stamp)
    compare(diagnostics, expected["diagnostics"], "diagnostics")
    compare(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], "manifest")
    compare(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], "packet")
    compare(json.loads((folder / "chart_data.json").read_text()), expected["chart"], "chart")
    if (folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes():
        raise AssertionError("spec snapshot differs")
    if (folder / "replication.py").read_text() != expected["wrapper"]:
        raise AssertionError("replication wrapper differs")
    if (folder / "result_card.md").read_text() != summary_text(result, registration, lock):
        raise AssertionError("result card differs")
    if (ROOT / SUMMARY).read_text() != summary_text(result, registration, lock):
        raise AssertionError("summary differs")
    primary = result["primary"]
    expected_rows = [] if primary is None else [{"term": "coverage_per_ten", **primary}]
    actual_rows = pd.read_parquet(folder / "coefficients.parquet").to_dict("records")
    compare(actual_rows, expected_rows, "coefficients")
    print(f"exact replay passed: {ID} {result['verdict']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.lock:
        write_lock()
        return 0
    registration, runner = registration_and_runner()
    lock = committed_lock(registration, runner)
    countries = roster()
    sources = source_files()
    panel, gate = measured_panel(countries, sources, lock)
    result = estimate(panel, gate)
    if args.run:
        write_result(result, registration, lock)
        print(f"wrote {RUN_DIR}: {result['verdict']}")
    else:
        verify_result(result, registration, lock)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
