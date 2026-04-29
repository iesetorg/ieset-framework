"""Argentina fetcher: BCRA (central bank) + INDEC (via datos.gob.ar).

Two publishers share this module because their Argentine time series are
routinely co-queried for the monetary / fiscal-dominance hypothesis family
(hyperinflation_requires_fiscal_dominance, populist_peso_cycle, and the
Peronism-cycle pre-registered hypotheses). Argentina is the canonical case
for these analyses and IMF WEO / World Bank WDI data carry the 2007-2015
INDEC falsification attenuation, so direct BCRA + INDEC access matters.

BCRA API v4.0:
  Docs: https://www.bcra.gob.ar/Catalogo/APIs.asp
  Variables list: GET /estadisticas/v4.0/Monetarias
  Observations:   GET /estadisticas/v4.0/Monetarias/{idVariable}
                    ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
  (v3.0 and v2.0 were deprecated in 2025. v4.0 now returns a
  `results` array directly.)
  The BCRA SSL chain is periodically out-of-date; we disable verification and
  suppress the urllib3 InsecureRequestWarning. Public-domain statistics.

INDEC (via apis.datos.gob.ar):
  Docs: https://apis.datos.gob.ar/series/api/
  Observations:   GET /series/api/series?ids=<serie>&format=json&limit=5000
  Argentina open-data portal aggregates INDEC + other public series. CC-BY.
  NB: INDEC CPI and GDP deflator series for 2007-2015 are considered
  falsified by the profession; flagged in publishers.yaml (credibility_tier 2).
"""
from __future__ import annotations

import time
import warnings
from datetime import datetime, date
from typing import Any

import pandas as pd
import requests

try:  # suppress InsecureRequestWarning from BCRA's aging SSL cert chain
    from urllib3.exceptions import InsecureRequestWarning  # type: ignore
    warnings.simplefilter("ignore", InsecureRequestWarning)
except Exception:  # pragma: no cover - optional dependency path
    pass

from ._base import FetchResult, utc_now, write_vintage

BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
DATOS_BASE = "https://apis.datos.gob.ar/series/api/series"

BCRA_LICENSE = "Public Domain (BCRA)"
INDEC_LICENSE = "CC-BY 4.0 (Argentina datos.gob.ar / INDEC)"

# Mozilla-style UA: BCRA's edge blocks python-requests default UA sometimes.
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_HEADERS = {"User-Agent": _UA, "Accept": "application/json"}


class ArgentinaError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Top-level dispatch
# ---------------------------------------------------------------------------


def fetch(
    series_id: str,
    *,
    publisher_id: str = "bcra",
    vintage_utc: datetime | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    limit: int = 5000,
) -> FetchResult:
    """Fetch an Argentine macro series.

    Parameters
    ----------
    series_id:
        For publisher_id='bcra', the BCRA ``idVariable`` as a string
        (integer-valued; e.g. '15' for monetary base).
        For publisher_id='indec', the full datos.gob.ar series id, e.g.
        '148.3_INIVELNAL_DICI_M_26'.
    publisher_id:
        'bcra' or 'indec'. Selects API and vintage publisher tag.
    vintage_utc:
        Not used by either API (neither exposes a realtime/vintage parameter).
        Retained for interface parity with FRED; stored in extras.
    desde, hasta:
        Optional ISO dates (YYYY-MM-DD) narrowing the BCRA window. Ignored
        for INDEC (datos.gob.ar has no built-in date filter; full series
        returned up to ``limit``).
    limit:
        INDEC-only: max rows per datos.gob.ar call (API maximum is 5000).
    """
    pub = publisher_id.strip().lower()
    if pub == "bcra":
        return _fetch_bcra(
            series_id,
            vintage_utc=vintage_utc,
            desde=desde,
            hasta=hasta,
        )
    if pub == "indec":
        return _fetch_indec(
            series_id,
            vintage_utc=vintage_utc,
            limit=limit,
        )
    raise ArgentinaError(
        f"publisher_id must be 'bcra' or 'indec'; got {publisher_id!r}"
    )


# ---------------------------------------------------------------------------
# BCRA
# ---------------------------------------------------------------------------


def _bcra_get(url: str, params: dict[str, Any] | None = None) -> dict:
    last: Exception | None = None
    for attempt in (1, 2, 3):
        try:
            r = requests.get(
                url,
                params=params or {},
                headers=_HEADERS,
                timeout=60,
                verify=False,  # BCRA chain often expired; endpoint is public anyway
            )
        except requests.RequestException as e:
            last = e
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429 or 500 <= r.status_code < 600:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    raise ArgentinaError(f"BCRA retries exhausted for {url}: {last}")


def _bcra_variable_meta(id_variable: int) -> dict[str, Any]:
    """Look up human-readable metadata for idVariable in the catalog listing."""
    payload = _bcra_get(BCRA_BASE)
    results = payload.get("results") or []
    for row in results:
        if int(row.get("idVariable", -1)) == id_variable:
            return row
    return {}


def _fetch_bcra(
    series_id: str,
    *,
    vintage_utc: datetime | None,
    desde: str | None,
    hasta: str | None,
) -> FetchResult:
    try:
        id_variable = int(series_id)
    except ValueError as e:
        raise ArgentinaError(
            f"BCRA series_id must be an integer idVariable; got {series_id!r}"
        ) from e

    fetch_ts = utc_now()

    # BCRA caps server-side at ~3000 rows per call. A default desde of
    # 2000-01-01 covers well over the post-convertibility era; callers can
    # override for daily-series pulls that would blow that cap.
    if desde is None:
        desde = "2002-01-01"
    if hasta is None:
        hasta = date.today().isoformat()

    url = f"{BCRA_BASE}/{id_variable}"
    payload = _bcra_get(url, params={"desde": desde, "hasta": hasta, "limit": 3000})
    results = payload.get("results") or []
    # v4.0: results = [{"idVariable": N, "detalle": [{"fecha","valor"},...]}]
    # v3.0 was: results = [{"fecha","valor"},...] directly.
    obs: list = []
    if results and isinstance(results[0], dict) and "detalle" in results[0]:
        obs = results[0].get("detalle") or []
    else:
        obs = results
    if not obs:
        raise ArgentinaError(
            f"BCRA returned no observations for idVariable={id_variable} "
            f"in [{desde}, {hasta}]"
        )

    df = pd.DataFrame(obs)
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.sort_values("fecha").reset_index(drop=True)

    # Coerce any stray object columns to str so parquet (pyarrow) serialises
    # cleanly without inferring mixed types.
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str)

    meta = _bcra_variable_meta(id_variable)

    path, sha = write_vintage(
        publisher="bcra",
        series_id=str(id_variable),
        frame=df,
        fetch_utc=fetch_ts,
    )

    # Classify currency heuristically from description. Rates (TNA, %,
    # tasa), indices, and inflation readings are unit-less; monetary base,
    # reserves, deposits are stocks in ARS/USD.
    descripcion = str(meta.get("descripcion", ""))
    desc_lower = descripcion.lower()
    currency: str | None
    if any(k in desc_lower for k in ("reservas internacionales", "u$s", "usd", "dólar")):
        currency = "USD"
    elif any(k in desc_lower for k in ("tasa", "%", "inflación")):
        currency = None
    elif any(k in desc_lower for k in ("base monetaria", "m2", "m3", "depósitos", "pesos", "$")):
        currency = "ARS"
    else:
        currency = "ARS"

    start = df["fecha"].min().date().isoformat() if "fecha" in df.columns and len(df) else None
    end = df["fecha"].max().date().isoformat() if "fecha" in df.columns and len(df) else None

    return FetchResult(
        publisher="bcra",
        series_id=str(id_variable),
        source_url=f"{url}?desde={desde}&hasta={hasta}",
        methodology_url="https://www.bcra.gob.ar/PublicacionesEstadisticas/",
        license=BCRA_LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=_bcra_freq(descripcion),
        units=str(meta.get("unidad") or meta.get("descripcion") or "per BCRA catalog"),
        currency=currency,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path,
        extra={
            "descripcion": descripcion,
            "categoria": meta.get("categoria"),
            "desde": desde,
            "hasta": hasta,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _bcra_freq(descripcion: str) -> str:
    """Best-effort frequency classification from BCRA description strings."""
    d = descripcion.lower()
    if "mensual" in d or "i.p.c" in d or "ipc" in d:
        return "monthly"
    if "diaria" in d or "diario" in d:
        return "daily"
    if "trimestral" in d:
        return "quarterly"
    if "anual" in d:
        return "annual"
    # BCRA daily series dominate the /Monetarias catalog.
    return "daily"


# ---------------------------------------------------------------------------
# INDEC (via datos.gob.ar)
# ---------------------------------------------------------------------------


def _datos_get(params: dict[str, Any]) -> dict:
    last: Exception | None = None
    for attempt in (1, 2, 3):
        try:
            r = requests.get(DATOS_BASE, params=params, headers=_HEADERS, timeout=60)
        except requests.RequestException as e:
            last = e
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429 or 500 <= r.status_code < 600:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    raise ArgentinaError(f"datos.gob.ar retries exhausted: {last}")


def _fetch_indec(
    series_id: str,
    *,
    vintage_utc: datetime | None,
    limit: int,
) -> FetchResult:
    fetch_ts = utc_now()

    # Paginate: datos.gob.ar caps limit at 5000; step via start offset.
    all_rows: list[tuple[str, float | None]] = []
    start = 0
    step = max(1, min(limit, 5000))
    meta_payload: dict[str, Any] = {}
    while True:
        payload = _datos_get(
            {
                "ids": series_id,
                "format": "json",
                "limit": step,
                "start": start,
                "metadata": "full",
            }
        )
        if not meta_payload:
            meta_payload = payload
        rows = payload.get("data") or []
        if not rows:
            break
        for row in rows:
            # rows are ``[date, value, (more if multi-id)]``; single id requested.
            if len(row) >= 2:
                all_rows.append((row[0], row[1]))
        if len(rows) < step:
            break
        start += step
        time.sleep(0.25)  # small courtesy delay

    if not all_rows:
        raise ArgentinaError(f"datos.gob.ar returned no observations for {series_id}")

    df = pd.DataFrame(all_rows, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str)

    # Extract per-series metadata from the multi-id aware response shape.
    meta_block: dict[str, Any] = {}
    try:
        mb = meta_payload.get("meta") or []
        # meta[0] is dataset-level, meta[1:] are per-series
        for entry in mb[1:]:
            if entry.get("field", {}).get("id") == series_id or entry.get("field", {}).get("id_serie") == series_id:
                meta_block = entry
                break
        if not meta_block and len(mb) > 1:
            meta_block = mb[1]
    except Exception:
        meta_block = {}

    field = meta_block.get("field", {}) if isinstance(meta_block, dict) else {}
    dataset = meta_block.get("dataset", {}) if isinstance(meta_block, dict) else {}
    distribution = meta_block.get("distribution", {}) if isinstance(meta_block, dict) else {}
    frequency = field.get("periodicity") or field.get("frequency") or "unknown"
    units = field.get("units") or "per datos.gob.ar catalog"

    path, sha = write_vintage(
        publisher="indec",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="indec",
        series_id=series_id,
        source_url=f"{DATOS_BASE}?ids={series_id}&format=json",
        methodology_url=(
            distribution.get("landingPage")
            or dataset.get("landingPage")
            or "https://datos.gob.ar/"
        ),
        license=INDEC_LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=str(frequency),
        units=str(units),
        currency=None,
        start_date=df["date"].min().date().isoformat() if len(df) else None,
        end_date=df["date"].max().date().isoformat() if len(df) else None,
        sha256=sha,
        parquet_path=path,
        extra={
            "title": field.get("description") or field.get("title"),
            "dataset_title": dataset.get("title"),
            "publisher_name": dataset.get("publisher", {}).get("name")
            if isinstance(dataset.get("publisher"), dict) else None,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
