#!/usr/bin/env python3
"""Replication — EU post-2021 gas shock industrial output impact.

Treatment: high-gas-exposure EU economies, treated 2022 (post-invasion gas spike).
Outcome: log industrial value added (WDI NV.IND.TOTL.KD).
Estimator: Callaway-Sant'Anna staggered DiD.

Notes: a single common treatment year (2022) for a treated set, control = non-EU
peers. Continuous-intensity gas-exposure interaction is NOT in the differences
ATTgt v0.3 simple API; we use the binary EU-vs-non-EU specification as primary.
"""
from __future__ import annotations

import json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib_did_cs import REPO_ROOT, load_wdi, cs_did, write_result_card

warnings.filterwarnings("ignore")
RUN_ID = "eu_post_2021_gas_shock_industrial_output_impact"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

# Treated: high-gas-exposure EU economies (German, Italian, Polish, etc., heavy pipeline-gas reliance)
TREATED = ["DEU", "ITA", "POL", "AUT", "BEL", "NLD", "ESP", "FRA"]
# Controls: non-EU peers
CONTROLS = ["USA", "GBR", "JPN", "KOR", "CAN", "AUS", "NOR", "CHE"]
TREATMENT_YEAR = 2022
PERIOD = (2010, 2024)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"hypothesis_id": RUN_ID, "estimator": "did_callaway_santanna",
                "treatment_year": TREATMENT_YEAR, "treated": TREATED, "controls": CONTROLS,
                "inputs": {}}

    ind, p1, h1 = load_wdi("NV.IND.TOTL.KD", "ind_va")  # industrial VA (real)
    pop, p2, h2 = load_wdi("SP.POP.TOTL", "pop")
    manifest["inputs"]["industrial_va"] = {"vintage": p1, "sha256": h1}
    manifest["inputs"]["pop"] = {"vintage": p2, "sha256": h2}

    df = ind.merge(pop, on=["country", "year"], how="inner")
    df = df[df["country"].isin(TREATED + CONTROLS)]
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])]
    df["log_ind_va_pc"] = np.log(df["ind_va"] / df["pop"])
    df["cohort"] = df["country"].map(lambda c: TREATMENT_YEAR if c in TREATED else np.nan)
    df = df.dropna(subset=["log_ind_va_pc"]).reset_index(drop=True)

    overall, event, cohort_agg, summary = cs_did(df, "log_ind_va_pc")

    out = {
        "method": "differences.ATTgt",
        "n_treated_countries": len(TREATED),
        "n_control_countries": len([c for c in CONTROLS if c in df["country"].unique()]),
        "n_obs": int(len(df)),
        "period": list(PERIOD),
        "outcome": "log industrial VA per capita (constant USD)",
        "expected_sign": "negative",
        "overall_att": {"raw": overall, "summary": summary},
        "event_study": event,
        "by_cohort": cohort_agg,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(out, indent=2, default=str))
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    falsification = """
Not supported if (a) the interaction of post-2021Q4 × gas-exposure is zero or
positive at p<0.10 on industrial production (should be negative), OR (b) the
effect vanishes after controlling for oil price and COVID residual, OR (c) the
synthetic-control DEU post-shock gap is within the 95th percentile of placebo
gaps. This run executes the binary EU-vs-non-EU CS-DiD piece.
""".strip()
    write_result_card(OUT_DIR / "result_card.md", RUN_ID, out, falsification)
    print("done", RUN_ID)


if __name__ == "__main__":
    main()
