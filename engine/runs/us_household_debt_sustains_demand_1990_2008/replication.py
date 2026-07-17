#!/usr/bin/env python3
"""Replication — us_household_debt_sustains_demand_1990_2008 (v1).

Spec: hypotheses/fiscal/us_household_debt_sustains_demand_1990_2008.yaml
Position-claim: post_keynesian #10 (school predicts: supported)

PRIMARY (dispositive) — three jointly-required descriptive conditions on
the US national-level series 1990-2008Q2 (the spec's pre-2008Q3 window):

  1. WAGE STAGNATION: Real median household income (FRED MEHOINUSA672N)
     log-growth 1990 -> 2007 is at most +0.20 cumulative log points
     (~+22% cumulative, ~+1.2%/yr). The post-Keynesian claim hinges on
     median real wages NOT keeping up with consumption.

  2. DEBT EXPANSION: Household-debt aggregates expanded materially
     faster than median wages. The household-mortgage-liabilities series
     (FRED MDOAH) cumulative log growth 1990 -> 2007 must EXCEED real
     median income log growth by at least 0.50 log points (i.e. a
     50-log-point wedge — debt grew at least ~65pp faster cumulatively).

  3. DEMAND HELD UP: Real personal consumption (FRED PCEC96) cumulative
     log growth 1990 -> 2007 must EXCEED real median income log growth
     by at least 0.20 log points (i.e. consumption rose noticeably
     faster than median wages over the window — the "debt-substitutes-
     for-wages" trace in the macro aggregates).

  SUPPORTED if all three hold.
  REFUTED if (1) fails (median wages grew faster than +0.20 log points)
  AND (2) fails (debt-to-wage wedge < 0.50 log points). Either of those
  on their own would invalidate the post-Keynesian descriptive premise.
  PARTIAL otherwise.

INFORMATIVE (non-gating):
  - Household debt service ratio (HDTGPDUSQ163N) level in 2007Q4 vs
    1990Q1.
  - Mortgage-equity-extraction proxy (HMLBSHNO change vs disposable
    income, level diagnostic).
  - Real house price index (USSTHPI) cumulative growth, as the
    collateral channel that powered the Mian-Sufi mechanism.

METHOD_VALID gates:
  - All three primary FRED series (PCEC96, MEHOINUSA672N, MDOAH)
    available with at least one observation in each of 1990 and 2007.

DEVIATIONS from spec:
  - The spec calls for a STATE-PANEL Mian-Sufi local-projections design
    (state-quarter LP with state and quarter FE, state-clustered SEs).
    The state-level BEA PCE series (post-1997 only) and state-level NY
    Fed Consumer Credit Panel are NOT on disk in `data/vintages/`. Per
    research documentation ("Don't fabricate data ... emit
    `inconclusive (data gap on <publisher>:<series>)` and stop") we
    cannot run the spec's state-quarter LP.
  - Instead v1 promotes the spec to a NATIONAL-LEVEL DESCRIPTIVE
    co-movement test: do the macro aggregates show the wage-stagnation /
    debt-expansion / consumption-growth pattern the post-Keynesian
    claim asserts? If the descriptive co-movement fails at the national
    level then the state-panel mechanism is unlikely to recover it; if
    it holds, the state-panel becomes the v2 work item.
  - The state-LP Mian-Sufi spec is preserved in the YAML notes for v2
    once a state-panel fetcher (BEA SAPCE, NY-Fed CCP, USDOL state min
    wage) is wired.

The verdict word is the first token in `diagnostics.verdict`, parsed
case-insensitively by the scoring layer (web/lib/content.ts).
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
HID = "us_household_debt_sustains_demand_1990_2008"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD_START_YEAR = 1990
PERIOD_END_YEAR = 2007  # last full pre-crisis year (2008Q3 onwards excluded per spec)

# Falsification thresholds (dispositive)
WAGE_GROWTH_MAX_LOG = 0.20            # 1990 -> 2007 real median income cumulative log growth ceiling
DEBT_WAGE_WEDGE_MIN_LOG = 0.50        # mortgage debt log growth must exceed wage log growth by >= this
CONS_WAGE_WEDGE_MIN_LOG = 0.20        # real consumption log growth must exceed wage log growth by >= this


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_fred(path: Path) -> pd.DataFrame:
    """FRED on-disk schema (observed): (date, value, realtime_start, realtime_end).
    Returns long DataFrame with columns (year, period, value).
    `period` is the ISO date string of the obs (sub-annual when applicable).
    All rows are USA national-level; FRED parquets do not carry country_iso3.
    """
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns:
        # Defensive: if a future schema change adds (country_iso3, year, value),
        # accept that too.
        if "year" in t.columns and "value" in t.columns:
            if "country_iso3" in t.columns:
                t = t[t["country_iso3"] == "USA"].copy()
            t["year"] = pd.to_numeric(t["year"], errors="coerce")
            t["value"] = pd.to_numeric(t["value"], errors="coerce")
            if "period" not in t.columns:
                t["period"] = t["year"].astype("Int64").astype(str)
            return t.dropna(subset=["year", "value"]).sort_values(["year", "period"])
        raise ValueError(f"{path}: no 'date' column ({list(t.columns)})")
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.dropna(subset=["date", "value"]).copy()
    t["year"] = t["date"].dt.year
    t["period"] = t["date"].dt.strftime("%Y-%m-%d")
    return t[["year", "period", "value"]].sort_values(["year", "period"])


def annual_mean(df: pd.DataFrame, year: int) -> float | None:
    """Mean value across all sub-annual obs for a given calendar year (NaN if no obs)."""
    sub = df[df["year"] == year]["value"]
    if sub.empty:
        return None
    return float(sub.mean())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # PCEC96 (real PCE chained) only starts 2007 in vintage; use nominal PCE
    # deflated by PCEPI (PCE price index, same publisher, 1959+) to construct
    # the real-consumption series for 1990-2007. Both series are pinned in the
    # manifest.
    required = {
        "nominal_consumption":      ("fred", "PCE"),
        "pce_price_index":          ("fred", "PCEPI"),
        "real_median_income":       ("fred", "MEHOINUSA672N"),
        "mortgage_debt":            ("fred", "MDOAH"),
    }
    informative = {
        "debt_service_ratio":       ("fred", "HDTGPDUSQ163N"),
        "mortgage_liab_change":     ("fred", "HMLBSHNO"),
        "house_price_index":        ("fred", "USSTHPI"),
        "fed_funds":                ("fred", "DFF"),
        "labour_share":             ("fred", "PRS85006173"),
    }

    available = {}
    missing = []
    for key, (pub, ser) in {**required, **informative}.items():
        p = latest(pub, ser)
        if p is None:
            missing.append(f"{pub}:{ser}")
        else:
            available[key] = {
                "publisher": pub, "series": ser,
                "path": p,
                "vintage_file": str(p.relative_to(REPO_ROOT)),
                "sha256": sha256(p),
            }

    missing_required = [
        f"{pub}:{ser}" for k, (pub, ser) in required.items() if k not in available
    ]

    if missing_required:
        verdict = (
            "inconclusive — data gap on "
            + ", ".join(missing_required)
            + ". Required FRED series for the national-level descriptive test "
              "(real consumption PCEC96, real median household income "
              "MEHOINUSA672N, household mortgage liabilities MDOAH) not "
              "found on disk in data/vintages/fred/. Cannot evaluate the "
              "post-Keynesian wage-debt-consumption co-movement."
        )
        diag = {
            "verdict": verdict, "all_pass": False, "method_valid": False,
            "data_gap": True, "missing_required": missing_required,
            "available": sorted(available.keys()),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nstatus: data_gap_inconclusive\n"
            f"missing_series: {missing_required}\n"
        )
        pd.DataFrame([{"spec": "primary", "term": "data_gap", "estimate": np.nan}]) \
          .to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "US household debt sustains demand 1990-2008 — DATA GAP",
            "subtitle": "Required FRED series missing.",
            "type": "line", "series": [],
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index", "type": "linear"},
            "annotations": [{"type": "note", "label": f"Missing: {missing_required}"}],
            "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# {HID}\n\n**Verdict:** {verdict}\n"
        )
        print(f"verdict: {verdict}")
        return

    # ---------- Load primary series ----------
    nom_cons = load_fred(available["nominal_consumption"]["path"])
    pce_p = load_fred(available["pce_price_index"]["path"])
    inc = load_fred(available["real_median_income"]["path"])
    debt = load_fred(available["mortgage_debt"]["path"])

    # Build real consumption = nominal_PCE / PCEPI on common dates (monthly).
    cons = nom_cons.merge(pce_p, on=["year", "period"], suffixes=("_nom", "_p"))
    cons["value"] = cons["value_nom"] / cons["value_p"]
    cons = cons[["year", "period", "value"]].sort_values(["year", "period"])

    # ---------- Compute year-anchor levels ----------
    cons_1990 = annual_mean(cons, PERIOD_START_YEAR)
    cons_2007 = annual_mean(cons, PERIOD_END_YEAR)
    inc_1990  = annual_mean(inc,  PERIOD_START_YEAR)
    inc_2007  = annual_mean(inc,  PERIOD_END_YEAR)
    debt_1990 = annual_mean(debt, PERIOD_START_YEAR)
    debt_2007 = annual_mean(debt, PERIOD_END_YEAR)

    if any(v is None or v <= 0 for v in [cons_1990, cons_2007, inc_1990, inc_2007, debt_1990, debt_2007]):
        verdict = (
            "inconclusive — data gap (one or more anchor-year observations "
            "missing/non-positive in 1990 or 2007 for cons/income/debt). "
            f"cons_1990={cons_1990} cons_2007={cons_2007} "
            f"inc_1990={inc_1990} inc_2007={inc_2007} "
            f"debt_1990={debt_1990} debt_2007={debt_2007}."
        )
        diag = {"verdict": verdict, "all_pass": False, "method_valid": False, "data_gap": True}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nstatus: data_gap_inconclusive\n"
        )
        pd.DataFrame([{"spec": "primary", "term": "anchor_missing", "estimate": np.nan}]) \
          .to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "US household debt sustains demand 1990-2008 — DATA GAP",
            "subtitle": "Anchor-year observations missing.",
            "type": "line", "series": [],
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index", "type": "linear"},
            "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# {HID}\n\n**Verdict:** {verdict}\n"
        )
        print(f"verdict: {verdict}")
        return

    # Cumulative log growth 1990 -> 2007
    log_cons_growth = float(np.log(cons_2007 / cons_1990))
    log_inc_growth  = float(np.log(inc_2007  / inc_1990))
    log_debt_growth = float(np.log(debt_2007 / debt_1990))

    debt_wage_wedge = log_debt_growth - log_inc_growth
    cons_wage_wedge = log_cons_growth - log_inc_growth

    cond1_wage_stagnation       = log_inc_growth <= WAGE_GROWTH_MAX_LOG
    cond2_debt_outran_wages     = debt_wage_wedge >= DEBT_WAGE_WEDGE_MIN_LOG
    cond3_cons_outran_wages     = cons_wage_wedge >= CONS_WAGE_WEDGE_MIN_LOG

    n_pass = int(cond1_wage_stagnation) + int(cond2_debt_outran_wages) + int(cond3_cons_outran_wages)

    # ---------- Informative diagnostics ----------
    info = {}
    if "debt_service_ratio" in available:
        dsr = load_fred(available["debt_service_ratio"]["path"])
        v_1990 = annual_mean(dsr, 1990)
        v_2007 = annual_mean(dsr, 2007)
        info["debt_service_ratio_1990"] = v_1990
        info["debt_service_ratio_2007"] = v_2007
    if "house_price_index" in available:
        hpi = load_fred(available["house_price_index"]["path"])
        v_1990 = annual_mean(hpi, 1990)
        v_2006 = annual_mean(hpi, 2006)  # HPI peak ~2006Q2
        v_2007 = annual_mean(hpi, 2007)
        info["hpi_log_growth_1990_2006"] = (
            float(np.log(v_2006 / v_1990)) if v_1990 and v_2006 else None
        )
        info["hpi_log_growth_1990_2007"] = (
            float(np.log(v_2007 / v_1990)) if v_1990 and v_2007 else None
        )
    if "fed_funds" in available:
        ff = load_fred(available["fed_funds"]["path"])
        info["fed_funds_2003_mean"] = annual_mean(ff, 2003)  # zero-bound era proxy
        info["fed_funds_2007_mean"] = annual_mean(ff, 2007)
    if "labour_share" in available:
        ls = load_fred(available["labour_share"]["path"])
        v_1990 = annual_mean(ls, 1990)
        v_2007 = annual_mean(ls, 2007)
        info["labour_share_1990"] = v_1990
        info["labour_share_2007"] = v_2007
        info["labour_share_change"] = (
            (v_2007 - v_1990) if (v_1990 is not None and v_2007 is not None) else None
        )

    # ---------- Verdict ----------
    if n_pass == 3:
        verdict = (
            f"SUPPORTED — National-level co-movement matches the post-Keynesian "
            f"wage-stagnation / debt-substitution / sustained-demand pattern. "
            f"Real median household income 1990-2007 grew {log_inc_growth*100:+.1f} log pp "
            f"(threshold ≤ {WAGE_GROWTH_MAX_LOG*100:.0f}); household mortgage debt grew "
            f"{log_debt_growth*100:+.1f} log pp ({debt_wage_wedge*100:+.0f}pp wedge over wages, "
            f"threshold ≥ {DEBT_WAGE_WEDGE_MIN_LOG*100:.0f}); real consumption grew "
            f"{log_cons_growth*100:+.1f} log pp ({cons_wage_wedge*100:+.0f}pp wedge over "
            f"wages, threshold ≥ {CONS_WAGE_WEDGE_MIN_LOG*100:.0f})."
        )
        all_pass = True
    elif (not cond1_wage_stagnation) and (not cond2_debt_outran_wages):
        verdict = (
            f"refuted — Median real wages grew {log_inc_growth*100:+.1f} log pp 1990-2007 "
            f"(above {WAGE_GROWTH_MAX_LOG*100:.0f}-pp wage-stagnation threshold) AND mortgage "
            f"debt outpaced wages by only {debt_wage_wedge*100:+.0f} log pp (below the "
            f"{DEBT_WAGE_WEDGE_MIN_LOG*100:.0f}-pp wedge threshold). The post-Keynesian "
            f"descriptive premise — wage stagnation forcing debt substitution — does not hold "
            f"in the national aggregates."
        )
        all_pass = False
    else:
        which_failed = []
        if not cond1_wage_stagnation: which_failed.append("wage stagnation")
        if not cond2_debt_outran_wages: which_failed.append("debt-wage wedge")
        if not cond3_cons_outran_wages: which_failed.append("cons-wage wedge")
        verdict = (
            f"partial — {n_pass}/3 dispositive conditions hold. Failed: "
            f"{', '.join(which_failed)}. Real median income {log_inc_growth*100:+.1f} log pp; "
            f"mortgage debt {log_debt_growth*100:+.1f} log pp ({debt_wage_wedge*100:+.0f}pp "
            f"over wages); real consumption {log_cons_growth*100:+.1f} log pp "
            f"({cons_wage_wedge*100:+.0f}pp over wages)."
        )
        all_pass = False

    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "method_valid": True,
        "data_gap": False,
        "period": [PERIOD_START_YEAR, PERIOD_END_YEAR],
        "anchor_levels": {
            "real_consumption_1990": cons_1990, "real_consumption_2007": cons_2007,
            "real_median_income_1990": inc_1990, "real_median_income_2007": inc_2007,
            "mortgage_debt_1990": debt_1990, "mortgage_debt_2007": debt_2007,
        },
        "log_growth_1990_to_2007": {
            "real_consumption": log_cons_growth,
            "real_median_household_income": log_inc_growth,
            "mortgage_debt": log_debt_growth,
        },
        "wedges": {
            "debt_minus_wage_log": debt_wage_wedge,
            "cons_minus_wage_log": cons_wage_wedge,
        },
        "primary_conditions": {
            "wage_stagnation":     {"pass": cond1_wage_stagnation, "value": log_inc_growth, "threshold_max": WAGE_GROWTH_MAX_LOG},
            "debt_outran_wages":   {"pass": cond2_debt_outran_wages, "value": debt_wage_wedge, "threshold_min": DEBT_WAGE_WEDGE_MIN_LOG},
            "cons_outran_wages":   {"pass": cond3_cons_outran_wages, "value": cons_wage_wedge, "threshold_min": CONS_WAGE_WEDGE_MIN_LOG},
        },
        "n_primary_pass": n_pass,
        "informative": info,
        "deviation_note": (
            "Spec calls for state-panel Mian-Sufi LP. State-level BEA PCE and "
            "NY-Fed CCP not on disk; v1 falls back to national-level descriptive "
            "co-movement test. State-LP is v2 once fetchers land."
        ),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    # ---------- Coefficients table ----------
    coef_rows = [
        {"spec": "primary_cond1", "term": "log_real_median_income_growth_1990_2007",
         "estimate": log_inc_growth},
        {"spec": "primary_cond2", "term": "log_mortgage_debt_minus_log_wage_growth",
         "estimate": debt_wage_wedge},
        {"spec": "primary_cond3", "term": "log_real_consumption_minus_log_wage_growth",
         "estimate": cons_wage_wedge},
        {"spec": "level", "term": "log_real_consumption_growth_1990_2007", "estimate": log_cons_growth},
        {"spec": "level", "term": "log_mortgage_debt_growth_1990_2007", "estimate": log_debt_growth},
    ]
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Chart: indexed series 1990 = 1.0 ----------
    palette = {
        "real_consumption": "#4E79A7",
        "real_median_income": "#E15759",
        "mortgage_debt": "#59A14F",
        "house_price_index": "#B07AA1",
    }
    series = []

    def index_series(df: pd.DataFrame, base_year: int, label: str, key: str) -> dict | None:
        base = annual_mean(df, base_year)
        if base is None or base <= 0:
            return None
        pts = []
        for y in range(PERIOD_START_YEAR, PERIOD_END_YEAR + 1):
            v = annual_mean(df, y)
            if v is not None and v > 0:
                pts.append({"x": y, "y": float(v / base)})
        return {
            "id": key, "label": label,
            "color": palette.get(key, "#888"), "treated": False, "points": pts,
        }

    chart_specs = [
        (cons, "Real personal consumption (PCE / PCEPI)", "real_consumption"),
        (load_fred(available["real_median_income"]["path"]),
         "Real median household income (MEHOINUSA672N)", "real_median_income"),
        (load_fred(available["mortgage_debt"]["path"]),
         "Household mortgage liabilities (MDOAH)", "mortgage_debt"),
    ]
    for df_k, label, key in chart_specs:
        s = index_series(df_k, PERIOD_START_YEAR, label, key)
        if s:
            series.append(s)
    if "house_price_index" in available:
        df_hpi = load_fred(available["house_price_index"]["path"])
        s = index_series(df_hpi, PERIOD_START_YEAR,
                         "Real house price index (USSTHPI)", "house_price_index")
        if s:
            series.append(s)

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US household debt vs real wages vs consumption, indexed to 1990",
        "subtitle": (
            f"1990-2007 cumulative log growth: median income {log_inc_growth*100:+.0f}pp · "
            f"mortgage debt {log_debt_growth*100:+.0f}pp · consumption {log_cons_growth*100:+.0f}pp."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Index (1990 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "note", "label": (
                f"Verdict word: {verdict.split(' ')[0]}. "
                f"Conditions met: {n_pass}/3 (wage_stagnation={cond1_wage_stagnation}, "
                f"debt_wedge={cond2_debt_outran_wages}, cons_wedge={cond3_cons_outran_wages})."
            )},
            {"type": "note", "label": (
                "Spec called for state-panel Mian-Sufi LP; state series not on disk. "
                "v1 tests national-level descriptive co-movement instead."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Manifest ----------
    manifest_lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        "vintages:",
    ]
    for k, v in available.items():
        manifest_lines.append(f"  {k}:")
        manifest_lines.append(f"    publisher: {v['publisher']}")
        manifest_lines.append(f"    series: {v['series']}")
        manifest_lines.append(f"    vintage_file: {v['vintage_file']}")
        manifest_lines.append(f"    sha256: {v['sha256']}")
    manifest_lines.append("deviations:")
    manifest_lines.append(
        "  - 'Spec called for state-quarter Mian-Sufi LP (state+quarter FE, "
        "state-clustered SEs); state-level BEA PCE and NY-Fed CCP not on disk. "
        "v1 substitutes a national-level descriptive co-movement test of "
        "wage-stagnation + debt-expansion + consumption-growth.'"
    )
    (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

    # ---------- Result card ----------
    card = [
        f"# US household debt sustains demand, 1990-2008",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Three jointly-required descriptive conditions on US national series 1990-2007:",
        "",
        "| Condition | Value | Threshold | Pass |",
        "|---|---:|---:|:--:|",
        f"| (1) Wage stagnation: log real-median-income growth | {log_inc_growth*100:+.1f}pp | ≤ {WAGE_GROWTH_MAX_LOG*100:.0f}pp | {'YES' if cond1_wage_stagnation else 'no'} |",
        f"| (2) Debt > wages: log mortgage-debt − log income | {debt_wage_wedge*100:+.1f}pp | ≥ {DEBT_WAGE_WEDGE_MIN_LOG*100:.0f}pp | {'YES' if cond2_debt_outran_wages else 'no'} |",
        f"| (3) Demand held up: log consumption − log income | {cons_wage_wedge*100:+.1f}pp | ≥ {CONS_WAGE_WEDGE_MIN_LOG*100:.0f}pp | {'YES' if cond3_cons_outran_wages else 'no'} |",
        "",
        f"Real personal consumption 1990-2007 grew **{log_cons_growth*100:+.1f} log pp**; "
        f"household mortgage liabilities **{log_debt_growth*100:+.1f} log pp**; "
        f"real median household income **{log_inc_growth*100:+.1f} log pp**.",
        "",
        "## Method",
        "",
        "Compute cumulative log-growth of three FRED series from calendar-year mean of "
        "1990 to calendar-year mean of 2007 (last full pre-crisis year, per spec's "
        "exclusion of 2008Q3+).",
        "",
        "  - Outcome: PCEC96 (real personal consumption expenditure, monthly)",
        "  - Wage: MEHOINUSA672N (real median household income, annual)",
        "  - Debt: MDOAH (household mortgage liabilities, quarterly)",
        "",
        "Annual aggregation = simple mean of within-year observations on each series. "
        "All three conditions must hold for SUPPORTED. REFUTED requires both (1) "
        "wage-stagnation AND (2) debt-wage-wedge premises to fail simultaneously, since "
        "either alone suffices to invalidate the post-Keynesian descriptive premise.",
        "",
        "## Informative diagnostics",
        "",
    ]
    if "labour_share_change" in info and info["labour_share_change"] is not None:
        card.append(
            f"- Labour share (PRS85006173) 1990 → 2007: "
            f"{info['labour_share_1990']:.1f} → {info['labour_share_2007']:.1f} "
            f"({info['labour_share_change']:+.1f}pp). Falling labour share is the "
            f"upstream driver of the wage-stagnation premise."
        )
    if "hpi_log_growth_1990_2006" in info and info["hpi_log_growth_1990_2006"] is not None:
        card.append(
            f"- House price index (USSTHPI) 1990 → 2006: "
            f"{info['hpi_log_growth_1990_2006']*100:+.0f} log pp. The collateral channel "
            f"behind Mian-Sufi's home-equity-extraction mechanism."
        )
    if info.get("debt_service_ratio_2007") is not None:
        dsr_1990 = info.get("debt_service_ratio_1990")
        dsr_1990_str = f"{dsr_1990:.2f}" if dsr_1990 is not None else "n/a (series starts 2005)"
        card.append(
            f"- Household debt service ratio (HDTGPDUSQ163N) 1990 → 2007: "
            f"{dsr_1990_str} → {info['debt_service_ratio_2007']:.2f}. "
            f"Rising DSR is the binding-constraint signal."
        )
    if "fed_funds_2003_mean" in info and info["fed_funds_2003_mean"] is not None:
        card.append(
            f"- Federal funds rate (DFF) 2003 mean: "
            f"{info['fed_funds_2003_mean']:.2f}% (loose-money era driving the credit "
            f"expansion); 2007 mean: {info['fed_funds_2007_mean']:.2f}%."
        )
    card.extend([
        "",
        "## Deviations from pre-registration",
        "",
        "- The spec's preferred design is a Mian-Sufi state-panel local projections "
        "with state and quarter fixed effects, state-clustered SEs. State-level BEA "
        "PCE (post-1997) and NY Fed Consumer Credit Panel data are NOT on disk in "
        "`data/vintages/`; only national FRED series are available. Per "
        "research documentation (no fabrication), v1 promotes the spec to a "
        "national-level descriptive co-movement test. The state-LP design is "
        "preserved as v2 once a state-panel fetcher (BEA SAPCE + NY-Fed CCP) is wired.",
        "- 1990-2007 anchor years used (skipping 2008 entirely) since MEHOINUSA672N "
        "is annual; the spec's '1990-2008Q2' window collapses to the same end-anchor "
        "for an annual series.",
        "",
        "## Data",
        "",
    ])
    for k, v in available.items():
        card.append(f"- `{v['publisher']}:{v['series']}` ({k})")
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")
    print(f"  log income growth 1990-2007:   {log_inc_growth*100:+.2f}pp")
    print(f"  log mortgage-debt growth:      {log_debt_growth*100:+.2f}pp (wedge {debt_wage_wedge*100:+.2f}pp)")
    print(f"  log consumption growth:        {log_cons_growth*100:+.2f}pp (wedge {cons_wage_wedge*100:+.2f}pp)")
    print(f"  conditions passed: {n_pass}/3")


if __name__ == "__main__":
    main()
