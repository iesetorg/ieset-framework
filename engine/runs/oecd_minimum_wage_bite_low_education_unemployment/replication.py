#!/usr/bin/env python3
"""OECD minimum-wage bite ratio and low-education unemployment panel."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "oecd_minimum_wage_bite_low_education_unemployment"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

MW_SERIES = "MWUSD"
LOW_ED_SERIES = "DSD_LMS_low_education_unemployment_rate"
PERIOD = (1990, 2024)
MIN_COUNTRIES = 12
MIN_YEARS = 20


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
    mw_path = latest("oecd", MW_SERIES)
    low_path = latest("oecd", LOW_ED_SERIES)

    mw = pd.read_parquet(mw_path)
    mw["year"] = pd.to_numeric(mw["period"], errors="coerce").astype("Int64")
    mw["bite_ratio"] = pd.to_numeric(mw["value"], errors="coerce") / 100.0
    mw = mw[
        (mw["AGGREGATION_OPERATION"] == "MEDIAN")
        & mw["REF_AREA"].notna()
        & mw["year"].between(*PERIOD)
        & mw["bite_ratio"].notna()
    ][["REF_AREA", "year", "bite_ratio"]]

    low = pd.read_parquet(low_path)
    low["year"] = pd.to_numeric(low["period"], errors="coerce").astype("Int64")
    low["low_education_unemployment_rate"] = pd.to_numeric(low["value"], errors="coerce")
    low = low[
        low["REF_AREA"].notna()
        & low["year"].between(*PERIOD)
        & low["low_education_unemployment_rate"].notna()
    ][["REF_AREA", "year", "low_education_unemployment_rate"]]

    panel = mw.merge(low, on=["REF_AREA", "year"], how="inner").rename(columns={"REF_AREA": "country_iso3"})
    coverage = panel.groupby("country_iso3")["year"].nunique()
    keep = coverage[coverage >= MIN_YEARS].index
    panel = panel[panel["country_iso3"].isin(keep)].copy()

    if panel["country_iso3"].nunique() < MIN_COUNTRIES:
        verdict = (
            f"inconclusive - only {panel['country_iso3'].nunique()} countries have "
            f">= {MIN_YEARS} overlapping years; threshold is {MIN_COUNTRIES}."
        )
        diagnostics = {
            "verdict": verdict,
            "all_pass": False,
            "method_valid": False,
            "coverage_gap": True,
            "n_countries": int(panel["country_iso3"].nunique()),
            "n_observations": int(len(panel)),
        }
        coefficients = pd.DataFrame([{"spec": "country_year_fe", "term": "bite_ratio", "estimate": np.nan}])
    else:
        reg = panel.set_index(["country_iso3", "year"]).sort_index()
        mod = PanelOLS(
            reg["low_education_unemployment_rate"],
            reg[["bite_ratio"]],
            entity_effects=True,
            time_effects=True,
            drop_absorbed=True,
        )
        res = mod.fit(cov_type="clustered", cluster_entity=True)
        beta = float(res.params["bite_ratio"])
        se = float(res.std_errors["bite_ratio"])
        pval = float(res.pvalues["bite_ratio"])
        supported = beta > 0 and pval < 0.10
        refuted = beta <= 0 and pval < 0.10
        bucket = "supported" if supported else "refuted" if refuted else "partial"
        verdict = (
            f"{bucket} - one-point higher minimum-wage bite ratio is associated "
            f"with {beta:.3f} percentage points low-education unemployment "
            f"(SE {se:.3f}, p={pval:.3f}) in OECD country/year FE."
        )
        diagnostics = {
            "verdict": verdict,
            "all_pass": supported,
            "method_valid": True,
            "coverage_gap": False,
            "n_countries": int(panel["country_iso3"].nunique()),
            "n_observations": int(len(panel)),
            "beta_bite_ratio": beta,
            "std_error": se,
            "p_value": pval,
            "r2_within": float(res.rsquared_within),
            "countries": sorted(panel["country_iso3"].unique().tolist()),
        }
        coefficients = pd.DataFrame(
            [
                {
                    "spec": "country_year_fe",
                    "term": "bite_ratio",
                    "estimate": beta,
                    "std_error": se,
                    "p_value": pval,
                }
            ]
        )

    coefficients.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest = {
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
        "status": "completed" if diagnostics.get("method_valid") else "coverage_gap_inconclusive",
        "missing_series": [],
        "vintages": {
            f"oecd:{MW_SERIES}": {
                "publisher": "oecd",
                "series": MW_SERIES,
                "vintage_file": str(mw_path.relative_to(REPO_ROOT)),
                "sha256": sha256(mw_path),
            },
            f"oecd:{LOW_ED_SERIES}": {
                "publisher": "oecd",
                "series": LOW_ED_SERIES,
                "vintage_file": str(low_path.relative_to(REPO_ROOT)),
                "sha256": sha256(low_path),
            },
        },
    }
    import yaml

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    chart = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "OECD minimum-wage bite and low-education unemployment",
        "subtitle": verdict,
        "type": "scatter",
        "x_axis": {"label": "minimum wage / median wage", "type": "linear"},
        "y_axis": {"label": "low-education unemployment rate", "type": "linear"},
        "series": [
            {
                "name": "country-years",
                "points": [
                    {
                        "x": float(r.bite_ratio),
                        "y": float(r.low_education_unemployment_rate),
                        "label": f"{r.country_iso3} {int(r.year)}",
                    }
                    for r in panel.itertuples()
                ],
            }
        ],
        "sources": [
            {"publisher_id": "oecd", "series_id": MW_SERIES, "vintage_file": str(mw_path.relative_to(REPO_ROOT))},
            {"publisher_id": "oecd", "series_id": LOW_ED_SERIES, "vintage_file": str(low_path.relative_to(REPO_ROOT))},
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                "# OECD minimum-wage bite and low-education unemployment",
                "",
                f"**Verdict:** {verdict}",
                "",
                "Country and year fixed-effects panel using OECD minimum wage relative to median full-time wages and OECD low-education unemployment.",
                "",
                f"- Observations: {diagnostics.get('n_observations')}",
                f"- Countries: {diagnostics.get('n_countries')}",
            ]
        )
        + "\n"
    )
    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
