"""Synthetic proof that public cards disclose estimated-only source inputs."""
import importlib.util
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("faostat_family", root / "scripts/run_faostat_relative_price_supply_2026.py")
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)


class FlagDisclosure(unittest.TestCase):
    def test_all_estimated_price_and_crop_inputs_are_explicit(self):
        roles = ("group_price_t_minus_1", "group_price_t", "agriculture_price_t_minus_1",
                 "agriculture_price_t", "outcome_t_minus_1", "outcome_t", "outcome_t_plus_1")
        sample = {"complete_rows_before_country_floor": 3,
                  "admitted_flag_counts_before_country_floor": {f"{role}:E": 3 for role in roles}}
        note = family.flag_disclosure(sample)
        self.assertIn("Every complete-case producer-price index input is FAO E-coded", note)
        self.assertIn("Every crop-outcome input is also FAO E-coded", note)

    def test_mixed_crop_inputs_are_not_called_all_estimated(self):
        price_roles = ("group_price_t_minus_1", "group_price_t", "agriculture_price_t_minus_1", "agriculture_price_t")
        sample = {"complete_rows_before_country_floor": 3,
                  "admitted_flag_counts_before_country_floor": {**{f"{role}:E": 3 for role in price_roles},
                                                                  "outcome_t_plus_1:A": 2, "outcome_t_plus_1:E": 1}}
        note = family.flag_disclosure(sample)
        self.assertIn("Crop-outcome inputs mix", note)
        self.assertNotIn("Every crop-outcome input", note)


if __name__ == "__main__":
    unittest.main()
