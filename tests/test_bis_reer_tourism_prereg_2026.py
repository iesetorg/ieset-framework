"""Synthetic estimator and outcome-access checks for the frozen tourism family."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_bis_reer_tourism_arrivals_2026.py"
SPEC = importlib.util.spec_from_file_location("reer_tourism_runner", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class TourismPreregTests(unittest.TestCase):
    def test_tourism_preflight_projects_keys_only(self) -> None:
        original = pd.read_parquet
        selected_columns: list[list[str]] = []

        def guarded_read(path, *args, **kwargs):
            if str(path).endswith("ST.INT.ARVL@2026-05-05T203952Z.parquet"):
                columns = list(kwargs["columns"])
                selected_columns.append(columns)
                self.assertEqual(columns, ["country_iso3", "year", "indicator_id"])
            return original(path, *args, **kwargs)

        with patch.object(runner.pd, "read_parquet", side_effect=guarded_read):
            keys = runner.wdi_keys("arrivals")
        self.assertEqual(len(selected_columns), 1)
        self.assertIn(("GBR", 2018), keys)
        self.assertNotIn(("WLD", 2018), keys)

    def test_run_cannot_build_panel_without_source_lock(self) -> None:
        with (
            patch.object(runner, "check_sources", return_value={}),
            patch.object(runner, "preflight", return_value={}),
            patch.object(runner, "registration_commit", return_value="registration"),
            patch.object(runner, "check_source_lock", side_effect=RuntimeError("lock absent")),
            patch.object(runner, "build_panel", side_effect=AssertionError("tourism opened")),
            patch.object(sys, "argv", [str(SCRIPT), "--run"]),
        ):
            with self.assertRaisesRegex(RuntimeError, "lock absent"):
                runner.main()

    def test_synthetic_negative_positive_and_null_associations(self) -> None:
        rng = np.random.default_rng(20261010)
        country_effect = rng.normal(0, 0.025, 30)
        year_effect = rng.normal(0, 0.01, 15)
        rows = []
        for country_index in range(30):
            country = f"C{country_index:02d}"
            for year_index, year in enumerate(range(2004, 2019)):
                x = int(rng.random() < 0.25)
                baseline = 10 + 0.06 * country_index + 0.02 * year_index + rng.normal(0, 0.15)
                gdp = 2 + rng.normal(0, 1.5)
                noise = rng.normal(0, 0.025)
                common = (
                    0.015 * baseline + 0.003 * gdp + country_effect[country_index]
                    + year_effect[year_index] + noise
                )
                rows.append({
                    "country_iso3": country, "year": year, "x": x,
                    "baseline_log_arrivals": baseline, "gdp_growth": gdp,
                    "common": common,
                })
        frame = pd.DataFrame(rows)
        event_countries = int(frame.loc[frame.x.eq(1), "country_iso3"].nunique())
        self.assertGreaterEqual(event_countries, 15)
        for signal, expected in [(-0.08, "SUPPORTED"), (+0.08, "REFUTED"), (0.0, "PARTIAL")]:
            panel = frame.drop(columns="common").copy()
            panel["arrival_growth"] = frame["common"] + signal * frame["x"]
            gate = {
                "complete_rows": len(panel), "complete_countries": 30,
                "event_rows": int(panel.x.sum()), "event_countries": event_countries,
            }
            result = runner.estimate(panel, gate)
            self.assertEqual(result["verdict"], expected, result)
            self.assertIsNotNone(result["primary"])


if __name__ == "__main__":
    unittest.main()
