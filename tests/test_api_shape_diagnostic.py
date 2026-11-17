"""Selected-session schema diagnostics never expose API field values."""
from datetime import date
from io import StringIO
import logging
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from api_shape_diagnostic import response_structure, structural_log
from speediance_api import Client, completed_record_reference


class ShapeDiagnosticTests(unittest.TestCase):
    def test_nested_fields_visible_without_values(self):
        response = {
            "id": 892342, "trainingId": 12222, "title": "PRIVATE-NAME",
            "startTime": "PRIVATE-DATE",
            "actionLibrary": [{"actionLibraryName": "PRIVATE-EXERCISE",
                               "finishedReps": [{"finishedCount": 12,
                                                 "trainingInfoDetail": {"weights": [25.0]}}]}],
        }
        result = structural_log(response)
        self.assertIn("$.actionLibrary[].finishedReps[].trainingInfoDetail.weights", result)
        self.assertIn("array[1]", result)
        for secret in ("892342", "12222", "PRIVATE-NAME", "PRIVATE-DATE",
                       "PRIVATE-EXERCISE", "25.0"):
            self.assertNotIn(secret, result)

    def test_arbitrary_keys_and_oversized_payload_are_bounded(self):
        response = {"PRIVATE@EMAIL": "SECRET", "user-1234567": "SECRET",
                    **{"validField%d" % i: [i] for i in range(500)}}
        rows = response_structure(response)
        self.assertLessEqual(len(rows), 160)
        self.assertNotIn("PRIVATE@EMAIL", str(rows))
        self.assertNotIn("user-1234567", str(rows))
        self.assertNotIn("SECRET", str(rows))

    def test_selected_history_is_retained_as_structure_only(self):
        logger = logging.getLogger("test-selected-shape")
        client = Client(logger)
        record = {
            "trainingId": 12345, "id": 67890, "title": "SENSITIVE-TITLE",
            "startTime": "2026-11-16 18:00:00",
            "trainingTime": 3394, "calorie": 454, "type": 5,
            "performedActions": [{"finishedReps": [{"finishedCount": 10}]}],
        }
        client.request = lambda path, **kwargs: (
            [record] if "userTrainingDataRecord" in path else []
        )
        sessions = client.list_workouts(date(2026, 11, 16), date(2026, 11, 16))
        self.assertEqual(len(sessions), 1)
        schema = sessions[0]["_history_response_shape"]
        self.assertIn("$.performedActions[].finishedReps[].finishedCount", schema)
        self.assertNotIn("67890", schema)
        self.assertNotIn("SENSITIVE-TITLE", schema)
        self.assertNotIn("3394", schema)

    def test_completed_record_reference_extracted_without_logging_id(self):
        session = {
            "trainingId": 12345, "id": 999,
            "title": "PRIVATE-WORKOUT",
            "startTime": "2026-11-16 18:00:00",
            "trainingTime": 3394, "calorie": 454, "type": 5,
            "aiEntryPageReq": {
                "pageType": 3,
                "trainingParam": {
                    "recordId": "PRIVATE-RECORD-UUID-123",
                    "completedTrainingPageType": 2,
                },
            },
        }
        self.assertEqual(completed_record_reference(session),
                         "PRIVATE-RECORD-UUID-123")
        client = Client(logging.getLogger("test-completed-record-memory"))
        client.request = lambda path, **kwargs: (
            [session] if "userTrainingDataRecord" in path else []
        )
        rows = client.list_workouts(date(2026, 11, 16), date(2026, 11, 16))
        self.assertEqual(rows[0]["_completed_record_id"], "PRIVATE-RECORD-UUID-123")
        self.assertNotIn("PRIVATE-RECORD", rows[0]["_history_response_shape"])
        self.assertIsNone(completed_record_reference({"aiEntryPageReq": {
            "trainingParam": {"recordId": "../not-valid"}}}))
        self.assertIsNone(completed_record_reference({"aiEntryPageReq": {
            "trainingParam": {"recordId": 12345}}}))

    def test_completed_record_probe_get_only_and_logs_no_values(self):
        logger = logging.getLogger("test-completed-ref-probe")
        logger.setLevel(logging.INFO)
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)
        try:
            client = Client(logger)
            requests = []
            def api(path, **kwargs):
                requests.append((path, kwargs))
                if path.endswith("/PRIVATE-RECORD-UUID-123") and "cttTrainingInfoDetail" in path:
                    return [{"actionLibraryName": "HIDDEN EXERCISE",
                             "finishedReps": [{"finishedCount": 10,
                                               "trainingInfoDetail": {"weights": [30]}}]}]
                return None
            client.request = api
            report = client.diagnose_workout({
                "training_id": 91827364,
                "type": 5,
                "_history_response_shape": structural_log({"id": 7777}),
                "_completed_record_id": "PRIVATE-RECORD-UUID-123",
            })
            self.assertEqual(report["checked"], 8)
            self.assertEqual(report["record_ref_checked"], 8)
            self.assertEqual(report["record_ref_responses_with_completed_sets"], 2)
            self.assertEqual(len(requests), 16)
            self.assertTrue(all("allow_error" in kw for _, kw in requests))
            self.assertIn("Selected recordId detail route=", stream.getvalue())
            self.assertIn("finishedReps[].finishedCount", stream.getvalue())
            for secret in ("PRIVATE-RECORD-UUID-123", "HIDDEN EXERCISE", "91827364", '"weights": [30]'):
                self.assertNotIn(secret, stream.getvalue())
        finally:
            logger.removeHandler(handler)

    def test_detail_diagnosis_inspects_wrapped_response_without_leaking_values(self):
        log = logging.getLogger("test-only-selected-api-shape")
        log.setLevel(logging.INFO)
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        log.addHandler(handler)
        try:
            client = Client(log)
            calls = []
            def api(path, **kwargs):
                calls.append(path)
                if "courseTrainingInfoDetail" in path:
                    return {"exerciseList": [{
                        "actionLibraryName": "SECRET EXERCISE",
                        "finishedReps": [{"finishedCount": 8,
                                          "trainingInfoDetail": {"weights": [42]}}]
                    }]}
                return None
            client.request = api
            workout = {"training_id": 12345678, "type": 2,
                       "_history_response_shape": structural_log({
                           "id": 87654321, "trainingId": 12345678,
                           "title": "SECRET TITLE",
                       })}
            report = client.diagnose_workout(workout)
            self.assertEqual(report["checked"], 8)
            self.assertEqual(report["responses_with_completed_sets"], 2)
            content = stream.getvalue()
            self.assertIn("exerciseList[].finishedReps[].finishedCount", content)
            self.assertIn("version=40304", content)
            self.assertNotIn("SECRET", content)
            self.assertNotIn("12345678", content)
            self.assertNotIn("87654321", content)
            self.assertEqual(len(calls), 8)
        finally:
            log.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
