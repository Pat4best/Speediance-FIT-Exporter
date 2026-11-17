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



def _representative_recorded_load(values):
    """Most frequently recorded *positive* resistance; latest wins a tie.

    The previous max() incorrectly treated an initial higher plan setting
    (e.g. 26 kg) as the executed load even after lowering it (e.g. 20 kg).
    Zero after disengaging is not an executed resistance. Speediance records
    arrays per rep and sometimes contains setup values before lifting.
    """
    positives = [v for v in values if v > 0]
    if not positives:
        return 0.0
    # Ignore small recording noise; allow 0.1 kg precision.
    readings = [round(v, 1) for v in positives]
    counts = {reading: readings.count(reading) for reading in set(readings)}
    highest = max(counts.values())
    return next(v for v in reversed(readings) if counts[v] == highest)


def _recorded_status(left, right, fallback, source):
    """Shape diagnostics only. Never log workout values or user metadata."""
    active = left + right if source in ("both_sides", "single_side") else fallback
    positives = [round(v, 1) for v in active if v > 0]
    return {
        "source": source,
        "readings": len(positives),
        "different_loads": len(set(positives)),
        "contains_changes": len(set(positives)) > 1,
    }


def measured_set_weight(detail, raw_set=None):
    """Return (resistance, already_total, shape) for recorded strength sets.

    Per-side arrays in trainingInfoDetail always take precedence over generic
    force/weight telemetry, and always reflect the particular completed set.
    No prescribed/template weights are ever read here.
    """
    detail = detail if isinstance(detail, dict) else {}
    raw_set = raw_set if isinstance(raw_set, dict) else {}
    left = _series(detail.get("leftWeights"))
    right = _series(detail.get("rightWeights"))
    try:
        side = int(raw_set.get("leftRight", detail.get("leftRight", 0)) or 0)
    except (ValueError, TypeError):
        side = 0
    fallback = _series(detail.get("weights"))
    if side == 1 and left:
        return (_representative_recorded_load(left), True,
                _recorded_status(left, [], fallback, "single_side"))
    if side == 2 and right:
        return (_representative_recorded_load(right), True,
                _recorded_status([], right, fallback, "single_side"))
    if left and right:
        return (_representative_recorded_load(left) +
                _representative_recorded_load(right), True,
                _recorded_status(left, right, fallback, "both_sides"))
    if left or right:
        return (_representative_recorded_load(left or right), side in (1, 2),
                _recorded_status(left or right, [], fallback, "single_side"))
    if fallback:
        return (_representative_recorded_load(fallback), False,
                _recorded_status([], [], fallback, "generic_telemetry"))
    return 0.0, False, _recorded_status([], [], [], "missing")


def set_weight(detail, raw_set=None):
    """Backward compatible result of the recorded-set resistance selector."""
    load, already_total, _ = measured_set_weight(detail, raw_set)
    return load, already_total
