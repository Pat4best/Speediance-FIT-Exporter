"""RC release metadata and symmetric German/English documentation checks.

Tests use no network, user account, personal FIT files or Windows APIs.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RC = "0.1.35-rc.2"
LANGUAGES = ("de", "en")
DOC_NAMES = {
    "README.md", "quick-start.md", "user-guide.md",
    "known-limitations.md", "changelog.md", "development.md",
    "rc-checklist.md", "third-party.md",
    "publication-checklist.md",
}


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class RCReleaseChecks(unittest.TestCase):
    def test_version_and_release_landing_pages_agree(self):
        for path in (
            "app/main.py", "README.md", "CHANGELOG.md",
            "docs/de/README.md", "docs/en/README.md",
            "docs/de/user-guide.md", "docs/en/user-guide.md",
            "docs/de/changelog.md", "docs/en/changelog.md",
        ):
            with self.subTest(path=path):
                self.assertIn(RC, read(path))

    def test_docs_are_mirrored_without_stale_root_documents(self):
        docs_root = ROOT / "docs"
        self.assertEqual(
            {entry.name for entry in docs_root.iterdir()},
            set(LANGUAGES),
        )
        for lang in LANGUAGES:
            filenames = {
                path.name for path in (docs_root / lang).iterdir()
                if path.is_file()
            }
            self.assertEqual(filenames, DOC_NAMES)
            for filename in DOC_NAMES:
                self.assertTrue(
                    (docs_root / lang / filename).is_file()
                )
                if filename == "README.md":
                    continue
                opposite = "en" if lang == "de" else "de"
                self.assertIn(
                    f"../{opposite}/{filename}",
                    read(f"docs/{lang}/{filename}"),
                    f"Missing language-switch link in {lang}/{filename}",
                )

    def test_english_user_manual_is_complete_not_a_quick_start(self):
        for lang in LANGUAGES:
            manual = read(f"docs/{lang}/user-guide.md")
            sections = re.findall(r"^## (\d+)\.", manual, re.MULTILINE)
            self.assertEqual(
                sections, [str(n) for n in range(1, 11)],
                f"Manual {lang} does not have all ten numbered chapters",
            )
            self.assertGreater(len(manual), 10000)
            self.assertIn("Garmin Personal API", manual)
            self.assertIn("Windows Credential Manager" if lang == "en"
                          else "Windows-Anmeldeinformationsmanager", manual)
            self.assertIn("Intensity Minutes" if lang == "en"
                          else "Intensitätsminuten", manual)

    def test_all_active_relative_markdown_links_resolve(self):
        # Check top-level entry points and every maintained DE/EN document.
        sources = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
        for lang in LANGUAGES:
            sources.extend((ROOT / "docs" / lang).glob("*.md"))
        for file in sources:
            body = file.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                relative = target.split("#", 1)[0].split("?", 1)[0]
                if not relative:
                    continue
                with self.subTest(source=str(file), target=target):
                    self.assertTrue(
                        (file.parent / relative).is_file(),
                        "Broken relative Markdown link",
                    )

    def test_installer_includes_all_documents_in_both_languages(self):
        script = read("installer.nsi")
        self.assertIn('VIProductVersion "0.1.35.2"', script)
        for lang in LANGUAGES:
            self.assertIn(f'SetOutPath "$INSTDIR\\docs\\{lang}"', script)
            for filename in DOC_NAMES:
                relative = f"docs\\{lang}\\{filename}"
                self.assertIn(f'File "{relative}"', script)
                self.assertIn(f'Delete "$INSTDIR\\{relative}"', script)
        self.assertIn("Benutzerhandbuch (Deutsch).lnk", script)
        self.assertIn("User Manual (English).lnk", script)
        self.assertIn('RMDir "$INSTDIR\\docs\\de"', script)
        self.assertIn('RMDir "$INSTDIR\\docs\\en"', script)
        self.assertNotIn('RMDir /r "$LOCALAPPDATA\\SpeedianceFITExporter"', script)

    def test_actions_artifact_bundles_both_documentation_trees(self):
        workflow = read(".github/workflows/windows-installer.yml")
        self.assertIn(
            "SpeedianceFITExporter-Windows-Setup-" + RC,
            workflow,
        )
        self.assertIn("docs/de/", workflow)
        self.assertIn("docs/en/", workflow)

    def test_known_intensity_limit_stays_disclosed_in_both_languages(self):
        self.assertIn(
            "keine neuen Intensitätsminuten",
            read("README.md"),
        )
        self.assertIn(
            "not add any new Intensity Minutes",
            read("docs/en/user-guide.md"),
        )
        self.assertIn(
            "nicht zusätzlich dem Garmin-Wochenkonto",
            read("docs/de/user-guide.md"),
        )


if __name__ == "__main__":
    unittest.main()
