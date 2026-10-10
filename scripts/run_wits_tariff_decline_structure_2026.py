#!/usr/bin/env python3
"""Frozen four-outcome, value-blind-registered tariff calibration family."""

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
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wits_tariff_decline_structure_2026_10_10"
RUNNER = "scripts/run_wits_tariff_decline_structure_2026.py"
PLAN = "engine/audits/wits_tariff_decline_structure_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wits_tariff_decline_structure_key_roster.csv"
ROSTER_SHA = "e9e90739212dd649390f873f3785acbb7d83a28276cf0a861e8d0ac5bc58e37b"
SLICE = "data/pinned_evidence/wits_tariff_decline_structure_source_slice.csv"
LOCK = "data/pinned_evidence/wits_tariff_decline_structure.manifest.json"
SUMMARY = "engine/audits/wits_tariff_decline_structure_results_2026-10-10.md"
ARTIFACTS = ("hypothesis.yaml", "manifest.yaml", "diagnostics.json", "coefficients.parquet",
             "chart_data.json", "result_card.md", "replication.py", "evidence_packet.yaml",
             "metric_results.parquet")
FAMILY_ALPHA, FAMILY_SIZE, P_MAX = 0.01, 4, 0.0025
MIN_N, MIN_ARM, MIN_IQR = 45, 10, 1.0
MAX_CONCENTRATION, MAX_LOO_FAILURE, MIN_LOO_SIGN = 0.20, 0.10, 0.75


def pin(publisher: str, series: str, vintage: str, digest: str, manifest: str,
        manifest_digest: str) -> dict[str, str]:
    return {"publisher": publisher, "series_id": series,
            "path": f"data/vintages/{publisher}/{series}@{vintage}.parquet",
            "sha256": digest, "manifest": manifest, "manifest_sha256": manifest_digest}


MAY_EARLY = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
MAY_EARLY_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
SOURCES = {
    "tariff": pin("wits", "weighted_mean_applied_tariff", "2026-07-23T151540Z",
                  "73520e0da6a44048e51a64671c97369aadf160130937f351f90375fb86b0e010",
                  "data/manifests/fetch_run_2026-07-23T151550Z.yaml",
                  "96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5"),
    "income": pin("world_bank_wdi", "NY.GDP.PCAP.KD", "2026-05-05T194645Z",
                  "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
                  MAY_EARLY, MAY_EARLY_SHA),
    "manufacturing_va": pin("world_bank_wdi", "NV.IND.MANF.ZS", "2026-05-05T194954Z",
                            "a440c8b254408d43b810059921c1d72c15612c8d9921fbec60a87b331adc2499",
                            MAY_EARLY, MAY_EARLY_SHA),
    "industrial_employment": pin("world_bank_wdi", "SL.IND.EMPL.ZS", "2026-05-05T203724Z",
                                 "920309f4af23176f159ebd3a51bbff2eedcc9b228c7e71647c578ad78a64b8fd",
                                 "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                                 "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "manufactures_exports": pin("world_bank_wdi", "TX.VAL.MANF.ZS.UN", "2026-04-30T115209Z",
                                "c5077c18a1ba1b953bc1cd66ac980f36b5cda7568fc3749126b91587cf17c98b",
                                "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
                                "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"),
    "fixed_investment": pin("world_bank_wdi", "NE.GDI.FTOT.ZS", "2026-05-05T203056Z",
                            "fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21",
                            "data/manifests/fetch_run_2026-05-05T203305Z.yaml",
                            "53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0"),
}
CASES = {
    "manufacturing_va": {"id": "wits_tariff_decline_manufacturing_value_added_forward_2026",
                         "label": "Manufacturing value added/GDP", "beta_min": 0.5},
    "industrial_employment": {"id": "wits_tariff_decline_industry_employment_forward_2026",
                              "label": "Industrial employment/total employment", "beta_min": 0.5},
    "manufactures_exports": {"id": "wits_tariff_decline_manufactures_export_share_forward_2026",
                             "label": "Manufactures/merchandise exports", "beta_min": 1.0},
    "fixed_investment": {"id": "wits_tariff_decline_fixed_investment_forward_2026",
                         "label": "Gross fixed capital formation/GDP", "beta_min": 0.5},
}
YEARS = {"tariff": (2005, 2010), "income": (2010,),
         **{role: (2000, 2010, 2019) for role in CASES}}


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
        raise RuntimeError(f"expected one first-addition commit for {path}: {revisions}")
    return revisions[0]


def committed_original(path: str, revision: str) -> None:
    if (ROOT / path).read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen file changed after registration or lock: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen file: {path}")


def earlier(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT).returncode == 0


def spec_rel(role: str) -> str:
    return f"hypotheses/trade/{CASES[role]['id']}.yaml"


def steelman_rel(role: str) -> str:
    return f"hypotheses/steelman/{CASES[role]['id']}.md"


def run_rel(role: str) -> str:
    return f"engine/runs/{CASES[role]['id']}"


def threshold(role: str) -> dict:
    return {"family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX,
            "meaningful_beta_min_pp_per_5pp_tariff_decline": CASES[role]["beta_min"],
            "min_complete_countries": MIN_N, "min_countries_decline_ge_2pp": MIN_ARM,
            "min_countries_decline_lt_2pp": MIN_ARM, "min_tariff_decline_iqr_pp": MIN_IQR,
            "max_country_residualized_exposure_share": MAX_CONCENTRATION,
            "max_loo_failure_share": MAX_LOO_FAILURE, "min_loo_sign_share": MIN_LOO_SIGN,
            "roster_sha256": ROSTER_SHA,
            "source_files": {key: {name: value for name, value in SOURCES[key].items()
                                   if name in ("path", "sha256", "manifest", "manifest_sha256")}
                             for key in ("tariff", "income", role)},
            "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
            "school_score_eligible": False, "school_score_credit": 0,
            "featured_eligible": False}


def registration_commit() -> str:
    paths = [RUNNER, PLAN, ROSTER]
    paths += [path for role in CASES for path in (spec_rel(role), steelman_rel(role))]
    revisions = {first_addition(path) for path in paths}
    if len(revisions) != 1:
        raise RuntimeError("registration files were not first added in one commit")
    revision = revisions.pop()
    for path in paths:
        committed_original(path, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK, SLICE).strip():
        raise RuntimeError("registration commit contained selected values")
    for role, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(role)).read_text())
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "descriptive" or spec.get("claim_direction") != "+"
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != [] or spec.get("steelman") != steelman_rel(role)
                or spec["falsification"]["threshold"] != threshold(role)):
            raise RuntimeError(f"frozen specification mismatch: {role}")
        if git("ls-tree", "-r", "--name-only", revision, "--", run_rel(role)).strip():
            raise RuntimeError("registration commit contained results")
    return revision


def source_custody_metadata() -> dict:
    output = {}
    for role, source in SOURCES.items():
        manifest_path = ROOT / source["manifest"]
        if file_sha(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"fetch manifest hash mismatch: {role}")
        entries = yaml.safe_load(manifest_path.read_text())["entries"]
        matches = [e for e in entries if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"fetch manifest does not custody selected file: {role}")
        e = matches[0]
        output[role] = {**source, "source_url": e.get("source_url"),
                        "methodology_url": e.get("methodology_url"),
                        "license": e.get("license"), "rows": e.get("rows")}
    return output


def source_custody(source_root: Path) -> dict:
    metadata = source_custody_metadata()
    for role, source in SOURCES.items():
        path = source_root / source["path"]
        if not path.is_file() or file_sha(path) != source["sha256"]:
            raise RuntimeError(f"source vintage missing or hash mismatch: {role}")
    return metadata


def source_keys(source_root: Path) -> list[str]:
    import pycountry
    permitted = {country.alpha_3 for country in pycountry.countries}
    eligible = permitted
    for role, source in SOURCES.items():
        frame = pd.read_parquet(source_root / source["path"], columns=["country_iso3", "year"])
        frame = frame[frame.country_iso3.isin(permitted) & frame.year.isin(YEARS[role])]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate selected country/year key: {role}")
        keys = set(map(tuple, frame[["country_iso3", "year"]].itertuples(index=False, name=None)))
        eligible = {country for country in eligible
                    if all((country, year) in keys for year in YEARS[role])}
    return sorted(eligible)


def roster_codes() -> list[str]:
    path = ROOT / ROSTER
    if file_sha(path) != ROSTER_SHA:
        raise RuntimeError("frozen key-roster hash mismatch")
    lines = path.read_text().splitlines()
    if lines[0] != "country_iso3" or lines[1:] != sorted(set(lines[1:])) or len(lines) != 216:
        raise RuntimeError("invalid fixed country roster")
    return lines[1:]


def preflight(source_root: Path) -> None:
    source_custody(source_root)
    codes = source_keys(source_root)
    if codes != roster_codes():
        raise RuntimeError("source-key roster changed")
    print(json.dumps({"candidate_codes": len(codes), "roster_sha256": ROSTER_SHA}, sort_keys=True))


def selected_csv(source_root: Path, codes: list[str]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["role", "country_iso3", "year", "value", "obs_status"])
    for role, source in SOURCES.items():
        frame = pd.read_parquet(source_root / source["path"],
                                columns=["country_iso3", "year", "value", "obs_status"])
        frame = frame[frame.country_iso3.isin(codes) & frame.year.isin(YEARS[role])]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate selected value key: {role}")
        expected = {(country, year) for country in codes for year in YEARS[role]}
        actual = set(map(tuple, frame[["country_iso3", "year"]].itertuples(index=False, name=None)))
        if actual != expected:
            raise RuntimeError(f"selected source keys changed: {role}")
        for row in frame.sort_values(["country_iso3", "year"]).itertuples(index=False):
            value = "" if pd.isna(row.value) else format(float(row.value), ".17g")
            status = "" if pd.isna(row.obs_status) else str(row.obs_status)
            writer.writerow([role, row.country_iso3, int(row.year), value, status])
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
    payload = {"schema": "ieset-tariff-decline-structure-source-lock-v1",
               "family": FAMILY, "registration_commit": revision,
               "candidate_codes": codes, "source_custody": custody,
               "source_slice": SLICE, "source_slice_sha256": file_sha(slice_path)}
    (ROOT / LOCK).write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"source_slice_rows": selected.count(b"\n") - 1,
                      "source_slice_sha256": payload["source_slice_sha256"]}, sort_keys=True))


def verified_lock() -> tuple[dict, str, str]:
    registered = registration_commit()
    revisions = {first_addition(path) for path in (LOCK, SLICE)}
    if len(revisions) != 1:
        raise RuntimeError("source lock files were not first added together")
    locked = revisions.pop()
    if not earlier(registered, locked):
        raise RuntimeError("source lock did not strictly follow registration")
    for path in (LOCK, SLICE):
        committed_original(path, locked)
    for role in CASES:
        if git("ls-tree", "-r", "--name-only", locked, "--", run_rel(role)).strip():
            raise RuntimeError("source lock commit already contained results")
    payload = json.loads((ROOT / LOCK).read_text())
    if (payload.get("family") != FAMILY or payload.get("registration_commit") != registered
            or payload.get("candidate_codes") != roster_codes()
            or payload.get("source_slice") != SLICE
            or payload.get("source_slice_sha256") != file_sha(ROOT / SLICE)
            or payload.get("source_custody") != source_custody_metadata()):
        raise RuntimeError("source lock content mismatch")
    return payload, registered, locked


def verify_source(source_root: Path) -> None:
    payload, _, _ = verified_lock()
    if source_custody(source_root) != payload["source_custody"]:
        raise RuntimeError("source custody differs")
    if source_keys(source_root) != roster_codes():
        raise RuntimeError("source-key roster differs")
    if selected_csv(source_root, roster_codes()) != (ROOT / SLICE).read_bytes():
        raise RuntimeError("source slice does not match the exact pinned vintages")
    print("Pinned source re-extraction matched source slice byte for byte")


def load_values() -> dict[str, dict[tuple[str, int], float | None]]:
    values = {role: {} for role in SOURCES}
    with (ROOT / SLICE).open(newline="") as fh:
        for row in csv.DictReader(fh):
            role = row["role"]
            key = (row["country_iso3"], int(row["year"]))
            if role not in values or key in values[role]:
                raise RuntimeError(f"invalid pinned row: {role}: {key}")
            values[role][key] = float(row["value"]) if row["value"] else None
    codes = roster_codes()
    for role in SOURCES:
        expected = {(country, year) for country in codes for year in YEARS[role]}
        if set(values[role]) != expected:
            raise RuntimeError(f"incomplete pinned source slice: {role}")
    return values


def bounded(value: float | None, lower: float, upper: float, *, positive: bool = False) -> bool:
    return value is not None and math.isfinite(value) and (value > lower if positive else value >= lower) and value <= upper


def sample_for(role: str, values: dict, codes: list[str]) -> tuple[pd.DataFrame, dict]:
    rows = []
    excluded = Counter()
    for country in codes:
        tariff_2005 = values["tariff"][(country, 2005)]
        tariff_2010 = values["tariff"][(country, 2010)]
        income = values["income"][(country, 2010)]
        y2000 = values[role][(country, 2000)]
        y2010 = values[role][(country, 2010)]
        y2019 = values[role][(country, 2019)]
        bad = []
        if not bounded(tariff_2005, 0, 100) or not bounded(tariff_2010, 0, 100):
            bad.append("tariff")
        if not bounded(income, 0, 1e9, positive=True):
            bad.append("income")
        if any(not bounded(value, 0, 100) for value in (y2000, y2010, y2019)):
            bad.append("outcome")
        if bad:
            excluded.update(bad)
            continue
        decline_pp = float(tariff_2005 - tariff_2010)
        rows.append({"country_iso3": country, "tariff_decline_pp": decline_pp,
                     "exposure_per_5pp": decline_pp / 5.0, "initial_tariff_2005": float(tariff_2005),
                     "log_income_2010": math.log(float(income)), "outcome_baseline_2010": float(y2010),
                     "outcome_pretrend_2000_2010": float(y2010 - y2000),
                     "outcome_change_2010_2019": float(y2019 - y2010)})
    frame = pd.DataFrame(rows, columns=["country_iso3", "tariff_decline_pp", "exposure_per_5pp",
                                        "initial_tariff_2005", "log_income_2010", "outcome_baseline_2010",
                                        "outcome_pretrend_2000_2010", "outcome_change_2010_2019"])
    return frame, {"source_key_candidate_countries": len(codes),
                   "complete_countries": len(frame), "excluded_reasons_overlap": dict(sorted(excluded.items()))}


def design(frame: pd.DataFrame, *, include_exposure: bool) -> pd.DataFrame:
    cols = ["initial_tariff_2005", "log_income_2010", "outcome_baseline_2010",
            "outcome_pretrend_2000_2010"]
    if include_exposure:
        cols = ["exposure_per_5pp", *cols]
    return sm.add_constant(frame[cols], has_constant="add")


def calculate(role: str, frame: pd.DataFrame, diag: dict) -> tuple[dict, str]:
    failures = []
    n = len(frame)
    diag["tariff_decline_ge_2pp_countries"] = int((frame.tariff_decline_pp >= 2).sum()) if n else 0
    diag["tariff_decline_lt_2pp_countries"] = n - diag["tariff_decline_ge_2pp_countries"]
    diag["tariff_decline_iqr_pp"] = float(frame.tariff_decline_pp.quantile(.75) - frame.tariff_decline_pp.quantile(.25)) if n else None
    if n < MIN_N: failures.append("min_complete_countries")
    if diag["tariff_decline_ge_2pp_countries"] < MIN_ARM: failures.append("min_decline_arm")
    if diag["tariff_decline_lt_2pp_countries"] < MIN_ARM: failures.append("min_comparator_arm")
    if n and diag["tariff_decline_iqr_pp"] < MIN_IQR: failures.append("min_tariff_decline_iqr")
    if failures:
        diag["failed_gates"] = failures
        return {}, "INCONCLUSIVE"
    controls = design(frame, include_exposure=False)
    full = design(frame, include_exposure=True)
    if (np.linalg.matrix_rank(np.asarray(controls)) != controls.shape[1]
            or np.linalg.matrix_rank(np.asarray(full)) != full.shape[1]):
        diag["failed_gates"] = ["design_rank"]
        return {}, "INCONCLUSIVE"
    residual = np.asarray(sm.OLS(frame.exposure_per_5pp, controls).fit().resid, dtype=float)
    denominator = float(np.sum(residual ** 2))
    if not math.isfinite(denominator) or denominator <= 1e-10:
        diag["failed_gates"] = ["residualized_exposure_variance"]
        return {}, "INCONCLUSIVE"
    concentration = float(np.max(residual ** 2) / denominator)
    diag["max_country_residualized_exposure_share"] = concentration
    if concentration > MAX_CONCENTRATION:
        diag["failed_gates"] = ["exposure_concentration"]
        return {}, "INCONCLUSIVE"
    model = sm.OLS(frame.outcome_change_2010_2019, full).fit(cov_type="HC3")
    beta = float(model.params["exposure_per_5pp"])
    se = float(model.bse["exposure_per_5pp"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        diag["failed_gates"] = ["finite_hc3_uncertainty"]
        return {}, "INCONCLUSIVE"
    pvalue = float(2 * student_t.sf(abs(beta / se), n - full.shape[1]))
    loo_betas = []
    loo_failures = 0
    for i in range(n):
        reduced = frame.drop(index=i)
        matrix = design(reduced, include_exposure=True)
        if np.linalg.matrix_rank(np.asarray(matrix)) != matrix.shape[1]:
            loo_failures += 1
            continue
        fit = sm.OLS(reduced.outcome_change_2010_2019, matrix).fit()
        value = float(fit.params["exposure_per_5pp"])
        if not math.isfinite(value):
            loo_failures += 1
        else:
            loo_betas.append(value)
    diag["loo_successes"] = len(loo_betas)
    diag["loo_failures"] = loo_failures
    diag["loo_positive_share"] = sum(value > 0 for value in loo_betas) / len(loo_betas) if loo_betas else 0
    diag["loo_negative_share"] = sum(value < 0 for value in loo_betas) / len(loo_betas) if loo_betas else 0
    if not loo_betas or loo_failures / n > MAX_LOO_FAILURE:
        diag["failed_gates"] = ["loo_success_floor"]
        return {}, "INCONCLUSIVE"
    diag["failed_gates"] = []
    estimate = {"coefficient": beta, "standard_error": se, "p_value": pvalue,
                "df": n - full.shape[1], "unit": "outcome share percentage points per five tariff points of reported decline"}
    threshold_beta = CASES[role]["beta_min"]
    if beta >= threshold_beta and pvalue <= P_MAX and diag["loo_positive_share"] >= MIN_LOO_SIGN:
        verdict = "SUPPORTED"
    elif beta <= -threshold_beta and pvalue <= P_MAX and diag["loo_negative_share"] >= MIN_LOO_SIGN:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return estimate, verdict


def json_write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(role: str, directory: Path, frame: pd.DataFrame, diag: dict, estimate: dict,
         verdict: str, registered: str, locked: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    case = CASES[role]
    (directory / "hypothesis.yaml").write_bytes((ROOT / spec_rel(role)).read_bytes())
    correction = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
                  "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
                  "bonferroni_p_max": P_MAX, "causal_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0,
                  "school_score_eligible": False, "school_score_credit": 0,
                  "featured_eligible": False}
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    lock_payload = json.loads((ROOT / LOCK).read_text())
    manifest = {"design_id": case["id"], "verdict": verdict, "evidence_type": "descriptive",
                "family_id": FAMILY, "spec_commit": registered, "lock_commit": locked,
                "spec_sha256": file_sha(ROOT / spec_rel(role)),
                "lock_sha256": file_sha(ROOT / LOCK), "runner_sha256": file_sha(ROOT / RUNNER),
                "source_slice_sha256": lock_payload["source_slice_sha256"],
                "source_custody": {key: lock_payload["source_custody"][key]
                                   for key in ("tariff", "income", role)},
                "artifacts": list(ARTIFACTS), "credit": credit}
    (directory / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    json_write(directory / "diagnostics.json", {**diag, "estimate": estimate, "verdict": verdict,
                                                "correction": correction, "analysis_scope": "descriptive_only"})
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["tariff_decline_per_5pp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                  ("standard_error", pa.float64()), ("p_value", pa.float64())]))
    json_write(directory / "chart_data.json", [
        {"country_iso3": str(row.country_iso3), "tariff_decline_pp": float(row.tariff_decline_pp),
         "outcome_change_pp_2010_2019": float(row.outcome_change_2010_2019)}
        for row in frame.itertuples(index=False)])
    lines = [f"# {case['label']} after reported tariff decline", "",
             f"**{verdict} — descriptive calibration only.**", "",
             f"Complete economies: {len(frame)} of {diag['source_key_candidate_countries']} source-key candidates.",
             f"Reported tariff-decline IQR: {diag['tariff_decline_iqr_pp']:.6g} percentage points." if len(frame) else "No complete observations."]
    if has_estimate:
        lines += [f"Coefficient {estimate['coefficient']:.6g} outcome points per five tariff points; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}.",
                  f"Leave-one-country-out positive share {diag['loo_positive_share']:.3f}; negative share {diag['loo_negative_share']:.3f}."]
    else:
        lines += ["No qualifying coefficient because frozen gates failed.",
                  f"Failed gates: {', '.join(diag['failed_gates'])}."]
    lines += ["", "The tariff series is import-weighted and may change with import composition. The four outcomes are correlated. No causal, tariff-policy, school, position, or featured credit follows.", ""]
    (directory / "result_card.md").write_text("\n".join(lines))
    (directory / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER}'), '--verify', *sys.argv[1:]], check=True)\n")
    packet = {"design_id": case["id"], "verdict": verdict, "evidence_type": "descriptive",
              "causal_claim": False, "policy_effect_credit": False, "school_claim_links": [],
              "correction": correction, "source_hashes_verified": True,
              "strict_spec_lock_chronology_verified": True,
              "interpretation": f"2010–2019 {case['label'].lower()} change associated with a prior reported tariff decline; no tariff-policy effect."}
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict], "complete_countries": [len(frame)]},
        pa.schema([("verdict", pa.string()), ("complete_countries", pa.int64())]))
    if tuple(sorted(path.name for path in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise RuntimeError("run artifact roster mismatch")


def result_summary(results: list[dict]) -> str:
    lines = ["# Weighted tariff decline and four later structural outcomes — frozen results", "",
             "Four source-locked descriptive tests share a 2005–2010 reported tariff decline. Outcome changes are exact 2010–2019 percentage-point differences. Each endpoint has its own complete-country sample; the fixed Bonferroni denominator is four, including inconclusive cases. None identifies an enacted tariff policy or receives causal, policy, school, position or featured credit.", "",
             "| Outcome | Complete countries | Beta per five tariff points | HC3 SE | Two-sided p | Verdict |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for row in results:
        estimate = row["estimate"]
        fmt = lambda key: f"{estimate[key]:.6g}" if key in estimate else "—"
        lines.append(f"| {row['label']} | {row['countries']} | {fmt('coefficient')} | {fmt('standard_error')} | {fmt('p_value')} | {row['verdict']} |")
    lines += ["", "Weighted tariffs depend on import composition and partner mix. Manufacturing value added, industrial employment, manufactured export share and fixed investment are different outcomes, but are correlated. The design controls measured baseline variables and cannot isolate policy effects or settle older archive claims.", ""]
    return "\n".join(lines)


def run_or_verify(verify: bool) -> None:
    _, registered, locked = verified_lock()
    values = load_values()
    codes = roster_codes()
    results = []
    with tempfile.TemporaryDirectory(prefix="ieset_tariff_decline_") as tmp:
        for role in CASES:
            frame, diag = sample_for(role, values, codes)
            estimate, verdict = calculate(role, frame, diag)
            generated = Path(tmp) / role
            emit(role, generated, frame, diag, estimate, verdict, registered, locked)
            target = ROOT / run_rel(role)
            if verify:
                if not target.is_dir():
                    raise RuntimeError(f"missing run: {role}")
                for artifact in ARTIFACTS:
                    if file_sha(generated / artifact) != file_sha(target / artifact):
                        raise RuntimeError(f"exact replay differs: {role}/{artifact}")
            else:
                if target.exists():
                    raise RuntimeError(f"run already exists: {role}")
                shutil.copytree(generated, target)
            results.append({"role": role, "label": CASES[role]["label"],
                            "countries": len(frame), "estimate": estimate,
                            "verdict": verdict, "failed_gates": diag["failed_gates"]})
    summary = result_summary(results)
    if verify:
        if (ROOT / SUMMARY).read_text() != summary:
            raise RuntimeError("result summary differs on replay")
        print("Exact replay matched four result summaries and all 36 run artifacts")
    else:
        (ROOT / SUMMARY).write_text(summary)
        print(json.dumps(results, sort_keys=True, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    for action in ("preflight", "lock", "verify-source", "run", "verify"):
        choices.add_argument("--" + action, action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.preflight:
        preflight(args.source_root)
    elif args.lock:
        lock(args.source_root)
    elif args.verify_source:
        verify_source(args.source_root)
    elif args.run:
        run_or_verify(False)
    else:
        run_or_verify(True)


if __name__ == "__main__":
    main()
