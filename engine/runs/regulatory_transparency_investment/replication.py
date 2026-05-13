#!/usr/bin/env python3
"""Direct PMR upgrade for regulatory_transparency_investment.

The earlier run used WGI regulatory quality as a broad proxy. This upgrade uses
OECD PMR regulatory-process measures and WDI gross capital formation share.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from linearmodels.panel import PanelOLS


REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "regulatory_transparency_investment"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID
PMR_MEASURES = [
    "REGULATIONS",
    "ADREG_BURDEN",
    "IMPACT_ASSESSMENT",
    "STAKEHOLDER_ENGAG",
]
PERIOD = (2018, 2023)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, pattern: str) -> Path:
    directory = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{pattern}")
    return files[-1]


def load_wdi(series: str, name: str) -> tuple[pd.DataFrame, dict]:
    path = latest("world_bank_wdi", f"{series}@*.parquet")
    df = pq.read_table(path).to_pandas()
    df = df[(df["country_iso3"].notna()) & (df["country_iso3"].str.len() == 3)].copy()
    out = df[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out[name] = pd.to_numeric(out["value"], errors="coerce")
    out = out.rename(columns={"country_iso3": "country"})[["country", "year", name]]
    meta = {"file": str(path.relative_to(REPO_ROOT)), "sha256": sha256(path), "series": series}
    return out, meta


def load_pmr() -> tuple[pd.DataFrame, dict]:
    path = latest("oecd_pmr", "PMR@*.parquet")
    df = pq.read_table(path).to_pandas()
    sub = df[df["MEASURE"].isin(PMR_MEASURES)].copy()
    sub["year"] = sub["period"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    pivot = (
        sub.pivot_table(index=["REF_AREA", "year"], columns="MEASURE", values="value", aggfunc="mean")
        .reset_index()
        .rename(columns={"REF_AREA": "country"})
    )
    pivot["pmr_process_burden"] = pivot[PMR_MEASURES].mean(axis=1)
    meta = {
        "file": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256(path),
        "series": "PMR",
        "measures": PMR_MEASURES,
        "scale": "0-6 OECD PMR restrictiveness score; higher means more restrictive",
    }
    return pivot, meta


def assemble() -> tuple[pd.DataFrame, dict]:
    pmr, pmr_meta = load_pmr()
    invest, invest_meta = load_wdi("NE.GDI.TOTL.ZS", "investment_share")
    gdp, gdp_meta = load_wdi("NY.GDP.PCAP.KD", "gdp_pc")
    trade, trade_meta = load_wdi("NE.TRD.GNFS.ZS", "trade_openness")

    df = (
        pmr.merge(invest, on=["country", "year"], how="left")
        .merge(gdp, on=["country", "year"], how="left")
        .merge(trade, on=["country", "year"], how="left")
    )
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])].copy()
    df["log_gdp_pc"] = np.log(df["gdp_pc"])
    df = df.dropna(subset=["pmr_process_burden", "investment_share", "log_gdp_pc"])
    manifest = {
        "oecd_pmr": pmr_meta,
        "investment_share": invest_meta,
        "gdp_pc": gdp_meta,
        "trade_openness": trade_meta,
    }
    return df.reset_index(drop=True), manifest


def fit_panel(df: pd.DataFrame) -> dict:
    cols = ["country", "year", "investment_share", "pmr_process_burden", "log_gdp_pc", "trade_openness"]
    d = df[cols].dropna().copy().set_index(["country", "year"])
    y = d["investment_share"]
    x = d[["pmr_process_burden", "log_gdp_pc", "trade_openness"]]
    res = PanelOLS(
        y,
        x,
        entity_effects=True,
        time_effects=True,
        check_rank=False,
        drop_absorbed=True,
    ).fit(cov_type="clustered", cluster_entity=True)
    ci = res.conf_int().loc["pmr_process_burden"]
    return {
        "n_obs": int(res.nobs),
        "n_countries": int(d.index.get_level_values("country").nunique()),
        "coef": float(res.params["pmr_process_burden"]),
        "se": float(res.std_errors["pmr_process_burden"]),
        "p": float(res.pvalues["pmr_process_burden"]),
        "t": float(res.tstats["pmr_process_burden"]),
        "ci_lo": float(ci["lower"]),
        "ci_hi": float(ci["upper"]),
        "r2_within": float(res.rsquared_within),
    }


def normal_pvalue(t_stat: float) -> float:
    return math.erfc(abs(t_stat) / math.sqrt(2.0))


def fit_change_ols(df: pd.DataFrame) -> dict:
    wide = df.pivot_table(
        index="country",
        columns="year",
        values=["investment_share", "pmr_process_burden", "log_gdp_pc", "trade_openness"],
        aggfunc="mean",
    )
    rows = []
    for country in wide.index:
        try:
            rows.append(
                {
                    "country": country,
                    "delta_investment_share": wide.loc[country, ("investment_share", 2023)]
                    - wide.loc[country, ("investment_share", 2018)],
                    "pmr_process_burden_2018": wide.loc[country, ("pmr_process_burden", 2018)],
                    "log_gdp_pc_2018": wide.loc[country, ("log_gdp_pc", 2018)],
                    "trade_openness_2018": wide.loc[country, ("trade_openness", 2018)],
                }
            )
        except KeyError:
            continue
    d = pd.DataFrame(rows).dropna()
    y = d["delta_investment_share"].to_numpy()
    x = np.column_stack(
        [
            np.ones(len(d)),
            d["pmr_process_burden_2018"].to_numpy(),
            d["log_gdp_pc_2018"].to_numpy(),
            d["trade_openness_2018"].to_numpy(),
        ]
    )
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    dof = max(len(d) - x.shape[1], 1)
    sigma2 = float((resid @ resid) / dof)
    vcov = sigma2 * np.linalg.pinv(x.T @ x)
    se = np.sqrt(np.diag(vcov))
    t_stat = float(beta[1] / se[1]) if se[1] else float("nan")
    return {
        "n_obs": int(len(d)),
        "coef": float(beta[1]),
        "se": float(se[1]),
        "t": t_stat,
        "p_normal_approx": float(normal_pvalue(t_stat)) if not math.isnan(t_stat) else None,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df, manifest = assemble()
    panel = fit_panel(df)
    change = fit_change_ols(df)

    panel_negative = panel["coef"] < 0
    panel_sig = panel["p"] < 0.10
    change_negative = change["coef"] < 0

    if panel_negative and panel_sig and change_negative:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED - direct OECD PMR regulatory-process burden predicts lower investment share "
            f"(panel beta={panel['coef']:+.3f}, p={panel['p']:.3f}); 2018-2023 change check has same sign."
        )
    elif (not panel_negative) and panel_sig:
        verdict_label = "REFUTED"
        verdict = (
            "REFUTED - direct OECD PMR regulatory-process burden predicts higher investment share "
            f"(panel beta={panel['coef']:+.3f}, p={panel['p']:.3f})."
        )
    else:
        verdict_label = "PARTIAL"
        verdict = (
            "PARTIAL - direct PMR estimate is not strong enough for support/refutation "
            f"(panel beta={panel['coef']:+.3f}, p={panel['p']:.3f}; "
            f"change beta={change['coef']:+.3f})."
        )

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "period": list(PERIOD),
        "primary_panel": panel,
        "change_check": change,
        "falsification": {
            "expected_sign": "-",
            "panel_negative": panel_negative,
            "panel_p_lt_0_10": panel_sig,
            "change_negative": change_negative,
        },
        "data_rows": int(len(df)),
        "countries": sorted(df["country"].unique().tolist()),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    coefficients = pd.DataFrame(
        [
            {"spec": "primary_panel", "term": "pmr_process_burden", **panel},
            {"spec": "change_check", "term": "pmr_process_burden_2018", **change},
        ]
    )
    coefficients.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    chart = {
        "title": "OECD PMR regulatory-process burden and investment share",
        "subtitle": "Higher PMR burden scores mean more restrictive regulation.",
        "series": [
            {
                "label": "country-year observations",
                "points": df[
                    ["country", "year", "pmr_process_burden", "investment_share"]
                ].to_dict(orient="records"),
            }
        ],
        "sources": manifest,
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": RUN_ID,
                "estimator": "pmr_panel_and_change_ols",
                "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                "vintages": manifest,
            },
            sort_keys=False,
        )
    )

    lines = [
        f"# Result card - {RUN_ID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## What Was Measured",
        "",
        "- Outcome: investment share, measured as gross capital formation as a percent of GDP.",
        "- Treatment: OECD PMR regulatory-process burden, averaging regulations impact evaluation, administrative burden, impact assessment, and stakeholder engagement scores.",
        "- Interpretation: higher PMR scores mean more restrictive or weaker regulatory process quality, so a negative coefficient supports the claim.",
        "",
        "## Primary Panel",
        "",
        "| term | estimate | se | p | n obs | countries |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| PMR process burden | {panel['coef']:+.3f} | {panel['se']:.3f} | {panel['p']:.3f} | {panel['n_obs']} | {panel['n_countries']} |",
        "",
        "## 2018-2023 Change Check",
        "",
        "| term | estimate | se | p approx | n countries |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| 2018 PMR process burden | {change['coef']:+.3f} | {change['se']:.3f} | {change['p_normal_approx']:.3f} | {change['n_obs']} |",
        "",
        "## Data",
        "",
    ]
    for name, meta in manifest.items():
        lines.append(f"- {name}: `{meta['file']}`")
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")
    print(verdict)


if __name__ == "__main__":
    main()
