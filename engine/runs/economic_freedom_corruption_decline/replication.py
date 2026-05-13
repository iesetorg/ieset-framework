#!/usr/bin/env python3
"""Direct V-Dem upgrade for economic_freedom_corruption_decline.

The earlier run reused a broad WGI regulatory-quality/control-of-corruption
panel. This version uses V-Dem corruption outcomes and V-Dem rule of law.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from linearmodels.panel import PanelOLS


REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "economic_freedom_corruption_decline"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID
PERIOD = (1996, 2023)
COUNTRIES = [
    "USA", "GBR", "CAN", "AUS", "NZL", "DEU", "FRA", "ITA", "ESP", "NLD",
    "SWE", "NOR", "DNK", "FIN", "JPN", "KOR", "CHN", "IND", "BRA", "MEX",
    "CHL", "ARG", "TUR", "ZAF", "POL", "EST", "VNM", "THA", "MYS", "IDN",
    "COL", "PER", "PHL", "EGY", "MAR", "KEN", "NGA", "BGD", "PAK", "LKA",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, pattern: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(pattern), key=lambda p: p.stat().st_mtime)
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
    return out, {"file": str(path.relative_to(REPO_ROOT)), "sha256": sha256(path), "series": series}


def load_vdem() -> tuple[pd.DataFrame, dict]:
    cols = [
        "country_text_id",
        "country_name",
        "year",
        "v2x_corr",
        "v2x_pubcorr",
        "v2x_execorr",
        "v2xnp_client",
        "v2xcl_rol",
    ]
    path = latest("vdem", "vdem_cy_full@*.parquet")
    df = pq.read_table(path, columns=cols).to_pandas()
    df = df.rename(columns={"country_text_id": "country"})
    df["year"] = df["year"].astype(int)
    for col in cols[3:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    out = df[["country", "country_name", "year"] + cols[3:]].copy()
    return out, {"file": str(path.relative_to(REPO_ROOT)), "sha256": sha256(path), "series": "vdem_cy_full"}


def assemble() -> tuple[pd.DataFrame, dict]:
    vdem, vdem_meta = load_vdem()
    gdp, gdp_meta = load_wdi("NY.GDP.PCAP.KD", "gdp_pc")
    df = vdem.merge(gdp, on=["country", "year"], how="left")
    df = df[df["country"].isin(COUNTRIES)].copy()
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])].copy()
    df["log_gdp_pc"] = np.log(df["gdp_pc"])
    df["control_of_corruption_vdem"] = 1.0 - df["v2x_corr"]
    df["public_sector_clean_vdem"] = 1.0 - df["v2x_pubcorr"]
    df["executive_clean_vdem"] = 1.0 - df["v2x_execorr"]
    df["low_clientelism_vdem"] = 1.0 - df["v2xnp_client"]
    df = df.dropna(subset=["control_of_corruption_vdem", "v2xcl_rol", "log_gdp_pc"])
    return df.reset_index(drop=True), {"vdem": vdem_meta, "gdp_pc": gdp_meta}


def fit(df: pd.DataFrame, outcome: str, label: str) -> dict:
    cols = ["country", "year", outcome, "v2xcl_rol", "log_gdp_pc"]
    d = df[cols].dropna().copy().set_index(["country", "year"])
    res = PanelOLS(
        d[outcome],
        d[["v2xcl_rol", "log_gdp_pc"]],
        entity_effects=True,
        time_effects=True,
        check_rank=False,
        drop_absorbed=True,
    ).fit(cov_type="clustered", cluster_entity=True)
    ci = res.conf_int().loc["v2xcl_rol"]
    return {
        "label": label,
        "outcome": outcome,
        "n_obs": int(res.nobs),
        "n_countries": int(d.index.get_level_values("country").nunique()),
        "coef": float(res.params["v2xcl_rol"]),
        "se": float(res.std_errors["v2xcl_rol"]),
        "p": float(res.pvalues["v2xcl_rol"]),
        "t": float(res.tstats["v2xcl_rol"]),
        "ci_lo": float(ci["lower"]),
        "ci_hi": float(ci["upper"]),
        "r2_within": float(res.rsquared_within),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df, manifest = assemble()
    primary = fit(df, "control_of_corruption_vdem", "primary_political_corruption")
    robustness = [
        fit(df, "public_sector_clean_vdem", "public_sector_corruption"),
        fit(df, "executive_clean_vdem", "executive_corruption"),
        fit(df, "low_clientelism_vdem", "clientelism"),
    ]

    same_sign = sum(1 for item in robustness if item["coef"] > 0)
    primary_positive = primary["coef"] > 0
    primary_sig = primary["p"] < 0.10

    if primary_positive and primary_sig and same_sign >= 2:
        verdict_label = "SUPPORTED"
        verdict = (
            "SUPPORTED - V-Dem rule of law predicts lower political corruption "
            f"(transformed beta={primary['coef']:+.3f}, p={primary['p']:.3f}); "
            f"{same_sign}/3 robustness outcomes have the same sign."
        )
    elif (not primary_positive) and primary_sig:
        verdict_label = "REFUTED"
        verdict = (
            "REFUTED - V-Dem rule of law significantly predicts more political corruption "
            f"(transformed beta={primary['coef']:+.3f}, p={primary['p']:.3f})."
        )
    else:
        verdict_label = "PARTIAL"
        verdict = (
            "PARTIAL - V-Dem rule-of-law association is not strong enough for support/refutation "
            f"(transformed beta={primary['coef']:+.3f}, p={primary['p']:.3f}; "
            f"{same_sign}/3 robustness outcomes same sign)."
        )

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "period": list(PERIOD),
        "primary": primary,
        "robustness": robustness,
        "falsification": {
            "expected_sign": "+",
            "primary_positive": primary_positive,
            "primary_p_lt_0_10": primary_sig,
            "robustness_same_sign_count": same_sign,
        },
        "data_rows": int(len(df)),
        "countries": sorted(df["country"].unique().tolist()),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    coefs = pd.DataFrame([primary] + robustness)
    coefs.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    chart = {
        "title": "V-Dem rule of law and political corruption",
        "subtitle": "Outcome is transformed so higher means less political corruption.",
        "series": [
            {
                "label": "country-year observations",
                "points": df[
                    ["country", "year", "v2xcl_rol", "control_of_corruption_vdem"]
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
                "estimator": "panel_fe",
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
        "- Outcome: V-Dem political corruption, transformed so higher means less corruption.",
        "- Treatment: V-Dem rule of law, where higher values mean stronger legal constraints.",
        "- Control: log real GDP per capita from WDI.",
        "",
        "## Primary Panel",
        "",
        "| term | estimate | se | p | n obs | countries |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| V-Dem rule of law | {primary['coef']:+.3f} | {primary['se']:.3f} | {primary['p']:.3f} | {primary['n_obs']} | {primary['n_countries']} |",
        "",
        "## Robustness Outcomes",
        "",
        "| outcome | estimate | p | n obs |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in robustness:
        lines.append(f"| {item['label']} | {item['coef']:+.3f} | {item['p']:.3f} | {item['n_obs']} |")
    lines.extend(["", "## Data", ""])
    for name, meta in manifest.items():
        lines.append(f"- {name}: `{meta['file']}`")
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")
    print(verdict)


if __name__ == "__main__":
    main()
