#!/usr/bin/env python3
"""Replication — Initial state-share predicts subsequent drift reversal.

Spec: hypotheses/institutional_quality/initial_state_share_predicts_drift_reversal.yaml v1

Tests the conditional-convergence-of-policy-structure claim: countries
that began with very high general-government spending shares in 1976
should, on average, show *lower* subsequent per-decade drift slopes
(i.e. more market-pivot moves) than countries that began with
constrained shares.

Method: cross-sectional OLS, n=26 liberal democracies. Outcome is the
per-decade drift slope (statist_drift composite from
data/derived/country_drift.json). Treatment is hand-coded 1976-1980
average general-government spending share (% GDP) from the YAML spec,
with post-1989 transition cases (POL/CZE/HUN) using 1995-1999. Control
is log GDP per capita at 1976 (Solow-style starting condition).

PRIMARY (dispositive): the OLS slope β of per-decade drift slope on
initial spending-share is negative AND significant at p<0.10
(two-sided) AND model R² >= 0.20.

Primary spec drops ISR (per spec, Cook's-D outlier from post-Yom-Kippur
emergency spending). Secondary spec keeps ISR for robustness.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "initial_state_share_predicts_drift_reversal"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID
DRIFT_JSON = REPO_ROOT / "data" / "derived" / "country_drift.json"

# Sample (sample.countries from the YAML)
COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "IRL", "AUT",
    "PRT", "GRC", "SWE", "NOR", "DNK", "FIN", "CHE", "POL", "CZE", "HUN",
    "AUS", "NZL", "CAN", "JPN", "KOR", "ISR",
]

# Hand-coded 1976-1980 average general-government spending share (% of GDP)
# from spec.variables.treatment.notes. Transition states (POL, CZE, HUN)
# use 1995-1999 since pre-transition data is non-comparable.
INITIAL_GOVT_SHARE = {
    "USA": 29.5, "GBR": 42.5, "DEU": 43.0, "FRA": 44.5, "ITA": 37.5,
    "ESP": 24.0, "NLD": 49.0, "BEL": 51.0, "IRL": 43.0, "AUT": 46.5,
    "PRT": 30.0, "GRC": 29.0, "SWE": 55.5, "NOR": 46.0, "DNK": 51.0,
    "FIN": 37.5, "CHE": 27.5, "POL": 44.0, "CZE": 42.0, "HUN": 49.0,
    "AUS": 29.0, "NZL": 37.5, "CAN": 39.5, "JPN": 27.0, "KOR": 18.5,
    "ISR": 63.5,
}

PERIOD_START = 1976
PERIOD_END = 2025

# Falsification thresholds (from spec.falsification.threshold)
BETA_P_THRESHOLD = 0.10
R2_THRESHOLD = 0.20


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


def ols_slope_per_decade(years: list[int], values: list[float]) -> float:
    """OLS slope of values on years, scaled to per-decade."""
    if len(years) < 2:
        return 0.0
    xs = np.asarray(years, dtype=float)
    ys = np.asarray(values, dtype=float)
    mx = xs.mean()
    my = ys.mean()
    den = np.sum((xs - mx) ** 2)
    if den == 0:
        return 0.0
    num = np.sum((xs - mx) * (ys - my))
    return float((num / den) * 10.0)


def ols_full(x: np.ndarray, y: np.ndarray) -> dict:
    """OLS regression of y on [intercept, x...]. Returns coefficients,
    SEs, t-stats, two-sided p-values, R², n."""
    n = len(y)
    if x.ndim == 1:
        X = np.column_stack([np.ones(n), x])
    else:
        X = np.column_stack([np.ones(n), x])
    k = X.shape[1]
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    yhat = X @ beta
    resid = y - yhat
    rss = float(np.sum(resid ** 2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - rss / tss if tss > 0 else 0.0
    df = n - k
    sigma2 = rss / df if df > 0 else float("nan")
    se = np.sqrt(np.diag(XtX_inv) * sigma2)
    t = beta / se
    # two-sided p-value via Student's-t survival (use scipy if available else
    # normal approximation for n large enough; here n is small so do it
    # manually with the regularised incomplete beta function from math)
    p = np.array([2.0 * _t_sf(abs(ti), df) for ti in t])
    return {
        "beta": beta.tolist(),
        "se": se.tolist(),
        "t": t.tolist(),
        "p": p.tolist(),
        "r2": float(r2),
        "n": int(n),
        "df": int(df),
        "rss": rss,
        "tss": tss,
    }


def _t_sf(t_abs: float, df: int) -> float:
    """Survival function (1-CDF) of Student's t at |t|, df>0. Uses the
    incomplete-beta identity: P(T > t) = 0.5 * I_{df/(df+t^2)}(df/2, 1/2)."""
    if df <= 0:
        return float("nan")
    x = df / (df + t_abs * t_abs)
    return 0.5 * _betai(df / 2.0, 0.5, x)


def _betai(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function via continued fraction
    (Numerical Recipes betai)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _betacf(a: float, b: float, x: float, maxit: int = 200, eps: float = 3e-7) -> float:
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    return h


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Load drift JSON for outcome ----------
    drift = json.loads(DRIFT_JSON.read_text())
    drift_years = drift["years"]
    drift_countries = drift["countries"]

    # Restrict drift to spec window (1976-2025), and compute per-decade slope
    # for each country (same approach as fiscal_rule_presence_dampens_statist_drift).
    window_idx = [i for i, y in enumerate(drift_years) if PERIOD_START <= y <= PERIOD_END]
    window_years = [drift_years[i] for i in window_idx]

    rows = []
    for iso3 in COUNTRIES:
        if iso3 not in drift_countries:
            continue
        traj_full = drift_countries[iso3]["statist_drift"]
        traj = [traj_full[i] for i in window_idx]
        # First-nonzero anchoring (matches fiscal_rule run): start the slope
        # at the first non-zero point so countries with late corpus entry
        # don't get artificial flat-then-jump slopes.
        first_nz = next((i for i, v in enumerate(traj) if v != 0), None)
        if first_nz is None:
            slope = 0.0
            n_obs = 0
        else:
            sub_xs = [int(window_years[i]) for i in range(first_nz, len(traj))]
            sub_ys = [float(traj[i]) for i in range(first_nz, len(traj))]
            slope = ols_slope_per_decade(sub_xs, sub_ys)
            n_obs = len(sub_xs)
        rows.append({
            "iso3": iso3,
            "initial_share": INITIAL_GOVT_SHARE[iso3],
            "slope_per_decade": slope,
            "drift_obs": n_obs,
            "movements": drift_countries[iso3].get("movement_count", 0),
        })

    df = pd.DataFrame(rows)

    # ---------- Load WDI GDP-pc for control ----------
    gdppc_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    gdppc = load_long(gdppc_path)
    # Initial = mean of 1976-1980 to match treatment window (post-1989
    # transitions: use 1995-1999 to match treatment construction).
    transition = {"POL", "CZE", "HUN"}
    log_init_gdp_pc: dict[str, float] = {}
    for c in COUNTRIES:
        win = (1995, 1999) if c in transition else (1976, 1980)
        s = gdppc[(gdppc["country_iso3"] == c) & (gdppc["year"].between(win[0], win[1]))]
        if not s.empty:
            log_init_gdp_pc[c] = float(np.log(s["value"].mean()))
        else:
            log_init_gdp_pc[c] = float("nan")
    df["log_init_gdp_pc"] = df["iso3"].map(log_init_gdp_pc)

    # ---------- PRIMARY SPEC: drop ISR ----------
    primary_df = df[df["iso3"] != "ISR"].copy()
    x = primary_df["initial_share"].to_numpy(dtype=float)
    y = primary_df["slope_per_decade"].to_numpy(dtype=float)
    primary_uni = ols_full(x, y)
    beta_uni = primary_uni["beta"][1]
    p_uni = primary_uni["p"][1]
    r2_uni = primary_uni["r2"]

    # With log-GDP-pc control (drop any rows with NaN control)
    primary_with_ctrl = primary_df.dropna(subset=["log_init_gdp_pc"]).copy()
    X2 = primary_with_ctrl[["initial_share", "log_init_gdp_pc"]].to_numpy(dtype=float)
    y2 = primary_with_ctrl["slope_per_decade"].to_numpy(dtype=float)
    primary_ctrl = ols_full(X2, y2)
    beta_ctrl = primary_ctrl["beta"][1]
    p_ctrl = primary_ctrl["p"][1]
    r2_ctrl = primary_ctrl["r2"]

    # ---------- SECONDARY SPEC: full sample including ISR ----------
    full_x = df["initial_share"].to_numpy(dtype=float)
    full_y = df["slope_per_decade"].to_numpy(dtype=float)
    secondary_uni = ols_full(full_x, full_y)

    # ---------- VERDICT against PRIMARY (univariate, ISR-excluded) ----------
    direction_correct = beta_uni < 0
    sig = p_uni < BETA_P_THRESHOLD
    r2_meets = r2_uni >= R2_THRESHOLD

    if direction_correct and sig and r2_meets:
        verdict = (
            f"SUPPORTED — Cross-sectional OLS (n={primary_uni['n']}, ISR-excluded) "
            f"of per-decade drift slope on initial 1976-1980 govt-spending share: "
            f"β = {beta_uni:+.4f} per pp share (p = {p_uni:.4f}), R² = {r2_uni:.3f}. "
            f"High-state-share countries reverted; low-state-share countries expanded. "
            f"With log-GDP-pc control: β = {beta_ctrl:+.4f} (p = {p_ctrl:.4f}), R² = {r2_ctrl:.3f}."
        )
    elif (not direction_correct) and sig:
        verdict = (
            f"refuted — Cross-sectional OLS (n={primary_uni['n']}, ISR-excluded): "
            f"β = {beta_uni:+.4f} per pp share (p = {p_uni:.4f}), R² = {r2_uni:.3f}. "
            f"The slope is positive and significant — high-state-share countries continued "
            f"to expand the state on average. The convergence claim is contradicted; the "
            f"data fit a creep narrative."
        )
    elif direction_correct and (sig or r2_meets):
        verdict = (
            f"partial — Direction is correct (β = {beta_uni:+.4f}) but the dispositive "
            f"thresholds are not jointly met: p = {p_uni:.4f} (need < {BETA_P_THRESHOLD}), "
            f"R² = {r2_uni:.3f} (need ≥ {R2_THRESHOLD}). Pattern is suggestive but not "
            f"clean."
        )
    elif direction_correct:
        verdict = (
            f"partial — Direction is correct (β = {beta_uni:+.4f}) but neither the "
            f"significance threshold (p = {p_uni:.4f}) nor the explanatory threshold "
            f"(R² = {r2_uni:.3f}) is met. Suggestive only."
        )
    elif (not direction_correct) and r2_uni < 0.05:
        verdict = (
            f"refuted — β = {beta_uni:+.4f} (positive, against claim) with R² = {r2_uni:.3f} "
            f"(< 0.05). No reversion-to-the-median signal detected."
        )
    else:
        verdict = (
            f"inconclusive — β = {beta_uni:+.4f} (p = {p_uni:.4f}), R² = {r2_uni:.3f}. "
            f"Effect statistically zero with no informative direction; the cross-section "
            f"is underpowered to discriminate between convergence and creep."
        )

    # ---------- Diagnostics ----------
    diagnostics = {
        "verdict": verdict,
        "method": "Cross-sectional OLS, n=26 liberal democracies; primary spec excludes ISR (Cook's-D outlier per spec)",
        "primary_univariate": {
            "n": primary_uni["n"],
            "beta_initial_share": round(beta_uni, 6),
            "se": round(primary_uni["se"][1], 6),
            "t": round(primary_uni["t"][1], 4),
            "p_two_sided": round(p_uni, 6),
            "intercept": round(primary_uni["beta"][0], 6),
            "r2": round(r2_uni, 6),
        },
        "primary_with_log_gdp_pc_control": {
            "n": primary_ctrl["n"],
            "beta_initial_share": round(beta_ctrl, 6),
            "p_two_sided_initial_share": round(p_ctrl, 6),
            "beta_log_gdp_pc": round(primary_ctrl["beta"][2], 6),
            "p_two_sided_log_gdp_pc": round(primary_ctrl["p"][2], 6),
            "intercept": round(primary_ctrl["beta"][0], 6),
            "r2": round(r2_ctrl, 6),
        },
        "secondary_full_sample_with_ISR": {
            "n": secondary_uni["n"],
            "beta_initial_share": round(secondary_uni["beta"][1], 6),
            "p_two_sided": round(secondary_uni["p"][1], 6),
            "r2": round(secondary_uni["r2"], 6),
        },
        "thresholds": {
            "direction": "beta < 0",
            "significance": f"p < {BETA_P_THRESHOLD}",
            "fit": f"R^2 >= {R2_THRESHOLD}",
        },
        "falsification_legs": {
            "direction_correct": bool(direction_correct),
            "significant_at_p10": bool(sig),
            "r2_above_0_20": bool(r2_meets),
        },
        "rows": rows,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Coefficients parquet ----------
    coef_rows = [
        {"spec": "primary_univariate", "term": "intercept",
         "estimate": primary_uni["beta"][0], "se": primary_uni["se"][0],
         "t": primary_uni["t"][0], "p": primary_uni["p"][0]},
        {"spec": "primary_univariate", "term": "initial_share",
         "estimate": primary_uni["beta"][1], "se": primary_uni["se"][1],
         "t": primary_uni["t"][1], "p": primary_uni["p"][1]},
        {"spec": "primary_with_control", "term": "intercept",
         "estimate": primary_ctrl["beta"][0], "se": primary_ctrl["se"][0],
         "t": primary_ctrl["t"][0], "p": primary_ctrl["p"][0]},
        {"spec": "primary_with_control", "term": "initial_share",
         "estimate": primary_ctrl["beta"][1], "se": primary_ctrl["se"][1],
         "t": primary_ctrl["t"][1], "p": primary_ctrl["p"][1]},
        {"spec": "primary_with_control", "term": "log_init_gdp_pc",
         "estimate": primary_ctrl["beta"][2], "se": primary_ctrl["se"][2],
         "t": primary_ctrl["t"][2], "p": primary_ctrl["p"][2]},
        {"spec": "secondary_full_sample", "term": "intercept",
         "estimate": secondary_uni["beta"][0], "se": secondary_uni["se"][0],
         "t": secondary_uni["t"][0], "p": secondary_uni["p"][0]},
        {"spec": "secondary_full_sample", "term": "initial_share",
         "estimate": secondary_uni["beta"][1], "se": secondary_uni["se"][1],
         "t": secondary_uni["t"][1], "p": secondary_uni["p"][1]},
    ]
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Chart: scatter of slope vs initial-share ----------
    palette = [
        "#4E79A7", "#59A14F", "#B07AA1", "#E15759", "#F28E2B", "#76B7B2",
        "#EDC948", "#B6992D", "#9C755F", "#8884d8", "#82ca9d", "#ffc658",
    ]
    primary_set = set(primary_df["iso3"])
    series = []
    for i, r in enumerate(rows):
        is_primary = r["iso3"] in primary_set
        series.append({
            "id": r["iso3"],
            "label": r["iso3"],
            "color": palette[i % len(palette)],
            "treated": not is_primary,  # ISR shown as outlier
            "points": [{
                "x": float(r["initial_share"]),
                "y": float(r["slope_per_decade"]),
            }],
        })

    # OLS fit-line for the primary (ISR-excluded) regression
    a = primary_uni["beta"][0]
    b = primary_uni["beta"][1]
    x_min = float(min(r["initial_share"] for r in rows if r["iso3"] in primary_set))
    x_max = float(max(r["initial_share"] for r in rows if r["iso3"] in primary_set))
    fit_pts = [
        {"x": x_min, "y": a + b * x_min},
        {"x": x_max, "y": a + b * x_max},
    ]
    series.insert(0, {
        "id": "OLS_FIT",
        "label": f"OLS fit (ISR-excluded): β = {b:+.3f}/pp share",
        "color": "#1f1f1f",
        "treated": True,
        "points": fit_pts,
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Per-decade drift slope vs initial 1976-1980 govt-spending share",
        "subtitle": (
            f"Cross-section, n={primary_uni['n']} (ISR excluded). "
            f"β = {beta_uni:+.4f} per pp share (p = {p_uni:.4f}), R² = {r2_uni:.3f}."
        ),
        "type": "scatter",
        "x_axis": {"label": "Initial govt spending share, % GDP (1976-1980 avg)", "type": "linear"},
        "y_axis": {"label": "Per-decade statist-drift slope", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Negative β ⇒ countries that started with a larger state "
                    f"have, on average, drifted toward market-liberal "
                    f"positions over the 1976-2025 corpus window."
                ),
            }
        ],
        "sources": [
            {
                "publisher_id": "constructed",
                "series_id": "data/derived/country_drift.json",
                "vintage_file": "data/derived/country_drift.json",
            },
            {
                "publisher_id": "world_bank_wdi",
                "series_id": "NY.GDP.PCAP.KD",
                "vintage_file": str(gdppc_path.relative_to(REPO_ROOT)),
            },
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Manifest ----------
    drift_sha = sha256(DRIFT_JSON)
    gdppc_sha = sha256(gdppc_path)
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        "  drift_json:\n"
        "    publisher: constructed\n"
        "    series: data/derived/country_drift.json\n"
        f"    vintage_file: {DRIFT_JSON.relative_to(REPO_ROOT)}\n"
        f"    sha256: {drift_sha}\n"
        "  gdp_per_capita:\n"
        "    publisher: world_bank_wdi\n"
        "    series: NY.GDP.PCAP.KD\n"
        f"    vintage_file: {gdppc_path.relative_to(REPO_ROOT)}\n"
        f"    sha256: {gdppc_sha}\n"
        "treatment_coding:\n"
        + "".join(f"  {k}: {v}\n" for k, v in INITIAL_GOVT_SHARE.items())
    )

    # ---------- Result card ----------
    sorted_rows = sorted(rows, key=lambda r: r["initial_share"])
    rows_table = "\n".join(
        f"| {r['iso3']} | {r['initial_share']:.1f} | {r['slope_per_decade']:+.3f} | "
        f"{r['drift_obs']} | {r['movements']} |"
        for r in sorted_rows
    )
    card = [
        f"# Initial state-share predicts drift reversal",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Primary specification (ISR excluded)",
        "",
        f"- n = {primary_uni['n']}",
        f"- β (initial_share) = {beta_uni:+.4f} per pp of GDP "
        f"(SE = {primary_uni['se'][1]:.4f}, t = {primary_uni['t'][1]:.3f}, "
        f"two-sided p = {p_uni:.4f})",
        f"- R² = {r2_uni:.3f}",
        f"- Threshold: β < 0 AND p < {BETA_P_THRESHOLD} AND R² ≥ {R2_THRESHOLD}",
        "",
        "## With log-GDP-pc control",
        "",
        f"- n = {primary_ctrl['n']}",
        f"- β (initial_share) = {beta_ctrl:+.4f} (p = {p_ctrl:.4f})",
        f"- β (log_init_gdp_pc) = {primary_ctrl['beta'][2]:+.4f} "
        f"(p = {primary_ctrl['p'][2]:.4f})",
        f"- R² = {r2_ctrl:.3f}",
        "",
        "## Secondary spec — full sample with ISR",
        "",
        f"- n = {secondary_uni['n']}",
        f"- β (initial_share) = {secondary_uni['beta'][1]:+.4f} "
        f"(p = {secondary_uni['p'][1]:.4f})",
        f"- R² = {secondary_uni['r2']:.3f}",
        "",
        "## Country-level data",
        "",
        "| Country | Initial share (% GDP) | Slope/decade | Drift obs | Movements |",
        "|---|---:|---:|---:|---:|",
        rows_table,
        "",
        "## Method",
        "",
        "Cross-sectional OLS, n=26 liberal democracies. Outcome = per-decade",
        "OLS slope of `statist_drift` composite from",
        "`data/derived/country_drift.json` (same outcome construction as",
        "`fiscal_rule_presence_dampens_statist_drift`: anchor at the first",
        "non-zero drift observation, then OLS slope × 10).",
        "",
        "Treatment = hand-coded 1976-1980 average general-government total",
        "expenditure share of GDP (post-1989 transitions POL/CZE/HUN: 1995-1999,",
        "since pre-transition socialist-bloc data is non-comparable).",
        "Control = log GDP-pc constant 2015 USD averaged over the same window.",
        "",
        "Primary spec excludes ISR (Israel) per the spec's own outlier flag —",
        "the 1976-1980 share of ~63.5% GDP reflects post-Yom-Kippur-War",
        "emergency spending and is far outside the range. Secondary spec keeps",
        "ISR for robustness; if signs flip between specs that's reported.",
        "",
        "## Falsification legs",
        "",
        f"- Direction correct (β < 0): **{direction_correct}**",
        f"- Significant at p<{BETA_P_THRESHOLD}: **{sig}**",
        f"- R² ≥ {R2_THRESHOLD}: **{r2_meets}**",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/initial_state_share_predicts_drift_reversal.md`.",
        "Particularly relevant: (i) the corpus' policy-direction coding is itself",
        "constructed from movements that may be biased toward market-pivot framing;",
        "(ii) the 1976-1980 starting window is long after the main post-war",
        "expansion of the state — earlier baselines (1960s) would produce different",
        "rankings; (iii) regression-to-the-median in coded measures can be a",
        "Galtonian artefact rather than a substantive convergence story.",
        "",
        "## Provenance",
        "",
        "- `data/derived/country_drift.json` (built by `scripts/compute_country_drift.py`)",
        f"- `world_bank_wdi:NY.GDP.PCAP.KD` (latest vintage on disk)",
        "- INITIAL_GOVT_SHARE dictionary in this script (hand-coded from spec)",
        "",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")
    print(f"  primary uni: β={beta_uni:+.4f}, p={p_uni:.4f}, R²={r2_uni:.3f}, n={primary_uni['n']}")
    print(f"  with control: β={beta_ctrl:+.4f}, p={p_ctrl:.4f}, R²={r2_ctrl:.3f}")
    print(f"  full sample (ISR included): β={secondary_uni['beta'][1]:+.4f}, "
          f"p={secondary_uni['p'][1]:.4f}, R²={secondary_uni['r2']:.3f}")
    print(f"\nartifacts in {OUT_DIR}")


if __name__ == "__main__":
    main()
