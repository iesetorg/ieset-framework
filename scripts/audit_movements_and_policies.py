"""Deep audit of movements and policies — beyond schema validation.

Catches: policy-shaped movements that slipped through, near-empty content,
duplicate/overlapping coverage, dangling cross-references, and quality
indicators that scripts/validate_specs.py doesn't cover.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
MOV = REPO / "movements"
POL = REPO / "policies"


POLICY_NAMING = re.compile(
    r"_(act|law|reform|plan|budget|amendment|pact|order|deal|accord|directive|"
    r"programme|program|tax|policy|decree|package|framework|guarantee|repeal|"
    r"launch|abolition|liberalisation|deregulation|nationalisation|"
    r"privatisation|treaty)(_|$)",
    re.I,
)


def load_yaml(p: Path):
    try:
        return yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        return {"_parse_error": str(e)}


def audit_movements():
    files = sorted(MOV.glob("*.yaml"))
    issues = defaultdict(list)
    movements = []
    by_id = {}

    for f in files:
        d = load_yaml(f)
        if d is None or not isinstance(d, dict):
            issues["parse"].append((f.name, "empty or non-dict YAML"))
            continue
        if "_parse_error" in d:
            issues["parse"].append((f.name, d["_parse_error"]))
            continue
        mid = d.get("movement_id")
        if not mid:
            issues["missing_id"].append((f.name, "no movement_id"))
            continue
        if mid in by_id:
            issues["duplicate_id"].append((f.name, f"id {mid} also in {by_id[mid]}"))
            continue
        by_id[mid] = f.name
        movements.append((f, d))

    for f, d in movements:
        mid = d["movement_id"]
        tf = d.get("timeframe") or {}
        start = tf.get("start")
        end = tf.get("end")
        coalition = (d.get("coalition") or "").strip()
        leaders = d.get("leaders") or []
        doctrine = (d.get("doctrine") or "").strip()
        policies = d.get("policies") or []
        axes_summary = d.get("axes_summary") or []

        # Policy-shaped movement — round 2
        if isinstance(start, int) and isinstance(end, int):
            duration = end - start
        elif end == "ongoing" and isinstance(start, int):
            duration = 2026 - start
        else:
            duration = None

        if (
            duration is not None
            and duration <= 1
            and len(policies) <= 1
            and not coalition
            and not leaders
            and POLICY_NAMING.search(mid)
        ):
            issues["policy_shaped"].append((mid, f"dur={duration}, policies={len(policies)}, no coalition/leaders, name matches policy pattern"))

        # Substantive content thresholds
        if len(doctrine) < 60:
            issues["thin_doctrine"].append((mid, f"len={len(doctrine)}"))
        if not policies:
            issues["no_policies"].append((mid, "empty policies list"))
        if len(policies) == 0 and len(axes_summary) == 0:
            issues["no_policies_no_axes"].append((mid, "neither policies nor axes_summary"))
        if not d.get("countries"):
            issues["no_countries"].append((mid, "empty countries list"))
        if not coalition and not leaders:
            issues["no_attribution"].append((mid, "no coalition + no leaders"))

        # Predecessor / successor dangling check
        pol_ids_in_policies_dir = {p.stem for p in POL.glob("*.yaml")}
        mov_ids = set(by_id.keys())

        for key in ("predecessor_movements", "successor_movements"):
            for ref in d.get(key) or []:
                if ref not in mov_ids:
                    issues["dangling_movement_ref"].append((mid, f"{key} → {ref} (not in movements/)"))

        # Movement.policies references that don't exist in policies/
        for pid in policies:
            if pid not in pol_ids_in_policies_dir:
                # Per validator this is a permitted forward-reference at status=candidate;
                # we still flag for visibility.
                issues["forward_policy_ref"].append((mid, pid))

        # axes_summary entries with magnitude/direction violations
        for entry in axes_summary:
            if entry.get("direction") not in {"+", "-", "0", "mixed"}:
                issues["bad_direction"].append((mid, f"axis={entry.get('axis')} direction={entry.get('direction')!r}"))

    return movements, issues, by_id


def audit_policies():
    files = sorted(POL.glob("*.yaml"))
    issues = defaultdict(list)
    policies = []
    by_id = {}

    for f in files:
        d = load_yaml(f)
        if not isinstance(d, dict) or "_parse_error" in d:
            issues["parse"].append((f.name, str(d.get("_parse_error", "non-dict"))))
            continue
        pid = d.get("policy_id")
        if not pid:
            issues["missing_id"].append((f.name, "no policy_id"))
            continue
        if pid in by_id:
            issues["duplicate_id"].append((f.name, f"id {pid} also in {by_id[pid]}"))
            continue
        by_id[pid] = f.name
        policies.append((f, d))

    for f, d in policies:
        pid = d["policy_id"]
        title = (d.get("title") or "").strip()
        countries = d.get("countries") or []
        description = (d.get("description") or "").strip()
        axes_moved = d.get("axes_moved") or []
        enacted_by = d.get("enacted_by") or []

        if len(title) < 6:
            issues["short_title"].append((pid, f"len={len(title)}"))
        if len(description) < 80:
            issues["thin_description"].append((pid, f"len={len(description)}"))
        if not axes_moved:
            issues["no_axes_moved"].append((pid, "empty axes_moved"))
        for entry in axes_moved:
            # Policy schema accepts +/-/0/mixed (mixed = bundled reform with
            # both directions in the same axis). Only flag truly invalid
            # direction tokens.
            if entry.get("direction") not in {"+", "-", "0", "mixed"}:
                issues["bad_policy_direction"].append((pid, f"axis={entry.get('axis')} direction={entry.get('direction')!r}"))
        if not countries:
            issues["no_countries"].append((pid, "empty countries"))

    return policies, issues, by_id


def main():
    print("=" * 70)
    print("MOVEMENTS AUDIT")
    print("=" * 70)
    movements, mov_issues, mov_ids = audit_movements()
    print(f"\nTotal movements: {len(movements)}")
    for category, items in sorted(mov_issues.items()):
        print(f"\n[{category}] {len(items)} issues")
        for mid, msg in items[:15]:
            print(f"  {mid:<60}  {msg}")
        if len(items) > 15:
            print(f"  ... and {len(items) - 15} more")

    print()
    print("=" * 70)
    print("POLICIES AUDIT")
    print("=" * 70)
    policies, pol_issues, pol_ids = audit_policies()
    print(f"\nTotal policies: {len(policies)}")
    for category, items in sorted(pol_issues.items()):
        print(f"\n[{category}] {len(items)} issues")
        for pid, msg in items[:15]:
            print(f"  {pid:<60}  {msg}")
        if len(items) > 15:
            print(f"  ... and {len(items) - 15} more")

    print()
    print("=" * 70)
    print("CROSS-REFERENCE AUDIT")
    print("=" * 70)
    # Policy.enacted_by → movement_ids that exist
    dangling = []
    for f, d in policies:
        for ref in d.get("enacted_by") or []:
            if ref not in mov_ids:
                dangling.append((d["policy_id"], ref))
    print(f"\nPolicy.enacted_by → movement that doesn't exist: {len(dangling)} cases")
    for pid, ref in dangling[:30]:
        print(f"  {pid:<60}  → {ref}")
    if len(dangling) > 30:
        print(f"  ... and {len(dangling) - 30} more")

    # Movement.policies → policy that doesn't exist
    forward_refs = mov_issues.get("forward_policy_ref", [])
    print(f"\nMovement.policies → forward-ref policy (not yet created): {len(forward_refs)} cases")

    # Total error count
    severity_a = sum(len(v) for k, v in mov_issues.items() if k in {"parse", "missing_id", "duplicate_id", "bad_direction", "policy_shaped"})
    severity_a += sum(len(v) for k, v in pol_issues.items() if k in {"parse", "missing_id", "duplicate_id", "bad_policy_direction"})
    severity_b = sum(len(v) for k, v in mov_issues.items() if k in {"thin_doctrine", "no_policies", "no_attribution", "no_countries", "dangling_movement_ref"})
    severity_b += sum(len(v) for k, v in pol_issues.items() if k in {"thin_description", "short_title", "no_axes_moved", "no_countries"})
    severity_b += len(dangling)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Critical (broken): {severity_a}")
    print(f"  Quality (thin/dangling): {severity_b}")
    print(f"  Forward refs (permitted but worth tracking): {len(forward_refs)}")


if __name__ == "__main__":
    main()
