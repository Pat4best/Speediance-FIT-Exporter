"""Tests for alternative Speediance detail endpoints and privacy-safe failures."""
import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from speediance_api import Client, APIError, completed_history_shape


class SpeedianceDetailTests(unittest.TestCase):
    WORKOUT = {"type": 1, "training_id": 789, "day": "2026-11-13",
               "title": "Example", "unit": "kg"}

    def test_fallback_when_first_route_has_no_details(self):
        client = Client(logging.getLogger("test"))
        calls = []
        def request(path, **kwargs):
            calls.append(path)
            if "courseTrainingInfoDetail" not in path:
                return []
            return [{"actionLibraryName": "Kreuzheben mit Langhantel",
                     "finishedReps": [
                         {"finishedCount": 5, "time": 28,
                          "trainingInfoDetail": {"weights": [13, 35]}}
                     ]}]
        client.request = request
        data = client.detail(self.WORKOUT)
        self.assertEqual(len(data["exercises"]), 1)
        self.assertEqual(data["exercises"][0]["name"], "Kreuzheben mit Langhantel")
        self.assertEqual(data["exercises"][0]["sets"][0]["weight"], 35)
        self.assertGreater(len(calls), 1)

    def test_fallback_when_endpoint_returns_empty_exercise_template(self):
        client = Client(logging.getLogger("test"))
        calls = []
        def request(path, **kwargs):
            calls.append(path)
            if "courseTrainingInfoDetail" in path:
                return [{"actionLibraryName": "Kreuzheben",
                         "finishedReps": [{"finishedCount": 5,
                                           "trainingInfoDetail": {"weights": [35]}}]}]
            return [{"actionLibraryName": "Empty Template", "finishedReps": []}]
        client.request = request
        detail = client.detail(self.WORKOUT)
        self.assertEqual(detail["exercises"][0]["name"], "Kreuzheben")
        self.assertEqual(len(detail["exercises"][0]["sets"]), 1)
        self.assertGreater(len(calls), 1)

    def test_history_identifier_shape_is_private_and_distinct_from_template(self):
        record = {
            "id": 14532, "trainingId": 923441,
            "type": 5, "templateId": 501,
            "startTime": "private start", "title": "private title",
            "appUserId": "private account",
        }
        result = completed_history_shape(record)
        self.assertEqual(result["history_type"], 5)
        self.assertEqual(result["id_relation"], "different")
        self.assertEqual(result["identifier_fields"],
                         ["id", "trainingId", "templateId", "type"])
        serialized = str(result)
        for private in ("14532", "923441", "private", "501"):
            self.assertNotIn(private, serialized)

    def test_history_session_type_wins_for_route_order(self):
        client = Client(logging.getLogger("test-history-session-type"))
        calls = []
        def request(path, **kwargs):
            calls.append(path)
            if "courseTrainingInfoDetail" in path:
                return [{
                    "actionLibraryName": "Test movement",
                    "finishedReps": [{
                        "finishedCount": 6, "time": 20,
                        "trainingInfoDetail": {"weights": [20, 20]},
                    }],
                }]
            return None
        client.request = request
        workout = dict(self.WORKOUT, type=5, history_type=2)
        detail = client.detail(workout)
        self.assertIn("courseTrainingInfoDetail", calls[0])
        self.assertEqual(detail["exercises"][0]["sets"][0]["weight"], 20)

    def test_no_silent_zero_set_export(self):
        client = Client(logging.getLogger("test"))
        client.request = lambda *args, **kwargs: []
        with self.assertRaisesRegex(APIError, "keine Übungsdetails"):
            client.detail(self.WORKOUT)

    def test_empty_set_detail_rejected(self):
        client = Client(logging.getLogger("test"))
        client.request = lambda *args, **kwargs: [
            {"actionLibraryName": "Übung", "finishedReps": []}]
        with self.assertRaisesRegex(APIError, "keine Übungsdetails"):
            client.detail(self.WORKOUT)


if __name__ == "__main__":
    unittest.main()
