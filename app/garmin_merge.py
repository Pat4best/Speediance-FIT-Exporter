"""Explicit, local Speediance/Garmin data-priority selection for a new FIT.

No online Garmin activity is changed. The generated FIT is a new synthetic
activity containing Speediance strength sets with genuine source measurements.
"""
from datetime import timezone
import math

from activity_time import activity_bounds

SOURCES = ("garmin", "speediance")
DEFAULT_PRIORITIES = {
    "heart_curve": "garmin",
    "heart_avg": "garmin",
    "heart_max": "garmin",
    "calories": "garmin",
    "start": "garmin",
    "duration": "garmin",
}

PRIORITY_LABELS = (
    ("heart_curve", "Herzfrequenzverlauf"),
    ("heart_avg", "Durchschnittspuls"),
    ("heart_max", "Maximalpuls"),
    ("calories", "Kalorien"),
    ("start", "Trainingsbeginn"),
    ("duration", "Trainingsdauer"),
)


def check_priorities(priorities):
    result = dict(DEFAULT_PRIORITIES)
    if priorities is not None:
        if not isinstance(priorities, dict):
            raise ValueError("Invalid merge priority configuration")
        for key, value in priorities.items():
            if key not in result or value not in SOURCES:
                raise ValueError("Invalid merge priority")
            result[key] = value
    return result


def _valid_hr(value):
    try:
        f = float(value)
    except (ValueError, TypeError):
        return None
    return int(round(f)) if math.isfinite(f) and 20 <= f <= 254 else None


def _positive_float(value):
    try:
        f = float(value)
    except (ValueError, TypeError):
        return None
    return f if math.isfinite(f) and f > 0 else None


def _absolute_start(value):
    return value.astimezone(timezone.utc) if value.tzinfo else value.astimezone().astimezone(timezone.utc)


def _resolve(field, speediance_value, garmin_value, priorities, validator):
    source = priorities[field]
    primary = garmin_value if source == "garmin" else speediance_value
    backup = speediance_value if source == "garmin" else garmin_value
    primary = validator(primary)
    if primary is not None:
        return primary
    return validator(backup)


def merge_workout(speediance, garmin, priorities=None):
    """Return (new_workout, meta). Strictly use real measured sample readings.

    Values retain their absolute source timestamps and are transformed onto
    the chosen activity clock. On matching seconds, the preferred source wins;
    holes may be filled by true measurements from the secondary source.
    """
    priorities = check_priorities(priorities)
    speed_start, _, speed_duration = activity_bounds(speediance)
    speed_start = _absolute_start(speed_start)
    garmin_start = garmin.get("start")
    if garmin_start is not None:
        garmin_start = _absolute_start(garmin_start)
    selected_start = (garmin_start if priorities["start"] == "garmin" and garmin_start is not None
                      else speed_start)
    if priorities["start"] == "speediance":
        selected_start = speed_start
    garmin_duration = _positive_float(garmin.get("duration_seconds"))
    duration = _resolve("duration", speed_duration, garmin_duration,
                        priorities, _positive_float)
    if duration is None:
        duration = speed_duration
    duration = int(round(duration))

    # The input Speediance points are seconds from the ORIGINAL Speediance
    # start, not from the merged session start. Likewise Garmin points are
    # already absolute UTC timestamps.
    speed_samples = {}
    for entry in speediance.get("heart_rate_points") or []:
        try:
            elapsed, bpm = entry
            elapsed = float(elapsed)
            bpm = _valid_hr(bpm)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(elapsed) or elapsed < 0 or bpm is None:
            continue
        ts = speed_start.timestamp() + elapsed
        speed_samples[int(round(ts - selected_start.timestamp()))] = bpm
    garmin_samples = {}
    for record in garmin.get("heart_rate_records") or []:
        try:
            ts, bpm = record
            bpm = _valid_hr(bpm)
            if bpm is not None:
                sec = int(round(_absolute_start(ts).timestamp()
                                - selected_start.timestamp()))
                garmin_samples[sec] = bpm
        except (TypeError, ValueError, AttributeError):
            continue

    if priorities["heart_curve"] == "garmin":
        main, backup = garmin_samples, speed_samples
    else:
        main, backup = speed_samples, garmin_samples
    all_samples = {
        sec: bpm for sec, bpm in backup.items()
        if 0 <= sec <= duration
    }
    all_samples.update({
        sec: bpm for sec, bpm in main.items()
        if 0 <= sec <= duration
    })
    series = sorted(all_samples.items())

    s_summary = speediance.get("heart_rate_summary") or {}
    g_summary = garmin.get("heart_rate_summary") or {}
    summary = {}
    for key, output in (("heart_avg", "avg"), ("heart_max", "max")):
        selected = _resolve(key, s_summary.get(output), g_summary.get(output),
                            priorities, _valid_hr)
        if selected is not None:
            summary[output] = selected

    def valid_calories(x):
        v = _positive_float(x)
        return int(round(v)) if v is not None else None
    calories = _resolve("calories", speediance.get("calories"),
                        garmin.get("calories"), priorities, valid_calories)

    output = dict(speediance)
    output["started_at"] = selected_start.isoformat()
    output["duration_seconds"] = duration
    # The current FIT writer receives completed reps, load and duration, but
    # *never* original per-set start timestamps. This is equally true for
    # recorded Speediance API/cache data and imported GM Manager rows.
    # Their SET positions are always estimates, unlike genuine Speediance
    # heart-rate observations, which were transformed independently above.
    #
    # When the watch started AFTER Speediance, a negative estimated SET
    # offset cannot be represented within the Garmin-selected activity.
    # Anchor only these estimated SETs to the watch's start. Leave actual
    # Garmin and Speediance HR samples at their measured absolute times.
    raw_strength_offset = int(round(
        speed_start.timestamp() - selected_start.timestamp()
    ))
    aligned_set_timing = raw_strength_offset < 0
    output["strength_start_offset"] = max(0, raw_strength_offset)
    output["set_timing_aligned_to_activity_start"] = aligned_set_timing
    output["duration_min"] = duration / 60
    output["finished_at"] = None
    output["heart_rate_points"] = series
    output["heart_rate_summary"] = summary
    output["heart_rate_timing_estimated"] = False
    # Respect the selected summary source, even if a different source has
    # a larger individual measured peak in the mixed fallback curve.
    output["respect_hr_summary"] = True
    if calories is not None:
        output["calories"] = calories
    # A Speediance sensor descriptor does not describe the source of Garmin
    # HR records. Avoid creating misleading device info on mixed exports.
    output["hr_sensor"] = None
    return output, {
        "selected": dict(priorities),
        "samples": len(series),
        "garmin_samples": len(garmin_samples),
        "speediance_samples": len(speed_samples),
        "out_of_window_samples": sum(
            not 0 <= sec <= duration
            for sec in (set(garmin_samples) | set(speed_samples))
        ),
        "start": selected_start,
        "duration_seconds": duration,
        "set_timing_aligned_to_activity_start": aligned_set_timing,
        "set_timing_original_offset_seconds": raw_strength_offset,
    }
