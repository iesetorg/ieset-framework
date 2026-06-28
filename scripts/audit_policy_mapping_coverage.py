#!/usr/bin/env python3
"""Audit policy/movement coverage for the global policy-mapping target sets.

This is intentionally lightweight: it counts movement and policy YAML files by
their `countries` entries, then reports thin countries for the G20, BRICS,
EU27, MENA, Mercosur, and Africa coverage sets used by the 2026-06-28 global
policy-mapping dispatch.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

TARGET_GROUPS: dict[str, list[str]] = {
    "g20_states": [
        "ARG", "AUS", "BRA", "CAN", "CHN", "FRA", "DEU", "IND", "IDN",
        "ITA", "JPN", "KOR", "MEX", "RUS", "SAU", "ZAF", "TUR", "GBR",
        "USA",
    ],
    "brics_coverage": [
        "BRA", "RUS", "IND", "CHN", "ZAF", "EGY", "ETH", "IDN", "IRN",
        "ARE", "SAU",
    ],
    "eu27": [
        "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN",
        "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX",
        "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
    ],
    "mercosur_coverage": ["ARG", "BOL", "BRA", "PRY", "URY", "VEN"],
    "mena_core": [
        "DZA", "BHR", "EGY", "IRN", "IRQ", "ISR", "JOR", "KWT", "LBN",
        "LBY", "MAR", "OMN", "PSE", "QAT", "SAU", "SYR", "TUN", "ARE",
        "YEM",
    ],
    "africa_coverage": [
        "DZA", "AGO", "BEN", "BWA", "BFA", "BDI", "CMR", "CPV", "CAF",
        "TCD", "COM", "COG", "COD", "CIV", "DJI", "EGY", "GNQ", "ERI",
        "SWZ", "ETH", "GAB", "GMB", "GHA", "GIN", "GNB", "KEN", "LSO",
        "LBR", "LBY", "MDG", "MWI", "MLI", "MRT", "MUS", "MAR", "MOZ",
        "NAM", "NER", "NGA", "RWA", "STP", "SEN", "SYC", "SLE", "SOM",
        "ZAF", "SSD", "SDN", "TZA", "TGO", "TUN", "UGA", "ESH", "ZMB",
        "ZWE",
    ],
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    return doc if isinstance(doc, dict) else {}


def collect_counts() -> dict[str, Any]:
    movement_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    ongoing_movements: defaultdict[str, list[str]] = defaultdict(list)

    for path in sorted((ROOT / "movements").glob("*.yaml")):
        doc = load_yaml(path)
        countries = doc.get("countries") or []
        timeframe = doc.get("timeframe") or {}
        movement_id = doc.get("movement_id") or path.stem
        for country in countries:
            movement_counts[country] += 1
            if isinstance(timeframe, dict) and timeframe.get("end") == "ongoing":
                ongoing_movements[country].append(movement_id)

    for path in sorted((ROOT / "policies").glob("*.yaml")):
        doc = load_yaml(path)
        for country in doc.get("countries") or []:
            policy_counts[country] += 1

    all_targets = sorted({iso for countries in TARGET_GROUPS.values() for iso in countries})
    rows = []
    for iso in all_targets:
        groups = [name for name, countries in TARGET_GROUPS.items() if iso in countries]
        rows.append({
            "iso3": iso,
            "groups": groups,
            "movements": movement_counts[iso],
            "policies": policy_counts[iso],
            "ongoing_movements": ongoing_movements[iso],
        })

    return {
        "movement_file_count": len(list((ROOT / "movements").glob("*.yaml"))),
        "policy_file_count": len(list((ROOT / "policies").glob("*.yaml"))),
        "groups": TARGET_GROUPS,
        "rows": rows,
    }


def coverage_band(row: dict[str, Any]) -> str:
    movements = int(row["movements"])
    policies = int(row["policies"])
    if movements == 0 and policies == 0:
        return "zero"
    if movements == 0 or policies <= 2:
        return "thin"
    if movements < 3 or policies < 10:
        return "partial"
    return "covered"


def render_markdown(data: dict[str, Any], thin_limit: int) -> str:
    rows = data["rows"]
    lines = [
        "# Policy Mapping Coverage Audit",
        "",
        f"- Movement specs: {data['movement_file_count']}",
        f"- Policy specs: {data['policy_file_count']}",
        "",
        "## Group Summary",
        "",
        "| Group | Countries | Zero | Thin | Partial | Covered |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for group, countries in TARGET_GROUPS.items():
        group_rows = [row for row in rows if row["iso3"] in countries]
        counts = Counter(coverage_band(row) for row in group_rows)
        lines.append(
            f"| {group} | {len(countries)} | {counts['zero']} | "
            f"{counts['thin']} | {counts['partial']} | {counts['covered']} |"
        )

    lines.extend([
        "",
        "## Thinnest Targets",
        "",
        "| ISO3 | Groups | Movements | Policies | Ongoing movement ids |",
        "| --- | --- | ---: | ---: | --- |",
    ])
    ranked = sorted(
        rows,
        key=lambda row: (
            coverage_band(row) != "zero",
            coverage_band(row) != "thin",
            int(row["movements"]),
            int(row["policies"]),
            row["iso3"],
        ),
    )
    for row in ranked[:thin_limit]:
        ongoing = ", ".join(row["ongoing_movements"][:3])
        lines.append(
            f"| {row['iso3']} | {', '.join(row['groups'])} | "
            f"{row['movements']} | {row['policies']} | {ongoing} |"
        )

    lines.extend([
        "",
        "## Full Target Table",
        "",
        "| ISO3 | Groups | Movements | Policies | Ongoing movement ids | Band |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ])
    for row in rows:
        ongoing = ", ".join(row["ongoing_movements"][:3])
        lines.append(
            f"| {row['iso3']} | {', '.join(row['groups'])} | "
            f"{row['movements']} | {row['policies']} | {ongoing} | "
            f"{coverage_band(row)} |"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    parser.add_argument("--output", type=Path, help="optional output path")
    parser.add_argument("--thin-limit", type=int, default=40)
    args = parser.parse_args()

    data = collect_counts()
    text = json.dumps(data, indent=2, sort_keys=True) + "\n" if args.json else render_markdown(data, args.thin_limit)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
