#!/usr/bin/env python3
"""Fail-closed source preflight for the frozen Czech–Slovak two-spec design."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_panel_fe  # noqa: E402
import frozen_source_lock  # noqa: E402

HID = "czech_slovak_market_transition_comparison"
RUN_DIR = ROOT / "engine" / "runs" / HID
CHANNELS = ["market_institutions_index", "fdi_inflows_pct_gdp", "govt_consumption_pct_gdp"]
ENDPOINTS = (1993, 2024)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior() -> None:
    target = RUN_DIR / "historical" / "2026-05-03_duplicate_control"
    target.mkdir(parents=True, exist_ok=True)
    names = ("diagnostics.json", "result_card.md", "replication.py")
    for name in names:
        source, dest = RUN_DIR / name, target / name
        if source.exists() and not dest.exists():
            shutil.copy2(source, dest)
    manifest = target / "sha256.json"
    if not manifest.exists():
        manifest.write_text(json.dumps(
            {name: sha256_file(target / name) for name in names if (target / name).exists()},
            indent=2, sort_keys=True,
        ) + "\n")


def build() -> tuple[dict, str]:
    found = run_panel_fe.load_spec(HID)
    if not found:
        raise RuntimeError("frozen v1 spec missing")
    spec_path, spec = found
    if spec.get("version") != 1 or (spec.get("estimator") or {}).get("template") != "panel_fe_decomposition":
        raise RuntimeError("frozen v1 two-spec contract changed")
    if [part["name"] for part in spec["variables"]["decomposition_channels"]] != CHANNELS:
        raise RuntimeError("frozen decomposition channels changed")
    notes = spec["estimator"]["notes"]
    if "1993 vs 2024" not in notes or "long-difference" not in notes:
        raise RuntimeError("registered 1993-to-2024 long-difference contract changed")
    panel, status = frozen_source_lock.checked_build_panel(HID, spec)
    panel = run_panel_fe.filter_sample(panel, spec).sort_values(["country_iso3", "year"])
    declared = sorted(spec["sample"]["countries"])
    endpoint_rows = []
    for country in declared:
        for year in ENDPOINTS:
            match = panel[(panel.country_iso3 == country) & (panel.year == year)]
            if len(match) != 1:
                missing = ["real_gdp_pc", *CHANNELS]
            else:
                missing = [name for name in ["real_gdp_pc", *CHANNELS]
                           if match[name].isna().iloc[0]]
            endpoint_rows.append({"country_iso3": country, "year": year,
                                  "missing": missing})
    complete_countries = [country for country in declared if not any(
        row["missing"] for row in endpoint_rows if row["country_iso3"] == country
    )]
    # A level_at_1993 control should be constant by country, hence absorbed by
    # country FE. The generic loader instead kept the contemporaneous series.
    current_initial_var = panel.groupby("country_iso3").initial_gdp_pc_1993.nunique()
    wrongly_time_varying = sorted(current_initial_var[current_initial_var > 1].index.tolist())
    reason = (
        "registered 1993-to-2024 long-difference cannot be estimated: "
        "Fraser market-institutions endpoints and 2024 government-consumption endpoints are absent"
    )
    digest = hashlib.sha256(panel.to_csv(index=False, float_format="%.17g", na_rep="NA").encode()).hexdigest()
    diagnostics = {
        "hypothesis_id": HID, "template": "panel_fe_decomposition",
        "verdict": f"INCONCLUSIVE_DATA_PENDING — {reason}",
        "verdict_label": "INCONCLUSIVE_DATA_PENDING", "verdict_reason": reason,
        "runner": "scripts/rerun_czech_slovak_frozen.py",
        "falsification_rule_text": spec["falsification"]["rule"],
        "estimate": {"error": reason, "method": "not fitted: frozen second specification lacks endpoints"},
        "frozen_rule_components": {
            "panel_market_plus_fdi_exceeds_government": None,
            "panel_market_coefficient_positive_p_below_0_10": None,
            "1993_to_2024_long_difference_replicates_channels": None,
        },
        "preflight": {
            "declared_countries": declared,
            "long_difference_endpoints": list(ENDPOINTS),
            "endpoint_rows": endpoint_rows,
            "countries_with_complete_both_endpoints": complete_countries,
            "generic_initial_gdp_control_wrongly_time_varying_countries": wrongly_time_varying,
            "panel_rows": len(panel),
        },
        "data_status": status,
        "provenance": {
            "spec_path": str(spec_path.relative_to(ROOT)), "spec_sha256": sha256_file(spec_path),
            "input_panel_sha256": digest,
            "prior_run": "historical/2026-05-03_duplicate_control",
            **frozen_source_lock.provenance(HID),
        },
    }
    card = "\n".join([
        f"# Result card — {HID}", "",
        f"**Verdict:** {diagnostics['verdict']}", "",
        "## Frozen two-spec preflight", "",
        f"The frozen two-spec design requires a panel decomposition and a 1993-to-2024 long-difference across {', '.join(CHANNELS)}. None of the {len(declared)} declared countries have all three channels at both endpoints.",
        "The Fraser market-institutions series has no 1993 or 2024 endpoint for Czechia and Slovakia; the WDI government-consumption series lacks 2024 values. Substituting nearby years would change the frozen test.",
        f"The old generic panel run also treated a 1993 baseline GDP control as a time-varying series from the same WDI GDP source in {len(wrongly_time_varying)} countries. Its R²=1 near-zero estimate cannot grade the frozen design. That run is preserved under `historical/` and receives no evidence credit.", "",
        "All frozen coefficient and long-difference decisions remain unassessable until the declared endpoints exist or a new prospective design is registered.", "",
        f"Spec SHA-256: `{sha256_file(spec_path)}`", f"Input-panel SHA-256: `{digest}`", "",
    ])
    return diagnostics, card


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?", default=HID)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.hypothesis_id != HID:
        parser.error(f"this runner only handles {HID}")
    diagnostics, card = build()
    manifest = frozen_source_lock.manifest_text(diagnostics)
    if args.check:
        existing = json.loads((RUN_DIR / "diagnostics.json").read_text())
        if (existing != diagnostics or (RUN_DIR / "result_card.md").read_text() != card
                or (RUN_DIR / "manifest.yaml").read_text() != manifest):
            print("FAIL: exact replay artifacts stale", file=sys.stderr)
            return 1
    else:
        snapshot_prior()
        (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n")
        (RUN_DIR / "result_card.md").write_text(card)
        (RUN_DIR / "manifest.yaml").write_text(manifest)
    print(f"{HID}: {diagnostics['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
