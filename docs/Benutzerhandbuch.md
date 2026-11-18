# Speediance FIT Exporter – Benutzerhandbuch

**Version:** 0.1.35-rc.1 (Release Candidate 1)  
**Plattform:** Windows 10/11  
**Sprachen der Anwendung:** Deutsch, Englisch  
**Projektstatus:** Unabhängiges Community-Tool; weder von Speediance noch von Garmin entwickelt oder unterstützt

> **Wichtig:** Diese Anwendung ändert niemals automatisch deine Daten in Garmin Connect. Sie erzeugt lokal eine neue FIT-Datei. Diese muss bei Bedarf manuell importiert werden. Bereits vorhandene Aktivitäten werden **nicht** überschrieben. Intensitätsminuten werden beim FIT-Reimport nach unseren Tests **nicht zusätzlich dem Garmin-Wochenkonto gutgeschrieben**.

## 1. Wofür ist das Programm?

Der Speediance FIT Exporter übernimmt *abgeschlossene* Übungen, Sätze, Wiederholungen, Gewichte und soweit vorhanden Herzfrequenzdaten aus deinem Speediance-Konto. Für den empfohlenen Ablauf lädt er zusätzlich deine originale Garmin-Aktivität über die **Garmin Personal API** und erstellt daraus lokal eine neue FIT-Datei. Dabei bleiben die originalen Garmin-Geräte- und Sensordaten sowie die vorhandenen Training-Effect-Werte erhalten; die tatsächlich absolvierten Speediance-Sätze ersetzen die bisherigen Krafttrainingssätze.

Die Anwendung funktioniert auch ohne eine kostenpflichtige GM-Manager-Schnittstelle, ohne einen CSV-Export und ohne eine zuvor manuell heruntergeladene Garmin-FIT-Datei.

**Nicht enthalten:** automatisches Hochladen in Garmin Connect, Bearbeiten bestehender Garmin-Aktivitäten, Garantie für alle Speediance-Trainingstypen oder Garantie für Garmin-Intensitätsminuten nach einem Reimport.

## 2. Installation und erster Start

1. Lade das RC-Paket `SpeedianceFITExporter-Windows-Setup-0.1.35-rc.1` herunter. Bei GitHub liegt es unter **Actions → Windows installer → erfolgreicher RC-Build → Artifacts**. Bei privater Weitergabe erhältst du die ZIP-Datei vom Anbieter.
2. Entpacke die ZIP-Datei. Darin liegt `SpeedianceFITExporter-Setup.exe` sowie dieses Handbuch.
3. Starte die Setup-Datei und folge dem Installationsassistenten. Die Installation erfolgt für den angemeldeten Windows-Benutzer, ohne Administratorrechte.
4. Starte das Programm über **Start → Speediance FIT Exporter**.
5. Eine nicht signierte Setup- oder EXE-Datei kann eine Windows-SmartScreen-Warnung auslösen. Führe nur eine Datei aus einer **vertrauenswürdigen Quelle** aus; deaktiviere dafür keine systemweiten Sicherheitsfunktionen.

**Für die Bedienung ist keine Python-Installation erforderlich.** Für Entwicklung und eigene Builds siehe `docs/Entwicklung.md`.

## 3. Speediance anmelden und Trainings laden

1. Gib die E-Mail-Adresse und das Passwort deines **eigenen** Speediance-Kontos ein und wähle die passende Region (**EU** oder **Global**).
2. Der Anmeldetyp `bike` ist die Voreinstellung, falls du kein Speediance Bike besitzt. Benutzt du ein Bike, kann `nano` sinnvoller sein, sofern du keinen Gym Nano besitzt. `phone` kann die Speediance-Smartphone-App abmelden. **Jeder Sitzungstyp kann mit einem real vorhandenen Gerät desselben Typs kollidieren.**
3. Klicke auf **Anmelden**. Falls gewünscht, aktiviere **Anmeldedaten auf diesem PC speichern**. Zugangsdaten werden dann im Windows-Anmeldeinformationsmanager gespeichert; ansonsten werden sie nicht dauerhaft gespeichert.
4. Stelle den gewünschten Zeitraum im Format `JJJJ-MM-TT` ein und klicke auf **Trainings laden**.
5. Wähle die absolvierte Trainingseinheit in der Liste. Das Programm zeigt Datum, Namen, Dauer und Kalorien.

**Automatische lokale Sicherung:** Beim Laden versucht das Programm, Details von bis zu **drei** noch nicht gesicherten Trainingseinheiten der letzten **30 Tage** abzurufen. Erfolgreich geladene, tatsächlich absolvierte Sätze werden lokal und nach Speediance-Konto/Region/Training getrennt gespeichert. Das verhindert manche spätere Datenverluste, beispielsweise nach dem Löschen einer Trainingsvorlage. Fehlschläge werden nicht durch erfundene Satzdaten ersetzt.

## 4. Übungen zuordnen

Garmin und Speediance verwenden unterschiedliche Bezeichnungen für Kraftübungen. So gehst du bei unbekannten Übungen vor:

1. Markiere ein Training und klicke **Übungen zuordnen…**. Der Editor zeigt **nur die bereits lokal gesicherten Übungen dieser Auswahl**.
2. Wähle links eine Speediance-Übung, suche rechts nach der passenden Garmin-Übung und klicke **Zuordnen**.
3. Wiederhole die Zuordnung für die weiteren Übungen. Gespeicherte Zuordnungen gelten auch für spätere Trainings mit denselben Übungsnamen.
4. Ist links keine Übung sichtbar, fehlen möglicherweise noch lokale Satzdetails. Über **Übungsnamen von Speediance laden…** kannst du sie gezielt online abrufen. Fehlen die Details weiterhin, kannst du **Übungsname hinzufügen…** nutzen; dies erzeugt **keine absolvierten Sätze**.

**Ohne markiertes Training** zeigt **Übungen zuordnen…** deine bisher global gespeicherten Übungsnamen. Zuordnungen werden dadurch nicht gelöscht.

**Gewichte:** Die regulär von Speediance als Gesamtgewicht gelieferten Messwerte werden nicht automatisch verdoppelt. Für ausdrücklich nur pro Griff gemeldete Gewichte kann die Zuordnung einen manuellen Faktor besitzen. Bei Unsicherheit erst den tatsächlich protokollierten Wert prüfen und keinen Faktor auf Verdacht setzen.

## 5. Empfohlen: Mit der originalen Garmin-Aktivität zusammenführen

Dieser Weg erhält die ursprünglichen Garmin-Messdaten am zuverlässigsten:

1. Zeichne das Training zusätzlich auf deiner Garmin-Uhr als Krafttraining auf und synchronisiere die Originalaktivität regulär mit Garmin Connect.
2. Starte den Exporter, melde dich bei Speediance an und klicke **Trainings laden**.
3. Markiere **genau ein** passendes Speediance-Training und klicke **Mit Garmin abgleichen…**.
4. Wähle unter **Garmin-FIT-Quelle** die Option **Garmin Personal API** (nicht die Option „Lokale Garmin-FIT-Datei“).
5. Über **Schlüssel erstellen** öffnest du die Garmin-Seite für einen persönlichen API-Schlüssel: <https://connect.garmin.com/app/settings/personalApiToken>. Erstelle ihn für dein eigenes Konto. Füge ihn in das dafür vorgesehene Feld ein. Optional kannst du den Schlüssel geschützt im Windows-Anmeldeinformationsmanager ablegen.
6. Lass die **Datenprioritäten** für Trainingsbeginn, Trainingsdauer, Herzfrequenz und Kalorien zunächst auf **Garmin**. Die echten absolvierten Sätze kommen weiterhin von Speediance.
7. Klicke **Garmin-Aktivitäten suchen / FIT prüfen**. Wähle die zeitlich passende Garmin-Aktivität aus der Trefferliste. Das Programm prüft Beginn und Dauer; der Kalendertag allein reicht nicht als Nachweis.
8. Klicke **Zusammengeführte FIT speichern…** und wähle einen Speicherort. Der Exporter lädt die Garmin-FIT über die schreibgeschützte Personal API, ergänzt lokal die Speediance-Sätze und speichert eine **neue** Datei.

**Wichtig:** Wenn keine tatsächlich abgeschlossenen Speediance-Sätze abrufbar sind, wird die Zusammenführung abgebrochen. Der Exporter erzeugt dann keine scheinbar erfolgreiche Garmin-only-FIT.

### Alternative: Originale Garmin-FIT lokal wählen

Falls die Garmin Personal API nicht verfügbar ist, kannst du im selben Dialog **Lokale Garmin-FIT-Datei** wählen und eine zuvor aus Garmin Connect exportierte, **unveränderte Garmin-Originaldatei** angeben. Der übrige Ablauf bleibt gleich. Das ist ein Ausweichweg, keine Voraussetzung für den normalen Export.

### Alternative: Eigenständige Speediance-FIT

Mit **Ausgewählte als .fit exportieren** kannst du eine Speediance-Aktivität ohne Garmin-Original erzeugen. Diese Datei enthält **keine ursprünglich von der Garmin-Uhr berechneten Training-Effect-Werte oder Garmin-Sensormetadaten**. Für die kombinierte Garmin-Auswertung nutze die Zusammenführung.

### Optionale historische Datenimporte

Im Garmin-Abgleich existieren noch optionale GM-Manager-JSON-/History-CSV-Importfunktionen für Sonderfälle. Sie sind **nicht nötig** für den regulären Ablauf. Ein JSON-Plan ist kein Nachweis tatsächlich durchgeführter Sätze; das Programm verlangt deshalb eine ausdrückliche Bestätigung. Eine kostenpflichtige GM-Manager-API wird nicht benötigt.

## 6. Neue FIT in Garmin Connect importieren

1. Melde dich auf <https://connect.garmin.com/> an.
2. Öffne **Daten importieren** (auf Garmin Connect Web üblicherweise über das Cloud-Symbol) und wähle die erzeugte Datei `JJJJ-MM-TT_Speediance_Garmin_MERGED.fit`.
3. Prüfe Sätze, Übungen, Wiederholungen, Gewichte, Herzfrequenz und **Training Effect**.
4. Die ursprüngliche, von der Uhr synchronisierte Garmin-Aktivität wird **nicht automatisch ersetzt**. Garmin Connect kann die neue Datei als zusätzliche Aktivität importieren oder aufgrund identischer Zeiten als Duplikat ablehnen.

**Nie die ursprüngliche Garmin-Aktivität löschen, nur um einen Testimport zu erzwingen.** Behalte auch die Original-FIT als Sicherheitskopie. Wenn du einen doppelten Import entfernen möchtest, stelle sicher, dass du die **richtige zusätzliche Aktivität** erwischt hast.

## 7. Welche Daten bleiben erhalten?

Beim Zusammenführen dient die originale Garmin-FIT als Grundlage. Ursprüngliche Geräteinformationen, proprietäre Nachrichten und aufgezeichnete Garmin-Herzfrequenzdatensätze werden bewahrt. Die vom Garmin-Gerät aufgezeichneten **Training-Effect-Werte** bleiben in der FIT. Für den RC wird auch die echte Garmin-Hersteller-/Produktkennung bewahrt; ein echter Garmin-Connect-Test vom 13.11.2026 bestätigte daraufhin **0,3 aerob, 0,0 anaerob und Belastungswert 4** mit **vier Speediance-Sätzen**.

Die neue Datei erhält eine eigene Dateiidentität; sie ist **kein unverändert originales Garmin-Gerätefile**. Gewählte Datenprioritäten können bestimmte Sitzungsfelder bewusst ändern.

**Wichtige Grenzen:**
- **Intensitätsminuten:** Der Garmin-Connect-Reimport hat im Test **keine neuen Intensitätsminuten dem Wochenkonto gutgeschrieben**, auch nachdem Training Effect wieder angezeigt wurde. Das ist kein reines Anzeigeproblem innerhalb des Krafttrainings. Synchronisiere die ursprüngliche Garmin-Uhr weiterhin regulär; unser Exporter verspricht keine Anrechnung beim Import.
- **Satz- und Pausenzeiten:** Speediance liefert echte Wiederholungen, Gewichte und soweit vorhanden Satzdauern, aber nicht für jeden Satz einen verifizierten absoluten Beginn. Satzanfänge und Garmin-„Belastungszeit“ können daher geschätzt bzw. von der Originalaufzeichnung abweichend sein.
- **Verwaiste/deaktivierte Trainingsdetails:** Wenn Speediance zwar einen Kalendereintrag, aber keine absolvierten Sätze mehr liefert (z. B. API-Code `100041`), kann der Exporter sie nicht zuverlässig wiederherstellen. Ein vorher erfolgreich gesicherter lokaler Cache kann helfen.
- **Importstatistiken:** Garmin Connect entscheidet nach seinen eigenen Regeln, ob eine importierte Aktivität zu übergreifenden Gesundheitsstatistiken beiträgt.

## 8. Datenschutz, lokale Speicherung und Deinstallation

- Anmeldung und Trainingsabruf laufen zwischen deiner Windows-App und **Speediance**; Aktivitätssuche und Garmin-FIT-Download laufen zwischen deiner App und **Garmin**. Das sind externe Dienste.
- Der eigentliche FIT-Merge und die Zuordnung erfolgen **lokal auf deinem PC**. Das Programm lädt **keine** Daten selbsttätig in Garmin Connect hoch.
- Zugangsdaten und der optionale Garmin-API-Schlüssel werden nur auf ausdrücklichen Wunsch im **Windows-Anmeldeinformationsmanager** gespeichert. Ein kurzzeitig genutztes Sitzungstoken bleibt nicht dauerhaft in den Programmeinstellungen.
- Persönliche Trainingsergebnisse, Übungsnamen, lokale FIT-Dateien sowie Einstellungen sind sensible Informationen; gib sie nur mit Einwilligung weiter.
- Lokale Einstellungen, Zuordnungen, Diagnoseprotokoll und ein Cache abgeschlossener Sätze liegen unter `%LOCALAPPDATA%\SpeedianceFITExporter\`. Der lokale Cache enthält tatsächlich absolvierte Sätze und ggf. Herzfrequenzdaten.
- **Diagnoseprotokoll speichern…** erzeugt eine Datei zur Fehleranalyse. Der Logger versucht Kennungen/Geheimnisse zu vermeiden; **prüfe den Inhalt vor jeder Weitergabe selbst**.
- **Deinstallation:** Über das Startmenü **Deinstallieren** wird das Programm entfernt. Lokale Einstellungen, FIT-Exporte, Cache und ggf. Windows-Anmeldeinformationen werden **nicht pauschal mitgelöscht**. Für eine vollständige persönliche Bereinigung zusätzlich den genannten Datenordner und die entsprechenden Windows-Anmeldeinformationen prüfen.

## 9. Fehlerbehebung

| Beobachtung | Was tun? |
| --- | --- |
| Anmeldung schlägt fehl | E-Mail, Passwort, Region (EU/Global) und gewählten Sitzungstyp kontrollieren. Die API ist inoffiziell und kann sich ändern. |
| Speediance-App wurde abgemeldet | Vermutlich gleicher Sitzungstyp. `phone` vermeiden, falls die Smartphone-App aktiv bleiben soll. |
| Training erscheint, aber Übungen fehlen | Trainingsdaten sind teilweise nicht mehr über Speediance verfügbar. Andere absolvierte Einheit prüfen; es wird nichts aus Vorlagen erfunden. |
| Bei **Übungen zuordnen…** ist die Liste leer | Das ausgewählte Training hat noch keine gesicherten absolvierten Satzdetails. Optional **Übungsnamen von Speediance laden…** verwenden. |
| Garmin-Aktivität nicht gefunden | Beide Aktivitäten auf passende Anfangszeit/Dauer prüfen; die Garmin-Uhr muss die Originalaufzeichnung bereits synchronisiert haben. |
| Garmin-API-Schlüssel funktioniert nicht | Persönlichen Schlüssel für das richtige Konto prüfen, ggf. bei Garmin neu erzeugen. |
| Nach Import fehlt Training Effect | Prüfen, ob tatsächlich eine **zusammengeführte FIT** auf Basis des Garmin-Originals verwendet wurde und ob der Exporter **0.1.35-rc.1 oder neuer** ist. |
| Nach Import fehlen Intensitätsminuten | Bekannte Garmin-Importeinschränkung; reguläre Uhrensynchronisierung bleibt relevant. Es ist **kein nachgewiesener FIT-Writer-Defekt**. |
| Garmin Connect meldet Duplikat | Die alte Aktivität nicht unbedacht löschen. Der FIT-Import ersetzt keine vorhandene Aktivität. |
| Windows warnt vor unbekanntem Herausgeber | Der Installer ist nicht codesigniert. Herkunft prüfen, nicht pauschal die Windows-Sicherheit deaktivieren. |

## 10. Hilfe und Fehler melden

Notiere **Programmversion**, die ausgeführte Funktion, die genaue **Fehlermeldung** und ob der Fehler vor oder nach dem Garmin-Abgleich auftrat. Nutze **Diagnose anzeigen…** oder **Diagnoseprotokoll speichern…** und entferne vor einer Weitergabe persönliche Informationen. **Keine Passwörter, API-Schlüssel, Tokens oder fremden FIT-Dateien veröffentlichen.**

Das Projekt ist kein offizielles Produkt von Speediance oder Garmin. Ein geschützter GitHub-Zugang ist für den Betrieb des bereits installierten Programms nicht erforderlich; lediglich der Weg zum Herunterladen des privaten RC-Installers hängt vom Verteiler ab.
