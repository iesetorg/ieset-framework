#!/usr/bin/env python3
"""Post-measurement label-only repair and exact replay for the frozen pay family.

The preregistered runner uses a shared estimator whose generic method label
says "prior employment growth". Its fifth design column actually contains
prior CPI-deflated compensation growth in this family. This wrapper checks
the original uncommitted outputs byte-for-byte before the first result commit,
then corrects that label and the replay entrypoint without changing data,
sample, coefficients, uncertainty, gates, or verdicts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_oecd_pdb_sector_real_compensation_2026 as frozen

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_oecd_pdb_sector_real_compensation_2026_metadata_fix.py"
OLD_DIAGNOSTIC_SHA = {
    "oecd_pdb_manufacturing_productivity_next_year_real_compensation_2026": "0342e712eb5553ae1233f2e6b271217224044a630412fe69d2757955621f67b2",
    "oecd_pdb_wholesale_retail_productivity_next_year_real_compensation_2026": "821457e2498f6c4f3eeb1ff0ed994de8eb3c4c7ee4bef3997b04fd25739018cf",
    "oecd_pdb_ict_productivity_next_year_real_compensation_2026": "59e6c94f8282e4261a0c3478c35723a4cf232b175f8fbaeccb62df530a07c330",
}
OLD_REPORT_SHA = "974fb3b6d252219742f180f9ce89f70db08e0566644a938525a0841d70dfd035"
OLD_METHOD = "equal-row country/year FE OLS with prior employment growth; country CR1 cluster t(G-1)"
NEW_METHOD = "equal-row country/year FE OLS with prior real compensation growth; country CR1 cluster t(G-1)"
ORIGINAL_FIT = frozen.core.fit


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected(pdb_path: Path, cpi_path: Path, run_utc: str) -> tuple[list[dict], dict[str, dict[str, bytes]], bytes]:
    diagnostics = frozen.measured_results(pdb_path, cpi_path, run_utc)
    packets = {item["hypothesis_id"]: frozen.packet_files(item, (ROOT / frozen.SPEC_RELS[i]).read_bytes())
               for i, item in enumerate(diagnostics)}
    return diagnostics, packets, frozen.report(diagnostics)


def repair_fit(rows: list[tuple[str, int, float, float, float]], *, full: bool = True) -> dict | None:
    result = ORIGINAL_FIT(rows, full=full)
    if result is not None and full:
        if result.get("method") != OLD_METHOD:
            raise RuntimeError("unexpected shared estimator method label")
        result["method"] = NEW_METHOD
    return result


def compare_saved(packets: dict[str, dict[str, bytes]], report: bytes) -> None:
    for hid, files in packets.items():
        for name, payload in files.items():
            path = ROOT / "engine/runs" / hid / name
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"exact replay mismatch: {path}")
    if (ROOT / frozen.REPORT_REL).read_bytes() != report:
        raise RuntimeError("exact replay mismatch: aggregate audit")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("repair", "verify"))
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    pdb_path, cpi_path = frozen.source_paths(args.source_root)
    registration = frozen.registration_commit()
    locks = frozen.committed_locks(registration, pdb_path, cpi_path)
    prior = json.loads((ROOT / frozen.DIAG_RELS[0]).read_text())
    run_utc = prior["run_utc"]
    if args.command == "repair":
        if frozen.git("ls-tree", "-r", "--name-only", "HEAD", "--", *frozen.DIAG_RELS).strip():
            raise RuntimeError("first measured result already committed; refuse metadata rewrite")
        _, original, report = expected(pdb_path, cpi_path, run_utc)
        compare_saved(original, report)
        if sha(report) != OLD_REPORT_SHA:
            raise RuntimeError("unexpected original aggregate audit")
        for hid, files in original.items():
            if sha(files["diagnostics.json"]) != OLD_DIAGNOSTIC_SHA[hid]:
                raise RuntimeError(f"unexpected original measured result: {hid}")
    frozen.core.fit = repair_fit
    frozen.RUNNER_REL = RUNNER
    diagnostics, packets, report = expected(pdb_path, cpi_path, run_utc)
    if args.command == "repair":
        for hid, files in packets.items():
            target = ROOT / "engine/runs" / hid
            for name, payload in files.items():
                (target / name).write_bytes(payload)
        (ROOT / frozen.REPORT_REL).write_bytes(report)
    else:
        run_commits = {frozen.first_add(relative) for relative in frozen.DIAG_RELS}
        if len(run_commits) != 1 or not frozen.ancestor(locks[-1], next(iter(run_commits))):
            raise RuntimeError("result commit predates final source lock or differs across cells")
        compare_saved(packets, report)
    for item in diagnostics:
        result = item["result"]
        print(json.dumps({"id": item["hypothesis_id"], "verdict": result["verdict"],
                          "rows": result["sample"]["valid_rows"],
                          "beta": None if result["primary"] is None else result["primary"]["beta"],
                          "holm_p": result["holm_adjusted_p"],
                          "method": None if result["primary"] is None else result["primary"]["method"]},
                         sort_keys=True))


if __name__ == "__main__":
    main()
