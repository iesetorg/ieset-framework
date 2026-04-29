#!/usr/bin/env python3
"""Derive the hypothesis -> data coverage map from hypothesis YAMLs + publisher registry.

Reads:
    hypotheses/**/*.yaml           (hypothesis specs)
    data/fetchers/publishers.yaml  (publisher registry)

Writes:
    data/manifests/coverage.derived.yaml  (generated artifact; gitignored)

Checks:
    - Every `variables[].source` in every hypothesis resolves to a registered publisher.
    - `status: pre_registered` hypotheses hard-fail on unresolved publishers or on
      publishers whose own status is not `ready`.
    - `status: candidate` hypotheses warn on gaps.
    - `status: draft` hypotheses surface gaps only in the report (no hard fail).

Usage:
    python scripts/derive_coverage.py              # generate + report (soft)
    python scripts/derive_coverage.py --strict     # CI: fail on pre_registered hypothesis citing UNREGISTERED publisher
    python scripts/derive_coverage.py --require-ready # run-time gate: fail unless all publishers are status=ready
    python scripts/derive_coverage.py --check-only # don't write output, just check

Policy rationale:
    Pre-registration precedes data readiness (METHODOLOGY.md invariant 1). A hypothesis
    may be pre-registered before its fetchers exist — the spec is the commitment, the
    run is the validation. So `--strict` only fails on UNRESOLVED (unregistered)
    publishers, which are genuine gaps. Publishers that are registered but pending
    surface in reporting but don't block CI.

    `--require-ready` is the run-time gate: before a model actually runs, every
    publisher it depends on must have `status: ready`. This is checked separately
    from pre-registration CI.

    Sources beginning with `constructed:` are treated as non-publisher composite
    variables (e.g. fiscal_dominance_indicator constructed from multiple sources
    per documented coding rule). They are reported but not counted as gaps.

Exit codes:
    0 — no policy violation for the selected mode
    1 — violation (strict: unresolved publisher on pre_registered; require-ready: non-ready publisher)
    2 — dependency missing
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: install pyyaml (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
PUBLISHERS_PATH = ROOT / "data" / "fetchers" / "publishers.yaml"
AXES_PATH = ROOT / "axes.yaml"
_HYP_ROOT = ROOT / "hypotheses"
_SKIP_DIRS = {"conditional_taxonomy", "steelman"}
HYPOTHESIS_DIRS = [
    p for p in sorted(_HYP_ROOT.iterdir()) if p.is_dir() and p.name not in _SKIP_DIRS
] if _HYP_ROOT.exists() else []
POLICY_DIR = ROOT / "policies"
MOVEMENT_DIR = ROOT / "movements"
OUTPUT_PATH = ROOT / "data" / "manifests" / "coverage.derived.yaml"

SOURCE_TOKEN_RE = re.compile(
    r"(?P<publisher>[a-z][a-z0-9_]*[a-z0-9])\s*:\s*(?P<series>[A-Za-z0-9_.\-]+(?:\s*\([A-Z]{2,5}\))?)"
)


@dataclass
class PublisherRegistry:
    by_id: dict
    aliases: dict

    @classmethod
    def load(cls, path: Path) -> "PublisherRegistry":
        if not path.exists():
            raise FileNotFoundError(f"Publisher registry not found at {path}")
        with path.open() as f:
            doc = yaml.safe_load(f)
        by_id = doc.get("publishers", {})
        aliases = {}
        for pub_id, rec in by_id.items():
            for alias in rec.get("aliases", []):
                if alias in by_id:
                    raise ValueError(f"Alias {alias!r} conflicts with canonical id")
                if alias in aliases:
                    raise ValueError(f"Alias {alias!r} defined for multiple publishers")
                aliases[alias] = pub_id
        return cls(by_id=by_id, aliases=aliases)

    def resolve(self, pub_id: str) -> tuple[str | None, dict | None]:
        """Return (canonical_id, record) or (None, None) if not registered."""
        if pub_id in self.by_id:
            return pub_id, self.by_id[pub_id]
        if pub_id in self.aliases:
            canonical = self.aliases[pub_id]
            return canonical, self.by_id[canonical]
        return None, None


@dataclass
class HypothesisRef:
    path: Path
    hypothesis_id: str
    status: str
    variable_sources: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class AxisRegistry:
    """Map axis_id -> list of source_publisher ids, built from axes.yaml."""
    by_id: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path) -> "AxisRegistry":
        if not path.exists():
            return cls(by_id={})
        doc = yaml.safe_load(path.read_text()) or {}
        by_id: dict[str, list[str]] = {}
        for a in doc.get("axes") or []:
            aid = a.get("id")
            if not aid:
                continue
            by_id[aid] = list(a.get("source_publishers") or [])
        return cls(by_id=by_id)


@dataclass
class ContentRef:
    """Policy or movement reference — axis-indirect coverage dependency."""
    path: Path
    content_type: str   # "policy" | "movement"
    content_id: str
    status: str
    axes: list[str] = field(default_factory=list)


def extract_hypotheses() -> list[HypothesisRef]:
    out: list[HypothesisRef] = []
    for d in HYPOTHESIS_DIRS:
        if not d.exists():
            continue
        for yml in d.glob("*.yaml"):
            with yml.open() as f:
                doc = yaml.safe_load(f)
            if not doc or "hypothesis_id" not in doc:
                continue
            sources: list[tuple[str, str]] = []
            variables = doc.get("variables") or {}
            for group in ("outcome", "treatment", "decomposition_channels", "controls", "instruments"):
                for v in variables.get(group) or []:
                    src = v.get("source")
                    if not src:
                        continue
                    sources.append((v.get("name", "?"), src))
            out.append(
                HypothesisRef(
                    path=yml.relative_to(ROOT),
                    hypothesis_id=doc["hypothesis_id"],
                    status=doc.get("status", "draft"),
                    variable_sources=sources,
                )
            )
    return out


def extract_content_axes() -> list[ContentRef]:
    """Scan policies/ and movements/ for axis references.

    Policies use `axes_moved[i].axis`; movements use `axes_summary[i].axis`.
    """
    out: list[ContentRef] = []

    def _process(dir_: Path, content_type: str, id_field: str, axes_field: str):
        if not dir_.exists():
            return
        for yml in dir_.glob("*.yaml"):
            with yml.open() as f:
                doc = yaml.safe_load(f)
            if not doc or id_field not in doc:
                continue
            axes = []
            for entry in doc.get(axes_field) or []:
                if isinstance(entry, dict) and entry.get("axis"):
                    axes.append(entry["axis"])
            out.append(ContentRef(
                path=yml.relative_to(ROOT),
                content_type=content_type,
                content_id=doc[id_field],
                status=doc.get("status", "draft"),
                axes=axes,
            ))

    _process(POLICY_DIR, "policy", "policy_id", "axes_moved")
    _process(MOVEMENT_DIR, "movement", "movement_id", "axes_summary")
    return out


CONSTRUCTED_PREFIX = "constructed:"


def parse_source_tokens(source_str: str) -> tuple[list[tuple[str, str]], bool]:
    """Extract (publisher_id, series_id) tuples from a source string.

    Accepts forms like:
        'fred:M2SL'
        'fred:M2SL (USA); ecb:BSI.M.U2 (EU)'
        'fred:GOLDAMGBD228NLBM + bis:effective_exchange_rates'
        'constructed: <coding rule description>'  -> returns ([], True)

    Returns (tokens, is_constructed).
    """
    stripped = source_str.lstrip()
    if stripped.lower().startswith(CONSTRUCTED_PREFIX):
        return [], True
    tokens = [(m.group("publisher"), m.group("series").strip()) for m in SOURCE_TOKEN_RE.finditer(source_str)]
    return tokens, False


def derive(
    registry: PublisherRegistry,
    hypotheses: list[HypothesisRef],
    axes: AxisRegistry | None = None,
    content: list[ContentRef] | None = None,
) -> dict:
    axes = axes or AxisRegistry(by_id={})
    content = content or []
    unresolved_publishers: set[str] = set()
    not_ready_publishers: set[str] = set()
    per_hypothesis: list[dict] = []
    hypothesis_gaps: list[dict] = []

    for h in hypotheses:
        entries = []
        gaps = []
        for var_name, source_str in h.variable_sources:
            tokens, is_constructed = parse_source_tokens(source_str)
            if is_constructed:
                entries.append({
                    "variable": var_name,
                    "publisher": "constructed",
                    "series": source_str[len(CONSTRUCTED_PREFIX):].strip()[:120],
                    "publisher_status": "constructed",
                })
                continue
            if not tokens:
                gaps.append({"variable": var_name, "raw": source_str, "reason": "no_publisher_token_parsed"})
                continue
            for pub_id, series in tokens:
                canonical, rec = registry.resolve(pub_id)
                if canonical is None:
                    unresolved_publishers.add(pub_id)
                    gaps.append({
                        "variable": var_name, "raw_token": f"{pub_id}:{series}",
                        "reason": "unresolved_publisher", "publisher_used": pub_id,
                    })
                    continue
                if rec.get("status") != "ready":
                    not_ready_publishers.add(canonical)
                entries.append({
                    "variable": var_name,
                    "publisher": canonical,
                    "series": series,
                    "publisher_status": rec.get("status"),
                    "credibility_tier": rec.get("credibility_tier"),
                    "license": rec.get("license"),
                })
        per_hypothesis.append({
            "hypothesis_id": h.hypothesis_id,
            "status": h.status,
            "path": str(h.path),
            "resolved_sources": entries,
            "gaps": gaps,
        })
        if gaps:
            hypothesis_gaps.append({
                "hypothesis_id": h.hypothesis_id,
                "status": h.status,
                "gap_count": len(gaps),
            })

    # Per-axis-based content (policies + movements) coverage
    per_content: list[dict] = []
    content_gaps: list[dict] = []
    unresolved_axes: set[str] = set()
    for c in content:
        resolved = []
        gaps: list[dict] = []
        for axis_id in c.axes:
            pubs = axes.by_id.get(axis_id)
            if pubs is None:
                unresolved_axes.add(axis_id)
                gaps.append({"axis": axis_id, "reason": "unknown_axis_id"})
                continue
            axis_entry = {"axis": axis_id, "publishers": []}
            for pub_id in pubs:
                canonical, rec = registry.resolve(pub_id)
                if canonical is None:
                    unresolved_publishers.add(pub_id)
                    axis_entry["publishers"].append({"publisher": pub_id, "status": "unregistered"})
                    continue
                if rec.get("status") != "ready":
                    not_ready_publishers.add(canonical)
                axis_entry["publishers"].append({
                    "publisher": canonical,
                    "status": rec.get("status"),
                    "credibility_tier": rec.get("credibility_tier"),
                })
            resolved.append(axis_entry)
        per_content.append({
            "content_type": c.content_type,
            "content_id": c.content_id,
            "status": c.status,
            "path": str(c.path),
            "axes": resolved,
            "gaps": gaps,
        })
        if gaps:
            content_gaps.append({
                "content_type": c.content_type,
                "content_id": c.content_id,
                "status": c.status,
                "gap_count": len(gaps),
            })

    return {
        "version": 1,
        "generated_by": "scripts/derive_coverage.py",
        "hypothesis_count": len(hypotheses),
        "content_count": len(content),
        "per_hypothesis": per_hypothesis,
        "per_content": per_content,
        "summary": {
            "unresolved_publishers": sorted(unresolved_publishers),
            "not_ready_publishers": sorted(not_ready_publishers),
            "unresolved_axes": sorted(unresolved_axes),
            "hypotheses_with_gaps": hypothesis_gaps,
            "content_with_gaps": content_gaps,
        },
    }


def report(coverage: dict) -> None:
    s = coverage["summary"]
    print(
        f"derive_coverage: {coverage['hypothesis_count']} hypothesis + "
        f"{coverage.get('content_count', 0)} policy/movement file(s) scanned"
    )
    if s["unresolved_publishers"]:
        print(f"  unresolved publishers: {', '.join(s['unresolved_publishers'])}")
    if s["not_ready_publishers"]:
        print(f"  registered-but-not-ready: {', '.join(s['not_ready_publishers'])}")
    if s.get("unresolved_axes"):
        print(f"  unresolved axis ids: {', '.join(s['unresolved_axes'])}")
    if s["hypotheses_with_gaps"]:
        print("  hypotheses with gaps:")
        for g in s["hypotheses_with_gaps"]:
            print(f"    {g['hypothesis_id']} [{g['status']}]: {g['gap_count']} gap(s)")
    if s.get("content_with_gaps"):
        print("  policies/movements with gaps:")
        for g in s["content_with_gaps"]:
            print(f"    {g['content_type']} {g['content_id']} [{g['status']}]: {g['gap_count']} gap(s)")


def enforce_strict(coverage: dict) -> int:
    """CI gate: fail iff a pre_registered hypothesis OR canonical policy/movement cites
    an unregistered publisher or unknown axis id. Registered-but-pending publishers
    don't block pre-registration (invariant 1).
    """
    violations: list[str] = []
    for h in coverage["per_hypothesis"]:
        if h["status"] != "pre_registered":
            continue
        for gap in h["gaps"]:
            if gap.get("reason") == "unresolved_publisher":
                violations.append(
                    f"hypothesis {h['hypothesis_id']}: cites unregistered publisher "
                    f"{gap.get('publisher_used')!r} (token: {gap.get('raw_token')})"
                )

    for c in coverage.get("per_content", []):
        if c["status"] != "canonical":
            continue
        for gap in c.get("gaps", []):
            if gap.get("reason") == "unknown_axis_id":
                violations.append(
                    f"{c['content_type']} {c['content_id']}: references unknown axis {gap.get('axis')!r}"
                )
        for axis in c.get("axes", []):
            for pe in axis.get("publishers", []):
                if pe.get("status") == "unregistered":
                    violations.append(
                        f"{c['content_type']} {c['content_id']}: axis {axis['axis']} → unregistered publisher {pe.get('publisher')!r}"
                    )

    if violations:
        print(
            "\nSTRICT FAIL — canonical/pre_registered content cites unregistered publishers or axes:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            "\nFix: register the publisher in data/fetchers/publishers.yaml "
            "or add the axis to axes.yaml.",
            file=sys.stderr,
        )
        return 1
    return 0


def enforce_require_ready(coverage: dict) -> int:
    """Run-time gate: fail if any hypothesis cites a publisher whose status is not 'ready'.

    Call this before actually running a model, not in general CI.
    """
    violations: list[str] = []
    for h in coverage["per_hypothesis"]:
        for src in h["resolved_sources"]:
            if src["publisher_status"] not in ("ready", "constructed"):
                violations.append(
                    f"{h['hypothesis_id']}: publisher {src['publisher']!r} status={src['publisher_status']!r}"
                )
    if violations:
        print("\nREQUIRE-READY FAIL — model runs blocked:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="CI gate: fail on pre_registered hypothesis citing unregistered publisher.")
    parser.add_argument("--require-ready", action="store_true", help="Run-time gate: fail unless all cited publishers are status=ready.")
    parser.add_argument("--check-only", action="store_true", help="Do not write output file.")
    args = parser.parse_args()

    registry = PublisherRegistry.load(PUBLISHERS_PATH)
    axes = AxisRegistry.load(AXES_PATH)
    hypotheses = extract_hypotheses()
    content = extract_content_axes()
    coverage = derive(registry, hypotheses, axes=axes, content=content)

    if not args.check_only:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w") as f:
            yaml.safe_dump(coverage, f, sort_keys=False, width=100)
        print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")

    report(coverage)

    rc = 0
    if args.strict:
        rc = max(rc, enforce_strict(coverage))
    if args.require_ready:
        rc = max(rc, enforce_require_ready(coverage))
    return rc


if __name__ == "__main__":
    sys.exit(main())
