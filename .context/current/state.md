# Current state

- Public repository `lvlaksim1/megafon-desktop` was created through `repo-factory` with Project Manager/Context Capsule installed.
- Product authority and manager-state authority are both `main`.
- Implemented: PySide6 account table, SQLite accounts/snapshots/offer-rule schema, Windows DPAPI password store, direct login + main/commercial balance adapter, transport abstraction, Playwright persistent-profile JSON capture fallback, and pure parsers for MBplugin-observed remainders/services plus recursive expense events.
- Verification: 11 local unit tests PASS and Python bytecode compilation PASS. No live MegaFon account requests were executed from this development runtime.
- Current parser fixtures are derived from the public MBplugin response shapes and legacy VBA semantics; owner browser logs remain the stronger evidence gate for current live contracts.
- The first GitHub Actions workflow was introduced with the bootstrap and its Windows result still requires verification.
