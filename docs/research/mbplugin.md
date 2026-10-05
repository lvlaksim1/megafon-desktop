# MBplugin findings

Source: <https://github.com/artyl/mbplugin> (MIT license).

We use MBplugin as a research reference, not as the product shell. Megafon Desktop remains a native
Windows application.

## Useful mechanisms

The current `plugin/megafon.py` logs in through the real `lk.megafon.ru` page and obtains values by
capturing network responses. Its current MegaFon collector watches resources including:

- `balance/api/main` -> balance and balance-with-limit;
- `/api/auth/sessionCheck` -> subscriber name;
- `api/tariff/2019-3/current` -> tariff;
- `remainders/mini` -> voice/SMS/data remainders;
- `api/services/currentServices/list` -> paid/free services;
- `api/reports/expenses` -> expense information.

The shared browser controller uses a persistent Chromium context and records responses, then plugins
select responses by URL fragments. This is a strong resilience pattern for us because it lets the
site itself perform whatever current authentication/bootstrap sequence MegaFon requires.

## What we do not copy

- MBplugin's web-server UI: our UI is native Qt.
- B2B plugin logic: B2B is explicitly out of scope.
- Its general multi-provider framework: this project is intentionally MegaFon-specific.
- Large generic compatibility layers that do not serve this product.

## Design consequence

Implement a small response-capture engine rather than porting the entire MBplugin browser
controller. Preserve the important ideas: persistent per-account browser profile, response capture,
URL-fragment selectors, diagnostic response logging with secret redaction, and explicit manual auth
gates.
