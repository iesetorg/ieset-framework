#!/usr/bin/env python3
"""Replication — Fiscal multipliers at the ZLB vs normal regime.

Spec: hypotheses/fiscal/fiscal_multipliers_zlb_higher_than_normal_regime.yaml v1
Position-claim: new_keynesian #3 (school predicts: supported)

The spec calls for a state-dependent LP-IV across an OECD panel
(1995-2021) using narrative fiscal-shock instruments (Ramey-Zubairy
defence-news; Guajardo-Leigh-Pescatori) with a country-level ZLB
regime indicator. Required inputs:

  - Quarterly OECD real GDP, government consumption (NAQ_GDP / OECD
    quarterly national accounts) for 21 OECD countries.
  - Narrative fiscal-shock series (Ramey defence-news; OLG international
    panel; Guajardo-Leigh-Pescatori narrative consolidations).
  - Country-quarter short-term policy rates for the panel.

Inventory of data on disk (`data/vintages/`):

  - FRED has the US quarterly real GDP (GDPC1), federal expenditures
    (FGEXPND), GDP deflator (GDPDEF), and monthly FEDFUNDS / daily DFF
    policy rate. These cover the US only.
  - IMF (data/vintages/imf/) has annual NGDP_RPCH, GGXCNL_NGDP,
    GGXWDG_NGDP, NGDPDPC for the panel — annual, not quarterly, and
    no government-consumption quarterly series.
  - OECD (data/vintages/oecd/) holds tax-revenue, prices, productivity,
    EPL, IDD, and health vintages — no quarterly NAQ_GDP and no
    quarterly government consumption.
  - No narrative fiscal-shock series is on disk under any publisher
    (no Ramey defence-news, no Guajardo-Leigh-Pescatori).

So the spec's identification (state-dependent LP-IV, OECD panel,
narrative IV) cannot be supported with the data the framework holds.
Per HANDOFF_TO_RUN_AGENT.md "What to do when your spec needs data
that isn't on disk" → emit `inconclusive (data gap on …)` and stop.

To keep the run ARTEFACT-COMPLETE and informative, this script also
runs a downgraded US-only state-dependent OLS local projection on the
FRED quarterly data:

  Δlog(real_gov_spending)_t  shock proxy
  Δlog(real_gdp)_{t..t+h}    cumulative response
  ZLB_t = 1 if FEDFUNDS quarterly average ≤ 0.25%, else 0

Cumulative multiplier at h is reported as the cumulative-response
coefficient on the shock, separately for the ZLB and normal regimes.
This is a US-only OLS LP — NOT the LP-IV panel the spec demands —
and is reported as an *informative diagnostic only*, not as
adjudicating the hypothesis. The verdict therefore remains
`inconclusive` regardless of the diagnostic's sign. The diagnostic is
useful for the next-run priors and for surfacing whether the
US-only signal even points the same way as the school's prediction.

PRIMARY (dispositive — gated by data availability)
  cumulative real-GDP multiplier on government-spending shocks at
  h = 8 quarters in the ZLB regime exceeds the same multiplier in
  the normal regime by at least +0.5, evaluated on the OECD panel
  with narrative-IV identification.

SECONDARY (informative diagnostic)
  US-only state-dependent OLS local projection of Δlog GDP at h=4,8,12
  quarters on the lag-1 federal-spending innovation, by ZLB indicator.
  Cumulative multiplier scaled by the steady-state spending share of
  GDP (G/Y).

METHOD_VALID
  All four required inputs present:
    (1) cross-country quarterly real GDP (OECD NAQ_GDP equivalent)
    (2) cross-country quarterly government consumption
    (3) narrative fiscal-shock series for at least 8 of 21 spec countries
    (4) ZLB indicator constructed from short-rate ≤ 0.25%
  Failure on any of (1)-(3) → verdict `inconclusive (data gap on …)`.

Verdict lead-words (parsed by web/lib/content.ts::verdictTone()):
  SUPPORTED / partial / refuted / weakened / inconclusive
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
HID = "fiscal_multipliers_zlb_higher_than_normal_regime"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Spec sample (sample.countries)
SPEC_COUNTRIES = [
    "AUS", "AUT", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
    "GBR", "IRL", "ITA", "JPN", "KOR", "NLD", "NOR", "NZL", "PRT", "SWE",
    "USA",
]
PANEL_PERIOD = (1995, 2021)
ZLB_RATE_THRESHOLD = 0.25  # short-rate <= 0.25% => ZLB regime
PRIMARY_HORIZON = 8        # quarters
PRIMARY_GAP_THRESHOLD = 0.5  # ZLB multiplier - normal multiplier >= 0.5


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
    return files[-1] if files else None


def load_fred(path: Path) -> pd.Series:
    """FRED schema is (date, value, realtime_start, realtime_end). Return a
    pd.Series indexed by date with the latest realtime cut already collapsed
    (the on-disk vintage is a single realtime snapshot)."""
    df = pq.read_table(path).to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"]).sort_values("date")
    s = df.set_index("date")["value"].astype(float)
    s = s[~s.index.duplicated(keep="last")]
    return s


def to_quarterly_mean(s: pd.Series) -> pd.Series:
    """Resample monthly/daily series to quarterly mean."""
    return s.resample("QS").mean()


def assess_required_panel_inputs() -> dict:
    """Check whether the spec's required quarterly OECD panel + narrative IV
    inputs exist on disk. Return a structured report."""
    report: dict = {"missing": [], "present": []}
    # Quarterly OECD national accounts (real GDP + govt consumption):
    oecd_dir = REPO_ROOT / "data" / "vintages" / "oecd"
    has_naq_gdp = any(
        "NAQ_GDP" in p.name or p.name.startswith("NAQ_")
        for p in oecd_dir.glob("*.parquet")
    ) if oecd_dir.exists() else False
    if not has_naq_gdp:
        report["missing"].extend([
            "oecd:NAQ_GDP (quarterly real GDP, panel)",
            "oecd:NAQ_government_consumption (quarterly govt consumption, panel)",
        ])
    else:
        report["present"].append("oecd:NAQ_*")
    # Narrative fiscal shocks:
    narrative_pubs = ["manual", "ramey_zubairy", "owyang_ramey_zubairy",
                      "guajardo_leigh_pescatori"]
    found_narrative = False
    for pub in narrative_pubs:
        d = REPO_ROOT / "data" / "vintages" / pub
        if d.exists() and any(d.glob("*.parquet")):
            report["present"].append(f"{pub}:*")
            found_narrative = True
            break
    if not found_narrative:
        report["missing"].append(
            "manual: Ramey-Zubairy defence-news / Guajardo-Leigh-Pescatori narrative consolidations"
        )
    return report


def state_dependent_ols_lp(
    g_growth: pd.Series,
    y_growth: pd.Series,
    zlb: pd.Series,
    horizons: list,
    g_y_ratio: float,
) -> dict:
    """US-only state-dependent OLS local projection.

    For each horizon h in `horizons`, estimate two regressions
    (ZLB sub-sample, normal sub-sample):

        sum_{i=0..h} y_growth_{t+i} = a + beta_h * shock_t + e

    Multiplier_h = beta_h / g_y_ratio  (Blanchard-Perotti scaling).
    The LP shock is the OLS innovation in g_growth (residual after
    regressing on its own lag and lagged y_growth) — a forecast-error
    proxy a la Auerbach-Gorodnichenko.
    """
    df = pd.concat({"dg": g_growth, "dy": y_growth, "zlb": zlb}, axis=1).dropna()
    df["dg_l1"] = df["dg"].shift(1)
    df["dy_l1"] = df["dy"].shift(1)
    df_s = df.dropna(subset=["dg", "dg_l1", "dy_l1"]).copy()
    X = np.column_stack([np.ones(len(df_s)), df_s["dg_l1"].values, df_s["dy_l1"].values])
    y_arr = df_s["dg"].values
    coef, *_ = np.linalg.lstsq(X, y_arr, rcond=None)
    df_s["shock"] = y_arr - X @ coef
    df = df.join(df_s["shock"], how="left")
    out: dict = {}
    for h in horizons:
        df[f"sum_dy_h{h}"] = df["dy"].rolling(h + 1).sum().shift(-h)
        for regime, mask in (("zlb", df["zlb"] == 1), ("normal", df["zlb"] == 0)):
            sub = df[mask & df["shock"].notna() & df[f"sum_dy_h{h}"].notna()]
            if len(sub) < 12:
                out[(h, regime)] = {"beta": None, "n": int(len(sub)), "multiplier": None}
                continue
            Xs = np.column_stack([np.ones(len(sub)), sub["shock"].values])
            ys = sub[f"sum_dy_h{h}"].values
            b, *_ = np.linalg.lstsq(Xs, ys, rcond=None)
            beta = float(b[1])
            mult = beta / g_y_ratio if g_y_ratio else None
            out[(h, regime)] = {"beta": beta, "n": int(len(sub)), "multiplier": mult}
    return out


def write_minimal_artifacts(verdict: str, diagnostics: dict) -> None:
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\nrun_utc: '{pd.Timestamp.utcnow().isoformat()}'\nvintages: {{}}\n"
    )
    (OUT_DIR / "chart_data.json").write_text(json.dumps({
        "kind": "result", "chart_id": f"{HID}/fig1",
        "title": "Data gap — replication cannot run",
        "type": "line", "series": [],
        "annotations": [{"type": "note", "label": verdict}],
        "sources": [], "permalink": f"/h/{HID}",
    }, indent=2) + "\n")
    pd.DataFrame([{
        "spec": "primary_panel_lp_iv",
        "term": "zlb_minus_normal_multiplier_h8",
        "estimate": float("nan"),
    }]).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    (OUT_DIR / "result_card.md").write_text(
        f"# Fiscal multipliers at the ZLB vs normal regime\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Summary\n\nReplication blocked on data availability. See diagnostics.json.\n"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------- METHOD_VALID gate: required panel inputs present? -------
    inventory = assess_required_panel_inputs()

    # ------- US-only diagnostic: load FRED quarterly inputs -------
    gdpc1_p = latest("fred", "GDPC1")
    fgexpnd_p = latest("fred", "FGEXPND")
    gdpdef_p = latest("fred", "GDPDEF")
    fedfunds_p = latest("fred", "FEDFUNDS")

    if not all([gdpc1_p, fgexpnd_p, gdpdef_p, fedfunds_p]):
        diag_only_missing = [
            f"fred:{s}" for s, p in [
                ("GDPC1", gdpc1_p), ("FGEXPND", fgexpnd_p),
                ("GDPDEF", gdpdef_p), ("FEDFUNDS", fedfunds_p),
            ] if p is None
        ]
        verdict = (
            f"inconclusive (data gap on quarterly OECD national accounts panel "
            f"+ Ramey-Zubairy / Guajardo-Leigh-Pescatori narrative fiscal-shock "
            f"series; US fallback also missing: {', '.join(diag_only_missing)})"
        )
        write_minimal_artifacts(verdict, {
            "verdict": verdict,
            "method_valid": False,
            "panel_inputs_missing": inventory["missing"],
            "panel_inputs_present": inventory["present"],
            "us_fallback_missing": diag_only_missing,
        })
        print(f"verdict: {verdict}")
        return

    manifest = {
        "real_gdp_us_quarterly": {
            "publisher": "fred", "series": "GDPC1",
            "vintage_file": str(gdpc1_p.relative_to(REPO_ROOT)),
            "sha256": sha256(gdpc1_p),
        },
        "federal_expenditures_us_quarterly": {
            "publisher": "fred", "series": "FGEXPND",
            "vintage_file": str(fgexpnd_p.relative_to(REPO_ROOT)),
            "sha256": sha256(fgexpnd_p),
        },
        "gdp_deflator_us_quarterly": {
            "publisher": "fred", "series": "GDPDEF",
            "vintage_file": str(gdpdef_p.relative_to(REPO_ROOT)),
            "sha256": sha256(gdpdef_p),
        },
        "fed_funds_rate_us_monthly": {
            "publisher": "fred", "series": "FEDFUNDS",
            "vintage_file": str(fedfunds_p.relative_to(REPO_ROOT)),
            "sha256": sha256(fedfunds_p),
        },
    }

    real_gdp = load_fred(gdpc1_p)         # billions chained 2017$, quarterly
    nom_fgexpnd = load_fred(fgexpnd_p)    # billions $, quarterly (NIPA)
    deflator = load_fred(gdpdef_p)        # index, quarterly
    ff_monthly = load_fred(fedfunds_p)    # %, monthly
    ff_quarterly = to_quarterly_mean(ff_monthly)

    # Real federal expenditures = nominal / (deflator/100)
    common_idx = nom_fgexpnd.index.intersection(deflator.index)
    real_fgexpnd = (nom_fgexpnd.loc[common_idx] / (deflator.loc[common_idx] / 100.0)).dropna()

    start = pd.Timestamp(f"{PANEL_PERIOD[0]}-01-01")
    end = pd.Timestamp(f"{PANEL_PERIOD[1]}-12-31")
    real_gdp = real_gdp.loc[start:end]
    real_fgexpnd = real_fgexpnd.loc[start:end]
    ff_quarterly = ff_quarterly.loc[start:end]

    # Drop COVID 2020Q2 per spec exclusion rules
    covid = pd.Timestamp("2020-04-01")
    real_gdp = real_gdp.drop(index=covid, errors="ignore")
    real_fgexpnd = real_fgexpnd.drop(index=covid, errors="ignore")
    ff_quarterly = ff_quarterly.drop(index=covid, errors="ignore")

    dy = np.log(real_gdp).diff()
    dg = np.log(real_fgexpnd).diff()
    zlb = (ff_quarterly <= ZLB_RATE_THRESHOLD).astype(int)

    common = real_gdp.index.intersection(real_fgexpnd.index)
    g_y_ratio = float((real_fgexpnd.loc[common] / real_gdp.loc[common]).mean())

    horizons = [4, 8, 12]
    lp = state_dependent_ols_lp(dg, dy, zlb, horizons, g_y_ratio)

    zlb_h = lp.get((PRIMARY_HORIZON, "zlb"), {})
    nor_h = lp.get((PRIMARY_HORIZON, "normal"), {})
    zlb_mult = zlb_h.get("multiplier")
    nor_mult = nor_h.get("multiplier")
    gap = (zlb_mult - nor_mult) if (zlb_mult is not None and nor_mult is not None) else None
    n_zlb_quarters = int(zlb.sum())
    n_normal_quarters = int((zlb == 0).sum())

    # ------- Verdict (always inconclusive: spec identification not feasible) -------
    if zlb_mult is not None and nor_mult is not None:
        diag_direction = (
            "in claimed direction (ZLB > normal)" if gap > 0
            else "against claimed direction (ZLB <= normal)"
        )
        verdict = (
            f"inconclusive (data gap on quarterly OECD national accounts panel "
            f"+ Ramey-Zubairy / Guajardo-Leigh-Pescatori narrative fiscal-shock "
            f"series; US-only OLS-LP diagnostic indicative only — h=8 ZLB "
            f"multiplier {zlb_mult:.2f} vs normal {nor_mult:.2f}, gap "
            f"{gap:+.2f}, {diag_direction}; threshold for SUPPORTED would have "
            f"been gap >= {PRIMARY_GAP_THRESHOLD:+.2f} on the panel LP-IV)."
        )
    else:
        verdict = (
            f"inconclusive (data gap on quarterly OECD national accounts panel "
            f"+ Ramey-Zubairy / Guajardo-Leigh-Pescatori narrative fiscal-shock "
            f"series; US-only fallback also under-identified at h={PRIMARY_HORIZON} "
            f"— ZLB n={zlb_h.get('n')}, normal n={nor_h.get('n')})."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid_for_spec": False,
        "panel_inputs_missing": inventory["missing"],
        "panel_inputs_present": inventory["present"],
        "us_only_diagnostic": {
            "method": "state_dependent_OLS_local_projection_us_only",
            "sample_period": [str(start.date()), str(end.date())],
            "zlb_rate_threshold_pct": ZLB_RATE_THRESHOLD,
            "n_quarters_zlb": n_zlb_quarters,
            "n_quarters_normal": n_normal_quarters,
            "g_over_y_steady_state": g_y_ratio,
            "primary_horizon_quarters": PRIMARY_HORIZON,
            "primary_gap_threshold": PRIMARY_GAP_THRESHOLD,
            "horizons": {
                str(h): {
                    "zlb_beta": lp[(h, "zlb")].get("beta"),
                    "zlb_multiplier": lp[(h, "zlb")].get("multiplier"),
                    "zlb_n": lp[(h, "zlb")].get("n"),
                    "normal_beta": lp[(h, "normal")].get("beta"),
                    "normal_multiplier": lp[(h, "normal")].get("multiplier"),
                    "normal_n": lp[(h, "normal")].get("n"),
                    "gap": (
                        lp[(h, "zlb")]["multiplier"] - lp[(h, "normal")]["multiplier"]
                    ) if (
                        lp[(h, "zlb")].get("multiplier") is not None
                        and lp[(h, "normal")].get("multiplier") is not None
                    ) else None,
                }
                for h in horizons
            },
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ------- Chart: cumulative US LP responses by regime, h=0..12 -------
    chart_horizons = list(range(0, 13))
    lp_chart = state_dependent_ols_lp(dg, dy, zlb, chart_horizons, g_y_ratio)
    series = []
    for regime, color in (("zlb", "#E15759"), ("normal", "#4E79A7")):
        pts = []
        for h in chart_horizons:
            m = lp_chart.get((h, regime), {}).get("multiplier")
            if m is not None:
                pts.append({"x": h, "y": float(m)})
        if pts:
            series.append({
                "id": regime,
                "label": "ZLB regime (FFR <= 0.25%)" if regime == "zlb" else "Normal regime (FFR > 0.25%)",
                "color": color,
                "treated": (regime == "zlb"),
                "points": pts,
            })

    if zlb_mult is not None and nor_mult is not None:
        subtitle = (
            f"US OLS LP, FRED quarterly 1995-2021 ex 2020Q2 - "
            f"ZLB n={n_zlb_quarters}q, normal n={n_normal_quarters}q - "
            f"h=8: ZLB={zlb_mult:.2f}, normal={nor_mult:.2f}, gap={gap:+.2f}"
        )
    else:
        subtitle = "Insufficient regime sub-sample to identify h=8 multiplier"

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "US-only state-dependent local projection - fiscal multiplier by regime (DIAGNOSTIC ONLY)",
        "subtitle": subtitle,
        "type": "line",
        "x_axis": {"label": "Horizon (quarters)", "type": "linear"},
        "y_axis": {"label": "Cumulative multiplier", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": PRIMARY_HORIZON, "label": "Primary horizon (h=8)"},
            {"type": "note", "label": (
                "DIAGNOSTIC ONLY - spec calls for OECD-panel LP-IV with "
                "narrative shocks; that identification is not feasible on the "
                "data on disk. Verdict is inconclusive regardless of the "
                "US-only OLS LP."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ------- Coefficients table -------
    rows = [{
        "spec": "primary_panel_lp_iv",
        "term": "zlb_minus_normal_multiplier_h8",
        "estimate": float("nan"),
    }]
    for h in horizons:
        for regime in ("zlb", "normal"):
            rec = lp[(h, regime)]
            rows.append({
                "spec": f"diagnostic_us_ols_lp_{regime}",
                "term": f"multiplier_h{h}",
                "estimate": rec["multiplier"] if rec["multiplier"] is not None else float("nan"),
            })
        if (lp[(h, "zlb")]["multiplier"] is not None
                and lp[(h, "normal")]["multiplier"] is not None):
            rows.append({
                "spec": "diagnostic_us_ols_lp_gap",
                "term": f"zlb_minus_normal_h{h}",
                "estimate": lp[(h, "zlb")]["multiplier"] - lp[(h, "normal")]["multiplier"],
            })
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ------- Manifest -------
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

    # ------- Result card -------
    fmt_m = lambda x: f"{x:.2f}" if x is not None else "n/a"
    fmt_g = lambda a, b: f"{(a - b):+.2f}" if (a is not None and b is not None) else "n/a"

    card_lines = [
        "# Fiscal multipliers at the ZLB vs normal regime",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "The spec calls for a state-dependent LP-IV across an OECD panel of "
        f"{len(SPEC_COUNTRIES)} countries (1995-2021), instrumenting "
        "government-spending innovations with the Ramey-Zubairy defence-news "
        "series and the Guajardo-Leigh-Pescatori narrative consolidations. "
        "Neither the quarterly OECD national-accounts panel (real GDP, "
        "government consumption) nor the narrative fiscal-shock series are on "
        "disk under any publisher. The pre-registered identification therefore "
        "cannot be run.",
        "",
        "Missing inputs flagged by `assess_required_panel_inputs()`:",
        "",
    ] + [f"- {m}" for m in inventory["missing"]] + [
        "",
        "## Informative diagnostic - US-only OLS LP",
        "",
        "To keep the run artefact-complete, this script also runs a US-only "
        "downgraded state-dependent OLS local projection on the FRED quarterly "
        "data (GDPC1, FGEXPND deflated by GDPDEF, FEDFUNDS for the ZLB "
        f"indicator). Sample window 1995-2021 ex 2020Q2 ({n_zlb_quarters} ZLB "
        f"quarters, {n_normal_quarters} normal quarters). The shock is the OLS "
        "innovation of dlog real federal expenditures after lag-1 controls "
        "(Auerbach-Gorodnichenko forecast-error proxy). Multiplier scaled by "
        f"steady-state G/Y = {g_y_ratio:.3f}. **This does not adjudicate the "
        "spec's panel-LP-IV claim** and is reported only to indicate whether "
        "the US signal points toward or away from the New-Keynesian prediction.",
        "",
    ]
    for h in horizons:
        z = lp[(h, "zlb")]
        n_ = lp[(h, "normal")]
        card_lines.append(
            f"- h={h}: ZLB multiplier {fmt_m(z['multiplier'])} (n={z['n']}), "
            f"normal multiplier {fmt_m(n_['multiplier'])} (n={n_['n']}), "
            f"gap {fmt_g(z['multiplier'], n_['multiplier'])}."
        )
    card_lines += [
        "",
        f"At the spec's primary horizon h={PRIMARY_HORIZON}, the US-only "
        f"diagnostic gap is "
        f"{fmt_g(zlb_mult, nor_mult)} "
        f"(threshold for SUPPORTED on the panel LP-IV would have been "
        f">= +{PRIMARY_GAP_THRESHOLD:.2f}).",
        "",
        "## Method (pre-registered, blocked)",
        "",
        "1. Quarterly OECD-panel real GDP and government consumption "
        "(OECD NAQ_GDP / quarterly national accounts).",
        "2. Country-quarter ZLB indicator constructed from short-rate "
        f"<= {ZLB_RATE_THRESHOLD:.2f}%.",
        "3. Narrative fiscal-shock series as instruments (Ramey-Zubairy "
        "defence-news; Guajardo-Leigh-Pescatori).",
        "4. State-dependent local-projection IV a la Ramey-Zubairy / "
        "Auerbach-Gorodnichenko, country-clustered SEs, country+year FE.",
        "5. Cumulative multiplier at h=8 quarters compared across the ZLB "
        f"and normal regimes; SUPPORTED if (ZLB - normal) >= +{PRIMARY_GAP_THRESHOLD:.2f}.",
        "",
        "## Data",
        "",
        "Available (US-only diagnostic):",
        "- fred:GDPC1 (real GDP, quarterly)",
        "- fred:FGEXPND (federal government expenditures, quarterly)",
        "- fred:GDPDEF (GDP deflator, quarterly)",
        "- fred:FEDFUNDS (effective federal funds rate, monthly to quarterly mean)",
        "",
        "Required for the spec but missing on disk:",
    ] + [f"- {m}" for m in inventory["missing"]] + [
        "",
        "Fetcher backlog:",
        "- OECD quarterly national accounts (NAQ_GDP, NAQ_government_consumption) "
        "for the 21-country panel.",
        "- A `manual` publisher hosting the Ramey-Zubairy defence-news and "
        "Owyang-Ramey-Zubairy international-panel news shocks, plus the "
        "Guajardo-Leigh-Pescatori narrative consolidations.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card_lines) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
