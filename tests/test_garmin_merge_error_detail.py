"""Garmin merge UI retains safe, specific errors instead of swallowing them.

No Tk display, private tokens, original Garmin files or network necessary.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from garmin_dialog import GarminMergeDialog
from garmin_fit_overlay import GarminOverlayError
from garmin_fit_reader import GarminFitError


class Entry:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class GarminMergeFailureDiagnosticsTests(unittest.TestCase):
    def fake_dialog(self):
        api = SimpleNamespace(
            download_activity_fit=lambda activity_id: b"synthetic-fit-source"
        )
        return SimpleNamespace(
            app=SimpleNamespace(
                busy=False,
                client=object(),
                tr=lambda text: text,
                # Synchronous fake worker to surface the original exception.
                run_job=lambda job, done: job(),
            ),
            source_verified="api",
            source_choice=Entry("api"),
            local_fit_bytes=None,
            local_file_path=Entry(""),
            garmin_client=api,
            match_combo=SimpleNamespace(current=lambda: 0),
            candidates=[{"id": 17}],
            _selected_priorities=lambda: {"start": "garmin"},
            workout={"day": "2026-11-13", "training_id": 4567},
            gm_manager_import=None,
            gm_history_import=None,
        )

    def run_with_overlay_error(self, error):
        with TemporaryDirectory() as folder:
            dest = str(Path(folder) / "merged.fit")
            with patch("garmin_dialog.filedialog.asksaveasfilename",
                       return_value=dest), patch(
                "garmin_dialog.save_merge_priorities"
            ), patch(
                "garmin_dialog.details_or_history",
                return_value={
                    "exercises": [{"name": "Recorded",
                                   "sets": [{"reps": 10, "weight": 20,
                                             "seconds": 25}]}]
                },
            ), patch("garmin_dialog.overlay_garmin_fit",
                     side_effect=error):
                GarminMergeDialog.save_merge(self.fake_dialog())

    def test_specific_overlay_error_is_visible_not_generic_valueerror(self):
        with self.assertRaisesRegex(
            GarminOverlayError, "genau einer Sitzung"
        ):
            self.run_with_overlay_error(GarminOverlayError(
                "Nur Garmin-Einzelaktivitäten mit genau einer Sitzung unterstützt"
            ))

    def test_validating_original_fit_keeps_source_owned_detail(self):
        with self.assertRaisesRegex(GarminFitError,
                                    "FIT-Header-Prüfsumme"):
            self.run_with_overlay_error(
                GarminFitError("FIT-Header-Prüfsumme fehlerhaft")
            )

    def test_untrusted_valueerror_stays_privacy_safe(self):
        with self.assertRaisesRegex(GarminOverlayError,
                                    "Ungültige FIT-Satzdaten"):
            self.run_with_overlay_error(ValueError(
                "Secret user info should not be shown"
            ))


if __name__ == "__main__":
    unittest.main()
