#!/usr/bin/env python3
"""Replication — soviet_industrial_catch_up_1928_1940 (v1).

Spec: hypotheses/growth/soviet_industrial_catch_up_1928_1940.yaml
Position-claim: marxist_leninist #2 (school predicts: supported)

CLAIM. Under the first two Five-Year Plans (1928-1940), Soviet output
grew measurably faster than the Western European average — a
"primitive socialist accumulation" catch-up.

PRIMARY TEST (dispositive). Cumulative log-growth differential of
Maddison MPD2020 real GDP (gdppc x pop, 2011 PPP$) for the USSR
(country_iso3 = SUN where present, else RUS) over 1928 -> 1940
versus the simple mean of cumulative log-growth across the Western
European comparator panel (GBR, DEU, FRA, ITA). Hypothesis SUPPORTED
if the differential >= +0.50 log points (~+65% advantage), per the
spec's pre-registered falsification threshold. REFUTED if the USSR
trails the WE-mean (differential < 0). PARTIAL between 0 and +0.50.

INFORMATIVE. (a) Same comparison against a USA + WE-mean panel —
the 1930s Western base was depressed by the Great Depression, so the
WE-only number is flattering; the US makes the comparison harder.
(b) JST jst_r6 industrial-production index ('iy') cumulative
log-growth for the WE+USA panel 1928 -> 1940 — RUS is NOT in JST
(17 advanced economies only), so a like-for-like industrial-output
comparison cannot be done from the parquet vintages. The
disclosure note in the spec already flags this; the JST numbers
contextualise what the WE comparators were doing in industrial
production specifically.

METHOD-VALIDITY GATE. Both endpoint years (1928 and 1940) must be
present in Maddison for SUN/RUS and for at least 3 of the 4 WE
comparators. If not, emit `inconclusive (data gap on
maddison:mpd2020)` and stop.

CAVEATS the script does NOT correct for. The USSR Maddison series
for 1928-40 is itself the Davies-Wheatcroft / Markevich-Harrison
reconstruction debate output — it is not an independent measurement.
The 1930s WE comparators were in the Great Depression for most of
the window, depressing the denominator. The famine cost (1932-33
Soviet famine), gulag forced labour, and consumption collapse are
not in this descriptive headline. These are noted in the result_card
and in the YAML's `disclosure` field; they do not enter the verdict
arithmetic.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "soviet_industrial_catch_up_1928_1940"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1928, 1940)
SOVIET_CODES = ["SUN", "RUS"]  # try SUN first (Soviet Union), fall back to RUS
WE_COMPARATORS = ["GBR", "DEU", "FRA", "ITA"]
USA = "USA"
JST_PANEL = ["GBR", "DEU", "FRA", "ITA", "USA"]

# Falsification thresholds (from spec.falsification.test, made dispositive)
PRIMARY_LOG_DIFFERENTIAL_THRESHOLD = 0.50  # USSR cum log-growth > WE-mean by >= 0.50 log
PARTIAL_LOWER = 0.0  # any positive differential is "partial"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, prefix: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{prefix}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{prefix}")
    return files[-1]


def load_maddison(path: Path) -> pd.DataFrame:
    """Maddison MPD2020. Columns: country_iso3, year, gdppc, pop.
    We compute total real GDP = gdppc * pop (2011 PPP $)."""
    t = pq.read_table(path).to_pandas()
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    keep = [c for c in ("country_iso3", "year", "gdppc", "pop") if c in t.columns]
    t = t[keep].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["gdppc"] = pd.to_numeric(t["gdppc"], errors="coerce")
    if "pop" in t.columns:
        t["pop"] = pd.to_numeric(t["pop"], errors="coerce")
    t = t.dropna(subset=["year", "gdppc"])
    t["year"] = t["year"].astype(int)
    if "pop" in t.columns:
        t["gdp"] = t["gdppc"] * t["pop"]
    else:
        t["gdp"] = np.nan
    return t.rename(columns={"country_iso3": "country"})


def load_jst(path: Path) -> pd.DataFrame:
    """JST R6. Wide-format; long-run macrofinancial. We need 'iy'
    (industrial production index) and country_iso3 + year."""
    t = pq.read_table(path).to_pandas()
    keep = [c for c in ("country_iso3", "year", "iy") if c in t.columns]
    if "iy" not in keep:
        # Some vintages may use a different column name; flag and bail.
        return pd.DataFrame(columns=["country", "year", "iy"])
    t = t[keep].copy()
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)]
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["iy"] = pd.to_numeric(t["iy"], errors="coerce")
    t = t.dropna(subset=["year", "iy"])
    t["year"] = t["year"].astype(int)
    return t.rename(columns={"country_iso3": "country"})


def cum_log_growth(series_by_year: pd.Series, y0: int, y1: int) -> float | None:
    if y0 not in series_by_year.index or y1 not in series_by_year.index:
        return None
    a = float(series_by_year.loc[y0])
    b = float(series_by_year.loc[y1])
    if a <= 0 or b <= 0:
        return None
    return float(np.log(b) - np.log(a))


def annualised_pct(cum_log: float, years: int) -> float:
    return float((np.exp(cum_log / years) - 1) * 100)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mpath = latest("maddison", "mpd2020")
    jpath = latest("jst", "jst_r6")
    manifest = {
        "real_gdp_long_run": {
            "publisher": "maddison",
            "series": "mpd2020",
            "vintage_file": str(mpath.relative_to(REPO_ROOT)),
            "sha256": sha256(mpath),
        },
        "industrial_production_index_jst": {
            "publisher": "jst",
            "series": "jst_r6",
            "vintage_file": str(jpath.relative_to(REPO_ROOT)),
            "sha256": sha256(jpath),
        },
    }

    md = load_maddison(mpath)
    jst = load_jst(jpath)

    # ---------- USSR endpoints (Maddison) ----------
    soviet_used = None
    soviet_endpoints = None
    for code in SOVIET_CODES:
        sub = md[md["country"] == code].set_index("year")["gdp"].sort_index()
        if PERIOD[0] in sub.index and PERIOD[1] in sub.index:
            soviet_used = code
            soviet_endpoints = (float(sub.loc[PERIOD[0]]), float(sub.loc[PERIOD[1]]))
            break

    # ---------- WE comparator endpoints ----------
    we_endpoints: dict[str, tuple[float, float]] = {}
    we_cum_logs: dict[str, float] = {}
    for c in WE_COMPARATORS:
        sub = md[md["country"] == c].set_index("year")["gdp"].sort_index()
        cl = cum_log_growth(sub, PERIOD[0], PERIOD[1])
        if cl is not None:
            we_endpoints[c] = (float(sub.loc[PERIOD[0]]), float(sub.loc[PERIOD[1]]))
            we_cum_logs[c] = cl

    # USA endpoint
    sub_usa = md[md["country"] == USA].set_index("year")["gdp"].sort_index()
    usa_cum_log = cum_log_growth(sub_usa, PERIOD[0], PERIOD[1])
    usa_endpoints = None
    if usa_cum_log is not None:
        usa_endpoints = (float(sub_usa.loc[PERIOD[0]]), float(sub_usa.loc[PERIOD[1]]))

    # Method-validity gate
    METHOD_MIN_WE = 3  # need at least 3 of 4 WE comparators
    method_valid = (
        soviet_endpoints is not None and len(we_cum_logs) >= METHOD_MIN_WE
    )

    if not method_valid:
        missing_parts = []
        if soviet_endpoints is None:
            missing_parts.append(f"USSR endpoints in {SOVIET_CODES}")
        if len(we_cum_logs) < METHOD_MIN_WE:
            missing_parts.append(
                f"WE comparators with both endpoints "
                f"({sorted(we_cum_logs)} of {WE_COMPARATORS})"
            )
        verdict = (
            "inconclusive (data gap on maddison:mpd2020) — missing: "
            + "; ".join(missing_parts)
            + f". Cannot evaluate {PERIOD[0]}->{PERIOD[1]} cum-log differential."
        )
        diagnostics = {
            "verdict": verdict,
            "method_valid": False,
            "soviet_used": soviet_used,
            "we_with_data": sorted(we_cum_logs),
            "period": list(PERIOD),
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        # Minimal stubs for the other artifacts so the agent contract is met.
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "estimator": "descriptive",
            "vintages": manifest,
            "notes": "data-gap inconclusive — see diagnostics.json",
        }, sort_keys=False))
        pd.DataFrame([{"spec": "primary", "term": "log_differential_USSR_minus_WE", "estimate": np.nan}]).to_parquet(
            OUT_DIR / "coefficients.parquet", index=False
        )
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1",
            "title": "Soviet 1928-1940 catch-up (data gap)",
            "subtitle": verdict, "type": "line",
            "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "log GDP (1928 = 0)", "type": "linear"},
            "series": [], "annotations": [],
            "sources": [{"publisher_id": v["publisher"], "series_id": v["series"],
                         "vintage_file": v["vintage_file"]} for v in manifest.values()],
            "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# Soviet industrial catch-up, 1928-1940\n\n**Verdict:** {verdict}\n"
        )
        print(f"verdict: {verdict}")
        return 0

    # ---------- PRIMARY statistic ----------
    soviet_cum_log = float(np.log(soviet_endpoints[1]) - np.log(soviet_endpoints[0]))
    we_mean_cum_log = float(np.mean(list(we_cum_logs.values())))
    primary_differential = soviet_cum_log - we_mean_cum_log

    # USSR vs USA (informative)
    usa_differential = (
        soviet_cum_log - usa_cum_log if usa_cum_log is not None else None
    )

    # USSR vs (WE + USA) panel mean (informative — harder denominator)
    we_plus_usa = dict(we_cum_logs)
    if usa_cum_log is not None:
        we_plus_usa[USA] = usa_cum_log
    we_plus_usa_mean = float(np.mean(list(we_plus_usa.values())))
    we_plus_usa_differential = soviet_cum_log - we_plus_usa_mean

    # ---------- INFORMATIVE: JST industrial production for WE+USA ----------
    jst_iy_cum_logs: dict[str, float] = {}
    for c in JST_PANEL:
        sub = jst[jst["country"] == c].set_index("year")["iy"].sort_index()
        cl = cum_log_growth(sub, PERIOD[0], PERIOD[1])
        if cl is not None:
            jst_iy_cum_logs[c] = cl
    jst_iy_panel_mean = (
        float(np.mean(list(jst_iy_cum_logs.values()))) if jst_iy_cum_logs else None
    )
    jst_we_iy_cum_logs = {c: v for c, v in jst_iy_cum_logs.items() if c in WE_COMPARATORS}
    jst_we_iy_mean = (
        float(np.mean(list(jst_we_iy_cum_logs.values()))) if jst_we_iy_cum_logs else None
    )

    n_years = PERIOD[1] - PERIOD[0]
    soviet_ann_pct = annualised_pct(soviet_cum_log, n_years)
    we_mean_ann_pct = annualised_pct(we_mean_cum_log, n_years)

    # ---------- Verdict ----------
    if primary_differential >= PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:
        verdict = (
            f"SUPPORTED — USSR ({soviet_used}) cumulative log-growth of real GDP "
            f"{PERIOD[0]}->{PERIOD[1]} is {soviet_cum_log:+.3f} "
            f"({soviet_ann_pct:+.2f}%/yr); WE-mean ({', '.join(sorted(we_cum_logs))}) "
            f"is {we_mean_cum_log:+.3f} ({we_mean_ann_pct:+.2f}%/yr); "
            f"differential {primary_differential:+.3f} clears the +{PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:.2f} threshold. "
            f"Caveat: WE base is Great-Depression-depressed and Maddison's USSR "
            f"series is itself a reconstruction; see result_card."
        )
    elif primary_differential > PARTIAL_LOWER:
        verdict = (
            f"partial — USSR cum-log growth {soviet_cum_log:+.3f} exceeds "
            f"WE-mean {we_mean_cum_log:+.3f} (differential {primary_differential:+.3f}) "
            f"but falls short of the +{PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:.2f} log "
            f"threshold the spec requires. Direction of the claim holds; magnitude does not."
        )
    else:
        verdict = (
            f"refuted — USSR cum-log growth {soviet_cum_log:+.3f} does NOT exceed "
            f"WE-mean {we_mean_cum_log:+.3f} (differential {primary_differential:+.3f}). "
            f"The Marxist-Leninist primitive-accumulation claim of measurable "
            f"out-performance fails its pre-registered test."
        )

    # ---------- diagnostics ----------
    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "primary_differential_log": primary_differential,
        "primary_threshold_log": PRIMARY_LOG_DIFFERENTIAL_THRESHOLD,
        "primary_pass": primary_differential >= PRIMARY_LOG_DIFFERENTIAL_THRESHOLD,
        "direction_pass": primary_differential > 0,
        "soviet_country_used": soviet_used,
        "soviet_cum_log_growth": soviet_cum_log,
        "soviet_annualised_pct": soviet_ann_pct,
        "soviet_gdp_1928": soviet_endpoints[0],
        "soviet_gdp_1940": soviet_endpoints[1],
        "we_comparator_cum_logs": we_cum_logs,
        "we_mean_cum_log": we_mean_cum_log,
        "we_mean_annualised_pct": we_mean_ann_pct,
        "usa_cum_log": usa_cum_log,
        "usa_differential_log": usa_differential,
        "we_plus_usa_mean_cum_log": we_plus_usa_mean,
        "we_plus_usa_differential_log": we_plus_usa_differential,
        "jst_iy_cum_logs_we_plus_usa": jst_iy_cum_logs,
        "jst_iy_we_panel_mean_cum_log": jst_we_iy_mean,
        "jst_iy_we_plus_usa_mean_cum_log": jst_iy_panel_mean,
        "jst_iy_ussr_cum_log": None,
        "jst_iy_ussr_data_gap_note": (
            "JST R6 covers 17 advanced economies — USSR/RUS not in panel; "
            "industrial-production like-for-like comparison cannot be done. "
            "Maddison total real GDP is the operational primary."
        ),
        "period": list(PERIOD),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- coefficients ----------
    rows = [
        {"spec": "primary", "term": "log_differential_USSR_minus_WE_mean", "estimate": primary_differential},
        {"spec": "primary", "term": "soviet_cum_log_1928_1940", "estimate": soviet_cum_log},
        {"spec": "primary", "term": "we_mean_cum_log_1928_1940", "estimate": we_mean_cum_log},
        {"spec": "informative", "term": "usa_cum_log_1928_1940", "estimate": usa_cum_log if usa_cum_log is not None else float("nan")},
        {"spec": "informative", "term": "log_differential_USSR_minus_USA", "estimate": usa_differential if usa_differential is not None else float("nan")},
        {"spec": "informative", "term": "log_differential_USSR_minus_WE_plus_USA_mean", "estimate": we_plus_usa_differential},
        {"spec": "informative", "term": "jst_iy_we_panel_mean_cum_log_1928_1940", "estimate": jst_we_iy_mean if jst_we_iy_mean is not None else float("nan")},
    ]
    for c, v in we_cum_logs.items():
        rows.append({"spec": "country_we_gdp", "term": f"cum_log_{c}", "estimate": v})
    for c, v in jst_iy_cum_logs.items():
        rows.append({"spec": "country_iy_jst", "term": f"cum_log_iy_{c}", "estimate": v})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- chart_data ----------
    palette = ["#E15759", "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2", "#9C755F"]
    series = []
    # USSR series
    sub_sov = md[md["country"] == soviet_used].set_index("year")["gdp"].sort_index()
    sov_pts = []
    base_log = np.log(soviet_endpoints[0])
    for y in range(PERIOD[0], PERIOD[1] + 1):
        if y in sub_sov.index and float(sub_sov.loc[y]) > 0:
            sov_pts.append({"x": int(y), "y": float(np.log(sub_sov.loc[y]) - base_log)})
    series.append({
        "id": soviet_used, "label": f"USSR ({soviet_used})", "color": palette[0],
        "treated": True, "points": sov_pts,
    })
    # WE comparators
    for i, c in enumerate(sorted(we_cum_logs)):
        sub = md[md["country"] == c].set_index("year")["gdp"].sort_index()
        base_we = np.log(we_endpoints[c][0])
        pts = []
        for y in range(PERIOD[0], PERIOD[1] + 1):
            if y in sub.index and float(sub.loc[y]) > 0:
                pts.append({"x": int(y), "y": float(np.log(sub.loc[y]) - base_we)})
        series.append({
            "id": c, "label": c, "color": palette[(i + 1) % len(palette)],
            "treated": False, "points": pts,
        })
    # USA
    if usa_endpoints is not None:
        base_usa = np.log(usa_endpoints[0])
        pts = []
        for y in range(PERIOD[0], PERIOD[1] + 1):
            if y in sub_usa.index and float(sub_usa.loc[y]) > 0:
                pts.append({"x": int(y), "y": float(np.log(sub_usa.loc[y]) - base_usa)})
        series.append({
            "id": "USA", "label": "USA", "color": "#1f1f1f",
            "treated": False, "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Cumulative log real-GDP growth, 1928 = 0 (Maddison MPD2020)",
        "subtitle": (
            f"USSR ({soviet_used}) {soviet_cum_log:+.3f} log "
            f"({soviet_ann_pct:+.2f}%/yr) vs WE-mean {we_mean_cum_log:+.3f} "
            f"({we_mean_ann_pct:+.2f}%/yr); differential {primary_differential:+.3f} "
            f"vs threshold +{PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:.2f}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log real GDP, 1928 = 0", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "note", "label": (
                "Maddison's USSR series for 1928-40 is itself the Davies-"
                "Wheatcroft / Markevich-Harrison reconstruction; the WE base "
                "is depressed by the Great Depression. Famine 1932-33, gulag "
                "labour and consumption collapse are not in this headline."
            )}
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- manifest ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "descriptive",
        "vintages": manifest,
        "notes": (
            "Maddison MPD2020 total real GDP (gdppc * pop, 2011 PPP $) is "
            "the operational primary. JST industrial-production index ('iy') "
            "is reported for the WE+USA panel only — JST does not include "
            "USSR/RUS (17 advanced economies). USSR figure pulled from "
            f"country_iso3 = {soviet_used} (tried {SOVIET_CODES} in order)."
        ),
    }, sort_keys=False))

    # ---------- result_card ----------
    we_rows = []
    for c in sorted(we_cum_logs):
        we_rows.append(
            f"| {c} | {we_endpoints[c][0]:>14,.0f} | {we_endpoints[c][1]:>14,.0f} | "
            f"{we_cum_logs[c]:+.3f} | {annualised_pct(we_cum_logs[c], n_years):+.2f}% |"
        )
    jst_rows = []
    for c in sorted(jst_iy_cum_logs):
        jst_rows.append(
            f"| {c} | {jst_iy_cum_logs[c]:+.3f} | {annualised_pct(jst_iy_cum_logs[c], n_years):+.2f}% |"
        )
    if not jst_rows:
        jst_rows = ["| — | — | — |"]

    lines = [
        "# Soviet industrial catch-up, 1928–1940",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Series: Maddison MPD2020 total real GDP = `gdppc x pop` (2011 PPP $).",
        f"- USSR (`{soviet_used}`) GDP {PERIOD[0]} → {PERIOD[1]}: "
        f"`{soviet_endpoints[0]:,.0f}` → `{soviet_endpoints[1]:,.0f}` "
        f"(cumulative {soviet_cum_log:+.3f} log; annualised {soviet_ann_pct:+.2f}%/yr).",
        f"- WE comparator panel ({', '.join(sorted(we_cum_logs))}) mean cumulative log-growth: "
        f"`{we_mean_cum_log:+.3f}` (annualised `{we_mean_ann_pct:+.2f}%/yr`).",
        f"- USA cumulative log-growth: "
        f"`{usa_cum_log:+.3f}` (annualised `{annualised_pct(usa_cum_log, n_years):+.2f}%/yr`)."
        if usa_cum_log is not None else "- USA: data missing.",
        f"- **Primary differential** (USSR – WE-mean): "
        f"`{primary_differential:+.3f}` log points "
        f"(threshold ≥ +{PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:.2f}).",
        f"- Differential vs WE+USA mean: `{we_plus_usa_differential:+.3f}` log points "
        f"(harder denominator — US was largely insulated from WE Depression timing).",
        "",
        "## WE comparator trajectories 1928 → 1940 (Maddison)",
        "",
        "| Country | GDP 1928 | GDP 1940 | cum log | annualised |",
        "|---|---:|---:|---:|---:|",
        *we_rows,
        "",
        "## JST industrial-production index (WE+USA only — RUS not in panel)",
        "",
        "| Country | cum log iy | annualised |",
        "|---|---:|---:|",
        *jst_rows,
        "",
        f"WE-only JST `iy` panel mean: "
        f"`{(f'{jst_we_iy_mean:+.3f}' if jst_we_iy_mean is not None else 'NA')}`. "
        f"WE+USA JST `iy` panel mean: "
        f"`{(f'{jst_iy_panel_mean:+.3f}' if jst_iy_panel_mean is not None else 'NA')}`. "
        "JST has no USSR row, so a strict industrial-production "
        "like-for-like comparison cannot be made from the parquet vintages.",
        "",
        "## Threshold applied",
        "",
        f"- PRIMARY: `cum_log(USSR, 1928→1940) − mean(cum_log(WE, 1928→1940)) "
        f">= {PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:.2f}`.",
        "- PARTIAL: differential positive but below threshold (direction holds, magnitude does not).",
        "- REFUTED: differential ≤ 0.",
        "",
        "## Caveats not adjusted for in the headline",
        "",
        "- Maddison's USSR series for 1928-40 is itself the "
        "  Davies-Wheatcroft / Markevich-Harrison reconstruction debate "
        "  output, not an independent measurement. Different reconstructions "
        "  give USSR 1928→1940 log growth between roughly +0.7 and +1.0; "
        "  treat the level as load-bearing only at one significant figure.",
        "- The WE base is the Great Depression. Picking 1928 = peak and "
        "  1940 = early-rearmament-recovery flatters any "
        "  fast-industrialiser comparison; a 1928→1937 window narrows the gap.",
        "- The 1932-33 famine, gulag labour, and consumption collapse "
        "  (real wages, retail goods availability) are not in the headline. "
        "  The claim is *output growth*, not *welfare growth*; this run "
        "  scores the literal claim, not the broader policy verdict.",
        "",
        "## Sources",
        "",
        f"- Maddison Project Database 2020 (vintage `{Path(manifest['real_gdp_long_run']['vintage_file']).name}`).",
        f"- Jordà-Schularick-Taylor R6 (vintage `{Path(manifest['industrial_production_index_jst']['vintage_file']).name}`) — WE+USA only.",
        "",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  USSR cum log {PERIOD[0]}-{PERIOD[1]}: {soviet_cum_log:+.3f} ({soviet_ann_pct:+.2f}%/yr)")
    print(f"  WE-mean cum log: {we_mean_cum_log:+.3f} ({we_mean_ann_pct:+.2f}%/yr)")
    print(f"  Primary differential: {primary_differential:+.3f} (threshold +{PRIMARY_LOG_DIFFERENTIAL_THRESHOLD:.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
