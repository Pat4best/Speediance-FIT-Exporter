"""Garmin-binary-first Speediance strength merge regression tests.

Prove that the Garmin activity is the base: original record bytes and unknown
developer/proprietary data survive; only selected metrics and strength SET
messages are edited. Never commit real user recordings or credentials.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fitwriter import Encoder, stamp, write_fit
from garmin_fit_overlay import overlay_garmin_fit, parse_fit_wire, GarminOverlayError
from garmin_merge import DEFAULT_PRIORITIES
from test_fit_profile import decode, crc


GARMIN_START = datetime(2026, 11, 16, 14, 19, 52, tzinfo=timezone.utc)
SPEED_START = GARMIN_START + timedelta(seconds=40)


def original_garmin_fit():
    enc = Encoder()
    enc.mesg(0, [
        (0, 0, 4), (1, 0x84, 1), (2, 0x84, 2222),
        (3, 0x8C, 12345678), (4, 0x86, stamp(GARMIN_START)),
    ])
    enc.mesg(23, [
        (253, 0x86, stamp(GARMIN_START)),
        (0, 2, 0), (2, 0x84, 1), (27, 7, "Fenix original watch"),
    ])
    enc.mesg(233, [(253, 0x86, stamp(GARMIN_START)), (0, 0x86, 1234)])
    enc.mesg(534, [(253, 0x86, stamp(GARMIN_START)), (0, 0x86, 9876)])
    # An original, rough Garmin SET is replaced with two actual Speediance sets.
    enc.mesg(225, [
        (254, 0x86, stamp(GARMIN_START + timedelta(seconds=5))),
        (0, 0x86, 5000), (3, 0x84, 1), (4, 0x84, 0xFFFF),
        (5, 2, 1), (6, 0x86, stamp(GARMIN_START)), (7, 0x84, 8),
        (8, 0x84, 0),
    ])
    for sec, hr in ((0, 90), (40, 100), (45, 110), (65, 130), (85, 140)):
        enc.mesg(20, [(253, 0x86, stamp(GARMIN_START + timedelta(seconds=sec))),
                      (3, 2, hr), (5, 0x86, 0)])
    enc.mesg(19, [
        (253, 0x86, stamp(GARMIN_START + timedelta(seconds=360))),
        (2, 0x86, stamp(GARMIN_START)),
        (7, 0x86, 360000), (8, 0x86, 360000),
        (10, 0x86, 57),
        (11, 0x84, 416), (15, 2, 111), (16, 2, 146),
    ])
    enc.mesg(18, [
        (253, 0x86, stamp(GARMIN_START + timedelta(seconds=360))),
        (2, 0x86, stamp(GARMIN_START)), (7, 0x86, 360000),
        (8, 0x86, 360000), (10, 0x86, 57),
        (11, 0x84, 416),
        (16, 2, 111), (17, 2, 146),
    ])
    enc.mesg(34, [
        (253, 0x86, stamp(GARMIN_START + timedelta(seconds=360))),
        (0, 0x86, 360000), (1, 0x84, 1),
        (2, 0, 0), (3, 0, 26), (4, 0, 1),
    ])
    return enc.result()


def speediance_executed():
    return {
        "day": "2026-11-16", "training_id": 5151,
        "started_at": SPEED_START.isoformat(),
        "finished_at": (SPEED_START + timedelta(seconds=300)).isoformat(),
        "duration_min": 5, "calories": 454,
        "heart_rate_points": [(0, 95), (10, 120), (25, 155), (30, 110)],
        "heart_rate_summary": {"avg": 115, "max": 155},
        "exercises": [{
            "name": "Barbell Bench Press",
            "sets": [
                {"reps": 10, "seconds": 25,
                 "weight": 20, "weight_already_total": True},
                {"reps": 10, "seconds": 25,
                 "weight": 20, "weight_already_total": True},
            ],
        }],
    }


def values(fit, number):
    return [f for n, f in decode(fit) if n == number]


def all_message_data(raw, glob):
    return [m["raw"] for m in parse_fit_wire(raw)
            if m["kind"] == "data" and m["global"] == glob]


class GarminOverlayTests(unittest.TestCase):
    def test_preserves_garmin_data_and_replaces_only_native_sets(self):
        original = original_garmin_fit()
        speed = speediance_executed()
        with TemporaryDirectory() as folder:
            filename, meta = overlay_garmin_fit(
                original, speed, Path(folder) / "garmin-first.fit"
            )
            result = filename.read_bytes()
        self.assertNotEqual(result, original)
        self.assertEqual(meta["garmin_device_info"], 1)
        self.assertEqual(meta["new_speediance_sets"], 2)
        self.assertEqual(meta["replaced_garmin_sets"], 1)
        self.assertGreater(meta["garmin_original_messages"], 5)
        self.assertEqual(meta["patched_hr_records"], 0)
        self.assertEqual(all_message_data(original, 23),
                         all_message_data(result, 23))
        self.assertEqual(all_message_data(original, 233),
                         all_message_data(result, 233))
        self.assertEqual(all_message_data(original, 534),
                         all_message_data(result, 534))
        # Every ORIGINAL Garmin HR record is unchanged, including distance.
        original_records = all_message_data(original, 20)
        for record in original_records:
            self.assertIn(record, all_message_data(result, 20))
        self.assertEqual(len(values(result, 225)), 2)
        self.assertEqual([r[4][1] / 16 for r in values(result, 225)],
                         [20.0, 20.0])
        # Extra Speediance-only real HR measurements fill timeline gaps.
        native_hrs = {
            r[253][1]: r[3][1]
            for r in values(result, 20) if 253 in r and 3 in r
        }
        self.assertEqual(native_hrs[stamp(SPEED_START)], 100)
        self.assertEqual(native_hrs[stamp(SPEED_START + timedelta(seconds=10))], 120)
        self.assertEqual(native_hrs[stamp(SPEED_START + timedelta(seconds=25))], 130)
        self.assertEqual(values(result, 18)[0][10][1], 20)
        self.assertEqual(values(result, 19)[0][10][1], 20)
        self.assertEqual(meta["speediance_repetitions"], 20)
        self.assertEqual(values(result, 18)[0][11][1], 416)
        self.assertEqual(values(result, 18)[0][16][1], 111)
        # New derived file ID, original Garmin device_info preserved.
        original_id = values(original, 0)[0]
        derivative_id = values(result, 0)[0]
        self.assertEqual(original_id[1][1], 1)
        self.assertEqual(derivative_id[1][1], 255)
        self.assertNotEqual(derivative_id[3][1], original_id[3][1])

    def test_speediance_record_priority_changes_only_hr_byte(self):
        opts = dict(DEFAULT_PRIORITIES, heart_curve="speediance")
        original = original_garmin_fit()
        with TemporaryDirectory() as folder:
            file, meta = overlay_garmin_fit(
                original, speediance_executed(),
                Path(folder) / "prefer-speed.fit", opts)
            result = file.read_bytes()
        self.assertEqual(meta["patched_hr_records"], 2)
        original_raw = all_message_data(original, 20)
        final_raw = all_message_data(result, 20)
        # No native records disappear; one overlapping HR byte is changed.
        self.assertEqual(len(final_raw), len(original_raw) + meta["added_hr_records"])
        changed = {
            r[253][1]: r[3][1]
            for r in values(result, 20) if 253 in r and 3 in r
        }
        self.assertEqual(changed[stamp(SPEED_START)], 95)
        self.assertEqual(changed[stamp(SPEED_START + timedelta(seconds=25))], 155)

    def test_speediance_priority_for_summary_time_and_calories(self):
        opts = dict(DEFAULT_PRIORITIES, start="speediance",
                    duration="speediance", calories="speediance",
                    heart_avg="speediance", heart_max="speediance")
        with TemporaryDirectory() as folder:
            file, meta = overlay_garmin_fit(
                original_garmin_fit(), speediance_executed(),
                Path(folder) / "prefer-speed-summary.fit", opts)
            result = file.read_bytes()
        session = values(result, 18)[0]
        self.assertEqual(session[2][1], stamp(SPEED_START))
        self.assertEqual(session[7][1], 300000)
        self.assertEqual(session[8][1], 300000)
        self.assertEqual(session[11][1], 454)
        self.assertEqual(session[16][1], 115)
        self.assertEqual(session[17][1], 155)
        lap = values(result, 19)[0]
        self.assertEqual(lap[11][1], 454)
        self.assertEqual(lap[15][1], 115)
        self.assertEqual(values(result, 34)[0][0][1], 300000)
        self.assertEqual(len(values(result, 225)), 2)
        self.assertEqual(all_message_data(result, 23),
                         all_message_data(original_garmin_fit(), 23))

    def test_timed_exercises_do_not_inflate_repetition_summary(self):
        speed = speediance_executed()
        speed["exercises"].append({
            "name": "Cardio ski timed",
            "completion_method": 2,
            "sets": [{"reps": 300, "weight": 0, "seconds": 300}],
        })
        # Timed sets still exist as Speediance SET messages but 300 seconds
        # must not become 300 completed strength repetitions.
        with TemporaryDirectory() as folder:
            file, meta = overlay_garmin_fit(
                original_garmin_fit(), speed,
                Path(folder) / "timed-ski.fit")
            session = values(file.read_bytes(), 18)[0]
        self.assertEqual(meta["new_speediance_sets"], 3)
        self.assertEqual(meta["speediance_repetitions"], 20)
        self.assertEqual(session[10][1], 20)

    def test_original_garmin_file_never_modified(self):
        original = original_garmin_fit()
        with TemporaryDirectory() as folder:
            file, meta = overlay_garmin_fit(
                original, speediance_executed(), Path(folder) / "merged.fit")
            self.assertEqual(original, original_garmin_fit())
            self.assertTrue(file.read_bytes())
            self.assertEqual(crc(file.read_bytes()[:-2]),
                             struct.unpack_from("<H", file.read_bytes(),
                                                len(file.read_bytes()) - 2)[0])


if __name__ == "__main__":
    unittest.main()
