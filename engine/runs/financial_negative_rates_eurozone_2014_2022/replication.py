#!/usr/bin/env python3
"""Exact local-proxy replication for Eurozone negative-rate passthrough."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HID = "financial_negative_rates_eurozone_2014_2022"


def latest(publisher: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / publisher).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {publisher}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vintage_meta(publisher: str, series: str, label: str) -> tuple[Path, dict]:
    path = latest(publisher, series)
    return path, {
        "publisher": publisher,
        "series": series,
        "label": label,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def run() -> int:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    dfr_path, dfr_meta = vintage_meta("ecb", "FM__B.U2.EUR.4F.KR.DFR.LEV", "ECB deposit facility rate")
    euribor_path, euribor_meta = vintage_meta(
        "ecb", "FM__M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA", "3-month Euribor"
    )
    m3_path, m3_meta = vintage_meta(
        "ecb", "BSI__M.U2.Y.V.M30.X.I.U2.2300.Z01.A", "Euro area M3 annual growth"
    )

    dfr = pd.read_parquet(dfr_path)
    dfr["date"] = pd.to_datetime(dfr["period"])
    dfr = (
        dfr[["date", "value"]]
        .sort_values("date")
        .set_index("date")
        .resample("MS")
        .ffill()
        .reset_index()
        .rename(columns={"value": "dfr"})
    )
    euribor = pd.read_parquet(euribor_path)
    euribor["date"] = pd.to_datetime(euribor["period"])
    euribor = euribor[["date", "value"]].rename(columns={"value": "euribor3m"})
    m3 = pd.read_parquet(m3_path)
    m3["date"] = pd.to_datetime(m3["period"])
    m3 = m3[["date", "value"]].rename(columns={"value": "m3_yoy"})

    panel = euribor.merge(dfr, on="date").merge(m3, on="date")
    window = panel[(panel["date"] >= "2014-06-01") & (panel["date"] <= "2022-07-01")].copy()
    pre = panel[(panel["date"] >= "2010-01-01") & (panel["date"] <= "2013-12-01")].copy()
    window["spread_bp"] = (window["euribor3m"] - window["dfr"]) * 100.0

    avg_spread_bp = float(window["spread_bp"].mean())
    negative_euribor_months = int((window["euribor3m"] < 0).sum())
    m3_pre_mean = float(pre["m3_yoy"].mean())
    m3_window_mean = float(window["m3_yoy"].mean())
    m3_gap_pp = m3_window_mean - m3_pre_mean
    m3_min = float(window["m3_yoy"].min())

    passthrough_gate = avg_spread_bp <= 10.0
    short_end_negative_gate = negative_euribor_months >= 24
    broad_money_no_run_gate = m3_min > -5.0
    exact_deposit_trend_gate = abs(m3_gap_pp) <= 2.0

    if passthrough_gate and short_end_negative_gate and exact_deposit_trend_gate:
        verdict = "SUPPORTED"
        reason = "local Euribor/M3 proxy clears passthrough, negative-rate, and trend-stability gates"
    elif passthrough_gate and short_end_negative_gate and broad_money_no_run_gate:
        verdict = "PARTIAL"
        reason = "money-market passthrough clears and no broad-money run appears, but M3 growth is not within 2pp of pre-2014 trend and exact household-deposit/core-yield gates are not loaded"
    else:
        verdict = "REFUTED"
        reason = "local proxy fails either passthrough or negative-rate persistence gates"

    estimate = {
        "method": "monthly ECB DFR, 3-month Euribor, and M3 annual-growth proxy checks",
        "window": ["2014-06", "2022-07"],
        "avg_euribor3m_minus_dfr_bp": avg_spread_bp,
        "median_euribor3m_minus_dfr_bp": float(window["spread_bp"].median()),
        "negative_euribor_months": negative_euribor_months,
        "window_months": int(len(window)),
        "m3_pre_2010_2013_mean_yoy_pct": m3_pre_mean,
        "m3_negative_rate_window_mean_yoy_pct": m3_window_mean,
        "m3_window_minus_pre_pp": m3_gap_pp,
        "m3_window_min_yoy_pct": m3_min,
        "passthrough_gate_spread_le_10bp": bool(passthrough_gate),
        "short_end_negative_gate_ge_24_months": bool(short_end_negative_gate),
        "broad_money_no_run_gate_min_gt_minus_5pct": bool(broad_money_no_run_gate),
        "exact_deposit_trend_gate_within_2pp": bool(exact_deposit_trend_gate),
        "proxy_note": "Eonia/ESTR, household deposits, and core 2y sovereign yields are not present locally; Euribor 3M and M3 annual growth are used as conservative local proxies.",
    }
    vintages = {"dfr": dfr_meta, "euribor3m": euribor_meta, "m3_yoy": m3_meta}
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "descriptive_exact_local_proxy",
        "estimate": estimate,
        "vintages": vintages,
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (OUT / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": HID,
                "run_utc": run_utc,
                "verdict_label": verdict,
                "runner": f"engine/runs/{HID}/replication.py",
                "vintages": vintages,
                "gates": {
                    "passthrough_spread_le_10bp": bool(passthrough_gate),
                    "negative_short_end_ge_24_months": bool(short_end_negative_gate),
                    "m3_growth_within_2pp_of_pre_2014": bool(exact_deposit_trend_gate),
                },
                "proxy_note": estimate["proxy_note"],
            },
            sort_keys=False,
        )
    )
    md = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Exact Local Test",
        f"- Average Euribor 3M minus DFR spread, Jun-2014 to Jul-2022: **{avg_spread_bp:.2f} bp**.",
        f"- Euribor 3M was below zero in **{negative_euribor_months}/{len(window)} months**.",
        f"- M3 annual growth averaged **{m3_window_mean:.2f}%** during the negative-rate window versus **{m3_pre_mean:.2f}%** in 2010-2013.",
        f"- Minimum M3 annual growth in the window: **{m3_min:.2f}%**.",
        "",
        "## Caveat",
        estimate["proxy_note"],
    ]
    (OUT / "result_card.md").write_text("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
