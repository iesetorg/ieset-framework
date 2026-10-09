"""The significance cutoff must not be parsed as a coefficient sign."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_panel_fe import infer_claim_direction


GENERIC_RULE = (
    "SUPPORTED if the treatment coefficient has the predicted sign at p<0.10. "
    "REFUTED if the opposite sign is significant at p<0.10. Otherwise PARTIAL."
)


def test_generic_rule_uses_positive_claim_not_p_cutoff():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim": "Higher measured income increases adult survival.",
        "falsification": {"rule": GENERIC_RULE},
    }
    assert infer_claim_direction(spec) == "+"


def test_generic_rule_uses_negative_claim_not_p_cutoff():
    spec = {
        "hypothesis_id": "unambiguous_claim_without_slug_shortcut",
        "claim": "Measured exposure reduces adult survival.",
        "falsification": {"rule": GENERIC_RULE},
    }
    assert infer_claim_direction(spec) == "-"


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
