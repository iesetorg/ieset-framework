#!/usr/bin/env python3
"""Proxy replication for consumer-choice/product-variety trade reform.

The preregistered final-goods SKU and Wacziarg-Welch episode inputs are not
local. This run-local repair uses the official/local spines now available:
PWT real consumption, WITS product-count/HHI export concentration, and WDI
trade openness/controls. The verdict is therefore a proxy screen, not a
scoreboard-ready causal episode estimate.
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
HYPOTHESIS_ID = "consumer_choice_variety_trade_market_reform"

sys.path.insert(0, str(ROOT / "scripts"))
from run_panel_fe import latest_vintage, load_variable, run_panel_ols  # noqa: E402


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


def load_wits_product_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    path = latest_vintage("wits", "export_product_hhi_wits")
    if path is None:
        raise RuntimeError("missing wits:export_product_hhi_wits vintage")
    raw = pd.read_parquet(path)
    panel = raw[["country_iso3", "year", "value", "number_of_products"]].copy()
    panel["country_iso3"] = panel["country_iso3"].astype(str).str.upper()
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")
    products = pd.to_numeric(panel["number_of_products"], errors="coerce")
    panel["import_product_variety_proxy"] = np.log(products.where(products > 0))
    panel["export_concentration_hhi"] = pd.to_numeric(panel["value"], errors="coerce")
    return (
        panel[
            [
                "country_iso3",
                "year",
                "import_product_variety_proxy",
                "export_concentration_hhi",
            ]
        ],
        {
            "publisher": "wits",
            "series": "export_product_hhi_wits",
            "source": "wits:export_product_hhi_wits",
            "vintage_file": rel(path),
            "sha256": sha256(path),
            "source_url": "manual://data/manual/wits/herfindahl_hirschman_product_concentration_index_export_2026-02-09.xlsx",
            "methodology_url": "https://wits.worldbank.org/",
        },
    )


def load_spec() -> dict[str, Any]:
    path = ROOT / "hypotheses" / "distribution" / f"{HYPOTHESIS_ID}.yaml"
    return yaml.safe_load(path.read_text())


def build_panel(spec: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    vintages: dict[str, dict[str, Any]] = {}
    consumption, vintages["outcome_real_consumption"] = load_series(
        "pwt:rconna", "real_quality_adjusted_consumption"
    )
    wits, vintages["outcome_wits_product_variety"] = load_wits_product_panel()
    trade, vintages["treatment_trade_openness"] = load_series(
        "world_bank_wdi:NE.TRD.GNFS.ZS", "trade_openness"
    )
    gdp, vintages["controls_log_gdp_per_capita"] = load_series(
        "world_bank_wdi:NY.GDP.PCAP.KD", "log_gdp_per_capita"
    )
    services, vintages["controls_services_share_gdp"] = load_series(
        "world_bank_wdi:NV.SRV.TOTL.ZS", "services_share_gdp"
    )

    gdp["log_gdp_per_capita"] = np.log(
        pd.to_numeric(gdp["log_gdp_per_capita"], errors="coerce").where(lambda s: s > 0)
    )
    panel = consumption.merge(wits, on=["country_iso3", "year"], how="outer")
    for frame in (trade, gdp, services):
        panel = panel.merge(frame, on=["country_iso3", "year"], how="outer")
    panel["log_real_consumption"] = np.log(
        pd.to_numeric(panel["real_quality_adjusted_consumption"], errors="coerce").where(
            lambda s: s > 0
        )
    )
    panel["trade_openness_z"] = zscore(panel["trade_openness"])

    countries = set(spec["sample"]["countries"])
    start, end = spec["sample"]["period"]
    panel = panel[
        panel["country_iso3"].isin(countries)
        & panel["year"].between(int(start), int(end))
    ].copy()
    return panel, vintages


def run_models(panel: pd.DataFrame, spec: dict[str, Any]) -> dict[str, Any]:
    model_spec = {
        "sample": spec["sample"],
        "variables": {
            "controls": [
                {"name": "log_gdp_per_capita"},
                {"name": "services_share_gdp"},
            ]
        },
        "estimator": {"fixed_effects": ["country", "year"], "clustering": "country"},
    }
    return {
        "consumption": run_panel_ols(
            panel, model_spec, "log_real_consumption", "trade_openness_z"
        ),
        "variety": run_panel_ols(
            panel,
            model_spec,
            "import_product_variety_proxy",
            "trade_openness_z",
        ),
        "concentration": run_panel_ols(
            panel, model_spec, "export_concentration_hhi", "trade_openness_z"
        ),
    }


def verdict(models: dict[str, Any]) -> tuple[str, str]:
    cons = models["consumption"]
    variety = models["variety"]
    if "error" in cons:
        return "INCONCLUSIVE_DATA_PENDING", cons["error"]
    cons_refutes = cons["coefficient"] < 0 and cons["p_value"] < 0.10
    variety_supports = (
        "error" not in variety
        and variety["coefficient"] > 0
        and variety["p_value"] < 0.10
    )
    if cons_refutes and not variety_supports:
        return (
            "REFUTED",
            "proxy screen: PWT consumption coefficient is negative and significant; "
            "WITS product-variety proxy is not positive/significant",
        )
    if variety_supports and cons["coefficient"] > 0 and cons["p_value"] < 0.10:
        return "SUPPORTED", "proxy screen: consumption and WITS variety both improve"
    return (
        "PARTIAL",
        "proxy screen mixed or statistically weak across consumption and WITS variety",
    )


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
        "constructed:wacziarg_welch_trade_liberalisation_dates",
        "constructed:state_ownership_share_and_sectoral_targeting",
        "final-goods SKU availability indices",
    ]
    diagnostics = {
        "verdict": f"{verdict_label} - {reason}",
        "verdict_label": verdict_label,
        "verdict_reason": reason,
        "hypothesis_id": HYPOTHESIS_ID,
        "template": "proxy_panel_fe",
        "runner": "engine/runs/consumer_choice_variety_trade_market_reform/replication.py",
        "run_utc": run_utc,
        "proxy_scope": {
            "primary_unavailable_inputs": missing,
            "treatment_proxy": "z-scored WDI trade openness",
            "welfare_proxy": "log PWT rconna",
            "variety_proxy": "log WITS number_of_products in export HHI workbook",
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
                    "name": "log_real_consumption",
                    "source": "pwt:rconna",
                    "publisher": "pwt",
                    "n_rows": int(panel["log_real_consumption"].notna().sum()),
                },
                {
                    "role": "outcome",
                    "name": "import_product_variety_proxy",
                    "source": "wits:export_product_hhi_wits",
                    "publisher": "wits",
                    "n_rows": int(panel["import_product_variety_proxy"].notna().sum()),
                },
                {
                    "role": "treatment",
                    "name": "trade_openness_z",
                    "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
                    "publisher": "world_bank_wdi",
                    "n_rows": int(panel["trade_openness_z"].notna().sum()),
                },
            ],
            "variables_missing": [{"source": item} for item in missing],
        },
        "limitations": [
            "Proxy screen uses continuous trade openness, not preregistered reform episodes.",
            "WITS product counts are broad export-product counts, not domestic final-goods SKU availability.",
            "Do not scoreboard-map this as a causal episode verdict without the missing episode/SKU data.",
        ],
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
                consumption_obs=("log_real_consumption", "count"),
                variety_obs=("import_product_variety_proxy", "count"),
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
        "runner": "engine/runs/consumer_choice_variety_trade_market_reform/replication.py",
        "verdict_label": verdict_label,
        "status": verdict_label,
        "reason": reason,
        "vintages": vintages,
        "missing_series": missing,
        "caveats": diagnostics["limitations"],
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
        "This is a proxy-screen repair using local PWT, WITS, and WDI vintages. "
        "The preregistered episode/SKU data remain missing, so the result is not "
        "a final causal episode test.",
        "",
        "## Estimates",
        estimate_line("PWT log real consumption on WDI trade openness", models["consumption"]),
        estimate_line("WITS log product-count proxy on WDI trade openness", models["variety"]),
        estimate_line("WITS export concentration HHI on WDI trade openness", models["concentration"]),
        "",
        "## Data",
        "- PWT `rconna` for real consumption.",
        "- WITS export-product HHI workbook for `number_of_products` and HHI.",
        "- WDI trade openness, GDP per capita, and services share controls.",
        "",
        "## Caveats",
    ]
    lines.extend(f"- {item}" for item in diagnostics["limitations"])
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
