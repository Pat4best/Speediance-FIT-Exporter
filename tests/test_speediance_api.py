"""Tests for alternative Speediance detail endpoints and privacy-safe failures."""
import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from speediance_api import Client, APIError, completed_history_shape, workout_provenance_shape


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

    def test_unrelated_history_cross_reference_is_not_assigned_to_selected_workout(self):
        # Mirrors the observed history situation: 2 history-only sessions,
        # 1 calendar duplicate, but the top selected custom workout need
        # not be the duplicate that generated the previous diagnosis.
        selected = {
            "training_id": 1000, "day": "2026-11-16",
            "title": "Custom workout", "duration_min": 56 + 34 / 60,
        }
        other_rows = [
            {"training_id": 3000, "day": "2026-11-11",
             "title": "Other workout", "duration_seconds": 180},
            {"training_id": 3001, "day": "2026-11-13",
             "title": "Warm up", "duration_seconds": 360},
            {"training_id": 3002, "day": "2026-11-13",
             "title": "First workout", "duration_seconds": 310},
        ]
        shape = workout_provenance_shape(selected, other_rows)
        self.assertFalse(shape["matched_by_trainingId"])
        self.assertEqual(shape["history_on_same_day"], 0)
        self.assertEqual(shape["same_day_title_and_duration"], 0)
        self.assertNotIn("1000", str(shape))
        self.assertNotIn("2026-11-16", str(shape))
        # A same-day session with a *different* ID is diagnostic only;
        # it must never automatically replace the selected workout ID.
        other_rows.append({
            "training_id": 4444, "day": "2026-11-16",
            "title": "Custom workout", "duration_seconds": 3394,
        })
        shape = workout_provenance_shape(selected, other_rows)
        self.assertFalse(shape["matched_by_trainingId"])
        self.assertEqual(shape["history_on_same_day"], 1)
        self.assertEqual(shape["same_day_title_and_duration"], 1)
        other_rows[-1]["training_id"] = 1000
        shape = workout_provenance_shape(selected, other_rows)
        self.assertTrue(shape["matched_by_trainingId"])

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
