# Current blockers and open risks

- Fresh owner browser network logs are not yet available. Current consumer-LK selectors/endpoints can be researched, but mutation contracts cannot be considered runtime-verified until reconciled with those logs.
- The first Windows GitHub Actions run introduced by the bootstrap commit has not yet been verified.
- Direct consumer endpoints are undocumented and can change without notice; failures must degrade into explicit protocol/auth states rather than silent data corruption.
