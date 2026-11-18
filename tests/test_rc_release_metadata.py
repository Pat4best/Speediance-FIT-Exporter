"""RC packaging/documentation checks, no Windows installation or account needed."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RCReleaseChecks(unittest.TestCase):
    def test_version_and_release_notes_agree(self):
        code = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        for text in (code, readme, changelog):
            self.assertIn("0.1.35-rc.1", text)

    def test_installer_includes_user_guides_and_removes_on_uninstall(self):
        script = (ROOT / "installer.nsi").read_text(encoding="utf-8")
        self.assertIn('VIProductVersion "0.1.35.1"', script)
        for relative in (
            "README.md", "CHANGELOG.md",
            "docs\\Benutzerhandbuch.md", "docs\\Quick_Start_EN.md",
            "docs\\Bekannte_Einschraenkungen.md",
            "docs\\Drittquellen.md",
        ):
            # NSIS installation and uninstallation are intentionally
            # explicit, to avoid deleting user settings or workout caches.
            self.assertIn("File \"" + relative + "\"", script)
            file_path = ROOT / relative.replace("\\", "/")
            self.assertTrue(file_path.is_file(), relative)
            self.assertIn("Delete \"$INSTDIR", script)
        self.assertIn('SetOutPath "$INSTDIR\\docs"', script)
        self.assertNotIn('RMDir /r "$LOCALAPPDATA\\SpeedianceFITExporter"', script)

    def test_ci_artifact_contains_docs(self):
        workflow = (ROOT / ".github" / "workflows" /
                    "windows-installer.yml").read_text(encoding="utf-8")
        self.assertIn(
            "SpeedianceFITExporter-Windows-Setup-0.1.35-rc.1",
            workflow,
        )
        for path in ("README.md", "CHANGELOG.md",
                     "docs/Benutzerhandbuch.md",
                     "docs/Quick_Start_EN.md"):
            self.assertIn(path, workflow)

    def test_no_unqualified_claim_for_intensity_minutes(self):
        docs = (
            (ROOT / "README.md").read_text(encoding="utf-8")
            + (ROOT / "docs" / "Benutzerhandbuch.md")
              .read_text(encoding="utf-8")
        )
        self.assertRegex(docs, r"Intensitätsminuten")
        self.assertRegex(docs, r"Garmin")
        self.assertIn("nicht dem Garmin-Wochenkonto", docs)


if __name__ == "__main__":
    unittest.main()
