#!/usr/bin/env python3
"""US county QCEW food-service employment and state minimum wages."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "us_qcew_county_food_service_minimum_wage_panel"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

FOOD_SERIES = "QCEW_county_NAICS722_employment_panel"
TOTAL_SERIES = "QCEW_county_total_employment_panel"
MIN_WAGE_SERIES = "state_minimum_wage_history"
PERIOD = (2014, 2024)


def latest(pub: str, series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    food_path = latest("bls", FOOD_SERIES)
    total_path = latest("bls", TOTAL_SERIES)
    mw_path = latest("usdol", MIN_WAGE_SERIES)

    food = pd.read_parquet(food_path)
    total = pd.read_parquet(total_path)
    mw = pd.read_parquet(mw_path)

    for df in (food, total):
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["annual_avg_emplvl"] = pd.to_numeric(df["annual_avg_emplvl"], errors="coerce")
        df["county_fips"] = df["area_fips"].astype(str).str.zfill(5)
        df["state_fips"] = df["county_fips"].str[:2]

    food = food[food["year"].between(*PERIOD) & (food["annual_avg_emplvl"] > 0)]
    total = total[total["year"].between(*PERIOD) & (total["annual_avg_emplvl"] > 0)]
    panel = food[["county_fips", "state_fips", "year", "annual_avg_emplvl"]].rename(
        columns={"annual_avg_emplvl": "food_service_employment"}
    )
    panel = panel.merge(
        total[["county_fips", "year", "annual_avg_emplvl"]].rename(columns={"annual_avg_emplvl": "total_employment"}),
        on=["county_fips", "year"],
        how="inner",
    )

    mw["year"] = pd.to_numeric(mw["year"], errors="coerce").astype("Int64")
    mw["minimum_wage"] = pd.to_numeric(mw["value"], errors="coerce")
    mw = mw[mw["year"].between(*PERIOD) & mw["state_fips"].notna() & mw["minimum_wage"].notna()]
    panel = panel.merge(mw[["state_fips", "year", "minimum_wage"]], on=["state_fips", "year"], how="inner")
    panel = panel[(panel["minimum_wage"] > 0) & (panel["food_service_employment"] > 0) & (panel["total_employment"] > 0)]
    panel["log_food_service_employment"] = np.log(panel["food_service_employment"])
    panel["log_total_employment"] = np.log(panel["total_employment"])
    panel["log_minimum_wage"] = np.log(panel["minimum_wage"])

    reg = panel.set_index(["county_fips", "year"]).sort_index()
    mod = PanelOLS(
        reg["log_food_service_employment"],
        reg[["log_minimum_wage", "log_total_employment"]],
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
    )
    res = mod.fit(cov_type="clustered", cluster_entity=True)
    beta = float(res.params["log_minimum_wage"])
    se = float(res.std_errors["log_minimum_wage"])
    pval = float(res.pvalues["log_minimum_wage"])
    supported = beta < -0.05 and pval < 0.10
    refuted = beta >= 0 and pval < 0.10
    bucket = "supported" if supported else "refuted" if refuted else "partial"
    verdict = (
        f"{bucket} - county FE elasticity of food-service employment with "
        f"respect to state minimum wage is {beta:.3f} (SE {se:.3f}, p={pval:.3f}), "
        "controlling for total county employment and year shocks."
    )
    diagnostics = {
        "verdict": verdict,
        "all_pass": supported,
        "method_valid": True,
        "n_counties": int(panel["county_fips"].nunique()),
        "n_states": int(panel["state_fips"].nunique()),
        "n_observations": int(len(panel)),
        "beta_log_minimum_wage": beta,
        "std_error": se,
        "p_value": pval,
        "r2_within": float(res.rsquared_within),
        "period": list(PERIOD),
    }

    pd.DataFrame(
        [
            {
                "spec": "county_year_fe",
                "term": "log_minimum_wage",
                "estimate": beta,
                "std_error": se,
                "p_value": pval,
            },
            {
                "spec": "county_year_fe",
                "term": "log_total_employment",
                "estimate": float(res.params["log_total_employment"]),
                "std_error": float(res.std_errors["log_total_employment"]),
                "p_value": float(res.pvalues["log_total_employment"]),
            },
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest = {
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
        "status": "completed",
        "missing_series": [],
        "vintages": {
            f"bls:{FOOD_SERIES}": {
                "publisher": "bls",
                "series": FOOD_SERIES,
                "vintage_file": str(food_path.relative_to(REPO_ROOT)),
                "sha256": sha256(food_path),
            },
            f"bls:{TOTAL_SERIES}": {
                "publisher": "bls",
                "series": TOTAL_SERIES,
                "vintage_file": str(total_path.relative_to(REPO_ROOT)),
                "sha256": sha256(total_path),
            },
            f"usdol:{MIN_WAGE_SERIES}": {
                "publisher": "usdol",
                "series": MIN_WAGE_SERIES,
                "vintage_file": str(mw_path.relative_to(REPO_ROOT)),
                "sha256": sha256(mw_path),
            },
        },
    }
    import yaml

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    chart = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US QCEW county food-service employment and minimum wages",
        "subtitle": verdict,
        "type": "scatter",
        "x_axis": {"label": "log state minimum wage", "type": "linear"},
        "y_axis": {"label": "log county food-service employment", "type": "linear"},
        "series": [
            {
                "name": "county-years",
                "points": [
                    {
                        "x": float(r.log_minimum_wage),
                        "y": float(r.log_food_service_employment),
                        "label": f"{r.county_fips} {int(r.year)}",
                    }
                    for r in panel.sample(min(len(panel), 2000), random_state=1).itertuples()
                ],
            }
        ],
        "sources": [
            {"publisher_id": "bls", "series_id": FOOD_SERIES, "vintage_file": str(food_path.relative_to(REPO_ROOT))},
            {"publisher_id": "bls", "series_id": TOTAL_SERIES, "vintage_file": str(total_path.relative_to(REPO_ROOT))},
            {"publisher_id": "usdol", "series_id": MIN_WAGE_SERIES, "vintage_file": str(mw_path.relative_to(REPO_ROOT))},
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                "# US QCEW county food-service employment and minimum wages",
                "",
                f"**Verdict:** {verdict}",
                "",
                "County and year fixed-effects panel using official BLS QCEW county NAICS 722 employment, BLS county total employment, and USDOL state minimum-wage history.",
                "",
                f"- Observations: {diagnostics['n_observations']}",
                f"- Counties: {diagnostics['n_counties']}",
                f"- States/DC: {diagnostics['n_states']}",
            ]
        )
        + "\n"
    )
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
