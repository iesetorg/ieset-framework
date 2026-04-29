#!/usr/bin/env python3
"""Replication — Cuban Special Period 1991-2000 health/education resilience
versus an ex-ante-fixed Caribbean + post-Soviet comparator pool.

Spec: hypotheses/growth/cuba_special_period_resilience.yaml v2
Position-claim: marxist_leninist #11 (school predicts: supported)

Tests the dispositive form of the claim that Cuban socialist planning
preserved health/education outputs through the post-1991 external shock
better than market-economy peers of similar pre-shock standing.

  PRIMARY-LE:  (LE_CUB_2000 - LE_CUB_1991) - mean_pool(LE_2000 - LE_1991)
               must be >= 0 years.
  PRIMARY-IMR: ((IMR_CUB_1991 - IMR_CUB_2000) / IMR_CUB_1991)
               - mean_pool(same fraction) must be >= 0.

Comparator pool is fixed in the spec, not selected on observed data:
  Caribbean middle-income peers: JAM, DOM, HTI, NIC
  Post-Soviet transition states:  UKR, MDA, ARM, GEO

INFORMATIVE: primary-school enrolment (SE.PRM.ENRR) trajectory; reported
but does not gate the verdict because WDI coverage of this series is
sparse for several comparators in the 1990s.

METHOD_VALID: at least 4 of 8 comparators must have non-null endpoints
on each PRIMARY metric, otherwise the verdict is inconclusive.

If both primaries hold -> SUPPORTED.
If both primaries fail -> refuted.
If one holds and one fails -> partial.
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
HID = "cuba_special_period_resilience"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "CUB"
CARIBBEAN_POOL = ["JAM", "DOM", "HTI", "NIC"]
POSTSOVIET_POOL = ["UKR", "MDA", "ARM", "GEO"]
COMPARATORS = CARIBBEAN_POOL + POSTSOVIET_POOL

YEAR_START = 1991
YEAR_END = 2000

# A small year-search window each side of the endpoints, in case a country
# is missing exactly 1991 or exactly 2000 (some WDI series have small holes).
YEAR_START_TOL = 1
YEAR_END_TOL = 1

# Falsification thresholds (exact spec wording: "Cuba must NOT
# underperform comparator pool" -> Cuba minus pool mean >= 0).
LE_THRESHOLD_YEARS = 0.0  # PRIMARY-LE: Cuba minus pool mean >= 0 years
IMR_PCT_THRESHOLD = 0.0   # PRIMARY-IMR: Cuba minus pool mean >= 0 (fraction)
METHOD_MIN_COMPARATORS = 4  # at least 4 of 8 comparators with both endpoints


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
    """Standard normaliser for WDI/IMF/OECD: keep (country_iso3, year, value)."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns ({list(t.columns)})")
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


def endpoint_value(df: pd.DataFrame, country: str, target_year: int, tol: int) -> tuple[float | None, int | None]:
    """Return (value, actual_year) for the row at target_year for country, or
    fall back to the nearest year within +/- tol. Returns (None, None) if no
    observation in the window."""
    sub = df[(df["country_iso3"] == country) & (df["year"].between(target_year - tol, target_year + tol))]
    if sub.empty:
        return (None, None)
    sub = sub.assign(dist=(sub["year"] - target_year).abs()).sort_values(["dist", "year"])
    row = sub.iloc[0]
    return (float(row["value"]), int(row["year"]))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    le_path = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    imr_path = latest("world_bank_wdi", "SP.DYN.IMRT.IN")
    sch_path = latest("world_bank_wdi", "SE.PRM.ENRR")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")

    manifest = {
        "life_expectancy_at_birth": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.LE00.IN",
            "vintage_file": str(le_path.relative_to(REPO_ROOT)),
            "sha256": sha256(le_path),
        },
        "infant_mortality_rate": {
            "publisher": "world_bank_wdi",
            "series": "SP.DYN.IMRT.IN",
            "vintage_file": str(imr_path.relative_to(REPO_ROOT)),
            "sha256": sha256(imr_path),
        },
        "school_enrollment_primary": {
            "publisher": "world_bank_wdi",
            "series": "SE.PRM.ENRR",
            "vintage_file": str(sch_path.relative_to(REPO_ROOT)),
            "sha256": sha256(sch_path),
        },
        "gdp_per_capita_ppp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.PP.KD",
            "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdppc_path),
        },
    }

    le = load_long(le_path)
    imr = load_long(imr_path)
    sch = load_long(sch_path)

    def endpoints(df: pd.DataFrame, countries: list[str]) -> dict[str, dict]:
        out = {}
        for c in countries:
            v0, y0 = endpoint_value(df, c, YEAR_START, YEAR_START_TOL)
            v1, y1 = endpoint_value(df, c, YEAR_END, YEAR_END_TOL)
            out[c] = {"start_value": v0, "start_year": y0, "end_value": v1, "end_year": y1}
        return out

    le_ep = endpoints(le, [TREATED] + COMPARATORS)
    imr_ep = endpoints(imr, [TREATED] + COMPARATORS)
    sch_ep = endpoints(sch, [TREATED] + COMPARATORS)

    # ---------- PRIMARY 1: life expectancy change ----------
    le_cub_change = None
    if le_ep[TREATED]["start_value"] is not None and le_ep[TREATED]["end_value"] is not None:
        le_cub_change = le_ep[TREATED]["end_value"] - le_ep[TREATED]["start_value"]

    le_pool_changes = {
        c: (le_ep[c]["end_value"] - le_ep[c]["start_value"])
        for c in COMPARATORS
        if le_ep[c]["start_value"] is not None and le_ep[c]["end_value"] is not None
    }
    le_pool_n = len(le_pool_changes)
    le_pool_mean = float(np.mean(list(le_pool_changes.values()))) if le_pool_n else None
    le_diff = (le_cub_change - le_pool_mean) if (le_cub_change is not None and le_pool_mean is not None) else None

    # ---------- PRIMARY 2: infant mortality % reduction ----------
    imr_cub_pct = None
    if imr_ep[TREATED]["start_value"] not in (None, 0) and imr_ep[TREATED]["end_value"] is not None:
        imr_cub_pct = (imr_ep[TREATED]["start_value"] - imr_ep[TREATED]["end_value"]) / imr_ep[TREATED]["start_value"]

    imr_pool_pcts = {}
    for c in COMPARATORS:
        s, e = imr_ep[c]["start_value"], imr_ep[c]["end_value"]
        if s is not None and e is not None and s > 0:
            imr_pool_pcts[c] = (s - e) / s
    imr_pool_n = len(imr_pool_pcts)
    imr_pool_mean = float(np.mean(list(imr_pool_pcts.values()))) if imr_pool_n else None
    imr_diff = (imr_cub_pct - imr_pool_mean) if (imr_cub_pct is not None and imr_pool_mean is not None) else None

    # ---------- INFORMATIVE: school enrolment ----------
    sch_cub_change = None
    if sch_ep[TREATED]["start_value"] is not None and sch_ep[TREATED]["end_value"] is not None:
        sch_cub_change = sch_ep[TREATED]["end_value"] - sch_ep[TREATED]["start_value"]
    sch_pool_changes = {
        c: (sch_ep[c]["end_value"] - sch_ep[c]["start_value"])
        for c in COMPARATORS
        if sch_ep[c]["start_value"] is not None and sch_ep[c]["end_value"] is not None
    }
    sch_pool_mean = float(np.mean(list(sch_pool_changes.values()))) if sch_pool_changes else None
    sch_diff = (sch_cub_change - sch_pool_mean) if (sch_cub_change is not None and sch_pool_mean is not None) else None

    # ---------- METHOD_VALID gate ----------
    method_valid = (
        le_pool_n >= METHOD_MIN_COMPARATORS
        and imr_pool_n >= METHOD_MIN_COMPARATORS
        and le_cub_change is not None
        and imr_cub_pct is not None
    )

    # ---------- Verdict ----------
    if not method_valid:
        gaps = []
        if le_cub_change is None:
            gaps.append("CUB life-expectancy endpoints missing")
        if imr_cub_pct is None:
            gaps.append("CUB infant-mortality endpoints missing")
        if le_pool_n < METHOD_MIN_COMPARATORS:
            gaps.append(f"only {le_pool_n}/8 comparators have LE endpoints")
        if imr_pool_n < METHOD_MIN_COMPARATORS:
            gaps.append(f"only {imr_pool_n}/8 comparators have IMR endpoints")
        verdict = (
            "inconclusive (data gap on world_bank_wdi:SP.DYN.LE00.IN/SP.DYN.IMRT.IN) — "
            + "; ".join(gaps)
        )
        primary_le_pass = None
        primary_imr_pass = None
    else:
        primary_le_pass = le_diff >= LE_THRESHOLD_YEARS
        primary_imr_pass = imr_diff >= IMR_PCT_THRESHOLD
        if primary_le_pass and primary_imr_pass:
            verdict = (
                f"SUPPORTED — Cuba 1991-2000 LE change "
                f"{le_cub_change:+.2f}y vs comparator-pool mean {le_pool_mean:+.2f}y "
                f"(Cuba minus pool: {le_diff:+.2f}y, threshold >= 0). "
                f"Cuba IMR reduction {imr_cub_pct*100:+.1f}% of 1991 baseline vs "
                f"pool mean {imr_pool_mean*100:+.1f}% (Cuba minus pool: "
                f"{imr_diff*100:+.1f}pp, threshold >= 0). Both primary tests pass."
            )
        elif (not primary_le_pass) and (not primary_imr_pass):
            verdict = (
                f"refuted — Cuba 1991-2000 LE change "
                f"{le_cub_change:+.2f}y is {abs(le_diff):.2f}y BELOW pool mean "
                f"{le_pool_mean:+.2f}y, AND IMR reduction {imr_cub_pct*100:+.1f}% is "
                f"{abs(imr_diff)*100:.1f}pp BELOW pool mean {imr_pool_mean*100:+.1f}%. "
                f"Both primary tests fail."
            )
        else:
            which_held = "LE" if primary_le_pass else "IMR"
            which_failed = "IMR" if primary_le_pass else "LE"
            verdict = (
                f"partial — Cuba 1991-2000: PRIMARY-{which_held} held but "
                f"PRIMARY-{which_failed} did not. LE Cuba {le_cub_change:+.2f}y vs "
                f"pool {le_pool_mean:+.2f}y (diff {le_diff:+.2f}y); IMR reduction "
                f"Cuba {imr_cub_pct*100:+.1f}% vs pool {imr_pool_mean*100:+.1f}% "
                f"(diff {imr_diff*100:+.1f}pp)."
            )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "primary1_le_pass": primary_le_pass,
        "primary2_imr_pass": primary_imr_pass,
        "treated": TREATED,
        "comparator_pool": COMPARATORS,
        "caribbean_pool": CARIBBEAN_POOL,
        "postsoviet_pool": POSTSOVIET_POOL,
        "year_start": YEAR_START,
        "year_end": YEAR_END,
        "le_cub_change_years": le_cub_change,
        "le_pool_mean_change_years": le_pool_mean,
        "le_diff_cub_minus_pool_years": le_diff,
        "le_threshold_years": LE_THRESHOLD_YEARS,
        "le_pool_n": le_pool_n,
        "le_pool_changes": le_pool_changes,
        "imr_cub_pct_reduction": imr_cub_pct,
        "imr_pool_mean_pct_reduction": imr_pool_mean,
        "imr_diff_cub_minus_pool": imr_diff,
        "imr_pct_threshold": IMR_PCT_THRESHOLD,
        "imr_pool_n": imr_pool_n,
        "imr_pool_pct_reductions": imr_pool_pcts,
        "school_cub_change_pct_pts": sch_cub_change,
        "school_pool_mean_change_pct_pts": sch_pool_mean,
        "school_diff_cub_minus_pool": sch_diff,
        "school_pool_n": len(sch_pool_changes),
        "endpoints": {
            "life_expectancy": le_ep,
            "infant_mortality": imr_ep,
            "school_enrolment": sch_ep,
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ---------- Chart ----------
    palette = {
        "CUB": "#E15759",
        "JAM": "#4E79A7",
        "DOM": "#76B7B2",
        "HTI": "#59A14F",
        "NIC": "#EDC948",
        "UKR": "#B07AA1",
        "MDA": "#F28E2B",
        "ARM": "#9C755F",
        "GEO": "#B6992D",
    }

    def country_series(df: pd.DataFrame, country: str) -> list[dict]:
        sub = df[(df["country_iso3"] == country) & (df["year"].between(YEAR_START - 2, YEAR_END + 1))]
        sub = sub.dropna(subset=["value"]).sort_values("year")
        return [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]

    series = []
    for c in [TREATED] + COMPARATORS:
        pts = country_series(le, c)
        if not pts:
            continue
        series.append(
            {
                "id": c,
                "label": c,
                "color": palette.get(c, "#888888"),
                "treated": c == TREATED,
                "points": pts,
            }
        )

    if le_cub_change is not None and le_pool_mean is not None:
        subtitle = (
            f"Cuba LE 1991-2000: {le_cub_change:+.2f}y vs comparator-pool mean "
            f"{le_pool_mean:+.2f}y (Cuba minus pool {le_diff:+.2f}y); IMR reduction "
            f"Cuba {(imr_cub_pct or 0)*100:+.1f}% vs pool "
            f"{(imr_pool_mean or 0)*100:+.1f}% (diff {(imr_diff or 0)*100:+.1f}pp)."
        )
    else:
        subtitle = "Endpoint data missing for one or more required series; verdict inconclusive."

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Life expectancy at birth, Cuba vs Caribbean + post-Soviet pool, 1989-2001",
        "subtitle": subtitle,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Life expectancy at birth (years)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    "Comparator pool fixed ex-ante in YAML: Caribbean (JAM, DOM, HTI, NIC) "
                    "+ post-Soviet (UKR, MDA, ARM, GEO). Cuba (red) is the treated unit. "
                    "Verdict gates on Cuba minus pool-mean change in LE and IMR-reduction%."
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

    # ---------- Coefficients ----------
    coeff_rows = [
        {"spec": "primary1_le", "term": "le_cub_change_years", "estimate": le_cub_change},
        {"spec": "primary1_le", "term": "le_pool_mean_change_years", "estimate": le_pool_mean},
        {"spec": "primary1_le", "term": "le_diff_cub_minus_pool_years", "estimate": le_diff},
        {"spec": "primary2_imr", "term": "imr_cub_pct_reduction", "estimate": imr_cub_pct},
        {"spec": "primary2_imr", "term": "imr_pool_mean_pct_reduction", "estimate": imr_pool_mean},
        {"spec": "primary2_imr", "term": "imr_diff_cub_minus_pool", "estimate": imr_diff},
        {"spec": "informative_school", "term": "school_cub_change_pct_pts", "estimate": sch_cub_change},
        {"spec": "informative_school", "term": "school_pool_mean_change_pct_pts", "estimate": sch_pool_mean},
        {"spec": "informative_school", "term": "school_diff_cub_minus_pool", "estimate": sch_diff},
    ]
    pd.DataFrame(coeff_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
    def fmt(v, suffix="", decimals=2):
        if v is None:
            return "n/a"
        return f"{v:+.{decimals}f}{suffix}"

    def pct(v, decimals=1):
        if v is None:
            return "n/a"
        return f"{v*100:+.{decimals}f}%"

    pool_le_lines = "\n".join(
        f"| {c} | "
        f"{le_ep[c]['start_value'] if le_ep[c]['start_value'] is not None else 'n/a'} ({le_ep[c]['start_year']}) | "
        f"{le_ep[c]['end_value'] if le_ep[c]['end_value'] is not None else 'n/a'} ({le_ep[c]['end_year']}) | "
        f"{fmt(le_pool_changes.get(c), 'y')} |"
        for c in COMPARATORS
    )
    pool_imr_lines = "\n".join(
        f"| {c} | "
        f"{imr_ep[c]['start_value'] if imr_ep[c]['start_value'] is not None else 'n/a'} ({imr_ep[c]['start_year']}) | "
        f"{imr_ep[c]['end_value'] if imr_ep[c]['end_value'] is not None else 'n/a'} ({imr_ep[c]['end_year']}) | "
        f"{pct(imr_pool_pcts.get(c))} |"
        for c in COMPARATORS
    )

    card = [
        f"# Cuba Special Period 1991-2000 — health/education resilience",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- **PRIMARY-LE:** Cuba 1991-2000 life-expectancy change "
        f"**{fmt(le_cub_change, 'y')}**; comparator-pool mean "
        f"**{fmt(le_pool_mean, 'y')}**; Cuba minus pool **{fmt(le_diff, 'y')}** "
        f"(threshold >= 0). N comparators with both endpoints: {le_pool_n}/8.",
        f"- **PRIMARY-IMR:** Cuba IMR reduction "
        f"**{pct(imr_cub_pct)}** of 1991 baseline; pool mean **{pct(imr_pool_mean)}**; "
        f"Cuba minus pool **{pct(imr_diff)}** (threshold >= 0). "
        f"N comparators with both endpoints: {imr_pool_n}/8.",
        f"- **INFORMATIVE (school enrolment, GER):** Cuba "
        f"**{fmt(sch_cub_change, 'pp')}**; pool mean "
        f"**{fmt(sch_pool_mean, 'pp')}**; difference **{fmt(sch_diff, 'pp')}** "
        f"(coverage gaps; not a verdict gate).",
        "",
        "## Method",
        "",
        "Head-to-head 1991→2000 trajectory comparison, Cuba versus the mean of",
        "an ex-ante-fixed comparator pool of 8 economies — 4 Caribbean middle-",
        "income peers (JAM, DOM, HTI, NIC) and 4 post-Soviet transition states",
        "(UKR, MDA, ARM, GEO). Pool is hardcoded in the YAML so it cannot be",
        "selected on the outcome data. Endpoint values use a +/-1-year tolerance",
        "to fill small holes in WDI coverage; the actual year used per country",
        "is reported in `diagnostics.json:endpoints`. METHOD_VALID gate requires",
        "at least 4 of 8 comparators with both endpoints on each PRIMARY metric;",
        "otherwise the verdict is inconclusive (data gap), not refuted.",
        "",
        "## Data",
        "",
        "- world_bank_wdi:SP.DYN.LE00.IN (life expectancy at birth, years)",
        "- world_bank_wdi:SP.DYN.IMRT.IN (infant mortality, per 1000 live births)",
        "- world_bank_wdi:SE.PRM.ENRR (gross primary-school enrolment ratio)",
        "- world_bank_wdi:NY.GDP.PCAP.PP.KD (GDP per capita PPP — reference;",
        "  WDI does not publish for CUB in this window so the comparator pool",
        "  is fixed by region/transition status rather than by observed PPP-GDP)",
        "",
        "## Comparator detail — life expectancy",
        "",
        f"Cuba 1991: {le_ep[TREATED]['start_value']} (year {le_ep[TREATED]['start_year']}); "
        f"Cuba 2000: {le_ep[TREATED]['end_value']} (year {le_ep[TREATED]['end_year']}); "
        f"Cuba change: **{fmt(le_cub_change, 'y')}**.",
        "",
        "| Country | LE 1991 | LE 2000 | Change |",
        "|---|---|---|---|",
        pool_le_lines,
        "",
        "## Comparator detail — infant mortality",
        "",
        f"Cuba 1991: {imr_ep[TREATED]['start_value']} (year {imr_ep[TREATED]['start_year']}); "
        f"Cuba 2000: {imr_ep[TREATED]['end_value']} (year {imr_ep[TREATED]['end_year']}); "
        f"Cuba % reduction: **{pct(imr_cub_pct)}**.",
        "",
        "| Country | IMR 1991 | IMR 2000 | % reduction |",
        "|---|---|---|---|",
        pool_imr_lines,
        "",
        "## Steelman",
        "",
        "See `hypotheses/steelman/cuba_special_period_resilience.md` for the",
        "strongest opposing arguments (state-collapse confound in the post-",
        "Soviet pool; absence-of-shock confound in the Caribbean pool; ",
        "Cuban-official-data measurement caveat; education-quality vs",
        "GER mismatch).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
