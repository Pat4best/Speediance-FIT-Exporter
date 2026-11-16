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


class APIError(Exception):
    pass


class Client:
    def __init__(self, logger, region="EU", device=1):
        self.logger = logger
        self.host = HOSTS[region]
        self.device = device
        self.token = None
        self.user_id = None
        self.unit = "kg"

    def request(self, path, payload=None, allow_error=False):
        method = "POST" if payload is not None else "GET"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Dart/3.9 (dart:io)",
            "Timestamp": str(int(time.time() * 1000)),
            "Versioncode": "40304",
            "App_type": "SOFTWARE",
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
        verified = self.request("/api/app/v2/login/verifyIdentity", {
            "type": 2, "userIdentity": email
        })
        if not isinstance(verified, dict):
            raise APIError("Unbekannte Login-Prüfantwort")
        if verified.get("isExist") is False:
            raise APIError("Account in dieser Region nicht gefunden")
        if verified.get("hasPwd") is False:
            raise APIError("Für den Account ist kein Passwort eingerichtet")

        data = self.request("/api/app/v2/login/byPass", {
            "userIdentity": email, "password": password, "type": 2
        })
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
        for route in ROUTES.get(workout["type"], ALL_ROUTES):
            raw = self.request(
                "/api/app/trainingInfo/%s/%d" % (route, workout["training_id"]),
                allow_error=True,
            )
            if raw:
                break
        if not isinstance(raw, list):
            self.logger.warning("No strength-set details for workout type %s", workout["type"])
            raw = []
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
        self.logger.info("Loaded %d exercises and %d sets",
                         len(exercises), sum(len(e["sets"]) for e in exercises))
        return dict(workout, exercises=exercises)
