# Windows releases

Megafon Desktop is distributed as a single Inno Setup executable installer.

## Installation locations

Program files are installed per-user into:

`%LOCALAPPDATA%\Programs\Megafon Desktop`

All application-owned persistent data is kept under:

`%LOCALAPPDATA%\MegaFonDesktop`

That data directory contains the SQLite database, DPAPI-encrypted account secrets and browser
profiles used by the Playwright fallback.

No application-owned persistent data should be written outside those two roots.

## Updates

The initial public package was `MegafonDesktop-Setup-v0.1.0.exe`. Every later package is an
executable update installer:

`MegafonDesktop-Update-vX.Y.Z.exe`

The update package contains the complete application payload. It uses the same Inno Setup
`AppId` and destination, so it upgrades an existing installation in place; when no previous
installation exists, the same executable can perform a clean installation.

ZIP archives and manual file replacement are not part of the release workflow.

## Uninstall

The uninstaller removes the dedicated program directory, application data directory, SQLite
database, DPAPI-encrypted secrets, Playwright profiles and application shortcuts. Inno Setup also
removes its own uninstall registration.

Windows-owned forensic/history data such as Prefetch or Event Log entries is outside the
application's storage contract and is not modified.

## Repository storage policy

Release builds do not upload GitHub Actions artifacts. The installer is uploaded directly from the
ephemeral runner workspace to GitHub Releases.

After a successful release, the workflow:

1. keeps the newly published release;
2. deletes older GitHub Releases and their tags;
3. deletes any Actions artifacts that may remain from older workflows.

Therefore the repository keeps source code plus only the current release installer as a retained
binary distribution.

For each later release:

1. keep `RELEASE_KIND` set to `Update`;
2. bump `RELEASE_VERSION`, package version and runtime `__version__` together;
3. push the synchronized version change to `main`.

Changing `RELEASE_VERSION` triggers the Windows release workflow. It runs tests and lint, builds
the PyInstaller application, wraps it with Inno Setup and publishes the executable to the current
GitHub Release.
