"""Hanke-Krus hyperinflation catalogue fetcher.

Source: Hanke, S. H. & Krus, N. (2012). 'World Hyperinflations'. Cato
Institute Working Paper #8. 57 documented hyperinflation episodes meeting
Cagan's >=50%/month threshold.

The JHU-hosted landing page returns 403 to automated fetchers. Cato's mirror
of the same working paper (same data table) returns 200 cleanly. This
fetcher hits Cato, parses pages 13-15 where the table lives, and emits a
tidy DataFrame.

Content is frozen (2012 paper + 2016 update). Post-2012 episodes (Venezuela
2016-2019, Lebanon 2019-2023 near-threshold) require manual supplementation
documented in hypotheses/monetary/hyperinflation_fiscal_dominance_coding.md.
"""
from __future__ import annotations

import io
import re
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://www.cato.org/sites/cato.org/files/pubs/pdf/workingpaper-8.pdf"
LICENSE = "academic — Hanke & Krus 2012; citation required"
UA = {"User-Agent": "Mozilla/5.0"}

# Table pages in the Cato PDF (0-indexed)
TABLE_PAGES = [12, 13, 14]

# Countries appearing in the catalogue — used as row-anchors in the parse,
# because pdfplumber table extraction flattens the multi-column headers
# but the country names are reliable row-start markers.
EPISODE_COUNTRIES = [
    "Hungary", "Zimbabwe", "Yugoslavia", "Republika Srpska", "Germany",
    "Greece", "China", "Free City of Danzig", "Armenia", "Turkmenistan",
    "Taiwan", "Peru", "Bosnia and Herzegovina", "France", "Nicaragua",
    "Congo", "Ukraine", "Poland", "Belarus", "Kazakhstan", "Tajikistan",
    "Kyrgyzstan", "Georgia", "Argentina", "Bolivia", "Azerbaijan",
    "Brazil", "Uzbekistan", "Russia", "Moldova", "Estonia", "Austria",
    "Bulgaria", "Latvia", "Chile", "Venezuela", "Angola", "Ossetia",
    "Montenegro", "Mexico", "Serbia", "Soviet Union", "Israel", "Lithuania",
    "Vietnam", "Ghana", "Egypt", "Uganda",
]


class HankeError(RuntimeError):
    pass


def fetch(series_id: str = "hyperinflation_table", *, vintage_utc: datetime | None = None) -> FetchResult:
    try:
        import pdfplumber  # type: ignore
    except ImportError as e:
        raise HankeError("pdfplumber not installed; pip install pdfplumber") from e

    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()

    rows: list[dict] = []
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        for page_idx in TABLE_PAGES:
            if page_idx >= len(pdf.pages):
                continue
            text = pdf.pages[page_idx].extract_text() or ""
            for line in text.splitlines():
                parsed = _parse_row(line)
                if parsed:
                    rows.append(parsed)

    if not rows:
        raise HankeError("failed to parse any rows from Hanke-Krus table")
    df = pd.DataFrame(rows)

    path_out, sha = write_vintage(
        publisher="hanke",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="hanke",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://www.cato.org/working-paper/world-hyperinflations",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="episode",
        units="monthly inflation rate at peak; episode-level",
        currency=None,
        start_date=(
            str(df["start_date"].dropna().astype(str).min())
            if "start_date" in df.columns and df["start_date"].notna().any()
            else None
        ),
        end_date=(
            str(df["end_date"].dropna().astype(str).max())
            if "end_date" in df.columns and df["end_date"].notna().any()
            else None
        ),
        sha256=sha,
        parquet_path=path_out,
        extra={
            "source_paper": "Hanke & Krus 2012, Cato WP #8",
            "catalogue_vintage": "2012 (post-2016 supplementation required for Venezuela, Lebanon)",
            "n_episodes": len(df),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


# Row format from the PDF (one line per episode, e.g.):
# Hungary1 Aug. 1945 Jul. 1946 Jul. 1946 4.19 × 1016% 207% 15.0 hours Pengő Consumer
# Columns: location<note>, start_date, end_date, peak_month, peak_monthly_rate,
#          peak_daily_rate, doubling_time, currency, price_index_type
_ROW_RE = re.compile(
    r"^(?P<country>[A-Z][A-Za-z\.\s\-]+?)\s*\d*\s+"                    # country name + optional footnote digit
    r"(?P<start>(?:\w{3,4}\.?|[A-Z][a-z]+-?)\s*\d{4})\s+"             # start date 'Aug. 1945' or 'Mid-Nov. 2008'
    r"(?P<end>(?:\w{3,4}\.?|[A-Z][a-z]+-?|Mid-\w{3,4}\.?)\s*\d{4})\s+" # end date
    r"(?P<peak_month>(?:\w{3,4}\.?|[A-Z][a-z]+-?|Mid-\w{3,4}\.?)\s*\d{4})\s+"  # peak month
    r"(?P<peak_monthly>[\d\.,]+(?:\s*×\s*10\^?\d+)?%?)\s+"             # peak monthly rate
    r"(?P<peak_daily>[\d\.,]+%?)\s+"                                   # peak daily rate
    r"(?P<doubling>[\d\.,]+\s*(?:days?|hours?|minutes?|seconds?))\s+"  # doubling time
    r"(?P<currency>[A-Za-zǿ\s\-ğ]+?)\s+"                               # currency (includes special chars)
    r"(?P<price_index>Consumer|Implied|Exchange|Wholesale)",           # price index type
    re.IGNORECASE,
)


def _parse_row(line: str) -> dict | None:
    line = line.strip()
    if not line or len(line) < 40:
        return None
    # Must start with a known country (or 'Republika', 'Free City', etc.)
    if not any(line.startswith(c) for c in EPISODE_COUNTRIES):
        return None
    m = _ROW_RE.match(line)
    if not m:
        # Row matched a known country but didn't parse — keep the raw line for manual review.
        return {"country_raw": line, "parse_status": "country_matched_but_row_regex_failed"}
    d = m.groupdict()
    return {
        "country": d["country"].strip(),
        "start_date": d["start"].strip(),
        "end_date": d["end"].strip(),
        "peak_month": d["peak_month"].strip(),
        "peak_monthly_rate_raw": d["peak_monthly"].strip(),
        "peak_daily_rate_raw": d["peak_daily"].strip(),
        "doubling_time_raw": d["doubling"].strip(),
        "currency": d["currency"].strip(),
        "price_index_type": d["price_index"].strip(),
        "parse_status": "parsed",
    }
