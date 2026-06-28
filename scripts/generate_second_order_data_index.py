#!/usr/bin/env python3
"""Generate an index for the second-order data acquisition program."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import validate_second_order_data_program as validator


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "engine" / "second_order_data_source_index.json"
OUT_MD = ROOT / "engine" / "second_order_data_source_index.md"


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    errors = validator.validate()
    if errors:
        raise ValueError("second-order data program validation failed:\n" + "\n".join(errors))
    return validator.load_yaml(validator.INVENTORY_PATH), validator.load_yaml(validator.QUEUE_PATH)


def sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def compact_source(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": rec["source_id"],
        "source_name": rec["source_name"],
        "source_family_id": rec["source_family_id"],
        "publisher": rec["publisher"],
        "domain": rec["domain"],
        "geography": rec["geography"],
        "unit_of_observation": rec["unit_of_observation"],
        "time_coverage": rec["time_coverage"],
        "access_format": rec["access_format"],
        "source_url": rec["source_url"],
        "license_or_terms": rec["license_or_terms"],
        "acquisition_status": rec["acquisition_status"],
        "verification_status": rec["verification_status"],
        "ingestion_difficulty": rec["ingestion_difficulty"],
        "immediate_payoff_rank": rec["immediate_payoff_rank"],
        "second_order_layers": rec["second_order_layers"],
        "gate_unlocks": rec["gate_unlocks"],
    }


def compact_wave(wave: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_ids = wave.get("source_ids") or []
    statuses = Counter(source_by_id[sid]["acquisition_status"] for sid in source_ids)
    difficulties = Counter(source_by_id[sid]["ingestion_difficulty"] for sid in source_ids)
    return {
        "wave_id": wave["wave_id"],
        "status": wave["status"],
        "owner_lane": wave["owner_lane"],
        "loop_type": wave["loop_type"],
        "cadence": wave["cadence"],
        "objective": wave["objective"],
        "source_count": len(source_ids),
        "source_ids": source_ids,
        "source_family_ids": wave.get("source_family_ids") or [],
        "target_gate_layers": wave.get("target_gate_layers") or [],
        "target_cases": wave.get("target_cases") or [],
        "expected_outputs": wave.get("expected_outputs") or [],
        "acquisition_status_counts": sorted_counts(statuses),
        "ingestion_difficulty_counts": sorted_counts(difficulties),
    }


def build_index() -> dict[str, Any]:
    inventory, queue = load_inputs()
    records = inventory.get("source_records") or []
    source_by_id = {rec["source_id"]: rec for rec in records}

    by_status: Counter[str] = Counter()
    by_verification: Counter[str] = Counter()
    by_difficulty: Counter[str] = Counter()
    by_layer: Counter[str] = Counter()
    by_family: Counter[str] = Counter()
    by_domain: Counter[str] = Counter()
    for rec in records:
        by_status[rec["acquisition_status"]] += 1
        by_verification[rec["verification_status"]] += 1
        by_difficulty[rec["ingestion_difficulty"]] += 1
        by_family[rec["source_family_id"]] += 1
        by_domain[rec["domain"]] += 1
        by_layer.update(rec["second_order_layers"])

    ranked_sources = sorted(records, key=lambda rec: (rec["immediate_payoff_rank"], rec["source_id"]))
    waves = [compact_wave(wave, source_by_id) for wave in queue.get("waves") or []]

    return {
        "generated_by": "scripts/generate_second_order_data_index.py",
        "summary": {
            "source_count": len(records),
            "wave_count": len(waves),
            "backlog_snapshot": inventory["backlog_snapshot"],
            "acquisition_status_counts": sorted_counts(by_status),
            "verification_status_counts": sorted_counts(by_verification),
            "ingestion_difficulty_counts": sorted_counts(by_difficulty),
            "second_order_layer_counts": sorted_counts(by_layer),
            "source_family_counts": sorted_counts(by_family),
            "domain_counts_top20": dict(sorted(by_domain.items(), key=lambda item: (-item[1], item[0]))[:20]),
        },
        "top_ingestion_candidates": [compact_source(rec) for rec in ranked_sources[:40]],
        "waves": waves,
        "sources": [compact_source(rec) for rec in ranked_sources],
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = payload["summary"]
    snapshot = summary["backlog_snapshot"]
    lines = [
        "# Second-order Data Source Index",
        "",
        "Generated from `data/second_order/source_inventory.yaml` and `data/second_order/ingestion_queue.yaml`.",
        "",
        "## Gate Backlog Snapshot",
        "",
        f"- Strict held public claim links: {snapshot['strict_held_public_claim_links']}",
        f"- Strict eligible public claim links: {snapshot['strict_eligible_public_claim_links']}",
        f"- Held hypotheses: {snapshot['held_hypotheses']}",
        f"- Policies missing explicit designs: {snapshot['policies_missing_explicit_design']}",
        f"- Policies needing treated/comparison unit coding: {snapshot['policies_needing_treated_comparison_units']}",
        f"- Policies needing exact event dates: {snapshot['policies_needing_exact_event_dates']}",
        "",
        "## Summary",
        "",
        f"- Sources indexed: {summary['source_count']}",
        f"- Ingestion waves: {summary['wave_count']}",
        f"- Acquisition statuses: `{json.dumps(summary['acquisition_status_counts'], sort_keys=True)}`",
        f"- Verification statuses: `{json.dumps(summary['verification_status_counts'], sort_keys=True)}`",
        f"- Ingestion difficulty: `{json.dumps(summary['ingestion_difficulty_counts'], sort_keys=True)}`",
        "",
        "## Most Covered Layers",
        "",
    ]
    for layer, count in list(summary["second_order_layer_counts"].items())[:15]:
        lines.append(f"- `{layer}` ({count})")

    lines.extend(
        [
            "",
            "## Ingestion Waves",
            "",
            "| wave | status | lane | loop | sources | target layers |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for wave in payload["waves"]:
        layers = ", ".join(wave["target_gate_layers"][:4])
        if len(wave["target_gate_layers"]) > 4:
            layers += ", ..."
        lines.append(
            f"| `{wave['wave_id']}` | {wave['status']} | {wave['owner_lane']} | "
            f"{wave['loop_type']} | {wave['source_count']} | {layers} |"
        )

    lines.extend(
        [
            "",
            "## Top Ingestion Candidates",
            "",
            "| rank | source | family | status | difficulty | primary unlock |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for rec in payload["top_ingestion_candidates"][:30]:
        unlock = rec["gate_unlocks"][0].replace("|", "/")
        lines.append(
            f"| {rec['immediate_payoff_rank']} | `{rec['source_id']}` | "
            f"`{rec['source_family_id']}` | {rec['acquisition_status']} | "
            f"{rec['ingestion_difficulty']} | {unlock} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    payload = build_index()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
