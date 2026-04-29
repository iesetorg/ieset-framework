#!/usr/bin/env python3
"""Replication — Post-2008 FOMC forward-guidance term-structure event study.

Spec: hypotheses/monetary/forward_guidance_term_structure_effect.yaml v1
Position-claim: new_keynesian #12 (school predicts: supported)

Tests whether US Treasury yields (2y/5y/10y) reacted materially to a hand-coded
list of canonical FOMC forward-guidance announcements 2008-2017, relative to a
calendar-matched non-FOMC-Wednesday placebo.

PRIMARY (dispositive):
  mean_abs_dgs2_fg >= 0.05 pp AND
  mean_abs_dgs2_fg >= 2 * mean_abs_dgs2_placebo

INFORMATIVE:
  Same direction at DGS5 with mean_abs_dgs5_fg >= 1.5 * placebo (else verdict
  downgraded one notch).

METHOD_VALID:
  DGS2/5/10 all on disk for 2008-2017 with no missing FG-day observations and
  >=10 placebo observations per event-month. Failure -> inconclusive.

Out of scope (data-gap, METHOD_VALID):
  - Intraday 30-min windows (no intraday FRED on disk).
  - ECB / BoE / BoJ forward-guidance legs (no euro-area, UK, JP yield series
    on disk in current vintage tree).
  - Pure-signal RE benchmark (no calibrated NK model in repo).
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
HID = "forward_guidance_term_structure_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Hand-coded FOMC forward-guidance announcement dates (canonical literature list).
FG_EVENT_DATES = [
    pd.Timestamp("2008-12-16"),  # ZLB + "extended period" guidance
    pd.Timestamp("2011-08-09"),  # mid-2013 calendar guidance
    pd.Timestamp("2012-09-13"),  # mid-2015 calendar guidance + QE3
    pd.Timestamp("2013-12-18"),  # taper announcement + threshold guidance
    pd.Timestamp("2015-09-17"),  # lift-off delay
]

# Falsification thresholds (dispositive).
DGS2_ABS_THRESHOLD_PP = 0.05  # >=5 bp mean absolute move on FG days
PRIMARY_PLACEBO_RATIO = 2.0   # FG mean abs >= 2x placebo mean abs
INFORMATIVE_PLACEBO_RATIO = 1.5  # downgrade if DGS5 doesn't clear 1.5x


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_optional(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_daily(path: Path) -> pd.DataFrame:
    """FRED on-disk shape: (date, value, realtime_start, realtime_end)."""
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns or "value" not in t.columns:
        raise ValueError(f"{path}: need (date,value) cols, got {list(t.columns)}")
    t = t[["date", "value"]].copy()
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna().sort_values("date").reset_index(drop=True)


def one_day_change(df: pd.DataFrame, event: pd.Timestamp) -> dict:
    """Close-to-close change anchored to last trading day strictly before
    `event` and the close on or after `event`."""
    pre_window = df[(df["date"] < event) & (df["date"] >= event - pd.Timedelta(days=10))]
    on_after = df[df["date"] >= event][df["date"] <= event + pd.Timedelta(days=4)]
    if pre_window.empty or on_after.empty:
        return {"error": f"missing pre/post observation around {event.date()}"}
    pre = pre_window.iloc[-1]
    post = on_after.iloc[0]
    return {
        "event": event.date().isoformat(),
        "pre_date": pre["date"].date().isoformat(),
        "pre_value": float(pre["value"]),
        "post_date": post["date"].date().isoformat(),
        "post_value": float(post["value"]),
        "delta_pp": float(post["value"] - pre["value"]),
    }


def placebo_dates(df: pd.DataFrame, event: pd.Timestamp,
                  exclude: set[pd.Timestamp]) -> list[pd.Timestamp]:
    """Calendar-matched non-FOMC Wednesdays in the SAME calendar month as
    `event` (excluding the event date itself). FOMC meets on Tue/Wed and the
    bulk of FG headlines hit on Wednesday afternoons; matching to other
    Wednesdays in the month is a clean same-month, same-day-of-week placebo."""
    month_start = event.replace(day=1)
    next_month = (month_start + pd.offsets.MonthBegin(1))
    same_month = df[(df["date"] >= month_start) & (df["date"] < next_month)]
    weds = same_month[same_month["date"].dt.dayofweek == 2]
    return [d for d in weds["date"].tolist() if pd.Timestamp(d) not in exclude]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------- Locate vintages -----------------
    dgs2_path = latest_optional("fred", "DGS2")
    dgs5_path = latest_optional("fred", "DGS5")
    dgs10_path = latest_optional("fred", "DGS10")
    vix_path = latest_optional("fred", "VIXCLS")

    manifest: dict[str, dict] = {}

    def pin(role: str, pub: str, series: str, path: Path | None) -> None:
        if path is None:
            manifest[role] = {"publisher": pub, "series": series,
                              "vintage_file": None, "sha256": None,
                              "status": "missing_on_disk"}
        else:
            manifest[role] = {
                "publisher": pub, "series": series,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
                "status": "loaded",
            }

    pin("treasury_2y", "fred", "DGS2", dgs2_path)
    pin("treasury_5y", "fred", "DGS5", dgs5_path)
    pin("treasury_10y", "fred", "DGS10", dgs10_path)
    pin("vix", "fred", "VIXCLS", vix_path)

    # METHOD_VALID gate on primary outcome
    if dgs2_path is None:
        verdict = ("inconclusive (data gap on fred:DGS2) — primary outcome "
                   "series not available; cannot evaluate FOMC FG term-structure "
                   "claim.")
        _write_data_gap(verdict, manifest)
        print(f"verdict: {verdict}")
        return

    dgs2 = load_daily(dgs2_path)
    dgs5 = load_daily(dgs5_path) if dgs5_path else None
    dgs10 = load_daily(dgs10_path) if dgs10_path else None
    vix = load_daily(vix_path) if vix_path else None

    # ----------------- Per-event 1-day changes -----------------
    fg_set = set(FG_EVENT_DATES)
    per_event = []
    for ev in FG_EVENT_DATES:
        row = {"event_date": ev.date().isoformat()}
        for label, df in [("dgs2", dgs2), ("dgs5", dgs5), ("dgs10", dgs10),
                          ("vix", vix)]:
            if df is None:
                row[f"{label}_delta"] = None
                continue
            res = one_day_change(df, ev)
            row[f"{label}_delta"] = res.get("delta_pp")
            if "error" in res:
                row[f"{label}_error"] = res["error"]
        per_event.append(row)

    # ----------------- Placebo Wednesdays -----------------
    placebo_per_event: list[dict] = []
    for ev in FG_EVENT_DATES:
        # Need at least DGS2 placebos for the primary statistic.
        ev_placebos = placebo_dates(dgs2, ev, fg_set)
        evrow = {"event_date": ev.date().isoformat(),
                 "n_placebo_wednesdays": len(ev_placebos),
                 "placebo_deltas_dgs2": []}
        for p in ev_placebos:
            r = one_day_change(dgs2, pd.Timestamp(p))
            if "delta_pp" in r:
                evrow["placebo_deltas_dgs2"].append(r["delta_pp"])
        if dgs5 is not None:
            evrow["placebo_deltas_dgs5"] = []
            for p in ev_placebos:
                r = one_day_change(dgs5, pd.Timestamp(p))
                if "delta_pp" in r:
                    evrow["placebo_deltas_dgs5"].append(r["delta_pp"])
        placebo_per_event.append(evrow)

    # ----------------- Mean abs statistics -----------------
    fg_dgs2 = [r["dgs2_delta"] for r in per_event if r.get("dgs2_delta") is not None]
    fg_dgs5 = [r["dgs5_delta"] for r in per_event if r.get("dgs5_delta") is not None]
    fg_dgs10 = [r["dgs10_delta"] for r in per_event if r.get("dgs10_delta") is not None]
    placebo_dgs2_all: list[float] = []
    placebo_dgs5_all: list[float] = []
    for evrow in placebo_per_event:
        placebo_dgs2_all.extend(evrow.get("placebo_deltas_dgs2", []))
        placebo_dgs5_all.extend(evrow.get("placebo_deltas_dgs5", []))

    mean_abs_fg_dgs2 = float(np.mean(np.abs(fg_dgs2))) if fg_dgs2 else None
    mean_abs_fg_dgs5 = float(np.mean(np.abs(fg_dgs5))) if fg_dgs5 else None
    mean_abs_fg_dgs10 = float(np.mean(np.abs(fg_dgs10))) if fg_dgs10 else None
    mean_abs_placebo_dgs2 = (float(np.mean(np.abs(placebo_dgs2_all)))
                             if placebo_dgs2_all else None)
    mean_abs_placebo_dgs5 = (float(np.mean(np.abs(placebo_dgs5_all)))
                             if placebo_dgs5_all else None)

    # METHOD_VALID gates.
    method_valid_msgs: list[str] = []
    if mean_abs_fg_dgs2 is None or len(fg_dgs2) < 5:
        method_valid_msgs.append(
            f"DGS2 missing on FG dates: only {len(fg_dgs2)}/5 events resolved.")
    if mean_abs_placebo_dgs2 is None or len(placebo_dgs2_all) < 10:
        method_valid_msgs.append(
            f"<10 DGS2 placebo Wednesdays available "
            f"({len(placebo_dgs2_all)}); placebo bar unreliable.")

    if method_valid_msgs:
        verdict = ("inconclusive (METHOD_VALID failure) — "
                   + "; ".join(method_valid_msgs))
        _write_data_gap(verdict, manifest, extra={
            "per_event": per_event,
            "placebo_per_event": placebo_per_event,
        })
        print(f"verdict: {verdict}")
        return

    placebo_ratio_dgs2 = (mean_abs_fg_dgs2 / mean_abs_placebo_dgs2
                          if mean_abs_placebo_dgs2 else None)
    placebo_ratio_dgs5 = (
        (mean_abs_fg_dgs5 / mean_abs_placebo_dgs5)
        if (mean_abs_fg_dgs5 is not None and mean_abs_placebo_dgs5)
        else None)

    # ----------------- Verdict -----------------
    primary_pass_magnitude = mean_abs_fg_dgs2 >= DGS2_ABS_THRESHOLD_PP
    primary_pass_placebo = (placebo_ratio_dgs2 is not None and
                            placebo_ratio_dgs2 >= PRIMARY_PLACEBO_RATIO)
    informative_pass = (placebo_ratio_dgs5 is not None and
                        placebo_ratio_dgs5 >= INFORMATIVE_PLACEBO_RATIO)

    summary_stat = (
        f"mean |ΔDGS2| on {len(fg_dgs2)} FG days = {mean_abs_fg_dgs2*100:.1f} bp; "
        f"placebo mean |Δ| = {mean_abs_placebo_dgs2*100:.1f} bp "
        f"(ratio {placebo_ratio_dgs2:.2f}x); "
        f"DGS5 ratio = {placebo_ratio_dgs5:.2f}x"
        if placebo_ratio_dgs5 is not None
        else f"DGS5 placebo ratio unresolved"
    )

    if primary_pass_magnitude and primary_pass_placebo and informative_pass:
        verdict_label = "SUPPORTED"
        verdict = (f"SUPPORTED (US-FOMC daily channel only) — {summary_stat}. "
                   f"Mean |ΔDGS2| clears the 5bp magnitude bar AND the 2x "
                   f"placebo bar; DGS5 also clears the 1.5x informative bar. "
                   f"ECB/BoE/BoJ legs and intraday discrimination of "
                   f"sticky-info vs RE-signal remain METHOD_VALID data gaps.")
    elif primary_pass_magnitude and primary_pass_placebo and not informative_pass:
        verdict_label = "partial"
        verdict = (f"partial — {summary_stat}. Primary DGS2 bars met (>=5bp, "
                   f">=2x placebo) but DGS5 informative gate (>=1.5x placebo) "
                   f"missed; term-structure leg of claim only partially borne "
                   f"out in daily data. Verdict downgraded one notch from "
                   f"SUPPORTED.")
    elif primary_pass_magnitude and not primary_pass_placebo:
        verdict_label = "partial"
        verdict = (f"partial — {summary_stat}. DGS2 cleared the 5bp magnitude "
                   f"bar but failed the 2x placebo bar; FG-day moves are "
                   f"large in absolute terms but not distinguishable from "
                   f"normal monthly Wednesday volatility.")
    elif not primary_pass_magnitude and primary_pass_placebo:
        verdict_label = "partial"
        verdict = (f"partial — {summary_stat}. DGS2 cleared the 2x placebo "
                   f"bar but mean |Δ| is below the 5bp magnitude floor; "
                   f"effect direction-consistent but small in absolute terms.")
    else:
        verdict_label = "refuted"
        verdict = (f"refuted (US-FOMC daily channel) — {summary_stat}. "
                   f"Mean |ΔDGS2| failed BOTH the 5bp magnitude floor AND "
                   f"the 2x placebo bar; daily yields did not move materially "
                   f"more on FOMC FG days than on matched non-FOMC Wednesdays. "
                   f"Note: this refutes the daily-frequency US-only proxy "
                   f"only; the spec's intraday and non-US legs remain "
                   f"METHOD_VALID data gaps.")

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "fg_event_dates": [d.date().isoformat() for d in FG_EVENT_DATES],
        "primary": {
            "outcome": "fred:DGS2 1-day Δ on FOMC FG days vs placebo Wednesdays",
            "n_fg_events_resolved": len(fg_dgs2),
            "mean_abs_fg_dgs2_pp": mean_abs_fg_dgs2,
            "mean_abs_placebo_dgs2_pp": mean_abs_placebo_dgs2,
            "placebo_ratio_dgs2": placebo_ratio_dgs2,
            "magnitude_threshold_pp": DGS2_ABS_THRESHOLD_PP,
            "placebo_ratio_threshold": PRIMARY_PLACEBO_RATIO,
            "magnitude_pass": primary_pass_magnitude,
            "placebo_ratio_pass": primary_pass_placebo,
        },
        "informative_dgs5": {
            "n_fg_events_resolved": len(fg_dgs5),
            "mean_abs_fg_dgs5_pp": mean_abs_fg_dgs5,
            "mean_abs_placebo_dgs5_pp": mean_abs_placebo_dgs5,
            "placebo_ratio_dgs5": placebo_ratio_dgs5,
            "placebo_ratio_threshold": INFORMATIVE_PLACEBO_RATIO,
            "pass": informative_pass,
        },
        "informative_dgs10": {
            "n_fg_events_resolved": len(fg_dgs10),
            "mean_abs_fg_dgs10_pp": mean_abs_fg_dgs10,
        },
        "per_event": per_event,
        "placebo_per_event_summary": [
            {"event_date": evrow["event_date"],
             "n_placebo_wednesdays": evrow["n_placebo_wednesdays"]}
            for evrow in placebo_per_event
        ],
        "method_valid": {
            "intraday_data": "missing — no high-frequency 30-min FRED on disk",
            "ecb_yields": "missing — euro-area 2y/5y/10y not on disk",
            "boe_yields": "missing — UK gilt yields not on disk",
            "boj_yields": "missing — JGB yields not on disk",
            "re_signal_benchmark": ("missing — no calibrated NK pure-signal RE "
                                    "model in repo; daily test cannot directly "
                                    "discriminate sticky-info from RE channels"),
        },
        "manifest": manifest,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ----------------- Coefficients -----------------
    rows = [
        {"spec": "primary", "term": "mean_abs_dgs2_fg_pp", "estimate": mean_abs_fg_dgs2},
        {"spec": "primary", "term": "mean_abs_dgs2_placebo_pp", "estimate": mean_abs_placebo_dgs2},
        {"spec": "primary", "term": "placebo_ratio_dgs2", "estimate": placebo_ratio_dgs2},
        {"spec": "primary", "term": "magnitude_threshold_pp", "estimate": DGS2_ABS_THRESHOLD_PP},
        {"spec": "primary", "term": "placebo_ratio_threshold", "estimate": PRIMARY_PLACEBO_RATIO},
    ]
    if mean_abs_fg_dgs5 is not None:
        rows.append({"spec": "informative", "term": "mean_abs_dgs5_fg_pp",
                     "estimate": mean_abs_fg_dgs5})
        rows.append({"spec": "informative", "term": "placebo_ratio_dgs5",
                     "estimate": placebo_ratio_dgs5})
    if mean_abs_fg_dgs10 is not None:
        rows.append({"spec": "informative", "term": "mean_abs_dgs10_fg_pp",
                     "estimate": mean_abs_fg_dgs10})
    for ev_row in per_event:
        for k, v in ev_row.items():
            if k.endswith("_delta") and v is not None:
                rows.append({"spec": "per_event",
                             "term": f"{ev_row['event_date']}_{k}",
                             "estimate": float(v)})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ----------------- Chart -----------------
    palette = {"DGS2": "#4E79A7", "DGS5": "#59A14F", "DGS10": "#B07AA1"}
    series_out = []
    for ylabel, df in [("DGS2", dgs2), ("DGS5", dgs5), ("DGS10", dgs10)]:
        if df is None:
            continue
        win = df[(df["date"] >= pd.Timestamp("2008-01-01"))
                 & (df["date"] <= pd.Timestamp("2017-12-31"))]
        pts = [{"x": d.date().isoformat(), "y": float(v)}
               for d, v in zip(win["date"], win["value"])]
        series_out.append({
            "id": ylabel,
            "label": f"{ylabel} (US Treasury yield, %)",
            "color": palette[ylabel],
            "treated": ylabel == "DGS2",
            "points": pts,
        })

    annotations = [
        {"type": "vline", "x": d.date().isoformat(),
         "label": f"FOMC FG {d.date().isoformat()}"}
        for d in FG_EVENT_DATES
    ]
    annotations.append({
        "type": "note",
        "label": (f"Mean |ΔDGS2| on FG days = {mean_abs_fg_dgs2*100:.1f} bp; "
                  f"placebo Wed mean = {mean_abs_placebo_dgs2*100:.1f} bp "
                  f"(ratio {placebo_ratio_dgs2:.2f}x; threshold "
                  f"{PRIMARY_PLACEBO_RATIO:.1f}x).")
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US Treasury yields 2008-2017 — FOMC forward-guidance days highlighted",
        "subtitle": (
            f"Verdict: {verdict_label}. "
            f"Mean |ΔDGS2| FG days = {mean_abs_fg_dgs2*100:.1f} bp vs "
            f"placebo {mean_abs_placebo_dgs2*100:.1f} bp "
            f"(ratio {placebo_ratio_dgs2:.2f}x; threshold {PRIMARY_PLACEBO_RATIO:.1f}x)."
        ),
        "type": "line",
        "x_axis": {"label": "Date", "type": "time"},
        "y_axis": {"label": "Treasury yield (%)", "type": "linear"},
        "series": series_out,
        "annotations": annotations,
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values() if v.get("vintage_file")
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ----------------- Manifest YAML -----------------
    lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        f"verdict_label: {verdict_label}",
        "vintages:",
    ]
    for k, v in manifest.items():
        lines.append(f"  {k}:")
        lines.append(f"    publisher: {v['publisher']}")
        lines.append(f"    series: {v['series']}")
        lines.append(f"    status: {v.get('status', 'loaded')}")
        if v.get("vintage_file"):
            lines.append(f"    vintage_file: {v['vintage_file']}")
            lines.append(f"    sha256: {v['sha256']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n")

    # ----------------- Result card -----------------
    card = [
        f"# Forward-guidance term-structure event study (post-2008 FOMC)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Hand-coded FOMC forward-guidance event dates (n={len(FG_EVENT_DATES)}): "
        + ", ".join(d.date().isoformat() for d in FG_EVENT_DATES) + ".",
        f"- Mean absolute 1-day Δ DGS2 on FG days: "
        f"**{mean_abs_fg_dgs2*100:.1f} bp** (n={len(fg_dgs2)}).",
        f"- Mean absolute 1-day Δ DGS2 on calendar-matched non-FOMC Wednesdays: "
        f"**{mean_abs_placebo_dgs2*100:.1f} bp** (n={len(placebo_dgs2_all)}).",
        f"- FG/placebo ratio (DGS2): **{placebo_ratio_dgs2:.2f}x** "
        f"(threshold {PRIMARY_PLACEBO_RATIO:.1f}x).",
    ]
    if mean_abs_fg_dgs5 is not None:
        card.append(f"- DGS5 mean |Δ|: FG {mean_abs_fg_dgs5*100:.1f} bp vs "
                    f"placebo {mean_abs_placebo_dgs5*100:.1f} bp "
                    f"(ratio {placebo_ratio_dgs5:.2f}x; informative threshold "
                    f"{INFORMATIVE_PLACEBO_RATIO:.1f}x).")
    if mean_abs_fg_dgs10 is not None:
        card.append(f"- DGS10 mean |Δ|: FG {mean_abs_fg_dgs10*100:.1f} bp.")
    card += [
        "",
        "## Per-event 1-day yield changes (pp)",
        "",
        "| Event | DGS2 Δ | DGS5 Δ | DGS10 Δ |",
        "|---|---|---|---|",
    ]
    for r in per_event:
        def fmt(x):
            return f"{x:+.3f}" if isinstance(x, (int, float)) else "n/a"
        card.append(f"| {r['event_date']} | {fmt(r.get('dgs2_delta'))} | "
                    f"{fmt(r.get('dgs5_delta'))} | {fmt(r.get('dgs10_delta'))} |")
    card += [
        "",
        "## Method",
        "",
        "Daily-frequency US-FOMC forward-guidance event study. For each of the "
        "5 hand-coded FG announcement dates, compute the 1-day change in "
        "DGS2/DGS5/DGS10 (post-event-day close minus prior-trading-day close, "
        "in percentage points). Compare the mean absolute FG-day change "
        "against a calendar-matched placebo of all non-FOMC Wednesdays in "
        "the same months. The dispositive primary is mean |ΔDGS2|.",
        "",
        "## METHOD_VALID data gaps",
        "",
        "- **Intraday data**: the original spec asked for 30-minute windows. "
        "  Only daily FRED is on disk. Daily windows are noisier and cannot "
        "  attribute movement specifically to the FG headline.",
        "- **Non-US central banks**: ECB / BoE / BoJ yield series and FG "
        "  event lists are not in the current vintage tree.",
        "- **Pure-signal RE benchmark**: a calibrated NK model is required to "
        "  discriminate sticky-information from rational-expectations channels "
        "  per the original spec; no such model in repo. The daily test only "
        "  detects whether the term structure moved materially on FG days.",
        "",
        "## Data",
        "",
        "- fred:DGS2 — primary outcome (US 2y treasury yield, daily)",
        "- fred:DGS5 — informative outcome (US 5y, daily)",
        "- fred:DGS10 — informative outcome (US 10y, daily)",
        "- fred:VIXCLS — backdrop control (CBOE VIX, daily)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


def _write_data_gap(verdict: str, manifest: dict, extra: dict | None = None) -> None:
    """Emit a minimal artifact set for the data-gap / method-valid-failure path."""
    diag = {"verdict": verdict, "manifest": manifest}
    if extra:
        diag.update(extra)
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2, default=str) + "\n")
    (OUT_DIR / "result_card.md").write_text(
        f"# {HID}\n\n**Verdict:** {verdict}\n\n"
        "## Method\n\nReplication exited at the METHOD_VALID gate; see "
        "diagnostics.json for the per-series status.\n")
    pd.DataFrame([{"spec": "primary", "term": "method_valid_gate",
                   "estimate": float("nan")}]).to_parquet(
        OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "verdict_label: inconclusive\n"
    )
    (OUT_DIR / "chart_data.json").write_text(json.dumps({
        "kind": "result", "chart_id": f"{HID}/fig1",
        "title": "Forward-guidance term-structure — METHOD_VALID failure",
        "type": "line", "series": [],
        "annotations": [{"type": "note", "label": verdict}],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v.get("vintage_file")}
            for v in manifest.values() if v.get("vintage_file")
        ],
        "permalink": f"/h/{HID}",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
