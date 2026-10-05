# Manager plans

1. Keep `lvlaksim1/megafon-desktop` as the sole active product repository.
2. Treat B2C web-LK reverse traffic as the protocol authority; ignore B2B and official/public MegaFon API documentation for this product.
3. Build an HTTP-only bootstrap that derives the current frontend request parameters from the active service-worker / `app.<hash>.js` assets.
4. On manual refresh only, restore account auth state, call `/api/auth/sessionCheck`, verify account identity, and reuse the session if valid.
5. If needed, perform password login and CAPTCHA in one preserved HTTP session and persist the resulting cookies immediately on authentication success.
6. Persist any subsequent cookie/token rotations after authenticated calls.
7. Specifically research refresh-token mechanics by obtaining evidence that spans expiry of the observed ~20-minute access/id tokens; determine whether renewal is implicit on an ordinary authenticated/sessionCheck request or uses a distinct endpoint, and whether the refresh token rotates.
8. Base tests on redacted real-capture contracts rather than invented fake cookies/headers.
9. Apply requested UI cleanup and account deletion with complete secret/session cleanup.
10. Resume remainders/services/expenses/tariff only after authorization is stable; keep mutations gated.
11. Publish each fixed version only as an executable update installer after green Windows CI.
