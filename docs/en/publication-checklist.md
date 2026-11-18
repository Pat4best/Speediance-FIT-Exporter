# Checklist: Publishing the GitHub repository

**Project:** Speediance FIT Exporter · **Current status: NOT approved for public release**  
**Goal:** Complete private RC testing and rights/security assessment before considering public distribution.

This is a preliminary technical and organizational checklist, **not legal advice**. External API access, Garmin SDK-derived data and trademarks may require legal review.

[Deutsche Version](../de/publication-checklist.md) · [Documentation index](README.md)

## Required before switching visibility to Public

- [ ] **Project license:** Select a license for the **software you own** (e.g. MIT or Apache-2.0) only after checking third-party rights. **No LICENSE file has yet been added.** An application license cannot automatically relicense Garmin material.
- [ ] **Garmin FIT SDK rights:** Review origin and redistribution rights for `app/garmin_catalog_part*.py`, which contains an extensive Garmin FIT Java SDK-based exercise catalog. The [FIT SDK license](https://github.com/garmin/fit-java-sdk/blob/main/LICENSE.txt) is **not** simply MIT. Do not publish the entire catalog under an unrelated permissive license without adequate rights; consider authorization or a valid alternative source.
- [ ] **Speediance terms:** Determine the actual applicable regional/device-app/cloud terms for the unofficial API, including any restrictions on automated access or reverse engineering. Do not claim Speediance certification. Web-shop conditions are not necessarily identical to cloud service conditions.
- [ ] **Garmin Personal API:** Each user must use their **own** key for **their own** recordings, consistent with Garmin's personal-use documentation. An open-source application license does not grant permission to share keys or operate a commercial shared-access backend.
- [ ] **Audit ALL Git history:** Existing commits, old branches/PRs, commit messages, Actions logs and downloadable build artifacts could become public. Check for real workout names, FIT files, API responses, screenshots, account IDs, emails, tokens and other identifying data. **Auditing only the current working tree is insufficient.**
- [ ] **Check and rotate secrets if necessary:** Search historical `.env` files, passwords, API keys, OAuth tokens, private certificates and identifiable test fixtures. Activate appropriate secret scanning. Once exposed, a credential should be treated as compromised even if its commit is later rewritten.
- [ ] **Audit packaged artifacts and licenses:** Ensure NSIS/PyInstaller installers include no real user's FIT records, diagnostics or credentials. Follow dependency/license notice obligations.
- [ ] **Trademarks and disclaimers:** Names may be used descriptively without implying brand authorization. Do not use someone else's logos as your own branding.
- [ ] **Public docs and support:** Both language manuals, troubleshooting, limitations, privacy, changelogs, issue reporting instructions (with no credentials), and realistic support expectations.
- [ ] **Release validation:** Windows tests and installer pass; installation is checked manually on a clean Windows PC, and an authorized real end-to-end workout merge is verified.
- [ ] **Repository-owner decision:** Only after completing the checks, consciously change `Pat4best/Speediance-FIT-Exporter` visibility in **GitHub Settings → General → Danger Zone → Change repository visibility**.

## Current technical findings

- App runtime uses the Python standard library. There was **no LICENSE file** in the repository root at the start of the RC review.
- November 18, 2026 end-to-end user verification confirmed the original-based Garmin FIT merge, recorded Speediance strength sets and recovered Training Effect.
- GitHub repository is currently **private** and has an extensive beta commit and Actions history, which has **not** been exhaustively audited for identifying data and secrets.
- The Garmin exercise catalog includes data derived from the official FIT SDK. Rights to redistribute that compiled catalog remain **undetermined**.

## Alternative if the old repository cannot safely be published

Do **not** simply switch visibility on a repository with sensitive history. Depending on licensing and permissions, assess whether a fresh, reviewed repository with a curated source snapshot and no old history would be safer.

**Important:** A fresh repository does **not** solve rights questions for the Garmin catalog or Speediance API access.

Until those issues are resolved, keep the RC **private**. A selected-audience installer distribution must also comply with applicable license and usage terms.
