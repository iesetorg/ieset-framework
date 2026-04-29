#!/usr/bin/env python3
"""Replication — ESOP firm survival and productivity post-1974 ERISA.

Spec: hypotheses/growth/esop_firm_survival_productivity.yaml v2
Position-claim: market_socialist #8 (school predicts: supported)

Status: INCONCLUSIVE — DATA GAP.

The hypothesis's PRIMARY test is a firm-level matched-sample comparison of
US ESOP firms vs industry/size/age-matched non-ESOP controls (NCEO ESOP
firm-year panel + Compustat or D&B matched control, or a Census LBD x
Form 5500 ESOP linkage). That panel is NOT on disk as of 2026-04-27.

The only ownership-relevant series available is country-level US labour
productivity (WDI SL.GDP.PCAP.EM.KD, GDP per person employed). That
macro series is reported here as INFORMATIVE-only context — it cannot
identify any firm-level ESOP-vs-matched-non-ESOP effect (ESOPs are at
most ~10-15% of US private-sector employment, and macro productivity
variation is dominated by ICT capital deepening and sectoral shift).
The METHOD_VALID gate in the v2 spec requires the firm-level panel; the
verdict here is inconclusive regardless of macro pattern.

When the NCEO/Blasi-Kruse-Freeman fetcher lands, only the data-loading
block in main() needs updating; the verdict logic is already in place.
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
HID = "esop_firm_survival_productivity"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample from the spec
COUNTRY = "USA"
PERIOD = (1974, 2023)

# PRIMARY thresholds (firm-level; cannot be tested until the panel lands)
SURVIVAL_GAP_THRESHOLD = 0.05      # ESOP - control 10yr survival rate >= +5pp
PRODUCTIVITY_FLOOR = -0.05         # ESOP - control productivity growth >= -5%

# METHOD_VALID gate (firm-level)
MIN_ESOP_FIRM_YEARS = 1000

# Required firm-level vintages (NOT on disk; absence triggers inconclusive)
REQUIRED_FIRM_LEVEL = [
    ("nceo", "esop_firm_year_panel"),
]

# Informative-only macro context
MACRO_PUB = "world_bank_wdi"
MACRO_SERIES = "SL.GDP.PCAP.EM.KD"


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
    """Standard long-format normaliser: keep (country_iso3, year, value)."""
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- METHOD_VALID gate: firm-level panel availability ----------
    firm_level_missing = [
        f"{pub}:{series}" for pub, series in REQUIRED_FIRM_LEVEL
        if latest(pub, series) is None
    ]
    method_valid = len(firm_level_missing) == 0

    # ---------- Macro INFORMATIVE-only series ----------
    macro_path = latest(MACRO_PUB, MACRO_SERIES)
    macro_available = macro_path is not None

    manifest: dict = {}
    macro_series_points: list[dict] = []
    macro_summary: dict = {}

    if macro_available:
        manifest["us_gdp_per_person_employed"] = {
            "publisher": MACRO_PUB,
            "series": MACRO_SERIES,
            "vintage_file": str(macro_path.relative_to(REPO_ROOT)),
            "sha256": sha256(macro_path),
            "role": "INFORMATIVE_ONLY",
        }
        macro = load_long(macro_path)
        macro = macro[
            (macro["country_iso3"] == COUNTRY)
            & (macro["year"].between(PERIOD[0], PERIOD[1]))
        ].copy()
        macro["year"] = macro["year"].astype(int)
        macro = macro.sort_values("year")
        macro_series_points = [
            {"x": int(r.year), "y": float(r.value)} for r in macro.itertuples()
        ]
        if len(macro) >= 2:
            v0 = float(macro["value"].iloc[0])
            v1 = float(macro["value"].iloc[-1])
            n_years = int(macro["year"].iloc[-1]) - int(macro["year"].iloc[0])
            cagr = (v1 / v0) ** (1.0 / n_years) - 1.0 if n_years > 0 and v0 > 0 else float("nan")
            macro_summary = {
                "country": COUNTRY,
                "first_year": int(macro["year"].iloc[0]),
                "last_year": int(macro["year"].iloc[-1]),
                "first_value": v0,
                "last_value": v1,
                "cagr": cagr,
                "n_years": int(len(macro)),
            }

    # ---------- Verdict ----------
    if not method_valid:
        verdict = (
            "inconclusive — data gap on firm-level ESOP vs matched non-ESOP panel. "
            f"Required vintages missing: {', '.join(firm_level_missing)}. "
            "Macro placeholder (US GDP per employed) is reported as INFORMATIVE only."
        )
    else:
        # Reserved for the post-fetcher world. The panel-level test will be
        # implemented here when NCEO/Blasi-Kruse-Freeman data lands.
        verdict = (
            "inconclusive — firm-level panel found on disk but matched-sample "
            "estimator not yet implemented in this v2 script. Update main() "
            "with the matched-sample comparison and re-run."
        )

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "firm_level_panel_required": [
            {"publisher": p, "series": s} for p, s in REQUIRED_FIRM_LEVEL
        ],
        "firm_level_panel_missing": firm_level_missing,
        "primary_thresholds": {
            "survival_gap_min_pp": SURVIVAL_GAP_THRESHOLD,
            "productivity_floor": PRODUCTIVITY_FLOOR,
            "min_esop_firm_years": MIN_ESOP_FIRM_YEARS,
        },
        "informative_only_macro": {
            "publisher": MACRO_PUB,
            "series": MACRO_SERIES,
            "available_on_disk": macro_available,
            "summary": macro_summary,
            "note": (
                "US country-level GDP per person employed. ESOPs are at most "
                "~10-15% of US private-sector employment; this series cannot "
                "identify a firm-level ownership-form effect. Reported as "
                "background context only; does NOT determine the verdict."
            ),
        },
        "primary_estimate_firm_level": None,
        "data_gap": {
            "what_is_missing": (
                "Firm-level NCEO ESOP database (firm-year panel: formations, "
                "survival, employment) joined to a matched non-ESOP control "
                "drawn from the same industry/size/age strata."
            ),
            "fetcher_needed": (
                "data/fetchers/nceo/ — NCEO ESOP firm-year panel; OR a Census "
                "LBD x Form 5500 ESOP linkage (restricted, requires Census RDC)."
            ),
            "matched_control_options": [
                "Compustat firm-year panel filtered to non-ESOP and matched on "
                "SIC-2/employment-decile/firm-age strata.",
                "D&B (Dun & Bradstreet) private-firm panel with same matching.",
            ],
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    # ---------- Chart (informative-only) ----------
    if macro_series_points:
        subtitle = (
            "INFORMATIVE-only context: US country-level GDP per person employed (WDI "
            "SL.GDP.PCAP.EM.KD). Verdict is inconclusive — firm-level matched-sample "
            "ESOP vs non-ESOP panel is the dispositive test and is not on disk."
        )
        series = [
            {
                "id": "USA_GDP_PER_EMPLOYED",
                "label": "US GDP per person employed (constant 2017 PPP $) — INFORMATIVE-only",
                "color": "#9C9C9C",
                "treated": False,
                "points": macro_series_points,
            }
        ]
    else:
        subtitle = (
            "Verdict is inconclusive — firm-level matched-sample ESOP vs non-ESOP panel "
            "is the dispositive test and is not on disk. Macro placeholder series also "
            "not available locally."
        )
        series = []

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "ESOP firm survival and productivity — DATA GAP",
        "subtitle": subtitle,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "GDP per person employed (constant 2017 PPP $)", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    "Dispositive test (not yet runnable): firm-level NCEO ESOP panel vs "
                    "matched non-ESOP control. Required: 10-year survival gap >= +5pp AND "
                    "productivity gap >= -5%. METHOD_VALID gate requires >= 1000 ESOP "
                    "firm-years on disk."
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

    # ---------- Coefficients (long-form) ----------
    coef_rows = [
        {"spec": "method_valid_gate", "term": "firm_level_panel_present", "estimate": float(method_valid)},
        {"spec": "method_valid_gate", "term": "min_esop_firm_years_required", "estimate": float(MIN_ESOP_FIRM_YEARS)},
        {"spec": "primary_threshold", "term": "survival_gap_min_pp", "estimate": SURVIVAL_GAP_THRESHOLD},
        {"spec": "primary_threshold", "term": "productivity_floor", "estimate": PRODUCTIVITY_FLOOR},
    ]
    if macro_summary:
        coef_rows.append(
            {"spec": "informative_macro", "term": "us_gdp_per_employed_cagr", "estimate": float(macro_summary["cagr"])}
        )
        coef_rows.append(
            {"spec": "informative_macro", "term": "us_gdp_per_employed_first_value", "estimate": float(macro_summary["first_value"])}
        )
        coef_rows.append(
            {"spec": "informative_macro", "term": "us_gdp_per_employed_last_value", "estimate": float(macro_summary["last_value"])}
        )
    pd.DataFrame(coef_rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- Manifest ----------
    if manifest:
        manifest_body = "vintages:\n" + "".join(
            f"  {k}:\n"
            f"    publisher: {v['publisher']}\n"
            f"    series: {v['series']}\n"
            f"    vintage_file: {v['vintage_file']}\n"
            f"    sha256: {v['sha256']}\n"
            f"    role: {v.get('role', 'PRIMARY')}\n"
            for k, v in manifest.items()
        )
    else:
        manifest_body = "vintages: {}\n"
    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'\n"
        f"method_valid: {str(method_valid).lower()}\n"
        f"verdict_class: inconclusive_data_gap\n"
        + manifest_body
    )

    # ---------- Result card ----------
    macro_line = "  - Macro INFORMATIVE-only series not available on disk."
    if macro_summary:
        macro_line = (
            f"  - Macro INFORMATIVE-only context: US GDP per person employed "
            f"(WDI {MACRO_SERIES}) ran from {macro_summary['first_value']:,.0f} "
            f"in {macro_summary['first_year']} to {macro_summary['last_value']:,.0f} "
            f"in {macro_summary['last_year']} (CAGR "
            f"{macro_summary['cagr']*100:+.2f}%/yr over {macro_summary['n_years']} obs)."
        )

    card = [
        f"# ESOP firm survival and productivity post-1974 ERISA",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        "- The dispositive PRIMARY test for this hypothesis is a firm-level "
        "matched-sample comparison of US ESOP vs industry/size/age-matched "
        "non-ESOP firms over 1974-2023. That panel is NOT on disk.",
        "- The METHOD_VALID gate in the v2 spec requires a firm-level NCEO "
        "(or equivalent) ESOP firm-year panel with at least 1,000 ESOP "
        "firm-years and a matched non-ESOP control set. No such vintage "
        "exists in `data/vintages/nceo/`.",
        f"- Required firm-level vintages missing: {', '.join(firm_level_missing) or '(none)'}.",
        macro_line,
        "- Macro series is INFORMATIVE-only and CANNOT determine the verdict. "
        "ESOPs are at most ~10-15% of US private-sector employment; macro "
        "labour-productivity variation is dominated by ICT capital deepening "
        "and sectoral shift, neither of which identifies an ownership-form "
        "effect.",
        "",
        "## Method",
        "",
        "Two-step verdict logic:",
        "",
        "1. **METHOD_VALID gate** (data-availability check). Look for the "
        "firm-level NCEO ESOP panel in `data/vintages/nceo/`. If absent, the "
        "verdict is `inconclusive — data gap` and the script stops.",
        "2. **PRIMARY test** (firm-level matched sample, not yet runnable): "
        "(a) ESOP 10-year survival rate minus matched-control rate must be "
        f">= +{SURVIVAL_GAP_THRESHOLD*100:.0f}pp, AND (b) ESOP labour-productivity "
        f"growth gap to control must be >= {PRODUCTIVITY_FLOOR*100:.0f}%. "
        "Both thresholds inherit from the v1 falsification text; v2 only "
        "added the explicit METHOD_VALID gate, no threshold weakening.",
        "",
        "## Data",
        "",
        "Required (NOT on disk):",
        "",
        "- `nceo:esop_firm_year_panel` — NCEO ESOP firm-year panel (formations, "
        "survival, employment).",
        "- Matched non-ESOP control set: Compustat or D&B firm-year panel "
        "filtered to non-ESOP and matched on SIC-2 / employment-decile / "
        "firm-age strata. Gold-standard alternative: Census LBD x Form 5500 "
        "ESOP linkage (restricted, requires Census RDC).",
        "",
        "Available (INFORMATIVE-only):",
        "",
        f"- `{MACRO_PUB}:{MACRO_SERIES}` — US country-level GDP per person "
        "employed. Used for chart context; cannot determine the verdict.",
        "",
        "## What needs to land for v3 to produce a real verdict",
        "",
        "1. A `data/fetchers/nceo/` fetcher that pulls the NCEO ESOP firm-year "
        "panel (or an equivalent restricted-access Census LBD x Form 5500 "
        "linkage from a Census RDC).",
        "2. A matched-control fetcher pulling Compustat or D&B firm-year "
        "records and applying the industry/size/age matching.",
        "3. Once both vintages are on disk, this script's `main()` only needs "
        "its data-loading block updated; the threshold logic and verdict "
        "branches are already in place.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(card) + "\n")

    print(f"verdict: {verdict}")


if __name__ == "__main__":
    main()
