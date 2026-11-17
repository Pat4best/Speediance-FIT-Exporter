"""Local Windows desktop interface for Speediance cloud -> Garmin FIT."""
from datetime import date, timedelta
from pathlib import Path
import logging
import os
import queue
import re
import shutil
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from speediance_api import Client
from fitwriter import write_fit
from exercise_mapping import fit_exercise
from windows_credentials import load_login, save_login, delete_login
from preferences import export_folder, save_export_folder, saved_mappings, remember_names, load_login_client_type, save_login_client_type
from mapping_editor import MappingEditor
from exercise_discovery import discover_names

APP = "Speediance FIT Exporter"
VERSION = "0.1.7-beta"
DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SpeedianceFITExporter"
DATA.mkdir(parents=True, exist_ok=True)
LOG = DATA / "diagnose.log"


class SafeFormatter(logging.Formatter):
    def format(self, record):
        line = super().format(record)
        line = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[E-MAIL]", line)
        line = re.sub(r"(?i)(bearer\s+)[a-z0-9._-]+", r"\1[REDACTED]", line)
        line = re.sub(r"(?i)((?:token|password|secret|authorization)[\s:=]+)[^\s,;}]+",
                      r"\1[REDACTED]", line)
        return line


logger = logging.getLogger("speediance_fit")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG, encoding="utf-8", mode="w")
handler.setFormatter(SafeFormatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.info("Application started version=%s platform=%s", VERSION, sys.platform)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP + " – " + VERSION)
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d" % (min(1080, max(720, screen_w - 60)),
                                 min(770, max(460, screen_h - 100))))
        self.minsize(720, 460)
        self.client = None
        self.sessions = []
        self.events = queue.Queue()
        self.busy = False
        self.save_login_var = tk.BooleanVar(value=False)
        self.login_client_type = tk.StringVar(value=load_login_client_type())
        self.export_dir = tk.StringVar(value=export_folder())
        self.build_ui()
        self._load_remembered_login()
        self.after(100, self.poll)

    def build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        # Reserve the footer before packing the resizable workout list.
        # This keeps actions visible on high-DPI and laptop displays.
        footer = ttk.Frame(root)
        footer.pack(side="bottom", fill="x")
        body = ttk.Frame(root)
        body.pack(side="top", fill="both", expand=True)
        ttk.Label(body, text=APP, font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(body, text="Workouts aus deinem Speediance-Account als Garmin-FIT exportieren").pack(
            anchor="w", pady=(2, 8))

        login = ttk.LabelFrame(body, text="1 – Speediance-Anmeldung", padding=8)
        login.pack(fill="x")
        line = ttk.Frame(login)
        line.pack(fill="x")
        ttk.Label(line, text="E-Mail").pack(side="left")
        self.email = tk.StringVar()
        ttk.Entry(line, textvariable=self.email, width=28).pack(side="left", padx=(5, 12))
        ttk.Label(line, text="Passwort").pack(side="left")
        self.password = tk.StringVar()
        ttk.Entry(line, textvariable=self.password, show="●", width=22).pack(side="left", padx=5)
        self.region = tk.StringVar(value="EU")
        ttk.Combobox(line, textvariable=self.region, values=["EU", "Global"],
                     state="readonly", width=8).pack(side="left", padx=7)
        self.login_button = ttk.Button(line, text="Anmelden", command=self.login)
        self.login_button.pack(side="right")
        self.login_status = tk.StringVar(value="● Nicht angemeldet")
        self.login_status_label = ttk.Label(
            login, textvariable=self.login_status, foreground="#9a3412"
        )
        self.login_status_label.pack(anchor="w", pady=(4, 0))
        login_options = ttk.Frame(login)
        login_options.pack(fill="x", pady=(8, 0))
        ttk.Checkbutton(login_options, text="Anmeldedaten auf diesem PC speichern",
                        variable=self.save_login_var).pack(side="left")
        ttk.Button(login_options, text="Gespeicherte Anmeldung löschen",
                   command=self.clear_saved_login).pack(side="right")
        slot_row = ttk.Frame(login)
        slot_row.pack(fill="x", pady=(6, 0))
        ttk.Label(slot_row, text="Anmeldetyp (Sitzungsplatz):").pack(side="left")
        ttk.Combobox(slot_row, textvariable=self.login_client_type,
                     values=["bike", "nano", "phone"], width=12,
                     state="readonly").pack(side="left", padx=(8, 12))
        ttk.Label(slot_row, text="bike empfohlen, wenn kein Speediance Bike vorhanden; "
                  "sonst nano wählen.",
                  foreground="#555").pack(side="left")
        ttk.Label(login, text="Achtung: 'phone' meldet die iOS-App ab. "
                  "'bike'/'nano' können ein Gerät desselben Typs abmelden. "
                  "Passwortspeicherung optional im Windows-Anmeldeinformationsmanager.",
                  foreground="#8a4800", wraplength=810).pack(anchor="w", pady=(6, 0))

        controls = ttk.LabelFrame(body, text="2 – Trainingshistorie", padding=8)
        controls.pack(fill="x", pady=6)
        row = ttk.Frame(controls)
        row.pack(fill="x")
        today = date.today()
        self.from_date = tk.StringVar(value=(today - timedelta(days=60)).isoformat())
        self.to_date = tk.StringVar(value=today.isoformat())
        ttk.Label(row, text="Von (JJJJ-MM-TT)").pack(side="left")
        ttk.Entry(row, textvariable=self.from_date, width=13).pack(side="left", padx=6)
        ttk.Label(row, text="Bis").pack(side="left")
        ttk.Entry(row, textvariable=self.to_date, width=13).pack(side="left", padx=6)
        self.fetch_button = ttk.Button(row, text="Trainings laden", command=self.fetch)
        self.fetch_button.pack(side="left", padx=10)

        content = ttk.Frame(body)
        content.pack(fill="both", expand=True)
        self.table = ttk.Treeview(content, columns=("day", "title", "minutes", "kcal"),
                                  show="headings", selectmode="extended")
        for col, title, width in [
            ("day", "Datum", 105), ("title", "Training", 380),
            ("minutes", "Minuten", 85), ("kcal", "kcal", 70)
        ]:
            self.table.heading(col, text=title)
            self.table.column(col, width=width, stretch=col == "title")
        self.table.pack(side="left", fill="both", expand=True)
        scroller = ttk.Scrollbar(content, command=self.table.yview)
        scroller.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scroller.set)

        folder_row = ttk.Frame(footer)
        folder_row.pack(fill="x", pady=(6, 0))
        ttk.Label(folder_row, text="Exportordner: ").pack(side="left")
        ttk.Label(folder_row, textvariable=self.export_dir, width=60).pack(
            side="left", padx=(5, 8), fill="x", expand=True)
        ttk.Button(folder_row, text="Ordner auswählen…",
                   command=self.choose_export_dir).pack(side="right")

        actions = ttk.Frame(footer)
        actions.pack(fill="x", pady=(6, 0))
        self.export_button = ttk.Button(actions, text="Ausgewählte als .fit exportieren",
                                         command=self.export)
        self.export_button.pack(side="left")
        self.mapping_button = ttk.Button(actions, text="Übungen zuordnen…",
                                         command=self.manage_mappings)
        self.mapping_button.pack(side="left", padx=(10, 0))
        ttk.Button(actions, text="Diagnose-Ordner öffnen", command=self.open_log_dir).pack(
            side="right")
        ttk.Button(actions, text="Diagnoseprotokoll speichern…",
                   command=self.save_log).pack(side="right", padx=8)
        self.status = tk.StringVar(value="Bereit. Bitte anmelden.")
        ttk.Label(footer, textvariable=self.status).pack(anchor="w", pady=(6, 0))
        ttk.Label(footer, text="FIT-Aktivitätsimport, kein Garmin-Trainingsplan. Fehlende Satzzeiten werden geschätzt.",
                  foreground="#666").pack(anchor="w", pady=(2, 0))

    def _load_remembered_login(self):
        try:
            saved = load_login()
        except Exception as exc:
            logger.warning("Windows credentials read failed: %s", type(exc).__name__)
            return
        if saved:
            email, password, region = saved
            self.email.set(email)
            self.password.set(password)
            self.region.set(region)
            self.save_login_var.set(True)
            self.login_status.set("● Nicht angemeldet – Zugangsdaten vorausgefüllt")
            self.status.set("Gespeicherte Anmeldung geladen. Zum Verbinden auf Anmelden klicken.")

    def clear_saved_login(self):
        if not messagebox.askyesno("Anmeldedaten löschen",
                                   "Gespeicherte Speediance-Zugangsdaten von diesem PC löschen?"):
            return
        try:
            delete_login()
        except Exception as exc:
            logger.warning("Windows credential deletion failed: %s", type(exc).__name__)
            messagebox.showerror("Anmeldedaten", "Löschen im Windows-Anmeldeinformationsmanager fehlgeschlagen.")
            return
        self.email.set("")
        self.password.set("")
        self.save_login_var.set(False)
        self.login_status.set("● Angemeldet" if self.client is not None else "● Nicht angemeldet")
        self.status.set("Gespeicherte Anmeldung gelöscht. Bestehende Sitzung bleibt angemeldet.")

    def choose_export_dir(self):
        current = self.export_dir.get()
        initial = current if current and Path(current).is_dir() else str(Path.home())
        folder = filedialog.askdirectory(title="Exportordner auswählen", initialdir=initial)
        if not folder:
            return None
        try:
            save_export_folder(folder)
        except (ValueError, OSError) as exc:
            logger.warning("Export directory preferences failed: %s", type(exc).__name__)
            messagebox.showerror("Exportordner", "Ordner konnte nicht gespeichert werden.")
            return None
        self.export_dir.set(folder)
        self.status.set("Exportordner gespeichert.")
        return folder

    def manage_mappings(self):
        """Load names from marked Speediance workouts before showing the editor.

        If no workout is selected, show already discovered names. Never open a
        silently empty editor when no exercises have been collected yet.
        """
        if self.busy:
            return
        indices = [int(i) for i in self.table.selection()]
        if not indices:
            from preferences import observed_names
            if observed_names():
                MappingEditor(self)
            else:
                messagebox.showinfo(
                    "Übungen zuordnen",
                    "Bitte zuerst ein oder mehrere Trainings in der Liste markieren. "
                    "Danach lädt das Programm ihre Übungen direkt aus Speediance."
                )
            return
        if self.client is None:
            messagebox.showinfo("Speediance-Anmeldung", "Bitte zuerst anmelden.")
            return
        selected = [self.sessions[i] for i in indices]

        def work():
            return discover_names(self.client, selected, logger=logger)

        def done(result):
            names, failures = result
            if names:
                try:
                    remember_names(names)
                except OSError as exc:
                    logger.warning("Could not save detected exercise names (%s)",
                                   type(exc).__name__)
                    messagebox.showwarning(
                        "Übungsnamen", "Die Übungen wurden geladen, können aber "
                        "möglicherweise nicht dauerhaft gespeichert werden."
                    )
                self.status.set("%d Übungen aus %d gewählten Training(s) geladen." %
                                (len(names), len(selected)))
                MappingEditor(self, names=names)
                if failures:
                    messagebox.showwarning(
                        "Unvollständige Übungsliste",
                        "%d gewählte Trainingseinheit(en) konnten nicht vollständig "
                        "gelesen werden. Details stehen im Diagnoseprotokoll." % failures,
                        parent=self,
                    )
            else:
                self.status.set("Für die markierten Trainings wurden keine Übungen geladen.")
                messagebox.showwarning(
                    "Keine Übungen abrufbar",
                    "Speediance hat für die markierten Trainings keine Übungen geliefert. "
                    "Prüfe das Diagnoseprotokoll. Der Zuordnungsdialog wird deshalb "
                    "nicht leer geöffnet."
                )

        self.run_job(work, done)

    def run_job(self, action, callback):
        if self.busy:
            return
        self.busy = True
        self.status.set("Arbeite …")
        for button in (self.login_button, self.fetch_button, self.export_button, self.mapping_button):
            button.state(["disabled"])

        def worker():
            try:
                self.events.put(("ok", callback, action()))
            except Exception as exc:
                # Never include arbitrary exception text in shareable diagnostics.
                logger.error("Action failed: %s", type(exc).__name__)
                # Our own APIError strings contain routes/error codes, not response bodies.
                from speediance_api import APIError
                display = str(exc) if isinstance(exc, APIError) else type(exc).__name__
                self.events.put(("error", display, None))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, callback, value = self.events.get_nowait()
                self.busy = False
                for button in (self.login_button, self.fetch_button, self.export_button, self.mapping_button):
                    button.state(["!disabled"])
                if kind == "ok":
                    callback(value)
                else:
                    self.status.set("Fehler. Diagnoseprotokoll kann gespeichert werden.")
                    if self.login_status.get().startswith("● Anmeldung läuft"):
                        self.login_status.set("● Nicht angemeldet – Anmeldung fehlgeschlagen")
                        self.login_status_label.configure(foreground="#9a3412")
                    messagebox.showerror("Fehler", callback)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def login(self):
        email = self.email.get().strip()
        password = self.password.get()
        if not email or not password:
            messagebox.showinfo("Anmeldung", "Bitte E-Mail und Passwort eingeben.")
            return
        region = self.region.get()
        login_slot = self.login_client_type.get()
        if login_slot == "phone" and not messagebox.askyesno(
            "Achtung: iOS-App wird abgemeldet",
            "Der Typ 'phone' verwendet den gleichen Speediance-Sitzungsplatz wie "
            "deine iOS-App. Das kann deine iOS-App sofort abmelden. "
            "Trotzdem mit 'phone' anmelden?"
        ):
            return

        def job():
            client = Client(logger, region=region, login_client_type=login_slot)
            client.login(email, password)
            return client

        def done(client):
            self.client = client
            self.login_status.set("● Angemeldet (Speediance, %s)" % login_slot)
            self.login_status_label.configure(foreground="#23754a")
            try:
                save_login_client_type(login_slot)
            except OSError as exc:
                logger.warning("Saving login client setting failed: %s", type(exc).__name__)
            if self.save_login_var.get():
                try:
                    save_login(email, password, region)
                except Exception as exc:
                    logger.warning("Windows credential save failed: %s", type(exc).__name__)
                    messagebox.showwarning(
                        "Anmeldedaten",
                        "Login erfolgreich, aber Speichern im Windows-Anmeldeinformationsmanager fehlgeschlagen."
                    )
            else:
                try:
                    delete_login()
                except Exception as exc:
                    logger.warning("Windows credential deletion failed: %s", type(exc).__name__)
            self.password.set("")
            self.status.set("Angemeldet. Jetzt Trainings laden.")

        self.client = None
        self.login_status.set("● Anmeldung läuft …")
        self.status.set("Anmeldung wird geprüft …")
        self.run_job(job, done)

    def fetch(self):
        if self.client is None:
            messagebox.showinfo("Anmeldung", "Bitte zuerst anmelden.")
            return
        try:
            start = date.fromisoformat(self.from_date.get())
            end = date.fromisoformat(self.to_date.get())
            if end < start or (end - start).days > 366 * 3:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Datum", "Bitte gültigen Zeitraum bis zu 3 Jahren wählen.")
            return

        def done(items):
            self.sessions = items
            for row in self.table.get_children():
                self.table.delete(row)
            for i, item in enumerate(items):
                self.table.insert("", "end", iid=str(i), values=(
                    item["day"], item["title"], item["duration_min"], item["calories"]
                ))
            recovered = getattr(self.client, "calendar_fallback_added", 0)
            other_device = getattr(self.client, "calendar_other_device_added", 0)
            self.status.set(
                "%d abgeschlossene Workouts geladen (frühere API: +%d; anderer Gerätetyp: +%d)." %
                (len(items), recovered, other_device)
            )

        self.run_job(lambda: self.client.list_workouts(start, end), done)

    def export(self):
        indices = [int(i) for i in self.table.selection()]
        if not indices:
            messagebox.showinfo("Auswahl", "Bitte mindestens ein Workout markieren.")
            return
        folder = self.export_dir.get()
        if not folder or not Path(folder).is_dir():
            folder = self.choose_export_dir()
        if not folder:
            return
        selected = [self.sessions[i] for i in indices]

        def job():
            successes = []
            failures = 0
            overrides = saved_mappings()
            not_mapped = set()
            missing_details = 0
            for item in selected:
                try:
                    detailed = self.client.detail(item)
                    names = [ex.get("name") or "Unbekannt" for ex in detailed["exercises"]]
                    remember_names(names)
                    for name in names:
                        if fit_exercise(name, overrides=overrides)[1] is None:
                            not_mapped.add(name)
                    safe_name = re.sub(r"[^\w -]+", "_", item["title"]).strip(" _")[:60] or "Training"
                    filename = "%s_%s_%s.fit" % (item["day"], safe_name, item["training_id"])
                    successes.append(write_fit(detailed, Path(folder) / filename,
                                               overrides=overrides))
                except Exception as exc:
                    logger.warning("FIT export failed: %s", type(exc).__name__)
                    from speediance_api import APIError
                    if isinstance(exc, APIError) and ("keine Übungsdetails" in str(exc)
                                                     or "keine Sätze" in str(exc)):
                        missing_details += 1
                    failures += 1
            return successes, failures, len(not_mapped), missing_details

        def done(result):
            successes, failures, unknown_count, missing_details = result
            self.status.set("%d exportiert, %d Fehler, %d ohne Garmin-Zuordnung." %
                            (len(successes), failures, unknown_count))
            message = "%d FIT-Dateien gespeichert. Fehler: %d" % (len(successes), failures)
            if unknown_count:
                message += ("\n%d Übungsnamen haben keine eindeutige Garmin-Zuordnung. "
                            "Die Originalnamen sind lokal für die Zuordnung gespeichert. "
                            "Klicke auf 'Übungen zuordnen…' und exportiere erneut.") % unknown_count
            if missing_details:
                message += ("\n%d Trainingseinheiten ohne Speediance-Satzdaten "
                            "wurden NICHT als leere FIT-Aktivitäten exportiert.") % missing_details
            messagebox.showinfo("Export", message)

        self.run_job(job, done)

    def save_log(self):
        target = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="speediance-diagnose.txt",
            filetypes=[("Textdatei", "*.txt")]
        )
        if target:
            handler.flush()
            shutil.copyfile(LOG, target)
            messagebox.showinfo("Diagnose", "Gespeichert. Bitte vor Weitergabe selbst prüfen.")

    def open_log_dir(self):
        try:
            os.startfile(str(DATA))
        except OSError:
            messagebox.showinfo("Diagnose", str(DATA))


if __name__ == "__main__":
    App().mainloop()
