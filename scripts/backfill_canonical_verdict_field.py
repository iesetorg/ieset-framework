#!/usr/bin/env python3
"""Copy an existing run verdict_label into an absent canonical verdict field.

Only explicitly named, verified runs whose sole current evidence-tier blocker
is verdict_missing are eligible. The result card must independently state the
same verdict, and the local replication runner must exist. The edit inserts a
single JSON field without reserializing diagnostics or changing result data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import audit_evidence_tiers
import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_LABELS = {"SUPPORTED", "REFUTED", "PARTIAL", "SUPPORTED_SUBSET"}
LABEL_LINE = re.compile(
    r'(?m)^(?P<indent>[ \t]*)"verdict_label":[ \t]*"(?P<label>[A-Z_]+)",[ \t]*$'
)
CARD_VERDICT = re.compile(r"(?m)^\*\*Verdict:\*\*\s*([A-Z_]+)\b")


def strict_json(text: str) -> dict:
    value = json.loads(
        text,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-standard JSON constant: {token}")
        ),
    )
    if not isinstance(value, dict):
        raise ValueError("diagnostics root must be an object")
    return value


def validate_runner(hypothesis_id: str, runner: object, label: str) -> None:
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    if not (run_dir / "replication.py").is_file():
        raise ValueError(f"{hypothesis_id}: replication wrapper is missing")
    if not isinstance(runner, str):
        raise ValueError(f"{hypothesis_id}: local replication runner is missing")
    if runner.startswith("scripts/") and (ROOT / runner).is_file():
        return
    if runner != f"engine/runs/{hypothesis_id}/replication.py":
        raise ValueError(f"{hypothesis_id}: local replication runner is missing")

    manifest_path = run_dir / "manifest.yaml"
    if not manifest_path.is_file():
        raise ValueError(f"{hypothesis_id}: pinned run manifest is missing")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if manifest.get("hypothesis_id") != hypothesis_id or manifest.get("verdict_label") != label:
        raise ValueError(f"{hypothesis_id}: pinned run manifest disagrees with diagnostics")
    vintages = manifest.get("vintages") or {}
    if not isinstance(vintages, dict) or not vintages:
        raise ValueError(f"{hypothesis_id}: pinned run manifest has no vintages")
    vintage_root = (ROOT / "data" / "vintages").resolve()
    for item in vintages.values():
        if not isinstance(item, dict) or not item.get("vintage_file") or not item.get("sha256"):
            raise ValueError(f"{hypothesis_id}: incomplete pinned vintage record")
        path = (ROOT / str(item["vintage_file"])).resolve()
        try:
            path.relative_to(vintage_root)
        except ValueError as exc:
            raise ValueError(f"{hypothesis_id}: vintage path is outside data/vintages") from exc
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"{hypothesis_id}: pinned vintage hash does not match")


def prepare(hypothesis_id: str, registrations: dict) -> tuple[Path, str, str]:
    if not re.fullmatch(r"[a-z0-9_]+", hypothesis_id):
        raise ValueError(f"{hypothesis_id}: invalid hypothesis ID")
    paths = list((ROOT / "hypotheses").glob(f"*/{hypothesis_id}.yaml"))
    if len(paths) != 1:
        raise ValueError(f"{hypothesis_id}: expected exactly one formal spec")
    record = audit_evidence_tiers.build_record(paths[0], registrations)
    if record["registration_status"] != "verified" or record["exclusion_reasons"] != ["verdict_missing"]:
        raise ValueError(f"{hypothesis_id}: not a verified verdict-only repair: {record['exclusion_reasons']}")

    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics_path = run_dir / "diagnostics.json"
    original = diagnostics_path.read_text(encoding="utf-8")
    diagnostics = strict_json(original)
    if "verdict" in diagnostics:
        raise ValueError(f"{hypothesis_id}: canonical verdict key already exists")
    label = diagnostics.get("verdict_label")
    if label not in ALLOWED_LABELS:
        raise ValueError(f"{hypothesis_id}: no eligible explicit verdict_label")
    card = (run_dir / "result_card.md").read_text(encoding="utf-8")
    card_match = CARD_VERDICT.search(card)
    if card_match is None or card_match.group(1) != label:
        raise ValueError(f"{hypothesis_id}: result-card verdict disagrees with diagnostics")
    validate_runner(hypothesis_id, diagnostics.get("runner"), label)

    matches = list(LABEL_LINE.finditer(original))
    if len(matches) != 1 or matches[0].group("label") != label:
        raise ValueError(f"{hypothesis_id}: verdict_label JSON line is not uniquely editable")
    match = matches[0]
    insertion = f'{match.group("indent")}"verdict": "{label}",\n'
    updated = original[:match.start()] + insertion + original[match.start():]
    if strict_json(updated).get("verdict") != label:
        raise ValueError(f"{hypothesis_id}: edited diagnostics did not validate")
    return diagnostics_path, updated, label


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("hypothesis_ids", nargs="+", help="Explicit run IDs to repair")
    parser.add_argument("--apply", action="store_true", help="Write the preflighted field additions")
    args = parser.parse_args()
    if len(args.hypothesis_ids) != len(set(args.hypothesis_ids)):
        parser.error("duplicate hypothesis ID")

    registrations = audit_evidence_tiers.registration_rows()
    prepared = [prepare(hid, registrations) for hid in args.hypothesis_ids]
    for (path, updated, label), hid in zip(prepared, args.hypothesis_ids):
        if args.apply:
            path.write_text(updated, encoding="utf-8")
        print(f"{'applied' if args.apply else 'ready'} {hid}: verdict={label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
