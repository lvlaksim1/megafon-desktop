# Megafon Desktop

Native Windows desktop manager for **consumer** MegaFon accounts.

The project replaces a legacy Excel/VBA workflow with a maintainable application:

- multiple accounts in one local database;
- HTTP-only reverse integration with the consumer web cabinet;
- persistent per-account HTTP authorization protected by Windows DPAPI;
- interactive CAPTCHA inside the desktop application;
- explicit manual refresh per account or for all accounts;
- balances, tariff, services/options, expenses, forwarding and personal offers;
- owner-defined rules for keeping/rejecting personal offers;
- no browser extension, no browser runtime dependency, no B2B scope, and no official MegaFon API dependency.

> The consumer MegaFon endpoints used by this project are internal, undocumented interfaces and
> may change without notice. Network behavior is therefore isolated behind transport interfaces.

## Current status

`v0.2.1` is the current Windows build.

The authoritative repository is `lvlaksim1/megafon-desktop`. The earlier `megafon-manager`
repository is legacy/migration material only.

### v0.2.1

- refresh is never started automatically when the program opens;
- each account has its own **Обновить** button and there is one **Обновить всё** action;
- **Обновить выбранные** was removed;
- the extra toolbar logo beside **Добавить номер** was removed; the application/window/shortcut icon remains;
- each account now has an **Удалить** action with confirmation; deletion removes the database row,
  saved password, and saved HTTP session state;
- authorization follows the current B2C web-LK flow: frontend bootstrap, dynamic
  `X-Cabinet-Id-Param`, `X-Cabinet-Check-Info`, `X-Cabinet-Validation-Param`,
  and `/api/auth/sessionCheck`;
- CAPTCHA code `a211` is handled in the same HTTP session:
  `/api/login` -> `/api/captcha/next` -> repeated `/api/login` with `captcha`;
- a successful password/CAPTCHA authorization is persisted immediately, before balance reads;
- restored authorization is reused only when `sessionCheck` confirms the expected phone number;
- failures after CAPTCHA are surfaced to the user instead of silently ending the refresh;
- no explicit refresh-token renewal mechanism is implemented in this release. The full cookie jar
  is persisted, but refresh-token behavior remains gated on a proven source of truth.

## Installation and updates

Windows distribution is one executable installer retained in the latest GitHub Release.

- The initial public build was `MegafonDesktop-Setup-v0.1.0.exe`.
- Current and future versions are `MegafonDesktop-Update-vX.Y.Z.exe`.

An update installer is a full payload: it upgrades an existing installation in place and can also
perform a clean installation when no older version is installed.

Program files: `%LOCALAPPDATA%\Programs\Megafon Desktop`

Application data: `%LOCALAPPDATA%\MegaFonDesktop`

Update installation does not delete application data, passwords, or saved HTTP authorization.
Uninstall removes both application-owned locations and application shortcuts. See
`docs/release.md`.

Release builds are not retained as GitHub Actions artifacts. After publishing a new release, older
releases/tags and residual Actions artifacts are removed automatically. CI/release pip caching is
also disabled to avoid repository Actions-cache growth.

## Development

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
megafon-desktop
```

## Data and secrets

Application data is kept under `%LOCALAPPDATA%\MegaFonDesktop` on Windows. Passwords and
serialized reusable HTTP authorization state are not stored in plaintext in SQLite: Windows DPAPI
encrypts them for the current Windows user.

## Research inputs

The implementation is based on:

1. the owner's legacy VBA automation;
2. fresh owner browser-network captures of the consumer personal cabinet;
3. current public reverse-engineered B2C implementations, including
   `Unlicensed-ZZZ/MobileBalance` and `dukei/any-balance-providers`;
4. `artyl/mbplugin` as additional behavioral/research context.

Browser tooling is a research instrument only; Megafon Desktop runtime remains HTTP-only.
