"""Anonymized GM Manager history CSV regression cases (no real user data)."""
import csv
from io import StringIO
from datetime import timedelta
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gm_history_import import GMHistoryCSVError, parse_gm_history_csv, load_gm_history_file
from garmin_fit_overlay import overlay_garmin_fit
from garmin_merge import DEFAULT_PRIORITIES
from test_garmin_fit_overlay import (original_garmin_fit, values, all_message_data,
                                     speediance_executed, GARMIN_START)


COLUMNS = [
    "Date", "Workout", "Exercise", "Category", "Set", "Weight (kg)",
    "Reps", "Rest (s)", "Notes", "Session ID", "Time",
    "Session Type", "Device", "Session Duration (s)", "Session Volume (kg)",
    "Session Calories (kcal)", "Exercise ID", "Side", "Target Reps",
    "Set Volume (kg)", "Set Duration (s)",
]
SELECTED = {"day": "2020-01-02", "title": "Synthetic Workout",
            "duration_min": 3394 / 60}


def fixture_rows():
    rows = []
    def add(ex_id, name, set_no, reps, kg=None, volume=0, seconds=None, side="", notes=""):
        row = dict.fromkeys(COLUMNS, "")
        row.update({
            "Date": "2020-01-02", "Workout": "Synthetic Workout",
            "Exercise": name, "Exercise ID": str(ex_id), "Set": str(set_no),
            "Weight (kg)": "" if kg is None else str(kg),
            "Reps": str(reps), "Notes": notes,
            "Session ID": "9001", "Time": "13:00:00",
            "Session Type": "Template", "Device": "Gym Monster",
            "Session Duration (s)": "3394", "Session Volume (kg)": "6291",
            "Session Calories (kcal)": "454", "Set Volume (kg)": str(volume),
            "Set Duration (s)": "" if seconds is None else str(seconds),
            "Side": side,
        })
        rows.append(row)

    for i in (1, 2):
        add(101, "Synthetic cardio", i, 0, seconds=None, notes="timed set: 300 s")
    for i, (reps, kg, vol, dur) in enumerate([
        (10, 13, 137, 38.7), (5, 24, 120, 9.5),
        (10, 37, 370, 22.1), (10, 37, 370, 22.2),
        (10, 37, 370, 20.9), (10, 37, 370, 23.3),
    ], 1):
        add(102, "Synthetic bench", i, reps, kg, vol, dur)
    for i, (reps, kg, vol, dur) in enumerate([
        (5, 17, 170, 10.1), (10, 26, 520, 24.5),
        (10, 26, 520, 26.1), (10, 26, 520, 25.3),
        (10, 26, 520, 26.7),
    ], 1):
        add(103, "Synthetic lat exercise", i, reps, kg, vol, dur)
    for i, kg in enumerate((18, 12, 12), 1):
        add(104, "Synthetic press", i, 10, kg, 20 * kg, 25)
    for i in range(1, 4):
        add(105, "Synthetic row", i, 10, 20, 400, 24.1)
    for i in (1, 2):
        add(106, "Synthetic reverse", i, 12, 5.5, 132, 30.6)
    for ex_id in (107, 108, 109):
        for side in ("L", "R"):
            add(ex_id, "Synthetic stretch " + str(ex_id), 1, 0,
                seconds=30, side=side, notes="timed set: 30 s")
    return rows


def fixture_csv(rows=None):
    out = StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(fixture_rows() if rows is None else rows)
    return out.getvalue()


class GMHistoryImportTests(unittest.TestCase):
    def test_synthetic_27_recorded_sets_and_true_weight_not_doubled(self):
        report = parse_gm_history_csv(fixture_csv(), SELECTED)
        self.assertEqual(report["exercise_count"], 9)
        self.assertEqual(report["fit_exercise_count"], 12)
        self.assertEqual(report["set_count"], 27)
        self.assertEqual(report["strength_set_count"], 19)
        self.assertEqual(report["timed_set_count"], 8)
        self.assertEqual(report["side_rows"], 6)
        self.assertEqual(report["total_reps"], 184)
        self.assertEqual(report["duration_seconds"], 3394)
        self.assertEqual(report["unit"], "kg")
        self.assertEqual(report["exercises"][0]["sets"][0]["seconds"], 300)
        self.assertEqual(report["exercises"][0]["sets"][0]["reps"], 0)
        row = next(ex for ex in report["exercises"] if ex["name"] == "Synthetic row")
        self.assertEqual([s["weight"] for s in row["sets"]], [20, 20, 20])
        self.assertTrue(all(s["weight_already_total"] for s in row["sets"]))
        self.assertEqual(report["exercises"][-1]["name"], "Synthetic stretch 109 (rechts)")

    def test_reject_wrong_session_bad_values_and_ambiguous_recording(self):
        data = fixture_csv()
        with self.assertRaises(GMHistoryCSVError):
            parse_gm_history_csv(data, {"day": "2020-01-03", "title": "Synthetic Workout"})
        with self.assertRaises(GMHistoryCSVError):
            parse_gm_history_csv(data, {"day": "2020-01-02", "title": "Other"})
        rows = fixture_rows()
        rows[0]["Session ID"] = "9002"
        with self.assertRaisesRegex(GMHistoryCSVError, "Mehrdeutige"):
            parse_gm_history_csv(fixture_csv(rows), SELECTED)
        rows = fixture_rows()
        rows[0]["Set Volume (kg)"] = "-8"
        with self.assertRaises(GMHistoryCSVError):
            parse_gm_history_csv(fixture_csv(rows), SELECTED)
        rows = fixture_rows()
        rows[16]["Weight (kg)"] = "nan"
        with self.assertRaises(GMHistoryCSVError):
            parse_gm_history_csv(fixture_csv(rows), SELECTED)
        rows = fixture_rows()
        rows[16]["Weight (kg)"] = "40"
        # This is not rejected: aggregate volume cannot determine the actual
        # resistance; there is intentionally no automatic x2 correction.
        self.assertEqual(parse_gm_history_csv(fixture_csv(rows), SELECTED)
                         ["exercises"][4]["sets"][0]["weight"], 40)
        rows = fixture_rows()
        rows[0]["Session Volume (kg)"] = "1"
        with self.assertRaisesRegex(GMHistoryCSVError, "widersprüchlich"):
            parse_gm_history_csv(fixture_csv(rows), SELECTED)

    def test_wrong_duration_rejected(self):
        rows = fixture_rows()
        rows[0]["Session Duration (s)"] = "4000"
        with self.assertRaisesRegex(GMHistoryCSVError, "Uneinheitliche"):
            parse_gm_history_csv(fixture_csv(rows), SELECTED)

    def test_file_load_works_with_bom_and_unrelated_session(self):
        rows = fixture_rows()
        unrelated = dict(rows[0], Date="2020-01-01", Workout="Unrelated",
                         **{"Session ID": "9000"})
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / "history.csv"
            file.write_bytes(("\ufeff" + fixture_csv([unrelated] + rows)).encode("utf-8"))
            result = load_gm_history_file(file, SELECTED)
            self.assertEqual(result["set_count"], 27)

    def test_real_garmin_wire_is_preserved_and_27_set_messages_inserted(self):
        original = original_garmin_fit()
        recorded = parse_gm_history_csv(fixture_csv(), SELECTED)
        speediance = speediance_executed()
        speediance.update({
            # Reproduce the genuine account timing: the completed workout
            # began 95 seconds before the original Garmin activity. This
            # used to fail at fitwriter.py with a bare ValueError.
            "started_at": (GARMIN_START - timedelta(seconds=95)).isoformat(),
            "exercises": recorded["exercises"],
            "unit": "kg",
            "_set_source": "gm_manager_history_csv",
            "duration_seconds": 3394,
            "duration_min": 3394 / 60,
            "finished_at": None,
            "heart_rate_points": [],
            "heart_rate_summary": {},
        })
        with TemporaryDirectory() as tmp:
            out, metadata = overlay_garmin_fit(
                original, speediance, Path(tmp) / "merged.fit",
                dict(DEFAULT_PRIORITIES, duration="speediance"),
                expected_set_count=recorded["set_count"],
            )
            result = out.read_bytes()
        self.assertEqual(metadata["speediance_source"], "gm_manager_history_csv")
        self.assertTrue(metadata["set_timing_aligned_to_activity_start"])
        self.assertEqual(metadata["new_speediance_sets"], 27)
        self.assertEqual(metadata["replaced_garmin_sets"], 1)
        self.assertEqual(metadata["speediance_repetitions"], 184)
        self.assertEqual(len(values(result, 225)), 27)
        from fitwriter import stamp
        self.assertEqual(values(result, 225)[0][6][1], stamp(GARMIN_START))
        self.assertEqual(values(result, 225)[0][3][1], 0)  # timed set, not 300 reps
        self.assertEqual(values(result, 225)[1][3][1], 0)
        for index in (16, 17, 18):
            self.assertEqual(values(result, 225)[index][3][1], 10)
            self.assertAlmostEqual(values(result, 225)[index][4][1] / 16, 20)
        for glob in (20, 23, 233, 534):
            for native in all_message_data(original, glob):
                self.assertIn(native, all_message_data(result, glob))


if __name__ == "__main__":
    unittest.main()
