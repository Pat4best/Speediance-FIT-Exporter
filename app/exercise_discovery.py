"""Fetch exercise names from selected Speediance workouts before opening the mapping UI.

Keep the detail requests independent of FIT exports. This module does not store
credentials or personally identifying account details.
"""


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
            exercises = detail.get("exercises", [])
            if not isinstance(exercises, list):
                raise ValueError("Expected exercise list")
            names = []
            for exercise in exercises:
                if not isinstance(exercise, dict):
                    continue
                name = exercise.get("name")
                if not isinstance(name, str):
                    continue
                name = name.strip()
                if name:
                    names.append(name)
            if not names:
                raise ValueError("Empty exercise list")
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
