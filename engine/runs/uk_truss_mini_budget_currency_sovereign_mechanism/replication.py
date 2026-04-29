#!/usr/bin/env python3
"""Replication — UK Truss 2022 mini-budget: currency + sovereign-yield mechanism test.

Spec: hypotheses/fiscal/uk_truss_mini_budget_currency_sovereign_mechanism.yaml v1
Position-claim: mmt #6 (school predicts: mixed)

This is the MECHANISM test that complements the FX-only sister hypothesis
`unfunded_fiscal_expansion_above_zlb_bond_market_response`. The MMT
framing reads the September 2022 gilt crisis as institutional-framework
rupture (LDI cascade) rather than a hard-fiscal-limit event, with the
BoE acting as issuer's bank to restore order. Two empirical legs are
required for that reading to fit the close-of-day data:

  PRIMARY LEG 1 (FX repricing):  GBP/USD trough close in 2022-09-23..
    2022-09-28 falls >= 3.0% (log) below the 2022-09-22 close.

  PRIMARY LEG 2 (Yield channel — pre-intervention spike + post-
    intervention retrace):  UK 10y gilt yield (boe:IUDMNZC) excess move
    over US 10y treasury (fred:DGS10), measured pre-anchor 2022-09-22 ->
    peak in 2022-09-23..2022-09-28, is >= +60bp (UK rises >= 60bp more
    than US over the pre-intervention sub-window). AND the BoE
    intervention causes that UK-US 10y excess gap to give back >= 50%
    of the spike within 5 trading days of the 28-Sep facility (close on
    28-Sep -> close 5 trading days later vs the spike).

Both primaries must hold for SUPPORTED. PARTIAL if FX leg holds but
yield leg falls in [+20bp, +60bp) at peak OR retrace in [25%, 50%).
REFUTED if FX leg < 1.5% OR yield leg < +20bp OR retrace < 25%.

DATA-GAP (METHOD_VALID): the spec also names 30y gilt (boe:IUDLG7N)
and FRED UK long-term yield (fred:IRLTLT01GBM156N) as outcomes —
neither is on disk in the current vintage tree. The yield channel
verdict therefore rests on the 10y point alone (which is the most-
active node through the LDI episode in any case). Documented as a
data-gap rather than treated as missing falsifying evidence.
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
HID = "uk_truss_mini_budget_currency_sovereign_mechanism"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Spec-pinned event dates.
PRE_EVENT_DATE = pd.Timestamp("2022-09-22")    # last trading day BEFORE announcement
EVENT_DATE = pd.Timestamp("2022-09-23")        # Kwarteng "growth plan"
BOE_INTERVENTION = pd.Timestamp("2022-09-28")  # BoE temporary gilt-purchase facility
HUNT_REVERSAL = pd.Timestamp("2022-10-14")     # Hunt restoration begins
TRUSS_RESIGNATION = pd.Timestamp("2022-10-20")
RETRACE_TRADING_DAYS = 5  # close on BoE day -> 5 trading days later

# --- Falsification thresholds (dispositive) ---
# FX leg
GBPUSD_THRESHOLD_SUPPORTED = 0.030   # log-decline at trough
GBPUSD_THRESHOLD_PARTIAL_FLOOR = 0.015
# Yield-spike leg (UK 10y minus US 10y, percentage points; 1pp = 100bp)
EXCESS_SPIKE_SUPPORTED_BP = 0.60     # >= 60bp
EXCESS_SPIKE_PARTIAL_FLOOR_BP = 0.20 # >= 20bp
# Retrace leg (fraction of spike that BoE reverses by t+5d after 28-Sep)
RETRACE_SUPPORTED_FRAC = 0.50        # >= 50%
RETRACE_PARTIAL_FLOOR_FRAC = 0.25    # >= 25%


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
    """Normalise to (date, value). FRED has extra realtime cols; BoE doesn't."""
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns or "value" not in t.columns:
        raise ValueError(f"{path}: need (date,value), got {list(t.columns)}")
    t = t[["date", "value"]].copy()
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna().sort_values("date").reset_index(drop=True)


def value_on_or_before(df: pd.DataFrame, t: pd.Timestamp) -> tuple[pd.Timestamp, float] | None:
    sub = df[df["date"] <= t]
    if sub.empty:
        return None
    row = sub.iloc[-1]
    return row["date"], float(row["value"])


def value_on_or_after(df: pd.DataFrame, t: pd.Timestamp) -> tuple[pd.Timestamp, float] | None:
    sub = df[df["date"] >= t]
    if sub.empty:
        return None
    row = sub.iloc[0]
    return row["date"], float(row["value"])


def trading_days_after(df: pd.DataFrame, anchor: pd.Timestamp, n: int,
                       value_col: str = "value") -> tuple[pd.Timestamp, float] | None:
    """Walk n trading-day positions forward from the first observation on or after anchor."""
    on_or_after = df[df["date"] >= anchor]
    if on_or_after.empty:
        return None
    start_idx = on_or_after.index[0]
    target_idx = start_idx + n
    if target_idx >= len(df):
        return None
    row = df.iloc[target_idx]
    return row["date"], float(row[value_col])


def build_excess(uk: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
    """Inner-join UK 10y and US 10y on date; return (date, uk, us, excess) where excess = uk - us."""
    m = uk.rename(columns={"value": "uk"}).merge(
        us.rename(columns={"value": "us"}), on="date", how="inner"
    )
    m["excess"] = m["uk"] - m["us"]
    return m.sort_values("date").reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------- Locate vintages -----------------
    dexusuk_path = latest_optional("fred", "DEXUSUK")
    uk_10y_path = latest_optional("boe", "IUDMNZC")
    us_10y_path = latest_optional("fred", "DGS10")
    us_30y_path = latest_optional("fred", "DGS30")  # informative
    vix_path = latest_optional("fred", "VIXCLS")
    bankrate_path = latest_optional("boe", "IUDBEDR")
    sonia_path = latest_optional("boe", "IUDSOIA")
    gbpeur_path = latest_optional("boe", "XUDLERS")  # informative cross-check
    # Spec-named outcomes that are NOT on disk:
    boe_30y_gilt_path = latest_optional("boe", "IUDLG7N")
    fred_uk_lt_path = latest_optional("fred", "IRLTLT01GBM156N")

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
    pin("uk_10y_gilt", "boe", "IUDMNZC", uk_10y_path)
    pin("us_10y_treasury", "fred", "DGS10", us_10y_path)
    pin("us_30y_treasury", "fred", "DGS30", us_30y_path)
    pin("vix", "fred", "VIXCLS", vix_path)
    pin("boe_bank_rate", "boe", "IUDBEDR", bankrate_path)
    pin("sonia", "boe", "IUDSOIA", sonia_path)
    pin("gbp_eur", "boe", "XUDLERS", gbpeur_path)
    pin("uk_30y_gilt_boe", "boe", "IUDLG7N", boe_30y_gilt_path)
    pin("uk_long_term_yield_fred", "fred", "IRLTLT01GBM156N", fred_uk_lt_path)

    # ----------------- Hard data-gap check on PRIMARIES -----------------
    if dexusuk_path is None or uk_10y_path is None or us_10y_path is None:
        missing = [s for s, p in [("fred:DEXUSUK", dexusuk_path),
                                  ("boe:IUDMNZC", uk_10y_path),
                                  ("fred:DGS10", us_10y_path)] if p is None]
        verdict = (f"inconclusive (data gap on {', '.join(missing)}) — primary "
                   f"mechanism series unavailable; cannot evaluate the Truss "
                   f"mini-budget institutional-rupture claim.")
        diagnostics = {"verdict": verdict, "primary_series_missing": missing,
                       "manifest": manifest}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(f"# {HID}\n\n**Verdict:** {verdict}\n")
        pd.DataFrame([{"spec": "primary", "term": "data_gap", "estimate": np.nan}]
                     ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nrun_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
            "verdict: inconclusive_data_gap\n"
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps(
            {"kind": "result", "chart_id": f"{HID}/fig1",
             "title": "Truss mini-budget mechanism — data unavailable",
             "type": "line", "series": [],
             "annotations": [{"type": "note", "label": verdict}],
             "permalink": f"/h/{HID}"}, indent=2))
        print(f"verdict: {verdict}")
        return

    # ============================================================
    # PRIMARY LEG 1 — FX repricing (GBP/USD trough vs pre-anchor)
    # ============================================================
    fx = load_daily(dexusuk_path)
    pre_fx = value_on_or_before(fx, PRE_EVENT_DATE)
    crisis_fx = fx[(fx["date"] >= EVENT_DATE) & (fx["date"] <= BOE_INTERVENTION)]
    if pre_fx is None or crisis_fx.empty:
        fx_log_decline = None
        fx_pct_decline = None
        trough = {"error": "missing FX observations in window"}
    else:
        pre_anchor_date, pre_anchor_value = pre_fx
        trough_row = crisis_fx.loc[crisis_fx["value"].idxmin()]
        log_change = float(np.log(trough_row["value"]) - np.log(pre_anchor_value))
        fx_log_decline = -log_change  # positive = GBP weakened
        fx_pct_decline = (1.0 - np.exp(-fx_log_decline)) * 100.0
        trough = {
            "trough_date": trough_row["date"].date().isoformat(),
            "trough_value": float(trough_row["value"]),
            "pre_anchor_date": pre_anchor_date.date().isoformat(),
            "pre_anchor_value": pre_anchor_value,
            "log_decline": fx_log_decline,
            "pct_decline": fx_pct_decline,
        }

    # ============================================================
    # PRIMARY LEG 2 — Yield channel (UK-US 10y excess spike + retrace)
    # ============================================================
    uk = load_daily(uk_10y_path)
    us = load_daily(us_10y_path)
    excess = build_excess(uk, us)

    # Pre-anchor excess on/before 22-Sep (matches FX pre-anchor logic).
    pre_excess = value_on_or_before(excess.rename(columns={"excess": "value"})[["date", "value"]],
                                    PRE_EVENT_DATE)
    # Pre-intervention sub-window: 23-Sep..28-Sep peak excess.
    pre_int = excess[(excess["date"] >= EVENT_DATE) & (excess["date"] <= BOE_INTERVENTION)]
    # Retrace measurement: close on BoE day, then n trading days later.
    boe_close = excess[excess["date"] >= BOE_INTERVENTION]
    if pre_excess is None or pre_int.empty or boe_close.empty:
        yield_diag = {"error": "missing UK/US 10y joint observations in window"}
        excess_spike_bp = None
        retrace_frac = None
        peak_row = None
        post_intervention_retrace = None
    else:
        pre_excess_date, pre_excess_value = pre_excess
        peak_idx = pre_int["excess"].idxmax()
        peak_row = pre_int.loc[peak_idx]
        excess_spike_bp = float(peak_row["excess"] - pre_excess_value)  # in pp; 1pp = 100bp; we report as percentage points

        # Five trading-day retrace anchored at the BoE day's joint close.
        retrace_pair = trading_days_after(excess, BOE_INTERVENTION,
                                          RETRACE_TRADING_DAYS, value_col="excess")
        if retrace_pair is None:
            retrace_frac = None
            post_intervention_retrace = {"error": "insufficient post-BoE history"}
        else:
            retrace_date, retrace_value = retrace_pair
            # Spike measured from pre-anchor; retrace measured from peak down to retrace value
            retrace_amount = float(peak_row["excess"] - retrace_value)
            if excess_spike_bp <= 0:
                retrace_frac = None
            else:
                retrace_frac = retrace_amount / excess_spike_bp
            post_intervention_retrace = {
                "boe_intervention_date": BOE_INTERVENTION.date().isoformat(),
                "retrace_target_date": retrace_date.date().isoformat(),
                "retrace_target_value": retrace_value,
                "peak_excess_bp_pp": float(peak_row["excess"]),
                "retrace_excess_bp_pp": retrace_value,
                "spike_size_pp": excess_spike_bp,
                "retrace_amount_pp": retrace_amount,
                "retrace_fraction": retrace_frac,
            }

        yield_diag = {
            "pre_anchor_date": pre_excess_date.date().isoformat(),
            "pre_anchor_excess_pp": pre_excess_value,
            "peak_date": peak_row["date"].date().isoformat(),
            "peak_uk_10y_pct": float(peak_row["uk"]),
            "peak_us_10y_pct": float(peak_row["us"]),
            "peak_excess_pp": float(peak_row["excess"]),
            "spike_size_pp": excess_spike_bp,
            "spike_size_bp": excess_spike_bp * 100.0,
            "post_intervention_retrace": post_intervention_retrace,
        }

    # ============================================================
    # Verdict logic (both primaries required)
    # ============================================================
    fx_leg_pass = (fx_log_decline is not None and fx_log_decline >= GBPUSD_THRESHOLD_SUPPORTED)
    fx_leg_partial = (fx_log_decline is not None
                      and GBPUSD_THRESHOLD_PARTIAL_FLOOR <= fx_log_decline < GBPUSD_THRESHOLD_SUPPORTED)
    fx_leg_refute = (fx_log_decline is not None and fx_log_decline < GBPUSD_THRESHOLD_PARTIAL_FLOOR)

    spike_pass = (excess_spike_bp is not None and excess_spike_bp >= EXCESS_SPIKE_SUPPORTED_BP)
    spike_partial = (excess_spike_bp is not None
                     and EXCESS_SPIKE_PARTIAL_FLOOR_BP <= excess_spike_bp < EXCESS_SPIKE_SUPPORTED_BP)
    spike_refute = (excess_spike_bp is not None and excess_spike_bp < EXCESS_SPIKE_PARTIAL_FLOOR_BP)

    retrace_pass = (retrace_frac is not None and retrace_frac >= RETRACE_SUPPORTED_FRAC)
    retrace_partial = (retrace_frac is not None
                       and RETRACE_PARTIAL_FLOOR_FRAC <= retrace_frac < RETRACE_SUPPORTED_FRAC)
    retrace_refute = (retrace_frac is not None and retrace_frac < RETRACE_PARTIAL_FLOOR_FRAC)

    yield_leg_pass = spike_pass and retrace_pass
    yield_leg_partial = (
        (spike_pass and retrace_partial)
        or (spike_partial and (retrace_pass or retrace_partial))
    )
    yield_leg_refute = spike_refute or retrace_refute

    if fx_log_decline is None or excess_spike_bp is None or retrace_frac is None:
        verdict_label = "inconclusive"
        verdict = (f"inconclusive — one or more event-window measurements "
                   f"could not be computed (FX log-decline: "
                   f"{fx_log_decline}, yield spike pp: {excess_spike_bp}, "
                   f"retrace fraction: {retrace_frac}).")
    elif fx_leg_pass and yield_leg_pass:
        verdict_label = "SUPPORTED"
        verdict = (
            f"SUPPORTED — Both legs of the institutional-rupture mechanism "
            f"hold. FX trough on {trough['trough_date']} fell "
            f"{fx_pct_decline:.2f}% (log {fx_log_decline:+.4f}) vs the "
            f"{trough['pre_anchor_date']} close (>= 3.0% threshold). "
            f"UK 10y gilt-yield excess over US 10y spiked "
            f"+{excess_spike_bp*100:.0f}bp pre-anchor->peak "
            f"({yield_diag['peak_date']}; >= 60bp threshold) and the BoE "
            f"intervention retraced {retrace_frac*100:.0f}% of that spike "
            f"by close on {post_intervention_retrace['retrace_target_date']} "
            f"(>= 50% threshold). The institutional channel — repricing "
            f"that BoE intervention then reversed — fits."
        )
    elif fx_leg_refute or yield_leg_refute:
        which = []
        if fx_leg_refute:
            which.append(f"FX leg refutes (only {fx_pct_decline:.2f}% trough decline; needs >= 1.5%)")
        if spike_refute:
            which.append(f"yield-spike leg refutes (only +{excess_spike_bp*100:.0f}bp spike; needs >= 20bp)")
        if retrace_refute:
            which.append(f"BoE-retrace leg refutes (only {retrace_frac*100:.0f}% retrace; needs >= 25%)")
        verdict_label = "refuted"
        verdict = (
            f"refuted — Mechanism leg(s) below floor: "
            f"{'; '.join(which)}. The institutional-rupture-then-BoE-fix "
            f"reading is not supported by the close-of-day data."
        )
    else:
        verdict_label = "partial"
        notes = []
        if fx_leg_pass:
            notes.append(f"FX leg holds ({fx_pct_decline:.2f}% trough decline)")
        elif fx_leg_partial:
            notes.append(f"FX leg directionally consistent ({fx_pct_decline:.2f}%, between 1.5% and 3.0%)")
        if yield_leg_pass:
            notes.append(f"yield leg holds ({excess_spike_bp*100:.0f}bp spike, {retrace_frac*100:.0f}% retrace)")
        elif yield_leg_partial:
            notes.append(f"yield leg partial ({excess_spike_bp*100:.0f}bp spike, {retrace_frac*100:.0f}% retrace)")
        verdict = (
            f"partial — Both mechanism legs are directionally consistent "
            f"but at least one fails the SUPPORTED threshold: "
            f"{'; '.join(notes)}."
        )

    # ----------------- Informative diagnostics -----------------
    # Persistent post-intervention level: UK-US 10y excess on TRUSS_RESIGNATION date.
    if peak_row is not None:
        post_truss = excess[excess["date"] >= TRUSS_RESIGNATION]
        if not post_truss.empty:
            tr_date = post_truss.iloc[0]["date"]
            tr_excess = float(post_truss.iloc[0]["excess"])
            persistence = {
                "date": tr_date.date().isoformat(),
                "excess_pp": tr_excess,
                "vs_pre_anchor_change_pp": tr_excess - yield_diag["pre_anchor_excess_pp"],
            }
        else:
            persistence = None
    else:
        persistence = None

    # GBP/EUR cross-check
    gbpeur_block = None
    if gbpeur_path is not None:
        try:
            gbpeur = load_daily(gbpeur_path)
            pre_eur = value_on_or_before(gbpeur, PRE_EVENT_DATE)
            crisis_eur = gbpeur[(gbpeur["date"] >= EVENT_DATE) & (gbpeur["date"] <= BOE_INTERVENTION)]
            if pre_eur is not None and not crisis_eur.empty:
                pre_d, pre_v = pre_eur
                trough_e = crisis_eur.loc[crisis_eur["value"].idxmin()]
                # XUDLERS = GBP per 1 EUR? boe code XUDLERS is "Sterling effective EUR rate" (GBP per EUR).
                # A FALL in XUDLERS means EUR weakens vs GBP (= GBP strengthens). For our purposes we
                # report log-change of XUDLERS vs pre-anchor and let the reader interpret.
                log_change_e = float(np.log(trough_e["value"]) - np.log(pre_v))
                gbpeur_block = {
                    "series": "boe:XUDLERS (sterling-effective EUR rate)",
                    "pre_anchor_date": pre_d.date().isoformat(),
                    "pre_anchor_value": pre_v,
                    "trough_date": trough_e["date"].date().isoformat(),
                    "trough_value": float(trough_e["value"]),
                    "log_change_at_trough": log_change_e,
                    "note": ("XUDLERS = GBP per 1 EUR; a RISE means GBP "
                             "weakened against EUR. Reported informationally.")
                }
        except Exception as exc:
            gbpeur_block = {"error": str(exc)}

    # Bank Rate / SONIA / VIX context
    def window_change(path: Path | None, t0: pd.Timestamp, t_n: int) -> dict | None:
        if path is None:
            return None
        try:
            df = load_daily(path)
        except Exception as exc:
            return {"error": str(exc)}
        anchor_pair = value_on_or_after(df, t0)
        target_pair = trading_days_after(df, t0, t_n)
        if anchor_pair is None or target_pair is None:
            return {"error": "insufficient data"}
        return {
            "anchor_date": anchor_pair[0].date().isoformat(),
            "anchor_value": anchor_pair[1],
            "target_date": target_pair[0].date().isoformat(),
            "target_value": target_pair[1],
            "trading_days": t_n,
            "change": target_pair[1] - anchor_pair[1],
        }

    bankrate_5d = window_change(bankrate_path, EVENT_DATE, 5)
    sonia_5d = window_change(sonia_path, EVENT_DATE, 5)
    vix_5d = window_change(vix_path, EVENT_DATE, 5)

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "event_date": EVENT_DATE.date().isoformat(),
        "boe_intervention_date": BOE_INTERVENTION.date().isoformat(),
        "primary_leg_1_fx": {
            **trough,
            "threshold_supported_log": GBPUSD_THRESHOLD_SUPPORTED,
            "threshold_partial_floor_log": GBPUSD_THRESHOLD_PARTIAL_FLOOR,
            "leg_pass": bool(fx_leg_pass),
        },
        "primary_leg_2_yield": {
            **yield_diag,
            "threshold_spike_supported_bp": EXCESS_SPIKE_SUPPORTED_BP * 100.0,
            "threshold_spike_partial_floor_bp": EXCESS_SPIKE_PARTIAL_FLOOR_BP * 100.0,
            "threshold_retrace_supported_frac": RETRACE_SUPPORTED_FRAC,
            "threshold_retrace_partial_floor_frac": RETRACE_PARTIAL_FLOOR_FRAC,
            "spike_pass": bool(spike_pass),
            "retrace_pass": bool(retrace_pass),
            "leg_pass": bool(yield_leg_pass),
        },
        "informative": {
            "persistence_at_truss_resignation": persistence,
            "gbp_eur_cross_check": gbpeur_block,
            "boe_bank_rate_5d_change_pct": bankrate_5d,
            "sonia_5d_change_pct": sonia_5d,
            "vix_5d_change_pts": vix_5d,
        },
        "method_valid": {
            "uk_10y_gilt_on_disk": uk_10y_path is not None,
            "us_10y_treasury_on_disk": us_10y_path is not None,
            "fx_on_disk": dexusuk_path is not None,
            "boe_30y_gilt_on_disk": boe_30y_gilt_path is not None,
            "fred_uk_long_term_on_disk": fred_uk_lt_path is not None,
            "yield_channel_status": (
                "10y point used as yield channel; spec also names 30y "
                "(boe:IUDLG7N) and FRED UK long-term (fred:IRLTLT01GBM156N) "
                "but neither is on disk in the current vintage. The 30y "
                "leg is documented as a data-gap; the 10y point is the "
                "most-active node through the LDI episode in any case."
            ),
        },
        "manifest": manifest,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ----------------- Coefficients -----------------
    rows = [
        {"spec": "primary_leg_1_fx", "term": "gbp_usd_trough_log_decline",
         "estimate": fx_log_decline if fx_log_decline is not None else np.nan},
        {"spec": "primary_leg_1_fx", "term": "gbp_usd_trough_pct_decline",
         "estimate": fx_pct_decline if fx_pct_decline is not None else np.nan},
        {"spec": "primary_leg_1_fx", "term": "threshold_supported_log",
         "estimate": GBPUSD_THRESHOLD_SUPPORTED},
        {"spec": "primary_leg_2_yield", "term": "uk_us_10y_excess_spike_pp",
         "estimate": excess_spike_bp if excess_spike_bp is not None else np.nan},
        {"spec": "primary_leg_2_yield", "term": "uk_us_10y_excess_spike_bp",
         "estimate": excess_spike_bp * 100.0 if excess_spike_bp is not None else np.nan},
        {"spec": "primary_leg_2_yield", "term": "boe_retrace_fraction",
         "estimate": retrace_frac if retrace_frac is not None else np.nan},
        {"spec": "primary_leg_2_yield", "term": "threshold_spike_supported_bp",
         "estimate": EXCESS_SPIKE_SUPPORTED_BP * 100.0},
        {"spec": "primary_leg_2_yield", "term": "threshold_retrace_supported_frac",
         "estimate": RETRACE_SUPPORTED_FRAC},
    ]
    if persistence is not None:
        rows.append({"spec": "informative", "term": "uk_us_10y_excess_on_truss_resignation_pp",
                     "estimate": persistence["excess_pp"]})
        rows.append({"spec": "informative", "term": "uk_us_10y_excess_change_vs_pre_anchor_pp",
                     "estimate": persistence["vs_pre_anchor_change_pp"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ----------------- Chart -----------------
    chart_window_start = EVENT_DATE - pd.Timedelta(days=20)
    chart_window_end = EVENT_DATE + pd.Timedelta(days=45)
    excess_window = excess[(excess["date"] >= chart_window_start)
                           & (excess["date"] <= chart_window_end)]
    excess_pts = [{"x": d.date().isoformat(), "y": float(v) * 100.0}  # in basis points
                  for d, v in zip(excess_window["date"], excess_window["excess"])]
    uk_pts = [{"x": d.date().isoformat(), "y": float(v) * 100.0}
              for d, v in zip(excess_window["date"], excess_window["uk"])]
    us_pts = [{"x": d.date().isoformat(), "y": float(v) * 100.0}
              for d, v in zip(excess_window["date"], excess_window["us"])]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "UK 10y gilt yield vs US 10y treasury — Truss mini-budget event window",
        "subtitle": (
            f"Yield-leg: spike {(excess_spike_bp or 0)*100:+.0f}bp pre-anchor->peak "
            f"({(EXCESS_SPIKE_SUPPORTED_BP)*100:.0f}bp threshold); BoE retrace "
            f"{(retrace_frac or 0)*100:.0f}% ({RETRACE_SUPPORTED_FRAC*100:.0f}% threshold). "
            f"FX-leg: trough {(fx_pct_decline or 0):+.2f}% "
            f"({GBPUSD_THRESHOLD_SUPPORTED*100:.1f}% threshold). "
            f"Verdict: {verdict_label}."
        ),
        "type": "line",
        "x_axis": {"label": "Date", "type": "time"},
        "y_axis": {"label": "Yield (bp; UK-US gap on the 'excess' line)", "type": "linear"},
        "series": [
            {"id": "excess", "label": "UK 10y minus US 10y (bp)",
             "color": "#E15759", "treated": True, "points": excess_pts},
            {"id": "uk_10y", "label": "UK 10y gilt (bp)",
             "color": "#4E79A7", "treated": False, "points": uk_pts},
            {"id": "us_10y", "label": "US 10y treasury (bp)",
             "color": "#59A14F", "treated": False, "points": us_pts},
        ],
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
             "label": (f"Pre-anchor excess (22-Sep) = "
                       f"{yield_diag.get('pre_anchor_excess_pp', 0)*100:.0f}bp; "
                       f"peak ({yield_diag.get('peak_date','?')}) = "
                       f"{yield_diag.get('peak_excess_pp', 0)*100:.0f}bp; "
                       f"spike = +{(excess_spike_bp or 0)*100:.0f}bp.")},
            {"type": "note",
             "label": ("30y gilt (boe:IUDLG7N) and FRED UK long-term "
                       "(fred:IRLTLT01GBM156N) are missing from the current "
                       "vintage tree; yield channel rests on 10y point.")},
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
        f"# Truss 2022 mini-budget — currency + sovereign-yield mechanism",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Event date: **2022-09-23** (Kwarteng growth plan).",
        f"- BoE intervention: **2022-09-28** (temporary gilt-purchase facility).",
        "",
        "### Primary leg 1 — FX repricing (GBP/USD)",
        "",
        f"- Pre-anchor close ({trough.get('pre_anchor_date','?')}): "
        f"{trough.get('pre_anchor_value','?')} USD/GBP.",
        f"- Trough close in 23-28 Sep ({trough.get('trough_date','?')}): "
        f"{trough.get('trough_value','?')} USD/GBP.",
        f"- Log-decline at trough: **{(fx_log_decline or 0):+.4f}** "
        f"({(fx_pct_decline or 0):+.2f}%). Threshold for SUPPORTED: 3.0%; "
        f"partial floor: 1.5%.",
        "",
        "### Primary leg 2 — Yield channel (UK 10y minus US 10y, bp)",
        "",
        f"- Pre-anchor excess ({yield_diag.get('pre_anchor_date','?')}): "
        f"**{yield_diag.get('pre_anchor_excess_pp', 0)*100:+.0f}bp**.",
        f"- Peak excess in 23-28 Sep ({yield_diag.get('peak_date','?')}): "
        f"**{yield_diag.get('peak_excess_pp', 0)*100:+.0f}bp**.",
        f"- Spike size: **+{(excess_spike_bp or 0)*100:.0f}bp**. "
        f"Threshold for SUPPORTED: +60bp; partial floor: +20bp.",
        f"- BoE retrace 5 trading days after intervention close: "
        f"**{(retrace_frac or 0)*100:.0f}%** of the spike. "
        f"Threshold for SUPPORTED: 50%; partial floor: 25%.",
        "",
        "## Method",
        "",
        "Daily close-of-day mechanism event-window test. The MMT-style "
        "institutional-rupture-not-hard-fiscal-limit reading requires "
        "two empirical patterns: (1) a sharp pre-intervention sovereign "
        "repricing in the affected currency and yield curve, and (2) "
        "evidence that BoE intervention substantively retraces the "
        "yield repricing (i.e., the issuer's bank can normalise the "
        "channel). The yield leg is computed as a UK-US 10y excess "
        "(boe:IUDMNZC minus fred:DGS10) to net out the global rate "
        "backdrop. Both legs use the 2022-09-22 close as the pre-event "
        "anchor; the yield-spike window ends at 2022-09-28 (BoE-LDI "
        "facility close); the retrace is measured 5 trading days after "
        "the BoE close. The FX leg uses the trough close in the same "
        "23-28 Sep window. Spec also names 30y gilt (boe:IUDLG7N) and "
        "FRED UK long-term yield (fred:IRLTLT01GBM156N) — neither is "
        "on disk in the current vintage; documented as data-gap.",
        "",
        "## Informative",
        "",
    ]
    if persistence is not None:
        card.append(f"- UK-US 10y excess on Truss resignation "
                    f"({persistence['date']}): {persistence['excess_pp']*100:+.0f}bp "
                    f"({persistence['vs_pre_anchor_change_pp']*100:+.0f}bp vs pre-anchor).")
    if gbpeur_block and "trough_value" in gbpeur_block:
        card.append(f"- GBP/EUR cross-check (boe:XUDLERS, GBP per 1 EUR): "
                    f"trough {gbpeur_block['trough_value']:.4f} on "
                    f"{gbpeur_block['trough_date']} (log-change vs anchor "
                    f"{gbpeur_block['log_change_at_trough']:+.4f}; positive = "
                    f"GBP weakened vs EUR).")
    if vix_5d and "change" in vix_5d:
        card.append(f"- VIX change t..t+5d: {vix_5d['change']:+.2f} pts.")
    if bankrate_5d and "change" in bankrate_5d:
        card.append(f"- BoE Bank Rate change t..t+5d: "
                    f"{bankrate_5d['change']:+.3f}pp.")
    if sonia_5d and "change" in sonia_5d:
        card.append(f"- SONIA change t..t+5d: {sonia_5d['change']:+.3f}pp.")

    card += [
        "",
        "## Data",
        "",
        "- fred:DEXUSUK (USD per GBP, daily) — primary leg 1",
        "- boe:IUDMNZC (UK 10y gilt yield, daily) — primary leg 2",
        "- fred:DGS10 (US 10y treasury yield, daily) — primary leg 2 control",
        "- fred:DGS30, fred:VIXCLS, boe:IUDBEDR, boe:IUDSOIA, boe:XUDLERS — informative",
        "- boe:IUDLG7N (UK 30y gilt) — **MISSING** (data gap)",
        "- fred:IRLTLT01GBM156N (UK long-term yield) — **MISSING** (data gap)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
