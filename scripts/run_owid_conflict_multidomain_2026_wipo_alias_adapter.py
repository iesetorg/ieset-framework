#!/usr/bin/env python3
"""Post-lock WIPO physical-indicator adapter for the conflict family.

The manifest series alias is patent_applications_resident; the pinned Parquet
stores IP.PAT.RESD in indicator_id. Keep manifest and lock verification on the
frozen alias, and use the observed physical identifier only during that one
frozen numeric-loader call. Geography and every model/gate come from the
separately committed national-scope adapter and original frozen runner.
"""
from __future__ import annotations

import sys
from pathlib import Path

import run_owid_conflict_multidomain_2026_geo_adapter as geo

frozen = geo.frozen
ADAPTER = "scripts/run_owid_conflict_multidomain_2026_wipo_alias_adapter.py"
REGISTERED_ALIAS = "patent_applications_resident"
PHYSICAL_ID = "IP.PAT.RESD"


def numeric_with_physical_patent_id(source_root: Path, role: str) -> dict[tuple[str, int], float]:
    if role != "patents":
        return geo.national_numeric_values(source_root, role)
    item = frozen.SOURCE_DICT[role]
    if item["series_id"] != REGISTERED_ALIAS:
        raise RuntimeError("registered WIPO series alias changed")
    item["series_id"] = PHYSICAL_ID
    try:
        return geo.national_numeric_values(source_root, role)
    finally:
        item["series_id"] = REGISTERED_ALIAS


def main() -> None:
    if "--lock-case" in sys.argv:
        raise SystemExit("source locks belong to the original frozen runner")
    geo.ADAPTER = ADAPTER
    frozen.conflict_values = geo.national_conflict_values
    frozen.numeric_values = numeric_with_physical_patent_id
    frozen.verify_locks = geo.verify_original_locks
    frozen.RUNNER = ADAPTER
    frozen.main()


if __name__ == "__main__":
    main()
