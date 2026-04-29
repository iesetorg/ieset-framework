#!/usr/bin/env python3
"""Replication — Bismarckian welfare architectures vs Beveridgean: fiscal sustainability under ageing.

Spec: hypotheses/fiscal/bismarckian_welfare_fiscal_sustainability.yaml v1
Position-claim: ordoliberal #5 (school predicts: supported)

The ordoliberal claim: contributory-Bismarckian welfare states (DEU, AUT,
CHE — supplemented by FRA, BEL, ITA which the spec also codes Bismarckian)
are MORE fiscally sustainable than Beveridgean tax-financed universal
states (GBR, SWE, DNK, FIN, NOR, NLD, IRL, USA) when demographic ageing
is severe, because the contribution-benefit linkage is supposed to
constrain expansion.

Multi-metric checklist (4 metrics from the spec):
  M1 (PRIMARY):  public pension expenditure / GDP — Bismarckian < Beveridgean
                 mean by 2018-2023.  Series: oecd:PensionExpenditure /
                 eurostat:spr_exp_pens.
  M2 (PRIMARY):  implicit pension debt / GDP — Bismarckian < Beveridgean.
                 Series: oecd:ImplicitPensionDebt.
  M3 (informative): net replacement rate — directionally LOWER in
                 Bismarckian if "contribution-benefit linkage constrains
                 expansion" is right. Series: oecd:NetReplacementRate.
  M4 (informative): total social contribution rate / wage — directionally
                 HIGHER in Bismarckian (the contributory architecture
                 demands it). Series: oecd:SocialContributionRate.

Spec falsification: "Refute if Bismarckian regimes do not score better on
≥3 of 4 metrics under matched dependency-ratio shifts."

Sharpened threshold (PRIMARY, dispositive):
  SUPPORTED if Bismarckian-mean is at least 1.5pp of GDP LOWER than
  Beveridgean-mean for BOTH pension-expenditure (M1) and implicit
  pension debt (M2) in the 2018-2023 window, conditional on similar
  old-age dependency ratios. REFUTED if M1 and M2 BOTH show Bismarckian
  ≥ Beveridgean at the same threshold, with the dispersion sign flipped.
  PARTIAL otherwise.

DATA-GAP PROTOCOL:
  None of the four spec-named series (oecd:PensionExpenditure,
  oecd:ImplicitPensionDebt, oecd:NetReplacementRate,
  oecd:SocialContributionRate) is in the current data vintage —
  data/vintages/oecd/ contains the OECD SDMX bulk parquets but no
  per-indicator pension expenditure / replacement rate / contribution
  rate fetcher has been built. Per HANDOFF_TO_RUN_AGENT.md "What to do
  when your spec needs data that isn't on disk", the verdict is
  inconclusive (data gap on oecd:PensionExpenditure,
  oecd:ImplicitPensionDebt, oecd:NetReplacementRate,
  oecd:SocialContributionRate); the script becomes immediately
  re-runnable once the OECD pension fetchers land.

  As an INFORMATIVE-ONLY auxiliary, we run a general-government
  fiscal-trajectory comparison on the same Bismarckian / Beveridgean
  partition using the available IMF series (GGXWDG_NGDP general gov
  gross debt, exp general gov expenditure / GDP). This colours the
  result-card with a directional read but does NOT decide the verdict —
  general gov debt and expenditure are NOT the spec's pre-registered
  pension-specific metrics. The auxiliary is reported as informative
  context only.
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
HID = "bismarckian_welfare_fiscal_sustainability"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Treatment partition (from spec.variables.treatment.bismarckian_architecture)
BISMARCKIAN = ["DEU", "AUT", "CHE", "FRA", "BEL", "ITA"]
BEVERIDGEAN = ["GBR", "IRL", "DNK", "SWE", "FIN", "NOR", "NLD", "USA"]

# Other countries in spec.sample (ESP, GRC, JPN, PRT) are mixed/southern-European
# regimes; the Esping-Andersen typology cross-walked to OECD pension classification
# typically codes ESP/GRC/PRT/ITA as "Mediterranean Bismarckian-derivative" and JPN
# as Bismarckian-derivative. The spec codes only DEU/AUT/CHE/FRA/BEL/ITA as
# Bismarckian, so we follow the spec exactly here.

PERIOD = (1990, 2023)
LATE_WINDOW = (2018, 2023)
EARLY_WINDOW = (1990, 1995)

# Sharpened thresholds (replacing spec stub "≥3 of 4 metrics" with dispositive
# pp-of-GDP gaps; see hypotheses YAML methodology_note for promotion rationale).
PCT_GDP_GAP_THRESHOLD_PP = 1.5    # M1, M2: Bismarckian must be 1.5pp LOWER
REPLACEMENT_RATE_GAP_PP = 5.0      # M3: directional — Bismarckian lower by 5pp
CONTRIB_RATE_GAP_PP = 3.0          # M4: directional — Bismarckian higher by 3pp


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    return files[-1]


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year", "indicator_id",
                "unit", "obs_status", "decimal"}
        cands = [c for c in t.columns if c not in meta]
        if not cands:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def window_mean_country(df: pd.DataFrame, country: str, lo: int, hi: int) -> float:
    sub = df[
        (df["country_iso3"] == country) & (df["year"].between(lo, hi))
    ]["value"]
    return float(sub.mean()) if len(sub) else float("nan")


def group_mean(df: pd.DataFrame, countries: list[str], lo: int, hi: int) -> tuple[float, int]:
    """Mean of country-window-means for a country group. Returns (mean, n_with_data)."""
    vals = []
    for c in countries:
        v = window_mean_country(df, c, lo, hi)
        if not np.isnan(v):
            vals.append(v)
    if not vals:
        return float("nan"), 0
    return float(np.mean(vals)), len(vals)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Resolve the FOUR primary spec series ----------
    primary_series = [
        ("pension_expenditure_pct_gdp", "oecd", "PensionExpenditure"),
        ("implicit_pension_debt_pct_gdp", "oecd", "ImplicitPensionDebt"),
        ("net_replacement_rate", "oecd", "NetReplacementRate"),
        ("contribution_rate_total", "oecd", "SocialContributionRate"),
    ]
    primary_paths: dict[str, Path | None] = {
        name: latest(pub, series) for (name, pub, series) in primary_series
    }
    primary_meta: dict[str, tuple[str, str]] = {
        name: (pub, series) for (name, pub, series) in primary_series
    }

    # Auxiliary IMF/WDI series (for the informative leg only)
    debt_path = latest("imf", "GGXWDG_NGDP")          # general gov gross debt / GDP
    exp_path = latest("imf", "exp")                    # general gov expenditure / GDP
    pop_path = latest("world_bank_wdi", "SP.POP.TOTL")  # for context only

    # ---------- Manifest (record everything, including missing series) ----------
    manifest: dict = {}
    for (name, pub, series) in primary_series:
        path = primary_paths[name]
        if path is None:
            manifest[name] = {"publisher": pub, "series": series, "missing": True}
        else:
            manifest[name] = {
                "publisher": pub, "series": series,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
            }
    for name, pub, series, path in [
        ("aux_general_gov_debt_pct_gdp", "imf", "GGXWDG_NGDP", debt_path),
        ("aux_general_gov_expenditure_pct_gdp", "imf", "exp", exp_path),
        ("aux_population", "world_bank_wdi", "SP.POP.TOTL", pop_path),
    ]:
        if path is None:
            manifest[name] = {"publisher": pub, "series": series, "missing": True}
        else:
            manifest[name] = {
                "publisher": pub, "series": series,
                "vintage_file": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
            }

    # ---------- Per-metric primary tests (all gated on data availability) ----------
    metrics: dict[str, dict] = {}

    def run_pct_gdp_metric(name: str, direction: str, threshold_pp: float) -> dict:
        """Bismarckian-mean vs Beveridgean-mean in LATE_WINDOW.
        direction='lower': Bismarckian < Beveridgean by threshold_pp -> pass.
        direction='higher': Bismarckian > Beveridgean by threshold_pp -> pass.
        """
        path = primary_paths.get(name)
        if path is None:
            pub, series = primary_meta.get(name, ("oecd", name))
            return {"available": False, "publisher": pub, "series": series}
        df = load_long(path)
        bi_mean, bi_n = group_mean(df, BISMARCKIAN, *LATE_WINDOW)
        be_mean, be_n = group_mean(df, BEVERIDGEAN, *LATE_WINDOW)
        if np.isnan(bi_mean) or np.isnan(be_mean):
            return {"available": False, "reason": "no overlapping data in window",
                    "bi_mean": bi_mean, "be_mean": be_mean,
                    "bi_n": bi_n, "be_n": be_n}
        gap = bi_mean - be_mean   # negative = Bismarckian lower
        if direction == "lower":
            passes = gap <= -threshold_pp
        else:
            passes = gap >= threshold_pp
        return {
            "available": True,
            "bi_mean": bi_mean, "be_mean": be_mean,
            "bi_n_countries_with_data": bi_n, "be_n_countries_with_data": be_n,
            "gap_bi_minus_be_pp": gap,
            "direction_required": direction,
            "threshold_pp": threshold_pp,
            "passes_in_claimed_direction": bool(passes),
        }

    metrics["M1_pension_expenditure_pct_gdp"] = run_pct_gdp_metric(
        "pension_expenditure_pct_gdp", "lower", PCT_GDP_GAP_THRESHOLD_PP)
    metrics["M2_implicit_pension_debt_pct_gdp"] = run_pct_gdp_metric(
        "implicit_pension_debt_pct_gdp", "lower", PCT_GDP_GAP_THRESHOLD_PP)
    metrics["M3_net_replacement_rate"] = run_pct_gdp_metric(
        "net_replacement_rate", "lower", REPLACEMENT_RATE_GAP_PP)
    metrics["M4_contribution_rate_total"] = run_pct_gdp_metric(
        "contribution_rate_total", "higher", CONTRIB_RATE_GAP_PP)

    primary_available = all(m["available"] for m in metrics.values())

    # ---------- Auxiliary (INFORMATIVE-ONLY) general-government fiscal leg ----------
    # NOT a substitute for the pension-specific primary metrics; just a sanity
    # read of broader fiscal sustainability under ageing.
    aux: dict = {"available": False}
    if debt_path is not None and exp_path is not None:
        debt = load_long(debt_path)
        exp = load_long(exp_path)
        bi_debt_late, bi_debt_n = group_mean(debt, BISMARCKIAN, *LATE_WINDOW)
        be_debt_late, be_debt_n = group_mean(debt, BEVERIDGEAN, *LATE_WINDOW)
        bi_exp_late, bi_exp_n = group_mean(exp, BISMARCKIAN, *LATE_WINDOW)
        be_exp_late, be_exp_n = group_mean(exp, BEVERIDGEAN, *LATE_WINDOW)
        bi_debt_early, _ = group_mean(debt, BISMARCKIAN, *EARLY_WINDOW)
        be_debt_early, _ = group_mean(debt, BEVERIDGEAN, *EARLY_WINDOW)
        aux = {
            "available": True,
            "bi_general_gov_debt_late_pct_gdp": bi_debt_late,
            "be_general_gov_debt_late_pct_gdp": be_debt_late,
            "debt_gap_bi_minus_be_pp": bi_debt_late - be_debt_late,
            "bi_general_gov_expenditure_late_pct_gdp": bi_exp_late,
            "be_general_gov_expenditure_late_pct_gdp": be_exp_late,
            "expenditure_gap_bi_minus_be_pp": bi_exp_late - be_exp_late,
            "bi_general_gov_debt_early_pct_gdp": bi_debt_early,
            "be_general_gov_debt_early_pct_gdp": be_debt_early,
            "bi_debt_drift_pp": bi_debt_late - bi_debt_early,
            "be_debt_drift_pp": be_debt_late - be_debt_early,
            "n_bismarckian_with_data": bi_debt_n,
            "n_beveridgean_with_data": be_debt_n,
        }

    # ---------- Verdict ----------
    if not primary_available:
        missing = [
            f"{m['publisher']}:{m['series']}"
            for m in (manifest[k] for k in [
                "pension_expenditure_pct_gdp",
                "implicit_pension_debt_pct_gdp",
                "net_replacement_rate",
                "contribution_rate_total",
            ])
            if m.get("missing")
        ]
        # Aux summary string for context
        aux_bit = ""
        if aux.get("available"):
            debt_gap = aux["debt_gap_bi_minus_be_pp"]
            exp_gap = aux["expenditure_gap_bi_minus_be_pp"]
            aux_bit = (
                f" Auxiliary (NOT dispositive — general-government, not "
                f"pension-specific): in {LATE_WINDOW[0]}-{LATE_WINDOW[1]} "
                f"Bismarckian general-gov debt is {debt_gap:+.1f}pp of GDP "
                f"vs Beveridgean (Bismarckian "
                f"{aux['bi_general_gov_debt_late_pct_gdp']:.1f}%, "
                f"Beveridgean {aux['be_general_gov_debt_late_pct_gdp']:.1f}%); "
                f"general-gov expenditure {exp_gap:+.1f}pp "
                f"(Bismarckian {aux['bi_general_gov_expenditure_late_pct_gdp']:.1f}%, "
                f"Beveridgean {aux['be_general_gov_expenditure_late_pct_gdp']:.1f}%). "
                f"Sign of the gap (positive = Bismarckian higher) is the "
                f"opposite of what the ordoliberal claim predicts for the "
                f"pension-specific metrics, but general-gov fiscal aggregates "
                f"can diverge from pension-specific outcomes."
            )
        verdict = (
            f"inconclusive (data gap on {', '.join(missing)}) — none of "
            f"the four pre-registered pension-specific metrics "
            f"(pension expenditure / GDP, implicit pension debt / GDP, "
            f"net replacement rate, total social contribution rate) are "
            f"in the current data vintage. The Bismarckian-vs-Beveridgean "
            f"comparison cannot be dispositively scored until the OECD "
            f"pension-system fetchers land.{aux_bit}"
        )
        all_pass = False
        n_passing = 0
    else:
        n_passing = sum(1 for m in metrics.values()
                        if m["available"] and m["passes_in_claimed_direction"])
        m1_pass = metrics["M1_pension_expenditure_pct_gdp"]["passes_in_claimed_direction"]
        m2_pass = metrics["M2_implicit_pension_debt_pct_gdp"]["passes_in_claimed_direction"]
        m1_gap = metrics["M1_pension_expenditure_pct_gdp"]["gap_bi_minus_be_pp"]
        m2_gap = metrics["M2_implicit_pension_debt_pct_gdp"]["gap_bi_minus_be_pp"]
        # SUPPORTED: BOTH primary fiscal metrics show Bismarckian-lower by
        # threshold (M1 + M2). REFUTED: BOTH show Bismarckian higher (gap >= 0).
        if m1_pass and m2_pass:
            verdict = (
                f"SUPPORTED — Bismarckian pension-expenditure / GDP "
                f"{m1_gap:+.1f}pp vs Beveridgean (≤ -{PCT_GDP_GAP_THRESHOLD_PP:.1f}pp "
                f"threshold met) AND implicit pension debt / GDP "
                f"{m2_gap:+.1f}pp ({n_passing}/4 total metrics pass)."
            )
            all_pass = True
        elif m1_gap >= 0 and m2_gap >= 0:
            verdict = (
                f"refuted — Bismarckian pension-expenditure / GDP is "
                f"{m1_gap:+.1f}pp vs Beveridgean (Bismarckian "
                f"{'higher' if m1_gap > 0 else 'equal'}, opposite of claim) "
                f"AND implicit pension debt {m2_gap:+.1f}pp "
                f"({'higher' if m2_gap > 0 else 'equal'}). The "
                f"contribution-benefit-link sustainability premise does not "
                f"survive: contributory architectures are not lower on either "
                f"primary fiscal-pressure metric."
            )
            all_pass = False
        else:
            verdict = (
                f"partial — {n_passing}/4 metrics pass in the claimed "
                f"direction. M1 pension-exp/GDP gap {m1_gap:+.1f}pp "
                f"(pass={m1_pass}); M2 implicit-debt/GDP gap {m2_gap:+.1f}pp "
                f"(pass={m2_pass}). Mixed evidence on the "
                f"sustainability-from-architecture claim."
            )
            all_pass = False

    diagnostics = {
        "verdict": verdict,
        "all_pass": all_pass,
        "n_metrics_passing_in_claimed_direction": n_passing,
        "primary_metrics_available": primary_available,
        "thresholds": {
            "pct_gdp_gap_pp": PCT_GDP_GAP_THRESHOLD_PP,
            "replacement_rate_gap_pp": REPLACEMENT_RATE_GAP_PP,
            "contribution_rate_gap_pp": CONTRIB_RATE_GAP_PP,
        },
        "windows": {
            "early": list(EARLY_WINDOW),
            "late": list(LATE_WINDOW),
        },
        "treatment_groups": {
            "bismarckian": BISMARCKIAN,
            "beveridgean": BEVERIDGEAN,
        },
        "metrics": metrics,
        "auxiliary_general_gov_fiscal_leg_informative_only": aux,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- coefficients.parquet ----------
    coef_rows: list[dict] = []
    for k, m in metrics.items():
        if m.get("available"):
            coef_rows.append({"spec": k, "term": "bi_mean", "estimate": m["bi_mean"]})
            coef_rows.append({"spec": k, "term": "be_mean", "estimate": m["be_mean"]})
            coef_rows.append({"spec": k, "term": "gap_bi_minus_be_pp",
                              "estimate": m["gap_bi_minus_be_pp"]})
        else:
            coef_rows.append({"spec": k, "term": "missing", "estimate": float("nan")})
    if aux.get("available"):
        coef_rows.append({"spec": "aux_general_gov_debt", "term": "bi_late_mean",
                          "estimate": aux["bi_general_gov_debt_late_pct_gdp"]})
        coef_rows.append({"spec": "aux_general_gov_debt", "term": "be_late_mean",
                          "estimate": aux["be_general_gov_debt_late_pct_gdp"]})
        coef_rows.append({"spec": "aux_general_gov_debt", "term": "gap_bi_minus_be_pp",
                          "estimate": aux["debt_gap_bi_minus_be_pp"]})
        coef_rows.append({"spec": "aux_general_gov_expenditure", "term": "bi_late_mean",
                          "estimate": aux["bi_general_gov_expenditure_late_pct_gdp"]})
        coef_rows.append({"spec": "aux_general_gov_expenditure", "term": "be_late_mean",
                          "estimate": aux["be_general_gov_expenditure_late_pct_gdp"]})
        coef_rows.append({"spec": "aux_general_gov_expenditure", "term": "gap_bi_minus_be_pp",
                          "estimate": aux["expenditure_gap_bi_minus_be_pp"]})
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- chart_data.json ----------
    # Use general-gov debt trajectory as the headline chart (it has data; the
    # primary pension-specific series are missing).
    palette_bi = ["#4E79A7", "#59A14F", "#B07AA1", "#F28E2B", "#76B7B2", "#9C755F"]
    palette_be = ["#E15759", "#EDC948", "#B6992D", "#8884d8", "#82ca9d", "#ffc658",
                  "#d62728", "#bcbd22"]

    series = []
    if debt_path is not None:
        debt = load_long(debt_path)
        for i, c in enumerate(BISMARCKIAN):
            sub = (
                debt[(debt["country_iso3"] == c) & debt["year"].between(*PERIOD)]
                [["year", "value"]].dropna().sort_values("year")
            )
            if sub.empty:
                continue
            series.append({
                "id": c, "label": f"{c} (Bismarckian)",
                "color": palette_bi[i % len(palette_bi)],
                "treated": True,
                "points": [{"x": int(r.year), "y": float(r.value)}
                           for r in sub.itertuples()],
            })
        for i, c in enumerate(BEVERIDGEAN):
            sub = (
                debt[(debt["country_iso3"] == c) & debt["year"].between(*PERIOD)]
                [["year", "value"]].dropna().sort_values("year")
            )
            if sub.empty:
                continue
            series.append({
                "id": c, "label": f"{c} (Beveridgean)",
                "color": palette_be[i % len(palette_be)],
                "treated": False,
                "points": [{"x": int(r.year), "y": float(r.value)}
                           for r in sub.itertuples()],
            })

    chart_subtitle = (
        "DATA GAP on pre-registered pension-specific metrics — verdict is "
        "inconclusive. Chart shows general-government gross debt (NOT the "
        "primary metric; informative only)."
    )
    if primary_available:
        chart_subtitle = (
            f"Bismarckian vs Beveridgean fiscal sustainability under ageing, "
            f"{LATE_WINDOW[0]}-{LATE_WINDOW[1]}. Verdict: {verdict[:120]}..."
        )

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Bismarckian vs Beveridgean general government gross debt, 1990-2023",
        "subtitle": chart_subtitle,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "general gov gross debt, % of GDP", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "note", "label": (
                f"Verdict: {verdict[:200]}{'...' if len(verdict) > 200 else ''}"
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
        "# Bismarckian welfare architectures — fiscal sustainability under ageing",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Pre-registered four-metric checklist comparing contributory-Bismarckian "
        "welfare states (DEU, AUT, CHE, FRA, BEL, ITA per spec coding) against "
        "Beveridgean tax-financed states (GBR, IRL, DNK, SWE, FIN, NOR, NLD, USA), "
        f"in the {LATE_WINDOW[0]}-{LATE_WINDOW[1]} window where both groups face "
        "severe demographic ageing.",
        "",
        f"1. **M1 (PRIMARY)** — pension expenditure / GDP. Bismarckian-mean must "
        f"be ≥{PCT_GDP_GAP_THRESHOLD_PP:.1f}pp LOWER than Beveridgean.",
        f"2. **M2 (PRIMARY)** — implicit pension debt / GDP. Bismarckian-mean "
        f"must be ≥{PCT_GDP_GAP_THRESHOLD_PP:.1f}pp LOWER than Beveridgean.",
        f"3. **M3 (informative)** — net replacement rate. Directionally lower "
        f"in Bismarckian (≥{REPLACEMENT_RATE_GAP_PP:.0f}pp).",
        f"4. **M4 (informative)** — total social contribution rate / wage. "
        f"Directionally higher in Bismarckian (≥{CONTRIB_RATE_GAP_PP:.0f}pp).",
        "",
        "**SUPPORTED** if BOTH M1 and M2 pass (the dispositive primaries). "
        "**REFUTED** if BOTH show Bismarckian ≥ Beveridgean (opposite sign). "
        "**PARTIAL** otherwise.",
        "",
        "## Metric results",
        "",
    ]

    metric_labels = {
        "M1_pension_expenditure_pct_gdp": "M1 — Pension expenditure / GDP (PRIMARY)",
        "M2_implicit_pension_debt_pct_gdp": "M2 — Implicit pension debt / GDP (PRIMARY)",
        "M3_net_replacement_rate": "M3 — Net replacement rate (informative)",
        "M4_contribution_rate_total": "M4 — Total contribution rate / wage (informative)",
    }
    for k, m in metrics.items():
        lines.append(f"### {metric_labels[k]}")
        lines.append("")
        if not m.get("available"):
            lines.append("**DATA GAP — series not in current vintage.** "
                         "Re-runs automatically when the OECD pension fetcher lands.")
            lines.append("")
            continue
        lines += [
            f"- Bismarckian mean: **{m['bi_mean']:.1f}** "
            f"(n={m['bi_n_countries_with_data']} countries with data)",
            f"- Beveridgean mean: **{m['be_mean']:.1f}** "
            f"(n={m['be_n_countries_with_data']} countries with data)",
            f"- Gap (Bismarckian − Beveridgean): **{m['gap_bi_minus_be_pp']:+.1f}pp**",
            f"- Threshold for the claim's direction "
            f"(`{m['direction_required']}`): {m['threshold_pp']:.1f}pp",
            f"- Passes in claimed direction: "
            f"{'YES' if m['passes_in_claimed_direction'] else 'NO'}",
            "",
        ]

    if aux.get("available"):
        lines += [
            "## Auxiliary (INFORMATIVE-ONLY) — general government fiscal aggregates",
            "",
            "These are **NOT the spec's pre-registered pension-specific metrics**, "
            "they cover all government activity. Reported here only because the "
            "primary metrics are missing.",
            "",
            f"| Group | Gen-gov debt {LATE_WINDOW[0]}-{LATE_WINDOW[1]} (% GDP) | "
            f"Gen-gov exp {LATE_WINDOW[0]}-{LATE_WINDOW[1]} (% GDP) | "
            f"Debt drift since {EARLY_WINDOW[0]}-{EARLY_WINDOW[1]} (pp) |",
            "|---|---:|---:|---:|",
            f"| Bismarckian | {aux['bi_general_gov_debt_late_pct_gdp']:.1f} | "
            f"{aux['bi_general_gov_expenditure_late_pct_gdp']:.1f} | "
            f"{aux['bi_debt_drift_pp']:+.1f} |",
            f"| Beveridgean | {aux['be_general_gov_debt_late_pct_gdp']:.1f} | "
            f"{aux['be_general_gov_expenditure_late_pct_gdp']:.1f} | "
            f"{aux['be_debt_drift_pp']:+.1f} |",
            f"| Gap (Bi − Be) | {aux['debt_gap_bi_minus_be_pp']:+.1f} | "
            f"{aux['expenditure_gap_bi_minus_be_pp']:+.1f} | — |",
            "",
            "Ordoliberal claim predicts Bismarckian-lower on pension-specific "
            "metrics. The general-government aggregates above can diverge "
            "from pension-specific outcomes (e.g. Italy's high general-gov "
            "debt is largely structural / pre-ageing rather than driven by "
            "Bismarckian pension architecture per se).",
            "",
        ]

    lines += [
        "## Method",
        "",
        "Multi-metric checklist comparing two pre-defined country groups "
        "(Bismarckian / Beveridgean per spec.variables.treatment) on four "
        "OECD pension-system indicators. For each metric: country-window-"
        f"mean over {LATE_WINDOW[0]}-{LATE_WINDOW[1]} per country, then "
        "group-mean across countries with data. Pass criterion: gap "
        "between group means in claimed direction at the pre-registered "
        "pp threshold.",
        "",
        "## Caveats",
        "",
        "- All four pre-registered pension-specific OECD series "
        "(`PensionExpenditure`, `ImplicitPensionDebt`, `NetReplacementRate`, "
        "`SocialContributionRate`) are missing from the current data "
        "vintage — `data/vintages/oecd/` contains broader SDMX bulk "
        "parquets but no pension-system fetchers. The verdict is "
        "`inconclusive (data gap)` until those land.",
        "- The auxiliary general-government fiscal leg is **informative "
        "only** and is not the primary outcome. General-gov debt is "
        "driven by many forces (e.g. Italy's pre-existing structural "
        "stock, France's social-democratic-style universal coverage on "
        "top of contributory pensions) that are not the "
        "Bismarckian-architecture treatment.",
        "- The spec's country-coding follows Esping-Andersen typology "
        "cross-walked to OECD pension-system classification. ITA/FRA/BEL "
        "are coded Bismarckian per the spec; other typologies sometimes "
        "place ITA in a 'Mediterranean' cluster. v2 should report "
        "robustness to that recoding.",
        "- Old-age-dependency-ratio matching, requested by the spec's "
        "controls block, is not implemented in v1: WDI dependency-ratio "
        "series (`SP.POP.DPND.OL`) is also missing from the vintage. v2 "
        "should weight country contributions by dependency-ratio similarity.",
        "",
        "## Data",
        "",
    ]
    for k, v in manifest.items():
        if v.get("missing"):
            lines.append(f"- **MISSING** `{v['publisher']}:{v['series']}` "
                         f"(blocks the {k} leg)")
        else:
            lines.append(f"- {v['publisher']}:{v['series']} — `{v['vintage_file']}`")
    lines.append("")

    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict[:300]}")


if __name__ == "__main__":
    main()
