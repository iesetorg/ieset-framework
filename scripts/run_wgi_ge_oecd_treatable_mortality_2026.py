#!/usr/bin/env python3
"""Guarded prospective WGI-to-OECD descriptive calibration.

Preflight and lock project OECD selector/key columns only. Measured OECD
columns are first read by run/verify after the source-lock commit is checked.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
STUDY = "wgi_ge_oecd_treatable_mortality_forward_2026"
SPEC = f"hypotheses/healthcare/{STUDY}.yaml"
STEELMAN = f"hypotheses/steelman/{STUDY}.md"
PREREG = "engine/audits/wgi_ge_oecd_treatable_mortality_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wgi_ge_oecd_treatable_mortality_2026_key_roster.csv"
RUNNER = "scripts/run_wgi_ge_oecd_treatable_mortality_2026.py"
TESTS = "tests/test_wgi_ge_oecd_treatable_mortality_2026.py"
LOCK = "data/pinned_evidence/wgi_ge_oecd_treatable_mortality_2026_source_lock.json"
RESULT_DIR = f"engine/runs/{STUDY}"
ROSTER_SHA = "15f38fe6043ad1a2c45224ee7424824699201ffd0c45754a559043d68b90e608"
EXPECTED_KEYS = 781
EXPECTED_COUNTRIES = 45
YEAR_START, YEAR_END = 2000, 2018
MIN_YEARS = 8
MIN_ROWS, MIN_COUNTRIES = 450, 30
MAX_TOP_ROWS, MAX_COUNTRY, MAX_YEAR = 0.20, 0.15, 0.20
P_MAX, MIN_BETA = 0.01, 0.05
SOURCES: dict[str, dict[str, str]] = {
    "ge": {
        "publisher": "wgi", "series_id": "GOV_WGI_GE.EST",
        "path": "data/vintages/wgi/GOV_WGI_GE.EST@2026-05-05T195208Z.parquet",
        "sha256": "607d47979340b803fec2fefc1e57c94a7a167432317451ea0b1ade3ee0503edc",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
    "income": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    },
    "mortality": {
        "publisher": "oecd",
        "series_id": "OECD.ELS.HD,DSD_HEALTH_STAT@DF_AMENABLE_MORT,1.0",
        "path": "data/vintages/oecd/OECD.ELS.HD_DSD_HEALTH_STAT_DF_AMENABLE_MORT_1.0@2026-05-01T071213Z.parquet",
        "sha256": "e00d243302893fb2bcf455a6d75ab8e5467a208186683d52d291f235a4279f94",
        "manifest": "data/manifests/fetch_run_2026-05-01T071226Z.yaml",
        "manifest_sha256": "bf47fbd459e6074ad737def46b88a7fb9fa86d317fb0666567e50931ea861148",
    },
}
OUTCOME_FILTERS = {
    "FREQ": "A", "MEASURE": "TRTM", "UNIT_MEASURE": "DT_10P5HB",
    "AGE": "_T", "SEX": "_T", "CALC_METHODOLOGY": "STANDARD",
    "SOCIO_ECON_STATUS": "_Z", "DEATH_CAUSE": "_Z",
    "GESTATION_THRESHOLD": "_Z", "HEALTH_STATUS": "_Z",
    "DISEASE": "_Z", "CANCER_SITE": "_Z",
}
OUTCOME_KEY_COLUMNS = ["REF_AREA", "period", *OUTCOME_FILTERS]
OUTCOME_MEASURED_COLUMNS = ["value", "Observation value", "OBS_STATUS", "OBS_STATUS2", "OBS_STATUS3"]
REGISTRATION_FILES = [SPEC, STEELMAN, PREREG, ROSTER, RUNNER, TESTS]
LIMITATIONS = [
    "WGI is a perceptions-based governance composite, not a health-policy intervention.",
    "The one-year lead and fixed effects do not identify a causal effect or remove country-specific time-varying confounding.",
    "OECD mortality cause coding and WGI methods may change despite the selected status screen.",
    "The same OECD mortality vintage appears in earlier IESET studies; this is not an independent archive holdout.",
    "No causal, policy, school, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(relative: str) -> str:
    lines = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not lines:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return lines[-1]


def frozen_file(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"registered file changed from first addition: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted registered file: {relative}")


def is_ancestor(older: str, newer: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT).returncode == 0


def registration_commit() -> str:
    additions = {first_addition(path) for path in REGISTRATION_FILES}
    if len(additions) != 1:
        raise RuntimeError("six registration files need one shared first-addition commit")
    revision = additions.pop()
    if not is_ancestor(revision, git("rev-parse", "HEAD").decode().strip()):
        raise RuntimeError("registration commit is not in current history")
    for path in REGISTRATION_FILES:
        frozen_file(path, revision)
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen key roster hash mismatch")
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK, RESULT_DIR).strip():
        raise RuntimeError("registration commit contains a source lock or measured result")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = spec.get("falsification", {}).get("threshold", {})
    expected = {
        "p_max_two_sided": P_MAX, "meaningful_beta_min_abs": MIN_BETA,
        "min_complete_pairs": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
        "min_years_per_country": MIN_YEARS,
        "max_top_one_percent_partialled_treatment_share": MAX_TOP_ROWS,
        "max_top_country_partialled_treatment_share": MAX_COUNTRY,
        "max_top_year_partialled_treatment_share": MAX_YEAR,
        "expected_key_pairs": EXPECTED_KEYS, "expected_key_countries": EXPECTED_COUNTRIES,
        "key_roster_sha256": ROSTER_SHA,
    }
    if (spec.get("hypothesis_id") != STUDY or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-"
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != [] or spec.get("steelman") != STEELMAN
            or spec.get("sample", {}).get("period") != [YEAR_START, YEAR_END]
            or any(threshold.get(k) != v for k, v in expected.items())
            or threshold.get("causal_credit") != 0
            or threshold.get("policy_score_eligible") is not False
            or threshold.get("school_score_eligible") is not False
            or threshold.get("featured_eligible") is not False):
        raise RuntimeError("frozen spec does not match guarded design")
    return revision


def check_sources(source_root: Path) -> dict[str, dict[str, str]]:
    checked = {}
    for role, source in SOURCES.items():
        raw = source_root / source["path"]
        manifest = source_root / source["manifest"]
        if not raw.is_file() or sha256(raw) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned raw source: {role}")
        if not manifest.is_file() or sha256(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched tracked fetch manifest: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"fetch manifest lacks exact source entry: {role}")
        checked[role] = {**source, **{field: matches[0].get(field) for field in
                          ("source_url", "methodology_url", "license", "fetch_utc",
                           "start_date", "end_date", "frequency", "units")}}
    return checked


def valid_iso3(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.fullmatch(r"[A-Z]{3}")


def treatment_control(source_root: Path) -> pd.DataFrame:
    columns = ["country_iso3", "indicator_id", "year", "value"]
    frames = []
    for role, expected_id in (("ge", "GOV_WGI_GE.EST"), ("income", "NY.GDP.PCAP.KD")):
        raw = pq.read_table(source_root / SOURCES[role]["path"], columns=columns).to_pandas()
        raw = raw.loc[raw.indicator_id.eq(expected_id) & valid_iso3(raw.country_iso3)].copy()
        raw["year"] = pd.to_numeric(raw.year, errors="coerce")
        raw = raw.loc[raw.year.between(YEAR_START, YEAR_END)].copy()
        if raw.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate {role} national country/year key")
        raw["value"] = pd.to_numeric(raw.value, errors="coerce")
        good = np.isfinite(raw.value)
        good &= raw.value.between(-3, 3) if role == "ge" else raw.value.gt(0)
        raw = raw.loc[good, ["country_iso3", "year", "value"]].copy()
        raw["year"] = raw.year.astype(int)
        frames.append(raw.rename(columns={"value": role}))
    joined = frames[0].merge(frames[1], on=["country_iso3", "year"], validate="one_to_one")
    joined["log_income"] = np.log(joined.income.astype(float))
    return joined[["country_iso3", "year", "ge", "log_income"]]


def outcome_rows(source_root: Path, *, measured: bool) -> pd.DataFrame:
    # This projection is the blindness boundary. Do not add measured columns
    # to the preflight/lock branch.
    columns = OUTCOME_KEY_COLUMNS + (OUTCOME_MEASURED_COLUMNS if measured else [])
    raw = pq.read_table(source_root / SOURCES["mortality"]["path"], columns=columns).to_pandas()
    for field, wanted in OUTCOME_FILTERS.items():
        raw = raw.loc[raw[field].eq(wanted)]
    raw = raw.loc[valid_iso3(raw.REF_AREA)].copy()
    raw["period"] = pd.to_numeric(raw.period, errors="coerce")
    raw = raw.loc[raw.period.between(YEAR_START + 1, YEAR_END + 1)].copy()
    if raw.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate selected OECD country/year key")
    raw["year"] = raw.period.astype(int) - 1
    raw = raw.rename(columns={"REF_AREA": "country_iso3"})
    keep = ["country_iso3", "year"] + (OUTCOME_MEASURED_COLUMNS if measured else [])
    return raw[keep].sort_values(["country_iso3", "year"]).reset_index(drop=True)


def frozen_roster() -> pd.DataFrame:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("key-only roster hash mismatch")
    roster = pd.read_csv(path)
    if list(roster.columns) != ["country_iso3", "year"] or roster.duplicated().any():
        raise RuntimeError("invalid key-only roster")
    if len(roster) != EXPECTED_KEYS or roster.country_iso3.nunique() != EXPECTED_COUNTRIES:
        raise RuntimeError("key-only roster envelope changed")
    ordered = roster.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    if not roster.reset_index(drop=True).equals(ordered):
        raise RuntimeError("key-only roster order changed")
    return roster


def concentration(panel: pd.DataFrame) -> dict[str, float]:
    fit = smf.ols("ge ~ log_income + C(country_iso3) + C(year)", data=panel).fit()
    resid = np.asarray(fit.resid, dtype=float)
    squares = np.square(resid)
    total = float(squares.sum())
    if not math.isfinite(total) or total <= 0:
        raise RuntimeError("zero/nonfinite partialled treatment variation")
    count = max(1, math.ceil(len(squares) * 0.01))
    top_rows = float(np.sort(squares)[-count:].sum() / total)
    by_country = pd.Series(squares).groupby(panel.country_iso3.reset_index(drop=True)).sum()
    by_year = pd.Series(squares).groupby(panel.year.reset_index(drop=True)).sum()
    return {"top_one_percent_rows": top_rows, "top_country": float(by_country.max() / total),
            "top_year": float(by_year.max() / total)}


def preflight_panel(source_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    check_sources(source_root)
    treatment = treatment_control(source_root)
    outcome_keys = outcome_rows(source_root, measured=False)  # no values, masks, or statuses
    panel = treatment.merge(outcome_keys, on=["country_iso3", "year"], validate="one_to_one")
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts >= MIN_YEARS].index)].copy()
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    if not panel[["country_iso3", "year"]].equals(frozen_roster()):
        raise RuntimeError("preflight keys differ from frozen roster")
    summary = {"key_pairs": len(panel), "key_countries": panel.country_iso3.nunique(),
               "partialled_treatment_concentration": concentration(panel)}
    return panel, summary


def lock_payload(registration: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "study_id": STUDY,
        "registration_commit": registration,
        "key_roster_sha256": ROSTER_SHA,
        "sources": SOURCES,
        "preflight": summary,
        "measurement_permitted_only_after_separate_lock_commit": True,
    }


def canonical_json(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def create_lock(source_root: Path) -> Path:
    registration = registration_commit()
    if git("rev-parse", "HEAD").decode().strip() != registration:
        raise RuntimeError("lock must be generated immediately after registration commit")
    _, summary = preflight_panel(source_root)
    destination = ROOT / LOCK
    if destination.exists() or (ROOT / RESULT_DIR).exists():
        raise RuntimeError("source lock or measured result already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json(lock_payload(registration, summary)))
    return destination


def committed_lock(source_root: Path) -> tuple[str, str, pd.DataFrame]:
    registration = registration_commit()
    revision = first_addition(LOCK)
    if revision == registration or not is_ancestor(registration, revision):
        raise RuntimeError("source lock must be first added in a later commit")
    if not is_ancestor(revision, git("rev-parse", "HEAD").decode().strip()):
        raise RuntimeError("source lock commit is not in current history")
    frozen_file(LOCK, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RESULT_DIR).strip():
        raise RuntimeError("source-lock commit already contains measured results")
    panel, summary = preflight_panel(source_root)  # outcome keys only
    expected = canonical_json(lock_payload(registration, summary))
    if (ROOT / LOCK).read_bytes() != expected:
        raise RuntimeError("source-lock content does not match pinned preflight")
    return registration, revision, panel


def clean_outcome(selected: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen post-lock value/status rule, without trimming magnitudes."""
    data = selected.copy()
    values = pd.to_numeric(data["value"], errors="coerce")
    originals = pd.to_numeric(data["Observation value"], errors="coerce")
    accepted = np.isfinite(values) & np.isfinite(originals) & values.gt(0)
    accepted &= np.isclose(values, originals, rtol=1e-8, atol=1e-8)
    for field in ("OBS_STATUS", "OBS_STATUS2", "OBS_STATUS3"):
        accepted &= data[field].fillna("").astype(str).str.strip().isin(["", "A"])
    clean = data.loc[accepted, ["country_iso3", "year"]].copy()
    clean["log_mortality"] = np.log(values.loc[accepted].astype(float).to_numpy())
    return clean


def classify(beta: float, p_value: float) -> str:
    if beta <= -MIN_BETA and p_value <= P_MAX:
        return "SUPPORTED"
    if beta >= MIN_BETA and p_value <= P_MAX:
        return "REFUTED"
    return "PARTIAL"


def estimate(panel: pd.DataFrame) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    """Return fitted statistics only after every sample/concentration gate passes."""
    failures = []
    counts = panel.groupby("country_iso3").size()
    eligible = panel.loc[panel.country_iso3.isin(counts[counts >= MIN_YEARS].index)].copy()
    eligible = eligible.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    diagnostics: dict[str, Any] = {
        "complete_pairs_before_country_floor": len(panel),
        "complete_pairs": len(eligible),
        "complete_countries": int(eligible.country_iso3.nunique()),
        "min_complete_years_per_retained_country": int(eligible.groupby("country_iso3").size().min()) if len(eligible) else 0,
    }
    if len(eligible) < MIN_ROWS:
        failures.append("complete_pair_floor")
    if eligible.country_iso3.nunique() < MIN_COUNTRIES:
        failures.append("complete_country_floor")
    if failures:
        return None, failures, diagnostics
    try:
        shares = concentration(eligible)
        diagnostics["partialled_treatment_concentration"] = shares
        if shares["top_one_percent_rows"] > MAX_TOP_ROWS:
            failures.append("top_one_percent_row_concentration")
        if shares["top_country"] > MAX_COUNTRY:
            failures.append("country_concentration")
        if shares["top_year"] > MAX_YEAR:
            failures.append("year_concentration")
        if failures:
            return None, failures, diagnostics
        fitted = smf.ols("log_mortality ~ ge + log_income + C(country_iso3) + C(year)", data=eligible).fit()
        matrix = np.asarray(fitted.model.exog, dtype=float)
        if np.linalg.matrix_rank(matrix) != matrix.shape[1]:
            return None, ["design_rank"], diagnostics
        robust = fitted.get_robustcov_results(cov_type="cluster", groups=eligible.country_iso3,
                                                use_t=True, use_correction=True)
        index = list(fitted.params.index).index("ge")
        beta, se = float(robust.params[index]), float(robust.bse[index])
        if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
            return None, ["cluster_uncertainty"], diagnostics
        degrees = int(eligible.country_iso3.nunique() - 1)
        statistic = beta / se
        p_value = float(2 * student_t.sf(abs(statistic), degrees))
        radius = float(student_t.ppf(0.995, degrees) * se)
        if not all(map(math.isfinite, (p_value, radius))):
            return None, ["cluster_uncertainty"], diagnostics
        estimates = {"beta_log_points_per_wgi_point": beta, "cluster_se": se,
                     "two_sided_p": p_value, "t_df": degrees,
                     "confidence_interval_99_pct": [beta - radius, beta + radius],
                     "verdict": classify(beta, p_value)}
        return estimates, [], diagnostics
    except (ValueError, np.linalg.LinAlgError, FloatingPointError, ZeroDivisionError) as exc:
        diagnostics["model_gate_error"] = type(exc).__name__
        return None, ["model_or_variation_gate"], diagnostics


def measured_result(source_root: Path, registration: str, lock_revision: str,
                    preflight: pd.DataFrame) -> dict[str, Any]:
    # Caller MUST establish committed_lock before reaching this function.
    measured = outcome_rows(source_root, measured=True)
    clean = clean_outcome(measured)
    complete = preflight.merge(clean, on=["country_iso3", "year"], validate="one_to_one")
    estimates, failures, diagnostics = estimate(complete)
    return {
        "study_id": STUDY, "status": "measured_descriptive_calibration",
        "registration_commit": registration, "source_lock_commit": lock_revision,
        "key_roster_sha256": ROSTER_SHA,
        "source_sha256": {role: item["sha256"] for role, item in SOURCES.items()},
        "outcome_selector": OUTCOME_FILTERS,
        "selected_outcome_key_rows": len(measured),
        "valid_selected_outcome_rows": len(clean),
        "diagnostics": diagnostics, "failed_gates": failures,
        "estimate": estimates,
        "verdict": "INCONCLUSIVE" if failures else estimates["verdict"],
        "limits": LIMITATIONS,
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }


def result_card(result: dict[str, Any]) -> bytes:
    lines = [f"# {STUDY}", "", f"**Verdict:** {result['verdict']} (descriptive calibration only)", "",
             f"Complete pairs: {result['diagnostics']['complete_pairs']}; countries: {result['diagnostics']['complete_countries']}."]
    if result["failed_gates"]:
        lines += ["", "Failed prespecified gates: " + ", ".join(result["failed_gates"]) + "."]
    else:
        value = result["estimate"]
        lines += ["", f"WGI coefficient: {value['beta_log_points_per_wgi_point']:.8g} log points per index point; "
                  f"country-cluster two-sided p={value['two_sided_p']:.8g}; "
                  f"99% CI [{value['confidence_interval_99_pct'][0]:.8g}, "
                  f"{value['confidence_interval_99_pct'][1]:.8g}]."]
    lines += ["", "No causal, policy, school, position, or featured credit is assigned.",
              "The result JSON preserves all custody, sample, concentration, and uncertainty gates.", ""]
    return "\n".join(lines).encode()


RUN_ARTIFACTS = (
    "result.json", "diagnostics.json", "manifest.yaml", "hypothesis.yaml",
    "replication.py", "coefficients.parquet", "chart_data.json",
    "result_card.md", "evidence_packet.yaml",
)


def canonical_yaml(payload: Any) -> bytes:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True).encode()


def coefficient_parquet(result: dict[str, Any]) -> bytes:
    fitted = result["estimate"] or {}
    ci = fitted.get("confidence_interval_99_pct") or [None, None]
    schema = pa.schema([
        pa.field("hypothesis_id", pa.string()), pa.field("term", pa.string()),
        pa.field("estimate", pa.float64()), pa.field("std_error", pa.float64()),
        pa.field("p_value", pa.float64()), pa.field("ci99_low", pa.float64()),
        pa.field("ci99_high", pa.float64()), pa.field("n_observations", pa.int64()),
        pa.field("n_countries", pa.int64()), pa.field("verdict", pa.string()),
    ])
    row = {
        "hypothesis_id": [STUDY], "term": ["government_effectiveness_estimate_t"],
        "estimate": [fitted.get("beta_log_points_per_wgi_point")],
        "std_error": [fitted.get("cluster_se")], "p_value": [fitted.get("two_sided_p")],
        "ci99_low": [ci[0]], "ci99_high": [ci[1]],
        "n_observations": [result["diagnostics"]["complete_pairs"]],
        "n_countries": [result["diagnostics"]["complete_countries"]],
        "verdict": [result["verdict"]],
    }
    sink = io.BytesIO()
    pq.write_table(pa.Table.from_pydict(row, schema=schema), sink,
                   compression="zstd", version="2.6", use_dictionary=False)
    return sink.getvalue()


def replication_wrapper() -> bytes:
    # A committed result replays through the guarded verifier. Source-root is
    # optional because ignored raw vintages may live in a separate checkout.
    return f'''#!/usr/bin/env python3
"""Exact replay of {STUDY}; requires the committed result packet."""
import argparse
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-root", type=Path)
args = parser.parse_args()
command = [sys.executable, str(root / "{RUNNER}"), "verify"]
if args.source_root is not None:
    command += ["--source-root", str(args.source_root)]
raise SystemExit(subprocess.call(command, cwd=root))
'''.encode()


def result_artifacts(result: dict[str, Any], source_entries: dict[str, dict[str, Any]]) -> dict[str, bytes]:
    """Build the complete immutable run packet; self-hash is omitted."""
    fitted = result["estimate"] or {}
    diagnostics = {
        "hypothesis_id": STUDY, "verdict": result["verdict"],
        "verdict_label": result["verdict"], "status": result["status"],
        "reason": ", ".join(result["failed_gates"]) if result["failed_gates"] else "prespecified model estimated",
        "template": "panel_fe", "runner": RUNNER,
        "coefficient": fitted.get("beta_log_points_per_wgi_point"),
        "standard_error_cluster_country": fitted.get("cluster_se"),
        "p_value": fitted.get("two_sided_p"),
        "ci99": fitted.get("confidence_interval_99_pct"),
        "n_observations": result["diagnostics"]["complete_pairs"],
        "n_countries": result["diagnostics"]["complete_countries"],
        "failed_gates": result["failed_gates"],
        "sample_and_concentration": result["diagnostics"],
        "causal_credit": 0, "policy_score_eligible": False,
        "school_score_eligible": False, "featured_eligible": False,
        "correction": {"disposition": "descriptive_calibration_only",
                       "family_size": 1, "local_p_max": P_MAX,
                       "archive_wide_selection_adjustment": False,
                       "causal_credit": 0, "policy_score_eligible": False,
                       "policy_score_credit": 0, "school_score_eligible": False,
                       "school_score_credit": 0, "featured_eligible": False},
    }
    vintages = [{
        "name": role, "vintage_file": source["path"],
        "publisher": source["publisher"], "series_id": source["series_id"],
        "sha256": source["sha256"], "fetch_manifest": source["manifest"],
        "fetch_manifest_sha256": source["manifest_sha256"],
        "source_url": source.get("source_url"),
        "methodology_url": source.get("methodology_url"),
        "license": source.get("license"),
    } for role, source in source_entries.items()]
    manifest = {
        "hypothesis_id": STUDY, "runner": RUNNER, "status": result["verdict"],
        "registration_commit": result["registration_commit"],
        "source_lock_commit": result["source_lock_commit"],
        "source_lock": LOCK, "key_roster": ROSTER,
        "key_roster_sha256": ROSTER_SHA,
        "vintages": vintages, "missing_series": [],
        "design": {
            "outcome_selector": OUTCOME_FILTERS, "treatment_years": [YEAR_START, YEAR_END],
            "outcome_lag_years": 1, "min_complete_pairs": MIN_ROWS,
            "min_complete_countries": MIN_COUNTRIES,
            "min_years_per_country": MIN_YEARS,
            "p_max_two_sided": P_MAX, "meaningful_beta_min_abs": MIN_BETA,
            "inference": "country-cluster CR1; Student t(G-1); 99% CI",
            "disposition": "descriptive_calibration_only",
        },
    }
    chart = {
        "hypothesis_id": STUDY, "verdict": result["verdict"],
        "series": ([{
            "name": "WGI government effectiveness coefficient",
            "estimate": fitted["beta_log_points_per_wgi_point"],
            "ci99_low": fitted["confidence_interval_99_pct"][0],
            "ci99_high": fitted["confidence_interval_99_pct"][1],
        }] if fitted else []),
        "note": "Aggregate descriptive coefficient only; no country-level mortality values are exported.",
    }
    artifacts = {
        "result.json": canonical_json(result),
        "diagnostics.json": canonical_json(diagnostics),
        "manifest.yaml": canonical_yaml(manifest),
        "hypothesis.yaml": (ROOT / SPEC).read_bytes(),
        "replication.py": replication_wrapper(),
        "coefficients.parquet": coefficient_parquet(result),
        "chart_data.json": canonical_json(chart),
        "result_card.md": result_card(result),
    }
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    packet_inputs = [{
        "name": role, "publisher": source["publisher"],
        "series_id": source["series_id"], "vintage_file": source["path"],
        "hash": {"declared_sha256": source["sha256"],
                 "computed_sha256": source["sha256"], "status": "match"},
        "source": {"type": "official", "url": source.get("source_url"),
                   "methodology_url": source.get("methodology_url"),
                   "license": source.get("license"),
                   "fetch_utc": source.get("fetch_utc"),
                   "fetch_manifest": source["manifest"]},
        "coverage": {field: source.get(field) for field in
                     ("start_date", "end_date", "frequency", "units")},
    } for role, source in source_entries.items()]
    bucket = {"SUPPORTED": "supported", "REFUTED": "refuted",
              "PARTIAL": "partial", "INCONCLUSIVE": "inconclusive"}[result["verdict"]]
    packet = {
        "packet_version": 1,
        "repository": {"root": ".", "git_commit": result["source_lock_commit"],
                       "registration_commit": result["registration_commit"],
                       "source_lock_commit": result["source_lock_commit"]},
        "hypothesis": {"id": STUDY, "path": SPEC, "topic": spec["topic"],
                       "claim": spec["claim"], "school": None},
        "verdict": {"raw": result["verdict"], "bucket": bucket,
                    "reason": diagnostics["reason"], "status": result["status"]},
        "preregistration": {"path": PREREG, "claim": spec["claim"],
                            "falsification_rule": spec["falsification"]["rule"],
                            "threshold": spec["falsification"]["threshold"],
                            "estimator": spec["estimator"], "steelman": STEELMAN},
        "reproduction": {"run_dir": RESULT_DIR, "runner": RUNNER,
                         "replication_script": f"{RESULT_DIR}/replication.py",
                         "suggested_command": f"python {RESULT_DIR}/replication.py --source-root <pinned-source-checkout>"},
        "data": {"inputs": packet_inputs, "missing_series": [],
                 "data_quality": {"grade": "reproducible_hash_verified_at_run",
                                  "input_count": len(packet_inputs),
                                  "hash_status_counts": {"match": len(packet_inputs)}}},
        "artifacts": [{"path": f"{RESULT_DIR}/{name}",
                       "sha256": hashlib.sha256(content).hexdigest(),
                       "bytes": len(content)} for name, content in artifacts.items()],
        "references": [{"kind": "source", "publisher": source["publisher"],
                        "series_id": source["series_id"], "url": source.get("source_url")}
                       for source in source_entries.values()],
        "caveats": LIMITATIONS,
        "credit": {"causal": 0, "policy_score_eligible": False,
                   "policy_score_credit": 0, "school_score_eligible": False,
                   "school_score_credit": 0, "featured_eligible": False},
    }
    artifacts["evidence_packet.yaml"] = canonical_yaml(packet)
    if tuple(artifacts) != RUN_ARTIFACTS:
        raise RuntimeError("standard run artifacts changed")
    return artifacts


def run(source_root: Path) -> Path:
    registration, lock_revision, panel = committed_lock(source_root)
    destination = ROOT / RESULT_DIR
    if destination.exists():
        raise RuntimeError("result directory already exists; never overwrite a measured run")
    result = measured_result(source_root, registration, lock_revision, panel)
    artifacts = result_artifacts(result, check_sources(source_root))
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in artifacts.items():
        (destination / name).write_bytes(content)
    return destination


def verify(source_root: Path) -> None:
    registration, lock_revision, panel = committed_lock(source_root)
    additions = {first_addition(f"{RESULT_DIR}/{name}") for name in RUN_ARTIFACTS}
    if len(additions) != 1:
        raise RuntimeError("all nine result artifacts need one shared measured-result commit")
    result_revision = additions.pop()
    if result_revision in (registration, lock_revision) or not is_ancestor(lock_revision, result_revision):
        raise RuntimeError("measured result commit must follow source-lock commit")
    destination = ROOT / RESULT_DIR
    if {path.name for path in destination.iterdir() if path.is_file()} != set(RUN_ARTIFACTS):
        raise RuntimeError("standard run artifact set is incomplete or contains extra files")
    for name in RUN_ARTIFACTS:
        frozen_file(f"{RESULT_DIR}/{name}", result_revision)
    result = measured_result(source_root, registration, lock_revision, panel)
    expected = result_artifacts(result, check_sources(source_root))
    for name in RUN_ARTIFACTS:
        if (destination / name).read_bytes() != expected[name]:
            raise RuntimeError(f"exact replay mismatch: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "lock", "run", "verify"))
    parser.add_argument("--source-root", type=Path, default=ROOT,
                        help="checkout containing byte-identical pinned raw vintages and manifests")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.action == "preflight":
        _, summary = preflight_panel(source_root)
        print(json.dumps(summary, sort_keys=True, indent=2))
    elif args.action == "lock":
        print(create_lock(source_root))
    elif args.action == "run":
        print(run(source_root))
    else:
        verify(source_root)
        print("exact replay verified")


if __name__ == "__main__":
    main()
