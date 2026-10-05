# Current blockers and open risks

- Fresh owner browser network logs are not yet available. Current consumer-LK selectors/endpoints can be researched, but mutation contracts cannot be considered runtime-verified until reconciled with those logs.
- Direct consumer endpoints are undocumented and can change without notice; failures must degrade into explicit protocol/auth states rather than silent data corruption.
- The v0.1.0 installer is not code-signed with a commercial Windows signing certificate, so Windows SmartScreen/reputation warnings may occur on first runs despite the release asset being produced by verified CI.
