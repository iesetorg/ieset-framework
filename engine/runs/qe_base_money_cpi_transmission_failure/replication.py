#!/usr/bin/env python3
"""Replication — post-2008 QE base-money/CPI pass-through."""
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
HID = "qe_base_money_cpi_transmission_failure"
OUT_DIR = ROOT / "engine" / "runs" / HID

START = "2008-08-01"
PRIMARY_END = "2019-12-01"
SENSITIVITY_END = "2021-01-01"


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


def load_series(series: str) -> pd.Series:
    path = latest(series)
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["value"]).set_index("date")["value"].sort_index()


def window_metrics(base: pd.Series, m2: pd.Series, cpi: pd.Series, end: str) -> dict:
    start = pd.Timestamp(START)
    end_ts = pd.Timestamp(end)
    base_multiple = float(base.loc[end_ts] / base.loc[start])
    m2_multiple = float(m2.loc[end_ts] / m2.loc[start])
    cpi_multiple = float(cpi.loc[end_ts] / cpi.loc[start])
    years = (end_ts - start).days / 365.25
    avg_cpi_inflation = cpi_multiple ** (1 / years) - 1
    base_growth = base_multiple - 1
    return {
        "start": START,
        "end": end,
        "base_multiple": base_multiple,
        "m2_multiple": m2_multiple,
        "cpi_multiple": cpi_multiple,
        "m2_base_pass_through": (m2_multiple - 1) / base_growth,
        "cpi_base_pass_through": (cpi_multiple - 1) / base_growth,
        "annualised_cpi_inflation": avg_cpi_inflation,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    base = load_series("BOGMBASE")
    m2 = load_series("M2SL")
    cpi = load_series("CPIAUCSL")
    assets = load_series("WALCL")

    primary = window_metrics(base, m2, cpi, PRIMARY_END)
    sensitivity = window_metrics(base, m2, cpi, SENSITIVITY_END)
    asset_multiple = float(
        assets.loc[pd.Timestamp(PRIMARY_END):].iloc[0]
        / assets.loc[pd.Timestamp(START):].iloc[0]
    )

    supported = (
        primary["base_multiple"] >= 3.5
        and primary["cpi_base_pass_through"] < 0.20
        and primary["m2_base_pass_through"] < 0.50
    )
    refuted = (
        primary["cpi_base_pass_through"] >= 0.50
        or primary["annualised_cpi_inflation"] > 0.04
    )
    if supported:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED — monetary base rose "
            f"{primary['base_multiple']:.1f}x from Aug-2008 to Dec-2019, while "
            f"CPI/base pass-through was {primary['cpi_base_pass_through']:.2f} and "
            f"M2/base pass-through was {primary['m2_base_pass_through']:.2f}."
        )
    elif refuted:
        verdict_label = "refuted"
        verdict = (
            "refuted — CPI/base pass-through or average inflation breached the registered "
            "mechanical-transmission threshold."
        )
    else:
        verdict_label = "weakened"
        verdict = (
            "weakened — base money expanded sharply, but pass-through metrics land between "
            "the support and refutation bands."
        )

    manifest = {}
    for series in ["BOGMBASE", "M2SL", "CPIAUCSL", "WALCL"]:
        path = latest(series)
        manifest[series] = {
            "publisher": "fred",
            "series": series,
            "vintage_file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "primary_window": primary,
        "sensitivity_window": sensitivity,
        "fed_assets_multiple_primary_window": asset_multiple,
        "thresholds": {
            "support_base_multiple_min": 3.5,
            "support_cpi_base_pass_through_max": 0.20,
            "support_m2_base_pass_through_max": 0.50,
            "refute_cpi_base_pass_through_min": 0.50,
            "refute_annualised_cpi_inflation_min": 0.04,
        },
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n"
        + "\n".join(f"  {k}: {v['vintage_file']}" for k, v in manifest.items())
        + "\n"
    )
    pd.DataFrame([primary | {"window": "primary"}, sensitivity | {"window": "sensitivity"}]).to_parquet(
        OUT_DIR / "coefficients.parquet", index=False
    )
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Primary Window",
                "",
                f"- Monetary base multiple: {primary['base_multiple']:.2f}x.",
                f"- M2 multiple: {primary['m2_multiple']:.2f}x.",
                f"- CPI multiple: {primary['cpi_multiple']:.2f}x.",
                f"- CPI/base pass-through: {primary['cpi_base_pass_through']:.3f}.",
                f"- M2/base pass-through: {primary['m2_base_pass_through']:.3f}.",
                f"- Annualised CPI inflation: {primary['annualised_cpi_inflation']*100:.2f}%.",
                "",
                "## Sensitivity",
                "",
                f"- Through Jan-2021, CPI/base pass-through: {sensitivity['cpi_base_pass_through']:.3f}.",
                f"- Through Jan-2021, M2/base pass-through: {sensitivity['m2_base_pass_through']:.3f}.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
