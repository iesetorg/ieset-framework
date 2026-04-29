"""Shared contract for every publisher fetcher.

Per METHODOLOGY.md invariant #2: every fetch produces a FetchResult carrying
publisher, source_url, license, fetch_utc, methodology_url, and SHA256 of the
parquet payload. Manifests under data/manifests/ record every run.

Vintage files are written to:
    data/vintages/<publisher>/<sanitised_series_id>@<fetch_utc>.parquet

They are gitignored (too large). The manifest + fetcher code + vintage_utc is
sufficient for reproducibility.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
VINTAGES = ROOT / "data" / "vintages"
MANIFESTS = ROOT / "data" / "manifests"

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitise(s: str) -> str:
    return _SAFE.sub("_", s)


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def utc_stamp(dt: datetime | None = None) -> str:
    dt = (dt or utc_now()).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H%M%SZ")


@dataclass
class FetchResult:
    publisher: str
    series_id: str
    source_url: str
    methodology_url: str
    license: str
    fetch_utc: datetime
    rows: int
    frequency: str
    units: str
    currency: str | None
    start_date: str | None
    end_date: str | None
    sha256: str
    parquet_path: Path
    extra: dict[str, Any] = field(default_factory=dict)

    def as_manifest_entry(self) -> dict[str, Any]:
        d = asdict(self)
        d["fetch_utc"] = self.fetch_utc.isoformat()
        d["parquet_path"] = str(self.parquet_path.relative_to(ROOT))
        return d


def write_vintage(
    *,
    publisher: str,
    series_id: str,
    frame: pd.DataFrame,
    fetch_utc: datetime,
) -> tuple[Path, str]:
    safe = _sanitise(series_id)
    out_dir = VINTAGES / publisher
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe}@{utc_stamp(fetch_utc)}.parquet"
    frame.to_parquet(path, engine="pyarrow", index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, digest


def write_manifest(results: list[FetchResult], run_stamp: str | None = None) -> Path:
    run_stamp = run_stamp or utc_stamp()
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    path = MANIFESTS / f"fetch_run_{run_stamp}.yaml"
    payload = {
        "run_utc": run_stamp,
        "entries": [r.as_manifest_entry() for r in results],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path
