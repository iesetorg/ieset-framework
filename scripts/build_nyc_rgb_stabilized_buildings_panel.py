#!/usr/bin/env python3
"""Build the NYC rent-stabilized building registry panel from the NYC Rent
Guidelines Board stabilized building lists (DHCR building file, 2024).

Promotes inventory source `nyc_rent_guidelines_board_stabilized_lists`
(city treatment-registry exemplar) from scout_reported_unverified to
endpoint_verified: the RGB resource page pins five per-borough PDFs with one
row per stabilized building (ZIP, address, county code, status codes, BLOCK,
LOT). This builder downloads the pinned files, parses the fixed-column text
layout, validates rows, writes the parsed rows as a pinned vintage parquet,
and emits a per-borough/per-ZIP panel joined to the IESET city spine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]

RGB_PAGE = "https://rentguidelinesboard.cityofnewyork.us/resources/rent-stabilized-building-lists/"
RGB_UPLOAD = "https://rentguidelinesboard.cityofnewyork.us/wp-content/uploads/2025/12"
BOROUGHS = {
    "manhattan": "New York County (Manhattan)",
    "brooklyn": "Kings County (Brooklyn)",
    "bronx": "Bronx County (The Bronx)",
    "queens": "Queens County (Queens)",
    "staten-island": "Richmond County (Staten Island)",
}
BOROUGH_CITY_NAMES = {
    "manhattan": "NEW YORK",
    "brooklyn": "BROOKLYN",
    "bronx": "BRONX",
    "queens": "QUEENS",
    "staten-island": "STATEN ISLAND",
}
LIST_YEAR = 2024
NYC_IESET_CITY_ID = "ghsl_ucdb_r2024a:8099"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

ZIP_RE = re.compile(r"^\d{5}$")
PAGE_FOOTER_RE = re.compile(r"^\d{1,3}$")


PDF_FILE_NAMES = {
    "manhattan": "Manhattan",
    "brooklyn": "Brooklyn",
    "bronx": "Bronx",
    "queens": "Queens",
    "staten-island": "Staten-Island",
}


def pdf_url(borough: str) -> str:
    return f"{RGB_UPLOAD}/{LIST_YEAR}-DHCR-Bldg-File-{PDF_FILE_NAMES[borough]}.pdf"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def parse_building_line(line: str, borough: str) -> dict[str, Any] | None:
    """Parse one fixed-column text row from a DHCR building-file PDF page.

    Layout: ZIP BLDGNO1 STREET1 STSUFX1 [BLDGNO2 STREET2 STSUFX2] CITY
    COUNTYSTATUS1 [STATUS2 [STATUS3]] BLOCK LOT — fields are space-separated
    in the extracted text; BLOCK and LOT are the last two integer tokens and
    the borough's city name anchors the address/status split.
    """
    tokens = line.split()
    if len(tokens) < 6:
        return None
    if not ZIP_RE.match(tokens[0]):
        return None
    zip_code = tokens[0]
    try:
        block = int(tokens[-2])
        lot = int(tokens[-1])
    except ValueError:
        return None
    if block <= 0 or lot <= 0:
        return None
    city_name = BOROUGH_CITY_NAMES[borough]
    city_tokens = city_name.split()
    city_index = None
    for i in range(len(tokens) - len(city_tokens) - 2):
        if tokens[i : i + len(city_tokens)] == city_tokens:
            city_index = i
            break
    if city_index is None or city_index < 2:
        return None
    address_tokens = tokens[1:city_index]
    tail_tokens = tokens[city_index + len(city_tokens) : -2]
    if not address_tokens or not tail_tokens:
        return None
    county_code = tail_tokens[0]
    statuses = tail_tokens[1:]
    if not statuses:
        return None
    return {
        "zip": zip_code,
        "address": " ".join(address_tokens),
        "county_code": county_code,
        "status_codes": " ".join(statuses),
        "block": block,
        "lot": lot,
        "borough": borough,
    }


def parse_pdf_bytes(data: bytes, borough: str, pdfplumber) -> list[dict[str, Any]]:
    import io

    rows: list[dict[str, Any]] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped or PAGE_FOOTER_RE.match(stripped):
                    continue
                if stripped.startswith("List of ") or stripped.startswith("ZIP "):
                    continue
                parsed = parse_building_line(stripped, borough)
                if parsed is not None:
                    rows.append(parsed)
    return rows


def default_fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def build(
    fetch: Callable[[str], bytes] = default_fetch,
    run_utc: datetime | None = None,
    boroughs: dict[str, str] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Run the fetch→parse→validate→vintage→panel→manifest pipeline.

    `boroughs` narrows the run (used by tests to drive the full pipeline on a
    pinned fixture borough); production runs cover all five boroughs. `root`
    redirects artifact output (tests write to tmp_path; production uses the
    repository root).
    """
    import pdfplumber

    selected = boroughs or BOROUGHS
    root = root or ROOT
    run_utc = run_utc or datetime.now(tz=timezone.utc)
    stamp = utc_stamp(run_utc)

    entries: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    raw_dir = root / "data" / "raw" / "city_level" / "nyc_rgb_stabilized_buildings"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for borough in selected:
        url = pdf_url(borough)
        data = fetch(url)
        raw_path = raw_dir / f"{LIST_YEAR}-{borough}.pdf"
        if not raw_path.exists():
            raw_path.write_bytes(data)
        rows = parse_pdf_bytes(data, borough, pdfplumber)
        if not rows:
            raise ValueError(f"no building rows parsed from {url}")
        all_rows.extend(rows)
        entries.append(
            {
                "source_id": "nyc_rent_guidelines_board_stabilized_lists",
                "publisher": "NYC Rent Guidelines Board (DHCR building file)",
                "url": url,
                "sha256": sha256_bytes(data),
                "bytes": len(data),
                "rows_parsed": len(rows),
                "borough": borough,
                "list_year": LIST_YEAR,
                "transport": "direct",
            }
        )

    frame = pd.DataFrame(all_rows)
    frame["list_year"] = LIST_YEAR
    frame["ieset_city_id"] = NYC_IESET_CITY_ID

    vintage_dir = root / "data" / "vintages" / "nyc_rgb_stabilized_buildings"
    vintage_dir.mkdir(parents=True, exist_ok=True)
    vintage_path = vintage_dir / f"{LIST_YEAR}_building_list@{stamp}.parquet"
    frame.to_parquet(vintage_path, index=False)

    borough_panel = (
        frame.groupby(["ieset_city_id", "borough", "list_year"])
        .agg(stabilized_buildings=("block", "size"), zips_covered=("zip", "nunique"))
        .reset_index()
    )
    zip_panel = (
        frame.groupby(["ieset_city_id", "borough", "zip", "list_year"])
        .agg(stabilized_buildings=("block", "size"))
        .reset_index()
        .rename(columns={"zip": "zip_code"})
    )
    panel = borough_panel.merge(zip_panel, on=["ieset_city_id", "borough", "list_year"], suffixes=("", "_zip"))
    panel = panel.rename(columns={"stabilized_buildings_zip": "zip_stabilized_buildings"})
    panel["source"] = "nyc_rent_guidelines_board_stabilized_lists"

    output_path = root / "data" / "derived" / "nyc_rgb_stabilized_buildings_panel.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, index=False)

    manifest_dir = root / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"fetch_run_{stamp}_nyc_rgb_stabilized_buildings.yaml"
    manifest = {
        "run_utc": stamp,
        "pipeline": "nyc_rgb_stabilized_buildings_panel",
        "resource_page": RGB_PAGE,
        "entries": entries,
        "artifacts": {
            "vintage_parquet": str(vintage_path.relative_to(root)),
            "vintage_sha256": sha256_path(vintage_path),
            "panel_parquet": str(output_path.relative_to(root)),
            "panel_sha256": sha256_path(output_path),
            "panel_rows": len(panel),
            "total_stabilized_buildings": int(frame.shape[0]),
        },
    }
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
    return {
        "rows": len(frame),
        "panel_rows": len(panel),
        "manifest": str(manifest_path.relative_to(root)),
        "panel": str(output_path.relative_to(root)),
        "vintage": str(vintage_path.relative_to(root)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit result as JSON")
    args = parser.parse_args()
    result = build()
    if args.json:
        print(json.dumps(result))
    else:
        print(f"rows parsed: {result['rows']}")
        print(f"panel: {result['panel']} ({result['panel_rows']} rows)")
        print(f"vintage: {result['vintage']}")
        print(f"manifest: {result['manifest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
