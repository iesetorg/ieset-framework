"""Synthetic guard checks for the frozen FAOSTAT crop-response family."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("faostat_family", ROOT / "scripts/run_faostat_relative_price_supply_2026.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FAOSTATFamilyGuards(unittest.TestCase):
    def test_eight_distinct_cells_and_family_cutoff(self):
        self.assertEqual(len(MODULE.CASES), 8)
        self.assertEqual({c["group"] for c in MODULE.CASES.values()}, set(MODULE.GROUPS))
        self.assertEqual({c["margin"] for c in MODULE.CASES.values()}, set(MODULE.MARGINS))
        self.assertEqual(MODULE.P_MAX, 0.00125)

    def test_flags_and_positive_measurement_gate(self):
        prices = {(1717, "GBR", 2000): (100.0, "A"), (1717, "GBR", 2001): (100.0, "I")}
        self.assertEqual(MODULE.selected_price(prices, 1717, "GBR", 2000), (100.0, "A"))
        self.assertIsNone(MODULE.selected_price(prices, 1717, "GBR", 2001))
        crops = {(1717, 5312, "GBR", 2000): (0.0, "A", "ha"),
                 (1717, 5312, "GBR", 2001): (42.0, "E", "ha")}
        self.assertIsNone(MODULE.selected_crop(crops, 1717, 5312, "GBR", 2000, "ha"))
        self.assertIsNone(MODULE.selected_crop(crops, 1717, 5312, "GBR", 2001, "kg/ha"))
        self.assertEqual(MODULE.selected_crop(crops, 1717, 5312, "GBR", 2001, "ha"), (42.0, "E"))

    def test_sample_gate_is_inconclusive_without_fit(self):
        verdict, reason, result = MODULE.fit_case(None, {"valid_rows": 499, "valid_countries": 29,
                                                        "material_exposure_rows": 99,
                                                        "material_exposure_countries": 19})
        self.assertEqual(verdict, "INCONCLUSIVE")
        self.assertEqual(result["gates_failed"], ["complete_case_floor", "material_exposure_floor"])


if __name__ == "__main__":
    unittest.main()
