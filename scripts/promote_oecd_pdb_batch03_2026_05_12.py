#!/usr/bin/env python3
"""Promote and run Batch 03 OECD PDB productivity hypotheses.

This script is intentionally self-contained because the 2026-05-12 monthly
swarm assigned this agent ownership of only Batch 03 OECD Productivity /
Frontier Convergence artifacts.
"""
from __future__ import annotations

import hashlib
import json
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
HYP = ROOT / "hypotheses" / "growth"
STEEL = ROOT / "hypotheses" / "steelman"
AUDITS = ROOT / "engine" / "audits"

PDB_REQUIRED = "oecd:OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0"
PMR_REQUIRED = "oecd_pmr:OECD.ECO.GCRD,DSD_PMR@DF_PMR,1.2"
TAX_REQUIRED = "oecd:OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1"
INVESTMENT_SHARE_REQUIRED = "oecd_pdb:investment share / gross fixed capital formation share in OECD PDB"

OECD_CORE = {
    "AUS", "AUT", "BEL", "CAN", "CHE", "CZE", "DEU", "DNK", "ESP", "FIN",
    "FRA", "GBR", "GRC", "HUN", "IRL", "ISL", "ITA", "JPN", "KOR", "LUX",
    "MEX", "NLD", "NOR", "NZL", "POL", "PRT", "SVK", "SVN", "SWE", "TUR",
    "USA",
}
SMALL_OPEN = {
    "AUT", "BEL", "CHE", "CZE", "DNK", "FIN", "IRL", "NLD", "NOR", "NZL",
    "PRT", "SVK", "SVN", "SWE",
}


@dataclass(frozen=True)
class ReadySpec:
    run_id: str
    title: str
    claim: str
    formula: str
    data_filter: str
    expected_sign: str
    treatment: str
    outcome: str
    min_obs: int = 120
    min_countries: int = 12


READY_SPECS = [
    ReadySpec(
        "oecd_pdb_gdp_hour_frontier_convergence_1950_2025",
        "OECD PDB GDP/hour frontier convergence",
        "Countries farther below the annual OECD labour-productivity frontier subsequently grow faster in GDP per hour.",
        "gdp_hour_growth ~ frontier_gap_lag + C(country) + C(year)",
        "year >= 1971 and year <= 2025",
        "positive",
        "frontier_gap_lag",
        "gdp_hour_growth",
    ),
    ReadySpec(
        "oecd_pdb_tfp_growth_frontier_persistence_1970_2025",
        "OECD PDB TFP growth persistence",
        "OECD multifactor-productivity growth has country-level persistence after common year shocks.",
        "tfp_growth ~ tfp_growth_lag + C(country) + C(year)",
        "year >= 1986 and year <= 2024",
        "positive",
        "tfp_growth_lag",
        "tfp_growth",
        min_obs=180,
        min_countries=15,
    ),
    ReadySpec(
        "oecd_pdb_capital_deepening_without_tfp_limit",
        "Capital deepening without TFP limit",
        "Capital deepening alone is a weak predictor of labour-productivity growth once MFP contribution is included.",
        "lp_growth ~ capital_deepening + tfp_contribution + C(country) + C(year)",
        "year >= 1986 and year <= 2024",
        "tfp_dominates",
        "capital_deepening",
        "lp_growth",
        min_obs=180,
        min_countries=15,
    ),
    ReadySpec(
        "oecd_pdb_small_open_economy_frontier_convergence",
        "Small open economy frontier convergence",
        "Small open OECD economies show conditional labour-productivity convergence toward the annual frontier.",
        "lp_growth ~ frontier_gap_lag + C(country) + C(year)",
        "small_open == 1 and year >= 1971 and year <= 2025",
        "positive",
        "frontier_gap_lag",
        "lp_growth",
        min_obs=250,
        min_countries=10,
    ),
    ReadySpec(
        "oecd_pdb_market_reform_productivity_compounder",
        "PMR reform productivity compounder",
        "Countries with larger PMR declines from 2018 to 2023 saw faster PDB labour-productivity growth in the following window.",
        "lp_growth_2018_2024 ~ pmr_decline_2018_2023",
        "cross_section_pmr",
        "positive",
        "pmr_decline_2018_2023",
        "lp_growth_2018_2024",
        min_obs=12,
        min_countries=12,
    ),
    ReadySpec(
        "oecd_pdb_hours_reduction_output_tradeoff_panel",
        "Hours reduction output tradeoff",
        "Average-hours reductions are not mechanically associated with lower real GVA growth in OECD PDB panels after fixed effects.",
        "gva_growth ~ hours_growth + C(country) + C(year)",
        "year >= 1971 and year <= 2025",
        "not_negative_large",
        "hours_growth",
        "gva_growth",
    ),
    ReadySpec(
        "oecd_pdb_post_2008_productivity_hysteresis_panel",
        "Post-2008 productivity hysteresis",
        "OECD labour-productivity growth was persistently lower after 2008 than before 2008.",
        "lp_growth ~ post_2008 + C(country)",
        "year >= 1995 and year <= 2024 and year != 2020",
        "negative",
        "post_2008",
        "lp_growth",
    ),
    ReadySpec(
        "oecd_pdb_public_sector_share_productivity_drag",
        "Public-sector share productivity drag",
        "A larger public-administration, education, and health GVA share predicts slower subsequent total-economy labour-productivity growth.",
        "lp_growth ~ public_gva_share_lag + C(country) + C(year)",
        "year >= 1971 and year <= 2025",
        "negative",
        "public_gva_share_lag",
        "lp_growth",
    ),
]

BLOCKED = [
    {
        "run_id": "oecd_pdb_investment_share_tfp_interaction_panel",
        "status": "BLOCKED_MISSING_SERIES",
        "missing_series": [INVESTMENT_SHARE_REQUIRED],
        "note": "Latest OECD PDB vintage has capital services and capital-deepening measures, but no investment-share/GFCF-share measure needed by the registered id.",
    },
    {
        "run_id": "oecd_pdb_tax_wedge_productivity_growth_panel",
        "status": "BLOCKED_MISSING_SERIES",
        "missing_series": [TAX_REQUIRED],
        "note": "No OECD tax-wage/tax-wedge parquet vintage is present under data/vintages/oecd.",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pattern: str, base: Path) -> Path | None:
    files = sorted(base.glob(pattern), key=lambda p: (p.stat().st_mtime, p.name))
    return files[-1] if files else None


def load_pdb() -> tuple[pd.DataFrame, Path]:
    p = latest("DSD_PDB@*.parquet", ROOT / "data" / "vintages" / "oecd")
    if p is None:
        p = latest("OECD.SDD.TPS_DSD_PDB_DF_PDB_2.0@*.parquet", ROOT / "data" / "vintages" / "oecd")
    if p is None:
        raise FileNotFoundError("Missing OECD PDB vintage: DSD_PDB@*.parquet")
    cols = [
        "REF_AREA", "MEASURE", "ACTIVITY", "UNIT_MEASURE", "PRICE_BASE",
        "TRANSFORMATION", "ASSET_CODE", "period", "value",
    ]
    df = pd.read_parquet(p, columns=cols)
    df = df.rename(columns={"REF_AREA": "country", "period": "year"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["country"].isin(OECD_CORE) & df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)
    return df, p


def series(df: pd.DataFrame, measure: str, *, activity: str = "_T",
           price: str | None = None, transformation: str | None = None,
           unit: str | None = None, asset: str | None = None,
           name: str) -> pd.DataFrame:
    m = (df["MEASURE"] == measure) & (df["ACTIVITY"] == activity)
    if price is not None:
        m &= df["PRICE_BASE"].eq(price)
    if transformation is not None:
        m &= df["TRANSFORMATION"].eq(transformation)
    if unit is not None:
        m &= df["UNIT_MEASURE"].eq(unit)
    if asset is not None:
        m &= df["ASSET_CODE"].eq(asset)
    out = df.loc[m, ["country", "year", "value"]].dropna().copy()
    out = out.groupby(["country", "year"], as_index=False)["value"].mean()
    return out.rename(columns={"value": name})


def load_panel(pdb: pd.DataFrame) -> pd.DataFrame:
    panel = series(pdb, "GVAHRS", price="LR", transformation="N", unit="USD_PPP_H", name="lp")
    for s in [
        series(pdb, "GDPHRS", price="LR", transformation="N", unit="USD_PPP_H", name="gdp_hour"),
        series(pdb, "GVA", activity="_T", price="LR", transformation="N", unit="USD_PPP", name="gva_real"),
        series(pdb, "HRSAV", transformation="N", unit="H_PS", name="hours_avg"),
        series(pdb, "MFPH", price="LR", transformation="GY", asset="_T", name="tfp_growth"),
        series(pdb, "MFP_PCCONLP", price="LR", transformation="GY", asset="_T", name="tfp_contribution"),
        series(pdb, "KSERHRS", price="LR", transformation="GY", asset="_T", name="capital_deepening"),
    ]:
        panel = panel.merge(s, on=["country", "year"], how="outer")

    total_gva_v = series(pdb, "GVA", activity="_T", price="V", transformation="N", unit="XDC", name="gva_total_current")
    public_gva_v = series(pdb, "GVA", activity="OTQ", price="V", transformation="N", unit="XDC", name="gva_public_current")
    panel = panel.merge(total_gva_v, on=["country", "year"], how="left").merge(public_gva_v, on=["country", "year"], how="left")

    panel = panel.sort_values(["country", "year"])
    for col in ["lp", "gdp_hour", "gva_real", "hours_avg"]:
        panel[f"log_{col}"] = np.log(panel[col].where(panel[col] > 0))
        panel[f"{col}_growth"] = panel.groupby("country")[f"log_{col}"].diff() * 100.0

    panel["lp_growth"] = panel["lp_growth"]
    panel["gva_growth"] = panel["gva_real_growth"]
    panel["hours_growth"] = panel["hours_avg_growth"]
    panel["frontier_lp"] = panel.groupby("year")["log_lp"].transform("max")
    panel["frontier_gap"] = panel["frontier_lp"] - panel["log_lp"]
    panel["frontier_gap_lag"] = panel.groupby("country")["frontier_gap"].shift(1)
    panel["tfp_growth_lag"] = panel.groupby("country")["tfp_growth"].shift(1)
    panel["public_gva_share"] = panel["gva_public_current"] / panel["gva_total_current"]
    panel["public_gva_share_lag"] = panel.groupby("country")["public_gva_share"].shift(1)
    panel["post_2008"] = (panel["year"] >= 2009).astype(int)
    panel["small_open"] = panel["country"].isin(SMALL_OPEN).astype(int)
    return panel


def load_pmr_cross_section(panel: pd.DataFrame) -> tuple[pd.DataFrame, Path | None]:
    p = latest("OECD.ECO.GCRD_DSD_PMR_DF_PMR_1.2@*.parquet", ROOT / "data" / "vintages" / "oecd_pmr")
    if p is None:
        p = latest("PMR@*.parquet", ROOT / "data" / "vintages" / "oecd_pmr")
    if p is None:
        return pd.DataFrame(), None
    pmr = pd.read_parquet(p)
    pmr = pmr.rename(columns={"REF_AREA": "country", "period": "year"})
    pmr["year"] = pd.to_numeric(pmr["year"], errors="coerce").astype("Int64")
    pmr["value"] = pd.to_numeric(pmr["value"], errors="coerce")
    pmr = pmr[(pmr["country"].isin(OECD_CORE)) & (pmr["MEASURE"].eq("PMR")) & (pmr["year"].isin([2018, 2023]))]
    wide = pmr.pivot_table(index="country", columns="year", values="value", aggfunc="mean")
    if 2018 not in wide.columns or 2023 not in wide.columns:
        return pd.DataFrame(), p
    wide["pmr_decline_2018_2023"] = wide[2018] - wide[2023]
    lp = panel[(panel["year"].between(2018, 2024))].groupby("country")["lp_growth"].mean().rename("lp_growth_2018_2024")
    out = wide[["pmr_decline_2018_2023"]].join(lp).dropna().reset_index()
    return out, p


def fit(spec: ReadySpec, panel: pd.DataFrame, pmr_panel: pd.DataFrame) -> dict:
    if spec.data_filter == "cross_section_pmr":
        d = pmr_panel.copy()
        formula = spec.formula
        groups = d["country"] if "country" in d else None
    else:
        d = panel.query(spec.data_filter).copy()
        formula = spec.formula
        groups = d["country"]
    needed = [spec.treatment, spec.outcome]
    if spec.expected_sign == "tfp_dominates":
        needed.append("tfp_contribution")
    d = d.dropna(subset=list(dict.fromkeys(needed)))
    n_countries = int(d["country"].nunique()) if "country" in d else int(len(d))
    if len(d) < spec.min_obs or n_countries < spec.min_countries:
        return {
            "status": "INCONCLUSIVE_DATA_PENDING",
            "error": f"insufficient usable panel: n={len(d)}, countries={n_countries}",
            "n_obs": int(len(d)),
            "n_countries": n_countries,
        }
    model = smf.ols(formula, data=d)
    if groups is not None and d["country"].nunique() > 1:
        res = model.fit(cov_type="cluster", cov_kwds={"groups": groups.loc[d.index]})
    else:
        res = model.fit()
    params = {}
    for name in [spec.treatment, "tfp_contribution"]:
        if name in res.params.index:
            ci = res.conf_int().loc[name]
            params[name] = {
                "estimate": float(res.params[name]),
                "se": float(res.bse[name]),
                "p": float(res.pvalues[name]),
                "ci_lo": float(ci[0]),
                "ci_hi": float(ci[1]),
            }
    verdict = verdict_for(spec, params)
    return {
        "status": verdict,
        "n_obs": int(res.nobs),
        "n_countries": n_countries,
        "r2": float(res.rsquared),
        "formula": formula,
        "coefficients": params,
        "sample_min_year": int(d["year"].min()) if "year" in d else None,
        "sample_max_year": int(d["year"].max()) if "year" in d else None,
    }


def verdict_for(spec: ReadySpec, params: dict) -> str:
    t = params.get(spec.treatment)
    if not t:
        return "INCONCLUSIVE"
    est, p = t["estimate"], t["p"]
    if spec.expected_sign == "positive":
        return "SUPPORTED" if est > 0 and p < 0.10 else "REFUTED_OR_WEAK"
    if spec.expected_sign == "negative":
        return "SUPPORTED" if est < 0 and p < 0.10 else "REFUTED_OR_WEAK"
    if spec.expected_sign == "not_negative_large":
        return "SUPPORTED" if t["ci_lo"] > -0.5 else "INCONCLUSIVE"
    if spec.expected_sign == "tfp_dominates":
        tfp = params.get("tfp_contribution")
        if tfp and abs(tfp["estimate"]) > abs(est) and tfp["p"] < 0.10:
            return "SUPPORTED"
        return "REFUTED_OR_WEAK"
    return "INCONCLUSIVE"


def write_hypothesis(spec: ReadySpec) -> None:
    HYP.mkdir(parents=True, exist_ok=True)
    STEEL.mkdir(parents=True, exist_ok=True)
    is_cross_section = spec.data_filter == "cross_section_pmr"
    period = [2018, 2024] if is_cross_section else [1971, 2025]
    countries = sorted(SMALL_OPEN if "small_open" in spec.run_id else OECD_CORE)
    treatment_source = PMR_REQUIRED if ("pmr" in spec.run_id or "market_reform" in spec.run_id) else PDB_REQUIRED
    payload = {
        "hypothesis_id": spec.run_id,
        "version": 1,
        "status": "candidate",
        "topic": "growth",
        "claim": spec.claim,
        "methodology_note": "Promoted for Batch 03 on 2026-05-12 using the local OECD Productivity Database vintage, with PMR added only for the product-market-reform cross-section.",
        "evidence_type": "associational",
        "sample": {
            "countries": countries,
            "period": period,
            "temporal_structure": "cross_section_with_justification" if is_cross_section else "panel",
            **({"cross_section_justification": "PMR-reform exposure is observed as a 2018-2023 change and tested against following-window productivity growth."} if is_cross_section else {}),
            "exclusion_rules": ["drop non-OECD observations and country-years missing the primary outcome or treatment"],
        },
        "variables": {
            "outcome": [{"name": spec.outcome, "source": PDB_REQUIRED, "transformation": "growth_or_level_as_named"}],
            "treatment": [{"name": spec.treatment, "source": treatment_source, "transformation": "lagged_level_or_change_as_named"}],
            "controls": [],
        },
        "estimator": {
            "template": "descriptive" if is_cross_section else "panel_fe",
            "fixed_effects": [] if is_cross_section else ["country", "year"],
            "clustering": "country",
            "notes": "Local first-pass throughput screen; upgrade robustness before scoreboard conversion.",
        },
        "falsification": {
            "rule": f"Estimate `{spec.formula}` on the landed OECD PDB vintage; expected sign: {spec.expected_sign}. SUPPORTED requires the pre-registered sign at p<0.10 or the named dominance criterion; otherwise the result is partial or weak.",
            "test": f"oecd_pdb_batch03_{spec.run_id}",
            "threshold": "p<0.10 with pre-registered sign, except dominance tests compare the named contribution magnitudes",
        },
        "prior_confidence": 0.55,
        "disclosure": "These OECD productivity screens are proxy-first associational tests intended to identify scoreboard candidates, not final causal estimates.",
        "steelman": f"hypotheses/steelman/{spec.run_id}.md",
        "scope": {
            "period": period,
            "countries": ["OECD"],
            "outcome_dim": ["productivity", "gdp_growth"],
            "policy_family": ["regulation"] if is_cross_section else ["institutional_reform"],
            "treatment_tags": [spec.treatment, "oecd_pdb_batch03"],
        },
        "covers_claims": [],
    }
    (HYP / f"{spec.run_id}.yaml").write_text(
        "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
        + yaml.safe_dump(payload, sort_keys=False, width=100),
        encoding="utf-8",
    )
    STEEL.joinpath(f"{spec.run_id}.md").write_text(
        f"# {spec.title}\n\n"
        f"**Claim.** {spec.claim}\n\n"
        f"**Data.** Latest landed OECD Productivity Database vintage, with PMR added only for the market-reform specification.\n\n"
        f"**Test.** `{spec.formula}`.\n",
        encoding="utf-8",
    )


def write_run(spec: ReadySpec, result: dict, pdb_path: Path, pmr_path: Path | None) -> None:
    out = RUNS / spec.run_id
    out.mkdir(parents=True, exist_ok=True)
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "hypothesis_id": spec.run_id,
        "run_utc": run_utc,
        "verdict_label": result.get("status"),
        "title": spec.title,
        "created_by": "scripts/promote_oecd_pdb_batch03_2026_05_12.py",
        "vintages": [
            {"publisher": "oecd", "series": PDB_REQUIRED, "file": str(pdb_path.relative_to(ROOT)), "sha256": sha256(pdb_path)},
        ],
        "formula": result.get("formula", spec.formula),
    }
    if pmr_path is not None and ("pmr" in spec.run_id or "market_reform" in spec.run_id):
        manifest["vintages"].append({"publisher": "oecd_pmr", "series": PMR_REQUIRED, "file": str(pmr_path.relative_to(ROOT)), "sha256": sha256(pmr_path)})
    (out / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (out / "diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    coef_rows = []
    for name, vals in result.get("coefficients", {}).items():
        row = {"term": name}
        row.update(vals)
        coef_rows.append(row)
    pd.DataFrame(coef_rows).to_parquet(out / "coefficients.parquet", index=False)
    chart = {
        "run_id": spec.run_id,
        "status": result.get("status"),
        "coefficients": result.get("coefficients", {}),
        "n_obs": result.get("n_obs"),
        "n_countries": result.get("n_countries"),
    }
    (out / "chart_data.json").write_text(json.dumps(chart, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\nimport sys\n"
        "ROOT = Path(__file__).resolve().parents[3]\n"
        "sys.path.insert(0, str(ROOT / 'scripts'))\n"
        "from promote_oecd_pdb_batch03_2026_05_12 import run_one\n\n"
        f"if __name__ == '__main__':\n    print(run_one('{spec.run_id}'))\n",
        encoding="utf-8",
    )
    coef_text = "\n".join(
        f"- `{k}`: beta={v['estimate']:.4g}, p={v['p']:.3g}, 90/95 CI approx [{v['ci_lo']:.4g}, {v['ci_hi']:.4g}]"
        for k, v in result.get("coefficients", {}).items()
    ) or "- No coefficient estimated."
    card = f"""# {spec.title}

**Verdict:** {result.get('status')}

**Claim:** {spec.claim}

**Test:** `{result.get('formula', spec.formula)}`

**Sample:** n={result.get('n_obs')}, countries={result.get('n_countries')}, years={result.get('sample_min_year')}–{result.get('sample_max_year')}.

**Key coefficients**
{coef_text}

**Data:** `{PDB_REQUIRED}` from `{pdb_path.relative_to(ROOT)}`.
"""
    (out / "result_card.md").write_text(card, encoding="utf-8")


def run_one(run_id: str) -> dict:
    pdb, pdb_path = load_pdb()
    panel = load_panel(pdb)
    pmr_panel, pmr_path = load_pmr_cross_section(panel)
    spec = {s.run_id: s for s in READY_SPECS}[run_id]
    write_hypothesis(spec)
    result = fit(spec, panel, pmr_panel)
    write_run(spec, result, pdb_path, pmr_path)
    return result


def write_audit(results: list[dict], pdb_path: Path, pmr_path: Path | None) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    pdb_vintages = sorted(
        str(p.relative_to(ROOT))
        for p in (ROOT / "data" / "vintages" / "oecd").glob("*DSD_PDB*.parquet")
    )
    ready_ids = {s.run_id for s in READY_SPECS}
    existing_pdb_runners = []
    for run_dir in sorted(RUNS.iterdir()):
        if not run_dir.is_dir() or run_dir.name in ready_ids:
            continue
        haystack = []
        for name in ("manifest.yaml", "result_card.md", "replication.py", "diagnostics.json"):
            p = run_dir / name
            if p.exists():
                try:
                    haystack.append(p.read_text(encoding="utf-8", errors="ignore")[:50000])
                except OSError:
                    pass
        if "DSD_PDB" in "\n".join(haystack) or "load_pdb" in "\n".join(haystack):
            existing_pdb_runners.append(str(run_dir.relative_to(ROOT)))
    payload = {
        "batch": "Batch 03 OECD Productivity / Frontier Convergence",
        "date": "2026-05-12",
        "available_pdb_vintages": pdb_vintages,
        "existing_pdb_runners_detected": existing_pdb_runners,
        "pdb_vintage": str(pdb_path.relative_to(ROOT)),
        "pmr_vintage": str(pmr_path.relative_to(ROOT)) if pmr_path else None,
        "promoted_run_count": len(results),
        "blocked_count": len(BLOCKED),
        "results": results,
        "blocked": BLOCKED,
    }
    stem = "monthly_hypothesis_throughput_batch_03_oecd_pdb_A2_2026-05-12"
    (AUDITS / f"{stem}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Batch 03 OECD PDB readiness and run audit",
        "",
        f"- PDB vintage: `{pdb_path.relative_to(ROOT)}`",
        f"- PMR vintage: `{pmr_path.relative_to(ROOT) if pmr_path else 'MISSING'}`",
        f"- Available PDB vintages: {len(pdb_vintages)}",
        f"- Existing PDB runners detected before Batch 03 exclusion: {len(existing_pdb_runners)}",
        f"- Promoted and run: {len(results)} of 10",
        f"- Blocked as registered: {len(BLOCKED)} of 10",
        "",
        "## Inventory",
        "",
        "PDB vintages:",
        *[f"- `{p}`" for p in pdb_vintages],
        "",
        "Existing PDB runners detected:",
        *[f"- `{p}`" for p in existing_pdb_runners],
        "",
        "## Completed",
    ]
    for r in results:
        lines.append(f"- `{r['run_id']}`: {r['status']} (n={r.get('n_obs')}, countries={r.get('n_countries')})")
    lines += ["", "## Blockers"]
    for b in BLOCKED:
        missing = ", ".join(f"`{s}`" for s in b["missing_series"])
        lines.append(f"- `{b['run_id']}`: {b['status']}; missing {missing}. {b['note']}")
    (AUDITS / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    pdb, pdb_path = load_pdb()
    panel = load_panel(pdb)
    pmr_panel, pmr_path = load_pmr_cross_section(panel)
    results = []
    for spec in READY_SPECS:
        write_hypothesis(spec)
        result = fit(spec, panel, pmr_panel)
        write_run(spec, result, pdb_path, pmr_path)
        result = {"run_id": spec.run_id, **result}
        results.append(result)
        print(f"{spec.run_id}: {result['status']} n={result.get('n_obs')} countries={result.get('n_countries')}")
    write_audit(results, pdb_path, pmr_path)
    print("blocked:", ", ".join(b["run_id"] for b in BLOCKED))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
