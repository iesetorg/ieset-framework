#!/usr/bin/env python3
"""Frozen, source-pinned descriptive credit/manufacturing continuation.

The prepare-lock command reads source keys only. The run/verify commands are
the only paths that read selected WDI values and require a separately committed
lock first. No historical run or hypothesis is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.api as sm
import yaml


ROOT = Path(__file__).resolve().parents[1]
ID = "private_credit_manufacturing_share_2022_2024_holdout_v2"
HYP = Path("hypotheses/growth") / f"{ID}.yaml"
LOCK = Path("data/pinned_evidence") / f"{ID}.source_lock.json"
RUN = Path("engine/runs") / ID
REGISTRATION_FILES = (
    HYP,
    Path("hypotheses/steelman") / f"{ID}.md",
    Path("engine/audits/private_credit_manufacturing_2024_v2_source_plan.md"),
    Path("scripts/run_private_credit_manufacturing_2024_v2.py"),
)
MANIFEST = Path("data/manifests/fetch_run_2026-05-05T200056Z.yaml")
MANIFEST_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
SOURCES = {
    "credit": (
        Path("data/vintages/world_bank_wdi/FS.AST.PRVT.GD.ZS@2026-05-05T194720Z.parquet"),
        "57d2717d9097b3142f9b116242218621e4560a6bf4e29ddc22081dd66b2a1b19",
        (2022,),
    ),
    "manufacturing": (
        Path("data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet"),
        "a440c8b254408d43b810059921c1d72c15612c8d9921fbec60a87b331adc2499",
        (2022, 2024),
    ),
    "gdp_pc": (
        Path("data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet"),
        "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        (2022,),
    ),
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def registration_commit() -> str:
    additions: set[str] = set()
    for relative in REGISTRATION_FILES:
        if not (ROOT / relative).is_file():
            raise RuntimeError(f"registration file missing: {relative}")
        commits = git("log", "--diff-filter=A", "--format=%H", "--", str(relative)).splitlines()
        if len(commits) != 1:
            raise RuntimeError(f"registration first-addition ambiguity: {relative}: {commits}")
        additions.add(commits[0])
    if len(additions) != 1:
        raise RuntimeError(f"registration files were not added together: {additions}")
    commit = next(iter(additions))
    git("merge-base", "--is-ancestor", commit, "HEAD")
    for relative in REGISTRATION_FILES:
        original = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True
        ).stdout
        if original != (ROOT / relative).read_bytes():
            raise RuntimeError(f"frozen registration file changed since first addition: {relative}")
    return commit


def source_lock_commit(registration: str) -> str:
    additions = git("log", "--diff-filter=A", "--format=%H", "--", str(LOCK)).splitlines()
    if len(additions) != 1:
        raise RuntimeError(f"source lock must have one first-addition commit: {additions}")
    commit = additions[0]
    if commit == registration:
        raise RuntimeError("source lock was committed with the registration")
    git("merge-base", "--is-ancestor", registration, commit)
    git("merge-base", "--is-ancestor", commit, "HEAD")
    original = subprocess.run(
        ["git", "show", f"{commit}:{LOCK}"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    if original != (ROOT / LOCK).read_bytes():
        raise RuntimeError("source lock differs from its first committed bytes")
    return commit


def hypothesis() -> dict:
    doc = yaml.safe_load((ROOT / HYP).read_text())
    if doc.get("hypothesis_id") != ID or doc.get("status") != "pre_registered":
        raise RuntimeError("hypothesis identity/status changed")
    roster = doc["sample"]["countries"]
    if len(roster) != 181 or len(set(roster)) != 181:
        raise RuntimeError("fixed country roster is not 181 unique countries")
    return doc


def source_paths(source_root: Path) -> dict[str, Path]:
    paths = {key: source_root / relative for key, (relative, _, _) in SOURCES.items()}
    paths["manifest"] = source_root / MANIFEST
    for key, path in paths.items():
        expected = MANIFEST_SHA if key == "manifest" else SOURCES[key][1]
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"missing or hash-mismatched {key} source: {path}")
    manifest_text = paths["manifest"].read_text()
    for relative, expected, _ in SOURCES.values():
        if str(relative) not in manifest_text or expected not in manifest_text:
            raise RuntimeError(f"source not pinned in publisher fetch manifest: {relative}")
    return paths


def source_keys(paths: dict[str, Path], roster: list[str]) -> dict[str, dict]:
    """Only metadata columns; do not read value or obs_status here."""
    result: dict[str, dict] = {}
    allowed = set(roster)
    for key, (_, _, years) in SOURCES.items():
        table = pq.read_table(paths[key], columns=["country_iso3", "year", "indicator_id"])
        frame = table.to_pandas()
        frame = frame[frame.country_iso3.isin(allowed) & frame.year.isin(years)].copy()
        rows = sorted(
            [str(country) + ":" + str(int(year)) + ":" + str(indicator)
             for country, year, indicator in frame[["country_iso3", "year", "indicator_id"]].itertuples(index=False, name=None)]
        )
        result[key] = {
            "selected_key_rows": len(rows),
            "unique_key_rows": len(set(rows)),
            "key_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
        }
    return result


def prepare_lock(source_root: Path) -> None:
    registration = registration_commit()
    doc = hypothesis()
    paths = source_paths(source_root)
    keys = source_keys(paths, doc["sample"]["countries"])
    expected = {"credit": 181, "manufacturing": 362, "gdp_pc": 181}
    for key, count in expected.items():
        if keys[key]["selected_key_rows"] != count or keys[key]["unique_key_rows"] != count:
            raise RuntimeError(f"fixed key grid incomplete or duplicated: {key}: {keys[key]}")
    data = {
        "schema": "ieset-private-credit-manufacturing-2024-key-lock-v1",
        "hypothesis_id": ID,
        "registration_commit": registration,
        "country_roster_sha256": hashlib.sha256(canonical_bytes(doc["sample"]["countries"])).hexdigest(),
        "source_manifest": {"path": str(MANIFEST), "sha256": MANIFEST_SHA},
        "sources": {
            key: {"path": str(relative), "sha256": expected_sha, "selected_years": list(years), **keys[key]}
            for key, (relative, expected_sha, years) in SOURCES.items()
        },
        "contains_selected_values_or_null_masks": False,
    }
    path = ROOT / LOCK
    if path.exists():
        raise RuntimeError("source lock already exists; do not overwrite it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(data, sort_keys=True, indent=2).encode() + b"\n")
    print(f"key-only lock written: {LOCK}; commit it separately before --run")


def verify_lock(source_root: Path) -> tuple[dict, dict[str, Path], str, str]:
    registration = registration_commit()
    commit = source_lock_commit(registration)
    doc = hypothesis()
    lock = json.loads((ROOT / LOCK).read_text())
    if lock.get("registration_commit") != registration or lock.get("hypothesis_id") != ID:
        raise RuntimeError("source lock registration mismatch")
    if lock.get("country_roster_sha256") != hashlib.sha256(canonical_bytes(doc["sample"]["countries"])).hexdigest():
        raise RuntimeError("source lock roster mismatch")
    paths = source_paths(source_root)
    keys = source_keys(paths, doc["sample"]["countries"])
    for key, (_, expected_sha, years) in SOURCES.items():
        wanted = {"path": str(SOURCES[key][0]), "sha256": expected_sha, "selected_years": list(years), **keys[key]}
        if lock["sources"].get(key) != wanted:
            raise RuntimeError(f"source key lock mismatch: {key}")
    return doc, paths, registration, commit


def selected_values(path: Path, roster: list[str], years: tuple[int, ...]) -> pd.DataFrame:
    frame = pq.read_table(path, columns=["country_iso3", "year", "value", "obs_status"]).to_pandas()
    frame = frame[frame.country_iso3.isin(set(roster)) & frame.year.isin(years)].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate selected country-year source row")
    return frame.set_index(["country_iso3", "year"])


def model_result(doc: dict, paths: dict[str, Path]) -> dict:
    roster = doc["sample"]["countries"]
    frames = {key: selected_values(paths[key], roster, years) for key, (_, _, years) in SOURCES.items()}
    records = []
    missing = 0
    nonblank_status = 0
    invalid_range = 0
    for country in roster:
        wanted = [
            ("credit", (country, 2022)), ("manufacturing", (country, 2022)),
            ("manufacturing", (country, 2024)), ("gdp_pc", (country, 2022)),
        ]
        cells = []
        for source, index in wanted:
            if index not in frames[source].index:
                cells = []
                break
            row = frames[source].loc[index]
            status = row["obs_status"]
            if pd.notna(status) and str(status).strip():
                nonblank_status += 1
                cells = []
                break
            value = pd.to_numeric(row["value"], errors="coerce")
            if not np.isfinite(value):
                cells = []
                break
            cells.append(float(value))
        if len(cells) != 4:
            missing += 1
            continue
        credit, manufacturing_2022, manufacturing_2024, gdp_pc = cells
        if not (0 <= credit <= 300 and 0 <= manufacturing_2022 <= 100
                and 0 <= manufacturing_2024 <= 100 and gdp_pc > 0):
            invalid_range += 1
            continue
        records.append((country, credit, manufacturing_2022, manufacturing_2024,
                        gdp_pc, manufacturing_2024 - manufacturing_2022))
    panel = pd.DataFrame(records, columns=["country", "credit", "manufacturing_2022",
                                           "manufacturing_2024", "gdp_pc", "change"])
    result = {
        "hypothesis_id": ID,
        "verdict": "INCONCLUSIVE",
        "method": "frozen cross-country OLS with HC3 covariance",
        "evidence_tier_recommendation": "calibration",
        "correction": {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                       "school_score_credit": 0, "policy_score_eligible": False,
                       "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False},
        "sample": {"roster_countries": len(roster), "complete_countries": len(panel),
                   "missing_or_status_countries": missing, "nonblank_status_cells": nonblank_status,
                   "out_of_range_countries": invalid_range},
        "selected_2024_values_read_after_committed_lock": True,
    }
    if len(panel) < 80:
        result["reason"] = "frozen complete-country floor failed"
        return result
    credit_iqr = float(np.quantile(panel.credit, .75) - np.quantile(panel.credit, .25))
    result["sample"]["credit_iqr_gdp_points"] = credit_iqr
    if credit_iqr < 10:
        result["reason"] = "frozen credit-variation floor failed"
        return result
    x = np.column_stack([
        np.ones(len(panel)), panel.credit.to_numpy() / 10,
        panel.manufacturing_2022.to_numpy(), np.log(panel.gdp_pc.to_numpy())
    ])
    if int(np.linalg.matrix_rank(x)) != 4:
        result["reason"] = "frozen model rank gate failed"
        return result
    fit = sm.OLS(panel.change.to_numpy(), x).fit(cov_type="HC3")
    beta, se = float(fit.params[1]), float(fit.bse[1])
    low, high = [float(v) for v in fit.conf_int(alpha=.05)[1]]
    if not all(math.isfinite(v) for v in (beta, se, low, high)):
        result["reason"] = "frozen HC3 finiteness gate failed"
        return result
    result["estimate"] = {"beta_per_10_credit_gdp_points": beta, "se_hc3": se,
                          "ci95": [low, high], "p_value_two_sided": float(fit.pvalues[1]),
                          "r_squared": float(fit.rsquared)}
    if beta <= -.10 and high < 0:
        result["verdict"] = "SUPPORTED"
    elif beta >= .10 and low > 0:
        result["verdict"] = "REFUTED"
    else:
        result["verdict"] = "PARTIAL"
    result["reason"] = "frozen sample, variation and HC3 estimator gates passed"
    return result


def render_outputs(result: dict, registration: str, source_commit: str) -> dict[Path, bytes]:
    verdict = result["verdict"]
    sample = result["sample"]
    estimate = result.get("estimate")
    lines = [
        f"# {ID}", "", f"**Verdict: {verdict}** — {result['reason']}", "",
        "Descriptive cross-country calibration only. This does not establish that credit causes manufacturing-share change.",
        "", f"- Complete countries: {sample['complete_countries']} of 181; frozen floor 80.",
        f"- Selected WDI vintage: 2026-05-05; outcome change 2022–2024.",
        f"- Registration commit: `{registration}`; key-only source lock commit: `{source_commit}`.",
        "- School, policy, causal and featured credit: zero.",
    ]
    if estimate:
        lines += [
            f"- Credit IQR: {sample['credit_iqr_gdp_points']:.6f} GDP percentage points; floor 10.",
            f"- Beta: {estimate['beta_per_10_credit_gdp_points']:+.6f} manufacturing-share points per 10 credit/GDP points.",
            f"- HC3 95% CI: [{estimate['ci95'][0]:+.6f}, {estimate['ci95'][1]:+.6f}].",
        ]
    lines += ["", "The source predates registration and the old 1990–2023 result is known; this is neither independent source replication nor a causal policy test.",
              "The WDI manufacturing series measures a GDP share and may change with relative prices or services output.",
              "", "Exact replay: `python3 scripts/run_private_credit_manufacturing_2024_v2.py --verify --source-root <root-with-pinned-WDI-vintages>`.", ""]
    manifest = {
        "hypothesis_id": ID, "status": verdict,
        "runner": "scripts/run_private_credit_manufacturing_2024_v2.py",
        "preregistration_commit": registration, "source_lock_commit": source_commit,
        "source_lock": str(LOCK), "publication_tier": "descriptive_calibration" if verdict != "INCONCLUSIVE" else "inconclusive_archive",
        "vintages": [
            {"publisher": "world_bank_wdi", "series_id": relative.name.split("@")[0],
             "path": str(relative), "sha256": expected_sha,
             "provenance": str(MANIFEST), "provenance_sha256": MANIFEST_SHA}
            for relative, expected_sha, _ in SOURCES.values()
        ],
        "correction": result["correction"],
    }
    packet = {"hypothesis_id": ID, "verdict": verdict,
              "evidence_type": "descriptive", "school_score_eligible": False,
              "policy_score_eligible": False, "claim_limit": "association only, no causal attribution",
              "replication_command": "python3 scripts/run_private_credit_manufacturing_2024_v2.py --verify --source-root <source-root>"}
    replication = (
        "#!/usr/bin/env python3\n"
        "\"\"\"Exact replay through the frozen source-pinned runner.\"\"\"\n"
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, str(root / 'scripts/run_private_credit_manufacturing_2024_v2.py'), '--verify', *sys.argv[1:]]))\n"
    )
    return {
        RUN / "diagnostics.json": (json.dumps(result, sort_keys=True, indent=2) + "\n").encode(),
        RUN / "result_card.md": ("\n".join(lines)).encode(),
        RUN / "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False).encode(),
        RUN / "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        RUN / "replication.py": replication.encode(),
        RUN / "hypothesis.yaml": (ROOT / HYP).read_bytes(),
    }


def execute(source_root: Path, verify: bool) -> None:
    doc, paths, registration, source_commit = verify_lock(source_root)
    result = model_result(doc, paths)
    result["preregistration_commit"] = registration
    result["source_lock_commit"] = source_commit
    result["source_manifest_sha256"] = MANIFEST_SHA
    outputs = render_outputs(result, registration, source_commit)
    if verify:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"exact replay differs: {relative}")
        print(f"exact replay verified: {ID}; verdict {result['verdict']}")
    else:
        if (ROOT / RUN).exists():
            raise RuntimeError("run directory exists; do not overwrite historical result")
        (ROOT / RUN).mkdir(parents=True)
        for relative, content in outputs.items():
            (ROOT / relative).write_bytes(content)
        print(f"run written: {ID}; verdict {result['verdict']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-lock", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.prepare_lock:
        prepare_lock(source_root)
    else:
        execute(source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
