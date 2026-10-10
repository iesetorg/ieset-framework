#!/usr/bin/env python3
"""Frozen descriptive SMARD monthly electricity calibration.

--make-roster and --prepare-lock inspect dates, region/filter keys, schemas,
manifest metadata and file bytes only. --run and --verify may open selected
values only after a separate committed source lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.api as sm
import yaml
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
HID = "smard_german_vre_share_day_ahead_price_2018_2026"
SPEC = f"hypotheses/energy/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PREREG = f"engine/audits/{HID}_prereg_2026-10-10.md"
ROSTER = f"data/pinned_evidence/{HID}_key_roster.csv"
RUNNER = f"scripts/run_{HID}.py"
LOCK = f"data/pinned_evidence/{HID}.manifest.json"
RUN_DIR = f"engine/runs/{HID}"
SUMMARY = f"engine/audits/{HID}_results_2026-10-10.md"
REGISTERED = (SPEC, STEELMAN, PREREG, ROSTER, RUNNER)
ROSTER_SHA = "5541b2d7ed6c88d5caa2176408340a14445dd747a46ea82be5b1dbbc9343673b"
FETCH_MANIFEST = "data/manifests/fetch_run_2026-10-09T121824Z.yaml"
FETCH_SHA = "befe6a588f0e2c0de0fd42566f34e76226ce161151432e0373bf3dced401d960"
SOURCES = {
    "price": ("price_de_lu_DE_month@2026-10-09T121732Z.parquet",
              "6f0447b805603f7a2e6ff917bc8e57e80697e05efe9dbe6b035e1e9253a6c14e", 4169, "EUR/MWh"),
    "solar": ("solar_DE_month@2026-10-09T121736Z.parquet",
              "025836509aad657121bbb46286ce60059c3b3b697773239cb86a156f495ea4dd", 4068, "MWh"),
    "onshore": ("wind_onshore_DE_month@2026-10-09T121740Z.parquet",
                "b2d24dfb71569ecd534432cd460a9eefca93a12cb429399fff943581c1524529", 4067, "MWh"),
    "offshore": ("wind_offshore_DE_month@2026-10-09T121744Z.parquet",
                 "6931c817a5c55c1bf326e0497ae42622dd02e4f967215f8bf2d0b5bd9f486608", 1225, "MWh"),
    "load": ("load_DE_month@2026-10-09T121805Z.parquet",
             "a73d3b489ed62e0eceb0e7deef6072b6c46c4d78937ae3e29fec00dcce931d0d", 410, "MWh"),
}
YEARS_OMIT = tuple(range(2019, 2026))
MIN_COMPLETE = 84
MIN_FULL_YEARS = 6
MIN_IQR_PP = 5.0
MAX_LAG = 3
MIN_BETA = 1.0
ALPHA = 0.01
MIN_SAME_SIGN = 5
LIMITATIONS = [
    "German generation and load do not exactly match the Germany/Luxembourg bidding-zone price footprint.",
    "Monthly average price hides hourly merit-order effects; imports, outages, fuel and carbon prices, weather and demand confound the association.",
    "SMARD can revise historical data; these exact local parquet bytes are pinned but the original HTTP response was not preserved.",
    "This one-test local cutoff does not correct the wider archive selection history.",
    "No causal, policy, school, position or featured credit is permitted.",
]
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": HID,
    "family_size": 1, "family_alpha": ALPHA, "causal_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0,
    "featured_eligible": False,
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise ValueError(f"Missing first-addition commit for {relative}")
    return commits[-1]


def unchanged(relative: str, revision: str) -> None:
    current = (ROOT / relative).read_bytes()
    if (current != git("show", f"{revision}:{relative}")
            or current != git("show", f"HEAD:{relative}")
            or git("status", "--porcelain", "--", relative).strip()):
        raise ValueError(f"Frozen file differs from its first-addition commit: {relative}")


def registered() -> str:
    revisions = {first_addition(path) for path in REGISTERED}
    if len(revisions) != 1:
        raise ValueError("Registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in REGISTERED:
        unchanged(path, revision)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != HID or spec.get("status") != "pre_registered"
            or spec.get("falsification", {}).get("threshold", {}).get("family_size") != 1
            or spec.get("steelman") != STEELMAN):
        raise ValueError("Spec does not match frozen one-question runner")
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise ValueError("Registration commit contained results")
    return revision


def source_paths(source_root: Path) -> dict[str, Path]:
    return {role: source_root / "data/vintages/smard" / meta[0]
            for role, meta in SOURCES.items()}


def key_only_preflight(source_root: Path) -> dict:
    manifest_path = source_root / FETCH_MANIFEST
    if not manifest_path.is_file() or sha(manifest_path) != FETCH_SHA:
        raise ValueError("Fetch-manifest bytes missing or changed")
    manifest = yaml.safe_load(manifest_path.read_text())
    entries = manifest.get("entries", [])
    all_dates = []
    source_info = {}
    for role, (name, digest, filter_id, units) in SOURCES.items():
        path = source_paths(source_root)[role]
        relative = f"data/vintages/smard/{name}"
        if not path.is_file() or sha(path) != digest:
            raise ValueError(f"Source bytes missing or changed: {role}")
        matches = [item for item in entries if item.get("parquet_path") == relative]
        if (len(matches) != 1 or matches[0].get("sha256") != digest
                or matches[0].get("publisher") != "smard"
                or matches[0].get("units") != units
                or matches[0].get("extra", {}).get("filter_id") != filter_id):
            raise ValueError(f"Fetch-manifest entry mismatch: {role}")
        schema = pq.ParquetFile(path).schema_arrow.names
        if not {"date", "region", "filter_id", "value"}.issubset(schema):
            raise ValueError(f"Source schema mismatch: {role}")
        keys = pq.read_table(path, columns=["date", "region", "filter_id"]).to_pydict()
        if (set(keys["region"]) != {"DE"} or set(keys["filter_id"]) != {filter_id}):
            raise ValueError(f"Source geography/filter mismatch: {role}")
        dates = [d.strftime("%Y-%m-%d") for d in keys["date"]]
        if len(dates) != len(set(dates)):
            raise ValueError(f"Duplicate source date: {role}")
        all_dates.append(set(dates))
        source_info[role] = {
            "publisher": "smard", "series_id": name.split("@")[0],
            "path": relative, "sha256": digest,
            "source_url": matches[0].get("source_url"),
            "fetch_utc": matches[0].get("fetch_utc"),
            "units": units, "filter_id": filter_id, "source_key_count": len(dates),
        }
    dates = sorted(set.intersection(*all_dates))
    expected_dates = [d.strftime("%Y-%m-%d") for d in
                      pd.date_range("2018-10-01", "2026-09-01", freq="MS")]
    if dates != expected_dates or len(dates) != 96:
        raise ValueError("Source-key intersection differs from frozen 96-month window")
    roster_bytes = ("month\n" + "".join(f"{d}\n" for d in dates)).encode()
    if hashlib.sha256(roster_bytes).hexdigest() != ROSTER_SHA:
        raise ValueError("Source-key roster hash differs from registration")
    return {
        "sources": source_info,
        "fetch_manifest": {"path": FETCH_MANIFEST, "sha256": FETCH_SHA},
        "key_only_months": dates, "key_roster": ROSTER,
        "key_roster_sha256": ROSTER_SHA, "selected_values_opened": False,
        "original_http_payload_preserved": False,
    }


def make_roster(source_root: Path) -> None:
    metadata = key_only_preflight(source_root)
    path = ROOT / ROSTER
    if path.exists():
        raise FileExistsError(ROSTER)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("month\n" + "".join(f"{d}\n" for d in metadata["key_only_months"]))
    if sha(path) != ROSTER_SHA:
        raise AssertionError("Roster write mismatch")


def expected_lock(source_root: Path) -> dict:
    revision = registered()
    metadata = key_only_preflight(source_root)
    if sha(ROOT / ROSTER) != ROSTER_SHA:
        raise ValueError("Frozen roster differs")
    return {
        "hypothesis_id": HID, "preregistration_commit": revision,
        "registered_sha256": {path: sha(ROOT / path) for path in REGISTERED},
        "source_custody": metadata,
        "statement": "This metadata-only lock was committed before any selected source values or missingness were opened.",
    }


def prepare_lock(source_root: Path) -> None:
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(expected_lock(source_root), indent=2, sort_keys=True) + "\n")


def verify_lock(source_root: Path) -> tuple[str, str, dict]:
    registration = registered()
    lock_commit = first_addition(LOCK)
    unchanged(LOCK, lock_commit)
    if lock_commit == registration:
        raise ValueError("Source lock must follow registration")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", registration, lock_commit], cwd=ROOT)
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_DIR).strip():
        raise ValueError("Source-lock commit contained results")
    metadata = expected_lock(source_root)
    if json.loads((ROOT / LOCK).read_text()) != metadata:
        raise ValueError("Committed source custody differs from current source bytes or keys")
    return registration, lock_commit, metadata


def finite(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def selected_panel(source_root: Path, dates: list[str]) -> tuple[pd.DataFrame, dict]:
    selected = set(dates)
    cells = {}
    for role, path in source_paths(source_root).items():
        rows = pq.read_table(path, columns=["date", "value"]).to_pydict()
        vals = {}
        for day, value in zip(rows["date"], rows["value"]):
            key = day.strftime("%Y-%m-%d")
            if key in selected:
                if key in vals:
                    raise ValueError(f"Duplicate selected month: {role} {key}")
                vals[key] = finite(value)
        if set(vals) != selected:
            raise ValueError(f"Missing selected month key: {role}")
        cells[role] = vals
    records = []
    exclusions = 0
    for day in dates:
        row = {role: vals[day] for role, vals in cells.items()}
        if any(v is None for v in row.values()):
            exclusions += 1
            continue
        load = row["load"]
        generation = row["solar"] + row["onshore"] + row["offshore"]
        if (load <= 0 or min(row["solar"], row["onshore"], row["offshore"]) < 0
                or generation > 1.5 * load or not -500 <= row["price"] <= 1000):
            exclusions += 1
            continue
        date = pd.Timestamp(day)
        records.append({
            "date": day, "year": date.year, "month": date.month,
            "price": row["price"], "load": load,
            "vre_share_pp": 100 * generation / load,
            "vre_share_10pp": 10 * generation / load,
            "log_load": math.log(load),
        })
    panel = pd.DataFrame(records)
    gate = {
        "key_only_months": len(dates), "complete_months": len(panel),
        "excluded_missing_invalid_or_out_of_range": exclusions,
        "full_calendar_years": [int(y) for y in YEARS_OMIT
                                if len(panel.loc[panel.year.eq(y)]) == 12] if len(panel) else [],
        "share_iqr_pp": (float(np.percentile(panel.vre_share_pp, 75)
                               - np.percentile(panel.vre_share_pp, 25)) if len(panel) else None),
        "selected_values_read_after_committed_lock": True,
    }
    return panel, gate


def design(panel: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    x = panel[["vre_share_10pp", "log_load"]].reset_index(drop=True)
    month = pd.get_dummies(panel.month.astype(str), prefix="month", drop_first=True).astype(float)
    year = pd.get_dummies(panel.year.astype(str), prefix="year", drop_first=True).astype(float)
    x = pd.concat([x, month.reset_index(drop=True), year.reset_index(drop=True)], axis=1)
    x = sm.add_constant(x.astype(float), has_constant="add")
    return panel.price.reset_index(drop=True).astype(float), x


def fit(panel: pd.DataFrame) -> dict | None:
    y, x = design(panel)
    if len(x) <= x.shape[1] or np.linalg.matrix_rank(x.to_numpy()) != x.shape[1]:
        return None
    model = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": MAX_LAG})
    beta = float(model.params["vre_share_10pp"])
    se = float(model.bse["vre_share_10pp"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return None
    p = float(2 * norm.sf(abs(beta / se)))
    return {"beta_eur_per_mwh_per_10pp": beta, "se_hac3": se,
            "p_value_two_sided_normal": p, "n_months": len(panel),
            "design_columns": list(x.columns)}


def evaluate(panel: pd.DataFrame, gate: dict) -> dict:
    reasons = []
    if gate["complete_months"] < MIN_COMPLETE:
        reasons.append("complete-month floor failed")
    if len(gate["full_calendar_years"]) < MIN_FULL_YEARS:
        reasons.append("full-year floor failed")
    if gate["share_iqr_pp"] is None or gate["share_iqr_pp"] < MIN_IQR_PP:
        reasons.append("share-IQR floor failed")
    if reasons:
        return {"verdict": "INCONCLUSIVE", "reason": "; ".join(reasons),
                "gate": gate, "primary": None, "year_omissions": []}
    primary = fit(panel)
    if primary is None:
        return {"verdict": "INCONCLUSIVE", "reason": "rank or HAC uncertainty gate failed",
                "gate": gate, "primary": None, "year_omissions": []}
    omissions = []
    for year in YEARS_OMIT:
        sub = fit(panel.loc[panel.year.ne(year)].reset_index(drop=True))
        omissions.append({"omitted_year": year,
                          "beta_eur_per_mwh_per_10pp":
                              sub["beta_eur_per_mwh_per_10pp"] if sub else None})
    neg = sum(item["beta_eur_per_mwh_per_10pp"] is not None
              and item["beta_eur_per_mwh_per_10pp"] < 0 for item in omissions)
    pos = sum(item["beta_eur_per_mwh_per_10pp"] is not None
              and item["beta_eur_per_mwh_per_10pp"] > 0 for item in omissions)
    beta, p = primary["beta_eur_per_mwh_per_10pp"], primary["p_value_two_sided_normal"]
    if beta <= -MIN_BETA and p <= ALPHA and neg >= MIN_SAME_SIGN:
        verdict, reason = "SUPPORTED", "frozen negative association gates passed"
    elif beta >= MIN_BETA and p <= ALPHA and pos >= MIN_SAME_SIGN:
        verdict, reason = "REFUTED", "frozen positive association gates passed"
    else:
        verdict, reason = "PARTIAL", "estimable association misses a frozen directional gate"
    primary.update({"year_omission_negative_count": neg, "year_omission_positive_count": pos})
    return {"verdict": verdict, "reason": reason, "gate": gate,
            "primary": primary, "year_omissions": omissions}


def artifacts(result: dict, registration: str, lock_commit: str,
              metadata: dict, stamp: str) -> dict:
    verdict = result["verdict"]
    gate = result["gate"]
    primary = result["primary"]
    diagnostics = {
        "hypothesis_id": HID, "family_id": HID, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"],
        "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "template": "descriptive",
        "preflight": gate, "primary": primary,
        "year_omissions": result["year_omissions"],
        "data_status": {"variables_missing": [], "input_vintages":
                        list(metadata["source_custody"]["sources"].values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict,
        "vintages": list(metadata["source_custody"]["sources"].values()),
        "derived_panel": gate, "correction": CORRECTION,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "topic": "energy"},
        "preregistration": {
            "spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": HID, "family_size": 1, "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
                         "command": f"python3 {RUNNER} --verify --source-root <local IESET source checkout>"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(),
                    "reason": result["reason"]},
        "data": {"inputs": metadata["source_custody"]["sources"],
                 "sample": gate}, "results": {"primary": primary,
                                             "year_omissions": result["year_omissions"]},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    card = (f"# Result card: {HID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Preregistration: {registration}; source lock: {lock_commit}.\n\n"
            f"Complete months: {gate['complete_months']} of 96 fixed keys; "
            f"share IQR: {gate['share_iqr_pp']} percentage points.\n")
    if primary:
        card += (f"\nSlope: {primary['beta_eur_per_mwh_per_10pp']:+.6g} "
                 f"EUR/MWh per ten share points; HAC(3) SE "
                 f"{primary['se_hac3']:.6g}; two-sided p "
                 f"{primary['p_value_two_sided_normal']:.6g}.\n")
    card += ("\nGerman generation/load and Germany/Luxembourg price have different "
             "footprints. Descriptive monthly co-movement only; no causal, "
             "renewable-policy, consumer-price, school, position or featured credit.\n")
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else root\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), "
        "'--verify', '--source-root', str(source_root)], cwd=root))\n"
    )
    chart = {"hypothesis_id": HID, "family_id": HID, "verdict": verdict,
             "primary": primary}
    coefficients = ([{"term": "vre_share_10pp",
                      "coefficient": primary["beta_eur_per_mwh_per_10pp"],
                      "standard_error": primary["se_hac3"],
                      "p_value_two_sided": primary["p_value_two_sided_normal"],
                      "n_months": primary["n_months"]}] if primary else [])
    summary = (
        "# SMARD wind/solar generation and wholesale price: frozen result\n\n"
        f"Preregistration {registration}; source lock {lock_commit}.\n\n"
        f"**{verdict}** — {result['reason']}. Complete months: "
        f"{gate['complete_months']}/96; share IQR: {gate['share_iqr_pp']} points.\n\n"
    )
    if primary:
        summary += (f"HAC(3) slope {primary['beta_eur_per_mwh_per_10pp']:+.6g} "
                    f"EUR/MWh per 10 share points (SE {primary['se_hac3']:.6g}, "
                    f"two-sided p {primary['p_value_two_sided_normal']:.6g}). "
                    f"Year omission signs: {primary['year_omission_negative_count']} "
                    "negative and "
                    f"{primary['year_omission_positive_count']} positive of seven.\n\n")
    summary += (
        "This single descriptive calibration does not identify a renewable "
        "policy or consumer-tariff effect. German generation/load and the "
        "Germany/Luxembourg wholesale price differ in footprint. The source "
        "HTTP payload is not preserved, although the local parquet and manifest "
        "bytes are pinned. Causal, policy, school, position and featured "
        "credit are zero.\n"
    )
    return {"diagnostics": diagnostics, "manifest": manifest,
            "packet": packet, "card": card, "wrapper": wrapper,
            "chart": chart, "coefficients": coefficients, "summary": summary}


def write_artifacts(result: dict, registration: str, lock_commit: str,
                    metadata: dict) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("Measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated = artifacts(result, registration, lock_commit, metadata, stamp)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(generated["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(generated["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(generated["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(generated["card"])
    (folder / "replication.py").write_text(generated["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(generated["chart"], indent=2) + "\n")
    pd.DataFrame(generated["coefficients"],
                 columns=["term", "coefficient", "standard_error",
                          "p_value_two_sided", "n_months"]).to_parquet(
                              folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(generated["summary"])


def verify_artifacts(result: dict, registration: str, lock_commit: str,
                     metadata: dict) -> None:
    folder = ROOT / RUN_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    generated = artifacts(result, registration, lock_commit, metadata, saved["run_utc"])
    if saved != generated["diagnostics"]:
        raise AssertionError("Diagnostics differ from exact replay")
    for file, key in (("manifest.yaml", "manifest"), ("evidence_packet.yaml", "packet")):
        if yaml.safe_load((folder / file).read_text()) != generated[key]:
            raise AssertionError(f"{file} differs from exact replay")
    if json.loads((folder / "chart_data.json").read_text()) != generated["chart"]:
        raise AssertionError("Chart differs from exact replay")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != generated["card"]
            or (folder / "replication.py").read_text() != generated["wrapper"]
            or (ROOT / SUMMARY).read_text() != generated["summary"]):
        raise AssertionError("Text artifact differs from exact replay")
    actual = pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records")
    if actual != generated["coefficients"]:
        raise AssertionError("Coefficient artifact differs from exact replay")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("make-roster", "preflight", "prepare-lock", "run", "verify"):
        actions.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.make_roster:
        make_roster(source_root)
        print(f"wrote key-only {ROSTER}")
        return
    if args.preflight:
        data = key_only_preflight(source_root)
        print(json.dumps({"key_only_months": len(data["key_only_months"]),
                          "selected_values_opened": False}, indent=2))
        return
    if args.prepare_lock:
        prepare_lock(source_root)
        print(f"wrote metadata-only {LOCK}; commit before --run")
        return
    registration, lock_commit, metadata = verify_lock(source_root)
    panel, gate = selected_panel(source_root, metadata["source_custody"]["key_only_months"])
    result = evaluate(panel, gate)
    if args.run:
        write_artifacts(result, registration, lock_commit, metadata)
        print(f"{HID}: {result['verdict']}, {gate['complete_months']} complete months")
    else:
        verify_artifacts(result, registration, lock_commit, metadata)
        print(f"exact replay passed: {HID} {result['verdict']}")


if __name__ == "__main__":
    main()
