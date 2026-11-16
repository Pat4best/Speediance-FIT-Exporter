"""Regression tests: login must not steal the phone's Speediance session by default."""
import json
import logging
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from speediance_api import Client, LOGIN_CLIENT_TYPES
from preferences import load_login_client_type, save_login_client_type


class FakeResponse:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit):
        return json.dumps({"code": 0, "data": self.data}).encode("utf-8")


class LoginClientTests(unittest.TestCase):
    def test_login_uses_bike_for_both_calls_but_not_normal_get(self):
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            if "verifyIdentity" in request.full_url:
                return FakeResponse({"isExist": True, "hasPwd": True})
            if "byPass" in request.full_url:
                return FakeResponse({"token": "test-token", "appUserId": "test-user",
                                     "unit": 0})
            return FakeResponse([])

        client = Client(logging.getLogger("test"))
        with patch("urllib.request.urlopen", fake_urlopen):
            client.login("example@test.invalid", "test-password")
            client.request("/api/app/v5/trainingCalendar/monthNew?date=2026-11")
        self.assertEqual(len(requests), 3)
        for request in requests[:2]:
            self.assertEqual(request.get_header("App_type"), "BIKE")
            self.assertEqual(request.get_header("Versioncode"), "1")
        self.assertEqual(requests[2].get_header("App_type"), "SOFTWARE")
        self.assertEqual(requests[2].get_header("Versioncode"), "41000")
        self.assertEqual(requests[2].get_header("Token"), "test-token")

    def test_other_slots(self):
        self.assertEqual(LOGIN_CLIENT_TYPES["nano"], ("NANO", "1"))
        self.assertEqual(LOGIN_CLIENT_TYPES["phone"], ("SOFTWARE", "41000"))
        with self.assertRaises(ValueError):
            Client(logging.getLogger("test"), login_client_type="gym-monster")

    def test_slot_preference_default_and_override(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            self.assertEqual(load_login_client_type(root), "bike")
            save_login_client_type("nano", root)
            self.assertEqual(load_login_client_type(root), "nano")
            with self.assertRaises(ValueError):
                save_login_client_type("something", root)


if __name__ == "__main__":
    unittest.main()
