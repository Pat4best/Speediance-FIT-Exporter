# Checkliste: Öffentliches GitHub-Repository

**Projekt:** Speediance FIT Exporter · **Aktueller Status: nicht zur Veröffentlichung freigegeben**  
**Ziel:** zunächst sicher privat testen, dann nach Rechte-/Sicherheitsprüfung ggf. offen zur gemeinsamen Weiterentwicklung veröffentlichen.

Dies ist eine **technische und organisatorische Vorprüfung, keine Rechtsberatung**. Gerade bei der Schnittstelle eines Drittherstellers, Marken und FIT-SDK-Daten kann eine rechtliche Fachprüfung nötig sein.

## Vor dem Umschalten auf „Public“ zwingend

- [ ] **Lizenzentscheidung:** Eine eigene Lizenz für den **selbst entwickelten Quellcode** wählen, z. B. MIT oder Apache-2.0, **erst nachdem** die Rechte an eingebundenen Drittbestandteilen geklärt sind. **Noch keine LICENSE-Datei hinzugefügt.** Eine Lizenz der eigenen Software darf Garmin-Material nicht pauschal unterlizenzieren.
- [ ] **FIT-SDK-Rechte:** Herkunft und Weitergaberechte des großen, auf dem Garmin FIT Java SDK basierenden Übungskatalogs (`app/garmin_catalog_part*.py`) rechtlich prüfen. Die [FIT SDK License](https://github.com/garmin/fit-java-sdk/blob/main/LICENSE.txt) ist **nicht** schlicht MIT. Bei ungeklärter Rechtslage Katalog nicht unbesehen öffentlich machen; eine geeignete, nachweislich zulässige Datenquelle oder ausdrückliche Zustimmung prüfen.
- [ ] **Speediance-Bedingungen:** Inoffizielle Cloud-API sowie regionale, für die tatsächlich verwendete Geräte-/App-Cloud geltenden Nutzungsbedingungen prüfen; nicht allein Shop-AGB als maßgeblich voraussetzen. Keine Unterstützung oder Zertifizierung von Speediance behaupten.
- [ ] **Garmin Personal API:** Jeder Benutzer verwendet nur seinen **eigenen** Schlüssel für seine **eigenen** Garmin-Daten. Die FAQ beschreibt den Zugang als für persönliche Nutzung, nicht für kommerzielle Dienste mit mehreren Endkunden gedacht. Nutzung und Weitergabe daran ausrichten; die konkrete Lizenz der Anwendung ersetzt keine API-Erlaubnis.
- [ ] **Komplette Git-Historie prüfen:** Alte Commits, bereits geschlossene Branches/PRs, Commit-Texte und GitHub Actions Logs/Artefakte werden beim Sichtbarkeitswechsel potenziell öffentlich. Nach benutzerspezifischen Trainingsbezeichnungen/Daten, persönlichen Fit-Dateien, Roh-API-Antworten, Screenshots, IDs, Zugangsdaten, Tokens und E-Mail-Adressen suchen. **Eine Prüfung des aktuellen Dateibaums genügt nicht.**
- [ ] **Geheimnisse prüfen und nötigenfalls rotieren:** Spezifische Suche nach API-Schlüsseln, Passwörtern, OAuth-Tokens, privaten Zertifikaten, `.env`, personenbezogenen Test-Fixtures. Sicherheitsvorkehrungen aktivieren. Ein einmal veröffentlichter Schlüssel ist als kompromittiert zu behandeln – selbst nach Git-History-Rewrite.
- [ ] **Build-Artefakte und externe Lizenzen prüfen:** Keine privaten Beispiel-FITs, privaten Diagnosedaten oder Zugangsschlüssel im NSIS-/PyInstaller-Paket. Auf Bedingungen von PyInstaller und NSIS und beizufügende Lizenzhinweise achten.
- [ ] **Marken/Disclaimer:** Nur beschreibende Verwendung „Speediance“ und „Garmin“, keine fremden Logos, kein offizieller Unterstützungsanschein. Dokumentation und Releases klar als inoffiziell kennzeichnen.
- [ ] **Dokumentation und Support:** Aktueller Schnellstart/Benutzerhandbuch, bekannte Einschränkungen, Datenschutz-Hinweis, Changelog, Issue-Vorlage ohne Secrets; geregelte Erwartung an Community-Support.
- [ ] **RC-Freigabe:** Tests + Windows-Installer erfolgreich, Installation auf einem zweiten Windows-10/11-Rechner (keine Entwicklerumgebung) manuell geprüft, mindestens ein direkt über beide Accounts zusammengeführtes Training.
- [ ] **Bewusste Eigentümerentscheidung:** Erst nach Abschluss der Punkte Sichtbarkeit des bestehenden Repos `Pat4best/Speediance-FIT-Exporter` über GitHub **Settings → General → Danger Zone → Change repository visibility** auf Public stellen.

## Technisch bislang festgestellt

- Laufzeitcode ist Python-Standardbibliothek-basiert; im GitHub-Hauptverzeichnis war **keine LICENSE-Datei** vorhanden.
- Live-Test vom 18.11.2026 bestätigt die direkte Garmin-FIT-Zusammenführung einschließlich wiederhergestelltem Training Effect und tatsächlich absolvierten Speediance-Sätzen.
- GitHub-Repositorium ist derzeit **private**, enthält eine umfangreiche Beta-Commit- und Actions-Historie. Diese wurde **noch nicht lückenlos auf personenbezogene Daten oder Geheimnisse geprüft**.
- Bestehende `app/garmin_catalog_part*.py`-Daten stammen aus dem offiziellen Garmin-FIT-Katalog; die konkrete Urheberrechts-/Lizenzlage der gebündelten Enum-Liste bleibt ungeklärt.

## Alternative bei ungeklärter Freigabe

Falls der bestehende Repository-Verlauf sensible Daten enthält: **Nicht blind auf Public schalten**. Erst unabhängig von der Lizenzfrage abwägen, ob ein neuer, sauber zusammengestellter öffentlicher Projekt-Stand ohne Historie geeigneter ist. Ein neues Repository löst **nicht** die Lizenzfrage des Garmin-Katalogs oder API-Nutzungsbedingungen.

Bis zur Klärung bleibt der RC **privat**. Der **fertige Installer kann nach gesonderter Prüfung** testweise an ausgewählte Personen weitergegeben werden; auch dafür sind Lizenz-/Nutzungsrechte zu beachten.
