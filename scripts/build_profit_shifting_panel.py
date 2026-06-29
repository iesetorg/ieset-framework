#!/usr/bin/env python3
"""Build a jurisdiction-year panel of multinational profit shifting to tax havens.

Enables the Zucman profit-shifting claim (Z5: ~40% of multinational profits
booked in tax havens) from Tørsløv, Wier & Zucman, "The Missing Profits of
Nations" (TWZ).

Sources (all public, key-free):

1. missingprofits.world — TWZ replication workbooks.
   - TWZ2019.xlsx (the original NBER/TWZ "Missing Profits of Nations" tables;
     benchmark years 2015 & 2016): Table 2 (OECD countries), Table 3 (main
     developing countries), and the tax-haven block give shifted profits
     ($Bn) and corporate-tax-revenue loss/gain (% of collected) per
     jurisdiction. Havens appear with negative shifted profits = net INFLOW.
   - TWZ2022.xlsx (2022 update, 2019 benchmark): Table2 gives shifted profits
     into each major haven (baseline estimate); DataF2 gives the effective tax
     rate and the profitability of foreign-controlled vs local firms by
     country — the misalignment signal underlying the shifting estimate.

2. OECD Country-by-Country Reporting (CbCR) aggregate totals by jurisdiction
   (DSD_CBCR@DF_CBCRI), fetched key-free from the OECD SDMX REST endpoint.
   Used for a SUPPLEMENTARY cross-jurisdiction profit-vs-employment misalignment
   signal (profit booked, employees, profit per employee) summed over all
   reporting parent jurisdictions, 2016-2022. NOTE: the public bulk extract is
   reported by a non-exhaustive set of parent jurisdictions (the US and several
   large reporters are missing financial measures), so CbCR totals here are a
   partial-coverage indicator, not a global aggregate. They are flagged as such.

Output (long): data/derived/profit_shifting_panel.parquet
  columns: jurisdiction_iso3, year, series_id, value, unit, source

The TWZ figures are cross-sectional benchmarks (2015/2016/2019). The CbCR
profit-per-employee misalignment series is a genuine 2016-2022 time series but
of partial coverage. The Z5 "~40% of MNC profits shifted" headline is captured
by the TWZ profit-shifting-share figure; the "haven share rose" trend test is
only weakly supportable from the partial CbCR panel and is documented as such
in the brief.
"""
from __future__ import annotations

import io
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import (  # noqa: E402
    FetchResult,
    utc_now,
    utc_stamp,
    write_manifest,
    write_vintage,
)

DERIVED = ROOT / "data" / "derived"
PANEL_PARQUET = DERIVED / "profit_shifting_panel.parquet"

RAW_DIR = ROOT / "data" / "raw" / "profit_shifting"
TWZ2019_XLSX = RAW_DIR / "TWZ2019.xlsx"
TWZ2022_XLSX = RAW_DIR / "TWZ2022.xlsx"

TWZ2019_URL = "https://missingprofits.world/wp-content/uploads/2020/02/TWZ2019.xlsx"
TWZ2022_URL = "https://missingprofits.world/wp-content/uploads/2022/04/TWZ2022.xlsx"
MPW_URL = "https://missingprofits.world/"
TWZ_METHOD_URL = (
    "https://gabriel-zucman.eu/files/TWZ2018.pdf"  # The Missing Profits of Nations
)
TWZ_LICENSE = "Tørsløv, Wier & Zucman replication data (missingprofits.world); academic use, attribution"

OECD_CBCR_FLOW = "OECD.CTP.TPS,DSD_CBCR@DF_CBCRI,1.1"
OECD_CBCR_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CTP.TPS,DSD_CBCR@DF_CBCRI,1.1/all?format=csvfilewithlabels"
)
OECD_CBCR_METHOD_URL = (
    "https://www.oecd.org/en/data/datasets/corporate-tax-statistics-database.html"
)
OECD_LICENSE = "OECD standard permissions (attribution required)"

# TWZ jurisdiction name -> ISO3. Composite regions ("Caribbean", "Other") have no
# single ISO3 and are dropped from the per-jurisdiction panel.
NAME_TO_ISO3: dict[str, str] = {
    "Australia": "AUS", "Austria": "AUT", "Canada": "CAN", "Chile": "CHL",
    "Czech Republic": "CZE", "Denmark": "DNK", "Estonia": "EST", "Finland": "FIN",
    "France": "FRA", "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN",
    "Iceland": "ISL", "Israel": "ISR", "Italy": "ITA", "Japan": "JPN",
    "Korea": "KOR", "Latvia": "LVA", "Mexico": "MEX", "New Zealand": "NZL",
    "Norway": "NOR", "Poland": "POL", "Portugal": "PRT", "Slovakia": "SVK",
    "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE", "Turkey": "TUR",
    "United Kingdom": "GBR", "United States": "USA",
    "Brazil": "BRA", "China": "CHN", "Colombia": "COL", "Costa Rica": "CRI",
    "India": "IND", "Russia": "RUS", "South Africa": "ZAF",
    "Argentina": "ARG", "Egypt": "EGY", "Indonesia": "IDN", "Malaysia": "MYS",
    "Nigeria": "NGA", "Thailand": "THA", "Uruguay": "URY", "Venezuela": "VEN",
    # Tax havens
    "Belgium": "BEL", "Ireland": "IRL", "Luxembourg": "LUX", "Malta": "MLT",
    "Netherlands": "NLD", "Bermuda": "BMU", "Singapore": "SGP",
    "Puerto Rico": "PRI", "Hong Kong": "HKG", "Switzerland": "CHE",
    "Cyprus": "CYP",
}
# Regions intentionally excluded (no single ISO3): Caribbean, Other, etc.
SKIP_NAMES = {"Caribbean", "Other", "OECD countries", "Main developing countries",
              "Tax havens", "EU havens", "Non-EU tax havens", "Rest", "All havens"}

# Known havens that must be present for the test (net inflow expected).
KNOWN_HAVENS = ["IRL", "LUX", "NLD", "CHE", "SGP", "BMU"]


def _clean_name(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().strip("'").strip()
    return text or None


# --------------------------------------------------------------------------- #
# TWZ2019: shifted profits + corp-tax revenue loss, 2015 & 2016               #
# --------------------------------------------------------------------------- #
def _parse_twz2019() -> list[dict[str, Any]]:
    """Table 2 (OECD), Table 3 (developing), tax-haven block from TWZ2019.

    Table 2 layout (header=None):
      col1 = country, col2 = shifted profits 2015 ($Bn), col3 = 2016 ($Bn),
      col6 = corp-tax revenue loss/gain 2015 (% of collected), col7 = 2016.
    Table 3 layout:
      col1 = country, col2 = shifted profits ($Bn, 2016 benchmark),
      col3 = corp-tax revenue loss (% of collected).
    """
    rows: list[dict[str, Any]] = []

    t2 = pd.read_excel(TWZ2019_XLSX, sheet_name="Table 2", header=None)
    for _, r in t2.iterrows():
        name = _clean_name(r[1])
        if not name or name in SKIP_NAMES:
            continue
        iso = NAME_TO_ISO3.get(name)
        if not iso:
            continue
        for year, sp_col, loss_col in ((2015, 2, 6), (2016, 3, 7)):
            sp = pd.to_numeric(r[sp_col], errors="coerce")
            if pd.notna(sp):
                rows.append({
                    "jurisdiction_iso3": iso, "year": year,
                    "series_id": "twz_shifted_profits_usd_bn",
                    "value": float(sp), "unit": "USD billion (negative = net inflow to haven)",
                    "source": "twz2019:Table2",
                })
            loss = pd.to_numeric(r[loss_col], errors="coerce")
            if pd.notna(loss):
                rows.append({
                    "jurisdiction_iso3": iso, "year": year,
                    "series_id": "twz_corp_tax_revenue_loss_pct",
                    "value": float(loss) * 100.0,
                    "unit": "percent of corporate tax collected (negative = gain)",
                    "source": "twz2019:Table2",
                })

    t3 = pd.read_excel(TWZ2019_XLSX, sheet_name="Table 3", header=None)
    for _, r in t3.iterrows():
        name = _clean_name(r[1])
        if not name or name in SKIP_NAMES:
            continue
        iso = NAME_TO_ISO3.get(name)
        if not iso:
            continue
        sp = pd.to_numeric(r[2], errors="coerce")
        if pd.notna(sp):
            rows.append({
                "jurisdiction_iso3": iso, "year": 2016,
                "series_id": "twz_shifted_profits_usd_bn",
                "value": float(sp), "unit": "USD billion (negative = net inflow to haven)",
                "source": "twz2019:Table3",
            })
        loss = pd.to_numeric(r[3], errors="coerce")
        if pd.notna(loss):
            rows.append({
                "jurisdiction_iso3": iso, "year": 2016,
                "series_id": "twz_corp_tax_revenue_loss_pct",
                "value": float(loss) * 100.0,
                "unit": "percent of corporate tax collected (negative = gain)",
                "source": "twz2019:Table3",
            })
    return rows


# --------------------------------------------------------------------------- #
# TWZ2022: 2019 benchmark haven inflow + foreign/local ETR & profitability    #
# --------------------------------------------------------------------------- #
def _parse_twz2022() -> list[dict[str, Any]]:
    """TWZ2022 update workbook. Its baseline tables reproduce the TWZ 2015
    benchmark (Table2 haven inflows equal TWZ2019's 2015 figures), so we do NOT
    re-emit the haven-inflow series from here (it would duplicate TWZ2019). We
    take the foreign-vs-local effective tax rate / profitability (DataF2), which
    is the per-jurisdiction misalignment signal, and the global Z5 headline
    (Table1).

    DataF2 layout (header=None):
      col0 = country, col1 = foreign-less-local profitability,
      col2 = pi_f (foreign-controlled firms), col3 = pi_l (local firms),
      col4 = effective tax rate (of foreign-controlled firms).
    """
    rows: list[dict[str, Any]] = []

    f2 = pd.read_excel(TWZ2022_XLSX, sheet_name="DataF2", header=None)
    for _, r in f2.iterrows():
        name = _clean_name(r[0])
        if not name or name in SKIP_NAMES:
            continue
        iso = NAME_TO_ISO3.get(name)
        if not iso:
            continue
        pif = pd.to_numeric(r[2], errors="coerce")
        pil = pd.to_numeric(r[3], errors="coerce")
        etr = pd.to_numeric(r[4], errors="coerce")
        if pd.notna(etr):
            rows.append({
                "jurisdiction_iso3": iso, "year": 2015,
                "series_id": "twz_foreign_firm_effective_tax_rate",
                "value": float(etr) * 100.0, "unit": "percent",
                "source": "twz2022:DataF2",
            })
        if pd.notna(pif):
            rows.append({
                "jurisdiction_iso3": iso, "year": 2015,
                "series_id": "twz_foreign_firm_profitability_ratio",
                "value": float(pif),
                "unit": "ratio of pre-tax profits to wages (foreign-controlled firms)",
                "source": "twz2022:DataF2",
            })
        if pd.notna(pil):
            rows.append({
                "jurisdiction_iso3": iso, "year": 2015,
                "series_id": "twz_local_firm_profitability_ratio",
                "value": float(pil),
                "unit": "ratio of pre-tax profits to wages (local firms)",
                "source": "twz2022:DataF2",
            })

    # Table1: global Z5 headline accounting (2015 benchmark). Emitted as WORLD.
    #   row "Net profits of foreign-controlled corp." col2 = USD bn, col3 = share
    #   row "Of which: shifted to tax havens"        col2 = USD bn, col3 = share
    t1 = pd.read_excel(TWZ2022_XLSX, sheet_name="Table1", header=None)
    for _, r in t1.iterrows():
        label = _clean_name(r[1])
        if not label:
            continue
        usd_bn = pd.to_numeric(r[2], errors="coerce")
        share = pd.to_numeric(r[3], errors="coerce")
        if label.startswith("Net profits of foreign-controlled") and pd.notna(usd_bn):
            rows.append({
                "jurisdiction_iso3": "WLD", "year": 2015,
                "series_id": "twz_global_foreign_controlled_profits_usd_bn",
                "value": float(usd_bn), "unit": "USD billion (global)",
                "source": "twz2022:Table1",
            })
        if label.startswith("Of which: shifted to tax havens"):
            if pd.notna(usd_bn):
                rows.append({
                    "jurisdiction_iso3": "WLD", "year": 2015,
                    "series_id": "twz_global_shifted_to_havens_usd_bn",
                    "value": float(usd_bn), "unit": "USD billion (global)",
                    "source": "twz2022:Table1",
                })
    # Headline share: shifted-to-havens / foreign-controlled profits (the ~40%/Z5).
    return rows


# --------------------------------------------------------------------------- #
# OECD CbCR: supplementary profit-vs-employment misalignment, 2016-2022       #
# --------------------------------------------------------------------------- #
def _load_cbcr() -> pd.DataFrame | None:
    """Fetch OECD CbCR aggregate-totals dataflow (key-free SDMX CSV).

    Returns a DataFrame of the relevant measures, or None if unreachable.
    """
    from data.fetchers._http import get as robust_get  # local import; optional dep

    try:
        url = (
            "https://sdmx.oecd.org/public/rest/data/"
            f"{OECD_CBCR_FLOW}/all"
        )
        payload = robust_get(
            url,
            params={"format": "csvfilewithlabels"},
            timeout=300,
            headers={"Accept": "text/csv,*/*;q=0.8"},
            return_http_errors=True,
        )
        if payload.status_code >= 400 or not payload.text.strip():
            return None
        return pd.read_csv(io.StringIO(payload.text), low_memory=False)
    except Exception:
        return None


def _parse_cbcr(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Profit booked, employees, profit-per-employee by booked jurisdiction-year.

    COUNTERPART_AREA = jurisdiction where activity is booked.
    REF_AREA = reporting parent jurisdiction. We sum over all reporting parents.
    PROFIT uses PROFIT_GROUPING == '_T' (all sub-groups); EMPLOYEES has no panel.
    """
    rows: list[dict[str, Any]] = []
    needed = {"COUNTERPART_AREA", "TIME_PERIOD", "OBS_VALUE", "MEASURE"}
    if not needed.issubset(df.columns):
        return rows

    def agg(measure: str) -> pd.DataFrame:
        s = df[df["MEASURE"] == measure].copy()
        if measure == "PROFIT" and "PROFIT_GROUPING" in s.columns:
            s = s[s["PROFIT_GROUPING"] == "_T"]
        s = s[s["COUNTERPART_AREA"].astype(str).str.len() == 3]  # drop region codes
        g = (
            s.groupby(["COUNTERPART_AREA", "TIME_PERIOD"], as_index=False)["OBS_VALUE"]
            .sum()
            .rename(columns={"OBS_VALUE": measure})
        )
        return g

    profit = agg("PROFIT")
    emp = agg("EMPLOYEES")
    if profit.empty or emp.empty:
        return rows

    merged = profit.merge(emp, on=["COUNTERPART_AREA", "TIME_PERIOD"], how="outer")
    for _, r in merged.iterrows():
        iso = str(r["COUNTERPART_AREA"]).strip().upper()
        if len(iso) != 3:
            continue
        year = int(r["TIME_PERIOD"])
        p = r.get("PROFIT")
        e = r.get("EMPLOYEES")
        if pd.notna(p):
            rows.append({
                "jurisdiction_iso3": iso, "year": year,
                "series_id": "cbcr_profit_booked_usd",
                "value": float(p),
                "unit": "USD (profit booked in jurisdiction, summed over reporting parents; partial coverage)",
                "source": "oecd_cbcr:DF_CBCRI",
            })
        if pd.notna(e):
            rows.append({
                "jurisdiction_iso3": iso, "year": year,
                "series_id": "cbcr_employees",
                "value": float(e),
                "unit": "employees (summed over reporting parents; partial coverage)",
                "source": "oecd_cbcr:DF_CBCRI",
            })
        if pd.notna(p) and pd.notna(e) and e and e > 0:
            rows.append({
                "jurisdiction_iso3": iso, "year": year,
                "series_id": "cbcr_profit_per_employee_usd",
                "value": float(p) / float(e),
                "unit": "USD profit per employee (misalignment signal; partial coverage)",
                "source": "oecd_cbcr:DF_CBCRI",
            })
    return rows


def build_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    if not TWZ2019_XLSX.exists() or not TWZ2022_XLSX.exists():
        raise FileNotFoundError(
            f"missing TWZ workbooks under {RAW_DIR}; "
            f"download {TWZ2019_URL} and {TWZ2022_URL}"
        )

    rows: list[dict[str, Any]] = []
    rows.extend(_parse_twz2019())
    rows.extend(_parse_twz2022())

    # Derived global Z5 headline: shifted-to-havens / foreign-controlled profits.
    g_fc = next((r["value"] for r in rows
                 if r["series_id"] == "twz_global_foreign_controlled_profits_usd_bn"), None)
    g_sh = next((r["value"] for r in rows
                 if r["series_id"] == "twz_global_shifted_to_havens_usd_bn"), None)
    if g_fc and g_sh:
        rows.append({
            "jurisdiction_iso3": "WLD", "year": 2015,
            "series_id": "twz_share_foreign_profits_shifted_pct",
            "value": 100.0 * g_sh / g_fc,
            "unit": "percent of foreign-controlled MNC profits booked in tax havens",
            "source": "twz2022:Table1",
        })

    cbcr_df = _load_cbcr()
    cbcr_reachable = cbcr_df is not None
    cbcr_rows = _parse_cbcr(cbcr_df) if cbcr_df is not None else []
    rows.extend(cbcr_rows)

    panel = pd.DataFrame(rows)
    panel = (
        panel.dropna(subset=["value"])
        .drop_duplicates(["jurisdiction_iso3", "year", "series_id", "source"])
        .sort_values(["series_id", "jurisdiction_iso3", "year"])
        .reset_index(drop=True)
    )
    panel["year"] = panel["year"].astype(int)

    stats = {
        "rows": int(len(panel)),
        "jurisdictions": int(panel["jurisdiction_iso3"].nunique()),
        "series": sorted(panel["series_id"].unique().tolist()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "cbcr_reachable": cbcr_reachable,
        "cbcr_rows": len(cbcr_rows),
        "per_series": {
            sid: {
                "rows": int((panel["series_id"] == sid).sum()),
                "jurisdictions": int(panel.loc[panel["series_id"] == sid, "jurisdiction_iso3"].nunique()),
                "year_min": int(panel.loc[panel["series_id"] == sid, "year"].min()),
                "year_max": int(panel.loc[panel["series_id"] == sid, "year"].max()),
            }
            for sid in sorted(panel["series_id"].unique())
        },
    }
    return panel, stats


def main() -> int:
    fetch_ts = utc_now()
    panel, stats = build_panel()
    DERIVED.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(PANEL_PARQUET, engine="pyarrow", index=False)

    results: list[FetchResult] = []
    path, sha = write_vintage(
        publisher="profit_shifting",
        series_id="profit_shifting_panel",
        frame=panel,
        fetch_utc=fetch_ts,
    )
    results.append(
        FetchResult(
            publisher="profit_shifting",
            series_id="profit_shifting_panel",
            source_url=MPW_URL,
            methodology_url=TWZ_METHOD_URL,
            license=TWZ_LICENSE,
            fetch_utc=fetch_ts,
            rows=len(panel),
            frequency="benchmark/annual",
            units="long: jurisdiction_iso3, year, series_id, value, unit, source",
            currency="USD",
            start_date=str(stats["year_min"]),
            end_date=str(stats["year_max"]),
            sha256=sha,
            parquet_path=path,
            extra={
                "twz2019_url": TWZ2019_URL,
                "twz2022_url": TWZ2022_URL,
                "oecd_cbcr_url": OECD_CBCR_URL,
                "oecd_cbcr_flow": OECD_CBCR_FLOW,
                "stats": stats,
            },
        )
    )

    manifest = write_manifest(
        results, run_stamp=f"{utc_stamp(fetch_ts)}_profit_shifting"
    )
    audit = (
        ROOT / "engine" / "audits"
        / f"profit_shifting_panel_build_{utc_stamp(fetch_ts)}.json"
    )
    audit.write_text(json.dumps([asdict(r) for r in results], default=str, indent=2) + "\n")

    print(
        f"OK profit_shifting:profit_shifting_panel rows={len(panel)} "
        f"jurisdictions={stats['jurisdictions']} period={stats['year_min']}->{stats['year_max']}"
    )
    print(f"panel: {PANEL_PARQUET.relative_to(ROOT)}")
    print(f"manifest: {manifest.relative_to(ROOT)}")
    print(f"audit: {audit.relative_to(ROOT)}")
    print(f"cbcr_reachable={stats['cbcr_reachable']} cbcr_rows={stats['cbcr_rows']}")
    for sid, s in stats["per_series"].items():
        print(f"  {sid}: rows={s['rows']} jur={s['jurisdictions']} {s['year_min']}-{s['year_max']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
