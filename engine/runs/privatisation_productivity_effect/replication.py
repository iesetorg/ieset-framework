#!/usr/bin/env python3
"""Replication — Thatcher-era UK privatisations and productivity.

Spec: hypotheses/growth/privatisation_productivity_effect.yaml v1
Position-claim: classical_liberal #5 (school predicts: supported)

The seed spec called for a stacked FIRM-level event-study around BT 1984,
British Gas 1986, BA 1987 and water 1989. Firm-level productivity panels
are not in the framework's vintage tree (no FAME/Compustat-UK firm-year
parquets). This v1 promotes the country-level analogue:

  PRIMARY (dispositive):
    1) GBR mean annual TFP-growth (PWT rtfpna log-diff) over the
       privatisation window 1984-1990 must exceed the GBR pre-window
       1975-1983 mean by AT LEAST +0.5 percentage-points/year.
    2) GBR mean annual TFP-growth over 1984-1990 must exceed the
       comparator-country mean (FRA, DEU, ITA, ESP, NLD, SWE, USA, JPN)
       over the same window by AT LEAST +0.3 pp/year.

  SUPPORTED iff both PRIMARY hold; REFUTED iff both differentials are
  negative; PARTIAL otherwise; INCONCLUSIVE if PWT data missing for GBR
  or any comparator over 1975-1990.

  INFORMATIVE: labour-productivity (rgdpna/emp) DiD also positive;
  GBR-vs-comparator gap monotone over h=1..6.

  METHOD_VALID: at least 7 of 8 comparator countries with continuous
  PWT TFP data 1975-1990; pre-window length >= 5 years.
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
HID = "privatisation_productivity_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "GBR"
COMPARATORS = ["FRA", "DEU", "ITA", "ESP", "NLD", "SWE", "USA", "JPN"]
ALL_COUNTRIES = [TREATED] + COMPARATORS

# Anchor: BT November 1984 — the first of the four Thatcher-era big-four
# utility privatisations cited in the spec. Pre-window ends 1983 (the year
# before BT). Post-window 1984-1990 covers BT, British Gas (1986),
# BA (1987), water (1989); ends before the 1991 recession noise.
PRE_WINDOW = (1975, 1983)
POST_WINDOW = (1984, 1990)
EVENT_HORIZONS = list(range(1, 7))  # h=1..6 from anchor=1984

# Falsification thresholds (dispositive PRIMARY)
PRIMARY1_MIN_PRE_POST_DIFF = 0.005  # +0.5 pp/yr
PRIMARY2_MIN_VS_COMPARATOR_DIFF = 0.003  # +0.3 pp/yr


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
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def annual_log_growth(df: pd.DataFrame, country: str, lo: int, hi: int) -> list[float]:
    """Annual log-difference of `value` for country over [lo, hi] inclusive."""
    sub = (
        df[(df["country_iso3"] == country) & (df["year"].between(lo - 1, hi))]
        .sort_values("year")
        .set_index("year")["value"]
    )
    out = []
    for y in range(lo, hi + 1):
        if y - 1 in sub.index and y in sub.index and sub[y - 1] > 0 and sub[y] > 0:
            out.append(float(np.log(sub[y]) - np.log(sub[y - 1])))
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tfp_path = latest("pwt", "rtfpna")
    rgdpna_path = latest("pwt", "rgdpna")
    emp_path = latest("pwt", "emp")

    manifest = {
        "tfp_at_constant_national_prices": {
            "publisher": "pwt",
            "series": "rtfpna",
            "vintage_file": str(tfp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(tfp_path),
        },
        "real_gdp_at_constant_national_prices": {
            "publisher": "pwt",
            "series": "rgdpna",
            "vintage_file": str(rgdpna_path.relative_to(REPO_ROOT)),
            "sha256": sha256(rgdpna_path),
        },
        "employment": {
            "publisher": "pwt",
            "series": "emp",
            "vintage_file": str(emp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(emp_path),
        },
    }

    tfp = load_long(tfp_path)
    rgdpna = load_long(rgdpna_path)
    emp = load_long(emp_path)

    # ---------- METHOD-VALID gate ----------
    coverage = {}
    method_problems = []
    for c in ALL_COUNTRIES:
        years = set(tfp[tfp["country_iso3"] == c]["year"].astype(int).tolist())
        needed = set(range(PRE_WINDOW[0] - 1, POST_WINDOW[1] + 1))  # need 1974..1990
        missing = sorted(needed - years)
        coverage[c] = {"missing_years": missing, "n_years": len(years & needed)}
        if missing:
            method_problems.append(f"{c}: missing {missing}")

    n_full_comparators = sum(
        1 for c in COMPARATORS if not coverage[c]["missing_years"]
    )
    method_valid = (
        n_full_comparators >= 7
        and not coverage[TREATED]["missing_years"]
    )

    if not method_valid:
        verdict = (
            f"inconclusive — METHOD_VALID gate failed. PWT rtfpna missing "
            f"continuous coverage for GBR or comparators 1974-1990. "
            f"{n_full_comparators}/8 comparators with full coverage; "
            f"GBR missing years: {coverage[TREATED]['missing_years']}."
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "coverage": coverage,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    # ---------- PRIMARY 1: GBR pre vs post TFP growth ----------
    gbr_pre_growth = annual_log_growth(tfp, TREATED, PRE_WINDOW[0], PRE_WINDOW[1])
    gbr_post_growth = annual_log_growth(tfp, TREATED, POST_WINDOW[0], POST_WINDOW[1])

    gbr_pre_mean = float(np.mean(gbr_pre_growth))
    gbr_post_mean = float(np.mean(gbr_post_growth))
    pre_post_diff = gbr_post_mean - gbr_pre_mean
    primary1_pass = pre_post_diff >= PRIMARY1_MIN_PRE_POST_DIFF

    # ---------- PRIMARY 2: GBR vs comparator-mean post TFP growth ----------
    comp_post_means = {}
    for c in COMPARATORS:
        g = annual_log_growth(tfp, c, POST_WINDOW[0], POST_WINDOW[1])
        if g:
            comp_post_means[c] = float(np.mean(g))
    comp_post_mean = float(np.mean(list(comp_post_means.values())))
    vs_comparator_diff = gbr_post_mean - comp_post_mean
    primary2_pass = vs_comparator_diff >= PRIMARY2_MIN_VS_COMPARATOR_DIFF

    # Also: GBR pre vs comparator pre (for context)
    comp_pre_means = {}
    for c in COMPARATORS:
        g = annual_log_growth(tfp, c, PRE_WINDOW[0], PRE_WINDOW[1])
        if g:
            comp_pre_means[c] = float(np.mean(g))
    comp_pre_mean = float(np.mean(list(comp_pre_means.values())))
    # Difference-in-differences: (GBR post - GBR pre) - (Comp post - Comp pre)
    did = (gbr_post_mean - gbr_pre_mean) - (comp_post_mean - comp_pre_mean)

    # ---------- INFORMATIVE: labour productivity (rgdpna/emp) ----------
    # Build labour-productivity series per country, then log-diff
    def labprod_growth(country: str, lo: int, hi: int) -> list[float]:
        gdp = rgdpna[rgdpna["country_iso3"] == country].set_index("year")["value"]
        e = emp[emp["country_iso3"] == country].set_index("year")["value"]
        joined = pd.concat([gdp, e], axis=1, keys=["gdp", "emp"]).dropna()
        joined = joined[(joined["gdp"] > 0) & (joined["emp"] > 0)]
        joined["lp"] = joined["gdp"] / joined["emp"]
        joined = joined.sort_index()
        out = []
        for y in range(lo, hi + 1):
            if y - 1 in joined.index and y in joined.index:
                out.append(float(np.log(joined.loc[y, "lp"]) - np.log(joined.loc[y - 1, "lp"])))
        return out

    gbr_lp_pre = float(np.mean(labprod_growth(TREATED, *PRE_WINDOW)))
    gbr_lp_post = float(np.mean(labprod_growth(TREATED, *POST_WINDOW)))
    comp_lp_post = float(np.mean([
        float(np.mean(labprod_growth(c, *POST_WINDOW))) for c in COMPARATORS
    ]))
    comp_lp_pre = float(np.mean([
        float(np.mean(labprod_growth(c, *PRE_WINDOW))) for c in COMPARATORS
    ]))
    lp_did = (gbr_lp_post - gbr_lp_pre) - (comp_lp_post - comp_lp_pre)
    informative_lp_did_positive = lp_did > 0

    # INFORMATIVE: monotone widening of GBR-vs-comparator gap across h=1..6
    yearly_gaps = {}
    for h in EVENT_HORIZONS:
        y = POST_WINDOW[0] + h - 1  # h=1 → 1984
        gbr_g = annual_log_growth(tfp, TREATED, y, y)
        comp_g = [
            np.mean(annual_log_growth(tfp, c, y, y)) for c in COMPARATORS
        ]
        comp_g = [v for v in comp_g if not np.isnan(v)]
        if gbr_g and comp_g:
            yearly_gaps[h] = float(gbr_g[0] - float(np.mean(comp_g)))
    gap_values = [yearly_gaps[h] for h in sorted(yearly_gaps)]
    gap_monotone_widening = all(
        gap_values[i] <= gap_values[i + 1] for i in range(len(gap_values) - 1)
    ) if len(gap_values) >= 2 else False

    # ---------- Verdict ----------
    if primary1_pass and primary2_pass:
        verdict = (
            f"SUPPORTED — GBR TFP growth accelerated by "
            f"{pre_post_diff*100:+.2f}pp/yr (pre {gbr_pre_mean*100:+.2f}% → "
            f"post {gbr_post_mean*100:+.2f}%, threshold +0.5pp) AND beat the "
            f"comparator-OECD mean by {vs_comparator_diff*100:+.2f}pp/yr "
            f"(comparator post {comp_post_mean*100:+.2f}%, threshold +0.3pp). "
            f"DiD vs comparator OECD: {did*100:+.2f}pp/yr."
        )
    elif (not primary1_pass) and (not primary2_pass) and pre_post_diff < 0 and vs_comparator_diff < 0:
        verdict = (
            f"refuted — GBR TFP growth FELL post-1984 ("
            f"{pre_post_diff*100:+.2f}pp/yr, pre {gbr_pre_mean*100:+.2f}% → "
            f"post {gbr_post_mean*100:+.2f}%) AND underperformed the "
            f"comparator-OECD mean ({vs_comparator_diff*100:+.2f}pp/yr; "
            f"comparator post {comp_post_mean*100:+.2f}%). The "
            f"productivity-from-privatisation premise does not show in PWT "
            f"country-level TFP."
        )
    else:
        which_held = []
        which_missed = []
        if primary1_pass:
            which_held.append(
                f"pre/post change {pre_post_diff*100:+.2f}pp/yr ≥ +0.5pp"
            )
        else:
            which_missed.append(
                f"pre/post change {pre_post_diff*100:+.2f}pp/yr (need ≥ +0.5pp)"
            )
        if primary2_pass:
            which_held.append(
                f"vs-comparator {vs_comparator_diff*100:+.2f}pp/yr ≥ +0.3pp"
            )
        else:
            which_missed.append(
                f"vs-comparator {vs_comparator_diff*100:+.2f}pp/yr (need ≥ +0.3pp)"
            )
        verdict = (
            f"partial — One PRIMARY held, the other did not. Held: "
            f"{'; '.join(which_held) or 'none'}. Missed: "
            f"{'; '.join(which_missed) or 'none'}. GBR pre "
            f"{gbr_pre_mean*100:+.2f}% → post {gbr_post_mean*100:+.2f}%; "
            f"comparator post {comp_post_mean*100:+.2f}%; DiD "
            f"{did*100:+.2f}pp/yr."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "primary1_pre_post_pass": primary1_pass,
        "primary2_vs_comparator_pass": primary2_pass,
        "gbr_tfp_pre_mean": gbr_pre_mean,
        "gbr_tfp_post_mean": gbr_post_mean,
        "gbr_pre_post_diff": pre_post_diff,
        "primary1_threshold": PRIMARY1_MIN_PRE_POST_DIFF,
        "comparator_tfp_pre_mean": comp_pre_mean,
        "comparator_tfp_post_mean": comp_post_mean,
        "gbr_minus_comparator_post": vs_comparator_diff,
        "primary2_threshold": PRIMARY2_MIN_VS_COMPARATOR_DIFF,
        "did_tfp": did,
        "comparator_post_means": comp_post_means,
        "comparator_pre_means": comp_pre_means,
        "informative_labprod_did": lp_did,
        "informative_labprod_did_positive": informative_lp_did_positive,
        "gbr_labprod_pre_mean": gbr_lp_pre,
        "gbr_labprod_post_mean": gbr_lp_post,
        "yearly_gbr_minus_comparator_gaps": yearly_gaps,
        "gap_monotone_widening": gap_monotone_widening,
        "n_full_comparators": n_full_comparators,
        "pre_window": list(PRE_WINDOW),
        "post_window": list(POST_WINDOW),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F",
    ]
    series = []
    plot_lo, plot_hi = 1975, 1990
    # Index TFP to 1979 = 100 (Thatcher election year) for visual comparability
    for i, c in enumerate(ALL_COUNTRIES):
        sub = (
            tfp[(tfp["country_iso3"] == c) & (tfp["year"].between(plot_lo, plot_hi))]
            .sort_values("year")[["year", "value"]]
        )
        if sub.empty:
            continue
        base = sub[sub["year"] == 1979]["value"]
        if base.empty or float(base.iloc[0]) <= 0:
            continue
        b = float(base.iloc[0])
        pts = [
            {"x": int(r.year), "y": float(r.value / b * 100.0)}
            for r in sub.itertuples()
        ]
        series.append({
            "id": c,
            "label": c,
            "color": "#1f1f1f" if c == TREATED else palette[i % len(palette)],
            "treated": c == TREATED,
            "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "PWT TFP at constant national prices, 1975-1990 (1979 = 100)",
        "subtitle": (
            f"GBR pre-1984 mean TFP growth {gbr_pre_mean*100:+.2f}%/yr → "
            f"post-1984 {gbr_post_mean*100:+.2f}%/yr (Δ {pre_post_diff*100:+.2f}pp). "
            f"Comparator-OECD post-1984 mean {comp_post_mean*100:+.2f}%/yr; "
            f"DiD {did*100:+.2f}pp/yr."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "TFP index (1979 = 100)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 1984, "label": "BT privatisation (Nov 1984)"},
            {"type": "vline", "x": 1986, "label": "British Gas privatisation"},
            {"type": "vline", "x": 1989, "label": "Water privatisation"},
            {
                "type": "note",
                "label": (
                    f"Primary thresholds: GBR post-pre ≥ +0.5pp/yr; "
                    f"GBR-vs-comparator post ≥ +0.3pp/yr."
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

    coef_rows = [
        {"spec": "primary1", "term": "gbr_tfp_pre_mean", "estimate": gbr_pre_mean},
        {"spec": "primary1", "term": "gbr_tfp_post_mean", "estimate": gbr_post_mean},
        {"spec": "primary1", "term": "gbr_pre_post_diff", "estimate": pre_post_diff},
        {"spec": "primary2", "term": "comparator_tfp_post_mean", "estimate": comp_post_mean},
        {"spec": "primary2", "term": "gbr_minus_comparator_post", "estimate": vs_comparator_diff},
        {"spec": "did", "term": "tfp_did", "estimate": did},
        {"spec": "informative", "term": "labprod_did", "estimate": lp_did},
    ]
    for c, v in comp_post_means.items():
        coef_rows.append({"spec": "comparator_post", "term": c, "estimate": v})
    for h, g in yearly_gaps.items():
        coef_rows.append({"spec": "event_year_gap", "term": f"h{h}", "estimate": g})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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

    card = [
        f"# Thatcher-era UK privatisations and productivity",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- GBR mean annual TFP growth (PWT rtfpna) over 1975-1983 (pre): "
        f"**{gbr_pre_mean*100:+.2f}%/yr**.",
        f"- GBR mean annual TFP growth over 1984-1990 (post): "
        f"**{gbr_post_mean*100:+.2f}%/yr**.",
        f"- Pre/post change: **{pre_post_diff*100:+.2f}pp/yr** "
        f"(PRIMARY 1 threshold: ≥ +0.5pp; "
        f"{'PASS' if primary1_pass else 'FAIL'}).",
        f"- Comparator-OECD post-1984 mean (FRA, DEU, ITA, ESP, NLD, SWE, "
        f"USA, JPN): **{comp_post_mean*100:+.2f}%/yr**.",
        f"- GBR – comparator post: **{vs_comparator_diff*100:+.2f}pp/yr** "
        f"(PRIMARY 2 threshold: ≥ +0.3pp; "
        f"{'PASS' if primary2_pass else 'FAIL'}).",
        f"- DiD (post − pre, GBR vs comparator): "
        f"**{did*100:+.2f}pp/yr**.",
        f"- Labour-productivity DiD (rgdpna/emp): "
        f"**{lp_did*100:+.2f}pp/yr** (informative).",
        "",
        "## Method",
        "",
        "Country-level TFP DiD around the 1984 BT privatisation anchor:",
        "",
        "1. PWT 10.x rtfpna (TFP at constant national prices), log-differenced "
        "year-on-year for GBR and 8 OECD comparators.",
        "2. Pre-window 1975-1983 (9 years, ending the year before BT). "
        "Post-window 1984-1990 (7 years, ending before the 1991 recession).",
        "3. PRIMARY 1: pre/post change inside GBR ≥ +0.5pp/yr. "
        "PRIMARY 2: GBR – comparator-mean over 1984-1990 ≥ +0.3pp/yr.",
        "4. Labour productivity (rgdpna/emp) reported as INFORMATIVE only.",
        "",
        "**Caveats** (see steelman): country-level TFP cannot isolate the "
        "privatised-sector productivity effect from the rest-of-economy "
        "effect. The pre-1984 baseline includes Thatcher's 1979-1983 "
        "labour-shedding-under-public-ownership phase, which Florio (2004) "
        "argues did most of the lifting; this lifts the pre-mean and works "
        "AGAINST a privatisation-from-1984 finding. The 1980-1981 recession "
        "and recovery dynamics are an OECD-wide phenomenon and the "
        "comparator DiD addresses that confound. The price-reduction and "
        "cost-shifting components of the original claim are not tested.",
        "",
        "## Data",
        "",
        f"- pwt:rtfpna",
        f"- pwt:rgdpna",
        f"- pwt:emp",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
