#!/usr/bin/env python3
"""Exact/proxy OECD productivity wrappers for Worker D wave 2.

The functions in this module write run-local IESET artifacts for a narrow set
of OECD/PWT/STAN productivity, competition, services-trade, and wage hypotheses.
They prefer on-disk public vintages and record missing exact series explicitly
instead of silently promoting broad proxies.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = Path(__file__).resolve().parent

INPUTS = {
    "oecd_pdb": ROOT / "data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet",
    "oecd_pmr": ROOT / "data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet",
    "pmr_barrier_entry": ROOT / "data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet",
    "pmr_barrier_trade": ROOT / "data/vintages/oecd_pmr/BARRIER_TRADE@2026-05-02T220000Z.parquet",
    "pmr_network": ROOT / "data/vintages/oecd_pmr/NETWORK_SECTORS@2026-05-02T220000Z.parquet",
    "pmr_state_invol": ROOT / "data/vintages/oecd_pmr/STATE_INVOL@2026-05-02T220000Z.parquet",
    "pmr_tariffs": ROOT / "data/vintages/oecd_pmr/TARIFFS@2026-05-02T220000Z.parquet",
    "stan": ROOT / "data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet",
    "pwt_full": ROOT / "data/vintages/pwt/pwt_full@2026-05-05T195237Z.parquet",
    "wgi_rq": ROOT / "data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet",
    "wgi_rl": ROOT / "data/vintages/wgi/GOV_WGI_RL.EST@2026-05-05T195218Z.parquet",
    "wdi_gdp_pc": ROOT / "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T113730Z.parquet",
    "wdi_gdp_pc_ppp": ROOT / "data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet",
    "wdi_trade": ROOT / "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
    "wdi_manufacturing_share": ROOT / "data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet",
    "wdi_services_share": ROOT / "data/vintages/world_bank_wdi/NV.SRV.TOTL.ZS@2026-05-05T195011Z.parquet",
    "wdi_cpi": ROOT / "data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-04-30T135619Z.parquet",
    "owid_top1": ROOT / "data/vintages/owid/top-1-share-of-total-income@2026-05-05T195312Z.parquet",
    "bis_spp": ROOT / "data/vintages/bis/WS_SPP@2026-05-12T132625Z.parquet",
}

VINTAGE_META = {
    "oecd_pdb": ("oecd", "DSD_PDB", "OECD Productivity Database"),
    "oecd_pmr": ("oecd_pmr", "PMR", "OECD product market regulation"),
    "pmr_barrier_entry": ("oecd_pmr", "BARRIER_ENTRY", "OECD PMR barriers to entry"),
    "pmr_barrier_trade": ("oecd_pmr", "BARRIER_TRADE", "OECD PMR barriers to trade/investment"),
    "pmr_network": ("oecd_pmr", "NETWORK_SECTORS", "OECD PMR network-sector regulation"),
    "pmr_state_invol": ("oecd_pmr", "STATE_INVOL", "OECD PMR state involvement"),
    "pmr_tariffs": ("oecd_pmr", "TARIFFS", "OECD PMR tariffs"),
    "stan": ("oecd_stan", "STAN", "OECD STAN value added"),
    "pwt_full": ("pwt", "pwt_full", "Penn World Table full panel"),
    "wgi_rq": ("wgi", "GOV_WGI_RQ.EST", "World Governance Indicators regulatory quality"),
    "wgi_rl": ("wgi", "GOV_WGI_RL.EST", "World Governance Indicators rule of law"),
    "wdi_gdp_pc": ("world_bank_wdi", "NY.GDP.PCAP.KD", "WDI real GDP per capita"),
    "wdi_gdp_pc_ppp": ("world_bank_wdi", "NY.GDP.PCAP.PP.KD", "WDI real GDP per capita PPP"),
    "wdi_trade": ("world_bank_wdi", "NE.TRD.GNFS.ZS", "WDI trade openness"),
    "wdi_manufacturing_share": ("world_bank_wdi", "NV.IND.MANF.ZS", "WDI manufacturing share"),
    "wdi_services_share": ("world_bank_wdi", "NV.SRV.TOTL.ZS", "WDI services share"),
    "wdi_cpi": ("world_bank_wdi", "FP.CPI.TOTL.ZG", "WDI CPI inflation"),
    "owid_top1": ("owid", "top-1-share-of-total-income", "OWID/WID top 1 percent income share"),
    "bis_spp": ("bis", "WS_SPP", "BIS real property price index"),
}

COUNTRY2_TO_ISO3 = {
    "AU": "AUS",
    "AT": "AUT",
    "BE": "BEL",
    "CA": "CAN",
    "CH": "CHE",
    "CL": "CHL",
    "CO": "COL",
    "CZ": "CZE",
    "DE": "DEU",
    "DK": "DNK",
    "EE": "EST",
    "ES": "ESP",
    "FI": "FIN",
    "FR": "FRA",
    "GB": "GBR",
    "GR": "GRC",
    "HU": "HUN",
    "IE": "IRL",
    "IL": "ISR",
    "IS": "ISL",
    "IT": "ITA",
    "JP": "JPN",
    "KR": "KOR",
    "LT": "LTU",
    "LU": "LUX",
    "LV": "LVA",
    "MX": "MEX",
    "NL": "NLD",
    "NO": "NOR",
    "NZ": "NZL",
    "PL": "POL",
    "PT": "PRT",
    "SE": "SWE",
    "SI": "SVN",
    "SK": "SVK",
    "TR": "TUR",
    "US": "USA",
}

OECD_FRONTIER = [
    "AUS",
    "AUT",
    "BEL",
    "CAN",
    "CHE",
    "CHL",
    "COL",
    "CZE",
    "DEU",
    "DNK",
    "ESP",
    "EST",
    "FIN",
    "FRA",
    "GBR",
    "GRC",
    "HUN",
    "IRL",
    "ISR",
    "ITA",
    "JPN",
    "KOR",
    "MEX",
    "NLD",
    "NOR",
    "NZL",
    "POL",
    "PRT",
    "SVK",
    "SVN",
    "SWE",
    "TUR",
    "USA",
]

TOP1_SAMPLE = [
    "USA",
    "GBR",
    "CAN",
    "AUS",
    "NZL",
    "DEU",
    "FRA",
    "ITA",
    "ESP",
    "NLD",
    "SWE",
    "NOR",
    "DNK",
    "FIN",
    "JPN",
    "KOR",
    "CHE",
    "BEL",
    "AUT",
    "IRL",
]

LABOR_REFORM_SAMPLE = [
    "USA",
    "GBR",
    "CAN",
    "AUS",
    "NZL",
    "DEU",
    "FRA",
    "ITA",
    "ESP",
    "NLD",
    "SWE",
    "NOR",
    "DNK",
    "FIN",
    "JPN",
    "KOR",
    "CHN",
    "IND",
    "BRA",
    "MEX",
    "CHL",
    "ARG",
    "TUR",
    "ZAF",
    "POL",
    "EST",
    "VNM",
    "THA",
    "MYS",
    "IDN",
    "COL",
    "PER",
    "PHL",
    "EGY",
    "MAR",
    "KEN",
    "NGA",
    "BGD",
    "PAK",
    "LKA",
]

SERVICE_ACTIVITIES = ["G", "H", "J", "M_N"]

HYPOTHESIS_PATHS = {
    "sectoral_competition_services_productivity": ROOT
    / "hypotheses/regulatory/sectoral_competition_services_productivity.yaml",
    "services_trade_liberalisation_frontier_growth": ROOT
    / "hypotheses/trade/services_trade_liberalisation_frontier_growth.yaml",
    "oecd_product_market_deregulation_tfp_panel": ROOT
    / "hypotheses/regulatory/oecd_product_market_deregulation_tfp_panel.yaml",
    "working_time_regulation_productivity_per_hour": ROOT
    / "hypotheses/labour/working_time_regulation_productivity_per_hour.yaml",
    "top_1_percent_income_share_growth_drivers": ROOT
    / "hypotheses/distribution/top_1_percent_income_share_growth_drivers.yaml",
    "labor_reform_real_wage_growth": ROOT
    / "hypotheses/labour/labor_reform_real_wage_growth.yaml",
}


def ascii_safe(value: object) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2011": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2265": ">=",
        "\u2264": "<=",
        "\u03b1": "alpha",
        "\u03b2": "beta",
        "\u0394": "Delta",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zscore(series: pd.Series, invert: bool = False) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce")
    sd = series.std(ddof=0)
    if not sd or math.isnan(float(sd)):
        out = series * np.nan
    else:
        out = (series - series.mean()) / sd
    return -out if invert else out


def hypothesis_spec(hid: str) -> dict[str, object]:
    path = HYPOTHESIS_PATHS[hid]
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {}


def manifest_inputs(keys: list[str]) -> list[dict[str, object]]:
    items = []
    for key in keys:
        path = INPUTS[key]
        publisher, series_id, label = VINTAGE_META[key]
        items.append(
            {
                "name": label,
                "publisher": publisher,
                "series_id": series_id,
                "vintage_file": rel(path),
                "sha256": sha256(path),
            }
        )
    return items


def load_wdi(key: str, name: str) -> pd.DataFrame:
    return (
        pd.read_parquet(INPUTS[key])[["country_iso3", "year", "value"]]
        .assign(country_iso3=lambda d: d["country_iso3"].astype(str))
        .query("country_iso3 != ''")
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype("Int64"))
        .dropna(subset=["year"])
        .assign(year=lambda d: d["year"].astype(int), value=lambda d: pd.to_numeric(d["value"], errors="coerce"))
        .rename(columns={"value": name})
    )


def load_wgi(key: str, name: str) -> pd.DataFrame:
    return (
        pd.read_parquet(INPUTS[key])[["country_iso3", "year", "value"]]
        .assign(country_iso3=lambda d: d["country_iso3"].astype(str))
        .query("country_iso3 != ''")
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype("Int64"))
        .dropna(subset=["year"])
        .assign(year=lambda d: d["year"].astype(int), value=lambda d: pd.to_numeric(d["value"], errors="coerce"))
        .rename(columns={"value": name})
    )


def pmr_simple(key: str, name: str) -> pd.DataFrame:
    return (
        pd.read_parquet(INPUTS[key])
        .rename(columns={"value": name})
        .assign(
            country_iso3=lambda d: d["country_iso3"].astype(str),
            year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype("Int64"),
            **{name: lambda d: pd.to_numeric(d[name], errors="coerce")},
        )
        .dropna(subset=["year"])
        .assign(year=lambda d: d["year"].astype(int))
    )


def pmr_measure(measure: str, name: str) -> pd.DataFrame:
    raw = pd.read_parquet(INPUTS["oecd_pmr"])
    return (
        raw.loc[raw["MEASURE"].eq(measure), ["REF_AREA", "period", "value"]]
        .rename(columns={"REF_AREA": "country_iso3", "period": "year", "value": name})
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype("Int64"))
        .dropna(subset=["year"])
        .assign(year=lambda d: d["year"].astype(int), **{name: lambda d: pd.to_numeric(d[name], errors="coerce")})
    )


def pdb_series(measure: str, activity: str, transformation: str, price_base: str, name: str) -> pd.DataFrame:
    pdb = pd.read_parquet(INPUTS["oecd_pdb"])
    return (
        pdb.loc[
            pdb["MEASURE"].eq(measure)
            & pdb["ACTIVITY"].eq(activity)
            & pdb["TRANSFORMATION"].eq(transformation)
            & pdb["PRICE_BASE"].eq(price_base),
            ["REF_AREA", "period", "value"],
        ]
        .rename(columns={"REF_AREA": "country_iso3", "period": "year", "value": name})
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype("Int64"))
        .dropna(subset=["year"])
        .assign(year=lambda d: d["year"].astype(int), **{name: lambda d: pd.to_numeric(d[name], errors="coerce")})
    )


def pdb_activity_average(measure: str, activities: list[str], transformation: str, price_base: str, name: str) -> pd.DataFrame:
    frames = [
        pdb_series(measure, activity, transformation, price_base, f"{name}_{activity}")
        for activity in activities
    ]
    data = frames[0]
    for frame in frames[1:]:
        data = data.merge(frame, on=["country_iso3", "year"], how="outer")
    cols = [c for c in data.columns if c.startswith(f"{name}_")]
    data[name] = data[cols].mean(axis=1, skipna=True)
    return data[["country_iso3", "year", name]]


def stan_share(activities: list[str], name: str) -> pd.DataFrame:
    stan = pd.read_parquet(INPUTS["stan"])
    base = stan.loc[
        stan["MEASURE"].eq("B1G")
        & stan["PRICE_BASE"].eq("V")
        & stan["ACTIVITY"].isin(activities + ["_T"]),
        ["REF_AREA", "ACTIVITY", "TIME_PERIOD", "OBS_VALUE"],
    ].copy()
    base["year"] = pd.to_numeric(base["TIME_PERIOD"], errors="coerce")
    base["value"] = pd.to_numeric(base["OBS_VALUE"], errors="coerce")
    parts = (
        base.loc[base["ACTIVITY"].isin(activities)]
        .groupby(["REF_AREA", "year"], as_index=False)["value"]
        .sum()
        .rename(columns={"value": "sector_value"})
    )
    total = (
        base.loc[base["ACTIVITY"].eq("_T"), ["REF_AREA", "year", "value"]]
        .rename(columns={"value": "total_value"})
    )
    out = parts.merge(total, on=["REF_AREA", "year"], how="inner")
    out[name] = 100.0 * out["sector_value"] / out["total_value"]
    return (
        out.rename(columns={"REF_AREA": "country_iso3"})[["country_iso3", "year", name]]
        .dropna()
        .assign(year=lambda d: d["year"].astype(int))
    )


def endpoint_change(df: pd.DataFrame, value_col: str, start: int, end: int, name: str) -> pd.DataFrame:
    data = df.loc[df["year"].between(start, end), ["country_iso3", "year", value_col]].dropna()
    rows = []
    for country, group in data.groupby("country_iso3"):
        group = group.sort_values("year")
        if len(group) < 2:
            continue
        first = group.iloc[0]
        last = group.iloc[-1]
        rows.append(
            {
                "country_iso3": country,
                f"{name}_start_year": int(first["year"]),
                f"{name}_end_year": int(last["year"]),
                f"{name}_start": float(first[value_col]),
                f"{name}_end": float(last[value_col]),
                name: float(last[value_col]) - float(first[value_col]),
            }
        )
    return pd.DataFrame(rows)


def window_mean(df: pd.DataFrame, value_col: str, start: int, end: int, name: str) -> pd.DataFrame:
    return (
        df.loc[df["year"].between(start, end), ["country_iso3", value_col]]
        .dropna()
        .groupby("country_iso3", as_index=False)[value_col]
        .mean()
        .rename(columns={value_col: name})
    )


def panel_ols(
    data: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    entity_fe: bool = False,
    time_fe: bool = False,
    cluster: str | None = None,
) -> tuple[dict[str, object], pd.DataFrame]:
    cols = ["country_iso3", "year", outcome] + predictors
    if cluster and cluster not in cols:
        cols.append(cluster)
    model_data = data[cols].dropna().copy()
    y = pd.to_numeric(model_data[outcome], errors="coerce")
    x = model_data[predictors].apply(pd.to_numeric, errors="coerce")
    if entity_fe:
        x = pd.concat(
            [x, pd.get_dummies(model_data["country_iso3"], prefix="country", drop_first=True)],
            axis=1,
        )
    if time_fe:
        x = pd.concat(
            [x, pd.get_dummies(model_data["year"], prefix="year", drop_first=True)],
            axis=1,
        )
    x = sm.add_constant(x, has_constant="add").astype(float)
    y = y.astype(float)
    if len(model_data) <= len(x.columns):
        raise ValueError(f"not enough rows for OLS: rows={len(model_data)}, columns={len(x.columns)}")
    fit = sm.OLS(y, x, missing="drop").fit()
    if cluster and model_data[cluster].nunique() > 1:
        fit = fit.get_robustcov_results(cov_type="cluster", groups=model_data[cluster])
    else:
        fit = fit.get_robustcov_results(cov_type="HC1")
    params = pd.Series(fit.params, index=x.columns)
    bse = pd.Series(fit.bse, index=x.columns)
    pvalues = pd.Series(fit.pvalues, index=x.columns)
    result = {
        "outcome": outcome,
        "predictors": predictors,
        "n_obs": int(fit.nobs),
        "n_countries": int(model_data["country_iso3"].nunique()),
        "year_min": int(model_data["year"].min()) if "year" in model_data else None,
        "year_max": int(model_data["year"].max()) if "year" in model_data else None,
        "r_squared": float(fit.rsquared),
        "entity_fe": entity_fe,
        "time_fe": time_fe,
        "covariance": "clustered by country" if cluster else "HC1 robust",
        "terms": {},
    }
    for predictor in predictors:
        result["terms"][predictor] = {
            "coefficient": float(params[predictor]),
            "std_error": float(bse[predictor]),
            "p_value": float(pvalues[predictor]),
        }
    return result, model_data


def write_artifacts(
    hid: str,
    verdict_label: str,
    verdict_reason: str,
    method: str,
    estimates: list[dict[str, object]],
    panel: pd.DataFrame,
    input_keys: list[str],
    loaded: list[dict[str, str]],
    missing: list[dict[str, str]],
    caveats: list[str],
    interpretation: str,
    coefficients: pd.DataFrame | None = None,
) -> None:
    run_dir = RUNS_DIR / hid
    run_dir.mkdir(parents=True, exist_ok=True)
    spec = hypothesis_spec(hid)
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    runner = rel(run_dir / "replication.py")
    verdict = f"{verdict_label} - {verdict_reason}"

    chart_rows = panel.replace({np.nan: None}).to_dict(orient="records")
    (run_dir / "chart_data.json").write_text(json.dumps(chart_rows, indent=2, default=str) + "\n", encoding="utf-8")

    if coefficients is None:
        rows = []
        for estimate in estimates:
            for term, stats in estimate.get("terms", {}).items():
                rows.append(
                    {
                        "outcome": estimate.get("outcome"),
                        "term": term,
                        "coefficient": stats.get("coefficient"),
                        "std_error": stats.get("std_error"),
                        "p_value": stats.get("p_value"),
                        "n_obs": estimate.get("n_obs"),
                        "n_countries": estimate.get("n_countries"),
                        "r_squared": estimate.get("r_squared"),
                    }
                )
        coefficients = pd.DataFrame(rows)
    coefficients.to_parquet(run_dir / "coefficients.parquet", index=False)

    diagnostics = {
        "hypothesis_id": hid,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "method": method,
        "runner": runner,
        "run_utc": generated_utc,
        "claim": ascii_safe(spec.get("claim")),
        "falsification_rule": ascii_safe((spec.get("falsification") or {}).get("rule")),
        "falsification_test": ascii_safe((spec.get("falsification") or {}).get("test")),
        "estimates": estimates,
        "data_status": {
            "variables_loaded": loaded,
            "variables_missing_or_proxied": missing,
        },
        "caveats": caveats,
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "hypothesis_id": hid,
        "status": verdict_label,
        "reason": verdict_reason,
        "method": method,
        "runner": runner,
        "run_utc": generated_utc,
        "vintages": manifest_inputs(input_keys),
        "variables_loaded": loaded,
        "missing_or_proxied_series": missing,
        "deviations": caveats,
    }
    (run_dir / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )

    evidence = {
        "hypothesis_id": hid,
        "verdict": verdict,
        "primary_estimates": estimates,
        "interpretation": ascii_safe(interpretation),
        "artifact_files": [
            "result_card.md",
            "diagnostics.json",
            "manifest.yaml",
            "coefficients.parquet",
            "chart_data.json",
            "evidence_packet.yaml",
        ],
    }
    (run_dir / "evidence_packet.yaml").write_text(
        yaml.safe_dump(evidence, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )

    claim = ascii_safe(spec.get("claim"))
    rule = ascii_safe((spec.get("falsification") or {}).get("rule"))
    test = ascii_safe((spec.get("falsification") or {}).get("test"))
    md = [
        f"# Result card - {hid}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Pre-registration",
        f"- **Claim:** {claim}",
        f"- **Falsification rule:** {rule}",
        f"- **Falsification test:** {test}" if test else "- **Falsification test:** not specified in current YAML",
        "",
        "## Method",
        ascii_safe(method),
        "",
        "## Estimates",
    ]
    for estimate in estimates:
        md.append(f"### {estimate.get('outcome')}")
        md.append(
            f"- Sample: n={estimate.get('n_obs')}, countries={estimate.get('n_countries')}, "
            f"years={estimate.get('year_min')}-{estimate.get('year_max')}"
        )
        md.append(f"- R-squared: {float(estimate.get('r_squared', 0.0)):.3f}")
        for term, stats in estimate.get("terms", {}).items():
            md.append(
                f"- `{term}`: beta={stats['coefficient']:+.4g}, "
                f"se={stats['std_error']:.4g}, p={stats['p_value']:.4g}"
            )
        extra = estimate.get("extra")
        if extra:
            for key, value in extra.items():
                md.append(f"- {ascii_safe(key)}: {ascii_safe(value)}")
        md.append("")
    md.extend(
        [
            "## Interpretation",
            ascii_safe(interpretation),
            "",
            "## Variables Loaded",
        ]
    )
    md.extend(f"- `{item['name']}` ({item['role']}): {item['source']}" for item in loaded)
    md.append("")
    md.append("## Missing Or Proxied")
    md.extend(f"- `{item['name']}` ({item['role']}): {item['source']}" for item in missing)
    md.append("")
    md.append("## Source Paths")
    for item in manifest_inputs(input_keys):
        md.append(f"- `{item['name']}` -> `{item['vintage_file']}`")
    md.append("")
    md.append("## Caveats")
    md.extend(f"- {ascii_safe(caveat)}" for caveat in caveats)
    md.append("")
    (run_dir / "result_card.md").write_text("\n".join(md), encoding="utf-8")

    print(f"{hid}: {verdict}")


def run_sectoral_competition() -> None:
    hid = "sectoral_competition_services_productivity"
    service_prod = window_mean(
        pdb_activity_average("GVAHRS", SERVICE_ACTIVITIES, "GY", "LR", "services_gvahrs_growth"),
        "services_gvahrs_growth",
        2019,
        2024,
        "services_productivity_growth_2019_2024",
    )
    total_prod = window_mean(
        pdb_series("GDPHRS", "_T", "GY", "L", "total_gdphrs_growth"),
        "total_gdphrs_growth",
        2019,
        2024,
        "total_productivity_growth_2019_2024",
    )
    manufacturing = window_mean(
        pdb_series("GVAHRS", "C", "GY", "LR", "manufacturing_gvahrs_growth"),
        "manufacturing_gvahrs_growth",
        2019,
        2024,
        "manufacturing_productivity_growth_2019_2024",
    )
    prof = pmr_measure("PROFSERV", "pmr_professional_services")
    entry = pmr_simple("pmr_barrier_entry", "pmr_barrier_entry")
    network = pmr_simple("pmr_network", "pmr_network")
    state = pmr_simple("pmr_state_invol", "pmr_state_involvement")
    controls = (
        load_wdi("wdi_gdp_pc", "gdp_pc")
        .loc[lambda d: d["year"].eq(2018)]
        .assign(log_gdp_pc_2018=lambda d: np.log(d["gdp_pc"]))
        [["country_iso3", "log_gdp_pc_2018"]]
        .merge(
            load_wdi("wdi_manufacturing_share", "manufacturing_share_2018")
            .loc[lambda d: d["year"].eq(2018), ["country_iso3", "manufacturing_share_2018"]],
            on="country_iso3",
            how="outer",
        )
    )
    panel = (
        prof.loc[prof["year"].eq(2023)]
        .merge(entry.loc[entry["year"].eq(2023)], on=["country_iso3", "year"], how="outer")
        .merge(network.loc[network["year"].eq(2023)], on=["country_iso3", "year"], how="outer")
        .merge(state.loc[state["year"].eq(2023)], on=["country_iso3", "year"], how="outer")
        .merge(service_prod, on="country_iso3", how="inner")
        .merge(total_prod, on="country_iso3", how="left")
        .merge(manufacturing, on="country_iso3", how="left")
        .merge(controls, on="country_iso3", how="left")
    )
    panel = panel.loc[panel["country_iso3"].isin(OECD_FRONTIER)].copy()
    panel["services_competition_index"] = zscore(
        panel[["pmr_professional_services", "pmr_barrier_entry", "pmr_network"]].mean(axis=1),
        invert=True,
    )
    panel["state_involvement_z"] = zscore(panel["pmr_state_involvement"])
    estimate, model_data = panel_ols(
        panel,
        "services_productivity_growth_2019_2024",
        ["services_competition_index", "state_involvement_z", "log_gdp_pc_2018", "manufacturing_share_2018"],
    )
    terciles = model_data.copy()
    terciles["tercile"] = pd.qcut(terciles["services_competition_index"], 3, labels=["bottom", "middle", "top"])
    means = terciles.groupby("tercile", observed=True)["services_productivity_growth_2019_2024"].mean()
    gap = float(means.get("top", np.nan) - means.get("bottom", np.nan))
    estimate["extra"] = {
        "top_minus_bottom_services_competition_gap_pp_per_year": round(gap, 4),
        "top_tercile_mean": round(float(means.get("top", np.nan)), 4),
        "bottom_tercile_mean": round(float(means.get("bottom", np.nan)), 4),
    }
    beta = estimate["terms"]["services_competition_index"]["coefficient"]
    pval = estimate["terms"]["services_competition_index"]["p_value"]
    state_t = abs(
        estimate["terms"]["state_involvement_z"]["coefficient"]
        / estimate["terms"]["state_involvement_z"]["std_error"]
    )
    service_t = abs(beta / estimate["terms"]["services_competition_index"]["std_error"])
    if beta > 0 and pval < 0.10 and gap >= 0.3 and service_t > state_t:
        verdict, reason = "SUPPORTED", "services competition clears the proxy horse-race and top-tercile productivity gates"
    elif beta < 0 and pval < 0.10:
        verdict, reason = "REFUTED", "services competition has a statistically negative proxy coefficient"
    else:
        verdict, reason = "PARTIAL", "proxy horse-race does not clear the registered positive/significant services-productivity gate"
    write_artifacts(
        hid,
        verdict,
        reason,
        "Cross-sectional OECD 2023 PMR services-competition proxy against 2019-2024 PDB services labour-productivity growth; HC1 robust OLS with initial income and manufacturing-share controls.",
        [estimate],
        panel,
        ["oecd_pdb", "oecd_pmr", "pmr_barrier_entry", "pmr_network", "pmr_state_invol", "wdi_gdp_pc", "wdi_manufacturing_share"],
        [
            {"role": "outcome", "name": "services_productivity_growth_2019_2024", "source": "oecd_pdb:GVAHRS_GY_L averaged over G,H,J,M_N"},
            {"role": "treatment", "name": "services_competition_index", "source": "inverted z-score of OECD PMR PROFSERV, BARRIER_ENTRY, NETWORK_SECTORS"},
            {"role": "horse_race_proxy", "name": "state_involvement_z", "source": "oecd_pmr:STATE_INVOL"},
            {"role": "controls", "name": "log_gdp_pc_2018, manufacturing_share_2018", "source": "world_bank_wdi"},
        ],
        [
            {"role": "exact_treatment", "name": "manufacturing_industrial_policy_spending", "source": "constructed state-aid/subsidy/directed-credit series not local"},
            {"role": "exact_treatment", "name": "services-sector churn", "source": "firm entry/exit microdata not local"},
        ],
        [
            "PMR coverage is limited to 2018 and 2023, so the test is a short-window proxy rather than a 1990-2020 panel.",
            "Services productivity uses PDB GVA per hour for retail/transport/information/professional activities as the local STAN-equivalent proxy.",
        ],
        "The local OECD proxy does not provide a clean services-competition win over state-involvement controls; keep the artifact research-only until longer PMR/STAN coverage and direct industrial-policy spending are loaded.",
    )


def run_services_trade() -> None:
    hid = "services_trade_liberalisation_frontier_growth"
    services_mfp = window_mean(
        pdb_activity_average("MFPH", SERVICE_ACTIVITIES, "GY", "LR", "services_mfp_growth"),
        "services_mfp_growth",
        2019,
        2024,
        "services_mfp_growth_2019_2024",
    )
    total_mfp = window_mean(
        pdb_series("MFPH", "_T", "GY", "LR", "total_mfp_growth"),
        "total_mfp_growth",
        2019,
        2024,
        "total_mfp_growth_2019_2024",
    )
    trade_barrier = pmr_simple("pmr_barrier_trade", "pmr_barrier_trade")
    state = pmr_simple("pmr_state_invol", "pmr_state_involvement")
    tariffs = pmr_simple("pmr_tariffs", "pmr_tariffs")
    controls = (
        load_wdi("wdi_gdp_pc", "gdp_pc")
        .loc[lambda d: d["year"].eq(2018)]
        .assign(log_gdp_pc_2018=lambda d: np.log(d["gdp_pc"]))
        [["country_iso3", "log_gdp_pc_2018"]]
        .merge(
            pd.read_parquet(INPUTS["pwt_full"])[["country_iso3", "year", "rtfpna"]]
            .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype(int))
            .loc[lambda d: d["year"].eq(2018)]
            .assign(log_tfp_2018=lambda d: np.log(pd.to_numeric(d["rtfpna"], errors="coerce")))
            [["country_iso3", "log_tfp_2018"]],
            on="country_iso3",
            how="outer",
        )
    )
    barrier_wide = trade_barrier.pivot(index="country_iso3", columns="year", values="pmr_barrier_trade").reset_index()
    barrier_wide["services_trade_liberalisation_2018_2023"] = barrier_wide.get(2018) - barrier_wide.get(2023)
    barrier_wide["services_trade_liberalisation_z"] = zscore(barrier_wide["services_trade_liberalisation_2018_2023"])
    state_2023 = state.loc[state["year"].eq(2023), ["country_iso3", "pmr_state_involvement"]]
    tariffs_2023 = tariffs.loc[tariffs["year"].eq(2023), ["country_iso3", "pmr_tariffs"]]
    panel = (
        barrier_wide[["country_iso3", "services_trade_liberalisation_2018_2023", "services_trade_liberalisation_z"]]
        .merge(state_2023, on="country_iso3", how="left")
        .merge(tariffs_2023, on="country_iso3", how="left")
        .merge(services_mfp, on="country_iso3", how="inner")
        .merge(total_mfp, on="country_iso3", how="left")
        .merge(controls, on="country_iso3", how="left")
    )
    panel["goods_policy_intensity_z"] = zscore(panel[["pmr_state_involvement", "pmr_tariffs"]].mean(axis=1))
    panel = panel.loc[panel["country_iso3"].isin(OECD_FRONTIER)].copy()
    panel["year"] = 2024
    estimate, _ = panel_ols(
        panel,
        "services_mfp_growth_2019_2024",
        ["services_trade_liberalisation_z", "goods_policy_intensity_z", "log_gdp_pc_2018", "log_tfp_2018"],
    )
    beta = estimate["terms"]["services_trade_liberalisation_z"]["coefficient"]
    pval = estimate["terms"]["services_trade_liberalisation_z"]["p_value"]
    goods_beta = estimate["terms"]["goods_policy_intensity_z"]["coefficient"]
    goods_p = estimate["terms"]["goods_policy_intensity_z"]["p_value"]
    if beta > 0 and pval < 0.10 and abs(beta) > abs(goods_beta):
        verdict, reason = "PARTIAL", "services-trade proxy clears the directional gate but exact STRI and goods-subsidy series are absent"
    elif beta < 0 and pval < 0.10:
        verdict, reason = "REFUTED", "services-trade liberalisation proxy has a statistically negative MFP association"
    elif goods_beta > beta and goods_p < 0.10:
        verdict, reason = "REFUTED", "goods-policy proxy outperforms the services-trade proxy in the local horse-race"
    else:
        verdict, reason = "INCONCLUSIVE_DATA_PENDING", "local PMR trade-barrier proxy does not settle the STRI/services-TFP hypothesis"
    write_artifacts(
        hid,
        verdict,
        reason,
        "Cross-sectional OECD proxy: decline in PMR barriers to trade/investment from 2018 to 2023 predicts 2019-2024 PDB services MFP growth, compared with state-involvement/tariff goods-policy proxy.",
        [estimate],
        panel,
        ["oecd_pdb", "pmr_barrier_trade", "pmr_state_invol", "pmr_tariffs", "pwt_full", "wdi_gdp_pc"],
        [
            {"role": "outcome_proxy", "name": "services_mfp_growth_2019_2024", "source": "oecd_pdb:MFPH_GY_LR averaged over G,H,J,M_N"},
            {"role": "treatment_proxy", "name": "services_trade_liberalisation_2018_2023", "source": "decline in oecd_pmr:BARRIER_TRADE"},
            {"role": "horse_race_proxy", "name": "goods_policy_intensity_z", "source": "oecd_pmr:STATE_INVOL and TARIFFS"},
            {"role": "controls", "name": "log_gdp_pc_2018, log_tfp_2018", "source": "WDI and PWT"},
        ],
        [
            {"role": "exact_treatment", "name": "OECD STRI overall/services-sector index", "source": "not local"},
            {"role": "exact_outcome", "name": "EU KLEMS/OECD STAN sectoral TFP for services", "source": "not local beyond PDB MFP proxy"},
            {"role": "exact_horse_race", "name": "goods-sector subsidy intensity", "source": "CRDF/ITC/WITS subsidy panel not local"},
        ],
        [
            "PMR barriers to trade are a broad trade/investment-barrier proxy, not the OECD STRI.",
            "Only the 2018-2023 PMR change is local, so this is a short-window screen.",
        ],
        "The available local data are useful for triage but not dispositive: they replace STRI and goods subsidies with PMR trade/tariff/state-involvement proxies.",
    )


def run_oecd_pmr_tfp() -> None:
    hid = "oecd_product_market_deregulation_tfp_panel"
    mfp = window_mean(
        pdb_series("MFPH", "_T", "GY", "LR", "total_mfp_growth"),
        "total_mfp_growth",
        2019,
        2024,
        "mfp_growth_2019_2024",
    )
    lp = window_mean(
        pdb_series("GDPHRS", "_T", "GY", "L", "lp_growth"),
        "lp_growth",
        2019,
        2024,
        "lp_growth_2019_2024",
    )
    pmr = pmr_measure("PMR", "pmr_overall")
    pmr_wide = pmr.pivot(index="country_iso3", columns="year", values="pmr_overall").reset_index()
    pmr_wide["pmr_decline_2018_2023"] = pmr_wide.get(2018) - pmr_wide.get(2023)
    pmr_wide["pmr_decline_z"] = zscore(pmr_wide["pmr_decline_2018_2023"])
    controls = (
        pd.read_parquet(INPUTS["pwt_full"])[["country_iso3", "year", "rtfpna", "hc"]]
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype(int))
        .loc[lambda d: d["year"].eq(2018)]
        .assign(log_tfp_2018=lambda d: np.log(pd.to_numeric(d["rtfpna"], errors="coerce")))
        [["country_iso3", "log_tfp_2018", "hc"]]
        .merge(
            load_wdi("wdi_trade", "trade_openness_2018").loc[lambda d: d["year"].eq(2018), ["country_iso3", "trade_openness_2018"]],
            on="country_iso3",
            how="outer",
        )
    )
    panel = (
        pmr_wide[["country_iso3", "pmr_decline_2018_2023", "pmr_decline_z"]]
        .merge(mfp, on="country_iso3", how="inner")
        .merge(lp, on="country_iso3", how="left")
        .merge(controls, on="country_iso3", how="left")
    )
    panel = panel.loc[panel["country_iso3"].isin(OECD_FRONTIER)].copy()
    panel["year"] = 2024
    estimate_mfp, _ = panel_ols(panel, "mfp_growth_2019_2024", ["pmr_decline_z", "log_tfp_2018", "hc", "trade_openness_2018"])
    estimate_lp, _ = panel_ols(panel, "lp_growth_2019_2024", ["pmr_decline_z", "log_tfp_2018", "hc", "trade_openness_2018"])
    beta_mfp = estimate_mfp["terms"]["pmr_decline_z"]["coefficient"]
    p_mfp = estimate_mfp["terms"]["pmr_decline_z"]["p_value"]
    beta_lp = estimate_lp["terms"]["pmr_decline_z"]["coefficient"]
    p_lp = estimate_lp["terms"]["pmr_decline_z"]["p_value"]
    if beta_mfp > 0 and p_mfp < 0.05 and beta_lp > 0 and p_lp < 0.05:
        verdict, reason = "SUPPORTED", "PMR decline predicts both MFP and labour-productivity growth in the short-window proxy"
    elif beta_mfp < 0 and p_mfp < 0.05:
        verdict, reason = "REFUTED", "PMR decline has a statistically negative MFP association"
    else:
        verdict, reason = "PARTIAL", "short-window PMR decline proxy does not clear both positive/significant productivity gates"
    write_artifacts(
        hid,
        verdict,
        reason,
        "OECD cross-section replacing the infeasible two-year TWFE PMR panel with PMR decline from 2018 to 2023 and 2019-2024 PDB MFP/labour-productivity growth.",
        [estimate_mfp, estimate_lp],
        panel,
        ["oecd_pdb", "oecd_pmr", "pwt_full", "wdi_trade"],
        [
            {"role": "outcome", "name": "mfp_growth_2019_2024", "source": "oecd_pdb:MFPH_GY_LR total economy"},
            {"role": "outcome", "name": "lp_growth_2019_2024", "source": "oecd_pdb:GDPHRS_GY_L total economy"},
            {"role": "treatment", "name": "pmr_decline_2018_2023", "source": "decline in OECD PMR overall index"},
            {"role": "controls", "name": "log_tfp_2018, hc, trade_openness_2018", "source": "PWT and WDI"},
        ],
        [
            {"role": "exact_design", "name": "1998-2019 PMR panel", "source": "local PMR vintage has only 2018 and 2023"},
            {"role": "control", "name": "R&D intensity", "source": "not used because PDB R&D extraction is sparse in this window"},
        ],
        [
            "This repairs the previous no-within-country-variation failure by using the pre-registered PMR-change exposure as a cross-section.",
            "PDB MFP coverage is used instead of PWT TFP because the local PWT vintage ends before the 2023 PMR endpoint.",
        ],
        "The repaired local design is more informative than the failed FE rerun, but remains a short-window proxy around the 2018/2023 PMR vintages.",
    )


def run_working_time() -> None:
    hid = "working_time_regulation_productivity_per_hour"
    hours = pdb_series("HRSAV", "_T", "GY", "_Z", "avg_hours_growth")
    hours["hours_reduction"] = -hours["avg_hours_growth"]
    hourly = pdb_series("GDPHRS", "_T", "GY", "L", "hourly_productivity_growth")
    worker = pdb_series("GDPEMP", "_T", "GY", "L", "output_per_worker_growth")
    panel = (
        hours[["country_iso3", "year", "avg_hours_growth", "hours_reduction"]]
        .merge(hourly, on=["country_iso3", "year"], how="inner")
        .merge(worker, on=["country_iso3", "year"], how="inner")
    )
    panel = panel.loc[panel["year"].between(1990, 2023) & panel["country_iso3"].isin(OECD_FRONTIER)].copy()
    estimate_hourly, _ = panel_ols(
        panel,
        "hourly_productivity_growth",
        ["hours_reduction"],
        entity_fe=True,
        time_fe=True,
        cluster="country_iso3",
    )
    estimate_worker, _ = panel_ols(
        panel,
        "output_per_worker_growth",
        ["hours_reduction"],
        entity_fe=True,
        time_fe=True,
        cluster="country_iso3",
    )
    b_hour = estimate_hourly["terms"]["hours_reduction"]["coefficient"]
    p_hour = estimate_hourly["terms"]["hours_reduction"]["p_value"]
    b_worker = estimate_worker["terms"]["hours_reduction"]["coefficient"]
    p_worker = estimate_worker["terms"]["hours_reduction"]["p_value"]
    if b_hour > 0 and p_hour < 0.10 and b_worker < 0 and p_worker < 0.10:
        verdict, reason = "SUPPORTED", "hours reductions predict higher hourly productivity and lower output per worker"
    elif (b_hour < 0 and p_hour < 0.10) or (b_worker > 0 and p_worker < 0.10):
        verdict, reason = "REFUTED", "at least one registered sign is statistically opposite in the OECD PDB panel"
    else:
        verdict, reason = "PARTIAL", "OECD PDB panel does not clear both registered working-time sign/significance gates"
    write_artifacts(
        hid,
        verdict,
        reason,
        "OECD PDB country-year FE panel: GDP per hour and GDP per employed person growth on reductions in average hours worked per employee, with country and year fixed effects clustered by country.",
        [estimate_hourly, estimate_worker],
        panel,
        ["oecd_pdb"],
        [
            {"role": "treatment_proxy", "name": "hours_reduction", "source": "negative of oecd_pdb:HRSAV_GY total economy"},
            {"role": "outcome", "name": "hourly_productivity_growth", "source": "oecd_pdb:GDPHRS_GY total economy"},
            {"role": "outcome", "name": "output_per_worker_growth", "source": "oecd_pdb:GDPEMP_GY total economy"},
        ],
        [
            {"role": "exact_treatment", "name": "statutory working-time limits", "source": "policy/legal panel not local"},
            {"role": "welfare_outcome", "name": "welfare effects", "source": "not tested by PDB productivity data"},
        ],
        [
            "Average-hours reductions are an observed-outcome proxy for stricter working-time regulation.",
            "The result should not be read causally without statutory reform timing or instruments.",
        ],
        "The PDB productivity panel directly tests the productivity/output-per-worker pattern, but the policy treatment itself remains proxied by realised hours reductions.",
    )


def annual_bis_real_property_growth() -> pd.DataFrame:
    bis = pd.read_parquet(INPUTS["bis_spp"])
    data = bis.loc[bis["VALUE"].eq("R"), ["REF_AREA", "period", "value"]].copy()
    data["country_iso3"] = data["REF_AREA"].map(COUNTRY2_TO_ISO3)
    data["year"] = data["period"].astype(str).str[:4].astype(int)
    annual = (
        data.dropna(subset=["country_iso3"])
        .groupby(["country_iso3", "year"], as_index=False)["value"]
        .mean()
        .sort_values(["country_iso3", "year"])
    )
    annual["real_property_price_growth"] = annual.groupby("country_iso3")["value"].pct_change() * 100.0
    return annual[["country_iso3", "year", "real_property_price_growth"]]


def run_top1() -> None:
    hid = "top_1_percent_income_share_growth_drivers"
    top = (
        pd.read_parquet(INPUTS["owid_top1"])
        .rename(columns={"Share (top 1%, before tax)": "top1_share"})
        [["country_iso3", "year", "top1_share"]]
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype(int))
    )
    top_change = endpoint_change(top, "top1_share", 2015, 2022, "top1_share_change_2015_2022")
    skill = endpoint_change(stan_share(["J", "M_N"], "skill_services_share"), "skill_services_share", 2015, 2022, "skill_services_share_change")
    finance = endpoint_change(stan_share(["K"], "finance_share"), "finance_share", 2015, 2022, "finance_share_change")
    property_growth = window_mean(annual_bis_real_property_growth(), "real_property_price_growth", 2015, 2022, "real_property_growth_mean")
    entry = pmr_simple("pmr_barrier_entry", "barrier_entry_2023").loc[lambda d: d["year"].eq(2023), ["country_iso3", "barrier_entry_2023"]]
    controls = load_wdi("wdi_gdp_pc_ppp", "gdp_pc_ppp").loc[lambda d: d["year"].eq(2015), ["country_iso3", "gdp_pc_ppp"]]
    controls["log_gdp_pc_ppp_2015"] = np.log(controls["gdp_pc_ppp"])
    panel = (
        top_change[["country_iso3", "top1_share_change_2015_2022"]]
        .merge(skill[["country_iso3", "skill_services_share_change"]], on="country_iso3", how="inner")
        .merge(finance[["country_iso3", "finance_share_change"]], on="country_iso3", how="inner")
        .merge(property_growth, on="country_iso3", how="inner")
        .merge(entry, on="country_iso3", how="left")
        .merge(controls[["country_iso3", "log_gdp_pc_ppp_2015"]], on="country_iso3", how="left")
    )
    panel = panel.loc[panel["country_iso3"].isin(TOP1_SAMPLE)].copy()
    for col in ["skill_services_share_change", "real_property_growth_mean", "finance_share_change", "barrier_entry_2023"]:
        panel[f"{col}_z"] = zscore(panel[col])
    estimate, model_data = panel_ols(
        panel.assign(year=2022),
        "top1_share_change_2015_2022",
        [
            "skill_services_share_change_z",
            "real_property_growth_mean_z",
            "finance_share_change_z",
            "barrier_entry_2023_z",
            "log_gdp_pc_ppp_2015",
        ],
    )
    y = zscore(model_data["top1_share_change_2015_2022"])
    contrib = {}
    for col in [
        "skill_services_share_change_z",
        "real_property_growth_mean_z",
        "finance_share_change_z",
        "barrier_entry_2023_z",
    ]:
        beta = estimate["terms"][col]["coefficient"]
        corr = float(np.corrcoef(model_data[col], y)[0, 1])
        contrib[col] = max(0.0, beta * corr)
    total = sum(contrib.values()) or np.nan
    shares = {key: (value / total if total and not np.isnan(total) else np.nan) for key, value in contrib.items()}
    skill_capital = shares["skill_services_share_change_z"] + shares["real_property_growth_mean_z"]
    rent_concentration = shares["finance_share_change_z"] + shares["barrier_entry_2023_z"]
    estimate["extra"] = {
        "skill_plus_capital_contribution_share": round(float(skill_capital), 4),
        "rent_plus_concentration_contribution_share": round(float(rent_concentration), 4),
        "contribution_shares": {key: round(float(value), 4) for key, value in shares.items()},
    }
    min_p = min(estimate["terms"][col]["p_value"] for col in contrib)
    if skill_capital >= 0.40 and skill_capital > rent_concentration and min_p < 0.05:
        verdict, reason = "SUPPORTED", "proxy decomposition gives majority explanatory share to skill-services plus capital-appreciation channels"
    elif rent_concentration > skill_capital and min_p < 0.05:
        verdict, reason = "REFUTED", "rent/concentration proxy channels dominate the short-panel decomposition"
    else:
        verdict, reason = "PARTIAL", "short STAN/OWID proxy decomposition is informative but does not clear the registered majority/significance gate"
    write_artifacts(
        hid,
        verdict,
        reason,
        "Short-panel 2015-2022 OECD proxy decomposition of top-1 percent share changes using STAN skill-services and finance shares, BIS real property-price growth, and PMR barriers to entry.",
        [estimate],
        panel.assign(year=2022),
        ["owid_top1", "stan", "bis_spp", "pmr_barrier_entry", "wdi_gdp_pc_ppp"],
        [
            {"role": "outcome", "name": "top1_share_change_2015_2022", "source": "owid:top-1-share-of-total-income"},
            {"role": "skill_channel_proxy", "name": "skill_services_share_change", "source": "oecd_stan:J plus M_N value-added share"},
            {"role": "capital_channel_proxy", "name": "real_property_growth_mean", "source": "BIS real property price growth"},
            {"role": "rent_channel_proxy", "name": "finance_share_change", "source": "oecd_stan:K value-added share"},
            {"role": "concentration_proxy", "name": "barrier_entry_2023", "source": "oecd_pmr:BARRIER_ENTRY"},
        ],
        [
            {"role": "exact_skill_channel", "name": "specialist wage growth/superstar firm wages", "source": "micro wage-sector panel not local"},
            {"role": "exact_capital_channel", "name": "equity-price capital-income growth", "source": "BIS SPP is real property-price proxy, not equity index"},
            {"role": "exact_concentration_channel", "name": "Herfindahl/markup concentration", "source": "not local"},
            {"role": "long_panel", "name": "1980-2020 decomposition", "source": "local STAN vintage covers 2015-2022 only"},
        ],
        [
            "This is a short, proxy-only decomposition because the landed STAN vintage starts in 2015.",
            "Contribution shares use standardized beta times outcome correlation, normalized across the four pre-registered channels.",
        ],
        "The artifact repairs the earlier channel miswiring, but the short STAN window and asset-price proxy mean it should remain research-only.",
    )


def run_labor_reform_real_wage() -> None:
    hid = "labor_reform_real_wage_growth"
    wage = pdb_series("LCHRS", "_T", "GY", "V", "nominal_comp_hour_growth")
    cpi = load_wdi("wdi_cpi", "cpi_inflation")
    wage = wage.merge(cpi, on=["country_iso3", "year"], how="left")
    wage["real_comp_hour_growth_proxy"] = wage["nominal_comp_hour_growth"] - wage["cpi_inflation"]
    productivity = pdb_series("GDPHRS", "_T", "GY", "L", "labour_productivity_growth")
    rq = load_wgi("wgi_rq", "regulatory_quality")
    rq["regulatory_quality_lag"] = rq.groupby("country_iso3")["regulatory_quality"].shift(1)
    controls = (
        load_wdi("wdi_gdp_pc", "gdp_pc")
        .assign(log_gdp_pc=lambda d: np.log(d["gdp_pc"]))
        [["country_iso3", "year", "log_gdp_pc"]]
        .merge(load_wgi("wgi_rl", "rule_of_law"), on=["country_iso3", "year"], how="left")
    )
    panel = (
        wage[["country_iso3", "year", "real_comp_hour_growth_proxy", "nominal_comp_hour_growth", "cpi_inflation"]]
        .merge(productivity, on=["country_iso3", "year"], how="left")
        .merge(rq[["country_iso3", "year", "regulatory_quality_lag"]], on=["country_iso3", "year"], how="inner")
        .merge(controls, on=["country_iso3", "year"], how="left")
    )
    panel = panel.loc[panel["year"].between(1996, 2023) & panel["country_iso3"].isin(LABOR_REFORM_SAMPLE)].copy()
    estimate_wage, _ = panel_ols(
        panel,
        "real_comp_hour_growth_proxy",
        ["regulatory_quality_lag", "log_gdp_pc", "rule_of_law"],
        entity_fe=True,
        time_fe=True,
        cluster="country_iso3",
    )
    estimate_prod, _ = panel_ols(
        panel,
        "labour_productivity_growth",
        ["regulatory_quality_lag", "log_gdp_pc", "rule_of_law"],
        entity_fe=True,
        time_fe=True,
        cluster="country_iso3",
    )
    b_wage = estimate_wage["terms"]["regulatory_quality_lag"]["coefficient"]
    p_wage = estimate_wage["terms"]["regulatory_quality_lag"]["p_value"]
    b_prod = estimate_prod["terms"]["regulatory_quality_lag"]["coefficient"]
    p_prod = estimate_prod["terms"]["regulatory_quality_lag"]["p_value"]
    if b_wage > 0 and p_wage < 0.10 and b_prod > 0 and p_prod < 0.10:
        verdict, reason = "SUPPORTED", "lagged regulatory quality predicts both real compensation and productivity growth proxies"
    elif b_wage < 0 and p_wage < 0.10:
        verdict, reason = "REFUTED", "lagged regulatory quality has a statistically negative real-compensation association"
    else:
        verdict, reason = "PARTIAL", "exact wage/productivity proxy does not clear the positive/significant wage gate"
    write_artifacts(
        hid,
        verdict,
        reason,
        "Country-year FE panel using OECD PDB labour compensation per hour deflated by WDI CPI as the real-wage proxy, with lagged WGI regulatory quality and rule-of-law/income controls.",
        [estimate_wage, estimate_prod],
        panel,
        ["oecd_pdb", "wdi_cpi", "wgi_rq", "wgi_rl", "wdi_gdp_pc"],
        [
            {"role": "outcome_proxy", "name": "real_comp_hour_growth_proxy", "source": "oecd_pdb:LCHRS_GY total economy minus WDI CPI inflation"},
            {"role": "outcome", "name": "labour_productivity_growth", "source": "oecd_pdb:GDPHRS_GY total economy"},
            {"role": "treatment", "name": "regulatory_quality_lag", "source": "wgi:GOV_WGI_RQ.EST lagged one year"},
            {"role": "controls", "name": "log_gdp_pc, rule_of_law", "source": "WDI and WGI"},
        ],
        [
            {"role": "exact_outcome", "name": "real wage growth", "source": "OECD average-wage/median-wage real series not local for broad sample"},
            {"role": "exact_treatment", "name": "labour-market reform episodes", "source": "policy event panel not local"},
        ],
        [
            "The wage outcome is labour compensation per hour deflated by CPI, not a worker-level real wage series.",
            "Regulatory quality is a broad institutional proxy, not a specific labour reform treatment.",
        ],
        "This replaces the prior GDP-per-capita proxy with a closer compensation-per-hour proxy while preserving the registered direction test as research-only.",
    )


RUNNERS: dict[str, Callable[[], None]] = {
    "sectoral_competition_services_productivity": run_sectoral_competition,
    "services_trade_liberalisation_frontier_growth": run_services_trade,
    "oecd_product_market_deregulation_tfp_panel": run_oecd_pmr_tfp,
    "working_time_regulation_productivity_per_hour": run_working_time,
    "top_1_percent_income_share_growth_drivers": run_top1,
    "labor_reform_real_wage_growth": run_labor_reform_real_wage,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in RUNNERS:
        print("Usage: oecd_productivity_worker_d_exact.py <hypothesis_id>", file=sys.stderr)
        print("Known ids:", ", ".join(sorted(RUNNERS)), file=sys.stderr)
        return 2
    RUNNERS[argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
