#!/usr/bin/env python3
"""Prospective OECD housing overburden → Eurostat fertility calibration.

--register/--preflight read housing values/status and fertility dimension keys
only. Fertility values and null masks are first read by --run/--verify after
separate committed preregistration and source-lock steps.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pycountry
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
HID = "oecd_housing_overburden_fertility_forward_2026"
FAMILY = "oecd_housing_eurostat_fertility_forward_2026_10_10"
RUNNER = "scripts/run_oecd_housing_eurostat_fertility_forward_2026.py"
SPEC = f"hypotheses/housing/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PREREG = "engine/audits/oecd_housing_eurostat_fertility_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/oecd_housing_eurostat_fertility_forward_2026_key_roster.csv"
ROSTER_SHA = "22e167449e554362a42d4126c6346d69a54cd833819d029696e7645e5bdef9b1"
LOCK = "data/pinned_evidence/oecd_housing_eurostat_fertility_forward_2026.manifest.json"
SUMMARY = "engine/audits/oecd_housing_eurostat_fertility_results_2026-10-10.md"
RUN_DIR = f"engine/runs/{HID}"
SOURCES = {
    "housing": {"publisher": "oecd", "series_id": "OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0",
        "path": "data/vintages/oecd/OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0@2026-07-23T150432Z.parquet",
        "sha256": "ac7581cb015748d97a21d4feadd08a3afb16cb1d5912af9e0997913ce4db65db",
        "manifest": "data/manifests/fetch_run_2026-07-23T150922Z.yaml",
        "manifest_sha256": "f8d2a682717c02832a2cf323fb5ea777139502e14987348859f3114042bece51"},
    "fertility": {"publisher": "eurostat", "series_id": "demo_find",
        "path": "data/vintages/eurostat/demo_find@2026-04-30T115530Z.parquet",
        "sha256": "4db9d291092c0c146aebaa9f3e143b9f9a7a8741f7fc41886e31941aa412c039",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
}
ANCHORS = tuple(range(2013, 2020))
CANDIDATE_ROWS, CANDIDATE_COUNTRIES = 118, 24
MATERIAL_ROWS, MATERIAL_COUNTRIES = 63, 23
MIN_ROWS, MIN_COUNTRIES = 95, 20
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 50, 18
MATERIAL_CHANGE = 2.0
ALPHA, MIN_ABS_BETA = 0.01, 0.003
MAX_TOP_TWO_RESIDUAL_SHARE, MAX_TOP_COUNTRY_SHARE = 0.30, 0.25
MIN_SENSITIVITY_ROWS, MIN_SENSITIVITY_COUNTRIES = 45, 14
ISO_TO_EU = {country.alpha_3: country.alpha_2 for country in pycountry.countries}
ISO_TO_EU.update(GRC="EL", GBR="UK")
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": ALPHA, "family_p_max": ALPHA,
    "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "OECD How's Life 3_3 is the share of the low-income population above a 40% housing-cost burden, not an average price or all-household burden. The pinned 1.1 file labels the unit PT_POP.",
    "Eurostat demo_find total fertility is a period synthetic births-per-woman rate, not completed family size or births to the low-income population.",
    "The OECD housing series comes from surveys and can have time-series breaks; four consecutive normal-status years are required for each exposure window.",
    "Annual three-year windows overlap across anchors. Country clustering addresses within-country dependence imperfectly; the 2013–2016 pre-pandemic subset is frozen as a sign-sensitivity check.",
    "Income, family policy, demographic composition, migration, and housing supply can jointly move burden and fertility. Timing and fixed effects do not identify a causal or policy effect.",
    "Earlier IESET housing and fertility studies make the research question archive-selected; local p≤0.01 does not correct the full archive search.",
    "No causal, policy, school-score, position, or featured credit is permitted.",
]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    history = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not history:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return history[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def check_sources() -> dict[str, dict[str, Any]]:
    verified = {}
    for role, pin in SOURCES.items():
        raw, manifest = ROOT / pin["path"], ROOT / pin["manifest"]
        if not raw.is_file() or sha(raw) != pin["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned raw vintage: {role}")
        if not manifest.is_file() or sha(manifest) != pin["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("publisher") == pin["publisher"]
            and entry.get("series_id") == pin["series_id"] and entry.get("parquet_path") == pin["path"]
            and entry.get("sha256") == pin["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest lacks exact vintage: {role}")
        verified[role] = {**pin, "source_url": matches[0].get("source_url"),
            "methodology_url": matches[0].get("methodology_url"),
            "license": matches[0].get("license"), "fetch_utc": matches[0].get("fetch_utc")}
    return verified


def housing_values() -> pd.DataFrame:
    cols = ["REF_AREA", "MEASURE", "UNIT_MEASURE", "AGE", "SEX", "EDUCATION_LEV",
        "DOMAIN", "period", "value", "OBS_STATUS"]
    frame = pd.read_parquet(ROOT / SOURCES["housing"]["path"], columns=cols)
    mask = ((frame.MEASURE == "3_3") & (frame.UNIT_MEASURE == "PT_POP")
        & (frame.AGE == "_T") & (frame.SEX == "_T")
        & (frame.EDUCATION_LEV == "_T") & (frame.DOMAIN == "HSL_3"))
    frame = frame.loc[mask, ["REF_AREA", "period", "value", "OBS_STATUS"]].copy()
    frame["period"] = frame.period.astype(int)
    if frame.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicated housing country-year dimension")
    return frame.set_index(["REF_AREA", "period"]).sort_index()


def fertility_keys() -> set[tuple[str, int]]:
    # Read physical dimension keys only; never request value or a null mask here.
    cols = ["freq", "indic_de", "geo_code", "period"]
    frame = pd.read_parquet(ROOT / SOURCES["fertility"]["path"], columns=cols)
    frame = frame.loc[(frame.freq == "A") & (frame.indic_de == "TOTFERRT"),
        ["geo_code", "period"]].copy()
    frame["period"] = frame.period.astype(int)
    if frame.duplicated(["geo_code", "period"]).any():
        raise RuntimeError("duplicated fertility geography-year key")
    return set(frame.itertuples(index=False, name=None))


def expected_roster() -> list[tuple[str, str, int]]:
    housing, keys = housing_values(), fertility_keys()
    rows = []
    countries = sorted(set(housing.index.get_level_values(0)))
    for country in countries:
        geo = ISO_TO_EU.get(country)
        if geo is None:
            continue
        for anchor in ANCHORS:
            if (geo, anchor) not in keys or (geo, anchor + 3) not in keys:
                continue
            points = [(country, year) for year in range(anchor - 3, anchor + 1)]
            if any(point not in housing.index for point in points):
                continue
            observations = [housing.loc[point] for point in points]
            if any(observation.OBS_STATUS != "A" or not math.isfinite(float(observation.value))
                or not 0 <= float(observation.value) <= 100 for observation in observations):
                continue
            rows.append((country, geo, anchor))
    counts = Counter(country for country, _, _ in rows)
    return [row for row in rows if counts[row[0]] >= 2]


def roster_bytes(rows: list[tuple[str, str, int]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["country_iso3", "eurostat_geo", "anchor_year"])
    writer.writerows(rows)
    return buffer.getvalue().encode()


def load_roster() -> list[tuple[str, str, int]]:
    raw = (ROOT / ROSTER).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROSTER_SHA:
        raise RuntimeError("key roster SHA mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    rows = [(r["country_iso3"], r["eurostat_geo"], int(r["anchor_year"])) for r in records]
    if (raw != roster_bytes(rows) or rows != expected_roster()
        or len(rows) != CANDIDATE_ROWS or len({r[0] for r in rows}) != CANDIDATE_COUNTRIES):
        raise RuntimeError("frozen roster differs from housing values and fertility keys")
    return rows


def preflight(rows: list[tuple[str, str, int]]) -> dict[str, Any]:
    housing = housing_values()
    changes = [(country, float(housing.loc[country, anchor].value)
        - float(housing.loc[country, anchor - 3].value)) for country, _, anchor in rows]
    material = [(country, x) for country, x in changes if abs(x) >= MATERIAL_CHANGE]
    if (len(rows) != CANDIDATE_ROWS or len({r[0] for r in rows}) != CANDIDATE_COUNTRIES
        or len(material) != MATERIAL_ROWS
        or len({country for country, _ in material}) != MATERIAL_COUNTRIES):
        raise RuntimeError("treatment-only envelope differs from frozen counts")
    return {"key_only_rows": len(rows), "key_only_countries": CANDIDATE_COUNTRIES,
        "material_exposure_rows": len(material), "material_exposure_countries": MATERIAL_COUNTRIES,
        "anchors": list(ANCHORS), "outcome_values_opened": False,
        "outcome_null_masks_opened": False}


def threshold() -> dict[str, Any]:
    return {"family_id": FAMILY, "family_size": 1, "family_alpha": ALPHA,
        "p_max_two_sided": ALPHA, "expected_beta_sign": "-",
        "meaningful_beta_min_abs": MIN_ABS_BETA,
        "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_COUNTRIES,
        "min_material_change_rows": MIN_MATERIAL_ROWS,
        "min_material_change_countries": MIN_MATERIAL_COUNTRIES,
        "material_housing_change_min_abs": MATERIAL_CHANGE,
        "min_complete_anchors_per_country": 2,
        "max_top_two_residual_x_share": MAX_TOP_TWO_RESIDUAL_SHARE,
        "max_top_country_residual_x_share": MAX_TOP_COUNTRY_SHARE,
        "prepandemic_sensitivity_through_anchor": 2016,
        "min_sensitivity_rows": MIN_SENSITIVITY_ROWS,
        "min_sensitivity_countries": MIN_SENSITIVITY_COUNTRIES,
        "expected_key_rows": CANDIDATE_ROWS,
        "expected_key_countries": CANDIDATE_COUNTRIES,
        "roster_sha256": ROSTER_SHA,
        "source_files": {role: {field: pin[field] for field in
            ("path", "sha256", "manifest", "manifest_sha256")}
            for role, pin in SOURCES.items()}, **CORRECTION}


def spec_payload(rows: list[tuple[str, str, int]]) -> dict[str, Any]:
    countries = sorted({country for country, _, _ in rows})
    return {"hypothesis_id": HID, "version": 1, "status": "pre_registered",
        "topic": "housing", "claim_direction": "-",
        "claim": "Within the fixed OECD–Eurostat country panel, a larger prior three-year increase in low-income housing cost overburden predicts a larger fall in the total fertility rate during the following three years.",
        "methodology_note": "One-test prospective descriptive calibration registered from housing exposure values and Eurostat fertility country-year keys only; no selected fertility value, null mask, or fitted result was opened before the separate source lock. Exact design in " + PREREG + ".",
        "evidence_type": "associational",
        "sample": {"countries": countries, "period": [2010, 2022],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "Use only the exact 118-row committed key roster with 2013–2019 anchors; no countries, windows, or alternate outcome vintages may be substituted.",
                "OECD How's Life 3_3, PT_POP, all ages/sex/education total, housing domain only. Require normal OBS_STATUS=A, finite [0,100] values in all four years t−3 through t and at least two eligible anchors per country.",
                "Eurostat demo_find annual TOTFERRT exact year t and t+3 keys only; after the source-lock commit retain finite values [0.5,10] births per woman and at least two complete anchors per country. No nearest-year join or interpolation.",
                "The completed sample and every gate are fixed independently of observed fertility values; exclude no observation based on outcome sign or fitted effect." ]},
        "variables": {"treatment": [{"name": "three_year_low_income_housing_overburden_change_pp",
            "source": "oecd:OECD.WISE.WDP,DSD_HSL@DF_HSL_CWB,1.1",
            "transformation": "HSL 3_3 PT_POP at t minus t−3, percentage points.",
            "notes": "Population in the bottom 40% of income above the 40% housing-cost-to-disposable-income threshold; not a policy treatment."}],
            "outcome": [{"name": "next_three_year_total_fertility_change",
                "source": "eurostat:demo_find",
                "transformation": "TOTFERRT at t+3 minus TOTFERRT at t, births per woman.",
                "notes": "Period synthetic total fertility for all women; not completed family size or fertility among low-income households."}],
            "controls": [{"name": "baseline_housing_overburden",
                "source": "oecd:OECD.WISE.WDP,DSD_HSL@DF_HSL_CWB,1.1",
                "transformation": "HSL 3_3 level at t−3, percentage of the bottom-40 population."},
                {"name": "baseline_total_fertility",
                "source": "eurostat:demo_find",
                "transformation": "TOTFERRT level at t, births per woman."}]},
        "estimator": {"template": "panel_fe", "fixed_effects": ["country", "anchor_year"],
            "clustering": "country",
            "notes": "OLS of later three-year total-fertility change on prior three-year housing-overburden change, baseline housing burden and fertility, country and anchor-year effects. Country-cluster CR1 and two-sided Student t(G−1). Overlapping annual windows are retained as fixed; a 2013–2016 pre-pandemic subset is a sign-sensitivity check."},
        "falsification": {"test": FAMILY,
            "rule": "INCONCLUSIVE if source/chronology, complete-case (95 rows/20 countries), material-change (50 rows/18 countries), two-complete-anchor, residualized-treatment concentration (largest two rows ≤30%; largest country ≤25%), full-rank, or finite-positive clustered-uncertainty gates fail. Otherwise SUPPORTED only if beta ≤−0.003 births per woman per +1 burden point, two-sided p≤0.01, and the 2013–2016 sensitivity beta is also negative with at least 45 rows/14 countries. REFUTED symmetrically for beta ≥+0.003 and positive sensitivity. All other estimable results are PARTIAL. Every verdict has only descriptive calibration status.",
            "threshold": threshold()},
        "prior_confidence": 0.35,
        "disclosure": "National low-income housing burden and national fertility can co-move under income, migration, family-policy and housing-market shocks. These ecological lags and controls cannot identify causation. Earlier IESET housing/fertility cases make this archive-selected; the local p≤0.01 rule is not an archive-wide multiplicity correction. Zero causal, policy, school-score, position, or featured credit.",
        "steelman": STEELMAN,
        "scope": {"period": [2010, 2022], "countries": countries,
            "outcome_dim": ["demographics_migration"], "policy_family": [],
            "treatment_tags": ["housing_cost_overburden", "fertility_transition"]},
        "covers_claims": [], "linked_hypotheses": [], "linked_conditions": []}


def register() -> None:
    selected = check_sources()
    rows = expected_roster()
    raw = roster_bytes(rows)
    if hashlib.sha256(raw).hexdigest() != ROSTER_SHA:
        raise RuntimeError("unexpected treatment/key-only roster")
    blind = preflight(rows)
    if any((ROOT / relative).exists() for relative in (SPEC, STEELMAN, PREREG, ROSTER, LOCK, SUMMARY)):
        raise FileExistsError("prospective artifacts already exist")
    (ROOT / ROSTER).write_bytes(raw)
    (ROOT / SPEC).write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
        + yaml.safe_dump(spec_payload(rows), sort_keys=False, allow_unicode=True))
    (ROOT / STEELMAN).write_text(
        f"# Steelman: {HID}\n\nHousing cost pressure may delay births, but the OECD series measures only the low-income population while Eurostat total fertility covers all women. Income, migration, student debt, age composition, housing supply, and family policies can move both series. More expensive housing can coexist with higher fertility in growing regions. Within-country fixed effects and prior timing do not remove these alternatives. A weak, opposite, unstable, or gate-failing result must stay visible.\n")
    (ROOT / PREREG).write_text(
        "# OECD housing overburden and later fertility: frozen registration\n\n"
        "Registered before selected Eurostat fertility values, missingness, or model fits were opened. "
        "The preflight read OECD exposure values and statuses plus Eurostat country/year/indicator keys only. "
        "Both pinned files predated this registration within the broader IESET corpus; this is not an independent future-data holdout.\n\n"
        "## Fixed question and sample\n\n"
        "OECD How's Life 3_3 PT_POP low-income housing-cost overburden change t−3→t (anchors 2013–2019) "
        "predicts Eurostat demo_find TOTFERRT change t→t+3. Exact normal-status housing observations "
        "are required for all four exposure years; country enters only with at least two eligible anchors. "
        f"The key-only roster has **{blind['key_only_rows']} pairs in {blind['key_only_countries']} countries**; "
        f"{blind['material_exposure_rows']} pairs in {blind['material_exposure_countries']} countries have "
        "at least 2 percentage points of absolute exposure change. These are upper bounds, not observed fertility coverage.\n\n"
        "## Frozen analysis\n\n"
        "Outcome is three-year fertility change in births per woman. OLS includes baseline housing burden at t−3, "
        "baseline fertility at t, country effects and anchor-year effects. Inference uses country-cluster CR1 "
        "and two-sided Student t(G−1). Complete-case floors are 95 pairs/20 countries and 50 material "
        "pairs/18 countries. Residualized exposure must be nonzero; the two largest squared-residual rows "
        "may contribute at most 30%, and the largest country at most 25%. Full rank and finite positive "
        "clustered uncertainty are required. The 2013–2016 pre-pandemic sign check requires 45 pairs/14 "
        "countries. SUPPORTED requires beta≤−0.003, p≤0.01 and negative pre-pandemic beta; REFUTED "
        "requires beta≥+0.003, p≤0.01 and positive pre-pandemic beta. Other estimable results are PARTIAL; "
        "any primary coverage, concentration or estimator failure is INCONCLUSIVE. No gates change after lock.\n\n"
        "## Sources and interpretation\n\n"
        f"- OECD 3_3 source: `{SOURCES['housing']['path']}`; SHA-256 `{SOURCES['housing']['sha256']}`.\n"
        f"- Eurostat TOTFERRT source: `{SOURCES['fertility']['path']}`; SHA-256 `{SOURCES['fertility']['sha256']}`.\n"
        f"- Frozen roster SHA-256: `{ROSTER_SHA}`.\n"
        "- [OECD How's Life definitions](https://www.oecd.org/wise/oecd-well-being-database-definitions.pdf): "
        "3_3 is overburden among the bottom-40 income population; the pinned 1.1 parquet labels PT_POP. "
        "[OECD Data Explorer](https://data-explorer.oecd.org/vis?bp=true&df%5Bag%5D=OECD.WISE.WDP&df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_HSL%40DF_HSL_CWB&df%5Bvs%5D=1.1&dq=.3_3.._T._T._T.&fc=Topic&fs%5B0%5D=Topic%2C1%7CSociety%23SOC%23%7CWell-being+and+beyond+GDP%23SOC_WEL%23&pd=%2C&pg=0&snb=26&to%5BTIME_PERIOD%5D=false&vw=tb).\n"
        "- [Eurostat fertility metadata](https://ec.europa.eu/eurostat/cache/metadata/en/demo_fer_esms.htm): "
        "TOTFERRT is the sum of period age-specific fertility rates.\n\n"
        "This is descriptive calibration only, with zero causal, policy, school-score, position and featured credit. "
        "The local p rule does not correct the full IESET archive.\n")
    print("registered fixed roster and one hypothesis", blind)


def validate_spec(rows: list[tuple[str, str, int]]) -> None:
    document = yaml.safe_load((ROOT / SPEC).read_text())
    if document != spec_payload(rows):
        raise RuntimeError("frozen spec differs from runner")


def registration_commit() -> str:
    paths = [RUNNER, SPEC, STEELMAN, PREREG, ROSTER]
    revisions = {first_addition(relative) for relative in paths}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for relative in paths:
        committed_unchanged(relative, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise RuntimeError("registration commit already contained measured artifacts")
    validate_spec(load_roster())
    return revision


def lock_payload(registration: str, selected: dict[str, dict[str, Any]],
    blind: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
        "sources": selected, "key_only_preflight": blind,
        "statement": "Two exact vintages and manifests locked after registration; selected fertility values and missingness still unopened."}


def write_source_lock() -> None:
    registration = registration_commit()
    selected = check_sources()
    blind = preflight(load_roster())
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, selected, blind), indent=2, sort_keys=True) + "\n")


def check_source_lock(registration: str, selected: dict[str, dict[str, Any]],
    blind: dict[str, Any]) -> str:
    revision = first_addition(LOCK)
    if revision == registration:
        raise RuntimeError("source lock must be in a later separate commit")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT)
    committed_unchanged(LOCK, revision)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, selected, blind):
        raise RuntimeError("source-lock payload differs from frozen pins")
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise RuntimeError("source-lock commit already contained measured artifacts")
    return revision


def measured_panel(rows: list[tuple[str, str, int]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    # First selected fertility-value and null access occurs here, after both commits.
    fertility = pd.read_parquet(ROOT / SOURCES["fertility"]["path"],
        columns=["freq", "indic_de", "geo_code", "period", "value"])
    fertility = fertility.loc[(fertility.freq == "A") & (fertility.indic_de == "TOTFERRT"),
        ["geo_code", "period", "value"]].copy()
    fertility["period"] = fertility.period.astype(int)
    fertility = fertility.set_index(["geo_code", "period"]).value
    housing = housing_values()
    records = []
    invalid = 0
    for country, geo, anchor in rows:
        base, later = float(fertility.loc[geo, anchor]), float(fertility.loc[geo, anchor + 3])
        if not (math.isfinite(base) and math.isfinite(later)
            and 0.5 <= base <= 10 and 0.5 <= later <= 10):
            invalid += 1
            continue
        h0 = float(housing.loc[country, anchor - 3].value)
        h1 = float(housing.loc[country, anchor].value)
        records.append({"country_iso3": country, "eurostat_geo": geo, "anchor_year": anchor,
            "x": h1 - h0, "baseline_housing": h0, "baseline_fertility": base,
            "y": later - base})
    frame = pd.DataFrame(records, columns=["country_iso3", "eurostat_geo", "anchor_year",
        "x", "baseline_housing", "baseline_fertility", "y"])
    counts = frame.country_iso3.value_counts()
    frame = frame.loc[frame.country_iso3.map(counts).ge(2)].copy()
    frame = frame.sort_values(["country_iso3", "anchor_year"]).reset_index(drop=True)
    material = frame.x.abs().ge(MATERIAL_CHANGE)
    gate = {"key_only_rows": len(rows), "invalid_or_missing_fertility_pairs": invalid,
        "valid_rows": len(frame), "valid_countries": int(frame.country_iso3.nunique()),
        "material_change_rows": int(material.sum()),
        "material_change_countries": int(frame.loc[material, "country_iso3"].nunique()),
        "outcome_values_read_after_lock": True}
    return frame, gate


def fitted_beta(panel: pd.DataFrame) -> tuple[float, float, float, int]:
    formula = "y ~ x + baseline_housing + baseline_fertility + C(country_iso3) + C(anchor_year)"
    model = smf.ols(formula, data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        raise ValueError("model not full rank")
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
        "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    countries = int(panel.country_iso3.nunique())
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        raise ValueError("nonfinite or nonpositive country-cluster uncertainty")
    p = float(2 * student_t.sf(abs(beta / se), countries - 1))
    if not math.isfinite(p):
        raise ValueError("nonfinite Student-t p value")
    return beta, se, p, int(fit.model.rank)


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES
        or gate["material_change_rows"] < MIN_MATERIAL_ROWS
        or gate["material_change_countries"] < MIN_MATERIAL_COUNTRIES):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen coverage or material-exposure floor failed",
            "gate": gate, "primary": None, "sensitivity": None}
    residual_model = smf.ols(
        "x ~ baseline_housing + baseline_fertility + C(country_iso3) + C(anchor_year)",
        data=panel)
    if np.linalg.matrix_rank(residual_model.exog) != residual_model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "treatment residualization lacks full rank",
            "gate": gate, "primary": None, "sensitivity": None}
    squared = np.square(np.asarray(residual_model.fit().resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "no finite residualized exposure variation",
            "gate": gate, "primary": None, "sensitivity": None}
    gate["top_two_residual_x_share"] = float(sum(sorted(squared, reverse=True)[:2]) / total)
    gate["top_country_residual_x_share"] = float(panel.assign(residual_sq=squared)
        .groupby("country_iso3").residual_sq.sum().max() / total)
    if (gate["top_two_residual_x_share"] > MAX_TOP_TWO_RESIDUAL_SHARE
        or gate["top_country_residual_x_share"] > MAX_TOP_COUNTRY_SHARE):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen residualized-exposure concentration gate failed",
            "gate": gate, "primary": None, "sensitivity": None}
    try:
        beta, se, p, rank = fitted_beta(panel)
    except ValueError as exc:
        return {"verdict": "INCONCLUSIVE", "reason": str(exc),
            "gate": gate, "primary": None, "sensitivity": None}
    countries = gate["valid_countries"]
    critical = float(student_t.ppf(0.995, countries - 1))
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 0.99,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": countries,
        "df_inference": countries - 1, "model_rank": rank,
        "method": "country/anchor FE OLS with baseline housing and fertility; country-cluster CR1; Student t(G-1)"}
    sensitivity_panel = panel.loc[panel.anchor_year.le(2016)].copy()
    sensitivity_counts = sensitivity_panel.country_iso3.value_counts()
    sensitivity_panel = sensitivity_panel.loc[sensitivity_panel.country_iso3.map(sensitivity_counts).ge(2)]
    sensitivity = {"n_rows": len(sensitivity_panel),
        "n_countries": int(sensitivity_panel.country_iso3.nunique()),
        "coefficient": None, "reason": "insufficient pre-pandemic sample"}
    if (sensitivity["n_rows"] >= MIN_SENSITIVITY_ROWS
        and sensitivity["n_countries"] >= MIN_SENSITIVITY_COUNTRIES):
        try:
            s_beta, s_se, s_p, _ = fitted_beta(sensitivity_panel)
            sensitivity.update(coefficient=s_beta, std_error=s_se,
                p_value_two_sided=s_p, reason="estimable")
        except ValueError as exc:
            sensitivity["reason"] = str(exc)
    robust_negative = sensitivity["coefficient"] is not None and sensitivity["coefficient"] < 0
    robust_positive = sensitivity["coefficient"] is not None and sensitivity["coefficient"] > 0
    if beta <= -MIN_ABS_BETA and p <= ALPHA and robust_negative:
        verdict, reason = "SUPPORTED", "negative association clears frozen size, significance and pre-pandemic sign gates"
    elif beta >= MIN_ABS_BETA and p <= ALPHA and robust_positive:
        verdict, reason = "REFUTED", "opposite association clears frozen size, significance and pre-pandemic sign gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear every frozen directional gate"
    return {"verdict": verdict, "reason": reason, "gate": gate,
        "primary": primary, "sensitivity": sensitivity}


def output_payload(result: dict[str, Any], registration: str, locked: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    diagnostic = {"hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": locked, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "primary": primary,
        "prepandemic_sensitivity": result["sensitivity"],
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": locked,
        "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
        "derived_panel": gate, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "topic": "housing"},
        "preregistration": {"spec_commit": registration, "source_lock_commit": locked,
            "family_id": FAMILY, "family_size": 1, "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
            "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary, "prepandemic_sensitivity": result["sensitivity"]},
        "limitations": LIMITATIONS, "correction": CORRECTION}
    card = (f"# Result card: {HID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Preregistration: `{registration}`; source lock: `{locked}`.\n\n"
        f"OECD low-income housing overburden change from t−3 to t; Eurostat total fertility change "
        f"from t to t+3. Complete pairs: {gate['valid_rows']} / {gate['valid_countries']} countries; "
        f"material housing changes: {gate['material_change_rows']} / "
        f"{gate['material_change_countries']} countries.\n")
    if primary is not None:
        card += (f"\nBeta={primary['coefficient']:+.6g} births-per-woman change per +1 burden point; "
            f"country-cluster SE={primary['std_error']:.6g}; two-sided t p="
            f"{primary['p_value_two_sided']:.6g}; 99% CI={primary['confidence_interval']}.\n")
    sensitivity = result["sensitivity"]
    if sensitivity is not None:
        card += (f"\nPre-pandemic 2013–2016 sign check: {sensitivity['n_rows']} rows / "
            f"{sensitivity['n_countries']} countries; beta={sensitivity['coefficient']}; "
            f"{sensitivity['reason']}.\n")
    card += ("\nOne fixed test uses p≤0.01 and |beta|≥0.003 for direction, with a same-sign "
        "pre-pandemic check. This is descriptive calibration only; zero causal, policy, "
        "school, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict,
        "primary": primary, "prepandemic_sensitivity": sensitivity}
    coefficients = [{"term": "housing_overburden_change_pp", **primary}] if primary is not None else []
    return {"diagnostic": diagnostic, "manifest": manifest, "packet": packet,
        "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def result_summary(result: dict[str, Any], registration: str, locked: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = f"{primary['coefficient']:+.6g}" if primary else "not estimated"
    p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
    return ("# Low-income housing overburden and later fertility: frozen descriptive result\n\n"
        f"Preregistration `{registration}`; source lock `{locked}`.\n\n"
        "| Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |\n"
        "| --- | ---: | ---: | ---: | ---: |\n"
        f"| **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | "
        f"{gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |\n\n"
        "Beta is the later three-year fertility-rate change (births per woman) per +1 percentage-point "
        "earlier three-year increase in OECD low-income housing overburden. The frozen rule requires "
        "p≤0.01, |beta|≥0.003, and a same-sign pre-pandemic check for directional credit. "
        "The test is descriptive calibration without causal, policy, school-score, position, or featured credit.\n")


def normalize(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize(v) for key, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected,
            rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def write_artifacts(result: dict[str, Any], registration: str, locked: str) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated = output_payload(result, registration, locked, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(generated["diagnostic"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(generated["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(generated["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(generated["card"])
    (folder / "replication.py").write_text(generated["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(generated["chart"], indent=2) + "\n")
    pd.DataFrame(generated["coefficients"], columns=["term", "coefficient", "std_error",
        "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows",
        "n_countries", "df_inference", "model_rank", "method"]).to_parquet(
            folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(result_summary(result, registration, locked))


def verify_artifacts(result: dict[str, Any], registration: str, locked: str) -> None:
    folder = ROOT / RUN_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    generated = output_payload(result, registration, locked, saved["run_utc"])
    equal_close(saved, generated["diagnostic"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), generated["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), generated["packet"], "packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), generated["chart"], "chart")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
        generated["coefficients"], "coefficients")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
        or (folder / "result_card.md").read_text() != generated["card"]
        or (folder / "replication.py").read_text() != generated["wrapper"]
        or (ROOT / SUMMARY).read_text() != result_summary(result, registration, locked)):
        raise AssertionError("text result artifact differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("register", "check-sources", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.register:
        register()
        return 0
    selected = check_sources()
    if args.check_sources:
        print("two exact source vintages and manifests match; selected fertility values unopened")
        return 0
    rows = load_roster()
    blind = preflight(rows)
    if args.preflight:
        print(json.dumps(blind, indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    registration = registration_commit()
    locked = check_source_lock(registration, selected, blind)
    panel, gate = measured_panel(rows)
    result = estimate(panel, gate)
    if args.run:
        write_artifacts(result, registration, locked)
        print(HID, result["verdict"], gate)
        return 0
    verify_artifacts(result, registration, locked)
    print("verified exact replay", HID, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
