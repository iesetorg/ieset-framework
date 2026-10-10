#!/usr/bin/env python3
"""Frozen eight-cell FAOSTAT relative producer-price / crop supply family.

The preparation command reads source keys only. Measurement requires a later,
committed source lock with exact raw hashes; the source cache is supplied at run
and replay time. No source file is silently substituted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import pycountry
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "faostat_relative_price_crop_supply_family_2026_10_10"
RUNNER = "scripts/run_faostat_relative_price_supply_2026.py"
TEST = "tests/test_faostat_relative_price_supply_2026.py"
PREREG = "engine/audits/faostat_relative_price_crop_supply_prereg_2026-10-10.md"
SUMMARY = "engine/audits/faostat_relative_price_crop_supply_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/faostat_relative_price_crop_supply_2026_key_roster.csv"
LOCK = "data/pinned_evidence/faostat_relative_price_crop_supply_2026.manifest.json"
SOURCES = {
    "price_archive": {"path": "data/vintages/faostat/prices@2026-05-02T212150Z.zip", "sha256": "0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b"},
    "price_panel": {"path": "data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet", "sha256": "c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c"},
    "crop_archive": {"path": "data/vintages/faostat/Production_Crops_Livestock_E_All_Data_(Normalized)@2026-05-02T211649Z.zip", "sha256": "c5835418c18f9322e7decbd6800f93a216eaae3cdfa31acb08f0518c0c6d6853"},
    "crop_panel": {"path": "data/vintages/faostat/faostat_prod_All_Data_(Normalized)@2026-05-02T212007Z.parquet", "sha256": "02d93061467ca6e9a6cc738ba72702271d26abbaa21480c51d04d29b1017734a"},
    "crop_flag_legend": {"path": "data/vintages/faostat/faostat_prod_Flags@2026-05-02T212007Z.parquet", "sha256": "c9c44507c716b6fe7bd22d68febe1752c3cb4d08c11d62e2311092a8bacc2a6d"},
}
GROUPS = {
    "cereals": {"code": 1717, "label": "cereals, primary", "tags": ["cereals", "farm_supply"]},
    "roots": {"code": 1720, "label": "roots and tubers", "tags": ["roots_tubers", "farm_supply"]},
    "pulses": {"code": 1726, "label": "pulses", "tags": ["pulses", "farm_supply"]},
    "oilcrops": {"code": 1732, "label": "oilcrops, oil equivalent", "tags": ["oilcrops", "farm_supply"]},
}
MARGINS = {
    "area": {"code": 5312, "label": "harvested area", "unit": "ha", "dimension": "industrial_capability", "mechanism": "land allocation"},
    "yield": {"code": 5412, "label": "yield", "unit": "kg/ha", "dimension": "productivity", "mechanism": "intensification or composition"},
}
CASES = {f"{group}_{margin}": {"group": group, "margin": margin,
          "id": f"faostat_{group}_relative_price_forward_{margin}_2026"}
         for group in GROUPS for margin in MARGINS}
T_START, T_END = 1992, 2023
AGRICULTURE_INDEX_CODE, INDEX_ELEMENT, ANNUAL_MONTH_CODE = 2051, 5539, 7021
ALLOWED_FLAGS = {"A", "E", "X"}
MIN_COUNTRY_YEARS = 5
MAX_ABS_LOG_CHANGE = 0.50
MATERIAL_ABS_PRICE_CHANGE = 0.05
MIN_COMPLETE_ROWS, MIN_COMPLETE_COUNTRIES = 500, 30
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 100, 20
MAX_TOP_COUNTRY_RESIDUAL_SHARE = 0.20
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MEANINGFUL_BETA = 0.05  # 0.5% later growth for a 10% relative-price increase
LIMITATIONS = [
    "The predictor is a relative producer-price change, not a randomized price incentive or policy treatment.",
    "Harvests can change prices and farmers may anticipate shocks; a one-year lead does not identify a causal response.",
    "FAOSTAT's crop-group indices and aggregate yields can change when the crop mix changes; harvested area may count multiple harvests of a parcel.",
    "Official, estimated, and external-organization observations are admitted and reported separately; imputed and break flags are excluded.",
    "Country/year effects and prior outcome growth do not remove weather, trade, input-cost, exchange-rate, or subsidy confounding.",
    "Eight correlated tests use one Bonferroni family; this does not adjust the wider IESET archive search and they are not independent replications.",
    "Raw FAOSTAT archives and derived parquets are hash-pinned in a local source cache, not copied into Git; the derived-parquet transformation lacks a tracked fetch manifest.",
    "No causal, policy, school, position, or featured credit is assigned.",
]
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "featured_eligible": False}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(path: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if not commits:
        raise RuntimeError(f"no first-addition commit: {path}")
    return commits[-1]


def frozen(path: str, revision: str) -> None:
    target = ROOT / path
    if not target.is_file() or target.read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen byte mismatch: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen path: {path}")


def raw(source_root: Path, role: str) -> Path:
    return source_root / SOURCES[role]["path"]


def iso3(m49: object) -> str | None:
    try:
        code = str(m49).strip().replace("'", "").zfill(3)
        country = pycountry.countries.get(numeric=code)
        return country.alpha_3 if country is not None else None
    except (TypeError, AttributeError):
        return None


def case_paths(case: dict) -> tuple[str, str, str]:
    ident = case["id"]
    return (f"hypotheses/growth/{ident}.yaml", f"hypotheses/steelman/{ident}.md", f"engine/runs/{ident}")


def key_roster(source_root: Path) -> list[tuple[str, str, int]]:
    """Use only keys, item/element codes and months; never values, flags, or masks."""
    price = pd.read_parquet(raw(source_root, "price_panel"),
                            columns=["Area Code (M49)", "Item Code", "Element Code", "Months Code", "Year"])
    price = price.loc[(price["Element Code"] == INDEX_ELEMENT) &
                      (price["Months Code"] == ANNUAL_MONTH_CODE) &
                      price["Item Code"].isin([AGRICULTURE_INDEX_CODE] + [v["code"] for v in GROUPS.values()])]
    price = price.assign(iso=price["Area Code (M49)"].map(iso3))
    price = price.loc[price["iso"].notna()]
    price_keys = {(int(r["Item Code"]), str(r["iso"]), int(r["Year"])) for _, r in price.iterrows()}
    crop = pd.read_parquet(raw(source_root, "crop_panel"),
                           columns=["Area Code (M49)", "Item Code", "Element Code", "Year"])
    crop = crop.loc[crop["Item Code"].isin([v["code"] for v in GROUPS.values()]) &
                    crop["Element Code"].isin([v["code"] for v in MARGINS.values()])]
    crop = crop.assign(iso=crop["Area Code (M49)"].map(iso3))
    crop = crop.loc[crop["iso"].notna()]
    crop_keys = {(int(r["Item Code"]), int(r["Element Code"]), str(r["iso"]), int(r["Year"]))
                 for _, r in crop.iterrows()}
    records = []
    countries = sorted({c for _, c, _ in price_keys})
    for key, case in CASES.items():
        item, element = GROUPS[case["group"]]["code"], MARGINS[case["margin"]]["code"]
        for country in countries:
            for year in range(T_START, T_END + 1):
                if (all((p, country, y) in price_keys for p in (item, AGRICULTURE_INDEX_CODE)
                        for y in (year - 1, year)) and
                    all((item, element, country, y) in crop_keys for y in (year - 1, year, year + 1))):
                    records.append((key, country, year))
    return records


def roster_rows() -> list[tuple[str, str, int]]:
    with (ROOT / ROSTER).open(newline="") as handle:
        rows = [(r["case"], r["country_iso3"], int(r["treatment_year"])) for r in csv.DictReader(handle)]
    if rows != sorted(rows, key=lambda z: (list(CASES).index(z[0]), z[1], z[2])):
        raise RuntimeError("roster order changed")
    if len(set(rows)) != len(rows) or any(k not in CASES or not T_START <= t <= T_END for k, _, t in rows):
        raise RuntimeError("invalid or duplicate roster keys")
    return rows


def roster_stats(rows: list[tuple[str, str, int]]) -> dict:
    return {key: {"key_rows": sum(k == key for k, _, _ in rows),
                  "key_countries": len({c for k, c, _ in rows if k == key})}
            for key in CASES}


def threshold(key: str, roster_hash: str) -> dict:
    return {"family_id": FAMILY, "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
            "meaningful_beta_min_abs": MEANINGFUL_BETA, "meaningful_beta_unit": "log growth per log relative-price change",
            "min_complete_rows": MIN_COMPLETE_ROWS, "min_complete_countries": MIN_COMPLETE_COUNTRIES,
            "min_material_rows": MIN_MATERIAL_ROWS, "min_material_countries": MIN_MATERIAL_COUNTRIES,
            "material_abs_relative_price_log_change": MATERIAL_ABS_PRICE_CHANGE,
            "max_abs_price_and_outcome_log_change": MAX_ABS_LOG_CHANGE,
            "min_complete_years_per_country": MIN_COUNTRY_YEARS,
            "max_top_country_residualized_exposure_share": MAX_TOP_COUNTRY_RESIDUAL_SHARE,
            "roster_sha256": roster_hash, "source_lock_path": LOCK,
            "causal_credit": 0, "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0, "featured_eligible": False}


def make_registration(source_root: Path) -> None:
    rows = key_roster(source_root)
    roster_path = ROOT / ROSTER
    roster_path.parent.mkdir(parents=True, exist_ok=True)
    if roster_path.exists():
        raise RuntimeError("roster already exists")
    with roster_path.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["case", "country_iso3", "treatment_year"])
        writer.writerows(rows)
    roster_hash = sha256(roster_path)
    stats = roster_stats(rows)
    for key, case in CASES.items():
        group, margin = GROUPS[case["group"]], MARGINS[case["margin"]]
        countries = sorted({c for k, c, _ in rows if k == key})
        spec_path, steelman_path, _ = case_paths(case)
        claim = (f"In the frozen 1992–2023 country-year source-key roster, stronger annual growth in the "
                 f"{group['label']} producer-price index relative to the agriculture producer-price index "
                 f"from t-1 to t predicts higher {group['label']} {margin['label']} growth from t to t+1, "
                 "after prior outcome growth and country/year effects.")
        spec = {
            "hypothesis_id": case["id"], "version": 1, "status": "pre_registered", "topic": "growth",
            "claim_direction": "+", "claim": claim,
            "methodology_note": "Prospective eight-cell FAOSTAT descriptive family. Only schemas, codebooks, source hashes and item/country/year keys were read before registration. Price and crop measurements, flags and null masks remain unopened until the separate source lock is committed. Four food-crop groups cross two distinct supply margins; the eight cells overlap and are not independent replications.",
            "evidence_type": "associational",
            "sample": {"countries": countries, "period": [T_START - 1, T_END + 1], "temporal_structure": "panel",
                       "exclusion_rules": [
                           "Use only fixed key-roster treatment years, exact t-1/t producer price indices and exact t-1/t/t+1 crop outcome; no interpolation or nearest-year join.",
                           "Map FAOSTAT M49 country keys to current ISO3 with pycountry; exclude non-ISO3 aggregates.",
                           "Admit finite positive index/outcome values with A, E or X flags; exclude I, B, M, blank and unknown flags, and report admitted flag counts.",
                           "Exclude absolute log relative-price growth or either outcome growth above 0.50. Keep countries with at least five complete treatment years.",
                           "Do not change codes, years, flags, transformations, sample floors, multiplicity, estimator or gate thresholds after selected measurements are opened." ]},
            "variables": {
                "outcome": [{"name": f"forward_{case['margin']}_log_growth", "source": "faostat:crop_and_livestock_products",
                             "transformation": f"log({margin['label']} at t+1) minus log({margin['label']} at t), exact item {group['code']}, element {margin['code']}, unit {margin['unit']}",
                             "notes": "Aggregate group outcome; yield can change with crop composition."}],
                "treatment": [{"name": "relative_crop_producer_price_log_growth", "source": "faostat:producer_prices",
                               "transformation": f"[log(index item {group['code']}/agriculture index item 2051) at t] minus same at t-1; element 5539, annual 7021",
                               "notes": "Relative nominal farm-gate price index; not an exogenous price shock."}],
                "controls": [{"name": "prior_outcome_log_growth", "source": "faostat:crop_and_livestock_products",
                              "transformation": "log(outcome at t) minus log(outcome at t-1)"}]},
            "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"], "clustering": "country",
                          "notes": "OLS of next-year log outcome growth on current relative-price log growth and prior outcome log growth, with country and treatment-year effects. Country-cluster CR1 uncertainty, two-sided Student t(G-1), full-rank and residualized-exposure concentration gates."},
            "falsification": {"test": f"{FAMILY}_{key}",
                              "rule": "INCONCLUSIVE if any committed-source, sample (500/30), material-exposure (100/20), five-year-country, rank, concentration or finite-cluster-uncertainty gate fails. SUPPORTED iff beta >= +0.05 and two-sided p <= 0.01/8. REFUTED iff beta <= -0.05 and the same cutoff. Otherwise PARTIAL if estimable. All eight cells remain in the family denominator.",
                              "threshold": threshold(key, roster_hash)},
            "prior_confidence": 0.3,
            "disclosure": "Predictive, descriptive calibration only. Prices can respond to harvest shocks and common drivers; country/year effects and prior growth do not identify a causal farm response. No causal, policy, school, position or featured credit.",
            "steelman": steelman_path,
            "scope": {"period": [T_START - 1, T_END + 1], "countries": countries,
                      "outcome_dim": [margin["dimension"]], "policy_family": [], "treatment_tags": group["tags"]},
            "covers_claims": [], "linked_hypotheses": [], "linked_conditions": []}
        path = ROOT / spec_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise RuntimeError(f"existing spec: {path}")
        path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" +
                        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        steelman = (f"# Steelman: {group['label']} relative price and later {margin['label']}\n\n"
                    f"A rise in the farm-gate price of {group['label']} relative to the overall agriculture index can improve expected returns to producing that group. Farmers may respond through {margin['mechanism']}, so the frozen prediction is positive later {margin['label']} growth. The design compares a country with itself, removes common calendar-year shifts and adjusts for prior outcome growth.\n\n"
                    "The strongest alternative is joint determination: a poor harvest can raise current prices, while future weather, trade restrictions, input costs, subsidies, exchange rates and land limits can affect both price and output. Group-level yield can rise through commodity mix changes. A null or negative result weakens this predictive association but says little about a causal price response.\n\n"
                    "This is one of eight correlated pre-registered crop-group × supply-margin cells. All use a two-sided 0.01/8 family cutoff and explicit sample/failure gates. Raw source archives are hash-pinned in a local cache, with derived-parquet custody limitations. Zero causal, policy, school, position and featured credit.\n")
        (ROOT / steelman_path).write_text(steelman)
    lines = ["# Blind FAOSTAT crop supply-response preregistration", "",
             "Eight complete, claim-matched cells are fixed before any selected price/crop measurements, flags, null masks, sample variance or fits were opened. Only source schemas/codebooks, hashes and item/country/year keys were inspected. The four groups are FAOSTAT's cereals, roots and tubers, pulses, and oilcrops; the two supply margins are harvested area and yield. This is one coherent, correlated family, not eight independent replications.", "",
             f"Key-roster path: `{ROSTER}`; SHA-256 `{roster_hash}`. Source-key counts, which do not establish measured complete cases:", "",
             "| Cell | Key rows | Countries |", "| --- | ---: | ---: |"]
    for key, stat in stats.items():
        lines.append(f"| `{key}` | {stat['key_rows']} | {stat['key_countries']} |")
    lines += ["", "## Source custody", "",
              "The following ignored local FAOSTAT raw archive/derived-parquet files are pinned by exact SHA-256. They are not copied into Git; replay requires the matching local raw cache. There is no tracked fetch manifest proving the archive-to-parquet derivation, so provenance is limited. The official FAOSTAT database terms and crop/price metadata are cited below.", "",
              "| Role | Relative source path | SHA-256 |", "| --- | --- | --- |"]
    for role, source in SOURCES.items():
        lines.append(f"| {role} | `{source['path']}` | `{source['sha256']}` |")
    lines += ["", "FAOSTAT price element 5539 is the annual (month code 7021) 2014–2016=100 producer price index. The crop outcomes are element 5312 area harvested (ha) and element 5412 yield (kg/ha). M49 keys are mapped to current ISO3 and noncountry aggregates excluded. Flags A (official), E (estimated) and X (external organization) are admitted; I (receiving-agency imputed), B (time-series break), M (missing) and blanks are excluded. All admitted flag counts are reported after source lock.", "",
              "## Frozen analysis and failure gates", "",
              "For each group and country-year t=1992..2023, x is the annual log change in that group's producer-price index divided by the all-agriculture index, t-1 to t. y is log harvested-area or yield growth, t to t+1. Prior outcome log growth t-1 to t is controlled. Require finite positive observations and abs(x), abs(prior y), abs(forward y) <=0.50. Only countries with >=5 complete years remain. OLS includes country and treatment-year fixed effects; CR1 country-cluster standard errors use two-sided t(G-1). No fallback estimator or proxy is allowed.", "",
              "Each cell requires >=500 complete country-years in >=30 countries, >=100 material exposure years with |x|>=0.05 in >=20 countries, a full-rank design, finite positive clustered SE and no country providing >20% of residualized exposure sum of squares. Failure is INCONCLUSIVE. A positive coefficient >=0.05 and two-sided p<=0.00125 is SUPPORTED; a negative coefficient <=-0.05 at the same cutoff is REFUTED; other estimable cases are PARTIAL. Coefficient 0.05 means about 0.5% later log growth for a 10% relative-price increase. All eight remain in the Bonferroni denominator, including failures. Family alpha is 0.01; archive-wide selection remains unadjusted.", "",
              "This is predictive calibration, not a causal estimate. Price may respond to same-year harvest shocks or anticipation; group aggregation and estimation flags further limit interpretation. Zero causal, policy, school, position and featured credit.", "",
              "## Official source documentation", "",
              "- FAO Agricultural producer prices dataset and methodology: https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1 and https://files-faostat.fao.org/production/PP/PP_e.pdf",
              "- FAO crop production, yield and harvested-area dataset: https://data.fao.org/catalog/iso/d24a448b-3b62-4c09-8c1d-4a39bb599876",
              "- FAO statistical database terms (attribution and use conditions): https://www.fao.org/contact-us/terms/db-terms-of-use/en", ""]
    path = ROOT / PREREG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    print(json.dumps({"roster_sha256": roster_hash, "counts": stats}, indent=2))


def registration_commit() -> tuple[str, str, list[tuple[str, str, int]]]:
    paths = [RUNNER, TEST, PREREG, ROSTER]
    for case in CASES.values():
        paths.extend(case_paths(case)[:2])
    additions = {first_addition(path) for path in paths}
    if len(additions) != 1:
        raise RuntimeError("registration paths lack one first-addition commit")
    revision = additions.pop()
    for path in paths:
        frozen(path, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock was present in registration commit")
    rows = roster_rows()
    roster_hash = sha256(ROOT / ROSTER)
    for key, case in CASES.items():
        spec_path, steelman_path, run_path = case_paths(case)
        spec = yaml.safe_load((ROOT / spec_path).read_text())
        countries = sorted({c for k, c, _ in rows if k == key})
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered" or
            spec.get("sample", {}).get("countries") != countries or
            spec.get("scope", {}).get("countries") != countries or
            spec.get("falsification", {}).get("threshold") != threshold(key, roster_hash) or
            spec.get("steelman") != steelman_path or spec.get("covers_claims") != [] or
            spec.get("linked_hypotheses") != [] or
            git("ls-tree", "-r", "--name-only", revision, "--", run_path).strip()):
            raise RuntimeError(f"registered spec mismatch: {key}")
    return revision, roster_hash, rows


def make_lock(source_root: Path) -> None:
    reg, roster_hash, _ = registration_commit()
    for role, source in SOURCES.items():
        if sha256(raw(source_root, role)) != source["sha256"]:
            raise RuntimeError(f"raw source hash mismatch: {role}")
    path = ROOT / LOCK
    if path.exists():
        raise RuntimeError("source lock already exists")
    path.write_text(json.dumps({"family_id": FAMILY, "registration_commit": reg,
                                "roster_sha256": roster_hash, "sources": SOURCES,
                                "custody": "exact local raw archive and derived-parquet hashes; no tracked fetch manifest; raw files not copied into Git"},
                               indent=2) + "\n")
    print("prepared source lock", path)


def source_lock_commit(source_root: Path, reg: str, roster_hash: str) -> str:
    lock_rev = first_addition(LOCK)
    if lock_rev == reg or subprocess.run(["git", "merge-base", "--is-ancestor", reg, lock_rev], cwd=ROOT).returncode:
        raise RuntimeError("source-lock commit is not after registration")
    frozen(LOCK, lock_rev)
    document = json.loads((ROOT / LOCK).read_text())
    if document.get("family_id") != FAMILY or document.get("registration_commit") != reg or document.get("roster_sha256") != roster_hash or document.get("sources") != SOURCES:
        raise RuntimeError("source lock differs from frozen source list")
    for role, source in SOURCES.items():
        if not raw(source_root, role).is_file() or sha256(raw(source_root, role)) != source["sha256"]:
            raise RuntimeError(f"pinned source not present or changed: {role}")
    return lock_rev


def finite(value: object) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def normal_flag(flag: object) -> str | None:
    return str(flag).strip() if str(flag).strip() in ALLOWED_FLAGS else None


def load_values(source_root: Path) -> tuple[dict, dict]:
    """Called only after committed registration and source-lock checks."""
    price = pd.read_parquet(raw(source_root, "price_panel"), columns=["Area Code (M49)", "Item Code", "Element Code", "Months Code", "Year", "Value", "Flag"])
    price = price.loc[(price["Element Code"] == INDEX_ELEMENT) &
                      (price["Months Code"] == ANNUAL_MONTH_CODE) &
                      price["Item Code"].isin([AGRICULTURE_INDEX_CODE] + [v["code"] for v in GROUPS.values()])]
    crop = pd.read_parquet(raw(source_root, "crop_panel"), columns=["Area Code (M49)", "Item Code", "Element Code", "Year", "Value", "Flag", "Unit"])
    crop = crop.loc[crop["Item Code"].isin([v["code"] for v in GROUPS.values()]) &
                    crop["Element Code"].isin([v["code"] for v in MARGINS.values()])]
    pmap, cmap = {}, {}
    for r in price.itertuples(index=False, name=None):
        area, item, _, _, year, value, flag = r
        country = iso3(area)
        if country is None:
            continue
        key = (int(item), country, int(year))
        if key in pmap:
            raise RuntimeError(f"duplicate producer-price key: {key}")
        pmap[key] = (finite(value), normal_flag(flag))
    for r in crop.itertuples(index=False, name=None):
        area, item, element, year, value, flag, unit = r
        country = iso3(area)
        if country is None:
            continue
        key = (int(item), int(element), country, int(year))
        if key in cmap:
            raise RuntimeError(f"duplicate crop key: {key}")
        cmap[key] = (finite(value), normal_flag(flag), str(unit))
    return pmap, cmap


def selected_price(pmap: dict, item: int, country: str, year: int) -> tuple[float, str] | None:
    cell = pmap.get((item, country, year))
    return (cell[0], cell[1]) if cell and cell[0] is not None and cell[0] > 0 and normal_flag(cell[1]) else None


def selected_crop(cmap: dict, item: int, element: int, country: str, year: int, unit: str) -> tuple[float, str] | None:
    cell = cmap.get((item, element, country, year))
    return (cell[0], cell[1]) if cell and cell[0] is not None and cell[0] > 0 and normal_flag(cell[1]) and cell[2] == unit else None


def case_frame(key: str, rows: list[tuple[str, str, int]], pmap: dict, cmap: dict) -> tuple[pd.DataFrame, dict]:
    case = CASES[key]
    item, element = GROUPS[case["group"]]["code"], MARGINS[case["margin"]]["code"]
    unit = MARGINS[case["margin"]]["unit"]
    records, dropped, flag_counts = [], Counter(), Counter()
    case_rows = [(country, year) for k, country, year in rows if k == key]
    for country, year in case_rows:
        g0, g1 = selected_price(pmap, item, country, year - 1), selected_price(pmap, item, country, year)
        a0, a1 = selected_price(pmap, AGRICULTURE_INDEX_CODE, country, year - 1), selected_price(pmap, AGRICULTURE_INDEX_CODE, country, year)
        if not all((g0, g1, a0, a1)):
            dropped["price_value_or_flag"] += 1
            continue
        x = math.log(g1[0] / a1[0]) - math.log(g0[0] / a0[0])
        if abs(x) > MAX_ABS_LOG_CHANGE:
            dropped["price_growth_bound"] += 1
            continue
        o0, o1, o2 = (selected_crop(cmap, item, element, country, year + offset, unit) for offset in (-1, 0, 1))
        if not all((o0, o1, o2)):
            dropped["outcome_value_flag_or_unit"] += 1
            continue
        prior = math.log(o1[0] / o0[0])
        response = math.log(o2[0] / o1[0])
        if abs(prior) > MAX_ABS_LOG_CHANGE or abs(response) > MAX_ABS_LOG_CHANGE:
            dropped["outcome_growth_bound"] += 1
            continue
        records.append({"country": country, "year": year, "x": x, "prior": prior, "response": response})
        for role, cell in (("group_price_t_minus_1", g0), ("group_price_t", g1),
                           ("agriculture_price_t_minus_1", a0), ("agriculture_price_t", a1),
                           ("outcome_t_minus_1", o0), ("outcome_t", o1), ("outcome_t_plus_1", o2)):
            flag_counts[f"{role}:{cell[1]}"] += 1
    before = len(records)
    n_by_country = Counter(r["country"] for r in records)
    records = [r for r in records if n_by_country[r["country"]] >= MIN_COUNTRY_YEARS]
    frame = pd.DataFrame(records).sort_values(["year", "country"]).reset_index(drop=True) if records else pd.DataFrame()
    material = frame.loc[frame["x"].abs() >= MATERIAL_ABS_PRICE_CHANGE] if len(frame) else frame
    sample = {"key_rows": len(case_rows), "key_countries": len({c for c, _ in case_rows}),
              "complete_rows_before_country_floor": before, "valid_rows": len(frame),
              "valid_countries": int(frame["country"].nunique()) if len(frame) else 0,
              "material_exposure_rows": len(material),
              "material_exposure_countries": int(material["country"].nunique()) if len(material) else 0,
              "dropped": dict(dropped), "admitted_flag_counts_before_country_floor": dict(flag_counts),
              "selected_values_read_after_committed_source_lock": True}
    return frame, sample


def fit_case(frame: pd.DataFrame, sample: dict) -> tuple[str, str, dict]:
    failures = []
    if sample["valid_rows"] < MIN_COMPLETE_ROWS or sample["valid_countries"] < MIN_COMPLETE_COUNTRIES:
        failures.append("complete_case_floor")
    if sample["material_exposure_rows"] < MIN_MATERIAL_ROWS or sample["material_exposure_countries"] < MIN_MATERIAL_COUNTRIES:
        failures.append("material_exposure_floor")
    if failures:
        return "INCONCLUSIVE", ", ".join(failures), {"gates_failed": failures}
    nuisance = patsy.dmatrix("prior + C(country) + C(year)", frame, return_type="dataframe").to_numpy(dtype=float)
    design = patsy.dmatrix("x + prior + C(country) + C(year)", frame, return_type="dataframe")
    matrix = design.to_numpy(dtype=float)
    if np.linalg.matrix_rank(matrix) != matrix.shape[1]:
        return "INCONCLUSIVE", "full-rank gate failed", {"gates_failed": ["full_rank"]}
    residual_x = sm.OLS(frame["x"].to_numpy(dtype=float), nuisance).fit().resid
    shares = pd.DataFrame({"country": frame["country"], "ss": residual_x ** 2}).groupby("country", sort=True)["ss"].sum()
    total = float(shares.sum())
    if not math.isfinite(total) or total <= 0:
        return "INCONCLUSIVE", "no residualized exposure", {"gates_failed": ["residual_exposure"]}
    concentration = float(shares.max() / total)
    sample["top_country_residualized_exposure_share"] = concentration
    if concentration > MAX_TOP_COUNTRY_RESIDUAL_SHARE:
        return "INCONCLUSIVE", "residualized exposure concentrated in one country", {"gates_failed": ["residual_concentration"]}
    fit = sm.OLS(frame["response"].to_numpy(dtype=float), design).fit(
        cov_type="cluster", cov_kwds={"groups": frame["country"].to_numpy(), "use_correction": True})
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return "INCONCLUSIVE", "nonfinite country-cluster uncertainty", {"gates_failed": ["uncertainty"]}
    df = sample["valid_countries"] - 1
    p = float(2 * student_t.sf(abs(beta / se), df))
    critical = float(student_t.ppf(1 - P_MAX / 2, df))
    result = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
              "confidence_level": 1 - P_MAX, "confidence_interval": [beta - critical * se, beta + critical * se],
              "n_rows": sample["valid_rows"], "n_countries": sample["valid_countries"],
              "df_inference": df, "model_rank": matrix.shape[1],
              "top_country_residualized_exposure_share": concentration,
              "method": "country/year FE OLS plus prior outcome growth; country-cluster CR1; Student t(G-1)"}
    if beta >= MEANINGFUL_BETA and p <= P_MAX:
        return "SUPPORTED", "positive magnitude and eight-test multiplicity gates pass", result
    if beta <= -MEANINGFUL_BETA and p <= P_MAX:
        return "REFUTED", "negative magnitude and eight-test multiplicity gates pass", result
    return "PARTIAL", "estimable association does not clear directional magnitude and multiplicity gates", result


def artifacts(key: str, frame: pd.DataFrame, sample: dict, verdict: str, reason: str,
              result: dict, reg: str, lock_rev: str, roster_hash: str, run_utc: str) -> dict[str, bytes]:
    case = CASES[key]
    group, margin = GROUPS[case["group"]], MARGINS[case["margin"]]
    spec_path, steelman_path, run_path = case_paths(case)
    inputs = {role: SOURCES[role] for role in SOURCES}
    diagnostic = {"hypothesis_id": case["id"], "family_id": FAMILY, "verdict": verdict,
                  "verdict_label": verdict, "verdict_reason": reason, "run_utc": run_utc,
                  "runner": RUNNER, "preregistration_commit": reg, "source_lock_commit": lock_rev,
                  "source_lock": LOCK, "template": "panel_fe", "preflight": sample, "primary": result,
                  "p_max_two_sided_bonferroni": P_MAX, "meaningful_beta_min_abs": MEANINGFUL_BETA,
                  "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
                  "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": case["id"], "run_utc": run_utc, "runner": RUNNER,
                "preregistration_commit": reg, "source_lock_commit": lock_rev,
                "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
                "derived_panel": sample, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": run_utc,
              "hypothesis": {"id": case["id"], "path": spec_path, "topic": "growth"},
              "preregistration": {"spec_commit": reg, "source_lock_commit": lock_rev,
                                  "family_id": FAMILY, "family_size": len(CASES),
                                  "key_roster": ROSTER, "key_roster_sha256": roster_hash,
                                  "steelman": steelman_path},
              "reproduction": {"runner": RUNNER, "run_dir": run_path,
                               "command": f"python3 {RUNNER} --source-root <local raw cache> --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": inputs, "sample": sample}, "results": {"primary": result},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    if verdict == "INCONCLUSIVE":
        finding = f"**INCONCLUSIVE.** {reason}. No directional claim is graded."
    else:
        finding = (f"**{verdict}.** Frozen descriptive beta {result['coefficient']:+.5f} log growth per "
                   f"one log-point relative producer-price growth (country-cluster SE {result['std_error']:.5f}; "
                   f"two-sided p={result['p_value_two_sided']:.5g}; {result['n_rows']} country-years; "
                   f"{result['n_countries']} countries). {reason}.")
    card = (f"# {group['label']} relative producer price and next-year {margin['label']}\n\n{finding}\n\n"
            "One of eight correlated FAOSTAT crop supply-response cells, with a shared 0.01/8 family cutoff. "
            "A relative producer-price association does not identify a causal farm response. "
            "Raw source hashes require the matching local cache for exact replay. "
            "Zero causal, policy, school, position or featured credit.\n")
    binned = []
    if len(frame):
        bins = pd.qcut(frame["x"], q=10, duplicates="drop")
        for interval, sub in frame.groupby(bins, observed=True):
            binned.append({"relative_price_log_change_min": float(sub["x"].min()),
                           "relative_price_log_change_max": float(sub["x"].max()),
                           "median_forward_outcome_log_growth": float(sub["response"].median()),
                           "rows": int(len(sub))})
    coefficient = pd.DataFrame([{"hypothesis_id": case["id"], "term": "relative_crop_price_log_growth",
                                 "estimate": result.get("coefficient", float("nan")),
                                 "std_error": result.get("std_error", float("nan")),
                                 "p_value": result.get("p_value_two_sided", float("nan"))}])
    parquet = io.BytesIO()
    coefficient.to_parquet(parquet, index=False)
    replication = ("#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\n"
                   "root = os.environ.get('IESET_RAW_ROOT')\n"
                   "if not root:\n    raise SystemExit('set IESET_RAW_ROOT to the matching raw FAOSTAT cache')\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--source-root', root, '--verify']))\n")
    return {"manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "diagnostics.json": (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(),
            "result_card.md": card.encode(),
            "chart_data.json": (json.dumps(binned, indent=2, ensure_ascii=False) + "\n").encode(),
            "coefficients.parquet": parquet.getvalue(),
            "hypothesis.yaml": (ROOT / spec_path).read_bytes(), "replication.py": replication.encode()}


def run(source_root: Path, verify: bool) -> None:
    reg, roster_hash, rows = registration_commit()
    lock_rev = source_lock_commit(source_root, reg, roster_hash)
    pmap, cmap = load_values(source_root)
    first = next(iter(CASES.values()))
    run_utc = (json.loads((ROOT / case_paths(first)[2] / "diagnostics.json").read_text())["run_utc"]
               if verify else datetime.now(timezone.utc).isoformat(timespec="seconds"))
    summaries = []
    for key, case in CASES.items():
        frame, sample = case_frame(key, rows, pmap, cmap)
        verdict, reason, result = fit_case(frame, sample)
        produced = artifacts(key, frame, sample, verdict, reason, result, reg, lock_rev, roster_hash, run_utc)
        directory = ROOT / case_paths(case)[2]
        if verify:
            mismatch = [name for name, content in produced.items()
                        if not (directory / name).is_file() or (directory / name).read_bytes() != content]
            if mismatch:
                raise RuntimeError(f"{case['id']} exact replay mismatch: {mismatch}")
        else:
            directory.mkdir(parents=True, exist_ok=False)
            for name, content in produced.items():
                (directory / name).write_bytes(content)
        summaries.append((case["id"], verdict, sample["valid_rows"], sample["valid_countries"], reason))
    if verify:
        print("Exact replay passed:", summaries)
        return
    lines = ["# FAOSTAT relative-price crop supply family — results", "",
             f"Registration commit: `{reg}`; source-lock commit: `{lock_rev}`.",
             "All eight registered cells remain in the Bonferroni denominator, including inconclusive cases.", "",
             "| Cell | Verdict | Rows | Countries | Gate summary |", "| --- | --- | ---: | ---: | --- |"]
    for ident, verdict, n, countries, reason in summaries:
        lines.append(f"| `{ident}` | {verdict} | {n} | {countries} | {reason} |")
    lines += ["", "These correlated associations use overlapping years, group sectors and two related supply margins. They are not independent replications. Relative prices may respond to harvest shocks. All results are descriptive calibrations with zero causal, policy, school, position or featured credit.",
              "The raw archives and derived parquets are hash-pinned in a local cache; no tracked FAOSTAT fetch manifest proves archive-to-parquet derivation. Official FAO database terms and attribution apply.", ""]
    (ROOT / SUMMARY).write_text("\n".join(lines))
    print(summaries)


def main() -> None:
    parser = argparse.ArgumentParser()
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--make-registration", action="store_true")
    choices.add_argument("--check-registration", action="store_true")
    choices.add_argument("--make-lock", action="store_true")
    choices.add_argument("--check-lock", action="store_true")
    choices.add_argument("--run", action="store_true")
    choices.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    if args.make_registration or args.make_lock or args.check_lock or args.run or args.verify:
        if args.source_root is None:
            parser.error("--source-root is required for this command")
    if args.make_registration:
        make_registration(args.source_root)
    elif args.check_registration:
        print("registration", registration_commit()[0])
    elif args.make_lock:
        make_lock(args.source_root)
    elif args.check_lock:
        reg, roster_hash, _ = registration_commit()
        print("source lock", source_lock_commit(args.source_root, reg, roster_hash))
    else:
        run(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
