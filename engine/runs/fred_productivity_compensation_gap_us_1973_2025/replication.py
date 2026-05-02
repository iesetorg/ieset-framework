#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "fred_productivity_compensation_gap_us_1973_2025"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


def latest(series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing fred:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_annual(path: Path, name: str) -> pd.Series:
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    if "realtime_end" in df.columns:
        df = df.drop_duplicates("date", keep="last")
    df["year"] = df["date"].dt.year
    return df.groupby("year")["value"].mean().rename(name)


def log_gap(prod: pd.Series, comp: pd.Series, start: int, end: int) -> float:
    return 100.0 * (np.log(prod.loc[end] / prod.loc[start]) - np.log(comp.loc[end] / comp.loc[start]))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {"OPHNFB": latest("OPHNFB"), "COMPRNFB": latest("COMPRNFB")}
    prod = load_annual(paths["OPHNFB"], "output_per_hour")
    comp = load_annual(paths["COMPRNFB"], "real_hourly_comp")
    panel = pd.concat([prod, comp], axis=1).dropna()
    method_valid = all(y in panel.index for y in [1973, 2019])
    if method_valid:
        gap_1973_2019 = float(log_gap(panel["output_per_hour"], panel["real_hourly_comp"], 1973, 2019))
        latest_year = int(min(2025, panel.index.max()))
        gap_1973_latest = float(log_gap(panel["output_per_hour"], panel["real_hourly_comp"], 1973, latest_year))
        if gap_1973_2019 >= 20.0:
            verdict = "supported"
        elif gap_1973_2019 <= 0:
            verdict = "refuted"
        else:
            verdict = "partial"
        reason = f"1973-2019 productivity-compensation log gap {gap_1973_2019:.1f} ppts; 1973-{latest_year} informative gap {gap_1973_latest:.1f} ppts"
    else:
        verdict = "inconclusive"
        latest_year = int(panel.index.max()) if len(panel) else None
        gap_1973_2019 = float("nan")
        gap_1973_latest = float("nan")
        reason = "missing 1973 or 2019 endpoint"

    rows = panel.reset_index().rename(columns={"index": "year"})
    rows.to_parquet(OUT_DIR / "metric_results.parquet", index=False)
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "method_valid": method_valid,
        "gap_1973_2019_log_ppts": gap_1973_2019,
        "gap_1973_latest_log_ppts": gap_1973_latest,
        "latest_year": latest_year,
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\nstatus: {verdict}\nreason: {reason}\nvintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n**Verdict:** {verdict} - {reason}\n\n"
        "Support requires the 1973-2019 cumulative productivity-minus-compensation log gap to be at least +20 log percentage points.\n"
    )
    print(f"verdict: {verdict} - {reason}")


if __name__ == "__main__":
    main()
