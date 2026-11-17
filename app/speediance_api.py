"""Read-only, experimental Speediance cloud client (unofficial API).

Never log request payloads, headers, full responses or account IDs.
"""
from datetime import date, datetime, timedelta
import json
import time
import urllib.error
import urllib.request
from urllib.parse import quote

from heart_rate import graph_details, graph_shape, valid_bpm
from hr_sensor import find_hr_sensor
from weight_handling import measured_set_weight
from activity_time import activity_bounds
from completed_workout_cache import load_detail_cache, save_detail_cache

HOSTS = {"EU": "euapi.speediance.com", "Global": "api2.speediance.com"}
ROUTES = {
    1: ["freeTraining"],
    2: ["courseTrainingInfoDetail"],
    3: ["cttTrainingInfoDetail"],
    4: ["aiCourseTrainingInfoDetail"],
    5: ["cttTrainingInfoDetail"],
    6: ["freeTraining"],
    7: ["freeTraining"],
    9: ["aiCourseTrainingInfoDetail"],
}
ALL_ROUTES = ["cttTrainingInfoDetail", "courseTrainingInfoDetail", "freeTraining", "aiCourseTrainingInfoDetail"]
# Speediance keeps one session per client type. The phone app uses SOFTWARE.
# BIKE/NANO work as separate slots, provided the user owns neither device.
# References: labatt/speediance-mcp and labatt/speediance-smartgym-workout-manager.
LOGIN_CLIENT_TYPES = {
    "bike": ("BIKE", "1"),
    "nano": ("NANO", "1"),
    "phone": ("SOFTWARE", "41000"),
}
DEFAULT_LOGIN_CLIENT_TYPE = "bike"
READ_VERSIONS = ("41000", "40304")  # Current and previously working calendar API version


class APIError(Exception):
    pass


# Presence-only diagnostics: a different history 'id' is not necessarily a
# completed-session ID and must never be guessed as a detail endpoint path.
HISTORY_CANDIDATE_FIELDS = (
    "id", "recordId", "trainingRecordId", "sessionId", "uuid",
    "trainingId", "templateId", "trainingTemplateId", "courseId",
    "planId", "courseType", "type",
)


def completed_history_shape(record):
    """Safe to log: no identifiers, titles, timestamps or measured values."""
    if not isinstance(record, dict):
        return {"identifier_fields": [], "id_relation": "unavailable",
                "history_type": "unknown"}
    fields = [key for key in HISTORY_CANDIDATE_FIELDS
              if record.get(key) is not None]
    history_id = record.get("id")
    training_id = record.get("trainingId")
    if history_id is None or training_id is None:
        relation = "unavailable"
    elif str(history_id) == str(training_id):
        relation = "same"
    else:
        relation = "different"
    try:
        kind = int(record.get("type"))
    except (ValueError, TypeError, OverflowError):
        kind = None
    return {
        "identifier_fields": fields,
        "id_relation": relation,
        "history_type": kind if kind in ROUTES else "unknown",
    }


def workout_provenance_shape(workout, history_rows):
    """Compare selected workout to completed history without exposing IDs.

    Calendar rows are not guaranteed to occur in the history response, and
    a logged cross-reference for another row must not be attributed to this
    selected workout. Only compare in memory; return counts and booleans.
    """
    try:
        current_id = int(workout.get("training_id"))
    except (ValueError, TypeError, OverflowError):
        current_id = None
    day = str(workout.get("day") or "")[:10]
    title = " ".join(str(workout.get("title") or "").casefold().split())
    try:
        duration = float(workout.get("duration_min") or 0) * 60
    except (ValueError, TypeError, OverflowError):
        duration = 0
    valid_day = [r for r in history_rows if r.get("day") == day and day]
    exact = [r for r in history_rows if current_id is not None
             and r.get("training_id") == current_id]
    same_title = [r for r in valid_day if title and
                  " ".join(str(r.get("title") or "").casefold().split()) == title]
    near_duration = [r for r in valid_day
                     if duration > 0 and r.get("duration_seconds") is not None
                     and abs(r["duration_seconds"] - duration) <= 180]
    both = [r for r in same_title if r in near_duration]
    return {
        "matched_by_trainingId": bool(exact),
        "history_on_same_day": len(valid_day),
        "same_day_same_title": len(same_title),
        "same_day_close_duration": len(near_duration),
        "same_day_title_and_duration": len(both),
    }


class Client:
    def __init__(self, logger, region="EU", device=1,
                 login_client_type=DEFAULT_LOGIN_CLIENT_TYPE, cache_dir=None):
        self.logger = logger
        self.host = HOSTS[region]
        self.device = device
        self.token = None
        self.user_id = None
        self.unit = "kg"
        if login_client_type not in LOGIN_CLIENT_TYPES:
            raise ValueError("Unbekannter Speediance-Anmeldetyp")
        self.login_client_type = login_client_type
        self.cache_dir = cache_dir
        self.calendar_fallback_added = 0

    def request(self, path, payload=None, allow_error=False, login_as=None, read_version=None):
        method = "POST" if payload is not None else "GET"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        # Only login endpoints use a dedicated client slot; regular
        # read-only requests continue as SOFTWARE with that slot's token.
        if login_as is not None and login_as not in LOGIN_CLIENT_TYPES:
            raise ValueError("Unbekannter Speediance-Anmeldetyp")
        app_type, version_code = (
            LOGIN_CLIENT_TYPES[login_as] if login_as
            else ("SOFTWARE", "41000")
        )
        if read_version is not None:
            if method != "GET" or login_as is not None or read_version not in READ_VERSIONS:
                raise ValueError("API-Versionswechsel nur für lesende Kalenderabfragen zulässig")
            version_code = read_version
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Dart/3.9 (dart:io)",
            "Timestamp": str(int(time.time() * 1000)),
            "Versioncode": version_code,
            "App_type": app_type,
        }
        if self.token:
            headers["Token"] = self.token
            headers["App_user_id"] = self.user_id

        # Explicitly avoid path parameters in logs (training IDs).
        route = path.split("?")[0].rsplit("/", 1)[0] if "/trainingInfo/" in path else path.split("?")[0]
        self.logger.info("API %s %s", method, route)
        request = urllib.request.Request(
            "https://" + self.host + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                content = response.read(5_000_000)
        except urllib.error.HTTPError as exc:
            self.logger.warning("HTTP %s on %s", exc.code, route)
            if allow_error:
                return None
            raise APIError("HTTP %s (%s)" % (exc.code, route)) from None
        except Exception as exc:
            self.logger.warning("Network error %s on %s", type(exc).__name__, route)
            raise APIError("Verbindung fehlgeschlagen (%s)" % type(exc).__name__) from None

        try:
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError("Unexpected response shape")
            code = result.get("code")
            safe_code = str(code)[:32] if isinstance(code, (str, int)) else "unknown"
            self.logger.info("API response HTTP=%s code=%s on %s", status, safe_code, route)
            if code not in (0, None, "0"):
                if allow_error:
                    return None
                raise APIError("Speediance API-Fehler %s (%s)" % (safe_code, route))
            return result.get("data")
        except (ValueError, AttributeError, TypeError):
            self.logger.warning("Invalid JSON response on %s", route)
            raise APIError("Antwort ist kein gültiges API-JSON") from None

    def login(self, email, password):
        self.logger.info("Speediance login using client type %s", self.login_client_type)
        verified = self.request("/api/app/v2/login/verifyIdentity", {
            "type": 2, "userIdentity": email
        }, login_as=self.login_client_type)
        if not isinstance(verified, dict):
            raise APIError("Unbekannte Login-Prüfantwort")
        if verified.get("isExist") is False:
            raise APIError("Account in dieser Region nicht gefunden")
        if verified.get("hasPwd") is False:
            raise APIError("Für den Account ist kein Passwort eingerichtet")

        try:
            data = self.request("/api/app/v2/login/byPass", {
                "userIdentity": email, "password": password, "type": 2
            }, login_as=self.login_client_type)
        except APIError as exc:
            # API code 96, among others, is a server-side login rejection.
            # The detailed code is already recorded by request() in the
            # sanitized log; show a clear, non-technical message to users.
            if "Speediance API-Fehler" in str(exc):
                raise APIError(
                    "Anmeldung fehlgeschlagen. Bitte E-Mail-Adresse, Passwort "
                    "und Region (EU/Global) überprüfen."
                ) from None
            raise
        if not isinstance(data, dict):
            raise APIError("Login-Antwort unvollständig")
        self.token = data.get("token")
        self.user_id = str(data.get("appUserId") or "")
        self.unit = "lb" if data.get("unit") == 1 else "kg"
        if not self.token or not self.user_id:
            raise APIError("Login: Token oder Nutzer-ID fehlt")
        self.logger.info("Login successful")

    def list_workouts(self, start, end):
        """Merge the documented Gym Monster and Gym Pal calendar views.

        Speediance may filter workouts by selectedDeviceType and by API version.
        Both requests are read-only and reuse our Bike/Nano session; they NEVER
        log in again as a phone. De-duplicate finished workouts by trainingId.
        """
        if end < start:
            raise ValueError("Ungültiger Zeitraum")
        items = {}
        self.calendar_fallback_added = 0
        self.calendar_other_device_added = 0
        self.history_added = 0
        self.history_stats = {}
        self.calendar_query_stats = []
        history_candidates = []
        year, month = start.year, start.month
        device_types = (self.device, 2 if self.device == 1 else 1)
        while (year, month) <= (end.year, end.month):
            valid_responses = 0
            for device_type in device_types:
                path = "/api/app/v5/trainingCalendar/monthNew?date=%d-%02d&selectedDeviceType=%d" % (
                    year, month, device_type
                )
                for version in READ_VERSIONS:
                    try:
                        days = self.request(path, read_version=version)
                    except APIError:
                        self.logger.warning(
                            "Calendar request failed month=%04d-%02d device=%d version=%s",
                            year, month, device_type, version
                        )
                        continue
                    if not isinstance(days, list):
                        self.logger.warning(
                            "Calendar invalid response month=%04d-%02d device=%d version=%s",
                            year, month, device_type, version
                        )
                        continue
                    valid_responses += 1
                    added = 0
                    duplicates = 0
                    unfinished = 0
                    skipped = 0
                    candidate_count = 0
                    for day in days:
                        if not isinstance(day, dict):
                            skipped += 1
                            continue
                        try:
                            day_date = date.fromisoformat(str(day["date"])[:10])
                        except (ValueError, KeyError, TypeError):
                            skipped += 1
                            continue
                        if not start <= day_date <= end:
                            continue
                        plans = day.get("trainingPlanList") or []
                        if not isinstance(plans, list):
                            skipped += 1
                            continue
                        candidate_count += len(plans)
                        for plan in plans:
                            if not isinstance(plan, dict):
                                skipped += 1
                                continue
                            if plan.get("isFinish") not in (1, True, "1", "true", "True"):
                                unfinished += 1
                                continue
                            try:
                                training_id = int(plan["trainingId"])
                                if training_id <= 0:
                                    skipped += 1
                                    continue
                            except (ValueError, TypeError, KeyError):
                                skipped += 1
                                continue
                            if training_id in items:
                                duplicates += 1
                                continue
                            items[training_id] = {
                                "training_id": training_id,
                                "day": day_date.isoformat(),
                                "title": plan.get("title") or "Training",
                                "finished_at": plan.get("finishTime"),
                                "duration_min": plan.get("durationMinute") or 0,
                                "calories": plan.get("calorie") or 0,
                                "type": plan.get("type") or 0,
                                "unit": self.unit,
                                "device_type": device_type,
                            }
                            added += 1
                            if version == READ_VERSIONS[-1]:
                                self.calendar_fallback_added += 1
                            if device_type != self.device:
                                self.calendar_other_device_added += 1
                    self.calendar_query_stats.append({
                        "month": "%04d-%02d" % (year, month),
                        "device": device_type, "version": version,
                        "days": len(days), "candidates": candidate_count,
                        "added": added, "duplicates": duplicates,
                        "unfinished": unfinished, "skipped": skipped,
                    })
                    # Aggregates only: no dates of workouts, titles or training IDs.
                    self.logger.info(
                        "Calendar month=%04d-%02d device=%d version=%s days=%d "
                        "candidates=%d added=%d duplicates=%d unfinished=%d skipped=%d",
                        year, month, device_type, version, len(days),
                        candidate_count, added, duplicates, unfinished, skipped
                    )
            if not valid_responses:
                raise APIError(
                    "Speediance-Kalender für %04d-%02d ist derzeit nicht verfügbar" %
                    (year, month)
                )
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        # Unlike monthNew, userTrainingDataRecord includes completed CUSTOM
        # templates. No new login; this is a read-only authenticated GET.
        history_path = (
            "/api/mobile/v2/report/userTrainingDataRecord?"
            "startDate=%s&endDate=%s" % (start.isoformat(), end.isoformat())
        )
        try:
            rows = self.request(history_path)
        except APIError:
            self.logger.warning("Training history query failed (APIError)")
            rows = None
        if not isinstance(rows, list):
            self.logger.warning("Training history unavailable or unexpected response type")
        else:
            stat = {"rows": len(rows), "added": 0, "duplicates": 0,
                    "outside": 0, "health": 0, "invalid": 0}
            for record in rows:
                if not isinstance(record, dict):
                    stat["invalid"] += 1
                    continue
                # Phone Health walk/rides aren't Gym Monster workouts.
                if record.get("belongUserHealth") or not record.get("trainingId"):
                    stat["health"] += 1
                    continue
                try:
                    tid = int(record["trainingId"])
                    date_text = str(record["startTime"])[:10]
                    started = date.fromisoformat(date_text)
                    if tid <= 0:
                        raise ValueError("invalid id")
                except (ValueError, KeyError, TypeError):
                    stat["invalid"] += 1
                    continue
                if not start <= started <= end:
                    stat["outside"] += 1
                    continue
                try:
                    history_duration = float(record.get("trainingTime"))
                    if not 0 < history_duration <= 86400:
                        history_duration = None
                except (ValueError, TypeError, OverflowError):
                    history_duration = None
                history_candidates.append({
                    "training_id": tid,
                    "day": started.isoformat(),
                    "title": record.get("title"),
                    "duration_seconds": history_duration,
                })
                if tid in items:
                    # A calendar template might no longer exist. The history
                    # record may expose distinct identifiers. Only compare
                    # structural presence; never log actual values or assume
                    # another id is safe to request as a detail endpoint.
                    shape = completed_history_shape(record)
                    calendar_kind = items[tid].get("type")
                    items[tid]["history_type"] = shape["history_type"]
                    self.logger.info(
                        "Completed workout history cross-reference: "
                        "history_fields=%s id_vs_trainingId=%s "
                        "calendar_type=%s history_type=%s",
                        shape["identifier_fields"], shape["id_relation"],
                        calendar_kind if calendar_kind in ROUTES else "unknown",
                        shape["history_type"],
                    )
                    # History can contain the real clock start of a workout
                    # already discovered through the month calendar.
                    items[tid]["watch_type"] = record.get("watchType") or 0
                    if record.get("startTime"):
                        items[tid]["started_at"] = record["startTime"]
                    sensor = find_hr_sensor(record)
                    if sensor:
                        items[tid]["hr_sensor"] = sensor
                    stat["duplicates"] += 1
                    continue
                try:
                    seconds = max(0, float(record.get("trainingTime") or 0))
                except (TypeError, ValueError):
                    seconds = 0
                # History startTime is LOCAL; derive the end only when the
                # timestamp is present, rather than inventing clock times.
                try:
                    started_at = datetime.fromisoformat(
                        str(record["startTime"]).replace("Z", "+00:00"))
                    finished_at = (started_at + timedelta(seconds=seconds)).isoformat()
                except (ValueError, TypeError):
                    finished_at = None
                items[tid] = {
                    "training_id": tid,
                    "day": started.isoformat(),
                    "title": record.get("title") or "Training",
                    "finished_at": finished_at,
                    "duration_min": seconds / 60,
                    "calories": record.get("calorie") or 0,
                    "type": record.get("type") or 0,
                    "unit": self.unit,
                    "device_type": self.device,
                    "source": "history",
                    "history_type": completed_history_shape(record)["history_type"],
                    "started_at": record.get("startTime"),
                    "watch_type": record.get("watchType") or 0,
                    "hr_sensor": find_hr_sensor(record),
                }
                stat["added"] += 1
            self.history_added = stat["added"]
            self.history_stats = stat
            self.logger.info(
                "Training history rows=%d added=%d duplicates=%d outside=%d "
                "health=%d invalid=%d",
                stat["rows"], stat["added"], stat["duplicates"],
                stat["outside"], stat["health"], stat["invalid"]
            )
        result = list(items.values())
        result.sort(key=lambda w: (
            w["day"], str(w["finished_at"] or ""), w["training_id"]
        ), reverse=True)
        # One privacy-safe line per visible workout row. The 1-based row
        # matches the displayed list order, allowing the selected session
        # to be diagnosed without showing title, date, ID or measured values.
        for row_number, workout in enumerate(result, 1):
            evidence = workout_provenance_shape(workout, history_candidates)
            source = workout.get("source") or "calendar"
            self.logger.info(
                "Workout history provenance row=%d source=%s "
                "matched_by_trainingId=%s history_on_same_day=%d "
                "same_day_same_title=%d same_day_close_duration=%d "
                "same_day_title_and_duration=%d",
                row_number, source if source in ("calendar", "history") else "unknown",
                evidence["matched_by_trainingId"],
                evidence["history_on_same_day"],
                evidence["same_day_same_title"],
                evidence["same_day_close_duration"],
                evidence["same_day_title_and_duration"],
            )
        self.logger.info(
            "Loaded %d completed workouts; recovered=%d old API, %d other device, %d history",
            len(result), self.calendar_fallback_added,
            self.calendar_other_device_added, self.history_added
        )
        return result

    def detail(self, workout):
        # A completed workout is immutable. Prefer its previously verified
        # observations over another network request; never reconstruct
        # planned weights from a calendar template.
        cached = load_detail_cache(
            self.cache_dir, self.host, self.user_id, workout
        )
        if cached is not None:
            self.logger.info(
                "Completed workout details from local cache: exercises=%d sets=%d "
                "heart_samples=%d",
                len(cached["exercises"]),
                sum(len(e["sets"]) for e in cached["exercises"]),
                len(cached["heart_rate_points"]),
            )
            return dict(workout, **cached)
        raw = None
        # The calendar's type sometimes points at an empty detail endpoint.
        # Safely try alternative read-only endpoints before declaring no details.
        # The completed-history session type takes priority when known.
        # This only affects route order; no speculative ID substitution.
        resolved_type = workout.get("history_type")
        if resolved_type not in ROUTES:
            resolved_type = workout.get("type")
        preferred = ROUTES.get(resolved_type, [])
        routes = list(dict.fromkeys(preferred + ALL_ROUTES))
        # The Speediance backend sometimes rejects the same completed-set
        # detail with an app code (observed 100041) while returning the
        # workout in the calendar. Try the older *read-only* version headers
        # after the ordinary routes fail. No additional logins or POSTs.
        variants = [(route, None) for route in routes]
        variants.extend((route, READ_VERSIONS[-1]) for route in routes)
        self.logger.info(
            "Fetching session details using up to %d routes and %d "
            "read-only API version variants", len(routes), len(variants)
        )
        raw = []
        recording_uuid = None
        sensor_detail = None
        for route, version in variants:
            candidate = self.request(
                "/api/app/trainingInfo/%s/%d" % (route, workout["training_id"]),
                allow_error=True,
                read_version=version,
            )
            candidate_sensor = find_hr_sensor(candidate)
            candidate_uuid = (candidate.get("uuid") if isinstance(candidate, dict) else None)
            if isinstance(candidate, dict):
                # Free Lift and other variant APIs can carry a session UUID
                # on the response wrapper.
                candidate = next((candidate[key] for key in (
                    "list", "records", "data", "trainingInfoDetailList", "exerciseList")
                    if isinstance(candidate.get(key), list)), [])
            # A nonempty list can still be just a template with zero performed
            # reps. Keep looking for the session's actual completed-set log.
            if isinstance(candidate, list) and any(
                isinstance(ex, dict) and ex.get("finishedReps") for ex in candidate
            ):
                raw = candidate
                sensor_detail = candidate_sensor or find_hr_sensor(candidate)
                recording_uuid = candidate_uuid if isinstance(candidate_uuid, str) else None
                break
            self.logger.info(
                "Detail endpoint returned no completed sets; trying fallback "
                "(legacy_read_version=%s)",
                "yes" if version is not None else "no"
            )
        if not isinstance(raw, list) or not raw:
            self.logger.warning("No exercise details after trying %d endpoints", len(routes))
            raise APIError("Speediance hat für diese Trainingseinheit keine Übungsdetails geliefert")
        exercises = []
        weight_sources = {}
        variable_sets = 0
        unknown_weight_fields = set()
        for ex in raw:
            sets = []
            for s in (ex.get("finishedReps") or []):
                detail = s.get("trainingInfoDetail") or {}
                if not recording_uuid and isinstance(detail.get("uuid"), str):
                    recording_uuid = detail["uuid"]
                weight, already_total, weight_diagnostic = measured_set_weight(detail, s)
                source = weight_diagnostic["source"]
                weight_sources[source] = weight_sources.get(source, 0) + 1
                variable_sets += int(weight_diagnostic["contains_changes"])
                # Available fields, never their contents, may help distinguish
                # recorded load from a plan setting if the reported load is wrong.
                candidate_fields = {
                    "weight", "actualWeight", "actualWeights", "realWeight",
                    "realWeights", "finishedWeight", "usedWeight",
                    "targetWeight", "targetWeights", "setWeight",
                    "startWeight", "endWeight", "resistance", "load",
                    "leftWeight", "rightWeight",
                }
                unknown_weight_fields.update(candidate_fields.intersection(s))
                unknown_weight_fields.update(candidate_fields.intersection(detail))
                sets.append({
                    "reps": s.get("finishedCount") or 0,
                    "seconds": s.get("time") or 0,
                    "weight": weight,
                    "weight_already_total": already_total,
                })
            exercises.append({
                "name": ex.get("actionLibraryName") or "Übung",
                "sets": sets,
                # 1 = repetitions, 0/2 = timed; needed to avoid counting
                # cardio/dehn seconds as strength repetitions in Garmin.
                "completion_method": ex.get("completionMethod"),
            })
        count = sum(len(e["sets"]) for e in exercises)
        self.logger.info("Loaded %d exercises and %d sets", len(exercises), count)
        self.logger.info(
            "Weight source of completed sets: %s; variable_recorded_sets=%d; "
            "other_recognized_weight_fields=%s",
            weight_sources, variable_sets, sorted(unknown_weight_fields),
        )
        if weight_sources.get("generic_telemetry"):
            self.logger.warning(
                "Weight provenance: %d sets use generic 'weights' data "
                "without independently verified per-cable measurements",
                weight_sources["generic_telemetry"],
            )
        if not count:
            raise APIError("Speediance hat für dieses Training keine Sätze geliefert")
        # A per-set maximum is a real measurement. It can form a true
        # maximum summary but never an average or synthetic sample series.
        peaks = [
            bpm for ex in raw for row in (ex.get("finishedReps") or [])
            if isinstance(row, dict)
            for bpm in [valid_bpm(row.get("maxHeartRate"))]
            if bpm is not None
        ]
        self.logger.info("Heart-rate: %d sets with measured peaks", len(peaks))
        heart_points = []
        summary = {"max": max(peaks)} if peaks else {}
        timing_estimated = False
        sensor = sensor_detail or workout.get("hr_sensor")
        self.logger.info("Heart-rate sensor model exposed by Speediance: %s",
                         "yes" if sensor else "no")
        if recording_uuid:
            # Read-only cloud request with existing Bike/Nano session.
            # Never log UUID, raw graph, exact sensor name or pulse values.
            try:
                graph = self.request(
                    "/api/app/watchMsg/getHeartRateGraph?uuid=%s" %
                    quote(recording_uuid, safe=""),
                    allow_error=True,
                )
                activity_start, _, duration = activity_bounds(
                    dict(workout, exercises=exercises)
                )
                local_clock = activity_start.astimezone()
                day_seconds = (local_clock.hour * 3600 +
                               local_clock.minute * 60 +
                               local_clock.second)
                parsed = graph_details(
                    graph, duration_seconds=duration,
                    start_epoch=activity_start.timestamp(),
                    start_day_seconds=day_seconds,
                )
                heart_points = parsed["points"]
                timing_estimated = parsed["timing_estimated"]
                summary.update(parsed["summary"])
                if peaks:
                    summary["max"] = max(peaks + ([summary["max"]] if "max" in summary else []))
                sensor = sensor or find_hr_sensor(graph)
                self.logger.info(
                    "Heart-rate graph: %d measured samples; format=%s "
                    "raw_samples=%d time_mode=%s skipped_time=%d "
                    "estimated_timing=%s; summary=%s",
                    len(heart_points), parsed["series_format"],
                    parsed["raw_sample_count"], parsed["time_mode"],
                    parsed["skipped_time_points"], timing_estimated,
                    "yes" if parsed["summary"] else "no"
                )
                if not heart_points and parsed["raw_sample_count"]:
                    # Shape only: no UUIDs, arbitrary field names or BPM values.
                    self.logger.warning(
                        "Heart-rate sample structure unrecognized: %s",
                        graph_shape(graph)
                    )
            except (APIError, ValueError, TypeError):
                # Optional data must never break the strength export.
                self.logger.warning("Heart-rate graph request unavailable")
        else:
            self.logger.info("Heart-rate graph unavailable: recording UUID missing")
        result = dict(
            workout, exercises=exercises,
            heart_rate_points=heart_points,
            heart_rate_summary=summary,
            heart_rate_timing_estimated=timing_estimated,
            hr_sensor=sensor,
        )
        try:
            saved = save_detail_cache(
                self.cache_dir, self.host, self.user_id, workout, result
            )
            if saved:
                self.logger.info(
                    "Completed workout details cached locally: exercises=%d sets=%d "
                    "heart_samples=%d",
                    len(exercises), count, len(heart_points),
                )
        except (OSError, ValueError, TypeError):
            self.logger.warning("Local completed-workout cache write failed")
        return result
