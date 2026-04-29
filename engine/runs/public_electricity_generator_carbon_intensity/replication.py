#!/usr/bin/env python3
"""Replication — Public electricity generators (EDF, Vattenfall) vs privatised
counterparts: lower-carbon generation mix, 1970-1999.

Spec: hypotheses/energy/public_electricity_generator_carbon_intensity.yaml v1
Position-claim: eco_socialist #5 (school predicts: supported)

The claim: publicly owned generators (EDF in France pre-privatisation,
Vattenfall Sweden) achieved a lower-carbon generation MIX than otherwise-
matched privatised counterparts over 1970-1999.

The spec's stated test (falsification.test):
> Refute if public-generator carbon intensity not >25% lower than matched
> private comparators in 5-year rolling windows at p<0.10.

PRIMARY (dispositive) — 25% gap rule:
    Mean ratio of public-cohort electricity carbon-intensity proxy to
    private-cohort proxy across the available 1970-1999 window must be
    <= 0.75 (i.e. public is at least 25% lower) for SUPPORT. Ratio in
    [0.75, 1.00) is partial. Ratio >= 1.00 is REFUTED.

OPERATIONAL definition of carbon-intensity proxy:
    Fossil share of electricity (% of generation from coal/gas/oil), via
    OWID-Ember share-electricity-fossil-fuels. Lower fossil share => lower
    grid CO2 intensity, with near-1:1 correlation in this period because
    non-fossil = nuclear + hydro + nascent renewables (gas/coal carbon
    factors dominate variation). This is the publisher-on-disk proxy
    closest to the spec's gCO2/kWh target. The spec's preferred outcome
    (electricity-sector gCO2/kWh from IEA energy balances) requires an
    IEA fetcher that has not shipped.

INFORMATIVE — non-fossil (nuclear + renewables) share gap, and OWID
    co2-intensity (CO2/GDP) gap. Same direction expected.

METHOD_VALID — at least 5 years of OWID-Ember coverage in [1985, 1999]
    for FRA, SWE, AND for at least 4 of the 7 privatised comparators.
    OWID-Ember's electricity-share series begin in 1985, so the 1970-
    1984 portion of the spec's claimed window is structurally
    DATA-GAPPED — the spec's 1970s premise CANNOT be tested with the
    publishers on disk. We test the 1985-1999 sub-window and flag
    1970-1984 explicitly as unmeasured.

COHORTS (per spec.sample.countries):
    Public: FRA (EDF nationalised 1946-2005), SWE (Vattenfall public from 1909)
    Private/Privatised comparators: GBR (privatised 1990), USA (IOU-dominant),
        DEU, ITA, ESP, BEL, NLD

CAVEATS (per spec.disclosure):
    EDF's nuclear-heavy mix and Vattenfall's hydro+nuclear mix were
    largely products of national resource endowments and postwar
    industrial planning, not directly attributable to public-ownership
    status. Even if the 25% gap holds in the data, the causal attribution
    to public ownership is contested. The verdict speaks only to the
    descriptive cross-cohort gap, not to the causal claim.
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
HID = "public_electricity_generator_carbon_intensity"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Cohorts from spec.sample.countries
PUBLIC_COHORT = ["FRA", "SWE"]
PRIVATE_COHORT = ["GBR", "USA", "DEU", "ITA", "ESP", "BEL", "NLD"]
ALL_COUNTRIES = PUBLIC_COHORT + PRIVATE_COHORT

# Spec window: 1970-1999. OWID-Ember begins ~1985 — the pre-1985 sub-window
# is structurally data-gapped on disk.
SPEC_PERIOD = (1970, 1999)
TESTABLE_PERIOD = (1985, 1999)

# Falsification thresholds (from spec.falsification.test, made dispositive)
GAP_THRESHOLD_RATIO = 0.75  # public ≤ 75% of private => SUPPORTED (>=25% lower)
PARTIAL_RATIO_UPPER = 1.00  # public < private but not by 25% => partial
MIN_OVERLAP_YEARS = 5  # method-valid: at least 5 years of overlap data
MIN_PRIVATE_COMPARATORS = 4  # method-valid: at least 4 of 7 private comparators


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
    """Standard normaliser to (country_iso3, year, value)."""
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


def cohort_mean_by_year(df: pd.DataFrame, countries: list[str],
                       y_lo: int, y_hi: int) -> pd.Series:
    """Yearly cross-country mean restricted to the given countries and window."""
    sub = df[
        df["country_iso3"].isin(countries)
        & df["year"].between(y_lo, y_hi)
    ].copy()
    sub["year"] = sub["year"].astype(int)
    return sub.groupby("year")["value"].mean()


def country_coverage(df: pd.DataFrame, countries: list[str],
                    y_lo: int, y_hi: int) -> dict[str, dict]:
    cov = {}
    for c in countries:
        sub = df[
            (df["country_iso3"] == c) & df["year"].between(y_lo, y_hi)
        ]
        years = sorted(sub["year"].astype(int).unique().tolist())
        cov[c] = {
            "n_years": len(years),
            "first_year": years[0] if years else None,
            "last_year": years[-1] if years else None,
        }
    return cov


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fossil_path = latest("owid", "share-electricity-fossil-fuels")
    nuclear_path = latest("owid", "share-electricity-nuclear")
    renew_path = latest("owid", "share-electricity-renewables")
    co2int_path = latest("owid", "co2-intensity")

    manifest = {
        "share_electricity_fossil_fuels": {
            "publisher": "owid",
            "series": "share-electricity-fossil-fuels",
            "vintage_file": str(fossil_path.relative_to(REPO_ROOT)),
            "sha256": sha256(fossil_path),
        },
        "share_electricity_nuclear": {
            "publisher": "owid",
            "series": "share-electricity-nuclear",
            "vintage_file": str(nuclear_path.relative_to(REPO_ROOT)),
            "sha256": sha256(nuclear_path),
        },
        "share_electricity_renewables": {
            "publisher": "owid",
            "series": "share-electricity-renewables",
            "vintage_file": str(renew_path.relative_to(REPO_ROOT)),
            "sha256": sha256(renew_path),
        },
        "co2_intensity": {
            "publisher": "owid",
            "series": "co2-intensity",
            "vintage_file": str(co2int_path.relative_to(REPO_ROOT)),
            "sha256": sha256(co2int_path),
        },
    }

    fossil = load_long(fossil_path)
    nuclear = load_long(nuclear_path)
    renew = load_long(renew_path)
    co2int = load_long(co2int_path)

    # ---------- Coverage diagnostics ----------
    pub_cov = country_coverage(fossil, PUBLIC_COHORT, *TESTABLE_PERIOD)
    priv_cov = country_coverage(fossil, PRIVATE_COHORT, *TESTABLE_PERIOD)

    pub_with_data = [c for c, v in pub_cov.items() if v["n_years"] >= MIN_OVERLAP_YEARS]
    priv_with_data = [c for c, v in priv_cov.items() if v["n_years"] >= MIN_OVERLAP_YEARS]

    method_valid = (
        len(pub_with_data) == len(PUBLIC_COHORT)
        and len(priv_with_data) >= MIN_PRIVATE_COMPARATORS
    )
    method_notes = []
    if len(pub_with_data) < len(PUBLIC_COHORT):
        missing_pub = [c for c in PUBLIC_COHORT if c not in pub_with_data]
        method_notes.append(f"public cohort missing OWID coverage: {missing_pub}")
    if len(priv_with_data) < MIN_PRIVATE_COMPARATORS:
        method_notes.append(
            f"only {len(priv_with_data)}/{MIN_PRIVATE_COMPARATORS} private "
            f"comparators have ≥{MIN_OVERLAP_YEARS} years of OWID coverage"
        )

    # The 1970-1984 sub-window is structurally data-gapped — flag explicitly.
    pre_owid_window = [SPEC_PERIOD[0], TESTABLE_PERIOD[0] - 1]
    pre_owid_gap_years = pre_owid_window[1] - pre_owid_window[0] + 1
    spec_window_years = SPEC_PERIOD[1] - SPEC_PERIOD[0] + 1
    pre_owid_gap_share = pre_owid_gap_years / spec_window_years

    # ---------- PRIMARY: fossil-share gap, 1985-1999 ----------
    pub_fossil = cohort_mean_by_year(fossil, pub_with_data, *TESTABLE_PERIOD)
    priv_fossil = cohort_mean_by_year(fossil, priv_with_data, *TESTABLE_PERIOD)

    overlap_years = sorted(set(pub_fossil.index) & set(priv_fossil.index))
    if not overlap_years:
        method_valid = False
        method_notes.append("zero overlap years between cohorts in 1985-1999")

    pub_fossil_mean = float(pub_fossil.loc[overlap_years].mean()) if overlap_years else float("nan")
    priv_fossil_mean = float(priv_fossil.loc[overlap_years].mean()) if overlap_years else float("nan")
    fossil_ratio = (
        pub_fossil_mean / priv_fossil_mean
        if priv_fossil_mean and not np.isnan(priv_fossil_mean) and priv_fossil_mean > 0
        else float("nan")
    )

    # 5-year rolling means (per spec.falsification.test) — descriptive support
    rolling_table = []
    if overlap_years:
        for end_y in range(overlap_years[0] + 4, overlap_years[-1] + 1):
            window = list(range(end_y - 4, end_y + 1))
            wpub = pub_fossil.reindex(window).dropna()
            wpriv = priv_fossil.reindex(window).dropna()
            if len(wpub) >= 3 and len(wpriv) >= 3:
                rolling_table.append({
                    "window_end": end_y,
                    "pub_fossil_share": float(wpub.mean()),
                    "priv_fossil_share": float(wpriv.mean()),
                    "ratio": float(wpub.mean() / wpriv.mean()) if wpriv.mean() > 0 else None,
                })

    # ---------- INFORMATIVE: non-fossil share gap, co2-intensity gap ----------
    pub_nuc = cohort_mean_by_year(nuclear, pub_with_data, *TESTABLE_PERIOD)
    priv_nuc = cohort_mean_by_year(nuclear, priv_with_data, *TESTABLE_PERIOD)
    pub_ren = cohort_mean_by_year(renew, pub_with_data, *TESTABLE_PERIOD)
    priv_ren = cohort_mean_by_year(renew, priv_with_data, *TESTABLE_PERIOD)

    pub_nonfossil_mean = (
        float((pub_nuc + pub_ren).loc[overlap_years].mean()) if overlap_years else float("nan")
    )
    priv_nonfossil_mean = (
        float((priv_nuc + priv_ren).loc[overlap_years].mean()) if overlap_years else float("nan")
    )
    nonfossil_gap_pp = pub_nonfossil_mean - priv_nonfossil_mean

    pub_co2int = cohort_mean_by_year(co2int, pub_with_data, *TESTABLE_PERIOD)
    priv_co2int = cohort_mean_by_year(co2int, priv_with_data, *TESTABLE_PERIOD)
    co2int_overlap = sorted(set(pub_co2int.index) & set(priv_co2int.index))
    pub_co2int_mean = float(pub_co2int.loc[co2int_overlap].mean()) if co2int_overlap else float("nan")
    priv_co2int_mean = float(priv_co2int.loc[co2int_overlap].mean()) if co2int_overlap else float("nan")
    co2int_ratio = (
        pub_co2int_mean / priv_co2int_mean
        if priv_co2int_mean and not np.isnan(priv_co2int_mean) and priv_co2int_mean > 0
        else float("nan")
    )

    # ---------- Verdict ----------
    if not method_valid:
        verdict_word = "inconclusive"
        verdict = (
            f"inconclusive — Method validity failed: "
            f"{'; '.join(method_notes)}. The spec window is "
            f"{SPEC_PERIOD[0]}-{SPEC_PERIOD[1]}; OWID-Ember electricity-share "
            f"series only begin in 1985, so the 1970-1984 sub-window "
            f"({pre_owid_gap_years} years, {pre_owid_gap_share*100:.0f}% of "
            f"spec window) is structurally data-gapped. The IEA energy-"
            f"balance fetcher needed for the spec's preferred 1970s "
            f"gCO2/kWh outcome has not shipped."
        )
    else:
        # Even when method-valid on the testable sub-window, the structural
        # 1970-1984 gap remains. Verdict speaks to the testable 1985-1999
        # sub-window only.
        if fossil_ratio <= GAP_THRESHOLD_RATIO:
            verdict_word = "SUPPORTED"
            verdict = (
                f"SUPPORTED — Public cohort (FRA, SWE) fossil share averaged "
                f"{pub_fossil_mean:.1f}% vs private cohort (GBR, USA, DEU, "
                f"ITA, ESP, BEL, NLD: {len(priv_with_data)} with data) "
                f"{priv_fossil_mean:.1f}% over {overlap_years[0]}-"
                f"{overlap_years[-1]}; ratio {fossil_ratio:.2f} ≤ "
                f"{GAP_THRESHOLD_RATIO} threshold (≥25% lower). Non-fossil "
                f"share gap: {nonfossil_gap_pp:+.1f}pp (public higher). "
                f"NOTE: 1970-1984 sub-window of the spec ({pre_owid_gap_years}/"
                f"{spec_window_years} years) is data-gapped on OWID-Ember; "
                f"verdict is on the 1985-1999 sub-window only. Causal "
                f"attribution to public ownership is contested per the "
                f"spec's own disclosure (resource endowments + postwar "
                f"planning are correlated)."
            )
        elif fossil_ratio < PARTIAL_RATIO_UPPER:
            verdict_word = "partial"
            gap_pct = (1 - fossil_ratio) * 100
            verdict = (
                f"partial — Public cohort fossil share is "
                f"{gap_pct:.0f}% lower than private cohort over "
                f"{overlap_years[0]}-{overlap_years[-1]} "
                f"({pub_fossil_mean:.1f}% vs {priv_fossil_mean:.1f}%, "
                f"ratio {fossil_ratio:.2f}), correct direction but does "
                f"not clear the 25% threshold ({GAP_THRESHOLD_RATIO} "
                f"ratio). Non-fossil share gap: {nonfossil_gap_pp:+.1f}pp. "
                f"NOTE: 1970-1984 spec sub-window is data-gapped."
            )
        else:
            verdict_word = "refuted"
            verdict = (
                f"refuted — Public cohort fossil share "
                f"({pub_fossil_mean:.1f}%) is not lower than private "
                f"cohort ({priv_fossil_mean:.1f}%) over "
                f"{overlap_years[0]}-{overlap_years[-1]} "
                f"(ratio {fossil_ratio:.2f} ≥ 1.00). The descriptive "
                f"premise of the eco-socialist claim does not hold on "
                f"the testable 1985-1999 sub-window."
            )

    diagnostics = {
        "verdict": verdict,
        "verdict_word": verdict_word,
        "method_valid": method_valid,
        "method_notes": method_notes,
        "spec_period": list(SPEC_PERIOD),
        "testable_period": list(TESTABLE_PERIOD),
        "pre_owid_data_gap_years": pre_owid_gap_years,
        "pre_owid_data_gap_share_of_spec": pre_owid_gap_share,
        "public_cohort": PUBLIC_COHORT,
        "private_cohort": PRIVATE_COHORT,
        "public_with_data": pub_with_data,
        "private_with_data": priv_with_data,
        "public_coverage": pub_cov,
        "private_coverage": priv_cov,
        "primary": {
            "name": "fossil_share_ratio_public_over_private",
            "public_fossil_share_mean": pub_fossil_mean,
            "private_fossil_share_mean": priv_fossil_mean,
            "ratio": fossil_ratio,
            "threshold_supported": GAP_THRESHOLD_RATIO,
            "threshold_partial_upper": PARTIAL_RATIO_UPPER,
            "overlap_years": overlap_years,
        },
        "informative": {
            "non_fossil_share_gap_pp": nonfossil_gap_pp,
            "public_non_fossil_share_mean": pub_nonfossil_mean,
            "private_non_fossil_share_mean": priv_nonfossil_mean,
            "co2_intensity_ratio": co2int_ratio,
            "public_co2_intensity_mean": pub_co2int_mean,
            "private_co2_intensity_mean": priv_co2int_mean,
        },
        "rolling_5yr_table": rolling_table,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=str) + "\n"
    )

    # ---------- Chart ----------
    palette_public = ["#4E79A7", "#59A14F"]   # cool — public
    palette_private = ["#E15759", "#F28E2B", "#B07AA1", "#EDC948", "#76B7B2", "#9C755F", "#B6992D"]

    series = []
    for i, c in enumerate(PUBLIC_COHORT):
        sub = fossil[
            (fossil["country_iso3"] == c)
            & fossil["year"].between(*TESTABLE_PERIOD)
        ].sort_values("year")
        if sub.empty:
            continue
        pts = [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]
        series.append({
            "id": c,
            "label": f"{c} (public)",
            "color": palette_public[i % len(palette_public)],
            "treated": True,
            "points": pts,
        })
    for i, c in enumerate(PRIVATE_COHORT):
        sub = fossil[
            (fossil["country_iso3"] == c)
            & fossil["year"].between(*TESTABLE_PERIOD)
        ].sort_values("year")
        if sub.empty:
            continue
        pts = [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]
        series.append({
            "id": c,
            "label": f"{c} (private/privatised)",
            "color": palette_private[i % len(palette_private)],
            "treated": False,
            "points": pts,
        })

    subtitle = (
        f"Public cohort {pub_fossil_mean:.1f}% vs private cohort "
        f"{priv_fossil_mean:.1f}% mean fossil share, {overlap_years[0] if overlap_years else '—'}-"
        f"{overlap_years[-1] if overlap_years else '—'}; ratio {fossil_ratio:.2f} "
        f"(threshold {GAP_THRESHOLD_RATIO} for SUPPORT). 1970-1984 sub-window "
        f"({pre_owid_gap_years} yrs) data-gapped on OWID-Ember."
        if overlap_years
        else
        "1970-1984 spec sub-window data-gapped on OWID-Ember; "
        "1985-1999 sub-window method-validity failed."
    )

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Fossil share of electricity — public (FRA, SWE) vs privatised counterparts",
        "subtitle": subtitle,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Fossil share of electricity (%)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Verdict: {verdict_word}. Spec window 1970-1999; "
                    f"OWID-Ember coverage starts 1985 → 1970-1984 unmeasured. "
                    f"Public-cohort proxy = fossil share (lower = lower-carbon mix)."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients ----------
    coef_rows = [
        {"spec": "primary", "term": "public_fossil_share_pct", "estimate": pub_fossil_mean},
        {"spec": "primary", "term": "private_fossil_share_pct", "estimate": priv_fossil_mean},
        {"spec": "primary", "term": "fossil_share_ratio_pub_over_priv", "estimate": fossil_ratio},
        {"spec": "primary", "term": "threshold_supported_ratio", "estimate": float(GAP_THRESHOLD_RATIO)},
        {"spec": "informative", "term": "non_fossil_share_gap_pp", "estimate": nonfossil_gap_pp},
        {"spec": "informative", "term": "public_non_fossil_share_pct", "estimate": pub_nonfossil_mean},
        {"spec": "informative", "term": "private_non_fossil_share_pct", "estimate": priv_nonfossil_mean},
        {"spec": "informative", "term": "co2_intensity_ratio_pub_over_priv", "estimate": co2int_ratio},
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
        f"# Public electricity generators — lower-carbon mix vs privatised, 1970-1999",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Spec window: {SPEC_PERIOD[0]}–{SPEC_PERIOD[1]}. Public cohort: "
        f"FRA (EDF, nationalised 1946–2005) and SWE (Vattenfall, public from 1909). "
        f"Private/privatised comparators: GBR, USA, DEU, ITA, ESP, BEL, NLD.",
        f"- **Structural data gap:** OWID-Ember electricity-share series begin "
        f"in 1985. The 1970–1984 sub-window ({pre_owid_gap_years} years, "
        f"{pre_owid_gap_share*100:.0f}% of the spec's 30-year window) cannot be "
        f"tested with publishers on disk. The IEA energy-balance fetcher needed "
        f"for the spec's preferred gCO2/kWh outcome has not shipped.",
        f"- **Testable sub-window 1985–1999:** Public cohort mean fossil share "
        f"= **{pub_fossil_mean:.1f}%**; private cohort (with data: "
        f"{', '.join(priv_with_data)}) mean fossil share = "
        f"**{priv_fossil_mean:.1f}%**.",
        f"- Ratio public/private = **{fossil_ratio:.2f}**. Spec's 25%-lower "
        f"threshold corresponds to ratio ≤ {GAP_THRESHOLD_RATIO}.",
        f"- Informative: public-cohort non-fossil (nuclear + renewables) share "
        f"is **{nonfossil_gap_pp:+.1f}pp** higher than private cohort. "
        f"OWID CO2-intensity-of-GDP ratio public/private = {co2int_ratio:.2f}.",
        "",
        "## Method",
        "",
        f"**Primary statistic:** ratio of public-cohort mean fossil share of "
        f"electricity to private-cohort mean fossil share, averaged across "
        f"overlap years in 1985–1999.",
        "",
        f"**Threshold map:**",
        f"- ratio ≤ {GAP_THRESHOLD_RATIO} → SUPPORTED (≥25% lower)",
        f"- {GAP_THRESHOLD_RATIO} < ratio < {PARTIAL_RATIO_UPPER} → partial",
        f"- ratio ≥ {PARTIAL_RATIO_UPPER} → refuted",
        "",
        f"**Method validity gate:** at least {MIN_OVERLAP_YEARS} years of OWID "
        f"coverage in 1985-1999 for both public-cohort countries AND for at "
        f"least {MIN_PRIVATE_COMPARATORS} of {len(PRIVATE_COHORT)} private "
        f"comparators. {'PASSED' if method_valid else 'FAILED'}: "
        f"public {len(pub_with_data)}/{len(PUBLIC_COHORT)}, "
        f"private {len(priv_with_data)}/{len(PRIVATE_COHORT)}.",
        "",
        "**Why fossil share, not gCO2/kWh?** The spec's preferred outcome is "
        "electricity-sector CO2 intensity (gCO2/kWh) from IEA energy "
        "balances. That fetcher has not shipped. OWID-Ember "
        "share-electricity-fossil-fuels is the closest publisher-on-disk "
        "proxy: lower fossil share => lower grid CO2 intensity, with "
        "near-1:1 ranking in this period because non-fossil = nuclear + "
        "hydro + nascent renewables (gas/coal carbon factors dominate). "
        "Reported alongside is OWID co2-intensity (CO2/GDP) for context.",
        "",
        "## Data",
        "",
        "- owid:share-electricity-fossil-fuels (Ember-derived; primary outcome proxy)",
        "- owid:share-electricity-nuclear (Ember-derived; informative)",
        "- owid:share-electricity-renewables (Ember-derived; informative)",
        "- owid:co2-intensity (informative — CO2/GDP, not electricity-specific)",
        "",
        "## Caveats",
        "",
        "- **Causal attribution is contested** even if the descriptive gap "
        "holds. Per the spec's own disclosure: EDF's nuclear-heavy mix and "
        "Vattenfall's hydro+nuclear mix were largely the products of "
        "national resource endowments (Sweden's hydro; France's uranium-"
        "policy-driven Messmer plan from 1973) and postwar industrial "
        "planning, not cleanly attributable to public-ownership status.",
        "- **Matched-private comparators are scarce.** The 'private' cohort "
        "mixes IOU-dominant USA (regulated monopolies, not market-disciplined) "
        "with continental utilities that were variously state-owned, "
        "municipally owned, or only privatised mid-window (GBR 1990; ITA "
        "ENEL partial 1992; ESP partial 1990s).",
        "- **1970–1984 unmeasured.** The spec's claim explicitly covers the "
        f"1970s; the structural data gap means the verdict above can only "
        f"speak to the {TESTABLE_PERIOD[0]}-{TESTABLE_PERIOD[1]} window. A v2 "
        f"using the IEA energy-balance fetcher could close this gap.",
        "- **No statistical inference.** The spec calls for p<0.10 in 5-year "
        "rolling windows; with N=2 public countries the conventional t-test "
        "is degenerate, so we report descriptive ratios and rolling-window "
        "diagnostics instead. See diagnostics.json's `rolling_5yr_table`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
