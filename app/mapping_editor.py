"""Searchable desktop dialog for local Speediance → Garmin FIT exercise mapping.

The full Garmin FIT exercise catalog is bundled offline (1,838 enum entries),
and the user can search by movement name and filter by exercise category.
The numeric FIT fields are read-only unless Advanced manual IDs is enabled.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from exercise_mapping import fit_exercise
from garmin_catalog import (
    FULL_CATALOG_COUNT, all_options, category_filters,
    category_title, normalize_query, search_options,
)
from preferences import (
    observed_names, remember_names, saved_mappings, set_override,
    load_catalog_language, save_catalog_language,
)
from i18n import translate


class MappingEditor(tk.Toplevel):
    def __init__(self, parent, names=None):
        super().__init__(parent)
        self.language = load_catalog_language()
        self.tr = lambda phrase: translate(self.language, phrase)
        self.language_choice = tk.StringVar(
            value="Deutsch" if self.language == "de" else "English"
        )
        self.title(self.tr("Speediance → Garmin: Übungszuordnung"))
        self.geometry("%dx%d" % (
            min(1160, parent.winfo_screenwidth() - 70),
            min(740, parent.winfo_screenheight() - 100),
        ))
        self.minsize(min(820, parent.winfo_screenwidth() - 70),
                     min(560, parent.winfo_screenheight() - 100))
        self.transient(parent)
        self.grab_set()

        self.names = sorted(set(names)) if names is not None else observed_names()
        self.visible_names = []
        self.selected_name = None
        self.result_rows = []

        self.left_search = tk.StringVar()
        self.query = tk.StringVar()
        self.category_choice = tk.StringVar()
        self.category = tk.StringVar()
        self.subtype = tk.StringVar()
        self.current = tk.StringVar(value=self.tr("Noch keine Übung ausgewählt"))
        self.assigned_label = tk.StringVar(value=self.tr("Noch keine Garmin-Übung gewählt"))
        self.result_count = tk.StringVar()
        self.manual_mode = tk.BooleanVar(value=False)

        self.filters = [(self.tr("Alle Kategorien"), None)] + list(
            category_filters(self.language)
        )
        self.filter_lookup = dict(self.filters)
        self.category_choice.set(self.filters[0][0])

        self._build()
        self._refresh_left()
        self._refresh_results()
        self.left_search.trace_add("write", lambda *_: self._refresh_left())
        self.query.trace_add("write", lambda *_: self._refresh_results())

    def _build(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        title_row = ttk.Frame(frame)
        title_row.pack(fill="x", pady=(0, 5))
        ttk.Label(title_row, text=self.tr("Speediance → Garmin: Übungszuordnung"),
                  font=("Segoe UI", 15, "bold")).pack(side="left")
        locale = ttk.Combobox(
            title_row, textvariable=self.language_choice,
            values=("Deutsch", "English"), state="readonly", width=11
        )
        locale.pack(side="right")
        locale.bind("<<ComboboxSelected>>", self.change_picker_language)
        ttk.Label(title_row, text=self.tr("Katalogsprache:")).pack(
            side="right", padx=(0, 6)
        )
        ttk.Label(
            frame,
            text=self.tr("Speediance-Übung links auswählen, rechts im vollständigen Garmin-Katalog suchen und die Zuordnung speichern."),
            wraplength=1030,
        ).pack(anchor="w", pady=(0, 8))

        content = ttk.Frame(frame)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=4)
        content.columnconfigure(1, weight=6)
        content.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(content, text=self.tr("Speediance-Übungen"), padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text=self.tr("Speediance-Namen filtern:")).grid(
            row=0, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.left_search).grid(
            row=1, column=0, sticky="ew", pady=(4, 8))

        left_table_frame = ttk.Frame(left)
        left_table_frame.grid(row=2, column=0, sticky="nsew")
        self.table = ttk.Treeview(
            left_table_frame, columns=("name", "mapped"),
            show="headings", selectmode="browse",
        )
        self.table.heading("name", text=self.tr("Speediance-Übung"))
        self.table.heading("mapped", text=self.tr("Garmin-Zuordnung"))
        self.table.column("name", width=235, minwidth=120, stretch=True)
        self.table.column("mapped", width=170, minwidth=90, stretch=True)
        self.table.pack(side="left", fill="both", expand=True)
        left_scroll = ttk.Scrollbar(left_table_frame, command=self.table.yview)
        left_scroll.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=left_scroll.set)
        self.table.bind("<<TreeviewSelect>>", self.select)

        ttk.Button(left, text=self.tr("Übungsname hinzufügen…"),
                   command=self.add_name).grid(row=3, column=0, sticky="w", pady=(8, 0))

        right = ttk.LabelFrame(content, text=self.tr("Garmin-Katalog durchsuchen"),
                               padding=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        ttk.Label(right, text=self.tr("Suchbegriff (z. B. Bankdrücken / bench, Kreuzheben / deadlift):")).grid(
            row=0, column=0, sticky="w")
        self.search_entry = ttk.Entry(right, textvariable=self.query)
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        ttk.Label(right, text=self.tr("Kategorie filtern:")).grid(
            row=2, column=0, sticky="w")
        combo = ttk.Combobox(
            right, textvariable=self.category_choice,
            values=[name for name, _ in self.filters], state="readonly",
        )
        combo.grid(row=3, column=0, sticky="ew", pady=(4, 6))
        combo.bind("<<ComboboxSelected>>", lambda event: self._refresh_results())

        results = ttk.Frame(right)
        results.grid(row=4, column=0, sticky="nsew")
        self.results_table = ttk.Treeview(results, columns=("exercise", "category"),
                                          show="headings", selectmode="browse")
        self.results_table.heading("exercise", text=self.tr("Garmin-Übung"))
        self.results_table.heading("category", text=self.tr("Kategorie"))
        self.results_table.column("exercise", width=365, minwidth=180, stretch=True)
        self.results_table.column("category", width=150, minwidth=95, stretch=True)
        self.results_table.pack(side="left", fill="both", expand=True)
        right_scroll = ttk.Scrollbar(results, command=self.results_table.yview)
        right_scroll.pack(side="right", fill="y")
        self.results_table.configure(yscrollcommand=right_scroll.set)
        self.results_table.bind("<<TreeviewSelect>>", self.choose_result)
        self.results_table.bind("<Double-1>", self.choose_result)

        ttk.Label(right, textvariable=self.result_count, foreground="#555").grid(
            row=5, column=0, sticky="w", pady=(6, 0))

        bottom = ttk.LabelFrame(frame, text=self.tr("Zuordnung bearbeiten"), padding=9)
        bottom.pack(fill="x", pady=(8, 0))
        ttk.Label(bottom, textvariable=self.current, font=("Segoe UI", 10, "bold")).pack(
            anchor="w")
        ttk.Label(bottom, textvariable=self.assigned_label).pack(
            anchor="w", pady=(2, 4))
        code_line = ttk.Frame(bottom)
        code_line.pack(fill="x")
        ttk.Label(code_line, text=self.tr("Kategorie (FIT):")).pack(side="left")
        self.category_entry = ttk.Entry(code_line, width=7, textvariable=self.category,
                                        state="readonly")
        self.category_entry.pack(side="left", padx=(6, 16))
        ttk.Label(code_line, text=self.tr("ID / Unterkategorie (FIT):")).pack(side="left")
        self.subtype_entry = ttk.Entry(code_line, width=7, textvariable=self.subtype,
                                       state="readonly")
        self.subtype_entry.pack(side="left", padx=(6, 16))
        ttk.Checkbutton(code_line, text=self.tr("IDs manuell bearbeiten (Expertenmodus)"),
                        variable=self.manual_mode, command=self.toggle_manual).pack(
            side="left")
        ttk.Label(
            bottom, text=self.tr(
                "Kategorie = Übungsfamilie (8 = Kreuzheben); ID = Variante in dieser Familie "
                "(0 = Langhantel-Kreuzheben). Die Auswahl setzt beide Zahlen automatisch."
            ), foreground="#555", wraplength=1020,
        ).pack(anchor="w", pady=(6, 0))

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(9, 0))
        ttk.Button(controls, text=self.tr("Zuordnung speichern"),
                   command=self.save).pack(side="left")
        ttk.Button(controls, text=self.tr("Zuordnung entfernen"),
                   command=self.remove).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text=self.tr("Schließen"),
                   command=self.destroy).pack(side="right")

    def change_picker_language(self, event=None):
        """Switch the exercise picker DE/EN in place, preserving current work."""
        selected = "en" if self.language_choice.get() == "English" else "de"
        if selected == self.language:
            return
        try:
            save_catalog_language(selected)
        except OSError:
            messagebox.showwarning(
                self.tr("Zuordnung"),
                self.tr("Katalogsprache konnte nicht gespeichert werden."),
                parent=self,
            )
        category_id = self.filter_lookup.get(self.category_choice.get())
        current = self.selected_name
        old_codes = (self.category.get(), self.subtype.get())
        self.language = selected
        self.filters = [(self.tr("Alle Kategorien"), None)] + list(
            category_filters(self.language)
        )
        self.filter_lookup = dict(self.filters)
        self.category_choice.set(next(
            (label for label, cat in self.filters if cat == category_id),
            self.filters[0][0],
        ))
        for widget in self.winfo_children():
            widget.destroy()
        self._build()
        self._refresh_left(selected=current)
        self._refresh_results()
        self.current.set(current or self.tr("Noch keine Übung ausgewählt"))
        self.category.set(old_codes[0])
        self.subtype.set(old_codes[1])
        if all(old_codes):
            self.assigned_label.set(
                self._label_for_codes(int(old_codes[0]), int(old_codes[1]))
            )
        else:
            self.assigned_label.set(self.tr("Noch keine Garmin-Übung gewählt"))
        self.toggle_manual()

    def _refresh_left(self, selected=None):
        search = normalize_query(self.left_search.get())
        previous = selected or self.selected_name
        self.visible_names = [
            name for name in self.names if search in normalize_query(name)
        ]
        rows = self.table.get_children()
        if rows:
            self.table.delete(*rows)
        mappings = saved_mappings()
        for i, name in enumerate(self.visible_names):
            cat, sub = fit_exercise(name, overrides=mappings)
            label = self._label_for_codes(cat, sub) if sub is not None else self.tr(
                "Keine Zuordnung")
            self.table.insert("", "end", iid=str(i), values=(name, label))
        if previous in self.visible_names:
            row_id = str(self.visible_names.index(previous))
            self.table.selection_set(row_id)
            self.table.see(row_id)

    def _label_for_codes(self, cat, sub):
        if sub is None:
            return self.tr("Keine Zuordnung")
        for title, row_cat, row_sub, _ in all_options(self.language):
            if row_cat == cat and row_sub == sub:
                return title.split("  ·  ", 1)[0]
        return self.tr("Kategorie %d / ID %d") % (cat, sub)

    def _refresh_results(self):
        category = self.filter_lookup.get(self.category_choice.get())
        self.result_rows, total = search_options(
            self.query.get(), category, self.language, limit=180
        )
        rows = self.results_table.get_children()
        if rows:
            self.results_table.delete(*rows)
        for i, (name, cat, sub, _) in enumerate(self.result_rows):
            self.results_table.insert(
                "", "end", iid=str(i),
                values=(name.split("  ·  ", 1)[0], category_title(cat, self.language))
            )
        self.result_count.set(
            self.tr("%d von %d Treffern angezeigt (Gesamtkatalog: %d).")
            % (len(self.result_rows), total, FULL_CATALOG_COUNT)
        )

    def select(self, event=None):
        rows = self.table.selection()
        if not rows:
            return
        i = int(rows[0])
        if i >= len(self.visible_names):
            return
        self.selected_name = self.visible_names[i]
        self.current.set(self.selected_name)
        cat, sub = fit_exercise(self.selected_name, overrides=saved_mappings())
        self.category.set(str(cat) if sub is not None else "")
        self.subtype.set(str(sub) if sub is not None else "")
        self.assigned_label.set(self._label_for_codes(cat, sub))
        self.search_entry.focus_set()

    def choose_result(self, event=None):
        rows = self.results_table.selection()
        if not rows:
            return
        i = int(rows[0])
        if i >= len(self.result_rows):
            return
        label, cat, sub, _ = self.result_rows[i]
        self.category.set(str(cat))
        self.subtype.set(str(sub))
        self.assigned_label.set(label.split("  ·  ", 1)[0])
        # Selection is staged until Save mapping is clicked.

    def toggle_manual(self):
        state = "normal" if self.manual_mode.get() else "readonly"
        self.category_entry.configure(state=state)
        self.subtype_entry.configure(state=state)

    def add_name(self):
        name = simpledialog.askstring(
            self.tr("Speediance-Übung"), self.tr("Name der Speediance-Übung:"),
            parent=self,
        )
        if not name or not name.strip():
            return
        name = name.strip()
        remember_names([name])
        self.names = observed_names()
        self._refresh_left(selected=name)
        self.select()

    def save(self):
        name = self.selected_name
        if not name:
            messagebox.showinfo(
                self.tr("Zuordnung"), self.tr("Bitte zuerst eine Übung auswählen."),
                parent=self,
            )
            return
        try:
            cat = int(self.category.get())
            sub = int(self.subtype.get())
            if not 0 <= cat < 65534 or not 0 <= sub < 65534:
                raise ValueError("Invalid FIT category or subtype")
            if not self.manual_mode.get():
                # The numbers must correspond to a known Garmin FIT enum
                # unless the user expressly enabled expert mode.
                if not any((c, s) == (cat, sub) for _, c, s, _ in all_options()):
                    raise ValueError("Choose a Garmin exercise from the catalog")
            set_override(name, cat, sub)
        except (ValueError, OSError):
            messagebox.showerror(
                self.tr("Ungültige Zuordnung"),
                self.tr("Bitte eine Garmin-Übung auswählen oder gültige FIT-IDs im Expertenmodus eingeben."),
                parent=self,
            )
            return
        self._refresh_left(selected=name)
        self.assigned_label.set(self._label_for_codes(cat, sub))
        messagebox.showinfo(
            self.tr("Zuordnung"),
            self.tr("Zuordnung lokal gespeichert. Für Garmin bitte FIT-Dateien erneut exportieren."),
            parent=self,
        )

    def remove(self):
        if not self.selected_name:
            return
        try:
            set_override(self.selected_name, None, None)
        except (ValueError, OSError):
            messagebox.showerror(
                self.tr("Zuordnung"), self.tr("Zuordnung konnte nicht gelöscht werden."),
                parent=self,
            )
            return
        self._refresh_left(selected=self.selected_name)
        self.select()
