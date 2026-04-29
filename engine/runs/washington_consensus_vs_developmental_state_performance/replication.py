#!/usr/bin/env python3
"""Replication — Washington Consensus vs Developmental State performance.

Spec: hypotheses/growth/washington_consensus_vs_developmental_state_performance.yaml v1
Position-claim: developmentalism #10 (school predicts: supported)

Dispositive descriptive comparison of cumulative real GDP-per-capita growth:

  PRIMARY: Cumulative log-growth gap = log(GDP-pc[end]/GDP-pc[start])_KOR
           - log(GDP-pc[end]/GDP-pc[start])_ARG, over the matched decade.

           ARG window: 1991-2001 (Menem convertibility & privatisation era,
           ending in the 2001 collapse).

           KOR window: a decade beginning in the year when KOR's real
           GDP-pc level (WDI NY.GDP.PCAP.KD, constant 2015 USD) was
           closest to ARG's 1991 real GDP-pc level — i.e. the
           "comparable starting point" matched-decade reading. The
           window then spans [match_year, match_year + 10].

  SUPPORTED if KOR exceeds ARG by >= +0.30 log-points (~+35pp
  cumulative GDP-pc growth advantage). REFUTED if ARG >= KOR
  cumulatively. PARTIAL if KOR > ARG but gap < +0.30 log-points.

  METHOD_VALID: both ARG 1991, ARG 2001, KOR match_year and
  KOR match_year+10 must be present in WDI; if not, emit
  inconclusive (data gap).

The PPP series (NY.GDP.PCAP.PP.KD) is reported as a robustness panel
but does not gate the verdict.
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
HID = "washington_consensus_vs_developmental_state_performance"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# ARG matched window (Menem era)
ARG_START = 1991
ARG_END = 2001

# KOR window length matches ARG (decade)
WINDOW_YEARS = ARG_END - ARG_START  # 10

# Falsification thresholds
SUPPORTED_LOG_GAP = 0.30  # KOR - ARG cumulative log GDP-pc growth gap


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


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
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


def write_inconclusive(reason: str, manifest: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    verdict = f"inconclusive — {reason}"
    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "data_gap": True,
        "reason": reason,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "chart_data.json").write_text(json.dumps({
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Washington Consensus vs Developmental State — data gap",
        "subtitle": reason,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Real GDP per capita (constant 2015 USD)", "type": "linear"},
        "series": [],
        "annotations": [],
        "sources": [],
        "permalink": f"/h/{HID}",
    }, indent=2) + "\n")
    pd.DataFrame([{"spec": "primary", "term": "data_gap", "estimate": float("nan")}]).to_parquet(
        OUT_DIR / "coefficients.parquet", index=False
    )
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + ("".join(
            f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
            f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
            for k, v in manifest.items()
        ) if manifest else "  {}\n")
    )
    (OUT_DIR / "result_card.md").write_text(
        f"# Washington Consensus vs Developmental State performance\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Summary\n\nMissing data prevents a dispositive read; see diagnostics.\n"
    )
    print(f"verdict: {verdict}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    gdp_ppp_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")

    if gdp_path is None:
        write_inconclusive("data gap on world_bank_wdi:NY.GDP.PCAP.KD", {})
        return

    manifest = {
        "real_gdp_per_capita": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        }
    }
    if gdp_ppp_path is not None:
        manifest["real_gdp_per_capita_ppp"] = {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.PP.KD",
            "vintage_file": str(gdp_ppp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_ppp_path),
        }

    gdp = load_long(gdp_path)
    arg = (
        gdp[gdp["country_iso3"] == "ARG"][["year", "value"]]
        .assign(year=lambda d: d["year"].astype(int))
        .set_index("year")["value"]
        .sort_index()
    )
    kor = (
        gdp[gdp["country_iso3"] == "KOR"][["year", "value"]]
        .assign(year=lambda d: d["year"].astype(int))
        .set_index("year")["value"]
        .sort_index()
    )

    # ---------- ARG 1991-2001 ----------
    if ARG_START not in arg.index or ARG_END not in arg.index:
        write_inconclusive(
            f"data gap on world_bank_wdi:NY.GDP.PCAP.KD for ARG "
            f"({ARG_START} or {ARG_END} missing)",
            manifest,
        )
        return
    arg_start_val = float(arg[ARG_START])
    arg_end_val = float(arg[ARG_END])
    arg_log_growth = float(np.log(arg_end_val / arg_start_val))

    # ---------- KOR matched-decade ----------
    # Pick KOR start year as the year KOR's real GDP-pc was closest
    # to ARG's 1991 starting level. Search KOR's available years that
    # leave room for a full decade window before the latest available.
    kor_max_year = int(kor.index.max())
    candidate_years = [y for y in kor.index if y + WINDOW_YEARS <= kor_max_year]
    if not candidate_years:
        write_inconclusive(
            "data gap on world_bank_wdi:NY.GDP.PCAP.KD for KOR (insufficient years)",
            manifest,
        )
        return

    # Closest-level match
    kor_levels = kor.loc[candidate_years]
    diffs = (kor_levels - arg_start_val).abs()
    kor_match_year = int(diffs.idxmin())
    kor_match_end_year = kor_match_year + WINDOW_YEARS

    if kor_match_end_year not in kor.index:
        write_inconclusive(
            f"data gap on world_bank_wdi:NY.GDP.PCAP.KD for KOR "
            f"({kor_match_end_year} missing)",
            manifest,
        )
        return

    kor_start_val = float(kor[kor_match_year])
    kor_end_val = float(kor[kor_match_end_year])
    kor_log_growth = float(np.log(kor_end_val / kor_start_val))

    # ---------- PRIMARY ----------
    log_gap = kor_log_growth - arg_log_growth  # KOR minus ARG
    arg_pct = (np.exp(arg_log_growth) - 1) * 100
    kor_pct = (np.exp(kor_log_growth) - 1) * 100
    gap_pct_points = kor_pct - arg_pct

    if log_gap >= SUPPORTED_LOG_GAP:
        verdict = (
            f"SUPPORTED — KOR cumulative GDP-pc growth over its matched "
            f"decade {kor_match_year}-{kor_match_end_year} (start level "
            f"${kor_start_val:,.0f} ≈ ARG {ARG_START} ${arg_start_val:,.0f}) "
            f"was {kor_log_growth:+.3f} log-points ({kor_pct:+.1f}%), vs "
            f"ARG {ARG_START}-{ARG_END} {arg_log_growth:+.3f} log-points "
            f"({arg_pct:+.1f}%). Gap = {log_gap:+.3f} log-points "
            f"({gap_pct_points:+.1f}pp), at/above the +0.30 log-point "
            f"(~+35pp) SUPPORTED threshold."
        )
    elif log_gap <= 0:
        verdict = (
            f"refuted — ARG {ARG_START}-{ARG_END} cumulative GDP-pc "
            f"growth ({arg_log_growth:+.3f} log-points / {arg_pct:+.1f}%) "
            f"matched or exceeded KOR's matched decade "
            f"{kor_match_year}-{kor_match_end_year} "
            f"({kor_log_growth:+.3f} log-points / {kor_pct:+.1f}%). "
            f"Gap (KOR-ARG) = {log_gap:+.3f} log-points."
        )
    else:
        verdict = (
            f"partial — KOR's matched decade "
            f"{kor_match_year}-{kor_match_end_year} outperformed ARG "
            f"{ARG_START}-{ARG_END} by {log_gap:+.3f} log-points "
            f"({gap_pct_points:+.1f}pp), but the gap fell short of the "
            f"+0.30 log-point (~+35pp) SUPPORTED threshold. "
            f"KOR {kor_log_growth:+.3f} vs ARG {arg_log_growth:+.3f}."
        )

    # ---------- Supplementary: Park-era KOR window 1962-1972 ----------
    # The spec also references the Park Chung-hee developmental-state era as
    # the canonical comparator. Report it as a secondary descriptive panel
    # alongside the level-matched window. Does NOT gate the verdict.
    PARK_START, PARK_END = 1962, 1972
    if PARK_START in kor.index and PARK_END in kor.index:
        kor_park_start = float(kor[PARK_START])
        kor_park_end = float(kor[PARK_END])
        kor_park_log = float(np.log(kor_park_end / kor_park_start))
        kor_park_pct = (np.exp(kor_park_log) - 1) * 100
        park_log_gap = kor_park_log - arg_log_growth
    else:
        kor_park_start = kor_park_end = kor_park_log = kor_park_pct = None
        park_log_gap = None

    # ---------- PPP robustness ----------
    ppp_panel = {}
    if gdp_ppp_path is not None:
        ppp = load_long(gdp_ppp_path)
        for iso in ("ARG", "KOR"):
            s = (
                ppp[ppp["country_iso3"] == iso][["year", "value"]]
                .assign(year=lambda d: d["year"].astype(int))
                .set_index("year")["value"]
                .sort_index()
            )
            ppp_panel[iso] = s
        # Compute the same windows in PPP if available
        try:
            arg_ppp_lg = float(np.log(ppp_panel["ARG"][ARG_END] / ppp_panel["ARG"][ARG_START]))
        except KeyError:
            arg_ppp_lg = None
        try:
            kor_ppp_lg = float(np.log(
                ppp_panel["KOR"][kor_match_end_year] / ppp_panel["KOR"][kor_match_year]
            ))
        except KeyError:
            kor_ppp_lg = None
        ppp_log_gap = (
            (kor_ppp_lg - arg_ppp_lg)
            if (arg_ppp_lg is not None and kor_ppp_lg is not None)
            else None
        )
    else:
        arg_ppp_lg = kor_ppp_lg = ppp_log_gap = None

    diagnostics = {
        "verdict": verdict,
        "all_pass": log_gap >= SUPPORTED_LOG_GAP,
        "primary_log_gap_kor_minus_arg": log_gap,
        "supported_threshold_log_points": SUPPORTED_LOG_GAP,
        "arg_window": [ARG_START, ARG_END],
        "kor_window": [kor_match_year, kor_match_end_year],
        "arg_start_value": arg_start_val,
        "arg_end_value": arg_end_val,
        "arg_log_growth": arg_log_growth,
        "arg_cum_pct": arg_pct,
        "kor_start_value": kor_start_val,
        "kor_end_value": kor_end_val,
        "kor_log_growth": kor_log_growth,
        "kor_cum_pct": kor_pct,
        "gap_pct_points": gap_pct_points,
        "matching_method": (
            "KOR start year = year minimising |KOR_GDPpc(year) - ARG_GDPpc(1991)|"
            f" over WDI NY.GDP.PCAP.KD; closest level was ${kor_start_val:,.0f} "
            f"in {kor_match_year} vs ARG {ARG_START} ${arg_start_val:,.0f}."
        ),
        "ppp_robustness": {
            "arg_log_growth_ppp": arg_ppp_lg,
            "kor_log_growth_ppp": kor_ppp_lg,
            "ppp_log_gap_kor_minus_arg": ppp_log_gap,
        },
        "supplementary_park_era_window": {
            "kor_window": [PARK_START, PARK_END],
            "kor_start_value": kor_park_start,
            "kor_end_value": kor_park_end,
            "kor_log_growth": kor_park_log,
            "kor_cum_pct": kor_park_pct,
            "log_gap_kor_minus_arg": park_log_gap,
            "note": (
                "Park Chung-hee developmental-state era (1962-1972). KOR "
                "starting GDP-pc was far below ARG 1991, so this is NOT a "
                "level-matched comparator; reported as a secondary check "
                "of the developmentalist canonical decade."
            ),
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    # Two indexed-to-100 trajectories aligned to year-0 (start of each window).
    arg_pts = []
    for offset in range(WINDOW_YEARS + 1):
        y = ARG_START + offset
        if y in arg.index:
            arg_pts.append({"x": offset, "y": float(arg[y] / arg_start_val * 100.0)})
    kor_pts = []
    for offset in range(WINDOW_YEARS + 1):
        y = kor_match_year + offset
        if y in kor.index:
            kor_pts.append({"x": offset, "y": float(kor[y] / kor_start_val * 100.0)})

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Real GDP per capita, indexed to 100 at decade start",
        "subtitle": (
            f"ARG {ARG_START}-{ARG_END} (Menem) vs KOR "
            f"{kor_match_year}-{kor_match_end_year} (matched on starting level). "
            f"Cumulative log-gap KOR-ARG = {log_gap:+.3f}."
        ),
        "type": "line",
        "x_axis": {"label": "Years since decade start", "type": "linear"},
        "y_axis": {"label": "Real GDP per capita (decade start = 100)", "type": "linear"},
        "series": [
            {
                "id": "ARG",
                "label": f"ARG {ARG_START}-{ARG_END}",
                "color": "#4E79A7",
                "treated": True,
                "points": arg_pts,
            },
            {
                "id": "KOR",
                "label": f"KOR {kor_match_year}-{kor_match_end_year}",
                "color": "#E15759",
                "treated": False,
                "points": kor_pts,
            },
        ],
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"ARG end-of-decade index: {arg_pts[-1]['y']:.1f}. "
                    f"KOR end-of-decade index: {kor_pts[-1]['y']:.1f}. "
                    f"SUPPORTED threshold: KOR-ARG cumulative log-growth >= +0.30."
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
            {"spec": "primary", "term": "arg_log_growth_91_01", "estimate": arg_log_growth},
            {"spec": "primary", "term": "kor_log_growth_matched_decade", "estimate": kor_log_growth},
            {"spec": "primary", "term": "log_gap_kor_minus_arg", "estimate": log_gap},
            {"spec": "primary", "term": "supported_threshold", "estimate": SUPPORTED_LOG_GAP},
            {"spec": "robustness_ppp", "term": "arg_log_growth_ppp",
             "estimate": float("nan") if arg_ppp_lg is None else arg_ppp_lg},
            {"spec": "robustness_ppp", "term": "kor_log_growth_ppp",
             "estimate": float("nan") if kor_ppp_lg is None else kor_ppp_lg},
            {"spec": "robustness_ppp", "term": "log_gap_kor_minus_arg_ppp",
             "estimate": float("nan") if ppp_log_gap is None else ppp_log_gap},
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

    ppp_line = (
        f"- PPP robustness (NY.GDP.PCAP.PP.KD): KOR-ARG log-gap = "
        f"{ppp_log_gap:+.3f}.\n"
        if ppp_log_gap is not None
        else "- PPP robustness: not available (series missing required years).\n"
    )
    park_line = (
        f"- Supplementary KOR Park-era 1962-1972 (low-base, NOT "
        f"level-matched): {kor_park_log:+.3f} log-points "
        f"({kor_park_pct:+.1f}%); KOR-ARG gap = {park_log_gap:+.3f}.\n"
        if park_log_gap is not None
        else "- Supplementary Park-era window: not available.\n"
    )

    card = (
        f"# Washington Consensus vs Developmental State performance\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Summary\n\n"
        f"- ARG {ARG_START}-{ARG_END} (Menem-era convertibility & "
        f"privatisation): real GDP-pc went ${arg_start_val:,.0f} -> "
        f"${arg_end_val:,.0f} (constant 2015 USD), cumulative "
        f"{arg_log_growth:+.3f} log-points ({arg_pct:+.1f}%).\n"
        f"- KOR matched decade {kor_match_year}-{kor_match_end_year} "
        f"(starting GDP-pc closest to ARG {ARG_START} level): "
        f"${kor_start_val:,.0f} -> ${kor_end_val:,.0f}, cumulative "
        f"{kor_log_growth:+.3f} log-points ({kor_pct:+.1f}%).\n"
        f"- Cumulative log-growth gap KOR - ARG = "
        f"**{log_gap:+.3f} log-points** ({gap_pct_points:+.1f}pp).\n"
        f"- SUPPORTED threshold: gap >= +0.30 log-points (~+35pp). "
        f"{'Met.' if log_gap >= SUPPORTED_LOG_GAP else 'Not met.'}\n"
        f"{ppp_line}"
        f"{park_line}"
        f"\n## Method\n\n"
        f"Bilateral matched-decade comparison. ARG window is fixed to "
        f"the Menem convertibility era 1991-2001 (the spec's "
        f"treatment-tag window). The KOR \"comparable decade\" is "
        f"chosen by matching on starting real GDP-pc level: KOR start "
        f"year = the year minimising |KOR GDP-pc(year) - ARG GDP-pc(1991)|, "
        f"using WDI NY.GDP.PCAP.KD (constant 2015 USD). The KOR window "
        f"then spans [match_year, match_year+10] to mirror ARG's "
        f"horizon. This is the descriptive approach the developmentalist "
        f"claim invites: \"compare like-for-like starting levels and "
        f"see which growth model produced more cumulative real income.\"\n\n"
        f"Cumulative growth is reported in natural logs (additive, "
        f"crisis-symmetric: a 50% boom and 50% bust net to roughly zero). "
        f"PPP-based GDP-pc is computed in parallel as a robustness panel "
        f"but does not gate the verdict (PPP coverage starts in 1990 "
        f"so it cannot anchor a 1960s/70s KOR window).\n\n"
        f"### Steelman of the alternative reading\n\n"
        f"The market-liberal counter-frame would protest that the ARG "
        f"2001 collapse was driven by the convertibility regime's fixed "
        f"peg (a Washington Consensus *deviation*: real liberal advice "
        f"was a flexible exchange rate), not by privatisation per se. "
        f"On that reading the comparison conflates two policies. This "
        f"replication intentionally keeps the developmentalist framing "
        f"as written in the spec: the matched-decade test is on the "
        f"observed Argentine policy bundle as actually implemented, not "
        f"on a counterfactual Washington Consensus.\n\n"
        f"## Data\n\n"
        f"- world_bank_wdi:NY.GDP.PCAP.KD (constant 2015 USD)\n"
        f"- world_bank_wdi:NY.GDP.PCAP.PP.KD (PPP, robustness only)\n"
    )
    (OUT_DIR / "result_card.md").write_text(card)

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
