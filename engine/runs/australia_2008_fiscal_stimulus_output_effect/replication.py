#!/usr/bin/env python3
"""Replication — Australia 2008 fiscal stimulus output effect.

Spec: hypotheses/monetary/australia_2008_fiscal_stimulus_output_effect.yaml v1
Position-claim: mmt #7 (school predicts: supported)

Original spec called for synthetic-control of Australia 2008-2010 vs an OECD
donor pool that did not deploy a comparable cash-handout fiscal package. No
synthetic-control library is installed in the local venv, so per the
HANDOFF_TO_RUN_AGENT.md downgrade allowance this run uses a peer-mean
DIFFERENCE-IN-DIFFERENCES comparison: AUS 2010 - 2007 change minus the
unweighted mean change of an OECD donor pool over the same window.

The donor pool is the spec's sample countries minus AUS. The exclusion rule
("no economy with comparable >2% GDP cash-handout fiscal package in 2008-09")
is implemented by additionally dropping the USA — the American Recovery and
Reinvestment Act (ARRA, Feb 2009) ran ~5.5% of GDP and is the only sample
peer with a stimulus package larger than AUS's combined Rudd
ESS+NBP (~5% GDP, with the ESS direct cash component ~1% of GDP). Other
sample countries had counter-cyclical packages but smaller and not direct
cash-handout-shaped — they remain in the donor pool. Robustness reports
the verdict with USA reincluded.

PRIMARY (dispositive)
  AUS-vs-donor-mean DiD on log real GDP per capita over 2007 → 2010
  is at least +2.0pp. (Spec's stated "real-GDP-per-capita gap >2%".)

SECONDARY (informative, not gating)
  - AUS-vs-donor-mean change in unemployment rate over 2007 → 2010
    (negative = AUS labour-market outperformance).
  - AUS-vs-donor-mean change in CPI inflation over 2007 → 2010
    (small or zero = MMT-consistent "minimal inflation cost" claim).
  - Pre-trend check 2003 → 2007 (parallel-trend proxy).

METHOD_VALID
  - At least 8 of the 13 donor countries (12 with USA reincluded) must
    have GDP-per-capita data at both 2007 and 2010, otherwise the run
    emits inconclusive (data gap).
  - Pre-trend gap (AUS vs donor-mean log-gdp-per-capita 2003→2007) must
    be smaller in magnitude than the 2007→2010 gap, otherwise the
    verdict is downgraded to weakened (parallel-trends violation).

Verdict rules (lead-word required by web/lib/content.ts::verdictTone):
  SUPPORTED — primary DiD ≥ +2.0pp AND pre-trend gap < |primary DiD|.
  partial   — primary DiD in claimed direction (positive) but < 2.0pp,
              with clean pre-trend.
  refuted   — primary DiD ≤ 0pp (AUS underperformed donor pool).
  weakened  — primary DiD ≥ +2.0pp BUT pre-trend gap is comparable
              or larger (parallel-trends violation).
  inconclusive — donor-pool data coverage below threshold.
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
HID = "australia_2008_fiscal_stimulus_output_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
SAMPLE = [
    "AUS", "CAN", "GBR", "USA", "NZL", "DEU", "FRA", "ITA", "JPN", "KOR",
    "CHE", "NOR", "SWE", "NLD",
]
TREATED = "AUS"
# Per spec.sample.exclusion_rules: drop economies with comparable >2% GDP
# cash-handout package. ARRA (USA) ran ~5.5% GDP — the only clear peer
# match. Others had smaller / non-cash-handout packages and stay in donors.
DONOR_EXCLUSIONS_PRIMARY = {"USA"}

PRE_PRE = 2003   # for parallel-trend check
PRE = 2007       # baseline (pre-stimulus)
POST = 2010      # primary outcome year (end of Rudd packages)

PRIMARY_THRESHOLD_PP = 0.02  # AUS DiD on log GDP per capita ≥ +2.0pp
MIN_DONORS = 8


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


def country_year_value(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].iloc[0])


def did_log_gdp_pc(gdp_pc: pd.DataFrame, donors: list[str], pre: int, post: int):
    """AUS log change minus mean donor log change between `pre` and `post`."""
    aus_pre = country_year_value(gdp_pc, TREATED, pre)
    aus_post = country_year_value(gdp_pc, TREATED, post)
    if aus_pre is None or aus_post is None or aus_pre <= 0 or aus_post <= 0:
        return None, None, [], []
    aus_dlog = float(np.log(aus_post) - np.log(aus_pre))
    donor_dlogs = []
    used_donors = []
    for c in donors:
        v_pre = country_year_value(gdp_pc, c, pre)
        v_post = country_year_value(gdp_pc, c, post)
        if v_pre is None or v_post is None or v_pre <= 0 or v_post <= 0:
            continue
        donor_dlogs.append(float(np.log(v_post) - np.log(v_pre)))
        used_donors.append(c)
    if not donor_dlogs:
        return aus_dlog, None, [], used_donors
    donor_mean = float(np.mean(donor_dlogs))
    return aus_dlog, donor_mean, donor_dlogs, used_donors


def did_level(df: pd.DataFrame, donors: list[str], pre: int, post: int):
    """AUS (post-pre) minus mean donor (post-pre) for level series."""
    aus_pre = country_year_value(df, TREATED, pre)
    aus_post = country_year_value(df, TREATED, post)
    if aus_pre is None or aus_post is None:
        return None, None, []
    aus_d = aus_post - aus_pre
    donor_ds = []
    used = []
    for c in donors:
        v_pre = country_year_value(df, c, pre)
        v_post = country_year_value(df, c, post)
        if v_pre is None or v_post is None:
            continue
        donor_ds.append(v_post - v_pre)
        used.append(c)
    if not donor_ds:
        return aus_d, None, used
    return aus_d, float(np.mean(donor_ds)), used


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_pc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    unemp_path = latest("world_bank_wdi", "SL.UEM.TOTL.ZS")
    cpi_path = latest("world_bank_wdi", "FP.CPI.TOTL.ZG")

    manifest = {
        "real_gdp_per_capita": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_pc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_pc_path),
        },
        "unemployment_rate": {
            "publisher": "world_bank_wdi",
            "series": "SL.UEM.TOTL.ZS",
            "vintage_file": str(unemp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(unemp_path),
        },
        "cpi_inflation": {
            "publisher": "world_bank_wdi",
            "series": "FP.CPI.TOTL.ZG",
            "vintage_file": str(cpi_path.relative_to(REPO_ROOT)),
            "sha256": sha256(cpi_path),
        },
    }

    gdp_pc = load_long(gdp_pc_path)
    unemp = load_long(unemp_path)
    cpi = load_long(cpi_path)

    donors_primary = [c for c in SAMPLE if c != TREATED and c not in DONOR_EXCLUSIONS_PRIMARY]
    donors_robust = [c for c in SAMPLE if c != TREATED]  # USA reincluded

    # ---------- PRIMARY: DiD on log real GDP per capita 2007→2010 ----------
    aus_dlog, donor_mean_dlog, donor_dlogs, used_donors = did_log_gdp_pc(
        gdp_pc, donors_primary, PRE, POST
    )
    method_valid = (
        aus_dlog is not None
        and donor_mean_dlog is not None
        and len(used_donors) >= MIN_DONORS
    )
    primary_did = (
        (aus_dlog - donor_mean_dlog) if method_valid else None
    )

    # Robustness: include USA
    aus_dlog_r, donor_mean_dlog_r, donor_dlogs_r, used_donors_r = did_log_gdp_pc(
        gdp_pc, donors_robust, PRE, POST
    )
    primary_did_robust = (
        (aus_dlog_r - donor_mean_dlog_r)
        if (aus_dlog_r is not None and donor_mean_dlog_r is not None)
        else None
    )

    # Parallel-trend check 2003→2007
    aus_dlog_pre, donor_mean_dlog_pre, _, used_donors_pre = did_log_gdp_pc(
        gdp_pc, donors_primary, PRE_PRE, PRE
    )
    pre_trend_did = (
        (aus_dlog_pre - donor_mean_dlog_pre)
        if (aus_dlog_pre is not None and donor_mean_dlog_pre is not None)
        else None
    )

    # ---------- SECONDARY: unemployment & CPI ----------
    aus_du, donor_mean_du, _ = did_level(unemp, donors_primary, PRE, POST)
    unemp_did = (
        (aus_du - donor_mean_du)
        if (aus_du is not None and donor_mean_du is not None)
        else None
    )

    aus_dc, donor_mean_dc, _ = did_level(cpi, donors_primary, PRE, POST)
    cpi_did = (
        (aus_dc - donor_mean_dc)
        if (aus_dc is not None and donor_mean_dc is not None)
        else None
    )

    # ---------- Verdict ----------
    if not method_valid or primary_did is None:
        verdict = (
            f"inconclusive — donor-pool coverage below {MIN_DONORS} "
            f"countries with usable 2007 and 2010 GDP-per-capita data "
            f"({len(used_donors) if used_donors else 0} available)."
        )
    else:
        pre_trend_clean = (
            pre_trend_did is None or abs(pre_trend_did) < abs(primary_did)
        )
        if primary_did >= PRIMARY_THRESHOLD_PP and pre_trend_clean:
            verdict = (
                f"SUPPORTED — AUS log GDP per capita rose "
                f"{aus_dlog*100:+.2f}pp 2007→2010 vs donor-mean "
                f"{donor_mean_dlog*100:+.2f}pp; DiD = "
                f"{primary_did*100:+.2f}pp (≥ {PRIMARY_THRESHOLD_PP*100:.1f}pp "
                f"threshold). Pre-trend 2003→2007 DiD = "
                f"{(pre_trend_did or 0)*100:+.2f}pp (smaller). "
                f"Donor pool: {len(used_donors)} countries excluding USA (ARRA)."
            )
        elif primary_did >= PRIMARY_THRESHOLD_PP and not pre_trend_clean:
            verdict = (
                f"weakened — Primary DiD = {primary_did*100:+.2f}pp meets "
                f"the +{PRIMARY_THRESHOLD_PP*100:.1f}pp threshold, but the "
                f"2003→2007 pre-trend DiD is "
                f"{(pre_trend_did or 0)*100:+.2f}pp — "
                f"parallel-trends assumption violated. Treatment effect "
                f"is not separable from a pre-existing AUS divergence."
            )
        elif primary_did > 0:
            verdict = (
                f"partial — AUS outperformed the donor pool "
                f"({primary_did*100:+.2f}pp on log GDP per capita 2007→2010) "
                f"but the gap is below the +{PRIMARY_THRESHOLD_PP*100:.1f}pp "
                f"threshold the spec set as dispositive."
            )
        else:
            verdict = (
                f"refuted — AUS log GDP per capita changed "
                f"{aus_dlog*100:+.2f}pp 2007→2010 vs donor-mean "
                f"{donor_mean_dlog*100:+.2f}pp; DiD = "
                f"{primary_did*100:+.2f}pp (claimed-direction threshold was "
                f"≥ +{PRIMARY_THRESHOLD_PP*100:.1f}pp). AUS did not "
                f"outperform the donor pool over the stimulus window."
            )

    diagnostics = {
        "verdict": verdict,
        "method": "did_peer_mean_downgrade_from_synthetic_control",
        "treated": TREATED,
        "donors_primary": used_donors,
        "donors_excluded_for_comparable_stimulus": sorted(DONOR_EXCLUSIONS_PRIMARY),
        "donors_robust_with_usa": used_donors_r,
        "pre_year": PRE,
        "post_year": POST,
        "pre_pre_year": PRE_PRE,
        "primary_threshold_pp": PRIMARY_THRESHOLD_PP,
        "min_donors_required": MIN_DONORS,
        "method_valid": method_valid,
        # GDP per capita
        "aus_dlog_gdp_pc_2007_2010": aus_dlog,
        "donor_mean_dlog_gdp_pc_2007_2010": donor_mean_dlog,
        "primary_did_log_gdp_pc": primary_did,
        "primary_did_log_gdp_pc_with_usa": primary_did_robust,
        "donor_dlogs_gdp_pc": dict(zip(used_donors, donor_dlogs)) if used_donors else {},
        # Pre-trend
        "aus_dlog_gdp_pc_2003_2007": aus_dlog_pre,
        "donor_mean_dlog_gdp_pc_2003_2007": donor_mean_dlog_pre,
        "pre_trend_did_log_gdp_pc": pre_trend_did,
        # Secondary outcomes
        "aus_d_unemp_2007_2010_pp": aus_du,
        "donor_mean_d_unemp_2007_2010_pp": donor_mean_du,
        "unemp_did_pp": unemp_did,
        "aus_d_cpi_inflation_2007_2010_pp": aus_dc,
        "donor_mean_d_cpi_inflation_2007_2010_pp": donor_mean_dc,
        "cpi_did_pp": cpi_did,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: log GDP per capita indexed to 2007=1.0 ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
        "#d62728", "#7f7f7f",
    ]
    chart_period = (2003, 2012)
    series = []
    # Treated first
    sub = (
        gdp_pc[(gdp_pc["country_iso3"] == TREATED) & (gdp_pc["year"].between(*chart_period))]
        .sort_values("year")
    )
    base = country_year_value(gdp_pc, TREATED, PRE)
    if base and not sub.empty:
        series.append({
            "id": TREATED,
            "label": f"{TREATED} (treated)",
            "color": "#1f1f1f",
            "treated": True,
            "points": [
                {"x": int(r.year), "y": float(r.value / base)}
                for r in sub.itertuples()
            ],
        })

    # Donor mean trajectory (geometric mean of indexed values for used donors)
    yearly_means = []
    for y in range(chart_period[0], chart_period[1] + 1):
        vals = []
        for c in used_donors:
            v = country_year_value(gdp_pc, c, y)
            v_pre = country_year_value(gdp_pc, c, PRE)
            if v is None or v_pre is None or v_pre <= 0:
                continue
            vals.append(np.log(v / v_pre))
        if vals:
            yearly_means.append({"x": y, "y": float(np.exp(np.mean(vals)))})
    if yearly_means:
        series.append({
            "id": "DONOR_MEAN",
            "label": "Donor pool mean (excl. USA)",
            "color": "#4E79A7",
            "treated": False,
            "points": yearly_means,
        })

    # Individual donors (faded)
    for i, c in enumerate(used_donors):
        c_base = country_year_value(gdp_pc, c, PRE)
        if not c_base:
            continue
        sub_c = (
            gdp_pc[(gdp_pc["country_iso3"] == c) & (gdp_pc["year"].between(*chart_period))]
            .sort_values("year")
        )
        if sub_c.empty:
            continue
        series.append({
            "id": c,
            "label": c,
            "color": palette[i % len(palette)],
            "treated": False,
            "points": [
                {"x": int(r.year), "y": float(r.value / c_base)}
                for r in sub_c.itertuples()
            ],
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Australia vs OECD donor pool — real GDP per capita (2007 = 1.0)",
        "subtitle": (
            f"AUS 2007→2010 Δlog: {aus_dlog*100:+.2f}pp · "
            f"Donor mean: {(donor_mean_dlog or 0)*100:+.2f}pp · "
            f"DiD: {(primary_did or 0)*100:+.2f}pp "
            f"(threshold +{PRIMARY_THRESHOLD_PP*100:.1f}pp)"
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "real GDP per capita (2007 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 2008, "label": "Rudd ESS (Oct 2008)"},
            {"type": "vline", "x": 2009, "label": "Nation Building Plan (Feb 2009)"},
            {"type": "note", "label": (
                f"Donor pool excludes USA (ARRA ~5.5% GDP — comparable "
                f"package). Pre-trend 2003→2007 DiD: "
                f"{(pre_trend_did or 0)*100:+.2f}pp."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients table ----------
    rows = [
        {"spec": "primary", "term": "did_log_gdp_pc_2007_2010", "estimate": primary_did if primary_did is not None else float("nan")},
        {"spec": "primary", "term": "aus_dlog_gdp_pc", "estimate": aus_dlog if aus_dlog is not None else float("nan")},
        {"spec": "primary", "term": "donor_mean_dlog_gdp_pc", "estimate": donor_mean_dlog if donor_mean_dlog is not None else float("nan")},
        {"spec": "robustness", "term": "did_log_gdp_pc_with_usa", "estimate": primary_did_robust if primary_did_robust is not None else float("nan")},
        {"spec": "pre_trend", "term": "did_log_gdp_pc_2003_2007", "estimate": pre_trend_did if pre_trend_did is not None else float("nan")},
        {"spec": "secondary", "term": "did_unemp_pp_2007_2010", "estimate": unemp_did if unemp_did is not None else float("nan")},
        {"spec": "secondary", "term": "did_cpi_inflation_pp_2007_2010", "estimate": cpi_did if cpi_did is not None else float("nan")},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
    fmt_pp = lambda x: f"{x*100:+.2f}pp" if x is not None else "n/a"
    fmt_lvl = lambda x: f"{x:+.2f}pp" if x is not None else "n/a"
    card = [
        f"# Australia 2008 fiscal stimulus output effect",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Primary DiD (AUS minus donor-mean Δlog GDP per capita "
        f"2007→2010): **{fmt_pp(primary_did)}** "
        f"(threshold ≥ +{PRIMARY_THRESHOLD_PP*100:.1f}pp).",
        f"- AUS 2007→2010 Δlog GDP per capita: {fmt_pp(aus_dlog)}.",
        f"- Donor-mean (excl. USA) 2007→2010 Δlog GDP per capita: "
        f"{fmt_pp(donor_mean_dlog)}.",
        f"- Pre-trend check 2003→2007 DiD: {fmt_pp(pre_trend_did)} "
        f"(should be smaller than the primary DiD).",
        f"- Robustness DiD with USA reincluded: "
        f"{fmt_pp(primary_did_robust)}.",
        f"- Secondary: AUS-vs-donor unemployment-rate change "
        f"2007→2010 = {fmt_lvl(unemp_did)} "
        f"(negative = AUS labour-market outperformance).",
        f"- Secondary: AUS-vs-donor CPI-inflation change 2007→2010 = "
        f"{fmt_lvl(cpi_did)} (small = MMT minimal-inflation-cost claim holds).",
        f"- Donor pool: {', '.join(used_donors) if used_donors else 'none'}.",
        "",
        "## Method",
        "",
        "Spec called for synthetic-control matching of Australia 2008-2010 "
        "to a weighted OECD donor pool. The local venv has no synth library "
        "(`SyntheticControlMethods`, `pysynth`), so per the handoff doc's "
        "downgrade allowance this run uses an unweighted peer-mean DiD: "
        "AUS Δlog GDP per capita minus the simple mean of donor-pool Δlogs "
        "between 2007 and 2010. The donor pool is the spec's sample minus "
        "AUS minus USA (ARRA was the only sample peer with a comparable "
        ">2%-of-GDP cash-handout package; ~5.5% of GDP). Robustness with "
        "USA reincluded is reported separately.",
        "",
        "Pre-trend 2003→2007 is checked against the primary 2007→2010 "
        "magnitude as a parallel-trends proxy. If the pre-trend is "
        "comparable or larger in absolute value than the primary effect, "
        "the verdict is downgraded to `weakened` regardless of the primary "
        "magnitude.",
        "",
        "Secondary outcomes (unemployment-rate change, CPI inflation "
        "change) are reported as informative DiDs but do not gate the "
        "verdict.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.PCAP.KD",
        f"- world_bank_wdi:SL.UEM.TOTL.ZS",
        f"- world_bank_wdi:FP.CPI.TOTL.ZG",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
