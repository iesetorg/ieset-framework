#!/usr/bin/env python3
"""Replication — Taiwan ITRI-led frontier-capability effect.

Spec: hypotheses/growth/taiwan_itri_frontier_capability_effect.yaml v1
Position-claim: developmentalism #4 (school predicts: supported)

The original spec asked for outcomes including foundry market share, semi
patent stock, and the Atlas Economic Complexity Index. None of those series
are on disk in a Taiwan-inclusive form: WIPO ip_statistics_data_center has
no TWN rows and is sparsely populated; the OWID economic-complexity-index
file is not present; WDI excludes Taiwan entirely. PWT 10.x is the only
publisher on disk that covers Taiwan plus the donor pool over the full
1955-2019 window. We therefore re-cast the test on PWT productivity
indicators, which are the closest defensible proxies for "frontier
capability" given the available data:

  PRIMARY 1 (capability proxy): Total-factor-productivity (rtfpna)
    cumulative log-growth, 1973 -> 2019. Taiwan vs the simple mean of the
    comparable-1970s-income donor pool {KOR, PHL, MYS, BRA, MEX, ARG, THA,
    IDN}. SUPPORTED if TWN's cumulative TFP gain exceeds the pool mean by
    >= 0.20 log-points (~22% extra TFP) AND TWN ranks #1 or #2 in the
    nine-country sample. REFUTED if TWN's gain is below the pool mean.
    PARTIAL otherwise.

  PRIMARY 2 (output proxy): Real GDP per capita (rgdpe / pop) cumulative
    log-growth, 1973 -> 2019. SUPPORTED if TWN's cumulative gain exceeds
    the pool mean by >= 0.50 log-points (~65% extra income) AND TWN ranks
    #1. REFUTED if TWN's gain is below the pool mean. PARTIAL otherwise.

KOR is intentionally retained in the donor pool: the spec's claim is that
ITRI-style state-coordinated technology strategy produced a frontier-
capability industry that *market-led* peers did not generate. KOR is itself
a developmentalist case (HCI drive, chaebol-state coordination), which
makes it a hard comparator rather than a clean control. The verdict
diagnostics report TWN's gap to (i) the full donor pool and (ii) a
"market-led-only" subpool {PHL, MYS, BRA, MEX, ARG, THA, IDN} excluding
KOR, so a reader can see both framings.

This is a descriptive panel replication, not the synth_did template the
YAML originally named: with one treated unit and small-T pre-period
(1955-1972 = 17 years) and a 9-unit donor pool, a synthetic-control fit is
under-identified for the long-horizon question we actually care about.
The simple cumulative-gap statistic is more honest and the threshold is
the dispositive part anyway.
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
HID = "taiwan_itri_frontier_capability_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
TREATED = "TWN"
DONOR_POOL = ["KOR", "PHL", "MYS", "BRA", "MEX", "ARG", "THA", "IDN"]
MARKET_LED_SUBPOOL = ["PHL", "MYS", "BRA", "MEX", "ARG", "THA", "IDN"]  # KOR removed
ALL_COUNTRIES = [TREATED] + DONOR_POOL

# Treatment window: ITRI founded 1973; we measure cumulative gains 1973 -> end-of-data
TREATMENT_YEAR = 1973
END_YEAR = 2019  # PWT 10.x ends 2019

# Falsification thresholds (made dispositive — see module docstring)
TFP_GAP_SUPPORTED_THRESHOLD = 0.20   # log-points; ~22% extra TFP vs pool mean
GDPPC_GAP_SUPPORTED_THRESHOLD = 0.50  # log-points; ~65% extra income vs pool mean


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
    """Standard normaliser — keep (country_iso3, year, value)."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
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


def cum_log_change(series: pd.Series, y0: int, y1: int) -> float | None:
    """log(v[y1]) - log(v[y0]); None if either endpoint missing or non-positive."""
    if y0 not in series.index or y1 not in series.index:
        return None
    v0, v1 = series[y0], series[y1]
    if v0 is None or v1 is None or v0 <= 0 or v1 <= 0 or pd.isna(v0) or pd.isna(v1):
        return None
    return float(np.log(v1) - np.log(v0))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load PWT series — rtfpna is the relative TFP at constant national prices
    # (the standard PWT productivity index; index = 1 in 2017). rgdpe is real
    # GDP at PPP, expenditure-side (constant 2017 USD millions). pop is in
    # millions.
    rtfpna_path = latest("pwt", "rtfpna")
    rgdpe_path = latest("pwt", "rgdpe")
    pop_path = latest("pwt", "pop")

    manifest = {
        "tfp_index": {
            "publisher": "pwt",
            "series": "rtfpna",
            "vintage_file": str(rtfpna_path.relative_to(REPO_ROOT)),
            "sha256": sha256(rtfpna_path),
        },
        "real_gdp_ppp": {
            "publisher": "pwt",
            "series": "rgdpe",
            "vintage_file": str(rgdpe_path.relative_to(REPO_ROOT)),
            "sha256": sha256(rgdpe_path),
        },
        "population": {
            "publisher": "pwt",
            "series": "pop",
            "vintage_file": str(pop_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pop_path),
        },
    }

    tfp_long = load_long(rtfpna_path)
    rgdpe_long = load_long(rgdpe_path)
    pop_long = load_long(pop_path)

    def country_series(df: pd.DataFrame, c: str) -> pd.Series:
        s = df[df["country_iso3"] == c].set_index("year")["value"].sort_index()
        # Coerce duplicates by keeping mean (PWT is unique per country-year, but be safe).
        return s.groupby(level=0).mean()

    # ---------- PRIMARY 1: TFP cumulative log-change 1973 -> 2019 ----------
    tfp_cum = {}
    for c in ALL_COUNTRIES:
        s = country_series(tfp_long, c)
        tfp_cum[c] = cum_log_change(s, TREATMENT_YEAR, END_YEAR)

    tfp_twn = tfp_cum[TREATED]
    tfp_pool_vals = [tfp_cum[c] for c in DONOR_POOL if tfp_cum[c] is not None]
    tfp_pool_mean = float(np.mean(tfp_pool_vals)) if tfp_pool_vals else None
    tfp_market_led_vals = [tfp_cum[c] for c in MARKET_LED_SUBPOOL if tfp_cum[c] is not None]
    tfp_market_led_mean = (
        float(np.mean(tfp_market_led_vals)) if tfp_market_led_vals else None
    )

    tfp_ranking = sorted(
        [(c, tfp_cum[c]) for c in ALL_COUNTRIES if tfp_cum[c] is not None],
        key=lambda kv: kv[1],
        reverse=True,
    )
    tfp_rank_twn = next(
        (i + 1 for i, (c, _) in enumerate(tfp_ranking) if c == TREATED), None
    )

    tfp_gap_pool = (
        tfp_twn - tfp_pool_mean
        if tfp_twn is not None and tfp_pool_mean is not None
        else None
    )
    tfp_gap_market_led = (
        tfp_twn - tfp_market_led_mean
        if tfp_twn is not None and tfp_market_led_mean is not None
        else None
    )

    primary1_supported = (
        tfp_gap_pool is not None
        and tfp_gap_pool >= TFP_GAP_SUPPORTED_THRESHOLD
        and tfp_rank_twn is not None
        and tfp_rank_twn <= 2
    )
    primary1_refuted = tfp_gap_pool is not None and tfp_gap_pool < 0

    # ---------- PRIMARY 2: real GDP per capita cumulative log-change ----------
    gdppc_cum = {}
    gdppc_series_by_country: dict[str, pd.Series] = {}
    for c in ALL_COUNTRIES:
        rg = country_series(rgdpe_long, c)
        po = country_series(pop_long, c)
        common_years = rg.index.intersection(po.index)
        if len(common_years) == 0:
            gdppc_cum[c] = None
            continue
        gdppc = rg.loc[common_years] / po.loc[common_years]
        gdppc_series_by_country[c] = gdppc
        gdppc_cum[c] = cum_log_change(gdppc, TREATMENT_YEAR, END_YEAR)

    gdppc_twn = gdppc_cum[TREATED]
    gdppc_pool_vals = [gdppc_cum[c] for c in DONOR_POOL if gdppc_cum[c] is not None]
    gdppc_pool_mean = float(np.mean(gdppc_pool_vals)) if gdppc_pool_vals else None
    gdppc_market_led_vals = [
        gdppc_cum[c] for c in MARKET_LED_SUBPOOL if gdppc_cum[c] is not None
    ]
    gdppc_market_led_mean = (
        float(np.mean(gdppc_market_led_vals)) if gdppc_market_led_vals else None
    )

    gdppc_ranking = sorted(
        [(c, gdppc_cum[c]) for c in ALL_COUNTRIES if gdppc_cum[c] is not None],
        key=lambda kv: kv[1],
        reverse=True,
    )
    gdppc_rank_twn = next(
        (i + 1 for i, (c, _) in enumerate(gdppc_ranking) if c == TREATED), None
    )

    gdppc_gap_pool = (
        gdppc_twn - gdppc_pool_mean
        if gdppc_twn is not None and gdppc_pool_mean is not None
        else None
    )
    gdppc_gap_market_led = (
        gdppc_twn - gdppc_market_led_mean
        if gdppc_twn is not None and gdppc_market_led_mean is not None
        else None
    )

    primary2_supported = (
        gdppc_gap_pool is not None
        and gdppc_gap_pool >= GDPPC_GAP_SUPPORTED_THRESHOLD
        and gdppc_rank_twn == 1
    )
    primary2_refuted = gdppc_gap_pool is not None and gdppc_gap_pool < 0

    # ---------- METHOD-VALID gate ----------
    n_donors_with_tfp = len(tfp_pool_vals)
    n_donors_with_gdppc = len(gdppc_pool_vals)
    method_valid = (
        tfp_twn is not None
        and gdppc_twn is not None
        and n_donors_with_tfp >= 6
        and n_donors_with_gdppc >= 6
    )

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            "inconclusive — Insufficient donor coverage in PWT 10.x "
            f"(TFP donors: {n_donors_with_tfp}/8, GDPpc donors: "
            f"{n_donors_with_gdppc}/8, TWN TFP series present: "
            f"{tfp_twn is not None}, TWN GDPpc series present: "
            f"{gdppc_twn is not None})."
        )
    elif primary1_supported and primary2_supported:
        verdict = (
            f"SUPPORTED — Taiwan's 1973-2019 cumulative TFP gain is "
            f"{tfp_twn*100:+.0f} log-pts vs donor-pool mean "
            f"{tfp_pool_mean*100:+.0f} (gap {tfp_gap_pool*100:+.0f} ≥ "
            f"{TFP_GAP_SUPPORTED_THRESHOLD*100:+.0f}); rank "
            f"{tfp_rank_twn}/{len(tfp_ranking)}. Real GDPpc gain "
            f"{gdppc_twn*100:+.0f} log-pts vs pool {gdppc_pool_mean*100:+.0f} "
            f"(gap {gdppc_gap_pool*100:+.0f} ≥ "
            f"{GDPPC_GAP_SUPPORTED_THRESHOLD*100:+.0f}); rank "
            f"{gdppc_rank_twn}/{len(gdppc_ranking)}."
        )
    elif primary1_refuted and primary2_refuted:
        verdict = (
            f"refuted — Taiwan's TFP gain ({tfp_twn*100:+.0f} log-pts) is "
            f"BELOW the donor-pool mean ({tfp_pool_mean*100:+.0f}), gap "
            f"{tfp_gap_pool*100:+.0f}. GDPpc gain ({gdppc_twn*100:+.0f}) is "
            f"also below pool mean ({gdppc_pool_mean*100:+.0f})."
        )
    else:
        bits = []
        bits.append(
            f"TFP gap {tfp_gap_pool*100:+.0f} log-pts (threshold "
            f"{TFP_GAP_SUPPORTED_THRESHOLD*100:+.0f}, rank {tfp_rank_twn})"
        )
        bits.append(
            f"GDPpc gap {gdppc_gap_pool*100:+.0f} log-pts (threshold "
            f"{GDPPC_GAP_SUPPORTED_THRESHOLD*100:+.0f}, rank {gdppc_rank_twn})"
        )
        verdict = (
            "partial — One primary held but not the other (or magnitudes "
            "fell short of the strong-form threshold). " + "; ".join(bits) + "."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "primary1_tfp_supported": primary1_supported,
        "primary1_tfp_refuted": primary1_refuted,
        "primary2_gdppc_supported": primary2_supported,
        "primary2_gdppc_refuted": primary2_refuted,
        "tfp_cumlog_1973_2019": tfp_cum,
        "tfp_twn": tfp_twn,
        "tfp_pool_mean": tfp_pool_mean,
        "tfp_market_led_mean": tfp_market_led_mean,
        "tfp_gap_vs_pool": tfp_gap_pool,
        "tfp_gap_vs_market_led": tfp_gap_market_led,
        "tfp_rank_twn": tfp_rank_twn,
        "tfp_n_donors": n_donors_with_tfp,
        "tfp_threshold_logpts": TFP_GAP_SUPPORTED_THRESHOLD,
        "gdppc_cumlog_1973_2019": gdppc_cum,
        "gdppc_twn": gdppc_twn,
        "gdppc_pool_mean": gdppc_pool_mean,
        "gdppc_market_led_mean": gdppc_market_led_mean,
        "gdppc_gap_vs_pool": gdppc_gap_pool,
        "gdppc_gap_vs_market_led": gdppc_gap_market_led,
        "gdppc_rank_twn": gdppc_rank_twn,
        "gdppc_n_donors": n_donors_with_gdppc,
        "gdppc_threshold_logpts": GDPPC_GAP_SUPPORTED_THRESHOLD,
        "treatment_year": TREATMENT_YEAR,
        "end_year": END_YEAR,
        "donor_pool": DONOR_POOL,
        "market_led_subpool": MARKET_LED_SUBPOOL,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: log GDP per capita rebased to 1973 ----------
    palette = [
        "#E15759", "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F",
    ]
    series = []
    for i, c in enumerate(ALL_COUNTRIES):
        if c not in gdppc_series_by_country:
            continue
        s = gdppc_series_by_country[c]
        s = s[(s.index >= 1955) & (s.index <= END_YEAR)]
        if TREATMENT_YEAR not in s.index:
            continue
        base = s[TREATMENT_YEAR]
        if base <= 0 or pd.isna(base):
            continue
        pts = [
            {"x": int(y), "y": float(np.log(s[y]) - np.log(base))}
            for y in s.index
            if s[y] > 0 and not pd.isna(s[y])
        ]
        series.append(
            {
                "id": c,
                "label": c,
                "color": palette[i % len(palette)],
                "treated": (c == TREATED),
                "points": pts,
            }
        )

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": (
            "Real GDP per capita, log-difference vs 1973 — "
            "Taiwan vs comparable-1970s-income donor pool"
        ),
        "subtitle": (
            f"TWN cumulative log-gain 1973-2019: "
            f"{(gdppc_twn or 0)*100:+.0f} pts · "
            f"donor-pool mean: {(gdppc_pool_mean or 0)*100:+.0f} pts · "
            f"market-led-only subpool: {(gdppc_market_led_mean or 0)*100:+.0f} pts. "
            f"TFP (PWT rtfpna) cumulative log-gain — TWN: "
            f"{(tfp_twn or 0)*100:+.0f}, pool mean: "
            f"{(tfp_pool_mean or 0)*100:+.0f}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log(GDPpc / GDPpc[1973])", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vline",
                "x": TREATMENT_YEAR,
                "label": "ITRI founded (1973)",
            },
            {
                "type": "vline",
                "x": 1987,
                "label": "TSMC spinoff (1987)",
            },
            {
                "type": "note",
                "label": (
                    f"PWT 10.x; series ends 2019. Donor pool: "
                    f"{', '.join(DONOR_POOL)}."
                ),
            },
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

    coef_rows = [
        {"spec": "primary1_tfp", "term": "twn_cumlog_change_1973_2019", "estimate": tfp_twn},
        {"spec": "primary1_tfp", "term": "pool_mean_cumlog_change", "estimate": tfp_pool_mean},
        {"spec": "primary1_tfp", "term": "twn_minus_pool_logpts", "estimate": tfp_gap_pool},
        {"spec": "primary1_tfp", "term": "market_led_subpool_mean", "estimate": tfp_market_led_mean},
        {"spec": "primary1_tfp", "term": "twn_minus_market_led_logpts", "estimate": tfp_gap_market_led},
        {"spec": "primary2_gdppc", "term": "twn_cumlog_change_1973_2019", "estimate": gdppc_twn},
        {"spec": "primary2_gdppc", "term": "pool_mean_cumlog_change", "estimate": gdppc_pool_mean},
        {"spec": "primary2_gdppc", "term": "twn_minus_pool_logpts", "estimate": gdppc_gap_pool},
        {"spec": "primary2_gdppc", "term": "market_led_subpool_mean", "estimate": gdppc_market_led_mean},
        {"spec": "primary2_gdppc", "term": "twn_minus_market_led_logpts", "estimate": gdppc_gap_market_led},
    ]
    for c in ALL_COUNTRIES:
        coef_rows.append(
            {"spec": "primary1_tfp", "term": f"cumlog_tfp_{c}", "estimate": tfp_cum.get(c)}
        )
        coef_rows.append(
            {"spec": "primary2_gdppc", "term": f"cumlog_gdppc_{c}", "estimate": gdppc_cum.get(c)}
        )
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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

    def fmt_logpts(x):
        return "n/a" if x is None else f"{x*100:+.0f}"

    card_lines = [
        "# Taiwan ITRI frontier-capability effect",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Treatment year: {TREATMENT_YEAR} (ITRI founded). End of available data: {END_YEAR} (PWT 10.x).",
        f"- Donor pool: {', '.join(DONOR_POOL)} (n=8); 'market-led-only' subpool excludes KOR.",
        "",
        "**Primary 1 — TFP cumulative log-change (PWT rtfpna):**",
        "",
        f"- Taiwan: **{fmt_logpts(tfp_twn)}** log-pts.",
        f"- Donor-pool mean: **{fmt_logpts(tfp_pool_mean)}** log-pts.",
        f"- Market-led subpool mean (no KOR): **{fmt_logpts(tfp_market_led_mean)}** log-pts.",
        f"- Gap vs pool: **{fmt_logpts(tfp_gap_pool)}** log-pts (threshold for SUPPORTED: ≥{int(TFP_GAP_SUPPORTED_THRESHOLD*100)} log-pts AND TWN rank ≤ 2).",
        f"- Taiwan rank in 9-country sample: **{tfp_rank_twn}**.",
        "",
        "**Primary 2 — Real GDP per capita cumulative log-change (PWT rgdpe / pop):**",
        "",
        f"- Taiwan: **{fmt_logpts(gdppc_twn)}** log-pts.",
        f"- Donor-pool mean: **{fmt_logpts(gdppc_pool_mean)}** log-pts.",
        f"- Market-led subpool mean (no KOR): **{fmt_logpts(gdppc_market_led_mean)}** log-pts.",
        f"- Gap vs pool: **{fmt_logpts(gdppc_gap_pool)}** log-pts (threshold for SUPPORTED: ≥{int(GDPPC_GAP_SUPPORTED_THRESHOLD*100)} log-pts AND TWN rank #1).",
        f"- Taiwan rank in 9-country sample: **{gdppc_rank_twn}**.",
        "",
        "## Method",
        "",
        "Single-treated-unit cumulative-gap test on PWT 10.x productivity",
        "indicators, 1973 (ITRI founding) to 2019 (last PWT year). The",
        "spec originally requested foundry market-share, semiconductor",
        "patent stock, and the Atlas Economic Complexity Index, but none",
        "of those series are present on disk in a Taiwan-inclusive form",
        "(WIPO ip_statistics_data_center has no TWN rows; OWID economic-",
        "complexity-index file is not present; WDI excludes Taiwan",
        "entirely). PWT is the only on-disk publisher with full TWN",
        "coverage 1955-2019 plus the donor pool. TFP is the closest",
        "available proxy for 'frontier capability' the spec asks about;",
        "real GDP per capita is the closest proxy for 'output of a",
        "frontier industry' that flows to the wider economy.",
        "",
        "We do not run a synthetic-control fit. With one treated unit,",
        "9-country donor pool, and only ~17 years of pre-period (1955-",
        "1972), a synth fit on long-horizon outcomes is under-identified;",
        "the dispositive question is the magnitude of Taiwan's gap to a",
        "comparable-income peer mean, which the cumulative-log statistic",
        "answers directly.",
        "",
        "## Caveats",
        "",
        "- KOR is itself a developmentalist case (HCI drive, chaebol-",
        "  state coordination), not a clean control. The 'market-led",
        "  subpool' diagnostic strips KOR out so a reader can see both",
        "  framings; the headline gap is to the full 8-country donor pool.",
        "- The treatment is 'ITRI strategy' but PWT productivity captures",
        "  *all* sources of Taiwan's TFP catch-up — Cold War US technology",
        "  transfer, returning diaspora engineers, the global pure-play",
        "  foundry shift. The replication cannot isolate the ITRI channel.",
        "- PWT ends 2019, so the 2020s semiconductor boom (TSMC 3nm/N2,",
        "  CHIPS Act spillovers) does not enter the test.",
        "- This is an associational descriptive comparison, not a causal",
        "  identification. The verdict labels a magnitude pattern, not a",
        "  causal estimate.",
        "",
        "## Data",
        "",
        "- pwt:rtfpna (TFP at constant national prices, 2017 = 1)",
        "- pwt:rgdpe (real GDP at chained PPPs, expenditure-side)",
        "- pwt:pop (population, millions)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card_lines) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
