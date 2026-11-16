# Speediance FIT Exporter (Beta)

Lokale Windows-10/11-Anwendung zum Abruf abgeschlossener Speediance-Trainingseinheiten aus dem eigenen Account und zum Export als Garmin-FIT-Aktivitäten. Die Speediance-API ist **inoffiziell**; der Login ist ohne echten Testaccount nicht verifiziert.

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
