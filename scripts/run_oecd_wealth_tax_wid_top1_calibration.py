#!/usr/bin/env python3
"""Locked, descriptive OECD wealth-tax receipts / WID top-1 calibration.

Do not invoke --run before distinct spec and source-lock commits. --prepare-lock
reads only source bytes and country/year keys; it never reads source values.
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
from patsy import dmatrix
from scipy.stats import t as student_t
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
DESIGN_ID = "oecd_wealth_tax_receipts_wid_top1_share_lag3_calibration"
SPEC_REL = f"hypotheses/distribution/{DESIGN_ID}.yaml"
ROSTER_REL = "engine/audits/prospective_wealth_tax_top1_calibration/source_roster.json"
LOCK_REL = f"prereg/locks/{DESIGN_ID}.json"
RUN_REL = f"engine/runs/{DESIGN_ID}"
RUNNER_REL = "scripts/run_oecd_wealth_tax_wid_top1_calibration.py"
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def key_digest(keys: list[tuple[str, int]]) -> str:
    """Hash unique, sorted country/year keys without touching values."""
    return sha256_bytes("".join(f"{country},{year}\n" for country, year in keys).encode())


def pair_digest(pairs: list[tuple[str, int]]) -> str:
    return sha256_bytes("".join(f"{country},{year},{year + 3}\n" for country, year in pairs).encode())


def source_keys(path: Path, expected: dict) -> set[tuple[str, int]]:
    if not path.is_file():
        raise ValueError(f"Missing pinned source: {path}")
    if sha256_file(path) != expected["sha256"]:
        raise ValueError(f"Pinned source byte hash differs: {path}")
    schema = pq.ParquetFile(path).schema_arrow
    if set(schema.names) != {"country_iso3", "year", "value"}:
        raise ValueError(f"Unexpected source schema: {path}: {schema.names}")
    rows = pq.read_table(path, columns=["country_iso3", "year"]).to_pylist()
    keys = [(row["country_iso3"], int(row["year"])) for row in rows]
    if len(keys) != len(set(keys)) or any(not isinstance(c, str) or len(c) != 3 for c, _ in keys):
        raise ValueError(f"Duplicate or invalid source key: {path}")
    keys = sorted(keys)
    if len(keys) != expected["key_count"] or key_digest(keys) != expected["key_sha256"]:
        raise ValueError(f"Pinned source key roster differs: {path}")
    return set(keys)


def preflight(source_root: Path, roster: dict) -> list[tuple[str, int]]:
    """Values and null status are intentionally unavailable to this function."""
    sources = roster["sources"]
    for source in sources.values():
        if "publisher_manifest" in source:
            manifest = source_root / source["publisher_manifest"]
            if not manifest.is_file() or sha256_file(manifest) != source["publisher_manifest_sha256"]:
                raise ValueError(f"Publisher manifest is missing or changed: {manifest}")
        for upstream in source.get("upstream", []):
            upstream_path = source_root / upstream["path"]
            if not upstream_path.is_file() or sha256_file(upstream_path) != upstream["sha256"]:
                raise ValueError(f"Upstream source is missing or changed: {upstream_path}")
    tax = source_keys(source_root / sources["treatment"]["path"], sources["treatment"])
    wealth = source_keys(source_root / sources["outcome"]["path"], sources["outcome"])
    adapter = source_root / sources["outcome"]["derived_adapter"]
    if not adapter.is_file() or sha256_file(adapter) != sources["outcome"]["derived_adapter_sha256"]:
        raise ValueError("Pinned WID adapter is missing or changed")
    pairs = sorted((country, year) for country, year in tax
                   if 1990 <= year <= 2020 and (country, year + 3) in wealth)
    if len(pairs) != roster["analytic_key_count"] or pair_digest(pairs) != roster["analytic_key_sha256"]:
        raise ValueError("Pinned analytic key roster differs")
    if sorted({country for country, _ in pairs}) != roster["country_roster"]:
        raise ValueError("Pinned country roster differs")
    return pairs


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_add_commit(path: str) -> str:
    commits = git("log", "--follow", "--diff-filter=A", "--format=%H", "--", path).decode().splitlines()
    if not commits:
        raise ValueError(f"Path has no preregistration commit: {path}")
    return commits[-1]


def committed_original(path: str, commit: str) -> None:
    current = (ROOT / path).read_bytes()
    if git("show", f"{commit}:{path}") != current or git("show", f"HEAD:{path}") != current:
        raise ValueError(f"Registered file changed after first commit: {path}")


def ancestor(older: str, newer: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", older, newer],
                          cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def registered_spec() -> tuple[str, dict]:
    commit = first_add_commit(SPEC_REL)
    committed_original(SPEC_REL, commit)
    for path in (ROSTER_REL, RUNNER_REL):
        if first_add_commit(path) != commit:
            raise ValueError(f"Source roster and runner must enter with the spec: {path}")
        committed_original(path, commit)
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text())
    if spec["hypothesis_id"] != DESIGN_ID or spec["status"] != "pre_registered":
        raise ValueError("Spec must be committed as pre_registered before lock")
    return commit, spec


def prepare_lock(source_root: Path, roster: dict) -> None:
    spec_commit, _ = registered_spec()
    preflight(source_root, roster)
    lock_path = ROOT / LOCK_REL
    if lock_path.exists():
        raise ValueError("Lock already exists")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = {
        "design_id": DESIGN_ID,
        "spec_commit": spec_commit,
        "spec_sha256": sha256_file(ROOT / SPEC_REL),
        "roster_sha256": sha256_file(ROOT / ROSTER_REL),
        "runner_sha256": sha256_file(ROOT / RUNNER_REL),
        "source_sha256": {role: info["sha256"] for role, info in roster["sources"].items()},
        "analytic_key_sha256": roster["analytic_key_sha256"],
        "instruction": "Commit this lock in a separate commit. Only then run estimation.",
    }
    lock_path.write_text(json.dumps(lock, sort_keys=True, indent=2) + "\n")
    print(f"Prepared uncommitted source lock: {lock_path}")


def verify_lock(source_root: Path, roster: dict) -> tuple[dict, str, str]:
    spec_commit, _ = registered_spec()
    lock_commit = first_add_commit(LOCK_REL)
    committed_original(LOCK_REL, lock_commit)
    if lock_commit == spec_commit or not ancestor(spec_commit, lock_commit) or not ancestor(lock_commit, "HEAD"):
        raise ValueError("Spec, lock, and run chronology is not strict")
    lock = json.loads((ROOT / LOCK_REL).read_text())
    expected = {
        "design_id": DESIGN_ID,
        "spec_commit": spec_commit,
        "spec_sha256": sha256_file(ROOT / SPEC_REL),
        "roster_sha256": sha256_file(ROOT / ROSTER_REL),
        "runner_sha256": sha256_file(ROOT / RUNNER_REL),
        "source_sha256": {role: info["sha256"] for role, info in roster["sources"].items()},
        "analytic_key_sha256": roster["analytic_key_sha256"],
        "instruction": "Commit this lock in a separate commit. Only then run estimation.",
    }
    if lock != expected:
        raise ValueError("Lock does not bind the current spec, roster, runner, and sources")
    preflight(source_root, roster)
    return lock, spec_commit, lock_commit


def load_analysis(source_root: Path, roster: dict, pairs: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict]:
    """The first value read is allowed only after verify_lock succeeds."""
    sources = roster["sources"]
    tax = pq.read_table(source_root / sources["treatment"]["path"]).to_pandas()
    wealth = pq.read_table(source_root / sources["outcome"]["path"]).to_pandas()
    tax = tax.rename(columns={"year": "tax_year", "value": "tax_receipts"})
    wealth = wealth.rename(columns={"year": "outcome_year", "value": "top1_share"})
    wealth["tax_year"] = wealth["outcome_year"] - 3
    panel = tax.merge(wealth[["country_iso3", "tax_year", "top1_share"]],
                      on=["country_iso3", "tax_year"], how="inner", validate="one_to_one")
    panel = panel.loc[panel["tax_year"].between(1990, 2020)].copy()
    panel = panel.sort_values(["country_iso3", "tax_year"]).reset_index(drop=True)
    if list(zip(panel["country_iso3"], panel["tax_year"])) != pairs:
        raise ValueError("Value load altered the frozen key roster")
    for column in ("tax_receipts", "top1_share"):
        panel[column] = pd.to_numeric(panel[column], errors="coerce")
    finite = np.isfinite(panel["tax_receipts"]) & np.isfinite(panel["top1_share"])
    complete = panel.loc[finite].copy()
    diag = {"candidate_key_pairs": len(pairs), "excluded_missing_or_nonfinite": int((~finite).sum()),
            "complete_pairs": len(complete),
            "countries": int(complete.country_iso3.nunique()),
            "tax_years": int(complete.tax_year.nunique()),
            "varying_countries": int(sum(group.tax_receipts.max() - group.tax_receipts.min() > 1e-8
                                         for _, group in complete.groupby("country_iso3")))}
    diag["invalid_range_rows"] = int(((complete.tax_receipts < 0) | (complete.tax_receipts > 100) |
                                       (complete.top1_share < 0) | (complete.top1_share > 100)).sum())
    return complete, diag


def fit(panel: pd.DataFrame) -> dict:
    model = smf.ols("top1_share ~ tax_receipts + C(country_iso3) + C(tax_year)", data=panel)
    x = np.asarray(model.exog, dtype=float)
    n, k = x.shape
    if np.linalg.matrix_rank(x) != k or n <= k:
        raise ValueError("Main design matrix is not full rank")
    result = model.fit()
    residuals = np.asarray(result.resid, dtype=float)
    groups = panel["country_iso3"].to_numpy()
    countries = sorted(set(groups))
    g = len(countries)
    if g <= 1:
        raise ValueError("Too few country clusters")
    xpx_inverse = np.linalg.inv(x.T @ x)
    meat = np.zeros((k, k), dtype=float)
    for country in countries:
        cluster_score = x[groups == country].T @ residuals[groups == country]
        meat += np.outer(cluster_score, cluster_score)
    cr1 = (g / (g - 1)) * ((n - 1) / (n - k))
    covariance = cr1 * (xpx_inverse @ meat @ xpx_inverse)
    term_index = model.exog_names.index("tax_receipts")
    beta = float(result.params["tax_receipts"])
    se = float(np.sqrt(covariance[term_index, term_index]))
    statistic = beta / se if se > 0 else float("nan")
    p = float(2 * student_t.sf(abs(statistic), df=g - 1))
    if not all(math.isfinite(x) for x in (beta, se, p)) or se <= 0:
        raise ValueError("Nonfinite or degenerate coefficient")
    return {"coefficient": beta, "standard_error": se, "t_statistic": statistic,
            "p_value": p, "reference_df": g - 1, "covariance": "CR1_country_cluster"}


def residualized_treatment_influence(panel: pd.DataFrame) -> dict:
    """Concentration of complete-case treatment variation after fixed effects."""
    z = np.asarray(dmatrix("1 + C(country_iso3) + C(tax_year)", panel), dtype=float)
    if np.linalg.matrix_rank(z) != z.shape[1]:
        raise ValueError("Fixed-effects-only design is not full rank")
    receipts = panel["tax_receipts"].to_numpy(dtype=float)
    residual = receipts - z @ np.linalg.lstsq(z, receipts, rcond=None)[0]
    squared = residual * residual
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 1e-12:
        raise ValueError("No residualized treatment signal")
    count = max(1, math.ceil(len(panel) * 0.01))
    top_rows = float(np.sort(squared)[-count:].sum() / total)
    top_country = float(pd.Series(squared).groupby(panel["country_iso3"].to_numpy()).sum().max() / total)
    top_year = float(pd.Series(squared).groupby(panel["tax_year"].to_numpy()).sum().max() / total)
    return {"top_one_percent_rows": top_rows, "top_one_percent_row_count": count,
            "top_country": top_country, "top_tax_year": top_year,
            "passed": top_rows <= 0.20 and top_country <= 0.15 and top_year <= 0.20}


def classify(diag: dict, estimate: dict | None, loo: list[float]) -> str:
    if (diag["complete_pairs"] < 400 or diag["countries"] < 25 or diag["tax_years"] < 20
            or diag["varying_countries"] < 15 or diag["invalid_range_rows"] or
            not diag.get("full_rank") or not diag.get("influence_pass") or
            estimate is None or len(loo) < 25):
        return "INCONCLUSIVE"
    beta, p = estimate["coefficient"], estimate["p_value"]
    if p <= 0.01 and beta <= -0.5 and sum(x < 0 for x in loo) / len(loo) >= 0.8:
        return "SUPPORTED"
    if p <= 0.01 and beta >= 0.5 and sum(x > 0 for x in loo) / len(loo) >= 0.8:
        return "REFUTED"
    return "PARTIAL"


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict | None, list[float], str]:
    diag["full_rank"] = False
    diag["influence_pass"] = False
    if (diag["complete_pairs"] < 400 or diag["countries"] < 25 or diag["tax_years"] < 20
            or diag["varying_countries"] < 15 or diag["invalid_range_rows"]):
        return None, [], "INCONCLUSIVE"
    try:
        influence = residualized_treatment_influence(panel)
        diag["residualized_treatment_influence"] = influence
        diag["influence_pass"] = influence["passed"]
        if not influence["passed"]:
            return None, [], "INCONCLUSIVE"
        estimate = fit(panel)
        diag["full_rank"] = True
    except (ValueError, KeyError, np.linalg.LinAlgError):
        return None, [], "INCONCLUSIVE"
    loo = []
    for country in sorted(panel.country_iso3.unique()):
        try:
            loo.append(fit(panel.loc[panel.country_iso3 != country])["coefficient"])
        except (ValueError, KeyError, np.linalg.LinAlgError):
            continue
    return estimate, loo, classify(diag, estimate, loo)


def json_write(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, panel: pd.DataFrame, diag: dict, estimate: dict | None,
         loo: list[float], verdict: str, roster: dict, spec_commit: str, lock_commit: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    manifest = {
        "design_id": DESIGN_ID, "evidence_type": "descriptive", "verdict": verdict,
        "spec_commit": spec_commit, "lock_commit": lock_commit,
        "spec_sha256": sha256_file(ROOT / SPEC_REL),
        "lock_sha256": sha256_file(ROOT / LOCK_REL),
        "roster_sha256": sha256_file(ROOT / ROSTER_REL),
        "runner_sha256": sha256_file(ROOT / RUNNER_REL),
        "analytic_key_sha256": roster["analytic_key_sha256"],
        "source_files": {role: {"path": item["path"], "sha256": item["sha256"]}
                         for role, item in roster["sources"].items()},
        "artifacts": list(ARTIFACTS),
        "credit": {"causal": 0, "policy": 0, "school": 0, "featured": 0},
    }
    (directory / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=True))
    correction = {"disposition": "descriptive_calibration_only",
                  "causal_credit": 0, "policy_score_eligible": False,
                  "policy_score_credit": 0, "school_score_eligible": False,
                  "school_score_credit": 0, "featured_eligible": False}
    diag = {**diag, "correction": correction, "verdict": verdict, "main_estimate": estimate,
            "loo_successes": len(loo),
            "loo_negative_share": sum(x < 0 for x in loo) / len(loo) if loo else None,
            "loo_positive_share": sum(x > 0 for x in loo) / len(loo) if loo else None,
            "analysis_scope": "descriptive_only", "causal_policy_school_featured_credit": 0}
    json_write(directory / "diagnostics.json", diag)
    coeff_schema = pa.schema([("term", pa.string()), ("coefficient", pa.float64()),
                              ("standard_error", pa.float64()), ("p_value", pa.float64())])
    values = [estimate] if estimate else []
    parquet_write(directory / "coefficients.parquet",
                  {"term": ["tax_receipts"] * len(values),
                   "coefficient": [row["coefficient"] for row in values],
                   "standard_error": [row["standard_error"] for row in values],
                   "p_value": [row["p_value"] for row in values]}, coeff_schema)
    chart = []
    for year, group in panel.groupby("tax_year", sort=True):
        chart.append({"tax_year": int(year), "countries": int(group.country_iso3.nunique()),
                      "mean_tax_receipts_pct_gdp": float(group.tax_receipts.mean()),
                      "mean_top1_share_t_plus_3": float(group.top1_share.mean())})
    json_write(directory / "chart_data.json", chart)
    beta_text = "not estimated" if estimate is None else f"{estimate['coefficient']:.6g} (SE {estimate['standard_error']:.6g}; p {estimate['p_value']:.6g})"
    card = (f"# {DESIGN_ID}\n\n**Verdict: {verdict} — descriptive only.**\n\n"
            f"Main coefficient: {beta_text}. Complete pairs: {diag['complete_pairs']}; "
            f"countries: {diag['countries']}; tax years: {diag['tax_years']}; "
            f"leave-one-country-out fits: {len(loo)}.\n\n"
            "Tax receipts are endogenous to the tax base, GDP and enforcement. "
            "This result has zero causal, policy, school and featured credit. "
            "See diagnostics and the pre-registered steelman.\n")
    (directory / "result_card.md").write_text(card)
    replication = ("#!/usr/bin/env python3\n"
                   "from pathlib import Path\nimport subprocess\nimport sys\n"
                   "root = Path(__file__).resolve().parents[3]\n"
                   f"runner = root / '{RUNNER_REL}'\n"
                   "subprocess.run([sys.executable, str(runner), '--replay', *sys.argv[1:]], check=True)\n")
    (directory / "replication.py").write_text(replication)
    packet = {"design_id": DESIGN_ID, "verdict": verdict,
              "evidence_type": "descriptive", "causal_claim": False,
              "school_claim_links": [], "policy_effect_credit": False,
              "correction": correction,
              "source_hashes_verified": True, "key_roster_verified": True,
              "strict_spec_lock_chronology_verified": True,
              "interpretation": "Associational calibration only; no policy effect inferred."}
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=True))
    metric_schema = pa.schema([("verdict", pa.string()), ("complete_pairs", pa.int64()),
                               ("countries", pa.int64()), ("tax_years", pa.int64()),
                               ("loo_successes", pa.int64())])
    parquet_write(directory / "metric_results.parquet",
                  {"verdict": [verdict], "complete_pairs": [diag["complete_pairs"]],
                   "countries": [diag["countries"]], "tax_years": [diag["tax_years"]],
                   "loo_successes": [len(loo)]}, metric_schema)
    actual = tuple(sorted(p.name for p in directory.iterdir()))
    if actual != tuple(sorted(ARTIFACTS)):
        raise ValueError(f"Run artifact roster differs: {actual}")


def run_or_replay(source_root: Path, roster: dict, replay: bool) -> None:
    _, spec_commit, lock_commit = verify_lock(source_root, roster)
    pairs = preflight(source_root, roster)
    panel, diag = load_analysis(source_root, roster, pairs)
    estimate, loo, verdict = calculate(panel, diag)
    target = ROOT / RUN_REL
    if replay and not target.is_dir():
        raise ValueError("No existing run artifacts to replay")
    if not replay and target.exists():
        raise ValueError("Run artifacts already exist; use --replay")
    with tempfile.TemporaryDirectory(prefix="ieset_wealth_tax_replay_") as tmp:
        generated = Path(tmp) / "run"
        emit(generated, panel, diag, estimate, loo, verdict, roster, spec_commit, lock_commit)
        if replay:
            for name in ARTIFACTS:
                if sha256_file(generated / name) != sha256_file(target / name):
                    raise ValueError(f"Exact replay mismatch: {name}")
            print(f"Exact replay matched all {len(ARTIFACTS)} artifacts")
        else:
            shutil.copytree(generated, target)
            print(f"Created {len(ARTIFACTS)} run artifacts in {target}; verdict {verdict}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare-lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--replay", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT,
                        help="Checkout containing the exact pinned data/vintages files")
    args = parser.parse_args()
    roster = json.loads((ROOT / ROSTER_REL).read_text())
    if args.prepare_lock:
        prepare_lock(args.source_root, roster)
    else:
        run_or_replay(args.source_root, roster, args.replay)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
