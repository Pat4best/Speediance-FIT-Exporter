"""GM Manager confirmed workout JSON -> genuine Garmin FIT overlay regression tests.

Sample data is synthetic. The real GM Manager export is NOT a recorded-set
API response; its use as completed sets requires explicit user confirmation.
"""
import json
import logging
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gm_manager_import import (
    parse_gm_manager_json, load_gm_manager_file, GMManagerImportError,
    resolve_exercise_names,
)
from garmin_fit_overlay import overlay_garmin_fit, parse_fit_wire
from garmin_merge import DEFAULT_PRIORITIES
from test_garmin_fit_overlay import (
    original_garmin_fit, speediance_executed, values, all_message_data
)
from test_fit_profile import crc


def synthetic_manager_doc():
    return {
        "app": "gmvoice-speediance", "kind": "custom-workouts",
        "version": 1, "unit": 0,
        "workouts": [{
            "name": "GMC · Mon 16 Nov",
            "exercises": [
                {"groupId": 1001, "kind": "cardio",
                 "sets": [{"reps": 300, "rest": 60}, {"reps": 300, "rest": 60}]},
                {"groupId": 1002, "kind": "strength",
                 "sets": [{"reps": r, "rest": 90, "weight": w,
                           "mode": 1, "unit": "reps"}
                          for r, w in [(10, 13), (5, 24), (10, 37), (10, 37), (10, 37), (10, 37)]]},
                {"groupId": 1003, "kind": "strength",
                 "sets": [{"reps": r, "rest": 90, "weight": w,
                           "mode": 1, "unit": "reps"}
                          for r, w in [(5, 17), (10, 26), (10, 26), (10, 26), (10, 26)]]},
                {"groupId": 1004, "kind": "strength",
                 "sets": [{"reps": 10, "rest": 90, "weight": w,
                           "mode": 1, "unit": "reps"} for w in (18, 12, 12)]},
                {"groupId": 1005, "kind": "strength",
                 "sets": [{"reps": 10, "rest": 90, "weight": 20,
                           "mode": 1, "unit": "reps"} for _ in range(3)]},
                {"groupId": 1006, "kind": "strength",
                 "sets": [{"reps": 12, "rest": 60, "weight": 5.5,
                           "mode": 1, "unit": "reps"} for _ in range(2)]},
                *[
                    {"groupId": 2000 + index, "kind": "mat",
                     "sets": [{"reps": 30, "rest": 10}]}
                    for index in range(3)
                ],
            ],
        }],
    }


class GMManagerImportTests(unittest.TestCase):
    selected = {"title": "GMC · Mon 16 Nov", "day": "2026-11-16"}

    def test_synthetic_confirmed_export_counts_preserve_exact_loads(self):
        decoded = parse_gm_manager_json(json.dumps(synthetic_manager_doc()),
                                        self.selected)
        self.assertEqual(decoded["exercise_count"], 9)
        self.assertEqual(decoded["set_count"], 24)
        self.assertEqual(decoded["strength_set_count"], 19)
        self.assertEqual(decoded["timed_set_count"], 5)
        self.assertEqual(decoded["unit"], "kg")
        self.assertEqual(decoded["exercises"][0]["sets"][0]["seconds"], 300)
        self.assertEqual(decoded["exercises"][0]["sets"][0]["reps"], 0)
        self.assertEqual(decoded["exercises"][1]["sets"][2]["weight"], 37)
        self.assertTrue(decoded["exercises"][1]["sets"][2]["weight_already_total"])
        self.assertEqual(decoded["exercises"][5]["sets"][0]["weight"], 5.5)
        self.assertEqual(
            sum(set_item["reps"] for ex in decoded["exercises"]
                for set_item in ex["sets"]), 184
        )

    def test_reject_other_workout_or_wrong_schema_and_values(self):
        doc = synthetic_manager_doc()
        with self.assertRaisesRegex(GMManagerImportError, "passt nicht"):
            parse_gm_manager_json(json.dumps(doc), {"title": "Different"})
        doc["kind"] = "exercise-library"
        with self.assertRaisesRegex(GMManagerImportError, "unterstützte"):
            parse_gm_manager_json(json.dumps(doc), self.selected)
        doc["kind"] = "custom-workouts"
        doc["workouts"][0]["exercises"][1]["sets"][0]["weight"] = -1
        with self.assertRaises(GMManagerImportError):
            parse_gm_manager_json(json.dumps(doc), self.selected)
        doc["workouts"][0]["exercises"][1]["sets"][0]["weight"] = 13
        doc["workouts"].append(doc["workouts"][0])
        with self.assertRaises(GMManagerImportError):
            parse_gm_manager_json(json.dumps(doc), self.selected)
        with self.assertRaises(GMManagerImportError):
            parse_gm_manager_json('{"app":"no"', self.selected)

    def test_name_lookup_fallback_and_no_raw_ids_in_logged_output(self):
        parsed = parse_gm_manager_json(json.dumps(synthetic_manager_doc()),
                                       self.selected)
        class Fake:
            def request(self, path, **kwargs):
                if "/1002?" in path:
                    return {"actionLibraryName": "Barbell Deadlift"}
                return None
        resolved = resolve_exercise_names(Fake(), parsed)
        self.assertEqual(resolved[1]["name"], "Barbell Deadlift")
        self.assertIn("1003", resolved[2]["name"])

    def test_import_file_and_overlay_retains_garmin_telemetry(self):
        sample = synthetic_manager_doc()
        original = original_garmin_fit()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "session.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            imported = load_gm_manager_file(path, self.selected)
            speed = speediance_executed()
            speed.update({
                "exercises": imported["exercises"],
                "unit": imported["unit"],
                "_set_source": "gm_manager_confirmed",
                "duration_min": 60,
                "finished_at": None,
            })
            # The original toy Garmin fixture lasts 360 seconds. Select the
            # actual 60-minute workout duration, sufficient for timed sets.
            options = dict(DEFAULT_PRIORITIES, duration="speediance")
            output, metadata = overlay_garmin_fit(
                original, speed, Path(folder) / "merged.fit", options
            )
            emitted = output.read_bytes()
        self.assertEqual(metadata["new_speediance_sets"], 24)
        self.assertEqual(metadata["speediance_repetitions"], 184)
        self.assertEqual(metadata["speediance_source"], "gm_manager_confirmed")
        self.assertEqual(len(values(emitted, 225)), 24)
        self.assertEqual(values(emitted, 225)[0][3][1], 0)
        self.assertEqual(values(emitted, 225)[2][3][1], 10)
        self.assertAlmostEqual(values(emitted, 225)[2][4][1] / 16, 13)
        self.assertAlmostEqual(values(emitted, 225)[2 + 6][4][1] / 16, 17)
        self.assertAlmostEqual(values(emitted, 225)[2 + 6 + 5 + 3 + 3][4][1] / 16, 5.5)
        self.assertEqual(all_message_data(original, 23),
                         all_message_data(emitted, 23))
        self.assertEqual(all_message_data(original, 233),
                         all_message_data(emitted, 233))
        self.assertEqual(all_message_data(original, 534),
                         all_message_data(emitted, 534))
        self.assertEqual(all_message_data(original, 20)[:-1],
                         all_message_data(emitted, 20)[:len(values(original, 20))-1])
        self.assertEqual(len(parse_fit_wire(emitted)), len(parse_fit_wire(emitted)))


if __name__ == "__main__":
    unittest.main()
