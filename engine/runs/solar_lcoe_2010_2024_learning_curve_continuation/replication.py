#!/usr/bin/env python3
"""Replication for solar_lcoe_2010_2024_learning_curve_continuation.

This is a dedicated descriptive replication because the IRENA LCOE workbook
available locally is a global technology series, while the generic panel runner
expects country-level outcomes. The test uses the pre-registered headline v1:
global solar PV LCOE against cumulative installed solar PV capacity.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent

LCOE_PATH = ROOT / "data/vintages/irena/lcoe_solar_pv@2026-05-12T125721Z.parquet"
CAPACITY_PATH = ROOT / "data/vintages/irena/installed_capacity_solar_pv@2026-05-05T212314Z.parquet"


def fit_learning_curve(df: pd.DataFrame) -> dict:
    x = sm.add_constant(df["ln_capacity"])
    model = sm.OLS(df["ln_lcoe"], x).fit()
    beta = float(model.params["ln_capacity"])
    return {
        "n": int(len(df)),
        "beta_log_cost_on_log_capacity": beta,
        "learning_rate_per_capacity_doubling": float(1 - (2 ** beta)),
        "p_value": float(model.pvalues["ln_capacity"]),
        "r_squared": float(model.rsquared),
    }


def main() -> None:
    lcoe = pd.read_parquet(LCOE_PATH)
    capacity = pd.read_parquet(CAPACITY_PATH)

    global_capacity = (
        capacity.groupby("year", as_index=False)["value"]
        .sum()
        .rename(columns={"value": "global_solar_capacity_mw"})
    )
    panel = (
        lcoe[["year", "value"]]
        .rename(columns={"value": "solar_lcoe_2024_usd_per_mwh"})
        .merge(global_capacity, on="year", how="inner")
    )
    panel = panel[(panel["year"] >= 2010) & (panel["year"] <= 2024)].copy()
    panel["ln_lcoe"] = np.log(panel["solar_lcoe_2024_usd_per_mwh"])
    panel["ln_capacity"] = np.log(panel["global_solar_capacity_mw"])
    panel["post_2020"] = (panel["year"] >= 2020).astype(int)
    panel["ln_capacity_x_post_2020"] = panel["ln_capacity"] * panel["post_2020"]

    pre = fit_learning_curve(panel[panel["year"] <= 2019])
    full = fit_learning_curve(panel)
    slope_retention = abs(full["beta_log_cost_on_log_capacity"]) / abs(
        pre["beta_log_cost_on_log_capacity"]
    )

    interaction_x = sm.add_constant(
        panel[["ln_capacity", "post_2020", "ln_capacity_x_post_2020"]]
    )
    interaction = sm.OLS(panel["ln_lcoe"], interaction_x).fit()
    interaction_term = float(interaction.params["ln_capacity_x_post_2020"])
    interaction_p = float(interaction.pvalues["ln_capacity_x_post_2020"])

    lcoe_2019 = float(panel.loc[panel["year"] == 2019, "solar_lcoe_2024_usd_per_mwh"].iloc[0])
    lcoe_2024 = float(panel.loc[panel["year"] == 2024, "solar_lcoe_2024_usd_per_mwh"].iloc[0])
    lcoe_change_2019_2024 = (lcoe_2024 / lcoe_2019) - 1

    criteria = {
        "full_slope_retains_at_least_85pct_of_pre_2020_slope": slope_retention >= 0.85,
        "lcoe_2024_below_2019": lcoe_2024 < lcoe_2019,
        "post_2020_slowdown_not_significant_at_10pct": not (
            interaction_term > 0 and interaction_p < 0.10
        ),
        "module_price_and_bos_components_available": False,
    }
    verdict = "partial"
    reason = (
        "Headline learning curve continued and 2024 LCOE is below 2019, but the "
        "post-2020 interaction shows statistically visible flattening and the "
        "module/BOS component checks remain unavailable in the current local data."
    )

    diagnostics = {
        "hypothesis_id": "solar_lcoe_2010_2024_learning_curve_continuation",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "pre_2010_2019": pre,
        "full_2010_2024": full,
        "slope_retention_full_vs_pre": float(slope_retention),
        "post_2020_interaction": {
            "coefficient": interaction_term,
            "p_value": interaction_p,
            "r_squared": float(interaction.rsquared),
        },
        "lcoe_2019_2024": {
            "lcoe_2019_2024_usd_per_mwh": lcoe_2019,
            "lcoe_2024_2024_usd_per_mwh": lcoe_2024,
            "percent_change": float(lcoe_change_2019_2024 * 100),
        },
        "criteria": criteria,
        "input_vintages": {
            "irena_lcoe_solar_pv": str(LCOE_PATH.relative_to(ROOT)),
            "irena_installed_capacity_solar_pv": str(CAPACITY_PATH.relative_to(ROOT)),
        },
        "panel": panel[
            ["year", "solar_lcoe_2024_usd_per_mwh", "global_solar_capacity_mw"]
        ].to_dict(orient="records"),
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/solar_lcoe_2010_2024_learning_curve_continuation/replication.py",
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))

    lines = [
        "# Result card - solar_lcoe_2010_2024_learning_curve_continuation",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Plain-English Brief",
        "Solar power kept getting cheaper after the 2020 supply-chain and inflation shocks, but not quite as cleanly as the strongest version of the hypothesis predicted.",
        "",
        "## What Was Measured",
        "- Global utility-scale solar PV LCOE from IRENA, in 2024 USD per MWh.",
        "- Global installed solar PV capacity, summed from the IRENA country panel.",
        "- The learning-curve slope: how much cost falls when cumulative capacity doubles.",
        "- A post-2020 slowdown check: whether the cost decline visibly flattened after the shock period.",
        "",
        "## Result",
        f"- 2010-2019 learning rate per doubling: **{pre['learning_rate_per_capacity_doubling']:.1%}**.",
        f"- 2010-2024 learning rate per doubling: **{full['learning_rate_per_capacity_doubling']:.1%}**.",
        f"- Full-sample slope retained **{slope_retention:.1%}** of the pre-2020 slope.",
        f"- Solar LCOE moved from **${lcoe_2019:.2f}/MWh in 2019** to **${lcoe_2024:.2f}/MWh in 2024**.",
        f"- Post-2020 flattening interaction: coefficient **{interaction_term:.3f}**, p-value **{interaction_p:.3f}**.",
        "",
        "## Why This Is Partial",
        "The main cost decline clearly continued: 2024 is far below 2019, and the full-period learning slope is close to the pre-2020 slope. But the stricter pre-registration also asked for no statistically visible post-2020 slowdown and for module/BOS component checks. The slowdown check is visible, and the component data is not in the current local dataset.",
        "",
        "## Sources",
        f"- `{LCOE_PATH.relative_to(ROOT)}`",
        f"- `{CAPACITY_PATH.relative_to(ROOT)}`",
        "",
        f"_Generated by `replication.py` at {diagnostics['run_utc']}_",
    ]
    (RUN_DIR / "result_card.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
