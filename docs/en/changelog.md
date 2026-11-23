# Changelog

[Deutsche Änderungsübersicht](../de/changelog.md) · [Documentation index](README.md)

Key changes in reverse chronological order. For detailed early beta history, see the [German archive](../../archive/Entwicklungshistorie.md).

## 0.1.36-beta – Speediance and Garmin merge (November 23, 2026)

- The merged FIT exports a repetition count for rep-based sets and a duration for timed sets.
- Development resumes in beta. A new release candidate will follow after acceptance testing.

## 0.1.35-rc.2 – Full bilingual documentation (November 18, 2026)

**Documentation and packaging only; FIT merge and API behavior are unchanged.**

- Reorganized maintained documentation into `docs/de/` and `docs/en/` with the **same nine file names and mirrored topics**.
- Complete German and English ten-chapter user manuals, quick starts, limitations, third-party notices, development instructions, release/publication checklists and changelogs.
- Language switch links, navigation indexes and unmaintained beta notes moved to a separate historical archive.
- Windows installer and CI artifacts contain **both complete language directories**. Start-menu shortcuts open the respective full-language manuals.
- Added automated validation of filename parity, local links, full manual chapters and RC version consistency.

## 0.1.35-rc.1 – Release Candidate 1 (November 18, 2026)

**Stabilization and documentation release; no new FIT or API features.**

- Froze the tested 0.1.35-beta Garmin Connect import: actual Speediance completed sets merged into original-Garmin-based FIT with correct device identity, HR and Training Effect.
- Application version changed to `0.1.35-rc.1`.
- Replaced the previous 900+ line beta README with a concise project overview.
- Created a complete German user manual, an English quick start, technical build instructions, limitations, third-party/publication notes and an acceptance checklist.
- Original detailed beta notes were preserved as historical records.
- Installer included basic user documentation.
- Repository remained **private**, pending a license choice, review of Garmin FIT SDK-derived catalog data, Speediance API terms and historic Git/Actions content.

**Known limits:** No newly credited weekly Intensity Minutes on the tested Garmin Connect FIT reimport; the app cannot invent unavailable completed-set data; absolute set start times are not always available; imported activities never replace existing Garmin Connect recordings automatically.

## 0.1.35-beta – Real Garmin manufacturer/product identity and Training Effect

- The derived FIT retains `file_id.manufacturer` and `file_id.product` from the genuine original Garmin recording, without inventing a new device.
- It still receives a new serial and creation-time identity.
- A controlled Garmin Connect import then displayed **0.3 aerobic / 0.0 anaerobic Training Effect, load 4**, together with four actual Speediance sets.
- Original Garmin device and sensor messages remain preserved.

## 0.1.34-beta – Direct merge and diagnosable errors

- Retrieved actual completed Speediance sets and HR from the account-isolated cache.
- Aligned estimated set start timestamps when Speediance began before Garmin, without shifting real Garmin HR samples.
- Preserved specific Garmin FIT errors instead of converting them into generic `ValueError` messages.

## 0.1.33-beta – Per-workout exercise mapping

- **Map exercises…** displays only actual account-scoped cached exercise names belonging to the selected workout, never exercises belonging to other sessions.
- Without a selected workout, previously saved global mappings remain accessible. Offline mapping works even when cloud data is missing.

## 0.1.32-beta – Proactive completed-workout backup

- Cached verified performed strength sets for up to three recent uncached workouts per retrieval, covering the preceding 30 days.
- Account/region/workout isolation; training templates without completed sets are never interpreted as performed exercises.
- Added completed Free Lift handling and appropriate weight provenance.

## 0.1.31-beta and earlier

- Garmin Personal API and original FIT overlay, exercise mapping, extensive Garmin FIT exercise catalog, FIT export/weight conversion, bilingual UI, Speediance calendar/history discovery and optional Windows Credential Manager storage.
- For full historical details, see the [German beta archive](../../archive/Entwicklungshistorie.md).
