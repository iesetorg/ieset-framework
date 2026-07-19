#!/usr/bin/env python3
"""Graduate scoreboard-safe policy-contrast hypotheses via prior mappings.

The policy-contrast wave was estimated before it had school links.  This pass
does not infer ideology from the observed result.  A target is eligible only
when:

1. the wave graduation audit says it passed every research gate;
2. it survives the pre-declared Benjamini-Hochberg 10% FDR gate; and
3. an older, already-mapped hypothesis tests the same treatment/outcome
   mechanism, allowing the target to inherit school predictions and polarity.

Usage:
    python scripts/apply_scoreboard_graduation_wave_2026_07_19.py
    python scripts/apply_scoreboard_graduation_wave_2026_07_19.py --apply
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from apply_market_order_opposition_coverage_wave import insert_covers_yaml
from audit_scoreboard_outcomes import (
    BENCHMARK_CONTROL_POSITION_IDS,
    hypothesis_public_verdict,
    score_positions,
    score_signal,
    verdict_class,
    write_outputs,
)
from backfill_hypothesis_schools import insert_fsc_yaml


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESES = ROOT / "hypotheses"
POSITIONS = ROOT / "positions"
RUNS = ROOT / "engine" / "runs"
AUDITS = ROOT / "engine" / "audits"
PREREG_INDEX = ROOT / "engine" / "preregistration_index.json"
WAVE_AUDIT = AUDITS / "policy_contrast_wave_100_2026_07_18_graduation.json"
AUDIT_BASE = AUDITS / "scoreboard_graduation_wave_2026-07-19"
SCOREBOARD_BASE = AUDITS / "scoreboard_prediction_outcome_audit_2026-07-19"


# Each mapping is narrow on both treatment and outcome.  The source hypothesis
# already has reciprocal school predictions, so no prediction label is chosen
# from the target's observed sign.
TARGET_TO_SISTER = {
    "pcw100_global_efw_legal_rights_investment":
        "market_order_rule_of_law_investment_share_panel",
    "pcw100_global_efw_legal_rights_gdp_growth":
        "market_order_rule_of_law_gdp_pc_growth_panel",
    "pcw100_global_efw_regulation_employment":
        "market_order_regulatory_quality_employment_rate_panel",
    "pcw100_global_efw_regulation_gdp_growth":
        "market_order_regulatory_quality_gdp_pc_growth_panel",
    "pcw100_global_efw_regulation_investment":
        "market_order_regulatory_quality_investment_share_panel",
    "pcw100_global_efw_sound_money_employment":
        "market_order_sound_money_employment_rate_panel",
    "pcw100_global_efw_sound_money_gdp_growth":
        "market_order_sound_money_gdp_pc_growth_panel",
    "pcw100_global_efw_sound_money_investment":
        "market_order_sound_money_investment_share_panel",
    "pcw100_global_efw_trade_freedom_employment":
        "market_order_trade_openness_employment_rate_panel",
    "pcw100_global_efw_trade_freedom_gdp_growth":
        "market_order_trade_openness_gdp_pc_growth_panel",
    "pcw100_us_mw_binding_premium_p10_wage":
        "minimum_wage_bite_low_pay_poverty_employment_panel",
    "pcw100_us_mw_bite_ratio_p10_wage":
        "minimum_wage_bite_low_pay_poverty_employment_panel",
    "pcw100_us_mw_binding_premium_food_weekly_wage":
        "minimum_wage_bite_low_pay_poverty_employment_panel",
    "pcw100_us_mw_bite_ratio_food_weekly_wage":
        "minimum_wage_bite_low_pay_poverty_employment_panel",
}

FDR_HOLDS = {
    "pcw100_global_efw_legal_rights_life_expectancy":
        "No pre-existing school claim matches legal-rights treatment and life expectancy.",
    "pcw100_global_efw_legal_rights_under5_mortality":
        "No pre-existing school claim matches legal-rights treatment and under-five mortality.",
    "pcw100_global_efw_legal_rights_manufacturing":
        "No pre-existing school claim matches legal-rights treatment and manufacturing share.",
}

MINIMUM_WAGE_CLUSTER = {
    "pcw100_us_mw_binding_premium_p10_wage",
    "pcw100_us_mw_bite_ratio_p10_wage",
    "pcw100_us_mw_binding_premium_food_weekly_wage",
    "pcw100_us_mw_bite_ratio_food_weekly_wage",
}
MINIMUM_WAGE_SENSITIVITY_REPRESENTATIVE = "pcw100_us_mw_bite_ratio_p10_wage"

WAVE_NOTE = (
    "2026-07-19 scoreboard graduation. Target eligibility was fixed by the "
    "wave's research-graduation checks and BH q<0.10. School prediction, "
    "polarity, and confidence are inherited from an older exact-mechanism "
    "sister mapping; none was chosen from the target result. Evidence is "
    "associational and receives 0.5 scoreboard quality weight."
)


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def hypothesis_paths() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in sorted(HYPOTHESES.glob("*/*.yaml")):
        if path.parent.name in {"steelman", "conditional_taxonomy"}:
            continue
        doc = load_yaml(path)
        hypothesis_id = doc.get("hypothesis_id")
        if hypothesis_id:
            out[hypothesis_id] = path
    return out


def position_docs() -> dict[str, tuple[Path, dict[str, Any]]]:
    out: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(POSITIONS.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = load_yaml(path)
        position_id = doc.get("position_id")
        if position_id:
            out[position_id] = (path, doc)
    return out


def inbound_links(positions: dict[str, tuple[Path, dict[str, Any]]]) -> set[str]:
    return {
        claim.get("linked_hypothesis_id")
        for _, doc in positions.values()
        for claim in (doc.get("falsifiable_specific_claims") or [])
        if claim.get("linked_hypothesis_id")
    }


def steelman_exists(hypothesis: dict[str, Any], hypothesis_id: str) -> bool:
    declared = hypothesis.get("steelman")
    if declared:
        return (ROOT / declared).exists()
    return (HYPOTHESES / "steelman" / f"{hypothesis_id}.md").exists()


def repo_inventory(
    paths: dict[str, Path],
    positions: dict[str, tuple[Path, dict[str, Any]]],
) -> dict[str, Any]:
    """Inventory the whole formal library under one conservative gate."""
    registrations = json.loads(PREREG_INDEX.read_text(encoding="utf-8")).get(
        "registrations", {}
    )
    hypotheses = {hid: load_yaml(path) for hid, path in paths.items()}
    inbound = inbound_links(positions)
    totals: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    unmapped: list[dict[str, Any]] = []

    for hypothesis_id, hypothesis in hypotheses.items():
        totals["formal_hypotheses"] += 1
        run_dir = RUNS / hypothesis_id
        verified = registrations.get(hypothesis_id, {}).get("status") == "verified"
        replication = (run_dir / "replication.py").exists()
        packet = (run_dir / "evidence_packet.yaml").exists()
        steelman = steelman_exists(hypothesis, hypothesis_id)
        public, verdict = hypothesis_public_verdict(hypothesis_id, hypotheses)
        mapped = bool(hypothesis.get("covers_claims")) or hypothesis_id in inbound

        totals["strict_prereg_verified"] += int(verified)
        totals["replication_present"] += int(replication)
        totals["evidence_packet_present"] += int(packet)
        totals["steelman_present"] += int(steelman)
        totals["public_verdict"] += int(public)
        totals["mapped"] += int(mapped)

        fully_graduated = verified and replication and packet and steelman and public
        if not fully_graduated:
            continue
        totals["fully_graduated"] += 1
        if mapped:
            totals["fully_graduated_mapped"] += 1
            continue

        kind = verdict_class(verdict)
        decisive = kind in {"supported", "refuted"}
        totals["fully_graduated_unmapped"] += 1
        totals["fully_graduated_unmapped_decisive"] += int(decisive)
        totals["fully_graduated_unmapped_nondecisive"] += int(not decisive)
        topic = paths[hypothesis_id].parent.name
        evidence_type = hypothesis.get("evidence_type") or "unspecified"
        topic_counts[topic] += 1
        evidence_counts[evidence_type] += 1
        verdict_counts[kind] += 1
        unmapped.append(
            {
                "hypothesis_id": hypothesis_id,
                "topic": topic,
                "verdict": verdict,
                "verdict_class": kind,
                "evidence_type": evidence_type,
                "claim": " ".join(str(hypothesis.get("claim") or "").split()),
            }
        )

    return {
        "gate": [
            "strict preregistration index status=verified",
            "public non-stub verdict",
            "replication.py present",
            "evidence_packet.yaml present",
            "steelman present",
        ],
        "counts": dict(totals),
        "unmapped_by_topic": dict(sorted(topic_counts.items())),
        "unmapped_by_evidence_type": dict(sorted(evidence_counts.items())),
        "unmapped_by_verdict_class": dict(sorted(verdict_counts.items())),
        "unmapped": sorted(unmapped, key=lambda row: row["hypothesis_id"]),
    }


def source_claim(
    position: dict[str, Any], sister_id: str, claim_index: int
) -> dict[str, Any]:
    claims = position.get("falsifiable_specific_claims") or []
    if not 0 <= claim_index < len(claims):
        raise ValueError(
            f"{position.get('position_id')} sister index {claim_index} is out of range"
        )
    claim = claims[claim_index]
    if claim.get("linked_hypothesis_id") != sister_id:
        raise ValueError(
            f"{position.get('position_id')}#{claim_index} does not link to {sister_id}"
        )
    return claim


def wave_rows() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    audit = json.loads(WAVE_AUDIT.read_text(encoding="utf-8"))
    return audit, {
        row["hypothesis_id"]: row for row in audit.get("hypotheses", [])
    }


def build_plan(
    paths: dict[str, Path],
    positions: dict[str, tuple[Path, dict[str, Any]]],
) -> list[dict[str, Any]]:
    audit, rows = wave_rows()
    if not audit.get("all_graduated") or audit.get("graduated_count") != 100:
        raise ValueError("the 100-hypothesis research graduation audit is not clean")

    plan: list[dict[str, Any]] = []
    for target_id, sister_id in TARGET_TO_SISTER.items():
        if target_id not in paths or sister_id not in paths:
            raise ValueError(f"missing target/sister spec: {target_id} / {sister_id}")
        target = load_yaml(paths[target_id])
        sister = load_yaml(paths[sister_id])
        row = rows.get(target_id) or {}
        if not row.get("graduated") or not row.get("fdr_bh_10"):
            raise ValueError(f"{target_id} does not pass graduation + BH q<0.10")
        if verdict_class(row.get("verdict")) not in {"supported", "refuted"}:
            raise ValueError(f"{target_id} is not decisive: {row.get('verdict')}")
        covers = sister.get("covers_claims") or []
        if not covers:
            raise ValueError(f"sister {sister_id} has no prior school coverage")

        inherited: list[dict[str, Any]] = []
        for cover in covers:
            position_id = cover.get("position_id")
            if position_id not in positions:
                raise ValueError(f"missing position {position_id}")
            position = positions[position_id][1]
            prior_claim = source_claim(
                position, sister_id, int(cover.get("claim_index", -1))
            )
            prediction = cover.get("school_prediction") or prior_claim.get(
                "school_prediction"
            )
            polarity = cover.get("polarity") or prior_claim.get(
                "claim_polarity", "aligned"
            )
            if prediction not in {"supported", "falsified", "mixed"}:
                raise ValueError(
                    f"{sister_id} -> {position_id} has invalid prediction {prediction}"
                )
            if prior_claim.get("school_prediction") != prediction:
                raise ValueError(
                    f"{sister_id} -> {position_id} prediction is not reciprocal"
                )
            if prior_claim.get("claim_polarity", "aligned") != polarity:
                raise ValueError(
                    f"{sister_id} -> {position_id} polarity is not reciprocal"
                )
            inherited.append(
                {
                    "position_id": position_id,
                    "school_prediction": prediction,
                    "polarity": polarity,
                    "confidence": cover.get("confidence") or "medium",
                    "source_claim_index": cover["claim_index"],
                }
            )

        plan.append(
            {
                "target_id": target_id,
                "sister_id": sister_id,
                "target": target,
                "verdict": row["verdict"],
                "fdr_bh_q_value": row.get("fdr_bh_q_value"),
                "inherited": inherited,
            }
        )

    robust_ids = {
        row["hypothesis_id"]
        for row in rows.values()
        if row.get("graduated") and row.get("fdr_bh_10")
    }
    accounted = set(TARGET_TO_SISTER) | set(FDR_HOLDS)
    if robust_ids != accounted:
        missing = sorted(robust_ids - accounted)
        extra = sorted(accounted - robust_ids)
        raise ValueError(f"FDR accounting mismatch; missing={missing}, extra={extra}")
    return plan


def claim_text(
    position_id: str, prediction: str, target: dict[str, Any]
) -> str:
    school = position_id.replace("_", " ").title()
    claim = " ".join(str(target.get("claim") or "").split())
    if prediction == "supported":
        return f"{school} predicts this policy-contrast claim should hold: {claim}"
    if prediction == "falsified":
        return (
            f"{school} predicts this policy-contrast claim should not hold "
            f"as a general rule: {claim}"
        )
    return (
        f"{school} treats this policy-contrast claim as conditional rather "
        f"than dispositive: {claim}"
    )


def mapping_note(sister_id: str, target_id: str) -> str:
    cluster = (
        " This target belongs to the four-model minimum-wage wage-outcome "
        "cluster; read the cluster sensitivity in the audit."
        if target_id in MINIMUM_WAGE_CLUSTER
        else ""
    )
    return f"{WAVE_NOTE} Sister={sister_id}.{cluster}"


def apply_plan(
    plan: list[dict[str, Any]],
    paths: dict[str, Path],
    positions: dict[str, tuple[Path, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Append position claims, then reciprocal target covers_claims."""
    existing_inbound: dict[tuple[str, str], int] = {}
    blocks_by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    start_indexes: dict[str, int] = {}
    planned_indexes: dict[tuple[str, str], int] = {}

    for position_id, (_, position) in positions.items():
        claims = position.get("falsifiable_specific_claims") or []
        start_indexes[position_id] = len(claims)
        for index, claim in enumerate(claims):
            hypothesis_id = claim.get("linked_hypothesis_id")
            if hypothesis_id:
                existing_inbound[(position_id, hypothesis_id)] = index

    for item in plan:
        target_id = item["target_id"]
        target = item["target"]
        empirical_status = verdict_class(item["verdict"])
        for inherited in item["inherited"]:
            position_id = inherited["position_id"]
            key = (position_id, target_id)
            if key in existing_inbound:
                planned_indexes[key] = existing_inbound[key]
                continue
            planned_indexes[key] = (
                start_indexes[position_id] + len(blocks_by_position[position_id])
            )
            blocks_by_position[position_id].append(
                {
                    "claim": claim_text(
                        position_id, inherited["school_prediction"], target
                    ),
                    "linked_hypothesis_id": target_id,
                    "school_prediction": inherited["school_prediction"],
                    "claim_polarity": inherited["polarity"],
                    "empirical_status": empirical_status,
                    "scope": target.get("scope") or {},
                    "notes": mapping_note(item["sister_id"], target_id),
                }
            )

    for position_id, blocks in blocks_by_position.items():
        if not blocks:
            continue
        path = positions[position_id][0]
        path.write_text(
            insert_fsc_yaml(path.read_text(encoding="utf-8"), blocks),
            encoding="utf-8",
        )

    entries: list[dict[str, Any]] = []
    for item in plan:
        target_id = item["target_id"]
        path = paths[target_id]
        current = load_yaml(path)
        current_covers = current.get("covers_claims") or []
        existing_pairs = {
            (entry.get("position_id"), int(entry.get("claim_index", -1)))
            for entry in current_covers
        }
        new_entries: list[dict[str, Any]] = []
        for inherited in item["inherited"]:
            position_id = inherited["position_id"]
            claim_index = planned_indexes[(position_id, target_id)]
            if (position_id, claim_index) in existing_pairs:
                continue
            entry = {
                "position_id": position_id,
                "claim_index": claim_index,
                "polarity": inherited["polarity"],
                "school_prediction": inherited["school_prediction"],
                "confidence": inherited["confidence"],
                "notes": mapping_note(item["sister_id"], target_id),
            }
            new_entries.append(entry)
            entries.append(
                {
                    "hypothesis_id": target_id,
                    "sister_hypothesis_id": item["sister_id"],
                    **entry,
                }
            )
        if new_entries:
            path.write_text(
                insert_covers_yaml(
                    path.read_text(encoding="utf-8"), new_entries
                ),
                encoding="utf-8",
            )
    return entries


def score_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    positions = audit["positions"]
    school_rows = [
        row
        for position_id, row in positions.items()
        if row.get("scoreboard_role") != "benchmark_control"
        and position_id not in BENCHMARK_CONTROL_POSITION_IDS
    ]
    return {
        "public_claim_links": audit["public_claim_links"],
        "school_signal_counts": dict(
            sorted(Counter(row["adjusted_score_signal"] for row in school_rows).items())
        ),
        "positions": {
            position_id: {
                "q_net": row["adjusted_net_score"],
                "q_tested": row["adjusted_tested_weight"],
                "q_signal": row["adjusted_score_signal"],
                "q_band": row["adjusted_signal_threshold"],
                "raw_net": row["net_score"],
                "tested": row["tested"],
                "counts": row["counts"],
            }
            for position_id, row in sorted(positions.items())
        },
    }


def score_changes(
    before: dict[str, Any], after: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    before_positions = before["positions"]
    after_positions = after["positions"]
    for position_id in sorted(after_positions):
        old = before_positions[position_id]
        new = after_positions[position_id]
        q_delta = new["adjusted_net_score"] - old["adjusted_net_score"]
        tested_delta = new["tested"] - old["tested"]
        if not q_delta and not tested_delta:
            continue
        rows.append(
            {
                "position_id": position_id,
                "scoreboard_role": new.get("scoreboard_role"),
                "q_net_before": old["adjusted_net_score"],
                "q_net_after": new["adjusted_net_score"],
                "q_net_delta": q_delta,
                "tested_before": old["tested"],
                "tested_after": new["tested"],
                "tested_delta": tested_delta,
                "signal_before": old["adjusted_score_signal"],
                "signal_after": new["adjusted_score_signal"],
            }
        )
    return rows


def minimum_wage_cluster_sensitivity(
    plan: list[dict[str, Any]], after: dict[str, Any]
) -> list[dict[str, Any]]:
    """Remove three correlated MW models from the official post-map score."""
    remove = MINIMUM_WAGE_CLUSTER - {MINIMUM_WAGE_SENSITIVITY_REPRESENTATIVE}
    deltas: dict[str, dict[str, float]] = defaultdict(
        lambda: {"q_net": 0.0, "q_tested": 0.0, "raw_net": 0.0, "tested": 0.0}
    )
    for item in plan:
        if item["target_id"] not in remove:
            continue
        for inherited in item["inherited"]:
            position_id = inherited["position_id"]
            prediction = inherited["school_prediction"]
            raw = 1.0 if prediction == "supported" else -1.0 if prediction == "falsified" else 0.0
            deltas[position_id]["raw_net"] += raw
            deltas[position_id]["q_net"] += raw * 0.5
            deltas[position_id]["tested"] += 1.0
            deltas[position_id]["q_tested"] += 0.5

    rows = []
    for position_id, removed in sorted(deltas.items()):
        official = after["positions"][position_id]
        q_net = official["adjusted_net_score"] - removed["q_net"]
        q_tested = official["adjusted_tested_weight"] - removed["q_tested"]
        signal = score_signal(q_net, q_tested)
        rows.append(
            {
                "position_id": position_id,
                "representative_retained": MINIMUM_WAGE_SENSITIVITY_REPRESENTATIVE,
                "formal_models_removed": 3,
                "official_q_net": official["adjusted_net_score"],
                "cluster_sensitivity_q_net": q_net,
                "cluster_sensitivity_q_tested": q_tested,
                "cluster_sensitivity_signal": signal["score_signal"],
            }
        )
    return rows


def analytic_freeze_check(paths: dict[str, Path]) -> dict[str, Any]:
    """Confirm post-run changes are limited to scoreboard linkage metadata."""
    rows = []
    for target_id in TARGET_TO_SISTER:
        current = load_yaml(paths[target_id])
        frozen = load_yaml(RUNS / target_id / "hypothesis.yaml")
        current_analytic = dict(current)
        frozen_analytic = dict(frozen)
        current_analytic.pop("covers_claims", None)
        frozen_analytic.pop("covers_claims", None)
        rows.append(
            {
                "hypothesis_id": target_id,
                "analytic_fields_match_frozen_run": current_analytic == frozen_analytic,
                "current_cover_count": len(current.get("covers_claims") or []),
                "frozen_cover_count": len(frozen.get("covers_claims") or []),
            }
        )
    return {
        "all_analytic_fields_match": all(
            row["analytic_fields_match_frozen_run"] for row in rows
        ),
        "excluded_metadata_field": "covers_claims",
        "rows": rows,
    }


def write_audit(
    plan: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    inventory_before: dict[str, Any],
    inventory_after: dict[str, Any],
    score_before: dict[str, Any],
    score_after: dict[str, Any],
    paths: dict[str, Path],
) -> None:
    by_position = Counter(entry["position_id"] for entry in entries)
    by_prediction = Counter(entry["school_prediction"] for entry in entries)
    wave_items = [
        {
            "hypothesis_id": item["target_id"],
            "sister_hypothesis_id": item["sister_id"],
            "verdict": item["verdict"],
            "fdr_bh_q_value": item["fdr_bh_q_value"],
            "new_claim_links": sum(
                entry["hypothesis_id"] == item["target_id"] for entry in entries
            ),
            "inherited_positions": [
                {
                    key: inherited[key]
                    for key in (
                        "position_id",
                        "school_prediction",
                        "polarity",
                        "confidence",
                        "source_claim_index",
                    )
                }
                for inherited in item["inherited"]
            ],
            "correlated_family": (
                "minimum_wage_wage_outcomes"
                if item["target_id"] in MINIMUM_WAGE_CLUSTER
                else None
            ),
        }
        for item in plan
    ]
    changes = score_changes(score_before, score_after)
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "wave": "scoreboard_graduation_wave_2026-07-19",
        "methodology_gate": {
            "research_gate": "All targets passed the 100-wave graduation audit.",
            "multiplicity_gate": "All targets survive Benjamini-Hochberg FDR q<0.10 across the 100 registered tests.",
            "mapping_gate": "School prediction, polarity, and confidence inherit from an older exact treatment/outcome sister mapping.",
            "post_result_safeguard": "The observed target sign was not used to choose a school prediction. Three FDR-robust results without an exact sister remain held.",
            "quality_weight": "All promoted targets are associational and receive 0.5 Q-weight.",
            "correlation_caution": "Four minimum-wage wage models are formal hypotheses but a correlated evidence cluster; a one-representative sensitivity is reported.",
        },
        "repo_inventory_before": inventory_before,
        "repo_inventory_after": inventory_after,
        "wave_counts": {
            "research_graduated": 100,
            "fdr_robust": len(TARGET_TO_SISTER) + len(FDR_HOLDS),
            "scoreboard_promoted": len(TARGET_TO_SISTER),
            "fdr_robust_held_no_exact_sister": len(FDR_HOLDS),
            "new_reciprocal_claim_links": len(entries),
            "minimum_wage_formal_hypotheses": len(MINIMUM_WAGE_CLUSTER),
            "minimum_wage_cluster_representatives_in_sensitivity": 1,
        },
        "new_links_by_position": dict(sorted(by_position.items())),
        "new_links_by_school_prediction": dict(sorted(by_prediction.items())),
        "promoted": wave_items,
        "held_fdr_robust": [
            {"hypothesis_id": hypothesis_id, "reason": reason}
            for hypothesis_id, reason in FDR_HOLDS.items()
        ],
        "entries": entries,
        "analytic_freeze_check": analytic_freeze_check(paths),
        "scoreboard_before": score_snapshot(score_before),
        "scoreboard_after": score_snapshot(score_after),
        "scoreboard_changes": changes,
        "minimum_wage_cluster_sensitivity": minimum_wage_cluster_sensitivity(
            plan, score_after
        ),
    }
    AUDIT_BASE.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    before_counts = inventory_before["counts"]
    after_counts = inventory_after["counts"]
    lines = [
        "# Scoreboard Graduation Wave — 2026-07-19",
        "",
        f"Generated: {payload['generated_utc']}",
        "",
        "## Bottom Line",
        "",
        f"- Research-graduated in the new-data wave: **100**.",
        f"- Survive BH FDR at 10%: **{payload['wave_counts']['fdr_robust']}**.",
        f"- Safe to map through an exact older sister claim: **{len(TARGET_TO_SISTER)}**.",
        f"- Robust but held for no exact prior school mapping: **{len(FDR_HOLDS)}**.",
        f"- New reciprocal position/hypothesis claim links: **{len(entries)}**.",
        "",
        "## Whole-Repository Funnel",
        "",
        f"- Formal hypotheses scanned: **{before_counts.get('formal_hypotheses', 0)}**.",
        f"- Fully graduated under the conservative repo screen: **{before_counts.get('fully_graduated', 0)}**.",
        f"- Fully graduated but unmapped before this pass: **{before_counts.get('fully_graduated_unmapped', 0)}** "
        f"({before_counts.get('fully_graduated_unmapped_decisive', 0)} decisive).",
        f"- Fully graduated but unmapped after this pass: **{after_counts.get('fully_graduated_unmapped', 0)}** "
        f"({after_counts.get('fully_graduated_unmapped_decisive', 0)} decisive).",
        "",
        "The remaining decisive queue is not automatically scoreboard-safe: each item still needs a prior prediction source, duplicate/correlation review, and exact scope matching.",
        "",
        "## Methodology Gate",
        "",
        "- Targets passed all research-graduation checks and BH q<0.10.",
        "- School prediction, polarity, and confidence inherit from an older exact treatment/outcome sister mapping.",
        "- The target result was not used to choose a school prediction.",
        "- Three robust hypotheses with no exact prior mapping remain held.",
        "- All promoted evidence is associational and receives 0.5 Q-weight.",
        "- Four minimum-wage wage models are correlated; the JSON includes a one-representative sensitivity.",
        "",
        "## Scoreboard Movement",
        "",
        f"- Public claim links: {score_before['public_claim_links']} → {score_after['public_claim_links']} "
        f"(+{score_after['public_claim_links'] - score_before['public_claim_links']}).",
        "",
        "| position | role | q-net before | q-net after | delta | tested delta | signal |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for change in changes:
        lines.append(
            f"| `{change['position_id']}` | {change['scoreboard_role']} | "
            f"{change['q_net_before']:.3f} | {change['q_net_after']:.3f} | "
            f"{change['q_net_delta']:+.3f} | {change['tested_delta']:+d} | "
            f"{change['signal_before']} → {change['signal_after']} |"
        )
    lines += [
        "",
        "## Promoted Hypotheses",
        "",
        "| target | inherited sister | verdict | BH q | links |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for item in wave_items:
        lines.append(
            f"| `{item['hypothesis_id']}` | `{item['sister_hypothesis_id']}` | "
            f"{item['verdict']} | {item['fdr_bh_q_value']:.6g} | "
            f"{item['new_claim_links']} |"
        )
    lines += ["", "## Robust Holds", ""]
    for hypothesis_id, reason in FDR_HOLDS.items():
        lines.append(f"- `{hypothesis_id}` — {reason}")
    lines += [
        "",
        "## Integrity",
        "",
        f"- Analytic fields still match frozen run copies (excluding `covers_claims` linkage metadata): "
        f"**{payload['analytic_freeze_check']['all_analytic_fields_match']}**.",
        f"- Scoreboard artifacts: `{SCOREBOARD_BASE.relative_to(ROOT)}.json` and `.md`.",
    ]
    AUDIT_BASE.with_suffix(".md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def dry_run_summary(plan: list[dict[str, Any]]) -> None:
    by_position: Counter[str] = Counter()
    by_prediction: Counter[str] = Counter()
    for item in plan:
        for inherited in item["inherited"]:
            by_position[inherited["position_id"]] += 1
            by_prediction[inherited["school_prediction"]] += 1
    print(
        json.dumps(
            {
                "mode": "dry_run",
                "research_graduated": 100,
                "fdr_robust": len(TARGET_TO_SISTER) + len(FDR_HOLDS),
                "scoreboard_eligible": len(plan),
                "held_no_exact_sister": len(FDR_HOLDS),
                "planned_reciprocal_links": sum(by_position.values()),
                "links_by_position": dict(sorted(by_position.items())),
                "links_by_prediction": dict(sorted(by_prediction.items())),
            },
            indent=2,
            sort_keys=True,
        )
    )


def assert_clean_target_mapping_state(
    paths: dict[str, Path],
    positions: dict[str, tuple[Path, dict[str, Any]]],
) -> None:
    target_ids = set(TARGET_TO_SISTER)
    forward = sum(
        claim.get("linked_hypothesis_id") in target_ids
        for _, position in positions.values()
        for claim in (position.get("falsifiable_specific_claims") or [])
    )
    reverse = sum(
        len(load_yaml(paths[target_id]).get("covers_claims") or [])
        for target_id in target_ids
    )
    if forward or reverse:
        raise ValueError(
            "refusing apply because target mappings already exist: "
            f"position_links={forward}, covers_claims={reverse}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    paths = hypothesis_paths()
    positions_before = position_docs()
    plan = build_plan(paths, positions_before)
    inventory_before = repo_inventory(paths, positions_before)
    if not args.apply:
        dry_run_summary(plan)
        return 0

    assert_clean_target_mapping_state(paths, positions_before)
    score_before = score_positions()
    entries = apply_plan(plan, paths, positions_before)
    if len(entries) != sum(len(item["inherited"]) for item in plan):
        raise ValueError(
            "refusing partial/idempotent apply: expected a clean unmapped target set"
        )

    positions_after = position_docs()
    inventory_after = repo_inventory(paths, positions_after)
    score_after = score_positions()
    write_outputs(score_after, SCOREBOARD_BASE)
    write_audit(
        plan,
        entries,
        inventory_before,
        inventory_after,
        score_before,
        score_after,
        paths,
    )
    print(
        json.dumps(
            {
                "scoreboard_promoted": len(plan),
                "new_reciprocal_links": len(entries),
                "public_claim_links_before": score_before["public_claim_links"],
                "public_claim_links_after": score_after["public_claim_links"],
                "audit": str(AUDIT_BASE.relative_to(ROOT)),
                "scoreboard": str(SCOREBOARD_BASE.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
