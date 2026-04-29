#!/usr/bin/env python3
"""Print countries whose latest authored movement ends before the current year.

The atlas slider's max year is the current year. A country with no movement
spanning the current year shows as blank/grey on the map even if there is
clearly an active government there. This script flags those gaps so the
movement library can be brought current.

Defunct-state ISOs (SUN, CSK, YUG) are skipped because the world topojson
uses modern borders — they never render at any slider position.
"""
from __future__ import annotations

import datetime as _dt
import glob
import os
import sys
from collections import defaultdict
from typing import Tuple

try:
    import yaml  # type: ignore
except ImportError:
    sys.stderr.write("PyYAML required. pip install pyyaml.\n")
    sys.exit(1)

DEFUNCT = {"SUN", "CSK", "YUG"}
NOW = _dt.date.today().year


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    movements_dir = os.path.join(repo_root, "movements")
    latest: dict[str, Tuple[int, str, object]] = defaultdict(
        lambda: (-1, "", None)
    )
    for f in sorted(glob.glob(os.path.join(movements_dir, "*.yaml"))):
        base = os.path.basename(f)
        if base.startswith("_"):
            continue
        try:
            with open(f) as fh:
                doc = yaml.safe_load(fh)
        except Exception:
            continue
        if not doc or "movement_id" not in doc:
            continue
        countries = doc.get("countries") or []
        tf = doc.get("timeframe") or {}
        end = tf.get("end")
        if end in ("ongoing", "present", None):
            end_y = NOW
        else:
            try:
                end_y = int(end)
            except Exception:
                continue
        for c in countries:
            if end_y > latest[c][0]:
                latest[c] = (end_y, doc["movement_id"], end)

    stale = sorted(
        (c, y, mid, raw)
        for c, (y, mid, raw) in latest.items()
        if y < NOW and c not in DEFUNCT
    )
    print(f"Atlas year: {NOW}")
    print(f"{len(stale)} countries with no authored movement covering {NOW}:")
    print(f"  (excluded defunct ISOs: {sorted(DEFUNCT)})")
    print()
    print(f"{'iso3':<6}{'last_end':<10}{'raw':<14}{'latest_movement_id'}")
    print("-" * 80)
    for c, y, mid, raw in stale:
        print(f"{c:<6}{y:<10}{str(raw):<14}{mid}")
    return 0 if not stale else 1


if __name__ == "__main__":
    raise SystemExit(main())
