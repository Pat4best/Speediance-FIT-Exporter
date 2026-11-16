"""Conservative Speediance -> Garmin FIT exercise-category mapping.

Only use exact synonyms or high-confidence matches. Garmin exercise_category
UNKNOWN is 65534, not 0: 0 means BENCH_PRESS. The per-set subtype is a Garmin
exercise-name ID *within* a category, not an arbitrary name.
Numbers verified against Garmin FIT SDK ExerciseCategory, DeadliftExerciseName,
and CardioExerciseName.
"""
import re
import unicodedata

UNKNOWN = 65534

# Key is a normalized exercise title; value = (category, category_subtype).
EXERCISES = {
    "kreuzheben mit langhantel": (8, 0),
    "langhantel kreuzheben": (8, 0),
    "kreuzheben": (8, 0),
    "barbell deadlift": (8, 0),
    "deadlift barbell": (8, 0),
    "deadlift": (8, 0),
    "romanian deadlift": (8, 23),
    "rumänisches kreuzheben": (8, 23),
    "rumaenisches kreuzheben": (8, 23),
    "sumo deadlift": (8, 15),
    "sumo kreuzheben": (8, 15),
    "dumbbell deadlift": (8, 2),
    "sternsprunge": (2, 12),
    "sternsprung": (2, 12),
    "jumping jacks": (2, 12),
    "jumping jack": (2, 12),
    "gewichtete sternsprunge": (2, 13),
    # High knees and skaters are not named subtypes in the standard Garmin
    # CARDIO list. They are intentionally left UNKNOWN instead of mislabelled.
}


def normalize(name):
    name = unicodedata.normalize("NFKD", str(name).casefold())
    name = name.replace("ß", "ss")
    name = "".join(c for c in name if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", name))


def fit_exercise(name, overrides=None):
    """Returns (category, subtype) or (65534, None) for an unknown title.

    Caller assigns a unique subtype for unknown exercises and may include a
    FIT exercise_title record to preserve its native text.
    """
    norm = normalize(name)
    if overrides and norm in overrides:
        cat, sub = overrides[norm]
        if not (0 <= int(cat) <= 65534 and 0 <= int(sub) <= 65534):
            raise ValueError("Invalid exercise mapping")
        return int(cat), int(sub)
    return EXERCISES.get(norm, (UNKNOWN, None))
