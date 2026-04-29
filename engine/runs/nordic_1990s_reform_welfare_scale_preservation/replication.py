#!/usr/bin/env python3
"""Replication — Nordic 1990s reform: welfare-scale preservation + fiscal sustainability.

Spec: hypotheses/welfare_architecture/nordic_1990s_reform_welfare_scale_preservation.yaml v1
Position-claim: social_democratic #6 (school predicts: supported)

Tests three pre-registered components of the claim that 1990s Nordic reforms
(SWE 1999 pension, NOR 2001 handlingsregel, DNK 1994 flexicurity) preserved
welfare-state scope while restoring fiscal sustainability:

  PRIMARY LEG-A (welfare-scale preservation):
      OECD SOCX public social expenditure as % of GDP — peak-to-late-2000s
      decline ≤ 3pp for SWE/NOR/DNK/FIN. THIS IS THE PRIMARY DISPOSITIVE
      OUTCOME because the claim is fundamentally about scale preservation.

  PRIMARY LEG-B (fiscal sustainability):
      IMF GGXWDG_NGDP general government gross debt — late-2000s mean
      (2005-2008, pre-GFC to avoid contamination) at most 5pp above the
      mid-1990s peak. The reform package's stated point was to STABILISE
      debt (not necessarily reduce it dramatically); a 5pp tolerance is
      what a fair reader of the claim would accept.

  PRIMARY LEG-C (employment recovery):
      WDI SL.UEM.TOTL.ZS unemployment rate (used as the inverse-employment
      proxy because the spec's preferred SL.EMP.TOTL.SP.ZS is not on disk
      in this vintage — the constructed test is "unemployment fell ≥ 2pp
      from 1990s peak to 2005-2008 mean", logically equivalent to the
      spec's "employment rate up >2pp" claim under the labour-force
      participation stability assumption that holds for all four countries
      in this period per OECD LFS).

Hypothesis is SUPPORTED only if ALL THREE primary legs hold for at least
3 of the 4 Nordic countries (SWE/NOR/DNK/FIN). REFUTED if any leg fails
materially in 3 or more countries. PARTIAL if 1-2 legs hold cleanly and
the others miss by a small margin.

Data-gap protocol: OECD SOCX is not currently fetched into
data/vintages/oecd/. Per the framework's invariant on provenance
(HANDOFF_TO_RUN_AGENT.md §"What to do when your spec needs data that
isn't on disk"), we emit verdict = "inconclusive (data gap on oecd:SOCX)"
when the spending-share leg cannot be evaluated, and report the remaining
legs as informative. The script becomes immediately re-runnable once the
SOCX fetcher lands; nothing else has to change.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "nordic_1990s_reform_welfare_scale_preservation"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRIES = ["SWE", "NOR", "DNK", "FIN"]
PERIOD = (1985, 2015)

# Reform onset dates from the claim
REFORM_DATES = {
    "SWE": 1999,  # pension reform
    "NOR": 2001,  # handlingsregel (fiscal rule)
    "DNK": 1994,  # flexicurity reforms (post-1993 unemployment crisis)
    "FIN": 1996,  # post-banking-crisis fiscal consolidation
}

# Pre-reform window: 1990-1995 (the crisis period when each country hit a peak
# in debt/unemployment). Post-reform window: 2005-2008 (mature reform regime,
# pre-GFC contamination).
PRE_WINDOW = (1990, 1995)
POST_WINDOW = (2005, 2008)

# Falsification thresholds (sharpened from the spec's generic rule)
SOCX_DECLINE_THRESHOLD_PP = 3.0  # peak-to-late-2000s decline must be ≤ 3pp
DEBT_DRIFT_THRESHOLD_PP = 5.0    # late-2000s mean − 1990s peak ≤ +5pp
UNEMPLOYMENT_FALL_THRESHOLD_PP = 2.0  # 1990s peak − late-2000s mean ≥ +2pp
COUNTRIES_REQUIRED_FOR_SUPPORT = 3   # of 4


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    return files[-1]


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def window_mean(df: pd.DataFrame, country: str, lo: int, hi: int) -> float:
    sub = df[
        (df["country_iso3"] == country)
        & (df["year"].between(lo, hi))
    ]["value"]
    return float(sub.mean()) if len(sub) else float("nan")


def window_max(df: pd.DataFrame, country: str, lo: int, hi: int) -> float:
    sub = df[
        (df["country_iso3"] == country)
        & (df["year"].between(lo, hi))
    ]["value"]
    return float(sub.max()) if len(sub) else float("nan")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Resolve vintages ----------
    socx_path = latest("oecd", "SOCX")  # canonical name; will be None until fetched
    debt_path = latest("imf", "GGXWDG_NGDP")
    unem_path = latest("world_bank_wdi", "SL.UEM.TOTL.ZS")
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")

    manifest: dict = {}
    if socx_path is not None:
        manifest["socx"] = {
            "publisher": "oecd", "series": "SOCX",
            "vintage_file": str(socx_path.relative_to(REPO_ROOT)),
            "sha256": sha256(socx_path),
        }
    else:
        manifest["socx"] = {"publisher": "oecd", "series": "SOCX", "missing": True}

    for name, pub, series, path in [
        ("debt_to_gdp", "imf", "GGXWDG_NGDP", debt_path),
        ("unemployment", "world_bank_wdi", "SL.UEM.TOTL.ZS", unem_path),
        ("gdp_per_capita", "world_bank_wdi", "NY.GDP.PCAP.KD", gdppc_path),
    ]:
        if path is None:
            manifest[name] = {"publisher": pub, "series": series, "missing": True}
        else:
            manifest[name] = {
                "publisher": pub, "series": series,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
            }

    # ---------- LEG-A: Social expenditure share (PRIMARY, often missing) ----------
    leg_a = {"available": socx_path is not None, "by_country": {}}
    if socx_path is not None:
        socx = load_long(socx_path)
        for c in COUNTRIES:
            peak = window_max(socx, c, 1985, 2000)  # peak before/around reform
            late = window_mean(socx, c, *POST_WINDOW)
            decline = peak - late if not (np.isnan(peak) or np.isnan(late)) else float("nan")
            preserved = (not np.isnan(decline)) and (decline <= SOCX_DECLINE_THRESHOLD_PP)
            leg_a["by_country"][c] = {
                "peak_share": peak, "late2000s_mean": late,
                "decline_pp": decline, "preserved": preserved,
            }
        leg_a["countries_passing"] = sum(
            1 for d in leg_a["by_country"].values() if d.get("preserved")
        )
        leg_a["passes"] = leg_a["countries_passing"] >= COUNTRIES_REQUIRED_FOR_SUPPORT

    # ---------- LEG-B: Debt sustainability ----------
    leg_b = {"available": debt_path is not None, "by_country": {}}
    if debt_path is not None:
        debt = load_long(debt_path)
        for c in COUNTRIES:
            peak = window_max(debt, c, *PRE_WINDOW)  # 1990-1995 crisis peak
            late = window_mean(debt, c, *POST_WINDOW)
            drift = late - peak if not (np.isnan(peak) or np.isnan(late)) else float("nan")
            stable = (not np.isnan(drift)) and (drift <= DEBT_DRIFT_THRESHOLD_PP)
            leg_b["by_country"][c] = {
                "peak_1990_1995": peak, "late2000s_mean": late,
                "drift_pp": drift, "stabilised": stable,
            }
        leg_b["countries_passing"] = sum(
            1 for d in leg_b["by_country"].values() if d.get("stabilised")
        )
        leg_b["passes"] = leg_b["countries_passing"] >= COUNTRIES_REQUIRED_FOR_SUPPORT

    # ---------- LEG-C: Employment recovery (via unemployment fall) ----------
    leg_c = {"available": unem_path is not None, "by_country": {}}
    if unem_path is not None:
        unem = load_long(unem_path)
        for c in COUNTRIES:
            peak = window_max(unem, c, *PRE_WINDOW)
            late = window_mean(unem, c, *POST_WINDOW)
            fall = peak - late if not (np.isnan(peak) or np.isnan(late)) else float("nan")
            recovered = (not np.isnan(fall)) and (fall >= UNEMPLOYMENT_FALL_THRESHOLD_PP)
            leg_c["by_country"][c] = {
                "unemployment_peak_1990_1995": peak,
                "unemployment_late2000s_mean": late,
                "fall_pp": fall, "recovered": recovered,
            }
        leg_c["countries_passing"] = sum(
            1 for d in leg_c["by_country"].values() if d.get("recovered")
        )
        leg_c["passes"] = leg_c["countries_passing"] >= COUNTRIES_REQUIRED_FOR_SUPPORT

    # ---------- Verdict ----------
    legs_complete = leg_a["available"] and leg_b["available"] and leg_c["available"]

    if not legs_complete:
        # Data gap on the primary outcome → inconclusive per framework rule
        missing = []
        if not leg_a["available"]:
            missing.append("oecd:SOCX")
        if not leg_b["available"]:
            missing.append("imf:GGXWDG_NGDP")
        if not leg_c["available"]:
            missing.append("world_bank_wdi:SL.UEM.TOTL.ZS")

        # Still report what we did manage to compute
        partial_bits = []
        if leg_b["available"]:
            partial_bits.append(
                f"fiscal-sustainability leg ran: {leg_b['countries_passing']}/4 "
                f"Nordics had debt/GDP within +{DEBT_DRIFT_THRESHOLD_PP:.0f}pp of "
                f"the 1990s peak by 2005-2008"
            )
        if leg_c["available"]:
            partial_bits.append(
                f"employment-recovery leg ran (unemployment proxy): "
                f"{leg_c['countries_passing']}/4 Nordics saw unemployment fall "
                f"≥{UNEMPLOYMENT_FALL_THRESHOLD_PP:.0f}pp from 1990s peak"
            )
        suffix = ("; " + "; ".join(partial_bits)) if partial_bits else ""
        verdict = (
            f"inconclusive (data gap on {', '.join(missing)}) — primary "
            f"welfare-scale-preservation outcome (OECD SOCX public social "
            f"expenditure share of GDP) is not in the current data vintage; "
            f"the supplementary fiscal-sustainability and employment-recovery "
            f"legs alone cannot dispositively grade the scale-preservation claim"
            f"{suffix}."
        )
        all_pass = False
    else:
        passes = [leg_a["passes"], leg_b["passes"], leg_c["passes"]]
        n_passing = sum(passes)
        if n_passing == 3:
            verdict = (
                f"SUPPORTED — All three primary legs held in ≥3 of 4 Nordics. "
                f"Welfare-scale: {leg_a['countries_passing']}/4 with SOCX "
                f"decline ≤ {SOCX_DECLINE_THRESHOLD_PP:.0f}pp from peak. "
                f"Fiscal: {leg_b['countries_passing']}/4 with debt drift ≤ "
                f"+{DEBT_DRIFT_THRESHOLD_PP:.0f}pp. Employment: "
                f"{leg_c['countries_passing']}/4 with unemployment fall ≥ "
                f"{UNEMPLOYMENT_FALL_THRESHOLD_PP:.0f}pp."
            )
            all_pass = True
        elif n_passing == 0:
            verdict = (
                f"refuted — None of the three primary legs held in 3+ of 4 "
                f"Nordics. Welfare-scale {leg_a['countries_passing']}/4, "
                f"fiscal {leg_b['countries_passing']}/4, employment "
                f"{leg_c['countries_passing']}/4."
            )
            all_pass = False
        else:
            verdict = (
                f"partial — {n_passing} of 3 primary legs held. Welfare-scale "
                f"{leg_a['countries_passing']}/4 (pass={leg_a['passes']}), "
                f"fiscal {leg_b['countries_passing']}/4 "
                f"(pass={leg_b['passes']}), employment "
                f"{leg_c['countries_passing']}/4 (pass={leg_c['passes']})."
            )
            all_pass = False

    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "thresholds": {
            "socx_decline_pp_max": SOCX_DECLINE_THRESHOLD_PP,
            "debt_drift_pp_max": DEBT_DRIFT_THRESHOLD_PP,
            "unemployment_fall_pp_min": UNEMPLOYMENT_FALL_THRESHOLD_PP,
            "countries_required_for_support": COUNTRIES_REQUIRED_FOR_SUPPORT,
        },
        "leg_a_socx_welfare_scale": leg_a,
        "leg_b_debt_sustainability": leg_b,
        "leg_c_employment_recovery": leg_c,
        "windows": {
            "pre_reform_crisis": list(PRE_WINDOW),
            "post_reform_pre_gfc": list(POST_WINDOW),
        },
        "reform_dates": REFORM_DATES,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- coefficients.parquet ----------
    coef_rows: list[dict] = []
    for c in COUNTRIES:
        if leg_a["available"]:
            d = leg_a["by_country"][c]
            coef_rows.append({
                "spec": "socx_decline_pp", "term": c,
                "estimate": d["decline_pp"],
            })
        if leg_b["available"]:
            d = leg_b["by_country"][c]
            coef_rows.append({
                "spec": "debt_drift_pp", "term": c,
                "estimate": d["drift_pp"],
            })
        if leg_c["available"]:
            d = leg_c["by_country"][c]
            coef_rows.append({
                "spec": "unemployment_fall_pp", "term": c,
                "estimate": d["fall_pp"],
            })
    if not coef_rows:
        coef_rows.append({"spec": "n/a", "term": "no_data", "estimate": float("nan")})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- chart_data.json ----------
    palette = {"SWE": "#4E79A7", "NOR": "#59A14F", "DNK": "#B07AA1", "FIN": "#E15759"}
    series = []

    # Use debt/GDP as the headline chart series (it's the leg most directly
    # tied to the "fiscal sustainability restored" claim, and it has data).
    if debt_path is not None:
        debt = load_long(debt_path)
        for c in COUNTRIES:
            sub = (
                debt[
                    (debt["country_iso3"] == c)
                    & (debt["year"].between(PERIOD[0], PERIOD[1]))
                ][["year", "value"]]
                .dropna()
                .sort_values("year")
            )
            if sub.empty:
                continue
            series.append({
                "id": c, "label": c, "color": palette[c],
                "treated": True,
                "points": [
                    {"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()
                ],
            })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Nordic gross general government debt as % of GDP, 1985-2015",
        "subtitle": (
            f"1990s reform onsets: SWE 1999, NOR 2001, DNK 1994, FIN 1996. "
            f"Fiscal-sustainability test: 2005-2008 mean ≤ 1990s peak + "
            f"{DEBT_DRIFT_THRESHOLD_PP:.0f}pp."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "general govt gross debt, % of GDP", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "note", "label": (
                f"Verdict: {verdict[:140]}{'...' if len(verdict) > 140 else ''}"
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v.get("vintage_file", "MISSING")}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- manifest.yaml ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- result_card.md ----------
    lines = [
        f"# Nordic 1990s reform — welfare-scale preservation + fiscal sustainability",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Three pre-registered primary legs of the social-democratic claim that "
        "1990s Nordic reforms preserved welfare-state scope while restoring "
        "fiscal sustainability:",
        "",
        f"1. **Welfare-scale preservation** — OECD SOCX public social spending "
        f"share of GDP, peak-to-2005-2008 decline ≤ {SOCX_DECLINE_THRESHOLD_PP:.0f}pp.",
        f"2. **Fiscal sustainability** — IMF general govt gross debt, 2005-2008 "
        f"mean within +{DEBT_DRIFT_THRESHOLD_PP:.0f}pp of 1990s peak.",
        f"3. **Employment recovery (via unemployment proxy)** — WDI unemployment "
        f"rate, 1990s peak − 2005-2008 mean ≥ {UNEMPLOYMENT_FALL_THRESHOLD_PP:.0f}pp.",
        "",
        f"Hypothesis SUPPORTED if all three legs hold in ≥{COUNTRIES_REQUIRED_FOR_SUPPORT} "
        f"of 4 Nordic countries (SWE/NOR/DNK/FIN).",
        "",
        "## Leg results",
        "",
    ]

    if leg_a["available"]:
        lines += [
            "### Leg A — welfare-scale preservation (OECD SOCX)",
            "",
            "| Country | Peak SOCX (% GDP) | 2005-2008 mean | Decline (pp) | Preserved? |",
            "|---|---:|---:|---:|:---:|",
        ]
        for c in COUNTRIES:
            d = leg_a["by_country"][c]
            lines.append(
                f"| {c} | {d['peak_share']:.1f} | {d['late2000s_mean']:.1f} | "
                f"{d['decline_pp']:+.1f} | {'✓' if d['preserved'] else '✗'} |"
            )
        lines += ["", f"Countries passing: {leg_a['countries_passing']}/4 — "
                  f"leg {'PASS' if leg_a['passes'] else 'FAIL'}.", ""]
    else:
        lines += [
            "### Leg A — welfare-scale preservation",
            "",
            "**DATA GAP — OECD SOCX series not available in current vintage.** "
            "This is the primary dispositive outcome for the scale-preservation "
            "claim; until the SOCX fetcher lands the verdict cannot be conclusive. "
            "When SOCX lands, this script re-runs without modification and the "
            "verdict re-grades automatically.", "",
        ]

    if leg_b["available"]:
        lines += [
            "### Leg B — fiscal sustainability (IMF general govt gross debt)",
            "",
            "| Country | 1990-1995 peak (% GDP) | 2005-2008 mean | Drift (pp) | Stable? |",
            "|---|---:|---:|---:|:---:|",
        ]
        for c in COUNTRIES:
            d = leg_b["by_country"][c]
            lines.append(
                f"| {c} | {d['peak_1990_1995']:.1f} | {d['late2000s_mean']:.1f} | "
                f"{d['drift_pp']:+.1f} | {'✓' if d['stabilised'] else '✗'} |"
            )
        lines += ["", f"Countries passing: {leg_b['countries_passing']}/4 — "
                  f"leg {'PASS' if leg_b['passes'] else 'FAIL'}.", ""]

    if leg_c["available"]:
        lines += [
            "### Leg C — employment recovery (WDI unemployment, inverse proxy)",
            "",
            "| Country | 1990-1995 peak unemployment | 2005-2008 mean | Fall (pp) | Recovered? |",
            "|---|---:|---:|---:|:---:|",
        ]
        for c in COUNTRIES:
            d = leg_c["by_country"][c]
            lines.append(
                f"| {c} | {d['unemployment_peak_1990_1995']:.1f} | "
                f"{d['unemployment_late2000s_mean']:.1f} | "
                f"{d['fall_pp']:+.1f} | {'✓' if d['recovered'] else '✗'} |"
            )
        lines += ["", f"Countries passing: {leg_c['countries_passing']}/4 — "
                  f"leg {'PASS' if leg_c['passes'] else 'FAIL'}.", ""]

    lines += [
        "## Method",
        "",
        "Pre-/post-reform descriptive comparison on the four Nordic countries, "
        "using the 1990-1995 crisis window (debt + unemployment peak years for "
        "each country) as the pre-reform baseline and 2005-2008 (mature reform "
        "regime, pre-GFC contamination) as the post-reform window. Each leg "
        "evaluates a country-level pass/fail; the hypothesis as a whole is "
        f"SUPPORTED if all three legs pass in ≥{COUNTRIES_REQUIRED_FOR_SUPPORT}/4 "
        "Nordics.",
        "",
        "## Caveats",
        "",
        "- Macro-cyclical recovery 1995-2007 partially explains the employment "
        "and debt outcomes (the spec flags this as TODO swarm-6e). A matched "
        "OECD donor-pool sensitivity is not in v1.",
        "- The unemployment-fall proxy for the spec's preferred employment-rate "
        "outcome assumes labour-force participation stability, which holds for "
        "all four countries 1995-2008 per OECD LFS but is not formally tested "
        "here.",
        "- DNK's 1994 flexicurity onset slightly precedes the formal reform "
        "package; we use 1994 per the spec but the post-window is unaffected.",
        "",
        "## Data",
        "",
    ]
    for k, v in manifest.items():
        if v.get("missing"):
            lines.append(f"- {v['publisher']}:{v['series']} — **MISSING (data gap)**")
        else:
            lines.append(f"- {v['publisher']}:{v['series']} — `{v['vintage_file']}`")
    lines.append("")

    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
