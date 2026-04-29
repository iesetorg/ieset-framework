#!/usr/bin/env python3
"""Audit hypothesis runnability.

Classifies every hypothesis under hypotheses/<topic>/*.yaml (excluding
steelman/ and conditional_taxonomy/) by readiness to run:

  READY           - estimator.template is supported AND every variables.*.source
                    that names a known publisher has a vintage on disk.
  NEEDS_DATA      - template is supported but at least one source publisher
                    has no vintage (or no parquet file at all).
  NEEDS_TEMPLATE  - no estimator.template set OR template not in supported list.
  LEGACY_SCHEMA   - missing required fields (version / claim / estimator /
                    falsification) — same fields the validator already flags.
  HAS_RUN         - engine/runs/<hypothesis_id>/ exists.

A hypothesis can carry multiple flags (e.g. HAS_RUN + READY).

Outputs:
  engine/runnability.derived.yaml  — machine-readable per-hypothesis block.
  engine/runnability.report.md     — human-readable summary.

CLI:
  python3 scripts/audit_runnability.py [--strict]

`--strict` exits non-zero if any classification fails (LEGACY_SCHEMA or
NEEDS_TEMPLATE present).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: install pyyaml: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
HYP_ROOT = ROOT / "hypotheses"
VINTAGE_ROOT = ROOT / "data" / "vintages"
RUNS_ROOT = ROOT / "engine" / "runs"

OUT_YAML = ROOT / "engine" / "runnability.derived.yaml"
OUT_MD = ROOT / "engine" / "runnability.report.md"

SKIP_TOPIC_DIRS = {"steelman", "conditional_taxonomy"}

# Templates that have an existing replication.py in engine/runs/, plus the
# template enum from the schema. Treat all schema-listed templates as
# "supported in principle" — NEEDS_TEMPLATE only fires when the field is
# missing or the value is off-enum.
SUPPORTED_TEMPLATES = {
    "panel_fe",
    "panel_fe_decomposition",
    "did_callaway_santanna",
    "did_chaisemartin",
    "synthetic_control",
    "synth_did",
    "cointegration_vecm",
    "iv_2sls",
    "lp_iv",
    "event_study",
    "local_projections",
    "multi_metric_checklist",
    "descriptive",
}

# Required fields for a non-legacy spec — matches the validator's "required" list.
REQUIRED_FIELDS = ("hypothesis_id", "version", "topic", "claim", "status")

# A "publisher" prefix in a source string is anything matching ^[a-z][a-z0-9_]*$
# followed by ":" and a series id. The "constructed:" prefix is special and
# means the variable is derived in-script — not a fetcher dependency.
SOURCE_TOKEN_RE = re.compile(r"\b([a-z][a-z0-9_]*)\s*:\s*([^\s;,#)]+)")
CONSTRUCTED_PREFIXES = {"constructed", "derived", "manual", "academic", "proxies"}


def load_yaml(path: Path) -> dict | None:
    try:
        with path.open() as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None


def list_publishers_with_data() -> dict[str, set[str]]:
    """Return {publisher_id: {series_id, ...}} for every publisher with at least
    one parquet file on disk."""
    result: dict[str, set[str]] = {}
    if not VINTAGE_ROOT.exists():
        return result
    for pub_dir in VINTAGE_ROOT.iterdir():
        if not pub_dir.is_dir():
            continue
        series: set[str] = set()
        for parquet in pub_dir.glob("*.parquet"):
            # filename is <series>@<timestamp>.parquet
            stem = parquet.stem
            if "@" in stem:
                series.add(stem.split("@", 1)[0])
        if series:
            result[pub_dir.name] = series
    return result


def parse_sources(variables_block: dict | None) -> list[tuple[str, str]]:
    """Extract (publisher, series) tokens from every variables.<group>[].source.

    Multi-publisher composites (separated by `;` or `,`) yield multiple tokens.
    `constructed:`/`derived:`/`manual:` prefixes are skipped — they're not
    fetcher dependencies. Inline `# notes` are stripped.
    """
    if not variables_block or not isinstance(variables_block, dict):
        return []
    tokens: list[tuple[str, str]] = []
    for group in ("outcome", "treatment", "controls", "instruments", "decomposition_channels"):
        items = variables_block.get(group) or []
        if not isinstance(items, list):
            continue
        for v in items:
            if not isinstance(v, dict):
                continue
            src = v.get("source")
            if not isinstance(src, str):
                continue
            # strip inline comments (everything after ` # `)
            src_clean = re.split(r"\s+#\s+", src, maxsplit=1)[0]
            for m in SOURCE_TOKEN_RE.finditer(src_clean):
                pub = m.group(1)
                series = m.group(2).strip().strip('"').strip("'")
                if pub in CONSTRUCTED_PREFIXES:
                    continue
                # Drop trailing punctuation a careless author might include.
                series = series.rstrip(".,;)")
                tokens.append((pub, series))
    return tokens


def parse_canonical_metric_sources(metrics: list | None) -> list[tuple[str, str]]:
    if not metrics or not isinstance(metrics, list):
        return []
    tokens: list[tuple[str, str]] = []
    for m in metrics:
        if not isinstance(m, dict):
            continue
        src = m.get("source")
        if not isinstance(src, str):
            continue
        src_clean = re.split(r"\s+#\s+", src, maxsplit=1)[0]
        for mm in SOURCE_TOKEN_RE.finditer(src_clean):
            pub = mm.group(1)
            series = mm.group(2).strip().strip('"').strip("'").rstrip(".,;)")
            if pub in CONSTRUCTED_PREFIXES:
                continue
            tokens.append((pub, series))
    return tokens


def classify(
    spec: dict | None,
    path: Path,
    publisher_index: dict[str, set[str]],
) -> dict[str, Any]:
    """Classify a single hypothesis. Returns a record dict."""
    rel = str(path.relative_to(ROOT))
    rec: dict[str, Any] = {
        "path": rel,
        "hypothesis_id": None,
        "topic": None,
        "status": None,
        "estimator_template": None,
        "flags": [],
        "missing_fields": [],
        "missing_publishers": [],
        "missing_series": [],  # publisher present but specific series absent
        "all_publishers": [],
        "has_run": False,
    }

    if not isinstance(spec, dict):
        rec["flags"].append("LEGACY_SCHEMA")
        rec["missing_fields"] = ["<unparseable>"]
        return rec

    rec["hypothesis_id"] = spec.get("hypothesis_id") or path.stem
    rec["topic"] = spec.get("topic")
    rec["status"] = spec.get("status")

    # 1. LEGACY_SCHEMA — missing any required validator field, or no
    #    estimator block at all, or no falsification block.
    missing = [f for f in REQUIRED_FIELDS if f not in spec]
    if "estimator" not in spec:
        missing.append("estimator")
    if "falsification" not in spec:
        missing.append("falsification")
    if missing:
        rec["flags"].append("LEGACY_SCHEMA")
        rec["missing_fields"] = missing

    # 2. Estimator template
    estimator = spec.get("estimator")
    template = None
    if isinstance(estimator, dict):
        template = estimator.get("template")
    rec["estimator_template"] = template
    if template is None or template not in SUPPORTED_TEMPLATES:
        rec["flags"].append("NEEDS_TEMPLATE")

    # 3. Data sources
    tokens = parse_sources(spec.get("variables"))
    if spec.get("evidence_type") == "canonical_case_multi_metric":
        tokens.extend(parse_canonical_metric_sources(spec.get("canonical_metrics")))

    publishers_seen: set[str] = set()
    missing_pubs: set[str] = set()
    missing_series: set[tuple[str, str]] = set()
    for pub, series in tokens:
        publishers_seen.add(pub)
        if pub not in publisher_index:
            missing_pubs.add(pub)
        else:
            if series not in publisher_index[pub]:
                missing_series.add((pub, series))

    rec["all_publishers"] = sorted(publishers_seen)
    rec["missing_publishers"] = sorted(missing_pubs)
    rec["missing_series"] = sorted(f"{p}:{s}" for p, s in missing_series)

    has_template = template in SUPPORTED_TEMPLATES
    has_data = not missing_pubs  # publisher-level only; series-miss is softer

    if has_template and not has_data:
        rec["flags"].append("NEEDS_DATA")
    if has_template and has_data and "LEGACY_SCHEMA" not in rec["flags"]:
        rec["flags"].append("READY")

    # 4. HAS_RUN
    hyp_id = rec["hypothesis_id"]
    if hyp_id and (RUNS_ROOT / hyp_id).is_dir():
        rec["has_run"] = True
        rec["flags"].append("HAS_RUN")

    return rec


def collect_records(publisher_index: dict[str, set[str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not HYP_ROOT.exists():
        return records
    for topic_dir in sorted(p for p in HYP_ROOT.iterdir() if p.is_dir()):
        if topic_dir.name in SKIP_TOPIC_DIRS:
            continue
        for yml in sorted(topic_dir.glob("*.yaml")):
            if yml.name.startswith("_"):
                continue
            spec = load_yaml(yml)
            records.append(classify(spec, yml, publisher_index))
    return records


def write_yaml(records: list[dict[str, Any]]) -> None:
    payload = {
        "schema_version": 1,
        "generated_by": "scripts/audit_runnability.py",
        "total": len(records),
        "hypotheses": records,
    }
    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    with OUT_YAML.open("w") as f:
        yaml.safe_dump(payload, f, sort_keys=False, width=100)


def write_report(records: list[dict[str, Any]]) -> None:
    flag_counts = Counter()
    for r in records:
        for f in r["flags"]:
            flag_counts[f] += 1

    # Top blocking publishers: how many hypotheses would unlock if this
    # publisher were added. Only counts hypotheses that have a supported
    # template AND no other blocking publisher than this one (i.e. adding
    # the fetcher actually unlocks the hypothesis). For reporting we show
    # both unconditional (any-hypothesis-mentioning-it) and unlock-count.
    mentions = Counter()
    unlock_counts = Counter()
    for r in records:
        if "LEGACY_SCHEMA" in r["flags"]:
            continue
        if r["estimator_template"] not in SUPPORTED_TEMPLATES:
            continue
        if "READY" in r["flags"] or "HAS_RUN" in r["flags"]:
            continue
        miss = r["missing_publishers"]
        for p in miss:
            mentions[p] += 1
        if len(miss) == 1:
            unlock_counts[miss[0]] += 1

    # READY but not run.
    ready_not_run = [r for r in records
                     if "READY" in r["flags"] and "HAS_RUN" not in r["flags"]]
    ready_not_run.sort(key=lambda r: (r["topic"] or "", r["hypothesis_id"] or ""))

    lines: list[str] = []
    lines.append("# Hypothesis runnability audit\n")
    lines.append(f"_Generated by `scripts/audit_runnability.py` from {len(records)} hypothesis specs._\n")

    lines.append("## Summary counts\n")
    lines.append("| Flag | Count |")
    lines.append("|------|------:|")
    for flag in ("READY", "NEEDS_DATA", "NEEDS_TEMPLATE", "LEGACY_SCHEMA", "HAS_RUN"):
        lines.append(f"| {flag} | {flag_counts.get(flag, 0)} |")
    lines.append(f"| (total specs) | {len(records)} |")
    lines.append("")

    # Topic breakdown
    by_topic: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        t = r["topic"] or "unknown"
        for f in r["flags"]:
            by_topic[t][f] += 1
        by_topic[t]["TOTAL"] += 1
    lines.append("## By topic\n")
    lines.append("| Topic | Total | READY | NEEDS_DATA | NEEDS_TEMPLATE | LEGACY | HAS_RUN |")
    lines.append("|-------|------:|------:|-----------:|---------------:|-------:|--------:|")
    for t in sorted(by_topic):
        c = by_topic[t]
        lines.append(f"| {t} | {c['TOTAL']} | {c['READY']} | {c['NEEDS_DATA']} | "
                     f"{c['NEEDS_TEMPLATE']} | {c['LEGACY_SCHEMA']} | {c['HAS_RUN']} |")
    lines.append("")

    lines.append("## Top blocking publishers\n")
    lines.append("Publishers that, if a fetcher were added, would unlock the most "
                 "currently-blocked hypotheses. `solo_unlock` = hypotheses where "
                 "this is the *only* missing publisher; `mentioned` = total "
                 "blocked-hypothesis mentions.\n")
    lines.append("| Publisher | solo_unlock | mentioned |")
    lines.append("|-----------|------------:|----------:|")
    combined = sorted(set(mentions) | set(unlock_counts),
                      key=lambda p: (-unlock_counts.get(p, 0), -mentions.get(p, 0), p))
    for p in combined[:30]:
        lines.append(f"| {p} | {unlock_counts.get(p, 0)} | {mentions.get(p, 0)} |")
    lines.append("")

    lines.append("## READY-but-not-run candidates\n")
    lines.append(f"_{len(ready_not_run)} hypotheses are READY (template + data on disk) and have no engine/runs/ directory._\n")
    lines.append("| Topic | Hypothesis | Template |")
    lines.append("|-------|------------|----------|")
    for r in ready_not_run:
        lines.append(f"| {r['topic']} | `{r['hypothesis_id']}` | {r['estimator_template']} |")
    lines.append("")

    # NEEDS_TEMPLATE list — short, since it's actionable.
    nt = [r for r in records if "NEEDS_TEMPLATE" in r["flags"] and "LEGACY_SCHEMA" not in r["flags"]]
    if nt:
        lines.append("## NEEDS_TEMPLATE\n")
        lines.append("_Hypothesis has the schema but no recognised `estimator.template`._\n")
        lines.append("| Topic | Hypothesis | template field |")
        lines.append("|-------|------------|----------------|")
        for r in nt:
            lines.append(f"| {r['topic']} | `{r['hypothesis_id']}` | `{r['estimator_template']}` |")
        lines.append("")

    # LEGACY_SCHEMA list — also short.
    ls = [r for r in records if "LEGACY_SCHEMA" in r["flags"]]
    if ls:
        lines.append("## LEGACY_SCHEMA\n")
        lines.append("_Specs missing required fields (validator would flag these too)._\n")
        lines.append("| Hypothesis | missing |")
        lines.append("|------------|---------|")
        for r in ls:
            lines.append(f"| `{r['hypothesis_id']}` | {', '.join(r['missing_fields'])} |")
        lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero if any LEGACY_SCHEMA or NEEDS_TEMPLATE classifications.")
    args = ap.parse_args()

    publisher_index = list_publishers_with_data()
    records = collect_records(publisher_index)

    if not records:
        print("No hypothesis YAMLs found.", file=sys.stderr)
        return 2

    write_yaml(records)
    write_report(records)

    counts = Counter()
    for r in records:
        for f in r["flags"]:
            counts[f] += 1

    print(f"Audited {len(records)} hypothesis specs.")
    for k in ("READY", "NEEDS_DATA", "NEEDS_TEMPLATE", "LEGACY_SCHEMA", "HAS_RUN"):
        print(f"  {k:<15} {counts.get(k, 0)}")
    print(f"Wrote {OUT_YAML.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")

    if args.strict and (counts.get("LEGACY_SCHEMA", 0) or counts.get("NEEDS_TEMPLATE", 0)):
        print("STRICT: failed (LEGACY_SCHEMA or NEEDS_TEMPLATE present).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
