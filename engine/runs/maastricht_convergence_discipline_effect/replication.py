#!/usr/bin/env python3
"""Replication — Maastricht convergence discipline effect on inflation.

Spec: hypotheses/monetary/maastricht_convergence_discipline_effect.yaml v1
Position-claim: ordoliberal #7 (school predicts: supported)

The ordoliberal claim: Maastricht (1992) imposed rules-based fiscal-monetary
discipline that produced inflation and interest-rate convergence in
pre-accession EU members vs the Bundesbank/DEU anchor.

We treat the Feb-1992 Maastricht treaty signature as the event; the relevant
convergence outcome is observed by 2002 (euro launch in 1999, full physical
adoption in 2002 — the canonical "convergence test" window).

Treated: ITA, ESP, PRT, GRC, IRL — the periphery, the high-inflation
pre-accession states whose convergence is the empirical focus of the claim.
Anchor: DEU (Bundesbank — the low-inflation benchmark by construction).
Controls: GBR, USA, JPN, CAN — non-Eurozone OECD comparators that did NOT
sign Maastricht (GBR opted out per spec).

PRIMARY (dispositive): the difference-in-differences in CPI inflation
between (treated peripherals) and (non-Eurozone OECD controls), comparing
the pre-treatment window 1985-1991 to the post-Maastricht convergence
window 1996-2002. Convergence is measured as the change in the absolute
inflation gap to the German anchor: |pi_c - pi_DEU|.

  primary_stat = mean_c in TREATED of [|pi_c - pi_DEU|_post - |pi_c - pi_DEU|_pre]
                 - mean_c in CONTROL of [|pi_c - pi_DEU|_post - |pi_c - pi_DEU|_pre]

Negative = convergence on treated relative to controls = SUPPORTED.

Thresholds:
  SUPPORTED: primary_stat <= -3.0 percentage points (treated peripherals
             narrowed their gap to DEU by at least 3 pp MORE than controls).
  partial:   -3.0 < primary_stat <= -1.0 (some relative convergence but
             below the dispositive threshold).
  refuted:   primary_stat >  -1.0 OR opposite direction (no relative
             convergence; controls converged as much or the periphery
             diverged).

INFORMATIVE: per-country gap closure; absolute level of treated mean
inflation in 1996-2002 (should be near DEU level if convergence held).

METHOD_VALID: at least 4 of 5 treated countries and 3 of 4 control
countries have CPI inflation observations covering both windows. WDI
FP.CPI.TOTL.ZG for all 10 countries spans the period.

Note: the spec also lists 10y sovereign yields and inflation dispersion
as outcomes. Yield convergence is informative-only here because reliable
ECB/national 10y yield series for ITA/ESP/PRT/GRC across 1985-1991 are
not on disk in a unified vintage. Inflation is the primary dispositive
test; yields are reported descriptively if available.
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
HID = "maastricht_convergence_discipline_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample
ANCHOR = "DEU"  # Bundesbank anchor
TREATED = ["ITA", "ESP", "PRT", "GRC", "IRL"]  # periphery pre-accession
CONTROLS = ["GBR", "USA", "JPN", "CAN"]  # non-Eurozone OECD
ALL_COUNTRIES = [ANCHOR] + TREATED + CONTROLS

# Windows
PRE_WINDOW = (1985, 1991)
POST_WINDOW = (1996, 2002)

# Falsification thresholds (dispositive)
PRIMARY_DID_SUPPORTED = -3.0  # pp: treated converged at least 3pp more than controls
PRIMARY_DID_PARTIAL = -1.0  # pp: partial range upper bound

# METHOD_VALID gate
MIN_TREATED_WITH_DATA = 4  # of 5
MIN_CONTROL_WITH_DATA = 3  # of 4


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


def window_mean(df: pd.DataFrame, country: str, lo: int, hi: int) -> float | None:
    sub = df[(df["country_iso3"] == country) & (df["year"].between(lo, hi))]
    if len(sub) == 0:
        return None
    return float(sub["value"].mean())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cpi_path = latest("world_bank_wdi", "FP.CPI.TOTL.ZG")
    debt_path = latest("imf", "GGXWDG_NGDP")

    manifest = {
        "cpi_inflation": {
            "publisher": "world_bank_wdi",
            "series": "FP.CPI.TOTL.ZG",
            "vintage_file": str(cpi_path.relative_to(REPO_ROOT)),
            "sha256": sha256(cpi_path),
        },
        "general_government_debt_pct_gdp": {
            "publisher": "imf",
            "series": "GGXWDG_NGDP",
            "vintage_file": str(debt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(debt_path),
        },
    }

    cpi = load_long(cpi_path)
    debt = load_long(debt_path)

    # ---------- PRIMARY: DiD on |inflation - DEU| ----------
    # 1) Compute window-mean inflation per country.
    pre_means: dict[str, float] = {}
    post_means: dict[str, float] = {}
    for c in ALL_COUNTRIES:
        v_pre = window_mean(cpi, c, *PRE_WINDOW)
        v_post = window_mean(cpi, c, *POST_WINDOW)
        if v_pre is not None:
            pre_means[c] = v_pre
        if v_post is not None:
            post_means[c] = v_post

    if ANCHOR not in pre_means or ANCHOR not in post_means:
        verdict = (
            "inconclusive — Anchor country DEU has no inflation data in one or "
            "both windows; cannot construct gap-to-anchor for the convergence test."
        )
        diagnostics = {
            "verdict": verdict,
            "primary_did": None,
            "method_valid": False,
            "data_gap": "DEU CPI inflation missing in PRE or POST window",
        }
        (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
        print(f"verdict: {verdict}")
        return

    deu_pre = pre_means[ANCHOR]
    deu_post = post_means[ANCHOR]

    treated_with_data = [c for c in TREATED if c in pre_means and c in post_means]
    controls_with_data = [c for c in CONTROLS if c in pre_means and c in post_means]

    method_valid = (
        len(treated_with_data) >= MIN_TREATED_WITH_DATA
        and len(controls_with_data) >= MIN_CONTROL_WITH_DATA
    )

    # 2) Per-country gap closure: |pi - DEU|_post - |pi - DEU|_pre
    def gap_closure(c: str) -> float:
        return abs(post_means[c] - deu_post) - abs(pre_means[c] - deu_pre)

    treated_gap_closures = {c: gap_closure(c) for c in treated_with_data}
    control_gap_closures = {c: gap_closure(c) for c in controls_with_data}

    treated_mean_closure = float(np.mean(list(treated_gap_closures.values()))) if treated_gap_closures else float("nan")
    control_mean_closure = float(np.mean(list(control_gap_closures.values()))) if control_gap_closures else float("nan")
    primary_did = treated_mean_closure - control_mean_closure

    # 3) Levels for context
    treated_pre_mean_level = float(np.mean([pre_means[c] for c in treated_with_data])) if treated_with_data else float("nan")
    treated_post_mean_level = float(np.mean([post_means[c] for c in treated_with_data])) if treated_with_data else float("nan")
    control_pre_mean_level = float(np.mean([pre_means[c] for c in controls_with_data])) if controls_with_data else float("nan")
    control_post_mean_level = float(np.mean([post_means[c] for c in controls_with_data])) if controls_with_data else float("nan")

    # 4) INFORMATIVE: fiscal discipline — gov debt / GDP trajectory
    debt_pre = {}
    debt_post = {}
    for c in TREATED + CONTROLS + [ANCHOR]:
        v_pre = window_mean(debt, c, *PRE_WINDOW)
        v_post = window_mean(debt, c, *POST_WINDOW)
        if v_pre is not None:
            debt_pre[c] = v_pre
        if v_post is not None:
            debt_post[c] = v_post

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            f"inconclusive — Insufficient panel coverage in CPI inflation: "
            f"{len(treated_with_data)}/5 treated and {len(controls_with_data)}/4 "
            f"control countries have data in both windows. "
            f"Cannot dispositively test the Maastricht convergence claim."
        )
    elif primary_did <= PRIMARY_DID_SUPPORTED:
        verdict = (
            f"SUPPORTED — Treated peripheral states (ITA/ESP/PRT/GRC/IRL) "
            f"narrowed their inflation gap to the German anchor by "
            f"{-treated_mean_closure:.2f}pp from {PRE_WINDOW[0]}-{PRE_WINDOW[1]} "
            f"to {POST_WINDOW[0]}-{POST_WINDOW[1]}, vs only "
            f"{-control_mean_closure:.2f}pp for non-Eurozone controls "
            f"(GBR/USA/JPN/CAN). DiD = {primary_did:+.2f}pp "
            f"(<= {PRIMARY_DID_SUPPORTED}pp dispositive threshold). "
            f"Mean treated inflation fell from {treated_pre_mean_level:.2f}% "
            f"to {treated_post_mean_level:.2f}%."
        )
    elif primary_did <= PRIMARY_DID_PARTIAL:
        verdict = (
            f"partial — Treated periphery converged on the German anchor "
            f"by {-treated_mean_closure:.2f}pp vs {-control_mean_closure:.2f}pp "
            f"for controls (DiD = {primary_did:+.2f}pp), in the right direction "
            f"but below the {PRIMARY_DID_SUPPORTED}pp dispositive threshold "
            f"for SUPPORTED. Mean treated inflation: "
            f"{treated_pre_mean_level:.2f}% -> {treated_post_mean_level:.2f}%."
        )
    else:
        verdict = (
            f"refuted — Treated periphery's relative convergence on the "
            f"German anchor was not dispositive: DiD = {primary_did:+.2f}pp "
            f"(threshold for refutation: > {PRIMARY_DID_PARTIAL}pp). "
            f"Treated gap-closure: {-treated_mean_closure:.2f}pp; "
            f"control gap-closure: {-control_mean_closure:.2f}pp. "
            f"Either both groups converged (global disinflation alternative) "
            f"or treated did not converge meaningfully on DEU."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "primary_did_pp": primary_did,
        "primary_did_supported_threshold": PRIMARY_DID_SUPPORTED,
        "primary_did_partial_threshold": PRIMARY_DID_PARTIAL,
        "treated_mean_gap_closure_pp": treated_mean_closure,
        "control_mean_gap_closure_pp": control_mean_closure,
        "treated_pre_mean_inflation_pct": treated_pre_mean_level,
        "treated_post_mean_inflation_pct": treated_post_mean_level,
        "control_pre_mean_inflation_pct": control_pre_mean_level,
        "control_post_mean_inflation_pct": control_post_mean_level,
        "deu_pre_mean_inflation_pct": deu_pre,
        "deu_post_mean_inflation_pct": deu_post,
        "treated_per_country_gap_closure_pp": treated_gap_closures,
        "control_per_country_gap_closure_pp": control_gap_closures,
        "treated_per_country_pre_inflation_pct": {c: pre_means[c] for c in treated_with_data},
        "treated_per_country_post_inflation_pct": {c: post_means[c] for c in treated_with_data},
        "control_per_country_pre_inflation_pct": {c: pre_means[c] for c in controls_with_data},
        "control_per_country_post_inflation_pct": {c: post_means[c] for c in controls_with_data},
        "informative_debt_pct_gdp_pre": debt_pre,
        "informative_debt_pct_gdp_post": debt_post,
        "n_treated_with_data": len(treated_with_data),
        "n_control_with_data": len(controls_with_data),
        "pre_window": list(PRE_WINDOW),
        "post_window": list(POST_WINDOW),
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart ----------
    palette_treated = ["#E15759", "#F28E2B", "#B07AA1", "#9C755F", "#EDC948"]
    palette_control = ["#4E79A7", "#76B7B2", "#59A14F", "#B6992D"]
    palette_anchor = "#1f1f1f"

    series = []
    # Anchor first
    sub = (
        cpi[(cpi["country_iso3"] == ANCHOR) & (cpi["year"].between(1985, 2002))]
        [["year", "value"]].dropna().sort_values("year")
    )
    series.append({
        "id": ANCHOR,
        "label": f"{ANCHOR} (anchor)",
        "color": palette_anchor,
        "treated": False,
        "points": [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()],
    })
    for i, c in enumerate(TREATED):
        sub = (
            cpi[(cpi["country_iso3"] == c) & (cpi["year"].between(1985, 2002))]
            [["year", "value"]].dropna().sort_values("year")
        )
        if sub.empty:
            continue
        series.append({
            "id": c,
            "label": c,
            "color": palette_treated[i % len(palette_treated)],
            "treated": True,
            "points": [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()],
        })
    for i, c in enumerate(CONTROLS):
        sub = (
            cpi[(cpi["country_iso3"] == c) & (cpi["year"].between(1985, 2002))]
            [["year", "value"]].dropna().sort_values("year")
        )
        if sub.empty:
            continue
        series.append({
            "id": c,
            "label": c,
            "color": palette_control[i % len(palette_control)],
            "treated": False,
            "points": [{"x": int(r.year), "y": float(r.value)} for r in sub.itertuples()],
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "CPI inflation, Maastricht convergence window 1985-2002",
        "subtitle": (
            f"DiD = {primary_did:+.2f}pp (treated peripheral gap closure to "
            f"DEU, less control gap closure). Threshold for SUPPORTED: "
            f"{PRIMARY_DID_SUPPORTED}pp."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "CPI inflation (% YoY)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": 1992, "label": "Maastricht treaty (Feb 1992)"},
            {"type": "vline", "x": 1999, "label": "Euro launch"},
            {"type": "note", "label": (
                f"Pre-window {PRE_WINDOW[0]}-{PRE_WINDOW[1]}: treated mean "
                f"{treated_pre_mean_level:.1f}% vs DEU {deu_pre:.1f}% "
                f"vs controls {control_pre_mean_level:.1f}%. "
                f"Post-window {POST_WINDOW[0]}-{POST_WINDOW[1]}: treated "
                f"{treated_post_mean_level:.1f}% vs DEU {deu_post:.1f}% "
                f"vs controls {control_post_mean_level:.1f}%."
            )},
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients ----------
    rows = [
        {"spec": "primary", "term": "did_gap_closure_pp", "estimate": primary_did},
        {"spec": "primary", "term": "treated_mean_gap_closure_pp", "estimate": treated_mean_closure},
        {"spec": "primary", "term": "control_mean_gap_closure_pp", "estimate": control_mean_closure},
        {"spec": "informative", "term": "deu_pre_mean_inflation", "estimate": deu_pre},
        {"spec": "informative", "term": "deu_post_mean_inflation", "estimate": deu_post},
        {"spec": "informative", "term": "treated_pre_mean_inflation", "estimate": treated_pre_mean_level},
        {"spec": "informative", "term": "treated_post_mean_inflation", "estimate": treated_post_mean_level},
        {"spec": "informative", "term": "control_pre_mean_inflation", "estimate": control_pre_mean_level},
        {"spec": "informative", "term": "control_post_mean_inflation", "estimate": control_post_mean_level},
    ]
    for c, v in treated_gap_closures.items():
        rows.append({"spec": "treated_country", "term": f"gap_closure_pp_{c}", "estimate": v})
    for c, v in control_gap_closures.items():
        rows.append({"spec": "control_country", "term": f"gap_closure_pp_{c}", "estimate": v})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

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
    def fmt(x: float) -> str:
        return f"{x:+.2f}" if isinstance(x, (int, float)) and not (isinstance(x, float) and np.isnan(x)) else "NA"

    treated_rows = [
        f"| {c} | {pre_means[c]:.2f}% | {post_means[c]:.2f}% | "
        f"{abs(pre_means[c]-deu_pre):+.2f}pp -> {abs(post_means[c]-deu_post):+.2f}pp | "
        f"{treated_gap_closures[c]:+.2f}pp |"
        for c in treated_with_data
    ]
    control_rows = [
        f"| {c} | {pre_means[c]:.2f}% | {post_means[c]:.2f}% | "
        f"{abs(pre_means[c]-deu_pre):+.2f}pp -> {abs(post_means[c]-deu_post):+.2f}pp | "
        f"{control_gap_closures[c]:+.2f}pp |"
        for c in controls_with_data
    ]

    card = [
        f"# Maastricht convergence: discipline effect on inflation",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Pre-Maastricht window: {PRE_WINDOW[0]}-{PRE_WINDOW[1]}.",
        f"- Post-Maastricht / convergence-test window: {POST_WINDOW[0]}-{POST_WINDOW[1]}.",
        f"- Anchor (Bundesbank): DEU. Pre {deu_pre:.2f}%, post {deu_post:.2f}%.",
        f"- Treated periphery (ITA/ESP/PRT/GRC/IRL): mean inflation "
        f"{treated_pre_mean_level:.2f}% -> {treated_post_mean_level:.2f}%, "
        f"mean gap-closure to DEU {treated_mean_closure:+.2f}pp.",
        f"- Non-Eurozone controls (GBR/USA/JPN/CAN): mean inflation "
        f"{control_pre_mean_level:.2f}% -> {control_post_mean_level:.2f}%, "
        f"mean gap-closure to DEU {control_mean_closure:+.2f}pp.",
        f"- **DiD (primary statistic): {primary_did:+.2f}pp.** Threshold for "
        f"SUPPORTED: <= {PRIMARY_DID_SUPPORTED}pp; partial range: "
        f"({PRIMARY_DID_SUPPORTED}, {PRIMARY_DID_PARTIAL}]; refuted: > "
        f"{PRIMARY_DID_PARTIAL}pp.",
        "",
        "## Per-country results",
        "",
        "**Treated periphery:**",
        "",
        "| Country | Pre infl. | Post infl. | |gap to DEU| pre -> post | Closure |",
        "|---|---|---|---|---|",
        *treated_rows,
        "",
        "**Controls:**",
        "",
        "| Country | Pre infl. | Post infl. | |gap to DEU| pre -> post | Closure |",
        "|---|---|---|---|---|",
        *control_rows,
        "",
        "## Method",
        "",
        "Difference-in-differences on the absolute inflation gap to the "
        "Bundesbank anchor (DEU). For each country we compute window-mean "
        "WDI FP.CPI.TOTL.ZG over the 1985-1991 (pre-Maastricht) and "
        "1996-2002 (post-Maastricht convergence-test) periods, then the "
        "absolute gap to DEU's window-mean. Per-country gap closure = "
        "|post-gap| - |pre-gap| (negative = convergence). Primary statistic "
        "is the difference of group-mean closures (treated - control).",
        "",
        "Yields convergence is informative-only: vintage 10y sovereign "
        "yields for ITA/ESP/PRT/GRC across 1985-1991 are not unified on "
        "disk; falsification is on inflation alone.",
        "",
        "## Data",
        "",
        f"- world_bank_wdi:FP.CPI.TOTL.ZG (CPI inflation, %YoY)",
        f"- imf:GGXWDG_NGDP (general government debt %GDP, informative)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
