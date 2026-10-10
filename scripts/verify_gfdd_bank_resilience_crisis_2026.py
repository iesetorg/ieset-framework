#!/usr/bin/env python3
"""Replay frozen GFDD results while checking the saved diagnostic checksum.

The preregistered runner must remain byte-for-byte frozen at its registration
commit. Its JSON/YAML comparator accepts tiny numeric differences, but its
packet comparison also hashes newly serialized floats. This companion verifier
compares recomputed values under that original tolerance and separately checks
that every saved packet hashes its saved diagnostics bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

import run_gfdd_bank_resilience_crisis_2026 as frozen


def verify(source_root: Path) -> dict[str, str]:
    paths = frozen.source_paths(source_root)
    registration = frozen.registration_commit(paths)
    locks = frozen.lock_commits(registration)
    roster = frozen.loaded_roster(paths)
    values, income = frozen.selected_values(paths)
    results = {}
    for cell in frozen.CELLS:
        panel, gate = frozen.measured_panel(cell, roster, values, income)
        results[frozen.hid(cell)] = frozen.estimate(panel, gate)
    frozen.holm(results)

    saved_results = {}
    for cell in frozen.CELLS:
        identifier = frozen.hid(cell)
        folder = frozen.ROOT / frozen.run_rel(cell)
        saved_diagnostic_bytes = (folder / 'diagnostics.json').read_bytes()
        saved_diagnostic = json.loads(saved_diagnostic_bytes)
        saved_results[identifier] = saved_diagnostic['result']
        expected = frozen.artifacts(
            cell, results[identifier], registration, locks[identifier],
            saved_diagnostic['run_utc'],
        )
        saved_artifacts = frozen.artifacts(
            cell, saved_diagnostic['result'], registration, locks[identifier],
            saved_diagnostic['run_utc'],
        )
        for name, content in expected.items():
            path = folder / name
            label = f'{identifier}:{name}'
            if name.endswith('.yaml') and name != 'hypothesis.yaml':
                frozen.equal_close(
                    yaml.safe_load(path.read_text()),
                    yaml.safe_load(saved_artifacts[name]),
                    f'{label}:saved',
                )
            elif path.read_bytes() != saved_artifacts[name]:
                raise AssertionError(f'{label}: saved artifact differs from saved result')
            if name == 'evidence_packet.yaml':
                actual_packet = yaml.safe_load(path.read_text())
                replay_packet = yaml.safe_load(content)
                saved_hash = hashlib.sha256(saved_diagnostic_bytes).hexdigest()
                if actual_packet['reproduction']['result_sha256'] != saved_hash:
                    raise AssertionError(f'{identifier}: saved diagnostic checksum mismatch')
                replay_packet['reproduction']['result_sha256'] = saved_hash
                frozen.equal_close(actual_packet, replay_packet, label)
            elif name.endswith('.json'):
                frozen.equal_close(json.loads(path.read_text()), json.loads(content), label)
            elif name.endswith('.yaml') and name != 'hypothesis.yaml':
                frozen.equal_close(yaml.safe_load(path.read_text()), yaml.safe_load(content), label)
    if (frozen.ROOT / frozen.REPORT).read_text() != frozen.report_text(saved_results, registration, locks):
        raise AssertionError('family result report differs from replay')
    return {identifier: result['verdict'] for identifier, result in results.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--source-root', type=Path, default=frozen.ROOT)
    args = parser.parse_args()
    print('verified GFDD numeric replay and saved diagnostic checksums', verify(args.source_root))


if __name__ == '__main__':
    main()
