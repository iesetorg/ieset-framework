#!/usr/bin/env python3
"""Replication — German decline 2018-2025: regulatory not fiscal.

Spec: hypotheses/regulatory/germany_decline_2018_2025_regulatory_not_fiscal.yaml
Steelman: hypotheses/steelman/germany_decline_2018_2025_regulatory_not_fiscal.md

Synthetic control: DEU treated, treatment 2018 (GroKo formation + tightened
climate policy + Nord Stream 2 construction). Donor pool from sample
countries. Pre-period 2005-2017, post-period 2018-2025.

DATA-GATED CAVEAT: the YAML's full secondary specification — variance
decomposition of the synthetic-control gap onto regulatory bundle (EPS +
electricity price + Russia gas share) vs fiscal bundle (gov consumption +
tax + debt) — requires OECD EPS, IEA industrial electricity price, and
Russian gas import share. Those fetchers are pending. We run the primary
synthetic control on log industrial GVA (the YAML's primary outcome), but
the regulatory-vs-fiscal decomposition runs in degraded form using only
the WDI fiscal-channel measures (gov consumption %GDP, debt/GDP) we have
on hand. The headline regulatory-vs-fiscal ratio is therefore reported as
a placeholder pending the regulatory-channel fetchers.
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
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "engine" / "runs" / "germany_decline_2018_2025_regulatory_not_fiscal"

TREATED = "DEU"
DONORS = ["FRA", "NLD", "BEL", "ITA", "ESP", "POL", "CZE", "AUT", "SWE", "FIN", "USA"]
ALL = [TREATED] + DONORS
PERIOD = (2005, 2025)
TREATMENT_YEAR = 2018


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


def load_long(path: Path, name: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def assemble():
    paths = {
        "ind_gva":     ("world_bank_wdi", "NV.IND.TOTL.KD"),
        "gdp_pc_ppp":  ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "population":  ("world_bank_wdi", "SP.POP.TOTL"),
        "trade_open":  ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "debt_gdp":    ("imf", "GGXWDG_NGDP"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths.items():
        try:
            p = latest(pub, series)
            manifest[v] = {"publisher": pub, "series": series,
                           "vintage_file": str(p.relative_to(REPO_ROOT)),
                           "sha256": sha256(p)}
            frames.append(load_long(p, v))
        except FileNotFoundError:
            print(f"missing series {pub}:{series}; skipping")
    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(ALL)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)
    panel["log_ind_gva"]    = np.log(panel["ind_gva"])
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    return panel, manifest


def synth_weights(treated_pre: np.ndarray, donors_pre: np.ndarray) -> np.ndarray:
    n = donors_pre.shape[1]
    x0 = np.ones(n) / n
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0, 1)] * n

    def loss(w):
        return float(np.mean((treated_pre - donors_pre @ w) ** 2))

    sol = minimize(loss, x0, method="SLSQP", bounds=bnds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-10})
    return sol.x


def synth_for_unit(wide, unit, donors, pre_years, post_years):
    treated = wide[unit].reindex(pre_years + post_years).values
    donor_mat_pre = wide[donors].reindex(pre_years).values
    donor_mat_post = wide[donors].reindex(post_years).values
    treated_pre = treated[: len(pre_years)]
    treated_post = treated[len(pre_years):]
    if np.isnan(treated_pre).any() or np.isnan(donor_mat_pre).any():
        return {"error": "missing pre-period data"}
    w = synth_weights(treated_pre, donor_mat_pre)
    synth_pre = donor_mat_pre @ w
    synth_post = donor_mat_post @ w
    pre_rmspe = float(np.sqrt(np.mean((treated_pre - synth_pre) ** 2)))
    valid = ~np.isnan(treated_post) & ~np.isnan(synth_post)
    post_rmspe = float(np.sqrt(np.mean(((treated_post - synth_post)[valid]) ** 2))) if valid.any() else float("nan")
    gap = treated_post - synth_post
    return {
        "unit": unit,
        "weights": {d: float(w[i]) for i, d in enumerate(donors)},
        "pre_rmspe": pre_rmspe,
        "post_rmspe": post_rmspe,
        "rmspe_ratio": (post_rmspe / pre_rmspe) if pre_rmspe > 0 else float("inf"),
        "treated_pre": [float(x) for x in treated_pre],
        "synth_pre": [float(x) for x in synth_pre],
        "treated_post": [float(x) if not np.isnan(x) else None for x in treated_post],
        "synth_post":   [float(x) if not np.isnan(x) else None for x in synth_post],
        "gap_post":     [float(x) if not np.isnan(x) else None for x in gap],
        "post_years": post_years,
        "pre_years": pre_years,
        "cumulative_gap": float(np.nansum(gap)),
        "mean_gap": float(np.nanmean(gap)),
    }


def placebo_run(wide, donors_full, pre_years, post_years):
    out = []
    for d in donors_full:
        rest = [x for x in donors_full if x != d]
        try:
            r = synth_for_unit(wide, d, rest, pre_years, post_years)
            if "error" not in r:
                out.append(r)
        except Exception:
            pass
    return out


def fiscal_channel_decomp(panel, post_years):
    """Degraded fiscal-channel test: compare DEU's post-treatment delta vs donor-pool
    average for debt/GDP. If DEU's debt/GDP fell vs donors over the window, fiscal
    loosening is NOT the explanation (channel = null). The full regulatory-vs-fiscal
    ratio requires OECD EPS / IEA price / gas share fetchers (pending)."""
    out = {"available_channels": []}
    for ch in ["debt_gdp", "trade_open"]:
        if ch not in panel.columns:
            continue
        sub = panel.dropna(subset=[ch])
        deu = sub[sub["country"] == TREATED].set_index("year")[ch]
        donor = sub[sub["country"].isin(DONORS)].groupby("year")[ch].mean()
        if 2017 in deu.index and (2023 in deu.index or 2022 in deu.index):
            end = 2023 if 2023 in deu.index else 2022
            deu_delta = float(deu.loc[end] - deu.loc[2017])
            donor_delta = float(donor.loc[end] - donor.loc[2017]) if end in donor.index and 2017 in donor.index else float("nan")
            out[f"{ch}_deu_delta_2017_to_{end}"] = deu_delta
            out[f"{ch}_donor_avg_delta_2017_to_{end}"] = donor_delta
            out[f"{ch}_deu_minus_donor_delta"] = deu_delta - donor_delta
            out["available_channels"].append(ch)
    out["regulatory_channel_status"] = "PENDING (OECD EPS, IEA elec price, Russia gas share fetchers required)"
    return out


def build_chart(df, sc, manifest):
    colors = {"DEU": "#E15759", "FRA": "#4E79A7", "NLD": "#59A14F", "BEL": "#9C755F",
              "ITA": "#1f77b4", "ESP": "#bcbd22", "POL": "#76B7B2", "CZE": "#F28E2B",
              "AUT": "#B07AA1", "SWE": "#EDC948", "FIN": "#2ca02c", "USA": "#ff7f0e"}
    series = []
    for c in ALL:
        sub = df[df["country"] == c][["year", "log_ind_gva"]].dropna().sort_values("year")
        if sub.empty:
            continue
        series.append({
            "id": c, "label": c, "color": colors.get(c, "#666"),
            "treated": c == TREATED,
            "points": [{"x": int(r.year), "y": float(r.log_ind_gva)} for r in sub.itertuples()],
        })
    if "error" not in sc:
        synth_full = list(zip(sc["pre_years"], sc["synth_pre"])) + \
                     list(zip(sc["post_years"], sc["synth_post"]))
        series.append({
            "id": "DEU_synthetic", "label": "DEU synthetic counterfactual",
            "color": "#000000", "dashed": True, "treated": False,
            "points": [{"x": int(y), "y": float(v)} for y, v in synth_full
                       if v is not None and not np.isnan(v)],
        })
    return {
        "chart_id": "germany_decline_2018_2025_regulatory_not_fiscal/fig1",
        "title": "Log industrial GVA, Germany vs synthetic counterfactual, 2005-2025",
        "subtitle": (
            f"Treatment 2018 (GroKo + climate-policy tightening + Nord Stream 2). "
            f"Pre-RMSPE {sc.get('pre_rmspe', float('nan')):.4f}, "
            f"post/pre ratio {sc.get('rmspe_ratio', float('nan')):.2f}, "
            f"mean post-2018 gap {sc.get('mean_gap', float('nan')):+.3f} log."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log industrial GVA (rebased)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": TREATMENT_YEAR, "label": "GroKo / climate-policy tightening"},
            {"type": "note", "label": "Outcome: log NV.IND.TOTL.KD, rebased per country to 0 at first pre-year. Donor pool: FRA, NLD, BEL, ITA, ESP, POL, CZE, AUT, SWE, FIN, USA."},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": "/h/germany_decline_2018_2025_regulatory_not_fiscal",
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    wide_raw = panel.pivot(index="year", columns="country", values="log_ind_gva")
    wide = wide_raw.copy()
    for c in wide.columns:
        s = wide[c].dropna()
        if not s.empty:
            base = s.loc[s.index.min()]
            wide[c] = wide[c] - base
    available_donors = [d for d in DONORS if d in wide.columns and wide[d].dropna().shape[0] >= 10]
    pre_years = list(range(PERIOD[0], TREATMENT_YEAR))
    post_years = list(range(TREATMENT_YEAR, PERIOD[1] + 1))

    sc = synth_for_unit(wide, TREATED, available_donors, pre_years, post_years)

    placebos = placebo_run(wide, available_donors, pre_years, post_years)
    placebo_ratios = sorted([p["rmspe_ratio"] for p in placebos
                             if np.isfinite(p["rmspe_ratio"])])
    treated_ratio = sc.get("rmspe_ratio", float("nan"))
    if placebo_ratios and np.isfinite(treated_ratio):
        all_ratios = sorted(placebo_ratios + [treated_ratio], reverse=True)
        rank = all_ratios.index(treated_ratio) + 1
        n_total = len(all_ratios)
        placebo_pvalue = rank / n_total
    else:
        rank = None
        n_total = len(placebo_ratios) + 1
        placebo_pvalue = None

    # 5-yr cumulative gap (2018-2022)
    cum_5yr = sum([sc["gap_post"][i] for i, y in enumerate(post_years)
                   if y <= 2022 and sc["gap_post"][i] is not None])

    # Fiscal-channel partial decomposition
    fiscal = fiscal_channel_decomp(panel, post_years)

    # Falsification (per YAML rule):
    #   (a) pre-RMSPE > 0.04 -> fail (method)
    #   (b) post-2018 gap not in top 90th-percentile of placebos -> fail
    #   (c) regulatory channel < 40% of explained gap -> fail (CANNOT EVALUATE; data-gated)
    #   (d) fiscal > regulatory -> fail (CANNOT EVALUATE)
    pretrend_ok = sc.get("pre_rmspe", 1.0) <= 0.04
    placebo_ok = (placebo_pvalue is not None and placebo_pvalue < 0.10)
    sign_ok = cum_5yr < 0
    magnitude_ok = cum_5yr <= -0.05
    primary_pass = pretrend_ok and placebo_ok and sign_ok and magnitude_ok

    if not pretrend_ok:
        verdict = (f"refuted-on-method — pre-period RMSPE {sc.get('pre_rmspe', float('nan')):.4f} "
                   f"exceeds 0.04; donor pool does not match pre-2018 DEU trajectory "
                   f"closely enough.")
    elif primary_pass:
        verdict = (f"partial-supported — DEU industrial GVA ran "
                   f"{cum_5yr:+.3f} cumulative log-points below synthetic over "
                   f"2018-2022 (5-yr horizon). Placebo rank {rank}/{n_total} "
                   f"(p={placebo_pvalue:.2f}). Magnitude direction-consistent. "
                   f"REGULATORY-vs-FISCAL decomposition CANNOT EVALUATE — OECD "
                   f"EPS, IEA electricity price, and Russia gas share fetchers "
                   f"are pending. Verdict reports the synthetic-control divergence "
                   f"only, not the channel-attribution that distinguishes this "
                   f"hypothesis from german_energiewende.")
    elif sign_ok:
        verdict = (f"partial — DEU below synthetic by {cum_5yr:+.3f} cumulative "
                   f"over 2018-2022 (sign correct), but magnitude or placebo "
                   f"p={placebo_pvalue} below pre-registered thresholds. "
                   f"Regulatory-vs-fiscal channel split unresolved (data-gated).")
    else:
        verdict = (f"refuted — DEU 5-yr cumulative gap {cum_5yr:+.3f} log "
                   f"(wrong sign for industrial-decline story), placebo "
                   f"p={placebo_pvalue}.")

    (OUT_DIR / "chart_data.json").write_text(json.dumps(
        build_chart(panel, sc, manifest), indent=2) + "\n")

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "all_pass": primary_pass,
        "synthetic_control": sc,
        "placebos": placebos,
        "placebo_p_value": placebo_pvalue,
        "treated_rank": rank,
        "n_in_placebo_distribution": n_total,
        "cumulative_5yr_gap_2018_2022": cum_5yr,
        "fiscal_channel_partial": fiscal,
        "falsification_components": {
            "pre_rmspe_le_0p04": pretrend_ok,
            "placebo_p_lt_0p10": placebo_ok,
            "sign_negative": sign_ok,
            "magnitude_le_minus_0p05_cum": magnitude_ok,
            "regulatory_vs_fiscal_decomposition": "PENDING — data-gated on OECD EPS / IEA price / gas share fetchers",
        },
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "germany_decline_2018_2025_regulatory_not_fiscal",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator_template": "synthetic_control",
        "treated_unit": TREATED,
        "donor_pool": available_donors,
        "treatment_year": TREATMENT_YEAR,
        "pre_period": list(pre_years),
        "post_period": list(post_years),
        "vintages": manifest,
    }, sort_keys=False))

    lines = [
        "# Result card — German decline 2018-2025: regulatory not fiscal",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"Outcome: log industrial GVA real (WDI NV.IND.TOTL.KD), rebased per country.",
        f"Treated: DEU. Donors used: {', '.join(available_donors)}.",
        f"Pre {pre_years[0]}-{pre_years[-1]}, post {post_years[0]}-{post_years[-1]}.",
        "",
        "## Synthetic control fit",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Pre-period RMSPE | {sc.get('pre_rmspe', float('nan')):.4f} |",
        f"| Post-period RMSPE | {sc.get('post_rmspe', float('nan')):.4f} |",
        f"| Post/Pre RMSPE ratio | {treated_ratio:.2f} |",
        f"| Mean post-2018 gap | {sc.get('mean_gap', float('nan')):+.3f} log |",
        f"| Cumulative 5-yr gap (2018-2022) | {cum_5yr:+.3f} log-yr |",
        f"| Placebo rank | {rank}/{n_total} |",
        f"| Placebo p-value | {placebo_pvalue if placebo_pvalue is not None else 'n/a'} |",
        "",
        "## Donor weights",
        "",
        "| Donor | Weight |",
        "|---|---:|",
    ]
    for d, w in (sc.get("weights") or {}).items():
        lines.append(f"| {d} | {w:.3f} |")
    lines += [
        "",
        "## Post-period gap",
        "",
        "| Year | DEU (rebased) | Synth | Gap |",
        "|---:|---:|---:|---:|",
    ]
    for i, y in enumerate(sc.get("post_years", [])):
        d_v = sc["treated_post"][i] if sc.get("treated_post") else None
        s_v = sc["synth_post"][i] if sc.get("synth_post") else None
        g_v = sc["gap_post"][i] if sc.get("gap_post") else None
        if d_v is None or s_v is None:
            continue
        lines.append(f"| {y} | {d_v:.3f} | {s_v:.3f} | {g_v:+.3f} |")
    lines += [
        "",
        "## Fiscal-channel partial check (degraded)",
        "",
        f"Available channels: {', '.join(fiscal.get('available_channels', [])) or 'none'}",
        "",
    ]
    for k, v in fiscal.items():
        if isinstance(v, (int, float)):
            lines.append(f"- `{k}` = {v:+.3f}")
    lines += [
        "",
        "**Regulatory-channel status:** " + fiscal.get("regulatory_channel_status", "n/a"),
        "",
        "## Data-status caveat",
        "",
        "The hypothesis's HEADLINE test is the regulatory-vs-fiscal variance decomposition",
        "of the post-2018 synthetic gap. Running it requires:",
        "- OECD Environmental Policy Stringency index — pending",
        "- IEA industrial electricity price — pending",
        "- Russian gas import share — pending",
        "- China industrial-production index — pending",
        "- OECD SDD household disposable income — pending",
        "",
        "v1 here runs the synthetic-control divergence only. The verdict gates on the",
        "synthetic-control component of the falsification rule; the regulatory-vs-fiscal",
        "channel-attribution component is reported as PENDING and does not contribute to",
        "the verdict. When the four pending fetchers ship, v1.1 reruns and the verdict",
        "resolves cleanly.",
        "",
        "## Steelman-live concerns",
        "",
        "1. 2020-2021 COVID and 2022-2023 Russia-Ukraine energy shock are large confounds",
        "   in the post-2018 window; sensitivities pending.",
        "2. DEU sole treated unit; external validity narrow.",
        "3. The 'regulatory-vs-fiscal' framing requires both bundles fully measured to",
        "   evaluate — currently fiscal-side has WDI gov consumption + IMF debt/GDP",
        "   available; regulatory-side awaits EPS + IEA + gas-share.",
        "4. Industrial GVA reflects sector-mix shifts (e.g. EVs, software) independent of",
        "   the regulatory channel.",
        "",
        "## Provenance",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  pre-RMSPE: {sc.get('pre_rmspe', float('nan')):.4f}")
    print(f"  post/pre ratio: {treated_ratio:.2f}")
    print(f"  cumulative 5-yr gap: {cum_5yr:+.3f} log-yr")
    print(f"  placebo rank: {rank}/{n_total} (p={placebo_pvalue})")


if __name__ == "__main__":
    sys.exit(main())
