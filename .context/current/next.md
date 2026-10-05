# Next actions

1. Continue M1 by connecting captured tariff/remainders/services/expenses to aggregate read models and native UI.
2. Extend SQLite/domain/UI for read-only service, remainder and expense views using fixture-driven tests.
3. Add bounded-concurrency bulk refresh and per-account progress/error isolation.
4. On receipt of fresh owner logs, reconcile endpoint/selectors and unlock only mutations whose current contracts are verified.
5. For the next release, keep `RELEASE_KIND=Update`, bump `RELEASE_VERSION`, and publish only an executable update installer after green Windows CI.
