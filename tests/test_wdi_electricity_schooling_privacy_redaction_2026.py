"""The published PLAN permits exactly two source-root token redactions."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "schooling_privacy", ROOT / "scripts/verify_wdi_electricity_schooling_privacy_redaction_2026.py"
)
assert SPEC and SPEC.loader
redaction = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(redaction)


def test_only_the_registered_two_token_redaction_is_accepted() -> None:
    registered = subprocess.check_output(
        ["git", "show", f"{redaction.REGISTRATION}:{redaction.PLAN}"], cwd=ROOT
    )
    expected = redaction.strict_redacted_image(registered)
    assert (ROOT / redaction.PLAN).read_bytes() == expected
    assert redaction.sha(expected) == redaction.REDACTED_PLAN_SHA
    with pytest.raises(RuntimeError, match="pinned hash"):
        redaction.strict_redacted_image(registered.replace(b"Five", b"Four", 1))
    with pytest.raises(RuntimeError, match="beyond the two"):
        original = redaction.strict_redacted_image
        try:
            redaction.strict_redacted_image = lambda _: expected + b"extra"
            redaction.attest_plan()
        finally:
            redaction.strict_redacted_image = original


def test_current_plan_has_no_absolute_machine_source_root() -> None:
    current = (ROOT / redaction.PLAN).read_bytes()
    assert b"--source-root /" not in current
    assert current.count(redaction.REDACTION) == 2
