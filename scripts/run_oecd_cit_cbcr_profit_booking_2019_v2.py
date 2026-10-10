#!/usr/bin/env python3
"""Frozen 2019 statutory CIT/CbCR rank calibration.

--preflight reads only country/year/series keys. Selected source values and
finite masks are first loaded by --run or --verify after a separate committed
source lock. The optional source root locates ignored local vintages but is
never written into public artifacts.
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
import yaml
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
HID = "oecd_cit_cbcr_profit_booking_2019_v2"
FAMILY = HID
SPEC = f"hypotheses/fiscal/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PREREG = f"engine/audits/{HID}_prereg_2026-10-10.md"
ROSTER = f"data/pinned_evidence/{HID}_key_roster.csv"
RUNNER = f"scripts/run_{HID}.py"
LOCK = f"data/pinned_evidence/{HID}.manifest.json"
SUMMARY = f"engine/audits/{HID}_results_2026-10-10.md"
RUN_DIR = f"engine/runs/{HID}"
ROSTER_SHA = "617e3febe5a7566e2a52669679b996e4f0b93f0bf3b2b3805e5c338f9bed9d86"
BUILDER = "scripts/build_profit_shifting_panel.py"
BUILDER_SHA = "49bedf729b83d0818904a67a96cab41a97994c31a901b31ff705b9fad997ff5d"
CBCR_URL = ("https://sdmx.oecd.org/public/rest/data/"
            "OECD.CTP.TPS,DSD_CBCR@DF_CBCRI,1.1/all?format=csvfilewithlabels")
SOURCES = {
    "cbcr_composite": {
        "publisher": "profit_shifting", "series_id": "profit_shifting_panel",
        "path": "data/vintages/profit_shifting/profit_shifting_panel@2026-06-29T160050Z.parquet",
        "sha256": "96bad604e38151689d4d31a28f5c86cdec0e0941c7bac310fb8d2cac4472f733",
        "manifest": "data/manifests/fetch_run_2026-06-29T160050Z_profit_shifting.yaml",
        "manifest_sha256": "1108d0451cf57ae95de814e159f72e69356edf4d795d87ed3333b41662fb98fc",
    },
    "statutory_cit": {
        "publisher": "oecd", "series_id": "oecd_combined_corporate_income_tax_rate",
        "path": "data/vintages/oecd/oecd_combined_corporate_income_tax_rate@2026-07-23T153857Z.parquet",
        "sha256": "3e9c5987717087d04d5f82461fc1a3fb5e406ba646fb9f333f8c542e5f3f5ee1",
        "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
        "manifest_sha256": "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18",
    },
}
YEAR = 2019
CBCR_SERIES = (
    "cbcr_profit_booked_usd", "cbcr_employees", "cbcr_profit_per_employee_usd"
)
MIN_COMPLETE = 120
MIN_RATE_DISTINCT = 10
MIN_RATE_IQR = 5.0
MIN_RATIO_DISTINCT = 30
MAX_RATE = 60.0
PERMUTATIONS = 10000
SEED = 21019
ALPHA = 0.01
MIN_ABS_RHO = 0.20
MIN_LOO_SHARE = 0.95
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 1, "family_alpha": ALPHA,
    "causal_credit": 0, "policy_score_eligible": False,
    "policy_score_credit": 0, "school_score_eligible": False,
    "school_score_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "The pinned CbCR extract includes only reporting parents represented in a local OECD aggregate; it is not a global MNE total.",
    "The raw OECD HTTP payload was not preserved, so exact publisher-byte replay and the source-native currency multiplier cannot be checked. The analysis interprets only ranks.",
    "Statutory rates differ from effective rates and may coexist with tax rulings, treaty networks, capital intensity, sector mix, and resource rents.",
    "One pre-pandemic cross-section avoids changes in reporting-parent coverage across years but cannot identify a tax reform effect or actual shifted profit.",
    "This archive-selected test has only a local one-test p cutoff, not an archive-wide multiple-testing correction.",
    "No causal, policy, school, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def thresholds() -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 1,
        "min_key_jurisdictions": 143, "min_complete_jurisdictions": MIN_COMPLETE,
        "min_distinct_tax_rates": MIN_RATE_DISTINCT,
        "min_tax_rate_iqr_pp": MIN_RATE_IQR,
        "min_distinct_cbcr_ratios": MIN_RATIO_DISTINCT,
        "permutations": PERMUTATIONS, "permutation_seed": SEED,
        "two_sided_p_max": ALPHA, "min_abs_rho": MIN_ABS_RHO,
        "min_loo_sign_share": MIN_LOO_SHARE, "max_tax_rate_pct": int(MAX_RATE),
        "causal_credit": 0, "policy_score_credit": 0, "school_score_credit": 0,
    }


def roster() -> list[str]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("frozen key-only roster hash mismatch")
    raw = path.read_bytes()
    if not raw.startswith(b"jurisdiction_iso3,year\n"):
        raise RuntimeError("key-only roster header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    keys = [r["jurisdiction_iso3"] for r in records]
    if (len(keys) != 143 or keys != sorted(set(keys)) or
            any(int(r["year"]) != YEAR for r in records)):
        raise RuntimeError("key-only roster content changed")
    return keys


def validate_spec() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != HID or spec.get("status") != "pre_registered"
            or spec.get("claim_direction") != "-" or spec.get("evidence_type") != "descriptive"
            or spec.get("steelman") != STEELMAN or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != [] or spec.get("linked_conditions") != []
            or spec["sample"].get("countries") != ["GLOBAL"]
            or spec["sample"].get("period") != [YEAR, YEAR]
            or spec["falsification"].get("threshold") != thresholds()):
        raise RuntimeError("spec differs from the frozen runner")
    roster()


def registration_commit() -> str:
    files = [SPEC, STEELMAN, PREREG, ROSTER, RUNNER]
    revisions = {first_addition(path) for path in files}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in files:
        unchanged(path, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise RuntimeError("registration commit already contained run artifacts")
    validate_spec()
    return revision


def source_meta(source_root: Path) -> dict[str, Any]:
    if sha256(ROOT / BUILDER) != BUILDER_SHA:
        raise RuntimeError("CbCR derivation script hash mismatch")
    result: dict[str, Any] = {}
    for role, source in SOURCES.items():
        path = source_root / source["path"]
        manifest = ROOT / source["manifest"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned source: {role}")
        if not manifest.is_file() or sha256(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [item for item in entries
            if item.get("publisher") == source["publisher"]
            and item.get("series_id") == source["series_id"]
            and item.get("parquet_path") == source["path"]
            and item.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest lacks the exact entry: {role}")
        entry = matches[0]
        if role == "cbcr_composite" and entry.get("extra", {}).get("oecd_cbcr_url") != CBCR_URL:
            raise RuntimeError("composite manifest lacks exact OECD CbCR endpoint")
        result[role] = {
            **source, "source_url": CBCR_URL if role == "cbcr_composite" else entry.get("source_url"),
            "license": "OECD standard permissions (attribution required)"
            if role == "cbcr_composite" else entry.get("license"),
            "fetch_utc": entry.get("fetch_utc"),
            "pinned_parquet_preserved": True,
            "publisher_http_payload_preserved": False,
        }
    return result


def key_only_preflight(source_root: Path) -> dict[str, Any]:
    cbcr = pd.read_parquet(source_root / SOURCES["cbcr_composite"]["path"],
        columns=["jurisdiction_iso3", "year", "series_id"])
    cit = pd.read_parquet(source_root / SOURCES["statutory_cit"]["path"],
        columns=["country_iso3", "year"])
    cbcr = cbcr.loc[cbcr.year.eq(YEAR) & cbcr.series_id.isin(CBCR_SERIES)]
    cit = cit.loc[cit.year.eq(YEAR)]
    if cit.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate statutory-rate source keys")
    if cbcr.duplicated(["jurisdiction_iso3", "year", "series_id"]).any():
        raise RuntimeError("duplicate CbCR source keys")
    keys = set(cit.country_iso3)
    for series in CBCR_SERIES:
        keys &= set(cbcr.loc[cbcr.series_id.eq(series), "jurisdiction_iso3"])
    if sorted(keys) != roster():
        raise RuntimeError("source-key intersection differs from committed roster")
    return {
        "year": YEAR, "source_key_jurisdictions": len(keys),
        "roster_sha256": ROSTER_SHA, "selected_values_opened": False,
        "family_size": 1,
    }


def lock_payload(registration: str, sources: dict[str, Any],
                 blind: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": FAMILY, "preregistration_commit": registration,
        "key_only_preflight": blind, "sources": sources,
        "builder_path": BUILDER, "builder_sha256": BUILDER_SHA,
        "raw_cbcr_payload_preserved": False,
        "all_paths_relative": True,
    }


def prepare_lock(source_root: Path) -> None:
    registration = registration_commit()
    sources = source_meta(source_root)
    blind = key_only_preflight(source_root)
    if (ROOT / LOCK).exists():
        raise FileExistsError(LOCK)
    (ROOT / LOCK).write_text(
        json.dumps(lock_payload(registration, sources, blind), indent=2, sort_keys=True) + "\n"
    )


def check_lock(registration: str, sources: dict[str, Any],
               blind: dict[str, Any]) -> str:
    lock_commit = first_addition(LOCK)
    if lock_commit == registration:
        raise RuntimeError("source lock must be a separate later commit")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", registration, lock_commit], cwd=ROOT)
    unchanged(LOCK, lock_commit)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, sources, blind):
        raise RuntimeError("source lock differs from frozen source pins")
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_DIR).strip():
        raise RuntimeError("source-lock commit already contained run artifacts")
    return lock_commit


def measured(source_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    # First selected numeric and null-mask access occurs after check_lock().
    wanted = roster()
    cbcr = pd.read_parquet(source_root / SOURCES["cbcr_composite"]["path"],
        columns=["jurisdiction_iso3", "year", "series_id", "value"])
    cbcr = cbcr.loc[cbcr.year.eq(YEAR) & cbcr.jurisdiction_iso3.isin(wanted)
        & cbcr.series_id.isin(CBCR_SERIES)].copy()
    cit = pd.read_parquet(source_root / SOURCES["statutory_cit"]["path"],
        columns=["country_iso3", "year", "value"])
    cit = cit.loc[cit.year.eq(YEAR) & cit.country_iso3.isin(wanted)].copy()
    if (cbcr.duplicated(["jurisdiction_iso3", "series_id"]).any()
            or cit.duplicated(["country_iso3"]).any()):
        raise RuntimeError("duplicate selected values after source lock")
    matrix = cbcr.pivot(index="jurisdiction_iso3", columns="series_id", values="value")
    matrix = matrix.reindex(wanted)
    matrix["cit"] = cit.set_index("country_iso3").value.reindex(wanted)
    for col in [*CBCR_SERIES, "cit"]:
        matrix[col] = pd.to_numeric(matrix[col], errors="coerce")
    valid = (np.isfinite(matrix[[*CBCR_SERIES, "cit"]]).all(axis=1)
        & matrix["cbcr_employees"].gt(0)
        & matrix["cit"].between(0, MAX_RATE))
    complete = matrix.loc[valid].copy()
    ratio = complete["cbcr_profit_booked_usd"] / complete["cbcr_employees"]
    inconsistent = ~np.isclose(ratio.to_numpy(),
        complete["cbcr_profit_per_employee_usd"].to_numpy(),
        rtol=1e-8, atol=1e-10)
    gate = {
        "key_only_jurisdictions": len(wanted),
        "complete_jurisdictions": len(complete),
        "excluded_missing_invalid_or_out_of_range": int((~valid).sum()),
        "ratio_inconsistent_jurisdictions": int(inconsistent.sum()),
        "distinct_tax_rates": int(complete["cit"].nunique()),
        "tax_rate_iqr_pp": float(complete["cit"].quantile(.75)
                                 - complete["cit"].quantile(.25)) if len(complete) else None,
        "distinct_cbcr_ratios": int(complete["cbcr_profit_per_employee_usd"].nunique()),
        "year": YEAR,
        "selected_values_read_after_committed_lock": True,
    }
    complete.index.name = "jurisdiction_iso3"
    return complete, gate


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if gate["ratio_inconsistent_jurisdictions"]:
        return {"verdict": "INCONCLUSIVE", "reason": "source ratio consistency gate failed",
                "gate": gate, "primary": None}
    if (gate["complete_jurisdictions"] < MIN_COMPLETE
            or gate["distinct_tax_rates"] < MIN_RATE_DISTINCT
            or (gate["tax_rate_iqr_pp"] is None or gate["tax_rate_iqr_pp"] < MIN_RATE_IQR)
            or gate["distinct_cbcr_ratios"] < MIN_RATIO_DISTINCT):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen complete-case or variation gate failed",
                "gate": gate, "primary": None}
    x = rankdata(panel["cit"].to_numpy(dtype=float), method="average")
    y = rankdata(panel["cbcr_profit_per_employee_usd"].to_numpy(dtype=float), method="average")
    xdev, ydev = x - x.mean(), y - y.mean()
    norm = float(np.sqrt((xdev @ xdev) * (ydev @ ydev)))
    if not math.isfinite(norm) or norm <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "rank variation is nonfinite or zero",
                "gate": gate, "primary": None}
    rho = float((xdev @ ydev) / norm)
    rng = np.random.default_rng(SEED)
    extreme = sum(abs(float(xdev @ rng.permutation(ydev) / norm)) >= abs(rho) - 1e-15
                  for _ in range(PERMUTATIONS))
    p = (1 + extreme) / (PERMUTATIONS + 1)
    loo = [float(spearmanr(np.delete(panel["cit"].to_numpy(dtype=float), i),
            np.delete(panel["cbcr_profit_per_employee_usd"].to_numpy(dtype=float), i)).statistic)
            for i in range(len(panel))]
    if not all(math.isfinite(value) for value in loo):
        return {"verdict": "INCONCLUSIVE", "reason": "leave-one-out rank statistic nonfinite",
                "gate": gate, "primary": None}
    negative_share = sum(value < 0 for value in loo) / len(loo)
    positive_share = sum(value > 0 for value in loo) / len(loo)
    primary = {
        "rho": rho, "p_value_two_sided_permutation": p,
        "permutation_extreme_count": int(extreme), "permutations": PERMUTATIONS,
        "n_jurisdictions": len(panel),
        "loo_negative_share": negative_share, "loo_positive_share": positive_share,
        "loo_min_rho": min(loo), "loo_max_rho": max(loo),
        "method": "2019 cross-jurisdiction Spearman with average ties and 10000 fixed-seed outcome-rank permutations",
    }
    if rho <= -MIN_ABS_RHO and p <= ALPHA and negative_share >= MIN_LOO_SHARE:
        verdict, reason = "SUPPORTED", "negative rank association clears all frozen descriptive gates"
    elif rho >= MIN_ABS_RHO and p <= ALPHA and positive_share >= MIN_LOO_SHARE:
        verdict, reason = "REFUTED", "positive rank association clears mirrored descriptive gates"
    else:
        verdict, reason = "PARTIAL", "estimable association misses at least one frozen directional gate"
    return {"verdict": verdict, "reason": reason, "gate": gate, "primary": primary}


def artifacts(result: dict[str, Any], registration: str,
              lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    diagnostics = {
        "hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"],
        "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "template": "descriptive",
        "preflight": gate, "primary": primary,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
        "derived_panel": gate, "correction": CORRECTION,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "topic": "fiscal"},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": 1,
            "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
            "command": f"python3 {RUNNER} --verify --source-root <local IESET source checkout>"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": primary}, "limitations": LIMITATIONS,
        "correction": CORRECTION,
    }
    card = (f"# Result card: {HID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
        f"Complete 2019 tax jurisdictions: {gate['complete_jurisdictions']} of "
        f"{gate['key_only_jurisdictions']} fixed source keys.\n")
    if primary:
        card += (f"\nSpearman rho={primary['rho']:+.6g}; two-sided fixed-seed "
            f"permutation p={primary['p_value_two_sided_permutation']:.6g}; "
            f"leave-one-out negative share={primary['loo_negative_share']:.3f}.\n")
    card += ("\nOne partial-coverage descriptive association only. The source's "
        "raw CbCR HTTP payload was not preserved, and its dollar multiplier "
        "cannot be independently replayed. No profit-shifting amount, "
        "tax-policy effect, causal, school, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else root\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), "
        "'--verify', '--source-root', str(source_root)], cwd=root))\n")
    chart = {"hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict,
        "primary": primary}
    coefficients = ([{"term": "spearman_rho", "coefficient": primary["rho"],
        "p_value_two_sided": primary["p_value_two_sided_permutation"],
        "n_jurisdictions": primary["n_jurisdictions"]}] if primary else [])
    summary = (
        f"# 2019 statutory corporate tax and CbCR profit booking: frozen result\n\n"
        f"Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
        f"**{verdict}** — {result['reason']}. Complete jurisdictions: "
        f"{gate['complete_jurisdictions']} / {gate['key_only_jurisdictions']}; "
        f"tax-rate IQR: {gate['tax_rate_iqr_pp']} percentage points.\n\n"
    )
    if primary:
        summary += (f"Spearman rho {primary['rho']:+.6g}; two-sided permutation "
            f"p {primary['p_value_two_sided_permutation']:.6g}; "
            f"{primary['permutation_extreme_count']} of {PERMUTATIONS} permutations "
            f"at least as extreme. Leave-one-out negative sign share "
            f"{primary['loo_negative_share']:.3f}.\n\n")
    summary += (
        "This is one descriptive calibration, not a measured tax-policy effect "
        "or a global profit-shifting estimate. The local derived CbCR vintage "
        "has exact hash custody, but its raw OECD response was not preserved. "
        "Causal, policy, school, position, and featured credit are zero.\n"
    )
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
        "card": card, "wrapper": wrapper, "chart": chart,
        "coefficients": coefficients, "summary": summary}


def normalize(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected,
                rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def write_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated = artifacts(result, registration, lock_commit, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(generated["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(generated["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(generated["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(generated["card"])
    (folder / "replication.py").write_text(generated["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(generated["chart"], indent=2) + "\n")
    pd.DataFrame(generated["coefficients"],
        columns=["term", "coefficient", "p_value_two_sided", "n_jurisdictions"]).to_parquet(
            folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(generated["summary"])


def verify_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RUN_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    generated = artifacts(result, registration, lock_commit, saved["run_utc"])
    equal_close(saved, generated["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()),
        generated["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()),
        generated["packet"], "evidence_packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()),
        generated["chart"], "chart")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
        generated["coefficients"], "coefficients")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != generated["card"]
            or (folder / "replication.py").read_text() != generated["wrapper"]
            or (ROOT / SUMMARY).read_text() != generated["summary"]):
        raise AssertionError("text artifact differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("preflight", "prepare-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    source_meta(source_root)
    blind = key_only_preflight(source_root)
    if args.preflight:
        validate_spec()
        print(json.dumps(blind, indent=2, sort_keys=True))
        return 0
    if args.prepare_lock:
        prepare_lock(source_root)
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    registration = registration_commit()
    sources = source_meta(source_root)
    lock_commit = check_lock(registration, sources, blind)
    panel, gate = measured(source_root)
    result = estimate(panel, gate)
    if args.run:
        write_artifacts(result, registration, lock_commit)
        print(HID, result["verdict"], gate)
        return 0
    verify_artifacts(result, registration, lock_commit)
    print("verified exact replay", HID, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
