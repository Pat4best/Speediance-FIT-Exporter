# Speediance FIT Exporter – English quick start

**Version:** 0.1.35-rc.1 · **Windows 10/11** · Independent third-party community tool (not affiliated with Speediance or Garmin)

For complete instructions and troubleshooting, see the [German user manual](Benutzerhandbuch.md). The application itself supports **English** through the language selector in the top right corner.

## Purpose

Export **completed** Speediance strength exercises/sets directly from your own Speediance account. Merge those recorded sets with the **original Garmin activity** obtained through Garmin Personal API. The resulting FIT file retains original Garmin sensor records, original device identity and the Training Effect fields as far as confirmed by live Garmin Connect tests.

No paid GM Manager API, manually downloaded Garmin FIT file or CSV export is required for the recommended workflow. The app never uploads or alters your existing Garmin Connect activity automatically.

## Install

1. Download the trusted `SpeedianceFITExporter-Windows-Setup-0.1.35-rc.1` ZIP artifact from the project's successful GitHub Actions Windows installer run, or obtain it from the distributor.
2. Extract and run `SpeedianceFITExporter-Setup.exe`; installation is per Windows user and does not require Python or administrator access.
3. Start **Speediance FIT Exporter** from the Windows Start menu. The installer is currently **unsigned**; only run it if you trust the source.

## Merge a workout

1. Enter your Speediance email/password, select the **EU** or **Global** region, and sign in. Default login type `bike` avoids competing with the phone app when you do not own a Speediance Bike; choose `nano` if appropriate. **Using `phone` may sign out your Speediance mobile app**. Login slots may conflict with actual devices.
2. Set a date range in `YYYY-MM-DD` format and click **Load workouts / Trainings laden**.
3. Select one completed workout. Optionally choose **Map exercises / Übungen zuordnen…** to match Speediance exercise names to the built-in Garmin exercise catalog. With a selected workout, this list reflects only that workout's cached completed exercises; no selection displays previous mappings.
4. Click **Match with Garmin / Mit Garmin abgleichen…** and select **Garmin Personal API** as the source.
5. Use **Create key / Schlüssel erstellen** or visit <https://connect.garmin.com/app/settings/personalApiToken>. Paste your personal Garmin API key; optionally save it in Windows Credential Manager.
6. Keep the initial data priorities at **Garmin** for timestamps, duration, HR and calories. Click **Find Garmin activities / Garmin-Aktivitäten suchen**, select the correct time-matched original recording.
7. Click **Save merged FIT / Zusammengeführte FIT speichern…**. The original Garmin activity stays untouched. This step creates a **new local FIT file**.
8. Manually import this file into <https://connect.garmin.com/> using **Import data**. Verify completed sets, reps, weights, heart rate and Training Effect. The import **does not overwrite** the original, and may be rejected as a duplicate.

**Alternative input:** Choose **Local Garmin FIT file** if the Garmin Personal API is unavailable; you must then provide an authentic original Garmin FIT file.

**Alternative export:** **Export selected as FIT** creates a Speediance-only activity; it will not contain your original Garmin watch's Training Effect or device telemetry.

## Important limitations

- **Intensity Minutes:** The controlled Garmin Connect test did not credit the manually imported merged activity with additional weekly intensity minutes, even after Training Effect was restored. This is a Garmin import/account-health behavior; continue syncing your Garmin watch normally.
- **SET timestamps and active/rest time:** Direct Speediance data contains recorded sets but not verified absolute start times for every set. Some timing is necessarily estimated.
- **Deleted templates/missing history:** Speediance may list completed activities while refusing access to their recorded sets. A previously cached completed-set snapshot may help, but the app never invents sets.
- **Training Effect:** Confirmed recovered with original Garmin manufacturer/product fields retained in the new FIT, while keeping a distinct file identity. Further Garmin Connect import behavior can vary.

## Privacy and safe sharing

The app uses Speediance and Garmin online services only for account login/read-only retrieval, and merges FIT files locally. Optional credentials and the personal Garmin API key are stored via **Windows Credential Manager**; exercise mappings, settings, anonymous-ish diagnostics and cached completed workouts are stored under `%LOCALAPPDATA%\\SpeedianceFITExporter\\`. Cached sets and heart rate are personal information. Review diagnostics before sharing; **never share passwords, API keys or tokens**.

The Windows uninstaller removes the application, **not necessarily your user settings/cache/credentials**. The project is independent of the two brands, relies on an unofficial Speediance API, and is distributed without a code-signing certificate.
