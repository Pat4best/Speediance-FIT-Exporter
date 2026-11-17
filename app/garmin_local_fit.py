"""Offline Garmin FIT source for the original-file-first strength merge.

A selected local Garmin FIT replaces the *Garmin Personal API download* only.
It does not supply Speediance workout details, which remain necessary.
Validate the original file and clock before any Speediance network calls.
Never log FIT content or local file paths.
"""
from datetime import timezone
from pathlib import Path
from hashlib import sha256
import math

from activity_time import activity_bounds
from garmin_fit_overlay import parse_fit_wire, _get_numeric
from garmin_fit_reader import read_garmin_activity


MAX_SIZE = 24 * 1024 * 1024


class LocalGarminFitError(ValueError):
    """Non-sensitive, user-readable local Garmin FIT validation error."""


def read_local_garmin_fit(path):
    """Return validated original FIT bytes, digest and summary."""
    candidate = Path(path)
    if candidate.suffix.lower() != ".fit":
        raise LocalGarminFitError("Bitte eine Garmin-Aktivitätsdatei (.fit) wählen")
    try:
        size = candidate.stat().st_size
        if size < 16 or size > MAX_SIZE:
            raise LocalGarminFitError("Garmin-FIT ist leer oder größer als 24 MB")
        content = candidate.read_bytes()
    except OSError:
        raise LocalGarminFitError("Die gewählte FIT-Datei kann nicht gelesen werden") from None
    if len(content) != size:
        raise LocalGarminFitError("Die FIT-Datei wurde während des Lesens verändert")
    try:
        chunks = parse_fit_wire(content)
        identities = [x for x in chunks if x["kind"] == "data" and x["global"] == 0]
        sessions = [x for x in chunks if x["kind"] == "data" and x["global"] == 18]
        if len(identities) != 1 or len(sessions) != 1:
            raise LocalGarminFitError(
                "Die Garmin-FIT muss eine einzelne abgeschlossene Aktivität enthalten"
            )
        if _get_numeric(identities[0], 0) != 4:
            raise LocalGarminFitError("Die Datei ist kein Garmin-FIT-Aktivitätsexport")
        if _get_numeric(identities[0], 1) != 1:
            raise LocalGarminFitError(
                "Bitte die originale Garmin-FIT herunterladen, nicht einen Speediance- oder bereits gemergten FIT-Export"
            )
        result = read_garmin_activity(content)
    except LocalGarminFitError:
        raise
    except (ValueError, TypeError, OverflowError, IndexError):
        raise LocalGarminFitError("Ungültige oder beschädigte Garmin-FIT-Datei") from None
    if result.get("start") is None or not result.get("duration_seconds"):
        raise LocalGarminFitError(
            "Garmin-FIT enthält keine auswertbaren Start- und Dauerdaten"
        )
    return content, sha256(content).hexdigest(), result


def match_local_garmin_fit(workout, garmin, *, start_window_seconds=20 * 60):
    """Check clock and duration; never pair activities on date alone."""
    speed_start, _, speed_duration = activity_bounds(workout)
    if speed_start.tzinfo is None:
        speed_start = speed_start.astimezone()
    speed_start = speed_start.astimezone(timezone.utc)
    garmin_start = garmin.get("start")
    if garmin_start is None:
        raise LocalGarminFitError("Garmin-FIT enthält keinen Trainingsbeginn")
    garmin_start = garmin_start.astimezone(timezone.utc)
    offset = abs((speed_start - garmin_start).total_seconds())
    garmin_duration = garmin.get("duration_seconds")
    try:
        garmin_duration = float(garmin_duration)
    except (TypeError, ValueError, OverflowError):
        garmin_duration = None
    if garmin_duration is not None and not math.isfinite(garmin_duration):
        garmin_duration = None
    diff_ratio = (
        abs(garmin_duration - speed_duration) / max(garmin_duration, speed_duration)
        if garmin_duration is not None and garmin_duration > 0 else None
    )
    if offset > start_window_seconds or (diff_ratio is not None and diff_ratio > 0.40):
        raise LocalGarminFitError(
            "Garmin-FIT passt zeitlich nicht zum ausgewählten Speediance-Training "
            "(Start über 20 Minuten oder Dauer um mehr als 40 % abweichend)"
        )
    return {
        "start": garmin_start,
        "start_delta_seconds": int(round(offset)),
        "garmin_duration_seconds": garmin_duration,
        "speediance_duration_seconds": speed_duration,
        "record_count": garmin["record_count"],
    }


def validated_local_fit(workout, path):
    """Checks content and matching independently of Garmin/Speediance API."""
    content, digest, metrics = read_local_garmin_fit(path)
    match = match_local_garmin_fit(workout, metrics)
    return content, digest, match
