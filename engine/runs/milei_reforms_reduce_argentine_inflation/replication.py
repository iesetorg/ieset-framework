#!/usr/bin/env python3
"""Replication — Milei reforms reduce Argentine inflation.

Spec: hypotheses/monetary/milei_reforms_reduce_argentine_inflation.yaml v1
Position-claim: austrian #14, chicago_monetarism #14 (school predicts: supported)

Tests three pre-registered conditions on Argentine monthly CPI inflation
(INDEC IPC Nacional, level index → month-on-month % change), with the
Milei inauguration (December 2023, t=0) as the event date:

  PRIMARY 1: median(m/m inflation) over window [t+10, t+14]
             (Oct 2024 through Feb 2025) <= 5.0%.
  PRIMARY 2: median(m/m inflation) over window [t+16, t+20]
             (Apr 2025 through Aug 2025) <= 3.0%.
  PRIMARY 3: months_to_first_sub_5 (first calendar month after t=0
             whose m/m inflation falls below 5%) <= 10.

Hypothesis is SUPPORTED only if ALL THREE primaries hold. Per the
spec's `falsification.rule`, ANY single failure makes it "not
supported"; with the magnitude framing in the canonical example we
treat 1/3 holding as `partial`, and 0/3 as `refuted`. Method-validity
is method_valid iff INDEC monthly index covers t-12 through t+18 (i.e.
Dec 2022 through Jun 2025) without gaps.

Treatment date: 2023-12-10 (Milei inauguration). t=0 is the m/m change
landing in Dec 2023 (i.e. Dec 2023 / Nov 2023 - 1). This is the month
of the 54% peso devaluation; so the post-event window starts at t+1
(Jan 2024) for stabilisation timing tests.
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
HID = "milei_reforms_reduce_argentine_inflation"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Event date — Milei inauguration. t=0 is the Dec-2023 m/m print.
EVENT_YEAR = 2023
EVENT_MONTH = 12

# Falsification thresholds (from spec.falsification.threshold)
WINDOW_A_BOUNDS = (10, 14)      # months from event, inclusive
WINDOW_A_THRESHOLD = 5.0        # median m/m % must be <= 5.0
WINDOW_B_BOUNDS = (16, 20)      # months from event, inclusive
WINDOW_B_THRESHOLD = 3.0        # median m/m % must be <= 3.0
MAX_MONTHS_TO_SUB5 = 10         # first month under 5% must arrive by t+10

# Method-validity coverage requirement
COVERAGE_START = pd.Timestamp("2022-12-01")  # t-12
COVERAGE_END = pd.Timestamp("2025-06-01")    # t+18


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_glob(pub: str, glob: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(glob), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{glob}")
    return files[-1]


def event_month_offset(d: pd.Timestamp) -> int:
    """Months from event date (2023-12) to month d."""
    return (d.year - EVENT_YEAR) * 12 + (d.month - EVENT_MONTH)


def emit_data_pending(missing: str) -> None:
    reason = (
        "INDEC IPC Nacional vintage missing from local data/vintages; "
        f"expected indec:148.3_INIVELNAL_DICI_M_26 ({missing})."
    )
    verdict = "INCONCLUSIVE_DATA_PENDING"
    diagnostics = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "all_pass": False,
        "method_valid": False,
        "event_date": f"{EVENT_YEAR}-{EVENT_MONTH:02d}",
        "missing_series": ["indec:148.3_INIVELNAL_DICI_M_26"],
        "run_utc": pd.Timestamp.utcnow().isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Argentine monthly CPI inflation",
        "subtitle": reason,
        "type": "line",
        "x_axis": {"label": "Month", "type": "time"},
        "y_axis": {"label": "Monthly CPI change (%)", "type": "linear"},
        "series": [],
        "annotations": [{"type": "note", "label": reason}],
        "sources": [],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [
            {
                "spec": "data_gate",
                "term": "missing_series",
                "estimate": np.nan,
                "note": "indec:148.3_INIVELNAL_DICI_M_26",
            }
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "status: INCONCLUSIVE_DATA_PENDING\n"
        f"reason: {json.dumps(reason)}\n"
        "runner: engine/runs/milei_reforms_reduce_argentine_inflation/replication.py\n"
        "missing_series:\n"
        "  - indec:148.3_INIVELNAL_DICI_M_26\n"
        "vintages:\n"
        "  indec_ipc_monthly_index:\n"
        "    publisher: indec\n"
        "    series: 148.3_INIVELNAL_DICI_M_26\n"
        "    vintage_file: data/vintages/indec/148.3_INIVELNAL_DICI_M_26@*.parquet\n"
    )

    card = [
        "# Milei reforms reduce Argentine inflation",
        "",
        f"**Verdict:** {verdict} - {reason}",
        "",
        "## Data Gate",
        "",
        "- Required local vintage: `data/vintages/indec/148.3_INIVELNAL_DICI_M_26@*.parquet`.",
        "- The current workspace does not contain an `indec` vintage directory or matching INDEC IPC file.",
        "- The prior supported result cannot be reproduced in this lane without the registered INDEC input.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # INDEC IPC Nacional — series 148.3_INIVELNAL_DICI_M_26 is the
    # monthly index level (Dec 2016 = 100).
    try:
        indec_path = latest_glob("indec", "148.3_INIVELNAL_DICI_M_26@*.parquet")
    except FileNotFoundError as exc:
        emit_data_pending(str(exc))
        print(
            "verdict: INCONCLUSIVE_DATA_PENDING - "
            "missing indec:148.3_INIVELNAL_DICI_M_26"
        )
        return

    manifest = {
        "indec_ipc_monthly_index": {
            "publisher": "indec",
            "series": "148.3_INIVELNAL_DICI_M_26",
            "vintage_file": str(indec_path.relative_to(REPO_ROOT)),
            "sha256": sha256(indec_path),
        },
    }

    raw = pq.read_table(indec_path).to_pandas()
    if "date" not in raw.columns or "value" not in raw.columns:
        raise ValueError(f"INDEC schema unexpected: {list(raw.columns)}")

    raw["date"] = pd.to_datetime(raw["date"])
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw.dropna(subset=["value"]).sort_values("date").reset_index(drop=True)

    # Compute month-on-month % change
    raw["mom_pct"] = raw["value"].pct_change() * 100.0
    raw["t"] = raw["date"].apply(event_month_offset)

    # ---------- Method-validity check ----------
    coverage_ok = (
        (raw["date"].min() <= COVERAGE_START)
        and (raw["date"].max() >= COVERAGE_END)
        and not raw[raw["date"].between(COVERAGE_START, COVERAGE_END)]["value"].isna().any()
    )

    # ---------- PRIMARY 1: window [t+10, t+14] median ----------
    win_a = raw[raw["t"].between(WINDOW_A_BOUNDS[0], WINDOW_A_BOUNDS[1])]
    median_a = float(win_a["mom_pct"].median()) if len(win_a) else float("nan")
    p1_pass = (not np.isnan(median_a)) and (median_a <= WINDOW_A_THRESHOLD)
    win_a_max = float(win_a["mom_pct"].max()) if len(win_a) else float("nan")

    # ---------- PRIMARY 2: window [t+16, t+20] median ----------
    win_b = raw[raw["t"].between(WINDOW_B_BOUNDS[0], WINDOW_B_BOUNDS[1])]
    median_b = float(win_b["mom_pct"].median()) if len(win_b) else float("nan")
    p2_pass = (not np.isnan(median_b)) and (median_b <= WINDOW_B_THRESHOLD)
    win_b_max = float(win_b["mom_pct"].max()) if len(win_b) else float("nan")

    # ---------- PRIMARY 3: months_to_first_sub_5 ----------
    post = raw[raw["t"] >= 1].sort_values("t")  # post-event months only
    months_to_sub5 = None
    for _, row in post.iterrows():
        if row["mom_pct"] < 5.0:
            months_to_sub5 = int(row["t"])
            break
    p3_pass = (months_to_sub5 is not None) and (months_to_sub5 <= MAX_MONTHS_TO_SUB5)

    # ---------- Verdict aggregation ----------
    n_pass = int(p1_pass) + int(p2_pass) + int(p3_pass)

    # Pre-Milei reference: median m/m inflation over t-12 to t-1 (Dec 2022-Nov 2023)
    pre = raw[raw["t"].between(-11, 0)]
    pre_median = float(pre["mom_pct"].median()) if len(pre) else float("nan")
    # Peak m/m inflation in t=0 month (Dec 2023, the devaluation print)
    t0_row = raw[raw["t"] == 0]
    t0_mom = float(t0_row["mom_pct"].iloc[0]) if len(t0_row) else float("nan")

    if not coverage_ok:
        verdict = (
            f"inconclusive — INDEC IPC monthly index does not span "
            f"{COVERAGE_START.date()} → {COVERAGE_END.date()} without gaps; "
            f"method_valid gate fails."
        )
    elif n_pass == 3:
        verdict = (
            f"SUPPORTED — All three pre-registered tests hold. "
            f"Median m/m inflation Oct'24-Feb'25 = {median_a:.2f}% "
            f"(<= {WINDOW_A_THRESHOLD:.1f}%); Apr-Aug'25 = {median_b:.2f}% "
            f"(<= {WINDOW_B_THRESHOLD:.1f}%); first sub-5% m/m print at "
            f"t+{months_to_sub5} (<= t+{MAX_MONTHS_TO_SUB5}). "
            f"Pre-Milei median m/m {pre_median:.2f}% → t=0 print "
            f"{t0_mom:.2f}% → stabilisation as predicted."
        )
    elif n_pass == 0:
        verdict = (
            f"refuted — None of the three pre-registered tests hold. "
            f"Median Oct'24-Feb'25 m/m = {median_a:.2f}% (threshold "
            f"{WINDOW_A_THRESHOLD:.1f}%); Apr-Aug'25 = {median_b:.2f}% "
            f"(threshold {WINDOW_B_THRESHOLD:.1f}%); first sub-5% at "
            f"t+{months_to_sub5 if months_to_sub5 is not None else 'never'} "
            f"(threshold t+{MAX_MONTHS_TO_SUB5})."
        )
    else:
        which = []
        if p1_pass:
            which.append(f"window-A median {median_a:.2f}% <= {WINDOW_A_THRESHOLD:.1f}%")
        else:
            which.append(f"window-A median {median_a:.2f}% > {WINDOW_A_THRESHOLD:.1f}% [FAIL]")
        if p2_pass:
            which.append(f"window-B median {median_b:.2f}% <= {WINDOW_B_THRESHOLD:.1f}%")
        else:
            which.append(f"window-B median {median_b:.2f}% > {WINDOW_B_THRESHOLD:.1f}% [FAIL]")
        if p3_pass:
            which.append(f"first sub-5% at t+{months_to_sub5}")
        else:
            mts = months_to_sub5 if months_to_sub5 is not None else "never"
            which.append(f"first sub-5% at t+{mts} > t+{MAX_MONTHS_TO_SUB5} [FAIL]")
        verdict = (
            f"partial — {n_pass} of 3 pre-registered tests hold. "
            + "; ".join(which) + "."
        )

    diagnostics = {
        "verdict": verdict,
        "n_pass": n_pass,
        "all_pass": n_pass == 3,
        "method_valid": bool(coverage_ok),
        "primary1_window_a_median_pass": bool(p1_pass),
        "primary2_window_b_median_pass": bool(p2_pass),
        "primary3_months_to_sub5_pass": bool(p3_pass),
        "window_a_bounds_months_from_event": list(WINDOW_A_BOUNDS),
        "window_a_threshold_pct": WINDOW_A_THRESHOLD,
        "window_a_median_pct": median_a,
        "window_a_max_pct": win_a_max,
        "window_a_n_obs": int(len(win_a)),
        "window_b_bounds_months_from_event": list(WINDOW_B_BOUNDS),
        "window_b_threshold_pct": WINDOW_B_THRESHOLD,
        "window_b_median_pct": median_b,
        "window_b_max_pct": win_b_max,
        "window_b_n_obs": int(len(win_b)),
        "max_months_to_sub5": MAX_MONTHS_TO_SUB5,
        "months_to_first_sub5": months_to_sub5,
        "pre_milei_median_mom_pct": pre_median,
        "event_month_mom_pct": t0_mom,
        "event_date": f"{EVENT_YEAR}-{EVENT_MONTH:02d}",
        "data_first_date": str(raw["date"].min().date()),
        "data_last_date": str(raw["date"].max().date()),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    pts = [
        {"x": d.strftime("%Y-%m"), "y": float(v)}
        for d, v in zip(raw["date"], raw["mom_pct"])
        if not pd.isna(v)
    ]
    series = [
        {
            "id": "ARG_MOM_CPI",
            "label": "Argentina monthly CPI inflation (m/m %)",
            "color": "#4E79A7",
            "treated": True,
            "points": pts,
        },
        {
            "id": "THRESH_5",
            "label": "5% m/m threshold (window A: t+10..t+14)",
            "color": "#E15759",
            "treated": False,
            "points": [
                {"x": d.strftime("%Y-%m"), "y": 5.0}
                for d in raw["date"]
            ],
        },
        {
            "id": "THRESH_3",
            "label": "3% m/m threshold (window B: t+16..t+20)",
            "color": "#F28E2B",
            "treated": False,
            "points": [
                {"x": d.strftime("%Y-%m"), "y": 3.0}
                for d in raw["date"]
            ],
        },
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Argentine monthly CPI inflation, 2017-2026 (INDEC IPC Nacional)",
        "subtitle": (
            f"t=0: Dec 2023 Milei inauguration (m/m = {t0_mom:.1f}% post-devaluation). "
            f"Window A median {median_a:.2f}% vs 5.0% threshold; "
            f"window B median {median_b:.2f}% vs 3.0% threshold; "
            f"first sub-5% at t+{months_to_sub5}."
        ),
        "type": "line",
        "x_axis": {"label": "Month", "type": "time"},
        "y_axis": {"label": "Monthly CPI change (%)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vertical_line",
                "x": "2023-12",
                "label": "Milei inauguration (t=0)",
            },
            {
                "type": "note",
                "label": (
                    f"Pre-Milei median m/m (t-11..t=0): {pre_median:.2f}%. "
                    f"Window A [Oct'24..Feb'25] median: {median_a:.2f}% "
                    f"({'pass' if p1_pass else 'fail'}). "
                    f"Window B [Apr'25..Aug'25] median: {median_b:.2f}% "
                    f"({'pass' if p2_pass else 'fail'}). "
                    f"First m/m < 5% at t+{months_to_sub5} "
                    f"({'pass' if p3_pass else 'fail'})."
                ),
            }
        ],
        "sources": [
            {
                "publisher_id": v["publisher"],
                "series_id": v["series"],
                "vintage_file": v["vintage_file"],
            }
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients ----------
    coef_rows = [
        {"spec": "primary1", "term": "window_a_median_mom_pct", "estimate": median_a},
        {"spec": "primary1", "term": "window_a_threshold_pct", "estimate": WINDOW_A_THRESHOLD},
        {"spec": "primary2", "term": "window_b_median_mom_pct", "estimate": median_b},
        {"spec": "primary2", "term": "window_b_threshold_pct", "estimate": WINDOW_B_THRESHOLD},
        {
            "spec": "primary3",
            "term": "months_to_first_sub5",
            "estimate": float(months_to_sub5) if months_to_sub5 is not None else float("nan"),
        },
        {
            "spec": "primary3",
            "term": "max_months_to_sub5_threshold",
            "estimate": float(MAX_MONTHS_TO_SUB5),
        },
        {"spec": "context", "term": "pre_milei_median_mom_pct", "estimate": pre_median},
        {"spec": "context", "term": "event_month_mom_pct", "estimate": t0_mom},
    ]
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Manifest ----------
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
        f"# Milei reforms reduce Argentine inflation",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Event date: {EVENT_YEAR}-{EVENT_MONTH:02d} (Milei inauguration); "
        f"t=0 m/m print = {t0_mom:.2f}% (post 54% peso devaluation).",
        f"- Pre-Milei median m/m inflation (t-11 through t=0): "
        f"**{pre_median:.2f}%/month**.",
        f"- **Primary 1** — window [t+10, t+14] (Oct 2024 - Feb 2025) "
        f"median m/m: **{median_a:.2f}%** "
        f"(threshold ≤ {WINDOW_A_THRESHOLD:.1f}%). "
        f"{'PASS' if p1_pass else 'FAIL'}.",
        f"- **Primary 2** — window [t+16, t+20] (Apr 2025 - Aug 2025) "
        f"median m/m: **{median_b:.2f}%** "
        f"(threshold ≤ {WINDOW_B_THRESHOLD:.1f}%). "
        f"{'PASS' if p2_pass else 'FAIL'}.",
        f"- **Primary 3** — months from inauguration to first m/m < 5%: "
        f"**t+{months_to_sub5 if months_to_sub5 is not None else '∞'}** "
        f"(threshold ≤ t+{MAX_MONTHS_TO_SUB5}). "
        f"{'PASS' if p3_pass else 'FAIL'}.",
        f"- Method validity (INDEC monthly coverage Dec 2022 → Jun 2025 "
        f"without gaps): {'OK' if coverage_ok else 'FAIL'}.",
        "",
        "## Method",
        "",
        "Event-study presentation around the December 2023 Milei "
        "inauguration. INDEC IPC Nacional monthly index level "
        "(Dec 2016 = 100, series 148.3_INIVELNAL_DICI_M_26) is "
        "transformed to month-on-month percent change. The three "
        "pre-registered tests in the spec's "
        "`falsification.threshold` block are evaluated literally: "
        "window-A median ≤ 5%, window-B median ≤ 3%, and "
        "months-to-first-sub-5%-print ≤ 10. Verdict aggregates the "
        "three: 3/3 = SUPPORTED, 0/3 = refuted, 1-2/3 = partial. "
        "Method-valid gate requires gap-free INDEC coverage from "
        "t-12 through t+18.",
        "",
        "Synthetic-control LatAm peer comparison and local-projection "
        "robustness (mentioned in `estimator.notes`) are deferred to "
        "v2; the three-threshold dispositive test is binding for v1 "
        "per the explicit pre-registration in `falsification.threshold`.",
        "",
        "## Data",
        "",
        f"- indec:148.3_INIVELNAL_DICI_M_26 (monthly IPC Nacional "
        f"index level, Dec 2016 = 100; coverage "
        f"{raw['date'].min().date()} → {raw['date'].max().date()}).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
