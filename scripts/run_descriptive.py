#!/usr/bin/env python3
"""Generic runner for hypotheses with estimator.template = descriptive.

Descriptive specs don't have a causal-inference design — the test is whether
the data shows the claimed pattern. This runner handles three common shapes:

  bilateral     — sample.countries has exactly 2 entries; compute the
                  log-ratio (or absolute ratio) of the outcome between them
                  at the end-period and compare against any threshold the
                  claim mentions (e.g. "20x", "10%", "less than half").
  pre_post      — sample.countries has 1 entry, sample has a treatment date
                  inferable from the falsification test text; compute pre-
                  vs post-mean of the outcome.
  panel_summary — many countries; compute treatment-country trajectory vs
                  donor-pool median.

Verdicts:
  SUPPORTED                  — direction matches claim AND magnitude clears the
                               extracted threshold (or, if no threshold was
                               found, the relative deviation is "large":
                               |Δ| > 0.5 in log-units or |ratio-1| > 0.2).
  REFUTED                    — direction opposite the claim.
  PARTIAL                    — direction matches but magnitude below threshold,
                               OR threshold can't be extracted and effect is
                               small.
  INCONCLUSIVE_DATA_PENDING  — outcome can't be loaded.

Usage:
    python3 scripts/run_descriptive.py <hypothesis_id>
    python3 scripts/run_descriptive.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Re-use the panel runner's vintage / spec / loader plumbing.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_panel_fe import (
    is_stub_falsification_rule,    has_committed_verdict,
    ROOT, RUNS, load_spec, load_variable, transform, parse_source,
    infer_claim_direction, build_panel, first_loaded_var,
    filter_sample,
    should_persist_preflight_inconclusive, bump_bulk_run_count,
    print_bulk_run_summary,
)


# ---------------------------------------------------------------------------
# Threshold extraction
# ---------------------------------------------------------------------------

NUM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(x|×|%|percent|pp|fold|times)?", re.I)


def extract_threshold(text: str) -> dict:
    """Look for ratio / percentage / fold thresholds in claim or falsification text.

    Returns a dict with `ratio`, `percent`, `fold`, `pp` if any are found.
    """
    out: dict = {}
    if not text:
        return out
    text = text.lower()
    for m in NUM_RE.finditer(text):
        num = float(m.group(1))
        unit = (m.group(2) or "").lower().strip("()")
        if unit in ("x", "×", "fold", "times"):
            out.setdefault("fold", num)
        elif unit in ("%", "percent"):
            out.setdefault("percent", num)
        elif unit == "pp":
            out.setdefault("pp", num)
    return out


# ---------------------------------------------------------------------------
# Comparison shapes
# ---------------------------------------------------------------------------


def bilateral_comparison(panel: pd.DataFrame, outcome: str, countries: list[str],
                         period: list[int]) -> dict:
    """Compute end-period level and log-ratio between two countries."""
    sub = panel[panel["country_iso3"].isin(countries)].copy()
    if sub.empty or outcome not in sub.columns:
        return {"error": "no data for bilateral comparison"}
    sub = sub.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"all values for {outcome} are missing"}
    end_year = period[1] if period and len(period) > 1 else int(sub["year"].max())
    # Find the latest available year in each country (within 5y of end_year).
    latest_per_country = (
        sub.groupby("country_iso3")["year"].max().to_dict()
    )
    a, b = countries[0], countries[1]
    if a not in latest_per_country or b not in latest_per_country:
        return {"error": f"missing country data: {set(countries) - set(latest_per_country)}"}
    yr_a = latest_per_country[a]
    yr_b = latest_per_country[b]
    val_a = sub[(sub["country_iso3"] == a) & (sub["year"] == yr_a)][outcome].iloc[0]
    val_b = sub[(sub["country_iso3"] == b) & (sub["year"] == yr_b)][outcome].iloc[0]
    if val_a is None or val_b is None or val_b == 0 or pd.isna(val_a) or pd.isna(val_b):
        return {"error": f"end-period values invalid: {a}={val_a}, {b}={val_b}"}
    ratio = float(val_a / val_b)
    log_diff = float(np.log(abs(val_a)) - np.log(abs(val_b))) if val_a != 0 else None
    return {
        "shape": "bilateral",
        "country_a": a, "country_b": b,
        "year_a": int(yr_a), "year_b": int(yr_b),
        "value_a": float(val_a), "value_b": float(val_b),
        "ratio_a_to_b": ratio,
        "log_diff_a_minus_b": log_diff,
        "n_obs": int(len(sub)),
    }


def pre_post_comparison(panel: pd.DataFrame, outcome: str, country: str,
                        cut_year: int, period: list[int]) -> dict:
    sub = panel[(panel["country_iso3"] == country)].copy()
    if outcome not in sub.columns:
        return {"error": f"outcome {outcome} not in panel"}
    sub = sub.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"no {country} data"}
    pre = sub[sub["year"] < cut_year][outcome]
    post = sub[sub["year"] >= cut_year][outcome]
    if len(pre) < 3 or len(post) < 3:
        return {"error": f"insufficient pre ({len(pre)}) or post ({len(post)}) obs"}
    return {
        "shape": "pre_post",
        "country": country,
        "cut_year": int(cut_year),
        "pre_mean": float(pre.mean()),
        "post_mean": float(post.mean()),
        "delta": float(post.mean() - pre.mean()),
        "log_delta": (float(np.log(abs(post.mean())) - np.log(abs(pre.mean())))
                      if pre.mean() != 0 and post.mean() != 0 else None),
        "n_pre": int(len(pre)),
        "n_post": int(len(post)),
    }


def panel_summary(panel: pd.DataFrame, outcome: str, treatment_country: str,
                  donor_countries: list[str], period: list[int]) -> dict:
    sub = panel.dropna(subset=[outcome])
    if sub.empty:
        return {"error": f"no data for {outcome}"}
    end_year = period[1] if period and len(period) > 1 else int(sub["year"].max())
    near_end = sub[sub["year"] >= end_year - 5]
    if treatment_country not in near_end["country_iso3"].values:
        return {"error": f"no {treatment_country} obs near end-period"}
    treat_val = near_end[near_end["country_iso3"] == treatment_country][outcome].mean()
    donor_panel = near_end[near_end["country_iso3"].isin(donor_countries)]
    if donor_panel.empty:
        return {"error": "no donor-pool obs near end-period"}
    donor_med = donor_panel.groupby("country_iso3")[outcome].mean().median()
    return {
        "shape": "panel_summary",
        "treatment_country": treatment_country,
        "treatment_value": float(treat_val),
        "donor_pool_median": float(donor_med),
        "ratio": float(treat_val / donor_med) if donor_med != 0 else None,
        "log_diff": (float(np.log(abs(treat_val)) - np.log(abs(donor_med)))
                     if donor_med != 0 and treat_val != 0 else None),
        "n_donor_countries": int(donor_panel["country_iso3"].nunique()),
        "end_year_window": [int(end_year - 5), int(end_year)],
    }


def _value_near_year(panel: pd.DataFrame, country: str, outcome: str, year: int) -> float | None:
    sub = panel[(panel["country_iso3"] == country)].dropna(subset=[outcome]).copy()
    if sub.empty:
        return None
    sub["_distance"] = (sub["year"].astype(int) - int(year)).abs()
    row = sub.sort_values(["_distance", "year"]).iloc[0]
    if int(row["_distance"]) > 1:
        return None
    return float(row[outcome])


def india_jam_findex_comparison(panel: pd.DataFrame, outcome: str) -> dict:
    peers = ["BRA", "IDN", "MEX", "NGA", "PHL", "ZAF"]
    start_year = 2011
    end_year = 2021
    ind_start = _value_near_year(panel, "IND", outcome, start_year)
    ind_end = _value_near_year(panel, "IND", outcome, end_year)
    if ind_start is None or ind_end is None:
        return {"error": "missing IND Findex account-ownership endpoints"}
    peer_rows = []
    for peer in peers:
        p_start = _value_near_year(panel, peer, outcome, start_year)
        p_end = _value_near_year(panel, peer, outcome, end_year)
        if p_start is None or p_end is None:
            continue
        peer_rows.append(
            {
                "country": peer,
                "start": p_start,
                "end": p_end,
                "delta_pp": p_end - p_start,
            }
        )
    if not peer_rows:
        return {"error": "no peer Findex endpoint pairs loaded"}
    ind_delta = ind_end - ind_start
    peer_mean_delta = float(np.mean([r["delta_pp"] for r in peer_rows]))
    return {
        "shape": "india_jam_findex_differential",
        "country": "IND",
        "start_year": start_year,
        "end_year": end_year,
        "ind_start": ind_start,
        "ind_end": ind_end,
        "ind_delta_pp": ind_delta,
        "peer_mean_delta_pp": peer_mean_delta,
        "differential_pp": ind_delta - peer_mean_delta,
        "peer_rows": peer_rows,
        "n_peer_countries": len(peer_rows),
    }


def india_jam_findex_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    ind_delta = comp["ind_delta_pp"]
    diff = comp["differential_pp"]
    if ind_delta >= 35.0 and diff >= 20.0:
        return (
            "SUPPORTED",
            f"IND account ownership rose {ind_delta:.1f}pp and beat peer mean by {diff:.1f}pp",
        )
    if ind_delta < 20.0 or diff < 0.0:
        return (
            "REFUTED",
            f"IND account ownership rose {ind_delta:.1f}pp with peer differential {diff:.1f}pp",
        )
    return (
        "PARTIAL",
        f"IND account ownership rose {ind_delta:.1f}pp with peer differential {diff:.1f}pp",
    )


def fiat_hard_asset_comparison(spec: dict) -> dict:
    countries = (spec.get("sample") or {}).get("countries") or []
    if not countries:
        return {"error": "no fiat-country sample defined"}

    commodity = load_variable("imf_pcps:PALLFNF")
    if commodity is None:
        commodity = load_variable("fred:PPIACO")
    if commodity is None:
        return {"error": "no commodity-basket benchmark loaded"}
    commodity_df, commodity_pub = commodity
    commodity_df = commodity_df.dropna(subset=["value"]).sort_values("year")
    commodity_df = commodity_df[
        (commodity_df["year"] >= 1990) & (commodity_df["year"] <= 2025)
    ]
    if commodity_df.empty:
        return {"error": "commodity benchmark has no usable 1990-2025 observations"}
    commodity_start = float(commodity_df.iloc[0]["value"])
    commodity_end = float(commodity_df.iloc[-1]["value"])
    commodity_ratio = commodity_end / commodity_start if commodity_start else np.nan

    housing = load_variable("bis:WS_SPP")
    housing_df = None
    if housing is not None:
        housing_df, _ = housing
        housing_df = housing_df.dropna(subset=["value"]).sort_values(["country_iso3", "year"])

    rows = []
    for country in countries:
        assets = []
        if np.isfinite(commodity_ratio) and commodity_ratio > 0:
            assets.append(
                {
                    "asset": "commodity_basket",
                    "publisher": commodity_pub,
                    "start_year": int(commodity_df.iloc[0]["year"]),
                    "end_year": int(commodity_df.iloc[-1]["year"]),
                    "asset_ratio_end_to_start": float(commodity_ratio),
                    "purchasing_power_index_end": float(100.0 / commodity_ratio),
                    "passes": bool(commodity_ratio > 1.0),
                }
            )
        if housing_df is not None:
            h = housing_df[housing_df["country_iso3"].eq(country)]
            h = h[(h["year"] >= 1971) & (h["year"] <= 2025)]
            if not h.empty and float(h.iloc[0]["value"]) != 0:
                ratio = float(h.iloc[-1]["value"] / h.iloc[0]["value"])
                assets.append(
                    {
                        "asset": "real_residential_property",
                        "publisher": "bis",
                        "start_year": int(h.iloc[0]["year"]),
                        "end_year": int(h.iloc[-1]["year"]),
                        "asset_ratio_end_to_start": ratio,
                        "purchasing_power_index_end": float(100.0 / ratio),
                        "passes": bool(ratio > 1.0),
                    }
                )
        rows.append(
            {
                "country": country,
                "assets": assets,
                "passes_any_asset": any(a["passes"] for a in assets),
            }
        )

    passed = sum(1 for row in rows if row["passes_any_asset"])
    return {
        "shape": "fiat_hard_asset_endpoint_check",
        "countries_tested": len(rows),
        "countries_passing_any_asset": passed,
        "rule": "end-of-period purchasing-power index < 100 against at least one hard-asset benchmark",
        "rows": rows,
    }


def fiat_hard_asset_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    total = comp["countries_tested"]
    passed = comp["countries_passing_any_asset"]
    if total and passed == total:
        return "SUPPORTED", f"{passed}/{total} fiat currencies lost purchasing power against at least one hard-asset benchmark"
    if passed == 0:
        return "REFUTED", "no sampled fiat currency lost purchasing power against the loaded hard-asset benchmarks"
    return "PARTIAL", f"{passed}/{total} sampled fiat currencies clear the hard-asset erosion threshold"


def _country_series(source: str, country: str, value_name: str = "value") -> pd.DataFrame | None:
    loaded = load_variable(source, value_name)
    if loaded is None:
        return None
    df, _ = loaded
    sub = df[df["country_iso3"].eq(country)].dropna(subset=["value"]).copy()
    if sub.empty:
        return None
    return sub.sort_values("year")


def _latest_value_before(df: pd.DataFrame, year: int, *, max_lag: int = 3) -> dict | None:
    sub = df[df["year"] < int(year)].copy()
    if sub.empty:
        return None
    row = sub.iloc[-1]
    if int(year) - int(row["year"]) > max_lag:
        return None
    return {"year": int(row["year"]), "value": float(row["value"])}


def japan_debt_threshold_comparison(spec: dict, *, sargent_wallace: bool = False) -> dict:
    """Debt-threshold pattern check for the Japan solvency/Sargent-Wallace specs.

    The generic descriptive runner's pre/post mean comparison is the wrong
    estimand here. These specs name explicit debt-crossing gates: after Japan
    crosses debt/GDP thresholds, do yields or CPI breach crisis thresholds?
    """
    country = "JPN"
    period = (spec.get("sample") or {}).get("period") or [1990, 2024]
    start, end = int(period[0]), int(period[1])

    debt = _country_series("imf:GGXWDG_NGDP; world_bank_wdi:GC.DOD.TOTL.GD.ZS", country, "gross_public_debt_pct_gdp")
    jgb = _country_series("boj:bond_yields_10y; fred:IRLTLT01JPM156N", country, "jgb_yield_10y")
    cpi = _country_series("fred:JPNCPIALLMINMEI; boj:CPI", country, "cpi_index")
    if debt is None or jgb is None or cpi is None:
        missing = []
        if debt is None:
            missing.append("gross public debt/GDP")
        if jgb is None:
            missing.append("10y JGB yield")
        if cpi is None:
            missing.append("CPI index")
        return {"error": f"missing primary Japan series: {missing}"}

    cpi = cpi.copy()
    cpi["cpi_yoy"] = cpi["value"].pct_change() * 100.0
    thresholds = [100.0, 150.0, 200.0, 250.0] if sargent_wallace else [150.0, 200.0, 250.0]
    rows = []
    for threshold in thresholds:
        crossed = debt[
            (debt["year"] >= start)
            & (debt["year"] <= end)
            & (debt["value"] >= threshold)
        ]
        if crossed.empty:
            rows.append(
                {
                    "threshold_debt_pct_gdp": threshold,
                    "status": "not_crossed_in_local_vintage",
                    "max_local_debt_pct_gdp": float(
                        debt[(debt["year"] >= start) & (debt["year"] <= end)]["value"].max()
                    ),
                }
            )
            continue

        cross = crossed.iloc[0]
        cross_year = int(cross["year"])
        pre_yield = _latest_value_before(jgb, cross_year)
        yield_window = jgb[(jgb["year"] >= cross_year) & (jgb["year"] <= cross_year + 2)]
        cpi_window = cpi[(cpi["year"] >= cross_year) & (cpi["year"] <= cross_year + 2)]
        max_yield = float(yield_window["value"].max()) if not yield_window.empty else None
        max_cpi_yoy = (
            float(cpi_window["cpi_yoy"].max())
            if not cpi_window.empty and cpi_window["cpi_yoy"].notna().any()
            else None
        )
        yield_spike_pp = (
            max_yield - pre_yield["value"]
            if max_yield is not None and pre_yield is not None
            else None
        )
        rows.append(
            {
                "threshold_debt_pct_gdp": threshold,
                "status": "crossed",
                "cross_year": cross_year,
                "debt_pct_gdp_at_cross": float(cross["value"]),
                "pre_cross_yield": pre_yield,
                "max_10y_yield_next_2y": max_yield,
                "yield_spike_pp_next_2y": yield_spike_pp,
                "max_cpi_yoy_next_2y": max_cpi_yoy,
                "yield_spike_breach_gt_3pp": (
                    bool(yield_spike_pp > 3.0) if yield_spike_pp is not None else None
                ),
                "cpi_breach_gt_5pct": (
                    bool(max_cpi_yoy > 5.0) if max_cpi_yoy is not None else None
                ),
            }
        )

    high_debt_start = None
    crossed_rows = [r for r in rows if r.get("status") == "crossed"]
    if crossed_rows:
        high_debt_start = int(crossed_rows[0]["cross_year"])

    post_100 = {}
    regression = None
    if sargent_wallace and high_debt_start is not None:
        jgb_post = jgb[(jgb["year"] >= high_debt_start) & (jgb["year"] <= end)]
        cpi_post = cpi[(cpi["year"] >= high_debt_start) & (cpi["year"] <= end)]
        post_100 = {
            "start_year": high_debt_start,
            "max_10y_yield_after_first_cross": float(jgb_post["value"].max()) if not jgb_post.empty else None,
            "max_cpi_yoy_after_first_cross": (
                float(cpi_post["cpi_yoy"].max())
                if not cpi_post.empty and cpi_post["cpi_yoy"].notna().any()
                else None
            ),
            "cpi_latest_year": int(cpi_post["year"].max()) if not cpi_post.empty else None,
        }
        try:
            import statsmodels.api as sm

            gdp = _country_series("world_bank_wdi:NY.GDP.MKTP.KD.ZG", country, "real_gdp_growth")
            workage = _country_series("world_bank_wdi:SP.POP.1564.TO.ZS", country, "working_age_population_share")
            current_account = _country_series("imf:BCA_NGDPD", country, "current_account_pct_gdp")
            reg = (
                debt.rename(columns={"value": "debt_pct_gdp"})[["year", "debt_pct_gdp"]]
                .merge(jgb.rename(columns={"value": "jgb_yield_10y"})[["year", "jgb_yield_10y"]], on="year")
            )
            for frame, col in (
                (gdp, "real_gdp_growth"),
                (workage, "working_age_population_share"),
                (current_account, "current_account_pct_gdp"),
            ):
                if frame is not None:
                    reg = reg.merge(
                        frame.rename(columns={"value": col})[["year", col]],
                        on="year",
                        how="left",
                    )
            reg = reg[(reg["year"] >= high_debt_start) & (reg["year"] <= min(end, 2015))]
            reg = reg.dropna()
            rhs = [c for c in ["debt_pct_gdp", "real_gdp_growth", "working_age_population_share", "current_account_pct_gdp"] if c in reg.columns]
            if len(reg) >= 8 and "debt_pct_gdp" in rhs:
                X = sm.add_constant(reg[rhs], has_constant="add")
                res = sm.OLS(reg["jgb_yield_10y"], X).fit(cov_type="HC1")
                regression = {
                    "sample_years": [int(reg["year"].min()), int(reg["year"].max())],
                    "n_obs": int(len(reg)),
                    "debt_to_yield_coefficient": float(res.params["debt_pct_gdp"]),
                    "debt_to_yield_p_value": float(res.pvalues["debt_pct_gdp"]),
                    "positive_significant_at_1pct": bool(
                        res.params["debt_pct_gdp"] > 0 and res.pvalues["debt_pct_gdp"] < 0.01
                    ),
                }
        except Exception as exc:
            regression = {"error": f"debt-yield regression unavailable: {exc}"}

    return {
        "shape": "japan_debt_threshold_gate",
        "country": country,
        "period": [start, end],
        "threshold_rows": rows,
        "post_first_debt_crossing_gate": post_100,
        "debt_yield_regression": regression,
        "distress_event_count": 0 if sargent_wallace else None,
        "distress_event_count_source": (
            "spec-coded zero-event claim; not a machine-fetched vintage"
            if sargent_wallace
            else None
        ),
        "data_coverage": {
            "debt_years": [int(debt["year"].min()), int(debt["year"].max())],
            "jgb_years": [int(jgb["year"].min()), int(jgb["year"].max())],
            "cpi_years": [int(cpi["year"].min()), int(cpi["year"].max())],
        },
    }


def japan_debt_threshold_verdict(comp: dict, *, sargent_wallace: bool = False) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]

    rows = comp.get("threshold_rows") or []
    crossed = [r for r in rows if r.get("status") == "crossed"]
    not_crossed = [r for r in rows if r.get("status") != "crossed"]
    yield_breaches = [r for r in crossed if r.get("yield_spike_breach_gt_3pp") is True]
    cpi_breaches = [r for r in crossed if r.get("cpi_breach_gt_5pct") is True]
    incomplete = [
        r
        for r in crossed
        if r.get("yield_spike_breach_gt_3pp") is None or r.get("cpi_breach_gt_5pct") is None
    ]

    if sargent_wallace:
        post = comp.get("post_first_debt_crossing_gate") or {}
        max_yield = post.get("max_10y_yield_after_first_cross")
        max_cpi = post.get("max_cpi_yoy_after_first_cross")
        regression = comp.get("debt_yield_regression") or {}
        gate_breaches = []
        if max_yield is not None and max_yield > 4.0:
            gate_breaches.append(f"post-crossing max 10y JGB yield {max_yield:.2f}% > 4%")
        if max_cpi is not None and max_cpi > 5.0:
            gate_breaches.append(f"post-crossing max CPI YoY {max_cpi:.2f}% > 5%")
        if regression.get("positive_significant_at_1pct"):
            gate_breaches.append(
                "debt-to-yield coefficient positive at p<0.01"
            )
        if gate_breaches:
            return "REFUTED", "; ".join(gate_breaches)
        caveats = []
        if not_crossed:
            caveats.append(
                "local IMF debt vintage does not cross "
                + ", ".join(f"{r['threshold_debt_pct_gdp']:.0f}%" for r in not_crossed)
            )
        if post.get("cpi_latest_year") is not None and post["cpi_latest_year"] < comp["period"][1]:
            caveats.append(f"CPI coverage stops {post['cpi_latest_year']}")
        caveats.append("distress-event count is spec-coded, not machine-fetched")
        if caveats:
            return (
                "WEAKENED",
                "no observed yield/CPI/regression breach after crossed thresholds; "
                + "; ".join(caveats),
            )
        return "SUPPORTED", "all crossed debt thresholds clear the yield/CPI/distress gates"

    if yield_breaches or cpi_breaches:
        bad = yield_breaches + cpi_breaches
        return (
            "REFUTED",
            "threshold breach at "
            + ", ".join(f"{r.get('threshold_debt_pct_gdp'):.0f}%" for r in bad),
        )
    if not_crossed or incomplete:
        reason_bits = []
        if crossed:
            reason_bits.append(
                "observed crossed thresholds clear the 300bp-yield and 5% CPI gates"
            )
        if not_crossed:
            reason_bits.append(
                "local IMF debt vintage does not cross "
                + ", ".join(f"{r['threshold_debt_pct_gdp']:.0f}%" for r in not_crossed)
            )
        if incomplete:
            reason_bits.append(
                "incomplete yield/CPI window at "
                + ", ".join(f"{r['threshold_debt_pct_gdp']:.0f}%" for r in incomplete)
            )
        return "WEAKENED", "; ".join(reason_bits)
    return "SUPPORTED", "all debt-threshold windows clear the 300bp-yield and 5% CPI gates"


def _value_at_year(df: pd.DataFrame, country: str, year: int, *, max_distance: int = 0) -> dict | None:
    sub = df[df["country_iso3"].eq(country)].dropna(subset=["value"]).copy()
    if sub.empty:
        return None
    sub["_distance"] = (sub["year"].astype(int) - int(year)).abs()
    row = sub.sort_values(["_distance", "year"]).iloc[0]
    if int(row["_distance"]) > max_distance:
        return None
    return {"year": int(row["year"]), "value": float(row["value"])}


def bangladesh_apparel_threshold_comparison() -> dict:
    manuf_loaded = load_variable("world_bank_wdi:NV.IND.MANF.ZS", "manufacturing_value_added_pct_gdp")
    growth_loaded = load_variable("world_bank_wdi:NY.GDP.PCAP.KD.ZG", "real_gdp_pc_growth")
    if manuf_loaded is None or growth_loaded is None:
        missing = []
        if manuf_loaded is None:
            missing.append("WDI manufacturing value added share")
        if growth_loaded is None:
            missing.append("WDI real GDP per-capita growth")
        return {"error": f"missing Bangladesh primary series: {missing}"}

    manuf, manuf_pub = manuf_loaded
    growth, growth_pub = growth_loaded
    start = _value_at_year(manuf, "BGD", 1985)
    end = _value_at_year(manuf, "BGD", 2019)
    if start is None or end is None:
        return {"error": "missing BGD manufacturing-share endpoint at 1985 or 2019"}
    manuf_delta = end["value"] - start["value"]

    growth_window = growth[(growth["year"] >= 2000) & (growth["year"] <= 2019)]
    bgd_growth = growth_window[growth_window["country_iso3"].eq("BGD")]["value"].dropna()
    pak_growth = growth_window[growth_window["country_iso3"].eq("PAK")]["value"].dropna()
    if bgd_growth.empty or pak_growth.empty:
        return {"error": "missing BGD/PAK real GDP-per-capita growth window"}
    bgd_mean = float(bgd_growth.mean())
    pak_mean = float(pak_growth.mean())
    growth_diff_pp = bgd_mean - pak_mean

    peers = {}
    for peer in ["PAK", "IND", "NPL", "LKA"]:
        peer_growth = growth_window[growth_window["country_iso3"].eq(peer)]["value"].dropna()
        if not peer_growth.empty:
            peers[peer] = {
                "mean_growth_2000_2019": float(peer_growth.mean()),
                "n_obs": int(len(peer_growth)),
            }

    return {
        "shape": "bangladesh_apparel_threshold_check",
        "manufacturing_source_publisher": manuf_pub,
        "growth_source_publisher": growth_pub,
        "manufacturing_share_1985": start,
        "manufacturing_share_2019": end,
        "manufacturing_share_delta_pp": float(manuf_delta),
        "manufacturing_gate_delta_ge_5pp": bool(manuf_delta >= 5.0),
        "bgd_mean_gdp_pc_growth_2000_2019": bgd_mean,
        "pak_mean_gdp_pc_growth_2000_2019": pak_mean,
        "bgd_minus_pak_growth_diff_pp": float(growth_diff_pp),
        "growth_gate_diff_ge_1pp": bool(growth_diff_pp >= 1.0),
        "peer_growth_rows": peers,
    }


def bangladesh_apparel_threshold_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    manuf_ok = comp.get("manufacturing_gate_delta_ge_5pp") is True
    growth_ok = comp.get("growth_gate_diff_ge_1pp") is True
    manuf_delta = comp.get("manufacturing_share_delta_pp")
    growth_diff = comp.get("bgd_minus_pak_growth_diff_pp")
    if manuf_ok and growth_ok:
        return (
            "SUPPORTED",
            f"manufacturing share +{manuf_delta:.2f}pp and BGD-PAK growth gap +{growth_diff:.2f}pp/yr clear both primary gates",
        )
    failed = []
    if not manuf_ok:
        failed.append(f"manufacturing share delta {manuf_delta:.2f}pp < 5pp")
    if not growth_ok:
        failed.append(f"BGD-PAK growth gap {growth_diff:.2f}pp/yr < 1pp")
    return "REFUTED", "; ".join(failed)


def monetary_finance_cpi_threshold_comparison() -> dict:
    cpi_loaded = load_variable(
        "fred:CPIAUCSL (USA); fred:JPNCPIALLMINMEI (JPN); ecb:ICP.M.U2.N.000000.4.ANR (EUR aggregate))",
        "cpi_index",
    )
    if cpi_loaded is None:
        return {"error": "missing CPI index series for USA/JPN/EUR threshold check"}
    cpi, cpi_pub = cpi_loaded
    cpi = cpi.sort_values(["country_iso3", "year"]).copy()
    cpi["cpi_yoy"] = cpi.groupby("country_iso3", sort=False)["value"].pct_change() * 100.0

    windows = {
        "zlb_2008_2014": [2008, 2014],
        "covid_2020_2021": [2020, 2021],
    }
    rows = []
    coverage = {}
    for country in ["USA", "JPN", "U2"]:
        sub = cpi[cpi["country_iso3"].eq(country)].dropna(subset=["cpi_yoy"]).copy()
        if sub.empty:
            coverage[country] = None
            continue
        coverage[country] = [int(sub["year"].min()), int(sub["year"].max())]
        for window_name, (start, end) in windows.items():
            w = sub[(sub["year"] >= start) & (sub["year"] <= end)].copy()
            if w.empty:
                rows.append(
                    {
                        "country": country,
                        "window": window_name,
                        "status": "missing_window",
                    }
                )
                continue
            peak = w.sort_values("cpi_yoy", ascending=False).iloc[0]
            rows.append(
                {
                    "country": country,
                    "window": window_name,
                    "status": "observed",
                    "n_obs": int(len(w)),
                    "max_cpi_yoy": float(peak["cpi_yoy"]),
                    "max_cpi_yoy_year": int(peak["year"]),
                    "breach_gt_3pct": bool(float(peak["cpi_yoy"]) > 3.0),
                }
            )

    return {
        "shape": "monetary_finance_cpi_threshold_gate",
        "cpi_source_publisher": cpi_pub,
        "threshold": "CPI YoY must stay below 3% in 2008-2014 and 2020-2021 windows",
        "rows": rows,
        "coverage": coverage,
        "missing_eurozone_cpi": coverage.get("U2") is None,
    }


def monetary_finance_cpi_threshold_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    rows = comp.get("rows") or []
    breaches = [r for r in rows if r.get("breach_gt_3pct") is True]
    if breaches:
        examples = "; ".join(
            f"{r['country']} {r['window']} peak {r['max_cpi_yoy']:.2f}% in {r['max_cpi_yoy_year']}"
            for r in breaches[:4]
        )
        caveat = "; Eurozone CPI not loaded" if comp.get("missing_eurozone_cpi") else ""
        return "REFUTED", f"CPI threshold breach: {examples}{caveat}"
    missing = [r for r in rows if r.get("status") == "missing_window"]
    if missing or comp.get("missing_eurozone_cpi"):
        caveats = []
        if missing:
            caveats.append(
                "missing windows: "
                + ", ".join(f"{r['country']} {r['window']}" for r in missing)
            )
        if comp.get("missing_eurozone_cpi"):
            caveats.append("Eurozone CPI not loaded")
        return "WEAKENED", "observed CPI windows clear the 3% gate; " + "; ".join(caveats)
    return "SUPPORTED", "all observed CPI windows stay below the 3% gate"


def central_bank_decoupling_usa_coverage_comparison() -> dict:
    core_loaded = load_variable("fred:CPILFESL", "core_cpi_index")
    exp_loaded = load_variable("fred:T5YIFR", "inflation_expectations_5y5y_forward")
    walcl_loaded = load_variable("fred:WALCL", "fed_balance_sheet_total_assets")
    gdp_loaded = load_variable("fred:GDP", "nominal_gdp")
    if any(v is None for v in (core_loaded, exp_loaded, walcl_loaded, gdp_loaded)):
        missing = []
        if core_loaded is None:
            missing.append("FRED CPILFESL")
        if exp_loaded is None:
            missing.append("FRED T5YIFR")
        if walcl_loaded is None:
            missing.append("FRED WALCL")
        if gdp_loaded is None:
            missing.append("FRED GDP")
        return {"error": f"missing USA central-bank decoupling inputs: {missing}"}

    core = core_loaded[0]
    exp = exp_loaded[0]
    walcl = walcl_loaded[0]
    gdp = gdp_loaded[0]

    core = core[core["country_iso3"].eq("USA")].dropna(subset=["value"]).sort_values("year").copy()
    exp = exp[exp["country_iso3"].eq("USA")].dropna(subset=["value"]).sort_values("year").copy()
    walcl = walcl[walcl["country_iso3"].eq("USA")].dropna(subset=["value"]).sort_values("year").copy()
    gdp = gdp[gdp["country_iso3"].eq("USA")].dropna(subset=["value"]).sort_values("year").copy()
    if core.empty or exp.empty or walcl.empty or gdp.empty:
        return {"error": "one or more USA central-bank decoupling inputs are empty after country filtering"}

    core["core_cpi_yoy"] = core["value"].pct_change() * 100.0
    core_baseline = float(core[(core["year"] >= 2003) & (core["year"] <= 2007)]["core_cpi_yoy"].mean())
    core_window = core[(core["year"] >= 2008) & (core["year"] <= 2020)].copy()
    core_window["divergence_from_2003_2007_mean_pp"] = core_window["core_cpi_yoy"] - core_baseline
    max_core = core_window.reindex(
        core_window["divergence_from_2003_2007_mean_pp"].abs().sort_values(ascending=False).index
    ).iloc[0]

    exp_baseline = float(exp[(exp["year"] >= 2003) & (exp["year"] <= 2007)]["value"].mean())
    exp_band = [exp_baseline - 0.75, exp_baseline + 0.75]
    exp_window = exp[(exp["year"] >= 2008) & (exp["year"] <= 2020)].copy()
    exp_window["outside_band"] = (exp_window["value"] < exp_band[0]) | (exp_window["value"] > exp_band[1])

    bs = (
        walcl.rename(columns={"value": "walcl_millions"})[["year", "walcl_millions"]]
        .merge(
            gdp.rename(columns={"value": "gdp_billions"})[["year", "gdp_billions"]],
            on="year",
            how="inner",
        )
    )
    bs["balance_sheet_pct_gdp"] = bs["walcl_millions"] / (bs["gdp_billions"] * 1000.0) * 100.0
    bs_window = bs[(bs["year"] >= 2008) & (bs["year"] <= 2020)].copy()
    max_bs = bs_window.sort_values("balance_sheet_pct_gdp", ascending=False).iloc[0]

    return {
        "shape": "central_bank_decoupling_usa_coverage_gate",
        "country": "USA",
        "coverage_scope": "USA-only; Japan/ECB/BoE core-CPI and expectations gates are not loaded",
        "core_cpi_baseline_yoy_2003_2007": core_baseline,
        "max_abs_core_cpi_divergence_2008_2020": {
            "year": int(max_core["year"]),
            "core_cpi_yoy": float(max_core["core_cpi_yoy"]),
            "divergence_pp": float(max_core["divergence_from_2003_2007_mean_pp"]),
            "breach_abs_gt_2pp": bool(abs(float(max_core["divergence_from_2003_2007_mean_pp"])) > 2.0),
        },
        "inflation_expectations_baseline_2003_2007": exp_baseline,
        "inflation_expectations_band": exp_band,
        "inflation_expectations_2008_2020_min": float(exp_window["value"].min()),
        "inflation_expectations_2008_2020_max": float(exp_window["value"].max()),
        "inflation_expectations_band_breach": bool(exp_window["outside_band"].any()),
        "balance_sheet_pct_gdp_2008": float(bs[bs["year"].eq(2008)]["balance_sheet_pct_gdp"].iloc[0]),
        "max_balance_sheet_pct_gdp_2008_2020": {
            "year": int(max_bs["year"]),
            "value": float(max_bs["balance_sheet_pct_gdp"]),
            "breach_gt_30pct": bool(float(max_bs["balance_sheet_pct_gdp"]) > 30.0),
        },
    }


def central_bank_decoupling_usa_coverage_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    core_breach = comp["max_abs_core_cpi_divergence_2008_2020"]["breach_abs_gt_2pp"]
    expectations_breach = comp["inflation_expectations_band_breach"]
    bs_value = comp["max_balance_sheet_pct_gdp_2008_2020"]["value"]
    bs_year = comp["max_balance_sheet_pct_gdp_2008_2020"]["year"]
    if core_breach or expectations_breach:
        breaches = []
        if core_breach:
            breaches.append("USA core-CPI divergence exceeds ±2pp")
        if expectations_breach:
            breaches.append("USA 5y5y expectations exit the ±0.75pp band")
        return "REFUTED", "; ".join(breaches)
    caveats = [
        "USA-only coverage; Japan/ECB/BoE gates not loaded",
        f"USA balance sheet reaches {bs_value:.2f}% of GDP in {bs_year}, just {'above' if bs_value > 30 else 'below'} the 30% claim gate",
    ]
    return (
        "WEAKENED",
        "USA core-CPI and expectations gates clear; " + "; ".join(caveats),
    )


def us_issuer_solvency_event_count_comparison(spec: dict) -> dict:
    period = (spec.get("sample") or {}).get("period") or [1971, 2024]
    start, end = int(period[0]), int(period[1])
    debt_loaded = load_variable("fred:GFDEGDQ188S", "gross_federal_debt_pct_gdp")
    dgs10_loaded = load_variable("fred:DGS10", "us_treasury_yield_10y")
    dgs30_loaded = load_variable("fred:DGS30", "us_treasury_yield_30y")
    cpi_loaded = load_variable("fred:CPIAUCSL", "cpi_index")
    if debt_loaded is None:
        return {"error": "missing FRED gross federal debt/GDP"}
    debt = debt_loaded[0]
    debt = debt[debt["country_iso3"].eq("USA")].dropna(subset=["value"]).sort_values("year")
    in_period = debt[(debt["year"] >= start) & (debt["year"] <= end)]
    if in_period.empty:
        return {"error": "gross federal debt/GDP has no USA observations in sample period"}
    over_100 = in_period[in_period["value"] >= 100.0]
    cross_100 = None
    if not over_100.empty:
        row = over_100.iloc[0]
        cross_100 = {"year": int(row["year"]), "value": float(row["value"])}

    context = {
        "gross_debt_pct_gdp_max": {
            "year": int(in_period.sort_values("value", ascending=False).iloc[0]["year"]),
            "value": float(in_period["value"].max()),
        },
        "gross_debt_pct_gdp_cross_100": cross_100,
    }

    for label, loaded in (("us_treasury_yield_10y", dgs10_loaded), ("us_treasury_yield_30y", dgs30_loaded)):
        if loaded is None:
            context[label] = None
            continue
        df = loaded[0]
        sub = df[
            (df["country_iso3"].eq("USA"))
            & (df["year"] >= start)
            & (df["year"] <= end)
        ].dropna(subset=["value"])
        if sub.empty:
            context[label] = None
            continue
        context[label] = {
            "min": float(sub["value"].min()),
            "max": float(sub["value"].max()),
            "end_year": int(sub.sort_values("year").iloc[-1]["year"]),
            "end_value": float(sub.sort_values("year").iloc[-1]["value"]),
        }

    if cpi_loaded is not None:
        cpi = cpi_loaded[0]
        cpi = cpi[
            (cpi["country_iso3"].eq("USA"))
            & (cpi["year"] >= start)
            & (cpi["year"] <= end)
        ].dropna(subset=["value"]).sort_values("year")
        if not cpi.empty:
            cpi = cpi.copy()
            cpi["cpi_yoy"] = cpi["value"].pct_change() * 100.0
            peak = cpi.sort_values("cpi_yoy", ascending=False).iloc[0]
            context["cpi_yoy_peak"] = {
                "year": int(peak["year"]),
                "value": float(peak["cpi_yoy"]),
            }

    return {
        "shape": "us_issuer_solvency_zero_event_gate",
        "country": "USA",
        "period": [start, end],
        "qualifying_default_or_distress_event_count": 0,
        "event_count_source": "spec-coded zero-event claim; machine-readable default/CDS/auction vintage not yet loaded",
        "machine_fetched_event_vintage_loaded": False,
        "cds_gate_loaded": False,
        "treasury_auction_gate_loaded": False,
        "context": context,
    }


def us_issuer_solvency_event_count_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    event_count = int(comp.get("qualifying_default_or_distress_event_count", 0))
    if event_count > 0:
        return "REFUTED", f"{event_count} qualifying dollar-denominated solvency events recorded"
    debt_cross = ((comp.get("context") or {}).get("gross_debt_pct_gdp_cross_100") or {})
    debt_text = (
        f"gross federal debt/GDP crosses 100% in {debt_cross.get('year')}"
        if debt_cross
        else "gross federal debt/GDP does not cross 100% in loaded sample"
    )
    return (
        "WEAKENED",
        f"zero qualifying events in the coded record and {debt_text}; default/CDS/auction gates are not machine-fetched yet",
    )


def fed_rrp_peak_decline_comparison() -> dict:
    """Exact peak/decline gate for the ON RRP descriptive spec.

    The generic descriptive path annualises FRED daily data, which is the
    wrong statistic for this pre-registered peak-and-trough claim.
    """
    files = sorted((ROOT / "data" / "vintages" / "fred").glob("RRPONTSYD@*.parquet"))
    if not files:
        return {"error": "missing FRED:RRPONTSYD daily vintage"}
    vintage = files[-1]
    df = pd.read_parquet(vintage)
    if "date" not in df.columns or "value" not in df.columns:
        return {"error": f"unexpected RRPONTSYD schema: {list(df.columns)}"}
    df = df.dropna(subset=["value"]).copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    peak_window = df[(df["date"] >= "2021-01-01") & (df["date"] <= "2023-12-31")]
    q3_2024 = df[(df["date"] >= "2024-07-01") & (df["date"] <= "2024-09-30")]
    mid_2024 = df[(df["date"] >= "2024-06-01") & (df["date"] <= "2024-07-31")]
    if peak_window.empty or q3_2024.empty:
        return {"error": "RRPONTSYD vintage lacks 2021-2023 peak or 2024Q3 observations"}

    peak = peak_window.loc[peak_window["value"].idxmax()]
    q3_min = q3_2024.loc[q3_2024["value"].idxmin()]
    mid_min = mid_2024.loc[mid_2024["value"].idxmin()] if not mid_2024.empty else q3_min
    decline_q3 = float(peak["value"] - q3_min["value"])
    decline_mid = float(peak["value"] - mid_min["value"])
    return {
        "shape": "fed_on_rrp_peak_decline_gate",
        "vintage_file": str(vintage.relative_to(ROOT)),
        "raw_daily_observations": int(len(df)),
        "peak_window": ["2021-01-01", "2023-12-31"],
        "peak_date": peak["date"].date().isoformat(),
        "peak_usd_bn": float(peak["value"]),
        "q3_2024_low_date": q3_min["date"].date().isoformat(),
        "q3_2024_low_usd_bn": float(q3_min["value"]),
        "decline_peak_to_q3_2024_low_usd_bn": decline_q3,
        "mid_2024_low_date": mid_min["date"].date().isoformat(),
        "mid_2024_low_usd_bn": float(mid_min["value"]),
        "decline_peak_to_mid_2024_low_usd_bn": decline_mid,
        "peak_gate_pass_ge_2000": bool(float(peak["value"]) >= 2000.0),
        "decline_gate_pass_ge_1500": bool(decline_q3 >= 1500.0),
        "mid_2024_below_500_gate": bool(float(mid_min["value"]) < 500.0),
    }


def fed_rrp_peak_decline_verdict(comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    peak = comp["peak_usd_bn"]
    decline = comp["decline_peak_to_q3_2024_low_usd_bn"]
    if comp["peak_gate_pass_ge_2000"] and comp["decline_gate_pass_ge_1500"]:
        return (
            "SUPPORTED",
            f"ON RRP peaked at ${peak:,.0f}bn and fell ${decline:,.0f}bn by 2024Q3",
        )
    if peak < 1500.0 or decline < 1000.0:
        return (
            "REFUTED",
            f"ON RRP peak ${peak:,.0f}bn or decline ${decline:,.0f}bn misses refutation gate",
        )
    return (
        "PARTIAL",
        f"one ON RRP gate clears: peak ${peak:,.0f}bn, decline ${decline:,.0f}bn",
    )


def _load_named_panel(source: str, variable_name: str) -> tuple[pd.DataFrame, str] | None:
    loaded = load_variable(source, variable_name)
    if loaded is None:
        return None
    df, publisher = loaded
    if "value" not in df.columns:
        return None
    return df.dropna(subset=["value"]).copy(), publisher


def _window_mean(
    df: pd.DataFrame,
    country: str,
    start_year: int,
    end_year: int,
    *,
    exclude_years: set[int] | None = None,
) -> dict | None:
    sub = df[
        (df["country_iso3"].eq(country))
        & (df["year"] >= int(start_year))
        & (df["year"] <= int(end_year))
    ].copy()
    if exclude_years:
        sub = sub[~sub["year"].astype(int).isin(exclude_years)]
    sub = sub.dropna(subset=["value"]).sort_values("year")
    if sub.empty:
        return None
    return {
        "country": country,
        "window": [int(start_year), int(end_year)],
        "excluded_years": sorted(exclude_years or []),
        "mean": float(sub["value"].mean()),
        "n_years": int(sub["year"].nunique()),
        "year_min": int(sub["year"].min()),
        "year_max": int(sub["year"].max()),
    }


def _window_delta(
    df: pd.DataFrame,
    country: str,
    pre: tuple[int, int],
    post: tuple[int, int],
    *,
    exclude_by_country: dict[str, set[int]] | None = None,
) -> dict | None:
    exclude_by_country = exclude_by_country or {}
    pre_row = _window_mean(
        df,
        country,
        pre[0],
        pre[1],
        exclude_years=exclude_by_country.get(country),
    )
    post_row = _window_mean(
        df,
        country,
        post[0],
        post[1],
        exclude_years=exclude_by_country.get(country),
    )
    if pre_row is None or post_row is None:
        return None
    return {
        "country": country,
        "pre": pre_row,
        "post": post_row,
        "delta_pp": float(post_row["mean"] - pre_row["mean"]),
    }


def _endpoint_value(df: pd.DataFrame, country: str, year: int) -> dict | None:
    sub = df[(df["country_iso3"].eq(country)) & (df["year"] == int(year))]
    sub = sub.dropna(subset=["value"])
    if sub.empty:
        return None
    row = sub.iloc[0]
    return {"country": country, "year": int(row["year"]), "value": float(row["value"])}


def _endpoint_delta(df: pd.DataFrame, country: str, start_year: int, end_year: int) -> dict | None:
    start = _endpoint_value(df, country, start_year)
    end = _endpoint_value(df, country, end_year)
    if start is None or end is None:
        return None
    return {
        "country": country,
        "start": start,
        "end": end,
        "delta_pp": float(end["value"] - start["value"]),
    }


def _comparator_window_deltas(
    df: pd.DataFrame,
    countries: list[str],
    pre: tuple[int, int],
    post: tuple[int, int],
    *,
    exclude_by_country: dict[str, set[int]] | None = None,
) -> list[dict]:
    rows = []
    for country in countries:
        row = _window_delta(
            df,
            country,
            pre,
            post,
            exclude_by_country=exclude_by_country,
        )
        if row is not None:
            rows.append(row)
    return rows


def _comparator_endpoint_deltas(
    df: pd.DataFrame,
    countries: list[str],
    start_year: int,
    end_year: int,
) -> list[dict]:
    rows = []
    for country in countries:
        row = _endpoint_delta(df, country, start_year, end_year)
        if row is not None:
            rows.append(row)
    return rows


def _mean_delta(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return float(np.mean([row["delta_pp"] for row in rows]))


def trade_window_threshold_comparison(hid: str) -> dict:
    trade_loaded = _load_named_panel("world_bank_wdi:NE.TRD.GNFS.ZS", "trade_openness_pct_gdp")
    manuf_loaded = _load_named_panel("world_bank_wdi:NV.IND.MANF.ZS", "manufacturing_share_of_gdp")
    if trade_loaded is None:
        return {"error": "missing WDI trade openness series NE.TRD.GNFS.ZS"}
    trade, trade_pub = trade_loaded

    if hid == "trade_lib_india_1991_tariff_cut_export_response":
        primary = _window_delta(trade, "IND", (1980, 1990), (1992, 2007))
        wide = _window_delta(trade, "IND", (1980, 1990), (1992, 2019))
        if primary is None:
            return {"error": "missing India trade-openness window data"}
        return {
            "shape": "registered_trade_window_delta",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "IND",
            "primary_delta": primary,
            "wide_post_window_delta": wide,
            "support_gate_delta_ge_10pp": bool(primary["delta_pp"] >= 10.0),
            "refute_gate_delta_lt_5pp": bool(primary["delta_pp"] < 5.0),
        }

    if hid == "trade_lib_indonesia_1980s_1990s_unilateral":
        primary = _window_delta(trade, "IDN", (1975, 1984), (1986, 1996))
        peers = _comparator_window_deltas(trade, ["MYS", "THA", "PHL"], (1975, 1984), (1986, 1996))
        if primary is None:
            return {"error": "missing Indonesia trade-openness window data"}
        return {
            "shape": "registered_trade_window_delta",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "IDN",
            "primary_delta": primary,
            "peer_deltas": peers,
            "peer_mean_delta_pp": _mean_delta(peers),
            "support_gate_delta_ge_10pp": bool(primary["delta_pp"] >= 10.0),
            "refute_gate_delta_lt_5pp": bool(primary["delta_pp"] < 5.0),
        }

    if hid == "trade_lib_egypt_fta_cascade":
        pre = _window_mean(trade, "EGY", 1995, 1999)
        peak = _window_mean(trade, "EGY", 2007, 2010)
        post = _window_mean(trade, "EGY", 2015, 2019)
        if pre is None or peak is None or post is None:
            return {"error": "missing Egypt pre/peak/post trade-openness windows"}
        rise = float(peak["mean"] - pre["mean"])
        post_minus_peak = float(post["mean"] - peak["mean"])
        return {
            "shape": "registered_egypt_fta_peak_reversal_gate",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "EGY",
            "pre_1995_1999": pre,
            "peak_2007_2010": peak,
            "post_2015_2019": post,
            "rise_pre_to_peak_pp": rise,
            "post_minus_peak_pp": post_minus_peak,
            "support_gate_rise_ge_5pp": bool(rise >= 5.0),
            "support_gate_post_close_or_below_peak_plus_2pp": bool(post["mean"] <= peak["mean"] + 2.0),
            "refute_gate_peak_did_not_materialise": bool(rise < 5.0),
        }

    if hid == "trade_lib_south_africa_sadc_trade":
        primary = _window_delta(trade, "ZAF", (1995, 1999), (2010, 2019))
        peers = _comparator_window_deltas(
            trade,
            ["BWA", "NAM", "SWZ", "LSO", "MOZ", "ZMB", "ZWE", "MUS", "TZA"],
            (1995, 1999),
            (2010, 2019),
        )
        if primary is None:
            return {"error": "missing South Africa trade-openness window data"}
        delta = primary["delta_pp"]
        return {
            "shape": "registered_zaf_sadc_window_gate",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "ZAF",
            "primary_delta": primary,
            "peer_deltas": peers,
            "peer_mean_delta_pp": _mean_delta(peers),
            "support_gate_delta_between_minus5_and_20pp": bool(-5.0 <= delta <= 20.0),
            "refute_gate_delta_gt_20pp": bool(delta > 20.0),
        }

    if hid == "trade_lib_chile_bilateral_fta_cascade":
        primary = _window_delta(trade, "CHL", (1985, 1994), (2010, 2019))
        peers = _comparator_window_deltas(trade, ["ARG", "BRA", "COL", "PER", "MEX"], (1985, 1994), (2010, 2019))
        if primary is None or not peers:
            return {"error": "missing Chile or comparator trade-openness window data"}
        peer_mean = _mean_delta(peers)
        diff_change = float(primary["delta_pp"] - peer_mean)
        return {
            "shape": "registered_chile_fta_differential_gate",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "CHL",
            "primary_delta": primary,
            "peer_deltas": peers,
            "peer_mean_delta_pp": peer_mean,
            "differential_change_pp": diff_change,
            "support_gate_chl_delta_ge_15pp": bool(primary["delta_pp"] >= 15.0),
            "support_gate_differential_ge_10pp": bool(diff_change >= 10.0),
            "refute_gate_differential_not_increased": bool(diff_change <= 0.0),
        }

    if hid == "trade_lib_mexico_eu_fta_2000":
        exclude = {"ARG": {2003}}
        primary = _window_delta(trade, "MEX", (1995, 1999), (2003, 2007))
        peers = _comparator_window_deltas(
            trade,
            ["BRA", "ARG", "CHL", "COL"],
            (1995, 1999),
            (2003, 2007),
            exclude_by_country=exclude,
        )
        if primary is None or not peers:
            return {"error": "missing Mexico or comparator trade-openness window data"}
        peer_mean = _mean_delta(peers)
        diff = float(primary["delta_pp"] - peer_mean)
        return {
            "shape": "registered_mexico_eu_fta_differential_gate",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "MEX",
            "primary_delta": primary,
            "peer_deltas": peers,
            "peer_mean_delta_pp": peer_mean,
            "differential_change_pp": diff,
            "support_gate_differential_ge_2pp": bool(diff >= 2.0),
            "refute_gate_differential_negative": bool(diff < 0.0),
        }

    if hid == "trade_lib_colombia_us_fta_2012":
        primary = _window_delta(trade, "COL", (2002, 2011), (2012, 2019))
        peers = _comparator_window_deltas(trade, ["PER", "ECU", "CHL", "MEX"], (2002, 2011), (2012, 2019))
        if primary is None or not peers:
            return {"error": "missing Colombia or comparator trade-openness window data"}
        peer_mean = _mean_delta(peers)
        diff = float(primary["delta_pp"] - peer_mean)
        return {
            "shape": "registered_colombia_us_fta_null_gate",
            "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
            "publisher": trade_pub,
            "country": "COL",
            "primary_delta": primary,
            "peer_deltas": peers,
            "peer_mean_delta_pp": peer_mean,
            "differential_change_pp": diff,
            "support_gate_abs_differential_le_3pp": bool(abs(diff) <= 3.0),
            "refute_gate_outperformance_gt_5pp": bool(diff > 5.0),
        }

    if hid == "trade_lib_argentina_mercosur_industrial_effect":
        if manuf_loaded is None:
            return {"error": "missing WDI manufacturing share series NV.IND.MANF.ZS"}
        manuf, manuf_pub = manuf_loaded
        peers = ["BRA", "CHL", "COL", "PER", "ECU", "BOL", "MEX"]
        primary = _endpoint_delta(manuf, "ARG", 1995, 2019)
        peer_rows = _comparator_endpoint_deltas(manuf, peers, 1995, 2019)
        if primary is None or not peer_rows:
            return {"error": "missing Argentina or comparator manufacturing-share endpoints"}
        peer_mean = _mean_delta(peer_rows)
        diff = float(primary["delta_pp"] - peer_mean)
        return {
            "shape": "registered_argentina_mercosur_mfg_share_gate",
            "source": "world_bank_wdi:NV.IND.MANF.ZS",
            "publisher": manuf_pub,
            "country": "ARG",
            "primary_delta": primary,
            "peer_deltas": peer_rows,
            "peer_mean_delta_pp": peer_mean,
            "differential_change_pp": diff,
            "support_gate_abs_differential_lt_2pp": bool(abs(diff) < 2.0),
            "partial_gate_arg_better_gt_2pp": bool(diff > 2.0),
            "refute_gate_arg_worse_lt_minus_2pp": bool(diff < -2.0),
        }

    return {"error": f"no registered trade-window evaluator for {hid}"}


def trade_window_threshold_verdict(hid: str, comp: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]

    if hid in {
        "trade_lib_india_1991_tariff_cut_export_response",
        "trade_lib_indonesia_1980s_1990s_unilateral",
    }:
        delta = comp["primary_delta"]["delta_pp"]
        if comp["support_gate_delta_ge_10pp"]:
            return "SUPPORTED", f"trade openness rose {delta:+.1f}pp, clearing the +10pp gate"
        if comp["refute_gate_delta_lt_5pp"]:
            return "REFUTED", f"trade openness rose only {delta:+.1f}pp, below the +5pp refutation gate"
        return "PARTIAL", f"trade openness rose {delta:+.1f}pp, between the +5pp and +10pp gates"

    if hid == "trade_lib_egypt_fta_cascade":
        rise = comp["rise_pre_to_peak_pp"]
        post_gap = comp["post_minus_peak_pp"]
        if comp["support_gate_rise_ge_5pp"] and comp["support_gate_post_close_or_below_peak_plus_2pp"]:
            return "SUPPORTED", f"openness rose {rise:+.1f}pp by 2007-2010, then post-2011 mean sat {post_gap:+.1f}pp below peak"
        if comp["refute_gate_peak_did_not_materialise"]:
            return "REFUTED", f"2007-2010 openness peak rose only {rise:+.1f}pp"
        return "PARTIAL", f"openness peak rose {rise:+.1f}pp, but the post-2011 stagnation gate did not clear"

    if hid == "trade_lib_south_africa_sadc_trade":
        delta = comp["primary_delta"]["delta_pp"]
        if comp["support_gate_delta_between_minus5_and_20pp"]:
            return "SUPPORTED", f"ZAF openness changed {delta:+.1f}pp, inside the registered [-5,+20]pp band"
        if comp["refute_gate_delta_gt_20pp"]:
            return "REFUTED", f"ZAF openness changed {delta:+.1f}pp, above the +20pp refutation gate"
        return "PARTIAL", f"ZAF openness changed {delta:+.1f}pp, outside the null/modest band on the downside"

    if hid == "trade_lib_chile_bilateral_fta_cascade":
        delta = comp["primary_delta"]["delta_pp"]
        diff = comp["differential_change_pp"]
        if comp["support_gate_chl_delta_ge_15pp"] and comp["support_gate_differential_ge_10pp"]:
            return "SUPPORTED", f"CHL openness rose {delta:+.1f}pp and differential increased {diff:+.1f}pp"
        if comp["refute_gate_differential_not_increased"]:
            return "REFUTED", f"CHL openness rose {delta:+.1f}pp but comparator differential moved {diff:+.1f}pp"
        return "PARTIAL", f"CHL openness rose {delta:+.1f}pp with differential change {diff:+.1f}pp"

    if hid == "trade_lib_mexico_eu_fta_2000":
        diff = comp["differential_change_pp"]
        if comp["support_gate_differential_ge_2pp"]:
            return "SUPPORTED", f"MEX openness change beat comparators by {diff:+.1f}pp"
        if comp["refute_gate_differential_negative"]:
            return "REFUTED", f"MEX openness change lagged comparators by {abs(diff):.1f}pp"
        return "PARTIAL", f"MEX openness change beat comparators by only {diff:+.1f}pp"

    if hid == "trade_lib_colombia_us_fta_2012":
        diff = comp["differential_change_pp"]
        if comp["support_gate_abs_differential_le_3pp"]:
            return "SUPPORTED", f"COL openness change was within {diff:+.1f}pp of comparator change"
        if comp["refute_gate_outperformance_gt_5pp"]:
            return "REFUTED", f"COL openness outperformed comparators by {diff:+.1f}pp"
        return "PARTIAL", f"COL openness differential was {diff:+.1f}pp, outside the null band but not the refutation gate"

    if hid == "trade_lib_argentina_mercosur_industrial_effect":
        diff = comp["differential_change_pp"]
        if comp["support_gate_abs_differential_lt_2pp"]:
            return "SUPPORTED", f"ARG manufacturing-share change differed from comparators by only {diff:+.1f}pp"
        if comp["partial_gate_arg_better_gt_2pp"]:
            return "PARTIAL", f"ARG manufacturing-share change beat comparators by {diff:+.1f}pp"
        return "REFUTED", f"ARG manufacturing-share change lagged comparators by {abs(diff):.1f}pp"

    return "INCONCLUSIVE_DATA_PENDING", f"no registered trade-window verdict for {hid}"


def find_cut_year(spec: dict) -> int | None:
    """Try to infer a treatment / event year from claim or falsification text."""
    text = ((spec.get("claim") or "") + " " +
            (spec.get("falsification") or {}).get("test", ""))
    # Look for 4-digit years in the text.
    years = [int(m.group(0)) for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", text)]
    if not years:
        return None
    period = (spec.get("sample") or {}).get("period") or []
    if len(period) == 2:
        # Pick a year inside the sample period.
        years = [y for y in years if period[0] < y < period[1]]
    return years[0] if years else None


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def descriptive_verdict(comp: dict, claim_dir: str, threshold: dict) -> tuple[str, str]:
    if "error" in comp:
        return "INCONCLUSIVE_DATA_PENDING", comp["error"]
    shape = comp["shape"]

    # Get a signed magnitude.
    if shape == "bilateral":
        log_diff = comp.get("log_diff_a_minus_b")
        ratio = comp.get("ratio_a_to_b")
        if log_diff is None:
            return "INCONCLUSIVE_DATA_PENDING", "log-diff undefined"
        magnitude = log_diff
        ratio_check = abs(ratio) if ratio else None
    elif shape == "pre_post":
        log_diff = comp.get("log_delta")
        magnitude = log_diff if log_diff is not None else comp["delta"]
        ratio_check = None
    elif shape == "panel_summary":
        log_diff = comp.get("log_diff")
        magnitude = log_diff if log_diff is not None else 0
        ratio_check = comp.get("ratio")
    else:
        return "INCONCLUSIVE_DATA_PENDING", f"unknown shape {shape}"

    sign = "+" if magnitude >= 0 else "-"
    mag_str = f"|Δ_log|={abs(magnitude):.3g}"
    if ratio_check:
        mag_str += f", ratio={ratio_check:.3g}"

    # Check threshold.
    fold = threshold.get("fold")
    pct = threshold.get("percent")
    threshold_met = None
    threshold_str = ""
    if fold and ratio_check:
        threshold_met = abs(np.log(abs(ratio_check))) > np.log(fold) * 0.5  # half-claim threshold
        threshold_str = f"; threshold {fold}x, observed {ratio_check:.2g}x"
    elif pct and magnitude is not None:
        threshold_met = abs(magnitude) > pct / 100.0
        threshold_str = f"; threshold {pct}%, observed {abs(magnitude)*100:.1f}%"
    elif abs(magnitude) > 0.5:
        threshold_met = True  # no explicit threshold, but big effect
    elif abs(magnitude) > 0.1:
        threshold_met = None  # ambiguous
    else:
        threshold_met = False

    if claim_dir == "?":
        return ("PARTIAL",
                f"shape={shape}, {mag_str}{threshold_str}; claim direction ambiguous")
    if sign == claim_dir:
        if threshold_met is True:
            return ("SUPPORTED",
                    f"shape={shape}, sign matches claim {claim_dir}, {mag_str}{threshold_str}")
        if threshold_met is False:
            return ("PARTIAL",
                    f"shape={shape}, sign matches but magnitude below threshold; {mag_str}{threshold_str}")
        return ("PARTIAL",
                f"shape={shape}, sign matches; {mag_str}{threshold_str}; threshold not extracted")
    # Opposite sign: only REFUTED if magnitude is meaningful. Tiny effects
    # like ratio=0.986 (1.4% off) shouldn't count as REFUTED.
    if threshold_met is True or abs(magnitude) > 0.1:
        return ("REFUTED",
                f"shape={shape}, sign {sign} OPPOSITE claim {claim_dir}; {mag_str}{threshold_str}")
    return ("PARTIAL",
            f"shape={shape}, sign opposite claim {claim_dir} but magnitude tiny; {mag_str}{threshold_str}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_outputs(hid: str, spec: dict, status: dict, comp: dict,
                  threshold: dict, verdict: str, reason: str) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)

    diag = {
        "verdict": f"{verdict} — {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": hid,
        "template": "descriptive",
        "claim_direction_inferred": infer_claim_direction(spec),
        "threshold_extracted": threshold,
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "comparison": comp,
        "data_status": status,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/run_descriptive.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str))

    md = [
        f"# Result card — {hid}",
        "",
        f"**Verdict:** {verdict} — {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim','').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule','').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test','').strip()}",
        "",
        "## Comparison",
    ]
    if "error" in comp:
        md.append(f"- _Error:_ {comp['error']}")
    else:
        for k, v in comp.items():
            md.append(f"- **{k}:** {v}")

    if threshold:
        md.append(f"\n## Extracted threshold: {threshold}")

    md.append("")
    md.append("## Variables resolved")
    if status["variables_loaded"]:
        for v in status["variables_loaded"]:
            md.append(f"- `{v['source']}` → {v['name']} ({v['role']}, "
                      f"publisher={v['publisher']}, n={v['n_rows']})")
    if status["variables_missing"]:
        md.append("\n### Variables missing data")
        for v in status["variables_missing"]:
            md.append(f"- `{v['source']}` ({v['role']}, name={v['name']})")

    md.append("")
    md.append(f"_Generated by `scripts/run_descriptive.py` at "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    (out_dir / "result_card.md").write_text("\n".join(md))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def list_descriptive_specs() -> list[str]:
    derived = ROOT / "engine" / "runnability.derived.yaml"
    with derived.open() as f:
        d = yaml.safe_load(f)
    return [
        h["hypothesis_id"]
        for h in d["hypotheses"]
        if h["estimator_template"] == "descriptive"
    ]


def run_one(
    hid: str,
    force: bool = False,
    persist_preflight_inconclusive: bool = True,
) -> str:
    if not force and has_committed_verdict(hid):
        return f"  · {hid}: skipped (committed verdict already on disk)"
    found = load_spec(hid)
    if found is None:
        return f"  ✗ {hid}: spec not found"
    _, spec = found
    # Integrity gate: refuse to grade against a stub falsification rule.
    # The auto-grader's verdicts are only meaningful against a dispositive
    # pre-registered threshold; running against the generic boilerplate
    # ("…when this stub is promoted from draft") would attach a fake-clean
    # verdict to a non-promoted spec. See post-mortem (commit bba6f644).
    if is_stub_falsification_rule(spec):
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = (
            "falsification rule not sharpened — auto-grader refuses to "
            "grade against the generic stub boilerplate. Promote the spec "
            "(replace falsification.rule with a dispositive threshold AND "
            "document the sharpening in methodology_note) before running."
        )
        persisted = should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        )
        if persisted:
            write_outputs(
                hid,
                spec,
                {"variables_loaded": [], "variables_missing": []},
                {"error": reason},
                {},
                verdict,
                reason,
            )
        suffix = " (stub rule, refused to grade)"
        if not persisted:
            suffix += " [artifact skipped]"
        return f"  ⚠ {hid}: {verdict}{suffix}"

    panel, status = build_panel(spec)
    var_blocks = spec.get("variables") or {}
    outcome_items = var_blocks.get("outcome") or []
    if not outcome_items:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = "no outcome variable in spec"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, {}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"
    panel_filt = filter_sample(panel, spec)
    outcome_name = first_loaded_var(outcome_items, panel_filt)
    threshold = extract_threshold(
        (spec.get("claim") or "") + " " +
        (spec.get("falsification") or {}).get("test", "")
    )
    if hid in {"usd_issuer_solvency_no_default_post_1971", "us_dollar_issuer_solvency_record"}:
        comp = us_issuer_solvency_event_count_comparison(spec)
        verdict, reason = us_issuer_solvency_event_count_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if outcome_name is None:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        missing = [v["source"] for v in status["variables_missing"]
                   if v["role"] == "outcome"]
        reason = f"no outcome variable loaded; missing: {missing}"
        if should_persist_preflight_inconclusive(
            reason, persist_preflight_inconclusive
        ):
            write_outputs(hid, spec, status, {"error": reason}, {}, verdict, reason)
        return f"  ⚠ {hid}: {verdict}"

    sample = spec.get("sample") or {}
    countries = sample.get("countries") or []
    period = sample.get("period") or [None, None]

    # Choose comparison shape.
    if hid == "india_extra_aadhaar_upi_productivity":
        comp = india_jam_findex_comparison(panel_filt, outcome_name)
        verdict, reason = india_jam_findex_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid == "fiat_expansion_erodes_currency_purchasing_power_long_run":
        comp = fiat_hard_asset_comparison(spec)
        verdict, reason = fiat_hard_asset_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid in {
        "japan_public_debt_solvency_inflation_independence",
        "japan_sargent_wallace_refutation_1990_2024",
    }:
        is_sargent = hid == "japan_sargent_wallace_refutation_1990_2024"
        comp = japan_debt_threshold_comparison(spec, sargent_wallace=is_sargent)
        verdict, reason = japan_debt_threshold_verdict(comp, sargent_wallace=is_sargent)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid == "asia_bangladesh_apparel_growth_1985_2024":
        comp = bangladesh_apparel_threshold_comparison()
        verdict, reason = bangladesh_apparel_threshold_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid == "monetary_finance_zlb_no_inflation":
        comp = monetary_finance_cpi_threshold_comparison()
        verdict, reason = monetary_finance_cpi_threshold_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid == "central_bank_balance_sheet_cpi_decoupling_panel_2008_2020":
        comp = central_bank_decoupling_usa_coverage_comparison()
        verdict, reason = central_bank_decoupling_usa_coverage_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid == "financial_fed_reverse_repo_facility_usage_2021_2024":
        comp = fed_rrp_peak_decline_comparison()
        verdict, reason = fed_rrp_peak_decline_verdict(comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if hid in {
        "trade_lib_india_1991_tariff_cut_export_response",
        "trade_lib_indonesia_1980s_1990s_unilateral",
        "trade_lib_egypt_fta_cascade",
        "trade_lib_south_africa_sadc_trade",
        "trade_lib_chile_bilateral_fta_cascade",
        "trade_lib_mexico_eu_fta_2000",
        "trade_lib_colombia_us_fta_2012",
        "trade_lib_argentina_mercosur_industrial_effect",
    }:
        comp = trade_window_threshold_comparison(hid)
        verdict, reason = trade_window_threshold_verdict(hid, comp)
        write_outputs(hid, spec, status, comp, threshold, verdict, reason)
        icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·",
                "WEAKENED": "·", "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
        return f"  {icon} {hid}: {verdict} — {reason}"
    if len(countries) == 2:
        comp = bilateral_comparison(panel_filt, outcome_name, countries, period)
    elif len(countries) == 1:
        cut = find_cut_year(spec)
        if cut is None:
            cut = (period[0] + period[1]) // 2 if len(period) == 2 and all(period) else None
        if cut is None:
            verdict = "INCONCLUSIVE_DATA_PENDING"
            reason = "couldn't infer pre/post cut year"
            if should_persist_preflight_inconclusive(
                reason, persist_preflight_inconclusive
            ):
                write_outputs(
                    hid, spec, status, {"error": reason}, {}, verdict, reason
                )
            return f"  ⚠ {hid}: {verdict}"
        else:
            comp = pre_post_comparison(panel_filt, outcome_name, countries[0], cut, period)
    else:
        if not countries:
            verdict = "INCONCLUSIVE_DATA_PENDING"
            reason = "no countries in sample"
            if should_persist_preflight_inconclusive(
                reason, persist_preflight_inconclusive
            ):
                write_outputs(
                    hid, spec, status, {"error": reason}, {}, verdict, reason
                )
            return f"  ⚠ {hid}: {verdict}"
        else:
            # First country = treatment; rest = donor pool.
            comp = panel_summary(panel_filt, outcome_name, countries[0],
                                 countries[1:], period)

    claim_dir = infer_claim_direction(spec)
    verdict, reason = descriptive_verdict(comp, claim_dir, threshold)
    write_outputs(hid, spec, status, comp, threshold, verdict, reason)

    icon = {"SUPPORTED": "✓", "REFUTED": "✗", "PARTIAL": "·", "WEAKENED": "·",
            "INCONCLUSIVE_DATA_PENDING": "⚠"}.get(verdict, " ")
    return f"  {icon} {hid}: {verdict} — {reason}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing committed verdicts.")
    parser.add_argument(
        "--write-preflight-inconclusive",
        action="store_true",
        help="Persist obvious preflight INCONCLUSIVE artifacts during bulk runs.",
    )
    args = parser.parse_args()
    persist_preflight = args.write_preflight_inconclusive or not args.all
    if args.all:
        ids = list_descriptive_specs()
        counts: dict[str, int] = {}
        print(f"Running {len(ids)} descriptive specs…")
        for hid in ids:
            try:
                msg = (
                    run_one(
                        hid,
                        force=args.force,
                        persist_preflight_inconclusive=persist_preflight,
                    )
                )
                print(msg)
                bump_bulk_run_count(counts, msg)
            except Exception as exc:
                print(f"  ✗ {hid}: runner crashed — {exc}")
                counts["crashed"] = counts.get("crashed", 0) + 1
                traceback.print_exc()
        print_bulk_run_summary("descriptive", counts)
        return 0
    if not args.hypothesis_id:
        parser.error("Pass <hypothesis_id> or --all.")
    print(
        run_one(
            args.hypothesis_id,
            force=args.force,
            persist_preflight_inconclusive=persist_preflight,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
