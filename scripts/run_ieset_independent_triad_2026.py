#!/usr/bin/env python3
"""Frozen, descriptive, three-test independent-measure calibration family.

Preflight and source lock read source bytes, schemas, dimensions, and keys only.
Selected numeric values are opened only after distinct committed registration
and metadata-only lock. Verify regenerates every run artifact byte for byte.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pycountry
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "ieset_three_distinct_measurements_2026_10_10"
RUNNER = "scripts/run_ieset_independent_triad_2026.py"
PLAN = "engine/audits/ieset_independent_triad_2026_prereg_2026-10-10.md"
LOCK = "prereg/locks/ieset_independent_triad_2026.json"
SUMMARY = "engine/audits/ieset_independent_triad_2026_result_2026-10-10.md"
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)
ALPHA = 0.01
FAMILY_SIZE = 3
P_MAX = ALPHA / FAMILY_SIZE

MANIFESTS = {
    "irena": ("data/manifests/fetch_run_2026-05-05T212957Z.yaml",
              "d09b3816f3aee52ff2dfd7849289cde9b027ac9b72669c741423b3d7db209718"),
    "who": ("data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
            "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"),
    "wdi": ("data/manifests/fetch_run_2026-05-05T200056Z.yaml",
            "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"),
    "wdi_education": ("data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                      "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "ilo": ("data/manifests/fetch_run_2026-07-23T152624Z.yaml",
            "367fc796f8738908e3be217054f798e7684d29acee3d7304107136aecd05cdb6"),
}
SOURCES = {
    "solar": {
        "publisher": "irena", "series_id": "installed_capacity_solar_pv",
        "path": "data/vintages/irena/installed_capacity_solar_pv@2026-05-05T212314Z.parquet",
        "sha256": "5473eb1f2a057b831796c2c9394394c145c8ac14f74511841e8d4aeb74ddd205",
        "manifest_key": "irena", "area_col": "country", "years": (2010, 2015),
        "selector": {},
    },
    "population": {
        "publisher": "world_bank_wdi", "series_id": "SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest_key": "wdi", "area_col": "country_iso3", "years": (2010, 2015),
        "selector": {},
    },
    "pm25": {
        "publisher": "who_gho", "series_id": "SDGPM25",
        "path": "data/vintages/who_gho/SDGPM25@2026-04-30T114744Z.parquet",
        "sha256": "c2cf89f4ab41dc8c4b6b251e7b47651edcd07d826cb45a7d5e1d8ab0ee4c6e34",
        "manifest_key": "who", "area_col": "country_iso3", "years": (2010, 2015, 2019),
        "selector": {"SpatialDimType": "COUNTRY", "Dim1": "RESIDENCEAREATYPE_TOTL"},
    },
    "education": {
        "publisher": "world_bank_wdi", "series_id": "SE.XPD.TOTL.GD.ZS",
        "path": "data/vintages/world_bank_wdi/SE.XPD.TOTL.GD.ZS@2026-05-05T204028Z.parquet",
        "sha256": "0f21a848f064c16fce431b5425f5fb51519044c3e88256f329821b00504cc501",
        "manifest_key": "wdi_education", "area_col": "country_iso3",
        "years": (2005, 2015), "selector": {},
    },
    "female_lfp": {
        "publisher": "ilostat", "series_id": "EAP_2WAP_SEX_AGE_RT_A",
        "path": "data/vintages/ilostat/EAP_2WAP_SEX_AGE_RT_A@2026-07-23T152621Z.parquet",
        "sha256": "17e1ed07bf963364d866304ff6384dbbfb8bc06d5ba30b42a474098c2c54e395",
        "manifest_key": "ilo", "area_col": "country_iso3", "years": (2005, 2015, 2023),
        "selector": {
            "indicator": "EAP_2WAP_SEX_AGE_RT",
            "sex": "SEX_F", "classif1": "AGE_AGGREGATE_Y25-54",
        },
    },
    "inflation": {
        "publisher": "world_bank_wdi", "series_id": "FP.CPI.TOTL.ZG",
        "path": "data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-05-05T194737Z.parquet",
        "sha256": "dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0",
        "manifest_key": "wdi", "area_col": "country_iso3",
        "years": tuple(range(2005, 2014)), "selector": {},
    },
    "suicide": {
        "publisher": "who_gho", "series_id": "SDGSUICIDE",
        "path": "data/vintages/who_gho/SDGSUICIDE@2026-04-30T114842Z.parquet",
        "sha256": "72bf65650b553ac47df60cd624f21ad5d12c062694b3564ebbe300275ccec937",
        "manifest_key": "who", "area_col": "country_iso3", "years": (2014, 2021),
        "selector": {
            "SpatialDimType": "COUNTRY",
            "Dim1": "SEX_BTSX", "Dim2": "AGEGROUP_YEARSALL",
        },
    },
}
TESTS = {
    "solar_air": {
        "id": "irena_solar_who_pm25_forward_2026", "topic": "energy",
        "sources": ("solar", "population", "pm25"),
        "roster": "data/pinned_evidence/irena_solar_who_pm25_forward_2026_key_roster.csv",
        "roster_sha256": "ec601ededde0590ad2603dcdbb824626aab1ab0c81d005ba2668a7267a961107",
        "expected_sign": "-", "min_complete": 85, "min_material": 30,
        "material_exposure_min": 0.7, "min_exposure_iqr": 0.5,
        "max_exposure_share": 0.15, "max_outcome_share": 0.20,
        "max_loo_failures": 2, "min_loo_sign_share": 0.80,
        "meaningful_abs_beta": 0.5,
        "unit": "micrograms per cubic metre 2015-to-2019 PM2.5 change per +1 change in log1p(solar MW per million people)",
        "description": "Solar PV capacity per resident and later all-area ambient PM2.5",
        "limits": "IRENA records capacity, not electricity generation or fossil displacement. WHO PM2.5 is modelled population-weighted all-residence exposure, not the urban-only SDG series. Meteorology, transport, industry, transboundary pollution, population denominators, and secular trends can move PM2.5 independently of solar deployment.",
    },
    "education_lfp": {
        "id": "wdi_education_ilostat_female_lfp_forward_2026", "topic": "labour",
        "sources": ("education", "female_lfp"),
        "roster": "data/pinned_evidence/wdi_education_ilostat_female_lfp_forward_2026_key_roster.csv",
        "roster_sha256": "3d6430fc9cf9e5d7016db12afc962f2dd13dd57ec8494d06608229c612a251f1",
        "expected_sign": "+", "min_complete": 90, "min_material": 30,
        "material_exposure_min": 0.5, "min_exposure_iqr": 0.5,
        "max_exposure_share": 0.15, "max_outcome_share": 0.20,
        "max_loo_failures": 2, "min_loo_sign_share": 0.80,
        "meaningful_abs_beta": 1.0,
        "unit": "percentage-point 2015-to-2023 female prime-age labour participation change per +1 GDP-percentage-point education-spending change",
        "description": "Earlier public education-spending share and later female prime-age labour participation",
        "limits": "The WDI education spending ratio may change through GDP, composition, or accounting. ILO participation includes job seekers and may contain modelled estimates; it is not female employment or job quality. Childcare, norms, demographics, labour demand, and common shocks remain confounders.",
    },
    "inflation_suicide": {
        "id": "wdi_inflation_who_suicide_forward_2026", "topic": "healthcare",
        "sources": ("inflation", "suicide"),
        "roster": "data/pinned_evidence/wdi_inflation_who_suicide_forward_2026_key_roster.csv",
        "roster_sha256": "153a79fc73ea16c106bc669723e5d74ac60051f02748e8ccbfcec8ec2b556bc6",
        "expected_sign": "+", "min_complete": 110, "min_material": 30,
        "material_exposure_min": 5.0, "min_exposure_iqr": 0.25,
        "max_exposure_share": 0.15, "max_outcome_share": 0.20,
        "max_loo_failures": 2, "min_loo_sign_share": 0.80,
        "meaningful_abs_beta": 0.5,
        "unit": "suicide deaths per 100,000 people 2014-to-2021 change per +1 asinh(2005-to-2013 CPI-inflation SD / 5)",
        "description": "Earlier CPI-inflation volatility and later all-age suicide mortality",
        "limits": "CPI inflation is an economy-wide price index, not household hardship. WHO suicide mortality combines death registration and modelled adjustments and can vary with coding, age structure, mental-health services, conflict, and the 2020-2021 pandemic. A cross-country association cannot identify a mental-health effect of inflation.",
    },
}
for case in TESTS.values():
    case["spec"] = f"hypotheses/{case['topic']}/{case['id']}.yaml"
    case["steelman"] = f"hypotheses/steelman/{case['id']}.md"
    case["run"] = f"engine/runs/{case['id']}"
REGISTERED = tuple(
    path for case in TESTS.values()
    for path in (case["spec"], case["steelman"], case["roster"])
) + (PLAN, RUNNER)


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(path: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H",
                  "HEAD", "--", path).decode().splitlines()
    if len(commits) != 1:
        raise ValueError(f"Expected one first-addition commit for {path}: {commits}")
    return commits[0]


def committed_original(path: str, revision: str) -> None:
    content = (ROOT / path).read_bytes()
    if content != git("show", f"{revision}:{path}") or content != git("show", f"HEAD:{path}"):
        raise ValueError(f"Frozen file changed after registration: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise ValueError(f"Frozen file has uncommitted changes: {path}")


def ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def national(geo: object) -> bool:
    return isinstance(geo, str) and pycountry.countries.get(alpha_3=geo) is not None


def roster(case: dict) -> list[str]:
    path = ROOT / case["roster"]
    if file_sha(path) != case["roster_sha256"]:
        raise ValueError(f"Key-roster hash mismatch for {case['id']}")
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0] != ["country_iso3"]:
        raise ValueError("Invalid key-roster header")
    geos = [r[0] for r in rows[1:]]
    if geos != sorted(set(geos)) or not all(national(g) for g in geos):
        raise ValueError("Invalid national-area key roster")
    return geos


def threshold(case: dict) -> dict:
    return {
        "family_id": FAMILY, "family_size": FAMILY_SIZE,
        "family_alpha": ALPHA, "p_max_two_sided_bonferroni": P_MAX,
        "expected_sign": case["expected_sign"],
        "min_complete_national_areas": case["min_complete"],
        "min_material_exposure_areas": case["min_material"],
        "material_exposure_min": case["material_exposure_min"],
        "min_exposure_iqr": case["min_exposure_iqr"],
        "max_single_area_residualized_exposure_share": case["max_exposure_share"],
        "max_single_area_residualized_outcome_share": case["max_outcome_share"],
        "max_loo_fit_failures": case["max_loo_failures"],
        "min_loo_same_sign_share": case["min_loo_sign_share"],
        "meaningful_abs_beta": case["meaningful_abs_beta"],
        "roster_sha256": case["roster_sha256"],
        "source_files": {
            role: {
                "path": SOURCES[role]["path"], "sha256": SOURCES[role]["sha256"],
                "manifest": MANIFESTS[SOURCES[role]["manifest_key"]][0],
                "manifest_sha256": MANIFESTS[SOURCES[role]["manifest_key"]][1],
                "selector": SOURCES[role]["selector"],
            }
            for role in case["sources"]
        },
        "causal_credit": 0, "policy_score_eligible": False,
        "policy_score_credit": 0, "school_score_eligible": False,
        "school_score_credit": 0, "position_credit": 0,
        "featured_eligible": False,
    }


def registration_commit() -> str:
    commits = {first_addition(path) for path in REGISTERED}
    if len(commits) != 1:
        raise ValueError("Registration files entered in different commits")
    registered = commits.pop()
    for path in REGISTERED:
        committed_original(path, registered)
    if git("ls-tree", "-r", "--name-only", registered, "--", LOCK, SUMMARY,
           *(case["run"] for case in TESTS.values())).strip():
        raise ValueError("Registration commit contained source lock or results")
    for case in TESTS.values():
        spec = yaml.safe_load((ROOT / case["spec"]).read_text())
        if (spec.get("hypothesis_id") != case["id"]
                or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "descriptive"
                or spec.get("claim_direction") != case["expected_sign"]
                or spec.get("covers_claims") != []
                or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != []
                or spec.get("steelman") != case["steelman"]
                or spec["falsification"]["threshold"] != threshold(case)):
            raise ValueError(f"Frozen spec identity or gates differ: {case['id']}")
    return registered


def source_custody(source_root: Path) -> tuple[dict, dict[str, list[str]]]:
    """Verify exact raw bytes and dimension/year keys without reading value columns."""
    manifests = {}
    for name, (path, sha) in MANIFESTS.items():
        if file_sha(ROOT / path) != sha:
            raise ValueError(f"Tracked fetch manifest changed: {name}")
        manifests[name] = yaml.safe_load((ROOT / path).read_text())["entries"]
    custody, keysets = {}, {}
    for role, source in SOURCES.items():
        raw = source_root / source["path"]
        if not raw.is_file() or file_sha(raw) != source["sha256"]:
            raise ValueError(f"Missing or changed raw vintage: {role}")
        schema = set(pq.ParquetFile(raw).schema_arrow.names)
        required = set(source["selector"]) | {source["area_col"], "year", "value"}
        if not required.issubset(schema):
            raise ValueError(f"Unexpected raw source schema: {role}")
        cols = list(source["selector"]) + [source["area_col"], "year"]
        rows = pq.read_table(raw, columns=cols).to_pylist()
        keys = [
            (row[source["area_col"]], int(row["year"]))
            for row in rows
            if all(row[k] == v for k, v in source["selector"].items())
            and national(row[source["area_col"]])
            and row["year"] is not None
            and int(row["year"]) in source["years"]
        ]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate selected national-area/year key: {role}")
        keysets[role] = set(keys)
        matches = [
            e for e in manifests[source["manifest_key"]]
            if e.get("publisher") == source["publisher"]
            and e.get("series_id") == source["series_id"]
            and e.get("parquet_path") == source["path"]
        ]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise ValueError(f"Fetch manifest does not custody exact source: {role}")
        e = matches[0]
        manifest, manifest_sha = MANIFESTS[source["manifest_key"]]
        custody[role] = {
            "publisher": source["publisher"], "series_id": source["series_id"],
            "path": source["path"], "sha256": source["sha256"],
            "manifest": manifest, "manifest_sha256": manifest_sha,
            "selector": source["selector"], "years": list(source["years"]),
            "license": e.get("license"), "source_url": e.get("source_url"),
            "methodology_url": e.get("methodology_url"), "source_rows": e.get("rows"),
            "selected_national_area_year_keys": len(keys),
            "selected_key_sha256": hashlib.sha256(
                "".join(f"{geo},{year}\n" for geo, year in sorted(keys)).encode()
            ).hexdigest(),
        }
    candidates = {}
    for name, case in TESTS.items():
        geos = sorted(
            g for g in {key[0] for role in case["sources"] for key in keysets[role]}
            if national(g) and all(
                (g, y) in keysets[role]
                for role in case["sources"] for y in SOURCES[role]["years"]
            )
        )
        if geos != roster(case):
            raise ValueError(f"Raw selector keys differ from frozen roster: {name}")
        candidates[name] = geos
    return custody, candidates


def expected_lock(source_root: Path) -> dict:
    registered = registration_commit()
    custody, candidates = source_custody(source_root)
    return {
        "family_id": FAMILY, "registration_commit": registered,
        "registered_sha256": {path: file_sha(ROOT / path) for path in REGISTERED},
        "source_custody": custody, "candidate_national_areas": candidates,
        "selected_values_read": False,
        "instruction": "Commit this metadata-only lock before selected numeric access.",
    }


def make_lock(source_root: Path) -> None:
    path = ROOT / LOCK
    if path.exists():
        raise ValueError("Source lock already exists")
    payload = expected_lock(source_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print({name: len(geos) for name, geos in payload["candidate_national_areas"].items()})


def verified_lock(source_root: Path) -> tuple[dict, str, str]:
    registered = registration_commit()
    locked = first_addition(LOCK)
    committed_original(LOCK, locked)
    if not ancestor(registered, locked) or not ancestor(locked, "HEAD"):
        raise ValueError("Strict registration/source-lock chronology failed")
    if git("ls-tree", "-r", "--name-only", locked, "--", SUMMARY,
           *(case["run"] for case in TESTS.values())).strip():
        raise ValueError("Source-lock commit contained results")
    payload = json.loads((ROOT / LOCK).read_text())
    if payload != expected_lock(source_root):
        raise ValueError("Source lock differs from raw bytes, keys, or registration")
    return payload, registered, locked


def selected_values(source_root: Path, role: str, geos: set[str]) -> dict[tuple[str, int], float | None]:
    """Called only after verified_lock; no selected values are tracked."""
    source = SOURCES[role]
    cols = list(source["selector"]) + [source["area_col"], "year", "value"]
    values = {}
    for row in pq.read_table(source_root / source["path"], columns=cols).to_pylist():
        geo = row[source["area_col"]]
        if geo not in geos or row["year"] is None:
            continue
        year = int(row["year"])
        if year not in source["years"] or not all(
                row[k] == v for k, v in source["selector"].items()):
            continue
        key = geo, year
        if key in values:
            raise ValueError(f"Duplicate selected value key: {role} {key}")
        try:
            value = float(row["value"])
        except (TypeError, ValueError):
            value = None
        values[key] = value if value is not None and math.isfinite(value) else None
    if len(values) != len(geos) * len(source["years"]):
        raise ValueError(f"Missing locked source key: {role}")
    return values


def valid(value: float | None, low: float, high: float | None = None) -> bool:
    return value is not None and low <= value and (high is None or value <= high)


def panel_for_test(source_root: Path, case_name: str, geos: list[str]) -> tuple[pd.DataFrame, dict]:
    case = TESTS[case_name]
    data = {role: selected_values(source_root, role, set(geos)) for role in case["sources"]}
    rows, exclusions = [], Counter()
    for geo in geos:
        reasons = []
        if case_name == "solar_air":
            s10, s15 = (data["solar"][geo, y] for y in (2010, 2015))
            p10, p15 = (data["population"][geo, y] for y in (2010, 2015))
            m10, m15, m19 = (data["pm25"][geo, y] for y in (2010, 2015, 2019))
            if not all(valid(v, 0) for v in (s10, s15)):
                reasons.append("solar_missing_or_invalid")
            if not all(v is not None and v > 0 for v in (p10, p15)):
                reasons.append("population_missing_or_invalid")
            if not all(valid(v, 0, 500) for v in (m10, m15, m19)):
                reasons.append("pm25_missing_or_invalid")
            if reasons:
                exclusions.update(reasons)
                continue
            x0 = math.log1p(s10 * 1_000_000 / p10)
            x1 = math.log1p(s15 * 1_000_000 / p15)
            x = x1 - x0
            y = m19 - m15
            controls = (x0, m15, m15 - m10)
            material = abs(x)
        elif case_name == "education_lfp":
            e05, e15 = (data["education"][geo, y] for y in (2005, 2015))
            l05, l15, l23 = (data["female_lfp"][geo, y] for y in (2005, 2015, 2023))
            if not all(valid(v, 0, 20) for v in (e05, e15)):
                reasons.append("education_spending_missing_or_invalid")
            if not all(valid(v, 0, 100) for v in (l05, l15, l23)):
                reasons.append("female_lfp_missing_or_invalid")
            if reasons:
                exclusions.update(reasons)
                continue
            x = e15 - e05
            y = l23 - l15
            controls = (e05, l15, l15 - l05)
            material = abs(x)
        else:
            inflation = [data["inflation"][geo, y] for y in range(2005, 2014)]
            s14, s21 = (data["suicide"][geo, y] for y in (2014, 2021))
            if not all(valid(v, -100, 10_000) for v in inflation):
                reasons.append("inflation_missing_or_invalid")
            if not all(valid(v, 0, 200) for v in (s14, s21)):
                reasons.append("suicide_missing_or_invalid")
            if reasons:
                exclusions.update(reasons)
                continue
            volatility = float(np.std(inflation, ddof=1))
            x = math.asinh(volatility / 5)
            y = s21 - s14
            controls = (s14, math.asinh(float(np.mean(inflation)) / 5))
            material = volatility
        rows.append({
            "country_iso3": geo, "exposure": x, "outcome": y,
            "control_1": controls[0], "control_2": controls[1],
            "control_3": controls[2] if len(controls) > 2 else None,
            "material_metric": material,
        })
    panel = pd.DataFrame(rows, columns=[
        "country_iso3", "exposure", "outcome", "control_1",
        "control_2", "control_3", "material_metric",
    ]).sort_values("country_iso3").reset_index(drop=True)
    return panel, {
        "source_key_candidate_national_areas": len(geos),
        "complete_national_areas": len(panel),
        "exclusion_reasons_overlapping": dict(sorted(exclusions.items())),
    }


def design(panel: pd.DataFrame, case_name: str) -> tuple[np.ndarray, np.ndarray]:
    controls = ["control_1", "control_2"] + ([] if case_name == "inflation_suicide" else ["control_3"])
    x = np.column_stack(
        [np.ones(len(panel)), panel["exposure"].to_numpy(dtype=float)]
        + [panel[c].to_numpy(dtype=float) for c in controls]
    )
    return x, panel["outcome"].to_numpy(dtype=float)


def fit(panel: pd.DataFrame, case_name: str) -> dict:
    x, y = design(panel, case_name)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank model unavailable")
    controls = np.delete(x, 1, axis=1)
    rx = x[:, 1] - controls @ np.linalg.lstsq(controls, x[:, 1], rcond=None)[0]
    ry = y - controls @ np.linalg.lstsq(controls, y, rcond=None)[0]
    sx, sy = float(np.sum(rx * rx)), float(np.sum(ry * ry))
    if not all(math.isfinite(v) and v > 1e-10 for v in (sx, sy)):
        raise ValueError("No residualized exposure or outcome variation")
    result = sm.OLS(y, x).fit(cov_type="HC3")
    beta, se = float(result.params[1]), float(result.bse[1])
    p = float(2 * student_t.sf(abs(beta / se), df=n-k)) if se > 0 else float("nan")
    if not all(math.isfinite(v) for v in (beta, se, p)) or se <= 0:
        raise ValueError("Nonfinite HC3 uncertainty")
    return {
        "coefficient": beta, "standard_error": se, "p_value": p,
        "reference_df": n-k, "covariance": "HC3",
        "max_single_area_residualized_exposure_share": float(np.max(rx*rx) / sx),
        "max_single_area_residualized_outcome_share": float(np.max(ry*ry) / sy),
        "unit": TESTS[case_name]["unit"],
    }


def calculate(panel: pd.DataFrame, case_name: str, diag: dict) -> tuple[dict, str]:
    case = TESTS[case_name]
    n = len(panel)
    exposure = panel["exposure"].to_numpy(dtype=float)
    diag["material_exposure_areas"] = int(
        (panel["material_metric"].to_numpy(dtype=float) >= case["material_exposure_min"]).sum()
    )
    diag["exposure_iqr"] = float(np.quantile(exposure, .75) - np.quantile(exposure, .25)) if n else 0.0
    failed = []
    if n < case["min_complete"]:
        failed.append("min_complete_national_areas")
    if diag["material_exposure_areas"] < case["min_material"]:
        failed.append("min_material_exposure_areas")
    if diag["exposure_iqr"] < case["min_exposure_iqr"]:
        failed.append("min_exposure_iqr")
    if failed:
        diag["failed_gates"] = failed
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel, case_name)
    except ValueError as exc:
        diag["failed_gates"] = [f"estimator:{exc}"]
        return {}, "INCONCLUSIVE"
    diag["max_single_area_residualized_exposure_share"] = estimate[
        "max_single_area_residualized_exposure_share"
    ]
    diag["max_single_area_residualized_outcome_share"] = estimate[
        "max_single_area_residualized_outcome_share"
    ]
    if diag["max_single_area_residualized_exposure_share"] > case["max_exposure_share"]:
        failed.append("residualized_exposure_concentration")
    if diag["max_single_area_residualized_outcome_share"] > case["max_outcome_share"]:
        failed.append("residualized_outcome_concentration")
    loo, loo_failures = [], 0
    for geo in panel["country_iso3"]:
        try:
            loo.append(fit(panel.loc[panel.country_iso3 != geo], case_name)["coefficient"])
        except ValueError:
            loo_failures += 1
    diag["loo_successes"] = len(loo)
    diag["loo_failures"] = loo_failures
    diag["loo_positive_share"] = sum(beta > 0 for beta in loo) / len(loo) if loo else None
    diag["loo_negative_share"] = sum(beta < 0 for beta in loo) / len(loo) if loo else None
    if loo_failures > case["max_loo_failures"]:
        failed.append("leave_one_out_fit_failures")
    diag["failed_gates"] = failed
    if failed:
        return {}, "INCONCLUSIVE"
    sign = case["expected_sign"]
    b = estimate["coefficient"]
    p = estimate["p_value"]
    limit = case["meaningful_abs_beta"]
    concordance = diag["loo_positive_share"] if sign == "+" else diag["loo_negative_share"]
    opposite = diag["loo_negative_share"] if sign == "+" else diag["loo_positive_share"]
    aligned = b >= limit if sign == "+" else b <= -limit
    reversed_sign = b <= -limit if sign == "+" else b >= limit
    if aligned and p <= P_MAX and concordance >= case["min_loo_sign_share"]:
        return estimate, "SUPPORTED"
    if reversed_sign and p <= P_MAX and opposite >= case["min_loo_sign_share"]:
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, case_name: str, diag: dict, estimate: dict,
         verdict: str, registered: str, locked: str) -> None:
    case = TESTS[case_name]
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "hypothesis.yaml").write_bytes((ROOT / case["spec"]).read_bytes())
    custody = json.loads((ROOT / LOCK).read_text())["source_custody"]
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    (directory / "manifest.yaml").write_text(yaml.safe_dump({
        "family_id": FAMILY, "design_id": case["id"], "verdict": verdict,
        "evidence_type": "descriptive", "registration_commit": registered,
        "lock_commit": locked, "spec_sha256": file_sha(ROOT / case["spec"]),
        "lock_sha256": file_sha(ROOT / LOCK), "runner_sha256": file_sha(ROOT / RUNNER),
        "source_custody": {role: custody[role] for role in case["sources"]},
        "artifacts": list(ARTIFACTS), "credit": credit,
        "chart_data_omitted_to_keep_raw_values_out_of_repository": True,
    }, sort_keys=True))
    correction = {
        "disposition": "descriptive_calibration_only", "causal_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "position_credit": 0, "featured_eligible": False,
    }
    json_write(directory / "diagnostics.json", {
        **diag, "estimate": estimate, "verdict": verdict,
        "correction": correction, "analysis_scope": "descriptive_only",
    })
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["exposure"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([
        ("term", pa.string()), ("coefficient", pa.float64()),
        ("standard_error", pa.float64()), ("p_value", pa.float64()),
    ]))
    json_write(directory / "chart_data.json", [])
    lines = [
        f"# {case['description']}", "",
        f"**{verdict} — descriptive calibration only.**", "",
        f"Complete national areas: {diag['complete_national_areas']} of {diag['source_key_candidate_national_areas']} key candidates.",
        f"Material exposure areas: {diag['material_exposure_areas']}; exposure IQR: {diag['exposure_iqr']:.6g}.",
    ]
    if has_estimate:
        lines += [
            f"Beta {estimate['coefficient']:.6g} {case['unit']}; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}.",
        ]
    else:
        lines += ["No coefficient is published because a frozen gate failed."]
    lines += [
        f"Failed gates: {', '.join(diag['failed_gates']) if diag['failed_gates'] else 'none'}.",
        "", case["limits"], "",
        "This selected three-test family uses a local 0.01/3 cutoff. It does not control broader archive search or establish independent replication. Zero causal, policy, school, position, and featured credit.", "",
    ]
    (directory / "result_card.md").write_text("\n".join(lines))
    (directory / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER}'), '--verify', *sys.argv[1:]], check=True)\n"
    )
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump({
        "family_id": FAMILY, "design_id": case["id"], "verdict": verdict,
        "evidence_type": "descriptive", "causal_claim": False,
        "policy_effect_credit": False, "school_claim_links": [],
        "source_hashes_verified": True, "strict_spec_lock_chronology_verified": True,
        "correction": correction, "interpretation": case["description"] + " only.",
    }, sort_keys=True))
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict],
        "complete_national_areas": [diag["complete_national_areas"]],
        "material_exposure_areas": [diag["material_exposure_areas"]],
    }, pa.schema([
        ("verdict", pa.string()), ("complete_national_areas", pa.int64()),
        ("material_exposure_areas", pa.int64()),
    ]))
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError("Unexpected run artifact roster")


def result_summary(results: dict) -> str:
    lines = [
        "# Three distinct measured outcomes — frozen family result", "",
        "One prospectively registered descriptive three-test family; local two-sided threshold p≤0.01/3.",
        "Key-only national-area rosters and fixed source pins were committed before selected values; a separate metadata-only lock preceded all three runs.",
        "",
    ]
    for name, case in TESTS.items():
        diag, estimate, verdict = results[name]
        lines += [
            f"## {case['description']}", "",
            f"**{verdict}.** {diag['complete_national_areas']} of {diag['source_key_candidate_national_areas']} key candidates complete; {diag['material_exposure_areas']} material exposures; exposure IQR {diag['exposure_iqr']:.8g}.",
        ]
        if "coefficient" in estimate:
            lines += [
                f"Beta {estimate['coefficient']:.8g} {case['unit']}; HC3 SE {estimate['standard_error']:.8g}; two-sided p {estimate['p_value']:.8g}.",
            ]
        else:
            lines += ["No public coefficient because a frozen gate failed."]
        for key in (
            "max_single_area_residualized_exposure_share",
            "max_single_area_residualized_outcome_share",
            "loo_successes", "loo_failures",
            "loo_positive_share", "loo_negative_share",
        ):
            if key in diag:
                lines.append(f"{key}: {diag[key]}.")
        lines += [
            f"Failed gates: {', '.join(diag['failed_gates']) if diag['failed_gates'] else 'none'}.",
            case["limits"], "",
        ]
    lines += [
        "The three outcomes are distinct environmental exposure, labour participation, and mortality measures. They are not three independent replications of one effect. Data-vintage, source-model, selection, and common-shock limitations remain. No causal, policy, school, position, or featured credit.",
        "",
        "Definitions: [IRENA renewable capacity](https://dashboard.irena.org/download/Methodology.pdf); [WHO PM2.5](https://www.who.int/data/gho/data/themes/air-pollution/modelled-exposure-of-pm-air-pollution-exposure); [WDI education spending](https://data.worldbank.org/indicator/SE.XPD.TOTL.GD.ZS); [ILOSTAT](https://ilostat.ilo.org/data/); [WDI CPI inflation](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG); [WHO suicide mortality](https://www.who.int/data/gho/indicator-metadata-registry/imr-details/4664).",
        "",
    ]
    return "\n".join(lines)


def run_or_verify(source_root: Path, verify: bool) -> None:
    lock, registered, locked = verified_lock(source_root)
    results = {}
    for name in TESTS:
        panel, diag = panel_for_test(
            source_root, name, lock["candidate_national_areas"][name]
        )
        estimate, verdict = calculate(panel, name, diag)
        results[name] = (diag, estimate, verdict)
    summary = result_summary(results)
    if verify and not (ROOT / SUMMARY).exists():
        raise ValueError("Missing family result audit")
    if not verify and (
        (ROOT / SUMMARY).exists()
        or any((ROOT / case["run"]).exists() for case in TESTS.values())
    ):
        raise ValueError("Run already exists")
    with tempfile.TemporaryDirectory(prefix="ieset_distinct_triad_") as temporary:
        generated = Path(temporary)
        for name, case in TESTS.items():
            diag, estimate, verdict = results[name]
            path = generated / name
            emit(path, name, diag, estimate, verdict, registered, locked)
            target = ROOT / case["run"]
            if verify:
                for artifact in ARTIFACTS:
                    if file_sha(path / artifact) != file_sha(target / artifact):
                        raise ValueError(f"Exact replay differs: {case['id']}/{artifact}")
        if verify:
            if (ROOT / SUMMARY).read_text() != summary:
                raise ValueError("Exact family result audit differs")
            print("Exact replay matched 27 run artifacts and family audit")
        else:
            for name, case in TESTS.items():
                shutil.copytree(generated / name, ROOT / case["run"])
            (ROOT / SUMMARY).write_text(summary)
            print(json.dumps({
                name: {"verdict": verdict, **diag, "estimate": estimate}
                for name, (diag, estimate, verdict) in results.items()
            }, sort_keys=True, indent=2, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Checkout containing the hash-pinned raw vintages")
    args = parser.parse_args()
    if args.preflight:
        custody, candidates = source_custody(args.source_root)
        print(json.dumps({
            "key_candidate_counts": {name: len(geos) for name, geos in candidates.items()},
            "source_custody": custody, "selected_values_read": False,
        }, sort_keys=True, indent=2))
    elif args.lock:
        make_lock(args.source_root)
    else:
        run_or_verify(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
