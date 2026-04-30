"""BAK Economics + KOF Swiss Economic Institute fetcher.

Source URLs (browser):
    BAK Economics  — https://www.bak-economics.com/en/
    KOF (ETH Zurich) — https://kof.ethz.ch/en/forecasts-and-indicators/indicators.html
    KOF Globalisation Index — https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-globalisation-index.html

Reality check:
  - BAK Economics is a paid-research firm. Headline cantonal indicators
    (per-capita GDP, employment shares by industry) are published as PDF /
    XLSX previews behind their press / media-room flow. There is no public
    JSON or stable CSV endpoint we can hit, so cantonal BAK series are
    handled as **manual drops** under data/manual/bak_swiss/<series_id>/.
  - KOF publishes the Globalisation Index (KOFGI) and several cantonal
    indices (regulation index, business-cycle barometer) as free downloads.
    The KOFGI ships as a stable XLSX at the indicator landing page; the
    cantonal regulation index is a PDF release with companion XLSX. We
    therefore treat KOF series as manual drops too — the file is free, the
    URL is stable enough that automated fetch would work, but the rotating
    publication cadence + light Cloudflare gating on kof.ethz.ch make a
    manual-drop pattern simpler and consistent with Fraser EFW / IEA style.
  - Swiss FSO (publisher key 'swiss_fso') already covers underlying canton
    demographics + GDP via its own manual-drop pipeline; cross-reference
    there if the BAK files are unavailable for a given vintage.

Canonical series for IESET:
    kof_globalisation_index_economic_de_facto  — country-year economic
                                                 globalisation (KOFGI, de facto)
    kof_globalisation_index_economic_de_jure   — country-year economic
                                                 globalisation (KOFGI, de jure)
    bak_canton_gdp_per_capita_chf              — canton x year GDP per capita
                                                 (CHF, current prices)
    bak_canton_employment_share_industry       — canton x industry x year
                                                 employment share (% of total)
    kof_swiss_regulation_index_canton          — canton x year KOF regulation
                                                 intensity index

Output schema (where applicable):
    country_iso3='CHE', region_code (canton ISO-3166-2 code, e.g. 'CH-ZH'),
    year, value. Country-level KOFGI series carry country_iso3 only and
    leave region_code null.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import MANUAL_ROOT, ManualDropError

LICENSE = "unknown"  # KOF: open / Swiss-gov terms; BAK: paid-research preview.

SUPPORTED: dict[str, dict[str, Any]] = {
    "kof_globalisation_index_economic_de_facto": {
        "title": "KOF Globalisation Index — Economic globalisation (de facto)",
        "frequency": "annual",
        "currency": None,
        "units": "Index 1-100 (higher = more economically globalised, de facto flows)",
        "source_url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-globalisation-index.html",
        "methodology_url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-globalisation-index.html",
        "scope": "country-year",
    },
    "kof_globalisation_index_economic_de_jure": {
        "title": "KOF Globalisation Index — Economic globalisation (de jure)",
        "frequency": "annual",
        "currency": None,
        "units": "Index 1-100 (higher = more economically globalised, de jure rules)",
        "source_url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-globalisation-index.html",
        "methodology_url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators/kof-globalisation-index.html",
        "scope": "country-year",
    },
    "bak_canton_gdp_per_capita_chf": {
        "title": "BAK Economics — Cantonal GDP per capita (CHF, current prices)",
        "frequency": "annual",
        "currency": "CHF",
        "units": "CHF per capita (canton-year, current prices)",
        "source_url": "https://www.bak-economics.com/en/economic-forecasts/regional-forecasts",
        "methodology_url": "https://www.bak-economics.com/en/methods",
        "scope": "canton-year",
    },
    "bak_canton_employment_share_industry": {
        "title": "BAK Economics — Cantonal employment share by industry",
        "frequency": "annual",
        "currency": None,
        "units": "Share of cantonal employment by NOGA-industry (% of total)",
        "source_url": "https://www.bak-economics.com/en/economic-forecasts/regional-forecasts",
        "methodology_url": "https://www.bak-economics.com/en/methods",
        "scope": "canton-industry-year",
    },
    "kof_swiss_regulation_index_canton": {
        "title": "KOF Swiss Economic Institute — Regulation index by canton",
        "frequency": "annual",
        "currency": None,
        "units": "Index (higher = more regulatory intensity), canton-year",
        "source_url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators.html",
        "methodology_url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators.html",
        "scope": "canton-year",
    },
}

# Canton-name to ISO-3166-2:CH region code map (used when files ship with
# canton names rather than codes). Covers all 26 cantons in DE/FR/EN/IT.
CANTON_TO_ISO: dict[str, str] = {
    # ZH
    "zurich": "CH-ZH", "zürich": "CH-ZH", "zh": "CH-ZH",
    # BE
    "bern": "CH-BE", "berne": "CH-BE", "be": "CH-BE",
    # LU
    "lucerne": "CH-LU", "luzern": "CH-LU", "lu": "CH-LU",
    # UR
    "uri": "CH-UR", "ur": "CH-UR",
    # SZ
    "schwyz": "CH-SZ", "sz": "CH-SZ",
    # OW
    "obwalden": "CH-OW", "obwald": "CH-OW", "ow": "CH-OW",
    # NW
    "nidwalden": "CH-NW", "nidwald": "CH-NW", "nw": "CH-NW",
    # GL
    "glarus": "CH-GL", "glaris": "CH-GL", "gl": "CH-GL",
    # ZG
    "zug": "CH-ZG", "zoug": "CH-ZG", "zg": "CH-ZG",
    # FR
    "fribourg": "CH-FR", "freiburg": "CH-FR", "fr": "CH-FR",
    # SO
    "solothurn": "CH-SO", "soleure": "CH-SO", "so": "CH-SO",
    # BS
    "basel-stadt": "CH-BS", "basel stadt": "CH-BS", "basel-city": "CH-BS",
    "bale-ville": "CH-BS", "bâle-ville": "CH-BS", "bs": "CH-BS",
    # BL
    "basel-landschaft": "CH-BL", "basel-land": "CH-BL", "basel land": "CH-BL",
    "bale-campagne": "CH-BL", "bâle-campagne": "CH-BL", "bl": "CH-BL",
    # SH
    "schaffhausen": "CH-SH", "schaffhouse": "CH-SH", "sh": "CH-SH",
    # AR
    "appenzell ausserrhoden": "CH-AR", "appenzell a.rh.": "CH-AR",
    "appenzell ar": "CH-AR", "ar": "CH-AR",
    # AI
    "appenzell innerrhoden": "CH-AI", "appenzell i.rh.": "CH-AI",
    "appenzell ai": "CH-AI", "ai": "CH-AI",
    # SG
    "st. gallen": "CH-SG", "st gallen": "CH-SG", "saint-gall": "CH-SG",
    "st.gallen": "CH-SG", "sg": "CH-SG",
    # GR
    "graubunden": "CH-GR", "graubünden": "CH-GR", "grisons": "CH-GR",
    "grigioni": "CH-GR", "gr": "CH-GR",
    # AG
    "aargau": "CH-AG", "argovie": "CH-AG", "ag": "CH-AG",
    # TG
    "thurgau": "CH-TG", "thurgovie": "CH-TG", "tg": "CH-TG",
    # TI
    "ticino": "CH-TI", "tessin": "CH-TI", "ti": "CH-TI",
    # VD
    "vaud": "CH-VD", "vd": "CH-VD",
    # VS
    "valais": "CH-VS", "wallis": "CH-VS", "vs": "CH-VS",
    # NE
    "neuchatel": "CH-NE", "neuchâtel": "CH-NE", "neuenburg": "CH-NE", "ne": "CH-NE",
    # GE
    "geneva": "CH-GE", "genève": "CH-GE", "geneve": "CH-GE", "genf": "CH-GE", "ge": "CH-GE",
    # JU
    "jura": "CH-JU", "ju": "CH-JU",
}


class BAKSwissError(RuntimeError):
    pass


def _find_manual_for_series(series_id: str) -> Path:
    """Locate the latest manual-drop file for a given BAK/KOF series.

    Convention: data/manual/bak_swiss/<series_id>/<file>.{csv,xlsx,xls}.
    Falls back to data/manual/bak_swiss/ root if the per-series subdir is
    empty (file stem must contain series_id) — keeps single-drop bootstrap
    cheap.
    """
    accepted = (".csv", ".xlsx", ".xls")
    series_dir = MANUAL_ROOT / "bak_swiss" / series_id
    candidates: list[Path] = []
    if series_dir.exists():
        candidates = [
            p for p in series_dir.iterdir()
            if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in accepted
        ]
    if not candidates:
        root_dir = MANUAL_ROOT / "bak_swiss"
        if root_dir.exists():
            candidates = [
                p for p in root_dir.iterdir()
                if p.is_file()
                and not p.name.startswith(".")
                and p.suffix.lower() in accepted
                and series_id.lower() in p.stem.lower()
            ]
    if not candidates:
        raise ManualDropError(
            f"No BAK/KOF manual-drop file for series '{series_id}'. "
            f"Drop a .csv/.xlsx into data/manual/bak_swiss/{series_id}/ "
            f"(or name a file in data/manual/bak_swiss/ to include "
            f"'{series_id}' in its stem). Sources: KOF — "
            f"https://kof.ethz.ch/en/forecasts-and-indicators/indicators.html ; "
            f"BAK — https://www.bak-economics.com/en/."
        )
    return max(candidates, key=lambda p: (p.name, p.stat().st_mtime))


def _read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        # KOF / BAK workbooks ship a 'Notes' / 'Cover' sheet first; pick the
        # widest-by-row sheet as a robust default.
        best_name = max(
            xls.sheet_names,
            key=lambda s: len(xls.parse(s, nrows=0).columns),
        )
        df = xls.parse(best_name)
    else:
        df = pd.read_csv(path)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    return df


def _normalise_canton_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'region_code' column (CH-XX ISO-3166-2) when a canton column is
    detectable. Idempotent if region_code already populated."""
    if "region_code" in df.columns:
        return df
    candidate_cols = [
        c for c in df.columns
        if str(c).strip().lower() in {
            "canton", "kanton", "canton_name", "kanton_name",
            "region", "region_name", "geo", "name",
        }
    ]
    if not candidate_cols:
        return df
    src = candidate_cols[0]
    df = df.copy()
    df["region_code"] = (
        df[src]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(CANTON_TO_ISO)
        .astype("string")
    )
    return df


def fetch(
    series_id: str = "kof_globalisation_index_economic_de_facto",
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch a BAK / KOF series from data/manual/bak_swiss/<series_id>/.

    series_id: a key in SUPPORTED (the five canonical Swiss-cantonal series).
               Unknown ids are accepted as free-form aliases and matched
               against filenames in data/manual/bak_swiss/.
    """
    fetch_ts = utc_now()
    meta = SUPPORTED.get(series_id, {})
    path = _find_manual_for_series(series_id)
    df = _read_any(path)
    if df.empty:
        raise BAKSwissError(f"BAK/KOF manual file {path.name} parsed to 0 rows")

    # Inject country_iso3='CHE' for the cantonal series (and KOFGI Swiss
    # vintages that ship without an explicit country column).
    scope = meta.get("scope", "")
    if "country_iso3" not in df.columns and ("canton" in scope or scope == "country-year"):
        df = df.copy()
        df["country_iso3"] = "CHE"

    if "canton" in scope:
        df = _normalise_canton_column(df)

    out, sha = write_vintage(
        publisher="bak_swiss",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    # Best-effort year coverage extraction.
    start = end = None
    year_col = next(
        (c for c in df.columns if str(c).strip().lower() in {"year", "jahr", "annee", "anno"}),
        None,
    )
    if year_col:
        years = pd.to_numeric(df[year_col], errors="coerce").dropna()
        if not years.empty:
            start = str(int(years.min()))
            end = str(int(years.max()))

    return FetchResult(
        publisher="bak_swiss",
        series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url=meta.get(
            "methodology_url",
            "https://kof.ethz.ch/en/forecasts-and-indicators/indicators.html",
        ),
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta.get("frequency", "annual"),
        units=meta.get("units", "per BAK/KOF publication metadata"),
        currency=meta.get("currency"),
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=out,
        extra={
            "manual_file": path.name,
            "n_columns": len(df.columns),
            "title": meta.get("title", ""),
            "scope": scope,
            "publisher_source_url": meta.get(
                "source_url",
                "https://kof.ethz.ch/en/forecasts-and-indicators/indicators.html",
            ),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
