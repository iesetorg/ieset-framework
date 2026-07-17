#!/usr/bin/env python3
"""Reconcile data/manifests/baseline_pull.yaml against actual on-disk vintages.

The baseline pull manifest accumulated speculative series tokens during the
"swarm-9 expansion" and "INCONCLUSIVE-cleanup wave" runs. Many never resolved
to a working fetch. This script reports, per publisher and per series_id,
whether a vintage file exists under data/vintages/<publisher>/.

Outputs a markdown report (or --json for machine use) classifying each
manifest entry as:
  RESOLVED    — at least one vintage file matches the series_id
  MISSING     — no vintage file found
  PENDING     — publisher registered in publishers.yaml but no fetcher_module
  UNREGISTERED — publisher not in publishers.yaml at all

Usage:
    python3 scripts/reconcile_pull_manifest.py
    python3 scripts/reconcile_pull_manifest.py --json
    python3 scripts/reconcile_pull_manifest.py --publisher iea
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifests" / "baseline_pull.yaml"
VINTAGES = ROOT / "data" / "vintages"
PUBLISHERS = ROOT / "data" / "fetchers" / "publishers.yaml"


def load_manifest() -> list[dict]:
    doc = yaml.safe_load(MANIFEST.read_text())
    return doc.get("pulls") or []


def load_publishers() -> dict[str, dict]:
    doc = yaml.safe_load(PUBLISHERS.read_text())
    return doc.get("publishers") or {}


def vintage_exists(publisher: str, series_id: str) -> bool:
    pub_dir = VINTAGES / publisher
    if not pub_dir.exists():
        return False
    # series_ids can contain characters that are path-unsafe (":", "(").
    # The write_vintage helper sanitises; check glob prefixes.
    safe = series_id.split("(")[0].strip()
    for pattern in (f"{safe}*.parquet", f"{safe}.parquet"):
        if list(pub_dir.glob(pattern)):
            return True
    # Check subdirectory form
    sub = pub_dir / safe
    if sub.exists() and any(sub.glob("*.parquet")):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument("--publisher", help="Restrict to one publisher id.")
    args = parser.parse_args()

    pulls = load_manifest()
    publishers = load_publishers()

    # Collapse duplicate (publisher, series_id) tokens — the manifest has many.
    seen: dict[tuple[str, str], list[str]] = defaultdict(list)
    for pull in pulls:
        pub = pull.get("publisher", "")
        for s in pull.get("series") or []:
            sid = s.get("id", "")
            if sid:
                seen[(pub, sid)].append(s.get("desc", ""))

    rows: list[dict] = []
    for (pub, sid), descs in sorted(seen.items()):
        if args.publisher and pub != args.publisher:
            continue
        registered = pub in publishers
        has_fetcher = bool(publishers.get(pub, {}).get("fetcher_module"))
        exists = vintage_exists(pub, sid)
        if exists:
            status = "RESOLVED"
        elif not registered:
            status = "UNREGISTERED"
        elif not has_fetcher:
            status = "PENDING"
        else:
            status = "MISSING"
        rows.append({
            "publisher": pub,
            "series_id": sid,
            "status": status,
            "desc": (descs[0] if descs else "")[:80],
        })

    if args.json:
        print(json.dumps({"rows": rows}, indent=2))
        return 0

    by_status: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_status[r["status"]].append(r)

    total = len(rows)
    print(f"# baseline_pull.yaml reconciliation")
    print(f"_Scanned {total} unique (publisher, series_id) tokens_\n")
    for status in ("RESOLVED", "MISSING", "PENDING", "UNREGISTERED"):
        bucket = by_status.get(status, [])
        print(f"## {status} ({len(bucket)})")
        if status != "RESOLVED":
            for r in bucket:
                print(f"- `{r['publisher']}:{r['series_id']}` — {r['desc']}")
        print()

    # Action recommendations
    print("## Recommended actions")
    print()
    n_missing = len(by_status.get("MISSING", []))
    n_pending = len(by_status.get("PENDING", []))
    n_unreg = len(by_status.get("UNREGISTERED", []))
    if n_missing:
        print(f"- **MISSING ({n_missing})**: registered publisher with fetcher but no vintage on disk. "
              "Run the fetcher or drop a manual file. These are the cheapest unlocks.")
    if n_pending:
        print(f"- **PENDING ({n_pending})**: publisher registered but no fetcher_module. "
              "These need a fetcher implementation (see research documentation priority list).")
    if n_unreg:
        print(f"- **UNREGISTERED ({n_unreg})**: token in manifest but publisher not in publishers.yaml. "
              "Either register the publisher or remove the stale token from baseline_pull.yaml.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
