#!/usr/bin/env python3
"""Replication — US productivity-compensation decoupling post-1973.

Spec:     hypotheses/growth/productivity_compensation_decoupling_post_1973.yaml
Position-claim: marxian #7 (school predicts: supported)

PRIMARY (dispositive):
  Cumulative log-gap between US nonfarm-business labour productivity
  (output per hour, BLS PRS85006092) and US nonfarm-business real
  hourly compensation (BLS PRS85006112) over 1973-2019 must exceed
  +30 log-percentage-points (productivity > compensation), measured as

    gap_2019 = 100 * ( log(P_2019/P_1973) - log(C_2019/C_1973) )

  REFUTED if gap_2019 <= 0 (compensation kept up with or outpaced
  productivity over the 1973-2019 horizon — i.e. no decoupling).

  PARTIAL if gap_2019 is in (0, 30) — directionally consistent with
  decoupling but below the EPI/Mishel-style >30 ppts framing the
  Marxian claim leans on.

INFORMATIVE (reported, not gating):
  - 1947-1973 baseline cumulative gap (the "co-movement era")
  - Median weekly real earnings (FRED LES1252881600Q) cumulative log gap
    1979-2019 vs the same productivity series (LES starts 1979Q1).
  - Labour share trend (FRED PRS85006173) — should fall over the period.

METHOD_VALID:
  - BLS PRS85006092 and PRS85006112 both available with annual coverage
    spanning 1947-2019 (annual aggregation = mean of monthly/quarterly
    observations within each year). If either ends before 2019, the
    verdict is `inconclusive — data gap`.

The verdict word is the first token in `diagnostics.verdict`, parsed
case-insensitively by the scoring layer (web/lib/content.ts).
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
HID = "productivity_compensation_decoupling_post_1973"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Pre/post-1973 break (Bretton-Woods collapse, productivity slowdown onset).
BASE_YEAR = 1973
END_YEAR = 2019  # pre-COVID terminal year
PRE_BASELINE_START = 1947  # earliest BLS PRS coverage

# Dispositive thresholds
GAP_REFUTE_THRESHOLD_PPT = 0.0   # gap <= 0 → refuted
GAP_SUPPORT_THRESHOLD_PPT = 30.0 # gap >= 30 → supported


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


def annualise(df: pd.DataFrame) -> pd.Series:
    """Collapse a publisher dataframe to year-indexed annual series.

    Handles both BLS-style frames (year, period, periodName, value, ...)
    and FRED-style frames (date, value, realtime_start, realtime_end).
    For BLS series with sub-annual periods we use only periodName == 'Annual'
    if present; otherwise we average all sub-annual obs within each year.
    For FRED frames we average within calendar year.
    Returns an integer-year-indexed pd.Series of the value column.
    """
    if "year" in df.columns and "value" in df.columns:
        # BLS-style. Drop nulls in value.
        d = df[df["value"].notna()].copy()
        if "period" in d.columns:
            ann = d[d["period"].astype(str).str.upper() == "M13"]
            if len(ann) >= 5:
                d = ann
            else:
                # Fall through to average sub-annual obs.
                pass
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
        d = d.dropna(subset=["year"])
        s = d.groupby(d["year"].astype(int))["value"].mean().sort_index()
        s.index = s.index.astype(int)
        return s
    if "date" in df.columns and "value" in df.columns:
        d = df[df["value"].notna()].copy()
        d["date"] = pd.to_datetime(d["date"], errors="coerce")
        d = d.dropna(subset=["date"])
        d["year"] = d["date"].dt.year
        s = d.groupby("year")["value"].mean().sort_index()
        s.index = s.index.astype(int)
        return s
    raise ValueError(f"Unknown schema: {list(df.columns)}")


def cumulative_log_gap_ppt(p: pd.Series, c: pd.Series, t0: int, t1: int) -> float:
    """100 * (log P_t1/P_t0 - log C_t1/C_t0). NaN if either endpoint missing."""
    if t0 not in p.index or t1 not in p.index or t0 not in c.index or t1 not in c.index:
        return float("nan")
    p0, p1, c0, c1 = float(p.loc[t0]), float(p.loc[t1]), float(c.loc[t0]), float(c.loc[t1])
    if p0 <= 0 or c0 <= 0 or p1 <= 0 or c1 <= 0:
        return float("nan")
    return 100.0 * (np.log(p1 / p0) - np.log(c1 / c0))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Load series ----------
    prod_path = latest("bls", "PRS85006092")        # output per hour, NFB
    comp_path = latest("bls", "PRS85006112")        # real hourly comp, NFB
    lshare_path = latest("fred", "PRS85006173")     # labour share, NFB
    medwage_path = latest("fred", "LES1252881600Q") # median real weekly earnings

    manifest = {
        "labour_productivity": {
            "publisher": "bls", "series": "PRS85006092",
            "vintage_file": str(prod_path.relative_to(REPO_ROOT)),
            "sha256": sha256(prod_path),
        },
        "real_hourly_compensation": {
            "publisher": "bls", "series": "PRS85006112",
            "vintage_file": str(comp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(comp_path),
        },
        "labour_share": {
            "publisher": "fred", "series": "PRS85006173",
            "vintage_file": str(lshare_path.relative_to(REPO_ROOT)),
            "sha256": sha256(lshare_path),
        },
        "median_real_weekly_earnings": {
            "publisher": "fred", "series": "LES1252881600Q",
            "vintage_file": str(medwage_path.relative_to(REPO_ROOT)),
            "sha256": sha256(medwage_path),
        },
    }

    prod = annualise(pq.read_table(prod_path).to_pandas())
    comp = annualise(pq.read_table(comp_path).to_pandas())
    lshare = annualise(pq.read_table(lshare_path).to_pandas())
    medwage = annualise(pq.read_table(medwage_path).to_pandas())

    # ---------- METHOD_VALID gate ----------
    method_valid = True
    method_notes = []
    for name, s in [("PRS85006092", prod), ("PRS85006112", comp)]:
        if BASE_YEAR not in s.index:
            method_valid = False
            method_notes.append(f"{name} missing {BASE_YEAR}")
        if END_YEAR not in s.index:
            method_valid = False
            method_notes.append(f"{name} missing {END_YEAR}")

    if not method_valid:
        verdict = (
            "inconclusive — data gap on bls:PRS85006092 / bls:PRS85006112; "
            f"missing endpoints: {', '.join(method_notes)}"
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "missing": method_notes,
            "n_prod_years": int(len(prod)),
            "n_comp_years": int(len(comp)),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        # Minimal artefacts for downstream
        pd.DataFrame([{"spec": "primary", "term": "gap_ppt", "estimate": float("nan")}]).to_parquet(
            OUT_DIR / "coefficients.parquet", index=False
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "US productivity vs compensation — DATA GAP",
            "subtitle": verdict,
            "type": "line", "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Index (1973=100)", "type": "linear"},
            "series": [], "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nrun_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
            "vintages:\n" + "".join(
                f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
                f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
                for k, v in manifest.items()
            )
        )
        (OUT_DIR / "result_card.md").write_text(
            f"# US productivity-compensation decoupling post-1973\n\n"
            f"**Verdict:** {verdict}\n\n"
            f"## Data gap\n\n{', '.join(method_notes)}\n"
        )
        print(f"verdict: {verdict}")
        return

    # ---------- PRIMARY: post-1973 cumulative log-gap ----------
    gap_post_1973 = cumulative_log_gap_ppt(prod, comp, BASE_YEAR, END_YEAR)

    # ---------- INFORMATIVE: pre-1973 baseline gap ----------
    pre_start = max(PRE_BASELINE_START, int(min(prod.index.min(), comp.index.min())))
    gap_pre_1973 = cumulative_log_gap_ppt(prod, comp, pre_start, BASE_YEAR)

    # Median weekly real earnings — only available 1979+
    medwage_start = int(medwage.index.min()) if len(medwage) else None
    if medwage_start is not None and medwage_start <= 1979 + 5 and END_YEAR in medwage.index:
        # Use the first year of overlap as the base.
        medwage_base = max(1979, medwage_start)
        gap_post_medwage = cumulative_log_gap_ppt(prod, medwage, medwage_base, END_YEAR)
    else:
        medwage_base = None
        gap_post_medwage = float("nan")

    # Labour share change (in percentage points)
    if BASE_YEAR in lshare.index and END_YEAR in lshare.index:
        lshare_change_ppt = float(lshare.loc[END_YEAR] - lshare.loc[BASE_YEAR])
    else:
        lshare_change_ppt = float("nan")

    # ---------- Verdict ----------
    if gap_post_1973 >= GAP_SUPPORT_THRESHOLD_PPT:
        verdict = (
            f"SUPPORTED — Post-1973 cumulative productivity-compensation log-gap "
            f"(US nonfarm business, 1973-{END_YEAR}): "
            f"+{gap_post_1973:.1f} log-ppts (productivity > compensation), "
            f"exceeding the EPI/Mishel-style >+30 ppt threshold. "
            f"Pre-1973 baseline gap ({pre_start}-1973): {gap_pre_1973:+.1f} log-ppts. "
            f"Labour share change: {lshare_change_ppt:+.1f} ppt."
        )
    elif gap_post_1973 > GAP_REFUTE_THRESHOLD_PPT:
        verdict = (
            f"partial — Post-1973 cumulative productivity-compensation log-gap "
            f"is positive ({gap_post_1973:+.1f} log-ppts) — directionally consistent "
            f"with decoupling — but below the +30 ppt EPI/Mishel framing the "
            f"Marxian claim leans on. Pre-1973 baseline gap ({pre_start}-1973): "
            f"{gap_pre_1973:+.1f}. Labour share change: {lshare_change_ppt:+.1f} ppt."
        )
    elif np.isnan(gap_post_1973):
        verdict = (
            "inconclusive — could not compute the cumulative log-gap with available data."
        )
    else:
        verdict = (
            f"refuted — Post-1973 cumulative log-gap is {gap_post_1973:+.1f} log-ppts "
            f"(productivity did NOT outpace compensation 1973-{END_YEAR} on the "
            f"composition-adjusted nonfarm-business measure). Pre-1973 baseline gap: "
            f"{gap_pre_1973:+.1f}. Labour share change: {lshare_change_ppt:+.1f} ppt."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "primary_gap_ppt_post_1973": gap_post_1973,
        "primary_threshold_support_ppt": GAP_SUPPORT_THRESHOLD_PPT,
        "primary_threshold_refute_ppt": GAP_REFUTE_THRESHOLD_PPT,
        "informative_gap_ppt_pre_1973": gap_pre_1973,
        "informative_pre_baseline_start_year": int(pre_start),
        "informative_gap_ppt_medwage_post": gap_post_medwage,
        "informative_medwage_base_year": medwage_base,
        "informative_labour_share_change_ppt": lshare_change_ppt,
        "endpoints": {
            "base_year": BASE_YEAR,
            "end_year": END_YEAR,
        },
        "n_prod_years": int(len(prod)),
        "n_comp_years": int(len(comp)),
        "prod_year_min": int(prod.index.min()),
        "prod_year_max": int(prod.index.max()),
        "comp_year_min": int(comp.index.min()),
        "comp_year_max": int(comp.index.max()),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    # Indexed productivity vs compensation, 1973=100, full available range.
    years = sorted(set(prod.index) & set(comp.index))
    if BASE_YEAR not in years:
        years = sorted(set(prod.index) & set(comp.index) | {BASE_YEAR})

    p_base = float(prod.loc[BASE_YEAR])
    c_base = float(comp.loc[BASE_YEAR])

    prod_pts = [
        {"x": int(y), "y": float(prod.loc[y] / p_base * 100.0)}
        for y in sorted(prod.index) if y >= max(PRE_BASELINE_START, 1947)
    ]
    comp_pts = [
        {"x": int(y), "y": float(comp.loc[y] / c_base * 100.0)}
        for y in sorted(comp.index) if y >= max(PRE_BASELINE_START, 1947)
    ]

    # Labour share secondary series (level, not indexed) — keep optional series
    lshare_pts = []
    if len(lshare):
        for y in sorted(lshare.index):
            if y >= max(PRE_BASELINE_START, 1947):
                lshare_pts.append({"x": int(y), "y": float(lshare.loc[y])})

    series = [
        {
            "id": "productivity",
            "label": "Labour productivity (NFB output/hour)",
            "color": "#4E79A7",
            "treated": True,
            "points": prod_pts,
        },
        {
            "id": "real_compensation",
            "label": "Real hourly compensation (NFB)",
            "color": "#E15759",
            "treated": False,
            "points": comp_pts,
        },
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US labour productivity vs real hourly compensation, 1947-2019",
        "subtitle": (
            f"Both indexed to {BASE_YEAR}=100. "
            f"Cumulative gap {BASE_YEAR}-{END_YEAR}: {gap_post_1973:+.1f} log-ppts. "
            f"Pre-1973 ({pre_start}-{BASE_YEAR}) baseline gap: {gap_pre_1973:+.1f} log-ppts."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": f"Index ({BASE_YEAR} = 100)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vertical_line",
                "x": BASE_YEAR,
                "label": f"{BASE_YEAR} — Bretton Woods collapse / productivity slowdown onset",
            },
            {
                "type": "note",
                "label": (
                    f"Gap by {END_YEAR}: {gap_post_1973:+.1f} log-ppts. "
                    f"EPI/Mishel-style threshold for the decoupling claim: > +30 ppts. "
                    f"Labour share change {BASE_YEAR}-{END_YEAR}: {lshare_change_ppt:+.1f} ppt."
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

    # ---------- Coefficients ----------
    pd.DataFrame(
        [
            {"spec": "primary", "term": "gap_log_ppt_1973_2019", "estimate": gap_post_1973},
            {"spec": "informative", "term": f"gap_log_ppt_{pre_start}_1973", "estimate": gap_pre_1973},
            {"spec": "informative", "term": "gap_log_ppt_medwage_post_1979", "estimate": gap_post_medwage},
            {"spec": "informative", "term": "labour_share_change_ppt_1973_2019", "estimate": lshare_change_ppt},
            {"spec": "diagnostic", "term": "prod_index_2019_base_1973", "estimate": float(prod.loc[END_YEAR] / prod.loc[BASE_YEAR] * 100.0)},
            {"spec": "diagnostic", "term": "comp_index_2019_base_1973", "estimate": float(comp.loc[END_YEAR] / comp.loc[BASE_YEAR] * 100.0)},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
        f"# US productivity-compensation decoupling post-1973",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Cumulative log-gap (productivity − compensation), {BASE_YEAR}-{END_YEAR}: "
        f"**{gap_post_1973:+.1f} log-ppts**.",
        f"- Threshold for SUPPORTED (EPI/Mishel-style \"large gap\" framing): "
        f"≥ +{GAP_SUPPORT_THRESHOLD_PPT:.0f} log-ppts.",
        f"- Threshold for REFUTED: ≤ {GAP_REFUTE_THRESHOLD_PPT:.0f} log-ppts "
        "(compensation kept up with productivity).",
        f"- Pre-1973 baseline gap ({pre_start}-{BASE_YEAR}): **{gap_pre_1973:+.1f} log-ppts**.",
        f"- Labour share change {BASE_YEAR}-{END_YEAR}: **{lshare_change_ppt:+.1f} ppt**.",
        f"- Median weekly real earnings cumulative gap "
        f"({medwage_base or 'n/a'}-{END_YEAR}): "
        f"**{gap_post_medwage:+.1f} log-ppts** (informative, not gating).",
        "",
        "## Method",
        "",
        "Annual collapse of BLS PRS85006092 (output per hour, nonfarm business) "
        "and BLS PRS85006112 (real hourly compensation, nonfarm business). "
        "Both are composition-adjusted aggregate series (the BLS productivity "
        "and costs program's own benchmark indexes), so the test is *already* "
        "on the composition-adjusted measure the spec calls for — not on raw "
        "median wages. The cumulative log-gap is the standard EPI/Mishel "
        "decoupling measure.",
        "",
        "Ending the post-1973 horizon at 2019 avoids the COVID-2020 distortion. "
        "The 1973 break corresponds to the Bretton-Woods collapse and the onset "
        "of the post-WWII productivity slowdown.",
        "",
        "Median weekly real earnings (FRED LES1252881600Q) starts in 1979Q1, "
        "so the median-wage test uses a shorter window and is reported as "
        "informative only.",
        "",
        "## Data",
        "",
        "- bls:PRS85006092 — Output per hour, nonfarm business sector (productivity)",
        "- bls:PRS85006112 — Real hourly compensation, nonfarm business sector",
        "- fred:PRS85006173 — Labor share, nonfarm business sector",
        "- fred:LES1252881600Q — Median usual weekly real earnings (16+ wage workers)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
