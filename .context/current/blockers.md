# Current blockers and open risks

- v0.2.0 authorization is not protocol-complete for the current consumer web cabinet. It omits dynamic frontend-derived X-Cabinet request context and the sessionCheck-first lifecycle.
- The supplied owner capture covers successful CAPTCHA login and immediate authenticated traffic, but it is too short to observe expiry of the ~20-minute access/id tokens. Therefore the exact refresh-token exchange/rotation mechanism is not yet runtime-proven.
- Direct consumer endpoints and frontend-generated request parameters are undocumented and volatile. The implementation must discover current values and fail explicitly when the protocol changes.
- Authentication material is highly sensitive. Passwords, cookies and token families must remain per-account and DPAPI-protected; raw capture secrets must never be committed to the repository.
- The Windows installer is not code-signed with a commercial certificate, so SmartScreen/reputation warnings may occur.
