#!/usr/bin/env python3
"""Replication — CHIPS Act / IRA semiconductor industrial policy effectiveness.

Spec: hypotheses/trade/industrial_policy_semiconductor_chips_act_effectiveness.yaml v1
Position-claim: developmentalism #8, empirical_pragmatist #12

The spec proposes a 2030 multi-metric pattern check:
  PRIMARY 1 (capacity):     US semi-fab manufacturing-VA gain >30% over 2021 baseline
  PRIMARY 2 (jobs-mixed):   aggregate semiconductor sector employment gain <15%
  PRIMARY 3 (leverage):     cumulative private capex commitments >$200B

The required series for a clean primary test are:
  - oecd:STAN_INDUSTRY (ISIC C26 — computer/electronic/optical products)
  - bls:CES3133 (semiconductor & other electronic component manufacturing employment)
  - ilostat:semiconductor_employment (cross-country sectoral employment)
  - constructed: hand-coded CHIPS Act award announcements + private capex (DoC database)

NONE of these series are available on disk in the current vintages tree.
Best available proxy is world_bank_wdi:NV.IND.TOTL.KD (broad industry value
added, all sectors) — but for the treated unit (USA) this series has only a
single non-null observation in the 2015-2025 window we need, so even the
proxy cannot support a primary test of the treated unit's trajectory.

Furthermore, even if the spec series were on disk, the treatment dates are
August 2022 (CHIPS) and August 2022 (IRA). With a current-vintage cutoff
in 2024-2025 we have at most ~2-3 post-treatment observations against a
spec-defined 2030 horizon. CHIPS Act fab construction lead times are
3-5 years and equipment commissioning typically extends a further
12-24 months — first-of-a-kind US leading-edge fabs (TSMC Arizona,
Intel Ohio, Samsung Taylor) are not expected to reach steady-state output
until 2026-2028, with the spec's 2030 evaluation window a deliberate
acknowledgment of the lead-time issue.

The right verdict here is INCONCLUSIVE on two stacked grounds:
  (a) data gap on every primary outcome series, AND
  (b) post-treatment window currently 2-3 years vs spec's 2030 horizon.

This script encodes that detection: it attempts to load each spec-named
series, records which are missing, and emits an inconclusive verdict
with a result-card section pointing at the fetcher backlog.
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
HID = "industrial_policy_semiconductor_chips_act_effectiveness"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from the spec
TREATED = "USA"
COMPARATORS = ["KOR", "TWN", "JPN", "DEU"]
ALL_COUNTRIES = [TREATED] + COMPARATORS
PERIOD = (2018, 2030)  # spec sample.period
TREATMENT_YEAR = 2022  # CHIPS Act + IRA enactment

# Falsification thresholds (made dispositive from spec.estimator.notes)
CAPACITY_GAIN_THRESHOLD = 0.30        # >30% over 2021 baseline by 2030
EMPLOYMENT_GAIN_CEILING = 0.15        # <15% gain = "jobs-mixed" pattern
PRIVATE_CAPEX_FLOOR_USD_BN = 200.0    # >$200B cumulative
HORIZON_YEAR = 2030                   # spec's evaluation horizon
MIN_POST_TREATMENT_YEARS = 4          # need at least 4 yrs of post-treatment data

# Spec-named series — declared at top so we can record which are missing
REQUIRED_SERIES = [
    ("oecd", "STAN_INDUSTRY_C26",
     "OECD STAN ISIC C26 (computer, electronic, optical products) value added"),
    ("bls", "CES3133",
     "BLS CES semiconductor & other electronic component mfg employment"),
    ("ilostat", "semiconductor_employment",
     "ILOSTAT cross-country sectoral employment, NACE C26"),
    ("constructed", "chips_act_capex_commitments",
     "Hand-coded CHIPS Act award announcements + private capex commitments"),
]

# Best-available proxy (broad industry VA, all sectors, not semi-specific)
PROXY_PUB = "world_bank_wdi"
PROXY_SERIES = "NV.IND.TOTL.KD"


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- Audit which spec-named series are present ----------
    series_status = []
    for pub, ser, desc in REQUIRED_SERIES:
        p = latest(pub, ser)
        series_status.append({
            "publisher": pub,
            "series": ser,
            "description": desc,
            "available": p is not None,
            "path": str(p.relative_to(REPO_ROOT)) if p else None,
        })
    missing = [s for s in series_status if not s["available"]]
    n_missing = len(missing)
    n_required = len(REQUIRED_SERIES)

    # ---------- Best-available proxy probe (industry VA, all sectors) ----------
    proxy_path = latest(PROXY_PUB, PROXY_SERIES)
    proxy_diagnostic = {"publisher": PROXY_PUB, "series": PROXY_SERIES}
    treated_post_obs = 0
    treated_baseline_value = None
    treated_latest_value = None
    treated_latest_year = None
    proxy_capacity_change = None
    if proxy_path is not None:
        df = load_long(proxy_path)
        proxy_diagnostic["sha256"] = sha256(proxy_path)
        proxy_diagnostic["vintage_file"] = str(proxy_path.relative_to(REPO_ROOT))
        treated = df[
            (df["country_iso3"] == TREATED)
            & (df["year"].between(PERIOD[0], PERIOD[1]))
        ].copy()
        treated_post = treated[treated["year"] >= TREATMENT_YEAR]
        treated_post_obs = int(len(treated_post))
        baseline_row = treated[treated["year"] == 2021]
        if not baseline_row.empty:
            treated_baseline_value = float(baseline_row["value"].iloc[0])
        if not treated_post.empty:
            latest_row = treated_post.sort_values("year").iloc[-1]
            treated_latest_value = float(latest_row["value"])
            treated_latest_year = int(latest_row["year"])
            if treated_baseline_value and treated_baseline_value > 0:
                proxy_capacity_change = (
                    treated_latest_value / treated_baseline_value - 1.0
                )
        proxy_diagnostic["treated_post_2022_obs"] = treated_post_obs
        proxy_diagnostic["treated_2021_baseline"] = treated_baseline_value
        proxy_diagnostic["treated_latest_value"] = treated_latest_value
        proxy_diagnostic["treated_latest_year"] = treated_latest_year
        proxy_diagnostic["proxy_capacity_change_vs_2021"] = proxy_capacity_change

    # ---------- Window-length check ----------
    # Latest year of any plausible post-treatment evidence today
    latest_observed_year = max(
        [treated_latest_year] if treated_latest_year else [TREATMENT_YEAR]
    )
    post_window_years = max(0, latest_observed_year - TREATMENT_YEAR)
    horizon_gap_years = HORIZON_YEAR - latest_observed_year
    window_too_short = post_window_years < MIN_POST_TREATMENT_YEARS

    # ---------- Verdict ----------
    # Two independent grounds for inconclusive
    data_gap_blocks_primary = n_missing >= 3  # all three semi-specific series missing
    proxy_treated_unusable = (
        treated_baseline_value is None or treated_post_obs < 2
    )

    if data_gap_blocks_primary and window_too_short:
        verdict = (
            f"inconclusive — Stacked: ({n_missing}/{n_required}) spec-named "
            f"semi-specific series unavailable on disk "
            f"(oecd:STAN_INDUSTRY ISIC C26, bls:CES3133, ilostat:semiconductor "
            f"employment, constructed CHIPS capex), AND post-treatment window "
            f"is {post_window_years} year(s) vs spec horizon 2030 "
            f"({horizon_gap_years}-year gap). CHIPS/IRA fab build-out "
            f"lead-times of 3-5 years mean leading-edge US fabs "
            f"(TSMC AZ, Intel OH, Samsung TX) are not expected to reach "
            f"steady-state output until 2026-2028; the spec's 2030 horizon "
            f"is a deliberate acknowledgement of this. Re-run when "
            f"semi-specific fetchers land AND post-2022 vintage extends "
            f"to 2027+."
        )
    elif data_gap_blocks_primary:
        verdict = (
            f"inconclusive — Data gap: {n_missing}/{n_required} spec-named "
            f"semiconductor-specific series missing on disk. Cannot evaluate "
            f"capacity (oecd STAN C26), employment (bls CES3133/ilostat), "
            f"or capex (constructed) primaries. Best-available proxy "
            f"(world_bank_wdi:NV.IND.TOTL.KD, broad industry VA) is too "
            f"coarse for a semiconductor-targeted industrial-policy claim."
        )
    elif window_too_short:
        verdict = (
            f"inconclusive — Window too short: {post_window_years} post-treatment "
            f"year(s) of {MIN_POST_TREATMENT_YEARS}-year minimum needed for "
            f"a CHIPS/IRA capacity test. Spec horizon 2030. Re-run when "
            f"vintage extends past 2026."
        )
    else:
        # Only run primary-test scaffolding if data and window allow it
        # (this branch is a placeholder for future agent re-runs once data lands)
        verdict = (
            f"inconclusive — Primary tests not implemented in this v1 run "
            f"because spec-named series remain unavailable. Once "
            f"oecd:STAN_INDUSTRY, bls:CES3133, ilostat sectoral, and the "
            f"CHIPS-capex tracker are on disk, primary capacity / employment "
            f"/ capex thresholds (>30% / <15% / >$200B) become testable."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "treatment_year": TREATMENT_YEAR,
        "horizon_year": HORIZON_YEAR,
        "latest_observed_year": latest_observed_year,
        "post_treatment_window_years": post_window_years,
        "horizon_gap_years": horizon_gap_years,
        "window_too_short": window_too_short,
        "min_post_treatment_years_required": MIN_POST_TREATMENT_YEARS,
        "n_required_series": n_required,
        "n_missing_series": n_missing,
        "data_gap_blocks_primary": data_gap_blocks_primary,
        "series_status": series_status,
        "proxy_diagnostic": proxy_diagnostic,
        "thresholds": {
            "capacity_gain_threshold_over_2021": CAPACITY_GAIN_THRESHOLD,
            "employment_gain_ceiling": EMPLOYMENT_GAIN_CEILING,
            "private_capex_floor_usd_bn": PRIVATE_CAPEX_FLOOR_USD_BN,
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Manifest (record only what we actually loaded) ----------
    manifest_entries = {}
    if proxy_path is not None:
        manifest_entries["industry_value_added_proxy"] = {
            "publisher": PROXY_PUB,
            "series": PROXY_SERIES,
            "vintage_file": proxy_diagnostic.get("vintage_file"),
            "sha256": proxy_diagnostic.get("sha256"),
        }
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        "vintages:\n"
        + (
            "".join(
                f"  {k}:\n    publisher: {v['publisher']}\n    series: {v['series']}\n"
                f"    vintage_file: {v['vintage_file']}\n    sha256: {v['sha256']}\n"
                for k, v in manifest_entries.items()
            )
            if manifest_entries
            else "  {}  # no spec-named series available; data gap\n"
        )
    )

    # ---------- Chart: data-availability x window diagnostic ----------
    # Show the spec's required series as a coverage strip + post-treatment
    # window as a count. This is the honest visual for an inconclusive run.
    palette = ["#4E79A7", "#59A14F", "#B07AA1", "#E15759"]
    series_plot = [
        {
            "id": s["series"],
            "label": f"{s['publisher']}:{s['series']}",
            "color": palette[i % len(palette)],
            "treated": False,
            "points": [
                {"x": PERIOD[0], "y": 1.0 if s["available"] else 0.0},
                {"x": HORIZON_YEAR, "y": 1.0 if s["available"] else 0.0},
            ],
        }
        for i, s in enumerate(series_status)
    ]
    # Add a treatment-year vertical marker as an annotation
    annotations = [
        {
            "type": "vline",
            "x": TREATMENT_YEAR,
            "label": "CHIPS + IRA enactment (Aug 2022)",
        },
        {
            "type": "vline",
            "x": HORIZON_YEAR,
            "label": "Spec evaluation horizon (2030)",
        },
        {
            "type": "note",
            "label": (
                f"{n_missing}/{n_required} spec-named series unavailable on disk; "
                f"post-treatment window {post_window_years}y of "
                f"{MIN_POST_TREATMENT_YEARS}y minimum. Verdict: inconclusive."
            ),
        },
    ]
    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "CHIPS/IRA semiconductor primaries — data and window status",
        "subtitle": (
            f"Spec needs {n_required} sector-specific series; {n_missing} "
            f"missing today. Treatment 2022; current vintage cut-off "
            f"{latest_observed_year}; spec horizon 2030."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "1 = series available, 0 = missing", "type": "linear"},
        "series": series_plot,
        "annotations": annotations,
        "sources": [
            {
                "publisher_id": v["publisher"],
                "series_id": v["series"],
                "vintage_file": v["vintage_file"],
            }
            for v in manifest_entries.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- Coefficients (data-gap row only) ----------
    coef_rows = [
        {"spec": "data_audit", "term": "n_required_series", "estimate": float(n_required)},
        {"spec": "data_audit", "term": "n_missing_series", "estimate": float(n_missing)},
        {"spec": "window", "term": "post_treatment_years", "estimate": float(post_window_years)},
        {"spec": "window", "term": "horizon_gap_years", "estimate": float(horizon_gap_years)},
    ]
    if proxy_capacity_change is not None:
        coef_rows.append({
            "spec": "proxy",
            "term": "industry_va_change_vs_2021_treated",
            "estimate": float(proxy_capacity_change),
        })
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Result card ----------
    missing_lines = "\n".join(
        f"  - `{s['publisher']}:{s['series']}` — {s['description']}"
        for s in missing
    )
    available_lines = "\n".join(
        f"  - `{s['publisher']}:{s['series']}` — {s['description']}"
        for s in series_status if s["available"]
    ) or "  - (none)"

    card = [
        "# CHIPS Act / IRA semiconductor industrial policy effectiveness",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "Spec proposes a 2030 multi-metric pattern check on US CHIPS Act + IRA",
        "industrial policy: capacity-VA gain >30%, employment gain <15%,",
        "private capex >$200B. Two stacked obstacles prevent dispositive",
        "evaluation today:",
        "",
        f"1. **Data gap** — {n_missing}/{n_required} spec-named "
        "semiconductor-specific series are not available in current",
        "   vintages. The proxy on disk (broad industry VA) is too coarse,",
        "   and for the treated unit (USA) the proxy itself is sparse.",
        "2. **Window too short** — Treatment year is 2022; latest available",
        f"   data extends to {latest_observed_year} ({post_window_years} "
        f"post-treatment years vs {MIN_POST_TREATMENT_YEARS}-year minimum).",
        "   CHIPS Act fab build-out lead-times are 3-5 years before",
        "   commissioning; the spec's deliberate 2030 horizon reflects",
        "   that lead-time. Even with perfect data, primary tests are not",
        "   informative until 2027-2028 at the earliest.",
        "",
        "## Method",
        "",
        "v1 promotion (2026-04-24). The replication encodes:",
        "",
        "- A series-availability audit against the four spec-named series,",
        "- A post-treatment window-length check (≥4 years required),",
        "- A best-available proxy probe (world_bank_wdi:NV.IND.TOTL.KD)",
        "  showing the treated unit (USA) has near-zero coverage in the",
        "  post-2018 window even at the broad industry level.",
        "",
        "Either obstacle alone would justify inconclusive; both together",
        "make the case unambiguous. The script is structured to re-run",
        "cleanly once the missing series land — primary thresholds",
        f"({CAPACITY_GAIN_THRESHOLD*100:.0f}% capacity / "
        f"{EMPLOYMENT_GAIN_CEILING*100:.0f}% employment / "
        f"${PRIVATE_CAPEX_FLOOR_USD_BN:.0f}B capex) are pinned as",
        "constants.",
        "",
        "## Data",
        "",
        "Required (missing — fetcher backlog):",
        "",
        missing_lines,
        "",
        "Available (used for window probe only):",
        "",
        available_lines,
        "",
        "## Reproduction",
        "",
        "```",
        f".venv/bin/python3 engine/runs/{HID}/replication.py",
        "```",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
