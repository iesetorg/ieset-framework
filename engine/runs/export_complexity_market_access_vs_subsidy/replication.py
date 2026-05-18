#!/usr/bin/env python3
"""Proxy replication for market access versus subsidy export upgrading.

The preregistered Harvard Atlas ECI and direct subsidy-intensity panel are not
local. This run-local repair estimates a transparent proxy screen using WDI
high-tech export share, derived/WITS export diversification, WDI trade openness,
OECD PMR trade barriers, Fraser trade freedom, and state-burden proxies.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
HYPOTHESIS_ID = "export_complexity_market_access_vs_subsidy"

sys.path.insert(0, str(ROOT / "scripts"))
from run_panel_fe import (  # noqa: E402
    latest_vintage,
    load_variable,
    normalise_panel,
    run_panel_ols,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def zscore(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    sd = values.std(skipna=True)
    if not sd or not np.isfinite(sd):
        return values * np.nan
    return (values - values.mean(skipna=True)) / sd


def load_series(source: str, name: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    loaded = load_variable(source, variable_name=name)
    if loaded is None:
        raise RuntimeError(f"missing required vintage for {source}")
    df, publisher = loaded
    if "value" in df.columns:
        df = df.rename(columns={"value": name})
    path = latest_vintage(*source.split(":", 1))
    if path is None:
        raise RuntimeError(f"could not resolve path for {source}")
    return (
        df[["country_iso3", "year", name]].copy(),
        {
            "publisher": publisher,
            "series": source.split(":", 1)[1],
            "source": source,
            "vintage_file": rel(path),
            "sha256": sha256(path),
        },
    )


def load_derived_diversification() -> tuple[pd.DataFrame, dict[str, Any]]:
    path = latest_vintage("derived", "export_diversification_index")
    if path is None:
        raise RuntimeError("missing derived:export_diversification_index vintage")
    raw = pd.read_parquet(path)
    panel = normalise_panel(
        raw,
        "derived",
        series="export_diversification_index",
        variable_name="export_diversification_index",
    )
    if panel is None or panel.empty:
        raise RuntimeError("could not normalise derived export diversification panel")
    panel = panel.rename(columns={"value": "export_diversification_index"})
    return (
        panel[["country_iso3", "year", "export_diversification_index"]],
        {
            "publisher": "derived",
            "series": "export_diversification_index",
            "source": "derived:export_diversification_index",
            "vintage_file": rel(path),
            "sha256": sha256(path),
            "source_url": "derived://scripts/build_export_diversification_vintage.py",
            "methodology_url": "local://scripts/build_export_diversification_vintage.py",
        },
    )


def load_spec() -> dict[str, Any]:
    path = ROOT / "hypotheses" / "trade" / f"{HYPOTHESIS_ID}.yaml"
    return yaml.safe_load(path.read_text())


def build_panel(spec: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    vintages: dict[str, dict[str, Any]] = {}
    hightech, vintages["outcome_high_tech_export_share"] = load_series(
        "world_bank_wdi:TX.VAL.TECH.MF.ZS", "high_tech_export_share"
    )
    diversification, vintages["outcome_export_diversification_index"] = (
        load_derived_diversification()
    )
    trade, vintages["treatment_trade_openness"] = load_series(
        "world_bank_wdi:NE.TRD.GNFS.ZS", "trade_openness"
    )
    pmr, vintages["treatment_oecd_pmr_trade_barrier"] = load_series(
        "oecd_pmr:BARRIER_TRADE", "barrier_trade"
    )
    efw_trade, vintages["treatment_fraser_trade_freedom"] = load_series(
        "fraser_efw:freedom_to_trade_internationally", "efw_trade_freedom"
    )
    government, vintages["treatment_government_consumption_share"] = load_series(
        "world_bank_wdi:NE.CON.GOVT.ZS", "government_consumption_share"
    )
    state_size, vintages["treatment_fraser_size_of_government"] = load_series(
        "fraser_efw:size_of_government", "state_size_index"
    )
    gdp, vintages["controls_log_gdp_per_capita"] = load_series(
        "world_bank_wdi:NY.GDP.PCAP.KD", "log_gdp_per_capita"
    )
    human_capital, vintages["controls_human_capital_index"] = load_series(
        "pwt:hc", "human_capital_index"
    )
    fdi, vintages["controls_fdi_inflows_pct_gdp"] = load_series(
        "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS", "fdi_inflows_pct_gdp"
    )

    gdp["log_gdp_per_capita"] = np.log(
        pd.to_numeric(gdp["log_gdp_per_capita"], errors="coerce").where(lambda s: s > 0)
    )
    panel = hightech.merge(diversification, on=["country_iso3", "year"], how="outer")
    for frame in (
        trade,
        pmr,
        efw_trade,
        government,
        state_size,
        gdp,
        human_capital,
        fdi,
    ):
        panel = panel.merge(frame, on=["country_iso3", "year"], how="outer")

    panel["market_access_index"] = pd.concat(
        [
            zscore(panel["trade_openness"]),
            zscore(-panel["barrier_trade"]),
            zscore(panel["efw_trade_freedom"]),
        ],
        axis=1,
    ).mean(axis=1, skipna=True)
    panel["subsidy_state_burden_index"] = pd.concat(
        [
            zscore(panel["government_consumption_share"]),
            zscore(-panel["state_size_index"]),
        ],
        axis=1,
    ).mean(axis=1, skipna=True)

    countries = set(spec["sample"]["countries"])
    start, end = spec["sample"]["period"]
    panel = panel[
        panel["country_iso3"].isin(countries)
        & panel["year"].between(int(start), int(end))
    ].copy()
    return panel, vintages


def run_models(panel: pd.DataFrame, spec: dict[str, Any]) -> dict[str, Any]:
    base_controls = [
        {"name": "log_gdp_per_capita"},
        {"name": "human_capital_index"},
        {"name": "fdi_inflows_pct_gdp"},
    ]
    market_spec = {
        "sample": spec["sample"],
        "variables": {
            "controls": [{"name": "subsidy_state_burden_index"}, *base_controls]
        },
        "estimator": {"fixed_effects": ["country", "year"], "clustering": "country"},
    }
    subsidy_spec = {
        "sample": spec["sample"],
        "variables": {"controls": [{"name": "market_access_index"}, *base_controls]},
        "estimator": {"fixed_effects": ["country", "year"], "clustering": "country"},
    }
    return {
        "high_tech_market_access": run_panel_ols(
            panel, market_spec, "high_tech_export_share", "market_access_index"
        ),
        "high_tech_subsidy_burden": run_panel_ols(
            panel,
            subsidy_spec,
            "high_tech_export_share",
            "subsidy_state_burden_index",
        ),
        "diversification_market_access": run_panel_ols(
            panel,
            market_spec,
            "export_diversification_index",
            "market_access_index",
        ),
        "diversification_subsidy_burden": run_panel_ols(
            panel,
            subsidy_spec,
            "export_diversification_index",
            "subsidy_state_burden_index",
        ),
    }


def verdict(models: dict[str, Any]) -> tuple[str, str]:
    high_market = models["high_tech_market_access"]
    high_subsidy = models["high_tech_subsidy_burden"]
    div_market = models["diversification_market_access"]
    if "error" in high_market:
        return "INCONCLUSIVE_DATA_PENDING", high_market["error"]
    market_high_supported = (
        high_market["coefficient"] > 0 and high_market["p_value"] < 0.05
    )
    subsidy_weaker = (
        "error" not in high_subsidy
        and abs(high_market["coefficient"]) > abs(high_subsidy["coefficient"])
        and high_subsidy["p_value"] >= 0.10
    )
    diversification_confirmed = (
        "error" not in div_market
        and div_market["coefficient"] > 0
        and div_market["p_value"] < 0.10
    )
    if market_high_supported and subsidy_weaker and diversification_confirmed:
        return "SUPPORTED", "proxy screen: high-tech and diversification channels both favor market access"
    if market_high_supported and subsidy_weaker:
        return (
            "PARTIAL",
            "proxy screen: market access predicts higher WDI high-tech export share, "
            "but broad diversification does not confirm",
        )
    if high_market["coefficient"] < 0 and high_market["p_value"] < 0.05:
        return "REFUTED", "proxy screen: market-access proxy is negative for high-tech exports"
    return "PARTIAL", "proxy screen is directionally weak or statistically inconclusive"


def write_outputs(
    spec: dict[str, Any],
    panel: pd.DataFrame,
    vintages: dict[str, dict[str, Any]],
    models: dict[str, Any],
    verdict_label: str,
    reason: str,
) -> None:
    run_utc = utc_now()
    missing = [
        "constructed: Atlas of Economic Complexity (Harvard CID)",
        "direct subsidy industrial-policy intensity panel",
        "direct tariff-faced-abroad market-access panel",
    ]
    limitations = [
        "Proxy screen uses WDI high-tech export share and derived/WITS diversification, not Harvard ECI.",
        "Subsidy/state-burden proxy uses government consumption and Fraser size-of-government; it is not direct sectoral subsidy spending.",
        "Do not scoreboard-map this as a final ECI/subsidy causal result without the missing primary data.",
    ]
    diagnostics = {
        "verdict": f"{verdict_label} - {reason}",
        "verdict_label": verdict_label,
        "verdict_reason": reason,
        "hypothesis_id": HYPOTHESIS_ID,
        "template": "proxy_panel_fe_decomposition",
        "runner": "engine/runs/export_complexity_market_access_vs_subsidy/replication.py",
        "run_utc": run_utc,
        "proxy_scope": {
            "market_access_index": "mean z-score of WDI trade openness, inverse OECD PMR trade barriers, and Fraser trade freedom",
            "subsidy_state_burden_index": "mean z-score of WDI government consumption and inverse Fraser size-of-government score",
            "outcomes": [
                "WDI high-tech exports share",
                "derived export diversification index",
            ],
            "primary_unavailable_inputs": missing,
        },
        "models": models,
        "sample": {
            "rows_any": int(len(panel)),
            "countries_any": int(panel["country_iso3"].nunique()),
            "year_min": int(panel["year"].min()),
            "year_max": int(panel["year"].max()),
        },
        "data_status": {
            "variables_loaded": [
                {
                    "role": "outcome",
                    "name": "high_tech_export_share",
                    "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
                    "publisher": "world_bank_wdi",
                    "n_rows": int(panel["high_tech_export_share"].notna().sum()),
                },
                {
                    "role": "outcome",
                    "name": "export_diversification_index",
                    "source": "derived:export_diversification_index",
                    "publisher": "derived",
                    "n_rows": int(panel["export_diversification_index"].notna().sum()),
                },
                {
                    "role": "treatment",
                    "name": "market_access_index",
                    "source": "constructed from WDI/OECD PMR/Fraser",
                    "publisher": "derived",
                    "n_rows": int(panel["market_access_index"].notna().sum()),
                },
                {
                    "role": "treatment",
                    "name": "subsidy_state_burden_index",
                    "source": "constructed from WDI/Fraser",
                    "publisher": "derived",
                    "n_rows": int(panel["subsidy_state_burden_index"].notna().sum()),
                },
            ],
            "variables_missing": [{"source": item} for item in missing],
        },
        "limitations": limitations,
    }
    (RUN_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=str) + "\n"
    )

    chart_data = {
        "models": [
            {"name": name, **result}
            for name, result in models.items()
            if "error" not in result
        ],
        "panel_coverage": (
            panel.groupby("year")
            .agg(
                countries=("country_iso3", "nunique"),
                high_tech_obs=("high_tech_export_share", "count"),
                diversification_obs=("export_diversification_index", "count"),
            )
            .reset_index()
            .to_dict("records")
        ),
    }
    (RUN_DIR / "chart_data.json").write_text(
        json.dumps(chart_data, indent=2, default=str) + "\n"
    )

    manifest = {
        "hypothesis_id": HYPOTHESIS_ID,
        "run_utc": run_utc,
        "runner": "engine/runs/export_complexity_market_access_vs_subsidy/replication.py",
        "verdict_label": verdict_label,
        "status": verdict_label,
        "reason": reason,
        "vintages": vintages,
        "missing_series": missing,
        "caveats": limitations,
    }
    (RUN_DIR / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False)
    )

    def estimate_line(label: str, result: dict[str, Any]) -> str:
        if "error" in result:
            return f"- {label}: error: {result['error']}"
        return (
            f"- {label}: coef={result['coefficient']:+.4g}, "
            f"se={result['std_error']:.4g}, p={result['p_value']:.3g}, "
            f"n={result['n_obs']}, countries={result['n_countries']}"
        )

    lines = [
        f"# Result card - {HYPOTHESIS_ID}",
        "",
        f"**Verdict:** {verdict_label} - {reason}",
        "",
        "## What changed",
        "This is a proxy-screen repair using local WDI, WITS/derived, OECD PMR, "
        "Fraser, and PWT vintages. The preregistered ECI and direct subsidy "
        "series remain missing.",
        "",
        "## Estimates",
        estimate_line("WDI high-tech exports on market-access index", models["high_tech_market_access"]),
        estimate_line("WDI high-tech exports on subsidy/state-burden index", models["high_tech_subsidy_burden"]),
        estimate_line("Derived diversification on market-access index", models["diversification_market_access"]),
        estimate_line("Derived diversification on subsidy/state-burden index", models["diversification_subsidy_burden"]),
        "",
        "## Caveats",
    ]
    lines.extend(f"- {item}" for item in limitations)
    lines.append("")
    lines.append(f"_Generated by `{manifest['runner']}` at {run_utc}_")
    (RUN_DIR / "result_card.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    spec = load_spec()
    panel, vintages = build_panel(spec)
    models = run_models(panel, spec)
    verdict_label, reason = verdict(models)
    write_outputs(spec, panel, vintages, models, verdict_label, reason)
    print(f"{HYPOTHESIS_ID}: {verdict_label} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
