#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "jolts_openings_wage_pressure_us_2007_2026"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


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


def pct_log_yoy(series: pd.Series) -> pd.Series:
    return (100.0 * np.log(series / series.shift(12))).replace([np.inf, -np.inf], np.nan)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {"JTSJOL": latest("JTSJOL"), "CES0500000003": latest("CES0500000003")}
    openings = load_monthly(paths["JTSJOL"], "openings")
    wages = load_monthly(paths["CES0500000003"], "ahe")
    panel = pd.concat([pct_log_yoy(openings).rename("openings_yoy"), pct_log_yoy(wages).rename("wage_yoy")], axis=1).dropna()
    panel["wage_yoy_6m_ahead"] = panel["wage_yoy"].shift(-6)
    panel["wage_accel_6m"] = panel["wage_yoy_6m_ahead"] - panel["wage_yoy"]
    primary = panel.dropna().loc["2007-03-01":"2026-03-01"].copy()
    primary = primary[~((primary.index >= "2020-03-01") & (primary.index <= "2021-12-01"))]
    corr = float(primary["openings_yoy"].corr(primary["wage_yoy_6m_ahead"]))
    q75 = float(primary["openings_yoy"].quantile(0.75))
    top = primary[primary["openings_yoy"] >= q75]
    median_accel = float(top["wage_accel_6m"].median())
    n = int(len(primary))

    if corr >= 0.45 and median_accel >= 0.25:
        verdict = "supported"
    elif corr <= 0.15 or median_accel <= 0:
        verdict = "refuted"
    else:
        verdict = "partial"
    reason = f"lead r={corr:.3f}; top-quartile median 6m wage acceleration={median_accel:.2f}pp; n={n}"

    rows = primary.reset_index().rename(columns={"index": "month"})
    rows["month"] = rows["month"].dt.strftime("%Y-%m")
    rows.to_parquet(OUT_DIR / "metric_results.parquet", index=False)
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "method_valid": n >= 120,
        "lead_correlation_openings_yoy_wage_yoy_6m": corr,
        "top_quartile_openings_yoy_threshold": q75,
        "top_quartile_median_wage_acceleration_6m_pp": median_accel,
        "primary_observations": n,
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\nstatus: {verdict}\nreason: {reason}\nvintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## Predeclared Test\n\n"
        "Support requires openings YoY to correlate at least 0.45 with private AHE YoY six months later, "
        "and top-quartile openings-growth months to show at least +0.25pp median wage-growth acceleration six months later.\n\n"
        f"Primary sample excludes 2020-03 through 2021-12. Vintages: {', '.join(str(v.relative_to(REPO_ROOT)) for v in paths.values())}.\n"
    )
    print(f"verdict: {verdict} - {reason}")


if __name__ == "__main__":
    main()
