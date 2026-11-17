"""Localization/persistence checks; run without a Windows GUI."""
from pathlib import Path
import sys
import unittest
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from i18n import translate, EN
from preferences import load_language, save_language, save_export_folder, export_folder
from garmin_catalog import GARMIN_OPTIONS


class LanguageTests(unittest.TestCase):
    def test_default_is_german(self):
        with TemporaryDirectory() as directory:
            self.assertEqual(load_language(Path(directory)), "de")
        self.assertEqual(translate("de", "Anmelden"), "Anmelden")

    def test_english_translation_and_fallback(self):
        self.assertEqual(translate("en", "Anmelden"), "Sign in")
        self.assertEqual(translate("en", "Übungen zuordnen…"), "Map exercises…")
        self.assertEqual(translate("en", "● Nicht angemeldet – Anmeldung fehlgeschlagen"),
                         "● Not signed in – sign-in failed")
        self.assertEqual(translate("en", "Unknown Speediance exercise name"),
                         "Unknown Speediance exercise name")

    def test_persist_language_without_losing_export_folder(self):
        with TemporaryDirectory() as td:
            root = Path(td) / "prefs"
            folder = Path(td) / "out"
            folder.mkdir()
            save_export_folder(folder, root)
            save_language("en", root)
            self.assertEqual(load_language(root), "en")
            self.assertEqual(export_folder(root), str(folder.resolve()))
            save_language("de", root)
            self.assertEqual(load_language(root), "de")
            with self.assertRaises(ValueError):
                save_language("fr", root)

    def test_translated_garmin_labels_leave_ids_unchanged(self):
        labels = [translate("en", name) for name in GARMIN_OPTIONS]
        self.assertEqual(len(set(labels)), len(GARMIN_OPTIONS))
        for name, value in GARMIN_OPTIONS.items():
            self.assertEqual(GARMIN_OPTIONS[name], value)
        self.assertEqual(translate("en", "Kreuzheben – Langhantel"),
                         "Barbell deadlift")

    def test_required_dialog_translations(self):
        expected = [
            "Bitte zuerst anmelden.", "Trainings laden",
            "Gespeichert. Bitte vor Weitergabe selbst prüfen.",
            "Anmeldung fehlgeschlagen. Bitte E-Mail-Adresse, Passwort und Region (EU/Global) überprüfen.",
        ]
        self.assertTrue(all(x in EN for x in expected))


if __name__ == "__main__":
    unittest.main()
