# Current blockers and open risks

- v0.2.1 implements the evidence-backed B2C auth flow, but owner-side live verification of the new build is still pending.
- Refresh-token renewal is not implemented. The exact current B2C renewal endpoint/trigger/rotation must come from a proven source of truth; owner explicitly rejected refresh-expiry experiments.
- Direct consumer endpoints and frontend-generated request parameters are undocumented and volatile. The implementation discovers current X-Cabinet values dynamically and must fail explicitly when the protocol changes.
- Authentication material is highly sensitive. Passwords, cookies and token families remain per-account and DPAPI-protected; raw capture secrets must never be committed.
- The Windows installer is not commercially code-signed, so SmartScreen/reputation warnings may occur.
