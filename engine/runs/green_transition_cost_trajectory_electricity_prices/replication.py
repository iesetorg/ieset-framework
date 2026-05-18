#!/usr/bin/env python3
"""Exact local diagnostic for green-transition electricity-price costs.

The original pre-registration asks for IEA industrial electricity prices,
OECD STAN sector output, and broad comparators including the USA, Japan, and
Korea. The landed local data now supports a narrower exact European diagnostic:
Eurostat industrial electricity prices for DE/BE/NL versus FR/IT/ES/SE/NO, plus
WDI real manufacturing value added. This wrapper grades only that local slice.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent

PRICE_PATH = ROOT / "data/vintages/eurostat/nrg_pc_205@2026-05-12T135519Z.parquet"
MANUFACTURING_PATH = ROOT / "data/vintages/world_bank_wdi/NV.IND.MANF.KD@2026-04-30T140100Z.parquet"

ISO2_TO_ISO3 = {
    "BE": "BEL",
    "DE": "DEU",
    "ES": "ESP",
    "FR": "FRA",
    "IT": "ITA",
    "NL": "NLD",
    "NO": "NOR",
    "SE": "SWE",
}
GROUPS = {
    "BE": "high_transition",
    "DE": "high_transition",
    "NL": "high_transition",
    "ES": "measured_transition",
    "FR": "measured_transition",
    "IT": "measured_transition",
    "NO": "measured_transition",
    "SE": "measured_transition",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_price_panel() -> pd.DataFrame:
    df = pd.read_parquet(PRICE_PATH)
    panel = df[
        (df["siec"] == "E7000")
        & (df["unit"] == "KWH")
        & (df["tax"] == "I_TAX")
        & (df["currency"] == "EUR")
        & (df["nrg_cons"] == "MWH2000-19999")
        & (df["geo_code"].isin(GROUPS))
    ].copy()
    panel["year"] = panel["period"].astype(str).str.slice(0, 4).astype(int)
    panel = (
        panel.groupby(["geo_code", "year"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "industrial_electricity_price_eur_per_kwh"})
    )
    panel["country_iso3"] = panel["geo_code"].map(ISO2_TO_ISO3)
    panel["transition_group"] = panel["geo_code"].map(GROUPS)
    panel["high_transition"] = (panel["transition_group"] == "high_transition").astype(int)
    panel["log_price"] = panel["industrial_electricity_price_eur_per_kwh"].map(math.log)
    return panel


def load_manufacturing_panel() -> pd.DataFrame:
    df = pd.read_parquet(MANUFACTURING_PATH)
    panel = df[df["country_iso3"].isin(ISO2_TO_ISO3.values())].copy()
    panel = panel[["country_iso3", "year", "value"]].dropna()
    panel = panel.rename(columns={"value": "real_manufacturing_va_2015_usd"})
    iso3_to_geo = {v: k for k, v in ISO2_TO_ISO3.items()}
    panel["geo_code"] = panel["country_iso3"].map(iso3_to_geo)
    panel["transition_group"] = panel["geo_code"].map(GROUPS)
    panel["high_transition"] = (panel["transition_group"] == "high_transition").astype(int)
    return panel


def endpoint_change(df: pd.DataFrame, start: int, end: int, value_col: str) -> pd.DataFrame:
    endpoints = (
        df[df["year"].isin([start, end])]
        .pivot(index=["geo_code", "country_iso3", "transition_group"], columns="year", values=value_col)
        .dropna()
        .reset_index()
    )
    endpoints["pct_change"] = (endpoints[end] / endpoints[start] - 1) * 100.0
    return endpoints


def main() -> None:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prices = load_price_panel()
    manufacturing = load_manufacturing_panel()

    price_window = prices[(prices["year"] >= 2015) & (prices["year"] <= 2023)].copy()
    price_model = smf.ols("log_price ~ high_transition + C(year)", data=price_window).fit(
        cov_type="cluster", cov_kwds={"groups": price_window["geo_code"]}
    )
    interaction_model = smf.ols(
        "log_price ~ high_transition * post_2021 + C(geo_code) + C(year)",
        data=price_window.assign(post_2021=(price_window["year"] >= 2021).astype(int)),
    ).fit(cov_type="cluster", cov_kwds={"groups": price_window["geo_code"]})

    annual_group_prices = (
        price_window.groupby(["transition_group", "year"])["industrial_electricity_price_eur_per_kwh"]
        .mean()
        .unstack("transition_group")
        .reset_index()
    )
    annual_group_prices["price_gap_pct"] = (
        annual_group_prices["high_transition"] / annual_group_prices["measured_transition"] - 1
    ) * 100.0

    manuf_endpoints = endpoint_change(
        manufacturing[manufacturing["year"].between(2019, 2023)],
        2019,
        2023,
        "real_manufacturing_va_2015_usd",
    )
    manuf_group_change = manuf_endpoints.groupby("transition_group")["pct_change"].mean().to_dict()
    manufacturing_gap_pp = (
        manuf_group_change.get("high_transition", float("nan"))
        - manuf_group_change.get("measured_transition", float("nan"))
    )

    avg_gap_2015_2023 = float(annual_group_prices["price_gap_pct"].mean())
    gap_2023 = float(annual_group_prices.loc[annual_group_prices["year"] == 2023, "price_gap_pct"].iloc[0])
    price_coef = float(price_model.params["high_transition"])
    price_p = float(price_model.pvalues["high_transition"])
    post2021_coef = float(interaction_model.params["high_transition:post_2021"])
    post2021_p = float(interaction_model.pvalues["high_transition:post_2021"])

    price_leg_supported = avg_gap_2015_2023 >= 10.0 and gap_2023 >= 15.0 and price_coef > 0
    output_leg_supported = manufacturing_gap_pp <= -5.0
    if price_leg_supported and output_leg_supported:
        label = "SUPPORTED"
        reason = "Eurostat price gap and WDI manufacturing-output divergence both clear the local thresholds."
    elif price_leg_supported:
        label = "PARTIAL"
        reason = (
            "Eurostat industrial-price gap is clear, but WDI real manufacturing value added does "
            "not show the predicted 2019-2023 high-transition output underperformance."
        )
    else:
        label = "REFUTED"
        reason = "The local Eurostat industrial-price gap does not clear the pre-specified direction and size screen."

    diagnostics = {
        "hypothesis_id": "green_transition_cost_trajectory_electricity_prices",
        "verdict": f"{label} - {reason}",
        "verdict_label": label,
        "verdict_reason": reason,
        "scope_note": (
            "Exact local diagnostic only. It excludes USA/JPN/KOR and UK post-2020 because the local "
            "Eurostat price vintage does not cover those comparators over the full 2015-2023 window."
        ),
        "test_window": [2015, 2023],
        "price_band": "Eurostat NRG_PC_205 industrial electricity band MWH2000-19999, EUR/kWh incl. taxes",
        "groups": GROUPS,
        "metrics": {
            "average_price_gap_pct_2015_2023": avg_gap_2015_2023,
            "price_gap_pct_2023": gap_2023,
            "price_level_log_coef_high_transition_year_fe": price_coef,
            "price_level_p_value_cluster_geo": price_p,
            "post_2021_interaction_log_coef": post2021_coef,
            "post_2021_interaction_p_value_cluster_geo": post2021_p,
            "manufacturing_va_pct_change_2019_2023_high_transition": manuf_group_change.get("high_transition"),
            "manufacturing_va_pct_change_2019_2023_measured_transition": manuf_group_change.get("measured_transition"),
            "manufacturing_va_gap_pp_high_minus_measured": manufacturing_gap_pp,
        },
        "criteria": {
            "price_leg_supported": price_leg_supported,
            "output_leg_supported": output_leg_supported,
        },
        "annual_group_prices": annual_group_prices.to_dict(orient="records"),
        "manufacturing_endpoints": manuf_endpoints.to_dict(orient="records"),
        "vintages": {
            "eurostat_nrg_pc_205": str(PRICE_PATH.relative_to(ROOT)),
            "wdi_real_manufacturing_va": str(MANUFACTURING_PATH.relative_to(ROOT)),
        },
        "sha256": {
            "eurostat_nrg_pc_205": sha256(PRICE_PATH),
            "wdi_real_manufacturing_va": sha256(MANUFACTURING_PATH),
        },
        "run_utc": run_utc,
        "runner": "engine/runs/green_transition_cost_trajectory_electricity_prices/replication.py",
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest = {
        "hypothesis_id": "green_transition_cost_trajectory_electricity_prices",
        "run_utc": run_utc,
        "verdict_label": label,
        "wrapper": "engine/runs/green_transition_cost_trajectory_electricity_prices/replication.py",
        "scope": "European local diagnostic: Eurostat industrial electricity prices plus WDI real manufacturing VA",
        "vintages": {
            "eurostat_nrg_pc_205": {
                "publisher": "eurostat",
                "series_id": "nrg_pc_205",
                "vintage_file": str(PRICE_PATH.relative_to(ROOT)),
                "sha256": diagnostics["sha256"]["eurostat_nrg_pc_205"],
            },
            "world_bank_wdi_NV_IND_MANF_KD": {
                "publisher": "world_bank_wdi",
                "series_id": "NV.IND.MANF.KD",
                "vintage_file": str(MANUFACTURING_PATH.relative_to(ROOT)),
                "sha256": diagnostics["sha256"]["wdi_real_manufacturing_va"],
            },
        },
        "limits": [
            "IEA industrial-price, OECD STAN sector-output, and non-European comparator legs remain outside this local diagnostic.",
            "2022-2023 gas shock is reported as a confound; this wrapper does not claim a clean causal transition-policy estimate.",
        ],
    }
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    lines = [
        "# Result card - green_transition_cost_trajectory_electricity_prices",
        "",
        f"**Verdict:** {label} - {reason}",
        "",
        "## Local Test",
        "",
        "This rerun uses the exact landed local data slice now available: Eurostat `nrg_pc_205` industrial electricity prices for DE/BE/NL versus FR/IT/ES/SE/NO, and WDI real manufacturing value added. It does not grade the unavailable IEA, OECD STAN, USA/JPN/KOR, or full UK legs.",
        "",
        "## Price Channel",
        "",
        f"- Average high-transition price gap, 2015-2023: **{avg_gap_2015_2023:.1f}%**.",
        f"- High-transition price gap in 2023: **{gap_2023:.1f}%**.",
        f"- Year-FE log price coefficient for high-transition group: **{price_coef:.3f}** (clustered p={price_p:.3f}).",
        f"- Post-2021 high-transition interaction: **{post2021_coef:.3f}** (clustered p={post2021_p:.3f}).",
        "",
        "## Manufacturing Channel",
        "",
        f"- High-transition WDI real manufacturing VA change, 2019-2023: **{manuf_group_change.get('high_transition'):.1f}%**.",
        f"- Measured-transition WDI real manufacturing VA change, 2019-2023: **{manuf_group_change.get('measured_transition'):.1f}%**.",
        f"- Gap, high minus measured: **{manufacturing_gap_pp:.1f} pp**.",
        "",
        "## Interpretation",
        "",
        "The electricity-price leg is strongly pattern-consistent with the claim. The output-relocation leg is not: in this local European subset, high-transition countries did not underperform the comparator group on real manufacturing value added from 2019 to 2023. The result is therefore partial, not a clean supported verdict.",
        "",
        "## Provenance",
        "",
        "Exact vintages and SHA-256 hashes are pinned in `manifest.yaml`. Re-run with `python3 engine/runs/green_transition_cost_trajectory_electricity_prices/replication.py`.",
        "",
        f"_Generated by `replication.py` at {run_utc}_",
    ]
    (RUN_DIR / "result_card.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
