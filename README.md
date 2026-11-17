# Speediance FIT Exporter (Beta 0.1.9)

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

## Änderungen 0.1.4 / 0.1.5: Übungen direkt laden, iOS-App nicht mehr abmelden

**0.1.4** – Im Bereich **Trainingshistorie** ein oder mehrere Workouts markieren und **Übungen zuordnen…** drücken. Die App lädt die Übungsnamen dann direkt aus Speediance und öffnet eine bereits befüllte Zuordnungsübersicht. Ein FIT-Export ist dafür nicht mehr erforderlich. Wenn keine Satzdaten geliefert werden, wird eine Fehlermeldung statt eines leeren Dialogs gezeigt.

**0.1.5** – Speediance erlaubt offenbar nur eine gleichzeitig gültige Sitzung pro **Client-Typ**, nicht pro Account. Der bisherige Login als `SOFTWARE` belegte den Platz der iOS-/Android-App und meldete diese ab. Die Anmeldung erfolgt deshalb standardmäßig mit `App_type: BIKE` und `Versioncode: 1`. Nach dem Login greifen alle Leseaufrufe weiterhin mit `App_type: SOFTWARE` und `Versioncode: 41000` auf die Speediance-Cloud zu. Eine neue Option **Anmeldetyp (Sitzungsplatz)** bietet `bike`, `nano` oder `phone`; sie wird ohne Passwort und Token in den lokalen Einstellungen gespeichert.

- **bike (Voreinstellung):** empfehlenswert, wenn du **kein Speediance Bike** benutzt.
- **nano:** wenn du ein Speediance Bike besitzt, aber **kein Gym Nano**.
- **phone:** kollidiert ausdrücklich mit der iOS-/Android-App; beim Login erscheint eine Warnung.
- **Nicht angeboten:** `gym-monster`, um das eigentliche Trainingsgerät nicht versehentlich abzumelden.

**Wichtig:** Auch ein Bike- oder Nano-Login belegt den jeweiligen Sitzungstyp; ein echtes Gerät desselben Typs oder ein anderes Tool auf diesem Platz kann dadurch abgemeldet werden. Die API ist inoffiziell, nicht dokumentiert und kann sich ändern. Erneute Anmeldung im iPhone ist einmalig nötig, wenn die vorherige Version dessen Sitzung bereits beendet hat.

Dokumentation des beobachteten Speediance-Verhaltens: https://github.com/labatt/speediance-smartgym-workout-manager und https://github.com/labatt/speediance-mcp. Ein Test der neuen Sitzungstypen mit deinem Speediance-Account steht noch aus.

## 0.1.6 – Fehlende Trainings aus dem Monatskalender wiederfinden

Wenn eine abgeschlossene Einheit im Speediance-Kalender erscheint, im Exporter aber fehlt, kann die Kalenderansicht je nach API-Versionsnummer unterschiedliche Ergebnisse liefern. Frühere Builds lasen die Speediance-Kalenderdaten mit `Versioncode=40304`, spätere mit `41000`.

Ab 0.1.6 fragt der Exporter die Monate **lesend** mit beiden bekannten API-Versionen ab, führt Aktivitäten über die Speediance-`trainingId` zusammen und zeigt in der Statusleiste an, wie viele Einheiten nur über die frühere Kalenderansicht wiedergefunden wurden. Es werden **keine zusätzlichen Logins** ausgeführt und der frei gewählte `bike`- bzw. `nano`-Sitzungsplatz bleibt bestehen. Geplante, nicht abgeschlossene Einheiten werden weiterhin ausgeschlossen.

Für Diagnosezwecke protokolliert die Anwendung ausschließlich anonyme Zählwerte (Monat, Kalender-Version, Anzahl Tage, hinzugefügte und übersprungene Einträge), niemals Trainingstitel, Trainings-IDs, Passwörter oder Sitzungstokens. So kann man bei weiteren Differenzen zum Speediance-Kalender prüfen, welche API-Ansicht Einheiten nicht zurückgibt.

**Wichtig:** Der konkrete Fall „GMC · Mon 16 Nov“ am 16.11.2026 ist mit einer lokalen Testantwort nachgestellt; ob Speediance unter dem echten Account dieselben Daten über die alte Version liefert, muss noch an einem echten Abruf geprüft werden. Falls das Training weiterhin fehlt, bitte das neue anonymisierte Diagnoseprotokoll bereitstellen.

## 0.1.7/0.1.8 – Verbesserte Bedienung und zweisprachige Oberfläche

- **Klarere Loginfehler:** Fehlgeschlagene Anmeldungen zeigen eine verständliche Meldung, etwa dass E-Mail-Adresse, Passwort oder Region geprüft werden sollen. Technische API-Fehlercodes bleiben nur im lokal gespeicherten Diagnoseprotokoll.
- **Sichtbarer Sitzungsstatus:** Nicht angemeldet / Anmeldung läuft / Angemeldet, einschließlich des verwendeten Speediance-Sitzungstyps (Bike/Nano/Phone).
- **Reparierte Fensteraufteilung:** Die Export- und Diagnosebuttons sind fest am unteren Fensterrand, während die Trainingsliste den restlichen Platz nutzt. Die Startgröße orientiert sich an der verfügbaren Monitorfläche.
- **Erweiterte Trainingssuche:** Die Kalenderansichten beider Gerätetypen (Gym Monster und Gym Pal) und beider bekannten API-Versionen werden lesend abgefragt, zusammengeführt und anhand der Trainings-ID dedupliziert. In der Diagnose stehen pro Abfrage nur Anzahl Tage, Einträge, hinzugefügte, doppelte, nicht abgeschlossene und verworfene Einträge. Ein fehlendes Training wird **nicht erfunden oder als abgeschlossen markiert**. Ob das Training vom 16.11. in diesen Antworten enthalten ist, muss anhand des echten Accounts überprüft werden.
- **Diagnose anzeigen / kopieren:** Das lokale Protokoll kann direkt im Programm angezeigt und in die Zwischenablage kopiert werden. Vor Weitergabe bitte immer selbst prüfen.
- **Deutsch / English:** Rechts oben im Hauptfenster die Sprache wechseln. Die Auswahl wird in `%LOCALAPPDATA%\\SpeedianceFITExporter\\settings.json` gespeichert und beim nächsten Programmstart wieder geladen. Beim Wechsel bleiben aktuelle Anmeldung, Datumsauswahl, geladene Trainings und Trainingsauswahl erhalten; auch die Übungszuordnung und Standarddialoge sind übersetzt. Die von Speediance gelieferten Original-Übungsnamen bleiben für exakte Garmin-Zuordnungen unverändert.

**Sicherheit:** Die Änderung führt **keine zusätzlichen Anmeldungen** aus. Für den Kalender werden nur bereits bestehende Sitzungen wiederverwendet.

## 0.1.9 – Abgeschlossene selbst erstellte Trainings aus der Historie laden

Die Speediance-Monatskalender-API `/api/app/v5/trainingCalendar/monthNew` blendet abgeschlossene **eigene Custom-Template-Workouts** in manchen Ansichten aus. Das ist in der öffentlich einsehbaren Speediance-MCP-Implementierung dokumentiert.

Daher erfolgt ab Version 0.1.9 **zusätzlich** eine schreibgeschützte GET-Abfrage bei
`/api/mobile/v2/report/userTrainingDataRecord?startDate=JJJJ-MM-TT&endDate=JJJJ-MM-TT`.
Sie liefert die Trainingshistorie einschließlich `trainingId`, `startTime`, `trainingTime` (Sekunden), `type`, `calorie`, `title` und wird anhand der `trainingId` mit den bisherigen Kalendereinträgen zusammengeführt. Die Quelle `history` liefert bei eigenen Trainings häufig die Einträge, die dem Kalender fehlen. Gesundheitsdaten aus der Phone-Synchronisation ohne Gym-Training-ID werden ausgeschlossen. Die Dauer wird auf Minuten umgerechnet und der Endzeitpunkt aus dem tatsächlichen Beginn + Dauer abgeleitet.

Der Status meldet nun, wie viele Aktivitäten **zusätzlich aus der Historie** geladen wurden. Das Diagnoseprotokoll protokolliert ausschließlich Zählwerte aus der Historie (`rows`, `added`, `duplicates`, `outside`, `health`, `invalid`), keine privaten Trainingstitel/IDs oder Zugangsdaten. Bestehende Bike-/Nano-Anmeldungen werden weiterverwendet: der Aufruf benötigt **keinen neuen Login** und verdrängt keine Telefon-Sitzung.

Die detailbezogenen Typen unterscheiden sich zwischen Kalender und Historie. Das Mapping wurde korrigiert (historische Custom-Templates: `type=5` → `cttTrainingInfoDetail`). Fehlt bei einem tatsächlich trainierten Workout dennoch der Übungsdatensatz, bleibt der Schutz vor einem stillen, inhaltlich leeren FIT-Export bestehen.

**Prüfung:** Für den Fall „GMC · Mon 16 Nov“ ist der Unterschied der Quellen durch lokale Tests nachgestellt. Ob dein echter Account die Session in der Historie liefert, wird erst beim tatsächlichen Abruf mit deinem Login sichtbar.

Quelle zum API-Verhalten: https://github.com/labatt/speediance-mcp

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
