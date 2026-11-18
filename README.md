# Speediance FIT Exporter

**0.1.35-rc.1 · Release Candidate 1 · Windows 10/11**  
**Deutsch / English** · Inoffizielles, unabhängiges Community-Projekt

Lokales Windows-Programm, das tatsächlich abgeschlossene Krafttrainingssätze aus deinem **Speediance-Konto** mit der **originalen Garmin-Aufzeichnung** zusammenführt. Originale Garmin-Sensordaten, Geräteinformationen, Herzfrequenz und Training Effect bleiben dabei erhalten; Übungen, Sätze, Wiederholungen und Gewichte stammen aus Speediance.

Die Verbindung erfolgt für die Standardfunktion direkt über die Speediance-Cloud und die **Garmin Connect Personal API** des jeweiligen Nutzers. Ein kostenpflichtiger GM Manager, eine lokale Garmin-FIT-Datei und CSV-Dateien sind **nicht notwendig**.

> **Hinweis:** Der Exporter erzeugt eine **neue lokale FIT-Datei**, lädt sie aber **nicht** in Garmin Connect hoch und verändert keine vorhandene Garmin-Aktivität. **Intensitätsminuten werden nach einem FIT-Reimport möglicherweise nicht dem Garmin-Wochenkonto gutgeschrieben.** Die originale Garmin-Uhr weiterhin normal synchronisieren.

## Schnellstart

1. Den RC-Installer aus dem erfolgreichen [Windows-Build](https://github.com/Pat4best/Speediance-FIT-Exporter/actions/workflows/windows-installer.yml) herunterladen. Bei privater Weitergabe die ZIP-Datei vom Verteiler verwenden.
2. ZIP entpacken und `SpeedianceFITExporter-Setup.exe` unter Windows ausführen. Die Anwendung benötigt **kein installiertes Python**.
3. Programm öffnen, mit deinem Speediance-Konto (Region EU/Global) anmelden und **Trainings laden** wählen.
4. Eine absolvierte Einheit markieren und bei Bedarf über **Übungen zuordnen…** passende Garmin-Übungen bestimmen.
5. **Mit Garmin abgleichen…** → **Garmin Personal API** auswählen, einen eigenen API-Schlüssel eingeben, die zeitlich passende Garmin-Aktivität suchen und **Zusammengeführte FIT speichern…** wählen.
6. Die neue `*_Speediance_Garmin_MERGED.fit` bei Bedarf über **Garmin Connect Web → Daten importieren** hochladen. Ursprüngliche Garmin-Aktivität **nicht löschen**; die importierte Datei kann als zusätzliche oder als Duplikat eingestufte Aktivität erscheinen.

**Detaillierte Anleitung:** [Benutzerhandbuch (Deutsch)](docs/Benutzerhandbuch.md) · [English quick start](docs/Quick_Start_EN.md)

## Funktioniert im RC

- Direkter, schreibgeschützter Abruf abgeschlossener Speediance-Trainings und Satzdaten sowie lokale, kontobezogene Sicherung.
- Korrekte Zuordnung der Übungen des **ausgewählten** Trainings zu Garmin-FIT-Kategorien.
- Abgleich über Garmin Connect Personal API, originalbasierter FIT-Merge und manuelle Speicherung.
- Erhalt der Garmin-Herzfrequenz, originaler Geräte-/Spezialdaten sowie der Training-Effect-Werte. Der Erhalt des Training Effects wurde beim Import in Garmin Connect mit der originalen Hersteller-/Produktkennung praktisch bestätigt.
- Deutsche und englische Bedienoberfläche, optional sichere Zugangsdatenablage im Windows-Anmeldeinformationsmanager und Diagnoseprotokoll.

## Einschränkungen

- Die **Intensitätsminuten** der neu importierten Aktivität werden nach dem bisherigen Test **nicht dem Wochenkonto gutgeschrieben**. Das ist nach der Untersuchung kein sicher durch zusätzliche FIT-Felder behebbarer Fehler.
- Die echten Speediance-Satzanfangszeiten fehlen teilweise; der Exporter schätzt die Zeitpositionen. Die Garmin-„Belastungszeit“ kann deshalb abweichen.
- Die inoffizielle Speediance-API kann nach Änderungen oder dem Löschen einer Trainingsvorlage keine abgeschlossenen Satzdaten mehr liefern. Nicht verfügbare Sätze werden **niemals erfunden**.
- Garmin Connect kann neue FIT-Dateien mit derselben Aktivitätszeit als Duplikate erkennen. Es wird **nichts automatisch überschrieben oder ersetzt**.
- Installer ist noch nicht digital codesigniert. Nur aus einer **vertrauenswürdigen Quelle** installieren.

Weitere Informationen: [Bekannte Einschränkungen](docs/Bekannte_Einschraenkungen.md) · [RC-Versionshinweise](CHANGELOG.md) · [Entwicklung/Build](docs/Entwicklung.md)

## Datenschutz und Sicherheit

Das FIT-Merging geschieht lokal. Die App nutzt nur die vom Nutzer gewählten Speediance-/Garmin-Konten zum lesenden Abruf und überträgt selbst keine Aktivität an Garmin Connect. Optionale Passwörter und API-Schlüssel werden über den Windows-Anmeldeinformationsmanager verwaltet. Gesicherte Trainingssätze, Einstellungen, Übungszuordnungen und Diagnoseprotokolle liegen unter `%LOCALAPPDATA%\\SpeedianceFITExporter\\`. FIT-Dateien und lokale Cache-Daten können sensible Gesundheitsinformationen enthalten.

**Niemals** persönliche Token, Passwörter, API-Schlüssel oder Trainingsdateien in GitHub-Issues veröffentlichen. Diagnoseprotokolle vor Weitergabe selbst prüfen.

**Marken:** „Speediance“, „Garmin“, „Garmin Connect“ und „FIT“ gehören den jeweiligen Rechteinhabern. Dieses Projekt ist von keinem der Hersteller autorisiert oder unterstützt. Für eigene Projekte nur die jeweils zulässigen API-Nutzungsbedingungen beachten.

## Projekt und Lizenzstatus

Dieser RC ist für eine private technische Testphase vorbereitet. **Vor der öffentlichen Repository-Freigabe** müssen eine eigene Quellcode-Lizenz ausgewählt, die Verteilung der aus dem Garmin FIT SDK abgeleiteten Übungskatalog-Daten rechtlich geprüft sowie Git-/Actions-Historie und Geheimnisse kontrolliert werden. Siehe [Checkliste zur Veröffentlichung](docs/Veroeffentlichung_Checkliste.md) und [Drittquellenhinweise](docs/Drittquellen.md). **Die Veröffentlichung ist noch nicht freigegeben.**

Die alte, sehr umfangreiche Beta-Dokumentation ist aus Gründen der Nachvollziehbarkeit unter [Historische Entwicklungsnotizen](docs/Entwicklungshistorie.md) archiviert und enthält teilweise überholte Hinweise. Maßgeblich für den RC ist dieses README und das aktuelle Handbuch.

## Technischer Überblick

Python 3.12/Tkinter, reine Standardbibliothek zur Laufzeit; Windows-Build mit PyInstaller und NSIS via GitHub Actions. Der FIT-Merge kopiert originale Garmin-Nachrichten und ergänzt absolvierte Speediance-`SET`-Nachrichten. **164 automatisierte Tests** aus dem letzten Beta-Stand prüfen API-Auswertung, Übungszuordnung, FIT-Konformität und Merge/Originalschutz; der RC wird separat erneut durch CI gebaut.

Bei Fehlern bitte Programmversion, genaue reproduzierbare Schritte und ein **geprüftes, bereinigtes** Diagnoseprotokoll bereitstellen.
