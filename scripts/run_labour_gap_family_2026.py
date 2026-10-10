#!/usr/bin/env python3
"""Frozen prospective two-test labour-gap family; never open outcomes before the source lock."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import t as student_t
from statsmodels.formula.api import ols
from statsmodels.stats.sandwich_covariance import cov_cluster
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_labour_gap_family_2026.py"
PLAN = "engine/audits/labour_gap_family_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/labour_gap_family_2026_key_roster.csv"
LOCK = "data/pinned_evidence/labour_gap_family_2026.manifest.json"
FAMILY = "labour_gap_family_2026_10_10"
P_MAX = 0.005
ACCEPTABLE_OUTCOME_STATUSES = ("", "A")  # SDMX blank defaults to normal A
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": 0.01,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "Country and year fixed effects and temporal ordering do not identify causality.",
    "SOCX ALMP spending can react to unemployment and GDP denominator changes.",
    "FOR_STLS arrivals classify citizenship, while the unemployment gap classifies birthplace.",
    "Eurostat total-age REACH and COMPLET differ for Netherlands 2018 and Belgium 2013-14 in the pinned vintage.",
    "Only blank/A normal OECD observation statuses are accepted after source lock; other flags are excluded.",
    "The Bonferroni correction is local to these two prospectively registered tests, not the full IESET archive.",
    "No result receives causal, policy, school, position, or featured credit.",
]
ROSTER_SHA = "3e850df6b2cf9b90d566fb5acf271e9c7358024ea7f593dd7acce60441475e20"
START, END, MIN_YEARS = 2001, 2022, 5
TESTS = {
    "oecd_almp_migrant_unemployment_gap_forward_2026": {
        "sign": -1, "scale": 0.1, "sesoi_pp": 0.1,
        "min_rows": 300, "min_countries": 25,
        "min_material_rows": 80, "min_material_countries": 20,
        "material_cut": 0.05, "expected_keys": 641, "expected_countries": 35,
    },
    "eurostat_foreign_arrivals_migrant_unemployment_gap_forward_2026": {
        "sign": 1, "scale": 1.0, "sesoi_pp": 0.1,
        "min_rows": 220, "min_countries": 18,
        "min_material_rows": 60, "min_material_countries": 12,
        "material_cut": 1.0, "expected_keys": 463, "expected_countries": 26,
    },
}
ALMP_ID, ARRIVALS_ID = tuple(TESTS)
EURO_TO_ISO3 = dict(zip(
    "AT BE CH CZ DE DK ES EE FI FR UK EL HU IE IS IT LT LU LV NL NO PL PT SK SI SE".split(),
    "AUT BEL CHE CZE DEU DNK ESP EST FIN FRA GBR GRC HUN IRL ISL ITA LTU LUX LVA NLD NOR POL PRT SVK SVN SWE".split(),
))
if len(EURO_TO_ISO3) != 26:
    raise RuntimeError("frozen Eurostat country crosswalk changed")
SOURCES = {
    "almp": {
        "source": "oecd:DSD_SOCX@DF_SOCX_AGG",
        "path": "data/vintages/oecd/DSD_SOCX_DF_SOCX_AGG@2026-05-05T210247Z.parquet",
        "sha256": "93e7e29b24dc791baf22833ae5596b4a381a366ddd0d78499bf59f7b80786124",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
        "series_id": "DSD_SOCX@DF_SOCX_AGG",
    },
    "immigration": {
        "source": "eurostat:migr_imm1ctz",
        "path": "data/vintages/eurostat/migr_imm1ctz@2026-05-05T205902Z.parquet",
        "sha256": "b0b178278dd7d1ef68d4a03188e496b580d3e30b61f9fa21c7db13ed547bfeb1",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
        "series_id": "migr_imm1ctz",
    },
    "population": {
        "source": "eurostat:demo_pjan",
        "path": "data/vintages/eurostat/demo_pjan@2026-05-05T205848Z.parquet",
        "sha256": "c0910d085947e1c95da781ea3679f79909f41cab5c2cf5731db4e8fcf415f3e3",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
        "series_id": "demo_pjan",
    },
    "outcome": {
        "source": "oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_NUP_SEX,1.0",
        "path": "data/vintages/oecd/OECD.ELS.IMD_DSD_MIG_DF_MIG_NUP_SEX_1.0@2026-07-23T150503Z.parquet",
        "sha256": "ae1346956bb114faa54f84801d8c80153081069f1d3012ab8762d60f1c4c89a0",
        "manifest": "data/manifests/fetch_run_2026-07-23T150922Z.yaml",
        "manifest_sha256": "f8d2a682717c02832a2cf323fb5ea777139502e14987348859f3114042bece51",
        "series_id": "OECD.ELS.IMD,DSD_MIG@DF_MIG_NUP_SEX,1.0",
    },
}
ALMP_SELECTOR = {
    "FREQ": "A", "MEASURE": "SOCX", "UNIT_MEASURE": "PT_B1GQ",
    "EXPEND_SOURCE": "ES10", "SPENDING_TYPE": "_T",
    "PROGRAMME_TYPE": "TP60", "PRICE_BASE": "_Z",
}
IMM_SELECTOR = {"freq": "A", "citizen": "FOR_STLS", "age": "TOTAL", "unit": "NR", "sex": "T"}
POP_SELECTOR = {"freq": "A", "age": "TOTAL", "unit": "NR", "sex": "T"}
MIG_SELECTOR = {
    "FREQ": "A", "CITIZENSHIP": "_Z", "MEASURE": "UNE_RATE",
    "SEX": "_T", "EDUCATION_LEV": "_Z", "UNIT_MEASURE": "PT_LF_SUB",
}

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)

def first_addition(relative: str) -> str:
    revisions = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"no first-addition commit for {relative}")
    return revisions[-1]

def frozen_file(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file changed: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")

def spec_path(study: str) -> str:
    return f"hypotheses/labour/{study}.yaml"

def steelman_path(study: str) -> str:
    return f"hypotheses/steelman/{study}.md"

def registration_commit() -> str:
    files = [RUNNER, PLAN, ROSTER]
    for study in TESTS:
        files.extend([spec_path(study), steelman_path(study)])
    revisions = {first_addition(relative) for relative in files}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for relative in files:
        frozen_file(relative, revision)
    for study in TESTS:
        if git("ls-tree", "-r", "--name-only", revision, "--", f"engine/runs/{study}").strip():
            raise RuntimeError("registration commit already contained measured results")
    return revision

def validate_specs() -> None:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen key roster changed")
    roster = pd.read_csv(ROOT / ROSTER)
    if list(roster.columns) != ["study_id", "country_iso3", "year"] or roster.duplicated().any():
        raise RuntimeError("invalid key roster")
    for study, config in TESTS.items():
        spec = yaml.safe_load((ROOT / spec_path(study)).read_text())
        threshold = spec["falsification"]["threshold"]
        expected = {
            "family_id": FAMILY, "family_size": 2, "family_alpha": 0.01,
            "p_max_two_sided": P_MAX, "practical_effect_pp_min": config["sesoi_pp"],
            "exposure_scale": config["scale"], "min_valid_rows": config["min_rows"],
            "min_valid_countries": config["min_countries"],
            "min_years_per_country": MIN_YEARS,
            "min_material_rows": config["min_material_rows"],
            "min_material_countries": config["min_material_countries"],
            "material_exposure_change": config["material_cut"],
            "expected_key_rows": config["expected_keys"],
            "expected_key_countries": config["expected_countries"],
            "roster_sha256": ROSTER_SHA, "school_score_eligible": False,
            "school_score_credit": 0, "policy_score_eligible": False,
            "policy_score_credit": 0, "featured_eligible": False,
            "accepted_outcome_statuses": list(ACCEPTABLE_OUTCOME_STATUSES),
            "source_files": SOURCES,
        }
        if any(threshold.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"frozen threshold/source mismatch: {study}")
        if (spec.get("hypothesis_id") != study or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "associational"
                or spec.get("claim_direction") != ("-" if config["sign"] < 0 else "+")
                or spec.get("steelman") != steelman_path(study)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != [] or spec["sample"].get("period") != [START, END]):
            raise RuntimeError(f"registration structure mismatch: {study}")
        rows = roster.loc[roster.study_id.eq(study)]
        if len(rows) != config["expected_keys"] or rows.country_iso3.nunique() != config["expected_countries"]:
            raise RuntimeError(f"frozen roster size mismatch: {study}")
        if spec["sample"].get("countries") != sorted(rows.country_iso3.unique().tolist()):
            raise RuntimeError(f"frozen roster country list mismatch: {study}")

def check_sources(source_root: Path) -> None:
    for role, info in SOURCES.items():
        path = source_root / info["path"]
        manifest_path = source_root / info["manifest"]
        if not path.is_file() or sha256(path) != info["sha256"]:
            raise RuntimeError(f"missing or mismatched raw source: {role}")
        if not manifest_path.is_file() or sha256(manifest_path) != info["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        manifest = yaml.safe_load(manifest_path.read_text())
        entries = [e for e in manifest["entries"]
                   if e.get("parquet_path") == info["path"] and e.get("series_id") == info["series_id"]]
        if len(entries) != 1 or entries[0].get("sha256") != info["sha256"]:
            raise RuntimeError(f"manifest does not custody source: {role}")

def lock_payload(revision: str) -> dict:
    return {"family_id": FAMILY, "preregistration_commit": revision,
            "roster_sha256": ROSTER_SHA, "sources": SOURCES,
            "note": "Separate post-registration source lock before outcome values or null masks."}

def write_lock() -> None:
    revision = registration_commit()
    validate_specs()
    check_sources(ROOT)
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(lock_payload(revision), indent=2, sort_keys=True) + "\n")

def check_lock(revision: str) -> None:
    target = ROOT / LOCK
    if json.loads(target.read_text()) != lock_payload(revision):
        raise RuntimeError("source lock differs from frozen design")
    lock_revision = first_addition(LOCK)
    if lock_revision == revision:
        raise RuntimeError("source lock must be a later, separate commit")
    if subprocess.call(["git", "merge-base", "--is-ancestor", revision, lock_revision], cwd=ROOT) != 0:
        raise RuntimeError("source lock does not descend from registration commit")
    frozen_file(LOCK, lock_revision)
    for study in TESTS:
        if git("ls-tree", "-r", "--name-only", lock_revision, "--", f"engine/runs/{study}").strip():
            raise RuntimeError("source-lock commit already contained measured results")

def selected_frame(source_root: Path, role: str, selector: dict, keys: list[str],
                   include_value: bool) -> pd.DataFrame:
    columns = list(dict.fromkeys([*selector.keys(), *keys, *(["value"] if include_value else [])]))
    chunks = []
    parquet = pq.ParquetFile(source_root / SOURCES[role]["path"])
    for batch in parquet.iter_batches(batch_size=200_000, columns=columns):
        part = batch.to_pandas()
        mask = pd.Series(True, index=part.index)
        for key, value in selector.items():
            mask &= part[key].eq(value)
        if mask.any():
            chunks.append(part.loc[mask, [*keys, *(["value"] if include_value else [])]])
    if not chunks:
        raise RuntimeError(f"no selected rows for {role}")
    return pd.concat(chunks, ignore_index=True)

def migrant_frame(source_root: Path, with_values: bool) -> pd.DataFrame:
    selector = {**MIG_SELECTOR}
    columns = ["REF_AREA", "period", "BIRTH_PLACE"] + (["OBS_STATUS"] if with_values else [])
    frame = selected_frame(source_root, "outcome", selector, columns, with_values)
    frame = frame.loc[frame.BIRTH_PLACE.isin(["FB", "NB"]) & frame.REF_AREA.ne("EU27_2020")].copy()
    frame["year"] = pd.to_numeric(frame.period, errors="raise").astype(int)
    if frame.duplicated(["REF_AREA", "year", "BIRTH_PLACE"]).any():
        raise RuntimeError("duplicate OECD birth-place unemployment keys")
    frame = frame.rename(columns={"REF_AREA": "country_iso3"})
    if not with_values:
        counts = frame.groupby(["country_iso3", "year"]).BIRTH_PLACE.nunique()
        keys = counts[counts.eq(2)].reset_index()[["country_iso3", "year"]]
        return keys
    status = frame.OBS_STATUS.fillna("").astype(str).str.strip()
    frame = frame.loc[status.isin(ACCEPTABLE_OUTCOME_STATUSES)].copy()
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    wide = frame.pivot(index=["country_iso3", "year"], columns="BIRTH_PLACE", values="value").reset_index()
    wide.columns.name = None
    for birthplace in ("FB", "NB"):
        if birthplace not in wide.columns:
            wide[birthplace] = np.nan
    wide = wide.loc[wide.FB.between(0, 100) & wide.NB.between(0, 100)].copy()
    wide["gap"] = wide.FB - wide.NB
    return wide[["country_iso3", "year", "gap"]]

def almp_exposure(source_root: Path) -> pd.DataFrame:
    frame = selected_frame(source_root, "almp", ALMP_SELECTOR, ["REF_AREA", "period"], True)
    frame = frame.loc[frame.REF_AREA.ne("OECD")].copy()
    frame["year"] = pd.to_numeric(frame.period, errors="raise").astype(int)
    if frame.duplicated(["REF_AREA", "year"]).any():
        raise RuntimeError("duplicate OECD SOCX public TP60 keys")
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    frame = frame.loc[frame.value.between(0, 10)].copy()
    frame = frame.rename(columns={"REF_AREA": "country_iso3"})
    current = frame[["country_iso3", "year", "value"]]
    previous = current.rename(columns={"value": "previous"}).copy()
    previous["year"] += 1
    paired = current.merge(previous, on=["country_iso3", "year"], validate="one_to_one")
    paired["treatment"] = paired.value - paired.previous
    return paired[["country_iso3", "year", "treatment"]]

def arrivals_exposure(source_root: Path, age_definition: str) -> pd.DataFrame:
    if age_definition not in {"REACH", "COMPLET"}:
        raise ValueError(age_definition)
    arrivals = selected_frame(
        source_root, "immigration", {**IMM_SELECTOR, "agedef": age_definition},
        ["geo_code", "period"], True,
    )
    population = selected_frame(source_root, "population", POP_SELECTOR,
                                ["geo_code", "period"], True)
    for frame, label in [(arrivals, "immigration"), (population, "population")]:
        frame["year"] = pd.to_numeric(frame.period, errors="raise").astype(int)
        if frame.duplicated(["geo_code", "year"]).any():
            raise RuntimeError(f"duplicate Eurostat country-year keys: {label}")
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    arrivals = arrivals.loc[arrivals.geo_code.isin(EURO_TO_ISO3)].copy()
    population = population.loc[population.geo_code.isin(EURO_TO_ISO3)].copy()
    merged = arrivals[["geo_code", "year", "value"]].merge(
        population[["geo_code", "year", "value"]].rename(columns={"value": "population"}),
        on=["geo_code", "year"], validate="one_to_one",
    )
    merged = merged.loc[np.isfinite(merged.value) & np.isfinite(merged.population)
                        & merged.value.ge(0) & merged.population.gt(0)].copy()
    merged["rate"] = 1000 * merged.value / merged.population
    current = merged[["geo_code", "year", "rate"]]
    previous = current.rename(columns={"rate": "previous"}).copy()
    previous["year"] += 1
    paired = current.merge(previous, on=["geo_code", "year"], validate="one_to_one")
    paired["country_iso3"] = paired.geo_code.map(EURO_TO_ISO3)
    paired["treatment"] = paired.rate - paired.previous
    return paired[["country_iso3", "year", "treatment"]]

def roster_frame(study: str) -> pd.DataFrame:
    roster = pd.read_csv(ROOT / ROSTER)
    part = roster.loc[roster.study_id.eq(study), ["country_iso3", "year"]].copy()
    part["year"] = part.year.astype(int)
    return part.sort_values(["country_iso3", "year"]).reset_index(drop=True)

def key_panel(source_root: Path, study: str, age_definition: str = "REACH",
              require_primary_roster: bool = True) -> pd.DataFrame:
    exposure = (almp_exposure(source_root) if study == ALMP_ID
                else arrivals_exposure(source_root, age_definition))
    gap_keys = migrant_frame(source_root, False)
    future = gap_keys.copy()
    future["year"] -= 1
    panel = exposure.merge(gap_keys, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.loc[panel.year.between(START, END)].copy()
    if study == ARRIVALS_ID and age_definition == "COMPLET":
        panel = panel.merge(roster_frame(study), on=["country_iso3", "year"], validate="one_to_one")
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts.ge(MIN_YEARS)].index)]
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    if require_primary_roster:
        actual = panel[["country_iso3", "year"]]
        expected = roster_frame(study)
        if not actual.equals(expected):
            raise RuntimeError(f"key-only roster drift: {study}")
    return panel

def preflight(source_root: Path) -> dict:
    report = {}
    for study, config in TESTS.items():
        panel = key_panel(source_root, study)
        material = panel.treatment.abs().ge(config["material_cut"])
        report[study] = {
            "key_rows": int(len(panel)),
            "key_countries": int(panel.country_iso3.nunique()),
            "material_rows": int(material.sum()),
            "material_countries": int(panel.loc[material, "country_iso3"].nunique()),
            "values_read": "treatment-only",
            "outcome_values_read": False,
            "outcome_null_masks_read": False,
        }
        if (len(panel) != config["expected_keys"]
                or panel.country_iso3.nunique() != config["expected_countries"]
                or material.sum() < config["min_material_rows"]
                or panel.loc[material, "country_iso3"].nunique() < config["min_material_countries"]):
            raise RuntimeError(f"frozen key and treatment-variation preflight failed: {study}")
    alt = key_panel(source_root, ARRIVALS_ID, "COMPLET", False)
    report["COMPLET_sensitivity"] = {
        "key_rows": int(len(alt)), "key_countries": int(alt.country_iso3.nunique()),
        "outcome_values_read": False, "outcome_null_masks_read": False,
    }
    return report

def measured_panel(source_root: Path, study: str, age_definition: str = "REACH") -> pd.DataFrame:
    # Outcome values are first read here; the caller must already have verified
    # registration ancestry, exact sources, the later source lock, and preflight.
    candidate = key_panel(source_root, study, age_definition,
                          require_primary_roster=(study == ALMP_ID or age_definition == "REACH"))
    outcome = migrant_frame(source_root, True)
    baseline = outcome.rename(columns={"gap": "baseline"})
    future = outcome.rename(columns={"gap": "future"}).copy()
    future["year"] -= 1
    panel = candidate.merge(baseline, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    panel["outcome"] = panel.future - panel.baseline
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["treatment", "baseline", "future", "outcome"])
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts.ge(MIN_YEARS)].index)]
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)

def gate(frame: pd.DataFrame, study: str) -> dict:
    config = TESTS[study]
    material = frame.treatment.abs().ge(config["material_cut"])
    result = {
        "rows": int(len(frame)), "countries": int(frame.country_iso3.nunique()),
        "material_rows": int(material.sum()),
        "material_countries": int(frame.loc[material, "country_iso3"].nunique()),
        "minimum_years_per_country": MIN_YEARS,
    }
    result["passed"] = bool(
        result["rows"] >= config["min_rows"]
        and result["countries"] >= config["min_countries"]
        and result["material_rows"] >= config["min_material_rows"]
        and result["material_countries"] >= config["min_material_countries"])
    return result

def estimate(frame: pd.DataFrame, *, baseline_adjusted: bool = False) -> dict | None:
    countries = frame.country_iso3.nunique()
    if len(frame) < 50 or countries < 10:
        return None
    formula = ("outcome ~ treatment + baseline + C(country_iso3) + C(year)"
               if baseline_adjusted else
               "outcome ~ treatment + C(country_iso3) + C(year)")
    fit = ols(formula, data=frame).fit()
    if fit.model.rank != fit.model.exog.shape[1]:
        return None
    cov = cov_cluster(fit, frame.country_iso3, use_correction=True)
    location = fit.model.exog_names.index("treatment")
    se = float(np.sqrt(cov[location, location]))
    beta = float(fit.params["treatment"])
    if not math.isfinite(se) or se <= 0 or not math.isfinite(beta):
        return None
    degrees = int(countries - 1)
    p = float(2 * student_t.sf(abs(beta / se), df=degrees))
    critical = float(student_t.ppf(1 - P_MAX / 2, df=degrees))
    fields = [beta, se, p, critical, float(fit.rsquared)]
    if not all(math.isfinite(value) for value in fields):
        return None
    return {
        "coefficient": beta, "std_error": se, "p_value": p,
        "ci99_5_low": beta - critical * se,
        "ci99_5_high": beta + critical * se,
        "n_obs": int(len(frame)), "n_countries": int(countries),
        "cluster_df": degrees, "r_squared": float(fit.rsquared),
        "method": ("OLS country+year FE, baseline gap diagnostic, CR1 country cluster, t(G-1)"
                   if baseline_adjusted else
                   "OLS change-only country+year FE, CR1 country cluster, t(G-1)"),
    }

def directional_pass(result: dict | None, study: str, sign: int) -> bool:
    if result is None:
        return False
    config = TESTS[study]
    return (result["p_value"] <= P_MAX
            and sign * result["coefficient"] * config["scale"] >= config["sesoi_pp"])

def study_result(source_root: Path, study: str) -> dict:
    frame = measured_panel(source_root, study)
    primary_gate = gate(frame, study)
    primary = estimate(frame) if primary_gate["passed"] else None
    alternate_gate, alternate = None, None
    if study == ARRIVALS_ID:
        alternate_frame = measured_panel(source_root, study, "COMPLET")
        alternate_gate = gate(alternate_frame, study)
        alternate = estimate(alternate_frame) if alternate_gate["passed"] else None
    config = TESTS[study]
    if not primary_gate["passed"] or (primary_gate["passed"] and primary is None):
        verdict = "INCONCLUSIVE"
        reason = "complete-case/material-variation floor or fixed-effect identification failed"
    elif study == ARRIVALS_ID and (not alternate_gate["passed"] or alternate is None):
        verdict = "INCONCLUSIVE"
        reason = "age-definition sensitivity floor or identification failed"
    elif directional_pass(primary, study, config["sign"]) and (
            study == ALMP_ID or directional_pass(alternate, study, config["sign"])):
        verdict = "SUPPORTED"
        reason = "registered sign, family cutoff, and practical effect cleared"
    elif directional_pass(primary, study, -config["sign"]) and (
            study == ALMP_ID or directional_pass(alternate, study, -config["sign"])):
        verdict = "REFUTED"
        reason = "opposite sign, family cutoff, and practical effect cleared"
    else:
        verdict = "PARTIAL"
        reason = "directional family cutoff, practical effect, or age sensitivity did not all clear"
    sensitivities = {}
    sensitivities["baseline_adjusted"] = {
        "rows": int(len(frame)), "countries": int(frame.country_iso3.nunique()),
        "estimate": estimate(frame, baseline_adjusted=True) if primary_gate["passed"] else None,
    }
    for label, mask in (
        ("exclude_2022", frame.year.ne(2022)),
        ("through_2019", frame.year.le(2019)),
    ):
        part = frame.loc[mask].copy()
        sensitivities[label] = {"rows": int(len(part)), "countries": int(part.country_iso3.nunique()),
                                "estimate": estimate(part)}
    return {
        "study_id": study, "verdict": verdict, "reason": reason,
        "primary_gate": primary_gate, "primary": primary,
        "COMPLET_gate": alternate_gate, "COMPLET_sensitivity": alternate,
        "time_sensitivities": sensitivities,
        "family_p_max_two_sided": P_MAX,
        "practical_effect_pp_min": config["sesoi_pp"],
        "exposure_scale": config["scale"],
        "zero_credit": {"causal": True, "policy": True, "school": True, "featured": True},
    }

def result_paths(study: str) -> Path:
    return ROOT / "engine" / "runs" / study

def artifacts(result: dict, prereg_revision: str, lock_revision: str, stamp: str) -> dict:
    study = result["study_id"]
    config = TESTS[study]
    common = {
        "hypothesis_id": study, "family_id": FAMILY, "study_id": study,
        "verdict": result["verdict"], "runner": RUNNER,
        "preregistration_commit": prereg_revision,
        "source_lock_commit": lock_revision,
        "source_lock": LOCK, "roster_sha256": ROSTER_SHA,
        "run_utc": stamp, "sources": SOURCES,
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        **common, **result, "verdict_label": result["verdict"],
        "verdict_reason": result["reason"], "template": "panel_fe",
        "preflight": result["primary_gate"],
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values()),
                        "accepted_outcome_statuses": list(ACCEPTABLE_OUTCOME_STATUSES)},
    }
    manifest = {
        **common, "status": result["verdict"], "vintages": list(SOURCES.values()),
        "derived_panel": result["primary_gate"],
        "method": "change-only country/year fixed-effects OLS; country CR1 cluster",
        "outcome": "foreign-born minus native-born unemployment-rate gap change t to t+1",
        "treatment": ("public TP60 ALMP spending percent-GDP change t-1 to t"
                      if study == ALMP_ID else
                      "FOR_STLS arrivals per 1000 1-January residents change t-1 to t"),
        "family_size": 2, "p_max_two_sided": P_MAX,
        "school_score_eligible": False, "policy_score_eligible": False,
        "featured_eligible": False,
    }
    packet = {
        **common, "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": study, "path": spec_path(study), "topic": "labour"},
        "preregistration": {"spec_commit": prereg_revision,
                            "source_lock_commit": lock_revision, "family_id": FAMILY,
                            "family_size": 2, "key_roster": ROSTER,
                            "key_roster_sha256": ROSTER_SHA,
                            "steelman": steelman_path(study)},
        "reproduction": {"runner": RUNNER, "run_dir": str(result_paths(study).relative_to(ROOT)),
                         "command": f"python3 {RUNNER} --verify {study}"},
        "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                    "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": result["primary_gate"]},
        "results": {"primary": result["primary"],
                    "COMPLET": result["COMPLET_sensitivity"],
                    "sensitivities": result["time_sensitivities"]},
        "evidence_type": "associational",
        "claim_scope": "prospective country-panel descriptive calibration",
        "primary_gate": result["primary_gate"],
        "coefficient": result["primary"],
        "practical_effect_pp_min": config["sesoi_pp"],
        "exposure_scale": config["scale"],
        "age_sensitivity_required_for_arrivals": study == ARRIVALS_ID,
        "age_sensitivity": result["COMPLET_sensitivity"],
        "causal_credit": 0, "policy_credit": 0,
        "school_score_credit": 0, "featured_credit": 0,
    }
    measured = result["primary"]
    beta_line = ("No identified coefficient passed the frozen sample gate."
                 if measured is None else
                 f"Primary coefficient {measured['coefficient']:.6g} gap points per treatment unit; "
                 f"two-sided p={measured['p_value']:.6g}; "
                 f"99.5% CI [{measured['ci99_5_low']:.6g}, {measured['ci99_5_high']:.6g}].")
    card = (
        f"# {study}\n\n"
        f"Verdict: **{result['verdict']}**. {result['reason']}.\n\n"
        f"{beta_line}\n\n"
        f"Complete-case rows/countries: {result['primary_gate']['rows']}/"
        f"{result['primary_gate']['countries']}. "
        f"Material exposure changes: {result['primary_gate']['material_rows']} rows in "
        f"{result['primary_gate']['material_countries']} countries.\n\n"
        "Two fixed tests use family alpha 0.01 and a two-sided Bonferroni cutoff of 0.005 each. "
        "A directional verdict also requires at least 0.1 percentage point "
        "of gap change at the prespecified exposure scale. "
        + ("The COMPLET age convention must independently clear the same directional "
           "cutoff and practical threshold. " if study == ARRIVALS_ID else "")
        + "Baseline-gap adjustment, excluding 2022, and restricting through 2019 are reported sensitivity checks; "
          "they cannot create a primary verdict.\n\n"
        "This is a country-level association. Immigration flows use citizenship, "
        "whereas the unemployment gap uses birthplace. ALMP spending may respond "
        "to unemployment and GDP movements. No causal, policy-effect, school, "
        "position, or featured credit follows.\n"
    )
    chart = {
        "study_id": study, "verdict": result["verdict"], "primary": measured,
        "COMPLET": result["COMPLET_sensitivity"], "time_sensitivities": result["time_sensitivities"],
        "correction": CORRECTION,
    }
    rows = []
    for name, estimate_row in (
        ("primary", measured),
        ("COMPLET", result["COMPLET_sensitivity"]),
        ("baseline_adjusted", result["time_sensitivities"]["baseline_adjusted"]["estimate"]),
        ("exclude_2022", result["time_sensitivities"]["exclude_2022"]["estimate"]),
        ("through_2019", result["time_sensitivities"]["through_2019"]["estimate"]),
    ):
        if estimate_row is not None:
            rows.append({"term": name, **estimate_row})
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER}'), "
        f"'--verify', '{study}'], cwd=root))\n"
    )
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "chart": chart, "rows": rows, "wrapper": wrapper}

def write_artifacts(study: str, payload: dict) -> None:
    folder = result_paths(study)
    if folder.exists():
        raise FileExistsError(folder)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / spec_path(study)).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2, sort_keys=True) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2, sort_keys=True) + "\n")
    (folder / "replication.py").write_text(payload["wrapper"])
    columns = ["term", "coefficient", "std_error", "p_value", "ci99_5_low", "ci99_5_high",
               "n_obs", "n_countries", "cluster_df", "r_squared", "method"]
    pd.DataFrame(payload["rows"], columns=columns).to_parquet(folder / "coefficients.parquet", index=False)

def comparable(actual, expected, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: fields differ")
        for key, value in expected.items():
            comparable(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: lengths differ")
        for index, value in enumerate(expected):
            comparable(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(
                float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numerical mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: mismatch")

def verify_one(study: str, prereg_revision: str, lock_revision: str) -> None:
    folder = result_paths(study)
    stored = json.loads((folder / "diagnostics.json").read_text())
    result = study_result(ROOT, study)
    expected = artifacts(result, prereg_revision, lock_revision, stored["run_utc"])
    comparable(stored, expected["diagnostics"], "diagnostics")
    comparable(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], "manifest")
    comparable(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], "packet")
    comparable(json.loads((folder / "chart_data.json").read_text()), expected["chart"], "chart")
    comparable(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
               expected["rows"], "coefficients")
    for name, contents in (
        ("hypothesis.yaml", (ROOT / spec_path(study)).read_bytes()),
        ("result_card.md", expected["card"].encode()),
        ("replication.py", expected["wrapper"].encode()),
    ):
        if (folder / name).read_bytes() != contents:
            raise AssertionError(f"{study}: {name} differs from exact replay")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate-specs", action="store_true")
    actions.add_argument("--check-sources", action="store_true")
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--write-source-lock", action="store_true")
    actions.add_argument("--run", action="store_true")
    actions.add_argument("--verify", nargs="?", const="all", choices=[*TESTS, "all"])
    parser.add_argument("--source-root", type=Path,
                        help="only for staged read-only preflight/check-sources")
    args = parser.parse_args()
    if args.source_root is not None and not (args.preflight or args.check_sources):
        parser.error("--source-root is restricted to read-only preflight/check-sources")
    validate_specs()
    if args.validate_specs:
        print("frozen two-study specs and roster agree")
        return 0
    source_root = args.source_root or ROOT
    check_sources(source_root)
    if args.check_sources:
        print("four exact raw hashes and committed fetch manifests agree")
        return 0
    if args.preflight and args.source_root is not None:
        print(json.dumps(preflight(source_root), indent=2, sort_keys=True))
        return 0
    prereg_revision = registration_commit()
    if args.write_source_lock:
        write_lock()
        print(f"wrote {LOCK}; commit separately before opening outcome values")
        return 0
    check_lock(prereg_revision)
    lock_revision = first_addition(LOCK)
    check = preflight(ROOT)
    if args.preflight:
        print(json.dumps(check, indent=2, sort_keys=True))
        return 0
    if args.verify is not None:
        selected = TESTS if args.verify == "all" else [args.verify]
        for study in selected:
            verify_one(study, prereg_revision, lock_revision)
            print("verified exact frozen-model replay", study)
        return 0
    if any(result_paths(study).exists() for study in TESTS):
        raise FileExistsError("family result folder already exists")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payloads = {
        study: artifacts(study_result(ROOT, study), prereg_revision, lock_revision, stamp)
        for study in TESTS
    }
    for study, payload in payloads.items():
        write_artifacts(study, payload)
        print(study, payload["diagnostics"]["verdict"], payload["diagnostics"]["primary_gate"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
