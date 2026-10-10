#!/usr/bin/env python3
"""Transparent SIPRI fraction-to-percentage-point repair for the frozen test.

The registered words, share bounds, material threshold and beta units say
percentage points, while the SIPRI Share-of-GDP parquet stores fractions.
This wrapper changes only that physical unit, before any coefficient was
estimated; it preserves the registered runner, model, sample and gates.
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
sys.path.insert(0, str(ROOT / 'scripts'))
import run_sipri_military_fixed_investment_2026 as base

WRAPPER = 'scripts/run_sipri_military_fixed_investment_2026_unit_fix.py'
CORRECTION = {
    'type': 'source_unit_conversion',
    'source_role': 'military',
    'source_stored_unit': 'fraction of GDP',
    'registered_unit': 'percentage points of GDP',
    'exact_multiplier': 100,
    'scope': 'SIPRI military input values only; no change to cohort, endpoints, controls, estimator, significance rule or any registered threshold',
    'first_attempt': 'First locked execution stopped at the material-change coverage gate (0 material rows among 485 complete rows); no coefficient or directional result was estimated.',
    'first_attempt_diagnostics': 'engine/audits/sipri_military_fixed_investment_unscaled_diagnostic_2026-10-10.json',
    'first_attempt_diagnostics_sha256': 'd159451b9610649ce9c1f3aecd64d56bbef9872519f027894ced6760513ba34a',
}
original_values = base.series_values
original_artifacts = base.artifacts


def corrected_values(path: Path, role: str, roster: list[tuple[str, str, int]]) -> dict[tuple[str, int], float]:
    values = original_values(path, role, roster)
    if role == 'military':
        return {key: value * 100.0 for key, value in values.items()}
    return values


def corrected_artifacts(result: dict, registration: str, locked: str, stamp: str) -> dict[str, bytes]:
    files = original_artifacts(result, registration, locked, stamp)
    diag = json.loads(files['diagnostics.json'])
    diag['runner'] = WRAPPER
    diag['unit_correction'] = CORRECTION
    diagnostic_bytes = base.js(diag)
    manifest = yaml.safe_load(files['manifest.yaml'])
    manifest['runner'] = WRAPPER
    manifest['unit_correction'] = CORRECTION
    packet = yaml.safe_load(files['evidence_packet.yaml'])
    packet['reproduction']['runner'] = WRAPPER
    packet['reproduction']['command'] = f'python3 {WRAPPER} verify --source-root /path/to/IESET'
    packet['reproduction']['result_sha256'] = hashlib.sha256(diagnostic_bytes).hexdigest()
    packet['unit_correction'] = CORRECTION
    statement = ('\nSource-unit repair: the pinned SIPRI Share-of-GDP parquet stores fractions; '
        'this replay converts them ×100 to the registered percentage-point unit. '
        'The uncorrected locked attempt stopped at its material-change gate and estimated no coefficient. '
        'No registered threshold or model changed.\n')
    replication = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root=Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable,str(root/{WRAPPER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
    files.update({'diagnostics.json': diagnostic_bytes,
        'manifest.yaml': base.ya(manifest), 'evidence_packet.yaml': base.ya(packet),
        'result_card.md': files['result_card.md'] + statement.encode(),
        '_report': files['_report'] + statement.encode(),
        'replication.py': replication.encode()})
    return files


def correction_commit(source_root: Path) -> str:
    paths = base.source_paths(source_root)
    registration = base.registration_commit(paths)
    locked = base.lock_commit(registration)
    added = base.first_add(WRAPPER)
    if added in (registration, locked) or subprocess.run(
        ['git', 'merge-base', '--is-ancestor', locked, added], cwd=ROOT).returncode:
        raise RuntimeError('unit-repair wrapper must be committed after source lock')
    base.frozen(WRAPPER, added)
    audit = ROOT / CORRECTION['first_attempt_diagnostics']
    if base.sha(audit) != CORRECTION['first_attempt_diagnostics_sha256']:
        raise RuntimeError('first unit-audit diagnostic hash mismatch')
    base.frozen(CORRECTION['first_attempt_diagnostics'], added)
    if base.git('ls-tree', '-r', '--name-only', added, '--', base.RUN_DIR).strip():
        raise RuntimeError('unit-repair commit already contained measured result')
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action', choices=['measure', 'verify'])
    parser.add_argument('--source-root', type=Path, default=ROOT)
    args = parser.parse_args()
    correction_commit(args.source_root)
    base.series_values = corrected_values
    base.artifacts = corrected_artifacts
    return base.main()


if __name__ == '__main__':
    raise SystemExit(main())
