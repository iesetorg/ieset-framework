#!/usr/bin/env python3
"""Frozen descriptive WDI health-financing calibration.

--prepare-lock reads bytes, schemas, and country/year keys only. --run may
read selected values only after a distinct committed source lock.
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
DESIGN_ID = "wdi_oop_change_under5_mortality_followthrough_v2"
SPEC_REL = f"hypotheses/healthcare/{DESIGN_ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{DESIGN_ID}.md"
PLAN_REL = f"engine/audits/{DESIGN_ID}_prereg_2026-10-10.md"
RUNNER_REL = f"scripts/run_{DESIGN_ID}.py"
LOCK_REL = f"prereg/locks/{DESIGN_ID}.json"
RUN_REL = f"engine/runs/{DESIGN_ID}"
REGISTERED = (SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL)
SOURCES = {
    "oop": "data/vintages/world_bank_wdi/SH.XPD.OOPC.CH.ZS@2026-05-05T203530Z.parquet",
    "mortality": "data/vintages/world_bank_wdi/SH.DYN.MORT@2026-05-05T194907Z.parquet",
    "income": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
    "health_spending": "data/vintages/world_bank_wdi/SH.XPD.CHEX.GD.ZS@2026-05-05T203513Z.parquet",
}
MANIFESTS = {
    "may5_200056": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
    "may5_210519": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
}
SOURCE_MANIFEST = {
    "oop": "may5_210519", "mortality": "may5_200056",
    "income": "may5_200056", "health_spending": "may5_210519",
}
YEARS = {
    "oop": (2005, 2015), "mortality": (2005, 2015, 2023),
    "income": (2005, 2015), "health_spending": (2015,),
}
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)
TERMS = (
    "intercept", "oop_change_per_10pp", "log_mortality_2015",
    "mortality_pretrend", "log_income_2015", "income_pretrend",
    "health_spending_2015",
)


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_add_commit(path: str) -> str:
    commits = git("log", "--follow", "--diff-filter=A", "--format=%H", "--", path).decode().splitlines()
    if not commits:
        raise ValueError(f"No first-addition commit for {path}")
    return commits[-1]


def committed_original(path: str, commit: str) -> None:
    current = (ROOT / path).read_bytes()
    if current != git("show", f"{commit}:{path}") or current != git("show", f"HEAD:{path}"):
        raise ValueError(f"Registered file changed after first addition: {path}")


def ancestor(older: str, newer: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def registered_spec() -> tuple[str, dict]:
    commit = first_add_commit(SPEC_REL)
    for path in REGISTERED:
        if first_add_commit(path) != commit:
            raise ValueError(f"Registration files entered in different commits: {path}")
        committed_original(path, commit)
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text())
    if spec["hypothesis_id"] != DESIGN_ID or spec["status"] != "pre_registered":
        raise ValueError("Registered spec identity changed")
    return commit, spec


def source_key_sets(source_root: Path) -> tuple[dict, list[str]]:
    """Read only keys, schemas, and full-file bytes; never value or status."""
    allowed = {country.alpha_3 for country in pycountry.countries} | {"XKX"}
    source_info = {}
    complete_per_source = []
    for role, relative in SOURCES.items():
        path = source_root / relative
        if not path.is_file():
            raise ValueError(f"Missing preserved source: {path}")
        names = pq.ParquetFile(path).schema_arrow.names
        if not {"country_iso3", "year", "value"}.issubset(names):
            raise ValueError(f"Missing expected source schema: {relative}")
        columns = pq.read_table(path, columns=["country_iso3", "year"]).to_pydict()
        keys = [(c, int(y)) for c, y in zip(columns["country_iso3"], columns["year"])
                if c in allowed and int(y) in YEARS[role]]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate selected key in {relative}")
        key_set = set(keys)
        complete_per_source.append({c for c in allowed
                                    if all((c, year) in key_set for year in YEARS[role])})
        source_info[role] = {
            "path": relative, "sha256": file_sha(path), "schema_names": names,
            "eligible_selected_key_count": len(keys),
            "eligible_selected_key_sha256": hashlib.sha256(
                "".join(f"{c},{y}\n" for c, y in sorted(keys)).encode()).hexdigest(),
        }
    roster = sorted(set.intersection(*complete_per_source))
    if len(roster) != 216:
        raise ValueError(f"Expected 216 key-complete candidate economies, got {len(roster)}")
    return source_info, roster


def preflight(source_root: Path) -> dict:
    source_info, roster = source_key_sets(source_root)
    manifest_info = {}
    for role, relative in MANIFESTS.items():
        path = source_root / relative
        if not path.is_file():
            raise ValueError(f"Missing fetch manifest: {path}")
        manifest_info[role] = {"path": relative, "sha256": file_sha(path)}
    for source_role, manifest_role in SOURCE_MANIFEST.items():
        entries = yaml.safe_load((source_root / MANIFESTS[manifest_role]).read_text()).get("entries", [])
        matched = [entry for entry in entries if entry.get("parquet_path") == SOURCES[source_role]]
        if len(matched) != 1 or matched[0].get("sha256") != source_info[source_role]["sha256"]:
            raise ValueError(f"Exact fetch-manifest source/hash mismatch: {source_role}")
    return {
        "sources": source_info, "manifests": manifest_info,
        "candidate_economies": roster,
        "candidate_roster_sha256": hashlib.sha256(
            "".join(f"{c}\n" for c in roster).encode()).hexdigest(),
        "selected_values_read": False,
    }


def expected_lock(source_root: Path) -> dict:
    spec_commit, _ = registered_spec()
    return {
        "design_id": DESIGN_ID, "spec_commit": spec_commit,
        "registered_sha256": {path: file_sha(ROOT / path) for path in REGISTERED},
        "source_custody": preflight(source_root),
        "instruction": "Commit this metadata-only lock separately before reading any selected values.",
    }


def prepare_lock(source_root: Path) -> None:
    path = ROOT / LOCK_REL
    if path.exists():
        raise ValueError("Source lock already exists")
    data = expected_lock(source_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print(f"Prepared metadata-only source lock for {len(data['source_custody']['candidate_economies'])} economies")


def verify_lock(source_root: Path) -> tuple[dict, str, str]:
    spec_commit, spec = registered_spec()
    lock_commit = first_add_commit(LOCK_REL)
    committed_original(LOCK_REL, lock_commit)
    if lock_commit == spec_commit or not ancestor(spec_commit, lock_commit) or not ancestor(lock_commit, "HEAD"):
        raise ValueError("Registration and source-lock chronology is not strict")
    if json.loads((ROOT / LOCK_REL).read_text()) != expected_lock(source_root):
        raise ValueError("Source bytes, keys, manifest, or registration differ from lock")
    return spec, spec_commit, lock_commit


def selected_values(path: Path, countries: list[str], years: tuple[int, ...]) -> dict:
    """Only called after strict registration and lock verification."""
    selected = set(countries)
    out = {}
    for row in pq.read_table(path, columns=["country_iso3", "year", "value"]).to_pylist():
        key = (row["country_iso3"], int(row["year"]))
        if key[0] in selected and key[1] in years:
            if key in out:
                raise ValueError(f"Duplicate selected value key: {key}")
            out[key] = row["value"]
    return out


def finite(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def panel_from_sources(source_root: Path, countries: list[str]) -> tuple[pd.DataFrame, dict]:
    values = {role: selected_values(source_root / relative, countries, YEARS[role])
              for role, relative in SOURCES.items()}
    rows = []
    missing = {}
    for country in countries:
        def cell(role: str, year: int) -> float | None:
            return finite(values[role].get((country, year)))
        oop_05, oop_15 = cell("oop", 2005), cell("oop", 2015)
        m_05, m_15, m_23 = (cell("mortality", y) for y in (2005, 2015, 2023))
        g_05, g_15 = cell("income", 2005), cell("income", 2015)
        health_15 = cell("health_spending", 2015)
        reasons = []
        if any(v is None or not 0 <= v <= 100 for v in (oop_05, oop_15)):
            reasons.append("out_of_pocket_missing_or_invalid")
        if any(v is None or v <= 0 for v in (m_05, m_15, m_23)):
            reasons.append("mortality_missing_or_nonpositive")
        if any(v is None or v <= 0 for v in (g_05, g_15)):
            reasons.append("income_missing_or_nonpositive")
        if health_15 is None or not 0 < health_15 <= 100:
            reasons.append("health_spending_missing_or_invalid")
        if reasons:
            for reason in reasons:
                missing[reason] = missing.get(reason, 0) + 1
            continue
        rows.append({
            "country_iso3": country,
            "oop_change_per_10pp": (oop_15 - oop_05) / 10.0,
            "log_mortality_2015": math.log(m_15),
            "mortality_pretrend": 10.0 * (math.log(m_15) - math.log(m_05)),
            "log_income_2015": math.log(g_15),
            "income_pretrend": 10.0 * (math.log(g_15) - math.log(g_05)),
            "health_spending_2015": health_15,
            "outcome": 12.5 * (math.log(m_23) - math.log(m_15)),
        })
    panel = pd.DataFrame(rows)
    if len(panel):
        panel = panel.sort_values("country_iso3").reset_index(drop=True)
    return panel, {"candidate_economies": len(countries), "complete_economies": len(panel),
                   "excluded_by_reason_overlapping": missing}


def design(panel: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = np.column_stack([np.ones(len(panel))] +
                        [panel[name].to_numpy(dtype=float) for name in TERMS[1:]])
    return x, panel["outcome"].to_numpy(dtype=float)


def fit(panel: pd.DataFrame) -> dict:
    x, y = design(panel)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank model unavailable")
    result = sm.OLS(y, x).fit(cov_type="HC3")
    beta, se = float(result.params[1]), float(result.bse[1])
    p = float(2 * student_t.sf(abs(beta / se), df=n - k)) if se > 0 else float("nan")
    if not all(math.isfinite(v) for v in (beta, se, p)) or se <= 0:
        raise ValueError("Nonfinite HC3 estimate")
    controls = x[:, [0, 2, 3, 4, 5, 6]]
    residual = x[:, 1] - controls @ np.linalg.lstsq(controls, x[:, 1], rcond=None)[0]
    squared = residual * residual
    if float(squared.sum()) <= 1e-12:
        raise ValueError("No residualized exposure variation")
    return {
        "coefficient": beta, "standard_error": se, "p_value": p,
        "reference_df": n - k, "covariance": "HC3",
        "max_single_economy_residualized_exposure_share": float(squared.max() / squared.sum()),
    }


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict, str]:
    n = len(panel)
    if not n:
        diag["large_exposure_change_economies"] = 0
        diag["exposure_iqr_pp"] = 0.0
    else:
        exposure_pp = 10.0 * panel["oop_change_per_10pp"].to_numpy(dtype=float)
        diag["large_exposure_change_economies"] = int((np.abs(exposure_pp) >= 5.0).sum())
        diag["exposure_iqr_pp"] = float(np.quantile(exposure_pp, 0.75) - np.quantile(exposure_pp, 0.25))
    if (n < 80 or diag["large_exposure_change_economies"] < 20
            or diag["exposure_iqr_pp"] < 3.0):
        diag["failed_gate"] = "sample_or_exposure_floor"
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel)
        loo = []
        for country in panel["country_iso3"]:
            try:
                loo.append(fit(panel.loc[panel["country_iso3"] != country])["coefficient"])
            except ValueError:
                continue
    except ValueError as exc:
        diag["failed_gate"] = f"estimator:{exc}"
        return {}, "INCONCLUSIVE"
    estimate["loo_successes"] = len(loo)
    estimate["loo_positive_share"] = sum(v > 0 for v in loo) / len(loo) if loo else None
    estimate["loo_negative_share"] = sum(v < 0 for v in loo) / len(loo) if loo else None
    if (estimate["max_single_economy_residualized_exposure_share"] > 0.20
            or len(loo) < n - 2):
        diag["failed_gate"] = "influence_or_loo"
        return estimate, "INCONCLUSIVE"
    if (estimate["coefficient"] >= 0.5 and estimate["p_value"] <= 0.01
            and estimate["loo_positive_share"] >= 0.75):
        return estimate, "SUPPORTED"
    if (estimate["coefficient"] <= -0.5 and estimate["p_value"] <= 0.01
            and estimate["loo_negative_share"] >= 0.75):
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, panel: pd.DataFrame, diag: dict, estimate: dict,
         verdict: str, spec_commit: str, lock_commit: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    custody = json.loads((ROOT / LOCK_REL).read_text())["source_custody"]
    manifest = {
        "design_id": DESIGN_ID, "verdict": verdict, "evidence_type": "descriptive",
        "spec_commit": spec_commit, "lock_commit": lock_commit,
        "spec_sha256": file_sha(ROOT / SPEC_REL), "lock_sha256": file_sha(ROOT / LOCK_REL),
        "runner_sha256": file_sha(ROOT / RUNNER_REL), "source_custody": custody,
        "artifacts": list(ARTIFACTS), "credit": credit,
    }
    (directory / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    correction = {"disposition": "descriptive_calibration_only", "causal_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0,
                  "school_score_eligible": False, "school_score_credit": 0,
                  "featured_eligible": False}
    json_write(directory / "diagnostics.json",
               {**diag, "verdict": verdict, "estimate": estimate,
                "correction": correction, "analysis_scope": "descriptive_only"})
    coeff_schema = pa.schema([
        ("term", pa.string()), ("coefficient", pa.float64()),
        ("standard_error", pa.float64()), ("p_value", pa.float64()),
    ])
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["oop_change_per_10pp"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, coeff_schema)
    json_write(directory / "chart_data.json", [
        {"country_iso3": str(row.country_iso3),
         "oop_change_pp": 10.0 * float(row.oop_change_per_10pp),
         "future_under5_mortality_annual_log_change_pp": float(row.outcome)}
        for row in panel.itertuples(index=False)
    ])
    lines = [f"# {DESIGN_ID}", "", f"**Verdict: {verdict} — descriptive only.**", "",
             f"Complete economies: {len(panel)} of {diag['candidate_economies']} source-key candidates.",
             f"Absolute exposure changes >=5 pp: {diag['large_exposure_change_economies']}; exposure IQR: {diag['exposure_iqr_pp']:.6g} pp."]
    if has_estimate:
        lines += [f"Exposure coefficient: {estimate['coefficient']:.6g} annual log-change pp per 10-pp rise; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}; LOO fits {estimate['loo_successes']}."]
    else:
        lines += ["No coefficient was estimated because a frozen gate failed."]
    lines += ["", "Out-of-pocket spending is a financing share, not a policy event. Under-five mortality is modelled. This does not test avoidable mortality or medical impoverishment. No causal, policy, school, position, or featured credit follows.", ""]
    (directory / "result_card.md").write_text("\n".join(lines))
    (directory / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER_REL}'), '--replay', *sys.argv[1:]], check=True)\n"
    )
    packet = {
        "design_id": DESIGN_ID, "verdict": verdict, "evidence_type": "descriptive",
        "causal_claim": False, "school_claim_links": [], "policy_effect_credit": False,
        "correction": correction, "source_hashes_verified": True,
        "strict_spec_lock_chronology_verified": True,
        "interpretation": "Later under-five mortality association with prior financing mix only; old broad claims remain ungraded.",
    }
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    metric_schema = pa.schema([("verdict", pa.string()), ("complete_economies", pa.int64()),
                               ("large_exposure_change_economies", pa.int64())])
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict], "complete_economies": [len(panel)],
        "large_exposure_change_economies": [diag["large_exposure_change_economies"]],
    }, metric_schema)
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError("Run artifact roster differs")


def run_or_replay(source_root: Path, replay: bool) -> None:
    spec, spec_commit, lock_commit = verify_lock(source_root)
    roster = json.loads((ROOT / LOCK_REL).read_text())["source_custody"]["candidate_economies"]
    panel, diag = panel_from_sources(source_root, roster)
    estimate, verdict = calculate(panel, diag)
    target = ROOT / RUN_REL
    if replay and not target.is_dir():
        raise ValueError("No run artifacts to replay")
    if not replay and target.exists():
        raise ValueError("Run already exists; use --replay")
    with tempfile.TemporaryDirectory(prefix="ieset_oop_under5_") as tmp:
        generated = Path(tmp) / "run"
        emit(generated, panel, diag, estimate, verdict, spec_commit, lock_commit)
        if replay:
            for name in ARTIFACTS:
                if file_sha(generated / name) != file_sha(target / name):
                    raise ValueError(f"Exact replay differs: {name}")
            print(f"Exact replay matched {len(ARTIFACTS)} artifacts")
        else:
            shutil.copytree(generated, target)
            print(f"Created {len(ARTIFACTS)} run artifacts; verdict {verdict}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare-lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--replay", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.prepare_lock:
        prepare_lock(args.source_root)
    else:
        run_or_replay(args.source_root, args.replay)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
