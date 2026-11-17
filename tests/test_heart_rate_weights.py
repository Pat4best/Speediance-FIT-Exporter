"""Real HR samples and bilateral Speediance weight conversion regressions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from heart_rate import graph_points
from weight_handling import weight_multiplier_for, suggested_weight_multiplier, set_weight
from preferences import saved_weight_multipliers, set_weight_multiplier
from speediance_api import Client
from fitwriter import write_fit
from test_fit_profile import decode


class WeightTests(unittest.TestCase):
    def test_dual_handle_5_5_each_becomes_11_kg(self):
        self.assertEqual(suggested_weight_multiplier("Bent-Over Dual-Handle Reverse Fly"), 2)
        self.assertEqual(weight_multiplier_for("Barbell Bench Press"), 1)
        with TemporaryDirectory() as td:
            path = Path(td) / "reverse_fly.fit"
            write_fit({
                "day": "2026-11-16", "duration_min": 3,
                "exercises": [{
                    "name": "Bent-Over Dual-Handle Reverse Fly",
                    "sets": [{"reps": 10, "weight": 5.5, "seconds": 30}],
                }],
            }, path)
            sets = [fields for n, fields in decode(path.read_bytes()) if n == 225]
            self.assertEqual(sets[0][4][1] / 16, 11)

    def test_side_telemetry_summed_once_even_when_dual_handle_multiplier(self):
        resistance, total = set_weight({
            "weights": [15, 15],  # force telemetry, not the resistance
            "leftWeights": [5.5, 5.5], "rightWeights": [5.5, 5.5],
        })
        self.assertEqual((resistance, total), (11, True))
        with TemporaryDirectory() as td:
            path = Path(td) / "sides.fit"
            write_fit({
                "day": "2026-11-16", "duration_min": 3,
                "exercises": [{
                    "name": "Bent-Over Dual-Handle Reverse Fly",
                    "sets": [{
                        "reps": 10, "weight": resistance,
                        "weight_already_total": total, "seconds": 30,
                    }],
                }],
            }, path, weight_overrides={
                "bent over dual handle reverse fly": 2,
            })
            sets = [fields for n, fields in decode(path.read_bytes()) if n == 225]
            self.assertEqual(sets[0][4][1] / 16, 11)

    def test_single_side_stays_single(self):
        weight, already = set_weight({
            "leftWeights": [5.5], "rightWeights": [5.5]
        }, {"leftRight": 1})
        self.assertEqual(weight, 5.5)
        self.assertTrue(already)

    def test_per_exercise_override_and_persistence(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            name = "Bent-Over Dual-Handle Reverse Fly"
            self.assertEqual(weight_multiplier_for(name), 2)
            set_weight_multiplier(name, 1, root)
            self.assertEqual(weight_multiplier_for(name, saved_weight_multipliers(root)), 1)
            set_weight_multiplier("Normal Cable Fly", 2, root)
            self.assertEqual(weight_multiplier_for("Normal Cable Fly", saved_weight_multipliers(root)), 2)
            with self.assertRaises(ValueError):
                set_weight_multiplier(name, 3, root)

    def test_weight_lb_and_non_dual_exercises_unchanged(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "lb.fit"
            write_fit({
                "day": "2026-11-16", "duration_min": 3, "unit": "lb",
                "exercises": [{"name": "Two-Handle Row", "sets": [
                    {"weight": 5.5, "reps": 10, "seconds": 25}]}],
            }, path)
            sets = [fields for n, fields in decode(path.read_bytes()) if n == 225]
            self.assertAlmostEqual(sets[0][4][1] / 16, 11 * 0.45359237, delta=0.07)


class HeartRateTests(unittest.TestCase):
    def test_graph_preserves_missing_second_and_no_fabricated_bpm(self):
        self.assertEqual(graph_points([
            {"time": 0, "heartRate": 120},
            {"time": 1, "heartRate": 0},
            {"time": 2, "heartRate": 150},
            {"time": 3, "heartRate": "not-a-number"},
        ]), [(0, 120), (2, 150)])
        self.assertEqual(graph_points([]), [])
        self.assertEqual(graph_points(None), [])

    def test_fit_contains_actual_record_heart_rate_and_session_summary(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "hr.fit"
            write_fit({
                "day": "2026-11-16", "duration_min": 3,
                "heart_rate_points": [(0, 120), (2, 150), (10, 140)],
                "exercises": [{"name": "Barbell Bench Press",
                               "sets": [{"seconds": 30, "reps": 8, "weight": 25}]}],
            }, path)
            messages = decode(path.read_bytes())
            readings = [(fields[253][1], fields[3][1])
                        for n, fields in messages if n == 20 and 3 in fields]
            self.assertEqual([bpm for _, bpm in readings], [120, 150, 140])
            self.assertEqual([timestamp - readings[0][0] for timestamp, _ in readings],
                             [0, 2, 10])
            session = next(fields for n, fields in messages if n == 18)
            self.assertEqual(session[16][1], 137)
            self.assertEqual(session[17][1], 150)

    def test_no_heart_rate_does_not_generate_fake_metrics(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "nohr.fit"
            write_fit({"day": "2026-11-16", "duration_min": 3,
                       "exercises": []}, path)
            messages = decode(path.read_bytes())
            session = next(fields for n, fields in messages if n == 18)
            self.assertNotIn(16, session)
            self.assertNotIn(17, session)
            self.assertFalse(any(n == 20 and 3 in fields for n, fields in messages))

    def test_detail_fetches_recorded_graph_with_uuid(self):
        client = Client(logging.getLogger("test-heart-rate"))
        paths = []
        def get(path, **kwargs):
            paths.append(path.split("?")[0])
            if "getHeartRateGraph" in path:
                return [{"time": 0, "heartRate": 120},
                        {"time": 1, "heartRate": 0},
                        {"time": 2, "heartRate": 150}]
            return [{"actionLibraryName": "Bent-Over Dual-Handle Reverse Fly",
                     "finishedReps": [{
                        "finishedCount": 10, "time": 20, "trainingInfoDetail": {
                            "uuid": "synthetic-session-uuid",
                            "leftWeights": [5.5], "rightWeights": [5.5],
                            "weights": [15],
                        }
                    }]}]
        client.request = get
        detail = client.detail({"training_id": 7, "type": 5, "day": "2026-11-16"})
        self.assertEqual(detail["heart_rate_points"], [(0, 120), (2, 150)])
        self.assertEqual(detail["exercises"][0]["sets"][0]["weight"], 11)
        self.assertTrue(detail["exercises"][0]["sets"][0]["weight_already_total"])
        self.assertIn("/api/app/watchMsg/getHeartRateGraph", paths)


if __name__ == "__main__":
    unittest.main()
