# Änderungsübersicht

[English changelog](../en/changelog.md) · [Dokumentationsübersicht](README.md)

Wichtige Änderungen in absteigender Reihenfolge. Frühere Details der Beta-Entwicklung stehen in [../../archive/Entwicklungshistorie.md](../../archive/Entwicklungshistorie.md).

## 0.1.36-beta – Speediance-Garmin-Abgleich (23. November 2026)

- Wiederholungssätze werden mit Wiederholungszahl und Zeitsätze mit Satzdauer in die zusammengeführte FIT exportiert.
- Die Weiterentwicklung läuft wieder als Beta. Ein neuer Release Candidate folgt nach erfolgreicher Abnahme.

## 0.1.35-rc.2 – Vollständig zweisprachige Dokumentation (18. November 2026)

**Reines Dokumentations-/Paketierungsupdate; keine Änderung an FIT-Merge oder API-Verhalten.**

- Aktive Dokumentation in `docs/de/` und `docs/en/` mit identischen neun Dateinamen und übereinstimmender Themenstruktur.
- Deutsches und **vollständiges englisches Benutzerhandbuch** mit denselben zehn Kapiteln; in beiden Sprachen Schnellstart, Grenzen, Drittquellen, Entwicklung, RC- und Veröffentlichungscheckliste sowie Changelog.
- Spracheinstiege und Querverweise direkt zwischen den Dokumenten; historische Beta-Notizen nach `archive/` ausgelagert (nur als historisches, nicht gepflegtes Archiv).
- Windows-Installer und CI-Artefakt enthalten jetzt **beide vollständigen Dokumentationsverzeichnisse**. Startmenü bietet je einen Link auf das deutsche und englische Handbuch.
- Automatisierte Tests erzwingen Sprachparität, funktionierende lokale Links, die vollständige Handbuchkapitelstruktur und eine einheitliche RC-Version.

## 0.1.35-rc.1 – Release Candidate 1 (18. November 2026)

**Stabilisierungs- und Dokumentationsrelease; keine neuen FIT- oder API-Funktionen.**

- Die mit Garmin Connect praktisch bestätigte Zusammenführung aus 0.1.35-beta wird eingefroren: echte Speediance-Sätze + originalbasierte Garmin-FIT, Hersteller-/Produktkennung, Herzfrequenz und Training Effect.
- Versionskennzeichnung auf `0.1.35-rc.1` geändert.
- README komplett neu als nachvollziehbarer Einstieg statt 900+ Zeilen historischen Beta-Änderungen.
- Deutschsprachiges Benutzerhandbuch, englischer Schnellstart, bekannte Einschränkungen, technische Build-Anleitung und RC-Testcheckliste ergänzt.
- Alte Beta-Entwicklungsnotizen in einen Archivbereich verschoben.
- Dokumentation und Changelog werden mit dem Windows-Installer mitgeliefert.
- Veröffentlichung vorerst **private**: eigene Projektlizenz, Garmin-FIT-SDK-Katalog und Speediance-API-Rechtelage sowie die ältere Git-/Actions-Historie benötigen vor einem öffentlichen Repository weitere Prüfung.

**Bekannte Einschränkungen:** Keine Anrechnung von Intensitätsminuten für den untersuchten Garmin-Connect-FIT-Reimport; nicht durch Garmin Connect gelieferte Trainingseinzelsätze können nicht erfunden werden; exakte Satzstartzeiten nicht vollständig verfügbar; keine automatische Aktualisierung oder Ersetzung bereits vorhandener Garmin-Connect-Aktivitäten.

## 0.1.35-beta – Geräteidentität und Training Effect

- Originale `file_id.manufacturer`- und `file_id.product`-Werte aus der Garmin-Quelle bleiben im zusammengeführten FIT erhalten.
- Neue abgeleitete FIT-Datei behält trotzdem eine eigene Serial-/Erstellungszeit-Identität.
- Ein kontrollierter Garmin-Connect-Import zeigte daraufhin wieder Training Effect **0,3 aerob / 0,0 anaerob / Belastung 4**, mit vier direkt abgerufenen Speediance-Sätzen.
- Alle echten Garmin-Geräteinformationen und Sensornachrichten bleiben in der FIT.

## 0.1.34-beta – Direkter Merge und nachvollziehbare Fehler

- Erfolgreicher Abruf absolvierter Speediance-Details aus dem Konto-Cache, einschließlich echter Herzfrequenzwerte.
- Geschätzte Satzanfänge werden bei negativem Startversatz zur Garmin-Aktivität angepasst; die tatsächlichen gemessenen HF-Zeitpunkte werden nicht verschoben.
- Spezifische Garmin-FIT-Fehler werden nicht mehr durch generische `ValueError`-Meldungen verschluckt.

## 0.1.33-beta – Zuordnung zum ausgewählten Training

- **Übungen zuordnen…** zeigt bei markierter Einheit ausschließlich deren tatsächliche, kontobezogene lokale Speediance-Daten statt früher global gespeicherter Übungen anderer Workouts.
- Ohne Auswahl bleiben ältere Übungszuordnungen zugänglich. Offline-Zuordnungsdialog funktioniert auch ohne erfolgreichen Cloud-Abruf.

## 0.1.32-beta – Vorsorgliche Speediance-Sicherung

- Automatisches Sichern verifizierter tatsächlich ausgeführter Sätze für bis zu drei noch nicht gespeicherte Workouts aus den letzten 30 Tagen pro Abruf.
- Konto/Region/Training-isolierter lokaler Cache; keine geplanten Vorlagen ohne tatsächliche Sätze.
- Unterstützung für abgeschlossene Free-Lift-Daten und deren tatsächliche Gewichtsherkunft.

## 0.1.31-beta und früher

- Garmin Personal API, Original-FIT-Overlay, Übungszuordnung, Garmin-FIT-Katalog, Export- und Gewichtslogik, mehrsprachige Oberfläche, Speediance-Kalender-/Historienabruf und geschützte Windows-Anmeldeinformationen.
- Vollständiger Verlauf: [Historische Entwicklungsnotizen](../../archive/Entwicklungshistorie.md).
