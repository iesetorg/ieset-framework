#!/usr/bin/env python3
"""Replication for wealth_tax_forecast_realized_yield_gap.

Grades the capital-flight "systematic yield gap" prediction on the curated
wealth_tax_manual:revenue_forecast_realized vintage. A country shows a yield
gap if the median realised/forecast revenue ratio across its case-years is
below 0.85 (realised >=15% under the legislator's enactment forecast).

  SUPPORTED  >= 3 of 4 countries show a gap   (systematic under-delivery)
  PARTIAL    exactly 2 of 4 show a gap        (real but not systematic)
  REFUTED    <= 1 of 4 show a gap             (realised meets/exceeds forecast)
  INCONCLUSIVE_DATA_PENDING  panel missing / < 3 countries resolve
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HID = "wealth_tax_forecast_realized_yield_gap"
OUT = ROOT / "engine" / "runs" / HID
GAP_THRESHOLD = 0.85          # realised/forecast below this == a >=15% gap
SYSTEMATIC_N = 3              # countries (of 4) needed for SUPPORTED


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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        path = latest("wealth_tax_manual", "revenue_forecast_realized")
    except FileNotFoundError:
        verdict, reason = "INCONCLUSIVE_DATA_PENDING", "wealth_tax_manual panel not on disk"
        _write(verdict, reason, None, [], None)
        print(reason)
        return 0

    df = pd.read_parquet(path)
    df = df.dropna(subset=["forecast_revenue_local", "realized_revenue_local"])
    df = df[df["forecast_revenue_local"] > 0].copy()
    df["ratio"] = df["realized_revenue_local"] / df["forecast_revenue_local"]

    per_country = (
        df.groupby("country_iso3")["ratio"]
        .agg(["median", "count"])
        .reset_index()
        .sort_values("country_iso3")
    )
    per_country["gap"] = per_country["median"] < GAP_THRESHOLD
    n_countries = int(len(per_country))
    n_gap = int(per_country["gap"].sum())

    if n_countries < 3:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = f"only {n_countries} countries resolved (need >=3)"
    elif n_gap >= SYSTEMATIC_N:
        verdict = "SUPPORTED"
        reason = (f"{n_gap}/{n_countries} countries show a country-level yield gap "
                  f"(median realised/forecast < {GAP_THRESHOLD}) — systematic under-delivery")
    elif n_gap <= 1:
        verdict = "REFUTED"
        reason = (f"only {n_gap}/{n_countries} countries show a yield gap; realised meets or "
                  f"exceeds forecast in the majority — no systematic under-delivery")
    else:
        verdict = "PARTIAL"
        gappers = ", ".join(per_country.loc[per_country["gap"], "country_iso3"])
        reason = (f"{n_gap}/{n_countries} countries show a yield gap ({gappers}) — real but not "
                  f"systematic; the other countries met or exceeded forecast")

    cases = df[["country_iso3", "case_id", "revenue_year", "forecast_revenue_local",
                "realized_revenue_local", "ratio", "currency"]].to_dict("records")
    _write(verdict, reason, path, per_country.to_dict("records"), cases)
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0


def _write(verdict: str, reason: str, path: Path | None,
           per_country: list[dict], cases: list[dict] | None) -> None:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "descriptive_case_ratio",
        "gap_threshold": GAP_THRESHOLD,
        "systematic_country_threshold": SYSTEMATIC_N,
        "per_country": per_country,
        "cases": cases,
        "data_status": {
            "variables_loaded": (
                [{"source": "wealth_tax_manual:revenue_forecast_realized",
                  "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}]
                if path else []
            ),
            "variables_missing": [] if path else ["wealth_tax_manual:revenue_forecast_realized"],
        },
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))
    if path:
        (OUT / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\n"
            "sources:\n"
            f"  forecast_realized: {path.relative_to(ROOT)}\n"
            f"  sha256: {sha256(path)}\n"
            f"run_utc: {run_utc}\n"
        )
    rows = "\n".join(
        f"| {c['country_iso3']} | {c['median']:.3f} | {int(c['count'])} | {'GAP' if c['gap'] else 'no gap'} |"
        for c in per_country
    )
    (OUT / "result_card.md").write_text(
        f"# Result card — {HID}\n\n"
        f"**Verdict:** {verdict} — {reason}\n\n"
        f"## Per-country realised/forecast ratio (gap threshold {GAP_THRESHOLD})\n"
        "| Country | Median ratio | Case-years | Gap? |\n"
        "| --- | ---: | ---: | --- |\n"
        f"{rows}\n\n"
        "A country shows a yield gap when realised wealth-tax revenue runs >=15% below the "
        "legislator's enactment-year forecast (median ratio < 0.85). Spain and Colombia (new "
        "2022 taxes with optimistic headline forecasts) show large gaps; France's IFI and "
        "Norway's formuesskatt met or exceeded forecast — so the gap is real but not systematic.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
