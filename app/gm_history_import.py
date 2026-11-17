"""Offline import of completed GM Manager workout-history CSV.

This is a workout *history* export, not the GM Manager custom-workout
template JSON. Read only the exact date/name session selected by the user.
Import real per-set duration and repetition data without inventing start
timestamps or per-sample power/heart-rate telemetry.
"""
import csv
from collections import OrderedDict
from io import StringIO
import math
from pathlib import Path
import re

MAX_BYTES = 3_000_000
MAX_ROWS = 3000
MAX_SESSION_SETS = 500
REQUIRED = {
    "Date", "Workout", "Session ID", "Exercise", "Exercise ID",
    "Set", "Weight (kg)", "Reps", "Notes", "Session Duration (s)",
    "Set Duration (s)", "Set Volume (kg)",
}
TIMED = re.compile(r"timed set:\s*([0-9]+(?:\.[0-9]+)?)\s*s\b", re.I)
SAFE_NOTE_SIDE = {"L": "links", "R": "rechts"}


class GMHistoryCSVError(ValueError):
    pass


def _number(value, field, maximum, *, nullable=False):
    if value is None or str(value).strip() == "":
        if nullable:
            return None
        raise GMHistoryCSVError("Pflichtwert fehlt: " + field)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise GMHistoryCSVError("Ungültiger CSV-Wert: " + field) from None
    if not math.isfinite(number) or not 0 <= number <= maximum:
        raise GMHistoryCSVError("CSV-Wert außerhalb des erlaubten Bereichs: " + field)
    return number


def _int(value, field, maximum):
    n = _number(value, field, maximum)
    if not n.is_integer():
        raise GMHistoryCSVError("Ungültige ganze Zahl: " + field)
    return int(n)


def _name(s):
    return " ".join(str(s or "").casefold().split())


def parse_gm_history_csv(payload, selected):
    if isinstance(payload, bytes):
        if len(payload) > MAX_BYTES:
            raise GMHistoryCSVError("CSV-Datei zu groß")
        try:
            payload = payload.decode("utf-8-sig")
        except UnicodeError:
            raise GMHistoryCSVError("CSV-Datei ist nicht UTF-8") from None
    if not isinstance(payload, str) or len(payload.encode("utf-8")) > MAX_BYTES:
        raise GMHistoryCSVError("Ungültige CSV-Datei")
    try:
        reader = csv.DictReader(StringIO(payload, newline=""))
        if reader.fieldnames is None or not REQUIRED.issubset(reader.fieldnames):
            raise GMHistoryCSVError("Keine unterstützte GM-Manager-Workout-History-CSV")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise GMHistoryCSVError("CSV-Datei enthält zu viele Zeilen")
            if None in row:
                raise GMHistoryCSVError("Ungültiges CSV-Zeilenformat")
            if any((str(x or "").strip() for x in row.values())):
                rows.append(row)
    except csv.Error:
        raise GMHistoryCSVError("Ungültiges CSV-Format") from None

    expected_day = str(selected.get("day") or "")[:10]
    expected_name = _name(selected.get("title"))
    matching = [r for r in rows
                if str(r["Date"]).strip() == expected_day
                and _name(r["Workout"]) == expected_name]
    if not matching:
        raise GMHistoryCSVError(
            "Kein eindeutiges Training mit passendem Datum und Namen in der CSV gefunden"
        )
    session_ids = {r["Session ID"].strip() for r in matching}
    if len(session_ids) != 1 or not next(iter(session_ids)):
        raise GMHistoryCSVError("Mehrdeutige Trainingseinheiten in der History-CSV")
    if len(matching) > MAX_SESSION_SETS:
        raise GMHistoryCSVError("Zu viele Satzzeilen für ein Training")

    # The export repeats session metrics on each set row. Require agreement
    # rather than silently using an unrelated session summary.
    session_duration = {_int(r["Session Duration (s)"], "Session Duration (s)", 86400)
                        for r in matching}
    if len(session_duration) != 1 or next(iter(session_duration)) < 60:
        raise GMHistoryCSVError("Uneinheitliche Trainingsdauer in der CSV")
    duration = next(iter(session_duration))
    original_duration = float(selected.get("duration_seconds") or
                              float(selected.get("duration_min") or 0) * 60)
    if original_duration > 0 and abs(duration - original_duration) > 180:
        raise GMHistoryCSVError(
            "Trainingsdauer der CSV passt nicht zur ausgewählten Speediance-Einheit"
        )

    exercises = OrderedDict()
    strength_count = timed_count = bilateral_rows = 0
    guessed_duration = 0
    last_set_by_exercise = {}
    total_reps = 0
    volume_total = 0.0
    for row in matching:
        exercise_id = row["Exercise ID"].strip()
        name = row["Exercise"].strip()
        if not name or not exercise_id:
            raise GMHistoryCSVError("Übungsname oder Kennung fehlt")
        set_num = _int(row["Set"], "Set", 500)
        if set_num < 1:
            raise GMHistoryCSVError("Ungültige Satznummer")
        side = row.get("Side", "").strip().upper()
        if side not in ("", "L", "R"):
            raise GMHistoryCSVError("Unbekannte Satzseite in der CSV")
        # Preserve left/right as separate FIT sets and distinguish their
        # titles, rather than throwing away half of the timed movements.
        display_name = name + (" (" + SAFE_NOTE_SIDE[side] + ")" if side else "")
        key = (exercise_id, side)
        if key not in exercises:
            exercises[key] = {"name": display_name, "group_id": exercise_id,
                              "sets": [], "completion_method": None}
        elif exercises[key]["name"] != display_name:
            raise GMHistoryCSVError("Widersprüchlicher Übungsname in der CSV")
        previous = last_set_by_exercise.get(key, 0)
        if set_num <= previous:
            raise GMHistoryCSVError("Satznummern müssen je Übung aufsteigend sein")
        last_set_by_exercise[key] = set_num

        reps = _int(row["Reps"], "Reps", 65534)
        displayed = _number(row.get("Weight (kg)"), "Weight (kg)", 4095,
                            nullable=True)
        volume = _number(row.get("Set Volume (kg)"), "Set Volume (kg)", 1e7,
                         nullable=True)
        duration_seconds = _number(row.get("Set Duration (s)"),
                                   "Set Duration (s)", 86400, nullable=True)
        notes = row.get("Notes") or ""
        if reps:
            if displayed is None:
                raise GMHistoryCSVError("Wiederholungssatz ohne dokumentiertes Gewicht")
            # Preserve the explicitly exported per-set resistance verbatim.
            # Set Volume is an aggregate and MUST NOT be used to guess a
            # per-grip multiplier (regression to the v0.1.18 weight bug).
            weight = displayed
            strength_count += 1
            total_reps += reps
            exercises[key]["completion_method"] = 1
        else:
            if displayed not in (None, 0):
                raise GMHistoryCSVError("Zeitsatz mit unerwartetem Gewicht")
            weight = 0
            timed_count += 1
            if side:
                bilateral_rows += 1
            exercises[key]["completion_method"] = 0
            if duration_seconds is None:
                note_match = TIMED.search(notes)
                if not note_match:
                    raise GMHistoryCSVError("Zeitsatz ohne Dauer in der CSV")
                duration_seconds = _number(note_match.group(1), "timed set", 86400)
                guessed_duration += 1

        if duration_seconds is None:
            # No timing telemetry for the rare weighted set missing a
            # duration. The FIT writer will use its documented fallback.
            guessed_duration += 1
        if volume is not None:
            volume_total += volume
        exercises[key]["sets"].append({
            "reps": reps,
            "seconds": duration_seconds or 0,
            "weight": weight,
            "weight_already_total": True,
        })

    if not strength_count:
        raise GMHistoryCSVError("Dieses Training enthält keine Kraftsätze")
    expected_volume = _number(matching[0].get("Session Volume (kg)"),
                              "Session Volume (kg)", 1e9, nullable=True)
    if expected_volume is not None and abs(volume_total - expected_volume) > max(1, expected_volume * 0.005):
        raise GMHistoryCSVError("Satzvolumen und Gesamtvolumen der CSV sind widersprüchlich")
    if sum(float((s.get("seconds") or 0)) for ex in exercises.values()
           for s in ex["sets"]) > duration + 10:
        raise GMHistoryCSVError("Satzdauern übersteigen die Trainingsdauer")
    return {
        "exercises": list(exercises.values()),
        "unit": "kg",
        "exercise_count": len({r["Exercise ID"].strip() for r in matching}),
        "fit_exercise_count": len(exercises),
        "set_count": len(matching),
        "strength_set_count": strength_count,
        "timed_set_count": timed_count,
        "side_rows": bilateral_rows,
        "estimated_durations": guessed_duration,
        "total_reps": total_reps,
        "duration_seconds": duration,
        "source": "gm_manager_history_csv",
    }


def load_gm_history_file(path, workout):
    p = Path(path)
    try:
        if not 0 < p.stat().st_size <= MAX_BYTES:
            raise GMHistoryCSVError("History-CSV ist leer oder zu groß")
        return parse_gm_history_csv(p.read_bytes(), workout)
    except (OSError, UnicodeError):
        raise GMHistoryCSVError("History-CSV konnte nicht gelesen werden") from None
