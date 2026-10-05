# Roadmap

## M0 — repository and architecture

- [x] Public repository via repo-factory with Project Manager/Context Capsule.
- [x] Native Qt application skeleton.
- [x] SQLite account/snapshot persistence.
- [x] Windows DPAPI secret storage.
- [x] Direct login + balance transport from legacy VBA contract.
- [x] Unit-test baseline and CI.

## M1 — browser capture fallback

- [ ] Persistent per-account Playwright profile.
- [ ] Capture JSON responses by URL fragment.
- [ ] Login-state/CAPTCHA/manual-auth state machine.
- [ ] Balance, tariff, remainders, current services and expenses collectors.
- [ ] Redacted diagnostic bundle import/export for owner-provided browser logs.

## M2 — parity with active VBA workflow

- [ ] Paid-option classification and owner rules.
- [ ] Last paid action from expense categories.
- [ ] Available-option catalogue.
- [ ] Personal offers catalogue and keep/reject/ask rules.
- [ ] Bulk refresh with bounded concurrency and per-account progress.

## M3 — controlled mutations

Only after current browser-log verification:

- [ ] connect/disconnect option;
- [ ] reject/activate personal offer;
- [ ] forwarding read/reset/set;
- [ ] tariff change;
- [ ] confirmation UX and operation audit log.

## M4 — packaging

- [ ] PyInstaller one-file/one-folder evaluation.
- [ ] Windows installer and in-place updater.
- [ ] signed releases when signing material is configured.
