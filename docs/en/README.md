# Documentation – English

**Speediance FIT Exporter 0.1.35-rc.2** · Windows 10/11 · Independent community project

[Deutsche Dokumentation](../de/README.md) · [Project home](../../README.md)

The maintained documentation uses **two synchronized language directories**, `docs/de/` and `docs/en/`. Each directory has **the same topics and identical filenames**. Content changes should be reflected in both languages. Automated tests check filename parity, complete manual chapter coverage and relative links.

## For users

- [Quick start](quick-start.md) – installation and the direct Speediance→Garmin workflow
- [Complete user manual](user-guide.md) – all features, exercise mapping, Garmin Personal API, imports, privacy and troubleshooting
- [Known limitations](known-limitations.md) – Intensity Minutes, estimated SET timing, missing Speediance details and duplicates
- [Changelog](changelog.md) – RC versions and earlier beta milestones

## For developers and distributors

- [Development and builds](development.md) – architecture, Windows build, tests and data provenance
- [RC acceptance checklist](rc-checklist.md) – automated and manual quality checks
- [Third-party sources and license notices](third-party.md) – Garmin FIT SDK, Speediance, trademarks and packaging dependencies
- [Public repository checklist](publication-checklist.md) – unresolved licensing and security checks before visibility change

## Archive

The original 900+ lines of detailed beta-development notes are retained as an **unmaintained German-language historical archive** in [archive/Entwicklungshistorie.md](../../archive/Entwicklungshistorie.md). The archive is **outside the active mirrored documentation** and may contain outdated instructions.

**Important:** The release candidate never modifies Garmin Connect automatically. In our tested FIT import, weekly Intensity Minutes were not newly credited. The repository stays private pending independent rights and security review.
