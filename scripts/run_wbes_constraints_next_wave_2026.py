#!/usr/bin/env python3
"""Frozen eight-cell WBES country-aggregate next-wave descriptive family.

--lock-case checks committed registration and source hashes without parsing
selected value, N, or missingness fields. Commit each case lock separately.
--run/--verify only parse those fields after all eight source locks exist.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_wbes_constraints_next_wave_2026.py"
FAMILY = "wbes_constraints_next_wave_growth_2026_10_10"
PREREG = "engine/audits/wbes_constraints_next_wave_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wbes_constraints_next_wave_2026_key_roster.csv"
ROSTER_SHA = "1376c8b28f3e6541f42239b21dc3a62d93f2b8adccc55238027181a599b1df78"
SOURCE_MANIFEST = "data/pinned_evidence/wbes_aggregate_2024_source_manifest.yaml"
SOURCE_MANIFEST_SHA = "350236e2e73e0560ece000b871962bc5f79bc06383eaf4e04e43b846a388887f"
SELECTOR = {"cut": "All", "subcut": "All", "method": "Global", "sector_MS": ""}
CONSTRAINTS = {
    "electricity": ("in12", "electricity_obstacle"),
    "finance": ("fin16", "finance_obstacle"),
    "bribery": ("graft3", "bribery_incidence"),
    "regulatory_time": ("reg1", "regulatory_management_time"),
}
OUTCOMES = {
    "sales": ("perf1", "sales_growth", "growth"),
    "employment": ("perf2", "employment_growth", "labour"),
}
CASES = {
    f"{treatment}_{outcome}": (topic, f"wbes_{slug}_{out_slug}_next_wave_2026", code, out_code)
    for treatment, (code, slug) in CONSTRAINTS.items()
    for outcome, (out_code, out_slug, topic) in OUTCOMES.items()
}
MEMBERS = sorted(item[1] for item in CASES.values())
SOURCE_FILES = {
    "aggregate": {
        "path": "data/vintages/world_bank_enterprise/indicators_long_view_November_11_2024.csv",
        "sha256": "bb3155ee0093c2833878b16e5f3587afa97b536ab3db0a893a8b870113d2b920",
        "source_url": "https://datacatalogfiles.worldbank.org/ddh-published-v2/0037947/5/DR0094302/indicators_long_view_November_11_2024.csv",
        "manifest": SOURCE_MANIFEST, "manifest_sha256": SOURCE_MANIFEST_SHA,
    },
    "codebook": {
        "path": "data/vintages/world_bank_enterprise/Indicator_and_Topic_Names_2024.xls",
        "sha256": "6a7eab2649b80283960778194d053ad32b90685a710f91080c72de34c1d10bef",
        "source_url": "https://datacatalogfiles.worldbank.org/ddh-published-v2/0037947/5/DR0094304/Indicator%20and%20Topic%20Names.xls",
        "manifest": SOURCE_MANIFEST, "manifest_sha256": SOURCE_MANIFEST_SHA,
    },
}
SOURCE_SHA = hashlib.sha256(json.dumps(SOURCE_FILES, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
LIMITATIONS = [
    "Public country aggregates describe changing cross-sectional samples of registered formal firms with at least five workers, not tracked firms.",
    "Baseline constraints and later retrospective growth can reflect country shocks, endogenous responses, selection, and survey-composition changes.",
    "The August 2022 ISIC Rev.4 eligibility expansion can affect comparability; the 4-year minimum survey gap does not certify exact fiscal-period separation.",
    "Four constraint measures and two growth outcomes are correlated; eight records are not independent experiments and the family correction is local.",
    "This retrospective family follows prior IESET work and the source scout saw isolated official search snippets; there is no independent external holdout.",
    "No causal, policy, school, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return result.stdout


def first_addition(rel: str) -> str:
    revisions = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", rel).decode().splitlines()
    if len(revisions) != 1:
        raise RuntimeError("missing or ambiguous first addition: " + rel)
    return revisions[0]


def require_unchanged(rel: str, revision: str) -> None:
    if (ROOT / rel).read_bytes() != git("show", revision + ":" + rel):
        raise RuntimeError("frozen bytes differ from first addition: " + rel)
    if git("status", "--porcelain", "--", rel).strip():
        raise RuntimeError("uncommitted frozen path: " + rel)


def spec_rel(role: str) -> str:
    topic, hid, _, _ = CASES[role]
    return f"hypotheses/{topic}/{hid}.yaml"


def run_rel(role: str) -> str:
    return "engine/runs/" + CASES[role][1]


def lock_rel(role: str) -> str:
    return "data/pinned_evidence/" + CASES[role][1] + ".source.json"


def registration_commit() -> str:
    paths = [PREREG, ROSTER, SOURCE_MANIFEST] + [spec_rel(role) for role in CASES]
    commits = {first_addition(rel) for rel in paths}
    if len(commits) != 1:
        raise RuntimeError("family registration artifacts not in one first commit")
    commit = commits.pop()
    for rel in paths:
        require_unchanged(rel, commit)
    return commit


def load_specs() -> dict[str, dict]:
    specs = {}
    for role, (_, hid, code, outcome) in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(role)).read_text())
        threshold = spec["falsification"]["threshold"]
        if (spec["hypothesis_id"] != hid or spec["falsification"]["test"] != FAMILY
                or threshold.get("family_id") != FAMILY or threshold.get("family_size") != 8
                or threshold.get("family_alpha") != 0.01
                or threshold.get("p_max_two_sided_bonferroni") != 0.00125
                or threshold.get("key_roster_sha256") != ROSTER_SHA
                or threshold.get("source_files") != SOURCE_FILES
                or spec["variables"]["treatment"][0]["source"] != "world_bank_enterprise:" + code
                or spec["variables"]["outcome"][0]["source"] != "world_bank_enterprise:" + outcome):
            raise RuntimeError("case registration differs from frozen contract: " + role)
        specs[role] = spec
    return specs


def load_roster(specs: dict[str, dict]) -> list[tuple[str, int, int, int]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("key-roster SHA-256 mismatch")
    rows = [(r["country_iso3"], int(r["exposure_year"]), int(r["outcome_year"]), int(r["gap_years"]))
            for r in csv.DictReader(io.StringIO(path.read_text()))]
    if len(rows) != len(set(rows)) or rows != sorted(rows):
        raise RuntimeError("key roster duplicated or not sorted")
    if len(rows) != 114 or len({r[0] for r in rows}) != 49:
        raise RuntimeError("key-roster denominator differs from registration")
    counts = Counter(r[0] for r in rows)
    if any(count < 2 for count in counts.values()):
        raise RuntimeError("key roster has country with fewer than two intervals")
    by_country = defaultdict(list)
    for country, first, later, gap in rows:
        if (len(country) != 3 or not 2006 <= first < later <= 2024 or later - first != gap
                or not 4 <= gap <= 10):
            raise RuntimeError("invalid key-roster row")
        by_country[country].append((first, later))
    for intervals in by_country.values():
        for (_, prior_later), (next_first, _) in zip(intervals, intervals[1:]):
            if prior_later != next_first:
                raise RuntimeError("roster intervals are not adjacent survey waves")
    for spec in specs.values():
        threshold = spec["falsification"]["threshold"]
        if threshold["expected_key_rows"] != len(rows) or threshold["expected_key_countries"] != len(counts):
            raise RuntimeError("case key-roster count mismatch")
    return rows


def source_metadata(source_root: Path) -> dict[str, dict]:
    manifest_path = ROOT / SOURCE_MANIFEST
    if sha256(manifest_path) != SOURCE_MANIFEST_SHA:
        raise RuntimeError("tracked WBES source manifest hash mismatch")
    manifest = yaml.safe_load(manifest_path.read_text())
    if (manifest.get("publisher") != "world_bank_enterprise"
            or manifest.get("license") != "CC BY 4.0"
            or manifest.get("selector") != SELECTOR
            or manifest.get("indicator_codes") != {
                "electricity": "in12", "credit": "fin16", "bribery": "graft3",
                "regulatory_time": "reg1", "sales_growth": "perf1", "employment_growth": "perf2",
            }):
        raise RuntimeError("WBES source manifest metadata changed")
    checked = {}
    for role, item in SOURCE_FILES.items():
        path = source_root / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise RuntimeError("missing or mismatched pinned WBES file: " + role)
        if manifest["files"].get(role) != {k: item[k] for k in ("path", "sha256", "source_url")}:
            raise RuntimeError("WBES manifest entry changed: " + role)
        checked[role] = {**item, "publisher": "world_bank_enterprise", "license": "CC BY 4.0",
                         "attribution": "World Bank Enterprise Surveys"}
    return checked


def write_case_lock(role: str, source_root: Path) -> None:
    registration = registration_commit()
    specs = load_specs()
    load_roster(specs)
    sources = source_metadata(source_root)  # hashes bytes; does not parse value/N fields
    runner_commit = first_addition(RUNNER)
    require_unchanged(RUNNER, runner_commit)
    if subprocess.run(["git", "merge-base", "--is-ancestor", registration, runner_commit], cwd=ROOT).returncode:
        raise RuntimeError("runner does not follow preregistration")
    path = ROOT / lock_rel(role)
    if path.exists():
        raise RuntimeError("case source lock already exists: " + role)
    lock = {
        "schema": "ieset-source-lock-v1", "hypothesis_id": specs[role]["hypothesis_id"],
        "family_id": FAMILY, "family_size": len(CASES), "registration_commit": registration,
        "runner_commit": runner_commit, "runner_sha256": sha256(ROOT / RUNNER),
        "source_sha256": SOURCE_SHA, "key_roster_sha256": ROSTER_SHA, "sources": sources,
    }
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    print("wrote " + lock_rel(role) + "; commit this source lock alone")


def verify_locks(source_root: Path, specs: dict[str, dict]) -> dict[str, str]:
    registration = registration_commit()
    require_unchanged(RUNNER, first_addition(RUNNER))
    sources = source_metadata(source_root)
    commits = {}
    for role in CASES:
        rel = lock_rel(role)
        revision = first_addition(rel)
        require_unchanged(rel, revision)
        if registration == revision or subprocess.run(
            ["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT
        ).returncode:
            raise RuntimeError("source lock does not follow registration: " + role)
        lock = json.loads((ROOT / rel).read_text())
        if (lock.get("hypothesis_id") != specs[role]["hypothesis_id"]
                or lock.get("family_id") != FAMILY or lock.get("family_size") != 8
                or lock.get("registration_commit") != registration
                or lock.get("runner_sha256") != sha256(ROOT / RUNNER)
                or lock.get("source_sha256") != SOURCE_SHA
                or lock.get("key_roster_sha256") != ROSTER_SHA
                or lock.get("sources") != sources):
            raise RuntimeError("case source lock payload mismatch: " + role)
        names = git("diff-tree", "--no-commit-id", "--name-only", "-r", revision).decode().splitlines()
        if sum(name.startswith("data/pinned_evidence/") and name.endswith(".source.json") for name in names) != 1:
            raise RuntimeError("source lock commit must add one .source.json: " + role)
        commits[role] = revision
    return commits


def finite(raw) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) else None


def period_for(year: int) -> str:
    if 2010 <= year <= 2013:
        return "2010_13"
    if 2014 <= year <= 2017:
        return "2014_17"
    if 2018 <= year <= 2021:
        return "2018_21"
    if 2022 <= year <= 2024:
        return "2022_24"
    raise RuntimeError("later wave outside registered period bins")


def numeric_rows(source_root: Path, roster: list[tuple[str, int, int, int]]) -> dict[tuple[str, str, int], tuple[float | None, float | None]]:
    """Only reached after all eight source locks verify; parses selected values/N."""
    needed = {(country, year) for country, first, later, _ in roster for year in (first, later)}
    codes = {code for code, _ in CONSTRAINTS.values()} | {outcome[0] for outcome in OUTCOMES.values()}
    found = {}
    path = source_root / SOURCE_FILES["aggregate"]["path"]
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        expected = {"country", "cabr", "year", "cut", "subcut", "indicator", "value", "se", "N", "method", "fielddate", "sector_MS"}
        if not expected.issubset(set(reader.fieldnames or [])):
            raise RuntimeError("WBES aggregate CSV columns changed")
        for row in reader:
            if (row["cut"] != "All" or row["subcut"] != "All"
                    or row["method"] != "Global" or (row["sector_MS"] or "").strip() != ""
                    or row["indicator"] not in codes):
                continue
            try:
                key = (row["cabr"], int(row["year"]))
            except (TypeError, ValueError):
                continue
            if key not in needed:
                continue
            full = (row["indicator"], *key)
            if full in found:
                raise RuntimeError("duplicate selected WBES indicator/country/year key")
            found[full] = (finite(row["value"]), finite(row["N"]))
    return found


def cell_panel(role: str, roster: list[tuple[str, int, int, int]], values: dict,
               spec: dict) -> tuple[pd.DataFrame, int]:
    _, _, code, outcome = CASES[role]
    t = spec["falsification"]["threshold"]
    n_min = t["min_n_per_selected_indicator_wave"]
    x_lo, x_hi = t["valid_constraint_pct"]
    y_lo, y_hi = t["valid_growth_pct"]
    rows = []
    for country, first, later, gap in roster:
        exposure = values.get((code, country, first))
        baseline = values.get((outcome, country, first))
        future = values.get((outcome, country, later))
        if exposure is None or baseline is None or future is None:
            continue
        (x, nx), (base, nb), (y, ny) = exposure, baseline, future
        if (x is None or base is None or y is None or nx is None or nb is None or ny is None
                or nx < n_min or nb < n_min or ny < n_min
                or not x_lo <= x <= x_hi or not y_lo <= base <= y_hi or not y_lo <= y <= y_hi):
            continue
        rows.append({"country": country, "first_year": first, "later_year": later,
                     "gap_years": gap, "period": period_for(later), "x": x / 10.0,
                     "baseline_growth": base, "y": y})
    before_country_floor = len(rows)
    counts = Counter(row["country"] for row in rows)
    kept = [row for row in rows if counts[row["country"]] >= t["min_complete_pairs_per_country"]]
    frame = pd.DataFrame(kept, columns=["country", "first_year", "later_year", "gap_years",
                                        "period", "x", "baseline_growth", "y"])
    return frame.sort_values(["country", "first_year"]).reset_index(drop=True), before_country_floor


def concentration(panel: pd.DataFrame, exog: np.ndarray, names: list[str]) -> dict[str, float]:
    position = names.index("x")
    other = np.delete(exog, position, axis=1)
    residual = exog[:, position] - other @ np.linalg.lstsq(other, exog[:, position], rcond=None)[0]
    weight = residual ** 2
    total = float(weight.sum())
    if total <= 1e-15:
        return {"top_one_percent": 1.0, "country": 1.0, "later_period": 1.0}
    n_top = max(1, math.ceil(len(panel) * 0.01))
    return {
        "top_one_percent": float(np.sort(weight)[-n_top:].sum() / total),
        "country": float(pd.Series(weight).groupby(panel["country"]).sum().max() / total),
        "later_period": float(pd.Series(weight).groupby(panel["period"]).sum().max() / total),
    }


def evaluate(role: str, panel: pd.DataFrame, before_country_floor: int, spec: dict) -> dict:
    t = spec["falsification"]["threshold"]
    rows = len(panel)
    countries = panel.country.nunique() if rows else 0
    periods = panel.period.nunique() if rows else 0
    changers = sum((group.x.max() - group.x.min()) >= 0.5 for _, group in panel.groupby("country")) if rows else 0
    sample = {"key_pairs": t["expected_key_rows"], "complete_before_country_floor": before_country_floor,
              "complete_pairs": rows, "countries": int(countries), "later_wave_periods": int(periods),
              "within_country_exposure_changers_5pp": int(changers)}
    failures = []
    for label, actual, floor in [
        ("complete_pairs", rows, t["min_complete_pairs"]),
        ("complete_countries", countries, t["min_complete_countries"]),
        ("later_wave_periods", periods, t["min_later_wave_periods"]),
        ("within_country_exposure_changers_5pp", changers, t["min_within_country_exposure_changers_5pp"]),
    ]:
        if actual < floor:
            failures.append(label + "_below_frozen_floor")
    primary = None
    if not failures:
        try:
            fit = smf.ols("y ~ x + baseline_growth + gap_years + C(country) + C(period)", data=panel).fit(
                cov_type="cluster", cov_kwds={"groups": panel.country, "use_correction": True}
            )
            exog, names = fit.model.exog, fit.model.exog_names
            if fit.model.rank != exog.shape[1]:
                failures.append("model_not_full_rank")
            beta, se = float(fit.params["x"]), float(fit.bse["x"])
            if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
                failures.append("clustered_uncertainty_invalid")
            shares = concentration(panel, exog, names)
            sample["residual_exposure_share"] = shares
            for label, cap in [
                ("top_one_percent", t["max_top_one_percent_residual_x_share"]),
                ("country", t["max_one_country_residual_x_share"]),
                ("later_period", t["max_one_later_period_residual_x_share"]),
            ]:
                if shares[label] > cap:
                    failures.append(label + "_residual_exposure_cap")
            if not failures:
                p = float(2 * student_t.sf(abs(beta / se), df=int(countries) - 1))
                critical = float(student_t.ppf(1 - t["p_max_two_sided_bonferroni"] / 2,
                                               df=int(countries) - 1))
                primary = {"coefficient_per_10pp_constraint": beta, "std_error": se,
                           "p_value_two_sided": p, "confidence_level": 1 - t["p_max_two_sided_bonferroni"],
                           "confidence_interval": [beta - critical * se, beta + critical * se],
                           "n_pairs": rows, "n_countries": int(countries), "df_inference": int(countries) - 1,
                           "design_rank": int(fit.model.rank),
                           "method": "country/later-period FE OLS, baseline outcome and survey-gap controls; country-cluster CR1, Student t(G-1)"}
        except (ValueError, np.linalg.LinAlgError, KeyError, FloatingPointError) as exc:
            failures.append("model_exception_" + type(exc).__name__)
    if failures:
        verdict, reason = "INCONCLUSIVE", "one or more frozen sample, variation, rank, influence, or uncertainty gates failed"
    else:
        beta, p = primary["coefficient_per_10pp_constraint"], primary["p_value_two_sided"]
        material = t["meaningful_beta_min_abs_per_10pp"]
        if p <= t["p_max_two_sided_bonferroni"] and beta <= -material:
            verdict, reason = "SUPPORTED", "predicted negative descriptive association clears local family and material gates"
        elif p <= t["p_max_two_sided_bonferroni"] and beta >= material:
            verdict, reason = "REFUTED", "opposite positive descriptive association clears local family and material gates"
        else:
            verdict, reason = "PARTIAL", "estimable descriptive association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate_failures": failures, "sample": sample, "primary": primary}


def diagnostics_for(role: str, result: dict, registration: str, lock_commit: str) -> dict:
    return {"hypothesis_id": CASES[role][1], "family_id": FAMILY, "family_size": len(CASES),
            "registration_commit": registration, "source_lock_commit": lock_commit,
            "source_sha256": SOURCE_SHA, "source_key_roster_sha256": ROSTER_SHA,
            "result": result,
            "correction": {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
                           "family_size": len(CASES), "family_alpha": 0.01,
                           "bonferroni_p_max": 0.00125, "causal_credit": 0,
                           "policy_score_eligible": False, "policy_score_credit": 0,
                           "school_score_eligible": False, "school_score_credit": 0,
                           "featured_eligible": False},
            "limitations": LIMITATIONS}


def json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def packet_for(role: str, diagnostic: dict, spec: dict, lock_commit: str) -> dict:
    return {"packet_version": 1,
            "hypothesis": {"id": diagnostic["hypothesis_id"], "path": spec_rel(role), "topic": spec["topic"]},
            "preregistration": {"spec_commit": diagnostic["registration_commit"],
                                "source_lock_commit": lock_commit, "key_roster": ROSTER,
                                "key_roster_sha256": ROSTER_SHA},
            "family": {"id": FAMILY, "size": len(CASES), "members": MEMBERS},
            "source": {"source_sha256": SOURCE_SHA, "inputs": SOURCE_FILES,
                       "attribution": "World Bank Enterprise Surveys", "license": "CC BY 4.0"},
            "result": diagnostic["result"],
            "reproduction": {"runner": RUNNER,
                             "command": "python3 " + RUNNER + " --verify --source-root <pinned-cache-root>",
                             "result_sha256": hashlib.sha256(json_bytes(diagnostic)).hexdigest()},
            "limitations": LIMITATIONS, "correction": diagnostic["correction"]}


def manifest_for(role: str, diagnostic: dict, lock_commit: str) -> dict:
    verdict = diagnostic["result"]["verdict"]
    return {"hypothesis_id": diagnostic["hypothesis_id"], "runner": RUNNER,
            "preregistration_commit": diagnostic["registration_commit"],
            "source_lock_commit": lock_commit, "status": verdict,
            "publication_tier": "archive" if verdict == "INCONCLUSIVE" else "public_descriptive_calibration",
            "source": {"source_sha256": SOURCE_SHA, "source_lock_commit": lock_commit,
                       "key_roster_sha256": ROSTER_SHA},
            "vintages": list(SOURCE_FILES.values()), "family_id": FAMILY, "family_size": len(CASES)}


def card_for(role: str, diagnostic: dict) -> str:
    result, sample = diagnostic["result"], diagnostic["result"]["sample"]
    lines = ["# " + diagnostic["hypothesis_id"].replace("_", " "), "",
             "Verdict: " + result["verdict"] + ". " + result["reason"] + ".", "",
             "This is a descriptive country-aggregate association across adjacent Enterprise Surveys, not a firm-level or policy effect.",
             "", "Complete survey pairs / countries / later-wave periods: "
             + str(sample["complete_pairs"]) + " / " + str(sample["countries"]) + " / "
             + str(sample["later_wave_periods"]) + ".",
             "Countries with >=5pp baseline-constraint change: "
             + str(sample["within_country_exposure_changers_5pp"]) + "."]
    if result["primary"] is not None:
        p = result["primary"]
        lines += ["Country-clustered slope in annual growth points per +10pp constraint: "
                  + format(p["coefficient_per_10pp_constraint"], ".8g") + " (SE "
                  + format(p["std_error"], ".8g") + ", two-sided p "
                  + format(p["p_value_two_sided"], ".8g") + ")."]
    if result["gate_failures"]:
        lines += ["Frozen gate failures: " + ", ".join(result["gate_failures"]) + "."]
    lines += ["", "Eight correlated cells share a local Bonferroni two-sided p gate of 0.00125; no causal, policy, school, position, or featured credit.",
              "", "The exact aggregate and codebook hashes, key roster, registration, source lock, and full result are in the evidence packet.", ""]
    return "\n".join(lines)


def render_outputs(role: str, diagnostic: dict, spec: dict, lock_commit: str) -> dict[str, bytes]:
    packet = packet_for(role, diagnostic, spec, lock_commit)
    manifest = manifest_for(role, diagnostic, lock_commit)
    replay = ("#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\nfrom pathlib import Path\n"
              "root = Path(__file__).resolve().parents[3]\n"
              "source_root = os.environ.get('IESET_SOURCE_ROOT', str(root))\n"
              "raise SystemExit(subprocess.call([sys.executable, str(root / '" + RUNNER
              + "'), '--verify', '--source-root', source_root], cwd=root))\n")
    chart = {"hypothesis_id": diagnostic["hypothesis_id"], "verdict": diagnostic["result"]["verdict"],
             "sample": diagnostic["result"]["sample"], "primary": diagnostic["result"]["primary"],
             "descriptive_only": True}
    return {"hypothesis.yaml": (ROOT / spec_rel(role)).read_bytes(),
            "diagnostics.json": json_bytes(diagnostic),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "result_card.md": card_for(role, diagnostic).encode(), "replication.py": replay.encode(),
            "chart_data.json": json_bytes(chart)}


def compute_family(source_root: Path, specs: dict[str, dict], roster: list,
                   lock_commits: dict[str, str], registration: str) -> dict[str, dict[str, bytes]]:
    values = numeric_rows(source_root, roster)
    outputs = {}
    for role in CASES:
        panel, before_floor = cell_panel(role, roster, values, specs[role])
        result = evaluate(role, panel, before_floor, specs[role])
        diagnostic = diagnostics_for(role, result, registration, lock_commits[role])
        outputs[role] = render_outputs(role, diagnostic, specs[role], lock_commits[role])
        print(role + ": " + result["verdict"] + " (pairs=" + str(result["sample"]["complete_pairs"])
              + ", countries=" + str(result["sample"]["countries"])
              + ", gates=" + str(result["gate_failures"]) + ")")
    return outputs


def write_outputs(outputs: dict[str, dict[str, bytes]]) -> None:
    for role, files in outputs.items():
        folder = ROOT / run_rel(role)
        if folder.exists():
            raise RuntimeError("run directory already exists: " + role)
        folder.mkdir(parents=True)
        for name, contents in files.items():
            (folder / name).write_bytes(contents)


def verify_outputs(outputs: dict[str, dict[str, bytes]]) -> None:
    for role, files in outputs.items():
        folder = ROOT / run_rel(role)
        for name, expected in files.items():
            if (folder / name).read_bytes() != expected:
                raise RuntimeError("exact replay differs: " + role + "/" + name)
        packet = yaml.safe_load((folder / "evidence_packet.yaml").read_text())
        if packet["reproduction"]["result_sha256"] != sha256(folder / "diagnostics.json"):
            raise RuntimeError("packet/result hash mismatch: " + role)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lock-case", choices=sorted(CASES))
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.lock_case:
        write_case_lock(args.lock_case, source_root)
        return
    specs = load_specs()
    roster = load_roster(specs)
    registration = registration_commit()
    commits = verify_locks(source_root, specs)
    outputs = compute_family(source_root, specs, roster, commits, registration)
    if args.run:
        write_outputs(outputs)
    else:
        verify_outputs(outputs)
        print("exact replay passed for all eight WBES cases")


if __name__ == "__main__":
    main()
