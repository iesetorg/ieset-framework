"""Synthetic, value-blind checks of the frozen weather/crop runner."""
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
    "weather_crop_family", ROOT / "scripts/run_cckp_faostat_weather_crop_2026.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WeatherCropFamilyGuards(unittest.TestCase):
    def test_frozen_grid_and_flag_gate(self):
        self.assertEqual(len(MODULE.CASES), 56)
        self.assertEqual(len({MODULE.case_id(case) for case in MODULE.CASES}), 56)
        self.assertEqual(MODULE.P_MAX, 0.01 / 56)
        crop = {(1717, 5312, "GBR", 2000): (42.0, "A", "ha"),
                (1717, 5312, "GBR", 2001): (42.0, "I", "ha"),
                (1717, 5312, "GBR", 2002): (0.0, "E", "ha")}
        self.assertEqual(MODULE.selected_crop(crop, 1717, 5312, "GBR", 2000, "ha"), (42.0, "A"))
        self.assertIsNone(MODULE.selected_crop(crop, 1717, 5312, "GBR", 2000, "kg/ha"))
        self.assertIsNone(MODULE.selected_crop(crop, 1717, 5312, "GBR", 2001, "ha"))
        self.assertIsNone(MODULE.selected_crop(crop, 1717, 5312, "GBR", 2002, "ha"))

    def test_exact_year_growth_and_weather_control(self):
        case = ("cereals", "area", "temperature")
        roster = {("cereals", "area"): [("GBR", 2000)]}
        weather = {("GBR", 2000): (1.25, 0.75)}
        crops = {(1717, 5312, "GBR", year): (value, "A", "ha")
                 for year, value in [(1998, 100.0), (1999, 110.0), (2000, 121.0)]}
        frame, sample = MODULE.case_frame(case, roster, weather, crops)
        self.assertEqual(sample["complete_rows_before_country_floor"], 1)
        self.assertEqual(sample["valid_rows"], 0)  # five-year country gate
        self.assertAlmostEqual(math.log(121.0 / 110.0), math.log(110.0 / 100.0))

    def test_absolute_anomalies_and_sample_sd(self):
        tas = {f"{year}-07": float(year - 1961) for year in range(1961, 1991)}
        pr = {f"{year}-07": float(2 * (year - 1961)) for year in range(1961, 1991)}
        tas["2000-07"], pr["2000-07"] = 2.0, 2.0
        result = MODULE.climate_departures(tas, pr)
        self.assertAlmostEqual(result[2000][0], 12.5)
        self.assertAlmostEqual(result[2000][1], 27.0 / np.std(list(range(0, 60, 2)), ddof=1))
        self.assertEqual(MODULE.climate_departures({"1961-07": 1}, pr), {})

    def test_country_cr1_matches_independent_statsmodels_fit(self):
        rng = np.random.default_rng(19)
        records = []
        for country in range(31):
            for year in range(20):
                x = abs(1.2 * rng.standard_normal() + country * 0.003 + year * 0.002)
                other = rng.standard_normal()
                prior = rng.standard_normal() * 0.1
                response = -0.07 * x + 0.04 * other + 0.15 * prior + country * 0.001 + year * 0.0003 + 0.08 * rng.standard_normal()
                records.append({"country": f"C{country:02d}", "year": 2000 + year,
                                "x": x, "other": other, "prior": prior, "response": response})
        frame = pd.DataFrame(records)
        material = frame.loc[frame["x"].abs() >= 1.0]
        sample = {"valid_rows": len(frame), "valid_countries": frame["country"].nunique(),
                  "material_exposure_rows": len(material),
                  "material_exposure_countries": material["country"].nunique()}
        verdict, _, result = MODULE.fit_case(frame, sample)
        self.assertEqual(verdict, "SUPPORTED")
        design = patsy.dmatrix("1 + x + other + prior + C(country) + C(year)", frame,
                               return_type="dataframe")
        fit = sm.OLS(frame["response"], design).fit(
            cov_type="cluster", cov_kwds={"groups": frame["country"], "use_correction": True})
        self.assertAlmostEqual(result["coefficient"], float(fit.params["x"]), places=10)
        self.assertAlmostEqual(result["std_error"], float(fit.bse["x"]), places=10)


if __name__ == "__main__":
    unittest.main()
