"""Fetch exercise names from selected Speediance workouts before opening the mapping UI.

Keep the detail requests independent of FIT exports. This module does not store
credentials or personally identifying account details.
"""


def names_from_completed_detail(detail):
    """Only names of actually recorded exercises, never unrelated mappings.

    Per-workout completed detail is keyed by account, host and training ID
    in the existing cache. Do not use a global observed-name pool here.
    """
    found = []
    seen = set()
    if not isinstance(detail, dict):
        return found
    for exercise in detail.get("exercises") or ():
        if not isinstance(exercise, dict) or not exercise.get("sets"):
            continue
        name = exercise.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            found.append(name)
    return found


def cached_workout_names(client, workout):
    """Read a selected workout's *verified completed-set* cache only.

    Never fall back to names from other sessions. A missing cache returns
    an empty list; it is not evidence that the workout has no exercises.
    """
    if client is None or not isinstance(workout, dict):
        return []
    from completed_workout_cache import load_detail_cache
    cached = load_detail_cache(
        getattr(client, "cache_dir", None),
        getattr(client, "host", None),
        getattr(client, "user_id", None),
        workout,
    )
    return names_from_completed_detail(cached)


def discover_names(client, workouts, logger=None):
    """Return (unique_names_in_workout_order, failed_workout_count).

    The caller runs this off the Tk main thread and saves names only after the
    read has completed. A single unavailable workout won't hide the others.
    """
    found = []
    seen = set()
    failures = 0
    for workout in workouts:
        try:
            detail = client.detail(workout)
            names = names_from_completed_detail(detail)
            if not names:
                raise ValueError("No completed exercise names")
            for name in names:
                key = name.casefold()
                if key not in seen:
                    seen.add(key)
                    found.append(name)
        except Exception as exc:
            failures += 1
            if logger is not None:
                # Do not include workout data, API responses or personal details.
                logger.warning("Mapping: training detail unavailable (%s)", type(exc).__name__)
    return found, failures
