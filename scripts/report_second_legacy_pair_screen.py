#!/usr/bin/env python3
"""Reproduce a metadata-only source-pair screen of 820 legacy hypotheses.

The fixed Git snapshot predates the second five-case preregistration batch.
This script reads only the review queue, registration index, and old YAML specs
from that commit. It never opens a candidate vintage or outcome value.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "19615241bdf76f630782e47eb19ca3dcedf50d23"
QUEUE_REL = "engine/audits/prospective_v2_500_review_queue_2026-10-09.json"
INDEX_REL = "engine/preregistration_index.json"
OUT_STEM = "engine/audits/second_legacy_panel_pair_screen_2026-10-09"
DECISIVE_OR_PARTIAL = {"supported", "partial", "refuted"}
RISK_BLOCKERS = frozenset({
    "missing_variables", "estimator_floor_failure",
    "integrity_or_correction_review", "falsification_rule_unsharpened",
    "few_panel_units_review", "small_panel_sample_review",
})


def git_bytes(relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative}"],
        cwd=ROOT, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"missing fixed-snapshot file: {relative}")
    return result.stdout


def source_set(spec: dict[str, Any], role: str) -> tuple[str, ...]:
    variables = spec.get("variables") or {}
    block = variables.get(role) or []
    return tuple(sorted({
        str(item["source"]) for item in block
        if isinstance(item, dict) and item.get("source")
    }))


def source_pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return source_set(spec, "treatment"), source_set(spec, "outcome")


def explicit_old_roster(spec: dict[str, Any]) -> tuple[str, ...] | None:
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    if not isinstance(countries, list) or len(countries) < 5:
        return None
    if not all(isinstance(code, str) and len(code) == 3 and code.isalpha()
               and code.isupper() for code in countries):
        return None
    if len(set(countries)) != len(countries):
        return None
    return tuple(sorted(countries))


def pair_id(pair: tuple[tuple[str, ...], tuple[str, ...]]) -> str:
    payload = json.dumps(
        {"treatment_sources": pair[0], "outcome_sources": pair[1]},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    return "pair_" + hashlib.sha256(payload).hexdigest()[:12]


def basic_reasons(row: dict[str, Any]) -> list[str]:
    reasons = []
    if row.get("old_estimator_template") != "panel_fe":
        reasons.append("template_not_panel_fe")
    if row.get("old_runner") != "scripts/run_panel_fe.py":
        reasons.append("runner_not_run_panel_fe")
    if row.get("old_result_bucket") not in DECISIVE_OR_PARTIAL:
        reasons.append("old_result_not_decisive_or_partial")
    for flag in sorted(set(row.get("review_flags") or []) & RISK_BLOCKERS):
        reasons.append("risk_flag:" + flag)
    return reasons


def build() -> dict[str, Any]:
    queue_bytes = git_bytes(QUEUE_REL)
    index_bytes = git_bytes(INDEX_REL)
    queue = json.loads(queue_bytes)
    registrations = json.loads(index_bytes)["registrations"]
    if len(queue["cases"]) != 1320 or len(registrations) != 1938:
        raise AssertionError("fixed-snapshot population changed")
    cases = [row for row in queue["cases"] if row["review_rank"] > 500]
    if len(cases) != 820:
        raise AssertionError("fixed-snapshot remainder must contain 820 old cases")

    spec_cache: dict[str, dict[str, Any]] = {}
    spec_blob_cache: dict[str, bytes] = {}
    def spec_blob(relative: str) -> bytes:
        if relative not in spec_blob_cache:
            spec_blob_cache[relative] = git_bytes(relative)
        return spec_blob_cache[relative]

    def spec_at(relative: str) -> dict[str, Any]:
        if relative not in spec_cache:
            parsed = yaml.safe_load(spec_blob(relative)) or {}
            if not isinstance(parsed, dict):
                raise ValueError(f"invalid historical spec: {relative}")
            spec_cache[relative] = parsed
        return spec_cache[relative]

    strict_by_pair: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = defaultdict(list)
    for hypothesis_id, registration in registrations.items():
        if registration.get("status") != "verified":
            continue
        pair = source_pair(spec_at(registration["path"]))
        strict_by_pair[pair].append(hypothesis_id)
    for ids in strict_by_pair.values():
        ids.sort()

    processed = []
    basic_count = 0
    explicit_count = 0
    groups_before_strict: dict[tuple[tuple[str, ...], tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
    for row in cases:
        spec_rel = row["spec_path"]
        spec = spec_at(spec_rel)
        roster = explicit_old_roster(spec)
        pair = source_pair(spec)
        reasons = basic_reasons(row)
        if not reasons:
            basic_count += 1
            if roster is None:
                reasons.append("old_country_roster_not_explicit_iso3")
            elif not pair[0] or not pair[1]:
                reasons.append("empty_treatment_or_outcome_source")
            else:
                explicit_count += 1
                groups_before_strict[pair].append(row)
        processed.append({
            "review_rank": row["review_rank"],
            "old_hypothesis_id": row["hypothesis_id"],
            "spec_path": spec_rel,
            "spec_sha256": hashlib.sha256(spec_blob(spec_rel)).hexdigest(),
            "topic": row["topic"],
            "old_status": row["old_spec_status"],
            "old_result_bucket": row["old_result_bucket"],
            "old_estimator_template": row["old_estimator_template"],
            "old_runner": row["old_runner"],
            "old_n_obs": row["old_n_obs"],
            "old_n_units": row["old_n_units"],
            "review_flags": sorted(row.get("review_flags") or []),
            "old_country_roster": list(roster) if roster is not None else None,
            "old_country_roster_count": len(roster) if roster is not None else None,
            "treatment_sources": list(pair[0]),
            "outcome_sources": list(pair[1]),
            "pair_id": pair_id(pair),
            "exclusion_reasons": reasons,
            "exact_strict_pair_ids": [],
            "disposition": None,
            "pair_representative_id": None,
        })

    by_id = {row["old_hypothesis_id"]: row for row in processed}
    retained_groups = []
    exact_strict_groups = 0
    exact_strict_cases = 0
    for pair, old_rows in sorted(groups_before_strict.items(), key=lambda item: pair_id(item[0])):
        prior_ids = strict_by_pair.get(pair, [])
        ranked = sorted(old_rows, key=lambda row: (row["review_rank"], row["hypothesis_id"]))
        representative = ranked[0]["hypothesis_id"]
        if prior_ids:
            exact_strict_groups += 1
            exact_strict_cases += len(ranked)
            for old in ranked:
                case = by_id[old["hypothesis_id"]]
                case["exact_strict_pair_ids"] = prior_ids
                case["exclusion_reasons"].append("exact_pair_already_in_strict_registration")
                case["disposition"] = "excluded_existing_exact_pair"
                case["pair_representative_id"] = representative
            continue
        for old in ranked:
            case = by_id[old["hypothesis_id"]]
            case["pair_representative_id"] = representative
            case["disposition"] = (
                "screened_pair_representative" if old["hypothesis_id"] == representative
                else "grouped_duplicate_old_source_pair"
            )
        retained_groups.append({
            "pair_id": pair_id(pair),
            "treatment_sources": list(pair[0]),
            "outcome_sources": list(pair[1]),
            "representative_old_id": representative,
            "old_ids": [old["hypothesis_id"] for old in ranked],
            "old_review_ranks": [old["review_rank"] for old in ranked],
            "old_result_buckets": [old["old_result_bucket"] for old in ranked],
            "old_roster_counts": [by_id[old["hypothesis_id"]]["old_country_roster_count"]
                                  for old in ranked],
            "old_review_flags": sorted({
                flag for old in ranked for flag in old.get("review_flags") or []
            }),
            "existing_exact_strict_pair_ids": [],
            "screening_only": True,
            "new_graduations_created": 0,
        })

    for case in processed:
        if case["disposition"] is None:
            case["disposition"] = "excluded_pre_pair_screen"
    retained_old_cases = sum(len(group["old_ids"]) for group in retained_groups)
    duplicates_grouped = retained_old_cases - len(retained_groups)
    reason_counts = Counter(
        reason for case in processed for reason in case["exclusion_reasons"]
    )
    retained_flag_counts = Counter(
        flag for group in retained_groups for flag in group["old_review_flags"]
    )
    report = {
        "schema": "ieset-second-legacy-panel-pair-screen-v1",
        "as_of": "2026-10-09",
        "snapshot_commit": BASELINE_COMMIT,
        "input_sha256": {
            QUEUE_REL: hashlib.sha256(queue_bytes).hexdigest(),
            INDEX_REL: hashlib.sha256(index_bytes).hexdigest(),
        },
        "purpose": (
            "A reproducible metadata-only screen of legacy cases ranked 501-1320. "
            "It is neither a preregistration nor a result or graduation."
        ),
        "status": {
            "screening_only": True,
            "new_preregistrations_created": 0,
            "new_runs_created": 0,
            "new_graduations_created": 0,
            "tracks_subsequent_v2_results": False,
        },
        "selection_rule": [
            "Use only queue rows ranked above 500 in the fixed snapshot.",
            "Require old panel_fe template, scripts/run_panel_fe.py, and an old supported, partial, or refuted bucket.",
            "Exclude recorded missing-variable, estimator-floor, integrity, fuzzy-rule, and small/few-unit flags.",
            "Require an explicit old spec roster of at least five unique uppercase ISO3 country codes.",
            "Group exact treatment-source and outcome-source string sets; exclude groups already present in a baseline verified strict registration.",
            "Count each remaining source pair once. No held-out outcome value, null mask, coefficient, or candidate fit is read.",
        ],
        "summary": {
            "legacy_remainder": len(cases),
            "basic_panel_records": basic_count,
            "explicit_old_roster_records": explicit_count,
            "unique_pairs_before_strict_overlap": len(groups_before_strict),
            "existing_exact_strict_pair_groups": exact_strict_groups,
            "existing_exact_strict_pair_old_records": exact_strict_cases,
            "screened_distinct_source_pairs_upper_bound": len(retained_groups),
            "screened_old_records_in_those_pairs": retained_old_cases,
            "grouped_duplicate_old_records": duplicates_grouped,
            "simple_one_treatment_one_outcome_source_pairs": sum(
                len(group["treatment_sources"]) == len(group["outcome_sources"]) == 1
                for group in retained_groups
            ),
        },
        "exclusion_reason_counts_overlapping": dict(sorted(reason_counts.items())),
        "retained_group_review_flag_counts_overlapping": dict(sorted(retained_flag_counts.items())),
        "caveats": [
            "67 exact source-string pairs are a screening upper bound, not 67 ready studies or graduations.",
            "A shared indicator under different aliases may still be a semantic duplicate; exact string matching does not settle this.",
            "An explicit old spec roster is not per-case historical fitted-row proof; each selected old run still needs a source and historical-runner audit.",
            "Many old records carry screening, proxy-design, missing-manifest, or missing-packet warnings even when they pass this coarse screen.",
            "Fresh v2 designs need narrowed direct claims, genuine unused holdouts, old-result disclosure, preregistration before outcome values, correction across tested families, exact replay, and no automatic school credit.",
            "This fixed snapshot precedes the separately committed five-case geographic-holdout batch and does not track later registrations or runs.",
        ],
        "groups": retained_groups,
        "cases": processed,
    }
    assert report["summary"]["basic_panel_records"] == 166
    assert report["summary"]["explicit_old_roster_records"] == 100
    assert report["summary"]["unique_pairs_before_strict_overlap"] == 78
    assert report["summary"]["existing_exact_strict_pair_groups"] == 11
    assert report["summary"]["existing_exact_strict_pair_old_records"] == 12
    assert report["summary"]["screened_distinct_source_pairs_upper_bound"] == 67
    assert report["summary"]["screened_old_records_in_those_pairs"] == 88
    assert report["summary"]["grouped_duplicate_old_records"] == 21
    assert report["summary"]["simple_one_treatment_one_outcome_source_pairs"] == 54
    return report


def markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Second-wave legacy panel source-pair screen",
        "",
        "Date: 2026-10-09. Fixed queue and preregistration snapshot: " + BASELINE_COMMIT + ".",
        "",
        "**Screening only. This report creates zero preregistrations, runs, or graduations.** "
        "Its 67 exact source-string pairs are an upper bound for manual design review, "
        "not 67 approved studies. Current graduation totals are in the conversion funnel.",
        "",
        "The script reads the fixed review queue, index, and old spec metadata from Git. "
        "It does not open candidate data vintages, outcome values, null masks, or estimates. "
        "The separate five-case preregistration batch came later than this fixed snapshot.",
        "",
        "## Funnel",
        "",
        "| Screen | Count |",
        "| --- | ---: |",
        f"| Legacy cases beyond first 500 | {summary['legacy_remainder']} |",
        f"| Basic panel records | {summary['basic_panel_records']} |",
        f"| Explicit old ISO3 rosters | {summary['explicit_old_roster_records']} |",
        f"| Distinct exact source pairs before strict overlap | {summary['unique_pairs_before_strict_overlap']} |",
        f"| Pairs already in baseline strict registrations | {summary['existing_exact_strict_pair_groups']} |",
        f"| Remaining exact source-pair groups | {summary['screened_distinct_source_pairs_upper_bound']} |",
        f"| Old records within remaining groups | {summary['screened_old_records_in_those_pairs']} |",
        f"| Duplicate old records grouped with a representative | {summary['grouped_duplicate_old_records']} |",
        f"| Single-treatment/single-outcome source groups | {summary['simple_one_treatment_one_outcome_source_pairs']} |",
        "",
        "## Exclusion reasons",
        "",
        "Counts overlap because one old case can fail several checks. Exact reasons for "
        "all 820 old IDs are in the companion CSV and JSON.",
        "",
        "| Reason | Old records |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {reason} | {count} |"
        for reason, count in report["exclusion_reason_counts_overlapping"].items()
    )
    lines += [
        "",
        "## Review flags within the 67 retained groups",
        "",
        "These flags are not cleared by pair screening.",
        "",
        "| Existing old-record flag | Pair groups |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {flag} | {count} |"
        for flag, count in report["retained_group_review_flag_counts_overlapping"].items()
    )
    lines += [
        "",
        "## All 67 exact source-pair groups",
        "",
        "The first old ID in each group is a deterministic review representative, "
        "not a preferred result. Multiple old IDs in one row share the same exact "
        "treatment/outcome source sets and count once.",
        "",
        "| Group | Treatment source set | Outcome source set | Old IDs (representative first) |",
        "| --- | --- | --- | --- |",
    ]
    for group in report["groups"]:
        treatment = " + ".join(group["treatment_sources"])
        outcome = " + ".join(group["outcome_sources"])
        old_ids = ", ".join(group["old_ids"])
        lines.append(f"| {group['pair_id']} | {treatment} | {outcome} | {old_ids} |")
    lines += [
        "",
        "## Interpretation limits and next step",
        "",
    ]
    lines.extend("- " + caveat for caveat in report["caveats"])
    lines += [
        "",
        "For each group, audit the old fitted-country boundary and source semantics, "
        "remove substantive duplicates and weak proxies, then write a narrower "
        "new-ID preregistration with a genuine holdout before inspecting candidate "
        "outcome values. A result needs exact replay and evidence-tier review before "
        "it counts as a graduation.",
        "",
    ]
    return "\n".join(lines)


def csv_text(report: dict[str, Any]) -> str:
    fields = [
        "review_rank", "old_hypothesis_id", "topic", "old_result_bucket",
        "old_estimator_template", "old_runner", "old_n_obs", "old_n_units",
        "old_country_roster_count", "treatment_sources", "outcome_sources",
        "pair_id", "pair_representative_id", "disposition", "exclusion_reasons",
        "exact_strict_pair_ids", "review_flags", "spec_path", "spec_sha256",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for case in report["cases"]:
        row = {key: case.get(key) for key in fields}
        for key in ("treatment_sources", "outcome_sources", "exclusion_reasons",
                    "exact_strict_pair_ids", "review_flags"):
            row[key] = " | ".join(row[key] or [])
        writer.writerow(row)
    return stream.getvalue()


def outputs(report: dict[str, Any]) -> dict[Path, bytes]:
    return {
        ROOT / (OUT_STEM + ".json"): (json.dumps(report, indent=2, sort_keys=True) + "\n").encode(),
        ROOT / (OUT_STEM + ".md"): markdown(report).encode(),
        ROOT / (OUT_STEM + ".csv"): csv_text(report).encode(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build()
    files = outputs(report)
    if args.check:
        for path, expected in files.items():
            if not path.is_file() or path.read_bytes() != expected:
                raise SystemExit(f"stale or missing report: {path.relative_to(ROOT)}")
    else:
        for path, content in files.items():
            path.write_bytes(content)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
