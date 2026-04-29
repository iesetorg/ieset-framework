"""Shared helpers for manual-drop publishers.

Publishers where Cloudflare/JS/session-gating blocks automated access use
this pattern: user drops files into data/manual/<publisher>/, the fetcher
picks the latest matching file and parses it. Refresh cadence matches the
publisher's own release schedule (usually annual).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANUAL_ROOT = ROOT / "data" / "manual"


class ManualDropError(RuntimeError):
    pass


def find_latest(publisher: str, *extensions: str) -> Path:
    """Locate the latest file for a manual-drop publisher.

    publisher: subdirectory name under data/manual/
    extensions: file extensions to accept (e.g. 'xlsx', 'xls', 'csv', 'zip').
                If empty, accepts all files.
    Returns the Path of the file with lexicographically-latest filename
    (falling back to modification time on ties).
    """
    pub_dir = MANUAL_ROOT / publisher
    if not pub_dir.exists():
        raise ManualDropError(
            f"No manual-drop dir for '{publisher}'. Create {pub_dir.relative_to(ROOT)} "
            f"and drop the latest publisher file there."
        )
    exts = tuple(f".{e.lstrip('.')}" for e in extensions) if extensions else None
    candidates = [p for p in pub_dir.iterdir() if p.is_file() and not p.name.startswith(".")]
    if exts:
        candidates = [p for p in candidates if p.suffix.lower() in exts]
    if not candidates:
        exts_str = ", ".join(extensions) if extensions else "any"
        raise ManualDropError(
            f"No files ({exts_str}) in {pub_dir.relative_to(ROOT)}. "
            f"Drop the latest publisher file there."
        )
    return max(candidates, key=lambda p: (p.name, p.stat().st_mtime))
