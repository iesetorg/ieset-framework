#!/usr/bin/env python3
"""Pinned, descriptive Argentina core-CPI holdout with a preregistration gate.

Default/--preflight hashes the official source, its raw capture and manifest,
then reads date/component/country keys only. --run and --check read index
values only after the unchanged first-addition spec, steelman, runner,
source manifest, raw capture, and parquet are verified in Git. No mode
assigns school-score credit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
HID = "argentina_core_inflation_2025_2026_durability_holdout_v2"
OLD_ID = "milei_reforms_reduce_argentine_inflation"
SPEC_REL = f"hypotheses/monetary/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
SOURCE_REL = "data/vintages/indec_ipc/all@2026-10-09T121609Z.parquet"
SOURCE_SHA256 = "f093e71a89254c3c51d265bc45f1b4ef58e7e59a47113dd4e59416620b03bd98"
SOURCE_MANIFEST_REL = "data/manifests/fetch_run_2026-10-09T121824Z.yaml"
SOURCE_MANIFEST_SHA256 = "befe6a588f0e2c0de0fd42566f34e76226ce161151432e0373bf3dced401d960"
RAW_REL = "data/raw/indec_ipc/all@2026-10-09T121609Z.json"
RAW_SHA256 = "5bc83847b0fe5f673ae0f7887b1337abdd1373eb183b757d439eb7216aa83c96"
OLD_DIAGNOSTICS_REL = f"engine/runs/{OLD_ID}/diagnostics.json"
OLD_DIAGNOSTICS_SHA256 = "0b302ea5ea7b81dcbcc17f2bd5e4d85f6fead09d6c29b9ff51409b6cc0bf4b4d"
OLD_CARD_REL = f"engine/runs/{OLD_ID}/result_card.md"
OLD_CARD_SHA256 = "3a04a29e128a4fa40a392cba30ac04dc626ad6ddf684a884af85e3933176b70e"
REGISTRATION_FILES = (
    SPEC_REL, STEELMAN_REL, RUNNER_REL,
    SOURCE_MANIFEST_REL, SOURCE_REL, RAW_REL,
)
COUNTRY = "ARG"
COMPONENTS = ("core", "headline", "services")
COMPONENT_SERIES = {
    "core": "148.3_INUCLEONAL_DICI_M_19",
    "headline": "148.3_INIVELNAL_DICI_M_26",
    "services": "147.3_ISERVICNAL_DICI_T_22",
}
# Keep the published INDEC component tokens exact so a changed map fails closed.
BASELINE = "2025-08"
MONTHS = (
    "2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02",
    "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08",
)
ALL_MONTHS = (BASELINE, *MONTHS)
MIN_INDEX_CELLS = len(COMPONENTS) * len(ALL_MONTHS)
CORE_THRESHOLD = 3.0
DECIMAL_THRESHOLD = Decimal("3.0")
MIN_CORE_MONTHS = 9
EXPECTED_SOURCE = {
    "path": SOURCE_REL, "sha256": SOURCE_SHA256,
    "manifest": SOURCE_MANIFEST_REL, "manifest_sha256": SOURCE_MANIFEST_SHA256,
    "raw_path": RAW_REL, "raw_sha256": RAW_SHA256,
    "publisher": "indec_ipc", "series_id": "all",
}
EXPECTED_THRESHOLD = {
    "old_hypothesis_id": OLD_ID,
    "old_result_seen": "INCONCLUSIVE_DATA_PENDING",
    "country_iso3": COUNTRY,
    "baseline_month": BASELINE,
    "endpoint_months": list(MONTHS),
    "required_components": list(COMPONENTS),
    "required_index_cells": MIN_INDEX_CELLS,
    "core_median_support_max_pct": CORE_THRESHOLD,
    "core_months_at_or_below_3_support_min": MIN_CORE_MONTHS,
    "source_file": EXPECTED_SOURCE,
}
LIMITATIONS = [
    "Descriptive single-country CPI-component durability, not a policy-effect estimate.",
    "The old headline CPI run was INCONCLUSIVE_DATA_PENDING and is not repaired here.",
    "Its old result card mentions an earlier supported result that was not reproducible in that run.",
    "The pinned source was fetched before registration; only internal pre-analysis custody is claimed.",
    "Exchange rates, recession, administered prices, and external shocks remain alternative explanations.",
    "No causal, school-score, or automatic policy-evidence credit follows from this result.",
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
        spec.get("sample", {}).get("countries") != [COUNTRY],
        spec.get("sample", {}).get("period") != [2025, 2026],
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("covers_claims") != [],
        spec.get("linked_hypotheses") != [],
        spec.get("falsification", {}).get("threshold") != EXPECTED_THRESHOLD,
    )):
        raise ValueError("Argentina core holdout differs from the frozen runner contract")
    observed_sources = [item.get("source") for item in spec["variables"]["outcome"]]
    expected_sources = [f"indec_ipc:{COMPONENT_SERIES[c]}" for c in COMPONENTS]
    if observed_sources != expected_sources:
        raise ValueError("registered component source mapping changed")
    return spec


def verified_source() -> dict[str, Any]:
    for rel, expected in (
        (SOURCE_REL, SOURCE_SHA256),
        (SOURCE_MANIFEST_REL, SOURCE_MANIFEST_SHA256),
        (RAW_REL, RAW_SHA256),
        (OLD_DIAGNOSTICS_REL, OLD_DIAGNOSTICS_SHA256),
        (OLD_CARD_REL, OLD_CARD_SHA256),
    ):
        if sha256(ROOT / rel) != expected:
            raise ValueError(f"pinned source or old-run hash mismatch: {rel}")
    manifest = yaml.safe_load((ROOT / SOURCE_MANIFEST_REL).read_text(encoding="utf-8"))
    entries = [e for e in manifest.get("entries", []) if e.get("parquet_path") == SOURCE_REL]
    if len(entries) != 1:
        raise ValueError("manifest lacks one exact pinned INDEC parquet entry")
    entry = entries[0]
    url = str(entry.get("source_url", ""))
    if any((
        entry.get("publisher") != "indec_ipc",
        entry.get("series_id") != "all",
        entry.get("sha256") != SOURCE_SHA256,
        entry.get("extra", {}).get("components", {}).get("core") != COMPONENT_SERIES["core"],
        entry.get("extra", {}).get("components", {}).get("headline") != COMPONENT_SERIES["headline"],
        entry.get("extra", {}).get("components", {}).get("services") != COMPONENT_SERIES["services"],
        not url.startswith("https://apis.datos.gob.ar/series/api/series?ids="),
    )):
        raise ValueError("manifest publisher, hash, or INDEC component identity changed")
    old = json.loads((ROOT / OLD_DIAGNOSTICS_REL).read_text(encoding="utf-8"))
    if old.get("verdict_label") != "INCONCLUSIVE_DATA_PENDING":
        raise ValueError("old result disclosure no longer matches pinned run")
    return {
        **EXPECTED_SOURCE, "source_url": url,
        "methodology_url": entry.get("methodology_url"),
        "license": entry.get("license"),
        "old_diagnostics_path": OLD_DIAGNOSTICS_REL,
        "old_diagnostics_sha256": OLD_DIAGNOSTICS_SHA256,
        "old_result_card_sha256": OLD_CARD_SHA256,
    }


def selected_rows(*, include_index: bool) -> pd.DataFrame:
    """The preflight branch projects dimension keys, never index or mom_pct."""
    columns = ["date", "component", "country_iso3"]
    if include_index:
        columns.append("index")
    frame = pd.read_parquet(ROOT / SOURCE_REL, columns=columns)
    frame = frame[
        (frame["country_iso3"] == COUNTRY)
        & frame["component"].isin(COMPONENTS)
        & frame["date"].isin(pd.to_datetime([f"{month}-01" for month in ALL_MONTHS]))
    ].copy()
    if frame["date"].isna().any():
        raise ValueError("null date in selected source rows")
    frame["month"] = frame["date"].dt.strftime("%Y-%m")
    if frame.duplicated(["component", "month"]).any():
        raise ValueError("duplicate selected component-month keys")
    return frame


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_spec()
    source = verified_source()
    frame = selected_rows(include_index=False)
    expected = {(component, month) for component in COMPONENTS for month in ALL_MONTHS}
    present = set(zip(frame["component"], frame["month"]))
    if len(frame) != MIN_INDEX_CELLS or present != expected:
        raise ValueError("incomplete fixed 13-month component keys")
    gate = {
        "country_iso3": COUNTRY,
        "baseline_month": BASELINE,
        "endpoint_months": list(MONTHS),
        "required_components": list(COMPONENTS),
        "selected_index_keys": len(present),
        "required_index_keys": MIN_INDEX_CELLS,
        "candidate_values_accessed": False,
        "positive_finite_index_values": "not_checked_until_committed_run",
        "passed": True,
    }
    return gate, source


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require all registration files in one unchanged first-addition commit."""
    records: list[dict[str, str]] = []
    for rel in REGISTRATION_FILES:
        current = (ROOT / rel).read_bytes()
        head = _git("show", f"HEAD:{rel}")
        if head.returncode or head.stdout != current:
            raise RuntimeError(f"commit exact registration bytes before value access: {rel}")
        records.append({"path": rel, "sha256": hashlib.sha256(current).hexdigest()})
    history = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = history.stdout.decode("ascii", errors="replace").strip().splitlines()
    if history.returncode or not commits:
        raise RuntimeError("new Argentina spec has no first-addition commit")
    first = commits[0]
    tree = _git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if tree.returncode or tree.stdout.strip():
        raise RuntimeError("run artifact existed in the registration commit")
    for rel in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{rel}")
        if frozen.returncode or frozen.stdout != (ROOT / rel).read_bytes():
            raise RuntimeError(f"registration changed after first-addition commit: {rel}")
    return first, records


def selected_values() -> dict[str, dict[str, float]]:
    """Call only after registration_files and preflight succeed."""
    frame = selected_rows(include_index=True)
    if len(frame) != MIN_INDEX_CELLS:
        raise ValueError("incomplete selected index values")
    values: dict[str, dict[str, float]] = {component: {} for component in COMPONENTS}
    for component, month, raw in frame[["component", "month", "index"]].itertuples(index=False, name=None):
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError("non-numeric selected index") from None
        if not math.isfinite(value) or value <= 0:
            raise ValueError("nonfinite or nonpositive selected index")
        values[str(component)][str(month)] = value
    if any(len(values[c]) != len(ALL_MONTHS) for c in COMPONENTS):
        raise ValueError("selected index coverage changed after preflight")
    return values


def classify(core_median: Decimal, core_count: int) -> tuple[str, str]:
    if core_median > DECIMAL_THRESHOLD:
        return "REFUTED", "the registered twelve-month core median exceeds 3.0 percent"
    if core_count >= MIN_CORE_MONTHS:
        return "SUPPORTED", "the core median and at least nine monthly rates meet the registered ceiling"
    return "PARTIAL", "the core median meets the ceiling but fewer than nine months do"


def evaluate() -> tuple[str, str, dict[str, Any]]:
    values = selected_values()
    paths: dict[str, list[dict[str, Any]]] = {}
    medians: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for component in COMPONENTS:
        monthly: list[dict[str, Any]] = []
        exact_rates: list[Decimal] = []
        previous = BASELINE
        for month in MONTHS:
            rate = Decimal(100) * (
                Decimal(str(values[component][month]))
                / Decimal(str(values[component][previous])) - Decimal(1)
            )
            monthly.append({"month": month, "mom_pct": float(rate),
                            "mom_pct_decimal": str(rate)})
            exact_rates.append(rate)
            previous = month
        paths[component] = monthly
        medians[component] = statistics.median(exact_rates)
        counts[component] = sum(rate <= DECIMAL_THRESHOLD for rate in exact_rates)
    label, reason = classify(medians["core"], counts["core"])
    estimate = {
        "method": "direct INDEC index changes; twelve-month descriptive median and threshold count",
        "n_countries": 1, "n_endpoint_months": len(MONTHS),
        "core_median_mom_pct": float(medians["core"]),
        "core_median_mom_pct_decimal": str(medians["core"]),
        "core_months_at_or_below_3_pct": counts["core"],
        "secondary_medians_mom_pct": {c: float(medians[c]) for c in ("headline", "services")},
        "secondary_medians_mom_pct_decimal": {c: str(medians[c]) for c in ("headline", "services")},
        "secondary_months_at_or_below_3_pct": {c: counts[c] for c in ("headline", "services")},
        "monthly_paths": paths,
    }
    return label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only exact replay of the Argentina core-CPI packet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


def artifact_records(
    stamp: str, prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], source: dict[str, Any], label: str, reason: str,
    estimate: dict[str, Any] | None,
) -> dict[str, Any]:
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "descriptive",
        "preflight": gate, "estimate": estimate,
        "old_hypothesis_id": OLD_ID,
        "old_result_seen": "INCONCLUSIVE_DATA_PENDING",
        "school_score_eligible": False, "school_score_credit": 0,
        "limitations": LIMITATIONS,
        "data_status": {
            "variables_missing": [] if estimate is not None else ["required_component_index_values"],
            "input_status": "verified" if estimate is not None else "unverified",
            "input_vintages": [SOURCE_REL],
        },
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": label,
        "registration_files": registration, "vintages": [source],
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "monetary"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL,
                            "registration_files": registration, "gate": EXPECTED_THRESHOLD},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": [source], "endpoint_months": list(MONTHS)},
        "results": estimate, "limitations": LIMITATIONS,
        "school_score_eligible": False, "school_score_credit": 0,
    }
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Old study: `{OLD_ID}` (INCONCLUSIVE_DATA_PENDING; no fitted result).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        "Sample: Argentina national core CPI, September 2025–August 2026.\n"
        "Method: direct index month-on-month changes; median and count against 3.0%.\n"
    )
    if estimate is not None:
        card += (
            f"\nCore median: {estimate['core_median_mom_pct']:.8g}%.\n"
            f"Core months at or below 3.0%: {estimate['core_months_at_or_below_3_pct']}/12.\n"
            f"Headline median (secondary): {estimate['secondary_medians_mom_pct']['headline']:.8g}%.\n"
            f"Services median (secondary): {estimate['secondary_medians_mom_pct']['services']:.8g}%.\n"
        )
    card += "\nThis descriptive packet supplies no policy causation, school-score credit, or old-claim repair.\n"
    chart = {
        "hypothesis_id": HID, "verdict": label, "registered_ceiling_pct": CORE_THRESHOLD,
        "registered_minimum_core_months": MIN_CORE_MONTHS,
        "monthly_paths": estimate["monthly_paths"] if estimate else None,
    }
    rows = [] if estimate is None else [
        {"term": "core_median_mom_pct", "coefficient": estimate["core_median_mom_pct"],
         "std_error": None, "p_value": None, "n_obs": len(MONTHS), "n_countries": 1},
        {"term": "core_months_at_or_below_3_pct", "coefficient": estimate["core_months_at_or_below_3_pct"],
         "std_error": None, "p_value": None, "n_obs": len(MONTHS), "n_countries": 1},
    ]
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "chart": chart, "rows": rows}


COEFFICIENT_COLUMNS = ("term", "coefficient", "std_error", "p_value", "n_obs", "n_countries")


def calculate() -> tuple[dict[str, Any], dict[str, Any], str, str, dict[str, Any] | None]:
    gate, source = preflight()
    try:
        label, reason, estimate = evaluate()
    except (ValueError, KeyError, OverflowError, ZeroDivisionError) as error:
        label, reason, estimate = "INCONCLUSIVE", f"registered measurement invalid: {error}", None
    return gate, source, label, reason, estimate


def run_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before candidate values
    if RUN_DIR.exists():
        raise FileExistsError(f"run already exists: {RUN_REL}; use --check")
    gate, source, label, reason, estimate = calculate()
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    records = artifact_records(stamp, prereg_commit, registration, gate, source, label, reason, estimate)
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(records["manifest"], sort_keys=False), encoding="utf-8")
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(records["diagnostics"], indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(records["packet"], sort_keys=False), encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(records["card"], encoding="utf-8")
    (RUN_DIR / "replication.py").write_text(replication_wrapper(), encoding="utf-8")
    (RUN_DIR / "chart_data.json").write_text(json.dumps(records["chart"], indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(records["rows"], columns=list(COEFFICIENT_COLUMNS)).to_parquet(
        RUN_DIR / "coefficients.parquet", index=False,
    )
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "wrote_files": True, "estimate": estimate}


def check_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before candidate values
    stored = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    stamp = stored.get("run_utc")
    gate, source, label, reason, estimate = calculate()
    expected = artifact_records(stamp, prereg_commit, registration, gate, source, label, reason, estimate)
    actual_manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text(encoding="utf-8"))
    actual_packet = yaml.safe_load((RUN_DIR / "evidence_packet.yaml").read_text(encoding="utf-8"))
    actual_chart = json.loads((RUN_DIR / "chart_data.json").read_text(encoding="utf-8"))
    coefficients = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    expected_coefficients = pd.DataFrame(expected["rows"], columns=list(COEFFICIENT_COLUMNS))
    if any((
        stored != expected["diagnostics"],
        actual_manifest != expected["manifest"],
        actual_packet != expected["packet"],
        actual_chart != expected["chart"],
        (RUN_DIR / "result_card.md").read_text(encoding="utf-8") != expected["card"],
        (RUN_DIR / "replication.py").read_text(encoding="utf-8") != replication_wrapper(),
        (RUN_DIR / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes(),
        not coefficients.equals(expected_coefficients.astype(coefficients.dtypes.to_dict())),
    )):
        raise AssertionError("saved Argentina core-CPI packet does not match exact replay")
    return {"hypothesis_id": HID, "verified": True, "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="source hashes and dimension keys only")
    mode.add_argument("--run", action="store_true", help="guarded first run after Git preregistration")
    mode.add_argument("--check", action="store_true", help="read-only exact replay")
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
