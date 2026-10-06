# Latest handoff

## Current release

**Megafon Desktop v0.3.6** is published.

- Installer: `MegafonDesktop-Update-v0.3.6.exe`
- Size: 36,352,321 bytes
- SHA-256: `4bf3b7591fffa34ae0812d2b6d9b73320afef342c10b2e391da16582317b5eb1`
- Target: `3bc479cdb988244c6ec82010969f641ab82ecb2b`
- CI: 28 tests PASS, ruff PASS
- Frozen executable startup-smoke: PASS
- Only latest release retained.

## Stable-table direction

The hard rollback to v0.3.0 remains the architectural base. v0.3.6 restores only the previously successful features that do not depend on the abandoned QML reorder/animation branch.

- Qt Widgets/QTableWidget account table.
- Native movable columns retained.
- Stable complete row-order persistence through the native vertical header.
- Cell click/range selection, double-click editing, arrow-key navigation, native wheel scrolling.
- Local **Метка** persists; server fields are temporary edits.
- Ctrl+F active-table search.
- Dark scrollbars.
- No cell-value hover tooltips.

## VBA offer workflow

- /api/personaloffer/game
- /api/personaloffer/availableOffers
- full offer detail
- catalog + phone associations
- keep/delete rules
- same-name rule inheritance
- unknown-offer decision dialog
- /api/personaloffer/rejected/{id}
- reread after rejection
- only kept offers appear in the account summary
- offer-linked options populate **Доступные опции**

## Packaging

The unused Qt OpenSSL backend/libcrypto pair is removed from the frozen package, and the already-built executable must pass startup-smoke before installer publication.
