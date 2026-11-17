"""Completed Speediance strength-detail cache regressions (no live account)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import logging
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from completed_workout_cache import load_detail_cache, save_detail_cache
from speediance_api import Client, APIError


WORKOUT = {
    "training_id": 81077, "day": "2026-11-16", "type": 5,
    "title": "Test activity", "unit": "kg",
    "duration_min": 56 + 34 / 60,
    "started_at": "2026-11-16T15:14:00+01:00",
}
DETAIL = dict(WORKOUT, exercises=[{
    "name": "Sitzendes Rudern mit zwei Griffen",
    "completion_method": 1,
    "sets": [{"reps": 10, "seconds": 25, "weight": 20,
              "weight_already_total": True}],
}], heart_rate_points=[(0, 110), (3, 120)],
    heart_rate_summary={"avg": 110, "max": 146},
    heart_rate_timing_estimated=False, hr_sensor={
        "device_id": "private identifier must not be cached",
    })


class DetailCacheTests(unittest.TestCase):
    def test_persist_actual_weight_and_hr_without_private_identifiers(self):
        with TemporaryDirectory() as root:
            self.assertTrue(save_detail_cache(
                root, "euapi.speediance.com", "accountA", WORKOUT, DETAIL
            ))
            loaded = load_detail_cache(
                root, "euapi.speediance.com", "accountA", WORKOUT
            )
            self.assertEqual(loaded["exercises"][0]["sets"][0]["weight"], 20)
            self.assertEqual(loaded["heart_rate_points"], [[0, 110], [3, 120]])
            self.assertEqual(loaded["heart_rate_summary"]["max"], 146)
            body = "".join(p.read_text(encoding="utf8")
                           for p in Path(root).glob("*.json"))
            self.assertNotIn("accountA", body)
            self.assertNotIn("private identifier", body)
            self.assertNotIn("hr_sensor", body)
            self.assertNotIn("api_key", body)
            self.assertNotIn("password", body)
            self.assertNotIn("test-session-uuid", body)

    def test_cache_isolated_by_account_region_and_workout_id(self):
        with TemporaryDirectory() as root:
            self.assertTrue(save_detail_cache(
                root, "euapi.speediance.com", "accountA", WORKOUT, DETAIL
            ))
            self.assertIsNone(load_detail_cache(
                root, "euapi.speediance.com", "accountB", WORKOUT))
            self.assertIsNone(load_detail_cache(
                root, "api2.speediance.com", "accountA", WORKOUT))
            self.assertIsNone(load_detail_cache(
                root, "euapi.speediance.com", "accountA",
                dict(WORKOUT, training_id=81078)))
            self.assertIsNone(load_detail_cache(
                root, "euapi.speediance.com", "accountA",
                dict(WORKOUT, day="2026-11-15")))
            self.assertEqual(list(Path(root).glob("*.json")).__len__(), 1)

    def test_no_empty_template_or_bad_data_can_be_cached(self):
        with TemporaryDirectory() as root:
            self.assertFalse(save_detail_cache(
                root, "euapi.speediance.com", "accountA",
                WORKOUT, dict(DETAIL, exercises=[])))
            self.assertFalse(save_detail_cache(
                root, "euapi.speediance.com", "accountA",
                WORKOUT, dict(DETAIL, heart_rate_points=[(1, -10)])))
            self.assertFalse(list(Path(root).glob("*.json")))

    def test_corrupt_cache_ignored_without_crash(self):
        with TemporaryDirectory() as root:
            self.assertTrue(save_detail_cache(
                root, "euapi.speediance.com", "accountA", WORKOUT, DETAIL
            ))
            file = next(Path(root).glob("*.json"))
            file.write_text("garbage", encoding="utf8")
            self.assertIsNone(load_detail_cache(
                root, "euapi.speediance.com", "accountA", WORKOUT))

    def test_second_speediance_export_uses_cached_actual_details_offline(self):
        with TemporaryDirectory() as root:
            client = Client(logging.getLogger("test-cached-workout"), cache_dir=root)
            client.user_id = "accountA"
            client.token = "test-token-not-persisted"
            visits = []
            def request(route, **kwargs):
                visits.append(route)
                if "cttTrainingInfoDetail" in route:
                    return [{
                        "actionLibraryName": "Sitzendes Rudern mit zwei Griffen",
                        "completionMethod": 1,
                        "finishedReps": [{
                            "finishedCount": 10, "time": 25,
                            "trainingInfoDetail": {
                                "leftWeights": [13, 10, 10, 10],
                                "rightWeights": [13, 10, 10, 10],
                            },
                        }],
                    }]
                return None
            client.request = request
            initial = client.detail(WORKOUT)
            self.assertEqual(initial["exercises"][0]["sets"][0]["weight"], 20)
            self.assertGreater(len(visits), 0)
            second_client = Client(
                logging.getLogger("test-cached-workout"),
                cache_dir=root,
            )
            second_client.user_id = "accountA"
            def never_request(*args, **kwargs):
                raise AssertionError("Cached details must not call API")
            second_client.request = never_request
            loaded = second_client.detail(WORKOUT)
            self.assertEqual(loaded["exercises"][0]["sets"][0]["weight"], 20)
            self.assertEqual(loaded["exercises"][0]["sets"][0]["reps"], 10)

    def test_no_account_context_does_not_cache_or_reuse(self):
        with TemporaryDirectory() as root:
            self.assertFalse(save_detail_cache(
                root, "euapi.speediance.com", None, WORKOUT, DETAIL))
            self.assertIsNone(load_detail_cache(
                root, "euapi.speediance.com", None, WORKOUT))


if __name__ == "__main__":
    unittest.main()
