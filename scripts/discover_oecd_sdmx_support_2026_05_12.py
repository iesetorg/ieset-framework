#!/usr/bin/env python3
"""Local OECD SDMX support discovery for STAN, revenue, and fossil work.

This script is intentionally offline by default. It inspects the checked-in
OECD fetcher mappings, local vintages, and hypothesis/spec references so a
planner can decide which OECD dataflows are ready to fetch and which need
catalogue probing later.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OECD_FETCHER = ROOT / "data" / "fetchers" / "oecd.py"
VINTAGES = ROOT / "data" / "vintages"
SEARCH_ROOTS = [ROOT / "hypotheses", ROOT / "scripts", ROOT / "data" / "manifests"]

TARGETS = {
    "stan": ("stan", "dsd_stan", "df_stan", "oecd stan", "value added"),
    "revenue": ("revenue", "tax", "dsd_tax", "df_tax", "taxation"),
    "fossil": ("fossil", "subsid", "energy", "carbon", "fuel"),
}


def load_fetcher_dicts() -> dict[str, dict[str, str]]:
    tree = ast.parse(OECD_FETCHER.read_text())
    out: dict[str, dict[str, str]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.AnnAssign, ast.Assign)):
            continue
        target: ast.expr | None
        value: ast.expr
        if isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        else:
            target = node.targets[0] if node.targets else None
            value = node.value
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Dict):
            continue
        if target.id not in {"_OECD_SHORTCUTS", "_DSD_AGENCY"}:
            continue
        parsed: dict[str, str] = {}
        for k_node, v_node in zip(value.keys, value.values):
            if isinstance(k_node, ast.Constant) and isinstance(v_node, ast.Constant):
                parsed[str(k_node.value)] = str(v_node.value)
        out[target.id] = parsed
    return out


def matches_target(text: str, target: str) -> bool:
    haystack = text.lower()
    if target == "stan":
        return any(
            re.search(pattern, haystack)
            for pattern in (
                r"(?<![a-z0-9])stan(?![a-z0-9])",
                r"dsd_stan",
                r"df_stan",
                r"oecd\s+stan",
                r"value[- ]added",
            )
        )
    return any(token in haystack for token in TARGETS[target])


def matching_items(items: dict[str, str], target: str) -> list[dict[str, str]]:
    rows = []
    for key, value in sorted(items.items()):
        joined = f"{key} {value}"
        if matches_target(joined, target):
            rows.append({"key": key, "value": value})
    return rows


def matching_vintages(target: str) -> list[str]:
    rows = []
    if not VINTAGES.exists():
        return rows
    for path in sorted(VINTAGES.glob("*/*")):
        rel = path.relative_to(ROOT).as_posix()
        if matches_target(rel, target):
            rows.append(rel)
    return rows


def matching_refs(target: str, limit: int) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    suffixes = {".py", ".yaml", ".yml", ".md"}
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.suffix in suffixes):
            rel = path.relative_to(ROOT).as_posix()
            try:
                lines = path.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                if "oecd" not in line.lower() and target == "stan":
                    if "stan" not in line.lower():
                        continue
                if matches_target(line, target):
                    refs.append({"path": rel, "line": lineno, "text": line.strip()[:220]})
                    if len(refs) >= limit:
                        return refs
    return refs


def status_for(target: str, shortcuts: list[dict[str, str]], vintages: list[str]) -> str:
    if target == "fossil":
        if any("/oecd" in v and matches_target(v, target) for v in vintages):
            return "local_oecd_vintage_present"
        return "no_oecd_shortcut_or_vintage; use non-OECD vintages or manual fossil support first"
    if shortcuts and vintages:
        return "mapped_and_some_local_vintage_present"
    if shortcuts:
        return "mapped_in_fetcher; fetch/probe still needed"
    if vintages:
        return "local_vintage_present; fetcher alias may need alignment"
    return "not_locally_supported"


def build_report(ref_limit: int) -> dict[str, Any]:
    mappings = load_fetcher_dicts()
    shortcuts = mappings.get("_OECD_SHORTCUTS", {})
    dsd_agency = mappings.get("_DSD_AGENCY", {})
    targets = {}
    for target in TARGETS:
        shortcut_hits = matching_items(shortcuts, target)
        agency_hits = matching_items(dsd_agency, target)
        vintages = matching_vintages(target)
        targets[target] = {
            "status": status_for(target, shortcut_hits + agency_hits, vintages),
            "fetcher_shortcuts": shortcut_hits,
            "dsd_agency_hints": agency_hits,
            "local_vintages": vintages[:30],
            "local_vintage_count": len(vintages),
            "references": matching_refs(target, ref_limit),
        }
    return {
        "script": Path(__file__).relative_to(ROOT).as_posix(),
        "network_required": False,
        "fetcher": OECD_FETCHER.relative_to(ROOT).as_posix(),
        "targets": targets,
        "suggested_fetch_commands": [
            "python3 scripts/fetch.py oecd STAN --start 2015 --end 2024",
            "python3 scripts/fetch.py oecd DSD_TAX --start 1990 --end 2024",
            "python3 scripts/fetch.py oecd 'OECD.ENV.EPI,DSD_GHG@DF_AIR_GHG,1.0' --start 1990 --end 2024  # only after catalogue confirmation",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref-limit", type=int, default=15)
    args = parser.parse_args()
    print(json.dumps(build_report(args.ref_limit), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
