# Speediance FIT Exporter (Beta 0.1.35)

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

## 0.1.10 – Garmin-Übungen durchsuchen und zuordnen

Die bisherige Garmin-Liste umfasste nur 25 häufige Übungen. Die neue Variante enthält **1.838 Garmin-FIT-Übungseinträge aus allen 51 Übungsnamen-Enums** des Garmin FIT Java SDK (Profil **21.221.0**, 2026). Die englischen Originalbezeichnungen und die beiden unveränderten numerischen FIT-Codes sind für die Zuordnung entscheidend. Die vollständige Liste ist bereits in der Anwendung enthalten und benötigt dafür keine Internetverbindung.

**So funktioniert die Zuordnung:**
1. In der Trainingsliste ein oder mehrere Speediance-Trainings markieren → **Übungen zuordnen…**.
2. Links einen Speediance-Übungsnamen wählen. Optional links über das Textfeld filtern.
3. Rechts einen Begriff eingeben (z. B. `bench`, `fly`, `stretch` oder `lat`). Die Liste zeigt live Treffer aus dem vollständigen Katalog. Über **Kategorie filtern** lässt sich die Suche weiter eingrenzen. Ohne Suchbegriff erscheinen zunächst maximal 180 Einträge – nicht die gesamte Liste auf einmal.
4. Garmin-Übung anklicken. Das Programm setzt automatisch **Kategorie** und **ID / Unterkategorie**.
5. **Zuordnung speichern**, danach das Training neu als FIT exportieren.

**Was bedeuten die Zahlen?** In jeder Garmin-FIT-`set`-Nachricht kodiert Feld 7 die `exercise_category` (Übungsfamilie), Feld 8 die `category_subtype` (Übungsvariante). Beispielsweise ist `8 / 0` Langhantel-Kreuzheben und `0 / 1` Langhantel-Bankdrücken. `65534` bedeutet „unbekannt“ und darf nicht mit `0` (Bankdrücken) verwechselt werden.

Die numerischen Felder sind standardmäßig nur lesbar. Über **IDs manuell bearbeiten (Expertenmodus)** kann man sie in Ausnahmefällen selbst setzen. Das ist normalerweise nicht notwendig und kann bei falschen Zahlen zu falsch benannten Übungen in Garmin Connect führen.

Zusätzlich werden jetzt Speediance-Übungen, deren **englischer Name exakt und eindeutig** einem Garmin-FIT-Namen entspricht (z. B. `Barbell Bench Press` oder `Biceps Stretch`), automatisch zugeordnet. Individuell gespeicherte Zuordnungen haben Vorrang. Die übrigen Speediance-Namen bleiben zunächst unbekannt, bis sie bewusst einer Garmin-Übung zugeordnet werden. Nicht jede Speediance-Bewegung existiert als eigene Garmin-Unterkategorie; Garmin Connect kann außerdem eigene Anzeige-/Importregeln verwenden.

Der Datenkatalog basiert auf öffentlich verfügbaren Garmin-FIT-SDK-Enumwerten und enthält keine vom SDK kopierte Programmlogik. Quelle: https://github.com/garmin/fit-java-sdk (siehe dort geltende FIT-Protokoll-Lizenz).

## 0.1.11 – Zweisprachiger Garmin-Übungskatalog (DE / EN)

Im **Übungen zuordnen…**-Fenster befindet sich jetzt oben rechts eine separate Auswahl **Katalogsprache: Deutsch / English**. Standardmäßig übernimmt sie beim ersten Öffnen die Sprache der Hauptanwendung. Danach merkt sie sich die eigene Auswahl in `%LOCALAPPDATA%\\SpeedianceFITExporter\\settings.json` als `catalog_language` – unabhängig von der Hauptsprache. Die Änderung wirkt sofort ohne erneutes Laden der Trainingseinheiten; markierte Speediance-Übung, eingegebene Suchbegriffe, Kategorienfilter und noch nicht gespeicherte FIT-Codes bleiben erhalten.

- **Deutsch:** Zeigt deutsche Übungsnamen, soweit verfügbar (teilweise durch eine konservative Wortübersetzung), und daneben in Klammern den **originalen englischen Garmin-Namen** zur eindeutigen Zuordnung.
- **English:** Zeigt die **englischen Originalnamen** des Garmin-FIT-Profils.
- **Suche:** Unabhängig von der Anzeigesprache werden sowohl deutsche als auch englische Begriffe gefunden, z. B. `Langhantel` und `barbell` oder `Kreuzheben` und `deadlift`. Beide Sprachen verwenden unveränderte Garmin-Kategorie- und Unterkategorie-IDs. Alle 1.838 vorhandenen Garmin-Enumwerte bleiben erhalten und erscheinen nicht doppelt.
- **Wichtig:** Nicht jede der 1.838 Übungen hat eine redaktionell geprüfte deutsche Übersetzung. Unbekannte Fachbegriffe bleiben bewusst im englischen Original; die englische Bezeichnung dient zur Gegenprüfung. Das beeinflusst nicht die exportierten FIT-Codes.

## 0.1.12 – Ein Klick für die Übungszuordnung

**Vereinfachter Ablauf:** Links eine Speediance-Übung markieren, rechts im Garmin-Katalog die passende Übung anklicken und anschließend den neuen Button **„← Zuordnen“** direkt unter der rechten Liste drücken. Die Zuordnung wird **sofort lokal gespeichert** und erscheint unmittelbar in der linken Spalte **„Garmin-Zuordnung“**. Ein zusätzlicher Speicherdialog ist nicht erforderlich; so lassen sich mehrere Übungen nacheinander schneller zuordnen.

- Der Button wird erst aktiv, wenn links eine Speediance-Übung und rechts ein Garmin-Treffer ausgewählt wurden.
- Beim Wechsel auf eine andere Speediance-Übung wird die vorherige, noch nicht gespeicherte Garmin-Auswahl bewusst zurückgesetzt – das verhindert versehentliche Fehlzuordnungen.
- **Zuordnung entfernen** bleibt erhalten, um eine falsch gesetzte Zuordnung zurückzusetzen.
- Die technischen FIT-Felder **Kategorie / ID** werden weiter automatisch gesetzt; die manuelle Eingabe bleibt nur im Expertenmodus möglich.
- **Deutsch / English** werden für Button, Hinweise und Bestätigung unterstützt. Eine offene Zuordnung bleibt beim Wechsel der Katalogsprache erhalten.
- Die gespeicherten Zuordnungen werden beim nächsten FIT-Export berücksichtigt. Bereits in Garmin Connect importierte Aktivitäten ändern sich dadurch nicht.

## 0.1.13 – Herzfrequenz und Gesamtgewicht bei zwei Griffen

**Herzfrequenz:** Wenn eine Speediance-Trainingseinheit eine Aufzeichnungs-UUID enthält, fragt die Anwendung mit der **bereits angemeldeten Bike-/Nano-Sitzung** den schreibgeschützten Endpunkt `/api/app/watchMsg/getHeartRateGraph?uuid=...` ab. Von Speediance tatsächlich gelieferte Herzfrequenzwerte werden als FIT-`record`-Messpunkte (Feld 3: heart_rate) mitsamt aufgezeichnetem Sekundenoffset exportiert. FIT-`session` enthält daraus Durchschnitt und Maximum; es werden **keine Herzfrequenzwerte interpoliert oder geschätzt**. Leere/ungültige/0-Messungen bleiben ausgelassen. Die Zuordnung der relativen Sekunden erfolgt zum Start der Trainingseinheit – falls die externe Herzfrequenzaufzeichnung zeitversetzt begann, kann sich die Kurve zeitlich verschieben. Die Exportmeldung zeigt die Anzahl der Messpunkte und das anonymisierte Diagnoseprotokoll notiert, ob eine Aufzeichnungs-ID und wie viele Messwerte vorliegen, nicht aber Herzfrequenzwerte oder die ID selbst. Ist kein Graph abrufbar, wird das Training **ohne HF-Daten** exportiert, statt den Export zu blockieren. Der Dienst ist inoffiziell; ein echter Test mit einem gekoppelten Brustgurt steht noch aus.

**Gewicht bei zwei Griffen:** Die bisherigen `trainingInfoDetail.weights` wurden allein verwendet, auch wenn Speediance getrennte `leftWeights` und `rightWeights` liefert. Bei beidseitiger Bewegung verwendet der Exporter jetzt **max(leftWeights) + max(rightWeights)** als Gesamtgewicht; bei einseitiger Bewegung nur die aktive Seite. Das verhindert auch, dass abgeleitete `weights`-Kraftwerte als Widerstand missverstanden werden. Gibt es nur eine Gewichtsangabe, gilt für eindeutig benannte Übungen mit `Dual-Handle`, `Dual-Grip`, `Two-Handle` usw. standardmäßig **×2**, damit 5,5 kg pro Griff als 11 kg Gesamtgewicht nach Garmin gelangen.

**Individuelle Anpassung:** Über **Übungen zuordnen…** links eine Speediance-Übung markieren und unten die Checkbox **„Speediance-Gewicht pro Griff (×2 für Garmin)“** aktivieren oder deaktivieren. Die Einstellung wird sofort lokal gespeichert, ist pro Übung unterschiedlich und in der linken Tabelle als `×1` oder `×2` sichtbar. Eine explizite `×1`-Auswahl verhindert auch die automatische `×2`-Regel. Der Faktor gilt **nur dann**, wenn Speediance keine bereits getrennt auswertbaren Links-/Rechts-Werte liefert. Zwei bereits zusammengezählte Seiten werden niemals erneut verdoppelt. FIT-Export rechnet zusätzlich das eingestellte Anzeigegewicht bei Bedarf von lb nach kg um.

**Deutsch / English:** Die neue Gewichtseinstellung und die Exportmeldung sind zweisprachig.

**Wichtig:** Bereits importierte Garmin-Aktivitäten ändern sich nicht automatisch. Nach Änderung der Gewichtsregel oder zur Übernahme tatsächlich verfügbarer Herzfrequenzdaten muss die FIT-Datei erneut exportiert und in Garmin Connect importiert werden. Der Import kann eine bestehende Aktivität duplizieren.

Referenz für die inoffizielle Speediance-Cloud-API und die Links-/Rechts-Telemetrie:
https://github.com/labatt/speediance-mcp

## 0.1.14 – Herzfrequenzkurve und HF-Sensor in Garmin Connect

**Behobener HF-Parser:** Die Speediance-Cloud liefert eine gespeicherte Herzfrequenzkurve unter dem Feld `heartRates`, beispielsweise `{"heartRates":[96,110,128,142,158], "avgHeartRate":131, "maxHeartRate":158}`. Frühere Versionen erkannten dieses Feld nicht und importierten trotz HTTP 200 und aufgezeichneter Herzfrequenz **0 Messpunkte**. Ab 0.1.14 werden die Werte übernommen und die von Speediance gelieferten Durchschnitts- und Maximalwerte in die FIT-Zusammenfassung geschrieben.

**Zeitliche Auflösung:** Wenn die API nur die BPM-Liste ohne Einzelzeitstempel liefert, werden die *Positionen* der echten Messwerte gleichmäßig über die Workout-Dauer verteilt; es werden keine zusätzlichen Pulswerte erfunden. Diese Zeitachsen-Schätzung ist in der Exportmeldung und im anonymisierten Diagnoseprotokoll als `estimated_timing=True` kenntlich gemacht. Der Verlauf kann sich dadurch gegenüber der originalen Speediance-Grafik zeitlich unterscheiden. Fehlen alle Messpunkte, wird aus den echten pro-Satz-Maxima nur der maximale Puls abgeleitet, **keine gefälschte Kurve oder Durchschnitts-HF**.

**HF-Gerät in der FIT-Datei:** Der Exporter versucht, den Sensornamen aus ausdrücklich benannten Speediance-API-Feldern zu übernehmen. Wird nur in der Speediance-App die Datenquelle angezeigt (z. B. `HRM600:654360`), kann sie im Hauptfenster unter **HF-Sensor (optional)** einmal manuell eingetragen werden. Die Einstellung wird lokal gespeichert; sie dient nur als Rückfalllösung, wenn die Cloud keinen Gerätenamen liefert. Für den konkreten Eintrag wird `Garmin HRM 600` in der FIT-`device_info`-Nachricht als Gerät eingetragen, zusätzlich `HRM600:654360` als Beschreibung. Die Endziffern sind nicht verifiziert als Seriennummer und werden deshalb **nicht** als solche ausgegeben. Ohne eindeutige Daten setzen wir weder Garmin-Produkt-ID noch ANT-/Bluetooth-Protokoll. Ob Garmin Connect einen externen Sensor in der Aktivitätsansicht sichtbar anzeigt, richtet sich nach den Garmin-Importregeln.

**Deutsch / English:** Die Sensor-Eingabe, Statusanzeige und Zeitachsenwarnung sind zweisprachig.

Zum Überprüfen nach dem Upgrade das Training vom 16.11. erneut exportieren und die FIT-Datei in Garmin Connect importieren. Bereits importierte Aktivitäten werden nicht aktualisiert und können beim Import dupliziert werden.

## 0.1.15 – HF-Verlauf: Diagnose der Speediance-Messpunkte, manuellen Sensor entfernt

Das reale Diagnoseprotokoll der Trainingseinheit vom 16.11.2026 zeigte **942 `heartRates`-Einträge**, aber **0 erkannte Einzelmessungen**. Durchschnitts-/Maximalpuls aus der Speediance-Zusammenfassung wurden dagegen korrekt exportiert. Deshalb wird die Dateninterpretation nun robuster: Neben `heartRate` werden beispielsweise `heartRateValue`, `realHeartRate`, `currentHeartRate` und andere eindeutig bezeichnete Messwertfelder erkannt. Zeit-, Maximum-, Durchschnitts-, Ziel- und Gerätefelder werden **nicht** als Messpunkte behandelt. Ist weiterhin kein verwertbarer Puls vorhanden, notiert das lokale Protokoll die **Elementtypen** und eine streng begrenzte Menge bekannter Feldnamen und Zählwerte – niemals Pulszahlen, UUIDs, Geräte-IDs oder beliebige unbekannte API-Feldnamen. Das dient der nächsten gezielten Analyse der Speediance-Antwortstruktur.

Das bisherige Eingabefeld **„HF-Sensor (optional)“** wurde **vollständig entfernt**, ebenso die Speicherung neuer manueller Angaben. Die bereits lokal gespeicherte Einstellung `hr_sensor_name` wird nicht mehr gelesen oder verwendet. Falls die Speediance-API selbst ein bekanntes Herzfrequenz-Gerätemodell übermittelt, darf es weiterhin automatisch in die FIT-`device_info`-Nachricht übernommen werden. Garmin Connect entscheidet selbst, ob eine solche Metadaten-Nachricht bei manuell importierten Aktivitäten angezeigt wird.

**Hinweis:** Eine bei Garmin Connect vorhandene FIT-Datei mit einer echten HF-Kurve ist ein wertvoller technischer Vergleich für die `record`- und `device_info`-Felder. Die API gibt noch keinen Zugriff auf solche Referenzdateien; diese müssen als tatsächliche `.fit`-Datei im Chat angehängt werden.

## 0.1.16 – Herzfrequenz-Diagnose konkretisiert

Das reale Protokoll von 0.1.15 zeigt `heartRates` mit **942 Objekten**, in denen `heartRate` und `time` vorhanden sind; bisher werden daraus dennoch null gültige Messpunkte. Die Ursache steht noch **nicht** fest – möglich sind beispielsweise null/ungültige Pulswerte, spezielle Zeitformate oder ein verschachtelter Datentyp.

Die neue Diagnosezeile `Heart-rate sample structure unrecognized:` enthält ab 0.1.16 zusätzlich:

- `heartRate_types` – nur Datentyp und Anzahl des Feldes `heartRate`
- `heartRate_status` – Anzahlen von `valid`, `zero`, `below_range`, `above_range`, `nonnumeric`, `absent`
- `time_types` und `time_status` – Zeitwerttypen und Zählwerte

Die Ausgabe enthält **keine** Herzfrequenz-Messwerte, Zeitstempel, Gerätekennungen oder beliebigen unbekannten Feldnamen. So lässt sich der verbleibende Fehler gezielt eingrenzen. Die bisherigen FIT-Trainingsdaten und echte HF-Messwerte werden unverändert behandelt.

**Test:** Mit 0.1.16 das Training vom 16.11. erneut exportieren und die neue Warnzeile aus `Diagnose anzeigen…` bereitstellen. Falls nun Messpunkte erkannt werden, in Garmin Connect kontrollieren, ob ein vollständiger Verlauf erscheint. Es werden keine Pulsdaten aus einer Fenix-FIT-Datei übernommen.

## 0.1.17 – 942 echte Herzfrequenzwerte mit Speediance-Zeitstempeln

Das reale Protokoll von v0.1.16 hat die Ursache präzise lokalisiert:
`heartRates` enthält **942 Objekte** mit **942 gültigen `heartRate`-Werten** (`int`); auch `time` ist **942-mal `int`**, aber **alle Werte sind größer als 86.400**. Bisher wurden die Messungen vollständig verworfen, weil der Parser ausschließlich Sekunden seit Trainingsbeginn unterhalb von 24 Stunden erlaubte.

**Korrektur:** Der Exporter klassifiziert die `time`-Werte jetzt pro Aufzeichnung und unterstützt unter anderem:

- absolute Unix-Zeitstempel in Sekunden, Millisekunden oder Mikrosekunden; sie werden mit dem wirklichen Trainingsbeginn verglichen
- Sekunden/Millisekunden seit Trainingsbeginn und gegebenenfalls lokale Tageszeit
- unbekannte Zeitursprünge mit plausibler *echter* Zeitdifferenz: Relativzeit wird an den Trainingsbeginn angehängt; diese Platzierung ist in Exportmeldung und Diagnose ausdrücklich als **geschätzt** gekennzeichnet

Die echten BPM-Messungen werden nicht interpoliert oder verändert, ebenso wenig werden die Zeitabstände zwischen den Messungen absichtlich gestreckt. Aufzeichnungen, deren Zeitwerte nicht sicher oder zumindest plausibel in diese Skalen fallen, bleiben sicherheitshalber ohne erfundene Herzfrequenzkurve. Die anonymisierte Diagnose nennt `time_mode` und die Zahl ausgelassener Zeitpunkte.

**Einheitliche Trainingsuhr:** FIT-Sitzung und HR-Import nutzen dieselbe Berechnung des Trainingsbeginns; wenn die abgeschlossene Trainingshistorie eine `startTime` liefert, wird diese statt eines aus Endzeit minus Dauer berechneten Starts verwendet. Der gewohnte direkte Speediance→Garmin-FIT-Export bleibt der einzige Workflow; die Fenix-8-Datei dient nur als Referenz und wird nicht eingemischt.

**Überprüfung:** Mit 0.1.17 die Trainingseinheit vom 16.11.2026 erneut exportieren. Erwartet wird, dass im Diagnoseprotokoll jetzt ein `time_mode=` erscheint und bei unterstützten Zeittypen die 942 Speediance-Pulswerte als FIT-`record`-Messpunkte übernommen werden. Die tatsächliche Zeitkonvention wird erst durch diesen Praxis-Test bestätigt; bei `0 measured samples` bitte die vollständige `Heart-rate graph:`-Zeile bereitstellen.

## 0.1.18 – tatsächlich ausgeführte Satzgewichte statt Höchstwert

Beim Vergleich eines Trainings am 16.11.2026 mit den tatsächlichen Einstellungen am Gym Monster fiel eine Abweichung auf: Bei **„Sitzendes Rudern mit zwei Griffen“** waren **26 kg im FIT-Import**, nach einer Korrektur am Gerät aber **20 kg ausgeführt** worden.

Bisher hat der Exporter in den aufgezeichneten `trainingInfoDetail.weights` bzw. `leftWeights`/`rightWeights` pro Satz **`max()`** genommen. Eine kurzzeitige höhere Vorgabe oder ein Einstellwert kann dadurch fälschlich zum ausgeführten Gewicht werden. Jetzt wird aus den *aufgezeichneten positiven Messwerten dieses Satzes* der am häufigsten vorkommende Gewichtswert ausgewählt; bei Gleichstand zählt der letzte Wert. Nullen nach dem Ausklinken werden ignoriert. Sind separate Links-/Rechts-Serien vorhanden, werden sie unabhängig ausgewertet und bei zwei Griffen einmalig summiert. Der vorhandene per-Übung-Multiplikator wird nicht noch einmal darauf angewendet.

Die Gewichte stammen weiterhin direkt aus den Speediance-*Trainingsaufzeichnungen*, nicht aus einem GM-Manager-Trainingsplan. Ein neuer, datensparsamer Diagnoseeintrag `Weight source of completed sets:` nennt je Training nur die Anzahl der gewählten Datenquellen (`both_sides`, `single_side`, `generic_telemetry`, `missing`) und wie viele Satzserien unterschiedliche Gewichte enthalten – keine Gewichtszahlen oder persönliche Identifikatoren. Falls für einen Satz ausschließlich generische `weights`-Telemetrie verfügbar ist, weist das Protokoll auf diese Unsicherheit hin.

**Einschränkung:** Ohne das Original der privaten Speediance-API-Antwort lässt sich nicht sicher bestätigen, ob die korrigierten **20 kg** tatsächlich in den gespeicherten Satzserien vorhanden sind. Die Fehlerursache `max()` ist behoben, aber die reale Aufzeichnung muss den neuen Wert liefern. Nach einem Export mit 0.1.18 bitte den konkret betroffenen Satz in Garmin Connect kontrollieren und bei unverändert 26 kg die neue Diagnosezeile teilen; dann muss die Quelle genauer untersucht werden.

## 0.1.19 – offizielle Garmin Personal API und individuell wählbare Datenpriorität

**Voraussetzungen:** eigener Garmin Connect Personal API-Schlüssel und eine bereits
vorhandene, zeitlich passende Garmin-Connect-Aktivität. Den Schlüssel in Garmin Connect
unter [Personal API](https://connect.garmin.com/app/settings/personalApiToken) erzeugen.
**Keinen Schlüssel in Chat, Issue, Log oder GitHub hochladen.**

1. Mit Speediance anmelden, Trainingseinheiten laden und **genau eine** Einheit auswählen.
2. **„Mit Garmin abgleichen…“** öffnen und den persönlichen API-Schlüssel **lokal**
   eingeben. Optional kann Windows Credential Manager den Schlüssel geschützt für
   spätere Aufrufe speichern. Der Schlüssel wird weder in `settings.json` noch
   in `diagnose.log` gespeichert.
3. Für sechs getrennte Felder Garmin oder Speediance als bevorzugte Quelle einstellen:
   **Herzfrequenzkurve**, **Durchschnittspuls**, **Maximalpuls**, **Kalorien**,
   **Trainingsbeginn** und **Trainingsdauer**. Die Auswahl (ohne Geheimnisse)
   bleibt lokal gespeichert. Standard: jeweils Garmin.
4. **„Garmin-Aktivitäten suchen“** ruft die offizielle **schreibgeschützte**
   Personal API auf. Nur ausreichend passende Trainingszeiten und -dauern werden
   angeboten; bei mehreren Kandidaten die richtige Garmin-Aktivität auswählen.
5. **„Zusammengeführte FIT speichern…“** liest die ausgewählte ursprüngliche
   Garmin-FIT-Datei und erstellt eine **neue lokale** FIT-Aktivität mit den
   Speediance-Übungen, Wiederholungen, Satzgewichten und den nach gewählter
   Priorität kombinierten Messwerten.

**Messwertkonflikte:** Pro FIT-Zeitpunkt gewinnt der gewählte Herzfrequenzverlauf.
Eine echte Messung aus der anderen Quelle kann eine fehlende Sekunde ergänzen.
Gemessene Pulswerte werden nicht erfunden. Für die Zusammenführung werden die
absoluten Aufnahmezeiten verwendet, und die Speediance-Sätze bleiben auf ihrer
ursprünglichen Zeitachse, selbst wenn der Garmin-Startzeitpunkt früher liegt.
Falls die gewählte Trainingsdauer Aufnahmen ausschließt, wird die Zahl
ausgeschlossener Zeitpunkte angezeigt. Die Geräteidentität wird nicht
irreführend in die neue FIT-Datei kopiert.

**Wichtig:** Die offizielle Garmin Personal API ist **nur zum Lesen**.
Es gibt dort keinen unterstützten Schreibendpunkt, um eine in Garmin Connect
bestehende Aktivität zu verändern. Deshalb wird **niemals** automatisch etwas
in Garmin Connect gelöscht, ersetzt oder hochgeladen. Eine später manuell
hochgeladene zusammengeführte FIT-Datei kann als **zweite Aktivität** erscheinen.
Bitte vor dem Import prüfen, ob du die ursprüngliche Garmin-Aktivität behalten
möchtest. Der bisherige direkte Speediance→FIT-Export funktioniert unabhängig
davon weiter. Der zusammengeführte Export übernimmt keine vollständigen
Garmin-GPS-Tracks, Sensor-Rohfelder oder alle proprietären Metadaten, sondern
nur die oben genannten Messwerte.

Die Umsetzung nutzt die dokumentierten Endpunkte für den API-Key-Tokenaustausch,
die Aktivitätssuche und den **originalen ZIP/FIT-Download**, ohne private
Garmin-Endpunkte oder Passwort-Automation. Automatisierte Tests verwenden
fiktive Token und FIT-Aufzeichnungen. Der tatsächliche Datenabruf muss noch
mit einem lokal eingegebenen persönlichen Schlüssel im Zielkonto geprüft werden.

## 0.1.20 – Garmin-FIT als Originalbasis (kein rekonstruiertes Speediance-FIT)

**Fehler in 0.1.19:** Die Garmin-API hat die echte Fenix-FIT-Datei
heruntergeladen, danach wurden jedoch nur Puls-/Zeit-/Kalorienwerte extrahiert
und mit dem minimalistischen Speediance-Schreibprogramm ein neues FIT
erzeugt. Native Garmin-Geräteinformationen, Sensor-/Developer-Blöcke und
proprietäre Trainingsdaten gingen dabei verloren. Dadurch sah der Import
überwiegend wie ein reiner Speediance-Export aus.

**Korrektur in 0.1.20:** Der Garmin-Originalexport ist jetzt *binär* die
Ausgangsdatei. Die FIT-Nachrichten werden einzeln gelesen und unverändert
wieder ausgegeben; nur bewusst ausgewählte Felder dürfen angepasst werden.
Die ursprünglichen Garmin-Records (HF und andere Metriken), vollständigen
`device_info`-Meldungen, Garmin-eigenen Zusatzfelder und proprietären
Nachrichten bleiben erhalten. Im Test bleiben Garmin-Record-Nachrichten
sogar byteidentisch, sofern die Herzfrequenzpriorität Garmin lautet.

- Alle bestehenden Garmin-SET-Nachrichten (`global 225`) werden in dieser
  **neuen** Datei durch die detaillierten tatsächlichen Speediance-Sätze
  ersetzt, damit die Übungs-/Satzdaten nicht doppelt vorkommen. Die
  bewährte Gewichtsumrechnung aus 0.1.18 bleibt unverändert.
- Mit **Garmin als Herzfrequenzquelle** werden die nativen Garmin-HF-Records
  nicht überschrieben. Echte zusätzliche Speediance-Messungen ergänzen
  nur fehlende FIT-Zeitstempel. Mit **Speediance als bevorzugter Quelle**
  wird gezielt der HF-Wert in überlappenden Garmin-Records aktualisiert –
  alle anderen Sensorfelder desselben Garmin-Records bleiben unverändert.
- Durchschnitts-/Maximalpuls und Kalorien können pro Feld weiterhin
  Garmin oder Speediance bevorzugen. Bei einem einzelnen Garmin-Lap können
  dessen Summen ebenfalls abgeglichen werden; mehrere individuelle Garmin-
  Runden bleiben unangetastet. Multisport-FITs mit mehreren Sitzungen
  werden aus Sicherheitsgründen abgelehnt.
- Die originale `file_id` der Fenix wird in der **abgeleiteten Kopie**
  als Entwicklungs-/Merge-Datei mit eigener reproduzierbarer Seriennummer
  gekennzeichnet. Das vermeidet die identische Geräte-Datei-ID, ohne
  die originalen Garmin-`device_info`-Meldungen zu verfälschen.
- Garmin FIT wird **nirgends auf Garmin Connect** geändert: nur
  Herunterladen per Personal API und Speichern einer neuen lokalen FIT.
  Der spätere manuelle Import kann ein Duplikat verursachen oder von
  Garmin Connect als schon bekannte Aktivität zurückgewiesen werden;
  das lässt sich ohne offizielle Schreib-API nicht garantieren.
- **Datenpriorität Trainingsbeginn/-dauer:** Garmin empfohlen, wenn die
  Garmin-Aufzeichnung vollständig bleiben soll. Bei Auswahl Speediance
  werden Sitzungs-Zusammenfassungsfelder angepasst, die ursprünglichen
  Garmin-Sensormeldungen außerhalb der kürzeren Speediance-Dauer werden
  jedoch **nicht zerstört**. Dadurch können Zeitangaben von
  Detailmessungen und Session-Summary voneinander abweichen.
- Die genauen Startzeiten einzelner Speediance-Sätze sind weiterhin
  nicht unabhängig bestätigt; wo die API nur Satzdauern liefert,
  bleiben die Satzzeitpositionen geschätzt. Es werden keine
  Garmin-Messwerte erfunden.

**Diagnose:** Der neue Merge-Logeintrag nennt die Zahl der erhaltenen
Garmin-Nachrichten/-Meldungstypen, Geräteinformationen, ersetzten
Garmin-Sätze und ergänzten Speediance-Sätze. Es werden keine originalen
Garmin-Privatfelder, API-Schlüssel, Nutzernamen oder Pulswerte geloggt.

Der vollständige Neuaufbau als reine Speediance-FIT-Datei bleibt als
**separater** Exportknopf vorhanden. Der Originaldatei-basierte Garmin-Merge
wird ausschließlich über **„Mit Garmin abgleichen…“** aufgerufen.

## 0.1.21 – lokale Garmin-FIT und Speediance-FIT bei API-Ausfällen

Die Garmin Personal API ist jetzt **optional**. Im Fenster
**„Mit Garmin abgleichen…“** gibt es zwei Garmin-Quellen:

- **Garmin Personal API:** vorhandenen Schlüssel lokal verwenden und
  Garmin-Aktivitäten über die offizielle schreibgeschützte API suchen.
- **Lokale Garmin-FIT-Datei:** eine selbst aus Garmin Connect exportierte
  **originale `.fit`-Aktivität** auswählen. Es ist **kein Garmin-API-Schlüssel**
  nötig. Der Exporter prüft die Dateistruktur samt CRC, verlangt eine
  Original-Garmin-Datei (nicht einen Speediance-/Merge-Export), prüft eine
  einzelne Sitzung und gleicht Beginn und Dauer mit dem ausgewählten
  Speediance-Training ab (**max. 20 Minuten Startdifferenz**, **max. 40 %
  Dauerabweichung**). Die ursprüngliche Datei wird nicht verändert.

Die Garmin-Aktivitätssuche und die lokale Garmin-Dateiprüfung laufen jetzt
**unabhängig** vom Abruf der Speediance-Satzdetails. Dadurch lässt sich die
Garmin-Seite zuverlässig auswählen, auch wenn Speediance einen Fehler liefert.

### Wenn Speediance für ein Training keine Übungsdetails mehr liefert

In einem Praxistest lieferte `cttTrainingInfoDetail` zeitweise
`code=100041`, die anderen Routen `403` oder keine Sätze, obwohl
dieses Training zuvor erfolgreich exportiert worden war. Ursache auf
Speediance-Serverseite weiterhin unbestätigt.

1. Für den Detailabruf probiert der Exporter zusätzlich zu den normalen
   schreibgeschützten Routen die ältere Versionskennung `40304` – **ohne**
   Anmeldung unter einem anderen Client-Typ.
2. Zusätzlich kannst du im Garmin-Merge-Fenster unter
   **„Bei Speediance-API-Ausfall“** einen **bereits früher erfolgreich
   erzeugten direkten Speediance-`.fit`-Export** dieses Trainings wählen,
   z. B. mit Version 0.1.18. Die Datei muss zu genau derselben
   Speediance-Trainings-ID gehören und eine einzelne Krafttrainings-Sitzung
   mit aufgezeichneten Sätzen enthalten. Die Prüfung erfolgt lokal.
3. Liefert Speediance wieder Sätze, verwendet der Merge die aktuellen
   Cloud-Daten. Scheitert der Detailabruf, nimmt er stattdessen die
   in der lokalen Speediance-FIT vorhandenen **echten Gewichte, Sätze,
   Wiederholungen und Zeitstempel**, ohne neue Werte zu schätzen.
   Die ursprünglichen Speediance-`SET`-Nachrichten werden direkt
   übernommen, statt durch einen neuen Plan ersetzt zu werden.
   Falls weder Cloud noch passende Backup-FIT vorhanden sind, wird der
   Merge abgebrochen. **Keine leeren oder erfundenen Trainingseinheiten.**

Beide Eingabe-FIT-Dateien bleiben unverändert; die neu erzeugte Datei
muss unter einem **anderen Dateinamen** gespeichert werden.
Passende Garmin-Sensor-/Geräteinformationen werden weiterhin binär
erhalten; die bisherige Auswahl der Datenprioritäten bleibt bestehen.
Garmin Connect wird über die Personal API **niemals verändert**.

**Hinweis:** Ein lokaler Garmin-Export ersetzt *nur* die Garmin-API.
Für Speediance-Sätze ist weiterhin der Speediance-Detailabruf
**oder eine früher erzeugte Speediance-FIT** notwendig.
Ob die neue Version den konkreten Speediance-API-Fehler
`100041` über die alte Versionskennung beheben kann, lässt
sich erst im echten Konto feststellen.

## 0.1.22 – vereinfachtes Handling: Speediance-Training + Garmin-FIT

**Nur zwei Quellen:** Speediance liefert die **fertig aufgezeichneten Übungen,
Sätze, Wiederholungen und tatsächlichen Gewichte direkt per Cloud-API**;
Garmin liefert die **Original-FIT-Datei** über die persönliche Garmin-API
**oder** über den Dateiauswahldialog. Der Nutzer muss **keine
Speediance-FIT-Datei besitzen oder extra erzeugen**.

1. Bei Speediance anmelden und **eine abgeschlossene Trainingseinheit**
   markieren.
2. „Mit Garmin abgleichen…“ anklicken und entweder „Lokale Garmin-FIT-Datei“
   (jetzt voreingestellt) oder „Garmin Personal API“ verwenden.
3. Die passende Fenix/Garmin-Aktivität auswählen, Datenprioritäten festlegen
   und eine **neue** Garmin-basierte FIT-Datei erzeugen.

Die in 0.1.21 eingeführte zusätzliche **Speediance-FIT-Dateiauswahl ist aus
der Benutzeroberfläche entfernt**. Die Trainingsliste selbst enthält nur
Zusammenfassungen; tatsächliche Satzgewichte stehen erst im
Speediance-Detailabruf. Ein Hinweis auf eine notwendige Speediance-FIT
wäre deshalb irreführend.

### Lokaler Cache für fertig absolvierte Speediance-Trainings

Sobald der Exporter eine abgeschlossene Trainingseinheit **einmal
erfolgreich** vollständig von Speediance erhalten hat, bewahrt er die
aufgezeichneten Satzdaten und die vorhandenen echten Herzfrequenzmessungen
automatisch unter
`%LOCALAPPDATA%\\SpeedianceFITExporter\\completed_training_cache`
für den aktuellen Windows-Benutzer auf. Weitere FIT-Exporte und Garmin-Merges
derselben Trainingseinheit können diese bereits abgefragten Daten
wiederverwenden, ohne einen fehleranfälligen erneuten Detailabruf.

Der Cache wird nach Speediance-Account, Serverregion und Trainings-ID
getrennt und beim Lesen auch gegen das Trainingsdatum abgeglichen.
Die lokalen JSON-Dateien enthalten **Trainings- und Pulsmessdaten**,
aber **keine Passwörter, Tokens, Sensor-IDs oder API-Antwort-UUIDs**.
Sie werden nicht automatisch synchronisiert oder hochgeladen.
Wer diese lokal gespeicherten Trainingsdaten löschen möchte, kann den
oben genannten Ordner entfernen.

**Grenze:** Hat Speediance die Satzdetails noch **nie erfolgreich an
0.1.22** geliefert, ist der Cache natürlich noch leer. Die ältere
Version `40304` wird bei einem API-Fehler zusätzlich abgefragt,
doch wenn Speediance weiterhin `100041` / `403` oder keine
abgeschlossenen Sätze zurückliefert, ist ein zuverlässiger Merge
dieses Trainings aktuell nicht möglich. Der Exporter stoppt dann
ausdrücklich, statt geplante Gewichte als ausgeführte auszugeben.
Ein Cache aus früheren Versionen 0.1.18–0.1.21 wird nicht
rückwirkend erzeugt.

Der direkte Speediance→FIT-Export, die Wahl zwischen Garmin-API und
lokaler Garmin-FIT und alle einzelnen Messwert-Prioritäten bleiben erhalten.
Garmin Connect wird beim Merge ausschließlich **gelesen**.
Eine spätere manuelle Einfuhr kann eine zusätzliche Aktivität erzeugen.

---

## 0.1.23 – Diagnose gelöschter Vorlagen vs. absolvierte Einheit

**Beobachtung:** Das Custom-Training vom 16.11.2026 war früher erfolgreich
auslesbar (9 Übungen, 27 Sätze); nach Löschen der zugehörigen Vorlage
liefert `cttTrainingInfoDetail` den API-Code `100041` – auch in der
alten Version 0.1.18. Der Eintrag steht weiter im Speediance-Kalender
und in der Trainingshistorie. Ein unabhängiger Detail-Endpunkt für
gelöschte Vorlagen ist derzeit **nicht belegt**.

Die Version 0.1.23 vergleicht vorhandene Daten aus
`userTrainingDataRecord` mit der Kalenderansicht. Bei einem Treffer
schreibt sie ins Diagnoseprotokoll
`Completed workout history cross-reference:` mit
`history_fields`, `id_vs_trainingId`, `calendar_type` und
`history_type`. Es werden **keine tatsächlichen Kennungen, UUIDs,
Trainingsnamen, Zeitpunkte oder Messwerte** geloggt.

Die Server-Historie ist bei unterschiedlichen Trainingstypen künftig
die maßgebliche Quelle für die **Reihenfolge der bereits bekannten**
read-only Detail-Endpunkte. Andere IDs werden nicht auf Verdacht
abgefragt. Ist die Detail-Aufzeichnung dennoch nicht erreichbar,
wird **kein** Export mit geplanten oder erfundenen Satzgewichten erzeugt.

**Für die Diagnose** die neueste Version öffnen, Speediance anmelden
und Trainingsliste laden. Im Diagnoseprotokoll die Zeile
`Completed workout history cross-reference` teilen. Danach kann
entschieden werden, ob ein unabhängiger Datensatzschlüssel vorhanden
ist und welcher nachweislich gültige Endpunkt ihn nutzt.
Der Garmin-Merge und die lokale Garmin-FIT-Auswahl bleiben unverändert.

## 0.1.24 – Verlauf eindeutig pro ausgewählter Trainingseinheit prüfen

Die allgemeine `Completed workout history cross-reference`-Zeile der
Version 0.1.23 kann sich auf **eine andere Einheit** beziehen.
Beim Test war `calendar_type=1` mit `history_type=2` verknüpft,
während die ausgewählte Custom-Trainingseinheit zuerst den
`cttTrainingInfoDetail`-Endpunkt nutzte. Deshalb war keine eindeutige
Zuordnung dieser Diagnose zum 16.11. belegt.

Nach dem normalen Klick auf **„Trainings laden“** protokolliert 0.1.24
jetzt für **jede sichtbare Listenzeile** eine knappe
`Workout history provenance row=N`-Diagnose. `row=1` bezeichnet die
oberste Einheit der angezeigten Liste – im beschriebenen Beispiel
„GMC · Mon 16 Nov“.

Diese Zeile enthält nur **boolesche Aussagen und Anzahlen**:
`matched_by_trainingId`, `history_on_same_day`,
`same_day_same_title`, `same_day_close_duration`,
`same_day_title_and_duration`. Die Diagnose verrät keine IDs,
Datums-/Uhrzeitangaben, Namen, Trainingswerte oder Zugangsdaten.
Daten werden ausschließlich aus dem bereits abgerufenen
Kalender-/Historienergebnis abgeglichen; **keine zusätzlichen API-Requests**.

Damit kann sauber unterschieden werden, ob der ausgewählte Kalender-
Trainingsdatensatz in der abgeschlossenen Historie mit gleicher ID
vorliegt, nur als möglicherweise anderer Datensatz am gleichen Tag
erscheint oder gar nicht dort vertreten ist. Ein Treffer nach Titel
und Dauer allein führt **nicht** zum automatischen Austausch der
Trainings-ID. Solange der richtige Satz-Detail-Endpunkt nicht verifiziert
ist, werden keine Planwerte als ausgeführt exportiert.

**Nächster Test:** Nur anmelden, Trainingsliste laden und die Zeile
`Workout history provenance row=1` senden. Danach können wir gezielt
ermitteln, ob überhaupt eine getrennte Aufzeichnungskennung vorhanden
ist. Die Garmin-FIT-Funktionen bleiben unverändert.

## 0.1.25-beta – Strukturprüfung der tatsächlich gelieferten Speediance-Daten

Damit wir den fehlenden Satzimport nicht weiter durch bloße API-Vermutungen ersetzen,
gibt es nach **Trainings laden** eine neue Schaltfläche
**Speediance-Datensatz prüfen…**. Genau eine Zeile markieren und anklicken.

Die Anwendung protokolliert die **bereits empfangene** Struktur der ausgewählten
Historien- bzw. Kalenderantwort, darunter Feldpfade, Typen und Listenlängen.
Danach prüft sie ausschließlich lesend bis zu acht bereits bekannte
Trainingsdetail-Routen/-Versionen und protokolliert deren **Antwortstruktur**
(auch bei leeren Antworten). So können wir unterscheiden, ob die Historie
bereits verschachtelte Übungsdaten enthält oder ein anderer Endpunkt nötig ist.

Der Diagnoselauf zeigt am Ende automatisch **Diagnose anzeigen…**.
Die relevanten Abschnitte beginnen mit
`Selected Speediance workout API structure BEGIN` und enden mit
`Selected Speediance workout API structure END`.
Die Antwortwerte selbst werden **nicht** gespeichert oder protokolliert:
keine Benutzernamen, Trainingstitel, Übungen, Wiederholungszahlen,
Gewichte, Datumswerte, Token oder numerischen Trainingskennungen.
Bitte das Protokoll trotzdem vor Weitergabe prüfen.

**Diese Version ist eine Diagnose – kein belegter Fix des Satzabrufs.**
Ob und wo das private Speediance-Backend wirklich abgeschlossene Sätze
zurückliefert, muss anhand des echten ausgewählten Datensatzes geklärt werden.

## 0.1.26-beta – Gezielter Test des recordId-Verweises

Die echte Strukturdiagnose der abgeschlossenen Einheit zeigt
`trainingPartSetsInfoList` mit drei **aggregierten** Trainingsteilen sowie
`aiEntryPageReq.trainingParam.recordId` als separate Zeichenketten-Kennung.
Die bisherigen GET-Detailabfragen mit `trainingId` lieferten nur
`100041`, `403` oder leere Listen. Weder Übungsnamen noch
Wiederholungen/Gewichte sind damit derzeit belegt.

Mit **Speediance-Datensatz prüfen…** untersucht Version 0.1.26
zunächst die bisherigen acht Abfragen und danach – **ausschließlich
lesend** – dieselben bekannten Routen mit dem tatsächlich
im ausgewählten Historieneintrag enthaltenen `recordId`, sofern
die Kennung ein sicheres Pfadformat hat.
Die Kennung wird nur während der Sitzung im Speicher gehalten und
**niemals** in das Diagnoseprotokoll geschrieben.

Im neuen Abschnitt `Selected recordId detail route=` stehen nur
Routenname, verwendete API-Version und die wertfreie Antwortstruktur.
Die Schlusszeile meldet zusätzlich `record_ref_checked` und
`record_ref_responses_with_completed_sets`. Keine Trainingswerte
oder Anmeldedaten teilen.

**Diese Version übernimmt aus recordId-Antworten noch keine Sätze in den
FIT-Export.** Erst eine Antwort mit nachweislich abgeschlossenen Sätzen
rechtfertigt eine Änderung der Exportlogik. So vermeiden wir
eine erneute falsche Erfolgsmeldung oder erfundene Trainingsdaten.

## 0.1.27-beta – Bestätigte GM-Manager-Satzwerte für Garmin-FIT-Merge

Wenn Speediance für eine abgeschlossene Trainingseinheit keine Sätze mehr
über die offizielle/unoffizielle Detail-API liefert, kannst du im
**Garmin-Abgleich** optional eine lokale GM-Manager-JSON-Datei verwenden.

1. Trainingshistorie laden und **die tatsächlich absolvierte Trainingseinheit**
   auswählen.
2. **Mit Garmin abgleichen…** öffnen.
3. Unter **Datenpriorität** auf **GM-Manager-JSON wählen…** klicken und die
   bereits aus GM Manager exportierte Datei auswählen (Format:
   `app: gmvoice-speediance`, `kind: custom-workouts`, `version: 1`).
4. Der Exporter verlangt einen **eindeutigen gleichen Trainingsnamen** und
   zeigt vor Übernahme die Zahl der Übungen und Sätze. Bestätige nur dann,
   wenn **die Wiederholungen und Gewichte tatsächlich absolviert wurden**
   und die Einheit/Gewichtswerte richtig sind.
5. Wie bisher die **originale Garmin-FIT** prüfen oder eine passende Garmin
   Personal-API-Aktivität auswählen und dann **Zusammengeführte FIT speichern…**.

Die GM-Manager-Datei selbst ist ein Export von **Planvorgaben**, keine
aufgezeichnete Sitzung. Die explizite Bestätigung ist daher erforderlich;
die Werte werden als **vom Nutzer bestätigt**, nicht als Live-Messungen
von Speediance, gekennzeichnet. Die zehn-/hundertsekündigen Cardio- und
Mattenangaben werden als **zeitbasierte Sätze** interpretiert, nicht als
`300` Wiederholungen. Gewichte werden exakt übernommen (kein
stillschweigendes Verdoppeln). Es werden keine Trainingsbeginne oder
Kalorien aus dem GM-Manager-JSON erfunden.

**Grenzen:** GM Manager liefert keine tatsächlich erfassten Satzzeitpunkte;
diese werden innerhalb der ausgewählten Trainingsdauer geschätzt.
Die originalen Garmin-Sensor- und `record`-Nachrichten bleiben erhalten,
aber das bisherige Garmin-`SET` wird durch die bestätigten 24 Sätze (19
Kraftsätze, 5 zeitbasierte Sätze im Referenztraining) ersetzt.
Die Übungsnamen werden anhand der Gruppenkennungen lesend aus der
Speediance-Übungsbibliothek nachgeladen, falls verfügbar. Scheitert das,
wird die Gruppenkennung als Platzhalter im FIT-Übungsnamen sichtbar.
Garmin Connect kann frei definierte Übungsnamen bei importierten Aktivitäten
abweichend darstellen.

Der Import erfordert **keine Änderung der Cloud-Trainingsdaten** und stellt
keinen nachgewiesenen Fix des problematischen Detail-Endpunkts dar.
Zur zuverlässigen Garmin-Connect-Anzeige ist ein echter manueller
Importtest erforderlich.

## 0.1.28-beta – GM-Manager-Workout-History-CSV als Satzquelle

Der bisherige JSON-Import aus 0.1.27 liest einen **Trainingsplan**, der
erst durch deine Bestätigung als tatsächlich absolviert behandelt werden
darf. Der neue **History-CSV-Import** dagegen liest die vom GM Manager
exportierte Historie der tatsächlich aufgezeichneten Trainingseinheit.

**Ablauf:** Speediance-Training auswählen, **Mit Garmin abgleichen…**
öffnen, unter Datenpriorität **GM-Manager-History-CSV wählen…** klicken
und die originale History-CSV auswählen. Der Exporter verlangt
*gleiches Trainingsdatum und gleichen Trainingsnamen*, genau eine
CSV-Sitzungs-ID und eine passende Trainingsdauer. Erst nach Bestätigung
werden die Zeilen als Satzquelle gewählt. Danach die originale
Garmin-FIT wählen bzw. über die Personal API lesen und die
**zusammengeführte FIT** speichern.

**Referenztraining vom 16.11.2026 (nicht im Repository gespeichert):**
9 verschiedene Übungen, **27 aufgezeichnete Satzzeilen** (19 Kraft,
8 zeitbasiert), **184 Wiederholungen**, **6 separat erfasste
Links-/Rechts-Dehnzeilen**. Die früher verwendete JSON-Vorlage
enthält nur 24 Satzvorgaben und bildet diese Trennung nicht vollständig ab.

**Bereits implementierte Schutzmaßnahmen bleiben erhalten:**
- Das Garmin-FIT bleibt binäre Grundlage; originaler Garmin-HF-Verlauf,
  Sensor- und Geräteinformationen bleiben nach gewählten Prioritäten
  erhalten. Die vorhandenen Garmin-Sätze werden nur im neuen
  Export ersetzt.
- Die Gewichtskorrektur von **0.1.18** bleibt unverändert. Der
  CSV-Importer verwendet **exakt das dokumentierte Gewicht pro Satz**
  aus der Spalte Weight (kg); er verdoppelt **nicht** aufgrund des
  aggregierten Satzvolumens. Set Volume (kg) wird lediglich
  mit Session Volume (kg) auf Konsistenz geprüft.
- Die CSV enthält **Satzdauern**, teilweise über die Notes-Angabe
  "timed set: ... s", aber keine tatsächlichen Satzanfangszeiten.
  Daher schätzt der FIT-Writer die zeitliche Position jedes Satzes.
  Ein zeitbasierter Satz von 300 Sekunden wird nicht als 300
  Kraftwiederholungen gezählt.
- Die CSV-Satzwerte werden **nicht** als persönliche Speediance-API-
  Messungen ausgegeben. Der Import bleibt eine vom Nutzer
  ausgewählte lokale Quelle, erkennbar als gm_manager_history_csv.
- Keine Rohdaten, Trainingsnamen, CSV-Pfade, Gewichte, IDs oder
  Zugangsdaten in die Diagnose-Logs schreiben. Der Import greift
  nicht schreibend auf Garmin Connect oder Speediance zu.

**Grenzen:** Es findet noch keine Übernahme einzelner Satz-Wattwerte,
Links-/Rechts-Leistungsverläufe oder per-Satz-Maximalpulswerte statt.
Auch die originale CSV enthält keine exakten Zeitpunkte für die
Satzanfänge. Die tatsächlich sichtbare Garmin-Connect-Darstellung
muss weiterhin an einem echten manuellen Import überprüft werden.

## 0.1.29-beta – Kein falscher Erfolg bei fehlenden Speediance-Sätzen

Der direkte Vergleich einer originalen Garmin-FIT und einer als
zusammengeführt angezeigten FIT zeigte eine entscheidende Fehlfunktion:
**Beide Dateien enthielten genau eine Garmin-SET-Nachricht und keine
neuen Speediance-Sätze.** Nur die FIT-Dateiidentität war verändert.

Die Ursache liegt in einem seit 0.1.23 tolerierten Garmin-only-Fallback.
Ab jetzt gilt für **Mit Garmin abgleichen…**:

- Liefert Speediance keine abgeschlossenen Sätze und wurde keine bestätigte
  GM-Manager-History-CSV (oder GM-Manager-JSON) ausgewählt, **bricht der
  Merge mit einer verständlichen Fehlermeldung ab, ohne eine FIT-Datei
  zu schreiben**.
- Wird die History-CSV ausgewählt, muss die Zahl der Quellzeilen genau
  der Zahl der erzeugten **und der finalen** FIT-SET-Nachrichten entsprechen.
  Im bestätigten Referenzfall sind das **27 Satzzeilen**. Für den JSON-
  Ersatz gilt entsprechend die Zahl seiner 24 bestätigten Satzvorgaben.
- Die finale FIT wird weiterhin auf FIT-CRC, Nachrichtenstruktur und
  erhaltene Garmin-Nachrichten geprüft. Beim CSV-Import werden zusätzlich
  die Wiederholungen und Gewichte jedes einzelnen Satzes aus der finalen
  FIT dekodiert und mit dem bestätigten Import verglichen. Die
  Gewichtswerte werden nicht aus Satzvolumina verdoppelt (0.1.18).
- Die Diagnose meldet künftig die ausgewählte Satzquelle
  (Cloud, bestätigte JSON-Datei oder History-CSV) und die Anzahl
  übernommener Sätze. Es gibt keine irreführende Erfolgsmeldung
  mehr bei **0** importierten Sätzen.

Für den Anwendungsfall vom 16.11.2026 in der Merge-Maske explizit
**GM-Manager-History-CSV wählen…** und die 27 Zeilen bestätigen,
danach die Original-Garmin-FIT auswählen und exportieren.
Die Warnung über geschätzte Satzanfangszeiten bleibt bestehen.

Diese Prüfungen verhindern erneut unbemerkte Garmin-only-Dateien.
Ein abschließender Importtest der neuen Version mit der echten
Fenix-Aufzeichnung muss noch nachgewiesen werden.

## 0.1.30-beta – Garmin-/Speediance-Zeitversatz aus echtem Training behoben

Der echte Export von Version 0.1.29 meldete trotz erfolgreich ausgewählter
GM-Manager-History-CSV mit **9 Übungen und 27 Satzzeilen** nur `ValueError`.
Ein erneuter Abgleich der originalen Daten zeigt die Ursache:

- Beginn GM Manager / Speediance: **16.11.2026, 15:18:17 MEZ**
- Beginn Original-Garmin-FIT: **16.11.2026, 15:19:52 MEZ**
- Zeitversatz: **−95 Sekunden** (Speediance beginnt früher)

Mit Trainingsbeginn-Priorität **Garmin** war der bisherige
`strength_start_offset = -95`. Der direkte FIT-Writer lehnt negative
Satzstartpositionen ab. Die bisherigen synthetischen Tests verwendeten
nur den umgekehrten Fall und erkannten diesen Fehler nicht.

Ab 0.1.30 werden ausschließlich bei **GM-Manager-History-CSV** bzw.
vom Nutzer bestätigter **GM-Manager-JSON** die *geschätzten*
Satzzeitpunkte auf den Garmin-Aktivitätsbeginn gelegt, wenn Speediance
vor Garmin gestartet wurde. Die originalen Garmin-Record-Zeitstempel,
Herzfrequenz- und Geräteaufzeichnungen bleiben unverändert.
Originale Speediance-Telemetrie wird nicht auf diese Weise verschoben.
Im Diagnoseprotokoll steht für einen betroffenen Export
`estimated_set_timing_aligned_to_garmin=True`; die Erfolgsmeldung
enthält einen deutlichen Hinweis auf diese Anpassung.

Für fehlgeschlagene FIT-Exporte wird ein verständlicher Fehlertext statt
eines nackten `ValueError` angezeigt. Der in 0.1.29 eingeführte
Schutz gegen 0 importierte Sätze sowie die finale Prüfung von Satzanzahl,
Wiederholungen und Gewichten bleiben erhalten.

Die Regressionstests reproduzieren ausdrücklich den negativen
95-Sekunden-Abstand und prüfen die unveränderten Garmin-Sensor-Datensätze.

## 0.1.31-beta – Manuelle Garmin-Übungszuordnung wieder direkt erreichbar

Wenn Speediance bei einem älteren oder gelöschten Custom-Training keine
`finishedReps`-Details mehr liefert, blockierte bisher der Hauptfenster-
Button **Übungen zuordnen…**: Er versuchte vor dem Öffnen des Editors
einen Cloud-Detailabruf und brach bei `100041` ab.

Die **manuelle Zuordnung ist jetzt unabhängig vom Cloud-Abruf**:

- **Übungen zuordnen…** im Hauptfenster öffnet den vorhandenen
  Garmin-Katalogeditor unmittelbar – auch ohne Login, API-Sätze oder
  gespeicherte Übungsnamen. Im Editor können Namen über
  **Übungsname hinzufügen…** lokal angelegt werden.
- **Übungsnamen von Speediance laden…** ist ein eigener, optionaler
  Button. Er ruft die tatsächlichen Namen der markierten Workouts über
  die Speediance-API ab, wenn diese verfügbar sind.
- Im Fenster **Mit Garmin abgleichen…** gibt es ebenfalls
  **Übungen zuordnen…**. Nach dem bestätigten Import einer
  GM-Manager-History-CSV stehen die darin enthaltenen Übungsnamen
  sofort im Editor zur Auswahl. Ist noch keine Quelle verfügbar,
  öffnet er trotzdem, damit Namen manuell angelegt werden können.
- Bestätigte History-CSV-Übungsnamen und Zuordnungen werden nur in den
  bestehenden lokalen Benutzer-Einstellungen gespeichert. Keine
  CSV-Trainingswerte oder Accountkennungen werden dafür protokolliert.
- Die Zuordnungen werden wie bisher beim endgültigen FIT-Export über
  `saved_mappings()` auf die Garmin-FIT-Übungskategorien angewandt.
  Die Gewichtskorrektur von 0.1.18 und alle Garmin-FIT-Messdaten bleiben
  unverändert.

**Abgrenzung:** Eine manuelle Übungszuordnung liefert keine fehlenden
Satzdaten nach. Der direkte Satzabruf aus Speediance bleibt ein
separates Entwicklungsziel.

## 0.1.32-beta – Direkter Speediance-Satzabruf und automatische Sicherung

**Ohne GM Manager und ohne manuelle CSV:** Beim Klick auf
**Trainings laden** werden die jüngsten, noch nicht lokal gesicherten
abgeschlossenen Speediance-Einheiten nun unmittelbar über die bestehenden
authentifizierten, ausschließlich lesenden Speediance-GET-Endpunkte
abgerufen. Erfolgreich geladene **tatsächlich absolvierte** Sätze
werden im bereits vorhandenen, nach Speediance-Konto/Region/Training
getrennten lokalen Cache gespeichert. Die Sicherung ist auf maximal
**3 neue Einheiten pro Laden**, **30 Tage Rückblick** und eine
aktuelle API-Versionsvariante beschränkt, um die inoffizielle Speediance-API
nicht mit Massenzugriffen zu belasten. Ein vorübergehender Fehler einer
Einheit blockiert die Trainingsliste nicht. Bei der späteren FIT-Erstellung
wird der Cache automatisch wiederverwendet.

Zusätzlich unterstützt der direkte API-Client jetzt das nachgewiesene
**Free Lift**-Antwortformat
`freeTraining → actionList[].setList[].summary`. Die tatsächlich
abgeschlossenen Werte (`finishedCount`, `time` und
`summary.weight`) werden in normale Satzdaten umgesetzt. Nicht
absolvierte oder nur geplante Sätze werden nicht exportiert. Das ebenfalls
vorhandene direkte `freeTrainingDetail`-Format wird als zusätzlicher
GET-Fallback erkannt. `summary.weight` ist bereits das angezeigte
Gesamtgewicht der Free-Lift-Aufzeichnung; daraus wird **keine pauschale
Verdopplung** abgeleitet. Die für Custom- und Kurs-Trainings
bestehende modale Gewichtsmessung bleibt unverändert.

**Grenzen:** Vor der ersten erfolgreichen Sicherung gelöschte
Trainingsvorlagen können nicht aus leeren Serverantworten rekonstruiert
werden. Der konkrete Fall vom 16.11.2026 mit Code 100041 bleibt
deshalb ohne historische Kopie der vollendeten Sätze ein
Serverdaten-Problem; die früher erfolgreich importierte CSV bleibt eine
optionale Alt-Daten-Rettung. Die neue Free-Lift-Unterstützung ist
durch synthetische API-Antworten und Regressionstests geprüft,
nicht durch einen Live-Login auf das Nutzerkonto. Es gibt keine
zusätzlichen Logins, keine Drittanbieter-API und keine automatischen
Garmin-Connect-Änderungen.

## 0.1.33-beta – Übungszuordnung an ausgewähltes Training gebunden

**Behobener Fehler aus 0.1.32:** Ein markiertes Training wie
`Your First Training with Gym Monster` zeigte im manuellen
Zuordnungseditor trotzdem die zuvor gespeicherten GMC-Übungen des
16.11.2026. Ursache: Der Hauptfenster-Button
`Übungen zuordnen…` benutzte immer den globalen `observed_names()`-
Pool, auch wenn ein einzelnes Training markiert war.

- **Mit markiertem Training:** Der Editor zeigt ausschließlich die
  tatsächlich absolvierten Übungen aus dem bereits automatisch
  gespeicherten und nach Konto, Region und Training isolierten
  Speediance-Detailcache. Es gibt keine erneute API-Abfrage.
  Fehlt der Cache, öffnet sich der Editor leer mit einem
  verständlichen Hinweis statt mit fremden Übungen. **Übungsname
  hinzufügen…** bleibt möglich.
- **Ohne markiertes Training:** Alle bisher gespeicherten Übungen und
  manuellen Garmin-Zuordnungen sind wie bisher sichtbar und bearbeitbar.
- **Übungsnamen von Speediance laden…:** Der separate Button kann
  neue Namen bei Bedarf online für die markierte Einheit abrufen.
- **Im Garmin-Abgleich:** Der Editor verwendet entweder die
  bestätigten Übungsnamen einer History-CSV oder die gespeicherten
  Speediance-Details des ausgewählten Trainings, niemals die global
  gespeicherten Übungen einer anderen Einheit.
- Bereits gespeicherte Garmin-Kategorien/-IDs und
  Gewichtsmultiplikatoren werden **nicht gelöscht oder geändert**.
  Free-Lift-Unterstützung, automatische Sicherung und der
  Garmin-FIT-Merge aus 0.1.32 bleiben unangetastet.

## 0.1.34-beta – Garmin-Merge mit direkt von Speediance gesicherten Sätzen

**Realer Test vom 18.11.2026:** `Your First Training with Gym Monster`
(13.11.) wurde erfolgreich über den kontobezogenen Cache geladen
(**1 Übung, 4 Sätze, 362 echte Herzfrequenzwerte**), danach meldete der
Garmin-Abgleich lediglich `GarminOverlayError`. Die Datenbeschaffung
funktionierte also; die Ursache lag danach auf dem FIT-Merge-Pfad.
Der genaue Fehler war im Log nicht unterscheidbar.

Zwei konkrete Fehlerbilder sind deshalb behoben:

- Der Garmin-Exportdialog fängt **`GarminOverlayError` (Unterklasse
  `ValueError`) und `GarminFitError`** jetzt vor dem generischen
  ValueError ab. Der konkrete, eigens formulierte Fehlertext bleibt
  in der Oberfläche erhalten; fremde/unerwartete Fehlermeldungen
  bleiben aus Datenschutzgründen weiterhin anonymisiert.
- **Auch echte direkt geladene Speediance-Satzdaten enthalten bislang
  keine absoluten SET-Anfangszeiten**, sondern nur gemessene
  Wiederholungen, Gewichte und Satzdauern. Begann die Garmin-Uhr
  später als Speediance, konnte der geschätzte `strength_start_offset`
  negativ werden, was der FIT-Writer zurückwies. Diese geschätzten
  **SET-Zeitpunkte** werden nun bei negativem Offset wie bereits bei
  der bestätigten History-CSV auf den Garmin-Aktivitätsbeginn
  ausgerichtet. **Echte Garmin- und Speediance-Herzfrequenz-
  Messzeitpunkte bleiben absolut unverändert.**
- Das Diagnoseprotokoll meldet ausschließlich datenschutzverträgliche
  relative Werte: `Garmin merge set timeline: raw_offset_sec=...`
  und `chosen_offset_sec=...`, außerdem die Eingangsquelle und
  Zahl übernommener Sätze. Keine Token, Account-IDs oder absoluten
  Trainingszeiten.

Neue Regressionen prüfen direkt geladene **4 Sätze**, negativen
95-Sekunden-Startversatz, unveränderte Garmin-Record- und
Geräte-Nachrichten sowie aussagekräftige Fehlermeldungen.

**Wichtig:** Der konkrete `GarminOverlayError` aus dem Log von
09:59 Uhr ist nicht allein anhand seines Klassennamens eindeutig
zuordenbar. Diese Version behebt den belegten Meldungsverlust und
einen plausiblen Satzzeitfehler; ein erneuter Live-Test ist nötig.
Es gibt weiterhin keine Behauptung, Garmin Connect würde alle
Training-Effect-Metriken aus neuen Importen wiederherstellen.

## 0.1.35-beta – Training Effect in Garmin Connect nach FIT-Reimport

**Mit einem echten Nutzerimport am 18.11.2026 bestätigt:** Die originalen
FIT-Sitzungswerte für Training Effect waren bereits in der von
0.1.34-beta erzeugten MERGED-Datei erhalten, wurden in Garmin Connect
aber nicht angezeigt. Im **separaten erfolgreichen Testimport** wurde
ausschließlich die ursprüngliche, aus der Garmin-Original-FIT gelesene
Hersteller- und Produktkennung in `file_id` wiederhergestellt
(`Garmin/4536` statt `Development/0`). Danach zeigte Garmin Connect
wieder **0,3 aerob / 0,0 anaerob / Belastungswert 4** zusammen mit
**4 direkt von Speediance geladenen Sätzen**, **111/123 bpm** und dem
Trainingsvolumen. Die Prüfsumme wurde für die beiden geänderten Felder
neu berechnet. Bei anderen originalen Garmin-Geräten wird **deren
tatsächlich aufgezeichnete** Kennung übernommen, nicht die hier
getestete konkrete Produktnummer fest eingebaut.

- Das Garmin-basierte FIT-Overlay kopiert jetzt die unveränderten
  `file_id.manufacturer`- und `file_id.product`-Werte der originalen
  Garmin-Quelle statt sie als `Development/0` zu überschreiben.
  Ungültige Quellkennungen führen zu einer Fehlermeldung, nicht zu
  erfundenen Geräteangaben.
- Die MERGED-FIT erhält weiterhin eine **neue Dateiidentität**
  (serielle Ableitungskennung und Erstellungszeit), ohne die ursprüngliche
  Aktivitätszeit zu verändern. Garmin Connect kann dennoch Aktivitäten
  mit gleicher Uhrzeit als Duplikate erkennen; der Import ersetzt
  **niemals automatisch** eine vorhandene Aktivität.
- Die vorhandenen Garmin-`device_info`- und Spezialnachrichten,
  SESSION-Felder für Training Effect und alle Original-HF-Daten
  werden wie zuvor beibehalten. Regressionstests prüfen zusätzlich
  die ursprünglichen SESSION-Felder 24/137 und das unveränderte
  Durchreichen eventuell vorhandener `MONITORING`-Nachrichten.
  Repetitionen und Sätze werden weiterhin wie in 0.1.34 übernommen.

**Intensitätsminuten sind ein getrenntes Garmin-Connect-Thema:**
Die vom Nutzer angezeigten **3 moderaten + 1 hohe (doppelt gewertet)
= 5 Minuten** wurden trotz identischer Garmin-Gerätekennung im
Testimport nicht angezeigt. Die bereitgestellten Original- und
MERGED-FIT-Dateien vom 13.11. enthalten beide **keine
`MONITORING`-Nachrichten (FIT-Nachricht 55)**. Das ist kein Beleg,
dass die 5 Minuten vollständig über diese Nachricht kodiert sein
müssten; die Garmin-Connect-Geräte-/Gesundheitsberechnung kann separat
erfolgen. **Keine Intensitätsminuten werden erfunden oder künstlich
in die FIT geschrieben.** Die originale Garmin-Aktivität bleibt
unverändert.

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
