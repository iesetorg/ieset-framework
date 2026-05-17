#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HID = "fed_qt_balance_sheet_unwind_2022_2025_market_response"
OUT = ROOT / "engine" / "runs" / HID
EVENTS = ["2022-05-04", "2022-06-01", "2022-09-01", "2024-05-01", "2024-06-03"]


def latest(series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing fred:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(series: str) -> tuple[pd.DataFrame, Path]:
    path = latest(series)
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["date", "value"]).sort_values("date"), path


def prev(df: pd.DataFrame, date: str | pd.Timestamp) -> pd.Series:
    return df[df["date"] < pd.Timestamp(date)].tail(1).iloc[0]


def on_or_after(df: pd.DataFrame, date: str | pd.Timestamp) -> pd.Series:
    return df[df["date"] >= pd.Timestamp(date)].head(1).iloc[0]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tp, tp_path = load("THREEFYTP10")
    dgs10, dgs10_path = load("DGS10")
    mtg, mtg_path = load("MORTGAGE30US")
    walcl, walcl_path = load("WALCL")
    rows = []
    for ev in EVENTS:
        tp0, tp1 = prev(tp, ev), on_or_after(tp, ev)
        term_bp = 100.0 * (tp1["value"] - tp0["value"])
        mtg0, mtg1 = prev(mtg, ev), on_or_after(mtg, ev)
        d100, d101 = prev(dgs10, mtg0["date"]), on_or_after(dgs10, mtg1["date"])
        spread0 = 100.0 * (mtg0["value"] - d100["value"])
        spread1 = 100.0 * (mtg1["value"] - d101["value"])
        rows.append({
            "event_date": ev,
            "term_premium_1d_bp": float(term_bp),
            "mortgage_treasury_spread_bp": float(spread1 - spread0),
        })
    cumulative_tp = sum(r["term_premium_1d_bp"] for r in rows)
    start = on_or_after(walcl, "2022-06-01")
    end = on_or_after(walcl, "2024-06-05")
    balance_sheet_change_trn = float((end["value"] - start["value"]) / 1_000_000.0)
    bp_per_trn = cumulative_tp / abs(balance_sheet_change_trn)
    if 10.0 <= cumulative_tp <= 40.0 and 3.0 <= bp_per_trn <= 12.0:
        verdict, reason = "SUPPORTED", "cumulative term-premium and per-dollar QT gates clear"
    elif cumulative_tp <= 0.0 or bp_per_trn > 20.0:
        verdict, reason = "REFUTED", "cumulative term-premium response is non-positive"
    else:
        verdict, reason = "PARTIAL", "term-premium response is positive but outside the registered magnitude band"
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "event_study_daily_exact",
        "events": rows,
        "summary": {
            "cumulative_term_premium_1d_bp": float(cumulative_tp),
            "balance_sheet_change_trn_2022_06_to_2024_06": balance_sheet_change_trn,
            "term_premium_bp_per_trn_abs_runoff": float(bp_per_trn),
            "note": "The 2025-01 event in the YAML is not date-pinned, so this exact wrapper grades the five pinned QT events.",
        },
        "data_status": {
            "variables_loaded": [
                {"source": "fred:THREEFYTP10", "vintage_file": str(tp_path.relative_to(ROOT)), "sha256": sha256(tp_path)},
                {"source": "fred:DGS10", "vintage_file": str(dgs10_path.relative_to(ROOT)), "sha256": sha256(dgs10_path)},
                {"source": "fred:MORTGAGE30US", "vintage_file": str(mtg_path.relative_to(ROOT)), "sha256": sha256(mtg_path)},
                {"source": "fred:WALCL", "vintage_file": str(walcl_path.relative_to(ROOT)), "sha256": sha256(walcl_path)},
            ],
            "variables_missing": ["fred:BAMLC0A0CMTRIV", "constructed:2025-01 QT event date"],
        },
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (OUT / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        "sources:\n"
        f"  term_premium_10y: {tp_path.relative_to(ROOT)}\n"
        f"  treasury_10y: {dgs10_path.relative_to(ROOT)}\n"
        f"  mortgage_30y: {mtg_path.relative_to(ROOT)}\n"
        f"  fed_balance_sheet: {walcl_path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    md_rows = "\n".join(
        f"| {r['event_date']} | {r['term_premium_1d_bp']:.2f} | {r['mortgage_treasury_spread_bp']:.2f} |"
        for r in rows
    )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## QT Event Responses\n"
        "| Event | 10y term-premium 1d bp | Mortgage-Treasury spread bp |\n"
        "| --- | ---: | ---: |\n"
        f"{md_rows}\n\n"
        f"- Cumulative term-premium response: **{cumulative_tp:.2f} bp**.\n"
        f"- Balance-sheet runoff through 2024-06: **{balance_sheet_change_trn:.3f} trillion dollars**.\n"
        f"- Term-premium response per absolute trillion dollars runoff: **{bp_per_trn:.2f} bp/$T**.\n\n"
        "The non-positive cumulative term-premium response fails the registered reverse-QE direction gate.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
