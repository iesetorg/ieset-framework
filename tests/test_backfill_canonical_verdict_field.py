"""Verdict-field repair must never infer a result from pending or status text."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_evidence_tiers as tiers  # noqa: E402
import backfill_canonical_verdict_field as backfill  # noqa: E402


def test_pending_label_cannot_be_promoted():
    with pytest.raises(ValueError, match="eligible explicit verdict_label"):
        backfill.prepare(
            "bis_corporate_credit_boom_investment_slowdown_panel_1970_2025",
            tiers.registration_rows(),
        )


def test_status_text_cannot_replace_missing_verdict_label():
    with pytest.raises(ValueError, match="eligible explicit verdict_label"):
        backfill.prepare(
            "oecd_pdb_tfp_growth_frontier_persistence_1970_2025",
            tiers.registration_rows(),
        )


def test_undefined_raw_gate_cannot_be_relabelled():
    with pytest.raises(ValueError, match="not a verified verdict-only repair"):
        backfill.prepare(
            "oecd_epl_growth_shock_unemployment_persistence_panel",
            tiers.registration_rows(),
        )


def test_already_repaired_run_is_not_edited_again():
    with pytest.raises(ValueError, match="verdict-only repair"):
        backfill.prepare(
            "bis_credit_gap_current_account_twin_deficit_risk",
            tiers.registration_rows(),
        )
