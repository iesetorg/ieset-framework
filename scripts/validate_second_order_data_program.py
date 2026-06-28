#!/usr/bin/env python3
"""Validate the second-order data acquisition inventory and queue.

This is intentionally narrower than validate_specs.py. The files under
data/second_order/ are a research-to-ingestion planning surface, so the checks
focus on source schema, dedupe, source-family cross references, and queue
integrity.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: install dependencies: pip install pyyaml jsonschema", file=sys.stderr)
    sys.exit(2)


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "data" / "second_order" / "source_inventory.yaml"
QUEUE_PATH = ROOT / "data" / "second_order" / "ingestion_queue.yaml"
SECOND_ORDER_SOURCES_PATH = ROOT / "data" / "second_order_sources.yaml"
INVENTORY_SCHEMA = ROOT / "schemas" / "second_order_data_source_inventory.schema.json"
QUEUE_SCHEMA = ROOT / "schemas" / "second_order_data_ingestion_queue.schema.json"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        raise ValueError(f"{path.relative_to(ROOT)} did not parse to a mapping")
    return doc


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def schema_errors(path: Path, schema_path: Path) -> list[str]:
    try:
        doc = load_yaml(path)
    except Exception as exc:
        return [f"{path.relative_to(ROOT)}: YAML parse/load error: {exc}"]
    validator = Draft202012Validator(load_json(schema_path))
    errors: list[str] = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: tuple(str(p) for p in e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"{path.relative_to(ROOT)}: at {loc}: {err.message}")
    return errors


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return sorted(dupes)


def source_records(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return list(inventory.get("source_records") or [])


def second_order_family_ids(path: Path = SECOND_ORDER_SOURCES_PATH) -> set[str]:
    if not path.exists():
        return set()
    doc = load_yaml(path)
    return set((doc.get("source_families") or {}).keys())


def cross_reference_errors(
    inventory: dict[str, Any],
    queue: dict[str, Any],
    family_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    records = source_records(inventory)
    ids = [str(rec.get("source_id")) for rec in records]
    for source_id in duplicate_values(ids):
        errors.append(f"{INVENTORY_PATH.relative_to(ROOT)}: duplicate source_id {source_id!r}")

    ranks = [str(rec.get("immediate_payoff_rank")) for rec in records]
    for rank in duplicate_values(ranks):
        errors.append(f"{INVENTORY_PATH.relative_to(ROOT)}: duplicate immediate_payoff_rank {rank!r}")

    known_sources = set(ids)
    for rec in records:
        family_id = rec.get("source_family_id")
        if family_id not in family_ids:
            errors.append(
                f"{INVENTORY_PATH.relative_to(ROOT)}: source {rec.get('source_id')!r} "
                f"references unknown source_family_id {family_id!r}"
            )

    seen_waves: set[str] = set()
    for wave in queue.get("waves") or []:
        wave_id = wave.get("wave_id")
        if wave_id in seen_waves:
            errors.append(f"{QUEUE_PATH.relative_to(ROOT)}: duplicate wave_id {wave_id!r}")
        seen_waves.add(wave_id)
        for source_id in wave.get("source_ids") or []:
            if source_id not in known_sources:
                errors.append(
                    f"{QUEUE_PATH.relative_to(ROOT)}: wave {wave_id!r} references "
                    f"unknown source_id {source_id!r}"
                )
        for family_id in wave.get("source_family_ids") or []:
            if family_id not in family_ids:
                errors.append(
                    f"{QUEUE_PATH.relative_to(ROOT)}: wave {wave_id!r} references "
                    f"unknown source_family_id {family_id!r}"
                )
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    errors.extend(schema_errors(INVENTORY_PATH, INVENTORY_SCHEMA))
    errors.extend(schema_errors(QUEUE_PATH, QUEUE_SCHEMA))
    if errors:
        return errors
    inventory = load_yaml(INVENTORY_PATH)
    queue = load_yaml(QUEUE_PATH)
    errors.extend(cross_reference_errors(inventory, queue, second_order_family_ids()))
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    inventory = load_yaml(INVENTORY_PATH)
    queue = load_yaml(QUEUE_PATH)
    print(
        json.dumps(
            {
                "status": "ok",
                "source_records": len(inventory.get("source_records") or []),
                "waves": len(queue.get("waves") or []),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
