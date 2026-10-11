#!/usr/bin/env python3
"""Reproduce the atlas's unscored constitutional context from pinned CCP v6 data.

Offline by design. It never edits movements, policy axes, or drift measurements.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE_RELATIVE = Path("data/sources/ccp")
OUTPUT_RELATIVE = Path("data/atlas/constitutional_history.json")
REQUIRED_COLUMNS = {"cowcode", "country", "year", "systid", "evntid", "evnttype"}
EVENT_LABELS = {
    "new": "Constitution adopted",
    "amendment": "Constitutional amendment",
    "interim": "Interim constitution",
    "reinstated": "Constitution reinstated",
    "suspension": "Constitution suspended",
    "samendment": "Constitutional event (source code: samendment)",
}
ALLOWED_TYPES = set(EVENT_LABELS) | {"non-event"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_rows(data: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if set(reader.fieldnames or []) != REQUIRED_COLUMNS:
        raise ValueError("CCP CSV columns differ from the reviewed v6 schema")
    rows = []
    for line, raw in enumerate(reader, start=2):
        if None in raw:
            raise ValueError(f"CCP CSV line {line}: unexpected extra columns")
        if raw["evnttype"] not in ALLOWED_TYPES:
            raise ValueError(f"CCP CSV line {line}: unknown event type {raw['evnttype']!r}")
        row = {"source_row_id": line, "country": raw["country"], "event_type": raw["evnttype"]}
        if not row["country"]:
            raise ValueError(f"CCP CSV line {line}: missing country")
        for raw_key, key in [("cowcode", "cowcode"), ("year", "year"), ("systid", "system_id"), ("evntid", "event_id")]:
            value = raw[raw_key]
            if not value and raw_key in {"systid", "evntid"}:
                row[key] = None
            elif value and value.isdecimal():
                row[key] = int(value)
            else:
                raise ValueError(f"CCP CSV line {line}: invalid {raw_key}")
        if not 1789 <= row["year"] <= 2025:
            raise ValueError(f"CCP CSV line {line}: year outside reviewed source coverage")
        if row["event_type"] != "non-event" and row["event_id"] is None:
            raise ValueError(f"CCP CSV line {line}: constitutional event lacks source event ID")
        rows.append(row)
    return rows


def validate_crosswalk(crosswalk: dict) -> dict:
    targets = {country["iso3"] for country in crosswalk["countries"]}
    if len(targets) != len(crosswalk["countries"]):
        raise ValueError("Duplicate target country in crosswalk")
    result = {}
    for entity in crosswalk["entities"]:
        key = (entity["cowcode"], entity["country"])
        if key in result:
            raise ValueError(f"Duplicate source entity in crosswalk: {key}")
        segments = sorted(entity["segments"], key=lambda item: item["start_year"])
        last_end = 1788
        for segment in segments:
            if segment["start_year"] <= last_end or segment["start_year"] > segment["end_year"]:
                raise ValueError(f"Overlapping or reversed mapping segments: {key}")
            last_end = segment["end_year"]
            if segment["iso3"] is not None and segment["iso3"] not in targets:
                raise ValueError(f"Unknown mapping target: {segment['iso3']}")
            if not segment.get("note"):
                raise ValueError(f"Mapping segment lacks explanation: {key}")
        result[key] = segments
    return result


def map_row(row: dict, crosswalk: dict) -> tuple[str | None, str]:
    key = (row["cowcode"], row["country"])
    if key not in crosswalk:
        raise ValueError(f"Source entity missing from reviewed crosswalk: {key}")
    matching = [segment for segment in crosswalk[key] if segment["start_year"] <= row["year"] <= segment["end_year"]]
    if len(matching) != 1:
        raise ValueError(f"Source row requires exactly one explicit mapping segment: {key}, {row['year']}")
    return matching[0]["iso3"], matching[0]["note"]


def missing_ranges(years: set[int]) -> list[dict]:
    if not years:
        return []
    missing = sorted(set(range(min(years), max(years) + 1)) - years)
    ranges = []
    for year in missing:
        if ranges and year == ranges[-1]["end_year"] + 1:
            ranges[-1]["end_year"] = year
        else:
            ranges.append({"start_year": year, "end_year": year})
    return ranges


def make_event(row: dict, source: dict) -> dict:
    event_type = row["event_type"]
    label = EVENT_LABELS[event_type]
    if event_type == "samendment":
        summary = "CCP records the event code 'samendment'. Its v6 codebook does not define this code, so no further interpretation is assigned."
    else:
        summary = f"CCP records a constitutional event ({event_type}) for {row['country']} in {row['year']}. This describes constitutional text, not implementation, ideology, or measured outcomes."
    return {
        "id": f"ccp-v6-row-{row['source_row_id']}",
        "start_year": row["year"],
        "title": f"{row['country']}: {label}",
        "summary": summary,
        "sources": [source],
        "source_row_id": row["source_row_id"],
        "source_cowcode": row["cowcode"],
        "source_country": row["country"],
        "source_system_id": row["system_id"],
        "source_event_id": row["event_id"],
        "source_event_code": event_type,
    }


def make_record(iso3: str | None, name: str, rows: list[dict], notes: set[str], provenance: dict, source: dict) -> dict:
    years = {row["year"] for row in rows}
    events = [make_event(row, source) for row in sorted(rows, key=lambda row: (row["year"], row["source_row_id"])) if row["event_type"] != "non-event"]
    coverage = {
        "start_year": min(years) if years else None,
        "end_year": max(years) if years else None,
        "observed_year_count": len(years),
        "source_row_count": len(rows),
        "unobserved_ranges": missing_ranges(years),
    }
    if not rows:
        status = "not_covered"
        summary = "No source rows have a reviewed mapping to this atlas country in CCP v6. This is a coverage gap, not evidence of no constitutional history."
    elif not events:
        status = "no_recorded_events"
        summary = f"CCP includes {len(years)} observed years for this entity ({min(years)}–{max(years)}), but no event-coded rows. This does not mean there was no constitution or constitutional history."
    else:
        status = "recorded"
        summary = f"CCP records {len(events)} constitutional events across {len(years)} observed years ({min(years)}–{max(years)}). Dates describe constitutional text, not implementation or political ideology."
    if rows:
        summary += " Missing source years are unknown; no event or constitutional status is inferred for 2026."
    result = {
        "title": f"{name} constitutional chronology",
        "summary": summary,
        "checked_on": provenance["retrieved_on"],
        "sources": [source],
        "events": events,
        "coverage": coverage,
        "status": status,
        "source_country_names": sorted({row["country"] for row in rows}),
        "mapping_note": " ".join(sorted(notes)) if notes else "No reviewed CCP source mapping is available for this atlas country.",
    }
    if iso3:
        result["iso3"] = iso3
    return result


def build_history(rows: list[dict], crosswalk: dict, provenance: dict) -> dict:
    mapping = validate_crosswalk(crosswalk)
    by_country, country_notes = defaultdict(list), defaultdict(set)
    unmapped, unmapped_notes = defaultdict(list), defaultdict(set)
    source = {"title": "CCP constitutional chronology v6 — dataset and codebook", "url": provenance["source_url"]}
    for row in rows:
        iso3, note = map_row(row, mapping)
        if iso3:
            by_country[iso3].append(row)
            country_notes[iso3].add(note)
        else:
            key = (row["cowcode"], row["country"])
            unmapped[key].append(row)
            unmapped_notes[key].add(note)
    countries = [make_record(country["iso3"], country["name"], by_country[country["iso3"]], country_notes[country["iso3"]], provenance, source) for country in sorted(crosswalk["countries"], key=lambda item: item["iso3"])]
    historical_entities = []
    for key in sorted(unmapped):
        record = make_record(None, key[1], unmapped[key], unmapped_notes[key], provenance, source)
        record["source_cowcode"] = key[0]
        record["source_country"] = key[1]
        historical_entities.append(record)
    mapped_events = sum(len(country["events"]) for country in countries)
    unmapped_events = sum(len(entity["events"]) for entity in historical_entities)
    event_count = sum(row["event_type"] != "non-event" for row in rows)
    if mapped_events + unmapped_events != event_count:
        raise ValueError("Constitutional events were lost or duplicated during country mapping")
    metadata = {key: provenance[key] for key in ["name", "version", "coverage_start", "coverage_end", "source_url", "archive_url", "archive_sha256", "publication_date", "citation", "license", "source_notes"]}
    metadata.update({
        "source_file": str(SOURCE_RELATIVE / "ccpcce_v6.csv"),
        "source_sha256": provenance["files"]["ccpcce_v6.csv"]["sha256"],
        "crosswalk_file": str(SOURCE_RELATIVE / "country_crosswalk_v6.json"),
        "source_row_count": len(rows),
        "source_entity_count": len({(row["cowcode"], row["country"]) for row in rows}),
        "source_event_type_counts": dict(sorted(Counter(row["event_type"] for row in rows).items())),
        "mapped_event_count": mapped_events,
        "unmapped_event_count": unmapped_events,
        "mapped_country_count": sum(country["status"] != "not_covered" for country in countries),
        "mapped_countries_with_events": sum(country["status"] == "recorded" for country in countries),
        "atlas_country_count": len(countries),
        "retained_historical_entity_count": len(historical_entities),
        "interpretation": "Discrete constitutional events only. No interpolation, economic policy classification, position score, or inferred current constitutional status.",
    })
    return {"schema_version": 1, "dataset": metadata, "countries": countries, "historical_entities": historical_entities}


def load_pinned(root: Path) -> tuple[list[dict], dict, dict]:
    directory = root / SOURCE_RELATIVE
    provenance = json.loads((directory / "provenance.json").read_text())
    for name, expected in provenance["files"].items():
        data = (directory / name).read_bytes()
        if sha256(data) != expected["sha256"] or len(data) != expected["bytes"]:
            raise ValueError(f"Pinned CCP source file changed: {name}")
    rows = parse_rows((directory / "ccpcce_v6.csv").read_bytes())
    crosswalk = json.loads((directory / "country_crosswalk_v6.json").read_text())
    registry_path = root / "data/atlas/countries.json"
    if registry_path.is_file():
        registry_ids = {country["iso3"] for country in json.loads(registry_path.read_text())}
        mapped_ids = {country["iso3"] for country in crosswalk["countries"]}
        if registry_ids != mapped_ids:
            raise ValueError("CCP target crosswalk differs from the atlas country registry")
    return rows, crosswalk, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="Check the derived JSON without editing it")
    args = parser.parse_args()
    root = args.root.resolve()
    destination = args.output or root / OUTPUT_RELATIVE
    try:
        history = build_history(*load_pinned(root))
        expected = json.dumps(history, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not destination.is_file() or destination.read_text() != expected:
                print(f"Stale constitutional history: {destination}", file=sys.stderr)
                return 1
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(expected)
        summary = Counter(country["status"] for country in history["countries"])
        print(json.dumps({"check": args.check, "output": str(destination), "countries": len(history["countries"]), "country_statuses": dict(summary), "source_rows": history["dataset"]["source_row_count"], "mapped_events": history["dataset"]["mapped_event_count"], "unmapped_events": history["dataset"]["unmapped_event_count"]}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Constitutional history import failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
