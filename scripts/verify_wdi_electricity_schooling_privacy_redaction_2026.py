#!/usr/bin/env python3
"""Replay the frozen schooling family after one exact PLAN path redaction.

The registered runner remains byte-identical. Only the two occurrences of a
machine-specific source-root token in the PLAN may differ from registration.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_wdi_electricity_schooling_forward_2026.py"
PLAN = "engine/audits/wdi_electricity_schooling_forward_prereg_2026-10-10.md"
REGISTRATION = "f732b27912c1ba92e741ec199ddf516574e1b4d4"
SOURCE_LOCK = "fce4b12e2e36d2144cbe43f1366035fe636320d2"
RESULT = "99db213809d13e5536e752c0722c4acd52f387cb"
REGISTERED_PLAN_SHA = "ad243eb4515d7298e51c71c187fe76ce8d2a0b0dc06b4b80d73dfa8392c4b48c"
ORIGINAL_TOKEN_SHA = "163ed1f8066099a828029cbe52ba33ee2a547469b165adc6b463e224be441b97"
REDACTED_PLAN_SHA = "66742e312ca3e46f1877a70fcb51ee4094b783663d2ec2a3beb16b5887c2db07"
REDACTION = b"<local-source-checkout>"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def strict_redacted_image(registered: bytes) -> bytes:
    """Construct the sole permitted PLAN image without storing the private token."""
    if sha(registered) != REGISTERED_PLAN_SHA:
        raise RuntimeError("registered PLAN bytes differ from the pinned hash")
    tokens = re.findall(rb"(?<=--source-root )/[^` ]+", registered)
    if len(tokens) != 2 or tokens[0] != tokens[1] or sha(tokens[0]) != ORIGINAL_TOKEN_SHA:
        raise RuntimeError("registered PLAN has unexpected machine path tokens")
    redacted = registered.replace(tokens[0], REDACTION)
    if sha(redacted) != REDACTED_PLAN_SHA:
        raise RuntimeError("redacted PLAN image differs from the pinned hash")
    return redacted


def attest_plan() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", RESULT, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("frozen measured result commit is not an ancestor")
    original = git("show", f"{REGISTRATION}:{PLAN}")
    current = (ROOT / PLAN).read_bytes()
    if current != strict_redacted_image(original):
        raise RuntimeError("PLAN differs beyond the two permitted path redactions")
    if git("show", f"HEAD:{PLAN}") != current or git("status", "--porcelain", "--", PLAN).strip():
        raise RuntimeError("redacted PLAN must be committed and clean")


def attest_result_artifacts(frozen: object) -> None:
    paths = [frozen.SUMMARY]
    paths.extend(f"{frozen.run_rel(key)}/{artifact}"
                 for key in frozen.CASES for artifact in frozen.ARTIFACTS)
    for path in paths:
        current = (ROOT / path).read_bytes()
        if git("show", f"{RESULT}:{path}") != current:
            raise RuntimeError(f"measured artifact changed after its result commit: {path}")
        if git("status", "--porcelain", "--", path).strip():
            raise RuntimeError(f"measured artifact has uncommitted changes: {path}")


def load_frozen_runner():
    spec = importlib.util.spec_from_file_location("frozen_electricity_schooling", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load registered runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.RUNNER != str(RUNNER.relative_to(ROOT)) or module.PLAN != PLAN:
        raise RuntimeError("unexpected frozen runner identity")
    return module


def verify(source_root: Path) -> None:
    attest_plan()
    frozen = load_frozen_runner()
    original_check = frozen.committed_original

    def strictly_attested_original(path: str, revision: str) -> None:
        if path == PLAN:
            if revision != REGISTRATION:
                raise RuntimeError("unexpected PLAN registration revision")
            attest_plan()
        else:
            original_check(path, revision)

    frozen.committed_original = strictly_attested_original
    if frozen.registration_commit() != REGISTRATION:
        raise RuntimeError("registration commit identity changed")
    payload, registration, locked = frozen.verified_lock()
    if registration != REGISTRATION or locked != SOURCE_LOCK:
        raise RuntimeError("source-lock chronology changed")
    attest_result_artifacts(frozen)
    frozen.verify_source(source_root)
    frozen.run_or_verify(True)
    print("Exact privacy redaction attested; original frozen source and results replayed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Local checkout holding the exact pinned raw vintages")
    args = parser.parse_args()
    verify(args.source_root)


if __name__ == "__main__":
    main()
