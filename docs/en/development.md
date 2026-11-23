# Development, tests and Windows builds

**Target:** Technical reference for **0.1.36-beta**. Regular Windows users do **not** need these steps.

[Deutsche Version](../de/development.md) · [Documentation index](README.md)

## Architecture at a glance

- `app/main.py`: Tkinter UI, background-worker coordination, Speediance authentication and workout history.
- `app/speediance_api.py`: Unofficial read-only Speediance API, discovery of calendars/history, and actual completed-set detail requests. Derived metrics are calculated only with a justified source.
- `app/completed_workout_cache.py`: Local cache of genuinely completed exercises, segregated by account, region and workout, without persistently saved access tokens.
- `app/exercise_discovery.py`, `app/mapping_editor.py`, `app/exercise_mapping.py`, `app/garmin_catalog*.py`: Completed exercise-name discovery, user mappings, Garmin category/subtype catalog.
- `app/garmin_personal.py`: Garmin Personal API access with each user's own key; read-only activity search and original FIT download.
- `app/garmin_fit_reader.py`, `app/garmin_fit_overlay.py`, `app/garmin_merge.py`, `app/fitwriter.py`: Garmin-original-based FIT overlay retaining device and sensor messages, source manufacturer/product identity and Training Effect fields while writing genuine performed Speediance `SET` messages.
- `app/windows_credentials.py`, `app/preferences.py`: Windows Credential Manager for opted-in credentials, local JSON preferences without tokens.
- `.github/workflows/windows-installer.yml` and `installer.nsi`: Windows CI tests, PyInstaller packaging and NSIS setup.

## Development environment (Windows)

Install **Python 3.12**. From the repository root run:

```powershell
python -m unittest discover -s tests -v
python app/main.py
```

Unit tests do **not** require personal accounts, Garmin API keys or live network access. They cover missing/unavailable Speediance details, selected-workout-only mapping, original Garmin FIT integrity, real strength-set counts, HR preservation and FIT conformance.

## Build a Windows installer

```powershell
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean --onefile --windowed --name SpeedianceFITExporter --paths app app/main.py
```

Then with **NSIS** installed:

```powershell
& "${env:ProgramFiles(x86)}\NSIS\makensis.exe" installer.nsi
```

Output: `dist/SpeedianceFITExporter-Setup.exe`. The installer includes documentation from both `docs/de/` and `docs/en/`. Do **not** copy any user's FIT exports, completed-workout cache or saved credentials into build directories.

GitHub **Actions → Windows installer** first runs the tests, then creates the executable and NSIS setup, and uploads a versioned ZIP artifact including both documentation trees. A failed test must fail the build.

## Invariants for data and merging

1. **Never invent performed sets:** A training plan is not a recorded workout. Abort when completed details are unavailable.
2. **Do not double weights blindly:** Already-total resistance is not multiplied; a per-handle correction must follow confirmed source semantics.
3. **Preserve authentic Garmin data:** Retain original data messages, developer fields and sensor measurements wherever possible; preserve the real manufacturer/product values, while giving the edited FIT its own fresh file identity.
4. **Distinguish measured and estimated timestamps:** Completed set duration may be measured while absolute start time is estimated. Do not shift real Garmin HR samples to match guessed strength-set positions.
5. **Garmin API is read-only:** Use it to locate/download the original activity only. The user controls any manual Garmin Connect import.
6. **State known limits explicitly:** Do not manufacture FIT monitoring messages for Intensity Minutes; the watch's original weekly total can be maintained independently of imported activities.

## RC acceptance tests

See [RC checklist](rc-checklist.md). CI tests run on Windows. A real end-to-end Speediance + Garmin workflow can be validated only by a user with **their own** authorized accounts; never put live credentials into source or test fixtures.

## Public repository and licensing

Before publishing source code, consult [Publication checklist](publication-checklist.md) and [Third-party sources](third-party.md). The Garmin exercise catalog originates from FIT SDK enum data; do not assume that a permissive license for your own code automatically covers Garmin catalog rights.
