#!/usr/bin/env python3
"""Run-local subtype feasibility diagnostics for resource developmentalism.

This script deliberately avoids shared movement builders and scoreboard files.
It validates the manual subtype sidecar, expands it to annual rows, and runs a
non-scoring broad-proxy feasibility pass.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_panel_fe import build_panel, latest_vintage, load_spec, run_panel_ols

RUN_DIR = Path(__file__).resolve().parent
CODING_PATH = ROOT / "data" / "manual" / "resource_developmentalism_subtype_coding_2026-05-16.csv"
WITS_CATALOG_PATH = (
    ROOT
    / "data"
    / "manual"
    / "wits"
    / "herfindahl_hirschman_product_concentration_index_export_2026-02-09.xlsx"
)
HYPOTHESIS_ID = "resource_developmentalism_rent_seeking_trap"
STAMP = "2026-05-17"
ANNUAL_PANEL_OUT = RUN_DIR / f"resource_developmentalism_subtype_annual_panel_{STAMP}.csv"
DIAGNOSTICS_OUT = RUN_DIR / f"subtype_fallback_diagnostics_{STAMP}.json"

REQUIRED_COLUMNS = {
    "country_iso3",
    "country_name",
    "movement_id",
    "episode_start",
    "episode_end",
    "subtype",
    "episode_role",
    "clean_comparator_eligible",
    "confidence",
    "current_alignment",
    "source_status",
    "coding_reason",
    "review_status",
}

ALLOWED_SUBTYPES = {
    "resource_statist_socialist",
    "resource_developmentalist",
    "market_open_resource_peer",
    "rule_bound_resource_manager",
    "resource_nationalisation_shock",
    "mixed",
    "uncoded",
}

ALLOWED_ROLES = {"treated", "comparator", "shock", "excluded", "uncoded"}
ALLOWED_COMPARATOR = {"yes", "conditional", "no"}
OUTCOMES = [
    "export_diversification_index",
    "total_factor_productivity_growth",
    "manufacturing_va_share",
]
FULL_CONTROLS = ["resource_rents", "initial_gdp_per_capita", "institutional_quality"]
NO_WGI_CONTROLS = ["resource_rents", "initial_gdp_per_capita"]


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if pd.isna(value) if not isinstance(value, (list, dict, tuple, set)) else False:
        return None
    return value


def load_and_validate_coding() -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.read_csv(CODING_PATH, dtype=str).fillna("")
    missing_columns = sorted(REQUIRED_COLUMNS - set(raw.columns))
    if missing_columns:
        raise ValueError(f"manual subtype coding is missing columns: {missing_columns}")

    coding = raw.copy()
    coding["country_iso3"] = coding["country_iso3"].str.strip().str.upper()
    coding["subtype"] = coding["subtype"].str.strip()
    coding["episode_role"] = coding["episode_role"].str.strip()
    coding["clean_comparator_eligible"] = coding["clean_comparator_eligible"].str.strip()
    coding["episode_start"] = pd.to_numeric(coding["episode_start"], errors="raise").astype(int)
    coding["episode_end"] = pd.to_numeric(coding["episode_end"], errors="raise").astype(int)

    invalid = {
        "subtype": sorted(set(coding["subtype"]) - ALLOWED_SUBTYPES),
        "episode_role": sorted(set(coding["episode_role"]) - ALLOWED_ROLES),
        "clean_comparator_eligible": sorted(
            set(coding["clean_comparator_eligible"]) - ALLOWED_COMPARATOR
        ),
    }
    invalid = {k: v for k, v in invalid.items() if v}
    bad_windows = coding[coding["episode_end"] < coding["episode_start"]]
    if invalid:
        raise ValueError(f"manual subtype coding has invalid vocabulary values: {invalid}")
    if not bad_windows.empty:
        raise ValueError(f"manual subtype coding has bad year windows: {len(bad_windows)}")

    expanded = expand_annual(coding)
    overlaps = expanded.duplicated(["country_iso3", "year"], keep=False)
    if overlaps.any():
        overlap_keys = (
            expanded.loc[overlaps, ["country_iso3", "year"]]
            .drop_duplicates()
            .head(20)
            .to_dict("records")
        )
        raise ValueError(f"manual subtype coding has country-year overlaps: {overlap_keys}")

    validation = {
        "coding_path": str(CODING_PATH.relative_to(ROOT)),
        "coding_sha256": sha256(CODING_PATH),
        "required_columns_present": True,
        "row_count": int(len(coding)),
        "country_count": int(coding["country_iso3"].nunique()),
        "year_min": int(coding["episode_start"].min()),
        "year_max": int(coding["episode_end"].max()),
        "annual_row_count": int(len(expanded)),
        "annual_country_year_overlaps": 0,
    }
    return expanded, validation


def expand_annual(coding: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    keep = [
        "country_iso3",
        "country_name",
        "movement_id",
        "subtype",
        "episode_role",
        "clean_comparator_eligible",
        "confidence",
        "source_status",
        "review_status",
    ]
    for rec in coding.to_dict("records"):
        for year in range(int(rec["episode_start"]), int(rec["episode_end"]) + 1):
            row = {key: rec[key] for key in keep}
            row["year"] = year
            row["subtype_treated_any"] = 1.0 if rec["episode_role"] == "treated" else 0.0
            row["subtype_clean_comparator"] = (
                1.0 if rec["clean_comparator_eligible"] == "yes" else 0.0
            )
            row["subtype_conditional_comparator"] = (
                1.0 if rec["clean_comparator_eligible"] == "conditional" else 0.0
            )
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["country_iso3", "year"]).reset_index(drop=True)


def count_rows(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return {
        str(k): int(v)
        for k, v in frame[column].value_counts(dropna=False).sort_index().items()
    }


def country_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return {
        str(k): int(v)
        for k, v in frame.groupby(column)["country_iso3"].nunique().sort_index().items()
    }


def annual_coverage(annual: pd.DataFrame) -> dict[str, Any]:
    window = annual[(annual["year"] >= 1970) & (annual["year"] <= 2020)]
    clean_model = window[
        (window["episode_role"] == "treated")
        | (window["clean_comparator_eligible"] == "yes")
    ]
    conditional_model = window[
        (window["episode_role"] == "treated")
        | (window["clean_comparator_eligible"].isin(["yes", "conditional"]))
    ]
    return {
        "all_annual_rows_1970_2020": int(len(window)),
        "countries_1970_2020": int(window["country_iso3"].nunique()),
        "rows_by_role_1970_2020": count_rows(window, "episode_role"),
        "countries_by_role_1970_2020": country_counts(window, "episode_role"),
        "rows_by_subtype_1970_2020": count_rows(window, "subtype"),
        "countries_by_subtype_1970_2020": country_counts(window, "subtype"),
        "clean_model_rows_1970_2020": int(len(clean_model)),
        "clean_model_countries_1970_2020": int(clean_model["country_iso3"].nunique()),
        "clean_model_treated_rows": int(clean_model["subtype_treated_any"].sum()),
        "clean_model_comparator_rows": int(clean_model["subtype_clean_comparator"].sum()),
        "conditional_model_rows_1970_2020": int(len(conditional_model)),
        "conditional_model_countries_1970_2020": int(
            conditional_model["country_iso3"].nunique()
        ),
    }


def generic_scalar_crosswalk(annual: pd.DataFrame) -> dict[str, Any]:
    path = latest_vintage("movements", "resource_developmentalism")
    if path is None:
        return {"error": "missing movements:resource_developmentalism vintage"}
    generic = pd.read_parquet(path)
    generic = generic[["country_iso3", "year", "value"]].copy()
    generic["country_iso3"] = generic["country_iso3"].astype(str).str.upper()
    generic["year"] = pd.to_numeric(generic["year"], errors="coerce")
    generic["value"] = pd.to_numeric(generic["value"], errors="coerce")
    countries = set(annual["country_iso3"].unique())
    generic = generic[
        generic["country_iso3"].isin(countries)
        & generic["year"].between(1970, 2020)
        & (generic["value"] > 0)
    ].copy()
    merged = generic.merge(
        annual[
            [
                "country_iso3",
                "year",
                "subtype",
                "episode_role",
                "clean_comparator_eligible",
            ]
        ],
        on=["country_iso3", "year"],
        how="left",
    )
    merged["episode_role"] = merged["episode_role"].fillna("not_in_manual_subtype_panel")
    merged["subtype"] = merged["subtype"].fillna("not_in_manual_subtype_panel")
    return {
        "generic_vintage_path": str(path.relative_to(ROOT)),
        "generic_vintage_sha256": sha256(path),
        "generic_positive_rows_manual_countries_1970_2020": int(len(generic)),
        "positive_rows_by_sidecar_role": count_rows(merged, "episode_role"),
        "positive_rows_by_sidecar_subtype": count_rows(merged, "subtype"),
        "generic_positive_rows_promoted_to_treated": int(
            (merged["episode_role"] == "treated").sum()
        ),
        "generic_positive_rows_blocked_from_clean_control_or_treatment": int(
            merged["episode_role"].isin(
                ["excluded", "uncoded", "shock", "not_in_manual_subtype_panel"]
            ).sum()
        ),
    }


def wits_catalog_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "catalog_path": str(WITS_CATALOG_PATH.relative_to(ROOT)),
        "catalog_exists": WITS_CATALOG_PATH.exists(),
        "catalog_sha256": sha256(WITS_CATALOG_PATH),
        "usable_product_panel": False,
        "reason": "catalog missing",
    }
    if not WITS_CATALOG_PATH.exists():
        return status
    catalog = pd.read_excel(WITS_CATALOG_PATH)
    local_payloads = sorted((WITS_CATALOG_PATH.parent).glob("ed_hhpci_*"))
    status.update(
        {
            "row_count": int(len(catalog)),
            "columns": [str(c) for c in catalog.columns],
            "year_min": int(pd.to_numeric(catalog["Year"], errors="coerce").min()),
            "year_max": int(pd.to_numeric(catalog["Year"], errors="coerce").max()),
            "last_update_values": sorted(catalog["Last Update"].astype(str).unique().tolist()),
            "url_count": int(catalog["Path"].astype(str).str.startswith("http").sum()),
            "local_payload_count": len(local_payloads),
            "reason": (
                "workbook is a WITS/Data Catalog URL manifest for annual ZIP payloads; "
                "the underlying country-year HHI CSV payloads are not present locally"
            ),
        }
    )
    return status


def build_core_panel() -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    found = load_spec(HYPOTHESIS_ID)
    if found is None:
        raise ValueError(f"missing hypothesis spec: {HYPOTHESIS_ID}")
    _, spec = found
    panel, status = build_panel(spec)
    countries = [
        str(c).upper()
        for c in ((spec.get("sample") or {}).get("countries") or [])
        if isinstance(c, str)
    ]
    return panel, status, countries


def model_spec(control_names: list[str], fixed_effects: list[str]) -> dict[str, Any]:
    return {
        "sample": {"period": [1970, 2020]},
        "variables": {
            "controls": [{"name": name} for name in control_names],
        },
        "estimator": {"fixed_effects": fixed_effects, "clustering": "country"},
    }


def sample_summary(frame: pd.DataFrame, outcome: str, controls: list[str]) -> dict[str, Any]:
    cols = ["country_iso3", "year", outcome, "subtype_treated_any"] + controls
    existing = [c for c in cols if c in frame.columns]
    listwise = frame[existing].dropna()
    return {
        "rows_before_listwise": int(len(frame)),
        "countries_before_listwise": int(frame["country_iso3"].nunique()),
        "treated_rows_before_listwise": int(frame["subtype_treated_any"].sum()),
        "comparator_rows_before_listwise": int((frame["subtype_treated_any"] == 0).sum()),
        "rows_after_listwise": int(len(listwise)),
        "countries_after_listwise": int(listwise["country_iso3"].nunique()),
        "treated_rows_after_listwise": int(listwise["subtype_treated_any"].sum())
        if "subtype_treated_any" in listwise
        else 0,
        "comparator_rows_after_listwise": int((listwise["subtype_treated_any"] == 0).sum())
        if "subtype_treated_any" in listwise
        else 0,
    }


def run_models(annual: pd.DataFrame) -> dict[str, Any]:
    core, load_status, original_countries = build_core_panel()
    annual_window = annual[(annual["year"] >= 1970) & (annual["year"] <= 2020)].copy()
    eligible = annual_window[
        (annual_window["episode_role"] == "treated")
        | (annual_window["clean_comparator_eligible"] == "yes")
    ].copy()
    eligible = eligible[
        [
            "country_iso3",
            "year",
            "subtype",
            "episode_role",
            "clean_comparator_eligible",
            "subtype_treated_any",
        ]
    ]
    merged = eligible.merge(core, on=["country_iso3", "year"], how="left")

    scopes = {
        "sidecar_clean_full_scope": merged.copy(),
        "sidecar_clean_original_hypothesis_scope": merged[
            merged["country_iso3"].isin(original_countries)
        ].copy(),
    }
    ladders = {
        "full_controls": FULL_CONTROLS,
        "no_wgi_controls": NO_WGI_CONTROLS,
    }
    fixed_effect_sets = {
        "country_year_fe": ["country", "year"],
        "year_fe_descriptive": ["year"],
    }

    results: dict[str, Any] = {
        "variable_load_status": load_status,
        "original_hypothesis_country_count": len(original_countries),
        "scopes": {},
    }
    for scope_name, frame in scopes.items():
        scope_result: dict[str, Any] = {
            "countries": sorted(frame["country_iso3"].dropna().unique().tolist()),
            "row_count": int(len(frame)),
            "treated_rows": int(frame["subtype_treated_any"].sum()),
            "comparator_rows": int((frame["subtype_treated_any"] == 0).sum()),
            "models": {},
        }
        for outcome in OUTCOMES:
            if outcome not in frame.columns:
                continue
            for ladder_name, controls in ladders.items():
                controls_present = [c for c in controls if c in frame.columns]
                for fe_name, fixed_effects in fixed_effect_sets.items():
                    key = f"{outcome}__{ladder_name}__{fe_name}"
                    fit_frame = frame[
                        ["country_iso3", "year", outcome, "subtype_treated_any"]
                        + controls_present
                    ].copy()
                    result = run_panel_ols(
                        fit_frame,
                        model_spec(controls_present, fixed_effects),
                        outcome,
                        "subtype_treated_any",
                    )
                    scope_result["models"][key] = {
                        "outcome": outcome,
                        "controls": controls_present,
                        "fixed_effects": fixed_effects,
                        "scoring_status": "blocked_causal" if fe_name == "country_year_fe" else "descriptive_only",
                        "sample": sample_summary(fit_frame, outcome, controls_present),
                        "result": result,
                    }
        results["scopes"][scope_name] = scope_result
    return results


def main() -> int:
    annual, validation = load_and_validate_coding()
    annual.to_csv(ANNUAL_PANEL_OUT, index=False)

    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID,
        "run_type": "non_scoring_subtype_feasibility",
        "verdict": "hold_repair",
        "annual_panel_path": str(ANNUAL_PANEL_OUT.relative_to(ROOT)),
        "validation": validation,
        "coverage": annual_coverage(annual),
        "generic_scalar_crosswalk": generic_scalar_crosswalk(annual),
        "wits_export_hhi_catalog": wits_catalog_status(),
        "models": run_models(annual),
        "blocked": [
            "country+year FE causal scoring is not estimable on the clean subtype-comparator sample because treatment is between-country within eligible rows",
            "product-level or official country-year export HHI payloads are not present locally; the WITS workbook is only a URL catalog",
            "current result_card remains a broad WDI proxy screen and should not be promoted",
        ],
    }
    DIAGNOSTICS_OUT.write_text(json.dumps(json_ready(diagnostics), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"wrote": str(DIAGNOSTICS_OUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
