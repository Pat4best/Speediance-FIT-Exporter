"""Opt-in, user-confirmed GM Manager custom-workout import for Garmin FIT merges.

The GM Manager JSON contains prescriptions, not a completed-session log.
Only use it after the person explicitly confirms that this selected
workout's prescribed repetitions/weights match what was actually done.
Never claim the imported values were verified as Speediance telemetry.
"""
import json
import math
from pathlib import Path

MAX_IMPORT_BYTES = 2_000_000
MAX_EXERCISES = 200
MAX_SETS = 500


class GMManagerImportError(ValueError):
    pass


def _count(value, field, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise GMManagerImportError("Ungültiger GM-Manager-Wert: " + field)
    return value


def _weight(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value < 4095:
        raise GMManagerImportError("Ungültiges GM-Manager-Gewicht")
    return float(value)


def parse_gm_manager_json(raw, workout):
    """Parse the selected named workout; do not infer performedness or set times.

    Returns the nine-or-fewer exercise lists as FIT-friendly records and an
    independently counted source summary. None of the exported metadata
    overrides the activity clock or original Garmin sensor readings.
    """
    if isinstance(raw, bytes):
        if len(raw) > MAX_IMPORT_BYTES:
            raise GMManagerImportError("GM-Manager-Datei ist zu groß")
        try:
            raw = raw.decode("utf-8-sig")
        except UnicodeError:
            raise GMManagerImportError("GM-Manager-Datei ist kein UTF-8") from None
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise GMManagerImportError("Ungültige GM-Manager-Datei")
    try:
        doc = json.loads(raw)
    except (ValueError, TypeError):
        raise GMManagerImportError("GM-Manager-Datei enthält kein gültiges JSON") from None
    if not isinstance(doc, dict) or doc.get("app") != "gmvoice-speediance" or doc.get("kind") != "custom-workouts" or doc.get("version") != 1:
        raise GMManagerImportError("Keine unterstützte GM-Manager-Trainingsdatei")
    unit_code = doc.get("unit")
    if type(unit_code) is not int or unit_code not in (0, 1):
        raise GMManagerImportError("Unbekannte Gewichtseinheit im GM Manager")
    unit = "kg" if unit_code == 0 else "lb"
    workouts = doc.get("workouts")
    if not isinstance(workouts, list) or not 1 <= len(workouts) <= 500:
        raise GMManagerImportError("Keine gültigen Trainings im GM-Manager-Export")
    expected = " ".join(str(workout.get("title") or "").casefold().split())
    matched = [w for w in workouts if isinstance(w, dict)
               and " ".join(str(w.get("name") or "").casefold().split()) == expected]
    if len(matched) != 1:
        raise GMManagerImportError("Der GM-Manager-Trainingsname passt nicht eindeutig zum ausgewählten Speediance-Training")
    entries = matched[0].get("exercises")
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_EXERCISES:
        raise GMManagerImportError("GM-Manager-Übungen fehlen oder sind ungültig")
    exercises = []
    total_sets = strength_sets = timed_sets = 0
    for ex in entries:
        if not isinstance(ex, dict):
            raise GMManagerImportError("Ungültiger Übungseintrag")
        group_id = ex.get("groupId")
        if type(group_id) is not int or not 0 < group_id < 2**63:
            raise GMManagerImportError("Ungültige GM-Manager-Übungskennung")
        kind = ex.get("kind")
        if kind not in ("strength", "cardio", "mat"):
            raise GMManagerImportError("Nicht unterstützte GM-Manager-Übungsart")
        source_sets = ex.get("sets")
        if not isinstance(source_sets, list) or not 1 <= len(source_sets) <= MAX_SETS:
            raise GMManagerImportError("Übung hat keine gültigen Sätze")
        parsed_sets = []
        for row in source_sets:
            if not isinstance(row, dict):
                raise GMManagerImportError("Ungültiger GM-Manager-Satz")
            reps = _count(row.get("reps"), "reps", 65534)
            _count(row.get("rest"), "rest", 86400)
            if kind == "strength":
                weight = _weight(row.get("weight"))
                if reps <= 0 or row.get("unit") != "reps":
                    raise GMManagerImportError("Kraftsatz hat keine gültigen Wiederholungen")
                parsed_sets.append({
                    "reps": reps, "weight": weight,
                    # Do not multiply user-confirmed displayed weights.
                    "weight_already_total": True,
                })
                strength_sets += 1
            else:
                if "weight" in row and row.get("weight") not in (None, 0, 0.0):
                    raise GMManagerImportError("Zeitbasierter Satz enthält unerwartetes Gewicht")
                if reps <= 0:
                    raise GMManagerImportError("Zeitbasierter Satz enthält keine Dauer")
                parsed_sets.append({
                    "reps": 0, "seconds": reps, "weight": 0,
                    "weight_already_total": True,
                })
                timed_sets += 1
            total_sets += 1
            if total_sets > MAX_SETS:
                raise GMManagerImportError("Zu viele GM-Manager-Sätze")
        exercises.append({
            "name": "GM Manager " + kind + " " + str(group_id),
            "group_id": group_id,
            "kind": kind,
            "completion_method": 1 if kind == "strength" else 0,
            "sets": parsed_sets,
        })
    return {
        "exercises": exercises,
        "unit": unit,
        "exercise_count": len(exercises),
        "set_count": total_sets,
        "strength_set_count": strength_sets,
        "timed_set_count": timed_sets,
        "title": matched[0]["name"],
    }


def load_gm_manager_file(path, workout):
    file = Path(path)
    try:
        if not 0 < file.stat().st_size <= MAX_IMPORT_BYTES:
            raise GMManagerImportError("GM-Manager-Datei ist leer oder zu groß")
        return parse_gm_manager_json(file.read_bytes(), workout)
    except (OSError, UnicodeError):
        raise GMManagerImportError("GM-Manager-Datei konnte nicht gelesen werden") from None


def resolve_exercise_names(client, parsed):
    """Optionally lookup public library names; keep explicit group IDs if unavailable.

    This lookup does not fetch per-session data. Never log raw group identifiers.
    """
    result = []
    for item in parsed["exercises"]:
        ex = dict(item)
        group_id = item["group_id"]
        try:
            data = client.request(
                "/api/app/actionLibraryGroup/%d?isDisplay=1" % group_id,
                allow_error=True
            )
        except Exception:
            data = None
        if isinstance(data, dict):
            for key in ("actionLibraryName", "name", "title", "groupName"):
                name = data.get(key)
                if isinstance(name, str) and 0 < len(name.strip()) <= 180:
                    ex["name"] = name.strip()
                    break
        result.append(ex)
    return result
