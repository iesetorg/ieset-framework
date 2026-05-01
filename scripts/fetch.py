#!/usr/bin/env python3
"""Fetch one series from one publisher; write vintage + manifest entry.

Publishers and their status are defined in data/fetchers/publishers.yaml.
This CLI dispatches through data.fetchers.REGISTRY, which only exposes
publishers whose status is 'ready' AND whose fetcher_module imports cleanly.

Examples:
    FRED_API_KEY=... python scripts/fetch.py fred M2SL
    python scripts/fetch.py world_bank_wdi NY.GDP.PCAP.KD --countries USA;GBR;JPN
    python scripts/fetch.py wgi GOV_WGI_GE.EST --countries NOR;SWE;DNK
    python scripts/fetch.py imf GGXWDG_NGDP --countries USA,GBR,DEU
    python scripts/fetch.py bis WS_SPP
    python scripts/fetch.py oecd 'OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0' --start 2020-01 --end 2023-12
    python scripts/fetch.py shiller ie_data
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers import REGISTRY
from data.fetchers._base import write_manifest


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("publisher", help=f"One of: {sorted(REGISTRY)}")
    p.add_argument("series_id")
    p.add_argument("--countries", default=None, help="Country filter; format varies per publisher (see publisher-module docstrings)")
    p.add_argument("--key", default=None, help="SDMX key filter (oecd, bis only)")
    p.add_argument("--start", default=None, help="OECD startPeriod")
    p.add_argument("--end", default=None, help="OECD endPeriod")
    args = p.parse_args()

    if args.publisher not in REGISTRY:
        print(f"unknown publisher {args.publisher!r}; known: {sorted(REGISTRY)}", file=sys.stderr)
        return 2

    mod = REGISTRY[args.publisher]
    kwargs: dict = {}
    # Publisher-specific argument wiring — kept loose to avoid a dispatch table per fetcher.
    if args.countries is not None:
        if args.publisher in ("imf", "imf_weo"):
            kwargs["countries"] = [c.strip() for c in args.countries.replace("/", ",").split(",") if c.strip()]
        elif args.publisher == "wid":
            kwargs["country_filter"] = [c.strip() for c in args.countries.replace("/", ",").split(",") if c.strip()]
        else:
            kwargs["countries"] = args.countries
    if args.key is not None:
        kwargs["key"] = args.key
    if args.start is not None:
        kwargs["start_period"] = args.start
    if args.end is not None:
        kwargs["end_period"] = args.end

    result = mod.fetch(args.series_id, **kwargs)
    manifest_path = write_manifest([result])
    print(f"OK  publisher={result.publisher} series={result.series_id} rows={result.rows}")
    print(f"    period:   {result.start_date} → {result.end_date}  freq={result.frequency}")
    print(f"    vintage:  {result.parquet_path.relative_to(ROOT)}")
    print(f"    sha256:   {result.sha256}")
    print(f"    manifest: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
