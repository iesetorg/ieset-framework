#!/usr/bin/env python3
"""Discover the current IRENA PxWeb table list and emit the Python literal
to paste into data/fetchers/irena.py::_PXWEB_CAPACITY_TABLES.

IRENA's PxWeb tables are versioned by half-year (e.g. 2025_H2) and the old
hardcoded list drifts out of date. This script hits the PxWeb folder API,
lists every `.px` file under the "Power Capacity and Generation" area,
filters for the country-level ELECCAP/ELECSTAT tables, and prints them
sorted newest-first.

Usage:
    python3 scripts/irena_pxweb_discover.py
    python3 scripts/irena_pxweb_discover.py --area "Power Capacity and Generation"
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import quote

import requests

PXWEB_HOST = "https://pxweb.irena.org"
DEFAULT_AREA = "Power Capacity and Generation"


def list_folder(path: str) -> list[dict]:
    url = f"{PXWEB_HOST}/api/v1/en/{quote(path)}"
    r = requests.get(
        url,
        timeout=60,
        headers={
            "User-Agent": "Mozilla/5.0 IESET irena_pxweb_discover",
            "Accept": "application/json",
        },
    )
    r.raise_for_status()
    return r.json()


def walk(area: str) -> list[str]:
    """Return all .px leaf paths under the area, depth-first."""
    leaves: list[str] = []
    seen: set[str] = set()

    def _recurse(path: str, depth: int = 0):
        if depth > 4 or path in seen:
            return
        seen.add(path)
        try:
            entries = list_folder(path)
        except requests.HTTPError as exc:
            print(f"  skip {path}: {exc}", file=sys.stderr)
            return
        for e in entries:
            if e.get("type") == "l":
                leaves.append(f"{path}/{e['label']}")
            elif e.get("type") == "d":
                _recurse(f"{path}/{e['label']}", depth + 1)

    _recurse(area)
    return leaves


def prefer_country_eleccap(leaves: list[str]) -> list[str]:
    """Sort so country-level ELECCAP/ELECSTAT tables come first, newest first."""
    def _key(path: str) -> tuple[int, tuple[int, int], str]:
        name = path.rsplit("/", 1)[-1]
        is_country = name.lower().startswith("country_")
        is_elec = any(token in name.upper() for token in ("ELECCAP", "ELECSTAT"))
        # Extract year+half from the filename, e.g. 2025_H2 -> (2025, 2)
        year_half = (0, 0)
        import re
        m = re.search(r"(\d{4})_H([12])", name)
        if m:
            year_half = (int(m.group(1)), int(m.group(2)))
        # Prefer: country > non-country; elec > non-elec; newer > older
        return (
            0 if is_country else 1,
            (-year_half[0], -year_half[1]),
            name,
        )

    return sorted(leaves, key=_key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--area",
        default=DEFAULT_AREA,
        help=f"PxWeb area folder (default: {DEFAULT_AREA!r})",
    )
    parser.add_argument(
        "--print-python",
        action="store_true",
        help="Print a ready-to-paste _PXWEB_CAPACITY_TABLES literal.",
    )
    args = parser.parse_args()

    print(f"Probing PxWeb area: {args.area}", file=sys.stderr)
    try:
        leaves = walk(args.area)
    except requests.RequestException as exc:
        print(f"PxWeb unreachable: {exc}", file=sys.stderr)
        return 1

    if not leaves:
        print("No .px tables discovered. PxWeb layout may have changed.", file=sys.stderr)
        return 2

    preferred = prefer_country_eleccap(leaves)
    # Just the filename portion (the fetcher builds the full URL itself).
    names = [p.rsplit("/", 1)[-1] for p in preferred]

    if args.print_python:
        print("_PXWEB_CAPACITY_TABLES = [")
        for n in names:
            print(f'    "{n}",')
        print("]")
        return 0

    print(f"# Discovered {len(names)} tables under {args.area!r}")
    print("# Paste the top entries into data/fetchers/irena.py::_PXWEB_CAPACITY_TABLES")
    print("# Newest country-level ELECCAP/ELECSTAT first:\n")
    for n in names[:20]:
        print(f"  {n}")
    print(f"\n# ... {max(0, len(names) - 20)} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
