"""Curated FIT exercise options verified against Garmin's public FIT SDK.

This is a *selection*, not the full Garmin exercise catalog. Category/subtype
values are from ExerciseCategory and matching XxxExerciseName classes.
"""
GARMIN_OPTIONS = {
    "Bankdrücken – Langhantel": (0, 1),
    "Bankdrücken – Kurzhantel": (0, 6),
    "Bankdrücken – Schrägbank Langhantel": (0, 8),
    "Bankdrücken – Schrägbank Kurzhantel": (0, 9),
    "Jumping Jacks / Sternsprünge": (2, 12),
    "Jumping Jacks mit Zusatzgewicht": (2, 13),
    "Kreuzheben – Langhantel": (8, 0),
    "Kreuzheben – Kurzhantel": (8, 2),
    "Kreuzheben – Rumänisch": (8, 23),
    "Kreuzheben – Sumo": (8, 15),
    "Kniebeuge – Langhantel hinten": (28, 6),
    "Kniebeuge – Langhantel vorne": (28, 8),
    "Klimmzug": (21, 38),
    "Klimmzug – neutraler Griff": (21, 43),
    "Plank / Unterarmstütz": (19, 43),
    "Rudern – Kabelzug stehend": (23, 1),
    "Rudern – Kabelzug sitzend": (23, 18),
    "Rudern – Kurzhantel": (23, 2),
    "Rudern – Kurzhantel einarmig": (23, 13),
    "Schulterdrücken – Langhantel": (24, 4),
    "Schulterdrücken – Kurzhantel über Kopf": (24, 15),
    "Schulterdrücken – Kurzhantel sitzend": (24, 17),
    "Stretch – Cat/Cow": (31, 38),
    "Stretch – Kinderhaltung": (31, 39),
    "Stretch – Hüftbeuger": (31, 45),
}


# Full bundled FIT exercise profile from the upstream Java SDK, including
# names not among the previous 25 German shortcuts. No runtime network needed.
from functools import lru_cache
import re
import unicodedata
from garmin_catalog_part1 import ROWS as _ROWS1
from garmin_catalog_part2 import ROWS as _ROWS2
from garmin_catalog_part3 import ROWS as _ROWS3
from garmin_catalog_part4 import ROWS as _ROWS4
from garmin_catalog_part5 import ROWS as _ROWS5

FULL_CATALOG = tuple(_ROWS1 + _ROWS2 + _ROWS3 + _ROWS4 + _ROWS5)
FULL_CATALOG_COUNT = len(FULL_CATALOG)

CATEGORY_TITLES = {
    category_id: key.replace("_", " ").title()
    for key, _, category_id, _ in FULL_CATALOG
}
CATEGORY_TITLES_DE = {
    0: "Bankdrücken", 1: "Wadenheben", 2: "Cardio",
    3: "Tragen", 4: "Rumpf-Rotation", 5: "Rumpf", 6: "Crunches",
    7: "Curls", 8: "Kreuzheben", 9: "Fliegende Bewegungen",
    10: "Hüftheben", 11: "Hüftstabilität", 12: "Hüftschwung",
    13: "Rückenstrecker", 14: "Seitheben", 15: "Beinbeuger",
    16: "Beinheben", 17: "Ausfallschritte", 18: "Olympisches Heben",
    19: "Planks", 20: "Plyometrie", 21: "Klimmzüge", 22: "Liegestütze",
    23: "Rudern", 24: "Schulterdrücken", 25: "Schulterstabilität",
    26: "Schulterheben", 27: "Sit-ups", 28: "Kniebeugen",
    29: "Ganzkörper", 30: "Trizepsstrecken", 31: "Aufwärmen/Dehnen",
    32: "Laufen", 33: "Radfahren", 35: "Bewegung", 36: "Posen",
    37: "Bandübungen", 38: "Battle Ropes", 39: "Crosstrainer",
    40: "Boden-Klettern", 41: "Indoor-Cycling", 42: "Indoor-Rudern",
    43: "Leiterübungen", 44: "Sandsack", 45: "Schlitten",
    46: "Vorschlaghammer", 47: "Treppensteiger", 49: "Schlingentrainer",
    50: "Reifenübungen", 52: "Laufen (Indoor)", 53: "Radfahren (Outdoor)",
}


def normalize_query(query):
    value = unicodedata.normalize("NFKD", str(query).casefold()).replace("ß", "ss")
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def category_title(category, language="de"):
    if language == "de":
        return CATEGORY_TITLES_DE.get(category, CATEGORY_TITLES.get(category, str(category)))
    return CATEGORY_TITLES.get(category, str(category))


@lru_cache(maxsize=2)
def all_options(language="de"):
    """Return only the official Garmin enum values, plus German search aliases.

    Every Garmin enum option is retained exactly once. The previous 25
    shortcuts are search keywords, not duplicate picker rows.
    """
    from i18n import translate
    aliases = {}
    for friendly, pair in GARMIN_OPTIONS.items():
        aliases.setdefault(pair, []).extend((friendly, translate(language, friendly)))
    results = []
    existing_labels = set()
    for category_key, exercise_key, cat, sub in FULL_CATALOG:
        english_name = exercise_key.replace("_", " ").title()
        cname = category_title(cat, language)
        display = "%s  ·  %s" % (english_name, cname)
        if display in existing_labels:
            display += " (%d/%d)" % (cat, sub)
        existing_labels.add(display)
        haystack = normalize_query("%s %s %s %s %s" % (
            english_name, cname, category_title(cat, "de"),
            category_key, " ".join(aliases.get((cat, sub), []))))
        results.append((display, cat, sub, haystack))
    return tuple(sorted(results, key=lambda x: (normalize_query(x[0]), x[1], x[2])))


@lru_cache(maxsize=1)
def _exact_names():
    unique = {}
    duplicate = set()
    for category_key, exercise_key, cat, sub in FULL_CATALOG:
        norm = normalize_query(exercise_key)
        if norm in unique and unique[norm] != (cat, sub):
            duplicate.add(norm)
        unique[norm] = (cat, sub)
    for key in duplicate:
        unique.pop(key, None)
    return unique


def exact_name_match(name):
    """Map an English Speediance name only if uniquely matching a Garmin enum."""
    return _exact_names().get(normalize_query(name))


def category_filters(language="de"):
    """Localized, uniquely identifiable category filter labels."""
    return tuple(
        ("%s (%d)" % (category_title(cat, language), cat), cat)
        for cat in sorted(CATEGORY_TITLES)
    )


def search_options(query="", category=None, language="de", limit=180):
    """Search tokens in any order, accent-insensitive, returning (results, total)."""
    terms = normalize_query(query).split()
    matches = [
        row for row in all_options(language)
        if (category is None or row[1] == category)
        and all(word in row[3] for word in terms)
    ]
    # Prefix matches float to top, but keep deterministic order.
    if terms:
        q = " ".join(terms)
        matches.sort(key=lambda x: (
            0 if normalize_query(x[0]).startswith(q) else
            1 if q in normalize_query(x[0]) else 2,
            normalize_query(x[0]),
        ))
    return matches[:limit], len(matches)
