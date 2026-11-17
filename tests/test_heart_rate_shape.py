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

    def test_diagnostics_identify_zero_and_invalid_types_without_exposing_values(self):
        graph = {"heartRates": [
            {"heartRate": 0, "time": 0, "secret": "TOKEN-ABC"},
            {"heartRate": "0", "time": "1"},
            {"heartRate": "121", "time": "unrecognized"},
            {"heartRate": {"value": 130}, "time": None},
            {"heartRate": 1000, "time": 9999999},
            {"heartRate": -1, "time": -5},
            {"time": 3},
        ]}
        shape = graph_shape(graph)
        self.assertEqual(shape["heartRate_types"], {
            "int": 3, "str": 2, "dict": 1,
        })
        self.assertEqual(shape["heartRate_status"], {
            "valid": 1, "zero": 2, "below_range": 1,
            "above_range": 1, "nonnumeric": 1, "absent": 1,
        })
        self.assertEqual(shape["time_status"], {
            "valid_seconds": 3, "negative": 1, "over_24h": 1,
            "nonnumeric": 2, "absent": 0,
        })
        self.assertNotIn("TOKEN-ABC", str(shape))
        self.assertNotIn("121", str(shape))
        self.assertNotIn("1000", str(shape))

    def test_942_empty_or_non_numeric_samples_do_not_fabricate_pulse(self):
        graph = {
            "heartRates": [
                {"heartRate": None, "time": i, "source": "private-opaque"}
                for i in range(942)
            ],
            "avgHeartRate": 110, "maxHeartRate": 146,
        }
        self.assertEqual(graph_details(graph, 1000)["points"], [])
        shape = graph_shape(graph)
        self.assertEqual(shape["heartRate_types"], {"NoneType": 942})
        self.assertEqual(shape["heartRate_status"]["nonnumeric"], 942)
        self.assertEqual(shape["time_status"]["valid_seconds"], 942)

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
