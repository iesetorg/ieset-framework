#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = panel_fe (or
panel_fe_decomposition).

For each spec, this script:

  1. Resolves variable source tokens (publisher:series) against
     data/vintages/<publisher>/<series>/<latest>.parquet.
  2. Normalises each variable parquet to (country_iso3, year, value).
  3. Pivots into a long-form panel (country × year × {outcome, treatment,
     controls}).
  4. Fits a PanelOLS regression with the spec's `estimator.fixed_effects`
     and country-clustered SEs.
  5. Compares the treatment coefficient direction + p-value to the
     `falsification.rule` and writes a verdict.
  6. Writes engine/runs/<hid>/result_card.md and diagnostics.json.

Verdicts:
  SUPPORTED                  — coefficient sign matches the claim AND p < 0.10.
  REFUTED                    — coefficient sign opposite the claim AND p < 0.10.
  PARTIAL                    — coefficient sign matches but p >= 0.10, OR
                                opposite sign with p >= 0.10.
  INCONCLUSIVE_DATA_PENDING  — outcome variable could not be loaded from
                                vintages (data not yet fetched / publisher
                                schema unknown).

Usage:
    python3 scripts/run_panel_fe.py <hypothesis_id>
    python3 scripts/run_panel_fe.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages"
RUNS = ROOT / "engine" / "runs"
PUBLISHERS_YAML = ROOT / "data" / "fetchers" / "publishers.yaml"

_ISO2_TO_ISO3 = {
    "AR": "ARG", "AT": "AUT", "AU": "AUS", "BE": "BEL", "BG": "BGR",
    "BR": "BRA", "CA": "CAN", "CH": "CHE", "CL": "CHL", "CN": "CHN",
    "CO": "COL", "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK",
    "EE": "EST", "EG": "EGY", "EL": "GRC", "ES": "ESP", "EU": "U2",
    "FI": "FIN", "FR": "FRA", "GB": "GBR", "GR": "GRC", "HK": "HKG",
    "HR": "HRV", "HU": "HUN", "ID": "IDN", "IE": "IRL", "IL": "ISR",
    "IN": "IND", "IS": "ISL", "IT": "ITA", "JP": "JPN", "KR": "KOR",
    "LT": "LTU", "LU": "LUX", "LV": "LVA", "MA": "MAR", "MT": "MLT",
    "MX": "MEX", "MY": "MYS", "NL": "NLD", "NO": "NOR", "NZ": "NZL",
    "PE": "PER", "PH": "PHL", "PK": "PAK", "PL": "POL", "PT": "PRT",
    "RO": "ROU", "RU": "RUS", "SE": "SWE", "SG": "SGP", "SI": "SVN",
    "SK": "SVK", "TH": "THA", "TR": "TUR", "TN": "TUN", "TW": "TWN",
    "UA": "UKR", "UK": "GBR", "US": "USA", "VN": "VNM", "ZA": "ZAF",
}

_COUNTRY_NAME_TO_ISO3 = {
    "UNITED STATES": "USA",
    "UNITED KINGDOM": "GBR",
    "GREAT BRITAIN": "GBR",
    "JAPAN": "JPN",
    "KOREA": "KOR",
    "SOUTH KOREA": "KOR",
    "REPUBLIC OF KOREA": "KOR",
    "GERMANY": "DEU",
    "FRANCE": "FRA",
    "ITALY": "ITA",
    "SPAIN": "ESP",
    "NETHERLANDS": "NLD",
    "BELGIUM": "BEL",
    "AUSTRIA": "AUT",
    "IRELAND": "IRL",
    "PORTUGAL": "PRT",
    "FINLAND": "FIN",
    "GREECE": "GRC",
    "SWEDEN": "SWE",
    "SWITZERLAND": "CHE",
    "DENMARK": "DNK",
    "CANADA": "CAN",
    "AUSTRALIA": "AUS",
    "NEW ZEALAND": "NZL",
    "ARGENTINA": "ARG",
    "BAHAMAS": "BHS",
    "BARBADOS": "BRB",
    "BOLIVIA": "BOL",
    "BRAZIL": "BRA",
    "CHILE": "CHL",
    "COLOMBIA": "COL",
    "COSTA RICA": "CRI",
    "DOMINICAN REPUBLIC": "DOM",
    "ECUADOR": "ECU",
    "EL SALVADOR": "SLV",
    "GUATEMALA": "GTM",
    "HAITI": "HTI",
    "HONDURAS": "HND",
    "JAMAICA": "JAM",
    "MEXICO": "MEX",
    "NICARAGUA": "NIC",
    "PANAMA": "PAN",
    "PARAGUAY": "PRY",
    "PERU": "PER",
    "TRINIDAD AND TOBAGO": "TTO",
    "URUGUAY": "URY",
    "QUEBEC": "CAN",
}

_ISO3_TO_COUNTRY_NAMES: dict[str, set[str]] = {}
for _country_name, _iso3 in _COUNTRY_NAME_TO_ISO3.items():
    _ISO3_TO_COUNTRY_NAMES.setdefault(_iso3, set()).add(_country_name)

_EU_MEMBER_ISO3 = {
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
    "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
    "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
}

_CONSTRUCTED_GROUP_ALIASES = {
    "founding eurozone members": {
        "AUT", "BEL", "DEU", "ESP", "FIN", "FRA", "IRL", "ITA", "LUX",
        "NLD", "PRT",
    },
    "eurozone founding members": {
        "AUT", "BEL", "DEU", "ESP", "FIN", "FRA", "IRL", "ITA", "LUX",
        "NLD", "PRT",
    },
    "original asean-6": {"BRN", "IDN", "MYS", "PHL", "SGP", "THA"},
    "asean-6": {"BRN", "IDN", "MYS", "PHL", "SGP", "THA"},
    "first-six ratifying members": {"AUS", "CAN", "JPN", "MEX", "NZL", "SGP"},
    "nordic universalist welfare": {"DNK", "FIN", "NOR", "SWE"},
    "nordic": {"DNK", "FIN", "ISL", "NOR", "SWE"},
    "germanic mittelstand model": {"AUT", "CHE", "DEU"},
    "oecd countries with universal coverage": {
        "AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "COL", "CRI", "CZE", "DEU",
        "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HUN", "IRL", "ISL",
        "ISR", "ITA", "JPN", "KOR", "LTU", "LUX", "LVA", "MEX", "NLD", "NOR",
        "NZL", "POL", "PRT", "SVK", "SVN", "SWE", "TUR",
    },
    "bismarckian": {"AUT", "BEL", "CHE", "DEU", "FRA", "NLD"},
    "beveridgean": {"DNK", "FIN", "GBR", "IRL", "ITA", "NOR", "PRT", "SWE"},
    "eu dg comp jurisdictions": _EU_MEMBER_ISO3,
    "dg comp jurisdictions": _EU_MEMBER_ISO3,
}


def _load_publisher_alias_map() -> dict[str, str]:
    alias_map: dict[str, str] = {}
    if not PUBLISHERS_YAML.exists():
        return alias_map
    try:
        doc = yaml.safe_load(PUBLISHERS_YAML.read_text()) or {}
    except Exception:
        return alias_map
    for canonical, rec in (doc.get("publishers") or {}).items():
        alias_map[str(canonical)] = str(canonical)
        for alias in rec.get("aliases", []) or []:
            alias_map[str(alias)] = str(canonical)
    return alias_map


PUBLISHER_ALIAS_MAP = _load_publisher_alias_map()
SERIES_ALIAS_BY_PUBLISHER = {
    "bis": {
        "WS_EER_M": "WS_EER",
        "WS_SPP_RPP": "WS_SPP",
        # Practical bridge: the on-disk credit-gap panel carries the
        # credit-to-GDP level used by these shorthand spec ids.
        "WS_CREDIT": "WS_CREDIT_GAP",
        "WS_TC": "WS_CREDIT_GAP",
        "TOTAL_CREDIT_TO_PRIVATE_NONFINANCIAL_SECTOR": "WS_CREDIT_GAP",
        "TOTAL_CREDIT_NONFINANCIAL_CORPORATES_TO_GDP": "WS_CREDIT_GAP",
        "REER_BROAD_ARS": "WS_EER",
        "REER_BROAD_ILS": "WS_EER",
        "REER_BROAD_KRW": "WS_EER",
        "REER_BROAD_SEK": "WS_EER",
    },
    "imf_pcps": {
        "PRIMARY": "PALLFNF",
        "OIL": "POILAPSP",
        "PNG_USD": "PNGASEU",
    },
    "boe": {
        "BANK_RATE": "IUDBEDR",
        "GILT_10Y": "IUDMNZC",
    },
    "bcra": {
        "EXCHANGE_RATE_OFFICIAL": "4",
        "FX_OFFICIAL": "4",
        "INFLATION_MONTHLY": "27",
    },
    "irena": {
        "CAPACITY": "installed_capacity_renewable",
        "SOLAR_PV_COSTS": "lcoe_solar_pv",
        "WIND_LCOE": "lcoe_wind_onshore",
    },
    "oecd": {
        "CPI": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
        "CPI:CORE": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
        "DSD_PRICES": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
        "DSD_PRICES@DF_PRICES_N_CP": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
        "DSD_TU@DF_TUD": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
        "DSD_TU@DF_CBC": "OECD.ELS.SAE,DSD_TUD_CBC@DF_CBC,1.0",
        "DSD_TU@DF_TU": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
        "OECD.ELS.SAE,DSD_TU@DF_TUD,1.0": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
        "OECD.ELS.SAE,DSD_TU@DF_CBC,1.0": "OECD.ELS.SAE,DSD_TUD_CBC@DF_CBC,1.0",
        "TUD": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
        "TRADE_UNION_DENSITY": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
        "EPL_OV": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
        "EPL_INDICATORS": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
        "HOUSE_PRICES": "OECD.SDD.PIN,DSD_RHPI@DF_RHPI,1.0",
        "HEALTH_STAT@DF_AMENABLE_MORT": "OECD.ELS.HD,DSD_HEALTH_STAT@DF_AMENABLE_MORT,1.0",
        "DSD_IDD": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
        "DSD_IDD@DF_IDD": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
        "DSD_IDD@DF_CHILD_POV": "OECD.WISE.INE,DSD_IDD@DF_CHILD_POV,1.0",
        "POVERTY": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
        "MWUSD": "OECD.ELS.SAE,DSD_EARN@DF_MW_DOL_RPP,1.0",
        "DSD_EARN": "OECD.ELS.SAE,DSD_EARN@DF_EARN_LFS,1.0",
        "DSD_EARNINGS": "OECD.SDD.TPS,DSD_EARNINGS@DF_EARNINGS,1.0",
        "NEET": "OECD.ELS.EMP,DSD_LFS@DF_NEET,1.0",
        "OUTGAP": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
        "OUTPUTGAP": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
        "DSD_KEI": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
        "DSD_PDB": "OECD.SDD.TPS,DSD_PDB@DF_PDB_PT,1.0",
        "DSD_PENSIONS@DF_PENSIONS_REPL_RATE": "OECD.ELS.SAE,DSD_PENSIONS@DF_PENSIONS_REPL_RATE,1.0",
        "DSD_SOCX@DF_SOCX_AGG": "OECD.ELS.SOC,DSD_SOCX@DF_SOCX_AGG,1.0",
        "DSD_SOCX@DF_SOCX_ALMP": "OECD.ELS.SOC,DSD_SOCX@DF_SOCX_ALMP,1.0",
        "DSD_TAX": "OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1",
        "FDI_STATISTICS": "OECD.DAF.INV,DSD_FDI@DF_FDI_FLOWS,1.0",
        "HFCE": "OECD.SDD.NAD,DSD_NAMAIN1@DF_HFCE,1.0",
        "GOVEXP": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
        "GOV_EXP": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
        "GGEXP": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
        "STAN": "OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0",
        "STAN_VA": "OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0",
    },
}
SOURCE_BRIDGES = {
    # Canonical upstream already exists locally; keep specs stable and
    # resolve to the better-supported publisher at load time.
    ("owid", "capital-account-openness"): ("chinn_ito", "kaopen_index_normalized"),
    ("owid", "top-0-1-share-of-total-income"): ("wid", "top-0-1-share-of-total-income"),
    ("boe", "CPI_UK"): ("ons", "D7BT"),
    ("imf", "general_government_gross_debt_pct_gdp"): ("imf", "GGXWDG_NGDP"),
    ("imf", "WEO_GGXWDG_NGDP"): ("imf", "GGXWDG_NGDP"),
    ("imf", "WEO.NGAP_NPGDP"): ("imf", "NGAP_NPGDP"),
    ("imf", "ENDA_XDC_USD_RATE"): ("world_bank_wdi", "PA.NUS.FCRF"),
}


def resolve_source_target(publisher: str, series: str) -> tuple[str, str]:
    """Resolve publisher aliases, cross-publisher bridges, and series aliases."""
    publisher = PUBLISHER_ALIAS_MAP.get(publisher, publisher)
    series = str(series).strip()
    bridge = SOURCE_BRIDGES.get((publisher, series))
    if bridge is None:
        bridge = SOURCE_BRIDGES.get((publisher, series.lower()))
    if bridge is not None:
        publisher, series = bridge
    series = SERIES_ALIAS_BY_PUBLISHER.get(publisher, {}).get(series.upper(), series)
    return publisher, series

# ---------------------------------------------------------------------------
# Vintage resolution
# ---------------------------------------------------------------------------

_OECD_DATAFLOW_CACHE: list[dict[str, str | None]] | None = None


def _normalise_series_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _load_oecd_dataflows() -> list[dict[str, str | None]]:
    """Cache the OECD dataflow catalogue once per process."""
    global _OECD_DATAFLOW_CACHE
    if _OECD_DATAFLOW_CACHE is not None:
        return _OECD_DATAFLOW_CACHE
    try:
        import requests

        r = requests.get(
            "https://sdmx.oecd.org/public/rest/dataflow/all/all/latest",
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 IESET"},
        )
        r.raise_for_status()
        ns = {
            "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
            "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
        }
        root = ET.fromstring(r.text)
        flows: list[dict[str, str | None]] = []
        for df in root.findall(".//s:Dataflow", ns):
            names = df.findall(".//c:Name", ns)
            name = next(
                (
                    n.text
                    for n in names
                    if n.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") == "en"
                ),
                names[0].text if names else "",
            )
            flows.append(
                {
                    "agencyID": df.attrib.get("agencyID"),
                    "id": df.attrib.get("id"),
                    "version": df.attrib.get("version") or "1.0",
                    "name": name,
                }
            )
        _OECD_DATAFLOW_CACHE = flows
    except Exception:
        _OECD_DATAFLOW_CACHE = []
    return _OECD_DATAFLOW_CACHE


def _resolve_oecd_urn_by_keyword(spec_urn: str) -> str | None:
    """Resolve common stale OECD DSD/DF citations against the live catalogue."""
    flows = _load_oecd_dataflows()
    if not flows:
        return None
    tokens = re.findall(r"(?:DSD|DF)_[A-Z0-9_]+", spec_urn.upper())
    if not tokens:
        return None
    norm_tokens = [_normalise_series_token(t) for t in tokens]

    best: tuple[int, dict[str, str | None]] | None = None
    for flow in flows:
        haystack = _normalise_series_token(
            " ".join(str(flow.get(k) or "") for k in ("agencyID", "id", "name"))
        )
        score = sum(1 for token in norm_tokens if token and token in haystack)
        if score and (best is None or score > best[0]):
            best = (score, flow)

    if best is None:
        return None
    flow = best[1]
    agency = flow.get("agencyID")
    flow_id = flow.get("id")
    version = flow.get("version") or "1.0"
    if not agency or not flow_id:
        return None
    return f"{agency},{flow_id},{version}"


def latest_vintage(publisher: str, series: str) -> Path | None:
    """Return the most recent .parquet under data/vintages/<publisher>/<series>/.

    Different fetchers use different on-disk layouts:
      - world_bank_wdi: data/vintages/world_bank_wdi/<series>@<utc>.parquet
      - eurostat:       data/vintages/eurostat/<dataset>@<utc>.parquet
      - oecd:           data/vintages/oecd/<full-SDMX-URN-with-dots-and-commas-mangled>@<utc>.parquet
        (e.g. "OECD.SDD.TPS,DSD_TU@DF_TUD,1.0" becomes "OECD.SDD.TPS_DSD_TU_DF_TUD_1.0")
      - fred / boj / ecb: a few use nested <series>/<utc>.parquet directories.

    Try several patterns:
      1. Exact: data/vintages/<pub>/<series>@*.parquet
      2. Nested: data/vintages/<pub>/<series>/*.parquet
      3. Fuzzy contains: any file whose name (with @ and , and : stripped) contains the series.
    """
    publisher, series = resolve_source_target(publisher, series)
    pub_dir = VINTAGES / publisher
    if not pub_dir.exists():
        return None

    # 1. Exact prefix match: <series>@... or <series>.parquet
    candidates = list(pub_dir.glob(f"{series}@*.parquet"))
    candidates.extend(pub_dir.glob(f"{series}.parquet"))
    # 2. Nested directory layout
    nested = pub_dir / series
    if nested.exists():
        candidates.extend(nested.glob("*.parquet"))
    # 3. Fuzzy: normalise both filename and series, look for substring containment.
    if not candidates:
        target = _normalise_series_token(series)
        for f in pub_dir.glob("*.parquet"):
            stem = f.stem.split("@", 1)[0]  # drop UTC stamp
            if target and target in _normalise_series_token(stem):
                candidates.append(f)
        # Also peek into one level of subdirectory
        for sub in pub_dir.iterdir():
            if sub.is_dir():
                for f in sub.glob("*.parquet"):
                    stem = f.stem.split("@", 1)[0]
                    if target and (
                        target in _normalise_series_token(stem)
                        or target in _normalise_series_token(sub.name)
                    ):
                        candidates.append(f)
    if not candidates and publisher == "oecd":
        resolved = _resolve_oecd_urn_by_keyword(series)
        if resolved and resolved != series:
            SERIES_ALIAS_BY_PUBLISHER.setdefault("oecd", {})[series.upper()] = resolved
            return latest_vintage(publisher, resolved)
    if not candidates:
        return None
    # Lexicographic max picks most recent UTC stamp.
    return max(candidates, key=lambda p: p.name)


def normalise_country_code(value: object) -> str | None:
    """Convert common publisher country codes to the repo's ISO3 convention."""
    if value is None or pd.isna(value):
        return None
    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none"}:
        return None
    upper = raw.upper()
    if upper in _ISO2_TO_ISO3:
        return _ISO2_TO_ISO3[upper]
    if upper in _COUNTRY_NAME_TO_ISO3:
        return _COUNTRY_NAME_TO_ISO3[upper]
    if len(upper) == 3 and upper.isalpha():
        return upper
    return upper


def normalise_panel(df: pd.DataFrame, publisher: str) -> pd.DataFrame | None:
    """Project an arbitrary publisher's parquet schema onto (country_iso3, year, value).

    Returns None if the schema can't be normalised.
    """
    cols = {c.lower(): c for c in df.columns}
    # Discover the country column.
    country_col = None
    for cand in ("country_iso3", "iso3", "ccode", "geo_code", "country", "ref_area", "region"):
        if cand in cols:
            country_col = cols[cand]
            break
    if country_col is None:
        # Single-country fetchers (FRED, BoE) — country defaults to a publisher-specific code.
        single_country_fallback = {
            "fred": "USA", "bls": "USA", "boe": "GBR", "boj": "JPN",
            "shiller": "USA", "rba": "AUS", "apra": "AUS", "statcan": "CAN",
            "bcra": "ARG", "bcv": "VEN", "cbr": "RUS", "cia": "USA",
            "destatis": "DEU", "destatis_germany": "DEU",
        }
        if publisher in single_country_fallback:
            df = df.copy()
            df["country_iso3"] = single_country_fallback[publisher]
            country_col = "country_iso3"
        else:
            return None
    # Discover the year column.
    year_col = None
    for cand in ("year", "period", "date", "obs_date", "time_period"):
        if cand in cols:
            year_col = cols[cand]
            break
    if year_col is None:
        return None
    # Discover the value column.
    value_col = None
    for cand in ("value", "obs_value", "gdppc", "rgdpe", "rgdpe_pc", "rtfpna",
                 "labsh", "v2x_polyarchy", "polity2", "freedom_house_score"):
        if cand in cols:
            value_col = cols[cand]
            break
    if value_col is None:
        # Maddison-style: pick the first numeric column that isn't year/pop.
        for c in df.columns:
            if c not in (country_col, year_col) and pd.api.types.is_numeric_dtype(df[c]):
                value_col = c
                break
    if value_col is None:
        return None

    out = df[[country_col, year_col, value_col]].copy()
    out.columns = ["country_iso3", "year", "value"]
    out["country_iso3"] = out["country_iso3"].map(normalise_country_code)
    # Coerce year — eurostat 'period' is sometimes "2020-Q1" or "2020-01"; take year prefix.
    if not pd.api.types.is_numeric_dtype(out["year"]):
        year_text = out["year"].astype(str).str.extract(r"((?:19|20)\d{2})", expand=False)
        out["year"] = pd.to_numeric(year_text, errors="coerce")
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["country_iso3", "year", "value"])
    # If multiple rows per (country, year), aggregate via mean (handles SDMX dim duplicates).
    out = out.groupby(["country_iso3", "year"], as_index=False)["value"].mean()
    return out


def parse_source(token: str) -> tuple[str, str] | None:
    """Parse a SINGLE 'publisher:series' token. For multi-fallback strings
    (e.g. 'ons:CDKO; world_bank_wdi:FP.CPI.TOTL.ZG'), use parse_sources()."""
    m = re.match(r"^\s*([a-z][a-z0-9_]*)\s*:\s*(.+?)\s*$", token)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def parse_sources(source: str) -> list[tuple[str, str]]:
    """Parse a source string into one or more (publisher, series) candidates.

    Many hypothesis specs use ';'-delimited fallback chains, e.g.
    'ons:CDKO; world_bank_wdi:FP.CPI.TOTL.ZG'. Loaders should iterate these
    candidates in order, returning the first one whose vintage resolves.
    """
    out: list[tuple[str, str]] = []
    for rec in parse_source_clauses(source):
        out.append((rec["publisher"], rec["series"]))
    return out


def parse_source_clauses(source: str) -> list[dict]:
    """Parse a ';'-delimited source chain, preserving trailing qualifiers."""
    out: list[dict] = []
    for raw in (source or "").split(";"):
        part = raw.strip()
        if not part or ":" not in part:
            continue
        pub, _, series = part.partition(":")
        qualifier = None
        qm = re.search(r"\(([^)]*)\)\s*$", series)
        if qm:
            qualifier = qm.group(1).strip()
            series = series[:qm.start()].strip()
        series = series.rstrip(",.; ")
        if pub.strip() and series:
            out.append(
                {
                    "publisher": pub.strip(),
                    "series": series,
                    "qualifier": qualifier,
                    "raw": part,
                }
            )
    return out


_META_PREFIXES = {"constructed", "derived", "manual", "academic", "proxies",
                  "fallback", "microdata", "dates"}


def load_variable(source: str) -> tuple[pd.DataFrame, str] | None:
    """Try each candidate (publisher, series) in the source string in order
    and return the first one whose vintage exists and parses.

    Supports ';'-delimited fallback chains.
    """
    clauses = parse_source_clauses(source)
    if not clauses:
        return None

    # Heuristic: qualifier-bearing chains are usually country-specific source unions
    # rather than true fallbacks, e.g. "fred:... (USA); world_bank_wdi:... (rest)".
    if len(clauses) > 1 and any(clause.get("qualifier") for clause in clauses):
        explicit_countries: set[str] = set()
        for clause in clauses:
            explicit_countries.update(extract_qualifier_countries(clause.get("qualifier")))
        frames: list[pd.DataFrame] = []
        pubs: list[str] = []
        for priority, clause in enumerate(clauses):
            canonical_pub, canonical_series = resolve_source_target(
                clause["publisher"],
                clause["series"],
            )
            if canonical_pub in _META_PREFIXES:
                continue
            path = latest_vintage(canonical_pub, canonical_series)
            if path is None:
                continue
            try:
                df = pd.read_parquet(path)
            except Exception:
                continue
            panel = normalise_panel(df, canonical_pub)
            if panel is None or panel.empty:
                continue
            panel = apply_source_qualifier(panel, clause.get("qualifier"), explicit_countries)
            if panel.empty:
                continue
            panel = panel.copy()
            panel["_priority"] = priority
            frames.append(panel)
            pubs.append(canonical_pub)
        if frames:
            merged = pd.concat(frames, ignore_index=True)
            merged = (
                merged.sort_values(["country_iso3", "year", "_priority"])
                .drop_duplicates(subset=["country_iso3", "year"], keep="first")
                .drop(columns="_priority")
            )
            return merged, "+".join(dict.fromkeys(pubs))

    for clause in clauses:
        canonical_pub, canonical_series = resolve_source_target(
            clause["publisher"],
            clause["series"],
        )
        if canonical_pub in _META_PREFIXES:
            continue
        path = latest_vintage(canonical_pub, canonical_series)
        if path is None:
            continue
        try:
            df = pd.read_parquet(path)
        except Exception:
            continue
        panel = normalise_panel(df, canonical_pub)
        if panel is None or panel.empty:
            continue
        return panel, canonical_pub
    return None


def first_loaded_var(items: list[dict], panel: pd.DataFrame) -> str | None:
    """Return the name of the first variable in `items` whose data is in
    panel.columns. Used by runners to fall through outcome/treatment lists
    when the primary item's data isn't on disk but a secondary is.
    """
    for item in items or []:
        name = item.get("name")
        if name and name in panel.columns and panel[name].notna().any():
            return name
    return None


def _extract_year_like(text: str) -> int | None:
    m = re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", text or "")
    return int(m.group(1)) if m else None


def _extract_year_window(text: str) -> tuple[int, int] | None:
    years = [int(y) for y in re.findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", text or "")]
    if not years:
        return None
    if len(years) == 1:
        return years[0], years[0]
    return min(years), max(years)


def _sample_countries(spec: dict) -> list[str]:
    sample = spec.get("sample") or {}
    countries = []
    for raw in sample.get("countries") or []:
        iso3 = normalise_country_code(raw)
        if iso3:
            countries.append(iso3)
    return list(dict.fromkeys(countries))


def _base_constructed_grid(
    spec: dict,
    existing_frames: list[pd.DataFrame] | None = None,
    panel: pd.DataFrame | None = None,
) -> pd.DataFrame | None:
    sample = spec.get("sample") or {}
    countries = _sample_countries(spec)
    period = sample.get("period") or [None, None]
    start = period[0]
    end = period[1]
    if countries and start is not None and end is not None:
        years = list(range(int(start), int(end) + 1))
        return pd.MultiIndex.from_product(
            [countries, years], names=["country_iso3", "year"]
        ).to_frame(index=False)

    frames = list(existing_frames or [])
    if panel is not None and not panel.empty:
        frames.append(panel)
    if frames:
        merged = pd.concat(
            [f[["country_iso3", "year"]] for f in frames if not f.empty],
            ignore_index=True,
        ).dropna().drop_duplicates()
        if not merged.empty:
            merged["year"] = pd.to_numeric(merged["year"], errors="coerce").astype("Int64")
            merged = merged.dropna(subset=["country_iso3", "year"]).copy()
            merged["year"] = merged["year"].astype(int)
            return merged.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    return None


def _expand_constructed_country_targets(text: str, sample_countries: list[str]) -> set[str]:
    targets: set[str] = set()
    if not text:
        return targets

    upper = text.upper()
    for token in re.findall(r"\b[A-Z]{2,3}\b", upper):
        iso3 = normalise_country_code(token)
        if iso3 and iso3 != "U2":
            targets.add(iso3)

    lowered = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    for country_name, iso3 in _COUNTRY_NAME_TO_ISO3.items():
        name_key = re.sub(r"[^a-z0-9]+", " ", country_name.lower()).strip()
        if name_key and name_key in lowered:
            if not sample_countries or iso3 in sample_countries:
                targets.add(iso3)
    for phrase, members in _CONSTRUCTED_GROUP_ALIASES.items():
        if phrase in lowered:
            if sample_countries:
                targets.update(m for m in members if m in sample_countries)
            else:
                targets.update(members)
    if "eu member state" in lowered or "eu member states" in lowered:
        if sample_countries:
            targets.update(c for c in sample_countries if c in _EU_MEMBER_ISO3)
        else:
            targets.update(_EU_MEMBER_ISO3)
    return targets


def construct_variable_from_text(
    spec: dict,
    item: dict,
    *,
    existing_frames: list[pd.DataFrame] | None = None,
    panel: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, str] | None:
    """Build a simple binary/time dummy from a `constructed:` source string."""
    source = (item.get("source") or "")
    if not source.lower().lstrip().startswith("constructed:"):
        return None

    body = source.split(":", 1)[1].strip()
    name = item.get("name") or "constructed_variable"
    grid = _base_constructed_grid(spec, existing_frames=existing_frames, panel=panel)
    if grid is None or grid.empty:
        return None

    out = grid.copy()
    out[name] = 0.0
    sample_countries = sorted(out["country_iso3"].dropna().astype(str).unique().tolist())
    applied = False

    def apply_assignment(
        countries: set[str] | None,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> None:
        nonlocal applied
        mask = pd.Series(True, index=out.index)
        if countries:
            valid = [c for c in countries if c in sample_countries]
            if not valid:
                return
            mask &= out["country_iso3"].isin(valid)
        if start_year is not None:
            mask &= out["year"] >= int(start_year)
        if end_year is not None:
            mask &= out["year"] <= int(end_year)
        if not mask.any():
            return
        out.loc[mask, name] = 1.0
        applied = True

    stripped = body.strip()
    global_window = re.search(
        r"\b(?:indicator|binary)?\s*=?\s*1\s*for\s*(\d{4}(?:[/-]?Q?\d+)?(?:\s*(?:-|to|through)\s*\d{4}(?:[/-]?Q?\d+)?)?)",
        stripped,
        flags=re.I,
    )
    if global_window:
        years = _extract_year_window(global_window.group(1))
        if years is not None:
            apply_assignment(None, years[0], years[1])

    for pat in (
        r"\b0\s+pre[-\s/]*(\d{4}(?:[-/]?Q?\d+)?)\s*,\s*1\s+from\s+(\d{4}(?:[-/]?Q?\d+)?)\s+onward",
        r"\b(?:indicator|binary)?\s*=?\s*1\s+from\s+(\d{4}(?:[-/]?Q?\d+)?)\s+onward",
        r"\b(?:indicator|binary)?\s*=?\s*1\s+from\s+(\d{4}(?:[-/]?Q?\d+)?)\s+onwards",
        r"\b(?:indicator|binary)?\s*=?\s*1\s+for\s+year\s*>=\s*(\d{4})",
        r"\b(?:indicator|binary)?\s*=?\s*1\s+for\s+years\s*>=\s*(\d{4})",
        r"\b(?:indicator|binary)?\s*=?\s*1\s+for\s+quarters\s*>=\s*(\d{4}(?:Q\d)?)",
    ):
        gm = re.search(pat, stripped, flags=re.I)
        if not gm:
            continue
        years = _extract_year_window(" ".join(g for g in gm.groups() if g))
        if years is not None:
            apply_assignment(None, years[0], years[1] if len(years) > 1 else None)

    segments = [seg.strip() for seg in re.split(r";|\.\s+", body) if seg.strip()]
    for seg in segments:
        segment = seg
        segment = re.sub(r"^(?:indicator|binary)\s*=\s*1\s*for\s+", "", segment, flags=re.I)
        segment = re.sub(r"^(?:indicator|binary)\s*for\s+", "", segment, flags=re.I)
        segment = re.sub(r"^1\s*for\s+", "", segment, flags=re.I)
        segment = re.sub(r"^\(?0\s+for\b.*$", "", segment, flags=re.I).strip()
        if not segment:
            continue

        explicit_pairs = re.findall(r"\b([A-Z]{2,3})\b\s*(?:years?\s*>=\s*)?(\d{4})\+?", segment)
        if explicit_pairs and " from " not in segment.lower():
            for raw_country, raw_year in explicit_pairs:
                country = normalise_country_code(raw_country)
                if country:
                    apply_assignment({country}, int(raw_year))

        m = re.search(r"^(.*?)\s+years?\s*>=\s*(\d{4})", segment, flags=re.I)
        if m:
            targets = _expand_constructed_country_targets(m.group(1), sample_countries)
            apply_assignment(targets, int(m.group(2)))
            continue

        m = re.search(
            r"^(.*?)\s+from\s+(\d{4}(?:[-/]?Q?\d+)?)(?:\s+(?:through|to)\s+(\d{4}(?:[-/]?Q?\d+)?))?",
            segment,
            flags=re.I,
        )
        if m:
            targets = _expand_constructed_country_targets(m.group(1), sample_countries)
            start_end = _extract_year_window(" ".join(x for x in m.groups()[1:] if x))
            if start_end is not None:
                apply_assignment(targets, start_end[0], start_end[1] if len(start_end) > 1 else None)
                continue

        if " for " in seg.lower():
            tail = re.split(r"\bfor\b", seg, maxsplit=1, flags=re.I)[1]
            targets = _expand_constructed_country_targets(tail, sample_countries)
            if targets:
                apply_assignment(targets)
                continue

        targets = _expand_constructed_country_targets(segment, sample_countries)
        if targets:
            apply_assignment(targets)

    if not applied:
        return None
    return out[["country_iso3", "year", name]], "constructed"


def construct_variable_from_notes(
    spec: dict,
    item: dict,
    *,
    existing_frames: list[pd.DataFrame] | None = None,
    panel: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, str] | None:
    """Try to synthesize a simple indicator from a variable note."""
    notes = (item.get("notes") or "").strip()
    if not notes:
        return None
    pseudo = dict(item)
    pseudo["source"] = f"constructed: {notes}"
    return construct_variable_from_text(
        spec,
        pseudo,
        existing_frames=existing_frames,
        panel=panel,
    )


def construct_treatment_from_text(spec: dict,
                                  panel: pd.DataFrame) -> tuple[pd.DataFrame, str] | None:
    """Build a simple constructed treatment column directly onto an existing panel."""
    var_blocks = spec.get("variables") or {}
    treatment_items = var_blocks.get("treatment") or []
    if not treatment_items:
        return None
    for item in treatment_items:
        built = construct_variable_from_text(spec, item, panel=panel)
        if built is None:
            continue
        df, _ = built
        name = item.get("name") or "constructed_treatment"
        merged = panel.merge(df, on=["country_iso3", "year"], how="left")
        merged[name] = merged[name].fillna(0.0)
        return merged, name
    return None


def construct_treatment_from_estimator_notes(
    spec: dict,
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, str] | None:
    """Conservatively infer a simple treatment from estimator notes.

    Only fires when notes explicitly describe an indicator-like regressor,
    e.g. ``CRI-indicator interaction`` or ``post-2010 indicator``.
    """
    notes = str((spec.get("estimator") or {}).get("notes") or "").strip()
    if not notes:
        return None

    sample_countries = _sample_countries(spec)
    country: str | None = None

    iso_match = re.search(r"\b([A-Z]{3})[-\s]*(?:indicator|specific)\b", notes)
    if iso_match:
        maybe = normalise_country_code(iso_match.group(1))
        if maybe in sample_countries:
            country = maybe

    if country is None:
        lowered = notes.lower()
        for iso3 in sample_countries:
            for raw_name in sorted(_ISO3_TO_COUNTRY_NAMES.get(iso3, set()), key=len, reverse=True):
                name_key = raw_name.lower()
                if (
                    f"{name_key}-indicator" in lowered
                    or f"{name_key} indicator" in lowered
                    or f"{name_key}-specific" in lowered
                    or f"{name_key} specific" in lowered
                ):
                    country = iso3
                    break
            if country is not None:
                break

    post_year = None
    post_match = re.search(r"\bpost[-\s]*(19\d{2}|20\d{2})\b", notes, flags=re.I)
    if post_match:
        post_year = int(post_match.group(1))

    if country is None and post_year is None:
        return None

    source_parts = ["indicator = 1"]
    if country is not None:
        source_parts.append(f"for {country}")
    if post_year is not None:
        if country is not None:
            source_parts.append(f"from {post_year}")
        else:
            source_parts.append(f"for year >= {post_year}")
    pseudo = {
        "name": "context_inferred_treatment",
        "source": f"constructed: {' '.join(source_parts)}",
        "transformation": "indicator",
    }
    built = construct_variable_from_text(spec, pseudo, panel=panel)
    if built is None:
        return None
    df, _ = built
    merged = panel.merge(df, on=["country_iso3", "year"], how="left")
    merged[pseudo["name"]] = merged[pseudo["name"]].fillna(0.0)
    return merged, pseudo["name"]


def extract_qualifier_countries(qualifier: str | None) -> set[str]:
    out: set[str] = set()
    if not qualifier:
        return out
    for token in re.findall(r"\b[A-Z]{2,3}\b", qualifier.upper()):
        iso3 = _ISO2_TO_ISO3.get(token, token if len(token) == 3 else None)
        if iso3 and iso3 not in {"U2"}:
            out.add(iso3)
    return out


def apply_source_qualifier(
    panel: pd.DataFrame,
    qualifier: str | None,
    explicit_countries: set[str],
) -> pd.DataFrame:
    if not qualifier:
        return panel
    text = qualifier.lower()
    if "rest" in text and explicit_countries:
        return panel[~panel["country_iso3"].isin(explicit_countries)].copy()
    targets = extract_qualifier_countries(qualifier)
    if targets:
        matched = panel[panel["country_iso3"].isin(targets)].copy()
        if not matched.empty:
            return matched
    return panel


def transform(s: pd.Series, kind: str) -> pd.Series:
    kind = (kind or "level").lower()
    if kind in ("level", "raw"):
        return s
    if kind == "log":
        return np.log(s.where(s > 0))
    if kind in ("diff", "first_diff"):
        return s.diff()
    if kind in ("yoy", "log_diff"):
        return np.log(s.where(s > 0)).diff()
    return s


# ---------------------------------------------------------------------------
# Spec loading
# ---------------------------------------------------------------------------


def load_spec(hid: str) -> tuple[Path, dict] | None:
    for p in (ROOT / "hypotheses").glob(f"**/{hid}.yaml"):
        with p.open() as f:
            return p, yaml.safe_load(f)
    return None


_STUB_RULE_MARKER = "when this stub is promoted from draft"
_PREFLIGHT_INCONCLUSIVE_MARKERS = (
    "falsification rule not sharpened",
    "interaction term requested",
    "no outcome variable in spec",
    "no outcome variable",
    "no treatment variable",
    "no outcome or no treatment variable",
    "no outcome variable loaded",
    "no treatment variable loaded",
    "variables not loaded",
    "couldn't infer event_year",
    "couldn't infer pre/post cut year",
    "no countries in sample",
    "need >= 3 countries",
)


def has_dispositive_test_threshold(spec: dict) -> bool:
    """Conservatively detect when `falsification.test` is already specific.

    Many draft specs still carry the generic promotion boilerplate in
    `falsification.rule`, but the adjacent `falsification.test` already pins a
    usable decision threshold (for example `p<0.10`, `magnitude below 5%`,
    `top quartile`, or `no >10% deterioration`). Those should be gradable.
    """
    text = " ".join(
        str(part or "")
        for part in (
            (spec.get("falsification") or {}).get("test"),
            spec.get("methodology_note"),
        )
    ).lower()
    if not text.strip():
        return False

    significance_threshold = bool(
        re.search(r"\bp\s*(?:<|<=|≤)\s*0?\.\d+\b", text)
        or re.search(r"(?:alpha|α)\s*=?\s*0?\.\d+\b", text)
        or "conventional significance" in text
    )
    ranked_threshold = bool(
        re.search(r"\btop\s+(?:half|third|quartile|quintile|decile)\b", text)
        or re.search(r"\bbottom\s+(?:half|third|quartile|quintile|decile)\b", text)
    )
    magnitude_threshold = bool(
        re.search(r"\b(?:more|less)\s+than\s+\d+(?:\.\d+)?\s*(?:%|pp|x|fold|times)\b", text)
        or re.search(r"\b(?:at\s+least|below|above)\s+\d+(?:\.\d+)?\s*(?:%|pp|x|fold|times)\b", text)
        or re.search(r"\bno\s*[<>]=?\s*\d+(?:\.\d+)?\s*(?:%|pp|x|fold|times)?\b", text)
        or re.search(r"[<>]=?\s*\d+(?:\.\d+)?\s*(?:%|pp|bp|x|fold|times)\b", text)
        or re.search(r"±\s*\d+(?:\.\d+)?\s*(?:%|pp|bp|sd)\b", text)
        or re.search(r"\b\d+(?:\.\d+)?\s*(?:%|pp|bp|x|fold|times)\b", text)
        or re.search(r"\b\d+\s+of\s+\d+\b", text)
        or "magnitude below" in text
    )
    directional_anchor = bool(
        re.search(
            r"\b(?:positive|negative|higher|lower|increase|decrease|"
            r"opposite|matches|direction|rank|coefficient|gap|effect|"
            r"supports?|refute|refutes|worse|better|peak|baseline)\b",
            text,
        )
    )
    return significance_threshold or ranked_threshold or (
        magnitude_threshold and directional_anchor
    )


def is_stub_falsification_rule(spec: dict) -> bool:
    """True iff the spec's falsification.rule is still the generic stub-promotion
    boilerplate AND the methodology_note doesn't document the dispositive
    sharpening. Runners use this to refuse to grade — they emit
    `inconclusive — falsification rule not sharpened` instead, so auto-grader
    output never gets attached to a non-promoted spec.

    See post-mortem in commit bba6f644 for the failure mode this prevents.
    """
    rule = ((spec.get("falsification") or {}).get("rule") or "").lower()
    if _STUB_RULE_MARKER not in rule:
        return False
    mn = (spec.get("methodology_note") or "").lower()
    if any(k in mn for k in ("dispositive", "sharpened", "primary (dispositive")):
        return False
    if has_dispositive_test_threshold(spec):
        return False
    return True


def requests_interaction_without_constructed_term(spec: dict) -> bool:
    """Detect specs whose estimand is explicitly an interaction term that the
    generic panel runner cannot construct.

    The runner estimates the first loaded treatment/decomposition variable as a
    main effect. If the spec says the discriminating coefficient is an
    interaction but does not provide a loadable constructed interaction variable,
    grading the main effect would create a false verdict.
    """
    text = " ".join(
        str(part or "")
        for part in (
            spec.get("claim"),
            (spec.get("falsification") or {}).get("rule"),
            (spec.get("falsification") or {}).get("test"),
            (spec.get("estimator") or {}).get("notes"),
        )
    ).lower()
    asks_for_interaction = (
        "interaction" in text
        or "interacted" in text
        or re.search(r"\b[a-z0-9_]+(?:\s+(?:x|×)\s+|\s*\*\s*)[a-z0-9_]+\b", text) is not None
    )
    if not asks_for_interaction:
        return False

    var_blocks = spec.get("variables") or {}
    candidate_items = (
        (var_blocks.get("treatment") or [])
        + (var_blocks.get("decomposition_channels") or [])
    )
    for item in candidate_items:
        item_text = " ".join(
            str(item.get(k) or "")
            for k in ("name", "source", "transformation", "notes")
        ).lower()
        if (
            "interaction" in item_text
            or "interacted" in item_text
            or re.search(r"\b[a-z0-9_]+(?:\s+(?:x|×)\s+|\s*\*\s*)[a-z0-9_]+\b", item_text)
        ):
            return False
    return True


def should_persist_preflight_inconclusive(
    reason: str, persist_preflight_inconclusive: bool
) -> bool:
    """Persist preflight inconclusives only when explicitly requested.

    Bulk `--all` runs are much easier to work with when obvious missing-data
    or missing-spec-shape failures are reported to stdout but do not also
    flood `engine/runs/` with artifacts. Estimation-stage inconclusives still
    persist.
    """
    if persist_preflight_inconclusive:
        return True
    text = (reason or "").lower()
    return not any(marker in text for marker in _PREFLIGHT_INCONCLUSIVE_MARKERS)


def classify_bulk_run_message(message: str) -> str:
    """Classify a runner status line into a small set of bulk-run buckets."""
    text = (message or "").upper()
    if "SKIPPED (COMMITTED VERDICT ALREADY ON DISK)" in text:
        return "committed_skip"
    if "INCONCLUSIVE_DATA_PENDING" in text:
        if "[ARTIFACT SKIPPED]" in text:
            return "preflight_skip"
        return "inconclusive_persisted"
    for prefix in _REAL_VERDICT_PREFIXES:
        if f": {prefix}" in text:
            return prefix.lower().replace(" ", "_")
    if "SPEC NOT FOUND" in text:
        return "spec_not_found"
    return "other"


def bump_bulk_run_count(counts: dict, message: str) -> None:
    bucket = classify_bulk_run_message(message)
    counts[bucket] = counts.get(bucket, 0) + 1


def print_bulk_run_summary(label: str, counts: dict) -> None:
    real = sum(
        counts.get(bucket, 0)
        for bucket in (
            "supported",
            "refuted",
            "partial",
            "mixed",
            "weakly",
            "weakened",
            "not_supported",
            "blocked",
        )
    )
    print("")
    print(f"{label} summary:")
    print(f"  real verdicts:               {real}")
    print(f"  preflight inconclusive skip: {counts.get('preflight_skip', 0)}")
    print(f"  persisted inconclusive:      {counts.get('inconclusive_persisted', 0)}")
    print(f"  committed verdict skips:     {counts.get('committed_skip', 0)}")
    print(f"  crashes:                     {counts.get('crashed', 0)}")


def list_panel_fe_specs() -> list[str]:
    derived = ROOT / "engine" / "runnability.derived.yaml"
    with derived.open() as f:
        d = yaml.safe_load(f)
    return [
        h["hypothesis_id"]
        for h in d["hypotheses"]
        if h["estimator_template"] in ("panel_fe", "panel_fe_decomposition")
    ]


# ---------------------------------------------------------------------------
# Estimator
# ---------------------------------------------------------------------------


def build_panel(spec: dict) -> tuple[pd.DataFrame, dict]:
    """Build (country, year)-indexed panel from spec's variables.

    Returns (long_panel, status) where status records which variables loaded
    or failed.
    """
    status: dict = {"variables_loaded": [], "variables_missing": []}
    frames: list[pd.DataFrame] = []
    var_blocks = spec.get("variables") or {}
    sample_countries = _sample_countries(spec)
    for role in ("outcome", "treatment", "decomposition_channels", "controls"):
        items = var_blocks.get(role) or []
        for item in items:
            name = item.get("name")
            source = item.get("source", "")
            kind = item.get("transformation", "level")
            if not name or not source:
                continue
            res = None
            if source.lower().lstrip().startswith("constructed:"):
                res = construct_variable_from_text(spec, item, existing_frames=frames)
            if res is None:
                res = load_variable(source)
            if (
                res is None
                and (
                    role == "treatment"
                    or str(kind).lower() == "indicator"
                )
            ):
                res = construct_variable_from_notes(spec, item, existing_frames=frames)
            if res is None:
                status["variables_missing"].append(
                    {"role": role, "name": name, "source": source}
                )
                continue
            df, pub = res
            df = df.copy()
            value_col = "value" if "value" in df.columns else name if name in df.columns else None
            if value_col is None:
                status["variables_missing"].append(
                    {"role": role, "name": name, "source": source}
                )
                continue
            df[value_col] = transform(df[value_col], kind)
            if value_col != name:
                df.rename(columns={value_col: name}, inplace=True)
            if (
                role == "controls"
                and len(sample_countries) > 1
                and "country_iso3" in df.columns
                and df["country_iso3"].nunique(dropna=True) == 1
            ):
                common = df[["year", name]].dropna().drop_duplicates().copy()
                if not common.empty:
                    df = pd.MultiIndex.from_product(
                        [sample_countries, common["year"].tolist()],
                        names=["country_iso3", "year"],
                    ).to_frame(index=False).merge(common, on="year", how="left")
            df["_role"] = role
            frames.append(df[["country_iso3", "year", name]])
            status["variables_loaded"].append(
                {"role": role, "name": name, "source": source, "publisher": pub,
                 "n_rows": int(len(df))}
            )

    if not frames:
        return pd.DataFrame(), status

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country_iso3", "year"], how="outer")
    return panel, status


def filter_sample(panel: pd.DataFrame, spec: dict) -> pd.DataFrame:
    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    period = sample.get("period") or [None, None]
    out = panel.copy()
    if "country_iso3" not in out.columns or "year" not in out.columns:
        return out
    if countries:
        out = out[out["country_iso3"].isin(countries)]
    if period[0] is not None:
        out = out[out["year"] >= int(period[0])]
    if period[1] is not None:
        out = out[out["year"] <= int(period[1])]
    return out


def prune_controls_for_overlap(
    panel: pd.DataFrame,
    required: list[str],
    candidate_controls: list[str],
    *,
    min_obs: int,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Drop overlap-killing controls until the working sample is usable.

    This keeps the runner from failing just because one optional control loaded as
    an all-null or off-sample column while the core outcome/treatment data is fine.
    """
    controls = [c for c in candidate_controls if c in panel.columns and c not in required]
    dropped: list[str] = []

    def current_sample(cols: list[str]) -> pd.DataFrame:
        keep = ["country_iso3", "year"] + required + cols
        return panel[keep].dropna()

    sub = current_sample(controls)
    while len(sub) < min_obs and controls:
        best_control = None
        best_n = len(sub)
        for control in controls:
            alt_controls = [c for c in controls if c != control]
            alt_n = len(current_sample(alt_controls))
            if alt_n > best_n:
                best_control = control
                best_n = alt_n
        if best_control is None:
            break
        controls.remove(best_control)
        dropped.append(best_control)
        sub = current_sample(controls)
    return sub, controls, dropped


def fit_fe_ols_fallback(
    sub: pd.DataFrame,
    outcome_name: str,
    rhs: list[str],
    treatment_name: str,
    *,
    entity: bool,
    time: bool,
    cluster_spec: str,
    method_label: str = "statsmodels OLS FE fallback",
) -> dict:
    """Two-way fixed-effects fallback using dummy-expanded statsmodels OLS."""
    try:
        import statsmodels.api as sm
    except Exception as exc:
        return {"error": f"statsmodels fallback unavailable: {exc}"}

    model_df = sub[["country_iso3", "year", outcome_name] + rhs].copy()
    X = model_df[rhs].astype(float).reset_index(drop=True)
    if entity:
        X = pd.concat(
            [
                X,
                pd.get_dummies(
                    model_df["country_iso3"], prefix="cty", drop_first=True, dtype=float
                ).reset_index(drop=True),
            ],
            axis=1,
        )
    if time:
        X = pd.concat(
            [
                X,
                pd.get_dummies(
                    model_df["year"].astype(int).astype(str),
                    prefix="yr",
                    drop_first=True,
                    dtype=float,
                ).reset_index(drop=True),
            ],
            axis=1,
        )
    X = sm.add_constant(X, has_constant="add")
    y = model_df[outcome_name].astype(float).reset_index(drop=True)
    try:
        model = sm.OLS(y, X)
        cluster_text = (cluster_spec or "").lower()
        if "country" in cluster_text:
            if model_df["country_iso3"].nunique() < 2:
                res = model.fit(cov_type="HC1")
            else:
                res = model.fit(
                    cov_type="cluster",
                    cov_kwds={"groups": model_df["country_iso3"].reset_index(drop=True)},
                )
        elif "year" in cluster_text:
            if model_df["year"].nunique() < 2:
                res = model.fit(cov_type="HC1")
            else:
                res = model.fit(
                    cov_type="cluster",
                    cov_kwds={"groups": model_df["year"].reset_index(drop=True)},
                )
        else:
            res = model.fit(cov_type="HC1")
    except Exception as exc:
        return {"error": f"statsmodels fallback failed: {exc}"}

    if treatment_name not in res.params.index:
        return {"error": f"treatment {treatment_name!r} absorbed in fallback FE regression"}
    return {
        "coefficient": float(res.params[treatment_name]),
        "std_error": float(res.bse[treatment_name]),
        "p_value": float(res.pvalues[treatment_name]),
        "n_obs": int(len(model_df)),
        "n_countries": int(model_df["country_iso3"].nunique()),
        "r_squared_within": float(getattr(res, "rsquared", 0.0) or 0.0),
        "fe_entity": entity,
        "fe_time": time,
        "cluster": cluster_spec,
        "method": method_label,
    }


def run_panel_ols(
    panel: pd.DataFrame,
    spec: dict,
    outcome_name: str,
    treatment_name: str,
    *,
    extra_regressors: list[str] | None = None,
) -> dict:
    """Fit a panel regression of outcome on treatment (+ controls) with FE.

    Falls back to dummy-encoded OLS if linearmodels isn't available.
    """
    var_blocks = spec.get("variables") or {}
    control_names = [c["name"] for c in (var_blocks.get("controls") or []) if c.get("name")]
    extra_regressors = [r for r in (extra_regressors or []) if r]
    fe_spec = (spec.get("estimator") or {}).get("fixed_effects", []) or []
    cluster_spec = (spec.get("estimator") or {}).get("clustering", "country")

    # Drop rows missing outcome/treatment, and stop a single all-null control
    # from collapsing the entire runnable sample.
    sub, usable_controls, dropped_controls = prune_controls_for_overlap(
        panel,
        [outcome_name, treatment_name],
        [
            c
            for c in (control_names + extra_regressors)
            if c in panel.columns and c != treatment_name
        ],
        min_obs=30,
    )
    if sub.empty or len(sub) < 30:
        return {"error": f"insufficient observations after listwise deletion ({len(sub)})"}
    rhs = [treatment_name] + usable_controls
    sub_plain = sub.copy()
    entity = "country" in [str(x).lower() for x in fe_spec]
    time = "year" in [str(x).lower() for x in fe_spec]
    if not entity and not time:
        entity, time = True, True

    try:
        from linearmodels.panel import PanelOLS

        sub = sub.set_index(["country_iso3", "year"])
        exog = sub[rhs]
        endog = sub[outcome_name]
        mod = PanelOLS(endog, exog, entity_effects=entity, time_effects=time,
                       drop_absorbed=True)
        cluster_kw = {}
        if "country" in cluster_spec.lower():
            cluster_kw = {"cov_type": "clustered", "cluster_entity": True}
        elif "year" in cluster_spec.lower():
            cluster_kw = {"cov_type": "clustered", "cluster_time": True}
        else:
            cluster_kw = {"cov_type": "robust"}
        res = mod.fit(**cluster_kw)
        coef = float(res.params[treatment_name])
        se = float(res.std_errors[treatment_name])
        pval = float(res.pvalues[treatment_name])
        nobs = int(res.nobs)
        return {
            "coefficient": coef,
            "std_error": se,
            "p_value": pval,
            "n_obs": nobs,
            "n_countries": int(sub.index.get_level_values(0).nunique()),
            "r_squared_within": float(res.rsquared_within or 0),
            "fe_entity": entity,
            "fe_time": time,
            "cluster": cluster_spec,
            "method": "linearmodels.PanelOLS",
            "dropped_controls_due_to_overlap": dropped_controls,
        }
    except Exception as exc:
        fallback = fit_fe_ols_fallback(
            sub_plain,
            outcome_name,
            rhs,
            treatment_name,
            entity=entity,
            time=time,
            cluster_spec=cluster_spec,
            method_label=f"statsmodels OLS FE fallback (linearmodels failed: {exc})",
        )
        if "error" not in fallback:
            fallback["dropped_controls_due_to_overlap"] = dropped_controls
        return fallback


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

# Verb-based claim-direction lexicon. Tuned for first-sentence parsing of
# typical IESET claims ("X increased Y", "X reduced Y", etc). Words appear
# all over the disclosure/notes/falsification text, which is why the previous
# whole-text counter produced spurious "ambiguous" verdicts. We restrict to
# the FIRST SENTENCE of `claim` and look only for predicate verbs.
_PLUS_VERBS = {
    "increased", "increases", "increase", "raised", "raises", "raise",
    "rose", "rises", "rise", "boosted", "boosts", "boost",
    "expanded", "expands", "expand", "accelerated", "accelerates",
    "acceleration", "growth",
    "improved", "improves", "improve", "elevated", "elevates",
    "higher", "more", "exceeds", "exceeded",
    "lifts", "lifted", "grew", "grows",
    "outpaced", "outperformed", "outperforms",
    "larger", "stronger", "greater",
    "predict", "predicts", "predicted",  # cross-sectional claims
}
_MINUS_VERBS = {
    "decreased", "decreases", "decrease", "reduced", "reduces", "reduce",
    "declined", "declines", "decline", "lowered", "lowers", "lower",
    "fell", "falls", "fall", "shrank", "shrinks", "shrink",
    "weakened", "weakens", "weaken", "compressed", "compresses",
    "less", "fewer", "below",
    "worsened", "worsens", "worsen", "deteriorated", "deteriorates",
    "underperformed", "underperforms",
    "depressed", "depresses",
    "smaller", "weaker", "lower", "stagnated", "stagnates",
    "collapsed", "collapses", "collapse",
}

# Hypothesis-ID suffix shortcuts — many specs encode direction in the slug.
_ID_SUFFIX_DIR = {
    "growth_acceleration": "+", "growth_collapse": "-",
    "expansion": "+", "decline": "-", "contraction": "-",
    "improvement": "+", "deterioration": "-",
    "rise": "+", "fall": "-",
    "outperforms": "+", "underperforms": "-",
    "above": "+", "below": "-",
}


def infer_claim_direction(spec: dict) -> str:
    """Return '+' / '-' / '?' for the first-sentence prediction direction.

    Strategy:
      1. Read explicit `claim_direction` field if present (preferred).
      2. Else: look at FIRST sentence of `claim` only (typically the
         testable prediction). Count predicate verbs from the +/- lexicons.
      3. Falsification.test as tiebreaker.
    """
    explicit = spec.get("claim_direction")
    if explicit in ("+", "-", "?"):
        return explicit
    if explicit in ("plus", "positive", "increase", "supported"):
        return "+"
    if explicit in ("minus", "negative", "decrease", "refuted"):
        return "-"

    threshold = (spec.get("falsification") or {}).get("threshold")
    if isinstance(threshold, dict):
        expected_sign = threshold.get("expected_sign")
        if expected_sign in ("+", "-", "?"):
            return expected_sign
        if expected_sign in ("plus", "positive", "increase", "supported"):
            return "+"
        if expected_sign in ("minus", "negative", "decrease", "refuted"):
            return "-"

    import re as _re

    # 1. Slug-suffix shortcut. Many hypothesis_ids encode direction.
    hid = (spec.get("hypothesis_id") or "").lower()
    for suffix, d in _ID_SUFFIX_DIR.items():
        if suffix in hid:
            return d

    claim = (spec.get("claim") or "").strip()
    if not claim:
        return "?"
    # 2. First sentence of `claim`
    first = _re.split(r"(?<=[.!?])\s+", claim, maxsplit=1)[0].lower()
    plus = sum(1 for v in _PLUS_VERBS if _re.search(rf"\b{v}\b", first))
    minus = sum(1 for v in _MINUS_VERBS if _re.search(rf"\b{v}\b", first))
    if plus > minus:
        return "+"
    if minus > plus:
        return "-"
    # 3. Falsification.test as tiebreaker
    test = ((spec.get("falsification") or {}).get("test") or "").lower()
    if test:
        plus_t = sum(1 for v in _PLUS_VERBS if _re.search(rf"\b{v}\b", test))
        minus_t = sum(1 for v in _MINUS_VERBS if _re.search(rf"\b{v}\b", test))
        if plus_t > minus_t: return "+"
        if minus_t > plus_t: return "-"
    return "?"


def verdict_from_estimate(est: dict, claim_dir: str) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]
    coef = est["coefficient"]
    pval = est["p_value"]
    sign = "+" if coef >= 0 else "-"
    alpha = 0.10
    if pval < alpha:
        if claim_dir == "?":
            return ("PARTIAL",
                    f"coef={coef:+.4g}, p={pval:.3g}; claim direction not auto-inferred")
        if sign == claim_dir:
            return ("SUPPORTED",
                    f"coef={coef:+.4g} (sign matches claim {claim_dir}), p={pval:.3g}")
        return ("REFUTED",
                f"coef={coef:+.4g} (sign opposite claim {claim_dir}), p={pval:.3g}")
    return ("PARTIAL",
            f"coef={coef:+.4g}, p={pval:.3g} (above α=0.10); direction inconclusive")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_outputs(hid: str, spec: dict, status: dict, est: dict,
                  verdict: str, reason: str) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)

    diag = {
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": (spec.get("estimator") or {}).get("template"),
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": est,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_panel_fe.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))

    md = [
        f"# Result card — {hid}",
        "",
        f"**Verdict:** {verdict} — {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test','').strip()}",
        "",
        "## Estimate",
    ]
    if "error" in est:
        md.append(f"- _Error:_ {est['error']}")
    else:
        md.extend([
            f"- Method: {est.get('method')}",
            f"- Coefficient (treatment): **{est['coefficient']:+.4g}**",
            f"- Std error: {est['std_error']:.4g}",
            f"- p-value: **{est['p_value']:.3g}**",
            f"- Observations: {est['n_obs']}, countries: {est['n_countries']}",
            f"- Within R²: {est['r_squared_within']:.3g}",
            f"- Fixed effects: entity={est['fe_entity']}, time={est['fe_time']}",
            f"- Clustering: {est['cluster']}",
        ])
    md.append("")
    md.append("## Variables resolved")
    if status["variables_loaded"]:
        for v in status["variables_loaded"]:
            md.append(f"- `{v['source']}` → {v['name']} ({v['role']}, "
                      f"publisher={v['publisher']}, n={v['n_rows']})")
    if status["variables_missing"]:
        md.append("\n### Variables missing data")
        for v in status["variables_missing"]:
            md.append(f"- `{v['source']}` ({v['role']}, name={v['name']}) — vintage not on disk")

    md.append("")
    md.append(f"_Generated by `scripts/run_panel_fe.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


_REAL_VERDICT_PREFIXES = (
    "SUPPORTED", "REFUTED", "PARTIAL", "MIXED", "WEAKLY",
    "WEAKENED", "NOT SUPPORTED", "NOT_SUPPORTED", "BLOCKED",
)


def has_committed_verdict(hid: str) -> bool:
    """True if engine/runs/<hid>/diagnostics.json exists with a real prior
    verdict (not INCONCLUSIVE). Used to prevent generic-runner output from
    clobbering bespoke prior run artifacts.

    Reads BOTH `verdict_label` (new schema) and `verdict` (legacy free-text,
    case-insensitive) so handcrafted artifacts like 'refuted — gap +0.74...'
    are properly protected.
    """
    diag = RUNS / hid / "diagnostics.json"
    if not diag.exists():
        return False
    try:
        import json as _json
        d = _json.loads(diag.read_text())
    except Exception:
        return False
    label = (d.get("verdict_label") or "").upper()
    free_text = (d.get("verdict") or "").upper().lstrip()
    is_inconclusive = (
        label == "INCONCLUSIVE_DATA_PENDING"
        or free_text.startswith("INCONCLUSIVE")
    )
    if is_inconclusive:
        return False  # OK to overwrite — was waiting on data, may have it now
    is_real = (
        label in _REAL_VERDICT_PREFIXES
        or any(free_text.startswith(p) for p in _REAL_VERDICT_PREFIXES)
    )
    if is_real:
        # Real verdict — protect from overwrite regardless of git-tracking
        # status (uncommitted handcrafted artifacts also worth preserving).
        return True
    if label or free_text:
        # Some other verdict label we don't recognise — be conservative,
        # check git-tracked status as a tiebreaker.
        import subprocess
        try:
            r = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(diag.relative_to(ROOT))],
                cwd=str(ROOT), capture_output=True, text=True, timeout=5,
            )
            return r.returncode == 0
        except Exception:
            return True  # Conservative: assume committed
    return False


def run_one(
    hid: str,
    verbose: bool = True,
    force: bool = False,
    persist_preflight_inconclusive: bool = True,
) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if found is None:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    # Integrity gate: refuse to grade against a stub falsification rule.
    # The auto-grader's verdicts are only meaningful against a dispositive
    # pre-registered threshold; running against the generic boilerplate
    # ("…when this stub is promoted from draft") would attach a fake-clean
    # verdict to a non-promoted spec. See post-mortem (commit bba6f644).
    if is_stub_falsification_rule(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "falsification rule not sharpened — auto-grader refuses to "
            "grade against the generic stub boilerplate. Promote the spec "
            "(replace falsification.rule with a dispositive threshold AND "
            "document the sharpening in methodology_note) before running."
        )
        persisted = should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        )
        if persisted:
            write_outputs(
                hid,
                spec,
                {"variables_loaded": [], "variables_missing": []},
                {"error": reason},
                verdict,
                reason,
            )
        suffix = " (stub rule, refused to grade)"
        if not persisted:
            suffix += " [artifact skipped]"
        return f"  ⚠ {hid}: {verdict}{suffix}"

    if requests_interaction_without_constructed_term(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "interaction term requested but no loadable constructed "
            "interaction variable is defined. The generic panel_fe runner "
            "would otherwise grade a main-effect coefficient instead of the "
            "pre-registered interaction estimand. Add a treatment or "
            "decomposition variable with transformation/source/name marking "
            "the interaction, or use a bespoke replication script."
        )
        write_outputs(
            hid,
            spec,
            {"variables_loaded": [], "variables_missing": []},
            {"error": reason},
            verdict,
            reason,
        )
        return f"  ⚠ {hid}: {verdict} — interaction term not constructible"

    panel, status = build_panel(spec)

    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    treatment_items = var_blocks.get("treatment") or []
    decomposition_items = var_blocks.get("decomposition_channels") or []
    template = (spec.get("estimator") or {}).get("template")
    decomposition_mode = template == "panel_fe_decomposition"
    if not outcome_items:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = "no outcome or no treatment variable in spec"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ⚠ {hid}: {verdict} — {reason}"

    panel_filt = filter_sample(panel, spec)
    outcome_name = first_loaded_var(outcome_items, panel_filt)
    if decomposition_mode:
        treatment_name = first_loaded_var(decomposition_items, panel_filt)
        extra_regressors = [
            item.get("name")
            for item in decomposition_items
            if item.get("name") and item.get("name") != treatment_name
        ]
    else:
        treatment_name = first_loaded_var(treatment_items, panel_filt)
        extra_regressors = []
    if outcome_name is None:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        missing = [v["source"] for v in status["variables_missing"]
                   if v["role"] == "outcome"]
        reason = f"no outcome variable loaded; missing: {missing}"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"
    if treatment_name is None and not decomposition_mode:
        built = construct_treatment_from_text(spec, panel_filt)
        if built is not None:
            panel_filt, treatment_name = built
        elif not treatment_items:
            built = construct_treatment_from_estimator_notes(spec, panel_filt)
            if built is not None:
                panel_filt, treatment_name = built
    if treatment_name is None:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        if decomposition_mode:
            missing = [
                v["source"]
                for v in status["variables_missing"]
                if v["role"] == "decomposition_channels"
            ]
            reason = f"no decomposition channel loaded; missing: {missing}"
        elif not treatment_items:
            reason = "no outcome or no treatment variable in spec"
        else:
            missing = [v["source"] for v in status["variables_missing"]
                       if v["role"] == "treatment"]
            reason = f"no treatment variable loaded; missing: {missing}"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"
    est = run_panel_ols(
        panel_filt,
        spec,
        outcome_name,
        treatment_name,
        extra_regressors=extra_regressors,
    )
    claim_dir = infer_claim_direction(spec)
    verdict, reason = verdict_from_estimate(est, claim_dir)
    write_outputs(hid, spec, status, est, verdict, reason)

    icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
            "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
    return f"  {icon} {hid}: {verdict} — {reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?")
    parser.add_argument("--all", action="store_true",
                        help="Run every panel_fe / panel_fe_decomposition spec.")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing committed verdicts (default skips).")
    parser.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts during bulk runs.",
    )
    args = parser.parse_args()
    persist_preflight = args.write_preflight_inconclusive or not args.all

    if args.all:
        ids = list_panel_fe_specs()
        counts: dict[str, int] = {}
        print(f"Running {len(ids)} panel_fe specs…")
        for hid in ids:
            try:
                msg = (
                    run_one(
                        hid,
                        force=args.force,
                        persist_preflight_inconclusive=persist_preflight,
                    )
                )
                print(msg)
                bump_bulk_run_count(counts, msg)
            except Exception as exc:
                print(f"  ✗ {hid}: runner crashed — {exc}")
                counts["crashed"] = counts.get("crashed", 0) + 1
                traceback.print_exc()
        print_bulk_run_summary("panel_fe", counts)
        return 0
    if not args.hypothesis_id:
        parser.error("Pass <hypothesis_id> or --all.")
    print(
        run_one(
            args.hypothesis_id,
            force=args.force,
            persist_preflight_inconclusive=persist_preflight,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
