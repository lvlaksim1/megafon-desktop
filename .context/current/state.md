# Current state

As of 2026-10-05:

- The authoritative public product repository is `lvlaksim1/megafon-desktop`; project/display name is exactly **Megafon Desktop**.
- Product authority and manager-state authority are both `main`.
- Current published product version is `0.2.0`, but its HTTP authorization implementation is known-broken against the owner's fresh B2C browser capture and must not be treated as the final auth architecture.
- Product scope is strictly consumer/B2C MegaFon personal cabinet. B2B and official/public MegaFon APIs are out of scope for protocol research.
- Runtime direction is **HTTP-only reverse engineering of the consumer web cabinet**. Browser/Playwright may be used only as an external research/capture instrument; it must not be a runtime dependency or fallback.
- Network access is user-triggered only: no automatic account refresh at application startup. The intended UI has per-account **Обновить** plus **Обновить всё**.
- Fresh owner capture proves the current password-login CAPTCHA flow: `POST /mlk/api/login` -> error code `a211` -> `GET /mlk/api/captcha/next` -> repeat `POST /mlk/api/login` with `captcha` -> `authenticated:true`.
- Current B2C web-LK requests require dynamic frontend-derived request context, notably `X-Cabinet-Id-Param`, `X-Cabinet-Check-Info`, and `X-Cabinet-Validation-Param`; login additionally uses current CSRF/session context.
- Fresh independent public implementations confirm that current frontend metadata can be discovered from the web-LK service worker / active `app.<hash>.js`, avoiding a browser runtime.
- Correct session reuse must use `/api/auth/sessionCheck` and verify that an authenticated session belongs to the requested account before reading data.
- Successful login sets a cookie-based auth family including short-lived access/id tokens and a long-lived `X-Cabinet-Refresh-Token`. Sensitive auth material must be persisted per account using Windows DPAPI.
- The owner capture shows access/id-token lifetime of about 1200 seconds and refresh-token lifetime of about 7776000 seconds (90 days) for that observed login. Exact refresh exchange/rotation behavior after access-token expiry is not yet proven by the current short capture.
- v0.2.0 currently saves session state too late (after balance reads), omits the current dynamic X-Cabinet bootstrap/sessionCheck model, and therefore can lose a successful CAPTCHA login when the following data request fails.
- Required UI cleanup for the next fix: add account deletion, remove the toolbar logo left of **Добавить номер**, remove **Обновить выбранные**, keep application/window/shortcut icon at the top/system level.
- Installation remains per-user under `%LOCALAPPDATA%\Programs\Megafon Desktop`; application data/auth state remains under `%LOCALAPPDATA%\MegaFonDesktop`. Update installers must preserve app data; full uninstall removes app-owned state.
- Subsequent releases remain executable update installers named `MegafonDesktop-Update-vX.Y.Z.exe`.
