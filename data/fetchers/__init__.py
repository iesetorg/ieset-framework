"""Publisher fetchers.

REGISTRY is loaded lazily from data/fetchers/publishers.yaml at import time.
Every publisher whose `status: ready` and `fetcher_module` points at an
importable module is added. Aliases are registered too. This keeps the
hardcoded-dict failure mode out of the codebase — if a publisher flips from
pending → ready by adding `fetcher_module`, it becomes usable without further
code changes here.

Each fetcher module must expose:
    fetch(series_id: str, *, vintage_utc: datetime | None = None, **kwargs) -> FetchResult
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import yaml

_PUBLISHERS_PATH = Path(__file__).parent / "publishers.yaml"

REGISTRY: dict[str, Any] = {}


def _load_registry() -> dict[str, Any]:
    if not _PUBLISHERS_PATH.exists():
        return {}
    doc = yaml.safe_load(_PUBLISHERS_PATH.read_text()) or {}
    result: dict[str, Any] = {}
    for pub_id, rec in (doc.get("publishers") or {}).items():
        if rec.get("status") != "ready":
            continue
        module_path = rec.get("fetcher_module")
        if not module_path:
            continue
        try:
            mod = importlib.import_module(module_path)
        except ImportError as e:
            # Silent — a ready publisher with a missing module is a publishers.yaml
            # bug, caught by derive_coverage.py's CI check. Don't blow up imports here.
            continue
        result[pub_id] = mod
        for alias in rec.get("aliases", []) or []:
            result[alias] = mod
    return result


REGISTRY.update(_load_registry())


def fetch(publisher_id: str, series_id: str, **kwargs):
    """Dispatch a fetch through the registry.

    Raises KeyError if the publisher is not registered as ready.
    """
    mod = REGISTRY.get(publisher_id)
    if mod is None:
        raise KeyError(
            f"publisher {publisher_id!r} has no ready fetcher; "
            f"known publishers: {sorted(REGISTRY)}"
        )
    return mod.fetch(series_id, **kwargs)


__all__ = ["REGISTRY", "fetch"]
