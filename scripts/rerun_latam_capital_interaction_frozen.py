#!/usr/bin/env python3
"""Re-estimate the frozen LATAM capital-openness interaction claim.

The original generic panel run graded a main effect after its interaction
construction failed. This exact replay estimates the two registered outcomes,
the FDI-by-WGI interaction, and all three registered decision components.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_panel_fe  # noqa: E402
import frozen_source_lock  # noqa: E402

HID = "latam_extra_capital_account_openness_panel_1990_2024"
RUN_DIR = ROOT / "engine" / "runs" / HID
OUTCOME_GROWTH = "log_gdp_pc_constant"
OUTCOME_VOLATILITY = "real_gdp_growth_volatility"
FDI = "fdi_inflow_share_gdp"
WGI = "wgi_government_effectiveness"
INTERACTION = "fdi_x_wgi"
RHS = [
    FDI, WGI, INTERACTION,
    "external_debt_stock_share_gni",
    "portfolio_equity_inflow_share_gdp",
    "terms_of_trade",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_prior() -> None:
    target = RUN_DIR / "historical" / "2026-04-30_generic_fallback"
    target.mkdir(parents=True, exist_ok=True)
    source_names = ("diagnostics.json", "result_card.md", "replication.py")
    for name in source_names:
        source = RUN_DIR / name
        dest = target / name
        if source.exists() and not dest.exists():
            shutil.copy2(source, dest)
    hashes = {name: sha256_file(target / name) for name in source_names if (target / name).exists()}
    manifest = target / "sha256.json"
    if not manifest.exists():
        manifest.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")


def prepare_panel() -> tuple[pd.DataFrame, dict, dict]:
    found = run_panel_fe.load_spec(HID)
    if not found:
        raise RuntimeError(f"missing frozen spec {HID}")
    spec_path, spec = found
    if spec.get("version") != 1 or (spec.get("estimator") or {}).get("template") != "panel_fe":
        raise RuntimeError("frozen v1 panel-FE contract changed")
    rule = str((spec.get("falsification") or {}).get("rule") or "")
    if not all(part in rule for part in ("FDI-openness coefficient", "openness × WGI interaction", "macro volatility")):
        raise RuntimeError("frozen three-part falsification rule changed")
    panel, status = frozen_source_lock.checked_build_panel(HID, spec)
    panel = run_panel_fe.filter_sample(panel, spec).copy()
    # This exclusion is explicit in sample.exclusion_rules.
    panel = panel[~(panel.country_iso3.eq("VEN") & panel.year.gt(1999))].copy()
    panel = panel.sort_values(["country_iso3", "year"])
    # The generic transform() treats rolling_5yr_sd as level. Construct the
    # actual registered trailing five-observation annual-growth SD here.
    panel[OUTCOME_VOLATILITY] = panel.groupby("country_iso3", sort=False)[
        OUTCOME_VOLATILITY
    ].transform(lambda series: series.rolling(5, min_periods=5).std(ddof=1))
    panel[INTERACTION] = panel[FDI] * panel[WGI]
    if panel.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate country-year after vintage join")
    meta = {"spec_path": str(spec_path.relative_to(ROOT)), "spec_sha256": sha256_file(spec_path)}
    return panel, status, meta


def fit_outcome(panel: pd.DataFrame, outcome: str) -> dict:
    sub = panel[["country_iso3", "year", outcome, *RHS]].dropna().copy()
    if sub.country_iso3.nunique() < 6 or len(sub) < 80:
        return {"error": "insufficient complete country-year coverage for exact interaction panel"}
    indexed = sub.set_index(["country_iso3", "year"])
    model = PanelOLS(
        indexed[outcome], indexed[RHS], entity_effects=True,
        time_effects=True, drop_absorbed=False,
    )
    result = model.fit(cov_type="clustered", cluster_entity=True)
    return {
        "fdi_coefficient": float(result.params[FDI]),
        "fdi_std_error": float(result.std_errors[FDI]),
        "fdi_p_value": float(result.pvalues[FDI]),
        "fdi_x_wgi_coefficient": float(result.params[INTERACTION]),
        "fdi_x_wgi_std_error": float(result.std_errors[INTERACTION]),
        "fdi_x_wgi_p_value": float(result.pvalues[INTERACTION]),
        "n_obs": int(result.nobs),
        "n_countries": int(sub.country_iso3.nunique()),
        "countries": sorted(sub.country_iso3.unique().tolist()),
        "n_years": int(sub.year.nunique()),
        "method": "two-way PanelOLS FE; FDI x WGI; country-clustered SE",
        "time_absorbed_controls": ["us_policy_rate", "oil_price"],
    }


def decision(growth: dict, volatility: dict) -> tuple[str, dict, str]:
    if "error" in growth or "error" in volatility:
        return "INCONCLUSIVE_DATA_PENDING", {}, "required interaction outcome could not be estimated"
    components = {
        "a_fdi_growth_positive_p_below_0_10": (
            growth["fdi_coefficient"] > 0 and growth["fdi_p_value"] < 0.10
        ),
        "b_fdi_x_wgi_growth_positive": growth["fdi_x_wgi_coefficient"] > 0,
        "c_fdi_x_wgi_volatility_negative": volatility["fdi_x_wgi_coefficient"] < 0,
    }
    if all(components.values()):
        return "SUPPORTED", components, "all three frozen coefficient conditions passed"
    failed = ", ".join(key.split("_", 1)[0] for key, ok in components.items() if not ok)
    return "REFUTED", components, f"preregistered support conjunction failed at condition(s) {failed}; this is not evidence of an opposite effect"


def build() -> tuple[dict, str]:
    panel, status, meta = prepare_panel()
    growth = fit_outcome(panel, OUTCOME_GROWTH)
    volatility = fit_outcome(panel, OUTCOME_VOLATILITY)
    verdict, components, reason = decision(growth, volatility)
    declared = sorted(run_panel_fe.load_spec(HID)[1]["sample"]["countries"])
    analysed = growth.get("countries") or []
    panel_digest = hashlib.sha256(
        panel.sort_values(["country_iso3", "year"]).to_csv(
            index=False, float_format="%.17g", na_rep="NA"
        ).encode()
    ).hexdigest()
    if verdict == "REFUTED":
        reason = (f"among the {len(analysed)}/{len(declared)} declared countries with complete cases, "
                  f"{reason}")
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "template": "panel_fe",
        "runner": "scripts/rerun_latam_capital_interaction_frozen.py",
        "falsification_rule_text": run_panel_fe.load_spec(HID)[1]["falsification"]["rule"],
        "estimate": {
            "coefficient": growth.get("fdi_coefficient"),
            "std_error": growth.get("fdi_std_error"),
            "p_value": growth.get("fdi_p_value"),
            "n_obs": growth.get("n_obs"),
            "n_countries": growth.get("n_countries"),
            "method": growth.get("method", "not estimable"),
        },
        "growth_model": growth,
        "volatility_model": volatility,
        "frozen_rule_components": components,
        "sample_coverage": {
            "declared_countries": declared,
            "analysed_countries": analysed,
            "unanalysed_countries": sorted(set(declared) - set(analysed)),
            "reason": "Complete cases for all registered capital-flow signals and country-varying controls",
        },
        "data_status": status,
        "provenance": {**meta, **frozen_source_lock.provenance(HID), "input_panel_sha256": panel_digest,
                       "prior_run": "historical/2026-04-30_generic_fallback"},
    }
    card = "\n".join([
        f"# Result card — {HID}", "",
        f"**Verdict:** {diagnostics['verdict']}", "",
        "## Frozen three-part rule", "",
        f"- (a) FDI growth coefficient > 0 at p < 0.10: **{components.get('a_fdi_growth_positive_p_below_0_10')}**; coef={growth.get('fdi_coefficient')}, p={growth.get('fdi_p_value')}",
        f"- (b) FDI × WGI growth interaction > 0: **{components.get('b_fdi_x_wgi_growth_positive')}**; coef={growth.get('fdi_x_wgi_coefficient')}",
        f"- (c) FDI × WGI growth-volatility interaction < 0: **{components.get('c_fdi_x_wgi_volatility_negative')}**; coef={volatility.get('fdi_x_wgi_coefficient')}",
        "",
        "## Method and coverage", "",
        "Two-way country and year fixed effects with country-clustered uncertainty. The five-year rolling growth volatility is calculated before fitting its separate outcome model. US rate and oil price are absorbed by year effects. The historical main-effect fallback is preserved under `historical/`.",
        f"Complete-case sample: {growth.get('n_obs')} country-years, {growth.get('n_countries')}/{len(declared)} declared countries. Missing countries: {', '.join(diagnostics['sample_coverage']['unanalysed_countries']) or 'none'}.",
        "The reduced coverage limits generalization beyond the analysed countries. REFUTED means the frozen three-condition support rule failed here; it does not establish a statistically significant effect in the opposite direction.", "",
        f"Spec SHA-256: `{meta['spec_sha256']}`", f"Input-panel SHA-256: `{panel_digest}`", "",
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
        if (not frozen_source_lock.same_packet(diagnostics, existing)
                or not frozen_source_lock.same_result_card(card, (RUN_DIR / "result_card.md").read_text())
                or (RUN_DIR / "manifest.yaml").read_text() != manifest):
            print("FAIL: exact replay artifacts stale", file=sys.stderr)
            return 1
    else:
        snapshot_prior()
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n")
        (RUN_DIR / "result_card.md").write_text(card)
        (RUN_DIR / "manifest.yaml").write_text(manifest)
    print(f"{HID}: {diagnostics['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
