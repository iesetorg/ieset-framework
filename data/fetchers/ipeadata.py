"""IPEADATA (Brazil — Instituto de Pesquisa Econômica Aplicada) fetcher.

Endpoint: free public OData v4 API at
    http://www.ipeadata.gov.br/api/odata4/

Two endpoints we care about:
    Metadados                       — series catalogue (one row per SERCODIGO).
    ValoresSerie(SERCODIGO='<code>') — observations for a specific series.

Both return JSON shaped roughly:
    { "@odata.context": "...",
      "value": [ { "SERCODIGO": "...", "VALDATA": "1980-01-01T00:00:00-03:00",
                   "VALVALOR": 1.23, "NIVNOME": "", "TERCODIGO": "" },
                 ... ] }

`VALDATA` is ISO-8601 with offset; we keep the date and derive `year`. Some
series have territorial breakdowns (`NIVNOME`/`TERCODIGO`) — for the curated
national series we either get a single national row per period or filter to
`NIVNOME == ""` (Brasil) where the catalogue annotates breakdowns.

Auth: none. License: open public reuse (cc_by-style; cite IPEA/IPEADATA).

We expose a small registry of canonical Brazilian series. Unknown ids are
treated as raw `SERCODIGO` strings and fetched directly via ValoresSerie.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "http://www.ipeadata.gov.br/api/odata4"
LICENSE = "IPEA/IPEADATA open public reuse — http://www.ipeadata.gov.br/"
METHODOLOGY = "http://www.ipeadata.gov.br/"

_RATE_SLEEP_S = 0.2


class IpeadataError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Spec:
    """How to resolve a IESET-friendly id to an IPEADATA SERCODIGO."""
    sercodigo: str
    label: str
    frequency: str
    units: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Curated catalogue
# ---------------------------------------------------------------------------
# SERCODIGOs validated against the IPEADATA Metadados endpoint (2026-04).
# These are stable identifiers; the underlying data is revisable.
_CATALOGUE: dict[str, _Spec] = {
    # --- Prices ---------------------------------------------------------
    "IPCA": _Spec(
        sercodigo="PRECOS12_IPCA12",
        label="IPCA — Índice de Preços ao Consumidor Amplo (IBGE)",
        frequency="monthly",
        units="index (Dec 1993=100)",
        notes="Headline Brazilian CPI, monthly index from IBGE/IPEA mirror.",
    ),
    # --- National accounts ---------------------------------------------
    "GDP": _Spec(
        sercodigo="BM12_PIBPM12",
        label="PIB a preços de mercado (BCB / IPEA monthly nominal)",
        frequency="monthly",
        units="BRL millions, current prices",
        notes="Monthly nominal GDP at market prices, BCB-derived series.",
    ),
    # --- Labour market -------------------------------------------------
    "MIN_WAGE": _Spec(
        sercodigo="MTE12_SALMIN12",
        label="Salário mínimo nominal (Ministério do Trabalho)",
        frequency="monthly",
        units="BRL per month, nominal",
        notes="Statutory minimum wage, monthly nominal value (MTE series).",
    ),
    "UNEMPLOYMENT": _Spec(
        sercodigo="PNADC12_TDESOC12",
        label="Taxa de desocupação (PNAD Contínua, IBGE)",
        frequency="monthly",
        units="percent of labour force",
        notes="Monthly unemployment rate from PNAD Contínua continuous survey.",
    ),
    # --- Social policy / poverty ---------------------------------------
    "BOLSA_FAMILIA": _Spec(
        sercodigo="MDS_BFCOB",
        label="Bolsa Família — famílias beneficiadas",
        frequency="monthly",
        units="number of families",
        notes="MDS coverage of Bolsa Família conditional cash transfer.",
    ),
}

# Lower-case alias map so callers can use friendly names.
_ALIASES: dict[str, str] = {
    "ipca": "IPCA",
    "cpi": "IPCA",
    "inflation": "IPCA",
    "precos12_ipca12": "IPCA",
    "gdp": "GDP",
    "pib": "GDP",
    "bm12_pibpm12": "GDP",
    "min_wage": "MIN_WAGE",
    "salario_minimo": "MIN_WAGE",
    "minimum_wage": "MIN_WAGE",
    "mte12_salmin12": "MIN_WAGE",
    "unemployment": "UNEMPLOYMENT",
    "desocupacao": "UNEMPLOYMENT",
    "pnadc": "UNEMPLOYMENT",
    "pnad": "UNEMPLOYMENT",
    "pnadc12_tdesoc12": "UNEMPLOYMENT",
    "bolsa_familia": "BOLSA_FAMILIA",
    "bf": "BOLSA_FAMILIA",
    "mds_bfcob": "BOLSA_FAMILIA",
}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _resolve(series_id: str) -> tuple[str, _Spec | None]:
    """Map a public series_id to (canonical_id, spec)."""
    key = _ALIASES.get(series_id.lower(), series_id)
    if key in _CATALOGUE:
        return key, _CATALOGUE[key]
    return series_id, None


def _request_json(url: str) -> Any:
    r = requests.get(
        url,
        timeout=120,
        headers={
            "User-Agent": "ieset-fetcher/1.0",
            "Accept": "application/json",
        },
    )
    if r.status_code == 404:
        raise IpeadataError(f"IPEADATA 404 for {url}")
    r.raise_for_status()
    try:
        return r.json()
    except ValueError as e:  # pragma: no cover
        raise IpeadataError(f"IPEADATA returned non-JSON for {url}: {e}")
    finally:
        time.sleep(_RATE_SLEEP_S)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _payload_to_frame(payload: Any, sercodigo: str) -> pd.DataFrame:
    """Reshape an OData ValoresSerie response into tidy records."""
    if not isinstance(payload, dict):
        raise IpeadataError(
            f"Unexpected IPEADATA payload shape: {type(payload).__name__}"
        )
    rows = payload.get("value")
    if not isinstance(rows, list):
        raise IpeadataError(
            f"IPEADATA payload missing 'value' list for {sercodigo}"
        )
    records: list[dict] = []
    for d in rows:
        if not isinstance(d, dict):
            continue
        valdata = d.get("VALDATA")
        date_iso: str | None = None
        year: int | None = None
        if isinstance(valdata, str) and valdata:
            # IPEADATA returns ISO-8601 with offset, e.g. "1994-07-01T00:00:00-03:00"
            try:
                date_iso = valdata[:10]
                year = int(valdata[:4])
            except (ValueError, TypeError):
                pass
        records.append(
            {
                "country_iso3": "BRA",
                "series_id": d.get("SERCODIGO") or sercodigo,
                "date": date_iso,
                "year": year,
                "value": d.get("VALVALOR"),
                "niv_nome": d.get("NIVNOME") or "",
                "ter_codigo": d.get("TERCODIGO") or "",
            }
        )
    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    sercodigo: str | None = None,
) -> FetchResult:
    """Fetch a Brazilian IPEADATA series via the OData v4 API.

    series_id: a key from the curated catalogue (e.g. 'IPCA', 'GDP',
               'MIN_WAGE', 'UNEMPLOYMENT', 'BOLSA_FAMILIA'), an alias
               ('cpi', 'pib', 'pnadc'), or a raw SERCODIGO string.
    sercodigo: explicit override — IPEADATA series code.
    """
    fetch_ts = utc_now()
    canonical, spec = _resolve(series_id)

    if sercodigo:
        eff_code = sercodigo
        label = f"raw:{sercodigo}"
        frequency = "unknown"
        units = "per IPEADATA metadata"
    elif spec is not None:
        eff_code = spec.sercodigo
        label = spec.label
        frequency = spec.frequency
        units = spec.units
    elif series_id and series_id.replace("_", "").isalnum():
        # Treat as raw SERCODIGO.
        eff_code = series_id
        label = f"raw:{series_id}"
        frequency = "unknown"
        units = "per IPEADATA metadata"
    else:
        raise IpeadataError(
            f"IPEADATA series_id {series_id!r} not in catalogue and no "
            f"sercodigo override. Known ids: {sorted(_CATALOGUE)}"
        )

    url = f"{BASE}/ValoresSerie(SERCODIGO='{eff_code}')"
    payload = _request_json(url)
    df = _payload_to_frame(payload, eff_code)
    if df.empty:
        raise IpeadataError(
            f"IPEADATA {series_id} ({url}) returned no observations"
        )

    path_out, sha = write_vintage(
        publisher="ipeadata",
        series_id=canonical,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = end = None
    if "date" in df.columns:
        dates = df["date"].dropna().astype(str)
        if not dates.empty:
            start = dates.min()
            end = dates.max()

    return FetchResult(
        publisher="ipeadata",
        series_id=canonical,
        source_url=url,
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=frequency,
        units=units,
        currency="BRL" if "PIB" in eff_code or "SALMIN" in eff_code else None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "label": label,
            "sercodigo": eff_code,
            "country_iso3": "BRA",
            "n_breakdowns": (
                int(df["niv_nome"].astype(str).nunique())
                if "niv_nome" in df.columns
                else 1
            ),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


SUPPORTED = sorted(_CATALOGUE)


__all__ = ["fetch", "IpeadataError", "SUPPORTED"]
