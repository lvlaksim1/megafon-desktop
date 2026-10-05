# Architecture

## Product boundary

Megafon Desktop is a **native Windows desktop application** with a native Qt interface and a direct
HTTP transport. The production runtime is deliberately independent of browsers and Playwright.
Browser captures supplied by the owner may be analyzed as research evidence, but no browser is
launched or controlled by the application.

B2B cabinets are out of scope.

## Layers

```text
Qt UI
  -> application services
      -> domain models
      -> SQLite repository
      -> secret store (Windows DPAPI)
      -> Direct HTTP MegaFon transport
```

### HTTP authorization strategy

Network access happens only after an explicit user refresh action.

For each account:

1. restore the DPAPI-protected serialized HTTP cookie jar;
2. try the requested read using that session;
3. if MegaFon rejects the session, perform a direct password login;
4. if login returns CAPTCHA code `a211`, fetch `/api/captcha/next`, display the image in the
   native application and continue login with the user's answer;
5. persist the resulting cookie jar again.

There is no automatic refresh when Megafon Desktop starts.

## Local state

SQLite contains non-secret account metadata, snapshots, offer rules and eventually operation logs.
Passwords and reusable authentication state are not stored in plaintext in SQLite. On Windows,
per-user DPAPI is the secret backend.

Program updates replace files under `%LOCALAPPDATA%\Programs\Megafon Desktop` and leave
`%LOCALAPPDATA%\MegaFonDesktop` intact, so account data and authorization survive updates.

## Network evidence

Endpoint contracts have confidence levels:

- **legacy-verified**: present in the owner's working VBA;
- **cross-project**: independently observed in MBplugin or another public implementation;
- **capture-observed**: seen in current owner-supplied network logs;
- **runtime-verified**: exercised successfully by the current application.

New operations should not be promoted to runtime-verified until exercised against an
owner-controlled account and their success condition is observed.
