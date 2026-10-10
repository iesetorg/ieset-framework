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
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

import audit_integrity_detectors

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "engine" / "evidence_tier_audit.json"
PUBLIC_OUTPUT = ROOT / "web" / "public" / "evidence-tiers.json"
PREREG_INDEX = ROOT / "engine" / "preregistration_index.json"
SCHOOL_SCORE_EXCLUSIONS = ROOT / "engine" / "school_score_exclusions.json"
PUBLIC_EVIDENCE_QUARANTINES = ROOT / "engine" / "public_evidence_quarantines.json"

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


def load_school_score_exclusions(path: Path = SCHOOL_SCORE_EXCLUSIONS) -> dict[str, str]:
    """Read explicit scoring holds without changing frozen run artifacts.

    A missing or malformed registry is an audit failure: silently dropping a
    hold would turn later-attached school links into scored claims.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "ieset-school-score-exclusions-v1":
        raise ValueError(f"invalid school-score exclusion schema: {path}")
    rows = payload.get("exclusions")
    if not isinstance(rows, list):
        raise ValueError(f"invalid school-score exclusions: {path}")
    exclusions: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"hypothesis_id", "reason"}:
            raise ValueError(f"invalid school-score exclusion row: {path}")
        hypothesis_id, reason = row["hypothesis_id"], row["reason"]
        if not isinstance(hypothesis_id, str) or not hypothesis_id.strip() or \
                not isinstance(reason, str) or not reason.strip() or hypothesis_id in exclusions:
            raise ValueError(f"duplicate or incomplete school-score exclusion: {path}")
        exclusions[hypothesis_id] = reason
    return exclusions


def load_public_evidence_quarantines(
    path: Path = PUBLIC_EVIDENCE_QUARANTINES,
) -> dict[str, str]:
    """Read source-semantic holds without altering frozen specs or run artifacts."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "ieset-public-evidence-quarantines-v1":
        raise ValueError(f"invalid public-evidence quarantine schema: {path}")
    rows = payload.get("quarantines")
    if not isinstance(rows, list):
        raise ValueError(f"invalid public-evidence quarantines: {path}")
    quarantines: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"hypothesis_id", "reason"}:
            raise ValueError(f"invalid public-evidence quarantine row: {path}")
        hypothesis_id, reason = row["hypothesis_id"], row["reason"]
        if (not isinstance(hypothesis_id, str) or not hypothesis_id.strip()
                or not isinstance(reason, str) or not reason.strip()
                or hypothesis_id in quarantines):
            raise ValueError(f"duplicate or incomplete public-evidence quarantine: {path}")
        quarantines[hypothesis_id] = reason
    return quarantines


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


def school_score_eligible_for_public_run(public_visible: bool, correction: Any) -> bool:
    if not public_visible:
        return False
    if not isinstance(correction, dict):
        return True
    return (
        correction.get("school_score_eligible") is not False
        and correction.get("school_score_credit") != 0
    )


def immutable_source_locked_nested_verdict(
    diagnostics: dict[str, Any],
    hypothesis_id: str,
    run_dir: Path,
    registration: dict[str, Any],
) -> str:
    """Accept a nested result only with an unchanged pre-result source lock.

    Legacy nested payloads cannot become public merely by adding a wrapper:
    the spec, lock, and first run must be distinct ordered Git commits, and
    the current source lock and aggregate result must match their first blobs.
    """
    nested = diagnostics.get("result")
    if not isinstance(nested, dict) or registration.get("status") != "verified":
        return ""
    verdict = str(nested.get("verdict") or "").strip().upper()
    if verdict not in {"SUPPORTED", "PARTIAL", "REFUTED", "INCONCLUSIVE"}:
        return ""
    if verdict != "INCONCLUSIVE" and nested.get("gate_failures") != []:
        return ""
    family_size = diagnostics.get("family_size")
    if (diagnostics.get("hypothesis_id") != hypothesis_id
            or not isinstance(family_size, int)
            or isinstance(family_size, bool)
            or family_size < 1
            or family_size > 20):
        return ""
    spec_commit = str(registration.get("spec_commit") or "")
    run_commit = str(registration.get("run_first_commit") or "")
    lock_commit = str(diagnostics.get("source_lock_commit") or "")
    source_sha = str(diagnostics.get("source_sha256") or "")
    key_sha = str(diagnostics.get("source_key_roster_sha256") or "")
    if (diagnostics.get("registration_commit") != spec_commit
            or any(not re.fullmatch(r"[0-9a-f]{40}", sha)
                   for sha in (spec_commit, lock_commit, run_commit))
            or any(not re.fullmatch(r"[0-9a-f]{64}", sha)
                   for sha in (source_sha, key_sha))):
        return ""

    def git_bytes(*args: str) -> bytes | None:
        proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
        return proc.stdout if proc.returncode == 0 else None

    if (git_bytes("merge-base", "--is-ancestor", spec_commit, lock_commit) is None
            or spec_commit == lock_commit
            or git_bytes("merge-base", "--is-ancestor", lock_commit, run_commit) is None
            or lock_commit == run_commit):
        return ""
    spec_rel = registration.get("path")
    if not isinstance(spec_rel, str) or not spec_rel.startswith("hypotheses/"):
        return ""
    if git_bytes("show", f"{spec_commit}:{spec_rel}") != (ROOT / spec_rel).read_bytes():
        return ""
    result_rel = (run_dir / "diagnostics.json").relative_to(ROOT).as_posix()
    if git_bytes("show", f"{run_commit}:{result_rel}") != (run_dir / "diagnostics.json").read_bytes():
        return ""
    names = git_bytes("diff-tree", "--no-commit-id", "--name-only", "-r", lock_commit)
    if names is None:
        return ""
    lock_paths = [name for name in names.decode().splitlines()
                  if name.startswith("data/pinned_evidence/") and name.endswith(".source.json")]
    if len(lock_paths) != 1:
        return ""
    lock_rel = lock_paths[0]
    committed_lock = git_bytes("show", f"{lock_commit}:{lock_rel}")
    lock_path = ROOT / lock_rel
    if committed_lock is None or not lock_path.is_file() or committed_lock != lock_path.read_bytes():
        return ""
    try:
        lock = json.loads(committed_lock)
    except (TypeError, ValueError):
        return ""
    if (lock.get("hypothesis_id") != hypothesis_id
            or lock.get("registration_commit") != spec_commit
            or lock.get("source_sha256") != source_sha
            or lock.get("key_roster_sha256") != key_sha
            or lock.get("family_size") != family_size):
        return ""
    packet_files = ("result_card.md", "replication.py", "hypothesis.yaml",
                    "manifest.yaml", "evidence_packet.yaml")
    if any(not (run_dir / name).is_file() for name in packet_files):
        return ""
    if (run_dir / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel).read_bytes():
        return ""
    try:
        manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text())
        packet = yaml.safe_load((run_dir / "evidence_packet.yaml").read_text())
    except (OSError, yaml.YAMLError):
        return ""
    if not isinstance(manifest, dict) or not isinstance(packet, dict):
        return ""
    packet_source = packet.get("source")
    reproduction = packet.get("reproduction")
    if (manifest.get("hypothesis_id") != hypothesis_id
            or manifest.get("status") != verdict
            or manifest.get("preregistration_commit") != spec_commit
            or not isinstance(manifest.get("source"), dict)
            or manifest["source"].get("source_sha256") != source_sha
            or manifest["source"].get("source_lock_commit") != lock_commit
            or packet.get("result") != nested
            or not isinstance(packet_source, dict)
            or packet_source.get("source_sha256") != source_sha
            or not isinstance(reproduction, dict)
            or reproduction.get("result_sha256")
                != hashlib.sha256((run_dir / "diagnostics.json").read_bytes()).hexdigest()):
        return ""
    if family_size > 1:
        # Multi-outcome families must be registered, locked, and measured as
        # the whole declared family. A single valid packet cannot claim a
        # family-adjusted result while its sibling remains absent or mutable.
        try:
            spec = yaml.safe_load((ROOT / spec_rel).read_text()) or {}
            threshold = (spec.get("falsification") or {}).get("threshold") or {}
        except (OSError, yaml.YAMLError, AttributeError):
            return ""
        family_id = diagnostics.get("family_id")
        family = packet.get("family")
        if (not isinstance(family_id, str)
                or threshold.get("family_id") != family_id
                or threshold.get("family_size") != family_size
                or lock.get("family_id") != family_id
                or not isinstance(family, dict)
                or family.get("id") != family_id
                or family.get("size") != family_size):
            return ""
        members = family.get("members")
        if (not isinstance(members, list)
                or len(members) != family_size
                or len(set(members)) != family_size
                or hypothesis_id not in members
                or any(not isinstance(member, str) for member in members)):
            return ""
        for member in members:
            matches = list((ROOT / "hypotheses").glob(f"*/{member}.yaml"))
            if len(matches) != 1:
                return ""
            member_spec_rel = matches[0].relative_to(ROOT).as_posix()
            member_add = git_bytes("log", "--diff-filter=A", "--reverse",
                                   "--format=%H", "HEAD", "--", member_spec_rel)
            if member_add is None or member_add.decode().splitlines() != [spec_commit]:
                return ""
            try:
                member_spec = yaml.safe_load(matches[0].read_text()) or {}
                member_threshold = (member_spec.get("falsification") or {}).get("threshold") or {}
            except (OSError, yaml.YAMLError, AttributeError):
                return ""
            if (member_spec.get("hypothesis_id") != member
                    or member_threshold.get("family_id") != family_id
                    or member_threshold.get("family_size") != family_size):
                return ""
            member_dir = ROOT / "engine" / "runs" / member
            member_diag_rel = (member_dir / "diagnostics.json").relative_to(ROOT).as_posix()
            member_diag_add = git_bytes("log", "--diff-filter=A", "--reverse",
                                        "--format=%H", "HEAD", "--", member_diag_rel)
            if member_diag_add is None or member_diag_add.decode().splitlines() != [run_commit]:
                return ""
            member_diag = load_json(member_dir / "diagnostics.json")
            if (member_diag.get("hypothesis_id") != member
                    or member_diag.get("family_id") != family_id
                    or member_diag.get("family_size") != family_size
                    or member_diag.get("registration_commit") != spec_commit
                    or member_diag.get("source_sha256") != source_sha
                    or member_diag.get("source_key_roster_sha256") != key_sha):
                return ""
            member_lock_commit = str(member_diag.get("source_lock_commit") or "")
            member_lock_rel = f"data/pinned_evidence/{member}.source.json"
            member_lock_bytes = git_bytes("show", f"{member_lock_commit}:{member_lock_rel}")
            member_lock_path = ROOT / member_lock_rel
            if (not re.fullmatch(r"[0-9a-f]{40}", member_lock_commit)
                    or git_bytes("merge-base", "--is-ancestor", spec_commit, member_lock_commit) is None
                    or git_bytes("merge-base", "--is-ancestor", member_lock_commit, run_commit) is None
                    or member_lock_bytes is None
                    or not member_lock_path.is_file()
                    or member_lock_bytes != member_lock_path.read_bytes()):
                return ""
            try:
                member_lock = json.loads(member_lock_bytes)
            except (TypeError, ValueError):
                return ""
            if (member_lock.get("hypothesis_id") != member
                    or member_lock.get("family_id") != family_id
                    or member_lock.get("family_size") != family_size
                    or member_lock.get("registration_commit") != spec_commit
                    or member_lock.get("source_sha256") != source_sha
                    or member_lock.get("key_roster_sha256") != key_sha):
                return ""
    return verdict


def build_record(
    path: Path,
    registrations: dict[str, dict[str, Any]],
    school_score_exclusions: dict[str, str] | None = None,
    public_evidence_quarantines: dict[str, str] | None = None,
) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    doc = raw if isinstance(raw, dict) else {}
    hypothesis_id = str(doc.get("hypothesis_id") or path.stem)
    school_score_exclusions = (
        load_school_score_exclusions()
        if school_score_exclusions is None else school_score_exclusions
    )
    school_score_exclusion_reason = school_score_exclusions.get(hypothesis_id)
    public_evidence_quarantines = (
        load_public_evidence_quarantines()
        if public_evidence_quarantines is None else public_evidence_quarantines
    )
    public_evidence_quarantine_reason = public_evidence_quarantines.get(hypothesis_id)
    # The legacy pre-registration index is keyed by spec filename. One early
    # filename uses uppercase initials while its declared hypothesis_id is
    # lowercase. Resolve both forms so the ledger is stable on case-sensitive
    # Linux CI and case-insensitive macOS worktrees.
    registration = (
        registrations.get(hypothesis_id)
        or registrations.get(path.stem)
        or {}
    )
    registration_status = str(registration.get("status") or "invalid_history")

    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    if not run_dir.is_dir():
        # Match the legacy uppercase filename/run-directory spelling used by
        # one early record. Do not let filesystem case-sensitivity change the
        # published ledger.
        legacy_run_dir = ROOT / "engine" / "runs" / path.stem
        if legacy_run_dir.is_dir():
            run_dir = legacy_run_dir
    diagnostics = load_json(run_dir / "diagnostics.json")
    verdict = str(diagnostics.get("verdict") or "").strip()
    if not verdict and isinstance(diagnostics.get("result"), dict):
        verdict = immutable_source_locked_nested_verdict(
            diagnostics, hypothesis_id, run_dir, registration
        )
    correction = diagnostics.get("correction") or {}
    disposition = (
        str(correction.get("disposition") or "").strip()
        if isinstance(correction, dict)
        else ""
    )
    detector_findings = audit_integrity_detectors.scan_diagnostics(diagnostics).get("findings") or []
    card_path = run_dir / "result_card.md"
    card_text = (
        card_path.read_text(encoding="utf-8", errors="replace")
        if card_path.exists()
        else ""
    )
    diagnostic_text = " ".join(
        str(verdict if key == "verdict" else diagnostics.get(key) or "")
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
    if detector_findings:
        exclusion_reasons.append("integrity_detector_flagged")
    if public_evidence_quarantine_reason is not None:
        exclusion_reasons.append("external_integrity_quarantine")
    if disposition == "quarantined_pending_v2":
        exclusion_reasons.append("audit_quarantined_pending_v2")
    elif disposition == "capped_partial_pending_v2":
        # The stored directional verdict has not yet been rescored as partial.
        exclusion_reasons.append("audit_verdict_rescore_pending_v2")

    public_visible = not exclusion_reasons
    # Public calibration can remain inspectable without scoring later-attached
    # school links. A zero weight alone would leave raw wins and tested counts.
    school_score_eligible = (
        school_score_eligible_for_public_run(public_visible, correction)
        and school_score_exclusion_reason is None
    )
    evidence_type = str(doc.get("evidence_type") or "unspecified")
    screen_or_descriptive_rescope = disposition in {
        "rescoped_screen_positive",
        "rescoped_descriptive",
        "descriptive_calibration_only",
    }
    # A run can document a conservative design-completeness cap. This field
    # only downgrades causal records; it can never grant public visibility or
    # elevate an archive/calibration record to featured.
    run_tier_recommendation = str(
        diagnostics.get("evidence_tier_recommendation") or ""
    ).strip().lower()
    scoreboard_weight_cap = (
        0.0 if public_evidence_quarantine_reason is not None
        else 0.0 if public_visible and not school_score_eligible
        else 0.25 if screen_or_descriptive_rescope else None
    )

    if (
        public_visible
        and evidence_type == "causal"
        and not screening
        and not screen_or_descriptive_rescope
        and school_score_eligible
        and run_tier_recommendation != "calibration"
    ):
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
        # Publish the explicit exception; absence retains the normal public rule.
        **({"school_score_eligible": False}
           if (public_visible and not school_score_eligible)
           or public_evidence_quarantine_reason is not None else {}),
        **({"school_score_exclusion_reason": school_score_exclusion_reason}
           if school_score_exclusion_reason is not None else {}),
        **({"public_evidence_quarantine_reason": public_evidence_quarantine_reason}
           if public_evidence_quarantine_reason is not None else {}),
        "reference_set": reference_set,
        "reference_note": reference_note if reference_set else None,
        "registration_status": registration_status,
        "evidence_type": evidence_type,
        "verdict_bucket": verdict_bucket(verdict) if verdict else "missing",
        "estimator_floor": "fail" if estimator_failures else "pass",
        "estimator_floor_failures": estimator_failures,
        "audit_disposition": disposition or None,
        "run_tier_recommendation": run_tier_recommendation or None,
        "integrity_detector_findings": sorted(
            {str(finding.get("detector")) for finding in detector_findings}
        ),
        "scoreboard_weight_cap": scoreboard_weight_cap,
        "screening_flags": screening,
        "exclusion_reasons": sorted(set(exclusion_reasons)),
        "canonical_url": (
            f"https://framework.ieset.org/h/{hypothesis_id}/"
        ),
    }


def build() -> dict[str, Any]:
    registrations = registration_rows()
    school_score_exclusions = load_school_score_exclusions()
    public_evidence_quarantines = load_public_evidence_quarantines()
    records = [
        build_record(path, registrations, school_score_exclusions, public_evidence_quarantines)
        for path in hypothesis_files()
    ]
    unknown_exclusions = set(school_score_exclusions) - {
        str(row["hypothesis_id"]) for row in records
    }
    if unknown_exclusions:
        raise ValueError(
            "school-score exclusions reference unknown hypothesis IDs: "
            + ", ".join(sorted(unknown_exclusions))
        )
    unknown_quarantines = set(public_evidence_quarantines) - {
        str(row["hypothesis_id"]) for row in records
    }
    if unknown_quarantines:
        raise ValueError(
            "public-evidence quarantines reference unknown hypothesis IDs: "
            + ", ".join(sorted(unknown_quarantines))
        )
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
                "estimator floor passed; causal evidence type; no screening "
                "markers or documented calibration cap."
            ),
            "calibration": (
                "Strict registration and public method gate passed, but the design "
                "is associational, descriptive, canonical-case, screening-grade, "
                "or has a documented causal-design completeness cap."
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
            "integrity_disposition": (
                "Live detector findings, explicit quarantine, and unresolved verdict "
                "rescores withhold public credit. Rescoped screens stay inspectable "
                "as calibration evidence with at most a 0.25 scoreboard weight cap; "
                "an explicit school_score_eligible=false or school_score_credit=0 "
                "keeps links visible but excludes school wins, losses, tested counts, and scores."
            ),
            "school_score_exclusions": (
                "A separate explicit registry can hold school score credit for immutable "
                "calibration runs. It changes scoring only; the original preregistered "
                "analysis and result artifacts remain unchanged."
            ),
            "public_evidence_quarantines": (
                "A separate explicit registry withholds public visibility and school "
                "credit when a saved result does not measure its named outcome. "
                "Frozen specifications and run artifacts remain unchanged."
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
