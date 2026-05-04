#!/usr/bin/env python3
"""Validate every hypothesis, condition, position, policy, movement, axes, and publisher YAML
against its JSON Schema, plus cross-reference axis ids and content-type references.

Usage:
    python scripts/validate_specs.py

Exits non-zero on any validation failure. Intended for CI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError:
    print("ERROR: install dependencies: pip install pyyaml jsonschema referencing", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def build_schema_registry() -> Registry:
    """Build a referencing Registry from every *.schema.json in SCHEMAS so
    cross-schema $refs (e.g. position.schema.json -> hypothesis.schema.json#/$defs/scope)
    resolve against local files instead of being fetched over HTTP.

    Each schema is registered under both its declared $id and its bare filename,
    so both `https://ieset.dev/schemas/hypothesis.schema.json` and the relative
    `hypothesis.schema.json` resolve.
    """
    resources: list[tuple[str, Resource]] = []
    for p in sorted(SCHEMAS.glob("*.schema.json")):
        schema = load_schema(p)
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        if "$id" in schema:
            resources.append((schema["$id"], resource))
        # Also register by bare filename so relative refs like "hypothesis.schema.json"
        # work even when the referrer doesn't share a base URI.
        resources.append((p.name, resource))
    return Registry().with_resources(resources)


def load_yaml(path: Path) -> dict | None:
    with path.open() as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError:
            return None


def validate_one(path: Path, validator: Draft202012Validator) -> list[str]:
    with path.open() as f:
        try:
            doc = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return [f"{path.relative_to(ROOT)}: YAML parse error: {e}"]
    if doc is None:
        return [f"{path.relative_to(ROOT)}: empty YAML document"]
    errors = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: tuple(str(p) for p in e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"{path.relative_to(ROOT)}: at {loc}: {err.message}")
    return errors


def load_axis_ids() -> set[str]:
    axes_path = ROOT / "axes.yaml"
    if not axes_path.exists():
        return set()
    doc = load_yaml(axes_path) or {}
    return {a["id"] for a in doc.get("axes", []) if "id" in a}


def cross_ref_axes(valid_axis_ids: set[str]) -> list[str]:
    """Every axis referenced in any policy/movement must exist in axes.yaml."""
    errors: list[str] = []
    for kind, d in (("policy", ROOT / "policies"), ("movement", ROOT / "movements")):
        if not d.exists():
            continue
        for yml in (y for y in d.glob("*.yaml") if not y.name.startswith("_")):
            doc = load_yaml(yml) or {}
            entries = doc.get("axes_moved") or doc.get("axes_summary") or []
            for e in entries:
                axis_id = e.get("axis") if isinstance(e, dict) else None
                if axis_id and axis_id not in valid_axis_ids:
                    errors.append(
                        f"{yml.relative_to(ROOT)}: axis {axis_id!r} not defined in axes.yaml"
                    )
    return errors


_STUB_RULE_MARKER = "when this stub is promoted from draft"


def integrity_check_falsification_rules() -> list[str]:
    """Fail when a hypothesis carries the stub-promotion boilerplate falsification
    rule AND a real verdict has been emitted in diagnostics.json. That combination
    means the auto-grader scored against a generic 'p<0.10 + correct sign' rule
    rather than against a dispositive pre-registered threshold a fair reader of
    the claim would defend — the integrity-failure mode that hit the pre-launch
    audit (post-mortem in commit bba6f644).

    Three legitimate states are still allowed:
      (1) Stub rule + no run yet: the spec is a draft. Fine.
      (2) Stub rule + run with verdict starting 'inconclusive_data_pending' or
          'blocked' — the runner declined to grade. Fine.
      (3) Sharpened rule + run with verdict — the canonical good state. Fine.
      (4) Stub rule field + methodology_note documenting the dispositive
          sharpening — acceptable upgrade-path state. Fine.

    The forbidden state is: stub rule + a verdict-bearing run + no methodology
    note explaining the sharpening. That's what this check catches.
    """
    import json
    errors: list[str] = []
    hyp_dir = ROOT / "hypotheses"
    if not hyp_dir.is_dir():
        return errors
    for yml in hyp_dir.rglob("*.yaml"):
        if yml.name.startswith("_") or "steelman" in yml.parts:
            continue
        doc = load_yaml(yml) or {}
        rule = ((doc.get("falsification") or {}).get("rule") or "").lower()
        if _STUB_RULE_MARKER not in rule:
            continue
        hid = doc.get("hypothesis_id")
        if not hid:
            continue
        mn = (doc.get("methodology_note") or "").lower()
        if any(k in mn for k in ("dispositive", "sharpened", "primary (dispositive")):
            continue
        diag = ROOT / "engine" / "runs" / hid / "diagnostics.json"
        if not diag.exists():
            continue
        try:
            d = json.loads(diag.read_text())
        except Exception:
            continue
        verdict = (d.get("verdict") or "").strip().lower()
        if not verdict:
            continue
        if verdict.startswith(("inconclusive", "blocked", "error", "no verdict")):
            continue
        rel = yml.relative_to(ROOT)
        errors.append(
            f"{rel}: hypothesis_id '{hid}' has STUB falsification rule "
            f"('…when this stub is promoted from draft') but diagnostics.json "
            f"carries a verdict ({verdict[:60]}…). Either sharpen the YAML rule, "
            f"document the sharpening in methodology_note, or remove the run."
        )
    return errors


def cross_ref_policies(known_policy_ids: set[str]) -> tuple[list[str], list[str]]:
    """Every policy_id referenced by a canonical movement.policies must exist.
    Candidate/draft movements can forward-reference policy_ids not yet materialised
    (those surface as warnings, not errors, so corpus-mined drafts don't block CI).
    Returns (hard_errors, soft_warnings).
    """
    hard_errors: list[str] = []
    warnings: list[str] = []
    d = ROOT / "movements"
    if not d.exists():
        return hard_errors, warnings
    for yml in d.glob("*.yaml"):
        doc = load_yaml(yml) or {}
        status = doc.get("status", "draft")
        for pid in doc.get("policies") or []:
            if pid not in known_policy_ids:
                msg = f"{yml.relative_to(ROOT)}: policy_id {pid!r} has no matching policies/*.yaml"
                if status == "canonical":
                    hard_errors.append(msg)
                else:
                    warnings.append(msg + f" [status={status}, forward-reference permitted]")
    return hard_errors, warnings


def main() -> int:
    registry = build_schema_registry()
    def _v(name: str) -> Draft202012Validator:
        return Draft202012Validator(load_schema(SCHEMAS / name), registry=registry)

    hyp_v      = _v("hypothesis.schema.json")
    cond_v     = _v("condition.schema.json")
    pos_v      = _v("position.schema.json")
    pub_v      = _v("publishers.schema.json")
    axes_v     = _v("axes.schema.json")
    policy_v   = _v("policy.schema.json")
    movement_v = _v("movement.schema.json")

    errors: list[str] = []
    checked = 0

    # Hypotheses — scan every subdir of hypotheses/ except conditional_taxonomy (different schema) and steelman (markdown only)
    hyp_root = ROOT / "hypotheses"
    if hyp_root.exists():
        for topic_dir in sorted(p for p in hyp_root.iterdir() if p.is_dir() and p.name not in ("conditional_taxonomy", "steelman")):
            for yml in (y for y in topic_dir.glob("*.yaml") if not y.name.startswith("_")):
                checked += 1
                errors.extend(validate_one(yml, hyp_v))

    # Conditions
    d = ROOT / "hypotheses" / "conditional_taxonomy"
    if d.exists():
        for yml in (y for y in d.glob("*.yaml") if not y.name.startswith("_")):
            checked += 1
            errors.extend(validate_one(yml, cond_v))

    # Positions
    d = ROOT / "positions"
    if d.exists():
        for yml in (y for y in d.glob("*.yaml") if not y.name.startswith("_")):
            checked += 1
            errors.extend(validate_one(yml, pos_v))

    # Publishers
    pub_path = ROOT / "data" / "fetchers" / "publishers.yaml"
    if pub_path.exists():
        checked += 1
        errors.extend(validate_one(pub_path, pub_v))

    # Axes registry
    axes_path = ROOT / "axes.yaml"
    if axes_path.exists():
        checked += 1
        errors.extend(validate_one(axes_path, axes_v))

    # Policies
    known_policy_ids: set[str] = set()
    d = ROOT / "policies"
    if d.exists():
        for yml in (y for y in d.glob("*.yaml") if not y.name.startswith("_")):
            checked += 1
            errors.extend(validate_one(yml, policy_v))
            doc = load_yaml(yml) or {}
            if "policy_id" in doc:
                known_policy_ids.add(doc["policy_id"])

    # Movements
    d = ROOT / "movements"
    if d.exists():
        for yml in (y for y in d.glob("*.yaml") if not y.name.startswith("_")):
            checked += 1
            errors.extend(validate_one(yml, movement_v))

    # Cross-references
    axis_ids = load_axis_ids()
    if axis_ids:
        errors.extend(cross_ref_axes(axis_ids))
    policy_errors, policy_warnings = cross_ref_policies(known_policy_ids)
    errors.extend(policy_errors)

    # Integrity gate: stub falsification rule + real verdict is forbidden.
    # See integrity_check_falsification_rules() for the rationale + exit states.
    errors.extend(integrity_check_falsification_rules())

    if policy_warnings:
        print(f"WARN ({len(policy_warnings)} unresolved policy forward-references):")
        for w in policy_warnings:
            print(f"  {w}")

    if errors:
        print(f"FAIL ({len(errors)} error(s) across {checked} file(s)):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK ({checked} spec file(s) validated + cross-references clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
