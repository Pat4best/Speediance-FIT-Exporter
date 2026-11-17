"""Regression: Speediance omits completed custom training from monthNew calendar.

The read-only userTrainingDataRecord endpoint includes custom sessions with
history type 5. Verify that their training ID/metadata survive to FIT export.
"""
from datetime import date
import logging
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from speediance_api import Client, APIError
from fitwriter import write_fit

def record(tid, title, started="2026-11-16 18:00:00", kind=5, seconds=3420):
    return {
        "trainingId": tid, "type": kind, "title": title,
        "startTime": started, "trainingTime": seconds,
        "calorie": 454, "totalCapacity": 8200,
    }

def calendar_day(tid):
    return {
        "date": "2026-11-13",
        "trainingPlanList": [
            {"trainingId": tid, "title": "Speediance Intro", "isFinish": 1,
             "type": 2, "durationMinute": 6, "calorie": 34},
        ],
    }

class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.client = Client(logging.getLogger("history-test"))

    def test_custom_session_in_history_is_merged_and_exportable(self):
        requested = []
        def api(path, **kwargs):
            requested.append((path, kwargs))
            if "userTrainingDataRecord" in path:
                return [
                    record(920, "GMC - Mon 16 Nov"),
                    record(100, "Speediance Intro", started="2026-11-13 09:00:00"),
                    {"trainingId": None, "belongUserHealth": 1, "title": "Walk",
                     "startTime": "2026-11-16 19:00:00"},
                    record(921, "Outside window", started="2026-11-18 13:00:00"),
                ]
            if "/trainingInfo/" in path:
                return [
                    {"actionLibraryName": "Barbell Deadlift", "finishedReps": [
                        {"finishedCount": 5, "time": 25,
                         "trainingInfoDetail": {"weights": [35.0]}}
                    ]},
                ]
            return [calendar_day(100)]
        self.client.request = api
        rows = self.client.list_workouts(date(2026, 11, 1), date(2026, 11, 17))
        self.assertEqual([x["training_id"] for x in rows], [920, 100])
        self.assertEqual(self.client.history_added, 1)
        self.assertEqual(self.client.history_stats["duplicates"], 1)
        self.assertEqual(self.client.history_stats["health"], 1)
        self.assertEqual(self.client.history_stats["outside"], 1)
        self.assertEqual(rows[0]["duration_min"], 57.0)
        self.assertEqual(rows[0]["type"], 5)
        self.assertEqual(rows[0]["finished_at"], "2026-11-16T18:57:00")
        self.assertTrue(any("userTrainingDataRecord" in path for path, _ in requested))
        details = self.client.detail(rows[0])
        self.assertEqual(details["exercises"][0]["sets"][0]["weight"], 35)
        with TemporaryDirectory() as td:
            file = write_fit(details, Path(td) / "custom.fit")
            self.assertTrue(file.is_file())
            self.assertGreater(file.stat().st_size, 150)

    def test_history_service_failure_preserves_calendar_workouts(self):
        def api(path, **kwargs):
            if "userTrainingDataRecord" in path:
                raise APIError("not available")
            return [calendar_day(100)]
        self.client.request = api
        rows = self.client.list_workouts(date(2026, 11, 1), date(2026, 11, 17))
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.client.history_added, 0)

    def test_history_only_session_in_range(self):
        def api(path, **kwargs):
            return [record(920, "GMC - Mon 16 Nov")] if "userTrainingDataRecord" in path else []
        self.client.request = api
        rows = self.client.list_workouts(date(2026, 11, 16), date(2026, 11, 17))
        self.assertEqual([x["training_id"] for x in rows], [920])

if __name__ == "__main__":
    unittest.main()
