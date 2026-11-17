"""Conservative per-exercise weight scaling for two-handle Speediance sets.

Some Speediance exercises report weight for ONE cable/handle while Garmin
Connect displays TOTAL weight. Never apply this globally: only clearly named
dual-handle movements default to x2. Users can override either direction.
"""
from exercise_mapping import normalize

# Deliberately narrow. Not every exercise using two hands has two independent
# weight stacks. Keep one-handle and barbell movements at x1 by default.
DUAL_HANDLE_TERMS = (
    "dual handle",
    "dual grip",
    "double handle",
    "two handle",
    "two grip",
    "2 handles",
)


def suggested_weight_multiplier(exercise_name):
    name = normalize(exercise_name)
    # Check whole phrases, not substrings (e.g. "individual handles").
    padded = " " + name + " "
    return 2 if any(" " + term + " " in padded for term in DUAL_HANDLE_TERMS) else 1


def weight_multiplier_for(exercise_name, overrides=None):
    """Return integer 1 or 2 for the specific Speediance exercise name.

    Explicit local setting wins over the suggested dual-handle default.
    """
    key = normalize(exercise_name)
    if overrides and key in overrides:
        value = overrides[key]
        if type(value) is not int or value not in (1, 2):
            raise ValueError("Weight multiplier must be 1 or 2")
        return value
    return suggested_weight_multiplier(exercise_name)
