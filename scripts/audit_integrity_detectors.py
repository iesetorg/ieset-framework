#!/usr/bin/env python3
"""Integrity detectors for adversarial audit findings X1-X4 (2026-07-31 audit).

Implements the audit's standing proposals A-D as runnable detectors over
engine/runs/*/diagnostics.json:

  A (X1) detect_unit_typetag_mismatch — thresholds expressed in absolute units
      (years, TFR points, Gini points, millions, percentage points) must not be
      evaluated against percent-change stats (peak_to_trough_pct_decline,
      pct_increase_from_baseline).
  B (X2) detect_sentinel_values — percent-decline stats near 100 and
      percent/ratio-family values at 1e4 scale are fallback/sentinel artefacts,
      never real observations.
  C (X3) detect_duplicate_source_hashes — fewer distinct vintage hashes than
      declared publishers cannot establish "independent sources" claims.
      Multiple series from one publisher count as one publisher; absent hashes
      are a missing-custody finding, not evidence of byte-identical files.
  D (X4) count_exceeds_declared_sample — `countries_meeting_threshold` counts
      above the sample size declared in the threshold ("at least k of n") mean
      the evaluator scanned the wrong universe.

Findings from these detectors are dispositions, not edits: affected runs are
corrected via visible annotations (see
engine/audits/ieset_adversarial_audit_remediation_2026-09-03.md), never silent
patching. Usage:

    venv/bin/python scripts/audit_integrity_detectors.py [--run RUN_ID]

Exit code 1 when any finding is present (CI regression mode).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "engine" / "runs"

# --- audit record B (X2): sentinel observed values ------------------------- #
PCT_CHANGE_STATS = {"peak_to_trough_pct_decline", "pct_increase_from_baseline"}
SENTINEL_PCT_THRESHOLD = 99.99  # a ~100% decline is impossible for a continuing series
SENTINEL_RATIO_CEILING = 1e4    # pct/ratio-family values at 1e4 scale are artefacts
PERCENT_DENOMINATED = re.compile(r"%|percent|percentage point|\bpp\b", re.IGNORECASE)

# --- audit record A (X1): unit typetag mismatch ---------------------------- #
ABSOLUTE_UNIT_PATTERNS = [
    (re.compile(r"\byears?\b", re.IGNORECASE), "years_absolute"),
    (re.compile(r"\bTFR\b"), "tfr_points"),
    (re.compile(r"\bGini\b", re.IGNORECASE), "gini_points"),
    (re.compile(r"\bmillion\b", re.IGNORECASE), "millions_absolute"),
]
PP_UNIT = re.compile(r"percentage points?\b|\bpp\b", re.IGNORECASE)

# --- audit record D (X4): sample-scope explosion --------------------------- #
COUNT_THRESHOLD_STATS = {"countries_meeting_threshold"}
SAMPLE_SIZE_RE = re.compile(r"\bof\s+(\d+)\b")


def _source_keys(metric: dict) -> list[str]:
    raw = metric.get("source") or ""
    return [p.strip() for p in raw.split(";") if p.strip()]


def _publishers(metric: dict) -> list[str]:
    return sorted({source.split(":", 1)[0].strip() for source in _source_keys(metric)})


def detect_sentinel_values(metrics: list[dict]) -> list[dict]:
    """Flag impossible-scale observed values (audit record B)."""
    findings = []
    for m in metrics:
        stat = m.get("observed_stat_name") or ""
        try:
            value = float(m.get("observed_value"))
        except (TypeError, ValueError):
            continue
        if stat in PCT_CHANGE_STATS and value >= SENTINEL_PCT_THRESHOLD:
            findings.append({
                "detector": "sentinel_value",
                "metric_id": m.get("metric_id"),
                "observed_value": value,
                "stat_name": stat,
                "detail": f"percent-change stat at {value:.4f} >= {SENTINEL_PCT_THRESHOLD} — fallback/sentinel artefact, not a real observation",
            })
        elif value >= SENTINEL_RATIO_CEILING and (
            stat in PCT_CHANGE_STATS
            or (stat == "max_in_window_fallback" and PERCENT_DENOMINATED.search(m.get("threshold") or ""))
        ):
            findings.append({
                "detector": "sentinel_value",
                "metric_id": m.get("metric_id"),
                "observed_value": value,
                "stat_name": stat,
                "detail": f"value {value:.4g} at >=1e4 scale for percent/ratio-family stat '{stat}' — wrong series or sentinel scored as MET",
            })
    return findings


def detect_unit_typetag_mismatch(metric: dict) -> dict | None:
    """Flag absolute-unit thresholds evaluated against percent-change stats
    (audit record A). Reports every absolute unit family found in the
    threshold, since thresholds mix families (e.g. "TFR ... trough year")."""
    stat = metric.get("observed_stat_name") or ""
    if stat not in PCT_CHANGE_STATS:
        return None
    threshold = metric.get("threshold") or ""
    unit_families = [family for pattern, family in ABSOLUTE_UNIT_PATTERNS if pattern.search(threshold)]
    if PP_UNIT.search(threshold) and stat == "pct_increase_from_baseline":
        unit_families.append("percentage_points")
    if not unit_families:
        return None
    return {
        "detector": "unit_typetag_mismatch",
        "metric_id": metric.get("metric_id"),
        "threshold": threshold,
        "threshold_units": unit_families,
        "stat_name": stat,
        "observed_value": metric.get("observed_value"),
        "detail": f"threshold in {'+'.join(unit_families)} evaluated against percent-change stat '{stat}' — MET/NOT_MET mechanically manufactured",
    }


def detect_duplicate_source_hashes(diagnostics: dict) -> list[dict]:
    """Flag missing custody separately from fewer hashes than publishers.

    The per-metric hashes do not map a particular file to a publisher. Fewer
    distinct hashes than publisher namespaces cannot establish that each has
    an independent pinned file; zero hashes proves only that source custody
    was not recorded for a multi-source metric.
    """
    findings = []
    for m in diagnostics.get("metrics") or []:
        if not isinstance(m, dict):
            continue
        source_keys = sorted(set(_source_keys(m)))
        pubs = _publishers(m)
        hashes = sorted(set(m.get("vintage_sha256") or []))
        if not hashes and len(source_keys) >= 2:
            findings.append({
                "detector": "missing_source_hash",
                "metric_id": m.get("metric_id"),
                "publishers": pubs,
                "source_keys": source_keys,
                "sha256": [],
                "detail": "multiple declared source series have no per-metric vintage hashes — source custody missing; byte identity unassessed",
            })
        elif len(pubs) >= 2 and len(hashes) < len(pubs):
            findings.append({
                "detector": "duplicate_source_hash",
                "metric_id": m.get("metric_id"),
                "publishers": pubs,
                "source_keys": source_keys,
                "sha256": hashes,
                "detail": (
                    f"{len(pubs)} declared publishers have only {len(hashes)} distinct per-metric vintage hash(es)"
                    " — independent source custody unverified"
                ),
            })
    return findings


def count_exceeds_declared_sample(observed_count: float, declared_sample_size: int) -> bool:
    """Audit record D core assertion: a count of units meeting a threshold can
    never exceed the declared sample size."""
    return observed_count > declared_sample_size


def detect_sample_explosion(metrics: list[dict]) -> list[dict]:
    """Flag `countries_meeting_threshold` counts above the sample size declared
    in the threshold text (audit record D)."""
    findings = []
    for m in metrics:
        stat = m.get("observed_stat_name") or ""
        if stat not in COUNT_THRESHOLD_STATS:
            continue
        match = SAMPLE_SIZE_RE.search(m.get("threshold") or "")
        if not match:
            continue
        declared = int(match.group(1))
        try:
            observed = float(m.get("observed_value"))
        except (TypeError, ValueError):
            continue
        if count_exceeds_declared_sample(observed, declared):
            findings.append({
                "detector": "sample_scope_explosion",
                "metric_id": m.get("metric_id"),
                "observed_count": observed,
                "declared_sample_size": declared,
                "threshold": m.get("threshold"),
                "detail": f"counted {observed:.0f} units against a declared sample of {declared} — evaluator scanned the wrong universe (aggregates double-counted)",
            })
    return findings


def scan_diagnostics(diagnostics: dict) -> dict:
    metrics = [m for m in (diagnostics.get("metrics") or []) if isinstance(m, dict)]
    if not metrics:
        return {"skipped": "no metrics list (non-multi-metric diagnostics shape)", "findings": []}
    unit_findings = [f for f in (detect_unit_typetag_mismatch(m) for m in metrics) if f]
    findings = (
        detect_sentinel_values(metrics)
        + unit_findings
        + detect_duplicate_source_hashes(diagnostics)
        + detect_sample_explosion(metrics)
    )
    return {"findings": findings}


def scan_run(run_dir: Path) -> dict:
    diag_path = run_dir / "diagnostics.json"
    if not diag_path.exists():
        return {"run_id": run_dir.name, "skipped": "no diagnostics.json"}
    diagnostics = json.loads(diag_path.read_text())
    result = scan_diagnostics(diagnostics)
    result["run_id"] = run_dir.name
    result["verdict"] = diagnostics.get("verdict")
    return result


def scan_all_runs() -> list[dict]:
    return [scan_run(p) for p in sorted(RUNS_ROOT.iterdir()) if p.is_dir()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", help="scan a single run id under engine/runs/")
    args = parser.parse_args()

    if args.run:
        results = [scan_run(RUNS_ROOT / args.run)]
    else:
        results = scan_all_runs()

    flagged = 0
    for result in results:
        findings = result.get("findings") or []
        if not findings:
            continue
        flagged += 1
        print(f"{result['run_id']} (verdict={result.get('verdict')}): {len(findings)} findings")
        for f in findings:
            detail = f.get("detail", "")
            metric = f.get("metric_id") or ",".join(f.get("sha256") or [])[:24]
            print(f"  [{f['detector']}] {metric}: {detail}")

    total = sum(len(r.get("findings") or []) for r in results)
    scanned = sum(1 for r in results if not r.get("skipped"))
    print(f"\nscanned {scanned} runs with metrics; {flagged} runs flagged; {total} findings")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
