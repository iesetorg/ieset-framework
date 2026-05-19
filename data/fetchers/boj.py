"""Bank of Japan Time-Series Data Search fetcher.

BoJ added a documented machine API in February 2026. The fetcher first tries
that official API and falls back to the historical manual-drop pattern if the
requested alias cannot be discovered. Direct API form:

    series_id="MD01:MABS1AN11"  # db:code

Alias form:

    series_id="monetary_base"   # discover from BoJ metadata, then fetch
"""
from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._http import get as robust_get
from ._manual_utils import MANUAL_ROOT, ManualDropError, find_latest

LICENSE = "Bank of Japan terms — attribution required"
BASE = "https://www.stat-search.boj.or.jp/api/v1"
METHOD_URL = "https://www.stat-search.boj.or.jp/info/api_manual_en.pdf"

ALIAS_SEARCH: dict[str, list[dict[str, Any]]] = {
    "monetary_base": [
        {"db": "MD01", "terms": ("monetary base",), "avoid": ("component",)},
        {"db": "MD09", "terms": ("monetary base",), "avoid": ("component",)},
    ],
    "money_stock_m2": [
        {"db": "MD02", "terms": ("m2", "money stock"), "avoid": ("velocity",)},
        {"db": "MD04", "terms": ("m2",), "avoid": ("velocity",)},
    ],
    "M2": [
        {"db": "MD02", "terms": ("m2", "money stock"), "avoid": ("velocity",)},
    ],
    "policy_rate": [
        {"db": "IR01", "terms": ("uncollateralized overnight call rate",), "avoid": ("euroyen",)},
        {"db": "IR01", "terms": ("basic discount",), "avoid": ()},
    ],
    "JPNDISCOUNT": [
        {"db": "IR01", "terms": ("basic discount",), "avoid": ()},
    ],
    "bond_yields_10y": [
        {"db": "IR01", "terms": ("government bond", "10-year"), "avoid": ("index",)},
        {"db": "IR01", "terms": ("jgb", "10-year"), "avoid": ()},
    ],
    "bond_yields_30y": [
        {"db": "IR01", "terms": ("government bond", "30-year"), "avoid": ("index",)},
        {"db": "IR01", "terms": ("jgb", "30-year"), "avoid": ()},
    ],
}


class BojError(RuntimeError):
    pass


def _read_csv_payload(content: bytes) -> pd.DataFrame:
    decoded = None
    for enc in ("utf-8-sig", "cp932"):
        try:
            decoded = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        decoded = content.decode("utf-8", errors="replace")
    lines = decoded.splitlines()
    header_index = 0
    for idx, line in enumerate(lines):
        clean = line.lstrip("\ufeff")
        if clean.startswith("SERIES_CODE,"):
            header_index = idx
            break
    trimmed = "\n".join(lines[header_index:])
    last: Exception | None = None
    for kwargs in ({"sep": None, "engine": "python"}, {}):
        try:
            return pd.read_csv(io.StringIO(trimmed), low_memory=False, **kwargs)
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise BojError(f"could not parse BoJ CSV payload: {last}")


def _manual_fetch(series_id: str, fetch_ts: datetime, vintage_utc: datetime | None) -> FetchResult:
    accepted = ("csv", "xlsx", "xls")
    try:
        series_dir = MANUAL_ROOT / "boj" / series_id
        if series_dir.exists():
            candidates = [
                p for p in series_dir.iterdir()
                if p.is_file() and p.suffix.lower().lstrip(".") in accepted
            ]
            if candidates:
                path = max(candidates, key=lambda p: (p.name, p.stat().st_mtime))
            else:
                raise ManualDropError("no series-specific file")
        else:
            path = find_latest("boj", *accepted)
    except Exception as exc:  # noqa: BLE001
        raise BojError(
            f"BoJ API discovery failed and no manual drop was available for {series_id}: {exc}"
        ) from exc

    if path.suffix.lower() in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    else:
        df = pd.read_csv(path)
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype("string")
    out, sha = write_vintage(publisher="boj", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="boj",
        series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url=METHOD_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="per BoJ/manual file",
        units="per BoJ series metadata",
        currency="JPY",
        start_date=None,
        end_date=None,
        sha256=sha,
        parquet_path=out,
        extra={
            "manual_file": path.name,
            "n_columns": len(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _normalise_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).lower()).strip()


def _metadata(db: str) -> pd.DataFrame:
    payload = robust_get(
        f"{BASE}/getMetadata",
        params={"format": "csv", "lang": "en", "db": db},
        timeout=180,
        return_http_errors=True,
    )
    if payload.status_code >= 400:
        raise BojError(f"BoJ metadata HTTP {payload.status_code} for db={db}")
    df = _read_csv_payload(payload.content)
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        raise BojError(f"BoJ metadata returned no rows for db={db}")
    return df


def _find_code_col(df: pd.DataFrame) -> str:
    for col in df.columns:
        text = col.lower()
        if "code" in text and ("series" in text or "time" in text or text == "code"):
            return col
    for col in df.columns:
        if "code" in col.lower():
            return col
    return df.columns[0]


def _split_db_code(db: str, value: Any) -> tuple[str, str]:
    token = str(value).strip()
    if "'" in token:
        maybe_db, code = token.split("'", 1)
        return maybe_db or db, code
    if ":" in token:
        maybe_db, code = token.split(":", 1)
        return maybe_db or db, code
    return db, token


def _discover_alias(series_id: str) -> tuple[str, str, dict[str, Any]]:
    candidates = ALIAS_SEARCH.get(series_id)
    if not candidates:
        raise BojError(f"unsupported BoJ alias {series_id!r}")

    best: tuple[int, str, str, dict[str, Any]] | None = None
    for candidate in candidates:
        db = candidate["db"]
        terms = tuple(_normalise_text(t) for t in candidate["terms"])
        avoid = tuple(_normalise_text(t) for t in candidate.get("avoid", ()))
        try:
            meta = _metadata(db)
        except Exception:
            continue
        code_col = _find_code_col(meta)
        for _, row in meta.iterrows():
            raw_code = row.get(code_col)
            if pd.isna(raw_code) or not str(raw_code).strip():
                continue
            hay = _normalise_text(" ".join(str(row.get(c, "")) for c in meta.columns))
            if not all(term in hay for term in terms):
                continue
            penalty = sum(1 for bad in avoid if bad and bad in hay)
            score = 100 + sum(len(term) for term in terms) - (25 * penalty)
            resolved_db, code = _split_db_code(db, raw_code)
            rec = {str(k): str(v) for k, v in row.items() if pd.notna(v)}
            if best is None or score > best[0]:
                best = (score, resolved_db, code, rec)
    if best is None:
        raise BojError(f"could not discover BoJ code for alias {series_id!r}")
    _, db, code, rec = best
    return db, code, rec


def _resolve(series_id: str) -> tuple[str, str, dict[str, Any]]:
    if ":" in series_id:
        db, code = series_id.split(":", 1)
        return db, code, {"direct": True}
    if "/" in series_id:
        db, code = series_id.split("/", 1)
        return db, code, {"direct": True}
    return _discover_alias(series_id)


def _fetch_api(db: str, code: str, *, start_date: str | None = None) -> tuple[pd.DataFrame, str]:
    params = {"format": "csv", "lang": "en", "db": db, "code": code}
    if start_date:
        params["startDate"] = start_date
    payload = robust_get(
        f"{BASE}/getDataCode",
        params=params,
        timeout=180,
        return_http_errors=True,
    )
    if payload.status_code >= 400:
        raise BojError(f"BoJ data HTTP {payload.status_code} for {db}:{code}")
    df = _read_csv_payload(payload.content)
    if df.empty:
        raise BojError(f"BoJ returned no rows for {db}:{code}")
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        lower = col.lower()
        if lower in {"date", "time_period", "period"} or "date" in lower:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().any():
                df = df.rename(columns={col: "date"})
                df["date"] = parsed
                break
    for col in df.columns:
        if col == "date":
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().sum() >= max(3, int(len(df) * 0.25)):
            df[col] = numeric
    return df, payload.transport


def fetch(series_id: str = "money_stock_m2", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    try:
        db, code, meta = _resolve(series_id)
        start_date = meta.get("START_OF_THE_TIME_SERIES") if isinstance(meta, dict) else None
        if start_date is not None and str(start_date).lower() != "nan":
            try:
                start_date = str(int(float(str(start_date))))
            except ValueError:
                start_date = str(start_date)
        else:
            start_date = None
        if "@" in code:
            start_date = None
        df, transport = _fetch_api(db, code, start_date=start_date)
        source_url = f"{BASE}/getDataCode?format=csv&lang=en&db={db}&code={code}"
        extra_source = {
            "api_db": db,
            "api_code": code,
            "api_metadata": meta,
            "transport": transport,
        }
    except Exception:
        return _manual_fetch(series_id, fetch_ts, vintage_utc)

    out, sha = write_vintage(publisher="boj", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    start = end = None
    if "date" in df.columns and df["date"].notna().any():
        start = df["date"].min().date().isoformat()
        end = df["date"].max().date().isoformat()

    return FetchResult(
        publisher="boj",
        series_id=series_id,
        source_url=source_url,
        methodology_url=METHOD_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="per BoJ series metadata",
        units="per BoJ series metadata",
        currency="JPY",
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=out,
        extra={
            **extra_source,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
