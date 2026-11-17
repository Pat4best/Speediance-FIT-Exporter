"""Parse real (never estimated) Speediance heart-rate graph samples.

The public community API notes identify /api/app/watchMsg/getHeartRateGraph
with a session UUID; graph rows have e.g. {"time": 2, "heartRate": 150}.
Missing/zero heart-rate samples are holes, not measurements.
"""
import math


def valid_bpm(raw):
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(value) or not 20 <= value <= 254:
        return None
    return int(round(value))


def graph_points(data):
    """Return ordered (elapsed_seconds, bpm), valid real observations only."""
    if isinstance(data, dict):
        for key in ("pointDataList", "heartRateList", "data", "list", "records"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = next((v for v in data.values() if isinstance(v, list)), [])
    if not isinstance(data, list):
        return []
    points = {}
    for index, entry in enumerate(data):
        if isinstance(entry, dict):
            value = next(
                (entry.get(key) for key in ("heartRate", "heart", "hr", "bpm", "value", "rate")
                 if key in entry),
                None,
            )
            second = entry.get("time", entry.get("seconds", index))
        else:
            value = entry
            second = index
        bpm = valid_bpm(value)
        if bpm is None:
            continue
        try:
            second = float(second)
        except (ValueError, TypeError):
            continue
        if not math.isfinite(second) or second < 0 or second > 24 * 60 * 60:
            continue
        points[int(round(second))] = bpm
    return sorted(points.items())
