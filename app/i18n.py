"""Small, offline German/English UI text catalog.

Speediance exercise names and raw diagnostic logs are not translated.
Keep the source German keys stable; English is the user-facing alternative.
"""
EN = {
    "Garmin-FIT als Grundlage: Originalaufzeichnung, Geräte- und Sensordaten bleiben erhalten. Die tatsächlichen Speediance-Krafttrainingssätze werden ergänzt. Online bleibt alles unverändert.":
        "Garmin FIT is the base: original activity, device and sensor data are preserved. Speediance adds actual strength sets. Nothing online is modified.",
    "Neue FIT-Datei aus der ORIGINALEN Garmin-Aufzeichnung. Für vollständige Garmin-Zeitachsen Garmin als Trainingsbeginn und Trainingsdauer wählen. Ein manueller Import kann eine zweite Aktivität erzeugen; online wird nichts gelöscht oder überschrieben.":
        "New FIT file based on the ORIGINAL Garmin activity. Choose Garmin for activity start and duration to retain the full native Garmin timeline. Manual import may create another activity; nothing online is deleted or overwritten.",
    "Garmin-originalbasierte FIT-Datei gespeichert:\\n%s\\n\\nSpeediance-Krafttrainingssätze: %d\\nGarmin-Geräteinformationen erhalten: %d\\nZusätzliche HF-Records: %d\\nAußerhalb der gewählten Dauer: %d\\n\\nGarmin Connect wurde NICHT verändert.":
        "Garmin-based FIT file saved:\\n%s\\n\\nSpeediance strength sets: %d\\nGarmin device information preserved: %d\\nAdded HR records: %d\\nOutside selected duration: %d\\n\\nGarmin Connect was NOT modified.",
    "Mit Garmin abgleichen…": "Match with Garmin…",
    "Garmin Personal API – Abgleich und FIT-Merge": "Garmin Personal API – match and FIT merge",
    "Garmin-Aktivität mit Speediance zusammenführen": "Merge a Garmin activity with Speediance",
    "Nur Lesen über die offizielle Garmin Personal API. Die ursprüngliche Garmin-Connect-Aktivität bleibt unverändert.":
        "Read-only access via the official Garmin Personal API. Your original Garmin Connect activity remains unchanged.",
    "1 – Persönlicher Garmin-API-Schlüssel": "1 – Personal Garmin API key",
    "Schlüssel erstellen": "Create API key",
    "Garmin-Schlüssel geschützt auf diesem PC speichern":
        "Save Garmin key securely on this PC",
    "2 – Datenpriorität festlegen": "2 – Choose data priorities",
    "Herzfrequenzverlauf": "Heart-rate graph",
    "Durchschnittspuls": "Average heart rate",
    "Maximalpuls": "Maximum heart rate",
    "Kalorien": "Calories",
    "Trainingsbeginn": "Activity start",
    "Trainingsdauer": "Activity duration",
    "Übungen, Sätze, Wiederholungen und tatsächliche Gewichte: immer Speediance. Fehlende Messwerte können aus der jeweils anderen Quelle ergänzt werden.":
        "Exercises, sets, repetitions and actual weights always come from Speediance. Missing readings may be supplied by the other source.",
    "3 – Passende Garmin-Aktivität wählen": "3 – Select matching Garmin activity",
    "Garmin-Aktivitäten suchen": "Find Garmin activities",
    "Noch keine Suche durchgeführt.": "No search yet.",
    "Es wird eine NEUE lokale FIT-Datei erstellt. Ein manueller Import in Garmin Connect kann eine zweite Aktivität erzeugen. Keine Aktivitäten werden online gelöscht oder überschrieben.":
        "A NEW local FIT file will be created. Importing it into Garmin Connect may create a duplicate activity. No online activities are deleted or overwritten.",
    "Zusammengeführte FIT speichern…": "Save merged FIT…",
    "Bitte laufenden Vorgang abschließen": "Please finish the current operation",
    "Der Abgleich läuft noch. Bitte erst nach Abschluss schließen.":
        "The matching operation is running. Close this window after it completes.",
    "Garmin API-Schlüssel": "Garmin API key",
    "Bitte einen persönlichen Garmin-API-Schlüssel eingeben.":
        "Enter your personal Garmin API key.",
    "Garmin-Schlüssel": "Garmin key",
    "Der Garmin-Schlüssel konnte nicht geschützt gespeichert werden.":
        "The Garmin key could not be securely stored.",
    "Suche läuft …": "Searching …",
    "Keine zeitlich passende Garmin-Aktivität gefunden.":
        "No matching Garmin activity found.",
    "Kein eindeutiger Treffer": "No matching activity",
    "Keine Garmin-Aktivität passt zeitlich ausreichend. Es wurde keine FIT-Datei erstellt.":
        "No Garmin activity matches the activity time closely enough. No FIT file was created.",
    "%d mögliche Garmin-Aktivität(en). Bitte eine auswählen.":
        "%d possible Garmin activities. Please select one.",
    "Garmin-Aktivität auswählen": "Select Garmin activity",
    "Bitte zuerst die passende Garmin-Aktivität auswählen.":
        "Select the matching Garmin activity first.",
    "Einstellungen": "Settings",
    "Datenpriorität konnte nicht gespeichert werden.":
        "Data priority settings could not be saved.",
    "Neue zusammengeführte FIT-Datei speichern": "Save new merged FIT file",
    "Zusammenführung abgeschlossen": "Merge completed",
    "Neue FIT-Datei lokal gespeichert:\\n%s\\n\\nHerzfrequenzpunkte: %d\\nAußerhalb der gewählten Dauer: %d\\n\\nGarmin Connect wurde NICHT verändert.":
        "New FIT file saved locally:\\n%s\\n\\nHeart-rate points: %d\\nOutside selected duration: %d\\n\\nGarmin Connect was NOT modified.",
    "Eine Trainingseinheit auswählen": "Select one workout",
    "Bitte genau eine Speediance-Trainingseinheit markieren.":
        "Select exactly one Speediance workout.",
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
    "Speediance-Übung links auswählen, rechts im vollständigen Garmin-Katalog suchen und die Zuordnung speichern.":
        "Select a Speediance exercise on the left, search the full Garmin catalog on the right, then save the mapping.",
    "Speediance-Übungen": "Speediance exercises",
    "Speediance-Namen filtern:": "Filter Speediance names:",
    "Garmin-Katalog durchsuchen": "Search Garmin exercise catalog",
    "Links und rechts eine Übung auswählen.":
        "Select an exercise on the left and right.",
    "Links die Speediance-Übung und rechts die Garmin-Übung wählen, dann auf „Zuordnen“ klicken. Die Zuordnung erscheint sofort links.":
        "Select a Speediance exercise on the left and a Garmin exercise on the right, then click Map. The mapping appears on the left immediately.",
    "← Zuordnen": "← Map",
    "Gewicht": "Weight",
    "\nHF-Sensorinformationen in %d FIT-Datei(en) hinterlegt.":
        "\nHR sensor details added to %d FIT file(s).",
    "\nBei %d Aktivität(en) wurden die HF-Zeitpunkte gleichmäßig über die Trainingsdauer verteilt.":
        "\nFor %d activity/activities, HR sample times were evenly distributed over the workout duration.",

    "Speediance-Gewicht pro Griff (×2 für Garmin)":
        "Speediance weight per handle (×2 for Garmin)",
    "Bei echten Links-/Rechts-Messwerten werden beide Seiten addiert. Die ×2-Regel gilt nur für einzelne Speediance-Gewichtsangaben.":
        "When left/right resistance samples are available, the sides are added. The ×2 rule applies only to a single reported weight value.",
    "Gewichtseinstellung konnte nicht gespeichert werden.":
        "Could not save weight setting.",
    "Gewichtsfaktor für %s gespeichert: ×%d":
        "Weight multiplier saved for %s: ×%d",
    "\nHerzfrequenz: %d echte Messpunkte übertragen.":
        "\nHeart rate: %d measured samples exported.",
    "\nGewichte: %d Sätze von pro Griff auf Gesamtgewicht umgerechnet.":
        "\nWeights: %d sets converted from per-handle to total weight.",

    "Rechts eine Garmin-Übung auswählen.":
        "Select a Garmin exercise on the right.",
    "Mit „← Zuordnen“ übernehmen.":
        "Click ← Map to assign this exercise.",
    "Zuordnung gespeichert: %s → %s":
        "Mapping saved: %s → %s",
    "Zuordnung entfernt.": "Mapping removed.",

    "Katalogsprache:": "Catalog language:",
    "Katalogsprache konnte nicht gespeichert werden.": "Could not save catalog language preference.",
    "Suchbegriff (z. B. Bankdrücken / bench, Kreuzheben / deadlift):":
        "Search (e.g., Bankdrücken / bench, Kreuzheben / deadlift):",

    "Suchbegriff (z. B. bench, fly, lat, stretch):":
        "Search term (e.g., bench, fly, lat, stretch):",
    "Kategorie filtern:": "Filter by category:",
    "Alle Kategorien": "All categories",
    "Noch keine Garmin-Übung gewählt": "No Garmin exercise selected",
    "Kategorie (FIT):": "Category (FIT):",
    "ID / Unterkategorie (FIT):": "ID / subtype (FIT):",
    "IDs manuell bearbeiten (Expertenmodus)": "Edit IDs manually (expert mode)",
    "Kategorie = Übungsfamilie (8 = Kreuzheben); ID = Variante in dieser Familie (0 = Langhantel-Kreuzheben). Die Auswahl setzt beide Zahlen automatisch.":
        "Category = exercise family (8 = Deadlift); ID = variation in that family (0 = Barbell Deadlift). Selecting a Garmin exercise fills both numbers automatically.",
    "%d von %d Treffern angezeigt (Gesamtkatalog: %d).":
        "Showing %d of %d matches (full catalog: %d).",
    "Bitte eine Garmin-Übung auswählen oder gültige FIT-IDs im Expertenmodus eingeben.":
        "Select a Garmin exercise or enter valid FIT IDs in expert mode.",
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
