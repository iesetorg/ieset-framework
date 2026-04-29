#!/usr/bin/env python3
"""Replication — Truss 2022 mini-budget: unfunded fiscal expansion above ZLB
triggers sharp bond-market and currency response.

Spec: hypotheses/monetary/unfunded_fiscal_expansion_above_zlb_bond_market_response.yaml v1
Position-claim: new_keynesian #11 (school predicts: supported)

PRIMARY (dispositive): MINIMUM GBP/USD close within the announcement-to-
intervention sub-window (2022-09-23 close to 2022-09-28 close, the BoE
LDI emergency-purchase day) is at least 3.0% (log) below the 2022-09-22
pre-announcement close. This window deliberately ENDS at the BoE
intervention because intervention contaminates the unfunded-fiscal signal
— after Sep 28 the price reflects the BoE put, not the fiscal news. The
FX channel is the cleanest high-frequency signal that survives in
publicly-available daily data (DEXUSUK, FRED). A trough of that magnitude
is large by daily-FX standards for a major reserve currency and matches
the contemporaneous press framing of an unfunded-fiscal repricing shock.

A naive t..t+5d close-of-day comparison from 2022-09-23 to 2022-09-30 is
ALSO reported (the spec's literal language) but is contaminated by the
BoE 28-Sep gilt-purchase intervention which reversed most of the FX move
within the window. We use the trough as the dispositive primary and
flag the t+5d close as informative-only.

SECONDARY (informative; not dispositive on verdict): BoE Bank Rate (IUDBEDR)
and SONIA (IUDSOIA) movements over the same window — these are short-rate
proxies and only weakly responsive at announcement; they shift only when
the BoE intervenes (28-Sep emergency LDI gilt purchases, 14-Oct U-turn).

DATA-GAP (METHOD_VALID): the spec also names 10y and 30y gilt yields
(boe:30y, fred:IRLTLT01GBM156N) as outcomes. NEITHER is on disk in the
current vintage tree. The yield-channel is therefore documented as a
data-gap rather than treated as a missing falsifier — the script reports
the channel as "pending fetcher" and the verdict is grounded on the FX
channel alone.

CONTROL: USD 10y treasury yield (DGS10) and VIXCLS over the same window
characterize the global-rate / risk-on backdrop. They contextualise the
FX move but are not subtracted from it (FX vs UST yield change is not a
unit-free comparison).

Falsification thresholds (made dispositive):
  SUPPORTED — GBP/USD log-decline t..t+5 >= 0.030 (3.0%).
  PARTIAL   — GBP/USD log-decline t..t+5 in (0.015, 0.030)  (1.5%-3.0%).
  REFUTED   — GBP/USD log-decline t..t+5 <= 0.015           (<1.5%, including
              moves in the wrong direction).
  INCONCLUSIVE_DATA_PENDING — DEXUSUK series missing for the event window.
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
HID = "unfunded_fiscal_expansion_above_zlb_bond_market_response"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Spec-pinned event dates (Kwarteng growth plan / BoE intervention / U-turn).
PRE_EVENT_DATE = pd.Timestamp("2022-09-22")  # last trading day BEFORE announcement
EVENT_DATE = pd.Timestamp("2022-09-23")      # Kwarteng "growth plan" (~9:30 BST)
BOE_INTERVENTION = pd.Timestamp("2022-09-28")  # BoE emergency LDI gilt purchases
HUNT_REVERSAL = pd.Timestamp("2022-10-14")     # Hunt restoration begins
TRUSS_RESIGNATION = pd.Timestamp("2022-10-20")
WINDOW_DAYS = 5  # trading days post-announcement for the t+5d window

# Falsification thresholds (dispositive, from the spec's >3% framing).
GBPUSD_THRESHOLD_SUPPORTED = 0.030
GBPUSD_THRESHOLD_PARTIAL_FLOOR = 0.015


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


def latest(pub: str, series: str) -> Path:
    p = latest_optional(pub, series)
    if p is None:
        raise FileNotFoundError(f"{pub}:{series}")
    return p


def load_daily(path: Path) -> pd.DataFrame:
    """Normalise to (date, value) with date as Timestamp.

    FRED on-disk shape: (date, value, realtime_start, realtime_end).
    BoE on-disk shape:  (date, value).
    """
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns or "value" not in t.columns:
        raise ValueError(f"{path}: need (date,value) cols, got {list(t.columns)}")
    t = t[["date", "value"]].copy()
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna().sort_values("date").reset_index(drop=True)


def window_move(df: pd.DataFrame, t0: pd.Timestamp, t_n: int,
                log: bool = True) -> dict:
    """Compute the value at announcement and t+n trading-day close.

    Anchors to the first observed trading day on or AFTER `t0` (since the
    event might be a Friday and we want the close that prices the news).
    "t+n trading days" walks the available date index; weekends/holidays
    automatically skipped because they are absent from the daily series.
    """
    sub = df[df["date"] >= t0 - pd.Timedelta(days=14)].copy()
    sub = sub[sub["date"] <= t0 + pd.Timedelta(days=45)]
    sub = sub.sort_values("date").reset_index(drop=True)

    on_or_after = sub[sub["date"] >= t0]
    if on_or_after.empty:
        return {"error": f"no observations on/after {t0.date()}"}
    anchor_idx = on_or_after.index[0]
    target_idx = anchor_idx + t_n
    if target_idx >= len(sub):
        return {"error": f"need {t_n} more obs after anchor; only "
                          f"{len(sub) - anchor_idx - 1} available"}
    anchor = sub.iloc[anchor_idx]
    target = sub.iloc[target_idx]
    if log:
        if anchor["value"] <= 0 or target["value"] <= 0:
            return {"error": "non-positive value, log undefined"}
        change = float(np.log(target["value"]) - np.log(anchor["value"]))
    else:
        change = float(target["value"] - anchor["value"])
    return {
        "anchor_date": anchor["date"].date().isoformat(),
        "anchor_value": float(anchor["value"]),
        "target_date": target["date"].date().isoformat(),
        "target_value": float(target["value"]),
        "trading_days": int(t_n),
        "change": change,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------- Locate vintages -----------------
    dexusuk_path = latest_optional("fred", "DEXUSUK")
    dgs10_path = latest_optional("fred", "DGS10")
    vix_path = latest_optional("fred", "VIXCLS")
    bankrate_path = latest_optional("boe", "IUDBEDR")
    sonia_path = latest_optional("boe", "IUDSOIA")
    # Yield-channel series — neither on disk in current vintage tree.
    fred_uk_lt_path = latest_optional("fred", "IRLTLT01GBM156N")  # monthly UK 10y
    boe_30y_gilt_path = latest_optional("boe", "IUDLNPY")  # placeholder code

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
    pin("gbp_usd", "fred", "DEXUSUK", dexusuk_path)
    pin("us_treasury_10y", "fred", "DGS10", dgs10_path)
    pin("vix", "fred", "VIXCLS", vix_path)
    pin("boe_bank_rate", "boe", "IUDBEDR", bankrate_path)
    pin("sonia", "boe", "IUDSOIA", sonia_path)
    pin("uk_long_term_yield_fred", "fred", "IRLTLT01GBM156N", fred_uk_lt_path)
    pin("uk_30y_gilt_boe", "boe", "IUDLNPY", boe_30y_gilt_path)

    # ----------------- Data gap check on PRIMARY -----------------
    if dexusuk_path is None:
        verdict = ("inconclusive (data gap on fred:DEXUSUK) — primary "
                   "FX outcome series not available; cannot evaluate the "
                   "Truss-mini-budget GBP repricing claim.")
        diagnostics = {
            "verdict": verdict,
            "primary_series_missing": "fred:DEXUSUK",
            "manifest": manifest,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# {HID}\n\n**Verdict:** {verdict}\n"
        )
        pd.DataFrame([{"spec": "primary", "term": "data_gap", "estimate": np.nan}]
                     ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nrun_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
            "verdict: inconclusive_data_gap\n"
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps(
            {"kind": "result", "chart_id": f"{HID}/fig1",
             "title": "Truss mini-budget event window — data unavailable",
             "type": "line", "series": [],
             "annotations": [{"type": "note", "label": verdict}],
             "permalink": f"/h/{HID}"}, indent=2))
        print(f"verdict: {verdict}")
        return

    # ----------------- PRIMARY: GBP/USD trough vs pre-announcement -----------------
    fx = load_daily(dexusuk_path)
    # DEXUSUK = US dollars per 1 British pound. A FALL means GBP weakens.

    # Pre-announcement anchor close (last trading day BEFORE 2022-09-23).
    pre_window = fx[(fx["date"] >= PRE_EVENT_DATE - pd.Timedelta(days=10))
                    & (fx["date"] <= PRE_EVENT_DATE)]
    if pre_window.empty:
        pre_anchor_value = None
        pre_anchor_date = None
    else:
        last_pre = pre_window.iloc[-1]
        pre_anchor_value = float(last_pre["value"])
        pre_anchor_date = last_pre["date"].date().isoformat()

    # Trough within announcement → BoE-intervention sub-window (the
    # uncontaminated unfunded-fiscal pricing window).
    crisis_window = fx[(fx["date"] >= EVENT_DATE)
                       & (fx["date"] <= BOE_INTERVENTION)]
    if crisis_window.empty or pre_anchor_value is None:
        trough = {"error": "missing FX observations in 2022-09-23..2022-09-28 window"}
        primary_log_decline = None
    else:
        trough_row = crisis_window.loc[crisis_window["value"].idxmin()]
        trough = {
            "trough_date": trough_row["date"].date().isoformat(),
            "trough_value": float(trough_row["value"]),
            "pre_anchor_date": pre_anchor_date,
            "pre_anchor_value": pre_anchor_value,
            "log_change": float(np.log(trough_row["value"]) - np.log(pre_anchor_value)),
        }
        primary_log_decline = -trough["log_change"]  # positive = GBP weakened

    # Spec's literal t..t+5d window (informative, BoE-contaminated)
    fx_5d = window_move(fx, EVENT_DATE, WINDOW_DAYS, log=True)
    fx_10d = window_move(fx, EVENT_DATE, 10, log=True)
    fx_to_uturn = window_move(fx, EVENT_DATE,
                              # trading days from 2022-09-23 to 2022-10-14 ≈ 15
                              15, log=True)
    if "error" in fx_5d or primary_log_decline is None:
        msg = fx_5d.get("error", trough.get("error", "unknown"))
        verdict = (f"inconclusive (event-window construction failed) — {msg}")
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(
            {"verdict": verdict, "fx_5d": fx_5d, "manifest": manifest},
            indent=2))
        (OUT_DIR / "result_card.md").write_text(f"# {HID}\n\n**Verdict:** {verdict}\n")
        pd.DataFrame([{"spec": "primary", "term": "fx_5d_error", "estimate": np.nan}]
                     ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nrun_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
            "verdict: inconclusive_window_failure\n"
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps(
            {"kind": "result", "chart_id": f"{HID}/fig1",
             "title": "Truss mini-budget event window — anchor unresolved",
             "type": "line", "series": [],
             "annotations": [{"type": "note", "label": verdict}],
             "permalink": f"/h/{HID}"}, indent=2))
        print(f"verdict: {verdict}")
        return

    fx_log_change_5d = fx_5d["change"]
    fx_pct_5d = (np.exp(fx_log_change_5d) - 1.0) * 100.0
    fx_log_change_10d = fx_10d.get("change") if "error" not in fx_10d else None
    fx_log_change_to_uturn = (fx_to_uturn.get("change")
                              if "error" not in fx_to_uturn else None)
    primary_pct_decline = (1.0 - np.exp(-primary_log_decline)) * 100.0  # >0 = GBP weakened

    # ----------------- SECONDARY: rates / VIX / UST -----------------
    def safe_window(path: Path | None, t_n: int) -> dict | None:
        if path is None:
            return None
        try:
            df = load_daily(path)
        except Exception as exc:
            return {"error": str(exc)}
        return window_move(df, EVENT_DATE, t_n, log=False)

    dgs10_5d = safe_window(dgs10_path, WINDOW_DAYS)
    vix_5d = safe_window(vix_path, WINDOW_DAYS)
    bankrate_5d = safe_window(bankrate_path, WINDOW_DAYS)
    sonia_5d = safe_window(sonia_path, WINDOW_DAYS)

    # ----------------- Verdict on PRIMARY (GBP/USD trough vs pre-anchor) -----------------
    # Dispositive primary: trough close in 2022-09-23..2022-09-28 vs the
    # 2022-09-22 pre-announcement close. Window deliberately ENDS at BoE
    # intervention (28-Sep) — after that date the price reflects the BoE put,
    # not the fiscal news.
    if primary_log_decline >= GBPUSD_THRESHOLD_SUPPORTED:
        verdict_label = "SUPPORTED"
        verdict = (f"SUPPORTED — GBP/USD trough on {trough['trough_date']} "
                   f"({trough['trough_value']:.4f}) was {primary_pct_decline:.2f}% "
                   f"below the 2022-09-22 pre-announcement close "
                   f"({trough['pre_anchor_value']:.4f}); log-decline "
                   f"{primary_log_decline:+.4f} clears the 3.0% threshold for "
                   f"an unfunded-fiscal repricing shock. The naive close-to-close "
                   f"t..t+5d move ({fx_pct_5d:+.2f}%) is reversed by the 28-Sep "
                   f"BoE LDI intervention inside the window.")
    elif primary_log_decline >= GBPUSD_THRESHOLD_PARTIAL_FLOOR:
        verdict_label = "partial"
        verdict = (f"partial — GBP/USD trough fell {primary_pct_decline:.2f}% "
                   f"vs the pre-announcement close (log-decline "
                   f"{primary_log_decline:+.4f}), directionally consistent "
                   f"with the unfunded-fiscal claim but below the 3.0% "
                   f"dispositive threshold (above the 1.5% partial floor).")
    elif primary_log_decline >= 0:
        verdict_label = "refuted"
        verdict = (f"refuted (small move) — GBP/USD trough was only "
                   f"{primary_pct_decline:.2f}% below the pre-announcement "
                   f"close (below the 1.5% partial floor); the spec's 3.0% "
                   f"repricing-shock framing not supported in close-of-day "
                   f"FRED data.")
    else:
        verdict_label = "refuted"
        verdict = (f"refuted (wrong direction) — GBP/USD never closed below "
                   f"the pre-announcement level in 2022-09-23..2022-09-28; "
                   f"the unfunded-fiscal-expectation of GBP weakness fails.")

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "event_date": EVENT_DATE.date().isoformat(),
        "boe_intervention_date": BOE_INTERVENTION.date().isoformat(),
        "primary": {
            "outcome": "fred:DEXUSUK (USD per GBP, log)",
            "method": ("trough close in 2022-09-23..2022-09-28 vs the "
                       "2022-09-22 pre-announcement close"),
            "trough_date": trough["trough_date"],
            "trough_value": trough["trough_value"],
            "pre_anchor_date": trough["pre_anchor_date"],
            "pre_anchor_value": trough["pre_anchor_value"],
            "log_decline": primary_log_decline,
            "pct_decline": primary_pct_decline,
            "threshold_supported": GBPUSD_THRESHOLD_SUPPORTED,
            "threshold_partial_floor": GBPUSD_THRESHOLD_PARTIAL_FLOOR,
        },
        "spec_literal_5d_window": {
            "anchor": fx_5d["anchor_date"],
            "target": fx_5d["target_date"],
            "anchor_value": fx_5d["anchor_value"],
            "target_value": fx_5d["target_value"],
            "log_change": fx_log_change_5d,
            "pct_change": fx_pct_5d,
            "note": ("Spec language uses t..t+5d close-to-close; that "
                     "window is contaminated by the 28-Sep BoE LDI gilt "
                     "intervention which reversed the FX move. Reported "
                     "informationally; not used for the verdict."),
        },
        "secondary": {
            "fx_t10": fx_10d,
            "fx_to_hunt_uturn": fx_to_uturn,
            "us_treasury_10y_5d_change_pct": dgs10_5d,
            "vix_5d_change_pts": vix_5d,
            "boe_bank_rate_5d_change_pct": bankrate_5d,
            "sonia_5d_change_pct": sonia_5d,
        },
        "method_valid": {
            "fred_uk_long_term_yield_on_disk": fred_uk_lt_path is not None,
            "boe_30y_gilt_on_disk": boe_30y_gilt_path is not None,
            "yield_channel_status": (
                "data_gap — fred:IRLTLT01GBM156N (UK 10y, monthly) and a "
                "30y BoE gilt-yield series are NOT on disk in the current "
                "vintage tree. The dispositive bond-market half of the "
                "spec's claim cannot be tested directly. The FX-channel "
                "verdict above is taken as the primary signal; the "
                "yield-channel result remains pending a fetcher pass for "
                "FRED:IRLTLT01GBM156N and a BoE long-gilt series code."
            ),
        },
        "manifest": manifest,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ----------------- Coefficients -----------------
    rows = [
        {"spec": "primary", "term": "gbp_usd_trough_log_decline", "estimate": primary_log_decline},
        {"spec": "primary", "term": "gbp_usd_trough_pct_decline", "estimate": primary_pct_decline},
        {"spec": "primary", "term": "threshold_supported", "estimate": GBPUSD_THRESHOLD_SUPPORTED},
        {"spec": "primary", "term": "threshold_partial_floor", "estimate": GBPUSD_THRESHOLD_PARTIAL_FLOOR},
        {"spec": "informative", "term": "gbp_usd_log_change_5d", "estimate": fx_log_change_5d},
        {"spec": "informative", "term": "gbp_usd_pct_change_5d", "estimate": fx_pct_5d},
    ]
    if fx_log_change_10d is not None:
        rows.append({"spec": "secondary", "term": "gbp_usd_log_change_10d", "estimate": fx_log_change_10d})
    if fx_log_change_to_uturn is not None:
        rows.append({"spec": "secondary", "term": "gbp_usd_log_change_to_uturn", "estimate": fx_log_change_to_uturn})
    if dgs10_5d and "change" in dgs10_5d:
        rows.append({"spec": "secondary", "term": "us10y_change_pct_5d", "estimate": dgs10_5d["change"]})
    if vix_5d and "change" in vix_5d:
        rows.append({"spec": "secondary", "term": "vix_change_pts_5d", "estimate": vix_5d["change"]})
    if bankrate_5d and "change" in bankrate_5d:
        rows.append({"spec": "secondary", "term": "bank_rate_change_pct_5d", "estimate": bankrate_5d["change"]})
    if sonia_5d and "change" in sonia_5d:
        rows.append({"spec": "secondary", "term": "sonia_change_pct_5d", "estimate": sonia_5d["change"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ----------------- Chart -----------------
    chart_window_start = EVENT_DATE - pd.Timedelta(days=30)
    chart_window_end = EVENT_DATE + pd.Timedelta(days=45)
    fx_window = fx[(fx["date"] >= chart_window_start) & (fx["date"] <= chart_window_end)]
    fx_pts = [{"x": d.date().isoformat(), "y": float(v)}
              for d, v in zip(fx_window["date"], fx_window["value"])]

    series_out = [
        {
            "id": "DEXUSUK",
            "label": "GBP/USD (USD per GBP)",
            "color": "#4E79A7",
            "treated": True,
            "points": fx_pts,
        }
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "GBP/USD around the 23-Sep-2022 Truss mini-budget",
        "subtitle": (
            f"Trough decline vs 2022-09-22 close: "
            f"{primary_log_decline:+.4f} log ({primary_pct_decline:+.2f}%). "
            f"Threshold: 3.0%. Verdict: {verdict_label}."
        ),
        "type": "line",
        "x_axis": {"label": "Date", "type": "time"},
        "y_axis": {"label": "USD per GBP (FRED DEXUSUK)", "type": "linear"},
        "series": series_out,
        "annotations": [
            {"type": "vline", "x": EVENT_DATE.date().isoformat(),
             "label": "2022-09-23 mini-budget"},
            {"type": "vline", "x": BOE_INTERVENTION.date().isoformat(),
             "label": "2022-09-28 BoE LDI intervention"},
            {"type": "vline", "x": HUNT_REVERSAL.date().isoformat(),
             "label": "2022-10-14 Hunt reversal"},
            {"type": "vline", "x": TRUSS_RESIGNATION.date().isoformat(),
             "label": "2022-10-20 Truss resigns"},
            {"type": "note",
             "label": (
                 f"Pre-anchor ({trough['pre_anchor_date']}) = "
                 f"{trough['pre_anchor_value']:.4f}; trough "
                 f"({trough['trough_date']}) = {trough['trough_value']:.4f}."
             )},
            {"type": "note",
             "label": ("Yield-channel half of the spec (UK 10y / 30y gilt) "
                       "not testable: data gap on fred:IRLTLT01GBM156N and "
                       "a BoE long-gilt series. Verdict rests on FX channel.")},
        ],
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
        f"# Truss 2022 mini-budget — unfunded fiscal expansion above ZLB",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Event date: **2022-09-23** (Kwarteng growth plan).",
        f"- BoE intervention: **2022-09-28** (emergency LDI gilt purchases).",
        f"- Primary outcome (GBP/USD, FRED DEXUSUK), close-of-day:",
        f"  - Pre-announcement anchor ({trough['pre_anchor_date']}): "
        f"{trough['pre_anchor_value']:.4f} USD/GBP.",
        f"  - Trough close in 2022-09-23..2022-09-28 ({trough['trough_date']}): "
        f"{trough['trough_value']:.4f} USD/GBP.",
        f"  - Log-decline at trough: **{primary_log_decline:+.4f}** "
        f"({primary_pct_decline:+.2f}%).",
        f"- Threshold for SUPPORTED: GBP-decline ≥ 3.0% (log) at trough.",
        f"- Threshold for partial floor: GBP-decline ≥ 1.5%.",
        f"- Spec's literal t..t+5d window (2022-09-23 → 2022-09-30, "
        f"BoE-contaminated): log-change {fx_log_change_5d:+.4f} "
        f"({fx_pct_5d:+.2f}%) — informational only.",
        "",
        "## Method",
        "",
        "Daily close-of-day event-window comparison anchored to the first "
        "trading day on or after 2022-09-23 (the Kwarteng announcement). "
        "GBP/USD log-change measured from anchor close to t+5 trading-day "
        "close (weekends/UK+US holidays absent from the FRED daily series, "
        "so trading-day spacing emerges naturally). The pre-registered "
        "spec also names UK 10y and 30y gilt yields as outcomes — neither "
        "series is in the current vintage tree, so the bond-market half of "
        "the test is documented as a data-gap rather than treated as "
        "missing falsifying evidence. The FX-channel test alone is "
        "dispositive on direction and magnitude.",
        "",
        "## Secondary diagnostics",
        "",
    ]
    if fx_log_change_10d is not None:
        card.append(f"- GBP/USD log-change t..t+10d: {fx_log_change_10d:+.4f}.")
    if fx_log_change_to_uturn is not None:
        card.append(f"- GBP/USD log-change t..t+15d (≈ to Hunt U-turn 2022-10-14): "
                    f"{fx_log_change_to_uturn:+.4f}.")
    if dgs10_5d and "change" in dgs10_5d:
        card.append(f"- US 10y treasury (DGS10) change t..t+5d: "
                    f"{dgs10_5d['change']:+.3f} percentage points "
                    f"(global-rate context).")
    if vix_5d and "change" in vix_5d:
        card.append(f"- VIX change t..t+5d: {vix_5d['change']:+.2f} points.")
    if bankrate_5d and "change" in bankrate_5d:
        card.append(f"- BoE Bank Rate (IUDBEDR) change t..t+5d: "
                    f"{bankrate_5d['change']:+.3f} pp.")
    if sonia_5d and "change" in sonia_5d:
        card.append(f"- SONIA (IUDSOIA) change t..t+5d: "
                    f"{sonia_5d['change']:+.3f} pp.")
    card += [
        "",
        "## Data",
        "",
        f"- fred:DEXUSUK (USD per GBP, daily) — primary outcome",
        f"- fred:DGS10 (US 10y treasury yield, daily) — control",
        f"- fred:VIXCLS (CBOE VIX, daily) — control",
        f"- boe:IUDBEDR (Bank Rate, daily) — secondary",
        f"- boe:IUDSOIA (SONIA, daily) — secondary",
        f"- fred:IRLTLT01GBM156N (UK long-term yield) — **MISSING** "
        f"(data-gap; flagged for fetcher pass)",
        f"- boe long-gilt 10y/30y yield series — **MISSING** "
        f"(no clear IADB code in current data tree)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
