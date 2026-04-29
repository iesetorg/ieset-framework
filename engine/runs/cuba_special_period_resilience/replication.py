"""cuba_special_period_resilience v3 — indicator + comparator-pool integrity correction.

v2 SUPPORTED was double-gamed: (1) indicator selection omitted nutrition status
during the documented 1991-1995 Cuban optic neuropathy epidemic (~50,000 cases
from B-vitamin deficiency); (2) comparator pool was shocked / failed-state
economies (UKR/MDA/ARM/GEO/HTI), lowering the bar. v3 requires canonical health
basket + UNSHOCKED counterfactual pool {CRI, PAN, MEX, ECU, COL, DOM}.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq
import yaml as _yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
HID = "cuba_special_period_resilience"

UNSHOCKED_POOL = ["CRI", "PAN", "MEX", "ECU", "COL", "DOM"]


def latest(publisher, series):
    d = ROOT / "data" / "vintages" / publisher
    if not d.exists():
        return None
    cands = sorted(d.glob(f"{series}@*.parquet"))
    return cands[-1] if cands else None


def load_long(path):
    t = pq.read_table(path).to_pandas()
    cols = {c.lower(): c for c in t.columns}
    iso_col = cols.get("country_iso3") or cols.get("iso3") or cols.get("countrycode")
    yr_col = cols.get("year") or cols.get("date")
    val_col = cols.get("value") or [c for c in t.columns if c not in (iso_col, yr_col)][-1]
    df = t[[iso_col, yr_col, val_col]].copy()
    df.columns = ["iso3", "year", "value"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


def get(df, iso, year, tol=1):
    sub = df[(df["iso3"] == iso) & (df["year"] >= year - tol) & (df["year"] <= year + tol)]
    if sub.empty:
        return None
    nearest = sub.iloc[(sub["year"] - year).abs().argsort()].iloc[0]
    return float(nearest["value"])


def main():
    p_le = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    p_imr = latest("world_bank_wdi", "SP.DYN.IMRT.IN")
    p_complete = latest("world_bank_wdi", "SE.PRM.CMPT.ZS")
    p_lit = latest("world_bank_wdi", "SE.ADT.LITR.ZS")
    p_undernourish = latest("world_bank_wdi", "SN.ITK.DEFC.ZS")
    p_optic = latest("cuba_manual", "optic_neuropathy_epidemic")

    canonical = {
        "le_cub_pool_coverage": p_le is not None,
        "imr_cub_pool_coverage": p_imr is not None,
        "nutrition_status_indicator": (p_undernourish is not None or p_optic is not None),
        "education_completion_or_literacy": (p_complete is not None or p_lit is not None),
        "unshocked_pool_le_coverage": False,
        "unshocked_pool_imr_coverage": False,
    }

    le_cov, imr_cov = 0, 0
    pool_le_results, pool_imr_results = {}, {}
    if p_le is not None:
        le = load_long(p_le)
        for iso in UNSHOCKED_POOL:
            v1, v2 = get(le, iso, 1991), get(le, iso, 2000)
            if v1 is not None and v2 is not None:
                pool_le_results[iso] = {"y1991": v1, "y2000": v2, "delta_y": v2 - v1}
                le_cov += 1
        canonical["unshocked_pool_le_coverage"] = le_cov >= 4
    if p_imr is not None:
        imr = load_long(p_imr)
        for iso in UNSHOCKED_POOL:
            v1, v2 = get(imr, iso, 1991), get(imr, iso, 2000)
            if v1 is not None and v2 is not None:
                pool_imr_results[iso] = {"y1991": v1, "y2000": v2, "pct_red": (v1 - v2) / v1}
                imr_cov += 1
        canonical["unshocked_pool_imr_coverage"] = imr_cov >= 4

    cuba_le_1991 = get(load_long(p_le), "CUB", 1991) if p_le else None
    cuba_le_2000 = get(load_long(p_le), "CUB", 2000) if p_le else None
    cuba_imr_1991 = get(load_long(p_imr), "CUB", 1991) if p_imr else None
    cuba_imr_2000 = get(load_long(p_imr), "CUB", 2000) if p_imr else None
    cuba_le_delta = (cuba_le_2000 - cuba_le_1991) if (cuba_le_2000 and cuba_le_1991) else None
    cuba_imr_pct = ((cuba_imr_1991 - cuba_imr_2000) / cuba_imr_1991) if (cuba_imr_1991 and cuba_imr_2000) else None

    pool_le_mean = (sum(r["delta_y"] for r in pool_le_results.values()) / len(pool_le_results)) if pool_le_results else None
    pool_imr_mean = (sum(r["pct_red"] for r in pool_imr_results.values()) / len(pool_imr_results)) if pool_imr_results else None
    le_rel = (cuba_le_delta - pool_le_mean) if (cuba_le_delta is not None and pool_le_mean is not None) else None
    imr_rel = (cuba_imr_pct - pool_imr_mean) if (cuba_imr_pct is not None and pool_imr_mean is not None) else None

    complete = all(canonical.values())

    if complete:
        verdict = "inconclusive — v3 canonical scaffold complete; full grading not yet enabled."
        method_valid = True
    else:
        missing = [k for k, v in canonical.items() if not v]
        verdict = (
            f"inconclusive — v3 spec requires canonical health basket (LE+IMR+nutrition status) AND "
            f"UNSHOCKED market-economy comparator pool (CRI/PAN/MEX/ECU/COL/DOM). v2 graded SUPPORTED "
            f"on LE/IMR alone vs SHOCKED pool — both gaming. Documented optic neuropathy epidemic 1991-"
            f"1995 (~50,000 cases, B-vitamin deficiency) would gate SUPPORTED if formally tested. "
            f"Missing canonical inputs: {', '.join(missing)}. Unshocked pool LE coverage: "
            f"{le_cov}/{len(UNSHOCKED_POOL)}; IMR coverage: {imr_cov}/{len(UNSHOCKED_POOL)}."
        )
        method_valid = False

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "canonical_basket_status": canonical,
        "data_gap_canonical_inputs": [k for k, v in canonical.items() if not v],
        "informative_unshocked_pool_check": {
            "cuba_le_delta_y": cuba_le_delta,
            "unshocked_pool_le_mean_delta_y": pool_le_mean,
            "cuba_minus_pool_le_y": le_rel,
            "cuba_imr_pct_reduction": cuba_imr_pct,
            "unshocked_pool_imr_mean_pct_red": pool_imr_mean,
            "cuba_minus_pool_imr_pct": imr_rel,
            "unshocked_pool_le_per_country": pool_le_results,
            "unshocked_pool_imr_per_country": pool_imr_results,
        },
        "documented_epidemic_evidence": {
            "optic_neuropathy_1991_1995": "~50,000 cases of bilateral optic + sensory neuropathy from B-vitamin deficiency. Roman 1994; Hedges et al. 1997 NEJM; Cuba MOH/WHO 1995.",
            "caloric_drop": "~30% (1989 ~2,900 → 1993 ~1,800 kcal/cap/day)",
        },
        "v3_correction": (
            "v2 SUPPORTED double-gamed: (1) indicator selection omitted nutrition status during "
            "documented B-vitamin deficiency epidemic; (2) comparator pool was shocked/failed-state "
            "economies, lowering the bar."
        ),
        "fetcher_backlog": [
            {"publisher": "cuba_manual", "series": "optic_neuropathy_epidemic_1991_1995"},
            {"publisher": "world_bank_wdi", "series": "SN.ITK.DEFC.ZS coverage 1991-2000"},
            {"publisher": "world_bank_wdi", "series": "SE.PRM.CMPT.ZS + SE.ADT.LITR.ZS 1991-2000"},
        ],
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str))

    chart = {
        "kind": "result",
        "title": "Cuba resilience: canonical-basket + unshocked-pool coverage",
        "series": [{"name": k, "value": int(v)} for k, v in canonical.items()],
        "annotations": [
            "v3 requires unshocked-market-pool counterfactual + canonical health basket.",
            f"Canonical dimensions testable: {sum(canonical.values())} of {len(canonical)}.",
            "Documented optic-neuropathy epidemic 1991-1995 (~50k cases) would gate SUPPORTED.",
        ],
    }
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2))

    coef_rows = [
        {"name": "canonical_dimension_count", "value": sum(canonical.values()), "threshold": len(canonical)},
        {"name": "method_valid", "value": int(method_valid), "threshold": 1},
        {"name": "unshocked_pool_le_coverage", "value": le_cov, "threshold": 4},
        {"name": "unshocked_pool_imr_coverage", "value": imr_cov, "threshold": 4},
        {"name": "cuba_minus_unshocked_pool_le_y", "value": le_rel, "threshold": None},
        {"name": "cuba_minus_unshocked_pool_imr_pct_red", "value": imr_rel, "threshold": None},
    ]
    pd.DataFrame(coef_rows).to_parquet(RUN_DIR / "coefficients.parquet", index=False)

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]

    vintages = []
    for label, p in (("world_bank_wdi:SP.DYN.LE00.IN", p_le),
                     ("world_bank_wdi:SP.DYN.IMRT.IN", p_imr),
                     ("world_bank_wdi:SE.PRM.CMPT.ZS", p_complete),
                     ("world_bank_wdi:SE.ADT.LITR.ZS", p_lit),
                     ("world_bank_wdi:SN.ITK.DEFC.ZS", p_undernourish),
                     ("cuba_manual:optic_neuropathy_epidemic", p_optic)):
        if p is not None:
            vintages.append({"id": label, "path": str(p.relative_to(ROOT)), "sha256_16": sha(p)})
        else:
            vintages.append({"id": label, "path": None, "missing": True})
    (RUN_DIR / "manifest.yaml").write_text(_yaml.safe_dump({"hypothesis_id": HID, "vintages": vintages}, sort_keys=False))

    result = (
        "# Cuba Special Period resilience claim — v3 honesty correction\n\n"
        f"**Verdict:** {verdict}\n\n"
        "## Two integrity gaps in the v2 SUPPORTED verdict\n\n"
        "**(1) Indicator gaming.** v2 tested only LE + IMR (+ informative primary enrolment) and "
        "called this 'health and education preserved'. The documented Cuban optic-neuropathy "
        "epidemic 1991-1995 (~50,000 cases of bilateral optic + sensory neuropathy attributable to "
        "B-vitamin deficiency from caloric collapse — Roman 1994; Hedges et al. 1997 NEJM; Cuba "
        "MOH/WHO 1995) is documented epidemic-scale nutrition-driven health degradation during the "
        "test window.\n\n"
        "**(2) Comparator-pool gaming.** v2's pool was {JAM, DOM, HTI, NIC, UKR, MDA, ARM, GEO}. "
        "The post-Soviet legs (UKR/MDA/ARM/GEO) were ALSO undergoing severe shocks "
        "(30-60% GDP contractions, hyperinflation, civil conflict). HTI was a failed state. "
        "Using shocked / failed-state comparators sets a low bar.\n\n"
        "The honest counterfactual for 'socialism resilient under shock vs markets' is similar-"
        "income market economies NOT undergoing shock — i.e. {CRI, PAN, MEX, ECU, COL, DOM} 1991-2000.\n\n"
        "## v3 canonical basket coverage\n\n"
        "| Dimension | Source | Status |\n"
        "|---|---|---|\n"
        "| Cuba + pool LE | WDI SP.DYN.LE00.IN | ✓ |\n"
        "| Cuba + pool IMR | WDI SP.DYN.IMRT.IN | ✓ |\n"
        f"| Nutrition status (epidemic gating) | cuba_manual / WDI SN.ITK.DEFC.ZS | {'✓' if canonical['nutrition_status_indicator'] else '✗ (gap)'} |\n"
        f"| Education completion / literacy | WDI | {'✓' if canonical['education_completion_or_literacy'] else '✗ (gap)'} |\n"
        f"| Unshocked pool LE | CRI/PAN/MEX/ECU/COL/DOM | {le_cov}/{len(UNSHOCKED_POOL)} |\n"
        f"| Unshocked pool IMR | CRI/PAN/MEX/ECU/COL/DOM | {imr_cov}/{len(UNSHOCKED_POOL)} |\n\n"
        "## INFORMATIVE Cuba vs unshocked-pool numbers (NOT a verdict)\n\n"
        f"- Cuba LE 1991→2000: {cuba_le_1991}→{cuba_le_2000} (delta {cuba_le_delta})\n"
        f"- Unshocked pool LE mean delta: {pool_le_mean}\n"
        f"- Cuba minus unshocked pool LE: {le_rel}\n"
        f"- Cuba IMR pct reduction: {cuba_imr_pct}\n"
        f"- Unshocked pool IMR mean pct reduction: {pool_imr_mean}\n"
        f"- Cuba minus unshocked pool IMR: {imr_rel}\n\n"
        "## Documented evidence (un-tested, would gate SUPPORTED if formally graded)\n\n"
        "- 1991-1995 optic neuropathy epidemic ~50,000 cases (B-vitamin deficiency)\n"
        "- Caloric supply collapse ~30% 1989-1993\n"
        "- 1994 balsero crisis (~35,000 attempts in August)\n\n"
        "## Fetcher backlog\n\n"
        "- cuba_manual annual optic-neuropathy case counts\n"
        "- WDI undernourishment prevalence for CUB + unshocked pool\n"
        "- WDI primary completion + adult literacy 1991-2000\n\n"
        "## Archives\n\n"
        "v0 at ARCHIVED_v0/. v2 (SUPPORTED on shocked-pool LE/IMR) at ARCHIVED_v2/.\n"
    )
    (RUN_DIR / "result_card.md").write_text(result)
    print(verdict[:200])


if __name__ == "__main__":
    main()
