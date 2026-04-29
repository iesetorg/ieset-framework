#!/usr/bin/env python3
"""Replication — Korea HCI drive capability effect (1961-1985 vs LATAM ISI donors).

Spec: hypotheses/growth/korea_hci_drive_capability_effect.yaml v1
Position-claim: developmentalism #2 (school predicts: supported)

Tests whether Park's 1961-1979 HCI drive (treated effective 1973 with the
HCI plan) produced durable industrial capability + export competitiveness
that outperformed the LATAM ISI counterfactual donor pool {BRA,ARG,MEX,
COL,CHL,PER} by 1985.

Two dispositive primary legs:
  PRIMARY-LEVELS: KOR-vs-LATAM-mean cumulative log-divergence on
                  (a) WDI real exports NE.EXP.GNFS.KD AND
                  (b) WDI industry value added NV.IND.TOTL.KD
                  must each exceed +1.00 log points (~2.7x more growth)
                  by 1985 (industry-VA baseline 1965 due to coverage).
  PRIMARY-DiD:    KOR-vs-LATAM-mean DiD on PWT rgdpna around 1973
                  must exceed +0.20 log points (post-1973 KOR
                  acceleration relative to LATAM-mean DiD).

INFORMATIVE secondary:
  - Real-exports DiD around 1973 (sign reported; HCI-specific timing)
  - PWT TFP (rtfpna) cumulative gap
  - Maddison gdppc_ppp cumulative gap
  - Pre-1973 KOR-vs-LATAM industry-VA gap (placebo / pre-trend)

This is a spec-compliant simplification of the synth-DID estimator
(convex weights deferred to v2 when ECI / HCI-export-share land).
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
HID = "korea_hci_drive_capability_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample
TREATED = "KOR"
DONORS = ["BRA", "ARG", "MEX", "COL", "CHL", "PER"]
ALL = [TREATED] + DONORS

PERIOD = (1961, 1985)
TREAT_YEAR = 1973  # HCI plan launch
INDUSTRY_VA_BASE = 1965  # NV.IND.TOTL.KD coverage starts 1965 for ARG/MEX/COL

# Falsification thresholds (per spec)
LEVELS_LOG_GAP_THRESHOLD = 1.00     # KOR-vs-LATAM cum-log gap
DID_GROWTH_THRESHOLD = 0.20         # KOR-vs-LATAM DiD on rgdpna


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


def load_long(path: Path, value_col: str | None = None) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value) rows.

    For Maddison the value lives in `gdppc`. WDI/PWT use `value`.
    """
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year cols ({list(t.columns)})")
    if value_col and value_col in t.columns:
        t = t.rename(columns={value_col: "value"})
    if "value" not in t.columns:
        raise ValueError(f"{path}: no value column ({list(t.columns)})")
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def cum_log_change(df: pd.DataFrame, country: str, y0: int, y1: int) -> float | None:
    sub = df[df["country_iso3"] == country].copy()
    sub = sub[sub["value"] > 0]
    s = sub.set_index("year")["value"].sort_index()
    if y0 not in s.index or y1 not in s.index:
        return None
    return float(np.log(s[y1]) - np.log(s[y0]))


def did_around_treat(df: pd.DataFrame, country: str, y0: int, treat: int, y1: int) -> float | None:
    """Returns (post_log_growth) - (pre_log_growth) for one country."""
    pre = cum_log_change(df, country, y0, treat)
    post = cum_log_change(df, country, treat, y1)
    if pre is None or post is None:
        return None
    return post - pre


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Load vintages ----------
    paths = {
        "real_exports": latest("world_bank_wdi", "NE.EXP.GNFS.KD"),
        "industry_va": latest("world_bank_wdi", "NV.IND.TOTL.KD"),
        "pwt_rgdpna": latest("pwt", "rgdpna"),
        "pwt_rtfpna": latest("pwt", "rtfpna"),
        "maddison_gdppc": latest("maddison", "gdppc_ppp"),
    }
    series_meta = {
        "real_exports":     ("world_bank_wdi", "NE.EXP.GNFS.KD"),
        "industry_va":      ("world_bank_wdi", "NV.IND.TOTL.KD"),
        "pwt_rgdpna":       ("pwt", "rgdpna"),
        "pwt_rtfpna":       ("pwt", "rtfpna"),
        "maddison_gdppc":   ("maddison", "gdppc_ppp"),
    }
    manifest = {
        k: {
            "publisher": series_meta[k][0],
            "series": series_meta[k][1],
            "vintage_file": str(p.relative_to(REPO_ROOT)),
            "sha256": sha256(p),
        }
        for k, p in paths.items()
    }

    real_exports = load_long(paths["real_exports"])
    industry_va = load_long(paths["industry_va"])
    pwt_rgdpna = load_long(paths["pwt_rgdpna"])
    pwt_rtfpna = load_long(paths["pwt_rtfpna"])
    maddison = load_long(paths["maddison_gdppc"], value_col="gdppc")

    # ---------- Coverage / METHOD_VALID ----------
    def country_year_count(df, country, y0, y1):
        return int(((df["country_iso3"] == country) & df["year"].between(y0, y1)).sum())

    coverage = {}
    for series_name, df, base in [
        ("real_exports", real_exports, PERIOD[0]),
        ("industry_va", industry_va, INDUSTRY_VA_BASE),
        ("pwt_rgdpna", pwt_rgdpna, PERIOD[0]),
        ("pwt_rtfpna", pwt_rtfpna, PERIOD[0]),
        ("maddison_gdppc", maddison, PERIOD[0]),
    ]:
        coverage[series_name] = {
            c: country_year_count(df, c, base, PERIOD[1]) for c in ALL
        }

    donors_with_full_coverage = {
        s: sum(1 for c in DONORS if v[c] >= (PERIOD[1] - (INDUSTRY_VA_BASE if s == "industry_va" else PERIOD[0]) + 1))
        for s, v in coverage.items()
    }
    # METHOD_VALID gate: ≥5 of 6 donors with full coverage on the two
    # series used by PRIMARY-LEVELS + the rgdpna series for PRIMARY-DiD.
    method_valid = (
        donors_with_full_coverage["real_exports"] >= 5
        and donors_with_full_coverage["industry_va"] >= 5
        and donors_with_full_coverage["pwt_rgdpna"] >= 5
        and coverage["real_exports"][TREATED] >= (PERIOD[1] - PERIOD[0] + 1)
        and coverage["industry_va"][TREATED] >= (PERIOD[1] - INDUSTRY_VA_BASE + 1)
        and coverage["pwt_rgdpna"][TREATED] >= (PERIOD[1] - PERIOD[0] + 1)
    )

    # ---------- PRIMARY-LEVELS: cum-log-divergence ----------
    def kor_vs_latam_cum(df, y0, y1):
        kor_cum = cum_log_change(df, TREATED, y0, y1)
        donor_vals = [cum_log_change(df, c, y0, y1) for c in DONORS]
        donor_vals = [v for v in donor_vals if v is not None]
        latam_cum = float(np.mean(donor_vals)) if donor_vals else None
        gap = (kor_cum - latam_cum) if (kor_cum is not None and latam_cum is not None) else None
        return kor_cum, latam_cum, gap, donor_vals

    exports_kor, exports_latam, exports_gap, _ = kor_vs_latam_cum(
        real_exports, PERIOD[0], PERIOD[1]
    )
    industry_kor, industry_latam, industry_gap, _ = kor_vs_latam_cum(
        industry_va, INDUSTRY_VA_BASE, PERIOD[1]
    )

    levels_exports_pass = exports_gap is not None and exports_gap > LEVELS_LOG_GAP_THRESHOLD
    levels_industry_pass = industry_gap is not None and industry_gap > LEVELS_LOG_GAP_THRESHOLD
    primary_levels_pass = levels_exports_pass and levels_industry_pass
    primary_levels_partial = levels_exports_pass != levels_industry_pass

    # ---------- PRIMARY-DiD: rgdpna around 1973 ----------
    kor_did_rgdpna = did_around_treat(pwt_rgdpna, TREATED, PERIOD[0], TREAT_YEAR, PERIOD[1])
    donor_dids_rgdpna = [did_around_treat(pwt_rgdpna, c, PERIOD[0], TREAT_YEAR, PERIOD[1]) for c in DONORS]
    donor_dids_rgdpna = [v for v in donor_dids_rgdpna if v is not None]
    latam_did_rgdpna = float(np.mean(donor_dids_rgdpna)) if donor_dids_rgdpna else None
    did_rgdpna_gap = (
        kor_did_rgdpna - latam_did_rgdpna
        if (kor_did_rgdpna is not None and latam_did_rgdpna is not None)
        else None
    )
    primary_did_pass = did_rgdpna_gap is not None and did_rgdpna_gap > DID_GROWTH_THRESHOLD

    # ---------- INFORMATIVE secondary ----------
    # 1. Pre-1973 industry-VA placebo
    pre_industry_kor, pre_industry_latam, pre_industry_gap, _ = kor_vs_latam_cum(
        industry_va, INDUSTRY_VA_BASE, TREAT_YEAR
    )
    pretrend_clean = pre_industry_gap is not None and pre_industry_gap < LEVELS_LOG_GAP_THRESHOLD

    # 2. Export-channel DiD (informative-only — see methodology_note)
    kor_did_exports = did_around_treat(real_exports, TREATED, PERIOD[0], TREAT_YEAR, PERIOD[1])
    donor_dids_exp = [did_around_treat(real_exports, c, PERIOD[0], TREAT_YEAR, PERIOD[1]) for c in DONORS]
    donor_dids_exp = [v for v in donor_dids_exp if v is not None]
    latam_did_exports = float(np.mean(donor_dids_exp)) if donor_dids_exp else None
    did_exports_gap = (
        kor_did_exports - latam_did_exports
        if (kor_did_exports is not None and latam_did_exports is not None)
        else None
    )

    # 3. TFP cumulative gap
    tfp_kor, tfp_latam, tfp_gap, _ = kor_vs_latam_cum(pwt_rtfpna, PERIOD[0], PERIOD[1])
    # 4. Maddison gdppc gap
    madd_kor, madd_latam, madd_gap, _ = kor_vs_latam_cum(maddison, PERIOD[0], PERIOD[1])

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive (method-validity failure) — donor coverage too sparse: "
            f"{donors_with_full_coverage}"
        )
    elif primary_levels_pass and primary_did_pass:
        verdict = (
            f"SUPPORTED — KOR-vs-LATAM cum-log gap by 1985: "
            f"real exports {exports_gap:+.2f} (>{LEVELS_LOG_GAP_THRESHOLD:+.2f}), "
            f"industry VA {industry_gap:+.2f} (>{LEVELS_LOG_GAP_THRESHOLD:+.2f}); "
            f"DiD on PWT rgdpna around 1973: {did_rgdpna_gap:+.2f} "
            f"(>{DID_GROWTH_THRESHOLD:+.2f}). "
            f"Pre-trend (industry VA pre-1973 gap): {pre_industry_gap:+.2f}."
        )
    elif primary_levels_pass and not primary_did_pass:
        verdict = (
            f"partial — Capability LEVELS strongly diverge in KOR's favour by 1985 "
            f"(exports gap {exports_gap:+.2f}, industry VA gap {industry_gap:+.2f}, "
            f"both >{LEVELS_LOG_GAP_THRESHOLD:+.2f}), BUT the DiD-around-1973 test on PWT real GDP "
            f"({did_rgdpna_gap:+.2f}) misses the {DID_GROWTH_THRESHOLD:+.2f} threshold — i.e. "
            f"capability divergence is real but is not concentrated in the post-1973 HCI window "
            f"(much of it is pre-HCI Park-era export-promotion era starting 1964)."
        )
    elif primary_levels_partial:
        verdict = (
            f"partial — One of two PRIMARY-LEVELS gates clears: "
            f"exports gap {exports_gap:+.2f} ({'pass' if levels_exports_pass else 'fail'}), "
            f"industry-VA gap {industry_gap:+.2f} ({'pass' if levels_industry_pass else 'fail'}); "
            f"DiD-rgdpna {did_rgdpna_gap:+.2f} ({'pass' if primary_did_pass else 'fail'})."
        )
    elif (exports_gap is not None and exports_gap < 0) or (industry_gap is not None and industry_gap < 0):
        verdict = (
            f"refuted — KOR did NOT outpace LATAM on capability levels by 1985: "
            f"exports gap {exports_gap:+.2f}, industry-VA gap {industry_gap:+.2f}."
        )
    else:
        verdict = (
            f"refuted — Neither PRIMARY-LEVELS gate clears the {LEVELS_LOG_GAP_THRESHOLD:+.2f} "
            f"threshold: exports gap {exports_gap:+.2f}, industry-VA gap {industry_gap:+.2f}; "
            f"DiD-rgdpna {did_rgdpna_gap:+.2f}."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "primary_levels_pass": primary_levels_pass,
        "primary_levels_exports_pass": levels_exports_pass,
        "primary_levels_industry_pass": levels_industry_pass,
        "primary_did_pass": primary_did_pass,
        "pretrend_clean": pretrend_clean,
        "thresholds": {
            "levels_log_gap": LEVELS_LOG_GAP_THRESHOLD,
            "did_growth": DID_GROWTH_THRESHOLD,
        },
        "primary_levels": {
            "real_exports": {"kor_cum_log_change_1961_1985": exports_kor,
                              "latam_mean_cum_log_change_1961_1985": exports_latam,
                              "kor_minus_latam_gap": exports_gap},
            "industry_value_added": {"kor_cum_log_change_1965_1985": industry_kor,
                                     "latam_mean_cum_log_change_1965_1985": industry_latam,
                                     "kor_minus_latam_gap": industry_gap,
                                     "baseline_year": INDUSTRY_VA_BASE},
        },
        "primary_did": {
            "pwt_rgdpna_kor_did_around_1973": kor_did_rgdpna,
            "pwt_rgdpna_latam_mean_did_around_1973": latam_did_rgdpna,
            "kor_minus_latam_did_gap": did_rgdpna_gap,
        },
        "informative": {
            "industry_va_pretrend_pre_1973_kor_minus_latam_gap": pre_industry_gap,
            "real_exports_did_around_1973_kor_minus_latam": did_exports_gap,
            "pwt_rtfpna_cum_kor_minus_latam_1961_1985": tfp_gap,
            "maddison_gdppc_ppp_cum_kor_minus_latam_1961_1985": madd_gap,
        },
        "coverage": coverage,
        "donors_with_full_coverage": donors_with_full_coverage,
        "treated": TREATED,
        "donors": DONORS,
        "treat_year": TREAT_YEAR,
        "period": list(PERIOD),
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- Chart: indexed log-output around 1973 ----------
    # Show real exports indexed to 1973 = 0 in log-points, KOR vs LATAM mean.
    palette = {
        "KOR": "#E15759",
        "BRA": "#4E79A7", "ARG": "#59A14F", "MEX": "#B07AA1",
        "COL": "#F28E2B", "CHL": "#76B7B2", "PER": "#EDC948",
        "LATAM_MEAN": "#1f1f1f",
    }
    series = []
    # KOR series — log-difference vs 1973 baseline
    for c in ALL:
        sub = real_exports[real_exports["country_iso3"] == c].set_index("year")["value"].sort_index()
        sub = sub[(sub.index >= PERIOD[0]) & (sub.index <= PERIOD[1])]
        if TREAT_YEAR not in sub.index or sub[TREAT_YEAR] <= 0:
            continue
        baseline_log = np.log(sub[TREAT_YEAR])
        pts = [
            {"x": int(y), "y": float(np.log(v) - baseline_log)}
            for y, v in sub.items() if v > 0
        ]
        series.append({
            "id": c, "label": c, "color": palette.get(c, "#888"),
            "treated": (c == TREATED), "points": pts,
        })

    # LATAM mean trace
    latam_mean_pts = []
    for y in range(PERIOD[0], PERIOD[1] + 1):
        vals = []
        for c in DONORS:
            sub = real_exports[(real_exports["country_iso3"] == c)
                                & (real_exports["year"] == y)]["value"]
            if not sub.empty:
                v = float(sub.iloc[0])
                if v > 0:
                    base_sub = real_exports[(real_exports["country_iso3"] == c)
                                              & (real_exports["year"] == TREAT_YEAR)]["value"]
                    if not base_sub.empty and float(base_sub.iloc[0]) > 0:
                        vals.append(np.log(v) - np.log(float(base_sub.iloc[0])))
        if vals:
            latam_mean_pts.append({"x": int(y), "y": float(np.mean(vals))})
    series.insert(0, {
        "id": "LATAM_MEAN", "label": "LATAM mean", "color": palette["LATAM_MEAN"],
        "treated": True, "points": latam_mean_pts,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Korea vs LATAM ISI donors — real exports indexed to 1973 = 0 (log)",
        "subtitle": (
            f"By 1985: KOR cum-log gap vs LATAM mean = {exports_gap:+.2f} on real exports, "
            f"{industry_gap:+.2f} on industry VA (threshold {LEVELS_LOG_GAP_THRESHOLD:+.2f}); "
            f"DiD on PWT rgdpna around 1973 = {did_rgdpna_gap:+.2f} "
            f"(threshold {DID_GROWTH_THRESHOLD:+.2f})."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log real exports (1973 = 0)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": TREAT_YEAR, "label": "HCI plan launched (1973)"},
            {"type": "note",
             "label": (f"KOR cum 1961→1985 log-export change: {exports_kor:+.2f}; "
                        f"LATAM mean: {exports_latam:+.2f}; gap: {exports_gap:+.2f}.")},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients table ----------
    rows = [
        {"spec": "primary_levels", "term": "real_exports_kor_cum", "estimate": exports_kor},
        {"spec": "primary_levels", "term": "real_exports_latam_mean_cum", "estimate": exports_latam},
        {"spec": "primary_levels", "term": "real_exports_kor_minus_latam_gap", "estimate": exports_gap},
        {"spec": "primary_levels", "term": "industry_va_kor_cum_1965_1985", "estimate": industry_kor},
        {"spec": "primary_levels", "term": "industry_va_latam_mean_cum_1965_1985", "estimate": industry_latam},
        {"spec": "primary_levels", "term": "industry_va_kor_minus_latam_gap", "estimate": industry_gap},
        {"spec": "primary_did",    "term": "rgdpna_kor_did_around_1973", "estimate": kor_did_rgdpna},
        {"spec": "primary_did",    "term": "rgdpna_latam_mean_did_around_1973", "estimate": latam_did_rgdpna},
        {"spec": "primary_did",    "term": "rgdpna_kor_minus_latam_did_gap", "estimate": did_rgdpna_gap},
        {"spec": "informative",    "term": "industry_va_pretrend_pre_1973_gap", "estimate": pre_industry_gap},
        {"spec": "informative",    "term": "real_exports_did_around_1973_gap", "estimate": did_exports_gap},
        {"spec": "informative",    "term": "rtfpna_cum_kor_minus_latam_1961_1985", "estimate": tfp_gap},
        {"spec": "informative",    "term": "maddison_gdppc_ppp_cum_kor_minus_latam_1961_1985", "estimate": madd_gap},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Manifest ----------
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        f"estimator: kor_vs_latam_levels_plus_did\n"
        "vintages:\n"
        + "".join(
            f"  {k}:\n"
            f"    publisher: {v['publisher']}\n"
            f"    series: {v['series']}\n"
            f"    vintage_file: {v['vintage_file']}\n"
            f"    sha256: {v['sha256']}\n"
            for k, v in manifest.items()
        )
    )

    # ---------- Result card ----------
    card = [
        f"# Korea HCI drive capability effect (1961-1985 vs LATAM ISI)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- **PRIMARY-LEVELS (capability divergence by 1985):**",
        f"  - Real exports (WDI NE.EXP.GNFS.KD): KOR cum log-change "
        f"`{exports_kor:+.3f}` vs LATAM mean `{exports_latam:+.3f}` "
        f"→ KOR-LATAM gap **`{exports_gap:+.3f}`** "
        f"(threshold `> +{LEVELS_LOG_GAP_THRESHOLD:.2f}`, "
        f"{'PASS' if levels_exports_pass else 'FAIL'}).",
        f"  - Industry value added (WDI NV.IND.TOTL.KD, base 1965): "
        f"KOR `{industry_kor:+.3f}` vs LATAM mean `{industry_latam:+.3f}` "
        f"→ gap **`{industry_gap:+.3f}`** "
        f"(threshold `> +{LEVELS_LOG_GAP_THRESHOLD:.2f}`, "
        f"{'PASS' if levels_industry_pass else 'FAIL'}).",
        f"- **PRIMARY-DiD (HCI causal channel around 1973):**",
        f"  - PWT rgdpna: KOR DiD `{kor_did_rgdpna:+.3f}` − LATAM DiD "
        f"`{latam_did_rgdpna:+.3f}` = **`{did_rgdpna_gap:+.3f}`** "
        f"(threshold `> +{DID_GROWTH_THRESHOLD:.2f}`, "
        f"{'PASS' if primary_did_pass else 'FAIL'}).",
        f"- **INFORMATIVE secondary:**",
        f"  - Industry-VA pre-trend (1965-1973 gap): `{pre_industry_gap:+.3f}` "
        f"({'clean' if pretrend_clean else 'concerning — pre-trend already exceeds the 1.0 threshold'}).",
        f"  - Real-exports DiD around 1973: `{did_exports_gap:+.3f}` "
        f"(informative-only — see methodology note; pre-1973 export miracle "
        f"means HCI-DiD on exports may not signal HCI's capability effect).",
        f"  - PWT rtfpna cum 1961-1985 KOR-LATAM: `{tfp_gap:+.3f}`.",
        f"  - Maddison gdppc_ppp cum 1961-1985 KOR-LATAM: `{madd_gap:+.3f}`.",
        f"- **METHOD_VALID:** {method_valid} "
        f"(donor full-coverage counts: {donors_with_full_coverage}).",
        "",
        "## Method",
        "",
        "Spec calls for synth-DID with KOR treated 1973 and LATAM ISI donor",
        "pool {BRA, ARG, MEX, COL, CHL, PER}. The dispositive outcomes asked",
        "for in the original spec — heavy-industry export share + Hidalgo-",
        "Hausmann ECI — are not on disk. v1 substitutes WDI real exports +",
        "WDI industry value added + PWT real GDP / TFP as proxy outcomes,",
        "with the synth-DID convex weights collapsed to an equal-weighted",
        "LATAM mean (donor pool is small enough that this is informative).",
        "",
        "Two PRIMARY tests:",
        "",
        "1. **Levels-divergence by 1985** on real exports + industry VA. KOR's",
        "   1961→1985 log change minus the LATAM-donor mean of the same.",
        "   Threshold: > +1.00 log points (~e^1 ≈ 2.7x more growth) on each.",
        "   Both must clear for SUPPORTED.",
        "2. **DiD around 1973** on PWT rgdpna. (post-1973 KOR log-growth −",
        "   pre-1973 KOR log-growth) − the same for LATAM mean. Threshold:",
        "   > +0.20 log points.",
        "",
        "Industry-VA baseline is 1965 (not 1961) because WDI NV.IND.TOTL.KD",
        "coverage starts 1965 for ARG/MEX/COL.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NE.EXP.GNFS.KD",
        f"- world_bank_wdi:NV.IND.TOTL.KD",
        f"- pwt:rgdpna",
        f"- pwt:rtfpna",
        f"- maddison:gdppc_ppp",
        "",
        "## Steelman",
        "",
        "See `hypotheses/steelman/korea_hci_drive_capability_effect.md` for",
        "the live concerns about this hypothesis (US security umbrella, the",
        "1964 export-promotion turn pre-dating HCI, alternative reads of the",
        "LATAM ISI counterfactual).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
