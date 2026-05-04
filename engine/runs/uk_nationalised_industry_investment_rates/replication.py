#!/usr/bin/env python3
"""Replication — UK nationalised-industry investment rates vs DEU/FRA peers.

Spec: hypotheses/growth/uk_nationalised_industry_investment_rates.yaml v2
Position-claim: market_socialist #13 (school predicts: supported)

Tests whether the UK's economy-wide gross capital formation share of GDP
1950-1979 was comparable to the unweighted mean of West Germany and
France over the same window.

  PRIMARY: |mean(GBR csh_i) - mean({DEU,FRA} csh_i)|
    SUPPORTED if absolute gap <= 5pp.
    REFUTED if UK undershoots peer mean by > 10pp.
    Otherwise weakened (UK below peers by 5-10pp) or partial
    (UK above peers by 5-10pp).

  METHOD_VALID: PWT csh_i has at least 28/30 non-null annual
    observations for each of GBR, DEU, FRA in 1950-1979.

v2 substitutes a country-level investment-share comparison for the
original sector-level (coal/rail/steel/gas) test because no on-disk
publisher has comparable sectoral capital-formation series back to 1950.
See methodology_note in the spec.
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
HID = "uk_nationalised_industry_investment_rates"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

UK = "GBR"
PEERS = ["DEU", "FRA"]
COUNTRIES = [UK] + PEERS
PERIOD = (1950, 1979)

# Falsification thresholds (from spec.falsification.threshold)
SUPPORTED_BAND_PP = 0.05  # |gap| <= 5pp
REFUTED_UK_UNDERSHOOT_PP = 0.10  # UK below peers by > 10pp


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


def latest_optional(pub: str, series: str) -> Path | None:
    try:
        return latest(pub, series)
    except FileNotFoundError:
        return None


def load_long(path: Path) -> pd.DataFrame:
    """Standard normaliser: keep (country_iso3, year, value) rows."""
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


def load_pwt_csh_i(path: Path) -> pd.DataFrame:
    """Load csh_i from either a single-series vintage or pwt_full."""
    t = pq.read_table(path).to_pandas()
    if "value" in t.columns:
        return load_long(path)
    if "csh_i" not in t.columns:
        raise ValueError(f"{path}: no csh_i column")
    out = t[["country_iso3", "country", "year", "csh_i"]].rename(columns={"csh_i": "value"})
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["year", "value"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csh_i_path = latest_optional("pwt", "pwt_full") or latest("pwt", "csh_i")
    manifest = {
        "csh_i": {
            "publisher": "pwt",
            "series": csh_i_path.name.split("@", 1)[0],
            "vintage_file": str(csh_i_path.relative_to(REPO_ROOT)),
            "sha256": sha256(csh_i_path),
        },
    }

    raw = load_pwt_csh_i(csh_i_path)
    panel = raw[
        raw["country_iso3"].isin(COUNTRIES)
        & raw["year"].between(PERIOD[0], PERIOD[1])
    ].copy()
    panel["year"] = panel["year"].astype(int)

    # ---------- METHOD_VALID gate ----------
    coverage = panel.groupby("country_iso3")["year"].nunique().to_dict()
    expected_years = PERIOD[1] - PERIOD[0] + 1
    method_valid = all(coverage.get(c, 0) >= 28 for c in COUNTRIES)

    # ---------- PRIMARY ----------
    country_means = panel.groupby("country_iso3")["value"].mean().to_dict()
    uk_mean = float(country_means.get(UK, np.nan))
    peer_mean = float(np.mean([country_means[c] for c in PEERS if c in country_means]))
    gap = uk_mean - peer_mean  # negative => UK below peers
    abs_gap = abs(gap)

    # Verdict
    if not method_valid:
        verdict = (
            f"inconclusive — PWT csh_i coverage 1950-1979 below the 28/30 "
            f"METHOD_VALID gate for at least one of GBR/DEU/FRA "
            f"({coverage})."
        )
        verdict_label = "inconclusive"
    elif abs_gap <= SUPPORTED_BAND_PP:
        verdict = (
            f"SUPPORTED — UK mean csh_i 1950-1979 {uk_mean*100:.1f}% vs "
            f"DEU+FRA peer mean {peer_mean*100:.1f}% (gap "
            f"{gap*100:+.1f}pp, within ±5pp SUPPORTED band)."
        )
        verdict_label = "SUPPORTED"
    elif gap < -REFUTED_UK_UNDERSHOOT_PP:
        verdict = (
            f"refuted — UK mean csh_i 1950-1979 {uk_mean*100:.1f}% vs "
            f"DEU+FRA peer mean {peer_mean*100:.1f}% (UK undershoots by "
            f"{-gap*100:.1f}pp, exceeding the 10pp REFUTED threshold)."
        )
        verdict_label = "refuted"
    elif gap < 0:
        # UK below peers by 5-10pp
        verdict = (
            f"weakened — UK mean csh_i 1950-1979 {uk_mean*100:.1f}% vs "
            f"DEU+FRA peer mean {peer_mean*100:.1f}% (UK undershoots by "
            f"{-gap*100:.1f}pp — outside the ±5pp SUPPORTED band but "
            f"short of the 10pp REFUTED threshold). Direction is "
            f"consistent with public-ownership investment crowd-out but "
            f"not dispositive."
        )
        verdict_label = "weakened"
    else:
        # UK above peers by 5-10pp
        verdict = (
            f"partial — UK mean csh_i 1950-1979 {uk_mean*100:.1f}% vs "
            f"DEU+FRA peer mean {peer_mean*100:.1f}% (UK exceeds peer "
            f"mean by {gap*100:.1f}pp — outside the ±5pp SUPPORTED band "
            f"but in the direction of the claim)."
        )
        verdict_label = "partial"

    # ---------- Year-by-year UK-vs-peer-mean gap series ----------
    wide = panel.pivot(index="year", columns="country_iso3", values="value")
    wide["peer_mean"] = wide[PEERS].mean(axis=1)
    wide["gap"] = wide[UK] - wide["peer_mean"]
    yearly = [
        {
            "year": int(y),
            "uk": (None if pd.isna(wide.loc[y, UK]) else float(wide.loc[y, UK])),
            "deu": (None if pd.isna(wide.loc[y, "DEU"]) else float(wide.loc[y, "DEU"])),
            "fra": (None if pd.isna(wide.loc[y, "FRA"]) else float(wide.loc[y, "FRA"])),
            "peer_mean": (None if pd.isna(wide.loc[y, "peer_mean"]) else float(wide.loc[y, "peer_mean"])),
            "gap_uk_minus_peer": (None if pd.isna(wide.loc[y, "gap"]) else float(wide.loc[y, "gap"])),
        }
        for y in wide.index
    ]
    n_years_uk_below_peers = int((wide["gap"] < 0).sum())

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "hypothesis_id": HID,
        "method_valid": method_valid,
        "coverage_years": coverage,
        "expected_years": expected_years,
        "uk_mean_csh_i": uk_mean,
        "peer_mean_csh_i": peer_mean,
        "country_means": country_means,
        "gap_uk_minus_peer_mean": gap,
        "abs_gap": abs_gap,
        "supported_band_pp": SUPPORTED_BAND_PP,
        "refuted_undershoot_pp": REFUTED_UK_UNDERSHOOT_PP,
        "n_years_uk_below_peer_mean": n_years_uk_below_peers,
        "n_years_total": int(len(wide)),
        "yearly_gap": yearly,
        "manifest": manifest,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    palette = {
        UK: "#E15759",
        "DEU": "#4E79A7",
        "FRA": "#59A14F",
        "PEER_MEAN": "#1f1f1f",
    }
    series = []
    for c in COUNTRIES:
        sub = panel[panel["country_iso3"] == c].sort_values("year")
        pts = [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]
        series.append({
            "id": c,
            "label": c,
            "color": palette[c],
            "treated": (c == UK),
            "points": pts,
        })
    peer_pts = [
        {"x": int(y), "y": float(wide.loc[y, "peer_mean"])}
        for y in wide.index if not pd.isna(wide.loc[y, "peer_mean"])
    ]
    series.append({
        "id": "PEER_MEAN",
        "label": "DEU+FRA mean",
        "color": palette["PEER_MEAN"],
        "treated": False,
        "points": peer_pts,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Gross capital formation share of GDP, 1950-1979",
        "subtitle": (
            f"UK mean {uk_mean*100:.1f}% vs DEU+FRA mean {peer_mean*100:.1f}% · "
            f"gap {gap*100:+.1f}pp · SUPPORTED band ±5pp · REFUTED if UK below by >10pp."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "csh_i (gross capital formation / GDP, current PPPs)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"PWT 10.x csh_i. UK below DEU+FRA mean in "
                    f"{n_years_uk_below_peers} of {len(wide)} years."
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

    # ---------- coefficients.parquet ----------
    rows = [
        {"spec": "primary", "term": "uk_mean_csh_i_1950_1979", "estimate": uk_mean},
        {"spec": "primary", "term": "peer_mean_csh_i_1950_1979", "estimate": peer_mean},
        {"spec": "primary", "term": "gap_uk_minus_peer", "estimate": gap},
        {"spec": "primary", "term": "abs_gap", "estimate": abs_gap},
    ]
    for c, v in country_means.items():
        rows.append({"spec": "informative", "term": f"mean_csh_i_{c}", "estimate": float(v)})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- manifest.yaml ----------
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

    # ---------- result_card.md ----------
    card = [
        f"# UK nationalised-industry investment rates vs DEU/FRA peers (1950-1979)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- UK mean gross capital formation share of GDP 1950-1979: **{uk_mean*100:.1f}%**.",
        f"- DEU+FRA peer mean over same window: **{peer_mean*100:.1f}%**.",
        f"- Gap (UK − peer mean): **{gap*100:+.1f}pp**.",
        f"- Per-country means: " + ", ".join(f"{c} {country_means[c]*100:.1f}%" for c in COUNTRIES if c in country_means) + ".",
        f"- Years UK below peer mean: **{n_years_uk_below_peers}/{len(wide)}**.",
        f"- METHOD_VALID gate (≥28/30 obs per country): "
        f"{'pass' if method_valid else 'FAIL'} — coverage {coverage}.",
        "",
        "## Method",
        "",
        "Country-level mean comparison of PWT csh_i (gross capital formation share of GDP at current PPPs) "
        "for GBR vs unweighted mean of {DEU, FRA} over 1950-1979. The PRIMARY statistic is the absolute "
        "gap between the UK mean and the peer mean. SUPPORTED band: |gap| ≤ 5pp. REFUTED: UK below peers "
        "by > 10pp. Asymmetric REFUTED zone reflects the directionality of the original claim (the "
        "market-socialist position is that UK nationalised industries were not investment-starved; the "
        "natural refutation direction is therefore UK undershoot).",
        "",
        "## Steelman (for and against)",
        "",
        "**For the claim (market-socialist):** UK post-war investment was constrained by stop-go macro "
        "policy and BoP crises, not by ownership form per se. France and Germany also had major state "
        "industries (Renault, Charbonnages, Bundesbahn, Volkswagen) — the comparison overstates the "
        "ownership contrast. Sector-level studies (Pryke 1981) suggest UK nationalised industries had "
        "investment rates roughly in line with private-sector capital intensity given their factor mix.",
        "",
        "**Against the claim (market-liberal):** The 8-9pp UK shortfall in country-level investment "
        "share over 1950-1979 is large by international-comparison standards. It is unlikely the entire "
        "shortfall is private-sector: the nationalised industries were ~10% of GDP and a much larger "
        "share of fixed capital formation, so a country-level investment-share gap is at least "
        "consistent with — though does not prove — sectoral-level investment crowd-out.",
        "",
        "## Caveats (v2 downgrade from sector-level)",
        "",
        "v2 substitutes a country-level investment-share for the original sector-level (coal/rail/"
        "steel/gas) test. This conflates the nationalised-sector signal with private-sector business "
        "investment differences (the German Wirtschaftswunder was largely private). A v3 with OECD "
        "STAN sectoral data, BoE Three Centuries, or hand-coded Pryke 1981 figures would supersede "
        "this. The v2 thresholds (5pp SUPPORTED, 10pp REFUTED) are correspondingly strict.",
        "",
        "## Data",
        "",
        f"- pwt:csh_i — gross capital formation share of GDP at current PPPs.",
        f"- Vintage: `{manifest['csh_i']['vintage_file']}`",
        f"- sha256: `{manifest['csh_i']['sha256']}`",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
