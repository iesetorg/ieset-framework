"""A reviewed policy must not regain generic axis-overlap evidence links."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import close_gaps  # noqa: E402
import link_policies_to_hypotheses as linker  # noqa: E402


def test_reviewed_policy_schema_requires_an_empty_inferred_list():
    schema = json.loads((ROOT / "schemas" / "policy.schema.json").read_text())
    policy = yaml.safe_load(
        (ROOT / "policies" / "pe_us_fta_implementation_2009.yaml").read_text()
    )
    validator = Draft202012Validator(schema)
    assert not list(validator.iter_errors(policy))

    policy["linked_hypotheses_inferred"] = ["unrelated_axis_match"]
    assert list(validator.iter_errors(policy))


def test_peru_treaty_review_survives_both_linkers(tmp_path, monkeypatch):
    source = ROOT / "policies" / "pe_us_fta_implementation_2009.yaml"
    policy = yaml.safe_load(source.read_text())
    assert policy["suppress_inferred_axis_links"] is True
    assert policy["linked_hypotheses_inferred"] == []
    assert policy["linked_hypotheses"] == ["peru_us_fta_bilateral_exports_2009"]

    # The overlap algorithm still finds candidates; the reviewed policy is
    # deliberately exempt because they do not test this specific treaty.
    ranked = linker.score_policy(policy, linker.load_hyp_axis_index())
    assert ranked
    path = tmp_path / source.name
    path.write_text(source.read_text())
    before = path.read_bytes()
    assert linker.update_policy_yaml(path, [ranked[0][0]], dry_run=False) == (
        False,
        "reviewed-no-inferred-links",
    )

    monkeypatch.setattr(close_gaps, "list_policy_files", lambda: [path])
    monkeypatch.setattr(
        close_gaps,
        "load_hypothesis_axis_index",
        lambda: {ranked[0][0]: {"regulatory.trade_openness"}},
    )
    result = close_gaps.close_orphans(dry_run=False)
    assert result["policies_inferred_written"] == 0
    assert path.read_bytes() == before


def test_unreviewed_policy_still_receives_axis_overlap_links(tmp_path, monkeypatch):
    policy = {
        "policy_id": "example_trade_policy",
        "axes_moved": [{"axis": "regulatory.trade_openness", "magnitude": "strong"}],
        "linked_hypotheses_inferred": [],
    }
    path = tmp_path / "example_trade_policy.yaml"
    path.write_text(yaml.safe_dump(policy))
    assert linker.update_policy_yaml(path, ["trade_example"], dry_run=False) == (
        True,
        "wrote",
    )
    assert yaml.safe_load(path.read_text())["linked_hypotheses_inferred"] == [
        "trade_example"
    ]

    path.write_text(yaml.safe_dump(policy))
    monkeypatch.setattr(close_gaps, "list_policy_files", lambda: [path])
    monkeypatch.setattr(
        close_gaps,
        "load_hypothesis_axis_index",
        lambda: {"trade_example": {"regulatory.trade_openness"}},
    )
    result = close_gaps.close_orphans(dry_run=False)
    assert result["policies_inferred_written"] == 1
    assert yaml.safe_load(path.read_text())["linked_hypotheses_inferred"] == [
        "trade_example"
    ]
