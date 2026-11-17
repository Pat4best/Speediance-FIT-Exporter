"""Account-isolated local cache of *completed* Speediance workout details.

Speediance sometimes exposes finished sessions in its calendar but refuses
subsequent read-only completed-set requests (e.g. app code 100041). The first
successful completed-set download is therefore reusable for later Garmin
merges, with no need for an exported Speediance FIT.

Only data actually returned by Speediance (recorded reps, weight, HR) is
cached. Never persist login credentials, sensor identifiers or response UUIDs.
Files remain in the current OS user's local application directory.
"""
from hashlib import sha256
import json
import os
from pathlib import Path

SCHEMA = 1
MAX_BYTES = 1_500_000


def _path(root, host, user_id, workout):
    if not root or not host or not user_id:
        return None
    try:
        training_id = int(workout["training_id"])
    except (ValueError, TypeError, KeyError):
        return None
    if training_id <= 0:
        return None
    identity = "\0".join((str(host), str(user_id), str(training_id)))
    digest = sha256(identity.encode("utf-8")).hexdigest()
    return Path(root) / (digest + ".json")


def _sanitized_exercises(raw):
    if not isinstance(raw, list) or not 0 < len(raw) <= 300:
        return None
    result = []
    for ex in raw:
        if not isinstance(ex, dict):
            return None
        name = ex.get("name")
        sets = ex.get("sets")
        if not isinstance(name, str) or not name.strip() or len(name) > 180:
            return None
        if not isinstance(sets, list) or len(sets) > 300:
            return None
        clean_sets = []
        for row in sets:
            if not isinstance(row, dict):
                return None
            clean_set = {}
            for key in ("reps", "weight", "seconds"):
                try:
                    value = float(row.get(key) or 0)
                except (TypeError, ValueError, OverflowError):
                    return None
                if not (0 <= value <= 1_000_000):
                    return None
                clean_set[key] = value
            clean_set["weight_already_total"] = bool(row.get("weight_already_total"))
            clean_sets.append(clean_set)
        method = ex.get("completion_method")
        if method is not None:
            try:
                method = int(method)
            except (ValueError, TypeError):
                method = None
        result.append({
            "name": name,
            "sets": clean_sets,
            "completion_method": method,
        })
    if not any(ex["sets"] for ex in result):
        return None
    return result


def _sanitized_hr(raw):
    if not isinstance(raw, list) or len(raw) > 100_000:
        return None
    points = []
    for pair in raw:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            return None
        try:
            elapsed, bpm = int(pair[0]), int(pair[1])
        except (TypeError, ValueError, OverflowError):
            return None
        if not 0 <= elapsed <= 86_400 or not 20 <= bpm <= 254:
            return None
        points.append([elapsed, bpm])
    return points


def _normalized(data):
    if not isinstance(data, dict):
        return None
    exercises = _sanitized_exercises(data.get("exercises"))
    hr = _sanitized_hr(data.get("heart_rate_points") or [])
    if exercises is None or hr is None:
        return None
    summary = {}
    candidate = data.get("heart_rate_summary") or {}
    if not isinstance(candidate, dict):
        return None
    for key in ("avg", "min", "max"):
        try:
            value = int(candidate.get(key))
        except (ValueError, TypeError, OverflowError):
            continue
        if 20 <= value <= 254:
            summary[key] = value
    return {
        "exercises": exercises,
        "heart_rate_points": hr,
        "heart_rate_summary": summary,
        "heart_rate_timing_estimated": bool(
            data.get("heart_rate_timing_estimated")
        ),
    }


def save_detail_cache(root, host, user_id, workout, detail):
    """Save only verified completed-set observations, atomically.

    A cache failure is optional and must never invalidate a live export.
    """
    path = _path(root, host, user_id, workout)
    payload = _normalized(detail)
    if path is None or payload is None:
        return False
    body = json.dumps({
        "schema": SCHEMA,
        "day": str(workout.get("day") or "")[:10],
        "data": payload,
    }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_BYTES:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    try:
        # Files are private to the current OS account; on Windows the
        # containing LocalAppData directory has a per-user ACL.
        fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(body)
        os.replace(temporary, path)
        return True
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def load_detail_cache(root, host, user_id, workout):
    """Read only matching day/account/workout details, never a template."""
    path = _path(root, host, user_id, workout)
    if path is None:
        return None
    try:
        if not 0 < path.stat().st_size <= MAX_BYTES:
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return None
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        return None
    if record.get("day") != str(workout.get("day") or "")[:10]:
        return None
    return _normalized(record.get("data"))
