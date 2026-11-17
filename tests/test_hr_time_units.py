"""Speediance watch-graph real pulse values with absolute/relative times.

Live diagnostics: heartRates[942] contains dicts with int heartRate and
int time. All values are valid BPM, but every time is > 86400. The unit
is not logged, so support and test the plausible Unix and ms clock types.
"""
import logging
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from activity_time import activity_bounds
from heart_rate import graph_details
from speediance_api import Client
from fitwriter import write_fit
from test_fit_profile import decode

START = datetime.fromisoformat("2026-11-16T15:20:00+01:00")
START_UNIX = START.timestamp()


class SpeedianceHeartTimeTests(unittest.TestCase):
    def test_942_real_samples_from_unix_milliseconds_preserve_timeline(self):
        series = [
            {"time": int(START_UNIX * 1000) + sec * 1000,
             "heartRate": 110 + (i % 21)}
            for i, sec in enumerate(range(0, 2826, 3))
        ]
        self.assertEqual(len(series), 942)
        result = graph_details({
            "heartRates": series, "avgHeartRate": 110, "maxHeartRate": 146
        }, duration_seconds=3000, start_epoch=START_UNIX)
        self.assertEqual(len(result["points"]), 942)
        self.assertEqual(result["points"][0], (0, 110))
        self.assertEqual(result["points"][-1][0], 2823)
        self.assertEqual(result["time_mode"], "unix_milliseconds")
        self.assertFalse(result["timing_estimated"])
        self.assertEqual(result["skipped_time_points"], 0)

    def test_unix_seconds_and_microseconds(self):
        for scale, mode in ((1, "unix_seconds"),
                            (1000000, "unix_microseconds")):
            with self.subTest(mode=mode):
                vals = [
                    {"time": round((START_UNIX + sec) * scale), "heartRate": 105}
                    for sec in (0, 2, 5)
                ]
                result = graph_details({"heartRates": vals},
                                       duration_seconds=10,
                                       start_epoch=START_UNIX)
                self.assertEqual(result["points"], [(0, 105), (2, 105), (5, 105)])
                self.assertEqual(result["time_mode"], mode)
                self.assertFalse(result["timing_estimated"])

    def test_elapsed_milliseconds_when_under_one_day(self):
        vals = [{"heartRate": 120, "time": 0},
                {"heartRate": 125, "time": 30000},
                {"heartRate": 130, "time": 60000}]
        result = graph_details({"heartRates": vals}, duration_seconds=60)
        self.assertEqual(result["points"], [(0, 120), (30, 125), (60, 130)])
        self.assertEqual(result["time_mode"], "elapsed_milliseconds")

    def test_relative_ms_with_nonzero_origin_flags_estimate(self):
        vals = [{"heartRate": 120, "time": 3_000_000},
                {"heartRate": 122, "time": 3_100_000},
                {"heartRate": 123, "time": 3_200_000}]
        result = graph_details({"heartRates": vals}, duration_seconds=200)
        self.assertEqual(result["points"], [(0, 120), (100, 122), (200, 123)])
        self.assertEqual(result["time_mode"], "relative_milliseconds_rebased")
        self.assertTrue(result["timing_estimated"])

    def test_epoch_timezone_disagreement_rebases_with_warning(self):
        vals = [{"heartRate": 120, "time": int((START_UNIX + 3600) * 1000)},
                {"heartRate": 125, "time": int((START_UNIX + 3620) * 1000)}]
        result = graph_details({"heartRates": vals}, duration_seconds=60,
                               start_epoch=START_UNIX)
        self.assertEqual(result["points"], [(0, 120), (20, 125)])
        self.assertEqual(result["time_mode"], "unix_milliseconds_rebased")
        self.assertTrue(result["timing_estimated"])

    def test_no_unjustified_rebase_when_epoch_from_wrong_year(self):
        old = datetime.fromisoformat("2020-11-16T15:20:00+01:00").timestamp()
        vals = [{"time": int(old * 1000), "heartRate": 125}]
        result = graph_details({"heartRates": vals}, duration_seconds=60,
                               start_epoch=START_UNIX)
        self.assertEqual(result["points"], [])
        self.assertEqual(result["time_mode"], "unix_milliseconds_clock_mismatch")

    def test_local_second_of_day_supported(self):
        vals = [{"time": 15 * 3600 + sec, "heartRate": 100}
                for sec in (0, 10, 20)]
        result = graph_details({"heartRates": vals}, duration_seconds=30,
                               start_day_seconds=15 * 3600)
        self.assertEqual(result["points"], [(0, 100), (10, 100), (20, 100)])
        self.assertEqual(result["time_mode"], "seconds_since_midnight")

    def test_activity_bounds_prefers_history_true_start_clock(self):
        workout = {
            "day": "2026-11-16", "started_at": START.isoformat(),
            "finished_at": (START + timedelta(minutes=58)).isoformat(),
            "duration_min": 55,
            "exercises": [{"name": "Row", "sets": [{"seconds": 60}]}],
        }
        start, end, duration = activity_bounds(workout)
        self.assertEqual(start, START)
        self.assertEqual(duration, 3300)
        self.assertEqual(end, START + timedelta(seconds=3300))

    def test_client_to_fit_integration_942_timestamped_hr_records(self):
        client = Client(logging.getLogger("test-speediance-epoch"))
        graph = [
            {"time": int(START_UNIX * 1000) + i * 3000,
             "heartRate": 110 + i % 20}
            for i in range(942)
        ]
        def request(path, **kwargs):
            if "getHeartRateGraph" in path:
                return {"heartRates": graph,
                        "avgHeartRate": 110, "maxHeartRate": 146}
            return [{"actionLibraryName": "Barbell Bench Press",
                     "finishedReps": [{"finishedCount": 8, "time": 20,
                        "maxHeartRate": 146,
                        "trainingInfoDetail": {
                            "uuid": "test-session-uuid", "weights": [25.0],
                        }}]}]
        client.request = request
        workout = {
            "day": "2026-11-16", "started_at": START.isoformat(),
            "finished_at": (START + timedelta(seconds=3000)).isoformat(),
            "duration_min": 50, "training_id": 12345, "type": 5,
        }
        detailed = client.detail(workout)
        self.assertEqual(len(detailed["heart_rate_points"]), 942)
        with TemporaryDirectory() as td:
            path = write_fit(detailed, Path(td) / "activity.fit")
            messages = decode(path.read_bytes())
            heart = [f for n, f in messages if n == 20 and 3 in f]
            self.assertEqual(len(heart), 942)
            self.assertEqual(heart[1][253][1] - heart[0][253][1], 3)
            self.assertEqual(heart[-1][253][1] - heart[0][253][1], 2823)
            session = next(f for n, f in messages if n == 18)
            self.assertEqual(session[16][1], 110)
            self.assertEqual(session[17][1], 146)


if __name__ == "__main__":
    unittest.main()
