#!/usr/bin/env python3
"""Read-only replay of this run using its three pinned, hash-checked vintages."""
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
import graduate_eurostat_household_energy_panels_2026_05_15 as original  # noqa: E402

SPEC = "hypotheses/energy/eurostat_household_electricity_price_consumption_panel.yaml"
SPEC_SHA256 = "03816fdca3d3f4fd4fcbd6ddfa13d54aad67af4ea85113201e8bfb91213f8702"
INPUTS = {
    ("world_bank_wdi", "NE.CON.PRVT.KD.ZG"): (
        "data/vintages/world_bank_wdi/NE.CON.PRVT.KD.ZG@2026-04-30T114957Z.parquet",
        "4ed47e5b56cd181ff3943be83e41c41d2bd6a23a857efa658c6cd9f41e5f4d56",
    ),
    ("eurostat", "nrg_pc_204"): (
        "data/vintages/eurostat/nrg_pc_204@2026-05-15T170020Z.parquet",
        "f49495b93f06637ac78106f3630005eef7bea6a5a0cd12d431c505f902a7bd2e",
    ),
    ("world_bank_wdi", "NY.GDP.PCAP.KD.ZG"): (
        "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-05-05T194650Z.parquet",
        "3bd65e60a77a1ad1cddeb9847cc579508c7e0f1c5e920c507b6953478f9604cf",
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
    checked_path(SPEC, SPEC_SHA256)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if spec["falsification"]["rule"] != (
        "SUPPORTED if treatment coefficient has the predicted sign at p<0.10; "
        "REFUTED if opposite sign at p<0.10; otherwise PARTIAL."
    ):
        raise AssertionError("The frozen falsification rule changed")

    pinned = {key: checked_path(*value) for key, value in INPUTS.items()}
    manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text())
    declared = {
        entry["vintage_file"] for entry in manifest["vintages"]
    }
    if declared != {relative for relative, _sha in INPUTS.values()}:
        raise AssertionError("Run manifest differs from pinned inputs")

    # The original batch runner's `latest` lookup is deliberately replaced in
    # memory, so a newer local vintage cannot silently change this replay.
    original.latest = lambda publisher, series: pinned[(publisher, series)]
    price, _ = original.household_price()
    gdp, _ = original.wdi("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth")
    consumption, _ = original.wdi("NE.CON.PRVT.KD.ZG", "household_consumption_growth")
    base = price.merge(gdp, on=["country", "year"], how="inner")
    base = base[
        (base["year"] >= original.PERIOD[0]) &
        (base["year"] <= original.PERIOD[1])
    ].copy()
    panel = base.merge(consumption, on=["country", "year"], how="inner")
    estimate = original.run_fe(
        panel, "household_consumption_growth", "household_electricity_price"
    )
    diagnostics = json.loads((RUN_DIR / "diagnostics.json").read_text())
    compare_estimate(estimate, diagnostics["estimate"])
    label, reason = original.verdict(estimate, "-")
    if (label, reason) != (
        diagnostics["verdict_label"], diagnostics["verdict_reason"]
    ):
        raise AssertionError("Replayed verdict differs from stored verdict")
    if diagnostics["verdict"] != f"{label} - {reason}":
        raise AssertionError("Stored verdict text differs from replay")
    print(f"Verified exact estimate and {label} verdict from pinned inputs; no artifacts written")


if __name__ == "__main__":
    main()
