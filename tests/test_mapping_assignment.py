"""One-click exercise mapping UI behavior without requiring a display server."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from mapping_editor import MappingEditor
from i18n import translate


class Variable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeButton:
    def __init__(self):
        self.state = None

    def configure(self, **kwargs):
        self.state = kwargs.get("state")


def fake_editor():
    editor = SimpleNamespace()
    editor.selected_name = "Lat Stretch"
    editor.chosen_garmin = (31, 46)
    editor.category = Variable("31")
    editor.subtype = Variable("46")
    editor.manual_mode = Variable(False)
    editor.assigned_label = Variable()
    editor.feedback = Variable()
    editor.assign_button = FakeButton()
    editor.tr = lambda text: text
    editor._label_for_codes = lambda cat, sub: (
        "Stretch Lat" if (cat, sub) == (31, 46) else "Not found"
    )
    editor.refreshed = []
    editor._refresh_left = lambda selected=None: editor.refreshed.append(selected)
    editor._update_assign_state = lambda: MappingEditor._update_assign_state(editor)
    return editor


class OneClickMappingTests(unittest.TestCase):
    def test_button_requires_both_exercise_choices(self):
        editor = fake_editor()
        MappingEditor._update_assign_state(editor)
        self.assertEqual(editor.assign_button.state, "normal")
        editor.chosen_garmin = None
        MappingEditor._update_assign_state(editor)
        self.assertEqual(editor.assign_button.state, "disabled")
        editor.chosen_garmin = (31, 46)
        editor.selected_name = None
        MappingEditor._update_assign_state(editor)
        self.assertEqual(editor.assign_button.state, "disabled")

    def test_click_maps_immediately_without_save_confirmation(self):
        editor = fake_editor()
        with patch("mapping_editor.set_override") as store, patch(
            "mapping_editor.messagebox.showinfo"
        ) as popup:
            MappingEditor.assign(editor)
        store.assert_called_once_with("Lat Stretch", 31, 46)
        popup.assert_not_called()
        self.assertEqual(editor.refreshed, ["Lat Stretch"])
        self.assertIsNone(editor.chosen_garmin)
        self.assertIn("Lat Stretch", editor.feedback.get())
        self.assertIn("Stretch Lat", editor.feedback.get())
        self.assertEqual(editor.assign_button.state, "disabled")

    def test_english_localization_of_mapping_action(self):
        self.assertEqual(translate("de", "← Zuordnen"), "← Zuordnen")
        self.assertEqual(translate("en", "← Zuordnen"), "← Map")
        self.assertIn(
            "Mapping saved",
            translate("en", "Zuordnung gespeichert: %s → %s")
        )


if __name__ == "__main__":
    unittest.main()
