# Speediance FIT Exporter (Beta 0.1.3)

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

## Neue Funktionen in 0.1.3

- **Anmeldedaten speichern (optional):** Häkchen in der Speediance-Anmeldung setzen und erfolgreich anmelden. E-Mail, Region und Passwort werden vom Windows-Anmeldeinformationsmanager für das lokale Windows-Benutzerkonto verwaltet. Die App lädt sie beim nächsten Start vorausgefüllt; die Anmeldung wird durch den Nutzer mit **Anmelden** ausgelöst. Das Speediance-Session-Token wird nicht dauerhaft gespeichert. Ohne Häkchen werden bereits gespeicherte Anmeldedaten beim nächsten erfolgreichen Login gelöscht. Alternativ über **Gespeicherte Anmeldung löschen**.
- **Exportordner merken:** Über **Ordner auswählen…** einen Zielordner festlegen. Diesen Ordner verwendet die App beim nächsten Export und bei zukünftigen Programmstarts automatisch wieder. Der Pfad liegt in `%LOCALAPPDATA%\\SpeedianceFITExporter\\settings.json` und enthält keine Zugangsdaten.
- **Übungen zuordnen…:** Beim Export erkannte Speediance-Übungsnamen werden ausschließlich lokal gespeichert und in der Zuordnungsverwaltung angezeigt. Zuordnung über die geprüfte Auswahlliste oder gültige Garmin-FIT-Kategorie/Unterkategorie eintragen. Speicherung in `%LOCALAPPDATA%\\SpeedianceFITExporter\\exercise_mappings.json`, kein Cloud-Abgleich.
- Geänderte Übungszuordnungen gelten **nur für neu erzeugte FIT-Dateien**, nicht für bereits importierte Garmin-Aktivitäten.

Der Garmin-FIT-Katalog ist umfangreich: Die Auswahlliste enthält zunächst eine Auswahl verifizierter Übungen und lässt weitere Kategorien/IDs manuell zu. Ein falsch eingegebener Wert kann zu einer falschen Garmin-Anzeige führen.

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

Zugangsdaten werden **nur bei aktivierter Option** im Windows-Anmeldeinformationsmanager (Credential Manager) für das aktuelle Windows-Benutzerkonto gespeichert; keine Passwörter oder Sitzungstokens in Konfigurationsdateien oder Logs. Über **Gespeicherte Anmeldung löschen** lassen sie sich wieder entfernen. Die lokale Diagnosedatei liegt unter `%LOCALAPPDATA%\SpeedianceFITExporter\diagnose.log`. Logs sollen nur Route ohne personenbezogene Kennungen, HTTP-Status, API-Fehlercode und Aktion enthalten.

**Beta:** Der Exporter ist ein experimentelles Projekt. Keine offizielle Integration; die Nutzung ist auf eigene Verantwortung.
