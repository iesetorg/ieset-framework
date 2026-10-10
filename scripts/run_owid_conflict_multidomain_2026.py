#!/usr/bin/env python3
"""Frozen eight-cell country-window conflict/outcome calibration.

The registration and key roster must be committed before per-case source locks.
The run opens selected outcome values only after all eight locks are committed.
Ignored raw vintages can be supplied by --source-root without saving that path.
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
FAMILY = "owid_conflict_multidomain_four_year_2026_10_10"
RUNNER = "scripts/run_owid_conflict_multidomain_2026.py"
ROSTER = "data/pinned_evidence/owid_conflict_multidomain_2026_key_roster.csv"
ROSTER_SHA = "8046e224ad39cb787ff95416ab5d3c3ab0714ce02e3e4a7b79bae6df485d831d"
PREREG = "engine/audits/owid_conflict_multidomain_prereg_2026-10-10.md"
ANCHORS = (1995, 1999, 2003, 2007, 2011, 2015, 2019)
CONFLICT_COLS = (
    "Internationalized intrastate", "Non-internationalized intrastate",
    "Extrasystemic", "Interstate",
)
CASES = {
    "life": ("healthcare", "life_expectancy"),
    "mean_school": ("growth", "mean_years_schooling"),
    "expected_school": ("growth", "expected_years_schooling"),
    "gni": ("growth", "gni_per_capita"),
    "patents": ("growth", "resident_patents"),
    "breadth": ("trade", "exported_hs6_breadth"),
    "concentration": ("trade", "export_market_concentration"),
    "investment": ("growth", "fixed_investment_share"),
}
SOURCE_FILES = {
    "conflict": ("owid", "number-of-state-based-conflicts",
                 "data/vintages/owid/number-of-state-based-conflicts@2026-04-30T114446Z.parquet",
                 "f79099534287e0b42d93b9ab622eec5e0d8d47c02eebd5dbf79f40138f8f3885",
                 "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
                 "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"),
    "life": ("undp_hdi", "life_expectancy",
             "data/vintages/undp_hdi/life_expectancy@2026-05-05T204045Z.parquet",
             "13b99319b8b1a2be96f0774dfd67104e2b7a41b4ca176bf43486b65ff99f43cb",
             "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
             "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "mean_school": ("undp_hdi", "mean_years_schooling",
                    "data/vintages/undp_hdi/mean_years_schooling@2026-05-05T204045Z.parquet",
                    "e3a1e5a17bf361219f2a13a1e5e4b6c5cc0faa28c620245a907f2e087a725449",
                    "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                    "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "expected_school": ("undp_hdi", "expected_years_schooling",
                        "data/vintages/undp_hdi/expected_years_schooling@2026-05-05T204045Z.parquet",
                        "86c0f5c46556a914fa8bc72405fa46ad9e8de550612d03795531d2d196d5735f",
                        "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
                        "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "gni": ("undp_hdi", "gni_per_capita",
            "data/vintages/undp_hdi/gni_per_capita@2026-05-05T204045Z.parquet",
            "9f9c6a839567dcfa4dd3f51876f8e76755e5bddff3d5539ba0cd077d618f30a0",
            "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
            "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "patents": ("wipo", "patent_applications_resident",
                "data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet",
                "8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e",
                "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
                "cf2f7e75af5612b302af7fbb0479c196598aa060c20f858723108a8c95455de4"),
    "breadth": ("wits", "unique_hs6_products",
                "data/vintages/wits/unique_hs6_products@2026-07-23T153652Z.parquet",
                "29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934",
                "data/manifests/fetch_run_2026-07-23T153659Z.yaml",
                "542aacbcc80b1856262eda14f37d0532c7a14611c8b9d698ab516529942d0b73"),
    "concentration": ("wits", "product_concentration",
                      "data/vintages/wits/product_concentration@2026-07-23T151543Z.parquet",
                      "c59b180e07f484546e131fa6a4f47a725ecc790effbb3d395e5d2c4e36381949",
                      "data/manifests/fetch_run_2026-07-23T151550Z.yaml",
                      "96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5"),
    "investment": ("world_bank_wdi", "NE.GDI.FTOT.ZS",
                   "data/vintages/world_bank_wdi/NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet",
                   "fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21",
                   "data/manifests/fetch_run_2026-05-05T203305Z.yaml",
                   "53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0"),
    "population": ("world_bank_wdi", "SP.POP.TOTL",
                   "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
                   "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
                   "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
                   "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"),
}
SOURCE_DICT = {
    role: dict(zip(("publisher", "series_id", "path", "sha256", "manifest", "manifest_sha256"), item))
    for role, item in SOURCE_FILES.items()
}
SOURCE_SHA = hashlib.sha256(
    json.dumps(SOURCE_DICT, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
MEMBERS = sorted("owid_conflict_" + slug + "_four_year_2026" for _, slug in CASES.values())
LIMITATIONS = [
    "A recorded four-year state-based conflict window is not a randomized policy intervention, all violence, or a battle-death rate.",
    "Conflict and social-economic changes occur in the same four-year interval; reverse timing and common shocks remain.",
    "Country averages hide local exposure, cross-border displacement, heterogeneous conflict intensity, and reporting revisions.",
    "Schooling and export indicators within this family are correlated, so eight records are not eight independent experiments.",
    "This retrospective family follows prior IESET conflict and outcome work; Bonferroni applies locally, not to archive-wide selection.",
    "No causal, policy, school, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return result.stdout


def first_addition(rel: str) -> str:
    found = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", rel).decode().splitlines()
    if len(found) != 1:
        raise RuntimeError("missing or ambiguous first addition: " + rel)
    return found[0]


def require_unchanged(rel: str, revision: str) -> None:
    if (ROOT / rel).read_bytes() != git("show", revision + ":" + rel):
        raise RuntimeError("frozen bytes differ from first addition: " + rel)
    if git("status", "--porcelain", "--", rel).strip():
        raise RuntimeError("uncommitted frozen path: " + rel)


def spec_rel(role: str) -> str:
    topic, slug = CASES[role]
    return "hypotheses/" + topic + "/owid_conflict_" + slug + "_four_year_2026.yaml"


def run_rel(role: str) -> str:
    return "engine/runs/" + "owid_conflict_" + CASES[role][1] + "_four_year_2026"


def lock_rel(role: str) -> str:
    return "data/pinned_evidence/" + "owid_conflict_" + CASES[role][1] + "_four_year_2026.source.json"


def registration_commit() -> str:
    revisions = {first_addition(spec_rel(role)) for role in CASES}
    revisions |= {first_addition(ROSTER), first_addition(PREREG)}
    if len(revisions) != 1:
        raise RuntimeError("family registration artifacts do not share one first commit")
    commit = revisions.pop()
    for rel in [ROSTER, PREREG] + [spec_rel(role) for role in CASES]:
        require_unchanged(rel, commit)
    return commit


def load_specs() -> dict[str, dict]:
    specs = {}
    for role in CASES:
        spec = yaml.safe_load((ROOT / spec_rel(role)).read_text())
        threshold = spec["falsification"]["threshold"]
        if (spec["hypothesis_id"] not in MEMBERS or threshold.get("family_id") != FAMILY
                or threshold.get("family_size") != 8 or threshold.get("family_alpha") != 0.01
                or threshold.get("p_max_two_sided_bonferroni") != 0.00125
                or threshold.get("key_roster_sha256") != ROSTER_SHA
                or threshold.get("source_files") != {
                    k: SOURCE_DICT[k] for k in ("conflict", role) + (("population",) if role == "patents" else ())
                }):
            raise RuntimeError("case registration differs from fixed family contract: " + role)
        specs[role] = spec
    return specs


def load_roster(specs: dict[str, dict]) -> dict[str, list[tuple[str, int]]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("key-roster SHA-256 mismatch")
    rows = [(r["case"], r["country_iso3"], int(r["anchor"]))
            for r in csv.DictReader(io.StringIO(path.read_text()))]
    if len(rows) != len(set(rows)) or rows != sorted(rows):
        raise RuntimeError("key roster is duplicated or not sorted")
    rosters = {role: [] for role in CASES}
    for role, country, anchor in rows:
        if role not in rosters or anchor not in ANCHORS or len(country) != 3:
            raise RuntimeError("invalid key-roster row")
        rosters[role].append((country, anchor))
    for role, values in rosters.items():
        t = specs[role]["falsification"]["threshold"]
        if (len(values) != t["expected_key_rows"]
                or len({c for c, _ in values}) != t["expected_key_countries"]):
            raise RuntimeError("case key-roster count mismatch: " + role)
    return rosters


def source_metadata(source_root: Path) -> dict[str, dict]:
    checked = {}
    for role, item in SOURCE_DICT.items():
        path = source_root / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise RuntimeError("missing or mismatched pinned raw source: " + role)
        manifest = ROOT / item["manifest"]
        if not manifest.is_file() or sha256(manifest) != item["manifest_sha256"]:
            raise RuntimeError("missing or mismatched tracked source manifest: " + role)
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [entry for entry in entries
                   if entry.get("publisher") == item["publisher"]
                   and entry.get("series_id") == item["series_id"]
                   and entry.get("parquet_path") == item["path"]
                   and entry.get("sha256") == item["sha256"]]
        if len(matches) != 1:
            raise RuntimeError("exact source entry missing in manifest: " + role)
        checked[role] = {
            **item, "source_url": matches[0].get("source_url"),
            "license": matches[0].get("license"), "units": matches[0].get("units"),
        }
    return checked


def write_case_lock(role: str, source_root: Path) -> None:
    if role not in CASES:
        raise RuntimeError("unknown case")
    commit = registration_commit()
    specs = load_specs()
    load_roster(specs)
    checked = source_metadata(source_root)
    runner_commit = first_addition(RUNNER)
    require_unchanged(RUNNER, runner_commit)
    if subprocess.run(["git", "merge-base", "--is-ancestor", commit, runner_commit], cwd=ROOT).returncode:
        raise RuntimeError("runner does not follow registration")
    path = ROOT / lock_rel(role)
    if path.exists():
        raise RuntimeError("case source lock already exists: " + role)
    payload = {
        "schema": "ieset-source-lock-v1", "hypothesis_id": specs[role]["hypothesis_id"],
        "family_id": FAMILY, "family_size": len(CASES), "registration_commit": commit,
        "runner_commit": runner_commit, "runner_sha256": sha256(ROOT / RUNNER),
        "source_sha256": SOURCE_SHA, "key_roster_sha256": ROSTER_SHA,
        "sources": checked,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print("wrote " + lock_rel(role) + "; commit this lock alone before the next case")


def verify_locks(source_root: Path, specs: dict[str, dict]) -> dict[str, str]:
    commit = registration_commit()
    require_unchanged(RUNNER, first_addition(RUNNER))
    checked_sources = source_metadata(source_root)
    lock_commits = {}
    for role in CASES:
        rel = lock_rel(role)
        revision = first_addition(rel)
        require_unchanged(rel, revision)
        if revision == commit or subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, revision], cwd=ROOT
        ).returncode:
            raise RuntimeError("case lock not after registration: " + role)
        lock = json.loads((ROOT / rel).read_text())
        if (lock.get("hypothesis_id") != specs[role]["hypothesis_id"]
                or lock.get("family_id") != FAMILY or lock.get("family_size") != len(CASES)
                or lock.get("registration_commit") != commit
                or lock.get("runner_sha256") != sha256(ROOT / RUNNER)
                or lock.get("source_sha256") != SOURCE_SHA
                or lock.get("key_roster_sha256") != ROSTER_SHA
                or lock.get("sources") != checked_sources):
            raise RuntimeError("case source lock payload mismatch: " + role)
        names = git("diff-tree", "--no-commit-id", "--name-only", "-r", revision).decode().splitlines()
        if sum(name.startswith("data/pinned_evidence/") and name.endswith(".source.json")
               for name in names) != 1:
            raise RuntimeError("lock commit must add exactly one .source.json: " + role)
        lock_commits[role] = revision
    return lock_commits


def normal_status(raw) -> bool:
    return pd.isna(raw) or str(raw).strip() in ("", "A")


def finite(raw) -> float | None:
    try:
        number = float(raw)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def conflict_values(source_root: Path) -> dict[tuple[str, int], int]:
    item = SOURCE_DICT["conflict"]
    columns = ["country_iso3", "year", *CONFLICT_COLS]
    frame = pd.read_parquet(source_root / item["path"], columns=columns)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate conflict country-year keys")
    out = {}
    for row in frame.itertuples(index=False, name=None):
        country, year, *raws = row
        values = [finite(v) for v in raws]
        if any(v is None or v < 0 or v > 100 or not v.is_integer() for v in values):
            continue
        out[(str(country), int(year))] = int(sum(values))
    return out


def numeric_values(source_root: Path, role: str) -> dict[tuple[str, int], float]:
    item = SOURCE_DICT[role]
    if role in ("life", "mean_school", "expected_school", "gni"):
        cols = ["country_iso3", "year", "value"]
    elif role in ("patents", "investment", "population"):
        cols = ["country_iso3", "year", "value", "obs_status", "indicator_id"]
    else:
        cols = ["country_iso3", "year", "value", "freq_id", "product_code",
                "partner_iso3", "indicator_id", "series_id"]
    frame = pd.read_parquet(source_root / item["path"], columns=cols)
    if role in ("patents", "investment", "population"):
        if not frame.indicator_id.eq(item["series_id"]).all():
            raise RuntimeError("wrong indicator in " + role)
        frame = frame[frame.obs_status.map(normal_status)]
    if role in ("breadth", "concentration"):
        partner = "WLD" if role == "breadth" else "999"
        indicator = "NMBR-XPRT-HS6-PRDCT" if role == "breadth" else "HH-MKT-CNCNTRTN-NDX"
        frame = frame[
            frame.freq_id.eq("A") & frame.product_code.eq("999999")
            & frame.partner_iso3.eq(partner) & frame.indicator_id.eq(indicator)
            & frame.series_id.eq(item["series_id"])
        ]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate national value keys: " + role)
    out = {}
    for country, year, raw in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None):
        value = finite(raw)
        if value is None:
            continue
        good = {
            "life": 20 <= value <= 100, "mean_school": 0 <= value <= 30,
            "expected_school": 0 <= value <= 40, "gni": value > 0,
            "patents": value >= 0, "breadth": value > 0,
            "concentration": 0 <= value <= 1, "investment": 0 <= value <= 100,
            "population": value > 0,
        }[role]
        if good:
            out[(str(country), int(year))] = value
    return out


def transformed(role: str, raw: float, population: float | None = None) -> float:
    if role == "gni":
        return 100 * math.log(raw)
    if role == "patents":
        if population is None:
            raise RuntimeError("patent population missing")
        return math.log1p(1_000_000 * raw / population)
    if role == "breadth":
        return math.log(raw)
    return raw


def case_panel(role: str, roster: list[tuple[str, int]], conflict: dict, outcome: dict,
               population: dict | None) -> tuple[pd.DataFrame, int]:
    rows = []
    for country, anchor in roster:
        before = [(country, y) for y in range(anchor - 3, anchor + 1)]
        during = [(country, y) for y in range(anchor + 1, anchor + 5)]
        if any(k not in conflict for k in before + during):
            continue
        raw0, raw1 = outcome.get((country, anchor)), outcome.get((country, anchor + 4))
        if raw0 is None or raw1 is None:
            continue
        pop0 = pop1 = None
        if role == "patents":
            pop0 = population.get((country, anchor)) if population is not None else None
            pop1 = population.get((country, anchor + 4)) if population is not None else None
            if pop0 is None or pop1 is None:
                continue
        y0 = transformed(role, raw0, pop0)
        y1 = transformed(role, raw1, pop1)
        if not math.isfinite(y0) or not math.isfinite(y1):
            continue
        rows.append({
            "country": country, "anchor": anchor, "x": int(sum(conflict[k] for k in during) > 0),
            "baseline": y0, "prior_conflict": math.log1p(sum(conflict[k] for k in before)),
            "y": y1 - y0,
        })
    before_country_floor = len(rows)
    counts = Counter(row["country"] for row in rows)
    kept = [row for row in rows if counts[row["country"]] >= 4]
    frame = pd.DataFrame(kept, columns=["country", "anchor", "x", "baseline", "prior_conflict", "y"])
    return frame.sort_values(["country", "anchor"]).reset_index(drop=True), before_country_floor


def concentration(frame: pd.DataFrame, exog: np.ndarray, names: list[str]) -> dict:
    position = names.index("x")
    other = np.delete(exog, position, axis=1)
    residual = exog[:, position] - other @ np.linalg.lstsq(other, exog[:, position], rcond=None)[0]
    weight = residual ** 2
    total = float(weight.sum())
    if total <= 1e-15:
        return {"top_one_percent": 1.0, "country": 1.0, "anchor": 1.0}
    n_top = max(1, math.ceil(len(frame) * 0.01))
    top_rows = float(np.sort(weight)[-n_top:].sum() / total)
    country = float(pd.Series(weight).groupby(frame["country"]).sum().max() / total)
    anchor = float(pd.Series(weight).groupby(frame["anchor"]).sum().max() / total)
    return {"top_one_percent": top_rows, "country": country, "anchor": anchor}


def evaluate(role: str, panel: pd.DataFrame, before_floor: int, spec: dict) -> dict:
    t = spec["falsification"]["threshold"]
    rows = len(panel)
    countries = panel.country.nunique() if rows else 0
    anchors = panel.anchor.nunique() if rows else 0
    conflict_rows = int(panel.x.sum()) if rows else 0
    conflict_countries = panel.loc[panel.x.eq(1), "country"].nunique() if rows else 0
    no_conflict_rows = rows - conflict_rows
    no_conflict_countries = panel.loc[panel.x.eq(0), "country"].nunique() if rows else 0
    switchers = sum(group.x.nunique() == 2 for _, group in panel.groupby("country")) if rows else 0
    sample = {
        "key_rows": t["expected_key_rows"], "complete_before_country_floor": before_floor,
        "complete_rows": rows, "countries": int(countries), "anchors": int(anchors),
        "conflict_rows": conflict_rows, "conflict_countries": int(conflict_countries),
        "no_conflict_rows": no_conflict_rows, "no_conflict_countries": int(no_conflict_countries),
        "within_country_switchers": int(switchers),
    }
    failures = []
    for name, actual, threshold in [
        ("complete_rows", rows, t["min_complete_rows"]),
        ("complete_countries", countries, t["min_complete_countries"]),
        ("anchors", anchors, t["min_anchors"]),
        ("conflict_rows", conflict_rows, t["min_conflict_rows"]),
        ("conflict_countries", conflict_countries, t["min_conflict_countries"]),
        ("no_conflict_rows", no_conflict_rows, t["min_no_conflict_rows"]),
        ("no_conflict_countries", no_conflict_countries, t["min_no_conflict_countries"]),
        ("within_country_switchers", switchers, t["min_within_country_switchers"]),
    ]:
        if actual < threshold:
            failures.append(name + "_below_frozen_floor")
    primary = None
    if not failures:
        try:
            fit = smf.ols(
                "y ~ x + baseline + prior_conflict + C(country) + C(anchor)", data=panel
            ).fit(cov_type="cluster", cov_kwds={"groups": panel.country, "use_correction": True})
            exog = fit.model.exog
            names = fit.model.exog_names
            if fit.model.rank != exog.shape[1]:
                failures.append("model_not_full_rank")
            beta, se = float(fit.params["x"]), float(fit.bse["x"])
            if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
                failures.append("clustered_uncertainty_invalid")
            influence = concentration(panel, exog, names)
            sample["residual_exposure_share"] = influence
            for label, cap in [
                ("top_one_percent", t["max_top_one_percent_residual_x_share"]),
                ("country", t["max_one_country_residual_x_share"]),
                ("anchor", t["max_one_anchor_residual_x_share"]),
            ]:
                if influence[label] > cap:
                    failures.append(label + "_residual_exposure_cap")
            if not failures:
                p = float(2 * student_t.sf(abs(beta / se), df=int(countries) - 1))
                critical = float(student_t.ppf(1 - t["p_max_two_sided_bonferroni"] / 2,
                                               df=int(countries) - 1))
                primary = {
                    "coefficient": beta, "std_error": se, "p_value_two_sided": p,
                    "confidence_level": 1 - t["p_max_two_sided_bonferroni"],
                    "confidence_interval": [beta - critical * se, beta + critical * se],
                    "n_rows": rows, "n_countries": int(countries),
                    "df_inference": int(countries) - 1, "design_rank": int(fit.model.rank),
                    "method": "country/anchor FE OLS, baseline outcome and prior conflict controls; country-cluster CR1, Student t(G-1)",
                }
        except (ValueError, np.linalg.LinAlgError, KeyError, FloatingPointError) as exc:
            failures.append("model_exception_" + type(exc).__name__)
    if failures:
        verdict = "INCONCLUSIVE"
        reason = "one or more frozen sample, variation, model, or influence gates failed"
    elif primary is None:
        verdict, reason = "INCONCLUSIVE", "no estimable coefficient"
    else:
        beta, p = primary["coefficient"], primary["p_value_two_sided"]
        material = t["meaningful_beta_min_abs"]
        direction = t["expected_beta_sign"]
        predicted = (beta <= -material) if direction == "-" else (beta >= material)
        opposite = (beta >= material) if direction == "-" else (beta <= -material)
        if p <= t["p_max_two_sided_bonferroni"] and predicted:
            verdict, reason = "SUPPORTED", "predicted-direction association clears local family and material gates"
        elif p <= t["p_max_two_sided_bonferroni"] and opposite:
            verdict, reason = "REFUTED", "opposite-direction association clears local family and material gates"
        else:
            verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {
        "verdict": verdict, "reason": reason, "gate_failures": failures,
        "sample": sample, "primary": primary,
    }


def diagnostics_for(role: str, result: dict, lock_commit: str, registration: str) -> dict:
    return {
        "hypothesis_id": "owid_conflict_" + CASES[role][1] + "_four_year_2026",
        "family_id": FAMILY, "family_size": len(CASES),
        "registration_commit": registration, "source_lock_commit": lock_commit,
        "source_sha256": SOURCE_SHA, "source_key_roster_sha256": ROSTER_SHA,
        "result": result,
        "correction": {
            "disposition": "descriptive_calibration_only", "family_id": FAMILY,
            "family_size": len(CASES), "family_alpha": 0.01,
            "bonferroni_p_max": 0.00125, "causal_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0,
            "school_score_eligible": False, "school_score_credit": 0,
            "featured_eligible": False,
        },
        "limitations": LIMITATIONS,
    }


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def packet_for(role: str, diagnostic: dict, spec: dict, lock_commit: str) -> dict:
    outcome_inputs = ["conflict", role] + (["population"] if role == "patents" else [])
    return {
        "packet_version": 1,
        "hypothesis": {"id": diagnostic["hypothesis_id"], "path": spec_rel(role),
                       "topic": spec["topic"]},
        "preregistration": {
            "spec_commit": diagnostic["registration_commit"],
            "source_lock_commit": lock_commit, "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA,
        },
        "family": {"id": FAMILY, "size": len(CASES), "members": MEMBERS},
        "source": {"source_sha256": SOURCE_SHA, "inputs": {
            k: SOURCE_DICT[k] for k in outcome_inputs
        }},
        "result": diagnostic["result"],
        "reproduction": {
            "runner": RUNNER,
            "command": "python3 " + RUNNER + " --verify --source-root <pinned-cache-root>",
            "result_sha256": hashlib.sha256(json_bytes(diagnostic)).hexdigest(),
        },
        "limitations": LIMITATIONS,
        "correction": diagnostic["correction"],
    }


def manifest_for(role: str, diagnostic: dict, lock_commit: str) -> dict:
    verdict = diagnostic["result"]["verdict"]
    return {
        "hypothesis_id": diagnostic["hypothesis_id"], "runner": RUNNER,
        "preregistration_commit": diagnostic["registration_commit"],
        "source_lock_commit": lock_commit,
        "status": verdict,
        "publication_tier": "archive" if verdict == "INCONCLUSIVE" else "public_descriptive_calibration",
        "source": {"source_sha256": SOURCE_SHA, "source_lock_commit": lock_commit,
                   "key_roster_sha256": ROSTER_SHA},
        "vintages": [
            SOURCE_DICT[k] for k in ["conflict", role] + (["population"] if role == "patents" else [])
        ],
        "family_id": FAMILY, "family_size": len(CASES),
    }


def card_for(role: str, diagnostic: dict) -> str:
    verdict = diagnostic["result"]["verdict"]
    result = diagnostic["result"]
    sample = result["sample"]
    lines = [
        "# " + diagnostic["hypothesis_id"].replace("_", " "),
        "",
        "Verdict: " + verdict + ". " + result["reason"] + ".",
        "",
        "This is a retrospective descriptive association between recorded state-based conflict in a four-year window and the same window's national outcome change. No causal or policy effect is identified.",
        "",
        "Complete rows / countries / anchors: "
        + str(sample["complete_rows"]) + " / " + str(sample["countries"]) + " / " + str(sample["anchors"]) + ".",
        "Conflict rows / non-conflict rows / switching countries: "
        + str(sample["conflict_rows"]) + " / " + str(sample["no_conflict_rows"])
        + " / " + str(sample["within_country_switchers"]) + ".",
    ]
    if result["primary"] is not None:
        primary = result["primary"]
        lines += [
            "Country-clustered coefficient per conflict window: " + format(primary["coefficient"], ".8g")
            + " (SE " + format(primary["std_error"], ".8g")
            + ", two-sided p " + format(primary["p_value_two_sided"], ".8g") + ").",
        ]
    if result["gate_failures"]:
        lines += ["Frozen gate failures: " + ", ".join(result["gate_failures"]) + "."]
    lines += [
        "",
        "All eight endpoints share a local Bonferroni two-sided p gate of 0.00125. A public verdict is a calibration record only. Conflict and outcome share the window, and prior results influenced the family search.",
        "",
        "Exact raw source hashes, the key roster, registration commit, source lock, and full result are in the evidence packet. Replay with the pinned source cache.",
        "",
    ]
    return "\n".join(lines)


def render_outputs(role: str, diagnostic: dict, spec: dict, lock_commit: str) -> dict[str, bytes]:
    packet = packet_for(role, diagnostic, spec, lock_commit)
    manifest = manifest_for(role, diagnostic, lock_commit)
    replay = (
        "#!/usr/bin/env python3\n"
        "import os\nimport subprocess\nimport sys\nfrom pathlib import Path\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "source_root = os.environ.get('IESET_SOURCE_ROOT', str(root))\n"
        "raise SystemExit(subprocess.call([sys.executable, str(root / '" + RUNNER
        + "'), '--verify', '--source-root', source_root], cwd=root))\n"
    )
    chart = {
        "hypothesis_id": diagnostic["hypothesis_id"],
        "verdict": diagnostic["result"]["verdict"],
        "sample": diagnostic["result"]["sample"],
        "primary": diagnostic["result"]["primary"],
        "descriptive_only": True,
    }
    return {
        "hypothesis.yaml": (ROOT / spec_rel(role)).read_bytes(),
        "diagnostics.json": json_bytes(diagnostic),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
        "result_card.md": card_for(role, diagnostic).encode(),
        "replication.py": replay.encode(),
        "chart_data.json": json_bytes(chart),
    }


def compute_family(source_root: Path, specs: dict[str, dict], rosters: dict,
                   lock_commits: dict[str, str], registration: str) -> dict[str, dict[str, bytes]]:
    conflicts = conflict_values(source_root)
    population = numeric_values(source_root, "population")
    outputs = {}
    for role in CASES:
        outcome = numeric_values(source_root, role)
        panel, before_floor = case_panel(role, rosters[role], conflicts, outcome, population)
        result = evaluate(role, panel, before_floor, specs[role])
        diagnostic = diagnostics_for(role, result, lock_commits[role], registration)
        outputs[role] = render_outputs(role, diagnostic, specs[role], lock_commits[role])
        print(role + ": " + result["verdict"] + " (rows=" + str(result["sample"]["complete_rows"])
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
            actual = (folder / name).read_bytes()
            if actual != expected:
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
    rosters = load_roster(specs)
    registration = registration_commit()
    locks = verify_locks(source_root, specs)
    outputs = compute_family(source_root, specs, rosters, locks, registration)
    if args.run:
        write_outputs(outputs)
    else:
        verify_outputs(outputs)
        print("exact replay passed for all eight cases")


if __name__ == "__main__":
    main()
