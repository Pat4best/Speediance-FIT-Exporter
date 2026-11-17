"""Parse observed Speediance heart-rate graph values without inventing BPM.

Speediance returns at least two shapes: explicit timestamped points and
{"heartRates": [...], "avgHeartRate": ..., "maxHeartRate": ...}.
The latter has NO sample timestamps. To plot it as an activity timeline,
evenly spaced timestamps are estimated across the known workout duration.
Only the *time positions* are estimated: HR values remain actual samples.
"""
import math


def valid_bpm(raw):
    if isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(value) or not 20 <= value <= 254:
        return None
    return int(round(value))


def _unwrap_series(data):
    """Return (series, has_explicit_times, format) from recognized API shapes."""
    if isinstance(data, dict):
        for key in ("heartRates", "pointDataList", "heartRateList",
                    "heartRatePoints", "records", "list", "data"):
            if isinstance(data.get(key), list):
                return data[key], key
        for key in ("data", "result", "graph"):
            if isinstance(data.get(key), dict):
                return _unwrap_series(data[key])
        return [], "unrecognized"
    if isinstance(data, list):
        return data, "list"
    return [], "unrecognized"


def _entry_heart_rate(entry):
    """Extract measured BPM from common and compound telemetry key names.

    Never mistake max/avg/target heart-rate summaries or timestamps for an
    actual sample. Honor explicit value-type keys first.
    """
    keys = ("heartRate", "heart", "heart_rate", "hr", "bpm", "value", "rate",
            "heartRateValue", "realHeartRate", "currentHeartRate", "heartRateBpm")
    for key in keys:
        if key in entry and valid_bpm(entry[key]) is not None:
            return entry[key]
    for key, value in entry.items():
        if not isinstance(key, str):
            continue
        normalized = "".join(ch for ch in key.casefold() if ch.isalnum())
        if any(term in normalized for term in ("time", "max", "min", "avg", "average",
                                                "target", "zone", "device", "serial",
                                                "timestamp", "duration", "count")):
            continue
        if any(term in normalized for term in ("heartrate", "pulse", "bpm")):
            if valid_bpm(value) is not None:
                return value
    return None


def graph_shape(data):
    """Sanitized shape-only report to debug missing samples without HR values.

    Lists of arbitrary values could contain identifiers. We report just type
    and safe recognized field labels, NEVER example values or raw keys.
    """
    series, fmt = _unwrap_series(data)
    types = {}
    known = set()
    for item in series[:30]:
        name = type(item).__name__
        types[name] = types.get(name, 0) + 1
        if isinstance(item, dict):
            for key in item:
                if isinstance(key, str):
                    n = "".join(c for c in key.casefold() if c.isalnum())
                    if n in {
                        "heartrate", "heartratevalue", "heart", "heartbeats",
                        "heartratebpm", "currentheartrate", "realheartrate",
                        "pulse", "bpm", "value", "rate", "time", "timestamp",
                        "elapsedseconds", "elapsed", "seconds", "second",
                        "maxheartrate", "avgheartrate", "minheartrate",
                    }:
                        known.add(n)
    # Detailed type-and-status counts from exactly the known HR/time fields.
    # These counts do not expose BPM readings or timestamps.
    hr_types = {}
    hr_status = {"valid": 0, "zero": 0, "below_range": 0,
                 "above_range": 0, "nonnumeric": 0, "absent": 0}
    time_types = {}
    time_status = {"valid_seconds": 0, "negative": 0, "over_24h": 0,
                   "nonnumeric": 0, "absent": 0}
    for item in series:
        if not isinstance(item, dict):
            continue
        has_hr = "heartRate" in item
        if has_hr:
            value = item["heartRate"]
            typ = type(value).__name__
            hr_types[typ] = hr_types.get(typ, 0) + 1
            try:
                v = float(value) if not isinstance(value, (dict, list, bool)) else math.nan
            except (ValueError, TypeError, OverflowError):
                v = math.nan
            if not math.isfinite(v):
                hr_status["nonnumeric"] += 1
            elif v == 0:
                hr_status["zero"] += 1
            elif v < 20:
                hr_status["below_range"] += 1
            elif v > 254:
                hr_status["above_range"] += 1
            else:
                hr_status["valid"] += 1
        else:
            hr_status["absent"] += 1
        if "time" not in item:
            time_status["absent"] += 1
        else:
            value = item["time"]
            typ = type(value).__name__
            time_types[typ] = time_types.get(typ, 0) + 1
            try:
                v = float(value) if not isinstance(value, (dict, list, bool)) else math.nan
            except (ValueError, TypeError, OverflowError):
                v = math.nan
            if not math.isfinite(v):
                time_status["nonnumeric"] += 1
            elif v < 0:
                time_status["negative"] += 1
            elif v > 86400:
                time_status["over_24h"] += 1
            else:
                time_status["valid_seconds"] += 1
    return {
        "format": fmt,
        "items": len(series),
        "sample_types": types,
        "known_fields": sorted(known),
        "dict_field_count": max(
            (len(item) for item in series[:30] if isinstance(item, dict)),
            default=0,
        ),
        "heartRate_types": hr_types,
        "heartRate_status": hr_status,
        "time_types": time_types,
        "time_status": time_status,
    }


def _numeric_time(value):
    if isinstance(value, (dict, list, bool)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _clock_mode(times, duration, start_epoch=None, start_day_seconds=None):
    """Determine the time unit once per series, not independently per sample.

    Return (label, value_to_elapsed_seconds, timing_estimated).
    Unix seconds/ms/us are compared to the known session clock. If the clock
    differs substantially, the source is only rebased for the same session
    when its measured span is plausible. Such an alignment is explicit and
    never described as an exact absolute timestamp.
    """
    if not times:
        return "no_time_values", None, True
    first, last = min(times), max(times)
    if first < 0:
        return "invalid_time", None, False
    if duration is None or duration <= 0:
        # graph_points() is also used standalone for small elapsed time series.
        if last <= 86400:
            return "elapsed_seconds", lambda v: v, False
        return "duration_required_for_long_times", None, False
    span = last - first
    reference = _numeric_time(start_epoch)
    def epoch_mode(scale, label):
        if reference is not None:
            # The raw source clock is usable when it covers this workout.
            offsets = [v / scale - reference for v in times]
            aligned = sum(-120 <= sec <= duration + 120 for sec in offsets)
            if aligned >= max(1, int(0.8 * len(times))):
                return label, lambda v: v / scale - reference, False
            # Some Speediance API routes use a different local/UTC convention.
            # Rebase only a plausible *same-day* measurement; make the
            # estimated placement explicit to users.
            if (abs(first / scale - reference) <= 24 * 3600
                    and span / scale <= duration * 1.5 + 120):
                return label + "_rebased", lambda v: (v - first) / scale, True
            return label + "_clock_mismatch", None, False
        if span / scale <= duration * 1.5 + 120:
            return label + "_rebased", lambda v: (v - first) / scale, True
        return label + "_unknown_clock", None, False

    if 946684800000000 <= first <= 4102444800000000:
        return epoch_mode(1_000_000, "unix_microseconds")
    if 946684800000 <= first <= 4102444800000:
        return epoch_mode(1000, "unix_milliseconds")
    if 946684800 <= first <= 4102444800:
        return epoch_mode(1, "unix_seconds")

    if last <= duration + 120:
        return "elapsed_seconds", lambda v: v, False
    # A native second-of-day clock can align exactly with the local start.
    local = _numeric_time(start_day_seconds)
    if last <= 86400 and local is not None:
        aligned = sum(-120 <= v - local <= duration + 120 for v in times)
        if aligned >= max(1, int(0.8 * len(times))) and first > duration + 120:
            return "seconds_since_midnight", lambda v: v - local, False
    if last <= 1000 * (duration + 120) and last > duration + 120:
        return "elapsed_milliseconds", lambda v: v / 1000, False

    # Some sources report milliseconds since midnight instead of an epoch.
    # Compare to the local activity clock before falling back to rebasing.
    if last <= 86_400_000 and span / 1000 <= duration * 1.5 + 120:
        local = _numeric_time(start_day_seconds)
        if local is not None:
            offsets = [v / 1000 - local for v in times]
            aligned = sum(-120 <= sec <= duration + 120 for sec in offsets)
            if aligned >= max(1, int(0.8 * len(times))):
                return "milliseconds_since_midnight", lambda v: v / 1000 - local, False

    # Unknown origin but high-resolution duration looks like milliseconds.
    # Do not stretch/compress the real sampling intervals to fill the workout.
    if 86400 < last < 946684800 and 5 <= span / 1000 <= duration * 1.5 + 120:
        return "relative_milliseconds_rebased", lambda v: (v - first) / 1000, True
    if 86400 < last < 946684800 and 5 <= span <= duration * 1.5 + 120:
        return "relative_seconds_rebased", lambda v: v - first, True
    return "unrecognized_time_scale", None, False


def graph_details(data, duration_seconds=None, start_epoch=None,
                  start_day_seconds=None):
    """Return true BPM measurements on a single, classified time axis.

    Supported time fields: elapsed seconds, elapsed ms, Unix s/ms/us and
    milliseconds since local midnight. Unknown-origin clocks are rebased only
    if their measured span is plausible and are reported as estimated timing.
    A sampling time is never guessed from a value unrelated to the session.
    """
    series, series_format = _unwrap_series(data)
    duration = _numeric_time(duration_seconds)
    if duration is not None and duration <= 0:
        duration = None
    extracted = []
    clock_values = []
    for i, entry in enumerate(series):
        if isinstance(entry, dict):
            bpm = valid_bpm(_entry_heart_rate(entry))
            raw_time = next((entry[key] for key in (
                "elapsedSeconds", "elapsed", "seconds", "time", "second"
            ) if key in entry), None)
        else:
            bpm, raw_time = valid_bpm(entry), None
        if bpm is None:
            continue
        numeric_time = _numeric_time(raw_time)
        extracted.append((i, bpm, numeric_time))
        if numeric_time is not None:
            clock_values.append(numeric_time)

    mode, convert, rebased = _clock_mode(
        clock_values, duration, start_epoch, start_day_seconds
    )
    if not clock_values:
        mode = "uniform_positions_without_timestamps"
        rebased = True
    samples = {}
    skipped_time = 0
    for index, bpm, raw in extracted:
        if raw is not None:
            if convert is None:
                skipped_time += 1
                continue
            second = convert(raw)
        else:
            rebased = True
            if duration is None:
                second = index
            elif len(series) > 1:
                second = index * duration / (len(series) - 1)
            else:
                second = duration / 2
        if not math.isfinite(second) or second < -1 or second > 86400:
            skipped_time += 1
            continue
        sec = int(round(max(0, second)))
        # Actual readings outside the activity aren't moved into its window.
        if duration is not None and sec > duration + 1:
            skipped_time += 1
            continue
        samples[sec] = bpm

    summary = {}
    if isinstance(data, dict):
        for source, target in (("minHeartRate", "min"),
                               ("avgHeartRate", "avg"),
                               ("maxHeartRate", "max")):
            value = valid_bpm(data.get(source))
            if value is not None:
                summary[target] = value
    return {
        "points": sorted(samples.items()),
        "summary": summary,
        "timing_estimated": rebased,
        "time_mode": mode,
        "skipped_time_points": skipped_time,
        "series_format": series_format,
        "raw_sample_count": len(series),
    }


def graph_points(data):
    """Backward-compatible observed samples; no duration gives index seconds."""
    return graph_details(data)["points"]
