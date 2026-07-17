#!/usr/bin/env python3
"""Print the worklist of spec-complete hypotheses without a run, ordered
by tractability. One row per hypothesis, TSV.

Columns:
  id                 hypothesis_id
  topic              hypothesis topic
  estimator          estimator.template
  status             yaml status
  prior              prior_confidence
  n_countries        sample.countries length
  treatment_class    auto | manual | none — how parseable the treatment is
  publishers_ok      Y/N — every publisher the spec needs has data on disk
  publishers_needed  comma-list of publishers required

Usage:
  python3 scripts/list_runnable_hypotheses.py | column -t -s $'\t' | head -30
  python3 scripts/list_runnable_hypotheses.py --format json
  python3 scripts/list_runnable_hypotheses.py --only-runnable

The intended consumer is research documentation. Each agent claims one
row, writes engine/runs/<id>/replication.py end-to-end, tightens the
YAML's falsification rule, and commits.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"
SKIP_DIRS = {"steelman", "conditional_taxonomy", "country_year_ideology"}
SOURCE_RE = re.compile(r"^([a-z][a-z0-9_]*):([A-Za-z0-9_.\-]+)")
COUNTRY_YEAR_RE = re.compile(
    r"country\s*=\s*([A-Z]{3})\s*and\s*year\s*[><=]+\s*(\d{4})", re.I
)


def list_files() -> list[Path]:
    out = []
    for topic in sorted(HYP_ROOT.iterdir()):
        if not topic.is_dir() or topic.name in SKIP_DIRS:
            continue
        for f in sorted(topic.glob("*.yaml")):
            if not f.name.startswith("_"):
                out.append(f)
    return out


def fully_specced(doc: dict) -> bool:
    v = doc.get("variables") or {}
    return bool(
        v.get("outcome")
        and doc.get("sample")
        and doc.get("estimator")
        and doc.get("falsification")
    )


def has_run(hid: str) -> bool:
    return (REPO / "engine" / "runs" / hid / "diagnostics.json").exists()


def has_replication_script(hid: str) -> bool:
    return (REPO / "engine" / "runs" / hid / "replication.py").exists()


def needed_publishers(doc: dict) -> set[str]:
    out = set()
    for bucket in ("outcome", "treatment", "decomposition_channels", "controls"):
        for v in (doc.get("variables") or {}).get(bucket, []) or []:
            if not isinstance(v, dict):
                continue
            src = v.get("source")
            if not isinstance(src, str):
                continue
            m = SOURCE_RE.match(src.strip())
            if m:
                out.add(m.group(1))
    return out


def treatment_class(doc: dict) -> str:
    treatments = (doc.get("variables") or {}).get("treatment", []) or []
    if not treatments:
        return "none"
    has_parseable = False
    has_manual = False
    for t in treatments:
        src = t.get("source", "") if isinstance(t, dict) else ""
        if not isinstance(src, str):
            continue
        if "manual_classification" in src or "AJR" in src or "Saiz" in src:
            has_manual = True
        elif COUNTRY_YEAR_RE.search(src):
            has_parseable = True
    if has_manual and not has_parseable:
        return "manual"
    if has_parseable:
        return "auto"
    return "manual"  # default — unclear treatments need human judgment


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["tsv", "json"], default="tsv")
    ap.add_argument(
        "--only-runnable",
        action="store_true",
        help="filter to rows where publishers_ok=Y AND no replication.py exists yet",
    )
    args = ap.parse_args()

    rows = []
    for path in list_files():
        try:
            doc = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict) or not doc.get("hypothesis_id"):
            continue
        if not fully_specced(doc):
            continue
        hid = doc["hypothesis_id"]
        if has_run(hid) or has_replication_script(hid):
            continue
        pubs = needed_publishers(doc)
        on_disk = {
            p for p in pubs if (REPO / "data" / "vintages" / p).exists()
        }
        publishers_ok = bool(pubs) and pubs.issubset(on_disk)
        if args.only_runnable and not publishers_ok:
            continue
        rows.append(
            {
                "id": hid,
                "topic": doc.get("topic", ""),
                "estimator": doc.get("estimator", {}).get("template", ""),
                "status": doc.get("status", ""),
                "prior": doc.get("prior_confidence", ""),
                "n_countries": len((doc.get("sample") or {}).get("countries", [])),
                "treatment_class": treatment_class(doc),
                "publishers_ok": "Y" if publishers_ok else "N",
                "publishers_needed": ",".join(sorted(pubs)),
            }
        )

    # Sort by tractability: data-ready first, then auto-treatments first
    def sort_key(r):
        return (
            0 if r["publishers_ok"] == "Y" else 1,
            {"auto": 0, "none": 1, "manual": 2}[r["treatment_class"]],
            -float(r["prior"]) if isinstance(r["prior"], (int, float)) else 0,
            r["id"],
        )

    rows.sort(key=sort_key)

    if args.format == "json":
        json.dump(rows, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    cols = [
        "id",
        "topic",
        "estimator",
        "status",
        "prior",
        "n_countries",
        "treatment_class",
        "publishers_ok",
        "publishers_needed",
    ]
    print("\t".join(cols))
    for r in rows:
        print("\t".join(str(r[c]) for c in cols))


if __name__ == "__main__":
    main()
