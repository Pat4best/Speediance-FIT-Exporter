"""Regression tests for anonymized diagnosis of live Speediance HR series.

The user actually observed heartRates containing 942 elements and zero
decoded samples in v0.1.14. These tests cover several plausible entry shapes
without assuming the user's private measurements or actual unknown schema.
"""
import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from heart_rate import graph_details, graph_shape
from speediance_api import Client


class HeartRateUnknownShapeTests(unittest.TestCase):
    def test_heart_rate_value_compound_key(self):
        graph = {
            "heartRates": [
                {"heartRateValue": 100, "time": 0},
                {"heartRateValue": 121, "time": 4},
                {"heartRateValue": 0, "time": 5},
                {"maxHeartRate": 199, "avgHeartRate": 115, "time": 10},
            ],
            "avgHeartRate": 110,
            "maxHeartRate": 146,
        }
        result = graph_details(graph, 60)
        self.assertEqual(result["points"], [(0, 100), (4, 121)])
        self.assertEqual(result["summary"]["avg"], 110)
        self.assertEqual(result["summary"]["max"], 146)
        self.assertFalse(result["timing_estimated"])

    def test_private_field_names_and_values_not_logged(self):
        graph = {"heartRates": [
            {"private-bearer-token": "SECRET-TOKEN",
             "sensitive-device-id": "ABCDEF",
             "maxHeartRate": 160},
        ] * 942, "avgHeartRate": 110, "maxHeartRate": 146}
        self.assertEqual(graph_details(graph, 600)["points"], [])
        diagnostic = graph_shape(graph)
        self.assertEqual(diagnostic["items"], 942)
        self.assertEqual(diagnostic["format"], "heartRates")
        self.assertIn("maxheartrate", diagnostic["known_fields"])
        serial = str(diagnostic)
        for secret in ("SECRET-TOKEN", "ABCDEF", "private-bearer-token",
                       "sensitive-device-id", "160", "146"):
            self.assertNotIn(secret, serial)

    def test_no_valid_samples_still_keeps_real_max_from_sets(self):
        client = Client(logging.getLogger("heart-shape"))
        def fake_request(path, **_kwargs):
            if "getHeartRateGraph" in path:
                return {"heartRates": [{"maxHeartRate": 146} for _ in range(942)],
                        "avgHeartRate": 110, "maxHeartRate": 146}
            return [
                {"actionLibraryName": "Barbell Bench Press",
                 "finishedReps": [{
                     "maxHeartRate": 146, "finishedCount": 8, "time": 30,
                     "trainingInfoDetail": {"uuid": "internal-test-uuid",
                                            "weights": [25.0]},
                 }]},
            ]
        client.request = fake_request
        session = client.detail({"training_id": 102, "type": 5,
                                 "day": "2026-11-16", "duration_min": 10})
        self.assertEqual(session["heart_rate_points"], [])
        self.assertEqual(session["heart_rate_summary"]["max"], 146)
        self.assertEqual(session["heart_rate_summary"]["avg"], 110)


if __name__ == "__main__":
    unittest.main()
