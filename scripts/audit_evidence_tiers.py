#!/usr/bin/env python3
"""Build the public evidence-quality ledger used by the site and APIs.

The ledger deliberately separates three questions that are easy to conflate:

1. Did the spec strictly precede the run in git?
2. Did the run clear the public method and estimator floor?
3. Is the design strong enough for a headline ("featured") evidence claim?

Historical and lower-identification work remains inspectable, but it cannot
silently inherit the standing of strict, method-valid causal work.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "engine" / "evidence_tier_audit.json"
PUBLIC_OUTPUT = ROOT / "web" / "public" / "evidence-tiers.json"
PREREG_INDEX = ROOT / "engine" / "preregistration_index.json"

SKIP_TOPICS = {"conditional_taxonomy", "steelman"}
NON_RESULT_PREFIXES = ("inconclusive", "blocked", "error", "no verdict")
STUB_RULE_MARKER = "when this stub is promoted from draft"

ESTIMATOR_FAILURE_MARKERS = {
    "primary_estimator_failed": (
        "linearmodels failed",
        "primary estimator failed",
        "primary specification failed",
    ),
    "rank_deficiency": (
        "full column rank",
        "rank deficiency",
        "rank-deficient",
    ),
    "fallback_estimator": (
        "fell back",
        "fallback estimator",
        "fallback specification",
    ),
    "effectively_zero": (
        "effect magnitude effectively zero",
        "machine-epsilon",
        "machine epsilon",
    ),
    "uncertainty_not_estimable": (
        "standard error/p-value not estimable",
        "p-value not estimable",
        "standard errors not estimable",
    ),
}

SCREENING_MARKERS = (
    "triage",
    "not bespoke",
    "not final scoreboard evidence",
    "generic panel",
    "alias-repair",
    "first-pass",
    "proxy-first",
    "candidate screen",
    "broad panel proxies",
    "throughput wave",
    "local-data first-pass",
    "generated from",
)

# A small, deliberately hand-audited reference set. Membership means "useful
# exemplar of the framework and its failure modes", not "peer reviewed" and
# not automatically "causal". Records only survive into the published set
# when they also clear the current public-visibility and estimator floors.
REFERENCE_SET_CANDIDATES: dict[str, str] = {
    "debt_overhang_private_investment_30yr": (
        "Long-horizon causal-design example with a supported directional result."
    ),
    "fiscal_consolidation_credibility_growth": (
        "Fiscal credibility example selected to expose estimator and threshold details."
    ),
    "poland_market_transition_30yr_growth": (
        "Long-run transition example with a supported result and strict registration."
    ),
    "sweden_1990s_market_reform_recovery": (
        "Refuted causal-design example; included to make adverse results prominent."
    ),
    "trade_lib_nafta_1994_mexico_manufacturing_employment": (
        "Trade event example with a supported result and inspectable replication."
    ),
    "welfare_transfer_argentina_auh_2009_child_poverty_effect": (
        "Refuted welfare-policy example; included to balance topics and verdict direction."
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def hypothesis_files() -> list[Path]:
    root = ROOT / "hypotheses"
    return sorted(
        path
        for path in root.glob("*/*.yaml")
        if path.parent.name not in SKIP_TOPICS
    )


def verdict_bucket(verdict: str) -> str:
    value = verdict.strip().lower()
    if value.startswith("supported_subset"):
        return "supported_subset"
    if value.startswith("inconclusive_data_pending"):
        return "inconclusive_data_pending"
    token = re.split(r"[^a-z_]+", value, maxsplit=1)[0]
    return token or "missing"


def registration_rows() -> dict[str, dict[str, Any]]:
    index = load_json(PREREG_INDEX)
    rows = index.get("registrations")
    return rows if isinstance(rows, dict) else {}


def estimator_floor_failures(text: str) -> list[str]:
    lower = text.lower()
    return sorted(
        label
        for label, markers in ESTIMATOR_FAILURE_MARKERS.items()
        if any(marker in lower for marker in markers)
    )


def has_sharpened_rule(doc: dict[str, Any]) -> bool:
    falsification = doc.get("falsification")
    rule = (
        str(falsification.get("rule") or "")
        if isinstance(falsification, dict)
        else ""
    )
    if STUB_RULE_MARKER not in rule.lower():
        return bool(rule.strip())
    notes = " ".join(
        str(doc.get(key) or "")
        for key in ("methodology_note", "notes", "disclosure")
    ).lower()
    return any(
        marker in notes
        for marker in ("dispositive", "sharpened", "primary (dispositive")
    )


def screening_flags(doc: dict[str, Any]) -> list[str]:
    estimator = doc.get("estimator")
    estimator_text = (
        " ".join(str(value) for value in estimator.values())
        if isinstance(estimator, dict)
        else ""
    )
    text = " ".join(
        (
            str(doc.get("methodology_note") or ""),
            str(doc.get("notes") or ""),
            str(doc.get("disclosure") or ""),
            estimator_text,
        )
    ).lower()
    return sorted(marker.replace(" ", "_") for marker in SCREENING_MARKERS if marker in text)


def build_record(
    path: Path,
    registrations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    doc = raw if isinstance(raw, dict) else {}
    hypothesis_id = str(doc.get("hypothesis_id") or path.stem)
    registration = registrations.get(hypothesis_id) or {}
    registration_status = str(registration.get("status") or "invalid_history")

    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics = load_json(run_dir / "diagnostics.json")
    verdict = str(diagnostics.get("verdict") or "").strip()
    card_path = run_dir / "result_card.md"
    card_text = (
        card_path.read_text(encoding="utf-8", errors="replace")
        if card_path.exists()
        else ""
    )
    diagnostic_text = " ".join(
        str(diagnostics.get(key) or "")
        for key in ("verdict", "method", "notes", "warning", "warnings")
    )
    estimator_failures = estimator_floor_failures(
        f"{diagnostic_text}\n{card_text}"
    )
    screening = screening_flags(doc)

    exclusion_reasons: list[str] = []
    if registration_status != "verified":
        exclusion_reasons.append(f"registration_{registration_status}")
    if not run_dir.is_dir():
        exclusion_reasons.append("run_missing")
    if not verdict:
        exclusion_reasons.append("verdict_missing")
    elif verdict.lower().startswith(NON_RESULT_PREFIXES):
        exclusion_reasons.append("non_result_verdict")
    if not (run_dir / "replication.py").exists():
        exclusion_reasons.append("replication_missing")
    if not has_sharpened_rule(doc):
        exclusion_reasons.append("falsification_rule_unsharpened")
    if estimator_failures:
        exclusion_reasons.append("estimator_floor_failed")

    public_visible = not exclusion_reasons
    evidence_type = str(doc.get("evidence_type") or "unspecified")

    if public_visible and evidence_type == "causal" and not screening:
        tier = "featured"
    elif public_visible:
        tier = "calibration"
    else:
        tier = "archive"

    reference_note = REFERENCE_SET_CANDIDATES.get(hypothesis_id)
    reference_set = bool(reference_note and public_visible and not estimator_failures)

    return {
        "hypothesis_id": hypothesis_id,
        "topic": str(doc.get("topic") or path.parent.name),
        "tier": tier,
        "public_visible": public_visible,
        "reference_set": reference_set,
        "reference_note": reference_note if reference_set else None,
        "registration_status": registration_status,
        "evidence_type": evidence_type,
        "verdict_bucket": verdict_bucket(verdict) if verdict else "missing",
        "estimator_floor": "fail" if estimator_failures else "pass",
        "estimator_floor_failures": estimator_failures,
        "screening_flags": screening,
        "exclusion_reasons": sorted(set(exclusion_reasons)),
        "canonical_url": (
            f"https://framework.ieset.org/h/{hypothesis_id}/"
        ),
    }


def build() -> dict[str, Any]:
    registrations = registration_rows()
    records = [
        build_record(path, registrations)
        for path in hypothesis_files()
    ]
    records.sort(key=lambda row: str(row["hypothesis_id"]))

    tier_counts = Counter(str(row["tier"]) for row in records)
    registration_counts = Counter(
        str(row["registration_status"]) for row in records
    )
    verdict_counts = Counter(str(row["verdict_bucket"]) for row in records)
    exclusion_counts = Counter(
        reason
        for row in records
        for reason in row["exclusion_reasons"]
    )
    estimator_failures = Counter(
        failure
        for row in records
        for failure in row["estimator_floor_failures"]
    )
    public_records = [row for row in records if row["public_visible"]]
    reference_records = [row for row in records if row["reference_set"]]

    return {
        "schema": "ieset-evidence-tier-audit-v1",
        "canonical_url": "https://framework.ieset.org/evidence/",
        "definitions": {
            "featured": (
                "Strict spec-before-run registration; public method gate; "
                "estimator floor passed; causal evidence type; no screening markers."
            ),
            "calibration": (
                "Strict registration and public method gate passed, but the design "
                "is associational, descriptive, canonical-case, or screening-grade."
            ),
            "archive": (
                "Directly inspectable research record that does not currently clear "
                "all public evidence gates. It receives no headline evidence credit."
            ),
            "reference_set": (
                "Small hand-audited set of useful exemplars. Membership is not peer "
                "review and does not override the evidence tier."
            ),
            "estimator_floor": (
                "Directional verdicts cannot receive public evidence credit when the "
                "primary estimator failed, was rank-deficient, fell back, produced an "
                "effectively-zero coefficient, or could not estimate uncertainty."
            ),
        },
        "summary": {
            "hypotheses": len(records),
            "public_visible": len(public_records),
            "reference_set": len(reference_records),
            "tier_counts": dict(sorted(tier_counts.items())),
            "registration_counts": dict(sorted(registration_counts.items())),
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "estimator_floor_failures": dict(sorted(estimator_failures.items())),
            "exclusion_counts": dict(sorted(exclusion_counts.items())),
        },
        "reference_set": [
            {
                "hypothesis_id": row["hypothesis_id"],
                "tier": row["tier"],
                "note": row["reference_note"],
                "canonical_url": row["canonical_url"],
            }
            for row in reference_records
        ],
        "records": records,
    }


def encoded(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when either committed public audit copy is stale.",
    )
    args = parser.parse_args()
    expected = encoded(build())
    targets = (OUTPUT, PUBLIC_OUTPUT)

    if args.check:
        stale = [
            path
            for path in targets
            if not path.exists()
            or path.read_text(encoding="utf-8") != expected
        ]
        if stale:
            for path in stale:
                print(
                    f"FAIL: {path.relative_to(ROOT)} is stale; run "
                    "python scripts/audit_evidence_tiers.py",
                    file=sys.stderr,
                )
            return 1
    else:
        for path in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")

    summary = json.loads(expected)["summary"]
    print(
        "OK "
        f"(featured={summary['tier_counts'].get('featured', 0)}, "
        f"calibration={summary['tier_counts'].get('calibration', 0)}, "
        f"archive={summary['tier_counts'].get('archive', 0)}, "
        f"estimator-floor failures="
        f"{sum(summary['estimator_floor_failures'].values())})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
