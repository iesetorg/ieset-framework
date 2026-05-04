#!/usr/bin/env python3
"""Probe blocked source recovery targets without storing API secrets.

Usage:
    python scripts/probe_blocked_sources.py --read-zenrows-key-stdin oecd-catalogue

The key is read from stdin, placed in the process environment, and never
written to disk.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read_key_if_needed(enabled: bool) -> None:
    if not enabled:
        return
    key = sys.stdin.readline().strip()
    if key:
        os.environ["ZENROWS_API_KEY"] = key


def oecd_catalogue() -> int:
    from data.fetchers.oecd import _load_dataflows

    flows = _load_dataflows()
    print(f"flows={len(flows)}")
    terms = [
        "FIN_RESOURCES", "EAG", "education finance", "financial resources",
        "HSG_INEQ", "housing inequality", "affordable housing", "HH_DASH",
    ]
    lowered = [(t, t.lower().replace("_", " ")) for t in terms]
    hits = []
    for flow in flows:
        haystack = " ".join(str(flow.get(k) or "") for k in ("agencyID", "id", "name"))
        hlow = haystack.lower().replace("_", " ")
        if any(term in hlow for _, term in lowered):
            hits.append(flow)
    for flow in hits[:80]:
        print(
            f"{flow.get('agencyID')},{flow.get('id')},{flow.get('version') or '1.0'}"
            f" :: {flow.get('name')}"
        )
    return 0 if flows else 1


def http_probe() -> int:
    from data.fetchers._http import get
    from data.fetchers.oecd import _resolve_dataflow

    probes = [
        ("oecd-dataflows", "https://sdmx.oecd.org/public/rest/dataflow/all/all/latest"),
        (
            "education-subnational-finance",
            "https://sdmx.oecd.org/public/rest/data/"
            + _resolve_dataflow("OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0")
            + "/all?startPeriod=2022&endPeriod=2022&format=csvfilewithlabels",
        ),
        (
            "housing-inequality",
            "https://sdmx.oecd.org/public/rest/data/"
            + _resolve_dataflow("OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0")
            + "/.3_2+3_3.....?format=csvfilewithlabels",
        ),
        ("oecd-data-explorer", "https://data-explorer.oecd.org/"),
    ]
    for label, url in probes:
        try:
            payload = get(url, timeout=60, zenrows_js_render=False)
            print(
                f"OK {label} {payload.status_code} {payload.transport} "
                f"{payload.content_type} bytes={len(payload.content)} url={payload.url}"
            )
            print(payload.text[:240].replace("\n", " "))
        except Exception as exc:  # noqa: BLE001
            text = str(exc)
            key = os.environ.get("ZENROWS_API_KEY")
            if key:
                text = text.replace(key, "<ZENROWS_API_KEY>")
            print(f"ERR {label} {type(exc).__name__}: {text}")
    return 0


def oecd_search(query: str, rows: int) -> int:
    from data.fetchers._http import get

    url = "https://dotstat-search.oecd.org/api/search?" + urlencode(
        {"tenant": "oecd", "q": query, "rows": rows}
    )
    payload = get(url, timeout=60, zenrows_js_render=False)
    data = json.loads(payload.text)
    print(f"query={query!r} rows={len(data.get('dataflows') or [])} total={data.get('numFound')}")
    for flow in (data.get("dataflows") or [])[:rows]:
        print(
            f"{flow.get('agencyId')},{flow.get('dataflowId')},{flow.get('version') or '1.0'}"
            f" :: {flow.get('name')}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read-zenrows-key-stdin", action="store_true")
    parser.add_argument("task", choices=["oecd-catalogue", "oecd-search", "http-probe"])
    parser.add_argument("--query", default="", help="Search query for oecd-search")
    parser.add_argument("--rows", type=int, default=20, help="Maximum search rows to display")
    args = parser.parse_args()
    read_key_if_needed(args.read_zenrows_key_stdin)
    if args.task == "oecd-catalogue":
        return oecd_catalogue()
    if args.task == "http-probe":
        return http_probe()
    if args.task == "oecd-search":
        if not args.query:
            print("--query is required for oecd-search", file=sys.stderr)
            return 2
        return oecd_search(args.query, args.rows)
    raise AssertionError(args.task)


if __name__ == "__main__":
    raise SystemExit(main())
