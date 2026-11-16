"""Read-only, experimental Speediance cloud client (unofficial API).

Never log request payloads, headers, full responses or account IDs.
"""
from datetime import date
import json
import time
import urllib.error
import urllib.request

HOSTS = {"EU": "euapi.speediance.com", "Global": "api2.speediance.com"}
ROUTES = {
    1: ["cttTrainingInfoDetail"],
    2: ["courseTrainingInfoDetail"],
    4: ["aiCourseTrainingInfoDetail"],
    5: ["cttTrainingInfoDetail"],
}
ALL_ROUTES = ["aiCourseTrainingInfoDetail", "courseTrainingInfoDetail", "cttTrainingInfoDetail"]
# Speediance keeps one session per client type. The phone app uses SOFTWARE.
# BIKE/NANO work as separate slots, provided the user owns neither device.
# References: labatt/speediance-mcp and labatt/speediance-smartgym-workout-manager.
LOGIN_CLIENT_TYPES = {
    "bike": ("BIKE", "1"),
    "nano": ("NANO", "1"),
    "phone": ("SOFTWARE", "41000"),
}
DEFAULT_LOGIN_CLIENT_TYPE = "bike"


class APIError(Exception):
    pass


class Client:
    def __init__(self, logger, region="EU", device=1, login_client_type=DEFAULT_LOGIN_CLIENT_TYPE):
        self.logger = logger
        self.host = HOSTS[region]
        self.device = device
        self.token = None
        self.user_id = None
        self.unit = "kg"
        if login_client_type not in LOGIN_CLIENT_TYPES:
            raise ValueError("Unbekannter Speediance-Anmeldetyp")
        self.login_client_type = login_client_type

    def request(self, path, payload=None, allow_error=False, login_as=None):
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

        data = self.request("/api/app/v2/login/byPass", {
            "userIdentity": email, "password": password, "type": 2
        }, login_as=self.login_client_type)
        if not isinstance(data, dict):
            raise APIError("Login-Antwort unvollständig")
        self.token = data.get("token")
        self.user_id = str(data.get("appUserId") or "")
        self.unit = "lb" if data.get("unit") == 1 else "kg"
        if not self.token or not self.user_id:
            raise APIError("Login: Token oder Nutzer-ID fehlt")
        self.logger.info("Login successful")

    def list_workouts(self, start, end):
        items = []
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            path = "/api/app/v5/trainingCalendar/monthNew?date=%d-%02d&selectedDeviceType=%d" % (
                year, month, self.device
            )
            days = self.request(path) or []
            if not isinstance(days, list):
                raise APIError("Kalenderantwort hat unerwartetes Format")
            for day in days:
                try:
                    day_date = date.fromisoformat(day["date"])
                except (ValueError, KeyError, TypeError):
                    continue
                if not start <= day_date <= end:
                    continue
                for plan in (day.get("trainingPlanList") or []):
                    if plan.get("isFinish") != 1 or not plan.get("trainingId"):
                        continue
                    items.append({
                        "training_id": int(plan["trainingId"]),
                        "day": day_date.isoformat(),
                        "title": plan.get("title") or "Training",
                        "finished_at": plan.get("finishTime"),
                        "duration_min": plan.get("durationMinute") or 0,
                        "calories": plan.get("calorie") or 0,
                        "type": plan.get("type") or 0,
                        "unit": self.unit,
                    })
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        items.sort(key=lambda w: (w["day"], w["finished_at"] or "", w["training_id"]), reverse=True)
        self.logger.info("Loaded %d completed workouts", len(items))
        return items

    def detail(self, workout):
        raw = None
        # The calendar's type sometimes points at an empty detail endpoint.
        # Safely try alternative read-only endpoints before declaring no details.
        preferred = ROUTES.get(workout.get("type"), [])
        routes = list(dict.fromkeys(preferred + ALL_ROUTES))
        self.logger.info("Fetching session details using up to %d routes", len(routes))
        raw = []
        for route in routes:
            candidate = self.request(
                "/api/app/trainingInfo/%s/%d" % (route, workout["training_id"]),
                allow_error=True,
            )
            if isinstance(candidate, dict):
                # Newer API variants may wrap the exercise list.
                candidate = next((candidate[key] for key in (
                    "list", "records", "data", "trainingInfoDetailList", "exerciseList")
                    if isinstance(candidate.get(key), list)), [])
            # A nonempty list can still be just a template with zero performed
            # reps. Keep looking for the session's actual completed-set log.
            if isinstance(candidate, list) and any(
                isinstance(ex, dict) and ex.get("finishedReps") for ex in candidate
            ):
                raw = candidate
                break
            self.logger.info("Detail endpoint returned no completed sets; trying fallback")
        if not isinstance(raw, list) or not raw:
            self.logger.warning("No exercise details after trying %d endpoints", len(routes))
            raise APIError("Speediance hat für diese Trainingseinheit keine Übungsdetails geliefert")
        exercises = []
        for ex in raw:
            sets = []
            for s in (ex.get("finishedReps") or []):
                detail = s.get("trainingInfoDetail") or {}
                weights = []
                for weight in (detail.get("weights") or []):
                    try:
                        weights.append(float(weight))
                    except (ValueError, TypeError):
                        pass
                sets.append({
                    "reps": s.get("finishedCount") or 0,
                    "seconds": s.get("time") or 0,
                    "weight": max(weights) if weights else 0,
                })
            exercises.append({"name": ex.get("actionLibraryName") or "Übung", "sets": sets})
        count = sum(len(e["sets"]) for e in exercises)
        self.logger.info("Loaded %d exercises and %d sets", len(exercises), count)
        if not count:
            raise APIError("Speediance hat für dieses Training keine Sätze geliefert")
        return dict(workout, exercises=exercises)
