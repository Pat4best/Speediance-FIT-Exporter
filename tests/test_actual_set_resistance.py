"""Actually executed Speediance resistance, not highest planned setting."""
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from weight_handling import set_weight, measured_set_weight
from speediance_api import Client
from fitwriter import write_fit
from test_fit_profile import decode


class RecordedResistanceTests(unittest.TestCase):
    def test_recorded_load_20_replaces_initial_plan_26(self):
        weight, total, shape = measured_set_weight({
            "weights": [26, 20, 20, 20, 20, 20],
        })
        self.assertEqual(weight, 20.0)
        self.assertFalse(total)
        self.assertTrue(shape["contains_changes"])
        self.assertEqual(shape["source"], "generic_telemetry")

    def test_seated_row_two_handles_reduces_13_each_to_10_each(self):
        weight, total, shape = measured_set_weight({
            "weights": [26] * 6,  # derived force: not the reliable load
            "leftWeights": [13, 10, 10, 10, 10],
            "rightWeights": [13, 10, 10, 10, 10],
        })
        self.assertEqual(weight, 20.0)
        self.assertTrue(total)
        self.assertEqual(shape["source"], "both_sides")

    def test_last_sample_wins_when_two_loads_recorded_once(self):
        # Setup at 26 kg followed by a single measured rep at 20 kg.
        self.assertEqual(set_weight({"weights": [26, 20]}), (20.0, False))

    def test_midset_increase_is_not_discarded(self):
        self.assertEqual(set_weight({
            "leftWeights": [10, 10, 13, 13, 13],
            "rightWeights": [10, 10, 13, 13, 13],
        }), (26.0, True))

    def test_zero_after_end_does_not_replace_20_kg(self):
        self.assertEqual(set_weight({
            "leftWeights": [10, 10, 0, 0, 0, 0],
            "rightWeights": [10, 10, 0, 0, 0, 0],
        }), (20.0, True))

    def test_true_set_load_flows_from_detail_to_fit_without_plan_weight(self):
        client = Client(logging.getLogger("test-actual-load"))
        def mock_request(path, **_kwargs):
            if "getHeartRateGraph" in path:
                return None
            return [{
                "actionLibraryName": "Sitzendes Rudern mit zwei Griffen",
                "finishedReps": [
                    {
                        "finishedCount": 10, "targetCount": 10, "time": 24,
                        "trainingInfoDetail": {
                            "weights": [26] * 10,
                            "leftWeights": [13, 10, 10, 10, 10, 10],
                            "rightWeights": [13, 10, 10, 10, 10, 10],
                            "uuid": "test-only-no-secret",
                        },
                    },
                    {
                        "finishedCount": 10, "targetCount": 10, "time": 25,
                        "trainingInfoDetail": {
                            "leftWeights": [10] * 10,
                            "rightWeights": [10] * 10,
                        },
                    },
                ],
            }]
        client.request = mock_request
        detail = client.detail({
            "training_id": 100, "day": "2026-11-16",
            "type": 5, "duration_min": 2,
        })
        sets = detail["exercises"][0]["sets"]
        self.assertEqual([s["weight"] for s in sets], [20.0, 20.0])
        self.assertTrue(all(s["weight_already_total"] for s in sets))
        with TemporaryDirectory() as td:
            output = write_fit(detail, Path(td) / "actual.fit")
            records = [fields for num, fields in decode(output.read_bytes())
                       if num == 225]
            self.assertEqual([r[4][1] / 16 for r in records], [20.0, 20.0])


if __name__ == "__main__":
    unittest.main()
