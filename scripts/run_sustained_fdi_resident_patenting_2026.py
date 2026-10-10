#!/usr/bin/env python3
"""Guarded, one-test sustained-FDI to resident-patenting calibration.

Preflight projects only patent keys. First patent value/null/status decoding requires
an immutable preregistration commit and a later, separately committed source lock.
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
ID = "sustained_fdi_resident_patenting_forward_2026"
FAMILY = "sustained_fdi_resident_patenting_forward_2026_10_10"
RUNNER = "scripts/run_sustained_fdi_resident_patenting_2026.py"
TEST = "tests/test_sustained_fdi_resident_patenting_2026.py"
SPEC = f"hypotheses/trade/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PREREG = "engine/audits/sustained_fdi_resident_patenting_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/fdi_patenting_2026_key_roster.csv"
ROSTER_SHA = "70ceb9453eabd876e0fa173188675eaf819b919dc60a7990fc64320a955500a4"
LOCK = "data/pinned_evidence/fdi_patenting_2026.manifest.json"
RUN = f"engine/runs/{ID}"
SUMMARY = "engine/audits/sustained_fdi_resident_patenting_results_2026-10-10.md"
T_START, T_END = 2004, 2019
POPULATION_FLOOR, FDI_EVENT_PP = 5_000_000, 3.0
COHORT = tuple(
    "AFG AGO ARG AUS AUT AZE BDI BEL BEN BFA BGD BGR BLR BOL BRA CAN CHE CHL CHN CIV CMR COD COL CUB "
    "CZE DEU DNK DOM DZA ECU EGY ESP ETH FIN FRA GBR GHA GIN GRC GTM HKG HND HTI HUN IDN IND IRN "
    "IRQ ISR ITA JOR JPN KAZ KEN KGZ KHM KOR LAO LBY LKA MAR MDG MEX MLI MMR MOZ MWI MYS NER NGA "
    "NIC NLD NPL PAK PER PHL PNG POL PRK PRT PRY ROU RUS RWA SAU SDN SEN SLE SLV SOM SRB SSD SVK "
    "SWE SYR TCD TGO THA TJK TUN TUR TZA UGA UKR USA UZB VEN VNM YEM ZAF ZMB ZWE".split()
)
assert len(COHORT) == len(set(COHORT)) == 112 and list(COHORT) == sorted(COHORT)
ROSTER_ROWS, ROSTER_COUNTRIES = 1723, 110
PREFLIGHT_EVENT_ROWS, PREFLIGHT_EVENT_COUNTRIES, PREFLIGHT_SWITCHERS = 702, 74, 66
MIN_ROWS, MIN_COUNTRIES, MIN_YEARS = 400, 35, 5
MIN_EVENTS, MIN_EVENT_COUNTRIES, MIN_SWITCHERS = 100, 25, 25
MAX_COUNTRY_SHARE, MAX_FIVE_COUNTRY_SHARE, MAX_TOP_ROW_SHARE = 0.15, 0.35, 0.20
P_MAX, MEANINGFUL_BETA = 0.01, 0.05
WDI_200056 = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
WDI_200056_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
WDI_210519 = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
WDI_210519_SHA = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"
SOURCES = {
    "fdi": {
        "publisher": "world_bank_wdi", "series_id": "BX.KLT.DINV.WD.GD.ZS",
        "path": "data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-05-05T195106Z.parquet",
        "sha256": "626691877048dc78d5f7b4f6948dd680d3e111aedff252d1286ca2fd40b8abc5",
        "manifest": WDI_200056, "manifest_sha256": WDI_200056_SHA,
    },
    "patents": {
        "publisher": "world_bank_wdi", "series_id": "IP.PAT.RESD",
        "path": "data/vintages/world_bank_wdi/IP.PAT.RESD@2026-05-05T203341Z.parquet",
        "sha256": "617c357fceaff7a4f21710f710426f9ad2c01e710e9c0432b9085a41e7b887fe",
        "manifest": WDI_210519, "manifest_sha256": WDI_210519_SHA,
    },
    "population": {
        "publisher": "world_bank_wdi", "series_id": "SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest": WDI_200056, "manifest_sha256": WDI_200056_SHA,
    },
    "gdp_pc": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": WDI_200056, "manifest_sha256": WDI_200056_SHA,
    },
    "gdp_growth": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
        "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
        "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
        "manifest": WDI_200056, "manifest_sha256": WDI_200056_SHA,
    },
}
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": P_MAX, "p_max_two_sided": P_MAX,
    "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    "position_score_credit": 0, "school_score_eligible": False,
    "school_score_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "Net FDI/GDP includes acquisitions, affiliate debt, reinvestment, disinvestment, and GDP-denominator effects; it is not greenfield investment.",
    "Resident patent applications are filings, not grants or patent quality; foreign-parent filings may occur abroad.",
    "Missing patent-office entries cannot be assumed to equal zero; office reporting and IP law can change counts.",
    "Country/year effects, baseline intensity, GDP controls, and forward timing do not remove reverse selection or time-varying confounding.",
    "The local one-test p threshold does not correct selection across the wider IESET archive.",
    "No causal, policy, position, school-score, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[0]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def threshold() -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 1, "family_alpha": P_MAX,
        "p_max_two_sided": P_MAX, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "min_complete_rows": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
        "min_years_per_country": MIN_YEARS, "min_exposed_rows": MIN_EVENTS,
        "min_exposed_countries": MIN_EVENT_COUNTRIES,
        "min_within_country_switchers": MIN_SWITCHERS,
        "max_top_country_residual_x_share": MAX_COUNTRY_SHARE,
        "max_top_five_country_residual_x_share": MAX_FIVE_COUNTRY_SHARE,
        "max_top_one_percent_rows_residual_x_share": MAX_TOP_ROW_SHARE,
        "event_mean_fdi_share_gdp_threshold_pp": FDI_EVENT_PP,
        "population_floor_2004": POPULATION_FLOOR,
        "expected_baseline_population_cohort": len(COHORT),
        "expected_key_rows": ROSTER_ROWS, "expected_key_countries": ROSTER_COUNTRIES,
        "expected_treatment_event_rows": PREFLIGHT_EVENT_ROWS,
        "expected_treatment_event_countries": PREFLIGHT_EVENT_COUNTRIES,
        "expected_treatment_switcher_countries": PREFLIGHT_SWITCHERS,
        "roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {field: source[field] for field in ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()
        },
        "causal_credit": 0, "policy_score_eligible": False,
        "policy_score_credit": 0, "school_score_eligible": False,
        "school_score_credit": 0, "position_score_credit": 0,
        "featured_eligible": False,
    }


def source_pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(tuple(sorted({item["source"] for item in variables.get(role, [])
                               if isinstance(item, dict) and item.get("source")}))
                 for role in ("treatment", "outcome"))


def verify_spec() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational"
            or spec.get("claim_direction") != "+"
            or spec.get("sample", {}).get("countries") != list(COHORT)
            or spec.get("sample", {}).get("period") != [T_START, T_END]
            or spec.get("scope", {}).get("countries") != list(COHORT)
            or spec.get("scope", {}).get("period") != [T_START, T_END + 3]
            or spec.get("scope", {}).get("outcome_dim") != ["industrial_capability"]
            or spec.get("falsification", {}).get("threshold") != threshold()
            or spec.get("steelman") != STEELMAN
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []):
        raise RuntimeError("frozen FDI/patent hypothesis contract mismatch")
    expected = (("world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",),
                ("world_bank_wdi:IP.PAT.RESD",))
    if source_pair(spec) != expected:
        raise RuntimeError("registered FDI/patent source pair changed")
    for path in (ROOT / "hypotheses").rglob("*.yaml"):
        if path == ROOT / SPEC:
            continue
        try:
            other = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            continue
        if other.get("status") == "pre_registered" and source_pair(other) == expected:
            raise RuntimeError(f"duplicate registered FDI/patent source pair: {path}")


def check_sources() -> dict[str, dict[str, Any]]:
    """Check exact bytes and extract only narrow public source metadata."""
    narrow: dict[str, dict[str, Any]] = {}
    for role, source in SOURCES.items():
        raw_path, manifest_path = ROOT / source["path"], ROOT / source["manifest"]
        if not raw_path.is_file() or sha256(raw_path) != source["sha256"]:
            raise RuntimeError(f"{role} source SHA-256 mismatch or absent")
        if not manifest_path.is_file() or sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch or absent")
        manifest = yaml.safe_load(manifest_path.read_text())
        matches = [entry for entry in manifest.get("entries", [])
                   if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} fetch-manifest entry mismatch")
        entry = matches[0]
        narrow[role] = {
            **source, "source_url": entry.get("source_url"),
            "methodology_url": entry.get("methodology_url"),
            "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
            "rows": entry.get("rows"), "frequency": entry.get("frequency"),
            "units": entry.get("units"),
        }
    return narrow


def read_control_values(role: str) -> dict[tuple[str, int], float]:
    """This helper expressly rejects patent-value access in every preflight."""
    if role not in ("fdi", "population", "gdp_pc", "gdp_growth"):
        raise RuntimeError("selected patent value access is forbidden before source lock")
    source = SOURCES[role]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "indicator_id", "year", "value"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError(f"{role} physical WDI indicator/row-count mismatch")
    frame = frame.loc[frame.country_iso3.isin(COHORT)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"{role} duplicate country/year key")
    return {(str(country), int(year)): float(value)
            for country, year, value in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}


def read_patent_keys() -> set[tuple[str, int]]:
    """Only this three-column projection is permitted before source lock."""
    source = SOURCES["patents"]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "indicator_id", "year"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError("patent key-only physical WDI contract changed")
    frame = frame.loc[frame.country_iso3.isin(COHORT)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate patent country/year key")
    return {(str(country), int(year))
            for country, year in frame[["country_iso3", "year"]].itertuples(index=False, name=None)}


def event_at(controls: dict[str, dict[tuple[str, int], float]],
             country: str, year: int) -> tuple[float, int] | None:
    values = [controls["fdi"].get((country, year - lag), math.nan) for lag in (2, 1, 0)]
    if not all(math.isfinite(value) for value in values):
        return None
    mean = sum(values) / 3.0
    return mean, int(mean >= FDI_EVENT_PP)


def generated_roster(controls: dict[str, dict[tuple[str, int], float]],
                     patent_keys: set[tuple[str, int]]) -> list[tuple[str, int]]:
    population = controls["population"]
    if any(not math.isfinite(population.get((country, 2004), math.nan))
           or population[(country, 2004)] < POPULATION_FLOOR for country in COHORT):
        raise RuntimeError("fixed 2004 population cohort changed")
    rows = []
    for country in COHORT:
        for year in range(T_START, T_END + 1):
            exposure = event_at(controls, country, year)
            income = controls["gdp_pc"].get((country, year), math.nan)
            growth = controls["gdp_growth"].get((country, year), math.nan)
            pop_now = population.get((country, year), math.nan)
            pop_forward = population.get((country, year + 3), math.nan)
            if (exposure is not None
                    and all(math.isfinite(value) for value in (income, growth, pop_now, pop_forward))
                    and income > 0 and pop_now > 0 and pop_forward > 0
                    and (country, year) in patent_keys
                    and (country, year + 3) in patent_keys):
                rows.append((country, year))
    return rows


def frozen_roster() -> list[tuple[str, int]]:
    path = ROOT / ROSTER
    raw = path.read_bytes()
    if sha256(path) != ROSTER_SHA or not raw.startswith(b"country_iso3,treatment_year\n"):
        raise RuntimeError("fixed key-roster SHA/header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    if any(set(record) != {"country_iso3", "treatment_year"} for record in records):
        raise RuntimeError("fixed key-roster columns changed")
    rows = [(record["country_iso3"], int(record["treatment_year"])) for record in records]
    if (len(rows) != ROSTER_ROWS or len({country for country, _ in rows}) != ROSTER_COUNTRIES
            or len(set(rows)) != len(rows) or rows != sorted(rows)
            or any(country not in COHORT or not T_START <= year <= T_END
                   for country, year in rows)):
        raise RuntimeError("fixed key-roster size, order, or country/year contract mismatch")
    return rows


def residual_shares(panel: pd.DataFrame, *, include_baseline: bool) -> tuple[float, float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    rhs = "log_gdp_pc + gdp_growth + C(country_iso3) + C(year)"
    if include_baseline:
        rhs = "baseline_log_patent_rate + " + rhs
    model = smf.ols("x ~ " + rhs, data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return None
    squared = np.square(np.asarray(model.fit().resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 1e-12:
        return None
    by_country = pd.DataFrame({"country": panel.country_iso3.to_numpy(), "square": squared})
    by_country = by_country.groupby("country").square.sum().sort_values(ascending=False)
    top_n = max(1, math.ceil(0.01 * len(squared)))
    return (float(by_country.iloc[0] / total),
            float(by_country.iloc[:5].sum() / total),
            float(np.sort(squared)[-top_n:].sum() / total))


def preflight() -> tuple[dict[str, dict[tuple[str, int], float]], dict[str, Any]]:
    verify_spec()
    controls = {role: read_control_values(role)
                for role in ("fdi", "population", "gdp_pc", "gdp_growth")}
    keys = read_patent_keys()
    generated = generated_roster(controls, keys)
    if generated != frozen_roster():
        raise RuntimeError("treatment/control and patent-key envelope differs from fixed roster")
    rows = []
    for country, year in generated:
        mean, event = event_at(controls, country, year)  # guaranteed by generated_roster
        rows.append({"country_iso3": country, "year": year, "x": event,
                     "fdi3_mean_pp": mean,
                     "log_gdp_pc": math.log(controls["gdp_pc"][(country, year)]),
                     "gdp_growth": controls["gdp_growth"][(country, year)]})
    panel = pd.DataFrame(rows)
    exposed = panel.loc[panel.x.eq(1)]
    switchers = int(panel.groupby("country_iso3").x.nunique().eq(2).sum())
    if (len(panel) != ROSTER_ROWS or panel.country_iso3.nunique() != ROSTER_COUNTRIES
            or len(exposed) != PREFLIGHT_EVENT_ROWS
            or exposed.country_iso3.nunique() != PREFLIGHT_EVENT_COUNTRIES
            or switchers != PREFLIGHT_SWITCHERS):
        raise RuntimeError("frozen treatment-only event counts changed")
    shares = residual_shares(panel, include_baseline=False)
    if shares is None:
        raise RuntimeError("treatment/control-only FDI event is not identifiable")
    report = {
        "key_rows_upper_bound": ROSTER_ROWS,
        "key_countries_upper_bound": ROSTER_COUNTRIES,
        "baseline_population_cohort": len(COHORT),
        "treatment_control_valid_rows": len(panel),
        "treatment_event_rows": len(exposed),
        "treatment_event_countries": int(exposed.country_iso3.nunique()),
        "treatment_switcher_countries": switchers,
        "treatment_control_top_country_residual_x_share": round(shares[0], 10),
        "treatment_control_top_five_country_residual_x_share": round(shares[1], 10),
        "treatment_control_top_one_percent_rows_residual_x_share": round(shares[2], 10),
        "roster_sha256": ROSTER_SHA,
        "selected_patent_columns_decoded": ["country_iso3", "indicator_id", "year"],
        "patent_values_decoded": False, "patent_null_masks_decoded": False,
        "patent_status_decoded": False, "patent_complete_case_count_known": False,
    }
    return controls, report


def registration_commit() -> str:
    files = (RUNNER, TEST, SPEC, STEELMAN, PREREG, ROSTER)
    commits = {first_addition(relative) for relative in files}
    if len(commits) != 1:
        raise RuntimeError("preregistration files lack one shared first-addition commit")
    revision = commits.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN).strip():
        raise RuntimeError("measured results existed in preregistration commit")
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock existed in preregistration commit")
    return revision


def lock_payload(revision: str, sources: dict[str, dict[str, Any]], key: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "preregistration_commit": revision,
        "sources": sources, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
        "key_preflight": key, "patent_values_opened_before_lock": False,
        "patent_null_masks_opened_before_lock": False,
        "patent_status_opened_before_lock": False,
        "whole_fetch_manifests_copied": False,
    }


def write_source_lock(revision: str, sources: dict[str, dict[str, Any]], key: dict[str, Any]) -> None:
    if (ROOT / RUN).exists() or (ROOT / SUMMARY).exists():
        raise RuntimeError("measured result artifacts exist before source lock")
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(revision, sources, key), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit this narrow lock separately before opening patent measurements")


def check_source_lock(revision: str, sources: dict[str, dict[str, Any]],
                      key: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if not path.is_file() or json.loads(path.read_text()) != lock_payload(revision, sources, key):
        raise RuntimeError("source lock absent or changed")
    lock_commit = first_addition(LOCK)
    if lock_commit == revision or subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, lock_commit], cwd=ROOT,
        check=False,
    ).returncode:
        raise RuntimeError("source-lock commit must follow preregistration")
    committed_unchanged(LOCK, lock_commit)
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN).strip():
        raise RuntimeError("measured results existed in source-lock commit")
    return lock_commit


def patent_values_after_lock(revision: str, sources: dict[str, dict[str, Any]],
                             key: dict[str, Any]) -> dict[tuple[str, int], tuple[float, str]]:
    """The first patent measurement projection has its own chronology guard."""
    check_source_lock(revision, sources, key)
    source = SOURCES["patents"]
    frame = pd.read_parquet(ROOT / source["path"],
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(frame) != 17556 or not frame.indicator_id.eq(source["series_id"]).all():
        raise RuntimeError("patent measurement WDI physical contract changed")
    frame = frame.loc[frame.country_iso3.isin(COHORT)].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate patent country/year key")
    frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    frame["obs_status"] = frame.obs_status.fillna("").astype(str).str.strip()
    return {(str(country), int(year)): (float(value), str(status))
            for country, year, value, status in frame[
                ["country_iso3", "year", "value", "obs_status"]
            ].itertuples(index=False, name=None)}


def build_panel(roster: list[tuple[str, int]],
                controls: dict[str, dict[tuple[str, int], float]],
                patents: dict[tuple[str, int], tuple[float, str]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    bad_status, bad_measurement = 0, 0
    population = controls["population"]
    for country, year in roster:
        baseline = patents.get((country, year))
        forward = patents.get((country, year + 3))
        if baseline is None or forward is None:
            bad_measurement += 1
            continue
        if baseline[1] or forward[1]:
            bad_status += 1
            continue
        b_count, f_count = baseline[0], forward[0]
        b_pop = population[(country, year)]
        f_pop = population[(country, year + 3)]
        if not (math.isfinite(b_count) and math.isfinite(f_count)
                and b_count >= 0 and f_count >= 0
                and math.isfinite(b_pop) and math.isfinite(f_pop)
                and b_pop > 0 and f_pop > 0):
            bad_measurement += 1
            continue
        b_rate = math.log1p(1_000_000 * b_count / b_pop)
        f_rate = math.log1p(1_000_000 * f_count / f_pop)
        _, event = event_at(controls, country, year)
        rows.append({
            "country_iso3": country, "year": year, "x": event,
            "outcome_change": f_rate - b_rate,
            "baseline_log_patent_rate": b_rate,
            "log_gdp_pc": math.log(controls["gdp_pc"][(country, year)]),
            "gdp_growth": controls["gdp_growth"][(country, year)],
        })
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "outcome_change",
                                        "baseline_log_patent_rate", "log_gdp_pc", "gdp_growth"])
    before_floor = len(panel)
    if before_floor:
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    exposed = panel.loc[panel.x.eq(1)]
    switchers = (int(panel.groupby("country_iso3").x.nunique().eq(2).sum())
                 if len(panel) else 0)
    gate = {
        "key_roster_rows": len(roster),
        "complete_pairs_before_country_five_year_floor": before_floor,
        "dropped_nonblank_patent_status_pairs": bad_status,
        "dropped_missing_or_invalid_patent_pairs": bad_measurement,
        "complete_rows": len(panel),
        "complete_countries": int(panel.country_iso3.nunique()) if len(panel) else 0,
        "min_complete_years_retained_country": int(panel.country_iso3.value_counts().min()) if len(panel) else 0,
        "event_rows": len(exposed),
        "event_countries": int(exposed.country_iso3.nunique()) if len(exposed) else 0,
        "within_country_switchers": switchers,
        "patent_measurements_decoded_after_lock": True,
    }
    return panel, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["complete_rows"] < MIN_ROWS or gate["complete_countries"] < MIN_COUNTRIES
            or gate["min_complete_years_retained_country"] < MIN_YEARS
            or gate["event_rows"] < MIN_EVENTS
            or gate["event_countries"] < MIN_EVENT_COUNTRIES
            or gate["within_country_switchers"] < MIN_SWITCHERS):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case, event, or switcher floor failed", "primary": None}
    shares = residual_shares(panel, include_baseline=True)
    if shares is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "residualized FDI event is unidentified", "primary": None}
    gate["top_country_residual_x_share"] = shares[0]
    gate["top_five_country_residual_x_share"] = shares[1]
    gate["top_one_percent_rows_residual_x_share"] = shares[2]
    if (shares[0] > MAX_COUNTRY_SHARE or shares[1] > MAX_FIVE_COUNTRY_SHARE
            or shares[2] > MAX_TOP_ROW_SHARE):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residualized FDI-event concentration gate failed", "primary": None}
    model = smf.ols(
        "outcome_change ~ x + baseline_log_patent_rate + log_gdp_pc + gdp_growth "
        "+ C(country_iso3) + C(year)", data=panel,
    )
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fixed-effect design is rank deficient", "primary": None}
    groups = int(panel.country_iso3.nunique())
    try:
        fit = model.fit(cov_type="cluster",
                        cov_kwds={"groups": panel.country_iso3,
                                   "use_correction": True, "df_correction": True},
                        use_t=True)
        beta, se = float(fit.params["x"]), float(fit.bse["x"])
        p = float(2 * student_t.sf(abs(beta / se), groups - 1))
        critical = float(student_t.ppf(1 - P_MAX / 2, groups - 1))
    except (ValueError, FloatingPointError, ZeroDivisionError, KeyError):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "country-cluster inference failed", "primary": None}
    if not all(math.isfinite(value) for value in (beta, se, p, critical)) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "country-cluster uncertainty is nonfinite or nonpositive", "primary": None}
    primary = {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 1 - P_MAX,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
        "model_rank": int(fit.model.rank),
        "method": "country/year FE OLS, baseline patent intensity and GDP controls; country-cluster CR1; Student t(G-1)",
    }
    if beta >= MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive association clears frozen magnitude and p gates"
    elif beta <= -MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "negative association clears frozen magnitude and p gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def payload(result: dict[str, Any], revision: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    vintages = list(SOURCES.values())
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC, "topic": "trade"},
        "preregistration": {"spec_commit": revision, "source_lock_commit": lock_commit,
                            "family_id": FAMILY, "family_size": 1,
                            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                            "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN,
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary}, "limitations": LIMITATIONS,
        "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": ID, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"],
        "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
        "primary": primary, "p_max_two_sided": P_MAX,
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "data_status": {"variables_missing": [], "input_vintages": vintages},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": vintages,
        "derived_panel": gate, "correction": CORRECTION,
    }
    card = (
        f"# Result card: {ID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Frozen preregistration: {revision}; source lock: {lock_commit}.\n\n"
        "Exposure: 3-year mean net FDI inflows >=3% GDP at t. Outcome: log(1 + resident "
        "patent applications per million) change from t to t+3. "
        f"Key-only upper bound: {ROSTER_ROWS} rows / {ROSTER_COUNTRIES} economies. "
        f"Complete pairs: {gate['complete_rows']} / {gate['complete_countries']}; "
        f"event rows: {gate['event_rows']}; switchers: {gate['within_country_switchers']}.\n"
    )
    if primary is not None:
        card += (
            f"\nBeta={primary['coefficient']:+.6g} log points per sustained-FDI event; "
            f"country-cluster SE={primary['std_error']:.6g}; "
            f"two-sided t p={primary['p_value_two_sided']:.6g}; "
            f"99% CI={primary['confidence_interval']}.\n"
        )
    card += (
        "\nOne prespecified test at two-sided p<=0.01; support requires beta>=+0.05 log points, "
        "refutation requires beta<=-0.05 log points and p<=0.01. Descriptive calibration only, without causal, "
        "policy, position, school or featured credit.\n"
    )
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n"
    )
    chart = {"hypothesis_id": ID, "family_id": FAMILY, "verdict": verdict,
             "primary": primary}
    coefficients = [{"term": "x", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart,
            "coefficients": coefficients}


def summary_text(result: dict[str, Any], revision: str, lock_commit: str) -> str:
    gate, primary = result["gate"], result["primary"]
    beta = f"{primary['coefficient']:+.6g}" if primary else "not estimated"
    p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
    return (
        "# Sustained FDI inflows and resident patent filings: one-test result\n\n"
        f"Preregistration {revision}; source lock {lock_commit}.\n\n"
        "| Verdict | Complete pairs / countries | Exposed rows / countries | Switchers | Beta | Two-sided p |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: |\n"
        f"| **{result['verdict']}** | {gate['complete_rows']} / {gate['complete_countries']} | "
        f"{gate['event_rows']} / {gate['event_countries']} | {gate['within_country_switchers']} | "
        f"{beta} | {p} |\n\n"
        "One fixed descriptive country/year FE test with baseline patent intensity and GDP controls, "
        "country-cluster CR1 and local two-sided p<=0.01. Positive support also needs beta>=0.05 "
        "log points; negative refutation likewise needs beta<=-0.05 log points and p<=0.01. "
        "This does not correct earlier IESET selection. "
        "No causal, policy, position, school-score, or featured credit.\n"
    )


def write_artifacts(result: dict[str, Any], revision: str, lock_commit: str) -> None:
    if (ROOT / RUN).exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("FDI/patent result artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    parts = payload(result, revision, lock_commit, stamp)
    folder = ROOT / RUN
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(parts["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(parts["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(parts["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(parts["card"])
    (folder / "replication.py").write_text(parts["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(parts["chart"], indent=2) + "\n")
    columns = ["term", "coefficient", "std_error", "p_value_two_sided", "confidence_level",
               "confidence_interval", "n_rows", "n_countries", "df_inference", "model_rank", "method"]
    pd.DataFrame(parts["coefficients"], columns=columns).to_parquet(
        folder / "coefficients.parquet", index=False
    )
    (ROOT / SUMMARY).write_text(summary_text(result, revision, lock_commit))


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(actual, np.ndarray):
        actual = actual.tolist()
    if isinstance(actual, np.generic):
        actual = actual.item()
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for name, value in expected.items():
            equal_close(actual[name], value, f"{label}.{name}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(
            float(actual), expected, rel_tol=1e-9, abs_tol=1e-11
        ):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(result: dict[str, Any], revision: str, lock_commit: str) -> None:
    folder = ROOT / RUN
    saved = json.loads((folder / "diagnostics.json").read_text())
    parts = payload(result, revision, lock_commit, saved["run_utc"])
    equal_close(saved, parts["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), parts["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), parts["packet"], "packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), parts["chart"], "chart")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != parts["card"]
            or (folder / "replication.py").read_text() != parts["wrapper"]):
        raise AssertionError("text artifact mismatch")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                parts["coefficients"], "coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(result, revision, lock_commit):
        raise AssertionError("summary differs from measured replay")


def execute_measured(mode: str) -> dict[str, Any]:
    sources = check_sources()
    controls, key = preflight()
    revision = registration_commit()
    lock_commit = check_source_lock(revision, sources, key)
    # patent_values_after_lock repeats the chronology check before the first value projection.
    patents = patent_values_after_lock(revision, sources, key)
    panel, gate = build_panel(frozen_roster(), controls, patents)
    result = estimate(panel, gate)
    if mode == "run":
        write_artifacts(result, revision, lock_commit)
    elif mode == "verify":
        verify_artifacts(result, revision, lock_commit)
    else:
        raise RuntimeError("unknown measured mode")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    for action in ("check-sources", "preflight", "lock", "run", "verify"):
        actions.add_argument(f"--{action}", action="store_true")
    args = parser.parse_args()
    if args.check_sources:
        check_sources()
        print("five exact source and fetch-manifest hashes match; patent measurements unopened")
        return 0
    if args.preflight:
        check_sources()
        _, key = preflight()
        print(json.dumps(key, indent=2, sort_keys=True))
        return 0
    if args.lock:
        sources = check_sources()
        _, key = preflight()
        revision = registration_commit()
        write_source_lock(revision, sources, key)
        return 0
    result = execute_measured("run" if args.run else "verify")
    print(result["verdict"], result["gate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
