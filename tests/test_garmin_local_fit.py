"""Offline Garmin FIT file selection and Speediance API legacy GET fallback.

No account credentials, API key or network request are used in these tests.
"""
from datetime import timedelta
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fitwriter import write_fit
from garmin_fit_overlay import overlay_garmin_fit
from garmin_local_fit import (
    LocalGarminFitError, read_local_garmin_fit,
    match_local_garmin_fit, validated_local_fit,
)
from speediance_api import Client, APIError
from test_garmin_fit_overlay import original_garmin_fit, speediance_executed


class LocalGarminFileTests(unittest.TestCase):
    def test_offline_original_garmin_fit_is_valid_and_time_matched(self):
        original = original_garmin_fit()
        with TemporaryDirectory() as td:
            path = Path(td) / "self-downloaded-from-connect.fit"
            path.write_bytes(original)
            saved, digest, metrics = read_local_garmin_fit(path)
            self.assertEqual(saved, original)
            self.assertEqual(len(digest), 64)
            self.assertEqual(metrics["record_count"], 5)
            match = match_local_garmin_fit(speediance_executed(), metrics)
            self.assertEqual(match["start_delta_seconds"], 40)
            self.assertEqual(match["record_count"], 5)
            self.assertEqual(validated_local_fit(speediance_executed(), path)[0],
                             original)

    def test_manual_download_still_preserves_garmin_fields_and_strength_sets(self):
        with TemporaryDirectory() as td:
            original = Path(td) / "fenix.fit"
            original.write_bytes(original_garmin_fit())
            contents, _, _ = validated_local_fit(speediance_executed(), original)
            dest, meta = overlay_garmin_fit(
                contents, speediance_executed(), Path(td) / "merged.fit"
            )
            self.assertTrue(dest.is_file())
            self.assertEqual(meta["new_speediance_sets"], 2)
            self.assertEqual(meta["garmin_device_info"], 1)

    def test_rejects_a_speediance_export_in_place_of_original_garmin(self):
        with TemporaryDirectory() as td:
            src = Path(td) / "speediance.fit"
            write_fit(speediance_executed(), src)
            with self.assertRaisesRegex(LocalGarminFitError,
                                        "originale Garmin-FIT"):
                read_local_garmin_fit(src)

    def test_rejects_mismatched_activity_even_if_date_matches(self):
        original = original_garmin_fit()
        with TemporaryDirectory() as td:
            src = Path(td) / "original.fit"
            src.write_bytes(original)
            _, _, metrics = read_local_garmin_fit(src)
            wrong = dict(speediance_executed())
            wrong["started_at"] = "2026-11-16T19:20:00+00:00"
            with self.assertRaisesRegex(LocalGarminFitError,
                                        "passt zeitlich nicht"):
                match_local_garmin_fit(wrong, metrics)
            wrong = dict(speediance_executed())
            wrong["duration_min"] = 60
            with self.assertRaises(LocalGarminFitError):
                match_local_garmin_fit(wrong, metrics)

    def test_rejects_invalid_file_and_corrupt_crc(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "garmin.fit"
            p.write_bytes(b"garbage-not-a-fit")
            with self.assertRaises(LocalGarminFitError):
                read_local_garmin_fit(p)
            corrupt = bytearray(original_garmin_fit())
            corrupt[-1] ^= 1
            p.write_bytes(corrupt)
            with self.assertRaises(LocalGarminFitError):
                read_local_garmin_fit(p)

    def test_local_input_does_not_modify_original_fit(self):
        with TemporaryDirectory() as td:
            src = Path(td) / "garmin.fit"
            raw = original_garmin_fit()
            src.write_bytes(raw)
            got, _, _ = validated_local_fit(speediance_executed(), src)
            overlay_garmin_fit(got, speediance_executed(), Path(td) / "new.fit")
            self.assertEqual(src.read_bytes(), raw)


class LegacyCompletedSetReadTests(unittest.TestCase):
    def test_retry_old_read_only_version_after_new_server_error(self):
        c = Client(logging.getLogger("test-speediance-alt-version"))
        calls = []
        def request(path, **kwargs):
            calls.append((path, kwargs))
            if kwargs.get("read_version") != "40304":
                return None  # newest backend rejected this workout ID
            if "cttTrainingInfoDetail" in path:
                return [{
                    "actionLibraryName": "Sitzendes Rudern mit zwei Griffen",
                    "finishedReps": [{
                        "finishedCount": 10, "time": 25,
                        "trainingInfoDetail": {
                            "leftWeights": [10, 10],
                            "rightWeights": [10, 10],
                        },
                    }],
                }]
            return None
        c.request = request
        workout = {"day": "2026-11-16", "type": 5,
                   "training_id": 456, "duration_min": 5}
        detail = c.detail(workout)
        self.assertTrue(any(k.get("read_version") == "40304"
                            for _, k in calls))
        self.assertEqual(detail["exercises"][0]["sets"][0]["weight"], 20)
        self.assertTrue(all(k.get("allow_error") for _, k in calls))

    def test_never_fabricate_workout_when_both_versions_fail(self):
        c = Client(logging.getLogger("test-speediance-alt-no-data"))
        calls = []
        def request(path, **kwargs):
            calls.append((path, kwargs))
            return None
        c.request = request
        with self.assertRaisesRegex(APIError, "keine Übungsdetails"):
            c.detail({"day": "2026-11-16", "type": 5,
                      "training_id": 456, "duration_min": 5})
        self.assertEqual(len(calls), 8)
        self.assertTrue(all(k.get("allow_error") for _, k in calls))


if __name__ == "__main__":
    unittest.main()
