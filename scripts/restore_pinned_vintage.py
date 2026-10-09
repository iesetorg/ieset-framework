#!/usr/bin/env python3
"""Recover one ignored vintage from another checkout using a committed pin.

Only hashes in HEAD under data/manifests or scripts/frozen_source_vintages.json
are trusted. The default invocation checks both files and makes no changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MANIFEST_PATHS = ("data/manifests", "scripts/frozen_source_vintages.json")


class RecoveryError(ValueError):
    """An input or pinned-file check failed closed."""


def vintage_relative_path(raw: str) -> Path:
    """Accept only an exact POSIX path inside data/vintages/."""
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise RecoveryError("vintage path must be a POSIX relative path")
    if any(ord(char) < 32 or ord(char) == 127 for char in raw):
        raise RecoveryError("vintage path contains a control character")
    parts = raw.split("/")
    if (parts[:2] != ["data", "vintages"] or len(parts) < 4
            or any(part in ("", ".", "..") for part in parts)):
        raise RecoveryError("vintage path must be below data/vintages without traversal")
    return Path(*parts)


def _git(repo_root: Path, *args: str, missing_ok: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True, capture_output=True, check=False,
    )
    if missing_ok and result.returncode == 1:
        return ""
    if result.returncode != 0:
        raise RecoveryError(f"Git manifest lookup failed: {result.stderr.strip()}")
    return result.stdout


def _candidate_records(doc: Any) -> list[dict[str, Any]]:
    if not isinstance(doc, dict):
        return []
    records: list[dict[str, Any]] = []
    entries = doc.get("entries")
    if isinstance(entries, list):
        records.extend(entry for entry in entries if isinstance(entry, dict))
    source_vintage = doc.get("source_vintage")
    if isinstance(source_vintage, dict):
        records.append(source_vintage)
    cases = doc.get("cases")
    if isinstance(cases, dict):
        for case_records in cases.values():
            if isinstance(case_records, list):
                records.extend(entry for entry in case_records if isinstance(entry, dict))
    return records


def committed_pin(repo_root: Path, raw_path: str) -> tuple[str, list[str]]:
    """Return the unambiguous SHA-256 and committed manifest names for a path."""
    vintage_relative_path(raw_path)
    grep = _git(
        repo_root, "grep", "-l", "-F", "-e", raw_path,
        "HEAD", "--", *MANIFEST_PATHS, missing_ok=True,
    )
    pins: dict[str, list[str]] = {}
    for line in grep.splitlines():
        prefix = "HEAD:"
        if not line.startswith(prefix):
            raise RecoveryError("unexpected Git manifest result")
        manifest = line[len(prefix):]
        if not (manifest.startswith("data/manifests/") and
                manifest.endswith((".yaml", ".yml")) or
                manifest == "scripts/frozen_source_vintages.json"):
            raise RecoveryError("manifest outside approved tracked paths")
        content = _git(repo_root, "show", f"HEAD:{manifest}")
        try:
            doc = json.loads(content) if manifest.endswith(".json") else yaml.safe_load(content)
        except (ValueError, yaml.YAMLError) as exc:
            raise RecoveryError(f"committed manifest could not be parsed: {manifest}") from exc
        for record in _candidate_records(doc):
            if record.get("parquet_path", record.get("path")) != raw_path:
                continue
            digest = record.get("sha256")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                raise RecoveryError(f"missing or invalid SHA-256 pin in {manifest}")
            pins.setdefault(digest, []).append(manifest)
    if not pins:
        raise RecoveryError("no SHA-256 pin for this path in committed manifests")
    if len(pins) != 1:
        raise RecoveryError("conflicting SHA-256 pins for this path in committed manifests")
    digest, manifests = next(iter(pins.items()))
    return digest, sorted(set(manifests))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _reject_symlink_components(root: Path, relative: Path) -> None:
    candidate = root
    for part in relative.parts:
        candidate /= part
        if candidate.is_symlink():
            raise RecoveryError(f"symlink in vintage path: {candidate}")


def recover(
    repo_root: Path, source_root: Path, raw_path: str, *, apply: bool = False,
) -> str:
    relative = vintage_relative_path(raw_path)
    if not source_root.is_absolute() or not source_root.is_dir():
        raise RecoveryError("--source-root must be an existing absolute checkout path")
    if not repo_root.is_dir():
        raise RecoveryError("destination checkout does not exist")
    repo_root = repo_root.resolve()
    source_root = source_root.resolve()
    if source_root == repo_root:
        raise RecoveryError("--source-root must be a different checkout")

    expected, manifests = committed_pin(repo_root, raw_path)
    _reject_symlink_components(source_root, relative)
    _reject_symlink_components(repo_root, relative)
    ignored = subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "-q", "--", raw_path],
        capture_output=True, check=False,
    )
    if ignored.returncode != 0:
        raise RecoveryError("destination vintage path is not Git-ignored")

    source = source_root / relative
    destination = repo_root / relative
    if not source.is_file():
        raise RecoveryError(f"source vintage is absent: {source}")
    if file_sha256(source) != expected:
        raise RecoveryError("source vintage SHA-256 differs from committed manifest")

    if destination.exists():
        if not destination.is_file() or file_sha256(destination) != expected:
            raise RecoveryError("destination exists with a different SHA-256; refusing overwrite")
        return f"already present and verified: {raw_path} ({expected}); {', '.join(manifests)}"
    if not apply:
        return f"dry run; would copy verified vintage: {raw_path} ({expected}); {', '.join(manifests)}"

    destination.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(repo_root, relative)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.",
            suffix=".tmp", delete=False,
        ) as output:
            temporary = Path(output.name)
            with source.open("rb") as input_file:
                for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                    output.write(chunk)
        if file_sha256(temporary) != expected:
            raise RecoveryError("source changed during copy; no vintage installed")
        try:
            os.link(temporary, destination)
        except FileExistsError:
            _reject_symlink_components(repo_root, relative)
            if not destination.is_file() or file_sha256(destination) != expected:
                raise RecoveryError("destination appeared with a different SHA-256; refusing overwrite")
            return f"already present and verified: {raw_path} ({expected}); {', '.join(manifests)}"
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return f"copied and verified: {raw_path} ({expected}); {', '.join(manifests)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("relative_vintage_path", help="data/vintages/... path pinned in a committed manifest")
    parser.add_argument("--source-root", type=Path, required=True,
                        help="absolute path to another checkout holding the raw vintage")
    parser.add_argument("--apply", action="store_true", help="copy the single verified file")
    args = parser.parse_args(argv)
    try:
        print(recover(REPO_ROOT, args.source_root, args.relative_vintage_path, apply=args.apply))
    except (RecoveryError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
