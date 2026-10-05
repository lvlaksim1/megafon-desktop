# Current state

As of 2026-10-05:

- The authoritative public product repository is `lvlaksim1/megafon-desktop`; project/display name is exactly **Megafon Desktop**.
- Product authority and manager-state authority are both `main`.
- Current published version is **v0.2.1**. GitHub Release contains only `MegafonDesktop-Update-v0.2.1.exe` (37,542,042 bytes), SHA-256 `ca81682b6404fcd32bd6e811b203e0e68f24ba29a953593e0b88c6db886c77d9`, target commit `d4dba41cb0acfc4a06267c773b1a0014fc65dd7f`. The prior v0.2.0 release was removed.
- Product scope is strictly consumer/B2C MegaFon personal cabinet. B2B and official/public MegaFon APIs are out of scope for protocol research.
- Runtime is **HTTP-only reverse engineering of the consumer web cabinet**. Browser/Playwright may be used only as an external research/capture instrument; it is not a runtime dependency or fallback.
- Network access is user-triggered only: no automatic account refresh at startup. UI provides per-account **Обновить** plus **Обновить всё**.
- v0.2.1 implements current frontend bootstrap via `/public/rwlk/service-worker.js` -> active `app.<hash>.js` and extracts `X-Cabinet-Id-Param`, `X-Cabinet-Check-Info`, and `X-Cabinet-Validation-Param`.
- Manual refresh checks `/api/auth/sessionCheck`; a saved session is reused only when it is authenticated for the requested phone.
- CAPTCHA auth is one preserved HTTP session: `POST /api/login` -> `a211` -> `GET /api/captcha/next` -> repeat login with `captcha` -> `authenticated:true`.
- Successful password/CAPTCHA auth is persisted immediately, before balance reads, so a later data endpoint failure does not discard a valid login.
- Per-account cookie jars/passwords are DPAPI-protected and survive application restarts and update installs.
- UI cleanup in v0.2.1: added **Удалить** per account with DB/password/auth-state cleanup; removed **Обновить выбранные**; removed the extra toolbar logo beside **Добавить номер**; application/window/shortcut icon remains.
- Refresh-token renewal is intentionally **not implemented**. Owner directive: do not run refresh-expiry experiments; only implement renewal after finding a proven source of truth that documents or implements the current B2C web-LK refresh mechanism.
- The observed login still establishes short-lived access/id tokens and long-lived `X-Cabinet-Refresh-Token`, but its renewal endpoint/trigger/rotation remains an evidence gap.
- v0.2.1 was built and published successfully through the trusted PC Runner Gateway on exact SHA. The contemporaneous GitHub-hosted release/CI jobs were cancelled before running steps and were not treated as code failures.
- Installation remains per-user under `%LOCALAPPDATA%\Programs\Megafon Desktop`; app data/auth state remains under `%LOCALAPPDATA%\MegaFonDesktop`. Updates preserve app data; full uninstall removes app-owned state.
