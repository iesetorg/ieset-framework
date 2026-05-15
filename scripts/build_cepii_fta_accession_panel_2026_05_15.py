#!/usr/bin/env python3
"""Build country-year FTA accession treatment panels from CEPII Gravity.

CEPII Gravity V202211 carries WTO RTA-IS trade-agreement variables at the
directed country-pair-year level. This script streams the official CSV zip and
collapses it into country-year panels suitable for the generic IESET runners.
"""
from __future__ import annotations

import csv
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RAW_ZIP = ROOT / "data/raw/cepii/Gravity_csv_V202211.zip"
OUT_DIR = ROOT / "data/vintages/cepii"
MANIFEST_DIR = ROOT / "data/manifests"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H%M%SZ")


def truthy(value: object) -> bool:
    try:
        return float(str(value).strip()) > 0
    except Exception:
        return False


def main() -> int:
    if not RAW_ZIP.exists():
        raise SystemExit(f"missing CEPII Gravity zip: {RAW_ZIP}")

    partners: dict[tuple[str, int], set[str]] = defaultdict(set)
    countries: set[str] = set()
    years: set[int] = set()

    with zipfile.ZipFile(RAW_ZIP) as zf:
        with zf.open("Gravity_V202211.csv") as raw:
            text = (line.decode("utf-8", errors="replace") for line in raw)
            reader = csv.DictReader(text)
            for row in reader:
                try:
                    year = int(row["year"])
                except Exception:
                    continue
                if year < 1948 or year > 2020:
                    continue
                origin = str(row.get("iso3_o") or "").strip().upper()
                dest = str(row.get("iso3_d") or "").strip().upper()
                if not origin or not dest or origin == dest:
                    continue
                countries.update([origin, dest])
                years.add(year)
                if truthy(row.get("fta_wto")):
                    partners[(origin, year)].add(dest)
                    partners[(dest, year)].add(origin)

    rows: list[dict[str, object]] = []
    all_years = range(min(years), max(years) + 1)
    for country in sorted(countries):
        previous_count = 0
        for year in all_years:
            partner_count = len(partners.get((country, year), set()))
            new_partner_count = max(partner_count - previous_count, 0)
            rows.append(
                {
                    "country_iso3": country,
                    "year": year,
                    "value": 1.0 if year >= 1990 and new_partner_count > 0 else 0.0,
                    "fta_partner_count": partner_count,
                    "new_fta_partner_count": new_partner_count,
                }
            )
            previous_count = partner_count

    panel = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    indicator_path = OUT_DIR / f"fta_accession_indicator@{stamp}.parquet"
    count_path = OUT_DIR / f"fta_partner_count@{stamp}.parquet"
    panel[["country_iso3", "year", "value"]].to_parquet(indicator_path, index=False)
    panel[["country_iso3", "year", "fta_partner_count"]].rename(
        columns={"fta_partner_count": "value"}
    ).to_parquet(count_path, index=False)

    manifest = {
        "run_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "CEPII Gravity V202211 official CSV zip",
        "source_url": "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip",
        "methodology_url": "https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf",
        "entries": [
            {
                "publisher": "cepii",
                "series_id": "fta_accession_indicator",
                "parquet_path": str(indicator_path.relative_to(ROOT)),
                "source_url": "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip",
                "methodology_url": "https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf",
                "rows": int(len(panel)),
                "start_date": int(panel["year"].min()),
                "end_date": int(panel["year"].max()),
                "frequency": "annual",
                "units": "binary indicator for first year with expanded WTO RTA partner coverage, 1990+",
            },
            {
                "publisher": "cepii",
                "series_id": "fta_partner_count",
                "parquet_path": str(count_path.relative_to(ROOT)),
                "source_url": "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip",
                "methodology_url": "https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf",
                "rows": int(len(panel)),
                "start_date": int(panel["year"].min()),
                "end_date": int(panel["year"].max()),
                "frequency": "annual",
                "units": "count of partner ISO3s with CEPII fta_wto == 1",
            },
        ],
    }
    manifest_path = MANIFEST_DIR / f"fetch_run_{stamp}_cepii_fta_accession.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    print(f"wrote {indicator_path.relative_to(ROOT)}")
    print(f"wrote {count_path.relative_to(ROOT)}")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
