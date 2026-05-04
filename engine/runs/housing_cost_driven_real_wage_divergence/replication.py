#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "housing_cost_driven_real_wage_divergence"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

START = pd.Timestamp("2006-03-01")
END = pd.Timestamp("2020-02-01")


def latest(series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing fred:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_monthly(path: Path, name: str) -> pd.Series:
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    if "realtime_end" in df.columns:
        df = df.drop_duplicates("date", keep="last")
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df.groupby("month")["value"].mean().rename(name)


def annualized_growth(start_value: float, end_value: float, years: float) -> float:
    return (end_value / start_value) ** (1.0 / years) - 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "CES0500000003": latest("CES0500000003"),
        "CPIAUCSL": latest("CPIAUCSL"),
        "CUSR0000SAH1": latest("CUSR0000SAH1"),
    }
    wages = load_monthly(paths["CES0500000003"], "avg_hourly_earnings")
    cpi = load_monthly(paths["CPIAUCSL"], "all_items_cpi")
    shelter = load_monthly(paths["CUSR0000SAH1"], "shelter_cpi")
    panel = pd.concat([wages, cpi, shelter], axis=1).dropna().sort_index()
    method_valid = START in panel.index and END in panel.index

    if method_valid:
        sample = panel.loc[START:END].copy()
        sample["real_wage_all_items"] = sample["avg_hourly_earnings"] / (sample["all_items_cpi"] / sample.loc[START, "all_items_cpi"])
        sample["real_wage_shelter_deflated"] = sample["avg_hourly_earnings"] / (sample["shelter_cpi"] / sample.loc[START, "shelter_cpi"])
        sample["all_items_real_wage_yoy"] = sample["real_wage_all_items"].pct_change(12)
        sample["shelter_deflated_wage_yoy"] = sample["real_wage_shelter_deflated"].pct_change(12)
        years = (END - START).days / 365.25
        all_growth = float(sample.loc[END, "real_wage_all_items"] / sample.loc[START, "real_wage_all_items"] - 1.0)
        shelter_growth = float(sample.loc[END, "real_wage_shelter_deflated"] / sample.loc[START, "real_wage_shelter_deflated"] - 1.0)
        gap_pp = float((all_growth - shelter_growth) * 100.0)
        corr = float(sample["all_items_real_wage_yoy"].corr(sample["shelter_deflated_wage_yoy"]))
        all_ann = float(annualized_growth(sample.loc[START, "real_wage_all_items"], sample.loc[END, "real_wage_all_items"], years))
        shelter_ann = float(annualized_growth(sample.loc[START, "real_wage_shelter_deflated"], sample.loc[END, "real_wage_shelter_deflated"], years))
        if gap_pp >= 5.0 and corr < 0.90:
            verdict_label = "PARTIAL"
            result_scope = "narrow measurement channel supported; full metro supply-elasticity claim not identified"
        elif gap_pp < 2.0 or corr >= 0.90:
            verdict_label = "REFUTED"
            result_scope = "narrow measurement channel failed"
        else:
            verdict_label = "PARTIAL"
            result_scope = "narrow measurement channel mixed"
        verdict_reason = (
            f"US FRED proxy: all-items real AHE growth {all_growth * 100:.1f}% vs shelter-deflated "
            f"{shelter_growth * 100:.1f}% from 2006-03 to 2020-02; gap {gap_pp:.1f}pp; YoY correlation {corr:.2f}"
        )
    else:
        sample = panel.copy()
        all_growth = shelter_growth = gap_pp = corr = all_ann = shelter_ann = None
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
        result_scope = "missing required FRED endpoints"
        verdict_reason = "missing 2006-03 or 2020-02 endpoint in local FRED overlap"

    rows = sample.reset_index().rename(columns={"index": "month"})
    rows["month"] = rows["month"].dt.strftime("%Y-%m")
    rows.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": f"{verdict_label} \u2014 {verdict_reason}",
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "method_valid": method_valid,
        "test": "fred_us_ahe_all_cpi_vs_shelter_cpi_2006_2020",
        "evidence_type": "descriptive_measurement_channel_proxy",
        "scope_note": result_scope,
        "causal_attribution": "not identified; no metro supply-elasticity panel is estimated",
        "estimate": {
            "all_items_real_ahe_growth": all_growth,
            "shelter_deflated_ahe_growth": shelter_growth,
            "growth_gap_percentage_points": gap_pp,
            "all_items_real_ahe_annualized_growth": all_ann,
            "shelter_deflated_ahe_annualized_growth": shelter_ann,
            "yoy_growth_correlation": corr,
        },
        "thresholds": {
            "support_growth_gap_pp_min": 5.0,
            "support_yoy_correlation_max": 0.90,
            "refute_growth_gap_pp_max": 2.0,
        },
        "data_status": {
            "variables_loaded": [
                {"name": "average_hourly_earnings", "source": "fred:CES0500000003", "publisher": "fred"},
                {"name": "all_items_cpi", "source": "fred:CPIAUCSL", "publisher": "fred"},
                {"name": "shelter_cpi", "source": "fred:CUSR0000SAH1", "publisher": "fred"},
            ],
            "variables_missing": [
                {"name": "metro_supply_elasticity_panel", "source": "manual:Saiz_HilberVermeulen_KendallTulip"}
            ],
        },
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/housing_cost_driven_real_wage_divergence/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict_label}\n"
        f"reason: {verdict_reason}\n"
        "methodology_note: FRED national proxy only; no metro supply-elasticity identification\n"
        "vintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict_label} - {verdict_reason}\n\n"
        "## Predeclared Test\n\n"
        "The v2 local diagnostic compares total-private average hourly earnings deflated by all-items CPI "
        "against the same earnings deflated by CPI shelter over the clean local FRED overlap from 2006-03 "
        "through 2020-02. It supports only the narrower measurement-channel claim if the growth gap is at "
        "least 5 percentage points and YoY growth correlation is below 0.90.\n\n"
        "## Scope Note\n\n"
        "This does not estimate the original cross-metro supply-elasticity design. Full support remains data-gated "
        "on a metro wage, housing-cost, productivity, and elasticity panel.\n"
    )
    print(f"verdict: {verdict_label} - {verdict_reason}")


if __name__ == "__main__":
    main()
