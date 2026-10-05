# Project constraints

- Consumer MegaFon only; B2B cabinets are out of scope until the owner changes scope explicitly.
- No required official consumer API exists; integration may use undocumented internal LK contracts.
- The application must be standalone Windows desktop software, not a browser extension.
- Evidence sources are the owner's legacy VBA, relevant public open-source projects (especially MBplugin), and owner-supplied browser network logs.
- Browser automation is an internal fallback transport, not the product UI.
- Never persist or commit passwords, cookies, session tokens, private browser profiles, or raw logs containing secrets.
- Do not execute bill-affecting or service-changing operations against a real account without explicit owner authorization and a currently verified contract.
- Keep public repository history free of bulky generated artifacts and local runtime data.
