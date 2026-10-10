"""Synthetic checks for the frozen named-crop PPI/weather runner."""
import importlib.util
import math
import pathlib
import unittest

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "weather_ppi_family", ROOT / "scripts/run_cckp_faostat_weather_named_crop_ppi_2026.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WeatherPriceFamilyGuards(unittest.TestCase):
    def test_family_and_finite_gate(self):
        self.assertEqual(MODULE.FAMILY_SIZE, 118)
        self.assertAlmostEqual(MODULE.P_MAX, 0.01 / 118)
        self.assertEqual(MODULE.case_id(388, "temperature"),
                         "cckp_faostat_crop388_temperature_forward_ppi_2026")
        self.assertIsNone(MODULE.finite(float("nan")))
        self.assertIsNone(MODULE.finite(None))
        self.assertEqual(MODULE.canon_number(100.0), (100.0).hex())

    def test_absolute_weather_departures(self):
        tas = {f"{year}-07": float(year - 1961) for year in range(1961, 1991)}
        pr = {f"{year}-07": float(2 * (year - 1961)) for year in range(1961, 1991)}
        tas["2000-07"], pr["2000-07"] = 2.0, 2.0
        result = MODULE.climate_departures(tas, pr)
        self.assertAlmostEqual(result[2000][0], 12.5)
        self.assertAlmostEqual(result[2000][1], 27.0 / np.std(list(range(0, 60, 2)), ddof=1))
        self.assertEqual(MODULE.climate_departures({"1961-07": 1}, pr), {})

    def test_exact_future_growth_and_flag_attrition(self):
        keys = [("GBR", 2000), ("GBR", 2001)]
        weather = {("GBR", 2000): (1.2, 0.8), ("GBR", 2001): (0.2, 1.1)}
        prices = {(388, "GBR", 1999): (100.0, "A"),
                  (388, "GBR", 2000): (110.0, "E"),
                  (388, "GBR", 2001): (121.0, "X"),
                  (388, "GBR", 2002): (133.1, "I")}
        frame, sample = MODULE.item_frame(388, keys, weather, prices)
        self.assertEqual(sample["complete_rows_before_country_floor"], 1)
        self.assertEqual(sample["dropped"]["excluded_ppi_flag"], 1)
        self.assertEqual(sample["valid_rows"], 0)  # five-year-country gate
        self.assertEqual(sample["admitted_ppi_flag_counts_before_country_floor"]["t_plus_1:X"], 1)
        self.assertAlmostEqual(math.log(121.0 / 110.0), math.log(110.0 / 100.0))

    def test_country_cr1_against_independent_statsmodels(self):
        rng = np.random.default_rng(19)
        rows = []
        for country in range(31):
            for year in range(20):
                x = abs(1.2 * rng.standard_normal() + country * 0.003 + year * 0.002)
                other = rng.standard_normal()
                prior = rng.standard_normal() * 0.1
                response = (0.08 * x + 0.04 * other + 0.15 * prior +
                            country * 0.001 + year * 0.0003 + 0.08 * rng.standard_normal())
                rows.append({"country": f"C{country:02d}", "year": 2000 + year,
                             "x": x, "other": other, "prior": prior, "response": response})
        frame = pd.DataFrame(rows)
        material = frame.loc[frame["x"] >= 1.0]
        sample = {"valid_rows": len(frame), "valid_countries": frame["country"].nunique(),
                  "material_exposure_rows": len(material),
                  "material_exposure_countries": material["country"].nunique()}
        verdict, _, result = MODULE.fit_case(frame, sample)
        self.assertEqual(verdict, "SUPPORTED")
        design = patsy.dmatrix("1 + x + other + prior + C(country) + C(year)",
                               frame, return_type="dataframe")
        fit = sm.OLS(frame["response"], design).fit(
            cov_type="cluster", cov_kwds={"groups": frame["country"], "use_correction": True})
        self.assertAlmostEqual(result["coefficient"], float(fit.params["x"]), places=10)
        self.assertAlmostEqual(result["std_error"], float(fit.bse["x"]), places=10)


if __name__ == "__main__":
    unittest.main()
