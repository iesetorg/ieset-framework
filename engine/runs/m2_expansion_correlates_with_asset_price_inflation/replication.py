#!/usr/bin/env python3
"""Replication — M2 expansion correlates with asset price inflation.

Spec: hypotheses/monetary/m2_expansion_correlates_with_asset_price_inflation.yaml v1
Position-claims: austrian #0, chicago_monetarism #1, marxian #2, post_keynesian #0
                 (all four schools predict: supported)

Tests the panel claim that broad-money (M2/M3) growth co-moves with — and
modestly leads — real asset-price returns in major developed economies
post-2008.

PRIMARY (dispositive): the hypothesis is SUPPORTED if BOTH
  (1) at least 6 of 10 countries have a non-negative lag-1 correlation
      between annual M2-growth(t-1) and real equity-total-return(t)
      OR real-housing-return(t) (asset-class disjunction is allowed by
      the spec's asymmetry clause), AND
  (2) the cross-country panel mean of those lag-1 correlations is > 0
      for either equities or housing (the "positive on average" leg).
REFUTED if both legs fail in BOTH asset classes.
PARTIAL otherwise (e.g. one asset class supported, the other not).

INFORMATIVE (does not gate): contemporaneous correlations and the
sign-distribution across countries are reported in diagnostics.

METHOD_VALID: JST Macrohistory has money + asset returns for all 10
spec countries 2008-2020 (CAN missing eq_tr and housing_tr — that
country drops from the asset-correlation tally but is kept for the
M2/house-price-nominal correlation). The 2021-2025 tail of the spec
period is not yet covered by JST; this is noted as a coverage gap
rather than a refutation.

Data:
  - jst:money       — broad money (M2/M3) annual level
  - jst:eq_tr       — nominal equity total return
  - jst:housing_tr  — nominal housing total return
  - jst:cpi         — CPI level (used to convert nominal returns to real)
  - jst:hpnom       — nominal house price index (CAN fallback for housing)
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
HID = "m2_expansion_correlates_with_asset_price_inflation"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from spec.sample.countries
COUNTRIES = ["USA", "GBR", "JPN", "AUS", "CAN", "DEU", "FRA", "ITA", "ESP", "NLD"]
SPEC_PERIOD = (2008, 2025)
# Effective period bounded by JST availability (annual through 2020).
DATA_PERIOD = (2008, 2020)

# Falsification thresholds — sharpened from spec.falsification.threshold
MIN_COUNTRIES_NONNEG_LAG = 6  # >= 6 of 10 countries lag-1 corr non-negative
MIN_PANEL_MEAN_LAG_CORR = 0.0  # panel mean lag-1 corr > 0 in at least one asset class


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


def load_jst_panel(path: Path) -> pd.DataFrame:
    """JST Macrohistory comes as a wide panel keyed on (country_iso3, year)."""
    df = pq.read_table(path).to_pandas()
    if "country_iso3" not in df.columns or "year" not in df.columns:
        raise ValueError(f"{path}: missing country_iso3/year columns")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    return df


def real_yoy(level: pd.Series, cpi: pd.Series) -> pd.Series:
    """Real YoY growth: (level_t / level_{t-1}) / (cpi_t / cpi_{t-1}) - 1."""
    nom = level / level.shift(1) - 1.0
    inf = cpi / cpi.shift(1) - 1.0
    return (1.0 + nom) / (1.0 + inf) - 1.0


def real_total_return(tr_nom: pd.Series, cpi: pd.Series) -> pd.Series:
    """JST eq_tr/housing_tr are gross-return ratios (1+r). Deflate by CPI YoY."""
    inf = cpi / cpi.shift(1) - 1.0
    return (tr_nom) / (1.0 + inf) - 1.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # JST 'money' file already contains all needed columns (it's the wide JST_R6
    # macrohistory panel split by metric; the 'money' export has the full row
    # of macrohistory variables). Pin a single vintage of the long-form file.
    jst_path = latest("jst", "money")

    manifest = {
        "jst_macrohistory": {
            "publisher": "jst",
            "series": "money",
            "vintage_file": str(jst_path.relative_to(REPO_ROOT)),
            "sha256": sha256(jst_path),
        },
    }

    df = load_jst_panel(jst_path)
    df = df[df["country_iso3"].isin(COUNTRIES)].copy()
    df = df[df["year"].between(DATA_PERIOD[0] - 1, DATA_PERIOD[1])]
    df = df.sort_values(["country_iso3", "year"]).reset_index(drop=True)

    # ---------- Build per-country annual series ----------
    rows = []
    for c in COUNTRIES:
        g = df[df["country_iso3"] == c].set_index("year").sort_index()
        if g.empty:
            continue
        m2_growth = np.log(g["money"]).diff()
        # Real equity total return (gross 1+r in JST eq_tr; deflate by CPI)
        cpi = g["cpi"]
        eq_real = real_total_return(g["eq_tr"], cpi) if g["eq_tr"].notna().any() else pd.Series(dtype=float)
        # Real housing total return — fallback to nominal house price if missing
        if g["housing_tr"].notna().any():
            house_real = real_total_return(g["housing_tr"], cpi)
        else:
            house_real = real_yoy(g["hpnom"], cpi)
        for y in g.index:
            rows.append({
                "country_iso3": c,
                "year": int(y),
                "m2_growth": float(m2_growth.loc[y]) if y in m2_growth.index and pd.notna(m2_growth.loc[y]) else np.nan,
                "equity_real_return": float(eq_real.loc[y]) if y in eq_real.index and pd.notna(eq_real.loc[y]) else np.nan,
                "housing_real_return": float(house_real.loc[y]) if y in house_real.index and pd.notna(house_real.loc[y]) else np.nan,
            })
    panel = pd.DataFrame(rows)
    panel = panel[panel["year"].between(DATA_PERIOD[0], DATA_PERIOD[1])].copy()

    # ---------- Per-country lag-1 correlations: M2_growth(t-1) vs return(t) ----------
    eq_lag_corr = {}
    eq_contemp_corr = {}
    house_lag_corr = {}
    house_contemp_corr = {}

    for c in COUNTRIES:
        g = panel[panel["country_iso3"] == c].set_index("year").sort_index()
        if g.empty:
            continue
        m2_lag = g["m2_growth"].shift(1)

        # Equities
        if g["equity_real_return"].notna().sum() >= 5 and m2_lag.notna().sum() >= 5:
            both = pd.concat([m2_lag, g["equity_real_return"]], axis=1).dropna()
            if len(both) >= 5:
                eq_lag_corr[c] = float(both.iloc[:, 0].corr(both.iloc[:, 1]))
            both_c = pd.concat([g["m2_growth"], g["equity_real_return"]], axis=1).dropna()
            if len(both_c) >= 5:
                eq_contemp_corr[c] = float(both_c.iloc[:, 0].corr(both_c.iloc[:, 1]))

        # Housing
        if g["housing_real_return"].notna().sum() >= 5 and m2_lag.notna().sum() >= 5:
            both = pd.concat([m2_lag, g["housing_real_return"]], axis=1).dropna()
            if len(both) >= 5:
                house_lag_corr[c] = float(both.iloc[:, 0].corr(both.iloc[:, 1]))
            both_c = pd.concat([g["m2_growth"], g["housing_real_return"]], axis=1).dropna()
            if len(both_c) >= 5:
                house_contemp_corr[c] = float(both_c.iloc[:, 0].corr(both_c.iloc[:, 1]))

    # ---------- Test the falsification thresholds ----------
    eq_n_nonneg = sum(1 for v in eq_lag_corr.values() if v >= 0)
    eq_n_total = len(eq_lag_corr)
    eq_panel_mean_lag = float(np.mean(list(eq_lag_corr.values()))) if eq_lag_corr else float("nan")

    house_n_nonneg = sum(1 for v in house_lag_corr.values() if v >= 0)
    house_n_total = len(house_lag_corr)
    house_panel_mean_lag = float(np.mean(list(house_lag_corr.values()))) if house_lag_corr else float("nan")

    eq_supported = (
        eq_n_nonneg >= MIN_COUNTRIES_NONNEG_LAG
        and not np.isnan(eq_panel_mean_lag)
        and eq_panel_mean_lag > MIN_PANEL_MEAN_LAG_CORR
    )
    house_supported = (
        house_n_nonneg >= MIN_COUNTRIES_NONNEG_LAG
        and not np.isnan(house_panel_mean_lag)
        and house_panel_mean_lag > MIN_PANEL_MEAN_LAG_CORR
    )
    any_supported = eq_supported or house_supported
    both_supported = eq_supported and house_supported
    both_failed = (not eq_supported) and (not house_supported)

    # Verdict
    if both_supported:
        verdict = (
            f"SUPPORTED — Lag-1 M2/asset-return correlation positive in both asset "
            f"classes across the panel 2008-2020. Equities: {eq_n_nonneg}/{eq_n_total} "
            f"countries non-negative, panel mean = {eq_panel_mean_lag:+.3f}. "
            f"Housing: {house_n_nonneg}/{house_n_total} non-negative, panel mean = "
            f"{house_panel_mean_lag:+.3f}. Sample period truncated at 2020 (JST "
            f"vintage); 2021-2025 not covered by current data."
        )
    elif any_supported:
        which = "equities" if eq_supported else "housing"
        other = "housing" if eq_supported else "equities"
        verdict = (
            f"partial — {which.capitalize()} leg met the >=6/10 + positive-mean "
            f"thresholds but {other} did not. Equities: {eq_n_nonneg}/{eq_n_total} "
            f"non-negative, mean lag-1 corr = {eq_panel_mean_lag:+.3f}. "
            f"Housing: {house_n_nonneg}/{house_n_total} non-negative, mean = "
            f"{house_panel_mean_lag:+.3f}. Spec's asymmetry clause is consistent "
            f"with this outcome but the symmetric-claim formulation is not "
            f"fully supported."
        )
    elif both_failed:
        verdict = (
            f"refuted — Neither asset class met the lag-1 thresholds. "
            f"Equities: {eq_n_nonneg}/{eq_n_total} non-negative, mean = "
            f"{eq_panel_mean_lag:+.3f}. Housing: {house_n_nonneg}/{house_n_total} "
            f"non-negative, mean = {house_panel_mean_lag:+.3f}. The post-2008 "
            f"developed-economy panel does not show the M2-leads-assets pattern "
            f"on annual JST data through 2020."
        )
    else:
        verdict = (
            f"inconclusive — pattern unclear. eq mean={eq_panel_mean_lag:+.3f}, "
            f"house mean={house_panel_mean_lag:+.3f}."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": both_supported,
        "any_pass": any_supported,
        "equity_supported": eq_supported,
        "housing_supported": house_supported,
        "thresholds": {
            "min_countries_nonneg_lag": MIN_COUNTRIES_NONNEG_LAG,
            "min_panel_mean_lag_corr": MIN_PANEL_MEAN_LAG_CORR,
        },
        "equity": {
            "n_countries_nonneg_lag1": eq_n_nonneg,
            "n_countries_with_data": eq_n_total,
            "panel_mean_lag1_corr": eq_panel_mean_lag,
            "panel_mean_contemp_corr": float(np.mean(list(eq_contemp_corr.values())))
                if eq_contemp_corr else float("nan"),
            "country_lag1_corr": eq_lag_corr,
            "country_contemp_corr": eq_contemp_corr,
        },
        "housing": {
            "n_countries_nonneg_lag1": house_n_nonneg,
            "n_countries_with_data": house_n_total,
            "panel_mean_lag1_corr": house_panel_mean_lag,
            "panel_mean_contemp_corr": float(np.mean(list(house_contemp_corr.values())))
                if house_contemp_corr else float("nan"),
            "country_lag1_corr": house_lag_corr,
            "country_contemp_corr": house_contemp_corr,
        },
        "data_period": list(DATA_PERIOD),
        "spec_period": list(SPEC_PERIOD),
        "n_country_year_obs": int(panel.dropna(subset=["m2_growth"]).shape[0]),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: per-country lag-1 correlation bars ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#1f1f1f",
    ]
    eq_series_pts = [
        {"x": c, "y": float(eq_lag_corr.get(c, 0.0)), "missing": c not in eq_lag_corr}
        for c in COUNTRIES
    ]
    house_series_pts = [
        {"x": c, "y": float(house_lag_corr.get(c, 0.0)), "missing": c not in house_lag_corr}
        for c in COUNTRIES
    ]

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "M2-growth(t-1) vs real asset return(t) — per-country correlations, 2008-2020",
        "subtitle": (
            f"Equities: {eq_n_nonneg}/{eq_n_total} non-neg, panel mean = "
            f"{eq_panel_mean_lag:+.3f}.  Housing: {house_n_nonneg}/{house_n_total} "
            f"non-neg, panel mean = {house_panel_mean_lag:+.3f}."
        ),
        "type": "bar",
        "x_axis": {"label": "Country (ISO3)", "type": "category"},
        "y_axis": {"label": "lag-1 Pearson correlation", "type": "linear"},
        "series": [
            {
                "id": "equity_lag1",
                "label": "Equities — real total return",
                "color": palette[0],
                "treated": False,
                "points": eq_series_pts,
            },
            {
                "id": "housing_lag1",
                "label": "Housing — real total return",
                "color": palette[1],
                "treated": False,
                "points": house_series_pts,
            },
        ],
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Falsification threshold: >=6/10 countries with non-negative "
                    f"lag-1 corr AND panel mean > 0, in at least one asset class. "
                    f"Equities {'PASS' if eq_supported else 'FAIL'}, "
                    f"Housing {'PASS' if house_supported else 'FAIL'}."
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

    # ---------- Coefficients table ----------
    coef_rows = []
    for c in COUNTRIES:
        if c in eq_lag_corr:
            coef_rows.append({"spec": "equity_lag1", "term": c, "estimate": eq_lag_corr[c]})
        if c in eq_contemp_corr:
            coef_rows.append({"spec": "equity_contemp", "term": c, "estimate": eq_contemp_corr[c]})
        if c in house_lag_corr:
            coef_rows.append({"spec": "housing_lag1", "term": c, "estimate": house_lag_corr[c]})
        if c in house_contemp_corr:
            coef_rows.append({"spec": "housing_contemp", "term": c, "estimate": house_contemp_corr[c]})
    coef_rows.append({"spec": "equity_lag1", "term": "panel_mean", "estimate": eq_panel_mean_lag})
    coef_rows.append({"spec": "housing_lag1", "term": "panel_mean", "estimate": house_panel_mean_lag})
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
    card = [
        f"# M2 expansion correlates with asset price inflation",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- 10-country developed-economy annual panel, JST Macrohistory "
        f"vintage (effective period {DATA_PERIOD[0]}-{DATA_PERIOD[1]}; spec "
        f"asks {SPEC_PERIOD[0]}-{SPEC_PERIOD[1]}; tail not yet covered).",
        f"- Equity leg: {eq_n_nonneg} of {eq_n_total} countries with non-negative "
        f"M2-growth(t-1) → real-equity-return(t) correlation. Panel mean "
        f"lag-1 correlation: **{eq_panel_mean_lag:+.3f}**.",
        f"- Housing leg: {house_n_nonneg} of {house_n_total} countries with "
        f"non-negative M2-growth(t-1) → real-housing-return(t) correlation. "
        f"Panel mean lag-1 correlation: **{house_panel_mean_lag:+.3f}**.",
        f"- Falsification threshold: ≥6/10 countries with non-negative lag-1 "
        f"correlation AND positive panel mean, in at least one asset class.",
        "",
        "## Method",
        "",
        "Annual data from the Jorda-Schularick-Taylor Macrohistory database "
        "(jst:money export, which carries the full wide JST_R6 row). For each "
        "of the 10 spec countries:",
        "",
        "1. M2 growth = first-difference of log(money).",
        "2. Real equity total return = (eq_tr) / (1 + CPI YoY) − 1, where "
        "eq_tr is the JST gross-return index ratio.",
        "3. Real housing total return = (housing_tr) / (1 + CPI YoY) − 1; for "
        "Canada, where JST has no housing_tr, fallback to real YoY of hpnom.",
        "4. Lag-1 correlation = Pearson(M2_growth(t-1), real_return(t)) over "
        "the 2008-2020 country sub-sample (≥5 obs required).",
        "",
        "Falsification rule (sharpened from spec): the symmetric-claim "
        "formulation requires both asset classes to clear; the asymmetric "
        "clause (\"asymmetric across asset classes\") is honoured by "
        "reporting a `partial` verdict when only one class clears.",
        "",
        "## Data",
        "",
        "- jst:money (Jorda-Schularick-Taylor Macrohistory wide panel, "
        "containing money / eq_tr / housing_tr / hpnom / cpi columns)",
        "",
        "## Caveats",
        "",
        "- JST annual frequency loses the quarterly lead-lag structure the "
        "spec's VECM design contemplated. The cointegration_vecm template is "
        "downgraded here to a panel-correlation primary because (a) annual "
        "frequency over 13 years yields too few observations for stable "
        "Johansen ranks per country, and (b) the spec's threshold is "
        "operationalisable as a country-share-of-positive-lag-correlations "
        "test without estimating a full VECM. A v2 promotion using "
        "quarterly BIS WS_SPP property prices + national M3 series could "
        "restore the VECM design.",
        "- Sample period 2008-2020 only; 2021-2025 (post-COVID QE peak and "
        "subsequent QT) not covered by the JST vintage on disk. The "
        "QE-peak years are exactly the test most favourable to the claim, "
        "so the absent tail makes the test slightly conservative.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
