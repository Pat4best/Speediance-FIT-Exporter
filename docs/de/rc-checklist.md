# Abnahmecheckliste – 0.1.35-rc.2

[English version](../en/rc-checklist.md) · [Dokumentationsübersicht](README.md)

Diese Checkliste dokumentiert die Freigabekriterien für **Release Candidate 2**. Sie enthält keine privaten Zugangsdaten oder FIT-Dateien und darf mit dem RC verteilt werden.

## Automatisch (GitHub Actions / Windows)

- [ ] `python -m unittest discover -s tests -v` auf Windows erfolgreich
- [ ] PyInstaller-`SpeedianceFITExporter.exe` erstellt
- [ ] NSIS-`SpeedianceFITExporter-Setup.exe` erstellt
- [ ] GitHub-Actions-Artefakt mit Installer **und** Endnutzer-Dokumentation vorhanden
- [ ] Version der Anwendung ist `0.1.35-rc.2`
- [ ] Zusammengeführte FIT: ursprünglicher Garmin-Hersteller / Produkt, neue Dateiidentität, Training Effect und Garmin-Geräte-/Sensordaten erhalten
- [ ] Keine versehentliche Einbeziehung von privaten Kontodaten oder FIT-Dateien in Installer/Artefakte

## Manuell auf einem Windows-10/11-PC ohne Entwicklungsumgebung

- [ ] Installer startet; keine Python-Installation nötig
- [ ] Startmenü-Verknüpfung öffnet den Exporter
- [ ] Benutzerhandbuch / Changelog ist mit dem Installer lokal vorhanden
- [ ] Speediance-Anmeldung mit eigenem Konto/Region erfolgreich
- [ ] Zeitraum auswählen → **Trainings laden** zeigt abgeschlossene Workouts
- [ ] Übungszuordnung bei markierter Einheit zeigt ausschließlich deren wirkliche gespeicherte Übungsnamen
- [ ] Bestehende Garmin-Zuordnungen bleiben erhalten
- [ ] Garmin Personal API mit eigenem Schlüssel → zeitlich passende Originalaktivität gefunden
- [ ] „Zusammengeführte FIT speichern…“ erstellt neue Datei mit tatsächlich absolvierten Sätzen
- [ ] Garmin Connect zeigt nach dem Import die richtigen Satz-/Gewichtsdaten, HF-Zusammenfassung sowie Training Effect
- [ ] Alte Garmin-Aktivität und ihre Daten wurden durch den Exporter nicht verändert
- [ ] Unverfügbare Speediance-Satzdaten brechen Merge sicher ab
- [ ] Deutsches und englisches Benutzerhandbuch kann geöffnet werden
- [ ] Deinstallation funktioniert; Benutzer-Daten bleiben getrennt im LocalAppData-Bereich

## Bewusst nicht als bestanden behauptet

- **Intensitätsminuten:** Garmin Connect schrieb beim Test keine zusätzlichen Minuten in das Wochenkonto; die Einschränkung ist dokumentiert, keine RC-Blockade.
- **Alle Speediance-Geräte/Regionen/Trainingsarten:** nicht mit allen realen Konten verifiziert.
- **Öffentliche GitHub-/Open-Source-Freigabe:** getrennte Rechts-, Lizenz- und Historiensicherheitsprüfung nötig.

## Referenz zu erfolgreichen Beta-Tests

- 0.1.35-beta: **164 Windows-Unittests bestanden**, Installer erfolgreich
- Ein Nutzer hat den vollständigen direkten Speediance→Garmin-Personal-API→FIT-Import und die wiederhergestellten Training-Effect-Werte bestätigt
- RC-Softwareänderungen sind auf Dokumentation, Versionsanzeige und Installer-Paketierung beschränkt

