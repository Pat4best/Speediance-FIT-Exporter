"""Tests for alternative Speediance detail endpoints and privacy-safe failures."""
import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from speediance_api import Client, APIError


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

    def test_no_silent_zero_set_export(self):
        client = Client(logging.getLogger("test"))
        client.request = lambda *args, **kwargs: []
        with self.assertRaisesRegex(APIError, "keine Übungsdetails"):
            client.detail(self.WORKOUT)

    def test_empty_set_detail_rejected(self):
        client = Client(logging.getLogger("test"))
        client.request = lambda *args, **kwargs: [
            {"actionLibraryName": "Übung", "finishedReps": []}]
        with self.assertRaisesRegex(APIError, "keine Sätze"):
            client.detail(self.WORKOUT)


if __name__ == "__main__":
    unittest.main()
