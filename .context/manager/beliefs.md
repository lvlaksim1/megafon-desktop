# Manager beliefs

- MegaFon Desktop is a standalone native Windows application for consumer MegaFon accounts; browser-extension and B2B approaches are explicitly out of scope.
  - source: owner directive, 2026-10-05
  - authority: owner-directive
- The behavioral specification is assembled from the owner's legacy VBA, relevant public projects, and browser network logs the owner will provide later.
  - source: owner directive, 2026-10-05
  - authority: owner-directive
- The legacy VBA demonstrates working/previously working consumer-LK contracts for login, balances, options, expenses, forwarding, tariff and personal offers, but undocumented contracts must be treated as volatile.
  - source: owner-supplied VBA analysis, 2026-10-05
  - authority: verified-repository-input
- MBplugin's current MegaFon implementation demonstrates a useful resilience pattern: authenticate through the real LK in a persistent Playwright profile and collect JSON network responses for known resources.
  - source: public `artyl/mbplugin` repository studied 2026-10-05
  - authority: trusted-external
- Product `main` contains the native vertical slice, Playwright response capture, and fixture-driven parsers for MBplugin-observed remainder/service shapes plus recursive expense events. Eleven local unit tests and Python compilation pass.
  - source: verified repository worktree and local test run, 2026-10-05
  - authority: verified-repository
- Current browser selectors and mutation contracts have not yet been verified against the owner's fresh browser logs; therefore real-account mutations remain gated.
  - source: current project evidence, 2026-10-05
  - authority: manager-inference
