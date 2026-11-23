# Speediance FIT Exporter – User Manual

**Version:** 0.1.36-beta (Beta)
**Platform:** Windows 10/11  
**Application languages:** German and English  
**Project status:** Independent community software; neither developed nor endorsed by Speediance or Garmin

> **Important:** This application never automatically modifies data in Garmin Connect. It creates a **new local FIT file** that you may import manually. Existing activities are **not overwritten**. In our Garmin Connect tests, manually reimporting a FIT **did not add Intensity Minutes to the weekly account total**.

[Deutsche Version](../de/user-guide.md) · [Documentation index](README.md)

## 1. What does the application do?

Speediance FIT Exporter retrieves **completed** exercises, sets, repetitions, weights and, where available, heart-rate readings from your own Speediance account. For the recommended workflow it also downloads your original Garmin activity through **Garmin Personal API** and produces a new local FIT file. The original Garmin device/sensor information and recorded Training Effect values are retained, while actual completed Speediance strength sets replace the original strength-set messages.

You do not need a paid GM Manager service, a CSV export, or a Garmin FIT file downloaded manually before using the recommended workflow.

**Not included:** automatic uploads to Garmin Connect, editing existing Garmin Connect activities, a guarantee for all Speediance workout types, or a guarantee of credited Garmin Intensity Minutes after reimport.

## 2. Installation and first launch

1. Obtain the `SpeedianceFITExporter-Windows-Setup-0.1.36-beta` ZIP package. In the private project it is available under **GitHub Actions → Windows installer → successful beta build → Artifacts**, or you may receive it directly from your distributor.
2. Extract the ZIP file. It contains `SpeedianceFITExporter-Setup.exe` and this manual.
3. Run the installer and follow the wizard. Installation is performed for the current Windows user without administrator permissions.
4. Launch the program from **Start → Speediance FIT Exporter**.
5. Because the installer and executable are not code-signed, Windows SmartScreen may warn about an unknown publisher. **Only run files from a source you trust.** Do not disable system security measures globally.

**No Python installation is needed to use the app.** To develop or build it yourself, see [Development and building](development.md).

## 3. Sign in to Speediance and load workouts

1. Enter the email address and password for **your own** Speediance account and select the appropriate region (**EU** or **Global**).
2. The default login client type is `bike` if you do not own a Speediance Bike. If you use the Bike, `nano` can be an alternative provided you do not own a Gym Nano. **`phone` can sign your Speediance phone app out.** Any selected login type may conflict with an actual device of the same type.
3. Click **Sign in** (`Anmelden`). If you want, select **Save credentials on this PC** (`Anmeldedaten auf diesem PC speichern`). Opted-in credentials are stored using Windows Credential Manager; without this choice they are not persisted.
4. Select the period in `YYYY-MM-DD` format and click **Load workouts** (`Trainings laden`).
5. Select a **completed** workout from the table. It lists its date, title, duration and calories.

**Automatic local backup:** During retrieval, the app attempts to preserve details for up to **three** not-yet-cached completed workouts from the last **30 days**. Successfully obtained real sets are stored locally, isolated by Speediance account, region and workout. This may protect completed-set details if Speediance later removes a template. Unavailable data is never replaced with invented exercise records.

## 4. Map Speediance exercises to Garmin

Garmin and Speediance use different strength-exercise names. To correct unknown mappings:

1. Select a workout and click **Map exercises…** (`Übungen zuordnen…`). The editor displays **only previously cached completed exercises for the selected workout**, rather than names belonging to unrelated sessions.
2. Choose a Speediance exercise on the **left**, search for its Garmin equivalent on the **right**, then click **Assign** (`Zuordnen`).
3. Repeat for any remaining exercises. Saved mappings also apply to later workouts using the same Speediance exercise names.
4. If no exercises appear on the left, completed-set details may not be cached yet. Use **Load exercise names from Speediance…** (`Übungsnamen von Speediance laden…`) to request them explicitly. If still unavailable you may use **Add exercise name…** (`Übungsname hinzufügen…`), but this **does not create any completed sets**.

**When no workout is selected**, **Map exercises…** displays your previously saved global exercise names. Existing mappings are preserved.

**Weights:** Values already reported by Speediance as total resistance are not doubled. For values explicitly reported per handle, you may configure a manual multiplier through the mapping editor. Verify the actual recorded measurement before changing this setting.

## 5. Recommended workflow: Merge with the original Garmin activity

This method best preserves the Garmin watch's original measurements:

1. Record your workout on your Garmin watch as a strength activity too, then let the watch synchronize the original recording to Garmin Connect.
2. Open the exporter, sign in to Speediance and click **Load workouts**.
3. Select **exactly one** corresponding Speediance workout and click **Match with Garmin…** (`Mit Garmin abgleichen…`).
4. Under **Garmin FIT source**, select **Garmin Personal API** (instead of the **Local Garmin FIT file** option).
5. Click **Create key** (`Schlüssel erstellen`) to visit Garmin's personal API key page: <https://connect.garmin.com/app/settings/personalApiToken>. Create a key for **your own account**, then paste it into the appropriate field. Optionally save the key securely in Windows Credential Manager.
6. Initially leave the **data priority** for workout start, duration, heart rate and calories set to **Garmin**. The real completed strength sets still come from Speediance.
7. Click **Find Garmin activities / check FIT** (`Garmin-Aktivitäten suchen / FIT prüfen`). Select the recording matching the workout's actual timing. Matching requires more than the calendar date alone.
8. Click **Save merged FIT…** (`Zusammengeführte FIT speichern…`) and choose a location. The exporter downloads the original Garmin FIT through the read-only Personal API, adds the completed Speediance sets locally, and saves a **new file**.

**Important:** If the app cannot retrieve any verified completed Speediance sets, it refuses the merge. It does not silently create an apparently successful Garmin-only file.

### Alternative: Choose an original Garmin FIT file locally

If Garmin Personal API is unavailable, select **Local Garmin FIT file** (`Lokale Garmin-FIT-Datei`) in the same dialog and supply a **genuine, unmodified Garmin original** FIT previously downloaded from Garmin Connect. The remaining steps are similar. This is only a fallback and is not required for normal use.

### Alternative: Export a standalone Speediance FIT

**Export selected as .fit** (`Ausgewählte als .fit exportieren`) creates a Speediance activity without the Garmin original. Therefore it **does not contain the original watch's Training Effect or Garmin sensor/device information**. Use the Garmin merge for the combined analysis.

### Optional legacy data imports

The Garmin merge dialog also retains optional GM Manager JSON/History CSV import functions for exceptional situations. They are **not required** for the normal workflow. A JSON training plan is not proof of completed sets, so the program requires explicit confirmation before accepting those values. No paid GM Manager API is needed.

## 6. Import the new FIT into Garmin Connect

1. Sign in at <https://connect.garmin.com/>.
2. Open **Import Data** (on Garmin Connect Web, generally via the cloud symbol) and select the saved `YYYY-MM-DD_Speediance_Garmin_MERGED.fit` file.
3. Verify exercises, sets, repetitions, weights, heart rate and **Training Effect**.
4. The original activity synchronized by your watch is **not automatically replaced**. Garmin Connect may import the new file as a second activity, or reject it as a duplicate because the activity times overlap.

**Never delete the original Garmin activity merely to force a test import.** Keep a backup of the original Garmin FIT as well. When removing an unwanted duplicate, verify that you are deleting **only the additional imported activity**.

## 7. Which Garmin data is preserved?

The authentic Garmin FIT is the base of the merge. Original device information, proprietary messages and recorded Garmin heart-rate records are preserved. The watch-recorded **Training Effect fields** also stay in the FIT. The exporter also keeps the original Garmin manufacturer and product values. A real Garmin Connect import test of the November 13, 2026 workout displayed **0.3 aerobic / 0.0 anaerobic Training Effect, training load 4**, and **four Speediance sets** after the merge.

The new output FIT has a fresh file identity. It is **an edited derivative, not an unchanged Garmin device recording**. Selecting Speediance for individual priority settings can intentionally change certain session-summary fields.

**Important limitations:**

- **Intensity Minutes:** The imported merged activity **did not add any new Intensity Minutes to the Garmin weekly account total** in the tested case, even though Training Effect was displayed. This is not just a missing label inside the activity. Continue synchronizing the original Garmin watch normally; the exporter does not guarantee imported Intensity Minutes.
- **Set/rest timing:** Speediance supplies genuine repetitions, weights and some set durations, but not a verified absolute start timestamp for every set. Set positions and Garmin's active-time statistics may be estimated or differ from the source recording.
- **Missing/deleted workout details:** If Speediance reports a completed calendar entry but no longer supplies the recorded sets (for example API code `100041`), the exporter cannot reliably reconstruct those records. A previously populated local cache may help.
- **Imported health statistics:** Garmin Connect determines according to its own rules whether imported activities contribute to account-level health and wellness statistics.

## 8. Privacy, local storage and uninstalling

- Sign-in and workout retrieval communicate between your Windows application and **Speediance**. Garmin activity search and original FIT download communicate with **Garmin**. These are external services.
- FIT processing and exercise mapping happen **locally on your PC**. The app never uploads an activity to Garmin Connect by itself.
- Your login password and optional Garmin API key are stored only if you explicitly request it, using **Windows Credential Manager**. Short-lived login session tokens are not saved in normal program settings.
- Workout results, exercise names, exported FIT files and configuration values may contain personal or health data. Share these only with appropriate consent.
- Local settings, exercise mappings, diagnostic logs and a cached copy of completed sets are stored under `%LOCALAPPDATA%\SpeedianceFITExporter\`. The cache may include recorded weights, repetitions and heart-rate data.
- **Save diagnostic log…** (`Diagnoseprotokoll speichern…`) produces a diagnostic file. Logging is designed to avoid secrets and identifiers, but **you must review the content yourself before sharing it**.
- **Uninstallation:** The Start-menu uninstaller removes the application. It does **not automatically delete** all local settings, FIT exports, caches or optional saved Windows credentials. If you want a full personal-data cleanup, additionally review the aforementioned data directory and corresponding Windows Credential Manager entries.

## 9. Troubleshooting

| Problem | What to do |
| --- | --- |
| Cannot sign in to Speediance | Verify email, password, EU/Global region and login client type. The API is unofficial and can change. |
| Speediance phone app was signed out | A login slot may have conflicted with the mobile app. Avoid `phone` if you want to keep your phone logged in. |
| Workout is listed but exercises are missing | Speediance may no longer provide its completed-set details. Check another completed workout; the exporter does not derive recorded sets from planned templates. |
| **Map exercises…** displays an empty list | The selected workout has no cached completed exercises. Optionally click **Load exercise names from Speediance…**. |
| Garmin workout cannot be found | Verify workout start and duration on both sides; the watch's original recording should already be synchronized. |
| Garmin API key does not work | Check that the personal key belongs to the intended Garmin account; regenerate it with Garmin if necessary. |
| Training Effect missing after import | Confirm that you used a **merged FIT based on a genuine Garmin original** and exporter **0.1.35-rc.2 or later**. |
| Intensity Minutes missing after import | Known Garmin Connect import limitation. Continue the normal watch synchronization. It is **not proven to be a bug in our FIT writer**. |
| Garmin Connect reports a duplicate | Do not casually delete the original Garmin activity. Import does not update existing activities. |
| Windows warns about unknown publisher | The installer is unsigned. Verify where the file came from; do not disable security globally. |

## 10. Help and reporting bugs

Include the **application version**, the exact steps you took, the **error message**, and whether the problem occurred before or after the Garmin merge. Use **View diagnostics…** (`Diagnose anzeigen…`) or **Save diagnostic log…** and remove any personal information before sharing. **Never publish passwords, API keys, tokens or other people's FIT files.**

This is not an official Speediance or Garmin product. Users do not need access to the private GitHub repository to run an installed copy; distribution of the RC installer is a separate matter while legal/publication checks remain outstanding.
