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



def _series(raw):
    """Read either a list or the comma-separated telemetry form."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.split(",")
    if not isinstance(raw, (tuple, list)):
        raw = [raw]
    result = []
    for value in raw:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if 0 <= number < 10000:
            result.append(number)
    return result


def set_weight(detail, raw_set=None):
    """Return (weight_in_account_units, already_total_or_unilateral).

    When Speediance provides per-side telemetry, it is more reliable than
    'weights' (which can be derived force telemetry). Sum max-left+max-right
    for dual cables, do NOT apply an additional name-based x2.
    """
    detail = detail if isinstance(detail, dict) else {}
    raw_set = raw_set if isinstance(raw_set, dict) else {}
    left = _series(detail.get("leftWeights"))
    right = _series(detail.get("rightWeights"))
    try:
        side = int(raw_set.get("leftRight", detail.get("leftRight", 0)) or 0)
    except (ValueError, TypeError):
        side = 0
    if side == 1 and left:
        return max(left), True
    if side == 2 and right:
        return max(right), True
    if left and right:
        return max(left) + max(right), True
    if left or right:
        return max(left or right), side in (1, 2)
    fallback = _series(detail.get("weights"))
    return (max(fallback) if fallback else 0), False
