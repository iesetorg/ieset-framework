"""Manual public-finance panel for wealth-tax forecast-vs-realized tests.

This fetcher intentionally reads a curated CSV instead of scraping arbitrary
budget pages. Each row must keep the forecast vintage and source URL so the
replication can test realized-vs-forecast gaps without losing provenance.

Expected input:
    data/manual/wealth_tax/revenue_forecast_realized.csv

Required columns:
    country_iso3, case_id, tax_name, forecast_vintage_year, revenue_year,
    forecast_revenue_local, realized_revenue_local, currency, source_url,
    methodology_url, notes
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from ._base import FetchResult, ROOT, utc_now, write_vintage

LICENSE = "mixed_public_finance_documents"
SERIES_ID = "revenue_forecast_realized"
INPUT = ROOT / "data" / "manual" / "wealth_tax" / f"{SERIES_ID}.csv"
REQUIRED = [
    "country_iso3",
    "case_id",
    "tax_name",
    "forecast_vintage_year",
    "revenue_year",
    "forecast_revenue_local",
    "realized_revenue_local",
    "currency",
    "source_url",
    "methodology_url",
    "notes",
]


class WealthTaxManualError(RuntimeError):
    pass


def fetch(series_id: str = SERIES_ID, *, vintage_utc: datetime | None = None) -> FetchResult:
    if series_id != SERIES_ID:
        raise WealthTaxManualError(f"unsupported series_id {series_id!r}; known: {SERIES_ID!r}")
    if not INPUT.exists():
        raise WealthTaxManualError(
            f"missing {INPUT.relative_to(ROOT)}; copy the template and fill sourced rows"
        )

    fetch_ts = utc_now()
    df = pd.read_csv(INPUT, dtype={"country_iso3": "string", "case_id": "string"})
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise WealthTaxManualError(f"{INPUT.relative_to(ROOT)} missing columns: {missing}")
    df = df[REQUIRED].copy()
    if df.empty:
        raise WealthTaxManualError(f"{INPUT.relative_to(ROOT)} has no data rows")

    for col in ("forecast_vintage_year", "revenue_year"):
        df[col] = pd.to_numeric(df[col], errors="raise").astype("Int64")
    for col in ("forecast_revenue_local", "realized_revenue_local"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[["forecast_revenue_local", "realized_revenue_local"]].isna().any().any():
        raise WealthTaxManualError("forecast and realized revenue columns must be numeric")
    if df["source_url"].isna().any() or df["source_url"].astype(str).str.len().lt(8).any():
        raise WealthTaxManualError("every row needs a source_url")

    out, sha = write_vintage(
        publisher="wealth_tax_manual",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="wealth_tax_manual",
        series_id=series_id,
        source_url=f"manual://{INPUT.relative_to(ROOT)}",
        methodology_url="manual://row-level-methodology_url",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="local currency revenue",
        currency=None,
        start_date=str(int(df["revenue_year"].min())),
        end_date=str(int(df["revenue_year"].max())),
        sha256=sha,
        parquet_path=out,
        extra={
            "input_file": str(INPUT.relative_to(ROOT)),
            "countries": sorted(df["country_iso3"].dropna().unique().tolist()),
            "cases": sorted(df["case_id"].dropna().unique().tolist()),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    result = fetch()
    print(f"OK rows={result.rows} {result.start_date}->{result.end_date}")
    print(f"   {Path(result.parquet_path).relative_to(ROOT)}")
