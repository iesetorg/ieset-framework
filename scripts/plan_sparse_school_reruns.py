#!/usr/bin/env python3
"""Build a conservative rerun cohort for the sparsest scoreboard schools.

METHODOLOGY.md defines registration as a hypothesis file committed before its
first run. This queue retains those timing-verified archives, then records the
YAML lifecycle status before the run as an additional design-readiness signal.
No saved verdict or verified timestamp makes an archived run score-ready.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPARSE_SCHOOLS = (
    "social_democratic",
    "democratic_socialist",
    "post_keynesian",
    "mmt",
    "new_keynesian",
    "degrowth",
    "market_socialist",
    "marxian",
    "marxist_leninist",
    "eco_socialist",
)
FROZEN_FIELDS = (
    "claim", "evidence_type", "sample", "variables", "estimator",
    "falsification", "prior_confidence",
)
DIRECTIONAL_TARGET = 200
INTACT_CASE_NOTES = {
    "judicial_independence_growth_persistence": (
        "The saved fallback does not load the registered V-Dem judicial composite or v2x_jucon; "
        "acquire those inputs and fit the frozen primary model."
    ),
    "labour_flexibility_security_complement": (
        "The saved fallback lacks OECD EPL and union-density inputs and does not test the "
        "registered security interaction."
    ),
    "oecd_pdb_hours_reduction_output_tradeoff_panel": (
        "The frozen hours-growth coefficient and support gate have the wrong sign for the English "
        "no-output-loss claim. Keep v1 quarantined; a new ID needs a signed equivalence or "
        "noninferiority estimand and independent holdout."
    ),
    "corruption_state_allocation_growth_interaction": (
        "The design is unchanged, but the external integrity hold requires source and result custody review."
    ),
    "government_consumption_share_tfp": (
        "The design is unchanged, but the external integrity hold requires source and result custody review."
    ),
    "unemployment_benefit_generosity_employment_drag": (
        "First committed as pre_registered. Later country-list deduplication did not change "
        "the frozen sample; its saved run remains externally quarantined. Replay the full "
        "original rule with claim-matched sources before judging feasibility."
    ),
    "workfare_conditionality_employment_effect": (
        "First committed as pre_registered. Later country-list deduplication did not change "
        "the frozen sample; its saved run remains externally quarantined. Replay the full "
        "original rule with claim-matched sources before judging feasibility."
    ),
}


def comparable_sample(value: Any) -> Any:
    """Country-list duplicates do not alter a panel's selected country set."""
    if not isinstance(value, dict):
        return value
    sample = dict(value)
    countries = sample.get("countries")
    if isinstance(countries, list) and all(isinstance(code, str) for code in countries):
        sample["countries"] = sorted(set(countries))
    return sample


def frozen_spec_drift(root: Path, registration: dict[str, Any]) -> list[str]:
    """Compare scoring-relevant fields with the original committed v1 spec."""
    revision = registration["spec_commit"]
    path = registration["path"]
    try:
        frozen_bytes = subprocess.check_output(
            ["git", "show", f"{revision}:{path}"], cwd=root, stderr=subprocess.DEVNULL
        )
        frozen = yaml.safe_load(frozen_bytes) or {}
        current = yaml.safe_load((root / path).read_text()) or {}
    except (OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot verify original specification {revision}:{path}") from exc
    return [
        field for field in FROZEN_FIELDS
        if (
            comparable_sample(frozen.get(field)) != comparable_sample(current.get(field))
            if field == "sample" else frozen.get(field) != current.get(field)
        )
    ]


def timing_verified(registration: dict[str, Any]) -> bool:
    if registration.get("status") != "verified" or registration.get("verified") is not True:
        return False
    if not registration.get("spec_commit") or not registration.get("run_first_commit"):
        return False
    try:
        spec_time = datetime.fromisoformat(registration["spec_committed_at"])
        run_time = datetime.fromisoformat(registration["run_committed_at"])
    except (KeyError, TypeError, ValueError):
        return False
    return spec_time < run_time and registration["spec_commit"] != registration["run_first_commit"]


def before_run_spec_status(root: Path, registration: dict[str, Any]) -> str:
    """Read the actual YAML status in the parent tree of the first run commit."""
    path = registration["path"]
    revision = registration["run_first_commit"] + "^"
    try:
        spec_bytes = subprocess.check_output(
            ["git", "show", f"{revision}:{path}"], cwd=root, stderr=subprocess.DEVNULL
        )
        spec = yaml.safe_load(spec_bytes) or {}
    except (OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot verify pre-run YAML status {revision}:{path}") from exc
    return str(spec.get("status") or "missing_status")


def build_cohort(
    queue_rows: list[dict[str, str]],
    registrations: dict[str, dict[str, Any]],
    *,
    root: Path = ROOT,
    schools: tuple[str, ...] = SPARSE_SCHOOLS,
    coverage_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    selected: dict[str, dict[str, Any]] = {}
    status_cache: dict[str, str] = {}
    schools_set = set(schools)
    for row in queue_rows:
        school = row["position_id"]
        if school not in schools_set:
            continue
        if row["registration_status"] != "verified" or row["evidence_tier"] != "archive":
            continue
        if row["prediction"] not in {"supported", "falsified"}:
            continue
        hypothesis_id = row["hypothesis_id"]
        registration = registrations.get(hypothesis_id) or {}
        if not timing_verified(registration):
            continue
        if hypothesis_id not in status_cache:
            status_cache[hypothesis_id] = before_run_spec_status(root, registration)
        before_run_status = status_cache[hypothesis_id]
        blockers = set(filter(None, row["blockers"].split(";")))
        if not blockers:
            raise ValueError(f"archived queue row lacks a public-gate blocker: {hypothesis_id}")
        entry = selected.setdefault(hypothesis_id, {
            "hypothesis_id": hypothesis_id,
            "status_before_first_run": before_run_status,
            "explicit_preregistered_status": before_run_status == "pre_registered",
            "school_links": set(),
            "blockers": set(),
            "first_spec_commit": registration["spec_commit"],
            "first_run_commit": registration["run_first_commit"],
            "spec_path": registration["path"],
        })
        entry["school_links"].add(school)
        entry["blockers"].update(blockers)

    for hypothesis_id, entry in selected.items():
        drift = frozen_spec_drift(root, registrations[hypothesis_id])
        blockers = sorted(entry["blockers"])
        if drift:
            next_action = "review_first_committed_spec_or_register_new_id"
        elif "audit_quarantined_pending_v2" in blockers:
            next_action = "independent_v2_review"
        elif "external_integrity_quarantine" in blockers:
            next_action = "integrity_source_review"
        else:
            next_action = "source_and_full_rule_estimator_repair"
        entry.update({
            "school_links": sorted(entry["school_links"]),
            "blockers": blockers,
            "frozen_field_drift": drift,
            "next_action": next_action,
            "case_repair_note": INTACT_CASE_NOTES.get(hypothesis_id),
            "ready_to_score": False,
            "estimated_score_gain_now": 0,
        })

    candidates = sorted(selected.values(), key=lambda row: row["hypothesis_id"])
    by_school: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        for school in candidate["school_links"]:
            by_school[school].append(candidate)
    coverage_by_school = {
        row["position_id"]: row for row in (coverage_rows or [])
    }
    school_rows = []
    for school in schools:
        items = by_school[school]
        coverage = coverage_by_school.get(school) or {}
        current_directional = coverage.get("unique_directional_scored")
        school_rows.append({
            "position_id": school,
            "current_directional_scored": current_directional,
            "timing_verified_archived_directional_links": len(items),
            "explicit_preregistered_status_links": sum(item["explicit_preregistered_status"] for item in items),
            "upper_bound_if_cohort_clears": (
                current_directional + len(items) if current_directional is not None else None
            ),
            "gap_after_cohort_upper_bound": (
                max(0, DIRECTIONAL_TARGET - current_directional - len(items))
                if current_directional is not None else None
            ),
            "intact_frozen_designs": sum(not item["frozen_field_drift"] for item in items),
            "changed_since_first_registration": sum(bool(item["frozen_field_drift"]) for item in items),
            "blocked_by_estimator_floor": sum("estimator_floor_failed" in item["blockers"] for item in items),
            "blocked_by_integrity_quarantine": sum("external_integrity_quarantine" in item["blockers"] for item in items),
            "blocked_by_v2_quarantine": sum("audit_quarantined_pending_v2" in item["blockers"] for item in items),
            "ready_to_score": 0,
            "hypothesis_ids": [item["hypothesis_id"] for item in items],
        })
    return {
        "generated_at": date.today().isoformat(),
        "methodology": {
            "source": "public-gated directional school queue plus Git pre-run YAML status and preregistration index",
            "selection": "Index-verified file-before-run timing per METHODOLOGY.md; archived tier; directional school prediction; named sparse school. YAML status is recorded as a separate quality signal, not a repository registration gate.",
            "boundary": "Every candidate remains archived. Original v1 fields must be replayed or a new ID preregistered before a fresh holdout; no saved verdict supplies score credit.",
        },
        "summary": {
            "schools": len(schools),
            "unique_candidates": len(candidates),
            "school_links": sum(len(item["school_links"]) for item in candidates),
            "explicit_preregistered_status": sum(item["explicit_preregistered_status"] for item in candidates),
            "explicit_preregistered_status_school_links": sum(
                len(item["school_links"]) for item in candidates if item["explicit_preregistered_status"]
            ),
            "draft_or_candidate_status_before_run": sum(
                not item["explicit_preregistered_status"] for item in candidates
            ),
            "intact_frozen_designs": sum(not item["frozen_field_drift"] for item in candidates),
            "changed_since_first_registration": sum(bool(item["frozen_field_drift"]) for item in candidates),
            "ready_to_score": 0,
            "blockers": dict(sorted(Counter(
                blocker for item in candidates for blocker in item["blockers"]
            ).items())),
        },
        "schools": school_rows,
        "candidates": candidates,
    }


def write_outputs(cohort: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(cohort, indent=2, sort_keys=True) + "\n")
    summary = cohort["summary"]
    lines = [
        f"# Sparse-school registered rerun cohort — {cohort['generated_at']}",
        "",
        "This is a **blocked engineering queue**, not a conversion or an increase in tested school coverage. "
        "METHODOLOGY.md defines registration as a hypothesis file committed before its first run; this queue follows that rule, "
        "then separately records whether its YAML status was explicitly `pre_registered` at that time. "
        "It checks scoring-relevant current fields against the original committed specification.",
        "",
        f"**{summary['unique_candidates']} timing-verified hypotheses / {summary['school_links']} school links / "
        f"{summary['ready_to_score']} ready to score.** "
        f"Only {summary['explicit_preregistered_status']} studies / "
        f"{summary['explicit_preregistered_status_school_links']} school links had explicit "
        "`pre_registered` status before running; the others were draft or candidate and need design-completeness review. "
        f"{summary['intact_frozen_designs']} retain an intact frozen design; "
        f"{summary['changed_since_first_registration']} changed scoring-relevant fields after first registration.",
        "",
        "| School | Directional scored now | Timing-verified rerun queue | Explicit prereg status | If queued cases later clear | Remaining to 200 | Ready now |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in cohort["schools"]:
        def display(value: int | None) -> str:
            return "n/a" if value is None else str(value)
        lines.append(
            f"| `{row['position_id']}` | {display(row['current_directional_scored'])} | "
            f"{row['timing_verified_archived_directional_links']} | "
            f"{row['explicit_preregistered_status_links']} | "
            f"{display(row['upper_bound_if_cohort_clears'])} | "
            f"{display(row['gap_after_cohort_upper_bound'])} | 0 |"
        )
    lines.extend(["", "## Case actions", "",
                  "| Hypothesis | Status before run | Schools | Original-spec drift | Current public blocker | Next action |",
                  "| --- | --- | --- | --- | --- | --- |"])
    for item in cohort["candidates"]:
        lines.append(
            f"| `{item['hypothesis_id']}` | `{item['status_before_first_run']}` | "
            f"{', '.join(item['school_links'])} | "
            f"{', '.join(item['frozen_field_drift']) or 'none'} | "
            f"{', '.join(item['blockers'])} | `{item['next_action']}` |"
        )
    lines.extend(["", "## Case-specific repair screens", ""])
    for item in cohort["candidates"]:
        if item["case_repair_note"]:
            lines.append(f"- `{item['hypothesis_id']}`: {item['case_repair_note']}")
    lines.extend([
        "", "## Gates before any claim can score", "",
        "1. Review the first committed spec for a complete frozen design. Replay that design if valid, or commit a new ID and independent holdout. Changed current fields are not retroactive preregistration.",
        "2. Obtain the declared source vintage and construct claim-matched variables. Reject generic GDP/EFW fallback regressions and estimator warnings.",
        "3. Execute the full frozen falsification rule with replication, then rebuild the evidence-tier ledger and school audit. Resolve every integrity/quarantine hold before publication.",
        "4. Add genuinely new school-specific claims for gaps this cohort cannot fill, especially Degrowth, only after their data and future holdout contracts are specified.",
        "", f"The {summary['school_links']} queued school links are overlapping predictions about "
        f"{summary['unique_candidates']} studies, not independent studies. "
        "Even if all later pass, each school remains far short of 200 directional scored tests.", "",
    ])
    output.with_suffix(".md").write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=ROOT / "engine" / "audits" / f"school_coverage_balance_{date.today().isoformat()}.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "engine" / "audits" / f"sparse_school_strict_rerun_cohort_{date.today().isoformat()}")
    args = parser.parse_args()
    with args.queue.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    registrations = json.loads((ROOT / "engine" / "preregistration_index.json").read_text())["registrations"]
    coverage_path = args.queue.with_suffix(".json")
    coverage_rows = json.loads(coverage_path.read_text())["schools"]
    cohort = build_cohort(rows, registrations, coverage_rows=coverage_rows)
    write_outputs(cohort, args.output)
    print(json.dumps(cohort["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
