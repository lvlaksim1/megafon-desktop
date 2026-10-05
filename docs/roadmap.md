# Roadmap

## M0 — repository and architecture

- [x] Public repository via repo-factory with Project Manager/Context Capsule.
- [x] Native Qt application skeleton.
- [x] SQLite account/snapshot persistence.
- [x] Windows DPAPI secret storage.
- [x] Direct login + balance transport from legacy VBA contract.
- [x] Unit-test baseline and CI.

## M1 — HTTP-only authorization and manual refresh

- [x] No automatic network refresh at application startup.
- [x] Per-account **Обновить** action.
- [x] **Обновить выбранные** and **Обновить всё** actions.
- [x] Persistent per-account HTTP cookie jar protected by Windows DPAPI.
- [x] Native CAPTCHA image/input flow for MegaFon login code `a211`.
- [x] Browser/Playwright removed from the production runtime.
- [x] Application, shortcut and installer icon.

## M2 — parity with active VBA workflow

- [ ] Read-only tariff/remainders/current services/expenses views.
- [ ] Paid-option classification and owner rules.
- [ ] Last paid action from expense categories.
- [ ] Available-option catalogue.
- [ ] Personal offers catalogue and keep/reject/ask rules.
- [ ] Bulk refresh with bounded concurrency and per-account progress.

## M3 — controlled mutations

Only after current capture-log verification:

- [ ] connect/disconnect option;
- [ ] reject/activate personal offer;
- [ ] forwarding read/reset/set;
- [ ] tariff change;
- [ ] confirmation UX and operation audit log.

## M4 — packaging

- [x] PyInstaller onedir Windows build.
- [x] Windows installer and in-place update installer.
- [x] Latest-release-only retention and zero retained Actions artifacts.
- [ ] signed releases when signing material is configured.
