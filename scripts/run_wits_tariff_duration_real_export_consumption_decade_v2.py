#!/usr/bin/env python3
"""Frozen, descriptive tariff-duration two-outcome calibration.

--prepare-lock reads source bytes, schemas and country/year keys only.
--run may read selected values only after a distinct committed source lock.
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
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
DESIGN_ID = "wits_tariff_duration_real_export_consumption_decade_v2"
SPEC_REL = f"hypotheses/trade/{DESIGN_ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{DESIGN_ID}.md"
PLAN_REL = f"engine/audits/{DESIGN_ID}_prereg_2026-10-10.md"
PROVENANCE_REL = f"engine/audits/{DESIGN_ID}_source_provenance_2026-10-10.md"
RUNNER_REL = f"scripts/run_{DESIGN_ID}.py"
LOCK_REL = f"prereg/locks/{DESIGN_ID}.json"
RUN_REL = f"engine/runs/{DESIGN_ID}"
REGISTERED = (SPEC_REL, STEELMAN_REL, PLAN_REL, PROVENANCE_REL, RUNNER_REL)
SOURCES = {
    "tariff": "data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet",
    "exports": "data/vintages/world_bank_wdi/NE.EXP.GNFS.KD.ZG@2026-05-03T054026Z.parquet",
    "consumption": "data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet",
    "income": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
    "ruleoflaw": "data/vintages/wgi/GOV_WGI_RL.EST@2026-05-05T195218Z.parquet",
    "tot": "data/vintages/world_bank_wdi/TT.PRI.MRCH.XD.WD@2026-05-05T203119Z.parquet",
    "investment": "data/vintages/world_bank_wdi/NE.GDI.TOTL.ZS@2026-05-05T194659Z.parquet",
}
MANIFESTS = {
    "tariff": "data/manifests/fetch_run_2026-07-23T151550Z.yaml",
    "exports": "data/manifests/baseline_pull.yaml",
    "may5": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
    "tot": "data/manifests/fetch_run_2026-05-05T203305Z.yaml",
}
EXACT_MANIFEST_FOR_SOURCE = {
    "tariff": "tariff", "consumption": "may5", "income": "may5",
    "ruleoflaw": "may5", "tot": "tot", "investment": "may5",
}
REQUIRED = {
    "tariff": range(2001, 2011),
    "exports": range(2001, 2021),
    "consumption": (2000, 2010, 2020),
    "income": (2010,),
    "ruleoflaw": (2010,),
    "tot": (2010,),
    "investment": (2010,),
}
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)
COVARIATE_NAMES = (
    "intercept", "duration_decades", "terminal_tariff",
    "log_income", "ruleoflaw", "log_tot", "investment", "pretrend",
)
OUTCOMES = ("exports", "consumption")


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest_keys(keys: list[tuple[str, int]]) -> str:
    raw = "".join(f"{c},{y}\n" for c, y in sorted(keys)).encode()
    return hashlib.sha256(raw).hexdigest()


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
        raise ValueError("Registered YAML ID or status differs")
    countries = spec["sample"]["countries"]
    if len(countries) != 65 or len(set(countries)) != 65 or countries != sorted(countries):
        raise ValueError("Frozen sample roster must be 65 unique sorted ISO3 keys")
    return commit, spec


def source_keys(path: Path, countries: list[str], years: range | tuple[int, ...]) -> tuple[list[tuple[str, int]], list[str]]:
    if not path.is_file():
        raise ValueError(f"Missing preserved source {path}")
    names = pq.ParquetFile(path).schema_arrow.names
    if not {"country_iso3", "year", "value"}.issubset(names):
        raise ValueError(f"Source schema lacks country/year/value: {path}")
    rows = pq.read_table(path, columns=["country_iso3", "year"]).to_pylist()
    targets = set(countries)
    needed = set(years)
    keys = [(row["country_iso3"], int(row["year"])) for row in rows
            if row["country_iso3"] in targets and int(row["year"]) in needed]
    if len(keys) != len(set(keys)):
        raise ValueError(f"Duplicate selected source key: {path}")
    wanted = {(c, y) for c in countries for y in years}
    if set(keys) != wanted:
        missing = sorted(wanted - set(keys))
        raise ValueError(f"Selected source keys missing: {path}: {missing[:5]}")
    return keys, names


def preflight(source_root: Path, countries: list[str]) -> dict:
    """No value, null, or observation-status column is read here."""
    source_info = {}
    for role, relative in SOURCES.items():
        path = source_root / relative
        keys, names = source_keys(path, countries, REQUIRED[role])
        source_info[role] = {
            "path": relative,
            "sha256": file_sha(path),
            "selected_key_sha256": digest_keys(keys),
            "selected_key_count": len(keys),
            "schema_names": names,
        }
    manifest_info = {}
    for role, relative in MANIFESTS.items():
        path = source_root / relative
        if not path.is_file():
            raise ValueError(f"Missing source custody file: {path}")
        manifest_info[role] = {"path": relative, "sha256": file_sha(path)}
    for source_role, manifest_role in EXACT_MANIFEST_FOR_SOURCE.items():
        entries = yaml.safe_load((source_root / MANIFESTS[manifest_role]).read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("parquet_path") == SOURCES[source_role]]
        if len(matches) != 1 or matches[0].get("sha256") != source_info[source_role]["sha256"]:
            raise ValueError(f"Fetch-manifest source/hash mismatch: {source_role}")
    baseline = yaml.safe_load((source_root / MANIFESTS["exports"]).read_text())
    world_bank_pulls = [pull for pull in baseline.get("pulls", [])
                        if pull.get("publisher") == "world_bank_wdi"]
    if not any(
            series.get("id") == "NE.EXP.GNFS.KD.ZG"
            for pull in world_bank_pulls for series in pull.get("series", [])):
        raise ValueError("WDI export-growth indicator absent from baseline pull configuration")
    return {"sources": source_info, "manifests": manifest_info,
            "exact_fetch_manifest_roles_verified": sorted(EXACT_MANIFEST_FOR_SOURCE),
            "export_fetch_receipt_available": False,
            "candidate_country_count": len(countries),
            "candidate_country_sha256": hashlib.sha256(
                "".join(f"{c}\n" for c in countries).encode()).hexdigest()}


def expected_lock(source_root: Path) -> dict:
    spec_commit, spec = registered_spec()
    return {
        "design_id": DESIGN_ID,
        "spec_commit": spec_commit,
        "registered_sha256": {path: file_sha(ROOT / path) for path in REGISTERED},
        "source_custody": preflight(source_root, spec["sample"]["countries"]),
        "custody_limit": "The WDI export-growth vintage has no exact fetch-time manifest or raw API payload; see frozen local provenance note. Descriptive calibration only.",
        "instruction": "Commit this source lock separately before loading any selected values.",
    }


def prepare_lock(source_root: Path) -> None:
    lock_path = ROOT / LOCK_REL
    if lock_path.exists():
        raise ValueError("Source lock already exists")
    data = expected_lock(source_root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print(f"Prepared key-only source lock: {lock_path}")


def verify_lock(source_root: Path) -> tuple[dict, str, str]:
    spec_commit, spec = registered_spec()
    lock_commit = first_add_commit(LOCK_REL)
    committed_original(LOCK_REL, lock_commit)
    if lock_commit == spec_commit or not ancestor(spec_commit, lock_commit) or not ancestor(lock_commit, "HEAD"):
        raise ValueError("Registration and source lock chronology is not strict")
    expected = expected_lock(source_root)
    actual = json.loads((ROOT / LOCK_REL).read_text())
    if actual != expected:
        raise ValueError("Source bytes, keys, manifests, or registered files differ from lock")
    return spec, spec_commit, lock_commit


def value_map(path: Path, countries: list[str], years: range | tuple[int, ...]) -> dict[tuple[str, int], object]:
    table = pq.read_table(path, columns=["country_iso3", "year", "value"])
    selected_countries, selected_years = set(countries), set(years)
    out = {}
    for row in table.to_pylist():
        key = (row["country_iso3"], int(row["year"]))
        if key[0] not in selected_countries or key[1] not in selected_years:
            continue
        if key in out:
            raise ValueError(f"Duplicate selected source value key: {path}: {key}")
        out[key] = row["value"]
    return out


def finite(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def load_panel(source_root: Path, countries: list[str]) -> tuple[pd.DataFrame, dict]:
    """Selected values are first read here, after verify_lock."""
    values = {role: value_map(source_root / path, countries, REQUIRED[role])
              for role, path in SOURCES.items()}
    rows = []
    missing = {}
    for country in countries:
        def cell(role: str, year: int) -> float | None:
            return finite(values[role].get((country, year)))
        tariffs = [cell("tariff", y) for y in range(2001, 2011)]
        exports = [cell("exports", y) for y in range(2001, 2021)]
        consumption = {y: cell("consumption", y) for y in (2000, 2010, 2020)}
        income = cell("income", 2010)
        ruleoflaw = cell("ruleoflaw", 2010)
        tot = cell("tot", 2010)
        investment = cell("investment", 2010)
        reasons = []
        if any(x is None or not 0 <= x <= 100 for x in tariffs):
            reasons.append("tariff_2001_2010_missing_or_out_of_range")
        if any(x is None for x in exports):
            reasons.append("export_growth_2001_2020_missing")
        if any(x is None or x <= 0 for x in consumption.values()):
            reasons.append("consumption_levels_missing_or_nonpositive")
        if income is None or income <= 0:
            reasons.append("income_2010_missing_or_nonpositive")
        if ruleoflaw is None:
            reasons.append("ruleoflaw_2010_missing")
        if tot is None or tot <= 0:
            reasons.append("terms_of_trade_2010_missing_or_nonpositive")
        if investment is None:
            reasons.append("investment_2010_missing")
        if reasons:
            for reason in reasons:
                missing[reason] = missing.get(reason, 0) + 1
            continue
        high_years = sum(x > 15.0 for x in tariffs)
        rows.append({
            "country_iso3": country,
            "duration_decades": high_years / 10.0,
            "high_tariff_years": high_years,
            "terminal_tariff": tariffs[-1],
            "log_income": math.log(income),
            "ruleoflaw": ruleoflaw,
            "log_tot": math.log(tot),
            "investment": investment,
            "exports_pretrend": float(np.mean(exports[:10])),
            "exports_outcome": float(np.mean(exports[10:])),
            "consumption_pretrend": 10.0 * (math.log(consumption[2010]) - math.log(consumption[2000])),
            "consumption_outcome": 10.0 * (math.log(consumption[2020]) - math.log(consumption[2010])),
        })
    panel = pd.DataFrame(rows)
    if len(panel):
        panel = panel.sort_values("country_iso3").reset_index(drop=True)
    return panel, {"candidate_countries": len(countries),
                   "complete_countries": len(panel),
                   "excluded_by_reason_overlapping": missing}


def design(panel: pd.DataFrame, outcome: str) -> tuple[np.ndarray, np.ndarray]:
    x = np.column_stack([
        np.ones(len(panel)),
        panel["duration_decades"].to_numpy(dtype=float),
        panel["terminal_tariff"].to_numpy(dtype=float),
        panel["log_income"].to_numpy(dtype=float),
        panel["ruleoflaw"].to_numpy(dtype=float),
        panel["log_tot"].to_numpy(dtype=float),
        panel["investment"].to_numpy(dtype=float),
        panel[f"{outcome}_pretrend"].to_numpy(dtype=float),
    ])
    y = panel[f"{outcome}_outcome"].to_numpy(dtype=float)
    return x, y


def fit(panel: pd.DataFrame, outcome: str) -> dict:
    x, y = design(panel, outcome)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank model unavailable")
    estimate = sm.OLS(y, x).fit(cov_type="HC3")
    beta = float(estimate.params[1])
    se = float(estimate.bse[1])
    p = float(2 * student_t.sf(abs(beta / se), df=n - k)) if se > 0 else float("nan")
    if not all(math.isfinite(v) for v in (beta, se, p)) or se <= 0:
        raise ValueError("Nonfinite HC3 estimate")
    z = x[:, [0, 2, 3, 4, 5, 6, 7]]
    partial = x[:, 1] - z @ np.linalg.lstsq(z, x[:, 1], rcond=None)[0]
    squared = partial * partial
    if float(squared.sum()) <= 1e-12:
        raise ValueError("No partialled duration variation")
    influence = float(squared.max() / squared.sum())
    return {"outcome": outcome, "coefficient": beta,
            "standard_error": se, "p_value": p,
            "reference_df": n - k, "covariance": "HC3",
            "max_single_country_partialled_duration_share": influence}


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict[str, dict], str]:
    results = {}
    n = len(panel)
    diag["zero_duration_countries"] = int((panel["high_tariff_years"] == 0).sum()) if n else 0
    diag["two_year_duration_countries"] = int((panel["high_tariff_years"] >= 2).sum()) if n else 0
    if n < 40 or diag["zero_duration_countries"] < 10 or diag["two_year_duration_countries"] < 10:
        diag["failed_gate"] = "sample_or_exposure_floor"
        return results, "INCONCLUSIVE"
    for outcome in OUTCOMES:
        try:
            estimate = fit(panel, outcome)
            loo = []
            for country in panel["country_iso3"]:
                subset = panel.loc[panel["country_iso3"] != country]
                try:
                    loo.append(fit(subset, outcome)["coefficient"])
                except ValueError:
                    continue
            estimate["loo_successes"] = len(loo)
            estimate["loo_negative_share"] = (sum(v < 0 for v in loo) / len(loo)) if loo else None
            estimate["loo_positive_share"] = (sum(v > 0 for v in loo) / len(loo)) if loo else None
            results[outcome] = estimate
        except ValueError as exc:
            diag["failed_gate"] = f"{outcome}_estimator:{exc}"
            return results, "INCONCLUSIVE"
    for outcome in OUTCOMES:
        estimate = results[outcome]
        if (estimate["max_single_country_partialled_duration_share"] > 0.20
                or estimate["loo_successes"] < max(35, n - 2)):
            diag["failed_gate"] = f"{outcome}_influence_or_loo"
            return results, "INCONCLUSIVE"
    magnitude = {"exports": 0.20, "consumption": 0.10}
    positive = any(
        (results[o]["coefficient"] >= magnitude[o] and results[o]["p_value"] <= 0.025
         and results[o]["loo_positive_share"] >= 0.75)
        for o in OUTCOMES
    )
    if positive:
        return results, "REFUTED"
    negative = all(
        (results[o]["coefficient"] <= -magnitude[o] and results[o]["p_value"] <= 0.025
         and results[o]["loo_negative_share"] >= 0.75)
        for o in OUTCOMES
    )
    return results, "SUPPORTED" if negative else "PARTIAL"


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, panel: pd.DataFrame, diag: dict, results: dict[str, dict],
         verdict: str, spec_commit: str, lock_commit: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    correction = {"disposition": "descriptive_calibration_only",
                  "causal_credit": 0, "policy_score_eligible": False,
                  "policy_score_credit": 0, "school_score_eligible": False,
                  "school_score_credit": 0, "featured_eligible": False}
    manifest = {
        "design_id": DESIGN_ID, "verdict": verdict, "evidence_type": "descriptive",
        "spec_commit": spec_commit, "lock_commit": lock_commit,
        "spec_sha256": file_sha(ROOT / SPEC_REL),
        "lock_sha256": file_sha(ROOT / LOCK_REL),
        "runner_sha256": file_sha(ROOT / RUNNER_REL),
        "source_custody": json.loads((ROOT / LOCK_REL).read_text())["source_custody"],
        "artifacts": list(ARTIFACTS),
        "credit": {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0},
    }
    (directory / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    diag = {**diag, "verdict": verdict, "estimates": results,
            "correction": correction, "analysis_scope": "descriptive_only",
            "source_fetch_manifest_limit": "Export-growth vintage has no exact fetch-time manifest."}
    json_write(directory / "diagnostics.json", diag)
    coeff_schema = pa.schema([
        ("outcome", pa.string()), ("term", pa.string()), ("coefficient", pa.float64()),
        ("standard_error", pa.float64()), ("p_value", pa.float64()),
    ])
    ordered = [results[o] for o in OUTCOMES if o in results]
    parquet_write(directory / "coefficients.parquet",
                  {"outcome": [r["outcome"] for r in ordered],
                   "term": ["duration_decades"] * len(ordered),
                   "coefficient": [r["coefficient"] for r in ordered],
                   "standard_error": [r["standard_error"] for r in ordered],
                   "p_value": [r["p_value"] for r in ordered]}, coeff_schema)
    chart = [
        {"country_iso3": str(r.country_iso3),
         "high_tariff_years": int(r.high_tariff_years),
         "export_growth_2011_2020_pp": float(r.exports_outcome),
         "consumption_growth_2010_2020_pp": float(r.consumption_outcome)}
        for r in panel.itertuples(index=False)
    ]
    json_write(directory / "chart_data.json", chart)
    lines = [f"# {DESIGN_ID}", "", f"**Verdict: {verdict} — descriptive only.**", "",
             f"Complete countries: {len(panel)} of 65 source-key candidates.",
             f"Zero-duration countries: {diag['zero_duration_countries']}; two-or-more-year countries: {diag['two_year_duration_countries']}.", ""]
    for outcome in OUTCOMES:
        if outcome in results:
            r = results[outcome]
            lines.append(f"{outcome}: duration coefficient {r['coefficient']:.6g} pp/year per protection decade; HC3 SE {r['standard_error']:.6g}; two-sided p {r['p_value']:.6g}; LOO fits {r['loo_successes']}.")
        else:
            lines.append(f"{outcome}: not estimated because a frozen gate failed.")
    lines += ["", "The WITS exposure is a weighted tariff series, not a policy event. Real exports include goods and services. The 2020 endpoint includes pandemic disruption. No causal, policy, school, position, or featured credit follows.", ""]
    (directory / "result_card.md").write_text("\n".join(lines))
    replication = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER_REL}'), '--replay', *sys.argv[1:]], check=True)\n"
    )
    (directory / "replication.py").write_text(replication)
    packet = {"design_id": DESIGN_ID, "verdict": verdict,
              "evidence_type": "descriptive", "causal_claim": False,
              "school_claim_links": [], "policy_effect_credit": False,
              "correction": correction, "source_hashes_verified": True,
              "strict_spec_lock_chronology_verified": True,
              "interpretation": "Two-outcome tariff-duration association only; original archived claim remains ungraded."}
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    metric_schema = pa.schema([
        ("verdict", pa.string()), ("complete_countries", pa.int64()),
        ("zero_duration_countries", pa.int64()),
        ("two_year_duration_countries", pa.int64()),
    ])
    parquet_write(directory / "metric_results.parquet",
                  {"verdict": [verdict], "complete_countries": [len(panel)],
                   "zero_duration_countries": [diag["zero_duration_countries"]],
                   "two_year_duration_countries": [diag["two_year_duration_countries"]]},
                  metric_schema)
    actual = tuple(sorted(p.name for p in directory.iterdir()))
    if actual != tuple(sorted(ARTIFACTS)):
        raise ValueError(f"Run artifact roster differs: {actual}")


def run_or_replay(source_root: Path, replay: bool) -> None:
    spec, spec_commit, lock_commit = verify_lock(source_root)
    panel, diag = load_panel(source_root, spec["sample"]["countries"])
    results, verdict = calculate(panel, diag)
    target = ROOT / RUN_REL
    if replay and not target.is_dir():
        raise ValueError("No run artifacts to replay")
    if not replay and target.exists():
        raise ValueError("Run already exists; use --replay")
    with tempfile.TemporaryDirectory(prefix="ieset_tariff_duration_") as tmp:
        generated = Path(tmp) / "run"
        emit(generated, panel, diag, results, verdict, spec_commit, lock_commit)
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
