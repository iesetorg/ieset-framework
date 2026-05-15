#!/usr/bin/env python3
"""Run-local replication for eurostat_industrial_electricity_price_manufacturing_va_2007_2025."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
VINTAGES = ROOT / "data" / "vintages"
HYPOTHESIS_ID = "eurostat_industrial_electricity_price_manufacturing_va_2007_2025"

ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
    "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC",
    "ES": "ESP", "FI": "FIN", "FR": "FRA", "GB": "GBR", "HR": "HRV",
    "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU",
    "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR",
    "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN",
    "SK": "SVK", "UK": "GBR",
}
CLAIM = "Higher industrial electricity prices predict lower manufacturing value-added shares in European panels."
SCHOOLS = ("classical_liberal", "ordoliberal", "developmentalism")


def latest(pub: str, stem: str) -> Path:
    files = sorted((VINTAGES / pub).glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing local vintage {pub}:{stem}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def meta(pub: str, stem: str, label: str) -> dict:
    path = latest(pub, stem)
    return {
        "publisher": pub,
        "series": stem,
        "label": label,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def industrial_price() -> tuple[pd.DataFrame, dict]:
    path = latest("eurostat", "nrg_pc_205")
    df = pd.read_parquet(path)
    df = df[
        (df["siec"] == "E7000")
        & (df["nrg_cons"] == "MWH2000-19999")
        & (df["unit"] == "KWH")
        & (df["tax"] == "I_TAX")
        & (df["currency"] == "EUR")
    ].copy()
    df["country"] = df["geo_code"].map(ISO2_TO_ISO3)
    df["year"] = df["period"].astype(str).str.slice(0, 4).astype(int)
    df["industrial_electricity_price"] = pd.to_numeric(df["value"], errors="coerce")
    annual = (
        df.dropna(subset=["country", "industrial_electricity_price"])
        .groupby(["country", "year"], as_index=False)["industrial_electricity_price"]
        .mean()
    )
    return annual, meta("eurostat", "nrg_pc_205", "industrial electricity prices, medium band, EUR/kWh incl. taxes")


def wdi(stem: str, out_col: str) -> tuple[pd.DataFrame, dict]:
    path = latest("world_bank_wdi", stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].copy()
    out.columns = ["country", "year", out_col]
    out["country"] = out["country"].astype(str).str.upper()
    out = out[out["country"].str.fullmatch(r"[A-Z]{3}")]
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out[out_col] = pd.to_numeric(out[out_col], errors="coerce")
    return out.dropna(), meta("world_bank_wdi", stem, out_col)


def verdict(coef: float, pval: float) -> tuple[str, str]:
    if pval < 0.10 and coef < 0:
        return "SUPPORTED", "coefficient is statistically significant in the predicted direction"
    if pval < 0.10 and coef > 0:
        return "REFUTED", "coefficient is statistically significant in the opposite direction"
    return "PARTIAL", "coefficient is not statistically decisive at p<0.10"


def main() -> int:
    run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    price, price_meta = industrial_price()
    manufacturing, manufacturing_meta = wdi("NV.IND.MANF.ZS", "manufacturing_va_share")
    gdp, gdp_meta = wdi("NY.GDP.PCAP.KD.ZG", "gdp_pc_growth")
    panel = price.merge(manufacturing, on=["country", "year"], how="outer").merge(gdp, on=["country", "year"], how="outer")
    keys = ["industrial_electricity_price", "manufacturing_va_share", "gdp_pc_growth"]
    d = panel[["country", "year"] + keys].replace([math.inf, -math.inf], float("nan")).dropna().copy()
    d = d[(d["year"] >= 2019) & (d["year"] <= 2025)]
    d["year"] = d["year"].astype(int)
    for col in keys:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna()
    if len(d) < 30 or d["country"].nunique() < 8:
        raise ValueError(f"insufficient usable panel for {HYPOTHESIS_ID}: n={len(d)}, countries={d['country'].nunique()}")

    formula = "Q('manufacturing_va_share') ~ Q('industrial_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)"
    model = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
    term = "Q('industrial_electricity_price')"
    coef = float(model.params[term])
    se = float(model.bse[term])
    pval = float(model.pvalues[term])
    ci = [float(x) for x in model.conf_int().loc[term].tolist()]
    label, reason = verdict(coef, pval)

    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID,
        "verdict_label": label,
        "verdict_reason": reason,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "period_min": int(d["year"].min()),
        "period_max": int(d["year"].max()),
        "formula": formula,
        "coefficient": coef,
        "standard_error_cluster_country": se,
        "p_value": pval,
        "ci95": ci,
        "direction": "-",
        "treatment": "industrial_electricity_price",
        "outcome": "manufacturing_va_share",
        "controls": ["gdp_pc_growth"],
        "run_utc": run_utc,
        "runner": f"engine/runs/{HYPOTHESIS_ID}/replication.py",
        "school_focus": list(SCHOOLS),
        "batch": "06_eurostat_energy_prices_nuclear_transition",
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "hypothesis_id": HYPOTHESIS_ID,
        "run_utc": run_utc,
        "verdict_label": label,
        "vintages": {
            "industrial_electricity_price": price_meta,
            "manufacturing_va_share": manufacturing_meta,
            "gdp_pc_growth": gdp_meta,
        },
        "formula": formula,
    }
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    pd.DataFrame(
        [{"term": "industrial_electricity_price", "coefficient": coef, "std_error": se, "p_value": pval, "ci95_low": ci[0], "ci95_high": ci[1]}]
    ).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    chart = d[["country", "year", "industrial_electricity_price", "manufacturing_va_share"]].sort_values(["country", "year"]).to_dict(orient="records")
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart[:2000], indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(
        f"# Result card - {HYPOTHESIS_ID}\n\n"
        f"**Verdict:** {label} - {reason}.\n\n"
        "## Plain-English Claim\n\n"
        f"{CLAIM}\n\n"
        "## School Coverage\n\n"
        f"{', '.join(SCHOOLS)}\n\n"
        "## What Was Measured\n\n"
        "- Outcome: `manufacturing_va_share`.\n"
        "- Treatment: `industrial_electricity_price`.\n"
        "- Controls: `gdp_pc_growth`.\n\n"
        "## Results\n\n"
        f"- Usable panel: **{len(d):,} observations**, **{d['country'].nunique()} countries**, {int(d['year'].min())}-{int(d['year'].max())}.\n"
        f"- Coefficient on treatment: **{coef:.4f}** (SE {se:.4f}, p={pval:.4f}).\n\n"
        "## Specification\n\n"
        f"`{formula}`\n\n"
        "This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.\n",
        encoding="utf-8",
    )
    print(f"{HYPOTHESIS_ID}: {label} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
