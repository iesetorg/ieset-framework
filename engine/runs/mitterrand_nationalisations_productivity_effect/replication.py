#!/usr/bin/env python3
"""Replication — Mitterrand 1981-1983 nationalisations and French productivity.

Spec: hypotheses/growth/mitterrand_nationalisations_productivity_effect.yaml v1
Position-claim: classical_liberal #8 (school predicts: supported)

The classical-liberal claim: Mitterrand's 1981-1983 nationalisations
reduced productivity in France and the 1983 'tournant de la rigueur'
reversal was needed to restore growth. The original spec asked for a
firm-level event study with firm + year FE; no firm-level French panel
exists in the repo. We sharpen to a country-level controlled event
study using PWT 'rtfpna' (real TFP at constant national prices) for
FRA, with DEU, GBR, ITA, NLD, BEL, ESP as the European-peer control
set (industry-matched at the country level).

PRIMARY (dispositive):
  1. Mean FRA log-TFP gap vs its 1975-1980 linear pre-trend, over
     the active-nationalisation window 1981-1983, NET OF the same
     gap measured for the European-control mean, must be at most
     -0.015 log-points (i.e. a ≥1.5% under-trend dip relative to
     controls). Catches the 'nationalisation depressed productivity'
     premise.
  2. (Recovery) The same control-net log-TFP gap must improve by at
     least +0.0075 log-points between 1981-1983 and 1984-1990 — i.e.
     the post-tournant period closes at least HALF of the dip. Catches
     the 'tournant de la rigueur was a course-correction' premise.

SUPPORTED only if BOTH primaries hold. REFUTED if FRA is ABOVE its
pre-trend by ≥0.005 log-points relative to controls in 1981-1983
(i.e. nationalisations did not even visibly depress productivity, the
opposite of the claim). PARTIAL otherwise.

Caveat: a country-level estimator cannot isolate the 16 nationalised
firms from the rest of the French economy, so a SUPPORTED verdict
here is consistent with — but not dispositive of — the firm-level
claim, and a REFUTED verdict is correspondingly weaker than a
firm-level test would give. v2 should resurrect the firm-level event
study once a Compustat / Banque-de-France firm panel is fetched.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "mitterrand_nationalisations_productivity_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "FRA"
CONTROLS = ["DEU", "GBR", "ITA", "NLD", "BEL", "ESP"]
ALL_COUNTRIES = [TREATED] + CONTROLS

PRE_WINDOW = (1975, 1980)        # pre-Mitterrand baseline
TREATMENT_WINDOW = (1981, 1983)   # active nationalisations, pre-tournant
RECOVERY_WINDOW = (1984, 1990)    # post-tournant
FULL_PERIOD = (1975, 1995)

# Sharpened thresholds (replacing the spec stub's generic "p<0.10" rule).
PRIMARY_DIP_THRESHOLD = -0.015   # log-units relative to controls during 1981-83
PRIMARY_RECOVERY_THRESHOLD = 0.0075  # half-closure of the dip
REFUTED_FLOOR = 0.005             # if FRA is +0.5 log-points ABOVE pre-trend net of controls -> refuted


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
    if not files:
        return None
    return files[-1]


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def country_log_series(df: pd.DataFrame, country: str, period: tuple[int, int]) -> pd.Series:
    sub = df[(df["country_iso3"] == country)
             & df["year"].between(period[0], period[1])]
    sub = sub.dropna(subset=["value"]).copy()
    sub = sub[sub["value"] > 0]
    if sub.empty:
        return pd.Series(dtype=float)
    sub["log"] = np.log(sub["value"])
    return sub.set_index("year")["log"].sort_index()


def fit_pretrend(log_s: pd.Series, pre_window: tuple[int, int]) -> tuple[float, float, int]:
    pre = log_s[(log_s.index >= pre_window[0]) & (log_s.index <= pre_window[1])]
    if len(pre) < 3:
        return float("nan"), float("nan"), int(len(pre))
    x = pre.index.astype(float).values
    y = pre.values
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept), int(len(pre))


def gap_in_window(log_s: pd.Series, slope: float, intercept: float,
                  window: tuple[int, int]) -> tuple[float, int]:
    """Mean (actual − pretrend-projection) over window, in log units."""
    if np.isnan(slope):
        return float("nan"), 0
    sub = log_s[(log_s.index >= window[0]) & (log_s.index <= window[1])]
    if sub.empty:
        return float("nan"), 0
    proj = slope * sub.index.astype(float).values + intercept
    gaps = sub.values - proj
    return float(np.mean(gaps)), int(len(gaps))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- PRIMARY: PWT TFP ----------
    tfp_path = latest("pwt", "rtfpna")
    if tfp_path is None:
        verdict = ("inconclusive (data gap on pwt:rtfpna) — PWT real-TFP "
                   "series not in the current vintage; the country-level "
                   "FRA TFP event study cannot run.")
        diagnostics = {"verdict": verdict, "primary_pass": False,
                       "missing_series": "pwt:rtfpna"}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "vintages": {"pwt_rtfpna": {"publisher": "pwt", "series": "rtfpna",
                                         "missing": True}},
        }, sort_keys=False))
        pd.DataFrame([{"spec": "primary", "term": "n/a", "estimate": float("nan")}]).to_parquet(
            OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "Mitterrand nationalisations — French TFP vs European peers (DATA GAP)",
            "subtitle": "PWT rtfpna missing; verdict inconclusive.",
            "type": "line", "x_axis": {"label": "Year"}, "y_axis": {"label": "log TFP"},
            "series": [], "annotations": [{"type": "note", "label": verdict}],
            "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# Mitterrand nationalisations — productivity effect\n\n"
            f"**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    tfp = load_long(tfp_path)

    manifest: dict = {
        "pwt_rtfpna": {
            "publisher": "pwt", "series": "rtfpna",
            "vintage_file": str(tfp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(tfp_path),
        }
    }

    # FRA pre-trend + windows
    fra_log = country_log_series(tfp, TREATED, FULL_PERIOD)
    fra_slope, fra_intercept, fra_n_pre = fit_pretrend(fra_log, PRE_WINDOW)
    fra_gap_treat, fra_n_treat = gap_in_window(
        fra_log, fra_slope, fra_intercept, TREATMENT_WINDOW)
    fra_gap_recov, fra_n_recov = gap_in_window(
        fra_log, fra_slope, fra_intercept, RECOVERY_WINDOW)

    # Per-control: same construction
    control_results: dict[str, dict] = {}
    for c in CONTROLS:
        s = country_log_series(tfp, c, FULL_PERIOD)
        slope, intercept, n_pre = fit_pretrend(s, PRE_WINDOW)
        g_t, n_t = gap_in_window(s, slope, intercept, TREATMENT_WINDOW)
        g_r, n_r = gap_in_window(s, slope, intercept, RECOVERY_WINDOW)
        control_results[c] = {
            "n_pre": n_pre, "slope": slope, "intercept": intercept,
            "gap_treat": g_t, "n_treat": n_t,
            "gap_recov": g_r, "n_recov": n_r,
            "available": (n_pre >= 3 and n_t >= 1 and n_r >= 1
                          and not np.isnan(g_t) and not np.isnan(g_r)),
        }

    avail_controls = [c for c, r in control_results.items() if r["available"]]
    n_avail_controls = len(avail_controls)

    method_valid = (fra_n_pre >= 3 and not np.isnan(fra_gap_treat)
                    and not np.isnan(fra_gap_recov) and n_avail_controls >= 4)

    if not method_valid:
        verdict = (f"inconclusive — METHOD_VALID failed: FRA pre-period "
                   f"obs={fra_n_pre}, treatment-window gap NaN={np.isnan(fra_gap_treat)}, "
                   f"controls available={n_avail_controls}/6 (need ≥4).")
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "fra_n_pre": fra_n_pre,
            "fra_gap_treat": fra_gap_treat, "fra_gap_recov": fra_gap_recov,
            "n_controls_available": n_avail_controls,
            "controls_available": avail_controls,
            "control_results": control_results,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2,
                                                              default=lambda o: None) + "\n")
        # Still emit other artifacts
        pd.DataFrame([{"spec": "primary", "term": "method_valid", "estimate": 0.0}]).to_parquet(
            OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "vintages": manifest,
        }, sort_keys=False))
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "Mitterrand nationalisations — French TFP vs European peers",
            "subtitle": "METHOD_VALID failed; see diagnostics.",
            "type": "line", "x_axis": {"label": "Year"}, "y_axis": {"label": "log TFP"},
            "series": [], "annotations": [{"type": "note", "label": verdict}],
            "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# Mitterrand nationalisations — productivity effect\n\n"
            f"**Verdict:** {verdict}\n")
        print(f"verdict: {verdict}")
        return

    control_gap_treat_mean = float(np.mean(
        [control_results[c]["gap_treat"] for c in avail_controls]))
    control_gap_recov_mean = float(np.mean(
        [control_results[c]["gap_recov"] for c in avail_controls]))

    # Net gaps (FRA minus control mean) — the effect attributable to
    # FRA-specific events (nationalisations + tournant) net of any
    # generic European productivity slowdown.
    net_gap_treat = fra_gap_treat - control_gap_treat_mean
    net_gap_recov = fra_gap_recov - control_gap_recov_mean
    recovery_delta = net_gap_recov - net_gap_treat  # positive = recovered

    primary1_dip = net_gap_treat <= PRIMARY_DIP_THRESHOLD
    primary2_recov = recovery_delta >= PRIMARY_RECOVERY_THRESHOLD

    # ---------- INFORMATIVE: WDI auxiliary series ----------
    aux: dict = {}
    for label, pub, series in [
        ("log_real_gdp_pc", "world_bank_wdi", "NY.GDP.PCAP.KD"),
        ("gross_capital_formation_pct_gdp", "world_bank_wdi", "NE.GDI.TOTL.ZS"),
        ("trade_openness", "world_bank_wdi", "NE.TRD.GNFS.ZS"),
    ]:
        path = latest(pub, series)
        if path is None:
            aux[label] = {"available": False, "publisher": pub, "series": series}
            manifest[label] = {"publisher": pub, "series": series, "missing": True}
            continue
        manifest[label] = {
            "publisher": pub, "series": series,
            "vintage_file": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256(path),
        }
        df = load_long(path)
        # Per-country mean over treatment window vs pre window (level, not log
        # for ratio-style series; log for GDP per cap).
        is_log = (label == "log_real_gdp_pc")
        fra_pre = float(df[(df.country_iso3 == TREATED)
                           & df.year.between(*PRE_WINDOW)]["value"].mean())
        fra_treat = float(df[(df.country_iso3 == TREATED)
                             & df.year.between(*TREATMENT_WINDOW)]["value"].mean())
        fra_recov = float(df[(df.country_iso3 == TREATED)
                             & df.year.between(*RECOVERY_WINDOW)]["value"].mean())
        if is_log and fra_pre > 0 and fra_treat > 0:
            change_treat = float(np.log(fra_treat) - np.log(fra_pre))
            change_recov = (float(np.log(fra_recov) - np.log(fra_pre))
                            if fra_recov > 0 else float("nan"))
        else:
            change_treat = fra_treat - fra_pre
            change_recov = fra_recov - fra_pre
        aux[label] = {
            "available": True, "publisher": pub, "series": series,
            "fra_pre_mean": fra_pre, "fra_treat_mean": fra_treat,
            "fra_recov_mean": fra_recov,
            "fra_change_treat_minus_pre": change_treat,
            "fra_change_recov_minus_pre": change_recov,
            "is_log": is_log,
        }

    # ---------- Verdict ----------
    if primary1_dip and primary2_recov:
        verdict = (
            f"SUPPORTED — French TFP fell {net_gap_treat*100:+.2f}% below "
            f"its 1975-80 pre-trend (net of European-peer controls) over the "
            f"1981-83 active-nationalisation window (≤ -1.50% threshold) AND "
            f"recovered {recovery_delta*100:+.2f}pp toward trend in the "
            f"1984-90 post-tournant window (≥ +0.75pp half-closure threshold). "
            f"Pattern matches the classical-liberal nationalisation→damage→"
            f"reversal narrative, though country-level data cannot isolate "
            f"the 16 nationalised firms from the rest of the French economy."
        )
    elif net_gap_treat >= REFUTED_FLOOR:
        verdict = (
            f"refuted — French TFP was {net_gap_treat*100:+.2f}% ABOVE its "
            f"1975-80 pre-trend (net of European-peer controls) during the "
            f"1981-83 active-nationalisation window, not below it. The "
            f"productivity-damage premise is not visible at the country level."
        )
    else:
        # Direction-matching but threshold(s) missed
        which = []
        if not primary1_dip:
            which.append(
                f"dip {net_gap_treat*100:+.2f}% vs ≤ -1.50% threshold")
        if not primary2_recov:
            which.append(
                f"recovery {recovery_delta*100:+.2f}pp vs ≥ +0.75pp threshold")
        verdict = (
            f"partial — direction-consistent but magnitude misses the bar: "
            f"{'; '.join(which)}. Net 1981-83 dip {net_gap_treat*100:+.2f}%, "
            f"net 1984-90 gap {net_gap_recov*100:+.2f}%, recovery delta "
            f"{recovery_delta*100:+.2f}pp."
        )

    diagnostics = {
        "verdict": verdict,
        "primary1_dip_passes": bool(primary1_dip),
        "primary2_recovery_passes": bool(primary2_recov),
        "method_valid": True,
        "windows": {
            "pre": list(PRE_WINDOW),
            "treatment": list(TREATMENT_WINDOW),
            "recovery": list(RECOVERY_WINDOW),
        },
        "thresholds": {
            "primary_dip_log": PRIMARY_DIP_THRESHOLD,
            "primary_recovery_log": PRIMARY_RECOVERY_THRESHOLD,
            "refuted_floor_log": REFUTED_FLOOR,
        },
        "fra": {
            "n_pre": fra_n_pre,
            "pre_slope": fra_slope,
            "pre_intercept": fra_intercept,
            "gap_treat_log": fra_gap_treat,
            "gap_recov_log": fra_gap_recov,
            "n_treat_obs": fra_n_treat,
            "n_recov_obs": fra_n_recov,
        },
        "controls": control_results,
        "n_controls_available": n_avail_controls,
        "controls_available": avail_controls,
        "control_gap_treat_mean": control_gap_treat_mean,
        "control_gap_recov_mean": control_gap_recov_mean,
        "net_gap_treat_log_fra_minus_controls": net_gap_treat,
        "net_gap_recov_log_fra_minus_controls": net_gap_recov,
        "recovery_delta_log": recovery_delta,
        "informative_wdi": aux,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    # ---------- coefficients.parquet ----------
    coef_rows = [
        {"spec": "primary", "term": "fra_pre_slope_log_per_year", "estimate": fra_slope},
        {"spec": "primary", "term": "fra_gap_treat_1981_1983", "estimate": fra_gap_treat},
        {"spec": "primary", "term": "fra_gap_recov_1984_1990", "estimate": fra_gap_recov},
        {"spec": "primary", "term": "control_gap_treat_mean", "estimate": control_gap_treat_mean},
        {"spec": "primary", "term": "control_gap_recov_mean", "estimate": control_gap_recov_mean},
        {"spec": "primary", "term": "net_gap_treat_fra_minus_controls", "estimate": net_gap_treat},
        {"spec": "primary", "term": "net_gap_recov_fra_minus_controls", "estimate": net_gap_recov},
        {"spec": "primary", "term": "recovery_delta", "estimate": recovery_delta},
    ]
    for c, r in control_results.items():
        coef_rows.append({"spec": f"control_{c}", "term": "gap_treat", "estimate": r["gap_treat"]})
        coef_rows.append({"spec": f"control_{c}", "term": "gap_recov", "estimate": r["gap_recov"]})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- manifest.yaml ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- chart_data.json ----------
    palette = {
        "FRA": "#E15759",
        "DEU": "#4E79A7", "GBR": "#59A14F", "ITA": "#B07AA1",
        "NLD": "#F28E2B", "BEL": "#76B7B2", "ESP": "#EDC948",
    }
    series = []
    # Plot log-TFP indexed so 1980 = 0 to make the event visible
    for c in ALL_COUNTRIES:
        s = country_log_series(tfp, c, FULL_PERIOD)
        if s.empty or 1980 not in s.index:
            continue
        base = s[1980]
        pts = [{"x": int(y), "y": float(s[y] - base)} for y in s.index]
        series.append({
            "id": c, "label": c, "color": palette.get(c, "#888"),
            "treated": (c == TREATED),
            "points": pts,
        })

    # Add FRA pre-trend projection over 1975-1990 to make the dip visible
    if not np.isnan(fra_slope) and 1980 in fra_log.index:
        base = fra_log[1980]
        proj_pts = []
        for y in range(FULL_PERIOD[0], 1991):
            proj_pts.append({"x": y,
                             "y": float(fra_slope * y + fra_intercept - base)})
        series.append({
            "id": "FRA_pretrend", "label": "FRA 1975-80 pre-trend (extended)",
            "color": "#1f1f1f", "treated": True, "points": proj_pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": ("French TFP vs European peers around the 1981-83 nationalisations "
                  "and 1983 'tournant de la rigueur'"),
        "subtitle": (
            f"FRA TFP 1981-83 net of controls: {net_gap_treat*100:+.2f}% vs pre-trend; "
            f"recovery 1984-90: {net_gap_recov*100:+.2f}%. "
            f"Verdict: {verdict.split(' — ')[0]}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log TFP, indexed to 1980 = 0", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 1981, "label": "1981 nationalisations"},
            {"type": "vline", "x": 1983, "label": "1983 tournant de la rigueur"},
            {"type": "note", "label": (
                f"Net 1981-83 dip {net_gap_treat*100:+.2f}% (≤ -1.50% threshold), "
                f"net 1984-90 gap {net_gap_recov*100:+.2f}%, recovery delta "
                f"{recovery_delta*100:+.2f}pp (≥ +0.75pp threshold)."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v.get("vintage_file", "MISSING")}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- result_card.md ----------
    aux_lines = []
    for label, a in aux.items():
        if not a.get("available"):
            aux_lines.append(f"- **{label}** ({a['publisher']}:{a['series']}) — MISSING")
            continue
        unit = "log-units" if a["is_log"] else "level"
        aux_lines.append(
            f"- **{label}** ({a['publisher']}:{a['series']}, {unit}): "
            f"FRA pre-window mean {a['fra_pre_mean']:.3f}; "
            f"treatment-window {a['fra_treat_mean']:.3f} "
            f"(Δ vs pre {a['fra_change_treat_minus_pre']:+.3f}); "
            f"recovery-window {a['fra_recov_mean']:.3f} "
            f"(Δ vs pre {a['fra_change_recov_minus_pre']:+.3f})."
        )

    lines = [
        "# Mitterrand nationalisations and French productivity",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Country-level event study of French TFP around the 1981-1983 "
        "nationalisations and the 1983 'tournant de la rigueur' reversal, "
        "benchmarked against European-peer controls (DEU, GBR, ITA, NLD, BEL, "
        "ESP). PWT 'rtfpna' (real TFP at constant national prices) is the "
        "primary outcome. Pre-trend window 1975-1980; treatment window "
        "1981-1983; recovery window 1984-1990.",
        "",
        "## Headline numbers",
        "",
        f"- FRA 1975-80 pre-trend slope (log-TFP per year): "
        f"**{fra_slope*100:+.3f}%/yr** over n={fra_n_pre} pre-period years.",
        f"- FRA 1981-83 mean log-TFP gap vs its own pre-trend: "
        f"**{fra_gap_treat*100:+.3f}%**.",
        f"- European-peer mean 1981-83 gap (n={n_avail_controls} controls): "
        f"**{control_gap_treat_mean*100:+.3f}%**.",
        f"- **Net 1981-83 dip (FRA − controls): {net_gap_treat*100:+.3f}%** "
        f"(threshold ≤ -1.50%; "
        f"{'PASS' if primary1_dip else 'FAIL'}).",
        f"- FRA 1984-90 mean log-TFP gap vs its own pre-trend: "
        f"**{fra_gap_recov*100:+.3f}%**.",
        f"- European-peer mean 1984-90 gap: **{control_gap_recov_mean*100:+.3f}%**.",
        f"- **Net 1984-90 gap (FRA − controls): {net_gap_recov*100:+.3f}%**.",
        f"- **Recovery delta (net 1984-90 − net 1981-83): "
        f"{recovery_delta*100:+.3f}pp** (threshold ≥ +0.75pp; "
        f"{'PASS' if primary2_recov else 'FAIL'}).",
        "",
        "## Threshold table",
        "",
        "| Component | Threshold | Realised | Pass |",
        "|---|---:|---:|:---:|",
        f"| PRIMARY 1: net 1981-83 dip | ≤ -1.50% | "
        f"{net_gap_treat*100:+.3f}% | {'YES' if primary1_dip else 'no'} |",
        f"| PRIMARY 2: net recovery delta | ≥ +0.75pp | "
        f"{recovery_delta*100:+.3f}pp | {'YES' if primary2_recov else 'no'} |",
        "",
        "## Per-country control results",
        "",
        "| Country | n_pre | pre-slope (%/yr) | gap 1981-83 (%) | gap 1984-90 (%) |",
        "|---|---:|---:|---:|---:|",
    ]
    lines.append(f"| {TREATED} (treated) | {fra_n_pre} | "
                 f"{fra_slope*100:+.3f} | {fra_gap_treat*100:+.3f} | "
                 f"{fra_gap_recov*100:+.3f} |")
    for c in CONTROLS:
        r = control_results[c]
        if not r["available"]:
            lines.append(f"| {c} (control) | {r['n_pre']} | (insufficient data) | — | — |")
        else:
            lines.append(f"| {c} (control) | {r['n_pre']} | "
                         f"{r['slope']*100:+.3f} | {r['gap_treat']*100:+.3f} | "
                         f"{r['gap_recov']*100:+.3f} |")
    lines.append("")
    lines += [
        "## Informative WDI auxiliaries",
        "",
        *(aux_lines or ["- (none available)"]),
        "",
        "## Method",
        "",
        "For each country in {FRA} ∪ {DEU, GBR, ITA, NLD, BEL, ESP}: take "
        "log(rtfpna), fit OLS linear pre-trend over 1975-1980, project "
        "forward, compute mean (actual − projected) over the treatment "
        "(1981-83) and recovery (1984-90) windows. The PRIMARY estimand is "
        "the FRA gap minus the simple mean of available control gaps in the "
        "same window — i.e. how much FRA over- or under-performed its own "
        "pre-trend net of any generic European productivity slowdown. A "
        "1.5%-of-TFP under-trend dip plus a half-closure recovery is required "
        "for SUPPORTED.",
        "",
        "## Caveats",
        "",
        "- **Country-level not firm-level.** The original spec requested a "
        "firm-level event study with firm + year FE comparing the 16 "
        "nationalised firms (Saint-Gobain, Thomson, Pechiney, Rhône-Poulenc, "
        "etc.) against industry-matched private comparators. No such "
        "firm-level French panel is in the repo. The country-level outcome "
        "blends nationalised-firm productivity with the rest of the French "
        "economy, attenuating the treatment effect. A SUPPORTED verdict here "
        "is consistent with — but weaker evidence than — the firm-level claim "
        "would give; a REFUTED verdict here is also weaker than firm-level "
        "would be.",
        "- **Confounds.** 1981-1983 also saw the second oil-shock tail, three "
        "Franc devaluations, EMS exit-and-stay-in pressure, and a fiscal "
        "expansion. The control-net design absorbs Europe-common shocks but "
        "not FRA-specific simultaneous shocks. The 1983 tournant itself "
        "bundled disinflation + fiscal consolidation alongside the "
        "nationalisation reversal logic, so the recovery primary is also "
        "FRA-policy-bundle, not nationalisation-reversal-isolated.",
        "- **Pre-trend length.** Only 6 pre-period years (1975-1980). The "
        "estimated pre-slope is therefore noisy; v2 should add a "
        "1965-1980 specification as robustness if PWT coverage extends.",
        "- **Disclosure (per spec).** Authorial bias risk: the classical-"
        "liberal framing wants nationalisation to damage productivity. The "
        "thresholds were pinned without seeing the result.",
        "",
        "## Data",
        "",
    ]
    for k, v in manifest.items():
        if v.get("missing"):
            lines.append(f"- **MISSING** `{v['publisher']}:{v['series']}`")
        else:
            lines.append(f"- {v['publisher']}:{v['series']} — `{v['vintage_file']}`")
    lines += [
        "",
        "## Steelman",
        "",
        "See `hypotheses/steelman/mitterrand_nationalisations_productivity_effect.md`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  primary1 (dip ≤ -1.50%): net={net_gap_treat*100:+.3f}% pass={primary1_dip}")
    print(f"  primary2 (recovery ≥ +0.75pp): delta={recovery_delta*100:+.3f}pp pass={primary2_recov}")


if __name__ == "__main__":
    main()
