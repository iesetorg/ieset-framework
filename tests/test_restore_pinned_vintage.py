"""Single-file recovery must trust committed hashes and leave raw data ignored."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "restore_pinned_vintage.py"
SPEC = importlib.util.spec_from_file_location("restore_pinned_vintage", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
RecoveryError = MODULE.RecoveryError
recover = MODULE.recover
vintage_relative_path = MODULE.vintage_relative_path


VINTAGE = "data/vintages/example/series@2026-01-01T000000Z.parquet"
RAW = b"small pinned fixture, not a real observation\n"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _fixture(tmp_path: Path, *, shape: str = "entries") -> tuple[Path, Path, Path]:
    destination_root = tmp_path / "destination"
    source_root = tmp_path / "source"
    destination_root.mkdir()
    source = source_root / VINTAGE
    source.parent.mkdir(parents=True)
    source.write_bytes(RAW)
    digest = hashlib.sha256(RAW).hexdigest()

    _git(destination_root, "init", "-q")
    _git(destination_root, "config", "user.name", "Fixture")
    _git(destination_root, "config", "user.email", "fixture@example.invalid")
    (destination_root / ".gitignore").write_text("/data/vintages/\n")
    if shape == "cases":
        manifest = destination_root / "scripts" / "frozen_source_vintages.json"
        manifest.parent.mkdir()
        manifest.write_text(json.dumps({"cases": {"case": [{"path": VINTAGE, "sha256": digest}]}}))
    else:
        manifest = destination_root / "data" / "manifests" / "fetch_run_fixture.yaml"
        manifest.parent.mkdir(parents=True)
        if shape == "entries":
            doc = {"entries": [{"parquet_path": VINTAGE, "sha256": digest}]}
        else:
            doc = {"source_vintage": {"path": VINTAGE, "sha256": digest}}
        manifest.write_text(yaml.safe_dump(doc))
    _git(destination_root, "add", ".gitignore", str(manifest.relative_to(destination_root)))
    _git(destination_root, "commit", "-qm", "Pin test vintage")
    return destination_root, source_root, manifest


@pytest.mark.parametrize("shape", ["entries", "source_vintage", "cases"])
def test_dry_run_then_copy_then_idempotent(tmp_path: Path, shape: str) -> None:
    destination_root, source_root, _ = _fixture(tmp_path, shape=shape)
    destination = destination_root / VINTAGE
    assert "dry run; would copy" in recover(destination_root, source_root, VINTAGE)
    assert not destination.exists()
    assert "copied and verified" in recover(destination_root, source_root, VINTAGE, apply=True)
    assert destination.read_bytes() == RAW
    assert "already present and verified" in recover(destination_root, source_root, VINTAGE, apply=True)


@pytest.mark.parametrize("unsafe", [
    "/data/vintages/example/a.parquet",
    "../data/vintages/example/a.parquet",
    "data/vintages/../secret.parquet",
    "data/vintages/example//a.parquet",
    "data\\vintages\\example\\a.parquet",
    "data/vintages/example/./a.parquet",
    "data/vintages/example/a\n.parquet",
    "data/vintages",
])
def test_rejects_unsafe_paths(unsafe: str) -> None:
    with pytest.raises(RecoveryError):
        vintage_relative_path(unsafe)


def test_source_hash_mismatch_refuses_copy(tmp_path: Path) -> None:
    destination_root, source_root, _ = _fixture(tmp_path)
    (source_root / VINTAGE).write_bytes(b"changed")
    with pytest.raises(RecoveryError, match="source vintage SHA-256"):
        recover(destination_root, source_root, VINTAGE, apply=True)
    assert not (destination_root / VINTAGE).exists()


def test_destination_hash_mismatch_refuses_overwrite(tmp_path: Path) -> None:
    destination_root, source_root, _ = _fixture(tmp_path)
    destination = destination_root / VINTAGE
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"do not replace")
    with pytest.raises(RecoveryError, match="refusing overwrite"):
        recover(destination_root, source_root, VINTAGE, apply=True)
    assert destination.read_bytes() == b"do not replace"


def test_uses_committed_manifest_not_worktree_edit(tmp_path: Path) -> None:
    destination_root, source_root, manifest = _fixture(tmp_path)
    doc = yaml.safe_load(manifest.read_text())
    doc["entries"][0]["sha256"] = "0" * 64
    manifest.write_text(yaml.safe_dump(doc))
    assert "dry run; would copy" in recover(destination_root, source_root, VINTAGE)


def test_untracked_manifest_is_not_a_pin(tmp_path: Path) -> None:
    destination_root, source_root, _ = _fixture(tmp_path)
    other = "data/vintages/example/other.parquet"
    (source_root / other).write_bytes(RAW)
    untracked = destination_root / "data" / "manifests" / "fetch_run_untracked.yaml"
    untracked.write_text(yaml.safe_dump({"entries": [{
        "parquet_path": other, "sha256": hashlib.sha256(RAW).hexdigest(),
    }]}))
    with pytest.raises(RecoveryError, match="no SHA-256 pin"):
        recover(destination_root, source_root, other)


def test_conflicting_committed_pins_fail_closed(tmp_path: Path) -> None:
    destination_root, source_root, _ = _fixture(tmp_path)
    second = destination_root / "data" / "manifests" / "fetch_run_conflict.yaml"
    second.write_text(yaml.safe_dump({"source_vintage": {
        "path": VINTAGE, "sha256": "0" * 64,
    }}))
    _git(destination_root, "add", str(second.relative_to(destination_root)))
    _git(destination_root, "commit", "-qm", "Conflicting pin")
    with pytest.raises(RecoveryError, match="conflicting SHA-256"):
        recover(destination_root, source_root, VINTAGE)


def test_rejects_symlink_escape_and_nonignored_target(tmp_path: Path) -> None:
    destination_root, source_root, _ = _fixture(tmp_path)
    (destination_root / "data").mkdir(exist_ok=True)
    (destination_root / "data" / "vintages").symlink_to(source_root / "data" / "vintages")
    with pytest.raises(RecoveryError, match="symlink"):
        recover(destination_root, source_root, VINTAGE, apply=True)

    (destination_root / "data" / "vintages").unlink()
    (destination_root / ".gitignore").write_text("")
    with pytest.raises(RecoveryError, match="not Git-ignored"):
        recover(destination_root, source_root, VINTAGE, apply=True)
