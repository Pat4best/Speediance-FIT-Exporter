"""Tests that missing Speediance sets do not block Garmin-first merges."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from garmin_dialog import details_or_history
from speediance_api import APIError
from garmin_fit_overlay import GarminOverlayError


class _Client:
    def __init__(self, answer):
        self.answer = answer

    def detail(self, workout):
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class GarminDetailFallbackTests(unittest.TestCase):
    def test_unavailable_completed_sets_block_merge_instead_of_silent_fallback(self):
        history = {"day": "2026-11-16", "duration_min": 56.5,
                   "calories": 454, "training_id": 5151}
        with self.assertRaisesRegex(GarminOverlayError, "History-CSV"):
            details_or_history(_Client(APIError(
                "Speediance hat für diese Trainingseinheit keine Übungsdetails geliefert"
            )), history)

    def test_empty_detail_also_blocks_merge(self):
        with self.assertRaisesRegex(GarminOverlayError, "Keine abgeschlossenen"):
            details_or_history(_Client({"exercises": []}), {})

    def test_valid_detail_is_used(self):
        detail = {"exercises": [{"sets": [{"reps": 10}]}]}
        self.assertIs(details_or_history(_Client(detail), {}), detail)

    def test_other_api_errors_are_not_masked(self):
        with self.assertRaises(APIError):
            details_or_history(_Client(APIError("Login failed")), {})


if __name__ == "__main__":
    unittest.main()
