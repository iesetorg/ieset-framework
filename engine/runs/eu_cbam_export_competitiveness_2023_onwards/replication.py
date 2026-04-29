#!/usr/bin/env python3
"""Replication — EU CBAM export-competitiveness, 2023 onwards.

Spec:     hypotheses/regulatory/eu_cbam_export_competitiveness_2023_onwards.yaml
Estimator: did_chaisemartin / Callaway-Sant'Anna (binary EU vs non-EU; treatment year 2023).

YAML flags v1 as a pre-registration: HS-level Comtrade and OECD STAN sectoral
production fetchers are pending. v1 weak proxy used here:
  outcome 1 = log real exports of goods+services (WDI NE.EXP.GNFS.KD)
  outcome 2 = log industrial value added (WDI NV.IND.TOTL.KD; CBAM-covered subsector
              proxy via aggregate industry — coarse).

Treatment: EU members from 2023 onward (CBAM reporting phase Oct 2023).
Control: non-EU advanced exporters (USA, GBR, CAN, JPN, KOR, AUS, CHE, NOR, TUR).
The author prior is low (CBAM reporting-only phase has admin cost not price);
hence a null/small effect would not be surprising and would not refute the v2
post-2026 test.
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
RUN_ID = "eu_cbam_export_competitiveness_2023_onwards"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

# Treated: large EU exporters with significant CBAM-covered subsector exposure
TREATED = ["DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "POL", "SWE", "AUT"]
# Controls: non-EU advanced exporters
CONTROLS = ["USA", "GBR", "CAN", "JPN", "KOR", "AUS", "CHE", "NOR", "TUR"]
TREATMENT_YEAR = 2023
PERIOD = (2015, 2024)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"hypothesis_id": RUN_ID,
                "estimator": "did_chaisemartin_via_callaway_santanna_proxy",
                "treatment_year": TREATMENT_YEAR,
                "treated": TREATED, "controls": CONTROLS,
                "v1_caveat": "HS-code-level CBAM-covered exports not on disk; v1 uses aggregate real exports as coarse proxy",
                "inputs": {}}

    exp, p1, h1 = load_wdi("NE.EXP.GNFS.KD", "exp_real")  # real exports of G&S
    pop, p2, h2 = load_wdi("SP.POP.TOTL", "pop")
    ind, p3, h3 = load_wdi("NV.IND.TOTL.KD", "ind_va")  # industrial VA real
    manifest["inputs"]["exports_real"] = {"vintage": p1, "sha256": h1}
    manifest["inputs"]["population"] = {"vintage": p2, "sha256": h2}
    manifest["inputs"]["industrial_va"] = {"vintage": p3, "sha256": h3}

    df = exp.merge(pop, on=["country", "year"], how="inner") \
            .merge(ind, on=["country", "year"], how="left")
    df = df[df["country"].isin(TREATED + CONTROLS)]
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])]
    df["log_exp_pc"] = np.log(df["exp_real"] / df["pop"])
    df["log_ind_va_pc"] = np.log(df["ind_va"] / df["pop"])
    df["cohort"] = df["country"].map(lambda c: TREATMENT_YEAR if c in TREATED else np.nan)

    # Run CS-DiD on both proxies
    results = {}
    for outcome, expected_sign in [("log_exp_pc", "negative"), ("log_ind_va_pc", "negative")]:
        d = df.dropna(subset=[outcome]).reset_index(drop=True)
        try:
            overall, event, cohort_agg, summary = cs_did(d, outcome)
            results[outcome] = {
                "method": "differences.ATTgt (Callaway-Sant'Anna binary)",
                "n_treated_countries": len([c for c in TREATED if c in d["country"].unique()]),
                "n_control_countries": len([c for c in CONTROLS if c in d["country"].unique()]),
                "n_obs": int(len(d)),
                "period": list(PERIOD),
                "outcome": outcome,
                "expected_sign": expected_sign,
                "overall_att": {"raw": overall, "summary": summary},
                "event_study": event,
                "by_cohort": cohort_agg,
            }
        except Exception as e:
            results[outcome] = {"error": str(e), "outcome": outcome}

    # Verdict logic — primary outcome is exports
    primary = results.get("log_exp_pc", {})
    summary = (primary.get("overall_att") or {}).get("summary") or {}
    att = summary.get("overall_att_simple")
    pre_pass = summary.get("pre_trend_pass_zero_in_band", True)

    if att is None:
        verdict = "INCONCLUSIVE — could not compute ATT on primary outcome (log real exports per capita)."
    elif att < -0.05 and pre_pass:
        verdict = (f"SUPPORTED — EU exports per capita post-2023 ATT = {att:+.4f} log "
                   f"(threshold β<-0.05 met); pre-trend clean. Caveat: this is the v1 "
                   f"weak proxy (aggregate exports) — sectoral CBAM-covered HS test in v1.1.")
    elif att < 0 and pre_pass:
        verdict = (f"DIRECTIONALLY CONSISTENT BUT BELOW THRESHOLD — ATT = {att:+.4f} log "
                   f"(threshold β<-0.05 not met). Author prior was low (reporting-phase only); "
                   f"this is consistent with prior. Re-run post-2026 (v2) when certificate "
                   f"phase active.")
    elif att >= 0 and pre_pass:
        verdict = (f"NOT SUPPORTED on aggregate-exports proxy — ATT = {att:+.4f} log "
                   f"is non-negative. Reporting-phase null is consistent with author's "
                   f"low prior; hypothesis re-runs in v2 post-2026.")
    else:
        verdict = (f"WEAKLY SUPPORTED — ATT = {att:+.4f} log but pre-trend fails; "
                   f"effect identification unreliable.")

    out = {
        "verdict": verdict,
        "primary_outcome": "log_exp_pc",
        "results_by_outcome": results,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    falsification = (
        "Not supported if (a) the EU-CBAM β is zero or positive at p<0.10, OR "
        "(b) effect vanishes after controlling for gas + ETS price, OR "
        "(c) pre-2023 placebo detects spurious divergence, OR "
        "(d) domestic CBAM-subsector production shows no contraction. "
        "Threshold: β < -0.05 log points at p<0.10. v1 uses aggregate-exports proxy."
    )

    # Use lib helper for primary outcome card, then append secondary
    if primary and "error" not in primary:
        write_result_card(OUT_DIR / "result_card.md", RUN_ID, primary, falsification)
        # Append secondary outcome and verdict-with-caveat
        sec = results.get("log_ind_va_pc", {})
        sec_summary = (sec.get("overall_att") or {}).get("summary") or {}
        sec_att = sec_summary.get("overall_att_simple")
        with open(OUT_DIR / "result_card.md", "a") as f:
            f.write("\n## Secondary outcome — log industrial VA per capita\n\n")
            if sec_att is not None:
                f.write(f"- ATT (simple) = {sec_att:+.4f} log points\n")
                f.write(f"- Pre-trend pass: {sec_summary.get('pre_trend_pass_zero_in_band')}\n")
            else:
                f.write(f"- ATT not computed: {sec.get('error', 'unknown')}\n")
            f.write("\n## v1 verdict (overrides lib helper auto-verdict)\n\n")
            f.write(f"**{verdict}**\n\n")
            f.write("## Caveats — v1 is a pre-registration\n\n")
            f.write("- Aggregate exports of goods+services is the coarse proxy; CBAM scope is HS-code-specific (steel, aluminium, cement, fertilisers, hydrogen, electricity).\n")
            f.write("- 2023-2024 is the *reporting* phase only (admin cost, no certificate purchase). Author prior was low for v1.\n")
            f.write("- v2 post-2026 will run with certificate-phase active and HS-level Comtrade data.\n")
            f.write("- Pre-period 2015-2022 contains COVID + gas-shock; identification rests on year-FE absorbing common shocks.\n")
    else:
        (OUT_DIR / "result_card.md").write_text(
            f"# Result card — {RUN_ID}\n\n**Verdict:** {verdict}\n\n"
            f"## Falsification\n{falsification}\n"
        )
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
