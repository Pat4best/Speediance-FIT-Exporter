# Drittquellen, Marken und Lizenzprüfung

[English version](../en/third-party.md) · [Dokumentationsübersicht](README.md)

**Stand:** 0.1.36-beta · **Vorläufige Bestandsaufnahme, keine Rechtsberatung**

Der Speediance FIT Exporter ist unabhängige Software. Der Quellcode besteht überwiegend aus Python-Standardbibliothek-basierten Komponenten; zur Erstellung des Windows-Installers werden PyInstaller und NSIS verwendet. Externe Marken, Protokollprofile, Server-APIs und deren Nutzungsrechte sind davon zu unterscheiden.

## Garmin FIT SDK / Garmin-FIT-Übungskatalog

Der integrierte Garmin-Übungskatalog mit über 1.800 Kategorien-/Übungsnamen-Einträgen wurde während der Beta-Entwicklung anhand der öffentlich zugänglichen Garmin-FIT-Java-SDK-Enumwerte erstellt. Die vollständigen Daten liegen in `app/garmin_catalog_part1.py` bis `app/garmin_catalog_part5.py` und `app/garmin_catalog.py`. Es wird kein Garmin Java SDK zur Laufzeit installiert.

**Achtung bei öffentlicher Quellcodeveröffentlichung:** Die offizielle [Garmin FIT SDK License](https://github.com/garmin/fit-java-sdk/blob/main/LICENSE.txt) ist **keine normale MIT-/BSD-/Apache-Open-Source-Lizenz**. Sie enthält Beschränkungen für Veröffentlichung/Weitergabe der lizenzierten Technologie. Dass einzelne Enum-Werte, Namen oder Protokoll-Feldnummern technisch standardisiert sind, bedeutet noch **nicht**, dass wir die zusammengetragene komplette SDK-Datensammlung ohne weitere Prüfung beliebig unter einer eigenen Open-Source-Lizenz weiterlizenzieren dürfen. Das ist vor einer Freigabe zu klären (ggf. Rechtsberatung, Erlaubnis oder Neukonzeption des Katalogs mit einer nachweisbar zulässigen Quelle).

**Keine eigene Repository-Lizenz darf Rechte an Garmin-Materialien behaupten**, die nicht zustehen. Hinweise und Lizenzen aus offiziellen Quellen nicht entfernen.

- Quelle: <https://github.com/garmin/fit-java-sdk>
- FIT-Dokumentation: <https://developer.garmin.com/fit/>
- FIT-SDK-Lizenz: <https://github.com/garmin/fit-java-sdk/blob/main/LICENSE.txt>

## Garmin Connect Personal API

Der Exporter verwendet die [Garmin Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/) zum lesenden Abruf der eigenen ursprünglichen Garmin-Aktivität. **Jeder Endnutzer** muss selbst einen persönlichen Schlüssel erzeugen; es liegt kein gemeinsamer Entwickler-Schlüssel im Repository. Die API und ihre Bedingungen sind für persönlichen Zugang zu den **eigenen Daten** gedacht, nicht für einen kommerziellen Mehrbenutzer-Service.

- Offizielle Dokumentation / [FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq)
- Schlüsselerstellung: <https://connect.garmin.com/app/settings/personalApiToken>
- Keine automatische Schreibfunktion nach Garmin Connect; der Nutzer importiert die neue FIT manuell.
- Eine freie Quellcode-Lizenz wäre **keine** Erlaubnis, fremde Garmin-Zugangsschlüssel gemeinsam zu nutzen oder Garmin-API-Bedingungen zu umgehen.

## Speediance-Cloud-Schnittstelle

Der Exporter spricht die **inoffizielle Speediance-Schnittstelle** mit dem vom Nutzer eingegebenen Konto an. Speediance hat keine Freigabe oder Schnittstellen-Stabilitätszusage für dieses Projekt erteilt.

**Rechtlicher Prüfpunkt:** Regionale Speediance-Nutzungsbedingungen enthalten zum Teil Beschränkungen für Reverse Engineering und automatisierte Auswertung. Welche konkreten Bedingungen für die Cloud-App und Nutzungsregion gelten und ob die Veröffentlichung/Verbreitung eines solchen Tools zulässig ist, muss vor einer öffentlichen Freigabe geklärt werden. Bedingungen für reine Webshops dürfen nicht automatisch als identische Bedingungen der Geräte-Cloud ausgegeben werden.

Hinweis: Der Programmname beschreibt nur die Datenquelle; Speediance darf nicht als Hersteller/Unterstützer des Tools dargestellt werden.

## Build-Abhängigkeiten

- **Python:** Standardbibliothek zur Laufzeit. Keine weiteren Pakete zur Laufzeit erforderlich.
- **PyInstaller:** Wird ausschließlich zur Windows-Bündelung benutzt. Dessen eigene Lizenz-/Distributionstexte und ggf. mitgebündelte Komponenten sind bei Verteilung der EXE zu berücksichtigen. Quelle: <https://pyinstaller.org/>
- **NSIS:** Installer-Werkzeug, siehe <https://nsis.sourceforge.io/License>. Die Verteilung des fertigen Installers ist gesondert von den Rechten an Quelltext und SDK-Daten zu bewerten.

## Markenhinweis und Haftung

„Speediance“, „Garmin“, „Garmin Connect“, „Gym Monster“ und zugehörige Marken sind Eigentum ihrer jeweiligen Inhaber. Kein Sponsoring, keine Zertifizierung, keine offizielle Partnerschaft. Keine Logos/Markenassets als eigenes Markenlogo verwenden. Für Veröffentlichung, Download-Seiten und README klar die unabhängige Herkunft kennzeichnen.

**Status:** Diese Datei ist **keine Rechtefreigabe** und ersetzt keine rechtliche Prüfung. Bis zur Klärung der FIT-Katalog-Rechte, Speediance-Bedingungen und der Repository-Historie bleibt die Verteilung **privat**.

