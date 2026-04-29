#!/usr/bin/env python3
"""Replication — Keynes 1930 'Possibilities for Our Grandchildren' growth-target check.

Spec: hypotheses/growth/keynes_1930_growth_targets_actually_met.yaml v1
Position-claim: degrowth #13 (school predicts: supported)

Keynes (1930) projected that per-capita output in advanced economies would
multiply 4-8x within "a hundred years" — i.e. by 2030 — making the
"economic problem" of subsistence essentially solved.

This descriptive replication tests whether the lower-bound (4x) Keynes
projection has been met using long-run Maddison real GDP per capita
(2011 PPP$) for an OECD-style panel of 18 advanced economies, comparing
1930 -> latest available year (typically 2018 in Maddison MPD2020).

PRIMARY (dispositive): the population-weighted mean ratio of real
GDP per capita (latest_year / 1930) across the panel must be >= 4.0
for the claim to be SUPPORTED.

Secondary (informative): the equal-weighted country mean ratio, and
the share of countries individually crossing the 4x threshold. These
colour the verdict but do not gate it.
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
HID = "keynes_1930_growth_targets_actually_met"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from the spec
COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "NLD", "BEL", "AUT", "SWE", "NOR",
    "DNK", "FIN", "IRL", "JPN", "CAN", "AUS", "NZL", "CHE",
]
ANCHOR_YEAR = 1930

# Falsification thresholds (made dispositive)
KEYNES_LOWER_BOUND = 4.0   # 4x — the lower of Keynes's 4-8x projection
KEYNES_UPPER_BOUND = 8.0   # 8x — for informative reporting only
METHOD_MIN = 14            # min countries with both endpoints for a valid run


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
    t = pq.read_table(path).to_pandas()
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    out = t[["country_iso3", "year", "gdppc", "pop"]].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out["gdppc"] = pd.to_numeric(out["gdppc"], errors="coerce")
    out["pop"] = pd.to_numeric(out["pop"], errors="coerce")
    out = out.dropna(subset=["year", "gdppc"])
    out["year"] = out["year"].astype(int)
    return out.rename(columns={"country_iso3": "country"})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    mpath = latest("maddison", "mpd2020")
    manifest = {
        "gdp_pc_ppp_2011": {
            "publisher": "maddison",
            "series": "mpd2020",
            "vintage_file": str(mpath.relative_to(REPO_ROOT)),
            "sha256": sha256(mpath),
        },
    }

    df = load_maddison(mpath)
    panel = df[df["country"].isin(COUNTRIES)].copy()

    # Find the latest year for which most panel countries have data
    # Maddison MPD2020 typically ends 2018.
    latest_year = int(panel["year"].max())

    # Per-country gdppc at anchor and latest
    rows = {}
    for c in COUNTRIES:
        sub = panel[panel["country"] == c].set_index("year")
        anchor = float(sub.loc[ANCHOR_YEAR, "gdppc"]) if ANCHOR_YEAR in sub.index else None
        end = float(sub.loc[latest_year, "gdppc"]) if latest_year in sub.index else None
        # Use end-year population as the weight (proxy for population-weighted mean)
        pop_end = float(sub.loc[latest_year, "pop"]) if (latest_year in sub.index and "pop" in sub.columns) else None
        ratio = (end / anchor) if (anchor and end and anchor > 0) else None
        rows[c] = {
            "gdppc_1930": anchor,
            f"gdppc_{latest_year}": end,
            "ratio": ratio,
            "pop_end": pop_end,
        }

    have_data = [c for c in COUNTRIES if rows[c]["ratio"] is not None]
    method_valid = len(have_data) >= METHOD_MIN

    ratios = np.array([rows[c]["ratio"] for c in have_data], dtype=float)
    pops = np.array([rows[c]["pop_end"] or 0.0 for c in have_data], dtype=float)
    n_above_4x = int((ratios >= KEYNES_LOWER_BOUND).sum())
    n_above_8x = int((ratios >= KEYNES_UPPER_BOUND).sum())
    n_total = len(have_data)

    equal_mean_ratio = float(ratios.mean()) if n_total else float("nan")
    median_ratio = float(np.median(ratios)) if n_total else float("nan")
    if pops.sum() > 0:
        pop_weighted_ratio = float((ratios * pops).sum() / pops.sum())
    else:
        pop_weighted_ratio = float("nan")

    # PRIMARY test
    primary_pass = (not np.isnan(pop_weighted_ratio)) and (pop_weighted_ratio >= KEYNES_LOWER_BOUND)
    share_above_4x = (n_above_4x / n_total) if n_total else float("nan")

    if not method_valid:
        verdict = (
            f"inconclusive (data gap on maddison:mpd2020) — only {n_total} of "
            f"{len(COUNTRIES)} panel countries have both 1930 and {latest_year} "
            f"observations; need >= {METHOD_MIN}."
        )
    elif primary_pass:
        verdict = (
            f"SUPPORTED — Population-weighted mean ratio of real GDP per capita "
            f"({latest_year}/1930) across the {n_total}-country OECD panel is "
            f"{pop_weighted_ratio:.2f}x, above Keynes's lower bound of "
            f"{KEYNES_LOWER_BOUND:.0f}x. {n_above_4x}/{n_total} countries individually "
            f"meet the 4x threshold; {n_above_8x}/{n_total} also clear the 8x upper bound."
        )
    else:
        if pop_weighted_ratio >= KEYNES_LOWER_BOUND * 0.5:
            verdict = (
                f"partial — Population-weighted mean ratio is {pop_weighted_ratio:.2f}x, "
                f"below Keynes's {KEYNES_LOWER_BOUND:.0f}x lower bound but above half "
                f"that threshold. {n_above_4x}/{n_total} countries individually clear 4x."
            )
        else:
            verdict = (
                f"refuted — Population-weighted mean ratio is {pop_weighted_ratio:.2f}x, "
                f"materially below Keynes's {KEYNES_LOWER_BOUND:.0f}x lower bound. Only "
                f"{n_above_4x}/{n_total} countries individually cleared 4x."
            )

    diagnostics = {
        "verdict": verdict,
        "anchor_year": ANCHOR_YEAR,
        "latest_year": latest_year,
        "primary_pass": bool(primary_pass),
        "method_valid": bool(method_valid),
        "keynes_lower_bound": KEYNES_LOWER_BOUND,
        "keynes_upper_bound": KEYNES_UPPER_BOUND,
        "pop_weighted_ratio": pop_weighted_ratio,
        "equal_weighted_mean_ratio": equal_mean_ratio,
        "median_ratio": median_ratio,
        "n_above_4x": n_above_4x,
        "n_above_8x": n_above_8x,
        "n_with_both_endpoints": n_total,
        "share_above_4x": share_above_4x,
        "country_ratios": {c: rows[c]["ratio"] for c in COUNTRIES},
        "country_endpoints": {
            c: {
                "gdppc_1930": rows[c]["gdppc_1930"],
                f"gdppc_{latest_year}": rows[c][f"gdppc_{latest_year}"],
            }
            for c in COUNTRIES
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    coeff_rows = [
        {"spec": "primary", "term": "pop_weighted_ratio", "estimate": pop_weighted_ratio},
        {"spec": "primary", "term": "threshold_lower_bound", "estimate": KEYNES_LOWER_BOUND},
        {"spec": "informative", "term": "equal_weighted_mean_ratio", "estimate": equal_mean_ratio},
        {"spec": "informative", "term": "median_ratio", "estimate": median_ratio},
        {"spec": "informative", "term": "share_above_4x", "estimate": share_above_4x},
        {"spec": "informative", "term": "n_above_8x", "estimate": float(n_above_8x)},
    ]
    for c in COUNTRIES:
        r = rows[c]["ratio"]
        if r is not None:
            coeff_rows.append({"spec": "country_ratio", "term": c, "estimate": float(r)})
    pd.DataFrame(coeff_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # Chart — country trajectories indexed to 1930 + 4x reference line
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
        "#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99", "#FDBF6F",
    ]
    series = []
    for i, c in enumerate(COUNTRIES):
        sub = panel[panel["country"] == c].sort_values("year")
        if sub.empty:
            continue
        anchor = rows[c]["gdppc_1930"]
        if not anchor or anchor <= 0:
            continue
        pts = [
            {"x": int(r.year), "y": float(r.gdppc / anchor)}
            for r in sub.itertuples()
            if r.year >= ANCHOR_YEAR
        ]
        series.append({
            "id": c,
            "label": c,
            "color": palette[i % len(palette)],
            "treated": False,
            "points": pts,
        })

    threshold_line = [
        {"x": ANCHOR_YEAR, "y": KEYNES_LOWER_BOUND},
        {"x": latest_year, "y": KEYNES_LOWER_BOUND},
    ]
    series.insert(0, {
        "id": "KEYNES_4X",
        "label": "Keynes lower bound (4x)",
        "color": "#1f1f1f",
        "treated": True,
        "points": threshold_line,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": f"OECD-panel real GDP per capita, indexed to 1930 (=1.0)",
        "subtitle": (
            f"Pop-weighted mean ratio {latest_year}/1930 = {pop_weighted_ratio:.2f}x · "
            f"{n_above_4x}/{n_total} countries clear Keynes's 4x lower bound."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "GDP per capita (1930 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Keynes (1930) projected 4-8x growth in per-capita output by "
                    f"~2030. Maddison MPD2020 ends in {latest_year}. Pop-weighted "
                    f"mean ratio = {pop_weighted_ratio:.2f}x; equal-weighted mean = "
                    f"{equal_mean_ratio:.2f}x; median = {median_ratio:.2f}x."
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

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "descriptive",
        "vintages": manifest,
        "notes": (
            f"Maddison MPD2020 GDP per capita (2011 PPP$). Anchor year {ANCHOR_YEAR}, "
            f"latest available year {latest_year} (MPD2020 series ends in 2018). "
            "Primary statistic is the population-weighted mean of country-level "
            "(latest/1930) ratios across the 18-country OECD-style panel; threshold "
            "is Keynes's 4x lower bound."
        ),
    }, sort_keys=False))

    table_rows = []
    for c in sorted(have_data, key=lambda c: -(rows[c]["ratio"] or 0)):
        r = rows[c]
        table_rows.append(
            f"| {c} | {r['gdppc_1930']:>7,.0f} | "
            f"{r[f'gdppc_{latest_year}']:>7,.0f} | {r['ratio']:>5.2f}x | "
            f"{'yes' if r['ratio'] >= KEYNES_LOWER_BOUND else 'no'} |"
        )
    missing = [c for c in COUNTRIES if rows[c]["ratio"] is None]

    card = [
        f"# Keynes 1930 'Possibilities for Our Grandchildren' growth-target check",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Anchor year **1930**, latest year **{latest_year}** (Maddison MPD2020).",
        f"- Population-weighted mean ratio (latest/1930): "
        f"**{pop_weighted_ratio:.2f}x**.",
        f"- Equal-weighted country mean: **{equal_mean_ratio:.2f}x**; "
        f"median **{median_ratio:.2f}x**.",
        f"- {n_above_4x} of {n_total} countries individually clear Keynes's "
        f"4x lower bound; {n_above_8x} also clear his 8x upper bound.",
        "",
        "## Threshold applied",
        "",
        "- PRIMARY (dispositive): population-weighted mean of "
        "(GDP-pc[latest] / GDP-pc[1930]) across the 18-country panel "
        f">= **{KEYNES_LOWER_BOUND:.0f}x** (Keynes's lower bound).",
        "- INFORMATIVE: equal-weighted mean, median, share of countries "
        ">= 4x, count of countries >= 8x (upper bound).",
        f"- METHOD_VALID: at least {METHOD_MIN} of {len(COUNTRIES)} panel "
        "countries observed at both endpoints — "
        f"{'pass' if method_valid else 'FAIL'} ({n_total}/{len(COUNTRIES)}).",
        "",
        "## Per-country ratios (Maddison 2011 PPP $)",
        "",
        f"| Country | GDP-pc 1930 | GDP-pc {latest_year} | ratio | >=4x? |",
        "|---|---:|---:|---:|:---:|",
        *table_rows,
        "",
        "## Method",
        "",
        "Long-run descriptive comparison. For each panel country with "
        "Maddison MPD2020 observations at both 1930 and the dataset's "
        f"latest year ({latest_year}), compute the per-capita GDP ratio "
        "in 2011 PPP $. Aggregate across countries by:",
        "",
        f"1. Population-weighted mean (weights: end-year population); "
        "this is the dispositive primary statistic.",
        "2. Equal-weighted country mean; reported as informative cross-check.",
        "3. Median; informative for skew.",
        "",
        "Maddison MPD2020 is the only published source that covers 1930 "
        "for the full advanced-economy panel; the WDI series "
        "`NY.GDP.PCAP.KD` only starts in 1960. The spec's secondary WDI "
        "series is therefore not used in this primary test.",
        "",
        "## Caveats",
        "",
        f"- Maddison ends in {latest_year}; Keynes's 100-year horizon was "
        "2030. Adding the further ~10-15 years of observed OECD growth at "
        "trend (~1.5%/yr) would raise the ratios by another factor of "
        "~1.15-1.25 — does not change a SUPPORTED verdict, would only "
        "tighten margins.",
        "- 2011 PPP $ chaining tracks output, not subjective standard of "
        "living; Keynes's 'economic problem' framing is broader than GDP.",
        "- The hypothesis is **descriptive**: a ratio computation, not a "
        "causal claim. The degrowth reframing question (whether the "
        "growth imperative still binds given the threshold has been met) "
        "is downstream, not tested here.",
        f"- Missing endpoint data: {missing if missing else 'none'}.",
        "",
        "## Data",
        "",
        f"- maddison:mpd2020 (vintage {Path(manifest['gdp_pc_ppp_2011']['vintage_file']).name})",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")
    print(f"  pop-weighted ratio {latest_year}/1930: {pop_weighted_ratio:.2f}x (threshold >= {KEYNES_LOWER_BOUND:.0f}x)")
    print(f"  equal-weighted mean: {equal_mean_ratio:.2f}x; median: {median_ratio:.2f}x")
    print(f"  {n_above_4x}/{n_total} countries above 4x; {n_above_8x}/{n_total} above 8x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
