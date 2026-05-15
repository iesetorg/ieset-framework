#!/usr/bin/env python3
"""Replicate wid_top_income_share_trade_openness_panel from local vintages."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HID = "wid_top_income_share_trade_openness_panel"
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "engine" / "runs" / HID

ISO2_TO_ISO3 = {
    "AR": "ARG", "AT": "AUT", "AU": "AUS", "BE": "BEL", "BG": "BGR",
    "BR": "BRA", "CA": "CAN", "CH": "CHE", "CL": "CHL", "CN": "CHN",
    "CO": "COL", "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK",
    "EE": "EST", "EG": "EGY", "EL": "GRC", "ES": "ESP", "FI": "FIN",
    "FR": "FRA", "GB": "GBR", "GR": "GRC", "HK": "HKG", "HR": "HRV",
    "HU": "HUN", "ID": "IDN", "IE": "IRL", "IL": "ISR", "IN": "IND",
    "IS": "ISL", "IT": "ITA", "JP": "JPN", "KR": "KOR", "LT": "LTU",
    "LU": "LUX", "LV": "LVA", "MA": "MAR", "MT": "MLT", "MX": "MEX",
    "MY": "MYS", "NL": "NLD", "NO": "NOR", "NZ": "NZL", "PE": "PER",
    "PH": "PHL", "PK": "PAK", "PL": "POL", "PT": "PRT", "RO": "ROU",
    "RU": "RUS", "SE": "SWE", "SG": "SGP", "SI": "SVN", "SK": "SVK",
    "TH": "THA", "TR": "TUR", "TW": "TWN", "UA": "UKR", "UK": "GBR",
    "US": "USA", "VN": "VNM", "ZA": "ZAF",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return matches[-1]


def manifest_item(name: str, publisher: str, series: str, path: Path) -> dict:
    return {
        "name": name,
        "publisher": publisher,
        "series_id": series,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def load_wdi(path: Path, name: str) -> pd.DataFrame:
    df = pd.read_parquet(path, columns=["country_iso3", "year", "value"])
    df = df.rename(columns={"value": name})
    df = df[df["country_iso3"].astype(str).str.len().eq(3)].copy()
    df[name] = pd.to_numeric(df[name], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    return df.dropna(subset=["country_iso3", "year", name]).assign(
        year=lambda d: d["year"].astype(int)
    )


def load_wid_top(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path, columns=["country", "year", "value"])
    df = df.rename(columns={"country": "country_iso3", "value": "top_0_1_pretax_income_share"})
    df["country_iso3"] = df["country_iso3"].map(lambda x: ISO2_TO_ISO3.get(str(x).upper()))
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["top_0_1_pretax_income_share"] = pd.to_numeric(
        df["top_0_1_pretax_income_share"], errors="coerce"
    )
    return df.dropna(subset=["country_iso3", "year", "top_0_1_pretax_income_share"]).assign(
        year=lambda d: d["year"].astype(int)
    )


def build_panel() -> tuple[pd.DataFrame, dict]:
    wid_path = latest("data/vintages/wid/top-0-1-share-of-total-income@*.parquet")
    trade_path = latest("data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@*.parquet")
    gdp_path = latest("data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@*.parquet")
    rq_path = latest("data/vintages/wgi/GOV_WGI_RQ.EST@*.parquet")
    pop_path = latest("data/vintages/world_bank_wdi/SP.POP.TOTL@*.parquet")

    manifest = {
        "top_0_1_pretax_income_share": manifest_item(
            "top_0_1_pretax_income_share", "wid", "top-0-1-share-of-total-income", wid_path
        ),
        "trade_open_gdp": manifest_item(
            "trade_open_gdp", "world_bank_wdi", "NE.TRD.GNFS.ZS", trade_path
        ),
        "gdp_pc_ppp": manifest_item(
            "gdp_pc_ppp", "world_bank_wdi", "NY.GDP.PCAP.PP.KD", gdp_path
        ),
        "regulatory_quality": manifest_item(
            "regulatory_quality", "wgi", "GOV_WGI_RQ.EST", rq_path
        ),
        "population": manifest_item(
            "population", "world_bank_wdi", "SP.POP.TOTL", pop_path
        ),
    }

    panel = (
        load_wid_top(wid_path)
        .merge(load_wdi(trade_path, "trade_open_gdp"), on=["country_iso3", "year"])
        .merge(load_wdi(gdp_path, "gdp_pc_ppp"), on=["country_iso3", "year"])
        .merge(load_wdi(rq_path, "regulatory_quality"), on=["country_iso3", "year"])
        .merge(load_wdi(pop_path, "population"), on=["country_iso3", "year"])
    )
    panel = panel[(panel["year"] >= 1996) & (panel["year"] <= 2023)].copy()
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["log_population"] = np.log(panel["population"])
    counts = panel.groupby("country_iso3").size()
    keep = counts[counts >= 15].index
    panel = panel[panel["country_iso3"].isin(keep)].copy()
    return panel, manifest


def estimate(panel: pd.DataFrame) -> dict:
    min_obs = 500
    min_countries = 25
    if len(panel) < min_obs or panel["country_iso3"].nunique() < min_countries:
        return {
            "error": (
                f"METHOD_VALID failed: n={len(panel)}, "
                f"countries={panel['country_iso3'].nunique()}"
            )
        }
    sub = panel.set_index(["country_iso3", "year"]).sort_index()
    y = sub["top_0_1_pretax_income_share"]
    x = sub[["trade_open_gdp", "log_gdp_pc_ppp", "regulatory_quality", "log_population"]]
    try:
        from linearmodels.panel import PanelOLS

        result = PanelOLS(y, x, entity_effects=True, time_effects=True, drop_absorbed=True).fit(
            cov_type="clustered", cluster_entity=True
        )
        coef = float(result.params["trade_open_gdp"])
        se = float(result.std_errors["trade_open_gdp"])
        pval = float(result.pvalues["trade_open_gdp"])
        method = "linearmodels.PanelOLS"
        r2_within = float(result.rsquared_within or 0.0)
    except Exception as exc:
        return {"error": f"PanelOLS failed: {exc}"}

    raw = panel.copy()
    raw["high_trade_quartile"] = raw.groupby("year")["trade_open_gdp"].transform(
        lambda s: s >= s.quantile(0.75)
    )
    contrast = raw.groupby("high_trade_quartile")["top_0_1_pretax_income_share"].mean()
    raw_diff = float(contrast.get(True, np.nan) - contrast.get(False, np.nan))

    return {
        "coefficient": coef,
        "std_error": se,
        "p_value": pval,
        "n_obs": int(len(panel)),
        "n_countries": int(panel["country_iso3"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "r_squared_within": r2_within,
        "raw_high_trade_quartile_minus_rest": raw_diff,
        "method": method,
        "fixed_effects": ["country", "year"],
        "cluster": "country",
    }


def verdict_from_estimate(est: dict) -> tuple[str, str]:
    if "error" in est:
        return "INCONCLUSIVE_DATA_PENDING", est["error"]
    coef = est["coefficient"]
    pval = est["p_value"]
    if pval < 0.10 and coef > 0:
        return "SUPPORTED", "positive trade-openness coefficient at p<0.10"
    if pval < 0.10 and coef < 0:
        return "REFUTED", "negative trade-openness coefficient at p<0.10"
    return "PARTIAL", "coefficient is not statistically decisive at p<0.10"


def write_outputs(panel: pd.DataFrame, manifest: dict, est: dict, verdict: str, reason: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    run_utc = now_utc()
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "run_utc": run_utc,
        "runner": "engine/runs/wid_top_income_share_trade_openness_panel/replication.py",
        "template": "panel_fe",
        "claim_direction": "+",
        "falsification_rule_text": (
            "SUPPORTED if trade_open_gdp coefficient > 0 at p<0.10; "
            "REFUTED if coefficient < 0 at p<0.10; PARTIAL otherwise."
        ),
        "estimate": est,
        "data_status": {
            "rows_after_join": int(len(panel)),
            "countries_after_join": int(panel["country_iso3"].nunique()),
            "period_after_join": [int(panel["year"].min()), int(panel["year"].max())],
            "min_obs_per_country": int(panel.groupby("country_iso3").size().min()),
            "variables_missing": [],
        },
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": HID,
                "run_utc": run_utc,
                "verdict_label": verdict,
                "runner": "engine/runs/wid_top_income_share_trade_openness_panel/replication.py",
                "method": "country and year fixed-effects panel, clustered by country",
                "vintages": manifest,
            },
            sort_keys=False,
        )
    )

    chart = (
        panel[["country_iso3", "year", "top_0_1_pretax_income_share", "trade_open_gdp"]]
        .sort_values(["country_iso3", "year"])
        .to_dict(orient="records")
    )
    (OUT / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    estimate_lines = []
    if "error" in est:
        estimate_lines.append(f"- Error: {est['error']}")
    else:
        estimate_lines.extend(
            [
                f"- Method: {est['method']}",
                f"- Coefficient on trade openness: **{est['coefficient']:+.4f}**",
                f"- Clustered standard error: **{est['std_error']:.4f}**",
                f"- p-value: **{est['p_value']:.4f}**",
                f"- Observations: **{est['n_obs']:,}** country-years across **{est['n_countries']}** countries",
                f"- Within R-squared: **{est['r_squared_within']:.4f}**",
                f"- Raw high-trade-quartile top-share contrast: **{est['raw_high_trade_quartile_minus_rest']:+.4f} pp**",
            ]
        )
    card = f"""# Result card - {HID}

**Verdict:** {verdict} - {reason}.

## Plain-English Claim

Higher WDI trade openness should be positively associated with WID top 0.1 percent pre-tax income shares after country/year fixed effects and GDP, population, and regulatory-quality controls.

## Estimate

{chr(10).join(estimate_lines)}

## Specification

`top_0_1_pretax_income_share ~ trade_open_gdp + log_gdp_pc_ppp + regulatory_quality + log_population + country_FE + year_FE`

The sample is 1996-2023 after the WGI join, with countries requiring at least 15 paired observations. This is an associational panel screen, not a causal trade-shock design. The raw quartile contrast is descriptive context only and is not used for the verdict.

## Data

Vintages and SHA-256 hashes are pinned in `manifest.yaml`; row-level panel data for visualization is in `chart_data.json`.
"""
    (OUT / "result_card.md").write_text(card)


def main() -> int:
    panel, manifest = build_panel()
    est = estimate(panel)
    verdict, reason = verdict_from_estimate(est)
    write_outputs(panel, manifest, est, verdict, reason)
    print(f"{HID}: {verdict} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
