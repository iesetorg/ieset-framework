#!/usr/bin/env python3
"""Frozen Fraser Area 2 change to forward WIPO resident filing-rate change."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "efw_legal_rights_resident_patenting_forward_2026"
FAMILY = "efw_legal_rights_resident_patenting_forward_2026_10_10"
SPEC = f"hypotheses/institutional_quality/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
RUNNER = "scripts/run_efw_legal_wipo_patenting_2026.py"
PREREG = "engine/audits/efw_legal_wipo_patent_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/efw_legal_wipo_resident_patent_2026_key_roster.csv"
ROSTER_SHA = "602cfb19cb1108c92f7395d3e2e26c7e6bfcade20ade356384393a74df66a95b"
LOCK = "data/pinned_evidence/efw_legal_wipo_resident_patent_2026.source.json"
RUN = f"engine/runs/{ID}"
SUMMARY = "engine/audits/efw_legal_wipo_patent_results_2026-10-10.md"
WIPO_MANIFEST = "data/manifests/fetch_run_2026-05-19T095056Z.yaml"
WDI_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
SOURCES = {
    "fraser_panel": {"publisher": "fraser_efw", "series_id": "efw_panel",
        "path": "data/vintages/fraser_efw/efw_panel@2026-05-02T202914Z.parquet",
        "sha256": "e1856242bda7b543aa4563d7e6e47688debed5c8f16d5a717855b552f9a8dcb7"},
    "fraser_workbook": {"publisher": "fraser_efw", "series_id": "efw_2025_master_workbook",
        "path": "data/vintages/fraser_efw/efw_2025@2026-05-02T202648Z.xlsx",
        "sha256": "0a478488e5c2a494a70afb5f4582ec34409536d5c15f9d4a0e0238b4b9d74d32"},
    "fraser_parser": {"publisher": "fraser_efw", "series_id": "tracked_fetcher",
        "path": "data/fetchers/fraser_efw.py",
        "sha256": "29d7ebf28de4bbe7a2507eceeb170e169109cad3696eefd8931ec52922a4877f"},
    "resident_patents": {"publisher": "wipo", "series_id": "patent_applications_resident",
        "indicator_id": "IP.PAT.RESD",
        "path": "data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet",
        "sha256": "8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e",
        "manifest": WIPO_MANIFEST,
        "manifest_sha256": "cf2f7e75af5612b302af7fbb0479c196598aa060c20f858723108a8c95455de4"},
    "population": {"publisher": "world_bank_wdi", "series_id": "SP.POP.TOTL",
        "indicator_id": "SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest": WDI_MANIFEST,
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "real_gdppc": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "indicator_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": WDI_MANIFEST,
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
}
START, END = 2003, 2016
MIN_YEARS, MIN_ROWS, MIN_COUNTRIES = 6, 700, 65
MATERIAL_X, MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = .25, 150, 40
MIN_FOLD_ROWS, MIN_FOLD_COUNTRIES = 500, 50
MAX_COUNTRY_SHARE, MAX_TOP_ONE_PERCENT = .15, .25
POP_MIN, P_MAX, MEANINGFUL_BETA = 1_000_000, .01, .10
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 1, "family_alpha": P_MAX, "p_max_two_sided": P_MAX,
              "causal_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "school_score_eligible": False,
              "school_score_credit": 0, "featured_eligible": False}
LIMITS = [
    "Fraser Area 2 is a broad institutional composite, not a direct patent-law or enforcement measure.",
    "WIPO resident applications are filings, not grants, invention quality or welfare.",
    "Legal change, income, industrial mix, research, filing practice and administrative capacity can move together.",
    "Country/year effects and baseline controls do not identify a causal legal-system effect.",
    "This family was chosen in a visible archive; p=0.01 does not correct archive-wide selection.",
    "No causal, policy, school, position or featured credit is assigned.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_add(path: str) -> str:
    lines = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if len(lines) != 1:
        raise RuntimeError(f"expected exactly one first-addition commit for {path}: {lines}")
    return lines[0]


def frozen(path: str, revision: str) -> None:
    if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"registered bytes changed: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted registered path: {path}")


def registration() -> str:
    paths = [SPEC, STEELMAN, RUNNER, PREREG, ROSTER]
    additions = {first_add(path) for path in paths}
    if len(additions) != 1:
        raise RuntimeError(f"registration paths have different first-addition commits: {additions}")
    revision = additions.pop()
    for path in paths:
        frozen(path, revision)
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("source-key roster hash changed")
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN).strip():
        raise RuntimeError("registration commit already contained measured result")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = spec["falsification"]["threshold"]
    expected = {"family_id": FAMILY, "family_size": 1, "family_alpha": P_MAX,
                "p_max_two_sided": P_MAX, "meaningful_beta_min_abs": MEANINGFUL_BETA,
                "min_complete_rows": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
                "min_complete_years_per_country": MIN_YEARS,
                "material_area2_change_min_abs": MATERIAL_X,
                "min_material_change_rows": MIN_MATERIAL_ROWS,
                "min_material_change_countries": MIN_MATERIAL_COUNTRIES,
                "max_top_country_residualized_exposure_share": MAX_COUNTRY_SHARE,
                "max_top_one_percent_residualized_exposure_share": MAX_TOP_ONE_PERCENT,
                "min_fold_rows": MIN_FOLD_ROWS, "min_fold_countries": MIN_FOLD_COUNTRIES,
                "population_min": POP_MIN, "source_key_roster_path": ROSTER,
                "source_key_roster_sha256": ROSTER_SHA, "source_lock_path": LOCK}
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("claim_direction") != "+" or spec.get("evidence_type") != "associational"
            or spec["sample"]["period"] != [2000, 2019]
            or any(threshold.get(k) != v for k, v in expected.items())
            or threshold.get("area2_range") != [0, 10]
            or spec.get("covers_claims") != []):
        raise RuntimeError("frozen specification does not match runner")
    return revision


def source_lock(reg: str) -> str:
    revision = first_add(LOCK)
    frozen(LOCK, revision)
    if subprocess.run(["git", "merge-base", "--is-ancestor", reg, revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock was not committed after registration")
    data = json.loads((ROOT / LOCK).read_text())
    if (data.get("family_id") != FAMILY or data.get("hypothesis_id") != ID
            or data.get("registration_commit") != reg
            or data.get("source_key_roster_sha256") != ROSTER_SHA
            or data.get("sources") != SOURCES):
        raise RuntimeError("source lock differs from registered source roles")
    return revision


def check_sources(source_root: Path) -> None:
    for role, src in SOURCES.items():
        raw = source_root / src["path"]
        if not raw.is_file() or sha256(raw) != src["sha256"]:
            raise RuntimeError(f"raw source hash mismatch: {role}")
        if "manifest" not in src:
            continue
        manifest = source_root / src["manifest"]
        if not manifest.is_file() or sha256(manifest) != src["manifest_sha256"]:
            raise RuntimeError(f"fetch manifest hash mismatch: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [e for e in entries if e.get("publisher") == src["publisher"]
                   and e.get("series_id") == src["series_id"]
                   and e.get("parquet_path") == src["path"]
                   and e.get("sha256") == src["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"no exact source-manifest entry: {role}")


def roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("source-key roster hash mismatch")
    with (ROOT / ROSTER).open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["country_iso3", "year"]:
            raise RuntimeError("source-key roster header changed")
        rows = [(r["country_iso3"], int(r["year"])) for r in reader]
    if (len(rows) != 2296 or len({c for c, _ in rows}) != 164
            or rows != sorted(rows) or len(set(rows)) != len(rows)
            or any(not START <= y <= END for _, y in rows)
            or any(len(c) != 3 or not c.isalpha() or not c.isupper() for c, _ in rows)):
        raise RuntimeError("source-key roster shape/order changed")
    return rows


def efw_cells(source_root: Path, countries: set[str]) -> dict[tuple[str, int], object]:
    frame = pd.read_parquet(source_root / SOURCES["fraser_panel"]["path"], columns=[
        "country_iso3", "year", "area_2_legal_system_property_rights"])
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate Fraser country/year source key")
    return {(c, int(y)): v for c, y, v in frame.itertuples(index=False, name=None) if not pd.isna(y)}


def indicator_cells(source_root: Path, role: str, countries: set[str]) -> dict[tuple[str, int], tuple[object, object]]:
    src = SOURCES[role]
    frame = pd.read_parquet(source_root / src["path"], columns=[
        "country_iso3", "indicator_id", "year", "value", "obs_status"])
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if set(frame.indicator_id.dropna()) != {src["indicator_id"]}:
        raise RuntimeError(f"indicator mismatch: {role}")
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate indicator country/year source key: {role}")
    return {(c, int(y)): (v, status) for c, _, y, v, status in frame.itertuples(index=False, name=None)}


def number(value: object, low: float, high: float = math.inf) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and low <= v <= high else None


def indicator_value(cell: tuple[object, object] | None, low: float) -> float | None:
    if cell is None:
        return None
    value, status = cell
    if status is not None and not pd.isna(status) and str(status).strip() not in ("", "A"):
        return None
    return number(value, low)


def build_panel(source_root: Path, keys: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict]:
    countries = {c for c, _ in keys}
    rights = efw_cells(source_root, countries)
    patent = indicator_cells(source_root, "resident_patents", countries)
    population = indicator_cells(source_root, "population", countries)
    income = indicator_cells(source_root, "real_gdppc", countries)
    kept, dropped = [], Counter()
    for country, year in keys:
        a0 = number(rights.get((country, year - 3)), 0, 10)
        a1 = number(rights.get((country, year)), 0, 10)
        if None in (a0, a1):
            dropped["missing_nonfinite_or_out_of_range_area2"] += 1
            continue
        p0 = indicator_value(patent.get((country, year)), 0)
        p1 = indicator_value(patent.get((country, year + 3)), 0)
        pop0 = indicator_value(population.get((country, year)), POP_MIN)
        pop1 = indicator_value(population.get((country, year + 3)), POP_MIN)
        gdppc = indicator_value(income.get((country, year)), 0)
        if None in (p0, p1, pop0, pop1, gdppc) or gdppc <= 0:
            dropped["missing_status_or_bound_endpoint"] += 1
            continue
        if abs(p0 - round(p0)) > 1e-6 or abs(p1 - round(p1)) > 1e-6:
            dropped["noninteger_patent_count"] += 1
            continue
        baseline = math.log1p(1e6 * p0 / pop0)
        endpoint = math.log1p(1e6 * p1 / pop1)
        kept.append((country, year, a1 - a0, endpoint - baseline,
                     baseline, math.log(gdppc)))
    frame = pd.DataFrame(kept, columns=["country", "year", "x", "y", "baseline", "log_gdppc"])
    before_floor = len(frame)
    if not frame.empty:
        counts = frame.country.value_counts()
        frame = frame.loc[frame.country.map(counts).ge(MIN_YEARS)].copy()
    dropped["country_below_six_year_floor"] = before_floor - len(frame)
    frame = frame.sort_values(["year", "country"]).reset_index(drop=True)
    material = frame.x.abs().ge(MATERIAL_X) if not frame.empty else pd.Series(dtype=bool)
    sample = {"key_roster_rows": len(keys), "key_roster_countries": len(countries),
              "complete_rows_before_country_floor": before_floor,
              "valid_rows": len(frame), "valid_countries": int(frame.country.nunique()) if not frame.empty else 0,
              "material_change_rows": int(material.sum()),
              "material_change_countries": int(frame.loc[material, "country"].nunique()) if not frame.empty else 0,
              "dropped": dict(sorted(dropped.items())),
              "selected_values_read_after_committed_lock": True}
    return frame, sample


def fit(frame: pd.DataFrame) -> dict:
    if len(frame) < 10 or frame.country.nunique() < 5:
        raise ValueError("too few country-years for fixed-effects estimator")
    covars = "1 + x + baseline + log_gdppc + C(country) + C(year)"
    design = patsy.dmatrix(covars, frame, return_type="dataframe")
    matrix = design.to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    if rank != matrix.shape[1]:
        raise ValueError(f"rank-deficient design {rank}/{matrix.shape[1]}")
    ix = list(design.columns).index("x")
    countries = int(frame.country.nunique())
    model = sm.OLS(frame.y.to_numpy(dtype=float), matrix).fit(
        cov_type="cluster", cov_kwds={"groups": frame.country.to_numpy(),
                                      "use_correction": True, "df_correction": True})
    beta, se = float(model.params[ix]), float(model.bse[ix])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        raise ValueError("nonfinite or nonpositive country-cluster uncertainty")
    p = float(2 * student_t.sf(abs(beta / se), df=countries - 1))
    if not math.isfinite(p):
        raise ValueError("nonfinite two-sided p")
    z = patsy.dmatrix("1 + baseline + log_gdppc + C(country) + C(year)",
                      frame, return_type="dataframe").to_numpy(dtype=float)
    x = frame.x.to_numpy(dtype=float)
    residual = x - z @ np.linalg.lstsq(z, x, rcond=None)[0]
    square = residual**2
    total = float(square.sum())
    if not math.isfinite(total) or total <= 1e-12:
        raise ValueError("no residualized Area 2 change variation")
    concentration = pd.DataFrame({"country": frame.country, "square": square})
    max_country = float(concentration.groupby("country").square.sum().max() / total)
    top_n = max(1, math.ceil(len(frame) * .01))
    max_rows = float(np.sort(square)[-top_n:].sum() / total)
    critical = float(student_t.ppf(1 - P_MAX / 2, df=countries - 1))
    return {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
            "confidence_interval_99pct": [beta - critical * se, beta + critical * se],
            "n_rows": len(frame), "n_countries": countries,
            "df_inference": countries - 1, "model_rank": rank,
            "model_columns": matrix.shape[1],
            "top_country_residualized_exposure_share": max_country,
            "top_one_percent_residualized_exposure_share": max_rows,
            "method": "country/year fixed-effects OLS with baseline controls; country-cluster CR1; Student t(G-1)"}


def fold(country: str) -> int:
    return int(hashlib.sha256(country.encode()).hexdigest()[:8], 16) % 5


def analyze(source_root: Path, run_utc: str, reg: str, lock_commit: str) -> tuple[dict, pd.DataFrame]:
    keys = roster()
    frame, sample = build_panel(source_root, keys)
    failures = []
    if sample["valid_rows"] < MIN_ROWS:
        failures.append("complete_row_floor")
    if sample["valid_countries"] < MIN_COUNTRIES:
        failures.append("complete_country_floor")
    if sample["material_change_rows"] < MIN_MATERIAL_ROWS:
        failures.append("material_change_row_floor")
    if sample["material_change_countries"] < MIN_MATERIAL_COUNTRIES:
        failures.append("material_change_country_floor")
    primary = None
    if not frame.empty:
        try:
            primary = fit(frame)
        except ValueError as exc:
            failures.append("primary_estimator: " + str(exc))
    if primary:
        if primary["top_country_residualized_exposure_share"] > MAX_COUNTRY_SHARE:
            failures.append("top_country_residual_concentration")
        if primary["top_one_percent_residualized_exposure_share"] > MAX_TOP_ONE_PERCENT:
            failures.append("top_one_percent_residual_concentration")
    folds = []
    for omitted in range(5):
        part = frame.loc[frame.country.map(fold).ne(omitted)].copy()
        record = {"omitted_hash_fold": omitted, "n_rows": len(part),
                  "n_countries": int(part.country.nunique()) if not part.empty else 0}
        if record["n_rows"] < MIN_FOLD_ROWS or record["n_countries"] < MIN_FOLD_COUNTRIES:
            failures.append(f"fold_{omitted}_sample_floor")
        try:
            estimate = fit(part)
            record.update({"coefficient": estimate["coefficient"],
                           "std_error": estimate["std_error"],
                           "p_value_two_sided": estimate["p_value_two_sided"]})
        except ValueError as exc:
            record["fit_error"] = str(exc)
            failures.append(f"fold_{omitted}_estimator")
        folds.append(record)
    positive_folds = sum(row.get("coefficient", 0) > 0 for row in folds)
    negative_folds = sum(row.get("coefficient", 0) < 0 for row in folds)
    if failures:
        verdict, reason = "INCONCLUSIVE", "; ".join(sorted(set(failures)))
    elif primary["coefficient"] >= MEANINGFUL_BETA and primary["p_value_two_sided"] <= P_MAX and positive_folds >= 4:
        verdict, reason = "SUPPORTED", "positive magnitude, p and country-fold sign gates cleared"
    elif primary["coefficient"] <= -MEANINGFUL_BETA and primary["p_value_two_sided"] <= P_MAX and negative_folds >= 4:
        verdict, reason = "REFUTED", "opposite negative magnitude, p and country-fold sign gates cleared"
    else:
        verdict, reason = "PARTIAL", "estimable association misses a directional gate"
    diag = {"hypothesis_id": ID, "family_id": FAMILY, "family_size": 1,
            "run_utc": run_utc, "runner": RUNNER, "registration_commit": reg,
            "source_lock_commit": lock_commit, "source_lock": LOCK,
            "source_key_roster_sha256": ROSTER_SHA, "verdict": verdict,
            "verdict_label": verdict, "verdict_reason": reason,
            "template": "panel_fe", "preflight": sample, "primary": primary,
            "holdout_folds": folds, "positive_fold_signs": positive_folds,
            "negative_fold_signs": negative_folds, "failed_gates": sorted(set(failures)),
            "p_max_two_sided": P_MAX, "meaningful_beta_min_abs": MEANINGFUL_BETA,
            "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
            "correction": CORRECTION, "limitations": LIMITS}
    return diag, frame


def payloads(diag: dict, frame: pd.DataFrame) -> dict[str, bytes]:
    verdict = diag["verdict"]
    manifest = {"hypothesis_id": ID, "run_utc": diag["run_utc"], "runner": RUNNER,
                "preregistration_commit": diag["registration_commit"],
                "source_lock_commit": diag["source_lock_commit"], "source_lock": LOCK,
                "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": diag["preflight"], "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": diag["run_utc"],
              "hypothesis": {"id": ID, "path": SPEC, "topic": "institutional_quality"},
              "preregistration": {"spec_commit": diag["registration_commit"],
                                  "source_lock_commit": diag["source_lock_commit"],
                                  "family_id": FAMILY, "family_size": 1,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": STEELMAN},
              "reproduction": {"runner": RUNNER, "run_dir": RUN,
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(),
                          "reason": diag["verdict_reason"]},
              "data": {"inputs": SOURCES, "sample": diag["preflight"]},
              "results": {"primary": diag["primary"], "folds": diag["holdout_folds"]},
              "failed_gates": diag["failed_gates"], "limitations": LIMITS,
              "correction": CORRECTION}
    annual = []
    if not frame.empty:
        for year, group in frame.groupby("year", sort=True):
            annual.append({"year": int(year), "n": len(group),
                           "median_area2_change": float(group.x.median()),
                           "median_forward_patent_rate_log_change": float(group.y.median())})
    chart = {"hypothesis_id": ID, "interpretation": "descriptive complete-case annual medians only",
             "years": annual}
    primary = diag["primary"] or {}
    coefficients = pd.DataFrame([{"term": "area2_change", **primary}]) if primary else pd.DataFrame(columns=[
        "term", "coefficient", "std_error", "p_value_two_sided"])
    buf = io.BytesIO()
    coefficients.to_parquet(buf, index=False)
    beta_text = f"{primary['coefficient']:+.6f}" if primary else "unavailable"
    p_text = f"{primary['p_value_two_sided']:.6g}" if primary else "unavailable"
    card = (f"# {ID}\n\n**{verdict}** — {diag['verdict_reason']}.\n\n"
            f"Locked slope {beta_text} log points per +1 Fraser Area 2 point; "
            f"two-sided country-cluster p={p_text}. Complete sample: "
            f"{diag['preflight']['valid_rows']} country-years in "
            f"{diag['preflight']['valid_countries']} countries. This is a descriptive "
            "association, not a causal legal-system or patent-law effect.\n\n"
            f"Registration: `{diag['registration_commit']}`; source lock: "
            f"`{diag['source_lock_commit']}`. Replay with `python3 {RUNNER} --verify`.\n\n"
            "WIPO applications measure filings rather than patent grants or invention quality. "
            "No policy, school, position, causal or featured credit.\n")
    replication = ("#!/usr/bin/env python3\nimport subprocess\nimport sys\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--verify']))\n")
    def js(value: object) -> bytes:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    def ya(value: object) -> bytes:
        return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode()
    return {"hypothesis.yaml": (ROOT / SPEC).read_bytes(), "manifest.yaml": ya(manifest),
            "evidence_packet.yaml": ya(packet), "diagnostics.json": js(diag),
            "chart_data.json": js(chart), "coefficients.parquet": buf.getvalue(),
            "result_card.md": card.encode(), "replication.py": replication.encode()}


def summary(diag: dict) -> str:
    primary = diag["primary"] or {}
    return ("# Fraser legal rights and forward resident patent filings — locked result\n\n"
            f"**{diag['verdict']}**. {diag['verdict_reason']}.\n\n"
            f"Frozen source-key roster: {diag['preflight']['key_roster_rows']} rows / "
            f"{diag['preflight']['key_roster_countries']} countries. Complete eligible panel "
            f"after the six-year country floor: {diag['preflight']['valid_rows']} rows / "
            f"{diag['preflight']['valid_countries']} countries. Material-change rows: "
            f"{diag['preflight']['material_change_rows']} across "
            f"{diag['preflight']['material_change_countries']} countries.\n\n"
            f"Area 2 beta {primary.get('coefficient', 'unavailable')}; country-cluster SE "
            f"{primary.get('std_error', 'unavailable')}; two-sided p "
            f"{primary.get('p_value_two_sided', 'unavailable')}; positive/negative "
            f"country-fold signs {diag['positive_fold_signs']}/{diag['negative_fold_signs']}. "
            f"Failed gates: {diag['failed_gates']}.\n\n"
            "Fraser Area 2 is a broad composite; WIPO resident applications are filings. "
            "This is a descriptive association, not a patent-law, enforcement or causal estimate. "
            "No policy, school, position, causal or featured credit. The one-test alpha does "
            "not correct archive-wide selection.\n\n"
            f"Spec commit `{diag['registration_commit']}`; source lock commit "
            f"`{diag['source_lock_commit']}`. Exact replay: `python3 {RUNNER} --verify`.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    reg = registration()
    lock_commit = source_lock(reg)
    check_sources(args.source_root)
    keys = roster()
    if args.preflight:
        print(json.dumps({"registration_commit": reg, "source_lock_commit": lock_commit,
                          "source_key_rows": len(keys),
                          "source_key_countries": len({c for c, _ in keys}),
                          "source_hashes": {role: src["sha256"] for role, src in SOURCES.items()}},
                         sort_keys=True))
        return 0
    out = ROOT / RUN
    if args.verify:
        if not out.is_dir() or not (ROOT / SUMMARY).is_file():
            raise RuntimeError("no saved run to verify")
        previous = json.loads((out / "diagnostics.json").read_text())
        run_utc = previous["run_utc"]
    else:
        if out.exists() or (ROOT / SUMMARY).exists():
            raise RuntimeError("result already exists; use --verify")
        run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diag, frame = analyze(args.source_root, run_utc, reg, lock_commit)
    files, report = payloads(diag, frame), summary(diag).encode()
    if args.verify:
        for name, data in files.items():
            if (out / name).read_bytes() != data:
                raise RuntimeError(f"exact replay mismatch: {name}")
        if (ROOT / SUMMARY).read_bytes() != report:
            raise RuntimeError("exact replay mismatch: result audit")
        print(f"OK exact replay: {len(files)} run artifacts + result audit; {diag['verdict']}")
        return 0
    out.mkdir(parents=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    (ROOT / SUMMARY).write_bytes(report)
    primary = diag["primary"] or {}
    print(f"{diag['verdict']} beta={primary.get('coefficient')} "
          f"p={primary.get('p_value_two_sided')} "
          f"n={diag['preflight']['valid_rows']} countries={diag['preflight']['valid_countries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
