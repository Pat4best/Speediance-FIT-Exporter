"""Exercise mapping dialog must be populated from selected training details."""
import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from exercise_discovery import discover_names


class FakeClient:
    def __init__(self):
        self.calls = []

    def detail(self, workout):
        self.calls.append(workout["id"])
        if workout["id"] == 2:
            raise RuntimeError("Simulated missing Speediance details")
        return {"exercises": [
            {"name": "Kreuzheben", "sets": [{"reps": 5}]},
            {"name": "Skater", "sets": [{"seconds": 30}]},
            {"name": "Kreuzheben", "sets": [{"reps": 4}]},
        ]}


class DiscoveryTests(unittest.TestCase):
    def test_selected_workouts_populate_editor(self):
        client = FakeClient()
        names, failures = discover_names(client, [{"id": 1}, {"id": 2}],
                                        logging.getLogger("test"))
        self.assertEqual(names, ["Kreuzheben", "Skater"])
        self.assertEqual(failures, 1)
        self.assertEqual(client.calls, [1, 2])

    def test_no_selection_does_not_contact_api(self):
        client = FakeClient()
        self.assertEqual(discover_names(client, []), ([], 0))
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
