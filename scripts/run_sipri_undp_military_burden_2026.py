#!/usr/bin/env python3
"""Frozen four-cell descriptive SIPRI military-burden/UNDP development family.

--prepare reads source hashes, schemas and keys only. Selected numeric columns
are first opened by --run, after separately committed source locks. Raw values
remain in a local ignored source cache and are never copied into Git.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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
FAMILY = "sipri_undp_military_burden_development_2026_10_10"
RUNNER = "scripts/run_sipri_undp_military_burden_2026.py"
PREREG = "engine/audits/sipri_undp_military_burden_prereg_2026-10-10.md"
SUMMARY = "engine/audits/sipri_undp_military_burden_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/sipri_undp_military_burden_2026_key_roster.csv"
LOCK = "data/pinned_evidence/sipri_undp_military_burden_2026.manifest.json"
SOURCES = {
    "military_burden": {"publisher": "sipri", "series_id": "milex_share_gdp",
        "path": "data/vintages/sipri/milex_share_gdp@2026-04-30T114417Z.parquet",
        "sha256": "5ccce854cc3127eb0510b2f9f0e99741fb4a037a5950c745137970e7c618d3be",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml"},
    "life_expectancy": {"publisher": "undp_hdi", "series_id": "life_expectancy",
        "path": "data/vintages/undp_hdi/life_expectancy@2026-05-05T204045Z.parquet",
        "sha256": "13b99319b8b1a2be96f0774dfd67104e2b7a41b4ca176bf43486b65ff99f43cb",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml"},
    "mean_years_schooling": {"publisher": "undp_hdi", "series_id": "mean_years_schooling",
        "path": "data/vintages/undp_hdi/mean_years_schooling@2026-05-05T204045Z.parquet",
        "sha256": "e3a1e5a17bf361219f2a13a1e5e4b6c5cc0faa28c620245a907f2e087a725449",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml"},
    "expected_years_schooling": {"publisher": "undp_hdi", "series_id": "expected_years_schooling",
        "path": "data/vintages/undp_hdi/expected_years_schooling@2026-05-05T204045Z.parquet",
        "sha256": "86c0f5c46556a914fa8bc72405fa46ad9e8de550612d03795531d2d196d5735f",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml"},
    "gni_per_capita": {"publisher": "undp_hdi", "series_id": "gni_per_capita",
        "path": "data/vintages/undp_hdi/gni_per_capita@2026-05-05T204045Z.parquet",
        "sha256": "9f9c6a839567dcfa4dd3f51876f8e76755e5bddff3d5539ba0cd077d618f30a0",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml"},
}
CASES = {
    "life_expectancy": {"id": "sipri_military_burden_later_life_expectancy_2026", "label": "life expectancy", "unit": "years", "meaningful": 0.15, "bound": 8.0, "topic": "healthcare", "dimension": "life_expectancy_health"},
    "mean_years_schooling": {"id": "sipri_military_burden_later_mean_schooling_2026", "label": "mean years of schooling", "unit": "years", "meaningful": 0.05, "bound": 5.0, "topic": "distribution", "dimension": "education_access"},
    "expected_years_schooling": {"id": "sipri_military_burden_later_expected_schooling_2026", "label": "expected years of schooling", "unit": "years", "meaningful": 0.10, "bound": 5.0, "topic": "distribution", "dimension": "education_access"},
    "gni_per_capita": {"id": "sipri_military_burden_later_gni_per_capita_2026", "label": "real GNI per person", "unit": "100 log points", "meaningful": 1.0, "bound": 100.0, "topic": "growth", "dimension": "gdp_growth"},
}
NAME_EXCEPTIONS = {
    "Brunei": "BRN", "Cape Verde": "CPV", "Congo, DR": "COD", "Congo, Republic": "COG",
    "Cote d'Ivoire": "CIV", "Czechia": "CZE", "Eswatini": "SWZ", "Gambia, The": "GMB",
    "Korea, North": "PRK", "Korea, South": "KOR", "Kyrgyz Republic": "KGZ",
    "Laos": "LAO", "Moldova": "MDA", "Russia": "RUS", "Taiwan": "TWN",
    "Timor Leste": "TLS", "Türkiye": "TUR", "United States of America": "USA",
    "Viet Nam": "VNM",
}
T_START, T_END = 1994, 2016  # all subsequent outcomes end by 2019
MIN_YEARS_PER_COUNTRY = 6
MAX_MILITARY_SHARE = 40.0  # SIPRI's source sheet is percentage of GDP
MAX_ABS_EXPOSURE = 3.0  # percentage-point change over three years
MATERIAL_ABS_EXPOSURE = 0.25
MIN_ROWS, MIN_COUNTRIES = 900, 60
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 100, 30
MAX_TOP_COUNTRY_RESIDUAL_SHARE = 0.15
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
LIMITATIONS = [
    "Military burden is observational and may respond to war, threats, politics, GDP-denominator changes and economic crises; it is not a randomized or policy treatment.",
    "Country and treatment-year effects plus prior outcome change do not remove time-varying conflict, development trends, aid, migration or fiscal composition confounding.",
    "SIPRI military-expenditure figures are continually revised; this test pins an older 2023-ending local Share of GDP sheet, not the current edition.",
    "The SIPRI Parquet retains no observation-quality flags; exact source vintages cannot identify interpolated or otherwise qualified cells. UNDP historical components may be modelled or revised.",
    "Three-year treatment and outcome windows overlap across consecutive observations. Country-clustered inference addresses some serial dependence but does not establish causality.",
    "Four correlated endpoints form one Bonferroni family, not four independent replications. The wider IESET archive search is not multiplicity-adjusted.",
    "The raw source files are hash-pinned in a local cache and supported by tracked fetch manifests; licensed SIPRI measurements are not copied into Git.",
    "No causal, policy, school, position or featured credit is assigned.",
]
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "featured_eligible": False}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(path: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if not commits:
        raise RuntimeError(f"no first-addition commit for {path}")
    return commits[-1]


def frozen(path: str, revision: str) -> None:
    file = ROOT / path
    if not file.is_file() or file.read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen bytes changed: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen path: {path}")


def raw(source_root: Path, role: str) -> Path:
    return source_root / SOURCES[role]["path"]


def verify_sources(source_root: Path) -> None:
    for role, source in SOURCES.items():
        path = raw(source_root, role)
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"source missing or hash mismatch: {role}")
        manifest = yaml.safe_load((source_root / source["manifest"]).read_text())
        matches = [e for e in manifest.get("entries", []) if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"tracked fetch manifest mismatch: {role}")


def iso3(name: str) -> str | None:
    if name in NAME_EXCEPTIONS:
        return NAME_EXCEPTIONS[name]
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None  # aggregate, predecessor state or ambiguous string


def paths(case: dict) -> tuple[str, str, str]:
    ident = case["id"]
    return (f"hypotheses/{case['topic']}/{ident}.yaml",
            f"hypotheses/steelman/{ident}.md", f"engine/runs/{ident}")


def key_roster(source_root: Path) -> list[tuple[str, str, int]]:
    """Only read country/year source keys; no value, null mask or flag column."""
    military = pd.read_parquet(raw(source_root, "military_burden"), columns=["Country", "year"])
    military["country"] = military["Country"].map(iso3)
    military = military.loc[military["country"].notna()]
    if military.duplicated(["country", "year"]).any():
        raise RuntimeError("duplicate SIPRI country/year keys after mapping")
    military_keys = set(zip(military["country"], military["year"]))
    rosters = []
    for key in CASES:
        outcome = pd.read_parquet(raw(source_root, key), columns=["country_iso3", "year"])
        if outcome.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate UNDP country/year keys: {key}")
        outcome_keys = set(zip(outcome["country_iso3"], outcome["year"]))
        for country in sorted(military["country"].unique()):
            for year in range(T_START, T_END + 1):
                if (all((country, z) in military_keys for z in (year - 3, year))
                        and all((country, z) in outcome_keys for z in (year - 3, year, year + 3))):
                    rosters.append((key, country, year))
    return rosters


def roster_rows() -> list[tuple[str, str, int]]:
    with (ROOT / ROSTER).open(newline="") as f:
        rows = [(r["case"], r["country_iso3"], int(r["treatment_year"])) for r in csv.DictReader(f)]
    if len(rows) != len(set(rows)) or any(k not in CASES or not T_START <= y <= T_END for k, _, y in rows):
        raise RuntimeError("invalid key roster")
    if rows != sorted(rows, key=lambda z: (list(CASES).index(z[0]), z[1], z[2])):
        raise RuntimeError("key roster order changed")
    return rows


def threshold(key: str, roster_hash: str) -> dict:
    case = CASES[key]
    return {"family_id": FAMILY, "family_size": len(CASES),
            "family_alpha": FAMILY_ALPHA, "p_max_two_sided_bonferroni": P_MAX,
            "expected_beta_sign": "-", "meaningful_beta_min_abs": case["meaningful"],
            "meaningful_beta_unit": f"{case['unit']} later 3-year change per +1 percentage point military-burden change",
            "key_roster_sha256": roster_hash, "source_lock_path": LOCK,
            "min_complete_rows": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
            "min_material_rows": MIN_MATERIAL_ROWS, "min_material_countries": MIN_MATERIAL_COUNTRIES,
            "material_abs_exposure_percentage_points": MATERIAL_ABS_EXPOSURE,
            "max_abs_exposure_percentage_points": MAX_ABS_EXPOSURE,
            "max_abs_prior_and_forward_outcome_change": case["bound"],
            "min_complete_years_per_country": MIN_YEARS_PER_COUNTRY,
            "max_top_country_residualized_exposure_share": MAX_TOP_COUNTRY_RESIDUAL_SHARE,
            "causal_credit": 0, "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0, "featured_eligible": False}


def prepare(source_root: Path) -> None:
    verify_sources(source_root)
    rows = key_roster(source_root)
    roster = ROOT / ROSTER
    roster.parent.mkdir(parents=True, exist_ok=True)
    if roster.exists():
        raise RuntimeError("roster already exists")
    with roster.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["case", "country_iso3", "treatment_year"])
        writer.writerows(rows)
    roster_hash = sha256(roster)
    stats = {k: {"key_rows": sum(r[0] == k for r in rows),
                 "key_countries": len({r[1] for r in rows if r[0] == k})} for k in CASES}
    for key, case in CASES.items():
        spec_path, steelman_path, _ = paths(case)
        countries = sorted({c for k, c, _ in rows if k == key})
        transform = ("100 * log(GNI per capita at t+3 / GNI per capita at t)"
                     if key == "gni_per_capita" else f"{case['label']} at t+3 minus t")
        prior = ("100 * log(GNI per capita at t / GNI per capita at t-3)"
                 if key == "gni_per_capita" else f"{case['label']} at t minus t-3")
        spec = {
            "hypothesis_id": case["id"], "version": 1, "status": "pre_registered", "topic": case["topic"],
            "claim_direction": "-",
            "claim": f"Within the frozen 1994–2016 treatment-year roster, a larger three-year rise in SIPRI military expenditure as a share of GDP from t-3 to t predicts a smaller subsequent three-year improvement in UNDP {case['label']} from t to t+3, after the prior outcome trend and country/year effects.",
            "methodology_note": "Blind four-cell descriptive SIPRI–UNDP family. Before registration only source manifests, hashes, schemas, name/country/year keys and official methodology were inspected; neither selected values nor null masks were read. Four correlated UNDP components share a SIPRI exposure; they are not independent replications.",
            "evidence_type": "associational",
            "sample": {"countries": countries, "period": [T_START - 3, T_END + 3],
                       "temporal_structure": "panel", "exclusion_rules": [
                           "Use only frozen key-roster years and exact t-3/t SIPRI and t-3/t/t+3 UNDP observations; no interpolation or nearest-year match.",
                           "Map SIPRI country names by frozen pycountry lookup and explicit exception table; exclude aggregates and predecessor states.",
                           "Keep finite military shares from 0 to 40 percent of GDP and finite outcomes; GNI per person must be strictly positive.",
                           "Exclude absolute three-year military-burden change above 3 percentage points and absolute prior or subsequent outcome change above the frozen outcome-specific bound.",
                           "Keep only countries with at least six complete treatment years; do not change the source, crosswalk, window, model, multiplicity or gates after selected values are opened."]},
            "variables": {
                "outcome": [{"name": f"later_{key}_three_year_change", "source": f"undp_hdi:{key}",
                             "transformation": transform, "notes": "UNDP historical series may be modelled or revised."}],
                "treatment": [{"name": "military_burden_three_year_change", "source": "sipri:milex_share_gdp",
                               "transformation": "military expenditure share of GDP at t minus t-3, in percentage points",
                               "notes": "Military burden is not an exogenous policy treatment; changes can reflect the GDP denominator."}],
                "controls": [{"name": "prior_outcome_three_year_change", "source": f"undp_hdi:{key}", "transformation": prior}]},
            "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"], "clustering": "country",
                          "notes": "OLS of later three-year change on military-burden change and prior outcome change, with country and treatment-year fixed effects. CR1 country-clustered SE and two-sided Student t(G-1); rank and residualized-exposure concentration gates."},
            "falsification": {"test": f"{FAMILY}_{key}",
                              "rule": f"INCONCLUSIVE if frozen-source, 900-row/60-country, 100-material-row/30-country, six-year-country, full-rank, finite clustered-SE or 15% residualized-exposure concentration gate fails. SUPPORTED iff beta <= -{case['meaningful']} and two-sided p <= 0.0025. REFUTED iff beta >= +{case['meaningful']} at the same cutoff. Otherwise PARTIAL if estimable. All four stay in the family denominator.",
                              "threshold": threshold(key, roster_hash)},
            "prior_confidence": 0.25,
            "disclosure": "Descriptive predictive calibration only. War, security shocks, GDP-denominator changes and development can jointly drive spending and UNDP outcomes. No causal, policy, school, position or featured credit.",
            "steelman": steelman_path,
            "scope": {"period": [T_START - 3, T_END + 3], "countries": countries,
                      "outcome_dim": [case["dimension"]], "policy_family": [],
                      "treatment_tags": ["military_burden", "public_spending_composition"]},
            "covers_claims": [], "linked_hypotheses": [], "linked_conditions": []}
        path = ROOT / spec_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise RuntimeError(f"existing spec: {path}")
        path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
                        + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        (ROOT / steelman_path).write_text(
            f"# Steelman: military burden and later {case['label']}\n\n"
            "A greater fraction of national output devoted to the military could coincide with fewer resources for other development priorities, so the frozen directional prediction is a smaller later improvement. This is an opportunity-cost mechanism, not an identified spending substitution.\n\n"
            "The strongest alternative is that security threats or wars raise military burden while independently harming health, schooling and income. Recessions can raise the military share by shrinking GDP even without higher spending. Reverse prioritization and slow-moving development trends also matter. A negative association cannot establish that military spending caused any change; a null or positive estimate weakens only this predictive pattern.\n\n"
            "This is one of four correlated UNDP endpoints in a single Bonferroni family. Exact source vintages and keys are pinned; the SIPRI extract lacks retained cell-quality flags and can be revised. No causal, policy, school, position or featured credit.\n")
    lines = ["# Blind SIPRI military burden and later UNDP components preregistration", "",
        "One four-cell descriptive family was fixed before selected military-share or UNDP values, null masks or fits were opened. Source manifest metadata, hashes, schemas, country/year keys and official methods were inspected. The four components overlap and are not independent replications.", "",
        f"Key roster `{ROSTER}` has SHA-256 `{roster_hash}`. Source-key opportunities do not establish measured complete cases.", "",
        "| Outcome | Key rows | Countries |", "| --- | ---: | ---: |"]
    for key in CASES:
        lines.append(f"| {key} | {stats[key]['key_rows']} | {stats[key]['key_countries']} |")
    lines += ["", "## Source custody", "",
        "All five ignored local Parquets are pinned below and match tracked fetch-manifest entries. The SIPRI vintage is the Share of GDP sheet of a 2023-ending workbook, while the UNDP vintage is the 2025 HDR component time series. Licensed raw values are not committed. Exact replay requires matching local files. The SIPRI local Parquet has no retained observation-quality flags.", "",
        "| Role | Relative path | SHA-256 | Manifest |", "| --- | --- | --- | --- |"]
    for role, source in SOURCES.items():
        lines.append(f"| {role} | `{source['path']}` | `{source['sha256']}` | `{source['manifest']}` |")
    lines += ["", "## Frozen design and failure gates", "",
        "Exposure years t=1994..2016; x is the SIPRI military-expenditure share of GDP (percentage points) at t minus t-3. Every outcome is its UNDP value change from t to t+3; GNI per person uses 100 × log ratio. Prior outcome change t-3 to t is controlled. Exact years only; no pandemic period enters the outcome. The explicit name crosswalk and pycountry conversion exclude aggregate and predecessor-state rows. Shares must be finite and 0..40, with |x|≤3. Outcome-specific three-year absolute bounds are 8 life years, 5 mean schooling years, 5 expected schooling years and 100 log points of GNI. Countries need at least six complete years.", "",
        "Each cell requires at least 900 complete rows/60 countries and at least 100 material rows/30 countries with |x|≥0.25 percentage points. The country and treatment-year fixed-effect OLS with prior outcome change must be full rank, finite clustered SE, and no country can exceed 15% of residualized exposure sum of squares. Failure is INCONCLUSIVE. A negative beta meeting the cell's fixed practical magnitude and two-sided p≤0.0025 is SUPPORTED; an equally strong positive beta is REFUTED; other estimable cells are PARTIAL. Four cells remain in the family denominator even if one fails. Family alpha is 0.01. No wider archive-search correction is claimed.", "",
        "This is an observational predictor test, not an estimate of spending tradeoffs or a military policy effect. War, threats, crises, recession denominators, fiscal composition and common development trends are unresolved. Overlapping windows and revised/modelled inputs add uncertainty. All cells have zero causal, policy, school, position and featured credit.", "",
        "Official source documentation: https://www.sipri.org/databases/milex/sources-and-methods and https://hdr.undp.org/data-center/documentation-and-downloads", ""]
    (ROOT / PREREG).write_text("\n".join(lines))
    print(json.dumps({"roster_sha256": roster_hash, "structural_counts": stats}, indent=2))


def registration_commit() -> tuple[str, str, list[tuple[str, str, int]]]:
    paths_to_check = [RUNNER, PREREG, ROSTER]
    for case in CASES.values():
        paths_to_check.extend(paths(case)[:2])
    additions = {first_addition(path) for path in paths_to_check}
    if len(additions) != 1:
        raise RuntimeError("registration paths must share one first-addition commit")
    revision = additions.pop()
    for path in paths_to_check:
        frozen(path, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock appeared in registration commit")
    rows = roster_rows()
    digest = sha256(ROOT / ROSTER)
    for key, case in CASES.items():
        spec_path, steelman_path, run_path = paths(case)
        spec = yaml.safe_load((ROOT / spec_path).read_text())
        countries = sorted({c for k, c, _ in rows if k == key})
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("sample", {}).get("countries") != countries
                or spec.get("falsification", {}).get("threshold") != threshold(key, digest)
                or spec.get("steelman") != steelman_path
                or git("ls-tree", "-r", "--name-only", revision, "--", run_path).strip()):
            raise RuntimeError(f"registered spec differs: {key}")
    return revision, digest, rows


def make_lock(source_root: Path) -> None:
    revision, digest, _ = registration_commit()
    verify_sources(source_root)
    path = ROOT / LOCK
    if path.exists():
        raise RuntimeError("source lock already exists")
    path.write_text(json.dumps({"family_id": FAMILY, "registration_commit": revision,
                                "key_roster_sha256": digest, "sources": SOURCES,
                                "custody": "tracked fetch-manifest entries and exact local Parquet hashes; raw measurements omitted from Git"},
                               indent=2) + "\n")
    print("prepared", path)


def lock_commit(source_root: Path, revision: str, digest: str) -> str:
    lock_revision = first_addition(LOCK)
    if lock_revision == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, lock_revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock does not descend from registration")
    frozen(LOCK, lock_revision)
    record = json.loads((ROOT / LOCK).read_text())
    if record != {"family_id": FAMILY, "registration_commit": revision,
                  "key_roster_sha256": digest, "sources": SOURCES,
                  "custody": "tracked fetch-manifest entries and exact local Parquet hashes; raw measurements omitted from Git"}:
        raise RuntimeError("source-lock content mismatch")
    verify_sources(source_root)
    return lock_revision


def finite(value: object) -> float | None:
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def values(source_root: Path) -> tuple[dict, dict]:
    """Call only after registration and source-lock commits are verified."""
    military = pd.read_parquet(raw(source_root, "military_burden"), columns=["Country", "year", "value"])
    military["country"] = military["Country"].map(iso3)
    military = military.loc[military["country"].notna()]
    if military.duplicated(["country", "year"]).any():
        raise RuntimeError("duplicate SIPRI mapped value key")
    mmap = {(str(c), int(y)): finite(v) for c, y, v in military[["country", "year", "value"]].itertuples(index=False, name=None)}
    outcomes = {}
    for key in CASES:
        df = pd.read_parquet(raw(source_root, key), columns=["country_iso3", "year", "value"])
        if df.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate UNDP value key: {key}")
        outcomes[key] = {(str(c), int(y)): finite(v) for c, y, v in df.itertuples(index=False, name=None)}
    return mmap, outcomes


def frame_for(key: str, rows: list[tuple[str, str, int]], mmap: dict, outcomes: dict) -> tuple[pd.DataFrame, dict]:
    case = CASES[key]
    selected = [(c, y) for k, c, y in rows if k == key]
    o = outcomes[key]
    records, dropped = [], Counter()
    for country, year in selected:
        s0, s1 = mmap.get((country, year - 3)), mmap.get((country, year))
        if s0 is None or s1 is None or not all(0 <= s <= MAX_MILITARY_SHARE for s in (s0, s1)):
            dropped["military_value_or_range"] += 1
            continue
        x = s1 - s0
        if abs(x) > MAX_ABS_EXPOSURE:
            dropped["exposure_bound"] += 1
            continue
        v0, v1, v2 = (o.get((country, year + offset)) for offset in (-3, 0, 3))
        if any(v is None for v in (v0, v1, v2)) or (key == "gni_per_capita" and min(v0, v1, v2) <= 0):
            dropped["outcome_value_or_sign"] += 1
            continue
        if key == "gni_per_capita":
            prior, later = 100 * math.log(v1 / v0), 100 * math.log(v2 / v1)
        else:
            prior, later = v1 - v0, v2 - v1
        if not all(math.isfinite(z) and abs(z) <= case["bound"] for z in (prior, later)):
            dropped["outcome_change_bound"] += 1
            continue
        records.append({"country": country, "year": year, "x": x, "prior": prior, "response": later})
    before = len(records)
    count_by_country = Counter(r["country"] for r in records)
    records = [r for r in records if count_by_country[r["country"]] >= MIN_YEARS_PER_COUNTRY]
    frame = pd.DataFrame(records).sort_values(["year", "country"]).reset_index(drop=True) if records else pd.DataFrame()
    material = frame.loc[frame["x"].abs() >= MATERIAL_ABS_EXPOSURE] if len(frame) else frame
    sample = {"key_rows": len(selected), "key_countries": len({c for c, _ in selected}),
              "complete_rows_before_country_floor": before, "valid_rows": len(frame),
              "valid_countries": int(frame["country"].nunique()) if len(frame) else 0,
              "material_exposure_rows": len(material),
              "material_exposure_countries": int(material["country"].nunique()) if len(material) else 0,
              "dropped": dict(dropped), "selected_values_read_after_committed_source_lock": True}
    return frame, sample


def fit_case(key: str, frame: pd.DataFrame, sample: dict) -> tuple[str, str, dict]:
    failures = []
    if sample["valid_rows"] < MIN_ROWS or sample["valid_countries"] < MIN_COUNTRIES:
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
        return "INCONCLUSIVE", "residualized exposure concentrated in one country", {"gates_failed": ["residual_concentration"], "top_country_residualized_exposure_share": concentration}
    fit = sm.OLS(frame["response"].to_numpy(dtype=float), design).fit(
        cov_type="cluster", cov_kwds={"groups": frame["country"].to_numpy(), "use_correction": True})
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return "INCONCLUSIVE", "invalid country-cluster uncertainty", {"gates_failed": ["uncertainty"]}
    df = sample["valid_countries"] - 1
    p = float(2 * student_t.sf(abs(beta / se), df))
    critical = float(student_t.ppf(1 - P_MAX / 2, df))
    result = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
              "confidence_level": 1 - P_MAX, "confidence_interval": [beta - critical * se, beta + critical * se],
              "n_rows": sample["valid_rows"], "n_countries": sample["valid_countries"],
              "df_inference": df, "model_rank": matrix.shape[1],
              "top_country_residualized_exposure_share": concentration,
              "method": "country/year FE OLS plus prior outcome change; country-cluster CR1; Student t(G-1)"}
    meaningful = CASES[key]["meaningful"]
    if beta <= -meaningful and p <= P_MAX:
        return "SUPPORTED", "negative magnitude and four-test multiplicity gates pass", result
    if beta >= meaningful and p <= P_MAX:
        return "REFUTED", "positive magnitude and four-test multiplicity gates pass", result
    return "PARTIAL", "estimable association does not clear directional magnitude and multiplicity gates", result


def artifacts(key: str, sample: dict, verdict: str, reason: str, result: dict,
              reg: str, lock_rev: str, roster_hash: str, run_utc: str) -> dict[str, bytes]:
    case = CASES[key]
    spec_path, steelman_path, run_path = paths(case)
    diagnostic = {"hypothesis_id": case["id"], "family_id": FAMILY, "family_size": len(CASES),
                  "verdict": verdict, "verdict_label": verdict, "verdict_reason": reason,
                  "run_utc": run_utc, "runner": RUNNER, "preregistration_commit": reg,
                  "source_lock_commit": lock_rev, "source_lock": LOCK,
                  "template": "panel_fe", "preflight": sample, "primary": result,
                  "p_max_two_sided_bonferroni": P_MAX,
                  "meaningful_beta_min_abs": case["meaningful"],
                  "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                  "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": case["id"], "run_utc": run_utc,
                "runner": RUNNER, "preregistration_commit": reg, "source_lock_commit": lock_rev,
                "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": sample, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": run_utc,
              "hypothesis": {"id": case["id"], "path": spec_path, "topic": case["topic"]},
              "preregistration": {"spec_commit": reg, "source_lock_commit": lock_rev,
                                  "family_id": FAMILY, "family_size": len(CASES),
                                  "key_roster": ROSTER, "key_roster_sha256": roster_hash,
                                  "steelman": steelman_path},
              "reproduction": {"runner": RUNNER, "run_dir": run_path,
                               "command": f"python3 {RUNNER} --source-root <matching local cache> --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": SOURCES, "sample": sample}, "results": {"primary": result},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    if verdict == "INCONCLUSIVE":
        finding = f"**INCONCLUSIVE.** {reason}. No directional claim is graded."
    else:
        finding = (f"**{verdict}.** Frozen descriptive beta {result['coefficient']:+.5f} {case['unit']} "
                   f"of later three-year change per +1 percentage-point military-burden change "
                   f"(country-cluster SE {result['std_error']:.5f}; two-sided p={result['p_value_two_sided']:.5g}; "
                   f"{result['n_rows']} country-years; {result['n_countries']} countries). {reason}.")
    card = (f"# Military burden and later {case['label']}\n\n{finding}\n\n"
            "One of four correlated SIPRI–UNDP descriptive cells, with a shared 0.01/4 family cutoff. "
            "War, security shocks, crises and GDP-denominator changes can drive both series. The local SIPRI extract has no retained cell-quality flags; UNDP component histories may be revised. "
            "A three-year lead does not identify a spending tradeoff. Exact replay requires the hash-matched local raw cache. "
            "Zero causal, policy, school, position or featured credit.\n")
    replication = ("#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\n"
                   "root = os.environ.get('IESET_RAW_ROOT')\n"
                   "if not root:\n    raise SystemExit('set IESET_RAW_ROOT to the matching local raw source cache')\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--source-root', root, '--verify']))\n")
    return {"manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "diagnostics.json": (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(),
            "result_card.md": card.encode(), "hypothesis.yaml": (ROOT / spec_path).read_bytes(),
            "replication.py": replication.encode()}


def summary_text(rows: list[tuple[str, str, int, int, str]], reg: str, lock_rev: str) -> str:
    lines = ["# SIPRI military burden and later UNDP components — results", "",
             f"Registration `{reg}`; source lock `{lock_rev}`. All four cells remain in the Bonferroni denominator.", "",
             "| Cell | Verdict | Rows | Countries | Gate summary |", "| --- | --- | ---: | ---: | --- |"]
    for ident, verdict, n, countries, reason in rows:
        lines.append(f"| `{ident}` | {verdict} | {n} | {countries} | {reason} |")
    lines += ["", "These are correlated, overlapping-window associations; they are not four independent replications. The military share can move because of the GDP denominator and security or war shocks, which may independently change every outcome. This does not identify a spending tradeoff or policy effect. SIPRI figures can be revised, and the local extract has no cell-quality flags. Zero causal, policy, school, position or featured credit.",
              "The exact local SIPRI and UNDP Parquet hashes match tracked fetch manifests. Raw SIPRI measurements are not copied into Git. See the preregistration for source URLs and the frozen failure rules.", ""]
    return "\n".join(lines)


def run(source_root: Path, verify: bool) -> None:
    reg, roster_hash, rows = registration_commit()
    lock_rev = lock_commit(source_root, reg, roster_hash)
    mmap, outcomes = values(source_root)
    first_case = next(iter(CASES.values()))
    first_diag = ROOT / paths(first_case)[2] / "diagnostics.json"
    run_utc = (json.loads(first_diag.read_text())["run_utc"] if verify
               else datetime.now(timezone.utc).isoformat(timespec="seconds"))
    summaries = []
    for key, case in CASES.items():
        frame, sample = frame_for(key, rows, mmap, outcomes)
        verdict, reason, result = fit_case(key, frame, sample)
        produced = artifacts(key, sample, verdict, reason, result, reg, lock_rev, roster_hash, run_utc)
        directory = ROOT / paths(case)[2]
        if verify:
            mismatches = [name for name, content in produced.items()
                          if not (directory / name).is_file() or (directory / name).read_bytes() != content]
            if mismatches:
                raise RuntimeError(f"{case['id']} exact replay mismatch: {mismatches}")
        else:
            directory.mkdir(parents=True, exist_ok=False)
            for name, content in produced.items():
                (directory / name).write_bytes(content)
        summaries.append((case["id"], verdict, sample["valid_rows"], sample["valid_countries"], reason))
    summary = summary_text(summaries, reg, lock_rev)
    path = ROOT / SUMMARY
    if verify:
        if not path.is_file() or path.read_text() != summary:
            raise RuntimeError("results summary exact replay mismatch")
        print("Exact replay passed:", summaries)
    else:
        path.write_text(summary)
        print(summaries)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--check-registration", action="store_true")
    group.add_argument("--make-lock", action="store_true")
    group.add_argument("--check-lock", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    if args.prepare or args.make_lock or args.check_lock or args.run or args.verify:
        if args.source_root is None:
            parser.error("--source-root is required")
    if args.prepare:
        prepare(args.source_root)
    elif args.check_registration:
        print("registration", registration_commit()[0])
    elif args.make_lock:
        make_lock(args.source_root)
    elif args.check_lock:
        reg, digest, _ = registration_commit()
        print("source lock", lock_commit(args.source_root, reg, digest))
    else:
        run(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
