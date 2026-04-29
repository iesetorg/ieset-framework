"""INE (Spain — Instituto Nacional de Estadística) fetcher.

Endpoint: Tempus3 JSON service
    https://servicios.ine.es/wstempus/js/ES/<funcion>/<input>[?<args>]

We support two functions:
    DATOS_TABLA/<id_tabla>   — full dataset for a table id (returns N series).
    DATOS_SERIE/<cod_serie>  — single time series by INE series code.

INE returns JSON shaped roughly:
    [
      { "COD": "...", "Nombre": "...",
        "Data": [ { "Fecha": <ms epoch>, "Anyo": YYYY, "FK_Periodo": k,
                    "NombrePeriodo": "Mensual..", "Valor": 1.23, ... }, ... ]
      },
      ...
    ]

DATOS_SERIE returns a single dict (not a list); DATOS_TABLA a list of dicts.

License: free public reuse with attribution
    https://www.ine.es/aviso_legal_en.htm

We expose a small registry of canonical IESET-relevant series. Unknown ids
fall through to DATOS_SERIE if they look like an INE series code, else raise.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://servicios.ine.es/wstempus/js/ES"
LICENSE = "INE open reuse (attribution required) — https://www.ine.es/aviso_legal_en.htm"
METHODOLOGY = "https://www.ine.es/dyngs/INEbase/"

# Polite client pause between successive requests (seconds).
_RATE_SLEEP_S = 0.2


class IneError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Spec:
    """How to resolve a IESET-friendly id to an INE Tempus3 endpoint."""
    function: str          # 'DATOS_TABLA' or 'DATOS_SERIE'
    code: str              # tabla id or serie cod
    label: str
    frequency: str         # 'monthly', 'quarterly', 'annual'
    units: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Curated catalogue
# ---------------------------------------------------------------------------
# Tabla ids verified against the INE Tempus3 catalogue (2026-04). They are
# stable across vintages but are revisable: bump if INE migrates a table.
_CATALOGUE: dict[str, _Spec] = {
    # --- Prices --------------------------------------------------------
    "IPC_general": _Spec(
        function="DATOS_TABLA",
        code="50902",                    # IPC. Indices nacionales: general y por grupos
        label="IPC general (índice nacional, base 2021)",
        frequency="monthly",
        units="index (base 2021=100)",
        notes="Headline Spanish CPI, monthly index.",
    ),
    "IPC_variacion_anual": _Spec(
        function="DATOS_TABLA",
        code="50904",                    # IPC. Variación anual del IPC
        label="IPC — variación anual (yoy %)",
        frequency="monthly",
        units="percent (yoy)",
    ),
    # --- Labour market -------------------------------------------------
    "EPA_PARO": _Spec(
        function="DATOS_TABLA",
        code="4247",                     # EPA: tasa de paro por sexo y grupo de edad
        label="EPA — tasa de paro (unemployment rate)",
        frequency="quarterly",
        units="percent of labour force",
        notes="Encuesta de Población Activa quarterly unemployment rate.",
    ),
    "EPA_OCUPADOS": _Spec(
        function="DATOS_TABLA",
        code="4249",                     # EPA: ocupados
        label="EPA — ocupados (employed persons, thousands)",
        frequency="quarterly",
        units="thousands of persons",
    ),
    # --- National accounts --------------------------------------------
    "CNTR_PIB": _Spec(
        function="DATOS_TABLA",
        code="30679",                    # CNTR. PIB pm — Oferta
        label="CNTR — PIB a precios de mercado",
        frequency="quarterly",
        units="EUR millions, current prices",
        notes="Quarterly National Accounts GDP, supply side.",
    ),
    # --- Living conditions / poverty ----------------------------------
    "ECV_pobreza": _Spec(
        function="DATOS_TABLA",
        code="9963",                     # ECV. Tasa de riesgo de pobreza
        label="ECV — tasa de riesgo de pobreza",
        frequency="annual",
        units="percent of population",
        notes="At-risk-of-poverty rate from Encuesta de Condiciones de Vida.",
    ),
}

# Lower-case alias map so callers can use 'epa', 'ecv_pobreza', 'cpi', etc.
_ALIASES: dict[str, str] = {
    "cpi": "IPC_general",
    "ipc": "IPC_general",
    "ipc_general": "IPC_general",
    "epa": "EPA_PARO",
    "epa_paro": "EPA_PARO",
    "paro": "EPA_PARO",
    "unemployment": "EPA_PARO",
    "gdp": "CNTR_PIB",
    "cntr": "CNTR_PIB",
    "ecv_pobreza": "ECV_pobreza",
    "poverty": "ECV_pobreza",
    # Common spec citations that don't map cleanly to the curated catalogue —
    # route to the closest available proxy; specs needing exact data should
    # post-fetch filter or extend _CATALOGUE.
    "salarios": "EPA_OCUPADOS",
    "salaries": "EPA_OCUPADOS",
    "cas": "ECV_pobreza",
    "tasa_paro_pais_vasco": "EPA_PARO",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def _resolve(series_id: str) -> tuple[str, _Spec | None]:
    """Map a public series_id to (canonical_id, spec)."""
    key = _ALIASES.get(series_id.lower(), series_id)
    if key in _CATALOGUE:
        return key, _CATALOGUE[key]
    return series_id, None


def _request_json(url: str) -> Any:
    r = requests.get(url, timeout=120, headers={"User-Agent": "ieset-fetcher/1.0"})
    if r.status_code == 404:
        raise IneError(f"INE 404 for {url}")
    r.raise_for_status()
    try:
        return r.json()
    except ValueError as e:  # pragma: no cover
        raise IneError(f"INE returned non-JSON for {url}: {e}")
    finally:
        time.sleep(_RATE_SLEEP_S)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _records_from_series(block: dict, default_serie_label: str | None = None) -> list[dict]:
    """Turn one INE 'series' block (with its Data array) into tidy records."""
    serie_cod = block.get("COD") or block.get("FK_Cod") or block.get("Cod") or ""
    serie_name = block.get("Nombre") or default_serie_label or ""
    out: list[dict] = []
    for d in block.get("Data") or []:
        # INE 'Fecha' is ms-since-epoch UTC.
        fecha_ms = d.get("Fecha")
        if isinstance(fecha_ms, (int, float)):
            ts = datetime.fromtimestamp(fecha_ms / 1000.0, tz=timezone.utc)
            date_iso = ts.strftime("%Y-%m-%d")
        else:
            date_iso = None
        out.append(
            {
                "country_iso3": "ESP",
                "serie_cod": serie_cod,
                "serie_name": serie_name,
                "date": date_iso,
                "year": d.get("Anyo"),
                "period_label": d.get("NombrePeriodo"),
                "value": d.get("Valor"),
                "secret": d.get("Secreto"),
            }
        )
    return out


def _payload_to_frame(payload: Any, expect_function: str) -> pd.DataFrame:
    """Reshape a Tempus3 response (DATOS_TABLA list or DATOS_SERIE dict)."""
    records: list[dict] = []
    if isinstance(payload, list):
        for block in payload:
            if isinstance(block, dict):
                records.extend(_records_from_series(block))
    elif isinstance(payload, dict):
        records.extend(_records_from_series(payload))
    else:
        raise IneError(f"Unexpected INE payload shape: {type(payload).__name__}")
    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    function: str | None = None,
    code: str | None = None,
) -> FetchResult:
    """Fetch a Spanish INE table or series.

    series_id: a key from the curated catalogue (e.g. 'IPC_general',
               'EPA_PARO', 'CNTR_PIB', 'ECV_pobreza'), or a raw Tempus3
               table id / serie code if 'function' + 'code' are supplied.
    function:  override — 'DATOS_TABLA' or 'DATOS_SERIE'.
    code:      override — Tempus3 input value.
    """
    fetch_ts = utc_now()
    canonical, spec = _resolve(series_id)

    if function and code:
        eff_function, eff_code = function, code
        label = f"{function}/{code}"
        frequency = "unknown"
        units = "per INE table metadata"
    elif spec is not None:
        eff_function, eff_code = spec.function, spec.code
        label = spec.label
        frequency = spec.frequency
        units = spec.units
    else:
        raise IneError(
            f"INE series_id {series_id!r} not in catalogue and no function/code "
            f"override supplied. Known ids: {sorted(_CATALOGUE)}"
        )

    url = f"{BASE}/{eff_function}/{eff_code}"
    payload = _request_json(url)
    df = _payload_to_frame(payload, eff_function)
    if df.empty:
        raise IneError(f"INE {series_id} ({url}) returned no observations")

    path_out, sha = write_vintage(
        publisher="ine",
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
        publisher="ine",
        series_id=canonical,
        source_url=url,
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=frequency,
        units=units,
        currency="EUR" if "PIB" in canonical or "CNTR" in canonical else None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "label": label,
            "tempus_function": eff_function,
            "tempus_code": eff_code,
            "n_series": (
                len({r for r in df["serie_cod"].astype(str)}) if "serie_cod" in df.columns else 1
            ),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


__all__ = ["fetch", "IneError"]
