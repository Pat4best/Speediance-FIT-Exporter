"""Direct Speediance completed sets and proactive local snapshot regressions.

Synthetic responses model observed API shapes. Nothing contacts a cloud API,
requires real workout metadata, or accesses the user's Windows credentials.
"""
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import logging
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from completed_workout_cache import load_detail_cache
from speediance_api import Client, APIError, free_lift_to_finished_reps

TODAY = date(2026, 11, 18)


def workout(training_id=511, *, type_=1, day="2026-11-17"):
    return {"training_id": training_id, "day": day, "title": "Synthetic Workout",
            "type": type_, "history_type": type_, "unit": "kg",
            "duration_min": 25, "calories": 200}


def free_lift_payload():
    return {
        "type": 1,
        "totalCapacity": 440,
        "actionList": [{
            "actionLibraryName": "Two Handle Row",
            "completionMethod": 1,
            "setList": [
                {"summary": {"finishedCount": 10, "time": 30,
                             "weight": 22, "totalCapacity": 440}},
                {"summary": {"finishedCount": 0, "time": 0,
                             "weight": 60}},  # prescribed/unperformed: reject
                {"summary": {"targetCount": 10,
                             "weight": 60}},  # prescribed, NOT recorded
            ],
        }],
    }


class DirectSpeedianceTests(unittest.TestCase):
    def client(self, root=None):
        result = Client(logging.getLogger("test-direct-speediance"),
                        cache_dir=root)
        result.user_id = "synthetic-user"
        result.token = "fake-session-only"
        return result

    def test_free_lift_nested_summary_normalized_from_direct_api(self):
        with TemporaryDirectory() as root:
            client = self.client(root)
            paths = []
            def request(path, **kwargs):
                paths.append(path)
                if path.endswith("/freeTraining/511"):
                    return free_lift_payload()
                return None
            client.request = request
            recorded = client.detail(workout())
            self.assertEqual(len(recorded["exercises"]), 1)
            sets = recorded["exercises"][0]["sets"]
            self.assertEqual(len(sets), 1)
            self.assertEqual(sets[0]["reps"], 10)
            self.assertEqual(sets[0]["seconds"], 30)
            self.assertEqual(sets[0]["weight"], 22)
            self.assertTrue(sets[0]["weight_already_total"])
            self.assertEqual(paths, ["/api/app/trainingInfo/freeTraining/511"])
            cached = load_detail_cache(root, client.host, client.user_id, workout())
            self.assertIsNotNone(cached)
            self.assertEqual(cached["exercises"][0]["sets"][0]["weight"], 22)

    def test_free_lift_never_uses_unperformed_target_sets(self):
        source = {"actionList": [{"actionLibraryName": "Example",
                  "setList": [
                      {"summary": {"targetCount": 10, "weight": 50}},
                      {"summary": {"finishedCount": 0, "time": 0, "weight": 30}},
                  ]}]}
        self.assertEqual(free_lift_to_finished_reps(source), [])
        client = self.client()
        client.request = lambda *args, **kwargs: source
        with self.assertRaisesRegex(APIError, "keine Übungsdetails"):
            client.detail(workout())

    def test_free_training_detail_fallback_is_supported(self):
        client = self.client()
        calls = []
        def request(path, **kwargs):
            calls.append(path)
            if path.endswith("/freeTrainingDetail/511"):
                return [{"actionLibraryName": "Row", "completionMethod": 1,
                         "finishedReps": [{"finishedCount": 8, "time": 21,
                                           "trainingInfoDetail": {
                                               "weights": [10, 20, 20]}}]}]
            return None
        client.request = request
        data = client.detail(workout())
        self.assertEqual(len(data["exercises"][0]["sets"]), 1)
        self.assertEqual(data["exercises"][0]["sets"][0]["weight"], 20)
        self.assertIn("/api/app/trainingInfo/freeTrainingDetail/511", calls)

    def test_history_refresh_auto_caches_recent_completed_sets_offline_later(self):
        with TemporaryDirectory() as root:
            client = self.client(root)
            calls = []
            def request(path, **kwargs):
                calls.append((path, kwargs.get("read_version")))
                if path.endswith("/cttTrainingInfoDetail/512"):
                    return [{"actionLibraryName": "Two Handle Row",
                             "completionMethod": 1,
                             "finishedReps": [{
                                 "finishedCount": 10, "time": 27,
                                 "trainingInfoDetail": {
                                     "leftWeights": [13, 10, 10],
                                     "rightWeights": [13, 10, 10],
                                 }}]}]
                return None
            client.request = request
            session = workout(512, type_=5)
            stats = client.snapshot_recent_workouts([session], today=TODAY)
            self.assertEqual(stats, {"attempted": 1, "saved": 1,
                                     "already_cached": 0, "unavailable": 0})
            self.assertTrue(all(version is None for _, version in calls))
            self.assertEqual(len(calls), 1)
            new_client = self.client(root)
            new_client.request = lambda *a, **kw: self.fail(
                "A verified cached workout must never need a new API call")
            result = new_client.detail(session)
            self.assertEqual(result["exercises"][0]["sets"][0]["reps"], 10)
            self.assertEqual(result["exercises"][0]["sets"][0]["weight"], 20)
            self.assertTrue(result["exercises"][0]["sets"][0]["weight_already_total"])
            stats = new_client.snapshot_recent_workouts([session], today=TODAY)
            self.assertEqual(stats["attempted"], 0)
            self.assertEqual(stats["already_cached"], 1)

    def test_missing_cloud_details_never_create_synthetic_cache(self):
        with TemporaryDirectory() as root:
            client = self.client(root)
            calls = []
            client.request = lambda path, **kwargs: calls.append(path) or None
            session = workout(515, type_=5)
            stats = client.snapshot_recent_workouts([session], today=TODAY)
            self.assertEqual(stats["attempted"], 1)
            self.assertEqual(stats["saved"], 0)
            self.assertEqual(stats["unavailable"], 1)
            self.assertLessEqual(len(calls), 5)  # current-version, bounded
            self.assertIsNone(load_detail_cache(
                root, client.host, client.user_id, session))
            before = len(calls)
            again = client.snapshot_recent_workouts([session], today=TODAY)
            self.assertEqual(again["attempted"], 0)
            self.assertEqual(len(calls), before)  # no repeat probes in session
            # The interactive merge can still try the normal full fallback.
            with self.assertRaises(APIError):
                client.detail(session)
            self.assertGreater(len(calls), before)

    def test_main_history_loading_triggers_snapshot_without_second_action(self):
        from main import App

        class Field:
            def __init__(self, value=""):
                self.value = value
            def get(self):
                return self.value
            def set(self, value):
                self.value = value

        class Table:
            def __init__(self):
                self.insertions = []
            def get_children(self):
                return []
            def insert(self, *args, **kwargs):
                self.insertions.append(kwargs["values"])

        requested = []
        session = workout(512, type_=5)
        fake_client = SimpleNamespace(
            list_workouts=lambda start, end:
                requested.append(("list", start, end)) or [session],
            snapshot_recent_workouts=lambda sessions:
                requested.append(("snapshot", sessions)) or
                {"attempted": 1, "saved": 1,
                 "already_cached": 0, "unavailable": 0},
            calendar_fallback_added=0, calendar_other_device_added=0,
            history_added=1,
        )
        fake = SimpleNamespace(
            client=fake_client, from_date=Field("2026-11-16"),
            to_date=Field("2026-11-18"), sessions=[],
            table=Table(), status=Field(), tr=lambda text: text,
            run_job=lambda action, done: done(action()),
        )
        App.fetch(fake)
        self.assertEqual([r[0] for r in requested], ["list", "snapshot"])
        self.assertEqual(fake.sessions, [session])
        self.assertEqual(len(fake.table.insertions), 1)
        self.assertIn("Automatisch gesichert: 1", fake.status.get())

    def test_recent_limit_skips_stale_future_and_unauthed_records(self):
        with TemporaryDirectory() as root:
            client = self.client(root)
            client.request = lambda path, **kwargs: (
                [{"actionLibraryName": "Example",
                  "finishedReps": [{"finishedCount": 4, "time": 10,
                                    "trainingInfoDetail": {"weights": [15]}}]}]
            )
            sessions = [workout(600, type_=5, day="2026-10-01"),
                        workout(601, type_=5, day="2026-11-20"),
                        workout(602, type_=5),
                        workout(603, type_=5),
                        workout(604, type_=5)]
            stats = client.snapshot_recent_workouts(
                sessions, today=TODAY, max_attempts=2)
            self.assertEqual(stats["attempted"], 2)
            self.assertEqual(stats["saved"], 2)
            self.assertIsNone(load_detail_cache(
                root, client.host, client.user_id, sessions[0]))
            self.assertIsNone(load_detail_cache(
                root, client.host, client.user_id, sessions[1]))
            self.assertIsNone(load_detail_cache(
                root, client.host, client.user_id, sessions[4]))
            other = Client(logging.getLogger("test-unauth"), cache_dir=root)
            self.assertEqual(other.snapshot_recent_workouts(
                sessions, today=TODAY)["attempted"], 0)


if __name__ == "__main__":
    unittest.main()
