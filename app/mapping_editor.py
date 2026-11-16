"""Desktop dialog for editing local Speediance-to-Garmin exercise mappings."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from exercise_mapping import fit_exercise
from garmin_catalog import GARMIN_OPTIONS
from preferences import observed_names, remember_names, saved_mappings, set_override


class MappingEditor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Speediance-Übungen zuordnen")
        self.geometry("810x530")
        self.minsize(650, 440)
        self.transient(parent)
        self.grab_set()
        self.names = observed_names()
        self.selected_name = None
        self._build()
        self.refresh()

    def _build(self):
        frame = ttk.Frame(self, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Speediance → Garmin: Übungszuordnung",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(frame,
                  text="Wähle links eine erkannte Speediance-Übung und ordne ihr rechts die "
                       "passende Garmin-Übung zu. Unbekannte Übungsnamen erscheinen nach dem Export.").pack(
            anchor="w", pady=(0, 10))

        table_area = ttk.Frame(frame)
        table_area.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_area, columns=("name", "mapped"),
                                  show="headings", selectmode="browse")
        self.table.heading("name", text="Speediance-Übung")
        self.table.heading("mapped", text="Garmin-Zuordnung")
        self.table.column("name", width=270)
        self.table.column("mapped", width=410)
        self.table.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(table_area, orient="vertical", command=self.table.yview)
        bar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=bar.set)
        self.table.bind("<<TreeviewSelect>>", self.select)

        inputs = ttk.LabelFrame(frame, text="Zuordnung bearbeiten", padding=10)
        inputs.pack(fill="x", pady=(10, 6))
        self.current = tk.StringVar(value="Noch keine Übung ausgewählt")
        ttk.Label(inputs, textvariable=self.current).pack(anchor="w", pady=(0, 6))
        line = ttk.Frame(inputs)
        line.pack(fill="x")
        ttk.Label(line, text="Garmin-Übung").pack(side="left")
        self.garmin_choice = tk.StringVar()
        self.option = ttk.Combobox(line, textvariable=self.garmin_choice,
                                   state="readonly", width=46,
                                   values=sorted(GARMIN_OPTIONS))
        self.option.pack(side="left", padx=(7, 10))
        self.option.bind("<<ComboboxSelected>>", self.select_option)
        ttk.Label(line, text="Kategorie").pack(side="left")
        self.category = tk.StringVar()
        ttk.Entry(line, textvariable=self.category, width=5).pack(side="left", padx=4)
        ttk.Label(line, text="ID").pack(side="left")
        self.subtype = tk.StringVar()
        ttk.Entry(line, textvariable=self.subtype, width=5).pack(side="left", padx=4)

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(4, 4))
        ttk.Button(controls, text="Übungsname hinzufügen…", command=self.add_name).pack(
            side="left")
        ttk.Button(controls, text="Zuordnung entfernen", command=self.remove).pack(
            side="left", padx=8)
        ttk.Button(controls, text="Zuordnung speichern", command=self.save).pack(
            side="left")
        ttk.Button(controls, text="Schließen", command=self.destroy).pack(side="right")

        ttk.Label(frame, text="Die Liste ist eine Auswahl bekannter Garmin-Übungen. "
                  "Andere gültige FIT-Kategorie/ID-Paare können rechts eingegeben werden. "
                  "Änderungen werden nur auf diesem Computer gespeichert.",
                  foreground="#555", wraplength=760).pack(anchor="w", pady=(8, 0))

    def refresh(self, selected=None):
        overrides = saved_mappings()
        existing = list(self.table.get_children())
        if existing:
            self.table.delete(*existing)
        for i, name in enumerate(self.names):
            category, subtype = fit_exercise(name, overrides=overrides)
            label = next((k for k, v in GARMIN_OPTIONS.items()
                          if v == (category, subtype)), "")
            if not label and subtype is not None:
                label = "Kategorie %d / ID %d" % (category, subtype)
            self.table.insert("", "end", iid=str(i),
                              values=(name, label or "Keine Zuordnung"))
        if selected in self.names:
            row = str(self.names.index(selected))
            self.table.selection_set(row)
            self.table.see(row)
            self.select()

    def select(self, event=None):
        choice = self.table.selection()
        if not choice:
            self.selected_name = None
            return
        name = self.names[int(choice[0])]
        self.selected_name = name
        self.current.set(name)
        category, subtype = fit_exercise(name, overrides=saved_mappings())
        self.category.set(str(category) if subtype is not None else "")
        self.subtype.set(str(subtype) if subtype is not None else "")
        known = next((k for k, v in GARMIN_OPTIONS.items()
                      if v == (category, subtype)), "")
        self.garmin_choice.set(known)

    def select_option(self, event=None):
        option = self.garmin_choice.get()
        if option in GARMIN_OPTIONS:
            category, subtype = GARMIN_OPTIONS[option]
            self.category.set(str(category))
            self.subtype.set(str(subtype))

    def add_name(self):
        name = simpledialog.askstring("Speediance-Übung", "Name der Speediance-Übung:",
                                      parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        remember_names([name])
        self.names = observed_names()
        self.refresh(selected=name)

    def save(self):
        name = self.selected_name
        if not name:
            messagebox.showinfo("Zuordnung", "Bitte zuerst eine Übung auswählen.", parent=self)
            return
        try:
            cat = int(self.category.get())
            subtype = int(self.subtype.get())
            set_override(name, cat, subtype)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Ungültige Zuordnung",
                                 "Bitte gültige Ganzzahlen für Garmin-Kategorie und ID eingeben.\n"
                                 + str(exc), parent=self)
            return
        self.refresh(selected=name)
        messagebox.showinfo("Zuordnung", "Zuordnung lokal gespeichert. "
                            "Für Garmin bitte FIT-Dateien erneut exportieren.", parent=self)

    def remove(self):
        if not self.selected_name:
            return
        try:
            set_override(self.selected_name, None, None)
        except (ValueError, OSError):
            messagebox.showerror("Zuordnung", "Zuordnung konnte nicht gelöscht werden.",
                                 parent=self)
            return
        self.refresh(selected=self.selected_name)
