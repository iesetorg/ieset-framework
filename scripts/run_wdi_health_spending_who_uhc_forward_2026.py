#!/usr/bin/env python3
"""Frozen descriptive WDI health-spending to WHO UHC calibration.

Preflight and lock read byte hashes, schemas, and country/year keys only.
The selected value columns may be opened only after a separate committed
registration and metadata-only source lock. Replay regenerates exact artifacts.
"""
from __future__ import annotations

import argparse
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
ID = "wdi_health_spending_who_uhc_forward_2026"
SPEC = f"hypotheses/healthcare/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PLAN = f"engine/audits/{ID}_prereg_2026-10-10.md"
RUNNER = f"scripts/run_{ID}.py"
ROSTER = "data/pinned_evidence/wdi_health_spending_who_uhc_key_roster.csv"
ROSTER_SHA = "34702ce92aa78d7e24b63744e33cfc2d09a0537333fcad2c08f5bc1404067270"
LOCK = f"prereg/locks/{ID}.json"
RUN = f"engine/runs/{ID}"
SUMMARY = f"engine/audits/{ID}_result_2026-10-10.md"
REGISTERED = (SPEC, STEELMAN, PLAN, RUNNER, ROSTER)
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)
SOURCES = {
    "spending": {
        "publisher": "world_bank_wdi",
        "series_id": "SH.XPD.CHEX.GD.ZS",
        "path": "data/vintages/world_bank_wdi/SH.XPD.CHEX.GD.ZS@2026-05-05T203513Z.parquet",
        "sha256": "ca58050bf93fd11b1b864f04c8d27eaedbd6e260eba3a7e5df473a8cb0b5cc40",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
        "years": (2000, 2010),
    },
    "uhc": {
        "publisher": "who_gho",
        "series_id": "UHC_INDEX_REPORTED",
        "path": "data/vintages/who_gho/UHC_INDEX_REPORTED@2026-04-30T114740Z.parquet",
        "sha256": "e4e1fea6a88f1cfcb97599a762f3c3988d5e2bff3674458f94f13e9710c35b1a",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e",
        "years": (2000, 2010, 2020),
    },
}
TERMS = (
    "intercept", "spending_change_pp", "uhc_2010",
    "uhc_pretrend_2000_2010", "spending_2000",
)
MIN_COUNTRIES = 80
MIN_MATERIAL = 20
MATERIAL_CHANGE_PP = 0.5
MIN_EXPOSURE_IQR_PP = 0.5
MAX_EXPOSURE_SHARE = 0.20
MAX_LOO_FAILURES = 2
MIN_LOO_SIGN_SHARE = 0.75
MEANINGFUL_BETA = 1.0
P_MAX = 0.01


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(path: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H",
                  "HEAD", "--", path).decode().splitlines()
    if len(commits) != 1:
        raise ValueError(f"Expected exactly one first-addition commit: {path}: {commits}")
    return commits[0]


def committed_original(path: str, commit: str) -> None:
    current = (ROOT / path).read_bytes()
    if current != git("show", f"{commit}:{path}") or current != git("show", f"HEAD:{path}"):
        raise ValueError(f"Frozen file changed after its first commit: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise ValueError(f"Frozen file has uncommitted changes: {path}")


def ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def roster_codes() -> list[str]:
    path = ROOT / ROSTER
    if file_sha(path) != ROSTER_SHA:
        raise ValueError("Frozen key-only country roster hash mismatch")
    lines = path.read_text().splitlines()
    if lines[0] != "country_iso3" or lines[1:] != sorted(set(lines[1:])):
        raise ValueError("Invalid key-only country roster")
    return lines[1:]


def registration_commit() -> str:
    commits = {first_addition(path) for path in REGISTERED}
    if len(commits) != 1:
        raise ValueError("Registration files did not enter together")
    registered = commits.pop()
    for path in REGISTERED:
        committed_original(path, registered)
    if git("ls-tree", "-r", "--name-only", registered, "--", LOCK, RUN, SUMMARY).strip():
        raise ValueError("Registration commit contained source lock or results")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "descriptive"
            or spec.get("claim_direction") != "+"
            or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or spec.get("steelman") != STEELMAN
            or spec["falsification"]["threshold"] != threshold()):
        raise ValueError("Frozen specification identity or gates differ")
    return registered


def threshold() -> dict:
    return {
        "family_size": 1, "min_complete_economies": MIN_COUNTRIES,
        "min_abs_change_0_5pp_economies": MIN_MATERIAL,
        "min_exposure_iqr_pp": MIN_EXPOSURE_IQR_PP,
        "max_single_economy_residualized_exposure_share": MAX_EXPOSURE_SHARE,
        "max_loo_failures": MAX_LOO_FAILURES,
        "min_loo_sign_share": MIN_LOO_SIGN_SHARE,
        "meaningful_abs_beta_index_points_per_gdp_pp": MEANINGFUL_BETA,
        "two_sided_p_max": P_MAX, "roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {key: source[key] for key in ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()
        },
        "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
    }


def source_custody(source_root: Path) -> tuple[dict, list[str]]:
    """Open no selected value, null-mask, or status column."""
    allowed = {country.alpha_3 for country in pycountry.countries} | {"XKX"}
    seen = {}
    custody = {}
    for role, source in SOURCES.items():
        path = source_root / source["path"]
        if not path.is_file() or file_sha(path) != source["sha256"]:
            raise ValueError(f"Missing or changed raw vintage: {role}")
        names = pq.ParquetFile(path).schema_arrow.names
        required = {"country_iso3", "year", "value"}
        if role == "uhc":
            required.add("SpatialDimType")
        if not required.issubset(names):
            raise ValueError(f"Wrong source schema: {role}")
        columns = ["country_iso3", "year"]
        if role == "uhc":
            columns.append("SpatialDimType")
        keys_table = pq.read_table(path, columns=columns).to_pylist()
        keys = [
            (row["country_iso3"], int(row["year"]))
            for row in keys_table
            if row["country_iso3"] in allowed
            and int(row["year"]) in source["years"]
            and (role != "uhc" or row["SpatialDimType"] == "COUNTRY")
        ]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate selected source key: {role}")
        seen[role] = set(keys)
        manifest = ROOT / source["manifest"]
        if file_sha(manifest) != source["manifest_sha256"]:
            raise ValueError(f"Changed fetch manifest: {role}")
        entries = [
            row for row in yaml.safe_load(manifest.read_text())["entries"]
            if row.get("publisher") == source["publisher"]
            and row.get("series_id") == source["series_id"]
            and row.get("parquet_path") == source["path"]
        ]
        if len(entries) != 1 or entries[0].get("sha256") != source["sha256"]:
            raise ValueError(f"Fetch manifest does not custody source: {role}")
        entry = entries[0]
        custody[role] = {
            **{key: source[key] for key in ("publisher", "series_id", "path", "sha256", "manifest", "manifest_sha256")},
            "source_url": entry.get("source_url"),
            "methodology_url": entry.get("methodology_url"),
            "license": entry.get("license"),
            "rows": entry.get("rows"),
            "selected_country_year_keys": len(keys),
            "selected_key_sha256": hashlib.sha256(
                "".join(f"{country},{year}\n" for country, year in sorted(keys)).encode()
            ).hexdigest(),
        }
    roster = sorted(
        country for country in allowed
        if all((country, year) in seen[role]
               for role, source in SOURCES.items() for year in source["years"])
    )
    if roster != roster_codes():
        raise ValueError("Raw source keys differ from registered roster")
    return custody, roster


def expected_lock(source_root: Path) -> dict:
    registered = registration_commit()
    custody, roster = source_custody(source_root)
    return {
        "design_id": ID, "registration_commit": registered,
        "registered_sha256": {path: file_sha(ROOT / path) for path in REGISTERED},
        "source_custody": custody, "candidate_economies": roster,
        "selected_values_read": False,
        "instruction": "Commit this metadata-only lock separately before opening selected values.",
    }


def make_lock(source_root: Path) -> None:
    if (ROOT / LOCK).exists():
        raise ValueError("Source lock already exists")
    payload = expected_lock(source_root)
    path = ROOT / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(f"Metadata-only source lock prepared for {len(payload['candidate_economies'])} economies")


def verified_lock(source_root: Path) -> tuple[dict, str, str]:
    registered = registration_commit()
    locked = first_addition(LOCK)
    committed_original(LOCK, locked)
    if not ancestor(registered, locked) or not ancestor(locked, "HEAD"):
        raise ValueError("Registration and source-lock chronology is not strict")
    if git("ls-tree", "-r", "--name-only", locked, "--", RUN, SUMMARY).strip():
        raise ValueError("Source-lock commit contained results")
    payload = json.loads((ROOT / LOCK).read_text())
    if payload != expected_lock(source_root):
        raise ValueError("Source lock differs from exact raw bytes, keys, or registration")
    return payload, registered, locked


def selected_values(source_root: Path, roster: list[str], role: str) -> dict[tuple[str, int], float | None]:
    source = SOURCES[role]
    columns = ["country_iso3", "year", "value"]
    if role == "uhc":
        columns.append("SpatialDimType")
    selected = set(roster)
    values = {}
    for row in pq.read_table(source_root / source["path"], columns=columns).to_pylist():
        code, year = row["country_iso3"], int(row["year"])
        if code not in selected or year not in source["years"]:
            continue
        if role == "uhc" and row["SpatialDimType"] != "COUNTRY":
            continue
        key = code, year
        if key in values:
            raise ValueError(f"Duplicate selected value key: {role} {key}")
        value = row["value"]
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = None
        values[key] = value if value is not None and math.isfinite(value) else None
    if len(values) != len(roster) * len(source["years"]):
        raise ValueError(f"Source key roster incomplete for {role}")
    return values


def valid(value: float | None, low: float, high: float, *, open_low: bool = False) -> bool:
    return value is not None and (value > low if open_low else value >= low) and value <= high


def panel_from_sources(source_root: Path, roster: list[str]) -> tuple[pd.DataFrame, dict]:
    s = selected_values(source_root, roster, "spending")
    u = selected_values(source_root, roster, "uhc")
    rows = []
    exclusions = Counter()
    for country in roster:
        s00, s10 = s[country, 2000], s[country, 2010]
        u00, u10, u20 = u[country, 2000], u[country, 2010], u[country, 2020]
        reasons = []
        if not valid(s00, 0, 100, open_low=True) or not valid(s10, 0, 100, open_low=True):
            reasons.append("current_health_spending_missing_or_invalid")
        if any(not valid(value, 0, 100) for value in (u00, u10, u20)):
            reasons.append("who_uhc_missing_or_invalid")
        if reasons:
            exclusions.update(reasons)
            continue
        rows.append({
            "country_iso3": country,
            "spending_change_pp": s10 - s00,
            "spending_2000": s00,
            "uhc_2010": u10,
            "uhc_pretrend_2000_2010": u10 - u00,
            "outcome": u20 - u10,
        })
    panel = pd.DataFrame(rows, columns=[
        "country_iso3", "spending_change_pp", "spending_2000",
        "uhc_2010", "uhc_pretrend_2000_2010", "outcome",
    ]).sort_values("country_iso3").reset_index(drop=True)
    diag = {
        "source_key_candidate_economies": len(roster),
        "complete_economies": len(panel),
        "exclusion_reasons_overlapping": dict(sorted(exclusions.items())),
    }
    return panel, diag


def design(panel: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = np.column_stack([
        np.ones(len(panel)),
        panel["spending_change_pp"].to_numpy(dtype=float),
        panel["uhc_2010"].to_numpy(dtype=float),
        panel["uhc_pretrend_2000_2010"].to_numpy(dtype=float),
        panel["spending_2000"].to_numpy(dtype=float),
    ])
    return x, panel["outcome"].to_numpy(dtype=float)


def fit(panel: pd.DataFrame) -> dict:
    x, y = design(panel)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank design unavailable")
    controls = x[:, [0, 2, 3, 4]]
    residual = x[:, 1] - controls @ np.linalg.lstsq(controls, x[:, 1], rcond=None)[0]
    squares = residual ** 2
    total = float(squares.sum())
    if not math.isfinite(total) or total <= 1e-10:
        raise ValueError("No residualized exposure variation")
    result = sm.OLS(y, x).fit(cov_type="HC3")
    beta, se = float(result.params[1]), float(result.bse[1])
    p = float(2 * student_t.sf(abs(beta / se), df=n-k)) if se > 0 else float("nan")
    if not all(math.isfinite(value) for value in (beta, se, p)) or se <= 0:
        raise ValueError("Nonfinite HC3 estimate")
    return {
        "coefficient": beta, "standard_error": se, "p_value": p,
        "reference_df": n-k, "covariance": "HC3",
        "max_single_economy_residualized_exposure_share": float(squares.max()/total),
        "unit": "2020-minus-2010 UHC index points per +1 GDP percentage point 2000-to-2010 current-health-expenditure change",
    }


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict, str]:
    n = len(panel)
    exposure = panel["spending_change_pp"].to_numpy(dtype=float)
    diag["material_exposure_change_economies"] = int((np.abs(exposure) >= MATERIAL_CHANGE_PP).sum())
    diag["exposure_iqr_pp"] = (
        float(np.quantile(exposure, .75) - np.quantile(exposure, .25))
        if n else 0.0
    )
    failed = []
    if n < MIN_COUNTRIES:
        failed.append("min_complete_economies")
    if diag["material_exposure_change_economies"] < MIN_MATERIAL:
        failed.append("min_abs_change_0_5pp_economies")
    if diag["exposure_iqr_pp"] < MIN_EXPOSURE_IQR_PP:
        failed.append("min_exposure_iqr_pp")
    if failed:
        diag["failed_gates"] = failed
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel)
    except ValueError as exc:
        diag["failed_gates"] = [f"estimator:{exc}"]
        return {}, "INCONCLUSIVE"
    diag["max_single_economy_residualized_exposure_share"] = estimate[
        "max_single_economy_residualized_exposure_share"
    ]
    if diag["max_single_economy_residualized_exposure_share"] > MAX_EXPOSURE_SHARE:
        failed.append("residualized_exposure_concentration")
    loo = []
    failures = 0
    for country in panel["country_iso3"]:
        try:
            loo.append(fit(panel.loc[panel["country_iso3"] != country])["coefficient"])
        except ValueError:
            failures += 1
    estimate["loo_successes"] = len(loo)
    estimate["loo_failures"] = failures
    estimate["loo_positive_share"] = sum(beta > 0 for beta in loo)/len(loo) if loo else None
    estimate["loo_negative_share"] = sum(beta < 0 for beta in loo)/len(loo) if loo else None
    if failures > MAX_LOO_FAILURES:
        failed.append("leave_one_out_fit_failures")
    diag["failed_gates"] = failed
    if failed:
        return estimate, "INCONCLUSIVE"
    if (estimate["coefficient"] >= MEANINGFUL_BETA and estimate["p_value"] <= P_MAX
            and estimate["loo_positive_share"] >= MIN_LOO_SIGN_SHARE):
        return estimate, "SUPPORTED"
    if (estimate["coefficient"] <= -MEANINGFUL_BETA and estimate["p_value"] <= P_MAX
            and estimate["loo_negative_share"] >= MIN_LOO_SIGN_SHARE):
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, diag: dict, estimate: dict, verdict: str,
         registered: str, locked: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    custody = json.loads((ROOT / LOCK).read_text())["source_custody"]
    (directory / "manifest.yaml").write_text(yaml.safe_dump({
        "design_id": ID, "verdict": verdict, "evidence_type": "descriptive",
        "spec_commit": registered, "lock_commit": locked,
        "spec_sha256": file_sha(ROOT / SPEC), "lock_sha256": file_sha(ROOT / LOCK),
        "runner_sha256": file_sha(ROOT / RUNNER), "source_custody": custody,
        "artifacts": list(ARTIFACTS), "credit": credit,
        "chart_data_omitted_for_source_license": True,
    }, sort_keys=True))
    correction = {
        "disposition": "descriptive_calibration_only", "causal_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }
    json_write(directory / "diagnostics.json", {
        **diag, "estimate": estimate, "verdict": verdict,
        "correction": correction, "analysis_scope": "descriptive_only",
    })
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["spending_change_pp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([
        ("term", pa.string()), ("coefficient", pa.float64()),
        ("standard_error", pa.float64()), ("p_value", pa.float64()),
    ]))
    json_write(directory / "chart_data.json", [])
    lines = [
        "# Earlier health spending and later WHO UHC service coverage",
        "", f"**{verdict} — descriptive calibration only.**", "",
        f"Complete economies: {diag['complete_economies']} of {diag['source_key_candidate_economies']} key candidates.",
        f"Material exposure changes (absolute at least 0.5 GDP pp): {diag['material_exposure_change_economies']}.",
        f"Exposure IQR: {diag['exposure_iqr_pp']:.6g} GDP pp.",
    ]
    if has_estimate:
        lines += [
            f"Coefficient {estimate['coefficient']:.6g} UHC index points per +1 GDP percentage point spending change; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}.",
            f"Maximum residualized exposure share {estimate['max_single_economy_residualized_exposure_share']:.6g}; successful leave-one-out fits {estimate['loo_successes']}.",
        ]
    else:
        lines += ["No coefficient was estimated because a frozen data or method gate failed."]
    if diag["failed_gates"]:
        lines += [f"Failed gates: {', '.join(diag['failed_gates'])}."]
    lines += [
        "", "Current health expenditure is total public plus private current health spending as a GDP share; it is not public spending or a policy enactment. The WHO index is a modelled composite of selected service-coverage tracers, not mortality or financial protection.",
        "The archived public-health-spending/avoidable-mortality REFUTED generic result is a distinct treatment and outcome and remains unchanged. No causal, policy, school, position, or featured credit follows.",
        "WHO source data are not redistributed in the chart artifact; obtain and use the licensed raw vintage for exact replay.", "",
    ]
    (directory / "result_card.md").write_text("\n".join(lines))
    (directory / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER}'), '--verify', *sys.argv[1:]], check=True)\n"
    )
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump({
        "design_id": ID, "verdict": verdict, "evidence_type": "descriptive",
        "causal_claim": False, "policy_effect_credit": False,
        "school_claim_links": [], "correction": correction,
        "source_hashes_verified": True,
        "strict_spec_lock_chronology_verified": True,
        "interpretation": "Earlier total current health-expenditure share change associated with later WHO service-coverage index change only.",
    }, sort_keys=True))
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict],
        "complete_economies": [diag["complete_economies"]],
        "material_exposure_change_economies": [diag["material_exposure_change_economies"]],
    }, pa.schema([
        ("verdict", pa.string()), ("complete_economies", pa.int64()),
        ("material_exposure_change_economies", pa.int64()),
    ]))
    if tuple(sorted(path.name for path in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError("Unexpected run artifact roster")


def result_summary(diag: dict, estimate: dict, verdict: str) -> str:
    lines = [
        "# Earlier health spending and later WHO UHC — frozen result",
        "",
        f"**Verdict: {verdict}.** One prospectively registered descriptive test. Complete economies: {diag['complete_economies']} of {diag['source_key_candidate_economies']} source-key candidates.",
        f"Material exposure changes: {diag['material_exposure_change_economies']}; exposure IQR: {diag['exposure_iqr_pp']:.6g} GDP percentage points.",
    ]
    if "coefficient" in estimate:
        lines += [
            f"Beta: {estimate['coefficient']:.8g} WHO index points per +1 GDP pp prior spending change; HC3 SE: {estimate['standard_error']:.8g}; two-sided p: {estimate['p_value']:.8g}.",
            f"Maximum single-economy residualized exposure share: {estimate['max_single_economy_residualized_exposure_share']:.8g}; leave-one-out successes: {estimate['loo_successes']}; failures: {estimate['loo_failures']}.",
        ]
    else:
        lines += ["No public coefficient because a frozen gate failed."]
    lines += [
        f"Failed gates: {', '.join(diag['failed_gates']) if diag['failed_gates'] else 'none'}.",
        "",
        "The exposure is **total current health expenditure/GDP**, not public health spending. The WHO UHC service coverage index is a 0–100 composite of tracer coverage; it is not mortality or financial hardship. The 2020 endpoint and revisable modelled estimates limit interpretation. Spending/GDP can move through its denominator and health systems may respond to unmet coverage. This association is neither a causal test nor a policy effect.",
        "",
        "An older generic public-health-spending/avoidable-mortality run was REFUTED under its legacy rules. This new question does not relabel, repair, reverse, or replicate that result. The wider archive and this known prior result mean the nominal 0.01 cutoff is not an archive-wide discovery correction.",
        "",
        "WHO's vintage is marked CC-BY-NC-SA-3.0 IGO in its fetch manifest. No row-level WHO values are copied into tracked artifacts. Exact replay requires the hash-pinned source vintage and its license terms.",
        "",
        "Source definitions: [World Bank current health expenditure](https://data.worldbank.org/indicator/SH.XPD.CHEX.GD.ZS); [WHO UHC service coverage index](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/uhc-index-of-service-coverage).",
        "",
    ]
    return "\n".join(lines)


def run_or_verify(source_root: Path, verify: bool) -> None:
    lock, registered, locked = verified_lock(source_root)
    panel, diag = panel_from_sources(source_root, lock["candidate_economies"])
    estimate, verdict = calculate(panel, diag)
    target = ROOT / RUN
    if verify and not target.is_dir():
        raise ValueError("Missing run artifacts")
    if not verify and target.exists():
        raise ValueError("Run already exists")
    with tempfile.TemporaryDirectory(prefix="ieset_wdi_who_uhc_") as temporary:
        generated = Path(temporary) / "run"
        emit(generated, diag, estimate, verdict, registered, locked)
        summary = result_summary(diag, estimate, verdict)
        if verify:
            for name in ARTIFACTS:
                if file_sha(generated / name) != file_sha(target / name):
                    raise ValueError(f"Exact replay differs: {name}")
            if (ROOT / SUMMARY).read_text() != summary:
                raise ValueError("Exact result audit differs")
            print(f"Exact replay matched {len(ARTIFACTS)} run artifacts and result audit; verdict {verdict}")
        else:
            shutil.copytree(generated, target)
            (ROOT / SUMMARY).write_text(summary)
            print(json.dumps({"verdict": verdict, **diag, "estimate": estimate},
                             sort_keys=True, indent=2, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.preflight:
        custody, roster = source_custody(args.source_root)
        print(json.dumps({"candidate_economies": len(roster), "roster_sha256": ROSTER_SHA,
                          "sources": custody}, sort_keys=True, indent=2))
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
