# Architecture

## Product boundary

MegaFon Desktop is a **native desktop application**. A browser may be launched invisibly or visibly
as an implementation detail of a fallback transport, but the product is not a browser extension and
does not use a web UI as its primary interface.

B2B cabinets are out of scope.

## Layers

```text
Qt UI
  -> application services
      -> domain models
      -> SQLite repository
      -> secret store (Windows DPAPI)
      -> MegaFon transport abstraction
           -> Direct HTTP transport
           -> Browser capture transport (Playwright, fallback)
```

### Transport strategy

`DirectHttpTransport` is preferred while a known internal consumer-LK contract is working. It is
fast and does not need Chromium. All endpoint knowledge is isolated in that module.

`BrowserCaptureTransport` is the resilience layer. It will use the real `lk.megafon.ru` application
to authenticate and will capture JSON network responses for known resources. This is inspired by
the successful pattern used by MBplugin. It is not the application's user interface.

The application service can later implement an ordered transport policy:

1. reuse a valid direct session;
2. retry direct login when appropriate;
3. fall back to Playwright for interactive/new authentication or protocol discovery;
4. surface CAPTCHA/SMS/manual gates explicitly instead of hiding them as generic failures.

## Local state

SQLite contains non-secret account metadata, snapshots, offer rules and eventually operation logs.
Passwords and reusable authentication secrets must not be stored in plaintext in SQLite. On Windows,
per-user DPAPI is the initial secret backend.

## Network evidence

Endpoint contracts have confidence levels:

- **legacy-verified**: present in the owner's working VBA;
- **cross-project**: independently observed in MBplugin or another public implementation;
- **browser-observed**: seen in current owner-supplied network logs;
- **runtime-verified**: exercised successfully by the current application.

New operations should not be promoted to runtime-verified until exercised against an owner-controlled
account and their success condition is observed.
