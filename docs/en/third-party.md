# Third-party sources, trademarks and license review

**Version:** 0.1.35-rc.2 · **Preliminary technical assessment, not legal advice**

Speediance FIT Exporter is independent software. Runtime code largely uses the Python standard library; Windows packaging uses PyInstaller and NSIS. Brand names, SDK-derived data, and hosted APIs each have distinct rights and conditions.

[Deutsche Version](../de/third-party.md) · [Documentation index](README.md)

## Garmin FIT SDK and exercise catalog

The included catalog of over 1,800 Garmin exercise category/name entries was compiled from publicly available enum values in the Garmin FIT Java SDK. Those records are in `app/garmin_catalog_part1.py` through `app/garmin_catalog_part5.py` and `app/garmin_catalog.py`. The Garmin Java SDK itself is **not** installed or executed at runtime.

**Public-source release risk:** [Garmin's FIT SDK License](https://github.com/garmin/fit-java-sdk/blob/main/LICENSE.txt) is **not** an ordinary MIT, BSD or Apache open-source license. It contains restrictions relating to the licensed technology and its redistribution. The fact that a field number or enum value is part of a technical protocol does **not automatically authorize redistribution of an entire catalog derived from SDK data under another license**. Check relevant rights before publication, potentially including legal advice, authorization or a demonstrably permissible alternative source.

Do not present your own application license as granting rights to Garmin-owned materials you do not hold. Preserve applicable notices.

- FIT SDK: <https://github.com/garmin/fit-java-sdk>
- FIT protocol: <https://developer.garmin.com/fit/>
- FIT SDK license: <https://github.com/garmin/fit-java-sdk/blob/main/LICENSE.txt>

## Garmin Connect Personal API

The program uses [Garmin Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/) to search and download the user's own original Garmin recordings, in read-only mode. **Each user must issue their own personal API key**. No developer key is shared. This access is intended for personal use with **your own data**, not a commercial shared service.

- [Garmin Personal API FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq)
- Personal key page: <https://connect.garmin.com/app/settings/personalApiToken>
- The exporter does not automatically write or update Garmin Connect activities; the user chooses whether to import locally generated FIT files.
- An open-source license does not permit bypassing Garmin account/key rules or redistributing other people's keys.

## Unofficial Speediance cloud API

The app connects to an **unofficial Speediance API** with credentials the user enters for their own account. Speediance has not licensed or officially certified the interface for this project, nor guaranteed its stability.

**Legal review point:** Applicable regional terms may restrict reverse engineering and automated access. Determine which terms actually apply to the device/cloud application and user region before distributing or publicly releasing this tool. Web-store terms should not automatically be assumed to govern the same service as the hardware/cloud application.

The project name describes the data source only, not authorization or sponsorship by Speediance.

## Packaging dependencies

- **Python:** Runtime uses the standard library without third-party runtime packages.
- **PyInstaller:** Used to bundle the Windows executable; follow its licensing and bundled-dependency redistribution notices. See <https://pyinstaller.org/>.
- **NSIS:** Windows installer builder; see <https://nsis.sourceforge.io/License>. Installer distribution rights are separate from permissions for SDK-derived catalog data.

## Trademarks and disclaimer

“Speediance”, “Garmin”, “Garmin Connect”, “Gym Monster” and associated marks belong to their respective owners. No sponsorship, certification or formal partnership is claimed. Do not use external logos as this project's brand identity.

**Status:** This document does **not** establish redistribution rights. The repository stays **private** until Garmin catalog permissions, applicable Speediance terms and historical commits/artifacts are reviewed.
