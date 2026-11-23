# Speediance FIT Exporter

**0.1.36-beta · Beta · Windows 10/11**
Independent third-party community tool · Unabhängiges, inoffizielles Community-Projekt

Merge actually completed **Speediance strength-training sets** with your **original Garmin FIT activity**. Keep recorded Garmin heart rate, device information and Training Effect while adding genuine Speediance exercises, repetitions and weights. The program produces a new local FIT file; it **never automatically changes Garmin Connect**.

Tatsächlich absolvierte **Speediance-Krafttrainingssätze** mit einer **originalen Garmin-FIT-Aktivität** zusammenführen. Garmin-Herzfrequenz, Geräteinformationen und Training Effect bleiben erhalten; die echten Speediance-Übungen, Wiederholungen und Gewichte werden ergänzt. Das Programm erstellt nur eine neue lokale FIT-Datei und **ändert Garmin Connect niemals automatisch**.

## Documentation / Dokumentation

Language / Sprache | Start here / Einstieg | Complete manual / Vollständiges BHB |
| --- | --- | --- |
| **Deutsch** | [Deutsch – Dokumentation](docs/de/README.md) | [Benutzerhandbuch](docs/de/user-guide.md) |
| **English** | [English – Documentation](docs/en/README.md) | [User Manual](docs/en/user-guide.md) |

Both language directories contain **the same nine file names and topics**, including quick start, user manual, limitations, development guide, release checklist, third-party notices, publication checklist and changelog. Beide Sprachordner enthalten **dieselben neun Dateien und Themen**, einschließlich Schnellstart, Benutzerhandbuch, Einschränkungen, Entwicklung, RC-Prüfung, Drittquellen, Veröffentlichungscheckliste und Änderungsübersicht.

## Setup / Installation

1. Download the trusted `SpeedianceFITExporter-Windows-Setup-0.1.36-beta` ZIP from [GitHub Actions – Windows installer](https://github.com/Pat4best/Speediance-FIT-Exporter/actions/workflows/windows-installer.yml) or receive it from your distributor. Lade die Beta-ZIP aus dem erfolgreichen Windows-Build oder vom Verteiler herunter.
2. Extract and run `SpeedianceFITExporter-Setup.exe`. No Python installation or administrator permissions are needed. ZIP entpacken und Setup starten; keine Python-Installation erforderlich.
3. Launch the application, sign in to your **own Speediance account**, load completed workouts, choose one workout, and select **Mit Garmin abgleichen… / Match with Garmin…**. Melde dich bei deinem eigenen Speediance-Konto an, lade abgeschlossene Trainings, markiere eine Einheit und öffne den Garmin-Abgleich.
4. Use your **own Garmin Personal API key**, match the original Garmin activity, save the merged FIT, and **manually** import it through Garmin Connect Web. Erstelle deinen eigenen Garmin-Personal-API-Schlüssel, wähle die passende Originalaktivität und importiere die gespeicherte FIT bei Bedarf **manuell**.

See the [English quick start](docs/en/quick-start.md) or [deutschen Schnellstart](docs/de/quick-start.md) for detailed steps.

## Known limits / Bekannte Grenzen

- **Intensity Minutes / Intensitätsminuten:** In the verified Garmin Connect FIT reimport, no additional weekly Intensity Minutes were credited. Bei unserem bestätigten FIT-Reimport wurden dem Garmin-Wochenkonto **keine neuen Intensitätsminuten** gutgeschrieben; synchronisiere weiterhin die ursprüngliche Garmin-Uhr.
- **SET timing / Satzzeitpunkte:** Speediance does not supply verified absolute timestamps for every completed set; some active/rest timing is estimated. Nicht alle absoluten Satzanfangszeiten sind verfügbar; Belastungs- und Pausenzeiten sind teils geschätzt.
- **Unavailable workouts / Fehlende Trainingsdetails:** The unofficial Speediance API can lose access to completed-set details, e.g. after template deletion. The exporter never invents sets. Die inoffizielle Speediance-API kann Satzdetails später nicht mehr liefern; es werden niemals Sätze erfunden.
- **Duplicate imports / Duplikate:** Garmin Connect can reject overlapping or repeated FIT activity imports; the original Garmin recording is never automatically overwritten. Garmin Connect kann doppelte Aktivitäten ablehnen; das Original bleibt unverändert.

## Privacy, licensing and release status / Datenschutz, Lizenzen und Freigabe

Optional passwords/personal API keys use **Windows Credential Manager**; completed-workout cache, exercise mappings, settings and diagnostic logs stay under `%LOCALAPPDATA%\SpeedianceFITExporter\`. FIT files and caches can contain sensitive fitness data; inspect logs before sharing. Optionale Zugangsdaten/Schlüssel werden im Windows-Anmeldeinformationsmanager gespeichert; private Trainings- und Diagnosedaten bleiben lokal und müssen vor Weitergabe geprüft werden.

The Windows installer is **unsigned**. The GitHub repository remains **private**, pending an explicit review of the Garmin FIT SDK-derived catalog, applicable Speediance/Garmin terms and historical Git/Actions content. Der Installer ist **nicht digital signiert**. Das Repository bleibt bis zur Rechts-, Lizenz- und Sicherheitsprüfung **privat**.

[Third-party sources (EN)](docs/en/third-party.md) · [Drittquellen (DE)](docs/de/third-party.md) · [Release notes / Changelog](CHANGELOG.md) · [Historic beta archive (German only)](archive/Entwicklungshistorie.md)
