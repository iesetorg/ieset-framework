#!/usr/bin/env python3
"""Replication — postwar Western GDP/CO2-throughput coupling proxy."""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
HID = "gdp_energy_coupling_1945_1973"
OUT_DIR = ROOT / "engine" / "runs" / HID

COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "NLD", "BEL", "AUT",
    "SWE", "NOR", "DNK", "FIN", "CHE", "JPN", "CAN", "AUS",
]
START_YEAR = 1950
END_YEAR = 1973


def latest(pub: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    maddison_path = latest("maddison", "mpd2020")
    co2_path = latest("owid", "co2-emissions-per-capita")
    mpd = pq.read_table(maddison_path).to_pandas()
    co2 = pq.read_table(co2_path).to_pandas()

    co2_value_col = [c for c in co2.columns if c not in {"country_name", "country_iso3", "year"}][-1]
    co2 = co2.rename(columns={co2_value_col: "co2_pc"})
    mpd = mpd[
        mpd["country_iso3"].isin(COUNTRIES)
        & mpd["year"].between(START_YEAR, END_YEAR)
    ].copy()
    co2 = co2[
        co2["country_iso3"].isin(COUNTRIES)
        & co2["year"].between(START_YEAR, END_YEAR)
    ].copy()

    mpd["gdp_total_proxy"] = pd.to_numeric(mpd["gdppc"], errors="coerce") * pd.to_numeric(mpd["pop"], errors="coerce")
    panel = mpd[["country_iso3", "year", "gdp_total_proxy", "pop"]].merge(
        co2[["country_iso3", "year", "co2_pc"]],
        on=["country_iso3", "year"],
        how="inner",
    )
    panel["year"] = panel["year"].astype(int)
    panel["co2_total_proxy"] = pd.to_numeric(panel["co2_pc"], errors="coerce") * pd.to_numeric(panel["pop"], errors="coerce") * 1000
    panel = panel[(panel["gdp_total_proxy"] > 0) & (panel["co2_total_proxy"] > 0)].copy()
    panel["log_gdp"] = np.log(panel["gdp_total_proxy"])
    panel["log_co2"] = np.log(panel["co2_total_proxy"])

    model = smf.ols("log_co2 ~ log_gdp + C(country_iso3) + C(year)", data=panel).fit(
        cov_type="cluster",
        cov_kwds={"groups": panel["country_iso3"]},
    )
    beta = float(model.params["log_gdp"])
    pvalue = float(model.pvalues["log_gdp"])

    if beta >= 0.7 and pvalue < 0.05:
        verdict_label = "partial"
        verdict = (
            f"partial — CO2-throughput proxy is tightly coupled to GDP in 1950-1973 "
            f"(FE elasticity {beta:.2f}, p={pvalue:.2g}), but primary-energy data are absent locally."
        )
    elif beta < 0.7 and pvalue < 0.05:
        verdict_label = "refuted"
        verdict = (
            f"refuted — CO2-throughput proxy elasticity is below the registered coupling threshold "
            f"(beta {beta:.2f}, p={pvalue:.2g})."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            f"weakened — CO2-throughput proxy elasticity is not decisively above or below the "
            f"registered threshold (beta {beta:.2f}, p={pvalue:.2g})."
        )

    coverage = (
        panel.groupby("country_iso3")["year"]
        .agg(["min", "max", "count"])
        .reset_index()
        .to_dict(orient="records")
    )
    country_growth = []
    for country, g in panel.sort_values("year").groupby("country_iso3"):
        first = g.iloc[0]
        last = g.iloc[-1]
        country_growth.append(
            {
                "country_iso3": country,
                "co2_total_growth_pct": float((last["co2_total_proxy"] / first["co2_total_proxy"] - 1) * 100),
                "gdp_total_growth_pct": float((last["gdp_total_proxy"] / first["gdp_total_proxy"] - 1) * 100),
            }
        )

    manifest = {
        "maddison_mpd2020": {
            "publisher": "maddison",
            "series": "mpd2020",
            "vintage_file": str(maddison_path.relative_to(ROOT)),
            "sha256": sha256(maddison_path),
        },
        "owid_co2_pc": {
            "publisher": "owid",
            "series": "co2-emissions-per-capita",
            "vintage_file": str(co2_path.relative_to(ROOT)),
            "sha256": sha256(co2_path),
        },
    }
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "period": [START_YEAR, END_YEAR],
        "n_observations": int(len(panel)),
        "n_countries": int(panel["country_iso3"].nunique()),
        "elasticity_log_co2_on_log_gdp": beta,
        "pvalue": pvalue,
        "rsquared": float(model.rsquared),
        "coverage": coverage,
        "country_growth": country_growth,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n" + "\n".join(f"  {k}: {v['vintage_file']}" for k, v in manifest.items()) + "\n"
    )
    pd.DataFrame(country_growth).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Proxy FE Estimate",
                "",
                f"- Countries: {panel['country_iso3'].nunique()}.",
                f"- Observations: {len(panel)}.",
                f"- Elasticity log(CO2 proxy) on log(GDP): {beta:.3f}.",
                f"- Clustered p-value: {pvalue:.3g}.",
                f"- R-squared: {model.rsquared:.3f}.",
                "",
                "## Method Note",
                "",
                "CO2 is a carbon-throughput proxy, not direct primary-energy consumption; support is capped at partial.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
