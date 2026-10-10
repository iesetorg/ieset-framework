#!/usr/bin/env python3
"""Source-locked electricity access and later schooling milestone calibrations.

Preflight reads treatment values and selected outcome keys only. Lock copies
selected values after registration; run requires a separately committed lock.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_electricity_schooling_forward_2026_10_10"
RUNNER = "scripts/run_wdi_electricity_schooling_forward_2026.py"
PLAN = "engine/audits/wdi_electricity_schooling_forward_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_electricity_schooling_forward_key_roster.csv"
ROSTER_SHA = "a7b8e33e420cd1c0ce8160ad4e03e1102440d184842dd450027a446df26e8638"
SLICE = "data/pinned_evidence/wdi_electricity_schooling_forward_source_slice.csv"
LOCK = "data/pinned_evidence/wdi_electricity_schooling_forward.manifest.json"
SUMMARY = "engine/audits/wdi_electricity_schooling_forward_results_2026-10-10.md"
ARTIFACTS = ("hypothesis.yaml", "manifest.yaml", "diagnostics.json",
             "coefficients.parquet", "chart_data.json", "result_card.md",
             "replication.py", "evidence_packet.yaml", "metric_results.parquet")

START, END, LAG, HORIZON = 2000, 2018, 5, 3
FAMILY_SIZE = 5
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
MIN_PAIRS, MIN_COUNTRIES, MIN_COUNTRY_PAIRS = 400, 50, 3
MIN_YEARS = 10
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES, MATERIAL_GAIN_PP = 50, 20, 10.0
MIN_LOW_ROWS, MIN_LOW_COUNTRIES, LOW_CHANGE_PP = 100, 30, 2.0
MAX_TOP_ONE_PERCENT_RESIDUAL_SHARE = 0.20
MAX_COUNTRY_RESIDUAL_SHARE, MAX_YEAR_RESIDUAL_SHARE = 0.15, 0.20

MAY_MANIFEST = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
MAY_MANIFEST_SHA = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"
EARLY_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
EARLY_MANIFEST_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
BOOTSTRAP_MANIFEST = "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml"
BOOTSTRAP_MANIFEST_SHA = "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"

def pin(series: str, vintage: str, digest: str, manifest: str, manifest_sha: str) -> dict[str, str]:
    return {"publisher": "world_bank_wdi", "series_id": series,
            "path": f"data/vintages/world_bank_wdi/{series}@{vintage}.parquet",
            "sha256": digest, "manifest": manifest, "manifest_sha256": manifest_sha}

SOURCES = {
    "electricity": pin("EG.ELC.ACCS.ZS", "2026-05-05T195057Z",
                       "aa564cbe2947b3d1c3499d7ecb9b2c38c6aa5de073d2cc1a797cfe2fe42f2931",
                       EARLY_MANIFEST, EARLY_MANIFEST_SHA),
    "income": pin("NY.GDP.PCAP.KD", "2026-05-05T194645Z",
                  "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
                  EARLY_MANIFEST, EARLY_MANIFEST_SHA),
    "primary_completion": pin("SE.PRM.CMPT.ZS", "2026-05-05T204018Z",
                              "ce77c940b4b6bbbb28dfc9efb2d2e0547fa3f73bfcc8780cca18708924060e4d",
                              MAY_MANIFEST, MAY_MANIFEST_SHA),
    "secondary_net_enrolment": pin("SE.SEC.NENR", "2026-04-30T141354Z",
                                    "f794ef6192174e0251cb58f3b72e502c93b0cd360c87c9527e86af3520ffed3a",
                                    "data/manifests/fetch_run_2026-04-30T141425Z.yaml",
                                    "45e429b7b0d8b2a0a07b31eb853a4910e84d34670622fd92a64666e0ece7019d"),
    "tertiary_enrolment": pin("SE.TER.ENRR", "2026-05-05T195043Z",
                              "0459b48b5625f54872c4708f4a6107e66c8c44087b18d798c99e91e83511cede",
                              EARLY_MANIFEST, EARLY_MANIFEST_SHA),
    "adult_literacy": pin("SE.ADT.LITR.ZS", "2026-04-30T114614Z",
                          "6c301217acea1c3ae201cd66aaa6c61daa31d7a57ad1aef0ec214ce6c5c35cbd",
                          BOOTSTRAP_MANIFEST, BOOTSTRAP_MANIFEST_SHA),
    "upper_secondary_attainment": pin("SE.SEC.CUAT.UP.ZS", "2026-04-30T115107Z",
                                      "ab2ebef019f3a4e19b64c8730f337609e2d3990d2a727ad3cc92c17eeea31dbb",
                                      BOOTSTRAP_MANIFEST, BOOTSTRAP_MANIFEST_SHA),
}
CASES = {
    "primary_completion": {"id": "wdi_electricity_gain_primary_completion_forward_2026",
                           "label": "Primary completion rate", "bound": 150.0, "beta_min": 0.5},
    "secondary_net_enrolment": {"id": "wdi_electricity_gain_secondary_net_enrolment_forward_2026",
                                "label": "Secondary net enrolment rate", "bound": 100.0, "beta_min": 0.5},
    "tertiary_enrolment": {"id": "wdi_electricity_gain_tertiary_enrolment_forward_2026",
                             "label": "Tertiary gross enrolment ratio", "bound": 200.0, "beta_min": 1.0},
    "adult_literacy": {"id": "wdi_electricity_gain_adult_literacy_forward_2026",
                       "label": "Adult literacy rate", "bound": 100.0, "beta_min": 0.3},
    "upper_secondary_attainment": {"id": "wdi_electricity_gain_upper_secondary_attainment_forward_2026",
                                   "label": "Adults 25+ with upper-secondary attainment", "bound": 100.0, "beta_min": 0.5},
}

def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(path: str) -> str:
    revisions = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if len(revisions) != 1:
        raise RuntimeError(f"expected one first-addition commit: {path}: {revisions}")
    return revisions[0]


def committed_original(path: str, revision: str) -> None:
    if (ROOT / path).read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen file changed after {revision}: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"frozen file has uncommitted changes: {path}")


def earlier(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT).returncode == 0


def spec_rel(key: str) -> str:
    return f"hypotheses/energy/{CASES[key]['id']}.yaml"


def steelman_rel(key: str) -> str:
    return f"hypotheses/steelman/{CASES[key]['id']}.md"


def run_rel(key: str) -> str:
    return f"engine/runs/{CASES[key]['id']}"


def threshold(key: str) -> dict:
    return {"family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX,
            "meaningful_beta_min_pp_per_10pp_access_gain": CASES[key]["beta_min"],
            "min_complete_pairs": MIN_PAIRS, "min_countries": MIN_COUNTRIES,
            "min_pairs_per_country": MIN_COUNTRY_PAIRS, "min_years": MIN_YEARS,
            "min_material_gain_rows": MIN_MATERIAL_ROWS,
            "min_material_gain_countries": MIN_MATERIAL_COUNTRIES,
            "material_gain_pp": MATERIAL_GAIN_PP,
            "min_low_change_rows": MIN_LOW_ROWS,
            "min_low_change_countries": MIN_LOW_COUNTRIES,
            "low_change_pp": LOW_CHANGE_PP,
            "max_top_one_percent_residualized_exposure_share": MAX_TOP_ONE_PERCENT_RESIDUAL_SHARE,
            "max_country_residualized_exposure_share": MAX_COUNTRY_RESIDUAL_SHARE,
            "max_year_residualized_exposure_share": MAX_YEAR_RESIDUAL_SHARE,
            "outcome_valid_max": CASES[key]["bound"], "roster_sha256": ROSTER_SHA,
            "source_files": {role: {k: v for k, v in SOURCES[role].items()
                                    if k in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role in ("electricity", "income", key)},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def registration_commit() -> str:
    paths = [RUNNER, PLAN, ROSTER]
    paths += [p for key in CASES for p in (spec_rel(key), steelman_rel(key))]
    revisions = {first_addition(p) for p in paths}
    if len(revisions) != 1:
        raise RuntimeError("family registration files were not first added together")
    revision = revisions.pop()
    for p in paths:
        committed_original(p, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK, SLICE).strip():
        raise RuntimeError("registration commit already contained measured source values")
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(key)).read_text())
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "descriptive" or spec.get("claim_direction") != "+"
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != [] or spec.get("steelman") != steelman_rel(key)
                or spec["falsification"]["threshold"] != threshold(key)):
            raise RuntimeError(f"frozen specification mismatch: {key}")
        if git("ls-tree", "-r", "--name-only", revision, "--", run_rel(key)).strip():
            raise RuntimeError("registration commit already contained run results")
    return revision


def source_custody(source_root: Path) -> dict:
    output = {}
    for role, source in SOURCES.items():
        raw_path = source_root / source["path"]
        if not raw_path.is_file() or file_sha(raw_path) != source["sha256"]:
            raise RuntimeError(f"source vintage missing or hash mismatch: {role}")
        manifest_path = ROOT / source["manifest"]
        if file_sha(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"tracked fetch manifest hash mismatch: {role}")
        manifest = yaml.safe_load(manifest_path.read_text())
        entries = [e for e in manifest.get("entries", [])
                   if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(entries) != 1 or entries[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"fetch manifest does not custody {role}")
        e = entries[0]
        output[role] = {**source, "source_url": e.get("source_url"),
                        "methodology_url": e.get("methodology_url"),
                        "license": e.get("license"), "rows": e.get("rows")}
    return output


def roster_codes() -> list[str]:
    raw = (ROOT / ROSTER).read_bytes()
    if file_sha(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen source-key country roster hash mismatch")
    lines = raw.decode().splitlines()
    if not lines or lines[0] != "country_iso3":
        raise RuntimeError("invalid roster header")
    codes = lines[1:]
    if codes != sorted(set(codes)) or any(len(c) != 3 or not c.isupper() for c in codes):
        raise RuntimeError("invalid roster codes")
    return codes


def source_keys(source_root: Path) -> list[str]:
    import pycountry
    permitted = {c.alpha_3 for c in pycountry.countries} | {"XKX"}
    keys = []
    for source in SOURCES.values():
        frame = pd.read_parquet(source_root / source["path"], columns=["country_iso3", "year"])
        frame = frame[frame.country_iso3.isin(permitted) & frame.year.between(START-LAG, END+HORIZON)]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate source country/year keys: {source['series_id']}")
        keys.append(set(map(tuple, frame[["country_iso3", "year"]].itertuples(index=False, name=None))))
    joint = set.intersection(*keys)
    required = set(range(START-LAG, END+HORIZON+1))
    codes = sorted({c for c, _ in joint if all((c, y) in joint for y in required)})
    if len(codes) < 100:
        raise RuntimeError("unexpectedly small source-key roster")
    return codes


def preflight(source_root: Path) -> None:
    source_custody(source_root)
    codes = source_keys(source_root)
    path = ROOT / ROSTER
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "country_iso3\n" + "\n".join(codes) + "\n"
    if path.exists() and path.read_text() != content:
        raise RuntimeError("existing key roster differs")
    path.write_text(content)
    print(json.dumps({"candidate_countries": len(codes), "roster_sha256": file_sha(path)}, sort_keys=True))


def selected_csv(source_root: Path, codes: list[str]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["role", "country_iso3", "year", "value", "obs_status"])
    year_set = set(range(START-LAG, END + HORIZON + 1))
    code_set = set(codes)
    for role in SOURCES:
        frame = pd.read_parquet(source_root / SOURCES[role]["path"],
                                columns=["country_iso3", "year", "value", "obs_status"])
        frame = frame[frame.country_iso3.isin(code_set) & frame.year.isin(year_set)]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate selected values: {role}")
        for row in frame.sort_values(["country_iso3", "year"]).itertuples(index=False):
            val = "" if pd.isna(row.value) else format(float(row.value), ".17g")
            status = "" if pd.isna(row.obs_status) else str(row.obs_status)
            writer.writerow([role, row.country_iso3, int(row.year), val, status])
    return output.getvalue().encode()


def lock(source_root: Path) -> None:
    revision = registration_commit()
    if (ROOT / LOCK).exists() or (ROOT / SLICE).exists():
        raise RuntimeError("source lock already exists")
    custody = source_custody(source_root)
    codes = roster_codes()
    if codes != source_keys(source_root):
        raise RuntimeError("source-key roster changed")
    selected = selected_csv(source_root, codes)
    slice_path = ROOT / SLICE
    slice_path.parent.mkdir(parents=True, exist_ok=True)
    slice_path.write_bytes(selected)
    payload = {"schema": "ieset-electricity-schooling-source-lock-v1",
               "family": FAMILY, "registration_commit": revision,
               "candidate_countries": codes, "source_custody": custody,
               "source_slice": SLICE, "source_slice_sha256": file_sha(slice_path)}
    (ROOT / LOCK).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"source_slice_rows": selected.count(b"\n") - 1,
                      "source_slice_sha256": payload["source_slice_sha256"]}, sort_keys=True))


def verified_lock() -> tuple[dict, str, str]:
    registered = registration_commit()
    revisions = {first_addition(p) for p in (LOCK, SLICE)}
    if len(revisions) != 1:
        raise RuntimeError("source lock files were not first added together")
    locked = revisions.pop()
    if not earlier(registered, locked):
        raise RuntimeError("source lock does not strictly follow registration")
    for p in (LOCK, SLICE):
        committed_original(p, locked)
    for key in CASES:
        if git("ls-tree", "-r", "--name-only", locked, "--", run_rel(key)).strip():
            raise RuntimeError("source lock already contained result artifacts")
    payload = json.loads((ROOT / LOCK).read_text())
    if (payload.get("registration_commit") != registered or payload.get("family") != FAMILY
            or payload.get("candidate_countries") != roster_codes()
            or payload.get("source_slice") != SLICE
            or payload.get("source_slice_sha256") != file_sha(ROOT / SLICE)):
        raise RuntimeError("source lock content mismatch")
    if payload["source_custody"] != source_custody_metadata():
        raise RuntimeError("source custody metadata changed")
    return payload, registered, locked


def source_custody_metadata() -> dict:
    output = {}
    for role, source in SOURCES.items():
        manifest = yaml.safe_load((ROOT / source["manifest"]).read_text())
        e = next(e for e in manifest["entries"]
                 if e.get("publisher") == source["publisher"]
                 and e.get("series_id") == source["series_id"]
                 and e.get("parquet_path") == source["path"])
        output[role] = {**source, "source_url": e.get("source_url"),
                        "methodology_url": e.get("methodology_url"),
                        "license": e.get("license"), "rows": e.get("rows")}
    return output


def verify_source(source_root: Path) -> None:
    payload, _, _ = verified_lock()
    if source_custody(source_root) != payload["source_custody"]:
        raise RuntimeError("source custody differs")
    if source_keys(source_root) != roster_codes():
        raise RuntimeError("source-key roster differs")
    if selected_csv(source_root, roster_codes()) != (ROOT / SLICE).read_bytes():
        raise RuntimeError("source slice does not match exact pinned raw vintages")
    print("Pinned source re-extraction matched source slice byte for byte")


def load_values() -> dict[str, dict[tuple[str, int], float | None]]:
    values: dict[str, dict[tuple[str, int], float | None]] = {role: {} for role in SOURCES}
    with (ROOT / SLICE).open(newline="") as fh:
        for row in csv.DictReader(fh):
            role = row["role"]
            key = (row["country_iso3"], int(row["year"]))
            if role not in values or key in values[role]:
                raise RuntimeError(f"invalid source slice row: {role}: {key}")
            values[role][key] = float(row["value"]) if row["value"] and row["obs_status"] in ("", "A") else None
    expected_rows = len(roster_codes()) * (END + HORIZON - (START-LAG) + 1)
    if any(len(table) != expected_rows for table in values.values()):
        raise RuntimeError("source slice has missing country/year rows")
    return values


def valid(value: float | None, low: float, high: float, *, open_low: bool = False) -> bool:
    return (value is not None and math.isfinite(value) and
            (value > low if open_low else value >= low) and value <= high)


def panel_for(key: str, values: dict, codes: list[str]) -> tuple[pd.DataFrame, dict]:
    rows = []
    excluded = Counter()
    bound = CASES[key]["bound"]
    for country in codes:
        for year in range(START, END + 1):
            before = (country, year-LAG)
            current = (country, year)
            future = (country, year+HORIZON)
            e0, e1 = values["electricity"][before], values["electricity"][current]
            i0, i1 = values["income"][before], values["income"][current]
            y0, y3 = values[key][current], values[key][future]
            bad = []
            if not valid(e0, 0, 100) or not valid(e1, 0, 100): bad.append("electricity")
            if not valid(i0, 0, 1e9, open_low=True) or not valid(i1, 0, 1e9, open_low=True): bad.append("income")
            if not valid(y0, 0, bound) or not valid(y3, 0, bound): bad.append("outcome")
            if bad:
                excluded.update(bad)
                continue
            rows.append({"country_iso3": country, "year": year,
                         "electricity_gain_10pp": (e1-e0)/10.0,
                         "baseline_access": e0, "log_income": math.log(i1),
                         "prior_income_growth": math.log(i1/i0),
                         "baseline_outcome": y0, "change": y3-y0})
    columns = ["country_iso3", "year", "electricity_gain_10pp", "baseline_access",
               "log_income", "prior_income_growth", "baseline_outcome", "change"]
    panel = pd.DataFrame(rows, columns=columns)
    initial_pairs = len(panel)
    if initial_pairs:
        panel = panel[panel.groupby("country_iso3").year.transform("size") >= MIN_COUNTRY_PAIRS].copy()
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    diagnostics = {"source_key_candidate_countries": len(codes),
                   "source_key_candidate_pairs": len(codes)*(END-START+1),
                   "pre_country_floor_complete_pairs": initial_pairs,
                   "complete_pairs": len(panel),
                   "complete_countries": int(panel.country_iso3.nunique()),
                   "complete_years": int(panel.year.nunique()),
                   "excluded_reasons_overlap": dict(sorted(excluded.items()))}
    return panel, diagnostics


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict, str]:
    failures = []
    n, countries = len(panel), diag["complete_countries"]
    if n < MIN_PAIRS: failures.append("min_complete_pairs")
    if countries < MIN_COUNTRIES: failures.append("min_countries")
    if diag["complete_years"] < MIN_YEARS: failures.append("min_years")
    material = panel[panel.electricity_gain_10pp >= MATERIAL_GAIN_PP/10]
    low = panel[panel.electricity_gain_10pp.abs() <= LOW_CHANGE_PP/10]
    diag["material_gain_rows"] = len(material)
    diag["material_gain_countries"] = int(material.country_iso3.nunique())
    diag["low_change_rows"] = len(low)
    diag["low_change_countries"] = int(low.country_iso3.nunique())
    if len(material) < MIN_MATERIAL_ROWS: failures.append("min_material_gain_rows")
    if diag["material_gain_countries"] < MIN_MATERIAL_COUNTRIES: failures.append("min_material_gain_countries")
    if len(low) < MIN_LOW_ROWS: failures.append("min_low_change_rows")
    if diag["low_change_countries"] < MIN_LOW_COUNTRIES: failures.append("min_low_change_countries")
    if failures:
        diag["failed_gates"] = failures
        return {}, "INCONCLUSIVE"
    controls = "baseline_access + baseline_outcome + log_income + prior_income_growth + C(country_iso3) + C(year)"
    model = smf.ols("change ~ electricity_gain_10pp + " + controls, panel)
    if np.linalg.matrix_rank(model.exog) < model.exog.shape[1]:
        diag["failed_gates"] = ["design_rank"]
        return {}, "INCONCLUSIVE"
    residual = np.asarray(smf.ols("electricity_gain_10pp ~ " + controls, panel).fit().resid, dtype=float)
    denom = float(np.sum(residual**2))
    if not math.isfinite(denom) or denom <= 1e-8:
        diag["failed_gates"] = ["residualized_exposure_variance"]
        return {}, "INCONCLUSIVE"
    weights = panel[["country_iso3", "year"]].copy()
    weights["sq"] = residual**2
    top_n = max(1, math.ceil(n*0.01))
    diag["top_one_percent_residualized_exposure_share"] = float(np.sort(weights.sq.to_numpy())[-top_n:].sum()/denom)
    diag["max_country_residualized_exposure_share"] = float(weights.groupby("country_iso3").sq.sum().max()/denom)
    diag["max_year_residualized_exposure_share"] = float(weights.groupby("year").sq.sum().max()/denom)
    if diag["top_one_percent_residualized_exposure_share"] > MAX_TOP_ONE_PERCENT_RESIDUAL_SHARE: failures.append("top_one_percent_concentration")
    if diag["max_country_residualized_exposure_share"] > MAX_COUNTRY_RESIDUAL_SHARE: failures.append("country_concentration")
    if diag["max_year_residualized_exposure_share"] > MAX_YEAR_RESIDUAL_SHARE: failures.append("year_concentration")
    if failures:
        diag["failed_gates"] = failures
        return {}, "INCONCLUSIVE"
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3})
    beta, se = float(fit.params["electricity_gain_10pp"]), float(fit.bse["electricity_gain_10pp"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        diag["failed_gates"] = ["finite_cluster_uncertainty"]
        return {}, "INCONCLUSIVE"
    pvalue = float(2*student_t.sf(abs(beta/se), countries-1))
    estimate = {"coefficient": beta, "standard_error": se, "p_value": pvalue,
                "country_cluster_df": countries-1,
                "unit": "outcome percentage-point change over three years per +10-point earlier electricity-access gain"}
    diag["failed_gates"] = []
    return estimate, "PARTIAL"


def json_write(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(key: str, directory: Path, panel: pd.DataFrame, diag: dict,
         estimate: dict, verdict: str, registered: str, locked: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    case = CASES[key]
    (directory / "hypothesis.yaml").write_bytes((ROOT / spec_rel(key)).read_bytes())
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    correction = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
                  "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
                  "bonferroni_p_max": P_MAX, "causal_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0,
                  "school_score_eligible": False, "school_score_credit": 0,
                  "featured_eligible": False}
    source_lock = json.loads((ROOT / LOCK).read_text())
    manifest = {"design_id": case["id"], "verdict": verdict,
                "evidence_type": "descriptive", "family_id": FAMILY,
                "spec_commit": registered, "lock_commit": locked,
                "spec_sha256": file_sha(ROOT / spec_rel(key)),
                "lock_sha256": file_sha(ROOT / LOCK), "runner_sha256": file_sha(ROOT / RUNNER),
                "source_slice_sha256": source_lock["source_slice_sha256"],
                "source_custody": {role: source_lock["source_custody"][role]
                                   for role in ("electricity", "income", key)},
                "artifacts": list(ARTIFACTS), "credit": credit}
    (directory / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    json_write(directory / "diagnostics.json",
               {**diag, "estimate": estimate, "verdict": verdict,
                "correction": correction, "analysis_scope": "descriptive_only"})
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["electricity_gain_10pp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                  ("standard_error", pa.float64()), ("p_value", pa.float64())]))
    json_write(directory / "chart_data.json", [
        {"country_iso3": str(r.country_iso3), "year": int(r.year),
         "earlier_electricity_gain_10pp": float(r.electricity_gain_10pp),
         "later_outcome_change_pp_3yr": float(r.change)}
        for r in panel.itertuples(index=False)])
    lines = [f"# {case['label']} after electricity access gain", "",
             f"**{verdict} — descriptive calibration only.**", "",
             f"Complete country-year pairs: {len(panel)} across {diag['complete_countries']} economies.",
             f"Material access-gain pairs: {diag['material_gain_rows']} across {diag['material_gain_countries']} economies."]
    if has_estimate:
        lines += [f"Coefficient {estimate['coefficient']:.6g} outcome points per +10 access points; country-cluster SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}."]
    else:
        lines += ["No coefficient was admitted because a frozen sample or method gate failed.",
                  f"Failed gates: {', '.join(diag['failed_gates'])}."]
    lines += ["", "Electricity access does not measure reliability, price, household connection, or a policy. Schooling measures share UNESCO sources and are correlated. This five-test family gives no causal, policy, school, position, or featured credit.", ""]
    (directory / "result_card.md").write_text("\n".join(lines))
    (directory / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER}'), '--verify', *sys.argv[1:]], check=True)\n")
    packet = {"design_id": case["id"], "verdict": verdict,
              "evidence_type": "descriptive", "causal_claim": False,
              "policy_effect_credit": False, "school_claim_links": [],
              "correction": correction, "source_hashes_verified": True,
              "strict_spec_lock_chronology_verified": True,
              "interpretation": f"Three-year {case['label'].lower()} change associated with prior electricity-access gain; no electricity or education-policy effect."}
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict], "complete_pairs": [len(panel)],
        "complete_countries": [diag["complete_countries"]],
    }, pa.schema([("verdict", pa.string()), ("complete_pairs", pa.int64()),
                  ("complete_countries", pa.int64())]))
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise RuntimeError("run artifact roster mismatch")


def result_summary(results: list[dict]) -> str:
    lines = ["# Earlier electricity access gains and later educational milestones — frozen results", "",
             "Five prospectively registered, source-locked descriptive tests use the same earlier WDI electricity-access gain and distinct but correlated WDI/UNESCO schooling milestones. Each has its own complete-case panel and country/year fixed effects. Five tests stay in the Bonferroni denominator even if one is inconclusive. Directional p cutoff is 0.01/5. No causal, policy, school, position, or featured credit.", "",
             "| Outcome | Complete pairs / countries | Material gain rows / countries | Beta | Country-cluster SE | Two-sided p | Verdict | Failed gates |",
             "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for r in results:
        e = r["estimate"]
        fmt = lambda name: f"{e[name]:.6g}" if name in e else "—"
        lines.append(f"| {r['label']} | {r['pairs']} / {r['countries']} | {r['material_rows']} / {r['material_countries']} | {fmt('coefficient')} | {fmt('standard_error')} | {fmt('p_value')} | {r['verdict']} | {', '.join(r['failed_gates']) or 'none'} |")
    lines += ["", "Electricity access is a modelled national share, not measured school electrification or a policy assignment. Income, urbanization, institutions, and reporting can affect both access and schooling. The five outcome measures are correlated and cannot count as independent replications. The local family correction does not repair archive-wide search.", ""]
    return "\n".join(lines)


def run_or_verify(verify: bool) -> None:
    _, registered, locked = verified_lock()
    values = load_values()
    codes = roster_codes()
    results = []
    with tempfile.TemporaryDirectory(prefix="ieset_electricity_schooling_") as tmp:
        for key in CASES:
            panel, diag = panel_for(key, values, codes)
            estimate, verdict = calculate(panel, diag)
            if estimate:
                magnitude = CASES[key]["beta_min"]
                beta, pval = estimate["coefficient"], estimate["p_value"]
                if beta >= magnitude and pval <= P_MAX: verdict = "SUPPORTED"
                elif beta <= -magnitude and pval <= P_MAX: verdict = "REFUTED"
            generated = Path(tmp) / key
            emit(key, generated, panel, diag, estimate, verdict, registered, locked)
            target = ROOT / run_rel(key)
            if verify:
                if not target.is_dir(): raise RuntimeError(f"missing run: {key}")
                for artifact in ARTIFACTS:
                    if file_sha(generated / artifact) != file_sha(target / artifact):
                        raise RuntimeError(f"exact replay differs: {key}/{artifact}")
            else:
                if target.exists(): raise RuntimeError(f"run already exists: {key}")
                shutil.copytree(generated, target)
            results.append({"key": key, "label": CASES[key]["label"],
                            "pairs": len(panel), "countries": diag["complete_countries"],
                            "material_rows": diag["material_gain_rows"],
                            "material_countries": diag["material_gain_countries"],
                            "estimate": estimate, "verdict": verdict,
                            "failed_gates": diag["failed_gates"]})
    summary = result_summary(results)
    if verify:
        if (ROOT / SUMMARY).read_text() != summary:
            raise RuntimeError("result summary differs on replay")
        print("Exact replay matched five result summaries and all 45 run artifacts")
    else:
        (ROOT / SUMMARY).write_text(summary)
        print(json.dumps(results, sort_keys=True, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    for name in ("preflight", "lock", "verify-source", "run", "verify"):
        choices.add_argument("--" + name, action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.preflight: preflight(args.source_root)
    elif args.lock: lock(args.source_root)
    elif args.verify_source: verify_source(args.source_root)
    elif args.run: run_or_verify(False)
    else: run_or_verify(True)


if __name__ == "__main__":
    main()
