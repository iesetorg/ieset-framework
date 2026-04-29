"""
uk_cameron_osborne_austerity_output_effect replication.

Tests the post-Keynesian claim that UK Cameron-Osborne austerity 2010-2016
reduced output below the counterfactual path AND failed to hit the 2010
debt-target on government's own timeline.

PRIMARY (dispositive): cumulative log GDP-per-capita gap UK − donor-pool
mean by 2014 ≤ −0.02 log-points (~−2 %) AND general government gross debt
% GDP at 2015 exceeds the 2010 government target by > 5 percentage points.

INFORMATIVE: per-donor log-gap dispersion; debt trajectory 2010-2016;
synth-DiD style donor weighting reported as a check on the equal-weighted
mean.

METHOD_VALID: WDI NY.GDP.PCAP.KD covers GBR + all 5 donors over 2007-2016;
IMF GGXWDG_NGDP covers GBR over 2010-2015.

Donor pool: USA, FRA, JPN, AUS, CAN — advanced economies with comparable
pre-2010 fiscal positions but no Cameron-Osborne-style consolidation
intensity. (FRA + JPN had their own consolidations later in the window;
this biases the test against finding an austerity effect, which is
conservative for the hypothesis.)
"""

from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
HID = "uk_cameron_osborne_austerity_output_effect"

DONORS = ["USA", "FRA", "JPN", "AUS", "CAN"]
TREATED = "GBR"
PRE = list(range(2007, 2010))    # 2007-2009 pre-window
POST = list(range(2010, 2017))   # 2010-2016 post window
GAP_YEAR = 2014                  # primary measurement year
DEBT_TARGET_2010_FOR_2015 = 67.0  # OBR June 2010 trajectory: PSND/GDP target ~67% by 2014-15
GAP_THRESHOLD = -0.02            # SUPPORTED if UK − donor mean log-gap <= this
DEBT_OVERSHOOT_PP = 5.0           # SUPPORTED if 2015 debt exceeds target by > 5pp


def latest(publisher: str, series: str) -> Optional[Path]:
    d = ROOT / "data" / "vintages" / publisher
    if not d.exists():
        return None
    cands = sorted(d.glob(f"{series}@*.parquet"))
    return cands[-1] if cands else None


def load_wdi(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    cols = {c.lower(): c for c in t.columns}
    iso_col = cols.get("country_iso3") or cols.get("iso3") or cols.get("countrycode")
    yr_col = cols.get("year") or cols.get("date")
    val_col = cols.get("value") or [c for c in t.columns if c not in (iso_col, yr_col)][-1]
    df = t[[iso_col, yr_col, val_col]].copy()
    df.columns = ["iso3", "year", "value"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


def get_year(df: pd.DataFrame, iso: str, year: int) -> Optional[float]:
    sub = df[(df["iso3"] == iso) & (df["year"] == year)]
    return float(sub.iloc[0]["value"]) if not sub.empty else None


def main():
    p_gdp = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    p_debt = latest("imf", "GGXWDG_NGDP")

    if p_gdp is None:
        diag = {"verdict": "inconclusive — data gap on world_bank_wdi:NY.GDP.PCAP.KD",
                "method_valid": False}
        (RUN_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2))
        print(diag["verdict"])
        return

    gdp = load_wdi(p_gdp)

    countries = [TREATED] + DONORS
    coverage_ok = all(
        all(get_year(gdp, c, y) is not None for y in (2007, 2009, GAP_YEAR))
        for c in countries
    )
    if not coverage_ok:
        diag = {"verdict": f"inconclusive — data gap: GDP coverage incomplete for one of {countries} over 2007-{GAP_YEAR}",
                "method_valid": False}
        (RUN_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2))
        print(diag["verdict"])
        return

    # Cumulative log GDP-pc growth 2009 -> GAP_YEAR for each country
    growth_log = {}
    for c in countries:
        g0 = get_year(gdp, c, 2009)
        gT = get_year(gdp, c, GAP_YEAR)
        growth_log[c] = math.log(gT / g0)

    uk_growth = growth_log[TREATED]
    donor_mean = float(np.mean([growth_log[c] for c in DONORS]))
    uk_gap = uk_growth - donor_mean

    # Convex (non-negative, sum-to-1) donor weights minimising MSE on the
    # 2007-2009 pre-period log-GDP-pc TREND. Closed-form for 2-pt vector:
    # use grid search over simplex (5-D, n=5) with step 0.05.
    pre_growth = {}
    for c in countries:
        g0 = get_year(gdp, c, 2007)
        g1 = get_year(gdp, c, 2009)
        pre_growth[c] = math.log(g1 / g0)
    target_pre = pre_growth[TREATED]
    donor_pre = np.array([pre_growth[c] for c in DONORS])

    # Random-search convex weights
    rng = np.random.default_rng(42)
    best = None
    for _ in range(20000):
        w = rng.dirichlet(np.ones(len(DONORS)))
        synth = float(np.dot(w, donor_pre))
        err = (synth - target_pre) ** 2
        if best is None or err < best[0]:
            best = (err, w)
    sc_weights = best[1]
    sc_post_growth = float(np.dot(sc_weights, [growth_log[c] for c in DONORS]))
    uk_gap_sc = uk_growth - sc_post_growth

    # Debt-target check (2015)
    debt_2015 = None
    if p_debt is not None:
        debt = load_wdi(p_debt)
        debt_2015 = get_year(debt, TREATED, 2015)
    debt_overshoot = (debt_2015 - DEBT_TARGET_2010_FOR_2015) if debt_2015 is not None else None

    primary_output_pass = uk_gap <= GAP_THRESHOLD
    primary_debt_pass = debt_overshoot is not None and debt_overshoot > DEBT_OVERSHOOT_PP
    primary_pass = primary_output_pass and primary_debt_pass

    if primary_pass:
        verdict = (f"SUPPORTED — UK 2009→{GAP_YEAR} log GDP-pc growth = {uk_growth:+.4f}, "
                   f"donor-mean = {donor_mean:+.4f}, gap = {uk_gap:+.4f} log-pts "
                   f"(<= {GAP_THRESHOLD}); 2015 debt/GDP {debt_2015:.1f}% overshoots 2010 "
                   f"target ({DEBT_TARGET_2010_FOR_2015:.1f}%) by {debt_overshoot:+.1f}pp.")
    elif primary_output_pass and not primary_debt_pass:
        verdict = (f"partial — output gap clears (gap = {uk_gap:+.4f}) but debt-target "
                   f"check fails: 2015 debt = {debt_2015}, overshoot = {debt_overshoot}. "
                   f"Half of the dispositive primary holds.")
    elif primary_debt_pass and not primary_output_pass:
        verdict = (f"partial — debt-target check passes ({debt_2015:.1f}% vs target "
                   f"{DEBT_TARGET_2010_FOR_2015:.1f}%, overshoot {debt_overshoot:+.1f}pp) but UK "
                   f"output gap to donor mean = {uk_gap:+.4f} log-pts > {GAP_THRESHOLD} — "
                   f"output did not fall below counterfactual by the threshold.")
    else:
        verdict = (f"refuted — UK 2009→{GAP_YEAR} log GDP-pc growth gap to donor mean = "
                   f"{uk_gap:+.4f} log-pts (above {GAP_THRESHOLD} threshold); 2015 debt "
                   f"overshoot = {debt_overshoot}.")

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "primary_pass": primary_pass,
        "primary_output_pass": primary_output_pass,
        "primary_debt_pass": primary_debt_pass,
        "uk_log_growth_2009_to_2014": uk_growth,
        "donor_mean_log_growth_2009_to_2014": donor_mean,
        "uk_minus_donor_mean_log_gap": uk_gap,
        "gap_threshold_log": GAP_THRESHOLD,
        "synth_control_log_growth": sc_post_growth,
        "uk_minus_sc_log_gap": uk_gap_sc,
        "sc_weights": dict(zip(DONORS, [float(x) for x in sc_weights])),
        "donor_pool_log_growth": {c: growth_log[c] for c in DONORS},
        "debt_2015_pct_gdp": debt_2015,
        "debt_target_2010_for_2015": DEBT_TARGET_2010_FOR_2015,
        "debt_overshoot_pp": debt_overshoot,
        "debt_overshoot_threshold_pp": DEBT_OVERSHOOT_PP,
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str))

    chart = {
        "kind": "result",
        "title": "UK Cameron-Osborne austerity 2010-16: output vs donor counterfactual",
        "series": [
            {"name": "UK log growth 2009→2014", "value": uk_growth},
            {"name": "Donor-mean log growth", "value": donor_mean},
            {"name": "Synth-control log growth", "value": sc_post_growth},
            {"name": "UK gap (donor-mean)", "value": uk_gap},
            {"name": "UK gap (synth-control)", "value": uk_gap_sc},
            {"name": "2015 debt %GDP", "value": debt_2015},
            {"name": "2010 government target for 2015", "value": DEBT_TARGET_2010_FOR_2015},
        ],
        "annotations": [f"PRIMARY: gap <= {GAP_THRESHOLD} AND debt overshoot > {DEBT_OVERSHOOT_PP}pp"],
    }
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2, default=str))

    coef_rows = [
        {"name": "uk_log_growth_2009_2014", "value": uk_growth, "threshold": None},
        {"name": "donor_mean_log_growth", "value": donor_mean, "threshold": None},
        {"name": "uk_minus_donor_mean_gap", "value": uk_gap, "threshold": GAP_THRESHOLD},
        {"name": "synth_control_log_growth", "value": sc_post_growth, "threshold": None},
        {"name": "uk_minus_sc_gap", "value": uk_gap_sc, "threshold": GAP_THRESHOLD},
        {"name": "debt_2015", "value": debt_2015, "threshold": DEBT_TARGET_2010_FOR_2015 + DEBT_OVERSHOOT_PP},
        {"name": "debt_overshoot_pp", "value": debt_overshoot, "threshold": DEBT_OVERSHOOT_PP},
    ]
    pd.DataFrame(coef_rows).to_parquet(RUN_DIR / "coefficients.parquet", index=False)

    def sha256_path(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]

    manifest = {
        "hypothesis_id": HID,
        "vintages": [
            {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD",
             "path": str(p_gdp.relative_to(ROOT)), "sha256_16": sha256_path(p_gdp)},
        ],
    }
    if p_debt is not None:
        manifest["vintages"].append({
            "publisher": "imf", "series": "GGXWDG_NGDP",
            "path": str(p_debt.relative_to(ROOT)), "sha256_16": sha256_path(p_debt),
        })
    import yaml as _yaml
    (RUN_DIR / "manifest.yaml").write_text(_yaml.safe_dump(manifest, sort_keys=False))

    result = (
        f"# UK Cameron-Osborne austerity 2010-16: output and debt path\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Method\n\n"
        f"Two-leg dispositive primary: (1) UK − donor-pool-mean log GDP-pc growth gap "
        f"2009→{GAP_YEAR} <= {GAP_THRESHOLD} log-pts AND (2) 2015 general-government debt "
        f"to GDP exceeds 2010 government target ({DEBT_TARGET_2010_FOR_2015}%) by "
        f"> {DEBT_OVERSHOOT_PP}pp. Both must hold for SUPPORTED. Donor pool: "
        f"{', '.join(DONORS)}. Synth-control weighting included as a robustness check on "
        f"the equal-weighted donor mean.\n\n"
        f"## Numbers\n\n"
        f"- UK log GDP-pc growth 2009→{GAP_YEAR}: {uk_growth:+.4f}\n"
        f"- Donor mean log growth: {donor_mean:+.4f} → UK gap {uk_gap:+.4f}\n"
        f"- Synth-control log growth: {sc_post_growth:+.4f} → UK gap {uk_gap_sc:+.4f}\n"
        f"- SC donor weights: {dict(zip(DONORS, [round(float(x),3) for x in sc_weights]))}\n"
        f"- 2015 UK debt/GDP: {debt_2015}; overshoot vs 2010 target {debt_overshoot}\n\n"
        f"## Caveats\n\n"
        f"- FRA + JPN had their own fiscal consolidations later in the window — biases the "
        f"test toward not finding an austerity effect (conservative for the hypothesis).\n"
        f"- Debt-target value 67% is the OBR June-2010 trajectory midpoint for PSND/GDP at "
        f"FY 2014/15; IMF GGXWDG is a slightly broader measure (general gov gross debt) and "
        f"runs a few pp higher than PSND.\n"
        f"- Synth-control weights are random-search Dirichlet over a 5-donor simplex with "
        f"pre-window 2007-2009 — short pre-window weakens identification.\n"
    )
    (RUN_DIR / "result_card.md").write_text(result)

    print(verdict)


if __name__ == "__main__":
    main()
