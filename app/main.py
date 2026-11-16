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

APP = "Speediance FIT Exporter"
VERSION = "0.1.0-beta"
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
        self.geometry("900x650")
        self.minsize(780, 540)
        self.client = None
        self.sessions = []
        self.events = queue.Queue()
        self.busy = False
        self.build_ui()
        self.after(100, self.poll)

    def build_ui(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=APP, font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(root, text="Workouts aus deinem Speediance-Account als Garmin-FIT exportieren").pack(
            anchor="w", pady=(2, 15))

        login = ttk.LabelFrame(root, text="1 – Speediance-Anmeldung", padding=10)
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
        ttk.Label(login, text="Inoffizielle Schnittstelle. Passwort und Token werden nicht gespeichert.",
                  foreground="#666").pack(anchor="w", pady=(8, 0))

        controls = ttk.LabelFrame(root, text="2 – Trainingshistorie", padding=10)
        controls.pack(fill="x", pady=12)
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

        content = ttk.Frame(root)
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

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(12, 0))
        self.export_button = ttk.Button(actions, text="Ausgewählte als .fit exportieren",
                                         command=self.export)
        self.export_button.pack(side="left")
        ttk.Button(actions, text="Diagnose-Ordner öffnen", command=self.open_log_dir).pack(
            side="right")
        ttk.Button(actions, text="Diagnoseprotokoll speichern…",
                   command=self.save_log).pack(side="right", padx=8)
        self.status = tk.StringVar(value="Bereit. Bitte anmelden.")
        ttk.Label(root, textvariable=self.status).pack(anchor="w", pady=(12, 0))
        ttk.Label(root, text="FIT-Aktivitätsimport, kein Garmin-Trainingsplan. Fehlende Satzzeiten werden geschätzt.",
                  foreground="#666").pack(anchor="w", pady=(5, 0))

    def run_job(self, action, callback):
        if self.busy:
            return
        self.busy = True
        self.status.set("Arbeite …")
        for button in (self.login_button, self.fetch_button, self.export_button):
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
                for button in (self.login_button, self.fetch_button, self.export_button):
                    button.state(["!disabled"])
                if kind == "ok":
                    callback(value)
                else:
                    self.status.set("Fehler. Diagnoseprotokoll kann gespeichert werden.")
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

        def job():
            client = Client(logger, region=region)
            client.login(email, password)
            return client

        def done(client):
            self.client = client
            self.password.set("")
            self.status.set("Angemeldet. Jetzt Trainings laden.")

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
            self.status.set("%d abgeschlossene Workouts geladen." % len(items))

        self.run_job(lambda: self.client.list_workouts(start, end), done)

    def export(self):
        indices = [int(i) for i in self.table.selection()]
        if not indices:
            messagebox.showinfo("Auswahl", "Bitte mindestens ein Workout markieren.")
            return
        folder = filedialog.askdirectory(title="FIT-Exportordner auswählen")
        if not folder:
            return
        selected = [self.sessions[i] for i in indices]

        def job():
            successes = []
            failures = 0
            for item in selected:
                try:
                    detailed = self.client.detail(item)
                    safe_name = re.sub(r"[^\w -]+", "_", item["title"]).strip(" _")[:60] or "Training"
                    filename = "%s_%s_%s.fit" % (item["day"], safe_name, item["training_id"])
                    successes.append(write_fit(detailed, Path(folder) / filename))
                except Exception as exc:
                    logger.warning("FIT export failed: %s", type(exc).__name__)
                    failures += 1
            return successes, failures

        def done(result):
            successes, failures = result
            self.status.set("%d exportiert, %d Fehler." % (len(successes), failures))
            messagebox.showinfo("Export", "%d FIT-Dateien gespeichert. Fehler: %d" % (
                len(successes), failures))

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
