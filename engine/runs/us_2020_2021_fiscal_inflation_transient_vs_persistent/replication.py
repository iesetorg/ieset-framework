#!/usr/bin/env python3
"""Replication — US 2020-2021 fiscal inflation transient-by-2024 test."""
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
HID = "us_2020_2021_fiscal_inflation_transient_vs_persistent"
OUT_DIR = ROOT / "engine" / "runs" / HID

SERIES = {
    "headline_cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "headline_pce": "PCEPI",
    "core_pce": "PCEPILFE",
}


def latest(series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / "fred").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"fred:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yoy(series: str) -> pd.Series:
    df = pq.read_table(latest(series)).to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    x = df.dropna(subset=["value"]).set_index("date")["value"].sort_index()
    return x.pct_change(12, fill_method=None) * 100


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    manifest = {}
    for name, series in SERIES.items():
        yoy = load_yoy(series)
        baseline = float(yoy["2018-01-01":"2019-12-01"].mean())
        q1_2024 = float(yoy["2024-01-01":"2024-03-01"].mean())
        peak_2021_2023 = float(yoy["2021-01-01":"2023-12-01"].max())
        gap = q1_2024 - baseline
        rows.append(
            {
                "metric": name,
                "series": series,
                "baseline_2018_2019_yoy": baseline,
                "q1_2024_yoy": q1_2024,
                "gap_vs_baseline_pp": gap,
                "within_1pp": gap <= 1.0,
                "peak_2021_2023_yoy": peak_2021_2023,
                "reversal_from_peak_pp": peak_2021_2023 - q1_2024,
            }
        )
        path = latest(series)
        manifest[name] = {
            "publisher": "fred",
            "series": series,
            "vintage_file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }

    within_count = sum(1 for r in rows if r["within_1pp"])
    core_rows = {r["metric"]: r for r in rows if r["metric"] in {"core_cpi", "core_pce"}}
    both_core_gt_1p5 = all(r["gap_vs_baseline_pp"] > 1.5 for r in core_rows.values())
    no_core_gt_1p5 = all(r["gap_vs_baseline_pp"] <= 1.5 for r in core_rows.values())

    if within_count >= 3 and no_core_gt_1p5:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED — at least three of four inflation measures returned within +1pp "
            "of their 2018-2019 baselines by 2024-Q1 and no core measure exceeded +1.5pp."
        )
    elif within_count < 2 or both_core_gt_1p5:
        verdict_label = "refuted"
        verdict = (
            "refuted — fewer than two of four inflation measures returned within +1pp "
            f"of baseline by 2024-Q1 ({within_count}/4)."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            "weakened — inflation receded materially from 2021-2023 peaks, but the "
            "registered 2024-Q1 return-to-baseline threshold was not cleanly met."
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "within_1pp_count": within_count,
        "both_core_gt_1p5": both_core_gt_1p5,
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
                    f"{r['metric']}: baseline {r['baseline_2018_2019_yoy']:.2f}%, "
                    f"2024-Q1 {r['q1_2024_yoy']:.2f}%, "
                    f"gap {r['gap_vs_baseline_pp']:+.2f}pp, within_1pp={r['within_1pp']}."
                    for r in rows
                ],
                "",
                "## Method Note",
                "",
                "This test checks return-to-baseline timing only; it does not identify the fiscal impulse's causal share.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
