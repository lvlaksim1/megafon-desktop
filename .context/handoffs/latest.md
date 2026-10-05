# Latest handoff

## Last completed work

- Consolidated the product under the authoritative public repository `lvlaksim1/megafon-desktop` and exact product name **Megafon Desktop**.
- Marked `lvlaksim1/megafon-manager` as moved/legacy rather than an active product repository.
- Added PyInstaller + Inno Setup release packaging and documented the installer/update policy.
- Fixed release-blocking ruff issues while preserving passing tests.
- Verified release commit `8f8c8a316ff0a79a869bc191d6e58aff5cc01f7a`: Windows CI passed with 14 tests and ruff.
- Windows installer workflow run `37340148966` completed successfully.
- Published GitHub Release `v0.1.0` with `MegafonDesktop-Setup-v0.1.0.exe`; SHA-256 `9a86fa0b5897ee19b553fc8d954fcf424471e9545fc78f04fcd30bc91c53bcf8`.
- Switched `RELEASE_KIND` to `Update` so subsequent releases are emitted as `MegafonDesktop-Update-vX.Y.Z.exe`.

## Verified current state

Native Qt + SQLite + DPAPI + direct consumer-LK balance transport + Playwright response capture + redacted HAR diagnostics + read-data parsers are present. Windows CI and installer packaging are verified. No real MegaFon mutation was executed.

## Next operation

Continue the read-only aggregate/UI path and use fresh owner browser logs as the evidence gate for current protocol contracts. The next release must be an update installer, not a ZIP or manual file replacement.
