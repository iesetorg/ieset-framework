#!/usr/bin/env python3
"""Replication for Japan debt/GDP solvency-inflation threshold test."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "japan_public_debt_solvency_inflation_independence"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

THRESHOLDS = [150.0, 200.0, 250.0]
YIELD_SPIKE_BP = 300.0
INFLATION_YOY_THRESHOLD = 5.0
INFLATION_SUSTAINED_MONTHS = 12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    files = sorted(
        (REPO_ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"),
        key=lambda p: p.stat().st_mtime,
    )
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def fred_monthly(series: str, value_name: str) -> tuple[pd.DataFrame, Path]:
    path = latest("fred", series)
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df[value_name] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", value_name]].dropna(), path


def annual_country(pub: str, series: str, country: str, value_name: str) -> tuple[pd.DataFrame, Path]:
    path = latest(pub, series)
    df = pq.read_table(path).to_pandas()
    df = df[df["country_iso3"] == country].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df[value_name] = pd.to_numeric(df["value"], errors="coerce")
    return df[["year", value_name]].dropna(), path


def max_consecutive_true(values: list[bool]) -> int:
    best = cur = 0
    for value in values:
        cur = cur + 1 if value else 0
        best = max(best, cur)
    return best


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    debt, debt_path = annual_country("imf", "GGXWDG_NGDP", "JPN", "debt_gdp")
    yields, yield_path = fred_monthly("IRLTLT01JPM156N", "jgb_10y")
    cpi, cpi_path = fred_monthly("JPNCPIALLMINMEI", "cpi")
    fx, fx_path = fred_monthly("DEXJPUS", "jpy_usd")
    gdp, gdp_path = annual_country("world_bank_wdi", "NY.GDP.MKTP.KD.ZG", "JPN", "real_gdp_growth")
    ca, ca_path = annual_country("imf", "BCA_NGDPD", "JPN", "current_account_pct_gdp")

    cpi = cpi.sort_values("date")
    cpi["cpi_yoy"] = cpi["cpi"].pct_change(12) * 100.0

    threshold_results = []
    breaches = []
    missing_windows = []
    for threshold in THRESHOLDS:
        crossed = debt[debt["debt_gdp"] >= threshold].sort_values("year")
        if crossed.empty:
            missing_windows.append({"threshold": threshold, "reason": "debt threshold not crossed"})
            continue
        year = int(crossed.iloc[0]["year"])
        start = pd.Timestamp(year=year, month=1, day=1)
        pre_start = start - pd.DateOffset(months=12)
        post_end = start + pd.DateOffset(months=24) - pd.DateOffset(days=1)

        pre_yield = yields[(yields["date"] >= pre_start) & (yields["date"] < start)]
        post_yield = yields[(yields["date"] >= start) & (yields["date"] <= post_end)]
        post_cpi = cpi[(cpi["date"] >= start) & (cpi["date"] <= post_end)]

        pre_yield_mean = float(pre_yield["jgb_10y"].mean()) if not pre_yield.empty else None
        post_yield_max = float(post_yield["jgb_10y"].max()) if not post_yield.empty else None
        yield_spike_bp = (
            (post_yield_max - pre_yield_mean) * 100.0
            if pre_yield_mean is not None and post_yield_max is not None
            else None
        )
        yield_breach = yield_spike_bp is not None and yield_spike_bp > YIELD_SPIKE_BP

        cpi_flags = (post_cpi["cpi_yoy"] > INFLATION_YOY_THRESHOLD).fillna(False).tolist()
        max_cpi_run = max_consecutive_true(cpi_flags)
        cpi_breach = max_cpi_run >= INFLATION_SUSTAINED_MONTHS

        result = {
            "threshold_debt_gdp": threshold,
            "crossing_year": year,
            "debt_gdp_at_crossing": float(crossed.iloc[0]["debt_gdp"]),
            "pre_12m_yield_mean": pre_yield_mean,
            "post_24m_yield_max": post_yield_max,
            "yield_spike_bp": yield_spike_bp,
            "yield_breach": yield_breach,
            "post_24m_max_cpi_yoy": (
                float(post_cpi["cpi_yoy"].max()) if not post_cpi["cpi_yoy"].dropna().empty else None
            ),
            "max_consecutive_months_cpi_yoy_gt_5": int(max_cpi_run),
            "cpi_breach": cpi_breach,
        }
        threshold_results.append(result)
        if yield_breach or cpi_breach:
            breaches.append(result)
        if pre_yield.empty or post_yield.empty or post_cpi["cpi_yoy"].dropna().empty:
            missing_windows.append({"threshold": threshold, "reason": "incomplete primary window"})

    method_valid = not missing_windows and len(threshold_results) == len(THRESHOLDS)
    if breaches:
        verdict_label = "refuted"
        verdict = (
            "refuted - at least one Japan debt/GDP threshold crossing was followed "
            "by a registered yield or inflation crisis breach."
        )
    elif method_valid:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED - Japan crossed 150%, 200%, and 250% gross public debt/GDP "
            "without a >300bp 10y JGB yield spike or 12 consecutive months of CPI "
            "inflation above 5% in the following 24 months."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            "weakened - observed windows show no registered yield or inflation "
            "crisis breach, but at least one primary threshold window is incomplete."
        )

    manifest = {
        "gross_public_debt_pct_gdp": ("imf", "GGXWDG_NGDP", debt_path),
        "jgb_yield_10y": ("fred", "IRLTLT01JPM156N", yield_path),
        "cpi_index": ("fred", "JPNCPIALLMINMEI", cpi_path),
        "jpy_usd": ("fred", "DEXJPUS", fx_path),
        "real_gdp_growth": ("world_bank_wdi", "NY.GDP.MKTP.KD.ZG", gdp_path),
        "current_account_pct_gdp": ("imf", "BCA_NGDPD", ca_path),
    }
    manifest_json = {
        key: {
            "publisher": pub,
            "series": series,
            "vintage_file": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256(path),
        }
        for key, (pub, series, path) in manifest.items()
    }

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "hypothesis_id": HID,
        "method_valid": method_valid,
        "threshold_results": threshold_results,
        "breaches": breaches,
        "missing_windows": missing_windows,
        "thresholds": {
            "debt_gdp_crossings": THRESHOLDS,
            "yield_spike_bp": YIELD_SPIKE_BP,
            "cpi_yoy_threshold": INFLATION_YOY_THRESHOLD,
            "cpi_sustained_months": INFLATION_SUSTAINED_MONTHS,
        },
        "context": {
            "max_debt_gdp_1990_2020": float(
                debt[(debt["year"] >= 1990) & (debt["year"] <= 2020)]["debt_gdp"].max()
            ),
            "max_jgb_10y_1990_2020": float(
                yields[(yields["date"].dt.year >= 1990) & (yields["date"].dt.year <= 2020)]["jgb_10y"].max()
            ),
            "max_cpi_yoy_1990_2020": float(
                cpi[(cpi["date"].dt.year >= 1990) & (cpi["date"].dt.year <= 2020)]["cpi_yoy"].max()
            ),
        },
        "manifest": manifest_json,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
        "runner": "engine/runs/japan_public_debt_solvency_inflation_independence/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    rows = []
    for result in threshold_results:
        rows.append({"spec": "threshold", "term": f"debt_crossing_{int(result['threshold_debt_gdp'])}", "estimate": result["debt_gdp_at_crossing"]})
        rows.append({"spec": "threshold", "term": f"yield_spike_bp_after_{int(result['threshold_debt_gdp'])}", "estimate": result["yield_spike_bp"]})
        rows.append({"spec": "threshold", "term": f"max_cpi_yoy_after_{int(result['threshold_debt_gdp'])}", "estimate": result["post_24m_max_cpi_yoy"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        "hypothesis_id: " + HID + "\n"
        "run_utc: '" + pd.Timestamp.utcnow().isoformat() + "'\n"
        "vintages:\n"
        + "".join(
            f"  {key}:\n    publisher: {meta['publisher']}\n    series: {meta['series']}\n"
            f"    vintage_file: {meta['vintage_file']}\n    sha256: {meta['sha256']}\n"
            for key, meta in manifest_json.items()
        )
    )

    lines = [
        "# Japan public debt solvency / inflation independence",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Threshold Results",
        "",
        "| Debt/GDP threshold | Crossing year | Debt/GDP | Yield spike bp | Max CPI YoY | CPI >5% max run | Breach |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in threshold_results:
        breach = "yes" if r["yield_breach"] or r["cpi_breach"] else "no"
        lines.append(
            f"| {r['threshold_debt_gdp']:.0f}% | {r['crossing_year']} | "
            f"{r['debt_gdp_at_crossing']:.1f}% | {r['yield_spike_bp']:.0f} | "
            f"{r['post_24m_max_cpi_yoy']:.1f}% | "
            f"{r['max_consecutive_months_cpi_yoy_gt_5']} | {breach} |"
        )
    lines += [
        "",
        "## Method",
        "",
        "This v1 promotion tests the already-named household-debt-analogue crisis gates: "
        "a >300bp 10y JGB yield spike above the trailing-12-month pre-crossing mean, "
        "or at least 12 consecutive months of CPI inflation above 5% within 24 months "
        "after Japan crosses 150%, 200%, and 250% gross public debt/GDP.",
        "",
        "BoJ JGB holdings and CDS are mechanism/context series, not primary gates, "
        "because they are not present in the on-disk vintage tree.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    return 0 if verdict_label == "SUPPORTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
