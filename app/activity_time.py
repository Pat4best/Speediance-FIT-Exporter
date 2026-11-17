"""One activity clock for FIT writing and Speediance HR timestamp alignment.

Calendar sessions may provide a finish time; completed history rows may also
have an actual startTime. Never silently shift dates between endpoints.
"""
from datetime import datetime, timedelta


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError):
        return None


def activity_bounds(workout):
    """Return (start_datetime, end_datetime, duration_seconds).

    The FIT file writer and HR importer use this exact same clock. When the
    history provides a start time, it is preferred over inferring it by
    subtracting the duration from calendar finishTime.
    """
    sets = [
        s for exercise in (workout.get("exercises") or [])
        for s in (exercise.get("sets") or [])
    ]
    measured_seconds = sum(max(0, int(float(s.get("seconds") or 0))) for s in sets)
    configured_seconds = int(float(workout.get("duration_min") or 0) * 60)
    duration = max(60, configured_seconds, measured_seconds, len(sets))
    start = _parse_datetime(workout.get("started_at"))
    if start is None:
        end = _parse_datetime(workout.get("finished_at"))
        if end is not None:
            start = end - timedelta(seconds=duration)
        else:
            start = datetime.fromisoformat(str(workout["day"])[:10] + "T12:00:00")
    return start, start + timedelta(seconds=duration), duration
