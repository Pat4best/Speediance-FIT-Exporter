"""Official Garmin Personal API, FIT reading and per-field priority regressions.

Network is mocked: tests never require real Garmin API keys or upload anything.
"""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import json
import sys
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fitwriter import Encoder, stamp, write_fit
from garmin_fit_reader import GarminFitError, read_garmin_activity
from garmin_merge import DEFAULT_PRIORITIES, check_priorities, merge_workout
from garmin_personal import GarminPersonalClient, GarminPersonalError, match_activities
from preferences import save_merge_priorities, saved_merge_priorities
from test_fit_profile import decode


GARMIN_START = datetime(2026, 11, 16, 14, 20, tzinfo=timezone.utc)
SPEED_START = GARMIN_START + timedelta(seconds=60)


def garmin_fit_fixture():
    enc = Encoder()
    for delta, hr in ((60, 101), (65, 107), (85, 130)):
        enc.mesg(20, [(253, 0x86, stamp(GARMIN_START + timedelta(seconds=delta))),
                      (3, 2, hr)])
    enc.mesg(18, [
        (2, 0x86, stamp(GARMIN_START)), (7, 0x86, 360000),
        (8, 0x86, 360000), (11, 0x84, 416), (16, 2, 110), (17, 2, 146),
    ])
    return enc.result()


def speediance_fixture():
    return {
        "day": "2026-11-16",
        "training_id": 4567,
        "started_at": SPEED_START.isoformat(),
        "finished_at": (SPEED_START + timedelta(seconds=300)).isoformat(),
        "duration_min": 5,
        "calories": 454,
        "heart_rate_summary": {"avg": 115, "max": 150},
        "heart_rate_points": [(0, 90), (5, 100), (10, 150)],
        "exercises": [{
            "name": "Barbell Bench Press",
            "sets": [{"reps": 10, "weight": 20, "seconds": 25},
                     {"reps": 10, "weight": 20, "seconds": 25}],
        }],
    }


class GarminMergeTests(unittest.TestCase):
    def test_read_garmin_fit_record_and_session_values(self):
        garmin = read_garmin_activity(garmin_fit_fixture())
        self.assertEqual(garmin["start"], GARMIN_START)
        self.assertEqual(garmin["duration_seconds"], 360)
        self.assertEqual(garmin["heart_rate_summary"], {"avg": 110, "max": 146})
        self.assertEqual(garmin["calories"], 416)
        self.assertEqual(garmin["record_count"], 3)
        self.assertEqual(garmin["heart_rate_records"][0],
                         (GARMIN_START + timedelta(seconds=60), 101))

    def test_invalid_fit_crc_rejected(self):
        bad = bytearray(garmin_fit_fixture())
        bad[20] ^= 0x80
        with self.assertRaises(GarminFitError):
            read_garmin_activity(bytes(bad))

    def test_default_priorities_and_original_speediance_strength_times(self):
        speed = speediance_fixture()
        garmin = read_garmin_activity(garmin_fit_fixture())
        merged, meta = merge_workout(speed, garmin)
        self.assertEqual(meta["duration_seconds"], 360)
        self.assertEqual(merged["started_at"], GARMIN_START.isoformat())
        self.assertEqual(merged["strength_start_offset"], 60)
        self.assertEqual(merged["calories"], 416)
        self.assertEqual(merged["heart_rate_summary"], {"avg": 110, "max": 146})
        values = dict(merged["heart_rate_points"])
        # Default Garmin wins on overlap; Speediance fills real gaps.
        self.assertEqual(values[60], 101)
        self.assertEqual(values[65], 107)
        self.assertEqual(values[70], 150)
        self.assertEqual(len(values), 4)
        with TemporaryDirectory() as folder:
            p = write_fit(merged, Path(folder) / "merged.fit")
            messages = decode(p.read_bytes())
            session = next(f for n, f in messages if n == 18)
            self.assertEqual(session[16][1], 110)
            self.assertEqual(session[17][1], 146)  # even though fallback measured 150
            self.assertEqual(session[11][1], 416)
            strength = [f for n, f in messages if n == 225]
            self.assertEqual(len(strength), 2)
            self.assertEqual(strength[0][6][1], stamp(SPEED_START))
            self.assertEqual(strength[0][4][1] / 16, 20)
            heart_records = {f[253][1]: f[3][1] for n, f in messages
                             if n == 20 and 3 in f}
            self.assertEqual(heart_records[stamp(SPEED_START)], 101)

    def test_confirmed_csv_with_start_95_seconds_before_garmin(self):
        original = garmin_fit_fixture()
        speed = speediance_fixture()
        speed["started_at"] = (GARMIN_START - timedelta(seconds=95)).isoformat()
        speed["_set_source"] = "gm_manager_history_csv"
        speed["heart_rate_points"] = []  # CSV has no second-by-second HR
        merged, meta = merge_workout(speed, read_garmin_activity(original))
        self.assertEqual(meta["set_timing_aligned_to_activity_start"], True)
        self.assertEqual(merged["strength_start_offset"], 0)
        self.assertEqual(merged["started_at"], GARMIN_START.isoformat())
        self.assertEqual(merged["heart_rate_summary"]["avg"], 110)
        with TemporaryDirectory() as folder:
            emitted = write_fit(merged, Path(folder) / "rebased.fit")
            messages = decode(emitted.read_bytes())
        sets = [fields for number, fields in messages if number == 225]
        self.assertEqual(len(sets), 2)
        self.assertEqual(sets[0][6][1], stamp(GARMIN_START))
        self.assertEqual([fields[4][1] / 16 for fields in sets], [20.0, 20.0])

    def test_direct_speediance_sets_are_estimated_but_hr_remains_absolute(self):
        # Even the direct Speediance API supplies recorded reps, weights and
        # durations but no real per-SET start timestamps to write into FIT.
        # When the watch began later, shift estimated SET positions ONLY.
        # Genuine HR timestamps must still be mapped from their original
        # absolute Speediance start and Garmin records remain unchanged.
        g = read_garmin_activity(garmin_fit_fixture())
        s = speediance_fixture()
        s["started_at"] = (GARMIN_START - timedelta(seconds=95)).isoformat()
        s["finished_at"] = (GARMIN_START + timedelta(seconds=205)).isoformat()
        s["heart_rate_points"] = [(0, 90), (95, 128), (120, 140)]
        merged, meta = merge_workout(s, g)
        self.assertEqual(meta["set_timing_original_offset_seconds"], -95)
        self.assertEqual(merged["strength_start_offset"], 0)
        self.assertTrue(meta["set_timing_aligned_to_activity_start"])
        self.assertEqual(merged["started_at"], GARMIN_START.isoformat())
        series = dict(merged["heart_rate_points"])
        self.assertNotIn(-95, series)  # pre-watch sample is outside activity
        self.assertEqual(series[0], 128)  # genuine Speediance observation
        self.assertEqual(series[25], 140)
        self.assertEqual(series[60], 101)  # genuine Garmin watch observation
        self.assertEqual(series[65], 107)
        with TemporaryDirectory() as folder:
            output = write_fit(merged, Path(folder) / "direct.fit")
            result = decode(output.read_bytes())
        sets = [fields for num, fields in result if num == 225]
        self.assertEqual(len(sets), 2)
        self.assertEqual(sets[0][6][1], stamp(GARMIN_START))

    def test_speediance_can_override_each_metric_independently(self):
        speed = speediance_fixture()
        garmin = read_garmin_activity(garmin_fit_fixture())
        priorities = dict(DEFAULT_PRIORITIES, heart_curve="speediance",
                          heart_avg="speediance", heart_max="garmin",
                          calories="speediance", start="speediance",
                          duration="speediance")
        merged, _ = merge_workout(speed, garmin, priorities)
        self.assertEqual(merged["heart_rate_summary"], {"avg": 115, "max": 146})
        self.assertEqual(merged["calories"], 454)
        self.assertEqual(merged["strength_start_offset"], 0)
        self.assertEqual(merged["duration_seconds"], 300)
        self.assertEqual(dict(merged["heart_rate_points"])[0], 90)
        self.assertEqual(merged["started_at"], SPEED_START.isoformat())

    def test_fallback_to_other_source_only_when_missing(self):
        s = speediance_fixture()
        g = read_garmin_activity(garmin_fit_fixture())
        g["heart_rate_summary"] = {"avg": None, "max": 146}
        g["calories"] = None
        merged, _ = merge_workout(s, g)
        self.assertEqual(merged["heart_rate_summary"]["avg"], 115)
        self.assertEqual(merged["heart_rate_summary"]["max"], 146)
        self.assertEqual(merged["calories"], 454)

    def test_unsupported_priority_rejected(self):
        with self.assertRaises(ValueError):
            check_priorities({"heart_curve": "online_fake"})
        with self.assertRaises(ValueError):
            check_priorities({"gps": "garmin"})

    def test_nonsecret_priorities_saved_separately_from_api_key(self):
        with TemporaryDirectory() as folder:
            save_merge_priorities({"heart_curve": "speediance"}, folder)
            preferences = saved_merge_priorities(folder)
            self.assertEqual(preferences["heart_curve"], "speediance")
            self.assertEqual(preferences["calories"], "garmin")
            content = (Path(folder) / "settings.json").read_text()
            self.assertNotIn("api_key", content)
            self.assertNotIn("bearer", content)

    def test_matching_requires_start_and_duration_not_just_day(self):
        speed = speediance_fixture()
        good = {"activityId": 111, "activityName": "Krafttraining",
                "startTimeGMT": GARMIN_START.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": 360}
        wrong_time = dict(good, activityId=222,
                          startTimeGMT="2026-11-16 08:30:00")
        wrong_duration = dict(good, activityId=333, duration=15000)
        self.assertEqual(
            [c["id"] for c in match_activities(speed,
                [wrong_time, wrong_duration, good])],
            [111])


class _Response:
    def __init__(self, data):
        self._data = data
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return None
    def read(self, size=None):
        return self._data


class GarminApiTests(unittest.TestCase):
    def test_key_exchange_activity_list_and_zip_get_only(self):
        calls = []
        fit = garmin_fit_fixture()
        binary = BytesIO()
        with ZipFile(binary, "w") as archive:
            archive.writestr("original/activity.fit", fit)

        def opener(req, timeout=20):
            calls.append((req.get_method(), req.full_url,
                          req.get_header("Authorization")))
            if req.get_method() == "POST":
                return _Response(b"a." + b"x" * 40 + b".signature")
            if "/download-service/files/activity/" in req.full_url:
                return _Response(binary.getvalue())
            return _Response(json.dumps([{
                "activityId": 111, "startTimeGMT": "2026-11-16 14:20:00",
                "duration": 360,
            }]).encode("utf-8"))

        c = GarminPersonalClient("SECRET-TOKEN-NEVER-LOG", opener=opener)
        rows = c.activities("2026-11-16", "2026-11-16")
        self.assertEqual(rows[0]["activityId"], 111)
        self.assertEqual(c.download_activity_fit(111), fit)
        self.assertEqual([row[0] for row in calls], ["POST", "GET", "GET"])
        self.assertTrue(calls[0][2].startswith("ApiKey "))
        self.assertTrue(all(x[2].startswith("Bearer ") for x in calls[1:]))
        self.assertTrue(all("SECRET-TOKEN-NEVER-LOG" not in url
                            for _, url, _ in calls))


if __name__ == "__main__":
    unittest.main()
