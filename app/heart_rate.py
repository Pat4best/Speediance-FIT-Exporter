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


def graph_details(data, duration_seconds=None):
    """Return samples, true summary values, source format and timeline provenance.

    If a list lacks time/seconds fields, samples are placed evenly over the
    workout's duration. This does not interpolate heart-rate measurements.
    """
    series, series_format = _unwrap_series(data)
    duration = None
    try:
        duration = float(duration_seconds)
        if not math.isfinite(duration) or duration <= 0:
            duration = None
    except (TypeError, ValueError):
        pass
    estimates = False
    samples = {}
    count = len(series)
    for index, entry in enumerate(series):
        if isinstance(entry, dict):
            raw = next((entry.get(key) for key in (
                "heartRate", "heart", "heart_rate", "hr", "bpm", "value", "rate"
            ) if key in entry), None)
            elapsed = next((entry[key] for key in (
                "elapsedSeconds", "elapsed", "seconds", "time", "second"
            ) if key in entry), None)
        else:
            raw, elapsed = entry, None
        bpm = valid_bpm(raw)
        if bpm is None:
            continue
        if elapsed is None:
            estimates = True
            if duration is not None and count > 1:
                elapsed = index * duration / (count - 1)
            elif duration is not None:
                elapsed = duration / 2
            else:
                elapsed = index
        try:
            sec = float(elapsed)
        except (ValueError, TypeError):
            continue
        if not math.isfinite(sec) or not 0 <= sec <= 24 * 60 * 60:
            continue
        samples[int(round(sec))] = bpm
    # Retain actual Speediance server statistics when present. A set maximum
    # is not a sample and must never be used to synthesize a graph.
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
        "timing_estimated": estimates,
        "series_format": series_format,
        "raw_sample_count": count,
    }


def graph_points(data):
    """Backward-compatible observed samples; no duration gives index seconds."""
    return graph_details(data)["points"]
