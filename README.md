# Speediance FIT Exporter (Beta 0.1.2)

Lokale Windows-10/11-Anwendung zum Abruf abgeschlossener Speediance-Trainingseinheiten aus dem eigenen Account und zum Export als Garmin-FIT-Aktivitäten. Die Speediance-API ist **inoffiziell**; der Login ist ohne echten Testaccount nicht verifiziert.

## FIT-Import-Fix in 0.1.1

Die erste Version erzeugte keine konformen FIT-Definitionen (fehlendes Architecture-Byte), kodierte Krafttraining als Schwimmen und schrieb die Gewichte in das falsche Set-Feld. Version 0.1.1 behebt diese Fehler und ergänzt strikte Tests für Datei-Header, Nachrichtenstruktur, Sporttyp, Gewichte und Pflicht-Nachrichten. Ein tatsächlicher Import in Garmin Connect ist weiterhin erst durch einen Test in deinem Account nachweisbar.

**Vorher erstellte .fit-Dateien bitte mit Version 0.1.1 neu exportieren.** Der Installer aus einem älteren GitHub-Actions-Lauf bleibt unverändert und muss neu heruntergeladen werden.

## Neue Übungszuordnung in 0.1.2

Die SET-Nachrichten enthalten jetzt die beiden Garmin-FIT-Felder `category` (Nr. 7) und `category_subtype` (Nr. 8). Die bisherige Kategorie `0` wurde fälschlich immer als **Bankdrücken** gelesen; `65534` bedeutet dagegen tatsächlich **Unbekannt**.

- Kreuzheben mit Langhantel / Barbell Deadlift: Garmin-Kategorie 8, Übung 0.
- Sternsprünge / Jumping Jacks: Kategorie 2, Übung 12.
- Hohe Knie / Skater: derzeit **keine exakte, bestätigte Garmin-Unterkategorie**. Ihr Originalname wird in einer FIT-`exercise_title`-Nachricht mitgeliefert, Garmin Connect kann diese beim Aktivitätsimport jedoch ignorieren. Dort ggf. manuell ändern.
- Unbekannte Übungen werden **nicht** auf Bankdrücken umgebogen.

Zusätzlich werden beim Abruf verschiedener Speediance-Trainingsarten weitere Detail-Endpunkte versucht. Ein Export ohne Satzdaten wird jetzt mit einem Fehler markiert statt eine inhaltlich leere FIT-Datei zu erzeugen.

**Bitte zuvor erzeugte Dateien mit dieser Version erneut exportieren.** Bereits in Garmin Connect importierte Aktivitäten werden nicht automatisch nachträglich geändert. Für den Test ggf. einen alten Import löschen, bevor die neue Datei importiert wird.

Die Zuordnung deckt noch nicht die gesamte Speediance-Übungsbibliothek ab. Garmin-FIT-Übungsnamen müssen explizit auf die IDs des Garmin-FIT-Profils abgebildet werden. Bitte weitere falsch zugeordnete Übungen melden, damit die Tabelle gezielt erweitert werden kann.

## Windows-Installer

GitHub → **Actions** → **Windows installer** → **Run workflow**. Nach einem erfolgreichen Lauf die Datei **SpeedianceFITExporter-Windows-Setup** unter **Artifacts** herunterladen und die darin enthaltene `SpeedianceFITExporter-Setup.exe` starten. Der Installer wird von GitHub auf Windows gebaut und benötigt beim Anwender kein Python. Eine nicht signierte EXE kann eine Windows-SmartScreen-Warnung auslösen.

## Bedienung

1. Speediance-E-Mail, Passwort und Region (EU/Global) eingeben und anmelden.
2. Zeitraum wählen und Trainings laden.
3. Ein oder mehrere Workouts markieren und als `.fit` exportieren.
4. Bei Problemen **Diagnoseprotokoll speichern** wählen und das Protokoll vor dem Teilen prüfen. Keine Passwörter oder Tokens weitergeben.

Die Anwendung ist unabhängig von Speediance und Garmin. Sie nutzt eine inoffizielle Schnittstelle, deren Endpunkte sich ändern können. FIT-Import in Garmin Connect ist noch nicht anhand eines echten Imports bestätigt. Fehlende Satzzeiten müssen geschätzt werden; es werden keine erfundenen Herzfrequenzdaten erzeugt. Ein FIT-Aktivitätsimport ist kein Garmin-Trainingsplan.

## Quellcode / Tests

Python-Standardbibliothek zur Laufzeit (Tkinter-GUI); PyInstaller und NSIS werden nur zum Erstellen des Windows-Installers benötigt. Lokal: `python -m unittest discover -s tests -v`; zum Starten `python app/main.py`. Der Windows-Build läuft per GitHub Actions auf `windows-latest`.

Die Zugangsdaten werden nicht auf der Festplatte gespeichert. Die lokale Diagnosedatei liegt unter `%LOCALAPPDATA%\SpeedianceFITExporter\diagnose.log`. Logs sollen nur Route ohne personenbezogene Kennungen, HTTP-Status, API-Fehlercode und Aktion enthalten.

**Beta:** Der Exporter ist ein experimentelles Projekt. Keine offizielle Integration; die Nutzung ist auf eigene Verantwortung.
