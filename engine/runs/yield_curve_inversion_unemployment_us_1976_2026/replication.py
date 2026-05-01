#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "yield_curve_inversion_unemployment_us_1976_2026"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


def latest(pub: str, series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_fred(path: Path) -> pd.DataFrame:
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).copy()
    if "realtime_end" in df.columns:
        df = df.sort_values(["date", "realtime_end"]).drop_duplicates("date", keep="last")
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df[["date", "month", "value"]].sort_values("date")


def detect_episodes(spread: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    inverted = spread < 0
    episodes: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    months = list(inverted.index)
    i = 0
    while i < len(months):
        if not bool(inverted.iloc[i]):
            i += 1
            continue
        start = months[i]
        j = i
        while j + 1 < len(months) and bool(inverted.iloc[j + 1]):
            j += 1
        end = months[j]
        if j - i + 1 >= 2:
            episodes.append((start, end))
        i = j + 1
    return episodes


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "DGS10": latest("fred", "DGS10"),
        "DGS2": latest("fred", "DGS2"),
        "UNRATE": latest("fred", "UNRATE"),
    }
    d10 = load_fred(paths["DGS10"]).groupby("month")["value"].mean().rename("dgs10")
    d2 = load_fred(paths["DGS2"]).groupby("month")["value"].mean().rename("dgs2")
    un = load_fred(paths["UNRATE"]).groupby("month")["value"].mean().rename("unrate")

    panel = pd.concat([d10, d2], axis=1, join="inner").dropna()
    panel = panel[panel.index >= pd.Timestamp("1976-06-01")]
    panel["spread"] = panel["dgs10"] - panel["dgs2"]
    max_complete_start = un.index.max() - pd.DateOffset(months=24)

    rows = []
    for start, end in detect_episodes(panel["spread"]):
        if start > max_complete_start:
            continue
        baseline = float(un.loc[start])
        follow = un[(un.index >= start) & (un.index <= start + pd.DateOffset(months=24))]
        max_unrate = float(follow.max())
        rows.append(
            {
                "episode_start": start.date().isoformat(),
                "episode_end": end.date().isoformat(),
                "baseline_unrate": baseline,
                "max_unrate_24m": max_unrate,
                "unrate_increase_pp": max_unrate - baseline,
                "passes_075pp": max_unrate - baseline >= 0.75,
            }
        )

    episodes = pd.DataFrame(rows)
    n = len(episodes)
    pass_rate = float(episodes["passes_075pp"].mean()) if n else 0.0
    median_increase = float(episodes["unrate_increase_pp"].median()) if n else 0.0
    if pass_rate >= 0.70 and median_increase >= 1.0:
        verdict = "supported"
        reason = f"{episodes['passes_075pp'].sum()} of {n} completed episodes pass; median increase {median_increase:.2f}pp"
    elif pass_rate < 0.50 or median_increase < 0.5:
        verdict = "refuted"
        reason = f"only {episodes['passes_075pp'].sum()} of {n} completed episodes pass; median increase {median_increase:.2f}pp"
    else:
        verdict = "partial"
        reason = f"{episodes['passes_075pp'].sum()} of {n} completed episodes pass; median increase {median_increase:.2f}pp"

    episodes.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    chart = {
        "chart_id": f"{HID}/episodes",
        "title": "US yield-curve inversion episodes and unemployment follow-through",
        "type": "table",
        "series": rows,
        "sources": [f"fred:{k}" for k in paths],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "completed_episodes": n,
        "pass_rate": pass_rate,
        "median_unrate_increase_pp": median_increase,
        "episodes": rows,
        "vintages": {k: str(v.relative_to(REPO_ROOT)) for k, v in paths.items()},
        "sha256": {k: sha256(v) for k, v in paths.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict}\n"
        f"reason: {reason}\n"
        "vintages:\n"
        + "".join(f"  {k}: {v.relative_to(REPO_ROOT)}\n" for k, v in paths.items())
    )
    rows_md = "\n".join(
        f"| {r['episode_start']} | {r['episode_end']} | {r['baseline_unrate']:.1f} | "
        f"{r['max_unrate_24m']:.1f} | {r['unrate_increase_pp']:.1f} | "
        f"{'yes' if r['passes_075pp'] else 'no'} |"
        for r in rows
    )
    card = f"""# Result card - {HID}

**Verdict:** {verdict} - {reason}

## Episode Test

Support threshold: at least 70% of completed inversion episodes pass the +0.75pp unemployment follow-through test and median increase >= 1.0pp.

| Start | End | Baseline unemployment | Max unemployment within 24m | Increase pp | Pass |
|---|---:|---:|---:|---:|:---:|
{rows_md}

## Interpretation

The test is associational: yield-curve inversion is treated as a timing signal, not a causal mechanism. Episodes that start fewer than 24 months before the latest unemployment observation are excluded as censored.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict} - {reason}")


if __name__ == "__main__":
    main()
