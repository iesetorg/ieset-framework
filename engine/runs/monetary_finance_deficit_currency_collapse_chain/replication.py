#!/usr/bin/env python3
"""Replication — Monetary finance -> currency-collapse causal chain (6 EM cases).

Spec: hypotheses/monetary/monetary_finance_deficit_currency_collapse_chain.yaml v1

Six EM cases with country-specific monetary-finance "intensification" events:
  ARG: 2019 (Fernandez return; BCRA adelantos transitorios surge)
  TUR: 2021 (Erdogan unorthodox-rate-cut campaign begins)
  VEN: 2013 (post-Chavez; BCV direct PDVSA + government transfers escalate)
  LKA: 2020 (MMT-style CBSL gilt purchases; pandemic + Rajapaksa tax cuts)
  GHA: 2020 (BoG advances escalate during pandemic + 2022 IMF programme)
  EGY: 2022 (CBE balance-sheet expansion + parallel-FX gap re-opens)

CHAIN:
  FIRST-ORDER (acknowledged): monetary finance is delivered. Treated as
    confirmed by case-construction (these are documented MF episodes).
  SECOND-ORDER (testable): inflation accelerates and real purchasing power
    deteriorates. Tested via IMF PCPIPCH year-on-year inflation rate vs
    pre-treatment 5-year mean.
  THIRD-ORDER (testable, partial): currency collapses (PA.NUS.PRVT.PP PPP
    private conversion factor depreciates rapidly) — proxy for parallel-FX
    gap and dollarisation pressure since most parallel-FX series are not
    on disk.

PRIMARY DISPOSITIVE TEST (executable, threshold-bound):
  Per-case: post-event-3yr-mean inflation >= 2x pre-event-5yr-mean inflation
            AND post-event-3yr currency depreciation >= 30% (cumulative LCU/USD
            PPP factor change).
  Chain holds if: SECOND-ORDER inflation acceleration confirmed in >=5/6
                  cases AND THIRD-ORDER currency depreciation confirmed in
                  >=4/6 cases.

VERDICT MAPPING:
  SUPPORTED if both the 5/6 inflation gate AND the 4/6 currency gate hold.
  partial if one gate holds.
  refuted if neither gate holds (would mean MF is not chained to either
    inflation or currency response in EM cases — a strong refutation).
  inconclusive if data gap on inflation in >=3 cases.

Outputs: diagnostics.json, chart_data.json, coefficients.parquet,
result_card.md, manifest.yaml.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "monetary_finance_deficit_currency_collapse_chain"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Country -> monetary-finance intensification event year (per spec.scope.treatment_tags)
EVENTS = {
    "ARG": 2019,  # argentina_fernandez_2019
    "TUR": 2021,  # turkey_erdogan_unorthodox_2021
    "VEN": 2013,  # venezuela_chavismo_monetary_finance (post-Chavez)
    "LKA": 2020,  # sri_lanka_2022_crisis (MF intensified 2020)
    "GHA": 2020,  # ghana_2022_crisis (BoG advances escalated 2020)
    "EGY": 2022,  # egypt_2022_crisis
}

PRE_WINDOW_YEARS = 5      # mean inflation over T-5..T-1
POST_WINDOW_YEARS = 3     # mean inflation over T+1..T+3
INFLATION_MULTIPLIER_THRESHOLD = 2.0      # post must be >= 2x pre
CURRENCY_DEPRECIATION_THRESHOLD = 0.30    # cumulative LCU/USD up >=30%
INFLATION_GATE_N = 5      # 5/6 cases for chain SUPPORTED on 2nd-order
CURRENCY_GATE_N = 4       # 4/6 cases for chain SUPPORTED on 3rd-order


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_long(path: Path) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value) rows."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator_id", "unit"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Inflation: IMF PCPIPCH (annual % change CPI). Best EM coverage.
    cpi_path = latest("imf", "PCPIPCH")
    # Currency depreciation proxy: WDI PA.NUS.PRVT.PP (PPP private conversion
    # factor, LCU per international $; rises as the LCU depreciates).
    fx_path = latest("world_bank_wdi", "PA.NUS.PRVT.PP")
    # Government debt/GDP (informative context for fiscal pressure)
    debt_path = latest("imf", "GGXWDG_NGDP")
    # Government primary balance/GDP (informative)
    bal_path = latest("imf", "GGXCNL_NGDP")

    manifest = {
        "cpi_inflation": {
            "publisher": "imf",
            "series": "PCPIPCH",
            "vintage_file": str(cpi_path.relative_to(REPO_ROOT)),
            "sha256": sha256(cpi_path),
        },
        "ppp_conversion_factor": {
            "publisher": "world_bank_wdi",
            "series": "PA.NUS.PRVT.PP",
            "vintage_file": str(fx_path.relative_to(REPO_ROOT)),
            "sha256": sha256(fx_path),
        },
        "gov_debt_gdp": {
            "publisher": "imf",
            "series": "GGXWDG_NGDP",
            "vintage_file": str(debt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(debt_path),
        },
        "gov_primary_balance_gdp": {
            "publisher": "imf",
            "series": "GGXCNL_NGDP",
            "vintage_file": str(bal_path.relative_to(REPO_ROOT)),
            "sha256": sha256(bal_path),
        },
    }

    cpi = load_long(cpi_path)
    fx = load_long(fx_path)
    debt = load_long(debt_path)
    bal = load_long(bal_path)

    # ---------- Per-country chain test ----------
    rows = []
    coef_rows = []
    for country, T in EVENTS.items():
        c_cpi = cpi[cpi["country_iso3"] == country].set_index("year")["value"]
        c_fx = fx[fx["country_iso3"] == country].set_index("year")["value"]

        pre_years = list(range(T - PRE_WINDOW_YEARS, T))
        post_years = list(range(T + 1, T + 1 + POST_WINDOW_YEARS))

        pre_cpi = c_cpi.reindex(pre_years).dropna()
        post_cpi = c_cpi.reindex(post_years).dropna()
        pre_fx_y = T - 1
        post_fx_y = T + POST_WINDOW_YEARS

        pre_inflation = float(pre_cpi.mean()) if len(pre_cpi) else np.nan
        post_inflation = float(post_cpi.mean()) if len(post_cpi) else np.nan
        inflation_multiple = (
            (post_inflation / pre_inflation)
            if (pre_inflation and pre_inflation > 0 and not np.isnan(post_inflation))
            else np.nan
        )

        # Currency: LCU-per-PPP$ ratio at T+3 vs T-1
        fx_pre = float(c_fx.get(pre_fx_y, np.nan))
        fx_post = float(c_fx.get(post_fx_y, np.nan))
        if not np.isnan(fx_pre) and not np.isnan(fx_post) and fx_pre > 0:
            currency_change_pct = (fx_post / fx_pre) - 1.0
        else:
            currency_change_pct = np.nan

        inflation_gate_pass = (
            (not np.isnan(inflation_multiple))
            and (inflation_multiple >= INFLATION_MULTIPLIER_THRESHOLD)
        )
        currency_gate_pass = (
            (not np.isnan(currency_change_pct))
            and (currency_change_pct >= CURRENCY_DEPRECIATION_THRESHOLD)
        )

        rows.append({
            "country": country,
            "event_year": T,
            "pre_inflation_mean": pre_inflation,
            "post_inflation_mean": post_inflation,
            "inflation_multiple": inflation_multiple,
            "inflation_gate_pass": inflation_gate_pass,
            "fx_pre_value": fx_pre,
            "fx_post_value": fx_post,
            "currency_change_pct": currency_change_pct,
            "currency_gate_pass": currency_gate_pass,
            "n_pre_cpi": int(len(pre_cpi)),
            "n_post_cpi": int(len(post_cpi)),
        })

        coef_rows.append(
            {"spec": "second_order", "country": country, "term": "pre_inflation_mean", "estimate": pre_inflation}
        )
        coef_rows.append(
            {"spec": "second_order", "country": country, "term": "post_inflation_mean", "estimate": post_inflation}
        )
        coef_rows.append(
            {"spec": "second_order", "country": country, "term": "inflation_multiple", "estimate": inflation_multiple}
        )
        coef_rows.append(
            {"spec": "third_order", "country": country, "term": "currency_change_pct", "estimate": currency_change_pct}
        )

    case_df = pd.DataFrame(rows)
    n_inflation_pass = int(case_df["inflation_gate_pass"].sum())
    n_currency_pass = int(case_df["currency_gate_pass"].sum())
    n_inflation_gap = int(case_df["inflation_multiple"].isna().sum())

    chain_2nd_order_holds = n_inflation_pass >= INFLATION_GATE_N
    chain_3rd_order_holds = n_currency_pass >= CURRENCY_GATE_N

    if n_inflation_gap >= 3:
        verdict = (
            f"inconclusive — Data gap on IMF:PCPIPCH for {n_inflation_gap}/6 cases prevents "
            f"dispositive inflation-acceleration test."
        )
    elif chain_2nd_order_holds and chain_3rd_order_holds:
        verdict = (
            f"SUPPORTED — Inflation accelerated >=2x in {n_inflation_pass}/6 cases "
            f"(threshold 5/6); cumulative LCU/USD depreciation >=30% in T-1..T+3 in "
            f"{n_currency_pass}/6 cases (threshold 4/6). Three-order MF chain confirmed."
        )
    elif chain_2nd_order_holds and not chain_3rd_order_holds:
        verdict = (
            f"partial — Inflation acceleration confirmed in {n_inflation_pass}/6 cases "
            f"(>=5/6 threshold met), but currency-depreciation third-order response "
            f"missed: {n_currency_pass}/6 (need 4/6). 2nd-order chain holds, 3rd-order weak."
        )
    elif (not chain_2nd_order_holds) and chain_3rd_order_holds:
        verdict = (
            f"partial — Currency depreciation confirmed in {n_currency_pass}/6 cases, but "
            f"inflation-acceleration second-order response missed: {n_inflation_pass}/6 "
            f"(need 5/6). 3rd-order holds, 2nd-order weak."
        )
    else:
        verdict = (
            f"refuted — Neither gate met: inflation accelerated >=2x in only "
            f"{n_inflation_pass}/6 cases (need 5/6); currency depreciated >=30% in only "
            f"{n_currency_pass}/6 cases (need 4/6). EM monetary-finance chain not detected."
        )

    diagnostics = {
        "verdict": verdict,
        "n_inflation_gate_pass": n_inflation_pass,
        "n_currency_gate_pass": n_currency_pass,
        "inflation_gate_threshold": INFLATION_GATE_N,
        "currency_gate_threshold": CURRENCY_GATE_N,
        "inflation_multiplier_threshold": INFLATION_MULTIPLIER_THRESHOLD,
        "currency_depreciation_threshold": CURRENCY_DEPRECIATION_THRESHOLD,
        "pre_window_years": PRE_WINDOW_YEARS,
        "post_window_years": POST_WINDOW_YEARS,
        "chain_2nd_order_holds": bool(chain_2nd_order_holds),
        "chain_3rd_order_holds": bool(chain_3rd_order_holds),
        "n_inflation_data_gap_cases": n_inflation_gap,
        "case_results": rows,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ---------- Chart: per-case pre/post inflation log-bar ----------
    palette = {
        "ARG": "#75AADB", "TUR": "#E30A17", "VEN": "#FCD116",
        "LKA": "#FFBE29", "GHA": "#CE1126", "EGY": "#000000",
    }
    series = []
    for r in rows:
        c = r["country"]
        pre = r["pre_inflation_mean"]
        post = r["post_inflation_mean"]
        if np.isnan(pre) or np.isnan(post):
            continue
        # x = relative year, y = inflation rate; one series per country
        # spans T-PRE..T+POST with NaN-skipping
        c_cpi = cpi[cpi["country_iso3"] == c].set_index("year")["value"]
        T = r["event_year"]
        pts = []
        for y in range(T - PRE_WINDOW_YEARS, T + 1 + POST_WINDOW_YEARS):
            if y in c_cpi.index:
                pts.append({"x": int(y - T), "y": float(c_cpi[y])})
        if pts:
            series.append({
                "id": c,
                "label": f"{c} (event {T})",
                "color": palette.get(c, "#888888"),
                "treated": True,
                "points": pts,
            })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Inflation around monetary-finance intensification events (six EM cases)",
        "subtitle": (
            f"Inflation accelerated >=2x in {n_inflation_pass}/6 cases (need 5/6); "
            f"currency depreciated >=30% in {n_currency_pass}/6 cases (need 4/6)."
        ),
        "type": "line",
        "x_axis": {"label": "Years from MF intensification (T=0)", "type": "linear"},
        "y_axis": {"label": "CPI inflation, % YoY", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    "Pre-window: T-5..T-1 mean. Post-window: T+1..T+3 mean. "
                    "Gate: post-mean >= 2x pre-mean inflation per case."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + "".join(
            f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
            f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
            for k, v in manifest.items()
        )
    )

    # ---------- Result card ----------
    card = [
        f"# Monetary-finance -> currency-collapse chain (six EM cases)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Per-case 2nd-order test: post-event 3-yr mean inflation >= 2x pre-event "
        f"5-yr mean. Pass: **{n_inflation_pass}/6** (gate: >=5/6).",
        f"- Per-case 3rd-order test: cumulative LCU/PPP$ depreciation >=30% over "
        f"T-1..T+3. Pass: **{n_currency_pass}/6** (gate: >=4/6).",
        "",
        "### Per-case detail",
        "",
        "| Country | Event | Pre-infl | Post-infl | Mult | FX chg% | Infl pass | FX pass |",
        "|---------|-------|----------|-----------|------|---------|-----------|---------|",
    ]
    for r in rows:
        card.append(
            f"| {r['country']} | {r['event_year']} | "
            f"{r['pre_inflation_mean']:.1f} | "
            f"{r['post_inflation_mean']:.1f} | "
            f"{r['inflation_multiple']:.2f} | "
            f"{(r['currency_change_pct']*100 if not np.isnan(r['currency_change_pct']) else float('nan')):.0f}% | "
            f"{'Y' if r['inflation_gate_pass'] else 'N'} | "
            f"{'Y' if r['currency_gate_pass'] else 'N'} |"
        )
    card += [
        "",
        "## Method",
        "",
        "Six EM cases of documented monetary-finance intensification, each with a",
        "country-specific event year T (ARG 2019, TUR 2021, VEN 2013, LKA 2020,",
        "GHA 2020, EGY 2022). For each case:",
        "",
        "1. Compute mean CPI inflation (IMF PCPIPCH) in pre-window T-5..T-1 and",
        "   post-window T+1..T+3. The ratio is the 'inflation multiple'. Gate:",
        "   ratio >= 2.0 -> 2nd-order chain confirmed for that case.",
        "2. Compute LCU/PPP$ ratio (WDI PA.NUS.PRVT.PP) at T-1 and T+3. The",
        "   change is the cumulative depreciation. Gate: change >= +30% -> 3rd-",
        "   order currency-collapse channel confirmed for that case.",
        "",
        "Chain SUPPORTED if 2nd-order gate passes in >=5/6 cases AND 3rd-order",
        "gate passes in >=4/6. Asymmetric thresholds reflect the spec's",
        "expectation that inflation transmission is near-mechanical while",
        "currency response can be muted in cases with capital controls or",
        "managed-float regimes (where parallel-FX would be the cleaner test,",
        "but parallel-FX series for ARG/TUR/EGY/LKA/GHA are not on disk in",
        "this repo's vintage tree — only Venezuela has dolartoday).",
        "",
        "## Data",
        "",
        f"- imf:PCPIPCH (CPI inflation, annual % change)",
        f"- world_bank_wdi:PA.NUS.PRVT.PP (private-sector PPP conversion factor)",
        f"- imf:GGXWDG_NGDP (gov debt/GDP, context)",
        f"- imf:GGXCNL_NGDP (gov primary balance/GDP, context)",
        "",
        "## Caveats",
        "",
        "- Real-wage erosion (spec 2nd-order outcome) is not separately tested:",
        "  no harmonised real-wage series for the six cases is on disk. CPI",
        "  inflation acceleration is the primary 2nd-order signal here.",
        "- Dollarisation share of bank deposits, parallel-FX premia, capital-",
        "  control stringency, and emigration flows (spec 3rd-order outcomes)",
        "  are not separately tested: bcra/tcmb/cbsl/cbe vintage data not on",
        "  disk. PPP-currency depreciation is used as a single 3rd-order proxy.",
        "- VEN dolartoday parallel-rate is on disk and could supplement future",
        "  v2 work; for v1 a single PPP proxy keeps the cross-case test uniform.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
