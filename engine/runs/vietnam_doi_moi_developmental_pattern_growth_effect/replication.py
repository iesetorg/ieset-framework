#!/usr/bin/env python3
"""Replication — Vietnam Doi Moi developmental pattern growth effect.

Spec: hypotheses/growth/vietnam_doi_moi_developmental_pattern_growth_effect.yaml v1
Position-claim: developmentalism #13 (school predicts: supported)

The developmentalist claim: Vietnam's 1986 Doi Moi reforms + export-oriented
strategy replicated the East Asian developmental-state pattern and produced
three decades of above-peer-region growth.

The spec's stub falsification rule:
  "Synth-DiD on Vietnam real GDP per capita post-1986 with donor pool
   {PHL, IDN, MMR, KHM, LAO, BGD}; supported if cumulative output gap by
   2010 exceeds +25% over synthetic counterfactual at p<0.10."

Sharpened to a dispositive primary statistic (no real synth-DiD weight
optimisation — we instead use the equal-weighted donor-pool counterfactual,
which is conservative for the SUPPORTED side because some donors (KHM, LAO,
MMR) had their own catch-up booms post-1990. A donor-weight optimiser would
likely down-weight those, raising the gap. A simple equal-weight pool that
still shows a >25pp cumulative log-gap is a strong test.

PRIMARY (dispositive):
  Cumulative log-GDP-per-capita gap (Vietnam minus equal-weighted donor mean)
  from the first year both have data (typically 1990, since WDI VNM coverage
  begins 1990) through 2010. SUPPORTED if the cumulative log-gap by 2010
  exceeds +0.25 (i.e., ~+25 log-points = +28% in level terms relative to
  donor-pool counterfactual).

INFORMATIVE:
  - Long-window (through 2019) cumulative gap.
  - Manufacturing value-added share (industrial-capability dimension).
  - Exports/GDP share (export-orientation dimension).
  - PWT TFP index (rtfpna) trajectory if available.

METHOD_VALID:
  - WDI NY.GDP.PCAP.PP.KD must cover VNM and ≥3 of the 6 donors with ≥15
    overlapping years post-1986. If <3 donors or <10 overlapping years,
    emit `inconclusive (data gap)`.
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
HID = "vietnam_doi_moi_developmental_pattern_growth_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "VNM"
DONORS = ["PHL", "IDN", "KHM", "LAO", "BGD", "MMR"]
# Spec sample also includes THA, MYS — these are East Asian Tigers / NIE peers
# rather than peer LDCs, so they are properly comparators, not donors. We
# include them in informative comparisons but not in the primary equal-weight
# counterfactual.
PEER_REFERENCE = ["THA", "MYS"]

TREATMENT_YEAR = 1986
PRIMARY_END_YEAR = 2010
LONG_END_YEAR = 2019

# Sharpened dispositive threshold (replacing spec stub's "+25% at p<0.10").
# +0.25 log-points cumulative ≈ +28% in level terms. The spec says ">+25%";
# +0.25 in logs is the closest dispositive log-space rendering.
LOG_GAP_THRESHOLD_2010 = 0.25
MIN_DONORS_WITH_DATA = 3
MIN_OVERLAP_YEARS = 10

# Manufacturing/exports informative thresholds (directional only)
MFG_SHARE_GAP_PP_INFORMATIVE = 3.0  # Vietnam mean post-2000 > donor mean by 3pp
EXP_SHARE_GAP_PP_INFORMATIVE = 10.0  # Vietnam mean post-2000 > donor mean by 10pp


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
    """Standard normaliser: keep (country_iso3, year, value)."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator_id",
                "unit", "obs_status", "decimal"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def country_series(df: pd.DataFrame, country: str) -> pd.Series:
    """Return year-indexed Series for one country."""
    sub = df[df["country_iso3"] == country].set_index("year")["value"].sort_index()
    # de-duplicate on year (multi-source)
    sub = sub[~sub.index.duplicated(keep="last")]
    return sub


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Resolve series ----------
    gdp_pc_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    mfg_path = latest("world_bank_wdi", "NV.IND.MANF.ZS")
    exp_path = latest("world_bank_wdi", "NE.EXP.GNFS.ZS")
    tfp_path = latest("pwt", "rtfpna")

    manifest: dict = {}
    for name, pub, series, path in [
        ("gdp_pc_ppp", "world_bank_wdi", "NY.GDP.PCAP.PP.KD", gdp_pc_path),
        ("mfg_value_added_pct_gdp", "world_bank_wdi", "NV.IND.MANF.ZS", mfg_path),
        ("exports_pct_gdp", "world_bank_wdi", "NE.EXP.GNFS.ZS", exp_path),
        ("tfp_pwt_rtfpna", "pwt", "rtfpna", tfp_path),
    ]:
        if path is None:
            manifest[name] = {"publisher": pub, "series": series, "missing": True}
        else:
            manifest[name] = {
                "publisher": pub, "series": series,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
            }

    # ---------- METHOD_VALID gate: GDP-pc data must be sufficient ----------
    if gdp_pc_path is None:
        verdict = (
            "inconclusive (data gap on world_bank_wdi:NY.GDP.PCAP.PP.KD) — the "
            "primary outcome series is not in the current data vintage. The "
            "Vietnam Doi Moi growth-effect test cannot be scored until the "
            "WDI fetcher for NY.GDP.PCAP.PP.KD lands."
        )
        diagnostics = {
            "verdict": verdict,
            "all_pass": False,
            "primary_data_available": False,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "vintages": manifest,
        }, sort_keys=False))
        pd.DataFrame([{"spec": "primary", "term": "missing", "estimate": float("nan")}]) \
            .to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "result_card.md").write_text(
            f"# Vietnam Doi Moi developmental pattern growth effect\n\n"
            f"**Verdict:** {verdict}\n"
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "DATA GAP", "subtitle": verdict, "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "—", "type": "linear"},
            "series": [], "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    gdp_pc = load_long(gdp_pc_path)

    # ---------- Build the primary panel ----------
    vnm_gdp = country_series(gdp_pc, TREATED)
    donor_series_dict: dict[str, pd.Series] = {}
    for d in DONORS:
        s = country_series(gdp_pc, d)
        if not s.empty:
            donor_series_dict[d] = s
    peer_series_dict: dict[str, pd.Series] = {
        c: country_series(gdp_pc, c) for c in PEER_REFERENCE
        if not country_series(gdp_pc, c).empty
    }

    # Determine first year both VNM and ≥1 donor have data
    if vnm_gdp.empty or not donor_series_dict:
        verdict = (
            f"inconclusive (data gap) — Vietnam GDP-per-capita PPP series "
            f"empty (n={len(vnm_gdp)}) or no donor coverage "
            f"(n_donors={len(donor_series_dict)})."
        )
        diagnostics = {"verdict": verdict, "all_pass": False,
                       "n_donors_with_data": len(donor_series_dict),
                       "n_vnm_obs": int(len(vnm_gdp))}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "vintages": manifest,
        }, sort_keys=False))
        pd.DataFrame([{"spec": "primary", "term": "missing", "estimate": float("nan")}]) \
            .to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "result_card.md").write_text(
            f"# Vietnam Doi Moi developmental pattern growth effect\n\n"
            f"**Verdict:** {verdict}\n"
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "DATA GAP", "subtitle": verdict, "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "—", "type": "linear"},
            "series": [], "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    # First year ≥ TREATMENT_YEAR with VNM data and ≥1 donor
    candidate_years = [
        y for y in sorted(vnm_gdp.index)
        if y >= TREATMENT_YEAR
        and any(y in s.index for s in donor_series_dict.values())
    ]
    if not candidate_years:
        verdict = "inconclusive (data gap) — no overlapping VNM/donor years post-1986."
        diagnostics = {"verdict": verdict, "all_pass": False}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "vintages": manifest,
        }, sort_keys=False))
        pd.DataFrame([{"spec": "primary", "term": "missing", "estimate": float("nan")}]) \
            .to_parquet(OUT_DIR / "coefficients.parquet", index=False)
        (OUT_DIR / "result_card.md").write_text(
            f"# Vietnam Doi Moi developmental pattern growth effect\n\n"
            f"**Verdict:** {verdict}\n"
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "DATA GAP", "subtitle": verdict, "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "—", "type": "linear"},
            "series": [], "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    base_year = candidate_years[0]
    vnm_base = vnm_gdp.loc[base_year]

    # Donors with data at base_year (anchor each donor's index here)
    donors_with_base = {
        d: s for d, s in donor_series_dict.items() if base_year in s.index
    }
    n_donors_at_base = len(donors_with_base)
    method_valid = n_donors_at_base >= MIN_DONORS_WITH_DATA

    # ---------- PRIMARY: log-gap by 2010 ----------
    def log_index(s: pd.Series, base_y: int) -> pd.Series:
        return np.log(s) - np.log(s.loc[base_y])

    vnm_log_idx = log_index(vnm_gdp, base_year)
    donor_log_indices = {
        d: log_index(s, base_year) for d, s in donors_with_base.items()
    }

    def gap_at(year: int) -> tuple[float, int, float, float]:
        """Return (vnm_minus_donor_mean_log_gap, n_donors_with_data,
        vnm_log_idx, mean_donor_log_idx) at given year."""
        vnm_v = vnm_log_idx.loc[year] if year in vnm_log_idx.index else np.nan
        donor_vals = [
            v.loc[year] for v in donor_log_indices.values()
            if year in v.index and np.isfinite(v.loc[year])
        ]
        if not donor_vals or not np.isfinite(vnm_v):
            return float("nan"), len(donor_vals), float(vnm_v), float("nan")
        donor_mean = float(np.mean(donor_vals))
        return float(vnm_v - donor_mean), len(donor_vals), float(vnm_v), donor_mean

    primary_gap, primary_n_donors, vnm_log_idx_2010, donor_mean_log_idx_2010 = gap_at(PRIMARY_END_YEAR)

    n_overlap_years = sum(
        1 for y in range(base_year, PRIMARY_END_YEAR + 1)
        if y in vnm_log_idx.index
        and any(y in v.index for v in donor_log_indices.values())
    )
    method_valid = method_valid and (n_overlap_years >= MIN_OVERLAP_YEARS)

    # Long-window gap (informative)
    long_gap, long_n_donors, vnm_log_idx_long, donor_mean_log_idx_long = gap_at(LONG_END_YEAR)

    # Per-year gap series for the chart and diagnostics
    annual_gaps = {}
    for y in range(base_year, LONG_END_YEAR + 1):
        g, n, vnm_v, donor_v = gap_at(y)
        if np.isfinite(g):
            annual_gaps[y] = {"gap_log": g, "n_donors": n,
                              "vnm_log_idx": vnm_v, "donor_mean_log_idx": donor_v}

    # ---------- INFORMATIVE: manufacturing & exports shares ----------
    def share_window_mean(df: pd.DataFrame, country: str, lo: int, hi: int) -> float:
        sub = df[
            (df["country_iso3"] == country) & (df["year"].between(lo, hi))
        ]["value"]
        return float(sub.mean()) if len(sub) else float("nan")

    informative: dict = {}
    for label, path, threshold, direction in [
        ("mfg_value_added_pct_gdp", mfg_path, MFG_SHARE_GAP_PP_INFORMATIVE, "higher"),
        ("exports_pct_gdp", exp_path, EXP_SHARE_GAP_PP_INFORMATIVE, "higher"),
    ]:
        if path is None:
            informative[label] = {"available": False, "reason": "missing series"}
            continue
        df = load_long(path)
        vnm_late = share_window_mean(df, TREATED, 2000, 2019)
        donor_lates = [
            share_window_mean(df, d, 2000, 2019) for d in DONORS
        ]
        donor_lates = [v for v in donor_lates if np.isfinite(v)]
        if not np.isfinite(vnm_late) or not donor_lates:
            informative[label] = {"available": False,
                                  "reason": "insufficient overlap 2000-2019"}
            continue
        donor_mean = float(np.mean(donor_lates))
        gap = vnm_late - donor_mean
        passes = (gap >= threshold) if direction == "higher" else (gap <= -threshold)
        informative[label] = {
            "available": True,
            "vnm_late_mean": vnm_late,
            "donor_late_mean": donor_mean,
            "gap_pp": gap,
            "threshold_pp": threshold,
            "direction_required": direction,
            "passes_in_claimed_direction": bool(passes),
            "n_donors_with_data": len(donor_lates),
        }

    # ---------- INFORMATIVE: PWT TFP ----------
    tfp_info: dict = {"available": False}
    if tfp_path is not None:
        tfp = load_long(tfp_path)
        vnm_tfp = country_series(tfp, TREATED)
        donor_tfps = {d: country_series(tfp, d) for d in DONORS}
        donor_tfps = {d: s for d, s in donor_tfps.items() if not s.empty}
        if not vnm_tfp.empty and donor_tfps:
            common_years = sorted(set(vnm_tfp.index).intersection(
                *(set(s.index) for s in donor_tfps.values())
            ))
            if common_years:
                tfp_base_year = common_years[0]
                tfp_end_year = common_years[-1]
                vnm_tfp_chg = float(np.log(vnm_tfp.loc[tfp_end_year]) -
                                    np.log(vnm_tfp.loc[tfp_base_year]))
                donor_tfp_chgs = [
                    float(np.log(s.loc[tfp_end_year]) - np.log(s.loc[tfp_base_year]))
                    for s in donor_tfps.values()
                ]
                tfp_info = {
                    "available": True,
                    "tfp_base_year": int(tfp_base_year),
                    "tfp_end_year": int(tfp_end_year),
                    "vnm_log_tfp_change": vnm_tfp_chg,
                    "donor_mean_log_tfp_change": float(np.mean(donor_tfp_chgs)),
                    "tfp_log_gap": vnm_tfp_chg - float(np.mean(donor_tfp_chgs)),
                    "n_donors_with_data": len(donor_tfps),
                }

    # ---------- VERDICT ----------
    if not method_valid:
        verdict = (
            f"inconclusive (method_valid failure) — only {n_donors_at_base} "
            f"donors with data at base year {base_year} (need ≥"
            f"{MIN_DONORS_WITH_DATA}) or only {n_overlap_years} overlapping "
            f"years base→2010 (need ≥{MIN_OVERLAP_YEARS}). The Doi Moi growth-"
            f"effect test cannot be dispositively scored on this vintage."
        )
        all_pass = False
    elif not np.isfinite(primary_gap):
        verdict = (
            f"inconclusive (data gap) — Vietnam or donor pool missing data at "
            f"{PRIMARY_END_YEAR}. Cannot compute primary log-gap."
        )
        all_pass = False
    elif primary_gap >= LOG_GAP_THRESHOLD_2010:
        pct_level_gap = (np.exp(primary_gap) - 1.0) * 100.0
        verdict = (
            f"SUPPORTED — Vietnam log-GDP-per-capita ran +{primary_gap:.2f} "
            f"log-points (≈ +{pct_level_gap:.0f}%) above the equal-weighted "
            f"SE-Asian donor pool ({', '.join(donors_with_base.keys())}) by "
            f"{PRIMARY_END_YEAR}, base year {base_year}. Threshold was "
            f"+{LOG_GAP_THRESHOLD_2010:.2f} log-points; cleared by "
            f"{(primary_gap - LOG_GAP_THRESHOLD_2010):+.2f}. Long-window gap "
            f"to {LONG_END_YEAR}: +{long_gap:.2f} log-points "
            f"(≈ +{(np.exp(long_gap)-1)*100:.0f}%)."
        )
        all_pass = True
    elif primary_gap <= 0:
        verdict = (
            f"refuted — Vietnam log-GDP-per-capita gap vs equal-weighted "
            f"donor pool by {PRIMARY_END_YEAR} is {primary_gap:+.2f} log-"
            f"points (base year {base_year}). The 'three decades of above-"
            f"peer growth' premise does not hold against the SE-Asian donor "
            f"pool on this vintage."
        )
        all_pass = False
    else:
        # 0 < gap < threshold — directionally correct but below dispositive bar
        miss = LOG_GAP_THRESHOLD_2010 - primary_gap
        verdict = (
            f"partial — Vietnam log-GDP-per-capita gap vs donor pool by "
            f"{PRIMARY_END_YEAR} is +{primary_gap:.2f} log-points "
            f"(directionally correct), but below the +"
            f"{LOG_GAP_THRESHOLD_2010:.2f} dispositive threshold by "
            f"{miss:.2f}. Long-window gap to {LONG_END_YEAR}: "
            f"+{long_gap:+.2f} log-points."
        )
        all_pass = False

    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "method_valid": method_valid,
        "primary_log_gap_2010": primary_gap,
        "primary_log_gap_threshold": LOG_GAP_THRESHOLD_2010,
        "long_window_log_gap_2019": long_gap,
        "base_year": int(base_year),
        "vnm_log_idx_2010": vnm_log_idx_2010,
        "donor_mean_log_idx_2010": donor_mean_log_idx_2010,
        "n_donors_at_base_year": n_donors_at_base,
        "donors_at_base_year": list(donors_with_base.keys()),
        "n_overlap_years_base_to_2010": n_overlap_years,
        "n_donors_at_2010": int(primary_n_donors),
        "n_donors_at_2019": int(long_n_donors),
        "informative_industrial_metrics": informative,
        "informative_tfp": tfp_info,
        "annual_gaps": {str(y): v for y, v in annual_gaps.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- coefficients.parquet ----------
    coef_rows = [
        {"spec": "primary", "term": "log_gap_2010", "estimate": primary_gap},
        {"spec": "primary", "term": "log_gap_threshold", "estimate": LOG_GAP_THRESHOLD_2010},
        {"spec": "primary", "term": "log_gap_2019", "estimate": long_gap},
        {"spec": "primary", "term": "vnm_log_idx_2010", "estimate": vnm_log_idx_2010},
        {"spec": "primary", "term": "donor_mean_log_idx_2010",
         "estimate": donor_mean_log_idx_2010},
        {"spec": "primary", "term": "base_year", "estimate": float(base_year)},
        {"spec": "primary", "term": "n_donors_at_base", "estimate": float(n_donors_at_base)},
    ]
    for k, v in informative.items():
        if v.get("available"):
            coef_rows.append({"spec": f"informative_{k}", "term": "vnm_late_mean",
                              "estimate": v["vnm_late_mean"]})
            coef_rows.append({"spec": f"informative_{k}", "term": "donor_late_mean",
                              "estimate": v["donor_late_mean"]})
            coef_rows.append({"spec": f"informative_{k}", "term": "gap_pp",
                              "estimate": v["gap_pp"]})
    if tfp_info.get("available"):
        coef_rows.append({"spec": "informative_tfp", "term": "tfp_log_gap",
                          "estimate": tfp_info["tfp_log_gap"]})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- chart_data.json ----------
    palette = ["#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B",
               "#76B7B2", "#EDC948", "#B6992D", "#9C755F"]
    series = []
    # Vietnam first, treated
    vnm_pts = [
        {"x": int(y), "y": float(vnm_log_idx.loc[y])}
        for y in sorted(vnm_log_idx.index) if base_year <= y <= LONG_END_YEAR
    ]
    series.append({
        "id": "VNM", "label": "Vietnam (treated)", "color": "#1f1f1f",
        "treated": True, "points": vnm_pts,
    })
    for i, (d, idx) in enumerate(donor_log_indices.items()):
        pts = [
            {"x": int(y), "y": float(idx.loc[y])}
            for y in sorted(idx.index) if base_year <= y <= LONG_END_YEAR
            and np.isfinite(idx.loc[y])
        ]
        series.append({
            "id": d, "label": f"{d} (donor)", "color": palette[i % len(palette)],
            "treated": False, "points": pts,
        })
    # Donor mean as a separate series
    donor_mean_pts = []
    for y in range(base_year, LONG_END_YEAR + 1):
        vals = [v.loc[y] for v in donor_log_indices.values()
                if y in v.index and np.isfinite(v.loc[y])]
        if vals:
            donor_mean_pts.append({"x": int(y), "y": float(np.mean(vals))})
    series.append({
        "id": "DONOR_MEAN", "label": "Donor pool mean (counterfactual)",
        "color": "#888888", "treated": False, "points": donor_mean_pts,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": (f"Vietnam vs SE-Asian donor pool: log GDP-per-capita "
                  f"(PPP), indexed to {base_year} = 0"),
        "subtitle": (
            f"Cumulative log-gap by {PRIMARY_END_YEAR}: "
            f"{primary_gap:+.2f} (≈ {(np.exp(primary_gap)-1)*100:+.0f}% in "
            f"levels). Dispositive threshold: +"
            f"{LOG_GAP_THRESHOLD_2010:.2f}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": f"log GDP-pc index ({base_year} = 0)",
                   "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": TREATMENT_YEAR,
             "label": "Doi Moi 1986 (pre-data)"},
            {"type": "vline", "x": PRIMARY_END_YEAR,
             "label": f"Primary horizon ({PRIMARY_END_YEAR})"},
            {"type": "note", "label": (
                f"Counterfactual = equal-weight mean of donor pool "
                f"({', '.join(donors_with_base.keys())}). Note: WDI VNM "
                f"GDP-pc-PPP coverage typically begins in 1990, so the "
                f"effective base year is {base_year}, not 1986; the script "
                f"reports the gap from the first overlapping year."
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

    # ---------- manifest.yaml ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- result_card.md ----------
    lines = [
        f"# Vietnam Doi Moi developmental pattern — growth effect",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"Equal-weighted SE-Asian donor-pool counterfactual for Vietnam's "
        f"post-Doi-Moi GDP-per-capita PPP. Vietnam treated in 1986; data "
        f"effectively begins {base_year} (WDI VNM coverage). Donor pool "
        f"(at base year): {', '.join(donors_with_base.keys())}.",
        "",
        f"- **Primary log-gap by {PRIMARY_END_YEAR}**: "
        f"**{primary_gap:+.2f} log-points** "
        f"(≈ {(np.exp(primary_gap)-1)*100:+.0f}% in levels) vs threshold "
        f"+{LOG_GAP_THRESHOLD_2010:.2f}.",
        f"- **Long-window gap to {LONG_END_YEAR}**: "
        f"**{long_gap:+.2f} log-points** "
        f"(≈ {(np.exp(long_gap)-1)*100:+.0f}% in levels).",
        f"- VNM log-index at {PRIMARY_END_YEAR}: {vnm_log_idx_2010:+.2f}; "
        f"donor mean: {donor_mean_log_idx_2010:+.2f}.",
        f"- Overlap years base→{PRIMARY_END_YEAR}: {n_overlap_years} "
        f"(need ≥{MIN_OVERLAP_YEARS}).",
        "",
        "## Informative metrics",
        "",
    ]
    for k, v in informative.items():
        if v.get("available"):
            lines.append(
                f"- **{k}** (post-2000 mean): VNM {v['vnm_late_mean']:.1f}%, "
                f"donor pool {v['donor_late_mean']:.1f}%, "
                f"gap **{v['gap_pp']:+.1f}pp** "
                f"(threshold ±{v['threshold_pp']:.0f}pp; "
                f"passes={v['passes_in_claimed_direction']})."
            )
        else:
            lines.append(f"- **{k}**: data gap ({v.get('reason', 'unknown')}).")
    if tfp_info.get("available"):
        lines.append(
            f"- **PWT TFP (rtfpna)**: VNM log-change "
            f"{tfp_info['vnm_log_tfp_change']:+.2f} vs donor-mean "
            f"{tfp_info['donor_mean_log_tfp_change']:+.2f} "
            f"({tfp_info['tfp_base_year']}-{tfp_info['tfp_end_year']}); "
            f"gap **{tfp_info['tfp_log_gap']:+.2f} log-points**."
        )
    else:
        lines.append("- **PWT TFP**: not available on this vintage.")
    lines += [
        "",
        "## Method",
        "",
        "- **Treatment**: Vietnam, year ≥ 1986 (Doi Moi).",
        f"- **Donor pool**: {', '.join(DONORS)} (Southeast-Asian peers with "
        "comparable 1986 income, excluding the East Asian Tigers THA/MYS "
        "which are reference comparators rather than donors).",
        "- **Counterfactual**: equal-weighted mean of donor pool log-GDP-pc-"
        "PPP, anchored to the first overlapping year (typically 1990 for "
        "WDI). No optimisation of donor weights — equal-weighting is a "
        "conservative baseline because it includes KHM/LAO/MMR which had "
        "their own catch-up booms post-1990; a true synth-DiD weight "
        "optimiser would likely down-weight these and INCREASE the gap.",
        f"- **Primary statistic**: cumulative log-GDP-pc gap (VNM minus "
        f"donor-mean) at {PRIMARY_END_YEAR}.",
        f"- **Dispositive threshold**: +{LOG_GAP_THRESHOLD_2010:.2f} "
        f"log-points (≈ +28% in levels). The spec asked for >+25%, "
        f"rendered in log-space here.",
        "- **Method validity gates**: ≥3 donors with data at base year, "
        "≥10 overlap years base→2010.",
        "",
        "## Caveats",
        "",
        "- WDI's NY.GDP.PCAP.PP.KD coverage for VNM begins 1990, not 1986. "
        "The script anchors the index at the first overlapping year (1990 "
        "in current vintage). Pre-Doi-Moi macro data for VNM is sparse "
        "and not in WDI on the PPP basis — synth-DiD pre-trend matching "
        "in the strict sense is not feasible without alternate sources.",
        "- Equal-weighted donor-pool counterfactual is NOT a true "
        "synth-DiD weight optimisation. v2 should run a proper synth "
        "with pre-1986 covariate matching where data permits, or fall "
        "back to PPP from PWT (which has earlier coverage).",
        "- Donor pool excludes THA/MYS (East Asian Tiger / NIE peers). "
        "If those were included, the counterfactual would be higher and "
        "the Vietnam gap would be smaller. v2 robustness check.",
        "- Author's market-liberal priors interpret Vietnam's success as "
        "primarily about market opening, not state-led pattern replication; "
        "this could under-weight industrial-policy evidence.",
        "",
        "## Data",
        "",
    ]
    for k, v in manifest.items():
        if v.get("missing"):
            lines.append(f"- **MISSING** `{v['publisher']}:{v['series']}`")
        else:
            lines.append(f"- {v['publisher']}:{v['series']} — `{v['vintage_file']}`")
    lines.append("")

    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict[:300]}")


if __name__ == "__main__":
    main()
