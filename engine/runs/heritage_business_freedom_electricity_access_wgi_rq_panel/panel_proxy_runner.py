#!/usr/bin/env python3
"""Run Worker E HERITAGE candidate-screen panel graduation artifacts.

The queue inputs are candidate screens, so this helper keeps the output
methodology-safe: every result is a stronger panel artifact, not scoreboard
evidence. The estimating equation is:

  outcome_it = beta * proxy_i,t-1 + gamma * log_gdp_pc_ppp_it
               + country FE + year FE + error_it

Standard errors are clustered by country.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from linearmodels.panel import PanelOLS


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "engine" / "runs"
VINTAGES = ROOT / "data" / "vintages"
GDP_SOURCE = {
    "publisher": "world_bank_wdi",
    "series": "NY.GDP.PCAP.PP.KD",
    "label": "PPP GDP per capita, constant international dollars",
}
REGION_SOURCE = {
    "publisher": "heritage_ief",
    "series": "ief_panel",
    "label": "Heritage IEF country region mapping",
}


def latest_path(publisher: str, series: str) -> Path:
    files = sorted((VINTAGES / publisher).glob(f"{series}@*.parquet"), key=lambda p: p.name)
    if not files:
        raise FileNotFoundError(f"Missing vintage for {publisher}:{series}")
    return files[-1]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_series(source: dict[str, Any], column: str, start_year: int, end_year: int) -> tuple[pd.DataFrame, Path]:
    path = latest_path(source["publisher"], source["series"])
    df = pd.read_parquet(path)
    iso_col = "country_iso3" if "country_iso3" in df.columns else "iso3"
    out = df[[iso_col, "year", "value"]].rename(columns={iso_col: "country_iso3", "value": column}).copy()
    out["country_iso3"] = out["country_iso3"].astype(str)
    out = out[out["country_iso3"].str.fullmatch(r"[A-Z]{3}")]
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["country_iso3", "year", column])
    out["year"] = out["year"].astype(int)
    out = out[(out["year"] >= start_year) & (out["year"] <= end_year)]
    out = out.groupby(["country_iso3", "year"], as_index=False)[column].mean()
    return out, path


def region_map() -> tuple[pd.DataFrame, Path]:
    path = latest_path(REGION_SOURCE["publisher"], REGION_SOURCE["series"])
    df = pd.read_parquet(path)
    out = df[["country_iso3", "region"]].dropna().drop_duplicates("country_iso3").copy()
    out["country_iso3"] = out["country_iso3"].astype(str)
    out = out[out["country_iso3"].str.fullmatch(r"[A-Z]{3}")]
    return out, path


def build_proxy(spec: dict[str, Any], start_year: int, end_year: int) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    proxy_sources = spec["proxy_sources"]
    loaded: list[dict[str, Any]] = []
    if spec["proxy_kind"] == "single":
        source = proxy_sources[0]
        df, path = load_series(source, "proxy", start_year - 1, end_year)
        loaded.append({**source, "vintage_file": rel(path), "sha256": sha256(path)})
        return df, loaded

    frames: list[pd.DataFrame] = []
    for source in proxy_sources:
        name = source["name"]
        df, path = load_series(source, name, start_year - 1, end_year)
        frames.append(df)
        loaded.append({**source, "vintage_file": rel(path), "sha256": sha256(path)})
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=["country_iso3", "year"], how="outer")
    for source in proxy_sources:
        name = source["name"]
        merged[f"{name}_z"] = merged.groupby("year")[name].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        )
    z_cols = [f"{source['name']}_z" for source in proxy_sources]
    merged["proxy"] = merged[z_cols].mean(axis=1)
    return merged[["country_iso3", "year", "proxy"]].dropna(), loaded


def transform_outcome(df: pd.DataFrame, transform: str | None) -> pd.DataFrame:
    if transform == "log":
        df = df.copy()
        df["outcome"] = np.log(df["outcome"].where(df["outcome"] > 0))
        return df.dropna(subset=["outcome"])
    if transform in (None, "level"):
        return df
    raise ValueError(f"Unsupported outcome transform: {transform}")


def fit_panel(df: pd.DataFrame):
    panel = df.set_index(["country_iso3", "year"]).sort_index()
    model = PanelOLS(
        panel["outcome"],
        panel[["proxy_lag1", "log_gdp_pc_ppp"]],
        entity_effects=True,
        time_effects=True,
        drop_absorbed=True,
        check_rank=False,
    )
    return model.fit(cov_type="clustered", cluster_entity=True)


def verdict_label(coef: float, p_value: float, expected_sign: str, alpha: float) -> str:
    expected_direction = coef > 0 if expected_sign == "+" else coef < 0
    if expected_direction and p_value <= alpha:
        return "SUPPORTED"
    if (not expected_direction) and p_value <= alpha:
        return "REFUTED"
    return "PARTIAL"


def fmt(x: float | int | None, digits: int = 4) -> str:
    if x is None:
        return "NA"
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "NA"
    return f"{x:.{digits}g}" if isinstance(x, float) else str(x)


def make_chart(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for year, part in df.groupby("year"):
        rows.append(
            {
                "year": int(year),
                "mean_outcome": float(part["outcome"].mean()),
                "mean_proxy_lag1": float(part["proxy_lag1"].mean()),
                "n": int(len(part)),
            }
        )
    return rows


def write_result_card(
    run_dir: Path,
    spec: dict[str, Any],
    label: str,
    reason: str,
    estimate: dict[str, Any],
    robustness: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    lines = [
        f"# Result card - {spec['hypothesis_id']}",
        "",
        f"**Verdict:** {label} - {reason}",
        "",
        "## Candidate Screen Source",
        f"- Queue rank: {spec['source_rank']}.",
        f"- Original candidate: `{spec['source_hypothesis_id']}`.",
        f"- Original controlled screen: {spec['source_controlled_verdict']}; q={spec['source_bh_q_value']}.",
        "",
        "## Panel Graduation Design",
        f"- Treatment proxy: {spec['proxy_label']} lagged one year.",
        f"- Outcome: {spec['outcome_label']} ({spec['outcome_source']['publisher']}:{spec['outcome_source']['series']}).",
        "- Estimator: country and year fixed effects with log PPP GDP per capita control.",
        "- Standard errors: clustered by country.",
        "- Gate: expected coefficient sign plus p <= 0.10 for support.",
        "",
        "## Estimate",
        f"- Usable panel: {estimate['n_obs']} observations, {estimate['n_countries']} countries, years {estimate['year_min']}-{estimate['year_max']}.",
        f"- Coefficient on lagged proxy: {fmt(estimate['coefficient'], 5)}.",
        f"- Standard error: {fmt(estimate['std_error'], 5)}.",
        f"- p-value: {fmt(estimate['p_value'], 5)}.",
        f"- Expected sign: `{spec['expected_sign']}`.",
        "",
        "## Leave-One-Region-Out",
        "| Omitted region | Coef | p-value | n | countries | direction ok |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in robustness:
        lines.append(
            f"| {row['omitted_region']} | {fmt(row['coefficient'], 5)} | {fmt(row['p_value'], 5)} | "
            f"{row['n_obs']} | {row['n_countries']} | {str(row['direction_ok']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Methodology Status",
            "This is a Worker E stronger panel artifact derived from a post-estimation HERITAGE candidate screen. "
            "It is not scoreboard evidence and should not be promoted without a matching pre-registration/spec audit.",
            "",
            "## Provenance",
            "Exact vintages and SHA-256 hashes are recorded in `manifest.yaml`. Re-run with `replication.py`.",
        ]
    )
    run_dir.joinpath("result_card.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(spec: dict[str, Any]) -> int:
    start_year = int(spec.get("start_year", 1996))
    end_year = int(spec.get("end_year", 2023))
    alpha = float(spec.get("alpha", 0.10))
    run_dir = RUNS / spec["hypothesis_id"]
    run_dir.mkdir(parents=True, exist_ok=True)

    outcome, outcome_path = load_series(spec["outcome_source"], "outcome", start_year, end_year)
    outcome = transform_outcome(outcome, spec.get("outcome_transform"))
    proxy, proxy_vintages = build_proxy(spec, start_year, end_year)
    proxy = proxy.sort_values(["country_iso3", "year"])
    proxy["proxy_lag1"] = proxy.groupby("country_iso3")["proxy"].shift(1)

    gdp, gdp_path = load_series(GDP_SOURCE, "gdp_pc_ppp", start_year, end_year)
    gdp["log_gdp_pc_ppp"] = np.log(gdp["gdp_pc_ppp"].where(gdp["gdp_pc_ppp"] > 0))
    gdp = gdp[["country_iso3", "year", "log_gdp_pc_ppp"]].dropna()
    regions, region_path = region_map()

    panel = (
        outcome.merge(proxy[["country_iso3", "year", "proxy_lag1"]], on=["country_iso3", "year"])
        .merge(gdp, on=["country_iso3", "year"])
        .merge(regions, on="country_iso3", how="left")
        .dropna(subset=["outcome", "proxy_lag1", "log_gdp_pc_ppp"])
    )
    if panel.empty:
        raise RuntimeError("No usable panel rows after merge")

    result = fit_panel(panel)
    coef = float(result.params["proxy_lag1"])
    se = float(result.std_errors["proxy_lag1"])
    p_value = float(result.pvalues["proxy_lag1"])
    expected_ok = coef > 0 if spec["expected_sign"] == "+" else coef < 0
    label = verdict_label(coef, p_value, spec["expected_sign"], alpha)
    if label == "SUPPORTED":
        reason = f"lagged proxy has expected sign {spec['expected_sign']} and p={p_value:.4g}"
        graduation_status = "panel_supported_not_scoreboard_eligible"
    elif expected_ok:
        reason = f"lagged proxy has expected sign {spec['expected_sign']} but p={p_value:.4g} exceeds {alpha}"
        graduation_status = "panel_directional_but_not_decisive"
    else:
        reason = f"lagged proxy is wrong-signed for expected sign {spec['expected_sign']} and p={p_value:.4g}"
        graduation_status = "panel_blocker_not_confirmed"

    robustness = []
    for region in sorted(x for x in panel["region"].dropna().unique() if isinstance(x, str)):
        subset = panel[panel["region"] != region]
        if subset["country_iso3"].nunique() < 20 or len(subset) < 100:
            continue
        rr = fit_panel(subset)
        rcoef = float(rr.params["proxy_lag1"])
        rp = float(rr.pvalues["proxy_lag1"])
        robustness.append(
            {
                "omitted_region": region,
                "coefficient": rcoef,
                "std_error": float(rr.std_errors["proxy_lag1"]),
                "p_value": rp,
                "n_obs": int(len(subset)),
                "n_countries": int(subset["country_iso3"].nunique()),
                "direction_ok": bool(rcoef > 0 if spec["expected_sign"] == "+" else rcoef < 0),
            }
        )

    run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    estimate = {
        "coefficient": coef,
        "std_error": se,
        "p_value": p_value,
        "n_obs": int(len(panel)),
        "n_countries": int(panel["country_iso3"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "r_squared_within": float(result.rsquared_within),
        "entity_effects": True,
        "time_effects": True,
        "cluster": "country",
        "method": "linearmodels.PanelOLS",
        "formula": "outcome ~ lag1_proxy + log_gdp_pc_ppp + country FE + year FE",
    }
    manifest = {
        "hypothesis_id": spec["hypothesis_id"],
        "run_utc": run_utc,
        "runner": "replication.py",
        "scoreboard_eligible": False,
        "methodology_gate": "candidate_screen_graduation_artifact_not_scoreboard_evidence",
        "graduation_status": graduation_status,
        "source_candidate_screen": {
            "rank": spec["source_rank"],
            "hypothesis_id": spec["source_hypothesis_id"],
            "controlled_verdict": spec["source_controlled_verdict"],
            "bh_q_value": spec["source_bh_q_value"],
            "run_path": spec["source_run_path"],
        },
        "design": {
            "template": "heritage_proxy_panel_fe",
            "start_year": start_year,
            "end_year": end_year,
            "treatment_proxy": spec["proxy_label"],
            "proxy_lag": 1,
            "outcome": spec["outcome_label"],
            "outcome_transform": spec.get("outcome_transform") or "level",
            "controls": ["log_gdp_pc_ppp"],
            "fixed_effects": ["country", "year"],
            "cluster": "country",
            "expected_sign": spec["expected_sign"],
            "alpha": alpha,
            "leave_one_region_out": True,
        },
        "vintages": {
            "outcome": {
                **spec["outcome_source"],
                "vintage_file": rel(outcome_path),
                "sha256": sha256(outcome_path),
            },
            "proxy_sources": proxy_vintages,
            "gdp_control": {**GDP_SOURCE, "vintage_file": rel(gdp_path), "sha256": sha256(gdp_path)},
            "region_map": {**REGION_SOURCE, "vintage_file": rel(region_path), "sha256": sha256(region_path)},
        },
    }
    diagnostics = {
        "hypothesis_id": spec["hypothesis_id"],
        "verdict": f"{label} - {reason}",
        "verdict_label": label,
        "verdict_reason": reason,
        "scoreboard_eligible": False,
        "methodology_gate": manifest["methodology_gate"],
        "graduation_status": graduation_status,
        "template": "heritage_proxy_panel_fe",
        "source_candidate_screen": manifest["source_candidate_screen"],
        "estimate": estimate,
        "robustness": {"leave_one_region_out": robustness},
        "data_status": {
            "variables_loaded": [
                {"role": "outcome", "source": spec["outcome_source"], "vintage_file": rel(outcome_path), "n_rows": int(len(outcome))},
                {"role": "proxy", "source": spec["proxy_sources"], "n_rows": int(len(proxy))},
                {"role": "control", "source": GDP_SOURCE, "vintage_file": rel(gdp_path), "n_rows": int(len(gdp))},
                {"role": "region", "source": REGION_SOURCE, "vintage_file": rel(region_path), "n_rows": int(len(regions))},
            ],
            "variables_missing": [],
        },
        "run_utc": run_utc,
        "runner": "replication.py",
    }

    run_dir.joinpath("diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    run_dir.joinpath("manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=False), encoding="utf-8")
    run_dir.joinpath("chart_data.json").write_text(
        json.dumps({"kind": "heritage_proxy_panel_summary", "series": make_chart(panel)}, indent=2) + "\n",
        encoding="utf-8",
    )
    write_result_card(run_dir, spec, label, reason, estimate, robustness, manifest)
    return 0


if __name__ == "__main__":
    print("Import this helper from a run-local replication.py wrapper.", file=sys.stderr)
    raise SystemExit(2)
