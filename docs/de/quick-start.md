# Speediance FIT Exporter – Schnellstart

**Version:** 0.1.35-rc.2 · **Windows 10/11** · Unabhängiges Community-Tool (keine Verbindung zu Speediance oder Garmin)

Für alle Einzelheiten und Fehlerbehebung siehe das [vollständige Benutzerhandbuch](user-guide.md). [English quick start](../en/quick-start.md) · [Dokumentationsübersicht](README.md). Die Anwendung kann oben rechts zwischen Deutsch und Englisch umgeschaltet werden.

## Zweck

Tatsächlich **abgeschlossene** Speediance-Übungen und Sätze direkt aus deinem eigenen Konto abrufen und mit der **originalen Garmin-Aktivität** aus der Garmin Personal API zusammenführen. Die neue FIT bewahrt Garmin-Sensordaten, Geräteidentität und die bereits berechneten Training-Effect-Werte.

Keine kostenpflichtige GM-Manager-Schnittstelle, keine lokal heruntergeladene Garmin-FIT und kein CSV-Export für den regulären Weg nötig. Garmin Connect wird nicht automatisch verändert.

## Installation

1. Das vertrauenswürdige ZIP-Artefakt `SpeedianceFITExporter-Windows-Setup-0.1.35-rc.2` aus einem erfolgreichen Windows-Installer-Build herunterladen oder vom Verteiler erhalten.
2. ZIP entpacken, `SpeedianceFITExporter-Setup.exe` starten. Keine Python-Installation und keine Administratorrechte erforderlich.
3. Über das Windows-Startmenü **Speediance FIT Exporter** öffnen. Die Anwendung ist noch nicht digital signiert; nur aus vertrauenswürdiger Quelle ausführen.

## Training zusammenführen

1. Mit Speediance-E-Mail und Passwort anmelden, Region **EU** oder **Global** wählen. Anmeldetyp `bike` ist geeignet, falls kein Speediance Bike verwendet wird; andernfalls ggf. `nano`. **`phone` kann die Smartphone-App abmelden**; Sitzungstypen können mit echten Geräten kollidieren.
2. Zeitraum `JJJJ-MM-TT` einstellen und **Trainings laden** wählen.
3. Eine absolvierte Einheit markieren. Falls nötig über **Übungen zuordnen…** die Speediance-Übung einer Garmin-Übung zuweisen. Bei markierter Einheit zeigt der Editor nur deren gesicherte Übungen; ohne Auswahl die bisherigen globalen Zuordnungen.
4. **Mit Garmin abgleichen…** anklicken und **Garmin Personal API** als Quelle auswählen.
5. Über **Schlüssel erstellen** einen eigenen Garmin-API-Schlüssel von <https://connect.garmin.com/app/settings/personalApiToken> anlegen und eingeben; optional im Windows-Anmeldeinformationsmanager sichern.
6. Datenprioritäten für Zeit, Dauer, Herzfrequenz und Kalorien zunächst bei **Garmin** belassen. **Garmin-Aktivitäten suchen / FIT prüfen** wählen und die zeitlich passende Originalaktivität auswählen.
7. **Zusammengeführte FIT speichern…** anklicken. Die ursprüngliche Garmin-Aktivität bleibt unverändert; es wird eine **neue lokale FIT-Datei** erstellt.
8. Datei über **Garmin Connect Web → Daten importieren** importieren und Sätze, Wiederholungen, Gewichte, HF und Training Effect prüfen. Ein Import ersetzt niemals automatisch das Original und kann als Duplikat abgelehnt werden.

**Alternative:** Die Option **Lokale Garmin-FIT-Datei** erlaubt den Abgleich ohne Garmin Personal API, verlangt dann aber die authentische originale Garmin-FIT als lokale Datei.

**Eigenständiger Export:** **Ausgewählte als .fit exportieren** erstellt eine reine Speediance-Aktivität **ohne** die originalen Garmin-Trainings-Effect- und Sensordaten.

## Wichtige Grenzen

- **Intensitätsminuten:** Beim getesteten Garmin-Connect-Reimport wurden dem Wochenkonto **keine neuen Intensitätsminuten gutgeschrieben**, obwohl der Training Effect korrekt erschien. Die Garmin-Uhr weiterhin normal synchronisieren.
- **SET-Zeitpunkte:** Tatsächlich absolvierte Sätze und Gewichte liegen vor, aber nicht für jeden Satz ein verifizierter absoluter Beginn. Belastungs- und Pausenzeiten sind teilweise geschätzt.
- **Gelöschte Vorlagen:** Speediance kann ein Training in der Historie anzeigen, ohne später noch die Satzdetails zu liefern. Ein zuvor angelegter lokaler Cache kann helfen; der Exporter erfindet keine Sätze.
- **Training Effect:** Erfolgreicher Test mit aus der Garmin-Originaldatei übernommener Hersteller-/Produktkennung und neuer Dateiidentität. Garmin Connect kann sich je nach Konto/Aufzeichnung unterschiedlich verhalten.

## Datenschutz und sichere Weitergabe

Konten werden ausschließlich für die Speediance- und Garmin-Abrufe verwendet. Der FIT-Merge läuft lokal und lädt selbst nichts bei Garmin Connect hoch. Optional gespeicherte Passwörter und Schlüssel liegen im **Windows-Anmeldeinformationsmanager**; persönliche Trainingsdetails, Cache und Einstellungen unter `%LOCALAPPDATA%\SpeedianceFITExporter\`. Diagnoseprotokolle vor Weitergabe prüfen. **Keine Passwörter, API-Schlüssel oder Tokens weitergeben.**

Die Deinstallation entfernt nicht zwangsläufig gespeicherte Einstellungen, Cache oder Zugangsdaten. Das Tool ist unabhängig von Speediance/Garmin und verwendet eine inoffizielle Speediance-Schnittstelle. Der Installer ist noch nicht codesigniert.
