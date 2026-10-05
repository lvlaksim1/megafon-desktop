# Windows releases

Megafon Desktop is distributed as an Inno Setup executable installer.

## Initial installation

The first public package is:

`MegafonDesktop-Setup-v0.1.0.exe`

It installs per-user into:

`%LOCALAPPDATA%\Programs\Megafon Desktop`

Application data and encrypted account secrets stay outside the program directory under:

`%LOCALAPPDATA%\MegaFonDesktop`

## Updates

All subsequent project updates must be published as executable update installers:

`MegafonDesktop-Update-vX.Y.Z.exe`

The update installer uses the same Inno Setup `AppId` and destination as the initial installer, so it upgrades the existing installation in place. ZIP archives and manual file replacement are not part of the normal update workflow.

For each later release:

1. keep `RELEASE_KIND` set to `Update`;
2. change `RELEASE_VERSION` to the new semantic version;
3. push to `main`.

Changing `RELEASE_VERSION` triggers the Windows release workflow. It runs tests and lint, builds the PyInstaller application, wraps it with Inno Setup and publishes the executable to the matching GitHub Release.
