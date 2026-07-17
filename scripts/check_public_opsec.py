#!/usr/bin/env python3
"""Reject private control-plane files, local paths, PII markers, and secrets."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PATHS = (
    "engine/brain/",
    "engine/agent_briefs/",
    "debate/",
)
PRIVATE_BASENAMES = {
    "STRATEGY.md",
    "GROWTH_PLAN_v1.md",
    "FRONTEND_DESIGN.md",
}
PRIVATE_PATH_PATTERNS = (
    re.compile(r"^HANDOFF_TO_.*\.md$"),
    re.compile(r"^schemas/brain_.*\.schema\.json$"),
    re.compile(r"^scripts/.*brain.*$"),
    re.compile(r"^tests/test_brain.*\.py$"),
)
PRIVATE_IDENTITY_MARKERS = (
    "duncan" + "campbell",
    "Duncan " + "Campbell",
    "Locals-" + "Mac-Studio",
    "localllm" + "@",
    "big" + "destiny2",
)
PRIVATE_IDENTITY_PATTERN = "|".join(
    re.escape(marker) for marker in PRIVATE_IDENTITY_MARKERS
)
CONTENT_PATTERNS = {
    "macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+"),
    "Windows home path": re.compile(
        r"[A-Za-z]:\\+Users\\+[A-Za-z0-9._-]+", re.IGNORECASE
    ),
    "private identity marker": re.compile(PRIVATE_IDENTITY_PATTERN, re.IGNORECASE),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
ALLOWED_CONTENT_FILES = {".gitignore", "scripts/check_public_opsec.py"}
HISTORY_PATTERN = re.compile(
    rf"(?:{PRIVATE_IDENTITY_PATTERN}|<[^>]+\.local>)", re.IGNORECASE
)


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


def private_path(path: str) -> bool:
    return (
        path in PRIVATE_BASENAMES
        or path.startswith(PRIVATE_PATHS)
        or any(pattern.match(path) for pattern in PRIVATE_PATH_PATTERNS)
    )


def scan_tree() -> list[str]:
    findings: list[str] = []
    for path in tracked_paths():
        if private_path(path):
            findings.append(f"{path}: private control-plane path is tracked")
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
        "--format=%H%x09%an <%ae>%x09%cn <%ce>",
        "HEAD",
    ).stdout.decode("utf-8", errors="replace")
    findings = []
    for line in output.splitlines():
        if HISTORY_PATTERN.search(line):
            findings.append(
                f"commit {line.split(chr(9), 1)[0][:12]}: private author metadata"
            )
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
