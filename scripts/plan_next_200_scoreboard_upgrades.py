#!/usr/bin/env python3
"""Plan the next 200 hypothesis upgrades and their highest-leverage data gaps.

The queue is deliberately drawn from hypotheses that already have public
scoreboard claim links but are held by the strict second-order gate. This
prioritizes converting existing corpus value into integrity-score evidence
before adding unrelated hypotheses.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
BACKLOG_PATH = ROOT / "engine" / "second_order_test_backlog.json"
SOURCE_PATH = ROOT / "data" / "second_order_sources.yaml"
SOURCE_INDEX_PATH = ROOT / "engine" / "second_order_data_source_index.json"
OUT_JSON = (
    ROOT
    / "engine"
    / "audits"
    / "next_200_scoreboard_data_gap_roadmap_2026-07-19.json"
)
OUT_MD = (
    ROOT
    / "engine"
    / "audits"
    / "next_200_scoreboard_data_gap_roadmap_2026-07-19.md"
)

QUEUE_SIZE = 200
WAVE_SIZE = 50
READINESS_ORDER = {
    "ready": 5,
    "partial_ready": 4,
    "reconstruct_needed": 3,
    "scrape_needed": 2,
    "proprietary_gap": 1,
    "source_family_gap": 0,
    "unknown": 0,
}
ACQUISITION_ACTION = {
    "ready": "bind existing public series and execute the measurement design",
    "partial_ready": "extend an existing fetcher or join before execution",
    "reconstruct_needed": "reconstruct a versioned public administrative panel",
    "scrape_needed": "complete access/legal review, then build a versioned scraper",
    "proprietary_gap": "secure access or identify a public substitute before preregistration",
    "source_family_gap": "define and register a source family for the uncovered causal layer",
    "unknown": "resolve a source family and publisher before preregistration",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text()) or {}


def choose_source_path(
    row: dict[str, Any],
    families: dict[str, dict[str, Any]],
    leverage: Counter[str],
    inventory: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Choose a compact, readiness-aware family set covering missing layers."""
    missing = set(row.get("missing_layers") or [])
    available = {
        rec["family_id"]: rec
        for rec in row.get("source_families") or []
        if rec.get("family_id") in families
    }
    selected: list[dict[str, Any]] = []
    uncovered = set(missing)

    while uncovered:
        ranked: list[tuple[tuple[int, int, int, str], str, set[str]]] = []
        for family_id, summary in available.items():
            if any(item["family_id"] == family_id for item in selected):
                continue
            record = families[family_id]
            covered = uncovered.intersection(record.get("layers") or [])
            if not covered:
                continue
            readiness = str(summary.get("readiness") or "unknown")
            score = (
                len(covered),
                READINESS_ORDER.get(readiness, 0),
                leverage[family_id],
                family_id,
            )
            ranked.append((score, family_id, covered))
        if not ranked:
            break
        _score, family_id, covered = max(ranked)
        source_summary = available[family_id]
        registered_sources = inventory.get(family_id, [])
        selected.append(
            {
                "family_id": family_id,
                "name": source_summary.get("name"),
                "readiness": source_summary.get("readiness") or "unknown",
                "layers_covered": sorted(covered),
                "existing_fetchers": source_summary.get("existing_fetchers") or [],
                "publisher_refs": source_summary.get("publisher_refs") or [],
                "inventory_status": (
                    "registered_concrete_sources"
                    if registered_sources
                    else "family_only_no_concrete_source"
                ),
                "registered_sources": [
                    {
                        "source_id": source.get("source_id"),
                        "source_name": source.get("source_name"),
                        "source_url": source.get("source_url"),
                        "acquisition_status": source.get("acquisition_status"),
                        "ingestion_difficulty": source.get("ingestion_difficulty"),
                        "immediate_payoff_rank": source.get("immediate_payoff_rank"),
                        "verification_status": source.get("verification_status"),
                    }
                    for source in registered_sources[:5]
                ],
            }
        )
        uncovered.difference_update(covered)

    return selected, sorted(uncovered)


def acquisition_class(path: list[dict[str, Any]], uncovered: list[str]) -> str:
    if uncovered:
        return "source_family_gap"
    readiness = {str(item.get("readiness") or "unknown") for item in path}
    for candidate in (
        "proprietary_gap",
        "scrape_needed",
        "reconstruct_needed",
        "partial_ready",
        "ready",
    ):
        if candidate in readiness:
            return candidate
    return "unknown"


def decorate_rows(
    rows: list[dict[str, Any]],
    families: dict[str, dict[str, Any]],
    leverage: Counter[str],
    inventory: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source_path, uncovered = choose_source_path(
            row, families, leverage, inventory
        )
        source_class = acquisition_class(source_path, uncovered)
        decorated.append(
            {
                "rank": index,
                "wave": ((index - 1) // WAVE_SIZE) + 1,
                "candidate_type": "scoreboard_integrity_upgrade",
                "hypothesis_id": row["hypothesis_id"],
                "topic": row.get("topic"),
                "current_status": row.get("status"),
                "evidence_type": row.get("evidence_type"),
                "priority": row.get("priority"),
                "public_claim_links_at_gate": row.get("public_claim_links_held", 0),
                "failure_credit_holds": row.get("failure_credit_holds", 0),
                "raw_weighted_score_at_gate": row.get("raw_weighted_score_at_hold", 0),
                "missing_layer_source": row.get("missing_layer_source"),
                "missing_layers": row.get("missing_layers") or [],
                "recommended_designs": row.get("recommended_designs") or [],
                "recommended_source_path": source_path,
                "uncovered_layers": uncovered,
                "acquisition_class": source_class,
                "next_actions": [
                    (
                        "formalize and preregister a measured mechanism contract"
                        if row.get("missing_layer_source") == "inferred_missing_contract"
                        else "complete the declared mechanism measurement contract"
                    ),
                    ACQUISITION_ACTION[source_class],
                    "run the recommended second-order design with a replication artifact",
                    "rerun evidence-tier, strict-gate, and scoreboard generation",
                ],
            }
        )
    return decorated


def family_portfolio(
    rows: list[dict[str, Any]],
    families: dict[str, dict[str, Any]],
    inventory: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    candidate_ids: dict[str, list[str]] = defaultdict(list)
    held_links: Counter[str] = Counter()
    layer_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for source in row["recommended_source_path"]:
            family_id = source["family_id"]
            candidate_ids[family_id].append(row["hypothesis_id"])
            held_links[family_id] += int(row["public_claim_links_at_gate"])
            layer_counts[family_id].update(source["layers_covered"])
        for layer in row["uncovered_layers"]:
            family_id = f"source_family_gap:{layer}"
            candidate_ids[family_id].append(row["hypothesis_id"])
            held_links[family_id] += int(row["public_claim_links_at_gate"])
            layer_counts[family_id][layer] += 1

    portfolio: list[dict[str, Any]] = []
    for family_id, ids in candidate_ids.items():
        is_catalog_gap = family_id.startswith("source_family_gap:")
        record = families.get(family_id, {})
        readiness = (
            "source_family_gap"
            if is_catalog_gap
            else str(record.get("readiness") or "unknown")
        )
        layer = family_id.partition(":")[2] if is_catalog_gap else None
        registered_sources = inventory.get(family_id, [])
        portfolio.append(
            {
                "family_id": family_id,
                "name": (
                    f"Unmapped source family for {layer}"
                    if is_catalog_gap
                    else record.get("name")
                ),
                "readiness": readiness,
                "candidate_count": len(ids),
                "held_link_exposure": held_links[family_id],
                "layer_counts": dict(layer_counts[family_id]),
                "existing_fetchers": record.get("existing_fetchers") or [],
                "publisher_refs": record.get("publisher_refs") or [],
                "inventory_status": (
                    "missing_family_definition"
                    if is_catalog_gap
                    else (
                        "registered_concrete_sources"
                        if registered_sources
                        else "family_only_no_concrete_source"
                    )
                ),
                "registered_source_count": len(registered_sources),
                "registered_sources": [
                    {
                        "source_id": source.get("source_id"),
                        "source_name": source.get("source_name"),
                        "source_url": source.get("source_url"),
                        "acquisition_status": source.get("acquisition_status"),
                        "ingestion_difficulty": source.get("ingestion_difficulty"),
                        "immediate_payoff_rank": source.get("immediate_payoff_rank"),
                        "verification_status": source.get("verification_status"),
                    }
                    for source in registered_sources[:10]
                ],
                "work_required": ACQUISITION_ACTION[readiness],
                "top_candidate_ids": ids[:10],
            }
        )
    portfolio.sort(
        key=lambda item: (
            -item["candidate_count"],
            -item["held_link_exposure"],
            -READINESS_ORDER.get(item["readiness"], 0),
            item["family_id"],
        )
    )
    return portfolio


def counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "unknown") for row in rows))


def summarize_wave(rows: list[dict[str, Any]], wave: int) -> dict[str, Any]:
    selected = [row for row in rows if row["wave"] == wave]
    return {
        "wave": wave,
        "rank_range": [selected[0]["rank"], selected[-1]["rank"]],
        "candidate_count": len(selected),
        "held_link_exposure": sum(
            int(row["public_claim_links_at_gate"]) for row in selected
        ),
        "failure_credit_holds": sum(
            int(row["failure_credit_holds"]) for row in selected
        ),
        "acquisition_class_counts": counts(selected, "acquisition_class"),
    }


def build_payload() -> dict[str, Any]:
    backlog_payload = load_json(BACKLOG_PATH)
    source_payload = load_yaml(SOURCE_PATH)
    source_index_payload = load_json(SOURCE_INDEX_PATH)
    families = source_payload.get("source_families") or {}
    inventory: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in source_index_payload.get("sources") or []:
        family_id = source.get("source_family_id")
        if family_id:
            inventory[str(family_id)].append(source)
    for source_rows in inventory.values():
        source_rows.sort(
            key=lambda source: (
                int(source.get("immediate_payoff_rank") or 10**9),
                str(source.get("source_id") or ""),
            )
        )
    backlog = backlog_payload.get("backlog") or []
    backlog_summary = backlog_payload.get("summary") or {}
    inventory_snapshot = (
        source_index_payload.get("summary", {}).get("backlog_snapshot") or {}
    )
    expected_snapshot = {
        "held_hypotheses": len(backlog),
        "strict_held_public_claim_links": int(
            backlog_summary.get("held_public_claim_links") or 0
        ),
    }
    for field, expected in expected_snapshot.items():
        if int(inventory_snapshot.get(field) or 0) != expected:
            raise RuntimeError(
                f"stale second-order source index: {field}="
                f"{inventory_snapshot.get(field)!r}, expected {expected}; "
                "update source_inventory.yaml and regenerate the source index"
            )
    if len(backlog) < QUEUE_SIZE:
        raise RuntimeError(
            f"backlog has only {len(backlog)} hypotheses; need {QUEUE_SIZE}"
        )

    leverage = Counter()
    for row in backlog:
        leverage.update(
            source["family_id"]
            for source in row.get("source_families") or []
            if source.get("family_id")
        )

    full_rows = decorate_rows(backlog, families, leverage, inventory)
    queue = full_rows[:QUEUE_SIZE]
    total_held_links = int(backlog_summary.get("held_public_claim_links") or 0)
    queue_held_links = sum(
        int(row["public_claim_links_at_gate"]) for row in queue
    )

    layer_counts = Counter()
    for row in queue:
        layer_counts.update(row["missing_layers"])

    return {
        "schema_version": 1,
        "generated_at": date.today().isoformat(),
        "generated_by": "scripts/plan_next_200_scoreboard_upgrades.py",
        "inputs": [
            str(BACKLOG_PATH.relative_to(ROOT)),
            str(SOURCE_PATH.relative_to(ROOT)),
            str(SOURCE_INDEX_PATH.relative_to(ROOT)),
        ],
        "objective": (
            "Graduate the 200 highest-leverage existing hypotheses through "
            "measured second-order contracts and into the strict A-net scoreboard."
        ),
        "guardrail": (
            "Held-link exposure is the maximum set touched by these upgrades, "
            "not a promised score change. A link becomes eligible only after "
            "its required layers, replication, estimator, and evidence gates pass."
        ),
        "selection": {
            "source_pool": "strict-gate-held hypotheses with public claim links",
            "ranking": (
                "existing second-order backlog priority: public links, absolute "
                "score weight, failure-credit holds, declared contracts, source "
                "readiness, and layer burden"
            ),
            "queue_size": len(queue),
            "whole_corpus_held_hypotheses": len(backlog),
            "queue_held_link_exposure": queue_held_links,
            "whole_corpus_held_public_claim_links": total_held_links,
            "queue_share_of_held_links": round(
                queue_held_links / total_held_links, 4
            )
            if total_held_links
            else 0,
            "failure_credit_holds": sum(
                int(row["failure_credit_holds"]) for row in queue
            ),
            "missing_contract_candidates": sum(
                row["missing_layer_source"] == "inferred_missing_contract"
                for row in queue
            ),
            "declared_contract_candidates": sum(
                row["missing_layer_source"] == "declared_contract_or_gate"
                for row in queue
            ),
            "topic_counts": counts(queue, "topic"),
            "status_counts": counts(queue, "current_status"),
            "evidence_type_counts": counts(queue, "evidence_type"),
            "acquisition_class_counts": counts(queue, "acquisition_class"),
            "candidates_with_source_inventory_gaps": sum(
                any(
                    source["inventory_status"]
                    == "family_only_no_concrete_source"
                    for source in row["recommended_source_path"]
                )
                for row in queue
            ),
            "registered_concrete_source_records": int(
                source_index_payload.get("summary", {}).get("source_count") or 0
            ),
            "missing_layer_counts": dict(layer_counts),
        },
        "waves": [
            summarize_wave(queue, wave)
            for wave in range(1, (QUEUE_SIZE // WAVE_SIZE) + 1)
        ],
        "top_200_data_gap_portfolio": family_portfolio(
            queue, families, inventory
        ),
        "whole_corpus_data_gap_portfolio": family_portfolio(
            full_rows, families, inventory
        ),
        "candidates": queue,
    }


def compact_counts(value: dict[str, int]) -> str:
    return ", ".join(f"{key}={count}" for key, count in sorted(value.items()))


def render_markdown(payload: dict[str, Any]) -> str:
    selection = payload["selection"]
    lines = [
        "# Next 200 Scoreboard Upgrades and Data-Gap Roadmap",
        "",
        (
            f"The queue contains exactly **{selection['queue_size']}** existing "
            "hypotheses. Together they touch "
            f"**{selection['queue_held_link_exposure']:,}** currently held public "
            "claim links, or "
            f"**{selection['queue_share_of_held_links']:.1%}** of the strict-gate "
            "backlog."
        ),
        "",
        "These are integrity upgrades, not 200 disconnected new hypotheses: each candidate already has a public scoreboard relationship, and each must add measured mechanism layers before it can affect A-net.",
        "",
        "## Selection and guardrail",
        "",
        f"- Source pool: {selection['whole_corpus_held_hypotheses']} held hypotheses / {selection['whole_corpus_held_public_claim_links']:,} held public links.",
        f"- Missing-contract candidates: {selection['missing_contract_candidates']}; declared-contract completions: {selection['declared_contract_candidates']}.",
        f"- Failure-credit holds in the queue: {selection['failure_credit_holds']}.",
        f"- Evidence types: {compact_counts(selection['evidence_type_counts'])}.",
        f"- Acquisition classes: {compact_counts(selection['acquisition_class_counts'])}.",
        (
            "- Concrete source inventory: "
            f"{selection['registered_concrete_source_records']} records; "
            f"{selection['candidates_with_source_inventory_gaps']} candidates "
            "use at least one defined family that still lacks a concrete "
            "second-order source record."
        ),
        f"- Guardrail: {payload['guardrail']}",
        "",
        "## Four execution waves",
        "",
        "| wave | ranks | candidates | held-link exposure | failure holds | acquisition classes |",
        "| ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for wave in payload["waves"]:
        lines.append(
            f"| {wave['wave']} | {wave['rank_range'][0]}–{wave['rank_range'][1]} | "
            f"{wave['candidate_count']} | {wave['held_link_exposure']:,} | "
            f"{wave['failure_credit_holds']} | "
            f"{compact_counts(wave['acquisition_class_counts'])} |"
        )

    lines.extend(
        [
            "",
            "## Highest-leverage data workstreams",
            "",
            "Candidate and link counts overlap across workstreams because a defensible mechanism test often needs more than one data family.",
            "",
            "| rank | data family | readiness | top-200 candidates | held-link exposure | concrete sources | work required |",
            "| ---: | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for rank, family in enumerate(
        payload["top_200_data_gap_portfolio"][:20], start=1
    ):
        sources = ", ".join(
            source["source_id"] for source in family["registered_sources"][:3]
        )
        if not sources:
            sources = family["inventory_status"]
        lines.append(
            f"| {rank} | `{family['family_id']}` | {family['readiness']} | "
            f"{family['candidate_count']} | {family['held_link_exposure']:,} | "
            f"{sources} | {family['work_required']} |"
        )

    lines.extend(
        [
            "",
            "## Whole-corpus leverage",
            "",
            "| rank | data family | readiness | held hypotheses | held-link exposure | concrete sources |",
            "| ---: | --- | --- | ---: | ---: | --- |",
        ]
    )
    for rank, family in enumerate(
        payload["whole_corpus_data_gap_portfolio"][:20], start=1
    ):
        sources = ", ".join(
            source["source_id"] for source in family["registered_sources"][:3]
        )
        if not sources:
            sources = family["inventory_status"]
        lines.append(
            f"| {rank} | `{family['family_id']}` | {family['readiness']} | "
            f"{family['candidate_count']} | {family['held_link_exposure']:,} | "
            f"{sources} |"
        )

    lines.extend(
        [
            "",
            "## Exact 200-candidate queue",
            "",
            "| rank | wave | hypothesis | topic | held links | priority | missing layers | source path | acquisition |",
            "| ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in payload["candidates"]:
        layers = ", ".join(row["missing_layers"])
        sources = ", ".join(
            source["family_id"] for source in row["recommended_source_path"]
        )
        if row["uncovered_layers"]:
            sources += (
                "; unresolved: " + ", ".join(row["uncovered_layers"])
            )
        lines.append(
            f"| {row['rank']} | {row['wave']} | `{row['hypothesis_id']}` | "
            f"{row['topic']} | {row['public_claim_links_at_gate']} | "
            f"{row['priority']:.2f} | {layers} | {sources} | "
            f"{row['acquisition_class']} |"
        )

    lines.extend(
        [
            "",
            "## Graduation definition",
            "",
            "A candidate graduates only when its mechanism contract is explicit, every dispositive layer is measured or honestly marked as a gap, the registered estimator runs with replication artifacts, and the evidence-tier plus strict scoreboard gates pass. The queue should be regenerated after each 50-candidate wave so later ranks absorb the evidence actually gained.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    payload = build_payload()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(payload))
    print(json.dumps(payload["selection"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
