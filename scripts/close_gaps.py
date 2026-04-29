#!/usr/bin/env python3
"""Close the two content gaps the framework has accumulated.

Problem 1 — phantom position predictions.
  17 positions cite 183 unique hypothesis IDs in their `falsifiable_specific_claims`,
  of which only ~33 exist as real YAML files. We close this in two passes:
    - fuzzy-rename phantoms that are near-duplicates of existing hypothesis IDs
      (edit distance / token Jaccard ≥ 0.72)
    - generate minimal schema-valid stub hypothesis files for the remainder,
      seeded from the position's claim text, topic-classified via keyword match.
  Stubs are committed with `status: draft` so the pre-registration invariant
  remains honest — they are placeholders awaiting human pre-registration, not
  claims of prior commitment.

Problem 2 — orphan policies.
  1,858 of 1,896 policies have no explicit `linked_hypotheses`. We mirror the
  axis-overlap matching from web/lib/matching.ts in Python and promote the
  top-5 inferred matches per policy into each policy YAML, under a distinct
  `linked_hypotheses_inferred` field (not `linked_hypotheses`, which is
  reserved for human-authored links). This gives 100% explicit coverage
  while preserving the human/derived distinction.
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"
POS_ROOT = REPO / "positions"
POL_ROOT = REPO / "policies"
AXES_FILE = REPO / "axes.yaml"
HYP_AXIS_INDEX = HYP_ROOT / "_axis_index.yaml"
SKIP_HYP_DIRS = {"steelman", "conditional_taxonomy", "country_year_ideology"}

TOPICS = [
    "monetary", "distribution", "growth", "trade", "labour", "healthcare",
    "welfare_architecture", "institutional_quality", "energy", "housing",
    "resource_rents", "fiscal", "regulatory",
]

# Keywords per topic — pick the highest scoring topic for a stub's claim text.
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "monetary": [
        "monetary", "m2", "hyperinflation", "central bank", "currency", "qe",
        "money supply", "interest rate", "fiat", "fx", "exchange rate",
        "inflation", "bitcoin", "deflation", "bank of", "fed", "ecb",
        "taylor rule", "reserve", "monetary policy",
    ],
    "distribution": [
        "inequality", "gini", "poverty", "mobility", "redistribution",
        "top 1%", "top 10%", "wealth share", "income share", "distributional",
        "piketty", "wage share", "labor share", "quintile",
    ],
    "growth": [
        "gdp", "growth", "output", "productivity", "recovery", "convergence",
        "stagnation", "gdp per capita", "real gdp", "output gap", "shock therapy",
        "industrial policy", "developmental state", "catch up",
    ],
    "trade": [
        "tariff", "import", "export", "trade", "fta", "wto", "protectionism",
        "free trade", "trade liberalisation", "trade policy", "embargo",
        "sanction", "decoupling",
    ],
    "labour": [
        "wage", "employment", "labour", "labor", "union", "minimum wage",
        "unemployment", "job", "hiring", "collective bargaining",
        "gig", "teen employment", "neet",
    ],
    "healthcare": [
        "healthcare", "health care", "mortality", "life expectancy", "insurance",
        "medical", "hospital", "drug price", "medicare", "nhs",
    ],
    "welfare_architecture": [
        "pension", "forced saving", "transfer", "welfare state", "social security",
        "unemployment benefit", "ubi", "universal basic income",
        "child benefit", "welfare architecture", "bismarck", "beveridge",
    ],
    "institutional_quality": [
        "rule of law", "corruption", "judicial", "property rights", "institutions",
        "bukele", "court-packing", "expropriation", "nationalisation",
        "nationalization", "governance", "civil service",
    ],
    "energy": [
        "energy", "electricity", "renewable", "carbon", "nuclear", "fossil",
        "emissions", "solar", "wind", "ets", "carbon price", "decarbonisation",
        "energiewende", "oil price",
    ],
    "housing": [
        "housing", "rent", "mortgage", "home price", "affordability",
        "rent control", "zoning", "real estate",
    ],
    "resource_rents": [
        "oil", "natural resource", "commodity", "mining", "sovereign wealth",
        "norway fund", "resource curse", "petroleum", "gas reserves",
    ],
    "fiscal": [
        "tax", "deficit", "debt", "spending", "fiscal", "budget",
        "austerity", "fiscal stimulus", "tax cut", "tax hike", "corporate tax",
        "wealth tax", "progressive tax", "vat",
    ],
    "regulatory": [
        "regulation", "licensing", "deregulation", "antitrust", "competition",
        "financial regulation", "banking regulation", "environmental regulation",
        "immigration", "visa",
    ],
}


# ---------- utilities ----------------------------------------------------

def load_yaml(p: Path) -> dict | None:
    try:
        doc = yaml.safe_load(p.read_text())
        return doc if isinstance(doc, dict) else None
    except yaml.YAMLError:
        return None


def list_hypothesis_files() -> list[Path]:
    out: list[Path] = []
    for topic_dir in HYP_ROOT.iterdir():
        if not topic_dir.is_dir() or topic_dir.name in SKIP_HYP_DIRS:
            continue
        for f in topic_dir.glob("*.yaml"):
            if not f.name.startswith("_"):
                out.append(f)
    return out


def existing_hypothesis_ids() -> set[str]:
    return {f.stem for f in list_hypothesis_files()}


def list_position_files() -> list[Path]:
    return [f for f in POS_ROOT.glob("*.yaml") if not f.name.startswith("_")]


def list_policy_files() -> list[Path]:
    return [f for f in POL_ROOT.glob("*.yaml") if not f.name.startswith("_")]


# ---------- topic classification -----------------------------------------

def classify_topic(claim: str) -> str:
    claim_l = claim.lower()
    scores: dict[str, int] = {t: 0 for t in TOPICS}
    for t, kws in TOPIC_KEYWORDS.items():
        for kw in kws:
            # whole-word-ish match
            if re.search(rf"\b{re.escape(kw)}\b", claim_l):
                scores[t] += 2
            elif kw in claim_l:
                scores[t] += 1
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else "growth"


# ---------- phantom closure ----------------------------------------------

def similarity(a: str, b: str) -> float:
    t1, t2 = set(a.split("_")), set(b.split("_"))
    jac = len(t1 & t2) / max(1, len(t1 | t2))
    sm = SequenceMatcher(None, a, b).ratio()
    return max(jac, sm)


def close_phantoms(dry_run: bool = False) -> dict:
    """Close every phantom position prediction. Returns stats."""
    existing = existing_hypothesis_ids()
    phantom_claims: dict[str, list[tuple[str, str]]] = defaultdict(list)

    # Gather every phantom reference with its claim text.
    position_docs: list[tuple[Path, dict]] = []
    for pf in list_position_files():
        doc = load_yaml(pf)
        if not doc:
            continue
        position_docs.append((pf, doc))
        for c in doc.get("falsifiable_specific_claims", []) or []:
            hid = c.get("linked_hypothesis_id")
            claim = c.get("claim", "")
            if hid and hid not in existing and claim:
                phantom_claims[hid].append((doc["position_id"], claim))

    renames: dict[str, str] = {}
    stubs_to_create: list[tuple[str, str, str]] = []  # (phantom_id, claim, topic)

    for phantom, refs in sorted(phantom_claims.items()):
        # Try fuzzy rename first.
        best = max(existing, key=lambda h: similarity(phantom, h))
        if similarity(phantom, best) >= 0.72:
            renames[phantom] = best
            continue
        # Pick the citing claim whose text most overlaps the hypothesis_id's
        # tokens (so e.g. `industrial_policy_semiconductor_chips_act_effectiveness`
        # prefers a claim mentioning chips/semiconductor over an unrelated
        # industrial-policy claim). Fall back to longest text if tied at zero.
        id_tokens = {t for t in phantom.split("_") if len(t) >= 4}

        def token_overlap(claim_text: str) -> int:
            words = re.findall(r"[a-z]{4,}", claim_text.lower())
            return sum(1 for t in id_tokens if t in words)

        refs_sorted = sorted(
            refs,
            key=lambda r: (-token_overlap(r[1]), -len(r[1])),
        )
        best_claim = refs_sorted[0][1]
        topic = classify_topic(best_claim)
        stubs_to_create.append((phantom, best_claim, topic))

    # === write renames into position YAMLs ===
    renamed_positions = 0
    for pf, doc in position_docs:
        changed = False
        for c in doc.get("falsifiable_specific_claims", []) or []:
            hid = c.get("linked_hypothesis_id")
            if hid in renames:
                c["linked_hypothesis_id"] = renames[hid]
                changed = True
        if changed:
            renamed_positions += 1
            if not dry_run:
                write_position(pf, doc)

    # === write stub hypothesis YAMLs ===
    for phantom, claim, topic in stubs_to_create:
        topic_dir = HYP_ROOT / topic
        topic_dir.mkdir(parents=True, exist_ok=True)
        out_path = topic_dir / f"{phantom}.yaml"
        if out_path.exists():
            continue
        stub = {
            "hypothesis_id": phantom,
            "version": 1,
            "status": "draft",
            "topic": topic,
            "claim": claim.strip(),
            "notes": (
                "Auto-generated stub — created to close the position-prediction "
                "coverage gap (see scripts/close_gaps.py). Seeded from the "
                "citing positions' claim text. Pre-registration requires a human "
                "to upgrade status to candidate/pre_registered, add a "
                "falsification rule, sample, estimator, and variables."
            ),
            "prior_confidence": 0.5,
        }
        if not dry_run:
            out_path.write_text(render_yaml(stub))

    return {
        "phantoms_seen": len(phantom_claims),
        "renamed_refs": len(renames),
        "positions_edited": renamed_positions,
        "stubs_written": len(stubs_to_create),
    }


def render_yaml(stub: dict) -> str:
    """Stable, readable YAML for stubs."""
    header = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
    return header + yaml.safe_dump(
        stub, sort_keys=False, width=100, allow_unicode=True
    )


def write_position(path: Path, doc: dict) -> None:
    """Re-emit a position YAML preserving the leading schema hint."""
    raw = path.read_text()
    header_lines = []
    for line in raw.splitlines():
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    body = yaml.safe_dump(doc, sort_keys=False, width=100, allow_unicode=True)
    out = "\n".join(header_lines + [body]) if header_lines else body
    path.write_text(out)


# ---------- orphan closure (inferred linked_hypotheses) ------------------

def load_hypothesis_axis_index() -> dict[str, set[str]]:
    doc = yaml.safe_load(HYP_AXIS_INDEX.read_text())
    return {
        hid: {t["axis"] for t in (tags or [])}
        for hid, tags in (doc.get("index") or {}).items()
    }


def close_orphans(dry_run: bool = False, top_k: int = 5) -> dict:
    """For every orphan policy, write the top-K inferred matches into
    `linked_hypotheses_inferred` (kept distinct from human `linked_hypotheses`)."""
    hyp_axes = load_hypothesis_axis_index()

    touched = 0
    already_linked = 0
    total = 0
    for pf in list_policy_files():
        doc = load_yaml(pf)
        if not doc:
            continue
        total += 1
        if doc.get("linked_hypotheses"):
            already_linked += 1
        pax = {
            m.get("axis")
            for m in (doc.get("axes_moved") or [])
            if isinstance(m, dict) and m.get("axis")
        }
        if not pax:
            continue

        scored: list[tuple[str, int]] = []
        for hid, hax in hyp_axes.items():
            shared = pax & hax
            if shared:
                scored.append((hid, len(shared)))
        scored.sort(key=lambda t: -t[1])
        top = [hid for hid, _ in scored[:top_k]]

        if not top:
            continue

        if doc.get("linked_hypotheses_inferred") == top:
            continue  # no-op
        doc["linked_hypotheses_inferred"] = top
        touched += 1

        if not dry_run:
            rewrite_policy(pf, doc)

    return {
        "policies_total": total,
        "policies_with_explicit_links": already_linked,
        "policies_inferred_written": touched,
    }


def rewrite_policy(path: Path, doc: dict) -> None:
    raw = path.read_text()
    header_lines = []
    for line in raw.splitlines():
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    body = yaml.safe_dump(doc, sort_keys=False, width=100, allow_unicode=True)
    out = "\n".join(header_lines + [body]) if header_lines else body
    path.write_text(out)


# ---------- phase 3: policies referenced by movements that don't exist --------

def humanise_policy_id(pid: str) -> str:
    # strip common 2-letter country prefix if followed by underscore
    parts = pid.split("_")
    if parts and len(parts[0]) in (2, 3) and parts[0].isalpha():
        parts = parts[1:]
    return " ".join(w for w in parts if w).replace("  ", " ").strip() or pid


def close_missing_policies(dry_run: bool = False) -> dict:
    existing = {f.stem for f in list_policy_files()}
    missing: dict[str, list[dict]] = defaultdict(list)

    for mf in REPO.glob("movements/*.yaml"):
        if mf.name.startswith("_"):
            continue
        doc = load_yaml(mf)
        if not doc:
            continue
        for pid in doc.get("policies", []) or []:
            if pid and pid not in existing:
                missing[pid].append(doc)

    written = 0
    for pid, citing in sorted(missing.items()):
        path = POL_ROOT / f"{pid}.yaml"
        if path.exists():
            continue
        # inherit country + timeframe from citing movement(s)
        m = citing[0]
        countries = m.get("countries") or []
        tf = m.get("timeframe") or {}
        start = tf.get("start", 1900)
        end = tf.get("end", "ongoing")
        movement_ids = [d.get("movement_id") for d in citing if d.get("movement_id")]

        stub = {
            "policy_id": pid,
            "status": "draft",
            "title": humanise_policy_id(pid).title(),
            "countries": list(countries) or ["XXX"],
            "timeframe": {
                "start": int(start) if isinstance(start, (int, str)) and str(start).isdigit() else 1900,
                "end": end,
            },
            "description": (
                "Auto-generated stub — referenced in the `policies` list of "
                f"{len(movement_ids)} movement{'s' if len(movement_ids) != 1 else ''} "
                f"({', '.join(movement_ids[:3])}{'…' if len(movement_ids) > 3 else ''}). "
                "Created to close the movement → policy connectivity gap. "
                "A human needs to describe what this policy did, the axes it "
                "moved, and (optionally) any hypotheses testing its outcomes."
            ),
            "enacted_by": movement_ids,
        }
        if not dry_run:
            write_policy_stub(path, stub)
        written += 1

    return {
        "missing_policy_ids": len(missing),
        "stubs_written": written,
    }


def write_policy_stub(path: Path, stub: dict) -> None:
    header = "# yaml-language-server: $schema=../schemas/policy.schema.json\n"
    path.write_text(header + yaml.safe_dump(stub, sort_keys=False, width=100, allow_unicode=True))


# ---------- CLI ----------------------------------------------------------

def main() -> None:
    dry = "--dry-run" in sys.argv

    print("=== phase 1: close phantom position predictions ===")
    p1 = close_phantoms(dry_run=dry)
    for k, v in p1.items():
        print(f"  {k:28s}  {v}")

    print("\n=== phase 2: close orphan policies (inferred links) ===")
    p2 = close_orphans(dry_run=dry, top_k=5)
    for k, v in p2.items():
        print(f"  {k:28s}  {v}")

    print("\n=== phase 3: close missing-policy references from movements ===")
    p3 = close_missing_policies(dry_run=dry)
    for k, v in p3.items():
        print(f"  {k:28s}  {v}")

    if dry:
        print("\n(dry run — no files written)")


if __name__ == "__main__":
    main()
