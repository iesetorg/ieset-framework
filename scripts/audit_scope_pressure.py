#!/usr/bin/env python3
"""Audit hypothesis scope pressure and identify downscope candidates.

This script highlights specs whose registered country scope is much wider
than the data coverage the current loader stack can actually sustain.
Those are good candidates to split into smaller-N variants:

- single-country descriptive or ITS specs
- bilateral comparisons
- treated-plus-3-to-5-donor synth specs
- compact regional panels instead of OECD-wide/global panels

Usage:
  ./venv/bin/python scripts/audit_scope_pressure.py
  ./venv/bin/python scripts/audit_scope_pressure.py --min-countries 11
  ./venv/bin/python scripts/audit_scope_pressure.py --write-report engine/scope_pressure.report.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_panel_fe


TEMPLATES_NEED_TREATMENT = {
    "panel_fe",
    "panel_fe_decomposition",
    "did_callaway_santanna",
    "did_chaisemartin",
    "event_study",
    "local_projections",
}
TEMPLATES_SYNTH = {"synth_did", "synthetic_control"}


def verdict_label(hid: str) -> str | None:
    path = ROOT / "engine" / "runs" / hid / "diagnostics.json"
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text())
    except Exception:
        return None
    label = doc.get("verdict_label") or doc.get("verdict")
    return str(label).strip() if label else None


def verdict_bucket(label: str | None) -> str:
    if not label:
        return "no_run"
    text = label.upper()
    if text.startswith("INCONCLUSIVE"):
        return "inconclusive"
    return "real_verdict"


def load_specs() -> list[dict]:
    rows: list[dict] = []
    for path in sorted((ROOT / "hypotheses").rglob("*.yaml")):
        try:
            spec = yaml.safe_load(path.read_text()) or {}
        except Exception:
            continue
        hid = spec.get("hypothesis_id")
        if not hid:
            continue
        sample = spec.get("sample") or {}
        estimator = spec.get("estimator") or {}
        countries = sample.get("countries") or []
        rows.append(
            {
                "hypothesis_id": hid,
                "path": str(path.relative_to(ROOT)),
                "spec": spec,
                "template": estimator.get("template") or "unknown",
                "country_count": len(countries),
                "countries": countries,
                "verdict_label": verdict_label(hid),
            }
        )
    return rows


def non_null_country_count(panel, col: str) -> int:
    if col not in panel.columns or "country_iso3" not in panel.columns:
        return 0
    sub = panel[panel[col].notna()]
    if sub.empty:
        return 0
    return int(sub["country_iso3"].nunique())


def non_null_row_count(panel, cols: list[str]) -> int:
    if any(col not in panel.columns for col in cols):
        return 0
    return int(len(panel.dropna(subset=cols)))


def profiled_metrics(meta: dict) -> dict:
    spec = meta["spec"]
    panel, status = run_panel_fe.build_panel(spec)
    panel_filt = run_panel_fe.filter_sample(panel, spec)
    outcome_items = ((spec.get("variables") or {}).get("outcome") or [])
    treatment_items = ((spec.get("variables") or {}).get("treatment") or [])
    outcome_name = run_panel_fe.first_loaded_var(outcome_items, panel_filt)
    treatment_name = run_panel_fe.first_loaded_var(treatment_items, panel_filt)

    metrics = {
        "variables_loaded": int(len(status.get("variables_loaded") or [])),
        "variables_missing": int(len(status.get("variables_missing") or [])),
        "loaded_publishers": sorted(
            {
                str(rec.get("publisher"))
                for rec in (status.get("variables_loaded") or [])
                if rec.get("publisher")
            }
        ),
        "outcome_name": outcome_name,
        "treatment_name": treatment_name,
        "filtered_rows": int(len(panel_filt)) if hasattr(panel_filt, "__len__") else 0,
        "outcome_rows": 0,
        "outcome_countries": 0,
        "treatment_rows": 0,
        "treatment_countries": 0,
        "joint_rows": 0,
        "joint_countries": 0,
    }

    if outcome_name:
        metrics["outcome_rows"] = non_null_row_count(panel_filt, [outcome_name])
        metrics["outcome_countries"] = non_null_country_count(panel_filt, outcome_name)
    if treatment_name:
        metrics["treatment_rows"] = non_null_row_count(panel_filt, [treatment_name])
        metrics["treatment_countries"] = non_null_country_count(panel_filt, treatment_name)
    if outcome_name and treatment_name:
        metrics["joint_rows"] = non_null_row_count(panel_filt, [outcome_name, treatment_name])
        if (
            outcome_name in panel_filt.columns
            and treatment_name in panel_filt.columns
            and "country_iso3" in panel_filt.columns
        ):
            joint = panel_filt.dropna(subset=[outcome_name, treatment_name])
            metrics["joint_countries"] = int(joint["country_iso3"].nunique()) if not joint.empty else 0

    metrics["coverage_countries"] = (
        metrics["joint_countries"]
        if meta["template"] in TEMPLATES_NEED_TREATMENT
        else metrics["outcome_countries"]
    )
    return metrics


def recommendation(meta: dict, metrics: dict) -> str:
    template = meta["template"]
    sample_n = meta["country_count"]
    outcome_c = metrics["outcome_countries"]
    treatment_c = metrics["treatment_countries"]
    coverage_c = metrics["coverage_countries"]
    joint_rows = metrics["joint_rows"]
    missing = metrics["variables_missing"]
    pubs = set(metrics["loaded_publishers"])

    if template in TEMPLATES_SYNTH:
        if coverage_c <= 1:
            return "Rewrite as single-country descriptive/event-study until donor data exists."
        if coverage_c <= 3 or sample_n >= 8:
            return "Trim to treated unit plus 3-5 curated donors with real pre-period coverage."
        return "Curate a smaller donor pool before expanding the sample."

    if template == "descriptive":
        if outcome_c <= 1:
            return "Rewrite as single-country descriptive spec."
        if outcome_c <= 2:
            return "Rewrite as bilateral comparison instead of broad multi-country descriptive scope."
        if sample_n >= 11 and outcome_c <= 5:
            return "Shrink to the 3-5 covered comparison countries."
        if pubs & {"ecb", "boe"} and outcome_c == 1 and sample_n >= 6:
            return "Use aggregate/regional descriptive scope instead of per-country panel framing."
        return "Narrow the comparison set before adding more countries."

    if template == "event_study":
        if sample_n >= 6 and coverage_c <= 2:
            return "Rewrite as single-country ITS or treated-vs-few-controls event study."
        if joint_rows and joint_rows < 30:
            return "Shrink to a compact treated/control set with enough pre/post overlap."
        return "Prefer a tighter event window with fewer countries."

    if template in TEMPLATES_NEED_TREATMENT:
        if joint_rows and joint_rows < 30:
            if coverage_c <= 2:
                return "Downscope to single-country/bilateral design; current panel is too wide for overlap."
            if sample_n >= 11:
                return "Re-register as a 3-5 country panel around the covered units only."
            return "Drop uncovered countries and keep only the best-overlap subset."
        if sample_n >= 11 and coverage_c <= 5:
            return "Replace broad panel framing with compact regional core countries."
        if missing >= 2 and sample_n >= 11:
            return "Narrow scope before chasing more sources; the spec is oversized for current coverage."
        return "Tighten the country set around units with real outcome-treatment overlap."

    return "Consider splitting into smaller-N companion specs."


def score(meta: dict, metrics: dict) -> tuple:
    sample_n = meta["country_count"]
    coverage_c = metrics["coverage_countries"]
    burden_gap = max(sample_n - coverage_c, 0)
    verdict = verdict_bucket(meta["verdict_label"])
    verdict_weight = {"inconclusive": 0, "no_run": 1, "real_verdict": 2}[verdict]
    return (verdict_weight, -burden_gap, -sample_n, coverage_c, -metrics["variables_missing"], meta["hypothesis_id"])


def build_report(rows: list[dict], profiled: list[dict], limit: int) -> str:
    lines: list[str] = []
    total = len(rows)
    lines.append("# Scope Pressure Audit")
    lines.append("")
    lines.append(f"- Total specs: **{total}**")
    lines.append(f"- Profiled large-scope specs: **{len(profiled)}**")
    lines.append("")

    lines.append("## Country-count buckets")
    bucket_defs = [
        ("1", lambda n: n == 1),
        ("2", lambda n: n == 2),
        ("3-5", lambda n: 3 <= n <= 5),
        ("6-10", lambda n: 6 <= n <= 10),
        ("11-20", lambda n: 11 <= n <= 20),
        ("21+", lambda n: n >= 21),
    ]
    for label, fn in bucket_defs:
        lines.append(f"- `{label}`: {sum(1 for row in rows if fn(row['country_count']))}")
    lines.append("")

    lines.append("## Large-scope unresolved specs by template")
    template_counts = Counter(
        row["template"]
        for row in profiled
        if verdict_bucket(row["verdict_label"]) in {"inconclusive", "no_run"}
    )
    for template, count in template_counts.most_common():
        lines.append(f"- `{template}`: {count}")
    lines.append("")

    lines.append("## Top downscope candidates")
    lines.append("")
    lines.append("| hypothesis_id | template | sample_n | covered_countries | joint_rows | verdict | recommendation |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    for row in sorted(profiled, key=lambda r: score(r, r["metrics"]))[:limit]:
        m = row["metrics"]
        lines.append(
            "| {hid} | {tpl} | {sample_n} | {cov} | {joint_rows} | {verdict} | {rec} |".format(
                hid=row["hypothesis_id"],
                tpl=row["template"],
                sample_n=row["country_count"],
                cov=m["coverage_countries"],
                joint_rows=m["joint_rows"],
                verdict=verdict_bucket(row["verdict_label"]),
                rec=row["recommendation"],
            )
        )
    lines.append("")

    lines.append("## Notes")
    lines.append("- `covered_countries` uses outcome-treatment overlap for panel-style specs and outcome coverage for descriptive specs.")
    lines.append("- These are rewrite/downscope candidates, not automatic spec edits.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-countries", type=int, default=6)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--write-report", type=str, default="")
    args = parser.parse_args()

    rows = load_specs()
    profiled: list[dict] = []
    for row in rows:
        verdict = verdict_bucket(row["verdict_label"])
        if row["country_count"] < args.min_countries:
            continue
        if verdict == "real_verdict" and row["country_count"] < 11:
            continue
        metrics = profiled_metrics(row)
        row = dict(row)
        row["metrics"] = metrics
        row["recommendation"] = recommendation(row, metrics)
        profiled.append(row)

    report = build_report(rows, profiled, args.limit)
    print(report, end="")

    if args.write_report:
        path = ROOT / args.write_report
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report)
        print(f"\nWrote report to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
