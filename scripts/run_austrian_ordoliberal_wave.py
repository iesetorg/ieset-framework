#!/usr/bin/env python3
"""Direct hypothesis test runner for Austrian/Ordoliberal 500 backlog.

Bypasses the existing series-resolution infrastructure and loads data
directly from vintages using known column names. Runs panel FE regressions
via linearmodels and produces SUPPORTED/REFUTED/PARTIAL/INCONCLUSIVE verdicts.

Usage:
    python3 scripts/run_austrian_ordolibular_wave.py --all
    python3 scripts/run_austrian_ordolibular_wave.py <hypothesis_id>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages"
RUNS = ROOT / "engine" / "runs"
HYPOTHESES = ROOT / "hypotheses"

# ── Publisher-to-file mapping ───────────────────────────────────────────────
# Maps publisher_id -> (glob_pattern, column_mapping)
# column_mapping: {role: (country_col, year_col, value_col_or_lambda)}

PUBLISHER_MAP = {
    "world_bank_wdi": {
        "pattern": "{series}@*.parquet",
        "country_col": "country_iso3",
        "year_col": "year",
        "value_col": "value",
    },
    "pwt": {
        "pattern": "{series}@*.parquet",
        "country_col": "countrycode",
        "year_col": "year",
        "value_col": "value",
    },
    "wgi": {
        "pattern": "{series}@*.parquet",
        "country_col": "country_iso3",
        "year_col": "year",
        "value_col": "value",
    },
    "fraser_efw": {
        "pattern": "efw_panel@*.parquet",
        "country_col": "country_iso3",
        "year_col": "year",
        "value_col": None,  # multi-column; resolved per-series
        "columns": {
            "summary_index": "efw_summary",
            "aggregate_score": "efw_summary",
            "size_of_government": "area_1_size_of_government",
            "area_1_size_of_government": "area_1_size_of_government",
            "legal_system_property_rights": "area_2_legal_system_property_rights",
            "area_2_legal_system_property_rights": "area_2_legal_system_property_rights",
            "sound_money": "area_3_sound_money",
            "area_3_sound_money": "area_3_sound_money",
            "freedom_to_trade_internationally": "area_4_freedom_to_trade_internationally",
            "area_4_freedom_to_trade_internationally": "area_4_freedom_to_trade_internationally",
            "regulation": "area_5_regulation",
            "area_5_regulation": "area_5_regulation",
        },
    },
    "heritage_ief": {
        "pattern": "ief_panel@*.parquet",
        "country_col": "country_iso3",
        "year_col": "year",
        "value_col": None,
        "columns": {
            "overall": "overall_score",
            "overall_score": "overall_score",
            "property_rights": "property_rights",
            "judicial_effectiveness": "judicial_effectiveness",
            "government_integrity": "government_integrity",
            "tax_burden": "tax_burden",
            "government_spending": "government_spending",
            "fiscal_health": "fiscal_health",
            "business_freedom": "business_freedom",
            "labor_freedom": "labor_freedom",
            "monetary_freedom": "monetary_freedom",
            "trade_freedom": "trade_freedom",
            "investment_freedom": "investment_freedom",
            "financial_freedom": "financial_freedom",
        },
    },
    "oecd_pmr": {
        "pattern": "PMR@*.parquet",
        "country_col": "REF_AREA",
        "year_col": "TIME_PERIOD",
        "value_col": "OBS_VALUE",
        "iso3_map": "oecd",  # use OECD country name mapping
    },
    "chinn_ito": {
        "pattern": "kaopen*@*.parquet",
        "country_col": "ccode",
        "year_col": "year",
        "value_col": "kaopen",
    },
    "oecd_stan": {
        "pattern": "STAN@*.parquet",
        "country_col": "REF_AREA",
        "year_col": "TIME_PERIOD",
        "value_col": "OBS_VALUE",
        "iso3_map": "oecd",
    },
    "bis": {
        "pattern": "{series}@*.parquet",
        "country_col": "country_iso3",
        "year_col": "year",
        "value_col": "value",
    },
    "laeven_valencia": {
        "pattern": "crisis_years@*.parquet",
        "country_col": "country_iso3",
        "year_col": "year",
        "value_col": "crisis",
    },
}


# ── ISO3 helpers ────────────────────────────────────────────────────────────

_OECD_NAME_TO_ISO3 = {
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN",
    "Chile": "CHL", "Colombia": "COL", "Costa Rica": "CRI", "Czech Republic": "CZE",
    "Denmark": "DNK", "Estonia": "EST", "Finland": "FIN", "France": "FRA",
    "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN", "Iceland": "ISL",
    "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA", "Japan": "JPN",
    "Korea": "KOR", "Latvia": "LVA", "Lithuania": "LTU", "Luxembourg": "LUX",
    "Mexico": "MEX", "Netherlands": "NLD", "New Zealand": "NZL", "Norway": "NOR",
    "Poland": "POL", "Portugal": "PRT", "Slovak Republic": "SVK", "Slovenia": "SVN",
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "CHE", "Türkiye": "TUR",
    "United Kingdom": "GBR", "United States": "USA",
}


def _to_iso3(series: pd.Series, mapping_type: str | None = None) -> pd.Series:
    s = series.astype(str).str.strip().str.upper()
    if mapping_type == "oecd":
        # First try to map from country names
        mapped = s.map(lambda x: _OECD_NAME_TO_ISO3.get(x.title(), x))
        return mapped
    # Assume already ISO3 or ISO2
    iso2_to_iso3 = {
        "AR": "ARG", "AT": "AUT", "AU": "AUS", "BE": "BEL", "BG": "BGR",
        "BR": "BRA", "CA": "CAN", "CH": "CHE", "CL": "CHL", "CN": "CHN",
        "CO": "COL", "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK",
        "EE": "EST", "EG": "EGY", "EL": "GRC", "ES": "ESP", "FI": "FIN",
        "FR": "FRA", "GB": "GBR", "GR": "GRC", "HK": "HKG", "HR": "HRV",
        "HU": "HUN", "ID": "IDN", "IE": "IRL", "IL": "ISR", "IN": "IND",
        "IS": "ISL", "IT": "ITA", "JP": "JPN", "KR": "KOR", "LT": "LTU",
        "LU": "LUX", "LV": "LVA", "MX": "MEX", "MY": "MYS", "NL": "NLD",
        "NO": "NOR", "NZ": "NZL", "PE": "PER", "PH": "PHL", "PK": "PAK",
        "PL": "POL", "PT": "PRT", "RO": "ROU", "RU": "RUS", "SE": "SWE",
        "SG": "SGP", "SI": "SVN", "SK": "SVK", "TH": "THA", "TR": "TUR",
        "TN": "TUN", "TW": "TWN", "UA": "UKR", "UK": "GBR", "US": "USA",
        "VN": "VNM", "ZA": "ZAF",
    }
    return s.map(lambda x: iso2_to_iso3.get(x, x))


# ── Data loading ────────────────────────────────────────────────────────────

def load_series(publisher: str, series: str) -> pd.DataFrame | None:
    """Load a series from vintages and normalize to (country_iso3, year, value)."""
    pub_dir = VINTAGES / publisher
    if not pub_dir.exists():
        return None

    cfg = PUBLISHER_MAP.get(publisher)
    if cfg is None:
        # Fallback: try to find any parquet matching series name
        candidates = list(pub_dir.glob(f"{series}@*.parquet"))
        if not candidates:
            candidates = list(pub_dir.glob("*.parquet"))
        if not candidates:
            return None
        df = pd.read_parquet(max(candidates, key=lambda p: p.stat().st_mtime))
        # Guess columns
        country_col = next((c for c in df.columns if "country" in c.lower() or c in ("iso3", "ccode", "REF_AREA")), None)
        year_col = next((c for c in df.columns if c.lower() in ("year", "time_period", "date", "period")), None)
        value_col = next((c for c in df.columns if c.lower() in ("value", "obs_value", "kaopen")), None)
        if not all([country_col, year_col, value_col]):
            return None
        df = df[[country_col, year_col, value_col]].rename(columns={
            country_col: "country_iso3", year_col: "year", value_col: "value"
        })
        df["country_iso3"] = _to_iso3(df["country_iso3"])
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        return df.dropna(subset=["country_iso3", "year", "value"])

    pattern = cfg["pattern"].format(series=series)
    candidates = list(pub_dir.glob(pattern))
    if not candidates:
        return None
    df = pd.read_parquet(max(candidates, key=lambda p: p.stat().st_mtime))

    country_col = cfg["country_col"]
    year_col = cfg["year_col"]
    value_col = cfg.get("value_col")

    # Multi-column publishers (fraser, heritage)
    if value_col is None and "columns" in cfg:
        col_map = cfg["columns"]
        actual_col = col_map.get(series.lower()) or col_map.get(series)
        if actual_col is None or actual_col not in df.columns:
            # Try case-insensitive match
            actual_col = next((c for c in df.columns if series.lower() in c.lower()), None)
        if actual_col is None:
            return None
        value_col = actual_col

    if country_col not in df.columns or year_col not in df.columns or value_col not in df.columns:
        return None

    df = df[[country_col, year_col, value_col]].rename(columns={
        country_col: "country_iso3", year_col: "year", value_col: "value"
    })
    df["country_iso3"] = _to_iso3(df["country_iso3"], cfg.get("iso3_map"))
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["country_iso3", "year", "value"])


# ── Panel building ──────────────────────────────────────────────────────────



def parse_constructed_source(source: str) -> dict | None:
    """Parse a constructed: source string into an operation spec."""
    if not source.startswith("constructed:"):
        return None
    body = source.replace("constructed:", "").strip()

    # Pattern 1: simple multiplication "A × B"
    m = re.search(r'(\w+):(\w+)\s*[×xX]\s*(\w+):(\w+)', body)
    if m:
        return {"op": "multiply", "left": (m.group(1), m.group(2)), "right": (m.group(3), m.group(4))}

    # Pattern 2: weighted sum "0.5×A:B + 0.5×C:D"
    terms = re.findall(r'([0-9.]+)\s*×\s*(\w+):(\w+)', body)
    if terms:
        return {"op": "weighted_sum", "terms": [(float(w), (p, s)) for w, p, s in terms]}

    # Pattern 3: simple average "0.5 × A:B + 0.5 × C:D" (with spaces)
    terms = re.findall(r'([0-9.]+)\s*×\s*(\w+):(\w+)', body)
    if terms:
        return {"op": "weighted_sum", "terms": [(float(w), (p, s)) for w, p, s in terms]}

    # Pattern 4: simple addition "A:B + C:D"
    terms = re.findall(r'(\w+):(\w+)', body)
    if len(terms) >= 2:
        return {"op": "weighted_sum", "terms": [(1.0/len(terms), (p, s)) for p, s in terms]}

    return None


def load_constructed_variable(panel: pd.DataFrame, name: str, source: str) -> pd.DataFrame | None:
    """Add a constructed variable to the panel."""
    spec = parse_constructed_source(source)
    if spec is None:
        return None

    if spec["op"] == "multiply":
        left_pub, left_ser = spec["left"]
        right_pub, right_ser = spec["right"]
        left = load_series(left_pub, left_ser)
        right = load_series(right_pub, right_ser)
        if left is None or right is None:
            return None
        left = left.rename(columns={"value": f"__{name}_left"})
        right = right.rename(columns={"value": f"__{name}_right"})
        merged = left.merge(right, on=["country_iso3", "year"], how="inner")
        merged[name] = merged[f"__{name}_left"] * merged[f"__{name}_right"]
        return merged[["country_iso3", "year", name]]

    if spec["op"] == "weighted_sum":
        frames = []
        for weight, (pub, ser) in spec["terms"]:
            df = load_series(pub, ser)
            if df is None:
                return None
            df = df.rename(columns={"value": f"__{name}_term"})
            df[f"__{name}_weight"] = weight
            frames.append(df)
        if not frames:
            return None
        merged = frames[0]
        for f in frames[1:]:
            merged = merged.merge(f, on=["country_iso3", "year"], how="inner")
        # Simple average of available terms
        term_cols = [c for c in merged.columns if c.startswith(f"__{name}_term")]
        merged[name] = merged[term_cols].mean(axis=1)
        return merged[["country_iso3", "year", name]]

    return None

def build_panel(spec: dict) -> tuple[pd.DataFrame | None, dict]:
    """Build a panel from spec variables. Returns (panel, load_status)."""
    vars_block = spec.get("variables") or {}
    roles = [("outcome", v) for v in vars_block.get("outcome", [])] + \
            [("treatment", v) for v in vars_block.get("treatment", [])] + \
            [("control", v) for v in vars_block.get("controls", [])]

    frames = []
    status = {}
    direct_frames = []
    constructed_vars = []

    for role, var in roles:
        src = var.get("source", "")
        if src.startswith("constructed:"):
            constructed_vars.append((role, var))
            continue
        if ":" not in src:
            continue
        pub, series = src.split(":", 1)
        df = load_series(pub, series)
        name = var["name"]
        if df is None or len(df) == 0:
            status[name] = {"loaded": False, "source": src}
            continue
        df = df.rename(columns={"value": name})
        direct_frames.append((role, df))
        status[name] = {"loaded": True, "n": len(df), "source": src}

    if not direct_frames:
        return None, status

    # Merge all direct frames
    merged = None
    for role, df in direct_frames:
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on=["country_iso3", "year"], how="outer")

    # Now load constructed variables using the merged panel
    for role, var in constructed_vars:
        src = var.get("source", "")
        name = var["name"]
        df = load_constructed_variable(merged, name, src)
        if df is not None:
            merged = merged.merge(df, on=["country_iso3", "year"], how="left")
            status[name] = {"loaded": True, "n": len(df), "source": src}
        else:
            status[name] = {"loaded": False, "source": src}

    # Filter sample
    sample = spec.get("sample", {})
    countries = sample.get("countries", [])
    period = sample.get("period", [])

    if countries:
        # Handle country groups
        country_set = set()
        for c in countries:
            if isinstance(c, str) and len(c) == 3:
                country_set.add(c)
            # Could expand groups here
        if country_set:
            merged = merged[merged["country_iso3"].isin(country_set)]

    if period and len(period) == 2:
        merged = merged[(merged["year"] >= period[0]) & (merged["year"] <= period[1])]

    # Check outcome and treatment exist
    outcome_names = [v["name"] for v in vars_block.get("outcome", [])]
    treatment_names = [v["name"] for v in vars_block.get("treatment", [])]

    has_outcome = any(o in merged.columns for o in outcome_names)
    has_treatment = any(t in merged.columns for t in treatment_names)

    if not has_outcome or not has_treatment:
        return None, status

    available_cols = [c for c in (outcome_names + treatment_names) if c in merged.columns]
    if not available_cols:
        return None, status
    return merged.dropna(subset=available_cols, how="any"), status


# ── Estimation ──────────────────────────────────────────────────────────────

def fit_panel_fe(panel: pd.DataFrame, spec: dict) -> dict:
    """Fit panel FE and return results dict."""
    vars_block = spec.get("variables") or {}
    outcome = vars_block["outcome"][0]["name"]
    treatment = vars_block["treatment"][0]["name"]
    controls = [c["name"] for c in vars_block.get("controls", []) if c.get("name") in panel.columns]

    needed = ["country_iso3", "year", outcome, treatment] + controls
    available = [c for c in needed if c in panel.columns]
    if len(available) < len([outcome, treatment]) + 2:
        missing = [c for c in needed if c not in panel.columns]
        return {"error": f"missing columns: {missing}"}

    sub = panel[available].dropna()
    if len(sub) < 30:
        return {"error": f"insufficient obs ({len(sub)})"}

    sub = sub.set_index(["country_iso3", "year"])
    rhs = [treatment] + controls

    try:
        mod = PanelOLS(sub[outcome], sub[rhs], entity_effects=True, time_effects=True, drop_absorbed=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True)
    except Exception as e:
        return {"error": str(e)}

    coef = float(res.params[treatment])
    pval = float(res.pvalues[treatment])
    se = float(res.std_errors[treatment])
    r2 = float(res.rsquared_within) if hasattr(res, "rsquared_within") else float(res.rsquared)

    return {
        "coefficient": coef,
        "std_error": se,
        "p_value": pval,
        "r_squared": r2,
        "n_obs": len(sub),
        "treatment": treatment,
        "outcome": outcome,
    }


# ── Verdict ─────────────────────────────────────────────────────────────────

def verdict(result: dict, spec: dict) -> str:
    if "error" in result:
        return "INCONCLUSIVE_DATA_PENDING"

    claim_dir = infer_claim_direction(spec)
    coef = result["coefficient"]
    pval = result["p_value"]

    if claim_dir == "+":
        if coef > 0 and pval < 0.10:
            return "SUPPORTED"
        elif coef < 0 and pval < 0.10:
            return "REFUTED"
        else:
            return "PARTIAL"
    elif claim_dir == "-":
        if coef < 0 and pval < 0.10:
            return "SUPPORTED"
        elif coef > 0 and pval < 0.10:
            return "REFUTED"
        else:
            return "PARTIAL"
    return "PARTIAL"


def infer_claim_direction(spec: dict) -> str:
    claim = spec.get("claim", "")
    falsification = spec.get("falsification", {}).get("rule", "")
    text = (claim + " " + falsification).lower()
    if "positively" in text or "positively associated" in text or "higher" in text:
        return "+"
    if "negatively" in text or "negatively associated" in text or "lower" in text:
        return "-"
    return "+"


# ── Main runner ─────────────────────────────────────────────────────────────

def run_hypothesis(hid: str) -> dict:
    # Find spec
    spec_path = None
    for p in HYPOTHESES.rglob(f"{hid}.yaml"):
        spec_path = p
        break
    if spec_path is None:
        return {"verdict": "INCONCLUSIVE", "error": f"Spec not found: {hid}"}

    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    panel, status = build_panel(spec)

    if panel is None:
        missing = [k for k, v in status.items() if not v.get("loaded")]
        return {
            "verdict": "INCONCLUSIVE_DATA_PENDING",
            "verdict_reason": f"variables not loaded: {missing}",
            "hypothesis_id": hid,
            "template": spec.get("estimator", {}).get("template", "panel_fe"),
            "data_status": status,
        }

    est_template = spec.get("estimator", {}).get("template", "panel_fe")
    if est_template in ("panel_fe", "panel_fe_decomposition"):
        result = fit_panel_fe(panel, spec)
    else:
        return {
            "verdict": "INCONCLUSIVE",
            "verdict_reason": f"estimator {est_template} not supported by this runner",
            "hypothesis_id": hid,
        }

    v = verdict(result, spec)
    return {
        "verdict": v,
        "verdict_label": v,
        "verdict_reason": "",
        "hypothesis_id": hid,
        "template": est_template,
        "estimate": result,
        "data_status": status,
        "claim_direction_inferred": infer_claim_direction(spec),
        "falsification_rule_text": spec.get("falsification", {}).get("rule", ""),
    }


def write_run(hid: str, result: dict):
    run_dir = RUNS / hid
    run_dir.mkdir(parents=True, exist_ok=True)
    diag_path = run_dir / "diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    card_lines = [
        f"# Result card — {hid}",
        f"",
        f"**Verdict:** {result['verdict']}",
        f"",
        f"## Estimate",
    ]
    est = result.get("estimate", {})
    if "error" in est:
        card_lines.append(f"- _Error:_ {est['error']}")
    else:
        card_lines.append(f"- **Coefficient:** {est.get('coefficient', 'N/A'):.4f}")
        card_lines.append(f"- **Std Error:** {est.get('std_error', 'N/A'):.4f}")
        card_lines.append(f"- **P-value:** {est.get('p_value', 'N/A'):.4f}")
        card_lines.append(f"- **R² (within):** {est.get('r_squared', 'N/A'):.4f}")
        card_lines.append(f"- **N obs:** {est.get('n_obs', 'N/A')}")
    card_lines.append("")
    card_lines.append("## Variables loaded")
    for name, st in result.get("data_status", {}).items():
        if st.get("loaded"):
            card_lines.append(f"- `{name}` → loaded (n={st.get('n', '?')})")
        else:
            card_lines.append(f"- `{name}` → **MISSING** ({st.get('source', '?')})")

    (run_dir / "result_card.md").write_text("\n".join(card_lines))


def list_inconclusive_with_new_publishers() -> list[str]:
    new_pubs = {"fraser_efw", "heritage_ief", "oecd_pmr", "chinn_ito", "oecd_stan", "oecd_patents", "gfdd", "laeven_valencia"}
    targets = []
    for diag_path in RUNS.rglob("diagnostics.json"):
        try:
            with open(diag_path) as f:
                d = json.load(f)
            if d.get("verdict_label") == "INCONCLUSIVE_DATA_PENDING":
                hid = d.get("hypothesis_id", diag_path.parent.name)
                for p in HYPOTHESES.rglob(f"{hid}.yaml"):
                    with open(p) as f:
                        spec = yaml.safe_load(f)
                    vars_block = spec.get("variables", {})
                    all_vars = vars_block.get("outcome", []) + vars_block.get("treatment", []) + vars_block.get("controls", [])
                    sources = [v.get("source", "") for v in all_vars]
                    pubs = set(s.split(":")[0] for s in sources if ":" in s)
                    if pubs & new_pubs:
                        targets.append(hid)
                    break
        except Exception:
            pass
    return targets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hid", nargs="?", help="Hypothesis ID to run")
    parser.add_argument("--all", action="store_true", help="Run all inconclusive hypotheses that reference new publishers")
    parser.add_argument("--list", action="store_true", help="List target hypotheses")
    args = parser.parse_args()

    if args.list:
        targets = list_inconclusive_with_new_publishers()
        print(f"Target hypotheses: {len(targets)}")
        for hid in targets:
            print(f"  {hid}")
        return

    if args.all:
        targets = list_inconclusive_with_new_publishers()
        print(f"Running {len(targets)} hypotheses...")
        results = []
        for hid in targets:
            print(f"\n  → {hid}")
            try:
                result = run_hypothesis(hid)
                write_run(hid, result)
                print(f"      {result['verdict']}")
                if "estimate" in result and "coefficient" in result["estimate"]:
                    print(f"      coef={result['estimate']['coefficient']:.4f}, p={result['estimate']['p_value']:.4f}, n={result['estimate']['n_obs']}")
                results.append((hid, result["verdict"]))
            except Exception as e:
                print(f"      ERROR: {e}")
                traceback.print_exc()
        print(f"\n{'='*50}")
        print("Summary:")
        for v in ["SUPPORTED", "REFUTED", "PARTIAL", "INCONCLUSIVE_DATA_PENDING", "INCONCLUSIVE"]:
            c = sum(1 for _, r in results if r == v)
            if c:
                print(f"  {v}: {c}")
        return

    if args.hid:
        result = run_hypothesis(args.hid)
        write_run(args.hid, result)
        print(json.dumps(result, indent=2, default=str))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
