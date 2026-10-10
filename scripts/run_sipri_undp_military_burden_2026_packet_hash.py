#!/usr/bin/env python3
"""Output-only packet hash completion after a preliminary corrected fit.

This helper delegates every data, gate and model operation to the frozen
SIPRI-unit adapter. Coefficients and preflight diagnostics must exactly match
the separately committed preliminary-fit audit. The run timestamp may change. It adds a digest of each final
diagnostic to the corresponding evidence packet and updates replication paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_sipri_undp_military_burden_2026 as base
import run_sipri_undp_military_burden_2026_unit_fix as unit

WRAPPER = "scripts/run_sipri_undp_military_burden_2026_packet_hash.py"
AUDIT = "engine/audits/sipri_undp_military_burden_preliminary_fit_2026-10-10.json"
NOTE = "engine/audits/sipri_undp_military_burden_packet_hash_amendment_2026-10-10.md"
AUDIT_SHA256 = "7db1c5e45eb42e559b9c21ed701135bf8c12ab5aaa31d8e22a44d2bce30f81d6"
OUTPUT_AMENDMENT = {
    "type": "packet_digest_and_replication_path_only",
    "preliminary_fit_audit": AUDIT,
    "preliminary_fit_audit_sha256": AUDIT_SHA256,
    "coefficients_seen_before_this_output_fix": True,
    "model_or_gate_change": False,
}
ORIGINAL_CORRECTED_ARTIFACTS = unit.corrected_artifacts
ORIGINAL_CORRECTED_SUMMARY = unit.corrected_summary


def audit_cells() -> dict[str, dict]:
    audit = json.loads((ROOT / AUDIT).read_text())
    if (audit.get("family_id") != base.FAMILY or audit.get("coefficients_seen_before_output_fix") is not True
            or audit.get("model_and_gate_amendment") is not False
            or len(audit.get("cells", [])) != len(base.CASES)):
        raise RuntimeError("preliminary-fit audit is incomplete")
    return {cell["hypothesis_id"]: cell for cell in audit["cells"]}


def hashed_artifacts(*args, **kwargs) -> dict[str, bytes]:
    files = ORIGINAL_CORRECTED_ARTIFACTS(*args, **kwargs)
    diagnostic = json.loads(files["diagnostics.json"])
    prior = audit_cells().get(diagnostic["hypothesis_id"])
    if (prior is None or prior["verdict"] != diagnostic["verdict"]
            or prior["preflight"] != diagnostic["preflight"]
            or prior["primary"] != diagnostic["primary"]):
        raise RuntimeError("preliminary numeric result changed during output-only repair")
    diagnostic["runner"] = WRAPPER
    diagnostic["output_amendment"] = OUTPUT_AMENDMENT
    diagnostic_bytes = (json.dumps(diagnostic, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    files["diagnostics.json"] = diagnostic_bytes
    manifest = yaml.safe_load(files["manifest.yaml"])
    manifest["runner"] = WRAPPER
    manifest["output_amendment"] = OUTPUT_AMENDMENT
    files["manifest.yaml"] = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()
    packet = yaml.safe_load(files["evidence_packet.yaml"])
    packet["reproduction"]["runner"] = WRAPPER
    packet["reproduction"]["command"] = f"python3 {WRAPPER} --source-root <matching local cache> --verify"
    packet["reproduction"]["result_sha256"] = hashlib.sha256(diagnostic_bytes).hexdigest()
    packet["output_amendment"] = OUTPUT_AMENDMENT
    files["evidence_packet.yaml"] = yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode()
    files["result_card.md"] += (
        "\n**Packet audit:** A post-fit, output-only repair added a SHA-256 of the final diagnostic "
        "and updated the replication command. The preliminary coefficient, sample, verdict and gates "
        "match the committed pre-repair audit exactly.\n"
    ).encode()
    files["replication.py"] = (
        "#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\n"
        "source_root = os.environ.get('IESET_RAW_ROOT')\n"
        "if not source_root:\n    raise SystemExit('set IESET_RAW_ROOT to the matching local raw cache')\n"
        f"raise SystemExit(subprocess.call([sys.executable, '{WRAPPER}', '--source-root', source_root, '--verify']))\n"
    ).encode()
    return files


def hashed_summary(*args, **kwargs) -> str:
    return ORIGINAL_CORRECTED_SUMMARY(*args, **kwargs) + (
        "\nA serialization-only amendment followed the preliminary corrected fit: final diagnostic "
        "SHA-256 fields and replay commands were added to all four packets. Frozen numeric outputs, "
        "sample gates and verdicts match the committed preliminary-fit audit exactly.\n"
    )


def output_commit(source_root: Path) -> str:
    adapter_commit = unit.correction_commit(source_root)
    additions = {base.first_addition(path) for path in (WRAPPER, AUDIT, NOTE)}
    if len(additions) != 1:
        raise RuntimeError("packet helper and preliminary-fit audit must be added together")
    commit = additions.pop()
    if commit == adapter_commit or subprocess.run(
            ["git", "merge-base", "--is-ancestor", adapter_commit, commit], cwd=ROOT).returncode:
        raise RuntimeError("packet helper must follow unit adapter")
    for path in (WRAPPER, AUDIT, NOTE):
        base.frozen(path, commit)
    if base.sha256(ROOT / AUDIT) != AUDIT_SHA256:
        raise RuntimeError("preliminary-fit audit hash changed")
    if set(audit_cells()) != {case["id"] for case in base.CASES.values()}:
        raise RuntimeError("preliminary-fit audit members differ")
    for case in base.CASES.values():
        if base.git("ls-tree", "-r", "--name-only", commit, "--", base.paths(case)[2]).strip():
            raise RuntimeError("packet-helper commit already contains a public result packet")
    return commit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    output_commit(args.source_root)
    base.values = unit.corrected_values
    base.artifacts = hashed_artifacts
    base.summary_text = hashed_summary
    base.run(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
