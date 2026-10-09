#!/usr/bin/env python3
"""Guarded national BLS payroll follow-up with key-only preflight and field replay.

--preflight verifies source bytes and selected month keys without projecting
employment values. --run and --check require an unchanged first-addition Git
registration of the spec, runner, manifest, and both small source parquets.
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

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
HID = "us_food_service_manufacturing_payroll_growth_2025_2026_v2"
OLD_ID = "post_covid_labour_reallocation_us_2020_2024"
SPEC_REL = f"hypotheses/labour/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
SOURCE_MANIFEST = "data/manifests/fetch_run_2026-10-09T122001Z.yaml"
SOURCE_MANIFEST_SHA256 = "39fa95739201945c380129e318ad6f24afc55ed694fccd92641fe6eb7093e01b"
OLD_DIAGNOSTICS = f"engine/runs/{OLD_ID}/diagnostics.json"
OLD_MANIFEST = f"engine/runs/{OLD_ID}/manifest.yaml"
OLD_DIAGNOSTICS_SHA256 = "a089a474e12f8227d5efca77f0bb87c1dc8251164f9b95608f281a2b8f90a1c8"
OLD_MANIFEST_SHA256 = "1e6d352d608973a10d7ece9845b627403334c9e9a80e707a3886e6c6761bc40d"
SOURCES = {
    "food_services": {
        "series_id": "CES7072200001",
        "path": "data/vintages/bls/CES7072200001@2026-10-09T121959Z.parquet",
        "sha256": "4f6b230f9bc04186f8f14fa9ac29d6c5bd3478eeb512eef7451dc21c2be5438c",
        "description": "US food services and drinking places, all employees, seasonally adjusted",
    },
    "manufacturing": {
        "series_id": "CES3000000001",
        "path": "data/vintages/bls/CES3000000001@2026-10-09T121958Z.parquet",
        "sha256": "5d131d12d7616d7f538b9e7cc334988cda1efac303ea5606d3d8b2581d23052b",
        "description": "US manufacturing, all employees, seasonally adjusted",
    },
}
MONTHS = tuple(
    [(2025, f"M{month:02d}") for month in range(8, 13)]
    + [(2026, f"M{month:02d}") for month in range(1, 9)]
)
FIRST = (2025, "M08")
LAST = (2026, "M08")
REQUIRED_MONTHS = len(MONTHS)
REQUIRED_CELLS = len(SOURCES) * REQUIRED_MONTHS
REGISTRATION_FILES = (
    SPEC_REL, STEELMAN_REL, RUNNER_REL, SOURCE_MANIFEST,
    SOURCES["food_services"]["path"], SOURCES["manufacturing"]["path"],
)
EXPECTED_THRESHOLD = {
    "old_hypothesis_id": OLD_ID,
    "old_result_seen": "INCONCLUSIVE_PENDING_DATA",
    "first_month": "2025-08",
    "last_month": "2026-08",
    "required_months_per_series": REQUIRED_MONTHS,
    "required_selected_cells": REQUIRED_CELLS,
    "food_services_series_id": SOURCES["food_services"]["series_id"],
    "manufacturing_series_id": SOURCES["manufacturing"]["series_id"],
    "support_growth_gap_pp_min_inclusive": 1.0,
    "refute_growth_gap_pp_max_inclusive": -1.0,
    "source_manifest": {"path": SOURCE_MANIFEST, "sha256": SOURCE_MANIFEST_SHA256},
    "source_parquets": {
        role: {"path": row["path"], "sha256": row["sha256"]}
        for role, row in SOURCES.items()
    },
}
LIMITATIONS = [
    "The old five-metric post-COVID case remains INCONCLUSIVE_PENDING_DATA.",
    "Food services is a subset of leisure/hospitality; manufacturing is a new comparator.",
    "The two BLS series do not test old wages, retail, information, quits, or remote-work metrics.",
    "A national payroll-growth gap cannot identify a COVID, labor-policy, trade, or other causal effect.",
    "The October 2026 BLS payroll vintage predates registration and may be revised.",
    "This descriptive follow-up has no school-score credit or automatic policy evidence link.",
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
        spec.get("sample", {}).get("period") != [2025, 2026],
        spec.get("sample", {}).get("temporal_structure") != "time_series",
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("falsification", {}).get("threshold") != EXPECTED_THRESHOLD,
        spec.get("covers_claims") != [],
        spec.get("linked_hypotheses") != [],
    )):
        raise ValueError("BLS registration differs from the frozen runner contract")
    if [item.get("source") for item in spec["variables"]["outcome"]] != [
        "bls:CES7072200001", "bls:CES3000000001",
    ]:
        raise ValueError("BLS outcome sources changed")
    return spec


def old_run_boundary() -> dict[str, Any]:
    """Verify the old five-metric status without using its result magnitudes."""
    if sha256(ROOT / OLD_DIAGNOSTICS) != OLD_DIAGNOSTICS_SHA256:
        raise ValueError("old labor diagnostics changed")
    if sha256(ROOT / OLD_MANIFEST) != OLD_MANIFEST_SHA256:
        raise ValueError("old labor manifest changed")
    old = json.loads((ROOT / OLD_DIAGNOSTICS).read_text(encoding="utf-8"))
    manifest = yaml.safe_load((ROOT / OLD_MANIFEST).read_text(encoding="utf-8"))
    if old.get("hypothesis_id") != OLD_ID or old.get("verdict") != "INCONCLUSIVE_PENDING_DATA":
        raise ValueError("old five-metric labor outcome changed")
    if manifest.get("evidence_type") != "canonical_case_multi_metric":
        raise ValueError("old labor evidence type changed")
    return {
        "old_hypothesis_id": OLD_ID,
        "old_verdict": "INCONCLUSIVE_PENDING_DATA",
        "old_diagnostics_sha256": OLD_DIAGNOSTICS_SHA256,
        "old_manifest_sha256": OLD_MANIFEST_SHA256,
        "old_window_end": 2024,
        "new_window_start": "2025-08",
        "calendar_disjoint": True,
        "old_five_metrics_resolved_by_new_test": False,
    }


def verified_sources() -> list[dict[str, Any]]:
    if sha256(ROOT / SOURCE_MANIFEST) != SOURCE_MANIFEST_SHA256:
        raise ValueError("BLS fetch manifest hash changed")
    manifest = yaml.safe_load((ROOT / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    entries = manifest.get("entries") or []
    if len(entries) != 4:
        raise ValueError("BLS fetch manifest entry set changed")
    records: list[dict[str, Any]] = []
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise ValueError(f"pinned BLS parquet changed: {role}")
        matches = [row for row in entries if row.get("parquet_path") == source["path"]]
        expected_url = f"https://api.bls.gov/publicAPI/v2/timeseries/data/{source['series_id']}"
        if len(matches) != 1 or any((
            matches[0].get("publisher") != "bls",
            matches[0].get("series_id") != source["series_id"],
            matches[0].get("source_url") != expected_url,
            matches[0].get("sha256") != source["sha256"],
            matches[0].get("frequency") != "monthly",
            matches[0].get("end_date") != "2026",
        )):
            raise ValueError(f"BLS source provenance changed: {role}")
        records.append({
            "role": role, "publisher": "bls", "series_id": source["series_id"],
            "description": source["description"], "source_url": expected_url,
            "manifest": SOURCE_MANIFEST, "manifest_sha256": SOURCE_MANIFEST_SHA256,
            "path": source["path"], "sha256": source["sha256"],
            "adjustment": "seasonally adjusted", "units": "thousands of employees",
            "revision_status": "fixed_local_vintage; subsequent BLS revisions not followed",
        })
    return records


def selected_rows(role: str, *, include_value: bool) -> pd.DataFrame:
    """Preflight reads only year and period keys from the pinned parquet."""
    columns = ["year", "period"] + (["value"] if include_value else [])
    frame = pd.read_parquet(ROOT / SOURCES[role]["path"], columns=columns)
    frame = frame[frame["period"].isin({month for _, month in MONTHS})].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    selected = pd.Series(
        [(year, period) in MONTHS for year, period in frame[["year", "period"]].itertuples(index=False, name=None)],
        index=frame.index,
    )
    frame = frame[selected]
    if frame.duplicated(["year", "period"]).any():
        raise ValueError(f"duplicate selected {role} month")
    return frame.sort_values(["year", "period"]).reset_index(drop=True)


def preflight() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_spec()
    old = old_run_boundary()
    sources = verified_sources()
    expected = set(MONTHS)
    counts: dict[str, int] = {}
    for role in SOURCES:
        rows = selected_rows(role, include_value=False)
        observed = set(rows.itertuples(index=False, name=None))
        if observed != expected or len(rows) != REQUIRED_MONTHS:
            raise ValueError(f"fixed {role} 13-month coverage is incomplete or ambiguous")
        counts[role] = len(observed)
    gate = {
        "window": ["2025-08", "2026-08"],
        "selected_month_keys": counts,
        "selected_cells": sum(counts.values()),
        "old_run_boundary": old,
        "passed": True,
        "heldout_values_accessed": False,
    }
    return gate, sources


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require unchanged first-addition bytes, including the two tiny source files."""
    records: list[dict[str, str]] = []
    for rel in REGISTRATION_FILES:
        current = (ROOT / rel).read_bytes()
        head = _git("show", f"HEAD:{rel}")
        if head.returncode or head.stdout != current:
            raise RuntimeError(f"commit exact registration bytes before value access: {rel}")
        records.append({"path": rel, "sha256": hashlib.sha256(current).hexdigest()})
    history = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = history.stdout.decode("ascii", errors="replace").strip().splitlines()
    if history.returncode or len(commits) != 1:
        raise RuntimeError("BLS spec requires one identifiable first-addition commit")
    first = commits[0]
    first_run_tree = _git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if first_run_tree.returncode or first_run_tree.stdout.strip():
        raise RuntimeError("run artifact existed in the registration commit")
    for rel in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{rel}")
        if frozen.returncode or frozen.stdout != (ROOT / rel).read_bytes():
            raise RuntimeError(f"registration file changed after first addition: {rel}")
    return first, records


def selected_values(role: str) -> dict[tuple[int, str], float]:
    rows = selected_rows(role, include_value=True)
    if len(rows) != REQUIRED_MONTHS:
        raise ValueError(f"incomplete selected {role} employment values")
    values: dict[tuple[int, str], float] = {}
    for year, period, raw in rows.itertuples(index=False, name=None):
        try:
            number = float(str(raw).replace(",", ""))
        except (TypeError, ValueError):
            raise ValueError(f"nonnumeric selected {role} employment value") from None
        if not math.isfinite(number) or number <= 0:
            raise ValueError(f"nonfinite or nonpositive selected {role} employment value")
        values[(int(year), str(period))] = number
    if len(values) != REQUIRED_MONTHS:
        raise ValueError(f"ambiguous selected {role} employment values")
    return values


def classify(growth_gap_pp: float) -> tuple[str, str]:
    if growth_gap_pp >= 1.0:
        return "SUPPORTED", "food-services payroll growth exceeded manufacturing by at least 1.0 pp"
    if growth_gap_pp <= -1.0:
        return "REFUTED", "manufacturing payroll growth exceeded food services by at least 1.0 pp"
    return "PARTIAL", "the fixed payroll-growth gap was inside the +/-1.0 pp band"


def evaluate() -> tuple[str, str, dict[str, Any]]:
    """Read selected employment values only after registration and preflight."""
    food = selected_values("food_services")
    manufacturing = selected_values("manufacturing")
    food_growth = 100.0 * (food[LAST] / food[FIRST] - 1.0)
    manufacturing_growth = 100.0 * (manufacturing[LAST] / manufacturing[FIRST] - 1.0)
    gap = food_growth - manufacturing_growth
    label, reason = classify(gap)
    monthly_index = [{
        "month": f"{year}-{period[1:]}",
        "food_services_index_aug2025_100": 100.0 * food[(year, period)] / food[FIRST],
        "manufacturing_index_aug2025_100": 100.0 * manufacturing[(year, period)] / manufacturing[FIRST],
    } for year, period in MONTHS]
    estimate = {
        "method": "national August-to-August percent-growth gap; descriptive",
        "n_selected_cells": REQUIRED_CELLS,
        "food_services_growth_pct": food_growth,
        "manufacturing_growth_pct": manufacturing_growth,
        "food_minus_manufacturing_growth_gap_pp": gap,
        "monthly_index": monthly_index,
    }
    return label, reason, estimate


def calculate() -> tuple[dict[str, Any], list[dict[str, Any]], str, str, dict[str, Any] | None]:
    gate, sources = preflight()
    try:
        label, reason, estimate = evaluate()
    except (KeyError, ValueError, OverflowError, ZeroDivisionError) as error:
        label, reason, estimate = "INCONCLUSIVE", f"selected BLS employment invalid: {error}", None
    return gate, sources, label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only field replay of the national BLS payroll packet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


COEFFICIENT_COLUMNS = ["term", "coefficient", "std_error", "p_value", "n_obs", "n_series", "method"]


def artifact_records(
    stamp: str, prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], sources: list[dict[str, Any]], label: str,
    reason: str, estimate: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any], list[dict[str, Any]]]:
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "descriptive",
        "preflight": gate, "estimate": estimate,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "INCONCLUSIVE_PENDING_DATA",
        "correction": {"disposition": "new_descriptive_followup_only", "school_score_credit": 0},
        "limitations": LIMITATIONS,
        "data_status": {
            "variables_missing": [] if estimate is not None else ["selected_payroll_invalid"],
            "input_status": "verified" if estimate is not None else "unverified",
            "input_vintages": [row["path"] for row in sources],
        },
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": label,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "INCONCLUSIVE_PENDING_DATA",
        "registration_files": registration, "vintages": sources,
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "labour"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL,
                            "registration_files": registration, "gate": EXPECTED_THRESHOLD},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": sources, "window": ["2025-08", "2026-08"],
                 "old_run_boundary": gate["old_run_boundary"]},
        "results": estimate, "limitations": LIMITATIONS,
        "credit_ceiling": "descriptive follow-up only; zero old-case and school-score credit",
    }
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Old five-metric study: `{OLD_ID}` (INCONCLUSIVE_PENDING_DATA; unchanged).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        "Sample: US national BLS CES, August 2025 to August 2026, two seasonally adjusted industries.\n"
        "Method: food-services minus manufacturing August-to-August payroll percentage growth.\n"
    )
    if estimate is not None:
        card += (
            f"\nFood-services growth: {estimate['food_services_growth_pct']:+.8g}%.\n"
            f"Manufacturing growth: {estimate['manufacturing_growth_pct']:+.8g}%.\n"
            f"Growth gap: {estimate['food_minus_manufacturing_growth_gap_pp']:+.8g} pp.\n"
        )
    card += (
        "\nThis is a narrow descriptive payroll comparison. It cannot establish "
        "post-COVID or policy causation, resolve the old five metrics, or earn school-score credit.\n"
    )
    chart = {
        "hypothesis_id": HID, "verdict": label,
        "window": ["2025-08", "2026-08"],
        "monthly_index": estimate["monthly_index"] if estimate else [],
        "growth_gap_pp": estimate["food_minus_manufacturing_growth_gap_pp"] if estimate else None,
        "support_min_pp": 1.0, "refute_max_pp": -1.0,
    }
    rows = [] if estimate is None else [{
        "term": "food_minus_manufacturing_growth_gap_pp",
        "coefficient": estimate["food_minus_manufacturing_growth_gap_pp"],
        "std_error": None, "p_value": None,
        "n_obs": REQUIRED_CELLS, "n_series": len(SOURCES),
        "method": "descriptive endpoint growth gap; no inferential estimate",
    }]
    return diagnostics, manifest, packet, card, chart, rows


def write_run(
    prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], sources: list[dict[str, Any]],
    label: str, reason: str, estimate: dict[str, Any] | None,
) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        stamp, prereg_commit, registration, gate, sources, label, reason, estimate
    )
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
    prereg_commit, registration = registration_files()  # before value access
    if RUN_DIR.exists():
        raise FileExistsError(f"run already exists: {RUN_REL}; use --check")
    gate, sources, label, reason, estimate = calculate()
    return write_run(prereg_commit, registration, gate, sources, label, reason, estimate)


def check_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before value access
    saved = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    saved_manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text(encoding="utf-8"))
    saved_packet = yaml.safe_load((RUN_DIR / "evidence_packet.yaml").read_text(encoding="utf-8"))
    saved_card = (RUN_DIR / "result_card.md").read_text(encoding="utf-8")
    saved_chart = json.loads((RUN_DIR / "chart_data.json").read_text(encoding="utf-8"))
    saved_wrapper = (RUN_DIR / "replication.py").read_text(encoding="utf-8")
    saved_snapshot = (RUN_DIR / "hypothesis.yaml").read_bytes()
    saved_coefficients = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    gate, sources, label, reason, estimate = calculate()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        saved["run_utc"], prereg_commit, registration, gate, sources, label, reason, estimate
    )
    if any((
        saved != diagnostics,
        saved_manifest != manifest,
        saved_packet != packet,
        saved_card != card,
        saved_chart != chart,
        saved_wrapper != replication_wrapper(),
        saved_snapshot != (ROOT / SPEC_REL).read_bytes(),
    )):
        raise AssertionError("saved BLS packet differs from pinned field replay")
    expected_coefficients = pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS)
    pd.testing.assert_frame_equal(saved_coefficients, expected_coefficients, check_dtype=False)
    return {"hypothesis_id": HID, "verified": True, "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="source hashes and month keys only")
    mode.add_argument("--run", action="store_true", help="guarded first result after registration")
    mode.add_argument("--check", action="store_true", help="read-only field replay of stored result")
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
