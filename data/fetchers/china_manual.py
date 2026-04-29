"""China manual-drop publisher.

Reads curated YAML files in `data/manual/china/` (one file per academic
series — e.g. great_leap_mortality.yaml, grain_output_1957_1965.yaml)
and emits tidy parquet vintages under `data/vintages/china_manual/<series_id>@<ts>.parquet`.

Each YAML file declares a `publisher: china_manual` and a `series_id`,
and provides one of:
    - an `observations:` list of {country, year, value} rows
      (consumed directly by the multi-metric runner)
    - a `canonical:` block with a single (country, year, value) — for
      metrics that summarise to a scalar (e.g. cumulative excess mortality)

This keeps the manual citation-keyed academic data discoverable,
reviewable, and consumable through the same vintage interface as
automated publishers.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "academic_citation_fair_use"
MANUAL_DIR = Path(__file__).resolve().parents[2] / "data" / "manual" / "china"


class ChinaManualError(RuntimeError):
    pass


def _yaml_files() -> list[Path]:
    if not MANUAL_DIR.exists():
        raise ChinaManualError(f"Manual dir not found: {MANUAL_DIR}")
    return sorted(p for p in MANUAL_DIR.glob("*.yaml") if not p.name.startswith("_"))


def _records_from_doc(doc: dict) -> tuple[str, pd.DataFrame, dict]:
    """Return (series_id, tidy_dataframe, extra_metadata)."""
    series_id = doc.get("series_id")
    if not series_id:
        raise ChinaManualError("yaml doc missing series_id")

    rows: list[dict] = []
    if "observations" in doc and isinstance(doc["observations"], list):
        for r in doc["observations"]:
            if "value" not in r or "year" not in r:
                continue
            rows.append({
                "country_iso3": r.get("country", "CHN"),
                "year": int(r["year"]),
                "value": float(r["value"]),
            })

    canonical = doc.get("canonical")
    if canonical and isinstance(canonical, dict) and not rows:
        # Single-scalar series (e.g. cumulative excess mortality)
        rows.append({
            "country_iso3": canonical.get("country", "CHN"),
            "year": int(canonical.get("year", 1962)),
            "value": float(canonical["value"]),
        })
    elif canonical and isinstance(canonical, dict) and rows:
        # Append the canonical scalar too if its (country, year) is not already in rows
        # — this is useful for series like provincial_excess_mortality where the
        # observations are per-province but the runner needs a per-(country, year) value.
        cy = (canonical.get("country", "CHN"), int(canonical.get("year", 1962)))
        if not any((r["country_iso3"], r["year"]) == cy for r in rows):
            rows.append({
                "country_iso3": cy[0],
                "year": cy[1],
                "value": float(canonical["value"]),
            })

    if not rows:
        raise ChinaManualError(f"no observations or canonical scalar in series {series_id}")

    df = pd.DataFrame(rows)
    df["country_iso3"] = df["country_iso3"].astype("string")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year", "value"]).sort_values(["country_iso3", "year"]).reset_index(drop=True)

    extra = {
        "units": doc.get("units"),
        "citations": doc.get("citations") or [],
        "n_obs": len(df),
    }
    return series_id, df, extra


def fetch(series_id: str | None = None, *, vintage_utc: datetime | None = None) -> FetchResult:
    """Fetch one (if series_id given) or panic — caller should iterate via fetch_all().

    Behaviour: if series_id is None, fetches the FIRST yaml's series. Use
    fetch_all() to publish every yaml in the directory as its own vintage.
    """
    files = _yaml_files()
    target_file = None
    target_doc = None
    if series_id is None:
        target_file = files[0]
        target_doc = yaml.safe_load(target_file.read_text())
    else:
        for f in files:
            doc = yaml.safe_load(f.read_text())
            if doc.get("series_id") == series_id:
                target_file = f
                target_doc = doc
                break
        if target_doc is None:
            raise ChinaManualError(
                f"series_id {series_id!r} not found among {[f.name for f in files]}"
            )

    sid, df, extra = _records_from_doc(target_doc)
    fetch_ts = utc_now()
    path_out, sha = write_vintage(
        publisher="china_manual",
        series_id=sid,
        frame=df,
        fetch_utc=fetch_ts,
    )
    start = int(df["year"].min()) if not df.empty else None
    end = int(df["year"].max()) if not df.empty else None

    return FetchResult(
        publisher="china_manual",
        series_id=sid,
        source_url=f"manual://china/{target_file.name}",
        methodology_url="see data/manual/china/_provenance.md",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=extra.get("units") or "see yaml",
        currency=None,
        start_date=str(start) if start else None,
        end_date=str(end) if end else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "manual_file": target_file.name,
            "n_citations": len(extra.get("citations") or []),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def fetch_all(*, vintage_utc: datetime | None = None) -> list[FetchResult]:
    """Publish every yaml in data/manual/china/ as its own vintage."""
    out: list[FetchResult] = []
    for f in _yaml_files():
        doc = yaml.safe_load(f.read_text())
        sid = doc.get("series_id")
        if not sid:
            continue
        out.append(fetch(series_id=sid, vintage_utc=vintage_utc))
    return out
