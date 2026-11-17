"""Regressions for the full Garmin FIT exercise search and IDs."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from garmin_catalog import (
    FULL_CATALOG, FULL_CATALOG_COUNT, all_options, category_filters,
    category_title, exact_name_match, normalize_query, search_options,
)
from exercise_mapping import fit_exercise
from i18n import translate
from garmin_localization import german_exercise_name, english_exercise_name
from preferences import load_catalog_language, save_catalog_language, load_language, save_language


class GarminCatalogTests(unittest.TestCase):
    def test_catalog_includes_all_fifty_one_sdk_exercise_classes(self):
        self.assertEqual(FULL_CATALOG_COUNT, 1838)
        self.assertGreaterEqual(len({row[2] for row in FULL_CATALOG}), 45)
        self.assertEqual(len({(row[2], row[3]) for row in FULL_CATALOG}),
                         FULL_CATALOG_COUNT)

    def test_exact_english_speediance_name_maps_automatically(self):
        self.assertEqual(exact_name_match("Barbell Bench Press"), (0, 1))
        self.assertEqual(fit_exercise("Barbell Bench Press"), (0, 1))
        self.assertEqual(fit_exercise("Biceps Stretch"), (31, 31))
        self.assertEqual(fit_exercise("Some Speediance-exclusive motion"),
                         (65534, None))

    def test_manual_mappings_have_priority(self):
        self.assertEqual(
            fit_exercise("Barbell Bench Press",
                         overrides={"barbell bench press": (8, 0)}), (8, 0))

    def test_search_finds_many_real_exercises(self):
        matches, count = search_options("press", language="en")
        self.assertGreater(count, 80)
        self.assertTrue(matches)
        self.assertLessEqual(len(matches), 180)
        self.assertTrue(all("press" in row[3] for row in matches))

    def test_search_tokens_any_order_and_accents(self):
        matches, count = search_options("bench barbell", language="en")
        self.assertGreater(count, 0)
        self.assertIn((0, 1), {(c, i) for _, c, i, _ in matches})
        aliases, alias_count = search_options("Kreuzheben", language="de")
        self.assertGreater(alias_count, 0)
        self.assertTrue(any(cat == 8 for _, cat, _, _ in aliases))
        self.assertEqual(normalize_query("Übungszuordnung"), "ubungszuordnung")

    def test_category_filter_is_real_id_not_label(self):
        matches, count = search_options("deadlift", category=8, language="en")
        self.assertTrue(count > 0)
        self.assertTrue(all(cat == 8 for _, cat, _, _ in matches))
        self.assertTrue(any(cat == 8 for _, cat in category_filters("de")))
        self.assertEqual(category_title(8, "de"), "Kreuzheben")
        self.assertEqual(category_title(8, "en"), "Deadlift")

    def test_shortcuts_and_full_values_not_modified_by_language(self):
        self.assertEqual(
            {(cat, sub) for _, cat, sub, _ in all_options("en")},
            {(cat, sub) for _, cat, sub, _ in all_options("de")},
        )
        self.assertEqual(
            translate("en", "IDs manuell bearbeiten (Expertenmodus)"),
            "Edit IDs manually (expert mode)",
        )

    def test_german_display_keeps_garmin_english_original(self):
        de = {(cat, sub): title for title, cat, sub, _ in all_options("de")}
        en = {(cat, sub): title for title, cat, sub, _ in all_options("en")}
        self.assertEqual(len(de), FULL_CATALOG_COUNT)
        self.assertEqual(len(en), FULL_CATALOG_COUNT)
        self.assertIn("Langhantel-Bankdrücken", de[(0, 1)])
        self.assertIn("Barbell Bench Press", de[(0, 1)])
        self.assertIn("Barbell Bench Press", en[(0, 1)])
        self.assertNotIn("Langhantel-Bankdrücken", en[(0, 1)])
        self.assertEqual(german_exercise_name("BICEPS_STRETCH", 31, 31),
                         "Bizepsdehnung")
        self.assertEqual(english_exercise_name("BICEPS_STRETCH"),
                         "Biceps Stretch")

    def test_bilingual_search_in_both_display_modes(self):
        for locale in ("de", "en"):
            for query in ("Bankdrücken", "bench press", "Langhantel", "barbell"):
                result, count = search_options(query, language=locale)
                self.assertGreater(count, 0, msg="%s / %s" % (locale, query))
            german, _ = search_options("Kreuzheben", category=8, language=locale)
            english, _ = search_options("deadlift", category=8, language=locale)
            self.assertTrue(any((c, sub) == (8, 0) for _, c, sub, _ in german))
            self.assertTrue(any((c, sub) == (8, 0) for _, c, sub, _ in english))

    def test_catalog_language_is_remembered_without_changing_app_language(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            root = Path(td)
            save_language("de", root)
            self.assertEqual(load_catalog_language(root), "de")
            save_catalog_language("en", root)
            self.assertEqual(load_catalog_language(root), "en")
            self.assertEqual(load_language(root), "de")
            save_catalog_language("de", root)
            self.assertEqual(load_catalog_language(root), "de")
            with self.assertRaises(ValueError):
                save_catalog_language("fr", root)

    def test_code_lookup_is_not_unknown_bench_press(self):
        # Category 0 is bench press. Unknown is 65534.
        self.assertNotEqual(fit_exercise("Nonexistent exercise"), (0, 0))


if __name__ == "__main__":
    unittest.main()
