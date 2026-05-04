#!/usr/bin/env python3
"""Replication — Argentina FX/fiscal overlap mechanism test."""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[3]
HID = "argentina_fx_obligation_inflation_mechanism"
OUT_DIR = ROOT / "engine" / "runs" / HID
COUNTRY = "ARG"
START_YEAR = 2014
END_YEAR = 2023


def latest(pub: str, series: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_bcra_monthly_inflation() -> pd.Series:
    path = latest("bcra", "27")
    df = pq.read_table(path).to_pandas()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["year"] = df["fecha"].dt.year
    return df.groupby("year")["valor"].apply(lambda s: (np.prod(1 + s / 100) - 1) * 100)


def load_bcra_fx_depreciation() -> pd.Series:
    path = latest("bcra", "4")
    df = pq.read_table(path).to_pandas()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"]).sort_values("fecha")
    df["year"] = df["fecha"].dt.year
    yearly = df.groupby("year").agg(fx_start=("valor", "first"), fx_end=("valor", "last"))
    return ((yearly["fx_end"] / yearly["fx_start"]) - 1) * 100


def load_country_series(pub: str, series: str) -> pd.Series:
    path = latest(pub, series)
    df = pq.read_table(path).to_pandas()
    out = df[df["country_iso3"].eq(COUNTRY)][["year", "value"]].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["year", "value"]).set_index("year")["value"]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    inflation = load_bcra_monthly_inflation().rename("annual_inflation")
    fx = load_bcra_fx_depreciation().rename("fx_depreciation")
    debt = load_country_series("world_bank_wdi", "DT.DOD.DECT.GN.ZS").rename("external_debt_gni")
    fiscal = load_country_series("imf", "GGXCNL_NGDP").rename("fiscal_balance_gdp")

    panel = pd.concat([inflation, fx, debt, fiscal], axis=1).loc[START_YEAR:END_YEAR]
    panel = panel.dropna()
    high = panel[panel["annual_inflation"] > 25].copy()
    high["fx_gate"] = high["fx_depreciation"] > 20
    high["debt_gate"] = high["external_debt_gni"] > 30
    high["deficit_gate"] = high["fiscal_balance_gdp"] < -2
    high["all_mechanism_gates"] = high[["fx_gate", "debt_gate", "deficit_gate"]].all(axis=1)
    corr = float(panel[["annual_inflation", "fx_depreciation"]].corr().iloc[0, 1])
    share_all = float(high["all_mechanism_gates"].mean()) if len(high) else 0.0

    if len(high) and share_all == 1.0 and corr >= 0.60:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED — every high-inflation year in the 2014-2023 BCRA/WDI/IMF overlap "
            f"window clears the FX/debt/deficit mechanism gates, and inflation-FX correlation is {corr:.2f}."
        )
    elif share_all < 0.50 or corr < 0.20:
        verdict_label = "refuted"
        verdict = (
            "refuted — fewer than half of high-inflation years clear all mechanism gates, "
            f"or inflation-FX correlation is too weak ({corr:.2f})."
        )
    else:
        verdict_label = "partial"
        verdict = (
            "partial — the mechanism is visible in the local overlap window, but not all registered "
            "support gates are cleared."
        )

    manifest = {}
    for key, pub, series in [
        ("bcra_monthly_inflation", "bcra", "27"),
        ("bcra_official_fx", "bcra", "4"),
        ("external_debt_gni", "world_bank_wdi", "DT.DOD.DECT.GN.ZS"),
        ("fiscal_balance", "imf", "GGXCNL_NGDP"),
    ]:
        path = latest(pub, series)
        manifest[key] = {
            "publisher": pub,
            "series": series,
            "vintage_file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }

    rows = []
    for year, r in panel.iterrows():
        rec = {"year": int(year)}
        rec.update({k: float(v) for k, v in r.items()})
        if year in high.index:
            rec.update(
                {
                    "high_inflation_year": True,
                    "fx_gate": bool(high.loc[year, "fx_gate"]),
                    "debt_gate": bool(high.loc[year, "debt_gate"]),
                    "deficit_gate": bool(high.loc[year, "deficit_gate"]),
                    "all_mechanism_gates": bool(high.loc[year, "all_mechanism_gates"]),
                }
            )
        else:
            rec["high_inflation_year"] = False
        rows.append(rec)

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "method_valid": True,
        "period": [START_YEAR, END_YEAR],
        "n_years": int(len(panel)),
        "n_high_inflation_years": int(len(high)),
        "share_high_years_all_gates": share_all,
        "inflation_fx_corr": corr,
        "rows": rows,
        "manifest": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        "inputs:\n" + "\n".join(f"  {k}: {v['vintage_file']}" for k, v in manifest.items()) + "\n"
    )
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "result_card.md").write_text(
        "\n".join(
            [
                f"# {HID}",
                "",
                f"**Verdict:** {verdict}",
                "",
                "## Registered Overlap Test",
                "",
                "- High inflation: compounded BCRA monthly inflation >25%.",
                "- Mechanism gates: FX depreciation >20%, external debt/GNI >30%, fiscal balance <-2% GDP.",
                f"- High-inflation years clearing all gates: {int(high['all_mechanism_gates'].sum())}/{len(high)}.",
                f"- Inflation-FX depreciation correlation: {corr:.3f}.",
                "",
                "## Method Note",
                "",
                "This is a local-data overlap-window test, not the full 1971-2023 VECM.",
                "",
            ]
        )
    )
    print("verdict:", verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
