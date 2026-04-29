"""European Environment Agency (EEA) fetcher.

Endpoint: https://www.eea.europa.eu/en/datahub  (data hub item viewer)
Bulk CSV/zip downloads ship from the EEA SDI Datashare (sdi.eea.europa.eu)
and the discomap host (discomap.eea.europa.eu). Auth: none.
License: cc_by_4_0 (EEA reuse policy — open with attribution).

Two series are wired:
  - eu_ets_verified_emissions  — EU Emissions Trading System verified
        emissions per installation/year (data hub item 9d3fbb4f-...).
  - greenhouse_gas_inventory   — Member-State greenhouse gas inventory,
        annual CRF reporting under the EU Climate Monitoring Mechanism
        (data hub item 4b8d1744-...).

The EEA migrates download URLs across vintages — the data hub item *page*
is stable but the underlying signed Datashare token rotates. We accept a
list of candidate URLs per series (current vintage URLs first, then
documented mirrors) and try each in turn. If none respond, we fall back
to a small embedded bootstrap row so downstream code (validate_specs,
import-time sanity checks, manifest scaffolding) keeps working without
the network. The manifest sha256 makes the live-vs-bootstrap distinction
auditable post-hoc.

Returned panel columns: country_iso3, year, value, plus passthrough columns.
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "cc_by_4_0"

# EEA country labels -> ISO3. Covers EU-27 + EEA-EFTA + UK (legacy reporter).
_COUNTRY_TO_ISO3: dict[str, str] = {
    "Austria": "AUT", "Belgium": "BEL", "Bulgaria": "BGR", "Croatia": "HRV",
    "Cyprus": "CYP", "Czechia": "CZE", "Czech Republic": "CZE",
    "Denmark": "DNK", "Estonia": "EST", "Finland": "FIN", "France": "FRA",
    "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN", "Iceland": "ISL",
    "Ireland": "IRL", "Italy": "ITA", "Latvia": "LVA", "Liechtenstein": "LIE",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Malta": "MLT",
    "Netherlands": "NLD", "Norway": "NOR", "Poland": "POL", "Portugal": "PRT",
    "Romania": "ROU", "Slovakia": "SVK", "Slovenia": "SVN", "Spain": "ESP",
    "Sweden": "SWE", "Switzerland": "CHE", "Türkiye": "TUR", "Turkey": "TUR",
    "United Kingdom": "GBR",
    # ISO2 fallbacks used in some EEA dumps
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "HR": "HRV", "CY": "CYP",
    "CZ": "CZE", "DK": "DNK", "EE": "EST", "FI": "FIN", "FR": "FRA",
    "DE": "DEU", "EL": "GRC", "GR": "GRC", "HU": "HUN", "IS": "ISL",
    "IE": "IRL", "IT": "ITA", "LV": "LVA", "LI": "LIE", "LT": "LTU",
    "LU": "LUX", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
    "PT": "PRT", "RO": "ROU", "SK": "SVK", "SI": "SVN", "ES": "ESP",
    "SE": "SWE", "CH": "CHE", "TR": "TUR", "UK": "GBR", "GB": "GBR",
}


SUPPORTED: dict[str, dict[str, Any]] = {
    "eu_ets_verified_emissions": {
        "desc": "EU ETS verified emissions by installation/year (tCO2e)",
        "frequency": "annual",
        "units": "tonnes CO2-equivalent",
        "datahub_item": "9d3fbb4f-b66d-4081-a23c-4abb12fdebed",
        "methodology_url": (
            "https://www.eea.europa.eu/en/datahub/datahubitem-view/"
            "9d3fbb4f-b66d-4081-a23c-4abb12fdebed"
        ),
        # Candidate bulk-download URLs. EEA rotates the signed Datashare
        # token across vintages; we keep a small ordered list and fall
        # through. The discomap mirror is the most stable historical path.
        "candidates": [
            "https://sdi.eea.europa.eu/datashare/s/CDhpAg2WkaCDXsH/download",
            "https://www.eea.europa.eu/data-and-maps/data/european-union-emissions-trading-scheme-17/eu-ets-data-download-latest/eu_ets-data-from-the-eu-transaction-log/at_download/file",
            "https://discomap.eea.europa.eu/App/EUETS/data/EUETS_verified_emissions.csv",
        ],
        "country_col_candidates": ["COUNTRY", "country", "Country", "MS", "MEMBER_STATE"],
        "year_col_candidates": ["YEAR", "year", "Year", "REPORTING_YEAR"],
        "value_col_candidates": [
            "VERIFIED_EMISSIONS", "verified_emissions", "Verified emissions",
            "VALUE", "value",
        ],
    },
    "greenhouse_gas_inventory": {
        "desc": "Member-State GHG inventory, annual CRF reporting (kt CO2e)",
        "frequency": "annual",
        "units": "kilotonnes CO2-equivalent",
        "datahub_item": "4b8d1744-1bfa-4666-9d9c-cf4f0cf52866",
        "methodology_url": (
            "https://www.eea.europa.eu/en/datahub/datahubitem-view/"
            "4b8d1744-1bfa-4666-9d9c-cf4f0cf52866"
        ),
        "candidates": [
            "https://sdi.eea.europa.eu/datashare/s/G37QqfSMx7g4XBQ/download",
            "https://www.eea.europa.eu/data-and-maps/data/national-emissions-reported-to-the-unfccc-and-to-the-eu-greenhouse-gas-monitoring-mechanism-23/european-union-greenhouse-gas-inventory-1/eea-greenhouse-gases-data-viewer/at_download/file",
            "https://discomap.eea.europa.eu/App/GhgInventory/data/ghg_inventory_eu.csv",
        ],
        "country_col_candidates": ["Country", "country", "COUNTRY", "Party"],
        "year_col_candidates": ["Year", "year", "YEAR"],
        "value_col_candidates": ["emissions", "Emissions", "value", "Value", "EMISSIONS"],
    },
}


class EeaError(RuntimeError):
    pass


def _try_download(urls: list[str]) -> tuple[pd.DataFrame, str]:
    """Try each candidate URL until one returns a parsable CSV."""
    last_err: Exception | None = None
    headers = {"User-Agent": "Mozilla/5.0 ieset-fetcher (+https://ieset.dev)"}
    for url in urls:
        try:
            r = requests.get(url, timeout=180, headers=headers, allow_redirects=True)
        except requests.RequestException as e:
            last_err = e
            continue
        if r.status_code != 200 or not r.content:
            last_err = EeaError(f"HTTP {r.status_code} for {url}")
            continue

        body = r.content
        # Try zip wrapper first
        try:
            z = zipfile.ZipFile(io.BytesIO(body))
            csv_name = next(
                (n for n in z.namelist() if n.lower().endswith((".csv", ".txt", ".tsv"))),
                None,
            )
            if csv_name is None:
                last_err = EeaError(f"no CSV in zip from {url}: {z.namelist()}")
                continue
            with z.open(csv_name) as f:
                df = pd.read_csv(f, low_memory=False, encoding="latin-1",
                                 sep=None, engine="python")
            return df, url
        except zipfile.BadZipFile:
            pass

        # Try plain CSV / TSV
        try:
            df = pd.read_csv(io.BytesIO(body), low_memory=False,
                             encoding="latin-1", sep=None, engine="python")
            if df.shape[1] >= 2 and len(df) > 0:
                return df, url
            last_err = EeaError(f"degenerate CSV from {url} shape={df.shape}")
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue

    raise EeaError(f"all EEA candidate URLs failed: {last_err}")


def _bootstrap_frame(series_id: str) -> pd.DataFrame:
    """Tiny embedded panel returned when every candidate URL is unreachable.

    This is *not* the real published data; it carries a single sentinel row
    so the manifest write + downstream sanity checks succeed in airgapped
    environments. The fetcher emits an `extra.bootstrap=True` flag which the
    coverage validator treats as 'fetcher implemented but live data not yet
    captured'. Real vintage capture overwrites it on the next online run.
    """
    return pd.DataFrame(
        [
            {
                "country_iso3": "EUR",
                "year": 2020,
                "value": float("nan"),
                "note": f"bootstrap-stub for {series_id}; live EEA URL unreachable at fetch time",
            }
        ]
    )


def _normalise(df: pd.DataFrame, spec: dict[str, Any]) -> pd.DataFrame:
    """Normalise a raw EEA CSV to (country_iso3, year, value, ...)."""
    df.columns = [str(c).strip() for c in df.columns]

    def _pick(cands: list[str]) -> str | None:
        lower = {c.lower(): c for c in df.columns}
        for cand in cands:
            if cand in df.columns:
                return cand
            if cand.lower() in lower:
                return lower[cand.lower()]
        return None

    country_col = _pick(spec["country_col_candidates"])
    year_col = _pick(spec["year_col_candidates"])
    value_col = _pick(spec["value_col_candidates"])

    if country_col is None or year_col is None or value_col is None:
        # Surface partial info to ease debugging — but don't raise; degrade
        # to bootstrap-shaped output so downstream scaffolding still moves.
        raise EeaError(
            f"unexpected EEA columns: country={country_col} year={year_col} "
            f"value={value_col}; available={df.columns.tolist()[:30]}"
        )

    out = pd.DataFrame(
        {
            "country_raw": df[country_col].astype(str),
            "year": pd.to_numeric(df[year_col], errors="coerce").astype("Int64"),
            "value": pd.to_numeric(df[value_col], errors="coerce"),
        }
    )
    out["country_iso3"] = out["country_raw"].map(_COUNTRY_TO_ISO3)
    out = out.dropna(subset=["country_iso3", "year"]).reset_index(drop=True)
    return out[["country_iso3", "year", "value", "country_raw"]]


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch an EEA series by IESET series_id.

    series_id: one of the keys in SUPPORTED.
    """
    if series_id not in SUPPORTED:
        raise EeaError(
            f"unsupported EEA series_id {series_id!r}; "
            f"known: {sorted(SUPPORTED)}"
        )
    spec = SUPPORTED[series_id]
    fetch_ts = utc_now()

    bootstrap = False
    src_url = spec["candidates"][0]
    try:
        raw, src_url = _try_download(spec["candidates"])
        df = _normalise(raw, spec)
        if df.empty:
            raise EeaError(f"EEA {series_id} returned no usable rows")
    except EeaError as e:
        # Fall back to bootstrap so the manifest entry exists and the
        # registry resolves; mark explicitly in `extra` for auditability.
        bootstrap = True
        df = _bootstrap_frame(series_id)
        df.attrs["bootstrap_reason"] = str(e)

    path_out, sha = write_vintage(
        publisher="eea",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = end = None
    if "year" in df.columns and df["year"].notna().any():
        start = str(int(df["year"].min()))
        end = str(int(df["year"].max()))

    return FetchResult(
        publisher="eea",
        series_id=series_id,
        source_url=src_url,
        methodology_url=spec["methodology_url"],
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec.get("frequency", "annual"),
        units=spec.get("units", "per dataset metadata"),
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "datahub_item": spec.get("datahub_item"),
            "desc": spec.get("desc"),
            "bootstrap": bootstrap,
            "bootstrap_reason": df.attrs.get("bootstrap_reason") if bootstrap else None,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from data.fetchers import eea as _self

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series", default="greenhouse_gas_inventory",
                   choices=sorted(SUPPORTED))
    args = p.parse_args()
    res = _self.fetch(args.series)
    print(f"OK rows={res.rows} {res.start_date}->{res.end_date} bootstrap={res.extra.get('bootstrap')}")
    print(f"   {res.parquet_path}")
