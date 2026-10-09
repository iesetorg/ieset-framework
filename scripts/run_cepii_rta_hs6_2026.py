#!/usr/bin/env python3
"""Frozen CEPII RTA-partner expansion / WITS HS6 descriptive calibration.

Source and key checks do not open the WITS measured column. The measured run
requires a strict earlier registration commit and a separate source-lock commit.
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
HYPOTHESIS_ID = "cepii_rta_partner_expansion_export_hs6_change_2026"
SPEC_REL = f"hypotheses/trade/{HYPOTHESIS_ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HYPOTHESIS_ID}.md"
PLAN_REL = "engine/audits/cepii_rta_hs6_prereg_2026-10-09.md"
RUNNER_REL = "scripts/run_cepii_rta_hs6_2026.py"
ROSTER_REL = "data/pinned_evidence/cepii_rta_hs6_key_roster_2026.csv"
LOCK_REL = "data/pinned_evidence/cepii_rta_hs6_2026.manifest.json"
RUN_REL = f"engine/runs/{HYPOTHESIS_ID}"
CEPII_REL = "data/vintages/cepii/fta_accession_indicator@2026-05-15T172455Z.parquet"
WITS_REL = "data/vintages/wits/unique_hs6_products@2026-07-23T153652Z.parquet"
RAW_CEPII_REL = "data/raw/cepii/Gravity_csv_V202211.zip"
CEPII_MANIFEST = "data/manifests/fetch_run_2026-05-15T172455Z_cepii_fta_accession.yaml"
WITS_MANIFEST = "data/manifests/fetch_run_2026-07-23T153659Z.yaml"
CEPII_SHA256 = "3125c268836d9e1e66d018d4b7d0acf3a7c918bd9f7fd77c3814109f65c09645"
WITS_SHA256 = "29db44b85d263bfc92307182b19f3baf4073dae446e5c3af37d82a284bfb2934"
RAW_CEPII_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
ROSTER_SHA256 = "57aebe9d5cc9012777b93ed2bd5331313b853857c3913bfaf0850ba963f10ebe"
EVENT_SHA256 = "1f41c274a8605425eac89875e4d68a94db935b9ef74d00e8c4f70bf38b73a239"
CONTROL_SHA256 = "8a954147e2af8d49fef91a714941bb8e2cbda27eec1560c02368ba93a64ad082"
P_MAX = 0.005
EFFECT_MIN = math.log(1.05)
MIN_EVENT_ROWS = 100
MIN_EVENT_COUNTRIES = 50
MIN_CONTROL_ROWS = 800
MIN_CONTROL_COUNTRIES = 80
MIN_EVENT_COHORTS = 15
ROSTER_HEADER = "role,country_iso3,year\n"
WITS_DIMS = {
    "freq_id": "A",
    "partner_iso3": "WLD",
    "product_code": "999999",
    "indicator_id": "NMBR-XPRT-HS6-PRDCT",
    "series_id": "unique_hs6_products",
}
SOURCES = {
    "treatment": {"publisher": "cepii", "series_id": "fta_accession_indicator",
                  "path": CEPII_REL, "sha256": CEPII_SHA256, "manifest": CEPII_MANIFEST},
    "outcome": {"publisher": "wits", "series_id": "unique_hs6_products",
                "path": WITS_REL, "sha256": WITS_SHA256, "manifest": WITS_MANIFEST},
}
CORRECTION = {
    "disposition": "descriptive_calibration_only",
    "school_score_eligible": False,
    "school_score_credit": 0,
    "policy_score_eligible": False,
    "policy_score_credit": 0,
    "featured_eligible": False,
}
LIMITATIONS = [
    "Conditional country-panel association; no treaty, tariff-cut, or causal effect is identified.",
    "CEPII's constructed event is a net increase in RTA-covered partner count, not first accession or statutory tariff change.",
    "Controls have no nearby expansion but can retain older RTA coverage; agreement selection and reporting changes remain confounders.",
    "WITS counts exported HS6 product categories, not export complexity, trade value, or domestic choice.",
    "The old CEPII FTA-growth/openness PARTIAL result, CEPII FTA/private-investment PARTIAL result, consumer-choice proxy REFUTED result, and related registered WITS screens were visible before this question.",
    "The two-sided p<=0.005 local screen does not correct the complete visible research search; no policy, school, causal, or featured credit.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from its first commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted change to frozen file: {relative}")


def is_ancestor(older: str, newer: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT).returncode == 0


def registration_commit() -> str:
    frozen = [SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL, ROSTER_REL]
    commits = {first_addition(path) for path in frozen}
    if len(commits) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = commits.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RUN_REL).strip():
        raise RuntimeError("registration commit already contains a run artifact")
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text())
    threshold = spec["falsification"]["threshold"]
    required = {
        "p_max_two_sided": P_MAX, "absolute_log_effect_min": EFFECT_MIN,
        "min_event_rows": MIN_EVENT_ROWS, "min_event_countries": MIN_EVENT_COUNTRIES,
        "min_control_rows": MIN_CONTROL_ROWS, "min_control_countries": MIN_CONTROL_COUNTRIES,
        "min_event_cohorts": MIN_EVENT_COHORTS, "expected_event_rows_from_keys": 169,
        "expected_control_rows_from_keys": 1376, "roster_sha256": ROSTER_SHA256,
        "roster_path": ROSTER_REL, "school_score_eligible": False,
        "school_score_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    }
    if any(threshold.get(k) != v for k, v in required.items()):
        raise RuntimeError("registered decision thresholds differ from frozen runner")
    if (spec.get("hypothesis_id") != HYPOTHESIS_ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != [] or spec.get("linked_conditions") != []
            or spec.get("steelman") != STEELMAN_REL):
        raise RuntimeError("registered descriptive hypothesis content changed")
    for role, source in SOURCES.items():
        pin = threshold["source_files"][role]
        if pin != {k: source[k] for k in ("path", "sha256", "manifest")}:
            raise RuntimeError(f"registered source pin differs: {role}")
    return revision


def check_sources() -> None:
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} source SHA-256 mismatch")
        manifest = yaml.safe_load((ROOT / source["manifest"]).read_text())
        matches = [item for item in manifest.get("entries", [])
                   if item.get("publisher") == source["publisher"]
                   and item.get("series_id") == source["series_id"]
                   and item.get("parquet_path") == source["path"]]
        if len(matches) != 1:
            raise RuntimeError(f"{role} source manifest entry mismatch")
        if matches[0].get("sha256") not in (None, source["sha256"]):
            raise RuntimeError(f"{role} source manifest SHA-256 mismatch")
    if sha256(ROOT / RAW_CEPII_REL) != RAW_CEPII_SHA256:
        raise RuntimeError("raw CEPII Gravity archive SHA-256 mismatch")


def load_roster() -> list[tuple[str, str, int]]:
    raw = (ROOT / ROSTER_REL).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROSTER_SHA256 or not raw.startswith(ROSTER_HEADER.encode()):
        raise RuntimeError("frozen source-key roster SHA-256 or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    rows = [(r["role"], r["country_iso3"], int(r["year"])) for r in records]
    if (len(rows) != 1545 or rows != sorted(rows, key=lambda x: (x[2], x[1], x[0]))
            or len(set(rows)) != len(rows) or any(r not in {"event", "control"} or len(c) != 3
                                              or not 1993 <= y <= 2019 for r, c, y in rows)):
        raise RuntimeError("frozen source-key roster rows invalid")
    for role, count, expected in (("event", 169, EVENT_SHA256), ("control", 1376, CONTROL_SHA256)):
        subset = [row for row in rows if row[0] == role]
        data = (ROSTER_HEADER + "".join(f"{r},{c},{y}\n" for r, c, y in subset)).encode()
        if len(subset) != count or hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError(f"frozen {role} key roster mismatch")
    return rows


def key_preflight() -> dict[str, Any]:
    """Check source dimensions and every selected key without WITS values."""
    rows = load_roster()
    wits = pd.read_parquet(ROOT / WITS_REL, columns=["country_iso3", "year", *WITS_DIMS])
    if len(wits) != 5308 or any(not wits[col].eq(value).all() for col, value in WITS_DIMS.items()):
        raise RuntimeError("WITS dimension or row-count contract changed")
    if wits.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WITS reporter-year key")
    wits_keys = {(str(c), int(y)) for c, y in zip(wits.country_iso3, wits.year)}
    cepii = pd.read_parquet(ROOT / CEPII_REL, columns=["country_iso3", "year", "value"])
    if len(cepii) != 17739 or cepii.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("CEPII key/row-count contract changed")
    if not cepii.value.isin([0, 1]).all():
        raise RuntimeError("CEPII constructed event is no longer binary")
    events: dict[str, set[int]] = {}
    for c, y, v in zip(cepii.country_iso3, cepii.year, cepii.value):
        if int(y) >= 1990 and int(v) == 1:
            events.setdefault(str(c), set()).add(int(y))
    for role, country, year in rows:
        if any((country, y) not in wits_keys for y in range(year - 3, year + 2)):
            raise RuntimeError(f"missing WITS source key in frozen {role} window")
        nearby = {y for y in events.get(country, set()) if year - 3 <= y <= year + 1}
        if nearby != ({year} if role == "event" else set()):
            raise RuntimeError(f"CEPII event role differs in frozen {role} window")
    event = [row for row in rows if row[0] == "event"]
    control = [row for row in rows if row[0] == "control"]
    return {
        "roster_sha256": ROSTER_SHA256,
        "event_rows": len(event), "event_countries": len({c for _, c, _ in event}),
        "event_cohorts": len({y for _, _, y in event}),
        "control_rows": len(control), "control_countries": len({c for _, c, _ in control}),
        "wits_values_read": False,
    }


def lock_payload(revision: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "hypothesis_id": HYPOTHESIS_ID,
        "preregistration_commit": revision,
        "source_files": SOURCES,
        "raw_cepii_archive": {"path": RAW_CEPII_REL, "sha256": RAW_CEPII_SHA256},
        "key_roster": {"path": ROSTER_REL, "sha256": ROSTER_SHA256,
                       "event_sha256": EVENT_SHA256, "control_sha256": CONTROL_SHA256},
        "key_preflight": preflight,
        "value_access_before_source_lock": False,
    }


def write_source_lock() -> None:
    revision = registration_commit()
    check_sources()
    preflight = key_preflight()
    path = ROOT / LOCK_REL
    if path.exists():
        raise FileExistsError(f"source lock already exists: {LOCK_REL}")
    path.write_text(json.dumps(lock_payload(revision, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK_REL}; commit it separately before measured-value access")


def check_source_lock(revision: str, preflight: dict[str, Any]) -> None:
    path = ROOT / LOCK_REL
    if json.loads(path.read_text()) != lock_payload(revision, preflight):
        raise RuntimeError("committed source lock differs from registered source/key contract")
    lock_commit = first_addition(LOCK_REL)
    if lock_commit == revision or not is_ancestor(revision, lock_commit):
        raise RuntimeError("source lock did not follow registration in Git history")
    committed_unchanged(LOCK_REL, lock_commit)
    if git_output("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_REL).strip():
        raise RuntimeError("source-lock commit already contains run artifacts")


def measured_panel(rows: list[tuple[str, str, int]]) -> tuple[pd.DataFrame | None, int]:
    """Open WITS measured values only after both frozen commits are verified."""
    columns = ["country_iso3", "year", "value", *WITS_DIMS]
    source = pd.read_parquet(ROOT / WITS_REL, columns=columns)
    if any(not source[col].eq(value).all() for col, value in WITS_DIMS.items()):
        raise RuntimeError("WITS measured source dimensions changed")
    values = {(str(c), int(y)): v for c, y, v in zip(source.country_iso3, source.year, source.value)}
    needed = {(c, y) for _, c, t in rows for y in range(t - 3, t + 2)}
    invalid = 0
    for key in needed:
        v = values.get(key)
        try:
            numeric = float(v)
            okay = math.isfinite(numeric) and numeric >= 0 and numeric.is_integer()
        except (TypeError, ValueError, OverflowError):
            okay = False
        if not okay:
            invalid += 1
    if invalid:
        return None, invalid
    panel_rows = []
    for role, country, year in rows:
        log = {offset: math.log1p(float(values[(country, year + offset)]))
               for offset in (-3, -1, 1)}
        panel_rows.append({
            "country_iso3": country, "year": year, "event": 1 if role == "event" else 0,
            "role": role, "forward_change": log[1] - log[-1],
            "pretrend": log[-1] - log[-3], "baseline_log": log[-1],
        })
    return pd.DataFrame(panel_rows), 0


def clustered_term(panel: pd.DataFrame, formula: str, term: str, ci_level: float) -> dict[str, Any] | None:
    model = smf.ols(formula, data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return None
    groups = panel.country_iso3
    n_clusters = int(groups.nunique())
    if n_clusters <= 1:
        return None
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups,
                                                  "use_correction": True,
                                                  "df_correction": True}, use_t=True)
    coefficient = float(fit.params[term])
    se = float(fit.bse[term])
    if not all(map(math.isfinite, (coefficient, se))) or se <= 0:
        return None
    df = n_clusters - 1
    p = float(2 * student_t.sf(abs(coefficient / se), df))
    half = float(student_t.ppf((1 + ci_level) / 2, df) * se)
    if not math.isfinite(p) or not math.isfinite(half):
        return None
    return {
        "coefficient": coefficient, "std_error": se, "p_value_two_sided": p,
        "confidence_level": ci_level, "confidence_interval": [coefficient - half, coefficient + half],
        "n_rows": int(len(panel)), "n_countries": n_clusters,
        "df_inference": df, "model_rank": int(fit.model.rank),
        "method": "country/year FE OLS, country-cluster CR1 finite correction, Student t(G-1)",
    }


def estimate(rows: list[tuple[str, str, int]], preflight: dict[str, Any]) -> dict[str, Any]:
    gate = dict(preflight)
    gate.pop("wits_values_read")
    gate["wits_values_read_after_lock"] = True
    gate["invalid_selected_wits_keys"] = 0
    floor = (gate["event_rows"] >= MIN_EVENT_ROWS and gate["event_countries"] >= MIN_EVENT_COUNTRIES
             and gate["control_rows"] >= MIN_CONTROL_ROWS and gate["control_countries"] >= MIN_CONTROL_COUNTRIES
             and gate["event_cohorts"] >= MIN_EVENT_COHORTS)
    if not floor:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen event/control sample floor failed",
                "primary": None, "pretrend_diagnostic": None, "raw_pretrend_means": None}
    panel, invalid = measured_panel(rows)
    gate["invalid_selected_wits_keys"] = invalid
    if invalid or panel is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen WITS value contract failed",
                "primary": None, "pretrend_diagnostic": None, "raw_pretrend_means": None}
    primary = clustered_term(panel,
                             "forward_change ~ event + pretrend + baseline_log + C(country_iso3) + C(year)",
                             "event", 0.95)
    diagnostic = clustered_term(panel, "pretrend ~ event + C(country_iso3) + C(year)", "event", 0.90)
    if primary is None or diagnostic is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "full rank or finite country-cluster uncertainty failed",
                "primary": None, "pretrend_diagnostic": None, "raw_pretrend_means": None}
    means = {role: float(panel.loc[panel.role.eq(role), "pretrend"].mean())
             for role in ("event", "control")}
    beta, p = primary["coefficient"], primary["p_value_two_sided"]
    if beta >= EFFECT_MIN and p <= P_MAX:
        verdict = "SUPPORTED"
        reason = "positive conditional descriptive association clears frozen magnitude and local p threshold"
    elif beta <= -EFFECT_MIN and p <= P_MAX:
        verdict = "REFUTED"
        reason = "negative conditional descriptive association clears frozen magnitude and local p threshold"
    else:
        verdict = "PARTIAL"
        reason = "estimable conditional descriptive association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason,
            "primary": primary, "pretrend_diagnostic": diagnostic, "raw_pretrend_means": means}


def artifacts(revision: str, result: dict[str, Any], stamp: str) -> dict[str, Any]:
    verdict = result["verdict"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HYPOTHESIS_ID, "path": SPEC_REL, "topic": "trade"},
        "preregistration": {"spec_commit": revision, "steelman": STEELMAN_REL,
                            "key_roster": ROSTER_REL, "key_roster_sha256": ROSTER_SHA256},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "key_roster": ROSTER_REL, "sample": result["gate"]},
        "results": {"primary": result["primary"], "pretrend_diagnostic": result["pretrend_diagnostic"],
                    "raw_pretrend_means": result["raw_pretrend_means"]},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": result["reason"], "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": revision, "source_lock": LOCK_REL,
        "template": "panel_fe", "preflight": result["gate"],
        "primary": result["primary"], "pretrend_diagnostic": result["pretrend_diagnostic"],
        "raw_pretrend_means": result["raw_pretrend_means"],
        "p_max_two_sided": P_MAX, "absolute_log_effect_min": EFFECT_MIN,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": HYPOTHESIS_ID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": revision, "source_lock": LOCK_REL,
        "status": verdict, "vintages": list(SOURCES.values()),
        "derived_panel": result["gate"], "correction": CORRECTION,
    }
    card = (f"# Result card: {HYPOTHESIS_ID}\n\n"
            f"Verdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration commit: `{revision}`. Source lock: `{LOCK_REL}`.\n\n"
            f"Key roster: {result['gate']['event_rows']} event windows / {result['gate']['event_countries']} countries; "
            f"{result['gate']['control_rows']} no-nearby-expansion control windows / "
            f"{result['gate']['control_countries']} countries.\n")
    if result["primary"] is not None:
        primary = result["primary"]
        pretrend = result["pretrend_diagnostic"]
        card += (f"Adjusted event association: beta={primary['coefficient']:+.6g}, "
                 f"country-cluster SE={primary['std_error']:.6g}, "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}, "
                 f"95% CI={primary['confidence_interval']}.\n"
                 f"Pre-event trend imbalance (diagnostic only): beta={pretrend['coefficient']:+.6g}, "
                 f"country-cluster SE={pretrend['std_error']:.6g}, "
                 f"p={pretrend['p_value_two_sided']:.6g}, "
                 f"90% CI={pretrend['confidence_interval']}; "
                 f"raw event/control means={result['raw_pretrend_means']}.\n")
    card += (f"\nDirectional gate: |beta| >= ln(1.05)={EFFECT_MIN:.9f} and two-sided p <= {P_MAX}; "
             "pretrend imbalance is reported and is not a promotion gate.\n\n"
             "This is a conditional descriptive association only. CEPII records net RTA-partner coverage expansion, "
             "not statutory tariff cuts; WITS records exported HS6 product count, not complexity. "
             "Prior related results were visible. Zero school, policy, causal, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": HYPOTHESIS_ID, "verdict": verdict,
             "primary": result["primary"], "pretrend_diagnostic": result["pretrend_diagnostic"]}
    coefficient_rows = []
    if result["primary"] is not None:
        coefficient_rows.append({"term": "isolated_net_rta_partner_coverage_expansion",
                                 **result["primary"]})
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficient_rows}


def write_artifacts(payload: dict[str, Any]) -> None:
    folder = ROOT / RUN_REL
    if folder.exists():
        raise FileExistsError(f"result directory already exists: {RUN_REL}")
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["coefficients"]).to_parquet(folder / "coefficients.parquet", index=False)


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(revision: str, result: dict[str, Any]) -> None:
    folder = ROOT / RUN_REL
    saved = json.loads((folder / "diagnostics.json").read_text())
    expected = artifacts(revision, result, saved["run_utc"])
    equal_close(saved, expected["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], "evidence_packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), expected["chart"], "chart_data")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes()
            or (folder / "result_card.md").read_text() != expected["card"]
            or (folder / "replication.py").read_text() != expected["wrapper"]):
        raise AssertionError("stored study text differs from exact replay")
    actual_rows = pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records")
    equal_close(actual_rows, expected["coefficients"], "coefficients")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-sources", action="store_true")
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--write-source-lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    check_sources()
    if args.check_sources:
        print("CEPII, WITS, and raw CEPII source SHA-256 pins match; WITS values not opened")
        return 0
    if args.preflight:
        print(json.dumps(key_preflight(), indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    revision = registration_commit()
    preflight = key_preflight()
    check_source_lock(revision, preflight)
    rows = load_roster()
    if args.run and (ROOT / RUN_REL).exists():
        raise FileExistsError(f"result directory already exists: {RUN_REL}")
    result = estimate(rows, preflight)
    if args.run:
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        write_artifacts(artifacts(revision, result, stamp))
        print(HYPOTHESIS_ID, result["verdict"], result["reason"])
        return 0
    verify_artifacts(revision, result)
    print("verified exact replay", HYPOTHESIS_ID, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
