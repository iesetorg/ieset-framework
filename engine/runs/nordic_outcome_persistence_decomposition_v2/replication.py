#!/usr/bin/env python3
"""Replication — Nordic decomposition v2 (expanded channel set).

Spec:    hypotheses/institutional_quality/nordic_outcome_persistence_decomposition_v2.yaml
Steelman: hypotheses/steelman/nordic_outcome_persistence_decomposition_v2.md

Same sample, same outcomes, same identification (time FE, no country FE) as
v1. Channel set expands from 3 to 8:
  v1: gov_eff, rule_of_law, debt_gdp_imf
  v2 adds: cc (control of corruption), rq (regulatory quality),
           net_lending_gdp (fiscal surplus flow), current_account_gdp,
           trade_openness
Controls unchanged: log_population, urbanisation.

Tests whether the v1 residual (0.98 on primary outcome) was due to omitted
variables (supports v2) or to structural limitation of cross-sectional
decomposition on this sample (refutes v2 → motivates v3 trajectory design).
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
OUT_DIR = REPO_ROOT / "engine" / "runs" / "nordic_outcome_persistence_decomposition_v2"

NORDIC = {"NOR", "SWE", "DNK", "FIN", "ISL"}
COMPARATORS = {"ESP", "ITA", "GRC", "PRT", "FRA"}
ALL_COUNTRIES = sorted(NORDIC | COMPARATORS)
PERIOD = (1996, 2023)

V1_CHANNELS = ["gov_eff", "rule_of_law", "debt_gdp"]
V2_NEW = ["cc", "rq", "net_lending_gdp", "current_account_gdp", "trade_openness"]
CONTROLS = ["log_population", "urbanisation"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_vintage(publisher: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / publisher
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"no vintages for {publisher}:{series}")
    return files[-1]


def load_long(path: Path, variable_name: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    t = t[["country_iso3", "year", "value"]].copy()
    t["year"] = t["year"].astype(int)
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t = t.rename(columns={"value": variable_name, "country_iso3": "country"})
    return t


def assemble_panel() -> tuple[pd.DataFrame, dict[str, dict[str, str]]]:
    vintage_paths = {
        "gdp_pc_ppp":       ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "gini":             ("world_bank_wdi", "SI.POV.GINI"),
        "unemployment":     ("world_bank_wdi", "SL.UEM.TOTL.ZS"),
        "debt_gdp":         ("imf", "GGXWDG_NGDP"),
        "population":       ("world_bank_wdi", "SP.POP.TOTL"),
        "urbanisation":     ("world_bank_wdi", "SP.URB.TOTL.IN.ZS"),
        "gov_eff":          ("wgi", "GOV_WGI_GE.EST"),
        "rule_of_law":      ("wgi", "GOV_WGI_RL.EST"),
        "cc":               ("wgi", "GOV_WGI_CC.EST"),
        "rq":               ("wgi", "GOV_WGI_RQ.EST"),
        "net_lending_gdp":  ("imf", "GGXCNL_NGDP"),
        "current_account_gdp": ("imf", "BCA_NGDPD"),
        "trade_openness":   ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
    }
    manifest: dict[str, dict[str, str]] = {}
    frames = []
    for var, (pub, series) in vintage_paths.items():
        path = latest_vintage(pub, series)
        manifest[var] = {
            "publisher": pub, "series": series,
            "vintage_file": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256(path),
        }
        frames.append(load_long(path, var))

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")

    panel = panel[panel["country"].isin(ALL_COUNTRIES)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel[~((panel["country"] == "ISL") & (panel["year"] < 1998))]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["log_population"] = np.log(panel["population"])
    panel["nordic_dummy"] = panel["country"].isin(NORDIC).astype(int)

    lo, hi = panel["gini"].quantile([0.01, 0.99])
    panel["gini"] = panel["gini"].clip(lo, hi)
    return panel, manifest


def vifs(df: pd.DataFrame, cols: list[str]) -> dict[str, float]:
    """Variance-inflation factor per column, regressing each on the others."""
    from numpy.linalg import lstsq
    X = df[cols].dropna().values
    out: dict[str, float] = {}
    for j, c in enumerate(cols):
        y = X[:, j]
        Xo = np.delete(X, j, axis=1)
        Xo = np.column_stack([np.ones(len(Xo)), Xo])
        coefs, *_ = lstsq(Xo, y, rcond=None)
        yhat = Xo @ coefs
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        out[c] = round(1 / (1 - r2) if r2 < 1 else float("inf"), 2)
    return out


def fit(df: pd.DataFrame, outcome: str, channels: list[str]) -> dict:
    cols = ["country", "year", outcome, "nordic_dummy"] + channels + CONTROLS
    d = df[cols].dropna().copy()
    d = d.set_index(["country", "year"])
    d["const"] = 1.0
    X = d[["const", "nordic_dummy"] + channels + CONTROLS]
    y = d[outcome]
    model = PanelOLS(y, X, time_effects=True, check_rank=False, drop_absorbed=True)
    res = model.fit(cov_type="clustered", cluster_entity=True)
    return {
        "n_obs": int(res.nobs),
        "nordic_coef": float(res.params["nordic_dummy"]),
        "nordic_se": float(res.std_errors["nordic_dummy"]),
        "nordic_ci_lo": float(res.conf_int().loc["nordic_dummy", "lower"]),
        "nordic_ci_hi": float(res.conf_int().loc["nordic_dummy", "upper"]),
        "nordic_p": float(res.pvalues["nordic_dummy"]),
        "r2": float(res.rsquared),
        "channel_coefs": {c: float(res.params[c]) for c in channels + CONTROLS if c in res.params.index},
    }


def fit_baseline(df: pd.DataFrame, outcome: str) -> dict:
    return fit(df, outcome, [])


def leave_one_out(df: pd.DataFrame, outcome: str, channels: list[str], baseline_coef: float) -> list[dict]:
    """Drop each channel in turn; report how much that changes the residual share."""
    out = []
    for drop in channels:
        kept = [c for c in channels if c != drop]
        r = fit(df, outcome, kept)
        out.append({
            "dropped": drop,
            "nordic_coef": r["nordic_coef"],
            "residual_share": abs(r["nordic_coef"]) / abs(baseline_coef) if baseline_coef != 0 else float("nan"),
        })
    return out


def build_chart_data(panel, outcomes_results, manifest):
    colors = {
        "NOR": "#4E79A7", "SWE": "#59A14F", "DNK": "#B07AA1", "FIN": "#E15759", "ISL": "#F28E2B",
        "ESP": "#76B7B2", "ITA": "#EDC948", "GRC": "#B6992D", "PRT": "#9C755F", "FRA": "#555555",
    }
    series = []
    for country in ALL_COUNTRIES:
        sub = panel[panel["country"] == country][["year", "log_gdp_pc_ppp"]].dropna().sort_values("year")
        if sub.empty:
            continue
        series.append({
            "id": country, "label": country,
            "color": colors.get(country, "#666"),
            "nordic": country in NORDIC,
            "points": [{"x": int(r.year), "y": float(r.log_gdp_pc_ppp)} for r in sub.itertuples()],
        })
    rs = outcomes_results["log_gdp_pc_ppp"]["v2_residual_share"]
    delta_v1 = outcomes_results["log_gdp_pc_ppp"]["delta_vs_v1"]
    chart_data = {
        "chart_id": "nordic_outcome_persistence_decomposition_v2/fig1",
        "title": "Log GDP per capita (PPP, constant intl $), 1996 – 2023 (v2)",
        "subtitle": (
            f"v2 adds 5 channels (CC, RQ, net-lending, CA, trade). "
            f"Primary-outcome residual share: {rs:.2f} "
            f"(Δ vs v1: {delta_v1:+.2f})."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log GDP per capita (PPP)", "type": "linear"},
        "series": series,
        "annotations": [{
            "type": "note",
            "label": (
                f"v1 residual share: {outcomes_results['log_gdp_pc_ppp']['v1_residual_share']:.2f}. "
                f"v2 residual share: {rs:.2f}. "
                f"{'Channels absorbed more of the gap.' if delta_v1 < -0.1 else 'Channel expansion did not materially shrink the residual.'}"
            ),
        }],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": "/h/nordic_outcome_persistence_decomposition_v2",
    }
    return chart_data


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble_panel()

    outcomes = ["log_gdp_pc_ppp", "gini", "unemployment"]
    thresholds = {"log_gdp_pc_ppp": 0.30, "gini": 0.50, "unemployment": 0.50}
    v1_rs = {"log_gdp_pc_ppp": 0.976, "gini": 0.842, "unemployment": 0.082}

    channels_v2 = V1_CHANNELS + V2_NEW
    results = {}
    for o in outcomes:
        baseline = fit_baseline(panel, o)
        v1_spec = fit(panel, o, V1_CHANNELS)
        v2_spec = fit(panel, o, channels_v2)
        rs_v1 = abs(v1_spec["nordic_coef"]) / abs(baseline["nordic_coef"]) if baseline["nordic_coef"] else float("nan")
        rs_v2 = abs(v2_spec["nordic_coef"]) / abs(baseline["nordic_coef"]) if baseline["nordic_coef"] else float("nan")
        delta = rs_v2 - rs_v1
        results[o] = {
            "baseline": baseline, "v1": v1_spec, "v2": v2_spec,
            "v1_residual_share": rs_v1,
            "v2_residual_share": rs_v2,
            "delta_vs_v1": delta,
        }

    # Per-outcome pass/fail
    per_pass = {o: results[o]["v2_residual_share"] <= thresholds[o] for o in outcomes}
    material_delta_primary = results["log_gdp_pc_ppp"]["v1_residual_share"] - results["log_gdp_pc_ppp"]["v2_residual_share"] >= 0.10
    all_pass = all(per_pass.values()) and material_delta_primary

    if all_pass:
        verdict = "supported"
    elif material_delta_primary and not per_pass["log_gdp_pc_ppp"]:
        verdict = "partially supported (primary outcome improved materially but did not meet 0.30 threshold)"
    elif not material_delta_primary:
        verdict = "refuted — channel expansion did not materially shrink the primary-outcome residual (<0.10 change from v1); decomposition framing is exhausted"
    else:
        verdict = "mixed"

    # Leave-one-out on primary outcome (diagnostic per steelman objection 1)
    loo = leave_one_out(panel, "log_gdp_pc_ppp", channels_v2, results["log_gdp_pc_ppp"]["baseline"]["nordic_coef"])

    # VIF diagnostic
    vif_cols = channels_v2 + CONTROLS
    vif_panel = panel[vif_cols].dropna()
    vif_result = vifs(vif_panel, vif_cols) if len(vif_panel) > len(vif_cols) + 1 else {"error": "insufficient obs for VIF"}

    # ---- artifacts ----

    # coefficients.parquet
    rows = []
    for o in outcomes:
        for spec_name, spec in (("baseline", results[o]["baseline"]),
                                ("v1", results[o]["v1"]),
                                ("v2", results[o]["v2"])):
            rows.append({"outcome": o, "spec": spec_name, "term": "nordic_dummy",
                         "estimate": spec["nordic_coef"], "std_error": spec["nordic_se"],
                         "ci_lower": spec["nordic_ci_lo"], "ci_upper": spec["nordic_ci_hi"],
                         "p_value": spec["nordic_p"], "n_obs": spec["n_obs"]})
            for term, coef in spec.get("channel_coefs", {}).items():
                rows.append({"outcome": o, "spec": spec_name, "term": term,
                             "estimate": coef, "std_error": float("nan"),
                             "ci_lower": float("nan"), "ci_upper": float("nan"),
                             "p_value": float("nan"), "n_obs": spec["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "chart_data.json").write_text(json.dumps(
        build_chart_data(panel, results, manifest), indent=2) + "\n")

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "material_delta_primary": material_delta_primary,
        "per_outcome": {o: {
            "v1_residual_share": results[o]["v1_residual_share"],
            "v2_residual_share": results[o]["v2_residual_share"],
            "delta_vs_v1": results[o]["delta_vs_v1"],
            "threshold": thresholds[o],
            "pass": per_pass[o],
        } for o in outcomes},
        "leave_one_out_primary": loo,
        "vifs": vif_result,
        "all_pass": all_pass,
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "nordic_outcome_persistence_decomposition_v2",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "vintages": manifest,
    }, sort_keys=False))

    # result_card.md
    lines = [
        "# Result card — Nordic outcome persistence decomposition v2",
        "",
        f"**Verdict:** {verdict}",
        "",
        "Pre-registered falsifier: v2 residual share on log GDP/cap PPP must be "
        "both (a) ≤ 0.30 *and* (b) materially lower than v1's 0.98 (Δ ≥ 0.10). "
        "Both must hold for v2 support.",
        "",
        "## Coefficient summary",
        "",
        "| Outcome | v1 residual | v2 residual | Δ | Threshold | Pass? |",
        "|---|---:|---:|---:|---:|:---:|",
    ]
    for o in outcomes:
        r = results[o]
        lines.append(
            f"| `{o}` | {r['v1_residual_share']:.2f} | "
            f"{r['v2_residual_share']:.2f} | "
            f"{r['delta_vs_v1']:+.2f} | "
            f"{thresholds[o]:.2f} | "
            f"{'✓' if per_pass[o] else '✗'} |"
        )
    lines += [
        "",
        f"Material-delta-on-primary (Δ ≥ 0.10): {'yes' if material_delta_primary else 'no'}",
        "",
        "## Leave-one-out sensitivity (primary outcome)",
        "",
        "Drops each v2 channel and reports how much the residual share changes. "
        "Channels that are load-bearing should show larger changes when dropped.",
        "",
        "| Channel dropped | Nordic coef | Residual share | Contribution |",
        "|---|---:|---:|---:|",
    ]
    v2_rs = results["log_gdp_pc_ppp"]["v2_residual_share"]
    for row in loo:
        contrib = row["residual_share"] - v2_rs
        lines.append(
            f"| `{row['dropped']}` | {row['nordic_coef']:+.3f} | "
            f"{row['residual_share']:.2f} | {contrib:+.2f} |"
        )
    lines += [
        "",
        "## VIFs (multicollinearity diagnostic)",
        "",
    ]
    if isinstance(vif_result, dict) and "error" not in vif_result:
        lines.append("| Variable | VIF |")
        lines.append("|---|---:|")
        for k, v in sorted(vif_result.items(), key=lambda x: -x[1] if isinstance(x[1], (int, float)) else 0):
            lines.append(f"| `{k}` | {v} |")
        max_vif = max([v for v in vif_result.values() if isinstance(v, (int, float))], default=0)
        lines.append("")
        if max_vif > 10:
            lines.append(f"**Warning:** max VIF = {max_vif:.1f}, indicates severe multicollinearity. Individual channel coefficients are unreliable even though the residual-share summary is mechanically interpretable.")
        else:
            lines.append(f"Max VIF = {max_vif:.1f} — below the conventional concern threshold of 10.")
    else:
        lines.append(f"VIF diagnostic skipped: {vif_result}")

    lines += [
        "",
        "## Interpretation",
        "",
    ]
    primary_rs = results["log_gdp_pc_ppp"]["v2_residual_share"]
    if all_pass:
        lines.append(
            f"v2 residual share on primary outcome dropped to {primary_rs:.2f} "
            f"(from v1's 0.98), passing both the absolute 0.30 threshold and "
            f"the material-delta requirement. The five additional channels "
            f"collectively absorb most of the Nordic-vs-comparator GDP gap. "
            f"This supports the decomposition framing — the v1 residual was "
            f"largely omitted-variable bias, not a structural limitation."
        )
    elif material_delta_primary and not per_pass["log_gdp_pc_ppp"]:
        lines.append(
            f"v2 reduced the primary-outcome residual from v1's 0.98 to "
            f"{primary_rs:.2f} (Δ = {results['log_gdp_pc_ppp']['delta_vs_v1']:+.2f}) "
            f"— a meaningful shrinkage but still above the 0.30 pre-registered "
            f"threshold. Partial support: more channels do explain more of the "
            f"gap, but the cross-sectional decomposition is still not fully "
            f"sufficient. Part of the Nordic advantage remains unmeasured on "
            f"this 10-country × 28-year panel."
        )
    elif not material_delta_primary:
        lines.append(
            f"v2 residual share on primary outcome is {primary_rs:.2f}, "
            f"essentially unchanged from v1's 0.98 (Δ = "
            f"{results['log_gdp_pc_ppp']['delta_vs_v1']:+.2f}). Expanding "
            f"the channel set from 3 to 8 did not materially shrink the "
            f"residual. This refutes the omitted-variable explanation of v1 "
            f"and supports the structural interpretation: cross-sectional "
            f"decomposition on this sample cannot explain the Nordic GDP "
            f"advantage regardless of how many channels are added. The next "
            f"step is v3 — within-country panel analysis with movement-level "
            f"treatment effects on specific reform episodes (Bildt 1991, "
            f"Nyrup 1994, Norwegian SWF 2001, Schröder 2003, vs Mitterrand "
            f"1981, Greek fiscal-dominance 2000s, Italian stagnation)."
        )

    lines += [
        "",
        "Per DISCLOSURE.md commitment, this finding is reported regardless "
        "of direction relative to the author's prior.",
        "",
        "## Provenance",
        "",
        "Reproduces deterministically from the vintages listed in `manifest.yaml`. "
        "See `replication.py`. Pre-registration: see "
        "`hypotheses/institutional_quality/nordic_outcome_persistence_decomposition_v2.yaml` "
        "and its git first-commit timestamp (predates this run).",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    # Console
    print(f"verdict: {verdict}")
    for o in outcomes:
        r = results[o]
        print(f"  {o}: v1_rs={r['v1_residual_share']:.3f}  v2_rs={r['v2_residual_share']:.3f}  Δ={r['delta_vs_v1']:+.3f}  pass={per_pass[o]}")
    print(f"max VIF: {max([v for v in vif_result.values() if isinstance(v, (int, float))], default=0):.1f}" if isinstance(vif_result, dict) and "error" not in vif_result else "VIF: skipped")
    print(f"artifacts: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
