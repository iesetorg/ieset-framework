"""FAOSTAT Food Balance Sheets fetcher (bulk-download path).

Endpoint: https://bulks-faostat.fao.org/production/<dataset>.zip
Auth: none.
License: CC-BY-4.0 (FAO terms).

The legacy `faostatservices.fao.org/api/v1/...` REST API now returns 401
without an API key for unauthenticated callers; the bulk-download path is
the supported public route. We fetch the normalised FBS zip, extract the
CSV, filter to the LatAm comparator set, and emit a tidy panel of
food-import share by country×year.

    import_share_pct = 100 * Import / (Production + Import - Export)

(All quantities expressed in 1000 tonnes — FBS Grand Total / "2901". We
treat tonnage import-share as the canonical caloric-self-sufficiency proxy;
the FAO does the kcal conversion internally for the per-capita supply rows
and the pattern is the same.)

Returned panel columns: country_iso3, year, value (= import_share_pct, %).
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "CC-BY-4.0 (FAO terms)"
BULK_URL = "https://bulks-faostat.fao.org/production/FoodBalanceSheets_E_All_Data_(Normalized).zip"

# FAOSTAT 'Area' name -> ISO3 for the LatAm + comparator countries IESET uses.
# (Name-based mapping is robust against area-code drift across FAOSTAT vintages.)
_AREA_NAME_TO_ISO3 = {
    "Cuba": "CUB",
    "Brazil": "BRA",
    "Argentina": "ARG",
    "Chile": "CHL",
    "Colombia": "COL",
    "Costa Rica": "CRI",
    "Dominican Republic": "DOM",
    "Ecuador": "ECU",
    "Guatemala": "GTM",
    "Honduras": "HND",
    "Haiti": "HTI",
    "Jamaica": "JAM",
    "Mexico": "MEX",
    "Nicaragua": "NIC",
    "Panama": "PAN",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Venezuela (Bolivarian Republic of)": "VEN",
    "Uruguay": "URY",
    "Bolivia (Plurinational State of)": "BOL",
    "El Salvador": "SLV",
}


class FaostatError(RuntimeError):
    pass


def _download_csv() -> pd.DataFrame:
    r = requests.get(BULK_URL, timeout=300, headers={"User-Agent": "Mozilla/5.0 ieset-fetcher"})
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    csv_name = next((n for n in z.namelist() if n.lower().endswith(".csv")), None)
    if csv_name is None:
        raise FaostatError(f"no CSV inside FAOSTAT FBS bulk zip; got {z.namelist()}")
    with z.open(csv_name) as f:
        df = pd.read_csv(f, low_memory=False, encoding="latin-1")
    return df


def fetch(
    series_id: str = "food_balance_sheets",
    *,
    vintage_utc: datetime | None = None,
    countries: str | None = None,
    year_from: int = 2010,
    year_to: int = 2023,
) -> FetchResult:
    """Fetch FAOSTAT FBS Grand Total tonnage flows and derive import share."""
    fetch_ts = utc_now()

    if countries:
        wanted = {c.strip().upper() for c in countries.split(";") if c.strip()}
    else:
        wanted = set(_AREA_NAME_TO_ISO3.values())

    raw = _download_csv()
    raw.columns = [c.strip() for c in raw.columns]
    if "Area" not in raw.columns:
        raise FaostatError(f"unexpected FBS columns: {raw.columns.tolist()[:10]}")

    raw["country_iso3"] = raw["Area"].map(_AREA_NAME_TO_ISO3)
    raw = raw.dropna(subset=["country_iso3"]).copy()
    raw = raw[raw["country_iso3"].isin(wanted)].copy()

    # FAOSTAT FBS Grand Total (2901) ships only "Domestic supply quantity"
    # and per-capita supply rows; no per-item Production/Import/Export. To
    # compute import share we sum Production + Import + Export across all
    # individual food items, EXCLUDING the synthetic Grand Total row to
    # avoid double-counting.
    item_code_col = "Item Code" if "Item Code" in raw.columns else "Item Code (FBS)"
    elem_col = "Element"
    raw[item_code_col] = pd.to_numeric(raw[item_code_col], errors="coerce")
    items = raw[raw[item_code_col] != 2901].copy()
    items = items[items["Element"].isin(["Production", "Import Quantity", "Import quantity",
                                          "Export Quantity", "Export quantity"])].copy()
    items["Element"] = items["Element"].replace({
        "Import quantity": "Import Quantity",
        "Export quantity": "Export Quantity",
    })

    items["year_int"] = pd.to_numeric(items["Year"], errors="coerce").astype("Int64")
    items = items[(items["year_int"] >= year_from) & (items["year_int"] <= year_to)]
    items["value_num"] = pd.to_numeric(items["Value"], errors="coerce")

    # Sum across items per (country, year, element)
    agg = (
        items.groupby(["country_iso3", "year_int", "Element"], as_index=False)["value_num"]
        .sum()
    )
    pivot = (
        agg.pivot(index=["country_iso3", "year_int"], columns="Element", values="value_num")
        .reset_index()
        .rename(columns={"year_int": "year"})
    )

    # Element labels in FAOSTAT FBS bulk: "Production", "Import Quantity",
    # "Export Quantity" (sometimes "Import quantity" / "Export quantity").
    def _col(p, *names):
        for n in names:
            if n in p.columns:
                return n
        return None

    prod = _col(pivot, "Production")
    imp = _col(pivot, "Import Quantity", "Import quantity")
    exp = _col(pivot, "Export Quantity", "Export quantity")
    if not (prod and imp):
        raise FaostatError(
            f"missing element columns: prod={prod} imp={imp} exp={exp} "
            f"available={pivot.columns.tolist()}"
        )

    pivot[prod] = pivot[prod].fillna(0)
    pivot[imp] = pivot[imp].fillna(0)
    if exp:
        pivot[exp] = pivot[exp].fillna(0)
    else:
        pivot["__exp"] = 0
        exp = "__exp"

    pivot["domestic_supply"] = pivot[prod] + pivot[imp] - pivot[exp]
    pivot["import_share_pct"] = (pivot[imp] / pivot["domestic_supply"]).where(pivot["domestic_supply"] > 0) * 100

    out = pivot[["country_iso3", "year", "import_share_pct"]].rename(
        columns={"import_share_pct": "value"}
    )
    out = out.dropna(subset=["value"]).sort_values(["country_iso3", "year"]).reset_index(drop=True)

    path_out, sha = write_vintage(
        publisher="faostat",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="faostat",
        series_id=series_id,
        source_url=BULK_URL,
        methodology_url="https://www.fao.org/faostat/en/#data/FBS",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="annual",
        units="percent (imports / domestic supply, Grand Total tonnage)",
        currency=None,
        start_date=str(int(out["year"].min())) if len(out) else None,
        end_date=str(int(out["year"].max())) if len(out) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "year_from": year_from,
            "year_to": year_to,
            "n_countries": int(out["country_iso3"].nunique()),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from data.fetchers import faostat as _self

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series", default="food_balance_sheets")
    p.add_argument("--countries", default=None)
    p.add_argument("--year-from", type=int, default=2010)
    p.add_argument("--year-to", type=int, default=2023)
    args = p.parse_args()
    res = _self.fetch(args.series, countries=args.countries, year_from=args.year_from, year_to=args.year_to)
    print(f"OK rows={res.rows} {res.start_date}->{res.end_date}")
    print(f"   {res.parquet_path}")
