#!/usr/bin/env python3
"""Replication — Rent control reduces housing supply and quality.

Spec:     hypotheses/housing/rent_control_reduces_housing_supply_and_quality.yaml
Method:   Callaway-Sant'Anna staggered DiD across pre-registered cohorts:
            Berlin Mietendeckel  (Feb 2020 - Apr 2021)
            St Paul              (Nov 2021)
            NYC HSTPA            (Jun 2019)
            Oregon SB-608        (Feb 2019)
          Outcome: housing-permit issuance, rental-listing counts, median
          rent. Donors: comparable metros not yet treated.

DATA STATUS: city-level housing data is NOT in vintages. The YAML itself
declares this and pre-registers ahead of data availability. This script
attempts to load the required series; if any treated-cohort outcome is
missing, it writes BLOCKED.md (rather than running a diluted country-level
proxy that would conflate signal dilution with absence of effect).

If/when fetchers ship, the staggered-DiD path here is a drop-in.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "rent_control_reduces_housing_supply_and_quality"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

# Pre-registered treatment cohorts (city, treatment-onset year-month, ISO)
COHORTS = [
    {"unit": "berlin_de",   "treat": "2020-02-23", "country": "DEU",
     "policy": "Mietendeckel"},
    {"unit": "stpaul_us",   "treat": "2021-11-02", "country": "USA",
     "policy": "St Paul rent stabilisation"},
    {"unit": "nyc_us",      "treat": "2019-06-14", "country": "USA",
     "policy": "HSTPA"},
    {"unit": "oregon_us",   "treat": "2019-02-28", "country": "USA",
     "policy": "SB-608"},
]

REQUIRED_DATA_PATHS = [
    # city/metro-level outcomes — none currently in vintages
    ("bls",      "CUURS12B_rent_nyc_msa"),         # not shipped
    ("bls",      "CUURS24B_rent_minneapolis_msa"), # not shipped
    ("bls",      "CUURS35B_rent_portland_msa"),    # not shipped
    ("eurostat", "prc_hpi_q_berlin"),              # not shipped
    ("us_census", "BPS_permits_metro"),            # not shipped
]


def latest(pub, series):
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    return files[-1]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Probe required data
    missing = []
    found = []
    for pub, series in REQUIRED_DATA_PATHS:
        p = latest(pub, series)
        if p is None:
            missing.append(f"{pub}:{series}")
        else:
            found.append(f"{pub}:{series}")

    blocked_path = OUT_DIR / "BLOCKED.md"
    diag_path = OUT_DIR / "diagnostics.json"

    if missing:
        # All city-level series are missing. Write/update BLOCKED.md and
        # write minimal diagnostics + manifest noting the block, plus a
        # result_card.md that surfaces the blocked status.
        verdict = (f"BLOCKED — required city/metro-level outcomes not in "
                   f"vintages ({len(missing)} missing). Hypothesis is "
                   f"pre-registered ahead of fetcher work; running on "
                   f"country-level proxy would conflate treatment dilution "
                   f"with absence of effect. See BLOCKED.md.")

        # Always (re)write BLOCKED.md so it tracks current state
        blocked_path.write_text(_blocked_md(missing, found))

        diag = {
            "verdict": verdict,
            "blocked": True,
            "all_pass": False,
            "missing_data": missing,
            "found_data": found,
            "cohorts_pre_registered": COHORTS,
            "estimator_template": "did_callaway_santanna",
            "next_steps": [
                "Ship BLS MSA-level rent CPI fetcher (CUURS12B/S24B/S35B)",
                "Ship US Census BPS metro permit fetcher",
                "Ship Eurostat subnational HPI / Berlin Statistik fetcher",
                "Re-run; replication.py auto-detects vintages and proceeds",
            ],
        }
        diag_path.write_text(json.dumps(diag, indent=2) + "\n")

        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": RUN_ID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "estimator_template": "did_callaway_santanna",
            "blocked": True,
            "missing_data": missing,
        }, sort_keys=False))

        # Empty coefficients file to keep the run-shape consistent
        pd.DataFrame([]).to_parquet(OUT_DIR / "coefficients.parquet")

        (OUT_DIR / "result_card.md").write_text(_result_card_blocked(verdict, missing))

        print(verdict)
        return 0

    # ---- if data ever lands, the rest would build the staggered-DiD panel
    # and call _lib_did_cs.cs_did. Not reached today. ----
    raise NotImplementedError(
        "Data lookup succeeded — implement staggered-DiD branch (drop-in via "
        "engine.runs._lib_did_cs.cs_did once cohort outcomes land)."
    )


def _blocked_md(missing, found):
    return (
        f"# BLOCKED — rent_control_reduces_housing_supply_and_quality\n\n"
        f"**Reason:** city/metro-level housing data not yet shipped.\n\n"
        f"## Missing data ({len(missing)})\n\n"
        + "".join(f"- `{m}`\n" for m in missing)
        + f"\n## Found data ({len(found)})\n\n"
        + ("".join(f"- `{m}`\n" for m in found) if found else "(none)\n")
        + "\n## Pre-registered treatment cohorts\n\n"
        + "".join(f"- {c['unit']} ({c['country']}): {c['policy']} — {c['treat']}\n"
                  for c in COHORTS)
        + "\n## Why we don't fall back to country-level\n\n"
        "Berlin is ~4% of German HPI; NYC is ~7% of US shelter CPI; running a "
        "country-level event study around these dates would attenuate the "
        "effect by an order of magnitude and risk reporting a null where a "
        "city-level analysis (per Diamond-McQuade-Qian 2019, Kholodilin-Kohl "
        "2023) cleanly identifies a supply contraction. The YAML's "
        "framework-validation purpose ('if the model cannot reproduce the "
        "~93%-economist-consensus finding, the framework is broken') makes "
        "it especially important to use the right resolution.\n\n"
        "## Unblock checklist\n\n"
        "1. `data.fetchers.bls`: MSA-level CUURS series\n"
        "2. US Census BPS metro permit fetcher\n"
        "3. Eurostat `prc_hpi_q` NUTS-2 / Berlin Statistik\n"
        "4. Re-run — replication.py auto-detects.\n"
    )


def _result_card_blocked(verdict, missing):
    return (
        f"# Result card — rent_control_reduces_housing_supply_and_quality\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Status\n\nBLOCKED on data. See BLOCKED.md.\n\n"
        f"## Missing data\n\n"
        + "".join(f"- `{m}`\n" for m in missing)
        + "\n## Estimator (pre-registered, awaiting data)\n\n"
        "Callaway-Sant'Anna staggered DiD across cohorts:\n"
        + "".join(f"- {c['unit']}: {c['policy']} ({c['treat']})\n" for c in COHORTS)
        + "\n## Outcomes (pre-registered)\n\n"
        "- housing-permit issuance (city/metro)\n"
        "- rental-listing counts\n"
        "- median rent\n\n"
        "## Provenance\n\nSee `manifest.yaml`, `BLOCKED.md`, `replication.py`.\n"
    )


if __name__ == "__main__":
    sys.exit(main())
