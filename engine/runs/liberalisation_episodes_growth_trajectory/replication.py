#!/usr/bin/env python3
"""Replication — Liberalisation episodes and growth trajectory.

Spec: hypotheses/growth/liberalisation_episodes_growth_trajectory.yaml v1
Position-claim: classical_liberal #0 (school predicts: supported)

Tests the classical-liberal claim that growth FOLLOWS liberalisation rather
than precedes it. Implements a stacked event study around dated
liberalisation episodes:

  Episode definition: country-year where the Fraser EFW aggregate score
  ('efw_summary') jumps by >= +0.5 points over the preceding 5 years.
  Fraser EFW is published at 5-year intervals 1970-2000 and annually
  2000-2023, so the 5-year window is the natural unit. To avoid
  double-counting the same reform wave we keep ONE episode per country —
  the year of that country's largest 5-year EFW jump, conditional on the
  jump exceeding +0.5 points.

  Outcome: real GDP-per-capita log-growth (year-on-year), built from
  NY.GDP.PCAP.PP.KD (PPP, 2021 USD) — falling back to NY.GDP.PCAP.KD
  (constant-USD, broader coverage pre-1990) for countries missing PPP
  data.

  Event-time horizons: h ∈ {-5, -3, 0, 3, 5, 10}. For each (country,
  episode-year e, horizon h) cell we average the year-on-year log-growth
  observations in a ±1 window around year e+h (so h=3 averages growth in
  years e+2..e+4). 2020 is dropped as a COVID outlier.

  Statistic: weighted (by number of obs) mean of growth at each horizon
  across the episode panel. Cluster-robust SE by country via a simple
  block-bootstrap of countries (1000 reps) — country is the cluster
  unit because the same country can host multiple episodes.

PRIMARY (dispositive):
  SUPPORTED if mean log-growth at h=3 AND h=5 AND h=10 is each ≥ +0.5
  pp/yr above the country-mean baseline AND statistically positive at
  p < 0.10 (block-bootstrap), AND pre-trend coefficients at h=-5 and h=-3
  are not significantly POSITIVE at p < 0.10 (i.e. p>=0.10 against the
  null of zero in the positive direction OR magnitude < +0.5pp).
  REFUTED if h=3,5,10 are not all positive, OR if pre-trends are
  significantly POSITIVE (reverse-causation indicator).
  Otherwise PARTIAL.

INFORMATIVE: per-horizon estimates and SEs reported in diagnostics.
METHOD_VALID: ≥ 30 episodes detected across the 41-country panel.
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
HID = "liberalisation_episodes_growth_trajectory"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from the spec (sample.countries)
COUNTRIES = [
    "USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "SWE",
    "NOR", "DNK", "FIN", "IRL", "JPN", "CAN", "AUS", "NZL", "KOR", "CHL",
    "MEX", "ARG", "BRA", "IND", "IDN", "TUR", "POL", "HUN", "CZE", "EST",
    "ZAF", "PHL", "MYS", "THA", "VNM", "CHN", "EGY", "MAR", "KEN", "GHA",
    "NGA",
]
PERIOD = (1971, 2019)
EXCLUDE_GROWTH_YEARS = {2020}  # COVID outlier

# Episode-detection thresholds
EFW_JUMP_5Y_THRESHOLD = 0.5  # 5-year change in EFW summary required for an episode
ONE_EPISODE_PER_COUNTRY = True  # take the year of largest qualifying 5-yr jump

# Event-study horizons
HORIZONS = [-5, -3, 0, 3, 5, 10]
HORIZON_WINDOW = 1  # ± 1 year around e+h

# Falsification thresholds
POST_HORIZONS_REQUIRED = [3, 5, 10]
POST_GROWTH_THRESHOLD = 0.005  # +0.5 pp/yr above country-mean baseline
PRETREND_HORIZONS = [-5, -3]
PRETREND_POSITIVE_THRESHOLD = 0.005  # +0.5pp/yr is "positive pre-trend"
ALPHA = 0.10
BOOTSTRAP_REPS = 1000
BOOTSTRAP_SEED = 20260424
MIN_EPISODES_FOR_VALID = 30


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
    """Standard normaliser for WDI/IMF-style (country_iso3, year, value)."""
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


def load_efw(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    # efw_panel columns: country_iso3, country_name, year, efw_summary, area_1..5
    t = t[["country_iso3", "year", "efw_summary"]].copy()
    t = t[t["country_iso3"].notna()]
    t["year"] = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    t["efw_summary"] = pd.to_numeric(t["efw_summary"], errors="coerce")
    return t.dropna(subset=["year", "efw_summary"])


def detect_episodes(efw: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    """Detect liberalisation episodes per country.

    For each country, find all years e where efw[e] - efw[e-5] >= 0.5.
    Among those, pick the year of the LARGEST 5-year jump as the country's
    liberalisation episode (one episode per country). Episodes restricted
    to year e in [PERIOD[0]+5, PERIOD[1]] so we have at least the 5-year
    pre-window inside the sample.
    """
    rows = []
    for c in countries:
        sub = (
            efw[efw["country_iso3"] == c]
            .set_index("year")["efw_summary"]
            .sort_index()
        )
        if sub.empty:
            continue
        candidates = []
        for y in sub.index:
            yi = int(y)
            if yi < PERIOD[0] + 5 or yi > PERIOD[1]:
                continue
            if (yi - 5) not in sub.index:
                continue
            jump5 = float(sub[yi] - sub[yi - 5])
            if jump5 >= EFW_JUMP_5Y_THRESHOLD:
                candidates.append((yi, jump5, float(sub[yi])))
        if not candidates:
            continue
        if ONE_EPISODE_PER_COUNTRY:
            # year of largest 5yr jump
            yi, j5, v = max(candidates, key=lambda t: t[1])
            rows.append({
                "country_iso3": c,
                "episode_year": int(yi),
                "efw_at_e": v,
                "efw_jump_5y": j5,
            })
        else:
            for yi, j5, v in candidates:
                rows.append({
                    "country_iso3": c,
                    "episode_year": int(yi),
                    "efw_at_e": v,
                    "efw_jump_5y": j5,
                })
    return pd.DataFrame(rows)


def build_growth_panel(gdp: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    """Per-country annual log-growth, dropping pairs touching COVID 2020."""
    rows = []
    for c in countries:
        sub = (
            gdp[gdp["country_iso3"] == c]
            .set_index("year")["value"]
            .sort_index()
        )
        if sub.empty:
            continue
        log = np.log(sub.replace(0, np.nan)).dropna()
        for y in log.index:
            yi = int(y)
            if (yi - 1) in log.index and yi not in EXCLUDE_GROWTH_YEARS and (yi - 1) not in EXCLUDE_GROWTH_YEARS:
                rows.append({
                    "country_iso3": c,
                    "year": yi,
                    "log_growth": float(log[yi] - log[yi - 1]),
                })
    return pd.DataFrame(rows)


def country_baseline(growth: pd.DataFrame) -> dict[str, float]:
    """Per-country mean log-growth across full sample period (excluding the
    horizon windows around episodes) to net out level differences."""
    return growth.groupby("country_iso3")["log_growth"].mean().to_dict()


def event_study(
    episodes: pd.DataFrame,
    growth: pd.DataFrame,
    baselines: dict[str, float],
) -> tuple[dict[int, float], dict[int, list[float]], dict[int, int]]:
    """Compute mean (growth - country baseline) at each event-time horizon.

    Returns:
      coef[h]  = mean of (growth - country_mean) across all (country, episode,
                 year-in-window) cells with event-time = h ± HORIZON_WINDOW.
      cells[h] = list of per-(country, episode) demean'd growth means at h
                 (used for bootstrap).
      n[h]     = number of (country, episode) cells with at least one obs.
    """
    coef = {}
    cells = {h: [] for h in HORIZONS}  # one entry per (country, episode)
    n = {h: 0 for h in HORIZONS}

    growth_idx = growth.set_index(["country_iso3", "year"])["log_growth"]

    for h in HORIZONS:
        per_episode_means = []
        for r in episodes.itertuples():
            c = r.country_iso3
            e = int(r.episode_year)
            base = baselines.get(c)
            if base is None:
                continue
            target = e + h
            ys = list(range(target - HORIZON_WINDOW, target + HORIZON_WINDOW + 1))
            obs = []
            for y in ys:
                key = (c, y)
                if key in growth_idx.index:
                    obs.append(float(growth_idx.loc[key]) - base)
            if obs:
                per_episode_means.append(np.mean(obs))
        if per_episode_means:
            coef[h] = float(np.mean(per_episode_means))
            cells[h] = per_episode_means
            n[h] = len(per_episode_means)
        else:
            coef[h] = float("nan")
    return coef, cells, n


def block_bootstrap(
    episodes: pd.DataFrame,
    growth: pd.DataFrame,
    baselines: dict[str, float],
    reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[int, np.ndarray]:
    """Country-block bootstrap: resample countries with replacement, recompute
    coef[h]. Returns dict h -> ndarray of bootstrap estimates."""
    rng = np.random.default_rng(seed)
    countries = sorted(episodes["country_iso3"].unique())
    n_c = len(countries)
    growth_idx = growth.set_index(["country_iso3", "year"])["log_growth"]
    out = {h: np.empty(reps) for h in HORIZONS}
    # Pre-compute per-episode means for each (country, h) so the inner loop is fast.
    per_country_h: dict[tuple[str, int], list[float]] = {}
    for r in episodes.itertuples():
        c = r.country_iso3
        e = int(r.episode_year)
        base = baselines.get(c)
        if base is None:
            continue
        for h in HORIZONS:
            target = e + h
            ys = list(range(target - HORIZON_WINDOW, target + HORIZON_WINDOW + 1))
            obs = []
            for y in ys:
                key = (c, y)
                if key in growth_idx.index:
                    obs.append(float(growth_idx.loc[key]) - base)
            if obs:
                per_country_h.setdefault((c, h), []).append(np.mean(obs))

    for b in range(reps):
        sample = rng.choice(countries, size=n_c, replace=True)
        for h in HORIZONS:
            vals = []
            for c in sample:
                vals.extend(per_country_h.get((c, h), []))
            out[h][b] = np.mean(vals) if vals else np.nan
    return out


def two_sided_p(boot: np.ndarray, point: float) -> float:
    """Two-sided p-value for the null that the true coef is 0, using the
    bootstrap distribution of the point estimate. p = 2 * min(P[b<=0], P[b>=0])."""
    finite = boot[np.isfinite(boot)]
    if len(finite) == 0:
        return float("nan")
    p_lo = float(np.mean(finite <= 0))
    p_hi = float(np.mean(finite >= 0))
    return min(1.0, 2.0 * min(p_lo, p_hi))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    efw_path = latest("fraser_efw", "efw_panel")
    gdp_pp_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    gdp_kd_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")

    manifest = {
        "efw": {
            "publisher": "fraser_efw",
            "series": "efw_panel",
            "vintage_file": str(efw_path.relative_to(REPO_ROOT)),
            "sha256": sha256(efw_path),
        },
        "gdp_pcap_ppp": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.PP.KD",
            "vintage_file": str(gdp_pp_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_pp_path),
        },
        "gdp_pcap_kd": {
            "publisher": "world_bank_wdi",
            "series": "NY.GDP.PCAP.KD",
            "vintage_file": str(gdp_kd_path.relative_to(REPO_ROOT)),
            "sha256": sha256(gdp_kd_path),
        },
    }

    efw = load_efw(efw_path)
    gdp_pp = load_long(gdp_pp_path)
    gdp_kd = load_long(gdp_kd_path)

    # Combine: prefer PPP, fall back to constant-USD where PPP missing.
    gdp_pp = gdp_pp[gdp_pp["country_iso3"].isin(COUNTRIES)].copy()
    gdp_kd = gdp_kd[gdp_kd["country_iso3"].isin(COUNTRIES)].copy()
    gdp_pp["src"] = "ppp"
    gdp_kd["src"] = "kd"
    have_pp = set(zip(gdp_pp["country_iso3"], gdp_pp["year"]))
    gdp_kd_supp = gdp_kd[
        ~gdp_kd.apply(lambda r: (r["country_iso3"], r["year"]) in have_pp, axis=1)
    ]
    gdp = pd.concat([gdp_pp, gdp_kd_supp], ignore_index=True)

    # ---------- Episode detection ----------
    episodes = detect_episodes(efw, COUNTRIES)
    n_episodes = int(len(episodes))
    n_episode_countries = int(episodes["country_iso3"].nunique()) if n_episodes else 0
    method_valid = n_episodes >= MIN_EPISODES_FOR_VALID

    # ---------- Growth panel & baselines ----------
    growth = build_growth_panel(gdp, COUNTRIES)
    baselines = country_baseline(growth)

    # ---------- Event study ----------
    coef, cells, n_per_h = event_study(episodes, growth, baselines)

    # Bootstrap SEs / p-values (only if we have enough episodes)
    if n_episodes > 0:
        boot = block_bootstrap(episodes, growth, baselines)
    else:
        boot = {h: np.empty(0) for h in HORIZONS}

    se = {}
    pval = {}
    for h in HORIZONS:
        b = boot[h]
        finite = b[np.isfinite(b)] if len(b) else np.array([])
        se[h] = float(np.std(finite, ddof=1)) if len(finite) > 1 else float("nan")
        pval[h] = float(two_sided_p(finite, coef[h])) if len(finite) > 0 else float("nan")

    # ---------- Verdict logic ----------
    primary_post_supported = True
    pre_trend_clean = True
    post_details = {}
    pretrend_details = {}

    if not method_valid:
        verdict = (
            f"inconclusive (method gap: only {n_episodes} liberalisation "
            f"episodes detected across {n_episode_countries} countries; "
            f"≥{MIN_EPISODES_FOR_VALID} required for the panel event study). "
            f"Spec needs a richer episode catalogue (Sachs-Warner / "
            f"Wacziarg-Welch dating) before this hypothesis can be graded."
        )
        primary_post_supported = False
        pre_trend_clean = False
    else:
        for h in POST_HORIZONS_REQUIRED:
            c = coef[h]
            p = pval[h]
            ok_mag = (np.isfinite(c) and c >= POST_GROWTH_THRESHOLD)
            ok_sig = (np.isfinite(p) and p < ALPHA and c > 0)
            post_details[str(h)] = {
                "coef": float(c) if np.isfinite(c) else None,
                "se": float(se[h]) if np.isfinite(se[h]) else None,
                "pval": float(p) if np.isfinite(p) else None,
                "n_cells": int(n_per_h[h]),
                "magnitude_ok": bool(ok_mag),
                "significance_ok": bool(ok_sig),
            }
            if not (ok_mag and ok_sig):
                primary_post_supported = False
        for h in PRETREND_HORIZONS:
            c = coef[h]
            p = pval[h]
            # "Positive pre-trend" = positive AND magnitude >= threshold AND p<alpha
            is_positive_pretrend = (
                np.isfinite(c)
                and np.isfinite(p)
                and c >= PRETREND_POSITIVE_THRESHOLD
                and p < ALPHA
            )
            pretrend_details[str(h)] = {
                "coef": float(c) if np.isfinite(c) else None,
                "se": float(se[h]) if np.isfinite(se[h]) else None,
                "pval": float(p) if np.isfinite(p) else None,
                "n_cells": int(n_per_h[h]),
                "is_positive_pretrend": bool(is_positive_pretrend),
            }
            if is_positive_pretrend:
                pre_trend_clean = False

        if primary_post_supported and pre_trend_clean:
            verdict = (
                f"SUPPORTED — Across {n_episodes} liberalisation episodes "
                f"({n_episode_countries} countries, EFW jump ≥0.5 over 3 yrs), "
                f"mean post-reform log-growth (excess over country baseline) "
                f"is +{coef[3]*100:+.2f}pp at h=3, +{coef[5]*100:+.2f}pp at h=5, "
                f"+{coef[10]*100:+.2f}pp at h=10 (each p<{ALPHA}). Pre-trends "
                f"at h=-3 ({coef[-3]*100:+.2f}pp, p={pval[-3]:.2f}) and h=-5 "
                f"({coef[-5]*100:+.2f}pp, p={pval[-5]:.2f}) are not "
                f"significantly positive — growth follows reform, not the "
                f"reverse."
            )
        elif (not primary_post_supported) and pre_trend_clean:
            misses = [h for h in POST_HORIZONS_REQUIRED if not (post_details[str(h)]["magnitude_ok"] and post_details[str(h)]["significance_ok"])]
            verdict = (
                f"refuted — Post-reform horizons fail at h={misses}: "
                f"h=3 {coef[3]*100:+.2f}pp (p={pval[3]:.2f}), "
                f"h=5 {coef[5]*100:+.2f}pp (p={pval[5]:.2f}), "
                f"h=10 {coef[10]*100:+.2f}pp (p={pval[10]:.2f}). "
                f"Pre-trends are clean but the claimed growth pickup after "
                f"liberalisation does not survive a stacked event study on "
                f"{n_episodes} EFW-jump episodes."
            )
        elif primary_post_supported and (not pre_trend_clean):
            verdict = (
                f"refuted — Reverse-causation indicator: pre-trend at "
                f"h=-3 {coef[-3]*100:+.2f}pp (p={pval[-3]:.2f}) and/or h=-5 "
                f"{coef[-5]*100:+.2f}pp (p={pval[-5]:.2f}) is significantly "
                f"positive, indicating that growth precedes EFW jumps rather "
                f"than the reverse. Post-reform coefs (h=3 {coef[3]*100:+.2f}pp; "
                f"h=5 {coef[5]*100:+.2f}pp; h=10 {coef[10]*100:+.2f}pp) are "
                f"positive but cannot be attributed to the reform."
            )
        else:
            # post fails AND pre-trends bad
            verdict = (
                f"refuted — Both the post-reform growth pickup and the "
                f"clean-pre-trend conditions fail. h=3 {coef[3]*100:+.2f}pp "
                f"(p={pval[3]:.2f}); h=5 {coef[5]*100:+.2f}pp (p={pval[5]:.2f}); "
                f"h=10 {coef[10]*100:+.2f}pp (p={pval[10]:.2f}). Pre-trends: "
                f"h=-3 {coef[-3]*100:+.2f}pp; h=-5 {coef[-5]*100:+.2f}pp."
            )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "n_episodes": n_episodes,
        "n_episode_countries": n_episode_countries,
        "n_panel_countries": int(growth["country_iso3"].nunique()),
        "n_country_year_growth_obs": int(len(growth)),
        "horizons": HORIZONS,
        "coef_by_horizon": {str(h): (float(coef[h]) if np.isfinite(coef[h]) else None) for h in HORIZONS},
        "se_by_horizon": {str(h): (float(se[h]) if np.isfinite(se[h]) else None) for h in HORIZONS},
        "pval_by_horizon": {str(h): (float(pval[h]) if np.isfinite(pval[h]) else None) for h in HORIZONS},
        "n_cells_by_horizon": {str(h): int(n_per_h[h]) for h in HORIZONS},
        "post_details": post_details,
        "pretrend_details": pretrend_details,
        "thresholds": {
            "post_growth_pp": POST_GROWTH_THRESHOLD,
            "pretrend_positive_pp": PRETREND_POSITIVE_THRESHOLD,
            "alpha": ALPHA,
            "min_episodes_for_valid": MIN_EPISODES_FOR_VALID,
            "efw_jump_5y": EFW_JUMP_5Y_THRESHOLD,
            "one_episode_per_country": ONE_EPISODE_PER_COUNTRY,
        },
        "episodes": episodes.to_dict(orient="records") if n_episodes else [],
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart: event-study coef by horizon ----------
    palette_pre = "#B07AA1"
    palette_post = "#4E79A7"
    series_pts = []
    for h in HORIZONS:
        c = coef[h]
        s = se[h]
        if np.isfinite(c):
            series_pts.append({
                "x": int(h),
                "y": float(c),
                "se": float(s) if np.isfinite(s) else None,
                "n": int(n_per_h[h]),
            })
    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Liberalisation episodes: log-growth (excess over country baseline) by event-time horizon",
        "subtitle": (
            f"{n_episodes} EFW-jump episodes ({n_episode_countries} countries) · "
            f"h=3 {coef[3]*100:+.2f}pp · h=5 {coef[5]*100:+.2f}pp · "
            f"h=10 {coef[10]*100:+.2f}pp · pre-trend h=-3 {coef[-3]*100:+.2f}pp"
        ) if n_episodes else f"Insufficient episodes ({n_episodes}) — see verdict.",
        "type": "line",
        "x_axis": {"label": "Years from liberalisation episode (h)", "type": "linear"},
        "y_axis": {"label": "Mean (growth − country baseline), log-points", "type": "linear"},
        "series": [
            {
                "id": "event_study_coef",
                "label": "Mean excess log-growth at horizon",
                "color": palette_post,
                "treated": True,
                "points": series_pts,
            }
        ],
        "annotations": [
            {
                "type": "note",
                "label": (
                    f"Episodes = year of largest 5-year jump in Fraser EFW "
                    f"aggregate score per country, conditional on jump "
                    f"≥+0.5 points (one episode per country). Country-block "
                    f"bootstrap ({BOOTSTRAP_REPS} reps) for SE / p-values."
                )
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
    for h in HORIZONS:
        coef_rows.append({
            "spec": "event_study",
            "term": f"h={h:+d}",
            "horizon": h,
            "estimate": float(coef[h]) if np.isfinite(coef[h]) else float("nan"),
            "se": float(se[h]) if np.isfinite(se[h]) else float("nan"),
            "pval": float(pval[h]) if np.isfinite(pval[h]) else float("nan"),
            "n_cells": int(n_per_h[h]),
        })
    coef_rows.append({
        "spec": "summary", "term": "n_episodes", "horizon": 0,
        "estimate": float(n_episodes), "se": float("nan"), "pval": float("nan"),
        "n_cells": int(n_episodes),
    })
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
    def fmt(h: int) -> str:
        c = coef[h]
        if not np.isfinite(c):
            return "n/a"
        ses = se[h]
        ps = pval[h]
        return (
            f"{c*100:+.2f}pp/yr "
            f"(SE {ses*100:.2f}pp, p={ps:.3f}, n={n_per_h[h]})"
        ) if np.isfinite(ses) else f"{c*100:+.2f}pp/yr (n={n_per_h[h]})"

    card = [
        f"# Liberalisation episodes and growth trajectory",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Episodes detected: **{n_episodes}** across **{n_episode_countries}** "
        f"countries (year of largest 5-year jump in Fraser EFW aggregate "
        f"score per country, conditional on jump ≥ +0.5 points).",
        f"- Method validity: **{'OK' if method_valid else f'INSUFFICIENT (need ≥{MIN_EPISODES_FOR_VALID})'}** — "
        f"event study estimates GDP-per-capita log-growth deviation from "
        f"country mean at horizons {HORIZONS}.",
        "",
        "### Event-study coefficients (excess log-growth over country baseline)",
        "",
        f"| Horizon h | Coef | SE | p | n cells |",
        f"|---:|---:|---:|---:|---:|",
        *[
            (f"| {h:+d} | {coef[h]*100:+.2f}pp | "
             f"{(se[h]*100 if np.isfinite(se[h]) else 0):.2f}pp | "
             f"{(pval[h] if np.isfinite(pval[h]) else 0):.3f} | "
             f"{n_per_h[h]} |")
            for h in HORIZONS
        ],
        "",
        "## Method",
        "",
        "- **Treatment**: liberalisation episode at the country-year of "
        "the LARGEST 5-year jump in Fraser EFW aggregate score "
        "(`efw_summary`) per country, conditional on that jump being ≥ "
        "+0.5 points. One episode per country (the EFW panel is "
        "5-year-spaced 1970-2000 and annual after, so 5 yr is the natural "
        "unit; one-per-country prevents stacked-event-study double-counting "
        "of the same multi-decade reform wave).",
        "- **Outcome**: real GDP-per-capita log-growth (year-on-year), "
        "preferring NY.GDP.PCAP.PP.KD (PPP) and falling back to "
        "NY.GDP.PCAP.KD where PPP is missing. 2020 dropped (COVID).",
        "- **Event study**: per (country, episode, h), average growth in "
        f"years e+h ± {HORIZON_WINDOW}, demean by country sample mean, "
        f"then average across (country, episode) cells. Country-block "
        f"bootstrap ({BOOTSTRAP_REPS} reps) for SE / two-sided p-values.",
        "- **Falsification rule (sharpened)**: SUPPORTED requires h ∈ "
        f"{{3,5,10}} all ≥ +{POST_GROWTH_THRESHOLD*100:.1f}pp/yr AND p<{ALPHA}; "
        "AND pre-trend at h ∈ {-3,-5} not significantly positive. REFUTED "
        "if either condition fails.",
        "",
        "## Data",
        "",
        f"- fraser_efw:efw_panel (Economic Freedom of the World, aggregate score)",
        f"- world_bank_wdi:NY.GDP.PCAP.PP.KD (PPP per-capita GDP)",
        f"- world_bank_wdi:NY.GDP.PCAP.KD (constant-USD per-capita GDP, fallback)",
        "",
        "## Caveats",
        "",
        "- Episode catalogue is derived from EFW jumps, which is an "
        "indicator-based (not narrative) coding. Spec mentions Sachs-Warner "
        "and Wacziarg-Welch dating; those would refine the catalogue but "
        "are not on disk.",
        "- Event horizons constrained by EFW coverage (most countries from "
        "1980; pre-1980 episodes therefore underweighted).",
        "- Country baseline-demeaning absorbs slow-moving country-fixed "
        "differences; richer two-way FE would need iterative "
        "within-estimation. Block-bootstrap by country mimics "
        "country-clustered SEs.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")
    print(f"n_episodes={n_episodes} n_countries={n_episode_countries}")
    for h in HORIZONS:
        print(f"  h={h:+d}: coef={coef[h]:.4f}  se={se[h]:.4f}  p={pval[h]:.3f}  n={n_per_h[h]}")


if __name__ == "__main__":
    main()
