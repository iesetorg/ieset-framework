"""The 2022 IRA must have one policy identity and reciprocal movement links."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_ira_policy_is_single_dated_event_with_reviewed_links() -> None:
    duplicate = ROOT / "policies" / "us_ira_inflation_reduction_act_2022.yaml"
    assert not duplicate.exists()

    policy = yaml.safe_load((ROOT / "policies" / "us_ira_2022.yaml").read_text())
    assert policy["policy_id"] == "us_ira_2022"
    assert policy["timeframe"]["start"] == 2022
    assert policy["timeframe"]["enacted_date"] == "2022-08-16"
    assert policy["suppress_inferred_axis_links"] is True
    assert policy["linked_hypotheses_inferred"] == []

    movements = {
        "biden_ira_chips_2022",
        "us_biden_administration_broad_2021_2025",
    }
    assert set(policy["enacted_by"]) == movements
    for movement_id in movements:
        movement = yaml.safe_load((ROOT / "movements" / f"{movement_id}.yaml").read_text())
        assert "us_ira_2022" in movement["policies"]
        assert "us_ira_inflation_reduction_act_2022" not in movement["policies"]
