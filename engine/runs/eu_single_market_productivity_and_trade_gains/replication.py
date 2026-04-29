#!/usr/bin/env python3
"""Replication — EU Single Market 1993: productivity and trade gains.

Spec: hypotheses/growth/eu_single_market_productivity_and_trade_gains.yaml
Position-claim: ordoliberal #4 (school predicts: supported)

Tests whether the 1993 EU Single Market produced measurable post-1993
trade and productivity gains for EU-12 vs non-EU OECD comparators,
consistent with the Ordoliberal claim that rules-based market integration
plus supranational competition enforcement raises welfare.

DESIGN: pre/post DiD comparison around the 1993 event date.

  Treated:    EU-12 (DEU, FRA, ITA, ESP, NLD, BEL, GBR, IRL, DNK, GRC, PRT, LUX)
  Controls:   non-EU OECD comparators (USA, JPN, CAN, AUS, NOR, CHE)
  Period:     1980-2010 (per spec; capped pre-GFC tail)
  Pre window: 1980-1992 ; Post window: 1994-2010

PRIMARY 1 (productivity proxy): DiD on log real GDP per capita PPP,
            EU-12 vs non-EU OECD. SUPPORTED if mean post-1993 EU-12
            log-PPP minus non-EU OECD log-PPP exceeds the pre-1993
            mean by at least +2.0 log points (i.e. EU-12 closed the
            gap to non-EU OECD by ≥2%, or pulled ahead).
PRIMARY 2 (trade gain): DiD on trade openness (NE.TRD.GNFS.ZS, %GDP),
            EU-12 vs non-EU OECD. SUPPORTED if EU-12 trade openness
            rose post-1993 by at least +5 percentage points more than
            non-EU OECD did.

Hypothesis is SUPPORTED only if BOTH primaries hold. REFUTED if both
fail (DiDs at/below zero on both). PARTIAL otherwise.

INFORMATIVE: PWT rtfpna (manufacturing TFP) post-1993 EU-12 vs control
mean trajectory, reported but not gating.

METHOD_VALID: at least 10 of 12 EU-12 countries with usable WDI
trade-openness data, and 4 of 6 non-EU OECD comparators with same.
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
HID = "eu_single_market_productivity_and_trade_gains"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample (from spec.sample.countries)
TREATED = ["DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "GBR", "IRL", "DNK", "GRC", "PRT", "LUX"]
CONTROLS = ["USA", "JPN", "CAN", "AUS", "NOR", "CHE"]
ALL_COUNTRIES = TREATED + CONTROLS

PERIOD = (1980, 2010)
EVENT_YEAR = 1993
PRE_WIN = (1980, 1992)
POST_WIN = (1994, 2010)

# Dispositive thresholds
GDP_DID_THRESHOLD_LOG = 0.02      # +2 log points
TRADE_DID_THRESHOLD_PP = 5.0       # +5 percentage points
MIN_TREATED_COVERAGE = 10          # of 12 EU-12
MIN_CONTROL_COVERAGE = 4           # of 6 non-EU OECD


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
    """Normalise parquet to (country_iso3, year, value) rows."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
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


def did_country_means(df: pd.DataFrame, value_col: str = "value") -> dict:
    """Compute per-country pre/post means for the given value column,
    then the (treated - control) DiD on means.
    """
    pre = df[df["year"].between(PRE_WIN[0], PRE_WIN[1])]
    post = df[df["year"].between(POST_WIN[0], POST_WIN[1])]

    pre_means = pre.groupby("country_iso3")[value_col].mean()
    post_means = post.groupby("country_iso3")[value_col].mean()

    # Country must have both pre and post observations to enter the DiD
    valid = pre_means.index.intersection(post_means.index)
    deltas = (post_means.loc[valid] - pre_means.loc[valid])

    treated_deltas = deltas[deltas.index.isin(TREATED)]
    control_deltas = deltas[deltas.index.isin(CONTROLS)]

    treated_delta_mean = float(treated_deltas.mean()) if len(treated_deltas) else float("nan")
    control_delta_mean = float(control_deltas.mean()) if len(control_deltas) else float("nan")

    return {
        "treated_pre_mean": float(pre_means.loc[pre_means.index.isin(TREATED)].mean()),
        "treated_post_mean": float(post_means.loc[post_means.index.isin(TREATED)].mean()),
        "control_pre_mean": float(pre_means.loc[pre_means.index.isin(CONTROLS)].mean()),
        "control_post_mean": float(post_means.loc[post_means.index.isin(CONTROLS)].mean()),
        "treated_delta_mean": treated_delta_mean,
        "control_delta_mean": control_delta_mean,
        "did": treated_delta_mean - control_delta_mean,
        "n_treated_with_both": int(treated_deltas.shape[0]),
        "n_control_with_both": int(control_deltas.shape[0]),
        "treated_country_deltas": {k: float(v) for k, v in treated_deltas.items()},
        "control_country_deltas": {k: float(v) for k, v in control_deltas.items()},
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----- Load series -----
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    trade_path = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    pop_path = latest("world_bank_wdi", "SP.POP.TOTL")
    tfp_path = latest("pwt", "rtfpna")

    manifest = {
        "gdp_pc_ppp_kd": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.PP.KD",
            "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdppc_path),
        },
        "trade_pct_gdp": {
            "publisher": "world_bank_wdi",
            "series": "NE.TRD.GNFS.ZS",
            "vintage_file": str(trade_path.relative_to(REPO_ROOT)),
            "sha256": sha256(trade_path),
        },
        "population": {
            "publisher": "world_bank_wdi",
            "series": "SP.POP.TOTL",
            "vintage_file": str(pop_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pop_path),
        },
        "pwt_rtfpna": {
            "publisher": "pwt",
            "series": "rtfpna",
            "vintage_file": str(tfp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(tfp_path),
        },
    }

    gdppc = load_long(gdppc_path)
    trade = load_long(trade_path)
    tfp = load_long(tfp_path)

    # Restrict to sample countries and period
    def restrict(df):
        return df[
            df["country_iso3"].isin(ALL_COUNTRIES)
            & df["year"].between(PERIOD[0], PERIOD[1])
        ].copy()

    gdppc = restrict(gdppc)
    trade = restrict(trade)
    tfp = restrict(tfp)

    # Log-transform GDP PC PPP
    gdppc["log_value"] = np.log(gdppc["value"])
    gdppc_did_input = gdppc[["country_iso3", "year", "log_value"]].rename(
        columns={"log_value": "value"}
    )

    # ----- PRIMARY 1: log GDP PC PPP DiD -----
    gdp_did = did_country_means(gdppc_did_input)

    # ----- PRIMARY 2: trade openness DiD -----
    trade_did = did_country_means(trade)

    # ----- INFORMATIVE: TFP -----
    tfp_did = did_country_means(tfp)

    # ----- METHOD_VALID gates -----
    # Use trade-openness coverage as the binding constraint (PWT rtfpna may
    # have weaker coverage for some countries; we report but don't gate on it).
    method_valid_treated = trade_did["n_treated_with_both"] >= MIN_TREATED_COVERAGE
    method_valid_control = trade_did["n_control_with_both"] >= MIN_CONTROL_COVERAGE
    method_valid = method_valid_treated and method_valid_control

    # ----- Verdict logic -----
    p1_pass = gdp_did["did"] >= GDP_DID_THRESHOLD_LOG
    p2_pass = trade_did["did"] >= TRADE_DID_THRESHOLD_PP

    p1_fail_neg = gdp_did["did"] <= 0.0
    p2_fail_neg = trade_did["did"] <= 0.0

    if not method_valid:
        verdict = (
            f"inconclusive — coverage shortfall: "
            f"{trade_did['n_treated_with_both']}/12 EU-12 and "
            f"{trade_did['n_control_with_both']}/6 non-EU OECD have both "
            f"pre- and post-1993 trade-openness data (requires "
            f"{MIN_TREATED_COVERAGE} and {MIN_CONTROL_COVERAGE})."
        )
    elif p1_pass and p2_pass:
        verdict = (
            f"SUPPORTED — EU-12 vs non-EU OECD DiD around 1993: "
            f"log GDP PC PPP +{gdp_did['did']*100:.2f} log pp "
            f"(threshold +{GDP_DID_THRESHOLD_LOG*100:.1f}) AND "
            f"trade openness +{trade_did['did']:.2f} pp "
            f"(threshold +{TRADE_DID_THRESHOLD_PP:.1f})."
        )
    elif p1_fail_neg and p2_fail_neg:
        verdict = (
            f"refuted — Both primaries failed in the wrong direction. "
            f"EU-12 vs non-EU OECD DiD: log GDP PC PPP "
            f"{gdp_did['did']*100:+.2f} log pp; trade openness "
            f"{trade_did['did']:+.2f} pp. EU-12 did NOT pull ahead "
            f"on either dimension after 1993."
        )
    else:
        which_pass = []
        which_fail = []
        if p1_pass:
            which_pass.append(f"productivity proxy (log GDP PC PPP DiD = {gdp_did['did']*100:+.2f} pp)")
        else:
            which_fail.append(f"productivity proxy (DiD = {gdp_did['did']*100:+.2f} pp, threshold +{GDP_DID_THRESHOLD_LOG*100:.1f})")
        if p2_pass:
            which_pass.append(f"trade openness (DiD = {trade_did['did']:+.2f} pp)")
        else:
            which_fail.append(f"trade openness (DiD = {trade_did['did']:+.2f} pp, threshold +{TRADE_DID_THRESHOLD_PP:.1f})")
        verdict = (
            f"partial — One primary held, the other did not. "
            f"Held: {', '.join(which_pass) if which_pass else 'none'}. "
            f"Missed: {', '.join(which_fail) if which_fail else 'none'}."
        )

    # ----- Diagnostics -----
    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "primary1_log_gdp_pc_ppp_did_pass": p1_pass,
        "primary2_trade_openness_did_pass": p2_pass,
        "thresholds": {
            "gdp_pc_ppp_did_log": GDP_DID_THRESHOLD_LOG,
            "trade_openness_did_pp": TRADE_DID_THRESHOLD_PP,
            "min_treated_coverage": MIN_TREATED_COVERAGE,
            "min_control_coverage": MIN_CONTROL_COVERAGE,
        },
        "gdp_pc_ppp_did": gdp_did,
        "trade_openness_did": trade_did,
        "tfp_rtfpna_did_informative": tfp_did,
        "design": {
            "treated": TREATED,
            "controls": CONTROLS,
            "event_year": EVENT_YEAR,
            "pre_window": list(PRE_WIN),
            "post_window": list(POST_WIN),
            "period": list(PERIOD),
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ----- Chart: trade openness trajectories, EU-12 mean vs non-EU OECD mean -----
    palette = {
        "EU12_MEAN": "#003399",  # EU blue
        "NONEU_MEAN": "#C8102E",  # contrast red
    }

    # Build group means by year (trade openness) for the chart
    yearly_treated = (
        trade[trade["country_iso3"].isin(TREATED)]
        .groupby("year")["value"].mean().reset_index()
        .sort_values("year")
    )
    yearly_control = (
        trade[trade["country_iso3"].isin(CONTROLS)]
        .groupby("year")["value"].mean().reset_index()
        .sort_values("year")
    )

    series = [
        {
            "id": "EU12_MEAN",
            "label": "EU-12 mean (treated)",
            "color": palette["EU12_MEAN"],
            "treated": True,
            "points": [
                {"x": int(r.year), "y": float(r.value)}
                for r in yearly_treated.itertuples()
            ],
        },
        {
            "id": "NONEU_OECD_MEAN",
            "label": "Non-EU OECD mean (control)",
            "color": palette["NONEU_MEAN"],
            "treated": False,
            "points": [
                {"x": int(r.year), "y": float(r.value)}
                for r in yearly_control.itertuples()
            ],
        },
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Trade openness around the 1993 EU Single Market",
        "subtitle": (
            f"EU-12 vs non-EU OECD; trade DiD = {trade_did['did']:+.2f} pp; "
            f"log GDP PC PPP DiD = {gdp_did['did']*100:+.2f} log pp."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Trade openness (% of GDP)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "vertical_line",
                "x": EVENT_YEAR,
                "label": "EU Single Market activation (1993)",
            },
            {
                "type": "note",
                "label": (
                    f"DiD = (EU12_post - EU12_pre) - (NonEU_post - NonEU_pre). "
                    f"Pre = {PRE_WIN[0]}-{PRE_WIN[1]}, Post = {POST_WIN[0]}-{POST_WIN[1]}."
                ),
            },
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ----- Coefficients table -----
    pd.DataFrame(
        [
            {"spec": "primary1_gdp_pc_ppp", "term": "did_log", "estimate": gdp_did["did"]},
            {"spec": "primary1_gdp_pc_ppp", "term": "treated_delta_log", "estimate": gdp_did["treated_delta_mean"]},
            {"spec": "primary1_gdp_pc_ppp", "term": "control_delta_log", "estimate": gdp_did["control_delta_mean"]},
            {"spec": "primary2_trade_openness", "term": "did_pp", "estimate": trade_did["did"]},
            {"spec": "primary2_trade_openness", "term": "treated_delta_pp", "estimate": trade_did["treated_delta_mean"]},
            {"spec": "primary2_trade_openness", "term": "control_delta_pp", "estimate": trade_did["control_delta_mean"]},
            {"spec": "informative_tfp_rtfpna", "term": "did_index", "estimate": tfp_did["did"]},
        ]
    ).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ----- Manifest -----
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

    # ----- Result card -----
    card = [
        f"# EU Single Market 1993 — productivity and trade gains",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- **Primary 1 (productivity proxy, log GDP PC PPP DiD):** "
        f"{gdp_did['did']*100:+.2f} log pp "
        f"(threshold ≥ +{GDP_DID_THRESHOLD_LOG*100:.1f} log pp). "
        f"{'PASS' if p1_pass else 'FAIL'}.",
        f"  - EU-12 mean delta (post − pre): {gdp_did['treated_delta_mean']*100:+.2f} log pp "
        f"({gdp_did['n_treated_with_both']} of 12 countries).",
        f"  - Non-EU OECD mean delta (post − pre): {gdp_did['control_delta_mean']*100:+.2f} log pp "
        f"({gdp_did['n_control_with_both']} of 6 countries).",
        "",
        f"- **Primary 2 (trade openness DiD):** {trade_did['did']:+.2f} pp "
        f"(threshold ≥ +{TRADE_DID_THRESHOLD_PP:.1f} pp). "
        f"{'PASS' if p2_pass else 'FAIL'}.",
        f"  - EU-12 mean delta (post − pre): {trade_did['treated_delta_mean']:+.2f} pp.",
        f"  - Non-EU OECD mean delta (post − pre): {trade_did['control_delta_mean']:+.2f} pp.",
        "",
        f"- **Informative (PWT rtfpna DiD):** {tfp_did['did']:+.4f} index points "
        f"(no gating threshold; reported for context).",
        "",
        "## Method",
        "",
        f"Pre/post DiD on country means around the 1993 Single Market activation.",
        f"",
        f"- Treated (EU-12, n=12): {', '.join(TREATED)}",
        f"- Controls (non-EU OECD, n=6): {', '.join(CONTROLS)}",
        f"- Pre window: {PRE_WIN[0]}-{PRE_WIN[1]}; Post window: {POST_WIN[0]}-{POST_WIN[1]}.",
        f"- DiD = (EU-12 post mean − EU-12 pre mean) − (non-EU OECD post mean − non-EU OECD pre mean).",
        "",
        "Outcomes:",
        "1. log real GDP per capita PPP (WDI NY.GDP.PCAP.PP.KD) — productivity proxy.",
        "2. Trade openness (WDI NE.TRD.GNFS.ZS, % of GDP) — trade gain.",
        "3. PWT rtfpna (TFP, manufacturing) — informative only.",
        "",
        "Note: the spec's intra-EU trade share series (eurostat:ext_lt_intratrd) "
        "is not on disk, so total trade openness from WDI substitutes as the "
        "trade-gain primary. This is conservative for the Ordoliberal claim: "
        "if Single Market deepens *intra-EU* trade specifically, total openness "
        "could rise OR fall (substitution from extra-EU to intra-EU trade). "
        "The DiD on total openness still captures whether the EU bloc became "
        "more trade-intensive overall vs non-EU OECD.",
        "",
        "## Caveats / non-identifying confounds",
        "",
        "- 1993 coincides with the broader Maastricht / EMU preparatory "
        "  process; the design cannot separate Single Market from EMU effects.",
        "- The post-1995 WTO formation and Eastern enlargement effects from "
        "  1995 onward (AUT/SWE/FIN joined) are not separated; AUT/SWE/FIN "
        "  are NOT in the EU-12 treated set so this contaminates the "
        "  control comparison only mildly via spillovers, not directly.",
        "- A simple two-period DiD on means is more transparent than an "
        "  event-study with leads/lags but discards the within-window "
        "  trajectory; v2 should add a year-by-year event-study spec.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:NY.GDP.PCAP.PP.KD",
        f"- world_bank_wdi:NE.TRD.GNFS.ZS",
        f"- world_bank_wdi:SP.POP.TOTL",
        f"- pwt:rtfpna",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
