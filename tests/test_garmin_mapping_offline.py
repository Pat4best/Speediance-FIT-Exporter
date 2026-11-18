"""Manual mapping must be usable without working Speediance detail endpoints.

These tests run without a graphical display, cloud token, or private CSV.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from garmin_dialog import GarminMergeDialog, mapping_names_for_merge
from main import App
from exercise_mapping import fit_exercise
from preferences import observed_names, remember_names, saved_mappings, set_override
from tempfile import TemporaryDirectory


class OfflineGarminMappingTests(unittest.TestCase):
    def test_csv_exercise_names_are_available_without_api(self):
        history = {"exercises": [
            {"name": "Seated Row", "sets": [{"reps": 10, "weight": 20}]},
            {"name": "Lat Stretch (links)", "sets": [{"seconds": 30}]},
            {"name": "Lat Stretch (rechts)", "sets": [{"seconds": 30}]},
            {"name": "Seated Row", "sets": [{"reps": 10, "weight": 20}]},
        ]}
        names = mapping_names_for_merge(history, ["Old Mapping", "Seated Row"])
        self.assertEqual(names, ["Lat Stretch (links)",
                                 "Lat Stretch (rechts)", "Old Mapping",
                                 "Seated Row"])

    def test_missing_csv_and_cache_do_not_block_mapping_window(self):
        state = SimpleNamespace(app=SimpleNamespace(busy=False),
                                gm_history_import=None, winfo_exists=lambda: True)
        state.wait_window = lambda editor: None
        calls = []
        state.grab_set = lambda: calls.append("restored")
        with patch("garmin_dialog.observed_names", return_value=[]), patch(
                "garmin_dialog.MappingEditor") as editor, patch(
                "garmin_dialog.messagebox.showinfo") as popup:
            GarminMergeDialog._open_mapping_editor(state)
        editor.assert_called_once_with(state, names=[])
        self.assertEqual(calls, ["restored"])
        popup.assert_not_called()

    def test_csv_names_reach_modal_editor_without_cloud_request(self):
        history = {"exercises": [{"name": "Seated Row"}, {"name": "Mat L"}]}
        state = SimpleNamespace(app=SimpleNamespace(busy=False),
                                gm_history_import=history,
                                winfo_exists=lambda: True,
                                grab_set=lambda: None,
                                wait_window=lambda editor: None)
        with patch("garmin_dialog.observed_names", return_value=["Old Mapping"]), \
             patch("garmin_dialog.MappingEditor") as editor:
            GarminMergeDialog._open_mapping_editor(state)
        editor.assert_called_once_with(
            state, names=["Mat L", "Old Mapping", "Seated Row"]
        )

    def test_main_mapping_button_does_not_contact_speediance(self):
        state = SimpleNamespace(busy=False, client=SimpleNamespace(
            detail=lambda _: self.fail("No API access needed")))
        with patch("main.observed_names", return_value=[]), \
             patch("main.MappingEditor") as editor:
            App.manage_mappings(state)
        editor.assert_called_once_with(state, names=[])

    def test_saved_names_and_fitted_codes_survive_offline(self):
        with TemporaryDirectory() as folder:
            remember_names(["Seated Row", "Lat Stretch (links)"], root=folder)
            self.assertEqual(observed_names(folder),
                             ["Lat Stretch (links)", "Seated Row"])
            set_override("Seated Row", 8, 0, root=folder)
            loaded = saved_mappings(folder)
            self.assertEqual(fit_exercise("Seated Row", overrides=loaded),
                             (8, 0))


if __name__ == "__main__":
    unittest.main()
