#!/usr/bin/env python3
"""Replay the frozen Korea–EU result after an audit-plan path redaction.

This adapter changes no research input, estimator, threshold, or run artifact.
It permits only a fixed substitution of a local home-directory prefix in the
registered prose source plan, while proving every other registered byte is
unchanged from its first-addition commit.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_korea_eu_fta_eu5_baci_2026.py"
spec = importlib.util.spec_from_file_location("frozen_korea_eu_fta", RUNNER)
assert spec is not None and spec.loader is not None
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


def registered_with_path_only_redaction() -> str:
    additions = [frozen.first_addition(path) for path in frozen.REGISTRATION_FILES]
    if len(set(additions)) != 1:
        raise RuntimeError("registered files did not first enter together")
    commit = additions[0]
    for relative in frozen.REGISTRATION_FILES:
        historical = frozen.git_bytes(commit, relative)
        current = (ROOT / relative).read_bytes()
        if current != frozen.git_bytes("HEAD", relative):
            raise RuntimeError(f"uncommitted registered file: {relative}")
        if relative == frozen.PLAN_REL:
            sanitized, replacements = re.subn(
                rb"/Users/[A-Za-z0-9._-]+/IESET/",
                b"<local-corpus>/",
                historical,
            )
            if replacements != 1 or current != sanitized:
                raise RuntimeError("source plan differs beyond the one local-path redaction")
        elif current != historical:
            raise RuntimeError(f"frozen registered bytes changed: {relative}")
    for relative in (frozen.SLICE_REL, frozen.SOURCE_MANIFEST_REL):
        if frozen.git("ls-tree", "-r", "--name-only", commit, "--", relative).stdout.strip():
            raise RuntimeError("source values appeared in registration commit")
    if frozen.git("ls-tree", "-r", "--name-only", commit, "--", frozen.RUN_REL).stdout.strip():
        raise RuntimeError("result appeared in registration commit")
    if subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                      cwd=ROOT).returncode != 0:
        raise RuntimeError("registration is not an ancestor of HEAD")
    return commit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path)
    args = parser.parse_args()
    frozen.registration_commit = registered_with_path_only_redaction
    frozen.run(verify=True)
    if args.source_zip is not None:
        frozen.verify_source(args.source_zip)


if __name__ == "__main__":
    main()
