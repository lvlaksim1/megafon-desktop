# Manager plans

1. Keep `lvlaksim1/megafon-desktop` as the sole active product repository.
2. Treat B2C web-LK reverse traffic and current proven reverse implementations as protocol authority; ignore B2B and official/public MegaFon API documentation.
3. Keep runtime HTTP-only and manual-refresh-only.
4. Use dynamic frontend bootstrap, `sessionCheck`, one-session CAPTCHA login, immediate cookie persistence and account-identity validation as the auth baseline.
5. Await owner live verification of v0.2.1; if it fails, diagnose the exact server response before editing the protocol.
6. Research refresh-token renewal only from a proven current B2C source of truth. Do not use expiry experiments or speculative endpoints.
7. Resume remainders/services/expenses/tariff after auth live confirmation; keep mutations gated.
8. Use replay/contract tests based on redacted real-capture structures for future protocol changes.
9. Keep account deletion coupled to database, password and auth-state cleanup.
10. Publish each fixed version as an executable update installer; use the trusted PC Runner Gateway exact-SHA release task when hosted runners are unavailable.
