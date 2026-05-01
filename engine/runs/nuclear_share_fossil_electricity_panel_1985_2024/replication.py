#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "nuclear_share_fossil_electricity_panel_1985_2024"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID


def latest(series: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / "owid").glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing owid:{series}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "share-electricity-nuclear": latest("share-electricity-nuclear"),
        "share-electricity-fossil-fuels": latest("share-electricity-fossil-fuels"),
    }
    nuc = pq.read_table(paths["share-electricity-nuclear"]).to_pandas().rename(columns={"Nuclear": "nuclear_share"})
    fos = pq.read_table(paths["share-electricity-fossil-fuels"]).to_pandas().rename(columns={"Fossil fuels": "fossil_share"})
    panel = nuc.merge(fos, on=["country_iso3", "country_name", "year"], how="inner")
    panel = panel.dropna(subset=["country_iso3", "nuclear_share", "fossil_share"])
    panel = panel[(panel["year"] >= 1985) & (panel["year"] <= 2024)].copy()

    rows = []
    for iso3, g in panel.groupby("country_iso3"):
        g = g.sort_values("year")
        if len(g) < 10:
            continue
        first = g.iloc[0]
        last = g.iloc[-1]
        nuclear_change = float(last["nuclear_share"] - first["nuclear_share"])
        fossil_change = float(last["fossil_share"] - first["fossil_share"])
        if nuclear_change < 5.0:
            continue
        rows.append(
            {
                "country_iso3": iso3,
                "country_name": str(first["country_name"]),
                "start_year": int(first["year"]),
                "end_year": int(last["year"]),
                "nuclear_change_pp": nuclear_change,
                "fossil_change_pp": fossil_change,
                "passes_fossil_decline": fossil_change <= -5.0,
            }
        )

    results = pd.DataFrame(rows)
    n = len(results)
    pass_rate = float(results["passes_fossil_decline"].mean()) if n else 0.0
    median_fossil = float(results["fossil_change_pp"].median()) if n else 0.0
    if pass_rate >= 0.75 and median_fossil <= -10.0:
        verdict = "supported"
    elif pass_rate < 0.50 or median_fossil >= 0:
        verdict = "refuted"
    else:
        verdict = "partial"
    reason = f"{int(results['passes_fossil_decline'].sum())} of {n} nuclear-buildout countries pass; median fossil-share change {median_fossil:.1f}pp"

    results.to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    chart = {
        "chart_id": f"{HID}/country_endpoints",
        "title": "Nuclear-share increases and fossil-electricity-share changes",
        "type": "scatter",
        "x_axis": {"label": "Nuclear electricity share change, pp"},
        "y_axis": {"label": "Fossil electricity share change, pp"},
        "series": rows,
        "sources": [f"owid:{k}" for k in paths],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "n_countries": n,
        "pass_rate": pass_rate,
        "median_fossil_change_pp": median_fossil,
        "countries": rows,
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
        f"| {r['country_iso3']} | {r['country_name']} | {r['start_year']}-{r['end_year']} | "
        f"{r['nuclear_change_pp']:.1f} | {r['fossil_change_pp']:.1f} | "
        f"{'yes' if r['passes_fossil_decline'] else 'no'} |"
        for r in rows
    )
    card = f"""# Result card - {HID}

**Verdict:** {verdict} - {reason}

## Endpoint Test

Countries enter the test if nuclear electricity share rose by at least 5pp over their 1985-2024 window. Support requires at least 75% of those countries to show fossil electricity share declines of at least 5pp, with median fossil-share change <= -10pp.

| ISO3 | Country | Window | Nuclear change pp | Fossil change pp | Pass |
|---|---|---:|---:|---:|:---:|
{rows_md}

## Interpretation

This is a descriptive substitution-pattern test. It does not isolate nuclear policy from demand growth, hydro/renewables, or broader energy-system reforms.
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"verdict: {verdict} - {reason}")


if __name__ == "__main__":
    main()
