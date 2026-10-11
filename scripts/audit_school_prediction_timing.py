#!/usr/bin/env python3
"""Freeze which reciprocal school forecasts preceded each hypothesis's first run.

This is a claim-row score gate. A hypothesis's own pre-registration and public
result do not make a school prediction prospective if the school link or its
reciprocal prediction was added after the result. The output contains no Git
hashes, so it can be regenerated after a public-history rewrite.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ieset-school-prediction-timing-v1"
DEFAULT_OUTPUT = ROOT / "engine" / "school_prediction_timing.json"
RIGHTS_HOLDS = ROOT / "engine" / "publication_rights_holds.json"


def git_yaml(root: Path, revision: str, relative_path: str) -> dict[str, Any] | None:
    proc = subprocess.run(
        ["git", "show", f"{revision}:{relative_path}"],
        cwd=root, capture_output=True, check=False,
    )
    if proc.returncode:
        return None
    try:
        value = yaml.safe_load(proc.stdout)
    except yaml.YAMLError:
        return None
    return value if isinstance(value, dict) else None


def matching_cover(
    doc: dict[str, Any] | None,
    position_id: str,
    claim_index: int,
    prediction: str,
    polarity: str,
) -> bool:
    if not doc:
        return False
    return any(
        isinstance(item, dict)
        and item.get("position_id") == position_id
        and item.get("claim_index") == claim_index
        and item.get("school_prediction") == prediction
        and (item.get("polarity") or "aligned") == polarity
        for item in (doc.get("covers_claims") or [])
    )


def matching_position_claim(
    doc: dict[str, Any] | None,
    claim_index: int,
    current: dict[str, Any],
    prediction: str,
    polarity: str,
) -> bool:
    if not doc:
        return False
    claims = doc.get("falsifiable_specific_claims") or []
    if not isinstance(claims, list) or claim_index >= len(claims):
        return False
    old = claims[claim_index]
    if not isinstance(old, dict):
        return False
    return (
        old.get("linked_hypothesis_id") == current.get("linked_hypothesis_id")
        and old.get("claim") == current.get("claim")
        and old.get("scope") == current.get("scope")
        and old.get("school_prediction") == prediction
        and (old.get("claim_polarity") or "aligned") == polarity
    )


def build_manifest(
    root: Path,
    registrations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    @lru_cache(maxsize=None)
    def historical(revision: str, relative_path: str) -> dict[str, Any] | None:
        return git_yaml(root, revision, relative_path)

    @lru_cache(maxsize=None)
    def current_hypothesis(relative_path: str) -> dict[str, Any] | None:
        try:
            value = yaml.safe_load((root / relative_path).read_text())
        except (OSError, yaml.YAMLError):
            return None
        return value if isinstance(value, dict) else None

    rows: dict[str, dict[str, Any]] = {}
    statuses: Counter[str] = Counter()
    for position_path in sorted((root / "positions").glob("*.yaml")):
        if position_path.name.startswith("_"):
            continue
        position = yaml.safe_load(position_path.read_text()) or {}
        position_id = position.get("position_id") or position_path.stem
        relative_position = position_path.relative_to(root).as_posix()
        for claim_index, claim in enumerate(position.get("falsifiable_specific_claims") or []):
            if not isinstance(claim, dict):
                continue
            hypothesis_id = claim.get("linked_hypothesis_id")
            if not isinstance(hypothesis_id, str) or not hypothesis_id:
                continue
            registration = registrations.get(hypothesis_id) or {}
            relative_hypothesis = registration.get("path")
            hypothesis = (
                current_hypothesis(relative_hypothesis)
                if isinstance(relative_hypothesis, str) else None
            )
            covers = [
                item for item in (hypothesis or {}).get("covers_claims") or []
                if isinstance(item, dict)
                and item.get("position_id") == position_id
                and item.get("claim_index") == claim_index
            ]
            cover = covers[0] if len(covers) == 1 else None
            prediction = (cover or {}).get("school_prediction") or claim.get("school_prediction")
            polarity = (cover or {}).get("polarity") or claim.get("claim_polarity") or "aligned"
            row: dict[str, Any] = {
                "position_id": position_id,
                "claim_index": claim_index,
                "hypothesis_id": hypothesis_id,
                "claim": claim.get("claim"),
                "scope": claim.get("scope"),
                "school_prediction": prediction,
                "polarity": polarity,
                "eligible": False,
            }
            if not cover:
                reason = "missing_current_reciprocal"
            elif registration.get("status") != "verified" or registration.get("verified") is not True:
                reason = "not_strict_registered"
            elif not registration.get("run_first_commit"):
                reason = "no_run"
            else:
                run_parent = registration["run_first_commit"] + "^"
                old_position = historical(run_parent, relative_position)
                old_hypothesis = historical(run_parent, relative_hypothesis)
                position_before = matching_position_claim(
                    old_position, claim_index, claim, prediction, polarity
                )
                reciprocal_before = matching_cover(
                    old_hypothesis, position_id, claim_index, prediction, polarity
                )
                if position_before and reciprocal_before:
                    reason = "prospective_reciprocal"
                    row["eligible"] = True
                elif not position_before and not reciprocal_before:
                    reason = "both_added_or_changed_after_run"
                elif not position_before:
                    reason = "position_added_or_changed_after_run"
                else:
                    reason = "reciprocal_added_or_changed_after_run"
            row["status"] = reason
            key = f"{position_id}#{claim_index}"
            rows[key] = row
            statuses[reason] += 1
    eligible = sorted(
        f"{key}:{row['hypothesis_id']}"
        for key, row in rows.items() if row["eligible"]
    )
    return {
        "schema": SCHEMA,
        "method": (
            "Score only a current claim whose exact index, hypothesis ID, wording, "
            "scope, prediction and polarity appear on the position side, and "
            "whose exact reciprocal prediction appears on the hypothesis side, "
            "in the parent tree of the hypothesis's first run commit. The "
            "hypothesis must also have strict spec-before-run registration."
        ),
        "summary": {
            "linked_claim_rows": len(rows),
            "prospective_reciprocal_claim_rows": len(eligible),
            "statuses": dict(sorted(statuses.items())),
        },
        "eligible_claims": eligible,
        "rows": rows,
    }


def public_held_ids(path: Path = RIGHTS_HOLDS) -> set[str]:
    """Fail closed when making a publicly reachable timing artifact."""
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"missing or unreadable publication rights registry: {path}") from exc
    if (payload.get("schema") != "ieset-publication-rights-holds-v1"
            or payload.get("status") != "active_publication_hold"
            or not isinstance(payload.get("groups"), list)):
        raise ValueError(f"invalid publication rights registry: {path}")
    ids: set[str] = set()
    for group in payload["groups"]:
        if not isinstance(group, dict) or not isinstance(group.get("hypothesis_ids"), list):
            raise ValueError(f"invalid publication rights group: {path}")
        group_ids = group["hypothesis_ids"]
        if (len(group_ids) != group.get("count")
                or any(not isinstance(item, str) or not item for item in group_ids)
                or ids.intersection(group_ids)):
            raise ValueError(f"invalid publication rights IDs: {path}")
        ids.update(group_ids)
    return ids


def public_projection(manifest: dict[str, Any], held_ids: set[str]) -> dict[str, Any]:
    rows = {
        key: row for key, row in manifest["rows"].items()
        if row["hypothesis_id"] not in held_ids
    }
    counts = Counter(row["status"] for row in rows.values())
    eligible = sorted(
        f"{key}:{row['hypothesis_id']}"
        for key, row in rows.items() if row["eligible"]
    )
    projected = {
        **manifest,
        "projection": "public_rights_filtered",
        "summary": {
            "linked_claim_rows": len(rows),
            "prospective_reciprocal_claim_rows": len(eligible),
            "statuses": dict(sorted(counts.items())),
        },
        "eligible_claims": eligible,
        "rows": rows,
    }
    encoded = json.dumps(projected, sort_keys=True)
    if any(hypothesis_id in encoded for hypothesis_id in held_ids):
        raise ValueError("held hypothesis ID remains in public timing artifact")
    return projected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--public", action="store_true", help="omit held IDs from publicly reachable output")
    args = parser.parse_args()
    from check_preregistration import build_index, load_legacy_exceptions, DEFAULT_LEGACY
    index, violations, _ = build_index(load_legacy_exceptions(DEFAULT_LEGACY))
    if violations:
        raise SystemExit(f"registration history has {len(violations)} violation(s)")
    manifest = build_manifest(ROOT, index["registrations"])
    if args.public:
        manifest = public_projection(manifest, public_held_ids())
    encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.check and (not args.out.exists() or args.out.read_text() != encoded):
        raise SystemExit(f"stale school timing manifest: {args.out}")
    if args.write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    print(json.dumps(manifest["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    raise SystemExit(main())
