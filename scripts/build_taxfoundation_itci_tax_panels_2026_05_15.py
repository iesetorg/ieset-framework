#!/usr/bin/env python3
"""Build Tax Foundation ITCI tax-rate panels used by fiscal hypotheses.

Inputs:
- Tax Foundation International Tax Competitiveness Index final-data CSVs.

Outputs:
- `taxfoundation_itci:capital_gains_tax_rate_panel`
- `taxfoundation_itci:capital_gains_tax_cut_indicator_panel`
- `taxfoundation_itci:corporate_tax_rate_panel`
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, write_manifest, write_vintage  # noqa: E402


RAW_BASE = (
    "https://raw.githubusercontent.com/TaxFoundation/"
    "international-tax-competitiveness-index/master/final_data"
)
REPO_URL = "https://github.com/TaxFoundation/international-tax-competitiveness-index"
README_URL = f"{REPO_URL}#explanation-of-data"
YEARS = range(2014, 2026)


def fetch_csv(year: int) -> tuple[pd.DataFrame, str, str]:
    url = f"{RAW_BASE}/final_index_data_{year}.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "IESET data builder"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError(f"{url} returned no rows")
    return frame, url, digest


def as_percent(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.where(numeric.abs() > 1, numeric * 100)


def build_rate_panel(raw: pd.DataFrame, column: str, value_name: str) -> pd.DataFrame:
    panel = raw[["ISO_2", "ISO_3", "country", "year", column, "source_file", "source_sha256"]].copy()
    panel["country_iso3"] = panel["ISO_3"].str.upper()
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")
    panel["value"] = as_percent(panel[column])
    panel["variable"] = value_name
    panel = panel.dropna(subset=["country_iso3", "year", "value"])
    panel["year"] = panel["year"].astype(int)
    return panel[
        [
            "country_iso3",
            "year",
            "value",
            "variable",
            "country",
            "ISO_2",
            "source_file",
            "source_sha256",
        ]
    ].sort_values(["country_iso3", "year"])


def build_cut_indicator(cgt_panel: pd.DataFrame) -> pd.DataFrame:
    base = cgt_panel[["country_iso3", "year", "value", "country", "ISO_2", "source_file", "source_sha256"]].copy()
    base = base.sort_values(["country_iso3", "year"])
    base["previous_rate"] = base.groupby("country_iso3")["value"].shift(1)
    base["annual_change_pp"] = base["value"] - base["previous_rate"]
    base["large_cut_year"] = (base["annual_change_pp"] <= -10).astype(int)

    windows = []
    for _, row in base[base["large_cut_year"] == 1].iterrows():
        for offset in range(0, 4):
            windows.append(
                {
                    "country_iso3": row["country_iso3"],
                    "year": int(row["year"]) + offset,
                    "cut_event_year": int(row["year"]),
                }
            )
    if windows:
        window_df = pd.DataFrame(windows).drop_duplicates(["country_iso3", "year"])
        out = base.merge(window_df, on=["country_iso3", "year"], how="left")
        out["value"] = out["cut_event_year"].notna().astype(int)
    else:
        out = base.copy()
        out["cut_event_year"] = pd.NA
        out["value"] = 0

    out["variable"] = "capital_gains_tax_cut_indicator"
    return out[
        [
            "country_iso3",
            "year",
            "value",
            "variable",
            "country",
            "ISO_2",
            "previous_rate",
            "annual_change_pp",
            "cut_event_year",
            "source_file",
            "source_sha256",
        ]
    ].sort_values(["country_iso3", "year"])


def emit(
    *,
    frame: pd.DataFrame,
    series_id: str,
    units: str,
    source_url: str,
    fetch_ts: datetime,
    extra: dict,
) -> FetchResult:
    out, sha = write_vintage(
        publisher="taxfoundation_itci",
        series_id=series_id,
        frame=frame,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="taxfoundation_itci",
        series_id=series_id,
        source_url=source_url,
        methodology_url=README_URL,
        license="Tax Foundation public GitHub dataset; see repository terms",
        fetch_utc=fetch_ts,
        rows=len(frame),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(frame["year"].min())) if len(frame) else None,
        end_date=str(int(frame["year"].max())) if len(frame) else None,
        sha256=sha,
        parquet_path=out,
        extra=extra,
    )


def main() -> int:
    fetch_ts = utc_now()
    frames = []
    source_files = []
    for year in YEARS:
        frame, url, digest = fetch_csv(year)
        frame["source_file"] = url
        frame["source_sha256"] = digest
        frames.append(frame)
        source_files.append({"year": year, "url": url, "sha256": digest, "rows": len(frame)})

    raw = pd.concat(frames, ignore_index=True)
    cgt = build_rate_panel(raw, "capital_gains_rate", "capital_gains_tax_rate")
    corporate = build_rate_panel(raw, "corporate_rate", "corporate_tax_rate")
    cut = build_cut_indicator(cgt)
    source_url = f"{RAW_BASE}/final_index_data_2014.csv ... final_index_data_2025.csv"

    results = [
        emit(
            frame=cgt,
            series_id="capital_gains_tax_rate_panel",
            units="percentage points",
            source_url=source_url,
            fetch_ts=fetch_ts,
            extra={
                "variable_definition": (
                    "Tax Foundation ITCI capital_gains_rate: tax rate for capital gains after "
                    "imputation, credit, or offset; listed shares after extended holding period "
                    "when asset-specific rates vary."
                ),
                "country_count": int(cgt["country_iso3"].nunique()),
                "source_files": source_files,
            },
        ),
        emit(
            frame=cut,
            series_id="capital_gains_tax_cut_indicator_panel",
            units="0/1 indicator",
            source_url=source_url,
            fetch_ts=fetch_ts,
            extra={
                "definition": (
                    "Equals 1 in the year of and three following years after a country records "
                    "a capital-gains-rate decline of at least 10 percentage points."
                ),
                "event_count": int(cut["cut_event_year"].notna().sum()),
                "source_files": source_files,
            },
        ),
        emit(
            frame=corporate,
            series_id="corporate_tax_rate_panel",
            units="percentage points",
            source_url=source_url,
            fetch_ts=fetch_ts,
            extra={
                "variable_definition": "Tax Foundation ITCI corporate_rate: top marginal corporate tax rate.",
                "country_count": int(corporate["country_iso3"].nunique()),
                "source_files": source_files,
            },
        ),
    ]

    manifest = write_manifest(results)
    audit = ROOT / "engine" / "audits" / f"taxfoundation_itci_tax_panel_build_{fetch_ts.strftime('%Y-%m-%dT%H%M%SZ')}.json"
    audit.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2) + "\n")
    for result in results:
        print(
            f"OK {result.publisher}:{result.series_id} rows={result.rows} "
            f"period={result.start_date}->{result.end_date} vintage={result.parquet_path.relative_to(ROOT)}"
        )
    print(f"manifest: {manifest.relative_to(ROOT)}")
    print(f"audit: {audit.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
