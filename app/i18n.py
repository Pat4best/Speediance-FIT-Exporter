"""Small, offline German/English UI text catalog.

Speediance exercise names and raw diagnostic logs are not translated.
Keep the source German keys stable; English is the user-facing alternative.
"""
EN = {
    "Sprache:": "Language:",
    "Workouts aus deinem Speediance-Account als Garmin-FIT exportieren":
        "Export workouts from your Speediance account as Garmin FIT files",
    "1 – Speediance-Anmeldung": "1 – Speediance sign-in",
    "E-Mail": "Email",
    "Passwort": "Password",
    "Anmelden": "Sign in",
    "● Nicht angemeldet": "● Not signed in",
    "● Anmeldung läuft …": "● Signing in …",
    "● Nicht angemeldet – Anmeldung fehlgeschlagen": "● Not signed in – sign-in failed",
    "● Nicht angemeldet – Zugangsdaten vorausgefüllt":
        "● Not signed in – saved credentials prefilled",
    "● Angemeldet": "● Signed in",
    "● Angemeldet (Speediance, %s)": "● Signed in (Speediance, %s)",
    "Anmeldedaten auf diesem PC speichern": "Remember sign-in on this PC",
    "Gespeicherte Anmeldung löschen": "Forget saved credentials",
    "Anmeldetyp (Sitzungsplatz):": "Sign-in type (session slot):",
    "bike empfohlen, wenn kein Speediance Bike vorhanden; sonst nano wählen.":
        "Choose bike unless you own a Speediance Bike; otherwise select nano.",
    "Achtung: 'phone' meldet die iOS-App ab. 'bike'/'nano' können ein Gerät desselben Typs abmelden. Passwortspeicherung optional im Windows-Anmeldeinformationsmanager.":
        "Warning: 'phone' may sign out the iOS app. 'bike'/'nano' can sign out a device of the same type. Saving passwords in Windows Credential Manager is optional.",
    "2 – Trainingshistorie": "2 – Workout history",
    "Von (JJJJ-MM-TT)": "From (YYYY-MM-DD)",
    "Bis": "To",
    "Trainings laden": "Load workouts",
    "Datum": "Date",
    "Training": "Workout",
    "Minuten": "Minutes",
    "kcal": "kcal",
    "Exportordner: ": "Export folder: ",
    "Ordner auswählen…": "Choose folder…",
    "Ausgewählte als .fit exportieren": "Export selected as .fit",
    "Übungen zuordnen…": "Map exercises…",
    "Diagnose-Ordner öffnen": "Open diagnostics folder",
    "Diagnoseprotokoll speichern…": "Save diagnostics…",
    "Diagnose anzeigen…": "View diagnostics…",
    "Bereit. Bitte anmelden.": "Ready. Please sign in.",
    "FIT-Aktivitätsimport, kein Garmin-Trainingsplan. Fehlende Satzzeiten werden geschätzt.":
        "Exports FIT activities, not Garmin workout plans. Missing set durations are estimated.",
    "Gespeicherte Anmeldung geladen. Zum Verbinden auf Anmelden klicken.":
        "Saved sign-in loaded. Click Sign in to connect.",
    "Anmeldedaten löschen": "Delete credentials",
    "Gespeicherte Speediance-Zugangsdaten von diesem PC löschen?":
        "Delete the saved Speediance credentials from this PC?",
    "Anmeldedaten": "Credentials",
    "Löschen im Windows-Anmeldeinformationsmanager fehlgeschlagen.":
        "Could not delete credentials from Windows Credential Manager.",
    "Gespeicherte Anmeldung gelöscht. Bestehende Sitzung bleibt angemeldet.":
        "Saved credentials deleted. Your current session remains signed in.",
    "Exportordner auswählen": "Choose export folder",
    "Exportordner": "Export folder",
    "Ordner konnte nicht gespeichert werden.": "Could not save the folder.",
    "Exportordner gespeichert.": "Export folder saved.",
    "Übungen zuordnen": "Map exercises",
    "Bitte zuerst ein oder mehrere Trainings in der Liste markieren. Danach lädt das Programm ihre Übungen direkt aus Speediance.":
        "First select one or more workouts in the list. The app will retrieve their exercises from Speediance.",
    "Speediance-Anmeldung": "Speediance sign-in",
    "Bitte zuerst anmelden.": "Please sign in first.",
    "Übungsnamen": "Exercise names",
    "Die Übungen wurden geladen, können aber möglicherweise nicht dauerhaft gespeichert werden.":
        "Exercises were loaded, but could not necessarily be saved permanently.",
    "%d Übungen aus %d gewählten Training(s) geladen.":
        "Loaded %d exercises from %d selected workout(s).",
    "Unvollständige Übungsliste": "Incomplete exercise list",
    "%d gewählte Trainingseinheit(en) konnten nicht vollständig gelesen werden. Details stehen im Diagnoseprotokoll.":
        "Could not read all details of %d selected workout(s). See the diagnostic log.",
    "Für die markierten Trainings wurden keine Übungen geladen.":
        "No exercises were retrieved for the selected workouts.",
    "Keine Übungen abrufbar": "No exercises available",
    "Speediance hat für die markierten Trainings keine Übungen geliefert. Prüfe das Diagnoseprotokoll. Der Zuordnungsdialog wird deshalb nicht leer geöffnet.":
        "Speediance returned no exercises for the selected workouts. Check diagnostics. The empty mapping dialog will not be opened.",
    "Arbeite …": "Working …",
    "Fehler. Diagnoseprotokoll kann gespeichert werden.":
        "An error occurred. You can save the diagnostic log.",
    "Fehler": "Error",
    "Anmeldung": "Sign-in",
    "Bitte E-Mail und Passwort eingeben.": "Enter your email and password.",
    "Achtung: iOS-App wird abgemeldet": "Warning: iOS app may be signed out",
    "Der Typ 'phone' verwendet den gleichen Speediance-Sitzungsplatz wie deine iOS-App. Das kann deine iOS-App sofort abmelden. Trotzdem mit 'phone' anmelden?":
        "The 'phone' sign-in type uses the same Speediance session slot as your iOS app. This may sign out your iOS app immediately. Continue with 'phone'?",
    "Login erfolgreich, aber Speichern im Windows-Anmeldeinformationsmanager fehlgeschlagen.":
        "Signed in, but could not save credentials in Windows Credential Manager.",
    "Angemeldet. Jetzt Trainings laden.": "Signed in. You can now load workouts.",
    "Anmeldung wird geprüft …": "Checking sign-in …",
    "Datum": "Date",
    "Bitte gültigen Zeitraum bis zu 3 Jahren wählen.":
        "Enter valid dates covering no more than three years.",
    "%d abgeschlossene Workouts geladen (Historie: +%d; frühere API: +%d; anderer Gerätetyp: +%d).":
        "Loaded %d completed workouts (history: +%d; older API: +%d; other device: +%d).",
    "%d abgeschlossene Workouts geladen (frühere API: +%d; anderer Gerätetyp: +%d).":
        "Loaded %d completed workouts (older API: +%d; other device type: +%d).",
    "%d abgeschlossene Workouts geladen.": "Loaded %d completed workouts.",
    "Auswahl": "Selection",
    "Bitte mindestens ein Workout markieren.": "Select at least one workout.",
    "Unbekannt": "Unknown",
    "%d exportiert, %d Fehler, %d ohne Garmin-Zuordnung.":
        "%d exported, %d failed, %d without Garmin mapping.",
    "%d FIT-Dateien gespeichert. Fehler: %d":
        "Saved %d FIT files. Errors: %d",
    "\n%d Übungsnamen haben keine eindeutige Garmin-Zuordnung. Die Originalnamen sind lokal für die Zuordnung gespeichert. Klicke auf 'Übungen zuordnen…' und exportiere erneut.":
        "\n%d exercise names have no definitive Garmin mapping. Their original names were saved locally. Choose 'Map exercises…' and export again.",
    "\n%d Trainingseinheiten ohne Speediance-Satzdaten wurden NICHT als leere FIT-Aktivitäten exportiert.":
        "\n%d workouts had no Speediance set data and were NOT exported as empty FIT activities.",
    "Export": "Export",
    "Diagnose": "Diagnostics",
    "Gespeichert. Bitte vor Weitergabe selbst prüfen.":
        "Saved. Review the file before sharing it.",
    "Textdatei": "Text file",
    "Diagnoseprotokoll – lokal": "Diagnostic log – local",
    "Keine Diagnosedaten vorhanden.": "No diagnostics available.",
    "Kopieren": "Copy",
    "Schließen": "Close",
    "In Zwischenablage kopiert.": "Copied to clipboard.",
    "Das Diagnoseprotokoll enthält technische Metadaten. Bitte vor dem Teilen prüfen.":
        "The diagnostic log contains technical metadata. Review it before sharing.",
    "Speediance → Garmin: Übungszuordnung": "Speediance → Garmin: exercise mapping",
    "Wähle links eine erkannte Speediance-Übung und ordne ihr rechts die passende Garmin-Übung zu. Die ausgewählten Trainings werden vor dem Öffnen abgefragt.":
        "Select a Speediance exercise on the left and map it to a Garmin exercise on the right. Selected workouts are loaded before opening this window.",
    "Speediance-Übung": "Speediance exercise",
    "Garmin-Zuordnung": "Garmin mapping",
    "Zuordnung bearbeiten": "Edit mapping",
    "Noch keine Übung ausgewählt": "No exercise selected",
    "Garmin-Übung": "Garmin exercise",
    "Kategorie": "Category",
    "ID": "ID",
    "Übungsname hinzufügen…": "Add exercise name…",
    "Zuordnung entfernen": "Remove mapping",
    "Zuordnung speichern": "Save mapping",
    "Die Liste ist eine Auswahl bekannter Garmin-Übungen. Andere gültige FIT-Kategorie/ID-Paare können rechts eingegeben werden. Änderungen werden nur auf diesem Computer gespeichert.":
        "This list contains selected Garmin exercises. Other valid FIT category/ID pairs can be entered on the right. Changes are saved on this PC only.",
    "Kategorie %d / ID %d": "Category %d / ID %d",
    "Keine Zuordnung": "Not mapped",
    "Name der Speediance-Übung:": "Name of Speediance exercise:",
    "Zuordnung": "Mapping",
    "Bitte zuerst eine Übung auswählen.": "Please select an exercise first.",
    "Ungültige Zuordnung": "Invalid mapping",
    "Bitte gültige Ganzzahlen für Garmin-Kategorie und ID eingeben.\n":
        "Enter valid integer values for the Garmin category and ID.\n",
    "Zuordnung lokal gespeichert. Für Garmin bitte FIT-Dateien erneut exportieren.":
        "Mapping saved locally. Re-export FIT files to update Garmin.",
    "Zuordnung konnte nicht gelöscht werden.": "Could not delete the mapping.",
    "Anmeldung fehlgeschlagen. Bitte E-Mail-Adresse, Passwort und Region (EU/Global) überprüfen.":
        "Sign-in failed. Check your email, password and region (EU/Global).",
    "Speediance hat für diese Trainingseinheit keine Übungsdetails geliefert":
        "Speediance returned no exercise details for this workout.",
    "Speediance hat für dieses Training keine Sätze geliefert":
        "Speediance returned no sets for this workout.",
    "Account in dieser Region nicht gefunden":
        "No Speediance account was found in the selected region.",
    "Für den Account ist kein Passwort eingerichtet":
        "This Speediance account does not have a password yet.",
    "Unbekannte Login-Prüfantwort":
        "Speediance returned an unexpected sign-in verification response.",
    "Login-Antwort unvollständig":
        "The Speediance sign-in response was incomplete.",
    "Login: Token oder Nutzer-ID fehlt":
        "Sign-in failed: missing session credentials.",
    "Verbindung fehlgeschlagen (URLError)":
        "Could not connect to Speediance (network error).",

}
# Translate curated Garmin exercise labels. IDs, not labels, drive FIT export.
EN.update({
    "Bankdrücken – Langhantel": "Barbell bench press",
    "Bankdrücken – Kurzhantel": "Dumbbell bench press",
    "Bankdrücken – Schrägbank Langhantel": "Incline barbell bench press",
    "Bankdrücken – Schrägbank Kurzhantel": "Incline dumbbell bench press",
    "Jumping Jacks / Sternsprünge": "Jumping jacks",
    "Jumping Jacks mit Zusatzgewicht": "Weighted jumping jacks",
    "Kreuzheben – Langhantel": "Barbell deadlift",
    "Kreuzheben – Kurzhantel": "Dumbbell deadlift",
    "Kreuzheben – Rumänisch": "Romanian deadlift",
    "Kreuzheben – Sumo": "Sumo deadlift",
    "Kniebeuge – Langhantel hinten": "Barbell back squat",
    "Kniebeuge – Langhantel vorne": "Barbell front squat",
    "Klimmzug": "Pull-up",
    "Klimmzug – neutraler Griff": "Neutral-grip pull-up",
    "Plank / Unterarmstütz": "Plank",
    "Rudern – Kabelzug stehend": "Standing cable row",
    "Rudern – Kabelzug sitzend": "Seated cable row",
    "Rudern – Kurzhantel": "Dumbbell row",
    "Rudern – Kurzhantel einarmig": "One-arm dumbbell row",
    "Schulterdrücken – Langhantel": "Barbell shoulder press",
    "Schulterdrücken – Kurzhantel über Kopf": "Dumbbell overhead press",
    "Schulterdrücken – Kurzhantel sitzend": "Seated dumbbell shoulder press",
    "Stretch – Cat/Cow": "Cat-cow stretch",
    "Stretch – Kinderhaltung": "Child's pose",
    "Stretch – Hüftbeuger": "Hip flexor stretch",
})


def translate(lang, text):
    """Return the localized UI string, falling back to German."""
    return EN.get(text, text) if lang == "en" else text
