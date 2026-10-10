#!/usr/bin/env python3
"""Post-lock text-decoding adapter for the frozen WBES next-wave runner.

The pinned CSV contains a few non-UTF-8 bytes in text labels. Its selected
country/year/indicator selectors and numeric fields are ASCII. This adapter
changes only decoding errors for the exact CSV's text stream, then invokes the
unchanged, hash-locked estimator. It also records this replay entry point in
the generated packets. See the dated encoding erratum in engine/audits.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

import run_wbes_constraints_next_wave_2026 as frozen


ADAPTER = "scripts/run_wbes_constraints_next_wave_encoding_adapter_2026.py"
RAW_NAME = Path(frozen.SOURCE_FILES["aggregate"]["path"]).name
ORIGINAL_OPEN = Path.open
ORIGINAL_RENDER = frozen.render_outputs


def compatible_open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
    if self.name == RAW_NAME and mode == "r" and encoding == "utf-8-sig":
        if errors not in (None, "replace"):
            raise RuntimeError("unexpected WBES CSV decoder error policy")
        errors = "replace"
    return ORIGINAL_OPEN(self, mode=mode, buffering=buffering, encoding=encoding,
                         errors=errors, newline=newline)


def render_with_erratum(role, diagnostic, spec, lock_commit):
    files = ORIGINAL_RENDER(role, diagnostic, spec, lock_commit)
    packet = yaml.safe_load(files["evidence_packet.yaml"])
    packet["reproduction"]["frozen_runner"] = frozen.RUNNER
    packet["reproduction"]["runner"] = ADAPTER
    packet["reproduction"]["command"] = (
        "python3 " + ADAPTER + " --verify --source-root <pinned-cache-root>"
    )
    packet["reproduction"]["encoding_erratum"] = (
        "engine/audits/wbes_constraints_next_wave_encoding_erratum_2026-10-10.md"
    )
    files["evidence_packet.yaml"] = yaml.safe_dump(
        packet, sort_keys=False, allow_unicode=True
    ).encode()
    manifest = yaml.safe_load(files["manifest.yaml"])
    manifest["frozen_runner"] = frozen.RUNNER
    manifest["runner"] = ADAPTER
    manifest["encoding_erratum"] = packet["reproduction"]["encoding_erratum"]
    files["manifest.yaml"] = yaml.safe_dump(
        manifest, sort_keys=False, allow_unicode=True
    ).encode()
    replay = (
        "#!/usr/bin/env python3\nimport os\nimport subprocess\nimport sys\nfrom pathlib import Path\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "source_root = os.environ.get('IESET_SOURCE_ROOT', str(root))\n"
        "raise SystemExit(subprocess.call([sys.executable, str(root / '" + ADAPTER
        + "'), '--verify', '--source-root', source_root], cwd=root))\n"
    )
    files["replication.py"] = replay.encode()
    files["encoding_erratum.json"] = (
        json.dumps({
            "schema": "ieset-post-lock-encoding-erratum-v1",
            "frozen_runner": frozen.RUNNER,
            "adapter": ADAPTER,
            "source_sha256": frozen.SOURCE_FILES["aggregate"]["sha256"],
            "change": "replace malformed UTF-8 bytes in CSV text labels during parsing",
            "estimator_or_gate_change": False,
        }, sort_keys=True, indent=2) + "\n"
    ).encode()
    return files


def main():
    Path.open = compatible_open
    frozen.render_outputs = render_with_erratum
    frozen.main()


if __name__ == "__main__":
    main()
