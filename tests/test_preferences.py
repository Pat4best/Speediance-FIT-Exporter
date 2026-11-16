"""Persisted export folder and exercise mapping regression tests."""
from tempfile import TemporaryDirectory
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from exercise_mapping import fit_exercise
from garmin_catalog import GARMIN_OPTIONS
from preferences import (
    export_folder, save_export_folder, saved_mappings,
    observed_names, remember_names, set_override,
)
from fitwriter import write_fit
from test_fit_profile import decode


class PreferenceTests(unittest.TestCase):
    def test_export_directory_is_remembered(self):
        with TemporaryDirectory() as td:
            root = Path(td) / "prefs"
            output = Path(td) / "my FIT exports"
            output.mkdir()
            self.assertEqual(export_folder(root), "")
            save_export_folder(output, root)
            self.assertEqual(export_folder(root), str(output.resolve()))
            with self.assertRaises(ValueError):
                save_export_folder(Path(td) / "does-not-exist", root)

    def test_mappings_can_be_added_and_deleted(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            remember_names(["Hohe Knie", "Skater"], root)
            self.assertEqual(observed_names(root), ["Hohe Knie", "Skater"])
            self.assertEqual(fit_exercise("Hohe Knie", saved_mappings(root)), (65534, None))
            set_override("Hohe Knie", 2, 12, root)
            self.assertEqual(fit_exercise("HOHE KNIE", saved_mappings(root)), (2, 12))
            set_override("Hohe Knie", None, None, root)
            self.assertEqual(fit_exercise("Hohe Knie", saved_mappings(root)), (65534, None))
            with self.assertRaises(ValueError):
                set_override("Skater", 99_999, 12, root)

    def test_saved_mapping_reaches_fit(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            set_override("Speediance Custom", 8, 23, root)
            fitfile = Path(td) / "test.fit"
            write_fit({
                "day": "2026-11-13", "duration_min": 3,
                "exercises": [{"name": "Speediance Custom",
                               "sets": [{"reps": 6, "weight": 25, "seconds": 20}]}]
            }, fitfile, overrides=saved_mappings(root))
            sets = [f for num, f in decode(fitfile.read_bytes()) if num == 225]
            self.assertEqual(sets[0][7][1], 8)
            self.assertEqual(sets[0][8][1], 23)

    def test_catalog_ids_are_valid_ranges(self):
        self.assertGreaterEqual(len(GARMIN_OPTIONS), 20)
        for category, subtype in GARMIN_OPTIONS.values():
            self.assertTrue(0 <= category <= 65534)
            self.assertTrue(0 <= subtype <= 65534)


if __name__ == "__main__":
    unittest.main()
