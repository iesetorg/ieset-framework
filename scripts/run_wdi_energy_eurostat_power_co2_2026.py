#!/usr/bin/env python3
"""Frozen WDI electricity exposures to Eurostat power/heat CO2 family.

Before separate registration and source-lock commits, only hashes, WDI
treatment values, and Eurostat outcome keys/dimensions are opened. Eurostat
numeric outcome values and null masks are first read by --run or --verify after
both commits pass chronology and immutable-file checks.
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
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_energy_eurostat_power_co2_2026_10_10"
RUNNER = "scripts/run_wdi_energy_eurostat_power_co2_2026.py"
PREREG = "engine/audits/wdi_energy_eurostat_power_co2_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_energy_eurostat_power_co2_2026_key_roster.csv"
ROSTER_SHA = "6bfeb62c5fa7bd02db3a3259708d9f24ccad4ab8559e60f80d79c0c778af0f8d"
LOCK = "data/pinned_evidence/wdi_energy_eurostat_power_co2_2026.manifest.json"
SUMMARY = "engine/audits/wdi_energy_eurostat_power_co2_results_2026-10-10.md"
OUTCOME = "data/vintages/eurostat/env_air_gge@2026-04-30T115534Z.parquet"
RENEWABLE = "data/vintages/world_bank_wdi/EG.ELC.RNEW.ZS@2026-05-05T203933Z.parquet"
ELECTRIC_USE = "data/vintages/world_bank_wdi/EG.USE.ELEC.KH.PC@2026-05-05T203903Z.parquet"
WDI_MANIFEST = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
EUROSTAT_MANIFEST = "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml"
SOURCES = {
    "outcome": {"publisher": "eurostat", "series_id": "env_air_gge", "path": OUTCOME,
                "sha256": "5597d4f1a75c8c9a91306723772bc8ce4e3df3cfa9af65ce137bc6a3e52d8ba2",
                "manifest": EUROSTAT_MANIFEST,
                "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
    "renewable": {"publisher": "world_bank_wdi", "series_id": "EG.ELC.RNEW.ZS", "path": RENEWABLE,
                  "sha256": "d54e3db8299b8e2dbd0452983f0a245ef01086e547681122ecf2368cd6775525",
                  "manifest": WDI_MANIFEST,
                  "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "electric_use": {"publisher": "world_bank_wdi", "series_id": "EG.USE.ELEC.KH.PC", "path": ELECTRIC_USE,
                     "sha256": "336a90a5d14417931359257729d9080de14f074085df19b4bb57b0e88e795b68",
                     "manifest": WDI_MANIFEST,
                     "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
}
GEO_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU",
    "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
    "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK",
}
CASES = {
    "renewable": {"id": "wdi_renewable_electricity_eurostat_power_co2_forward_2026",
                  "label": "renewable-electricity output share", "cap": 15.0, "material": 2.0,
                  "expected_sign": "-", "meaningful_beta": 0.005,
                  "key_rows": 873, "key_countries": 29, "material_rows": 344,
                  "material_countries": 27, "floor": (620, 23, 160, 20),
                  "pre2019_floor": (540, 23, 140, 19)},
    "electric_use": {"id": "wdi_electric_use_eurostat_power_co2_forward_2026",
                     "label": "electric-power consumption per capita", "cap": 0.25,
                     "material": 0.05, "expected_sign": "+", "meaningful_beta": 0.20,
                     "key_rows": 926, "key_countries": 29, "material_rows": 168,
                     "material_countries": 29, "floor": (670, 23, 80, 20),
                     "pre2019_floor": (570, 23, 65, 19)},
}
MIN_YEARS = 10
FAMILY_ALPHA, P_MAX = 0.01, 0.005
MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE = 0.30
MAX_TOP_COUNTRY_RESIDUAL_X_SHARE = 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "featured_eligible": False}
LIMITATIONS = [
    "WDI renewable output share and electric-power consumption are IEA-origin energy series; electricity generated, used, traded, and lost are different quantities.",
    "Eurostat env_air_gge republishes EEA/UNFCCC territorial inventories. CRF1A1A includes public electricity and heat production; it is not all electricity generation or all territorial emissions.",
    "The pinned Eurostat Parquet retains no observation flags, so provisional, revised, or break annotations cannot be screened from this vintage. The WDI status columns are blank; method breaks are likewise not identified.",
    "Coal-to-gas switching, nuclear dispatch, weather, imports, heat production, ETS, fuel prices, demand, and early-1990s transition can confound these forward associations.",
    "Pre-2019 sensitivity excludes 2019-2022 treatment years and 2020-2023 forward endpoints; it cannot remove earlier shocks or identify a causal effect.",
    "These are two source-overlapping local tests, not independent replications or renewable-policy interventions. No causal, policy, school-score, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/energy/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(key: str, case: dict[str, Any]) -> dict[str, Any]:
    n, c, m, mc = case["floor"]
    pn, pc, pm, pmc = case["pre2019_floor"]
    return {"family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX,
            "expected_beta_sign": case["expected_sign"],
            "meaningful_beta_min_abs": case["meaningful_beta"],
            "min_valid_rows": n, "min_valid_countries": c,
            "min_material_change_rows": m, "min_material_change_countries": mc,
            "pre2019_max_treatment_year": 2018,
            "pre2019_min_valid_rows": pn, "pre2019_min_valid_countries": pc,
            "pre2019_min_material_change_rows": pm,
            "pre2019_min_material_change_countries": pmc,
            "material_treatment_change_min_abs": case["material"],
            "max_abs_treatment_change": case["cap"],
            "min_years_per_country": MIN_YEARS,
            "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE,
            "max_top_country_residual_x_share": MAX_TOP_COUNTRY_RESIDUAL_X_SHARE,
            "expected_key_rows": case["key_rows"],
            "expected_key_countries": case["key_countries"],
            "roster_sha256": ROSTER_SHA,
            "source_files": {role: {field: SOURCES[role][field]
                                    for field in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role in (key, "outcome")},
            "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
            "school_score_eligible": False, "school_score_credit": 0,
            "featured_eligible": False}


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER]
    for case in CASES.values():
        frozen += [spec_rel(case), steelman_rel(case)]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec["hypothesis_id"] != case["id"] or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["steelman"] != steelman_rel(case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
                or spec["falsification"]["threshold"] != threshold_for(key, case)):
            raise RuntimeError(f"registered spec mismatch: {key}")
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contains measured results")
    return revision


def check_sources() -> dict[str, dict[str, Any]]:
    narrow = {}
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} raw SHA-256 mismatch")
        manifest_path = ROOT / source["manifest"]
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch")
        manifest = yaml.safe_load(manifest_path.read_text())
        matches = [e for e in manifest.get("entries", [])
                   if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} selected source entry mismatch")
        entry = matches[0]
        narrow[role] = {**source, "source_url": entry.get("source_url"),
                        "methodology_url": entry.get("methodology_url"),
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
                        "rows": entry.get("rows"), "frequency": entry.get("frequency"),
                        "units": entry.get("units")}
    return narrow


def load_roster() -> dict[str, list[tuple[str, int]]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"case_id,country_iso3,year\n"):
        raise RuntimeError("frozen roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    result = {key: [] for key in CASES}
    for row in records:
        if row["case_id"] not in result:
            raise RuntimeError("unexpected case in roster")
        result[row["case_id"]].append((row["country_iso3"], int(row["year"])))
    actual = [(r["case_id"], r["country_iso3"], int(r["year"])) for r in records]
    expected = [(key, c, y) for key in CASES
                for c, y in sorted(result[key], key=lambda item: (item[0], item[1]))]
    if actual != expected or len(actual) != 1799 or len(set(actual)) != len(actual):
        raise RuntimeError("frozen roster ordering, size, or uniqueness mismatch")
    for key, case in CASES.items():
        rows = result[key]
        if len(rows) != case["key_rows"] or len({c for c, _ in rows}) != case["key_countries"]:
            raise RuntimeError(f"frozen roster envelope mismatch: {key}")
    return result


def source_keys() -> tuple[dict[str, dict[tuple[str, int], float]], set[tuple[str, int]]]:
    """Read WDI treatment values and Eurostat outcome keys/dimensions only."""
    exposure = {}
    for key in CASES:
        source = SOURCES[key]
        frame = pd.read_parquet(ROOT / source["path"],
                                columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
        if (len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all()
                or not frame.obs_status.fillna("").eq("").all()):
            raise RuntimeError(f"{key} WDI raw/indicator/status contract changed")
        frame = frame.loc[frame.country_iso3.isin(GEO_TO_ISO3.values())]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate {key} national country-year key")
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        valid = np.isfinite(frame.value)
        valid &= frame.value.gt(0) if key == "electric_use" else frame.value.between(0, 100)
        frame = frame.loc[valid]
        exposure[key] = {(str(c), int(y)): float(v)
                         for c, y, v in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    outcome = pd.read_parquet(ROOT / OUTCOME,
                              columns=["freq", "unit", "airpol", "src_crf", "geo_code", "period"])
    if len(outcome) != 1520160:
        raise RuntimeError("Eurostat raw row-count contract changed")
    selected = outcome.loc[outcome.freq.eq("A") & outcome.unit.eq("THS_T")
                           & outcome.airpol.eq("CO2") & outcome.src_crf.eq("CRF1A1A")]
    if (set(selected.geo_code) != set(GEO_TO_ISO3) | {"EU27_2020"}
            or selected.duplicated(["geo_code", "period"]).any()):
        raise RuntimeError("selected power/heat CO2 key or geography contract changed")
    national = selected.loc[selected.geo_code.isin(GEO_TO_ISO3)]
    if len(national) != 986:
        raise RuntimeError("selected national outcome key count changed")
    keys = {(GEO_TO_ISO3[g], int(y))
            for g, y in national[["geo_code", "period"]].itertuples(index=False, name=None)}
    return exposure, keys


def concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    fit = smf.ols("x ~ C(country_iso3) + C(year)", data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    n_top = max(1, math.ceil(.01 * len(squared)))
    top_row = float(np.sort(squared)[-n_top:].sum() / total)
    grouped = pd.DataFrame({"country_iso3": panel.country_iso3.to_numpy(), "squared": squared})
    top_country = float(grouped.groupby("country_iso3").squared.sum().max() / total)
    return top_row, top_country


def build_roster(exposure: dict[str, dict[tuple[str, int], float]],
                 outcome_keys: set[tuple[str, int]]) -> tuple[dict[str, list[tuple[str, int]]], dict[str, Any]]:
    chosen, metrics = {}, {}
    for key, case in CASES.items():
        values = exposure[key]
        candidates = []
        for (country, year), value in values.items():
            if ((country, year - 1) not in values or (country, year) not in outcome_keys
                    or (country, year + 1) not in outcome_keys):
                continue
            delta = (math.log(value) - math.log(values[(country, year - 1)])
                     if key == "electric_use" else value - values[(country, year - 1)])
            if abs(delta) <= case["cap"]:
                candidates.append((country, year, float(delta)))
        counts = Counter(country for country, _, _ in candidates)
        rows = sorted((c, y, x) for c, y, x in candidates if counts[c] >= MIN_YEARS)
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x"])
        material = panel.x.abs().ge(case["material"])
        shares = concentration(panel)
        if shares is None or shares[0] > .30 or shares[1] > .20:
            raise RuntimeError(f"{key} prelock exposure-concentration gate failed")
        if (len(panel) != case["key_rows"] or panel.country_iso3.nunique() != case["key_countries"]
                or int(material.sum()) != case["material_rows"]
                or int(panel.loc[material, "country_iso3"].nunique()) != case["material_countries"]):
            raise RuntimeError(f"{key} treatment-only roster envelope changed")
        chosen[key] = [(c, int(y)) for c, y, _ in rows]
        metrics[key] = {"key_rows": len(panel), "key_countries": int(panel.country_iso3.nunique()),
                        "t_years": [int(panel.year.min()), int(panel.year.max())],
                        "treatment_only_material_rows": int(material.sum()),
                        "treatment_only_material_countries": int(panel.loc[material, "country_iso3"].nunique()),
                        "treatment_only_top_one_percent_residual_x_share": shares[0],
                        "treatment_only_top_country_residual_x_share": shares[1],
                        "pre2019_key_rows": int(panel.year.le(2018).sum()),
                        "pre2019_key_countries": int(panel.loc[panel.year.le(2018), "country_iso3"].nunique())}
    return chosen, metrics


def key_preflight() -> dict[str, Any]:
    exposure, keys = source_keys()
    generated, metrics = build_roster(exposure, keys)
    if generated != load_roster():
        raise RuntimeError("source key preflight differs from frozen roster")
    return {"treatment_values_read": True, "outcome_values_read": False,
            "outcome_null_masks_read": False, "outcome_status_available": False,
            "exact_year_join": True, "national_outcome_keys": len(keys),
            "roster_sha256": ROSTER_SHA, "cases": metrics}


def lock_payload(registration: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    registration = registration_commit()
    narrow = check_sources()
    preflight = key_preflight()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(registration, narrow, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening Eurostat numeric outcome values")


def check_source_lock(registration: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, narrow, preflight):
        raise RuntimeError("source lock differs from raw pins or frozen preflight")
    commit = first_addition(LOCK)
    if (commit == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, commit],
                                                cwd=ROOT).returncode):
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return commit


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First outcome-value/null access. Caller has verified both commits."""
    exposure, _ = source_keys()
    raw = pd.read_parquet(ROOT / OUTCOME,
                          columns=["freq", "unit", "airpol", "src_crf", "geo_code", "period", "value"])
    raw = raw.loc[raw.freq.eq("A") & raw.unit.eq("THS_T") & raw.airpol.eq("CO2")
                  & raw.src_crf.eq("CRF1A1A") & raw.geo_code.isin(GEO_TO_ISO3)]
    if raw.duplicated(["geo_code", "period"]).any():
        raise RuntimeError("duplicate selected national Eurostat emissions key")
    emissions = {(GEO_TO_ISO3[g], int(y)): float(v) if pd.notna(v) and math.isfinite(float(v))
                 and float(v) > 0 else None
                 for g, y, v in raw[["geo_code", "period", "value"]].itertuples(index=False, name=None)}
    panels = {}
    for key, case in CASES.items():
        rows, missing = [], 0
        for country, year in roster[key]:
            baseline, forward = emissions.get((country, year)), emissions.get((country, year + 1))
            if baseline is None or forward is None:
                missing += 1
                continue
            values = exposure[key]
            x = (math.log(values[(country, year)]) - math.log(values[(country, year - 1)])
                 if key == "electric_use" else values[(country, year)] - values[(country, year - 1)])
            rows.append({"country_iso3": country, "year": year, "x": x,
                         "y": math.log(forward) - math.log(baseline)})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "y"])
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        material = panel.x.abs().ge(case["material"])
        gate = {"roster_rows": len(roster[key]), "dropped_missing_nonpositive_or_invalid_outcome_pairs": missing,
                "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
                "material_change_rows": int(material.sum()),
                "material_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
                "outcome_values_read_after_lock": True}
        panels[key] = panel, gate
    return panels


def estimate(panel: pd.DataFrame, case: dict[str, Any], floor: tuple[int, int, int, int]) -> dict[str, Any]:
    n, c, m, mc = floor
    material = panel.x.abs().ge(case["material"])
    gate = {"valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
            "material_change_rows": int(material.sum()),
            "material_change_countries": int(panel.loc[material, "country_iso3"].nunique())}
    if (gate["valid_rows"] < n or gate["valid_countries"] < c
            or gate["material_change_rows"] < m or gate["material_change_countries"] < mc):
        return {"gate": gate, "reason": "frozen complete-case or material-exposure floor failed", "fit": None}
    shares = concentration(panel)
    if shares is None:
        return {"gate": gate, "reason": "no finite residual exposure variation", "fit": None}
    gate["top_one_percent_residual_x_share"], gate["top_country_residual_x_share"] = shares
    if shares[0] > MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE or shares[1] > MAX_TOP_COUNTRY_RESIDUAL_X_SHARE:
        return {"gate": gate, "reason": "frozen residual-exposure concentration gate failed", "fit": None}
    model = smf.ols("y ~ x + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "reason": "fixed-effect design lacks full rank", "fit": None}
    groups = int(panel.country_iso3.nunique())
    fitted = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                    "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fitted.params["x"]), float(fitted.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "reason": "invalid country-cluster uncertainty", "fit": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(.9975, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "reason": "invalid country-cluster t inference", "fit": None}
    return {"gate": gate, "reason": "estimable", "fit": {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": .995, "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
        "model_rank": int(fitted.model.rank),
        "method": "country/year FE OLS, country-cluster CR1, Student t(G-1)"}}


def directional(fit: dict[str, Any], case: dict[str, Any]) -> str | None:
    beta, p = fit["coefficient"], fit["p_value_two_sided"]
    mag = case["meaningful_beta"]
    if case["expected_sign"] == "-":
        if beta <= -mag and p <= P_MAX:
            return "SUPPORTED"
        if beta >= mag and p <= P_MAX:
            return "REFUTED"
    else:
        if beta >= mag and p <= P_MAX:
            return "SUPPORTED"
        if beta <= -mag and p <= P_MAX:
            return "REFUTED"
    return None


def judge(panel: pd.DataFrame, case: dict[str, Any]) -> dict[str, Any]:
    primary = estimate(panel, case, case["floor"])
    pre_panel = panel.loc[panel.year.le(2018)].copy()
    pre_counts = pre_panel.country_iso3.value_counts()
    pre_panel = pre_panel.loc[pre_panel.country_iso3.map(pre_counts).ge(MIN_YEARS)]
    pre2019 = estimate(pre_panel, case, case["pre2019_floor"])
    if primary["fit"] is None:
        verdict, reason = "INCONCLUSIVE", primary["reason"]
    else:
        main_direction = directional(primary["fit"], case)
        if main_direction is None:
            verdict, reason = "PARTIAL", "primary estimate misses magnitude or family p cutoff"
        elif pre2019["fit"] is None:
            verdict, reason = "INCONCLUSIVE", "mandatory pre-2019 disruption diagnostic cannot be estimated"
        elif directional(pre2019["fit"], case) != main_direction:
            verdict, reason = "PARTIAL", "pre-2019 diagnostic does not independently confirm direction, magnitude, and family p cutoff"
        else:
            verdict, reason = main_direction, "primary and pre-2019 estimates clear frozen directional gates"
    return {"verdict": verdict, "reason": reason, "primary": primary, "pre2019": pre2019}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any],
                     registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict = case["id"], result["verdict"]
    inputs = {role: SOURCES[role] for role in (key, "outcome")}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": "energy"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 2, "key_roster": ROSTER,
                                  "key_roster_sha256": ROSTER_SHA, "steelman": steelman_rel(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": inputs, "sample": result["primary"]["gate"]},
              "results": {"primary": result["primary"]["fit"], "pre2019": result["pre2019"]},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
                   "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER, "preregistration_commit": registration,
                   "source_lock_commit": lock_commit, "source_lock": LOCK, "template": "panel_fe",
                   "preflight": result["primary"]["gate"], "primary": result["primary"]["fit"],
                   "pre2019": result["pre2019"], "p_max_two_sided_bonferroni": P_MAX,
                   "meaningful_beta_min_abs": case["meaningful_beta"],
                   "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
                "derived_panel": result["primary"]["gate"], "correction": CORRECTION}
    main, pre = result["primary"]["fit"], result["pre2019"]["fit"]
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen registration `{registration}`; source lock `{lock_commit}`.\n\n"
            f"Exposure: {case['label']}; outcome: one-year forward log change in Eurostat "
            f"public electricity and heat CO2 (thousand tonnes). Key-only upper bound: "
            f"{case['key_rows']} country-years / {case['key_countries']} countries. "
            f"Complete primary pairs: {result['primary']['gate']['valid_rows']} / "
            f"{result['primary']['gate']['valid_countries']}.\n")
    if main is not None:
        card += (f"\nPrimary beta={main['coefficient']:+.6g}; country-cluster SE={main['std_error']:.6g}; "
                 f"two-sided t p={main['p_value_two_sided']:.6g}; 99.5% CI={main['confidence_interval']}.\n")
    if pre is not None:
        card += (f"Pre-2019 beta={pre['coefficient']:+.6g}; two-sided t p={pre['p_value_two_sided']:.6g}; "
                 f"complete pairs={pre['n_rows']}.\n")
    card += ("\nTwo prespecified tests; Bonferroni family alpha 0.01, each two-sided p <= 0.005. "
             "The pre-2019 diagnostic must independently clear the same directional gate for a directional verdict. "
             "Descriptive calibration only; no causal, policy, school, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
             "primary": main, "pre2019": pre}
    coefficients = ([{"term": "treatment_change", **main}] if main is not None else [])
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# Electricity mix and use to power-sector CO2: two-test result", "",
             f"Registration `{registration}`; source lock `{lock_commit}`.",
             "Both tests are in one Bonferroni family (alpha 0.01; each two-sided p <= 0.005).",
             "", "| Exposure | Verdict | Complete pairs / countries | Material pairs / countries | Primary beta | Primary p | Pre-2019 beta | Pre-2019 p |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, main, pre = result["primary"]["gate"], result["primary"]["fit"], result["pre2019"]["fit"]
        cell = lambda fit, field: f"{fit[field]:+.6g}" if fit is not None and field == "coefficient" else (f"{fit[field]:.6g}" if fit is not None else "not estimated")
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_change_rows']} / {gate['material_change_countries']} | {cell(main, 'coefficient')} | {cell(main, 'p_value_two_sided')} | {cell(pre, 'coefficient')} | {cell(pre, 'p_value_two_sided')} |")
    lines += ["", "The response is the log change in public-electricity-and-heat CO2 from t to t+1; the exposure change is from t-1 to t. Renewable share is percentage points; electric use is log kWh per capita. These are forward associations, not policy effects.",
              "", "The pre-2019 diagnostic excludes pandemic and 2022 energy-crisis forward endpoints. Exact source and measurement limits remain in the preregistration. No school, policy, causal, or featured credit.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("one or more family result artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for key, case in CASES.items():
        payload = artifact_payload(key, case, results[key], registration, lock_commit, stamp)
        folder = ROOT / run_rel(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
        pd.DataFrame(payload["coefficients"], columns=["term", "coefficient", "std_error",
                                                       "p_value_two_sided", "confidence_level",
                                                       "confidence_interval", "n_rows", "n_countries",
                                                       "df_inference", "model_rank", "method"]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def normalize_arrow(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize_arrow(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize_arrow(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_arrow(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize_arrow(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for key, case in CASES.items():
        folder = ROOT / run_rel(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(key, case, results[key], registration, lock_commit, saved["run_utc"])
        for name in ("diagnostics", "manifest", "packet", "chart", "coefficients"):
            path = folder / {"diagnostics": "diagnostics.json", "manifest": "manifest.yaml",
                             "packet": "evidence_packet.yaml", "chart": "chart_data.json",
                             "coefficients": "coefficients.parquet"}[name]
            actual = (pd.read_parquet(path).to_dict(orient="records") if name == "coefficients"
                      else yaml.safe_load(path.read_text()) if name in ("manifest", "packet")
                      else json.loads(path.read_text()))
            equal_close(actual, payload[name], f"{key}.{name}")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != payload["card"]
                or (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"{key}: text artifact mismatch")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    narrow = check_sources()
    if args.check_sources:
        print("WDI and Eurostat source SHA pins match; outcome values unopened")
        return 0
    if args.preflight:
        print(json.dumps(key_preflight(), indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    registration = registration_commit()
    preflight = key_preflight()
    lock_commit = check_source_lock(registration, narrow, preflight)
    panels = measured_panels(load_roster())
    results = {key: judge(panels[key][0], CASES[key]) for key in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        for key, result in results.items():
            print(key, result["verdict"], result["reason"])
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", FAMILY, {key: result["verdict"] for key, result in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
