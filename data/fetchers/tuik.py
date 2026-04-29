"""TÜİK (Türkiye İstatistik Kurumu / Turkish Statistical Institute) fetcher.

Portal:    https://data.tuik.gov.tr/
Indicator
endpoint:  https://biruni.tuik.gov.tr/medas/?kn=<key>   (returns Excel)
Bulletin
endpoint:  https://data.tuik.gov.tr/Bulten/DownloadIstatistikselTablo?p=<id>
Auth:      none. License: Turkish open-data clause (treated as 'unknown').

Strategy
--------
TÜİK is API-finicky in much the same way TCMB EVDS is: the public portal serves
session-cookie-gated Excel/CSV downloads from biruni.tuik.gov.tr and rotates
the indicator keys (`kn=`) and bulletin ids (`p=`) without notice. We attempt
a direct HTTP GET against the configured URL with a browser-style UA + Origin
header; if that fails (404 / 403 / non-binary body), we fall back to a
manual-drop file under data/manual/tuik/.

Methodology note (also mirrored in publishers.yaml): the 2021-2023 TÜİK CPI
methodology has been disputed; analyses sensitive to that vintage should
cross-check against the ENAGrup independent index.

SUPPORTED catalogues four cited series concepts. Series IDs are short logical
aliases; the registry stores the live URL, the document-style fallback name
the manual-drop loader will look for, plus units / frequency metadata.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import MANUAL_ROOT, ManualDropError

LICENSE = "unknown"

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_HEADERS = {
    "User-Agent": _UA,
    "Accept": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "application/vnd.ms-excel,text/csv,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.7",
    "Origin": "https://data.tuik.gov.tr",
    "Referer": "https://data.tuik.gov.tr/",
}

# Logical id -> {url, manual_glob, ...metadata}
SUPPORTED: dict[str, dict[str, Any]] = {
    "cpi": {
        "url": "https://biruni.tuik.gov.tr/medas/?kn=84",
        "manual_glob": "cpi",
        "title": "Consumer Price Index (TÜFE), monthly index",
        "frequency": "monthly",
        "units": "index, 2003=100",
        "currency": None,
        "methodology_url": "https://data.tuik.gov.tr/Kategori/GetKategori?p=Enflasyon-ve-Fiyat-106",
    },
    "unemployment": {
        "url": "https://biruni.tuik.gov.tr/medas/?kn=72",
        "manual_glob": "unemployment",
        "title": "Labour force survey — unemployment rate (HİA)",
        "frequency": "monthly",
        "units": "percent of labour force",
        "currency": None,
        "methodology_url": "https://data.tuik.gov.tr/Kategori/GetKategori?p=Istihdam-Issizlik-ve-Ucret-108",
    },
    "gdp": {
        "url": "https://biruni.tuik.gov.tr/medas/?kn=113",
        "manual_glob": "gdp",
        "title": "Gross domestic product, expenditure approach (quarterly)",
        "frequency": "quarterly",
        "units": "TRY million, current prices / chain-linked index",
        "currency": "TRY",
        "methodology_url": "https://data.tuik.gov.tr/Kategori/GetKategori?p=Ulusal-Hesaplar-113",
    },
    "exports": {
        "url": "https://biruni.tuik.gov.tr/medas/?kn=82",
        "manual_glob": "exports",
        "title": "Foreign trade — exports by month",
        "frequency": "monthly",
        "units": "USD thousands (FOB)",
        "currency": "USD",
        "methodology_url": "https://data.tuik.gov.tr/Kategori/GetKategori?p=Dis-Ticaret-104",
    },
}


class TuikError(RuntimeError):
    pass


def _resolve(series_id: str) -> str:
    s = series_id.strip().lower()
    if s in SUPPORTED:
        return s
    # Tolerate aliases like 'tufe' (Turkish for CPI) and 'hia'.
    aliases = {
        "tufe": "cpi",
        "tüfe": "cpi",
        "hia": "unemployment",
        "issizlik": "unemployment",
        "işsizlik": "unemployment",
        "gsyih": "gdp",
        "ihracat": "exports",
    }
    return aliases.get(s, s)


def _try_http(url: str) -> bytes | None:
    """Best-effort HTTP fetch. Returns binary body on success, None on any
    failure. TÜİK's biruni endpoint occasionally returns 200 with an HTML
    "session expired" body; we sniff for Excel/CSV magic bytes."""
    try:
        # session for cookie persistence (some indicator pulls 302 → cookie set)
        with requests.Session() as sess:
            sess.headers.update(_HEADERS)
            # Warm-up GET to set the ASP.NET session cookie.
            try:
                sess.get("https://data.tuik.gov.tr/", timeout=30)
            except requests.RequestException:
                pass
            r = sess.get(url, timeout=60, allow_redirects=True)
        if r.status_code != 200 or not r.content:
            return None
        head = r.content[:8]
        # XLSX (PK..), XLS (D0CF11E0..), or CSV-ish text (digit/letter/quote/BOM).
        if head[:2] == b"PK":
            return r.content
        if head[:4] == b"\xd0\xcf\x11\xe0":
            return r.content
        # CSV heuristic: looks like text and not <html
        sample = r.content[:512].lower()
        if b"<html" in sample or b"<!doctype" in sample:
            return None
        return r.content
    except requests.RequestException:
        return None


def _parse_bytes(blob: bytes, *, series_id: str) -> pd.DataFrame:
    head = blob[:8]
    if head[:2] == b"PK":
        return pd.read_excel(io.BytesIO(blob), engine="openpyxl")
    if head[:4] == b"\xd0\xcf\x11\xe0":
        return pd.read_excel(io.BytesIO(blob), engine="xlrd")
    # Try CSV; TÜİK CSVs are sometimes semicolon-delimited.
    text = blob.decode("utf-8-sig", errors="replace")
    for sep in (",", ";", "\t"):
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, engine="python", on_bad_lines="skip")
        except Exception:
            continue
        if df.shape[1] >= 2 and len(df) > 0:
            return df
    raise TuikError(f"could not parse TÜİK payload for {series_id!r}")


def _manual_fallback(series_id: str, glob_hint: str) -> tuple[pd.DataFrame, str]:
    """Look in data/manual/tuik/ for a file whose name contains ``glob_hint``.

    Falls back to the latest file in the directory if no match is found.
    Returns (frame, file_name).
    """
    pub_dir = MANUAL_ROOT / "tuik"
    if not pub_dir.exists():
        raise ManualDropError(
            "TÜİK biruni HTTP fetch failed and no manual-drop dir exists. "
            "Create data/manual/tuik/ and drop the latest publisher Excel/CSV "
            f"there (filename should contain '{glob_hint}')."
        )
    candidates = [
        p for p in pub_dir.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and p.suffix.lower() in (".xlsx", ".xls", ".csv")
    ]
    if not candidates:
        raise ManualDropError(
            "TÜİK manual-drop dir is empty. Drop the latest publisher Excel/CSV "
            f"into data/manual/tuik/ (filename should contain '{glob_hint}')."
        )
    matched = [p for p in candidates if glob_hint.lower() in p.name.lower()]
    chosen = max(
        matched or candidates,
        key=lambda p: (p.name, p.stat().st_mtime),
    )
    if chosen.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(chosen)
    else:
        df = pd.read_csv(chosen)
    return df, chosen.name


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch a TÜİK series.

    series_id: logical alias from SUPPORTED ('cpi', 'unemployment', 'gdp',
               'exports') or one of the Turkish-language aliases ('tufe',
               'issizlik', 'gsyih', 'ihracat').
    """
    fetch_ts = utc_now()
    sid = _resolve(series_id)
    if sid not in SUPPORTED:
        raise TuikError(
            f"unknown TÜİK series_id {series_id!r}; "
            f"known: {sorted(SUPPORTED)}"
        )
    meta = SUPPORTED[sid]

    used_manual = False
    manual_file: str | None = None
    blob = _try_http(meta["url"])
    if blob is not None:
        try:
            df = _parse_bytes(blob, series_id=sid)
        except TuikError:
            df, manual_file = _manual_fallback(sid, meta["manual_glob"])
            used_manual = True
    else:
        df, manual_file = _manual_fallback(sid, meta["manual_glob"])
        used_manual = True

    # Coerce object columns to string so pyarrow serialises cleanly.
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype("string")

    out, sha = write_vintage(
        publisher="tuik",
        series_id=sid,
        frame=df,
        fetch_utc=fetch_ts,
    )

    source_url = (
        f"manual://{manual_file}" if used_manual else meta["url"]
    )

    return FetchResult(
        publisher="tuik",
        series_id=sid,
        source_url=source_url,
        methodology_url=meta["methodology_url"],
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta["frequency"],
        units=meta["units"],
        currency=meta.get("currency"),
        start_date=None,
        end_date=None,
        sha256=sha,
        parquet_path=out,
        extra={
            "title": meta["title"],
            "transport": "manual_drop" if used_manual else "http",
            "manual_file": manual_file,
            "n_columns": len(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
