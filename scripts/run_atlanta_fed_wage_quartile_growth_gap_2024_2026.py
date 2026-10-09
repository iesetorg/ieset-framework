#!/usr/bin/env python3
"""Guarded Atlanta Fed wage-quartile gap study with value-blind preflight.

The design is committed first, then an OPSEC-clean one-entry source lock and
the exact raw and derived source bytes. --preflight projects only date/group
keys. --run and --check open wage values only after both first-addition commits
are unchanged. --check is a read-only field/semantic replay of the result.
"""

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
import yaml
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
HID = "atlanta_fed_wage_quartile_growth_gap_2024_2026"
SPEC_REL = f"hypotheses/labour/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
TEST_REL = f"tests/test_{HID}.py"
LOCK_REL = "data/manifests/atlanta_fed_wage_quartile_2026-10-09_source_lock.yaml"
PARQUET_REL = "data/vintages/atlanta_fed_wgt/wgt_Average_Wage_Quartile@2026-10-09T121815Z.parquet"
RAW_REL = "data/raw/atlanta_fed_wgt/wage-growth-data@2026-10-09T121815Z.xlsx"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
PARQUET_SHA = "1c3af8b31b40224c44c9530130dce74244737fb01c872a26ad3be8f7ad167eca"
RAW_SHA = "6e1201f3ab2bfe026a4013995314e96a733f64919b1165c90d1a980d6823c2a5"
PARENT_MANIFEST_SHA = "befe6a588f0e2c0de0fd42566f34e76226ce161151432e0373bf3dced401d960"
SOURCE_URL = "https://www.atlantafed.org/-/media/Project/Atlanta/FRBA/Documents/datafiles/chcs/wage-growth-tracker/wage-growth-data.xlsx"
METHOD_URL = "https://www.atlantafed.org/research-and-data/data/wage-growth-tracker"
LOW = "Lowest quartile of wage distribution"
HIGH = "Highest quartile of wage distribution"
GROUPS = (LOW, HIGH)
MONTHS = tuple(
    str(p) for p in pd.period_range("2024-01", "2026-09", freq="M")
    if str(p) != "2025-10"
)
YEARS = (2024, 2025, 2026)
DESIGN_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL, TEST_REL)
SOURCE_FILES = (LOCK_REL, PARQUET_REL, RAW_REL)
EXPECTED_THRESHOLD = {
    "first_month": "2024-01", "last_month": "2026-09",
    "excluded_month": "2025-10", "required_paired_months": 32,
    "required_selected_values": 64,
    "low_group": LOW, "high_group": HIGH,
    "support_mean_gap_pp_min_exclusive": 0.5,
    "refute_mean_gap_pp_max_exclusive": -0.5,
    "hac_maxlags": 12, "one_sided_alpha": 0.025,
    "year_sign_consistency": list(YEARS),
    "source_custody": LOCK_REL,
    "source_parquet_sha256": PARQUET_SHA,
    "raw_workbook_sha256": RAW_SHA,
}
LIMITATIONS = [
    "This is value-blind retrospective calibration of already published observations, not a future-data holdout.",
    "Wage-level quartiles are based on the mean of current and year-earlier hourly wages; outcomes are medians of individual nominal growth.",
    "Three-month smoothing, twelve-month matching, and just 32 monthly points limit HAC tail-probability precision.",
    "October 2025 is absent; the publisher substituted months in its November and December 2025 moving averages.",
    "The publisher reported a smaller CPS sample in late 2025, a 2024 topcoding change, and minor 2023-2025 revisions.",
    "The result is not a wage-level inequality, real-wage, minimum-wage, policy, or causal estimate.",
    "No old-hypothesis graduation, policy link, or school-score credit follows from this descriptive result.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_spec() -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    if any((
        spec.get("hypothesis_id") != HID,
        spec.get("status") != "pre_registered",
        spec.get("evidence_type") != "descriptive",
        spec.get("sample", {}).get("countries") != ["USA"],
        spec.get("sample", {}).get("period") != [2024, 2026],
        spec.get("sample", {}).get("temporal_structure") != "time_series",
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("falsification", {}).get("threshold") != EXPECTED_THRESHOLD,
        spec.get("steelman") != STEELMAN_REL,
        spec.get("covers_claims") != [],
        spec.get("linked_hypotheses") != [],
    )):
        raise ValueError("Atlanta preregistration differs from frozen runner contract")
    outcomes = spec.get("variables", {}).get("outcome", [])
    if len(outcomes) != 1 or outcomes[0].get("source") != "atlanta_fed_wgt:wgt_Average Wage Quartile":
        raise ValueError("Atlanta source or outcome changed")
    return spec


def verified_source() -> dict[str, Any]:
    lock = yaml.safe_load((ROOT / LOCK_REL).read_text(encoding="utf-8"))
    if lock.get("lock_version") != 1 or lock.get("source_entry_count") != 1:
        raise ValueError("Atlanta source lock version or entry count changed")
    origin = lock.get("origin") or {}
    if origin.get("full_manifest_sha256") != PARENT_MANIFEST_SHA:
        raise ValueError("Atlanta original manifest attribution changed")
    entry = lock.get("entry") or {}
    if any((
        entry.get("publisher") != "atlanta_fed_wgt",
        entry.get("series_id") != "wgt_Average Wage Quartile",
        entry.get("source_url") != SOURCE_URL,
        entry.get("methodology_url") != METHOD_URL,
        entry.get("fetch_utc") != "2026-10-09T12:18:15.440364+00:00",
        entry.get("rows") != 2492,
        entry.get("frequency") != "monthly",
        entry.get("units") != "percent, 12-month median hourly wage growth, 3mma",
        entry.get("start_date") != "1997-01-01",
        entry.get("end_date") != "2026-09-01",
        entry.get("parquet_path") != PARQUET_REL,
        entry.get("sha256") != PARQUET_SHA,
        sorted((entry.get("extra") or {}).get("groups") or []) != sorted([
            "2nd quartile of wage distribution", "3rd quartile of wage distribution",
            HIGH, "Lowest half of wage distribution", LOW, "Overall",
            "Upper half of wage distribution",
        ]),
    )):
        raise ValueError("Atlanta source-specific entry changed")
    raw = lock.get("raw_workbook") or {}
    if raw.get("path") != RAW_REL or raw.get("sha256") != RAW_SHA:
        raise ValueError("Atlanta raw-workbook custody changed")
    if sha256(ROOT / PARQUET_REL) != PARQUET_SHA or sha256(ROOT / RAW_REL) != RAW_SHA:
        raise ValueError("Atlanta pinned source bytes changed")
    return {
        "publisher": "atlanta_fed_wgt", "series_id": entry["series_id"],
        "source_url": SOURCE_URL, "methodology_url": METHOD_URL,
        "source_lock": LOCK_REL, "parquet_path": PARQUET_REL,
        "parquet_sha256": PARQUET_SHA, "raw_path": RAW_REL,
        "raw_sha256": RAW_SHA, "source_vintage_utc": entry["fetch_utc"],
        "units": entry["units"], "groups": list(GROUPS),
    }


def selected_rows(*, include_value: bool) -> pd.DataFrame:
    """With include_value=False, project only keys and never a value mask."""
    cols = ["date", "group"] + (["median_wage_growth_pct"] if include_value else [])
    frame = pd.read_parquet(ROOT / PARQUET_REL, columns=cols)
    frame["month"] = pd.to_datetime(frame["date"], errors="raise").dt.to_period("M").astype(str)
    frame = frame[frame["group"].isin(GROUPS) & frame["month"].isin(MONTHS)].copy()
    return frame.sort_values(["month", "group"]).reset_index(drop=True)


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_spec()
    source = verified_source()
    rows = selected_rows(include_value=False)
    observed = set(zip(rows["month"], rows["group"]))
    expected = {(month, group) for month in MONTHS for group in GROUPS}
    duplicate_keys = bool(rows.duplicated(["month", "group"]).any())
    passed = observed == expected and len(rows) == 64 and not duplicate_keys
    gate = {
        "window": ["2024-01", "2026-09"], "excluded_month": "2025-10",
        "paired_month_keys": len(MONTHS), "selected_group_keys": len(observed),
        "calendar_year_counts": {str(year): sum(m.startswith(str(year)) for m in MONTHS) for year in YEARS},
        "duplicate_selected_keys": duplicate_keys,
        "passed": passed, "selected_magnitudes_accessed": False,
        "selected_value_masks_accessed": False,
    }
    return gate, source


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def first_addition(rel: str) -> str:
    record = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", rel)
    commits = record.stdout.decode("ascii", errors="replace").strip().splitlines()
    if record.returncode or len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit: {rel}")
    return commits[0]


def registration_files() -> tuple[str, str, list[dict[str, str]]]:
    """Enforce two immutable prereg/source commits before any numeric access."""
    records = []
    for rel in (*DESIGN_FILES, *SOURCE_FILES):
        current = (ROOT / rel).read_bytes()
        at_head = _git("show", f"HEAD:{rel}")
        if at_head.returncode or at_head.stdout != current:
            raise RuntimeError(f"commit exact Atlanta registration bytes first: {rel}")
        records.append({"path": rel, "sha256": hashlib.sha256(current).hexdigest()})
    design = {first_addition(rel) for rel in DESIGN_FILES}
    sources = {first_addition(rel) for rel in SOURCE_FILES}
    if len(design) != 1 or len(sources) != 1:
        raise RuntimeError("Atlanta design and source files need coherent first-addition commits")
    design_commit, source_commit = design.pop(), sources.pop()
    if design_commit == source_commit or _git("merge-base", "--is-ancestor", design_commit, source_commit).returncode:
        raise RuntimeError("Atlanta source custody must follow its first design commit")
    for rel in (*DESIGN_FILES, *SOURCE_FILES):
        first = design_commit if rel in DESIGN_FILES else source_commit
        frozen = _git("show", f"{first}:{rel}")
        if frozen.returncode or frozen.stdout != (ROOT / rel).read_bytes():
            raise RuntimeError(f"Atlanta registered bytes changed after first addition: {rel}")
    for commit in (design_commit, source_commit):
        tree = _git("ls-tree", "-r", "--name-only", commit, "--", RUN_REL)
        if tree.returncode or tree.stdout.strip():
            raise RuntimeError("Atlanta result existed before value access was allowed")
    return design_commit, source_commit, records


def _raw_selected_values() -> dict[tuple[str, str], float]:
    """Recreate the published worksheet's selected cells after registration."""
    sheet = pd.read_excel(ROOT / RAW_REL, sheet_name="Average Wage Quartile", header=None)
    hdr = next(i for i in range(10) if sheet.iloc[i, 1:].notna().sum() >= 1 and pd.isna(sheet.iloc[i, 0]))
    columns = ["date"] + [str(col).strip() for col in sheet.iloc[hdr, 1:]]
    body = sheet.iloc[hdr + 1:].copy()
    body.columns = columns
    body = body[pd.to_datetime(body["date"], errors="coerce").notna()]
    body["date"] = pd.to_datetime(body["date"])
    long = body.melt(id_vars="date", var_name="group", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna()
    long["month"] = long["date"].dt.to_period("M").astype(str)
    long = long[long["group"].isin(GROUPS) & long["month"].isin(MONTHS)]
    if len(long) != 64 or long.duplicated(["month", "group"]).any():
        raise ValueError("raw workbook selected cells do not match frozen roster")
    return {(month, group): float(value) for month, group, value in
            long[["month", "group", "value"]].itertuples(index=False, name=None)}


def selected_values() -> dict[tuple[str, str], float]:
    rows = selected_rows(include_value=True)
    if len(rows) != 64 or rows.duplicated(["month", "group"]).any():
        raise ValueError("selected Atlanta pair count changed")
    raw = _raw_selected_values()
    values: dict[tuple[str, str], float] = {}
    for month, group, number in rows[["month", "group", "median_wage_growth_pct"]].itertuples(index=False, name=None):
        try:
            value = float(number)
        except (TypeError, ValueError):
            raise ValueError("nonnumeric Atlanta selected value") from None
        if not math.isfinite(value):
            raise ValueError("nonfinite Atlanta selected value")
        key = (month, group)
        if key not in raw or not math.isclose(value, raw[key], rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("raw workbook and pinned parquet disagree")
        values[key] = value
    if len(values) != 64:
        raise ValueError("Atlanta selected values are incomplete")
    return values


def hac_mean_test(gaps: list[float]) -> dict[str, float]:
    """Frozen Bartlett Newey-West intercept variance, with finite-sample t."""
    x = np.asarray(gaps, dtype=float)
    n = len(x)
    if n != 32 or not np.isfinite(x).all():
        raise ValueError("HAC input needs exactly 32 finite monthly gaps")
    mean = float(x.mean())
    residual = x - mean
    long_run = float(np.dot(residual, residual) / n)
    for lag in range(1, 13):
        long_run += 2.0 * (1.0 - lag / 13.0) * float(np.dot(residual[lag:], residual[:-lag]) / n)
    long_run *= n / (n - 1)
    if not math.isfinite(long_run) or long_run <= 0:
        raise ValueError("HAC variance is zero, negative, or nonfinite")
    se = math.sqrt(long_run / n)
    df = n - 1
    support_t = (mean - 0.5) / se
    refute_t = (mean + 0.5) / se
    critical = float(student_t.ppf(0.975, df))
    return {
        "mean_gap_pp": mean, "hac_se_pp": se, "hac_lags": 12,
        "t_df": df, "support_t_vs_plus_0_5": support_t,
        "support_one_sided_p": float(student_t.sf(support_t, df)),
        "refute_t_vs_minus_0_5": refute_t,
        "refute_one_sided_p": float(student_t.cdf(refute_t, df)),
        "lower_one_sided_97_5_pp": mean - critical * se,
        "upper_one_sided_97_5_pp": mean + critical * se,
    }


def classify(stats: dict[str, float], year_means: dict[str, float]) -> tuple[str, str]:
    positive = all(year_means[str(year)] > 0 for year in YEARS)
    negative = all(year_means[str(year)] < 0 for year in YEARS)
    if stats["support_one_sided_p"] <= 0.025 and positive:
        return "SUPPORTED", "mean low-minus-high growth gap clears +0.5 pp with HAC(12) and three positive years"
    if stats["refute_one_sided_p"] <= 0.025 and negative:
        return "REFUTED", "mean low-minus-high growth gap clears -0.5 pp in reverse with HAC(12) and three negative years"
    return "PARTIAL", "fixed gap did not clear a substantive tail bound with three matching annual signs"


def evaluate() -> tuple[str, str, dict[str, Any]]:
    values = selected_values()
    monthly = [{"month": month, "gap_pp": values[(month, LOW)] - values[(month, HIGH)]}
               for month in MONTHS]
    gaps = [row["gap_pp"] for row in monthly]
    stats = hac_mean_test(gaps)
    years = {str(year): float(np.mean([row["gap_pp"] for row in monthly
                                       if row["month"].startswith(str(year))])) for year in YEARS}
    label, reason = classify(stats, years)
    estimate = {"method": "mean monthly low-minus-high quartile growth gap; HAC(12) intercept test",
                "n_months": 32, "n_selected_values": 64, "annual_mean_gap_pp": years,
                "statistics": stats, "monthly_gap": monthly}
    return label, reason, estimate


def calculate() -> tuple[dict[str, Any], dict[str, Any], str, str, dict[str, Any] | None]:
    gate, source = preflight()
    if not gate["passed"]:
        return gate, source, "INCONCLUSIVE_DATA_PENDING", "fixed Atlanta month/group key roster invalid", None
    try:
        label, reason, estimate = evaluate()
    except (KeyError, ValueError, TypeError, OverflowError) as error:
        label, reason, estimate = "INCONCLUSIVE_DATA_PENDING", f"selected Atlanta values invalid: {error}", None
    return gate, source, label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only field replay of the Atlanta Fed wage-quartile result."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


COEFFICIENT_COLUMNS = ["term", "coefficient", "std_error", "p_value", "p_refute", "n_obs", "method"]


def artifact_records(stamp: str, design_commit: str, source_commit: str,
                     files: list[dict[str, str]], gate: dict[str, Any], source: dict[str, Any],
                     label: str, reason: str, estimate: dict[str, Any] | None) -> tuple[Any, ...]:
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": design_commit, "source_custody_commit": source_commit,
        "template": "descriptive", "preflight": gate, "estimate": estimate,
        "correction": {"disposition": "new_descriptive_calibration_only", "school_score_credit": 0},
        "limitations": LIMITATIONS,
        "data_status": {"variables_missing": [] if estimate is not None else ["selected_quartile_values_invalid"],
                        "input_status": "verified" if estimate is not None else "unverified",
                        "input_vintages": [PARQUET_REL, RAW_REL]},
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": design_commit, "source_custody_commit": source_commit,
        "status": label, "registration_files": files, "vintages": [source],
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "labour"},
        "preregistration": {"design_commit": design_commit, "source_commit": source_commit,
                            "steelman": STEELMAN_REL, "registration_files": files,
                            "gate": EXPECTED_THRESHOLD},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": [source], "window": ["2024-01", "2026-09"],
                 "excluded_month": "2025-10"},
        "results": estimate, "limitations": LIMITATIONS,
        "credit_ceiling": "descriptive calibration only; zero policy, old-case, and school-score credit",
    }
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Design preregistration: `{design_commit}`. Source custody: `{source_commit}`.\n\n"
        "Sample: 32 fixed US monthly observations, January 2024–September 2026, "
        "excluding unavailable October 2025.\n\n"
        "Method: Atlanta Fed matched-worker median nominal 12-month hourly-wage growth, "
        "lowest minus highest average-wage quartile, three-month moving averages. "
        "One-sided HAC(12) tests use the frozen +/-0.5 pp bounds and three-year sign rule.\n"
    )
    if estimate is not None:
        s = estimate["statistics"]
        card += (
            f"\nMean gap: {s['mean_gap_pp']:+.8g} pp; HAC SE: {s['hac_se_pp']:.8g} pp.\n"
            f"One-sided p for >+0.5 pp: {s['support_one_sided_p']:.8g}; "
            f"for <-0.5 pp: {s['refute_one_sided_p']:.8g}.\n"
            f"Year means (pp): {estimate['annual_mean_gap_pp']}.\n"
        )
    card += (
        "\nThis already published, short, smoothed series supports descriptive "
        "calibration only. It cannot establish wage inequality, real-wage gains, "
        "policy causation, or school credit.\n"
    )
    chart = {"hypothesis_id": HID, "verdict": label,
             "monthly_gap": estimate["monthly_gap"] if estimate else [],
             "support_bound_pp": 0.5, "refute_bound_pp": -0.5}
    rows = [] if estimate is None else [{
        "term": "mean_low_minus_high_growth_gap_pp",
        "coefficient": estimate["statistics"]["mean_gap_pp"],
        "std_error": estimate["statistics"]["hac_se_pp"],
        "p_value": estimate["statistics"]["support_one_sided_p"],
        "p_refute": estimate["statistics"]["refute_one_sided_p"],
        "n_obs": 32, "method": "Newey-West Bartlett HAC(12), t31; one-sided +/-0.5 pp tests",
    }]
    return diagnostics, manifest, packet, card, chart, rows


def write_run(design_commit: str, source_commit: str, files: list[dict[str, str]],
              gate: dict[str, Any], source: dict[str, Any], label: str,
              reason: str, estimate: dict[str, Any] | None) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        stamp, design_commit, source_commit, files, gate, source, label, reason, estimate)
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(card, encoding="utf-8")
    (RUN_DIR / "replication.py").write_text(replication_wrapper(), encoding="utf-8")
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "wrote_files": True, "estimate": estimate}


def run_one() -> dict[str, Any]:
    design_commit, source_commit, files = registration_files()
    if RUN_DIR.exists():
        raise FileExistsError(f"Atlanta result exists: {RUN_REL}; use --check")
    gate, source, label, reason, estimate = calculate()
    return write_run(design_commit, source_commit, files, gate, source, label, reason, estimate)


def check_one() -> dict[str, Any]:
    design_commit, source_commit, files = registration_files()
    saved = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    saved_manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text(encoding="utf-8"))
    saved_packet = yaml.safe_load((RUN_DIR / "evidence_packet.yaml").read_text(encoding="utf-8"))
    saved_card = (RUN_DIR / "result_card.md").read_text(encoding="utf-8")
    saved_chart = json.loads((RUN_DIR / "chart_data.json").read_text(encoding="utf-8"))
    saved_wrapper = (RUN_DIR / "replication.py").read_text(encoding="utf-8")
    saved_spec = (RUN_DIR / "hypothesis.yaml").read_bytes()
    saved_coefficients = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    gate, source, label, reason, estimate = calculate()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        saved["run_utc"], design_commit, source_commit, files,
        gate, source, label, reason, estimate)
    if any((saved != diagnostics, saved_manifest != manifest, saved_packet != packet,
            saved_card != card, saved_chart != chart, saved_wrapper != replication_wrapper(),
            saved_spec != (ROOT / SPEC_REL).read_bytes())):
        raise AssertionError("Atlanta packet differs from pinned read-only field replay")
    pd.testing.assert_frame_equal(saved_coefficients,
                                  pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS),
                                  check_dtype=False)
    return {"hypothesis_id": HID, "verified": True, "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="source hashes and keys only")
    mode.add_argument("--run", action="store_true", help="guarded first result")
    mode.add_argument("--check", action="store_true", help="read-only field replay")
    args = parser.parse_args()
    if args.run:
        result = run_one()
    elif args.check:
        result = check_one()
    else:
        result = preflight()[0]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
