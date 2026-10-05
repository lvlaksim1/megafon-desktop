# Project architecture

The product is a native Qt/PySide6 Windows application, not a browser extension and not a web UI.

Stable layers:

- Qt desktop UI;
- application services and domain models;
- SQLite for non-secret account state, snapshots, rules and audit/history;
- Windows DPAPI for per-user secret storage;
- `MegafonTransport` boundary with two implementations:
  - direct HTTP adapter for known consumer `api.megafon.ru/mlk/...` contracts;
  - Playwright persistent-profile response-capture adapter as resilience/discovery fallback.

Network knowledge is classified as legacy-verified, cross-project, browser-observed, or runtime-verified. Destructive/bill-affecting operations are implemented only after fresh browser-log verification of their current request/response contracts.
