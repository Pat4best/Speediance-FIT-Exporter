# Bekannte Einschränkungen – 0.1.35-rc.1

Der **Release Candidate 1** ist funktionsstabilisiert. Die folgenden Punkte sind dokumentierte Einschränkungen, **keine stillschweigend versprochenen Funktionen**.

## Intensitätsminuten werden beim Garmin-Import nicht neu gutgeschrieben

Eine separat importierte MERGED-FIT vom 13.11.2026 enthielt die vollständige ursprüngliche Garmin-Herzfrequenz und den wiederhergestellten **Training Effect (0,3 aerob / 0,0 anaerob / Belastungswert 4)**. Garmin Connect zeigte für die importierte Aktivität dennoch keine Intensitätsminuten; eine zusätzliche Gutschrift in der Wochenstatistik wurde im Test nicht festgestellt.

- Intensitätsminuten hängen von Garmins eigenständiger Erfassung und Kontostatistik ab. Beim Löschen einer importierten Aktivität kann eine bereits durch die Uhr erfasste Wochenstatistik unverändert bleiben.
- Weder die originale noch die MERGED-FIT des getesteten Trainings enthielt FIT-`MONITORING`-Nachrichten vom Typ 55. Daraus lässt sich **keine** allgemeine Garantie ableiten, Intensitätsminuten könnten mit beliebigen zusätzlichen FIT-Nachrichten importiert werden.
- Der Exporter generiert **keine erfundenen Intensitätsminuten** und benutzt keine inoffiziellen Schreib-Endpunkte für Garmin Connect.
- Für die Gesundheitserfassung die originale Garmin-Uhr wie gewohnt mit Garmin Connect synchronisieren.

## Satzzeitpunkte, Belastungszeit, Wiederholungen

Speediance liefert tatsächlich ausgeführte Wiederholungen, Gewichte und manchmal Satzdauern, aber nicht für jeden Satz einen verifizierten absoluten Beginn. Der FIT-Writer verteilt diese Sätze mit geschätzten Anfangszeiten; Pausen und „Belastungszeit“ können von der Garmin-Uhr abweichen. Bei negativem Startversatz zur Garmin-Uhr wird **nur der geschätzte Satzbeginn**, nicht der tatsächlich gemessene Garmin-Herzfrequenzverlauf, angepasst.

Die Zuordnung einer Bewegung zu einer Garmin-FIT-Übung kann bei unbekannten oder abweichend benannten Übungen manuell nötig sein. Die Zuordnungen bleiben lokal gespeichert. Ein `completion_method` für zeitbasierte Übungen darf keine künstlich hohen Kraft-Wiederholungszahlen erzeugen.

## Speediance liefert Kalenderdaten ohne vollständige Sätze

Eine abgeschlossene Aktivität kann in der Speediance-Historie stehen, obwohl die bekannten API-Endpunkte keine Satzdetails mehr liefern (Beispiel: API-Code `100041` nach Löschung einer benutzerdefinierten Trainingsvorlage).

- Ein erfolgreicher **lokaler Cache** kann die zuvor von Speediance tatsächlich gelieferten Satzdaten schützen. Der automatische Abruf ist auf bis zu drei noch nicht gesicherte aktuelle Trainingseinheiten je Aufruf beschränkt.
- Sind keine verifizierten absolvierten Sätze vorhanden, wird der eigentliche Merge verweigert.
- Keine Wiederherstellung aus Vorlagen, kein Erraten von Wiederholungen oder Gewichten und keine kostenpflichtige GM-Manager-Schnittstelle als Voraussetzung.

## Garmin-Original und Duplikate

Der Exporter erzeugt eine eigene Dateiidentität für die neue FIT. Garmin Connect kann eine weitere Aktivität importieren, aber auch identische Zeitbereiche als Duplikate ablehnen. **Eine vorhandene Garmin-Aktivität wird nicht automatisch aktualisiert.** Die originalen Trainingsdaten auf dem Gerät und in Garmin Connect bleiben beim Merge unangetastet.

Die originalen Garmin-Hersteller-/Produktwerte werden aus der authentischen Garmin-FIT übernommen, statt die Datei als fiktives Entwicklungsgerät zu markieren. Dadurch erschienen die erhaltenen Training-Effect-Metriken beim tatsächlichen Garmin-Connect-Import wieder. Die Garmin-Connect-Erfahrung kann je nach Firmware, Datei und Kontoeinstellungen abweichen.

## Nicht signierter Installer und Drittanbieter-APIs

- Der Windows-Installer ist **nicht codesigniert**; SmartScreen kann warnen. Nur aus geprüfter Quelle installieren.
- Die Speediance-Cloud-Schnittstelle ist **inoffiziell**. Sie kann sich ändern oder je nach Region/Trainingsart anders antworten.
- Die Garmin Personal API ist nutzerspezifisch. Nutzer müssen einen **eigenen** Schlüssel erzeugen. Der Exporter enthält keinen gemeinsamen Schlüssel, überträgt ihn nicht an den Entwickler und kann keine dauerhafte API-Verfügbarkeit garantieren.
- Eine Anmeldung unter einem Speediance-Sitzungstyp kann andere Geräte desselben Typs oder die Smartphone-App abmelden. `phone` ist deshalb nicht die Standardoption.

## Datenschutz und Veröffentlichung

Lokale Caches können Trainings- und Gesundheitsdaten enthalten. Das Diagnoseprotokoll ist auf technische Metadaten beschränkt, muss vor dem Teilen aber trotzdem überprüft werden. API-Schlüssel, Passwörter, Tokens und Nutzer-FITs gehören **niemals** in öffentliche GitHub-Issues oder Artefakte.

Für öffentliches Open-Source-Hosting siehe [Veröffentlichungscheckliste](Veroeffentlichung_Checkliste.md): Drittanbieter-Lizenz, Rechte an Garmin-Übungskatalogdaten, API-Bedingungen und Git-Historie müssen vorab geklärt werden.
