# Next actions

1. Owner live-test v0.2.1 against a real B2C account: new account -> manual **Обновить** -> CAPTCHA when requested -> successful balance refresh -> close/reopen app -> manual refresh reuses the saved session.
2. If live behavior differs, diagnose from the exact HTTP error and compare it against the supplied capture before changing the protocol implementation.
3. Find a **proven source of truth** for the current B2C refresh-token mechanism. Do not run expiry experiments and do not invent an endpoint/rotation rule.
4. Once refresh renewal is proven, implement it without changing the manual-refresh-only UX.
5. After auth is live-confirmed, continue read-only B2C data: remainders, services, tariff, expenses and bounded multi-account refresh.
6. Keep all bill-affecting mutations gated until their current contracts are independently verified.
7. Continue delivering every version as `MegafonDesktop-Update-vX.Y.Z.exe`; PC Runner Gateway is now an available exact-SHA Windows release path.
