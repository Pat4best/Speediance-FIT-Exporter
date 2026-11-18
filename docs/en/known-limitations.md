# Known limitations – 0.1.35-rc.2

Release Candidate 2 is a stabilization and documentation release. The following are explicitly documented limits, **not promised features**.

[Deutsche Version](../de/known-limitations.md) · [Documentation index](README.md)

## Intensity Minutes are not newly credited by Garmin Connect FIT reimports

A merged FIT imported for the November 13, 2026 workout retained the recorded Garmin HR and recovered **Training Effect (0.3 aerobic / 0.0 anaerobic / load 4)**. Garmin Connect still showed no Intensity Minutes for this imported activity, and no additional weekly-minute credit was observed.

- Garmin records Intensity Minutes through separate device and account-health functions. Removing an imported activity need not reverse time credited from the watch itself.
- Neither the Garmin original nor the merged FIT in that controlled test contained any FIT `MONITORING` messages (global message 55). This does **not** establish that adding fabricated monitoring messages would make imported minutes count.
- The exporter **does not manufacture Intensity Minutes** or call undocumented Garmin Connect write APIs.
- Keep synchronizing the original Garmin watch normally for its health/activity statistics.

## Set timestamps, active time and repetitions

Speediance supplies genuine completed repetitions, weights and sometimes set durations, but not a verified absolute start timestamp for every set. The FIT writer estimates set positions; rest periods and the active-time summary may differ from Garmin's original recording. If the estimated first Speediance set would begin before the watch recording, **only the estimated set timeline** is aligned to Garmin start; the actually recorded Garmin HR timestamps are not modified.

Some exercise names require manual mapping to the Garmin FIT catalog. User overrides are saved locally. Timed or other completion methods must not be misrepresented as implausible strength-repetition counts.

## Workouts may appear without completed-set details

A workout can remain visible in the Speediance history while the API no longer provides its performed sets (e.g. API error `100041` after deleting a custom template).

- Previously obtained **local verified cached sets** may still be available. The automatic snapshot attempts up to three uncached recent workouts per retrieval.
- If no genuine completed sets can be verified, the merge refuses to create an output.
- The exporter does not rebuild exercise results from scheduled plans or guess repetitions/weights. No paid GM Manager API is required.

## Original Garmin activity and duplicate uploads

The derived FIT receives a distinct file identity. Garmin Connect may accept it as a separate activity or reject it because its recorded workout time overlaps an existing activity. **The original Garmin activity is never automatically replaced or edited.**

The merged FIT retains the manufacturer and product values actually read from the source Garmin recording rather than a synthetic development device. This was important to the confirmed Training Effect display on Garmin Connect; behavior may differ across devices, firmware and account settings.

## Unsigned installer and external APIs

- The Windows installer is **not code-signed**, so Windows SmartScreen may warn. Install only from a trusted source.
- Speediance uses an **unofficial cloud API** that can change or return different results by device, workout and region.
- The Garmin Personal API requires **your own personal key**. No shared developer key is bundled, sent to the author, or guaranteed to work indefinitely.
- The Speediance login client type may displace a phone session or an actual device using the same slot. `phone` is deliberately not the default.

## Privacy and publication status

Cached sets can contain personal workout/health records. Diagnostics are designed to omit secrets but must still be reviewed before sharing. **Never post passwords, personal API keys, tokens or real user FIT files in public issues.**

A public/open-source repository is **not yet approved**; see [Publication checklist](publication-checklist.md) for the Garmin FIT SDK catalog rights, Speediance API terms, and Git history checks.
