# Current state

As of 2026-10-05:

- The authoritative public product repository is `lvlaksim1/megafon-desktop`; project/display name is exactly **Megafon Desktop**.
- The earlier `lvlaksim1/megafon-manager` repository has been marked as moved and is legacy/migration material only.
- Product authority and manager-state authority are both `main`.
- Implemented: PySide6 account table, SQLite accounts/snapshots/offer-rule schema, Windows DPAPI password store, direct login + main/commercial balance adapter, transport abstraction, Playwright persistent-profile JSON capture fallback, redacted HAR diagnostics, and pure parsers for MBplugin-observed remainders/services plus recursive expense events.
- Release version metadata is `0.1.0`.
- Windows CI for release commit `8f8c8a316ff0a79a869bc191d6e58aff5cc01f7a` completed successfully: 14 tests PASS and ruff PASS.
- Windows installer workflow run `37340148966` completed successfully through PyInstaller, Inno Setup, artifact upload and GitHub Release publication.
- GitHub Release `v0.1.0` contains `MegafonDesktop-Setup-v0.1.0.exe` (37,659,671 bytes), SHA-256 `9a86fa0b5897ee19b553fc8d954fcf424471e9545fc78f04fcd30bc91c53bcf8`.
- Installation is per-user under `%LOCALAPPDATA%\Programs\Megafon Desktop`; application data remains under `%LOCALAPPDATA%\MegaFonDesktop`.
- After publishing the initial setup, `RELEASE_KIND` was switched to `Update`. Future releases are therefore expected to be executable update installers named `MegafonDesktop-Update-vX.Y.Z.exe`.
- No live MegaFon account mutation has been executed from the development runtime.
- Current parser fixtures are derived from public MBplugin response shapes and legacy VBA semantics; fresh owner browser logs remain the stronger evidence gate for current live contracts.
