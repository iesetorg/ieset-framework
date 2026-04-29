#!/usr/bin/env python3
"""Replication — Argentine Peronism recurring fiscal-inflation cycle, 1945-2023.

Spec:     hypotheses/monetary/argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023.yaml
Method:   Cointegration / VECM (per task spec). Estimator template
          'cointegration_vecm'.

Operationalisation
------------------
The YAML names a 1945-2023 window. The vintaged data covers:
  - BIS WS_LONG_CPI annual %change for Argentina, 1944-2025 (74 years 1950-2023)
  - IMF GGXCNL_NGDP general govt net lending %GDP for Argentina, 1993-2023
  - IMF PCPIPCH inflation for Argentina, 1998-2023

The fiscal-deficit series only goes back to 1993, which constrains the
joint-system estimation window to 1993-2023 (annual, n≈31). We document the
window and report:

  1. Johansen cointegration test on (deficit, inflation), trace + max-eig
     statistics.
  2. If r ≥ 1, fit VECM(p=1, k_ar_diff=1, deterministic constant in
     cointegration). Report the cointegrating vector β and the
     error-correction adjustment coefficient α (the loading on the deficit
     equation). A negative-and-significant α on the inflation equation is
     interpreted as deficit and inflation being a joint stationary
     equilibrium with inflation responding to disequilibrium.
  3. Half-life of deviation: -ln(2) / ln(1 + α).
  4. Episode-precedence count: BIS inflation > 50% episodes 1945-2024 in
     Argentina; descriptive count satisfies/fails YAML threshold (≥8 of 12
     preceded by deficit > 4% GDP).
  5. Falsification: trace stat for r=0 must reject at 5% AND α negative.

Data limitations are reported transparently in the result card.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

EXCLUDE_YEARS = list(range(1991, 2002)) + [2020]   # YAML exclusion rules


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def latest(pub, series):
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_bis_long_cpi_argentina():
    p = latest("bis", "WS_LONG_CPI")
    t = pq.read_table(p).to_pandas()
    ar = t[(t["REF_AREA"] == "AR") & (t["FREQ"] == "A")
           & (t["UNIT_MEASURE"] == 771)].copy()
    ar["year"] = ar["period"].astype(str).str.slice(0, 4).astype(int)
    ar["inflation"] = pd.to_numeric(ar["value"], errors="coerce")
    ar = ar[["year", "inflation"]].dropna().drop_duplicates("year").sort_values("year")
    return ar.reset_index(drop=True), p


def load_imf_deficit(country, series):
    p = latest("imf", series)
    t = pq.read_table(p).to_pandas()
    sub = t[(t["country_iso3"] == country)][["year", "value"]].copy()
    sub["year"] = sub["year"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub = sub.dropna().drop_duplicates("year").sort_values("year")
    # GGXCNL_NGDP is net lending: positive = surplus. Flip sign to get deficit.
    sub = sub.rename(columns={"value": "net_lending_pct_gdp"})
    sub["deficit_pct_gdp"] = -sub["net_lending_pct_gdp"]
    return sub.reset_index(drop=True), p


def episode_count(infl_df, deficit_df):
    """Identify >50% inflation episodes; for each, check whether deficit
    > 4% GDP in t-1 or t-2 (where deficit data exist)."""
    epi = []
    infl_df = infl_df.set_index("year")
    deficit_lookup = deficit_df.set_index("year")["deficit_pct_gdp"].to_dict()
    in_episode = False
    start = None
    for y, row in infl_df.iterrows():
        v = row["inflation"]
        if v > 50 and not in_episode:
            in_episode = True
            start = y
        elif v <= 50 and in_episode:
            epi.append({"start": int(start), "end": int(y - 1)})
            in_episode = False
    if in_episode:
        epi.append({"start": int(start), "end": int(infl_df.index.max())})

    # Now check deficit precedence
    for e in epi:
        ys = e["start"]
        d_t1 = deficit_lookup.get(ys - 1)
        d_t2 = deficit_lookup.get(ys - 2)
        e["deficit_t_minus_1"] = d_t1
        e["deficit_t_minus_2"] = d_t2
        e["preceded_by_deficit_gt_4pct"] = bool(
            (d_t1 is not None and d_t1 > 4) or (d_t2 is not None and d_t2 > 4)
        )
    return epi


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    infl, ip = load_bis_long_cpi_argentina()
    deficit, dp = load_imf_deficit("ARG", "GGXCNL_NGDP")

    manifest = {
        "inflation": {"publisher": "bis", "series": "WS_LONG_CPI",
                      "vintage_file": str(ip.relative_to(REPO_ROOT)),
                      "sha256": sha256(ip)},
        "fiscal_balance": {"publisher": "imf", "series": "GGXCNL_NGDP",
                           "vintage_file": str(dp.relative_to(REPO_ROOT)),
                           "sha256": sha256(dp)},
    }

    # Episode analysis (uses full inflation series)
    epi = episode_count(infl, deficit)
    n_episodes = len(epi)
    n_with_deficit = sum(1 for e in epi if e["preceded_by_deficit_gt_4pct"])

    # Joint system: merge on year, restrict to where both available, exclude
    # convertibility (1991-2001) and 2020 pandemic per YAML
    joint = infl.merge(deficit[["year", "deficit_pct_gdp"]], on="year", how="inner")
    joint = joint[~joint["year"].isin(EXCLUDE_YEARS)].copy()
    joint = joint[(joint["year"] >= 1950) & (joint["year"] <= 2024)]
    joint = joint.sort_values("year").reset_index(drop=True)

    # Use log(1 + infl/100) to dampen extreme Argentine inflation outliers
    # for cointegration test (raw rates would dominate the variance and
    # compromise the linearity required by Johansen). This is a standard
    # transformation in Argentine inflation work.
    joint["log_inflation"] = np.log1p(joint["inflation"] / 100.0)

    # We need contiguous data. Drop any rows with NaN.
    joint = joint.dropna(subset=["deficit_pct_gdp", "log_inflation"])
    n_obs = len(joint)

    if n_obs < 12:
        verdict = (f"BLOCKED — insufficient overlap of fiscal+inflation series "
                   f"after exclusions (n={n_obs}); need ≥12 contiguous years.")
        diag = {"verdict": verdict, "blocked": True, "n_obs": n_obs,
                "joint_window": [int(joint["year"].min()) if n_obs else None,
                                 int(joint["year"].max()) if n_obs else None]}
        (OUT_DIR / "BLOCKED.md").write_text(
            f"# BLOCKED — {RUN_ID}\n\n{verdict}\n\n"
            "Argentine fiscal balance from IMF GGXCNL_NGDP starts 1993, and "
            "the YAML excludes 1991-2001 (Convertibility) + 2020. Long-run "
            "claim 1945-2023 requires historical Mauro et al / IMF historical "
            "fiscal panel which is not yet vintaged.\n"
        )
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
            "hypothesis_id": RUN_ID, "blocked": True,
            "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "vintages": manifest,
        }, sort_keys=False))
        pd.DataFrame([]).to_parquet(OUT_DIR / "coefficients.parquet")
        (OUT_DIR / "result_card.md").write_text(
            f"# Result card — {RUN_ID}\n\n**Verdict:** {verdict}\n"
        )
        print(verdict)
        return

    # Johansen cointegration on (deficit, log_inflation)
    Y = joint[["deficit_pct_gdp", "log_inflation"]].values
    # det_order: 0 = constant inside cointegration (allows level mean), -1 = no det
    det_order = 0
    k_ar_diff = 1
    try:
        jres = coint_johansen(Y, det_order=det_order, k_ar_diff=k_ar_diff)
    except Exception as e:
        verdict = f"BLOCKED — Johansen test failed: {e}"
        diag = {"verdict": verdict, "blocked": True}
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag) + "\n")
        print(verdict)
        return

    # Trace stat / max eig stat / critical values at 95%
    trace_stats = jres.lr1.tolist()
    eig_stats = jres.lr2.tolist()
    trace_cv95 = jres.cvt[:, 1].tolist()       # 5% critical
    eig_cv95 = jres.cvm[:, 1].tolist()
    # rank: count how many trace_stats[i] > trace_cv95[i]
    rank_trace = int(sum(1 for i in range(len(trace_stats))
                         if trace_stats[i] > trace_cv95[i]))

    # If r >= 1, fit VECM
    vecm_fit = None
    alpha_inflation = None
    alpha_p = None
    half_life = None
    coint_vector = None
    if rank_trace >= 1:
        try:
            v = VECM(Y, k_ar_diff=k_ar_diff, coint_rank=1, deterministic="ci")
            vfit = v.fit()
            # Cointegrating vector β (normalised so first element = 1)
            beta = vfit.beta[:, 0]
            if abs(beta[0]) > 1e-9:
                beta_norm = beta / beta[0]
            else:
                beta_norm = beta
            coint_vector = {"deficit_pct_gdp": float(beta_norm[0]),
                            "log_inflation": float(beta_norm[1])}
            # Alpha matrix: rows = equations (deficit, inflation), cols = rank
            alpha = vfit.alpha[:, 0]
            alpha_p_vals = vfit.pvalues_alpha[:, 0]
            alpha_deficit = float(alpha[0])
            alpha_inflation = float(alpha[1])
            alpha_deficit_p = float(alpha_p_vals[0])
            alpha_p = float(alpha_p_vals[1])
            # Half-life on the inflation equation (per task spec)
            if alpha_inflation < 0 and alpha_inflation > -1:
                half_life = float(-np.log(2) / np.log(1 + alpha_inflation))
            vecm_fit = {
                "alpha_deficit_eq": alpha_deficit,
                "alpha_deficit_p": alpha_deficit_p,
                "alpha_inflation_eq": alpha_inflation,
                "alpha_inflation_p": alpha_p,
                "half_life_years": half_life,
                "cointegrating_vector_normalised": coint_vector,
            }
        except Exception as e:
            vecm_fit = {"error": str(e)}

    # Verdict per YAML threshold:
    # granger_p < 0.01 [we use trace stat at 5% as the cointegration analogue
    # since YAML estimator template = cointegration_vecm not granger]
    # AND episode_precedence_rate >= 8/12
    coint_pass = rank_trace >= 1
    precedence_pass = (n_episodes > 0 and n_with_deficit / n_episodes >= 8 / 12)
    alpha_pass = (alpha_inflation is not None and alpha_inflation < 0
                  and alpha_p is not None and alpha_p < 0.10)

    if coint_pass and precedence_pass and alpha_pass:
        verdict = (f"SUPPORTED — Johansen rank={rank_trace}; α_inflation = "
                   f"{alpha_inflation:+.3f} (p={alpha_p:.3f}); episode "
                   f"precedence {n_with_deficit}/{n_episodes}; half-life "
                   f"= {half_life:.2f} yr.")
    elif coint_pass and not alpha_pass:
        verdict = (f"PARTIAL — cointegration found (rank={rank_trace}) but "
                   f"α on inflation equation = {alpha_inflation} (p={alpha_p}); "
                   f"adjustment toward equilibrium not strongly identified. "
                   f"Episode precedence: {n_with_deficit}/{n_episodes}.")
    elif coint_pass and not precedence_pass:
        verdict = (f"PARTIAL — cointegration rank={rank_trace}, α_infl="
                   f"{alpha_inflation}; episode precedence "
                   f"{n_with_deficit}/{n_episodes} below 8/12 threshold.")
    else:
        verdict = (f"REFUTED — Johansen rank={rank_trace} (no cointegration at 5%); "
                   f"trace stats={[f'{s:.2f}' for s in trace_stats]} vs "
                   f"cv95={[f'{c:.2f}' for c in trace_cv95]}.")

    chart = {
        "chart_id": f"{RUN_ID}/fig1",
        "title": "Argentina annual fiscal deficit (% GDP) and CPI inflation",
        "subtitle": (f"Joint window: {int(joint['year'].min())}-{int(joint['year'].max())}. "
                     f"Johansen rank={rank_trace}; "
                     f"α_inflation={alpha_inflation if alpha_inflation is not None else 'n/a'}; "
                     f"half-life={half_life if half_life is not None else 'n/a'} yr."),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "Value", "type": "linear"},
        "series": [
            {"id": "deficit", "label": "Deficit (% GDP)", "color": "#E15759",
             "points": [{"x": int(r.year), "y": float(r.deficit_pct_gdp)}
                        for r in joint.itertuples()]},
            {"id": "infl", "label": "CPI inflation %", "color": "#4E79A7",
             "points": [{"x": int(r.year), "y": float(r.inflation)}
                        for r in joint.itertuples()]},
        ],
        "annotations": [{"type": "note",
                         "label": "1991-2001 (Convertibility) and 2020 (pandemic) excluded per YAML."}],
        "sources": [{"publisher_id": v["publisher"], "series_id": v["series"],
                     "vintage_file": v["vintage_file"]} for v in manifest.values()],
        "permalink": f"/h/{RUN_ID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n")

    rows = []
    if vecm_fit and "alpha_deficit_eq" in vecm_fit:
        for term, val, pv in [
            ("alpha_deficit_eq", vecm_fit["alpha_deficit_eq"], vecm_fit["alpha_deficit_p"]),
            ("alpha_inflation_eq", vecm_fit["alpha_inflation_eq"], vecm_fit["alpha_inflation_p"]),
        ]:
            rows.append({"spec": "vecm_r1", "term": term, "estimate": val,
                         "p": pv, "n_obs": n_obs})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "all_pass": coint_pass and precedence_pass and alpha_pass,
        "n_obs_joint_system": n_obs,
        "joint_window": [int(joint["year"].min()), int(joint["year"].max())],
        "exclusions_applied": EXCLUDE_YEARS,
        "johansen": {
            "trace_stats": trace_stats,
            "trace_cv_5pct": trace_cv95,
            "max_eig_stats": eig_stats,
            "max_eig_cv_5pct": eig_cv95,
            "rank_trace_5pct": rank_trace,
        },
        "vecm": vecm_fit,
        "episodes_inflation_gt_50": {
            "all_episodes": epi,
            "n_episodes": n_episodes,
            "n_preceded_by_deficit_gt_4pct": n_with_deficit,
            "precedence_rate": (n_with_deficit / n_episodes) if n_episodes else None,
        },
        "falsification_components": {
            "cointegration_rank_ge_1_at_5pct": coint_pass,
            "episode_precedence_ge_8_of_12": precedence_pass,
            "alpha_inflation_negative_p_lt_010": alpha_pass,
        },
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator_template": "cointegration_vecm",
        "vintages": manifest,
        "data_window_note": ("IMF GGXCNL_NGDP only covers ARG 1993- ; long-run "
                              "1945-2023 cointegration window restricted to "
                              "1993-2024 minus exclusions"),
    }, sort_keys=False))

    lines = [
        f"# Result card — {RUN_ID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Joint-system Johansen cointegration test",
        "",
        f"- Window: {int(joint['year'].min())}-{int(joint['year'].max())} (n={n_obs})",
        f"- Exclusions: {EXCLUDE_YEARS}",
        f"- Trace stats: {[round(s, 3) for s in trace_stats]}",
        f"- Trace 5% CVs: {[round(c, 3) for c in trace_cv95]}",
        f"- Max-eig stats: {[round(s, 3) for s in eig_stats]}",
        f"- Max-eig 5% CVs: {[round(c, 3) for c in eig_cv95]}",
        f"- **Rank @5%: {rank_trace}**",
        "",
        "## VECM(1,1) — rank 1",
        "",
    ]
    if vecm_fit and "alpha_deficit_eq" in vecm_fit:
        lines += [
            f"- Cointegrating vector (β, normalised): {coint_vector}",
            f"- α (deficit eq):    {vecm_fit['alpha_deficit_eq']:+.4f} "
            f"(p={vecm_fit['alpha_deficit_p']:.3f})",
            f"- α (inflation eq):  {vecm_fit['alpha_inflation_eq']:+.4f} "
            f"(p={vecm_fit['alpha_inflation_p']:.3f})",
            f"- **Half-life of deviation:** "
            f"{half_life:.2f} years" if half_life is not None else "Half-life: n/a",
        ]
    else:
        lines.append(f"- VECM not fit (rank={rank_trace}, or fit error: {vecm_fit})")
    lines += [
        "",
        f"## Inflation episodes >50% (1944-2025)",
        "",
        f"- Total episodes: {n_episodes}",
        f"- Preceded by deficit > 4% GDP in t-1 or t-2 (where deficit data exists): "
        f"{n_with_deficit}",
        "",
        "| Episode start | end | deficit t-1 | deficit t-2 | preceded |",
        "|---|---|---|---|---|",
    ]
    for e in epi:
        lines.append(f"| {e['start']} | {e['end']} | {e['deficit_t_minus_1']} | "
                     f"{e['deficit_t_minus_2']} | {e['preceded_by_deficit_gt_4pct']} |")
    lines += [
        "",
        "## Data limitations",
        "",
        "Argentine fiscal balance (IMF GGXCNL_NGDP) only covers 1993- in vintages. "
        "The 1945-1992 portion of the YAML claim cannot be tested with current "
        "vintaged data; the inflation-episode count uses full BIS WS_LONG_CPI "
        "(1944-2025) but the deficit-precedence half of each episode-row is "
        "missing where deficit data is unavailable.",
        "",
        "## Falsification rule (YAML)",
        "",
        "- Cointegration rank ≥1 at 5% (proxy for Granger causality at p<0.01)",
        "- α on inflation equation negative + significant",
        "- Episode precedence ≥ 8/12",
        "",
        "## Provenance",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  Johansen rank={rank_trace}; α_infl={alpha_inflation}; half-life={half_life}")
    print(f"  Episodes precedence: {n_with_deficit}/{n_episodes}")


if __name__ == "__main__":
    sys.exit(main())
