#!/usr/bin/env python3
"""Build narrow Laeven-Valencia bridge series for financial_liberalisation_crisis_risk.

The generic panel runner resolves concrete ``publisher:series`` parquet vintages,
but the hypothesis previously cited broad ``constructed:*`` tokens. This script
materializes the three outcome series needed by the spec as normal
``country_iso3, year, value`` panels.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
HYPOTHESIS = ROOT / "hypotheses" / "growth" / "financial_liberalisation_crisis_risk.yaml"
LV_DIR = ROOT / "data" / "vintages" / "laeven_valencia"
WDI_DIR = ROOT / "data" / "vintages" / "world_bank_wdi"

COUNTRY_NAME_TO_ISO3 = {
    "Argentina": "ARG",
    "Bolivia": "BOL",
    "Brazil": "BRA",
    "Bulgaria": "BGR",
    "Chile": "CHL",
    "Colombia": "COL",
    "Croatia": "HRV",
    "Czech Republic": "CZE",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "Hungary": "HUN",
    "India": "IND",
    "Indonesia": "IDN",
    "Kazakhstan": "KAZ",
    "Korea": "KOR",
    "Malaysia": "MYS",
    "Mexico": "MEX",
    "Morocco": "MAR",
    "Pakistan": "PAK",
    "Peru": "PER",
    "Philippines": "PHL",
    "Poland": "POL",
    "Romania": "ROU",
    "Russia": "RUS",
    "South Africa": "ZAF",
    "Sri Lanka": "LKA",
    "Thailand": "THA",
    "Tunisia": "TUN",
    "Turkey": "TUR",
    "Ukraine": "UKR",
    "Uruguay": "URY",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
}


def latest(directory: Path, pattern: str) -> Path:
    files = sorted(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no files matched {directory / pattern}")
    return files[-1]


def clean_country(raw: object) -> str | None:
    if raw is None or pd.isna(raw):
        return None
    name = re.sub(r"\s+", " ", str(raw)).strip()
    name = re.sub(r"\s+\d+/$", "", name).strip()
    if not name or name.lower().startswith("source:"):
        return None
    return name


def parse_years(raw: object) -> set[int]:
    if raw is None or pd.isna(raw):
        return set()
    return {int(y) for y in re.findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", str(raw))}


def load_sample() -> tuple[list[str], int, int]:
    spec = yaml.safe_load(HYPOTHESIS.read_text())
    sample = spec["sample"]
    countries = [str(c).strip().upper() for c in sample["countries"]]
    start, end = [int(x) for x in sample["period"]]
    return countries, start, end


def base_grid(countries: list[str], start: int, end: int) -> pd.DataFrame:
    return pd.MultiIndex.from_product(
        [countries, range(start, end + 1)], names=["country_iso3", "year"]
    ).to_frame(index=False)


def load_event_years() -> tuple[dict[str, set[int]], dict[str, set[int]]]:
    crisis_years = pd.read_parquet(latest(LV_DIR, "crisis_years@*.parquet"))
    banking: dict[str, set[int]] = {}
    currency: dict[str, set[int]] = {}
    for _, row in crisis_years.iterrows():
        country = clean_country(row.get("Country"))
        if not country:
            continue
        iso3 = COUNTRY_NAME_TO_ISO3.get(country)
        if not iso3:
            continue
        banking.setdefault(iso3, set()).update(
            parse_years(row.get("Systemic Banking Crisis (starting date)"))
        )
        currency.setdefault(iso3, set()).update(parse_years(row.get("Currency Crisis")))
    return banking, currency


def indicator_panel(
    countries: list[str],
    start: int,
    end: int,
    events: dict[str, set[int]],
    series_name: str,
    vintage_utc: str,
) -> Path:
    out = base_grid(countries, start, end)
    event_pairs = {
        (country, year)
        for country, years in events.items()
        if country in countries
        for year in years
        if start <= year <= end
    }
    out["value"] = [
        1.0 if (country, int(year)) in event_pairs else 0.0
        for country, year in out[["country_iso3", "year"]].itertuples(index=False)
    ]
    out["source_note"] = "Laeven-Valencia Systemic Banking Crises Database II, crisis_years sheet"
    path = LV_DIR / f"{series_name}@{vintage_utc}.parquet"
    out.to_parquet(path, index=False)
    return path


def load_real_gdp_pc() -> pd.DataFrame:
    gdp = pd.read_parquet(latest(WDI_DIR, "NY.GDP.PCAP.KD@*.parquet"))
    gdp = gdp[["country_iso3", "year", "value"]].copy()
    gdp["country_iso3"] = gdp["country_iso3"].astype(str).str.upper()
    gdp["year"] = pd.to_numeric(gdp["year"], errors="coerce").astype("Int64")
    gdp["value"] = pd.to_numeric(gdp["value"], errors="coerce")
    return gdp.dropna(subset=["country_iso3", "year", "value"])


def peak_to_trough_loss(
    gdp: pd.DataFrame,
    country: str,
    event_year: int,
) -> float:
    country_gdp = gdp[gdp["country_iso3"] == country]
    peak_window = country_gdp[country_gdp["year"].between(event_year - 1, event_year)]
    trough_window = country_gdp[country_gdp["year"].between(event_year, event_year + 3)]
    if peak_window.empty or trough_window.empty:
        return np.nan
    peak = float(peak_window["value"].max())
    trough = float(trough_window["value"].min())
    if not np.isfinite(peak) or peak <= 0 or not np.isfinite(trough):
        return np.nan
    return max((peak - trough) / peak * 100.0, 0.0)


def output_loss_panel(
    countries: list[str],
    start: int,
    end: int,
    banking: dict[str, set[int]],
    currency: dict[str, set[int]],
    vintage_utc: str,
) -> Path:
    gdp = load_real_gdp_pc()
    out = base_grid(countries, start, end)
    out["value"] = 0.0
    event_pairs = {
        (country, year)
        for source in (banking, currency)
        for country, years in source.items()
        if country in countries
        for year in years
        if start <= year <= end
    }
    for country, year in sorted(event_pairs):
        loss = peak_to_trough_loss(gdp, country, year)
        out.loc[
            (out["country_iso3"] == country) & (out["year"] == year),
            "value",
        ] = loss
    out["source_note"] = (
        "Derived from Laeven-Valencia banking/currency event years and WDI "
        "NY.GDP.PCAP.KD; loss=max GDP pc in [T-1,T] to min in [T,T+3]."
    )
    path = LV_DIR / f"peak_to_trough_gdp_loss_crisis_years@{vintage_utc}.parquet"
    out.to_parquet(path, index=False)
    return path


def main() -> None:
    countries, start, end = load_sample()
    banking, currency = load_event_years()
    vintage_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    paths = [
        indicator_panel(countries, start, end, banking, "banking_crisis_indicator", vintage_utc),
        indicator_panel(countries, start, end, currency, "currency_crisis_indicator", vintage_utc),
        output_loss_panel(countries, start, end, banking, currency, vintage_utc),
    ]
    for path in paths:
        df = pd.read_parquet(path)
        print(f"{path.relative_to(ROOT)} rows={len(df)} nonzero={(df['value'] > 0).sum()}")


if __name__ == "__main__":
    main()
