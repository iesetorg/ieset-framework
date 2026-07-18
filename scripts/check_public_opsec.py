#!/usr/bin/env python3
"""Reject non-research files, local paths, personal metadata, and secrets."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NON_RESEARCH_BASENAMES = {
    "STRATEGY.md",
    "GROWTH_PLAN_v1.md",
    "FRONTEND_DESIGN.md",
}
NON_RESEARCH_PATH_PATTERNS = (
    re.compile(r"^HANDOFF_TO_.*\.md$"),
)
CONTENT_PATTERNS = {
    "macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+"),
    "Windows home path": re.compile(
        r"[A-Za-z]:\\+Users\\+[A-Za-z0-9._-]+", re.IGNORECASE
    ),
    "local-domain email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.local\b", re.IGNORECASE
    ),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
ALLOWED_CONTENT_FILES = {".gitignore", "scripts/check_public_opsec.py"}
ALLOWED_COMMIT_IDENTITIES = {
    ("iesetorg", "iesetorg@users.noreply.github.com"),
    ("IESET", "iesetorg@users.noreply.github.com"),
    ("IESET", "institute@ieset.dev"),
}


def command(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        capture_output=True,
        check=True,
    )


def tracked_paths() -> list[str]:
    output = command("git", "ls-files", "-z").stdout
    return sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in output.split(b"\0")
        if item
    )


def non_research_path(path: str) -> bool:
    return (
        path in NON_RESEARCH_BASENAMES
        or any(pattern.match(path) for pattern in NON_RESEARCH_PATH_PATTERNS)
    )


def scan_tree() -> list[str]:
    findings: list[str] = []
    for path in tracked_paths():
        if non_research_path(path):
            findings.append(f"{path}: non-research path is tracked")
            continue
        if path in ALLOWED_CONTENT_FILES:
            continue
        try:
            raw = (ROOT / path).read_bytes()
        except OSError as exc:
            findings.append(f"{path}: cannot read tracked file: {exc}")
            continue
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        for label, pattern in CONTENT_PATTERNS.items():
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path}:{line}: {label}")
    return findings


def scan_history() -> list[str]:
    output = command(
        "git",
        "log",
        "--format=%H%x09%an%x09%ae%x09%cn%x09%ce",
        "HEAD",
    ).stdout.decode("utf-8", errors="replace")
    findings = []
    for line in output.splitlines():
        commit, author, author_email, committer, committer_email = line.split("\t")
        identities = {
            (author, author_email),
            (committer, committer_email),
        }
        blocked = identities - ALLOWED_COMMIT_IDENTITIES
        if blocked:
            findings.append(f"commit {commit[:12]}: non-institutional metadata")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tree-only",
        action="store_true",
        help="Skip commit-author history (use only while preparing a rewrite).",
    )
    args = parser.parse_args()
    findings = scan_tree()
    if not args.tree_only:
        findings.extend(scan_history())
    if findings:
        print(f"FAIL: {len(findings)} public OPSEC finding(s):", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1
    scope = "public tree" if args.tree_only else "public tree and commit metadata"
    print(f"OK ({scope} contain no blocked OPSEC markers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
