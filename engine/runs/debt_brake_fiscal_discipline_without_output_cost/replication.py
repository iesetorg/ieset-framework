#!/usr/bin/env python3
"""Replication — German Schuldenbremse: debt discipline without output cost (2009-2019).

Spec: hypotheses/growth/debt_brake_fiscal_discipline_without_output_cost.yaml v1
Position-claim: ordoliberal #1 (school predicts: supported)

The original spec called for synthetic-DID with Germany treated 2009 and a donor
pool of fiscal-rule-absent advanced economies. The synth_did library is not in
the project venv and the implementation is non-trivial, so per HANDOFF allowance
this is downgraded to a transparent before/after panel comparison documented in
the methodology_note:

  - PRE = 2008 (year before the constitutional amendment) baseline
  - POST = 2019 (cleanest pre-COVID, pre-debt-brake-suspension end-point)
  - Treated unit: DEU
  - Donor pool: {FRA, ITA, ESP, NLD, BEL, AUT, FIN, IRL, PRT, GBR}

PRIMARY 1 (DEBT DISCIPLINE - dispositive)
  Germany's Δdebt-to-GDP 2008→2019 must be at least 10pp LOWER than the
  unweighted donor-pool mean Δdebt-to-GDP 2008→2019. The Schuldenbremse
  story requires a visibly differentiated debt trajectory.

PRIMARY 2 (NO OUTPUT COST - dispositive)
  Germany's cumulative log-real-GDP-per-capita growth 2008→2019 must be at
  least 90% of the donor-pool unweighted mean cumulative log growth (i.e.
  Germany no more than 10% behind the donor mean over the 11-year window).

VERDICT LOGIC
  - SUPPORTED:    BOTH primaries hold.
  - REFUTED:      PRIMARY 1 fails (no debt advantage at all - the
                  Schuldenbremse failed at its stated job).
  - partial:      PRIMARY 1 holds, PRIMARY 2 fails (debt discipline came
                  with non-trivial output cost - the Ordoliberal claim of
                  "without output loss" is rejected but the fiscal claim
                  survives).
  - inconclusive: data gap on debt or GDP series for >3 of 11 sample
                  countries.

INFORMATIVE
  - General-government net lending/GDP (GGXCNL_NGDP) trajectory.
  - Country-level dispersion of the donor pool.
  - Pre-period (2000-2008) parallel-trend check on log-GDP-pc.

CAVEATS
  - The donor pool is a fixed Eurozone+UK convenience sample, not selected
    to match Germany's pre-trend. A real synth-DID would weight donors to
    match the pre-period; this comparison instead reports the donor-pool
    mean and the pre-period gap as a parallel-trend diagnostic.
  - Attribution to Schuldenbremse alone is contested: ECB policy, intra-
    Eurozone competitiveness, and German export demand from peripheral
    austerity are confounds. This run only tests the descriptive
    regularity, not the causal claim.
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
HID = "debt_brake_fiscal_discipline_without_output_cost"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
TREATED = "DEU"
DONOR_POOL = ["FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "FIN", "IRL", "PRT", "GBR"]
ALL_COUNTRIES = [TREATED] + DONOR_POOL

# Treatment timing
PRE_YEAR = 2008      # last full year before the 2009 constitutional amendment
POST_YEAR = 2019     # last clean pre-COVID year (debt brake also suspended 2020-2022)
PRE_TREND_START = 2000  # for parallel-trend diagnostic

# Falsification thresholds (made dispositive from spec stub)
DEBT_GAP_THRESHOLD_PP = 10.0     # Germany must have ≥10pp lower Δdebt than donor mean
OUTPUT_RATIO_THRESHOLD = 0.90    # Germany cum log-GDP-pc growth ≥ 90% of donor mean
MAX_MISSING_DONORS = 3            # method-valid only if ≤3 of 10 donors missing data


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


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
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


def country_value(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    debt_path = latest("imf", "GGXWDG_NGDP")
    fb_path = latest("imf", "GGXCNL_NGDP")
    gdp_pc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")

    manifest = {
        "gov_debt_pct_gdp": {
            "publisher": "imf",
            "series": "GGXWDG_NGDP",
            "vintage_file": str(debt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(debt_path),
        },
        "gen_govt_balance_pct_gdp": {
            "publisher": "imf",
            "series": "GGXCNL_NGDP",
            "vintage_file": str(fb_path.relative_to(REPO_ROOT)),
            "sha256": sha256(fb_path),
        },
        "real_gdp_per_capita": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_pc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_pc_path),
        },
    }

    debt = load_long(debt_path)
    fb = load_long(fb_path)
    gdp_pc = load_long(gdp_pc_path)

    # ---------- Build per-country panel of the four key statistics ----------
    rows = []
    for c in ALL_COUNTRIES:
        debt_pre = country_value(debt, c, PRE_YEAR)
        debt_post = country_value(debt, c, POST_YEAR)
        gdp_pre = country_value(gdp_pc, c, PRE_YEAR)
        gdp_post = country_value(gdp_pc, c, POST_YEAR)
        gdp_trend_start = country_value(gdp_pc, c, PRE_TREND_START)
        fb_pre = country_value(fb, c, PRE_YEAR)
        fb_post = country_value(fb, c, POST_YEAR)

        delta_debt = (debt_post - debt_pre) if (debt_pre is not None and debt_post is not None) else None
        log_growth = (
            float(np.log(gdp_post) - np.log(gdp_pre))
            if (gdp_pre is not None and gdp_post is not None and gdp_pre > 0 and gdp_post > 0)
            else None
        )
        pre_trend_log_growth = (
            float(np.log(gdp_pre) - np.log(gdp_trend_start))
            if (gdp_pre is not None and gdp_trend_start is not None and gdp_pre > 0 and gdp_trend_start > 0)
            else None
        )
        delta_fb = (fb_post - fb_pre) if (fb_pre is not None and fb_post is not None) else None

        rows.append({
            "country": c,
            "treated": int(c == TREATED),
            "debt_pre": debt_pre,
            "debt_post": debt_post,
            "delta_debt_pp": delta_debt,
            "gdp_pre": gdp_pre,
            "gdp_post": gdp_post,
            "log_growth_2008_2019": log_growth,
            "pre_trend_log_growth_2000_2008": pre_trend_log_growth,
            "fb_pre": fb_pre,
            "fb_post": fb_post,
            "delta_fb_pp": delta_fb,
        })

    panel = pd.DataFrame(rows)

    # Treated row
    deu = panel[panel["country"] == TREATED].iloc[0].to_dict()

    # Donor pool with full debt + GDP coverage
    donors = panel[panel["country"] != TREATED].copy()
    donors_valid = donors.dropna(subset=["delta_debt_pp", "log_growth_2008_2019"]).copy()

    n_donors_valid = int(len(donors_valid))
    n_donors_total = int(len(donors))
    n_missing = n_donors_total - n_donors_valid

    method_valid = (
        n_missing <= MAX_MISSING_DONORS
        and deu["delta_debt_pp"] is not None
        and deu["log_growth_2008_2019"] is not None
    )

    # ---------- PRIMARY 1: debt path differential ----------
    donor_mean_delta_debt = float(donors_valid["delta_debt_pp"].mean()) if n_donors_valid > 0 else float("nan")
    deu_delta_debt = float(deu["delta_debt_pp"]) if deu["delta_debt_pp"] is not None else float("nan")
    debt_gap_pp = deu_delta_debt - donor_mean_delta_debt   # negative ⇒ Germany did better

    primary1_debt_disciplined = bool(
        not np.isnan(debt_gap_pp) and (debt_gap_pp <= -DEBT_GAP_THRESHOLD_PP)
    )

    # ---------- PRIMARY 2: output ratio ----------
    donor_mean_log_growth = float(donors_valid["log_growth_2008_2019"].mean()) if n_donors_valid > 0 else float("nan")
    deu_log_growth = float(deu["log_growth_2008_2019"]) if deu["log_growth_2008_2019"] is not None else float("nan")

    # The "ratio" of Germany's growth to donor mean. Handle sign carefully:
    # if donor mean is small or negative the ratio loses meaning, so we also
    # report a more robust gap-in-pp test as a tie-breaker.
    if (not np.isnan(donor_mean_log_growth)) and donor_mean_log_growth > 0:
        output_ratio = deu_log_growth / donor_mean_log_growth
    else:
        output_ratio = float("nan")

    output_gap_pp = (deu_log_growth - donor_mean_log_growth) * 100.0  # in pp of cumulative log-growth

    # PRIMARY 2 holds if Germany ≥ 90% of donor mean OR (donor mean ≤ 0 and
    # Germany at least matched donor mean within 5pp - i.e. didn't fall behind).
    if not np.isnan(output_ratio):
        primary2_no_output_cost = bool(output_ratio >= OUTPUT_RATIO_THRESHOLD)
    else:
        # Fallback when donor mean is non-positive: Germany within 5pp of donor mean
        primary2_no_output_cost = bool(output_gap_pp >= -5.0)

    # ---------- Pre-trend diagnostic ----------
    donor_mean_pre_trend = (
        float(donors_valid["pre_trend_log_growth_2000_2008"].dropna().mean())
        if n_donors_valid > 0 else float("nan")
    )
    deu_pre_trend = (
        float(deu["pre_trend_log_growth_2000_2008"])
        if deu["pre_trend_log_growth_2000_2008"] is not None else float("nan")
    )
    pre_trend_gap_pp = (
        (deu_pre_trend - donor_mean_pre_trend) * 100.0
        if not (np.isnan(deu_pre_trend) or np.isnan(donor_mean_pre_trend)) else float("nan")
    )

    # Pre-trend "clean" if Germany was within 5pp of donor cum-growth in 2000-2008
    pre_trend_clean = (not np.isnan(pre_trend_gap_pp)) and abs(pre_trend_gap_pp) <= 5.0

    # ---------- Fiscal-balance informative ----------
    donor_mean_delta_fb = (
        float(donors_valid["delta_fb_pp"].dropna().mean())
        if n_donors_valid > 0 else float("nan")
    )
    deu_delta_fb = float(deu["delta_fb_pp"]) if deu["delta_fb_pp"] is not None else float("nan")

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive (data gap on imf:GGXWDG_NGDP / wdi:NY.GDP.PCAP.KD) — "
            f"Only {n_donors_valid} of {n_donors_total} donor countries have "
            f"complete debt+GDP coverage at {PRE_YEAR} and {POST_YEAR}; spec "
            f"requires at most {MAX_MISSING_DONORS} missing."
        )
    else:
        if primary1_debt_disciplined and primary2_no_output_cost:
            verdict = (
                f"SUPPORTED — Germany's debt-to-GDP rose by "
                f"{deu_delta_debt:+.1f}pp 2008-2019 vs donor-pool mean "
                f"{donor_mean_delta_debt:+.1f}pp ({debt_gap_pp:+.1f}pp differential, "
                f"≥{DEBT_GAP_THRESHOLD_PP:.0f}pp threshold met). Cumulative log-"
                f"GDP-pc growth: Germany {deu_log_growth*100:+.1f}%, donor mean "
                f"{donor_mean_log_growth*100:+.1f}% (Germany {output_ratio*100:.0f}% "
                f"of donor mean, ≥{OUTPUT_RATIO_THRESHOLD*100:.0f}% threshold met). "
                f"N={n_donors_valid} donor countries."
            )
        elif primary1_debt_disciplined and not primary2_no_output_cost:
            verdict = (
                f"partial — Debt discipline holds: Germany Δdebt "
                f"{deu_delta_debt:+.1f}pp vs donor mean {donor_mean_delta_debt:+.1f}pp "
                f"({debt_gap_pp:+.1f}pp differential, threshold met). But output "
                f"cost is non-trivial: Germany cum growth {deu_log_growth*100:+.1f}% "
                f"vs donor {donor_mean_log_growth*100:+.1f}% (Germany "
                f"{output_ratio*100:.0f}% of donor mean, below "
                f"{OUTPUT_RATIO_THRESHOLD*100:.0f}% threshold). The 'without output "
                f"loss' half of the Ordoliberal claim is rejected."
            )
        elif (not primary1_debt_disciplined) and primary2_no_output_cost:
            verdict = (
                f"refuted — Schuldenbremse failed at its stated job: Germany's "
                f"Δdebt 2008-2019 was {deu_delta_debt:+.1f}pp vs donor-pool mean "
                f"{donor_mean_delta_debt:+.1f}pp ({debt_gap_pp:+.1f}pp differential, "
                f"need ≤-{DEBT_GAP_THRESHOLD_PP:.0f}pp). Output kept up "
                f"(Germany {output_ratio*100:.0f}% of donor mean) but the debt-"
                f"discipline premise of the claim does not hold. N={n_donors_valid}."
            )
        else:
            verdict = (
                f"refuted — Both primaries fail. Δdebt differential "
                f"{debt_gap_pp:+.1f}pp (need ≤-{DEBT_GAP_THRESHOLD_PP:.0f}pp); "
                f"Germany cum growth {deu_log_growth*100:+.1f}% is "
                f"{output_ratio*100:.0f}% of donor mean (need "
                f"≥{OUTPUT_RATIO_THRESHOLD*100:.0f}%). Neither the debt-discipline "
                f"nor the no-output-cost premise survives. N={n_donors_valid}."
            )

    if method_valid and not pre_trend_clean and not verdict.startswith(("inconclusive", "refuted")):
        # Pre-trend gap large; flag in verdict text without overriding direction.
        verdict = verdict + (
            f" Pre-trend caveat: Germany's 2000-2008 cum growth differed from "
            f"donor mean by {pre_trend_gap_pp:+.1f}pp (>5pp), so the simple "
            f"before/after comparison is sensitive to selection of pre-period."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": bool(primary1_debt_disciplined and primary2_no_output_cost),
        "method_valid": bool(method_valid),
        "pre_trend_clean": bool(pre_trend_clean),
        "n_donors_total": n_donors_total,
        "n_donors_valid": n_donors_valid,
        "n_donors_missing": n_missing,
        # Primary 1
        "primary1_debt_disciplined": bool(primary1_debt_disciplined),
        "deu_delta_debt_pp": deu_delta_debt,
        "donor_mean_delta_debt_pp": donor_mean_delta_debt,
        "debt_gap_pp": debt_gap_pp,
        "debt_gap_threshold_pp": DEBT_GAP_THRESHOLD_PP,
        # Primary 2
        "primary2_no_output_cost": bool(primary2_no_output_cost),
        "deu_log_growth_2008_2019": deu_log_growth,
        "donor_mean_log_growth_2008_2019": donor_mean_log_growth,
        "output_ratio_deu_over_donor": output_ratio,
        "output_gap_pp": output_gap_pp,
        "output_ratio_threshold": OUTPUT_RATIO_THRESHOLD,
        # Pre-trend
        "deu_pre_trend_log_growth_2000_2008": deu_pre_trend,
        "donor_mean_pre_trend_log_growth_2000_2008": donor_mean_pre_trend,
        "pre_trend_gap_pp": pre_trend_gap_pp,
        # Informative: fiscal balance
        "deu_delta_fiscal_balance_pp": deu_delta_fb,
        "donor_mean_delta_fiscal_balance_pp": donor_mean_delta_fb,
        # Per-country
        "country_records": [
            {k: (v if not isinstance(v, float) or not pd.isna(v) else None)
             for k, v in r.items()}
            for r in panel.to_dict("records")
        ],
        "downgrade_note": (
            "Spec called for synthetic-DID; downgraded to before/after panel "
            "comparison (Germany vs unweighted donor-pool mean, PRE=2008, "
            "POST=2019). synth_did not in venv; donor-weight optimisation is "
            "non-trivial. Pre-trend diagnostic 2000-2008 included as a "
            "method-validity check."
        ),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: debt-to-GDP trajectory, Germany vs donor mean ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d",
    ]

    chart_years = list(range(PRE_TREND_START, POST_YEAR + 1))
    series = []

    # Treated: Germany (debt-to-GDP)
    deu_debt_pts = []
    for y in chart_years:
        v = country_value(debt, TREATED, y)
        if v is not None:
            deu_debt_pts.append({"x": y, "y": v})
    series.append({
        "id": TREATED,
        "label": "Germany (treated)",
        "color": "#1f1f1f",
        "treated": True,
        "points": deu_debt_pts,
    })

    # Donor-pool mean trajectory
    donor_mean_pts = []
    for y in chart_years:
        vals = [country_value(debt, c, y) for c in DONOR_POOL]
        vals = [v for v in vals if v is not None]
        if vals:
            donor_mean_pts.append({"x": y, "y": float(np.mean(vals))})
    series.append({
        "id": "DONOR_MEAN",
        "label": f"Donor-pool mean (n={len(DONOR_POOL)})",
        "color": "#E15759",
        "treated": False,
        "points": donor_mean_pts,
    })

    # Individual donors as light context lines
    for i, c in enumerate(DONOR_POOL):
        pts = []
        for y in chart_years:
            v = country_value(debt, c, y)
            if v is not None:
                pts.append({"x": y, "y": v})
        if pts:
            series.append({
                "id": c,
                "label": c,
                "color": palette[i % len(palette)],
                "treated": False,
                "points": pts,
            })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Gross general-government debt as % of GDP, Germany vs donor pool",
        "subtitle": (
            f"PRE=2008, POST=2019. Δdebt: Germany {deu_delta_debt:+.1f}pp, "
            f"donor mean {donor_mean_delta_debt:+.1f}pp ({debt_gap_pp:+.1f}pp gap). "
            f"Cum log-GDP-pc growth: Germany {deu_log_growth*100:+.1f}%, donor "
            f"mean {donor_mean_log_growth*100:+.1f}% ({output_ratio*100:.0f}% ratio)."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Gross general-government debt / GDP (%)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vline",
                "x": 2009,
                "label": "Schuldenbremse adopted (June 2009)",
            },
            {
                "type": "note",
                "label": (
                    f"Threshold: Germany Δdebt at least {DEBT_GAP_THRESHOLD_PP:.0f}pp "
                    f"below donor-pool mean. Observed gap: {debt_gap_pp:+.1f}pp "
                    f"({'PASS' if primary1_debt_disciplined else 'FAIL'}). "
                    f"Output threshold: Germany ≥{OUTPUT_RATIO_THRESHOLD*100:.0f}% of "
                    f"donor mean cum growth. Observed: {output_ratio*100:.0f}% "
                    f"({'PASS' if primary2_no_output_cost else 'FAIL'})."
                ),
            },
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients parquet ----------
    coef_rows = [
        {"spec": "primary1_debt", "term": "deu_delta_debt_pp", "estimate": deu_delta_debt},
        {"spec": "primary1_debt", "term": "donor_mean_delta_debt_pp", "estimate": donor_mean_delta_debt},
        {"spec": "primary1_debt", "term": "debt_gap_pp", "estimate": debt_gap_pp},
        {"spec": "primary1_debt", "term": "debt_gap_threshold_pp", "estimate": DEBT_GAP_THRESHOLD_PP},
        {"spec": "primary2_output", "term": "deu_log_growth", "estimate": deu_log_growth},
        {"spec": "primary2_output", "term": "donor_mean_log_growth", "estimate": donor_mean_log_growth},
        {"spec": "primary2_output", "term": "output_ratio", "estimate": output_ratio},
        {"spec": "primary2_output", "term": "output_ratio_threshold", "estimate": OUTPUT_RATIO_THRESHOLD},
        {"spec": "pre_trend", "term": "deu_pre_trend_log_growth", "estimate": deu_pre_trend},
        {"spec": "pre_trend", "term": "donor_mean_pre_trend_log_growth", "estimate": donor_mean_pre_trend},
        {"spec": "pre_trend", "term": "pre_trend_gap_pp", "estimate": pre_trend_gap_pp},
        {"spec": "informative_fb", "term": "deu_delta_fb_pp", "estimate": deu_delta_fb},
        {"spec": "informative_fb", "term": "donor_mean_delta_fb_pp", "estimate": donor_mean_delta_fb},
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
        f"# Schuldenbremse: debt discipline without output cost (2009-2019)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- N = {n_donors_valid} of {n_donors_total} donor countries with complete coverage.",
        f"- Δdebt-to-GDP 2008-2019: **Germany {deu_delta_debt:+.1f}pp**, "
        f"**donor-pool mean {donor_mean_delta_debt:+.1f}pp** "
        f"(differential **{debt_gap_pp:+.1f}pp**; threshold ≤ -{DEBT_GAP_THRESHOLD_PP:.0f}pp).",
        f"- Cumulative log-GDP-per-capita growth 2008-2019: "
        f"**Germany {deu_log_growth*100:+.1f}%**, **donor mean {donor_mean_log_growth*100:+.1f}%** "
        f"(ratio **{output_ratio*100:.0f}%**; threshold ≥ {OUTPUT_RATIO_THRESHOLD*100:.0f}%).",
        f"- Pre-trend (2000-2008): Germany {deu_pre_trend*100:+.1f}% vs donor "
        f"{donor_mean_pre_trend*100:+.1f}% ({pre_trend_gap_pp:+.1f}pp gap; "
        f"{'within' if pre_trend_clean else 'outside'} 5pp diagnostic band).",
        f"- Δfiscal balance (informative): Germany {deu_delta_fb:+.1f}pp, "
        f"donor mean {donor_mean_delta_fb:+.1f}pp.",
        "",
        "## Method",
        "",
        "Before/after panel comparison: Germany (treated) vs unweighted mean of",
        f"a {len(DONOR_POOL)}-country donor pool of fiscal-rule-absent advanced ",
        "Eurozone economies + UK. PRE=2008 (year before the constitutional ",
        "amendment), POST=2019 (cleanest pre-COVID, pre-debt-brake-suspension ",
        "year).",
        "",
        "Outcomes:",
        "1. Δdebt-to-GDP (IMF GGXWDG_NGDP, level)",
        "2. Cumulative log-real-GDP-per-capita growth (WDI NY.GDP.PCAP.KD, log diff)",
        "3. Pre-trend log-growth 2000-2008 (parallel-trend diagnostic)",
        "4. Δgeneral-govt net lending / GDP (IMF GGXCNL_NGDP, informative)",
        "",
        "**Spec downgrade.** Original spec called for synthetic-DID; the donor-",
        "weight optimisation step is non-trivial and `synth_did` is not in the ",
        "project venv. Per research documentation allowance, downgraded to a ",
        "transparent before/after comparison with an explicit pre-trend ",
        "diagnostic. A real synth-DID would weight donors to match the pre-",
        "period; this comparison instead reports the unweighted donor mean ",
        "and the pre-period gap.",
        "",
        f"### Falsification thresholds",
        "",
        f"- PRIMARY 1 (debt): Germany Δdebt 2008-2019 must be ≥ "
        f"{DEBT_GAP_THRESHOLD_PP:.0f}pp lower than donor-pool mean.",
        f"- PRIMARY 2 (output): Germany cumulative log-growth 2008-2019 must "
        f"be ≥ {OUTPUT_RATIO_THRESHOLD*100:.0f}% of donor-pool mean.",
        f"- METHOD_VALID: at most {MAX_MISSING_DONORS} of "
        f"{len(DONOR_POOL)} donors missing data.",
        f"- INFORMATIVE: pre-trend gap |2000-2008 Δlog-GDP-pc| ≤ 5pp for clean "
        f"parallel-trend; if violated, verdict text flags caveat without ",
        f"overriding direction.",
        "",
        "## Data",
        "",
        "- imf:GGXWDG_NGDP (gross general-government debt / GDP)",
        "- imf:GGXCNL_NGDP (general-government net lending / GDP)",
        "- world_bank_wdi:NY.GDP.PCAP.KD (real GDP per capita, constant USD)",
        "",
        "## Caveats",
        "",
        "- Attribution to Schuldenbremse alone is contested. Confounds: ECB ",
        "policy reaction post-2010, intra-Eurozone competitiveness gaps, ",
        "German export demand boost from peripheral austerity, post-2010 ",
        "Hartz IV labour-market effects on unit labour costs.",
        "- Donor pool is a fixed Eurozone+UK convenience sample. Including ",
        "non-Eurozone non-fiscal-rule advanced economies (USA, JPN) would ",
        "shift the donor mean substantially.",
        "- 2008 pre-period endpoint is the eve of the Great Recession; both ",
        "Germany and donors entered POST with elevated debt due to crisis ",
        "interventions, which the simple endpoint comparison absorbs into ",
        "Δdebt for both sides equally.",
        "- The output ratio at low / negative donor means becomes unstable; ",
        "code falls back to a 5pp absolute-gap test in that regime.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
