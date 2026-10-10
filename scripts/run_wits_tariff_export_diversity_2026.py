#!/usr/bin/env python3
"""Guarded three-outcome WITS tariff/export-diversity calibration."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wits_tariff_export_diversity_2026_10_10"
RUNNER = "scripts/run_wits_tariff_export_diversity_2026.py"
TEST = "tests/test_wits_tariff_export_diversity_2026.py"
PLAN = "engine/audits/wits_tariff_export_diversity_prereg_2026-10-10.md"
SUMMARY = "engine/audits/wits_tariff_export_diversity_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/wits_tariff_export_diversity_key_roster_2026.csv"
ROSTER_SHA = "c0d49eac18fbc53fc1a26bb6426a7e3d090f123e1953d805fc6937c6854ce327"
LOCK = "data/pinned_evidence/wits_tariff_export_diversity.manifest.json"
CASE_ORDER = ("exported_hs6_count", "export_market_hhi", "export_product_hhi")
CASES = {
    "exported_hs6_count": {"id": "wits_tariff_decline_exported_hs6_breadth_forward_2026", "size": .01,
                           "kind": "count", "selector": {"partner_iso3": "WLD", "product_code": "999999",
                           "indicator_id": "NMBR-XPRT-HS6-PRDCT"}},
    "export_market_hhi": {"id": "wits_tariff_decline_export_market_diversity_forward_2026", "size": .005,
                          "kind": "hhi", "selector": {"partner_iso3": "999", "product_code": "999999",
                          "indicator_id": "HH-MKT-CNCNTRTN-NDX"}},
    "export_product_hhi": {"id": "wits_tariff_decline_export_product_diversity_forward_2026", "size": .005,
                           "kind": "hhi", "selector": {"partner_iso3": "WLD", "classification": "H0",
                           "product_cluster": "Tier3"}},
}
SOURCES = {
    "tariff": {"series_id": "weighted_mean_applied_tariff", "path": "data/vintages/wits/weighted_mean_applied_tariff@2026-07-23T151540Z.parquet", "sha256": "73520e0da6a44048e51a64671c97369aadf160130937f351f90375fb86b0e010", "manifest": "data/manifests/fetch_run_2026-07-23T151550Z.yaml", "manifest_sha256": "96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5"},
    "income": {"series_id": "NY.GDP.PCAP.KD", "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet", "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f", "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml", "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "exported_hs6_count": {"series_id": "unique_hs6_products", "path": "data/vintages/wits/unique_hs6_products@2026-07-23T153652Z.parquet", "sha256": "29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934", "manifest": "data/manifests/fetch_run_2026-07-23T153659Z.yaml", "manifest_sha256": "542aacbcc80b1856262eda14f37d0532c7a14611c8b9d698ab516529942d0b73"},
    "export_market_hhi": {"series_id": "product_concentration", "path": "data/vintages/wits/product_concentration@2026-07-23T151543Z.parquet", "sha256": "c59b180e07f484546e131fa6a4f47a725ecc790effbb3d395e5d2c4e36381949", "manifest": "data/manifests/fetch_run_2026-07-23T151550Z.yaml", "manifest_sha256": "96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5"},
    "export_product_hhi": {"series_id": "export_product_hhi_wits", "path": "data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet", "sha256": "88528dd4d46c0efebc928f2c4c3ac63d2b60bee5505d313184342b8e071b7d47", "manifest": "data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json", "manifest_sha256": "280a99ce5e9458f55b28009ec089b5b258600381524c53c880eeb9a67a09dd69"},
}
MIN_ROWS, MIN_REPORTERS, MIN_YEARS = 1000, 90, 5
MIN_DECLINE, MIN_DECLINE_REPORTERS = 200, 70
MIN_INCREASE, MIN_INCREASE_REPORTERS = 45, 25
MAX_TOP_ROWS, MAX_TOP_REPORTER = .30, .20
P_MAX = .01 / 3
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 3, "family_alpha": .01, "p_max_two_sided": P_MAX,
              "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0, "featured_eligible": False}
LIMITATIONS = ["Weighted applied tariff changes may reflect changing import shares, not statutory tariff changes.",
               "Trade prospects, resources, currency, agreements, income and measurement may jointly move tariffs and exports.",
               "Three-year panels overlap; reporter clustering does not identify a causal effect.",
               "WITS export series have no observation-status or method-break field; product HHI is mirrored Comtrade data.",
               "Three outcomes share sources and are not independent confirmations; family correction does not cover archive-wide selection.",
               "No causal, policy-effect, school, position, or featured credit applies to any verdict."]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    revisions = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if len(revisions) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}: {revisions}")
    return revisions[0]


def frozen(relative: str, revision: str) -> None:
    if (ROOT / relative).read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file changed: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec(case: str) -> str:
    return f"hypotheses/trade/{CASES[case]['id']}.yaml"


def steelman(case: str) -> str:
    return f"hypotheses/steelman/{CASES[case]['id']}.md"


def run_dir(case: str) -> str:
    return f"engine/runs/{CASES[case]['id']}"


def registration_commit() -> str:
    files = [PLAN, ROSTER, RUNNER, TEST]
    for case in CASE_ORDER:
        files.extend([spec(case), steelman(case)])
    revisions = {first_addition(file) for file in files}
    if len(revisions) != 1:
        raise RuntimeError(f"registration files not first added together: {revisions}")
    revision = revisions.pop()
    for file in files:
        frozen(file, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("registration commit already has source lock")
    for case in CASE_ORDER:
        if git("ls-tree", "-r", "--name-only", revision, "--", run_dir(case)).strip():
            raise RuntimeError("registration commit already has result")
    return revision


def source_checks(source_root: Path) -> dict[str, dict[str, str]]:
    selected = {}
    for role, source in SOURCES.items():
        path = source_root / source["path"]
        manifest = source_root / source["manifest"]
        if not path.is_file() or digest(path) != source["sha256"]:
            raise RuntimeError(f"source hash mismatch: {role}")
        if not manifest.is_file() or digest(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"manifest hash mismatch: {role}")
        entries = (json.loads(manifest.read_text()) if manifest.suffix == ".json" else yaml.safe_load(manifest.read_text()))["entries"]
        if not any(e.get("series_id") == source["series_id"] and e.get("sha256") == source["sha256"] for e in entries):
            raise RuntimeError(f"selected source not in pinned fetch manifest: {role}")
        selected[role] = source
    return selected


def roster_rows() -> dict[str, list[tuple[str, int]]]:
    path = ROOT / ROSTER
    if digest(path) != ROSTER_SHA:
        raise RuntimeError("key roster hash mismatch")
    rows = {case: [] for case in CASE_ORDER}
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["case", "country_iso3", "year"]:
            raise RuntimeError("key roster schema changed")
        for row in reader:
            if row["case"] not in rows:
                raise RuntimeError("unexpected case in key roster")
            rows[row["case"]].append((row["country_iso3"], int(row["year"])))
    if any(r != sorted(set(r)) for r in rows.values()):
        raise RuntimeError("duplicate or unsorted key roster")
    return rows


def source_keys(source_root: Path, case: str) -> set[tuple[str, int]]:
    sel = CASES[case]["selector"]
    columns = ["country_iso3", "year", *sel]
    table = pq.read_table(source_root / SOURCES[case]["path"], columns=columns).to_pandas()
    for key, value in sel.items():
        table = table.loc[table[key].eq(value)]
    keys = list(zip(table.country_iso3.astype(str), table.year.astype(int)))
    if len(keys) != len(set(keys)):
        raise RuntimeError(f"duplicate selected keys: {case}")
    return set(keys)


def covariate_maps(source_root: Path) -> tuple[dict[tuple[str, int], float], dict[tuple[str, int], float]]:
    maps = []
    for role in ("tariff", "income"):
        frame = pq.read_table(source_root / SOURCES[role]["path"], columns=["country_iso3", "year", "value", "obs_status"]).to_pandas()
        valid = frame.value.notna() & frame.value.map(lambda x: x is not None and math.isfinite(float(x))) & frame.obs_status.fillna("").eq("")
        if role == "income":
            valid &= frame.value.gt(0)
        values = {(str(c), int(y)): float(v) for c, y, v in frame.loc[valid, ["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
        maps.append(values)
    return maps[0], maps[1]


def candidate_panels(source_root: Path) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    roster = roster_rows()
    tariff, income = covariate_maps(source_root)
    panels, report = {}, {}
    for case in CASE_ORDER:
        keys = source_keys(source_root, case)
        computed = []
        for country, year in roster[case]:
            if (2000 <= year <= 2016 and all((country, z) in tariff and (country, z) in income for z in (year-3, year))
                    and all((country, z) in keys for z in (year-3, year, year+3))):
                computed.append((country, year))
        if computed != roster[case]:
            raise RuntimeError(f"candidate key roster differs from frozen case: {case}")
        data = []
        for country, year in computed:
            delta = tariff[country, year-3] - tariff[country, year]
            data.append({"country_iso3": country, "year": year, "delta_tariff_decline": delta,
                         "decline": int(delta >= 2), "increase": int(delta <= -2),
                         "log_gdp_pc": math.log(income[country, year]),
                         "prior_gdp_change": math.log(income[country, year]) - math.log(income[country, year-3])})
        panels[case] = pd.DataFrame(data)
        report[case] = {"key_only_rows": len(data), "key_only_reporters": len({c for c, _ in computed}),
                        "material_declines": sum(x["decline"] for x in data),
                        "material_decline_reporters": len({x["country_iso3"] for x in data if x["decline"]}),
                        "material_increases": sum(x["increase"] for x in data),
                        "material_increase_reporters": len({x["country_iso3"] for x in data if x["increase"]}),
                        "outcome_values_opened": False}
    return panels, report


def lock_payload(registration: str, selected: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"schema": "ieset-narrow-source-lock-v1", "family_id": FAMILY,
            "preregistration_commit": registration, "selected_sources": selected,
            "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def check_lock(registration: str, selected: dict[str, Any], preflight: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if not path.is_file() or json.loads(path.read_text()) != lock_payload(registration, selected, preflight):
        raise RuntimeError("missing or changed source lock")
    revision = first_addition(LOCK)
    if revision == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock must descend from registration in separate commit")
    frozen(LOCK, revision)
    for case in CASE_ORDER:
        if git("ls-tree", "-r", "--name-only", revision, "--", run_dir(case)).strip():
            raise RuntimeError("source lock already contains results")
    return revision


def valid_outcome(value: Any, kind: str) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(x):
        return None
    if kind == "count":
        return x if x >= 0 and x.is_integer() else None
    return x if 0 <= x <= 1 else None


def measured_panel(source_root: Path, case: str, candidate: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    sel = CASES[case]["selector"]
    frame = pd.read_parquet(source_root / SOURCES[case]["path"], columns=["country_iso3", "year", "value", *sel])
    for key, value in sel.items():
        frame = frame.loc[frame[key].eq(value)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate measured source key: {case}")
    values = {(str(c), int(y)): valid_outcome(v, CASES[case]["kind"]) for c, y, v in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    rows, invalid = [], 0
    for row in candidate.itertuples(index=False):
        before, base, after = [values.get((row.country_iso3, z)) for z in (row.year-3, row.year, row.year+3)]
        if before is None or base is None or after is None:
            invalid += 1
            continue
        transform = math.log1p if CASES[case]["kind"] == "count" else float
        b, m, a = map(transform, (before, base, after))
        sign = 1 if CASES[case]["kind"] == "count" else -1
        rows.append({"country_iso3": row.country_iso3, "year": row.year,
                     "delta_tariff_decline": row.delta_tariff_decline, "decline": row.decline,
                     "increase": row.increase, "log_gdp_pc": row.log_gdp_pc,
                     "prior_gdp_change": row.prior_gdp_change,
                     "baseline_export": m, "prior_export_change": sign*(m-b),
                     "forward_change": sign*(a-m)})
    panel = pd.DataFrame(rows)
    before_floor = len(panel)
    if not panel.empty:
        years = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(years).ge(MIN_YEARS)].reset_index(drop=True)
    gate = {"key_only_rows": len(candidate), "invalid_or_missing_selected_triples": invalid,
            "complete_triples_before_reporter_floor": before_floor,
            "valid_rows": len(panel), "valid_reporters": int(panel.country_iso3.nunique()) if not panel.empty else 0,
            "material_declines": int(panel.decline.sum()) if not panel.empty else 0,
            "material_decline_reporters": int(panel.loc[panel.decline.eq(1), "country_iso3"].nunique()) if not panel.empty else 0,
            "material_increases": int(panel.increase.sum()) if not panel.empty else 0,
            "material_increase_reporters": int(panel.loc[panel.increase.eq(1), "country_iso3"].nunique()) if not panel.empty else 0,
            "selected_outcome_values_opened_after_lock": True,
            "outcome_status_field_available": False}
    return panel, gate


def concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    formula = "delta_tariff_decline ~ baseline_export + prior_export_change + log_gdp_pc + prior_gdp_change + C(country_iso3) + C(year)"
    try:
        residual = np.asarray(smf.ols(formula, data=panel).fit().resid, dtype=float)
        squares = residual ** 2
        total = float(squares.sum())
        if total <= 0 or not math.isfinite(total):
            return None
        n = max(1, int(math.ceil(.01 * len(panel))))
        top_rows = float(np.sort(squares)[-n:].sum() / total)
        top_reporter = float(pd.DataFrame({"country": panel.country_iso3, "square": squares}).groupby("country").square.sum().max() / total)
        return top_rows, top_reporter
    except (ValueError, np.linalg.LinAlgError):
        return None


def estimate(case: str, panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_reporters"] < MIN_REPORTERS or
        gate["material_declines"] < MIN_DECLINE or gate["material_decline_reporters"] < MIN_DECLINE_REPORTERS or
        gate["material_increases"] < MIN_INCREASE or gate["material_increase_reporters"] < MIN_INCREASE_REPORTERS):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen sample or material-movement floor failed", "primary": None}
    shares = concentration(panel)
    gate["residual_treatment_shares"] = {"top_one_percent_rows": shares[0], "top_reporter": shares[1]} if shares else None
    if shares is None or shares[0] > MAX_TOP_ROWS or shares[1] > MAX_TOP_REPORTER:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen residual-treatment concentration floor failed", "primary": None}
    model = smf.ols("forward_change ~ delta_tariff_decline + baseline_export + prior_export_change + log_gdp_pc + prior_gdp_change + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "fixed design is rank deficient", "primary": None}
    reporters = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3, "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["delta_tariff_decline"]), float(fit.bse["delta_tariff_decline"])
    if not all(math.isfinite(x) for x in (beta, se)) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "invalid cluster uncertainty", "primary": None}
    p = float(2*student_t.sf(abs(beta/se), reporters-1))
    critical = float(student_t.ppf(.995, reporters-1))
    primary = {"beta_oriented_outcome_per_tariff_point": beta, "std_error": se,
               "p_value_two_sided": p, "confidence_level": .99,
               "confidence_interval": [beta-critical*se, beta+critical*se],
               "n_rows": len(panel), "n_reporters": reporters, "df_inference": reporters-1,
               "model_rank": int(fit.model.rank),
               "method": "reporter/year FE OLS with own baseline and pretrend and real-income controls; reporter-cluster CR1 Student t(G-1)"}
    size = CASES[case]["size"]
    if beta >= size and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive association clears family-adjusted p and practical-size gates"
    elif beta <= -size and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears family-adjusted p and practical-size gates"
    else:
        verdict, reason = "PARTIAL", "estimable association misses the frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(case: str, result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    study = CASES[case]["id"]
    source_subset = {role: SOURCES[role] for role in ("tariff", "income", case)}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": study, "path": spec(case), "topic": "trade"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 3, "key_roster": ROSTER,
                                  "key_roster_sha256": ROSTER_SHA, "steelman": steelman(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_dir(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(), "reason": result["reason"]},
              "data": {"inputs": source_subset, "sample": result["gate"]},
              "results": {"primary": result["primary"]}, "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": study, "family_id": FAMILY, "verdict": result["verdict"],
                   "verdict_label": result["verdict"], "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER, "preregistration_commit": registration,
                   "source_lock_commit": lock_commit, "source_lock": LOCK, "template": "panel_fe",
                   "preflight": result["gate"], "primary": result["primary"],
                   "p_max_two_sided": P_MAX, "practical_beta_min": CASES[case]["size"],
                   "data_status": {"variables_missing": [], "input_vintages": list(source_subset.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": study, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": result["verdict"],
                "vintages": list(source_subset.values()), "derived_panel": result["gate"], "correction": CORRECTION}
    primary = result["primary"]
    card = (f"# Result card: {study}\n\nVerdict: **{result['verdict']}**. {result['reason']}.\n\n"
            f"Frozen registration `{registration}`; source lock `{lock_commit}`. "
            f"Complete pairs {result['gate']['valid_rows']} / {result['gate']['valid_reporters']} reporter economies.\n")
    if primary:
        card += (f"\nOriented outcome coefficient {primary['beta_oriented_outcome_per_tariff_point']:+.6g} "
                 f"per one tariff percentage-point decline; reporter-cluster SE {primary['std_error']:.6g}; "
                 f"two-sided p {primary['p_value_two_sided']:.6g}; 99% CI {primary['confidence_interval']}.\n")
    card += ("\nOne of three related fixed outcomes. P<=0.01/3 and the prespecified practical threshold "
             "are required for a directional verdict. Descriptive only; zero causal, policy, school, "
             "position and featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": study, "family_id": FAMILY, "verdict": result["verdict"], "primary_coefficient": primary}
    coefficients = ([{"term": "three_year_weighted_mean_applied_tariff_decline",
                     "coefficient": primary["beta_oriented_outcome_per_tariff_point"],
                     "std_error": primary["std_error"], "p_value_two_sided": primary["p_value_two_sided"],
                     "confidence_level": primary["confidence_level"],
                     "confidence_interval": primary["confidence_interval"],
                     "n_rows": primary["n_rows"], "n_reporters": primary["n_reporters"],
                     "df_inference": primary["df_inference"], "model_rank": primary["model_rank"],
                     "method": primary["method"]}] if primary else [])
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# Applied tariffs and later export diversity: descriptive family", "",
             f"Registration `{registration}`; source lock `{lock_commit}`. All three tests share sources and family correction p<=0.01/3.", "",
             "| Outcome | Verdict | Rows / reporters | Oriented beta per tariff point | Two-sided p |", "| --- | --- | ---: | ---: | ---: |"]
    for case in CASE_ORDER:
        result = results[case]
        primary = result["primary"]
        beta = f"{primary['beta_oriented_outcome_per_tariff_point']:+.6g}" if primary else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary else "not estimated"
        gate = result["gate"]
        lines.append(f"| {case} | {result['verdict']} | {gate['valid_rows']} / {gate['valid_reporters']} | {beta} | {p} |")
    lines += ["", "Market HHI and product HHI are distinct. The local `product_concentration` source is market HHI (`HH-MKT-CNCNTRTN-NDX`).",
              "All outcomes are descriptive. No causal, tariff-policy, school, position or featured credit follows from a verdict.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if (ROOT / SUMMARY).exists() or any((ROOT / run_dir(case)).exists() for case in CASE_ORDER):
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for case in CASE_ORDER:
        payload = artifact_payload(case, results[case], registration, lock_commit, stamp)
        folder = ROOT / run_dir(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2, allow_nan=False)+"\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2, allow_nan=False)+"\n")
        pd.DataFrame(payload["coefficients"], columns=["term", "coefficient", "std_error", "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows", "n_reporters", "df_inference", "model_rank", "method"]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def normalized(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalized(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalized(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: keys differ")
        for k, v in expected.items():
            equal_close(actual[k], v, f"{label}.{k}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: length differs")
        for i, v in enumerate(expected):
            equal_close(actual[i], v, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric differs")
    elif actual != expected:
        raise AssertionError(f"{label}: value differs")


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for case in CASE_ORDER:
        folder = ROOT / run_dir(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(case, results[case], registration, lock_commit, saved["run_utc"])
        equal_close(saved, payload["diagnostics"], f"{case}.diagnostics")
        equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"], f"{case}.manifest")
        equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"], f"{case}.packet")
        equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"], f"{case}.chart")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec(case)).read_bytes() or
            (folder / "result_card.md").read_text() != payload["card"] or
            (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"{case}: text artifacts differ")
        equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"), payload["coefficients"], f"{case}.coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("preflight", "lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.source_root != ROOT and not args.preflight:
        parser.error("--source-root override is only for read-only preflight")
    selected = source_checks(args.source_root)
    candidates, preflight = candidate_panels(args.source_root)
    if args.preflight:
        print(json.dumps(preflight, indent=2, sort_keys=True, allow_nan=False))
        return 0
    registration = registration_commit()
    if args.lock:
        path = ROOT / LOCK
        if path.exists():
            raise FileExistsError(LOCK)
        path.write_text(json.dumps(lock_payload(registration, selected, preflight), indent=2, sort_keys=True, allow_nan=False)+"\n")
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    lock_commit = check_lock(registration, selected, preflight)
    results = {}
    for case in CASE_ORDER:
        panel, gate = measured_panel(ROOT, case, candidates[case])
        results[case] = estimate(case, panel, gate)
    if args.run:
        write_artifacts(results, registration, lock_commit)
        print({case: results[case]["verdict"] for case in CASE_ORDER})
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", {case: results[case]["verdict"] for case in CASE_ORDER})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
