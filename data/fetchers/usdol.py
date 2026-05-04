"""U.S. Department of Labor Wage and Hour Division fetcher.

Currently supported:
  state_minimum_wage_history

Source:
  https://www.dol.gov/agencies/whd/state/minimum-wage/history

The DOL table reports selected January-1 state minimum-wage rates from 1968
through 2024, plus a federal FLSA row. The IESET treatment panel uses the
effective floor for FLSA-covered workers: max(parsed state rate, parsed federal
rate), with federal fallback when a state has no state minimum-wage law.

Raw table cells, parsed lows/highs, and parser notes are retained because older
rows contain ranges, footnotes, and non-hourly entries.
"""
from __future__ import annotations

import io
import re
import subprocess
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

SOURCE_URL = "https://www.dol.gov/agencies/whd/state/minimum-wage/history"
LICENSE = "public_domain_us_gov"
METHODOLOGY = SOURCE_URL

SUPPORTED = {"state_minimum_wage_history"}

STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN",
    "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "Guam": "GU", "Puerto Rico": "PR", "U.S. Virgin Islands": "VI",
}

STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15",
    "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
    "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56", "GU": "66", "PR": "72", "VI": "78",
}


class UsdolError(RuntimeError):
    pass


def _year_from_column(col: object) -> int | None:
    m = re.search(r"\b(19\d{2}|20\d{2})\b", str(col))
    return int(m.group(1)) if m else None


def _parse_rate(raw: object) -> tuple[float | None, float | None, str]:
    if raw is None or pd.isna(raw):
        return None, None, "missing"
    text = str(raw).strip()
    if not text or text in {"...", "N.A.", "nan"}:
        return None, None, "no_state_rate"
    note = ""
    lower = text.lower()
    if "/wk" in lower or "/week" in lower or "/day" in lower:
        note = "non_hourly_cell"
        return None, None, note
    nums = [
        float(x)
        for x in re.findall(r"(?<!\d)(?:\d+\.\d+|\.\d+|\d+)(?!\d)", text.replace(",", ""))
    ]
    nums = [x if x >= 1 else round(x, 2) for x in nums]
    if not nums:
        return None, None, "unparsed"
    return min(nums), max(nums), note


def _load_tables() -> list[pd.DataFrame]:
    r = requests.get(SOURCE_URL, timeout=60, headers={"User-Agent": "Mozilla/5.0 IESET"})
    if r.status_code == 403:
        # DOL's Akamai edge sometimes blocks python-requests while allowing
        # ordinary curl. Keep a no-shell fallback so the official source remains
        # fetchable without a manual drop.
        fallback = subprocess.run(
            ["curl", "-sSL", SOURCE_URL],
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        if fallback.returncode == 0 and fallback.stdout.strip():
            return pd.read_html(io.StringIO(fallback.stdout))
    r.raise_for_status()
    return pd.read_html(io.StringIO(r.text))


def _state_panel(tables: list[pd.DataFrame]) -> pd.DataFrame:
    long_rows: list[dict] = []
    for table in tables:
        state_col = table.columns[0]
        for _, row in table.iterrows():
            jurisdiction = str(row[state_col]).strip()
            if not jurisdiction or jurisdiction.lower() == "nan":
                continue
            for col in table.columns[1:]:
                year = _year_from_column(col)
                if year is None:
                    continue
                raw = row[col]
                low, high, note = _parse_rate(raw)
                long_rows.append(
                    {
                        "jurisdiction": jurisdiction,
                        "year": year,
                        "raw_value": None if pd.isna(raw) else str(raw).strip(),
                        "state_rate_low": low,
                        "state_rate_high": high,
                        "parse_note": note,
                    }
                )
    df = pd.DataFrame(long_rows)
    if df.empty:
        raise UsdolError("DOL minimum-wage history parsed no rows")

    federal = (
        df[df["jurisdiction"].eq("Federal (FLSA)")][["year", "state_rate_high"]]
        .rename(columns={"state_rate_high": "federal_rate"})
        .dropna(subset=["federal_rate"])
    )
    states = df[~df["jurisdiction"].eq("Federal (FLSA)")].copy()
    states["state_abbr"] = states["jurisdiction"].map(STATE_ABBR)
    states = states[states["state_abbr"].notna()].copy()
    states["state_fips"] = states["state_abbr"].map(STATE_FIPS)
    states = states.merge(federal, on="year", how="left")
    states["value"] = states[["state_rate_high", "federal_rate"]].max(axis=1)
    states.loc[states["state_rate_high"].isna(), "value"] = states.loc[
        states["state_rate_high"].isna(), "federal_rate"
    ]
    states["country_iso3"] = "USA"
    states["unit_id"] = "US-" + states["state_abbr"]
    states = states.rename(columns={"jurisdiction": "state_name"})
    cols = [
        "country_iso3", "unit_id", "state_abbr", "state_fips", "state_name",
        "year", "value", "state_rate_low", "state_rate_high", "federal_rate",
        "raw_value", "parse_note",
    ]
    return states[cols].sort_values(["state_abbr", "year"]).reset_index(drop=True)


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    if series_id not in SUPPORTED:
        raise UsdolError(f"unsupported USDOL series_id {series_id!r}; known: {sorted(SUPPORTED)}")
    fetch_ts = utc_now()
    df = _state_panel(_load_tables())
    out, sha = write_vintage(
        publisher="usdol",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="usdol",
        series_id=series_id,
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="USD/hour",
        currency="USD",
        start_date=str(int(df["year"].min())),
        end_date=str(int(df["year"].max())),
        sha256=sha,
        parquet_path=out,
        extra={
            "columns": list(df.columns),
            "jurisdictions": int(df["state_abbr"].nunique()),
            "effective_floor_rule": "max(parsed_state_rate_high, federal_rate); federal fallback when state rate missing",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
