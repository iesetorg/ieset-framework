#!/usr/bin/env python3
"""Shared helpers for run-level replication wrappers.

Generated wrappers delegate back to the canonical methodology runner recorded in
`diagnostics.json`. This keeps estimation and verdict logic in one place while
making each archived run directly reproducible from its run directory.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root_from(wrapper_file: str | Path) -> Path:
    return Path(wrapper_file).resolve().parents[3]


def rerun(wrapper_file: str | Path, hypothesis_id: str, runner: str) -> int:
    repo_root = repo_root_from(wrapper_file)
    runner_path = repo_root / runner
    if not runner_path.exists():
        print(f"Replication runner not found: {runner_path}", file=sys.stderr)
        return 1

    cmd = [sys.executable, str(runner_path), hypothesis_id, "--force"]
    print("Replicating", hypothesis_id)
    print("Runner:", runner)
    return subprocess.call(cmd, cwd=repo_root)
