#!/usr/bin/env python3
"""Replication — Petro reform package economic trajectory (Colombia, 2022-present).

Spec: hypotheses/growth/petro_reform_package_economic_trajectory_2022_present.yaml v1
Position-claim: post_keynesian #15 (school predicts: mixed)

Symmetric-assessment classification of Colombia's macro trajectory under
Petro (treatment year 2022, inauguration 2022Q3) vs an equal-weighted
peer pool {PER, CHL, MEX}, using publisher-on-disk data only:

  PRIMARY 1: PETRO_GAP_GDP — cumulative log-GDP gap from 2023 onwards
    (year-on-year log-growth derived from IMF WEO NGDP_RPCH, accumulated
    from 2022 = 0). Sign and magnitude relative to peer mean classify.
  PRIMARY 2: PETRO_GAP_FDI — cumulative gap in FDI net inflows (% of
    GDP, WDI BX.KLT.DINV.WD.GD.ZS), summed from 2022 onwards.

  Classification (both must agree on sign and clear the magnitude band):
    supported-negative  : GDP gap < -0.030 AND FDI gap < -1.0
    supported-positive  : GDP gap > +0.030 AND FDI gap > +1.0
    supported-null      : |GDP gap| <= 0.015 AND |FDI gap| <= 0.5
    not-informative     : everything else (mixed sign or in the
                          "between bands" intermediate magnitude)

  INFORMATIVE (reported, non-gating): pre-treatment parallel-growth
    check 2014-2021 ex-2020 — mean absolute COL-vs-peer growth-rate
    difference should be <= 1.0 percentage points for the synthetic
    counterfactual to be defensible.
  AUXILIARY: BIS WS_EER REER divergence indexed to 2022 (annualised
    from monthly).
  METHOD_VALID: at least 2 post-treatment years (>=2023, 2024) for
    COL plus at least 2 of the 3 donors on each outcome; otherwise
    emit `inconclusive` with a data-gap note.

This is an EARLY-ASSESSMENT run. The spec is pre-registered to a v1
run at 2027 with a quarterly panel and JPMorgan EMBI+ spreads; this
2026 run uses the annual data already on disk.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "petro_reform_package_economic_trajectory_2022_present"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "COL"
DONORS = ["PER", "CHL", "MEX"]
ALL_COUNTRIES = [TREATED] + DONORS
TREATMENT_YEAR = 2022           # Petro inauguration 2022Q3; 2022 is the
                                # last pre-treatment full year for cum-log-GDP
                                # (cum-gap accumulates from 2023 onwards).
# IMF WEO mixes actuals and forecasts; cap at the last published actual to
# avoid grading on IMF projections. As of the 2026-04 WEO vintage, actuals
# extend through 2024 for COL/PER/CHL/MEX. Bump when a newer WEO actuals
# year lands; the script will detect the new ceiling but keep this guard.
ACTUALS_END_YEAR = 2024
PRE_PERIOD = (2014, 2021)        # parallel-trend window
COVID_YEAR = 2020
ISO2_TO_ISO3 = {"CO": "COL", "PE": "PER", "CL": "CHL", "MX": "MEX"}

# Dispositive thresholds (matching spec.falsification.threshold)
GDP_BAND_DISPOSITIVE = 0.030     # log-points; > 3pp cumulative
GDP_BAND_NULL = 0.015            # log-points; <= 1.5pp counts as null
FDI_BAND_DISPOSITIVE = 1.0       # cumulative pp-years
FDI_BAND_NULL = 0.5              # cumulative pp-years
PRETREND_TOLERANCE_PP = 1.0      # mean abs growth-rate gap, %


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_iso3_year_value(path: Path) -> pd.DataFrame:
    """Standard country_iso3 / year / value loader for IMF + WDI parquets."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise RuntimeError(
            f"{path.name}: missing country_iso3/year columns ({list(t.columns)})"
        )
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator_id", "frequency"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise RuntimeError(f"{path.name}: no value column")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["country_iso3"] = t["country_iso3"].astype(str).str.upper()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def load_bis_eer(path: Path) -> pd.DataFrame:
    """BIS WS_EER: monthly real broad EER, annualised mean. iso2 → iso3."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t.get("FREQ") == "M") & (t.get("EER_TYPE") == "R") &
            (t.get("EER_BASKET") == "B")].copy()
    if sub.empty:
        # Fall back to nominal broad if real-broad missing
        sub = t[(t.get("FREQ") == "M") & (t.get("EER_BASKET") == "B")].copy()
    if sub.empty:
        return pd.DataFrame(columns=["country_iso3", "year", "value"])
    sub["year"] = sub["period"].astype(str).str[:4].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["country_iso3"] = sub["REF_AREA"].map(ISO2_TO_ISO3).fillna(sub["REF_AREA"])
    sub = sub[sub["country_iso3"].isin(ALL_COUNTRIES)]
    out = (sub.groupby(["country_iso3", "year"], as_index=False)["value"].mean())
    return out.dropna(subset=["value"])


def series_for(df: pd.DataFrame, country: str) -> pd.Series:
    s = (df[df["country_iso3"] == country]
         .set_index("year")["value"].sort_index().dropna())
    s.index = s.index.astype(int)
    return s


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- pin vintages ----------
    gdp_growth_path = latest("imf", "NGDP_RPCH")
    fdi_path = latest("world_bank_wdi", "BX.KLT.DINV.WD.GD.ZS")
    reer_path = latest("bis", "WS_EER")

    if gdp_growth_path is None or fdi_path is None:
        verdict = (
            "inconclusive — required vintages missing: "
            f"{'imf:NGDP_RPCH ' if gdp_growth_path is None else ''}"
            f"{'world_bank_wdi:BX.KLT.DINV.WD.GD.ZS ' if fdi_path is None else ''}"
        )
        (OUT_DIR / "diagnostics.json").write_text(
            json.dumps({"verdict": verdict, "data_gap": True}, indent=2) + "\n"
        )
        print(verdict)
        return 0

    manifest: dict[str, dict[str, str]] = {}
    manifest["real_gdp_growth"] = {
        "publisher": "imf", "series": "NGDP_RPCH",
        "vintage_file": str(gdp_growth_path.relative_to(REPO_ROOT)),
        "sha256": sha256(gdp_growth_path),
    }
    manifest["fdi_pct_gdp"] = {
        "publisher": "world_bank_wdi", "series": "BX.KLT.DINV.WD.GD.ZS",
        "vintage_file": str(fdi_path.relative_to(REPO_ROOT)),
        "sha256": sha256(fdi_path),
    }
    if reer_path is not None:
        manifest["reer"] = {
            "publisher": "bis", "series": "WS_EER",
            "vintage_file": str(reer_path.relative_to(REPO_ROOT)),
            "sha256": sha256(reer_path),
        }

    growth_df = load_iso3_year_value(gdp_growth_path)
    growth_df = growth_df[growth_df["country_iso3"].isin(ALL_COUNTRIES)]
    fdi_df = load_iso3_year_value(fdi_path)
    fdi_df = fdi_df[fdi_df["country_iso3"].isin(ALL_COUNTRIES)]
    reer_df = load_bis_eer(reer_path) if reer_path is not None else pd.DataFrame()

    # ---------- pivot ----------
    growth_panel = {c: series_for(growth_df, c) for c in ALL_COUNTRIES}
    fdi_panel = {c: series_for(fdi_df, c) for c in ALL_COUNTRIES}
    reer_panel = {c: series_for(reer_df, c) for c in ALL_COUNTRIES} if not reer_df.empty else {}

    # Determine the latest post-treatment year present for COL on each outcome
    col_growth = growth_panel[TREATED]
    col_fdi = fdi_panel[TREATED]

    # Restrict to actuals only — IMF WEO mixes published forecasts which we
    # do not want to grade as realised outcomes.
    post_growth_years = sorted(
        [y for y in col_growth.index if TREATMENT_YEAR < y <= ACTUALS_END_YEAR]
    )
    post_fdi_years = sorted([y for y in col_fdi.index if y >= TREATMENT_YEAR])

    n_post_growth = len(post_growth_years)
    donors_present_growth = [d for d in DONORS
                             if any(y > TREATMENT_YEAR for y in growth_panel[d].index)]
    donors_present_fdi = [d for d in DONORS
                          if any(y >= TREATMENT_YEAR for y in fdi_panel[d].index)]

    method_valid = (n_post_growth >= 2
                    and len(donors_present_growth) >= 2
                    and len(donors_present_fdi) >= 2)

    # ---------- PRIMARY 1: cumulative log-GDP gap ----------
    # NGDP_RPCH is annual real GDP growth, %; convert to log-growth.
    def log_growth(country: str, year: int) -> float | None:
        s = growth_panel[country]
        if year not in s.index:
            return None
        return float(np.log1p(s[year] / 100.0))

    # cum-log-GDP, indexed to 2022 = 0; sum log-growths for years 2023..end.
    end_year_growth = max(post_growth_years) if post_growth_years else TREATMENT_YEAR
    years_post_growth = list(range(TREATMENT_YEAR + 1, end_year_growth + 1))

    cum_log = {c: 0.0 for c in ALL_COUNTRIES}
    cum_log_path: dict[str, list[tuple[int, float]]] = {c: [(TREATMENT_YEAR, 0.0)] for c in ALL_COUNTRIES}
    for c in ALL_COUNTRIES:
        running = 0.0
        for y in years_post_growth:
            g = log_growth(c, y)
            if g is None:
                continue
            running += g
            cum_log_path[c].append((y, running))
        cum_log[c] = running

    peer_cum_log_end = float(np.mean([cum_log[d] for d in donors_present_growth])) \
        if donors_present_growth else float("nan")
    petro_gap_gdp = cum_log[TREATED] - peer_cum_log_end

    # Per-year COL-vs-peer cumulative gap path
    gap_path = []
    for y in [TREATMENT_YEAR] + years_post_growth:
        col_v = next((v for yy, v in cum_log_path[TREATED] if yy == y), None)
        peer_vals = [next((v for yy, v in cum_log_path[d] if yy == y), None)
                     for d in donors_present_growth]
        peer_vals = [v for v in peer_vals if v is not None]
        if col_v is not None and peer_vals:
            gap_path.append({"year": y, "col_minus_peer_cum_log": col_v - float(np.mean(peer_vals))})

    # ---------- PRIMARY 2: cumulative FDI gap ----------
    end_year_fdi = max(post_fdi_years) if post_fdi_years else TREATMENT_YEAR
    years_post_fdi = list(range(TREATMENT_YEAR, end_year_fdi + 1))

    fdi_yearly_gap = []
    cum_fdi_gap = 0.0
    fdi_per_year_detail = []
    for y in years_post_fdi:
        col_v = float(col_fdi[y]) if y in col_fdi.index else None
        peer_vs = []
        for d in donors_present_fdi:
            sd = fdi_panel[d]
            if y in sd.index:
                peer_vs.append(float(sd[y]))
        if col_v is None or not peer_vs:
            continue
        peer_mean = float(np.mean(peer_vs))
        diff = col_v - peer_mean
        cum_fdi_gap += diff
        fdi_yearly_gap.append({"year": y, "col": col_v,
                               "peer_mean": peer_mean, "diff": diff,
                               "cumulative": cum_fdi_gap})
        fdi_per_year_detail.append({"year": int(y), "col": col_v,
                                    "peer_mean": peer_mean, "diff": diff,
                                    "cumulative": cum_fdi_gap})

    petro_gap_fdi = cum_fdi_gap

    # ---------- INFORMATIVE: pre-trend parallel-growth ----------
    pretrend_diffs = []
    pretrend_per_year = []
    for y in range(PRE_PERIOD[0], PRE_PERIOD[1] + 1):
        if y == COVID_YEAR:
            continue
        col_g = growth_panel[TREATED]
        if y not in col_g.index:
            continue
        peer_gs = []
        for d in DONORS:
            sd = growth_panel[d]
            if y in sd.index:
                peer_gs.append(float(sd[y]))
        if not peer_gs:
            continue
        diff = float(col_g[y]) - float(np.mean(peer_gs))
        pretrend_diffs.append(abs(diff))
        pretrend_per_year.append({"year": y, "col_growth": float(col_g[y]),
                                  "peer_mean_growth": float(np.mean(peer_gs)),
                                  "diff": diff})
    mean_abs_pretrend_gap = float(np.mean(pretrend_diffs)) if pretrend_diffs else float("nan")
    pretrend_pass = (np.isfinite(mean_abs_pretrend_gap)
                     and mean_abs_pretrend_gap <= PRETREND_TOLERANCE_PP)

    # ---------- AUXILIARY: REER divergence ----------
    reer_2022_index: dict[str, dict[int, float]] = {}
    if reer_panel:
        for c in ALL_COUNTRIES:
            sr = reer_panel.get(c, pd.Series(dtype=float))
            if sr.empty or 2022 not in sr.index or sr[2022] in (0, None):
                continue
            base = float(sr[2022])
            reer_2022_index[c] = {int(y): float(sr[y] / base * 100.0)
                                  for y in sr.index if pd.notna(sr[y])}

    # ---------- Classification ----------
    if not method_valid:
        classification = "inconclusive"
        verdict_lead = "inconclusive"
        method_note = (
            f"method-validity gap: {n_post_growth} post-treatment growth obs "
            f"(need >=2); donors with growth data: "
            f"{donors_present_growth}; donors with FDI data: {donors_present_fdi}."
        )
    else:
        gdp_neg = petro_gap_gdp < -GDP_BAND_DISPOSITIVE
        gdp_pos = petro_gap_gdp > GDP_BAND_DISPOSITIVE
        gdp_null = abs(petro_gap_gdp) <= GDP_BAND_NULL
        fdi_neg = petro_gap_fdi < -FDI_BAND_DISPOSITIVE
        fdi_pos = petro_gap_fdi > FDI_BAND_DISPOSITIVE
        fdi_null = abs(petro_gap_fdi) <= FDI_BAND_NULL
        if gdp_neg and fdi_neg:
            classification = "supported-negative"
            verdict_lead = "SUPPORTED"
        elif gdp_pos and fdi_pos:
            classification = "supported-positive"
            verdict_lead = "SUPPORTED"
        elif gdp_null and fdi_null:
            classification = "supported-null"
            verdict_lead = "SUPPORTED"
        else:
            classification = "not-informative"
            verdict_lead = "inconclusive"
        method_note = ""

    method_qualifier = ""
    if method_valid and not pretrend_pass:
        method_qualifier = (
            f" (METHOD-VALID flag: pre-trend parallel-growth check failed — "
            f"mean abs COL-vs-peer growth gap 2014-2021 ex-2020 = "
            f"{mean_abs_pretrend_gap:.2f}pp > {PRETREND_TOLERANCE_PP}pp tolerance)"
        )

    summary_numbers = (
        f"PETRO_GAP_GDP = {petro_gap_gdp:+.4f} log-points "
        f"({(np.exp(petro_gap_gdp) - 1) * 100:+.2f}% relative) over "
        f"{TREATMENT_YEAR + 1}-{end_year_growth}; "
        f"PETRO_GAP_FDI = {petro_gap_fdi:+.2f} cumulative pp-of-GDP-years "
        f"({TREATMENT_YEAR}-{end_year_fdi}); donors used: GDP {donors_present_growth}, "
        f"FDI {donors_present_fdi}."
    )
    if classification == "supported-negative":
        verdict = (f"SUPPORTED — supported-negative: Colombia underperformed "
                   f"the peer pool on BOTH growth and FDI. {summary_numbers}")
    elif classification == "supported-positive":
        verdict = (f"SUPPORTED — supported-positive: Colombia outperformed "
                   f"the peer pool on BOTH growth and FDI. {summary_numbers}")
    elif classification == "supported-null":
        verdict = (f"SUPPORTED — supported-null: Petro-era trajectory is "
                   f"within the null band on both metrics. {summary_numbers}")
    elif classification == "not-informative":
        verdict = (f"inconclusive — not-informative: GDP and FDI gaps do "
                   f"not jointly clear a dispositive band (mixed sign or "
                   f"intermediate magnitude). {summary_numbers}")
    else:
        verdict = (f"inconclusive — {method_note} {summary_numbers}")
    verdict = verdict + method_qualifier

    diagnostics = {
        "verdict": verdict,
        "classification": classification,
        "method_valid": method_valid,
        "pretrend_pass": pretrend_pass,
        "petro_gap_gdp_log_points": petro_gap_gdp,
        "petro_gap_gdp_pct_relative": float((np.exp(petro_gap_gdp) - 1) * 100),
        "petro_gap_fdi_cum_pp": petro_gap_fdi,
        "mean_abs_pretrend_growth_gap_pp": mean_abs_pretrend_gap,
        "treatment_year": TREATMENT_YEAR,
        "post_treatment_growth_years": [int(y) for y in years_post_growth],
        "post_treatment_fdi_years": [int(y) for y in years_post_fdi],
        "donors_used_growth": donors_present_growth,
        "donors_used_fdi": donors_present_fdi,
        "thresholds": {
            "gdp_band_dispositive_log": GDP_BAND_DISPOSITIVE,
            "gdp_band_null_log": GDP_BAND_NULL,
            "fdi_band_dispositive_pp": FDI_BAND_DISPOSITIVE,
            "fdi_band_null_pp": FDI_BAND_NULL,
            "pretrend_tolerance_pp": PRETREND_TOLERANCE_PP,
        },
        "cum_log_gdp_endpoint": {c: cum_log[c] for c in ALL_COUNTRIES},
        "cum_log_gdp_path_col_minus_peer": gap_path,
        "fdi_yearly_detail": fdi_per_year_detail,
        "pretrend_per_year": pretrend_per_year,
        "reer_indexed_2022_eq_100": reer_2022_index,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- chart ----------
    palette = {"COL": "#1f4e79", "PER": "#4E79A7",
               "CHL": "#59A14F", "MEX": "#B07AA1"}
    series_chart = []
    for c in ALL_COUNTRIES:
        pts = [{"x": int(y), "y": float(v)} for y, v in cum_log_path[c]]
        series_chart.append({
            "id": c, "label": c, "color": palette[c],
            "treated": (c == TREATED), "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Cumulative log-GDP path, indexed to 2022 = 0",
        "subtitle": (
            f"Treatment year: {TREATMENT_YEAR} (Petro inauguration 2022Q3). "
            f"PETRO_GAP_GDP at {end_year_growth} = {petro_gap_gdp:+.3f} log-points; "
            f"PETRO_GAP_FDI cumulative {TREATMENT_YEAR}-{end_year_fdi} = "
            f"{petro_gap_fdi:+.2f} pp-years. Classification: {classification}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "cumulative log-GDP (2022 = 0)", "type": "linear"},
        "series": series_chart,
        "annotations": [{
            "type": "note",
            "label": (
                f"Equal-weighted donor pool {donors_present_growth}; "
                f"pre-trend mean abs growth gap (2014-2021 ex-2020): "
                f"{mean_abs_pretrend_gap:.2f}pp "
                f"(tol {PRETREND_TOLERANCE_PP}pp; "
                f"{'pass' if pretrend_pass else 'fail'})."
            ),
        }],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- coefficients ----------
    coef_rows = [
        {"spec": "primary1_gdp", "term": "petro_gap_gdp_cum_log", "estimate": petro_gap_gdp},
        {"spec": "primary2_fdi", "term": "petro_gap_fdi_cum_pp", "estimate": petro_gap_fdi},
        {"spec": "informative_pretrend", "term": "mean_abs_pretrend_growth_gap_pp",
         "estimate": mean_abs_pretrend_gap},
    ]
    for c in ALL_COUNTRIES:
        coef_rows.append({"spec": "cum_log_gdp_endpoint",
                          "term": f"cum_log_gdp_{c}_at_{end_year_growth}",
                          "estimate": cum_log[c]})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- manifest ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "early_assessment_symmetric_classification",
        "treatment_year": TREATMENT_YEAR,
        "donors": DONORS,
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- result card ----------
    fdi_table_lines = ["| Year | COL | Peer mean | Diff | Cum diff |",
                       "|---:|---:|---:|---:|---:|"]
    for r in fdi_per_year_detail:
        fdi_table_lines.append(
            f"| {r['year']} | {r['col']:+.2f} | {r['peer_mean']:+.2f} | "
            f"{r['diff']:+.2f} | {r['cumulative']:+.2f} |"
        )
    pretrend_table_lines = ["| Year | COL growth (%) | Peer mean (%) | Diff (pp) |",
                            "|---:|---:|---:|---:|"]
    for r in pretrend_per_year:
        pretrend_table_lines.append(
            f"| {r['year']} | {r['col_growth']:+.2f} | "
            f"{r['peer_mean_growth']:+.2f} | {r['diff']:+.2f} |"
        )

    card_lines = [
        f"# Petro reform package economic trajectory (Colombia, 2022-present)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Classification",
        "",
        f"- **Outcome:** `{classification}`",
        f"- PETRO_GAP_GDP = **{petro_gap_gdp:+.4f} log-points** "
        f"({(np.exp(petro_gap_gdp) - 1) * 100:+.2f}% relative) cumulative "
        f"{TREATMENT_YEAR + 1}-{end_year_growth}.",
        f"- PETRO_GAP_FDI = **{petro_gap_fdi:+.2f}** pp-of-GDP-years "
        f"cumulative {TREATMENT_YEAR}-{end_year_fdi}.",
        f"- Pre-trend (2014-2021 ex-2020) mean abs COL-vs-peer growth gap "
        f"= **{mean_abs_pretrend_gap:.2f}pp** (tol {PRETREND_TOLERANCE_PP}pp; "
        f"{'pass' if pretrend_pass else 'fail'}).",
        "",
        "## Threshold (pre-registered, sharpened in v1)",
        "",
        "| Class | GDP gap (log) | FDI cum gap (pp-yr) |",
        "|---|---:|---:|",
        f"| supported-negative | < {-GDP_BAND_DISPOSITIVE:+.3f} | < {-FDI_BAND_DISPOSITIVE:+.1f} |",
        f"| supported-positive | > {GDP_BAND_DISPOSITIVE:+.3f} | > {FDI_BAND_DISPOSITIVE:+.1f} |",
        f"| supported-null | within ±{GDP_BAND_NULL:+.3f} | within ±{FDI_BAND_NULL:+.1f} |",
        f"| not-informative | otherwise | otherwise |",
        "",
        "## Method",
        "",
        f"Equal-weighted peer pool {{{', '.join(DONORS)}}}; donors actually "
        f"present in the post-treatment window: GDP = {donors_present_growth}, "
        f"FDI = {donors_present_fdi}. Synthetic-DiD weighting collapses to "
        "a degenerate corner solution with only 3 donors at this horizon, "
        "so equal weights with a parallel-pre-trend INFORMATIVE check is "
        "the defensible early-assessment estimator. Quarterly DANE/INEI/"
        "INE/INEGI panels and JPMorgan EMBI+ are deferred to the v1 2027 "
        "run; this run uses IMF WEO + WDI + BIS WS_EER only.",
        "",
        "## FDI gap detail",
        "",
        *fdi_table_lines,
        "",
        "## Pre-trend growth (parallel-trend INFORMATIVE check)",
        "",
        *pretrend_table_lines,
        "",
        "## Data",
        "",
        f"- imf:NGDP_RPCH (annual real-GDP growth, %) — primary GDP source.",
        f"- world_bank_wdi:BX.KLT.DINV.WD.GD.ZS (FDI net inflows, % GDP).",
        f"- bis:WS_EER (REER, monthly real broad → annual mean) — auxiliary.",
        "",
        "## Caveats / steelman",
        "",
        "Early-assessment run with only 2-3 post-treatment annual observations. "
        "The hypothesis is pre-registered to a v1 2027 endpoint with a quarterly "
        "panel and sovereign-spread series; this 2026 read should not be treated "
        "as the final verdict. Petro's largest reforms (pension, labour, health) "
        "were judicially or legislatively blocked, so the *actual* treatment "
        "intensity is well below the programmatic agenda — see "
        "`hypotheses/steelman/petro_reform_package_economic_trajectory_2022_present.md`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card_lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  classification: {classification}")
    print(f"  PETRO_GAP_GDP: {petro_gap_gdp:+.4f} log-points")
    print(f"  PETRO_GAP_FDI: {petro_gap_fdi:+.2f} cumulative pp-years")
    print(f"  pre-trend mean abs gap: {mean_abs_pretrend_gap:.2f}pp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
