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
HID = "biden_ira_chips_fiscal_inflation_pass_through"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

START = pd.Timestamp("2022-08-01")
END = pd.Timestamp("2025-12-01")
Q4_2025 = slice(pd.Timestamp("2025-10-01"), pd.Timestamp("2025-12-01"))


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


def log_yoy(series: pd.Series) -> pd.Series:
    return (100.0 * np.log(series / series.shift(12))).replace([np.inf, -np.inf], np.nan)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "TLMFGCONS": latest("TLMFGCONS"),
        "PCEPI": latest("PCEPI"),
        "PCEPILFE": latest("PCEPILFE"),
        "CES0500000003": latest("CES0500000003"),
    }

    mfg = load_monthly(paths["TLMFGCONS"], "mfg_construction")
    pce = load_monthly(paths["PCEPI"], "pce_price_index")
    core_pce = load_monthly(paths["PCEPILFE"], "core_pce_price_index")
    wages = load_monthly(paths["CES0500000003"], "average_hourly_earnings")

    panel = pd.concat([mfg, pce, core_pce, wages], axis=1).sort_index()
    required_dates = [START, END, pd.Timestamp("2025-10-01"), pd.Timestamp("2025-11-01"), pd.Timestamp("2025-12-01")]
    method_valid = all(d in panel.dropna(subset=["mfg_construction", "pce_price_index"]).index for d in [START, END])
    method_valid = method_valid and all(d in panel.dropna(subset=["core_pce_price_index", "average_hourly_earnings"]).index for d in required_dates[2:])

    panel["real_mfg_construction"] = np.nan
    if START in panel.index and pd.notna(panel.loc[START, "pce_price_index"]):
        base_pce = float(panel.loc[START, "pce_price_index"])
        panel["real_mfg_construction"] = panel["mfg_construction"] / (panel["pce_price_index"] / base_pce)

    panel["core_pce_yoy_pct"] = log_yoy(panel["core_pce_price_index"])
    panel["ahe_wage_yoy_pct"] = log_yoy(panel["average_hourly_earnings"])

    if method_valid:
        real_growth = float(panel.loc[END, "real_mfg_construction"] / panel.loc[START, "real_mfg_construction"] - 1.0)
        nominal_growth = float(panel.loc[END, "mfg_construction"] / panel.loc[START, "mfg_construction"] - 1.0)
        core_q4 = float(panel.loc[Q4_2025, "core_pce_yoy_pct"].mean())
        wage_q4 = float(panel.loc[Q4_2025, "ahe_wage_yoy_pct"].mean())
        supported = real_growth >= 0.25 and core_q4 < 4.0 and wage_q4 < 4.5
        refuted = real_growth < 0.10 or (core_q4 >= 4.0 and wage_q4 >= 4.5)
        if supported:
            verdict_label = "SUPPORTED"
        elif refuted:
            verdict_label = "REFUTED"
        else:
            verdict_label = "PARTIAL"
        verdict_reason = (
            f"real manufacturing construction {real_growth * 100:.1f}% from 2022-08 to 2025-12; "
            f"2025-Q4 core PCE {core_q4:.2f}% YoY; 2025-Q4 AHE wage growth {wage_q4:.2f}% YoY"
        )
    else:
        real_growth = None
        nominal_growth = None
        core_q4 = None
        wage_q4 = None
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
        missing = [d.strftime("%Y-%m") for d in required_dates if d not in panel.index]
        verdict_reason = f"missing required monthly endpoints: {missing}"

    sample = panel.loc["2018-01-01":"2025-12-01"].copy()
    sample.index.name = "month"
    sample = sample.reset_index()
    sample["month"] = sample["month"].dt.strftime("%Y-%m")
    sample.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": f"{verdict_label} \u2014 {verdict_reason}",
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "method_valid": method_valid,
        "test": "fred_mfg_construction_core_pce_wage_2022_2025",
        "evidence_type": "descriptive_post_enactment_outcome_test",
        "causal_attribution": "not identified; the test cannot isolate IRA/CHIPS from other industrial policy or supply-chain forces",
        "thresholds": {
            "support_real_mfg_construction_growth_min": 0.25,
            "support_core_pce_q4_2025_yoy_max": 4.0,
            "support_ahe_wage_q4_2025_yoy_max": 4.5,
            "refute_real_mfg_construction_growth_max": 0.10,
        },
        "estimate": {
            "real_mfg_construction_growth_2022_08_to_2025_12": real_growth,
            "nominal_mfg_construction_growth_2022_08_to_2025_12": nominal_growth,
            "core_pce_yoy_q4_2025_avg": core_q4,
            "ahe_wage_yoy_q4_2025_avg": wage_q4,
        },
        "data_status": {
            "variables_loaded": [
                {"name": "manufacturing_construction_spending", "source": "fred:TLMFGCONS", "publisher": "fred"},
                {"name": "pce_price_index", "source": "fred:PCEPI", "publisher": "fred"},
                {"name": "core_pce_price_index", "source": "fred:PCEPILFE", "publisher": "fred"},
                {"name": "average_hourly_earnings", "source": "fred:CES0500000003", "publisher": "fred"},
            ],
            "variables_missing": [],
        },
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/biden_ira_chips_fiscal_inflation_pass_through/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict_label}\n"
        f"reason: {verdict_reason}\n"
        "methodology_note: descriptive post-enactment test; no causal IRA/CHIPS attribution identified\n"
        "vintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict_label} - {verdict_reason}\n\n"
        "## Predeclared Test\n\n"
        "Support requires real manufacturing construction spending to be at least 25% above its August 2022 "
        "level by December 2025, with 2025-Q4 core PCE inflation below 4.0% YoY and 2025-Q4 private average "
        "hourly earnings growth below 4.5% YoY. Refutation triggers if real construction growth is below 10% "
        "or both inflation and wage growth breach the wage-price-spiral thresholds.\n\n"
        "## Scope Note\n\n"
        "This is a descriptive post-enactment outcome test. It does not identify a causal IRA/CHIPS outlay shock "
        "or separate these laws from other industrial-policy, monetary-policy, and supply-chain forces.\n"
    )
    print(f"verdict: {verdict_label} - {verdict_reason}")


if __name__ == "__main__":
    main()
