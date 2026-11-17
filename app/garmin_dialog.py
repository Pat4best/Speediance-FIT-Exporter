"""Optional user-confirmed Garmin Personal API activity match and local FIT merge."""
from datetime import date, timedelta
from pathlib import Path
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from fitwriter import write_fit
from garmin_fit_overlay import overlay_garmin_fit, GarminOverlayError
from gm_manager_import import (GMManagerImportError, load_gm_manager_file,
                               resolve_exercise_names)
from gm_history_import import GMHistoryCSVError, load_gm_history_file
from garmin_local_fit import (
    read_local_garmin_fit, match_local_garmin_fit, LocalGarminFitError,
)
from garmin_merge import PRIORITY_LABELS, check_priorities
from speediance_api import APIError
from garmin_personal import GarminPersonalClient, GarminPersonalError, match_activities
from preferences import (saved_mappings, saved_weight_multipliers,
                         saved_merge_priorities, save_merge_priorities)
from windows_credentials import (save_garmin_api_key, load_garmin_api_key,
                                 delete_garmin_api_key)

logger = logging.getLogger("speediance_fit")
API_KEY_PAGE = "https://connect.garmin.com/app/settings/personalApiToken"


def details_or_history(client, workout):
    """Never disguise an unavailable completed-session record as a merge."""
    try:
        detail = client.detail(workout)
    except APIError as exc:
        if "keine Übungsdetails" not in str(exc):
            raise
        logger.warning("Speediance completed set details unavailable; merge refused")
        raise GarminOverlayError(
            "Speediance liefert keine abgeschlossenen Übungssätze. "
            "Wähle zuerst 'GM-Manager-History-CSV wählen…' "
            "oder 'GM-Manager-JSON wählen…' und bestätige die Daten. "
            "Es wurde keine FIT-Datei erzeugt."
        ) from None
    if not any(ex.get("sets") for ex in detail.get("exercises") or []):
        raise GarminOverlayError(
            "Keine abgeschlossenen Übungssätze vorhanden; "
            "bitte eine GM-Manager-History-CSV auswählen."
        )
    return detail


class GarminMergeDialog(tk.Toplevel):
    def __init__(self, app, workout):
        super().__init__(app)
        self.app = app
        self.workout = workout
        self.detail = None
        self.candidates = []
        self.garmin_client = None
        self.local_fit_bytes = None
        self.source_verified = None
        self.gm_manager_import = None
        self.gm_history_import = None
        self.title(app.tr("Garmin-FIT-Quellen – Abgleich und Merge"))
        self.transient(app)
        w = min(850, max(640, app.winfo_screenwidth() - 80))
        h = min(760, max(650, app.winfo_screenheight() - 80))
        self.geometry("%dx%d" % (w, h))
        self.minsize(640, 540)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        self.grab_set()

    def _close(self):
        if self.app.busy:
            messagebox.showinfo(
                self.app.tr("Bitte laufenden Vorgang abschließen"),
                self.app.tr("Der Abgleich läuft noch. Bitte erst nach Abschluss schließen."),
                parent=self,
            )
            return
        self.garmin_client = None
        self.local_fit_bytes = None
        self.key.set("")
        self.destroy()

    def _build(self):
        tr = self.app.tr
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=tr("Garmin-Aktivität mit Speediance zusammenführen"),
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(outer, text=tr(
            "Garmin-FIT als Grundlage: Originalaufzeichnung, Geräte- und "
            "Sensordaten bleiben erhalten. Die tatsächlichen Speediance-"
            "Krafttrainingssätze werden ergänzt, wenn verfügbar; sonst bleiben Garmin-Sätze erhalten. "
            "Online bleibt alles unverändert."
        ), wraplength=745).pack(anchor="w", pady=(3, 10))

        credentials = ttk.LabelFrame(outer, text=tr("1 – Garmin-FIT-Quelle auswählen"),
                                     padding=8)
        credentials.pack(fill="x")
        self.source_choice = tk.StringVar(value="file")
        choices = ttk.Frame(credentials)
        choices.pack(fill="x", pady=(0, 6))
        ttk.Radiobutton(
            choices, text=tr("Garmin Personal API"), value="api",
            variable=self.source_choice, command=self._source_changed,
        ).pack(side="left")
        ttk.Radiobutton(
            choices, text=tr("Lokale Garmin-FIT-Datei"), value="file",
            variable=self.source_choice, command=self._source_changed,
        ).pack(side="left", padx=(24, 0))
        try:
            stored = load_garmin_api_key()
        except (OSError, RuntimeError, UnicodeError):
            stored = None
        self.key = tk.StringVar(value=stored or "")
        self.remember_key = tk.BooleanVar(value=bool(stored))
        row = ttk.Frame(credentials)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.key, show="●", width=48).pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text=tr("Schlüssel erstellen"),
                   command=lambda: webbrowser.open(API_KEY_PAGE)).pack(side="right")
        ttk.Checkbutton(
            credentials, text=tr("Garmin-Schlüssel geschützt auf diesem PC speichern"),
            variable=self.remember_key,
        ).pack(anchor="w", pady=(5, 0))
        self.local_file_path = tk.StringVar(value="")
        file_line = ttk.Frame(credentials)
        file_line.pack(fill="x", pady=(7, 0))
        ttk.Entry(file_line, textvariable=self.local_file_path,
                  width=63, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(file_line, text=tr("Garmin-FIT wählen…"),
                   command=self._pick_local_fit).pack(side="right")

        priority_frame = ttk.LabelFrame(outer, text=tr("2 – Datenpriorität festlegen"),
                                        padding=8)
        priority_frame.pack(fill="x", pady=(10, 0))
        self.priorities = {}
        stored_priority = saved_merge_priorities()
        for i, (key, german_label) in enumerate(PRIORITY_LABELS):
            ttk.Label(priority_frame, text=tr(german_label)).grid(
                row=i // 2, column=(i % 2) * 2, sticky="w",
                padx=(3 if i % 2 == 0 else 20, 8), pady=4)
            value = tk.StringVar(value=tr("Garmin") if stored_priority[key] == "garmin"
                                 else tr("Speediance"))
            ttk.Combobox(
                priority_frame, state="readonly", width=15,
                values=(tr("Garmin"), tr("Speediance")), textvariable=value,
            ).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="ew", pady=4)
            self.priorities[key] = value
        ttk.Label(priority_frame, text=tr(
            "Übungsdaten aus Speediance; alternativ bestätigte Werte aus GM Manager. "
            "Satzzeitpunkte ohne Aufzeichnung sind geschätzt."
        ), wraplength=730, foreground="#555").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.gm_manager_status = tk.StringVar(
            value=tr("Optional: GM-Manager-Export wählen und als absolviert bestätigen.")
        )
        ttk.Button(
            priority_frame, text=tr("GM-Manager-JSON wählen…"),
            command=self._pick_gm_manager_export,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 2), padx=(3, 0))
        ttk.Button(
            priority_frame, text=tr("GM-Manager-History-CSV wählen…"),
            command=self._pick_gm_history_export,
        ).grid(row=4, column=2, columnspan=2, sticky="w", pady=(6, 2), padx=(8, 0))
        ttk.Label(
            priority_frame, textvariable=self.gm_manager_status,
            wraplength=700, foreground="#555",
        ).grid(row=5, column=0, columnspan=4, sticky="w", padx=(3, 0))


        matched = ttk.LabelFrame(outer, text=tr("3 – Passende Garmin-Aktivität wählen"),
                                 padding=8)
        matched.pack(fill="x", pady=(10, 0))
        search_row = ttk.Frame(matched)
        search_row.pack(fill="x")
        self.search_button = ttk.Button(
            search_row, text=tr("Garmin-Aktivitäten suchen / FIT prüfen"),
            command=self.search)
        self.search_button.pack(side="left")
        self.search_status = tk.StringVar(value=tr("Noch keine Suche durchgeführt."))
        ttk.Label(search_row, textvariable=self.search_status,
                  foreground="#555").pack(side="left", padx=(12, 0))
        self.match_combo = ttk.Combobox(matched, state="readonly", width=84)
        self.match_combo.pack(fill="x", pady=(7, 0))

        ttk.Label(outer, text=tr(
            "Neue FIT-Datei aus der ORIGINALEN Garmin-Aufzeichnung. "
            "Für vollständige Garmin-Zeitachsen Garmin als Trainingsbeginn und "
            "Trainingsdauer wählen. Ein manueller Import kann eine zweite "
            "Aktivität erzeugen; online wird nichts gelöscht oder überschrieben."
        ), wraplength=750, foreground="#8a4800").pack(anchor="w", pady=(10, 6))

        bottom = ttk.Frame(outer)
        bottom.pack(side="bottom", fill="x", pady=(6, 0))
        ttk.Button(bottom, text=tr("Schließen"), command=self._close).pack(side="right")
        self.merge_button = ttk.Button(
            bottom, text=tr("Zusammengeführte FIT speichern…"),
            command=self.save_merge, state="disabled",
        )
        self.merge_button.pack(side="right", padx=(0, 10))

    def _selected_priorities(self):
        tr = self.app.tr
        data = {
            key: "garmin" if variable.get() == tr("Garmin") else "speediance"
            for key, variable in self.priorities.items()
        }
        return check_priorities(data)

    def _reset_search(self):
        self.detail = None
        self.candidates = []
        self.garmin_client = None
        self.local_fit_bytes = None
        self.source_verified = None
        self.match_combo["values"] = ()
        self.match_combo.set("")
        self.merge_button.state(["disabled"])
        self.search_status.set(self.app.tr("Quelle noch nicht überprüft."))

    def _source_changed(self):
        if not self.app.busy:
            self._reset_search()

    def _pick_local_fit(self):
        if self.app.busy:
            return
        selected = filedialog.askopenfilename(
            parent=self,
            title=self.app.tr("Originale Garmin-FIT-Datei wählen"),
            filetypes=[("FIT-Aktivitäten", "*.fit")],
        )
        if selected:
            self.local_file_path.set(selected)
            self.source_choice.set("file")
            self._reset_search()

    def _pick_gm_manager_export(self):
        if self.app.busy:
            return
        target = filedialog.askopenfilename(
            parent=self,
            title=self.app.tr("GM-Manager-Trainingsdatei wählen"),
            filetypes=[("JSON", "*.json")],
        )
        if not target:
            return
        try:
            parsed = load_gm_manager_file(target, self.workout)
        except GMManagerImportError as exc:
            messagebox.showerror(
                self.app.tr("GM-Manager-Import"), str(exc), parent=self,
            )
            return
        prompt = self.app.tr(
            "Dieser GM-Manager-Export enthält Vorgaben, keine nachgewiesenen "
            "Satz-Aufzeichnungen. Bestätigst du, dass die angegebenen "
            "Wiederholungen und Gewichte bei der ausgewählten Trainingseinheit "
            "tatsächlich absolviert wurden?\n\n"
            "Übungen: %d, Kraftsätze: %d, Zeitsätze: %d, Gewichte: %s.\n"
            "Garmin-Zeiten und Sensoraufzeichnung bleiben erhalten; "
            "Satzzeitpunkte werden geschätzt und die Gewichte nicht verdoppelt."
        ) % (parsed["exercise_count"], parsed["strength_set_count"],
             parsed["timed_set_count"], parsed["unit"])
        if not messagebox.askyesno(self.app.tr("Absolvierte Sätze bestätigen"),
                                   prompt, parent=self):
            return
        self.gm_manager_import = parsed
        self.gm_history_import = None
        self.gm_manager_status.set(
            self.app.tr("Bestätigt: %d Übungen, %d Sätze (davon %d Kraft).") %
            (parsed["exercise_count"], parsed["set_count"],
             parsed["strength_set_count"])
        )
        logger.info(
            "User-confirmed GM Manager import selected: exercise_count=%d "
            "sets=%d strength_sets=%d timed_sets=%d",
            parsed["exercise_count"], parsed["set_count"],
            parsed["strength_set_count"], parsed["timed_set_count"],
        )

    def _pick_gm_history_export(self):
        if self.app.busy:
            return
        target = filedialog.askopenfilename(
            parent=self,
            title=self.app.tr("GM-Manager-Trainingshistorie wählen"),
            filetypes=[("CSV", "*.csv")],
        )
        if not target:
            return
        try:
            parsed = load_gm_history_file(target, self.workout)
        except GMHistoryCSVError as exc:
            messagebox.showerror(
                self.app.tr("GM-Manager-Import"), str(exc), parent=self,
            )
            return
        prompt = self.app.tr(
            "Die GM-Manager-History-CSV enthält aufgezeichnete Satzwerte zur "
            "ausgewählten Einheit. Stimmt die Zuordnung?\n\n"
            "Übungen: %d, Kraftsätze: %d, Zeitsätze: %d, "
            "Links-/Rechts-Zeilen: %d.\n"
            "Gewichte werden ohne zusätzliche Verdopplung übernommen. "
            "Satzdauern werden verwendet; genaue Satzanfangszeiten sind nicht vorhanden."
        ) % (parsed["exercise_count"], parsed["strength_set_count"],
             parsed["timed_set_count"], parsed["side_rows"])
        if not messagebox.askyesno(self.app.tr("GM-Manager-History bestätigen"),
                                   prompt, parent=self):
            return
        self.gm_history_import = parsed
        self.gm_manager_import = None
        self.gm_manager_status.set(
            self.app.tr("History-CSV bestätigt: %d Übungen, %d Sätze, %d Kraft-Wiederholungen.") %
            (parsed["exercise_count"], parsed["set_count"], parsed["total_reps"])
        )
        logger.info(
            "Confirmed GM Manager workout history CSV: exercises=%d "
            "strength_sets=%d timed_sets=%d side_rows=%d "
            "estimated_durations=%d",
            parsed["exercise_count"], parsed["strength_set_count"],
            parsed["timed_set_count"], parsed["side_rows"],
            parsed["estimated_durations"],
        )

    def _show_matches(self, candidates, source_name):
        self.candidates = candidates
        if not candidates:
            self.search_status.set(
                self.app.tr("Keine zeitlich passende Garmin-Aktivität gefunden.")
            )
            messagebox.showinfo(
                self.app.tr("Kein eindeutiger Treffer"),
                self.app.tr("Keine Garmin-Aktivität passt zeitlich ausreichend. "
                            "Es wurde keine FIT-Datei erstellt."),
                parent=self,
            )
            return
        values = []
        for candidate in candidates:
            stamp = candidate["start"].replace("T", " ")[:19]
            minutes = round(candidate["start_delta_sec"] / 60, 1)
            values.append("%s | %s | Δ %.1f min" % (
                stamp, candidate["name"], minutes
            ))
        self.match_combo["values"] = values
        self.search_status.set(
            self.app.tr("%d mögliche Garmin-Aktivität(en). Bitte eine auswählen.") %
            len(values)
        )
        if len(values) == 1:
            self.match_combo.current(0)
        self.source_verified = source_name
        self.merge_button.state(["!disabled"])

    def search(self):
        if self.app.busy:
            return
        source = self.source_choice.get()
        # Validation happens without calling Speediance.detail(). Searching
        # Garmin does not depend on whether Speediance currently allows the
        # completed-set endpoint.
        if source == "file":
            candidate_path = self.local_file_path.get()
            if not candidate_path:
                self._pick_local_fit()
                candidate_path = self.local_file_path.get()
            if not candidate_path:
                return
            self._reset_search()
            self.search_status.set(self.app.tr("FIT-Datei wird geprüft …"))

            def job():
                content, _digest, metrics = read_local_garmin_fit(candidate_path)
                match = match_local_garmin_fit(self.workout, metrics)
                candidate = {
                    "name": self.app.tr("Lokale Garmin-FIT"),
                    "start": match["start"].isoformat(),
                    "start_delta_sec": match["start_delta_seconds"],
                    "duration_sec": match["garmin_duration_seconds"],
                }
                return content, candidate

            def done(result):
                content, candidate = result
                self.local_fit_bytes = content
                self._show_matches([candidate], "file")
                logger.info(
                    "Local Garmin FIT validated: source=file records=unknown "
                    "start_delta_sec=%d",
                    candidate["start_delta_sec"],
                )

            self.app.run_job(job, done)
            return

        key = self.key.get().strip()
        if not key:
            messagebox.showinfo(
                self.app.tr("Garmin API-Schlüssel"),
                self.app.tr("Bitte einen persönlichen Garmin-API-Schlüssel eingeben."),
                parent=self,
            )
            return
        try:
            if self.remember_key.get():
                save_garmin_api_key(key)
            else:
                delete_garmin_api_key()
        except (OSError, ValueError, RuntimeError):
            messagebox.showerror(
                self.app.tr("Garmin-Schlüssel"),
                self.app.tr("Der Garmin-Schlüssel konnte nicht geschützt gespeichert werden."),
                parent=self,
            )
            return
        self._reset_search()
        client = GarminPersonalClient(key)
        self.key.set("")
        self.garmin_client = client
        self.search_status.set(self.app.tr("Suche läuft …"))

        def job():
            day = date.fromisoformat(str(self.workout["day"])[:10])
            rows = client.activities(day - timedelta(days=1),
                                     day + timedelta(days=1))
            return match_activities(self.workout, rows)

        def done(candidates):
            self._show_matches(candidates, "api")

        self.app.run_job(job, done)

    def save_merge(self):
        if self.app.busy or self.source_verified != self.source_choice.get():
            return
        if self.source_verified == "file" and self.local_fit_bytes is None:
            return
        if self.source_verified == "api" and self.garmin_client is None:
            return
        selected = self.match_combo.current()
        if selected < 0 or selected >= len(self.candidates):
            messagebox.showinfo(
                self.app.tr("Garmin-Aktivität auswählen"),
                self.app.tr("Bitte zuerst die passende Garmin-Aktivität auswählen."),
                parent=self,
            )
            return
        try:
            priority = self._selected_priorities()
            save_merge_priorities(priority)
        except (OSError, ValueError):
            messagebox.showerror(
                self.app.tr("Einstellungen"),
                self.app.tr("Datenpriorität konnte nicht gespeichert werden."),
                parent=self,
            )
            return
        filename = "%s_Speediance_Garmin_MERGED.fit" % str(self.workout["day"])[:10]
        target = filedialog.asksaveasfilename(
            parent=self,
            title=self.app.tr("Neue zusammengeführte FIT-Datei speichern"),
            defaultextension=".fit",
            initialfile=filename,
            filetypes=[("Garmin FIT", "*.fit")],
        )
        if not target:
            return
        path = Path(target)
        original_path = self.local_file_path.get()
        if original_path and path.resolve() == Path(original_path).resolve():
            messagebox.showerror(
                self.app.tr("Originaldatei schützen"),
                self.app.tr("Die neue Datei darf die Original-FIT nicht überschreiben."),
                parent=self,
            )
            return
        candidate = self.candidates[selected]
        client = self.garmin_client
        local_fit = self.local_fit_bytes
        source = self.source_verified
        confirmed_gm = self.gm_manager_import
        gm_history = self.gm_history_import
        def job():
            # The Garmin original is either the local verified FIT or the
            # authenticated Personal API download. Sets come from the normal
            # Speediance completed-session API/cache, or explicitly from a
            # user-confirmed GM Manager JSON as an opt-in alternative.
            fit = (local_fit if source == "file"
                   else client.download_activity_fit(candidate["id"]))
            if gm_history is not None:
                # Completed GM Manager history rows, matched on day and title.
                # Do not use set-volume ratios to change measured resistance.
                detail = dict(
                    self.workout,
                    exercises=gm_history["exercises"],
                    unit=gm_history["unit"],
                    heart_rate_points=[],
                    heart_rate_summary={},
                    _set_source="gm_manager_history_csv",
                )
            elif confirmed_gm is not None:
                # The user confirmed the exported values match this completed
                # session. Do not pretend the plan file is API telemetry.
                # Garmin's genuine HR and device records remain the base.
                detail = dict(
                    self.workout,
                    exercises=resolve_exercise_names(self.app.client, confirmed_gm),
                    unit=confirmed_gm["unit"],
                    heart_rate_points=[],
                    heart_rate_summary={},
                    _set_source="gm_manager_confirmed",
                )
            else:
                detail = details_or_history(self.app.client, self.workout)
            expected_sets = (
                gm_history["set_count"] if gm_history is not None
                else confirmed_gm["set_count"] if confirmed_gm is not None
                else None
            )
            try:
                result, meta = overlay_garmin_fit(
                    fit, detail, path, priority,
                    overrides=saved_mappings(),
                    weight_overrides=saved_weight_multipliers(),
                    expected_set_count=expected_sets,
                )
            except ValueError:
                # Do not reduce a real export failure to the useless dialog
                # "ValueError". Avoid exposing private timestamp values.
                raise GarminOverlayError(
                    "Ungültige FIT-Satzdaten oder Zeitzuordnung. "
                    "Es wurde keine zusammengeführte FIT-Datei erzeugt."
                ) from None
            if meta["new_speediance_sets"] <= 0 or (
                expected_sets is not None
                and meta["new_speediance_sets"] != expected_sets
            ):
                # Defense in depth: never report a successful Garmin-only
                # file when a set source was selected.
                raise GarminOverlayError(
                    "Zusammenführung abgebrochen: Keine gültige "
                    "Satzübernahme in die FIT-Datei"
                )
            return result, meta

        def done(result):
            output, meta = result
            logger.info(
                "Local Garmin-Speediance merge saved: heart_points=%d "
                "garmin_hr=%d speediance_hr=%d out_of_window=%d "
                "duration_seconds=%d garmin_original=%d preserved_types=%d "
                "native_device_info=%d speediance_sets=%d replaced_native_sets=%d "
                "hr_records_added=%d hr_records_patched=%d set_source=%s "
                "estimated_set_timing_aligned_to_garmin=%s",
                meta["samples"], meta["garmin_samples"],
                meta["speediance_samples"], meta["out_of_window_samples"],
                meta["duration_seconds"],
                meta["garmin_original_messages"],
                meta["garmin_preserved_message_types"],
                meta["garmin_device_info"],
                meta["new_speediance_sets"],
                meta["replaced_garmin_sets"],
                meta["added_hr_records"],
                meta["patched_hr_records"],
                meta["speediance_source"],
                meta["set_timing_aligned_to_activity_start"],
            )
            timing_note = (
                self.app.tr(
                    "Hinweis: Das Speediance-Training begann vor der Garmin-Aufzeichnung. "
                    "Die geschätzten Satzanfänge wurden auf den Garmin-Trainingsbeginn "
                    "ausgerichtet; originale Garmin-Messpunkte bleiben unverändert.\n\n"
                ) if meta["set_timing_aligned_to_activity_start"] else ""
            )
            source_note = (
                self.app.tr("Satzquelle: GM-Manager-Workout-History-CSV. "
                            "Satzdauern vorhanden, Satzanfangszeiten geschätzt.\n\n")
                if meta.get("speediance_source") == "gm_manager_history_csv"
                else self.app.tr("Satzquelle: vom Nutzer bestätigter GM-Manager-Export. "
                                 "Satzzeitpunkte sind geschätzt.\n\n")
                if meta.get("speediance_source") == "gm_manager_confirmed" else ""
            )
            messagebox.showinfo(
                self.app.tr("Zusammenführung abgeschlossen"),
                source_note + timing_note + self.app.tr("Garmin-originalbasierte FIT-Datei gespeichert:\n%s\n\n"
                            "Importierte Übungssätze: %d\n"
                            "Erhaltene Garmin-Sätze: %d\n"
                            "Garmin-Geräteinformationen erhalten: %d\n"
                            "Zusätzliche HF-Records: %d\n"
                            "Außerhalb der gewählten Dauer: %d\n\n"
                            "Garmin Connect wurde NICHT verändert.") %
                (str(output), meta["new_speediance_sets"],
                 meta["preserved_native_sets"], meta["garmin_device_info"], meta["added_hr_records"],
                 meta["out_of_window_samples"]),
                parent=self,
            )

        self.app.run_job(job, done)
