#!/usr/bin/env python3
"""Rank hypotheses that can test target schools' falsified predictions.

This audit is deliberately about *pre-registered exposure*, not score hunting:
it finds hypotheses where selected schools already have `school_prediction:
falsified` links, then reports the current verdict/data status so data-repair
work can be aimed at clean tests without changing mechanisms or links.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
TARGET_SCHOOLS = {
    "marxian",
    "social_democratic",
    "democratic_socialist",
    "marxist_leninist",
}

PRIMARY_PULLS = {
    "minimum_wage_above_median_employment_teen_effects": "minimum wage high-bite chain",
    "minimum_wage_disemployment_at_high_bite_ratios": "minimum wage high-bite chain",
    "wealth_tax_capital_flight_revenue_yield_gap": "wealth tax flight/yield chain",
    "nuclear_phaseout_grid_reliability_cost_tradeoff": "nuclear phaseout reliability/cost",
    "nuclear_phaseout_energy_cost_industry_exit": "nuclear phaseout reliability/cost",
    "strong_union_labour_law_youth_unemployment_south_europe": "union/EPL youth labour-market chain",
    "rent_control_housing_supply_quality_decay_chain": "rent control second/third-order chain",
    "rent_control_reduces_housing_supply_and_quality": "rent control second/third-order chain",
    "state_size_reduces_household_income_growth": "state-size household-income growth",
    "price_controls_produce_shortages_and_quality_degradation": "price-control shortage chain",
    "price_controls_shortage_black_market_progression": "price-control shortage chain",
}

SAFE = re.compile(r"[^A-Za-z0-9._-]+")

TOPIC_PRIORITY = {
    "labour": 0,
    "housing": 1,
    "fiscal": 2,
    "energy": 3,
    "regulatory": 4,
    "growth": 5,
    "distribution": 6,
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def verdict_bucket(verdict: Any) -> str:
    if not verdict:
        return "no_run"
    text = str(verdict).strip().lower()
    if text.startswith("supported"):
        return "supported"
    if text.startswith("refuted"):
        return "refuted"
    if text.startswith("partial"):
        return "partial"
    if text.startswith("mixed"):
        return "mixed"
    if text.startswith("inconclusive") or "data_pending" in text or text.startswith("blocked"):
        return "inconclusive"
    return text.split()[0] if text else "no_run"


def missing_sources_from_diagnostics(doc: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    data_status = doc.get("data_status") if isinstance(doc.get("data_status"), dict) else {}
    for item in data_status.get("variables_missing") or []:
        if isinstance(item, dict) and item.get("source"):
            sources.append(str(item["source"]))
        elif isinstance(item, str):
            sources.append(item)
    for key in ("missing_exact_vintages", "primary_data_gaps"):
        values = doc.get(key)
        if isinstance(values, list):
            sources.extend(str(v) for v in values)
    missing_data = doc.get("missing_data")
    if isinstance(missing_data, list):
        sources.extend(str(v) for v in missing_data)
    return sorted(dict.fromkeys(sources))


def sanitise_series(series_id: str) -> str:
    return SAFE.sub("_", series_id)


def source_is_on_disk(source: str) -> bool:
    if ":" not in source:
        return False
    publisher, series = source.split(":", 1)
    if not publisher or not series:
        return False
    if any(token in series.lower() for token in (";", "pending", "same as above", "constructed:", " no local ")):
        return False
    series = series.strip()
    pub_dir = ROOT / "data" / "vintages" / publisher.strip()
    if not pub_dir.exists():
        return False
    safe = sanitise_series(series)
    return bool(list(pub_dir.glob(f"{safe}@*.parquet")) or list(pub_dir.glob(f"{series}@*.parquet")))


def split_resolved_missing_sources(sources: list[str]) -> tuple[list[str], list[str]]:
    resolved: list[str] = []
    unresolved: list[str] = []
    for source in sources:
        if source_is_on_disk(source):
            resolved.append(source)
        else:
            unresolved.append(source)
    return sorted(dict.fromkeys(resolved)), sorted(dict.fromkeys(unresolved))


def loaded_count_from_diagnostics(doc: dict[str, Any]) -> int:
    data_status = doc.get("data_status") if isinstance(doc.get("data_status"), dict) else {}
    loaded = data_status.get("variables_loaded")
    return len(loaded) if isinstance(loaded, list) else 0


def current_school_effect(prediction: str | None, verdict: str) -> str:
    pred = (prediction or "").strip().lower()
    if verdict in {"inconclusive", "no_run", "partial", "mixed"} or pred == "mixed":
        return "pending_or_neutral"
    if pred == "falsified" and verdict == "supported":
        return "currently_refutes_school"
    if pred == "falsified" and verdict == "refuted":
        return "currently_supports_school"
    if pred == "supported" and verdict == "refuted":
        return "currently_refutes_school"
    if pred == "supported" and verdict == "supported":
        return "currently_supports_school"
    return "pending_or_neutral"


def stage(verdict: str, missing_count: int) -> str:
    if verdict in {"supported", "refuted"}:
        return "already_scored"
    if verdict in {"partial", "mixed"}:
        return "needs_strengthening_or_bespoke_rerun"
    if missing_count == 0:
        return "rerun_or_custom_diagnostics_needed"
    if missing_count <= 2:
        return "one_or_two_repairs_away"
    return "manual_or_multi_source_panel_needed"


def anti_target_status(school_effects: Counter[str]) -> str:
    refutes = school_effects.get("currently_refutes_school", 0)
    supports = school_effects.get("currently_supports_school", 0)
    pending = school_effects.get("pending_or_neutral", 0)
    if refutes and not supports:
        return "existing_refutation_win"
    if supports and not refutes:
        return "currently_cuts_against_refutation"
    if refutes and supports:
        return "mixed_current_effect"
    if pending:
        return "pending_clean_test"
    return "unclassified"


def target_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((ROOT / "hypotheses").glob("**/*.yaml")):
        if path.name.startswith("_"):
            continue
        spec = load_yaml(path)
        hid = str(spec.get("hypothesis_id") or path.stem)
        target_links = []
        for claim in spec.get("covers_claims") or []:
            if not isinstance(claim, dict):
                continue
            school = claim.get("position_id")
            prediction = str(claim.get("school_prediction") or "").lower()
            if school in TARGET_SCHOOLS and prediction == "falsified":
                target_links.append(
                    {
                        "school": school,
                        "claim_index": claim.get("claim_index"),
                        "prediction": prediction,
                    }
                )
        if not target_links:
            continue

        diagnostics_path = ROOT / "engine" / "runs" / hid / "diagnostics.json"
        diagnostics = load_json(diagnostics_path)
        verdict = verdict_bucket(
            diagnostics.get("verdict_label")
            or diagnostics.get("verdict_word")
            or diagnostics.get("verdict")
        )
        reported_missing_sources = missing_sources_from_diagnostics(diagnostics)
        resolved_missing_sources, unresolved_missing_sources = split_resolved_missing_sources(
            reported_missing_sources
        )
        loaded_count = loaded_count_from_diagnostics(diagnostics)
        school_effects = Counter(
            current_school_effect(link["prediction"], verdict) for link in target_links
        )
        record = {
            "hypothesis_id": hid,
            "path": str(path.relative_to(ROOT)),
            "topic": spec.get("topic"),
            "status": spec.get("status"),
            "target_school_count": len({link["school"] for link in target_links}),
            "target_schools": sorted({link["school"] for link in target_links}),
            "verdict_bucket": verdict,
            "stage": stage(verdict, len(unresolved_missing_sources)),
            "loaded_variable_count": loaded_count,
            "reported_missing_source_count": len(reported_missing_sources),
            "missing_source_count": len(unresolved_missing_sources),
            "missing_sources": unresolved_missing_sources,
            "resolved_since_last_run_count": len(resolved_missing_sources),
            "resolved_since_last_run_sources": resolved_missing_sources,
            "school_effects": dict(school_effects),
            "anti_target_status": anti_target_status(school_effects),
            "primary_pull": PRIMARY_PULLS.get(hid),
        }
        records.append(record)

    def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
        anti_rank = {
            "pending_clean_test": 0,
            "existing_refutation_win": 1,
            "mixed_current_effect": 2,
            "currently_cuts_against_refutation": 3,
            "unclassified": 4,
        }.get(str(row["anti_target_status"]), 9)
        stage_rank = {
            "one_or_two_repairs_away": 0,
            "rerun_or_custom_diagnostics_needed": 1,
            "manual_or_multi_source_panel_needed": 2,
            "needs_strengthening_or_bespoke_rerun": 3,
            "already_scored": 4,
        }.get(str(row["stage"]), 9)
        primary = 0 if row.get("primary_pull") else 1
        return (
            primary,
            anti_rank,
            stage_rank,
            -int(row["target_school_count"]),
            int(row["missing_source_count"]),
            TOPIC_PRIORITY.get(str(row.get("topic")), 99),
            str(row["hypothesis_id"]),
        )

    return sorted(records, key=sort_key)


def write_outputs(records: list[dict[str, Any]]) -> tuple[Path, Path]:
    audit_dir = ROOT / "engine" / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / "refutation_target_queue_2026-05-04.json"
    md_path = audit_dir / "refutation_target_queue_2026-05-04.md"

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target_schools": sorted(TARGET_SCHOOLS),
        "methodology": (
            "Ranks only pre-existing covers_claims links where school_prediction is "
            "falsified; does not change links, verdicts, scores, or mechanisms."
        ),
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    by_stage = Counter(row["stage"] for row in records)
    by_anti_status = Counter(row["anti_target_status"] for row in records)
    lines = [
        "# Refutation Target Queue",
        "",
        f"Generated: {payload['generated_utc']}",
        "",
        "This queue identifies hypotheses where target schools already have `school_prediction: falsified` links. It is for data repair and rerun prioritisation only; it does not alter verdicts, links, or scores.",
        "",
        "## Stage Counts",
        "",
    ]
    for key, value in by_stage.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Anti-Target Status Counts", ""])
    for key, value in by_anti_status.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Highest-Leverage Pulls",
            "",
            "| rank | hypothesis | anti-target status | stage | verdict | schools | missing | primary pull |",
            "|---:|---|---|---|---|---:|---:|---|",
        ]
    )
    for idx, row in enumerate(records[:60], start=1):
        lines.append(
            "| {idx} | `{hid}` | `{anti}` | `{stage}` | `{verdict}` | {schools} | {missing} | {pull} |".format(
                idx=idx,
                hid=row["hypothesis_id"],
                anti=row["anti_target_status"],
                stage=row["stage"],
                verdict=row["verdict_bucket"],
                schools=row["target_school_count"],
                missing=row["missing_source_count"],
                pull=row.get("primary_pull") or "",
            )
        )
    lines.extend(["", "## Top Missing Bundles", ""])
    missing_counter = Counter()
    for row in records:
        weight = max(1, int(row["target_school_count"]))
        for source in row["missing_sources"]:
            missing_counter[source] += weight
    for source, count in missing_counter.most_common(30):
        lines.append(f"- `{source}`: weighted linked-school blockers={count}")
    lines.extend(["", "## Method Notes", ""])
    lines.append("- Prioritise one/two-repair targets before manual multi-source panels.")
    lines.append("- Treat `already_scored` as a sanity-check bucket, not a prompt to rerun until data vintage or methodology changes.")
    lines.append("- For all subnational labour/housing tests, preserve `unit_id`; country-year collapse invalidates the estimand.")
    lines.append("- For CTC, Laeven-Valencia, and China renewables, current registered links are not anti-left refutation levers even when the data are useful.")
    md_path.write_text("\n".join(lines) + "\n")
    return md_path, json_path


def main() -> int:
    records = target_records()
    md_path, json_path = write_outputs(records)
    print(f"records={len(records)}")
    print(f"markdown={md_path.relative_to(ROOT)}")
    print(f"json={json_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
