# Project goals

1. Replace the owner's working Excel/VBA automation with a maintainable standalone Windows application.
2. Reach behavioral parity with the active consumer-LK workflow: balances, tariff, services/options, expenses, forwarding and personal offers, including bulk multi-account work.
3. Remain resilient to undocumented MegaFon consumer-LK changes by combining a fast direct HTTP transport with a Playwright/browser-capture fallback.
4. Keep account secrets protected locally and never commit credentials, cookies, tokens or raw private browser logs.
5. Produce an installable/updatable Windows application with clear diagnostics and safe confirmation/audit for bill-affecting mutations.
