"""Official Garmin Connect Personal API: personal-use, READ ONLY.

API key -> 24h bearer JWT; GET activity summaries and original activity ZIP.
Never log credentials, bearer tokens, response bodies, or private activity names.
No undocumented Garmin Connect write/update endpoints are used.
"""
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import math
import zipfile

from activity_time import activity_bounds

BASE_URL = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
SEARCH_PATH = "/activitylist-service/activities/search/activities"


class GarminPersonalError(Exception):
    """Safe error class; never includes credentials or response content."""


def _read_response(request, opener=urlopen, timeout=20):
    try:
        with opener(request, timeout=timeout) as response:
            return response.read(24 * 1024 * 1024 + 1)
    except HTTPError as error:
        raise GarminPersonalError(
            "Garmin Personal API HTTP %d" % error.code
        ) from None
    except (URLError, OSError, TimeoutError):
        raise GarminPersonalError("Keine Verbindung zur Garmin Personal API") from None


def obtain_token(api_key, opener=urlopen):
    if not isinstance(api_key, str) or not api_key.strip():
        raise GarminPersonalError("Garmin Personal API-Schlüssel fehlt")
    request = Request(BASE_URL + TOKEN_PATH,
                      headers={"Authorization": "ApiKey " + api_key.strip(),
                               "Accept": "*/*"},
                      method="POST")
    payload = _read_response(request, opener=opener)
    try:
        token = payload.decode("utf-8").strip().strip('"')
        # Validate JWT shape without leaking or persisting its contents.
        if len(token.split(".")) != 3 or len(token) < 40:
            raise ValueError("Unexpected bearer token")
    except (ValueError, UnicodeDecodeError):
        raise GarminPersonalError("Ungültige Antwort vom Garmin-Tokenserver") from None
    return token


class GarminPersonalClient:
    def __init__(self, api_key, opener=urlopen):
        self._opener = opener
        self._api_key = api_key
        self._token = None
        self._token_expires_at = datetime.min.replace(tzinfo=timezone.utc)

    def _get_token(self):
        now = datetime.now(timezone.utc)
        if self._token and now < self._token_expires_at:
            return self._token
        self._token = obtain_token(self._api_key, opener=self._opener)
        # Expiry at most 24 h; conservatively re-exchange after 23 h.
        self._token_expires_at = now + timedelta(hours=23)
        return self._token

    def _get(self, path, params=None, binary=False):
        query = ("?" + urlencode(params)) if params else ""
        request = Request(
            BASE_URL + path + query,
            headers={
                "Authorization": "Bearer " + self._get_token(),
                "Accept": "application/zip, application/x-zip-compressed, application/octet-stream"
                if binary else "application/json",
            },
            method="GET",
        )
        response = _read_response(request, opener=self._opener)
        if len(response) > 24 * 1024 * 1024:
            raise GarminPersonalError("Garmin-Aktivitätsdatei zu groß")
        if binary:
            return response
        try:
            return json.loads(response)
        except (ValueError, UnicodeDecodeError):
            raise GarminPersonalError("Unverständliche Garmin-API-Antwort") from None

    def activities(self, start_date, end_date):
        """Search a narrow range, bounded pagination to avoid excessive GETs."""
        found = []
        for start in (0, 100, 200):
            rows = self._get(SEARCH_PATH, {
                "start": start, "limit": 100,
                "startDate": str(start_date), "endDate": str(end_date),
            })
            if not isinstance(rows, list):
                raise GarminPersonalError("Unerwartetes Garmin-Aktivitätsformat")
            found.extend(row for row in rows if isinstance(row, dict))
            if len(rows) < 100:
                break
        return found

    def download_activity_fit(self, activity_id):
        """Extract only an authentic .fit from Garmin ZIP; no path traversal."""
        try:
            numeric_id = int(activity_id)
        except (ValueError, TypeError):
            raise GarminPersonalError("Ungültige Garmin-Aktivitäts-ID") from None
        if numeric_id <= 0:
            raise GarminPersonalError("Ungültige Garmin-Aktivitäts-ID")
        content = self._get("/download-service/files/activity/%d" % numeric_id,
                            binary=True)
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                candidates = [
                    item for item in archive.infolist()
                    if PurePosixPath(item.filename).suffix.lower() == ".fit"
                    and not item.is_dir()
                ]
                if len(candidates) != 1 or candidates[0].file_size > 24 * 1024 * 1024:
                    raise GarminPersonalError(
                        "Garmin-Download enthält nicht genau eine unterstützte FIT-Datei"
                    )
                fit = archive.read(candidates[0])
            if len(fit) < 16 or fit[8:12] != b".FIT":
                raise GarminPersonalError("Garmin-Datei ist kein gültiger FIT-Container")
            return fit
        except (zipfile.BadZipFile, OSError, RuntimeError):
            raise GarminPersonalError("Garmin-Download ist keine lesbare FIT-ZIP-Datei") from None


def _parse_datetime(text, utc=False):
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        d = datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc) if utc else d.astimezone()
        return d.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _activity_time(row):
    # Connect startTimeGMT is a UTC wall clock with no timezone in its JSON.
    return (_parse_datetime(row.get("startTimeGMT"), utc=True)
            or _parse_datetime(row.get("startTimeLocal")))


def match_activities(workout, rows, *, max_start_delta_seconds=20 * 60):
    """Rank same-session candidates; ambiguous matches require a user choice.

    Date alone is never sufficient. Preserve Garmin activity ID as opaque id,
    do not emit any secrets or arbitrary Garmin response fields to diagnostics.
    """
    start, _, duration = activity_bounds(workout)
    if start.tzinfo is None:
        start = start.astimezone()
    start = start.astimezone(timezone.utc)
    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        activity_id = row.get("activityId")
        if not isinstance(activity_id, int) or activity_id <= 0:
            continue
        other = _activity_time(row)
        if other is None:
            continue
        delta = abs((start - other).total_seconds())
        if delta > max_start_delta_seconds:
            continue
        raw_duration = row.get("duration")
        try:
            other_duration = float(raw_duration)
            if not math.isfinite(other_duration) or other_duration <= 0:
                other_duration = None
        except (TypeError, ValueError):
            other_duration = None
        # Duration may differ by few minutes because the watch starts first.
        ratio = (abs(other_duration - duration) / max(duration, other_duration)
                 if other_duration is not None else None)
        if ratio is not None and ratio > 0.4:
            continue
        candidates.append({
            "id": activity_id,
            "name": str(row.get("activityName") or "Garmin-Aktivität")[:90],
            "start": other.isoformat(),
            "start_delta_sec": int(round(delta)),
            "duration_sec": other_duration,
            "duration_diff_ratio": ratio,
        })
    return sorted(candidates, key=lambda x: (
        x["start_delta_sec"], x["duration_diff_ratio"] or 0, x["id"]
    ))
