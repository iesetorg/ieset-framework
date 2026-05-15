#!/usr/bin/env python3
"""Revive the landed IRENA learning-curve slice for this hypothesis.

The original card asked for CHN-vs-OECD learning-rate differences, but the
landed IRENA LCOE vintages are world aggregates. This wrapper therefore runs
the safe narrower diagnostic: world LCOE on world installed capacity for solar
PV and onshore wind.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
VINTAGES = ROOT / "data" / "vintages" / "irena"

SERIES = {
    "solar_pv": {
        "label": "Solar PV",
        "lcoe": "lcoe_solar_pv@2026-05-12T125721Z.parquet",
        "capacity": "installed_capacity_solar_pv@2026-05-05T212314Z.parquet",
    },
    "wind_onshore": {
        "label": "Onshore wind",
        "lcoe": "lcoe_wind_onshore@2026-05-12T125721Z.parquet",
        "capacity": "installed_capacity_wind@2026-05-05T212316Z.parquet",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_panel(key: str, spec: dict) -> tuple[pd.DataFrame, dict]:
    lcoe_path = VINTAGES / spec["lcoe"]
    capacity_path = VINTAGES / spec["capacity"]
    lcoe = pd.read_parquet(lcoe_path)
    capacity = pd.read_parquet(capacity_path)

    world_lcoe = lcoe[lcoe["country"].astype(str).str.casefold() == "world"].copy()
    world_lcoe["year"] = pd.to_numeric(world_lcoe["year"], errors="coerce")
    world_lcoe["lcoe_usd_per_mwh"] = pd.to_numeric(world_lcoe["value"], errors="coerce")

    capacity["year"] = pd.to_numeric(capacity["year"], errors="coerce")
    capacity["capacity_mw"] = pd.to_numeric(capacity["value"], errors="coerce")
    world_capacity = (
        capacity.dropna(subset=["year", "capacity_mw"])
        .groupby("year", as_index=False)["capacity_mw"]
        .sum()
    )

    panel = world_lcoe[["year", "lcoe_usd_per_mwh"]].merge(world_capacity, on="year", how="inner")
    panel = panel[(panel["year"] >= 2010) & (panel["year"] <= 2024)].dropna().copy()
    panel = panel[(panel["lcoe_usd_per_mwh"] > 0) & (panel["capacity_mw"] > 0)]
    panel["technology"] = key
    panel["log_lcoe"] = np.log(panel["lcoe_usd_per_mwh"])
    panel["log_capacity"] = np.log(panel["capacity_mw"])

    meta = {
        "lcoe": {
            "vintage_file": str(lcoe_path.relative_to(ROOT)),
            "sha256": sha256(lcoe_path),
        },
        "capacity": {
            "vintage_file": str(capacity_path.relative_to(ROOT)),
            "sha256": sha256(capacity_path),
        },
    }
    return panel, meta


def fit_learning_curve(panel: pd.DataFrame) -> dict:
    x = sm.add_constant(panel["log_capacity"])
    model = sm.OLS(panel["log_lcoe"], x).fit(cov_type="HC1")
    slope = float(model.params["log_capacity"])
    se = float(model.bse["log_capacity"])
    p_value = float(model.pvalues["log_capacity"])
    ci_low, ci_high = [float(v) for v in model.conf_int().loc["log_capacity"].tolist()]
    learning_rate = 1 - math.pow(2, slope)
    return {
        "n_observations": int(len(panel)),
        "period_min": int(panel["year"].min()),
        "period_max": int(panel["year"].max()),
        "slope_log_lcoe_on_log_capacity": slope,
        "std_error_hc1": se,
        "p_value": p_value,
        "ci95_slope": [ci_low, ci_high],
        "learning_rate_per_capacity_doubling": learning_rate,
        "r_squared": float(model.rsquared),
        "lcoe_start_usd_per_mwh": float(panel.sort_values("year").iloc[0]["lcoe_usd_per_mwh"]),
        "lcoe_end_usd_per_mwh": float(panel.sort_values("year").iloc[-1]["lcoe_usd_per_mwh"]),
        "capacity_start_mw": float(panel.sort_values("year").iloc[0]["capacity_mw"]),
        "capacity_end_mw": float(panel.sort_values("year").iloc[-1]["capacity_mw"]),
    }


def verdict(results: dict[str, dict]) -> tuple[str, str]:
    slopes_negative = all(row["slope_log_lcoe_on_log_capacity"] < 0 for row in results.values())
    large_declines = all(row["learning_rate_per_capacity_doubling"] > 0.10 for row in results.values())
    significant = all(row["p_value"] < 0.10 for row in results.values())
    if slopes_negative and large_declines and significant:
        return (
            "INCONCLUSIVE_DATA_PENDING",
            "global IRENA LCOE vintages support a transparent learning-curve diagnostic, but the original CHN-vs-OECD mechanism test remains blocked",
        )
    return (
        "INCONCLUSIVE",
        "global learning-curve diagnostic did not clear the negative-slope, >10% learning-rate, p<0.10 screen for both technologies",
    )


def write_outputs(panel: pd.DataFrame, results: dict[str, dict], metas: dict[str, dict]) -> None:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    label, reason = verdict(results)
    diagnostics = {
        "hypothesis_id": "china_renewables_industrial_policy_learning_curve",
        "verdict_label": label,
        "verdict_reason": reason,
        "run_utc": run_utc,
        "runner": "engine/runs/china_renewables_industrial_policy_learning_curve/replication.py",
        "scope_note": (
            "Revival narrowed to world aggregate learning curves because landed IRENA LCOE "
            "vintages contain only country='World'. The original CHN-vs-OECD falsification "
            "test remains blocked without country/cohort LCOE."
        ),
        "formula": "log(lcoe_usd_per_mwh) ~ log(global_installed_capacity_mw), estimated separately by technology with HC1 standard errors",
        "results": results,
        "vintages": metas,
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    pd.DataFrame(
        [
            {
                "technology": tech,
                **{k: v for k, v in row.items() if not isinstance(v, list)},
                "ci95_slope_low": row["ci95_slope"][0],
                "ci95_slope_high": row["ci95_slope"][1],
            }
            for tech, row in results.items()
        ]
    ).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    panel.sort_values(["technology", "year"]).to_json(
        RUN_DIR / "chart_data.json",
        orient="records",
        indent=2,
    )
    (RUN_DIR / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": "china_renewables_industrial_policy_learning_curve",
                "run_utc": run_utc,
                "verdict_label": label,
                "scope": "world aggregate IRENA learning curve revival",
                "vintages": {
                    f"{tech}_{kind}": {
                        "publisher": "irena",
                        "series_id": f"{kind}_{tech}" if kind == "lcoe" else f"installed_capacity_{tech}",
                        "vintage_file": item["vintage_file"],
                        "sha256": item["sha256"],
                    }
                    for tech, meta in metas.items()
                    for kind, item in meta.items()
                },
            },
            sort_keys=False,
        )
    )

    lines = [
        "# Result card - china_renewables_industrial_policy_learning_curve",
        "",
        f"**Verdict:** {label} - {reason}.",
        "",
        "## What Was Revived",
        "",
        "The stale blocker is cleared for IRENA LCOE availability: local solar-PV and onshore-wind LCOE vintages now load. Because both LCOE files contain only `country = World`, this run does not grade the original China-vs-OECD claim. It records the narrower safe diagnostic: global LCOE learning curves against global installed capacity.",
        "",
        "## Results",
        "",
    ]
    for tech, row in results.items():
        pretty = SERIES[tech]["label"]
        lines.append(
            f"- **{pretty}:** slope {row['slope_log_lcoe_on_log_capacity']:.3f} "
            f"(HC1 SE {row['std_error_hc1']:.3f}, p={row['p_value']:.4f}); "
            f"implied learning rate {row['learning_rate_per_capacity_doubling'] * 100:.1f}% per capacity doubling; "
            f"n={row['n_observations']}, {row['period_min']}-{row['period_max']}."
        )
    lines.extend(
        [
            "",
            "## Specification",
            "",
            "`log(lcoe_usd_per_mwh) ~ log(global_installed_capacity_mw)`, estimated separately for solar PV and onshore wind with HC1 standard errors.",
            "",
            "## Remaining Blocker",
            "",
            "The original pre-registered falsification test requires CHN and OECD cohort-specific LCOE. The exact local IRENA LCOE vintages are world-only, so the China industrial-policy mechanism still needs country/cohort LCOE from BNEF, IEA, or another source before it can be graded directly.",
            "",
            "## Local Data",
            "",
        ]
    )
    for tech, meta in metas.items():
        pretty = SERIES[tech]["label"]
        lines.append(f"- **{pretty} LCOE:** `{meta['lcoe']['vintage_file']}`")
        lines.append(f"- **{pretty} capacity:** `{meta['capacity']['vintage_file']}`")
    lines.append("")
    lines.append(f"_Generated by `replication.py` at {run_utc}_")
    (RUN_DIR / "result_card.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    panels = []
    metas = {}
    results = {}
    for key, spec in SERIES.items():
        panel, meta = load_panel(key, spec)
        if len(panel) < 8:
            raise ValueError(f"insufficient annual overlap for {key}: {len(panel)} rows")
        panels.append(panel)
        metas[key] = meta
        results[key] = fit_learning_curve(panel)
    write_outputs(pd.concat(panels, ignore_index=True), results, metas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
