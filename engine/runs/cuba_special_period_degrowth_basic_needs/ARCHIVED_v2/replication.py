#!/usr/bin/env python3
"""Replication — Cuba Special Period (1989-2000) degrowth + basic-needs preservation.

Spec: hypotheses/growth/cuba_special_period_degrowth_basic_needs.yaml v2
Position-claim: degrowth #5 (school predicts: mixed, polarity aligned)

Tests two empirical regularities flagged by the degrowth-school
"Cuba-as-decoupling-success" claim:

  PRIMARY 1 (the contraction premise): Cuban real GDP per capita
            (WDI NY.GDP.PCAP.KD) contracted by at least 25% from
            its 1989 peak to its 1991-1995 trough. Without a real
            contraction the "forced degrowth" framing is empty.

  PRIMARY 2 (the basic-needs claim): None of the three basic-needs
            indicators (life expectancy SP.DYN.LE00.IN, infant
            mortality SP.DYN.IMRT.IN, primary-school gross enrolment
            SE.PRM.ENRR) degraded by more than 10% from the 1989
            baseline at any point in 1990-2000.

Hypothesis is SUPPORTED only if BOTH primaries hold. REFUTED if the
contraction was below threshold OR more than one basic-needs
indicator degraded >10%. PARTIAL otherwise (one indicator missed).

Method-validity gate: if any of the four series has a gap in the
1991-1995 trough window, verdict downgrades to inconclusive (data
gap on world_bank_wdi:<series>) rather than refuted.

Mirrors engine/runs/post_2008_oecd_growth_emissions_path/replication.py
canonical example.
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
HID = "cuba_special_period_degrowth_basic_needs"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from the spec
COUNTRY = "CUB"
PERIOD = (1989, 2000)
TROUGH_WINDOW = (1991, 1995)
BASELINE_YEAR = 1989

# Falsification thresholds (from spec.falsification.threshold)
GDP_CONTRACTION_THRESHOLD = 0.25  # >=25% peak-to-trough required
BASIC_NEEDS_DEGRADATION_THRESHOLD = 0.10  # any >10% degradation = fail


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
    """Standard normaliser: keep (country_iso3, year, value) rows."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator_id", "unit", "obs_status", "decimal"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def cub_series(path: Path) -> pd.Series:
    """Return CUB year -> value, sorted, restricted to PERIOD."""
    df = load_long(path)
    s = (
        df[(df["country_iso3"] == COUNTRY)
           & (df["year"].between(PERIOD[0], PERIOD[1]))]
        .set_index("year")["value"]
        .sort_index()
    )
    s.index = s.index.astype(int)
    return s


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    series_meta = {
        "gdp_per_capita": ("world_bank_wdi", "NY.GDP.PCAP.KD"),
        "life_expectancy": ("world_bank_wdi", "SP.DYN.LE00.IN"),
        "infant_mortality": ("world_bank_wdi", "SP.DYN.IMRT.IN"),
        "primary_enrolment": ("world_bank_wdi", "SE.PRM.ENRR"),
    }

    paths = {k: latest(pub, ser) for k, (pub, ser) in series_meta.items()}
    manifest = {
        k: {
            "publisher": series_meta[k][0],
            "series": series_meta[k][1],
            "vintage_file": str(paths[k].relative_to(REPO_ROOT)),
            "sha256": sha256(paths[k]),
        }
        for k in series_meta
    }

    cub = {k: cub_series(p) for k, p in paths.items()}

    # ---------- METHOD_VALID gate ----------
    method_problems: list[str] = []
    for k, s in cub.items():
        trough_years = set(range(TROUGH_WINDOW[0], TROUGH_WINDOW[1] + 1))
        present_trough = trough_years & set(s.index)
        if BASELINE_YEAR not in s.index:
            method_problems.append(f"{series_meta[k][1]} missing 1989 baseline")
        if len(present_trough) < len(trough_years):
            missing = sorted(trough_years - set(s.index))
            method_problems.append(
                f"{series_meta[k][1]} missing {missing} in trough window"
            )

    # ---------- PRIMARY 1: GDP contraction ----------
    gdp = cub["gdp_per_capita"]
    gdp_baseline = float(gdp.loc[BASELINE_YEAR]) if BASELINE_YEAR in gdp.index else float("nan")
    gdp_trough_window = gdp.loc[
        (gdp.index >= TROUGH_WINDOW[0]) & (gdp.index <= TROUGH_WINDOW[1])
    ]
    gdp_trough_value = float(gdp_trough_window.min()) if len(gdp_trough_window) else float("nan")
    gdp_trough_year = (
        int(gdp_trough_window.idxmin()) if len(gdp_trough_window) else None
    )
    gdp_decline_fraction = (
        (gdp_baseline - gdp_trough_value) / gdp_baseline
        if gdp_baseline and not np.isnan(gdp_trough_value) else float("nan")
    )
    gdp_2000 = float(gdp.loc[2000]) if 2000 in gdp.index else float("nan")
    gdp_recovery_fraction = (
        (gdp_2000 / gdp_baseline) if gdp_baseline and not np.isnan(gdp_2000) else float("nan")
    )
    primary1_contraction_held = (
        not np.isnan(gdp_decline_fraction)
        and gdp_decline_fraction >= GDP_CONTRACTION_THRESHOLD
    )

    # ---------- PRIMARY 2: basic-needs preservation ----------
    # For each indicator, check the worst-case 1990-2000 deviation from baseline.
    # LE / enrolment: degradation = decline (lower is worse).
    # IMR: degradation = rise (higher is worse).
    bn_results: dict[str, dict] = {}

    def post_baseline(s: pd.Series) -> pd.Series:
        return s.loc[(s.index >= BASELINE_YEAR + 1) & (s.index <= PERIOD[1])]

    # Life expectancy: check max decline from baseline
    le = cub["life_expectancy"]
    le_baseline = float(le.loc[BASELINE_YEAR]) if BASELINE_YEAR in le.index else float("nan")
    le_post = post_baseline(le)
    le_min = float(le_post.min()) if len(le_post) else float("nan")
    le_min_year = int(le_post.idxmin()) if len(le_post) else None
    le_max_decline_pct = (
        (le_baseline - le_min) / le_baseline
        if le_baseline and not np.isnan(le_min) else float("nan")
    )
    le_2000 = float(le.loc[2000]) if 2000 in le.index else float("nan")
    bn_results["life_expectancy"] = {
        "baseline_1989": le_baseline,
        "min_post_1989": le_min,
        "min_year": le_min_year,
        "value_2000": le_2000,
        "max_decline_pct": le_max_decline_pct,
        "preserved": (
            not np.isnan(le_max_decline_pct)
            and le_max_decline_pct <= BASIC_NEEDS_DEGRADATION_THRESHOLD
        ),
    }

    # Infant mortality: check max rise from baseline (any year > baseline*1.10 fails)
    imr = cub["infant_mortality"]
    imr_baseline = float(imr.loc[BASELINE_YEAR]) if BASELINE_YEAR in imr.index else float("nan")
    imr_post = post_baseline(imr)
    imr_max = float(imr_post.max()) if len(imr_post) else float("nan")
    imr_max_year = int(imr_post.idxmax()) if len(imr_post) else None
    imr_max_rise_pct = (
        (imr_max - imr_baseline) / imr_baseline
        if imr_baseline and not np.isnan(imr_max) else float("nan")
    )
    imr_2000 = float(imr.loc[2000]) if 2000 in imr.index else float("nan")
    bn_results["infant_mortality"] = {
        "baseline_1989": imr_baseline,
        "max_post_1989": imr_max,
        "max_year": imr_max_year,
        "value_2000": imr_2000,
        "max_rise_pct": imr_max_rise_pct,
        "preserved": (
            not np.isnan(imr_max_rise_pct)
            and imr_max_rise_pct <= BASIC_NEEDS_DEGRADATION_THRESHOLD
        ),
    }

    # Primary enrolment: check max decline from baseline
    enr = cub["primary_enrolment"]
    enr_baseline = float(enr.loc[BASELINE_YEAR]) if BASELINE_YEAR in enr.index else float("nan")
    enr_post = post_baseline(enr)
    enr_min = float(enr_post.min()) if len(enr_post) else float("nan")
    enr_min_year = int(enr_post.idxmin()) if len(enr_post) else None
    enr_max_decline_pct = (
        (enr_baseline - enr_min) / enr_baseline
        if enr_baseline and not np.isnan(enr_min) else float("nan")
    )
    enr_2000 = float(enr.loc[2000]) if 2000 in enr.index else float("nan")
    bn_results["primary_enrolment"] = {
        "baseline_1989": enr_baseline,
        "min_post_1989": enr_min,
        "min_year": enr_min_year,
        "value_2000": enr_2000,
        "max_decline_pct": enr_max_decline_pct,
        "preserved": (
            not np.isnan(enr_max_decline_pct)
            and enr_max_decline_pct <= BASIC_NEEDS_DEGRADATION_THRESHOLD
        ),
    }

    n_basic_needs_preserved = sum(1 for r in bn_results.values() if r["preserved"])
    n_basic_needs_degraded = 3 - n_basic_needs_preserved
    primary2_basic_needs_held = n_basic_needs_degraded == 0

    # ---------- Verdict ----------
    if method_problems:
        verdict = (
            "inconclusive (data gap on " + "; ".join(method_problems) + ")"
        )
        all_pass = False
    elif primary1_contraction_held and primary2_basic_needs_held:
        verdict = (
            f"SUPPORTED — Cuban real GDP per capita contracted "
            f"{gdp_decline_fraction*100:.1f}% from {BASELINE_YEAR} (USD "
            f"{gdp_baseline:.0f}) to {gdp_trough_year} trough (USD "
            f"{gdp_trough_value:.0f}); >=25% threshold met. All three "
            f"basic-needs indicators preserved through 2000: life "
            f"expectancy {le_baseline:.1f}y -> {le_2000:.1f}y; infant "
            f"mortality {imr_baseline:.1f}/1k -> {imr_2000:.1f}/1k; "
            f"primary enrolment {enr_baseline:.1f}% -> {enr_2000:.1f}% "
            f"(no >10% degradation in any year)."
        )
        all_pass = True
    elif not primary1_contraction_held:
        verdict = (
            f"refuted — GDP contraction of "
            f"{gdp_decline_fraction*100:.1f}% peak-to-trough is below "
            f"the 25% 'forced degrowth' threshold; the canonical "
            f"Special Period premise does not hold in this vintage."
        )
        all_pass = False
    elif n_basic_needs_degraded == 1:
        bad = next(k for k, r in bn_results.items() if not r["preserved"])
        verdict = (
            f"partial — GDP contracted {gdp_decline_fraction*100:.1f}% "
            f"(threshold met) but basic-needs indicator '{bad}' "
            f"degraded >10% from 1989 baseline. Other two indicators "
            f"preserved."
        )
        all_pass = False
    else:
        bad = ", ".join(k for k, r in bn_results.items() if not r["preserved"])
        verdict = (
            f"refuted — GDP contracted {gdp_decline_fraction*100:.1f}% "
            f"(threshold met) but {n_basic_needs_degraded} of 3 "
            f"basic-needs indicators degraded >10% from 1989 baseline "
            f"({bad}). Basic-needs preservation claim does not hold."
        )
        all_pass = False

    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "primary1_contraction_held": bool(primary1_contraction_held),
        "primary2_basic_needs_held": bool(primary2_basic_needs_held),
        "method_problems": method_problems,
        "gdp_per_capita": {
            "baseline_1989": gdp_baseline,
            "trough_value": gdp_trough_value,
            "trough_year": gdp_trough_year,
            "decline_fraction": gdp_decline_fraction,
            "value_2000": gdp_2000,
            "recovery_fraction_2000": gdp_recovery_fraction,
            "threshold": GDP_CONTRACTION_THRESHOLD,
        },
        "basic_needs": bn_results,
        "basic_needs_threshold": BASIC_NEEDS_DEGRADATION_THRESHOLD,
        "n_basic_needs_preserved": n_basic_needs_preserved,
        "n_basic_needs_degraded": n_basic_needs_degraded,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=float) + "\n")

    # ---------- Chart ----------
    palette = {
        "GDP per capita (2015 USD)": "#4E79A7",
        "Life expectancy (years)": "#59A14F",
        "Infant mortality (per 1,000)": "#E15759",
        "Primary enrolment (% gross)": "#F28E2B",
    }

    def index_series(s: pd.Series) -> list[dict]:
        baseline = float(s.loc[BASELINE_YEAR]) if BASELINE_YEAR in s.index else None
        if not baseline:
            return []
        return [
            {"x": int(y), "y": float(v / baseline)}
            for y, v in s.items()
        ]

    series_payload = [
        {
            "id": "gdp",
            "label": "GDP per capita (1989=1.0)",
            "color": palette["GDP per capita (2015 USD)"],
            "treated": True,
            "points": index_series(gdp),
        },
        {
            "id": "life_expectancy",
            "label": "Life expectancy (1989=1.0)",
            "color": palette["Life expectancy (years)"],
            "treated": False,
            "points": index_series(le),
        },
        {
            "id": "infant_mortality",
            "label": "Infant mortality (1989=1.0; lower is better)",
            "color": palette["Infant mortality (per 1,000)"],
            "treated": False,
            "points": index_series(imr),
        },
        {
            "id": "primary_enrolment",
            "label": "Primary enrolment (1989=1.0)",
            "color": palette["Primary enrolment (% gross)"],
            "treated": False,
            "points": index_series(enr),
        },
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Cuba Special Period: GDP collapse vs basic-needs indicators (1989-2000, indexed)",
        "subtitle": (
            f"GDP per capita {gdp_decline_fraction*100:.1f}% peak-to-trough "
            f"(1989->{gdp_trough_year}); LE {le_baseline:.1f}y->{le_2000:.1f}y; "
            f"IMR {imr_baseline:.1f}->{imr_2000:.1f} per 1k; "
            f"primary enrolment {enr_baseline:.0f}%->{enr_2000:.0f}%."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Value indexed to 1989 = 1.0", "type": "linear"},
        "series": series_payload,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Verdict: {verdict}"
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

    # ---------- coefficients table ----------
    pd.DataFrame(
        [
            {"spec": "primary1", "term": "gdp_pc_baseline_1989", "estimate": gdp_baseline},
            {"spec": "primary1", "term": "gdp_pc_trough_value", "estimate": gdp_trough_value},
            {"spec": "primary1", "term": "gdp_pc_trough_year", "estimate": float(gdp_trough_year) if gdp_trough_year else float("nan")},
            {"spec": "primary1", "term": "gdp_pc_decline_fraction", "estimate": gdp_decline_fraction},
            {"spec": "primary1", "term": "gdp_pc_recovery_fraction_2000", "estimate": gdp_recovery_fraction},
            {"spec": "primary2", "term": "life_expectancy_baseline_1989", "estimate": le_baseline},
            {"spec": "primary2", "term": "life_expectancy_max_decline_pct", "estimate": le_max_decline_pct},
            {"spec": "primary2", "term": "life_expectancy_2000", "estimate": le_2000},
            {"spec": "primary2", "term": "infant_mortality_baseline_1989", "estimate": imr_baseline},
            {"spec": "primary2", "term": "infant_mortality_max_rise_pct", "estimate": imr_max_rise_pct},
            {"spec": "primary2", "term": "infant_mortality_2000", "estimate": imr_2000},
            {"spec": "primary2", "term": "primary_enrolment_baseline_1989", "estimate": enr_baseline},
            {"spec": "primary2", "term": "primary_enrolment_max_decline_pct", "estimate": enr_max_decline_pct},
            {"spec": "primary2", "term": "primary_enrolment_2000", "estimate": enr_2000},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- manifest ----------
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

    # ---------- result card ----------
    card = [
        f"# Cuba Special Period — degrowth + basic-needs preservation (1989-2000)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Real GDP per capita: **{gdp_baseline:.0f} USD (1989) -> "
        f"{gdp_trough_value:.0f} USD ({gdp_trough_year} trough) -> "
        f"{gdp_2000:.0f} USD (2000)**. Peak-to-trough decline: "
        f"**{gdp_decline_fraction*100:.1f}%** (threshold: >=25%). "
        f"Recovery to 2000: {gdp_recovery_fraction*100:.0f}% of 1989 level.",
        f"- Life expectancy at birth: **{le_baseline:.2f}y (1989) -> "
        f"{le_min:.2f}y (min, {le_min_year}) -> {le_2000:.2f}y (2000)**. "
        f"Max decline from baseline: {le_max_decline_pct*100:+.2f}% "
        f"(threshold: -10% / +10%). Preserved: "
        f"{bn_results['life_expectancy']['preserved']}.",
        f"- Infant mortality rate: **{imr_baseline:.2f}/1k (1989) -> "
        f"{imr_max:.2f}/1k (max, {imr_max_year}) -> {imr_2000:.2f}/1k (2000)**. "
        f"Max rise from baseline: {imr_max_rise_pct*100:+.2f}% "
        f"(threshold: <=+10%). Preserved: "
        f"{bn_results['infant_mortality']['preserved']}.",
        f"- Primary-school gross enrolment: **{enr_baseline:.2f}% (1989) -> "
        f"{enr_min:.2f}% (min, {enr_min_year}) -> {enr_2000:.2f}% (2000)**. "
        f"Max decline from baseline: {enr_max_decline_pct*100:+.2f}% "
        f"(threshold: <=10%). Preserved: "
        f"{bn_results['primary_enrolment']['preserved']}.",
        "",
        "## Method",
        "",
        "Two dispositive primary tests against the spec's stated falsification rule:",
        "",
        "1. GDP per capita peak-to-trough decline 1989 -> argmin(1991..1995). "
        "Threshold: >=25%.",
        "2. For each of three basic-needs indicators, worst-case "
        "deviation from 1989 baseline across 1990-2000 must be within "
        "+/-10% on the wrong-direction side.",
        "",
        "Method-validity gate: all four WDI series must have CUB "
        "observations covering 1989-2000 with no gaps in the trough "
        "window 1991-1995. Missing data emits inconclusive, not refuted.",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/cuba_special_period_degrowth_basic_needs.md`. "
        "The 4-indicator set is the favourable subset; caloric intake, "
        "electricity availability, transport, consumer goods, and "
        "emigration as revealed-preference welfare are NOT in the test. "
        "Pre-1989 Soviet subsidies underwrote the health/education "
        "capital stock that produced the post-1989 inertia; 1989-2000 "
        "is short relative to the depreciation horizon for clinical "
        "and educational infrastructure. Cuban official IMR statistics "
        "carry a 1-3/1k uncertainty band that WHO independent series "
        "cannot cross-check before ~2000.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.PCAP.KD",
        f"- world_bank_wdi:SP.DYN.LE00.IN",
        f"- world_bank_wdi:SP.DYN.IMRT.IN",
        f"- world_bank_wdi:SE.PRM.ENRR",
        "",
        "All four series for CUB 1989-2000. Vintages pinned in "
        "`manifest.yaml` with sha256 hashes. The v0 archive (under "
        "`ARCHIVED_v0/`) was a pre-fix multi-metric runner output "
        "against placeholder source identifiers and is not "
        "substantively comparable to this v2 run.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
