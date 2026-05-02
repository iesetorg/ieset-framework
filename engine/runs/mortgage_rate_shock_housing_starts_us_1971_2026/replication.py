#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "mortgage_rate_shock_housing_starts_us_1971_2026"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


def latest(series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing fred:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {"MORTGAGE30US": latest("MORTGAGE30US"), "HOUST": latest("HOUST")}
    mort = load_monthly(paths["MORTGAGE30US"], "mortgage_rate")
    starts = load_monthly(paths["HOUST"], "housing_starts")
    panel = pd.concat([mort, starts], axis=1).dropna().loc["1972-04-01":"2026-03-01"]
    panel["mortgage_change_12m_bp"] = 100.0 * (panel["mortgage_rate"] - panel["mortgage_rate"].shift(12))
    panel["starts_change_12m_pct"] = 100.0 * np.log(panel["housing_starts"].shift(-12) / panel["housing_starts"])
    candidate_months = list(panel.index[panel["mortgage_change_12m_bp"] >= 150.0])
    episodes = []
    last_start = pd.Timestamp("1900-01-01")
    for month in candidate_months:
        if month < last_start + pd.DateOffset(months=12):
            continue
        if pd.isna(panel.loc[month, "starts_change_12m_pct"]):
            continue
        last_start = month
        change = float(panel.loc[month, "starts_change_12m_pct"])
        episodes.append({
            "episode_month": month.date().isoformat(),
            "mortgage_change_12m_bp": float(panel.loc[month, "mortgage_change_12m_bp"]),
            "mortgage_rate": float(panel.loc[month, "mortgage_rate"]),
            "housing_starts": float(panel.loc[month, "housing_starts"]),
            "housing_starts_change_12m_pct": change,
            "passes_decline_15pct": bool(change <= -15.0),
        })

    df = pd.DataFrame(episodes)
    n = int(len(df))
    pass_rate = float(df["passes_decline_15pct"].mean()) if n else 0.0
    median_change = float(df["housing_starts_change_12m_pct"].median()) if n else float("nan")
    if pass_rate >= 0.60 and median_change <= -15.0:
        verdict = "supported"
    elif pass_rate < 0.40 or median_change > 0:
        verdict = "refuted"
    else:
        verdict = "partial"
    reason = f"{int(df['passes_decline_15pct'].sum()) if n else 0}/{n} episodes pass; median 12m starts change {median_change:.1f}%"

    df.to_parquet(OUT_DIR / "metric_results.parquet", index=False)
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "completed_episodes": n,
        "pass_rate": pass_rate,
        "median_housing_starts_change_12m_pct": median_change,
        "episodes": episodes,
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\nstatus: {verdict}\nreason: {reason}\nvintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    rows = "\n".join(
        f"| {r['episode_month']} | {r['mortgage_change_12m_bp']:.0f} | {r['housing_starts_change_12m_pct']:.1f}% | {'yes' if r['passes_decline_15pct'] else 'no'} |"
        for r in episodes
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Result card - {HID}\n\n**Verdict:** {verdict} - {reason}\n\n"
        "## Episode Table\n\n| Month | 12m mortgage-rate change bp | 12m housing-starts change | Pass |\n|---|---:|---:|:---:|\n"
        f"{rows}\n"
    )
    print(f"verdict: {verdict} - {reason}")


if __name__ == "__main__":
    main()
