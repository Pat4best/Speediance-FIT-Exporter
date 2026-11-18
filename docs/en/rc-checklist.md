# Release-candidate acceptance checklist – 0.1.35-rc.2

This checklist separates **automated Windows CI checks**, **manual distribution testing**, and **known non-goals**. It contains no private credentials or user FIT files.

[Deutsche Version](../de/rc-checklist.md) · [Documentation index](README.md)

## Automated (GitHub Actions / Windows)

- [ ] `python -m unittest discover -s tests -v` succeeds on Windows
- [ ] PyInstaller creates `SpeedianceFITExporter.exe`
- [ ] NSIS creates `SpeedianceFITExporter-Setup.exe`
- [ ] CI uploads a versioned installer ZIP containing **both complete, mirrored documentation directories**
- [ ] Application version reports `0.1.35-rc.2`
- [ ] Garmin merge retains the original manufacturer/product, uses a fresh file identity, and preserves Training Effect, device messages and original sensor measurements
- [ ] No personal account data, actual user FIT files or credentials are embedded in the distribution

## Manual testing on a clean Windows 10/11 PC

- [ ] Installer runs and requires no installed Python
- [ ] Start-menu application shortcut works
- [ ] Both German and English **complete** user manuals open via Start-menu shortcuts
- [ ] Complete DE/EN documentation folders and changelogs are present after installation
- [ ] Sign in to Speediance using one's own account and region
- [ ] Selecting a period and loading workouts lists genuinely completed sessions
- [ ] Exercise mapping shows only cached names for the selected workout; previously saved mappings remain available
- [ ] Own Garmin Personal API key retrieves the appropriately time-matched original Garmin recording
- [ ] **Save merged FIT** produces a new file with recorded actual Speediance sets
- [ ] Garmin Connect import displays exercises/weights, HR summary and Training Effect
- [ ] The original Garmin activity remains unchanged by the exporter
- [ ] Missing completed-set details abort the merge rather than creating an empty or misleading output
- [ ] The uninstall process removes application files but keeps user settings and cache separate

## Deliberately NOT claimed as passed

- **Intensity Minutes:** In the known test, the Garmin Connect FIT reimport did not add new weekly minutes; documented limitation rather than an RC release blocker.
- **All Speediance models, workout types and regions:** Not validated with all live accounts.
- **Public/open-source publication:** Requires separate licensing, terms-of-use and complete Git/Actions history review.

## Previously confirmed behavior

- 0.1.35-beta: **164 Windows unit tests** and installer passed; direct Speediance → Garmin Personal API → merged FIT → Garmin Connect import confirmed with Training Effect restored.
- RC.1: **168 Windows tests** and installer passed with the first complete German handbook.
- RC.2: Documentation and packaging update only; the working FIT and API logic are not modified.
