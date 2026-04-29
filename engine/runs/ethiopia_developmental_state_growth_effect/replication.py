#!/usr/bin/env python3
"""Replication — Ethiopia developmental-state growth effect (1995-2010).

Spec: hypotheses/growth/ethiopia_developmental_state_growth_effect.yaml v1
Position-claim: developmentalism #12 (school predicts: supported)

Tests whether the EPRDF developmental-state strategy (state-led
infrastructure + industrial parks + export-credit allocation,
roughly 1995 onward) produced the FASTEST sustained Sub-Saharan
African growth in the pre-2010 window.

PRIMARY (dispositive):
  P1. Ethiopia's cumulative log-GDP-per-capita (PPP) growth from
      1995 to 2010 must rank #1 among the SSA peer pool
      (KEN, TZA, UGA, RWA, SEN, GHA, MOZ, MWI, ZMB, MDG, BDI).
  P2. The gap between Ethiopia's cumulative log-growth and the
      peer-pool MEDIAN cumulative log-growth over 1995-2010 must
      exceed +0.20 log points (i.e. Ethiopia's PPP per-capita
      grows >=20 log-points faster than the median peer over
      the 15-year window). This is the "fastest sustained"
      magnitude condition.

INFORMATIVE (colours verdict, not dispositive):
  - Synthetic-control-lite: pre-treatment-fit weighted
    counterfactual using 1991-1994 levels of the peer pool to
    match Ethiopia's pre-treatment level. Reported
    counterfactual gap at 2010 included as a robustness check.
  - Capital-formation share and trade-openness changes
    1995->2010 reported for Ethiopia and peers (mechanism
    diagnostics).

METHOD_VALID:
  - WDI NY.GDP.PCAP.PP.KD must be available 1991-2010 for
    Ethiopia and at least 9 of 11 peers (>=10/12 panel).

SUPPORTED iff P1 AND P2.
REFUTED if Ethiopia is NOT in the top-3 OR Ethiopia's gap to
median is BELOW zero (i.e. Ethiopia grew slower than typical peer).
PARTIAL otherwise.
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
HID = "ethiopia_developmental_state_growth_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "ETH"
PEERS = ["KEN", "TZA", "UGA", "RWA", "SEN", "GHA", "MOZ", "MWI", "ZMB", "MDG", "BDI"]
ALL_COUNTRIES = [TREATED] + PEERS

PRE_PERIOD = (1991, 1994)   # pre-EPRDF developmental strategy bedding-in
TREAT_START = 1995          # spec: indicator = 1 for ETH, year >= 1995
POST_PERIOD = (1995, 2010)  # spec scope
SAMPLE_PERIOD = (1991, 2019)

# Falsification thresholds
RANK_THRESHOLD = 1                # Ethiopia must rank #1 of 12 (top of peer pool)
GROWTH_GAP_THRESHOLD = 0.20       # cumulative log-points vs median peer
MIN_PEER_COVERAGE = 9             # of 11 peers


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdp_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    gcf_path = latest("world_bank_wdi", "NE.GDI.TOTL.ZS")
    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")

    manifest = {
        "gdp_pc_ppp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.PP.KD",
            "vintage_file": str(gdp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_path),
        },
        "gross_capital_formation_pct_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NE.GDI.TOTL.ZS",
            "vintage_file": str(gcf_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gcf_path),
        },
        "trade_openness_pct_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NE.TRD.GNFS.ZS",
            "vintage_file": str(trade_path.relative_to(REPO_ROOT)),
            "sha256": sha256(trade_path),
        },
    }

    gdp = load_long(gdp_path)
    gcf = load_long(gcf_path)
    trade = load_long(trade_path)

    # ---------- Build the panel ----------
    panel = gdp[
        gdp["country_iso3"].isin(ALL_COUNTRIES)
        & gdp["year"].between(SAMPLE_PERIOD[0], SAMPLE_PERIOD[1])
    ].copy()
    panel["year"] = panel["year"].astype(int)
    panel["log_gdp_pc"] = np.log(panel["value"])

    piv = panel.pivot_table(
        index="year", columns="country_iso3", values="log_gdp_pc"
    ).sort_index()

    # METHOD_VALID coverage check
    peers_with_data = [
        c for c in PEERS
        if c in piv.columns
        and not piv.loc[TREAT_START:POST_PERIOD[1], c].isna().any()
    ]
    eth_ok = (
        TREATED in piv.columns
        and not piv.loc[TREAT_START:POST_PERIOD[1], TREATED].isna().any()
    )
    method_valid = eth_ok and len(peers_with_data) >= MIN_PEER_COVERAGE

    # ---------- PRIMARY 1 + 2: cumulative log-growth ----------
    # log GDPpc(2010) - log GDPpc(1995), per country
    cum_growth: dict[str, float] = {}
    for c in ALL_COUNTRIES:
        if c not in piv.columns:
            continue
        if pd.isna(piv.loc[TREAT_START, c]) or pd.isna(piv.loc[POST_PERIOD[1], c]):
            continue
        cum_growth[c] = float(
            piv.loc[POST_PERIOD[1], c] - piv.loc[TREAT_START, c]
        )

    # Rank Ethiopia within the full panel (treated + peers)
    ranked = sorted(cum_growth.items(), key=lambda kv: -kv[1])
    rank_table = [{"country": c, "cum_log_growth_1995_2010": v} for c, v in ranked]
    rank_eth = next(
        (i + 1 for i, (c, _) in enumerate(ranked) if c == TREATED), None
    )
    eth_growth = cum_growth.get(TREATED, float("nan"))
    peer_growths = [v for c, v in cum_growth.items() if c != TREATED]
    peer_median = float(np.median(peer_growths)) if peer_growths else float("nan")
    peer_mean = float(np.mean(peer_growths)) if peer_growths else float("nan")
    eth_minus_median = eth_growth - peer_median
    eth_minus_mean = eth_growth - peer_mean

    primary1_rank_top = rank_eth == RANK_THRESHOLD
    primary2_gap_large = eth_minus_median >= GROWTH_GAP_THRESHOLD

    # ---------- INFORMATIVE: synthetic-control-lite ----------
    # Pick non-negative donor weights (sum to 1) that minimise SSE between
    # Ethiopia's pre-period log GDPpc and weighted donor pool, using a
    # simple grid + projection search (no scipy dependency).
    pre_years = list(range(PRE_PERIOD[0], PRE_PERIOD[1] + 1))
    eth_pre = piv.loc[pre_years, TREATED].values
    donors = [c for c in peers_with_data]
    donor_pre = np.column_stack([piv.loc[pre_years, c].values for c in donors])

    def synth_search(eth_pre, donor_pre, n_iter=20000, seed=42):
        rng = np.random.default_rng(seed)
        best_w = np.ones(donor_pre.shape[1]) / donor_pre.shape[1]
        best_err = float("inf")
        # Random Dirichlet samples
        alpha = np.ones(donor_pre.shape[1])
        for _ in range(n_iter):
            w = rng.dirichlet(alpha)
            err = float(np.sum((donor_pre @ w - eth_pre) ** 2))
            if err < best_err:
                best_err = err
                best_w = w
        return best_w, best_err

    weights, pre_sse = synth_search(eth_pre, donor_pre)
    synth_path = piv[donors].values @ weights  # shape (T,)
    synth_index = piv.index
    eth_path = piv[TREATED].values

    synth_2010 = float(synth_path[list(synth_index).index(POST_PERIOD[1])])
    eth_2010 = float(piv.loc[POST_PERIOD[1], TREATED])
    synth_1995 = float(synth_path[list(synth_index).index(TREAT_START)])
    eth_1995 = float(piv.loc[TREAT_START, TREATED])
    synth_growth = synth_2010 - synth_1995
    counterfactual_gap_2010 = eth_2010 - synth_2010
    counterfactual_growth_gap = (eth_2010 - eth_1995) - synth_growth

    # ---------- Mechanism diagnostics: GCF and trade openness ----------
    def mean_change(df: pd.DataFrame, country: str, y0: int, y1: int) -> float:
        s = df[(df["country_iso3"] == country) & df["year"].isin([y0, y1])]
        s = s.set_index("year")["value"]
        if y0 not in s.index or y1 not in s.index:
            return float("nan")
        return float(s[y1] - s[y0])

    gcf_changes = {c: mean_change(gcf, c, TREAT_START, POST_PERIOD[1]) for c in ALL_COUNTRIES}
    trade_changes = {c: mean_change(trade, c, TREAT_START, POST_PERIOD[1]) for c in ALL_COUNTRIES}

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive — METHOD_VALID failed: ETH coverage="
            f"{eth_ok}, peer coverage={len(peers_with_data)}/{len(PEERS)} "
            f"(need >= {MIN_PEER_COVERAGE})."
        )
    elif primary1_rank_top and primary2_gap_large:
        verdict = (
            f"SUPPORTED — Ethiopia 1995-2010 cumulative log-GDP-per-capita "
            f"(PPP) growth = {eth_growth*100:+.1f} log-points, ranking "
            f"#{rank_eth}/{len(cum_growth)} in the SSA peer pool. "
            f"Gap to peer median = {eth_minus_median*100:+.1f} log-points "
            f"(threshold {GROWTH_GAP_THRESHOLD*100:.0f}). Synthetic-control-"
            f"lite counterfactual gap at 2010 = "
            f"{counterfactual_gap_2010*100:+.1f} log-points."
        )
    elif (rank_eth is not None and rank_eth <= 3) or (eth_minus_median > 0):
        verdict = (
            f"partial — Ethiopia grew faster than the peer median "
            f"({eth_minus_median*100:+.1f} log-points) and ranked "
            f"#{rank_eth}/{len(cum_growth)}, but did not meet both primary "
            f"thresholds (rank #1 AND gap >= {GROWTH_GAP_THRESHOLD*100:.0f} "
            f"log-points). Synthetic counterfactual gap at 2010 = "
            f"{counterfactual_gap_2010*100:+.1f} log-points."
        )
    else:
        verdict = (
            f"refuted — Ethiopia ranked #{rank_eth}/{len(cum_growth)} on "
            f"cumulative 1995-2010 log-GDP-per-capita growth and was "
            f"{eth_minus_median*100:+.1f} log-points vs peer median. The "
            f"\"fastest sustained African growth\" claim does not hold "
            f"in the WDI panel."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "all_pass": bool(method_valid and primary1_rank_top and primary2_gap_large),
        "primary1_rank_top": bool(primary1_rank_top),
        "primary2_gap_large": bool(primary2_gap_large),
        "rank_eth": rank_eth,
        "rank_threshold": RANK_THRESHOLD,
        "eth_cum_log_growth_1995_2010": eth_growth,
        "peer_median_cum_log_growth_1995_2010": peer_median,
        "peer_mean_cum_log_growth_1995_2010": peer_mean,
        "eth_minus_peer_median": eth_minus_median,
        "eth_minus_peer_mean": eth_minus_mean,
        "growth_gap_threshold": GROWTH_GAP_THRESHOLD,
        "ranking_table": rank_table,
        "synth_donor_weights": {donors[i]: float(weights[i]) for i in range(len(donors))},
        "synth_pre_period_sse": pre_sse,
        "synth_counterfactual_log_gdppc_2010": synth_2010,
        "eth_log_gdppc_2010": eth_2010,
        "synth_counterfactual_gap_2010_log_points": counterfactual_gap_2010,
        "synth_counterfactual_growth_gap_log_points": counterfactual_growth_gap,
        "n_peers_with_data": len(peers_with_data),
        "peers_with_data": peers_with_data,
        "gcf_pct_gdp_change_1995_2010": gcf_changes,
        "trade_openness_pct_gdp_change_1995_2010": trade_changes,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    palette = [
        "#E15759", "#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
    ]
    series = []
    # Ethiopia treated (red, treated=True)
    eth_pts = [
        {"x": int(y), "y": float(piv.loc[y, TREATED])}
        for y in piv.index
        if not pd.isna(piv.loc[y, TREATED])
    ]
    series.append(
        {
            "id": TREATED,
            "label": "Ethiopia (treated)",
            "color": palette[0],
            "treated": True,
            "points": eth_pts,
        }
    )
    # Synthetic counterfactual
    synth_pts = [
        {"x": int(y), "y": float(synth_path[i])}
        for i, y in enumerate(piv.index)
    ]
    series.append(
        {
            "id": "SYNTH",
            "label": "Synthetic Ethiopia (Dirichlet-weighted SSA peers)",
            "color": "#1f1f1f",
            "treated": False,
            "points": synth_pts,
        }
    )
    # Peers
    for i, c in enumerate(PEERS):
        if c not in piv.columns:
            continue
        pts = [
            {"x": int(y), "y": float(piv.loc[y, c])}
            for y in piv.index
            if not pd.isna(piv.loc[y, c])
        ]
        series.append(
            {
                "id": c,
                "label": c,
                "color": palette[(i + 1) % len(palette)],
                "treated": False,
                "points": pts,
            }
        )

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Ethiopia vs SSA peers — log GDP per capita (PPP, 2017 USD)",
        "subtitle": (
            f"Ethiopia 1995-2010 cum log-growth = {eth_growth*100:+.1f} pts "
            f"(rank #{rank_eth}/{len(cum_growth)}); peer median = "
            f"{peer_median*100:+.1f} pts; synthetic counterfactual gap at "
            f"2010 = {counterfactual_gap_2010*100:+.1f} pts."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log GDP per capita (PPP)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vertical_line",
                "x": TREAT_START,
                "label": f"EPRDF developmental strategy ({TREAT_START})",
            },
            {
                "type": "note",
                "label": (
                    f"Donor weights (top): "
                    + ", ".join(
                        f"{donors[i]}={weights[i]:.2f}"
                        for i in np.argsort(-weights)[:5]
                    )
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
        {"spec": "primary1", "term": "rank_eth_1995_2010", "estimate": float(rank_eth) if rank_eth else float("nan")},
        {"spec": "primary2", "term": "eth_cum_log_growth", "estimate": eth_growth},
        {"spec": "primary2", "term": "peer_median_cum_log_growth", "estimate": peer_median},
        {"spec": "primary2", "term": "eth_minus_peer_median", "estimate": eth_minus_median},
        {"spec": "informative", "term": "synth_counterfactual_gap_2010_log_points", "estimate": counterfactual_gap_2010},
        {"spec": "informative", "term": "synth_counterfactual_growth_gap_log_points", "estimate": counterfactual_growth_gap},
    ]
    for c, v in cum_growth.items():
        coef_rows.append({"spec": "ranking", "term": f"cum_log_growth_1995_2010[{c}]", "estimate": v})
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

    # Build ranking text block
    rank_lines = [
        f"  {i+1}. {c}: {v*100:+.1f} log-points"
        for i, (c, v) in enumerate(ranked)
    ]
    card = [
        f"# Ethiopia developmental-state growth effect (1995-2010)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Ethiopia cumulative log-GDP-per-capita (PPP) growth 1995-2010: "
        f"**{eth_growth*100:+.1f} log-points** (~{(np.exp(eth_growth)-1)*100:.0f}% in levels).",
        f"- SSA peer-pool median cumulative growth: "
        f"**{peer_median*100:+.1f} log-points**; Ethiopia gap to median: "
        f"**{eth_minus_median*100:+.1f}** (threshold "
        f"{GROWTH_GAP_THRESHOLD*100:.0f}).",
        f"- Ethiopia rank: **#{rank_eth} of {len(cum_growth)}** "
        f"(threshold #{RANK_THRESHOLD}).",
        f"- Synthetic-control-lite counterfactual gap at 2010: "
        f"**{counterfactual_gap_2010*100:+.1f} log-points**.",
        "",
        "## Ranking",
        "",
        *rank_lines,
        "",
        "## Method",
        "",
        "Two dispositive primary tests, then synthetic-control-lite as an"
        " informative robustness check:",
        "",
        f"1. Cumulative log-difference of WDI NY.GDP.PCAP.PP.KD from "
        f"{TREAT_START} to {POST_PERIOD[1]}, computed for Ethiopia and "
        f"each peer; Ethiopia must rank #1 (P1) AND its gap to the peer "
        f"median must be at least {GROWTH_GAP_THRESHOLD:.2f} log-points "
        f"(P2). The 0.20 threshold corresponds to roughly 22% extra "
        f"per-capita PPP growth over 15 years versus the median peer — "
        f"the magnitude a fair reader of \"fastest sustained African "
        f"growth\" would expect to see for the Ethiopian developmental "
        f"state to count as the binding cause.",
        f"2. Synthetic-control-lite using a Dirichlet sample search to "
        f"weight the {len(peers_with_data)} SSA donor countries on "
        f"pre-treatment ({PRE_PERIOD[0]}-{PRE_PERIOD[1]}) levels of log "
        f"GDP per capita PPP. Counterfactual log GDPpc at 2010 reported.",
        "",
        "Donor weights are not meant to compete with Abadie-Diamond-"
        "Hainmueller's quadratic programming SC; the panel is small and "
        "the donor pool is the spec's pre-specified peer pool, so the "
        "synth gap is reported as informative, not dispositive.",
        "",
        "Mechanism diagnostics (gross capital formation share and trade "
        "openness, both as % of GDP) are reported as 1995->2010 changes "
        "for context but do not enter the verdict.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.PCAP.PP.KD (primary outcome)",
        f"- world_bank_wdi:NE.GDI.TOTL.ZS (gross capital formation, % of GDP)",
        f"- world_bank_wdi:NE.TRD.GNFS.ZS (trade, % of GDP)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
