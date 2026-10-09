"""The significance cutoff must not be parsed as a coefficient sign."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_panel_fe import infer_claim_direction, verdict_from_estimate


GENERIC_RULE = (
    "SUPPORTED if the treatment coefficient has the predicted sign at p<0.10. "
    "REFUTED if the opposite sign is significant at p<0.10. Otherwise PARTIAL."
)


def test_generic_rule_requires_an_explicit_direction_for_positive_claim():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim": "Higher measured income increases adult survival.",
        "falsification": {"rule": GENERIC_RULE},
    }
    assert infer_claim_direction(spec) == "?"


def test_generic_rule_requires_an_explicit_direction_for_negative_claim():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim": "Measured exposure reduces adult survival.",
        "falsification": {"rule": GENERIC_RULE},
    }
    assert infer_claim_direction(spec) == "?"


def test_explicit_coefficient_inequalities_still_take_precedence():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim": "Higher measured income increases adult survival.",
        "falsification": {"rule": "SUPPORTED if the treatment coefficient < 0 at p<0.10."},
    }
    assert infer_claim_direction(spec) == "-"
    spec["falsification"]["rule"] = "SUPPORTED if beta > 0 at p<0.10."
    assert infer_claim_direction(spec) == "+"


def test_machine_readable_direction_still_wins():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim_direction": "+",
        "claim": "Higher measured exposure reduces adult survival.",
        "falsification": {"rule": GENERIC_RULE},
    }
    assert infer_claim_direction(spec) == "+"


def test_generic_unpinned_rule_cannot_award_a_significant_verdict():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim": "Measured exposure reduces adult survival.",
        "falsification": {"rule": GENERIC_RULE},
    }
    verdict, reason = verdict_from_estimate(
        {"coefficient": -1.2, "p_value": 0.001}, infer_claim_direction(spec)
    )
    assert verdict == "PARTIAL"
    assert "not auto-inferred" in reason
