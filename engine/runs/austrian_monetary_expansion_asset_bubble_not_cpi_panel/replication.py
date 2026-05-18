#!/usr/bin/env python3
"""Exact local-proxy replication for the Austrian asset-inflation panel."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HID = "austrian_monetary_expansion_asset_bubble_not_cpi_panel"
COUNTRIES = ["USA", "GBR", "DEU", "FRA", "JPN", "CAN", "AUS", "NLD", "ITA", "ESP", "SWE", "CHE"]
ISO2_TO_ISO3 = {
    "US": "USA",
    "GB": "GBR",
    "DE": "DEU",
    "FR": "FRA",
    "JP": "JPN",
    "CA": "CAN",
    "AU": "AUS",
    "NL": "NLD",
    "IT": "ITA",
    "ES": "ESP",
    "SE": "SWE",
    "CH": "CHE",
}


def latest(publisher: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / publisher).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {publisher}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vintage_meta(publisher: str, series: str, label: str) -> tuple[Path, dict]:
    path = latest(publisher, series)
    return path, {
        "publisher": publisher,
        "series": series,
        "label": label,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def run() -> int:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    spp_path, spp_meta = vintage_meta("bis", "WS_SPP", "BIS real residential property price index")
    money_path, money_meta = vintage_meta("world_bank_wdi", "FM.LBL.BMNY.GD.ZS", "Broad money as percent of GDP")
    cpi_path, cpi_meta = vintage_meta("world_bank_wdi", "FP.CPI.TOTL.ZG", "CPI inflation")
    gdp_path, gdp_meta = vintage_meta("world_bank_wdi", "NY.GDP.MKTP.KD.ZG", "Real GDP growth")
    trade_path, trade_meta = vintage_meta("world_bank_wdi", "NE.TRD.GNFS.ZS", "Trade openness")

    spp = pd.read_parquet(spp_path)
    spp = spp[spp["VALUE"].eq("R")].copy()
    spp["country_iso3"] = spp["REF_AREA"].map(ISO2_TO_ISO3)
    spp["year"] = spp["period"].astype(str).str.extract(r"(\d{4})").astype(int)
    asset = (
        spp[spp["country_iso3"].isin(COUNTRIES)]
        .groupby(["country_iso3", "year"], as_index=False)["value"]
        .mean()
        .sort_values(["country_iso3", "year"])
    )
    asset["asset_growth"] = asset.groupby("country_iso3")["value"].transform(
        lambda s: np.log(s).diff() * 100.0
    )

    money = pd.read_parquet(money_path)
    money = money[money["country_iso3"].isin(COUNTRIES)].copy().sort_values(["country_iso3", "year"])
    money["money_growth"] = money.groupby("country_iso3")["value"].transform(lambda s: s.diff())

    cpi = pd.read_parquet(cpi_path)
    cpi = cpi[cpi["country_iso3"].isin(COUNTRIES)][["country_iso3", "year", "value"]].rename(
        columns={"value": "cpi_inflation"}
    )
    gdp = pd.read_parquet(gdp_path)
    gdp = gdp[gdp["country_iso3"].isin(COUNTRIES)][["country_iso3", "year", "value"]].rename(
        columns={"value": "real_gdp_growth"}
    )
    trade = pd.read_parquet(trade_path)
    trade = trade[trade["country_iso3"].isin(COUNTRIES)][["country_iso3", "year", "value"]].rename(
        columns={"value": "trade_openness"}
    )

    panel = (
        asset[["country_iso3", "year", "asset_growth"]]
        .merge(money[["country_iso3", "year", "money_growth"]], on=["country_iso3", "year"])
        .merge(cpi, on=["country_iso3", "year"])
        .merge(gdp, on=["country_iso3", "year"], how="left")
        .merge(trade, on=["country_iso3", "year"], how="left")
    )
    panel = panel[(panel["year"] >= 1987) & (panel["year"] <= 2007)].replace([np.inf, -np.inf], np.nan).dropna()

    formula_asset = "asset_growth ~ money_growth + real_gdp_growth + trade_openness + C(country_iso3) + C(year)"
    formula_cpi = "cpi_inflation ~ money_growth + real_gdp_growth + trade_openness + C(country_iso3) + C(year)"
    fit_asset = smf.ols(formula_asset, data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel["country_iso3"]}
    )
    fit_cpi = smf.ols(formula_cpi, data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel["country_iso3"]}
    )

    asset_beta = float(fit_asset.params["money_growth"])
    cpi_beta = float(fit_cpi.params["money_growth"])
    ratio = float(asset_beta / cpi_beta) if abs(cpi_beta) > 1e-12 else None
    asset_significant = asset_beta > 0 and float(fit_asset.pvalues["money_growth"]) < 0.05
    ratio_gate = ratio is not None and ratio >= 3.0
    if asset_significant and ratio_gate:
        verdict = "SUPPORTED"
        reason = "asset-price coefficient is positive/significant and at least 3x the CPI coefficient"
    elif not asset_significant:
        verdict = "REFUTED"
        reason = "local proxy asset-price coefficient is not positive and significant at p<0.05"
    else:
        verdict = "REFUTED"
        reason = "asset/CPI money-growth coefficient ratio does not clear the pre-registered 3x gate"

    estimate = {
        "method": "OLS with country and year fixed effects; SE clustered by country",
        "proxy_note": "Broad money growth is proxied by the annual change in WDI broad money as percent of GDP; asset prices use BIS real residential property prices.",
        "n_obs": int(len(panel)),
        "n_countries": int(panel["country_iso3"].nunique()),
        "countries_used": sorted(panel["country_iso3"].unique().tolist()),
        "asset_formula": formula_asset,
        "cpi_formula": formula_cpi,
        "asset_coefficient": asset_beta,
        "asset_std_error": float(fit_asset.bse["money_growth"]),
        "asset_p_value": float(fit_asset.pvalues["money_growth"]),
        "cpi_coefficient": cpi_beta,
        "cpi_std_error": float(fit_cpi.bse["money_growth"]),
        "cpi_p_value": float(fit_cpi.pvalues["money_growth"]),
        "asset_to_cpi_coefficient_ratio": ratio,
        "asset_positive_significant_gate": bool(asset_significant),
        "ratio_gate_ge_3": bool(ratio_gate),
    }
    vintages = {
        "real_home_price_index": spp_meta,
        "broad_money_to_gdp": money_meta,
        "cpi_inflation": cpi_meta,
        "real_gdp_growth": gdp_meta,
        "trade_openness": trade_meta,
    }
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "panel_fe_exact_local_proxy",
        "estimate": estimate,
        "vintages": vintages,
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (OUT / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": HID,
                "run_utc": run_utc,
                "verdict_label": verdict,
                "runner": f"engine/runs/{HID}/replication.py",
                "vintages": vintages,
                "formula": {
                    "asset": formula_asset,
                    "cpi": formula_cpi,
                },
                "proxy_note": estimate["proxy_note"],
            },
            sort_keys=False,
        )
    )
    md = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Claim",
        "Broad-money growth should correlate at least 3x more with asset-price growth than with CPI inflation, and the asset coefficient must be positive/significant.",
        "",
        "## Exact Local Test",
        f"- Usable panel: **{estimate['n_obs']} observations**, **{estimate['n_countries']} countries** ({', '.join(estimate['countries_used'])}).",
        f"- Asset-price coefficient: **{asset_beta:+.4f}** (SE {estimate['asset_std_error']:.4f}, p={estimate['asset_p_value']:.3g}).",
        f"- CPI coefficient: **{cpi_beta:+.4f}** (SE {estimate['cpi_std_error']:.4f}, p={estimate['cpi_p_value']:.3g}).",
        f"- Asset/CPI coefficient ratio: **{ratio:.3f}**." if ratio is not None else "- Asset/CPI coefficient ratio: undefined because CPI coefficient is near zero.",
        "",
        "## Caveat",
        "This is an exact local-data repair, not the ideal specification: WDI broad-money/GDP annual change proxies for broad-money growth, and BIS real residential property prices proxy the asset basket.",
    ]
    (OUT / "result_card.md").write_text("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
