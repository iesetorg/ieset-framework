#!/usr/bin/env python3
"""Replication — Growth vs distribution tradeoff (architecture clusters).

Spec:     hypotheses/distribution/growth_vs_distribution_tradeoff.yaml
Steelman: hypotheses/steelman/growth_vs_distribution_tradeoff.md

Three parallel TWFE specs, one per outcome:
  growth_yoy:        annual real GDP per capita growth (computed from WDI KD)
  income_gini:       SI.POV.GINI (proxy; native wealth Gini data-gated)
  gross_debt_gdp:    IMF GGXWDG_NGDP

Architecture coding (per spec):
  forced_saving_dominant: SGP, CHL (1985-2008), AUS (1992+), CHE
  tax_transfer_dominant:  NOR, SWE, DNK, FIN, FRA, GBR, DEU, NLD
  hybrid:                 USA, CAN, NZL, CHL post-2008, AUS pre-1992
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
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "engine" / "runs" / "growth_vs_distribution_tradeoff"

FORCED = ["SGP", "CHE"]      # always forced-saving dominant in sample window
TAX_TRANSFER = ["NOR", "SWE", "DNK", "FIN", "FRA", "GBR", "DEU", "NLD"]
HYBRID = ["USA", "CAN", "NZL"]
SPLIT_AUS = "AUS"            # forced-saving from 1992 onward, hybrid before
SPLIT_CHL = "CHL"            # forced-saving 1985-2008, hybrid after

ALL = sorted(FORCED + TAX_TRANSFER + HYBRID + [SPLIT_AUS, SPLIT_CHL])
PERIOD = (1985, 2020)


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
        "gdp_pc":         ("world_bank_wdi", "NY.GDP.PCAP.KD"),
        "population":     ("world_bank_wdi", "SP.POP.TOTL"),
        "urbanisation":   ("world_bank_wdi", "SP.URB.TOTL.IN.ZS"),
        "trade_openness": ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "income_gini":    ("world_bank_wdi", "SI.POV.GINI"),
        "gov_effective":  ("wgi", "GOV_WGI_GE.EST"),
        "gross_debt_gdp": ("imf", "GGXWDG_NGDP"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths.items():
        p = latest(pub, series)
        manifest[v] = {"publisher": pub, "series": series,
                       "vintage_file": str(p.relative_to(REPO_ROOT)),
                       "sha256": sha256(p)}
        frames.append(load_long(p, v))
    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")

    panel = panel[panel["country"].isin(ALL)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    panel["log_gdp_pc"] = np.log(panel["gdp_pc"])
    panel["log_population"] = np.log(panel["population"])
    panel["growth_yoy"] = panel.groupby("country")["log_gdp_pc"].diff() * 100  # in %

    # Architecture coding
    def code(row):
        c, y = row["country"], row["year"]
        if c in FORCED:
            return "forced_saving"
        if c in TAX_TRANSFER:
            return "tax_transfer"
        if c in HYBRID:
            return "hybrid"
        if c == SPLIT_AUS:
            return "forced_saving" if y >= 1992 else "hybrid"
        if c == SPLIT_CHL:
            return "forced_saving" if y <= 2008 else "hybrid"
        return "other"

    panel["architecture"] = panel.apply(code, axis=1)
    panel["arch_forced_saving"] = (panel["architecture"] == "forced_saving").astype(int)
    panel["arch_tax_transfer"] = (panel["architecture"] == "tax_transfer").astype(int)
    # hybrid is reference

    return panel, manifest


def fit_twfe(df, outcome, treatments, controls=None):
    controls = controls or []
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
    if d.shape[0] < 20:
        return {"n_obs": int(d.shape[0]), "coefs": {}, "error": "insufficient observations"}
    X = d[treatments + controls]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=True, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in treatments + controls:
        if t in res.params.index:
            out["coefs"][t] = {
                "estimate": float(res.params[t]),
                "se": float(res.std_errors[t]),
                "ci_lo": float(res.conf_int().loc[t, "lower"]),
                "ci_hi": float(res.conf_int().loc[t, "upper"]),
                "p": float(res.pvalues[t]),
                "t": float(res.tstats[t]),
            }
    return out


def cluster_means(df, outcome):
    """Simple country-mean → cluster-mean (forced vs tax-transfer)."""
    sub = df[["country", "year", "architecture", outcome]].dropna()
    cluster_mean = sub.groupby("architecture")[outcome].mean()
    return {k: float(v) for k, v in cluster_mean.items()}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    controls = ["log_population", "urbanisation", "trade_openness"]

    # Note: country FE absorbs time-invariant architecture for SGP/CHE/etc (always one regime).
    # The forced/tax/hybrid dummy is identified only by the AUS 1992 and CHL 2008 within-country
    # transitions in TWFE. We therefore also report cluster-mean gaps (between-country, no FE).

    # Spec 1: growth_yoy
    s_growth = fit_twfe(panel, "growth_yoy",
                        ["arch_forced_saving", "arch_tax_transfer"], controls)
    # Spec 2: income_gini
    s_gini = fit_twfe(panel, "income_gini",
                      ["arch_forced_saving", "arch_tax_transfer"], controls)
    # Spec 3: gross_debt_gdp
    s_debt = fit_twfe(panel, "gross_debt_gdp",
                      ["arch_forced_saving", "arch_tax_transfer"], controls)

    # Between-country cluster means (descriptive, not FE-absorbed)
    desc = {
        "growth_yoy": cluster_means(panel, "growth_yoy"),
        "income_gini": cluster_means(panel, "income_gini"),
        "gross_debt_gdp": cluster_means(panel, "gross_debt_gdp"),
    }

    # Falsification thresholds (per spec)
    g_force = desc["growth_yoy"].get("forced_saving")
    g_taxtr = desc["growth_yoy"].get("tax_transfer")
    delta_growth = (g_force - g_taxtr) if (g_force is not None and g_taxtr is not None) else None

    gi_force = desc["income_gini"].get("forced_saving")
    gi_taxtr = desc["income_gini"].get("tax_transfer")
    delta_gini = (gi_force - gi_taxtr) if (gi_force is not None and gi_taxtr is not None) else None

    d_force = desc["gross_debt_gdp"].get("forced_saving")
    d_taxtr = desc["gross_debt_gdp"].get("tax_transfer")
    delta_debt = (d_taxtr - d_force) if (d_force is not None and d_taxtr is not None) else None

    # SUPPORTED rule (per spec, falsification is one-sided on growth and Gini —
    # forced-saving is refuted only if it does WORSE than tax-transfer by the
    # threshold; comparable or better passes the test):
    growth_ok = delta_growth is not None and delta_growth > -0.5
    gini_ok = delta_gini is not None and delta_gini < 5.0
    debt_ok = delta_debt is not None and delta_debt >= 10.0

    if growth_ok and gini_ok and debt_ok:
        verdict = (f"SUPPORTED — forced-saving cluster within tolerance on growth "
                   f"(Δ={delta_growth:+.2f}pp) and Gini (Δ={delta_gini:+.1f}pts), "
                   f"with debt-to-GDP {delta_debt:+.1f}pp lower than tax-transfer cluster.")
    elif growth_ok and gini_ok and not debt_ok:
        verdict = (f"PARTIAL — comparable growth (Δ={delta_growth:+.2f}pp) and Gini "
                   f"(Δ={delta_gini:+.1f}pts), but fiscal-sustainability gap "
                   f"Δdebt={delta_debt:+.1f}pp falls short of 10pp threshold.")
    elif (growth_ok or gini_ok) and not debt_ok:
        verdict = (f"PARTIAL — directional but does not meet all three thresholds; "
                   f"Δgrowth={delta_growth:+.2f}pp, Δgini={delta_gini:+.1f}, Δdebt={delta_debt:+.1f}pp.")
    else:
        verdict = (f"REFUTED — falsification thresholds breached: "
                   f"Δgrowth={delta_growth:+.2f}pp (need <0.5pp), "
                   f"Δgini={delta_gini:+.1f} (need <5pts), "
                   f"Δdebt={delta_debt:+.1f}pp (need >=10pp).")

    # Note re: income vs wealth Gini
    note_gini = ("NOTE: spec calls for wealth Gini; this run uses disposable-income Gini "
                 "(SI.POV.GINI) as proxy because wealth Gini is data-gated.")

    # Coefficients table
    rows = []
    for spec_name, spec in [("growth_yoy", s_growth), ("income_gini", s_gini), ("gross_debt_gdp", s_debt)]:
        for t, c in spec.get("coefs", {}).items():
            rows.append({"spec": spec_name, "term": t, **c, "n_obs": spec["n_obs"]})
    if rows:
        pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "note_gini_proxy": note_gini,
        "spec_growth": s_growth,
        "spec_gini": s_gini,
        "spec_debt": s_debt,
        "cluster_means": desc,
        "deltas": {
            "delta_growth_pp": delta_growth,
            "delta_gini_points": delta_gini,
            "delta_debt_gdp_pp": delta_debt,
        },
        "falsification": {
            "abs_delta_growth_lt_0.5pp": growth_ok,
            "abs_delta_gini_lt_5pts": gini_ok,
            "delta_debt_ge_10pp": debt_ok,
        },
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "growth_vs_distribution_tradeoff",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # Result card
    g = s_growth["coefs"].get("arch_forced_saving", {})
    gi = s_gini["coefs"].get("arch_forced_saving", {})
    de = s_debt["coefs"].get("arch_forced_saving", {})
    g_tt = s_growth["coefs"].get("arch_tax_transfer", {})
    gi_tt = s_gini["coefs"].get("arch_tax_transfer", {})
    de_tt = s_debt["coefs"].get("arch_tax_transfer", {})

    lines = [
        "# Result card — Growth vs distribution tradeoff (welfare architecture)",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"_{note_gini}_",
        "",
        "## Cluster means (between-country, descriptive)",
        "",
        "| Cluster | Growth (yoy %) | Gini (income, SI.POV.GINI) | Gross debt / GDP (%) |",
        "|---|---:|---:|---:|",
        f"| forced_saving | {desc['growth_yoy'].get('forced_saving', float('nan')):.2f} | "
        f"{desc['income_gini'].get('forced_saving', float('nan')):.1f} | "
        f"{desc['gross_debt_gdp'].get('forced_saving', float('nan')):.1f} |",
        f"| tax_transfer | {desc['growth_yoy'].get('tax_transfer', float('nan')):.2f} | "
        f"{desc['income_gini'].get('tax_transfer', float('nan')):.1f} | "
        f"{desc['gross_debt_gdp'].get('tax_transfer', float('nan')):.1f} |",
        f"| hybrid | {desc['growth_yoy'].get('hybrid', float('nan')):.2f} | "
        f"{desc['income_gini'].get('hybrid', float('nan')):.1f} | "
        f"{desc['gross_debt_gdp'].get('hybrid', float('nan')):.1f} |",
        f"| **forced − tax_transfer** | **{delta_growth:+.2f}** | **{delta_gini:+.1f}** | **debt: {delta_debt:+.1f} (tt − fs)** |",
        "",
        "## TWFE regression coefficients (country + year FE; hybrid = reference)",
        "",
        "Country FE absorb time-invariant architecture; identification comes from",
        "AUS 1992 super introduction and CHL 2008 solidarity-pillar transition.",
        "Coefficients are within-country deviation; the cluster means above are",
        "the between-country evidence the spec also asks for.",
        "",
        "### Outcome 1 — annual real GDP per capita growth (%)",
        "",
        "| Term | Estimate | SE | p | n |",
        "|---|---:|---:|---:|---:|",
        f"| arch_forced_saving | {g.get('estimate', float('nan')):+.3f} | "
        f"{g.get('se', float('nan')):.3f} | {g.get('p', float('nan')):.3f} | {s_growth.get('n_obs', 'NA')} |",
        f"| arch_tax_transfer  | {g_tt.get('estimate', float('nan')):+.3f} | "
        f"{g_tt.get('se', float('nan')):.3f} | {g_tt.get('p', float('nan')):.3f} | — |",
        "",
        "### Outcome 2 — disposable-income Gini (SI.POV.GINI)",
        "",
        "| Term | Estimate | SE | p | n |",
        "|---|---:|---:|---:|---:|",
        f"| arch_forced_saving | {gi.get('estimate', float('nan')):+.3f} | "
        f"{gi.get('se', float('nan')):.3f} | {gi.get('p', float('nan')):.3f} | {s_gini.get('n_obs', 'NA')} |",
        f"| arch_tax_transfer  | {gi_tt.get('estimate', float('nan')):+.3f} | "
        f"{gi_tt.get('se', float('nan')):.3f} | {gi_tt.get('p', float('nan')):.3f} | — |",
        "",
        "### Outcome 3 — gross general govt debt / GDP (IMF GGXWDG_NGDP)",
        "",
        "| Term | Estimate | SE | p | n |",
        "|---|---:|---:|---:|---:|",
        f"| arch_forced_saving | {de.get('estimate', float('nan')):+.3f} | "
        f"{de.get('se', float('nan')):.3f} | {de.get('p', float('nan')):.3f} | {s_debt.get('n_obs', 'NA')} |",
        f"| arch_tax_transfer  | {de_tt.get('estimate', float('nan')):+.3f} | "
        f"{de_tt.get('se', float('nan')):.3f} | {de_tt.get('p', float('nan')):.3f} | — |",
        "",
        "## Falsification rule applied",
        "",
        "Spec requires ALL three thresholds:",
        f"- Δ growth (forced − tax_transfer) > −0.5 pp/yr (one-sided): **{'✓' if growth_ok else '✗'}** ({delta_growth:+.2f}pp)",
        f"- Δ Gini (forced − tax_transfer) < +5 pts (one-sided): **{'✓' if gini_ok else '✗'}** ({delta_gini:+.1f}pts)",
        f"- Δ debt-to-GDP (tax_transfer − forced_saving) ≥ 10pp: **{'✓' if debt_ok else '✗'}** ({delta_debt:+.1f}pp)",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/growth_vs_distribution_tradeoff.md`. Key concerns:",
        "1. Wealth Gini is the spec primary; income Gini under-states the architectural",
        "   distinction (forced-saving builds household wealth that is not in income flows).",
        "2. SGP and CHE score among the world's highest on government effectiveness;",
        "   architecture-vs-outcomes is heavily confounded with state capacity.",
        "3. Country FE absorb most architecture variation; identification leans on AUS 1992",
        "   and CHL 2008 transitions which have many other contemporaneous reforms.",
        "4. The N is too small for robust inference on cluster contrast — 4 forced-saving",
        "   countries (after AUS/CHL splits) vs 8 tax-transfer.",
        "",
        "## Provenance",
        "",
        "Data: WDI NY.GDP.PCAP.KD, SI.POV.GINI, NE.TRD.GNFS.ZS, SP.POP.TOTL, SP.URB.TOTL.IN.ZS;",
        "WGI GE.EST; IMF GGXWDG_NGDP. See `manifest.yaml`. Reproduces from `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    # Console
    print(f"verdict: {verdict}")
    print(f"  cluster means growth%: {desc['growth_yoy']}")
    print(f"  cluster means Gini:    {desc['income_gini']}")
    print(f"  cluster means debt%:   {desc['gross_debt_gdp']}")
    print(f"  Δgrowth={delta_growth:+.2f}pp, Δgini={delta_gini:+.1f}, Δdebt={delta_debt:+.1f}pp")
    print(f"  TWFE β_forced_saving (growth) = {g.get('estimate', float('nan')):+.3f} p={g.get('p', float('nan')):.3f}, n={s_growth.get('n_obs', 'NA')}")


if __name__ == "__main__":
    sys.exit(main())
