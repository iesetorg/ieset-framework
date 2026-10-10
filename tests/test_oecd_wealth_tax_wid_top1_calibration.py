"""Synthetic-only tests; never inspect the pinned outcome values before lock."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from scipy.stats import t as student_t
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import cov_cluster

RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts/run_oecd_wealth_tax_wid_top1_calibration.py"
SPEC = importlib.util.spec_from_file_location("wealth_tax_runner", RUNNER_PATH)
assert SPEC and SPEC.loader
run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(path: Path, rows: list[tuple[str, int, float]]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({"country_iso3": [c for c, _, _ in rows],
                      "year": [y for _, y, _ in rows],
                      "value": [v for _, _, v in rows]})
    pq.write_table(table, path)
    keys = sorted((c, y) for c, y, _ in rows)
    return {"path": str(path), "sha256": _sha(path),
            "key_sha256": run.key_digest(keys), "key_count": len(keys)}


def test_key_only_preflight_and_hash_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    treatment_path = tmp_path / "tax.parquet"
    outcome_path = tmp_path / "wealth.parquet"
    tax = _source(treatment_path, [("AAA", 2000, 0.5), ("BBB", 2000, 0.1)])
    wealth = _source(outcome_path, [("AAA", 2003, 10.0), ("BBB", 2003, 20.0)])
    adapter = tmp_path / "adapter.py"
    adapter.write_text("# synthetic adapter\n")
    wealth["derived_adapter"] = "adapter.py"
    wealth["derived_adapter_sha256"] = _sha(adapter)
    tax["path"] = "tax.parquet"
    wealth["path"] = "wealth.parquet"
    pairs = [("AAA", 2000), ("BBB", 2000)]
    roster = {"sources": {"treatment": tax, "outcome": wealth},
              "analytic_key_count": 2, "analytic_key_sha256": run.pair_digest(pairs),
              "country_roster": ["AAA", "BBB"]}
    real_read = run.pq.read_table
    seen = []

    def read_keys_only(*args, **kwargs):
        seen.append(kwargs.get("columns"))
        assert kwargs.get("columns") == ["country_iso3", "year"]
        return real_read(*args, **kwargs)

    monkeypatch.setattr(run.pq, "read_table", read_keys_only)
    assert run.preflight(tmp_path, roster) == pairs
    assert seen == [["country_iso3", "year"], ["country_iso3", "year"]]
    _source(treatment_path, [("AAA", 2000, 0.6), ("BBB", 2000, 0.1)])
    with pytest.raises(ValueError, match="byte hash differs"):
        run.preflight(tmp_path, roster)


@pytest.mark.parametrize(
    ("beta", "p", "loo", "expected"),
    [(-1.0, 0.01, [-1.0] * 30, "SUPPORTED"),
     (1.0, 0.01, [1.0] * 30, "REFUTED"),
     (-1.0, 0.2, [-1.0] * 30, "PARTIAL"),
     (-0.49, 0.001, [-1.0] * 30, "PARTIAL"),
     (0.49, 0.001, [1.0] * 30, "PARTIAL"),
     (-1.0, 0.01001, [-1.0] * 30, "PARTIAL"),
     (-1.0, 0.01, [-1.0] * 23 + [1.0] * 7, "PARTIAL")],
)
def test_symmetric_conservative_verdicts(beta: float, p: float, loo: list[float], expected: str) -> None:
    diag = {"complete_pairs": 500, "countries": 30, "tax_years": 25,
            "varying_countries": 20, "invalid_range_rows": 0,
            "full_rank": True, "influence_pass": True}
    assert run.classify(diag, {"coefficient": beta, "p_value": p}, loo) == expected
    diag["invalid_range_rows"] = 1
    assert run.classify(diag, {"coefficient": beta, "p_value": p}, loo) == "INCONCLUSIVE"


def test_same_commit_spec_and_lock_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    spec = repo / run.SPEC_REL
    spec.parent.mkdir(parents=True)
    spec.write_text(f"hypothesis_id: {run.DESIGN_ID}\nstatus: pre_registered\n")
    for relative in (run.ROSTER_REL, run.RUNNER_REL):
        companion = repo / relative
        companion.parent.mkdir(parents=True, exist_ok=True)
        companion.write_text("{}\n")
    lock = repo / run.LOCK_REL
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"design_id": run.DESIGN_ID}) + "\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "invalid same commit"], cwd=repo, check=True)
    monkeypatch.setattr(run, "ROOT", repo)
    with pytest.raises(ValueError, match="chronology is not strict"):
        run.verify_lock(repo, {"sources": {}, "analytic_key_sha256": "unused"})


def test_fixed_effects_fit_recovers_synthetic_negative_signal() -> None:
    rows = []
    for country_number in range(12):
        country = f"{country_number:03d}"
        for year in range(1990, 2015):
            tax = ((country_number * 7 + (year - 1990) * 11) % 37) / 20.0
            outcome = 40 + country_number / 3 + (year - 1990) / 7 - 2.0 * tax
            rows.append((country, year, tax, outcome))
    panel = pd.DataFrame(rows, columns=["country_iso3", "tax_year", "tax_receipts", "top1_share"])
    estimate = run.fit(panel)
    assert estimate["coefficient"] == pytest.approx(-2.0, abs=1e-8)
    assert estimate["p_value"] < 0.05
    assert estimate["reference_df"] == 11
    assert estimate["covariance"] == "CR1_country_cluster"


def test_cr1_standard_error_and_student_reference_match_independent_calculation() -> None:
    rows = []
    for country_number in range(12):
        country = f"{country_number:03d}"
        for year in range(1990, 2015):
            tax = ((country_number * 7 + (year - 1990) * 11) % 37) / 20.0
            noise = ((country_number * 13 + (year - 1990) * 17) % 19) / 12.0
            outcome = 40 + country_number / 3 + (year - 1990) / 7 - 2.0 * tax + noise
            rows.append((country, year, tax, outcome))
    panel = pd.DataFrame(rows, columns=["country_iso3", "tax_year", "tax_receipts", "top1_share"])
    estimate = run.fit(panel)
    reference = smf.ols("top1_share ~ tax_receipts + C(country_iso3) + C(tax_year)", data=panel).fit()
    term = list(reference.model.exog_names).index("tax_receipts")
    reference_se = float(cov_cluster(reference, panel.country_iso3, use_correction=True)[term, term] ** 0.5)
    reference_p = float(2 * student_t.sf(abs(reference.params["tax_receipts"] / reference_se), df=11))
    assert estimate["standard_error"] == pytest.approx(reference_se, rel=1e-8)
    assert estimate["p_value"] == pytest.approx(reference_p, rel=1e-8)


def test_full_rank_gate_rejects_absorbed_treatment() -> None:
    panel = pd.DataFrame({"country_iso3": ["AAA", "AAA", "BBB", "BBB"],
                          "tax_year": [2000, 2001, 2000, 2001],
                          "tax_receipts": [0.0, 0.0, 0.0, 0.0],
                          "top1_share": [10.0, 11.0, 12.0, 13.0]})
    with pytest.raises(ValueError, match="not full rank"):
        run.fit(panel)


def test_residualized_treatment_influence_detects_concentration() -> None:
    rows = []
    for country_number in range(30):
        country = f"{country_number:03d}"
        for year in range(2000, 2020):
            tax = ((country_number * 7 + (year - 2000) * 11) % 37) / 20.0
            if country_number == 0 and year == 2000:
                tax += 100.0
            rows.append((country, year, tax, 20.0))
    panel = pd.DataFrame(rows, columns=["country_iso3", "tax_year", "tax_receipts", "top1_share"])
    influence = run.residualized_treatment_influence(panel)
    assert not influence["passed"]
    assert influence["top_one_percent_rows"] > 0.2
    assert influence["top_country"] > 0.15


def test_standard_nine_artifacts_replay_byte_identically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    for relative, content in ((run.SPEC_REL, "status: pre_registered\n"),
                              (run.LOCK_REL, "{}\n"),
                              (run.ROSTER_REL, "{}\n"),
                              (run.RUNNER_REL, "# synthetic runner\n")):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    monkeypatch.setattr(run, "ROOT", repo)
    panel = pd.DataFrame({"country_iso3": ["AAA", "BBB"], "tax_year": [2000, 2000],
                          "tax_receipts": [0.1, 0.2], "top1_share": [10.0, 20.0]})
    diag = {"candidate_key_pairs": 2, "excluded_missing_or_nonfinite": 0,
            "complete_pairs": 2, "countries": 2, "tax_years": 1,
            "varying_countries": 0, "invalid_range_rows": 0}
    roster = {"analytic_key_sha256": "synthetic", "sources": {
        "treatment": {"path": "tax.parquet", "sha256": "a"},
        "outcome": {"path": "wealth.parquet", "sha256": "b"}}}
    first, second = tmp_path / "first", tmp_path / "second"
    for target in (first, second):
        run.emit(target, panel, diag, None, [], "INCONCLUSIVE", roster, "spec", "lock")
    assert sorted(path.name for path in first.iterdir()) == sorted(run.ARTIFACTS)
    assert {_sha(first / name) for name in run.ARTIFACTS} == {_sha(second / name) for name in run.ARTIFACTS}
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in run.ARTIFACTS)
