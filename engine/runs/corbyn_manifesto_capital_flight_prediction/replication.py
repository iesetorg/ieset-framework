#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HID = "corbyn_manifesto_capital_flight_prediction"
OUT = ROOT / "engine" / "runs" / HID
EVENTS = [pd.Timestamp("2017-05-16"), pd.Timestamp("2019-11-21")]


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


def load(pub: str, series: str) -> tuple[pd.DataFrame, Path]:
    path = latest(pub, series)
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["date", "value"]).sort_values("date"), path


def three_day_event(df: pd.DataFrame, event: pd.Timestamp, mode: str) -> dict:
    prev = df[df["date"] < event].tail(1).iloc[0]
    window = df[df["date"] >= event].head(3)
    end = window.iloc[-1]
    pre = df[(df["date"] < event) & (df["date"] >= event - pd.Timedelta(days=120))].copy()
    diffs = pre["value"].diff().dropna()
    if mode == "pct":
        change = 100.0 * (end["value"] / prev["value"] - 1.0)
        sigma = 100.0 * pre["value"].pct_change().dropna().std()
        adverse = -change / sigma if sigma and sigma > 0 else 0.0
    else:
        change = 100.0 * (end["value"] - prev["value"])
        sigma = 100.0 * diffs.std()
        adverse = change / sigma if sigma and sigma > 0 else 0.0
    return {
        "event_date": event.date().isoformat(),
        "previous_date": prev["date"].date().isoformat(),
        "window_end_date": end["date"].date().isoformat(),
        "change": float(change),
        "pre_event_sigma": float(sigma),
        "adverse_sigma": float(adverse),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    gbp, gbp_path = load("boe", "XUDLUSS")
    gilt, gilt_path = load("boe", "IUDMNZC")
    vix, vix_path = load("fred", "VIXCLS")
    event_rows = []
    for ev in EVENTS:
        event_rows.append({
            "event_date": ev.date().isoformat(),
            "gbp_usd_3d_pct_change": three_day_event(gbp, ev, "pct"),
            "gilt_10y_3d_bp_change": three_day_event(gilt, ev, "bp"),
            "vix_3d_point_change": three_day_event(vix, ev, "bp"),
        })
    max_primary_adverse = max(
        max(row["gbp_usd_3d_pct_change"]["adverse_sigma"], row["gilt_10y_3d_bp_change"]["adverse_sigma"])
        for row in event_rows
    )
    worst_gbp = min(row["gbp_usd_3d_pct_change"]["change"] for row in event_rows)
    worst_gilt = max(row["gilt_10y_3d_bp_change"]["change"] for row in event_rows)
    if max_primary_adverse < 2.0 and worst_gbp > -2.0 and worst_gilt < 20.0:
        verdict, reason = "SUPPORTED", "no manifesto window shows a >2-sigma adverse GBP or gilt move"
    elif max_primary_adverse >= 2.0 or worst_gbp <= -2.0 or worst_gilt >= 20.0:
        verdict, reason = "REFUTED", "at least one primary market window clears an adverse capital-flight gate"
    else:
        verdict, reason = "PARTIAL", "market moves are muted but one threshold is too close to call"
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "event_study_daily_exact",
        "events": event_rows,
        "summary": {
            "max_primary_adverse_sigma": float(max_primary_adverse),
            "worst_gbp_usd_3d_pct_change": float(worst_gbp),
            "worst_gilt_10y_3d_bp_change": float(worst_gilt),
        },
        "data_status": {
            "variables_loaded": [
                {"source": "boe:XUDLUSS", "vintage_file": str(gbp_path.relative_to(ROOT)), "sha256": sha256(gbp_path)},
                {"source": "boe:IUDMNZC", "vintage_file": str(gilt_path.relative_to(ROOT)), "sha256": sha256(gilt_path)},
                {"source": "fred:VIXCLS", "vintage_file": str(vix_path.relative_to(ROOT)), "sha256": sha256(vix_path)},
            ],
            "variables_missing": ["imf:BFOAFA", "owid:ftse-all-share"],
        },
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (OUT / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        "sources:\n"
        f"  gbp_usd: {gbp_path.relative_to(ROOT)}\n"
        f"  gilt_10y: {gilt_path.relative_to(ROOT)}\n"
        f"  vix: {vix_path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    rows = []
    for row in event_rows:
        rows.append(
            f"| {row['event_date']} | {row['gbp_usd_3d_pct_change']['change']:.3f}% | "
            f"{row['gbp_usd_3d_pct_change']['adverse_sigma']:.2f} | "
            f"{row['gilt_10y_3d_bp_change']['change']:.2f} | "
            f"{row['gilt_10y_3d_bp_change']['adverse_sigma']:.2f} |"
        )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## Tight-Window Market Reactions\n"
        "| Event | GBP/USD 3d change | GBP adverse sigma | Gilt 10y 3d bp | Gilt adverse sigma |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
        + "\n".join(rows)
        + "\n\n"
        "Primary adverse gates are GBP depreciation or gilt-yield increases over the 3-trading-day window. "
        "The VIX series is loaded as a global-risk control, not a gating UK outcome.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
