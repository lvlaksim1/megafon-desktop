# Latest handoff

## Current conclusion

v0.2.0's authorization path is not compatible with the full current B2C web-LK protocol. The owner supplied a fresh browser network capture showing the missing request context and successful CAPTCHA flow. Do not patch the existing simplified login blindly; replace it with the verified state machine.

## Verified B2C flow

- Runtime requirement: HTTP-only; no browser/Playwright runtime or fallback.
- No automatic account refresh at application startup.
- Manual refresh restores per-account auth state and first checks `/api/auth/sessionCheck`.
- Current frontend-derived request metadata includes `X-Cabinet-Id-Param`, `X-Cabinet-Check-Info`, `X-Cabinet-Validation-Param`.
- Password CAPTCHA flow is: login -> `a211` -> GET CAPTCHA image -> repeat login with CAPTCHA in the same HTTP session -> authenticated.
- Save the cookie jar immediately after successful authentication, before data reads.
- The observed successful login creates short-lived access/id token cookies (~1200 s) plus long-lived `X-Cabinet-Refresh-Token` (~90 days), CSRF cookies, JSESSIONID and identity cookies.
- Exact refresh-token exchange after short-token expiry is still an evidence gap. The current capture is too short; do not invent refresh behavior.

## External cross-check

Current/recent consumer reverse implementations (`Unlicensed-ZZZ/MobileBalance`, `dukei/any-balance-providers`) independently confirm sessionCheck, CAPTCHA continuation and dynamic X-Cabinet frontend metadata. MBplugin's current browser approach is useful as research evidence but is not the product runtime model.

## Required next UI changes

- Add delete-account with password/auth-state cleanup.
- Remove toolbar logo beside **Добавить номер**.
- Remove **Обновить выбранные**.
- Keep per-account **Обновить**, **Обновить всё**, and application/system icon.

## Release policy

All subsequent releases remain executable `MegafonDesktop-Update-vX.Y.Z.exe` installers and must preserve `%LOCALAPPDATA%\MegaFonDesktop` during updates.
