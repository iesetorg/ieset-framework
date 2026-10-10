"""The imported chronology must preserve source identity and uncertainty."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("atlas_constitutional_import", ROOT / "scripts/import_atlas_constitutional_history.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class ConstitutionalHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.crosswalk, cls.provenance = IMPORTER.load_pinned(ROOT)
        cls.history = IMPORTER.build_history(cls.rows, cls.crosswalk, cls.provenance)
        cls.countries = {country["iso3"]: country for country in cls.history["countries"]}
        cls.events = [event for country in cls.history["countries"] for event in country["events"]]
        cls.events += [event for entity in cls.history["historical_entities"] for event in entity["events"]]

    def test_pinned_release_reproduces_committed_output(self):
        self.assertEqual(len(self.rows), 20638)
        self.assertEqual(len(self.events), 4133)
        self.assertEqual(len({event["id"] for event in self.events}), 4133)
        self.assertEqual(json.loads((ROOT / IMPORTER.OUTPUT_RELATIVE).read_text()), self.history)

    def test_duplicate_country_year_events_are_all_retained(self):
        for name, year in [("Burkina Faso (Upper Volta)", 2022), ("Sudan", 2019), ("Syria", 2025)]:
            source = [row for row in self.rows if row["country"] == name and row["year"] == year and row["event_type"] != "non-event"]
            actual = [event for event in self.events if event["source_country"] == name and event["start_year"] == year]
            self.assertEqual(len(source), 2)
            self.assertEqual({event["source_row_id"] for event in actual}, {row["source_row_id"] for row in source})

    def test_known_events_retain_source_identifiers(self):
        for iso3, year, event_id in [("USA", 1789, 1041), ("FRA", 1791, 396), ("BDI", 1962, 167)]:
            events = [event for event in self.countries[iso3]["events"] if event["start_year"] == year]
            self.assertTrue(any(event["source_event_code"] == "new" and event["source_event_id"] == event_id for event in events))

    def test_serbia_does_not_inherit_all_yugoslav_events(self):
        serbian = {event["source_row_id"] for event in self.countries["SRB"]["events"]}
        yugoslav = {event["source_row_id"] for event in self.countries["YUG"]["events"]}
        self.assertTrue(yugoslav)
        self.assertFalse(serbian.intersection(yugoslav))

    def test_no_forward_fill_or_scoring_fields(self):
        forbidden = {"end_year", "axes", "axes_summary", "axes_moved", "position_id", "cluster", "direction"}
        for event in self.events:
            self.assertLessEqual(event["start_year"], 2025)
            self.assertGreaterEqual(event["start_year"], 1789)
            self.assertFalse(forbidden.intersection(event))
        self.assertEqual(self.countries["USA"]["coverage"]["end_year"], 2019)
        self.assertEqual(self.history["dataset"]["coverage_end"], 2025)

    def test_successor_countries_do_not_receive_soviet_events(self):
        soviet = self.countries["SUN"]["events"]
        self.assertTrue(soviet)
        self.assertTrue(all(1922 <= event["start_year"] <= 1991 for event in soviet))
        for iso3 in ["RUS", "UKR", "GEO", "ARM"]:
            ids = {event["source_row_id"] for event in self.countries[iso3]["events"]}
            self.assertFalse(ids.intersection(event["source_row_id"] for event in soviet))

    def test_historical_predecessors_are_not_nationwide_country_events(self):
        for iso3, earliest in [("DEU", 1871), ("ITA", 1861), ("TUR", 1923)]:
            self.assertGreaterEqual(self.countries[iso3]["coverage"]["start_year"], earliest)
        unmapped_names = {entity["source_country"] for entity in self.history["historical_entities"]}
        self.assertIn("German Democratic Republic", unmapped_names)
        self.assertIn("Germany (Prussia)", unmapped_names)

    def test_registry_historical_and_disputed_codes_keep_separate_rows(self):
        self.assertTrue(self.countries["CSK"]["events"])
        self.assertTrue(self.countries["XKX"]["events"])
        csk = {event["source_row_id"] for event in self.countries["CSK"]["events"]}
        for iso3 in ["CZE", "SVK"]:
            self.assertFalse(csk.intersection(event["source_row_id"] for event in self.countries[iso3]["events"]))
        registry = json.loads((ROOT / "data/atlas/countries.json").read_text())
        self.assertEqual(set(self.countries), {country["iso3"] for country in registry})

    def test_absence_and_uncodified_status_are_explicit(self):
        self.assertEqual(self.countries["LCA"]["status"], "no_recorded_events")
        self.assertIn("does not mean", self.countries["LCA"]["summary"])
        self.assertEqual(self.countries["ATA"]["status"], "not_covered")
        self.assertIsNone(self.countries["ATA"]["coverage"]["start_year"])
        self.assertIn("uncodified", self.countries["GBR"]["mapping_note"])

    def test_undefined_source_code_is_not_expanded(self):
        events = [event for event in self.events if event["source_event_code"] == "samendment"]
        self.assertEqual(len(events), 37)
        self.assertTrue(all("does not define" in event["summary"] for event in events))

    def test_unknown_event_code_fails_instead_of_silently_dropping(self):
        source = b"cowcode,country,year,systid,evntid,evnttype\n2,United States of America,1789,2,1041,unknown\n"
        with self.assertRaisesRegex(ValueError, "unknown event type"):
            IMPORTER.parse_rows(source)

    def test_ambiguous_or_missing_crosswalk_fails(self):
        broken = copy.deepcopy(self.crosswalk)
        broken["entities"][0]["segments"].append(copy.deepcopy(broken["entities"][0]["segments"][0]))
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            IMPORTER.validate_crosswalk(broken)
        with self.assertRaisesRegex(ValueError, "missing from reviewed crosswalk"):
            IMPORTER.map_row(self.rows[0], {})

    def test_raw_source_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / IMPORTER.SOURCE_RELATIVE, root / IMPORTER.SOURCE_RELATIVE)
            source = root / IMPORTER.SOURCE_RELATIVE / "ccpcce_v6.csv"
            source.write_bytes(source.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "Pinned CCP source file changed"):
                IMPORTER.load_pinned(root)


if __name__ == "__main__":
    unittest.main()
