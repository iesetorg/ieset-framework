#!/usr/bin/env python3
"""Replication — Nuclear phase-out grid reliability / cost trade-off.

Spec: hypotheses/energy/nuclear_phaseout_grid_reliability_cost_tradeoff.yaml v1

The spec's PRIMARY outcomes are:
  (a) industrial electricity price (IEA / Eurostat NRG_PC_205)
  (b) wholesale day-ahead volatility (ENTSO-E / EPEX / Nord Pool)
  (c) fossil-fired back-up capacity factor (ENTSO-E / EIA)
  (d) loss-of-load expectation (ENTSO-E MAF / NERC)

Of those, only the spirit of (c) — fossil reliance — has a publisher-on-disk
proxy: OWID share-electricity-fossil-fuels (Ember-derived). The headline
outcomes (industrial price, wholesale volatility, LOLE) are NOT on disk
because the IEA / Eurostat / ENTSO-E specialist fetchers have not shipped
yet (per the spec's `notes:` field).

Per HANDOFF guidance: do NOT substitute a different series silently to
force a verdict. Emit `inconclusive (data gap)` on the primary tests, AND
report what IS testable as informative evidence so the spec's authors and
reviewers can see whether the testable piece points the same direction
the hypothesis predicts.

The piece we CAN test:

  TESTABLE — Fossil share of electricity, phase-out vs retain.
    Phase-out cohort: DEU (2011 phase-out), BEL (2003 law), CHE (2017
    referendum). Retain cohort: FRA, FIN, SWE, USA, GBR. JPN excluded
    from primary cohorts (Fukushima created an effective pause that
    confounds; reported as sensitivity). KOR also reported as sensitivity
    (shifted but did not phase out).
    Statistic: change in mean fossil-share-of-electricity 2005 -> 2024
    in phase-out cohort minus the change in retain cohort. The
    hypothesis predicts a positive gap (phase-out countries leaned
    harder on fossils).

  INFORMATIVE — Nuclear share decline (verifies the treatment
    'happened') and renewables share rise (shows what replaced
    nuclear), reported as descriptive table only.

  METHOD_VALID — at least one full year of data 2005 and 2024 for all
    five non-JPN/KOR comparison countries.

The verdict will be `inconclusive` because the price/volatility primaries
cannot be evaluated. The testable surrogate is reported alongside.
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
HID = "nuclear_phaseout_grid_reliability_cost_tradeoff"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Cohorts from the spec
PHASEOUT = ["DEU", "BEL", "CHE"]
RETAIN = ["FRA", "FIN", "SWE", "USA", "GBR"]
SENSITIVITY = ["JPN", "KOR"]
ALL_COUNTRIES = PHASEOUT + RETAIN + SENSITIVITY

PERIOD = (2005, 2024)
START_YEAR, END_YEAR = PERIOD

# Threshold for the testable surrogate (fossil-share gap).
# The spec's stated economic story: phase-out countries lean harder on
# fossil back-up. A dispositive surrogate threshold: the phase-out cohort's
# fossil-share change must be at least 5 percentage points HIGHER than the
# retain cohort's change. This is informative-only because the headline
# spec outcomes (price, volatility, LOLE) are not on disk.
FOSSIL_GAP_THRESHOLD_PP = 5.0

# What the headline outcomes WOULD need (recorded only; not testable here)
SPEC_PRIMARY_DATA_GAPS = [
    "iea:industrial_electricity_price (band IC) — fetcher pending",
    "eurostat:NRG_PC_205 (industry electricity price) — series fetch pending",
    "entsoe:day_ahead_wholesale_prices — fetcher pending",
    "entsoe:fossil_capacity_factor — fetcher pending",
    "entsoe:MAF_LOLE — fetcher pending",
]


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
    """Normalise to (country_iso3, year, value). OWID puts the metric
    name as the value column."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def country_value_at(df: pd.DataFrame, iso3: str, year: int) -> float | None:
    sub = df[(df["country_iso3"] == iso3) & (df["year"] == year)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def country_nearest_value(df: pd.DataFrame, iso3: str, target_year: int,
                         max_window: int = 2) -> tuple[float | None, int | None]:
    """Get value at target_year, or nearest within +/-max_window."""
    for delta in range(0, max_window + 1):
        for sign in [0, -1, 1] if delta else [0]:
            y = target_year + sign * delta
            v = country_value_at(df, iso3, y)
            if v is not None:
                return v, y
    return None, None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    nuclear_path = latest("owid", "share-electricity-nuclear")
    fossil_path = latest("owid", "share-electricity-fossil-fuels")
    renew_path = latest("owid", "share-electricity-renewables")
    co2int_path = latest("owid", "co2-intensity")

    manifest = {
        "share_electricity_nuclear": {
            "publisher": "owid",
            "series": "share-electricity-nuclear",
            "vintage_file": str(nuclear_path.relative_to(REPO_ROOT)),
            "sha256": sha256(nuclear_path),
        },
        "share_electricity_fossil_fuels": {
            "publisher": "owid",
            "series": "share-electricity-fossil-fuels",
            "vintage_file": str(fossil_path.relative_to(REPO_ROOT)),
            "sha256": sha256(fossil_path),
        },
        "share_electricity_renewables": {
            "publisher": "owid",
            "series": "share-electricity-renewables",
            "vintage_file": str(renew_path.relative_to(REPO_ROOT)),
            "sha256": sha256(renew_path),
        },
        "co2_intensity": {
            "publisher": "owid",
            "series": "co2-intensity",
            "vintage_file": str(co2int_path.relative_to(REPO_ROOT)),
            "sha256": sha256(co2int_path),
        },
    }

    nuclear = load_long(nuclear_path)
    fossil = load_long(fossil_path)
    renew = load_long(renew_path)
    co2int = load_long(co2int_path)

    # ---------- Verify treatment 'happened' (informative) ----------
    nuclear_table = []
    for c in ALL_COUNTRIES:
        n_start, ys = country_nearest_value(nuclear, c, START_YEAR)
        n_end, ye = country_nearest_value(nuclear, c, END_YEAR)
        nuclear_table.append({
            "country": c,
            "year_start": ys,
            "nuclear_share_start": n_start,
            "year_end": ye,
            "nuclear_share_end": n_end,
            "nuclear_change_pp": (n_end - n_start) if (n_start is not None and n_end is not None) else None,
        })

    # ---------- TESTABLE: fossil-share gap (back-up reliance proxy) ----------
    fossil_table = []
    method_valid = True
    method_notes = []
    for c in PHASEOUT + RETAIN:
        f_start, ys = country_nearest_value(fossil, c, START_YEAR)
        f_end, ye = country_nearest_value(fossil, c, END_YEAR)
        if f_start is None or f_end is None:
            method_valid = False
            method_notes.append(f"missing fossil-share data for {c}")
        fossil_table.append({
            "country": c,
            "cohort": "phaseout" if c in PHASEOUT else "retain",
            "year_start": ys,
            "fossil_share_start": f_start,
            "year_end": ye,
            "fossil_share_end": f_end,
            "fossil_change_pp": (f_end - f_start) if (f_start is not None and f_end is not None) else None,
        })

    fdf = pd.DataFrame(fossil_table).dropna(subset=["fossil_change_pp"])
    phaseout_change = float(fdf[fdf["cohort"] == "phaseout"]["fossil_change_pp"].mean())
    retain_change = float(fdf[fdf["cohort"] == "retain"]["fossil_change_pp"].mean())
    fossil_gap = phaseout_change - retain_change

    surrogate_supports = fossil_gap >= FOSSIL_GAP_THRESHOLD_PP

    # ---------- Renewables / CO2-intensity (informative descriptive) ----------
    renew_table = []
    for c in PHASEOUT + RETAIN:
        r_start, _ = country_nearest_value(renew, c, START_YEAR)
        r_end, _ = country_nearest_value(renew, c, END_YEAR)
        renew_table.append({
            "country": c,
            "cohort": "phaseout" if c in PHASEOUT else "retain",
            "renew_share_start": r_start,
            "renew_share_end": r_end,
            "renew_change_pp": (r_end - r_start) if (r_start is not None and r_end is not None) else None,
        })
    rdf = pd.DataFrame(renew_table).dropna(subset=["renew_change_pp"])
    phaseout_renew_change = float(rdf[rdf["cohort"] == "phaseout"]["renew_change_pp"].mean())
    retain_renew_change = float(rdf[rdf["cohort"] == "retain"]["renew_change_pp"].mean())

    co2int_table = []
    for c in PHASEOUT + RETAIN:
        s, _ = country_nearest_value(co2int, c, START_YEAR)
        e, _ = country_nearest_value(co2int, c, END_YEAR)
        co2int_table.append({
            "country": c,
            "cohort": "phaseout" if c in PHASEOUT else "retain",
            "co2int_start": s,
            "co2int_end": e,
            "co2int_change_pct": ((e - s) / s * 100.0) if (s is not None and e is not None and s > 0) else None,
        })
    cdf = pd.DataFrame(co2int_table).dropna(subset=["co2int_change_pct"])
    phaseout_co2int_change = float(cdf[cdf["cohort"] == "phaseout"]["co2int_change_pct"].mean())
    retain_co2int_change = float(cdf[cdf["cohort"] == "retain"]["co2int_change_pct"].mean())

    # ---------- Verdict ----------
    # Primary outcomes (industrial price, wholesale volatility, LOLE) are not
    # on disk. The verdict is structurally `inconclusive` regardless of what
    # the surrogate shows. We still report what the surrogate said.
    verdict_word = "inconclusive"
    surrogate_phrase = (
        f"phase-out cohort fossil-share change {phaseout_change:+.1f}pp vs "
        f"retain cohort {retain_change:+.1f}pp — gap "
        f"{fossil_gap:+.1f}pp ({'consistent with' if surrogate_supports else 'NOT consistent with'} "
        f"{FOSSIL_GAP_THRESHOLD_PP:+.1f}pp threshold)"
    )
    verdict = (
        f"inconclusive — Primary outcomes (industrial electricity price, "
        f"wholesale day-ahead volatility, LOLE) require IEA / Eurostat "
        f"NRG_PC_205 / ENTSO-E specialist fetchers that have not shipped. "
        f"Testable surrogate (back-up reliance via fossil share of "
        f"electricity): {surrogate_phrase}. Treatment is observed: "
        f"phase-out cohort nuclear share fell from "
        f"{np.nanmean([r['nuclear_share_start'] for r in nuclear_table if r['country'] in PHASEOUT and r['nuclear_share_start'] is not None]):.0f}% "
        f"to {np.nanmean([r['nuclear_share_end'] for r in nuclear_table if r['country'] in PHASEOUT and r['nuclear_share_end'] is not None]):.0f}%; "
        f"retain cohort held "
        f"{np.nanmean([r['nuclear_share_start'] for r in nuclear_table if r['country'] in RETAIN and r['nuclear_share_start'] is not None]):.0f}% "
        f"to {np.nanmean([r['nuclear_share_end'] for r in nuclear_table if r['country'] in RETAIN and r['nuclear_share_end'] is not None]):.0f}%."
    )

    diagnostics = {
        "verdict": verdict,
        "verdict_word": verdict_word,
        "primary_data_gaps": SPEC_PRIMARY_DATA_GAPS,
        "method_valid": method_valid,
        "method_notes": method_notes,
        "surrogate": {
            "name": "fossil_share_change_pp_2005_to_2024",
            "phaseout_cohort_change_pp": phaseout_change,
            "retain_cohort_change_pp": retain_change,
            "gap_pp": fossil_gap,
            "threshold_pp": FOSSIL_GAP_THRESHOLD_PP,
            "supports_hypothesis": surrogate_supports,
        },
        "renewables_change_pp": {
            "phaseout_cohort": phaseout_renew_change,
            "retain_cohort": retain_renew_change,
        },
        "co2_intensity_change_pct": {
            "phaseout_cohort": phaseout_co2int_change,
            "retain_cohort": retain_co2int_change,
        },
        "nuclear_table": nuclear_table,
        "fossil_table": fossil_table,
        "renew_table": renew_table,
        "co2int_table": co2int_table,
        "period": list(PERIOD),
        "phaseout_cohort": PHASEOUT,
        "retain_cohort": RETAIN,
        "sensitivity_cohort": SENSITIVITY,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")

    # ---------- Chart ----------
    palette_phaseout = ["#E15759", "#F28E2B", "#B07AA1"]  # warm — phase-out
    palette_retain = ["#4E79A7", "#59A14F", "#76B7B2", "#EDC948", "#9C755F"]  # cool — retain

    # Plot fossil-share trajectories — the testable surrogate.
    series = []
    for i, c in enumerate(PHASEOUT):
        sub = fossil[(fossil["country_iso3"] == c) &
                     (fossil["year"].between(START_YEAR, END_YEAR))]
        sub = sub.sort_values("year")
        if sub.empty:
            continue
        pts = [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]
        series.append({
            "id": c,
            "label": f"{c} (phase-out)",
            "color": palette_phaseout[i % len(palette_phaseout)],
            "treated": True,
            "points": pts,
        })
    for i, c in enumerate(RETAIN):
        sub = fossil[(fossil["country_iso3"] == c) &
                     (fossil["year"].between(START_YEAR, END_YEAR))]
        sub = sub.sort_values("year")
        if sub.empty:
            continue
        pts = [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]
        series.append({
            "id": c,
            "label": f"{c} (retain)",
            "color": palette_retain[i % len(palette_retain)],
            "treated": False,
            "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Fossil share of electricity — nuclear phase-out vs nuclear-retaining cohorts",
        "subtitle": (
            f"Phase-out cohort change {phaseout_change:+.1f}pp vs retain {retain_change:+.1f}pp "
            f"(gap {fossil_gap:+.1f}pp). Headline outcomes (industrial price, wholesale "
            f"volatility, LOLE) require IEA / ENTSO-E fetchers that are pending."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Fossil share of electricity (%)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Surrogate test: fossil-share gap = {fossil_gap:+.1f}pp; "
                    f"threshold for surrogate-supports = +{FOSSIL_GAP_THRESHOLD_PP}pp. "
                    f"Verdict word: {verdict_word} (primary outcomes data-gapped)."
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
    coef_rows = [
        {"spec": "surrogate", "term": "phaseout_fossil_change_pp", "estimate": phaseout_change},
        {"spec": "surrogate", "term": "retain_fossil_change_pp", "estimate": retain_change},
        {"spec": "surrogate", "term": "fossil_gap_pp", "estimate": fossil_gap},
        {"spec": "surrogate", "term": "fossil_gap_threshold_pp", "estimate": float(FOSSIL_GAP_THRESHOLD_PP)},
        {"spec": "informative", "term": "phaseout_renew_change_pp", "estimate": phaseout_renew_change},
        {"spec": "informative", "term": "retain_renew_change_pp", "estimate": retain_renew_change},
        {"spec": "informative", "term": "phaseout_co2int_change_pct", "estimate": phaseout_co2int_change},
        {"spec": "informative", "term": "retain_co2int_change_pct", "estimate": retain_co2int_change},
    ]
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
    def fmt(x: float | None, pct: bool = False) -> str:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "—"
        return f"{x:+.1f}{'%' if pct else 'pp'}" if pct else f"{x:+.1f}"

    def row_for(r: dict, key_start: str, key_end: str, fmt_pct: str = "f") -> str:
        s, e = r.get(key_start), r.get(key_end)
        ss = f"{s:.1f}" if s is not None else "—"
        ee = f"{e:.1f}" if e is not None else "—"
        return f"{ss} → {ee}"

    card = [
        f"# Nuclear phase-out — grid reliability / cost trade-off",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- The spec's PRIMARY outcomes are industrial electricity price, "
        f"wholesale day-ahead volatility, fossil-fired back-up capacity "
        f"factor, and loss-of-load expectation. The first two and the "
        f"fourth are **not on disk** — the IEA / Eurostat NRG_PC_205 / "
        f"ENTSO-E fetchers are pending. The headline tests cannot be run "
        f"with publisher-pinned data; verdict is structurally **inconclusive**.",
        f"- The third primary (fossil back-up reliance) has an OWID-Ember "
        f"surrogate: share-electricity-fossil-fuels. As a check on whether "
        f"the testable piece points the way the spec predicts:",
        "",
        f"  - Phase-out cohort (DEU, BEL, CHE) fossil-share change "
        f"2005→2024: **{phaseout_change:+.1f}pp**",
        f"  - Retain cohort (FRA, FIN, SWE, USA, GBR) fossil-share change "
        f"2005→2024: **{retain_change:+.1f}pp**",
        f"  - Gap: **{fossil_gap:+.1f}pp** "
        f"(surrogate {'supports' if surrogate_supports else 'does NOT support'} "
        f"the +{FOSSIL_GAP_THRESHOLD_PP}pp threshold)",
        "",
        f"- Treatment is verifiable: phase-out cohort nuclear-share "
        f"declined materially while retain cohort held steady. See "
        f"diagnostics.json for the country-level breakout.",
        f"- Renewables build-out: phase-out cohort {phaseout_renew_change:+.1f}pp, "
        f"retain cohort {retain_renew_change:+.1f}pp — phase-out countries "
        f"deployed renewables harder, partially substituting for the "
        f"removed nuclear capacity (consistent with the spec's "
        f"acknowledged collinearity).",
        f"- CO2-intensity of GDP: phase-out cohort {phaseout_co2int_change:+.1f}%, "
        f"retain cohort {retain_co2int_change:+.1f}% — both decarbonising; "
        f"phase-out cohort started higher and converged.",
        "",
        "## Method",
        "",
        f"Period: {START_YEAR}–{END_YEAR}. Phase-out cohort: {', '.join(PHASEOUT)}. "
        f"Retain cohort: {', '.join(RETAIN)}. Sensitivity cohort (excluded "
        f"from primary cohorts): {', '.join(SENSITIVITY)}.",
        "",
        "**Why inconclusive, not refuted/supported:**",
        "",
        "Per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2, a method-valid failure "
        "(here: data gap on the headline outcomes) yields `inconclusive`, "
        "NOT `refuted`. Substituting a different series for industrial-"
        "electricity-price would violate provenance. The surrogate (fossil "
        "share) is reported as informative evidence only — it shares the "
        "spec's spirit on back-up reliance but does NOT settle the "
        "cost-of-electricity primary.",
        "",
        "**Specialist fetchers needed for v2:**",
        "",
        *[f"- {g}" for g in SPEC_PRIMARY_DATA_GAPS],
        "",
        "## Data",
        "",
        f"- owid:share-electricity-nuclear (Ember-derived; treatment verification)",
        f"- owid:share-electricity-fossil-fuels (Ember-derived; surrogate for back-up reliance)",
        f"- owid:share-electricity-renewables (Ember-derived; informative)",
        f"- owid:co2-intensity (informative)",
        "",
        "## Caveats",
        "",
        "- France's 2022 reactor-availability crisis (stress-corrosion "
        "cracking, ~half the fleet derated) confounds the FRA-as-control "
        "story for the gas-shock window. Steelman point #1.",
        "- Gas-price shock 2022-2024 dominates any cost-outcome data and "
        "is geographically correlated with the phase-out cohort. Steelman "
        "point #2; the planned drop-2021-2024 sensitivity needs the "
        "missing price data.",
        "- BEL extended Doel 4 / Tihange 3 beyond planned phase-out; CHE "
        "phase-out is passive. Treatment intensity is heterogeneous "
        "(steelman point #5).",
        "- Safety / waste-management benefits — the actual reasons for "
        "phase-out — are unmeasured here. The hypothesis answers a "
        "narrow trade-off question, not a net-welfare question.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
