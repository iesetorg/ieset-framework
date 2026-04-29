#!/usr/bin/env python3
"""Phase 2 scope-alignment validator.

Reads every position claim's `scope:` block and compares it against the
linked hypothesis's `scope:` block. Rejects links with zero overlap on any
REQUIRED axis (period, countries, outcome_dim) or with treatment_tags that
disagree.

Usage:
    scripts/validate_scope_alignment.py           # exit 1 on any ERROR
    scripts/validate_scope_alignment.py --strict  # also exit 1 on WARN
    scripts/validate_scope_alignment.py --summary # print counts, don't list

Scope block (see schemas/hypothesis.schema.json#/$defs/scope):
    period:          [start, end]  int years, inclusive
    countries:       ISO3 list + group tokens
    outcome_dim:     controlled-vocab list
    policy_family:   optional
    treatment_tags:  optional snake_case list

Group-token expansion:
    GLOBAL     → match anything
    OECD       → USA GBR DEU FRA ITA ESP NLD BEL AUT SWE NOR DNK FIN IRL CHE
                 GRC PRT LUX ISL AUS NZL JPN KOR MEX TUR ISR EST LVA LTU POL
                 HUN CZE SVK SVN CHL COL CRI
    LATAM      → ARG BRA CHL COL PER URY VEN ECU BOL MEX CRI GTM HND NIC PAN DOM SLV PRY
    EU         → DEU FRA ITA ESP NLD BEL AUT SWE DNK FIN IRL GRC PRT LUX
                 POL HUN CZE SVK SVN EST LVA LTU BGR ROU HRV CYP MLT
    EUROZONE   → subset of EU with euro currency
    ASIA_EM    → CHN IND VNM IDN MYS THA PHL BGD LKA KHM MMR PAK NPL
    AFRICA     → NGA KEN ZAF ETH GHA TZA UGA SEN CIV ZMB ZWE AGO MAR EGY DZA
    MENA       → EGY MAR DZA TUN SDN IRN IRQ SAU TUR ARE ISR JOR LBN SYR YEM
    POST_SOVIET → RUS UKR BLR KAZ UZB KGZ TJK TKM AZE ARM GEO MDA LTU LVA EST
    NORDIC     → SWE NOR DNK FIN ISL
    SOUTHERN_EUROPE → ITA ESP PRT GRC
    ANGLO      → USA GBR CAN AUS NZL IRL

Rules:
    ERROR — zero overlap on period
    ERROR — zero overlap on countries (after group expansion)
    ERROR — zero overlap on outcome_dim
    ERROR — claim has treatment_tags, hypothesis has treatment_tags, and
            their intersection is empty
    WARN  — one side missing scope block entirely (legacy row)
    WARN  — policy_family disjoint (informational, not blocking)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSITIONS_DIR = ROOT / "positions"
HYPOTHESES_DIR = ROOT / "hypotheses"
AUDIT_DIR = ROOT / "engine" / "audits"


# ---------------------------------------------------------------------------
# Group-token expansion
# ---------------------------------------------------------------------------
GROUPS: dict[str, set[str]] = {
    "OECD": {
        "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT",
        "SWE", "NOR", "DNK", "FIN", "IRL", "CHE", "GRC", "PRT", "LUX",
        "ISL", "AUS", "NZL", "JPN", "KOR", "MEX", "TUR", "ISR", "EST",
        "LVA", "LTU", "POL", "HUN", "CZE", "SVK", "SVN", "CHL", "COL",
        "CRI", "CAN",
    },
    "LATAM": {
        "ARG", "BRA", "CHL", "COL", "PER", "URY", "VEN", "ECU", "BOL",
        "MEX", "CRI", "GTM", "HND", "NIC", "PAN", "DOM", "SLV", "PRY",
    },
    "EU": {
        "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "SWE", "DNK",
        "FIN", "IRL", "GRC", "PRT", "LUX", "POL", "HUN", "CZE", "SVK",
        "SVN", "EST", "LVA", "LTU", "BGR", "ROU", "HRV", "CYP", "MLT",
    },
    "EUROZONE": {
        "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "FIN", "IRL",
        "GRC", "PRT", "LUX", "SVK", "SVN", "EST", "LVA", "LTU", "CYP", "MLT",
    },
    "ASIA_EM": {
        "CHN", "IND", "VNM", "IDN", "MYS", "THA", "PHL", "BGD", "LKA",
        "KHM", "MMR", "PAK", "NPL",
    },
    "AFRICA": {
        "NGA", "KEN", "ZAF", "ETH", "GHA", "TZA", "UGA", "SEN", "CIV",
        "ZMB", "ZWE", "AGO", "MAR", "EGY", "DZA",
    },
    "MENA": {
        "EGY", "MAR", "DZA", "TUN", "SDN", "IRN", "IRQ", "SAU", "TUR",
        "ARE", "ISR", "JOR", "LBN", "SYR", "YEM",
    },
    "POST_SOVIET": {
        "RUS", "UKR", "BLR", "KAZ", "UZB", "KGZ", "TJK", "TKM", "AZE",
        "ARM", "GEO", "MDA", "LTU", "LVA", "EST",
    },
    "NORDIC": {"SWE", "NOR", "DNK", "FIN", "ISL"},
    "SOUTHERN_EUROPE": {"ITA", "ESP", "PRT", "GRC"},
    "ANGLO": {"USA", "GBR", "CAN", "AUS", "NZL", "IRL"},
}


def expand_countries(countries: list[str]) -> tuple[set[str], bool]:
    """Return (expanded ISO3 set, is_global_flag).

    If 'GLOBAL' is present, returns (empty-set, True) and the caller should
    treat this as "matches anything".
    """
    if not countries:
        return set(), False
    out: set[str] = set()
    is_global = False
    for tok in countries:
        tok = tok.upper()
        if tok == "GLOBAL":
            is_global = True
            continue
        if tok in GROUPS:
            out |= GROUPS[tok]
            continue
        # Assume ISO3
        if len(tok) == 3 and tok.isalpha():
            out.add(tok)
    return out, is_global


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_hypotheses() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in HYPOTHESES_DIR.glob("*/*.yaml"):
        if p.parent.name == "steelman":
            continue
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        hid = spec.get("hypothesis_id", p.stem)
        out[hid] = {"path": str(p.relative_to(ROOT)), "spec": spec}
    return out


# ---------------------------------------------------------------------------
# Scope comparison
# ---------------------------------------------------------------------------
def period_overlap(a: list[int] | None, b: list[int] | None) -> bool:
    if not a or not b or len(a) != 2 or len(b) != 2:
        return True  # can't assess → don't error
    return not (a[1] < b[0] or a[0] > b[1])


def compare_scopes(claim_scope: dict, hyp_scope: dict) -> list[dict]:
    """Return list of {level, axis, msg} violations."""
    v: list[dict] = []

    # Period
    cp = claim_scope.get("period")
    hp = hyp_scope.get("period")
    if cp and hp and not period_overlap(cp, hp):
        v.append({
            "level": "ERROR", "axis": "period",
            "msg": f"claim period {cp} disjoint from hypothesis period {hp}",
        })

    # Countries
    cc_raw = claim_scope.get("countries") or []
    hc_raw = hyp_scope.get("countries") or []
    cc, cc_global = expand_countries(cc_raw)
    hc, hc_global = expand_countries(hc_raw)
    if cc_raw and hc_raw and not (cc_global or hc_global):
        overlap = cc & hc
        if not overlap:
            v.append({
                "level": "ERROR", "axis": "countries",
                "msg": (f"claim countries {sorted(cc_raw)} (→{len(cc)} ISO3) "
                        f"disjoint from hypothesis countries {sorted(hc_raw)} "
                        f"(→{len(hc)} ISO3)"),
            })

    # Outcome dim
    co = set(claim_scope.get("outcome_dim") or [])
    ho = set(hyp_scope.get("outcome_dim") or [])
    if co and ho and not (co & ho):
        v.append({
            "level": "ERROR", "axis": "outcome_dim",
            "msg": (f"claim outcome_dim {sorted(co)} disjoint from "
                    f"hypothesis outcome_dim {sorted(ho)}"),
        })

    # Treatment tags — error only if BOTH sides declare tags and intersection
    # is empty. If hypothesis has no tags, it's a generic panel; match allowed.
    ct = set(claim_scope.get("treatment_tags") or [])
    ht = set(hyp_scope.get("treatment_tags") or [])
    if ct and ht and not (ct & ht):
        v.append({
            "level": "ERROR", "axis": "treatment_tags",
            "msg": (f"claim treatment_tags {sorted(ct)} disjoint from "
                    f"hypothesis treatment_tags {sorted(ht)}"),
        })

    # Policy family — informational
    cpf = set(claim_scope.get("policy_family") or [])
    hpf = set(hyp_scope.get("policy_family") or [])
    if cpf and hpf and not (cpf & hpf):
        v.append({
            "level": "WARN", "axis": "policy_family",
            "msg": (f"claim policy_family {sorted(cpf)} disjoint from "
                    f"hypothesis policy_family {sorted(hpf)}"),
        })

    return v


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def validate_all() -> tuple[list[dict], Counter]:
    hyps = load_hypotheses()
    rows: list[dict] = []
    stats: Counter[str] = Counter()

    for p in sorted(POSITIONS_DIR.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        try:
            spec = yaml.safe_load(p.read_text())
        except Exception as e:
            rows.append({
                "level": "ERROR", "position_id": p.stem, "claim_index": -1,
                "axis": "yaml", "msg": f"YAML parse error: {e}",
            })
            stats["parse_error"] += 1
            continue
        if not isinstance(spec, dict):
            continue
        position_id = spec.get("position_id", p.stem)
        claims = spec.get("falsifiable_specific_claims", []) or []
        for i, c in enumerate(claims):
            hid = c.get("linked_hypothesis_id", "")
            claim_scope = c.get("scope") or {}
            hyp_entry = hyps.get(hid)

            if not hyp_entry:
                rows.append({
                    "level": "ERROR", "position_id": position_id,
                    "claim_index": i, "linked_hypothesis_id": hid,
                    "axis": "linked_hypothesis_id",
                    "msg": f"hypothesis '{hid}' not in library",
                })
                stats["no_hypothesis"] += 1
                continue

            hyp_scope = hyp_entry["spec"].get("scope") or {}

            if not claim_scope and not hyp_scope:
                stats["both_missing_scope"] += 1
                rows.append({
                    "level": "WARN", "position_id": position_id,
                    "claim_index": i, "linked_hypothesis_id": hid,
                    "axis": "scope",
                    "msg": "neither claim nor hypothesis has scope: block "
                           "(legacy row — Phase 4 will populate)",
                })
                continue
            if not claim_scope:
                stats["claim_missing_scope"] += 1
                rows.append({
                    "level": "WARN", "position_id": position_id,
                    "claim_index": i, "linked_hypothesis_id": hid,
                    "axis": "scope",
                    "msg": "claim has no scope: block (Phase 4 will populate)",
                })
                continue
            if not hyp_scope:
                stats["hyp_missing_scope"] += 1
                rows.append({
                    "level": "WARN", "position_id": position_id,
                    "claim_index": i, "linked_hypothesis_id": hid,
                    "axis": "scope",
                    "msg": f"hypothesis '{hid}' has no scope: block (Phase 4 will populate)",
                })
                continue

            violations = compare_scopes(claim_scope, hyp_scope)
            if not violations:
                stats["pass"] += 1
            for v in violations:
                stats[v["level"].lower()] += 1
                rows.append({
                    **v,
                    "position_id": position_id, "claim_index": i,
                    "linked_hypothesis_id": hid,
                })

    return rows, stats


def format_rows(rows: list[dict], level_filter: str | None = None) -> str:
    out_lines: list[str] = []
    for r in rows:
        if level_filter and r["level"] != level_filter:
            continue
        out_lines.append(
            f"  [{r['level']}] {r['position_id']:25s} #{r.get('claim_index', ''):>3} "
            f"→ {r.get('linked_hypothesis_id', '')}"
        )
        out_lines.append(f"      axis={r.get('axis', '')}  {r['msg']}")
    return "\n".join(out_lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on WARN too")
    ap.add_argument("--summary", action="store_true",
                    help="print summary only")
    ap.add_argument("--json-out", type=Path,
                    default=AUDIT_DIR / "scope_validation.json",
                    help="path to write JSON report")
    args = ap.parse_args(argv)

    rows, stats = validate_all()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(rows, indent=2) + "\n")

    errors = [r for r in rows if r["level"] == "ERROR"]
    warns = [r for r in rows if r["level"] == "WARN"]

    print(f"=== Scope-alignment validation ===\n")
    print(f"  pass:                  {stats.get('pass', 0)}")
    print(f"  errors:                {len(errors)}")
    print(f"  warnings:              {len(warns)}")
    print(f"  claim_missing_scope:   {stats.get('claim_missing_scope', 0)}")
    print(f"  hyp_missing_scope:     {stats.get('hyp_missing_scope', 0)}")
    print(f"  both_missing_scope:    {stats.get('both_missing_scope', 0)}")
    print(f"  no_hypothesis:         {stats.get('no_hypothesis', 0)}")

    if not args.summary:
        if errors:
            print("\nERRORS:")
            print(format_rows(errors, "ERROR"))
        if warns and args.strict:
            print("\nWARNINGS:")
            print(format_rows(warns, "WARN"))

    print(f"\nReport → {args.json_out.relative_to(ROOT)}")

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
