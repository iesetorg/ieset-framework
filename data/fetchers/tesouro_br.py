"""Brazil Tesouro Nacional — Resultado do Tesouro Nacional (RTN) monthly series.

Source: Tesouro Transparente CKAN, dataset ``resultado-do-tesouro-nacional``
  https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=resultado-do-tesouro-nacional
Auth: none.  License: CC-BY 4.0 (Tesouro Transparente open data).

The fetcher resolves the latest "Série Histórica - Mensal" XLSX through CKAN
(file name changes every month, e.g. seriehistoricajul26.xlsx), archives the
raw workbook, and parses one table into long format.

series_id: sheet code. Useful ones:
    1.1    Primary result of the central government, monthly, summary, R$ mn current
    1.1-A  same, constant (IPCA) prices
    1.2-B  primary result, constant prices, 12-month rolling
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import BROWSER_UA, save_raw

CKAN = "https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show"
DATASET = "resultado-do-tesouro-nacional"
LICENSE = "CC-BY 4.0 (Tesouro Transparente)"


def _latest_xlsx_url() -> tuple[str, str]:
    r = requests.get(CKAN, params={"id": DATASET}, timeout=60, headers={"User-Agent": BROWSER_UA})
    r.raise_for_status()
    for res in r.json()["result"]["resources"]:
        if res.get("format", "").upper() == "XLSX" and "Mensal" in res.get("name", ""):
            return res["url"], res.get("last_modified") or res.get("created") or ""
    raise RuntimeError("RTN monthly XLSX not found in CKAN package")


def fetch(series_id: str = "1.1", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    url, modified = _latest_xlsx_url()
    r = requests.get(url, timeout=180, headers={"User-Agent": BROWSER_UA})
    r.raise_for_status()
    raw_path, raw_sha = save_raw("tesouro_br", url.rsplit("/", 1)[-1], r.content, fetch_ts, "xlsx")
    sheet = pd.read_excel(io.BytesIO(r.content), sheet_name=series_id, header=None)
    hdr_row = sheet.index[sheet.iloc[:, 0].astype(str).str.strip().eq("Discriminação")][0]
    title = str(sheet.iloc[1, 0]).strip()
    units = str(sheet.iloc[2, 0]).strip()
    header = sheet.iloc[hdr_row]
    body = sheet.iloc[hdr_row + 1:].copy()
    body = body[body.iloc[:, 0].notna()]
    recs = []
    for _, row in body.iterrows():
        label = " ".join(str(row.iloc[0]).split())
        if label.lower().startswith(("fonte", "obs", "nota", "1/", "2/", "3/")) and len(label) > 60:
            continue
        for ci in range(1, len(header)):
            d = header.iloc[ci]
            if not isinstance(d, (pd.Timestamp, datetime)):
                continue
            v = pd.to_numeric(row.iloc[ci], errors="coerce")
            if pd.notna(v):
                recs.append({"line_item": label, "date": pd.Timestamp(d), "value": float(v)})
    df = pd.DataFrame(recs)
    df["country_iso3"] = "BRA"
    path, sha = write_vintage(publisher="tesouro_br", series_id=f"RTN_{series_id}", frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="tesouro_br",
        series_id=f"RTN_{series_id}",
        source_url=url,
        methodology_url="https://www.tesourotransparente.gov.br/temas/estatisticas-fiscais-e-planejamento/resultado-do-tesouro-nacional-rtn",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",
        units=units,
        currency="BRL",
        start_date=str(df["date"].min().date()),
        end_date=str(df["date"].max().date()),
        sha256=sha,
        parquet_path=path,
        extra={"table_title": title, "ckan_last_modified": modified, "raw_path": str(raw_path), "raw_sha256": raw_sha,
               "n_line_items": int(df["line_item"].nunique()),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
