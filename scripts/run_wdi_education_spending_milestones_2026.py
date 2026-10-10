#!/usr/bin/env python3
"""Six frozen, descriptive education-spending/milestone calibrations.

Preflight reads source identities and country/year keys only. Lock reads values
only after the registration commit and never estimates. Run requires a later,
committed source lock; replay rebuilds every result artifact byte for byte.
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
FAMILY = "wdi_education_spending_milestones_2026_10_10"
RUNNER = "scripts/run_wdi_education_spending_milestones_2026.py"
PLAN = "engine/audits/wdi_education_spending_milestones_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_education_spending_milestones_key_roster.csv"
ROSTER_SHA = "a7b8e33e420cd1c0ce8160ad4e03e1102440d184842dd450027a446df26e8638"
SLICE = "data/pinned_evidence/wdi_education_spending_milestones_source_slice.csv"
LOCK = "data/pinned_evidence/wdi_education_spending_milestones.manifest.json"
SUMMARY = "engine/audits/wdi_education_spending_milestones_results_2026-10-10.md"
ARTIFACTS = ("hypothesis.yaml", "manifest.yaml", "diagnostics.json",
             "coefficients.parquet", "chart_data.json", "result_card.md",
             "replication.py", "evidence_packet.yaml", "metric_results.parquet")

START, END, HORIZON = 2000, 2018, 3
FAMILY_SIZE = 6
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
BETA_MIN = 1.0  # milestone percentage points over three years per +1 GDP percentage point
MIN_PAIRS, MIN_COUNTRIES, MIN_COUNTRY_PAIRS = 150, 20, 3
MIN_MATERIAL_COUNTRIES, MATERIAL_RANGE_PP = 12, 0.5
MAX_COUNTRY_RESIDUAL_SHARE, MAX_YEAR_RESIDUAL_SHARE = 0.25, 0.20

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
    "spending": pin("SE.XPD.TOTL.GD.ZS", "2026-05-05T204028Z",
                    "0f21a848f064c16fce431b5425f5fb51519044c3e88256f329821b00504cc501",
                    MAY_MANIFEST, MAY_MANIFEST_SHA),
    "income": pin("NY.GDP.PCAP.KD", "2026-05-05T194645Z",
                  "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
                  EARLY_MANIFEST, EARLY_MANIFEST_SHA),
    "growth": pin("NY.GDP.MKTP.KD.ZG", "2026-05-05T194655Z",
                  "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
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
    "bachelor_attainment": pin("SE.TER.CUAT.BA.ZS", "2026-04-30T140201Z",
                               "2a075d3a95a43f49d2bdfd89e4425ea31c424fe87cc85d43f9e8192fd37cb9f4",
                               "data/manifests/fetch_run_2026-04-30T140220Z.yaml",
                               "d4bdfeeee67f35f05e1885e60b51f25c163aacb70844edacae05b15e18479e23"),
}
CASES = {
    "primary_completion": {"id": "wdi_education_spending_primary_completion_forward_2026",
                           "label": "Primary completion rate", "bound": 150.0, "topic": "fiscal"},
    "secondary_net_enrolment": {"id": "wdi_education_spending_secondary_net_enrolment_forward_2026",
                                "label": "Secondary net enrolment rate", "bound": 100.0, "topic": "fiscal"},
    "tertiary_enrolment": {"id": "wdi_education_spending_tertiary_enrolment_forward_2026",
                             "label": "Tertiary gross enrolment ratio", "bound": 200.0, "topic": "fiscal"},
    "adult_literacy": {"id": "wdi_education_spending_adult_literacy_forward_2026",
                       "label": "Adult literacy rate", "bound": 100.0, "topic": "fiscal"},
    "upper_secondary_attainment": {"id": "wdi_education_spending_upper_secondary_attainment_forward_2026",
                                   "label": "Adults 25+ with upper-secondary attainment", "bound": 100.0, "topic": "fiscal"},
    "bachelor_attainment": {"id": "wdi_education_spending_bachelor_attainment_forward_2026",
                            "label": "Adults 25+ with bachelor's attainment", "bound": 100.0, "topic": "fiscal"},
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
    return f"hypotheses/fiscal/{CASES[key]['id']}.yaml"


def steelman_rel(key: str) -> str:
    return f"hypotheses/steelman/{CASES[key]['id']}.md"


def run_rel(key: str) -> str:
    return f"engine/runs/{CASES[key]['id']}"


def threshold(key: str) -> dict:
    return {"family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "meaningful_beta_min_pp": BETA_MIN,
            "min_complete_pairs": MIN_PAIRS, "min_countries": MIN_COUNTRIES,
            "min_pairs_per_country": MIN_COUNTRY_PAIRS,
            "min_material_countries": MIN_MATERIAL_COUNTRIES,
            "material_within_country_spending_range_pp": MATERIAL_RANGE_PP,
            "max_country_residualized_exposure_share": MAX_COUNTRY_RESIDUAL_SHARE,
            "max_year_residualized_exposure_share": MAX_YEAR_RESIDUAL_SHARE,
            "outcome_valid_max": CASES[key]["bound"],
            "roster_sha256": ROSTER_SHA,
            "source_files": {role: {k: v for k, v in SOURCES[role].items()
                                    if k in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role in ("spending", "income", "growth", key)},
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
        raise RuntimeError("frozen country roster hash mismatch")
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
        frame = frame[frame.country_iso3.isin(permitted) & frame.year.between(START, END + HORIZON)]
        if frame.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate source country/year keys: {source['series_id']}")
        keys.append(set(map(tuple, frame[["country_iso3", "year"]].itertuples(index=False, name=None))))
    joint = set.intersection(*keys)
    required = set(range(START, END + HORIZON + 1))
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
    year_set = set(range(START, END + HORIZON + 1))
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
    payload = {"schema": "ieset-education-milestones-source-lock-v1",
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
            values[role][key] = float(row["value"]) if row["value"] else None
    expected_rows = len(roster_codes()) * (END + HORIZON - START + 1)
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
            source_key = (country, year)
            future_key = (country, year + HORIZON)
            spending = values["spending"][source_key]
            income = values["income"][source_key]
            growth = values["growth"][source_key]
            y0 = values[key][source_key]
            y3 = values[key][future_key]
            bad = []
            if not valid(spending, 0, 30, open_low=True): bad.append("spending")
            if not valid(income, 0, 1e9, open_low=True): bad.append("income")
            if not valid(growth, -100, 100): bad.append("gdp_growth")
            if not valid(y0, 0, bound) or not valid(y3, 0, bound): bad.append("outcome")
            if bad:
                excluded.update(bad)
                continue
            rows.append({"country_iso3": country, "year": year, "spending": spending,
                         "log_income": math.log(income), "gdp_growth": growth,
                         "baseline": y0, "change": y3 - y0})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "spending", "log_income",
                                        "gdp_growth", "baseline", "change"])
    initial_pairs = len(panel)
    if initial_pairs:
        counts = panel.groupby("country_iso3").year.transform("size")
        panel = panel[counts >= MIN_COUNTRY_PAIRS].copy()
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    diagnostics = {"source_key_candidate_countries": len(codes),
                   "source_key_candidate_pairs": len(codes) * (END - START + 1),
                   "pre_country_floor_complete_pairs": initial_pairs,
                   "complete_pairs": len(panel),
                   "complete_countries": int(panel.country_iso3.nunique()),
                   "excluded_reasons_overlap": dict(sorted(excluded.items()))}
    return panel, diagnostics


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict, str]:
    failures = []
    n, countries = len(panel), diag["complete_countries"]
    if n < MIN_PAIRS: failures.append("min_complete_pairs")
    if countries < MIN_COUNTRIES: failures.append("min_countries")
    if n:
        spread = panel.groupby("country_iso3").spending.agg(lambda x: float(x.max() - x.min()))
        material = int((spread >= MATERIAL_RANGE_PP).sum())
    else:
        material = 0
    diag["material_spending_countries"] = material
    if material < MIN_MATERIAL_COUNTRIES: failures.append("min_material_countries")
    if failures:
        diag["failed_gates"] = failures
        return {}, "INCONCLUSIVE"
    control_formula = "spending ~ baseline + log_income + gdp_growth + C(country_iso3) + C(year)"
    partial = smf.ols(control_formula, panel).fit()
    residual = np.asarray(partial.resid, dtype=float)
    denom = float(np.sum(residual ** 2))
    if not math.isfinite(denom) or denom <= 1e-8:
        diag["failed_gates"] = ["residualized_exposure_variance"]
        return {}, "INCONCLUSIVE"
    weights = panel[["country_iso3", "year"]].copy()
    weights["sq"] = residual ** 2
    country_max = float(weights.groupby("country_iso3").sq.sum().max() / denom)
    year_max = float(weights.groupby("year").sq.sum().max() / denom)
    diag["max_country_residualized_exposure_share"] = country_max
    diag["max_year_residualized_exposure_share"] = year_max
    if country_max > MAX_COUNTRY_RESIDUAL_SHARE: failures.append("country_concentration")
    if year_max > MAX_YEAR_RESIDUAL_SHARE: failures.append("year_concentration")
    if failures:
        diag["failed_gates"] = failures
        return {}, "INCONCLUSIVE"
    model = smf.ols("change ~ spending + baseline + log_income + gdp_growth + C(country_iso3) + C(year)", panel)
    if np.linalg.matrix_rank(model.exog) < model.exog.shape[1]:
        diag["failed_gates"] = ["design_rank"]
        return {}, "INCONCLUSIVE"
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3})
    beta, se = float(fit.params["spending"]), float(fit.bse["spending"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        diag["failed_gates"] = ["finite_cluster_uncertainty"]
        return {}, "INCONCLUSIVE"
    pvalue = float(2 * student_t.sf(abs(beta / se), countries - 1))
    estimate = {"coefficient": beta, "standard_error": se, "p_value": pvalue,
                "country_cluster_df": countries - 1,
                "unit": "outcome percentage-point change over three years per +1 percentage point of GDP education spending"}
    diag["failed_gates"] = []
    if beta >= BETA_MIN and pvalue <= P_MAX: verdict = "SUPPORTED"
    elif beta <= -BETA_MIN and pvalue <= P_MAX: verdict = "REFUTED"
    else: verdict = "PARTIAL"
    return estimate, verdict


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
                                   for role in ("spending", "income", "growth", key)},
                "artifacts": list(ARTIFACTS), "credit": credit}
    (directory / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    json_write(directory / "diagnostics.json",
               {**diag, "estimate": estimate, "verdict": verdict,
                "correction": correction, "analysis_scope": "descriptive_only"})
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["education_spending_pct_gdp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                  ("standard_error", pa.float64()), ("p_value", pa.float64())]))
    json_write(directory / "chart_data.json", [
        {"country_iso3": str(r.country_iso3), "year": int(r.year),
         "education_spending_pct_gdp": float(r.spending),
         "outcome_change_pp_3yr": float(r.change)}
        for r in panel.itertuples(index=False)])
    lines = [f"# {case['label']} after education spending", "",
             f"**{verdict} — descriptive calibration only.**", "",
             f"Complete country-year pairs: {len(panel)} across {diag['complete_countries']} economies.",
             f"Material-spending countries: {diag['material_spending_countries']}."]
    if has_estimate:
        lines += [f"Coefficient {estimate['coefficient']:.6g} outcome points per +1 GDP point of spending; country-cluster SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}."]
    else:
        lines += ["No coefficient was estimated because a frozen sample or method gate failed.",
                  f"Failed gates: {', '.join(diag['failed_gates'])}."]
    lines += ["", "Spending as a GDP share is neither an enacted education policy nor spending per student. The six outcomes are correlated educational milestones; the fixed six-test Bonferroni rule applies. No causal, policy, school, position, or featured credit follows.", ""]
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
              "interpretation": f"Three-year {case['label'].lower()} change associated with prior education expenditure share; no education-policy effect."}
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict], "complete_pairs": [len(panel)],
        "complete_countries": [diag["complete_countries"]],
    }, pa.schema([("verdict", pa.string()), ("complete_pairs", pa.int64()),
                  ("complete_countries", pa.int64())]))
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise RuntimeError("run artifact roster mismatch")


def result_summary(results: list[dict]) -> str:
    lines = ["# Education spending and six educational milestones — frozen results", "",
             "The six prospectively registered, source-locked tests use the same WDI education-spending share and distinct but correlated educational milestones. Each has its own complete-case panel and country/year fixed effects. The family denominator is six even when a test is inconclusive. Directional p cutoff is 0.01/6. All results are descriptive and receive zero causal, policy, school, position, and featured credit.", "",
             "| Outcome | Complete pairs / countries | Beta | Country-cluster SE | Two-sided p | Verdict |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for r in results:
        e = r["estimate"]
        fmt = lambda name: f"{e[name]:.6g}" if name in e else "—"
        lines.append(f"| {r['label']} | {r['pairs']} / {r['countries']} | {fmt('coefficient')} | {fmt('standard_error')} | {fmt('p_value')} | {r['verdict']} |")
    lines += ["", "The education-expenditure share can move when GDP changes, and outcomes may respond to past performance. Data missingness and uneven reporting limit this descriptive panel. These estimates do not identify education policy effects or grade old school claims.", ""]
    return "\n".join(lines)


def run_or_verify(verify: bool) -> None:
    _, registered, locked = verified_lock()
    values = load_values()
    codes = roster_codes()
    results = []
    with tempfile.TemporaryDirectory(prefix="ieset_education_milestones_") as tmp:
        for key in CASES:
            panel, diag = panel_for(key, values, codes)
            estimate, verdict = calculate(panel, diag)
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
                            "estimate": estimate, "verdict": verdict,
                            "failed_gates": diag["failed_gates"]})
    summary = result_summary(results)
    if verify:
        if (ROOT / SUMMARY).read_text() != summary:
            raise RuntimeError("result summary differs on replay")
        print("Exact replay matched six result summaries and all 54 run artifacts")
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
