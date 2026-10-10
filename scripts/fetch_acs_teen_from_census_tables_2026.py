#!/usr/bin/env python3
"""Acquire frozen S2301 fields through Census's official no-key table service.

This post-registration transport adapter does not alter the registered model,
roster, outcome fields, or verdict rule. It retains each exact HTTP body, then
creates API-shaped projections for the immutable registered runner. Its lock
explicitly identifies those projections as derived, not direct API responses.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_us_state_minimum_wage_bite_teen_employment_2026 as frozen  # noqa: E402

SERVICE = "https://data.census.gov/api/access/data/table"
TABLE_RAW_DIR = f"data/pinned_evidence/{frozen.HID}_official_table_responses"
ADAPTER = "scripts/fetch_acs_teen_from_census_tables_2026.py"
FIPS = tuple(sorted({f for f, _, _ in frozen.keys()}))


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def url_for(year: int, fips: str) -> str:
    return SERVICE + "?" + urllib.parse.urlencode({
        "id": f"ACSST1Y{year}.S2301", "g": f"040XX00US{fips}"})


def raw_path(year: int, fips: str) -> str:
    return f"{TABLE_RAW_DIR}/{year}/{fips}.json"


def parse_body(body: bytes, year: int, fips: str) -> list[str]:
    payload = json.loads(body)
    result = payload["response"]
    if result.get("objectId") != f"ACSST1Y{year}.S2301" or result.get("tableName") != "S2301":
        raise ValueError(f"wrong official table for {year}/{fips}")
    api_uri = str(result.get("dataAPIURI", ""))
    if (f"/data/{year}/acs/acs1/subject?" not in api_uri
            or "group(S2301)" not in api_uri
            or f"ucgid=0400000US{fips}" not in api_uri):
        raise ValueError(f"wrong underlying Census API relation for {year}/{fips}")
    data = result.get("data")
    if not isinstance(data, list) or len(data) != 2:
        raise ValueError(f"one state data row required for {year}/{fips}")
    header, row = data
    if len(header) != len(set(header)) or len(header) != len(row):
        raise ValueError(f"duplicate/misaligned columns for {year}/{fips}")
    required = ("GEO_ID", *frozen.FIELDS[0:3])
    if any(field not in header for field in required):
        raise ValueError(f"missing registered S2301 field for {year}/{fips}")
    indexed = dict(zip(header, row))
    if indexed["GEO_ID"] != f"0400000US{fips}" or not indexed["NAME"]:
        raise ValueError(f"wrong Census state key for {year}/{fips}")
    return [indexed["NAME"], indexed[frozen.FIELDS[1]], indexed[frozen.FIELDS[2]], fips]


def fetch_one(year: int, fips: str) -> tuple[int, str, bytes]:
    path = ROOT / raw_path(year, fips)
    if path.exists():
        body = path.read_bytes()
        parse_body(body, year, fips)
        return year, fips, body
    last = ""
    for attempt in range(3):
        proc = subprocess.run(["curl", "-fsS", "-G", "--max-time", "35",
                               "--data-urlencode", f"id=ACSST1Y{year}.S2301",
                               "--data-urlencode", f"g=040XX00US{fips}", SERVICE],
                              capture_output=True)
        if proc.returncode == 0:
            try:
                parse_body(proc.stdout, year, fips)
                return year, fips, proc.stdout
            except (ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
                last = str(exc)
        else:
            last = f"curl exit {proc.returncode}"
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"official Census response unavailable for {year}/{fips}: {last}")


def projections(raw: dict[tuple[int, str], bytes]) -> dict[int, bytes]:
    result = {}
    for year in frozen.YEARS:
        rows = [list(frozen.FIELDS)]
        for fips in FIPS:
            rows.append(parse_body(raw[(year, fips)], year, fips))
        result[year] = (json.dumps(rows, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    return result


def fetch_lock() -> dict:
    frozen.registered()
    frozen.preflight()
    if (ROOT / frozen.LOCK).exists() or (ROOT / frozen.SLICE).exists():
        raise FileExistsError("existing source lock/slice")
    raw = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        tasks = [pool.submit(fetch_one, year, fips) for year in frozen.YEARS for fips in FIPS]
        for task in concurrent.futures.as_completed(tasks):
            year, fips, body = task.result()
            path = ROOT / raw_path(year, fips)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != body:
                raise ValueError(f"cached official response changed for {year}/{fips}")
            path.write_bytes(body)
            raw[(year, fips)] = body
    if len(raw) != 408:
        raise ValueError("all 408 official state-year bodies required")
    projected = projections(raw)

    def download(canonical_url: str) -> bytes:
        year = int(canonical_url.split("/data/")[1].split("/")[0])
        if canonical_url != frozen.source_url(year):
            raise ValueError("unexpected registered Census URL")
        return projected[year]

    frozen.download = download
    built = frozen.build_slice()
    lock_path = ROOT / frozen.LOCK
    lock = json.loads(lock_path.read_text())
    lock["source_note"] = (
        "The eight raw_census year files are deterministic API-shaped projections, NOT direct "
        "HTTP responses from the key-gated api.census.gov URLs. The 408 original Census "
        "data.census.gov table-service response bodies are retained and hashed below. "
        "The registered fields, state/year roster, and estimator are unchanged. "
        "Alabama selected estimates were manually inspected before source lock; this run "
        "must be treated as exploratory calibration with zero public conversion credit.")
    lock["official_table_transport"] = {
        "publisher": "US Census Bureau",
        "service": SERVICE,
        "adapter": {"path": ADAPTER, "sha256": frozen.file_sha(ADAPTER)},
        "response_count": 408,
        "responses": [
            {"year": year, "state_fips": fips, "path": raw_path(year, fips),
             "url": url_for(year, fips), "sha256": sha(raw[(year, fips)])}
            for year in frozen.YEARS for fips in FIPS
        ],
        "projections": [
            {"year": year, "path": f"{frozen.RAW_DIR}/{year}.json",
             "sha256": sha(projected[year]), "direct_api_response": False}
            for year in frozen.YEARS
        ],
        "prelock_value_inspection": (
            "Alabama S2301_C03_002E estimates in all eight years and its 2024 MOE were "
            "printed during source availability probes before the lock."
        ),
    }
    for entry in lock["raw_census"]:
        entry["direct_api_response"] = False
        entry["retrieved_from"] = SERVICE
        entry["url_role"] = "canonical API field reference only; not the retrieval URL"
    lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    return {**built, "official_responses": 408, "transport": SERVICE,
            "prelock_value_inspection": True}


def verify_source() -> dict:
    frozen.locked()
    lock = json.loads((ROOT / frozen.LOCK).read_text())
    transport = lock["official_table_transport"]
    if (transport["service"] != SERVICE or transport["response_count"] != 408
            or transport["adapter"] != {"path": ADAPTER, "sha256": frozen.file_sha(ADAPTER)}):
        raise ValueError("official transport metadata differs")
    expected = [(year, fips) for year in frozen.YEARS for fips in FIPS]
    listed = [(int(e["year"]), e["state_fips"]) for e in transport["responses"]]
    if listed != expected:
        raise ValueError("official transport roster differs")
    raw = {}
    for entry in transport["responses"]:
        year, fips = int(entry["year"]), entry["state_fips"]
        if entry != {"year": year, "state_fips": fips,
                     "path": raw_path(year, fips), "url": url_for(year, fips),
                     "sha256": frozen.file_sha(raw_path(year, fips))}:
            raise ValueError(f"official response hash or path differs for {year}/{fips}")
        body = (ROOT / raw_path(year, fips)).read_bytes()
        parse_body(body, year, fips)
        raw[(year, fips)] = body
    projected = projections(raw)
    for year, entry in zip(frozen.YEARS, transport["projections"]):
        if entry != {"year": year, "path": f"{frozen.RAW_DIR}/{year}.json",
                     "sha256": sha(projected[year]), "direct_api_response": False}:
            raise ValueError(f"projection metadata differs for {year}")
        if (ROOT / entry["path"]).read_bytes() != projected[year]:
            raise ValueError(f"projection differs from official raw responses for {year}")
    return {"verified_official_responses": len(raw), "verified_projections": len(projected),
            "prelock_value_inspection": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fetch-lock", action="store_true")
    group.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(fetch_lock() if args.fetch_lock else verify_source(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
