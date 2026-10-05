# Next actions

1. Replace the v0.2.0 auth transport with the verified B2C web-LK state machine rather than patching the current simplified login.
2. Implement HTTP bootstrap of the active web frontend: discover the current `app.<hash>.js` from service-worker/front-end metadata and extract current `X-Cabinet-Id-Param`, `X-Cabinet-Check-Info`, and `X-Cabinet-Validation-Param`.
3. Restore the per-account DPAPI-protected cookie jar only on a user-triggered refresh, then call `/api/auth/sessionCheck`; reuse it only if `authenticated=true` and the account number matches.
4. If login is required, keep one requests.Session for bootstrap -> login -> CAPTCHA image -> CAPTCHA submit -> authenticated session; save auth cookies immediately after successful login, before data reads.
5. Research and verify refresh-token behavior. Current evidence shows a long-lived HttpOnly `X-Cabinet-Refresh-Token`, but the exact access-token renewal trigger/endpoint/rotation must be captured after short-lived access/id tokens expire.
6. Make data calls with the current frontend-derived X-Cabinet headers and preserve any cookie rotations returned by the server.
7. Add replay/contract tests based on redacted owner captures, including header propagation, CAPTCHA continuation, sessionCheck, token persistence, token expiry/refresh, and wrong-account session rejection.
8. UI: add delete-account action (including secrets/auth-state deletion), remove **Обновить выбранные**, remove the toolbar logo beside **Добавить номер**, retain per-row **Обновить** and **Обновить всё**.
9. Only after the auth path is verified against live owner evidence continue remainders/services/expenses/tariff and later mutations.
10. Publish the next fixed release only as `MegafonDesktop-Update-vX.Y.Z.exe` after green Windows CI and evidence-based auth tests.
