#!/usr/bin/env python3
"""Frozen two-test internet/public-R&D to resident-patenting calibration.

Before separate registration and source-lock commits, this runner reads only
exposure values and patent/population/income keys, never outcome or control
values or their null/status masks. --run and --verify unlock those values only
after immutable-file and Git chronology guards pass.
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
FAMILY = "internet_public_rd_resident_patenting_2026_10_10"
RUNNER = "scripts/run_internet_public_rd_patenting_2026.py"
PREREG = "engine/audits/internet_public_rd_patenting_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/internet_public_rd_patenting_2026_key_roster.csv"
ROSTER_SHA = "4b548bc4e78a5221a0b8079656eb8f61d152e404d97eaf385033f2bdb817d18f"
LOCK = "data/pinned_evidence/internet_public_rd_patenting_2026.manifest.json"
SUMMARY = "engine/audits/internet_public_rd_patenting_results_2026-10-10.md"
T_START, T_END, HORIZON, MIN_YEARS = 1998, 2017, 2, 5
FAMILY_ALPHA, P_MAX = 0.01, 0.005
MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE = 0.30
MAX_TOP_COUNTRY_RESIDUAL_X_SHARE = 0.30
EURO_TO_ISO3 = dict(zip(
    "AT BE BG CH CY CZ DE DK EE EL ES FI FR HR HU IE IS IT LT LU LV ME MK MT NL NO PL PT RO RS SE SI SK TR UK".split(),
    "AUT BEL BGR CHE CYP CZE DEU DNK EST GRC ESP FIN FRA HRV HUN IRL ISL ITA LTU LUX LVA MNE MKD MLT NLD NOR POL PRT ROU SRB SWE SVN SVK TUR GBR".split(),
))
COUNTRIES = frozenset(EURO_TO_ISO3.values())
assert len(EURO_TO_ISO3) == len(COUNTRIES) == 35
SOURCES = {
    "internet": {"publisher": "world_bank_wdi", "series_id": "IT.NET.USER.ZS",
                 "path": "data/vintages/world_bank_wdi/IT.NET.USER.ZS@2026-05-05T203400Z.parquet",
                 "sha256": "c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8",
                 "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                 "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "public_rd": {"publisher": "eurostat", "series_id": "rd_e_gerdtot",
                  "path": "data/vintages/eurostat/rd_e_gerdtot@2026-05-05T210242Z.parquet",
                  "sha256": "fea284d7b17e31a3803749fca052f6a110ed1b8e703a9151964d1d15f58df152",
                  "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                  "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "patents": {"publisher": "wipo", "series_id": "patent_applications_resident",
                "path": "data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet",
                "sha256": "8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e",
                "manifest": "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
                "manifest_sha256": "cf2f7e75af5612b302af7fbb0479c196598aa060c20f858723108a8c95455de4"},
    "population": {"publisher": "world_bank_wdi", "series_id": "SP.POP.TOTL",
                   "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
                   "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
                   "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
                   "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "income": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
               "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
               "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
               "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
               "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
}
CASES = {
    "internet": {"id": "wdi_internet_uptake_resident_patenting_forward_2026",
                 "label": "two-year internet-use uptake", "expected_rows": 684,
                 "expected_countries": 35, "min_rows": 400, "min_countries": 25,
                 "material_min": 5.0, "min_material_rows": 150,
                 "min_material_countries": 20, "meaningful_beta": 0.005,
                 "source": "world_bank_wdi:IT.NET.USER.ZS"},
    "public_rd": {"id": "eurostat_public_rd_resident_patenting_forward_2026",
                  "label": "government and higher-education performed R&D",
                  "expected_rows": 620, "expected_countries": 34,
                  "min_rows": 350, "min_countries": 25,
                  "material_min": 0.05, "min_material_rows": 20,
                  "min_material_countries": 20, "meaningful_beta": 0.25,
                  "source": "eurostat:rd_e_gerdtot"},
}
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "featured_eligible": False}
LIMITATIONS = [
    "WDI internet use measures people using the Internet, not broadband quality or productive digital use; estimates, survey modes, and mobile access change over time.",
    "Eurostat GOV+HES is R&D performed in government and higher-education sectors, not funding by government; the selected raw slice lacks observation-status or break flags.",
    "Resident patent applications are WIPO-origin counts delivered by the WDI API, not independent WIPO records or patent quality; filing law, office practices, and population denominators vary.",
    "Temporal ordering, country/year fixed effects, baseline patent intensity and income controls do not identify causal or policy effects. Reverse timing, anticipation, industrial composition, and common technology shocks remain.",
    "A prior IESET business-enterprise R&D to resident-patent study and older patent candidates were visible before selection of this family. The two-test Bonferroni gate is local, not corpus-wide selection control or independent replication.",
    "High-tech export share was screened from treatment values only and rejected for concentrated residual variation; no patent outcome values or null masks were used to choose this family.",
    "No causal, policy, school-score, position, or featured credit is permitted.",
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
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/growth/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(key: str, case: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
        "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": case["meaningful_beta"],
        "min_complete_rows": case["min_rows"], "min_complete_countries": case["min_countries"],
        "min_years_per_country": MIN_YEARS,
        "material_exposure_min": case["material_min"],
        "min_material_rows_or_varying_countries": case["min_material_rows"],
        "min_material_countries": case["min_material_countries"],
        "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE,
        "max_top_country_residual_x_share": MAX_TOP_COUNTRY_RESIDUAL_X_SHARE,
        "expected_key_rows": case["expected_rows"],
        "expected_key_countries": case["expected_countries"],
        "roster_sha256": ROSTER_SHA,
        "source_files": {role: {field: SOURCES[role][field]
                                for field in ("path", "sha256", "manifest", "manifest_sha256")}
                         for role in (key, "patents", "population", "income")},
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }


def registration_commit() -> str:
    files = [RUNNER, PREREG, ROSTER]
    for case in CASES.values():
        files += [spec_rel(case), steelman_rel(case)]
    commits = {first_addition(relative) for relative in files}
    if len(commits) != 1:
        raise RuntimeError("family registration files lack one shared first-addition commit")
    revision = commits.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "associational"
                or spec.get("claim_direction") != "+"
                or spec.get("steelman") != steelman_rel(case)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != []
                or spec["falsification"]["threshold"] != threshold_for(key, case)):
            raise RuntimeError(f"frozen hypothesis spec mismatch: {key}")
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contains results")
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
        matches = [entry for entry in manifest.get("entries", [])
                   if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} tracked fetch entry mismatch")
        entry = matches[0]
        narrow[role] = {**source, "source_url": entry.get("source_url"),
                        "methodology_url": entry.get("methodology_url"),
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
                        "rows": entry.get("rows"), "frequency": entry.get("frequency"),
                        "units": entry.get("units")}
    return narrow


def wdi_keys(role: str) -> set[tuple[str, int]]:
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "indicator_id", "year"])
    if len(frame) != 17556 or not frame.indicator_id.eq("IP.PAT.RESD" if role == "patents" else source["series_id"]).all():
        raise RuntimeError(f"{role} raw row or indicator contract changed")
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate {role} country/year key")
    return {(str(c), int(y)) for c, y in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def exposure_values() -> dict[str, dict[tuple[str, int], float]]:
    internet = pd.read_parquet(ROOT / SOURCES["internet"]["path"],
                               columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(internet) != 17556 or not internet.indicator_id.eq("IT.NET.USER.ZS").all():
        raise RuntimeError("internet raw row or indicator contract changed")
    internet = internet.loc[internet.country_iso3.isin(COUNTRIES)].copy()
    if internet.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate internet country/year key")
    internet["value"] = pd.to_numeric(internet.value, errors="coerce")
    internet = internet.loc[np.isfinite(internet.value) & internet.value.between(0, 100)
                            & internet.obs_status.fillna("").astype(str).str.strip().eq("")]
    internet_values = {(str(c), int(y)): float(v)
                       for c, y, v in internet[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    rd = pd.read_parquet(ROOT / SOURCES["public_rd"]["path"],
                         columns=["freq", "sectperf", "unit", "geo_code", "period", "value"])
    if len(rd) != 43474:
        raise RuntimeError("Eurostat R&D row-count contract changed")
    rd = rd.loc[rd.freq.eq("A") & rd.sectperf.isin(["GOV", "HES"])
                & rd.unit.eq("PC_GDP") & rd.geo_code.isin(EURO_TO_ISO3)].copy()
    rd["country_iso3"] = rd.geo_code.map(EURO_TO_ISO3)
    rd["year"] = pd.to_numeric(rd.period, errors="raise").astype(int)
    rd["value"] = pd.to_numeric(rd.value, errors="coerce")
    if rd.duplicated(["country_iso3", "year", "sectperf"]).any():
        raise RuntimeError("duplicate selected Eurostat R&D key")
    by_sector = rd.pivot(index=["country_iso3", "year"], columns="sectperf", values="value")
    by_sector = by_sector.loc[np.isfinite(by_sector.GOV) & np.isfinite(by_sector.HES)
                              & by_sector.GOV.between(0, 100) & by_sector.HES.between(0, 100)].copy()
    by_sector["x"] = by_sector.GOV + by_sector.HES
    by_sector = by_sector.loc[by_sector.x.between(0, 100)]
    public_rd_values = {(str(c), int(y)): float(v)
                        for (c, y), v in by_sector.x.items()}
    return {"internet": internet_values, "public_rd": public_rd_values}


def concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    fit = smf.ols("x ~ C(country_iso3) + C(year)", data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * len(squared)))
    top_row = float(np.sort(squared)[-top_n:].sum() / total)
    top_country = float(pd.DataFrame({"country": panel.country_iso3.to_numpy(), "squared": squared})
                        .groupby("country").squared.sum().max() / total)
    return top_row, top_country


def build_roster() -> tuple[dict[str, list[tuple[str, int]]], dict[str, dict[str, Any]]]:
    exposures = exposure_values()  # treatment values only
    keys = {role: wdi_keys(role) for role in ("patents", "population", "income")}
    rows_by_case, metrics = {}, {}
    for key, case in CASES.items():
        values = exposures[key]
        candidates = []
        for country in sorted(COUNTRIES):
            for year in range(T_START, T_END + 1):
                if (country, year) not in values:
                    continue
                if key == "internet" and (country, year - 2) not in values:
                    continue
                if any((country, year) not in keys[role] for role in ("patents", "population", "income")):
                    continue
                if any((country, year + HORIZON) not in keys[role] for role in ("patents", "population")):
                    continue
                candidates.append((country, year))
        counts = Counter(country for country, _ in candidates)
        selected = sorted(((country, year) for country, year in candidates
                           if counts[country] >= MIN_YEARS), key=lambda row: (row[1], row[0]))
        if len(selected) != case["expected_rows"] or len({country for country, _ in selected}) != case["expected_countries"]:
            raise RuntimeError(f"{key} treatment/key-only envelope changed")
        panel = pd.DataFrame([{"country_iso3": country, "year": year,
                               "x": values[(country, year)] - values[(country, year - 2)]
                               if key == "internet" else values[(country, year)]}
                              for country, year in selected])
        shares = concentration(panel)
        if shares is None or shares[0] > MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE or shares[1] > MAX_TOP_COUNTRY_RESIDUAL_X_SHARE:
            raise RuntimeError(f"{key} treatment-only concentration gate failed")
        material_rows = (int(panel.x.abs().ge(case["material_min"]).sum()) if key == "internet"
                         else int(panel.groupby("country_iso3").x.agg(lambda values: values.max() - values.min())
                                  .ge(case["material_min"]).sum()))
        metrics[key] = {"key_rows": len(selected), "key_countries": case["expected_countries"],
                        "t_years": [min(y for _, y in selected), max(y for _, y in selected)],
                        "treatment_only_material_rows_or_varying_countries": material_rows,
                        "treatment_only_top_one_percent_residual_x_share": shares[0],
                        "treatment_only_top_country_residual_x_share": shares[1]}
        rows_by_case[key] = selected
    return rows_by_case, metrics


def load_roster() -> dict[str, list[tuple[str, int]]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen key roster SHA mismatch")
    raw = (ROOT / ROSTER).read_bytes()
    if not raw.startswith(b"case_id,country_iso3,year\n"):
        raise RuntimeError("frozen key roster header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    result = {key: [] for key in CASES}
    for record in records:
        if record["case_id"] not in result:
            raise RuntimeError("unknown key roster case")
        result[record["case_id"]].append((record["country_iso3"], int(record["year"])))
    return result


def key_preflight() -> dict[str, Any]:
    generated, metrics = build_roster()
    if generated != load_roster():
        raise RuntimeError("treatment/key-only envelope differs from frozen roster")
    return {"treatment_values_read": True, "patent_values_read": False,
            "patent_null_masks_read": False, "population_values_read": False,
            "income_values_read": False, "exact_calendar_join": True,
            "roster_sha256": ROSTER_SHA, "cases": metrics}


def lock_payload(registration: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    registration = registration_commit()
    narrow, preflight = check_sources(), key_preflight()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(registration, narrow, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening outcome values")


def check_source_lock(registration: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, narrow, preflight):
        raise RuntimeError("source lock differs from frozen registration or preflight")
    commit = first_addition(LOCK)
    if commit == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains results")
    return commit


def measured_series(role: str, positive: bool) -> dict[tuple[str, int], float]:
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES)].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate measured {role} key")
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    frame = frame.loc[frame.obs_status.fillna("").astype(str).str.strip().eq("")
                      & np.isfinite(frame.value) & (frame.value.gt(0) if positive else frame.value.ge(0))]
    return {(str(c), int(y)): float(v)
            for c, y, v in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First outcome/control numeric and null access; lock chronology already checked."""
    exposures = exposure_values()
    patents = measured_series("patents", positive=False)
    population = measured_series("population", positive=True)
    income = measured_series("income", positive=True)
    panels = {}
    for key, case in CASES.items():
        rows = []
        for country, year in roster[key]:
            base = (country, year)
            later = (country, year + HORIZON)
            if any(base not in src for src in (patents, population, income)) or any(later not in src for src in (patents, population)):
                continue
            baseline = math.log1p(1_000_000.0 * patents[base] / population[base])
            forward = math.log1p(1_000_000.0 * patents[later] / population[later])
            x = (exposures[key][base] - exposures[key][(country, year - 2)]
                 if key == "internet" else exposures[key][base])
            rows.append({"country_iso3": country, "year": year, "x": x,
                         "patent_growth": forward - baseline,
                         "baseline_log_patents_pm": baseline,
                         "log_income_pc": math.log(income[base])})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "patent_growth",
                                            "baseline_log_patents_pm", "log_income_pc"])
        before = len(panel)
        if before:
            counts = panel.country_iso3.value_counts()
            panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        if key == "internet" and len(panel):
            material_rows = int(panel.x.abs().ge(case["material_min"]).sum())
            material_countries = int(panel.loc[panel.x.abs().ge(case["material_min"]), "country_iso3"].nunique())
        elif key == "public_rd" and len(panel):
            spans = panel.groupby("country_iso3").x.agg(lambda values: values.max() - values.min())
            material_rows = material_countries = int(spans.ge(case["material_min"]).sum())
        else:
            material_rows = material_countries = 0
        gate = {"key_roster_rows": len(roster[key]), "complete_pairs_before_five_year_floor": before,
                "complete_rows": len(panel), "complete_countries": int(panel.country_iso3.nunique()) if len(panel) else 0,
                "material_rows_or_varying_countries": material_rows,
                "material_countries": material_countries,
                "outcome_values_read_after_lock": True}
        panels[key] = (panel, gate)
    return panels


def estimate(panel: pd.DataFrame, gate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    if (gate["complete_rows"] < case["min_rows"] or gate["complete_countries"] < case["min_countries"]
            or gate["material_rows_or_varying_countries"] < case["min_material_rows"]
            or gate["material_countries"] < case["min_material_countries"]):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen sample or material-exposure floor failed", "primary": None}
    shares = concentration(panel)
    if shares is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "no finite residual exposure variation", "primary": None}
    gate["top_one_percent_residual_x_share"], gate["top_country_residual_x_share"] = shares
    if shares[0] > MAX_TOP_ONE_PERCENT_RESIDUAL_X_SHARE or shares[1] > MAX_TOP_COUNTRY_RESIDUAL_X_SHARE:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residual-exposure concentration gate failed", "primary": None}
    model = smf.ols("patent_growth ~ x + baseline_log_patents_pm + log_income_pc + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "fixed-effect design lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite clustered uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(0.9975, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite country-cluster t inference", "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.995,
               "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS with baseline patent and income controls; country-cluster CR1, Student t(G-1)"}
    meaningful = case["meaningful_beta"]
    if beta >= meaningful and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive descriptive association clears prespecified magnitude and family significance"
    elif beta <= -meaningful and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite descriptive association clears prespecified magnitude and family significance"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any],
                     registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hypothesis_id = case["id"]
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    inputs = {role: SOURCES[role] for role in (key, "patents", "population", "income")}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hypothesis_id, "path": spec_rel(case), "topic": "growth"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 2, "key_roster": ROSTER,
                                  "key_roster_sha256": ROSTER_SHA, "steelman": steelman_rel(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": inputs, "sample": gate}, "results": {"primary": primary},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": hypothesis_id, "family_id": FAMILY,
                   "verdict": verdict, "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
                   "primary": primary, "p_max_two_sided_bonferroni": P_MAX,
                   "meaningful_beta_min_abs": case["meaningful_beta"],
                   "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
            f"Exposure: {case['label']}; outcome: two-year change in log(1 + WIPO-origin resident "
            f"patent applications per million residents). Key-only bound: {case['expected_rows']} "
            f"country-years / {case['expected_countries']} countries. Complete pairs: "
            f"{gate['complete_rows']} / {gate['complete_countries']}.\n")
    if primary is not None:
        card += (f"\nBeta={primary['coefficient']:+.6g} log outcome units per 1 exposure unit; "
                 f"country-cluster SE={primary['std_error']:.6g}; "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}; "
                 f"99.5% CI={primary['confidence_interval']}.\n")
    card += ("\nTwo prespecified tests; Bonferroni alpha 0.01, each two-sided p<=0.005, "
             f"and absolute beta>={case['meaningful_beta']} required for direction. "
             "Descriptive calibration only, without causal, policy, school or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hypothesis_id, "family_id": FAMILY, "verdict": verdict,
             "primary": primary}
    coefficients = [{"term": "x", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# Internet uptake and public-sector performed R&D to resident patenting: two-test result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "Both tests belong to the same two-sided Bonferroni family (alpha 0.01; p<=0.005 each).", "",
             "| Exposure | Verdict | Complete pairs / countries | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['complete_rows']} / {gate['complete_countries']} | {beta} | {p} |")
    lines += ["", "The outcome is a two-year forward change in log(1 + WIPO-origin resident patent applications per million). Internet exposure is a two-year percentage-point uptake change; R&D exposure is GOV+HES performed R&D as a GDP percentage-point level. Coefficients are not directly comparable.",
              "", "These are descriptive measured associations. Earlier IESET R&D/patent and innovation studies were visible before this family's selection; the cutoff is local, not archive-wide selection control. No causal, policy, school, position or featured credit.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("family result artifacts already exist")
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
            "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows",
            "n_countries", "df_inference", "model_rank", "method"]).to_parquet(folder / "coefficients.parquet", index=False)
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
            raise AssertionError(f"{label}: list length mismatch")
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
        equal_close(saved, payload["diagnostics"], f"{key}.diagnostics")
        equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"], f"{key}.manifest")
        equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"], f"{key}.packet")
        equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"], f"{key}.chart")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != payload["card"]
                or (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"{key}: text artifact mismatch")
        equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                    payload["coefficients"], f"{key}.coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    for action in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        actions.add_argument(f"--{action}", action="store_true")
    args = parser.parse_args()
    narrow = check_sources()
    if args.check_sources:
        print("all five exact source and fetch-manifest hashes match; patent values unopened")
        return 0
    preflight = key_preflight()
    if args.preflight:
        print(json.dumps(preflight, indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    registration = registration_commit()
    lock_commit = check_source_lock(registration, narrow, preflight)
    panels = measured_panels(load_roster())
    results = {key: estimate(*panels[key], CASES[key]) for key in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        print(summary_text(results, registration, lock_commit))
    else:
        verify_artifacts(results, registration, lock_commit)
        print("exact result artifact replay passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
