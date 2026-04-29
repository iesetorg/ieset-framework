#!/usr/bin/env python3
"""Replication — Volcker disinflation output recovery (1979Q4 event study).

Spec: hypotheses/growth/volcker_disinflation_output_recovery.yaml v1
Steelman: hypotheses/steelman/volcker_disinflation_output_recovery.md

Tests the monetarist claim that Paul Volcker's October-1979 tightening
imposed a finite-cost disinflation: inflation re-anchored AND real GDP
returned to its pre-1979 trend by 1984.

PRIMARY (dispositive):
  A) CPI YoY inflation falls from its 1979-1980 peak (>= 10%) to a
     1983Q4 quarterly mean of <= 5.0%, AND the peak-to-1983Q4 drop is
     >= 5.0pp (Volcker disinflation magnitude).
  B) Real GDP (GDPC1) at 1984Q4 is within 2.0% of the linear log-time
     trend fit on 1972Q1-1979Q3 pre-event quarterly observations
     (output recovery to trend).

SUPPORTED iff both A and B.
REFUTED if peak-to-1983Q4 drop < 5pp OR 1984Q4 trend gap <= -5.0%.
PARTIAL otherwise.

INFORMATIVE: peak effective fed funds rate 1981 (treatment intensity);
inflation YoY trajectory; trough-quarter and recovery slope.

METHOD_VALID: needs CPIAUCSL + GDPC1 + FEDFUNDS for the 1972Q1-1984Q4
window. Missing series -> inconclusive (data gap).
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
HID = "volcker_disinflation_output_recovery"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Pre-trend window — Bretton Woods collapse onwards, stops just before
# the October 1979 Volcker tightening (so the trend includes the 1973
# and 1979-onset oil-shock growth drag, conservative for the recovery
# claim).
PRETREND_START = pd.Timestamp("1972-01-01")
PRETREND_END = pd.Timestamp("1979-09-30")

EVENT_DATE = pd.Timestamp("1979-10-01")  # Volcker FOMC tightening
INFL_TARGET_QUARTER = pd.Timestamp("1983-10-01")  # 1983Q4
RECOVERY_QUARTER = pd.Timestamp("1984-10-01")     # 1984Q4

# Falsification thresholds (sharpened in spec promotion)
INFL_LEVEL_MAX_1983Q4 = 5.0           # %
INFL_DROP_MIN_PP = 5.0                # peak-to-1983Q4 drop, percentage points
RECOVERY_GAP_THRESHOLD = -0.020       # log-points (>= -2% to clear)
REFUTED_GAP_FLOOR = -0.050            # log-points (<= -5% to refute)


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


def load_fred_series(path: Path) -> pd.Series:
    """FRED parquet: native schema (date, value, realtime_start, realtime_end).
    Returns a date-indexed numeric Series, sorted, deduped (keep latest
    realtime_end where a date has multiple vintages).
    """
    t = pq.read_table(path).to_pandas()
    cols = set(t.columns)
    if "date" not in cols or "value" not in cols:
        raise ValueError(f"{path}: expected (date, value) columns; got {list(t.columns)}")
    t = t[["date", "value"] + (["realtime_end"] if "realtime_end" in cols else [])].copy()
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.dropna(subset=["date", "value"])
    if "realtime_end" in t.columns:
        t["realtime_end"] = pd.to_datetime(t["realtime_end"], errors="coerce")
        t = t.sort_values(["date", "realtime_end"]).drop_duplicates("date", keep="last")
    else:
        t = t.sort_values("date").drop_duplicates("date", keep="last")
    return t.set_index("date")["value"].sort_index()


def to_quarterly_mean(s: pd.Series) -> pd.Series:
    """Resample monthly/daily series to quarterly mean, indexed by quarter-start."""
    return s.resample("QS").mean()


def cpi_yoy_quarterly(cpi_monthly: pd.Series) -> pd.Series:
    """Compute YoY % change on monthly CPI, then aggregate to quarterly mean."""
    yoy = (cpi_monthly / cpi_monthly.shift(12) - 1.0) * 100.0
    return yoy.resample("QS").mean()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Vintage discovery
    available, missing = {}, []

    def take(pub, series, role):
        p = latest(pub, series)
        key = f"{pub}:{series}"
        if p is None:
            missing.append(f"{key} ({role})")
            return None
        available[key] = {
            "publisher": pub, "series": series, "role": role,
            "vintage_file": str(p.relative_to(REPO_ROOT)),
            "sha256": sha256(p),
        }
        return p

    p_cpi = take("fred", "CPIAUCSL", "us_headline_cpi_monthly")
    p_gdp = take("fred", "GDPC1", "us_real_gdp_quarterly")
    p_ffr = take("fred", "FEDFUNDS", "us_effective_fed_funds_monthly")

    if p_cpi is None or p_gdp is None or p_ffr is None:
        verdict = "inconclusive (data gap on " + ", ".join(missing) + ")"
        _emit_inconclusive(verdict, available, missing)
        print(f"verdict: {verdict}")
        return

    # ---- Load
    cpi_m = load_fred_series(p_cpi)         # monthly index
    gdp_q = load_fred_series(p_gdp)         # quarterly real GDP, $bn chained
    ffr_m = load_fred_series(p_ffr)         # monthly effective fed funds

    # GDP timestamps from FRED are at quarter-start by convention; ensure QS index.
    gdp_q.index = pd.to_datetime(gdp_q.index)
    gdp_q = gdp_q.sort_index()

    # ---- CPI YoY at quarterly resolution
    cpi_yoy_q = cpi_yoy_quarterly(cpi_m)

    # Peak inflation in the 1979Q1-1981Q4 vicinity (Volcker-era peak)
    peak_window = cpi_yoy_q[(cpi_yoy_q.index >= "1979-01-01")
                            & (cpi_yoy_q.index <= "1981-12-31")]
    if peak_window.empty:
        raise RuntimeError("CPI YoY peak window empty — vintage too short")
    peak_qtr = peak_window.idxmax()
    peak_cpi_yoy = float(peak_window.max())

    # Inflation at 1983Q4
    if INFL_TARGET_QUARTER not in cpi_yoy_q.index:
        # Allow nearest within the same quarter
        nearest = cpi_yoy_q.index[cpi_yoy_q.index.year == 1983]
        nearest = nearest[(nearest.month >= 10)]
        if len(nearest) == 0:
            raise RuntimeError("No 1983Q4 CPI YoY observation")
        cpi_1983q4 = float(cpi_yoy_q.loc[nearest[0]])
    else:
        cpi_1983q4 = float(cpi_yoy_q.loc[INFL_TARGET_QUARTER])

    infl_drop_pp = peak_cpi_yoy - cpi_1983q4

    primary_a_pass = (cpi_1983q4 <= INFL_LEVEL_MAX_1983Q4) and (infl_drop_pp >= INFL_DROP_MIN_PP)

    # ---- Pre-trend log-linear fit on real GDP, 1972Q1-1979Q3
    gdp_pre = gdp_q[(gdp_q.index >= PRETREND_START) & (gdp_q.index <= PRETREND_END)]
    if len(gdp_pre) < 20:  # 8 yrs * 4 = 32 expected; require >= 20
        verdict = (
            f"inconclusive (pre-trend window 1972Q1-1979Q3 has only "
            f"{len(gdp_pre)} GDPC1 observations; need >= 20 for trend fit)"
        )
        _emit_inconclusive(verdict, available, missing,
                           note="pre-trend window underpopulated")
        print(f"verdict: {verdict}")
        return

    # Independent variable: time index in quarters since PRETREND_START
    t_pre = ((gdp_pre.index - PRETREND_START).days / 91.3125).to_numpy()
    log_gdp_pre = np.log(gdp_pre.values)
    # OLS on (t_pre, log_gdp_pre)
    A = np.vstack([t_pre, np.ones_like(t_pre)]).T
    slope, intercept = np.linalg.lstsq(A, log_gdp_pre, rcond=None)[0]
    pretrend_growth_pa = slope * 4.0  # log-points per year (approx % real growth)

    # Real GDP at 1984Q4
    if RECOVERY_QUARTER not in gdp_q.index:
        gdp_recovery_obs = gdp_q[(gdp_q.index.year == 1984) & (gdp_q.index.month >= 10)]
        if gdp_recovery_obs.empty:
            raise RuntimeError("No 1984Q4 GDPC1 observation")
        gdp_1984q4_qts = gdp_recovery_obs.index[0]
    else:
        gdp_1984q4_qts = RECOVERY_QUARTER
    gdp_1984q4 = float(gdp_q.loc[gdp_1984q4_qts])
    log_gdp_1984q4 = float(np.log(gdp_1984q4))

    t_1984q4 = (gdp_1984q4_qts - PRETREND_START).days / 91.3125
    trend_log_1984q4 = float(slope * t_1984q4 + intercept)
    gap_1984q4_log = log_gdp_1984q4 - trend_log_1984q4

    primary_b_pass = gap_1984q4_log >= RECOVERY_GAP_THRESHOLD
    refuted_b = gap_1984q4_log <= REFUTED_GAP_FLOOR
    refuted_a = infl_drop_pp < INFL_DROP_MIN_PP

    # ---- Informative: peak fed funds 1980-1981 + recession trough
    ffr_q = to_quarterly_mean(ffr_m)
    ffr_treatment_window = ffr_q[(ffr_q.index >= "1980-01-01") & (ffr_q.index <= "1982-06-30")]
    peak_ffr = float(ffr_treatment_window.max()) if not ffr_treatment_window.empty else float("nan")
    peak_ffr_qtr = ffr_treatment_window.idxmax() if not ffr_treatment_window.empty else None

    # Output trough between 1980Q1 and 1983Q4 (relative to trend)
    gdp_window = gdp_q[(gdp_q.index >= "1980-01-01") & (gdp_q.index <= "1983-12-31")]
    if not gdp_window.empty:
        gdp_window_t = ((gdp_window.index - PRETREND_START).days / 91.3125).to_numpy()
        gdp_window_trend = slope * gdp_window_t + intercept
        gdp_window_gap = np.log(gdp_window.values) - gdp_window_trend
        trough_idx = int(np.argmin(gdp_window_gap))
        trough_qtr = gdp_window.index[trough_idx]
        trough_gap = float(gdp_window_gap[trough_idx])
    else:
        trough_qtr = None
        trough_gap = float("nan")

    # ---- Verdict
    supported = primary_a_pass and primary_b_pass
    refuted = refuted_a or refuted_b

    def fmt_q(ts):
        return f"{ts.year}Q{((ts.month - 1) // 3) + 1}" if ts is not None else "n/a"

    if supported:
        verdict = (
            f"SUPPORTED — CPI YoY fell from {peak_cpi_yoy:.1f}% peak "
            f"({fmt_q(peak_qtr)}) to {cpi_1983q4:.1f}% in 1983Q4 "
            f"(drop = {infl_drop_pp:.1f}pp, threshold >= {INFL_DROP_MIN_PP}pp; "
            f"level threshold <= {INFL_LEVEL_MAX_1983Q4}%). Real GDP at 1984Q4 "
            f"was {gap_1984q4_log*100:+.1f}% relative to the 1972Q1-1979Q3 "
            f"linear log-time trend (recovery threshold >= "
            f"{RECOVERY_GAP_THRESHOLD*100:+.1f}%). Both primaries cleared."
        )
    elif refuted:
        which = []
        if refuted_a:
            which.append(
                f"inflation drop only {infl_drop_pp:.1f}pp (need >= {INFL_DROP_MIN_PP}pp)")
        if refuted_b:
            which.append(
                f"1984Q4 output gap {gap_1984q4_log*100:+.1f}% "
                f"(below the {REFUTED_GAP_FLOOR*100:+.1f}% refutation floor)")
        verdict = "refuted — " + "; ".join(which) + "."
    else:
        which = []
        if not primary_a_pass:
            which.append(
                f"disinflation primary failed (1983Q4 CPI YoY = {cpi_1983q4:.1f}%, "
                f"drop {infl_drop_pp:.1f}pp)")
        if not primary_b_pass:
            which.append(
                f"output-recovery primary failed (1984Q4 trend gap = "
                f"{gap_1984q4_log*100:+.1f}%, need >= {RECOVERY_GAP_THRESHOLD*100:+.1f}%)")
        verdict = (
            "partial — " + "; ".join(which) + ". One primary held but not both."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": bool(supported),
        "primary_a_disinflation_pass": bool(primary_a_pass),
        "primary_b_recovery_pass": bool(primary_b_pass),
        "refuted_gate_triggered": bool(refuted),
        "method_valid": True,
        "peak_cpi_yoy": peak_cpi_yoy,
        "peak_cpi_yoy_quarter": fmt_q(peak_qtr),
        "cpi_yoy_1983q4": cpi_1983q4,
        "inflation_drop_peak_to_1983q4_pp": infl_drop_pp,
        "infl_level_threshold_1983q4_pct": INFL_LEVEL_MAX_1983Q4,
        "infl_drop_threshold_pp": INFL_DROP_MIN_PP,
        "real_gdp_1984q4": gdp_1984q4,
        "log_real_gdp_1984q4": log_gdp_1984q4,
        "trend_log_1984q4": trend_log_1984q4,
        "gap_1984q4_to_pretrend_log": gap_1984q4_log,
        "recovery_gap_threshold_log": RECOVERY_GAP_THRESHOLD,
        "refuted_gap_floor_log": REFUTED_GAP_FLOOR,
        "pretrend_window_start": PRETREND_START.date().isoformat(),
        "pretrend_window_end": PRETREND_END.date().isoformat(),
        "pretrend_n_obs": int(len(gdp_pre)),
        "pretrend_growth_pct_per_year": pretrend_growth_pa * 100.0,
        "peak_fed_funds_rate_pct": peak_ffr,
        "peak_fed_funds_quarter": fmt_q(peak_ffr_qtr),
        "trough_quarter_gap_to_trend_pct": trough_gap * 100.0 if not np.isnan(trough_gap) else None,
        "trough_quarter": fmt_q(trough_qtr) if trough_qtr is not None else None,
        "event_date": EVENT_DATE.date().isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=float) + "\n"
    )

    # ---- Coefficients table
    coef = pd.DataFrame([
        {"spec": "primary_a", "term": "peak_cpi_yoy_pct", "estimate": peak_cpi_yoy},
        {"spec": "primary_a", "term": "cpi_yoy_1983q4_pct", "estimate": cpi_1983q4},
        {"spec": "primary_a", "term": "drop_peak_to_1983q4_pp", "estimate": infl_drop_pp},
        {"spec": "primary_b", "term": "log_gap_1984q4_to_pretrend", "estimate": gap_1984q4_log},
        {"spec": "primary_b", "term": "pretrend_growth_pct_per_year", "estimate": pretrend_growth_pa * 100.0},
        {"spec": "informative", "term": "peak_fed_funds_pct", "estimate": peak_ffr},
        {"spec": "informative", "term": "trough_gap_to_trend_pct", "estimate": (trough_gap * 100.0) if not np.isnan(trough_gap) else float("nan")},
    ])
    coef.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---- Chart: CPI YoY trajectory + GDP gap to pretrend
    cpi_pts = []
    for ts, v in cpi_yoy_q.loc["1972-01-01":"1985-12-31"].items():
        if pd.notna(v):
            cpi_pts.append({"x": ts.date().isoformat(), "y": float(v)})

    gap_pts = []
    gdp_chart_window = gdp_q.loc["1972-01-01":"1985-12-31"]
    for ts, v in gdp_chart_window.items():
        t = (ts - PRETREND_START).days / 91.3125
        trend = slope * t + intercept
        gap = float(np.log(v) - trend) * 100.0
        gap_pts.append({"x": ts.date().isoformat(), "y": gap})

    ffr_pts = []
    for ts, v in ffr_q.loc["1972-01-01":"1985-12-31"].items():
        if pd.notna(v):
            ffr_pts.append({"x": ts.date().isoformat(), "y": float(v)})

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Volcker disinflation: CPI YoY, fed funds, and GDP gap to pre-1979 trend",
        "subtitle": (
            f"Peak CPI YoY {peak_cpi_yoy:.1f}% ({fmt_q(peak_qtr)}) -> "
            f"{cpi_1983q4:.1f}% by 1983Q4 (drop = {infl_drop_pp:.1f}pp). "
            f"GDP at 1984Q4: {gap_1984q4_log*100:+.1f}% vs 1972-79 trend."
        ),
        "type": "line",
        "x_axis": {"label": "Quarter", "type": "time"},
        "y_axis": {"label": "% / log-points", "type": "linear"},
        "series": [
            {"id": "CPI_YOY", "label": "CPI YoY %", "color": "#E15759", "treated": True, "points": cpi_pts},
            {"id": "GDP_GAP", "label": "GDP log-gap to 1972-79 trend (%)", "color": "#4E79A7", "treated": False, "points": gap_pts},
            {"id": "FFR", "label": "Effective Fed Funds %", "color": "#59A14F", "treated": False, "points": ffr_pts},
        ],
        "annotations": [
            {"type": "event", "x": EVENT_DATE.date().isoformat(),
             "label": "1979-10 Volcker FOMC tightening"},
            {"type": "note", "label": (
                f"Pre-trend fit: 1972Q1-1979Q3, slope ~ {pretrend_growth_pa*100:.2f}%/yr. "
                f"Disinflation threshold: 1983Q4 CPI YoY <= {INFL_LEVEL_MAX_1983Q4}% AND drop >= {INFL_DROP_MIN_PP}pp. "
                f"Recovery threshold: 1984Q4 log-gap >= {RECOVERY_GAP_THRESHOLD*100:+.1f}%."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---- Manifest
    _write_manifest(available)

    # ---- Result card
    card = [
        "# Volcker disinflation output recovery",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Sample: USA quarterly, 1972Q1-1984Q4 with 1972-1979Q3 pre-trend.",
        f"- Event: 1979-10 Volcker FOMC tightening (effective fed funds peaks at "
        f"**{peak_ffr:.1f}%** in {fmt_q(peak_ffr_qtr)}).",
        f"- CPI YoY: peak **{peak_cpi_yoy:.1f}%** ({fmt_q(peak_qtr)}) -> "
        f"**{cpi_1983q4:.1f}%** in 1983Q4. Drop = **{infl_drop_pp:.1f}pp** "
        f"(threshold >= {INFL_DROP_MIN_PP}pp). Disinflation primary "
        f"{'PASS' if primary_a_pass else 'FAIL'}.",
        f"- Real GDP (GDPC1) at 1984Q4 = **{gap_1984q4_log*100:+.1f}%** vs the "
        f"linear log-time trend fit on 1972Q1-1979Q3 "
        f"(pre-trend growth ~ {pretrend_growth_pa*100:.2f}%/yr). Threshold for "
        f"recovery: gap >= {RECOVERY_GAP_THRESHOLD*100:+.1f}%. Recovery primary "
        f"{'PASS' if primary_b_pass else 'FAIL'}.",
        f"- Recession trough (largest negative gap to trend, 1980-1983): "
        f"**{trough_gap*100:+.1f}%** in {fmt_q(trough_qtr)}.",
        "",
        "## Method",
        "",
        "1. CPI YoY = 12-month log-difference of monthly CPIAUCSL, aggregated to "
        "quarterly mean.",
        "2. Peak CPI YoY identified within 1979Q1-1981Q4 (the Volcker-era peak window).",
        "3. Real-GDP trend = OLS linear fit of log(GDPC1) on time-index "
        "(quarters since 1972Q1) over 1972Q1-1979Q3, then extrapolated.",
        "4. 1984Q4 gap = log(GDPC1_1984Q4) - extrapolated_trend_1984Q4.",
        "5. SUPPORTED iff (1983Q4 CPI YoY <= 5% AND peak-to-1983Q4 drop >= 5pp) "
        "AND (1984Q4 trend gap >= -2%). REFUTED if drop < 5pp OR gap <= -5%.",
        "",
        "## Caveats",
        "",
        "- Pre-trend window includes both 1973 and 1979 oil-price shocks, so the "
        "estimated 1972-79 trajectory is dragged down by them. This is "
        "*conservative for the recovery claim*: a 'no-shock' counterfactual "
        "trend would be steeper, making the 1984Q4 gap larger (more negative). "
        "Hypothesis is therefore tested against an easy benchmark.",
        "- Volcker tightening is bundled with Reagan tax cuts (1981 ERTA) and "
        "the 1980 / 1981-82 recessions. The event-study identifies the *joint* "
        "macro outcome, not the pure monetary-policy effect. The Romer-Romer "
        "narrative-shock decomposition would be required to isolate.",
        "- Single-country analysis: no cross-country counterfactual to a "
        "country that did not tighten. The result is a within-US time-series "
        "test of the disinflation-with-recovery pattern.",
        "",
        "## Data",
        "",
        "- fred:CPIAUCSL — US headline CPI (monthly).",
        "- fred:GDPC1 — US real GDP, chained (quarterly).",
        "- fred:FEDFUNDS — US effective federal funds rate (monthly).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


def _write_manifest(available: dict) -> None:
    lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        "vintages:",
    ]
    for k, v in available.items():
        lines.append(f"  '{k}':")
        lines.append(f"    publisher: {v['publisher']}")
        lines.append(f"    series: {v['series']}")
        lines.append(f"    role: {v['role']}")
        lines.append(f"    vintage_file: {v['vintage_file']}")
        lines.append(f"    sha256: {v['sha256']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n")


def _emit_inconclusive(verdict, available, missing, note=""):
    diagnostics = {
        "verdict": verdict, "all_pass": False, "method_valid": False,
        "data_gap": True, "missing_series": missing,
        "available_series": sorted(available.keys()), "note": note,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    pd.DataFrame([
        {"spec": "primary_a", "term": "cpi_yoy_1983q4_pct", "estimate": np.nan},
        {"spec": "primary_b", "term": "log_gap_1984q4_to_pretrend", "estimate": np.nan},
    ]).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    chart_data = {
        "kind": "result", "chart_id": f"{HID}/fig1",
        "title": "Volcker disinflation output recovery — DATA GAP",
        "subtitle": verdict, "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "%", "type": "linear"},
        "series": [],
        "annotations": [{"type": "note", "label": "Missing: " + ", ".join(missing)}],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")
    _write_manifest(available)
    (OUT_DIR / "result_card.md").write_text(
        f"# Volcker disinflation output recovery\n\n**Verdict:** {verdict}\n\n"
        f"## Missing data\n\n" + "\n".join(f"- {m}" for m in missing) + "\n"
    )


if __name__ == "__main__":
    main()
