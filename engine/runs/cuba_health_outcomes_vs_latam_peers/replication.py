#!/usr/bin/env python3
"""Replication — Cuban health outcomes vs LATAM middle-income peers, 1960-2000.

Spec: hypotheses/healthcare/cuba_health_outcomes_vs_latam_peers.yaml v1
Position-claim: marxist_leninist #3 (school predicts: supported)

The claim under test: Cuban life expectancy and infant mortality outcomes
1960-2000 outperformed Latin American middle-income peers despite sanctions,
demonstrating socialist health-system superiority.

PRIMARY 1 (life expectancy): Cuba's LE-at-birth in 2000 minus the LATAM
peer-pool MEAN in 2000 must be at least +1.0 year for "outperform" to hold.
The same gap in 1960 sets a baseline; we also report the gain in the gap
(2000_gap minus 1960_gap) so the score does not just reward Cuba's pre-
revolution starting position.

PRIMARY 2 (infant mortality): Cuba's IMR in 2000 must be at most 50% of the
LATAM peer-pool MEAN (i.e. CUB_imr / mean_peer_imr <= 0.50). IMR is the
metric the claim hangs on most directly because it is sensitive to the
primary-care emphasis of the Cuban system.

Hypothesis is SUPPORTED only if BOTH primaries hold AND the 2000 gap on at
least one metric is wider than the 1960 gap (i.e. Cuba pulled away rather
than merely starting ahead). PARTIAL if exactly one primary holds. REFUTED
if neither holds.

INFORMATIVE: the post-1991 sub-period (Soviet subsidies removed) is reported
separately so readers can judge how much of the gap is system-architecture
vs subsidy.

METHOD_VALID: requires WDI coverage for CUB and at least 8 of the 11
peers across 1960 and 2000 endpoints.

NOTE on data quality: WDI back-fills Cuban data from Cuban government
sources, which are contested. The spec asks for a WHO-independent cross-
check; WHO GHO life-expectancy series (WHOSIS_000001) only begin around
2000, so a meaningful 1960-2000 cross-check is not available from that
publisher. Reported as a methodology caveat, not a refutation.
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
HID = "cuba_health_outcomes_vs_latam_peers"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample (sample.countries from spec)
TREATED = "CUB"
PEERS = ["MEX", "BRA", "ARG", "CHL", "COL", "VEN", "DOM", "ECU", "PER", "URY", "CRI"]
ALL_COUNTRIES = [TREATED] + PEERS
PERIOD = (1960, 2000)
ENDPOINT_BASELINE = 1960
ENDPOINT_FINAL = 2000
SOVIET_END = 1991  # subsidies cut

# Falsification thresholds (dispositive on the spec)
LE_GAP_THRESHOLD_YEARS = 1.0           # CUB - peer_mean LE at 2000 >= 1.0y
IMR_RATIO_THRESHOLD = 0.50             # CUB / peer_mean IMR at 2000 <= 0.50
MIN_PEER_COVERAGE = 8                  # of 11 peers needed at endpoints


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


def country_year_mean(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    le_path = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    imr_path = latest("world_bank_wdi", "SP.DYN.IMRT.IN")

    manifest = {
        "life_expectancy": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.LE00.IN",
            "vintage_file": str(le_path.relative_to(REPO_ROOT)),
            "sha256": sha256(le_path),
        },
        "infant_mortality": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.IMRT.IN",
            "vintage_file": str(imr_path.relative_to(REPO_ROOT)),
            "sha256": sha256(imr_path),
        },
    }

    le = load_long(le_path)
    imr = load_long(imr_path)

    le = le[(le["country_iso3"].isin(ALL_COUNTRIES)) & le["year"].between(*PERIOD)].copy()
    imr = imr[(imr["country_iso3"].isin(ALL_COUNTRIES)) & imr["year"].between(*PERIOD)].copy()
    le["year"] = le["year"].astype(int)
    imr["year"] = imr["year"].astype(int)

    # ---------- Endpoint values ----------
    le_cub_1960 = country_year_mean(le, "CUB", ENDPOINT_BASELINE)
    le_cub_2000 = country_year_mean(le, "CUB", ENDPOINT_FINAL)
    imr_cub_1960 = country_year_mean(imr, "CUB", ENDPOINT_BASELINE)
    imr_cub_2000 = country_year_mean(imr, "CUB", ENDPOINT_FINAL)

    le_peer_1960 = {c: country_year_mean(le, c, ENDPOINT_BASELINE) for c in PEERS}
    le_peer_2000 = {c: country_year_mean(le, c, ENDPOINT_FINAL) for c in PEERS}
    imr_peer_1960 = {c: country_year_mean(imr, c, ENDPOINT_BASELINE) for c in PEERS}
    imr_peer_2000 = {c: country_year_mean(imr, c, ENDPOINT_FINAL) for c in PEERS}

    le_peer_1960_vals = [v for v in le_peer_1960.values() if v is not None]
    le_peer_2000_vals = [v for v in le_peer_2000.values() if v is not None]
    imr_peer_1960_vals = [v for v in imr_peer_1960.values() if v is not None]
    imr_peer_2000_vals = [v for v in imr_peer_2000.values() if v is not None]

    le_peer_mean_1960 = float(np.mean(le_peer_1960_vals)) if le_peer_1960_vals else None
    le_peer_mean_2000 = float(np.mean(le_peer_2000_vals)) if le_peer_2000_vals else None
    imr_peer_mean_1960 = float(np.mean(imr_peer_1960_vals)) if imr_peer_1960_vals else None
    imr_peer_mean_2000 = float(np.mean(imr_peer_2000_vals)) if imr_peer_2000_vals else None

    method_valid = (
        le_cub_2000 is not None
        and imr_cub_2000 is not None
        and len(le_peer_2000_vals) >= MIN_PEER_COVERAGE
        and len(imr_peer_2000_vals) >= MIN_PEER_COVERAGE
    )

    # ---------- PRIMARY 1: life-expectancy gap at 2000 ----------
    le_gap_1960 = (le_cub_1960 - le_peer_mean_1960) if (le_cub_1960 is not None and le_peer_mean_1960 is not None) else None
    le_gap_2000 = (le_cub_2000 - le_peer_mean_2000) if (le_cub_2000 is not None and le_peer_mean_2000 is not None) else None
    le_gap_widening = (le_gap_2000 - le_gap_1960) if (le_gap_1960 is not None and le_gap_2000 is not None) else None
    primary1_le_outperform = le_gap_2000 is not None and le_gap_2000 >= LE_GAP_THRESHOLD_YEARS

    # ---------- PRIMARY 2: infant-mortality ratio at 2000 ----------
    imr_ratio_1960 = (imr_cub_1960 / imr_peer_mean_1960) if (imr_cub_1960 is not None and imr_peer_mean_1960 not in (None, 0)) else None
    imr_ratio_2000 = (imr_cub_2000 / imr_peer_mean_2000) if (imr_cub_2000 is not None and imr_peer_mean_2000 not in (None, 0)) else None
    imr_ratio_improvement = (imr_ratio_1960 - imr_ratio_2000) if (imr_ratio_1960 is not None and imr_ratio_2000 is not None) else None
    primary2_imr_outperform = imr_ratio_2000 is not None and imr_ratio_2000 <= IMR_RATIO_THRESHOLD

    # Cuba "pulled away" condition — at least one metric's 2000 gap is more
    # favourable than the 1960 gap (LE: wider in CUB's favour; IMR: lower ratio).
    pulled_away = (
        (le_gap_widening is not None and le_gap_widening > 0)
        or (imr_ratio_improvement is not None and imr_ratio_improvement > 0)
    )

    # ---------- Cuba's rank within the peer-pool at 2000 ----------
    le_2000_rank_pool = sorted(
        [(c, v) for c, v in {**le_peer_2000, "CUB": le_cub_2000}.items() if v is not None],
        key=lambda kv: kv[1], reverse=True,  # higher LE is better
    )
    imr_2000_rank_pool = sorted(
        [(c, v) for c, v in {**imr_peer_2000, "CUB": imr_cub_2000}.items() if v is not None],
        key=lambda kv: kv[1],  # lower IMR is better
    )
    le_cub_rank = next((i + 1 for i, (c, _) in enumerate(le_2000_rank_pool) if c == "CUB"), None)
    imr_cub_rank = next((i + 1 for i, (c, _) in enumerate(imr_2000_rank_pool) if c == "CUB"), None)

    # ---------- Soviet-subsidy sub-period (1991-2000) ----------
    le_cub_1991 = country_year_mean(le, "CUB", SOVIET_END)
    imr_cub_1991 = country_year_mean(imr, "CUB", SOVIET_END)
    le_peer_1991_vals = [country_year_mean(le, c, SOVIET_END) for c in PEERS]
    le_peer_1991_vals = [v for v in le_peer_1991_vals if v is not None]
    imr_peer_1991_vals = [country_year_mean(imr, c, SOVIET_END) for c in PEERS]
    imr_peer_1991_vals = [v for v in imr_peer_1991_vals if v is not None]
    le_gap_1991 = (
        le_cub_1991 - float(np.mean(le_peer_1991_vals))
        if (le_cub_1991 is not None and le_peer_1991_vals) else None
    )
    imr_ratio_1991 = (
        imr_cub_1991 / float(np.mean(imr_peer_1991_vals))
        if (imr_cub_1991 is not None and imr_peer_1991_vals and float(np.mean(imr_peer_1991_vals)) > 0) else None
    )

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive — insufficient peer coverage at 2000 endpoint "
            f"(LE peers: {len(le_peer_2000_vals)}/{len(PEERS)}, "
            f"IMR peers: {len(imr_peer_2000_vals)}/{len(PEERS)}, "
            f"need {MIN_PEER_COVERAGE})"
        )
        all_pass = False
    else:
        both = primary1_le_outperform and primary2_imr_outperform and pulled_away
        if both:
            # Be honest about which metric drove the "pulled away" gate
            le_widened = le_gap_widening is not None and le_gap_widening > 0
            imr_improved = imr_ratio_improvement is not None and imr_ratio_improvement > 0
            if le_widened and imr_improved:
                pull_phrase = "Cuba pulled away on both metrics"
            elif imr_improved and not le_widened:
                pull_phrase = (
                    f"IMR-ratio improved ({imr_ratio_1960:.2f} → {imr_ratio_2000:.2f}) but "
                    f"the LE gap NARROWED ({le_gap_1960:+.1f}y → {le_gap_2000:+.1f}y) — "
                    f"peers caught up on life expectancy"
                )
            elif le_widened and not imr_improved:
                pull_phrase = (
                    f"LE gap widened ({le_gap_1960:+.1f}y → {le_gap_2000:+.1f}y) but the "
                    f"IMR ratio worsened ({imr_ratio_1960:.2f} → {imr_ratio_2000:.2f})"
                )
            else:
                pull_phrase = "but Cuba did not pull away on either metric"
            verdict = (
                f"SUPPORTED — Cuba's 2000 LE was {le_cub_2000:.1f}y vs LATAM peer mean "
                f"{le_peer_mean_2000:.1f}y (gap {le_gap_2000:+.1f}y, threshold +{LE_GAP_THRESHOLD_YEARS:.1f}y). "
                f"Cuban IMR was {imr_cub_2000:.1f}/1k vs peer mean {imr_peer_mean_2000:.1f}/1k "
                f"(ratio {imr_ratio_2000:.2f}, threshold ≤{IMR_RATIO_THRESHOLD:.2f}). "
                f"LE rank {le_cub_rank}/{len(le_2000_rank_pool)}, IMR rank {imr_cub_rank}/{len(imr_2000_rank_pool)}. "
                f"{pull_phrase}."
            )
        elif primary1_le_outperform or primary2_imr_outperform:
            held = []
            if primary1_le_outperform:
                held.append(f"LE gap {le_gap_2000:+.1f}y at 2000")
            if primary2_imr_outperform:
                held.append(f"IMR ratio {imr_ratio_2000:.2f}")
            missed = []
            if not primary1_le_outperform:
                missed.append(f"LE gap only {le_gap_2000:+.1f}y (need ≥{LE_GAP_THRESHOLD_YEARS:.1f})")
            if not primary2_imr_outperform:
                missed.append(f"IMR ratio {imr_ratio_2000:.2f} (need ≤{IMR_RATIO_THRESHOLD:.2f})")
            verdict = (
                f"partial — one metric meets the bar, the other does not. "
                f"Held: {'; '.join(held)}. Missed: {'; '.join(missed)}. "
                f"LE rank {le_cub_rank}/{len(le_2000_rank_pool)}, IMR rank {imr_cub_rank}/{len(imr_2000_rank_pool)}."
            )
        else:
            verdict = (
                f"refuted — Neither primary threshold met. "
                f"2000 LE gap {le_gap_2000:+.1f}y (need ≥{LE_GAP_THRESHOLD_YEARS:.1f}y); "
                f"IMR ratio {imr_ratio_2000:.2f} (need ≤{IMR_RATIO_THRESHOLD:.2f}). "
                f"LE rank {le_cub_rank}/{len(le_2000_rank_pool)}, IMR rank {imr_cub_rank}/{len(imr_2000_rank_pool)}."
            )
        all_pass = both

    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "method_valid": method_valid,
        "primary1_le_outperform": primary1_le_outperform,
        "primary2_imr_outperform": primary2_imr_outperform,
        "pulled_away": pulled_away,
        "thresholds": {
            "le_gap_threshold_years": LE_GAP_THRESHOLD_YEARS,
            "imr_ratio_threshold": IMR_RATIO_THRESHOLD,
            "min_peer_coverage": MIN_PEER_COVERAGE,
        },
        "endpoints": {
            "le_cub_1960": le_cub_1960,
            "le_cub_2000": le_cub_2000,
            "le_peer_mean_1960": le_peer_mean_1960,
            "le_peer_mean_2000": le_peer_mean_2000,
            "le_gap_1960": le_gap_1960,
            "le_gap_2000": le_gap_2000,
            "le_gap_widening_1960_to_2000": le_gap_widening,
            "imr_cub_1960": imr_cub_1960,
            "imr_cub_2000": imr_cub_2000,
            "imr_peer_mean_1960": imr_peer_mean_1960,
            "imr_peer_mean_2000": imr_peer_mean_2000,
            "imr_ratio_1960": imr_ratio_1960,
            "imr_ratio_2000": imr_ratio_2000,
            "imr_ratio_improvement_1960_to_2000": imr_ratio_improvement,
        },
        "ranks_2000": {
            "le_cub_rank": le_cub_rank,
            "le_pool_size": len(le_2000_rank_pool),
            "imr_cub_rank": imr_cub_rank,
            "imr_pool_size": len(imr_2000_rank_pool),
        },
        "soviet_subsidy_subperiod": {
            "le_cub_1991": le_cub_1991,
            "imr_cub_1991": imr_cub_1991,
            "le_gap_1991": le_gap_1991,
            "imr_ratio_1991": imr_ratio_1991,
            "le_gap_change_1991_to_2000": (
                (le_gap_2000 - le_gap_1991) if (le_gap_2000 is not None and le_gap_1991 is not None) else None
            ),
            "imr_ratio_change_1991_to_2000": (
                (imr_ratio_2000 - imr_ratio_1991) if (imr_ratio_2000 is not None and imr_ratio_1991 is not None) else None
            ),
        },
        "peer_coverage": {
            "le_peers_with_data_1960": len(le_peer_1960_vals),
            "le_peers_with_data_2000": len(le_peer_2000_vals),
            "imr_peers_with_data_1960": len(imr_peer_1960_vals),
            "imr_peers_with_data_2000": len(imr_peer_2000_vals),
            "n_peers_total": len(PEERS),
        },
        "peer_endpoints_2000": {
            "le": {c: le_peer_2000[c] for c in PEERS},
            "imr": {c: imr_peer_2000[c] for c in PEERS},
        },
        "data_quality_caveat": (
            "WDI back-fills Cuban 1960-2000 estimates from Cuban government sources; "
            "WHO GHO independent life-expectancy series begins around 2000 so a "
            "1960-2000 cross-check from a fully-independent publisher is not possible "
            "with current vintages. Ranking and gap estimates retain the official-source "
            "lineage; treat magnitudes with the standard 1-2 year uncertainty band."
        ),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    # ---------- Chart: dual-panel via series annotations ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
    ]
    series = []
    # Cuba in red as treated; peers in palette
    cub_le = (
        le[le["country_iso3"] == "CUB"][["year", "value"]].dropna().sort_values("year")
    )
    series.append({
        "id": "CUB",
        "label": "CUB (treated)",
        "color": "#C0392B",
        "treated": True,
        "points": [{"x": int(r.year), "y": float(r.value)} for r in cub_le.itertuples()],
    })
    for i, c in enumerate(PEERS):
        sub = le[le["country_iso3"] == c][["year", "value"]].dropna().sort_values("year")
        if sub.empty:
            continue
        series.append({
            "id": c,
            "label": c,
            "color": palette[i % len(palette)],
            "treated": False,
            "points": [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()],
        })

    le_2000_str = f"{le_gap_2000:+.1f}y" if le_gap_2000 is not None else "n/a"
    imr_ratio_str = f"{imr_ratio_2000:.2f}" if imr_ratio_2000 is not None else "n/a"

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Life expectancy at birth, Cuba vs LATAM middle-income peers, 1960-2000",
        "subtitle": (
            f"Cuba 1960: {le_cub_1960:.1f}y → 2000: {le_cub_2000:.1f}y. "
            f"Peer mean 1960: {le_peer_mean_1960:.1f}y → 2000: {le_peer_mean_2000:.1f}y. "
            f"2000 gap: {le_2000_str} (threshold ≥ +{LE_GAP_THRESHOLD_YEARS:.1f}y). "
            f"2000 IMR ratio CUB/peer-mean: {imr_ratio_str} (threshold ≤ {IMR_RATIO_THRESHOLD:.2f})."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Life expectancy at birth (years)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 1959, "label": "Cuban revolution"},
            {"type": "vline", "x": 1962, "label": "US embargo"},
            {"type": "vline", "x": SOVIET_END, "label": "Soviet subsidies end"},
            {"type": "note", "label": (
                f"Peer pool: {', '.join(PEERS)}. "
                f"Cuban LE rank at 2000: {le_cub_rank}/{len(le_2000_rank_pool)} "
                f"(higher is better). IMR rank: {imr_cub_rank}/{len(imr_2000_rank_pool)} "
                f"(lower is better)."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients table ----------
    rows = [
        {"spec": "primary1_le", "term": "le_cub_2000", "estimate": le_cub_2000},
        {"spec": "primary1_le", "term": "le_peer_mean_2000", "estimate": le_peer_mean_2000},
        {"spec": "primary1_le", "term": "le_gap_2000", "estimate": le_gap_2000},
        {"spec": "primary1_le", "term": "le_gap_1960", "estimate": le_gap_1960},
        {"spec": "primary1_le", "term": "le_gap_widening", "estimate": le_gap_widening},
        {"spec": "primary2_imr", "term": "imr_cub_2000", "estimate": imr_cub_2000},
        {"spec": "primary2_imr", "term": "imr_peer_mean_2000", "estimate": imr_peer_mean_2000},
        {"spec": "primary2_imr", "term": "imr_ratio_2000", "estimate": imr_ratio_2000},
        {"spec": "primary2_imr", "term": "imr_ratio_1960", "estimate": imr_ratio_1960},
        {"spec": "primary2_imr", "term": "imr_ratio_improvement", "estimate": imr_ratio_improvement},
        {"spec": "subperiod", "term": "le_gap_1991", "estimate": le_gap_1991},
        {"spec": "subperiod", "term": "imr_ratio_1991", "estimate": imr_ratio_1991},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- Result card ----------
    def f(x, fmt=".2f"):
        return ("n/a" if x is None else format(x, fmt))

    card = [
        f"# Cuban health outcomes vs LATAM peers, 1960-2000",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Endpoint comparison",
        "",
        "| Metric | Cuba 1960 | Cuba 2000 | Peer mean 1960 | Peer mean 2000 | 2000 gap / ratio |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Life expectancy (y) | {f(le_cub_1960, '.1f')} | {f(le_cub_2000, '.1f')} | "
        f"{f(le_peer_mean_1960, '.1f')} | {f(le_peer_mean_2000, '.1f')} | "
        f"**{f(le_gap_2000, '+.1f')}y** (need ≥ +{LE_GAP_THRESHOLD_YEARS:.1f}y) |",
        f"| Infant mortality (per 1k) | {f(imr_cub_1960, '.1f')} | {f(imr_cub_2000, '.1f')} | "
        f"{f(imr_peer_mean_1960, '.1f')} | {f(imr_peer_mean_2000, '.1f')} | "
        f"**{f(imr_ratio_2000, '.2f')}** (need ≤ {IMR_RATIO_THRESHOLD:.2f}) |",
        "",
        f"At 2000 Cuba ranks **#{le_cub_rank}/{len(le_2000_rank_pool)}** on life expectancy "
        f"(higher = better) and **#{imr_cub_rank}/{len(imr_2000_rank_pool)}** on infant mortality "
        f"(lower = better) within the {len(le_2000_rank_pool)}-country pool (Cuba + 11 peers).",
        "",
        "## Did Cuba pull away or just start ahead?",
        "",
        f"- LE gap 1960: {f(le_gap_1960, '+.1f')}y → 2000: {f(le_gap_2000, '+.1f')}y "
        f"(change {f(le_gap_widening, '+.1f')}y).",
        f"- IMR ratio 1960: {f(imr_ratio_1960, '.2f')} → 2000: {f(imr_ratio_2000, '.2f')} "
        f"(improvement {f(imr_ratio_improvement, '+.2f')}).",
        f"- Pulled away on at least one metric: **{pulled_away}**.",
        "",
        "## Soviet-subsidy sub-period (1991-2000)",
        "",
        "Soviet bloc collapse cut Cuban subsidies hard from 1991. If the gap held or widened "
        "in 1991-2000, that points more towards system-architecture; if the gap narrowed, "
        "subsidies were doing more of the work.",
        "",
        f"- LE gap 1991: {f(le_gap_1991, '+.1f')}y → 2000: {f(le_gap_2000, '+.1f')}y.",
        f"- IMR ratio 1991: {f(imr_ratio_1991, '.2f')} → 2000: {f(imr_ratio_2000, '.2f')}.",
        "",
        "## Method",
        "",
        "Descriptive endpoint comparison; no causal panel estimator. The thresholds come "
        "from a fair-reader interpretation of 'outperform' for a primary-care-emphasising "
        "system: at least one year better on LE at the endpoint, half-or-less infant-mortality "
        "vs the peer pool. The peer pool is the spec's 11 LATAM middle-income countries "
        "(MEX, BRA, ARG, CHL, COL, VEN, DOM, ECU, PER, URY, CRI). Method-validity gate: "
        f"at least {MIN_PEER_COVERAGE} of {len(PEERS)} peers must have data at the 2000 endpoint.",
        "",
        "## Caveats",
        "",
        "- WDI back-fills the Cuban 1960-2000 series from Cuban government sources. WHO GHO "
        "  independent life-expectancy estimates start around 2000, so a contemporaneous WHO "
        "  cross-check across the full window is not possible from current vintages.",
        "- This is descriptive only — it does not separate Cuban primary-care architecture "
        "  from Soviet subsidy effects (1960-1991) or from primary-care diffusion across "
        "  peer countries (Costa Rica's primary care expanded substantially over the same "
        "  window and tracks Cuba closely).",
        "- The 2000 ranking conditions on whichever peer countries had both an embargo-style "
        "  shock and a non-Cuban political system; Venezuela's 1999 oil collapse and "
        "  Argentina's 2001 crisis sit at the back end of this window.",
        "",
        "## Provenance",
        "",
        f"- world_bank_wdi:SP.DYN.LE00.IN",
        f"- world_bank_wdi:SP.DYN.IMRT.IN",
        "",
        "See `manifest.yaml` for exact vintages. Reproduces from `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")
    print(f"  CUB LE 1960→2000: {f(le_cub_1960,'.1f')} → {f(le_cub_2000,'.1f')}")
    print(f"  Peer LE mean 1960→2000: {f(le_peer_mean_1960,'.1f')} → {f(le_peer_mean_2000,'.1f')}")
    print(f"  LE gap 2000: {f(le_gap_2000,'+.1f')}y (threshold +{LE_GAP_THRESHOLD_YEARS:.1f})")
    print(f"  CUB IMR 1960→2000: {f(imr_cub_1960,'.1f')} → {f(imr_cub_2000,'.1f')}")
    print(f"  Peer IMR mean 1960→2000: {f(imr_peer_mean_1960,'.1f')} → {f(imr_peer_mean_2000,'.1f')}")
    print(f"  IMR ratio 2000: {f(imr_ratio_2000,'.2f')} (threshold ≤{IMR_RATIO_THRESHOLD:.2f})")
    print(f"  CUB rank LE: {le_cub_rank}/{len(le_2000_rank_pool)}; IMR: {imr_cub_rank}/{len(imr_2000_rank_pool)}")


if __name__ == "__main__":
    sys.exit(main())
