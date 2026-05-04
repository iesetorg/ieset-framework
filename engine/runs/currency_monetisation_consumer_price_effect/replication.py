#!/usr/bin/env python3
"""Replication for QE-era base/CPI pass-through decoupling."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.api as sm

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "currency_monetisation_consumer_price_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRIES = {
    "USA": {
        "period": ("2008-01-01", "2019-12-31"),
        "base_series": "BOGMBASE",
        "cpi_series": "CPIAUCSL",
        "base_label": "monetary_base",
    },
    "JPN": {
        "period": ("1998-04-01", "2020-12-31"),
        "base_series": "JPNASSETS",
        "cpi_series": "JPNCPIALLMINMEI",
        "base_label": "central_bank_assets",
    },
}
SUPPORT_PASS_THROUGH = 0.20
REFUTE_PASS_THROUGH = 0.50


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(series: str) -> Path:
    files = sorted(
        (REPO_ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    if not files:
        raise FileNotFoundError(f"fred:{series}")
    return files[-1]


def fred_series(series: str, name: str) -> tuple[pd.DataFrame, Path]:
    path = latest(series)
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df[name] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", name]].dropna(), path


def run_country(country: str, cfg: dict) -> tuple[dict, dict[str, dict]]:
    base, base_path = fred_series(cfg["base_series"], "base")
    cpi, cpi_path = fred_series(cfg["cpi_series"], "cpi")
    start, end = cfg["period"]
    panel = base.merge(cpi, on="date", how="inner").dropna()
    panel = panel[(panel["date"] >= start) & (panel["date"] <= end)].copy()
    panel = panel.sort_values("date")
    panel["base_yoy"] = 100.0 * np.log(panel["base"]).diff(12)
    panel["cpi_yoy"] = 100.0 * np.log(panel["cpi"]).diff(12)
    reg = panel.dropna(subset=["base_yoy", "cpi_yoy"]).copy()

    x = sm.add_constant(reg["base_yoy"])
    model = sm.OLS(reg["cpi_yoy"], x).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    coefficient = float(model.params["base_yoy"])
    p_value = float(model.pvalues["base_yoy"])
    base_growth = float(np.log(panel["base"].iloc[-1]) - np.log(panel["base"].iloc[0]))
    cpi_growth = float(np.log(panel["cpi"].iloc[-1]) - np.log(panel["cpi"].iloc[0]))
    cumulative_pass_through = cpi_growth / base_growth if base_growth else None
    clears_support = (
        coefficient < SUPPORT_PASS_THROUGH
        and cumulative_pass_through is not None
        and cumulative_pass_through < SUPPORT_PASS_THROUGH
    )
    triggers_refute = (
        coefficient >= REFUTE_PASS_THROUGH
        or (
            cumulative_pass_through is not None
            and cumulative_pass_through >= REFUTE_PASS_THROUGH
        )
    )
    return {
        "country": country,
        "period": [start, end],
        "n_months_regression": int(len(reg)),
        "base_label": cfg["base_label"],
        "coefficient_cpi_yoy_on_base_yoy": coefficient,
        "p_value": p_value,
        "cumulative_base_log_growth": base_growth,
        "cumulative_cpi_log_growth": cpi_growth,
        "cumulative_pass_through": cumulative_pass_through,
        "clears_support_thresholds": clears_support,
        "triggers_refute_thresholds": triggers_refute,
    }, {
        f"{country.lower()}_base": {
            "publisher": "fred",
            "series": cfg["base_series"],
            "vintage_file": str(base_path.relative_to(REPO_ROOT)),
            "sha256": sha256(base_path),
        },
        f"{country.lower()}_cpi": {
            "publisher": "fred",
            "series": cfg["cpi_series"],
            "vintage_file": str(cpi_path.relative_to(REPO_ROOT)),
            "sha256": sha256(cpi_path),
        },
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    manifest: dict[str, dict] = {}
    for country, cfg in COUNTRIES.items():
        result, vintages = run_country(country, cfg)
        results.append(result)
        manifest.update(vintages)

    if any(r["triggers_refute_thresholds"] for r in results):
        verdict_label = "refuted"
        verdict = "refuted - at least one country breaches the registered base/CPI pass-through refutation threshold."
    elif all(r["clears_support_thresholds"] for r in results):
        verdict_label = "SUPPORTED"
        verdict = "SUPPORTED - USA and Japan both show base/CPI pass-through below 0.20 by regression coefficient and cumulative ratio."
    else:
        verdict_label = "partial"
        verdict = "partial - at least one country clears the support thresholds, but not all country checks clear."

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "hypothesis_id": HID,
        "country_results": results,
        "thresholds": {
            "support_pass_through": SUPPORT_PASS_THROUGH,
            "refute_pass_through": REFUTE_PASS_THROUGH,
        },
        "manifest": manifest,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
        "runner": "engine/runs/currency_monetisation_consumer_price_effect/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    rows = []
    for r in results:
        rows.append({"spec": r["country"], "term": "coefficient_cpi_yoy_on_base_yoy", "estimate": r["coefficient_cpi_yoy_on_base_yoy"]})
        rows.append({"spec": r["country"], "term": "cumulative_pass_through", "estimate": r["cumulative_pass_through"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        "hypothesis_id: " + HID + "\n"
        "run_utc: '" + pd.Timestamp.utcnow().isoformat() + "'\n"
        "vintages:\n"
        + "".join(
            f"  {key}:\n    publisher: {meta['publisher']}\n    series: {meta['series']}\n"
            f"    vintage_file: {meta['vintage_file']}\n    sha256: {meta['sha256']}\n"
            for key, meta in manifest.items()
        )
    )

    lines = [
        "# Currency monetisation and CPI pass-through",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Results",
        "",
        "| Country | Period | N | CPI/base coefficient | p-value | Cumulative pass-through |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['country']} | {r['period'][0]} to {r['period'][1]} | "
            f"{r['n_months_regression']} | {r['coefficient_cpi_yoy_on_base_yoy']:.3f} | "
            f"{r['p_value']:.3f} | {r['cumulative_pass_through']:.3f} |"
        )
    lines += [
        "",
        "## Method",
        "",
        "For each country, regress 12-month CPI inflation on 12-month monetary-base "
        "or central-bank-asset growth with HAC(12) standard errors. The registered "
        "support threshold is pass-through below 0.20 on both the regression "
        "coefficient and the cumulative CPI/base log-growth ratio.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    return 0 if verdict_label == "SUPPORTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
