#!/usr/bin/env python3
"""Read-only replay of the frozen WID apex wealth-share panel trend."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_panel_fe as original  # noqa: E402

SPEC = "hypotheses/distribution/wid_top_wealth_concentration_rise_post_1980.yaml"
# Fingerprint of the run-commit analysis plan: scope, variables, estimator,
# falsification rule, claim and evidence type. Later link metadata is excluded.
PLAN_FIELDS = (
    "claim", "claim_direction", "sample", "variables", "estimator",
    "falsification", "evidence_type",
)
PLAN_SHA256 = "2f5ef1bdd55b95c569ab11e295b440e1a7dda83f3e1cab1e46593217eaab7557"
INPUTS = {
    ("wid_clean", "top01_wealth_share"): (
        "data/vintages/wid_clean/top01_wealth_share@2026-06-29T154903Z.parquet",
        "088fd7cf68520b886cf0f556c902f2b015f87a4a6d713b54ce31d0b5f88316ed",
    ),
    ("trend", "calendar_year_trend"): (
        "data/vintages/trend/calendar_year_trend@2026-06-29T162802Z.parquet",
        "c015a7ad05d9c069c9f52df537cdd6c441f469b44ca0222c5b32d64916713c15",
    ),
}


def checked_path(relative: str, expected_sha256: str) -> Path:
    path = ROOT / relative
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise AssertionError(f"SHA-256 mismatch for {relative}: {actual}")
    return path


def compare_estimate(actual: dict, stored: dict) -> None:
    if actual.keys() != stored.keys():
        raise AssertionError("Replayed estimate fields differ from stored estimate")
    for key, expected in stored.items():
        observed = actual[key]
        if isinstance(expected, float):
            if not math.isclose(observed, expected, rel_tol=1e-9, abs_tol=1e-10):
                raise AssertionError(f"{key}: replay={observed!r}, stored={expected!r}")
        elif observed != expected:
            raise AssertionError(f"{key}: replay={observed!r}, stored={expected!r}")


def main() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    plan = {key: spec.get(key) for key in PLAN_FIELDS}
    plan_sha = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if plan_sha != PLAN_SHA256:
        raise AssertionError(f"Run-commit analysis plan changed: {plan_sha}")
    if spec["sample"]["period"] != [1980, 2024]:
        raise AssertionError("Expected study period changed")

    pinned = {key: checked_path(*value) for key, value in INPUTS.items()}
    # Restrict the generic loader to the two run-time vintages. Any new file in
    # data/vintages is irrelevant to this historical replay.
    original.latest_vintage = lambda publisher, series: pinned[(publisher, series)]
    panel, status = original.build_panel(spec)
    if status["variables_missing"] or len(status["variables_loaded"]) != 2:
        raise AssertionError(f"Unexpected variable loading: {status}")
    panel = original.filter_sample(panel, spec)
    estimate = original.run_panel_ols(
        panel, spec, "top_0p1_net_personal_wealth_share", "calendar_year_trend"
    )
    diagnostics = json.loads((RUN_DIR / "diagnostics.json").read_text())
    if status != diagnostics["data_status"]:
        raise AssertionError("Resolved variables differ from stored diagnostics")
    compare_estimate(estimate, diagnostics["estimate"])
    label, reason = original.verdict_from_estimate(
        estimate,
        original.infer_claim_direction(spec, "top_0p1_net_personal_wealth_share"),
        alpha=original.infer_significance_alpha(spec),
    )
    if (label, reason) != (
        diagnostics["verdict_label"], diagnostics["verdict_reason"]
    ):
        raise AssertionError("Replayed verdict differs from stored verdict")
    if diagnostics["verdict"] != f"{label} — {reason}":
        raise AssertionError("Stored verdict text differs from replay")
    print(f"Verified exact estimate and {label} verdict from pinned inputs; no artifacts written")


if __name__ == "__main__":
    main()
