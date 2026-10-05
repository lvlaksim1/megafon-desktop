# Manager plans

1. Verify the newly introduced Windows CI and repair any bootstrap failures.
2. Finish M1 around the existing `ResponseCapture`: persistent profile lifecycle, robust login/manual-auth gates, parsers for tariff/remainders/services/expenses, and redacted diagnostic bundle ingestion.
3. When the owner supplies fresh browser logs, reconcile observed consumer endpoints/selectors against legacy VBA and MBplugin before enabling mutations.
4. Expand SQLite/domain models and native UI for options, expenses and personal offers; add deterministic fixture-driven tests.
5. Add bounded-concurrency bulk refresh and progress/error isolation across accounts.
6. Only after read paths are stable, implement and explicitly gate bill-affecting mutations.
7. Package for Windows with installer/updater and release verification.
