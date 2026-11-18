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
from completed_workout_cache import save_detail_cache
from exercise_discovery import cached_workout_names, names_from_completed_detail
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
        state = SimpleNamespace(
            app=SimpleNamespace(busy=False, client=SimpleNamespace()),
            workout={"training_id": 2, "day": "2026-11-13"},
            gm_history_import=None, winfo_exists=lambda: True,
        )
        state.wait_window = lambda editor: None
        calls = []
        state.grab_set = lambda: calls.append("restored")
        with patch("garmin_dialog.cached_workout_names", return_value=[]), patch(
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
            state, names=["Mat L", "Seated Row"]
        )

    def test_main_no_selection_shows_global_mappings_without_api(self):
        state = SimpleNamespace(
            busy=False,
            table=SimpleNamespace(selection=lambda: ()),
            client=SimpleNamespace(
                detail=lambda _: self.fail("No API access needed")),
        )
        with patch("main.observed_names", return_value=["Old GMC Exercise"]), \
             patch("main.MappingEditor") as editor:
            App.manage_mappings(state)
        editor.assert_called_once_with(
            state, names=["Old GMC Exercise"])

    def test_selected_training_uses_only_its_cached_exercises(self):
        selected = {"training_id": 777, "day": "2026-11-13"}
        state = SimpleNamespace(
            busy=False,
            sessions=[selected],
            table=SimpleNamespace(selection=lambda: ("0",)),
            client=SimpleNamespace(
                detail=lambda _: self.fail("Must not call Speediance")),
            status=SimpleNamespace(set=lambda value: None),
            tr=lambda text: text,
        )
        with patch("main.cached_workout_names",
                   return_value=["Actual Selected Movement"]), \
             patch("main.observed_names",
                   return_value=["Old GMC Exercise"]), \
             patch("main.MappingEditor") as editor, \
             patch("main.messagebox.showinfo") as alert:
            App.manage_mappings(state)
        editor.assert_called_once_with(
            state, names=["Actual Selected Movement"])
        alert.assert_not_called()

    def test_no_cached_exercises_does_not_show_old_gmc_mappings(self):
        selected = {"training_id": 777, "day": "2026-11-13"}
        state = SimpleNamespace(
            busy=False, sessions=[selected],
            table=SimpleNamespace(selection=lambda: ("0",)),
            client=SimpleNamespace(),
            status=SimpleNamespace(set=lambda value: None),
            tr=lambda text: text,
        )
        with patch("main.cached_workout_names", return_value=[]), \
             patch("main.observed_names",
                   return_value=["Old GMC Exercise"]), \
             patch("main.MappingEditor") as editor, \
             patch("main.messagebox.showinfo") as alert:
            App.manage_mappings(state)
        editor.assert_called_once_with(state, names=[])
        alert.assert_called_once()

    def test_account_and_workout_cache_isolates_mapping_names(self):
        with TemporaryDirectory() as root:
            first = {"training_id": 111, "day": "2026-11-13"}
            second = {"training_id": 222, "day": "2026-11-13"}
            client = SimpleNamespace(
                cache_dir=root, host="euapi.speediance.com", user_id="u1",
            )
            self.assertTrue(save_detail_cache(
                root, client.host, client.user_id, first,
                {"exercises": [
                    {"name": "Selected Exercise",
                     "sets": [{"reps": 10, "weight": 20, "seconds": 30}]},
                    {"name": "Unperformed Plan", "sets": []},
                ]},
            ))
            self.assertTrue(save_detail_cache(
                root, client.host, client.user_id, second,
                {"exercises": [
                    {"name": "GMC Exercise",
                     "sets": [{"reps": 8, "weight": 30, "seconds": 21}]},
                ]},
            ))
            self.assertEqual(cached_workout_names(client, first),
                             ["Selected Exercise"])
            self.assertEqual(cached_workout_names(client, second),
                             ["GMC Exercise"])
            self.assertEqual(cached_workout_names(
                SimpleNamespace(cache_dir=root, host=client.host,
                                user_id="other-account"), first), [])
            self.assertEqual(cached_workout_names(
                SimpleNamespace(cache_dir=root, host="api2.speediance.com",
                                user_id=client.user_id), first), [])


    def test_merge_editor_uses_selected_workout_cache_not_global_pool(self):
        state = SimpleNamespace(
            app=SimpleNamespace(busy=False, client=SimpleNamespace()),
            workout={"training_id": 4, "day": "2026-11-13"},
            gm_history_import=None,
            winfo_exists=lambda: True,
            grab_set=lambda: None,
            wait_window=lambda editor: None,
        )
        with patch("garmin_dialog.cached_workout_names",
                   return_value=["Selected Exercise"]), \
             patch("garmin_dialog.observed_names",
                   return_value=["Old GMC Exercise"]), \
             patch("garmin_dialog.MappingEditor") as editor:
            GarminMergeDialog._open_mapping_editor(state)
        editor.assert_called_once_with(
            state, names=["Selected Exercise"])

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
