"""Raw-payload archive for fetchers added 2026-10-09 (IESET x-build).

Raw downloads are kept next to the parquet vintages so a publisher revision can
be diffed later. Files are timestamped and never overwritten:

    data/raw/<publisher>/<sanitised_name>@<fetch_utc>.<ext>

data/raw/ is gitignored, like data/vintages/.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from ._base import ROOT, _sanitise, utc_stamp

RAW = ROOT / "data" / "raw"

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def save_raw(publisher: str, name: str, payload: bytes, fetch_utc: datetime, ext: str) -> tuple[Path, str]:
    out_dir = RAW / publisher
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_sanitise(name)}@{utc_stamp(fetch_utc)}.{ext.lstrip('.')}"
    if path.exists():  # never overwrite an earlier vintage
        raise FileExistsError(path)
    path.write_bytes(payload)
    return path, hashlib.sha256(payload).hexdigest()


def load_env_file() -> None:
    """Populate os.environ from <repo>/.env (gitignored) without overriding."""
    import os
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
