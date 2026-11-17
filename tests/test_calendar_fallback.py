"""Calendar regression: a completed 16 Nov session must not disappear.

Speediance's monthNew calendar is version-dependent. The app used to show
November 16 using Versioncode 40304; recent versions read with 41000.
These offline fixtures test merging and de-duplication, not the live account.
"""
from datetime import date
import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from speediance_api import Client, APIError, READ_VERSIONS


def day(date_string, *plans):
    return {"date": date_string, "trainingPlanList": list(plans)}


def workout(id_, title, status=1):
    return {"trainingId": id_, "title": title, "isFinish": status,
            "finishTime": "2026-11-16 17:00:00",
            "durationMinute": 57, "calorie": 454, "type": 1}


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.client = Client(logging.getLogger("calendar-tests"))
        self.client.token = "fake"
        self.client.user_id = "fake-user"
        self.client.unit = "kg"

    def test_old_api_restores_monday_workout_without_duplicates(self):
        seen_versions = []
        def fake(path, **kwargs):
            if "userTrainingDataRecord" in path:
                return []
            version = kwargs["read_version"]
            seen_versions.append(version)
            if version == "41000":
                return [day("2026-11-13", workout(100, "Gym intro")),
                        day("2026-11-16", workout(102, "Planned", status=0))]
            if version == "40304":
                return [day("2026-11-13", workout(100, "Gym intro")),
                        day("2026-11-16", workout(101, "GMC - Mon 16 Nov"))]
            raise AssertionError("Unexpected version")
        self.client.request = fake
        result = self.client.list_workouts(date(2026, 11, 1), date(2026, 11, 17))
        self.assertEqual(seen_versions, list(READ_VERSIONS) * 2)
        self.assertEqual([w["training_id"] for w in result], [101, 100])
        self.assertEqual(self.client.calendar_fallback_added, 1)
        self.assertEqual(result[0]["day"], "2026-11-16")

    def test_other_device_filter_restores_missing_monday_training(self):
        def fake(path, **kwargs):
            if "userTrainingDataRecord" in path:
                return []
            # Gym Monster calendar does not show the Nov 16 workout.
            if "selectedDeviceType=1" in path:
                return [day("2026-11-13", workout(100, "Intro"))]
            return [day("2026-11-16", workout(101, "GMC - Mon 16 Nov"))]
        self.client.request = fake
        result = self.client.list_workouts(date(2026, 11, 1), date(2026, 11, 17))
        self.assertEqual([w["training_id"] for w in result], [101, 100])
        self.assertEqual(self.client.calendar_other_device_added, 1)
        self.assertEqual(len(self.client.calendar_query_stats), 4)
        self.assertEqual({stat["device"] for stat in self.client.calendar_query_stats}, {1, 2})

    def test_previous_api_failure_does_not_hide_current_activities(self):
        def fake(path, **kwargs):
            if "userTrainingDataRecord" in path:
                return []
            if kwargs["read_version"] == "40304":
                raise APIError("Unsupported")
            return [day("2026-11-16", workout(101, "Workout"))]
        self.client.request = fake
        result = self.client.list_workouts(date(2026, 11, 16), date(2026, 11, 17))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.client.calendar_fallback_added, 0)

    def test_first_version_failure_does_not_hide_old_calendar(self):
        def fake(path, **kwargs):
            if "userTrainingDataRecord" in path:
                return []
            return [] if kwargs["read_version"] == "41000" else [
                day("2026-11-16T00:00:00", workout("101", "Workout", status="1"))
            ]
        self.client.request = fake
        result = self.client.list_workouts(date(2026, 11, 16), date(2026, 11, 17))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.client.calendar_fallback_added, 1)

    def test_both_calendar_views_unavailable_is_not_silent(self):
        self.client.request = lambda path, **kwargs: None
        with self.assertRaisesRegex(APIError, "Kalender"):
            self.client.list_workouts(date(2026, 11, 1), date(2026, 11, 17))

    def test_read_version_only_get_and_no_relogin(self):
        with self.assertRaises(ValueError):
            self.client.request("/api/app/v2/login/byPass", payload={}, read_version="40304")
        with self.assertRaises(ValueError):
            self.client.request("/api/app/v5/trainingCalendar/monthNew",
                                login_as="phone", read_version="40304")
        with self.assertRaises(ValueError):
            self.client.request("/api/app/v5/trainingCalendar/monthNew",
                                read_version="99999")

    def test_legacy_header_is_used_only_for_read(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, limit):
                return json.dumps({"code": 0, "data": []}).encode("utf-8")
        requests = []
        def fake_urlopen(req, timeout):
            requests.append(req)
            return Response()
        with patch("urllib.request.urlopen", fake_urlopen):
            self.client.request("/api/app/v5/trainingCalendar/monthNew",
                                read_version="40304")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].get_header("Versioncode"), "40304")
        self.assertEqual(requests[0].get_header("App_type"), "SOFTWARE")
        self.assertEqual(requests[0].get_header("Token"), "fake")


if __name__ == "__main__":
    unittest.main()
