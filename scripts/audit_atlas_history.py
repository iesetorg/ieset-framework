#!/usr/bin/env python3
"""Audit authored atlas history for every registry unit without synthesising movements.

The registry includes countries, territories, disputed units and historical states.
Modern map boundaries are reference geography, not a reconstruction of past states.
Run with --check to verify the saved reports without changing any files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[1]
KINDS = {"country_or_territory", "historical", "disputed"}
SCOPES = {"national", "subnational", "supranational"}
REGISTRY_PROVENANCE = {
    "iso_source": "pycountry 24.6.1, databases/iso3166-1.json",
    "iso_database_sha256": "f01b812b57fba9f31ff621bf33e7c7570a01964dbeb5be2167e94decf538c89f",
    "iso_entries": 249,
    "supplemental_entries": "CSK, SUN and YUG are historical codes; XKX is an explicit non-ISO Kosovo identifier, not a sovereignty claim.",
}
GEOGRAPHY_NOTE = (
    "The map uses present-day reference boundaries. An authored country code does "
    "not establish sovereignty, unchanged borders, or policy continuity in a past "
    "year. Colonial, imperial and predecessor-state episodes need their own "
    "sourced jurisdiction description; they are not automatically attributed to "
    "every modern successor country. Countries and territories are not all sovereign states."
)


def year(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 2100


def validate_registry(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("Country registry must be an array")
    seen: set[str] = set()
    rows = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"iso3", "name", "kind"}:
            raise ValueError("Registry rows require exactly iso3, name and kind")
        code = item["iso3"]
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z]{3}", code):
            raise ValueError(f"Invalid registry identifier: {code!r}")
        if code in seen:
            raise ValueError(f"Duplicate registry identifier: {code}")
        if not isinstance(item["name"], str) or not item["name"].strip():
            raise ValueError(f"Missing registry name for {code}")
        if item["kind"] not in KINDS:
            raise ValueError(f"Invalid registry kind for {code}")
        seen.add(code)
        rows.append(dict(item))
    return sorted(rows, key=lambda row: row["iso3"])


def load_specs(repo: Path, folder: str, identifier: str) -> list[dict[str, Any]]:
    records = []
    seen = set()
    for path in sorted((repo / folder).glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not document.get(identifier):
            continue
        if document[identifier] in seen:
            raise ValueError(f"Duplicate {identifier}: {document[identifier]}")
        seen.add(document[identifier])
        document["_source_file"] = path.relative_to(repo).as_posix()
        records.append(document)
    return records


def map_coverage(repo: Path, registry: list[dict[str, str]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    lookup = dict(re.findall(r'"(\d{3})":\s*"([A-Z]{3})"', (repo / "web/lib/iso-numeric-to-alpha3.ts").read_text()))
    iso_registry = {row["iso3"] for row in registry if row["kind"] == "country_or_territory"}
    if iso_registry != set(lookup.values()):
        raise ValueError("Country/territory registry differs from the checked-in ISO mapping")
    topology = json.loads((repo / "web/public/world-110m.json").read_text())
    coverage: dict[str, dict[str, Any]] = {}
    unassigned = []
    supplemental = {"Kosovo": "XKX"} if any(row["iso3"] == "XKX" for row in registry) else {}
    for geometry in topology["objects"]["countries"]["geometries"]:
        name = geometry.get("properties", {}).get("name")
        numeric = str(geometry.get("id", ""))
        iso3 = lookup.get(numeric)
        linkage = "iso_numeric"
        if not iso3:
            iso3 = supplemental.get(name)
            linkage = "supplemental_name_only"
        if not iso3:
            unassigned.append({"name": name, "numeric_id": geometry.get("id")})
            continue
        record = coverage.setdefault(iso3, {"feature_names": [], "linkage": linkage})
        record["feature_names"].append(name)
    return coverage, sorted(unassigned, key=lambda row: str(row["name"]))


def merge_intervals(intervals: list[tuple[int, int]]) -> list[dict[str, int]]:
    merged: list[dict[str, int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1]["through_year"] + 1:
            merged.append({"from_year": start, "through_year": end})
        else:
            merged[-1]["through_year"] = max(merged[-1]["through_year"], end)
    return merged


def interval_gaps(merged: list[dict[str, int]]) -> list[dict[str, int]]:
    return [
        {"from_year": left["through_year"] + 1, "through_year": right["from_year"] - 1,
         "years": right["from_year"] - left["through_year"] - 1}
        for left, right in zip(merged, merged[1:])
    ]


def history_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    visible = [row for row in records if row["included_by_as_of_year"]]
    merged = merge_intervals([(row["start_year"], row["covered_through_year"]) for row in visible])
    return {
        "first_start_year": min((row["start_year"] for row in visible), default=None),
        "last_start_year": max((row["start_year"] for row in visible), default=None),
        "last_covered_year": max((row["covered_through_year"] for row in visible), default=None),
        "intervals": records,
        "merged_intervals": merged,
        "internal_gaps": interval_gaps(merged),
    }


def build_report(
    registry: list[dict[str, str]], movements: list[dict[str, Any]], policy_ids: set[str],
    geography: dict[str, dict[str, Any]], unassigned_features: list[dict[str, Any]],
    as_of_year: int, slider_floor: int | None = None,
    policy_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    registry = validate_registry(registry)
    if not year(as_of_year) or (slider_floor is not None and not year(slider_floor)):
        raise ValueError("Invalid as-of year or slider floor")
    codes = {row["iso3"] for row in registry}
    by_country: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scope_counts: Counter[str] = Counter()
    seen = set()
    implicit_national = 0
    primary_start_years = []
    for movement in sorted(movements, key=lambda row: row["movement_id"]):
        mid = movement["movement_id"]
        if mid in seen:
            raise ValueError(f"Duplicate movement ID: {mid}")
        seen.add(mid)
        scope = movement.get("scope", "national")
        if scope not in SCOPES:
            raise ValueError(f"{mid}: invalid scope")
        scope_counts[scope] += 1
        implicit_national += "scope" not in movement
        countries = movement.get("countries")
        if not isinstance(countries, list) or not countries or not all(isinstance(c, str) for c in countries):
            raise ValueError(f"{mid}: invalid countries")
        unknown = set(countries) - codes
        if unknown:
            raise ValueError(f"{mid}: countries absent from registry: {sorted(unknown)}")
        timeframe = movement.get("timeframe") or {}
        start = timeframe.get("start")
        end = timeframe.get("end")
        if not year(start) or (end not in (None, "ongoing", "present") and (not year(end) or end < start)):
            raise ValueError(f"{mid}: invalid timeframe")
        role = movement.get("country_drift_role", "primary")
        if role not in {"primary", "context_only"}:
            raise ValueError(f"{mid}: invalid country_drift_role")
        policies = movement.get("policies") or []
        if not isinstance(policies, list) or not all(isinstance(pid, str) for pid in policies):
            raise ValueError(f"{mid}: invalid policy references")
        missing = sorted(set(policies) - policy_ids)
        record = {
            "movement_id": mid, "name": movement.get("name", mid),
            "source_file": movement.get("_source_file", f"movements/{mid}.yaml"),
            "status": movement.get("status"), "scope": scope, "country_drift_role": role,
            "start_year": start, "authored_end": end,
            "covered_through_year": min(end, as_of_year) if year(end) else as_of_year,
            "included_by_as_of_year": start <= as_of_year,
            "policy_count": len(policies), "resolved_policy_count": sum(pid in policy_ids for pid in policies),
            "policy_references_complete": bool(policies) and not missing,
            "missing_policy_ids": missing,
            "has_position_alignments": bool(movement.get("position_alignments")),
        }
        if scope == "national" and role == "primary" and start <= as_of_year:
            primary_start_years.append(start)
        for code in sorted(set(countries)):
            by_country[code].append(record)

    if slider_floor is None:
        slider_floor = min(primary_start_years, default=as_of_year)
    policies_by_country: dict[str, list[dict[str, Any]]] = defaultdict(list)
    policy_scope_counts: Counter[str] = Counter()
    seen_policies = set()
    for policy in sorted(policy_records or [], key=lambda row: row["policy_id"]):
        pid = policy["policy_id"]
        if pid in seen_policies:
            raise ValueError(f"Duplicate policy ID: {pid}")
        seen_policies.add(pid)
        scope = policy.get("scope", "national")
        if scope not in SCOPES:
            raise ValueError(f"{pid}: invalid policy scope")
        policy_scope_counts[scope] += 1
        policy_countries = policy.get("countries") or []
        if set(policy_countries) - codes:
            raise ValueError(f"{pid}: policy countries absent from registry: {sorted(set(policy_countries) - codes)}")
        timeframe = policy.get("timeframe") or {}
        policy_year = timeframe.get("start")
        basis = "timeframe.start_proxy"
        enacted_date = str(timeframe.get("enacted_date") or "")
        if re.match(r"^\d{4}(?:-|$)", enacted_date) and year(int(enacted_date[:4])):
            policy_year = int(enacted_date[:4])
            basis = "enacted_date_year"
        if not year(policy_year):
            raise ValueError(f"{pid}: invalid policy year")
        record = {"policy_id": pid, "year": policy_year, "date_basis": basis,
                  "scope": scope, "has_axis_coding": bool(policy.get("axes_moved")),
                  "source_file": policy.get("_source_file", f"policies/{pid}.yaml")}
        for code in sorted(set(policy_countries)):
            policies_by_country[code].append(record)
    countries = []
    for item in registry:
        records = sorted(by_country[item["iso3"]], key=lambda row: (row["start_year"], row["movement_id"]))
        national = [row for row in records if row["scope"] == "national"]
        primary = [row for row in national if row["country_drift_role"] == "primary"]
        national_history = history_summary(national)
        primary_history = history_summary(primary)
        geometry = geography.get(item["iso3"])
        before_floor = [row for row in national if row["start_year"] < slider_floor]
        national_policies = sorted((row for row in policies_by_country[item["iso3"]]
                                    if row["scope"] == "national" and row["year"] <= as_of_year),
                                   key=lambda row: (row["year"], row["policy_id"]))
        first_policy_year = national_policies[0]["year"] if national_policies else None
        countries.append({
            **item, "has_map_geometry": geometry is not None,
            "map_linkage": geometry["linkage"] if geometry else None,
            "map_feature_names": sorted(geometry["feature_names"]) if geometry else [],
            "counts": {
                "all_movements": len(records), "national": len(national), "national_primary": len(primary),
                "national_context_only": len(national) - len(primary),
                "subnational": sum(row["scope"] == "subnational" for row in records),
                "supranational": sum(row["scope"] == "supranational" for row in records),
                "future_national": sum(not row["included_by_as_of_year"] for row in national),
                "national_with_complete_policy_references": sum(row["policy_references_complete"] for row in national),
                "national_with_incomplete_policy_references": sum(not row["policy_references_complete"] for row in national),
                "national_without_position_alignments": sum(not row["has_position_alignments"] for row in national),
                "national_starting_before_slider_floor": len(before_floor),
                "national_entirely_before_slider_floor": sum(year(row["authored_end"]) and row["authored_end"] < slider_floor for row in before_floor),
                "national_policies": len(national_policies),
                "national_policies_with_axis_coding": sum(row["has_axis_coding"] for row in national_policies),
                "national_policies_without_axis_coding": sum(not row["has_axis_coding"] for row in national_policies),
            },
            "national_history": national_history, "primary_national_history": primary_history,
            "national_policy_history": {
                "first_year": first_policy_year,
                "last_year": national_policies[-1]["year"] if national_policies else None,
                "earliest_policies": [row for row in national_policies if row["year"] == first_policy_year],
                "policy_ids": [row["policy_id"] for row in national_policies],
            },
            "other_scope_movement_ids": [row["movement_id"] for row in records if row["scope"] != "national"],
        })

    def summarize(rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "units": len(rows),
            "with_national_history": sum(row["national_history"]["first_start_year"] is not None for row in rows),
            "without_national_history": sum(row["national_history"]["first_start_year"] is None for row in rows),
            "with_national_start_before_1900": sum(row["national_history"]["first_start_year"] is not None and row["national_history"]["first_start_year"] < 1900 for row in rows),
            "with_national_start_before_1950": sum(row["national_history"]["first_start_year"] is not None and row["national_history"]["first_start_year"] < 1950 for row in rows),
            "without_primary_national_history": sum(row["primary_national_history"]["first_start_year"] is None for row in rows),
            "with_national_policy_history": sum(row["national_policy_history"]["first_year"] is not None for row in rows),
            "with_national_policy_before_1900": sum(row["national_policy_history"]["first_year"] is not None and row["national_policy_history"]["first_year"] < 1900 for row in rows),
            "without_map_geometry": sum(not row["has_map_geometry"] for row in rows),
            "national_internal_gap_segments": sum(len(row["national_history"]["internal_gaps"]) for row in rows),
            "primary_national_internal_gap_segments": sum(len(row["primary_national_history"]["internal_gaps"]) for row in rows),
        }

    return {
        "schema_version": 1, "as_of_year": as_of_year, "slider_floor": slider_floor,
        "registry_source": REGISTRY_PROVENANCE, "modern_geography_note": GEOGRAPHY_NOTE,
        "definitions": {
            "national": "scope=national or omitted under the movement schema. Explicit subnational and supranational records never count as national.",
            "primary_national": "National records excluding country_drift_role=context_only; reported separately so contextual episodes cannot conceal a primary-history gap.",
            "slider_floor": "Defaults to the first valid primary-national start on or before the as-of year, matching the historical atlas; an explicit --slider-floor can audit a different presentation boundary.",
            "intervals": "Inclusive authored years, clipped to the as-of year. Ongoing is authored coverage, not proof of annual activity or office holding. Future records remain listed but contribute no current coverage.",
            "first_last_years": "First and last movement start years and final covered year are separate; none establishes founding, independence or uninterrupted state identity.",
            "gaps": "Only intervals between merged authored ranges; not leading years before the first record, and not a claim that no government existed. Adjacent and overlapping intervals are merged.",
            "policy_references_complete": "At least one policy reference, with every referenced ID resolving to an authored policy. This is structural coverage, not evidence that policy claims are true or effects established.",
            "national_policy_history": "National-scope policy records, separate from movements. Enacted-date year is preferred; otherwise timeframe.start is a labelled proxy. A factual policy event without axes does not become an ideological movement. Future policy dates are omitted from history counts.",
            "map_linkage": "iso_numeric follows the checked-in map lookup. supplemental_name_only denotes an existing shape without an ISO ID; its presence does not prove that the UI binds that shape to this registry entry.",
        },
        "summary": {
            "registry_units": len(registry), "authored_movement_records": len(movements),
            "movement_records_by_scope": {scope: scope_counts[scope] for scope in sorted(SCOPES)},
            "authored_policy_records": len(policy_records or []),
            "policy_records_by_scope": {scope: policy_scope_counts[scope] for scope in sorted(SCOPES)},
            "implicit_national_scope_records": implicit_national,
            "country_or_territory": summarize([row for row in countries if row["kind"] == "country_or_territory"]),
            "historical": summarize([row for row in countries if row["kind"] == "historical"]),
            "disputed": summarize([row for row in countries if row["kind"] == "disputed"]),
            "mapped_iso_units": summarize([row for row in countries if row["kind"] == "country_or_territory" and row["has_map_geometry"]]),
        },
        "unassigned_map_features": unassigned_features, "countries": countries,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = ["# Atlas historical coverage audit", "",
        f"As of {report['as_of_year']}; atlas slider begins at {report['slider_floor']}. This is an authored-coverage audit, not a sovereignty register or a completed historical research programme.", "",
        report["modern_geography_note"], "",
        "## Coverage", "", "| Registry group | Units | No national history | Starts before 1900 | Starts before 1950 | No map geometry |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for key, label in [("country_or_territory", "ISO countries and territories"), ("historical", "Historical states"), ("disputed", "Supplemental disputed units"), ("mapped_iso_units", "ISO units on the current map")]:
        row = summary[key]
        lines.append(f"| {label} | {row['units']} | {row['without_national_history']} | {row['with_national_start_before_1900']} | {row['with_national_start_before_1950']} | {row['without_map_geometry']} |")
    counts = summary["movement_records_by_scope"]
    lines += ["", f"Authored movement records: {summary['authored_movement_records']} ({counts['national']} national, {counts['subnational']} subnational, {counts['supranational']} supranational). {summary['implicit_national_scope_records']} records use the schema's implicit national scope; classification itself may still need historical-jurisdiction review.", "",
        "A missing movement is a documented research gap. Empty ideological alignments remain unclassified. Neither a broad ongoing range nor an inherited country code supplies missing historical evidence.", "",
        "## Every registry unit", "", "First/last below refer to national movement start years; coverage end is shown separately. The complete JSON retains sorted movement intervals, merged ranges, primary-only coverage, policy-reference completeness and internal gaps.", "",
        "| Code | Name | Kind | Map | National movements | First start | Last start | Covered through | Internal gaps | Complete movement policy refs | National policies | Earliest policy |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in report["countries"]:
        history = row["national_history"]
        display = lambda value: "—" if value is None else str(value)
        name = row["name"].replace("|", "\\|")
        map_label = "yes" if row["map_linkage"] == "iso_numeric" else "name only" if row["has_map_geometry"] else "no"
        lines.append(f"| {row['iso3']} | {name} | {row['kind']} | {map_label} | {row['counts']['national']} | {display(history['first_start_year'])} | {display(history['last_start_year'])} | {display(history['last_covered_year'])} | {len(history['internal_gaps'])} | {row['counts']['national_with_complete_policy_references']} | {row['counts']['national_policies']} | {display(row['national_policy_history']['first_year'])} |")
    lines += ["", "## Sources and limits", "",
        f"Registry names: {REGISTRY_PROVENANCE['iso_source']}. Source database SHA-256: `{REGISTRY_PROVENANCE['iso_database_sha256']}`. Names reproduce source labels; their use does not adjudicate political status.", "",
        REGISTRY_PROVENANCE["supplemental_entries"], "",
        "Unassigned shapes: " + (", ".join(str(row["name"]) for row in report["unassigned_map_features"]) or "none") + ".", "",
        "No movements, policy positions, colonial mappings or outcome claims are generated by this audit.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-year", type=int, default=dt.date.today().year)
    parser.add_argument("--slider-floor", type=int, help="Optional override; defaults to the earliest eligible primary-national start")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json-out", type=Path, default=REPO / "engine/audits/atlas_history_coverage.json")
    parser.add_argument("--md-out", type=Path, default=REPO / "engine/audits/atlas_history_coverage.md")
    args = parser.parse_args()
    registry = validate_registry(json.loads((REPO / "data/atlas/countries.json").read_text()))
    geography, unassigned = map_coverage(REPO, registry)
    movements = load_specs(REPO, "movements", "movement_id")
    policies = load_specs(REPO, "policies", "policy_id")
    report = build_report(registry, movements, {row["policy_id"] for row in policies}, geography, unassigned, args.as_of_year, args.slider_floor, policies)
    outputs = {args.json_out: json.dumps(report, ensure_ascii=False, indent=2) + "\n", args.md_out: markdown_report(report)}
    if args.check:
        stale = [str(path) for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            raise SystemExit("Stale atlas history audit: " + ", ".join(stale))
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
