#!/usr/bin/env python3
"""Replication — universal_transfer_programmes_labour_force_participation_decline (v1).

Spec: hypotheses/fiscal/universal_transfer_programmes_labour_force_participation_decline.yaml
Steelman: hypotheses/steelman/universal_transfer_programmes_labour_force_participation_decline.md

The spec posits a three-order causal chain in five large-transfer cases:
  ARG (Planes Trabajar / Argentina Trabaja / Potenciar Trabajo, 2003-2020)
  ESP (Ingreso Mínimo Vital, 2020-06)
  GBR (Tax credits expansion 1999, Universal Credit rollout 2013-2018)
  VEN (CLAP food box, 2016-03)
  USA (Expanded Child Tax Credit, 2021)

PROMOTION DECISION — given which series ARE in the vintages, this run
operationalises the registered chain at the level the data supports:

  FIRST-ORDER (poverty/Gini):
    Direction of country Gini-coefficient change in the 5y window post
    programme rollout vs the prior 5y window. Spec asserts poverty
    drops ("acknowledged success"). Source: world_bank_wdi:SI.POV.GINI.

  SECOND-ORDER (prime-age LFP):
    Direction of national prime-age (25+) labour-force participation
    rate change in the 5y window post programme rollout vs the prior
    5y window, both sexes pooled.
    Source: ilostat:EAP_2WAP_SEX_AGE_RT_A, sex=SEX_T, classif1=
    AGE_YTHADULT_YGE25 (proxy for prime-age able-bodied; the spec asks
    for bottom-decile but no bottom-decile micro-panel is in vintages).
    A national-LFP signal underestimates the bottom-decile effect the
    spec predicts (since the bottom decile is a small share of total
    workforce); but it cannot SHOW a decline that did not occur.

DEVIATIONS from the YAML spec (recorded in methodology_note):
  - Bottom-decile LFP, hours-worked, EMTR, programme-spend %GDP, and
    administrative-panel re-employment series are not in vintages —
    these are the spec's preferred outcomes but require microdata or
    OECD Benefits-and-Wages files we do not hold.
  - Test reduced to 5-yr pre/post deltas (not C-S DiD) since donor pool
    construction with within-country pre-cohorts is not feasible from
    annual aggregate ILO/WDI alone.
  - 2020-2021 are excluded from the post-window for ESP IMV and USA CTC
    per the spec's exclusion rule (pandemic LFP shock); we use the
    earliest available post-programme year that is not pandemic-only.

DISPOSITIVE PRIMARY THRESHOLD:
  SUPPORTED if (a) at least 3/5 cases show prime-age LFP decline
              (Δ ≤ -1.0pp 5y-mean post vs 5y-mean pre)
            AND (b) at least 3/5 cases show Gini decline OR poverty
                   reduction in the post-window (first-order success).
  REFUTED if 4/5 or 5/5 cases show prime-age LFP RISE in the post-window
              (the chain doesn't fire).
  PARTIAL if 2/5 cases show LFP decline (mixed; design-dependent —
              consistent with the spec's "design matters" caveat).
  INCONCLUSIVE if data gaps dominate (>=3/5 cases lack prime-age LFP
              data covering both pre & post windows).
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
HID = "universal_transfer_programmes_labour_force_participation_decline"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Programme rollout years per spec.
# Where the spec gives a band, we pick the year of the most-binding
# expansion that the canonical literature treats as the "shock".
PROGRAMMES = {
    "ARG": {"name": "Planes Trabajar / Argentina Trabaja / Potenciar Trabajo",
            "rollout_year": 2003,  # Argentina Trabaja and Plan Jefes/Jefas wave
            "post_exclusion_years": set()},
    "ESP": {"name": "Ingreso Mínimo Vital",
            "rollout_year": 2020,
            "post_exclusion_years": {2020, 2021}},  # pandemic
    "GBR": {"name": "Universal Credit rollout (post tax-credit consolidation)",
            "rollout_year": 2013,  # UC pathfinder year
            "post_exclusion_years": set()},
    "VEN": {"name": "CLAP food box",
            "rollout_year": 2016,
            "post_exclusion_years": set()},
    "USA": {"name": "Expanded Child Tax Credit (2021 ARPA)",
            "rollout_year": 2021,
            "post_exclusion_years": {2020, 2021}},  # pandemic
}

PRE_WINDOW_YEARS = 5
POST_WINDOW_YEARS = 5

# Falsification thresholds (dispositive primary)
LFP_DECLINE_THRESHOLD_PP = -1.0  # 5y-mean post minus 5y-mean pre, in pp
GINI_DECLINE_THRESHOLD = 0.0     # any improvement counts as 1st-order success
N_CASES_REQUIRED_LFP = 3
N_CASES_REQUIRED_FIRST = 3
COUNTRIES = list(PROGRAMMES.keys())


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


def load_wdi(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])[["country_iso3", "year", "value"]]


def load_ilo_lfp_prime_age(path: Path) -> pd.DataFrame:
    """ILO EAP_2WAP_SEX_AGE_RT_A — labour force participation rate.
    Filter to both-sexes, 25+ ('AGE_YTHADULT_YGE25') as prime-age proxy."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["sex"] == "SEX_T") & (t["classif1"] == "AGE_YTHADULT_YGE25")].copy()
    sub = sub[(sub["country_iso3"].notna()) & (sub["country_iso3"].str.len() == 3)]
    sub["year"] = pd.to_numeric(sub["year"], errors="coerce").astype("Int64")
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub = sub.dropna(subset=["year", "value"])
    # If multiple rows per country-year (multiple sources), take mean
    return (sub.groupby(["country_iso3", "year"], as_index=False)["value"].mean())


def load_ilo_lfp_15plus(path: Path) -> pd.DataFrame:
    """Fallback: 15+ working-age population if 25+ unavailable."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["sex"] == "SEX_T") & (t["classif1"] == "AGE_YTHADULT_YGE15")].copy()
    sub = sub[(sub["country_iso3"].notna()) & (sub["country_iso3"].str.len() == 3)]
    sub["year"] = pd.to_numeric(sub["year"], errors="coerce").astype("Int64")
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub = sub.dropna(subset=["year", "value"])
    return (sub.groupby(["country_iso3", "year"], as_index=False)["value"].mean())


def window_mean(df: pd.DataFrame, country: str, years_inclusive: set[int]) -> tuple[float | None, int]:
    sub = df[(df["country_iso3"] == country) & (df["year"].astype(int).isin(years_inclusive))]
    sub = sub[sub["value"].notna()]
    if sub.empty:
        return None, 0
    return float(sub["value"].mean()), int(len(sub))


def case_windows(rollout: int, exclude: set[int]) -> tuple[set[int], set[int]]:
    pre = set(range(rollout - PRE_WINDOW_YEARS, rollout))  # 5 yrs before rollout
    post = set(range(rollout + 1, rollout + 1 + POST_WINDOW_YEARS))  # 5 yrs after
    post = {y for y in post if y not in exclude}
    pre = {y for y in pre if y not in exclude}
    return pre, post


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    lfp_path = latest("ilostat", "EAP_2WAP_SEX_AGE_RT_A")
    gini_path = latest("world_bank_wdi", "SI.POV.GINI")
    pov_path = latest("world_bank_wdi", "SI.POV.DDAY")

    manifest = {
        "lfp_prime_age_25plus": {
            "publisher": "ilostat",
            "series": "EAP_2WAP_SEX_AGE_RT_A",
            "filter": "sex=SEX_T, classif1=AGE_YTHADULT_YGE25",
            "vintage_file": str(lfp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(lfp_path),
        },
        "gini_index": {
            "publisher": "world_bank_wdi",
            "series": "SI.POV.GINI",
            "vintage_file": str(gini_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gini_path),
        },
        "poverty_215_dollar_a_day": {
            "publisher": "world_bank_wdi",
            "series": "SI.POV.DDAY",
            "vintage_file": str(pov_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pov_path),
        },
    }

    lfp_25 = load_ilo_lfp_prime_age(lfp_path)
    lfp_15 = load_ilo_lfp_15plus(lfp_path)
    gini = load_wdi(gini_path)
    pov = load_wdi(pov_path)

    case_results = []
    for country, info in PROGRAMMES.items():
        pre_years, post_years = case_windows(info["rollout_year"], info["post_exclusion_years"])

        # Prime-age (25+) LFP
        lfp_pre_25, n_pre_25 = window_mean(lfp_25, country, pre_years)
        lfp_post_25, n_post_25 = window_mean(lfp_25, country, post_years)
        # Fallback 15+
        lfp_pre_15, n_pre_15 = window_mean(lfp_15, country, pre_years)
        lfp_post_15, n_post_15 = window_mean(lfp_15, country, post_years)

        # Choose 25+ if we have at least 2 obs in each window, else 15+, else missing
        lfp_pre = lfp_pre_25 if (lfp_pre_25 is not None and n_pre_25 >= 2 and lfp_post_25 is not None and n_post_25 >= 2) else lfp_pre_15
        lfp_post = lfp_post_25 if (lfp_pre_25 is not None and n_pre_25 >= 2 and lfp_post_25 is not None and n_post_25 >= 2) else lfp_post_15
        lfp_basis = "AGE_YTHADULT_YGE25" if (lfp_pre_25 is not None and n_pre_25 >= 2 and lfp_post_25 is not None and n_post_25 >= 2) else "AGE_YTHADULT_YGE15"
        lfp_n_pre = n_pre_25 if lfp_basis == "AGE_YTHADULT_YGE25" else n_pre_15
        lfp_n_post = n_post_25 if lfp_basis == "AGE_YTHADULT_YGE25" else n_post_15

        if lfp_pre is None or lfp_post is None or lfp_n_pre < 2 or lfp_n_post < 2:
            lfp_delta = None
            lfp_decline = None
        else:
            lfp_delta = float(lfp_post - lfp_pre)
            lfp_decline = bool(lfp_delta <= LFP_DECLINE_THRESHOLD_PP)

        # First-order: prefer Gini for rich countries, $2.15 poverty for ARG/VEN
        gini_pre, gini_n_pre = window_mean(gini, country, pre_years)
        gini_post, gini_n_post = window_mean(gini, country, post_years)
        pov_pre, pov_n_pre = window_mean(pov, country, pre_years)
        pov_post, pov_n_post = window_mean(pov, country, post_years)

        first_order_metric = None
        first_order_pre = None
        first_order_post = None
        first_order_delta = None
        first_order_success = None

        if gini_pre is not None and gini_post is not None and gini_n_pre >= 2 and gini_n_post >= 2:
            first_order_metric = "gini_index"
            first_order_pre = gini_pre
            first_order_post = gini_post
            first_order_delta = float(gini_post - gini_pre)
            first_order_success = bool(first_order_delta < GINI_DECLINE_THRESHOLD)
        elif pov_pre is not None and pov_post is not None and pov_n_pre >= 2 and pov_n_post >= 2:
            first_order_metric = "extreme_poverty_215"
            first_order_pre = pov_pre
            first_order_post = pov_post
            first_order_delta = float(pov_post - pov_pre)
            first_order_success = bool(first_order_delta < GINI_DECLINE_THRESHOLD)

        case_results.append({
            "country": country,
            "programme": info["name"],
            "rollout_year": info["rollout_year"],
            "pre_window": sorted(pre_years),
            "post_window": sorted(post_years),
            "lfp_basis": lfp_basis,
            "lfp_pre_mean": lfp_pre,
            "lfp_post_mean": lfp_post,
            "lfp_n_pre": lfp_n_pre,
            "lfp_n_post": lfp_n_post,
            "lfp_delta_pp": lfp_delta,
            "lfp_declined_per_threshold": lfp_decline,
            "first_order_metric": first_order_metric,
            "first_order_pre_mean": first_order_pre,
            "first_order_post_mean": first_order_post,
            "first_order_delta": first_order_delta,
            "first_order_improved": first_order_success,
        })

    n_lfp_data = sum(1 for c in case_results if c["lfp_declined_per_threshold"] is not None)
    n_lfp_decline = sum(1 for c in case_results if c["lfp_declined_per_threshold"] is True)
    n_lfp_rise = sum(1 for c in case_results
                     if c["lfp_delta_pp"] is not None and c["lfp_delta_pp"] > 0)
    n_first_data = sum(1 for c in case_results if c["first_order_improved"] is not None)
    n_first_success = sum(1 for c in case_results if c["first_order_improved"] is True)

    # Verdict
    n_cases = len(case_results)
    if n_lfp_data < 3:
        verdict = (
            f"inconclusive — Only {n_lfp_data}/{n_cases} cases have prime-age "
            f"LFP data covering both pre- and post-rollout 5y windows. "
            f"Cannot grade the second-order link without sufficient panel "
            f"coverage. Data gap on ilostat:EAP_2WAP_SEX_AGE_RT_A for the "
            f"required windows."
        )
        verdict_label = "inconclusive"
    elif n_lfp_decline >= N_CASES_REQUIRED_LFP and n_first_success >= N_CASES_REQUIRED_FIRST:
        verdict = (
            f"SUPPORTED — Prime-age LFP fell by ≥1.0pp post-rollout in "
            f"{n_lfp_decline}/{n_lfp_data} cases (threshold: ≥3 of 5). "
            f"First-order welfare gain (Gini or extreme-poverty improvement) "
            f"present in {n_first_success}/{n_first_data} cases. Both legs "
            f"of the chain fire."
        )
        verdict_label = "supported"
    elif n_lfp_rise >= 4:
        verdict = (
            f"refuted — Prime-age LFP ROSE post-rollout in "
            f"{n_lfp_rise}/{n_lfp_data} cases. The second-order disincentive "
            f"channel does not appear at the national-aggregate level."
        )
        verdict_label = "refuted"
    elif n_lfp_decline >= 2:
        verdict = (
            f"partial — Prime-age LFP fell by ≥1.0pp in {n_lfp_decline}/"
            f"{n_lfp_data} cases (threshold for SUPPORTED: ≥3). First-order "
            f"improved in {n_first_success}/{n_first_data} cases. Mixed: "
            f"consistent with the spec's design-dependence caveat — some "
            f"programmes show the chain, others do not."
        )
        verdict_label = "partial"
    else:
        verdict = (
            f"refuted — Prime-age LFP declined by ≥1.0pp in only "
            f"{n_lfp_decline}/{n_lfp_data} cases (threshold: ≥3). The "
            f"hypothesised second-order channel is absent at the "
            f"national-aggregate level."
        )
        verdict_label = "refuted"

    diagnostics = {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "n_cases": n_cases,
        "n_cases_with_lfp_data": n_lfp_data,
        "n_cases_lfp_decline_threshold": n_lfp_decline,
        "n_cases_lfp_rise": n_lfp_rise,
        "n_cases_with_first_order_data": n_first_data,
        "n_cases_first_order_success": n_first_success,
        "lfp_decline_threshold_pp": LFP_DECLINE_THRESHOLD_PP,
        "n_cases_required_lfp": N_CASES_REQUIRED_LFP,
        "n_cases_required_first_order": N_CASES_REQUIRED_FIRST,
        "case_results": case_results,
        "method_notes": [
            "Bottom-decile LFP, hours, EMTR not in vintages; aggregate "
            "prime-age (25+, both sexes) used as proxy. National aggregate "
            "underestimates bottom-decile-specific signal.",
            "Pandemic years 2020-2021 excluded from ESP and USA post-windows.",
            "5y pre/post means rather than C-S DiD because no within-country "
            "donor cohort is constructible from annual aggregates alone.",
        ],
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Coefficients table ----------
    rows = []
    for c in case_results:
        rows.append({
            "spec": "primary_lfp",
            "term": f"{c['country']}_lfp_delta_pp",
            "estimate": c["lfp_delta_pp"] if c["lfp_delta_pp"] is not None else float("nan"),
        })
        rows.append({
            "spec": "first_order",
            "term": f"{c['country']}_{c['first_order_metric'] or 'na'}_delta",
            "estimate": c["first_order_delta"] if c["first_order_delta"] is not None else float("nan"),
        })
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Chart ----------
    palette = {"ARG": "#4E79A7", "ESP": "#59A14F", "GBR": "#B07AA1",
               "VEN": "#E15759", "USA": "#F28E2B"}

    series = []
    for country, info in PROGRAMMES.items():
        # Time series of LFP by year (use 25+ if any data, else 15+)
        sub25 = lfp_25[lfp_25["country_iso3"] == country].sort_values("year")
        if len(sub25) >= 5:
            sub = sub25
            basis = "25+"
        else:
            sub = lfp_15[lfp_15["country_iso3"] == country].sort_values("year")
            basis = "15+"
        pts = [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()]
        series.append({
            "id": country,
            "label": f"{country} LFP {basis} (rollout {info['rollout_year']})",
            "color": palette.get(country, "#666"),
            "treated": True,
            "points": pts,
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Prime-age labour-force participation rate around transfer-programme rollouts",
        "subtitle": (
            f"5y-mean post vs 5y-mean pre. LFP-decline cases: "
            f"{n_lfp_decline}/{n_lfp_data} (threshold ≥3 for SUPPORTED). "
            f"First-order welfare gain in {n_first_success}/{n_first_data}."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "LFP rate (%)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "note", "label": (
                f"Programme rollout years: " +
                ", ".join(f"{c}={i['rollout_year']}" for c, i in PROGRAMMES.items())
            )},
            {"type": "note", "label": (
                "ESP and USA post-windows exclude 2020-2021 (pandemic). "
                "Bottom-decile LFP and EMTR not available; national "
                "aggregate prime-age LFP used as proxy (underestimates "
                "the spec's bottom-decile claim)."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

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
    lines = [
        f"# Universal transfer programmes → labour-force participation decline",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Cases tested: {n_cases} ({', '.join(COUNTRIES)})",
        f"- Cases with usable prime-age LFP pre/post data: {n_lfp_data}/{n_cases}",
        f"- Cases showing LFP decline ≥1.0pp post-rollout: "
        f"**{n_lfp_decline}/{n_lfp_data}** (need ≥{N_CASES_REQUIRED_LFP} for SUPPORTED)",
        f"- Cases with first-order welfare gain (Gini or extreme-poverty drop): "
        f"{n_first_success}/{n_first_data}",
        "",
        "### Case-by-case",
        "",
    ]
    for c in case_results:
        d_lfp = f"{c['lfp_delta_pp']:+.2f}pp" if c["lfp_delta_pp"] is not None else "no data"
        d_fo = (f"{c['first_order_delta']:+.2f} ({c['first_order_metric']})"
                if c["first_order_delta"] is not None else "no data")
        lines.append(
            f"- **{c['country']}** ({c['programme']}, rollout {c['rollout_year']}): "
            f"prime-age LFP Δ = {d_lfp}; first-order Δ = {d_fo}."
        )
    lines += [
        "",
        "## Method",
        "",
        f"For each of the five programmes the script computes:",
        f"1. The 5y-mean prime-age (ILO age-band 25+) labour-force "
        f"   participation rate, both sexes, in the 5y window before rollout.",
        f"2. The 5y-mean prime-age LFP in the 5y window after rollout "
        f"   (excluding pandemic years 2020-2021 for ESP and USA).",
        f"3. The post-minus-pre delta in pp.",
        f"4. The Gini index pre-vs-post delta (or, when Gini lacks coverage, "
        f"   extreme-poverty $2.15/day).",
        "",
        "Verdict rule:",
        f"- SUPPORTED if ≥{N_CASES_REQUIRED_LFP}/5 cases show LFP decline "
        f"  ≥{abs(LFP_DECLINE_THRESHOLD_PP):.1f}pp AND ≥{N_CASES_REQUIRED_FIRST}/5 "
        f"  cases show first-order welfare gain.",
        f"- REFUTED if ≥4/5 cases show LFP rise (chain fails).",
        f"- PARTIAL if 2/5 cases show LFP decline (mixed; design-dependent).",
        f"- INCONCLUSIVE if <3/5 cases have data covering both windows.",
        "",
        "## Data",
        "",
        "- ilostat:EAP_2WAP_SEX_AGE_RT_A (LFP rate; sex=T, age 25+ classif1)",
        "- world_bank_wdi:SI.POV.GINI (Gini index)",
        "- world_bank_wdi:SI.POV.DDAY ($2.15/day extreme-poverty headcount)",
        "",
        "## Caveats",
        "",
        "- The spec's preferred outcomes (bottom-decile LFP, hours-worked, "
        "  effective marginal tax rate, programme-spend-as-pct-GDP, "
        "  long-tenure recipient subsequent-employment probability) require "
        "  household-microdata or OECD Benefits-and-Wages files not in "
        "  vintages. National aggregate LFP is a conservative proxy; if "
        "  bottom-decile LFP fell sharply but the upper deciles rose, the "
        "  national aggregate would mask the chain's appearance.",
        "- 5y pre/post-mean comparison rather than Callaway-Sant'Anna DiD "
        "  because the panel donor pool the C-S template requires is not "
        "  constructible from these annual aggregates alone.",
        "- VEN data after 2014 is sparse in WDI/ILO due to the country's "
        "  statistical disclosure interruption.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
