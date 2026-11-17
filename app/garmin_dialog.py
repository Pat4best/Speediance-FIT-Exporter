"""Optional user-confirmed Garmin Personal API activity match and local FIT merge."""
from datetime import date, timedelta
from pathlib import Path
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from fitwriter import write_fit
from garmin_fit_overlay import overlay_garmin_fit, GarminOverlayError
from garmin_merge import PRIORITY_LABELS, check_priorities
from garmin_personal import GarminPersonalClient, GarminPersonalError, match_activities
from preferences import (saved_mappings, saved_weight_multipliers,
                         saved_merge_priorities, save_merge_priorities)
from windows_credentials import (save_garmin_api_key, load_garmin_api_key,
                                 delete_garmin_api_key)

logger = logging.getLogger("speediance_fit")
API_KEY_PAGE = "https://connect.garmin.com/app/settings/personalApiToken"


class GarminMergeDialog(tk.Toplevel):
    def __init__(self, app, workout):
        super().__init__(app)
        self.app = app
        self.workout = workout
        self.detail = None
        self.candidates = []
        self.garmin_client = None
        self.title(app.tr("Garmin Personal API – Abgleich und FIT-Merge"))
        self.transient(app)
        w = min(790, max(600, app.winfo_screenwidth() - 80))
        h = min(640, max(530, app.winfo_screenheight() - 110))
        self.geometry("%dx%d" % (w, h))
        self.minsize(600, 530)
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
            "Krafttrainingssätze werden ergänzt. Online bleibt alles unverändert."
        ), wraplength=745).pack(anchor="w", pady=(3, 10))

        credentials = ttk.LabelFrame(outer, text=tr("1 – Persönlicher Garmin-API-Schlüssel"),
                                     padding=8)
        credentials.pack(fill="x")
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
            "Übungen, Sätze, Wiederholungen und tatsächliche Gewichte: immer Speediance. "
            "Fehlende Messwerte können aus der jeweils anderen Quelle ergänzt werden."
        ), wraplength=730, foreground="#555").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))

        matched = ttk.LabelFrame(outer, text=tr("3 – Passende Garmin-Aktivität wählen"),
                                 padding=8)
        matched.pack(fill="x", pady=(10, 0))
        search_row = ttk.Frame(matched)
        search_row.pack(fill="x")
        self.search_button = ttk.Button(
            search_row, text=tr("Garmin-Aktivitäten suchen"), command=self.search)
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

    def search(self):
        if self.app.busy:
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
        self.garmin_client = GarminPersonalClient(key)
        self.key.set("")
        self.detail = None
        self.candidates = []
        self.match_combo["values"] = ()
        self.match_combo.set("")
        self.merge_button.state(["disabled"])
        self.search_status.set(self.app.tr("Suche läuft …"))
        selected = self.workout
        client = self.garmin_client

        def job():
            # Get actual completed sets before matching session duration.
            detailed = self.app.client.detail(selected)
            day = date.fromisoformat(str(selected["day"])[:10])
            rows = client.activities(day - timedelta(days=1),
                                     day + timedelta(days=1))
            return detailed, match_activities(detailed, rows)

        def done(result):
            self.detail, self.candidates = result
            if not self.candidates:
                self.search_status.set(self.app.tr("Keine zeitlich passende Garmin-Aktivität gefunden."))
                messagebox.showinfo(
                    self.app.tr("Kein eindeutiger Treffer"),
                    self.app.tr("Keine Garmin-Aktivität passt zeitlich ausreichend. "
                                "Es wurde keine FIT-Datei erstellt."),
                    parent=self,
                )
                return
            values = []
            for candidate in self.candidates:
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
            self.merge_button.state(["!disabled"])

        self.app.run_job(job, done)

    def save_merge(self):
        if self.app.busy or self.detail is None or self.garmin_client is None:
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
        candidate = self.candidates[selected]
        client = self.garmin_client
        detail = self.detail

        def job():
            fit = client.download_activity_fit(candidate["id"])
            result, meta = overlay_garmin_fit(
                fit, detail, path, priority,
                overrides=saved_mappings(),
                weight_overrides=saved_weight_multipliers(),
            )
            return result, meta

        def done(result):
            output, meta = result
            logger.info(
                "Local Garmin-Speediance merge saved: heart_points=%d "
                "garmin_hr=%d speediance_hr=%d out_of_window=%d "
                "duration_seconds=%d garmin_original=%d preserved_types=%d "
                "native_device_info=%d speediance_sets=%d replaced_native_sets=%d "
                "hr_records_added=%d hr_records_patched=%d",
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
            )
            messagebox.showinfo(
                self.app.tr("Zusammenführung abgeschlossen"),
                self.app.tr("Garmin-originalbasierte FIT-Datei gespeichert:\n%s\n\n"
                            "Speediance-Krafttrainingssätze: %d\n"
                            "Garmin-Geräteinformationen erhalten: %d\n"
                            "Zusätzliche HF-Records: %d\n"
                            "Außerhalb der gewählten Dauer: %d\n\n"
                            "Garmin Connect wurde NICHT verändert.") %
                (str(output), meta["new_speediance_sets"],
                 meta["garmin_device_info"], meta["added_hr_records"],
                 meta["out_of_window_samples"]),
                parent=self,
            )

        self.app.run_job(job, done)
