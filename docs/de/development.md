# Entwicklung, Tests und eigener Windows-Build

**Ziel:** Technische Nachvollziehbarkeit von **0.1.35-rc.2**; normale Windows-Nutzer benötigen diese Schritte **nicht**.

## Architektur in Kürze

- `app/main.py`: Tkinter-Oberfläche, Status/Threads, Speediance-Login und Trainingshistorie.
- `app/speediance_api.py`: Inoffizielle, lesende Speediance-API. Authentifizierung des eigenen Accounts, Kalender/History-Discovery, echte abgeschlossene Set-Daten. Weitere abgeleitete Werte werden nur bei begründeter Datenherkunft berechnet.
- `app/completed_workout_cache.py`: Nach Benutzerkonto/Region/Workout getrennter, lokaler Cache tatsächlich abgeschlossener Übungen. Keine Speicherung von Zugangstokens.
- `app/exercise_discovery.py`, `app/mapping_editor.py`, `app/exercise_mapping.py` und `app/garmin_catalog*.py`: Erkennung absolvierter Übungen, Benutzer-Mapping, Garmin-FIT-Kategorien/-Unterkategorien.
- `app/garmin_personal.py`: Persönlicher Garmin-API-Schlüssel, Zugriff nur auf eigene Aktivitäten und Download des unveränderten Original-FITs.
- `app/garmin_fit_reader.py`, `app/garmin_fit_overlay.py`, `app/garmin_merge.py`, `app/fitwriter.py`: Originalbasierter, nachrichtenerhaltender Garmin-FIT-Merge, Schreiben echter absolvierter Speediance-`SET`-Nachrichten. Erhalt originaler Geräte- und Sensorwerte inklusive Hersteller/Produktkennung und Training-Effect-Sitzungsfeldern.
- `app/windows_credentials.py`, `app/preferences.py`: Windows Credential Manager für ausdrücklich gespeicherte Zugangsdaten; lokale JSON-Einstellungen ohne Tokens.
- `.github/workflows/windows-installer.yml` + `installer.nsi`: Windows CI, PyInstaller-`onefile` und NSIS-Setup.

## Entwicklungsumgebung (Windows)

Python **3.12** installieren, Repository herunterladen und im Repository-Hauptverzeichnis ausführen:

```powershell
python -m unittest discover -s tests -v
python app/main.py
```

Automatische Tests benötigen **keine privaten Konten**, keine Garmin-API-Schlüssel und keinen Internetzugang. Die Tests prüfen insbesondere unvollständige/nicht verfügbare Speediance-Details, Übungszuordnung zum ausgewählten Training, Garmin-Originalschutz, Trainingssatzmengen, Herzfrequenz und echte FIT-Daten.

## Windows-Setup selbst bauen

```powershell
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --onefile --windowed --name SpeedianceFITExporter --paths app app/main.py
```

Danach mit installiertem **NSIS**:

```powershell
& "${env:ProgramFiles(x86)}\NSIS\makensis.exe" installer.nsi
```

Ergebnis: `dist/SpeedianceFITExporter-Setup.exe`. Installer bindet die Benutzer-Dokumentation aus `docs/` und das Changelog ein. **Keine** Endnutzer-FIT-Dateien, gespeicherte Anmeldedaten oder Cacheverzeichnisse in das Repository oder Installer-Build-Verzeichnis kopieren.

CI unter GitHub **Actions → Windows installer** führt zuerst die Tests aus, erstellt nur bei Erfolg die Windows-EXE und das Setup und veröffentlicht das ZIP-Artefakt unter dem Buildlauf.

## Daten- und Abgleichprinzipien

1. **Keine erfundenen Sätze:** Ein Trainingsplan ist keine Aufzeichnung. Bei leeren/gesperrten Detaildaten Merge abbrechen.
2. **Keine blinde Gewichtsverdoppelung:** Wenn die API das vollständige Gewicht meldet, keine Umrechnung „pro Griff“; manuelle Korrekturen sind opt-in und abhängig von Datenherkunft.
3. **Garmin-Original erhalten:** Alle originalen Nachrichten/Entwicklerfelder so weit wie möglich kopieren; tatsächliche Garmin-Sensorpunkte und die echte Hersteller-/Produktkennung beibehalten. Neue abgeleitete FIT-Dateiidentität verwenden.
4. **Gemessene vs. geschätzte Zeitpunkte unterscheiden:** Speediance-Set-Dauern können echt sein, absolute Set-Startzeiten aber geschätzt; tatsächliche Garmin/Speediance-Herzfrequenzpunkte nicht willkürlich verschieben.
5. **Read-only Garmin Connect:** Die Personal API dient zur Originalaktivitätssuche und zum FIT-Download. Der Import einer fertigen FIT liegt beim Benutzer.
6. **Beschränkungen dokumentieren:** Intensitätsminuten werden nicht als künstliche FIT-MONITORING-Daten erzeugt. Der Original-Garmin-Wochenwert kann unabhängig von importierten Aktivitäten existieren.

## Tests vor RC-Freigabe

Siehe [RC-Testcheckliste](rc-checklist.md). Zusätzlich müssen alle CI-Tests auf Windows bestehen. Reale End-to-End-Verbindung von Speediance und Garmin kann nur ein Benutzer mit passenden **eigenen** Accounts bestätigen; keine Live-Anmeldedaten in den Quellcode einfügen.

## Rechtliche Veröffentlichung

Vor einer öffentlichen Repo-Freigabe die [Veröffentlichungscheckliste](publication-checklist.md) und [Drittquellenhinweise](third-party.md) lesen. Die Garmin-FIT-Katalogdaten sind aus dem offiziellen Garmin-FIT-SDK abgeleitet. Für diese Daten nicht ohne Prüfung pauschal eine eigene MIT-/Apache-Lizenz behaupten.

