#!/usr/bin/env python3
"""Replication — US financial-sector profit share, 1970 vs 2007 endpoint test.

Spec: hypotheses/growth/financial_sector_profit_share_rise_1970_2007.yaml v1
Position-claim: marxian #8 (school predicts: supported)

Tests two endpoint level conditions on a constructed share series:

  PRIMARY (a): annual-mean financial_share in 1970 <= 0.15 (tolerance band
               [0.10, 0.18]; > 0.18 falsifies the start-condition).
  PRIMARY (b): annual-mean financial_share in 2007 >= 0.30 (tolerance band
               [0.27, 0.33]; < 0.27 falsifies the end-condition).

Constructed series:
    financial_share = A453RC1Q027SBEA / (A453RC1Q027SBEA + A446RC1Q027SBEA)

A453RC1Q027SBEA = Financial corporate profits before tax (NIPA, quarterly)
A446RC1Q027SBEA = Domestic non-financial corporate profits before tax (NIPA, quarterly)

Annualisation: simple mean of within-year quarterly observations.

METHOD_VALID gate: both FRED series must be present on disk and have at
least 3 quarterly observations in each of 1970 and 2007. If not, the
verdict is `inconclusive (data gap)` rather than `refuted`.

Verdict semantics (first word, parsed by web/lib/content.ts::verdictTone()):
  SUPPORTED | partial | refuted | weakened | inconclusive
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
HID = "financial_sector_profit_share_rise_1970_2007"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Spec inputs
COUNTRY = "USA"
START_YEAR = 1970
END_YEAR = 2007

FRED_FINANCIAL = "A453RC1Q027SBEA"          # financial corp profits before tax
FRED_NONFINANCIAL = "A446RC1Q027SBEA"        # domestic non-financial corp profits before tax

# Falsification thresholds (from spec.falsification, made dispositive)
START_THRESHOLD = 0.15           # 1970 <= 0.15 supports
END_THRESHOLD = 0.30             # 2007 >= 0.30 supports
TOLERANCE = 0.03                 # ±3pp band around each threshold
START_FALSIFY_BAND = START_THRESHOLD + TOLERANCE   # 0.18 — strictly above falsifies
END_FALSIFY_BAND = END_THRESHOLD - TOLERANCE       # 0.27 — strictly below falsifies
DIRECTIONAL_RISE_PP = 0.10       # +10pp from 1970→2007 needed for "partial"


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


def load_fred_quarterly(path: Path) -> pd.DataFrame:
    """FRED schema: (date, value, realtime_start, realtime_end). Return
    a DataFrame with columns (date: datetime, year: int, value: float),
    one row per observation_date, picking the most recent realtime vintage
    per date."""
    t = pq.read_table(path).to_pandas()
    if "date" not in t.columns or "value" not in t.columns:
        raise ValueError(f"{path}: missing date/value ({list(t.columns)})")
    t["date"] = pd.to_datetime(t["date"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.dropna(subset=["date", "value"]).copy()
    if "realtime_end" in t.columns:
        # Pick the latest realtime vintage per observation date
        t = t.sort_values(["date", "realtime_end"]).drop_duplicates("date", keep="last")
    t["year"] = t["date"].dt.year.astype(int)
    return t[["date", "year", "value"]].sort_values("date").reset_index(drop=True)


def emit_inconclusive(reason: str, manifest: dict) -> None:
    """Write the four required artifacts with an inconclusive verdict and stop."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verdict = f"inconclusive — {reason}"
    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "data_gap": True,
        "reason": reason,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US financial-sector profit share, 1970–2007 (data gap)",
        "subtitle": reason,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "financial-corp share of total corp profits", "type": "linear"},
        "series": [],
        "annotations": [{"type": "note", "label": reason}],
        "sources": [],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [{"spec": "method_valid", "term": "data_gap", "estimate": float("nan")}]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        f"status: inconclusive\n"
        f"reason: {reason}\n"
        "vintages: {}\n"
    )

    card = [
        f"# US financial-sector profit share, 1970 vs 2007",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- The replication requires FRED `{FRED_FINANCIAL}` (financial corporate "
        "profits before tax, quarterly) and FRED "
        f"`{FRED_NONFINANCIAL}` (domestic non-financial corporate profits before "
        "tax, quarterly) under `data/vintages/fred/`.",
        f"- {reason}",
        f"- The replication script is ready to run as soon as the missing "
        "FRED series are fetched into the vintage store.",
        "",
        "## Method (planned)",
        "",
        "Construct annual financial_share = mean of quarterly "
        f"{FRED_FINANCIAL} ÷ (mean of quarterly {FRED_FINANCIAL} + mean of "
        f"quarterly {FRED_NONFINANCIAL}) for each calendar year. Test "
        f"financial_share[1970] ≤ 0.15 and financial_share[2007] ≥ 0.30, "
        f"with ±0.03 tolerance bands.",
        "",
        "## Data needed",
        "",
        f"- fred:{FRED_FINANCIAL}",
        f"- fred:{FRED_NONFINANCIAL}",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")
    print(f"verdict: {verdict}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fin_path = latest("fred", FRED_FINANCIAL)
    nfin_path = latest("fred", FRED_NONFINANCIAL)

    missing = []
    if fin_path is None:
        missing.append(f"fred:{FRED_FINANCIAL}")
    if nfin_path is None:
        missing.append(f"fred:{FRED_NONFINANCIAL}")
    if missing:
        emit_inconclusive(
            f"data gap on {', '.join(missing)} — vintage parquet not on disk",
            manifest={},
        )
        return

    manifest = {
        "financial_corp_profits_before_tax": {
            "publisher": "fred",
            "series": FRED_FINANCIAL,
            "vintage_file": str(fin_path.relative_to(REPO_ROOT)),
            "sha256": sha256(fin_path),
        },
        "nonfinancial_corp_profits_before_tax": {
            "publisher": "fred",
            "series": FRED_NONFINANCIAL,
            "vintage_file": str(nfin_path.relative_to(REPO_ROOT)),
            "sha256": sha256(nfin_path),
        },
    }

    fin = load_fred_quarterly(fin_path)
    nfin = load_fred_quarterly(nfin_path)

    # ---------- METHOD_VALID gate: at least 3 quarterly obs in 1970 & 2007 ----------
    def n_obs(df: pd.DataFrame, year: int) -> int:
        return int(df[df["year"] == year].shape[0])

    n_fin_1970 = n_obs(fin, START_YEAR)
    n_fin_2007 = n_obs(fin, END_YEAR)
    n_nfin_1970 = n_obs(nfin, START_YEAR)
    n_nfin_2007 = n_obs(nfin, END_YEAR)

    method_valid = (
        n_fin_1970 >= 3 and n_fin_2007 >= 3
        and n_nfin_1970 >= 3 and n_nfin_2007 >= 3
    )
    if not method_valid:
        emit_inconclusive(
            (
                f"insufficient quarterly coverage: "
                f"{FRED_FINANCIAL} 1970={n_fin_1970}q 2007={n_fin_2007}q; "
                f"{FRED_NONFINANCIAL} 1970={n_nfin_1970}q 2007={n_nfin_2007}q "
                f"(need ≥ 3 per year)"
            ),
            manifest=manifest,
        )
        return

    # ---------- Construct annual financial_share ----------
    # Annual mean of quarterly observations, then construct share.
    fin_annual = (
        fin[fin["year"].between(START_YEAR, END_YEAR)]
        .groupby("year", as_index=True)["value"].mean()
    )
    nfin_annual = (
        nfin[nfin["year"].between(START_YEAR, END_YEAR)]
        .groupby("year", as_index=True)["value"].mean()
    )
    common_years = sorted(set(fin_annual.index) & set(nfin_annual.index))
    share_annual = pd.Series(
        {y: float(fin_annual[y] / (fin_annual[y] + nfin_annual[y])) for y in common_years},
        name="financial_share",
    )

    if START_YEAR not in share_annual.index or END_YEAR not in share_annual.index:
        emit_inconclusive(
            f"annual share missing for one of the endpoint years (have "
            f"{sorted(share_annual.index)[:3]}…{sorted(share_annual.index)[-3:]})",
            manifest=manifest,
        )
        return

    share_1970 = float(share_annual[START_YEAR])
    share_2007 = float(share_annual[END_YEAR])
    delta_pp = share_2007 - share_1970

    # ---------- Endpoint tests ----------
    start_pass = share_1970 <= START_THRESHOLD
    start_falsified = share_1970 > START_FALSIFY_BAND  # > 0.18
    start_in_band = (not start_pass) and (not start_falsified)

    end_pass = share_2007 >= END_THRESHOLD
    end_falsified = share_2007 < END_FALSIFY_BAND  # < 0.27
    end_in_band = (not end_pass) and (not end_falsified)

    direction_ok = delta_pp >= DIRECTIONAL_RISE_PP

    # ---------- Informative diagnostics ----------
    def first_year_crossing(threshold: float) -> int | None:
        for y in sorted(share_annual.index):
            if share_annual[y] >= threshold:
                return int(y)
        return None

    cross_20 = first_year_crossing(0.20)
    cross_30 = first_year_crossing(0.30)
    n_years = len(share_annual)
    cagr_pp_per_yr = delta_pp / max(1, (END_YEAR - START_YEAR))

    # ---------- Verdict ----------
    if start_pass and end_pass:
        verdict = (
            f"SUPPORTED — US financial-corp share of total (financial + "
            f"non-financial) domestic corporate profits before tax was "
            f"{share_1970*100:.1f}% in 1970 (≤ 15% threshold) and "
            f"{share_2007*100:.1f}% in 2007 (≥ 30% threshold); rise of "
            f"{delta_pp*100:+.1f}pp over 37 years "
            f"({cagr_pp_per_yr*100:+.2f}pp/yr)."
        )
    elif start_falsified or end_falsified:
        which = []
        if start_falsified:
            which.append(f"1970 share = {share_1970*100:.1f}% > 18% falsify-band")
        if end_falsified:
            which.append(f"2007 share = {share_2007*100:.1f}% < 27% falsify-band")
        verdict = (
            f"refuted — endpoint outside falsification band: "
            f"{'; '.join(which)}. Direction {'ok' if direction_ok else 'wrong'} "
            f"({delta_pp*100:+.1f}pp 1970→2007)."
        )
    elif direction_ok and (start_in_band or end_in_band):
        verdict = (
            f"partial — direction correct (rise of {delta_pp*100:+.1f}pp 1970→2007) "
            f"but at least one endpoint sits inside the ±3pp tolerance band: "
            f"1970 = {share_1970*100:.1f}% (target ≤ 15%), "
            f"2007 = {share_2007*100:.1f}% (target ≥ 30%)."
        )
    else:
        verdict = (
            f"weakened — endpoints near the thresholds and rise of "
            f"{delta_pp*100:+.1f}pp is below the +10pp directional floor. "
            f"1970 = {share_1970*100:.1f}%, 2007 = {share_2007*100:.1f}%."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": bool(start_pass and end_pass),
        "method_valid": True,
        "primary_start_pass": bool(start_pass),
        "primary_end_pass": bool(end_pass),
        "primary_start_falsified": bool(start_falsified),
        "primary_end_falsified": bool(end_falsified),
        "share_1970": share_1970,
        "share_2007": share_2007,
        "delta_pp_1970_to_2007": delta_pp,
        "directional_rise_pp_floor": DIRECTIONAL_RISE_PP,
        "directional_pass": bool(direction_ok),
        "start_threshold": START_THRESHOLD,
        "end_threshold": END_THRESHOLD,
        "tolerance": TOLERANCE,
        "start_falsify_band_above": START_FALSIFY_BAND,
        "end_falsify_band_below": END_FALSIFY_BAND,
        "first_year_share_geq_0_20": cross_20,
        "first_year_share_geq_0_30": cross_30,
        "cagr_pp_per_year": cagr_pp_per_yr,
        "n_years_in_panel": n_years,
        "annual_share": {int(y): float(v) for y, v in share_annual.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    pts = [{"x": int(y), "y": float(share_annual[y])} for y in sorted(share_annual.index)]
    series = [
        {
            "id": "financial_share_USA",
            "label": "US financial-corp share of total corp profits (NIPA, BoP)",
            "color": "#4E79A7",
            "treated": True,
            "points": pts,
        },
        {
            "id": "threshold_15pct",
            "label": "1970 SUPPORTED threshold (≤ 15%)",
            "color": "#9C9C9C",
            "treated": False,
            "points": [{"x": START_YEAR, "y": START_THRESHOLD},
                       {"x": END_YEAR, "y": START_THRESHOLD}],
        },
        {
            "id": "threshold_30pct",
            "label": "2007 SUPPORTED threshold (≥ 30%)",
            "color": "#9C9C9C",
            "treated": False,
            "points": [{"x": START_YEAR, "y": END_THRESHOLD},
                       {"x": END_YEAR, "y": END_THRESHOLD}],
        },
    ]
    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US financial-corp profit share, 1970–2007",
        "subtitle": (
            f"1970: {share_1970*100:.1f}% (target ≤ 15%); "
            f"2007: {share_2007*100:.1f}% (target ≥ 30%); "
            f"Δ = {delta_pp*100:+.1f}pp."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "financial-corp share of total corp profits before tax", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Constructed share: A453 / (A453 + A446), annual mean of "
                    f"quarterly observations. ±3pp tolerance bands around the "
                    f"15%/30% thresholds."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    pd.DataFrame(
        [
            {"spec": "primary_a", "term": "share_1970", "estimate": share_1970},
            {"spec": "primary_b", "term": "share_2007", "estimate": share_2007},
            {"spec": "informative", "term": "delta_pp_1970_to_2007", "estimate": delta_pp},
            {"spec": "informative", "term": "cagr_pp_per_year", "estimate": cagr_pp_per_yr},
            {"spec": "informative", "term": "first_year_geq_0_20",
             "estimate": float(cross_20) if cross_20 is not None else float("nan")},
            {"spec": "informative", "term": "first_year_geq_0_30",
             "estimate": float(cross_30) if cross_30 is not None else float("nan")},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
        f"# US financial-sector profit share, 1970 vs 2007",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- 1970 financial_share = **{share_1970*100:.1f}%** "
        f"(target ≤ 15%; falsify-band: > 18%).",
        f"- 2007 financial_share = **{share_2007*100:.1f}%** "
        f"(target ≥ 30%; falsify-band: < 27%).",
        f"- Δ 1970→2007 = **{delta_pp*100:+.1f}pp** "
        f"({cagr_pp_per_yr*100:+.2f}pp/yr).",
        (f"- First year with share ≥ 20%: **{cross_20}**." if cross_20 else
         "- Share never crossed 20% in the panel."),
        (f"- First year with share ≥ 30%: **{cross_30}**." if cross_30 else
         "- Share never crossed 30% in the panel."),
        "",
        "## Method",
        "",
        "Constructed series: `financial_share = A453RC1Q027SBEA / "
        "(A453RC1Q027SBEA + A446RC1Q027SBEA)`. Both inputs are quarterly "
        "billions-of-dollars NIPA flows (financial corporate profits before "
        "tax, and domestic non-financial corporate profits before tax). The "
        "annual figure is the simple mean of within-year quarterly "
        "observations of each numerator/denominator, then the share is "
        "constructed from the annual means.",
        "",
        "Endpoint tests:",
        "",
        "- PRIMARY (a): share[1970] ≤ 0.15. Falsify-band: > 0.18.",
        "- PRIMARY (b): share[2007] ≥ 0.30. Falsify-band: < 0.27.",
        "",
        "If either endpoint sits inside its tolerance band but the direction "
        "is correct (Δ ≥ +10pp), the verdict is `partial`. If either is on "
        "the wrong side of its falsify-band, the verdict is `refuted`. If "
        "the input vintages are missing, the verdict is `inconclusive`.",
        "",
        "## Data",
        "",
        f"- fred:{FRED_FINANCIAL} (financial corporate profits before tax, quarterly)",
        f"- fred:{FRED_NONFINANCIAL} (domestic non-financial corporate profits before tax, quarterly)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
