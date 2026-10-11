#!/usr/bin/env python3
"""Audit the authored coverage behind the country drift maps.

This is a review queue, not a movement generator. It counts plotted movement
coverage, distinguishes other authored movement records, and points to existing
dated policy records that merit source review. It never infers a movement from a
policy or treats an interval labelled ``ongoing`` as proof of annual policy
activity.

Run from any directory::

    python3 scripts/audit_country_drift_coverage.py --as-of-year 2026

The report is deterministic for a fixed corpus and as-of year. No generation
timestamp is embedded in either output.
"""

from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "engine/audits/country_drift_coverage.json"
OUT_MD = REPO / "engine/audits/country_drift_coverage.md"
DEFUNCT_ISOS = {"CSK", "SUN", "YUG"}
LOW_COUNT_MAX = 2


def is_year(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def load_specs(folder: str, id_key: str) -> list[dict[str, Any]]:
    """Load all valid-shaped top-level specs; fail on malformed authored specs."""
    records = []
    seen = set()
    for path in sorted((REPO / folder).glob("*.yaml")):
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Cannot parse {path.relative_to(REPO)}: {exc}") from exc
        if not isinstance(document, dict) or not document.get(id_key):
            continue
        spec_id = document[id_key]
        if spec_id in seen:
            raise ValueError(f"Duplicate {id_key}: {spec_id}")
        seen.add(spec_id)
        timeframe = document.get("timeframe") or {}
        if not is_year(timeframe.get("start")) or not document.get("countries"):
            raise ValueError(f"Missing year or countries in {path.relative_to(REPO)}")
        document["_source_file"] = str(path.relative_to(REPO))
        records.append(document)
    return records


def is_plotted(movement: dict[str, Any]) -> bool:
    """Match compute_country_drift.py's country-level inclusion rule."""
    return (
        movement.get("scope", "national") != "subnational"
        and movement.get("country_drift_role") != "context_only"
    )


def end_year(record: dict[str, Any], as_of_year: int) -> int:
    start = record["timeframe"]["start"]
    raw = record["timeframe"].get("end")
    if raw in (None, "ongoing", "present"):
        return as_of_year
    if not is_year(raw) or raw < start:
        raise ValueError(f"Invalid timeframe end for {record.get('movement_id') or record.get('policy_id')}")
    return min(raw, as_of_year)


def spans_for(movements: list[dict[str, Any]], as_of_year: int) -> list[tuple[int, int]]:
    return sorted(
        (m["timeframe"]["start"], end_year(m, as_of_year))
        for m in movements
        if m["timeframe"]["start"] <= as_of_year
    )


def merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def gap_rows(merged: list[tuple[int, int]]) -> list[dict[str, int]]:
    return [
        {"from_year": earlier[1] + 1, "through_year": later[0] - 1,
         "years": later[0] - earlier[1] - 1}
        for earlier, later in zip(merged, merged[1:])
    ]


def policy_year(policy: dict[str, Any]) -> tuple[int, str]:
    date = policy["timeframe"].get("enacted_date")
    if date is not None:
        date_text = str(date)
        if len(date_text) >= 4 and date_text[:4].isdigit():
            return int(date_text[:4]), "enacted_date"
    return policy["timeframe"]["start"], "timeframe.start_proxy"


def report_for(
    movements: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    as_of_year: int,
) -> dict[str, Any]:
    if as_of_year < 1800 or as_of_year > 2100:
        raise ValueError("as-of year must be between 1800 and 2100")

    authored_by_country: dict[str, list[dict[str, Any]]] = defaultdict(list)
    plotted_by_country: dict[str, list[dict[str, Any]]] = defaultdict(list)
    movement_by_id = {m["movement_id"]: m for m in movements}
    for movement in movements:
        for country in movement["countries"]:
            authored_by_country[country].append(movement)
            if is_plotted(movement) and movement["timeframe"]["start"] <= as_of_year:
                plotted_by_country[country].append(movement)

    authored_country_codes = set(authored_by_country)
    policy_countries = {country for policy in policies for country in policy["countries"]}
    all_countries = sorted(authored_country_codes | policy_countries)
    countries: dict[str, dict[str, Any]] = {}
    for country in all_countries:
        authored = sorted(authored_by_country.get(country, []), key=lambda m: (m["timeframe"]["start"], m["movement_id"]))
        plotted = sorted(plotted_by_country.get(country, []), key=lambda m: (m["timeframe"]["start"], m["movement_id"]))
        merged = merge_spans(spans_for(plotted, as_of_year))
        step_years = [m["timeframe"]["start"] for m in plotted]
        step_years.extend(
            entry["drift_attribution_year"]
            for movement in plotted
            for entry in movement.get("axes_summary") or []
            if is_year(entry.get("drift_attribution_year"))
            and entry["drift_attribution_year"] <= as_of_year
        )
        last_covered_year = merged[-1][1] if merged else None
        current_expected = country not in DEFUNCT_ISOS
        countries[country] = {
            "authored_movement_count": len(authored),
            "plotted_movement_count": len(plotted),
            "context_only_movement_count": sum(m.get("country_drift_role") == "context_only" for m in authored),
            "subnational_movement_count": sum(m.get("scope") == "subnational" for m in authored),
            "first_coded_year": min(step_years) if step_years else None,
            "last_coded_year": max(step_years) if step_years else None,
            "last_movement_start_year": max((m["timeframe"]["start"] for m in plotted), default=None),
            "last_covered_year": last_covered_year,
            "current_coverage_expected": current_expected,
            "missing_current_coverage": current_expected and (last_covered_year is None or last_covered_year < as_of_year),
            "internal_gaps": gap_rows(merged),
            "plotted_movement_ids": [m["movement_id"] for m in plotted],
        }

    candidate_policy_leads = []
    for policy in sorted(policies, key=lambda p: p["policy_id"]):
        if policy.get("scope", "national") == "subnational":
            continue
        year, date_basis = policy_year(policy)
        if year > as_of_year:
            continue
        for country in sorted(set(policy["countries"])):
            plotted = plotted_by_country.get(country, [])
            merged = merge_spans(spans_for(plotted, as_of_year))
            reasons = []
            if not merged:
                reasons.append("no_plotted_movement")
            elif year < merged[0][0]:
                reasons.append("before_first_coded_year")
            elif year > merged[-1][1]:
                reasons.append("after_last_covered_year")
            elif not any(start <= year <= end for start, end in merged):
                reasons.append("internal_uncovered_year")

            linked = [
                movement_by_id[mid] for mid in policy.get("enacted_by") or []
                if mid in movement_by_id and country in movement_by_id[mid]["countries"]
            ]
            linked_in_year = [
                movement for movement in linked
                if movement["timeframe"]["start"] <= year <= end_year(movement, as_of_year)
            ]
            if linked and not linked_in_year:
                reasons.append("enactor_timeframe_mismatch")
            if linked and not any(is_plotted(m) for m in linked):
                if not any(policy["policy_id"] in (m.get("policies") or []) for m in plotted):
                    reasons.append("linked_only_to_nonplotted_movement")
            if not reasons:
                continue
            candidate_policy_leads.append({
                "country": country,
                "policy_id": policy["policy_id"],
                "title": policy.get("title") or policy["policy_id"],
                "policy_year": year,
                "date_basis": date_basis,
                "scope": policy.get("scope", "national"),
                "status": policy.get("status"),
                "source_file": policy["_source_file"],
                "linked_movement_ids": [m["movement_id"] for m in linked],
                "review_reasons": reasons,
            })
    candidate_policy_leads.sort(key=lambda row: (row["country"], row["policy_year"], row["policy_id"]))

    overlapping_pairs = 0
    overlapping_both_plotted_pairs = 0
    overlap_shared_policy_candidates = []
    for country in sorted(authored_by_country):
        candidates = [
            m for m in authored_by_country[country]
            if m.get("scope", "national") != "subnational"
            and m["timeframe"]["start"] <= as_of_year
        ]
        for left, right in itertools.combinations(candidates, 2):
            overlap_start = max(left["timeframe"]["start"], right["timeframe"]["start"])
            overlap_end = min(end_year(left, as_of_year), end_year(right, as_of_year))
            if overlap_start > overlap_end:
                continue
            overlapping_pairs += 1
            both_plotted = is_plotted(left) and is_plotted(right)
            if both_plotted:
                overlapping_both_plotted_pairs += 1
            shared = sorted(set(left.get("policies") or []) & set(right.get("policies") or []))
            if not shared:
                continue
            pair = sorted((left, right), key=lambda m: m["movement_id"])
            overlap_shared_policy_candidates.append({
                "country": country,
                "movement_ids": [m["movement_id"] for m in pair],
                "movement_source_files": [m["_source_file"] for m in pair],
                "plotted_in_drift": [is_plotted(m) for m in pair],
                "both_plotted_in_drift": both_plotted,
                "overlap_from_year": overlap_start,
                "overlap_through_year": overlap_end,
                "shared_policy_ids": shared,
            })
    overlap_shared_policy_candidates.sort(
        key=lambda row: (row["country"], row["overlap_from_year"], row["movement_ids"])
    )

    # A supranational record's countries list is an authored geographic sample,
    # not a verified inventory of every country where the instrument applies.
    # Keep this review queue explicit rather than silently extrapolating it.
    eu_geographic_scope_review = [
        {
            "movement_id": movement["movement_id"],
            "source_file": movement["_source_file"],
            "declared_country_count": len(movement["countries"]),
            "declared_countries": sorted(movement["countries"]),
            "plotted_in_drift": is_plotted(movement),
            "review_reason": "EU supranational movement uses an authored country list; check country applicability and historical membership before extending coverage.",
        }
        for movement in movements
        if movement.get("scope") == "supranational"
        and movement["movement_id"].startswith("eu_")
    ]
    eu_geographic_scope_review.sort(key=lambda row: row["movement_id"])

    represented = [row for row in countries.values() if row["plotted_movement_count"]]
    gap_rows_all = [gap for row in countries.values() for gap in row["internal_gaps"]]
    lead_reason_counts = Counter(
        reason for lead in candidate_policy_leads for reason in lead["review_reasons"]
    )
    summary = {
        "authored_movement_records": len(movements),
        "plotted_movement_records": sum(is_plotted(m) and m["timeframe"]["start"] <= as_of_year for m in movements),
        "authored_country_count": len(authored_country_codes),
        "plotted_country_count": len(represented),
        "policy_only_country_count": len(policy_countries - authored_country_codes),
        "single_plotted_movement_countries": sum(row["plotted_movement_count"] == 1 for row in represented),
        "low_plotted_movement_countries": sum(0 < row["plotted_movement_count"] <= LOW_COUNT_MAX for row in represented),
        "first_coded_after_2000_countries": sum(row["first_coded_year"] > 2000 for row in represented),
        "internal_gap_countries": sum(bool(row["internal_gaps"]) for row in countries.values()),
        "internal_gap_segments": len(gap_rows_all),
        "missing_current_coverage_countries": sum(row["missing_current_coverage"] for row in countries.values()),
        "missing_current_among_plotted_countries": sum(row["missing_current_coverage"] for row in represented),
        "candidate_policy_leads": len(candidate_policy_leads),
        "candidate_policy_lead_reason_counts": dict(sorted(lead_reason_counts.items())),
        "overlapping_authored_movement_pairs": overlapping_pairs,
        "overlapping_both_plotted_pairs": overlapping_both_plotted_pairs,
        "overlap_shared_policy_review_pairs": len(overlap_shared_policy_candidates),
        "overlap_shared_policy_both_plotted_pairs": sum(row["both_plotted_in_drift"] for row in overlap_shared_policy_candidates),
        "eu_supranational_geography_review_records": len(eu_geographic_scope_review),
    }
    return {
        "schema": "ieset-country-drift-coverage-audit-v1",
        "as_of_year": as_of_year,
        "method": {
            "plotted_rule": "Authored movements with country and timeframe, excluding scope=subnational and country_drift_role=context_only.",
            "coverage_interval": "Movement start through numeric end inclusive; ongoing or absent end is clipped to as_of_year. An interval denotes authored scope, not verified yearly activity.",
            "coded_year": "First/last plotted movement start or reviewed drift_attribution_year; most movement axes still use a start-year proxy.",
            "policy_leads": "Existing non-subnational policy records only. Their enacted_date year is preferred; otherwise timeframe.start is a proxy. Leads flag uncovered years or potentially mismatched links and are not inferred movements.",
            "overlap_review": "Same-country authored non-subnational movement pairs with overlapping intervals and at least one shared policy ID. Shared policies can be legitimate; these pairs are review candidates only.",
            "geographic_scope_review": "EU supranational movement country lists are authored samples, not verified full applicability maps. Unlisted countries are not evidence of no policy.",
            "excluded_from_current_gap": sorted(DEFUNCT_ISOS),
        },
        "summary": summary,
        "countries": countries,
        "candidate_policy_leads": candidate_policy_leads,
        "overlap_shared_policy_candidates": overlap_shared_policy_candidates,
        "eu_geographic_scope_review": eu_geographic_scope_review,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    countries = report["countries"]
    year = report["as_of_year"]
    lines = [
        "# Country drift coverage audit", "",
        f"As of **{year}**. This report is a source-review queue. Every movement and policy named here is an authored record; policy leads and overlap pairs are **candidates for review**, not verified new movements or corrected axis dates.",
        "", "## Summary", "",
        "| Measure | Count |", "| --- | ---: |",
        f"| Authored movement records | {summary['authored_movement_records']} |",
        f"| Movement records included in drift | {summary['plotted_movement_records']} |",
        f"| Countries with a plotted movement | {summary['plotted_country_count']} |",
        f"| Countries with one plotted movement | {summary['single_plotted_movement_countries']} |",
        f"| Countries with at most {LOW_COUNT_MAX} plotted movements | {summary['low_plotted_movement_countries']} |",
        f"| Countries first coded after 2000 | {summary['first_coded_after_2000_countries']} |",
        f"| Countries with internal uncovered intervals | {summary['internal_gap_countries']} |",
        f"| Countries lacking {year} coverage, including policy-only countries | {summary['missing_current_coverage_countries']} |",
        f"| Existing policy records flagged for research | {summary['candidate_policy_leads']} |",
        f"| Overlapping authored movement pairs sharing policy IDs | {summary['overlap_shared_policy_review_pairs']} |",
        f"| EU supranational geographic scope records to review | {summary['eu_supranational_geography_review_records']} |",
        "",
        "## Missing current coverage", "",
        "A broad movement marked ongoing counts as covered here; this does not confirm every intervening policy year.",
        "", "| ISO3 | Plotted movements | Last coded event | Last covered year |", "| --- | ---: | ---: | ---: |",
    ]
    for country, row in countries.items():
        if row["missing_current_coverage"]:
            lines.append(f"| {country} | {row['plotted_movement_count']} | {row['last_coded_year'] or '—'} | {row['last_covered_year'] or '—'} |")
    lines += ["", "## Late starts and sparse coding", "",
              "These are coverage observations. No movement is inferred from a date gap.",
              "", "| ISO3 | First coded year | Plotted movements | Last coded event |", "| --- | ---: | ---: | ---: |"]
    sparse = [
        (country, row) for country, row in countries.items()
        if row["plotted_movement_count"] and (row["first_coded_year"] > 2000 or row["plotted_movement_count"] <= LOW_COUNT_MAX)
    ]
    for country, row in sorted(sparse, key=lambda item: (-item[1]["first_coded_year"], item[1]["plotted_movement_count"], item[0])):
        lines.append(f"| {country} | {row['first_coded_year']} | {row['plotted_movement_count']} | {row['last_coded_year']} |")
    lines += ["", "## Longest internal uncovered intervals", "",
              "Intervals between authored movement timeframes, after excluding context-only and subnational records.",
              "", "| ISO3 | From | Through | Years |", "| --- | ---: | ---: | ---: |"]
    gap_list = sorted(
        ((country, gap) for country, row in countries.items() for gap in row["internal_gaps"]),
        key=lambda item: (-item[1]["years"], item[0], item[1]["from_year"]),
    )
    for country, gap in gap_list[:40]:
        lines.append(f"| {country} | {gap['from_year']} | {gap['through_year']} | {gap['years']} |")
    lines += ["", f"The full list of {summary['internal_gap_segments']} internal intervals is in the JSON report.",
              "", "## Existing dated policy leads", "",
              "These policy records may help locate missing movements or repair existing links. A `timeframe.start` year is a period proxy when no enacted date is recorded. No policy is automatically promoted to a movement.",
              "", "| Reason | Policy-country records |", "| --- | ---: |"]
    for reason, count in summary["candidate_policy_lead_reason_counts"].items():
        lines.append(f"| `{reason}` | {count} |")
    lines += ["", "| ISO3 | Year | Date basis | Scope | Existing policy | Review reason |", "| --- | ---: | --- | --- | --- | --- |"]
    for lead in report["candidate_policy_leads"][:50]:
        path = "../../" + lead["source_file"]
        reasons = ", ".join(lead["review_reasons"])
        lines.append(f"| {lead['country']} | {lead['policy_year']} | {lead['date_basis']} | {lead['scope']} | [{lead['policy_id']}]({path}) | {reasons} |")
    lines += ["", f"Showing {min(50, summary['candidate_policy_leads'])} of {summary['candidate_policy_leads']} policy-country leads; the JSON report contains all of them.",
              "", "## Overlap and shared-policy review", "",
              f"There are {summary['overlapping_authored_movement_pairs']} overlapping same-country authored movement pairs; {summary['overlapping_both_plotted_pairs']} have both records included in drift. Only pairs sharing a policy ID appear below. Sharing can be legitimate across successive or parallel movements.",
              "", "| ISO3 | Overlap | Both plotted? | Movement pair | Shared policy IDs |", "| --- | --- | --- | --- | --- |"]
    for item in report["overlap_shared_policy_candidates"]:
        mids = " / ".join(item["movement_ids"])
        shared = ", ".join(item["shared_policy_ids"])
        both = "yes" if item["both_plotted_in_drift"] else "no"
        lines.append(f"| {item['country']} | {item['overlap_from_year']}–{item['overlap_through_year']} | {both} | {mids} | {shared} |")
    lines += ["", "## EU geographic scope review", "",
              "These EU supranational movement records use authored country lists. An omitted country must not be interpreted as having no such policy. Check the instrument's applicability and membership at the relevant date before changing the lists or country map.",
              "", "| Movement | Countries currently listed | In drift? |", "| --- | ---: | --- |"]
    for item in report["eu_geographic_scope_review"]:
        path = "../../" + item["source_file"]
        plotted = "yes" if item["plotted_in_drift"] else "no"
        lines.append(f"| [{item['movement_id']}]({path}) | {item['declared_country_count']} | {plotted} |")
    lines += ["", "## Reading limits", "",
              "- Pre-first-year zeros in the numeric drift arrays are storage placeholders, not evidence of a market-oriented starting level.",
              "- A flat line inside a broad or ongoing movement interval does not establish policy stability. The method counts authored coverage, not actual legislative activity.",
              "- Policy leads need primary-source checks, scope checks, enacted-date review, and axis-level attribution before changing a map.",
              "- Overlap with a shared policy is a duplication risk to review, not proof of duplicate coding.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-year", type=int, default=dt.date.today().year)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON)
    parser.add_argument("--md-out", type=Path, default=OUT_MD)
    parser.add_argument("--check", action="store_true", help="Compare saved reports with the current corpus without writing files")
    args = parser.parse_args()
    report = report_for(load_specs("movements", "movement_id"), load_specs("policies", "policy_id"), args.as_of_year)
    rendered = {
        args.json_out: json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        args.md_out: markdown_report(report),
    }
    if args.check:
        stale = [path for path, content in rendered.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            raise SystemExit("Stale country drift coverage audit: " + ", ".join(str(path) for path in stale))
        print(f"Country drift coverage audit is current for {args.as_of_year}")
    else:
        for path, content in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"Wrote {args.json_out} and {args.md_out}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
