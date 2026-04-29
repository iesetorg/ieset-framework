#!/usr/bin/env python3
"""Replication — Maoist precondition for Deng-era reform growth (1949-1976).

Spec: hypotheses/growth/maoist_precondition_for_deng_reform_growth.yaml v1
Position-claim: marxist_leninist #4 (school predicts: supported)

Tests the Marxist-Leninist claim that pre-1978 Maoist development built the
human-capital base that later enabled post-1978 reform growth. Single-country
descriptive trajectory CHN 1949-1976 with LMIC peer-median comparators.

PRIMARY (dispositive):
  P1: Life-expectancy gain — CHN_1976_le >= 1.30 * CHN_1949_le
      (i.e. at least a 30% rise from 1949 baseline, per spec falsification rule).
  P2: Peer-relative life-expectancy — CHN_1976_le >= LMIC peer-median 1976 le
      (i.e. CHN converged to or above LMIC peer median by 1976).

INFORMATIVE (do not gate the verdict):
  - GDP per-capita level vs LMIC peer median (Maddison) — does CHN 1976 sit at
    or above the peer median?
  - Primary-school gross enrolment 1976 if WDI data exists for CHN at that point.

METHOD_VALID:
  - china_manual:life_expectancy_at_birth_years has CHN data for 1949 baseline
    and 1976 endpoint.
  - un_wpp:life_expectancy_at_birth has at least 6 of 9 LMIC peers in 1976.

The spec's life-expectancy series is `world_bank_wdi:SP.DYN.LE00.IN`, but WDI
coverage typically begins 1960; pre-1960 CHN values come from the curated
`china_manual:life_expectancy_at_birth_years` parquet (built from Banister 1987
and WHO_GHO). We use both: china_manual for the 1949 baseline, WDI for the
1976 endpoint where available, with china_manual fallback. Manifest pins both.

Falsification semantics (per HYPOTHESIS_FRAMEWORK_AUDIT.md):
  SUPPORTED iff P1 AND P2 hold.
  partial iff exactly one of P1/P2 holds.
  refuted iff both fail.
  inconclusive if data gap on the dispositive series.
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
HID = "maoist_precondition_for_deng_reform_growth"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRY = "CHN"
BASELINE_YEAR = 1949
ENDPOINT_YEAR = 1976
GDP_PEER_YEAR = 1976  # Maddison has CHN through 2018; peer-median for 1976

# LMIC peer set: large agrarian developing-economy peers of CHN circa 1949.
# Avoids OECD industrialised states; includes a mix of Asia/LatAm/MENA so we
# are not just measuring "Asian take-off" effects.
LMIC_PEERS = [
    "IND",  # India
    "IDN",  # Indonesia
    "PAK",  # Pakistan (BGD pre-1971 inside PAK)
    "BRA",  # Brazil
    "MEX",  # Mexico
    "EGY",  # Egypt
    "NGA",  # Nigeria
    "TUR",  # Turkey
    "THA",  # Thailand
    "PHL",  # Philippines
    "IRN",  # Iran
]

# Thresholds (sharpened from the spec's prose rule)
P1_LE_GROWTH_FACTOR = 1.30  # 1976/1949 life-expectancy ratio threshold
P2_PEER_RATIO = 1.00        # CHN_1976_le must be >= peer-median 1976


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
    """Normalise a publisher parquet to (country_iso3, year, value).
    Handles WDI/IMF/OECD-style 'value' columns and OWID-style metric-name
    columns (last non-meta column treated as value)."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator", "indicator_id"}
        candidates = [c for c in t.columns if c not in meta]
        if not candidates:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        # take the first numeric-looking candidate
        t = t.rename(columns={candidates[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def load_maddison(path: Path) -> pd.DataFrame:
    """Maddison MPD2020 uses 'gdppc' as the value column."""
    t = pq.read_table(path).to_pandas()
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    if "gdppc" in t.columns:
        t = t.rename(columns={"gdppc": "value"})
    elif "value" not in t.columns:
        raise ValueError(f"{path}: no gdppc/value column ({list(t.columns)})")
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])[["country_iso3", "year", "value"]]


def value_at(df: pd.DataFrame, country: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].iloc[0])


def nearest_value(df: pd.DataFrame, country: str, target_year: int, max_gap: int = 2) -> tuple[float | None, int | None]:
    """Return (value, year) at the closest year to target within max_gap."""
    sub = df[df["country_iso3"] == country]
    if sub.empty:
        return None, None
    sub = sub.copy()
    sub["abs_gap"] = (sub["year"] - target_year).abs()
    sub = sub[sub["abs_gap"] <= max_gap].sort_values("abs_gap")
    if sub.empty:
        return None, None
    row = sub.iloc[0]
    return float(row["value"]), int(row["year"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Load life-expectancy sources ----
    cm_le_path = latest("china_manual", "life_expectancy_at_birth_years")
    wdi_le_path = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    un_le_path = latest("un_wpp", "life_expectancy_at_birth")
    mpd_path = latest("maddison", "mpd2020")
    wdi_lit_path = latest("world_bank_wdi", "SE.ADT.LITR.ZS")
    wdi_enrr_path = latest("world_bank_wdi", "SE.PRM.ENRR")

    manifest = {
        "life_expectancy_chn_manual": {
            "publisher": "china_manual",
            "series": "life_expectancy_at_birth_years",
            "vintage_file": str(cm_le_path.relative_to(REPO_ROOT)),
            "sha256": sha256(cm_le_path),
        },
        "life_expectancy_wdi": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.LE00.IN",
            "vintage_file": str(wdi_le_path.relative_to(REPO_ROOT)),
            "sha256": sha256(wdi_le_path),
        },
        "life_expectancy_un_wpp": {
            "publisher": "un_wpp",
            "series": "life_expectancy_at_birth",
            "vintage_file": str(un_le_path.relative_to(REPO_ROOT)),
            "sha256": sha256(un_le_path),
        },
        "gdp_pc_maddison": {
            "publisher": "maddison",
            "series": "mpd2020",
            "vintage_file": str(mpd_path.relative_to(REPO_ROOT)),
            "sha256": sha256(mpd_path),
        },
        "literacy_wdi": {
            "publisher": "world_bank_wdi",
            "series": "SE.ADT.LITR.ZS",
            "vintage_file": str(wdi_lit_path.relative_to(REPO_ROOT)),
            "sha256": sha256(wdi_lit_path),
        },
        "primary_enrolment_gross_wdi": {
            "publisher": "world_bank_wdi",
            "series": "SE.PRM.ENRR",
            "vintage_file": str(wdi_enrr_path.relative_to(REPO_ROOT)),
            "sha256": sha256(wdi_enrr_path),
        },
    }

    cm_le = load_long(cm_le_path)
    wdi_le = load_long(wdi_le_path)
    un_le = load_long(un_le_path)
    mpd = load_maddison(mpd_path)
    wdi_lit = load_long(wdi_lit_path)
    wdi_enrr = load_long(wdi_enrr_path)

    # ---- CHN baseline (1949) and endpoint (1976) life expectancy ----
    # Baseline: china_manual is the only source for pre-1960.
    le_chn_1949 = value_at(cm_le, COUNTRY, BASELINE_YEAR)
    if le_chn_1949 is None:
        # Fall back to nearest year within 2.
        le_chn_1949, le_chn_1949_year = nearest_value(cm_le, COUNTRY, BASELINE_YEAR, max_gap=2)
    else:
        le_chn_1949_year = BASELINE_YEAR

    # Endpoint 1976: prefer WDI, fall back to china_manual then UN WPP.
    le_chn_1976 = value_at(wdi_le, COUNTRY, ENDPOINT_YEAR)
    le_chn_1976_source = "world_bank_wdi" if le_chn_1976 is not None else None
    if le_chn_1976 is None:
        le_chn_1976 = value_at(cm_le, COUNTRY, ENDPOINT_YEAR)
        le_chn_1976_source = "china_manual" if le_chn_1976 is not None else None
    if le_chn_1976 is None:
        le_chn_1976 = value_at(un_le, COUNTRY, ENDPOINT_YEAR)
        le_chn_1976_source = "un_wpp" if le_chn_1976 is not None else None

    if le_chn_1949 is None or le_chn_1976 is None:
        verdict = (
            f"inconclusive (data gap on china_manual:life_expectancy_at_birth_years "
            f"or world_bank_wdi:SP.DYN.LE00.IN — could not resolve "
            f"CHN baseline 1949 ({le_chn_1949}) or endpoint 1976 ({le_chn_1976}))."
        )
        diagnostics = {
            "verdict": verdict,
            "reason": "data_gap_on_chn_life_expectancy",
            "le_chn_1949": le_chn_1949,
            "le_chn_1976": le_chn_1976,
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        (OUT_DIR / "result_card.md").write_text(
            f"# Maoist precondition for Deng reform growth\n\n**Verdict:** {verdict}\n"
        )
        # Still write manifest + empty chart and coefficients for downstream layout.
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": HID,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "estimator": "descriptive",
            "vintages": manifest,
        }, sort_keys=False))
        (OUT_DIR / "chart_data.json").write_text(json.dumps({
            "kind": "result", "chart_id": f"{HID}/fig1", "title": "Data gap",
            "type": "line", "x_axis": {"label": "Year", "type": "linear"},
            "y_axis": {"label": "Life expectancy (years)", "type": "linear"},
            "series": [], "annotations": [], "sources": [], "permalink": f"/h/{HID}",
        }, indent=2) + "\n")
        pd.DataFrame([{"spec": "primary", "term": "le_chn_1949", "estimate": le_chn_1949},
                      {"spec": "primary", "term": "le_chn_1976", "estimate": le_chn_1976}]).to_parquet(
            OUT_DIR / "coefficients.parquet", index=False)
        print(f"verdict: {verdict}")
        return 0

    le_growth_factor = le_chn_1976 / le_chn_1949
    p1_pass = le_growth_factor >= P1_LE_GROWTH_FACTOR

    # ---- LMIC peer-median life expectancy in 1976 ----
    # Use UN WPP first (broad coverage), fall back to WDI.
    peer_le_1976 = {}
    for c in LMIC_PEERS:
        v = value_at(un_le, c, ENDPOINT_YEAR)
        if v is None:
            v = value_at(wdi_le, c, ENDPOINT_YEAR)
        if v is not None:
            peer_le_1976[c] = float(v)

    if len(peer_le_1976) >= 6:
        peer_median_1976 = float(np.median(list(peer_le_1976.values())))
        peer_mean_1976 = float(np.mean(list(peer_le_1976.values())))
        p2_pass = le_chn_1976 >= peer_median_1976 * P2_PEER_RATIO
        peer_method_valid = True
    else:
        peer_median_1976 = None
        peer_mean_1976 = None
        p2_pass = None
        peer_method_valid = False

    # ---- Informative: GDP per capita 1976 vs LMIC peer median ----
    gdp_chn_1976 = value_at(mpd, COUNTRY, GDP_PEER_YEAR)
    gdp_chn_1949 = value_at(mpd, COUNTRY, BASELINE_YEAR)
    peer_gdp_1976 = {}
    for c in LMIC_PEERS:
        v = value_at(mpd, c, GDP_PEER_YEAR)
        if v is not None:
            peer_gdp_1976[c] = float(v)
    peer_gdp_median_1976 = float(np.median(list(peer_gdp_1976.values()))) if len(peer_gdp_1976) >= 6 else None
    chn_gdp_ratio_to_peer_median = (
        gdp_chn_1976 / peer_gdp_median_1976 if (gdp_chn_1976 and peer_gdp_median_1976) else None
    )

    # ---- Informative: primary-school gross enrolment near 1976 ----
    chn_enrr_1976, chn_enrr_year = nearest_value(wdi_enrr, COUNTRY, ENDPOINT_YEAR, max_gap=4)
    chn_lit_1976, chn_lit_year = nearest_value(wdi_lit, COUNTRY, ENDPOINT_YEAR, max_gap=10)

    # ---- Verdict ----
    if peer_method_valid:
        all_pass = bool(p1_pass) and bool(p2_pass)
        if all_pass:
            verdict = (
                f"SUPPORTED — CHN life expectancy rose {le_chn_1949:.1f} (1949) → "
                f"{le_chn_1976:.1f} (1976), a factor of {le_growth_factor:.2f}× "
                f"(threshold ≥ {P1_LE_GROWTH_FACTOR:.2f}×). 1976 LMIC peer-median = "
                f"{peer_median_1976:.1f}; CHN sits {le_chn_1976 - peer_median_1976:+.1f}y "
                f"above. Maoist-era human-capital expansion is consistent with the "
                f"precondition claim."
            )
        elif (not p1_pass) and (not p2_pass):
            verdict = (
                f"refuted — CHN 1976 life expectancy {le_chn_1976:.1f} is "
                f"{le_growth_factor:.2f}× the 1949 level (below "
                f"{P1_LE_GROWTH_FACTOR:.2f}× threshold) AND below the LMIC "
                f"peer-median ({peer_median_1976:.1f}). The Maoist-precondition "
                f"premise does not hold descriptively."
            )
        else:
            failed = "growth threshold" if not p1_pass else "peer-median benchmark"
            verdict = (
                f"partial — CHN 1976 life expectancy {le_chn_1976:.1f} (1949 baseline "
                f"{le_chn_1949:.1f}, factor {le_growth_factor:.2f}×); LMIC peer-median "
                f"1976 = {peer_median_1976:.1f}. One of two primary tests held; the "
                f"{failed} did not."
            )
    else:
        verdict = (
            f"inconclusive — only {len(peer_le_1976)} of {len(LMIC_PEERS)} LMIC peers "
            f"have 1976 life-expectancy data; need ≥6 for a defensible peer median. "
            f"CHN: 1949 {le_chn_1949:.1f} → 1976 {le_chn_1976:.1f}, factor "
            f"{le_growth_factor:.2f}× (P1 {'pass' if p1_pass else 'fail'})."
        )

    diagnostics = {
        "verdict": verdict,
        "primary1_le_growth_factor_pass": bool(p1_pass) if p1_pass is not None else None,
        "primary2_le_above_peer_median_pass": bool(p2_pass) if p2_pass is not None else None,
        "method_valid_peer_panel": bool(peer_method_valid),
        "le_chn_1949": le_chn_1949,
        "le_chn_1949_year_used": le_chn_1949_year,
        "le_chn_1976": le_chn_1976,
        "le_chn_1976_source": le_chn_1976_source,
        "le_growth_factor_1976_over_1949": le_growth_factor,
        "p1_threshold_growth_factor": P1_LE_GROWTH_FACTOR,
        "lmic_peer_le_1976": peer_le_1976,
        "lmic_peer_le_median_1976": peer_median_1976,
        "lmic_peer_le_mean_1976": peer_mean_1976,
        "n_peers_with_data": len(peer_le_1976),
        "n_peers_required": 6,
        # Informative (not gating):
        "informative_gdp_chn_1949_maddison_2011usd": gdp_chn_1949,
        "informative_gdp_chn_1976_maddison_2011usd": gdp_chn_1976,
        "informative_lmic_peer_gdp_median_1976": peer_gdp_median_1976,
        "informative_chn_gdp_ratio_to_peer_median_1976": chn_gdp_ratio_to_peer_median,
        "informative_chn_primary_enrr_near_1976": chn_enrr_1976,
        "informative_chn_primary_enrr_year": chn_enrr_year,
        "informative_chn_adult_literacy_near_1976": chn_lit_1976,
        "informative_chn_adult_literacy_year": chn_lit_year,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    # ---- Chart: CHN life-expectancy trajectory + LMIC peer-median ----
    palette = ["#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
               "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658"]

    series = []
    # CHN trajectory: stitch china_manual (pre-1960) + WDI (1960+) for a clean line.
    chn_cm = cm_le[cm_le["country_iso3"] == COUNTRY][["year", "value"]].sort_values("year")
    chn_wdi = wdi_le[wdi_le["country_iso3"] == COUNTRY][["year", "value"]].sort_values("year")
    chn_pts = []
    seen = set()
    for r in chn_cm.itertuples():
        if 1949 <= int(r.year) <= 1990 and int(r.year) not in seen:
            chn_pts.append({"x": int(r.year), "y": float(r.value)})
            seen.add(int(r.year))
    for r in chn_wdi.itertuples():
        if 1960 <= int(r.year) <= 1990 and int(r.year) not in seen:
            chn_pts.append({"x": int(r.year), "y": float(r.value)})
            seen.add(int(r.year))
    chn_pts.sort(key=lambda p: p["x"])
    series.append({
        "id": "CHN", "label": "China (life expectancy)", "color": "#E15759",
        "treated": True, "points": chn_pts,
    })

    # Peer median trajectory (1949-1990) — annual median across peers with data.
    all_peers = pd.concat([
        un_le[un_le["country_iso3"].isin(LMIC_PEERS)][["country_iso3", "year", "value"]],
        wdi_le[wdi_le["country_iso3"].isin(LMIC_PEERS)][["country_iso3", "year", "value"]],
    ], ignore_index=True)
    all_peers = all_peers.drop_duplicates(subset=["country_iso3", "year"], keep="first")
    all_peers["year"] = all_peers["year"].astype(int)
    peer_median_by_year = (
        all_peers[(all_peers["year"] >= 1949) & (all_peers["year"] <= 1990)]
        .groupby("year")["value"].median().sort_index()
    )
    series.append({
        "id": "PEER_MEDIAN", "label": "LMIC peer median",
        "color": "#1f1f1f", "treated": False,
        "points": [{"x": int(y), "y": float(v)} for y, v in peer_median_by_year.items()],
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "China life expectancy 1949-1990 vs LMIC peer median",
        "subtitle": (
            f"CHN 1949 {le_chn_1949:.1f} → 1976 {le_chn_1976:.1f} "
            f"(factor {le_growth_factor:.2f}×, threshold ≥{P1_LE_GROWTH_FACTOR:.2f}×) · "
            f"1976 peer median {peer_median_1976:.1f}" if peer_median_1976 is not None
            else f"CHN 1949 {le_chn_1949:.1f} → 1976 {le_chn_1976:.1f}"
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Life expectancy at birth (years)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 1949, "label": "PRC founded"},
            {"type": "vline", "x": 1958, "label": "Great Leap"},
            {"type": "vline", "x": 1966, "label": "Cultural Revolution"},
            {"type": "vline", "x": 1976, "label": "End Mao era / endpoint"},
            {"type": "vline", "x": 1978, "label": "Reform era opens"},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    coef_rows = [
        {"spec": "primary1", "term": "le_chn_1949", "estimate": float(le_chn_1949)},
        {"spec": "primary1", "term": "le_chn_1976", "estimate": float(le_chn_1976)},
        {"spec": "primary1", "term": "le_growth_factor_1976_over_1949", "estimate": float(le_growth_factor)},
        {"spec": "primary2", "term": "lmic_peer_le_median_1976",
         "estimate": float(peer_median_1976) if peer_median_1976 is not None else float("nan")},
        {"spec": "informative", "term": "gdp_chn_1976",
         "estimate": float(gdp_chn_1976) if gdp_chn_1976 is not None else float("nan")},
        {"spec": "informative", "term": "lmic_peer_gdp_median_1976",
         "estimate": float(peer_gdp_median_1976) if peer_gdp_median_1976 is not None else float("nan")},
    ]
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "descriptive",
        "vintages": manifest,
    }, sort_keys=False))

    pct_rise = (le_growth_factor - 1.0) * 100.0
    lines = [
        f"# Maoist precondition for Deng-era reform growth",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Life expectancy at birth, CHN 1949: **{le_chn_1949:.1f}y** "
        f"(source: china_manual, year {le_chn_1949_year}).",
        f"- Life expectancy at birth, CHN 1976: **{le_chn_1976:.1f}y** "
        f"(source: {le_chn_1976_source}).",
        f"- Maoist-era life-expectancy gain: **{pct_rise:+.0f}%** over 27 years "
        f"(factor {le_growth_factor:.2f}×; PRIMARY threshold ≥1.30×, "
        f"{'pass' if p1_pass else 'fail'}).",
    ]
    if peer_method_valid:
        lines += [
            f"- LMIC peer-median 1976 life expectancy: **{peer_median_1976:.1f}y** "
            f"(n={len(peer_le_1976)} of {len(LMIC_PEERS)}; mean {peer_mean_1976:.1f}). "
            f"CHN gap to peer median: **{le_chn_1976 - peer_median_1976:+.1f}y** "
            f"({'CHN above' if p2_pass else 'CHN below'} median).",
        ]
    else:
        lines += [
            f"- LMIC peer median NOT computable: only {len(peer_le_1976)} of "
            f"{len(LMIC_PEERS)} peers have 1976 data (need ≥6).",
        ]
    lines += [
        "",
        "## Informative (non-gating)",
        "",
        f"- Maddison GDP per capita (2011 PPP $): CHN 1949 = "
        f"${gdp_chn_1949:,.0f}; CHN 1976 = ${gdp_chn_1976:,.0f}." if (gdp_chn_1949 and gdp_chn_1976)
        else f"- Maddison GDP per capita: CHN data partial.",
        f"- LMIC peer-median GDP-pc 1976: ${peer_gdp_median_1976:,.0f}; "
        f"CHN/peer-median ratio = {chn_gdp_ratio_to_peer_median:.2f}."
        if (peer_gdp_median_1976 and chn_gdp_ratio_to_peer_median)
        else "- LMIC peer-median GDP-pc unavailable.",
        f"- CHN gross primary enrolment near 1976: "
        + (f"{chn_enrr_1976:.1f}% (year {chn_enrr_year})." if chn_enrr_1976 is not None
           else "no WDI data within ±4y of 1976."),
        f"- CHN adult literacy near 1976: "
        + (f"{chn_lit_1976:.1f}% (year {chn_lit_year})." if chn_lit_1976 is not None
           else "no WDI data within ±10y of 1976 (literacy series begins 1982 for CHN)."),
        "",
        "## Method",
        "",
        f"- PRIMARY 1 (dispositive): CHN 1976 life expectancy ÷ CHN 1949 life "
        f"expectancy ≥ {P1_LE_GROWTH_FACTOR:.2f}. The spec phrases this as "
        f"\"≥30% rise above 1949 baseline\".",
        f"- PRIMARY 2 (dispositive): CHN 1976 life expectancy ≥ LMIC peer-median "
        f"1976 (peer set: {', '.join(LMIC_PEERS)}). Requires ≥6 peers with data.",
        f"- INFORMATIVE: GDP-pc level vs peer median, primary-enrolment, "
        f"adult-literacy level.",
        f"- METHOD_VALID gate: ≥6 LMIC peers in the 1976 panel; if fewer, "
        f"emit `inconclusive`.",
        "",
        "## Interpretation",
        "",
        "Within-country single-trajectory descriptive comparison; no causal "
        "identification. The peer-median test guards against attributing "
        "naturally-rising LMIC life expectancy in the 20th century purely to "
        "Maoist policy: if the entire LMIC cohort gained equally, CHN's gain "
        "is not informative for the precondition claim. The descriptive bar "
        "the framework asks of this hypothesis is whether Mao-era CHN reached "
        "human-capital levels comparable to or above its peer cohort by 1976 "
        "— a precondition for the post-1978 productivity catch-up. The test "
        "is silent on counterfactual paths and on the famine-era costs of "
        "the Maoist development model.",
        "",
        "## Sources",
        "",
        f"- china_manual:life_expectancy_at_birth_years (CHN 1949 baseline).",
        f"- world_bank_wdi:SP.DYN.LE00.IN (WDI life expectancy 1960+).",
        f"- un_wpp:life_expectancy_at_birth (LMIC peer panel).",
        f"- maddison:mpd2020 (informative GDP-pc 2011 PPP $).",
        f"- world_bank_wdi:SE.PRM.ENRR / SE.ADT.LITR.ZS (informative).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  CHN life expectancy: 1949 {le_chn_1949:.1f}y → 1976 {le_chn_1976:.1f}y "
          f"(factor {le_growth_factor:.2f}×, P1 threshold {P1_LE_GROWTH_FACTOR:.2f}×: "
          f"{'pass' if p1_pass else 'fail'})")
    if peer_method_valid:
        print(f"  LMIC peer-median 1976: {peer_median_1976:.1f}y (n={len(peer_le_1976)}); "
              f"P2 {'pass' if p2_pass else 'fail'}")
    else:
        print(f"  LMIC peer-median: insufficient coverage ({len(peer_le_1976)} of "
              f"{len(LMIC_PEERS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
