#!/usr/bin/env python3
"""Transparent fraction-to-percentage-point SIPRI input adapter.

The frozen spec defined percentage points, but the pinned source Parquet stores
fractions. The first locked execution stopped at the material-exposure gate and
estimated no coefficient. This adapter is separately committed after that
no-fit audit and before any directional result. It changes only the physical
scale of SIPRI inputs; the source, roster, exclusions, model and thresholds stay
exactly as registered. The result is disclosed as post-gate unit repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_sipri_undp_military_burden_2026 as base

WRAPPER = "scripts/run_sipri_undp_military_burden_2026_unit_fix.py"
AUDIT = "engine/audits/sipri_undp_military_burden_unscaled_diagnostic_2026-10-10.json"
NOTE = "engine/audits/sipri_undp_military_burden_source_unit_erratum_2026-10-10.md"
AUDIT_SHA256 = "0971f533a528879fb65ddcd392ca102aa23f83df9f6d9c3516b76e6bda85c3cd"
UNIT_CORRECTION = {
    "type": "source_unit_conversion_after_unscaled_gate_attempt",
    "source_role": "military_burden",
    "source_stored_unit": "fraction of GDP",
    "registered_unit": "percentage points of GDP",
    "exact_multiplier": 100,
    "scope": "SIPRI input values only; no source, roster, sample rule, outcome, estimator, family size, significance rule or registered threshold changed",
    "first_attempt": "All four locked unscaled cells stopped at the material-exposure gate with no coefficient or directional fit.",
    "first_attempt_audit": AUDIT,
    "first_attempt_audit_sha256": AUDIT_SHA256,
}
ORIGINAL_VALUES = base.values
ORIGINAL_ARTIFACTS = base.artifacts
ORIGINAL_SUMMARY = base.summary_text


def corrected_values(source_root: Path) -> tuple[dict, dict]:
    military, outcomes = ORIGINAL_VALUES(source_root)
    return {key: value * 100.0 if value is not None else None
            for key, value in military.items()}, outcomes


def corrected_artifacts(*args, **kwargs) -> dict[str, bytes]:
    files = ORIGINAL_ARTIFACTS(*args, **kwargs)
    diagnostic = json.loads(files["diagnostics.json"])
    diagnostic["runner"] = WRAPPER
    diagnostic["unit_correction"] = UNIT_CORRECTION
    files["diagnostics.json"] = (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    manifest = yaml.safe_load(files["manifest.yaml"])
    manifest["runner"] = WRAPPER
    manifest["unit_correction"] = UNIT_CORRECTION
    files["manifest.yaml"] = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()
    packet = yaml.safe_load(files["evidence_packet.yaml"])
    packet["reproduction"]["runner"] = WRAPPER
    packet["reproduction"]["command"] = f"python3 {WRAPPER} --source-root <matching local cache> --verify"
    packet["unit_correction"] = UNIT_CORRECTION
    files["evidence_packet.yaml"] = yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode()
    statement = ("\n**Source-unit repair:** The pinned SIPRI Share-of-GDP Parquet stores fractions. "
                 "After a locked unscaled no-fit attempt, this separately committed adapter multiplies "
                 "SIPRI inputs by exactly 100 to match the registered percentage-point unit. "
                 "The failed attempt and its diagnostic hash are preserved; no coefficient was seen "
                 "before this correction. The thresholds, sample rules and model stayed fixed. "
                 "This is a disclosed post-gate physical-unit correction, not a pristine blind run.\n")
    files["result_card.md"] += statement.encode()
    files["replication.py"] = (
        "#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\n"
        "source_root = os.environ.get('IESET_RAW_ROOT')\n"
        "if not source_root:\n    raise SystemExit('set IESET_RAW_ROOT to the matching local raw cache')\n"
        f"raise SystemExit(subprocess.call([sys.executable, '{WRAPPER}', '--source-root', source_root, '--verify']))\n"
    ).encode()
    return files


def corrected_summary(*args, **kwargs) -> str:
    return ORIGINAL_SUMMARY(*args, **kwargs) + (
        "\nSource-unit repair: The pinned SIPRI Share-of-GDP Parquet stores fractions, while "
        "the frozen test expresses military-share changes in percentage points. The first locked "
        "unscaled execution stopped at the material-exposure gate in all four cells; no coefficient "
        "was estimated. A separate pre-coefficient adapter multiplies SIPRI inputs by exactly 100. "
        "The original no-fit diagnostic is preserved, and no registered threshold, roster or model "
        "changed. This is a disclosed post-gate physical-unit correction.\n"
    )


def correction_commit(source_root: Path) -> str:
    registration, roster_hash, _ = base.registration_commit()
    locked = base.lock_commit(source_root, registration, roster_hash)
    additions = {base.first_addition(path) for path in (WRAPPER, AUDIT, NOTE)}
    if len(additions) != 1:
        raise RuntimeError("unit adapter and unscaled audit must be added together")
    commit = additions.pop()
    if commit in (registration, locked) or subprocess.run(
            ["git", "merge-base", "--is-ancestor", locked, commit], cwd=ROOT).returncode:
        raise RuntimeError("unit-adapter commit must follow source lock")
    for path in (WRAPPER, AUDIT, NOTE):
        base.frozen(path, commit)
    if base.sha256(ROOT / AUDIT) != AUDIT_SHA256:
        raise RuntimeError("unscaled audit hash changed")
    audit = json.loads((ROOT / AUDIT).read_text())
    if (audit.get("family_id") != base.FAMILY or audit.get("no_coefficient_estimated") is not True
            or len(audit.get("cells", [])) != 4):
        raise RuntimeError("unscaled audit is incomplete")
    for record in audit["cells"]:
        diagnostic = record["diagnostic"]
        if (diagnostic.get("verdict") != "INCONCLUSIVE"
                or diagnostic.get("primary") != {"gates_failed": ["material_exposure_floor"]}
                or diagnostic.get("preregistration_commit") != registration
                or diagnostic.get("source_lock_commit") != locked):
            raise RuntimeError("unscaled audit contains a fitted or mismatched result")
    for case in base.CASES.values():
        if base.git("ls-tree", "-r", "--name-only", commit, "--", base.paths(case)[2]).strip():
            raise RuntimeError("unit-adapter commit already contains a measured result")
    return commit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    correction_commit(args.source_root)
    base.values = corrected_values
    base.artifacts = corrected_artifacts
    base.summary_text = corrected_summary
    base.run(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
