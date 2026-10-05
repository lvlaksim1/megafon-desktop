# Latest handoff

## Current release

**Megafon Desktop v0.2.1** is published.

- Installer: `MegafonDesktop-Update-v0.2.1.exe`
- Size: 37,542,042 bytes
- SHA-256: `ca81682b6404fcd32bd6e811b203e0e68f24ba29a953593e0b88c6db886c77d9`
- Release target: `d4dba41cb0acfc4a06267c773b1a0014fc65dd7f`
- Only the latest release is retained.

## Implemented auth model

- B2C consumer cabinet only; no B2B or official API.
- HTTP-only runtime; no browser/Playwright fallback.
- No automatic refresh at startup.
- Frontend bootstrap: `/public/rwlk/service-worker.js` -> active `app.<hash>.js` -> dynamic X-Cabinet parameters.
- Manual refresh checks `/api/auth/sessionCheck` and validates the requested phone.
- CAPTCHA flow stays in the same HTTP session: login -> `a211` -> image -> login with CAPTCHA.
- Save the cookie jar immediately after successful auth, before data reads.
- Update installs preserve per-account DPAPI-protected passwords/auth state.

## UI in v0.2.1

- Per-account **Обновить**.
- Global **Обновить всё**.
- Per-account **Удалить** with password/session cleanup.
- Removed **Обновить выбранные**.
- Removed toolbar logo beside **Добавить номер**; system/application icon remains.

## Refresh token

Do not implement by inference and do not run expiry experiments. Owner requires a proven source of truth for the current B2C refresh mechanism before implementation.

## Build path

GitHub-hosted final jobs were cancelled before running. The trusted PC Runner Gateway built and published v0.2.1 successfully from exact SHA and is now allowlisted for Megafon Desktop `repo.powershell` tasks.
