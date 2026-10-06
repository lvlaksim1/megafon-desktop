# Current state

As of 2026-10-06:

- Authoritative repository: `lvlaksim1/megafon-desktop`.
- Current published version: **v0.3.6**.
- Release asset: `MegafonDesktop-Update-v0.3.6.exe`, 36,352,321 bytes.
- SHA-256: `4bf3b7591fffa34ae0812d2b6d9b73320afef342c10b2e391da16582317b5eb1`.
- Release target: `3bc479cdb988244c6ec82010969f641ab82ecb2b`.
- CI: 28 tests PASS and ruff PASS. Windows release workflow: tests/lint, PyInstaller, Qt OpenSSL cleanup, frozen-exe startup smoke, Inno Setup and release publish all PASS.
- The account table remains **Qt Widgets/QTableWidget**, intentionally avoiding the later QML table/reorder branch.
- Columns remain resizable/movable through the v0.3.0 QHeaderView mechanism.
- Row ordering no longer relies on a partial drop list. Rows are reordered through the native vertical header and the app writes only a complete unique account-id sequence to SQLite.
- Normal click selects a cell; left-button drag selects a cell range; table panning by left drag is disabled. Native mouse-wheel scrolling and scrollbars are used.
- Double click enters cell editing. **Метка** persists to SQLite; server-derived edits remain temporary and disappear on reload.
- Ctrl+F searches the active table with next/previous navigation.
- Cell-value hover tooltips are not used.
- Dark-theme scrollbars are explicitly darkened.
- The v0.3.1 VBA offer workflow was restored without restoring QML: /personaloffer/game, availableOffers, detail fetch, offer catalog, phone associations, keep/delete rules, title-based inheritance, unknown-offer dialog, reject endpoint and reread after rejection.
- **Доступные опции** now stores offer-linked options extracted from full offer details, deduplicated by optionId, matching the VBA model rather than /api/options/v2/list.
- Blocking enable keeps the one-shot behavior: successful POST -> local Да, no immediate verification request. Unblocking resolves the current blocking option id and DELETEs it.
- The proven HTTP-only B2C auth/sessionCheck/CAPTCHA/DPAPI foundation remains.
- Refresh-token renewal remains intentionally unimplemented pending a proven current B2C source.
