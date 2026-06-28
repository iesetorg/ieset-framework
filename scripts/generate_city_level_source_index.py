#!/usr/bin/env python3
"""Generate a city-level source index from the inventory and ingestion queue.

The source inventory is intentionally append-friendly. This index makes it
usable by data agents and policy runners by summarizing:

* how many sources are in the city-level sprint;
* which second-order layers and geographies have coverage;
* which records are still scout-reported or unverified; and
* which ingestion waves are ready for fetcher design.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import validate_city_level_sources as validator


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "engine" / "city_level_source_index.json"
OUT_MD = ROOT / "engine" / "city_level_source_index.md"


def load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    errors = validator.validate()
    if errors:
        raise ValueError("city-level source validation failed:\n" + "\n".join(errors))
    return validator.load_yaml(validator.INVENTORY_PATH), validator.load_yaml(validator.QUEUE_PATH)


def sorted_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def compact_source(rec: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": rec["source_id"],
        "source_name": rec["source_name"],
        "publisher": rec["publisher"],
        "geography": rec["geography"],
        "spatial_grain": rec["spatial_grain"],
        "time_coverage": rec["time_coverage"],
        "access_format": rec["access_format"],
        "source_url": rec["source_url"],
        "license_or_terms": rec["license_or_terms"],
        "verification_status": rec["verification_status"],
        "ingestion_difficulty": rec["ingestion_difficulty"],
        "top_1000_scalability": rec["top_1000_scalability"],
        "immediate_payoff_rank": rec["immediate_payoff_rank"],
        "second_order_layers": rec["second_order_layers"],
        "rent_control_use": rec["rent_control_use"],
    }


def compact_wave(wave: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_ids = wave.get("source_ids") or []
    statuses = Counter(source_by_id[sid]["verification_status"] for sid in source_ids)
    difficulties = Counter(source_by_id[sid]["ingestion_difficulty"] for sid in source_ids)
    return {
        "wave_id": wave["wave_id"],
        "status": wave["status"],
        "objective": wave["objective"],
        "source_count": len(source_ids),
        "source_ids": source_ids,
        "source_family_ids": wave.get("source_family_ids") or [],
        "target_cases": wave.get("target_cases") or [],
        "expected_outputs": wave.get("expected_outputs") or [],
        "verification_status_counts": sorted_counts(statuses),
        "ingestion_difficulty_counts": sorted_counts(difficulties),
    }


def build_index() -> dict[str, Any]:
    inventory, queue = load_inputs()
    records = inventory.get("source_records") or []
    source_by_id = {rec["source_id"]: rec for rec in records}

    by_status: Counter[str] = Counter()
    by_difficulty: Counter[str] = Counter()
    by_scalability: Counter[str] = Counter()
    by_layer: Counter[str] = Counter()
    by_geography: Counter[str] = Counter()
    for rec in records:
        by_status[rec["verification_status"]] += 1
        by_difficulty[rec["ingestion_difficulty"]] += 1
        by_scalability[rec["top_1000_scalability"]] += 1
        by_geography[rec["geography"]] += 1
        by_layer.update(rec["second_order_layers"])

    ranked_sources = sorted(
        records,
        key=lambda rec: (rec["immediate_payoff_rank"], rec["source_id"]),
    )
    waves = [compact_wave(wave, source_by_id) for wave in queue.get("waves") or []]

    return {
        "generated_by": "scripts/generate_city_level_source_index.py",
        "summary": {
            "source_count": len(records),
            "wave_count": len(waves),
            "primary_axis": inventory["primary_axis"],
            "preferred_city_anchor": inventory["canonical_city_universe"]["preferred_anchor"],
            "verification_status_counts": sorted_counts(by_status),
            "ingestion_difficulty_counts": sorted_counts(by_difficulty),
            "top_1000_scalability_counts": sorted_counts(by_scalability),
            "second_order_layer_counts": sorted_counts(by_layer),
            "geography_counts_top20": dict(
                sorted(by_geography.items(), key=lambda item: (-item[1], item[0]))[:20]
            ),
        },
        "canonical_city_universe": inventory["canonical_city_universe"],
        "top_ingestion_candidates": [compact_source(rec) for rec in ranked_sources[:40]],
        "waves": waves,
        "sources": [compact_source(rec) for rec in ranked_sources],
    }


def write_outputs(payload: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = payload["summary"]
    lines = [
        "# City-Level Source Index",
        "",
        "Generated from `data/city_level/source_inventory.yaml` and `data/city_level/ingestion_queue.yaml`.",
        "",
        "## Summary",
        "",
        f"- Sources indexed: {summary['source_count']}",
        f"- Ingestion waves: {summary['wave_count']}",
        f"- Primary axis: `{summary['primary_axis']}`",
        f"- Preferred city anchor: `{summary['preferred_city_anchor']}`",
        f"- Verification statuses: `{json.dumps(summary['verification_status_counts'], sort_keys=True)}`",
        f"- Ingestion difficulty: `{json.dumps(summary['ingestion_difficulty_counts'], sort_keys=True)}`",
        f"- Top-1000 scalability: `{json.dumps(summary['top_1000_scalability_counts'], sort_keys=True)}`",
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
            "| wave | status | sources | target cases |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for wave in payload["waves"]:
        targets = ", ".join(wave["target_cases"][:4]) or "-"
        if len(wave["target_cases"]) > 4:
            targets += ", ..."
        lines.append(
            f"| `{wave['wave_id']}` | {wave['status']} | {wave['source_count']} | {targets} |"
        )

    lines.extend(
        [
            "",
            "## Top Ingestion Candidates",
            "",
            "| rank | source | geography | difficulty | status | why it matters |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for rec in payload["top_ingestion_candidates"][:30]:
        use = rec["rent_control_use"].replace("|", "/")
        lines.append(
            f"| {rec['immediate_payoff_rank']} | `{rec['source_id']}` | "
            f"{rec['geography']} | {rec['ingestion_difficulty']} | "
            f"{rec['verification_status']} | {use} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    payload = build_index()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
