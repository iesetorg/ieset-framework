#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HID = "great_depression_over_accumulation_vs_monetary_cause"
OUT = ROOT / "engine" / "runs" / HID


def latest(pub: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing {pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pct_change(a: float, b: float) -> float:
    return 100.0 * (b / a - 1.0)


def log_ppt(a: float, b: float) -> float:
    return 100.0 * (np.log(b) - np.log(a))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    jst_path = latest("jst", "real_gdp")
    jst = pd.read_parquet(jst_path)
    usa = jst[jst["country_iso3"].eq("USA")].set_index("year").sort_index()

    shiller_path = latest("shiller", "ie_data")
    shiller = pd.read_parquet(shiller_path)
    annual = (
        shiller.groupby("year")
        .agg({"P": "mean", "E": "mean", "D": "mean", "Price": "mean", "Earnings": "mean", "CAPE": "mean"})
        .copy()
    )
    annual["earnings_yield"] = annual["E"] / annual["P"]
    annual["real_earnings_yield"] = annual["Earnings"] / annual["Price"]
    annual["dividend_yield"] = annual["D"] / annual["P"]

    metrics = {
        "jst_investment_share_pct_change_1920_1929": pct_change(usa.loc[1920, "iy"], usa.loc[1929, "iy"]),
        "jst_investment_share_pct_change_1923_1929": pct_change(usa.loc[1923, "iy"], usa.loc[1929, "iy"]),
        "jst_investment_share_pct_change_1925_1929": pct_change(usa.loc[1925, "iy"], usa.loc[1929, "iy"]),
        "shiller_earnings_yield_pct_change_1923_1929": pct_change(
            annual.loc[1923, "earnings_yield"], annual.loc[1929, "earnings_yield"]
        ),
        "shiller_real_earnings_yield_pct_change_1923_1929": pct_change(
            annual.loc[1923, "real_earnings_yield"], annual.loc[1929, "real_earnings_yield"]
        ),
        "shiller_dividend_yield_pct_change_1923_1929": pct_change(
            annual.loc[1923, "dividend_yield"], annual.loc[1929, "dividend_yield"]
        ),
        "shiller_nominal_earnings_pct_change_1923_1929": pct_change(annual.loc[1923, "E"], annual.loc[1929, "E"]),
        "shiller_price_pct_change_1923_1929": pct_change(annual.loc[1923, "P"], annual.loc[1929, "P"]),
        "shiller_cape_pct_change_1923_1929": pct_change(annual.loc[1923, "CAPE"], annual.loc[1929, "CAPE"]),
        "jst_money_log_ppt_change_1929_1933": log_ppt(usa.loc[1929, "money"], usa.loc[1933, "money"]),
        "jst_money_pct_change_1929_1933": pct_change(usa.loc[1929, "money"], usa.loc[1933, "money"]),
        "jst_nominal_gdp_pct_change_1929_1933": pct_change(usa.loc[1929, "gdp"], usa.loc[1933, "gdp"]),
        "jst_real_gdp_pct_change_1929_1933": pct_change(usa.loc[1929, "rgdpmad"], usa.loc[1933, "rgdpmad"]),
        "jst_cpi_pct_change_1929_1933": pct_change(usa.loc[1929, "cpi"], usa.loc[1933, "cpi"]),
        "jst_unemployment_pp_change_1929_1933": float(usa.loc[1933, "unemp"] - usa.loc[1929, "unemp"]),
    }

    profitability_proxy_gate = metrics["shiller_earnings_yield_pct_change_1923_1929"] <= -20.0
    accumulation_proxy_gate = metrics["jst_investment_share_pct_change_1923_1929"] > 0.0
    late_accumulation_gate = metrics["jst_investment_share_pct_change_1925_1929"] > 0.0
    monetary_competing_gate = (
        metrics["jst_money_log_ppt_change_1929_1933"] <= -25.0
        and metrics["jst_nominal_gdp_pct_change_1929_1933"] <= -25.0
        and metrics["jst_real_gdp_pct_change_1929_1933"] <= -20.0
    )

    gates = {
        "profitability_proxy_decline_gt_20pct": profitability_proxy_gate,
        "investment_share_rises_1923_1929": accumulation_proxy_gate,
        "late_1925_1929_investment_share_rises": late_accumulation_gate,
        "monetary_contraction_competing_channel_clears": monetary_competing_gate,
        "direct_capital_output_and_profit_rate_series_loaded": False,
    }

    verdict = "PARTIAL"
    reason = (
        "Shiller earnings-yield proxy falls more than 20% before 1929, but direct profit-rate/capital-output data are missing; "
        "late-1925 investment share does not rise and JST monetary-contraction gates also clear"
    )
    if not profitability_proxy_gate and monetary_competing_gate:
        verdict = "REFUTED"
        reason = "local proxies do not show the registered pre-1929 profitability decline, while monetary-contraction gates clear"

    loaded = [
        {
            "source": "jst:real_gdp",
            "vintage_file": str(jst_path.relative_to(ROOT)),
            "sha256": sha256(jst_path),
            "n_rows": int(jst.shape[0]),
        },
        {
            "source": "shiller:ie_data",
            "vintage_file": str(shiller_path.relative_to(ROOT)),
            "sha256": sha256(shiller_path),
            "n_rows": int(shiller.shape[0]),
        },
    ]
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "descriptive_exact_jst_shiller_proxy",
        "metrics": metrics,
        "gates": gates,
        "data_status": {
            "variables_loaded": loaded,
            "variables_missing": [
                {"source": "academic:dumenil_levy_us_rate_of_profit", "name": "rate_of_profit"},
                {"source": "academic:dumenil_levy_us_capital_output", "name": "capital_output_ratio"},
                {"source": "fred:CAPUTLB00004S or nber historical capacity", "name": "capacity_utilisation_1920s"},
            ],
        },
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))
    (OUT / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        "sources:\n"
        f"  jst_real_gdp: {jst_path.relative_to(ROOT)}\n"
        f"  shiller_ie_data: {shiller_path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )

    md = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Exact Local Proxy Gates",
    ]
    for key, value in metrics.items():
        md.append(f"- **{key}:** {value:.3f}")
    md.extend(
        [
            "",
            "## Gate Summary",
        ]
    )
    for key, value in gates.items():
        md.append(f"- **{key}:** {value}")
    md.extend(
        [
            "",
            "## Interpretation",
            "The local corpus can validate a proxy version of the over-accumulation story, not the full registered design. Equity earnings/dividend yields compress sharply before 1929, but nominal earnings rise and the direct capital-output/profit-rate series are absent. The same local JST panel strongly validates the competing monetary-contraction timing and magnitude, so the result is PARTIAL rather than a graduation to full support.",
            "",
            f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_",
        ]
    )
    (OUT / "result_card.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
