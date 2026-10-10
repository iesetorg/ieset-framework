#!/usr/bin/env python3
"""Blind union-density/low-education-unemployment calibration.

--build-roster and --preflight read the union-density exposure, GDPpc control,
and outcome keys/dimensions only. --run and --verify open selected outcome
values/status only after separate registration and source-lock commits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_union_density_low_education_unemployment_calibration_2026"
OLD_ID = "union_density_wage_compression_employment_tradeoff"
FAMILY = "union_density_low_education_unemployment_2026_10_10"
RUNNER = "scripts/run_union_density_low_education_unemployment_calibration_2026.py"
TESTS = "tests/test_union_density_low_education_unemployment_calibration_2026.py"
SPEC = f"hypotheses/labour/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PREREG = "engine/audits/union_density_low_education_unemployment_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/union_density_low_education_unemployment_2026_key_roster.csv"
ROSTER_SHA = "c8b551df75f431ab1450ecc7663f2b16d30b04dbd1c31c2a3d8151cf6b6c64cf"
LOCK = "data/pinned_evidence/union_density_low_education_unemployment_2026.manifest.json"
RUN = f"engine/runs/{ID}"
ANCHORS = (2007, 2010, 2013, 2016, 2019, 2022)
ALPHA = 0.01
MEANINGFUL_BETA = 0.25  # pp two-year unemployment change per 10 pp union density
FLOOR = {"min_valid_rows": 120, "min_valid_countries": 25,
         "min_countries_with_three_windows": 20, "min_distinct_anchors": 5,
         "min_rows_each_present_anchor": 15, "max_one_anchor_share": 0.30,
         "min_union_density_iqr_pp": 10.0,
         "min_countries_with_union_range_3pp": 20,
         "max_top_one_percent_partialled_x_share": 0.20,
         "max_top_country_partialled_x_share": 0.15}
MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
MANIFEST_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
SOURCES = {
    "union": {"publisher": "oecd", "series_id": "TUD",
              "path": "data/vintages/oecd/TUD@2026-05-05T195705Z.parquet",
              "sha256": "01ac4f0e100915330f53f4be310e9b26bfe33e7bcbd05f22cfa894447438a417",
              "manifest": MANIFEST, "manifest_sha256": MANIFEST_SHA},
    "unemployment": {"publisher": "oecd", "series_id": "DSD_LMS_low_education_unemployment_rate",
                     "path": "data/vintages/oecd/DSD_LMS_low_education_unemployment_rate@2026-05-05T195457Z.parquet",
                     "sha256": "e4977582ffe0de5526e75d1d473d07fb293a2fb55f73bd41b1e17cb89fd4c4a8",
                     "manifest": MANIFEST, "manifest_sha256": MANIFEST_SHA},
    "gdp_pc": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
               "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
               "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
               "manifest": MANIFEST, "manifest_sha256": MANIFEST_SHA},
}
CORRECTION = {"family_id": FAMILY, "family_size": 1, "family_alpha": ALPHA,
              "p_max_two_sided": ALPHA, "disposition": "descriptive_component_only",
              "school_score_eligible": False, "school_score_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "Union density is a share of employees in trade unions, not a policy intervention or collective-bargaining coverage.",
    "The OECD outcome is the unemployment rate among adults aged 25–64 with low educational attainment, not youth unemployment or wage compression.",
    "The design uses two-year nonoverlapping windows and country/anchor-year effects, but time-varying labour demand, institutions, and reverse causation remain.",
    "Baseline unemployment and GDP per capita adjust observed starting conditions but do not establish a causal effect.",
    "The one-test p threshold is local to this prospective calibration; it does not correct the historical IESET search across 131 placeholders.",
    "The old Fraser/GDP-per-capita placeholder stays archived with no score or verdict transfer.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    lines = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not lines:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return lines[-1]


def committed_unchanged(relative: str, rev: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{rev}:{relative}"):
        raise RuntimeError(f"frozen first-commit mismatch: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def source_check() -> None:
    manifest = ROOT / MANIFEST
    if not manifest.is_file() or sha256(manifest) != MANIFEST_SHA:
        raise RuntimeError("fetch manifest SHA mismatch")
    entries = yaml.safe_load(manifest.read_text()).get("entries", [])
    for role, src in SOURCES.items():
        path = ROOT / src["path"]
        if not path.is_file() or sha256(path) != src["sha256"]:
            raise RuntimeError(f"raw source SHA mismatch: {role}")
        matches = [entry for entry in entries
                   if entry.get("publisher") == src["publisher"]
                   and entry.get("series_id") == src["series_id"]
                   and entry.get("parquet_path") == src["path"]
                   and entry.get("sha256") == src["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest entry mismatch: {role}")


def blank_status(value: Any) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def outcome_dimensions() -> dict[str, Any]:
    return {"SEX": "_T", "AGE": "Y25T64", "ATTAINMENT_LEV": "ISCED11A_0T2",
            "MEASURE": "UNEMPLOYMENT", "UNIT_MEASURE": "PT_LF_SUB",
            "STATISTICAL_OPERATION": "OBS"}


def select_outcome_keys() -> set[tuple[str, int]]:
    """No outcome value, null mask, or status field is selected here."""
    cols = ["REF_AREA", "period", *outcome_dimensions()]
    data = pd.read_parquet(ROOT / SOURCES["unemployment"]["path"], columns=cols)
    for col, value in outcome_dimensions().items():
        data = data.loc[data[col].eq(value)]
    if data.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate selected outcome key")
    return {(str(c), int(y)) for c, y in data[["REF_AREA", "period"]].itertuples(index=False, name=None)}


def source_keys() -> list[tuple[str, int]]:
    """Read exposed union/GDPpc values and selected outcome keys only."""
    union = pd.read_parquet(ROOT / SOURCES["union"]["path"], columns=[
        "REF_AREA", "MEASURE", "UNIT_MEASURE", "period", "value", "OBS_STATUS"])
    union = union.loc[union.MEASURE.eq("TUD") & union.UNIT_MEASURE.eq("PT_SAL")
                      & union.OBS_STATUS.eq("A") & union.value.between(0, 100)].copy()
    if union.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate actual union-density key")
    gdp = pd.read_parquet(ROOT / SOURCES["gdp_pc"]["path"], columns=[
        "country_iso3", "year", "value", "obs_status"])
    gdp = gdp.loc[gdp.country_iso3.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
    if gdp.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate GDPpc control key")
    valid_gdp = {(str(c), int(y)) for c, y, v, s in gdp.itertuples(index=False, name=None)
                 if pd.notna(v) and np.isfinite(v) and v > 0 and blank_status(s)}
    keys = select_outcome_keys()
    rows = sorted(((str(c), int(y)) for c, y in union[["REF_AREA", "period"]].itertuples(index=False, name=None)
                   if y in ANCHORS and (c, y) in keys and (c, y+2) in keys
                   and (c, y) in valid_gdp), key=lambda z: (z[1], z[0]))
    if len(rows) != 200 or len({c for c, _ in rows}) != 39:
        raise RuntimeError(f"key-only envelope changed: {len(rows)} rows")
    return rows


def roster_bytes(rows: list[tuple[str, int]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["country_iso3", "anchor_year"])
    writer.writerows(rows)
    return buffer.getvalue().encode()


def key_preflight() -> dict[str, Any]:
    source_check()
    rows = source_keys()
    path = ROOT / ROSTER
    if not path.is_file() or path.read_bytes() != roster_bytes(rows) or sha256(path) != ROSTER_SHA:
        raise RuntimeError("frozen key-only roster mismatch")
    from collections import Counter
    counts = Counter(c for c, _ in rows)
    return {"roster_rows": len(rows), "roster_reporter_economies": len(counts),
            "reporters_with_three_windows": sum(v >= 3 for v in counts.values()),
            "anchor_counts": {str(y): sum(year == y for _, year in rows) for y in ANCHORS},
            "outcome_values_or_status_read": False}


def threshold() -> dict[str, Any]:
    return {"family_id": FAMILY, "family_size": 1, "family_alpha": ALPHA,
            "p_max_two_sided": ALPHA, "expected_beta_sign": "+",
            "meaningful_beta_min_abs": MEANINGFUL_BETA, **FLOOR,
            "roster_sha256": ROSTER_SHA,
            "source_files": {role: {field: src[field] for field in
                             ("path", "sha256", "manifest", "manifest_sha256")}
                             for role, src in SOURCES.items()},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER, TESTS, SPEC, STEELMAN]
    revs = {first_addition(path) for path in frozen}
    if len(revs) != 1:
        raise RuntimeError("registration files must share first-addition commit")
    rev = revs.pop()
    for path in frozen:
        committed_unchanged(path, rev)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec["hypothesis_id"] != ID or spec["status"] != "pre_registered"
            or spec["steelman"] != STEELMAN or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != []
            or spec["falsification"]["threshold"] != threshold()):
        raise RuntimeError("registered spec mismatch")
    if git_output("ls-tree", "-r", "--name-only", rev, "--", RUN).strip():
        raise RuntimeError("measured run present in registration commit")
    return rev


def lock_payload(rev: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": rev,
            "source_files": SOURCES, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "blind_preflight": preflight, "correction": CORRECTION,
            "locked_utc": datetime.now(timezone.utc).isoformat()}


def source_lock_commit() -> tuple[str, dict[str, Any]]:
    rev = first_addition(LOCK)
    committed_unchanged(LOCK, rev)
    payload = json.loads((ROOT / LOCK).read_text())
    if (payload.get("family_id") != FAMILY
            or payload.get("preregistration_commit") != registration_commit()
            or payload.get("source_files") != SOURCES
            or payload.get("key_roster") != {"path": ROSTER, "sha256": ROSTER_SHA}
            or payload.get("blind_preflight") != key_preflight()
            or payload.get("correction") != CORRECTION):
        raise RuntimeError("source lock changed or mismatches frozen registration")
    prereg_rev = payload["preregistration_commit"]
    if rev == prereg_rev:
        raise RuntimeError("source lock must be in a distinct later commit")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", prereg_rev, rev],
                              cwd=ROOT, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, check=False)
    if ancestor.returncode:
        raise RuntimeError("source-lock commit must descend from preregistration commit")
    if git_output("ls-tree", "-r", "--name-only", rev, "--", RUN).strip():
        raise RuntimeError("measured run present in source-lock commit")
    return rev, payload


def analysis_frame(rows: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict[str, int]]:
    union = pd.read_parquet(ROOT / SOURCES["union"]["path"], columns=[
        "REF_AREA", "MEASURE", "UNIT_MEASURE", "period", "value", "OBS_STATUS"])
    union = union.loc[union.MEASURE.eq("TUD") & union.UNIT_MEASURE.eq("PT_SAL")
                      & union.OBS_STATUS.eq("A") & union.value.between(0, 100)]
    u = {(str(c), int(y)): float(v) for c, y, _, _, v, _ in
         union[["REF_AREA", "period", "MEASURE", "UNIT_MEASURE", "value", "OBS_STATUS"]].itertuples(index=False, name=None)}
    gdp = pd.read_parquet(ROOT / SOURCES["gdp_pc"]["path"], columns=[
        "country_iso3", "year", "value", "obs_status"])
    gdp = gdp.loc[gdp.country_iso3.astype(str).str.fullmatch(r"[A-Z]{3}")].copy()
    g = {(str(c), int(y)): math.log(float(v)) for c, y, v, s in gdp.itertuples(index=False, name=None)
         if pd.notna(v) and np.isfinite(v) and v > 0 and blank_status(s)}
    cols = ["REF_AREA", "period", *outcome_dimensions(), "value", "OBS_STATUS"]
    outcome = pd.read_parquet(ROOT / SOURCES["unemployment"]["path"], columns=cols)
    for col, value in outcome_dimensions().items():
        outcome = outcome.loc[outcome[col].eq(value)]
    if outcome.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate selected outcome observation")
    o = {(str(c), int(y)): (v, status) for c, y, v, status in outcome[
        ["REF_AREA", "period", "value", "OBS_STATUS"]].itertuples(index=False, name=None)}
    valid = []
    invalid = non_actual = 0
    for c, y in rows:
        baseline, bs = o[(c, y)]
        followup, fs = o[(c, y+2)]
        if str(bs).strip() != "A" or str(fs).strip() != "A":
            non_actual += 1
            continue
        if not all(pd.notna(v) and np.isfinite(v) and 0 <= float(v) <= 100
                   for v in (baseline, followup)):
            invalid += 1
            continue
        valid.append({"country_iso3": c, "year": y, "outcome": float(followup)-float(baseline),
                      "baseline": float(baseline), "union10": u[(c, y)]/10,
                      "union_pp": u[(c, y)], "log_gdp_pc": g[(c, y)]})
    frame = pd.DataFrame(valid, columns=["country_iso3", "year", "outcome", "baseline",
                                         "union10", "union_pp", "log_gdp_pc"])
    return frame, {"roster_rows": len(rows), "invalid_or_missing_outcome_pairs": invalid,
                   "non_actual_outcome_status_pairs": non_actual}


def pre_estimation_gate(frame: pd.DataFrame) -> dict[str, bool]:
    names = ("min_valid_rows", "min_valid_countries", "min_countries_with_three_windows",
             "min_distinct_anchors", "min_rows_each_present_anchor", "max_one_anchor_share",
             "min_union_density_iqr_pp", "min_countries_with_union_range_3pp")
    if frame.empty:
        return {name: False for name in names}
    counts = frame.country_iso3.value_counts()
    waves = frame.year.value_counts()
    ranges = frame.groupby("country_iso3").union_pp.agg(lambda x: x.max()-x.min())
    measures = {"min_valid_rows": len(frame), "min_valid_countries": len(counts),
                "min_countries_with_three_windows": int((counts >= 3).sum()),
                "min_distinct_anchors": len(waves),
                "min_rows_each_present_anchor": int(waves.min()),
                "max_one_anchor_share": float(waves.max()/len(frame)),
                "min_union_density_iqr_pp": float(frame.union_pp.quantile(.75)-frame.union_pp.quantile(.25)),
                "min_countries_with_union_range_3pp": int((ranges >= 3).sum())}
    return {name: (value <= FLOOR[name] if name.startswith("max_") else value >= FLOOR[name])
            for name, value in measures.items()}


def concentration(model: Any, frame: pd.DataFrame) -> dict[str, float | None]:
    X = np.asarray(model.model.exog, dtype=float)
    ix = model.model.exog_names.index("union10")
    x = X[:, ix]
    Z = np.delete(X, ix, axis=1)
    residual = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    weight = residual*residual
    total = float(weight.sum())
    if total <= 1e-12:
        return {"max_top_one_percent_partialled_x_share": None,
                "max_top_country_partialled_x_share": None}
    k = max(1, math.ceil(len(weight)*.01))
    by_country = pd.DataFrame({"country": frame.country_iso3.to_numpy(), "weight": weight}).groupby("country").weight.sum()
    return {"max_top_one_percent_partialled_x_share": float(np.sort(weight)[-k:].sum()/total),
            "max_top_country_partialled_x_share": float(by_country.max()/total)}


def estimate(frame: pd.DataFrame) -> tuple[dict[str, Any] | None, dict[str, float | None]]:
    model = smf.ols("outcome ~ union10 + baseline + log_gdp_pc + C(country_iso3) + C(year)",
                    data=frame).fit()
    X = model.model.exog
    empty = {"max_top_one_percent_partialled_x_share": None,
             "max_top_country_partialled_x_share": None}
    if np.linalg.matrix_rank(X) != X.shape[1]:
        return None, empty
    clustered = model.get_robustcov_results(cov_type="cluster", groups=frame.country_iso3,
                                             use_correction=True, df_correction=True, use_t=True)
    ix = model.model.exog_names.index("union10")
    beta, se = float(clustered.params[ix]), float(clustered.bse[ix])
    groups = int(frame.country_iso3.nunique())
    if not np.isfinite(beta) or not np.isfinite(se) or se <= 0 or groups < 2:
        return None, empty
    df = groups-1
    p = float(2*student_t.sf(abs(beta/se), df))
    radius = float(student_t.ppf(1-ALPHA/2, df)*se)
    return ({"coefficient": beta, "std_error": se, "p_value_two_sided": p,
             "confidence_level": 1-ALPHA, "confidence_interval": [beta-radius, beta+radius],
             "n_rows": len(frame), "n_countries": groups, "df_inference": df,
             "model_rank": int(np.linalg.matrix_rank(X)),
             "method": "OLS with country/anchor-year FE; country-cluster CR1; Student t(G-1)"},
            concentration(model, frame))


def verdict(primary: dict[str, Any] | None, gates: dict[str, bool]) -> tuple[str, str]:
    if primary is None or not all(gates.values()):
        return "INCONCLUSIVE", "frozen coverage, design, influence, or estimator floor failed"
    beta, p = primary["coefficient"], primary["p_value_two_sided"]
    if p <= ALPHA and beta >= MEANINGFUL_BETA:
        return "SUPPORTED", "positive direction, p, and practical-effect gates passed"
    if p <= ALPHA and beta <= -MEANINGFUL_BETA:
        return "REFUTED", "opposite direction, p, and practical-effect gates passed"
    return "PARTIAL", "estimable association did not clear a frozen directional gate"


def outcome(rows: list[tuple[str, int]], prereg_rev: str, lock_rev: str, stamp: str) -> dict[str, Any]:
    frame, count = analysis_frame(rows)
    before_fit = pre_estimation_gate(frame)
    attempted = all(before_fit.values())
    if attempted:
        primary, influence = estimate(frame)
    else:
        primary = None
        influence = {"max_top_one_percent_partialled_x_share": None,
                     "max_top_country_partialled_x_share": None}
    sample = {**count, "valid_rows": len(frame),
              "valid_reporter_economies": int(frame.country_iso3.nunique()),
              "estimator_attempted": attempted, "outcome_values_read_after_lock": True,
              **influence}
    gates = {**before_fit, "full_rank_and_estimable_uncertainty": primary is not None,
             **{name: influence[name] is not None and influence[name] <= FLOOR[name]
                for name in influence}}
    if not all(gates.values()):
        primary = None  # No coefficient is published from an inconclusive run.
    status, reason = verdict(primary, gates)
    return {"hypothesis_id": ID, "replaces_component_of": OLD_ID,
            "family_id": FAMILY, "verdict": status, "verdict_label": status,
            "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER,
            "preregistration_commit": prereg_rev, "source_lock_commit": lock_rev,
            "source_lock": LOCK, "template": "panel_fe", "sample": sample,
            "gate_checks": gates, "primary": primary, "p_max_two_sided": ALPHA,
            "meaningful_beta_min_abs": MEANINGFUL_BETA,
            "data_status": {"variables_missing": [], "input_vintages": SOURCES},
            "limitations": LIMITATIONS, "correction": CORRECTION}


def artifact_bytes(result: dict[str, Any]) -> dict[str, bytes]:
    stamp = result["run_utc"]
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": ID, "path": SPEC, "topic": "labour"},
              "preregistration": {"spec_commit": result["preregistration_commit"],
                                  "source_lock_commit": result["source_lock_commit"],
                                  "family_id": FAMILY, "family_size": 1,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": STEELMAN},
              "reproduction": {"runner": RUNNER, "run_dir": RUN,
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                          "reason": result["verdict_reason"]},
              "data": {"inputs": SOURCES, "sample": result["sample"]},
              "results": {"primary": result["primary"], "gate_checks": result["gate_checks"]},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    card = (f"# {ID}\n\n**Verdict: {result['verdict']}** — {result['verdict_reason']}.\n\n"
            f"This tests the low-education-unemployment component of archived `{OLD_ID}`. "
            f"The old placeholder remains archived.\n\n"
            f"Complete rows: {result['sample']['valid_rows']}; reporter economies: "
            f"{result['sample']['valid_reporter_economies']}.\n")
    if result["primary"]:
        p = result["primary"]
        card += (f"Coefficient per 10 pp union density: {p['coefficient']:+.6g}; "
                 f"country-cluster SE {p['std_error']:.6g}; two-sided p "
                 f"{p['p_value_two_sided']:.6g}; 99% interval "
                 f"[{p['confidence_interval'][0]:+.6g}, {p['confidence_interval'][1]:+.6g}].\n")
    card += "\nNo causal, school, policy, or featured credit is assigned.\n"
    manifest = {"schema": "ieset-run-manifest-v1", "generated_utc": stamp,
                "hypothesis_id": ID, "runner": RUNNER,
                "preregistration_commit": result["preregistration_commit"],
                "source_lock_commit": result["source_lock_commit"],
                "inputs": SOURCES, "correction": CORRECTION}
    metrics = pd.DataFrame([{"hypothesis_id": ID, "verdict": result["verdict"],
                             "coefficient": None if result["primary"] is None else result["primary"]["coefficient"],
                             "std_error": None if result["primary"] is None else result["primary"]["std_error"],
                             "p_value": None if result["primary"] is None else result["primary"]["p_value_two_sided"],
                             "n_rows": result["sample"]["valid_rows"],
                             "n_countries": result["sample"]["valid_reporter_economies"]}])
    table = io.BytesIO()
    metrics.to_parquet(table, index=False)
    copy = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\n"
            "root = Path(__file__).resolve().parents[3]\n"
            f"subprocess.run(['python3', '{RUNNER}', '--verify'], cwd=root, check=True)\n")
    return {"diagnostics.json": (json.dumps(result, indent=2, sort_keys=True)+"\n").encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "result_card.md": card.encode(), "hypothesis.yaml": (ROOT / SPEC).read_bytes(),
            "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "replication.py": copy.encode(), "coefficients.parquet": table.getvalue(),
            "chart_data.json": (json.dumps({"hypothesis_id": ID, "primary": result["primary"],
                                             "verdict": result["verdict"]}, indent=2, sort_keys=True)+"\n").encode()}


def run_or_verify(verify: bool) -> None:
    lock_rev, lock = source_lock_commit()
    rows = source_keys()
    if roster_bytes(rows) != (ROOT / ROSTER).read_bytes():
        raise RuntimeError("source keys differ from registered roster")
    dest = ROOT / RUN
    if verify:
        diagnostic = dest / "diagnostics.json"
        if not diagnostic.is_file():
            raise RuntimeError("missing measured run for verification")
        stamp = json.loads(diagnostic.read_text())["run_utc"]
    else:
        if dest.exists():
            raise RuntimeError("measured run already exists; refusing overwrite")
        stamp = datetime.now(timezone.utc).isoformat()
    result = outcome(rows, lock["preregistration_commit"], lock_rev, stamp)
    expected = artifact_bytes(result)
    if verify:
        observed = {path.name for path in dest.iterdir() if path.is_file()}
        if observed != set(expected):
            raise RuntimeError("run artifact set mismatch")
        for name, raw in expected.items():
            if (dest / name).read_bytes() != raw:
                raise RuntimeError(f"exact replay mismatch: {name}")
        print("Exact replay passed: eight artifacts")
    else:
        dest.mkdir(parents=True)
        for name, raw in expected.items():
            (dest / name).write_bytes(raw)
        print(json.dumps({"verdict": result["verdict"], "sample": result["sample"],
                          "primary": result["primary"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ("build-roster", "preflight", "lock", "run", "verify"):
        group.add_argument("--"+flag, action="store_true")
    args = parser.parse_args()
    if args.build_roster:
        source_check()
        path = ROOT / ROSTER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(roster_bytes(source_keys()))
        print(json.dumps({"roster_sha256": sha256(path)}, indent=2))
    elif args.preflight:
        print(json.dumps(key_preflight(), indent=2))
    elif args.lock:
        rev = registration_commit()
        preflight = key_preflight()
        path = ROOT / LOCK
        if path.exists():
            raise RuntimeError("source lock already exists")
        path.write_text(json.dumps(lock_payload(rev, preflight), indent=2, sort_keys=True)+"\n")
        print(f"Source lock written after preregistration commit {rev}")
    elif args.run:
        run_or_verify(False)
    elif args.verify:
        run_or_verify(True)


if __name__ == "__main__":
    main()
