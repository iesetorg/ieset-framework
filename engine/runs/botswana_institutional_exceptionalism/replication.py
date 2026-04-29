#!/usr/bin/env python3
"""Replication — Botswana institutional exceptionalism, 1966-2023.

Spec: hypotheses/institutional_quality/botswana_institutional_exceptionalism.yaml v1
Position-claim: institutionalism #12 (school predicts: supported)

Tests three empirical regularities for the AJR-style Botswana exceptionalism
claim using a pure synthetic-control donor-pool design (single treated unit
BWA, donor pool = SSA resource-exporters).

  PRIMARY 1: Botswana's Maddison real GDP per capita synthetic-control gap
             (post-1976 mean log-gap vs SSA donor synth) ≥ +0.30 log-points
             (~35% level outperformance, on a sample where the institutionalist
             school predicts "BWA pulls away substantially").
  PRIMARY 2: BWA annual log-growth 1976-2023 vs donor-pool mean
             log-growth ≥ +2.0 percentage points / yr (the YAML's claim
             threshold).
  INFORMATIVE: V-Dem polyarchy gap (BWA − donor mean) and government-effectiveness
             gap (WGI, 1996+) shown for institutional-channel decomposition;
             they colour the verdict but do not gate it.

Hypothesis SUPPORTED if BOTH primaries hold. REFUTED if BOTH fail
(direction wrong or magnitude < half threshold). PARTIAL otherwise.

METHODOLOGY NOTE: spec called for `synthetic_control` with diamond-rents and
V-Dem covariates as decomposition channels. We implement classic
Abadie-Diamond-Hainmueller (2010) SC matching pre-1976 log-GDP-pc levels;
covariate decomposition is descriptive (gap series rather than channel
attribution). WDI mineral rents (NY.GDP.MINR.RT.ZS) is NOT on disk so the
diamond-rent attribution is reported as a data gap rather than estimated.
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
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "botswana_institutional_exceptionalism"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

TREATED = "BWA"
# SSA resource-exporter donor pool from the spec (sample.countries minus BWA).
DONORS = ["ZMB", "ZWE", "NGA", "AGO", "COD", "GAB", "GHA", "CIV", "NAM", "ZAF"]
PERIOD = (1966, 2023)
TREAT_YEAR = 1976  # spec.estimator.notes: "post-treatment 1976-2023"
PRE_FIT = (1966, 1975)

# Falsification thresholds (made dispositive from spec.falsification.test)
GAP_LOG_THRESHOLD = 0.30          # mean post-treat log-gap ≥ 0.30 (~35% level)
GROWTH_GAP_THRESHOLD_PP = 2.0     # BWA − donor mean annual growth ≥ 2pp/yr


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_maddison():
    p = latest("maddison", "mpd2020")
    t = pq.read_table(p).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["gdppc"] = pd.to_numeric(t["gdppc"], errors="coerce")
    t = t.dropna(subset=["year", "gdppc"])
    t["year"] = t["year"].astype(int)
    out = t[["country_iso3", "year", "gdppc"]].rename(columns={"country_iso3": "country"})
    return out, p


def load_vdem_polyarchy():
    p = latest("vdem", "vdem_cy_full")
    t = pq.read_table(p).to_pandas()
    cols_lower = {c.lower(): c for c in t.columns}
    iso_col = cols_lower.get("country_iso3") or cols_lower.get("country_text_id")
    yr_col = cols_lower.get("year")
    poly_col = cols_lower.get("v2x_polyarchy")
    if iso_col is None or yr_col is None or poly_col is None:
        return None, p
    t = t[[iso_col, yr_col, poly_col]].rename(
        columns={iso_col: "country", yr_col: "year", poly_col: "v2x_polyarchy"}
    )
    t = t[t["country"].notna() & (t["country"].astype(str).str.len() == 3)]
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["v2x_polyarchy"] = pd.to_numeric(t["v2x_polyarchy"], errors="coerce")
    return t.dropna().assign(year=lambda d: d.year.astype(int)), p


def load_wgi_ge():
    p = latest("wgi", "GOV_WGI_GE.EST")
    t = pq.read_table(p).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        # Try alternate naming
        for c in t.columns:
            if c.lower() in ("country_iso3", "iso3", "country_text_id"):
                t = t.rename(columns={c: "country_iso3"})
        if "country_iso3" not in t.columns:
            return None, p
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            return None, p
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.dropna(subset=["year", "value"])
    t["year"] = t["year"].astype(int)
    return t.rename(columns={"country_iso3": "country", "value": "wgi_ge"})[
        ["country", "year", "wgi_ge"]
    ], p


def synthetic_control(panel: pd.DataFrame):
    """Classic Abadie SC: minimise pre-fit SSE on log-GDP-pc level."""
    sub = panel[panel["country"].isin([TREATED] + DONORS)]
    wide = sub.pivot(index="year", columns="country", values="log_gdp_pc")
    pre_years = [y for y in wide.index if PRE_FIT[0] <= y <= PRE_FIT[1]]
    post_years = [y for y in wide.index if TREAT_YEAR <= y <= PERIOD[1]]
    if len(pre_years) < 2:
        return {"error": f"only {len(pre_years)} pre-fit years"}
    valid = [d for d in DONORS
             if wide.loc[pre_years, d].notna().all() and wide.loc[post_years, d].notna().any()]
    if not valid:
        return {"error": "no donors with full pre-fit coverage"}
    pre = wide.loc[pre_years, [TREATED] + valid]
    if pre[TREATED].isna().any():
        return {"error": "treated has missing pre-fit years"}
    treat_pre = pre[TREATED].values
    donor_pre = pre[valid].values

    def loss(w):
        return float(np.sum((treat_pre - donor_pre @ w) ** 2))

    n = len(valid)
    sol = minimize(
        loss, np.ones(n) / n, method="SLSQP",
        bounds=[(0, 1)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
    )
    w = sol.x

    # Build synthetic series across all years where donor coverage holds.
    all_years = sorted(set(pre_years + post_years))
    synth_by_year = {}
    treat_by_year = {}
    for y in all_years:
        if y not in wide.index:
            continue
        donor_row = wide.loc[y, valid]
        if donor_row.notna().all():
            synth_by_year[y] = float(donor_row.values @ w)
        if pd.notna(wide.loc[y, TREATED]):
            treat_by_year[y] = float(wide.loc[y, TREATED])

    pre_gaps = [treat_by_year[y] - synth_by_year[y]
                for y in pre_years if y in synth_by_year and y in treat_by_year]
    post_gaps_by_year = {y: treat_by_year[y] - synth_by_year[y]
                         for y in post_years
                         if y in synth_by_year and y in treat_by_year}
    post_gaps = list(post_gaps_by_year.values())
    return {
        "treat_year": TREAT_YEAR,
        "pre_fit": PRE_FIT,
        "donors": valid,
        "weights": {valid[i]: float(w[i]) for i in range(n)},
        "pre_fit_rmse_log": float(np.sqrt(np.mean(np.square(pre_gaps)))) if pre_gaps else None,
        "post_avg_gap_log": float(np.mean(post_gaps)) if post_gaps else None,
        "post_avg_gap_pct": float(np.expm1(np.mean(post_gaps)) * 100) if post_gaps else None,
        "post_2023_gap_log": post_gaps_by_year.get(2023),
        "synth_by_year": synth_by_year,
        "treat_by_year": treat_by_year,
        "post_gap_by_year": post_gaps_by_year,
    }


def placebo_permutation(panel: pd.DataFrame, valid_donors: list[str]) -> dict:
    """Run SC with each donor as 'treated' to see if BWA's gap is unusual.
    Returns ranks of BWA's post-treat absolute mean gap among donors."""
    gaps = []
    for placebo_unit in [TREATED] + valid_donors:
        # Treat as if this unit were the treated; donor pool = all others
        donors = [d for d in valid_donors if d != placebo_unit]
        if placebo_unit == TREATED:
            donors = valid_donors
        if len(donors) < 2:
            continue
        sub = panel[panel["country"].isin([placebo_unit] + donors)]
        wide = sub.pivot(index="year", columns="country", values="log_gdp_pc")
        pre_years = [y for y in wide.index if PRE_FIT[0] <= y <= PRE_FIT[1]]
        post_years = [y for y in wide.index if TREAT_YEAR <= y <= PERIOD[1]]
        if len(pre_years) < 2:
            continue
        if placebo_unit not in wide.columns or wide.loc[pre_years, placebo_unit].isna().any():
            continue
        valid = [d for d in donors if wide.loc[pre_years, d].notna().all()]
        if len(valid) < 2:
            continue
        treat_pre = wide.loc[pre_years, placebo_unit].values
        donor_pre = wide.loc[pre_years, valid].values

        def loss(w):
            return float(np.sum((treat_pre - donor_pre @ w) ** 2))

        n = len(valid)
        sol = minimize(loss, np.ones(n) / n, method="SLSQP",
                       bounds=[(0, 1)] * n,
                       constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}])
        w = sol.x
        post_synth = []
        post_treat = []
        for y in post_years:
            if y not in wide.index:
                continue
            row = wide.loc[y, valid]
            if row.notna().all() and pd.notna(wide.loc[y, placebo_unit]):
                post_synth.append(float(row.values @ w))
                post_treat.append(float(wide.loc[y, placebo_unit]))
        if len(post_treat) == 0:
            continue
        avg_gap = float(np.mean(np.array(post_treat) - np.array(post_synth)))
        gaps.append({"unit": placebo_unit, "post_avg_gap_log": avg_gap})

    # Rank BWA's gap (largest positive)
    if not gaps:
        return {"error": "placebo failed"}
    sorted_gaps = sorted(gaps, key=lambda r: -r["post_avg_gap_log"])
    bwa_rank = next((i for i, r in enumerate(sorted_gaps) if r["unit"] == TREATED), None)
    return {
        "ranks": sorted_gaps,
        "bwa_rank_among_n": (bwa_rank, len(sorted_gaps)) if bwa_rank is not None else None,
        "permutation_p_one_sided": (
            (bwa_rank + 1) / len(sorted_gaps) if bwa_rank is not None else None
        ),
    }


def growth_gap(panel: pd.DataFrame) -> dict:
    """Annual log-growth: BWA mean vs donor pool mean, 1976-2023."""
    sub = panel[panel["country"].isin([TREATED] + DONORS)].copy()
    sub = sub.sort_values(["country", "year"])
    sub["log_growth"] = sub.groupby("country")["log_gdp_pc"].diff()
    growth_post = sub[(sub["year"] >= TREAT_YEAR + 1) & (sub["year"] <= PERIOD[1])]
    bwa_growth = growth_post[growth_post["country"] == TREATED]["log_growth"].dropna()
    donor_growth = growth_post[growth_post["country"].isin(DONORS)]["log_growth"].dropna()
    bwa_mean = float(bwa_growth.mean()) if len(bwa_growth) else None
    donor_mean = float(donor_growth.mean()) if len(donor_growth) else None
    return {
        "bwa_mean_log_growth": bwa_mean,
        "donor_mean_log_growth": donor_mean,
        "gap_pp": (bwa_mean - donor_mean) * 100 if (bwa_mean is not None and donor_mean is not None) else None,
        "n_bwa_obs": int(len(bwa_growth)),
        "n_donor_obs": int(len(donor_growth)),
    }


def covariate_gaps(vdem: pd.DataFrame | None, wgi: pd.DataFrame | None):
    out = {}
    if vdem is not None:
        sub = vdem[vdem["country"].isin([TREATED] + DONORS)]
        sub_post = sub[(sub["year"] >= TREAT_YEAR) & (sub["year"] <= PERIOD[1])]
        bwa = sub_post[sub_post["country"] == TREATED]["v2x_polyarchy"]
        donor = sub_post[sub_post["country"].isin(DONORS)]["v2x_polyarchy"]
        out["vdem_polyarchy"] = {
            "bwa_mean": float(bwa.mean()) if len(bwa) else None,
            "donor_mean": float(donor.mean()) if len(donor) else None,
            "gap": (float(bwa.mean()) - float(donor.mean())) if (len(bwa) and len(donor)) else None,
            "n_bwa": int(len(bwa)),
            "n_donor": int(len(donor)),
        }
    else:
        out["vdem_polyarchy"] = {"error": "v2x_polyarchy not loadable"}
    if wgi is not None:
        sub = wgi[wgi["country"].isin([TREATED] + DONORS)]
        sub_post = sub[(sub["year"] >= 1996) & (sub["year"] <= PERIOD[1])]
        bwa = sub_post[sub_post["country"] == TREATED]["wgi_ge"]
        donor = sub_post[sub_post["country"].isin(DONORS)]["wgi_ge"]
        out["wgi_government_effectiveness_1996plus"] = {
            "bwa_mean": float(bwa.mean()) if len(bwa) else None,
            "donor_mean": float(donor.mean()) if len(donor) else None,
            "gap": (float(bwa.mean()) - float(donor.mean())) if (len(bwa) and len(donor)) else None,
            "n_bwa": int(len(bwa)),
            "n_donor": int(len(donor)),
        }
    else:
        out["wgi_government_effectiveness_1996plus"] = {"error": "WGI GE not loadable"}
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Load primary outcome ----------
    md, mpath = load_maddison()
    manifest = {
        "real_gdp_per_capita": {
            "publisher": "maddison",
            "series": "mpd2020",
            "vintage_file": str(mpath.relative_to(REPO_ROOT)),
            "sha256": sha256(mpath),
        }
    }

    panel = md[md["country"].isin([TREATED] + DONORS)].copy()
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.drop_duplicates(subset=["country", "year"]).reset_index(drop=True)
    panel["log_gdp_pc"] = np.log(panel["gdppc"])

    sc = synthetic_control(panel)
    gg = growth_gap(panel)

    # Placebo permutation only if SC succeeded
    placebo = {}
    if "error" not in sc:
        placebo = placebo_permutation(panel, sc.get("donors", []))

    # ---------- Load informative covariates ----------
    try:
        vdem, vpath = load_vdem_polyarchy()
        if vdem is not None:
            manifest["vdem_polyarchy"] = {
                "publisher": "vdem", "series": "vdem_cy_full",
                "vintage_file": str(vpath.relative_to(REPO_ROOT)),
                "sha256": sha256(vpath),
            }
    except Exception as e:
        vdem = None
        manifest["vdem_polyarchy"] = {"error": str(e)}
    try:
        wgi, wpath = load_wgi_ge()
        if wgi is not None:
            manifest["wgi_government_effectiveness"] = {
                "publisher": "wgi", "series": "GOV_WGI_GE.EST",
                "vintage_file": str(wpath.relative_to(REPO_ROOT)),
                "sha256": sha256(wpath),
            }
    except Exception as e:
        wgi = None
        manifest["wgi_government_effectiveness"] = {"error": str(e)}

    cov_gaps = covariate_gaps(vdem, wgi)

    # ---------- Falsification verdict ----------
    primary1 = ("error" not in sc) and (sc.get("post_avg_gap_log") is not None) and (
        sc["post_avg_gap_log"] >= GAP_LOG_THRESHOLD
    )
    primary2 = (gg["gap_pp"] is not None) and (gg["gap_pp"] >= GROWTH_GAP_THRESHOLD_PP)

    if "error" in sc:
        verdict = (
            f"inconclusive — synthetic control failed ({sc['error']}). "
            f"Growth gap (BWA−donor mean): {gg.get('gap_pp')}pp/yr."
        )
        all_pass = False
    elif primary1 and primary2:
        verdict = (
            f"SUPPORTED — Botswana's synthetic-control mean post-1976 log-gap = "
            f"{sc['post_avg_gap_log']:+.3f} (~{sc['post_avg_gap_pct']:+.0f}% level), "
            f"clearing the +0.30 log threshold. Annual log-growth advantage "
            f"{gg['gap_pp']:+.2f}pp/yr (≥ +2pp threshold). "
            f"Pre-fit RMSE (log) = {sc['pre_fit_rmse_log']:.3f}. "
            f"V-Dem polyarchy gap (post-1976) = "
            f"{cov_gaps['vdem_polyarchy'].get('gap')}; "
            f"WGI gov-effectiveness gap (1996+) = "
            f"{cov_gaps['wgi_government_effectiveness_1996plus'].get('gap')}."
        )
        all_pass = True
    elif (not primary1) and (not primary2):
        # Both directions wrong or magnitudes < half threshold → refuted
        gap_bad = (sc.get("post_avg_gap_log", 0) is not None and
                   sc.get("post_avg_gap_log", 0) < GAP_LOG_THRESHOLD / 2)
        growth_bad = (gg["gap_pp"] is not None and gg["gap_pp"] < GROWTH_GAP_THRESHOLD_PP / 2)
        if gap_bad and growth_bad:
            verdict = (
                f"refuted — Botswana SC mean post-1976 log-gap = "
                f"{sc.get('post_avg_gap_log', float('nan')):+.3f} (below 0.30 threshold "
                f"and below half of it). Annual growth gap "
                f"{gg['gap_pp']:+.2f}pp/yr (below +2pp and below half). The "
                f"institutional-exceptionalism magnitude claim does not hold against the "
                f"SSA resource-exporter donor pool."
            )
        else:
            verdict = (
                f"partial — Both primaries missed but at least one was within half "
                f"of threshold. SC log-gap {sc.get('post_avg_gap_log', float('nan')):+.3f} "
                f"vs +0.30; growth gap {gg['gap_pp']:+.2f}pp/yr vs +2.0pp."
            )
        all_pass = False
    else:
        which_passed = "SC log-gap" if primary1 else "growth gap"
        which_failed = "growth gap" if primary1 else "SC log-gap"
        verdict = (
            f"partial — {which_passed} primary clears threshold but {which_failed} "
            f"does not. SC log-gap {sc.get('post_avg_gap_log', float('nan')):+.3f} "
            f"(threshold +0.30); growth gap {gg.get('gap_pp')}pp/yr (threshold +2.0)."
        )
        all_pass = False

    # ---------- Diagnostics ----------
    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "primary1_sc_log_gap_geq_threshold": primary1,
        "primary2_growth_gap_geq_2pp": primary2,
        "thresholds": {
            "sc_log_gap_threshold": GAP_LOG_THRESHOLD,
            "growth_gap_pp_threshold": GROWTH_GAP_THRESHOLD_PP,
        },
        "synthetic_control": {k: v for k, v in sc.items()
                              if k not in ("synth_by_year", "treat_by_year", "post_gap_by_year")},
        "growth_gap": gg,
        "placebo_permutation": placebo,
        "covariate_gaps_informative": cov_gaps,
        "data_gaps": {
            "wdi_mineral_rents_NY.GDP.MINR.RT.ZS": (
                "vintage not on disk; diamond-rent attribution channel reported as "
                "data gap rather than estimated."
            ),
            "polity5_durable": (
                "polity5 vintage on disk but durable column not exercised in this v1; "
                "v2 could add as institutional-persistence robustness check."
            ),
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ---------- Chart ----------
    palette = ["#E15759", "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2",
               "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d"]
    series = []
    # Treated: BWA actual log GDP-pc
    bwa_sub = panel[panel["country"] == TREATED].sort_values("year")
    series.append({
        "id": "BWA",
        "label": "Botswana (actual)",
        "color": "#E15759",
        "treated": True,
        "points": [{"x": int(r.year), "y": float(r.log_gdp_pc)} for r in bwa_sub.itertuples()],
    })
    # Synthetic
    if "synth_by_year" in sc:
        synth_pts = [{"x": int(y), "y": float(v)} for y, v in sorted(sc["synth_by_year"].items())]
        series.append({
            "id": "BWA_SYNTH",
            "label": "Synthetic Botswana (SSA donors)",
            "color": "#1f1f1f",
            "treated": False,
            "points": synth_pts,
        })
    # Donors (light)
    for i, c in enumerate(DONORS):
        sub = panel[panel["country"] == c].sort_values("year")
        if sub.empty:
            continue
        series.append({
            "id": c,
            "label": c,
            "color": palette[(i + 2) % len(palette)],
            "treated": False,
            "points": [{"x": int(r.year), "y": float(r.log_gdp_pc)} for r in sub.itertuples()],
        })

    sc_gap_log = sc.get("post_avg_gap_log")
    sc_gap_pct = sc.get("post_avg_gap_pct")
    chart = {
        "kind": "result",
        "chart_id": f"{RUN_ID}/fig1",
        "title": f"Log GDP per capita — Botswana vs SSA resource-exporter donors, {PERIOD[0]}-{PERIOD[1]}",
        "subtitle": (
            f"Post-1976 SC mean log-gap = "
            f"{sc_gap_log:+.3f} ({sc_gap_pct:+.0f}%). " if sc_gap_log is not None else ""
        ) + (
            f"BWA−donor mean log-growth gap = {gg['gap_pp']:+.2f}pp/yr."
            if gg.get("gap_pp") is not None else ""
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log real GDP per capita (Maddison 2020 intl $)", "type": "linear"},
        "series": series,
        "annotations": [{
            "type": "note",
            "label": (
                f"Pre-fit window {PRE_FIT[0]}-{PRE_FIT[1]}; treatment year "
                f"{TREAT_YEAR}. Donor weights non-zero on: "
                + ", ".join(f"{k}={v:.2f}" for k, v in
                            sorted(sc.get("weights", {}).items(), key=lambda kv: -kv[1])
                            if v > 0.01)
            ),
        }],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v.get("vintage_file", "")}
            for k, v in manifest.items() if isinstance(v, dict) and "publisher" in v
        ],
        "permalink": f"/h/{RUN_ID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    # ---------- Coefficients table ----------
    coef_rows = []
    if "post_avg_gap_log" in sc and sc["post_avg_gap_log"] is not None:
        coef_rows.append({
            "spec": "synthetic_control",
            "term": "post_avg_gap_log",
            "estimate": sc["post_avg_gap_log"],
            "threshold": GAP_LOG_THRESHOLD,
            "passes": primary1,
        })
    if sc.get("pre_fit_rmse_log") is not None:
        coef_rows.append({
            "spec": "synthetic_control",
            "term": "pre_fit_rmse_log",
            "estimate": sc["pre_fit_rmse_log"],
            "threshold": None,
            "passes": None,
        })
    if gg["gap_pp"] is not None:
        coef_rows.append({
            "spec": "growth_gap",
            "term": "bwa_minus_donor_mean_pp",
            "estimate": gg["gap_pp"],
            "threshold": GROWTH_GAP_THRESHOLD_PP,
            "passes": primary2,
        })
    if placebo.get("permutation_p_one_sided") is not None:
        coef_rows.append({
            "spec": "placebo_permutation",
            "term": "permutation_p_one_sided",
            "estimate": placebo["permutation_p_one_sided"],
            "threshold": None,
            "passes": None,
        })
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Manifest ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator_template": "synthetic_control (Abadie-Diamond-Hainmueller 2010)",
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- Result card ----------
    weights_str = ", ".join(
        f"{k}={v:.2f}" for k, v in sorted(sc.get("weights", {}).items(), key=lambda kv: -kv[1])
        if v > 0.005
    )
    lines = [
        f"# Result card — Botswana institutional exceptionalism, 1966-2023",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Pre-registration",
        "",
        "- **Claim:** Botswana's divergence from SSA averages post-1966 is attributable",
        "  primarily to retained pre-colonial Tswana institutions plus post-independence",
        "  resource-rent management.",
        "- **Falsification (PRIMARY 1):** SC mean post-1976 log-gap ≥ +0.30 (~+35% level).",
        "- **Falsification (PRIMARY 2):** BWA − donor mean annual log-growth ≥ +2.0pp/yr.",
        "- **Informative (METHOD_VALID-style):** V-Dem polyarchy and WGI government",
        "  effectiveness gaps; pre-fit RMSE; placebo permutation rank.",
        "",
        "## Synthetic control",
        "",
        f"- Donor pool (post-fit-coverage filter): {sc.get('donors', [])}",
        f"- Pre-fit window: {PRE_FIT[0]}-{PRE_FIT[1]}; treatment year: {TREAT_YEAR}",
        f"- Pre-fit RMSE (log): {sc.get('pre_fit_rmse_log')}",
        f"- Donor weights (>0.5%): {weights_str}",
        f"- Post-treatment mean log-gap: {sc.get('post_avg_gap_log')}",
        f"- Post-treatment mean level gap: "
        f"{sc.get('post_avg_gap_pct')}%",
        f"- 2023 terminal log-gap: {sc.get('post_2023_gap_log')}",
        "",
        "## Growth gap",
        "",
        f"- BWA mean annual log-growth 1977-2023: {gg.get('bwa_mean_log_growth')}",
        f"- Donor pool mean annual log-growth 1977-2023: {gg.get('donor_mean_log_growth')}",
        f"- **Gap (BWA − donor mean):** {gg.get('gap_pp')} pp/yr  (threshold ≥ +2.0)",
        "",
        "## Placebo permutation",
        "",
        f"- BWA rank among donor pool (largest positive post-treat gap): "
        f"{placebo.get('bwa_rank_among_n')}",
        f"- One-sided permutation p-value: {placebo.get('permutation_p_one_sided')}",
        "",
        "## Informative covariate gaps (post-treatment)",
        "",
        f"- V-Dem polyarchy: BWA={cov_gaps.get('vdem_polyarchy', {}).get('bwa_mean')}, "
        f"donor mean={cov_gaps.get('vdem_polyarchy', {}).get('donor_mean')}, "
        f"gap={cov_gaps.get('vdem_polyarchy', {}).get('gap')}",
        f"- WGI gov-effectiveness (1996+): "
        f"BWA={cov_gaps.get('wgi_government_effectiveness_1996plus', {}).get('bwa_mean')}, "
        f"donor mean={cov_gaps.get('wgi_government_effectiveness_1996plus', {}).get('donor_mean')}, "
        f"gap={cov_gaps.get('wgi_government_effectiveness_1996plus', {}).get('gap')}",
        "",
        "## Method note (downgrade from spec)",
        "",
        "Spec called for `synthetic_control` with diamond-rent and V-Dem covariates",
        "as decomposition channels. Implemented classic Abadie-Diamond-Hainmueller",
        "synthetic control on log GDP-pc level matched in the pre-1976 window.",
        "Diamond-rent channel (WDI mineral rents, NY.GDP.MINR.RT.ZS) is NOT on disk;",
        "reported as a data gap rather than estimated. Channel decomposition is",
        "left as a v2 question — for now V-Dem and WGI gaps are reported descriptively",
        "to colour but not gate the verdict.",
        "",
        "## Data",
        "",
        f"- maddison:mpd2020 (primary outcome, log real GDP per capita)",
        f"- vdem:vdem_cy_full (v2x_polyarchy — informative)",
        f"- wgi:GOV_WGI_GE.EST (informative, 1996+)",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  SC post-avg log-gap: {sc.get('post_avg_gap_log')}")
    print(f"  Growth gap: {gg.get('gap_pp')} pp/yr")
    print(f"  Placebo p (one-sided): {placebo.get('permutation_p_one_sided')}")


if __name__ == "__main__":
    sys.exit(main())
