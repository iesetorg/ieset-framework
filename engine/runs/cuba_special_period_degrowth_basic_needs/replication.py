"""cuba_special_period_degrowth_basic_needs v3 — indicator-integrity correction.

v2 graded SUPPORTED on 3-indicator favourable subset (LE/IMR/primary
enrolment) while caveats noted caloric supply collapsed ~30% and the
1994 balsero crisis revealed mass dissatisfaction. That's indicator
gaming. Canonical basic-needs literature (Streeten 1981, Sen, UNDP HDI
extensions) treats food security as the primary basic need; emigration
as the canonical revealed-preference welfare metric. v3 requires the
canonical basket and emits inconclusive on data gap.
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
HID = "cuba_special_period_degrowth_basic_needs"


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


def cuba_window(df, lo, hi):
    return df[(df["iso3"] == "CUB") & (df["year"] >= lo) & (df["year"] <= hi)].sort_values("year")


def main():
    p_gdp = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    p_le = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    p_imr = latest("world_bank_wdi", "SP.DYN.IMRT.IN")
    p_enrol = latest("world_bank_wdi", "SE.PRM.ENRR")
    p_kcal = latest("faostat", "food_balance_sheets")
    p_emig = latest("cuba_manual", "emigration_share_pct")

    canonical_status = {
        "P1_gdp_pc": p_gdp is not None,
        "P2_caloric_supply_1989_2000": False,
        "P3a_life_expectancy": p_le is not None,
        "P3b_infant_mortality": p_imr is not None,
        "P3c_primary_enrolment": p_enrol is not None,
        "P4_emigration_annual_1989_2000": False,
    }

    kcal_obs = 0
    if p_kcal is not None:
        kcal_obs = len(cuba_window(load_long(p_kcal), 1989, 2000))
        canonical_status["P2_caloric_supply_1989_2000"] = kcal_obs >= 8
    emig_obs = 0
    if p_emig is not None:
        emig_obs = len(cuba_window(load_long(p_emig), 1989, 2000))
        canonical_status["P4_emigration_annual_1989_2000"] = emig_obs >= 8

    canonical_complete = all(canonical_status.values())

    informative = {}
    if p_gdp is not None:
        gdp_w = cuba_window(load_long(p_gdp), 1989, 2000)
        if not gdp_w.empty:
            v_1989 = gdp_w[gdp_w["year"] == 1989]["value"]
            trough = gdp_w[(gdp_w["year"] >= 1991) & (gdp_w["year"] <= 1995)]["value"]
            if not v_1989.empty and not trough.empty:
                informative["gdp_pc_peak_to_trough_decline_fraction"] = (float(v_1989.iloc[0]) - float(trough.min())) / float(v_1989.iloc[0])

    for name, p, kind in (("max_le_decline_fraction", p_le, "decline"),
                          ("max_imr_rise_fraction", p_imr, "rise"),
                          ("max_enrol_decline_fraction", p_enrol, "decline")):
        if p is not None:
            w = cuba_window(load_long(p), 1989, 2000)
            if not w.empty:
                base = w[w["year"] == 1989]["value"]
                if not base.empty:
                    if kind == "rise":
                        informative[name] = (float(w["value"].max()) - float(base.iloc[0])) / float(base.iloc[0])
                    else:
                        informative[name] = (float(base.iloc[0]) - float(w["value"].min())) / float(base.iloc[0])

    if canonical_complete:
        verdict = "inconclusive — v3 canonical scaffold complete; full grading not yet enabled."
        method_valid = True
    else:
        missing = [k for k, v in canonical_status.items() if not v]
        verdict = (
            f"inconclusive — canonical basic-needs basket incomplete. v2 graded SUPPORTED on a "
            f"3-indicator favourable subset (LE/IMR/enrolment) while caloric supply collapsed "
            f"~30% (Garfield & Santana 1997) and the 1994 balsero crisis revealed mass emigration. "
            f"v3 requires the canonical basket (Streeten/Sen/UNDP HDI extensions). Missing canonical "
            f"inputs: {', '.join(missing)}. FAO caloric obs in window: {kcal_obs}/12; emigration obs: {emig_obs}/12."
        )
        method_valid = False

    diagnostics = {
        "verdict": verdict,
        "method_valid": method_valid,
        "canonical_basket_status": canonical_status,
        "canonical_basket_complete": canonical_complete,
        "data_gap_canonical_inputs": [k for k, v in canonical_status.items() if not v],
        "informative_v2_subset": informative,
        "documented_qualitative_evidence": {
            "caloric_collapse_1989_1993": "~30% decline (Garfield & Santana 1997)",
            "balsero_crisis_1994": "~35,000 emigration attempts in August 1994 alone",
            "libreta_persistence_2024": "63% of households still depend on rationing",
        },
        "v3_correction": (
            "v2 SUPPORTED was indicator-gamed: chosen 3-indicator subset favoured Cuban performance "
            "while canonical primary basic need (food security) and revealed-preference welfare "
            "metric (emigration) were omitted."
        ),
        "fetcher_backlog": [
            {"publisher": "faostat", "series": "food_balance_sheets",
             "needed": "1989-2000 annual caloric supply (current slug 2010+ only)"},
            {"publisher": "cuba_manual", "series": "emigration_share_annual",
             "needed": "1989-2000 annual (current decade-stamp only)"},
        ],
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str))

    chart = {
        "kind": "result",
        "title": "Cuba Special Period: canonical basic-needs basket coverage",
        "series": [{"name": k, "value": int(v)} for k, v in canonical_status.items()],
        "annotations": [
            "v3 requires canonical basket (Streeten/Sen/UNDP).",
            f"{sum(canonical_status.values())} of {len(canonical_status)} dimensions testable.",
            "Verdict: inconclusive — food security + emigration data missing.",
        ],
    }
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2))

    coef_rows = [
        {"name": "canonical_dimension_count", "value": sum(canonical_status.values()), "threshold": len(canonical_status)},
        {"name": "method_valid", "value": int(method_valid), "threshold": 1},
        {"name": "kcal_obs_1989_2000", "value": kcal_obs, "threshold": 8},
        {"name": "emig_obs_1989_2000", "value": emig_obs, "threshold": 8},
    ]
    for k, v in informative.items():
        coef_rows.append({"name": f"informative_{k}", "value": v, "threshold": None})
    pd.DataFrame(coef_rows).to_parquet(RUN_DIR / "coefficients.parquet", index=False)

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]

    vintages = []
    for label, p in (("world_bank_wdi:NY.GDP.PCAP.KD", p_gdp),
                     ("world_bank_wdi:SP.DYN.LE00.IN", p_le),
                     ("world_bank_wdi:SP.DYN.IMRT.IN", p_imr),
                     ("world_bank_wdi:SE.PRM.ENRR", p_enrol),
                     ("faostat:food_balance_sheets", p_kcal),
                     ("cuba_manual:emigration_share_pct", p_emig)):
        if p is not None:
            vintages.append({"id": label, "path": str(p.relative_to(ROOT)), "sha256_16": sha(p)})
        else:
            vintages.append({"id": label, "path": None, "missing": True})
    (RUN_DIR / "manifest.yaml").write_text(_yaml.safe_dump({"hypothesis_id": HID, "vintages": vintages}, sort_keys=False))

    result = (
        "# Cuba Special Period basic-needs preservation — v3 honesty correction\n\n"
        f"**Verdict:** {verdict}\n\n"
        "## Why v3 lands inconclusive\n\n"
        "v2 graded SUPPORTED on a 3-indicator subset (LE / IMR / primary enrolment) while caveats "
        "explicitly noted that caloric supply per capita dropped ~30% from ~2,900 to ~1,800 kcal/cap/day "
        "between 1989 and 1993 (Garfield & Santana 1997 / FAO FBS) and that the 1994 balsero crisis "
        "produced ~35,000 emigration attempts in August alone. That's indicator gaming.\n\n"
        "Canonical basic-needs literature (Streeten 1981, Sen, UNDP HDI extensions) treats food "
        "security as the primary basic need; emigration as the canonical revealed-preference welfare "
        "metric. SUPPORTED on a favourable subset while the canonical-primary indicator collapsed "
        "is not an honest affirmation.\n\n"
        "## v3 canonical basket\n\n"
        "| Dimension | Source | On disk for 1989-2000? |\n"
        "|---|---|---|\n"
        "| GDP per capita | WDI NY.GDP.PCAP.KD | ✓ |\n"
        "| Caloric supply / cap / day | FAO FBS | **✗** (slug covers 2010+ only) |\n"
        "| Life expectancy | WDI SP.DYN.LE00.IN | ✓ |\n"
        "| Infant mortality | WDI SP.DYN.IMRT.IN | ✓ |\n"
        "| Primary enrolment | WDI SE.PRM.ENRR | ✓ |\n"
        "| Emigration (annual) | cuba_manual | **✗** (decade-stamp only) |\n\n"
        "4 of 6 canonical dimensions testable; 2 are documented data gaps. Per the framework's "
        "indicator-integrity rule, omission of canonical indicators triggers METHOD_VALID failure → "
        "inconclusive, not SUPPORTED on the favourable subset.\n\n"
        "## INFORMATIVE-only v2 subset numbers (NOT a verdict)\n\n"
    )
    for k, v in informative.items():
        result += f"- {k}: {v:.4f}\n"
    result += (
        "\n## Documented qualitative evidence (un-tested)\n\n"
        "- Caloric collapse 1989→1993: ~30% decline (Garfield & Santana 1997)\n"
        "- 1994 balsero crisis: ~35,000 attempts in August alone\n"
        "- Libreta persistence: 63% of households as of 2024\n\n"
        "## Fetcher backlog\n\n"
        "- faostat:food_balance_sheets full annual 1961+\n"
        "- cuba_manual emigration annual 1989-2000\n\n"
        "## Archives\n\n"
        "v0 at ARCHIVED_v0/. v2 (3-indicator subset, SUPPORTED) at ARCHIVED_v2/.\n"
    )
    (RUN_DIR / "result_card.md").write_text(result)
    print(verdict[:200])


if __name__ == "__main__":
    main()
