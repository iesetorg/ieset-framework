#!/usr/bin/env python3
"""Frozen, source-locked JST mortgage-share housing/crisis family (8 descriptive cells).

Only plan/source-lock read source keys and Parquet schema. Selected measurements
are opened only after the registration and all 8 metadata locks are committed.
No JST source rows, country effects, or country-level outcome values are saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "jst_mortgage_share_future_housing_crisis_four_eras_2026_10_10"
ERAS = {
    "1890_1910": (1890, 1895, 1900, 1905),
    "1950_1970": (1950, 1955, 1960, 1965),
    "1975_1995": (1975, 1980, 1985, 1990),
    "2000_2020": (2000, 2005, 2010, 2015),
}
OUTCOMES = {
    "real_house_price_growth": {"field": "hpnom,cpi", "topic": "housing", "sign": 1,
                     "unit": "annualized log percentage points"},
    "crisis_onset": {"field": "crisisjst", "topic": "regulatory", "sign": 1,
                     "unit": "percentage-point onset probability"},
}
CELLS = tuple((era, outcome) for era in ERAS for outcome in OUTCOMES)
IDS = tuple(f"jst_mortgage_share_{era}_{outcome}_2026" for era, outcome in CELLS)
TOPICS = tuple(OUTCOMES[outcome]["topic"] for _, outcome in CELLS)
COUNTRIES = ("AUS", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
             "GBR", "IRL", "ITA", "JPN", "NLD", "NOR", "PRT", "SWE", "USA")
YEARS = tuple(sorted({year for anchors in ERAS.values() for t in anchors
                      for year in range(t, t + 6)}))
EXPECTED_KEYS = {(country, year) for country in COUNTRIES for year in YEARS}
SOURCE_COLUMNS = ("country_iso3", "year", "tmort", "tloans", "hpnom", "cpi", "crisisjst")
SOURCE_BASENAME = "jst_macrohistory@2026-05-05T195309Z.parquet"
SOURCE_DEFAULT = ROOT / "data/vintages/jst" / SOURCE_BASENAME
SOURCE_SHA256 = "4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f"
SOURCE_URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
DOC_URL = "https://www.macrohistory.net/database/"
PLAN_REL = "engine/audits/jst_mortgage_share_source_plan_2026.md"
RUNNER_REL = "scripts/run_jst_mortgage_share_2026.py"
SPEC_RELS = tuple(f"hypotheses/{topic}/{hid}.yaml" for topic, hid in zip(TOPICS, IDS))
STEELMAN_RELS = tuple(f"hypotheses/steelman/{hid}.md" for hid in IDS)
LOCK_RELS = tuple(f"data/pinned_evidence/{hid}.source.json" for hid in IDS)
RESULT_RELS = tuple(f"engine/runs/{hid}/diagnostics.json" for hid in IDS)
PACKET_NAMES = ("diagnostics.json", "hypothesis.yaml", "manifest.yaml",
                "evidence_packet.yaml", "result_card.md", "replication.py")
REGISTRATION_FILES = SPEC_RELS + STEELMAN_RELS + (PLAN_REL, RUNNER_REL)
GATES = {
    "family_size": 8,
    "holm_alpha": 0.05,
    "minimum_abs_beta_outcome_pp_per_mortgage_pp": 0.25,
    "minimum_countries": 12,
    "minimum_country_anchors": 48,
    "minimum_anchors_per_country": 3,
    "minimum_countries_per_anchor": 10,
    "minimum_residual_mortgage_sd_pp": 1.0,
    "minimum_residual_outcome_sd_pp": 0.1,
    "maximum_country_mortgage_ss_share": 0.25,
    "minimum_crisis_event_intervals": 6,
    "minimum_crisis_nonevent_intervals": 20,
}
assert len(IDS) == 8 and len(YEARS) == 84 and len(EXPECTED_KEYS) == 1512

def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result


def git_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).stdout.decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}, got {len(commits)}")
    return commits[0]


def strict_ancestor(earlier: str, later: str) -> bool:
    return earlier != later and git("merge-base", "--is-ancestor", earlier, later, check=False).returncode == 0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def yaml_bytes(value: Any) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode()


def registration_commit() -> str:
    commits = {first_addition(relative) for relative in REGISTRATION_FILES}
    if len(commits) != 1:
        raise RuntimeError("all 8 specs, steelmans, plan, and runner must share their first commit")
    commit = commits.pop()
    schema = json.loads(git_bytes(commit, "schemas/hypothesis.schema.json"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for relative in REGISTRATION_FILES:
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"frozen registration changed after first commit: {relative}")
    for relative in SPEC_RELS:
        spec = yaml.safe_load(git_bytes(commit, relative))
        if not isinstance(spec, dict) or not validator.is_valid(spec):
            raise RuntimeError(f"first-commit registration failed its historical schema: {relative}")
    if git("ls-tree", "-r", "--name-only", commit, "--", *LOCK_RELS, *RESULT_RELS).stdout.strip():
        raise RuntimeError("source lock or result appeared in registration commit")
    return commit


def source_check(path: Path) -> dict[str, str]:
    if not path.is_file() or sha256_file(path) != SOURCE_SHA256:
        raise RuntimeError("exact local JST R6 source unavailable or SHA-256 mismatch")
    schema = pq.ParquetFile(path).schema_arrow
    missing = set(SOURCE_COLUMNS) - set(schema.names)
    if missing:
        raise RuntimeError(f"JST source lacks frozen columns: {sorted(missing)}")
    return {field: str(schema.field(field).type) for field in SOURCE_COLUMNS}


def source_key_check(path: Path) -> dict[str, Any]:
    """No treatment/outcome values or their missingness are read here."""
    schema = source_check(path)
    table = pq.read_table(path, columns=["country_iso3", "year"])
    selected = [(str(c), int(y)) for c, y in zip(table["country_iso3"].to_pylist(), table["year"].to_pylist())
                if c in COUNTRIES and y in YEARS]
    if len(selected) != len(EXPECTED_KEYS) or set(selected) != EXPECTED_KEYS or len(set(selected)) != len(selected):
        raise RuntimeError("fixed 18-country x 84-year source-key roster missing or duplicated")
    roster = "".join(f"{c},{y}\n" for c, y in sorted(selected)).encode()
    return {"selected_key_count": len(selected),
            "key_roster_sha256": hashlib.sha256(roster).hexdigest(),
            "selected_schema": schema}


def write_lock(path: Path, hypothesis_id: str) -> None:
    registration = registration_commit()
    index = IDS.index(hypothesis_id)
    relative = LOCK_RELS[index]
    if (ROOT / relative).exists():
        raise RuntimeError("source lock exists; immutable custody forbids overwrite")
    expected_head = registration if index == 0 else first_addition(LOCK_RELS[index - 1])
    if git("rev-parse", "HEAD").stdout.decode().strip() != expected_head:
        raise RuntimeError("source locks must be committed in frozen order, one per commit")
    info = source_key_check(path)
    lock = {
        "hypothesis_id": hypothesis_id, "family_id": FAMILY, "family_size": len(IDS),
        "registration_commit": registration,
        "publisher": "Jordà-Schularick-Taylor Macrohistory Database", "release": "R6",
        "official_source_url": SOURCE_URL, "documentation_url": DOC_URL,
        "citation": "Jordà, Schularick and Taylor (2017), Macrofinancial History and the New Business Cycle Facts",
        "license": "CC BY-NC-SA 4.0; no source or country-level values committed",
        "source_basename": SOURCE_BASENAME, "source_sha256": SOURCE_SHA256,
        "source_bytes": path.stat().st_size,
        "fetch_manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "countries": list(COUNTRIES), "years": list(YEARS),
        "era": CELLS[index][0], "outcome": CELLS[index][1],
        "contains_source_values": False, **info,
    }
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_json(lock))
    print(json.dumps({"lock": relative, "registration_commit": registration,
                      "key_roster_sha256": info["key_roster_sha256"]}, sort_keys=True))


def committed_locks(registration: str, path: Path) -> tuple[list[str], dict[str, Any]]:
    info = source_key_check(path)
    commits: list[str] = []
    for index, relative in enumerate(LOCK_RELS):
        local = ROOT / relative
        if not local.is_file():
            raise RuntimeError(f"missing metadata source lock: {relative}")
        commit = first_addition(relative)
        earlier = registration if not commits else commits[-1]
        if not strict_ancestor(earlier, commit):
            raise RuntimeError("source-lock chronology invalid")
        if git_bytes(commit, relative) != local.read_bytes():
            raise RuntimeError(f"committed source lock changed: {relative}")
        changes = git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.decode().splitlines()
        if changes != [relative]:
            raise RuntimeError(f"source-lock commit must contain exactly one file: {relative}")
        lock = json.loads(local.read_text())
        expected = {"hypothesis_id": IDS[index], "family_id": FAMILY,
                    "family_size": len(IDS), "registration_commit": registration,
                    "source_sha256": SOURCE_SHA256, **info}
        if any(lock.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"source-lock identity or metadata mismatch: {relative}")
        commits.append(commit)
    if git("ls-tree", "-r", "--name-only", commits[-1], "--", *RESULT_RELS).stdout.strip():
        raise RuntimeError("results predate final source lock")
    return commits, info


def selected_rows(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Only run/verify calls this, after every committed source lock validates."""
    table = pq.read_table(path, columns=list(SOURCE_COLUMNS))
    values = [table[name].to_pylist() for name in SOURCE_COLUMNS]
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for record in zip(*values):
        c, year = record[:2]
        if c in COUNTRIES and year in YEARS:
            key = (str(c), int(year))
            if key in rows:
                raise RuntimeError("duplicate selected JST source key")
            rows[key] = dict(zip(SOURCE_COLUMNS[2:], record[2:]))
    if set(rows) != EXPECTED_KEYS:
        raise RuntimeError("selected JST key roster changed")
    return rows


def finite(value: Any) -> bool:
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def cell_rows(source: dict[tuple[str, int], dict[str, Any]], era: str,
              outcome: str) -> list[tuple[str, int, float, float]]:
    rows: list[tuple[str, int, float, float]] = []
    for country in COUNTRIES:
        for anchor in ERAS[era]:
            start = source[(country, anchor)]
            end = source[(country, anchor + 5)]
            mortgage, loans = start["tmort"], start["tloans"]
            if not finite(mortgage) or not finite(loans) or loans <= 0:
                continue
            share = mortgage / loans
            if not math.isfinite(share) or not (0 <= share <= 1):
                continue
            if outcome == "crisis_onset":
                incident = [source[(country, year)]["crisisjst"]
                            for year in range(anchor + 1, anchor + 6)]
                if any(not finite(value) or value not in (0, 1) for value in incident):
                    continue
                response = 100.0 * float(any(value == 1 for value in incident))
            else:
                p0, p1, c0, c1 = start["hpnom"], end["hpnom"], start["cpi"], end["cpi"]
                if any(not finite(value) or value <= 0 for value in (p0, p1, c0, c1)):
                    continue
                response = 20.0 * math.log((p1 / c1) / (p0 / c0))
            mortgage_share = 100.0 * share
            if math.isfinite(response):
                rows.append((country, anchor, mortgage_share, response))
    return rows

def design(rows: list[tuple[str, int, float, float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    countries = sorted({row[0] for row in rows})
    anchors = sorted({row[1] for row in rows})
    n = len(rows)
    fixed = np.ones((n, 1 + len(countries) - 1 + len(anchors) - 1), dtype=float)
    for i, (country, anchor, _, _) in enumerate(rows):
        fixed[i, 1:1 + len(countries) - 1] = [float(country == c) for c in countries[1:]]
        fixed[i, len(countries):] = [float(anchor == a) for a in anchors[1:]]
    x = np.array([row[2] for row in rows], dtype=float)
    y = np.array([row[3] for row in rows], dtype=float)
    return fixed, x, y, np.array([countries.index(row[0]) for row in rows]), countries


def slope(rows: list[tuple[str, int, float, float]], full: bool = True) -> dict[str, float] | None:
    fixed, x, y, country_ids, countries = design(rows)
    matrix = np.column_stack((fixed[:, 0], x, fixed[:, 1:]))
    n, k = matrix.shape
    if n <= k or np.linalg.matrix_rank(matrix) != k:
        return None
    beta, _, _, _ = np.linalg.lstsq(matrix, y, rcond=None)
    out = {"beta": float(beta[1])}
    if not full:
        return out
    x_resid = x - fixed @ np.linalg.lstsq(fixed, x, rcond=None)[0]
    y_resid = y - fixed @ np.linalg.lstsq(fixed, y, rcond=None)[0]
    x_ss = float(x_resid @ x_resid)
    shares = [float(x_resid[country_ids == g] @ x_resid[country_ids == g]) / x_ss
              for g in range(len(countries))] if x_ss > 0 else [float("inf")]
    residual = y - matrix @ beta
    inv = np.linalg.inv(matrix.T @ matrix)
    meat = np.zeros((k, k), dtype=float)
    for group in range(len(countries)):
        index = country_ids == group
        score = matrix[index].T @ residual[index]
        meat += np.outer(score, score)
    g = len(countries)
    variance = (g / (g - 1)) * ((n - 1) / (n - k)) * (inv @ meat @ inv)[1, 1] if g > 1 else float("nan")
    se = math.sqrt(variance) if math.isfinite(variance) and variance > 0 else float("nan")
    p = float(2 * student_t.sf(abs(out["beta"] / se), g - 1)) if math.isfinite(se) else float("nan")
    out.update({"cluster_se": se, "p_two_sided": p,
                "residual_mortgage_sd_pp": float(np.std(x_resid, ddof=1)),
                "residual_outcome_sd_pp": float(np.std(y_resid, ddof=1)),
                "maximum_country_mortgage_ss_share": max(shares)})
    return out


def evaluate(source: dict[tuple[str, int], dict[str, Any]], era: str, outcome: str) -> dict[str, Any]:
    raw = cell_rows(source, era, outcome)
    counts = {country: sum(row[0] == country for row in raw) for country in COUNTRIES}
    rows = [row for row in raw if counts[row[0]] >= GATES["minimum_anchors_per_country"]]
    countries = sorted({row[0] for row in rows})
    anchor_counts = {str(anchor): sum(row[1] == anchor for row in rows) for anchor in ERAS[era]}
    result: dict[str, Any] = {
        "verdict": "INCONCLUSIVE", "gate_failures": [],
        "candidate_country_anchors": len(COUNTRIES) * len(ERAS[era]),
        "complete_country_anchors": len(rows), "complete_countries": len(countries),
        "anchor_counts": anchor_counts, "crisis_event_intervals": None,
        "crisis_nonevent_intervals": None, "beta": None, "country_cluster_se": None,
        "p_two_sided": None, "holm_adjusted_p": None,
        "residual_mortgage_sd_pp": None, "residual_outcome_sd_pp": None,
        "maximum_country_mortgage_ss_share": None,
        "leave_one_country_out_beta_min": None, "leave_one_country_out_beta_max": None,
    }
    failures = result["gate_failures"]
    if len(countries) < GATES["minimum_countries"]:
        failures.append("country_floor")
    if len(rows) < GATES["minimum_country_anchors"]:
        failures.append("country_anchor_floor")
    if any(count < GATES["minimum_countries_per_anchor"] for count in anchor_counts.values()):
        failures.append("anchor_floor")
    if outcome == "crisis_onset":
        events = sum(row[3] == 100.0 for row in rows)
        nonevents = len(rows) - events
        result["crisis_event_intervals"] = events
        result["crisis_nonevent_intervals"] = nonevents
        if events < GATES["minimum_crisis_event_intervals"]:
            failures.append("crisis_event_floor")
        if nonevents < GATES["minimum_crisis_nonevent_intervals"]:
            failures.append("crisis_nonevent_floor")
    if failures:
        return result
    fit = slope(rows)
    if fit is None:
        failures.append("rank_or_residual_df_failure")
        return result
    for key in ("beta", "cluster_se", "p_two_sided", "residual_mortgage_sd_pp",
                "residual_outcome_sd_pp", "maximum_country_mortgage_ss_share"):
        if not math.isfinite(fit[key]):
            failures.append("nonfinite_model_statistic")
            return result
    result.update({"beta": fit["beta"], "country_cluster_se": fit["cluster_se"],
                   "p_two_sided": fit["p_two_sided"],
                   "residual_mortgage_sd_pp": fit["residual_mortgage_sd_pp"],
                   "residual_outcome_sd_pp": fit["residual_outcome_sd_pp"],
                   "maximum_country_mortgage_ss_share": fit["maximum_country_mortgage_ss_share"]})
    if fit["residual_mortgage_sd_pp"] < GATES["minimum_residual_mortgage_sd_pp"]:
        failures.append("exposure_variation_floor")
    if fit["residual_outcome_sd_pp"] < GATES["minimum_residual_outcome_sd_pp"]:
        failures.append("outcome_variation_floor")
    if fit["maximum_country_mortgage_ss_share"] > GATES["maximum_country_mortgage_ss_share"]:
        failures.append("country_exposure_concentration")
    loo: list[float] = []
    for country in countries:
        reduced = slope([row for row in rows if row[0] != country], full=False)
        if reduced is None or not math.isfinite(reduced["beta"]):
            failures.append("country_deletion_fit_failure")
            break
        loo.append(reduced["beta"])
    if len(loo) == len(countries):
        result["leave_one_country_out_beta_min"] = min(loo)
        result["leave_one_country_out_beta_max"] = max(loo)
    return result


def holm_adjusted(p_values: list[float | None]) -> list[float]:
    """Fixed 8-test Holm family; an inconclusive test retains p=1."""
    assert len(p_values) == len(IDS)
    ordered = sorted(range(len(p_values)), key=lambda i: 1.0 if p_values[i] is None else p_values[i])
    adjusted = [1.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(ordered):
        p = 1.0 if p_values[index] is None else p_values[index]
        running = max(running, min(1.0, (len(p_values) - rank) * p))
        adjusted[index] = running
    return adjusted


def measured_results(path: Path) -> list[dict[str, Any]]:
    registration = registration_commit()
    locks, info = committed_locks(registration, path)
    source = selected_rows(path)
    evaluated = [evaluate(source, era, outcome) for era, outcome in CELLS]
    adjusted = holm_adjusted([row["p_two_sided"] if not row["gate_failures"] else None
                              for row in evaluated])
    diagnostics = []
    for index, ((era, outcome), hypothesis_id) in enumerate(zip(CELLS, IDS)):
        result = evaluated[index]
        result["holm_adjusted_p"] = adjusted[index]
        if not result["gate_failures"]:
            direction = OUTCOMES[outcome]["sign"]
            beta = direction * result["beta"]
            loo = (result["leave_one_country_out_beta_min"], result["leave_one_country_out_beta_max"])
            signed_loo = [direction * value for value in loo]
            threshold = GATES["minimum_abs_beta_outcome_pp_per_mortgage_pp"]
            if (beta >= threshold and adjusted[index] <= GATES["holm_alpha"]
                    and min(signed_loo) > 0):
                result["verdict"] = "SUPPORTED"
            elif (beta <= -threshold and adjusted[index] <= GATES["holm_alpha"]
                    and max(signed_loo) < 0):
                result["verdict"] = "REFUTED"
            else:
                result["verdict"] = "PARTIAL"
        diagnostics.append({
            "hypothesis_id": hypothesis_id, "family_id": FAMILY, "family_size": len(IDS),
            "family_members": list(IDS), "era": era, "anchors": list(ERAS[era]),
            "outcome": outcome, "outcome_field": OUTCOMES[outcome]["field"],
            "outcome_unit": OUTCOMES[outcome]["unit"], "predicted_sign": OUTCOMES[outcome]["sign"],
            "registration_commit": registration, "source_lock_commit": locks[index],
            "source_sha256": SOURCE_SHA256,
            "source_key_roster_sha256": info["key_roster_sha256"],
            "thresholds": GATES, "result": result,
            "credit_boundary": "One correlated descriptive mortgage-share family; no causal, policy, school, position, or featured credit; no independent replication claim",
            "source_citation": "Jordà, Schularick and Taylor (2017), JST Macrohistory R6; CC BY-NC-SA 4.0",
        })
    return diagnostics


def packet_files(diagnostic: dict[str, Any], spec_bytes: bytes) -> dict[str, bytes]:
    hypothesis_id = diagnostic["hypothesis_id"]
    index = IDS.index(hypothesis_id)
    run_rel = f"engine/runs/{hypothesis_id}"
    result = diagnostic["result"]
    verdict = result["verdict"]
    source = {
        "publisher": "Jordà-Schularick-Taylor Macrohistory Database", "release": "R6",
        "source_url": SOURCE_URL, "documentation_url": DOC_URL,
        "source_sha256": SOURCE_SHA256, "source_lock_manifest": LOCK_RELS[index],
        "source_lock_commit": diagnostic["source_lock_commit"],
        "key_roster_sha256": diagnostic["source_key_roster_sha256"],
        "license": "CC BY-NC-SA 4.0; local licensed source required; no raw or country-level values redistributed",
        "contains_source_values": False,
    }
    family = {"id": FAMILY, "size": len(IDS), "members": list(IDS),
              "holm_alpha": GATES["holm_alpha"],
              "interpretation": "Eight correlated cells across one source and four disjoint eras; one substantive family, not independent replication"}
    correction = {"disposition": "descriptive_calibration_only",
                  "school_score_eligible": False, "school_score_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0}
    diag_bytes = canonical_json(diagnostic)
    manifest = {
        "hypothesis_id": hypothesis_id, "run_date": "2026-10-10", "status": verdict,
        "runner": RUNNER_REL, "hypothesis_snapshot": f"{run_rel}/hypothesis.yaml",
        "preregistration_commit": diagnostic["registration_commit"],
        "source": source, "family": family, "correction": correction,
        "outputs": {"diagnostics": f"{run_rel}/diagnostics.json",
                    "result_card": f"{run_rel}/result_card.md"},
    }
    packet = {
        "packet_version": 1,
        "hypothesis": {"id": hypothesis_id, "path": SPEC_RELS[index]},
        "preregistration": {"commit": diagnostic["registration_commit"],
                            "steelman": STEELMAN_RELS[index], "source_plan": PLAN_REL,
                            "frozen_hypothesis_snapshot": f"{run_rel}/hypothesis.yaml"},
        "source": source, "family": family,
        "reproduction": {"runner": RUNNER_REL,
                         "command": "python3 scripts/run_jst_mortgage_share_2026.py verify --source-parquet <local-JST-R6-parquet>",
                         "result_sha256": hashlib.sha256(diag_bytes).hexdigest()},
        "gate": {"source_country_year_keys": len(EXPECTED_KEYS),
                 "country_roster": list(COUNTRIES), "era": diagnostic["era"],
                 "anchors": diagnostic["anchors"], "thresholds": GATES},
        "result": result,
        "scope_boundary": "Advanced-economy predictive association only; no causal policy, school, position, or featured credit",
        "correction": correction,
    }
    beta = result["beta"]
    estimate = "unavailable after frozen gate failure" if beta is None else f"{beta:.4f} outcome pp per 1 pp mortgage share"
    p = result["p_two_sided"]
    p_text = "not estimated" if p is None else f"{p:.6g} (Holm adjusted {result['holm_adjusted_p']:.6g})"
    card = (
        f"# {hypothesis_id}\n\n"
        f"**Measured verdict: {verdict}.** This is one cell in an 8-test descriptive JST mortgage-share family. "
        f"It grants no causal, policy, school, position, or featured credit.\n\n"
        f"Period: {diagnostic['era']}; anchors: {', '.join(map(str, diagnostic['anchors']))}. "
        f"The exposure is 100 times JST mortgage loans divided by all nonfinancial private loans at each anchor. "
        f"The outcome is {diagnostic['outcome']} over the next five years. "
        f"Complete sample: {result['complete_countries']} countries and "
        f"{result['complete_country_anchors']} country-anchor intervals.\n\n"
        f"Country-and-anchor fixed-effect slope: **{estimate}**. "
        f"Two-sided country-cluster p-value: **{p_text}**. "
        f"Gate failures: **{', '.join(result['gate_failures']) if result['gate_failures'] else 'none'}**.\n\n"
        "The two outcomes use distinct fields but share countries and one source. The four eras use separate "
        "year windows. This is one substantive family, not 8 independent replications. "
        "Mortgage composition may respond to housing booms and lending rules; the association cannot identify a mortgage-policy intervention.\n\n"
        f"Registration: `{diagnostic['registration_commit']}`. "
        f"Metadata source lock: `{diagnostic['source_lock_commit']}`. "
        "Source: JST Macrohistory Database R6, https://www.macrohistory.net/database/ ; "
        "Jordà, Schularick and Taylor (2017), *Macrofinancial History and the New Business Cycle Facts*. "
        "Licensed CC BY-NC-SA 4.0. Raw and country-level values are not committed.\n"
    )
    replication = (
        "#!/usr/bin/env python3\n"
        '"""Exact replay of the frozen 8-cell JST family; supply lawful local parquet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        f"runner = Path(__file__).resolve().parents[3] / {RUNNER_REL!r}\n"
        "raise SystemExit(subprocess.call([sys.executable, str(runner), 'verify', *sys.argv[1:]]))\n"
    )
    return {"diagnostics.json": diag_bytes, "hypothesis.yaml": spec_bytes,
            "manifest.yaml": yaml_bytes(manifest), "evidence_packet.yaml": yaml_bytes(packet),
            "result_card.md": card.encode(), "replication.py": replication.encode()}


def expected_packets(path: Path) -> dict[str, dict[str, bytes]]:
    diagnostics = measured_results(path)
    return {diagnostic["hypothesis_id"]: packet_files(diagnostic, (ROOT / SPEC_RELS[index]).read_bytes())
            for index, diagnostic in enumerate(diagnostics)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "source-lock", "run", "verify"))
    parser.add_argument("--source-parquet", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--id", choices=IDS)
    args = parser.parse_args()
    if args.command == "plan":
        print(canonical_json(source_key_check(args.source_parquet)).decode(), end="")
    elif args.command == "source-lock":
        if args.id is None:
            parser.error("--id is required for source-lock")
        write_lock(args.source_parquet, args.id)
    elif args.command == "run":
        if any((ROOT / relative).exists() for relative in RESULT_RELS):
            raise RuntimeError("a family result already exists; never overwrite")
        packets = expected_packets(args.source_parquet)
        for hypothesis_id, files in packets.items():
            target = ROOT / "engine/runs" / hypothesis_id
            target.mkdir(parents=True, exist_ok=True)
            for name, payload in files.items():
                (target / name).write_bytes(payload)
            print(json.dumps({"result": f"engine/runs/{hypothesis_id}/diagnostics.json",
                              "verdict": json.loads(files["diagnostics.json"])["result"]["verdict"],
                              "sha256": hashlib.sha256(files["diagnostics.json"]).hexdigest()}, sort_keys=True))
    else:
        registration = registration_commit()
        locks, _ = committed_locks(registration, args.source_parquet)
        additions = {first_addition(relative) for relative in RESULT_RELS}
        if len(additions) != 1:
            raise RuntimeError("all family results must first appear in one result commit")
        run_commit = additions.pop()
        if not strict_ancestor(locks[-1], run_commit):
            raise RuntimeError("result predates final source lock")
        packets = expected_packets(args.source_parquet)
        for hypothesis_id, files in packets.items():
            for name, payload in files.items():
                relative = f"engine/runs/{hypothesis_id}/{name}"
                target = ROOT / relative
                if not target.is_file() or target.read_bytes() != payload or git_bytes(run_commit, relative) != payload:
                    raise RuntimeError(f"exact replay mismatch: {relative}")
            print(json.dumps({"verified": True, "hypothesis_id": hypothesis_id,
                              "sha256": hashlib.sha256(files["diagnostics.json"]).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
