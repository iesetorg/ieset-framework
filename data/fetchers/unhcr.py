"""
UNHCR Refugee Data Finder API
https://api.unhcr.org/docs/refugee-statistics.html

series_id options:
  population          — refugee stock, asylum seekers, IDPs, stateless by country (annual)
  asylum_decisions    — asylum application decisions by country
  solutions           — durable solutions (resettlement, naturalisation, return)

publisher_id: unhcr
No auth required.
"""
from __future__ import annotations

import requests
import pandas as pd
from ._base import FetchResult, utc_now, write_vintage, ROOT

BASE = "https://api.unhcr.org/population/v1"
METHODOLOGY = "https://www.unhcr.org/refugee-statistics/methodology/"
LICENSE = "CC-BY"


def _get_all_pages(endpoint: str, params: dict) -> list[dict]:
    """Paginate through all pages of an UNHCR API response."""
    items: list[dict] = []
    page = 1
    while True:
        r = requests.get(
            f"{BASE}/{endpoint}/",
            params={**params, "page": page},
            timeout=60,
        )
        r.raise_for_status()
        d = r.json()
        items.extend(d.get("items", []))
        if page >= d.get("maxPages", 1):
            break
        page += 1
    return items


def fetch(series_id: str, year_from: str = "1975", year_to: str = "2024", **kwargs) -> FetchResult:
    """
    Fetch UNHCR refugee statistics.

    series_id:
      population          — by country of asylum (coa); all country columns
      population_origin   — by country of origin (coo); all country columns
      asylum_decisions    — recognition rates, rejections
      solutions           — resettlement + voluntary return + naturalisation
    """
    year_from = str(year_from)
    year_to = str(year_to)

    if series_id == "population":
        # Loop through years to get global totals by year (UNHCR API returns aggregate rows)
        # These are global-total rows (useful for macro trend analysis)
        params = {
            "limit": 10000,
            "yearFrom": year_from,
            "yearTo": year_to,
        }
        raw = _get_all_pages("population", params)
        rows = []
        for item in raw:
            # Take both country-level and aggregate rows
            coa = item.get("coa_iso") or "-"
            rows.append({
                "year": item["year"],
                "country_of_asylum_iso3": coa,
                "country_of_asylum": item.get("coa_name", "-"),
                "refugees": _to_num(item.get("refugees")),
                "asylum_seekers": _to_num(item.get("asylum_seekers")),
                "idps": _to_num(item.get("idps")),
                "stateless": _to_num(item.get("stateless")),
                "returned_refugees": _to_num(item.get("returned_refugees")),
                "ooc": _to_num(item.get("ooc")),
            })
        df = pd.DataFrame(rows)

    elif series_id == "population_origin":
        # All countries as country-of-origin — loop through coo_all for all countries
        # Use coo_iso filter looping over key country list
        TARGET_COUNTRIES = [
            "AFG","SYR","VEN","UKR","SOL","ETH","MMR","COD","SSD","NGA",
            "SDN","SOM","ERI","IRN","IRQ","PAK","CMR","CAF","BDI","YEM",
            "MOZ","NIC","HON","SLV","GTM","COL","CUB","ZWE","RUS","CHN",
        ]
        all_rows = []
        for coo in TARGET_COUNTRIES:
            try:
                p = {"limit": 1000, "yearFrom": year_from, "yearTo": year_to, "coo_iso": coo}
                items = _get_all_pages("population", p)
                for item in items:
                    all_rows.append({
                        "year": item["year"],
                        "country_of_origin_iso3": coo,
                        "refugees": _to_num(item.get("refugees")),
                        "asylum_seekers": _to_num(item.get("asylum_seekers")),
                    })
            except Exception:
                pass
        df = pd.DataFrame(all_rows)
        raw = all_rows  # for reference

    elif series_id == "population_origin":
        # All countries as country-of-origin
        params = {
            "limit": 10000,
            "yearFrom": year_from,
            "yearTo": year_to,
        }
        raw = _get_all_pages("population", params)
        rows = []
        for item in raw:
            coo = item.get("coo_iso") or item.get("coo") or "-"
            if coo == "-":
                continue
            rows.append({
                "year": item["year"],
                "country_of_origin_iso3": coo,
                "country_of_origin": item.get("coo_name", ""),
                "refugees": _to_num(item.get("refugees")),
                "asylum_seekers": _to_num(item.get("asylum_seekers")),
            })
        df = pd.DataFrame(rows)

    elif series_id == "asylum_decisions":
        params = {
            "limit": 10000,
            "yearFrom": year_from,
            "yearTo": year_to,
        }
        raw = _get_all_pages("asylum-decisions", params)
        df = pd.DataFrame([{
            "year": item["year"],
            "country_of_asylum_iso3": item.get("coa_iso", "-"),
            "country_of_origin_iso3": item.get("coo_iso", "-"),
            "applications": _to_num(item.get("applications")),
            "recognized": _to_num(item.get("recognized")),
            "rejected": _to_num(item.get("rejected")),
            "otherwise_closed": _to_num(item.get("otherwise_closed")),
        } for item in raw if item.get("coa_iso") != "-"])

    elif series_id == "solutions":
        params = {
            "limit": 10000,
            "yearFrom": year_from,
            "yearTo": year_to,
        }
        raw = _get_all_pages("solutions", params)
        df = pd.DataFrame([{
            "year": item["year"],
            "country_iso3": item.get("coa_iso") or item.get("coo_iso") or "-",
            "resettlement": _to_num(item.get("rst")),
            "naturalisation": _to_num(item.get("nat")),
            "voluntary_return": _to_num(item.get("vda")),
        } for item in raw])

    else:
        raise ValueError(f"Unknown UNHCR series_id '{series_id}'. "
                         f"Use: population, population_origin, asylum_decisions, solutions")

    # Coerce all object columns to str to avoid pyarrow mixed-type errors
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str)

    now = utc_now()
    path, digest = write_vintage(
        publisher="unhcr",
        series_id=series_id,
        frame=df,
        fetch_utc=now,
    )
    start = str(df["year"].min()) if "year" in df.columns and len(df) else year_from
    end   = str(df["year"].max()) if "year" in df.columns and len(df) else year_to
    return FetchResult(
        publisher="unhcr",
        series_id=series_id,
        source_url=f"{BASE}/{series_id}/",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=now,
        rows=len(df),
        frequency="A",
        units="persons",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=digest,
        parquet_path=path,
    )


def _to_num(v) -> float | None:
    if v is None or v == "-":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
