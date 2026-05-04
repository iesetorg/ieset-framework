#!/usr/bin/env python3
"""Replication — Sweden Meidner wage-earner funds capital-flight proxy."""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
HID = "meidner_wage_earner_fund_capital_flight"
OUT_DIR = ROOT / "engine" / "runs" / HID

COUNTRY = "SWE"
PRE = range(1980, 1984)
EVENT = range(1984, 1992)

SERIES = {
    "investment_pct_gdp": "NE.GDI.FTOT.ZS",
    "fdi_inflows_pct_gdp": "BX.KLT.DINV.WD.GD.ZS",
    "sek_usd_exchange_rate": "PA.NUS.FCRF",
}


def latest(series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / "world_bank_wdi").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"world_bank_wdi:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_wdi(series: str) -> pd.DataFrame:
    path = latest(series)
    df = pq.read_table(path).to_pandas()
    out = df[df["country_iso3"] == COUNTRY][["year", "value"]].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["year", "value"])


def means(df: pd.DataFrame) -> tuple[float, float]:
    pre = float(df[df["year"].isin(PRE)]["value"].mean())
    event = float(df[df["year"].isin(EVENT)]["value"].mean())
    return pre, event


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    manifest = {}
    for metric, series in SERIES.items():
        path = latest(series)
        df = load_wdi(series)
        pre_mean, event_mean = means(df)
        if metric == "sek_usd_exchange_rate":
            change = (event_mean / pre_mean) - 1
            breach = change > 0.25
            direction = "higher means SEK depreciation"
            threshold = 0.25
        elif metric == "investment_pct_gdp":
            change = event_mean - pre_mean
            breach = change < -2.0
            direction = "percentage-point change"
            threshold = -2.0
        else:
            change = event_mean - pre_mean
            breach = change < -1.0
            direction = "percentage-point change"
            threshold = -1.0
        rows.append(
            {
                "metric": metric,
                "series": series,
                "pre_1980_1983_mean": pre_mean,
                "event_1984_1991_mean": event_mean,
                "change": change,
                "direction": direction,
                "breach_threshold": threshold,
                "breach": breach,
            }
        )
        manifest[metric] = {
            "publisher": "world_bank_wdi",
            "series": series,
            "vintage_file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }

    breach_count = sum(1 for r in rows if r["breach"])
    if breach_count == 0:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED — none of the three registered macro capital-flight proxies breached "
            "the Sweden 1984-1991 Meidner-fund thresholds."
        )
    elif breach_count >= 2:
        verdict_label = "refuted"
        verdict = (
            "refuted — at least two registered macro capital-flight proxies breached the "
            f"thresholds ({breach_count}/3)."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            "weakened — one registered macro capital-flight proxy breached its threshold, "
            "but the majority did not."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "country": COUNTRY,
        "pre_period": [min(PRE), max(PRE)],
        "event_period": [min(EVENT), max(EVENT)],
        "breach_count": breach_count,
        "metrics": rows,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n"
        + "\n".join(f"  {k}: {v['vintage_file']}" for k, v in manifest.items())
        + "\n"
    )
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Registered Metrics",
                "",
                *[
                    "- "
                    f"{r['metric']}: pre {r['pre_1980_1983_mean']:.3f}, "
                    f"event {r['event_1984_1991_mean']:.3f}, change {r['change']:+.3f}, "
                    f"breach={r['breach']}."
                    for r in rows
                ],
                "",
                "## Method Note",
                "",
                "The 1992 Swedish currency crisis is outside the primary event window; this is a macro-proxy test, not household-level offshore wealth measurement.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
