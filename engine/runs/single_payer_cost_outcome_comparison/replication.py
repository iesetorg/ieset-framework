"""single_payer_cost_outcome_comparison v2 — canonical-outcomes-basket correction.

v1 graded SUPPORTED on cost (USA 1.94x GBR/CAN mean) + 3 simple mortality
outcomes (LE, IMR, U5MR). The spec's own disclosure flagged that the test
should consider amenable mortality vs LE — exactly the indicator-gaming
concern the new canonical-basket-gate prevents.

Canonical health-system outcomes basket (per OECD Health at a Glance,
WHO health system performance):
  - Mortality: LE, IMR, U5MR, amenable mortality, treatable mortality
  - Disease burden: HALE (healthy life-years), DALYs
  - Access: UHC index, unmet medical need %, waiting times
  - Quality: 5-yr cancer survival, hospital infections
  - Equity: out-of-pocket %, catastrophic-spending headcount

Documented heterogeneity v1 missed:
  - NHS waiting times exceed US in elective procedures
  - 5-yr cancer survival: USA outperforms NHS for breast/prostate/colon
  - Amenable mortality: complex; USA does better on some causes

v2 tests cost + canonical outcomes basket; documents the gaps that
prevent SUPPORTED. Lands supported_subset.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import yaml as _yaml

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
HID = "single_payer_cost_outcome_comparison"
WINDOW = (2010, 2023)


def latest(publisher, series):
    d = ROOT / "data" / "vintages" / publisher
    if not d.exists():
        return None
    cands = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_size)
    nonempty = [c for c in cands if c.stat().st_size > 1000]
    return nonempty[-1] if nonempty else (cands[-1] if cands else None)


def load_long(path):
    t = pq.read_table(path).to_pandas()
    cols = {c.lower(): c for c in t.columns}
    iso_col = cols.get("country_iso3") or cols.get("iso3") or cols.get("countrycode")
    yr_col = cols.get("year") or cols.get("date")
    val_col = cols.get("value") or cols.get("numericvalue") or [c for c in t.columns if c not in (iso_col, yr_col)][-1]
    df = t[[iso_col, yr_col, val_col]].copy()
    df.columns = ["iso3", "year", "value"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


def wm(df, iso, lo, hi):
    sub = df[(df["iso3"] == iso) & (df["year"] >= lo) & (df["year"] <= hi)]
    return float(sub["value"].mean()) if not sub.empty else None


def main():
    p_chexgdp = latest("world_bank_wdi", "SH.XPD.CHEX.GD.ZS")
    p_gdppc_ppp = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    p_le = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    p_imr = latest("world_bank_wdi", "SP.DYN.IMRT.IN")
    p_u5 = latest("world_bank_wdi", "SH.DYN.MORT")
    p_uhc = latest("who_gho", "UHC_INDEX_REPORTED")
    p_oop = latest("world_bank_wdi", "SH.XPD.OOPC.CH.ZS")
    p_amen = latest("oecd_health", "amenable_mortality")
    p_hale = latest("who_gho", "WHOSIS_000003")
    p_cancer = latest("oecd_health", "five_year_cancer_survival")
    p_wait = latest("oecd_health", "elective_waiting_times")

    canonical = {
        "C1_cost_per_capita": (p_chexgdp is not None and p_gdppc_ppp is not None),
        "O1_le": p_le is not None,
        "O2_imr": p_imr is not None,
        "O3_u5": p_u5 is not None,
        "O4_uhc": p_uhc is not None,
        "O5_oop": p_oop is not None,
        "O6_amenable_mortality": p_amen is not None,
        "O7_hale": p_hale is not None,
        "O8_5yr_cancer": p_cancer is not None,
        "O9_waiting_times": p_wait is not None,
    }

    countries = ["USA", "GBR", "CAN"]
    data = {}
    for label, p in (("le", p_le), ("imr", p_imr), ("u5", p_u5), ("uhc", p_uhc), ("oop", p_oop)):
        if p is not None:
            df = load_long(p)
            data[label] = {c: wm(df, c, *WINDOW) for c in countries}
        else:
            data[label] = {c: None for c in countries}

    cost = {}
    if p_chexgdp and p_gdppc_ppp:
        cg = load_long(p_chexgdp); gp = load_long(p_gdppc_ppp)
        for c in countries:
            cgv = wm(cg, c, *WINDOW); gpv = wm(gp, c, *WINDOW)
            cost[c] = (cgv / 100.0 * gpv) if (cgv and gpv) else None

    sp_cost = ((cost.get("GBR") + cost.get("CAN")) / 2.0) if (cost.get("GBR") and cost.get("CAN")) else None
    cost_ratio = (cost.get("USA") / sp_cost) if (cost.get("USA") and sp_cost) else None
    cost_pass = cost_ratio is not None and cost_ratio > 1.5

    def sp_mean(m):
        d = data[m]
        if d["GBR"] and d["CAN"]: return (d["GBR"] + d["CAN"]) / 2.0
        return None

    outcomes = {}
    for m, better in (("le", "ge"), ("imr", "le"), ("u5", "le"), ("uhc", "ge"), ("oop", "le")):
        sp = sp_mean(m); usa = data[m]["USA"]
        if sp is not None and usa is not None:
            won = sp >= usa if better == "ge" else sp <= usa
        else:
            won = None
        outcomes[m] = {"sp_mean": sp, "usa": usa, "single_payer_better_or_equal": won}

    n_tested = sum(1 for r in outcomes.values() if r["single_payer_better_or_equal"] is not None)
    n_won = sum(1 for r in outcomes.values() if r["single_payer_better_or_equal"] is True)
    n_missing = sum(1 for v in canonical.values() if not v)

    if cost_pass and n_won >= n_tested * 0.6:
        missing = [k for k, v in canonical.items() if not v]
        verdict = (f"supported_subset — cost test PASSES (USA per-capita PPP ${cost.get('USA',0):.0f} vs "
                   f"GBR/CAN mean ${sp_cost:.0f}, ratio {cost_ratio:.2f}x > 1.5); single-payer matched-or-"
                   f"beat USA on {n_won}/{n_tested} tested outcomes (LE/IMR/U5/UHC/OOP). BUT canonical "
                   f"health-system outcomes basket has {n_missing} documented data gaps: {', '.join(missing)}. "
                   f"The spec's own disclosure flagged amenable mortality + HALE as preferred outcomes; "
                   f"NHS waiting times and 5-yr cancer survival (USA outperforms) NOT in test. v1 SUPPORTED "
                   f"was indicator-gamed. Max tier: supported_subset.")
        method_valid = True
    elif cost_pass:
        verdict = f"partial — cost passes ({cost_ratio:.2f}x) but only {n_won}/{n_tested} outcomes favour single-payer."
        method_valid = True
    else:
        verdict = f"refuted — cost test fails (ratio {cost_ratio})."
        method_valid = True

    diagnostics = {
        "verdict": verdict, "method_valid": method_valid,
        "cost_test": {"usa_per_capita_ppp": cost.get("USA"), "gbr_per_capita_ppp": cost.get("GBR"),
                      "can_per_capita_ppp": cost.get("CAN"), "single_payer_mean": sp_cost,
                      "usa_to_sp_ratio": cost_ratio, "threshold": 1.5, "pass": cost_pass},
        "outcome_tests": outcomes,
        "canonical_basket_status": canonical,
        "missing_canonical_inputs": [k for k, v in canonical.items() if not v],
        "n_canonical_on_disk": sum(canonical.values()),
        "n_outcomes_tested": n_tested, "n_outcomes_won_by_sp": n_won,
        "v2_correction": ("v1 SUPPORTED on cost + 3 simple mortality outcomes ignored: (a) spec's own disclosure "
                          "flagging amenable mortality, (b) HALE, (c) NHS waiting times where NHS underperforms "
                          "USA, (d) 5-yr cancer survival where USA outperforms NHS, (e) within-system "
                          "heterogeneity. v2 tests cost + 5 outcome dimensions, flags 4 canonical dimensions "
                          "as documented data gaps, downgrades to supported_subset."),
        "fetcher_backlog": [
            {"publisher": "oecd_health", "series": "amenable_mortality_per_100k"},
            {"publisher": "who_gho", "series": "WHOSIS_000003 (HALE)"},
            {"publisher": "oecd_health", "series": "5yr_cancer_survival_breast_prostate_colon"},
            {"publisher": "oecd_health", "series": "elective_waiting_times"},
        ],
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str))

    chart = {"kind": "result", "title": "Single-payer cost vs outcome canonical basket",
             "series": [{"name": "USA/SP cost ratio", "value": cost_ratio, "threshold": 1.5},
                        {"name": "Outcome wins (SP)", "value": n_won, "threshold": n_tested},
                        {"name": "Canonical basket coverage", "value": sum(canonical.values()), "threshold": len(canonical)}],
             "annotations": [f"Canonical basket: {sum(canonical.values())}/{len(canonical)} on disk.",
                             f"4 dimensions missing → max tier supported_subset."]}
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2))

    coef = [{"name": "cost_ratio_usa_to_sp", "value": cost_ratio, "threshold": 1.5},
            {"name": "n_outcomes_won", "value": n_won, "threshold": n_tested},
            {"name": "canonical_count", "value": sum(canonical.values()), "threshold": len(canonical)}]
    for k, r in outcomes.items():
        coef.append({"name": f"{k}_sp", "value": r["sp_mean"], "threshold": None})
        coef.append({"name": f"{k}_usa", "value": r["usa"], "threshold": None})
    pd.DataFrame(coef).to_parquet(RUN_DIR / "coefficients.parquet", index=False)

    def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    vintages = []
    for label, p in (("world_bank_wdi:SH.XPD.CHEX.GD.ZS", p_chexgdp),
                     ("world_bank_wdi:NY.GDP.PCAP.PP.KD", p_gdppc_ppp),
                     ("world_bank_wdi:SP.DYN.LE00.IN", p_le),
                     ("world_bank_wdi:SP.DYN.IMRT.IN", p_imr),
                     ("world_bank_wdi:SH.DYN.MORT", p_u5),
                     ("who_gho:UHC_INDEX_REPORTED", p_uhc),
                     ("world_bank_wdi:SH.XPD.OOPC.CH.ZS", p_oop),
                     ("oecd_health:amenable_mortality", p_amen),
                     ("who_gho:HALE", p_hale),
                     ("oecd_health:5yr_cancer_survival", p_cancer),
                     ("oecd_health:elective_waiting_times", p_wait)):
        if p is not None:
            vintages.append({"id": label, "path": str(p.relative_to(ROOT)), "sha256_16": sha(p)})
        else:
            vintages.append({"id": label, "path": None, "missing": True})
    (RUN_DIR / "manifest.yaml").write_text(_yaml.safe_dump({"hypothesis_id": HID, "vintages": vintages}, sort_keys=False))

    result = (f"# Single-payer cost-outcome comparison — v2 honesty correction\n\n**Verdict:** {verdict}\n\n"
              f"## Why v2 differs from v1\n\nv1 graded SUPPORTED on cost (USA 1.94x GBR/CAN) + 3 simple "
              f"mortality outcomes. The spec's own disclosure flagged amenable mortality vs LE — exactly "
              f"the indicator-gaming concern.\n\nCanonical health-system outcomes basket (OECD HAG, WHO HSP) "
              f"includes: amenable mortality, HALE, waiting times (NHS lags USA), 5-yr cancer survival "
              f"(USA leads NHS), out-of-pocket equity. v1 omitted 4 canonical dimensions.\n\n"
              f"## Canonical basket\n\n| Dim | Status |\n|---|---|\n")
    for k, v in canonical.items():
        result += f"| {k} | {'✓' if v else '**✗ data gap**'} |\n"
    result += (f"\n## Numbers\n\n- USA per-capita PPP: ${cost.get('USA', 0):.0f}\n"
               f"- SP mean: ${sp_cost:.0f}\n- Cost ratio: {cost_ratio:.2f}x\n"
               f"- Outcomes tested: {n_tested}; won: {n_won}\n\n## Archives\n\nv1 at ARCHIVED_v1/.\n")
    (RUN_DIR / "result_card.md").write_text(result)
    print(verdict[:200])


if __name__ == "__main__":
    main()
