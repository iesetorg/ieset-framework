"""Tests for the derived-panel checklist runs (2026-09-03 hypothesis wave).

Re-drives the shipped evaluator functions over the real panel parquets and
asserts the recomputed metric statuses and verdicts match the landed run
artifacts — no re-implementation of the scoring logic, no hard-coded verdicts.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

NINE = [
    "sf_rent_control_1994_small_multifamily_expansion",
    "st_paul_rent_control_2021_permit_collapse_event",
    "catalonia_reference_rent_contract_supply_response_2020",
    "stockholm_rent_queue_allocation_distortion",
    "france_reference_rents_paris_lille_phase_in",
    "argentina_milei_disinflation_monetary_reconfiguration_2023_2028",
    "el_salvador_bukele_security_growth_equilibrium_2019_2026",
    "anglo_money_growth_public_crowding_stagnation_2019_2024",
    "welfare_anglo_transfer_ratchet_private_stagnation_2019_2024",
]


def load_runner():
    import sys

    if "derived_panel_runner" in sys.modules:
        return sys.modules["derived_panel_runner"]
    path = REPO_ROOT / "scripts" / "run_derived_panel_checklist.py"
    spec = importlib.util.spec_from_file_location("derived_panel_runner", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def landed(hypothesis_id: str) -> dict:
    return json.loads(
        (REPO_ROOT / "engine" / "runs" / hypothesis_id / "diagnostics.json").read_text()
    )


def test_all_nine_runs_have_complete_artifacts():
    for hypothesis_id in NINE:
        run_dir = REPO_ROOT / "engine" / "runs" / hypothesis_id
        for artifact in ("result_card.md", "diagnostics.json", "manifest.yaml", "replication.py"):
            assert (run_dir / artifact).is_file(), (hypothesis_id, artifact)
        card = (run_dir / "result_card.md").read_text()
        verdict_line = [l for l in card.splitlines() if l.startswith("**Verdict:**")]
        assert verdict_line, hypothesis_id
        assert any(
            token in verdict_line[0]
            for token in ("SUPPORTED", "REFUTED", "INCONCLUSIVE_DATA_PENDING", "PARTIAL")
        ), (hypothesis_id, verdict_line[0])


def test_recomputed_metrics_match_landed_cards():
    runner = load_runner()
    for hypothesis_id in NINE:
        results = runner.EVALUATORS[hypothesis_id]()
        by_id = {r.metric_id: r for r in results}
        diagnostics = landed(hypothesis_id)
        landed_by_id = {m["metric_id"]: m for m in diagnostics["metrics"]}
        assert set(by_id) == set(landed_by_id), hypothesis_id
        for metric_id, recomputed in by_id.items():
            assert recomputed.status == landed_by_id[metric_id]["status"], (
                hypothesis_id, metric_id, recomputed.status, landed_by_id[metric_id]["status"]
            )
            if recomputed.observed_value is not None:
                assert abs(
                    recomputed.observed_value - landed_by_id[metric_id]["observed_value"]
                ) < 1e-9, (hypothesis_id, metric_id)


def test_recomputed_verdicts_match_landed_cards():
    runner = load_runner()
    for hypothesis_id in NINE:
        results = runner.EVALUATORS[hypothesis_id]()
        diagnostics = landed(hypothesis_id)
        if hypothesis_id in runner.PATTERN_VERDICTS:
            verdict, _ = runner.PATTERN_VERDICTS[hypothesis_id](results)
        else:
            falsification = diagnostics["thresholds"]
            verdict, _ = runner.checklist_verdict(
                results,
                falsification["support_threshold"],
                falsification["refute_threshold"],
            )
        assert verdict == diagnostics["verdict"], (hypothesis_id, verdict, diagnostics["verdict"])


def test_pending_metrics_name_their_missing_source():
    for hypothesis_id in NINE:
        diagnostics = landed(hypothesis_id)
        for metric in diagnostics["metrics"]:
            if metric["status"].startswith("PENDING"):
                text = (metric.get("notes") or "") + (metric.get("source") or "")
                assert len(text.strip()) > 20, (hypothesis_id, metric["metric_id"], "PENDING without a named gap")
                assert metric["observed_value"] is None or metric["status"] == "PENDING_EVAL"


def test_detector_classes_clean_on_new_runs():
    runner = load_runner()  # noqa: F841  (imports exercise the shipped module)
    import subprocess

    for hypothesis_id in NINE:
        proc = subprocess.run(
            [
                str(REPO_ROOT / "venv" / "bin" / "python"),
                str(REPO_ROOT / "scripts" / "audit_integrity_detectors.py"),
                "--run", hypothesis_id,
            ],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        summary = proc.stdout.strip().splitlines()[-1]
        assert summary.endswith("0 findings"), (hypothesis_id, summary)


def test_argentina_scoring_uses_observed_cpi_only():
    """The shipped evaluator must never score forward-filled CPI months."""
    runner = load_runner()
    results = runner._arg()
    by_id = {r.metric_id: r for r in results}
    months = by_id["monthly_cpi_stabilised"].notes
    # 18 observed trailing months from the panel (panel ends 2026-09 with
    # two unobserved CPI months) — the count must reflect observed rows only
    assert "of last 18 observed months" in months
    panel = runner.load_panel(runner.ARG_PANEL)
    observed = panel[panel["cpi_observed"] == True]  # noqa: E712
    below = int((observed["cpi_mom_pct"].tail(18) < 3.0).sum())
    assert below == by_id["monthly_cpi_stabilised"].observed_value
