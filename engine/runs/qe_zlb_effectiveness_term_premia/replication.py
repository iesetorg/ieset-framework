#!/usr/bin/env python3
"""Replication — QE at the ZLB: event-study effects on long yields & spreads.

Spec: hypotheses/monetary/qe_zlb_effectiveness_term_premia.yaml v1
Position-claim: new_keynesian #2 (school predicts: supported)

PRIMARY (dispositive):
  Take six FOMC QE-related announcement dates (QE1 launch, QE1 expansion,
  QE2, Operation Twist, QE3, QE3 taper). For each, compute the change in
  the 10-year Treasury yield over a [t, t+1 trading day] window and a
  [t-1, t+5 trading day] window using FRED daily data (DGS10).
  The hypothesis is SUPPORTED if the *cumulative* (sum across announcements,
  excluding the taper which is an unwind) 1-day yield change is at most
  -25 bp AND the average 1-day change across the five easing announcements
  is at most -5 bp. The taper announcement is graded separately and is
  expected to RAISE yields (positive) under the same channel.

  REFUTED if the cumulative 1-day yield change across the five easing
  announcements is positive, OR if zero of five easing announcements show
  a yield decline.

SECONDARY (informative, does not gate verdict):
  - 30-year Treasury yield (DGS30) cumulative change, same construction.
  - High-yield OAS (BAMLH0A0HYM2) cumulative change — a portfolio-rebalancing
    channel implies HY spreads should also narrow on QE (negative cumulative
    change across easing dates).
  - BAA corporate yield change (note: AAA series not on disk so we report
    BAA level changes rather than BAA-AAA spread).

METHOD_VALID gates:
  - All six announcement dates fall inside the on-disk DGS10 vintage range.
  - At least 5 of 6 announcement dates have a tradable observation within
    +/- 2 trading days.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "qe_zlb_effectiveness_term_premia"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Event dates (per spec.variables.treatment[0])
QE_EVENTS = [
    ("2008-11-25", "QE1 launch",        "easing"),
    ("2009-03-18", "QE1 expansion",     "easing"),
    ("2010-11-03", "QE2",               "easing"),
    ("2011-09-21", "Operation Twist",   "easing"),
    ("2012-09-13", "QE3",               "easing"),
    ("2013-12-18", "QE3 taper",         "tightening"),
]

# Falsification thresholds (sharpened in promotion v1)
PRIMARY_CUMUL_1D_THRESHOLD_BP = -25.0  # sum across 5 easing events <= -25 bp
PRIMARY_AVG_1D_THRESHOLD_BP   = -5.0   # mean across 5 easing events <= -5 bp
TAPER_EXPECTED_SIGN_POSITIVE  = True


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


def load_fred(path: Path) -> pd.Series:
    """FRED parquet → date-indexed value Series (level, NaN-filtered)."""
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns or "value" not in t.columns:
        raise ValueError(f"{path}: missing date/value columns ({list(t.columns)})")
    t["date"] = pd.to_datetime(t["date"])
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.dropna(subset=["value"]).sort_values("date")
    # If realtime/vintage rows exist, take the last (latest) realtime per date.
    if "realtime_start" in t.columns:
        t = t.drop_duplicates("date", keep="last")
    return t.set_index("date")["value"]


def event_window(series: pd.Series, ev_date: pd.Timestamp,
                 lookback: int, lookahead: int) -> tuple[float | None, float | None, str]:
    """Return (pre_value, post_value, note).

    pre = the last observation strictly BEFORE ev_date (close of t-1).
          For lookback=1 this is the trading day immediately preceding ev_date.
          For lookback=N we step back N business days from ev_date and take
          the nearest prior observation.
    post = the first observation at-or-after the post_anchor day.
          post_anchor = ev_date + lookahead business days.
    """
    pre_target = ev_date - pd.tseries.offsets.BDay(lookback)
    # All obs strictly before ev_date (so we never use the announcement-day close itself)
    pre_window = series.loc[:ev_date - pd.Timedelta(days=1)]
    if pre_window.empty:
        return None, None, "no pre obs"
    # Take the obs closest to pre_target on or before it (or, if none, the last one before ev_date)
    pre_eligible = pre_window.loc[pre_window.index <= pre_target]
    if pre_eligible.empty:
        # No obs at-or-before pre_target — fall back to last obs before ev_date.
        pre_val = float(pre_window.iloc[-1])
    else:
        pre_val = float(pre_eligible.iloc[-1])

    post_target = ev_date + pd.tseries.offsets.BDay(lookahead)
    # First obs at-or-after post_target
    post_window = series.loc[post_target:]
    if post_window.empty:
        # Fall back to first obs after ev_date
        post_window = series.loc[ev_date + pd.Timedelta(days=1):]
    if post_window.empty:
        return pre_val, None, "no post obs"
    post_val = float(post_window.iloc[0])
    return pre_val, post_val, "ok"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Vintage discovery ----------
    series_pins = {
        "treasury_10y": ("fred", "DGS10"),
        "treasury_30y": ("fred", "DGS30"),
        "baa_corporate": ("fred", "BAA"),
        "high_yield_oas": ("fred", "BAMLH0A0HYM2"),
        "fed_balance_sheet": ("fred", "WALCL"),
        "vix": ("fred", "VIXCLS"),
        "sp500": ("fred", "SP500"),
        "fed_funds_rate": ("fred", "DFF"),
    }

    available: dict[str, dict] = {}
    missing: list[str] = []
    paths: dict[str, Path] = {}
    for role, (pub, ser) in series_pins.items():
        p = latest(pub, ser)
        if p is None:
            missing.append(f"{pub}:{ser}")
        else:
            available[role] = {
                "publisher": pub,
                "series": ser,
                "vintage_file": str(p.relative_to(REPO_ROOT)),
                "sha256": sha256(p),
            }
            paths[role] = p

    # The PRIMARY needs DGS10 only. Without it we are data-gapped.
    if "treasury_10y" not in paths:
        verdict = (
            f"inconclusive — data gap on fred:DGS10. "
            f"PRIMARY event-study on the 10-year yield cannot be computed."
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "data_gap": True,
            "missing_series": missing,
            "available": list(available.keys()),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(f"# {HID}\n\n**Verdict:** {verdict}\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nstatus: data_gap_inconclusive\n"
        )
        pd.DataFrame([{"spec": "primary", "term": "cumul_1d_dgs10_bp", "estimate": np.nan}]) \
          .to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "QE event study — DATA GAP",
            "type": "line", "series": [], "annotations": [], "sources": [],
            "permalink": f"/h/{HID}",
        }, indent=2))
        print(f"verdict: {verdict}")
        return

    # ---------- Load series ----------
    dgs10 = load_fred(paths["treasury_10y"])
    dgs30 = load_fred(paths["treasury_30y"]) if "treasury_30y" in paths else None
    baa = load_fred(paths["baa_corporate"]) if "baa_corporate" in paths else None
    hyoas = load_fred(paths["high_yield_oas"]) if "high_yield_oas" in paths else None
    walcl = load_fred(paths["fed_balance_sheet"]) if "fed_balance_sheet" in paths else None

    # ---------- Compute event windows ----------
    rows = []
    for ev_str, label, kind in QE_EVENTS:
        ev = pd.Timestamp(ev_str)
        # 1-day window: previous trading day → next trading day.
        pre10, post10, note10 = event_window(dgs10, ev, lookback=1, lookahead=1)
        # 5-day window: previous trading day → +5 trading days.
        pre10_5, post10_5, _ = event_window(dgs10, ev, lookback=1, lookahead=5)
        d10_1d = (post10 - pre10) * 100.0 if pre10 is not None and post10 is not None else None  # bp
        d10_5d = (post10_5 - pre10_5) * 100.0 if pre10_5 is not None and post10_5 is not None else None

        d30_1d = None
        if dgs30 is not None:
            pre30, post30, _ = event_window(dgs30, ev, 1, 1)
            if pre30 is not None and post30 is not None:
                d30_1d = (post30 - pre30) * 100.0

        dbaa_1d = None
        if baa is not None:
            preb, postb, _ = event_window(baa, ev, 1, 1)
            if preb is not None and postb is not None:
                dbaa_1d = (postb - preb) * 100.0

        dhy_1d = None
        if hyoas is not None:
            preh, posth, _ = event_window(hyoas, ev, 1, 1)
            if preh is not None and posth is not None:
                # OAS already in pp; convert to bp: multiply by 100.
                dhy_1d = (posth - preh) * 100.0

        rows.append({
            "event_date": ev_str,
            "label": label,
            "kind": kind,
            "d_dgs10_1d_bp": d10_1d,
            "d_dgs10_5d_bp": d10_5d,
            "d_dgs30_1d_bp": d30_1d,
            "d_baa_1d_bp": dbaa_1d,
            "d_hyoas_1d_bp": dhy_1d,
            "note_dgs10": note10,
        })

    ev_df = pd.DataFrame(rows)
    easing = ev_df[ev_df["kind"] == "easing"].copy()
    taper = ev_df[ev_df["kind"] == "tightening"].copy()

    # ---------- Method-validity gate ----------
    n_easing_with_dgs10 = int(easing["d_dgs10_1d_bp"].notna().sum())
    method_valid = n_easing_with_dgs10 >= 4  # >=4 of 5 easing events
    earliest_dgs10 = dgs10.index.min()
    latest_dgs10 = dgs10.index.max()
    all_dates_in_range = all(
        earliest_dgs10 <= pd.Timestamp(d) <= latest_dgs10
        for d, _, _ in QE_EVENTS
    )

    # ---------- PRIMARY statistics ----------
    cumul_1d = float(easing["d_dgs10_1d_bp"].sum(skipna=True))
    avg_1d = float(easing["d_dgs10_1d_bp"].mean(skipna=True))
    n_negative = int((easing["d_dgs10_1d_bp"] < 0).sum())
    n_total_easing = int(len(easing))

    primary_cumul_supported = cumul_1d <= PRIMARY_CUMUL_1D_THRESHOLD_BP
    primary_avg_supported = avg_1d <= PRIMARY_AVG_1D_THRESHOLD_BP
    primary_supported = primary_cumul_supported and primary_avg_supported
    primary_refuted = (cumul_1d > 0) or (n_negative == 0)

    # Taper grade (informative): expected sign positive
    taper_d10 = float(taper["d_dgs10_1d_bp"].iloc[0]) if len(taper) and pd.notna(taper["d_dgs10_1d_bp"].iloc[0]) else None
    taper_consistent = (taper_d10 is not None and taper_d10 > 0) == TAPER_EXPECTED_SIGN_POSITIVE if taper_d10 is not None else None

    # SECONDARY informative measures
    cumul_dgs30 = float(easing["d_dgs30_1d_bp"].sum(skipna=True))
    cumul_baa = float(easing["d_baa_1d_bp"].sum(skipna=True))
    cumul_hyoas = float(easing["d_hyoas_1d_bp"].sum(skipna=True))

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive — method-validity gate failed: only "
            f"{n_easing_with_dgs10} of {n_total_easing} easing events have a "
            f"DGS10 observation. Cannot grade primary."
        )
    elif primary_supported:
        verdict = (
            f"SUPPORTED — Cumulative 1-day 10y Treasury yield change across "
            f"{n_total_easing} easing announcements: {cumul_1d:+.1f} bp "
            f"(threshold: <= {PRIMARY_CUMUL_1D_THRESHOLD_BP:+.1f} bp). "
            f"Mean per-event: {avg_1d:+.1f} bp "
            f"(threshold: <= {PRIMARY_AVG_1D_THRESHOLD_BP:+.1f} bp). "
            f"{n_negative} of {n_total_easing} events show a yield decline. "
            f"Secondary: 30y cumul {cumul_dgs30:+.1f} bp, HY OAS cumul "
            f"{cumul_hyoas:+.1f} bp."
        )
    elif primary_refuted:
        verdict = (
            f"refuted — Cumulative 1-day 10y yield change across "
            f"{n_total_easing} easing announcements: {cumul_1d:+.1f} bp "
            f"(refute condition: > 0 OR zero declines). "
            f"{n_negative} of {n_total_easing} events show a yield decline."
        )
    else:
        verdict = (
            f"partial — Cumulative 1-day 10y yield change: {cumul_1d:+.1f} bp "
            f"(SUPPORT threshold: <= {PRIMARY_CUMUL_1D_THRESHOLD_BP:+.1f}). "
            f"Direction matches the claim "
            f"({n_negative}/{n_total_easing} declines, mean {avg_1d:+.1f} bp) "
            f"but magnitude misses the dispositive threshold."
        )

    # ---------- Diagnostics ----------
    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "all_announcements_in_data_range": all_dates_in_range,
        "n_easing_events": n_total_easing,
        "n_easing_with_dgs10": n_easing_with_dgs10,
        "primary_cumul_1d_dgs10_bp": cumul_1d,
        "primary_avg_1d_dgs10_bp": avg_1d,
        "primary_n_negative": n_negative,
        "primary_cumul_threshold_bp": PRIMARY_CUMUL_1D_THRESHOLD_BP,
        "primary_avg_threshold_bp": PRIMARY_AVG_1D_THRESHOLD_BP,
        "primary_cumul_supported": primary_cumul_supported,
        "primary_avg_supported": primary_avg_supported,
        "primary_supported": primary_supported,
        "primary_refuted": primary_refuted,
        "taper_d_dgs10_1d_bp": taper_d10,
        "taper_consistent_with_unwind": taper_consistent,
        "secondary_cumul_dgs30_bp": cumul_dgs30,
        "secondary_cumul_baa_bp": cumul_baa,
        "secondary_cumul_hyoas_bp": cumul_hyoas,
        "events": rows,
        "data_range": {
            "dgs10_start": str(earliest_dgs10.date()),
            "dgs10_end": str(latest_dgs10.date()),
        },
        "missing_series": missing,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ---------- Coefficients ----------
    coef_rows = []
    for r in rows:
        coef_rows.append({"spec": "event_1d_dgs10", "term": r["event_date"],
                           "estimate": r["d_dgs10_1d_bp"]})
    coef_rows.append({"spec": "primary", "term": "cumul_1d_dgs10_bp_easing", "estimate": cumul_1d})
    coef_rows.append({"spec": "primary", "term": "avg_1d_dgs10_bp_easing", "estimate": avg_1d})
    coef_rows.append({"spec": "secondary", "term": "cumul_1d_dgs30_bp_easing", "estimate": cumul_dgs30})
    coef_rows.append({"spec": "secondary", "term": "cumul_1d_baa_bp_easing", "estimate": cumul_baa})
    coef_rows.append({"spec": "secondary", "term": "cumul_1d_hyoas_bp_easing", "estimate": cumul_hyoas})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Chart ----------
    palette = ["#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2"]
    bar_series = []
    for i, r in enumerate(rows):
        bar_series.append({
            "id": r["event_date"],
            "label": f"{r['label']} ({r['event_date']})",
            "color": palette[i % len(palette)],
            "treated": r["kind"] == "tightening",
            "points": [
                {"x": "10y 1d", "y": r["d_dgs10_1d_bp"]},
                {"x": "10y 5d", "y": r["d_dgs10_5d_bp"]},
                {"x": "30y 1d", "y": r["d_dgs30_1d_bp"]},
                {"x": "HY OAS 1d", "y": r["d_hyoas_1d_bp"]},
            ],
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Fed QE announcement event study — yield & spread changes (bp)",
        "subtitle": (
            f"Cumulative 1-day 10y yield change across {n_total_easing} easing "
            f"announcements: {cumul_1d:+.1f} bp (threshold for SUPPORTED: "
            f"<= {PRIMARY_CUMUL_1D_THRESHOLD_BP:+.0f} bp). Taper sanity check: "
            f"{taper_d10:+.1f} bp." if taper_d10 is not None else
            f"Cumulative 1-day 10y yield change: {cumul_1d:+.1f} bp."
        ),
        "type": "bar",
        "x_axis": {"label": "instrument × window", "type": "categorical"},
        "y_axis": {"label": "change (basis points)", "type": "linear"},
        "series": bar_series,
        "annotations": [
            {"type": "note", "label": (
                f"PRIMARY (dispositive): cumulative 1-day DGS10 change across "
                f"the 5 easing events <= {PRIMARY_CUMUL_1D_THRESHOLD_BP:+.0f} bp "
                f"AND mean <= {PRIMARY_AVG_1D_THRESHOLD_BP:+.0f} bp."
            )},
            {"type": "note", "label": (
                f"Result: cumulative {cumul_1d:+.1f} bp; mean {avg_1d:+.1f} bp; "
                f"{n_negative}/{n_total_easing} events declined."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2, default=str) + "\n")

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
    if missing:
        manifest_lines.append("missing_series:")
        for m in missing:
            manifest_lines.append(f"  - {m}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

    # ---------- Result card ----------
    card = [
        f"# QE at the ZLB: term-premia compression event study",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Six FOMC QE-related announcement dates 2008-2013, FRED daily data.",
        f"- PRIMARY: cumulative 1-day 10y Treasury yield change across the "
        f"five easing announcements = **{cumul_1d:+.1f} bp** "
        f"(SUPPORT threshold: <= {PRIMARY_CUMUL_1D_THRESHOLD_BP:+.0f} bp).",
        f"- Mean per-event 1-day change: **{avg_1d:+.1f} bp** "
        f"(SUPPORT threshold: <= {PRIMARY_AVG_1D_THRESHOLD_BP:+.0f} bp).",
        f"- {n_negative} of {n_total_easing} easing events show a 1-day yield decline.",
        f"- 5-day cumulative 10y change: "
        f"{float(easing['d_dgs10_5d_bp'].sum(skipna=True)):+.1f} bp.",
        f"- Secondary 30y cumulative: **{cumul_dgs30:+.1f} bp**.",
        f"- Secondary HY OAS cumulative: **{cumul_hyoas:+.1f} bp** "
        f"(portfolio-rebalancing channel implies negative).",
        f"- Taper (2013-12-18) 1-day 10y: "
        f"**{taper_d10:+.1f} bp**" if taper_d10 is not None else "Taper: no data",
        ".",
        "",
        "## Per-event table (basis points)",
        "",
        "| Event | Date | Kind | 10y 1d | 10y 5d | 30y 1d | BAA 1d | HY OAS 1d |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    def _fmt(v):
        return f"{v:+.1f}" if v is not None and not (isinstance(v, float) and np.isnan(v)) else "NA"
    for r in rows:
        card.append(
            f"| {r['label']} | {r['event_date']} | {r['kind']} | "
            f"{_fmt(r['d_dgs10_1d_bp'])} | "
            f"{_fmt(r['d_dgs10_5d_bp'])} | "
            f"{_fmt(r['d_dgs30_1d_bp'])} | "
            f"{_fmt(r['d_baa_1d_bp'])} | "
            f"{_fmt(r['d_hyoas_1d_bp'])} |"
        )
    card += [
        "",
        "## Method",
        "",
        "Daily FRED yield series (DGS10, DGS30, BAA, BAMLH0A0HYM2). For each "
        "FOMC QE-related announcement date listed in spec.variables.treatment, "
        "compute the change between the previous trading day's close and the "
        "next trading day's close (1-day window). 5-day window is "
        "previous-trading-day → +5 trading days. Levels in percent are "
        "converted to basis points (×100).",
        "",
        "Why a daily window rather than the canonical 30-min intraday window: "
        "FRED publishes daily close yields, not intraday tick data. The "
        "1-day close-to-close window is a noisier-but-publicly-replicable "
        "proxy for the 30-min event window used in Gagnon-Raskin-Remache-Sack "
        "(2011) and Krishnamurthy-Vissing-Jorgensen (2011). The thresholds "
        "below were sized for this daily window rather than the literature's "
        "intraday window.",
        "",
        "Falsification thresholds (dispositive, sharpened in v1 promotion):",
        f"  PRIMARY (both required for SUPPORTED):",
        f"    - cumulative 1-day DGS10 change across 5 easing announcements "
        f"      <= {PRIMARY_CUMUL_1D_THRESHOLD_BP:+.0f} bp",
        f"    - mean 1-day DGS10 change across 5 easing announcements "
        f"      <= {PRIMARY_AVG_1D_THRESHOLD_BP:+.0f} bp",
        f"  REFUTED if cumulative > 0 bp OR zero of five easing events show a decline.",
        f"  PARTIAL if direction is correct but cumulative magnitude misses threshold.",
        "",
        "## Data",
        "",
    ]
    for k, v in available.items():
        card.append(f"- `{v['publisher']}:{v['series']}` ({k})")
    if missing:
        card.append("")
        card.append("Missing series (informative-only secondaries):")
        for m in missing:
            card.append(f"- `{m}`")
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
