"""Bilingual HRM 600 source, Speediance graph payload and FIT device_info."""
import logging
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from heart_rate import graph_details, graph_points
from hr_sensor import find_hr_sensor, user_confirmed_sensor
from fitwriter import write_fit
from preferences import save_hr_sensor_name, load_hr_sensor_name
from speediance_api import Client
from test_fit_profile import decode
from i18n import translate


class HRSourceTests(unittest.TestCase):
    def test_speediance_actual_heart_rates_array_uses_real_values(self):
        graph = {
            "uuid": "sensitive-uuid", "minHeartRate": 96,
            "avgHeartRate": 110, "maxHeartRate": 146,
            "heartRates": [96, 105, 0, 124, 146],
        }
        got = graph_details(graph, duration_seconds=60)
        self.assertEqual(got["points"], [(0, 96), (15, 105), (45, 124), (60, 146)])
        self.assertEqual(got["summary"], {"min": 96, "avg": 110, "max": 146})
        self.assertEqual(got["series_format"], "heartRates")
        self.assertTrue(got["timing_estimated"])
        self.assertEqual(graph_points(graph), [(0, 96), (1, 105), (3, 124), (4, 146)])

    def test_timestamps_preserved_when_explicit(self):
        got = graph_details({"pointDataList": [
            {"time": 0, "heartRate": 120}, {"time": 8, "heartRate": 145},
        ]}, 120)
        self.assertEqual(got["points"], [(0, 120), (8, 145)])
        self.assertFalse(got["timing_estimated"])

    def test_user_confirmed_hrm600_is_not_given_fake_serial(self):
        info = user_confirmed_sensor("HRM600:654360")
        self.assertEqual(info["name"], "Garmin HRM 600")
        self.assertEqual(info["descriptor"], "HRM600:654360")
        self.assertEqual(info["manufacturer"], "Garmin")
        self.assertEqual(info["verified_from"], "user_confirmed")
        self.assertNotIn("serial", info)
        with TemporaryDirectory() as td:
            out = write_fit({
                "day": "2026-11-16", "duration_min": 1,
                "hr_sensor": info,
                "heart_rate_points": [(0, 95), (30, 135)],
                "heart_rate_summary": {"avg": 110, "max": 146},
                "exercises": [],
            }, Path(td) / "h.fit")
            messages = decode(out.read_bytes())
            devices = [fields for n, fields in messages if n == 23]
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0][19][1], "HRM600:654360")
            self.assertEqual(devices[0][27][1], "Garmin HRM 600")
            self.assertEqual(devices[0][2][1], 1)
            self.assertNotIn(3, devices[0])  # do not falsify a serial number
            self.assertNotIn(4, devices[0])  # unknown Garmin product ID
            session = next(f for n, f in messages if n == 18)
            self.assertEqual(session[16][1], 110)
            self.assertEqual(session[17][1], 146)

    def test_no_sensor_is_not_invented_from_a_watch_type_or_pulse(self):
        self.assertIsNone(find_hr_sensor({
            "watchType": 1, "maxHeartRate": 146, "uuid": "opaque"
        }))
        with TemporaryDirectory() as td:
            out = write_fit({
                "day": "2026-11-16", "duration_min": 1,
                "heart_rate_points": [(0, 110)], "exercises": [],
            }, Path(td) / "no_device.fit")
            self.assertFalse(any(n == 23 for n, _ in decode(out.read_bytes())))

    def test_sensor_from_api_metadata(self):
        self.assertEqual(find_hr_sensor({
            "heartRateDeviceName": "Garmin HRM 600",
            "protocol": "BLE",
        })["protocol"], "ble")
        self.assertIsNone(find_hr_sensor({"name": "random unrelated device"}))

    def test_sensor_setting_persists_and_is_translated(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            save_hr_sensor_name("HRM600:654360", root)
            self.assertEqual(load_hr_sensor_name(root), "HRM600:654360")
        self.assertEqual(translate("en", "HF-Sensor (optional):"), "HR sensor (optional):")

    def test_client_with_real_graph_fixture(self):
        client = Client(logging.getLogger("test-hr-source"))
        def request(path, **kwargs):
            if "getHeartRateGraph" in path:
                return {
                    "heartRates": [96, 110, 128, 142, 146],
                    "avgHeartRate": 110, "maxHeartRate": 146,
                }
            return [{"actionLibraryName": "Barbell Bench Press", "finishedReps": [
                {"finishedCount": 8, "time": 30, "maxHeartRate": 146,
                 "trainingInfoDetail": {"weights": [40], "uuid": "realistic-uuid"}}
            ]}]
        client.request = request
        detail = client.detail({
            "training_id": 100, "type": 5, "day": "2026-11-16",
            "duration_min": 1, "title": "Test"
        })
        self.assertEqual(len(detail["heart_rate_points"]), 5)
        self.assertEqual(detail["heart_rate_summary"]["avg"], 110)
        self.assertEqual(detail["heart_rate_summary"]["max"], 146)
        self.assertTrue(detail["heart_rate_timing_estimated"])


if __name__ == "__main__":
    unittest.main()
