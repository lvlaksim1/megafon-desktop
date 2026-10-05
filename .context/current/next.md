# Next actions

1. Verify Windows CI and fix any test/lint/platform issue.
2. Continue M1 with a redacted browser-log/diagnostic bundle importer and connect captured tariff/remainders/services/expenses to an aggregate read model.
3. Extend SQLite/domain/UI for read-only service, remainder and expense views using fixture-driven tests.
4. Add bounded-concurrency bulk refresh and per-account progress/error isolation.
5. On receipt of fresh owner logs, reconcile endpoint/selectors and unlock only mutations whose current contracts are verified.
