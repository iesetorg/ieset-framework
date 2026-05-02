#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "baa_aaa_spread_real_activity_us_1919_2026"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


def latest(series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing fred:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    paths = {s: latest(s) for s in ["BAA", "AAA", "UNRATE", "INDPRO"]}
    baa = load_monthly(paths["BAA"], "baa")
    aaa = load_monthly(paths["AAA"], "aaa")
    unrate = load_monthly(paths["UNRATE"], "unrate")
    indpro = load_monthly(paths["INDPRO"], "indpro")
    panel = pd.concat([baa, aaa, unrate, indpro], axis=1)
    panel["spread"] = panel["baa"] - panel["aaa"]
    panel["spread_gap_vs_24m_median"] = panel["spread"] - panel["spread"].rolling(24, min_periods=18).median()
    panel["unrate_change_12m_max_pp"] = panel["unrate"].rolling(13, min_periods=2).max().shift(-12) - panel["unrate"]
    # Forward minimum IP over months t..t+12 as log change from episode month.
    future_ip_min = pd.concat([panel["indpro"].shift(-i) for i in range(13)], axis=1).min(axis=1)
    panel["indpro_min_change_12m_pct"] = 100.0 * np.log(future_ip_min / panel["indpro"])

    candidates = list(panel.index[panel["spread_gap_vs_24m_median"] >= 1.0])
    episodes = []
    last_start = pd.Timestamp("1800-01-01")
    for month in candidates:
        if month < last_start + pd.DateOffset(months=12):
            continue
        if pd.isna(panel.loc[month, "indpro_min_change_12m_pct"]):
            continue
        last_start = month
        un_chg = panel.loc[month, "unrate_change_12m_max_pp"]
        ip_chg = float(panel.loc[month, "indpro_min_change_12m_pct"])
        pass_un = bool(pd.notna(un_chg) and float(un_chg) >= 0.50)
        pass_ip = bool(ip_chg <= -3.0)
        episodes.append({
            "episode_month": month.date().isoformat(),
            "baa_aaa_spread": float(panel.loc[month, "spread"]),
            "spread_gap_vs_24m_median": float(panel.loc[month, "spread_gap_vs_24m_median"]),
            "unrate_change_12m_max_pp": None if pd.isna(un_chg) else float(un_chg),
            "indpro_min_change_12m_pct": ip_chg,
            "passes_real_activity_deterioration": pass_un or pass_ip,
        })

    df = pd.DataFrame(episodes)
    n = int(len(df))
    pass_count = int(df["passes_real_activity_deterioration"].sum()) if n else 0
    pass_rate = pass_count / n if n else 0.0
    un_changes = pd.to_numeric(df["unrate_change_12m_max_pp"], errors="coerce") if n else pd.Series(dtype=float)
    median_un = float(un_changes.dropna().median()) if len(un_changes.dropna()) else float("nan")
    median_ip = float(df["indpro_min_change_12m_pct"].median()) if n else float("nan")
    if pass_rate >= 0.65 and median_un > 0:
        verdict = "supported"
    elif pass_rate < 0.45 or ((not np.isnan(median_un) and median_un <= 0) and median_ip >= 0):
        verdict = "refuted"
    else:
        verdict = "partial"
    reason = f"{pass_count}/{n} episodes pass; median max unemployment change {median_un:.2f}pp; median min IP change {median_ip:.1f}%"

    df.to_parquet(OUT_DIR / "metric_results.parquet", index=False)
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "completed_episodes": n,
        "pass_rate": pass_rate,
        "median_unrate_change_12m_max_pp": median_un,
        "median_indpro_min_change_12m_pct": median_ip,
        "episodes": episodes,
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
        "A pass means unemployment rises at least +0.50pp or industrial production falls at least 3% within 12 months of a Baa-Aaa spread spike.\n"
    )
    print(f"verdict: {verdict} - {reason}")


if __name__ == "__main__":
    main()
